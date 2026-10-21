"""Closed CO2 progress DTO and exact authority checks before database access."""
from uuid import uuid4
import psycopg
import pytest
from app import crop_greenhouse_co2_execution_query as model

@pytest.mark.parametrize('fault', ['extra', 'version', 'status', 'steps', 'result', 'approval', 'approval-zero', 'checkpoint-approval', 'provenance', 'scope', 'counts-bool', 'result-family'])
def test_projection_closed_schema_and_inconsistent_progress_rejected(fault):
    at = '2026-10-01T00:00:02.123456Z'
    payload = {'version': model.VERSION, 'scope': model.custody.SCOPE, 'G0_G4': 'not_assessed', 'rights_or_gate_approval':False,
        'job': {'job_id':str(uuid4()), 'stage':'simulation', 'state':'simulating', 'attempt_count':1,
            'max_attempts':3, 'created_at':at, 'updated_at':at, 'reason_code':None},
        'cancel_requested':False, 'observed_at':at, 'checkpoint_status':'current', 'result':None,
        'checkpoint':{'head_sha256':'a'*64, 'proof_sha256':'b'*64, 'artifact_sha256':None,
            'status':'yielded', 'steps':1, 'planned_steps':16, 'counts':{'samples':2,'events':0},
            'computed_through_utc':at, 'checkpoint_recorded_at':at, 'publication_sequence':1,
            'provenance_sha256':'e'*64,'rights_or_gate_approval':False}}
    model.ExecutionRead.model_validate(payload)
    if fault == 'extra': payload['private'] = True
    elif fault == 'version': payload['version'] += '-future'
    elif fault == 'status': payload['checkpoint_status'] = 'unavailable'
    elif fault == 'steps': payload['checkpoint']['steps'] = -1
    elif fault=='approval': payload['rights_or_gate_approval']=True
    elif fault=='approval-zero': payload['rights_or_gate_approval']=0
    elif fault=='checkpoint-approval': payload['checkpoint']['rights_or_gate_approval']='false'
    elif fault=='provenance': payload['checkpoint']['provenance_sha256']='invalid'
    elif fault=='scope': payload['scope']='synthetic_joint_solar_math_only'
    elif fault=='counts-bool': payload['checkpoint']['counts']['samples']=True
    elif fault=='result-family':
        payload['checkpoint'].update(status='completed',steps=16,artifact_sha256='f'*64)
        payload['job']['state']='succeeded'
        payload['result']={'result_id':'joint-co2-solar-result-v1:'+'c'*64,'status':'completed',
            'farm':{'scenario_id':'farm','scenario_revision':'r1','registration_sha256':'d'*64,
                'crop_id':'crop','batch_id':'batch','zone_id':'zone'},
            'provenance_sha256':'e'*64,'rights_or_gate_approval':False}
        model.ExecutionRead.model_validate(payload)
        payload['result']['result_id']='joint-solar-result-v1:'+'c'*64
    else: payload['result'] = {'result_id':'joint-co2-solar-result-v1:'+'c'*64,
        'status':'completed','farm':{'scenario_id':'farm','scenario_revision':'r1','registration_sha256':'d'*64,'crop_id':'crop',
            'batch_id':'batch','zone_id':'zone'},'provenance_sha256':'e'*64,'rights_or_gate_approval':False}
    with pytest.raises(ValueError): model.ExecutionRead.model_validate(payload)

@pytest.mark.parametrize('checkpoint,result',[(None,object()),(object(),None),(object(),object())])
def test_progress_query_requires_exact_authorities_before_io(monkeypatch,checkpoint,result):
    calls=[]
    def denied(*a,**kw):calls.append(1);raise AssertionError('wrong authority used database')
    monkeypatch.setattr(psycopg,'connect',denied)
    with pytest.raises(model.Co2ExecutionQueryHold,match='^co2 execution query authority unavailable$'):
        model.Co2ExecutionQuery(checkpoint,result)
    assert calls==[]
