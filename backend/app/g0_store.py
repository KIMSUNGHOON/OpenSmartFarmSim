"""Signed, append-only PostgreSQL evidence for tenant-scoped G0 decisions."""

from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import re
from typing import Literal

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import model_validator

from app.gates import CheckEvidence, G0Policy, RightEvidence, SourceEvidence
from app.provenance import Digest, FrozenContract, Name, RightAction, SourceRecord, SourceScope


class ReviewProof(FrozenContract):
    """Independent reviewer material returned by a server configured resolver."""

    tenant_id: Name
    kind: Literal["source", "check", "right"]
    evidence_id: Name
    record_id: Name
    scope: SourceScope
    revision_id: Name
    raw_sha256: Digest
    reviewer: Name
    variable: Name | None = None
    check_name: Name | None = None
    check_version: Name | None = None
    action: RightAction | None = None
    use: Name | None = None
    conditions_met: bool | None = None
    evidence_content: bytes
    content_sha256: Digest

    @model_validator(mode="after")
    def valid_review(self):
        if not self.evidence_content or sha256(self.evidence_content).hexdigest() != self.content_sha256:
            raise ValueError("review content digest mismatch")
        check = (self.variable, self.check_name, self.check_version)
        if self.kind == "check":
            if any(value is None for value in check) or any(value is not None for value in (self.action, self.use, self.conditions_met)):
                raise ValueError("check proof scope mismatch")
        elif self.kind == "right":
            if any(value is not None for value in check) or self.action is None or self.use is None or self.conditions_met is None:
                raise ValueError("right proof purpose mismatch")
        elif any(value is not None for value in (*check, self.action, self.use, self.conditions_met)):
            raise ValueError("source proof scope mismatch")
        return self

    def binding(self) -> dict:
        return self.model_dump(mode="json", exclude={"evidence_content"})


def _json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _scope_digest(scope: SourceScope) -> str:
    return sha256(_json(scope.model_dump(mode="json")).encode()).hexdigest()


def install_g0_schema(conn: psycopg.Connection, schema: str) -> None:
    """Install into an existing, explicitly selected schema."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.g0_entries (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            kind text NOT NULL CHECK (kind IN
                ('record','policy','source','check','right','revocation','decision')),
            entry_id text NOT NULL CHECK (length(entry_id) BETWEEN 1 AND 200),
            record_id text,
            scope_digest char(64),
            action text,
            intended_use text,
            generation integer NOT NULL DEFAULT 0 CHECK (generation >= 0),
            payload text NOT NULL CHECK (octet_length(payload) BETWEEN 2 AND 1048576),
            payload_sha256 char(64) NOT NULL,
            signature char(64) NOT NULL CHECK (signature ~ '^[0-9a-f]{{64}}$'),
            recorded_at timestamptz NOT NULL,
            PRIMARY KEY (tenant_id, kind, entry_id),
            UNIQUE (tenant_id, entry_id),
            CHECK (payload_sha256 = encode(sha256(convert_to(payload, 'UTF8')), 'hex')),
            CHECK (kind != 'policy' OR
                (scope_digest IS NOT NULL AND action IS NOT NULL AND intended_use IS NOT NULL
                 AND generation > 0)),
            CHECK (kind != 'record' OR record_id = entry_id),
            CHECK (kind NOT IN ('source','check','right') OR record_id IS NOT NULL)
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE UNIQUE INDEX g0_policy_generation ON {}.g0_entries
            (tenant_id, scope_digest, action, intended_use, generation)
            WHERE kind = 'policy'
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE UNIQUE INDEX g0_one_revocation ON {}.g0_entries
            (tenant_id, action, record_id) WHERE kind = 'revocation'
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_g0_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'G0 evidence and decisions are immutable'; END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER g0_immutable BEFORE UPDATE OR DELETE ON {}.g0_entries
        FOR EACH ROW EXECUTE FUNCTION {}.reject_g0_change()
    """).format(namespace, namespace))


class G0Store:
    """The signing key and readers are server configuration, never request fields."""

    def __init__(self, dsn: str, schema: str, *, signing_key: bytes, raw_reader,
                 principal_provider, review_resolver):
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            raise ValueError("G0 signing key must contain at least 32 bytes")
        if not all(callable(provider) for provider in (raw_reader, principal_provider, review_resolver)):
            raise ValueError("G0 needs server raw, principal, and independent review providers")
        self.dsn = dsn
        self.schema = schema
        self._key = signing_key
        self.raw_reader = raw_reader
        self.principal_provider = principal_provider
        self.review_resolver = review_resolver

    def connect(self) -> psycopg.Connection:
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _table(self):
        return sql.SQL("{}.g0_entries").format(sql.Identifier(self.schema))

    def _lock(self, conn, tenant: str) -> None:
        conn.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 917032))", (tenant,))

    def _signature(self, row: dict) -> str:
        signed = {key: row[key] for key in (
            "tenant_id", "kind", "entry_id", "record_id", "scope_digest", "action",
            "intended_use", "generation", "payload_sha256")}
        signed["recorded_at"] = row["recorded_at"].astimezone(timezone.utc).isoformat()
        return hmac.new(self._key, _json(signed).encode(), sha256).hexdigest()

    def _append(self, conn, *, tenant: str, kind: str, entry_id: str, value: object,
                record_id: str | None = None, scope_digest: str | None = None,
                action: str | None = None, intended_use: str | None = None,
                generation: int = 0) -> None:
        payload = _json(value)
        row = dict(tenant_id=tenant, kind=kind, entry_id=entry_id, record_id=record_id,
                   scope_digest=scope_digest, action=action, intended_use=intended_use,
                   generation=generation, payload_sha256=sha256(payload.encode()).hexdigest(),
                   recorded_at=datetime.now(timezone.utc))
        conn.execute(sql.SQL("""
            INSERT INTO {} (tenant_id, kind, entry_id, record_id, scope_digest, action,
                intended_use, generation, payload, payload_sha256, signature, recorded_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """).format(self._table()), (
            tenant, kind, entry_id, record_id, scope_digest, action, intended_use,
            generation, payload, row["payload_sha256"], self._signature(row), row["recorded_at"]))

    def _verify(self, row: dict) -> object:
        if (sha256(row["payload"].encode()).hexdigest() != row["payload_sha256"] or
                not hmac.compare_digest(self._signature(row), row["signature"])):
            raise ValueError("G0 evidence integrity mismatch")
        return json.loads(row["payload"])

    def _one(self, conn, tenant: str, kind: str, entry_id: str, at: datetime | None = None):
        row = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND kind = %s AND entry_id = %s
        """).format(self._table()), (tenant, kind, entry_id)).fetchone()
        if row is None or (at is not None and row["recorded_at"] > at):
            return None
        self._verify(row)
        return row

    def _model(self, row, cls):
        if row is None:
            return None
        payload = self._verify(row)
        if cls in (SourceEvidence, CheckEvidence, RightEvidence):
            if (not isinstance(payload, dict) or set(payload) != {"review", "proof_binding"} or
                    not isinstance(payload["proof_binding"], dict)):
                raise ValueError("G0 review proof binding missing")
            model = cls.model_validate_json(_json(payload["review"]))
            binding = payload["proof_binding"]
            expected = dict(tenant_id=row["tenant_id"], kind=row["kind"],
                evidence_id=model.evidence_id, record_id=model.record_id,
                scope=model.scope.model_dump(mode="json"), revision_id=model.revision_id,
                raw_sha256=model.raw_sha256, reviewer=model.reviewer,
                variable=model.variable if isinstance(model, CheckEvidence) else None,
                check_name=model.check_name if isinstance(model, CheckEvidence) else None,
                check_version=model.check_version if isinstance(model, CheckEvidence) else None,
                action=model.action if isinstance(model, RightEvidence) else None,
                use=model.use if isinstance(model, RightEvidence) else None,
                conditions_met=model.conditions_met if isinstance(model, RightEvidence) else None)
            digest = binding.get("content_sha256")
            if (set(binding) != set(expected) | {"content_sha256"} or
                    any(binding[key] != value for key, value in expected.items()) or
                    not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
                raise ValueError("G0 review proof binding mismatch")
        else:
            model = cls.model_validate_json(row["payload"])
        expected = model.record_id if isinstance(model, SourceRecord) else (
            model.policy_id if isinstance(model, G0Policy) else model.evidence_id)
        if row["entry_id"] != expected:
            raise ValueError("G0 entry ID mismatch")
        if isinstance(model, G0Policy):
            if (row["scope_digest"] != _scope_digest(model.scope) or
                    row["action"] != model.intended_action or row["intended_use"] != model.intended_use):
                raise ValueError("G0 policy index mismatch")
        elif row["record_id"] != model.record_id:
            raise ValueError("G0 record binding mismatch")
        if isinstance(model, RightEvidence) and (
                row["action"] != model.action or row["intended_use"] != model.use):
            raise ValueError("G0 right purpose mismatch")
        return model

    def _revoked_at(self, conn, tenant: str, kind: str, entry_id: str, at: datetime):
        row = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND kind = 'revocation'
                AND record_id = %s AND action = %s AND recorded_at <= %s
        """).format(self._table()), (tenant, entry_id, kind, at)).fetchone()
        if row is None:
            return None
        value = self._verify(row)
        if (not isinstance(value, dict) or value.get("target_kind") != kind or
                value.get("target_id") != entry_id or
                not isinstance(value.get("reviewer"), str) or not value["reviewer"]):
            raise ValueError("G0 revocation binding mismatch")
        return row["recorded_at"].astimezone(timezone.utc)

    def repository(self, conn, tenant: str, at: datetime):
        return _Repository(self, conn, tenant, at)

    def get_decision(self, tenant: str, decision_id: str):
        principal = self.principal_provider()
        scopes = principal.get("scopes") if isinstance(principal, dict) else None
        if (not isinstance(principal, dict) or principal.get("authenticated") is not True or
                principal.get("tenant_id") != tenant or
                not isinstance(scopes, (set, frozenset, tuple, list)) or
                "g0_evaluate" not in scopes):
            raise PermissionError("G0 decision read denied")
        with self.connect() as conn:
            row = self._one(conn, tenant, "decision", decision_id)
            if row is None:
                return None
            value = self._verify(row)
            if value.get("decision_id") != decision_id or value.get("tenant_id") != tenant:
                raise ValueError("G0 decision binding mismatch")
            return value


class _Repository:
    def __init__(self, store: G0Store, conn, tenant: str, at: datetime):
        self.store, self.conn, self.tenant, self.at = store, conn, tenant, at

    def get_record(self, record_id: str):
        return self.store._model(self.store._one(self.conn, self.tenant, "record", record_id, self.at), SourceRecord)

    def get_raw_bytes(self, record_id: str):
        record = self.get_record(record_id)
        if record is None:
            return None
        raw = self.store.raw_reader(self.tenant, record.raw_sha256)
        return raw if isinstance(raw, bytes) else None

    def get_approved_policy(self, scope, action, use, decision_at):
        row = self.conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id = %s AND kind = 'policy'
                AND scope_digest = %s AND action = %s AND intended_use = %s
                AND recorded_at <= %s ORDER BY generation DESC LIMIT 1
        """).format(self.store._table()),
            (self.tenant, _scope_digest(scope), action, use, self.at)).fetchone()
        policy = self.store._model(row, G0Policy)
        if policy is None:
            return None
        revoked = self.store._revoked_at(self.conn, self.tenant, "policy", policy.policy_id, self.at)
        mandatory_times = ("observed_at", "published_at", "available_at")
        missing_times = tuple(name for name in mandatory_times if name not in policy.required_times)
        if revoked is None and not missing_times:
            return policy
        data = policy.model_dump(exclude={"policy_digest"})
        data["required_times"] = (*policy.required_times, *missing_times)
        if revoked is not None:
            data["revoked_at"] = revoked
        draft = G0Policy.model_construct(policy_digest="0" * 64, **data)
        return G0Policy(policy_digest=draft.content_digest(), **data)

    def _evidence(self, kind, entry_id, cls):
        model = self.store._model(self.store._one(self.conn, self.tenant, kind, entry_id, self.at), cls)
        if model is None:
            return None
        revoked = self.store._revoked_at(self.conn, self.tenant, kind, entry_id, self.at)
        return cls.model_validate({**model.model_dump(), "revoked_at": revoked}) if revoked else model

    def get_source_evidence(self, evidence_id):
        return self._evidence("source", evidence_id, SourceEvidence)

    def get_check_evidence(self, evidence_id):
        return self._evidence("check", evidence_id, CheckEvidence)

    def get_right_evidence(self, evidence_id):
        return self._evidence("right", evidence_id, RightEvidence)
