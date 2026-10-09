"""Authored values actually reach the existing deterministic thermal kernel."""

import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_input_compiler import compile_farm_inputs
from app.thermal import ThermalHold, calculate_fixture, euler_step
from app.thermal_units import quantity
from test_farm_inputs import example, parse, sources


def compile(document=None, raw=None):
    return compile_farm_inputs(parse(document or example()), *(raw or sources()),
                               review_at_utc='2026-09-28T01:00:00Z')


def step(compiled):
    document=json.loads(compiled.thermal_bytes)
    return euler_step(document['initial_state'],document['parameters'],
                      document['intervals'][0]['forcing'],document['heater'],quantity(60,'s'))


def test_compiler_preserves_weather_law_and_user_provenance_without_publishing():
    compiled=compile()
    assert compiled == compile()
    document=json.loads(compiled.thermal_bytes)
    original=json.loads(sources()[2])
    assert document['status']=='unpublished_candidate'
    assert document['parameters']['saturation_pressure_rule']==original['parameters']['saturation_pressure_rule']
    assert document['parameters']['dry_air_specific_heat']==original['parameters']['dry_air_specific_heat']
    assert document['parameters']['floor_area']['user_evidence']['origin']=='user'
    assert document['missing_evidence']==['authored_input_review','authored_snapshot_release']
    assert 'run_id' not in document
    assert 'purchased_energy' not in document
    assert step(compiled)['heat_delivered']['value']==500


@pytest.mark.parametrize('path,value,field', [
    (('heater','capacity','value'),'100','heat_delivered'),
    (('facility','envelope_conductance','value'),'100','heat_demand'),
    (('facility','floor_area','value'),'120','heat_demand'),
    (('facility','effective_heat_capacity','value'),'2000000','state_end'),
    (('initial_state','temperature','value'),'292','heat_demand'),
    (('facility','dry_air_mass','value'),'900','state_end'),
    (('facility','indoor_volume','value'),'900','relative_humidity_end'),
    (('facility','absorbed_solar_fraction','value'),'0','heat_demand'),
])
def test_authored_physical_values_change_numerical_results(path,value,field):
    baseline=step(compile())
    altered=example()
    target=altered
    for key in path[:-1]:
        target=target[key]
    target[path[-1]]=value
    result=step(compile(altered))
    assert baseline[field] != result[field]


def test_changed_forcing_affects_vapor_balance_and_reference_pins():
    altered=example()
    altered['forcing'][0]['canopy_evaporation']['value']='0.00002'
    candidate=compile(altered)
    assert candidate.farm_sha256 != compile().farm_sha256
    assert step(candidate)['state_end']['humidity_ratio'] != step(compile())['state_end']['humidity_ratio']


def test_source_or_snapshot_tampering_and_forcing_gap_rejected():
    for index in range(3):
        raw=list(sources())
        raw[index]+=b' '
        with pytest.raises(ValueError):
            compile(raw=raw)
    altered=example()
    altered['snapshot_id']='thermal-snapshot-v1:'+'b'*64
    with pytest.raises(ValueError):
        compile(altered)
    altered=example()
    altered['forcing'][1]['start']='2026-10-15T09:01:00Z'
    with pytest.raises(ValueError):
        compile(altered)


def test_unstable_parameter_and_saturated_initial_state_hold():
    altered=example()
    altered['facility']['effective_heat_capacity']['value']='1'
    with pytest.raises(ThermalHold,match='STABILITY'):
        compile(altered)
    altered=example()
    altered['initial_state']['humidity_ratio']['value']='1'
    with pytest.raises(ThermalHold,match='CONDENSATION'):
        compile(altered)


def test_all_120_authored_steps_match_original_kernel_and_repeat_exactly():
    document=json.loads(compile().thermal_bytes)
    expected=[json.loads(raw) for raw in calculate_fixture(*sources(),decision_id='test',
        decision_at_utc='2026-09-28T00:00:00Z',input_snapshot_id='test')]
    for replay in range(2):
        state=document['initial_state']
        for interval,trace in zip(document['intervals'],expected):
            for original in trace['steps']:
                result=euler_step(state,document['parameters'],interval['forcing'],
                                  document['heater'],quantity(60,'s'))
                for key in ('state_end','relative_humidity_end','heat_demand','heat_delivered',
                            'delivered_heat_energy','vapor_residual','aggregate_energy_residual'):
                    assert result[key]==original[key]
                state=result['state_end']


def test_authored_candidate_cannot_enter_existing_pinned_publisher_input_path():
    with pytest.raises(ThermalHold):
        calculate_fixture(sources()[0],sources()[1],compile().thermal_bytes,
            decision_id='test',decision_at_utc='2026-09-28T00:00:00Z',input_snapshot_id='test')
