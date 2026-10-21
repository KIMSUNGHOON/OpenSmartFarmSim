from copy import deepcopy
from decimal import Decimal,localcontext
from hashlib import sha256
import json
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_leaf_artifact_producer as producer
from app.crop_leaf_artifact_reader import read_leaf_area_manifest,read_leaf_area_frame
from app.crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.content_access import ContentAccess


ROOT=Path(__file__).resolve().parents[2]
PUBLIC=ROOT/'web/public/morphology-rational-replay'
PROGRAM=(ROOT/'fixtures/crop-leaf-area-software-program-v1.json').read_bytes()


@pytest.fixture(scope='module')
def stem(tmp_path_factory):
    directory=tmp_path_factory.mktemp('stem-original')/'blobs';access=ContentAccess(os.getuid(),os.getgid())
    digest=produce_rational_morphology_artifact(directory,access,program_raw=(PUBLIC/'input.json').read_bytes())
    assert digest=='436ed27cde92465c4aad93e1fc0ac52bc03027861b22fd80b15e80683dac0e4a'
    return directory,access


def produce(tmp_path,stem,raw=PROGRAM):
    directory=tmp_path/'leaf-blobs';source,access=stem
    root=producer.produce_leaf_area_artifact(directory,access,stem_directory=source,program_raw=raw)
    return directory,access,root


def test_actual_producer_all_original_stem_frames_and_36_independent_leaf_areas(tmp_path,stem,monkeypatch):
    original={p.name:sha256(p.read_bytes()).hexdigest() for p in stem[0].iterdir()};calls=[]
    advance=producer.inventory.advance_leaf_inventory
    def actual(**kw):calls.append(kw['inputs']['input_id']);return advance(**kw)
    monkeypatch.setattr(producer.inventory,'advance_leaf_inventory',actual)
    directory,access,root=produce(tmp_path,stem);assert len(calls)==12
    def forbidden(**_):raise AssertionError('reader recomputed leaf growth')
    monkeypatch.setattr(producer.inventory,'advance_leaf_inventory',forbidden)
    manifest=read_leaf_area_manifest(directory,access,root);assert len(manifest['samples'])==12
    program=json.loads(PROGRAM)
    with localcontext() as c:
        c.prec=100
        for index in range(12):
            frame=read_leaf_area_frame(directory,access,root,index=index)
            assert producer._canonical(frame['stem'])==(PUBLIC/f'frame-{index}.json').read_bytes()
            assert frame['at']==frame['stem']['at'] and frame['artifact_sha256']==root and frame['tracked_leaf_count']==3
            expected=[]
            for i,leaf in enumerate(frame['leaves']):
                values=program['initialization']['leaves'][i]['initialization']['curve']['values']
                m,k,tm=(Decimal.from_float(float(values[key]['value'])) for key in ('maximum_area','steepness','inflection_age'))
                age=Decimal(17)*Decimal(index+1)/12;area=m/(1+(-k*(age-tm)).exp());expected.append(area)
                assert leaf['area']['value']==pytest.approx(float(area),rel=1e-12,abs=0)
                assert leaf['attachment_internode_id'] in {n['internode_id'] for n in frame['stem']['internodes']}
            assert frame['tracked_leaf_area']['value']==pytest.approx(float(sum(expected)),rel=1e-12,abs=0)
    assert {p.name:sha256(p.read_bytes()).hexdigest() for p in stem[0].iterdir()}==original


@pytest.mark.parametrize('change',['unknown-attachment','wrong-origin','rights','stem-pin','normalization','display','extra'])
def test_unsupported_programs_never_publish_completed_leaf_root(tmp_path,stem,change):
    p=json.loads(PROGRAM)
    if change=='unknown-attachment':p['initialization']['leaves'][0]['attachment_internode_id']='not-in-stored-stem'
    elif change=='wrong-origin':p['initialization']['time_origin_utc']='2026-10-02T00:00:00Z'
    elif change=='rights':p['rights']['use']=False
    elif change=='stem-pin':p['stem']['program_sha256']='0'*64
    elif change=='normalization':p['initialization']['leaves'][0]['initialization']['normalization']='automatic'
    elif change=='display':p['display_policy']['leaf_count']='predicted'
    else:p['cultivar']='unreviewed'
    with pytest.raises(MorphologyArtifactHold):produce(tmp_path,stem,producer._canonical(p))


@pytest.mark.parametrize('index',[-1,12,True,.5])
def test_explicit_frame_index(tmp_path,stem,index):
    directory,access,root=produce(tmp_path,stem)
    with pytest.raises(MorphologyArtifactHold):read_leaf_area_frame(directory,access,root,index=index)


def test_payload_and_schema_tamper_hold(tmp_path,stem):
    directory,access,root=produce(tmp_path,stem);m=read_leaf_area_manifest(directory,access,root)
    path=directory/m['samples'][0]['payload_sha256'];path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(MorphologyArtifactHold):read_leaf_area_frame(directory,access,root,index=0)
    with MorphologyBlobStore(directory,access,write=True) as store:
        forged={**m,'schema_version':'unreviewed-future'};bad=store.put(producer._canonical(forged),maximum=2*1024**2)
    with pytest.raises(MorphologyArtifactHold):read_leaf_area_manifest(directory,access,bad)


def test_rehashed_projection_must_still_equal_original_numeric_result(tmp_path,stem):
    directory,access,root=produce(tmp_path,stem);m=read_leaf_area_manifest(directory,access,root)
    with MorphologyBlobStore(directory,access,write=True) as store:
        raw=store.get(m['samples'][0]['payload_sha256'],maximum=2*1024**2);payload=json.loads(raw)
        payload['leaves'][0]['area']['value']*=2;raw=producer._canonical(payload)
        m['samples'][0]['payload_sha256']=store.put(raw,maximum=2*1024**2);m['samples'][0]['payload_bytes']=len(raw)
        forged=store.put(producer._canonical(m),maximum=2*1024**2)
    with pytest.raises(MorphologyArtifactHold):read_leaf_area_frame(directory,access,forged,index=0)


def test_late_source_change_has_no_leaf_completion_root(tmp_path,stem,monkeypatch):
    original=producer._code_pins;calls=[]
    def changed():
        calls.append(1);value=original()
        if len(calls)>2:value[next(iter(value))]='0'*64
        return value
    monkeypatch.setattr(producer,'_code_pins',changed)
    with pytest.raises(MorphologyArtifactHold,match='CODE_HOLD'):produce(tmp_path,stem)
    for p in (tmp_path/'leaf-blobs').iterdir():
        assert json.loads(p.read_bytes()).get('schema_version')!='leaf-area-research-artifact-v1'


def test_fresh_reader_original_bytes_no_growth_imports_or_SQL(tmp_path,stem):
    directory,access,root=produce(tmp_path,stem);expected=[]
    for i in range(12):expected.append(sha256(producer._canonical(read_leaf_area_frame(directory,access,root,index=i))).hexdigest())
    config=tmp_path/'fresh.private.json';config.write_text(json.dumps({'directory':str(directory),'root':root,'expected':expected}));config.chmod(0o600)
    child=subprocess.run([sys.executable,'-B',str(Path(__file__).with_name('leaf_artifact_fresh.py')),str(config)],capture_output=True,text=True,timeout=30)
    assert child.returncode==0,child.stdout+child.stderr
    proof=json.loads(child.stdout);assert proof['frames']==12 and proof['growth_imports']==[] and not any(proof['calls'].values())


def exporter():
    spec=importlib.util.spec_from_file_location('export_leaf',ROOT/'research/export-leaf-area-replay.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module.export


def test_export_original_bytes_and_separate_stem_inputs(tmp_path,stem):
    directory,access,root=produce(tmp_path,stem);out=tmp_path/'public';result=exporter()(directory,root,out)
    assert result['frames']==12 and result['public_files']==17 and sha256((out/'index.json').read_bytes()).hexdigest()==result['index_sha256']
    assert (out/'stem-root.json').read_bytes()==(PUBLIC/'root.json').read_bytes()
    assert (out/'stem-input.json').read_bytes()==(PUBLIC/'input.json').read_bytes()
    for i in range(12):assert (out/f'frame-{i}.json').read_bytes()==producer._canonical(read_leaf_area_frame(directory,access,root,index=i))


@pytest.mark.parametrize('owner',['leaf','stem'])
def test_export_requires_both_redistribution_declarations(tmp_path,stem,owner):
    p=json.loads(PROGRAM)
    if owner=='leaf':p['rights']['redistribute']=False
    else:
        old=json.loads((PUBLIC/'input.json').read_bytes());old['rights']['redistribute']=False;raw=producer._canonical(old)
        source=tmp_path/'restricted-stem';digest=produce_rational_morphology_artifact(source,stem[1],program_raw=raw)
        stem=(source,stem[1]);p['stem']={'artifact_sha256':digest,'program_sha256':sha256(raw).hexdigest()}
    directory,access,root=produce(tmp_path,stem,producer._canonical(p));out=tmp_path/'not-published'
    with pytest.raises(MorphologyArtifactHold,match='RIGHTS_HOLD'):exporter()(directory,root,out)
    assert not out.exists()
