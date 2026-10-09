"""Match a stored selection intent to the exact thermal job and verified packet."""

from .thermal_scenario_store import ThermalScenarioStore, ThermalScenarioHold


SCENARIO_SCOPES = ('thermal_scenario_read', 'thermal_snapshot_read',
                   'decision_context_read', 'market_hold_context_read')


def scenario_execution_binding(store, runs, tenant, value, report=None):
    if type(store) is not ThermalScenarioStore or store.runs is not runs:
        raise ThermalScenarioHold('thermal scenario execution binding unavailable')
    store._binding()
    record = store.get(tenant, value.scenario_id, value.scenario_revision)
    if record is None:
        raise ThermalScenarioHold('thermal scenario execution record unavailable')
    model = record['scenario']
    if (record['status'] != 'registered_intent' or record['scenario_sha256'] != value.scenario_sha256 or
            (model.tenant_id, model.scenario_id, model.scenario_revision, model.snapshot_id) !=
            (tenant, value.scenario_id, value.scenario_revision, value.snapshot_id)):
        raise ThermalScenarioHold('thermal scenario execution pins differ')
    if report is not None and (
            (report['tenant_id'], report['snapshot_id'], report['decision_context_id']) !=
            (tenant, model.snapshot_id, model.decision_context_id) or
            report['context_sha256'] != record['pins']['context_sha256'] or
            report['manifest_sha256'] != record['pins']['manifest_sha256']):
        raise ThermalScenarioHold('thermal scenario execution context differs')
    return {'scenario_id': model.scenario_id, 'scenario_revision': model.scenario_revision,
            'scenario_sha256': record['scenario_sha256'], 'scenario_pins': record['pins']}
