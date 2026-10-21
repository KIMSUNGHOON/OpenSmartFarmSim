"""Checkpoint metadata shape checks; this fixture authorizes no farm or lease."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
from app import crop_greenhouse_co2_execution_checkpoint as model


def packet():
    fixture=Path(__file__).resolve().parents[2]/'fixtures/synthetic-co2-result-projection-template-v1.json'
    p=json.loads(fixture.read_bytes())['policies']['server_progress']
    return {'version':'joint-co2-solar-execution-checkpoint-v1','scope':model.custody.SCOPE,
        'G0_G4':'not_assessed','publication_sequence':1,'input_sha256':'a'*64,'rights_or_gate_approval':False,
        **{k:p[k] for k in ('head_sha256','proof_sha256','intent_sha256','source_sha256','context_sha256',
            'time_binding_sha256','header_sha256','artifact_sha256','custody_code_sha256','provenance_sha256',
            'status','steps','planned_steps','counts')},
        'farm_binding_sha256':p['binding_sha256'],'execution_code_sha256':model.execution.CODE_SHA256,
        'checkpoint_code_sha256':model.CODE_SHA256,'custody_sequence':p['commit_count'],
        'computed_through_utc':p['times']['last_confirmed']['at']}


def test_closed_metadata_retains_original_scope_and_microsecond_utc():
    value=packet();assert model._payload(deepcopy(value))==value
    assert value['computed_through_utc']=='2026-10-01T00:00:32.123456Z'
    assert len(model.custody._canonical(value))<=8192 and value['rights_or_gate_approval'] is False


@pytest.mark.parametrize('fault',['approval','gate','family','provenance','code','steps-bool','counts-bool','utc','extra'])
def test_forged_claims_cross_family_codes_and_unusable_metadata_are_rejected(fault):
    value=packet()
    if fault=='approval':value['rights_or_gate_approval']=True
    elif fault=='gate':value['G0_G4']='G1'
    elif fault=='family':value['version']='joint-solar-execution-checkpoint-v1'
    elif fault=='provenance':value['provenance_sha256']=None
    elif fault=='code':value['execution_code_sha256']='0'*64
    elif fault=='steps-bool':value['steps']=True
    elif fault=='counts-bool':value['counts']['samples']=True
    elif fault=='utc':value['computed_through_utc']='not-a-UTC-time'
    else:value['after_rhs']={}
    with pytest.raises(ValueError):model._payload(value)


@pytest.mark.parametrize('admission,server',[(None,object()),(object(),None),(object(),object())])
def test_exact_admission_and_custody_are_required(admission,server):
    with pytest.raises(model.Co2CheckpointHold,match='^co2 checkpoint authority unavailable$'):
        model.Co2ExecutionCheckpointStore(admission,server)
