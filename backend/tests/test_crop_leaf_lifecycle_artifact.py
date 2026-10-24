from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
import shutil
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_leaf_lifecycle_artifact_producer as producer
from app import crop_leaf_lifecycle_artifact_reader as reader
from app import crop_leaf_appearance_artifact_producer as original_producer
from app import crop_leaf_appearance_artifact_reader as original_reader
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_leaf_appearance_program import program as appearance_program
from test_crop_leaf_lifecycle_preparation import management, removal
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, snapshot, exact, fraction, reference_area


@pytest.fixture(scope='module')
def artifacts(source, tmp_path_factory):
    p = appearance_program(); raw = canonical(p); m = management(raw)
    old_dir = tmp_path_factory.mktemp('lifecycle-reference')/'blobs'
    old_root = original_producer.produce_leaf_appearance_artifact(old_dir, source[1], stem_directory=source[0], program_raw=raw)
    directory = tmp_path_factory.mktemp('lifecycle-artifact')/'blobs'
    root = producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0],
                                                   appearance_program_raw=raw, management_raw=canonical(m))
    return (directory, source[1], root), (old_dir, source[1], old_root), raw, m


def result(artifact, index):
    m = reader.read_leaf_lifecycle_manifest(*artifact)
    with MorphologyBlobStore(artifact[0], artifact[1]) as store:
        return json.loads(store.get(m['samples'][index]['result_sha256'], maximum=2 * 1024**2))


def leaves(value):
    state = value['state']
    return [x['state'] for x in [*state['existing_inventory_state']['leaf_checkpoints'], *state['new_leaf_checkpoints']] if x['state'] is not None]


def test_no_removal_original12frames47states_same_UTC_ids_areas_and_stored_hash_chain(artifacts):
    artifact, old, _, _ = artifacts; before = snapshot(artifact[0]); manifest = reader.read_leaf_lifecycle_manifest(*artifact)
    assert manifest['schema_version'] == 'leaf-lifecycle-research-artifact-v1' and len(manifest['samples']) == 12
    previous = manifest['initial_state_sha256']; count = 0
    for index in range(12):
        frame = reader.read_leaf_lifecycle_frame(*artifact, index=index)
        original = original_reader.read_leaf_appearance_frame(*old, index=index)
        assert frame['at'] == original['at'] and frame['stem'] == original['stem']
        assert frame['active_leaves'] == original['leaves'] and frame['active_leaf_area'] == original['tracked_leaf_area']
        assert frame['removed_leaves'] == [] and frame['removed_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
        assert frame['pending_leaf_count'] + frame['tracked_leaf_count'] == frame['declared_leaf_count'] == 5
        current = result(artifact, index); count += len(leaves(current)); descriptor = manifest['samples'][index]
        assert descriptor['input_state_sha256'] == previous
        assert descriptor['state_sha256'] == sha256(canonical(current['state'])).hexdigest()
        assert descriptor['input_sha256'] == current['input_sha256']; previous = descriptor['state_sha256']
    assert count == 47 and previous == manifest['terminal_state_sha256'] and snapshot(artifact[0]) == before


def test_original_sources_rights_preparation_and_repeat_are_preserved(artifacts, source):
    artifact, _, raw, m = artifacts; before = snapshot(artifact[0]); old_source = snapshot(source[0])
    manifest = reader.read_leaf_lifecycle_manifest(*artifact)
    assert manifest['appearance_program_sha256'] == sha256(raw).hexdigest()
    assert manifest['management_program_sha256'] == sha256(canonical(m)).hexdigest()
    assert manifest['source_rights']['appearance'] == appearance_program()['rights']
    assert manifest['source_rights']['management'] == m['rights']
    assert producer.produce_leaf_lifecycle_artifact(artifact[0], artifact[1], stem_directory=source[0],
        appearance_program_raw=raw, management_raw=canonical(m)) == artifact[2]
    assert snapshot(artifact[0]) == before and snapshot(source[0]) == old_source


def test_removed_initial_and_newborn_keep_last_state_while_pending_and_current_time_are_separate(source, tmp_path):
    raw = canonical(appearance_program())
    prepared = producer.preparation.prepare_leaf_lifecycle_program(source[0], source[1], appearance_program_raw=raw,
                                                                  management_raw=canonical(management(raw)))
    births = prepared['lifecycle_initialization']['births']; initial = prepared['lifecycle_initialization']['population_state']
    records = [removal(x['state']['clock_state']['leaf_id'], Fraction(0), 'initial-' + str(i)) for i, x in enumerate(initial['initial_inventory_state']['leaves'])]
    records += [removal(b['leaf_id'], fraction(b['emerged_elapsed_seconds_exact']), 'new-' + str(i)) for i, b in enumerate(births)]
    directory = tmp_path/'removed'; root = producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0],
        appearance_program_raw=raw, management_raw=canonical(management(raw, records)))
    for index in range(12):
        frame = reader.read_leaf_lifecycle_frame(directory, source[1], root, index=index)
        assert frame['active_leaves'] == [] and frame['active_leaf_area'] == {'value': 0.0, 'unit': 'm2'}
        assert frame['pending_leaf_count'] + frame['removed_leaf_count'] == 5
        for leaf in frame['removed_leaves']:
            assert fraction(leaf['last_at_elapsed_seconds_exact']) <= fraction(frame['at_elapsed_seconds_exact'])
            if leaf['leaf_id'].startswith('declared-leaf-'): assert leaf['last_at_elapsed_seconds_exact'] == exact(0)
            else: assert fraction(leaf['age_exact']) == 0
            assert leaf['last_at_elapsed_seconds_exact'] == leaf['removal_declaration']['at_elapsed_seconds_exact']
    assert frame['removed_leaf_count'] == 5 and frame['pending_leaf_count'] == 0


@pytest.mark.parametrize('index', [True, False, -1, 12, 1.0, '1', None])
def test_explicit_bounded_integer_index(artifacts, index):
    with pytest.raises(reader.LeafLifecycleReadHold): reader.read_leaf_lifecycle_frame(*artifacts[0], index=index)


def forged(artifact, directory, change, *, part='manifest', index=0):
    shutil.copytree(artifact[0], directory)
    with MorphologyBlobStore(directory, artifact[1], write=True) as store:
        manifest = json.loads(store.get(artifact[2], maximum=reader.MAX))
        if part == 'manifest': change(manifest)
        elif part == 'preparation':
            value = json.loads(store.get(manifest['preparation_sha256'], maximum=reader.MAX)); change(value)
            if 'lifecycle_initialization' in value: value['lifecycle_initialization_sha256'] = sha256(canonical(value['lifecycle_initialization'])).hexdigest()
            raw = canonical(value); manifest['preparation_sha256'] = store.put(raw, maximum=reader.MAX); manifest['preparation_bytes'] = len(raw)
        elif part == 'result':
            descriptor = manifest['samples'][index]; value = json.loads(store.get(descriptor['result_sha256'], maximum=reader.MAX)); changed = change(value)
            if changed is not None: value = changed
            raw = canonical(value); descriptor['result_sha256'] = store.put(raw, maximum=reader.MAX); descriptor['result_bytes'] = len(raw)
            if isinstance(value, dict) and 'state' in value:
                descriptor['state_sha256'] = sha256(canonical(value['state'])).hexdigest()
                if index + 1 < len(manifest['samples']): manifest['samples'][index + 1]['input_state_sha256'] = descriptor['state_sha256']
                else: manifest['terminal_state_sha256'] = descriptor['state_sha256']
                if 'input_sha256' in value: descriptor['input_sha256'] = value['input_sha256']
        root = store.put(canonical(manifest), maximum=reader.MAX)
    return directory, artifact[1], root


def test_selected_result_must_be_a_closed_object_even_with_a_new_valid_blob_hash(artifacts, tmp_path):
    value = forged(artifacts[0], tmp_path/'non-object', lambda _: [], part='result')
    with pytest.raises(reader.LeafLifecycleReadHold): reader.read_leaf_lifecycle_frame(*value, index=0)


@pytest.mark.parametrize('fault', ['extra', 'scope', 'display-bool', 'model', 'code-shape', 'code-link', 'preparation-size',
                                  'initial-size', 'missing-sample', 'index-bool', 'chain', 'origin', 'initial-time', 'terminal', 'stem'])
def test_rehashed_manifest_does_not_approve_changed_original_metadata(artifacts, tmp_path, fault):
    def change(m):
        if fault == 'extra': m['harvest_kg'] = 10
        elif fault == 'scope': m['gates'] = 'approved'
        elif fault == 'display-bool': m['display_policy']['petiole_rachis_area_excluded'] = 1
        elif fault == 'model': m['model_versions']['lifecycle'] = 'unknown'
        elif fault == 'code-shape': m['code_sha256']['unknown'] = '0' * 64
        elif fault == 'code-link': m['code_sha256']['backend/app/crop_morphology_artifact_io.py'] = '0' * 64
        elif fault == 'preparation-size': m['preparation_bytes'] += 1
        elif fault == 'initial-size': m['initial_state_bytes'] = True
        elif fault == 'missing-sample': m['samples'].pop()
        elif fault == 'index-bool': m['samples'][0]['index'] = False
        elif fault == 'chain': m['samples'][1]['input_state_sha256'] = '0' * 64
        elif fault == 'origin': m['time_origin_utc'] = '2026-10-01T00:00:01Z'
        elif fault == 'initial-time': m['initial_at_elapsed_seconds_exact'] = exact(1)
        elif fault == 'terminal': m['terminal_state_sha256'] = '0' * 64
        elif fault == 'stem': m['stem_program_sha256'] = '0' * 64
    value = forged(artifacts[0], tmp_path/fault, change)
    with pytest.raises(reader.LeafLifecycleReadHold): reader.read_leaf_lifecycle_manifest(*value)


@pytest.mark.parametrize('fault', ['extra', 'model', 'input-sha', 'source', 'forcing', 'rights', 'original-preparation', 'births', 'removals'])
def test_rehashed_preparation_still_must_match_original_sources(artifacts, tmp_path, fault):
    def change(p):
        if fault == 'extra': p['result_ready'] = True
        elif fault == 'model': p['model_version'] = 'unknown'
        elif fault == 'input-sha': p['input_sha256'] = '0' * 64
        elif fault == 'source': p['appearance_program_sha256'] = '0' * 64
        elif fault == 'forcing': p['forcing'][0]['air_temperature']['value'] += 1
        elif fault == 'rights': p['source_rights']['management']['display'] = False
        elif fault == 'original-preparation': p['appearance_preparation']['derivation_sha256'] = '0' * 64
        elif fault == 'births': p['lifecycle_initialization']['births'][0]['attachment_internode_id'] = 'other'
        elif fault == 'removals': p['lifecycle_initialization']['removals'] = [removal('declared-leaf-0', Fraction(1, 3))]
    value = forged(artifacts[0], tmp_path/fault, change, part='preparation')
    with pytest.raises(reader.LeafLifecycleReadHold): reader.read_leaf_lifecycle_manifest(*value)


@pytest.mark.parametrize('fault', ['extra', 'model', 'gate', 'input-sha', 'count', 'area', 'IDs', 'global-time', 'source',
                                  'missing-current', 'pending-current', 'declaration', 'receipt', 'new-clock'])
def test_rehashed_selected_result_is_validated_against_original_input(artifacts, tmp_path, fault):
    def change(r):
        if fault == 'extra': r['yield_kg'] = 100
        elif fault == 'model': r['model_version'] = 'unknown'
        elif fault == 'gate': r['gates'] = 'approved'
        elif fault == 'input-sha': r['input_sha256'] = '0' * 64
        elif fault == 'count': r['active_leaf_count'] = True
        elif fault == 'area': r['active_leaf_area']['value'] *= 2
        elif fault == 'IDs': r['active_leaf_ids'].reverse()
        elif fault == 'global-time': r['at_elapsed_seconds_exact'] = exact(1)
        elif fault == 'source': r['state']['existing_inventory_state']['source_population_sha256'] = '0' * 64
        elif fault == 'missing-current': r['state']['existing_inventory_state']['leaf_checkpoints'].pop()
        elif fault == 'pending-current': r['state']['new_leaf_checkpoints'][0]['state'] = deepcopy(r['state']['existing_inventory_state']['leaf_checkpoints'][0]['state'])
        elif fault == 'declaration': r['state']['birth_declarations_sha256'] = '0' * 64
        elif fault == 'receipt': r['state']['existing_inventory_state']['leaf_checkpoints'][0]['removal_receipt'] = {}
        elif fault == 'new-clock': r['state']['existing_inventory_state']['leaf_checkpoints'][0]['state']['clock_state']['at_elapsed_seconds_exact'] = exact(0)
    value = forged(artifacts[0], tmp_path/fault, change, part='result')
    with pytest.raises(reader.LeafLifecycleReadHold): reader.read_leaf_lifecycle_frame(*value, index=0)


@pytest.mark.parametrize('target', ['appearance', 'management'])
def test_no_redistribution_grant_is_preserved_for_internal_replay(source, tmp_path, target):
    p = appearance_program()
    if target == 'appearance': p['rights']['redistribute'] = False
    raw = canonical(p); m = management(raw)
    if target == 'management': m['rights']['redistribute'] = False
    root = producer.produce_leaf_lifecycle_artifact(tmp_path/'internal', source[1], stem_directory=source[0],
                                                   appearance_program_raw=raw, management_raw=canonical(m))
    assert reader.read_leaf_lifecycle_manifest(tmp_path/'internal', source[1], root)['source_rights'][target]['redistribute'] is False
    assert len(reader.read_leaf_lifecycle_frame(tmp_path/'internal', source[1], root, index=11)['active_leaves']) == 5


def completed_roots(directory):
    if not directory.exists(): return set()
    return {p.name for p in directory.iterdir() if json.loads(p.read_bytes()).get('schema_version') == 'leaf-lifecycle-research-artifact-v1'}


@pytest.mark.parametrize('stage', ['management', 'result', 'completion'])
def test_storage_failure_never_publishes_new_completion_or_changes_old_artifact(artifacts, source, tmp_path, monkeypatch, stage):
    original_artifact, _, raw, m = artifacts; directory = tmp_path/'with-old'; shutil.copytree(original_artifact[0], directory)
    old_files = snapshot(directory); old_roots = completed_roots(directory); m = deepcopy(m); m['removals'] = [removal('declared-leaf-0', Fraction(1, 3))]
    original = MorphologyBlobStore.put
    def fail(store, blob, *, maximum):
        value = json.loads(blob)
        selected = (stage == 'management' and value.get('schema_version') == 'leaf-lifecycle-management-program-v1') or (
            stage == 'result' and value.get('model_version') == reader.LIFECYCLE_VERSION and 'state' in value) or (
            stage == 'completion' and value.get('schema_version') == 'leaf-lifecycle-research-artifact-v1')
        if selected: raise producer.LeafLifecycleArtifactHold('STORAGE_HOLD: injected stage failure')
        return original(store, blob, maximum=maximum)
    monkeypatch.setattr(MorphologyBlobStore, 'put', fail)
    with pytest.raises(producer.LeafLifecycleArtifactHold):
        producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0], appearance_program_raw=raw, management_raw=canonical(m))
    after = snapshot(directory)
    assert all(after[k] == v for k, v in old_files.items()) and completed_roots(directory) == old_roots
    assert reader.read_leaf_lifecycle_frame(directory, source[1], original_artifact[2], index=11)['tracked_leaf_count'] == 5


@pytest.mark.parametrize('after', [1, 3])
def test_producer_code_drift_never_publishes_completion(source, tmp_path, monkeypatch, after):
    original = producer._code_pins; calls = []
    def changed():
        result = original(); calls.append(1)
        if len(calls) > after: result['backend/app/crop_leaf_lifecycle.py'] = '0' * 64
        return result
    monkeypatch.setattr(producer, '_code_pins', changed); directory = tmp_path/'drift'; raw = canonical(appearance_program())
    with pytest.raises(producer.LeafLifecycleArtifactHold, match='CODE_HOLD'):
        producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0], appearance_program_raw=raw, management_raw=canonical(management(raw)))
    assert completed_roots(directory) == set()


def test_late_original_source_change_after_calculation_prevents_completion(source, tmp_path, monkeypatch):
    directory = tmp_path/'source'; shutil.copytree(source[0], directory); target = tmp_path/'target'
    manifest = json.loads((directory/source[2]).read_bytes()); original = producer.lifecycle.advance_leaf_lifecycle; calls = []
    def changed(**kwargs):
        result = original(**kwargs); calls.append(1)
        if len(calls) == 1:
            file = directory/manifest['samples'][5]['result_sha256']; file.write_bytes(file.read_bytes() + b' ')
        return result
    monkeypatch.setattr(producer.lifecycle, 'advance_leaf_lifecycle', changed); raw = canonical(appearance_program())
    with pytest.raises(producer.LeafLifecycleArtifactHold):
        producer.produce_leaf_lifecycle_artifact(target, source[1], stem_directory=directory, appearance_program_raw=raw, management_raw=canonical(management(raw)))
    assert completed_roots(target) == set()


@pytest.mark.parametrize('target', ['selected', 'unselected', 'appearance', 'preparation', 'initial', 'management-mode', 'parent', 'directory'])
def test_late_changes_before_frame_return_are_not_hidden_by_projection(artifacts, tmp_path, monkeypatch, target):
    artifact = artifacts[0]; directory = tmp_path/'late'; shutil.copytree(artifact[0], directory)
    manifest = reader.read_leaf_lifecycle_manifest(directory, artifact[1], artifact[2]); original = reader._frame_data; calls = []
    def changed(*args, **kwargs):
        result = original(*args, **kwargs); calls.append(1)
        if len(calls) == 1:
            if target == 'directory':
                held = tmp_path/'held'; directory.rename(held); shutil.copytree(held, directory)
            else:
                if target == 'selected': digest = manifest['samples'][0]['result_sha256']
                elif target == 'unselected': digest = manifest['samples'][5]['result_sha256']
                elif target == 'parent':
                    parent = json.loads((directory/manifest['stem_artifact_sha256']).read_bytes()); digest = parent['samples'][5]['result_sha256']
                else: digest = manifest[{'appearance': 'appearance_program_sha256', 'preparation': 'preparation_sha256',
                                        'initial': 'initial_state_sha256', 'management-mode': 'management_program_sha256'}[target]]
                file = directory/digest
                if target == 'management-mode': file.chmod(0o600)
                else: file.write_bytes(file.read_bytes() + b' ')
        return result
    monkeypatch.setattr(reader, '_frame_data', changed)
    with pytest.raises(reader.LeafLifecycleReadHold): reader.read_leaf_lifecycle_frame(directory, artifact[1], artifact[2], index=0)


def test_only_lifecycle_producer_advances_and_database_cli_are_never_called(source, tmp_path, monkeypatch):
    import psycopg
    from app.job_store import JobStore
    from app import crop_leaf_population_artifact_producer as old_producer
    from app import crop_leaf_population as population
    calls = []; original = producer.lifecycle.advance_leaf_lifecycle
    def observed(**kwargs): calls.append(1); return original(**kwargs)
    def forbidden(*args, **kwargs): raise AssertionError('wrong calculation/DB/CLI boundary')
    monkeypatch.setattr(producer.lifecycle, 'advance_leaf_lifecycle', observed)
    for module, name in [(original_producer, 'produce_leaf_appearance_artifact'), (old_producer, 'produce_leaf_population_artifact'),
                          (population, 'advance_leaf_population'), (JobStore, 'connect'), (psycopg, 'connect'),
                          (subprocess, 'run'), (subprocess, 'Popen')]: monkeypatch.setattr(module, name, forbidden)
    raw = canonical(appearance_program()); directory = tmp_path/'only-producer'
    root = producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0],
                                                   appearance_program_raw=raw, management_raw=canonical(management(raw)))
    assert len(calls) == 12
    reader.read_leaf_lifecycle_manifest(directory, source[1], root)
    for index in range(12): reader.read_leaf_lifecycle_frame(directory, source[1], root, index=index)
    assert len(calls) == 12


def test_fractional_removals_preserve_independent_47ages_areas_and36sums(source, tmp_path):
    p = appearance_program(); raw = canonical(p)
    prepared = producer.preparation.prepare_leaf_lifecycle_program(source[0], source[1], appearance_program_raw=raw, management_raw=canonical(management(raw)))
    births = prepared['lifecycle_initialization']['births']; records = [removal('declared-leaf-0', Fraction(37, 5))]
    records += [removal(b['leaf_id'], fraction(b['emerged_elapsed_seconds_exact']) + Fraction(1, 3), 'new-' + str(i)) for i, b in enumerate(births)]
    directory = tmp_path/'independent'; root = producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0],
        appearance_program_raw=raw, management_raw=canonical(management(raw, records)))
    declared = {x['initialization']['clock_state']['leaf_id']: (x['initialization']['clock_state'], x['initialization']) for x in p['initialization']['initial_inventory']['leaves']}
    for b in births:
        declared[b['leaf_id']] = ({'at_elapsed_seconds_exact': b['emerged_elapsed_seconds_exact'],
                                  'age_exact': {'numerator': '0', 'denominator': '1', 'unit': 'degC_day'}, 'base_temperature': b['base_temperature']}, b)
    checks = 0
    for index in range(12):
        frame = reader.read_leaf_lifecycle_frame(directory, source[1], root, index=index); live = []; retired = []
        for kind, collection in [('active', frame['active_leaves']), ('removed', frame['removed_leaves'])]:
            for item in collection:
                clock, profile = declared[item['leaf_id']]; stop = fraction(frame['at_elapsed_seconds_exact'] if kind == 'active' else item['last_at_elapsed_seconds_exact'])
                begin = fraction(clock['at_elapsed_seconds_exact']); age = fraction(clock['age_exact'])
                for s in prepared['forcing']:
                    start = max(begin, fraction(s['start_elapsed_seconds_exact'])); end = min(stop, fraction(s['end_elapsed_seconds_exact']))
                    if end > start: age += (Fraction.from_float(float(s['air_temperature']['value'])) - Fraction.from_float(float(clock['base_temperature']['value']))) * (end - start) / 86400
                expected_area = reference_area(age, profile)
                assert fraction(item['age_exact']) == age and item['area']['value'] == pytest.approx(expected_area, rel=1e-12)
                (live if kind == 'active' else retired).append(expected_area); checks += 1
        for name, values in [('active_leaf_area', live), ('removed_leaf_area', retired), ('last_tracked_leaf_area', live + retired)]:
            assert frame[name]['value'] == pytest.approx(sum(values), rel=1e-12)
    assert checks == 47


def test_fresh_reader_imports_only_typed_readers_and_never_grows_connects_or_writes(artifacts):
    artifact = artifacts[0]
    script = r'''
import importlib.abc,json,os,subprocess,sys
sys.path.insert(0,sys.argv[1]);directory=sys.argv[2];root=sys.argv[3]
allowed={'crop_leaf_lifecycle_artifact_reader','crop_leaf_lifecycle_program','crop_leaf_appearance_artifact_reader',
'crop_leaf_appearance_program','crop_leaf_population_artifact_reader','crop_leaf_artifact_reader',
'crop_morphology_artifact_io','crop_morphology_artifact_reader','crop_rational_morphology_artifact_reader'}
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self,fullname,path=None,target=None):
  if fullname.startswith('app.crop_')and fullname.rsplit('.',1)[-1]not in allowed:raise AssertionError('growth import '+fullname)
sys.meta_path.insert(0,Block())
import psycopg
from app.content_access import ContentAccess
attempts=[]
def forbidden(*a,**k):attempts.append(1);raise AssertionError('DB/CLI/write forbidden')
psycopg.connect=subprocess.run=subprocess.Popen=forbidden
def audit(event,args):
 if event=='open' and type(args[2])is int and args[2]&(os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):forbidden()
 if event in {'subprocess.Popen','os.system','os.posix_spawn','os.fork','socket.connect'}:forbidden()
sys.addaudithook(audit)
from app.job_store import JobStore
JobStore.connect=forbidden
from app import crop_leaf_lifecycle_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyBlobStore
MorphologyBlobStore.put=forbidden;access=ContentAccess(os.getuid(),os.getgid());before=len(os.listdir('/proc/self/fd'))
m=reader.read_leaf_lifecycle_manifest(directory,access,root);frames=[]
for i in range(len(m['samples'])):frames.append(reader.read_leaf_lifecycle_frame(directory,access,root,index=i))
assert len(frames)==12 and sum(len(f['active_leaves'])for f in frames)==47 and not attempts
assert before==len(os.listdir('/proc/self/fd'))
print(json.dumps({'passed':True,'frames':12,'areas':47,'numerical_imports':0,'DB_CLI_writes':0,'FD_preserved':True,'frame_data':frames}))
'''
    before = snapshot(artifact[0]); env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
    value = subprocess.run([sys.executable, '-B', '-c', script, str(Path(__file__).resolve().parents[1]), str(artifact[0]), artifact[2]],
                           env=env, capture_output=True, text=True, timeout=45)
    assert value.returncode == 0, value.stderr
    result = json.loads(value.stdout)
    assert result['passed'] and result['numerical_imports'] == result['DB_CLI_writes'] == 0
    assert result['frame_data'] == [reader.read_leaf_lifecycle_frame(*artifact, index=i) for i in range(12)]
    assert snapshot(artifact[0]) == before
