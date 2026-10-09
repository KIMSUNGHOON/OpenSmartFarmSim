"""Admit an immutable intent to replay an actual completed calculation."""

from hashlib import sha256
from pathlib import Path
from typing import Literal
from uuid import UUID

from .api_contracts import public_job_status
from .api_job_break_even_result import BreakEvenCompletion, BreakEvenJobResultService
from .jobs import canonical_input_bytes
from .provenance import Digest
from .thermal_publisher import runtime_digests


class BreakEvenVerificationInput(BreakEvenCompletion):
    input_version: Literal['break-even-verification-input-v1']
    scan_version: Literal['break-even-grid-v1']
    formula_version: Literal['economic-ledger-v9-sales-settlement']
    code_sha256: Digest
    environment_sha256: Digest


class BreakEvenVerificationService:
    def __init__(self, jobs, store):
        self.authority = BreakEvenJobResultService(jobs, store)
        self.jobs, self.store = jobs, store

    @staticmethod
    def _digests():
        return runtime_digests(Path(__file__).resolve().parents[2])

    def _guard(self, tenant, pointers, digests):
        self.authority._guard(tenant, pointers)
        if (self.authority.jobs is not self.jobs or self.authority.store is not self.store or
                not self.jobs._has_scope(tenant, 'simulation_execute')):
            raise PermissionError('break-even verification admission denied')
        if self._digests() != digests:
            raise RuntimeError('break-even verification implementation changed')

    def prepare(self, tenant, calculation_job_id, *, check=None):
        if check is not None:
            check()
        metadata = self.authority.read_job_completion(tenant, UUID(calculation_job_id))
        if metadata is None:
            raise ValueError('completed break-even calculation unavailable')
        digests = self._digests()
        return BreakEvenVerificationInput(**metadata.model_dump(),
            input_version='break-even-verification-input-v1', scan_version='break-even-grid-v1',
            formula_version='economic-ledger-v9-sales-settlement',
            code_sha256=digests[0], environment_sha256=digests[1])

    def submit(self, tenant, calculation_job_id):
        if type(calculation_job_id) is not str or str(UUID(calculation_job_id)) != calculation_job_id:
            raise ValueError('break-even calculation job ID rejected')
        pointers, digests = self.authority.plans._pointers(), self._digests()
        guard = lambda: self._guard(tenant, pointers, digests)
        guard()
        value = self.prepare(tenant, calculation_job_id, check=guard)
        raw = canonical_input_bytes(value.model_dump(mode='json'))
        key = 'break-even-verification-v1:' + sha256(
            canonical_input_bytes({'parent': calculation_job_id, 'code': digests[0],
                                  'environment': digests[1]})).hexdigest()

        def commit_guard():
            guard()
            current = self.prepare(tenant, calculation_job_id, check=guard)
            if canonical_input_bytes(current.model_dump(mode='json')) != raw:
                raise RuntimeError('break-even verification parent changed')
            guard()

        return public_job_status(self.jobs.submit(tenant, 'simulation', value.model_dump(mode='json'),
            key, commit_guard=commit_guard))
