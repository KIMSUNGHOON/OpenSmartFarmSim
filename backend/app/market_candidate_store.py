"""Tenant-scoped immutable PostgreSQL pins for first-G1 market candidates.

The injected source repository remains responsible for baseline, shock, rights,
settlement and market-hold authority. This store persists only derived candidates
and their numeric input revisions; it never approves a MarketSnapshot.
"""

from copy import deepcopy
from hashlib import sha256
import json
import re

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .economic_contracts import (EconomicScenario, OwnedEconomicRecord,
                                 iter_economic_numbers, untrusted_data)
from .economics import canonical_scenario_sha256
from .market_scenario import MarketScenarioRequest, _json
from .market_runtime import connect_market, validate_market_identity


_DIGEST = re.compile(r"[0-9a-f]{64}\Z")
_RECORD_KEYS = {"candidate_id", "tenant_id", "request", "scenario_id", "revision",
                "economic_scenario_sha256", "shock_sha256", "rights_manifest_sha256",
                "binding_manifest_sha256", "immutable_job_input_ref",
                "immutable_job_input_sha256", "market_hold_report_id", "immutable"}


def _canonical(value):
    return _json(untrusted_data(value)).encode("utf-8")


def _hash(raw):
    return sha256(raw).hexdigest()


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("duplicate market candidate JSON key")
        value[key] = item
    return value


def _parse(raw, maximum=1048576):
    if type(raw) is not bytes or not 1 <= len(raw) <= maximum:
        raise ValueError("market candidate raw bytes invalid")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if _canonical(value) != raw:
            raise ValueError("market candidate raw bytes are not canonical")
    except (UnicodeError, TypeError, RecursionError, OverflowError) as exc:
        raise ValueError("market candidate JSON invalid") from exc
    return value


def _check_record_identity(record, scenario):
    if type(record) is not dict or set(record) != _RECORD_KEYS:
        raise ValueError("market candidate record shape differs")
    request = MarketScenarioRequest.model_validate_json(_canonical(record["request"]))
    hashes = (record["candidate_id"], record["economic_scenario_sha256"],
              record["shock_sha256"], record["rights_manifest_sha256"],
              record["binding_manifest_sha256"], record["immutable_job_input_sha256"])
    if any(type(value) is not str or not _DIGEST.fullmatch(value) for value in hashes):
        raise ValueError("market candidate digest is invalid")
    scenario_sha = canonical_scenario_sha256(scenario)
    identity = _hash(_canonical({"baseline": request.baseline.sha256,
                                 "shock": record["shock_sha256"],
                                 "rights": record["rights_manifest_sha256"],
                                 "bindings": record["binding_manifest_sha256"]}))
    candidate_id = _hash(_canonical({"shock": (request.shock.shock_id,
                                               request.shock.revision,
                                               record["shock_sha256"]),
                                      "rights": record["rights_manifest_sha256"],
                                      "bindings": record["binding_manifest_sha256"],
                                      "economic_scenario": scenario_sha}))
    if (record["immutable"] is not True or
            (record["tenant_id"], record["scenario_id"], record["revision"],
         record["economic_scenario_sha256"], record["candidate_id"],
         record["shock_sha256"], record["market_hold_report_id"],
         record["immutable_job_input_ref"], record["immutable_job_input_sha256"],
         record["immutable"]) !=
            (scenario.tenant_id, scenario.scenario_id, scenario.scenario_revision,
             scenario_sha, candidate_id, request.shock.sha256,
             request.market_context.hold_report_id, f"market-job-{candidate_id[:32]}",
             scenario_sha, True) or
            scenario.scenario_id != f"market-{identity[:32]}" or
            scenario.scenario_revision != "r1" or
            request.decision_at != scenario.decision_at or
            request.market_context != scenario.market_context or
            scenario.scenario_market_context != scenario.market_context):
        raise ValueError("market candidate record derivation differs")


def install_market_candidate_schema(conn, schema):
    """Owner-run, additive installation; no existing candidate is rewritten."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.market_candidate_pins (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            candidate_id char(64) NOT NULL CHECK (candidate_id ~ '^[0-9a-f]{{64}}$'),
            scenario_id text NOT NULL CHECK (length(scenario_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            record_raw bytea NOT NULL CHECK (octet_length(record_raw) BETWEEN 1 AND 1048576),
            record_sha256 char(64) NOT NULL,
            scenario_raw bytea NOT NULL CHECK (octet_length(scenario_raw) BETWEEN 1 AND 1048576),
            scenario_sha256 char(64) NOT NULL,
            inputs_manifest_raw bytea NOT NULL
                CHECK (octet_length(inputs_manifest_raw) BETWEEN 2 AND 1048576),
            inputs_manifest_sha256 char(64) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, scenario_id, revision),
            UNIQUE (tenant_id, candidate_id),
            CHECK (record_sha256 = encode(sha256(record_raw), 'hex')),
            CHECK (scenario_sha256 = encode(sha256(scenario_raw), 'hex')),
            CHECK (inputs_manifest_sha256 = encode(sha256(inputs_manifest_raw), 'hex')),
            CHECK (((convert_from(record_raw, 'UTF8')::jsonb->>'tenant_id') = tenant_id) IS TRUE),
            CHECK (((convert_from(record_raw, 'UTF8')::jsonb->>'scenario_id') = scenario_id) IS TRUE),
            CHECK (((convert_from(record_raw, 'UTF8')::jsonb->>'revision') = revision) IS TRUE),
            CHECK (((convert_from(record_raw, 'UTF8')::jsonb->>'candidate_id') = candidate_id) IS TRUE),
            CHECK (((convert_from(scenario_raw, 'UTF8')::jsonb->>'tenant_id') = tenant_id) IS TRUE),
            CHECK (((convert_from(scenario_raw, 'UTF8')::jsonb->>'scenario_id') = scenario_id) IS TRUE),
            CHECK (((convert_from(scenario_raw, 'UTF8')::jsonb->>'scenario_revision') = revision) IS TRUE)
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.market_candidate_inputs (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            input_id text NOT NULL CHECK (length(input_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 16384),
            payload_sha256 char(64) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, input_id, revision),
            CHECK (payload_sha256 = encode(sha256(payload_raw), 'hex')),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'tenant_id') = tenant_id) IS TRUE),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'input_id') = input_id) IS TRUE),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'revision') = revision) IS TRUE)
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_market_candidate_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'market candidate evidence is immutable'; END
        $$
    """).format(namespace))
    for table in ("market_candidate_pins", "market_candidate_inputs"):
        conn.execute(sql.SQL("""
            CREATE TRIGGER market_candidate_immutable BEFORE UPDATE OR DELETE ON {}.{}
            FOR EACH ROW EXECUTE FUNCTION {}.reject_market_candidate_change()
        """).format(namespace, sql.Identifier(table), namespace))


class MarketCandidateDenied(ValueError):
    pass


class MarketCandidateConflict(ValueError):
    pass


class MarketCandidateStore:
    """Persist derived candidates while trusted source readers resolve originals."""

    def __init__(self, dsn, schema, source_repository, *, principal_provider, runtime_identity=None):
        if not callable(principal_provider):
            raise ValueError("market candidate principal provider is required")
        validate_market_identity(schema, runtime_identity, calculation=True)
        self.runtime_identity = runtime_identity
        self.dsn, self.schema = dsn, schema
        self._source = source_repository
        self._principal_provider = principal_provider

    def connect(self):
        if self.runtime_identity is not None:
            return connect_market(self.dsn, self.runtime_identity)
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _table(self, name):
        return sql.SQL("{}.{}").format(sql.Identifier(self.schema), sql.Identifier(name))

    def _tenant(self, scope):
        try:
            principal = self._principal_provider()
            scopes = principal.get("scopes") if isinstance(principal, dict) else None
            if (principal.get("authenticated") is True and
                    type(principal.get("tenant_id")) is str and
                    isinstance(scopes, (set, frozenset, list, tuple)) and
                    scope in scopes and all(type(item) is str for item in scopes) and
                    self._source.tenant_is_authenticated(principal["tenant_id"]) is True):
                return principal["tenant_id"]
        except Exception:
            pass
        return None

    def tenant_is_authenticated(self, tenant_id):
        return self._tenant("market_candidate_read") == tenant_id

    def __getattr__(self, name):
        if name in {"get_joint_shock", "get_joint_shock_pin", "get_input_rights",
                    "get_settlement_applicability", "get_settlement_evidence",
                    "get_prior_batch_cost", "get_market_hold_report",
                    "get_decision_context"}:
            def scoped_lookup(*args):
                tenant = self._tenant("market_candidate_read")
                if tenant is None:
                    return None
                raw = getattr(self._source, name)(*args)
                value = untrusted_data(raw) if raw is not None else None
                return (deepcopy(value) if type(value) is dict and
                        value.get("tenant_id") == tenant else None)
            return scoped_lookup
        raise AttributeError(name)

    @staticmethod
    def _checked_input(row):
        if row is None or _hash(row["payload_raw"]) != row["payload_sha256"]:
            raise ValueError("market candidate input integrity differs")
        _parse(row["payload_raw"], 16384)
        record = OwnedEconomicRecord.model_validate_json(row["payload_raw"])
        if (record.tenant_id, record.input_id, record.revision) != (
                row["tenant_id"], row["input_id"], row["revision"]):
            raise ValueError("market candidate input identity differs")
        return record.model_dump(mode="python")

    def _checked_candidate(self, conn, row):
        if row is None or any(_hash(row[raw]) != row[digest] for raw, digest in (
                ("record_raw", "record_sha256"), ("scenario_raw", "scenario_sha256"),
                ("inputs_manifest_raw", "inputs_manifest_sha256"))):
            raise ValueError("market candidate pin integrity differs")
        record = _parse(row["record_raw"])
        scenario = EconomicScenario.model_validate_json(row["scenario_raw"])
        manifest = _parse(row["inputs_manifest_raw"])
        if (type(record) is not dict or type(manifest) is not list or
                not 0 <= len(manifest) <= 1000 or
                (record.get("tenant_id"), record.get("candidate_id"),
                 record.get("scenario_id"), record.get("revision")) !=
                (row["tenant_id"], row["candidate_id"], row["scenario_id"], row["revision"]) or
                (scenario.tenant_id, scenario.scenario_id, scenario.scenario_revision) !=
                (row["tenant_id"], row["scenario_id"], row["revision"]) or
                canonical_scenario_sha256(scenario) != row["scenario_sha256"] or
                record.get("economic_scenario_sha256") != row["scenario_sha256"]):
            raise ValueError("market candidate pin scope differs")
        _check_record_identity(record, scenario)
        if any(type(ref) is not dict or set(ref) != {"input_id", "revision", "sha256"} or
               type(ref["input_id"]) is not str or type(ref["revision"]) is not str or
               type(ref["sha256"]) is not str or not _DIGEST.fullmatch(ref["sha256"])
               for ref in manifest):
            raise ValueError("market candidate input manifest invalid")
        if manifest != sorted(manifest, key=lambda item: (item["input_id"], item["revision"])):
            raise ValueError("market candidate input manifest is not sorted")
        seen = set()
        for ref in manifest:
            key = (ref["input_id"], ref["revision"])
            if key in seen:
                raise ValueError("market candidate input manifest repeats an ID")
            seen.add(key)
        inputs = {}
        if manifest:
            input_rows = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND (input_id, revision) IN
                    (SELECT * FROM unnest(%s::text[], %s::text[]))
            """).format(self._table("market_candidate_inputs")),
                (row["tenant_id"], [ref["input_id"] for ref in manifest],
                 [ref["revision"] for ref in manifest])).fetchall()
            inputs = {(value["input_id"], value["revision"]): value for value in input_rows}
            if len(inputs) != len(input_rows):
                raise ValueError("market candidate input manifest repeats an ID")
        for ref in manifest:
            key = (ref["input_id"], ref["revision"])
            input_row = inputs.get(key)
            self._checked_input(input_row)
            if ((input_row["tenant_id"], input_row["input_id"], input_row["revision"]) !=
                    (row["tenant_id"], *key) or input_row["payload_sha256"] != ref["sha256"]):
                raise ValueError("market candidate input manifest hash differs")
        return record, scenario.model_dump(mode="python")

    def _candidate(self, scenario_id, revision):
        tenant = self._tenant("market_candidate_read")
        if tenant is None:
            return None
        with self.connect() as conn:
            return self._candidate_in_transaction(conn, tenant, scenario_id, revision)

    def _candidate_in_transaction(self, conn, tenant, scenario_id, revision):
        if self._tenant("market_candidate_read") != tenant:
            return None
        row = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s
        """).format(self._table("market_candidate_pins")),
            (tenant, scenario_id, revision)).fetchone()
        return self._checked_candidate(conn, row) if row is not None else None

    def get_market_candidate(self, scenario_id, revision):
        candidate = self._candidate(scenario_id, revision)
        return deepcopy(candidate[0]) if candidate is not None else None

    def get_economic_scenario(self, scenario_id, revision):
        candidate = self._candidate(scenario_id, revision)
        if candidate is not None:
            return deepcopy(candidate[1])
        tenant = self._tenant("market_candidate_read")
        if tenant is None:
            return None
        raw = self._source.get_economic_scenario(scenario_id, revision)
        value = untrusted_data(raw) if raw is not None else None
        return deepcopy(value) if type(value) is dict and value.get("tenant_id") == tenant else None

    def get_economic_scenario_pin(self, scenario_id, revision):
        candidate = self._candidate(scenario_id, revision)
        if candidate is not None:
            record, scenario = candidate
            return {"tenant_id": scenario["tenant_id"], "scenario_id": scenario_id,
                    "scenario_revision": revision, "decision_at": scenario["decision_at"],
                    "payload_sha256": record["economic_scenario_sha256"],
                    "immutable_job_input_ref": record["immutable_job_input_ref"],
                    "immutable_job_input_sha256": record["economic_scenario_sha256"],
                    "immutable": True}
        tenant = self._tenant("market_candidate_read")
        if tenant is None:
            return None
        raw = self._source.get_economic_scenario_pin(scenario_id, revision)
        value = untrusted_data(raw) if raw is not None else None
        return deepcopy(value) if type(value) is dict and value.get("tenant_id") == tenant else None

    def get_economic_input(self, input_id, revision):
        tenant = self._tenant("market_candidate_read")
        if tenant is None:
            return None
        with self.connect() as conn:
            value = self._input_in_transaction(conn, tenant, input_id, revision)
        if value is not None:
            return value
        raw = self._source.get_economic_input(input_id, revision)
        value = untrusted_data(raw) if raw is not None else None
        return deepcopy(value) if type(value) is dict and value.get("tenant_id") == tenant else None

    def _input_in_transaction(self, conn, tenant, input_id, revision):
        if self._tenant("market_candidate_read") != tenant:
            return None
        row = conn.execute(sql.SQL("""
            SELECT * FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s
        """).format(self._table("market_candidate_inputs")),
            (tenant, input_id, revision)).fetchone()
        return self._checked_input(row) if row is not None else None

    def pin_market_candidate(self, record_value, scenario_value, new_records):
        if self._tenant("market_candidate_write") is None:
            raise MarketCandidateDenied("market candidate write authority denied")
        with self.connect() as conn:
            self._pin_in_transaction(conn, record_value, scenario_value, new_records)
        return True

    def _pin_in_transaction(self, conn, record_value, scenario_value, new_records):
        scenario = EconomicScenario.model_validate(untrusted_data(scenario_value))
        tenant = scenario.tenant_id
        if self._tenant("market_candidate_write") != tenant:
            raise MarketCandidateDenied("market candidate write authority denied")
        record = untrusted_data(record_value)
        scenario_sha = canonical_scenario_sha256(scenario)
        if (type(record) is not dict or
                (record.get("tenant_id"), record.get("scenario_id"), record.get("revision"),
                 record.get("economic_scenario_sha256")) !=
                (tenant, scenario.scenario_id, scenario.scenario_revision, scenario_sha) or
                record.get("immutable") is not True or
                type(record.get("candidate_id")) is not str or
                not _DIGEST.fullmatch(record["candidate_id"]) or
                type(new_records) is not list or len(new_records) > 1000):
            raise ValueError("market candidate bundle scope invalid")
        _check_record_identity(record, scenario)
        scenario_numbers = tuple(iter_economic_numbers(scenario))
        numbers = {(item.input_id, item.revision): item for item in scenario_numbers}
        if len(numbers) != len(scenario_numbers):
            raise ValueError("market candidate repeats a numeric revision")
        additions = {}
        for raw in new_records:
            item = OwnedEconomicRecord.model_validate(untrusted_data(raw))
            key = (item.input_id, item.revision)
            original = numbers.get(key)
            if (key in additions or original is None or item.tenant_id != tenant or
                    item.available_at > scenario.decision_at or
                    item.scope_start > scenario.period_start or
                    item.scope_end < scenario.period_end or
                    item.model_dump(exclude={"tenant_id", "scope_start", "scope_end"}) !=
                    original.model_dump()):
                raise ValueError("market candidate numeric input scope invalid")
            additions[key] = _canonical(item.model_dump(mode="json"))
        for key, original in numbers.items():
            source_raw = self._source.get_economic_input(*key)
            if source_raw is None and key not in additions:
                raise ValueError("market candidate numeric input is missing")
            if source_raw is not None:
                source_item = OwnedEconomicRecord.model_validate(untrusted_data(source_raw))
                if (source_item.tenant_id != tenant or
                        source_item.available_at > scenario.decision_at or
                        source_item.scope_start > scenario.period_start or
                        source_item.scope_end < scenario.period_end or
                        source_item.model_dump(exclude={"tenant_id", "scope_start", "scope_end"})
                        != original.model_dump()):
                    raise ValueError("market candidate numeric revision collides with source")
        record_raw = _canonical(record)
        scenario_raw = _canonical(scenario.model_dump(mode="json"))
        manifest_raw = _canonical([{"input_id": key[0], "revision": key[1],
                                    "sha256": _hash(raw)}
                                   for key, raw in sorted(additions.items())])
        if max(len(record_raw), len(scenario_raw), len(manifest_raw)) > 1048576:
            raise ValueError("market candidate bundle exceeds size limit")
        conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, candidate_id, scenario_id, revision,
                    record_raw, record_sha256, scenario_raw, scenario_sha256,
                    inputs_manifest_raw, inputs_manifest_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT DO NOTHING
            """).format(self._table("market_candidate_pins")),
                (tenant, record["candidate_id"], scenario.scenario_id,
                 scenario.scenario_revision, record_raw, _hash(record_raw),
                 scenario_raw, _hash(scenario_raw), manifest_raw, _hash(manifest_raw)))
        for key, raw in sorted(additions.items()):
            if len(raw) > 16384:
                raise ValueError("market candidate numeric input exceeds size limit")
            conn.execute(sql.SQL("""
                    INSERT INTO {} (tenant_id, input_id, revision, payload_raw, payload_sha256)
                    VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
                """).format(self._table("market_candidate_inputs")),
                    (tenant, *key, raw, _hash(raw)))
            row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE tenant_id=%s AND input_id=%s AND revision=%s
                """).format(self._table("market_candidate_inputs")),
                    (tenant, *key)).fetchone()
            if row["payload_raw"] != raw:
                raise MarketCandidateConflict("market candidate numeric revision conflict")
        row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s
            """).format(self._table("market_candidate_pins")),
                (tenant, scenario.scenario_id, scenario.scenario_revision)).fetchone()
        if row is None or (row["record_raw"], row["scenario_raw"],
                           row["inputs_manifest_raw"]) != (
                record_raw, scenario_raw, manifest_raw):
            raise MarketCandidateConflict("market candidate immutable pin conflict")
        self._checked_candidate(conn, row)
        if self._tenant("market_candidate_write") != tenant:
            raise MarketCandidateDenied("market candidate write authority denied")
        return row
