from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
import os
import subprocess
import sys

import pytest

from app import crop_plant_startup_integration as integration
from app import crop_startup_artifact as artifact_module
from app.crop_startup_artifact import (
    StartupArtifactHold, calculate_startup_artifact, read_startup_artifact,
    MAX_PROGRAM_BYTES, MAX_ARTIFACT_BYTES,
)
from app.thermal_run_store import _canonical
from test_crop_plant_startup_integration import ROOT, PROFILES, program, REFERENCE, close

NOTICE = (ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
OPTIONS = {**PROFILES, 'notice_raw':NOTICE}


def make(candidate=None):
    return calculate_startup_artifact(_canonical(candidate or program()), **OPTIONS)


def read(raw):
    return read_startup_artifact(raw, expected_sha256=sha256(raw).hexdigest(), **OPTIONS)


def rehash(packet):
    result = packet['result']
    result['result_sha256'] = integration._hash({k:v for k,v in result.items() if k!='result_sha256'})
    packet['artifact_id'] = 'crop-startup-artifact-v1:'+sha256(_canonical(
        {k:v for k,v in packet.items() if k!='artifact_id'})).hexdigest()
    return _canonical(packet)


@pytest.fixture(scope='module')
def artifact():
    return make(program('full-removal-reentry'))


@pytest.mark.parametrize('case', REFERENCE['cases'], ids=lambda c:c['case_id'])
def test_six_independent_programs_have_exact_inputs_and_pinned_results(case):
    candidate = deepcopy(case['program']); before = deepcopy(candidate)
    raw = make(candidate); packet = read(raw)
    assert candidate==before
    assert packet['schema_version']=='crop-startup-artifact-v1'
    assert packet['claim_scope']=='synthetic_crop_math_only'
    assert packet['program_raw_utf8'].encode()==_canonical(candidate)
    assert packet['program_sha256']==sha256(_canonical(candidate)).hexdigest()
    assert all(packet['profile_raw_utf8'][k].encode()==p.raw_bytes for k,p in PROFILES.items())
    assert packet['notice_raw_utf8'].encode()==NOTICE
    assert packet['artifact_dependency_sha256']==artifact_module.ARTIFACT_DEPENDENCY_SHA256
    assert packet['result']['status']=='completed'
    for actual, expected in zip(packet['result']['samples'], case['expected'], strict=True):
        assert actual['at']==expected['at']
        for group in ('state','cumulative'):
            for key, value in expected[group].items():
                if type(value) is list:
                    for q,v in zip(actual[group][key], value, strict=True):close(q['value'], v)
                else:close(actual[group][key]['value'], value)
        close(actual['lai']['value'], expected['lai'])
        close(actual['fruit_carbohydrate_total']['value'], expected['fruit_carbohydrate_total'])
    assert len(raw)<MAX_ARTIFACT_BYTES
    assert not any(k in packet for k in ('tenant_id','farm','run_id','gate_signature','fresh_kg','ranking'))


def test_repeat_detached_read_and_no_reintegration(artifact,monkeypatch):
    assert make(program('full-removal-reentry'))==artifact
    monkeypatch.setattr(integration,'integrate_plant_startup',lambda **_:pytest.fail('reader recalculated'))
    first=read(artifact);first['result']['samples'][0]['state']['leaf']['value']=0
    assert read(artifact)['result']['samples'][0]['state']['leaf']['value']>0


def test_fresh_python_reads_bytes_without_reintegration(artifact,tmp_path):
    path=tmp_path/'artifact.json';path.write_bytes(artifact)
    child=subprocess.run([sys.executable,'-c',
        "from pathlib import Path; from test_crop_startup_artifact import read; "
        "from app import crop_plant_startup_integration as m; import sys; "
        "m.integrate_plant_startup=lambda **_: (_ for _ in ()).throw(AssertionError('reintegrated')); "
        "p=read(Path(sys.argv[1]).read_bytes()); print(p['artifact_id'])",str(path)],
        cwd=ROOT/'backend',env={**os.environ,'PYTHONPATH':'.:tests'},
        capture_output=True,text=True,timeout=10,check=True)
    assert child.stdout.strip()==read(artifact)['artifact_id']


def event_hold():
    candidate=program('positive-tail')
    candidate['events'][1]['removals']['values']['leaf']['value']=1e7
    return candidate


def test_actual_event_hold_preserves_pre_event_state_and_past_only():
    candidate=event_hold();result=read(make(candidate))['result']
    assert result['status']=='hold' and result['hold']['phase']=='event'
    assert result['hold']['at']==candidate['events'][1]['at']
    assert result['last_confirmed']['phase']=='step-end'
    assert result['last_confirmed']['at']==result['hold']['at']
    assert len(result['samples'])==3 and len(result['events'])==1
    assert all(s['at']<result['hold']['at'] for s in result['samples'])


def test_fractional_trial_hold_and_initial_hold_preserve_actual_prefix():
    candidate=program('positive-tail');candidate['events']=[];candidate['solver']['max_step_seconds']=3
    candidate['segments'][0]['removals']['values']['leaf']['value']=1e9
    result=read(make(candidate))['result']
    assert result['status']=='hold' and result['hold']['phase']=='rk4-k2'
    assert result['hold']['at'].endswith('01.500000Z')
    assert result['steps']==0 and len(result['samples'])==1
    assert result['last_confirmed']['phase']=='boundary'
    candidate=program('empty-entry')
    candidate['initial_state']['values']['temperature_sum']['value']=0
    result=read(make(candidate))['result']
    assert result['status']=='hold' and result['steps']==0
    assert not result['samples'] and not result['events'] and result['last_confirmed'] is None


@pytest.mark.parametrize('kind',['extra','observation','conflicting_id','bad_unit','nonfinite','solver_bool'])
def test_invalid_program_rejected_before_calculation(kind,monkeypatch):
    candidate=program()
    if kind=='extra':candidate['result']={}
    if kind=='observation':candidate['segments'][0]['fruit_entry']['origin']='reference_observation'
    if kind=='conflicting_id':candidate['segments'][1]['forcing']['input_id']=candidate['segments'][0]['forcing']['input_id']
    if kind=='bad_unit':candidate['initial_state']['values']['leaf']['unit']='kg'
    if kind=='solver_bool':candidate['solver']['max_step_seconds']=True
    raw=b'{"initial_state":NaN}' if kind=='nonfinite' else _canonical(candidate)
    monkeypatch.setattr(integration,'integrate_plant_startup',lambda **_:pytest.fail('invalid input calculated'))
    with pytest.raises(StartupArtifactHold):calculate_startup_artifact(raw,**OPTIONS)


@pytest.mark.parametrize('raw',[b'{"a":1,"a":1}',b'{} ',b'[]',b'\xff',b'x'*(MAX_PROGRAM_BYTES+1)])
def test_invalid_program_bytes(raw):
    with pytest.raises(StartupArtifactHold):calculate_startup_artifact(raw,**OPTIONS)


def test_trusted_digest_and_packet_bytes_limits(artifact):
    for digest in ('0'*64,None,'bad'):
        with pytest.raises(StartupArtifactHold):read_startup_artifact(artifact,expected_sha256=digest,**OPTIONS)
    for raw in (artifact+b' ',b'{"a":1,"a":1}',b'{"a":Infinity}',b'\xff',b'[]',
                b'x'*(MAX_ARTIFACT_BYTES+1),bytearray(artifact)):
        with pytest.raises(StartupArtifactHold):read(raw)


@pytest.mark.parametrize('kind',[
    'schema','model','program_version','profile','notice','code','artifact_code','helper_code','policy','allocation_policy',
    'solver','input','origin','assumption','convergence','transition','scope','unit','count','negative','bool',
    'lai','total','residual','budget','early_budget','startup_residual','startup_budget','early_startup_budget',
    'cumulative_extra','event','event_state','event_sample','event_cumulative','time','fractional_sample',
    'missing','steps','planned_bool','result_extra','packet_extra','raw_program_hash','raw_program',
])
def test_rehashed_mixed_malformed_results_rejected(artifact,kind):
    packet=json.loads(artifact);result=packet['result'];manifest=result['manifest'];sample=result['samples'][1]
    if kind=='schema':packet['schema_version']='crop-coupled-artifact-v1'
    if kind=='model':manifest['rate_model_version']='unreviewed'
    if kind=='program_version':manifest['program_version']='crop-plant-cohort-program-v1'
    if kind=='profile':packet['profile_raw_utf8']['cohort_profile']+=' '
    if kind=='notice':packet['notice_raw_utf8']+=' '
    if kind=='code':manifest['code_sha256']['integrator']='0'*64
    if kind=='artifact_code':packet['artifact_code_sha256']='0'*64
    if kind=='helper_code':packet['artifact_dependency_sha256']['legacy_artifact']='0'*64
    if kind=='policy':manifest['policy_sha256']='0'*64
    if kind=='allocation_policy':manifest['allocation_policy_sha256']='0'*64
    if kind=='solver':manifest['solver']['max_step_seconds']=2
    if kind=='input':manifest['input_sha256']='0'*64
    if kind=='origin':manifest['origins']=['reference_observation']
    if kind=='assumption':manifest['research_assumptions']=[]
    if kind=='convergence':manifest['convergence']='validated'
    if kind=='transition':manifest['startup_transition']='fourth_order'
    if kind=='scope':packet['claim_scope']='prediction'
    if kind=='unit':sample['state']['fruit_number'][0]['unit']='kg'
    if kind=='count':sample['state']['fruit_carbohydrate'].pop()
    if kind=='negative':sample['state']['buffer']['value']=-1
    if kind=='bool':sample['state']['fruit_number'][0]['value']=True
    if kind=='lai':sample['lai']['value']*=2
    if kind=='total':result['samples'][0]['fruit_carbohydrate_total']['value']+=1
    if kind=='residual':sample['carbon_residual']['value']=100
    if kind=='budget':sample['number_residual_budget']['value']=1e10
    if kind=='early_budget':result['samples'][0]['carbon_residual_budget']['value']*=2
    if kind=='startup_residual':sample['startup_diagnostics']['requested_residual']['value']=1
    if kind=='startup_budget':sample['startup_diagnostics']['requested_budget']['value']=1
    if kind=='early_startup_budget':sample['startup_diagnostics']['requested_budget']['value']*=1.5
    if kind=='cumulative_extra':sample['cumulative']['fresh_kg']={'value':1,'unit':'kg'}
    if kind=='event':result['events'][0]['removed']['fruit_number'][0]['value']*=2
    if kind=='event_state':result['events'][0]['after']['fruit_carbohydrate'][0]['value']*=2
    if kind=='event_sample':result['events'][0]['after']['temperature_sum']['value']+=1;result['events'][0]['before']['temperature_sum']['value']+=1
    if kind=='event_cumulative':sample['cumulative']['event_number']['value']+=1
    if kind=='time':sample['at']=result['samples'][0]['at']
    if kind=='fractional_sample':sample['at']=sample['at'][:-1]+'.000000Z'
    if kind=='missing':result['samples'].pop()
    if kind=='steps':result['steps']+=1
    if kind=='planned_bool':result['planned_steps']=True
    if kind=='result_extra':result['fresh_kg']=1
    if kind=='packet_extra':packet['prediction']=True
    if kind=='raw_program_hash':packet['program_sha256']='0'*64
    if kind=='raw_program':packet['program_raw_utf8']+=' '
    with pytest.raises(StartupArtifactHold):read(rehash(packet))


@pytest.mark.parametrize('kind',['retrograde','step_count','off_grid','phase','same_time_state','same_time_cumulative',
    'missing_confirmed','hold_before_confirmed','fractional_confirmed'])
def test_rehashed_hold_confirmation_must_match_saved_history_and_grid(kind):
    candidate=event_hold();packet=read(make(candidate));result=packet['result'];confirmed=result['last_confirmed']
    if kind=='retrograde':result['last_confirmed']={**deepcopy(result['samples'][0]),'phase':'boundary-after-event'};result['steps']=0
    if kind=='step_count':result['steps']-=1
    if kind=='off_grid':confirmed['at']=integration._stamp(integration._utc(confirmed['at'])-timedelta(seconds=1))
    if kind=='phase':confirmed['phase']='boundary-after-event'
    if kind=='missing_confirmed':result['last_confirmed']=None
    if kind=='hold_before_confirmed':result['hold']['at']=candidate['output_times'][1]
    if kind=='fractional_confirmed':confirmed['at']=confirmed['at'][:-1]+'.000000Z'
    if kind.startswith('same_time_'):
        candidate=program('empty-entry');candidate['solver']['max_step_seconds']=3
        candidate['segments'][0]['removals']['values']['leaf']['value']=1e9
        packet=read(make(candidate));result=packet['result'];confirmed=result['last_confirmed']
        if kind=='same_time_state':confirmed['state']['temperature_sum']['value']+=1
        else:confirmed['cumulative']['terminal_number']['value']=1e-20
    with pytest.raises(StartupArtifactHold):read(rehash(packet))


@pytest.mark.parametrize('key',['growth_profile','cohort_profile','transport_profile','notice_raw'])
def test_unpinned_constructor_inputs_rejected(key):
    options=dict(OPTIONS);options[key]=b'changed' if key=='notice_raw' else {}
    with pytest.raises(StartupArtifactHold):calculate_startup_artifact(_canonical(program()),**options)


def test_changed_validation_dependency_rejected_before_read(artifact,monkeypatch):
    monkeypatch.setattr(artifact_module,'ARTIFACT_DEPENDENCY_SHA256',{'legacy_artifact':'0'*64})
    with pytest.raises(StartupArtifactHold):read(artifact)
