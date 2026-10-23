from fractions import Fraction
from hashlib import sha256
import json
import shutil
import subprocess

import pytest

from app import crop_leaf_appearance_artifact_producer as producer
from app import crop_leaf_appearance_preparation as preparation
from app import crop_leaf_population_artifact_producer as inner_producer
from app import crop_leaf_population_artifact_reader as inner_reader
from app.crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore
from test_crop_leaf_appearance_program import program
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, snapshot, reference_area, fraction


MAX = 2*1024**2


def produce(directory, source, value=None):
    return producer.produce_leaf_appearance_artifact(directory, source[1], stem_directory=source[0],
        program_raw=canonical(program() if value is None else value))


def appearances(directory):
    if not directory.exists(): return []
    return [p.name for p in directory.iterdir()
        if json.loads(p.read_bytes()).get('schema_version') == 'leaf-appearance-research-artifact-v1']


def test_original_source_preparation_generated_program_inner_frames_and_repeat(source, tmp_path):
    original = snapshot(source[0]); directory = tmp_path/'appearance'; p = program(); raw = canonical(p)
    root = produce(directory, source); saved = snapshot(directory)
    assert len(saved) == 43 and len(appearances(directory)) == 1
    with MorphologyBlobStore(directory, source[1]) as store:
        manifest_raw = store.get(root, maximum=MAX); manifest = json.loads(manifest_raw)
        assert manifest_raw == canonical(manifest) and manifest['schema_version'] == 'leaf-appearance-research-artifact-v1'
        assert manifest['status'] == 'completed_software_fixture' and manifest['gates'] == 'not_assessed'
        assert manifest['source_program_sha256'] == sha256(raw).hexdigest() and manifest['source_program_bytes'] == len(raw)
        assert store.get(manifest['source_program_sha256'], maximum=MAX) == raw
        prepared_raw = store.get(manifest['preparation_sha256'], maximum=MAX); prepared = json.loads(prepared_raw)
        assert len(prepared_raw) == manifest['preparation_bytes'] and prepared == preparation.prepare_leaf_appearance_program(
            source[0], source[1], program_raw=raw)
        generated_raw = store.get(manifest['generated_program_sha256'], maximum=MAX)
        assert len(generated_raw) == manifest['generated_program_bytes'] and generated_raw == canonical(prepared['generated_program'])
        assert manifest['program_rights'] == p['rights'] and manifest['display_policy'] == p['display_policy']
        assert manifest['code_sha256'] == producer._code_pins() and len(manifest['code_sha256']) == 33
        assert all(manifest['code_sha256'][k] == v for k,v in prepared['code_sha256'].items())
        inner = inner_reader.read_leaf_population_manifest(directory, source[1], manifest['population_artifact_sha256'])
        assert manifest['initial_state_sha256'] == inner['initial_state_sha256'] == prepared['initial_state_sha256']
        assert manifest['terminal_state_sha256'] == inner['terminal_state_sha256']
        assert manifest['sample_count'] == len(inner['samples']) == 12
        assert manifest['time_origin_utc'] == inner['time_origin_utc']
        assert manifest['initial_at_elapsed_seconds_exact'] == inner['initial_at_elapsed_seconds_exact']
        assert manifest['stem_artifact_sha256'] == source[2] and manifest['stem_program_sha256'] == p['stem']['program_sha256']
        count = 0; counts = []
        initial = p['initialization']['initial_inventory']['leaves']
        refs = {v['initialization']['clock_state']['leaf_id']: (0, v['initialization']) for v in initial}
        for event,age in zip(prepared['generated_program']['births'], [5,15], strict=True):
            refs[event['leaf_id']] = (age,p['leaf_profile'])
        for index in range(12):
            frame = inner_reader.read_leaf_population_frame(directory, source[1], manifest['population_artifact_sha256'], index=index)
            assert frame['at'] == inner['samples'][index]['at']; counts.append(frame['tracked_leaf_count'])
            for leaf in frame['leaves']:
                age,profile = refs[leaf['leaf_id']]; expected_age = Fraction(17*(index+1),12)-age
                assert fraction(leaf['age_exact']) == expected_age
                assert leaf['area']['value'] == pytest.approx(reference_area(expected_age, profile), rel=1e-12, abs=0)
                count += 1
        assert count == 47 and counts == [3,3,3,4,4,4,4,4,4,4,5,5]
    assert produce(directory, source) == root and snapshot(directory) == saved and snapshot(source[0]) == original


def test_preexisting_inner_calculation_root_and_files_remain_identical(source, tmp_path):
    directory = tmp_path/'appearance'; prepared = preparation.prepare_leaf_appearance_program(source[0],source[1],program_raw=canonical(program()))
    old_root = inner_producer.produce_leaf_population_artifact(directory,source[1],stem_directory=source[0],program_raw=canonical(prepared['generated_program']))
    saved = snapshot(directory); root = produce(directory,source)
    now = snapshot(directory); assert all(now[k] == v for k,v in saved.items()) and len(now) == len(saved)+3
    with MorphologyBlobStore(directory,source[1]) as store:
        assert json.loads(store.get(root,maximum=MAX))['population_artifact_sha256'] == old_root


@pytest.mark.parametrize('field',['ownership_asserted','access','store','use','transform','display'])
def test_source_rights_never_inferred(source,tmp_path,field):
    value = program(); value['rights'][field] = False; directory = tmp_path/'appearance'
    with pytest.raises(producer.LeafAppearanceArtifactHold): produce(directory,source,value)
    assert not appearances(directory)


def test_internal_no_redistribution_and_separate_source_directory(source,tmp_path):
    p = program(); p['rights']['redistribute'] = False
    directory = tmp_path/'appearance'; root = produce(directory,source,p)
    with MorphologyBlobStore(directory,source[1]) as store:
        assert json.loads(store.get(root,maximum=MAX))['program_rights']['redistribute'] is False
    original = snapshot(source[0])
    with pytest.raises(producer.LeafAppearanceArtifactHold,match='STORAGE_HOLD'):produce(source[0],source)
    assert snapshot(source[0]) == original


@pytest.mark.parametrize('after',[1,2])
def test_late_source_code_change_never_publishes_outer_root(source,tmp_path,monkeypatch,after):
    original = producer._code_pins; calls = []
    def changed():
        value = original();calls.append(1)
        if len(calls)>after:value[next(iter(value))]='0'*64
        return value
    monkeypatch.setattr(producer,'_code_pins',changed); directory = tmp_path/'appearance'
    with pytest.raises(producer.LeafAppearanceArtifactHold,match='CODE_HOLD'): produce(directory,source)
    assert not appearances(directory)


@pytest.mark.parametrize('target',['source-raw','preparation','generated','inner-root','inner-result','inner-binding',
    'original-middle','original-root','original-program','copied-stem-middle','copied-stem-root','copied-stem-program'])
def test_late_blob_change_never_publishes_outer_root(source,tmp_path,monkeypatch,target):
    parent = tmp_path/'source'; shutil.copytree(source[0],parent); current = (parent,source[1],source[2])
    directory = tmp_path/'appearance'; original_put = MorphologyBlobStore.put; seen = []
    prepared = preparation.prepare_leaf_appearance_program(parent,source[1],program_raw=canonical(program()))
    source_sha = sha256(canonical(program())).hexdigest(); prep_sha = sha256(canonical(prepared)).hexdigest()
    def poisoned(store,raw,*,maximum):
        digest = original_put(store,raw,maximum=maximum)
        if digest == prep_sha and not seen:
            seen.append(1)
            if target=='source-raw': path=directory/source_sha
            elif target=='preparation': path=directory/prep_sha
            elif target=='generated':path=directory/prepared['generated_program_sha256']
            else:
                files={f.name:json.loads(f.read_bytes()) for f in directory.iterdir()}
                inner_sha,inner=next((h,v) for h,v in files.items() if v.get('schema_version')=='leaf-population-research-artifact-v1')
                if target=='inner-root':path=directory/inner_sha
                elif target.startswith(('original-','copied-stem-')):
                    stem=files[inner['stem_artifact_sha256']]
                    address = inner['stem_artifact_sha256'] if target.endswith('-root') else (
                        inner['stem_program_sha256'] if target.endswith('-program') else stem['samples'][5]['result_sha256'])
                    path=(parent if target.startswith('original-') else directory)/address
                else:path=directory/inner['samples'][5]['binding_sha256' if target=='inner-binding' else 'result_sha256']
            path.write_bytes(b'{}')
        return digest
    monkeypatch.setattr(MorphologyBlobStore,'put',poisoned)
    with pytest.raises(producer.LeafAppearanceArtifactHold):produce(directory,current)
    assert seen == [1] and not appearances(directory)


@pytest.mark.parametrize('change',['rights','births','initial-state','code','scope'])
def test_late_changed_preparation_refuses_completion(source,tmp_path,monkeypatch,change):
    original = preparation.prepare_leaf_appearance_program; calls=[]
    def changed(*args,**kwargs):
        value=original(*args,**kwargs);calls.append(1)
        if len(calls)>1:
            if change=='rights':value['generated_program']['rights']['display']=False
            elif change=='births':value['derivation']['events'].pop()
            elif change=='initial-state':value['initial_state_sha256']='0'*64
            elif change=='code':value['code_sha256'][next(iter(value['code_sha256']))]='0'*64
            else:value['gates']='approved'
        return value
    monkeypatch.setattr(preparation,'prepare_leaf_appearance_program',changed);directory=tmp_path/'appearance'
    with pytest.raises(producer.LeafAppearanceArtifactHold):produce(directory,source)
    assert len(calls)==2 and not appearances(directory)


@pytest.mark.parametrize('stage',['preparation','outer'])
def test_storage_failure_leaves_no_appearance_completion(source,tmp_path,monkeypatch,stage):
    directory=tmp_path/'appearance';original=MorphologyBlobStore.put
    def failed(store,raw,*,maximum):
        p=json.loads(raw)
        if (stage=='preparation' and p.get('model_version')==preparation.MODEL_VERSION) or p.get('schema_version')=='leaf-appearance-research-artifact-v1':
            raise MorphologyArtifactHold('STORAGE_HOLD: owned injected failure')
        return original(store,raw,maximum=maximum)
    monkeypatch.setattr(MorphologyBlobStore,'put',failed)
    with pytest.raises(producer.LeafAppearanceArtifactHold):produce(directory,source)
    assert not appearances(directory)


def test_growth_only_inside_inner_producer_and_no_database_or_cli(source,tmp_path,monkeypatch):
    import psycopg
    from app import crop_leaf_population as population
    entered=[];calls=[];original_producer=inner_producer.produce_leaf_population_artifact;advance=population.advance_leaf_population
    def entry(*args,**kwargs):
        entered.append(True)
        try:return original_producer(*args,**kwargs)
        finally:entered.pop()
    def grow(*args,**kwargs):
        assert entered==[True];calls.append(1);return advance(*args,**kwargs)
    def forbidden(*args,**kwargs):raise AssertionError('forbidden database or CLI')
    monkeypatch.setattr(inner_producer,'produce_leaf_population_artifact',entry)
    monkeypatch.setattr(population,'advance_leaf_population',grow)
    monkeypatch.setattr(psycopg,'connect',forbidden);monkeypatch.setattr(subprocess,'run',forbidden);monkeypatch.setattr(subprocess,'Popen',forbidden)
    produce(tmp_path/'appearance',source);assert len(calls)==12 and not entered


@pytest.mark.parametrize('target',['result_sha256','binding_sha256'])
def test_late_output_change_during_final_preparation_refuses_completion(source,tmp_path,monkeypatch,target):
    directory=tmp_path/'appearance'; original=preparation.prepare_leaf_appearance_program; calls=[]
    def changed(*args,**kwargs):
        value=original(*args,**kwargs);calls.append(1)
        if len(calls)==2:
            files={f.name:json.loads(f.read_bytes()) for f in directory.iterdir()}
            inner=next(v for v in files.values() if v.get('schema_version')=='leaf-population-research-artifact-v1')
            path=directory/inner['samples'][5][target];path.write_bytes(b'{}')
        return value
    monkeypatch.setattr(preparation,'prepare_leaf_appearance_program',changed)
    with pytest.raises(producer.LeafAppearanceArtifactHold):produce(directory,source)
    assert len(calls)==2 and not appearances(directory)


def test_failed_new_version_preserves_completed_old_version(source,tmp_path,monkeypatch):
    directory=tmp_path/'appearance';old_root=produce(directory,source);before=snapshot(directory)
    p=program();p['program_id']='new-appearance-version';original=MorphologyBlobStore.put
    def failed(store,raw,*,maximum):
        value=json.loads(raw)
        if value.get('schema_version')=='leaf-appearance-research-artifact-v1':
            raise MorphologyArtifactHold('STORAGE_HOLD: injected publication failure')
        return original(store,raw,maximum=maximum)
    monkeypatch.setattr(MorphologyBlobStore,'put',failed)
    with pytest.raises(producer.LeafAppearanceArtifactHold):produce(directory,source,p)
    after=snapshot(directory);assert all(after[k]==v for k,v in before.items())
    assert appearances(directory)==[old_root] and len(after)>len(before)
