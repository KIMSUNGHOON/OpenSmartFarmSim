"""Actual current farm/parent services and original signed leaf calculations under SCRAM."""
import ctypes
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

import psycopg
import pytest

from app import crop_leaf_appearance_signed_artifact as model
from app import crop_leaf_appearance_signed_producer as producer
from app.content_access import ContentAccess
from login_database import login_database,login_scope
from test_crop_morphology_signed_artifact_native import schema_hash,final_cleanup
import test_crop_leaf_appearance_farm_binding_native as leaf_factory
from leaf_appearance_farm_fresh import snapshot
import morphology_farm_factory as factory


KEY=b'owned-signed-leaf-native-test-key-32!'
PUBLIC=Path(__file__).resolve().parents[2]/'web/public/leaf-appearance-replay'
pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


READ_WRITES={}
READ_SQL=[]
READ_GROWTH={}


def readonly_query(authority,mode,*args,**kwargs):
    with pytest.MonkeyPatch.context() as patch:
        calls=leaf_factory.forbid_growth(patch)
        for name in ('submit','publish','record_decision','_insert_publication','_event','_durable_content','artifact.put'):
            READ_WRITES.setdefault(name,0)
            def blocked(*args,_name=name,**kwargs):
                READ_WRITES[_name]+=1;raise AssertionError('signed current query attempted write')
            if name=='artifact.put':patch.setattr(model.MorphologyBlobStore,'put',blocked)
            else:patch.setattr(type(authority.farm_binding.jobs),name,blocked)
        original=psycopg.Cursor.execute
        def execute(self,statement,*args,**kwargs):
            text=statement if type(statement) is str else statement.as_string(self.connection)
            if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO)\b',text,re.I):
                READ_SQL.append(text.split()[0]);raise AssertionError('signed current query attempted persistent SQL write')
            return original(self,statement,*args,**kwargs)
        patch.setattr(psycopg.Cursor,'execute',execute)
        try:return getattr(authority,'read_'+mode)(*args,**kwargs)
        finally:
            for name,count in calls.items():READ_GROWTH[name]=READ_GROWTH.get(name,0)+count


@pytest.fixture
def setup(login_scope,tmp_path,monkeypatch):
    values=leaf_factory.registered_leaf_services(login_scope,tmp_path,monkeypatch)
    authority=model.LeafAppearanceArtifactAuthority(values[0],directory=tmp_path/'leaf-signed',
        access=ContentAccess(os.getuid(),os.getgid()),integrity_key=KEY,issuer_id='owned-native-research',key_id='owned-signed-leaf-key-v1')
    READ_WRITES.clear();READ_SQL.clear();READ_GROWTH.clear()
    yield authority,values
    assert not any(READ_WRITES.values()) and not READ_SQL and not any(READ_GROWTH.values())


def publish(value):
    authority,values=value
    return producer.produce_registered_leaf_appearance(authority,'tenant-1',model.reader._canonical(values[1]),**values[2])


def test_actual_one_calculation_all_original_frames_current_reads_and_fresh(setup,login_scope,tmp_path,monkeypatch):
    authority,values=setup;service,body,packet,parent_body,parent_packet,review,parent_review,principal,*_=values
    before=schema_hash(login_scope[0]);parent_before=snapshot(service.parent_authority.directory)
    real=producer.numerical.produce_leaf_appearance_artifact;calculated=[]
    def calculate(*args,**kwargs):calculated.append(1);return real(*args,**kwargs)
    monkeypatch.setattr(producer.numerical,'produce_leaf_appearance_artifact',calculate)
    result=publish(setup);assert calculated==[1] and before==schema_hash(login_scope[0])
    calls=leaf_factory.forbid_growth(monkeypatch);calls['leaf_appearance_top_producer']=0
    def blocked_calculation(*args,**kwargs):calls['leaf_appearance_top_producer']+=1;raise AssertionError('query calculated')
    monkeypatch.setattr(producer.numerical,'produce_leaf_appearance_artifact',blocked_calculation)
    originals=snapshot(authority.directory);writes={k:0 for k in ('submit','publish','record_decision','_insert_publication','_event','_durable_content','artifact.put')}
    sql_writes=[];timings={}
    with monkeypatch.context() as patch:
        for name in writes:
            def fail(*args,_name=name,**kwargs):writes[_name]+=1;raise AssertionError('signed query wrote data')
            if name=='artifact.put':patch.setattr(model.MorphologyBlobStore,'put',fail)
            else:patch.setattr(type(service.jobs),name,fail)
        execute=psycopg.Cursor.execute
        def readonly(self,statement,*args,**kwargs):
            text=statement if type(statement) is str else statement.as_string(self.connection)
            if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO)\b',text,re.I):
                sql_writes.append(text.split()[0]);raise AssertionError('signed query persistent SQL write')
            return execute(self,statement,*args,**kwargs)
        patch.setattr(psycopg.Cursor,'execute',readonly)
        started=perf_counter();manifest=readonly_query(authority,'manifest','tenant-1',result);timings['manifest']=perf_counter()-started
        started=perf_counter();replay=readonly_query(authority,'replay','tenant-1',result);timings['replay']=perf_counter()-started
        assert replay['manifest']==manifest['manifest']==json.loads((PUBLIC/'root.json').read_bytes())
        frame_hashes=[]
        for index,frame in enumerate(replay['frames']):
            raw=(PUBLIC/f'frame-{index}.json').read_bytes();assert model.reader._canonical(frame)==raw
            frame_hashes.append(sha256(raw).hexdigest())
        for index in (0,11):
            value=readonly_query(authority,'frame','tenant-1',result,index=index)
            assert value['frame']==replay['frames'][index] and value['frame_sha256']==frame_hashes[index]
            assert value['calculated_at']==manifest['calculated_at']
    assert not any(writes.values()) and not sql_writes and not any(calls.values()) and calculated==[1]
    parent=service.parent_authority;payload=json.loads((parent.directory/body['parent']['result_sha256']).read_bytes())['payload']
    parent_binding=(parent.directory/payload['binding_sha256']).read_bytes()
    config=factory.fresh_config(parent.farm_binding,principal,parent_body,parent_packet,parent_review,parent_binding,tmp_path/'fresh')
    p=json.loads(Path(config).read_bytes());directory=tmp_path/'fresh'
    p['signed']={'directory':str(parent.directory),'key_file':factory.private_file(directory,'parent-key.private',parent.integrity_key),
        'issuer_id':parent.issuer_id,'key_id':parent.key_id}
    p['execution']={'job_id':body['parent']['job_id'],'resolver_version':service.parent_query.service.input_resolver.version}
    p['leaf']={'key_file':factory.private_file(directory,'leaf-input-key.private',service.input_authority.integrity_key),
        'issuer_id':service.input_authority.issuer_id,'key_id':service.input_authority.key_id,'review':review}
    p['leaf_signed']={'directory':str(authority.directory),'result_sha256':result,'root_sha256':manifest['numerical_root_sha256'],
        'calculated_at':manifest['calculated_at'],'parent_result_sha256':manifest['parent_result_sha256'],
        'key_file':factory.private_file(directory,'leaf-result-key.private',authority.integrity_key),
        'issuer_id':authority.issuer_id,'key_id':authority.key_id}
    path=factory.private_file(directory,'leaf-signed-configuration.private.json',model.reader._canonical(p))
    gc.collect();ctypes.CDLL(None).malloc_trim(0)
    done=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('leaf_appearance_signed_fresh.py')),path],
        stdin=subprocess.DEVNULL,capture_output=True,text=True,timeout=180,
        env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parents[1])})
    assert done.returncode==0,done.stderr
    fresh=json.loads(done.stdout);assert fresh['actual_SCRAM'] and fresh['original_frame_sha256']==frame_hashes
    assert parent_before==snapshot(parent.directory) and originals==snapshot(authority.directory) and before==schema_hash(login_scope[0])
    factory.save('leaf-signed-normal.json',{'result_sha256':result,'root_sha256':manifest['numerical_root_sha256'],
        'calculated_at':manifest['calculated_at'],'parent_job_id':manifest['parent_job_id'],
        'parent_result_sha256':manifest['parent_result_sha256'],'original_frame_sha256':frame_hashes,
        'one_numeric_producer_call':len(calculated),'growth_CLI_calls':calls,'job_write_calls':writes,
        'persistent_SQL_write_calls':sql_writes,'single_query_seconds':timings,'fresh':fresh,
        'database_before_after':[before,schema_hash(login_scope[0])],'original_parent_files':len(parent_before),
        'original_leaf_files':len(originals),'actual_farm_Runs':0,'G0_G4':'not_assessed'})


def test_actual_current_and_late_revocation_never_returns_result_or_partial_replay(setup,login_scope,monkeypatch):
    authority,values=setup;service,_,_,_,_,review,parent_review,principal,rights,parent_rights=values
    result=publish(setup);before=schema_hash(login_scope[0]);cases=[]
    with pytest.raises(PermissionError):readonly_query(authority,'manifest','foreign',result)
    for item in (review,parent_review):
        item['status']='revoked'
        with pytest.raises(model.LeafAppearanceSignedArtifactHold):readonly_query(authority,'manifest','tenant-1',result)
        item['status']='accepted_for_software_validation'
    for item in (rights,parent_rights):
        item.allowed=False
        with pytest.raises(model.LeafAppearanceSignedArtifactHold):readonly_query(authority,'replay','tenant-1',result)
        item.allowed=True
    principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError):readonly_query(authority,'manifest','tenant-1',result)
    principal['scopes'].add('crop_result_read')
    with monkeypatch.context() as patch:
        actual=model.reader.read_leaf_appearance_frame;seen=[]
        def late_frame(*args,**kwargs):
            value=actual(*args,**kwargs);seen.append(kwargs['index'])
            if kwargs['index']==11:review['status']='revoked'
            return value
        patch.setattr(model.reader,'read_leaf_appearance_frame',late_frame)
        with pytest.raises(model.LeafAppearanceSignedArtifactHold):readonly_query(authority,'replay','tenant-1',result)
        assert seen==list(range(12))
    review['status']='accepted_for_software_validation';cases.append('last-frame-review-revoked')
    with monkeypatch.context() as patch:
        actual=producer.numerical.produce_leaf_appearance_artifact
        def late_numeric(*args,**kwargs):
            value=actual(*args,**kwargs);review['status']='revoked';return value
        patch.setattr(producer.numerical,'produce_leaf_appearance_artifact',late_numeric)
        with pytest.raises(model.LeafAppearanceSignedArtifactHold):publish(setup)
    review['status']='accepted_for_software_validation';cases.append('after-numeric-no-result-ID')
    previous=set(authority.directory.iterdir())
    with monkeypatch.context() as patch:
        actual=model.MorphologyBlobStore.put
        def late_signed(self,raw,**kwargs):
            value=actual(self,raw,**kwargs)
            if json.loads(raw).get('payload',{}).get('schema_version')==model.VERSION:parent_rights.allowed=False
            return value
        patch.setattr(model.MorphologyBlobStore,'put',late_signed)
        with pytest.raises(model.LeafAppearanceSignedArtifactHold):publish(setup)
        with pytest.raises(model.LeafAppearanceSignedArtifactHold):readonly_query(authority,'manifest','tenant-1',result)
    parent_rights.allowed=True;cases.append('after-private-signed-write-no-result-ID')
    assert len(set(authority.directory.iterdir())-previous)==1
    assert readonly_query(authority,'manifest','tenant-1',result)['result_sha256']==result and before==schema_hash(login_scope[0])
    factory.save('leaf-signed-fences.json',{'cases':cases,'both_reviews_and_rights_revoked_rejected':True,
        'foreign_and_current_scope_rejected':True,'no_partial_replay_or_new_result_ID':True,
        'one_private_unpublished_signed_blob_retained':True,'original_result_restored':True,
        'database_before_after':[before,schema_hash(login_scope[0])],
        'all_query_write_calls':dict(READ_WRITES),'all_query_SQL_writes':list(READ_SQL),'all_query_growth_CLI_calls':dict(READ_GROWTH)})
