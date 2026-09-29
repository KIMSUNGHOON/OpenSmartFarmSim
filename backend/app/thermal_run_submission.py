"""Authenticated admission to a versioned thermal job; admission grants no gate."""

from typing import Annotated, Literal

from pydantic import Field, TypeAdapter

from .job_store import JobStore
from .thermal_publisher import ThermalG1Publisher
from .thermal_scenario_store import ThermalScenarioStore, IDENTIFIER
from .thermal_scenario_execution import SCENARIO_SCOPES, scenario_execution_binding
from .thermal_simulation_worker import (ScenarioSimulationInput, FarmSimulationInput,
    SIMULATION_INPUT, ThermalSimulationWorker)
from .farm_replay_scenario import READ_SCOPES as FARM_READ_SCOPES
from .farm_thermal_execution import farm_thermal_execution_binding, FarmThermalHold
from .owned_collection_review import REVIEW_SCOPES


SUBMISSION_SCOPES = ('thermal_run_submit', 'metadata', 'artifact') + SCENARIO_SCOPES
FARM_SUBMISSION_SCOPES = tuple(dict.fromkeys(FARM_READ_SCOPES + REVIEW_SCOPES))


class ThermalRunRequest(ScenarioSimulationInput):
    model_version: Literal['thermal-v1']
    parameter_set_version: Literal['synthetic-thermal-parameters-v1']
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


class FarmThermalRunRequest(FarmSimulationInput):
    model_version: Literal['thermal-v1']
    parameter_set_version: Literal['synthetic-thermal-parameters-v1']
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


RUN_REQUEST = TypeAdapter(Annotated[ThermalRunRequest | FarmThermalRunRequest,
    Field(discriminator='input_version')])


def run_request_schema():
    return {'oneOf': [model.model_json_schema() for model in (ThermalRunRequest, FarmThermalRunRequest)]}


class ThermalRunSubmissionService:
    def __init__(self, publisher, scenarios, farm_scenario_service=None):
        if (type(publisher) is not ThermalG1Publisher or type(scenarios) is not ThermalScenarioStore or
                type(publisher.job_store) is not JobStore or scenarios.runs is not publisher.run_store):
            raise ValueError('thermal submission binding rejected')
        self.publisher, self.scenarios = publisher, scenarios
        self.farm_scenario_service = farm_scenario_service
        self.jobs = publisher.job_store
        scenarios._binding()
        if (self.jobs.runtime_identity != scenarios.runtime_identity or
                self.jobs.schema != scenarios.schema or self.jobs._dsn != scenarios.dsn or
                self.jobs.audit_runtime_grants is not True or
                self.jobs.principal_provider is not scenarios.runs._principal_provider):
            raise ValueError('thermal submission binding rejected')

    def _access(self, tenant, farm=False):
        scopes = SUBMISSION_SCOPES + (FARM_SUBMISSION_SCOPES if farm else ())
        if not all(self.jobs._has_scope(tenant, scope) for scope in scopes):
            raise PermissionError('thermal submission denied')

    def _binding(self, tenant):
        if (type(self.publisher) is not ThermalG1Publisher or self.publisher.job_store is not self.jobs or
                type(self.scenarios) is not ThermalScenarioStore or
                self.scenarios.runs is not self.publisher.run_store):
            raise ValueError('thermal submission binding rejected')
        ThermalSimulationWorker(self.publisher, tenant_id=tenant, scenario_store=self.scenarios,
            farm_scenario_service=self.farm_scenario_service)

    def submit(self, tenant, body):
        body = RUN_REQUEST.validate_python(body.model_dump(mode='json'))
        farm = type(body) is FarmThermalRunRequest
        self._access(tenant, farm)
        value = SIMULATION_INPUT.validate_python(body.model_dump(mode='json', exclude={
            'model_version', 'parameter_set_version', 'idempotency_key'}))
        self._binding(tenant)
        scenario_execution_binding(self.scenarios, self.publisher.run_store, tenant, value)
        expected_farm = (farm_thermal_execution_binding(self.farm_scenario_service, self.jobs, tenant, value)
            if farm else None)
        report = self.publisher.validate_submission(tenant, value.review_job_id, value.snapshot_id)
        def guard():
            self._access(tenant, farm)
            self._binding(tenant)
            scenario_execution_binding(self.scenarios, self.publisher.run_store, tenant, value, report)
            if farm and farm_thermal_execution_binding(
                    self.farm_scenario_service, self.jobs, tenant, value,
                    report | {'review_job_id':value.review_job_id}) != expected_farm:
                raise FarmThermalHold('farm thermal admission pins differ')
        guard()
        return self.jobs.submit(tenant, 'simulation', value.model_dump(mode='json'),
                                body.idempotency_key, commit_guard=guard)
