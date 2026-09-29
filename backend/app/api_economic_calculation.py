"""Admission and verified completion lookup for deterministic economic jobs."""

from hashlib import sha256
import json
import re
from typing import Annotated

from pydantic import Field, TypeAdapter

from .api_economics import project_economic_result
from .api_economic_cash_flow import project_economic_cash_flow
from .economic_calculation_worker import (EconomicCalculationInput, EconomicCalculationWorker,
    FarmEconomicCalculationInput, ECONOMIC_INPUT, CALCULATION_SCOPES, _InputHold)
from .farm_economic_execution import FARM_ECONOMIC_SCOPES, FarmEconomicHold
from .jobs import canonical_input_bytes
from .market_result_codec import encode_market_result
from .thermal_scenario_store import IDENTIFIER


ECONOMIC_JOB_READ_SCOPES = ('metadata', 'artifact', 'market_source_read',
    'market_candidate_read', 'market_result_read', 'decision_context_read', 'market_hold_context_read')


class EconomicCalculationRequest(EconomicCalculationInput):
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


class FarmEconomicCalculationRequest(FarmEconomicCalculationInput):
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


ECONOMIC_REQUEST = TypeAdapter(Annotated[EconomicCalculationRequest | FarmEconomicCalculationRequest,
    Field(discriminator='input_version')])


def economic_request_schema():
    return {'oneOf': [model.model_json_schema() for model in
        (EconomicCalculationRequest, FarmEconomicCalculationRequest)]}


class EconomicCalculationHold(ValueError):
    pass


class EconomicCalculationService:
    def __init__(self, jobs, results, farm_scenario_service=None):
        self.jobs, self.results = jobs, results
        self.farm_scenario_service = farm_scenario_service
        try:
            EconomicCalculationWorker(jobs, results, tenant_id='binding-check',
                farm_scenario_service=farm_scenario_service)
        except Exception:
            raise ValueError('economic calculation service binding rejected') from None

    def _guard(self, tenant, worker, pointers, scopes):
        if not all(self.jobs._has_scope(tenant, scope) for scope in scopes):
            raise PermissionError('economic calculation access denied')
        worker._binding()
        if (self.jobs is not worker.jobs or self.results is not worker.results or
                self.farm_scenario_service is not worker.farm_scenario_service or worker._pointers() != pointers):
            raise RuntimeError('economic calculation service binding changed')

    @staticmethod
    def _prepare(worker, value):
        try:
            if type(value) is FarmEconomicCalculationInput:
                return canonical_input_bytes(worker._farm(value))
            return encode_market_result(worker._calculate(value))
        except (_InputHold, FarmEconomicHold):
            raise EconomicCalculationHold('economic calculation input unavailable') from None
        except ValueError:
            raise RuntimeError('economic calculation source unavailable') from None

    def submit(self, tenant, body):
        body = ECONOMIC_REQUEST.validate_python(body.model_dump(mode='json'))
        worker = EconomicCalculationWorker(self.jobs, self.results, tenant_id=tenant,
            farm_scenario_service=self.farm_scenario_service)
        pointers = worker._pointers()
        scopes = CALCULATION_SCOPES + (FARM_ECONOMIC_SCOPES if type(body) is FarmEconomicCalculationRequest else ())
        def guard():
            self._guard(tenant, worker, pointers, scopes)
        guard()
        value = ECONOMIC_INPUT.validate_python(body.model_dump(mode='json', exclude={'idempotency_key'}))
        try:
            fingerprint = self._prepare(worker, value)
        finally:
            guard()
        def final_guard():
            guard()
            try:
                if self._prepare(worker, value) != fingerprint:
                    raise RuntimeError('economic calculation input changed')
            finally:
                guard()
        key = 'economic-calculation-v1:'+sha256(body.idempotency_key.encode('ascii')).hexdigest()
        return self.jobs.submit(tenant, 'simulation', value.model_dump(mode='json'), key,
                                commit_guard=final_guard)

    def read_job_result(self, tenant, job_id):
        return self._read_job_result(tenant,job_id,project_economic_result)

    def read_job_cash_flow(self, tenant, job_id, *, after_month=None, limit=12):
        return self._read_job_result(tenant,job_id,lambda result:
            project_economic_cash_flow(result,after_month=after_month,limit=limit))

    def _read_job_result(self, tenant, job_id, project):
        worker = EconomicCalculationWorker(self.jobs, self.results, tenant_id=tenant,
            farm_scenario_service=self.farm_scenario_service)
        pointers = worker._pointers()
        scopes = ECONOMIC_JOB_READ_SCOPES
        def guard():
            self._guard(tenant, worker, pointers, scopes)
        guard()
        with self.jobs.connect() as conn:
            job = self.jobs._locked_job(conn, tenant, job_id)
            if job is None:
                return None
            if job['tenant_id'] != tenant or job['job_id'] != job_id:
                raise RuntimeError('economic job identity differs')
            if job['stage'] != 'simulation' or job['state'] != 'succeeded':
                return None
            raw_input = self.jobs._verified_input(job)
        guard()
        data = json.loads(raw_input)
        if type(data) is not dict or data.get('input_version') not in (
                'economic-calculation-input-v1', 'economic-calculation-input-v2'):
            return None
        value = ECONOMIC_INPUT.validate_json(raw_input)
        if type(value) is FarmEconomicCalculationInput:
            scopes += FARM_ECONOMIC_SCOPES
            guard()
        if canonical_input_bytes(value.model_dump(mode='json')) != raw_input:
            raise RuntimeError('economic job input differs')
        publication = self.jobs.get_publication(tenant, job_id)
        if (publication is None or type(publication.get('artifact_size')) is not int or
                not 1 <= publication['artifact_size'] <= 4096):
            raise RuntimeError('economic completion missing')
        raw = self.jobs.read_artifact(tenant, job_id)
        if type(raw) is not bytes or not 1 <= len(raw) <= 4096:
            raise RuntimeError('economic completion missing')
        receipt = json.loads(raw)
        if type(receipt) is not dict or raw != canonical_input_bytes(receipt):
            raise RuntimeError('economic receipt invalid')
        for key in ('code_sha256', 'environment_sha256'):
            if type(receipt.get(key)) is not str or not re.fullmatch(r'[0-9a-f]{64}', receipt[key]):
                raise RuntimeError('economic receipt digest invalid')
        digest = sha256(raw).hexdigest()
        manifest = {'schema_version': '1', 'job_id': str(job_id), 'stage': 'simulation',
            'input_sha256': job['input_sha256'], 'attempt': job['attempt_count'], 'artifact_sha256': digest}
        if (publication['tenant_id'] != tenant or publication['job_id'] != job_id or
                publication['attempt'] != job['attempt_count'] or publication['decision_id'] is not None or
                publication['artifact_sha256'] != digest or publication['artifact_size'] != len(raw) or
                canonical_input_bytes(publication['manifest']) != canonical_input_bytes(manifest)):
            raise RuntimeError('economic publication differs')
        try:
            result = self.results.get_market_result(value.scenario_id, value.scenario_revision)
        finally:
            guard()
        if result is None:
            raise RuntimeError('economic completed result missing')
        if (result.candidate_id != value.candidate_id or
                result.economic_scenario_sha256 != value.scenario_sha256 or
                result.economic_result.formula_version != value.formula_version):
            raise RuntimeError('economic completed result pins differ')
        expected = {'receipt_version': 'economic-calculation-result-v1', 'status': 'completed',
            'claim_scope': 'user_assumption_arithmetic_only', 'scenario_id': value.scenario_id,
            'scenario_revision': value.scenario_revision, 'scenario_sha256': value.scenario_sha256,
            'candidate_id': value.candidate_id, 'formula_version': value.formula_version,
            'market_result_id': result.result_id, 'economic_result_id': result.economic_result.result_id,
            'result_sha256': sha256(encode_market_result(result)).hexdigest(),
            'calculation_status': result.calculation_status, 'assessment_status': result.assessment_status,
            'code_sha256': receipt['code_sha256'], 'environment_sha256': receipt['environment_sha256']}
        if type(value) is FarmEconomicCalculationInput:
            expected.update(receipt_version='economic-calculation-result-v2', **worker._farm(value))
        if receipt != expected:
            raise RuntimeError('economic completed receipt differs')
        try:
            return project(result)
        finally:
            guard()
