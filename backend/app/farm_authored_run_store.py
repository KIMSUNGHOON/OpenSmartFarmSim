"""Immutable tenant-scoped custody for authored thermal Run publication bytes."""

from psycopg import sql


class AuthoredRunStoreHold(ValueError):
    pass


def install_authored_run_schema(conn, schema):
    """Owner-run additive table after jobs and authored release packet storage."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.authored_thermal_runs (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            run_id text NOT NULL CHECK (run_id ~ '^authored-thermal-run-v1:[0-9a-f]{{64}}$'),
            simulation_job_id uuid NOT NULL,
            review_job_id uuid NOT NULL,
            registration_sha256 char(64) NOT NULL,
            scenario_id text NOT NULL CHECK (length(scenario_id) BETWEEN 1 AND 200),
            scenario_revision text NOT NULL CHECK (length(scenario_revision) BETWEEN 1 AND 200),
            trace0_raw bytea NOT NULL CHECK (octet_length(trace0_raw) BETWEEN 1 AND 1048576),
            trace0_sha256 char(64) NOT NULL,
            trace1_raw bytea NOT NULL CHECK (octet_length(trace1_raw) BETWEEN 1 AND 1048576),
            trace1_sha256 char(64) NOT NULL,
            preparation_raw bytea NOT NULL CHECK (octet_length(preparation_raw) BETWEEN 1 AND 65536),
            preparation_sha256 char(64) NOT NULL,
            publication_raw bytea NOT NULL CHECK (octet_length(publication_raw) BETWEEN 1 AND 65536),
            publication_sha256 char(64) NOT NULL,
            gate_signature char(64) NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, run_id),
            UNIQUE (tenant_id, simulation_job_id),
            FOREIGN KEY (tenant_id, simulation_job_id)
                REFERENCES {}.jobs (tenant_id, job_id),
            FOREIGN KEY (tenant_id, review_job_id)
                REFERENCES {}.authored_release_packets (tenant_id, review_job_id),
            CHECK (trace0_sha256 = encode(sha256(trace0_raw), 'hex')),
            CHECK (trace1_sha256 = encode(sha256(trace1_raw), 'hex')),
            CHECK (preparation_sha256 = encode(sha256(preparation_raw), 'hex')),
            CHECK (publication_sha256 = encode(sha256(publication_raw), 'hex')),
            CHECK ((convert_from(trace0_raw, 'UTF8')::jsonb->>'run_id' = run_id) IS TRUE),
            CHECK ((convert_from(trace1_raw, 'UTF8')::jsonb->>'run_id' = run_id) IS TRUE),
            CHECK ((convert_from(trace0_raw, 'UTF8')::jsonb->>'status' = 'accepted') IS TRUE),
            CHECK ((convert_from(trace1_raw, 'UTF8')::jsonb->>'status' = 'accepted') IS TRUE),
            CHECK ((convert_from(preparation_raw, 'UTF8')::jsonb->>'status' = 'prepared_unpublished') IS TRUE),
            CHECK ((convert_from(publication_raw, 'UTF8')::jsonb->>'status' = 'accepted') IS TRUE),
            CHECK ((convert_from(publication_raw, 'UTF8')::jsonb->>'run_id' = run_id) IS TRUE),
            CHECK ((convert_from(publication_raw, 'UTF8')::jsonb->>'preparation_sha256' = preparation_sha256) IS TRUE),
            CHECK ((convert_from(trace1_raw, 'UTF8')::jsonb#>>
                '{{initial_state,temperature,previous_trace_sha256}}' = trace0_sha256) IS TRUE),
            CHECK ((convert_from(trace1_raw, 'UTF8')::jsonb#>>
                '{{initial_state,humidity_ratio,previous_trace_sha256}}' = trace0_sha256) IS TRUE)
        )
    """).format(namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_authored_run_change()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'authored thermal Run is immutable'; END $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER authored_run_immutable BEFORE UPDATE OR DELETE
        ON {}.authored_thermal_runs FOR EACH ROW
        EXECUTE FUNCTION {}.reject_authored_run_change()
    """).format(namespace, namespace))
