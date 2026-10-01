"""Read actual completed replay evidence and recheck current dependencies without arithmetic."""

from hashlib import sha256
import json

from .api_break_even import project_break_even_result
from .api_job_break_even_result import BreakEvenJobResultService
from .break_even_reference_read import recheck_replay_dependencies
from .break_even_replay import BreakEvenReplayEvidence
from .break_even_store import _canonical
from .break_even_verification import BreakEvenVerificationInput, BreakEvenVerificationService
from .jobs import canonical_input_bytes


class BreakEvenVerifiedResultService:
    def __init__(self, jobs, store):
        self.authority = BreakEvenJobResultService(jobs, store)
        self.jobs, self.store = jobs, store

    def _guard(self, tenant, pointers):
        self.authority._guard(tenant, pointers)
        if self.authority.jobs is not self.jobs or self.authority.store is not self.store:
            raise RuntimeError('break-even verified result binding changed')

    def read_job_result(self, tenant, job_id):
        pointers, digests = self.authority.plans._pointers(), BreakEvenVerificationService._digests()
        check = lambda: self._guard(tenant, pointers)
        check()
        try:
            return self._read(tenant, job_id, digests, check)
        finally:
            check()
            if BreakEvenVerificationService._digests() != digests:
                raise RuntimeError('break-even verified result implementation changed')

    def _read(self, tenant, job_id, digests, check):
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, tenant, job_id)
            if job is None:
                return None
            if job['tenant_id'] != tenant or job['job_id'] != job_id:
                raise RuntimeError('break-even verification identity differs')
            if job['stage'] != 'simulation' or job['state'] != 'succeeded':
                return None
            raw_input = self.jobs._verified_input(job)
        data = json.loads(raw_input)
        if type(data) is not dict or data.get('input_version') != 'break-even-verification-input-v1':
            return None
        value = BreakEvenVerificationInput.model_validate_json(raw_input)
        if (canonical_input_bytes(value.model_dump(mode='json')) != raw_input or
                (value.code_sha256, value.environment_sha256) != digests):
            raise RuntimeError('break-even verification input differs')
        check()
        publication = self.jobs.get_publication(tenant, job_id)
        if (publication is None or type(publication.get('artifact_size')) is not int or
                not 1 <= publication['artifact_size'] <= 4096):
            raise RuntimeError('break-even verification completion missing')
        raw = self.jobs.read_artifact(tenant, job_id)
        if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
            raise RuntimeError('break-even verification receipt missing')
        receipt = json.loads(raw)
        if type(receipt) is not dict or raw != canonical_input_bytes(receipt):
            raise RuntimeError('break-even verification receipt differs')
        digest = sha256(raw).hexdigest()
        manifest = {'schema_version': '1', 'job_id': str(job_id), 'stage': 'simulation',
            'input_sha256': job['input_sha256'], 'attempt': job['attempt_count'], 'artifact_sha256': digest}
        if (publication['tenant_id'] != tenant or publication['job_id'] != job_id or
                publication['attempt'] != job['attempt_count'] or publication['decision_id'] is not None or
                publication['artifact_sha256'] != digest or publication['artifact_size'] != len(raw) or
                canonical_input_bytes(publication['manifest']) != canonical_input_bytes(manifest)):
            raise RuntimeError('break-even verification publication differs')
        evidence_sha = receipt.get('evidence_sha256')
        evidence_size = receipt.get('evidence_size')
        if (type(evidence_sha) is not str or len(evidence_sha) != 64 or
                any(char not in '0123456789abcdef' for char in evidence_sha) or
                type(evidence_size) is not int or not 1 <= evidence_size <= 1048576):
            raise RuntimeError('break-even verification evidence reference differs')
        expected = {'receipt_version': 'break-even-verification-result-v1', 'status': 'completed',
            'verification_scope': 'historical_full_grid_replay_only', 'assessment_status': 'hold',
            'calculation_job_id': value.calculation_job_id, 'plan_id': value.plan_id,
            'verification_input_sha256': job['input_sha256'],
            'calculation_input_sha256': value.calculation_input_sha256,
            'calculation_receipt_sha256': value.calculation_receipt_sha256,
            'request_sha256': value.request_sha256, 'plan_sha256': value.plan_sha256,
            'result_sha256': value.result_sha256, 'evidence_sha256': evidence_sha,
            'evidence_size': evidence_size, 'trial_count': value.trial_count,
            'scan_version': value.scan_version, 'formula_version': value.formula_version,
            'code_sha256': digests[0], 'environment_sha256': digests[1]}
        if receipt != expected:
            raise RuntimeError('break-even verification receipt binding differs')
        raw_evidence = self.jobs._read_private_evidence(tenant,
            {'sha256': evidence_sha, 'size': evidence_size})
        if (type(raw_evidence) is not bytes or len(raw_evidence) != evidence_size or
                sha256(raw_evidence).hexdigest() != evidence_sha):
            raise RuntimeError('break-even verification evidence differs')
        evidence = BreakEvenReplayEvidence.model_validate_json(raw_evidence)
        if raw_evidence != _canonical(evidence.model_dump(mode='json')):
            raise RuntimeError('break-even verification evidence noncanonical')
        expected_evidence = {'evidence_version': 'break-even-replay-evidence-v1',
            'verification': 'full_grid_replay_evidence_only', 'tenant_id': tenant,
            'plan_id': value.plan_id, 'request_sha256': value.request_sha256,
            'plan_sha256': value.plan_sha256, 'result_sha256': value.result_sha256,
            'code_sha256': digests[0], 'environment_sha256': digests[1],
            'trial_count': value.trial_count}
        if evidence.model_dump(mode='json', exclude={'reads'}) != expected_evidence:
            raise RuntimeError('break-even verification evidence binding differs')
        parent = BreakEvenVerificationService(self.jobs, self.store).prepare(tenant, value.calculation_job_id)
        if canonical_input_bytes(parent.model_dump(mode='json')) != raw_input:
            raise RuntimeError('break-even verification parent differs')
        row = self.store._row(value.plan_id)
        request, plan, result = self.store._checked(row)
        if ((row['request_sha256'], row['plan_sha256'], row['result_sha256']) !=
                (value.request_sha256, value.plan_sha256, value.result_sha256) or
                len(plan.trials) != value.trial_count or len(result.trials) != value.trial_count or
                result.status != value.calculation_status):
            raise RuntimeError('break-even verified result differs')
        candidates = {item.args for item in evidence.reads if item.method == 'get_market_candidate'}
        if candidates != {(item.scenario_id, item.revision) for item in plan.trials}:
            raise RuntimeError('break-even verification candidate coverage differs')
        recheck_replay_dependencies(self.store, evidence, check=check)
        current_parent = BreakEvenVerificationService(self.jobs, self.store).prepare(tenant, value.calculation_job_id)
        if canonical_input_bytes(current_parent.model_dump(mode='json')) != raw_input:
            raise RuntimeError('break-even verification parent changed')
        check()
        return project_break_even_result(request, result)

