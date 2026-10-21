from copy import deepcopy
from hashlib import sha256
import json
import os
import subprocess
import sys

import pytest

from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame, read_rational_morphology_manifest
from app.crop_rational_shoot_inventory import advance_rational_shoot_internode_inventory
from app.job_store import JobStore
from app.thermal_run_store import _canonical
from test_crop_rational_shoot_inventory import fractional_inputs


def access():
    return ContentAccess(os.getuid(), os.getgid())


def program():
    p = fractional_inputs(); p['segments'][0]['end_utc'] = '2026-10-01T00:00:03Z'
    return {'schema_version': 'morphology-software-program-v2', 'origin': 'synthetic', 'program_id': 'synthetic-rational-morphology',
        'rights': {'declaration_id': 'self-authored-fixture', 'revision': 'r2', 'declared_at_utc': '2026-10-21T17:30:00Z',
            **{k: True for k in ('ownership_asserted', 'access', 'store', 'use', 'transform', 'display', 'redistribute')}},
        'initial_state': p['state'], 'segments': p['segments'],
        'output_times': ['2026-10-01T00:00:01Z', '2026-10-01T00:00:02Z', '2026-10-01T00:00:03Z']}


def produce(directory, p=None):
    return produce_rational_morphology_artifact(directory, access(), program_raw=_canonical(program() if p is None else p))


def test_original_results_exact_births_chain_and_same_root(tmp_path, monkeypatch):
    monkeypatch.setattr(JobStore, 'connect', lambda *a, **k: pytest.fail('DB forbidden'))
    directory = tmp_path / 'artifact'; root = produce(directory); p = program()
    manifest = read_rational_morphology_manifest(directory, access(), root)
    assert manifest['schema_version'] == 'morphology-research-artifact-v2'
    assert sha256(_canonical(manifest)).hexdigest() == root
    state = p['initial_state']; previous = manifest['initial_state_sha256']
    for index, descriptor in enumerate(manifest['samples']):
        assert descriptor['input_state_sha256'] == previous
        segment = {**p['segments'][0], 'start_utc': state['timeline_state']['at'], 'end_utc': descriptor['at']}
        expected = advance_rational_shoot_internode_inventory(inputs={'input_id': sha256(_canonical({
            'program_id': p['program_id'], 'output_at': descriptor['at']})).hexdigest(), 'state': state, 'segments': [segment]})
        with MorphologyBlobStore(directory, access()) as store:
            assert store.get(descriptor['result_sha256'], maximum=2*1024**2) == _canonical(expected)
        frame = read_rational_morphology_frame(directory, access(), root, index=index)
        assert frame['at'] == descriptor['at'] and frame['time_origin_utc'] == p['initial_state']['timeline_state']['started_at']
        assert frame['schema_version'] == 'morphology-replay-frame-v2' and frame['gates'] == 'not_assessed'
        assert len(frame['internodes']) == 6 + 3 * index
        assert frame['tracked_axis_length'] == expected['tracked_axis_length']
        for node, original in zip(frame['internodes'], expected['state']['internodes'], strict=True):
            clock = original['length_state']['clock_state']
            assert node['internode_id'] == clock['internode_id']
            assert node['emerged_elapsed_seconds_exact'] == clock['emerged_elapsed_seconds_exact']
            assert node['age_exact'] == clock['age_exact'] and node['length'] == original['length_state']['length']
            assert 'emerged_at' not in node
        previous = descriptor['state_sha256']; state = expected['state']
    assert manifest['terminal_state_sha256'] == previous
    before = {f.name: (f.stat().st_ino, f.stat().st_mtime_ns, f.read_bytes()) for f in directory.iterdir()}
    assert produce(directory) == root
    assert {f.name: (f.stat().st_ino, f.stat().st_mtime_ns, f.read_bytes()) for f in directory.iterdir()} == before


def test_manifest_versions_pin_actual_calculation_components(tmp_path):
    from app import crop_morphology_thermal_clock as air, crop_internode_length as point
    from app import crop_rational_morphology_clock as clock, crop_rational_internode_length as length
    from app import crop_phytomer_emergence as emergence, crop_shoot_timeline as timeline
    from app import crop_rational_new_internodes as new, crop_rational_shoot_inventory as inventory
    directory = tmp_path / 'artifact'; root = produce(directory)
    manifest = read_rational_morphology_manifest(directory, access(), root)
    assert manifest['model_versions'] == {'whole_second_air': air.AIR_SEGMENT_VERSION,
        'point': point.POINT_VERSION, 'clock': clock.MODEL_VERSION, 'length': length.MODEL_VERSION,
        'emergence': emergence.MODEL_VERSION, 'timeline': timeline.MODEL_VERSION,
        'air_adapter': new.AIR_ADAPTER_VERSION, 'new_internodes': new.MODEL_VERSION, 'inventory': inventory.MODEL_VERSION}


def test_fresh_reader_imports_no_growth_models_or_DB(tmp_path):
    directory = tmp_path / 'artifact'; root = produce(directory)
    expected = read_rational_morphology_frame(directory, access(), root, index=2)
    code = '''import os,sys,json
from pathlib import Path
from app.content_access import ContentAccess
from app.crop_rational_morphology_artifact_reader import read_rational_morphology_frame
from app.job_store import JobStore
JobStore.connect=lambda *a,**k: (_ for _ in ()).throw(AssertionError('DB forbidden'))
names=['crop_rational_shoot_inventory','crop_rational_new_internodes','crop_rational_internode_length','crop_rational_morphology_clock','crop_shoot_inventory','crop_new_internodes','crop_shoot_timeline','crop_phytomer_emergence','crop_internode_length','crop_internode_length_change','crop_morphology_thermal_clock','crop_internode_elongation']
assert all('app.'+name not in sys.modules for name in names)
value=read_rational_morphology_frame(Path(sys.argv[1]),ContentAccess(os.getuid(),os.getgid()),sys.argv[2],index=2)
assert all('app.'+name not in sys.modules for name in names)
print(json.dumps(value,sort_keys=True,separators=(',',':')))
'''
    done = subprocess.run([sys.executable, '-c', code, str(directory), root], capture_output=True, text=True, timeout=10)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout) == expected


@pytest.mark.parametrize('change', ['schema', 'observed', 'display', 'rights-extra', 'clock-unit', 'origin', 'fraction',
    'clock-now', 'zero-length', 'duplicate-output', 'missing-final', 'outputs-cap', 'below-base'])
def test_invalid_program_never_publishes_completed_root(tmp_path, change):
    p = program(); clock = p['initial_state']['internodes'][0]['length_state']['clock_state']
    if change == 'schema': p['schema_version'] = 'morphology-software-program-v1'
    elif change == 'observed': p['origin'] = 'observed'
    elif change == 'display': p['rights']['display'] = False
    elif change == 'rights-extra': p['rights']['approved'] = True
    elif change == 'clock-unit': clock['emerged_elapsed_seconds_exact']['unit'] = 'degC_day'
    elif change == 'origin': clock['time_origin_utc'] = '2026-09-30T00:00:00Z'
    elif change == 'fraction': clock['at_elapsed_seconds_exact'].update(numerator='0', denominator='2')
    elif change == 'clock-now': clock['at_elapsed_seconds_exact']['numerator'] = '1'
    elif change == 'zero-length': p['initial_state']['internodes'][0]['length_state']['length']['value'] = 0
    elif change == 'duplicate-output': p['output_times'][1] = p['output_times'][0]
    elif change == 'missing-final': p['output_times'].pop()
    elif change == 'outputs-cap': p['output_times'] *= 22
    else: p['segments'][0]['air_temperature']['value'] = -1
    directory = tmp_path / 'artifact'
    with pytest.raises(MorphologyArtifactHold): produce(directory, p)
    if directory.exists():
        assert not any(json.loads(f.read_bytes()).get('schema_version') == 'morphology-research-artifact-v2' for f in directory.iterdir())


@pytest.mark.parametrize('change', ['model', 'gate', 'chain', 'terminal', 'code-pins'])
def test_unsupported_or_changed_root_never_returns_frame(tmp_path, change):
    directory = tmp_path / 'artifact'; root = produce(directory)
    manifest = read_rational_morphology_manifest(directory, access(), root)
    if change == 'model': manifest['model_versions']['clock'] = 'unverified'
    elif change == 'gate': manifest['gates'] = 'G2_passed'
    elif change == 'chain': manifest['samples'][1]['input_state_sha256'] = '0' * 64
    elif change == 'terminal': manifest['terminal_state_sha256'] = '0' * 64
    else: manifest['code_sha256'].popitem()
    with MorphologyBlobStore(directory, access(), write=True) as store:
        bad = store.put(_canonical(manifest), maximum=128*1024)
    with pytest.raises(MorphologyArtifactHold): read_rational_morphology_frame(directory, access(), bad, index=2)


@pytest.mark.parametrize('change', ['seconds-unit', 'seconds-reduced', 'time-origin', 'clock-now', 'length-unit', 'extra-output', 'approximate-birth'])
def test_typed_reader_rejects_invalid_result_under_new_hashes(tmp_path, change):
    directory = tmp_path / 'artifact'; root = produce(directory)
    manifest = read_rational_morphology_manifest(directory, access(), root); d = manifest['samples'][-1]
    with MorphologyBlobStore(directory, access(), write=True) as store:
        result = json.loads(store.get(d['result_sha256'], maximum=2*1024**2)); clock = result['state']['internodes'][3]['length_state']['clock_state']
        if change == 'seconds-unit': clock['emerged_elapsed_seconds_exact']['unit'] = 'day'
        elif change == 'seconds-reduced': clock['emerged_elapsed_seconds_exact'].update(numerator='2', denominator='6')
        elif change == 'time-origin': clock['time_origin_utc'] = '2026-09-30T00:00:00Z'
        elif change == 'clock-now': clock['at_elapsed_seconds_exact']['numerator'] = '4'
        elif change == 'length-unit': result['state']['internodes'][0]['length_state']['length']['unit'] = 'cm'
        elif change == 'extra-output': result['yield'] = {'value': 1, 'unit': 'kg'}
        else: clock['emerged_at'] = '2026-10-01T00:00:00Z'
        raw = _canonical(result); d['result_sha256'] = store.put(raw, maximum=2*1024**2); d['result_bytes'] = len(raw)
        d['state_sha256'] = manifest['terminal_state_sha256'] = sha256(_canonical(result['state'])).hexdigest()
        bad = store.put(_canonical(manifest), maximum=128*1024)
    with pytest.raises(MorphologyArtifactHold): read_rational_morphology_frame(directory, access(), bad, index=2)


@pytest.mark.parametrize('index', [True, -1, 3])
def test_index_is_explicit_and_bounded(tmp_path, index):
    directory = tmp_path / 'artifact'; root = produce(directory)
    with pytest.raises(MorphologyArtifactHold): read_rational_morphology_frame(directory, access(), root, index=index)


def test_failed_second_step_has_no_completed_root(tmp_path, monkeypatch):
    from app import crop_rational_morphology_artifact_producer as producer
    original = producer.inventory.advance_rational_shoot_internode_inventory; calls = 0
    def fail(**kwargs):
        nonlocal calls
        calls += 1
        if calls == 2: raise producer.inventory.RationalShootInventoryHold('NUMERIC_HOLD: controlled fixture fault')
        return original(**kwargs)
    monkeypatch.setattr(producer.inventory, 'advance_rational_shoot_internode_inventory', fail)
    directory = tmp_path / 'artifact'
    with pytest.raises(MorphologyArtifactHold): produce(directory)
    assert calls == 2
    assert not any(json.loads(f.read_bytes()).get('schema_version') == 'morphology-research-artifact-v2' for f in directory.iterdir())
