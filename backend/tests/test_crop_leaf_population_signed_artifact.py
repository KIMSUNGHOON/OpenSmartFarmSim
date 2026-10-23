"""Real leaf numerical producer with explicit unit doubles for the farm boundary."""
from copy import deepcopy
from hashlib import sha256
import hmac
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.content_access import ContentAccess
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
import test_crop_leaf_population_farm_binding as controls
import test_crop_leaf_population_input_evidence as inputs


KEY=b'owned-leaf-result-software-test-key-32!'
PUBLIC=inputs.ROOT/'web/public/leaf-population-replay'


@pytest.fixture
def prepared(tmp_path,monkeypatch,request):
    model=importlib.import_module('app.crop_leaf_population_signed_artifact')
    producer=importlib.import_module('app.crop_leaf_population_signed_producer')
    shell,body,parent,packet=controls.prepared(model.farms)
    invalid=getattr(request,'param',None)
    if invalid:
        program=json.loads(packet['program_raw'])
        if invalid=='initial':program['initialization']['initial_inventory']['leaves'][0]['initialization']['initial_area']['value']*=2
        else:program['births'][0]['initial_area']['value']*=2
        raw,source=inputs.source_for(inputs.canonical(program));authority,args=inputs.configured(model.farms.evidence,raw,source)
        packet=dict(program_raw=raw,source_raw=source,evidence_raw=authority.issue(**args));shell.input_authority=authority
        parent['packet']={k:args['stem_arguments'][k] for k in ('program_raw','source_raw','evidence_raw')}
        parent['proof']['input_evidence_sha256']=sha256(parent['packet']['evidence_raw']).hexdigest()
        body['input'].update(program_sha256=sha256(raw).hexdigest(),source_sha256=sha256(source).hexdigest(),evidence_sha256=sha256(packet['evidence_raw']).hexdigest())
        body['rights']['input_source_sha256']=sha256(source).hexdigest()
    source=shell._input(body,parent,packet);access=ContentAccess(os.getuid(),os.getgid());stem=tmp_path/'stem'
    root=produce_rational_morphology_artifact(stem,access,program_raw=parent['packet']['program_raw'])
    assert root==body['parent']['numerical_root_sha256']
    summary={**body['parent'],'program_sha256':parent['proof']['program_sha256'],
        'source_sha256':parent['proof']['source_sha256'],'input_evidence_sha256':parent['proof']['input_evidence_sha256'],
        'binding_sha256':'3'*64,'calculated_at':'2026-10-22T00:00:00.000000Z'}
    binding={'version':model.farms.VERSION,'scope':'synthetic_leaf_population_input_binding_only','tenant_id':'tenant-1',
        'G0_G4':'not_assessed','rights_or_gate_approval':False,'numerical_initial_state_validation':False,
        'request':body,'registration':parent['binding']['registration'],'parent':summary,
        'parent_result_binding_verified':True,'input':source}
    raw_binding=inputs.canonical(binding);state={'allowed':True,'prepare':0,'current':[]}
    def checked(tenant,raw,expected=None,**kw):
        if tenant!='tenant-1':raise PermissionError('foreign tenant')
        if not state['allowed']:raise model.farms.LeafPopulationFarmBindingHold('owned current revoked')
        assert raw==inputs.canonical(body) and {k:kw[k] for k in packet}==packet
        if expected is None:state['prepare']+=1
        else:assert expected==raw_binding;state['current'].append(kw.get('write',False))
        return raw_binding
    monkeypatch.setattr(model.farms.LeafPopulationFarmBinding,'_binding',lambda self:None)
    monkeypatch.setattr(model.farms.LeafPopulationFarmBinding,'prepare',lambda self,t,r,**kw:checked(t,r,**kw))
    monkeypatch.setattr(model.farms.LeafPopulationFarmBinding,'current',lambda self,t,r,e,**kw:checked(t,r,e,**kw))
    shell._fixed=('owned-unit-double',);shell.parent_authority=SimpleNamespace(directory=stem,access=access)
    authority=model.LeafPopulationArtifactAuthority(shell,directory=tmp_path/'leaf',access=access,
        integrity_key=KEY,issuer_id='owned-software',key_id='owned-leaf-result-key')
    return model,producer,authority,body,packet,state


def publish(value):
    _,producer,authority,body,packet,_=value
    return producer.produce_registered_leaf_population(authority,'tenant-1',inputs.canonical(body),**packet)


def test_actual_one_producer_all_original_frames_replay_and_no_recalculation(prepared,monkeypatch):
    model,producer,authority,body,_,state=prepared;actual=producer.numerical.produce_leaf_population_artifact;calls=[]
    def calculate(*a,**kw):calls.append(1);return actual(*a,**kw)
    monkeypatch.setattr(producer.numerical,'produce_leaf_population_artifact',calculate)
    before={f.name:sha256(f.read_bytes()).hexdigest() for f in authority.farm_binding.parent_authority.directory.iterdir()}
    result=publish(prepared);assert calls==[1] and state['prepare']==1 and all(state['current'])
    assert KEY not in (authority.directory/result).read_bytes()
    monkeypatch.setattr(producer.numerical,'produce_leaf_population_artifact',lambda *a,**kw:pytest.fail('query calculated'))
    manifest=authority.read_manifest('tenant-1',result);replay=authority.read_replay('tenant-1',result)
    assert manifest['manifest']==json.loads((PUBLIC/'root.json').read_bytes())==replay['manifest']
    assert manifest['parent_job_id']==body['parent']['job_id'] and manifest['parent_result_sha256']==body['parent']['result_sha256']
    assert manifest['profile_applicability']=='unvalidated_for_registered_crop' and manifest['gates']=='not_assessed'
    for index in range(12):
        value=authority.read_frame('tenant-1',result,index=index);original=(PUBLIC/f'frame-{index}.json').read_bytes()
        assert inputs.canonical(value['frame'])==original==inputs.canonical(replay['frames'][index])
        assert value['frame_sha256']==sha256(original).hexdigest() and value['calculated_at']==manifest['calculated_at']
    assert before=={f.name:sha256(f.read_bytes()).hexdigest() for f in authority.farm_binding.parent_authority.directory.iterdir()}
    assert calls==[1] and state['current'][-2:]==[False,False]


@pytest.mark.parametrize('change',['hmac','issuer','key','tenant','scope','gates','code','root','binding','parent-job','parent-result','parent-root','parent-time','time','extra'])
def test_even_resigned_wrong_lineage_or_claims_hold(prepared,change):
    model,_,authority,_,_,_=prepared;result=publish(prepared);doc=json.loads((authority.directory/result).read_bytes());p=doc['payload']
    if change=='hmac':doc['hmac_sha256']='0'*64
    elif change=='issuer':p['issuer_id']='other'
    elif change=='key':p['key_id']='other'
    elif change=='tenant':p['tenant_id']='foreign'
    elif change=='scope':p['scope']='validated_crop'
    elif change=='gates':p['gates']='G1'
    elif change=='code':p['code_sha256'][next(iter(p['code_sha256']))]='0'*64
    elif change=='root':p['numerical_root_sha256']='0'*64
    elif change=='binding':p['binding_sha256']='0'*64
    elif change=='parent-job':p['parent_job_id']='00000000-0000-0000-0000-000000000000'
    elif change=='parent-result':p['parent_result_sha256']='0'*64
    elif change=='parent-root':p['parent_numerical_root_sha256']='0'*64
    elif change=='parent-time':p['parent_calculated_at']='2026-10-21T00:00:00.000000Z'
    elif change=='time':p['calculated_at']='2099-01-01T00:00:00.000000Z'
    else:p['predicted_yield']=1
    if change!='hmac':doc['hmac_sha256']=hmac.new(KEY,model.DOMAIN+inputs.canonical(p),'sha256').hexdigest()
    raw=inputs.canonical(doc);digest=sha256(raw).hexdigest();path=authority.directory/digest;path.write_bytes(raw);path.chmod(0o400)
    with pytest.raises((model.LeafPopulationSignedArtifactHold,PermissionError)):authority.read_manifest('tenant-1',digest)


@pytest.mark.parametrize('change',['program','source','evidence','binding','numerical-root','result','symlink'])
def test_original_file_metadata_hash_and_path_integrity(prepared,change):
    model,_,authority,_,_,_=prepared;result=publish(prepared);p=json.loads((authority.directory/result).read_bytes())['payload']
    field={'program':'program_sha256','source':'source_sha256','evidence':'input_evidence_sha256',
        'binding':'binding_sha256','numerical-root':'numerical_root_sha256'}.get(change)
    path=authority.directory/(p[field] if field else result)
    if change=='symlink':
        outside=authority.directory.parent/'outside';outside.write_bytes(path.read_bytes());path.unlink();path.symlink_to(outside)
    else:path.chmod(0o600);path.write_bytes(path.read_bytes()+b' ');path.chmod(0o400)
    with pytest.raises(model.LeafPopulationSignedArtifactHold):authority.read_replay('tenant-1',result)


@pytest.mark.parametrize('prepared',['initial','birth'],indirect=True)
def test_structurally_reviewed_wrong_initial_areas_never_publish(prepared):
    model,_,authority,_,_,_=prepared
    with pytest.raises(model.LeafPopulationSignedArtifactHold):publish(prepared)
    if authority.directory.exists():assert all(json.loads(f.read_bytes()).get('schema_version')!=model.VERSION for f in authority.directory.iterdir())


def test_current_and_last_frame_revocation_hold_entire_replay(prepared,monkeypatch):
    model,_,authority,_,_,state=prepared;result=publish(prepared);state['allowed']=False
    with pytest.raises(model.LeafPopulationSignedArtifactHold):authority.read_manifest('tenant-1',result)
    state['allowed']=True;actual=model.reader.read_leaf_population_frame;seen=[]
    def revoke(*a,**kw):
        value=actual(*a,**kw);seen.append(kw['index'])
        if kw['index']==11:state['allowed']=False
        return value
    monkeypatch.setattr(model.reader,'read_leaf_population_frame',revoke)
    with pytest.raises(model.LeafPopulationSignedArtifactHold):authority.read_replay('tenant-1',result)
    assert seen==list(range(12))


def test_late_producer_revocation_returns_no_result_identifier(prepared,monkeypatch):
    model,producer,_,_,_,state=prepared;actual=producer.numerical.produce_leaf_population_artifact
    def revoke(*a,**kw):value=actual(*a,**kw);state['allowed']=False;return value
    monkeypatch.setattr(producer.numerical,'produce_leaf_population_artifact',revoke)
    with pytest.raises(model.LeafPopulationSignedArtifactHold):publish(prepared)


@pytest.mark.parametrize('index',[True,-1,12,1.5])
def test_invalid_frame_indices_hold(prepared,index):
    model,_,authority,_,_,_=prepared;result=publish(prepared)
    with pytest.raises(model.LeafPopulationSignedArtifactHold):authority.read_frame('tenant-1',result,index=index)
    with pytest.raises(PermissionError):authority.read_manifest('foreign',result)


@pytest.mark.parametrize('change',['same-parent-directory','relative-directory','weak-key','different-access'])
def test_constructor_requires_separate_owned_storage_and_explicit_key(prepared,change):
    model,_,authority,_,_,_=prepared
    arguments=dict(directory=authority.directory,access=authority.access,integrity_key=KEY,
        issuer_id=authority.issuer_id,key_id=authority.key_id)
    if change=='same-parent-directory':arguments['directory']=authority.farm_binding.parent_authority.directory
    elif change=='relative-directory':arguments['directory']=Path('relative')
    elif change=='weak-key':arguments['integrity_key']=b'weak'
    else:arguments['access']=ContentAccess(os.getuid()+1,os.getgid())
    with pytest.raises(model.LeafPopulationSignedArtifactHold):model.LeafPopulationArtifactAuthority(authority.farm_binding,**arguments)


def test_revocation_after_private_signed_write_never_returns_a_published_result(prepared,monkeypatch):
    model,_,authority,_,_,state=prepared;actual=model.MorphologyBlobStore.put
    def revoke(self,raw,**kw):
        value=actual(self,raw,**kw)
        if json.loads(raw).get('payload',{}).get('schema_version')==model.VERSION:state['allowed']=False
        return value
    monkeypatch.setattr(model.MorphologyBlobStore,'put',revoke)
    with pytest.raises(model.LeafPopulationSignedArtifactHold):publish(prepared)
    candidates=[f.name for f in authority.directory.iterdir() if json.loads(f.read_bytes()).get('payload',{}).get('schema_version')==model.VERSION]
    assert len(candidates)==1
    with pytest.raises(model.LeafPopulationSignedArtifactHold):authority.read_manifest('tenant-1',candidates[0])
