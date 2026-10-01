"""Fenced finite-grid calculation; result and completion share one transaction."""

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from uuid import UUID

from psycopg import sql

from .break_even import BreakEvenService
from .break_even_replay import ReplayReferences
from .break_even_reference_read import recheck_replay_reads
from .break_even_store import canonical_result_bytes, _ProposedPlanRepository, BreakEvenDenied
from .break_even_plan_submission import (BreakEvenPlanSubmissionService, BreakEvenPlanInput,
    BreakEvenPlanSubmission, BreakEvenTrialPin)
from .economics import FORMULA_VERSION
from .jobs import canonical_input_bytes, require_name, require_seconds
from .thermal_publisher import runtime_digests


@dataclass(frozen=True)
class BreakEvenCalculationOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    plan_id: str | None = None


class _LeaseLost(ValueError):
    pass


class _InputHold(ValueError):
    pass


def _result_bytes(result):
    return canonical_result_bytes(result)


class BreakEvenCalculationWorker:
    def __init__(self, jobs, store, *, tenant_id, lease_seconds=300):
        try:
            require_name(tenant_id, 'tenant_id')
            require_seconds(lease_seconds, 'lease_seconds')
            self.jobs, self.store = jobs, store
            self.plans = BreakEvenPlanSubmissionService(jobs, store)
        except Exception:
            raise ValueError('break-even calculation binding rejected') from None
        self.tenant_id, self.lease_seconds = tenant_id, lease_seconds

    def _binding(self):
        self.plans._binding()
        if self.plans.jobs is not self.jobs or self.plans.store is not self.store:
            raise RuntimeError('break-even calculation binding changed')

    @staticmethod
    def _digests():
        return runtime_digests(Path(__file__).resolve().parents[2])

    def _guard(self, pointers, digests):
        self._binding()
        self.plans._access(self.tenant_id)
        if self.plans._pointers() != pointers or self._digests() != digests:
            raise RuntimeError('break-even calculation binding changed')

    def _pulse(self, lease, pointers, digests, conn=None):
        self._guard(pointers, digests)
        args = (self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'], self.lease_seconds)
        renewed = self.jobs.renew(*args) if conn is None else self.jobs._renew_in_transaction(conn, *args)
        if not renewed:
            raise _LeaseLost()

    def _calculate(self, value, check):
        check()
        body = BreakEvenPlanSubmission(request=value.request, trials=tuple(BreakEvenTrialPin(
            scenario_id=ref.scenario_id, revision=ref.revision, scenario_sha256=ref.scenario_sha256)
            for ref in value.plan.trials))
        try:
            rebuilt = self.plans._prepare(self.tenant_id, body, check=check)
            if canonical_input_bytes(rebuilt.model_dump(mode='json')) != canonical_input_bytes(value.model_dump(mode='json')):
                raise _InputHold()
            references = ReplayReferences(_ProposedPlanRepository(self.store._source, value.plan), self.tenant_id)
            result = BreakEvenService(references).scan(value.request, self.tenant_id, check=check)
            return result, references.observed_reads()
        except (_LeaseLost, PermissionError):
            raise
        except ValueError as exc:
            if exc.__cause__ is not None:
                raise RuntimeError('break-even source unavailable') from None
            raise _InputHold() from None

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                kind, code, termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return BreakEvenCalculationOutcome(lease['job_id'], lease['attempt'], state, code)

    def _lost(self, lease):
        try:
            canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], termination_reason='canceled_by_request')
        except Exception:
            canceled = False
        return BreakEvenCalculationOutcome(lease['job_id'], lease['attempt'],
            'canceled' if canceled else 'unclosed', 'canceled_by_request' if canceled else 'break_even_lease_lost')

    def run_once(self, job_id):
        self._binding()
        self.plans._access(self.tenant_id)
        try:
            if type(job_id) is not str or str(UUID(job_id)) != job_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError):
            raise ValueError('break-even calculation job ID rejected') from None
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, job_id)
            if job is None or job['stage'] != 'simulation' or job['state'] not in ('queued', 'simulating'):
                return None
            data = json.loads(self.jobs._verified_input(job))
            if type(data) is not dict or data.get('input_version') != 'break-even-calculation-input-v1':
                return None
        lease = self.jobs.claim(self.lease_seconds, tenant_id=self.tenant_id,
            allowed_stages=('simulation',), job_id=job_id)
        if lease is None:
            return None
        try:
            self._binding()
            pointers, digests = self.plans._pointers(), self._digests()
            raw = self.jobs.read_input(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'])
            if raw is None:
                raise _LeaseLost()
            try:
                value = BreakEvenPlanInput.model_validate_json(raw)
                if canonical_input_bytes(value.model_dump(mode='json')) != raw:
                    raise ValueError()
            except Exception:
                return self._close(lease, 'fatal', 'break_even_input_rejected')
            check = lambda: self._pulse(lease, pointers, digests)
            result, _ = self._calculate(value, check)
            self._finish(lease, raw, value, result, pointers, digests)
            return BreakEvenCalculationOutcome(lease['job_id'], lease['attempt'], 'succeeded', 'completed', value.plan.plan_id)
        except _LeaseLost:
            return self._lost(lease)
        except (_InputHold, PermissionError, BreakEvenDenied):
            return self._close(lease, 'hold', 'break_even_input_hold')
        except Exception:
            return self._close(lease, 'transient', 'break_even_runtime_failure')

    def _finish(self, lease, raw, value, result, pointers, digests):
        encoded = _result_bytes(result)
        replayed, reads = self._calculate(value, lambda: self._pulse(lease, pointers, digests))
        if _result_bytes(replayed) != encoded:
            raise _InputHold()
        receipt = {'receipt_version': 'break-even-calculation-result-v1', 'status': 'completed',
            'claim_scope': result.scope, 'plan_id': value.plan.plan_id,
            'request_sha256': value.plan.request_sha256,
            'plan_sha256': sha256(canonical_input_bytes(value.plan.model_dump(mode='json'))).hexdigest(),
            'result_sha256': sha256(encoded).hexdigest(), 'calculation_status': result.status,
            'assessment_status': result.assessment_status, 'scan_version': 'break-even-grid-v1',
            'formula_version': FORMULA_VERSION, 'code_sha256': digests[0], 'environment_sha256': digests[1]}
        artifact = canonical_input_bytes(receipt)
        digest = sha256(artifact).hexdigest()
        self.jobs._durable_artifact(artifact, digest)
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, lease['job_id'])
            if (not self.jobs._owns_live_lease(job, lease['attempt'], lease['lease_token']) or job['cancel_requested'] or
                    job['stage'] != 'simulation' or self.jobs._verified_input(job) != raw):
                raise _LeaseLost()
            check = lambda: self._pulse(lease, pointers, digests, conn)
            check()
            stored = self.store._pin_in_transaction(conn, value.request, value.plan, result)
            check()
            if stored['result_raw'] != encoded:
                raise _InputHold()
            try:
                recheck_replay_reads(self.store, self.tenant_id, reads, check=check, plan_row=stored)
            except ValueError as exc:
                if exc.__cause__ is not None:
                    raise RuntimeError('break-even source unavailable') from None
                raise _InputHold() from None
            check()
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
