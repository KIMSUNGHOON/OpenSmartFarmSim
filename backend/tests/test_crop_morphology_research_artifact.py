from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app.content_access import ContentAccess
from app.crop_internode_length import initialize_internode_length
from app.crop_morphology_artifact_io import MorphologyBlobStore, MorphologyArtifactHold
from app.crop_morphology_artifact_producer import produce_morphology_artifact
from app.crop_morphology_artifact_reader import read_morphology_frame, read_morphology_manifest
from app.job_store import JobStore
from app.thermal_run_store import _canonical

FIXTURE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-shoot-inventory-reference-v1.json').read_bytes())['cases'][0]


def access():
    return ContentAccess(os.getuid(),os.getgid())


def program():
    c=deepcopy(FIXTURE)
    nodes=[{'sequence':n['sequence'],'birth_age_exact':n['birth_age_exact'],
            'length_state':initialize_internode_length(inputs=n['length_inputs'])['state']}
           for n in c['initial_internodes']]
    return {'schema_version':'morphology-software-program-v1','origin':'synthetic','program_id':'synthetic-morphology-test',
        'rights':{'declaration_id':'self-authored-fixture','revision':'r1','declared_at_utc':'2026-10-21T15:30:00Z',
            **{k:True for k in ('ownership_asserted','access','store','use','transform','display','redistribute')}},
        'initial_state':{'timeline_state':c['timeline_state'],'inventory_start_sequence':0,
            'internodes':nodes,'emergence_profile':c['emergence_profile']}, 'segments':c['segments'],
        'output_times':['2026-10-01T08:00:00Z','2026-10-01T16:00:00Z','2026-10-02T00:00:00Z']}


def produce(root,p=None):
    return produce_morphology_artifact(root,access(),program_raw=_canonical(program() if p is None else p))


def test_original_stored_states_values_chain_and_repeat_root(tmp_path,monkeypatch):
    monkeypatch.setattr(JobStore,'connect',lambda *a,**k: pytest.fail('DB call forbidden'))
    root=tmp_path/'artifact'
    artifact=produce(root)
    manifest=read_morphology_manifest(root,access(),artifact)
    assert sha256(_canonical(manifest)).hexdigest()==artifact
    assert manifest['parameter_scope']=='synthetic_software_fixture_only'
    assert manifest['gates']=='not_assessed' and len(manifest['samples'])==3
    previous=manifest['initial_state_sha256']
    for index,descriptor in enumerate(manifest['samples']):
        assert descriptor['input_state_sha256']==previous
        previous=descriptor['state_sha256']
        frame=read_morphology_frame(root,access(),artifact,index=index)
        assert frame['at']==program()['output_times'][index]
        assert len(frame['internodes'])==index+4
        assert frame['result_sha256']==descriptor['result_sha256']
        assert frame['input_sha256']==descriptor['input_sha256']
        assert frame['schema_version']=='morphology-replay-frame-v1'
        assert frame['gates']=='not_assessed' and frame['claim_scope']=='synthetic_crop_math_only'
        assert 'height' not in frame and 'yield' not in frame
    final=read_morphology_frame(root,access(),artifact,index=2)
    for actual,expected in zip(final['internodes'],FIXTURE['expected'],strict=True):
        assert actual['sequence']==expected['sequence'] and actual['age_exact']==expected['end_age_exact']
        assert actual['length']['value']==pytest.approx(float(expected['end_length_m']),rel=1e-12,abs=0)
    assert final['tracked_axis_length']['value']==pytest.approx(float(FIXTURE['expected_axis_length_m']),rel=1e-12,abs=0)
    assert previous==manifest['terminal_state_sha256']
    before={p.name:(p.stat().st_ino,p.stat().st_mtime_ns,p.read_bytes()) for p in root.iterdir()}
    assert produce(root)==artifact
    assert {p.name:(p.stat().st_ino,p.stat().st_mtime_ns,p.read_bytes()) for p in root.iterdir()}==before


def test_reader_never_calls_models_or_DB_and_fresh_process_imports_no_models(tmp_path,monkeypatch):
    root=tmp_path/'artifact';artifact=produce(root)
    expected=read_morphology_frame(root,access(),artifact,index=2)
    from app import crop_shoot_inventory,crop_new_internodes,crop_shoot_timeline,crop_phytomer_emergence
    from app import crop_internode_length,crop_internode_length_change,crop_morphology_thermal_clock,crop_internode_elongation
    for module in (crop_shoot_inventory,crop_new_internodes,crop_shoot_timeline,crop_phytomer_emergence,
                   crop_internode_length,crop_internode_length_change,crop_morphology_thermal_clock,crop_internode_elongation):
        for name,value in vars(module).copy().items():
            if callable(value) and name.startswith(('calculate_','advance_','initialize_','normalize_','integrate_')):
                monkeypatch.setattr(module,name,lambda *a,**k: pytest.fail('model called during read'))
    monkeypatch.setattr(JobStore,'connect',lambda *a,**k: pytest.fail('DB called during read'))
    assert read_morphology_frame(root,access(),artifact,index=2)==expected
    assert read_morphology_manifest(root,access(),artifact)['terminal_state_sha256']
    code="""import os,sys,json
from pathlib import Path
from app.content_access import ContentAccess
from app.crop_morphology_artifact_reader import read_morphology_frame
from app.job_store import JobStore
JobStore.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('DB forbidden'))
names=['crop_shoot_inventory','crop_new_internodes','crop_shoot_timeline','crop_phytomer_emergence','crop_internode_length','crop_internode_length_change','crop_morphology_thermal_clock','crop_internode_elongation']
assert all('app.'+name not in sys.modules for name in names)
value=read_morphology_frame(Path(sys.argv[1]),ContentAccess(os.getuid(),os.getgid()),sys.argv[2],index=2)
assert all('app.'+name not in sys.modules for name in names)
print(json.dumps(value,sort_keys=True,separators=(',',':')))
"""
    done=subprocess.run([sys.executable,'-c',code,str(root),artifact],capture_output=True,text=True,timeout=10)
    assert done.returncode==0,done.stderr
    assert json.loads(done.stdout)==expected


@pytest.mark.parametrize('change',['origin','missing-inventory','display-right','rights-extra','duplicate-output',
    'reverse-output','missing-final','too-many-outputs','below-base','zero-initial'])
def test_invalid_programs_do_not_publish_normal_roots(tmp_path,change):
    p=program()
    if change=='origin':p['origin']='reference_observation'
    elif change=='missing-inventory':del p['initial_state']['internodes']
    elif change=='display-right':p['rights']['display']=False
    elif change=='rights-extra':p['rights']['source_approved']=True
    elif change=='duplicate-output':p['output_times'][1]=p['output_times'][0]
    elif change=='reverse-output':p['output_times'].reverse()
    elif change=='missing-final':p['output_times'].pop()
    elif change=='too-many-outputs':p['output_times']=['2026-10-01T08:00:00Z']*65
    elif change=='below-base':p['segments'][0]['air_temperature']['value']=4
    else:p['initial_state']['internodes'][0]['length_state']['length']['value']=0
    root=tmp_path/'artifact'
    with pytest.raises(MorphologyArtifactHold):produce(root,p)
    if root.exists():
        assert not any(json.loads(f.read_bytes()).get('schema_version')=='morphology-research-artifact-v1' for f in root.iterdir())


def test_subsecond_emergence_has_no_completed_root(tmp_path):
    p=program()
    timeline=json.loads((Path(__file__).resolve().parents[2]/'fixtures/crop-shoot-timeline-reference-v1.json').read_bytes())['cases'][3]['inputs']
    p['initial_state']['timeline_state']=timeline['state'];p['segments']=timeline['segments'];p['output_times']=[p['segments'][-1]['end_utc']]
    for n in p['initial_state']['internodes']:
        n['length_state']['clock_state']['base_temperature']['value']=0
        n['length_state']['anchor']['clock_state']['base_temperature']['value']=0
    with pytest.raises(MorphologyArtifactHold,match='SUBSECOND_EMERGENCE_HOLD'):produce(tmp_path/'artifact',p)


def forged_root(root,artifact,mutate):
    manifest=read_morphology_manifest(root,access(),artifact)
    mutate(manifest)
    with MorphologyBlobStore(root,access(),write=True) as store:
        return store.put(_canonical(manifest),maximum=128*1024)


@pytest.mark.parametrize('change',['model','gate','chain','terminal','program-hash'])
def test_unverified_manifest_never_returns_frame(tmp_path,change):
    root=tmp_path/'artifact';artifact=produce(root)
    def mutate(m):
        if change=='model':m['model_versions']['inventory']='unverified-model'
        elif change=='gate':m['gates']='G2_passed'
        elif change=='chain':m['samples'][1]['input_state_sha256']='0'*64
        elif change=='terminal':m['terminal_state_sha256']='0'*64
        else:m['program_sha256']='0'*64
    bad=forged_root(root,artifact,mutate)
    with pytest.raises(MorphologyArtifactHold):read_morphology_frame(root,access(),bad,index=2)


@pytest.mark.parametrize('change',['unit','utc','origin','extra-output'])
def test_typed_reader_rejects_changed_result_even_under_new_hashes(tmp_path,change):
    root=tmp_path/'artifact';artifact=produce(root)
    manifest=read_morphology_manifest(root,access(),artifact);descriptor=manifest['samples'][-1]
    with MorphologyBlobStore(root,access(),write=True) as store:
        result=json.loads(store.get(descriptor['result_sha256'],maximum=2*1024**2))
        if change=='unit':result['state']['internodes'][0]['length_state']['length']['unit']='cm'
        elif change=='utc':result['state']['timeline_state']['at']='2026-10-03T00:00:00Z'
        elif change=='origin':result['state']['internodes'][0]['length_state']['clock_state']['origin']='observed'
        else:result['yield']={'value':1,'unit':'kg'}
        raw=_canonical(result);descriptor['result_sha256']=store.put(raw,maximum=2*1024**2);descriptor['result_bytes']=len(raw)
        descriptor['state_sha256']=manifest['terminal_state_sha256']=sha256(_canonical(result['state'])).hexdigest()
        bad=store.put(_canonical(manifest),maximum=128*1024)
    with pytest.raises(MorphologyArtifactHold):read_morphology_frame(root,access(),bad,index=2)


@pytest.mark.parametrize('index',[True,-1,3])
def test_frame_index_is_explicit_and_bounded(tmp_path,index):
    root=tmp_path/'artifact';artifact=produce(root)
    with pytest.raises(MorphologyArtifactHold):read_morphology_frame(root,access(),artifact,index=index)


def test_failed_later_step_does_not_publish_completed_root(tmp_path,monkeypatch):
    from app import crop_morphology_artifact_producer as producer
    original=producer.inventory.advance_shoot_internode_inventory
    calls=0
    def failing(**kwargs):
        nonlocal calls
        calls+=1
        if calls==2:raise producer.inventory.ShootInventoryHold('NUMERIC_HOLD: controlled test fault')
        return original(**kwargs)
    monkeypatch.setattr(producer.inventory,'advance_shoot_internode_inventory',failing)
    root=tmp_path/'artifact'
    with pytest.raises(MorphologyArtifactHold):produce(root)
    assert calls==2
    assert not any(json.loads(f.read_bytes()).get('schema_version')=='morphology-research-artifact-v1' for f in root.iterdir())
