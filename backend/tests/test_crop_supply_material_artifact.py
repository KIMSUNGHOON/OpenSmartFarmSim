"""Own public source recalculation, immutable material window and cold reads."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_supply_material_artifact_producer as producer
from app import crop_supply_material_artifact_reader as reader
from app import crop_supply_material_owner as owner
from app import crop_supply_material_point as point
from app import crop_supply_forcing_threshold_state as candidate
from app import crop_supply_forcing_owner as forcing
from app import crop_supply_season as base
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source,setup,q,x,canonical,SOURCE
from test_crop_supply_forcing_owner import setup_owner
from test_crop_supply_material_point import make_inputs
from test_crop_supply_forcing_threshold import TOLERANCE


def public_calculation(source,path,*,redistribute=True):
    base_dir=path/'base';base_dir.mkdir()
    ws,old_definition,d,_,_=setup(source,base_dir)
    d['rights']['redistribute']=True
    with MorphologyBlobStore(ws.archive_directory,ws.access,write=True)as store:
        definition=store.put(canonical(d),maximum=base.PAGE_MAX)
    start=base.open_season(base.SourceRef(SOURCE,36),definition,ws)
    at512=base.advance(start,base.AdvanceRequest(q(512)))
    assert at512.status=='yielded',at512.hold
    origin={'workspace':ws,'source_ref':forcing.SourceRef(definition,at512.handle.cursor_sha256),'basis':at512.handle.basis}
    force_dir=path/'forcing';force_dir.mkdir()
    fws,fd,document=setup_owner(origin,force_dir,end=536)
    first=forcing.open_season(origin['source_ref'],fd,fws)
    pending=forcing.advance(first,base.AdvanceRequest(q(536),step_budget=10))
    assert pending.status=='awaiting_material',pending.hold
    state=candidate.calculate_threshold_state(pending.handle,pending.pending['page_sha256'],TOLERANCE)
    inputs=make_inputs({'workspace':fws,'definition':fd,'document':document,'result':pending},state)
    inputs['rights']['redistribute']=redistribute
    result=point.apply_material_point(pending.handle,pending.pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='point_ready',result.get('hold')
    material_ws=owner.Workspace(fws,path/'material-cas',fws.access)
    adopted=owner.adopt_material(pending.handle,pending.pending['page_sha256'],TOLERANCE,inputs=inputs,
        expected_point_sha256=result['calculation_sha256'],workspace=material_ws)
    assert adopted.status=='adopted',adopted.hold
    last=owner.advance(adopted.handle,base.AdvanceRequest(q(536),step_budget=10))
    assert last.status=='completed',last.hold
    return {'handle':last.handle,'adopted':adopted.handle,'point':result,'workspace':material_ws,'unused_private_definition':old_definition}


@pytest.fixture(scope='module')
def public_material(source,tmp_path_factory):
    return public_calculation(source,tmp_path_factory.mktemp('public-material'))


@pytest.fixture(scope='module')
def artifact(public_material,tmp_path_factory):
    directory=tmp_path_factory.mktemp('material-artifact')/'cas';access=public_material['workspace'].access
    root=producer.produce_material_artifact(directory,access,handle=public_material['handle'])
    return directory,access,root


def test_public_result_is_new_and_excludes_unused_private_archive_blobs(public_material,artifact):
    directory,access,root=artifact
    manifest=reader.read_material_manifest(directory,access,root)
    assert manifest['effective_rights']=={'use':True,'display':True,'redistribute':True}
    assert manifest['source']['original_root']['sha256']==SOURCE
    assert manifest['window']['covers_whole_season']is False
    assert len(manifest['frames'])==4
    assert [v['phase']for v in manifest['frames']]==['material_before','material_after','original_grid_endpoint','declared_end']
    assert not(directory/public_material['unused_private_definition']).exists()
    assert manifest['G0_G4']=='not_assessed'and manifest['R2']=='not_approved'


def test_exact_before_after_and_remainder_are_projected_without_RHS(public_material,artifact,monkeypatch):
    directory,access,root=artifact
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('artifact read evaluated RHS'))
    monkeypatch.setattr(owner,'open_material',lambda *a,**k:pytest.fail('artifact read imported model authority'))
    frames=[reader.read_material_frame(directory,access,root,index=i)for i in range(4)]
    before,after,grid,last=frames;p=public_material['point']
    assert before['snapshot']=={'at':p['at'],'state':p['before_dense']['state'],'derived':p['before_dense']['derived']}
    assert after['snapshot']=={'at':p['at'],'state':p['after_state'],'derived':p['after_derived']}
    assert before['at']==after['at']==p['at']
    assert len(before['leaves'])==11 and len(after['leaves'])==12
    assert after['leaves'][-1]['id']==p['source_event']['leaf_id']
    assert after['leaves'][-1]['parent_internode_id']==p['source_event']['internode_id']
    assert grid['at']['elapsed_seconds_exact']==q(528)and last['at']['elapsed_seconds_exact']==q(536)
    assert last['snapshot']==public_material['handle'].current['numeric']['last_confirmed']
    assert before['state_kind']=='dense_before_from_adopted_point'
    assert after['state_kind']=='confirmed_material_current'


def test_same_handle_produces_same_root_and_originals_stay_unchanged(public_material,artifact,tmp_path,monkeypatch):
    directory,access,root=artifact
    old={p.name:(p.stat().st_mtime_ns,sha256(p.read_bytes()).hexdigest())for p in directory.iterdir()}
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('producer replay evaluated RHS'))
    again=producer.produce_material_artifact(tmp_path/'other-cas',access,handle=public_material['handle'])
    assert again==root
    assert {p.name:(p.stat().st_mtime_ns,sha256(p.read_bytes()).hexdigest())for p in directory.iterdir()}==old


def exporter():
    from importlib.util import spec_from_file_location,module_from_spec
    path=__import__('pathlib').Path(__file__).resolve().parents[2]/'research/export-material-replay.py'
    spec=spec_from_file_location('material_export_test',path);module=module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_public_export_binds_original_raw_blobs_frames_and_notice(artifact,tmp_path,monkeypatch):
    directory,access,root=artifact;module=exporter()
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('export RHS'))
    output=tmp_path/'export';result=module.export(directory,root,output)
    index=json.loads((output/'index.json').read_bytes())
    assert result['artifact_sha256']==root and result['index_sha256']==sha256((output/'index.json').read_bytes()).hexdigest()
    assert index['effective_rights']=={'use':True,'display':True,'redistribute':True}
    assert index['sample_scalars']==722 and len(index['frames'])==4
    assert {d['path']for d in index['blobs']+index['frames']}|{'index.json'}=={p.name for p in output.iterdir()}
    for d in index['blobs']+index['frames']:
        b=(output/d['path']).read_bytes();assert len(b)==d['bytes']and sha256(b).hexdigest()==d['sha256']
    assert (output/index['notice']['path']).read_bytes()==(directory/index['notice']['sha256']).read_bytes()
    for i,d in enumerate(index['frames']):
        frame=json.loads((output/d['path']).read_bytes())['frame']
        assert sha256(canonical(frame)).hexdigest()==d['frame_sha256']
        actual=reader.read_material_frame(directory,access,root,index=i)
        assert frame=={k:v for k,v in actual.items()if k!='artifact_sha256'}


@pytest.mark.parametrize('permission',['use','display','redistribute'])
def test_each_export_permission_is_required_before_output(permission,tmp_path):
    module=exporter();manifest={'effective_rights':{'use':True,'display':True,'redistribute':True}}
    manifest['effective_rights'][permission]=False
    with pytest.raises(ValueError,match='RIGHTS_HOLD'):module._grants(manifest)


@pytest.mark.parametrize('kind',['same','descendant','ancestor','relative','symlink'])
def test_unsafe_export_paths_reject_before_loading(artifact,tmp_path,monkeypatch,kind):
    directory,access,root=artifact;module=exporter()
    if kind=='same':output=directory
    elif kind=='descendant':output=directory/'export'
    elif kind=='ancestor':output=directory.parent
    elif kind=='relative':output=__import__('pathlib').Path('relative-material-output')
    else:
        output=tmp_path/'link';output.symlink_to(directory,target_is_directory=True)
    monkeypatch.setattr(module.reader,'_load',lambda *a,**k:pytest.fail('unsafe output read source'))
    with pytest.raises(ValueError,match='STORAGE_HOLD'):module.export(directory,root,output)


def test_aggregate_limit_never_publishes_a_completed_index(artifact,tmp_path,monkeypatch):
    directory,_,root=artifact;module=exporter();output=tmp_path/'limited'
    monkeypatch.setattr(module,'MAX_PUBLIC_BYTES',2*1024**2)
    with pytest.raises(ValueError,match='CAPACITY_HOLD'):module.export(directory,root,output)
    assert not(output/'index.json').exists()
    assert sum(p.stat().st_size for p in output.iterdir())<=2*1024**2


def test_new_private_calculation_cannot_be_exported(source,tmp_path):
    path=tmp_path/'private-source';path.mkdir()
    private=public_calculation(source,path,redistribute=False)
    directory=tmp_path/'private-artifact';access=private['workspace'].access
    root=producer.produce_material_artifact(directory,access,handle=private['handle'])
    manifest=reader.read_material_manifest(directory,access,root)
    assert manifest['effective_rights']['redistribute']is False
    with pytest.raises(ValueError,match='RIGHTS_HOLD'):exporter().export(directory,root,tmp_path/'forbidden')
    assert not(tmp_path/'forbidden').exists()


@pytest.mark.parametrize('index',[True,-1,4,512,'0'])
def test_wrong_frame_index_never_selects_another_frame(artifact,index):
    directory,access,root=artifact
    with pytest.raises(ValueError,match='INDEX_HOLD'):reader.read_material_frame(directory,access,root,index=index)


@pytest.mark.parametrize('change',['frame','scope','code','extra_blob','rights','before_time'])
def test_rehashed_manifest_changes_are_rejected(artifact,public_material,change):
    directory,access,root=artifact;manifest=json.loads((directory/root).read_bytes())
    if change=='frame':manifest['frames'][0]['state_scalars']+=1
    elif change=='scope':manifest['G0_G4']='approved'
    elif change=='code':manifest['code_sha256']['backend/app/crop_supply_material_artifact_reader.py']='0'*64
    elif change=='extra_blob':
        name=public_material['unused_private_definition'];b=(public_material['workspace'].forcing_workspace.source_workspace.archive_directory/name).read_bytes()
        with MorphologyBlobStore(directory,access,write=True)as store:store.put(b,maximum=reader.MAX)
        manifest['blob_groups']['base'].append({'sha256':name,'bytes':len(b)})
    elif change=='rights':manifest['effective_rights']['redistribute']=False
    else:manifest['frames'][0]['at']['elapsed_seconds_exact']=q(0)
    with MorphologyBlobStore(directory,access,write=True)as store:reference=store.put(canonical(manifest),maximum=reader.MAX)
    with pytest.raises(ValueError):reader.read_material_manifest(directory,access,reference)


def rehashed_selected_current(artifact,change):
    directory,access,root=artifact
    with MorphologyBlobStore(directory,access)as source_store:manifest,frames,_=reader._load(source_store,root)
    manifest=deepcopy(manifest);last=deepcopy(frames[-1])
    old_cursor=manifest['source']['material']['cursor_sha256'];cursor=json.loads((directory/old_cursor).read_bytes())
    old_current=cursor['current_sha256'];current=json.loads((directory/old_current).read_bytes())
    old_page=cursor['history_page_sha256'];page=json.loads((directory/old_page).read_bytes())
    if change=='state':current['numeric']['last_confirmed']['state'][0]+=1.;last['snapshot']['state'][0]+=1.
    elif change=='phase':
        current['phase']='forcing_after';last['phase']='forcing_after';manifest['terminal']['status']='confirmed_prefix'
    else:
        row=current['numeric']['global_ledgers']['carbohydrate'];row['budget_exact']=q(x(row['budget_exact'])+1,row['budget_exact']['unit'])
        last['global_ledgers']['carbohydrate']['budget_exact']=deepcopy(row['budget_exact'])
    with MorphologyBlobStore(directory,access,write=True)as store:
        new_current=store.put(canonical(current),maximum=reader.MAX);cursor['current_sha256']=new_current
        page['after_current_sha256']=new_current;new_page=store.put(canonical(page),maximum=reader.MAX);cursor['history_page_sha256']=new_page
        new_cursor=store.put(canonical(cursor),maximum=reader.MAX)
        manifest['source']['material']['cursor_sha256']=new_cursor
        last['source_sha256']=new_current;last['source_cursor_sha256']=new_cursor;manifest['frames'][-1]=reader.frame_descriptor(last)
        replaced={old_cursor:new_cursor,old_current:new_current,old_page:new_page}
        for descriptor in manifest['blob_groups']['material']:
            if descriptor['sha256']in replaced:
                descriptor['sha256']=replaced[descriptor['sha256']];descriptor['bytes']=(directory/descriptor['sha256']).stat().st_size
        return store.put(canonical(manifest),maximum=reader.MAX)


@pytest.mark.parametrize('change',['state','phase','budget'])
def test_rehashed_state_phase_or_budget_cannot_override_saved_calculation(artifact,change):
    directory,access,_=artifact;reference=rehashed_selected_current(artifact,change)
    with pytest.raises(ValueError):reader.read_material_manifest(directory,access,reference)


def test_fresh_reader_and_export_block_growth_imports_DB_network_and_CAS_writes(artifact,tmp_path):
    import os,subprocess,sys
    from pathlib import Path
    directory,access,root=artifact;workspace=Path(__file__).resolve().parents[2]
    script=r'''
import importlib.abc,importlib.util,json,os,socket,sys
from pathlib import Path
from hashlib import sha256
R=Path(sys.argv[1]);directory=Path(sys.argv[2]);root=sys.argv[3];output=Path(sys.argv[4]);sys.path.insert(0,str(R/'backend'))
forbidden={'app.crop_supply_season','app.crop_supply_forcing_interval','app.crop_supply_forcing_owner','app.crop_supply_forcing_threshold','app.crop_supply_forcing_threshold_state','app.crop_supply_threshold_state_books','app.crop_supply_material_point','app.crop_supply_material_proof','app.crop_supply_material_owner','app.crop_supply_material_artifact_producer','app.crop_supply_morphology_birth_stage','app.crop_growth_rates','app.crop_leaf_area','app.crop_internode_length'}
class Guard(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname in forbidden:raise AssertionError('growth/model import: '+fullname)
sys.meta_path.insert(0,Guard())
import psycopg
from app.job_store import JobStore
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.content_access import ContentAccess
from app import crop_supply_material_artifact_reader as reader
calls={'DB':0,'network':0,'CAS_put':0}
def fail(name):
 def blocked(*a,**k):calls[name]+=1;raise AssertionError(name+' during cold read/export')
 return blocked
psycopg.connect=fail('DB');JobStore.connect=fail('DB');socket.socket=fail('network');socket.create_connection=fail('network');MorphologyBlobStore.put=fail('CAS_put')
access=ContentAccess(os.getuid(),os.getgid());m=reader.read_material_manifest(directory,access,root)
frames=[reader.read_material_frame(directory,access,root,index=i)for i in range(len(m['frames']))]
spec=importlib.util.spec_from_file_location('cold_material_export',R/'research/export-material-replay.py');exporter=importlib.util.module_from_spec(spec);spec.loader.exec_module(exporter)
exported=exporter.export(directory,root,output)
assert not forbidden.intersection(sys.modules)
print(json.dumps({'frames':[sha256(reader.raw(f)).hexdigest()for f in frames],'calls':calls,'exported':exported,'forbidden_imports':0}))
'''
    child=subprocess.run([sys.executable,'-B','-c',script,str(workspace),str(directory),root,str(tmp_path/'cold-export')],
        capture_output=True,text=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    assert child.returncode==0,child.stderr[-3000:]
    result=json.loads(child.stdout)
    expected=[sha256(canonical(reader.read_material_frame(directory,access,root,index=i))).hexdigest()for i in range(4)]
    assert result['frames']==expected and result['calls']=={'DB':0,'network':0,'CAS_put':0}and result['forbidden_imports']==0
    assert result['exported']['frames']==4


@pytest.mark.parametrize('change',['source','output'])
def test_late_source_or_output_change_never_publishes_index(artifact,tmp_path,monkeypatch,change):
    from shutil import copytree
    directory,access,root=artifact;copy=copytree(directory,tmp_path/'source-copy');original=(directory/root).read_bytes()
    module=exporter();verify=module.writer._Output.verify;changed={'now':False}
    def mutate(self,written):
        result=verify(self,written)
        if not changed['now']:
            target=copy/root if change=='source'else self.path/'frame-0.json'
            target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ');changed['now']=True
        return result
    monkeypatch.setattr(module.writer._Output,'verify',mutate)
    with pytest.raises((ValueError,OSError)):module.export(copy,root,tmp_path/'changed-export')
    assert not(tmp_path/'changed-export/index.json').exists()and(directory/root).read_bytes()==original


def test_every_stored_geometry_coordinate_and_clock_matches_actual_packets(public_material,artifact):
    directory,access,root=artifact
    for i in range(4):
        frame=reader.read_material_frame(directory,access,root,index=i);state=frame['snapshot']['state'];n=len(frame['leaves']);h=len(frame['internodes']);size=frame['state_layout']['original_prefix_length']
        for j,row in enumerate(frame['leaves']):
            assert row['geometry']['value']==state[106+n+j]and row['carbon']['value']==state[106+2*n+j]
            assert row['represented_age']['value']==state[106+j]
        ids=frame['state_layout']['original']['stem_root_compartment_ids']if 'stem_root_compartment_ids'in frame['state_layout']['original']else [v['compartment_id']for v in public_material['adopted'].basis['numeric_basis']['seed']['program']['stem_root_compartments']]
        for j,row in enumerate(frame['internodes']):
            assert row['geometry']['value']==state[size+h+j]and row['represented_age']['value']==state[size+j]
            # Carbon stocks are identified by source IDs, never by rendered mesh order.
            if row['id']in ids:assert row['carbon']['value']==state[106+3*n+ids.index(row['id'])]
        for row in frame['leaves']+frame['internodes']:
            b=row['birth'];duration=x(frame['at']['elapsed_seconds_exact'])-x(b['at_elapsed_seconds_exact'])
            air=x(frame['lifetime_transfers_exact']['indoor_air_temperature_time'])-x(b['air_temperature_integral_exact'])
            age=x(b['thermal_age_exact'])+(air-Fraction(b['base_temperature']['value'])*duration)/86400
            assert x(row['clock_exact'])==age


def test_producer_refuses_plain_DTO_without_creating_output(public_material,tmp_path):
    output=tmp_path/'fake-source'
    with pytest.raises(ValueError,match='CONTEXT_HOLD'):
        producer.produce_material_artifact(output,public_material['workspace'].access,handle=public_material['handle'].current)
    assert not output.exists()


@pytest.mark.parametrize('kind',['same','descendant','ancestor','relative','symlink'])
def test_producer_output_cannot_mutate_source_archives(public_material,tmp_path,monkeypatch,kind):
    from pathlib import Path
    source=public_material['workspace'].archive_directory
    old={p.name:sha256(p.read_bytes()).hexdigest()for p in source.iterdir()}
    if kind=='same':output=source
    elif kind=='descendant':output=source/'bad-output'
    elif kind=='ancestor':output=source.parent
    elif kind=='relative':output=Path('relative-material-artifact')
    else:
        output=tmp_path/'link';output.symlink_to(source,target_is_directory=True)
    monkeypatch.setattr(producer.model,'_session',lambda *a,**k:pytest.fail('unsafe producer path opened source'))
    with pytest.raises(ValueError,match='STORAGE_HOLD'):
        producer.produce_material_artifact(output,public_material['workspace'].access,handle=public_material['handle'])
    assert {p.name:sha256(p.read_bytes()).hexdigest()for p in source.iterdir()}==old


def test_missing_original_blob_is_held_without_model_recovery(artifact,tmp_path,monkeypatch):
    from shutil import copytree
    directory,access,root=artifact;copy=copytree(directory,tmp_path/'incomplete')
    manifest=json.loads((copy/root).read_bytes());(copy/manifest['notice']['sha256']).unlink()
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('missing source attempted RHS recovery'))
    with pytest.raises(ValueError):reader.read_material_frame(copy,access,root,index=0)
