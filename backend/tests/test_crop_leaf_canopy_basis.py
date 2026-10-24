from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from app import crop_leaf_canopy_basis as basis
from app import crop_leaf_lifecycle_artifact_reader as reader
from app import crop_leaf_lifecycle_artifact_producer as producer
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from test_crop_leaf_lifecycle_artifact import artifacts
from test_crop_leaf_lifecycle_preparation import management, removal
from test_crop_stored_shoot_leaf_birth_inputs import source, canonical, snapshot, fraction


def inputs(artifact, index=0, area=0.5):
    return {'schema_version': 'leaf-canopy-basis-input-v1', 'input_id': 'software-floor-basis',
            'origin': 'synthetic', 'evidence_level': 'assumed', 'evidence_id': 'own-synthetic-footprint',
            'artifact_sha256': artifact[2], 'index': index, 'floor_area': {'value': area, 'unit': 'm2_floor'}}


def calculate(artifact, value=None):
    return basis.calculate_stored_leaf_canopy_basis(*artifact[:2], inputs=inputs(artifact) if value is None else value)


@pytest.fixture(scope='module')
def variants(artifacts, source, tmp_path_factory):
    raw = artifacts[2]
    prepared = producer.preparation.prepare_leaf_lifecycle_program(source[0], source[1],
        appearance_program_raw=raw, management_raw=canonical(management(raw)))
    initialization = prepared['lifecycle_initialization']
    initial = initialization['population_state']['initial_inventory_state']['leaves']
    births = initialization['births']
    partial = [removal(initial[0]['state']['clock_state']['leaf_id'], 0, 'remove-initial'),
               removal(births[0]['leaf_id'], fraction(births[0]['emerged_elapsed_seconds_exact']), 'remove-new')]
    empty = [removal(r['state']['clock_state']['leaf_id'], 0, 'remove-' + str(i)) for i, r in enumerate(initial)]
    empty += [removal(r['leaf_id'], fraction(r['emerged_elapsed_seconds_exact']), 'new-' + str(i)) for i, r in enumerate(births)]
    result = [artifacts[0]]
    for name, records in [('removed', partial), ('empty', empty)]:
        directory = tmp_path_factory.mktemp('canopy-' + name) / 'blobs'
        root = producer.produce_leaf_lifecycle_artifact(directory, source[1], stem_directory=source[0],
            appearance_program_raw=raw, management_raw=canonical(management(raw, records)))
        result.append((directory, source[1], root))
    return result


@pytest.mark.parametrize('scenario', [0, 1])
def test_original12_frames_active_area_exact_clock_and_independent_floor_conversion(variants, scenario):
    artifact = variants[scenario]; original_files = snapshot(artifact[0])
    for index in range(12):
        frame = reader.read_leaf_lifecycle_frame(*artifact, index=index)
        for floor in (0.5, 2.0):
            value = inputs(artifact, index, floor); before = deepcopy(value); result = calculate(artifact, value)
            assert result['schema_version'] == basis.VERSION
            assert result['scope'] == 'software_research_only' and result['gates'] == 'not_assessed'
            assert result['claim_scope'] == 'synthetic_tracked_leaf_lai_math_only'
            assert result['canopy_use'] == 'tracked_inventory_comparison_only'
            assert result['inputs'] == before and value == before
            assert result['input_sha256'] == sha256(canonical(before)).hexdigest()
            assert result['code_sha256'] == sha256(Path(basis.__file__).read_bytes()).hexdigest()
            assert result['reader_code_sha256'] == sha256(Path(reader.__file__).read_bytes()).hexdigest()
            for key in ('artifact_sha256', 'result_sha256', 'input_sha256', 'appearance_program_sha256',
                        'management_program_sha256', 'preparation_sha256'):
                assert result['source'][key] == frame[key]
            for key in ('index', 'at', 'time_origin_utc', 'at_elapsed_seconds_exact', 'active_leaf_count',
                        'removed_leaf_count', 'pending_leaf_count', 'active_leaf_area'):
                assert result[key] == frame[key]
            for kind in ('active', 'removed', 'pending'):
                assert result[kind + '_leaf_ids'] == [r['leaf_id'] for r in frame[kind + '_leaves']]
            expected = float(Fraction(frame['active_leaf_area']['value']) / Fraction(floor))
            assert result['tracked_leaf_area_index'] == {'value': expected, 'unit': 'm2_leaf/m2_floor'}
            result['inputs']['floor_area']['value'] = 777
            assert value == before and calculate(artifact, value)['inputs'] == before
    assert snapshot(artifact[0]) == original_files


@pytest.mark.parametrize('value', [True, False, 0, -1, None, '1', float('nan'), float('inf'),
                                  -float('inf'), 10**400, sys.float_info.min / 2])
def test_invalid_floor_never_reads_source(artifacts, monkeypatch, value):
    def forbidden(*args, **kwargs): raise AssertionError('source must not be read')
    monkeypatch.setattr(reader, 'read_leaf_lifecycle_frame', forbidden)
    value = inputs(artifacts[0], area=value)
    with pytest.raises(basis.LeafCanopyBasisHold): calculate(artifacts[0], value)


@pytest.mark.parametrize('change', [
    lambda p: p.pop('floor_area'), lambda p: p.update(extra=1),
    lambda p: p.update(origin='reference_observation'), lambda p: p.update(evidence_level='measured'),
    lambda p: p.update(evidence_id=''), lambda p: p.update(input_id='a' * 201),
    lambda p: p.update(schema_version='leaf-canopy-basis-input-v2'),
    lambda p: p['floor_area'].update(unit='m2_leaf'), lambda p: p['floor_area'].update(extra=1),
    lambda p: p.update(artifact_sha256='A' * 64), lambda p: p.update(index=True),
    lambda p: p.update(index=-1), lambda p: p.update(index=0.0), lambda p: p.update(index=512),
    lambda p: p.update(density={'value': 2, 'unit': 'shoots/m2_floor'}),
    lambda p: p.update(coverage='complete_physical_canopy')])
def test_closed_synthetic_basis_has_no_implicit_replication_or_approval(artifacts, change):
    value = inputs(artifacts[0]); change(value)
    with pytest.raises(basis.LeafCanopyBasisHold): calculate(artifacts[0], value)


@pytest.mark.parametrize('area', [sys.float_info.max, sys.float_info.min])
def test_positive_area_division_out_of_normal_range_is_held(artifacts, monkeypatch, area):
    original = reader.read_leaf_lifecycle_frame
    def extreme(*args, **kwargs):
        frame = original(*args, **kwargs)
        frame['active_leaf_area']['value'] = sys.float_info.max if area == sys.float_info.min else sys.float_info.min
        return frame
    monkeypatch.setattr(reader, 'read_leaf_lifecycle_frame', extreme)
    with pytest.raises(basis.LeafCanopyBasisHold, match='NUMERIC_HOLD'):
        calculate(artifacts[0], inputs(artifacts[0], area=area))


def test_empty_current_inventory_has_zero_lai_no_removed_or_pending_area(variants):
    artifact = variants[2]; before = snapshot(artifact[0])
    for index in range(12):
        result = calculate(artifact, inputs(artifact, index))
        assert result['tracked_leaf_area_index'] == {'value': 0.0, 'unit': 'm2_leaf/m2_floor'}
        assert result['active_leaf_ids'] == [] and result['active_leaf_count'] == 0
        assert result['removed_leaf_count'] + result['pending_leaf_count'] == 5
    assert snapshot(artifact[0]) == before


def test_original_reader_storage_hold_is_preserved(artifacts, monkeypatch):
    def denied(*args, **kwargs): raise MorphologyArtifactHold('STORAGE_HOLD: denied')
    monkeypatch.setattr(reader, 'read_leaf_lifecycle_frame', denied)
    with pytest.raises(basis.LeafCanopyBasisHold, match='STORAGE_HOLD'): calculate(artifacts[0])


def test_actual_corrupt_source_no_replacement_result(artifacts, tmp_path):
    artifact = artifacts[0]; path = tmp_path / 'corrupt'; shutil.copytree(artifact[0], path)
    blob = path / artifact[2]; blob.write_bytes(blob.read_bytes() + b' ')
    with pytest.raises(basis.LeafCanopyBasisHold, match='HASH_HOLD'):
        calculate((path, artifact[1], artifact[2]))


def test_floor_and_source_selection_change_input_identity(artifacts):
    artifact = artifacts[0]
    results = [calculate(artifact, inputs(artifact, index, floor)) for index, floor in [(0, 0.5), (0, 2.0), (1, 0.5)]]
    assert len({r['input_sha256'] for r in results}) == 3
    assert results[0]['source'] == results[1]['source']
    assert results[0]['source']['result_sha256'] != results[2]['source']['result_sha256']


@pytest.mark.parametrize('floor', [0.3, 7, 1e-100, 1e100])
def test_non_power_of_two_and_wide_scale_floors_round_from_independent_exact_ratio(artifacts, floor):
    artifact = artifacts[0]; original = reader.read_leaf_lifecycle_frame(*artifact, index=0)
    expected = float(Fraction(original['active_leaf_area']['value']) / Fraction(float(floor)))
    result = calculate(artifact, inputs(artifact, area=floor))
    assert result['tracked_leaf_area_index']['value'] == expected
    assert result['inputs']['floor_area']['value'] == floor


def test_caller_mutation_during_read_does_not_change_captured_input_or_source(artifacts, monkeypatch):
    artifact = artifacts[0]; value = inputs(artifact); captured = deepcopy(value)
    original = reader.read_leaf_lifecycle_frame
    def changed(*args, **kwargs):
        value['floor_area']['value'] = 777; value['index'] = 1
        return original(*args, **kwargs)
    monkeypatch.setattr(reader, 'read_leaf_lifecycle_frame', changed)
    result = calculate(artifact, value)
    assert result['inputs'] == captured and result['index'] == captured['index']
    assert result['input_sha256'] == sha256(canonical(captured)).hexdigest()


FRESH_PROBE = r'''
import importlib.abc, json, os, pathlib, subprocess, sys
from fractions import Fraction
allowed = {'crop_leaf_canopy_basis', 'crop_leaf_appearance_artifact_reader', 'crop_leaf_appearance_program',
 'crop_leaf_artifact_reader', 'crop_leaf_lifecycle_artifact_reader', 'crop_leaf_lifecycle_program',
 'crop_leaf_population_artifact_reader', 'crop_morphology_artifact_io', 'crop_morphology_artifact_reader',
 'crop_rational_morphology_artifact_reader'}
attempts = []
def forbidden(*args, **kwargs):
 attempts.append(1); raise AssertionError('growth/DB/CLI/network/write forbidden')
class Block(importlib.abc.MetaPathFinder):
 def find_spec(self, fullname, path=None, target=None):
  if fullname.startswith('app.crop_') and fullname.rsplit('.', 1)[-1] not in allowed: forbidden()
sys.meta_path.insert(0, Block())
import psycopg
psycopg.connect = forbidden; subprocess.Popen = forbidden; subprocess.run = forbidden
def audit(event, args):
 if event == 'open' and ((isinstance(args[1], str) and any(c in args[1] for c in 'wax+')) or
   (isinstance(args[2], int) and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))): forbidden()
 if event in {'os.mkdir', 'os.remove', 'os.rmdir', 'os.rename', 'subprocess.Popen', 'os.system',
              'os.posix_spawn', 'os.fork', 'socket.connect'}: forbidden()
sys.addaudithook(audit)
from app.crop_leaf_canopy_basis import calculate_stored_leaf_canopy_basis
from app.content_access import ContentAccess
fds = len(os.listdir('/proc/self/fd')); rows = []
for directory, root in zip(sys.argv[1::2], sys.argv[2::2], strict=True):
 directory = pathlib.Path(directory); manifest = json.loads((directory/root).read_bytes())
 for index, descriptor in enumerate(manifest['samples']):
  original = json.loads((directory/descriptor['result_sha256']).read_bytes())
  for floor in (0.5, 2.0):
   inputs = {'schema_version': 'leaf-canopy-basis-input-v1', 'input_id': 'software-floor-basis',
    'origin': 'synthetic', 'evidence_level': 'assumed', 'evidence_id': 'own-synthetic-footprint',
    'artifact_sha256': root, 'index': index, 'floor_area': {'value': floor, 'unit': 'm2_floor'}}
   value = calculate_stored_leaf_canopy_basis(directory, ContentAccess(os.getuid(), os.getgid()), inputs=inputs)
   assert value['active_leaf_area'] == original['active_leaf_area']
   assert value['at'] == descriptor['at'] and value['time_origin_utc'] == original['time_origin_utc']
   assert value['at_elapsed_seconds_exact'] == original['at_elapsed_seconds_exact']
   assert value['source']['result_sha256'] == descriptor['result_sha256']
   for kind in ('active', 'removed', 'pending'):
    assert value[kind + '_leaf_ids'] == original[kind + '_leaf_ids']
   assert value['tracked_leaf_area_index']['value'] == float(Fraction(original['active_leaf_area']['value']) / Fraction(floor))
   rows.append(value)
assert rows and not attempts and fds == len(os.listdir('/proc/self/fd'))
assert {name.rsplit('.', 1)[-1] for name in sys.modules if name.startswith('app.crop_')} <= allowed
print(json.dumps({'passed': True, 'rows': rows, 'growth_imports_DB_CLI_network_writes': 0, 'FD_preserved': True}))
'''


def test_fresh_stored_variants_without_growth_imports_DB_CLI_network_or_writes(variants):
    before = [snapshot(a[0]) for a in variants]
    result = subprocess.run([sys.executable, '-B', '-c', FRESH_PROBE,
        *[str(v) for a in variants for v in (a[0], a[2])]],
        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    proof = json.loads(result.stdout)
    assert proof['passed'] and len(proof['rows']) == 72
    assert before == [snapshot(a[0]) for a in variants]
