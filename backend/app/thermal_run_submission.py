"""Authenticated admission to a versioned thermal job; admission grants no gate."""

from typing import Literal

from pydantic import Field

from .job_store import JobStore
from .thermal_publisher import ThermalG1Publisher
from .thermal_scenario_store import ThermalScenarioStore, IDENTIFIER
from .thermal_scenario_execution import SCENARIO_SCOPES, scenario_execution_binding
from .thermal_simulation_worker import ScenarioSimulationInput, ThermalSimulationWorker


SUBMISSION_SCOPES = ('thermal_run_submit', 'metadata', 'artifact') + SCENARIO_SCOPES


class ThermalRunRequest(ScenarioSimulationInput):
    model_version: Literal['thermal-v1']
    parameter_set_version: Literal['synthetic-thermal-parameters-v1']
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


class ThermalRunSubmissionService:
    def __init__(self, publisher, scenarios):
        if (type(publisher) is not ThermalG1Publisher or type(scenarios) is not ThermalScenarioStore or
                type(publisher.job_store) is not JobStore or scenarios.runs is not publisher.run_store):
            raise ValueError('thermal submission binding rejected')
        self.publisher, self.scenarios = publisher, scenarios
        self.jobs = publisher.job_store
        scenarios._binding()
        if (self.jobs.runtime_identity != scenarios.runtime_identity or
                self.jobs.schema != scenarios.schema or self.jobs._dsn != scenarios.dsn or
                self.jobs.audit_runtime_grants is not True or
                self.jobs.principal_provider is not scenarios.runs._principal_provider):
            raise ValueError('thermal submission binding rejected')

    def _access(self, tenant):
        if not all(self.jobs._has_scope(tenant, scope) for scope in SUBMISSION_SCOPES):
            raise PermissionError('thermal submission denied')

    def _binding(self, tenant):
        if (type(self.publisher) is not ThermalG1Publisher or self.publisher.job_store is not self.jobs or
                type(self.scenarios) is not ThermalScenarioStore or
                self.scenarios.runs is not self.publisher.run_store):
            raise ValueError('thermal submission binding rejected')
        ThermalSimulationWorker(self.publisher, tenant_id=tenant, scenario_store=self.scenarios)

    def submit(self, tenant, body):
        self._access(tenant)
        body = ThermalRunRequest.model_validate(body.model_dump(mode='json'))
        value = ScenarioSimulationInput.model_validate(body.model_dump(mode='json', exclude={
            'model_version', 'parameter_set_version', 'idempotency_key'}))
        self._binding(tenant)
        scenario_execution_binding(self.scenarios, self.publisher.run_store, tenant, value)
        report = self.publisher.validate_submission(tenant, value.review_job_id, value.snapshot_id)
        def guard():
            self._access(tenant)
            self._binding(tenant)
            scenario_execution_binding(self.scenarios, self.publisher.run_store, tenant, value, report)
        guard()
        return self.jobs.submit(tenant, 'simulation', value.model_dump(mode='json'),
                                body.idempotency_key, commit_guard=guard)
