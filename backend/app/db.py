"""Explicit PostgreSQL connection and installation; importing this module changes no schema."""

import os
from pathlib import Path
from typing import Mapping

import psycopg
from psycopg import sql
from psycopg.rows import dict_row


def connect_app(environ: Mapping[str, str] | None = None) -> psycopg.Connection:
    settings = os.environ if environ is None else environ
    password = settings.get("DB_PASSWORD")
    if password is None and settings.get("DB_PASSWORD_FILE"):
        password = Path(settings["DB_PASSWORD_FILE"]).read_text(encoding="utf-8").rstrip("\r\n")
    return psycopg.connect(
        host=settings.get("DB_HOST", "localhost"),
        port=settings.get("DB_PORT", "5432"),
        dbname=settings["DB_NAME"],
        user=settings["DB_USER"],
        password=password,
        row_factory=dict_row,
    )


def install_schema(conn: psycopg.Connection, schema: str) -> None:
    """Install v1 tables into an existing, explicitly selected schema."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.jobs (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            job_id uuid NOT NULL,
            stage text NOT NULL CHECK (stage IN ('research','collection','collection_review','simulation','assessment')),
            input_sha256 char(64) NOT NULL CHECK (input_sha256 ~ '^[0-9a-f]{{64}}$'),
            input_bytes bytea NOT NULL CHECK (octet_length(input_bytes) BETWEEN 1 AND 65536),
            CONSTRAINT jobs_input_digest_matches
                CHECK (encode(sha256(input_bytes), 'hex') = input_sha256),
            idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 200),
            state text NOT NULL CHECK (state IN ('queued','researching','collecting','reviewing','simulating','assessing','succeeded','hold','failed','canceled')),
            attempt_count integer NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
            max_attempts integer NOT NULL CHECK (max_attempts BETWEEN 1 AND 3),
            next_attempt_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            cancel_requested boolean NOT NULL DEFAULT false,
            lease_token text,
            lease_until timestamptz,
            reason jsonb,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            updated_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id),
            UNIQUE (tenant_id, stage, input_sha256, idempotency_key),
            CHECK (attempt_count <= max_attempts),
            CHECK (state IN ('queued','succeeded','hold','failed','canceled') OR
                   (stage = 'research' AND state = 'researching') OR
                   (stage = 'collection' AND state = 'collecting') OR
                   (stage = 'collection_review' AND state = 'reviewing') OR
                   (stage = 'simulation' AND state = 'simulating') OR
                   (stage = 'assessment' AND state = 'assessing')),
            CHECK ((state IN ('researching','collecting','reviewing','simulating','assessing')) =
                   (lease_token IS NOT NULL AND lease_until IS NOT NULL))
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.job_attempts (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            attempt integer NOT NULL CHECK (attempt > 0),
            lease_token text NOT NULL,
            started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id) REFERENCES {}.jobs (tenant_id, job_id)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.job_events (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            event_id uuid NOT NULL, attempt integer,
            kind text NOT NULL,
            reason jsonb,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, event_id),
            FOREIGN KEY (tenant_id, job_id) REFERENCES {}.jobs (tenant_id, job_id),
            FOREIGN KEY (tenant_id, job_id, attempt) REFERENCES {}.job_attempts (tenant_id, job_id, attempt)
        )
    """).format(namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.ai_decisions (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            attempt integer NOT NULL, decision_id uuid NOT NULL,
            output_sha256 char(64) NOT NULL CHECK (output_sha256 ~ '^[0-9a-f]{{64}}$'),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt, decision_id),
            FOREIGN KEY (tenant_id, job_id, attempt) REFERENCES {}.job_attempts (tenant_id, job_id, attempt)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.job_publications (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            publication_id uuid NOT NULL,
            attempt integer NOT NULL, decision_id uuid,
            artifact_sha256 char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{{64}}$'),
            artifact_size bigint NOT NULL CHECK (artifact_size >= 0),
            manifest jsonb NOT NULL,
            published_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id),
            UNIQUE (publication_id),
            FOREIGN KEY (tenant_id, job_id) REFERENCES {}.jobs (tenant_id, job_id),
            FOREIGN KEY (tenant_id, job_id, attempt)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, decision_id)
                REFERENCES {}.ai_decisions (tenant_id, job_id, attempt, decision_id)
        )
    """).format(namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_audit_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'accepted publication and audit rows are immutable'; END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.guard_job_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'job history is immutable';
            END IF;
            IF OLD.state IN ('succeeded','hold','failed','canceled') THEN
                RAISE EXCEPTION 'terminal job is immutable';
            END IF;
            IF (OLD.tenant_id, OLD.job_id, OLD.stage, OLD.input_sha256, OLD.input_bytes, OLD.idempotency_key,
                OLD.max_attempts) IS DISTINCT FROM
               (NEW.tenant_id, NEW.job_id, NEW.stage, NEW.input_sha256, NEW.input_bytes, NEW.idempotency_key,
                NEW.max_attempts) THEN
                RAISE EXCEPTION 'job identity is immutable';
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER guard_change BEFORE UPDATE OR DELETE ON {}.jobs
        FOR EACH ROW EXECUTE FUNCTION {}.guard_job_change()
    """).format(namespace, namespace))
    for table in ("job_attempts", "job_events", "ai_decisions", "job_publications"):
        conn.execute(sql.SQL("""
            CREATE TRIGGER reject_change BEFORE UPDATE OR DELETE ON {}.{}
            FOR EACH ROW EXECUTE FUNCTION {}.reject_audit_change()
        """).format(namespace, sql.Identifier(table), namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_publication_pair() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE
            row_tenant text;
            row_job uuid;
            job_state text;
            job_stage text;
            publication_count bigint;
            publication_decision uuid;
        BEGIN
            IF TG_OP = 'DELETE' THEN
                row_tenant := OLD.tenant_id;
                row_job := OLD.job_id;
            ELSE
                row_tenant := NEW.tenant_id;
                row_job := NEW.job_id;
            END IF;
            SELECT state, stage INTO job_state, job_stage FROM {}.jobs
                WHERE tenant_id = row_tenant AND job_id = row_job;
            SELECT count(*) INTO publication_count FROM {}.job_publications
                WHERE tenant_id = row_tenant AND job_id = row_job;
            IF publication_count = 1 THEN
                SELECT decision_id INTO publication_decision FROM {}.job_publications
                    WHERE tenant_id = row_tenant AND job_id = row_job;
                IF (job_stage IN ('collection', 'simulation') AND publication_decision IS NOT NULL)
                   OR (job_stage IN ('research', 'collection_review', 'assessment')
                       AND publication_decision IS NULL) THEN
                    RAISE EXCEPTION 'publication decision is incompatible with job stage'
                        USING ERRCODE = '23514';
                END IF;
            END IF;
            IF (job_state = 'succeeded') IS DISTINCT FROM (publication_count = 1) THEN
                RAISE EXCEPTION 'job is succeeded iff exactly one publication exists'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END
        $$
    """).format(namespace, namespace, namespace, namespace))
    for table in ("jobs", "job_publications"):
        conn.execute(sql.SQL("""
            CREATE CONSTRAINT TRIGGER check_publication_pair
            AFTER INSERT OR UPDATE OR DELETE ON {}.{}
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION {}.check_publication_pair()
        """).format(namespace, sql.Identifier(table), namespace))
