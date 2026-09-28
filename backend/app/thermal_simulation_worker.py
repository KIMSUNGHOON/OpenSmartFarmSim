"""One targeted deterministic job; verified Run and terminal job commit together."""

from dataclasses import dataclass
from hashlib import sha256
from typing import Literal
from uuid import UUID

from pydantic import Field
from psycopg import sql

from .job_store import JobStore
from .jobs import canonical_input_bytes, require_name, require_seconds
from .provenance import FrozenContract
from .runtime_roles import RuntimeLoginPolicy
from .thermal_publisher import ThermalG1Publisher, ThermalPublishHold
from .thermal_run_store import ThermalRunStore, ThermalStoreHold


class SimulationInput(FrozenContract):
    input_version: Literal['thermal-simulation-input-v1']
    snapshot_id: str = Field(min_length=84, max_length=84, pattern=r'^thermal-snapshot-v1:[0-9a-f]{64}$')
    review_job_id: str = Field(min_length=36, max_length=36,
        pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


@dataclass(frozen=True)
class SimulationResult:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    run_id: str | None = None


class _LeaseLost(ValueError):
    pass


_HOLDS = frozenset({'ACCESS_HOLD', 'PIN_HOLD', 'REVIEW_HOLD', 'CONTEXT_HOLD',
    'SOURCE_HOLD', 'RELEASE_HOLD', 'TRACE_HOLD', 'PHYSICS_HOLD', 'TIME_HOLD',
    'EXECUTION_HOLD', 'G1_HOLD'})


class ThermalSimulationWorker:
    def __init__(self, publisher, *, tenant_id, lease_seconds=120):
        try:
            require_name(tenant_id, 'tenant_id')
            require_seconds(lease_seconds, 'lease_seconds')
            if type(publisher) is not ThermalG1Publisher:
                raise ValueError()
            self.publisher = publisher
            self.jobs, self.runs = publisher.job_store, publisher.run_store
            self._binding()
        except Exception:
            raise ValueError('simulation worker binding rejected') from None
        self.tenant_id, self.lease_seconds = tenant_id, lease_seconds

    def _binding(self):
        binding = getattr(self.jobs, 'runtime_identity', None)
        if (type(self.jobs) is not JobStore or type(self.runs) is not ThermalRunStore or
                self.publisher.job_store is not self.jobs or self.publisher.run_store is not self.runs or
                type(binding) is not tuple or len(binding) != 2 or
                type(binding[0]) is not RuntimeLoginPolicy or binding[1] != 'authority' or
                binding[0].schema != self.jobs.schema or self.runs.schema != self.jobs.schema or
                self.runs.runtime_identity != binding or type(self.jobs._dsn) is not str or
                not self.jobs._dsn or self.runs.dsn != self.jobs._dsn or
                self.jobs.audit_runtime_grants is not True or
                not callable(self.jobs.principal_provider) or
                self.runs._principal_provider is not self.jobs.principal_provider):
            raise ValueError('simulation worker binding rejected')

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                kind, code, termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return SimulationResult(lease['job_id'], lease['attempt'], state, code)

    def _lost(self, lease):
        try:
            canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], termination_reason='canceled_by_request')
        except Exception:
            canceled = False
        return SimulationResult(lease['job_id'], lease['attempt'],
            'canceled' if canceled else 'unclosed',
            'canceled_by_request' if canceled else 'simulation_lease_lost')

    def run_once(self, job_id):
        self._binding()
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError('simulation job ID rejected') from None
        if not self.jobs._has_scope(self.tenant_id, 'simulation_execute'):
            raise ValueError('simulation execution denied')
        lease = self.jobs.claim(self.lease_seconds, tenant_id=self.tenant_id,
            allowed_stages=('simulation',), job_id=job_id)
        if lease is None:
            return None
        try:
            raw = self.jobs.read_input(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'])
            if raw is None:
                raise _LeaseLost()
            try:
                value = SimulationInput.model_validate_json(raw)
                if canonical_input_bytes(value.model_dump(mode='json')) != raw:
                    raise ValueError()
            except Exception:
                return self._close(lease, 'fatal', 'simulation_input_rejected')
            packet = self.publisher.prepare(self.tenant_id, value.review_job_id, value.snapshot_id)
            run_id = self._finish(lease, raw, value, packet)
            return SimulationResult(lease['job_id'], lease['attempt'], 'succeeded', 'completed', run_id)
        except _LeaseLost:
            return self._lost(lease)
        except ThermalPublishHold as exc:
            prefix = str(exc).partition(':')[0]
            code = prefix.lower() if prefix in _HOLDS else 'g1_hold'
            return self._close(lease, 'hold', 'thermal_'+code)
        except ThermalStoreHold:
            return self._close(lease, 'hold', 'thermal_g1_hold')
        except Exception:
            return self._close(lease, 'transient', 'simulation_runtime_failure')

    def _finish(self, lease, raw, value, packet):
        self._binding()
        report = self.runs._check_packet(**packet)
        if (report['tenant_id'] != self.tenant_id or report['snapshot_id'] != value.snapshot_id or
                report['review_job_id'] != value.review_job_id):
            raise ThermalStoreHold('REPORT_HOLD: simulation packet differs')
        receipt = {'receipt_version': 'thermal-simulation-result-v1', 'status': 'accepted',
            'claim_scope': 'synthetic_thermal_replay_only', 'run_id': report['run_id'],
            'snapshot_id': value.snapshot_id, 'review_job_id': value.review_job_id,
            'decision_context_id': report['decision_context_id'], 'decision_id': report['decision_id'],
            'trace_sha256': [sha256(trace).hexdigest() for trace in packet['trace_raws']],
            'report_sha256': sha256(packet['report_raw']).hexdigest()}
        artifact = canonical_input_bytes(receipt)
        digest = sha256(artifact).hexdigest()
        self.jobs._durable_artifact(artifact, digest)
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, lease['job_id'])
            if (not self.jobs._has_scope(self.tenant_id, 'simulation_execute') or
                    not self.jobs._owns_live_lease(job, lease['attempt'], lease['lease_token']) or
                    job['cancel_requested'] or job['stage'] != 'simulation' or
                    self.jobs._verified_input(job) != raw):
                raise _LeaseLost()
            stored = self.runs._publish_verified_in_transaction(conn, self.tenant_id, **packet)
            if stored != {'run_id': receipt['run_id'], 'trace_sha256': tuple(receipt['trace_sha256']),
                          'report_sha256': receipt['report_sha256']}:
                raise ThermalStoreHold('STORE_HOLD: simulation receipt differs')
            if not self.jobs._has_scope(self.tenant_id, 'simulation_execute'):
                raise _LeaseLost()
            updated = conn.execute(sql.SQL("""
                UPDATE {} SET state='succeeded', reason=NULL, lease_token=NULL, lease_until=NULL,
                    updated_at=clock_timestamp()
                WHERE tenant_id=%s AND job_id=%s AND stage='simulation' AND state='simulating'
                    AND attempt_count=%s AND lease_token=%s AND lease_until>clock_timestamp()
                    AND NOT cancel_requested
            """).format(self.jobs._table('jobs')),
                (self.tenant_id, job['job_id'], lease['attempt'], lease['lease_token']))
            if updated.rowcount != 1:
                raise _LeaseLost()
            manifest = {'schema_version': '1', 'job_id': str(job['job_id']), 'stage': 'simulation',
                'input_sha256': job['input_sha256'], 'attempt': lease['attempt'], 'artifact_sha256': digest}
            self.jobs._insert_publication(conn, self.tenant_id, job['job_id'], lease['attempt'], None,
                digest, len(artifact), manifest)
            self.jobs._event(conn, self.tenant_id, job['job_id'], 'succeeded', lease['attempt'])
            self.jobs._outcome(conn, self.tenant_id, job['job_id'], lease['attempt'], 'succeeded',
                termination_reason='completed')
        return report['run_id']
