from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app import crop_leaf_appearance_artifact_producer as producer
from app.crop_leaf_appearance_artifact_reader import read_leaf_appearance_frame
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from test_crop_leaf_appearance_artifact_reader import artifact, documents
from test_crop_leaf_appearance_program import program
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, snapshot, produce as produce_stem, STEM_PROGRAM

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'research/export-leaf-appearance-replay.py'
MAX=2*1024**2
FILES={'root.json':'artifact_sha256','input.json':'source_program_sha256','preparation.json':'preparation_sha256',
    'generated-input.json':'generated_program_sha256','population-root.json':'population_artifact_sha256',
    'stem-root.json':'stem_artifact_sha256','stem-input.json':'stem_program_sha256'}


def exporter():
    spec=importlib.util.spec_from_file_location('export_appearance',SCRIPT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_original20_files_bytes_frames_rights_repeat_and_existing_files_preserved(artifact,tmp_path):
    out=tmp_path/'public';before=snapshot(artifact[0]);old=snapshot(ROOT/'web/public/leaf-population-replay')
    result=exporter().export(artifact[0],artifact[2],out);index=json.loads((out/'index.json').read_bytes())
    assert result['frames']==12 and result['public_files']==20 and index['schema_version']=='leaf-appearance-public-fixture-v1'
    assert result['artifact_sha256']==artifact[2] and result['index_sha256']==sha256((out/'index.json').read_bytes()).hexdigest()
    assert set(p.name for p in out.iterdir())==set(FILES)|{f'frame-{i}.json'for i in range(12)}|{'index.json'}
    for name,field in FILES.items():
        raw=(out/name).read_bytes();assert raw==canonical(json.loads(raw)) and len(raw)<=MAX
        assert sha256(raw).hexdigest()==index[field]
    assert index['rights']['redistribute'] is index['stem_rights']['redistribute'] is True
    assert index['gates']=='not_assessed' and index['display_policy']['leaf_count']=='computed_from_explicit_phytomer_policy_v1'
    count=0
    for i,d in enumerate(index['frames']):
        raw=(out/d['path']).read_bytes();frame=read_leaf_appearance_frame(*artifact,index=i)
        assert raw==canonical(frame) and d['bytes']==len(raw) and d['sha256']==sha256(raw).hexdigest()
        assert d['result_sha256']==frame['result_sha256'] and d['binding_sha256']==frame['binding_sha256']
        assert d['at']==frame['at'] and d['stem_result_sha256']==frame['stem']['result_sha256'];count+=len(frame['leaves'])
    assert count==47
    saved=snapshot(out)
    with pytest.raises(FileExistsError):exporter().export(artifact[0],artifact[2],out)
    other=tmp_path/'repeat';assert exporter().export(artifact[0],artifact[2],other)==result
    assert {p.name:p.read_bytes()for p in other.iterdir()}=={p.name:p.read_bytes()for p in out.iterdir()}
    assert snapshot(out)==saved and snapshot(artifact[0])==before and snapshot(ROOT/'web/public/leaf-population-replay')==old


@pytest.mark.parametrize('owner',['source','stem'])
def test_both_actual_redistribution_rights_required_before_creation(source,tmp_path,owner):
    p=program()
    if owner=='source':p['rights']['redistribute']=False
    else:
        parent=deepcopy(STEM_PROGRAM);parent['rights']['redistribute']=False
        source=produce_stem(tmp_path/'restricted-stem',parent)
        parent_manifest=json.loads((source[0]/source[2]).read_bytes())
        p['stem']={'artifact_sha256':source[2],'program_sha256':parent_manifest['program_sha256']}
    directory=tmp_path/'restricted-appearance'
    root=producer.produce_leaf_appearance_artifact(directory,source[1],stem_directory=source[0],program_raw=canonical(p))
    out=tmp_path/'not-published'
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):exporter().export(directory,root,out)
    assert not out.exists()


@pytest.mark.parametrize('owner',['source','stem'])
def test_late_redistribution_denial_has_no_index(artifact,tmp_path,monkeypatch,owner):
    module=exporter();name='read_leaf_appearance_manifest'if owner=='source'else'read_rational_morphology_manifest'
    original=getattr(module,name);calls=[]
    def denied(*args,**kwargs):
        result=deepcopy(original(*args,**kwargs));calls.append(1)
        if len(calls)>1:result['program_rights']['redistribute']=False
        return result
    monkeypatch.setattr(module,name,denied);out=tmp_path/'late-denied'
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):module.export(artifact[0],artifact[2],out)
    assert len(calls)==2 and not(out/'index.json').exists()


@pytest.mark.parametrize('target',['source','preparation','unselected-result'])
def test_late_original_change_has_no_index(artifact,tmp_path,monkeypatch,target):
    directory=tmp_path/'changed';shutil.copytree(artifact[0],directory);m,p,s=documents(artifact);module=exporter()
    inner=json.loads((directory/m['population_artifact_sha256']).read_bytes());original=module.read_leaf_appearance_frame;calls=[]
    def changed(*args,**kwargs):
        value=original(*args,**kwargs)
        if kwargs['index']==11 and not calls:
            calls.append(1);digest=m['source_program_sha256']if target=='source'else(
                m['preparation_sha256']if target=='preparation'else inner['samples'][8]['result_sha256'])
            (directory/digest).write_bytes(b'{}')
        return value
    monkeypatch.setattr(module,'read_leaf_appearance_frame',changed);out=tmp_path/'late-change'
    with pytest.raises(MorphologyArtifactHold):module.export(directory,artifact[2],out)
    assert calls==[1] and not(out/'index.json').exists()


def test_changed_written_frame_has_no_index(artifact,tmp_path,monkeypatch):
    module=exporter();out=tmp_path/'corrupt-output';original=Path.write_bytes;calls=[]
    def changed(path,raw):
        result=original(path,raw)
        if path==out/'frame-5.json':original(path,b'{}');calls.append(1)
        return result
    monkeypatch.setattr(Path,'write_bytes',changed)
    with pytest.raises(MorphologyArtifactHold,match='HASH_HOLD'):module.export(artifact[0],artifact[2],out)
    assert calls==[1] and not(out/'index.json').exists()


@pytest.mark.parametrize('failure',['content-write','index-rename'])
def test_partial_write_or_rename_failure_has_no_index(artifact,tmp_path,monkeypatch,failure):
    module=exporter();out=tmp_path/'failed';before=snapshot(artifact[0])
    if failure=='content-write':
        original=Path.write_bytes
        def failed(path,raw):
            if path==out/'generated-input.json':raise OSError('owned injected write failure')
            return original(path,raw)
        monkeypatch.setattr(Path,'write_bytes',failed)
    else:
        original=os.replace
        def failed(src,dst,*args,**kwargs):
            if Path(dst)==out/'index.json':raise OSError('owned injected rename failure')
            return original(src,dst,*args,**kwargs)
        monkeypatch.setattr(os,'replace',failed)
    with pytest.raises(OSError):module.export(artifact[0],artifact[2],out)
    assert not(out/'index.json').exists() and snapshot(artifact[0])==before


def test_output_cannot_be_inside_immutable_source(artifact):
    before=snapshot(artifact[0]);out=artifact[0]/'forbidden'
    with pytest.raises(MorphologyArtifactHold,match='STORAGE_HOLD'):exporter().export(artifact[0],artifact[2],out)
    assert not out.exists() and snapshot(artifact[0])==before


def test_fresh_export_imports_no_numerical_model_and_writes_only_owned_output(artifact,tmp_path):
    script=r'''
import importlib.abc,importlib.util,json,os,pathlib,subprocess,sys
sys.path.insert(0,sys.argv[1]);out=pathlib.Path(sys.argv[5]).resolve();attempts=[]
allowed={'crop_leaf_appearance_artifact_reader','crop_leaf_appearance_program','crop_leaf_population_artifact_reader',
'crop_leaf_artifact_reader','crop_morphology_artifact_io','crop_morphology_artifact_reader','crop_rational_morphology_artifact_reader'}
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('app.crop_')and fullname.rsplit('.',1)[-1]not in allowed:raise AssertionError('numerical import '+fullname)
sys.meta_path.insert(0,Block())
import psycopg
def forbidden(*a,**k):attempts.append(1);raise AssertionError('DB/CLI/unowned write forbidden')
psycopg.connect=forbidden;subprocess.run=forbidden;subprocess.Popen=forbidden
def owned(path):
 return type(path)in(str,bytes)and(out==pathlib.Path(os.fsdecode(path)).resolve()or out in pathlib.Path(os.fsdecode(path)).resolve().parents)
def audit(event,args):
 if event=='open'and((type(args[1])is str and any(x in args[1]for x in 'wax+'))or(type(args[2])is int and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))and not owned(args[0]):forbidden()
 if event in {'os.mkdir','os.remove','os.rmdir'}and not owned(args[0]):forbidden()
 if event=='os.rename'and not(owned(args[0])and owned(args[1])):forbidden()
 if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','socket.connect'}:forbidden()
sys.addaudithook(audit)
spec=importlib.util.spec_from_file_location('export_appearance',sys.argv[2]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
before=len(os.listdir('/proc/self/fd'));result=m.export(pathlib.Path(sys.argv[3]),sys.argv[4],out)
assert result['frames']==12 and result['public_files']==20 and not attempts
assert before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'passed':True,'frames':12,'files':20,'numerical_imports':0,'DB_CLI_unowned_writes':0,'FD_preserved':True,'allowed_crop_modules':sorted(allowed),'result':result}))
'''
    before=snapshot(artifact[0]);out=tmp_path/'fresh-export'
    result=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'backend'),str(SCRIPT),str(artifact[0]),artifact[2],str(out)],
        capture_output=True,text=True,timeout=45,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert result.returncode==0,result.stderr
    proof=json.loads(result.stdout);assert proof['passed']and proof['numerical_imports']==proof['DB_CLI_unowned_writes']==0
    assert snapshot(artifact[0])==before
