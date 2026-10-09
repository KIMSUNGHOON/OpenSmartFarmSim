from copy import deepcopy
from hashlib import sha256
import json
import subprocess
import sys

import pytest

from app import crop_plant_cohort_integration as integration
from app.crop_coupled_artifact import (
    CoupledArtifactHold, calculate_coupled_artifact, read_coupled_artifact,
    MAX_PROGRAM_BYTES, MAX_ARTIFACT_BYTES,
)
from app.thermal_run_store import _canonical
from test_crop_plant_cohort_integration import ROOT, PROFILES, program, REFERENCE


NOTICE=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
OPTIONS={**PROFILES,'notice_raw':NOTICE}


def make(candidate=None):
    return calculate_coupled_artifact(_canonical(candidate or program()),**OPTIONS)


def read(raw):
    return read_coupled_artifact(raw,expected_sha256=sha256(raw).hexdigest(),**OPTIONS)


def rehash(packet):
    result=packet['result']
    result['result_sha256']=integration._hash({k:v for k,v in result.items() if k!='result_sha256'})
    packet['artifact_id']='crop-coupled-artifact-v1:'+sha256(_canonical({k:v for k,v in packet.items() if k!='artifact_id'})).hexdigest()
    return _canonical(packet)


@pytest.fixture(scope='module')
def artifact():
    return make()


@pytest.mark.parametrize('index',[0,1])
def test_two_independent_reference_programs_complete_with_exact_inputs(index):
    candidate=program(index);raw=make(candidate);packet=read(raw)
    assert packet['program_raw_utf8'].encode()==_canonical(candidate)
    assert packet['program_sha256']==sha256(_canonical(candidate)).hexdigest()
    assert set(packet['profile_raw_utf8'])==set(PROFILES)
    assert all(packet['profile_raw_utf8'][k].encode()==p.raw_bytes for k,p in PROFILES.items())
    assert packet['notice_raw_utf8'].encode()==NOTICE
    result=packet['result'];assert result==integration.integrate_plant_cohorts(**candidate,**PROFILES)
    for actual,expected in zip(result['samples'],REFERENCE['cases'][index]['expected'],strict=True):
        assert actual['at']==expected['at']
        assert actual['lai']['value']==pytest.approx(float(expected['lai']),rel=5e-9)
    assert len(raw)<MAX_ARTIFACT_BYTES and packet['claim_scope']=='synthetic_crop_math_only'
    assert not any(k in packet for k in ('tenant_id','farm','run_id','gate_signature','fresh_kg','ranking'))


def test_repeat_no_reintegration_on_read_and_detached_result(artifact,monkeypatch):
    assert make()==artifact
    monkeypatch.setattr(integration,'integrate_plant_cohorts',lambda **_:pytest.fail('read recalculated'))
    first=read(artifact);first['result']['samples'][0]['state']['leaf']['value']=0
    assert read(artifact)['result']['samples'][0]['state']['leaf']['value']!=0


def test_fresh_python_reads_exact_artifact_bytes(artifact,tmp_path):
    path=tmp_path/'artifact.json';path.write_bytes(artifact)
    child=subprocess.run([sys.executable,'-c',
        "from pathlib import Path; from test_crop_coupled_artifact import read; "
        "import sys; p=read(Path(sys.argv[1]).read_bytes()); print(p['artifact_id'])",str(path)],
        cwd=ROOT/'backend',env={**__import__('os').environ,'PYTHONPATH':'.:tests'},
        capture_output=True,text=True,timeout=10,check=True)
    assert child.stdout.strip()==read(artifact)['artifact_id']


def test_actual_event_hold_is_not_completed_or_filled():
    candidate=program();candidate['events'][1]['removals']['values']['leaf']['value']=1e7
    packet=read(make(candidate));result=packet['result']
    assert result['status']=='hold' and result['hold']['phase']=='event'
    assert result['hold']['at']==candidate['events'][1]['at']
    assert len(result['samples'])==3 and result['last_confirmed']['at']==result['hold']['at']
    assert all(s['at']<result['hold']['at'] for s in result['samples'])


def test_fractional_trial_hold_time_preserves_only_confirmed_boundary():
    candidate=program();candidate['events']=[];candidate['solver']['max_step_seconds']=3
    candidate['segments'][0]['removals']['values']['leaf']['value']=1e9
    result=read(make(candidate))['result']
    assert result['status']=='hold' and result['hold']['phase']=='rk4-k2'
    assert result['hold']['at'].endswith('01.500000Z')
    assert result['steps']==0 and len(result['samples'])==1
    assert result['last_confirmed']['at']==candidate['output_times'][0]


@pytest.mark.parametrize('kind',['extra','observation','conflicting_id','bad_unit','nonfinite'])
def test_invalid_program_rejected_before_calculation(kind,monkeypatch):
    candidate=program()
    if kind=='extra':candidate['result']={}
    if kind=='observation':candidate['segments'][0]['fruit_entry']['origin']='reference_observation'
    if kind=='conflicting_id':candidate['segments'][1]['forcing']['input_id']=candidate['segments'][0]['forcing']['input_id']
    if kind=='bad_unit':candidate['initial_state']['values']['leaf']['unit']='kg'
    if kind=='nonfinite':
        raw=b'{"initial_state":NaN}'
    else:raw=_canonical(candidate)
    monkeypatch.setattr(integration,'integrate_plant_cohorts',lambda **_:pytest.fail('invalid input calculated'))
    with pytest.raises(CoupledArtifactHold):calculate_coupled_artifact(raw,**OPTIONS)


@pytest.mark.parametrize('raw',[b'{"a":1,"a":1}',b'{} ',b'[]',b'\xff',b'x'*(MAX_PROGRAM_BYTES+1)])
def test_invalid_canonical_program_bytes(raw):
    with pytest.raises(CoupledArtifactHold):calculate_coupled_artifact(raw,**OPTIONS)


def test_expected_digest_and_byte_limits(artifact):
    for digest in ('0'*64,None,'bad'):
        with pytest.raises(CoupledArtifactHold):read_coupled_artifact(artifact,expected_sha256=digest,**OPTIONS)
    with pytest.raises(CoupledArtifactHold):read_coupled_artifact(artifact+b' ',expected_sha256=sha256(artifact).hexdigest(),**OPTIONS)
    with pytest.raises(CoupledArtifactHold):read(b'x'*(MAX_ARTIFACT_BYTES+1))


@pytest.mark.parametrize('kind',['model','profile','code','policy','solver','input','origin','assumption','scope',
    'unit','count','lai','total','residual','budget','event','event_state','time','missing','steps','result_extra'])
def test_rehashed_mixed_or_malformed_artifacts_rejected(artifact,kind):
    packet=json.loads(artifact);result=packet['result'];manifest=result['manifest'];sample=result['samples'][1]
    if kind=='model':manifest['rate_model_version']='unreviewed'
    if kind=='profile':packet['profile_raw_utf8']['cohort_profile']+=' '
    if kind=='code':manifest['code_sha256']['integrator']='0'*64
    if kind=='policy':manifest['policy_sha256']='0'*64
    if kind=='solver':manifest['solver']['max_step_seconds']=1
    if kind=='input':manifest['input_sha256']='0'*64
    if kind=='origin':manifest['origins']=['reference_observation']
    if kind=='assumption':manifest['research_assumptions']=[]
    if kind=='scope':packet['claim_scope']='prediction'
    if kind=='unit':sample['state']['fruit_number'][0]['unit']='kg'
    if kind=='count':sample['state']['fruit_carbohydrate'].pop()
    if kind=='lai':sample['lai']['value']*=2
    if kind=='total':sample['fruit_carbohydrate_total']['value']*=2
    if kind=='residual':sample['carbon_residual']['value']=100
    if kind=='budget':sample['number_residual_budget']['value']=1e10
    if kind=='event':result['events'][0]['removed']['fruit_number'][0]['value']*=2
    if kind=='event_state':result['events'][0]['after']['fruit_carbohydrate'][0]['value']*=2
    if kind=='time':sample['at']=result['samples'][0]['at']
    if kind=='missing':result['samples'].pop()
    if kind=='steps':result['steps']+=1
    if kind=='result_extra':result['fresh_kg']=1
    with pytest.raises(CoupledArtifactHold):read(rehash(packet))


@pytest.mark.parametrize('key',['growth_profile','cohort_profile','transport_profile','notice_raw'])
def test_unpinned_constructor_inputs_rejected(key):
    options=dict(OPTIONS);options[key]=b'changed' if key=='notice_raw' else {}
    with pytest.raises(CoupledArtifactHold):calculate_coupled_artifact(_canonical(program()),**options)
