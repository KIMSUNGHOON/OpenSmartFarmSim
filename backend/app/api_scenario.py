"""Public thermal selection intent: fixed version acknowledgement, no approval."""

from datetime import datetime
from typing import Literal

from pydantic import Field

from .market import UnavailableMarketContext
from .provenance import FrozenContract
from .thermal_scenario_store import IDENTIFIER


class ThermalScenarioRequest(FrozenContract):
    schema_version: Literal['thermal-scenario-v1']
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_revision: str = Field(pattern=IDENTIFIER, max_length=200)
    snapshot_id: str = Field(pattern=r'^thermal-snapshot-v1:[0-9a-f]{64}$', min_length=84, max_length=84)
    decision_context_id: str = Field(pattern=IDENTIFIER, max_length=200)
    market_context: UnavailableMarketContext
    zone_id: str = Field(pattern=IDENTIFIER, max_length=200)
    goal_id: Literal['historical-thermal-replay']
    model_version: Literal['thermal-v1']
    parameter_set_version: Literal['synthetic-thermal-parameters-v1']
    origin: Literal['user']
    evidence_level: Literal['assumed']


class ThermalScenarioSummary(FrozenContract):
    scenario_id: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_revision: str = Field(pattern=IDENTIFIER, max_length=200)
    scenario_sha256: str = Field(pattern=r'^[0-9a-f]{64}$', min_length=64, max_length=64)
    status: Literal['registered_intent']
    recorded_at: datetime


def scenario_request_schema():
    schema = ThermalScenarioRequest.model_json_schema()
    definitions = schema.pop('$defs')
    if set(definitions) != {'UnavailableMarketContext'}:
        raise ValueError('scenario request schema changed')
    schema['properties']['market_context'] = definitions['UnavailableMarketContext']
    return schema


def project_scenario(record):
    value = record['scenario']
    return ThermalScenarioSummary(scenario_id=value.scenario_id, scenario_revision=value.scenario_revision,
        scenario_sha256=record['scenario_sha256'], status=record['status'], recorded_at=record['recorded_at'])
