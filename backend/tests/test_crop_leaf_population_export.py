from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from app.crop_leaf_population_artifact_reader import read_leaf_population_frame
from app.crop_morphology_artifact_reader import _canonical
from app.crop_morphology_artifact_io import MorphologyArtifactHold
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from test_crop_leaf_population_artifact_producer import source,produce,PROGRAM,ROOT
from test_crop_leaf_stem_binding import snapshot


def exporter():
    spec=importlib.util.spec_from_file_location('export_population',ROOT/'research/export-leaf-population-replay.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.export


def test_original_17_files_bytes_binding_rights_and_existing_export_not_overwritten(source,tmp_path):
    directory=tmp_path/'population';root=produce(directory,source);before=snapshot(directory);out=tmp_path/'public'
    result=exporter()(directory,root,out);index=json.loads((out/'index.json').read_bytes())
    assert result['frames']==12 and result['public_files']==17 and index['schema_version']=='leaf-population-public-fixture-v1'
    assert sha256((out/'index.json').read_bytes()).hexdigest()==result['index_sha256']
    assert (out/'input.json').read_bytes()==PROGRAM and (out/'stem-input.json').read_bytes()==(ROOT/'web/public/morphology-rational-replay/input.json').read_bytes()
    assert (out/'stem-root.json').read_bytes()==(ROOT/'web/public/morphology-rational-replay/root.json').read_bytes()
    for i,d in enumerate(index['frames']):
        raw=(out/d['path']).read_bytes();frame=read_leaf_population_frame(directory,source[1],root,index=i)
        assert raw==_canonical(frame) and d['bytes']==len(raw) and d['sha256']==sha256(raw).hexdigest()
        assert d['binding_sha256']==frame['binding_sha256'] and d['at']==frame['at']
    saved={p.name:p.read_bytes() for p in out.iterdir()}
    with pytest.raises(FileExistsError):exporter()(directory,root,out)
    assert {p.name:p.read_bytes() for p in out.iterdir()}==saved and snapshot(directory)==before


@pytest.mark.parametrize('owner',['population','stem'])
def test_both_redistribution_rights_required_before_output_creation(source,tmp_path,owner):
    p=json.loads(PROGRAM)
    if owner=='population':p['rights']['redistribute']=False
    else:
        stem=json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes());stem['rights']['redistribute']=False;raw=_canonical(stem)
        directory=tmp_path/'restricted-stem';root=produce_rational_morphology_artifact(directory,source[1],program_raw=raw)
        source=(directory,source[1],root);p['stem']={'artifact_sha256':root,'program_sha256':sha256(raw).hexdigest()}
    directory=tmp_path/'population';root=produce(directory,source,_canonical(p));out=tmp_path/'not-published'
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):exporter()(directory,root,out)
    assert not out.exists()
