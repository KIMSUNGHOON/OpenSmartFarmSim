"""Calculate outside the job lock, then publish one completed opaque reference."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from psycopg import sql

from . import crop_leaf_population_execution as execution
from . import crop_leaf_population_execution_result as result
from .crop_leaf_population_signed_producer import produce_registered_leaf_population
from .jobs import require_name, require_seconds


CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class LeafPopulationLeaseLost(ValueError):
    """The original calculation attempt can no longer publish."""


@dataclass(frozen=True)
class LeafPopulationExecutionOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    result_sha256: str | None = None


class LeafPopulationExecutionWorker:
    CODE_SHA256 = CODE_SHA256

    def __init__(self, service, *, tenant_id, lease_seconds=600):
        require_name(tenant_id, 'tenant_id'); require_seconds(lease_seconds, 'lease_seconds', maximum=600)
        execution._need(type(service) is execution.LeafPopulationExecutionService)
        self.service, self.jobs, self.tenant_id, self.lease_seconds = service, service.jobs, tenant_id, lease_seconds
        self._fixed = (service, service.jobs, tenant_id, lease_seconds)
        self._binding()

    def _binding(self):
        execution._need((self.service, self.jobs, self.tenant_id, self.lease_seconds) == self._fixed
            and self.jobs is self.service.jobs and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256)
        self.service._binding()
        result._binding()

    def _lease(self, conn, lease):
        self._binding()
        row = self.jobs._locked_job(conn, self.tenant_id, lease['job_id'])
        if (not self.jobs._owns_live_lease(row, lease['attempt'], lease['lease_token'])
                or row['cancel_requested'] or row['stage'] != 'simulation' or row['state'] != 'simulating'):
            raise LeafPopulationLeaseLost('leaf population execution lease unavailable')
        self.jobs._verified_input(row)
        return row

    def _before(self, lease):
        with self.jobs.connect() as conn:
            job = self._lease(conn, lease)
            value, binding_raw, packet = self.service.current_input(self.tenant_id, job['input_bytes'], write=True)
            if not self.jobs._renew_in_transaction(conn, self.tenant_id, lease['job_id'], lease['attempt'],
                    lease['lease_token'], self.lease_seconds):
                raise LeafPopulationLeaseLost('leaf population execution lease unavailable')
            binding = execution.signed.reader._parse(binding_raw, execution.signed.farms.MAX_BINDING_BYTES)
            parent = self.service.authority.farm_binding.parent_authority
            with execution.signed.MorphologyBlobStore(parent.directory, parent.access) as store:
                stem_raw = store.get(binding['parent']['numerical_root_sha256'], maximum=execution.signed.reader.MAX)
            execution._need(sha256(stem_raw).hexdigest() == binding['parent']['manifest_sha256'])
            stem = execution.signed.reader._parse(stem_raw, execution.signed.reader.MAX)
            self.jobs._event(conn, self.tenant_id, job['job_id'], result.START_EVENT_KIND, lease['attempt'],
                {'execution_kind': 'deterministic_leaf_population', 'worker_code_sha256': CODE_SHA256,
                 'input_sha256': job['input_sha256'], 'planned_outputs': len(stem['samples'])})
        return value, binding_raw, packet

    def _finish(self, lease, original, result_sha256):
        value, binding_raw, packet = original
        self._binding()
        proof = self.service.authority.read_manifest(self.tenant_id, result_sha256)
        execution._need(proof['binding_sha256'] == value['farm_binding_sha256'])
        raw = result.result_link(lease, result_sha256); digest = sha256(raw).hexdigest()
        self.jobs._durable_artifact(raw, digest)
        with self.jobs.connect() as conn:
            job = self._lease(conn, lease)
            execution._need(self.service.current_input(self.tenant_id, job['input_bytes'], write=True) == original)
            manifest = result.publication_manifest(job, raw, result_sha256, CODE_SHA256)
            self.jobs._insert_publication(conn, self.tenant_id, job['job_id'], lease['attempt'], None, digest, len(raw), manifest)
            self.jobs._event(conn, self.tenant_id, job['job_id'], result.RESULT_EVENT_KIND, lease['attempt'], manifest)
            self.jobs._event(conn, self.tenant_id, job['job_id'], 'succeeded', lease['attempt'])
            self.jobs._outcome(conn, self.tenant_id, job['job_id'], lease['attempt'], 'succeeded',
                termination_reason='leaf_population_completed')
            execution._need(self.service.current_input(self.tenant_id, job['input_bytes'], write=True) == original
                and self.service.authority.read_manifest(self.tenant_id, result_sha256) == proof)
            current = self._lease(conn, lease)
            execution._need(current['input_bytes'] == job['input_bytes'])
            updated = conn.execute(sql.SQL("""UPDATE {} SET state='succeeded', reason=NULL,
                lease_token=NULL, lease_until=NULL, cancel_requested=false, updated_at=clock_timestamp()
                WHERE tenant_id=%s AND job_id=%s AND stage='simulation' AND state='simulating'
                AND attempt_count=%s AND lease_token=%s AND lease_until>clock_timestamp()
                AND NOT cancel_requested""").format(self.jobs._table('jobs')),
                (self.tenant_id, job['job_id'], lease['attempt'], lease['lease_token']))
            if updated.rowcount != 1:
                raise LeafPopulationLeaseLost('leaf population execution lease unavailable')
        return LeafPopulationExecutionOutcome(job['job_id'], lease['attempt'], 'succeeded', 'leaf_population_completed', result_sha256)

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                kind, code, termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return LeafPopulationExecutionOutcome(lease['job_id'], lease['attempt'], state, code)

    def run_once(self, job_id):
        self._binding()
        if type(job_id) is not str or str(UUID(job_id)) != job_id:
            raise ValueError('leaf population execution job ID rejected')
        self.service.authority.farm_binding._guard(self.tenant_id, True)
        with self.jobs.connect() as conn:
            target = conn.execute(sql.SQL('SELECT stage,input_bytes FROM {} WHERE tenant_id=%s AND job_id=%s')
                .format(self.jobs._table('jobs')), (self.tenant_id, job_id)).fetchone()
        if target is None or target['stage'] != 'simulation': return None
        try:
            if json.loads(target['input_bytes']).get('input_version') != execution.INPUT_VERSION: return None
        except (ValueError, AttributeError, TypeError): return None
        lease = self.jobs.claim(self.lease_seconds, allowed_stages=('simulation',), tenant_id=self.tenant_id, job_id=job_id)
        if lease is None: return None
        try:
            original = self._before(lease)
            value, _, packet = original
            root = produce_registered_leaf_population(self.service.authority, self.tenant_id,
                execution.signed.reader._canonical(value['request']), **packet)
            return self._finish(lease, original, root)
        except LeafPopulationLeaseLost:
            try:
                canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                    termination_reason='canceled_by_request')
            except Exception:
                canceled = False
            return LeafPopulationExecutionOutcome(lease['job_id'], lease['attempt'], 'canceled' if canceled else 'unclosed',
                'canceled_by_request' if canceled else 'leaf_population_execution_lease_lost')
        except (PermissionError, execution.LeafPopulationExecutionHold, execution.signed.LeafPopulationSignedArtifactHold,
                result.LeafPopulationResultLinkHold):
            return self._close(lease, 'hold', 'leaf_population_execution_hold')
        except Exception:
            return self._close(lease, 'transient', 'leaf_population_execution_runtime_failure')
