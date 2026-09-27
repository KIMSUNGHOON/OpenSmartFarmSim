"""PostgreSQL pin for a fully recalculated conditional market result."""

from hashlib import sha256

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

from .market_result_codec import decode_market_result, encode_market_result
from .market_scenario import MarketScenarioService


def _hash(raw):
    return sha256(raw).hexdigest()


def install_market_result_schema(conn, schema):
    """Install after the market candidate schema, under a schema owner."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.market_result_records (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            scenario_id text NOT NULL CHECK (length(scenario_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            candidate_id char(64) NOT NULL CHECK (candidate_id ~ '^[0-9a-f]{{64}}$'),
            result_id char(64) NOT NULL CHECK (result_id ~ '^[0-9a-f]{{64}}$'),
            scenario_sha256 char(64) NOT NULL CHECK (scenario_sha256 ~ '^[0-9a-f]{{64}}$'),
            result_raw bytea NOT NULL CHECK (octet_length(result_raw) BETWEEN 1 AND 1048576),
            result_sha256 char(64) NOT NULL CHECK (result_sha256 ~ '^[0-9a-f]{{64}}$'),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, scenario_id, revision),
            UNIQUE (tenant_id, result_id),
            FOREIGN KEY (tenant_id, scenario_id, revision)
                REFERENCES {}.market_candidate_pins (tenant_id, scenario_id, revision),
            CHECK (result_sha256 = encode(sha256(result_raw), 'hex')),
            CHECK (((convert_from(result_raw, 'UTF8')::jsonb->>'codec_version') =
                    'market-result-v1') IS TRUE),
            CHECK (((convert_from(result_raw, 'UTF8')::jsonb->'result'->>'result_id') =
                    result_id) IS TRUE),
            CHECK (((convert_from(result_raw, 'UTF8')::jsonb->'result'->>'candidate_id') =
                    candidate_id) IS TRUE),
            CHECK (((convert_from(result_raw, 'UTF8')::jsonb->'result'->>'economic_scenario_sha256') =
                    scenario_sha256) IS TRUE)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_market_result_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'market result evidence is immutable'; END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER market_result_immutable BEFORE UPDATE OR DELETE ON {}.market_result_records
        FOR EACH ROW EXECUTE FUNCTION {}.reject_market_result_change()
    """).format(namespace, namespace))


class MarketResultStore:
    """Store server-calculated results; callers cannot submit result bytes."""

    def __init__(self, dsn, schema, candidate_repository, *, principal_provider):
        if not callable(principal_provider):
            raise ValueError("market result principal provider is required")
        self.dsn, self.schema = dsn, schema
        self._candidates = candidate_repository
        self._principal_provider = principal_provider

    def connect(self):
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
                    all(type(item) is str for item in scopes) and scope in scopes and
                    self._candidates.tenant_is_authenticated(principal["tenant_id"]) is True):
                return principal["tenant_id"]
        except Exception:
            pass
        return None

    def tenant_is_authenticated(self, tenant_id):
        return self._tenant("market_result_read") == tenant_id

    def _checked(self, conn, row):
        if row is None or _hash(row["result_raw"]) != row["result_sha256"]:
            raise ValueError("market result stored bytes differ")
        result = decode_market_result(row["result_raw"])
        candidate = conn.execute(sql.SQL("""
            SELECT candidate_id, scenario_sha256 FROM {}
            WHERE tenant_id=%s AND scenario_id=%s AND revision=%s
        """).format(self._table("market_candidate_pins")),
            (row["tenant_id"], row["scenario_id"], row["revision"])).fetchone()
        if (candidate is None or
                (result.result_id, result.candidate_id, result.economic_scenario_sha256,
                 result.economic_result.scenario_id,
                 result.economic_result.scenario_revision,
                 result.economic_result.scenario_sha256) !=
                (row["result_id"], row["candidate_id"], row["scenario_sha256"],
                 row["scenario_id"], row["revision"], row["scenario_sha256"]) or
                (candidate["candidate_id"], candidate["scenario_sha256"]) !=
                (row["candidate_id"], row["scenario_sha256"]) or
                result.assessment_status != "hold" or
                result.market_context != result.economic_result.market_context):
            raise ValueError("market result candidate binding differs")
        return result

    def pin_market_result(self, scenario_id, revision):
        tenant = self._tenant("market_result_write")
        if tenant is None:
            raise ValueError("market result write authority denied")
        result = MarketScenarioService(self._candidates).calculate_pinned(
            scenario_id, revision, tenant)
        raw = encode_market_result(result)
        with self.connect() as conn:
            conn.execute(sql.SQL("""
                INSERT INTO {} (tenant_id, scenario_id, revision, candidate_id,
                    result_id, scenario_sha256, result_raw, result_sha256)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            """).format(self._table("market_result_records")),
                (tenant, scenario_id, revision, result.candidate_id, result.result_id,
                 result.economic_scenario_sha256, raw, _hash(raw)))
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s
            """).format(self._table("market_result_records")),
                (tenant, scenario_id, revision)).fetchone()
            self._checked(conn, row)
            if row["result_raw"] != raw:
                raise ValueError("market result immutable pin conflict")
        return result

    def get_market_result(self, scenario_id, revision):
        tenant = self._tenant("market_result_read")
        if tenant is None:
            return None
        with self.connect() as conn:
            row = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND scenario_id=%s AND revision=%s
            """).format(self._table("market_result_records")),
                (tenant, scenario_id, revision)).fetchone()
            stored = self._checked(conn, row) if row is not None else None
        if stored is None:
            return None
        recalculated = MarketScenarioService(self._candidates).calculate_pinned(
            scenario_id, revision, tenant)
        if encode_market_result(recalculated) != row["result_raw"]:
            raise ValueError("market result replay differs")
        return stored
