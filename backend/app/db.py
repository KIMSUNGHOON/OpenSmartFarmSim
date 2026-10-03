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


def upgrade_job_intent_key(conn: psycopg.Connection, schema: str) -> None:
    """Upgrade an installed job table before running code that names jobs_intent_key.

    This is an explicit, owner-run migration. Conflicting historical intents require
    operator reconciliation; the migration never discards or rewrites jobs.
    """
    table = sql.Identifier(schema, "jobs")
    with conn.transaction():
        conn.execute(sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(table))
        exists = conn.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_constraint c
                JOIN pg_class t ON t.oid = c.conrelid
                JOIN pg_namespace n ON n.oid = t.relnamespace
                WHERE n.nspname = %s AND t.relname = 'jobs'
                  AND c.conname = 'jobs_intent_key' AND c.contype = 'u'
            ) AS present
        """, (schema,)).fetchone()["present"]
        if exists:
            return
        duplicate = conn.execute(sql.SQL("""
            SELECT 1 FROM {} GROUP BY tenant_id, stage, idempotency_key
            HAVING count(*) > 1 LIMIT 1
        """).format(table)).fetchone()
        if duplicate is not None:
            raise ValueError("job intent key migration requires duplicate reconciliation")
        conn.execute(sql.SQL("""
            ALTER TABLE {} ADD CONSTRAINT jobs_intent_key
                UNIQUE (tenant_id, stage, idempotency_key)
        """).format(table))


def upgrade_cli_model_policy(conn: psycopg.Connection, schema: str) -> None:
    """Owner-run model cutover; retain immutable historical invocation rows."""
    _replace_cli_model_policy(conn, schema, "gpt-6-sol", "gpt-6.1-sol")


def downgrade_cli_model_policy(conn: psycopg.Connection, schema: str) -> None:
    """Restore the previous write policy without changing later audit records."""
    _replace_cli_model_policy(conn, schema, "gpt-6.1-sol", "gpt-6-sol")


def _replace_cli_model_policy(conn, schema, previous_model, target_model):
    # PostgreSQL's stored expression for the known installed CHECK contract.
    expression = (
        "(((execution_kind = 'codex_cli'::text) AND "
        "(cli_version ~ '^codex-cli [0-9]+[.][0-9]+[.][0-9]+$'::text) AND "
        "(NOT (model IS DISTINCT FROM '{model}'::text)) AND "
        "(NOT (reasoning_effort IS DISTINCT FROM 'xhigh'::text))) OR "
        "((execution_kind = 'synthetic_fixture'::text) AND "
        "(cli_version = 'synthetic_fixture'::text) AND "
        "(model IS NULL) AND (reasoning_effort IS NULL)))"
    )
    table = sql.Identifier(schema, "attempt_invocations")
    with conn.transaction():
        conn.execute(sql.SQL("LOCK TABLE {} IN ACCESS EXCLUSIVE MODE").format(table))
        policies = conn.execute("""
            SELECT c.conname, pg_get_expr(c.conbin, c.conrelid) AS expression
            FROM pg_constraint c
            JOIN pg_class t ON t.oid = c.conrelid
            JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE n.nspname = %s AND t.relname = 'attempt_invocations'
              AND c.contype = 'c' AND EXISTS (
                  SELECT 1 FROM pg_attribute a WHERE a.attrelid = t.oid
                    AND a.attnum = ANY(c.conkey)
                    AND a.attname IN ('model', 'reasoning_effort'))
        """, (schema,)).fetchall()
        if (len(policies) != 1 or policies[0]["conname"] not in
                ("attempt_invocations_check", "attempt_invocations_cli_policy")):
            raise ValueError("CLI model migration requires the known invocation policy")
        policy = policies[0]
        if policy["expression"] == expression.format(model=target_model):
            return
        if policy["expression"] != expression.format(model=previous_model):
            raise ValueError("CLI model migration requires the known invocation policy")
        conn.execute(sql.SQL("ALTER TABLE {} DROP CONSTRAINT {}").format(
            table, sql.Identifier(policy["conname"])))
        conn.execute(sql.SQL("""
            ALTER TABLE {} ADD CONSTRAINT attempt_invocations_cli_policy CHECK (
                (execution_kind = 'codex_cli'
                 AND cli_version ~ '^codex-cli [0-9]+[.][0-9]+[.][0-9]+$'
                 AND model IS NOT DISTINCT FROM {}
                 AND reasoning_effort IS NOT DISTINCT FROM 'xhigh')
                OR (execution_kind = 'synthetic_fixture'
                    AND cli_version = 'synthetic_fixture'
                    AND model IS NULL AND reasoning_effort IS NULL)) NOT VALID
        """).format(table, sql.Literal(target_model)))


def install_market_hold_schema(conn: psycopg.Connection, schema: str) -> None:
    """Owner-run, additive installation after the shared decision-context table."""
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL("""
        CREATE TABLE {}.market_hold_reports (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            hold_report_id text NOT NULL CHECK (length(hold_report_id) BETWEEN 1 AND 200),
            snapshot_id text NOT NULL CHECK (length(snapshot_id) BETWEEN 1 AND 200),
            decision_context_id text NOT NULL CHECK (length(decision_context_id) BETWEEN 1 AND 200),
            intent_sha256 char(64) NOT NULL CHECK (intent_sha256 ~ '^[0-9a-f]{{64}}$'),
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 16384),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256 ~ '^[0-9a-f]{{64}}$'),
            signature char(64) NOT NULL CHECK (signature ~ '^[0-9a-f]{{64}}$'),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, hold_report_id),
            UNIQUE (tenant_id, intent_sha256),
            FOREIGN KEY (tenant_id, snapshot_id, decision_context_id)
                REFERENCES {}.decision_contexts (tenant_id, snapshot_id, decision_context_id),
            FOREIGN KEY (tenant_id, snapshot_id)
                REFERENCES {}.thermal_input_snapshots (tenant_id, snapshot_id),
            CHECK (payload_sha256 = encode(sha256(payload_raw), 'hex')),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'tenant_id') = tenant_id) IS TRUE),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'hold_report_id') = hold_report_id) IS TRUE),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'snapshot_id') = snapshot_id) IS TRUE),
            CHECK (((convert_from(payload_raw, 'UTF8')::jsonb->>'decision_context_id') =
                    decision_context_id) IS TRUE)
        )
    """).format(namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE INDEX market_hold_by_context ON {}.market_hold_reports
            (tenant_id, decision_context_id, recorded_at)
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.reject_market_hold_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'market hold reports are immutable'; END
        $$
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER market_hold_immutable BEFORE UPDATE OR DELETE ON {}.market_hold_reports
        FOR EACH ROW EXECUTE FUNCTION {}.reject_market_hold_change()
    """).format(namespace, namespace))


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
            CONSTRAINT jobs_intent_key UNIQUE (tenant_id, stage, idempotency_key),
            CHECK (attempt_count <= max_attempts),
            CHECK (state NOT IN ('researching','collecting','reviewing','simulating','assessing')
                   OR attempt_count > 0),
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
            attempt_id uuid NOT NULL UNIQUE,
            lease_token_sha256 char(64) NOT NULL CHECK (lease_token_sha256 ~ '^[0-9a-f]{{64}}$'),
            started_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            UNIQUE (tenant_id, job_id, attempt, attempt_id),
            FOREIGN KEY (tenant_id, job_id) REFERENCES {}.jobs (tenant_id, job_id)
        )
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.evidence_authorizations (
            authorization_id uuid PRIMARY KEY,
            tenant_id text NOT NULL,
            source_id text NOT NULL CHECK (length(source_id) BETWEEN 1 AND 200),
            intended_use text NOT NULL CHECK (length(intended_use) BETWEEN 1 AND 200),
            payload_sha256 char(64) CHECK (payload_sha256 ~ '^[0-9a-f]{{64}}$'),
            rights_proof_id text NOT NULL CHECK (length(rights_proof_id) BETWEEN 1 AND 200),
            rights_version text NOT NULL CHECK (length(rights_version) BETWEEN 1 AND 200),
            policy_version text NOT NULL CHECK (length(policy_version) BETWEEN 1 AND 200),
            classification text NOT NULL CHECK (classification IN ('private','restricted')),
            read_scope text NOT NULL CHECK (read_scope IN ('auditor','none')),
            retain_raw boolean NOT NULL,
            retain_digest boolean NOT NULL,
            CHECK (NOT retain_raw OR retain_digest),
            CHECK ((retain_digest AND payload_sha256 IS NOT NULL)
                OR (NOT retain_digest AND payload_sha256 IS NULL)),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp()
        )
    """).format(namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.attempt_evidence (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            attempt integer NOT NULL, evidence_id uuid NOT NULL,
            kind text NOT NULL CHECK (kind IN
                ('prompt','output_schema','final_output','jsonl','tool_event','launch_event','validation_report')),
            sequence integer NOT NULL CHECK (sequence >= 0),
            late boolean NOT NULL,
            classification text NOT NULL CHECK (classification IN ('private','restricted')),
            rights_ref text NOT NULL CHECK (length(rights_ref) BETWEEN 1 AND 200),
            policy_version text NOT NULL CHECK (length(policy_version) BETWEEN 1 AND 200),
            authorization_id uuid NOT NULL REFERENCES {}.evidence_authorizations (authorization_id),
            receipt_state text NOT NULL CHECK (receipt_state IN
                ('retained','received_but_withheld','not_received')),
            sha256 char(64) CHECK (sha256 ~ '^[0-9a-f]{{64}}$'),
            size bigint CHECK (size BETWEEN 0 AND 10485760),
            withhold_reason text CHECK (withhold_reason ~ '^[a-z][a-z0-9_]{{0,63}}$'),
            hash_withheld_reason text CHECK (hash_withheld_reason ~ '^[a-z][a-z0-9_]{{0,63}}$'),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt, evidence_id),
            UNIQUE (evidence_id),
            UNIQUE (tenant_id, job_id, attempt, kind, sequence),
            FOREIGN KEY (tenant_id, job_id, attempt)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt),
            CHECK ((receipt_state = 'retained' AND sha256 IS NOT NULL AND size IS NOT NULL
                    AND withhold_reason IS NULL AND hash_withheld_reason IS NULL)
                OR (receipt_state = 'received_but_withheld' AND size IS NULL
                    AND withhold_reason IS NOT NULL
                    AND ((sha256 IS NOT NULL AND hash_withheld_reason IS NULL)
                         OR (sha256 IS NULL AND hash_withheld_reason IS NOT NULL)))
                OR (receipt_state = 'not_received' AND sha256 IS NULL AND size IS NULL
                    AND withhold_reason IS NOT NULL AND hash_withheld_reason IS NULL)),
            CHECK (kind != 'final_output' OR size IS NULL OR size <= 1048576)
        )
    """).format(namespace, namespace, namespace))
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
        CREATE TABLE {}.attempt_invocations (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            attempt integer NOT NULL, attempt_id uuid NOT NULL,
            input_sha256 char(64) NOT NULL CHECK (input_sha256 ~ '^[0-9a-f]{{64}}$'),
            prompt_evidence_id uuid NOT NULL,
            prompt_version text NOT NULL CHECK (length(prompt_version) BETWEEN 1 AND 200),
            prompt_sha256 char(64) NOT NULL CHECK (prompt_sha256 ~ '^[0-9a-f]{{64}}$'),
            schema_evidence_id uuid NOT NULL,
            schema_version text NOT NULL CHECK (length(schema_version) BETWEEN 1 AND 200),
            schema_sha256 char(64) NOT NULL CHECK (schema_sha256 ~ '^[0-9a-f]{{64}}$'),
            execution_kind text NOT NULL CHECK (execution_kind IN ('codex_cli','synthetic_fixture')),
            cli_version text NOT NULL,
            model text, reasoning_effort text,
            created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt, attempt_id),
            FOREIGN KEY (tenant_id, job_id, attempt, prompt_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            FOREIGN KEY (tenant_id, job_id, attempt, schema_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            CONSTRAINT attempt_invocations_cli_policy CHECK (
                (execution_kind = 'codex_cli' AND cli_version ~ '^codex-cli [0-9]+[.][0-9]+[.][0-9]+$'
                    AND model IS NOT DISTINCT FROM 'gpt-6.1-sol'
                    AND reasoning_effort IS NOT DISTINCT FROM 'xhigh')
                OR (execution_kind = 'synthetic_fixture' AND cli_version = 'synthetic_fixture'
                    AND model IS NULL AND reasoning_effort IS NULL))
        )
    """).format(namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.attempt_cli_launches (
            tenant_id text NOT NULL, job_id uuid NOT NULL, attempt integer NOT NULL,
            attempt_id uuid NOT NULL, launch_id uuid NOT NULL UNIQUE,
            launch_evidence_id uuid NOT NULL, executable text NOT NULL
                CHECK (length(executable) BETWEEN 1 AND 200),
            cli_version text NOT NULL, args_sha256 char(64) NOT NULL
                CHECK (args_sha256 ~ '^[0-9a-f]{{64}}$'),
            prompt_sha256 char(64) NOT NULL, schema_sha256 char(64) NOT NULL,
            process_id integer NOT NULL CHECK (process_id > 0),
            spawned_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            UNIQUE (tenant_id, job_id, attempt, attempt_id, launch_id),
            FOREIGN KEY (tenant_id, job_id, attempt)
                REFERENCES {}.attempt_invocations (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt, attempt_id),
            FOREIGN KEY (tenant_id, job_id, attempt, launch_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id)
        )
    """).format(namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.attempt_cli_captures (
            tenant_id text NOT NULL, job_id uuid NOT NULL, attempt integer NOT NULL,
            attempt_id uuid NOT NULL, launch_id uuid NOT NULL, capture_id uuid NOT NULL UNIQUE,
            jsonl_evidence_id uuid, jsonl_sha256 char(64),
            final_output_sha256 char(64) NOT NULL CHECK (final_output_sha256 ~ '^[0-9a-f]{{64}}$'),
            exit_code integer CHECK (exit_code BETWEEN 0 AND 255),
            termination_reason text NOT NULL CHECK (termination_reason ~ '^[a-z][a-z0-9_]{{0,63}}$'),
            usage jsonb,
            completed boolean NOT NULL,
            sealed_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            UNIQUE (tenant_id, job_id, attempt, capture_id, jsonl_sha256),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id, launch_id)
                REFERENCES {}.attempt_cli_launches (tenant_id, job_id, attempt, attempt_id, launch_id),
            FOREIGN KEY (tenant_id, job_id, attempt, jsonl_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            CHECK (jsonl_evidence_id IS NOT NULL OR jsonl_sha256 IS NULL)
        )
    """).format(namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.validation_receipts (
            tenant_id text NOT NULL, job_id uuid NOT NULL, attempt integer NOT NULL,
            attempt_id uuid NOT NULL, receipt_id uuid NOT NULL UNIQUE,
            final_evidence_id uuid NOT NULL, validation_evidence_id uuid NOT NULL,
            report_sha256 char(64) NOT NULL,
            output_sha256 char(64) NOT NULL,
            artifact_sha256 char(64) NOT NULL,
            input_sha256 char(64) NOT NULL,
            prompt_evidence_id uuid NOT NULL, schema_evidence_id uuid NOT NULL,
            prompt_sha256 char(64) NOT NULL, schema_sha256 char(64) NOT NULL,
            prompt_version text NOT NULL, schema_version text NOT NULL,
            execution_kind text NOT NULL, cli_version text NOT NULL,
            model text, reasoning_effort text,
            disposition text NOT NULL DEFAULT 'proceed' CHECK (disposition IN ('proceed','hold')),
            capture_id uuid, capture_sha256 char(64),
            stage text NOT NULL, validator_version text NOT NULL,
            validator_code text NOT NULL, passed boolean NOT NULL CHECK (passed),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt, attempt_id),
            FOREIGN KEY (tenant_id, job_id, attempt, final_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            FOREIGN KEY (tenant_id, job_id, attempt, validation_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            FOREIGN KEY (tenant_id, job_id, attempt, capture_id, capture_sha256)
                REFERENCES {}.attempt_cli_captures (tenant_id, job_id, attempt, capture_id, jsonl_sha256),
            CHECK ((execution_kind = 'codex_cli' AND capture_id IS NOT NULL AND capture_sha256 IS NOT NULL)
                OR (execution_kind = 'synthetic_fixture' AND capture_id IS NULL AND capture_sha256 IS NULL))
        )
    """).format(namespace, namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.ai_decisions (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            attempt integer NOT NULL, decision_id uuid NOT NULL,
            output_sha256 char(64) NOT NULL CHECK (output_sha256 ~ '^[0-9a-f]{{64}}$'),
            artifact_sha256 char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{{64}}$'),
            final_evidence_id uuid NOT NULL,
            validation_evidence_id uuid NOT NULL,
            receipt_id uuid NOT NULL REFERENCES {}.validation_receipts (receipt_id),
            disposition text NOT NULL DEFAULT 'proceed' CHECK (disposition IN ('proceed','hold')),
            capture_id uuid, capture_sha256 char(64),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            UNIQUE (tenant_id, job_id, attempt, decision_id),
            FOREIGN KEY (tenant_id, job_id, attempt) REFERENCES {}.job_attempts (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, final_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            FOREIGN KEY (tenant_id, job_id, attempt, validation_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id),
            FOREIGN KEY (tenant_id, job_id, attempt, capture_id, capture_sha256)
                REFERENCES {}.attempt_cli_captures (tenant_id, job_id, attempt, capture_id, jsonl_sha256)
        )
    """).format(namespace, namespace, namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.job_hold_reports (
            tenant_id text NOT NULL, job_id uuid NOT NULL, attempt integer NOT NULL,
            attempt_id uuid NOT NULL, decision_id uuid NOT NULL, receipt_id uuid NOT NULL,
            hold_id uuid NOT NULL UNIQUE, report_sha256 char(64) NOT NULL,
            report_size integer NOT NULL CHECK (report_size BETWEEN 1 AND 16384),
            authorization_id uuid NOT NULL REFERENCES {}.evidence_authorizations (authorization_id),
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt, attempt_id),
            FOREIGN KEY (tenant_id, job_id, attempt, decision_id)
                REFERENCES {}.ai_decisions (tenant_id, job_id, attempt, decision_id),
            FOREIGN KEY (receipt_id) REFERENCES {}.validation_receipts (receipt_id)
        )
    """).format(namespace, namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TABLE {}.attempt_outcomes (
            tenant_id text NOT NULL, job_id uuid NOT NULL,
            attempt integer NOT NULL, attempt_id uuid NOT NULL UNIQUE,
            state text NOT NULL CHECK (state IN
                ('queued','succeeded','hold','failed','canceled','lease_expired')),
            reason jsonb,
            decision_id uuid,
            exit_code integer CHECK (exit_code BETWEEN 0 AND 255),
            termination_reason text CHECK (termination_reason ~ '^[a-z][a-z0-9_]{{0,63}}$'),
            usage jsonb,
            jsonl_evidence_id uuid,
            ended_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, job_id, attempt),
            FOREIGN KEY (tenant_id, job_id, attempt, attempt_id)
                REFERENCES {}.job_attempts (tenant_id, job_id, attempt, attempt_id),
            FOREIGN KEY (tenant_id, job_id, attempt, decision_id)
                REFERENCES {}.ai_decisions (tenant_id, job_id, attempt, decision_id),
            FOREIGN KEY (tenant_id, job_id, attempt, jsonl_evidence_id)
                REFERENCES {}.attempt_evidence (tenant_id, job_id, attempt, evidence_id)
        )
    """).format(namespace, namespace, namespace, namespace))
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
    for table in ("job_attempts", "job_events", "evidence_authorizations", "attempt_evidence", "attempt_invocations",
                  "attempt_cli_launches", "attempt_cli_captures", "validation_receipts", "ai_decisions",
                  "attempt_outcomes", "job_publications", "job_hold_reports"):
        conn.execute(sql.SQL("""
            CREATE TRIGGER reject_change BEFORE UPDATE OR DELETE ON {}.{}
            FOR EACH ROW EXECUTE FUNCTION {}.reject_audit_change()
        """).format(namespace, sql.Identifier(table), namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_evidence_authorization() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE auth_row record;
        BEGIN
            SELECT * INTO auth_row FROM {}.evidence_authorizations
                WHERE authorization_id = NEW.authorization_id;
            IF auth_row.tenant_id IS DISTINCT FROM NEW.tenant_id
               OR auth_row.classification IS DISTINCT FROM NEW.classification
               OR auth_row.rights_proof_id IS DISTINCT FROM NEW.rights_ref
               OR auth_row.policy_version IS DISTINCT FROM NEW.policy_version
               OR (NEW.receipt_state = 'retained' AND
                   (auth_row.retain_raw IS DISTINCT FROM true
                    OR auth_row.payload_sha256 IS DISTINCT FROM NEW.sha256))
               OR (NEW.receipt_state = 'received_but_withheld' AND
                   ((auth_row.retain_digest AND
                     (auth_row.payload_sha256 IS NULL
                      OR NEW.sha256 IS DISTINCT FROM auth_row.payload_sha256))
                    OR (NOT auth_row.retain_digest AND
                        (auth_row.payload_sha256 IS NOT NULL OR NEW.sha256 IS NOT NULL))))
               OR (NEW.receipt_state = 'not_received' AND auth_row.payload_sha256 IS NOT NULL) THEN
                RAISE EXCEPTION 'evidence requires matching authorization snapshot'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER check_evidence_authorization BEFORE INSERT ON {}.attempt_evidence
        FOR EACH ROW EXECUTE FUNCTION {}.check_evidence_authorization()
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_invocation_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE prompt_row record; schema_row record; job_row record; recorded_attempt_id uuid;
        BEGIN
            SELECT stage, state, attempt_count, cancel_requested, lease_until,
                   input_sha256 INTO job_row FROM {}.jobs
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id;
            SELECT attempt_id INTO recorded_attempt_id FROM {}.job_attempts
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id AND attempt = NEW.attempt;
            SELECT kind, late, sha256, receipt_state INTO prompt_row FROM {}.attempt_evidence
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                  AND attempt = NEW.attempt AND evidence_id = NEW.prompt_evidence_id;
            SELECT kind, late, sha256, receipt_state INTO schema_row FROM {}.attempt_evidence
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                  AND attempt = NEW.attempt AND evidence_id = NEW.schema_evidence_id;
            IF job_row.stage NOT IN ('research','collection_review','assessment')
               OR job_row.state NOT IN ('researching','reviewing','assessing')
               OR job_row.attempt_count IS DISTINCT FROM NEW.attempt
               OR job_row.cancel_requested IS DISTINCT FROM false
               OR (job_row.lease_until > clock_timestamp()) IS DISTINCT FROM true
               OR job_row.input_sha256 IS DISTINCT FROM NEW.input_sha256
               OR recorded_attempt_id IS DISTINCT FROM NEW.attempt_id
               OR prompt_row.kind IS DISTINCT FROM 'prompt' OR prompt_row.late IS DISTINCT FROM false
               OR prompt_row.receipt_state IS DISTINCT FROM 'retained'
               OR prompt_row.sha256 IS DISTINCT FROM NEW.prompt_sha256
               OR schema_row.kind IS DISTINCT FROM 'output_schema' OR schema_row.late IS DISTINCT FROM false
               OR schema_row.receipt_state IS DISTINCT FROM 'retained'
               OR schema_row.sha256 IS DISTINCT FROM NEW.schema_sha256 THEN
                RAISE EXCEPTION 'invocation needs retained current prompt and output schema'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace, namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER check_invocation_evidence BEFORE INSERT ON {}.attempt_invocations
        FOR EACH ROW EXECUTE FUNCTION {}.check_invocation_evidence()
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_outcome_metadata() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE jsonl_row record; invocation_row record; capture_row record;
                recovery_code text;
        BEGIN
            IF NEW.state = 'lease_expired' THEN
                recovery_code := 'lease_expired';
            ELSIF NEW.state = 'canceled'
                  AND NEW.reason = '{{"code":"cancel_lease_expired"}}'::jsonb THEN
                recovery_code := 'cancel_lease_expired';
            ELSIF NEW.state = 'failed'
                  AND NEW.reason = '{{"code":"attempts_exhausted"}}'::jsonb THEN
                recovery_code := 'attempts_exhausted';
            END IF;
            IF recovery_code IS NOT NULL AND
               (NEW.reason->>'code' IS DISTINCT FROM recovery_code
                OR NEW.termination_reason IS DISTINCT FROM recovery_code
                OR NEW.exit_code IS NOT NULL OR NEW.usage IS NOT NULL) THEN
                RAISE EXCEPTION 'recovered attempt outcome must retain closure reason and unknown process status'
                    USING ERRCODE = '23514';
            END IF;
            SELECT execution_kind INTO invocation_row FROM {}.attempt_invocations
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id AND attempt = NEW.attempt;
            IF invocation_row.execution_kind = 'codex_cli' THEN
                SELECT * INTO capture_row FROM {}.attempt_cli_captures
                    WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id AND attempt = NEW.attempt;
                IF capture_row.capture_id IS NULL THEN
                    IF NEW.exit_code IS NOT NULL OR NEW.usage IS NOT NULL
                       OR (recovery_code IS NULL AND NEW.termination_reason IS NOT NULL)
                       OR NEW.state = 'succeeded'
                       OR NEW.reason->>'code' = 'ai_validated_hold' THEN
                        RAISE EXCEPTION 'uncaptured CLI outcome cannot claim process status'
                            USING ERRCODE = '23514';
                    END IF;
                ELSE
                    IF NEW.jsonl_evidence_id IS DISTINCT FROM capture_row.jsonl_evidence_id
                       OR (recovery_code IS NULL AND
                           (NEW.exit_code IS DISTINCT FROM capture_row.exit_code
                            OR NEW.usage IS DISTINCT FROM capture_row.usage
                            OR NEW.termination_reason IS DISTINCT FROM capture_row.termination_reason))
                       OR (NEW.state = 'succeeded' AND
                           (capture_row.completed IS DISTINCT FROM true OR capture_row.exit_code IS DISTINCT FROM 0))
                       OR (NEW.reason->>'code' = 'ai_validated_hold' AND
                           (capture_row.completed IS DISTINCT FROM true OR capture_row.exit_code IS DISTINCT FROM 0)) THEN
                        RAISE EXCEPTION 'CLI outcome must match sealed capture' USING ERRCODE = '23514';
                    END IF;
                END IF;
            END IF;
            IF NEW.jsonl_evidence_id IS NOT NULL THEN
                SELECT kind, late INTO jsonl_row FROM {}.attempt_evidence
                    WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                      AND attempt = NEW.attempt AND evidence_id = NEW.jsonl_evidence_id;
                IF jsonl_row.kind IS DISTINCT FROM 'jsonl' OR jsonl_row.late IS DISTINCT FROM false THEN
                    RAISE EXCEPTION 'outcome JSONL must belong to current attempt and be nonlate'
                        USING ERRCODE = '23514';
                END IF;
            END IF;
            IF NEW.usage IS NOT NULL THEN
                IF jsonb_typeof(NEW.usage) IS DISTINCT FROM 'object' OR NEW.usage = '{{}}'::jsonb THEN
                    RAISE EXCEPTION 'usage must be a nonempty token count object'
                        USING ERRCODE = '23514';
                END IF;
                IF EXISTS (SELECT 1 FROM jsonb_each(NEW.usage) AS item(key, value)
                    WHERE item.key NOT IN ('input_tokens','output_tokens','total_tokens',
                                           'cached_input_tokens','cache_write_input_tokens',
                                           'reasoning_output_tokens')
                       OR jsonb_typeof(item.value) IS DISTINCT FROM 'number'
                       OR item.value::text !~ '^(0|[1-9][0-9]{{0,18}})$'
                       OR item.value::numeric > 9223372036854775807) THEN
                    RAISE EXCEPTION 'usage contains invalid token counts'
                        USING ERRCODE = '23514';
                END IF;
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER check_outcome_metadata BEFORE INSERT ON {}.attempt_outcomes
        FOR EACH ROW EXECUTE FUNCTION {}.check_outcome_metadata()
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_cli_bridge() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE invocation_row record; launch_row record; evidence_row record; job_row record;
        BEGIN
            SELECT * INTO invocation_row FROM {}.attempt_invocations
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id AND attempt = NEW.attempt;
            SELECT * INTO job_row FROM {}.jobs
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id FOR UPDATE;
            IF invocation_row.execution_kind IS DISTINCT FROM 'codex_cli'
               OR job_row.attempt_count IS DISTINCT FROM NEW.attempt
               OR job_row.state NOT IN ('researching','reviewing','assessing')
               OR job_row.cancel_requested IS DISTINCT FROM false
               OR (job_row.lease_until > clock_timestamp()) IS DISTINCT FROM true
               OR invocation_row.attempt_id IS DISTINCT FROM NEW.attempt_id THEN
                RAISE EXCEPTION 'CLI bridge needs live matching invocation' USING ERRCODE = '23514';
            END IF;
            IF TG_TABLE_NAME = 'attempt_cli_launches' THEN
                SELECT * INTO evidence_row FROM {}.attempt_evidence WHERE tenant_id = NEW.tenant_id
                    AND job_id = NEW.job_id AND attempt = NEW.attempt
                    AND evidence_id = NEW.launch_evidence_id;
                IF evidence_row.kind IS DISTINCT FROM 'launch_event' OR evidence_row.late
                   OR evidence_row.receipt_state IS DISTINCT FROM 'retained'
                   OR NEW.cli_version IS DISTINCT FROM invocation_row.cli_version
                   OR NEW.prompt_sha256 IS DISTINCT FROM invocation_row.prompt_sha256
                   OR NEW.schema_sha256 IS DISTINCT FROM invocation_row.schema_sha256 THEN
                    RAISE EXCEPTION 'CLI launch evidence mismatch' USING ERRCODE = '23514';
                END IF;
            ELSE
                SELECT * INTO launch_row FROM {}.attempt_cli_launches WHERE tenant_id = NEW.tenant_id
                    AND job_id = NEW.job_id AND attempt = NEW.attempt AND launch_id = NEW.launch_id;
                IF launch_row.attempt_id IS DISTINCT FROM NEW.attempt_id THEN
                    RAISE EXCEPTION 'CLI capture launch mismatch' USING ERRCODE = '23514';
                END IF;
                IF NEW.jsonl_evidence_id IS NOT NULL THEN
                    SELECT * INTO evidence_row FROM {}.attempt_evidence WHERE tenant_id = NEW.tenant_id
                        AND job_id = NEW.job_id AND attempt = NEW.attempt
                        AND evidence_id = NEW.jsonl_evidence_id;
                    IF evidence_row.kind IS DISTINCT FROM 'jsonl' OR evidence_row.late
                       OR (evidence_row.receipt_state = 'retained' AND
                           (NEW.jsonl_sha256 IS NULL OR
                            evidence_row.sha256 IS DISTINCT FROM NEW.jsonl_sha256))
                       OR (evidence_row.receipt_state <> 'retained' AND
                           NEW.jsonl_sha256 IS NOT NULL) THEN
                        RAISE EXCEPTION 'CLI capture JSONL mismatch' USING ERRCODE = '23514';
                    END IF;
                END IF;
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace, namespace, namespace, namespace, namespace, namespace))
    for table in ("attempt_cli_launches", "attempt_cli_captures"):
        conn.execute(sql.SQL("""
            CREATE TRIGGER check_cli_bridge BEFORE INSERT ON {}.{}
            FOR EACH ROW EXECUTE FUNCTION {}.check_cli_bridge()
        """).format(namespace, sql.Identifier(table), namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_decision_evidence() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE final_row record; report_row record; job_row record;
                receipt_row record; invocation_row record;
        BEGIN
            SELECT stage, state, attempt_count, cancel_requested, lease_until,
                   input_sha256 INTO job_row FROM {}.jobs
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id FOR UPDATE;
            IF NOT FOUND THEN
                RAISE EXCEPTION 'decision needs retained current final output and validation report'
                    USING ERRCODE = '23514';
            END IF;
            IF job_row.stage NOT IN ('research','collection_review','assessment')
               OR job_row.state NOT IN ('researching','reviewing','assessing')
               OR job_row.attempt_count IS DISTINCT FROM NEW.attempt
               OR job_row.cancel_requested IS DISTINCT FROM false
               OR (job_row.lease_until > clock_timestamp()) IS DISTINCT FROM true
               OR EXISTS (SELECT 1 FROM {}.attempt_outcomes
                   WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                     AND attempt = NEW.attempt) THEN
                RAISE EXCEPTION 'decision needs live current attempt'
                    USING ERRCODE = '23514';
            END IF;
            SELECT * INTO invocation_row FROM {}.attempt_invocations
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id AND attempt = NEW.attempt;
            SELECT kind, late, sha256, receipt_state INTO final_row FROM {}.attempt_evidence
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                  AND attempt = NEW.attempt AND evidence_id = NEW.final_evidence_id;
            SELECT kind, late, sha256, receipt_state INTO report_row FROM {}.attempt_evidence
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                  AND attempt = NEW.attempt AND evidence_id = NEW.validation_evidence_id;
            SELECT * INTO receipt_row FROM {}.validation_receipts
                WHERE tenant_id = NEW.tenant_id AND job_id = NEW.job_id
                  AND attempt = NEW.attempt AND receipt_id = NEW.receipt_id;
            IF invocation_row.attempt_id IS NULL
               OR receipt_row.passed IS DISTINCT FROM true
               OR receipt_row.attempt_id IS DISTINCT FROM invocation_row.attempt_id
               OR receipt_row.input_sha256 IS DISTINCT FROM job_row.input_sha256
               OR receipt_row.prompt_sha256 IS DISTINCT FROM invocation_row.prompt_sha256
               OR receipt_row.schema_sha256 IS DISTINCT FROM invocation_row.schema_sha256
               OR receipt_row.prompt_evidence_id IS DISTINCT FROM invocation_row.prompt_evidence_id
               OR receipt_row.schema_evidence_id IS DISTINCT FROM invocation_row.schema_evidence_id
               OR receipt_row.prompt_version IS DISTINCT FROM invocation_row.prompt_version
               OR receipt_row.schema_version IS DISTINCT FROM invocation_row.schema_version
               OR receipt_row.execution_kind IS DISTINCT FROM invocation_row.execution_kind
               OR receipt_row.cli_version IS DISTINCT FROM invocation_row.cli_version
               OR receipt_row.model IS DISTINCT FROM invocation_row.model
               OR receipt_row.reasoning_effort IS DISTINCT FROM invocation_row.reasoning_effort
               OR receipt_row.stage IS DISTINCT FROM job_row.stage
               OR receipt_row.disposition IS DISTINCT FROM NEW.disposition
               OR receipt_row.capture_id IS DISTINCT FROM NEW.capture_id
               OR receipt_row.capture_sha256 IS DISTINCT FROM NEW.capture_sha256
               OR (invocation_row.execution_kind = 'codex_cli' AND
                   (NEW.capture_id IS NULL OR NEW.capture_sha256 IS NULL OR
                    NOT EXISTS (SELECT 1 FROM {}.attempt_cli_captures c WHERE
                        c.tenant_id = NEW.tenant_id AND c.job_id = NEW.job_id
                        AND c.attempt = NEW.attempt AND c.capture_id = NEW.capture_id
                        AND c.jsonl_sha256 = NEW.capture_sha256
                        AND c.final_output_sha256 = NEW.output_sha256
                        AND c.completed AND c.exit_code = 0
                        AND c.termination_reason = 'completed')))
               OR receipt_row.final_evidence_id IS DISTINCT FROM NEW.final_evidence_id
               OR receipt_row.validation_evidence_id IS DISTINCT FROM NEW.validation_evidence_id
               OR receipt_row.report_sha256 IS DISTINCT FROM report_row.sha256
               OR receipt_row.output_sha256 IS DISTINCT FROM NEW.output_sha256
               OR receipt_row.artifact_sha256 IS DISTINCT FROM NEW.artifact_sha256
               OR final_row.kind IS DISTINCT FROM 'final_output' OR final_row.late
               OR final_row.sha256 IS DISTINCT FROM NEW.output_sha256
               OR final_row.receipt_state IS DISTINCT FROM 'retained'
               OR report_row.kind IS DISTINCT FROM 'validation_report' OR report_row.late
               OR report_row.sha256 IS NULL OR report_row.receipt_state IS DISTINCT FROM 'retained' THEN
                RAISE EXCEPTION 'decision needs retained current final output and validation report'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace, namespace, namespace, namespace, namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER check_decision_evidence BEFORE INSERT ON {}.ai_decisions
        FOR EACH ROW EXECUTE FUNCTION {}.check_decision_evidence()
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_hold_report() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE decision_row record; auth_row record;
        BEGIN
            SELECT d.*, r.attempt_id AS receipt_attempt_id, r.disposition AS receipt_disposition
              INTO decision_row FROM {}.ai_decisions d JOIN {}.validation_receipts r
                ON r.tenant_id = d.tenant_id AND r.job_id = d.job_id
                AND r.attempt = d.attempt AND r.receipt_id = d.receipt_id
             WHERE d.tenant_id = NEW.tenant_id AND d.job_id = NEW.job_id
               AND d.attempt = NEW.attempt AND d.decision_id = NEW.decision_id;
            SELECT * INTO auth_row FROM {}.evidence_authorizations
                WHERE authorization_id = NEW.authorization_id;
            IF decision_row.disposition IS DISTINCT FROM 'hold'
               OR decision_row.receipt_disposition IS DISTINCT FROM 'hold'
               OR decision_row.receipt_id IS DISTINCT FROM NEW.receipt_id
               OR decision_row.receipt_attempt_id IS DISTINCT FROM NEW.attempt_id
               OR decision_row.artifact_sha256 IS DISTINCT FROM NEW.report_sha256
               OR auth_row.tenant_id IS DISTINCT FROM NEW.tenant_id
               OR auth_row.payload_sha256 IS DISTINCT FROM NEW.report_sha256
               OR auth_row.retain_raw IS DISTINCT FROM true
               OR auth_row.read_scope IS DISTINCT FROM 'auditor' THEN
                RAISE EXCEPTION 'hold report needs matching validated hold and authorization'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NEW;
        END
        $$
    """).format(namespace, namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE TRIGGER check_hold_report BEFORE INSERT ON {}.job_hold_reports
        FOR EACH ROW EXECUTE FUNCTION {}.check_hold_report()
    """).format(namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.check_attempt_closure() RETURNS trigger LANGUAGE plpgsql AS $$
        DECLARE row_tenant text; row_job uuid; current_attempt integer;
                job_state text; job_reason jsonb; missing_count bigint; bad_prior_count bigint;
                total_count bigint;
                current_state text; publication_row record; current_decision uuid;
                hold_row record;
        BEGIN
            row_tenant := NEW.tenant_id; row_job := NEW.job_id;
            SELECT attempt_count, state, reason INTO current_attempt, job_state, job_reason FROM {}.jobs
                WHERE tenant_id = row_tenant AND job_id = row_job;
            SELECT count(*) INTO missing_count FROM {}.job_attempts a
                LEFT JOIN {}.attempt_outcomes o USING (tenant_id, job_id, attempt)
                WHERE a.tenant_id = row_tenant AND a.job_id = row_job
                  AND a.attempt < current_attempt AND o.attempt IS NULL;
            SELECT count(*) INTO bad_prior_count FROM {}.attempt_outcomes
                WHERE tenant_id = row_tenant AND job_id = row_job
                  AND attempt < current_attempt AND state NOT IN ('queued','lease_expired');
            SELECT count(*) INTO total_count FROM {}.job_attempts
                WHERE tenant_id = row_tenant AND job_id = row_job;
            SELECT state, decision_id INTO current_state, current_decision FROM {}.attempt_outcomes
                WHERE tenant_id = row_tenant AND job_id = row_job
                  AND attempt = current_attempt;
            SELECT attempt, decision_id INTO publication_row FROM {}.job_publications
                WHERE tenant_id = row_tenant AND job_id = row_job;
            SELECT attempt, decision_id INTO hold_row FROM {}.job_hold_reports
                WHERE tenant_id = row_tenant AND job_id = row_job;
            IF missing_count <> 0 OR bad_prior_count <> 0 OR total_count <> current_attempt OR
               (job_state IN ('researching','collecting','reviewing','simulating','assessing')
                    AND current_state IS NOT NULL) OR
               (job_state = 'queued' AND current_attempt > 0
                    AND current_state NOT IN ('queued','lease_expired')) OR
               (job_state = 'succeeded' AND
                    (current_state IS DISTINCT FROM 'succeeded'
                     OR publication_row.attempt IS DISTINCT FROM current_attempt
                     OR publication_row.decision_id IS DISTINCT FROM current_decision)) OR
               (job_state IN ('hold','failed') AND current_attempt > 0
                    AND current_state IS DISTINCT FROM job_state
                    AND NOT (job_state = 'hold' AND job_reason->>'code' = 'input_sha256_mismatch'
                             AND current_state IN ('queued','lease_expired'))) OR
               (job_state = 'canceled' AND current_attempt > 0
                    AND current_state IS DISTINCT FROM 'canceled'
                    AND NOT (current_state IN ('queued','lease_expired')
                             AND job_reason->>'code' = 'canceled_by_request')) OR
               (job_state IN ('queued','hold','failed','canceled','succeeded')
                    AND current_attempt > 0 AND current_state IS NULL) OR
               ((job_state = 'hold' AND job_reason->>'code' = 'ai_validated_hold') IS DISTINCT FROM
                    (hold_row.attempt IS NOT NULL)) OR
               (hold_row.attempt IS NOT NULL AND
                    (hold_row.attempt IS DISTINCT FROM current_attempt OR
                     hold_row.decision_id IS DISTINCT FROM current_decision)) THEN
                RAISE EXCEPTION 'each claimed attempt must have exactly one closure'
                    USING ERRCODE = '23514';
            END IF;
            RETURN NULL;
        END
        $$
    """).format(namespace, namespace, namespace, namespace, namespace, namespace, namespace, namespace, namespace))
    for table in ("jobs", "job_attempts", "attempt_outcomes", "job_hold_reports"):
        conn.execute(sql.SQL("""
            CREATE CONSTRAINT TRIGGER check_attempt_closure
            AFTER INSERT OR UPDATE OR DELETE ON {}.{}
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION {}.check_attempt_closure()
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
            authorized_artifact char(64);
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
                IF publication_decision IS NOT NULL THEN
                    SELECT d.artifact_sha256 INTO authorized_artifact FROM {}.ai_decisions d
                    JOIN {}.job_publications p ON p.tenant_id = d.tenant_id
                        AND p.job_id = d.job_id AND p.attempt = d.attempt
                        AND p.decision_id = d.decision_id
                    WHERE p.tenant_id = row_tenant AND p.job_id = row_job
                      AND d.disposition = 'proceed';
                    IF authorized_artifact IS DISTINCT FROM
                        (SELECT artifact_sha256 FROM {}.job_publications
                         WHERE tenant_id = row_tenant AND job_id = row_job) THEN
                        RAISE EXCEPTION 'publication artifact differs from decision authorization'
                            USING ERRCODE = '23514';
                    END IF;
                END IF;
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
    """).format(namespace, namespace, namespace, namespace, namespace, namespace, namespace))
    for table in ("jobs", "job_publications"):
        conn.execute(sql.SQL("""
            CREATE CONSTRAINT TRIGGER check_publication_pair
            AFTER INSERT OR UPDATE OR DELETE ON {}.{}
            DEFERRABLE INITIALLY DEFERRED
            FOR EACH ROW EXECUTE FUNCTION {}.check_publication_pair()
        """).format(namespace, sql.Identifier(table), namespace))
