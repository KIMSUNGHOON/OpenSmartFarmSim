"""Current server-derived money inputs and bounded authored parent recovery links."""

from datetime import datetime
import json
import re
from typing import Literal
from uuid import UUID

from psycopg import sql
from pydantic import Field

from .api_contracts import AuthoredThermalRunSummary, JobStatus, public_job_status
from .api_authored_thermal import AUTHORED_RUN_ID_PATTERN, read_authored_job_completion
from .api_economic_calculation import EconomicCalculationService, ECONOMIC_JOB_READ_SCOPES
from .authored_economic_execution import AUTHORED_ECONOMIC_SCOPES, authored_economic_completion
from .calculation_assessment import AUTHORED_INPUT_VERSION, AUTHORED_FIELDS, BINDING_FIELDS, CONTEXT_FIELDS
from .economic_calculation_worker import AuthoredEconomicCalculationInput, EconomicCalculationWorker
from .farm_authoring_storage import FarmAuthoringCursor
from .jobs import canonical_input_bytes
from .provenance import FrozenContract


READ_SCOPES = tuple(dict.fromkeys((*AUTHORED_ECONOMIC_SCOPES, *ECONOMIC_JOB_READ_SCOPES)))
ECONOMIC_VERSION = 'economic-calculation-input-v3'
ASSESSMENT_FIELDS = set(BINDING_FIELDS) | set(CONTEXT_FIELDS) | set(AUTHORED_FIELDS) | {
    'input_version', 'tenant_id', 'candidate_ids', 'evidence_refs'}


class AuthoredEconomicSelection(FrozenContract):
    schema_version: Literal['authored-economic-selection-v1']
    thermal_run: AuthoredThermalRunSummary
    calculation_input: AuthoredEconomicCalculationInput
    verification: Literal['requires_admission_recheck']


class AuthoredFinancialActivity(FrozenContract):
    kind: Literal['economic', 'assessment']
    job: JobStatus
    economic_job: JobStatus | None


class AuthoredFinancialHistory(FrozenContract):
    schema_version: Literal['authored-financial-history-v1']
    thermal_job_id: UUID
    run_id: str = Field(pattern=AUTHORED_RUN_ID_PATTERN)
    items: list[AuthoredFinancialActivity] = Field(max_length=50)
    next_cursor: FarmAuthoringCursor | None
    verification: Literal['requires_current_read']


class AuthoredFinancialSelectionHold(ValueError):
    pass


class AuthoredFinancialSelectionService:
    def __init__(self, economic):
        if type(economic) is not EconomicCalculationService:
            raise ValueError('trusted economic selection service required')
        self.economic = economic

    def _authority(self, tenant):
        economic = self.economic
        worker = EconomicCalculationWorker(economic.jobs, economic.results, tenant_id=tenant,
            farm_scenario_service=economic.farm_scenario_service,
            authored_run_store=economic.authored_run_store)
        pointers = worker._pointers()
        def guard():
            if self.economic is not economic:
                raise RuntimeError('authored financial authority changed')
            economic._guard(tenant, worker, pointers, READ_SCOPES)
        guard()
        return economic, guard

    @staticmethod
    def _prepare(economic, tenant, job_id):
        if economic.authored_run_store is None:
            raise AuthoredFinancialSelectionHold('authored financial authority unavailable')
        completed = read_authored_job_completion(economic.jobs, economic.authored_run_store, tenant, job_id)
        if completed is None:
            return None
        identity = completed.value
        author = economic.authored_run_store.preparer.authoring
        registered = author.read_registration(tenant, identity['scenario_id'],
            identity['scenario_revision'], identity['registration_sha256'])
        selected = registered['farm'].economic
        value = AuthoredEconomicCalculationInput(input_version=ECONOMIC_VERSION,
            scenario_id=selected.scenario_id, scenario_revision=selected.revision,
            scenario_sha256=selected.sha256, candidate_id=selected.candidate_id,
            formula_version='economic-ledger-v9-sales-settlement',
            authored_scenario_id=identity['scenario_id'],
            authored_scenario_revision=identity['scenario_revision'],
            registration_sha256=identity['registration_sha256'], thermal_job_id=str(job_id))
        binding, completed = authored_economic_completion(economic.authored_run_store,
            economic.jobs, economic.results, economic.farm_scenario_service, tenant, value)
        selection = AuthoredEconomicSelection(schema_version='authored-economic-selection-v1',
            thermal_run=completed.summary, calculation_input=value,
            verification='requires_admission_recheck')
        return selection, binding, completed, registered

    def read(self, tenant, job_id):
        economic, guard = self._authority(tenant)
        try:
            prepared = self._prepare(economic, tenant, job_id)
            return prepared[0] if prepared else None
        finally:
            guard()

    @staticmethod
    def _economic_input(jobs, row, expected):
        raw = jobs._verified_input(row)
        value = AuthoredEconomicCalculationInput.model_validate_json(raw)
        if (row['stage'] != 'simulation' or value != expected or
                raw != canonical_input_bytes(value.model_dump(mode='json')) or
                re.fullmatch(r'economic-calculation-v1:[0-9a-f]{64}', row['idempotency_key']) is None):
            raise AuthoredFinancialSelectionHold('authored financial economic link differs')
        return value

    def history(self, tenant, job_id, *, limit=20, before_created_at=None, before_job_id=None):
        if (type(job_id) is not UUID or type(limit) is not int or not 1 <= limit <= 50 or
                (before_created_at is None) != (before_job_id is None) or
                (before_created_at is not None and (type(before_created_at) is not datetime or
                 before_created_at.tzinfo is None or type(before_job_id) is not UUID))):
            raise ValueError('authored financial cursor invalid')
        economic, guard = self._authority(tenant)
        try:
            prepared = self._prepare(economic, tenant, job_id)
            if prepared is None:
                return None
            selection, binding, thermal, registered = prepared
            jobs = economic.jobs
            cursor = sql.SQL('')
            args = [tenant, 'economic-calculation-v1:%', ECONOMIC_VERSION, str(job_id),
                'calculation-assessment-input-v1:%', AUTHORED_INPUT_VERSION, str(job_id)]
            if before_created_at is not None:
                cursor = sql.SQL(' AND (created_at, job_id) < (%s, %s)')
                args.extend((before_created_at, before_job_id))
            args.append(limit + 1)
            with jobs.connect() as conn:
                rows = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND ("
                    "(stage='simulation' AND idempotency_key LIKE %s AND "
                    "convert_from(input_bytes,'UTF8')::jsonb->>'input_version'=%s AND "
                    "convert_from(input_bytes,'UTF8')::jsonb->>'thermal_job_id'=%s) OR "
                    "(stage='assessment' AND idempotency_key LIKE %s AND "
                    "convert_from(input_bytes,'UTF8')::jsonb->>'input_version'=%s AND "
                    "convert_from(input_bytes,'UTF8')::jsonb->>'run_job_id'=%s)){} "
                    'ORDER BY created_at DESC, job_id DESC LIMIT %s')
                    .format(jobs._table('jobs'), cursor), args).fetchall()
                items = []
                for row in rows:
                    linked = None
                    kind = 'economic' if row['stage'] == 'simulation' else 'assessment'
                    if kind == 'economic':
                        self._economic_input(jobs, row, selection.calculation_input)
                    else:
                        raw = jobs._verified_input(row)
                        value = json.loads(raw)
                        trace = json.loads(thermal.stored['trace_raws'][0])
                        report = thermal.stored['report']
                        expected = {'input_version': AUTHORED_INPUT_VERSION, 'tenant_id': tenant,
                            'run_job_id': str(job_id), 'run_id': selection.thermal_run.run_id,
                            'thermal_input_sha256': binding['thermal_input_sha256'],
                            'thermal_receipt_sha256': binding['thermal_receipt_sha256'],
                            'thermal_report_sha256': binding['thermal_report_sha256'],
                            'snapshot_id': registered['farm'].snapshot_id,
                            'context_sha256': report['context_sha256'],
                            'market_hold_report_id': registered['farm'].market_context.hold_report_id,
                            'decision_context_id': report['decision_context_id'],
                            'decision_at_utc': report['decision_at_utc'], 'claim_mode': 'ex_post_replay',
                            'decision_time_kind': trace['decision_time_kind'],
                            'temporal_provenance': 'ex_post_replay', 'candidate_ids': [], 'evidence_refs': [],
                            **{key: binding[key] for key in AUTHORED_FIELDS}}
                        if (raw != canonical_input_bytes(value) or set(value) != ASSESSMENT_FIELDS or
                                any(value[key] != expected[key] for key in expected) or
                                re.fullmatch(r'calculation-assessment-input-v1:[0-9a-f]{64}',
                                    row['idempotency_key']) is None):
                            raise AuthoredFinancialSelectionHold('authored financial assessment link differs')
                        parent = jobs._locked_job(conn, tenant, UUID(value['economic_job_id']))
                        if parent is None or parent['tenant_id'] != tenant:
                            raise AuthoredFinancialSelectionHold('authored financial parent unavailable')
                        self._economic_input(jobs, parent, selection.calculation_input)
                        if (value['economic_input_sha256'] != parent['input_sha256'] or
                                any(type(value[key]) is not str or re.fullmatch(r'[0-9a-f]{64}', value[key]) is None
                                    for key in ('economic_receipt_sha256', 'economic_result_sha256'))):
                            raise AuthoredFinancialSelectionHold('authored financial parent input differs')
                        linked = public_job_status(parent)
                    items.append(AuthoredFinancialActivity(kind=kind, job=public_job_status(row), economic_job=linked))
            guard()
            current = self._prepare(economic, tenant, job_id)
            if current is None or current[0] != selection or current[1] != binding:
                raise AuthoredFinancialSelectionHold('authored financial parent changed')
            next_cursor = (FarmAuthoringCursor(created_at=rows[limit-1]['created_at'], job_id=rows[limit-1]['job_id'])
                if len(rows) > limit else None)
            return AuthoredFinancialHistory(schema_version='authored-financial-history-v1', thermal_job_id=job_id,
                run_id=selection.thermal_run.run_id, items=items[:limit], next_cursor=next_cursor,
                verification='requires_current_read')
        finally:
            guard()
