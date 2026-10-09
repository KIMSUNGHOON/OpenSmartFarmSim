"""Complete one authored thermal simulation job and Run in one transaction."""

from dataclasses import dataclass
from hashlib import sha256
import json
from uuid import UUID

from psycopg import sql

from .farm_authored_run import AuthoredRunHold
from .farm_authored_run_store import AuthoredRunStore, AuthoredRunStoreHold
from .job_store import JobStore
from .jobs import canonical_input_bytes, require_name, require_seconds
from .runtime_roles import RuntimeLoginPolicy


@dataclass(frozen=True)
class AuthoredSimulationResult:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    run_id: str | None = None


class _LeaseLost(ValueError):
    pass


class AuthoredSimulationWorker:
    """The CLI review is upstream; this worker performs deterministic physics."""

    def __init__(self, run_store, *, tenant_id, lease_seconds=600):
        require_name(tenant_id, 'tenant_id')
        require_seconds(lease_seconds, 'lease_seconds')
        self.run_store = run_store
        self.jobs = run_store.jobs
        self.tenant_id = tenant_id
        self.lease_seconds = lease_seconds
        self._binding()

    def _binding(self):
        try:
            store, jobs = self.run_store, self.jobs
            policy, kind = jobs.runtime_identity
            store.preparer._binding()
            if (type(store) is not AuthoredRunStore or type(jobs) is not JobStore or
                    store.jobs is not jobs or
                    store.preparer.release_store.jobs is not jobs or
                    type(policy) is not RuntimeLoginPolicy or kind != 'authority' or
                    not policy.authored_run_storage or
                    jobs.audit_runtime_grants is not True or
                    not callable(jobs.principal_provider)):
                raise ValueError()
        except Exception:
            raise ValueError('authored simulation worker authority unavailable') from None

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'],
                lease['attempt'], lease['lease_token'], kind, code,
                termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return AuthoredSimulationResult(lease['job_id'], lease['attempt'], state, code)

    def _lost(self, lease):
        try:
            canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'],
                lease['attempt'], lease['lease_token'],
                termination_reason='canceled_by_request')
        except Exception:
            canceled = False
        return AuthoredSimulationResult(lease['job_id'], lease['attempt'],
            'canceled' if canceled else 'unclosed',
            'canceled_by_request' if canceled else 'authored_simulation_lease_lost')

    def run_once(self, job_id):
        self._binding()
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except Exception:
            raise ValueError('authored simulation job ID rejected') from None
        if not self.jobs._has_scope(self.tenant_id, 'simulation_execute'):
            raise ValueError('authored simulation execution denied')
        with self.jobs.connect() as conn:
            target = conn.execute(sql.SQL("""
                SELECT stage, input_bytes FROM {} WHERE tenant_id=%s AND job_id=%s
            """).format(self.jobs._table('jobs')),
                (self.tenant_id, job_id)).fetchone()
        if target is None or target['stage'] != 'simulation':
            return None
        try:
            if json.loads(target['input_bytes']).get('input_version') != (
                    'authored-thermal-simulation-input-v1'):
                return None
        except Exception:
            return None
        lease = self.jobs.claim(self.lease_seconds,
            allowed_stages=('simulation',), tenant_id=self.tenant_id, job_id=job_id)
        if lease is None:
            return None
        try:
            raw = self.jobs.read_input(self.tenant_id, lease['job_id'],
                lease['attempt'], lease['lease_token'])
            if raw is None:
                raise _LeaseLost()
            try:
                value = json.loads(raw)
                self.run_store._input(raw, self.tenant_id,
                    value['review_job_id'], value['scenario_id'],
                    value['scenario_revision'], value['registration_sha256'])
                if str(UUID(value['review_job_id'])) != value['review_job_id']:
                    raise ValueError()
            except Exception:
                return self._close(lease, 'fatal',
                    'authored_simulation_input_rejected')
            packet = self.run_store.preparer.prepare(self.tenant_id,
                value['review_job_id'], value['scenario_id'],
                value['scenario_revision'], value['registration_sha256'])
            if not self.jobs.renew(self.tenant_id, lease['job_id'],
                    lease['attempt'], lease['lease_token'], self.lease_seconds):
                raise _LeaseLost()
            run_id = self._finish(lease, raw, value, packet)
            return AuthoredSimulationResult(lease['job_id'], lease['attempt'],
                'succeeded', 'completed', run_id)
        except _LeaseLost:
            return self._lost(lease)
        except (AuthoredRunHold, AuthoredRunStoreHold):
            return self._close(lease, 'hold', 'authored_run_hold')
        except Exception:
            return self._close(lease, 'transient',
                               'authored_simulation_runtime_failure')

    def _finish(self, lease, raw, value, packet):
        self._binding()
        publication, _ = self.run_store._publication_from_packet(
            self.tenant_id, lease['job_id'], lease['attempt'],
            value['review_job_id'], value['scenario_id'],
            value['scenario_revision'], value['registration_sha256'], packet)
        receipt = {'receipt_version': 'authored-thermal-simulation-result-v1',
            'status': 'accepted', 'claim_scope': 'synthetic_thermal_replay_only',
            'run_id': packet.run_id, 'review_job_id': value['review_job_id'],
            'registration_sha256': value['registration_sha256'],
            'trace_sha256': list(packet.trace_sha256),
            'preparation_sha256': sha256(packet.report_raw).hexdigest(),
            'publication_sha256': sha256(publication).hexdigest()}
        artifact = canonical_input_bytes(receipt)
        digest = sha256(artifact).hexdigest()
        self.jobs._durable_artifact(artifact, digest)
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, lease['job_id'])
            if (not self.jobs._has_scope(self.tenant_id, 'simulation_execute') or
                    not self.jobs._has_scope(self.tenant_id, 'authored_run_publish') or
                    not self.jobs._owns_live_lease(job, lease['attempt'],
                                                    lease['lease_token']) or
                    job['cancel_requested'] or job['stage'] != 'simulation' or
                    self.jobs._verified_input(job) != raw):
                raise _LeaseLost()
            stored = self.run_store._publish_in_transaction(conn,
                self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], raw, value['review_job_id'],
                value['scenario_id'], value['scenario_revision'],
                value['registration_sha256'], packet)
            if stored != {'run_id': receipt['run_id'],
                    'trace_sha256': tuple(receipt['trace_sha256']),
                    'publication_sha256': receipt['publication_sha256']}:
                raise AuthoredRunStoreHold('authored Run receipt differs')
            if (not self.jobs._has_scope(self.tenant_id, 'simulation_execute') or
                    not self.jobs._has_scope(self.tenant_id, 'authored_run_publish')):
                raise _LeaseLost()
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state='succeeded', reason=NULL, lease_token=NULL,
                    lease_until=NULL, updated_at=clock_timestamp()
                WHERE tenant_id=%s AND job_id=%s AND stage='simulation'
                    AND state='simulating' AND attempt_count=%s AND lease_token=%s
                    AND lease_until>clock_timestamp() AND NOT cancel_requested
            """).format(self.jobs._table('jobs')),
                (self.tenant_id, job['job_id'], lease['attempt'],
                 lease['lease_token']))
            if updated.rowcount != 1:
                raise _LeaseLost()
            manifest = {'schema_version': '1', 'job_id': str(job['job_id']),
                'stage': 'simulation', 'input_sha256': job['input_sha256'],
                'attempt': lease['attempt'], 'artifact_sha256': digest,
                'run_id': packet.run_id}
            self.jobs._insert_publication(conn, self.tenant_id, job['job_id'],
                lease['attempt'], None, digest, len(artifact), manifest)
            self.jobs._event(conn, self.tenant_id, job['job_id'], 'succeeded',
                             lease['attempt'])
            self.jobs._outcome(conn, self.tenant_id, job['job_id'],
                lease['attempt'], 'succeeded', termination_reason='completed')
        return packet.run_id
