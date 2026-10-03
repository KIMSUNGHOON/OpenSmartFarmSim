"""Lease a full replay, then fence a bounded receipt and private evidence."""

from dataclasses import dataclass
from hashlib import sha256
import json
from uuid import UUID

from psycopg import sql

from .break_even_store import BreakEvenDenied, _canonical
from .break_even_verification import BreakEvenVerificationInput, BreakEvenVerificationService
from .jobs import canonical_input_bytes, require_name, require_seconds


class _LeaseLost(ValueError):
    pass


class _InputHold(ValueError):
    pass


@dataclass(frozen=True)
class BreakEvenVerificationOutcome:
    job_id: UUID
    attempt: int
    state: str
    reason_code: str
    calculation_job_id: str | None = None


class BreakEvenVerificationWorker:
    def __init__(self, jobs, store, *, tenant_id, lease_seconds=300):
        require_name(tenant_id, 'tenant_id')
        require_seconds(lease_seconds, 'lease_seconds')
        self.service = BreakEvenVerificationService(jobs, store)
        self.jobs, self.store = jobs, store
        self.tenant_id, self.lease_seconds = tenant_id, lease_seconds

    def _guard(self, pointers, digests):
        if self.service.jobs is not self.jobs or self.service.store is not self.store:
            raise RuntimeError('break-even verification worker binding changed')
        self.service._guard(self.tenant_id, pointers, digests)

    def _pulse(self, lease, pointers, digests, conn=None):
        self._guard(pointers, digests)
        args = (self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'], self.lease_seconds)
        renewed = self.jobs.renew(*args) if conn is None else self.jobs._renew_in_transaction(conn, *args)
        if not renewed:
            raise _LeaseLost()

    def _parent(self, value, check):
        current = self.service.prepare(self.tenant_id, value.calculation_job_id, check=check)
        if canonical_input_bytes(current.model_dump(mode='json')) != canonical_input_bytes(value.model_dump(mode='json')):
            raise _InputHold()

    def _capture(self, value, check):
        try:
            self._parent(value, check)
            captured = self.store.capture_break_even_replay(self.tenant_id, value.plan_id, check=check)
            if captured is None:
                raise _InputHold()
            _, result, evidence = captured
            if ((evidence.tenant_id, evidence.plan_id, evidence.request_sha256,
                    evidence.plan_sha256, evidence.result_sha256, evidence.code_sha256,
                    evidence.environment_sha256, evidence.trial_count, result.status) !=
                    (self.tenant_id, value.plan_id, value.request_sha256, value.plan_sha256,
                     value.result_sha256, value.code_sha256, value.environment_sha256,
                     value.trial_count, value.calculation_status)):
                raise _InputHold()
            return evidence
        except (_LeaseLost, PermissionError):
            raise
        except ValueError as exc:
            if exc.__cause__ is not None:
                raise RuntimeError('break-even verification source unavailable') from None
            raise _InputHold() from None

    def _close(self, lease, kind, code):
        try:
            closed = self.jobs.fail(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'],
                kind, code, termination_reason=code)
            job = self.jobs.get_job(self.tenant_id, lease['job_id']) if closed else None
            state = job['state'] if job else 'unclosed'
        except Exception:
            state = 'unclosed'
        return BreakEvenVerificationOutcome(lease['job_id'], lease['attempt'], state, code)

    def _lost(self, lease):
        try:
            canceled = self.jobs.ack_cancel(self.tenant_id, lease['job_id'], lease['attempt'],
                lease['lease_token'], termination_reason='canceled_by_request')
        except Exception:
            canceled = False
        return BreakEvenVerificationOutcome(lease['job_id'], lease['attempt'],
            'canceled' if canceled else 'unclosed',
            'canceled_by_request' if canceled else 'break_even_verification_lease_lost')

    def run_once(self, job_id):
        if type(job_id) is not str or str(UUID(job_id)) != job_id:
            raise ValueError('break-even verification job ID rejected')
        pointers, digests = self.service.authority.plans._pointers(), self.service._digests()
        self._guard(pointers, digests)
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, UUID(job_id))
            if job is None or job['stage'] != 'simulation' or job['state'] not in ('queued', 'simulating'):
                return None
            data = json.loads(self.jobs._verified_input(job))
            if type(data) is not dict or data.get('input_version') != 'break-even-verification-input-v1':
                return None
        lease = self.jobs.claim(self.lease_seconds, tenant_id=self.tenant_id,
            allowed_stages=('simulation',), job_id=job_id)
        if lease is None:
            return None
        try:
            raw = self.jobs.read_input(self.tenant_id, lease['job_id'], lease['attempt'], lease['lease_token'])
            if raw is None:
                raise _LeaseLost()
            try:
                value = BreakEvenVerificationInput.model_validate_json(raw)
                if canonical_input_bytes(value.model_dump(mode='json')) != raw:
                    raise ValueError()
            except Exception:
                return self._close(lease, 'fatal', 'break_even_verification_input_rejected')
            if (value.code_sha256, value.environment_sha256) != digests:
                raise _InputHold()
            check = lambda: self._pulse(lease, pointers, digests)
            evidence = self._capture(value, check)
            self._finish(lease, raw, value, evidence, pointers, digests)
            return BreakEvenVerificationOutcome(lease['job_id'], lease['attempt'], 'succeeded',
                'completed', value.calculation_job_id)
        except _LeaseLost:
            return self._lost(lease)
        except (_InputHold, PermissionError, BreakEvenDenied):
            return self._close(lease, 'hold', 'break_even_verification_input_hold')
        except Exception:
            return self._close(lease, 'transient', 'break_even_verification_runtime_failure')

    def _finish(self, lease, raw, value, evidence, pointers, digests):
        evidence_raw = _canonical(evidence.model_dump(mode='json'))
        if not 1 <= len(evidence_raw) <= 1048576:
            raise _InputHold()
        evidence_sha = sha256(evidence_raw).hexdigest()
        receipt = {'receipt_version': 'break-even-verification-result-v1', 'status': 'completed',
            'verification_scope': 'historical_full_grid_replay_only', 'assessment_status': 'hold',
            'calculation_job_id': value.calculation_job_id, 'plan_id': value.plan_id,
            'verification_input_sha256': sha256(raw).hexdigest(),
            'calculation_input_sha256': value.calculation_input_sha256,
            'calculation_receipt_sha256': value.calculation_receipt_sha256,
            'request_sha256': value.request_sha256, 'plan_sha256': value.plan_sha256,
            'result_sha256': value.result_sha256, 'evidence_sha256': evidence_sha,
            'evidence_size': len(evidence_raw), 'trial_count': value.trial_count,
            'scan_version': value.scan_version, 'formula_version': value.formula_version,
            'code_sha256': digests[0], 'environment_sha256': digests[1]}
        artifact = canonical_input_bytes(receipt)
        if len(artifact) > 4096:
            raise _InputHold()
        digest = sha256(artifact).hexdigest()
        self.jobs._durable_evidence(self.tenant_id, evidence_raw, evidence_sha)
        self.jobs._durable_artifact(artifact, digest)
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, self.tenant_id, lease['job_id'])
            if (not self.jobs._owns_live_lease(job, lease['attempt'], lease['lease_token']) or
                    job['cancel_requested'] or job['stage'] != 'simulation' or
                    self.jobs._verified_input(job) != raw):
                raise _LeaseLost()
            check = lambda: self._pulse(lease, pointers, digests, conn)
            check()
            self._parent(value, check)
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
