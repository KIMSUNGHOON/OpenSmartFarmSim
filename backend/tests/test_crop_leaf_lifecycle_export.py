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

from app import crop_leaf_lifecycle_artifact_producer as producer
from app import crop_leaf_lifecycle_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from test_crop_leaf_lifecycle_artifact import artifacts
from test_crop_leaf_lifecycle_preparation import management, removal
from test_crop_leaf_appearance_program import program
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, fraction, snapshot, produce as produce_stem, STEM_PROGRAM

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT/'research/export-leaf-lifecycle-replay.py'
FILES = {'root.json': 'artifact_sha256', 'input.json': 'appearance_program_sha256',
    'management.json': 'management_program_sha256', 'preparation.json': 'preparation_sha256',
    'initial-state.json': 'initial_state_sha256', 'stem-root.json': 'stem_artifact_sha256', 'stem-input.json': 'stem_program_sha256'}


def exporter():
    spec = importlib.util.spec_from_file_location('export_lifecycle', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def test_both_scenarios_original20files_same_frames_source_rights_and_repeat(artifacts, source, tmp_path):
    artifact, _, raw, _ = artifacts; prepared = json.loads((artifact[0]/reader.read_leaf_lifecycle_manifest(*artifact)['preparation_sha256']).read_bytes())
    events = prepared['lifecycle_initialization']['births']; initial = prepared['lifecycle_initialization']['population_state']
    m = management(raw, [removal(initial['initial_inventory_state']['leaves'][0]['state']['clock_state']['leaf_id'], 0),
        removal(events[0]['leaf_id'], fraction(events[0]['emerged_elapsed_seconds_exact']), 'newborn')])
    directory = tmp_path/'removed-blobs'; removed_root = producer.produce_leaf_lifecycle_artifact(directory, source[1],
        stem_directory=source[0], appearance_program_raw=raw, management_raw=canonical(m))
    for name, current in [('none', artifact), ('removed', (directory, source[1], removed_root))]:
        before = snapshot(current[0]); out = tmp_path/name; result = exporter().export(current[0], current[2], out)
        index_raw = (out/'index.json').read_bytes(); index = json.loads(index_raw); root = reader.read_leaf_lifecycle_manifest(*current)
        assert result == {'artifact_sha256': current[2], 'index_sha256': sha256(index_raw).hexdigest(), 'frames': 12, 'public_files': 20}
        assert index['schema_version'] == 'leaf-lifecycle-public-fixture-v1' and index['gates'] == 'not_assessed'
        assert index['source_rights'] == root['source_rights'] and set(index['source_rights']) == {'appearance','management','stem'}
        assert set(p.name for p in out.iterdir()) == set(FILES)|{f'frame-{i}.json' for i in range(12)}|{'index.json'}
        assert len(index['sources']) == 7
        for d in index['sources']:
            raw_file = (out/d['path']).read_bytes(); field = FILES[d['path']]
            assert d['sha256'] == index[field] == sha256(raw_file).hexdigest() and d['bytes'] == len(raw_file)
            assert raw_file == (current[0]/index[field]).read_bytes() and raw_file == canonical(json.loads(raw_file))
        states = 0
        for i,d in enumerate(index['frames']):
            raw_frame = (out/d['path']).read_bytes(); frame = reader.read_leaf_lifecycle_frame(*current,index=i)
            assert raw_frame == canonical(frame) and len(raw_frame) == d['bytes'] and sha256(raw_frame).hexdigest() == d['sha256']
            for k in ['index','at','result_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256']: assert d[k] == root['samples'][i][k]
            states += len(frame['active_leaves']) + len(frame['removed_leaves'])
        assert states == 47
        saved = snapshot(out)
        with pytest.raises(FileExistsError): exporter().export(current[0], current[2], out)
        repeat = tmp_path/(name+'-repeat'); assert exporter().export(current[0],current[2],repeat) == result
        assert {f.name:f.read_bytes() for f in out.iterdir()} == {f.name:f.read_bytes() for f in repeat.iterdir()}
        assert snapshot(out) == saved and snapshot(current[0]) == before


@pytest.mark.parametrize('owner',['appearance','management','stem'])
def test_each_actual_redistribution_grant_required_before_creation(source, tmp_path, owner):
    p = program()
    if owner == 'stem':
        parent = deepcopy(STEM_PROGRAM); parent['rights']['redistribute'] = False; source = produce_stem(tmp_path/'restricted-stem', parent)
        m = json.loads((source[0]/source[2]).read_bytes()); p['stem'] = {'artifact_sha256':source[2],'program_sha256':m['program_sha256']}
    if owner == 'appearance': p['rights']['redistribute'] = False
    raw = canonical(p); m = management(raw)
    if owner == 'management': m['rights']['redistribute'] = False
    directory = tmp_path/'restricted'; root = producer.produce_leaf_lifecycle_artifact(directory,source[1],stem_directory=source[0],appearance_program_raw=raw,management_raw=canonical(m))
    out = tmp_path/'no-grant'
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'): exporter().export(directory,root,out)
    assert not out.exists()


@pytest.mark.parametrize('owner',['appearance','management','stem'])
@pytest.mark.parametrize('grant',['use','display','redistribute'])
def test_late_redistribution_denial_no_completed_index(artifacts, tmp_path, monkeypatch, owner, grant):
    artifact = artifacts[0]; module = exporter(); original = module.read_leaf_lifecycle_manifest; calls=[]
    def denied(*args,**kwargs):
        value=deepcopy(original(*args,**kwargs));calls.append(1)
        if len(calls)>1:value['source_rights'][owner][grant]=False
        return value
    monkeypatch.setattr(module,'read_leaf_lifecycle_manifest',denied);out=tmp_path/'late-denial'
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):module.export(artifact[0],artifact[2],out)
    assert len(calls)==2 and not(out/'index.json').exists()


@pytest.mark.parametrize('field',['appearance_program','management_program','preparation','initial_state','unselected-result','directory-mode'])
def test_late_original_change_no_completed_index(artifacts,tmp_path,monkeypatch,field):
    artifact=artifacts[0];directory=tmp_path/'changed-source';shutil.copytree(artifact[0],directory)
    manifest=reader.read_leaf_lifecycle_manifest(*artifact);module=exporter();original=module.read_leaf_lifecycle_frame;changed=[]
    def mutate(*args,**kwargs):
        value=original(*args,**kwargs)
        if kwargs['index']==11 and not changed:
            changed.append(1)
            if field=='directory-mode':directory.chmod(0o777)
            else:
                digest=manifest['samples'][4]['result_sha256'] if field=='unselected-result' else manifest[field+'_sha256']
                (directory/digest).write_bytes(b'{}')
        return value
    monkeypatch.setattr(module,'read_leaf_lifecycle_frame',mutate);out=tmp_path/'late-change'
    with pytest.raises(MorphologyArtifactHold):module.export(directory,artifact[2],out)
    assert changed==[1] and not(out/'index.json').exists()


@pytest.mark.parametrize('target',['frame-5.json','management.json','initial-state.json'])
def test_changed_written_bytes_no_completed_index(artifacts,tmp_path,monkeypatch,target):
    artifact=artifacts[0];module=exporter();out=tmp_path/'corrupt-output';original=Path.write_bytes
    def corrupt(path,raw):
        result=original(path,raw)
        if path==out/target:original(path,b'{}')
        return result
    monkeypatch.setattr(Path,'write_bytes',corrupt)
    with pytest.raises(MorphologyArtifactHold,match='HASH_HOLD'):module.export(artifact[0],artifact[2],out)
    assert not(out/'index.json').exists()


def test_fresh_export_growth_import_DB_CLI_network_and_unowned_writes_zero(artifacts,tmp_path):
    artifact=artifacts[0];before=snapshot(artifact[0]);out=tmp_path/'fresh'
    script=r'''
import importlib.abc,importlib.util,json,os,pathlib,subprocess,sys
sys.path.insert(0,sys.argv[1]);out=pathlib.Path(sys.argv[5]).resolve();attempts=[]
allowed={'crop_leaf_appearance_artifact_reader','crop_leaf_appearance_program','crop_leaf_artifact_reader',
'crop_leaf_lifecycle_artifact_reader','crop_leaf_lifecycle_program','crop_leaf_population_artifact_reader',
'crop_morphology_artifact_io','crop_morphology_artifact_reader','crop_rational_morphology_artifact_reader'}
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('app.crop_')and fullname.rsplit('.',1)[-1]not in allowed:raise AssertionError('growth import '+fullname)
sys.meta_path.insert(0,Block())
import psycopg
def forbidden(*a,**k):attempts.append(1);raise AssertionError('DB/CLI/network/unowned write forbidden')
psycopg.connect=forbidden;subprocess.run=forbidden;subprocess.Popen=forbidden
def owned(path):
 return type(path)in(str,bytes)and(out==pathlib.Path(os.fsdecode(path)).resolve()or out in pathlib.Path(os.fsdecode(path)).resolve().parents)
def audit(event,args):
 if event=='open'and((type(args[1])is str and any(x in args[1]for x in 'wax+'))or(type(args[2])is int and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND)))and not owned(args[0]):forbidden()
 if event in {'os.mkdir','os.remove','os.rmdir'}and not owned(args[0]):forbidden()
 if event=='os.rename'and not(owned(args[0])and owned(args[1])):forbidden()
 if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','socket.connect'}:forbidden()
sys.addaudithook(audit)
spec=importlib.util.spec_from_file_location('export_lifecycle',sys.argv[2]);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
before=len(os.listdir('/proc/self/fd'));result=m.export(pathlib.Path(sys.argv[3]),sys.argv[4],out)
assert result['frames']==12 and result['public_files']==20 and not attempts
assert before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'passed':True,'frames':12,'files':20,'growth_imports':0,'DB_CLI_network_unowned_writes':0,'FD_preserved':True,'result':result}))
'''
    result=subprocess.run([sys.executable,'-B','-c',script,str(ROOT/'backend'),str(SCRIPT),str(artifact[0]),artifact[2],str(out)],
        capture_output=True,text=True,timeout=45,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert result.returncode==0,result.stderr
    proof=json.loads(result.stdout);assert proof['passed'] and proof['growth_imports']==proof['DB_CLI_network_unowned_writes']==0
    assert snapshot(artifact[0])==before


@pytest.mark.parametrize('failure',['content-write','index-rename'])
def test_partial_write_or_index_rename_no_completed_index(artifacts,tmp_path,monkeypatch,failure):
    artifact=artifacts[0];module=exporter();out=tmp_path/'partial';before=snapshot(artifact[0])
    if failure=='content-write':
        original=Path.write_bytes
        def fail(path,raw):
            if path==out/'management.json':raise OSError('owned injected write failure')
            return original(path,raw)
        monkeypatch.setattr(Path,'write_bytes',fail)
    else:
        original=os.replace
        def fail(src,dst,*args,**kwargs):
            if Path(dst)==out/'index.json':raise OSError('owned injected rename failure')
            return original(src,dst,*args,**kwargs)
        monkeypatch.setattr(os,'replace',fail)
    with pytest.raises(OSError):module.export(artifact[0],artifact[2],out)
    assert not(out/'index.json').exists() and snapshot(artifact[0])==before


@pytest.mark.parametrize('target',['same','child'])
def test_output_outside_immutable_source_required(artifacts,target):
    artifact=artifacts[0];out=artifact[0] if target=='same' else artifact[0]/'forbidden';before=snapshot(artifact[0])
    with pytest.raises(MorphologyArtifactHold,match='STORAGE_HOLD'):exporter().export(artifact[0],artifact[2],out)
    assert snapshot(artifact[0])==before


@pytest.mark.parametrize('change',['mode','replace','extra-file'])
def test_changed_output_directory_no_completed_index(artifacts,tmp_path,monkeypatch,change):
    artifact=artifacts[0];module=exporter();out=tmp_path/'output';original=module.read_leaf_lifecycle_manifest;calls=[]
    def mutate(*args,**kwargs):
        value=original(*args,**kwargs);calls.append(1)
        if len(calls)==2:
            if change=='mode':out.chmod(0o777)
            elif change=='replace':
                saved=tmp_path/'saved';out.rename(saved);shutil.copytree(saved,out)
            else:(out/'extra.json').write_bytes(b'{}')
        return value
    monkeypatch.setattr(module,'read_leaf_lifecycle_manifest',mutate)
    with pytest.raises(MorphologyArtifactHold,match='STORAGE_HOLD'):module.export(artifact[0],artifact[2],out)
    assert not(out/'index.json').exists()
