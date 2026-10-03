"""Verified completed break-even jobs expose the existing conditional projection."""

from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import Field

from .api_break_even import project_break_even_result
from .break_even import canonical_request_sha256
from .break_even_calculation_worker import _result_bytes
from .break_even_plan_submission import BreakEvenPlanInput, BreakEvenPlanSubmissionService
from .economics import FORMULA_VERSION
from .jobs import canonical_input_bytes
from .owned_fixture_collection import UUID_PATTERN
from .provenance import Digest, FrozenContract


BREAK_EVEN_JOB_READ_SCOPES = ('metadata', 'artifact', 'break_even_read', 'market_source_read',
    'market_candidate_read', 'decision_context_read', 'market_hold_context_read')


class BreakEvenCompletion(FrozenContract):
    verification: Literal['completed_bytes_only_requires_replay']
    calculation_job_id: str = Field(pattern=UUID_PATTERN)
    calculation_attempt: int = Field(ge=1)
    calculation_input_sha256: Digest
    calculation_receipt_sha256: Digest
    plan_id: str = Field(min_length=1, max_length=200)
    request_sha256: Digest
    plan_sha256: Digest
    result_sha256: Digest
    calculation_status: Literal['zero_on_grid', 'no_zero_on_grid', 'bracket_only', 'nonmonotone_on_grid', 'hold']
    trial_count: int = Field(ge=2, le=256)


class BreakEvenJobResultService:
    def __init__(self, jobs, store):
        try:
            self.jobs, self.store = jobs, store
            self.plans = BreakEvenPlanSubmissionService(jobs, store)
        except Exception:
            raise ValueError('break-even job result binding rejected') from None

    def _guard(self, tenant, pointers):
        if not all(self.jobs._has_scope(tenant, scope) for scope in BREAK_EVEN_JOB_READ_SCOPES):
            raise PermissionError('break-even job result access denied')
        self.plans._binding()
        if (self.plans.jobs is not self.jobs or self.plans.store is not self.store or
                self.plans._pointers() != pointers):
            raise RuntimeError('break-even job result binding changed')

    def read_job_completion(self, tenant, job_id):
        pointers = self.plans._pointers()
        guard = lambda: self._guard(tenant, pointers)
        guard()
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, tenant, job_id)
            if job is None:
                return None
            if job['tenant_id'] != tenant or job['job_id'] != job_id:
                raise RuntimeError('break-even job identity differs')
            if job['stage'] != 'simulation' or job['state'] != 'succeeded':
                return None
            raw_input = self.jobs._verified_input(job)
        guard()
        data = json.loads(raw_input)
        if type(data) is not dict or data.get('input_version') != 'break-even-calculation-input-v1':
            return None
        value = BreakEvenPlanInput.model_validate_json(raw_input)
        if (canonical_input_bytes(value.model_dump(mode='json')) != raw_input or
                value.plan.tenant_id != tenant or value.plan.plan_id != value.request.plan_id or
                value.plan.request_sha256 != canonical_request_sha256(value.request)):
            raise RuntimeError('break-even job input differs')
        publication = self.jobs.get_publication(tenant, job_id)
        if (publication is None or type(publication.get('artifact_size')) is not int or
                not 1 <= publication['artifact_size'] <= 4096):
            raise RuntimeError('break-even completion missing')
        raw = self.jobs.read_artifact(tenant, job_id)
        if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
            raise RuntimeError('break-even completion missing')
        receipt = json.loads(raw)
        if type(receipt) is not dict or raw != canonical_input_bytes(receipt):
            raise RuntimeError('break-even receipt invalid')
        for key in ('result_sha256', 'code_sha256', 'environment_sha256'):
            if type(receipt.get(key)) is not str or not re.fullmatch(r'[0-9a-f]{64}', receipt[key]):
                raise RuntimeError('break-even receipt digest invalid')
        if receipt.get('calculation_status') not in (
                'zero_on_grid', 'no_zero_on_grid', 'bracket_only', 'nonmonotone_on_grid', 'hold'):
            raise RuntimeError('break-even receipt status invalid')
        expected = {'receipt_version': 'break-even-calculation-result-v1', 'status': 'completed',
            'claim_scope': 'conditional_user_grid_only', 'plan_id': value.plan.plan_id,
            'request_sha256': value.plan.request_sha256,
            'plan_sha256': sha256(canonical_input_bytes(value.plan.model_dump(mode='json'))).hexdigest(),
            'result_sha256': receipt['result_sha256'], 'calculation_status': receipt['calculation_status'],
            'assessment_status': 'hold', 'scan_version': 'break-even-grid-v1',
            'formula_version': FORMULA_VERSION, 'code_sha256': receipt['code_sha256'],
            'environment_sha256': receipt['environment_sha256']}
        if receipt != expected:
            raise RuntimeError('break-even completed receipt differs')
        digest = sha256(raw).hexdigest()
        manifest = {'schema_version': '1', 'job_id': str(job_id), 'stage': 'simulation',
            'input_sha256': job['input_sha256'], 'attempt': job['attempt_count'], 'artifact_sha256': digest}
        if (publication['tenant_id'] != tenant or publication['job_id'] != job_id or
                publication['attempt'] != job['attempt_count'] or publication['decision_id'] is not None or
                publication['artifact_sha256'] != digest or publication['artifact_size'] != len(raw) or
                canonical_input_bytes(publication['manifest']) != canonical_input_bytes(manifest)):
            raise RuntimeError('break-even publication differs')
        try:
            plan = self.store.get_break_even_plan(value.plan.plan_id)
            if plan is None or canonical_input_bytes(plan) != canonical_input_bytes(value.plan.model_dump(mode='json')):
                raise RuntimeError('break-even completed plan differs')
            row = self.store._row(value.plan.plan_id)
            if row is None:
                raise RuntimeError('break-even completed result missing')
            stored_request, stored_plan, stored_result = self.store._checked(row)
            if (stored_request.model_dump(mode='json') != value.request.model_dump(mode='json') or
                    stored_plan != value.plan or
                    row['result_sha256'] != receipt['result_sha256'] or
                    stored_result.status != receipt['calculation_status']):
                raise RuntimeError('break-even completed stored bytes differ')
        finally:
            guard()
        return BreakEvenCompletion(verification='completed_bytes_only_requires_replay',
            calculation_job_id=str(job_id), calculation_attempt=job['attempt_count'],
            calculation_input_sha256=job['input_sha256'], calculation_receipt_sha256=digest,
            plan_id=value.plan.plan_id, request_sha256=value.plan.request_sha256,
            plan_sha256=receipt['plan_sha256'], result_sha256=receipt['result_sha256'],
            calculation_status=receipt['calculation_status'], trial_count=len(value.plan.trials))

    def read_job_result(self, tenant, job_id):
        completion = self.read_job_completion(tenant, job_id)
        if completion is None:
            return None
        pointers = self.plans._pointers()
        guard = lambda: self._guard(tenant, pointers)
        guard()
        try:
            read = self.store.get_break_even_read(tenant, completion.plan_id)
        finally:
            guard()
        if read is None:
            raise RuntimeError('break-even completed result missing')
        request, result = read
        if (canonical_request_sha256(request) != completion.request_sha256 or
                sha256(_result_bytes(result)).hexdigest() != completion.result_sha256 or
                result.status != completion.calculation_status):
            raise RuntimeError('break-even completed result differs')
        projected = project_break_even_result(request, result)
        guard()
        return projected
