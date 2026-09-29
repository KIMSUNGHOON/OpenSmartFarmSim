"""Pin completed synthetic calculations to a server-validated held assessment."""

from hashlib import sha256
import json
import re
from uuid import UUID

from .api_economic_calculation import EconomicCalculationService, ECONOMIC_JOB_READ_SCOPES
from .api_job_run import read_job_run
from .cli_contracts import AuthoritySnapshot, DecisionContract, ProposalHold, _id, _utc
from .economic_calculation_worker import EconomicCalculationWorker
from .jobs import canonical_input_bytes
from .market_result_codec import encode_market_result
from .owned_fixture_collection import UUID_PATTERN
from .thermal_run_store import ThermalRunStore
from .thermal_scenario_store import ThermalScenarioStore


INPUT_VERSION = 'calculation-assessment-input-v1'
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

    def __init__(self, jobs, runs, results, scenario_store=None):
        self.jobs, self.runs, self.results, self.scenario_store = jobs, runs, results, scenario_store
        self.economic = EconomicCalculationService(jobs, results)
        self._worker = EconomicCalculationWorker(jobs, results, tenant_id='binding-check')
        try:
            self._binding()
        except Exception:
            raise ValueError('calculation assessment binding rejected') from None

    def _binding(self):
        self._worker._binding()
        holds = self.results._candidates._source._holds
        if (self._worker.jobs is not self.jobs or self._worker.results is not self.results or
                self.economic.jobs is not self.jobs or self.economic.results is not self.results or
                type(self.runs) is not ThermalRunStore or holds._context_store is not self.runs or
                not callable(self.runs._context_verifier)):
            raise RuntimeError('calculation assessment binding rejected')
        if self.scenario_store is not None:
            if (type(self.scenario_store) is not ThermalScenarioStore or
                    self.scenario_store.runs is not self.runs or self.scenario_store.holds is not holds):
                raise RuntimeError('calculation assessment scenario binding rejected')
            self.scenario_store._binding()

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
            thermal = read_job_run(self.jobs, self.runs, tenant, UUID(run_job_id), self.scenario_store)
            economic = self.economic.read_job_result(tenant, UUID(economic_job_id))
            if thermal is None or economic is None:
                raise ValueError()
            with self.jobs.connect() as conn:
                parents = [self.jobs._locked_job(conn, tenant, identifier)
                    for identifier in (run_job_id, economic_job_id)]
                for row in parents:
                    self.jobs._verified_input(row)
            if any(row['stage'] != 'simulation' or row['state'] != 'succeeded' for row in parents):
                raise ValueError()
            stored = self.runs.get_run(tenant, thermal.run_id)
            report = stored['report']
            data = json.loads(parents[1]['input_bytes'])
            result = self.results.get_market_result(data['scenario_id'], data['scenario_revision'])
            holds = self.results._candidates._source._holds
            market_hold_id = str(economic.market_hold_report_id)
            hold = holds.get_market_hold_report(market_hold_id)
            context = self.runs.get_decision_context(tenant, report['snapshot_id'], report['decision_context_id'])
            if (hold is None or context is None or
                    hold['tenant_id'] != tenant or hold['snapshot_id'] != report['snapshot_id'] or
                    any(context[key] != report[key] or hold[key] != context[key]
                        for key in ('decision_context_id', 'claim_mode', 'decision_time_kind')) or
                    context['context_sha256'] != report['context_sha256'] or
                    context['decision_at_utc'] != report['decision_at_utc'] or
                    hold['decision_at'] != _utc(context['decision_at_utc']) or
                    economic.decision_at_utc != _utc(context['decision_at_utc']) or
                    context['claim_mode'] != 'ex_post_replay' or
                    result.economic_result.result_id != economic.economic_result_id or
                    result.assessment_status != 'hold'):
                raise ValueError()
            value = {'input_version':INPUT_VERSION, 'tenant_id':tenant,
                'run_job_id':run_job_id, 'economic_job_id':economic_job_id,
                'run_id':thermal.run_id, 'economic_result_id':economic.economic_result_id,
                'thermal_input_sha256':parents[0]['input_sha256'],
                'economic_input_sha256':parents[1]['input_sha256'],
                'thermal_receipt_sha256':sha256(self.jobs.read_artifact(tenant, run_job_id)).hexdigest(),
                'economic_receipt_sha256':sha256(self.jobs.read_artifact(tenant, economic_job_id)).hexdigest(),
                'thermal_report_sha256':sha256(stored['report_raw']).hexdigest(),
                'economic_result_sha256':sha256(encode_market_result(result)).hexdigest(),
                'snapshot_id':report['snapshot_id'], 'context_sha256':context['context_sha256'],
                'market_hold_report_id':market_hold_id,
                'temporal_provenance':'ex_post_replay', 'candidate_ids':[], 'evidence_refs':[],
                **{key:context[key] for key in CONTEXT_FIELDS}}
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
        raw = canonical_input_bytes(value)
        def verify():
            self._guard(tenant, pointers, ADMISSION_SCOPES)
            current, _ = self.prepare(tenant, run_job_id, economic_job_id, scopes=ADMISSION_SCOPES)
            if canonical_input_bytes(current) != raw:
                raise CalculationAssessmentHold('calculation assessment inputs changed')
            self._guard(tenant, pointers, ADMISSION_SCOPES)
        key = INPUT_VERSION+':'+sha256(idempotency_key.encode('ascii')).hexdigest()
        return self.jobs.submit(tenant, 'assessment', value, key, commit_guard=verify)

    def verify_input(self, job, value):
        if (type(value) is not dict or value.get('input_version') != INPUT_VERSION or
                job.get('stage') != 'assessment' or
                canonical_input_bytes(value) != job.get('input_bytes') or
                sha256(job['input_bytes']).hexdigest() != job.get('input_sha256')):
            raise CalculationAssessmentHold('calculation assessment input rejected')
        current, recorded = self.prepare(job['tenant_id'], value.get('run_job_id'), value.get('economic_job_id'))
        if value != current or recorded > job['created_at']:
            raise CalculationAssessmentHold('calculation assessment pins differ')
        return current


class CalculationAssessmentContract(DecisionContract):
    VERSION = 'calculation-assessment-server-v1'

    def __init__(self, service):
        if type(service) is not CalculationAssessmentService:
            raise ValueError('calculation assessment service required')
        self.service = service
        super().__init__(self._authority, input_parser=self._parse)

    def binding_fields(self, job):
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
            {key:current[key] for key in BINDING_FIELDS},
            **{key:current[key] for key in CONTEXT_FIELDS})
