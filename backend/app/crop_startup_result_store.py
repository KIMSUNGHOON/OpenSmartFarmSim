"""Additive startup research schema; farm-bound custody follows this boundary."""
from psycopg import sql

from .runtime_roles import NAME

VERSION = 'crop-result-v3'
MAX_PACKET_BYTES = 20*1024*1024


def install_startup_crop_result_schema(conn,schema):
    """Provisioner-only fresh table before explicit runtime role grants."""
    if type(schema) is not str or not NAME.fullmatch(schema):raise ValueError('invalid startup crop schema')
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL('''
        CREATE TABLE {}.crop_startup_research_results (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            study_id text NOT NULL CHECK (length(study_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            result_id text NOT NULL CHECK (result_id ~ '^crop-result-v3:[0-9a-f]{{64}}$'),
            scenario_id text NOT NULL, scenario_revision text NOT NULL,
            registration_job_id uuid NOT NULL, registration_sha256 char(64) NOT NULL,
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 20971520),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
            integrity_signature char(64) NOT NULL CHECK (integrity_signature ~ '^[0-9a-f]{{64}}$'),
            registered_by text NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id,study_id,revision), UNIQUE (tenant_id,result_id),
            FOREIGN KEY (tenant_id,registration_job_id) REFERENCES {}.jobs (tenant_id,job_id),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'schema_version'='crop-result-v3') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'status'='stored_unpublished_research') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'claim_scope'='synthetic_crop_math_only') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'result_id'=result_id) IS TRUE)
        )
    ''').format(namespace,namespace))
    conn.execute(sql.SQL('''
        CREATE FUNCTION {}.reject_startup_crop_result_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'startup crop research result is immutable'; END $$
    ''').format(namespace))
    conn.execute(sql.SQL('''
        CREATE TRIGGER crop_startup_result_immutable BEFORE UPDATE OR DELETE ON {}.crop_startup_research_results
        FOR EACH ROW EXECUTE FUNCTION {}.reject_startup_crop_result_change()
    ''').format(namespace,namespace))
