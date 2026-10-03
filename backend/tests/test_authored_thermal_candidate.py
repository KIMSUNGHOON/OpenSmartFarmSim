"""Complete authored thermal trajectory remains an unpublished candidate."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.authored_thermal_candidate import (AuthoredThermalCandidateHold,
    calculate_authored_candidate, verify_authored_candidate, _calculate,
    _code_sha256)
from app.farm_input_compiler import compile_farm_inputs
from app.thermal import ThermalHold, calculate_fixture
from test_farm_inputs import example, parse, sources
from test_farm_authoring_storage import authoring, request
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope


def pure(document=None):
    compiled=compile_farm_inputs(parse(document or example()),*sources(),
        review_at_utc='2026-09-28T01:00:00Z')
    return _calculate(compiled,'a'*64,'b'*64,_code_sha256())


def test_all_120_steps_replay_original_kernel_and_carry_exact_state():
    candidate=pure()
    again=pure()
    assert candidate==again
    traces=[json.loads(raw) for raw in candidate.trace_raws]
    original=[json.loads(raw) for raw in calculate_fixture(*sources(),decision_id='test',
        decision_at_utc='2026-09-28T00:00:00Z',input_snapshot_id='test')]
    assert len(traces)==len(original)==2
    assert [len(trace['steps']) for trace in traces]==[60,60]
    assert all(trace['status']=='unpublished_candidate' and
        trace['claim_scope']=='synthetic_software_only' and
        'run_id' not in trace and 'purchased_energy' not in trace for trace in traces)
    assert traces[1]['initial_state']['temperature']['previous_trace_sha256']==sha256(candidate.trace_raws[0]).hexdigest()
    assert traces[1]['initial_state']['temperature']['value']==traces[0]['steps'][-1]['state_end']['temperature']['value']
    assert traces[1]['initial_state']['humidity_ratio']['value']==traces[0]['steps'][-1]['state_end']['humidity_ratio']['value']
    for got,expected in zip(traces,original):
        for actual_step,original_step in zip(got['steps'],expected['steps']):
            for name in ('state_start','state_end','heat_demand','heat_delivered',
                         'delivered_heat_energy','vapor_residual','aggregate_energy_residual',
                         'relative_humidity_end','convergence_deltas'):
                assert actual_step[name]==original_step[name]
            assert actual_step['start_utc']==original_step['start_utc']
            assert actual_step['end_utc']==original_step['end_utc']
    assert candidate.trace_sha256==tuple(sha256(raw).hexdigest() for raw in candidate.trace_raws)


def test_facility_and_forcing_changes_alter_timed_trajectory():
    baseline=json.loads(pure().trace_raws[0])
    changed=example()
    changed['facility']['envelope_conductance']['value']='100'
    lower_loss=json.loads(pure(changed).trace_raws[0])
    assert lower_loss['steps'][0]['state_end']!=baseline['steps'][0]['state_end']
    changed=example()
    changed['forcing'][0]['canopy_evaporation']['value']='0.00002'
    evaporating=json.loads(pure(changed).trace_raws[0])
    assert evaporating['steps'][0]['state_end']['humidity_ratio']!=baseline['steps'][0]['state_end']['humidity_ratio']


def test_late_condensation_holds_whole_candidate_without_partial_trace():
    changed=example()
    changed['forcing'][1]['canopy_evaporation']['value']='0.01'
    with pytest.raises(ThermalHold):
        pure(changed)


@pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,
    'break_even_calculation':True}],indirect=True)
def test_actual_registered_candidate_replays_and_rights_revocation_holds(authoring,login_scope,monkeypatch):
    service,body,_=authoring
    accepted=service.submit('tenant-1',request(body))
    candidate=calculate_authored_candidate(service,'tenant-1','farm-1','r1',accepted.scenario_sha256)
    assert len(candidate.trace_raws)==2 and candidate.registration_sha256==accepted.scenario_sha256
    assert verify_authored_candidate(service,'tenant-1','farm-1','r1',accepted.scenario_sha256,candidate)
    tampered=replace(candidate,trace_raws=(candidate.trace_raws[0]+b' ',candidate.trace_raws[1]))
    with pytest.raises(AuthoredThermalCandidateHold):
        verify_authored_candidate(service,'tenant-1','farm-1','r1',accepted.scenario_sha256,tampered)
    monkeypatch.setattr(service.replay.candidates._source._source,
        'get_input_rights',lambda *_:None)
    with pytest.raises(AuthoredThermalCandidateHold):
        calculate_authored_candidate(service,'tenant-1','farm-1','r1',accepted.scenario_sha256)
