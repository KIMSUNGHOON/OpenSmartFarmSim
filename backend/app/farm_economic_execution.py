"""Verify a joint selection and its actual completed thermal component."""

from hashlib import sha256
from uuid import UUID

from .api_job_run import read_job_run_completion
from .farm_replay_scenario import FarmReplayScenarioService, READ_SCOPES
from .jobs import canonical_input_bytes
from .thermal_simulation_worker import SIMULATION_INPUT, FarmSimulationInput


FARM_ECONOMIC_SCOPES = (*READ_SCOPES, 'thermal_run_read')


class FarmEconomicHold(ValueError):
    pass


def farm_economic_execution_binding(service, jobs, results, tenant, value):
    return _farm_economic_execution_completion(service, jobs, results, tenant, value)[0]


def _farm_economic_execution_completion(service, jobs, results, tenant, value):
    if (type(service) is not FarmReplayScenarioService or service.jobs is not jobs or
            service.candidates is not results._candidates or
            service.thermal.runs is not results._candidates._source._holds._context_store):
        raise FarmEconomicHold('farm economic binding unavailable')
    pointers = service._pointers()
    guard = lambda: service._guard(tenant, pointers, FARM_ECONOMIC_SCOPES)
    guard()
    try:
        thermal_id = UUID(value.thermal_job_id)
        completion = read_job_run_completion(jobs, service.thermal.runs, tenant, thermal_id, service.thermal, service)
        if completion is None or completion.farm_selection is None:
            raise ValueError()
        selected = completion.farm_selection
        economic = selected['request'].economic
        if (value.scenario_id, value.scenario_revision, value.scenario_sha256, value.candidate_id) != (
                economic.scenario_id, economic.revision, economic.sha256, economic.candidate_id):
            raise ValueError()
        with jobs.connect() as conn:
            row = jobs._locked_job(conn, tenant, thermal_id)
            raw = jobs._verified_input(row)
        thermal = SIMULATION_INPUT.validate_json(raw)
        if (type(thermal) is not FarmSimulationInput or row['stage'] != 'simulation' or
                row['state'] != 'succeeded' or row['cancel_requested'] or
                canonical_input_bytes(thermal.model_dump(mode='json')) != raw or thermal != completion.value or
                (thermal.farm_scenario_id, thermal.farm_scenario_revision, thermal.farm_scenario_sha256) !=
                (value.farm_scenario_id, value.farm_scenario_revision, value.farm_scenario_sha256)):
            raise ValueError()
        receipt = canonical_input_bytes(completion.receipt)
        if type(receipt) is not bytes or not 1 <= len(receipt) <= 4096:
            raise ValueError()
        binding = {'farm_scenario_id': value.farm_scenario_id,
            'farm_scenario_revision': value.farm_scenario_revision,
            'farm_scenario_sha256': selected['scenario_sha256'],
            'farm_bindings_sha256': sha256(canonical_input_bytes(selected['bindings'])).hexdigest(),
            'thermal_job_id': value.thermal_job_id, 'thermal_input_sha256': row['input_sha256'],
            'thermal_receipt_sha256': sha256(receipt).hexdigest(), 'thermal_run_id': completion.summary.run_id}
        return binding, completion
    except PermissionError:
        raise
    except Exception:
        raise FarmEconomicHold('farm economic selection or completion unavailable') from None
    finally:
        guard()
