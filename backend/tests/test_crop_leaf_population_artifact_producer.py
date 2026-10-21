from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app import crop_leaf_population_artifact_producer as producer
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from test_crop_leaf_stem_binding import snapshot

ROOT=Path(__file__).resolve().parents[2]
PROGRAM=(ROOT/'fixtures/crop-leaf-population-software-program-v1.json').read_bytes()


@pytest.fixture(scope='module')
def source(tmp_path_factory):
    directory=tmp_path_factory.mktemp('population-stem')/'blobs';access=ContentAccess(os.getuid(),os.getgid())
    root=produce_rational_morphology_artifact(directory,access,program_raw=(ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    return directory,access,root


def produce(directory,source,raw=PROGRAM):
    return producer.produce_leaf_population_artifact(directory,source[1],stem_directory=source[0],program_raw=raw)


def test_actual_12_population_results_bindings_original_frames_chain_and_repeat(source,tmp_path):
    original=snapshot(source[0]);directory=tmp_path/'population';root=produce(directory,source)
    with MorphologyBlobStore(directory,source[1]) as store:
        manifest=json.loads(store.get(root,maximum=2*1024**2));assert manifest['schema_version']=='leaf-population-research-artifact-v1'
        assert len(manifest['samples'])==12 and manifest['program_sha256']==sha256(PROGRAM).hexdigest()
        previous=manifest['initial_state_sha256'];counts=[]
        for index,item in enumerate(manifest['samples']):
            raw=store.get(item['result_sha256'],maximum=2*1024**2);r=json.loads(raw)
            bound=json.loads(store.get(item['binding_sha256'],maximum=2*1024**2))
            assert item['input_state_sha256']==previous and item['state_sha256']==sha256(producer._canonical(r['state'])).hexdigest()
            assert bound['population_state_sha256']==item['state_sha256'] and bound['tracked_leaf_area']==r['tracked_leaf_area']
            assert bound['stem']==read_rational_morphology_frame(*source,index=index)
            assert bound['at']==item['at'] and bound['tracked_leaf_count']==r['tracked_leaf_count'];counts.append(r['tracked_leaf_count'])
            previous=item['state_sha256']
        assert counts==[3,3,3,4,4,4,4,5,5,5,6,6] and manifest['terminal_state_sha256']==previous
        assert manifest['code_sha256']==producer._code_pins() and len(manifest['code_sha256'])==28
    saved=snapshot(directory);assert len(saved)==40
    assert produce(directory,source)==root and snapshot(directory)==saved and snapshot(source[0])==original


@pytest.mark.parametrize('change',['rights','duplicate-ID','unknown-parent','before-start','after-end','reverse-events','initial-clock','stem-root','stem-program','display','extra'])
def test_invalid_inputs_never_publish_completion_root(source,tmp_path,change):
    p=json.loads(PROGRAM)
    if change=='rights':p['rights']['use']=False
    elif change=='duplicate-ID':p['births'][0]['leaf_id']='declared-leaf-0'
    elif change=='unknown-parent':p['births'][0]['attachment_internode_id']='missing'
    elif change=='before-start':p['births'][0]['emerged_elapsed_seconds_exact']={'numerator':'0','denominator':'1','unit':'s'}
    elif change=='after-end':p['births'][-1]['emerged_elapsed_seconds_exact']={'numerator':'86401','denominator':'1','unit':'s'}
    elif change=='reverse-events':p['births'].reverse()
    elif change=='initial-clock':p['initialization']['initial_inventory']['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='stem-root':p['stem']['artifact_sha256']='0'*64
    elif change=='stem-program':p['stem']['program_sha256']='0'*64
    elif change=='display':p['display_policy']['leaf_count']='predicted'
    elif change=='extra':p['cultivar']='not-authorized'
    directory=tmp_path/'population'
    with pytest.raises(MorphologyArtifactHold):produce(directory,source,producer._canonical(p))
    if directory.exists():
        assert all(json.loads(f.read_bytes()).get('schema_version')!='leaf-population-research-artifact-v1' for f in directory.iterdir())


@pytest.mark.parametrize('change_after',[2,13])
def test_source_change_before_completion_never_publishes_root(source,tmp_path,monkeypatch,change_after):
    original=producer._code_pins;calls=[]
    def changed():
        value=original();calls.append(1)
        if len(calls)>change_after:value[next(iter(value))]='0'*64
        return value
    monkeypatch.setattr(producer,'_code_pins',changed)
    directory=tmp_path/'population'
    with pytest.raises(MorphologyArtifactHold,match='CODE_HOLD'):produce(directory,source)
    assert all(json.loads(f.read_bytes()).get('schema_version')!='leaf-population-research-artifact-v1' for f in directory.iterdir())
