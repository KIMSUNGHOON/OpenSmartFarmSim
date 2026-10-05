"""Closed metadata formatting only; real farm/file custody is tested separately."""
from copy import deepcopy
from hashlib import sha256
import json

import pytest

from app import crop_cycle_result_store as store
from app import crop_cycle_server_custody as server
from app import crop_cycle_farm_binding as farms
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_artifact as artifact
from app.thermal_run_store import _canonical


def packet():
    root='1'*64;registration='2'*64
    request={'study_id':'own-study','revision':'r1','farm':{'scenario_id':'farm-1',
        'scenario_revision':'r1','registration_sha256':registration,'crop_id':'crop-1'},
        'input':{'schema_version':inputs.VERSION,'root_sha256':root,'program_id':'own-program'},
        'rights':{'schema_version':farms.RIGHTS_VERSION,'declaration_id':'own-input','revision':'r1',
            'input_root_sha256':root,'available_at':'2026-01-01T00:00:00Z','redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}}
    binding={'version':farms.VERSION,'scope':server.SCOPE,'tenant_id':'own-tenant','request':request,
        'registration':{'registration_job_id':'00000000-0000-0000-0000-000000000001',
            'registration_sha256':registration},'input':{'root_sha256':root},
        'rights_policy_version':'own-policy-v1','binding_code_sha256':farms.CODE_SHA256}
    raw=_canonical(binding)
    progress={'version':server.VERSION,'scope':server.SCOPE,'intent_sha256':'3'*64,
        'binding_sha256':sha256(raw).hexdigest(),'input_root_sha256':root,'context_sha256':'4'*64,
        'custody_code_sha256':server.CODE_SHA256,'head_sha256':'5'*64,'proof_sha256':'6'*64,
        'header_sha256':'7'*64,'artifact_sha256':'8'*64,'status':'completed','commit_count':1,
        'steps':120,'planned_steps':120,'counts':{'samples':3,'events':0},'storage_bytes':36006,'file_count':6}
    return json.loads(store._packet(raw,_canonical(progress),'own-resolver-v1',b'owned fixture notice'))


def encoded(value):
    value=deepcopy(value);value.pop('result_id',None)
    value['result_id']=store.VERSION+':'+sha256(_canonical(value)).hexdigest()
    return _canonical(value)


def test_closed_reference_round_trip_retains_original_counts_and_binding():
    p=packet();raw=encoded(p)
    assert store._decode(raw)==p and p['binding']['scope']=='synthetic_crop_math_only'
    assert set(p)=={'schema_version','status','claim_scope','result_id','tenant_id','study_id','revision',
        'farm','input_root_sha256','artifact','binding','policies','code'}
    assert p['artifact']['ref']==artifact.VERSION+':'+p['artifact']['sha256']
    assert p['artifact']['sample_count']==3 and p['artifact']['event_count']==0


@pytest.mark.parametrize('path',[(),('farm',),('artifact',),('binding',),('policies',),('code',),
    ('policies','server_progress'),('policies','server_progress','counts')])
@pytest.mark.parametrize('kind',['extra','missing','null'])
def test_closed_objects_reject_valid_id_extra_missing_and_null(path,kind):
    p=packet();node=p
    for k in path:node=node[k]
    if kind=='extra':node['external_file_path']='/tmp/untrusted'
    elif kind=='missing':node.pop(next(iter(node)))
    elif path:
        parent=p
        for k in path[:-1]:parent=parent[k]
        parent[path[-1]]=None
    else:p=None
    with pytest.raises(server.CycleCustodyHold):store._decode(_canonical(p) if p is None else encoded(p))


@pytest.mark.parametrize('path,value',[
    (('schema_version',),'other'),(('claim_scope',),'crop_prediction'),(('status',),'published'),
    (('tenant_id',),'other'),(('study_id',),'other'),(('revision',),'other'),
    (('farm','registration_job_id'),'not-a-uuid'),(('farm','registration_sha256'),'0'*64),
    (('input_root_sha256',),'0'*64),
    (('binding','version'),'other'),(('binding','binding_code_sha256'),'0'*64),
    (('policies','input_rights_version'),'other'),(('policies','resolver_version'),''),
    (('policies','notice_sha256'),'bad'),(('policies','server_progress','scope'),'production'),
    (('policies','server_progress','binding_sha256'),'0'*64),
    (('policies','server_progress','custody_code_sha256'),'0'*64),
    (('policies','server_progress','header_sha256'),'0'*64),
    (('policies','server_progress','artifact_sha256'),None),
    (('policies','server_progress','status'),'yielded'),
    (('artifact','steps'),True),(('artifact','planned_steps'),121),
    (('artifact','sample_count'),3.0),(('artifact','event_count'),-1),
    (('artifact','commit_count'),0),(('artifact','storage_bytes'),0),
    (('artifact','file_count'),artifact.LIMITS['files']+1),
    (('code','storage_code_sha256'),'0'*64),(('code','schema_code_sha256'),'0'*64),
    (('code','server_dependency_sha256'),{}),
])
def test_rehashed_closed_packet_rejects_wrong_identity_types_and_mixed_reference(path,value):
    p=packet();node=p
    for k in path[:-1]:node=node[k]
    node[path[-1]]=value
    with pytest.raises(server.CycleCustodyHold):store._decode(encoded(p))


@pytest.mark.parametrize('kind',['space','duplicate','utf8','oversize','wrong-id'])
def test_raw_metadata_must_be_canonical_bounded_and_self_addressed(kind):
    raw=encoded(packet())
    if kind=='space':raw+=b' '
    if kind=='duplicate':raw=raw[:-1]+b',"status":"stored_unpublished_research"}'
    if kind=='utf8':raw=b'\xff'
    if kind=='oversize':raw=b' '* (store.MAX_PACKET_BYTES+1)
    if kind=='wrong-id':
        p=json.loads(raw);p['result_id']=store.VERSION+':'+'0'*64;raw=_canonical(p)
    with pytest.raises(server.CycleCustodyHold):store._decode(raw)


def test_numerical_hold_keeps_partial_counts_and_is_not_completed():
    p=packet();p['policies']['server_progress']['status']=p['artifact']['status']='hold'
    p['policies']['server_progress']['steps']=p['artifact']['steps']=0
    assert store._decode(encoded(p))['artifact']['status']=='hold'
