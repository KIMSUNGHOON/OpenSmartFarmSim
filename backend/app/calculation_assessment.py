"""Pin completed synthetic calculations to a server-validated held assessment."""

from hashlib import sha256
import json
import re
from uuid import UUID

from .api_economic_calculation import EconomicCalculationService, ECONOMIC_JOB_READ_SCOPES
from .api_economics import project_economic_result
from .api_job_run import read_job_run_completion
from .cli_contracts import AuthoritySnapshot, DecisionContract, ProposalHold, _id, _utc
from .economic_calculation_worker import EconomicCalculationWorker
from .farm_economic_execution import FARM_ECONOMIC_SCOPES
from .jobs import canonical_input_bytes
from .market_result_codec import encode_market_result
from .owned_fixture_collection import UUID_PATTERN
from .thermal_run_store import ThermalRunStore
from .thermal_scenario_store import ThermalScenarioStore


INPUT_VERSION = 'calculation-assessment-input-v1'
FARM_INPUT_VERSION = 'calculation-assessment-input-v2'
FARM_FIELDS = ('farm_scenario_id', 'farm_scenario_revision', 'farm_scenario_sha256', 'farm_bindings_sha256')
CONTEXT_FIELDS = ('decision_context_id', 'decision_at_utc', 'claim_mode', 'decision_time_kind')
READ_SCOPES = (*ECONOMIC_JOB_READ_SCOPES, 'thermal_run_read', 'thermal_snapshot_read')
ADMISSION_SCOPES = ('assessment_create', *READ_SCOPES)
BINDING_FIELDS = frozenset({'run_job_id', 'economic_job_id', 'run_id', 'economic_result_id',
    'thermal_input_sha256', 'economic_input_sha256', 'thermal_receipt_sha256',
    'economic_receipt_sha256', 'thermal_report_sha256', 'economic_result_sha256',
    'snapshot_id', 'context_sha256', 'market_hold_report_id', 'temporal_provenance'})


class CalculationAssessmentHold(ValueError):
    pass


class CalculationAssessmentService:
    MISSING_EVIDENCE = ('market_source_g0', 'eligible_crop_candidates', 'farm_scenario_binding',
        'local_measurements_g2', 'future_validation_g3a', 'paired_comparison_g3b')

    def __init__(self, jobs, runs, results, scenario_store=None, farm_scenario_service=None):
        self.jobs, self.runs, self.results, self.scenario_store = jobs, runs, results, scenario_store
        self.farm_scenario_service = farm_scenario_service
        self.economic = EconomicCalculationService(jobs, results, farm_scenario_service)
        self._worker = EconomicCalculationWorker(jobs, results, tenant_id='binding-check',
            farm_scenario_service=farm_scenario_service)
        try:
            self._binding()
        except Exception:
            raise ValueError('calculation assessment binding rejected') from None

    def _binding(self):
        self._worker._binding()
        holds = self.results._candidates._source._holds
        if (self._worker.jobs is not self.jobs or self._worker.results is not self.results or
                self.economic.jobs is not self.jobs or self.economic.results is not self.results or
                self.economic.farm_scenario_service is not self.farm_scenario_service or
                self._worker.farm_scenario_service is not self.farm_scenario_service or
                type(self.runs) is not ThermalRunStore or holds._context_store is not self.runs or
                not callable(self.runs._context_verifier)):
            raise RuntimeError('calculation assessment binding rejected')
        if self.scenario_store is not None:
            if (type(self.scenario_store) is not ThermalScenarioStore or
                    self.scenario_store.runs is not self.runs or self.scenario_store.holds is not holds):
                raise RuntimeError('calculation assessment scenario binding rejected')
            self.scenario_store._binding()
        if (self.farm_scenario_service is not None and
                self.farm_scenario_service.thermal is not self.scenario_store):
            raise RuntimeError('calculation assessment farm binding rejected')

    def _pointers(self):
        return (*self._worker._pointers(), self.economic, self.runs, self.scenario_store,
            self.jobs._dsn, self.jobs.schema, self.jobs.runtime_identity, self.jobs.principal_provider,
            self.jobs.artifact_root, self.jobs.content_access, self.runs._context_verifier,
            self.runs._release_verifier)

    def _guard(self, tenant, pointers, scopes):
        self._binding()
        if self._pointers() != pointers:
            raise RuntimeError('calculation assessment binding changed')
        if not all(self.jobs._has_scope(tenant, scope) for scope in scopes):
            raise PermissionError('calculation assessment access denied')

    def prepare(self, tenant, run_job_id, economic_job_id, *, scopes=READ_SCOPES):
        pointers = self._pointers()
        guard = lambda: self._guard(tenant, pointers, scopes)
        guard()
        try:
            if any(type(value) is not str or not re.fullmatch(UUID_PATTERN, value)
                   for value in (run_job_id, economic_job_id)):
                raise ValueError()
            with self.jobs.connect() as conn:
                parents = [self.jobs._locked_job(conn, tenant, identifier)
                    for identifier in (run_job_id, economic_job_id)]
                for row in parents:
                    self.jobs._verified_input(row)
            if any(row['stage'] != 'simulation' or row['state'] != 'succeeded' or row['cancel_requested']
                   for row in parents):
                raise ValueError()
            inputs = [json.loads(row['input_bytes']) for row in parents]
            farm = inputs[0].get('input_version') == 'thermal-simulation-input-v3'
            if farm != (inputs[1].get('input_version') == 'economic-calculation-input-v2'):
                raise ValueError()
            if farm:
                scopes += FARM_ECONOMIC_SCOPES
                guard()
                if inputs[1].get('thermal_job_id') != run_job_id:
                    raise ValueError()
            economic = self.economic._read_job_completion(tenant, UUID(economic_job_id))
            thermal = (economic.thermal_completion if farm and economic is not None else
                read_job_run_completion(self.jobs, self.runs, tenant, UUID(run_job_id), self.scenario_store))
            if (thermal is None or economic is None or
                    inputs[0] != thermal.value.model_dump(mode='json') or
                    inputs[1] != economic.value.model_dump(mode='json')):
                raise ValueError()
            stored = thermal.stored
            report = stored['report']
            result = economic.result
            public_economic = project_economic_result(result)
            holds = self.results._candidates._source._holds
            market_hold_id = str(public_economic.market_hold_report_id)
            hold = holds.get_market_hold_report(market_hold_id)
            context = self.runs.get_decision_context(tenant, report['snapshot_id'], report['decision_context_id'])
            if (hold is None or context is None or
                    hold['tenant_id'] != tenant or hold['snapshot_id'] != report['snapshot_id'] or
                    any(context[key] != report[key] or hold[key] != context[key]
                        for key in ('decision_context_id', 'claim_mode', 'decision_time_kind')) or
                    context['context_sha256'] != report['context_sha256'] or
                    context['decision_at_utc'] != report['decision_at_utc'] or
                    hold['decision_at'] != _utc(context['decision_at_utc']) or
                    public_economic.decision_at_utc != _utc(context['decision_at_utc']) or
                    context['claim_mode'] != 'ex_post_replay' or
                    result.assessment_status != 'hold'):
                raise ValueError()
            value = {'input_version':FARM_INPUT_VERSION if farm else INPUT_VERSION, 'tenant_id':tenant,
                'run_job_id':run_job_id, 'economic_job_id':economic_job_id,
                'run_id':thermal.summary.run_id, 'economic_result_id':result.economic_result.result_id,
                'thermal_input_sha256':parents[0]['input_sha256'],
                'economic_input_sha256':parents[1]['input_sha256'],
                'thermal_receipt_sha256':sha256(canonical_input_bytes(thermal.receipt)).hexdigest(),
                'economic_receipt_sha256':sha256(canonical_input_bytes(economic.receipt)).hexdigest(),
                'thermal_report_sha256':sha256(stored['report_raw']).hexdigest(),
                'economic_result_sha256':sha256(encode_market_result(result)).hexdigest(),
                'snapshot_id':report['snapshot_id'], 'context_sha256':context['context_sha256'],
                'market_hold_report_id':market_hold_id,
                'temporal_provenance':'ex_post_replay', 'candidate_ids':[], 'evidence_refs':[],
                **{key:context[key] for key in CONTEXT_FIELDS}}
            if farm:
                if any(thermal.receipt[key] != economic.receipt[key] for key in FARM_FIELDS):
                    raise ValueError()
                value.update({key:economic.receipt[key] for key in FARM_FIELDS})
            return value, max(context['recorded_at'], stored['recorded_at'],
                              *(row['updated_at'] for row in parents))
        except PermissionError:
            raise
        except Exception:
            raise CalculationAssessmentHold('calculation assessment inputs unavailable') from None
        finally:
            guard()

    def submit(self, tenant, run_job_id, economic_job_id, idempotency_key):
        if not _id(idempotency_key):
            raise ValueError('calculation assessment key rejected')
        pointers = self._pointers()
        value, _ = self.prepare(tenant, run_job_id, economic_job_id, scopes=ADMISSION_SCOPES)
        scopes = ADMISSION_SCOPES + (FARM_ECONOMIC_SCOPES if value['input_version'] == FARM_INPUT_VERSION else ())
        raw = canonical_input_bytes(value)
        def verify():
            self._guard(tenant, pointers, scopes)
            current, _ = self.prepare(tenant, run_job_id, economic_job_id, scopes=scopes)
            if canonical_input_bytes(current) != raw:
                raise CalculationAssessmentHold('calculation assessment inputs changed')
            self._guard(tenant, pointers, scopes)
        key = INPUT_VERSION+':'+sha256(idempotency_key.encode('ascii')).hexdigest()
        return self.jobs.submit(tenant, 'assessment', value, key, commit_guard=verify)

    def verify_input(self, job, value):
        if (type(value) is not dict or value.get('input_version') not in (INPUT_VERSION, FARM_INPUT_VERSION) or
                job.get('stage') != 'assessment' or
                canonical_input_bytes(value) != job.get('input_bytes') or
                sha256(job['input_bytes']).hexdigest() != job.get('input_sha256')):
            raise CalculationAssessmentHold('calculation assessment input rejected')
        current, recorded = self.prepare(job['tenant_id'], value.get('run_job_id'), value.get('economic_job_id'))
        if value != current or recorded > job['created_at']:
            raise CalculationAssessmentHold('calculation assessment pins differ')
        return current


class CalculationAssessmentContract(DecisionContract):
    VERSION = 'calculation-assessment-server-v2'

    def __init__(self, service):
        if type(service) is not CalculationAssessmentService:
            raise ValueError('calculation assessment service required')
        self.service = service
        super().__init__(self._authority, input_parser=self._parse)

    def binding_fields(self, job):
        value = json.loads(job['input_bytes'])
        if value.get('input_version') == FARM_INPUT_VERSION:
            return BINDING_FIELDS | frozenset(FARM_FIELDS)
        return BINDING_FIELDS

    def _parse(self, job, value):
        try:
            return self.service.verify_input(job, value)
        except Exception:
            raise ProposalHold('calculation_assessment_hold') from None

    def _authority(self, job, value):
        current = self.service.verify_input(job, value)
        return AuthoritySnapshot(job['tenant_id'], 'assessment', job['input_sha256'],
            frozenset(), {}, False, self.service.MISSING_EVIDENCE, {}, frozenset(), False,
            {key:current[key] for key in self.binding_fields(job)},
            **{key:current[key] for key in CONTEXT_FIELDS})
