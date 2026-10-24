from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from app import crop_leaf_carbon_stock_artifact_producer as producer
from app import crop_leaf_carbon_stock_artifact_reader as reader
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from test_crop_leaf_carbon_stock_artifact import ACCESS, inputs, encoded, profiles

ROOT = Path(__file__).resolve().parents[2]


def exporter():
    spec = importlib.util.spec_from_file_location('leaf_stock_export', ROOT/'research/export-leaf-carbon-stock-replay.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


@pytest.fixture(scope='module')
def artifacts(tmp_path_factory, profiles):
    out = tmp_path_factory.mktemp('export-sources'); cases = []
    for i in range(6):
        p = inputs(i); p['rights'].update(declaration_id='own-public-leaf-carbon-stock', revision='public-v1', redistribute=True)
        directory = out/str(i); root = producer.produce_leaf_carbon_stock_artifact(directory, ACCESS, inputs_raw=encoded(p), **profiles)
        cases.append((directory, root))
    return cases


@pytest.mark.parametrize('case', range(6))
def test_original_sources_checkpoints_DTOs_rights_notice_and_repeat(artifacts, tmp_path, case):
    directory, root = artifacts[case]; out = tmp_path/'export'; module = exporter()
    result = module.export(directory, root, out); index_raw = (out/'index.json').read_bytes(); index = json.loads(index_raw)
    manifest = reader.read_leaf_carbon_stock_manifest(directory, ACCESS, root)
    assert result == {'artifact_sha256': root, 'index_sha256': sha256(index_raw).hexdigest(), 'frames': 17, 'public_files': 46}
    assert index['source_rights'] == manifest['source_rights'] and index['G0_G4'] == 'not_assessed'
    assert len(index['sources']) == 11 and len(index['checkpoints']) == len(index['frames']) == 17
    assert len(list(out.iterdir())) == 46
    assert (out/'root.json').read_bytes() == (directory/root).read_bytes()
    for d in index['sources']+index['checkpoints']+index['frames']:
        raw = (out/d['path']).read_bytes(); assert len(raw) == d['bytes'] and sha256(raw).hexdigest() == d['sha256']
    for name, d in manifest['sources'].items():
        file = 'NOTICE.txt' if name == 'license_notice' else f'source-{name}.json'
        assert (out/file).read_bytes() == (directory/d['sha256']).read_bytes()
    for i in range(17):
        assert (out/f'checkpoint-{i}.json').read_bytes() == (directory/manifest['samples'][i]['checkpoint_sha256']).read_bytes()
        assert (out/f'frame-{i}.json').read_bytes() == encoded(reader.read_leaf_carbon_stock_frame(directory, ACCESS, root, index=i))
    other = tmp_path/'repeat'; assert module.export(directory, root, other) == result
    assert {p.name:p.read_bytes() for p in out.iterdir()} == {p.name:p.read_bytes() for p in other.iterdir()}
    with pytest.raises(FileExistsError): module.export(directory, root, out)


def test_private_redistribute_false_is_not_promoted(tmp_path, profiles):
    directory = tmp_path/'source'; root = producer.produce_leaf_carbon_stock_artifact(directory, ACCESS, inputs_raw=encoded(inputs(count=1)), **profiles)
    with pytest.raises(MorphologyArtifactHold, match='RIGHTS_HOLD'): exporter().export(directory, root, tmp_path/'denied')
    assert not (tmp_path/'denied').exists()


@pytest.mark.parametrize('grant', ('use', 'display', 'redistribute'))
def test_late_grant_denial_prevents_index(artifacts, tmp_path, monkeypatch, grant):
    module = exporter(); original = module.read_leaf_carbon_stock_manifest; calls = []
    def denied(*args):
        m = deepcopy(original(*args)); calls.append(1)
        if len(calls)>1: m['source_rights'][grant] = False
        return m
    monkeypatch.setattr(module, 'read_leaf_carbon_stock_manifest', denied)
    with pytest.raises(MorphologyArtifactHold): module.export(*artifacts[0], tmp_path/'late')
    assert len(calls) == 2 and not (tmp_path/'late/index.json').exists()


@pytest.mark.parametrize('failure', ('file', 'source', 'source-raw', 'code', 'write', 'publish', 'directory'))
def test_late_mutation_or_write_failure_prevents_completed_index(artifacts, tmp_path, monkeypatch, failure):
    module = exporter(); original = module._written; calls = []; output = tmp_path/'failed'
    artifact = artifacts[0]
    if failure == 'source-raw':
        source = tmp_path/'changed-source'; shutil.copytree(artifact[0], source); artifact = source, artifact[1]
    def changed(out, written, identity):
        calls.append(1)
        if len(calls) == 1:
            if failure == 'file': (out/'frame-0.json').write_bytes(b'{}')
            elif failure == 'source':
                monkeypatch.setattr(module, 'read_leaf_carbon_stock_manifest', lambda *args: (_ for _ in ()).throw(MorphologyArtifactHold('HASH_HOLD')))
            elif failure == 'source-raw':
                manifest = json.loads((artifact[0]/artifact[1]).read_bytes())
                (artifact[0]/manifest['sources']['growth_profile']['sha256']).write_bytes(b'{}')
            elif failure == 'code': module.CODE_SHA256 = '0'*64
            elif failure == 'directory': out.chmod(0o770)
        return original(out, written, identity)
    monkeypatch.setattr(module, '_written', changed)
    if failure == 'write': monkeypatch.setattr(module, '_write', lambda *args: (_ for _ in ()).throw(OSError('write failure')))
    if failure == 'publish': monkeypatch.setattr(module.os, 'replace', lambda *args: (_ for _ in ()).throw(OSError('publish failure')))
    with pytest.raises((MorphologyArtifactHold, OSError)): module.export(*artifact, output)
    assert not (output/'index.json').exists()


def test_output_must_be_new_and_outside_source_or_its_ancestors(artifacts, tmp_path):
    directory, root = artifacts[0]; module = exporter()
    for output in (directory, directory/'child', directory.parent):
        with pytest.raises(MorphologyArtifactHold): module.export(directory, root, output)
    target = tmp_path/'target'; target.mkdir(); link = tmp_path/'link'; link.symlink_to(target, target_is_directory=True)
    with pytest.raises(MorphologyArtifactHold): module.export(directory, root, link)


@pytest.mark.parametrize('count',[1,512])
def test_export_actual_stock_inventory_preserves_vector_and_dynamic_transfers(tmp_path,profiles,count):
    p=inputs(dt=.125,count=1);first=p['program']['leaves'][0]
    total=sum(x['initial_carbon']['value']for x in p['program']['leaves'])
    p['rights'].update(declaration_id='own-public-stock-boundary',redistribute=True)
    p['program']['leaves']=[{**deepcopy(first),'leaf_id':f'export-stock-{i}',
        'initial_carbon':{'value':total/count,'unit':'mg_CH2O/m2_floor'},
        'sink_weight':{'value':float(i%7)if count>1 else 1.,'unit':'1'}}for i in range(count)]
    p['program']['model_floor_area']['value']=count*.25/1.33
    directory=tmp_path/'stock-source';root=producer.produce_leaf_carbon_stock_artifact(directory,ACCESS,inputs_raw=encoded(p),**profiles)
    output=tmp_path/'stock-export';exporter().export(directory,root,output)
    cp=json.loads((output/'checkpoint-1.json').read_bytes());frame=json.loads((output/'frame-1.json').read_bytes())
    assert len(cp['last_confirmed']['state'])==107+3*count and len(cp['integrated_transfers'])==21+3*count
    assert frame['sample']==cp['last_confirmed']and frame['integrated_transfers']==cp['integrated_transfers']
    for i,l in enumerate(frame['leaves']):assert l['carbon']=={'value':cp['last_confirmed']['state'][107+2*count+i],'unit':'mg_CH2O/m2_floor'}
