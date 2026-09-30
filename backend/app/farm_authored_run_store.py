"""Immutable tenant-scoped custody for authored thermal Run publication bytes."""

import hmac
from psycopg import sql
from hashlib import sha256
import json
from uuid import UUID

from .farm_authored_run import AuthoredRunPreparer, PreparedAuthoredRun
from .farm_authored_release_store import AuthoredReleaseStore
from .job_store import JobStore
from .jobs import canonical_input_bytes
from .runtime_login import verify_runtime_identity
from .runtime_roles import RuntimeLoginPolicy


GATE_DOMAIN = b'ossf-authored-thermal-run-gate-v1\0'


class AuthoredRunStoreHold(ValueError):
    pass


def _need(condition):
    if not condition:
        raise AuthoredRunStoreHold('authored Run publication unavailable')


def _digest(raw):
    return sha256(raw).hexdigest()


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
    conn.execute(sql.SQL("""
        CREATE FUNCTION {}.require_authored_run_publication()
        RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM {}.jobs j JOIN {}.job_publications p
                    ON p.tenant_id=j.tenant_id AND p.job_id=j.job_id
                WHERE j.tenant_id=NEW.tenant_id AND j.job_id=NEW.simulation_job_id
                    AND j.stage='simulation' AND j.state='succeeded'
                    AND p.attempt=(convert_from(NEW.publication_raw, 'UTF8')::jsonb->>'attempt')::integer
                    AND p.manifest->>'stage'='simulation'
                    AND p.manifest->>'run_id'=NEW.run_id
                    AND p.manifest->>'input_sha256'=j.input_sha256
                    AND p.manifest->>'artifact_sha256'=p.artifact_sha256
            ) THEN RAISE EXCEPTION 'authored Run lacks atomic job publication'; END IF;
            RETURN NEW;
        END $$
    """).format(namespace, namespace, namespace))
    conn.execute(sql.SQL("""
        CREATE CONSTRAINT TRIGGER authored_run_publication
        AFTER INSERT ON {}.authored_thermal_runs
        DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
        EXECUTE FUNCTION {}.require_authored_run_publication()
    """).format(namespace, namespace))


class AuthoredRunStore:
    """Insert only inside a live simulation lease transaction."""

    def __init__(self, preparer, gate_key):
        try:
            preparer._binding()
            jobs = preparer.release_store.jobs
            policy, kind = jobs.runtime_identity
            _need(type(preparer) is AuthoredRunPreparer and
                  type(preparer.release_store) is AuthoredReleaseStore and
                  type(jobs) is JobStore and
                  type(policy) is RuntimeLoginPolicy and kind == 'authority' and
                  policy.authored_run_storage and
                  type(gate_key) is bytes and len(gate_key) >= 32)
        except Exception:
            raise AuthoredRunStoreHold('authored Run authority unavailable') from None
        self.preparer, self.jobs, self.gate_key = preparer, jobs, gate_key

    def _publication(self, tenant, simulation_job_id, attempt, review_job_id,
                     scenario_id, revision, registration_sha256, packet):
        try:
            self.preparer._binding()
            _need(type(packet) is PreparedAuthoredRun and
                  type(attempt) is int and attempt > 0 and
                  str(UUID(str(simulation_job_id))) == str(simulation_job_id) and
                  str(UUID(str(review_job_id))) == str(review_job_id))
            expected = self.preparer.prepare(tenant, review_job_id, scenario_id,
                                              revision, registration_sha256)
            _need(packet == expected)
            prepared = json.loads(packet.report_raw)
            _need(canonical_input_bytes(prepared) == packet.report_raw and
                  prepared['run_id'] == packet.run_id and
                  prepared['tenant_id'] == tenant and
                  prepared['scenario_id'] == scenario_id and
                  prepared['scenario_revision'] == revision and
                  prepared['registration_sha256'] == registration_sha256 and
                  prepared['review_job_id'] == str(review_job_id) and
                  prepared['status'] == 'prepared_unpublished' and
                  prepared['trace_sha256'] == list(packet.trace_sha256) and
                  prepared['claim_scope'] == 'synthetic_thermal_replay_only')
            publication = canonical_input_bytes({
                'gate_version': 'authored-thermal-run-gate-v1',
                'status': 'accepted', 'claim_scope': prepared['claim_scope'],
                'tenant_id': tenant, 'run_id': packet.run_id,
                'simulation_job_id': str(simulation_job_id), 'attempt': attempt,
                'review_job_id': str(review_job_id),
                'scenario_id': scenario_id, 'scenario_revision': revision,
                'registration_sha256': registration_sha256,
                'decision_context_id': prepared['decision_context_id'],
                'context_sha256': prepared['context_sha256'],
                'decision_at_utc': prepared['decision_at_utc'],
                'review_at_utc': prepared['review_at_utc'],
                'claim_mode': 'ex_post_replay',
                'release_sha256': prepared['release_sha256'],
                'preparation_sha256': _digest(packet.report_raw),
                'trace_sha256': list(packet.trace_sha256)})
            signature = hmac.new(self.gate_key, GATE_DOMAIN + publication + b'\0' +
                packet.trace_sha256[0].encode() + packet.trace_sha256[1].encode(),
                sha256).hexdigest()
            return publication, signature
        except Exception:
            raise AuthoredRunStoreHold('authored Run publication unavailable') from None

    @staticmethod
    def _input(raw, tenant, review_job_id, scenario_id, revision,
               registration_sha256):
        try:
            value = json.loads(raw)
            _need(canonical_input_bytes(value) == raw and set(value) == {
                'input_version', 'tenant_id', 'review_job_id', 'scenario_id',
                'scenario_revision', 'registration_sha256'} and
                value == {'input_version': 'authored-thermal-simulation-input-v1',
                    'tenant_id': tenant, 'review_job_id': str(review_job_id),
                    'scenario_id': scenario_id, 'scenario_revision': revision,
                    'registration_sha256': registration_sha256})
            return value
        except Exception:
            raise AuthoredRunStoreHold('authored simulation input unavailable') from None

    def _publish_in_transaction(self, conn, tenant, simulation_job_id, attempt,
                                lease_token, simulation_input_raw, review_job_id,
                                scenario_id, revision, registration_sha256, packet):
        """Caller must complete the same leased job before committing this connection."""
        try:
            policy, kind = self.jobs.runtime_identity
            verify_runtime_identity(conn, policy, kind)
            _need(self.jobs._has_scope(tenant, 'simulation_execute') and
                  self.jobs._has_scope(tenant, 'authored_run_publish'))
            job = self.jobs._locked_job(conn, tenant, simulation_job_id)
            _need(job is not None and job['stage'] == 'simulation' and
                  job['state'] == 'simulating' and not job['cancel_requested'] and
                  self.jobs._owns_live_lease(job, attempt, lease_token) and
                  self.jobs._verified_input(job) == simulation_input_raw)
            self._input(simulation_input_raw, tenant, review_job_id, scenario_id,
                        revision, registration_sha256)
            publication, signature = self._publication(tenant, simulation_job_id,
                attempt, review_job_id, scenario_id, revision,
                registration_sha256, packet)
            report = json.loads(packet.report_raw)
            with conn.transaction():
                conn.execute(sql.SQL("""
                    INSERT INTO {} (tenant_id, run_id, simulation_job_id,
                        review_job_id, registration_sha256, scenario_id,
                        scenario_revision, trace0_raw, trace0_sha256,
                        trace1_raw, trace1_sha256, preparation_raw,
                        preparation_sha256, publication_raw, publication_sha256,
                        gate_signature)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """).format(self.jobs._table('authored_thermal_runs')),
                    (tenant, packet.run_id, simulation_job_id, review_job_id,
                     registration_sha256, scenario_id, revision,
                     packet.trace_raws[0], packet.trace_sha256[0],
                     packet.trace_raws[1], packet.trace_sha256[1],
                     packet.report_raw, _digest(packet.report_raw),
                     publication, _digest(publication), signature))
                row = conn.execute(sql.SQL("""
                    SELECT * FROM {} WHERE tenant_id=%s AND run_id=%s
                """).format(self.jobs._table('authored_thermal_runs')),
                    (tenant, packet.run_id)).fetchone()
                _need(row is not None and
                      row['simulation_job_id'] == UUID(str(simulation_job_id)) and
                      row['review_job_id'] == UUID(str(review_job_id)) and
                      row['registration_sha256'] == registration_sha256 and
                      row['scenario_id'] == scenario_id and
                      row['scenario_revision'] == revision and
                      row['trace0_raw'] == packet.trace_raws[0] and
                      row['trace1_raw'] == packet.trace_raws[1] and
                      row['preparation_raw'] == packet.report_raw and
                      row['publication_raw'] == publication and
                      row['gate_signature'] == signature and
                      row['trace0_sha256'] == report['trace_sha256'][0] and
                      row['trace1_sha256'] == report['trace_sha256'][1])
            return {'run_id': packet.run_id,
                    'trace_sha256': packet.trace_sha256,
                    'publication_sha256': _digest(publication)}
        except Exception:
            raise AuthoredRunStoreHold('authored Run publication unavailable') from None

    def get_run(self, tenant, run_id):
        """Return a completed Run only while current release and input still verify."""
        if not self.jobs._has_scope(tenant, 'authored_run_read'):
            return None
        try:
            with self.jobs.connect() as conn:
                row = conn.execute(sql.SQL("""
                    SELECT r.*, j.state AS job_state, j.input_sha256,
                        j.input_bytes AS simulation_input_raw,
                        p.attempt AS published_attempt, p.artifact_sha256,
                        p.manifest
                    FROM {} r JOIN {} j ON j.tenant_id=r.tenant_id
                        AND j.job_id=r.simulation_job_id
                    JOIN {} p ON p.tenant_id=j.tenant_id AND p.job_id=j.job_id
                    WHERE r.tenant_id=%s AND r.run_id=%s
                """).format(self.jobs._table('authored_thermal_runs'),
                    self.jobs._table('jobs'), self.jobs._table('job_publications')),
                    (tenant, run_id)).fetchone()
            if row is None:
                return None
            self._input(row['simulation_input_raw'], tenant, row['review_job_id'],
                row['scenario_id'], row['scenario_revision'],
                row['registration_sha256'])
            packet = PreparedAuthoredRun(row['run_id'], row['preparation_raw'],
                (row['trace0_raw'], row['trace1_raw']))
            publication, signature = self._publication(tenant,
                row['simulation_job_id'], row['published_attempt'],
                row['review_job_id'], row['scenario_id'],
                row['scenario_revision'], row['registration_sha256'], packet)
            _need(row['job_state'] == 'succeeded' and
                  row['manifest'].get('stage') == 'simulation' and
                  row['manifest'].get('run_id') == run_id and
                  row['manifest'].get('input_sha256') == row['input_sha256'] and
                  row['manifest'].get('artifact_sha256') == row['artifact_sha256'] and
                  row['preparation_sha256'] == _digest(packet.report_raw) and
                  (row['trace0_sha256'], row['trace1_sha256']) ==
                    packet.trace_sha256 and
                  row['publication_raw'] == publication and
                  row['publication_sha256'] == _digest(publication) and
                  hmac.compare_digest(row['gate_signature'], signature))
            receipt_raw = self.jobs.read_artifact(tenant, row['simulation_job_id'])
            receipt = json.loads(receipt_raw)
            _need(canonical_input_bytes(receipt) == receipt_raw and
                  _digest(receipt_raw) == row['artifact_sha256'] and
                  receipt == {
                      'receipt_version': 'authored-thermal-simulation-result-v1',
                      'status': 'accepted',
                      'claim_scope': 'synthetic_thermal_replay_only',
                      'run_id': run_id,
                      'review_job_id': str(row['review_job_id']),
                      'registration_sha256': row['registration_sha256'],
                      'trace_sha256': list(packet.trace_sha256),
                      'preparation_sha256': row['preparation_sha256'],
                      'publication_sha256': row['publication_sha256']})
            return {'run_id': run_id, 'trace_raws': packet.trace_raws,
                    'report_raw': publication, 'report': json.loads(publication),
                    'recorded_at': row['recorded_at']}
        except Exception:
            raise AuthoredRunStoreHold('authored Run read unavailable') from None
