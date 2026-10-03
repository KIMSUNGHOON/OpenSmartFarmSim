"""Immutable server-clock planning events and public-key DecisionContext verification."""

from datetime import datetime, timezone
from hashlib import sha256
import re
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .thermal_run_store import _canonical, _document, _time


DOMAIN = b"decision-context-v1\0"
CONTEXT_FIELDS = frozenset({"context_version", "tenant_id", "snapshot_id", "decision_context_id",
    "decision_at_utc", "claim_mode", "decision_time_kind", "authority_id", "issued_at_utc", "planning_event_sha256"})
EVENT_FIELDS = (CONTEXT_FIELDS - {"context_version", "issued_at_utc", "planning_event_sha256"}) | {
    "event_version", "observed_at_utc"}


class PlanningHold(ValueError):
    pass


def _need(condition, code):
    if not condition:
        raise PlanningHold(code)


def _iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def install_planning_schema(conn, schema):
    """Fresh separately provisioned schema; no runtime grants or migration bypass."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL('''
        CREATE TABLE {}.planning_events (
            tenant_id text NOT NULL,
            decision_context_id text NOT NULL,
            event_raw bytea NOT NULL CHECK (octet_length(event_raw) BETWEEN 1 AND 16384),
            event_sha256 text NOT NULL CHECK (event_sha256 ~ '^[0-9a-f]{{64}}$'),
            context_raw bytea NOT NULL CHECK (octet_length(context_raw) BETWEEN 1 AND 16384),
            context_sha256 text NOT NULL CHECK (context_sha256 ~ '^[0-9a-f]{{64}}$'),
            context_signature text NOT NULL CHECK (context_signature ~ '^[0-9a-f]{{128}}$'),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, decision_context_id),
            UNIQUE (tenant_id, event_sha256),
            CHECK (encode(sha256(event_raw), 'hex') = event_sha256),
            CHECK (encode(sha256(context_raw), 'hex') = context_sha256)
        );
        CREATE FUNCTION {}.reject_planning_change() RETURNS trigger LANGUAGE plpgsql AS $body$
        BEGIN RAISE EXCEPTION 'immutable planning event'; END $body$;
        CREATE TRIGGER immutable_planning_event BEFORE UPDATE OR DELETE ON {}.planning_events
            FOR EACH ROW EXECUTE FUNCTION {}.reject_planning_change();
    ''').format(namespace, namespace, namespace, namespace))


class PlanningEventStore:
    def __init__(self, dsn, schema, *, principal_provider, runtime_identity=None):
        _need(type(dsn) is str and bool(dsn) and type(schema) is str and
              re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema) and callable(principal_provider),
              "planning_configuration_rejected")
        if runtime_identity is not None:
            from .planning_roles import PlanningLoginPolicy
            _need(type(runtime_identity) is tuple and len(runtime_identity) == 2 and
                  type(runtime_identity[0]) is PlanningLoginPolicy and runtime_identity[0].schema == schema and
                  type(runtime_identity[1]) is str and runtime_identity[1] in runtime_identity[0].roles,
                  "planning_configuration_rejected")
        self.dsn, self.schema, self.principal_provider = dsn, schema, principal_provider
        self.runtime_identity = runtime_identity

    def connect(self):
        if self.runtime_identity is not None:
            from .planning_roles import connect_planning
            return connect_planning(self.dsn, *self.runtime_identity)
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _table(self):
        return sql.SQL("{}.planning_events").format(sql.Identifier(self.schema))

    def _scope(self, tenant, scope):
        try:
            value = self.principal_provider()
            scopes = value.get("scopes") if type(value) is dict else None
            return (type(value) is dict and value.get("authenticated") is True and
                    value.get("tenant_id") == tenant and type(scopes) in (tuple, list, set, frozenset) and
                    all(type(item) is str for item in scopes) and scope in scopes)
        except Exception:
            return False

    def read_event(self, tenant, digest):
        if not self._scope(tenant, "planning_event_read"):
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND event_sha256=%s").format(
                self._table()), (tenant, digest)).fetchone()
        if row is None:
            return None
        _need(sha256(row["event_raw"]).hexdigest() == row["event_sha256"] and
              sha256(row["context_raw"]).hexdigest() == row["context_sha256"], "planning_integrity_rejected")
        return row


class PlanningAuthority:
    def __init__(self, store, authority_id, private_key, *, synthetic_smoke=False):
        _need(isinstance(store, PlanningEventStore) and type(authority_id) is str and
              re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", authority_id) and
              isinstance(private_key, Ed25519PrivateKey), "planning_authority_rejected")
        _need(synthetic_smoke is True or (store.runtime_identity is not None and
              store.runtime_identity[1] == "authority"), "planning_writer_login_required")
        self.store, self.authority_id, self.private_key = store, authority_id, private_key

    def issue(self, tenant, snapshot_id, *, claim_mode, decision_time_kind, hypothetical_at=None):
        _need(self.store._scope(tenant, "planning_event_issue"), "planning_issue_denied")
        _need(all(type(value) is str and 1 <= len(value) <= 200 and
                  not any(ord(character) < 32 for character in value) for value in (tenant, snapshot_id)) and
              claim_mode in ("ex_ante", "ex_post_replay") and
              type(claim_mode) is str and type(decision_time_kind) is str and
              decision_time_kind in ("actual", "hypothetical"), "planning_scope_rejected")
        if decision_time_kind == "actual":
            _need(hypothetical_at is None, "actual_time_override_rejected")
        else:
            _need(type(hypothetical_at) is datetime and hypothetical_at.tzinfo is not None and
                  hypothetical_at.utcoffset() is not None, "hypothetical_time_required")
        with self.store.connect() as conn:
            observed = conn.execute("SELECT clock_timestamp() AS now").fetchone()["now"]
            event = {"event_version": "planning-event-v1", "tenant_id": tenant, "snapshot_id": snapshot_id,
                "decision_context_id": str(uuid4()), "authority_id": self.authority_id,
                "claim_mode": claim_mode, "decision_time_kind": decision_time_kind,
                "observed_at_utc": _iso(observed),
                "decision_at_utc": _iso(observed if decision_time_kind == "actual" else hypothetical_at)}
            event_raw = _canonical(event)
            issued = conn.execute("SELECT clock_timestamp() AS now").fetchone()["now"]
            _need(issued >= observed, "planning_clock_reversed")
            context = {key: event[key] for key in CONTEXT_FIELDS & EVENT_FIELDS}
            context.update(context_version="decision-context-v1", issued_at_utc=_iso(issued),
                           planning_event_sha256=sha256(event_raw).hexdigest())
            raw = _canonical(context)
            signature = self.private_key.sign(DOMAIN + raw).hex()
            stored = conn.execute(sql.SQL('''INSERT INTO {} (tenant_id, decision_context_id, event_raw,
                event_sha256, context_raw, context_sha256, context_signature) VALUES (%s,%s,%s,%s,%s,%s,%s)
                RETURNING recorded_at
            ''').format(self.store._table()), (tenant, event["decision_context_id"], event_raw,
                context["planning_event_sha256"], raw, sha256(raw).hexdigest(), signature)).fetchone()
            _need(stored["recorded_at"] >= issued, "planning_clock_reversed")
        return raw, signature


class DecisionContextVerifier:
    """Only pinned public keys and a trusted read-only event reader, never a signing key."""

    def __init__(self, public_keys, event_reader, *, synthetic_smoke=False):
        _need(type(public_keys) is dict and bool(public_keys) and callable(event_reader) and all(
            type(name) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", name) and
            type(raw) is bytes and len(raw) == 32 for name, raw in public_keys.items()),
              "planning_verifier_rejected")
        reader = getattr(event_reader, "__self__", None)
        _need(synthetic_smoke is True or (type(reader) is PlanningEventStore and
              reader.runtime_identity is not None and reader.runtime_identity[1] == "supervisor" and
              getattr(event_reader, "__func__", None) is PlanningEventStore.read_event),
              "planning_reader_login_required")
        self.public_keys = {name: Ed25519PublicKey.from_public_bytes(raw) for name, raw in public_keys.items()}
        self.event_reader = event_reader

    def __call__(self, raw, signature):
        try:
            context = _document(raw)
            if (set(context) != CONTEXT_FIELDS or context["context_version"] != "decision-context-v1" or
                    type(signature) is not str or not re.fullmatch(r"[0-9a-f]{128}", signature)):
                return None
            key = self.public_keys.get(context["authority_id"])
            if key is None:
                return None
            key.verify(bytes.fromhex(signature), DOMAIN + raw)
            row = self.event_reader(context["tenant_id"], context["planning_event_sha256"])
            if (type(row) is not dict or row["context_raw"] != raw or row["context_signature"] != signature or
                    sha256(raw).hexdigest() != row["context_sha256"] or
                    sha256(row["event_raw"]).hexdigest() != context["planning_event_sha256"]):
                return None
            event = _document(row["event_raw"])
            if (set(event) != EVENT_FIELDS or event["event_version"] != "planning-event-v1" or
                    any(context[name] != event[name] for name in CONTEXT_FIELDS & EVENT_FIELDS) or
                    row["tenant_id"] != context["tenant_id"] or row["decision_context_id"] != context["decision_context_id"] or
                    row["event_sha256"] != context["planning_event_sha256"] or
                    not _time(event["observed_at_utc"]) <= _time(context["issued_at_utc"]) <= row["recorded_at"] or
                    context["claim_mode"] not in ("ex_ante", "ex_post_replay") or
                    context["decision_time_kind"] not in ("actual", "hypothetical") or
                    (context["decision_time_kind"] == "actual" and context["decision_at_utc"] != event["observed_at_utc"])):
                return None
            _time(context["decision_at_utc"])
            return {name: context[name] for name in
                    ("authority_id", "planning_event_sha256", "decision_at_utc", "decision_time_kind")}
        except Exception:
            return None
