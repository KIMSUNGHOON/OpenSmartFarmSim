"""Run one leased solar calculation; publish its result and completion together."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import time
from uuid import UUID

from psycopg import sql
from psycopg.types.json import Jsonb

from . import crop_greenhouse_solar_execution_checkpoint as checkpoints
from . import crop_greenhouse_solar_result_store as results
from .jobs import require_name, require_seconds

VERSION = 'joint-solar-execution-publication-v1'
RESULT_LINK_VERSION = 'joint-solar-execution-result-link-v1'
RESULT_EVENT_KIND = 'solar_execution_result_registered_v1'
CUSTODY_WAIT_SECONDS = 5.0
CUSTODY_RETRY_SECONDS = .05
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
_CONTRACT = (VERSION, RESULT_LINK_VERSION, RESULT_EVENT_KIND, checkpoints.CODE_SHA256, results.CODE_SHA256,
             CUSTODY_WAIT_SECONDS, CUSTODY_RETRY_SECONDS)


@dataclass(frozen=True)
class SolarExecutionOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    result_id: str | None = None


class SolarExecutionWorker:
    def __init__(self, checkpoint_store, result_store, *, tenant_id,
                 lease_seconds=600, chunk_budget=128):
        require_name(tenant_id, 'tenant_id')
        require_seconds(lease_seconds, 'lease_seconds')
        require_seconds(chunk_budget, 'chunk_budget', maximum=128)
        if (type(checkpoint_store) is not checkpoints.SolarExecutionCheckpointStore
                or type(result_store) is not results.SolarResultStore):
            raise checkpoints.SolarCheckpointHold('solar worker authority unavailable')
        self.checkpoints, self.results = checkpoint_store, result_store
        self.jobs, self.server = checkpoint_store.jobs, checkpoint_store.server
        self.tenant_id, self.lease_seconds, self.chunk_budget = tenant_id, lease_seconds, chunk_budget
        self._fixed = self._pointers()
        self._binding()

    def _pointers(self):
        return (self.checkpoints, self.results, self.jobs, self.server,
                self.tenant_id, self.lease_seconds, self.chunk_budget)

    def _binding(self):
        try:
            if (type(self.checkpoints) is not checkpoints.SolarExecutionCheckpointStore
                    or type(self.results) is not results.SolarResultStore
                    or self.results.server is not self.server or self.results.jobs is not self.jobs
                    or self.checkpoints.jobs is not self.jobs or self.checkpoints.server is not self.server
                    or self._pointers() != self._fixed
                    or (VERSION, RESULT_LINK_VERSION, RESULT_EVENT_KIND,
                        checkpoints.CODE_SHA256, results.CODE_SHA256,
                        CUSTODY_WAIT_SECONDS, CUSTODY_RETRY_SECONDS) != _CONTRACT
                    or sha256(Path(__file__).read_bytes()).hexdigest() != CODE_SHA256):
                raise ValueError()
            self.checkpoints._binding(); self.results._binding()
        except Exception:
            raise checkpoints.SolarCheckpointHold('solar worker authority unavailable') from None

    def _before(self, lease):
        self._binding()
        with self.jobs.connect() as conn:
            job = self.checkpoints._lease(conn, self.tenant_id, str(lease['job_id']),
                                         lease['attempt'], lease['lease_token'], lock=False)
            value, request_raw, binding_raw = self.checkpoints._input(self.tenant_id, job)
        self.checkpoints._current(self.tenant_id, value, request_raw, binding_raw)
        with self.jobs.connect() as conn:
            current = self.checkpoints._lease(conn, self.tenant_id, str(lease['job_id']),
                                             lease['attempt'], lease['lease_token'])
            if self.checkpoints._input(self.tenant_id, current) != (value, request_raw, binding_raw):
                raise checkpoints.SolarCheckpointHold('solar worker input changed')
            if not self.jobs._renew_in_transaction(conn, self.tenant_id, lease['job_id'],
                    lease['attempt'], lease['lease_token'], self.lease_seconds):
                raise checkpoints.SolarCheckpointLeaseLost('solar worker lease unavailable')
        return request_raw

    def _adopt(self, request_raw):
        # Opening a private intent does not prepare a numerical context.
        with self.server._open(self.tenant_id, request_raw, True) as (session, _):
            return session.progress() if checkpoints.custody.files._exists(session.artifact, 'HEAD') else None

    def _confirm(self, lease):
        return self.checkpoints.confirm(self.tenant_id, str(lease['job_id']),
            attempt=lease['attempt'], lease_token=lease['lease_token'])

    def _custody_call(self, lease, operation):
        deadline = None
        while True:
            try:
                return operation()
            except checkpoints.custody.SolarCustodyPending:
                now = time.monotonic()
                if deadline is None:
                    deadline = now + CUSTODY_WAIT_SECONDS
                if now >= deadline:
                    raise
                self._before(lease)
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise
                time.sleep(min(CUSTODY_RETRY_SECONDS, remaining))
                if time.monotonic() >= deadline:
                    raise

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], kind, code, termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return SolarExecutionOutcome(lease['job_id'], lease['attempt'], state, code)

    def _lost(self, lease):
        try:
            canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], termination_reason='canceled_by_request')
        except Exception:
            canceled = False
        return SolarExecutionOutcome(lease['job_id'], lease['attempt'],
            'canceled' if canceled else 'unclosed',
            'canceled_by_request' if canceled else 'solar_execution_lease_lost')

    def run_once(self, job_id):
        self._binding()
        if type(job_id) is not str:
            raise ValueError('solar execution job ID rejected')
        try:
            if str(UUID(job_id)) != job_id: raise ValueError()
        except ValueError:
            raise ValueError('solar execution job ID rejected') from None
        self.checkpoints._guard(self.tenant_id)
        with self.jobs.connect() as conn:
            target = conn.execute(sql.SQL('SELECT stage,input_bytes FROM {} WHERE tenant_id=%s AND job_id=%s')
                .format(self.jobs._table('jobs')), (self.tenant_id, job_id)).fetchone()
        if target is None or target['stage'] != 'simulation': return None
        try:
            if json.loads(target['input_bytes']).get('input_version') != checkpoints.execution.INPUT_VERSION:
                return None
        except (ValueError, AttributeError, TypeError): return None
        lease = self.jobs.claim(self.lease_seconds, allowed_stages=('simulation',),
                                tenant_id=self.tenant_id, job_id=job_id)
        if lease is None: return None
        try:
            raw = self._before(lease)
            progress = self._custody_call(lease, lambda:self._adopt(raw))
            confirmed = self._custody_call(lease, lambda:self._confirm(lease)) if progress is not None else None
            for _ in range(checkpoints.MAX_EVENTS):
                if confirmed is not None and confirmed['checkpoint']['status'] in ('completed', 'hold'):
                    return self._custody_call(lease, lambda:self._finish(lease, confirmed))
                raw = self._before(lease)
                self._custody_call(lease, lambda:self.server.advance(self.tenant_id, raw, budget=self.chunk_budget))
                next_confirmed = self._custody_call(lease, lambda:self._confirm(lease))
                if confirmed is not None and next_confirmed['event_id'] == confirmed['event_id']:
                    raise checkpoints.SolarCheckpointHold('solar worker made no checkpoint progress')
                confirmed = next_confirmed
            raise checkpoints.SolarCheckpointHold('solar worker checkpoint limit reached')
        except checkpoints.SolarCheckpointLeaseLost:
            return self._lost(lease)
        except checkpoints.custody.SolarCustodyPending:
            return self._close(lease, 'transient', 'solar_execution_busy')
        except (PermissionError, checkpoints.SolarCheckpointHold,
                checkpoints.custody.SolarCustodyHold, checkpoints.custody.SolarCustodyConflict):
            return self._close(lease, 'hold', 'solar_execution_hold')
        except Exception:
            return self._close(lease, 'transient', 'solar_execution_runtime_failure')

    def _finish(self, lease, confirmed):
        self._binding()
        tenant, attempt, token = self.tenant_id, lease['attempt'], lease['lease_token']
        with self.jobs.connect() as conn:
            job = self.checkpoints._lease(conn, tenant, str(lease['job_id']), attempt, token, lock=False)
            value, raw, binding_raw = self.checkpoints._input(tenant, job)
            self.checkpoints._current(tenant, value, raw, binding_raw)
            latest = self.checkpoints._history(conn, tenant, job)
            if latest is None or self.checkpoints._record(latest, job['job_id']) != confirmed:
                raise checkpoints.SolarCheckpointHold('solar worker checkpoint differs')
            with self.results._put_in_transaction(conn, tenant, raw) as record:
                packet = results._decode(record['payload_raw'])
                progress, checkpoint = packet['policies']['server_progress'], confirmed['checkpoint']
                fields = ('head_sha256', 'proof_sha256', 'artifact_sha256', 'intent_sha256',
                          'context_sha256', 'time_binding_sha256', 'header_sha256',
                          'source_sha256', 'custody_code_sha256', 'provenance_sha256', 'steps', 'planned_steps', 'counts', 'status')
                if (sha256(results._canonical(packet['binding'])).hexdigest() != value['farm_binding_sha256']
                        or any(progress[k] != checkpoint[k] for k in fields)
                        or progress['status'] not in ('completed', 'hold')):
                    raise checkpoints.SolarCheckpointHold('solar worker result differs')
                state = 'succeeded' if progress['status'] == 'completed' else 'hold'
                code = 'completed' if state == 'succeeded' else 'solar_numerical_hold'
                reason = None if state == 'succeeded' else {'code': code, 'kind': 'hold'}
                digest = sha256(record['payload_raw']).hexdigest()
                if record['payload_sha256'] != digest: raise checkpoints.SolarCheckpointHold('solar result digest differs')
                manifest = {'schema_version': '1', 'publication_version': VERSION,
                    'result_link_version': RESULT_LINK_VERSION, 'status': progress['status'],
                    'job_id': str(job['job_id']), 'stage': 'simulation', 'attempt': attempt,
                    'input_sha256': job['input_sha256'], 'result_id': record['result_id'],
                    'artifact_sha256': digest, 'artifact_size': len(record['payload_raw']),
                    'root_sha256': progress['artifact_sha256'],
                    'head_sha256': progress['head_sha256'], 'proof_sha256': progress['proof_sha256'],
                    'checkpoint_event_id': confirmed['event_id'],
                    'worker_code_sha256': CODE_SHA256, 'scope': checkpoints.custody.SCOPE, 'G0_G4': 'not_assessed',
                    'provenance_sha256': progress['provenance_sha256'], 'rights_or_gate_approval': False}
                if len(results._canonical(manifest)) > checkpoints.MAX_BYTES:
                    raise checkpoints.SolarCheckpointHold('solar worker result link too large')
                if state == 'succeeded':
                    self.jobs._durable_artifact(record['payload_raw'], digest)
                    self.jobs._insert_publication(conn, tenant, job['job_id'], attempt, None,
                                                 digest, len(record['payload_raw']), manifest)
                self.jobs._event(conn, tenant, job['job_id'], RESULT_EVENT_KIND, attempt, manifest)
                self.jobs._event(conn, tenant, job['job_id'], state, attempt, reason)
                self.jobs._outcome(conn, tenant, job['job_id'], attempt, state, reason, termination_reason=code)
            self.checkpoints._current(tenant, value, raw, binding_raw)
            current = self.checkpoints._lease(conn, tenant, str(job['job_id']), attempt, token)
            if (self.checkpoints._input(tenant, current) != (value, raw, binding_raw)
                    or self.checkpoints._history(conn, tenant, current) != latest):
                raise checkpoints.SolarCheckpointHold('solar worker input or checkpoint changed')
            updated = conn.execute(sql.SQL("""UPDATE {} SET state=%s, reason=%s,
                lease_token=NULL, lease_until=NULL, cancel_requested=false, updated_at=clock_timestamp()
                WHERE tenant_id=%s AND job_id=%s AND stage='simulation' AND state='simulating'
                AND attempt_count=%s AND lease_token=%s AND lease_until>clock_timestamp()
                AND NOT cancel_requested""").format(self.jobs._table('jobs')),
                (state, Jsonb(reason) if reason is not None else None, tenant, job['job_id'], attempt, token))
            if updated.rowcount != 1:
                raise checkpoints.SolarCheckpointLeaseLost('solar worker lease unavailable')
        return SolarExecutionOutcome(job['job_id'], attempt, state, code, record['result_id'])
