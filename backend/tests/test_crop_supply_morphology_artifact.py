"""Actual held-prefix storage/reader faults; no field-validation claim."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil

import pytest

from test_crop_supply_morphology_repeat import (
    current, profiles, prepared, pending, calculated, adopted, trajectory,
    post_pending, post_calculated, successor, repeat_root,
)
from app.content_access import ContentAccess
from app.crop_morphology_artifact_io import MorphologyBlobStore


@pytest.mark.parametrize('index', [True, False, -1, 512, 1., None, '0'])
def test_invalid_frame_indices_fail_before_opening_any_store(index):
    from app import crop_supply_morphology_artifact_reader as reader
    with pytest.raises(ValueError, match='INDEX_HOLD'):
        reader.read_supply_morphology_frame(None, None, None, index=index)


def test_missing_read_store_is_never_created(tmp_path):
    from app import crop_supply_morphology_artifact_reader as reader
    directory = tmp_path / 'missing'
    access = ContentAccess(owner_uid=os.getuid(), reader_gid=os.getgid())
    with pytest.raises(ValueError):
        reader.read_supply_morphology_manifest(directory, access, '0' * 64)
    assert not directory.exists()


def test_reader_code_closure_contains_every_current_model_dependency():
    from app import crop_supply_morphology_artifact_reader as reader
    from app import crop_supply_morphology_repeat_resume as model
    assert set(reader.MODEL_SOURCE_PATHS) == set(model._pins())
    pins = reader._pins()
    assert {name:pins[name] for name in reader.MODEL_SOURCE_PATHS} == model._pins()


@pytest.fixture(scope='module')
def actual_prefix(repeat_root, tmp_path_factory):
    from app import crop_supply_morphology_repeat_resume as model
    from app import crop_supply_morphology_artifact_producer as producer
    context = repeat_root[0]
    checkpoints = [model.start(context)]
    for _ in range(64):
        result = model.advance_chunk(context, checkpoints[-1], 1)
        if result['status'] == 'hold':
            assert result['pending_event'] is not None
            break
        assert result['status'] == 'yielded'
        checkpoints.append(result['checkpoint'])
    else:
        pytest.fail('actual next event was not reached')
    directory = tmp_path_factory.mktemp('actual-stored-prefix') / 'artifact'
    access = ContentAccess(owner_uid=os.getuid(), reader_gid=os.getgid())
    segments = [{'context':context, 'checkpoints':checkpoints}]
    terminal = {'status':'hold', 'hold':result['hold']}
    digest = producer.produce_supply_morphology_artifact(directory, access, segments=segments, terminal=terminal)
    return directory, access, digest, segments, terminal


@pytest.fixture
def replica(actual_prefix, tmp_path):
    source, access, digest, _, _ = actual_prefix
    directory = tmp_path / 'artifact'
    shutil.copytree(source, directory)
    try:
        yield directory, access, digest
    finally:
        shutil.rmtree(directory)


def read_manifest(case):
    from app import crop_supply_morphology_artifact_reader as reader
    return reader.read_supply_morphology_manifest(*case)


def store_root(case, mutate):
    from app import crop_supply_morphology_artifact_reader as reader
    directory, access, digest = case
    with MorphologyBlobStore(directory, access, write=True) as store:
        value = json.loads(store.get(digest, maximum=reader.MAX))
        mutate(value, store)
        return store.put(reader._canonical(value), maximum=reader.MAX)


def test_actual_held_prefix_retains_original_CP_bytes_and_retries_identically(actual_prefix):
    from app import crop_supply_morphology_artifact_reader as reader
    from app import crop_supply_morphology_artifact_producer as producer
    directory, access, digest, segments, terminal = actual_prefix
    before = {p.name:p.read_bytes() for p in directory.iterdir()}
    assert producer.produce_supply_morphology_artifact(directory, access, segments=segments, terminal=terminal) == digest
    manifest = reader.read_supply_morphology_manifest(directory, access, digest)
    assert manifest['terminal'] == terminal and manifest['redistribution_authorized'] is False
    assert len(manifest['frames']) == len(segments[0]['checkpoints'])
    for index, cp in enumerate(segments[0]['checkpoints']):
        frame = reader.read_supply_morphology_frame(directory, access, digest, index=index)
        assert frame['snapshot'] == cp.value['last_confirmed']
        assert (directory / frame['checkpoint_sha256']).read_bytes() == cp._raw
    assert {p.name:p.read_bytes() for p in directory.iterdir()} == before


@pytest.mark.parametrize('mutation', ['scope','gate','R2','reverse','missing','bool_index','completion','rights','redistribution','base','code'])
def test_self_rehashed_root_cannot_change_scope_order_rights_or_completion(replica, mutation):
    from app import crop_supply_morphology_artifact_reader as reader
    def mutate(value, store):
        if mutation == 'scope':value['scope'] = 'production'
        elif mutation == 'gate':value['G0_G4'] = 'approved'
        elif mutation == 'R2':value['R2'] = 'approved'
        elif mutation == 'reverse':value['frames'].reverse()
        elif mutation == 'missing':value['frames'].pop()
        elif mutation == 'bool_index':value['frames'][0]['index'] = False
        elif mutation == 'completion':value['terminal'] = {'status':'completed','hold':None}
        elif mutation == 'rights':value['source_rights']['declaration']['use'] = False
        elif mutation == 'redistribution':value['redistribution_authorized'] = True
        elif mutation == 'base':value['shoot_base_temperature'] += 1.
        else:value['code_sha256'].pop(next(iter(value['code_sha256'])))
    digest = store_root(replica, mutate)
    with pytest.raises(ValueError):
        reader.read_supply_morphology_manifest(replica[0], replica[1], digest)


@pytest.mark.parametrize('mutation', ['state','layout_size','time','counter','prefix','unit','transfer','budget','deficit','scope'])
def test_rehashed_checkpoint_must_still_match_source_state_time_accounts_and_units(replica, mutation):
    from app import crop_supply_morphology_artifact_reader as reader
    def mutate(value, store):
        descriptor = value['segments'][0]['checkpoints'][-1]
        cp = json.loads(store.get(descriptor['sha256'], maximum=reader.CP_MAX))
        if mutation == 'state':cp['last_confirmed']['state'][0] = 0.
        elif mutation == 'layout_size':cp['last_confirmed']['state'].pop()
        elif mutation == 'time':cp['at']['elapsed_seconds_exact']['numerator'] = '0'
        elif mutation == 'counter':cp['branch_steps'] = float(cp['branch_steps'])
        elif mutation == 'prefix':cp['output_prefix_sha256'] = '0' * 64
        elif mutation == 'unit':cp['lifetime_transfers_exact']['indoor_air_temperature_time']['unit'] = 's'
        elif mutation == 'transfer':cp['branch_integrated_transfers']['indoor_air_temperature_time']['value'] += 1.
        elif mutation == 'budget':next(iter(cp['global_ledgers'].values()))['budget_exact']['numerator'] = '-1'
        elif mutation == 'deficit':cp['geometry_diagnostics']['leaf_0']['deficit_exact']['numerator'] = '-1'
        else:cp['scope'] = 'production'
        raw = reader._canonical(cp)
        descriptor.update(sha256=store.put(raw, maximum=reader.CP_MAX), bytes=len(raw))
    digest = store_root(replica, mutate)
    with pytest.raises(ValueError):
        reader.read_supply_morphology_manifest(replica[0], replica[1], digest)


def test_raw_file_tampering_and_current_access_drift_hold(replica):
    from app import crop_supply_morphology_artifact_reader as reader
    directory, access, digest = replica
    manifest = read_manifest(replica)
    target = directory / manifest['segments'][0]['checkpoints'][0]['sha256']
    original = target.read_bytes()
    target.write_bytes(original + b' ')
    with pytest.raises(ValueError):read_manifest(replica)
    target.write_bytes(original)
    target.chmod(0o600)
    with pytest.raises(ValueError):read_manifest(replica)


def test_late_file_policy_change_never_returns_a_successful_response(replica, monkeypatch):
    from app import crop_supply_morphology_artifact_reader as reader
    directory, access, digest = replica
    target = directory / digest
    project = reader.projection.project
    calls = []
    def change_after_projection(*args, **kwargs):
        value = project(*args, **kwargs)
        target.chmod(0o600)
        calls.append(1)
        return value
    monkeypatch.setattr(reader.projection, 'project', change_after_projection)
    with pytest.raises(ValueError):read_manifest(replica)
    assert calls


def test_current_model_byte_drift_never_uses_a_cached_success(replica, monkeypatch):
    from app import crop_supply_morphology_artifact_reader as reader
    original = Path.read_bytes
    target = Path(reader.__file__).resolve().parents[2] / 'backend/app/crop_growth_rates.py'
    def changed(path):
        raw = original(path)
        return raw + b'changed-current-code' if path == target else raw
    monkeypatch.setattr(Path, 'read_bytes', changed)
    with pytest.raises(ValueError, match='CODE_HOLD'):read_manifest(replica)


def test_final_graph_failure_publishes_no_root_and_same_retry_can_complete(actual_prefix, tmp_path, monkeypatch):
    from app import crop_supply_morphology_artifact_reader as reader
    from app import crop_supply_morphology_artifact_producer as producer
    _, access, expected, segments, terminal = actual_prefix
    directory = tmp_path / 'failed-publication'
    load = reader._load
    def failed(*args, **kwargs):raise ValueError('INJECTED_HOLD: final graph validation failed')
    monkeypatch.setattr(reader, '_load', failed)
    with pytest.raises(ValueError):
        producer.produce_supply_morphology_artifact(directory, access, segments=segments, terminal=terminal)
    assert directory.exists() and not (directory / expected).exists()
    for path in directory.iterdir():
        try:
            document = json.loads(path.read_bytes())
        except (ValueError, UnicodeError):
            continue
        if isinstance(document, dict):
            assert document.get('schema_version') != reader.FLAGS['schema_version']
    monkeypatch.setattr(reader, '_load', load)
    assert producer.produce_supply_morphology_artifact(directory, access, segments=segments, terminal=terminal) == expected
