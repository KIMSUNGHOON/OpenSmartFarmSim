from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest

from app import crop_leaf_funded_birth_artifact_producer as producer
from app import crop_leaf_funded_birth_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore
from test_crop_leaf_funded_birth_artifact import ACCESS, calculated_inputs, encoded, profiles

ROOT = Path(__file__).resolve().parents[2]


def exporter():
    spec = importlib.util.spec_from_file_location('funded_leaf_export', ROOT/'research/export-leaf-funded-birth-replay.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


@pytest.fixture(scope='module')
def artifacts(tmp_path_factory, profiles):
    base = tmp_path_factory.mktemp('funded-export'); result = []
    for case in range(6):
        inputs, _ = calculated_inputs(profiles, case)
        inputs['rights'].update(declaration_id='own-public-funded-leaf', revision='public-v1', redistribute=True)
        directory = base/str(case)
        root = producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(inputs), **profiles)
        result.append((directory, root))
    return result


@pytest.mark.parametrize('case', range(6))
def test_exact_original_sources_events_contexts_CP_DTO_notice_and_repeat_output(tmp_path, artifacts, case):
    module = exporter(); directory, root = artifacts[case]; a = tmp_path/'a'; b = tmp_path/'b'
    before = {p.name: p.read_bytes() for p in directory.iterdir()}
    first = module.export(directory, root, a); second = module.export(directory, root, b)
    assert first == second and first['frames'] == 7 and first['events'] == 2
    assert first['public_files'] == 30
    assert {p.name: p.read_bytes() for p in a.iterdir()} == {p.name: p.read_bytes() for p in b.iterdir()}
    index = json.loads((a/'index.json').read_bytes()); m = reader.read_funded_leaf_manifest(directory, ACCESS, root)
    assert index['schema_version'] == 'funded-leaf-public-fixture-v1' and index['source_rights'] == m['source_rights']
    with MorphologyBlobStore(directory, ACCESS) as store:
        for descriptor in index['sources']:
            raw = (a/descriptor['path']).read_bytes()
            assert raw == store.get(descriptor['sha256'], maximum=reader.MAX)
            assert len(raw) == descriptor['bytes'] and sha256(raw).hexdigest() == descriptor['sha256']
        for i, event in enumerate(index['events']):
            for key in ('point', 'context_snapshot'):
                descriptor = event[key]
                assert (a/descriptor['path']).read_bytes() == store.get(m['events'][i][key]['sha256'], maximum=reader.MAX)
        for i, d in enumerate(index['checkpoints']):
            assert (a/d['path']).read_bytes() == store.get(m['samples'][i]['checkpoint_sha256'], maximum=reader.CHECKPOINT_MAX)
            frame = reader.read_funded_leaf_frame(directory, ACCESS, root, index=i)
            assert (a/index['frames'][i]['path']).read_bytes() == encoded(frame)
    assert {p.name: p.read_bytes() for p in directory.iterdir()} == before


def test_private_false_is_rejected_before_output_creation(tmp_path, profiles):
    inputs, _ = calculated_inputs(profiles)
    source = tmp_path/'private'; root = producer.produce_funded_leaf_artifact(source, ACCESS, inputs_raw=encoded(inputs), **profiles)
    before = {p.name: (p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.read_bytes()) for p in source.iterdir()}
    with pytest.raises(MorphologyArtifactHold, match='RIGHTS_HOLD'): exporter().export(source, root, tmp_path/'output')
    assert not (tmp_path/'output').exists()
    assert {p.name: (p.stat().st_mtime_ns, p.stat().st_ctime_ns, p.read_bytes()) for p in source.iterdir()} == before


@pytest.mark.parametrize('target', ['same', 'child', 'parent', 'existing', 'symlink'])
def test_output_paths_cannot_overlap_source_or_existing_paths(tmp_path, artifacts, target):
    directory, root = artifacts[0]
    if target == 'same': output = directory
    elif target == 'child': output = directory/'child'
    elif target == 'parent': output = directory.parent
    elif target == 'existing': output = tmp_path/'existing'; output.mkdir()
    else:
        real = tmp_path/'real'; real.mkdir(); output = tmp_path/'linked'; output.symlink_to(real)
    with pytest.raises((MorphologyArtifactHold, FileExistsError)): exporter().export(directory, root, output)


@pytest.mark.parametrize('kind', ['rights', 'changed_manifest', 'output', 'code'])
def test_late_source_rights_output_and_code_changes_prevent_index(tmp_path, artifacts, monkeypatch, kind):
    module = exporter(); directory, root = artifacts[0]; output = tmp_path/'out'; read = module.reader.read_funded_leaf_manifest; calls = []
    if kind in ('rights', 'changed_manifest'):
        def altered(*a, **k):
            value = read(*a, **k); calls.append(1)
            if len(calls) > 1:
                if kind == 'rights': value['source_rights']['redistribute'] = False
                else: value['input_id'] = 'changed'
            return value
        monkeypatch.setattr(module.reader, 'read_funded_leaf_manifest', altered)
    else:
        verify = module._Output.verify
        def changed(self, written):
            result = verify(self, written)
            if kind == 'output':
                first = self.path/written[0]['path']; first.write_bytes(b'changed')
            else: monkeypatch.setattr(module, 'CODE_SHA256', '0'*64)
            return result
        monkeypatch.setattr(module._Output, 'verify', changed)
    with pytest.raises(MorphologyArtifactHold): module.export(directory, root, output)
    assert not (output/'index.json').exists()


def test_replaced_output_directory_is_rejected_before_another_write(tmp_path, artifacts, monkeypatch):
    module = exporter(); directory, root = artifacts[0]; output = tmp_path/'out'; moved = tmp_path/'original'
    write = module._Output.write; calls = []
    def replaced(self, name, raw):
        calls.append(1)
        if len(calls) == 2:
            self.path.rename(moved); self.path.mkdir(mode=0o750)
        return write(self, name, raw)
    monkeypatch.setattr(module._Output, 'write', replaced)
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(MorphologyArtifactHold, match='STORAGE_HOLD'): module.export(directory, root, output)
    assert list(output.iterdir()) == [] and not (moved/'index.json').exists()
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('name', ['source-inputs.json', '.index.pending'])
def test_write_and_publication_failure_leave_no_index(tmp_path, artifacts, monkeypatch, name):
    module = exporter(); directory, root = artifacts[0]; output = tmp_path/'out'; write = module._Output.write
    def failed(self, current, raw):
        if current == name: raise OSError('injected write failure')
        return write(self, current, raw)
    monkeypatch.setattr(module._Output, 'write', failed)
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(OSError): module.export(directory, root, output)
    assert not (output/'index.json').exists() and len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('boundary', ['minimum', 'maximum'])
def test_original_one_and_result_512_leaf_export_boundaries(tmp_path, profiles, boundary):
    from test_crop_leaf_carbon_stock_artifact import inputs as original_inputs
    program = original_inputs()['program']; count = 4; new_count = 1
    if boundary == 'minimum':
        share = program['leaves'][0]['initial_area']['value']/sum(leaf['initial_area']['value'] for leaf in program['leaves'])
        program['scenario']['climate_state']['canopy_sensible_energy']['value'] *= share; program['leaves'] = program['leaves'][:1]
    else: new_count = 509; count = 1
    inputs, original = calculated_inputs(profiles, steps=(0,), count=count, new_count=new_count, base_program=program)
    inputs['rights'].update(declaration_id='own-public-funded-boundary', revision='public-v1', redistribute=True)
    directory = tmp_path/'source'; root = producer.produce_funded_leaf_artifact(directory, ACCESS, inputs_raw=encoded(inputs), **profiles)
    result = exporter().export(directory, root, tmp_path/'output')
    last = json.loads((tmp_path/'output'/f'frame-{len(original)-1}.json').read_bytes())
    assert len(last['leaves']) == (2 if boundary == 'minimum' else 512)
    assert result['frames'] == len(original)
