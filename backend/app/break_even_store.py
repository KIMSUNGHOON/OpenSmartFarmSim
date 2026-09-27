"""Immutable PostgreSQL plan and result pins for conditional break-even scans."""

from hashlib import sha256
import json

import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import TypeAdapter

from .break_even import (BreakEvenPlan, BreakEvenRequest, BreakEvenResult,
                         BreakEvenService, canonical_request_sha256)
from .economic_contracts import untrusted_data


_RESULT = TypeAdapter(BreakEvenResult)
_READ_METHODS = frozenset({
    "get_economic_scenario", "get_economic_scenario_pin", "get_economic_input",
    "get_joint_shock", "get_joint_shock_pin", "get_input_rights",
    "get_settlement_applicability", "get_settlement_evidence",
    "get_prior_batch_cost", "get_market_hold_report", "get_market_candidate",
    "get_decision_context",
})


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _hash(raw):
    return sha256(raw).hexdigest()


def install_break_even_store_schema(conn, schema):
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.break_even_plan_results (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            plan_id text NOT NULL CHECK (length(plan_id) BETWEEN 1 AND 200),
            request_raw bytea NOT NULL CHECK (octet_length(request_raw) BETWEEN 1 AND 16384),
            request_sha256 char(64) NOT NULL,
            plan_raw bytea NOT NULL CHECK (octet_length(plan_raw) BETWEEN 1 AND 1048576),
            plan_sha256 char(64) NOT NULL,
            result_raw bytea NOT NULL CHECK (octet_length(result_raw) BETWEEN 1 AND 1048576),
            result_sha256 char(64) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, plan_id),
            CHECK (request_sha256 = encode(sha256(request_raw), 'hex')),
            CHECK (plan_sha256 = encode(sha256(plan_raw), 'hex')),
            CHECK (result_sha256 = encode(sha256(result_raw), 'hex')),
            CHECK (((convert_from(request_raw, 'UTF8')::jsonb->>'plan_id') = plan_id) IS TRUE),
            CHECK (((convert_from(plan_raw, 'UTF8')::jsonb->>'plan_id') = plan_id) IS TRUE),
            CHECK (((convert_from(plan_raw, 'UTF8')::jsonb->>'tenant_id') = tenant_id) IS TRUE),
            CHECK (((convert_from(plan_raw, 'UTF8')::jsonb->>'request_sha256') = request_sha256)
                   IS TRUE)
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_break_even_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'break-even evidence is immutable'; END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER break_even_immutable BEFORE UPDATE OR DELETE ON {}.break_even_plan_results
        FOR EACH ROW EXECUTE FUNCTION {}.reject_break_even_change()
    """).format(namespace, namespace))


class _ProposedPlanRepository:
    def __init__(self, source, plan):
        self._source, self._plan = source, plan

    def get_break_even_plan(self, plan_id):
        return self._plan.model_dump(mode="json") if plan_id == self._plan.plan_id else None

    def __getattr__(self, name):
        return getattr(self._source, name)


class BreakEvenStore:
    """Read and write only through a trusted, tenant-scoped candidate source."""

    def __init__(self, dsn, schema, source_repository, *, principal_provider):
        if not callable(principal_provider):
            raise ValueError("break-even principal provider is required")
        self.dsn, self.schema = dsn, schema
        self._source = source_repository
        self._principal_provider = principal_provider

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def _table(self):
        return sql.SQL("{}.break_even_plan_results").format(sql.Identifier(self.schema))

    def _tenant(self, scope):
        try:
            principal = self._principal_provider()
            scopes = principal.get("scopes") if isinstance(principal, dict) else None
            if (principal.get("authenticated") is True and
                    type(principal.get("tenant_id")) is str and
                    isinstance(scopes, (set, frozenset, list, tuple)) and
                    all(type(item) is str for item in scopes) and scope in scopes and
                    self._source.tenant_is_authenticated(principal["tenant_id"]) is True):
                return principal["tenant_id"]
        except Exception:
            pass
        return None

    def tenant_is_authenticated(self, tenant_id):
        return self._tenant("break_even_read") == tenant_id

    def __getattr__(self, name):
        if name in _READ_METHODS:
            def scoped_lookup(*args):
                if self._tenant("break_even_read") is None:
                    return None
                return getattr(self._source, name)(*args)
            return scoped_lookup
        raise AttributeError(name)

    @staticmethod
    def _checked(row):
        if row is None or any(_hash(row[raw]) != row[digest] for raw, digest in (
                ("request_raw", "request_sha256"), ("plan_raw", "plan_sha256"),
                ("result_raw", "result_sha256"))):
            raise ValueError("break-even stored bytes differ")
        request = BreakEvenRequest.model_validate_json(row["request_raw"])
        plan = BreakEvenPlan.model_validate_json(row["plan_raw"])
        result = _RESULT.validate_json(row["result_raw"])
        if (row["request_raw"] != _canonical(request.model_dump(mode="json")) or
                row["plan_raw"] != _canonical(plan.model_dump(mode="json")) or
                row["result_raw"] != _canonical(_RESULT.dump_python(result, mode="json")) or
                (request.plan_id, plan.plan_id, plan.tenant_id, plan.request_sha256) !=
                (row["plan_id"], row["plan_id"], row["tenant_id"], row["request_sha256"]) or
                canonical_request_sha256(request) != row["request_sha256"]):
            raise ValueError("break-even stored plan binding differs")
        return request, plan, result

    def _row(self, plan_id):
        tenant = self._tenant("break_even_read")
        if tenant is None:
            return None
        with self.connect() as conn:
            return conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND plan_id=%s
            """).format(self._table()), (tenant, plan_id)).fetchone()

    def pin_break_even_plan(self, request_value, plan_value):
        request = BreakEvenRequest.model_validate(untrusted_data(request_value))
        plan = BreakEvenPlan.model_validate_json(_canonical(untrusted_data(plan_value)))
        if (self._tenant("break_even_write") != plan.tenant_id or
                plan.plan_id != request.plan_id or
                plan.request_sha256 != canonical_request_sha256(request)):
            raise ValueError("break-even plan write or request binding denied")
        result = BreakEvenService(_ProposedPlanRepository(self._source, plan)).scan(
            request, plan.tenant_id)
        request_raw = _canonical(request.model_dump(mode="json"))
        plan_raw = _canonical(plan.model_dump(mode="json"))
        result_raw = _canonical(_RESULT.dump_python(result, mode="json"))
        if (len(request_raw) > 16384 or len(plan_raw) > 1048576 or
                len(result_raw) > 1048576):
            raise ValueError("break-even plan or result exceeds size limit")
        with self.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, plan_id, request_raw, request_sha256,
                    plan_raw, plan_sha256, result_raw, result_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """).format(self._table()),
                (plan.tenant_id, plan.plan_id, request_raw, _hash(request_raw),
                 plan_raw, _hash(plan_raw), result_raw, _hash(result_raw)))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND plan_id=%s
            """).format(self._table()), (plan.tenant_id, plan.plan_id)).fetchone()
            self._checked(row)
            if ((row["request_raw"], row["plan_raw"], row["result_raw"]) !=
                    (request_raw, plan_raw, result_raw)):
                raise ValueError("break-even immutable plan conflict")
        return result

    def get_break_even_plan(self, plan_id):
        row = self._row(plan_id)
        return self._checked(row)[1].model_dump(mode="json") if row is not None else None

    def get_break_even_result(self, plan_id):
        row = self._row(plan_id)
        if row is None:
            return None
        request, _, stored = self._checked(row)
        recalculated = BreakEvenService(self).scan(request, row["tenant_id"])
        if _canonical(_RESULT.dump_python(recalculated, mode="json")) != row["result_raw"]:
            raise ValueError("break-even replay result differs")
        return stored
