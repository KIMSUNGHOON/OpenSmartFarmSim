"""Build a server-owned finite plan from actual pins and admit one immutable job."""

from hashlib import sha256
from typing import Literal

from pydantic import Field
from psycopg import sql

from .api_contracts import JobStatus, public_job_status
from .api_economic_scenario import EconomicScenarioService
from .break_even import (BreakEvenRequest, BreakEvenPlan, TrialRef, _grid, _sale_and_collection,
    canonical_request_sha256, fixed_trial_sha256, fixed_shock_sha256)
from .break_even_store import BreakEvenStore
from .jobs import canonical_input_bytes
from .market_scenario import MarketScenarioService
from .provenance import FrozenContract, Name, Digest
from .thermal_scenario_store import IDENTIFIER


PLAN_SUBMISSION_SCOPES = ('metadata', 'artifact', 'simulation_execute', 'break_even_read',
    'break_even_write', 'market_source_read', 'market_candidate_read',
    'decision_context_read', 'market_hold_context_read')
PLAN_RECEIPT_SCOPES = ('metadata','artifact','break_even_read')


class PlanReceiptConflict(ValueError):
    pass


class BreakEvenPlanRequest(BreakEvenRequest):
    plan_id: Name = Field(max_length=200)


class BreakEvenTrialPin(FrozenContract):
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    revision: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_sha256: Digest


class BreakEvenPlanSubmission(FrozenContract):
    request: BreakEvenPlanRequest
    trials: tuple[BreakEvenTrialPin, ...] = Field(min_length=2, max_length=256)


class BreakEvenPlanInput(FrozenContract):
    input_version: Literal['break-even-calculation-input-v1']
    request: BreakEvenPlanRequest
    plan: BreakEvenPlan


class BreakEvenPlanAccepted(FrozenContract):
    plan_id: str
    request_sha256: Digest
    plan_sha256: Digest
    trial_count: int = Field(ge=2, le=256)
    registration_status: Literal['pinned_user_grid_intent']
    intent_job: JobStatus


class BreakEvenPlanReceipt(FrozenContract):
    plan_id: str
    submission_sha256: Digest
    intent_status: Literal['stored']
    intent_job: JobStatus


class BreakEvenPlanSubmissionService:
    def __init__(self, jobs, store):
        try:
            if type(store) is not BreakEvenStore:
                raise ValueError()
            self.jobs, self.store = jobs, store
            self.authority = EconomicScenarioService(jobs, store._source)
            self._binding()
        except Exception:
            raise ValueError('break-even plan binding rejected') from None

    def _binding(self):
        self.authority._binding()
        if (type(self.store) is not BreakEvenStore or self.authority.jobs is not self.jobs or
                self.authority.candidates is not self.store._source or
                self.store.runtime_identity != self.jobs.runtime_identity or
                not self.jobs.runtime_identity[0].break_even_calculation or
                self.store.dsn != self.jobs._dsn or self.store.schema != self.jobs.schema or
                self.store._principal_provider is not self.jobs.principal_provider):
            raise RuntimeError('break-even plan binding rejected')

    def _pointers(self):
        candidates = self.store._source
        view = candidates._source
        return (self.jobs, self.store, candidates, view, view._source, view._holds, view._holds._context_store)

    def _access(self, tenant):
        if not all(self.jobs._has_scope(tenant, scope) for scope in PLAN_SUBMISSION_SCOPES):
            raise PermissionError('break-even plan admission denied')

    def read_receipt(self,tenant,plan_id,submission_sha256):
        pointers=self._pointers()
        def guard():
            if not all(self.jobs._has_scope(tenant,scope) for scope in PLAN_RECEIPT_SCOPES):
                raise PermissionError('break-even receipt access denied')
            self._binding()
            if self._pointers()!=pointers:
                raise RuntimeError('break-even receipt binding changed')
        guard()
        try:
            key='break-even-plan-v1:'+sha256(plan_id.encode('utf-8')).hexdigest()
            with self.jobs.connect() as conn:
                row=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND stage=%s AND idempotency_key=%s FOR SHARE')
                    .format(self.jobs._table('jobs')),(tenant,'simulation',key)).fetchone()
                if row is None:return None
                value=BreakEvenPlanInput.model_validate_json(self.jobs._verified_input(row))
                if (value.request.plan_id!=plan_id or value.plan.plan_id!=plan_id or value.plan.tenant_id!=tenant
                    or value.plan.request_sha256!=canonical_request_sha256(value.request)):
                    raise RuntimeError('break-even receipt input identity differs')
                reconstructed=BreakEvenPlanSubmission(request=value.request,trials=tuple(BreakEvenTrialPin(
                    scenario_id=ref.scenario_id,revision=ref.revision,scenario_sha256=ref.scenario_sha256) for ref in value.plan.trials))
                digest=sha256(canonical_input_bytes(reconstructed.model_dump(mode='json'))).hexdigest()
                if digest!=submission_sha256:raise PlanReceiptConflict('break-even receipt intent differs')
                return BreakEvenPlanReceipt(plan_id=plan_id,submission_sha256=digest,intent_status='stored',intent_job=public_job_status(row))
        finally:
            guard()

    def _prepare(self, tenant, body, *, check=None):
        values = _grid(body.request)
        if (len(values) != len(body.trials) or
                len({(pin.scenario_id, pin.revision) for pin in body.trials}) != len(values)):
            raise ValueError('break-even grid or references differ')
        refs, fixed_inputs, fixed_shock = [], None, None
        market = MarketScenarioService(self.store._source)
        for index, (value, pin) in enumerate(zip(values, body.trials, strict=True)):
            if check is not None:
                check()
            request, scenario, record = market.validate_pinned(pin.scenario_id, pin.revision, tenant)
            if (record['economic_scenario_sha256'] != pin.scenario_sha256 or request.baseline != body.request.baseline or
                    (scenario.tenant_id, scenario.decision_at, scenario.period_start, scenario.period_end,
                     scenario.market_context) != (tenant, body.request.decision_at, body.request.period_start,
                     body.request.period_end, body.request.market_context)):
                raise ValueError('break-even candidate scope differs')
            _sale_and_collection(body.request, scenario, value)
            inputs_hash = fixed_trial_sha256(scenario, body.request.variable, body.request.sale_id)
            shock = self.store._source.get_joint_shock(request.shock.shock_id, request.shock.revision)
            shock_hash = fixed_shock_sha256(shock, body.request.variable,
                body.request.sale_id, body.request.collection_id)
            if index == 0:
                fixed_inputs, fixed_shock = inputs_hash, shock_hash
            if (inputs_hash, shock_hash) != (fixed_inputs, fixed_shock):
                raise ValueError('break-even fixed assumptions differ')
            refs.append(TrialRef(ordinal=index, value=str(value), scenario_id=pin.scenario_id,
                revision=pin.revision, scenario_sha256=pin.scenario_sha256))
            if check is not None:
                check()
        plan = BreakEvenPlan(plan_id=body.request.plan_id, tenant_id=tenant,
            request_sha256=canonical_request_sha256(body.request), fixed_inputs_sha256=fixed_inputs,
            fixed_shock_sha256=fixed_shock, immutable=True, trials=tuple(refs))
        return BreakEvenPlanInput(input_version='break-even-calculation-input-v1', request=body.request, plan=plan)

    def submit(self, tenant, body):
        self._access(tenant)
        self._binding()
        pointers = self._pointers()
        body = BreakEvenPlanSubmission.model_validate_json(canonical_input_bytes(body.model_dump(mode='json')))
        def guard():
            self._access(tenant)
            self._binding()
            if self._pointers() != pointers:
                raise RuntimeError('break-even plan binding changed')
        def prepare():
            try:
                return self._prepare(tenant, body)
            except ValueError as exc:
                if exc.__cause__ is not None:
                    raise RuntimeError('break-even source unavailable') from None
                raise
            finally:
                guard()
        guard()
        value = prepare()
        raw = canonical_input_bytes(value.model_dump(mode='json'))
        def final_guard():
            guard()
            if canonical_input_bytes(prepare().model_dump(mode='json')) != raw:
                raise RuntimeError('break-even plan input changed')
            guard()
        key = 'break-even-plan-v1:'+sha256(body.request.plan_id.encode('utf-8')).hexdigest()
        job = self.jobs.submit(tenant, 'simulation', value.model_dump(mode='json'), key, commit_guard=final_guard)
        return BreakEvenPlanAccepted(plan_id=value.plan.plan_id, request_sha256=value.plan.request_sha256,
            plan_sha256=sha256(canonical_input_bytes(value.plan.model_dump(mode='json'))).hexdigest(),
            trial_count=len(value.plan.trials), registration_status='pinned_user_grid_intent',
            intent_job=public_job_status(job))
