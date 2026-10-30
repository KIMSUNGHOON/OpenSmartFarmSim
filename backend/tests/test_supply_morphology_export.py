"""Export permissions and path policy before exposing any stored fixture."""
from copy import deepcopy
from hashlib import sha256
from importlib.util import spec_from_file_location, module_from_spec
import json
from pathlib import Path
import shutil

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load_exporter():
    spec = spec_from_file_location('supply_morphology_export_test', ROOT / 'research/export-supply-morphology-replay.py')
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grants():
    value = dict.fromkeys(('ownership_asserted','access','store','use','transform','display','redistribute'), True)
    return {'redistribution_authorized':True, 'source_rights':{name:deepcopy(value) for name in ('crop','stem','declaration')}}


@pytest.mark.parametrize('source', ['crop','stem','declaration'])
@pytest.mark.parametrize('permission', ['ownership_asserted','access','store','use','transform','display','redistribute'])
def test_each_original_source_grant_is_required(source, permission):
    exporter = load_exporter()
    value = grants()
    value['source_rights'][source][permission] = False
    with pytest.raises(ValueError, match='RIGHTS_HOLD'):
        exporter._grants(value)


def test_material_redistribution_hold_cannot_be_overridden_by_source_grants():
    exporter = load_exporter()
    value = grants()
    value['redistribution_authorized'] = False
    with pytest.raises(ValueError, match='RIGHTS_HOLD'):
        exporter._grants(value)


def test_explicit_public_grants_are_preserved():
    exporter = load_exporter()
    value = grants()
    before = deepcopy(value)
    exporter._grants(value)
    assert value == before


@pytest.mark.parametrize('kind', ['same','descendant','ancestor','relative','symlink'])
def test_unsafe_output_paths_reject_before_reading_or_creating(tmp_path, kind, monkeypatch):
    exporter = load_exporter()
    source = tmp_path / 'source'
    source.mkdir()
    if kind == 'same':output = source
    elif kind == 'descendant':output = source / 'output'
    elif kind == 'ancestor':output = tmp_path
    elif kind == 'relative':output = Path('relative-output')
    else:
        output = tmp_path / 'link'
        output.symlink_to(source, target_is_directory=True)
    def forbidden(*args, **kwargs):raise AssertionError('unsafe path must fail before source read')
    monkeypatch.setattr(exporter.reader, '_load', forbidden)
    with pytest.raises(ValueError, match='STORAGE_HOLD'):
        exporter.export(source, '0' * 64, output)
    assert list(source.iterdir()) == []


def test_published_fixture_has_only_pinned_original_public_files():
    inventory = json.loads((ROOT / 'research/fixtures/supply-morphology-public-20261030.json').read_bytes())
    directory = ROOT / inventory['directory']
    assert inventory['artifact_sha256'] == '84daf00c44a964f904aa0b78e2c64f44c2753ec97641f23566fdfcc349bf4476'
    assert inventory['index_sha256'] == '94aaced1aff85a349a88ee03cb6dc64dbc653561f674ff371104db2bf407d8fc'
    assert set(inventory['files']) == {path.name for path in directory.iterdir()}
    for name, descriptor in inventory['files'].items():
        raw = (directory / name).read_bytes()
        assert {'sha256':sha256(raw).hexdigest(), 'bytes':len(raw)} == descriptor
    index = json.loads((directory / 'index.json').read_bytes())
    assert len(index['frames']) == 38 and index['sample_scalars'] == 6208
    assert index['G0_G4'] == 'not_assessed' and index['R2'] == 'not_approved'
    assert index['redistribution_authorized'] is True
    assert len(index['blobs']) == 62 and len(inventory['files']) == 101
    assert {d['path'] for d in index['blobs'] + index['frames']} | {'index.json'} == set(inventory['files'])
    assert inventory['files']['root.json']['sha256'] == inventory['artifact_sha256']
    assert inventory['files']['index.json']['sha256'] == inventory['index_sha256']
    for grants in index['source_rights'].values():
        assert all(grants[key] is True for key in ('ownership_asserted','access','store','use','transform','display','redistribute'))


def test_aggregate_export_limit_leaves_no_completed_index(tmp_path, monkeypatch):
    exporter = load_exporter()
    directory = ROOT / 'web/public/supply-morphology-replay/own-public-v1'
    index = json.loads((directory / 'index.json').read_bytes())
    source, output = tmp_path / 'source', tmp_path / 'output'
    source.mkdir(mode=0o750)
    for descriptor in index['blobs']:
        path = source / descriptor['sha256']
        shutil.copyfile(directory / descriptor['path'], path)
        path.chmod(0o640)
    monkeypatch.setattr(exporter, 'MAX_PUBLIC_BYTES', 2 * 1024**2, raising=False)
    with pytest.raises(ValueError, match='CAPACITY_HOLD'):
        exporter.export(source, index['artifact_sha256'], output)
    assert not (output / 'index.json').exists()
    assert sum(path.stat().st_size for path in output.iterdir()) <= 2 * 1024**2
