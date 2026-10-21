from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from app.crop_leaf_stem_binding import LeafStemBindingHold,bind_leaf_population_to_stored_stem
from app import crop_leaf_population as population,crop_declared_leaf_births as births,crop_rational_leaf_area as leaf
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from test_crop_rational_leaf_area import seconds

ROOT=Path(__file__).resolve().parents[2]
STEM_ROOT='436ed27cde92465c4aad93e1fc0ac52bc03027861b22fd80b15e80683dac0e4a'
PROGRAM=json.loads((ROOT/'fixtures/crop-leaf-area-software-program-v1.json').read_bytes())


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def fraction(value):return Fraction(int(value['numerator']),int(value['denominator']))


@pytest.fixture(scope='module')
def source(tmp_path_factory):
    directory=tmp_path_factory.mktemp('leaf-stem-original')/'blobs';access=ContentAccess(os.getuid(),os.getgid())
    root=produce_rational_morphology_artifact(directory,access,program_raw=(ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    assert root==STEM_ROOT
    return directory,access,root


def events(source):
    stem=read_rational_morphology_frame(*source,index=11);prototype=PROGRAM['initialization']['leaves'][0]['initialization'];result=[]
    for i,node in enumerate(stem['internodes'][3:]):
        result.append({'leaf_id':'explicit-followup-leaf-'+str(i),'attachment_internode_id':node['internode_id'],
            'emerged_elapsed_seconds_exact':deepcopy(node['emerged_elapsed_seconds_exact']),
            **{key:deepcopy(prototype[key]) for key in ['curve','normalization','initial_area']},
            'base_temperature':deepcopy(prototype['clock_state']['base_temperature'])})
    return result


def at(source,index=11,declared=None):
    end=(index+1)*7200;initial=population.initialize_leaf_population(inputs={'input_id':'explicit-population','initial_inventory':deepcopy(PROGRAM['initialization'])})['state']
    selected=[e for e in (events(source) if declared is None else declared) if fraction(e['emerged_elapsed_seconds_exact'])<=end]
    return population.advance_leaf_population(inputs={'input_id':'explicit-advance','state':initial,
        'segments':[{'start_elapsed_seconds_exact':seconds(0),'end_elapsed_seconds_exact':seconds(end),'air_temperature':{'value':22,'unit':'degC'}}],
        'births':selected})


def snapshot(directory):
    result={}
    for p in directory.iterdir():
        s=p.stat();result[p.name]=[s.st_dev,s.st_ino,s.st_uid,s.st_gid,s.st_mode,s.st_nlink,s.st_size,s.st_mtime_ns,s.st_ctime_ns,sha256(p.read_bytes()).hexdigest()]
    return result


def test_actual_all_12_original_stem_frames_and_exact_new_leaf_attachments(source,monkeypatch):
    before=snapshot(source[0]);prepared=[at(source,i) for i in range(12)];advances=[]
    def forbidden(*a,**kw):advances.append(1);raise AssertionError('binding cannot advance growth or create events')
    monkeypatch.setattr(population,'advance_leaf_population',forbidden);monkeypatch.setattr(births,'create_declared_leaves',forbidden)
    monkeypatch.setattr(leaf,'advance_rational_leaf_area',forbidden);monkeypatch.setattr(MorphologyBlobStore,'put',forbidden)
    import subprocess,psycopg
    from app.job_store import JobStore
    monkeypatch.setattr(JobStore,'connect',forbidden);monkeypatch.setattr(psycopg,'connect',forbidden)
    monkeypatch.setattr(subprocess,'run',forbidden);monkeypatch.setattr(subprocess,'Popen',forbidden)
    original_open=os.open
    def readonly_open(path,flags,*a,**kw):
        if flags&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):return forbidden()
        return original_open(path,flags,*a,**kw)
    monkeypatch.setattr(os,'open',readonly_open)
    for i,result in enumerate(prepared):
        state=result['state'];original=deepcopy(state);bound=bind_leaf_population_to_stored_stem(*source,index=i,population_state=state)
        assert canonical(bound['stem'])==(ROOT/f'web/public/morphology-rational-replay/frame-{i}.json').read_bytes()
        assert bound['tracked_leaf_count']==result['tracked_leaf_count']==len(bound['leaves'])==len(bound['stem']['internodes'])
        assert bound['tracked_leaf_area']==result['tracked_leaf_area']
        assert bound['population_state_sha256']==sha256(canonical(state)).hexdigest() and bound['stem_artifact_sha256']==STEM_ROOT
        assert bound['at']==bound['stem']['at'] and bound['scope']=='software_research_only' and bound['gates']=='not_assessed'
        for item in bound['leaves']:
            parent=next(n for n in bound['stem']['internodes'] if n['internode_id']==item['attachment_internode_id'])
            assert fraction(parent['emerged_elapsed_seconds_exact'])<=fraction(item['emerged_elapsed_seconds_exact'])
            assert item['area']['unit']=='m2' and item['age_exact']['unit']=='degC_day'
        assert state==original
    assert advances==[] and snapshot(source[0])==before


@pytest.mark.parametrize('change',['unknown-attachment','future-parent','leaf-before-parent','different-origin','different-current','fractional-current'])
def test_attachment_and_time_mismatch_hold(source,change):
    declared=events(source);index=11
    if change=='leaf-before-parent':declared[0]['emerged_elapsed_seconds_exact']=seconds(fraction(declared[0]['emerged_elapsed_seconds_exact'])-1)
    p=deepcopy(PROGRAM['initialization'])
    if change=='unknown-attachment':p['leaves'][0]['attachment_internode_id']='missing-in-stored-frame'
    elif change=='future-parent':p['leaves'][0]['attachment_internode_id']=declared[0]['attachment_internode_id'];index=0;declared=[]
    initial=population.initialize_leaf_population(inputs={'input_id':'test','initial_inventory':p})['state']
    state=population.advance_leaf_population(inputs={'input_id':'test','state':initial,
        'segments':[{'start_elapsed_seconds_exact':seconds(0),'end_elapsed_seconds_exact':seconds((index+1)*7200),
                     'air_temperature':{'value':22,'unit':'degC'}}],'births':declared})['state']
    if change in ['different-origin','different-current','fractional-current']:
        if change=='different-origin':
            state['time_origin_utc']='2026-10-02T00:00:00Z';state['initial_inventory_state']['time_origin_utc']=state['time_origin_utc']
            for item in state['initial_inventory_state']['leaves']:
                for key in ['clock_state','clock_anchor']:item['state'][key]['time_origin_utc']=state['time_origin_utc']
            for item in state['new_leaves']:
                for key in ['clock_state','clock_anchor']:item['state'][key]['time_origin_utc']=state['time_origin_utc']
        elif change=='different-current':index=10
        else:
            state=population.advance_leaf_population(inputs={'input_id':'fractional-current','state':state,
                'segments':[{'start_elapsed_seconds_exact':seconds(86400),'end_elapsed_seconds_exact':seconds(Fraction(86400)+Fraction(1,3)),
                    'air_temperature':{'value':22,'unit':'degC'}}],'births':[]})['state']
    with pytest.raises(LeafStemBindingHold):bind_leaf_population_to_stored_stem(*source,index=index,population_state=state)


@pytest.mark.parametrize('index',[-1,12,True,.5])
def test_invalid_stored_frame_index(source,index):
    with pytest.raises(LeafStemBindingHold):bind_leaf_population_to_stored_stem(*source,index=index,population_state=at(source)['state'])


def test_wrong_root_hold(source):
    with pytest.raises(LeafStemBindingHold):bind_leaf_population_to_stored_stem(source[0],source[1],'0'*64,index=11,population_state=at(source)['state'])


def test_corrupt_copied_stem_blob_holds_and_original_remains(source,tmp_path):
    import shutil
    from app.crop_rational_morphology_artifact_reader import read_rational_morphology_manifest
    before=snapshot(source[0]);state=at(source)['state'];manifest=read_rational_morphology_manifest(*source)
    copied=tmp_path/'copied-stem';shutil.copytree(source[0],copied)
    path=copied/manifest['samples'][11]['result_sha256'];path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(LeafStemBindingHold):bind_leaf_population_to_stored_stem(copied,source[1],source[2],index=11,population_state=state)
    assert snapshot(source[0])==before
