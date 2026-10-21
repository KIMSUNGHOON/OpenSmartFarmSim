from copy import deepcopy
from hashlib import sha256
import json

import pytest

from app.crop_leaf_population_artifact_reader import read_leaf_population_manifest
from app.crop_morphology_artifact_io import MorphologyArtifactHold,MorphologyBlobStore
from test_crop_leaf_population_artifact_producer import source,produce
from test_crop_leaf_stem_binding import snapshot
from app.crop_morphology_artifact_reader import _canonical


def test_manifest_original_bytes_without_growth_DB_or_writes(source,tmp_path,monkeypatch):
    directory=tmp_path/'population';root=produce(directory,source);before=snapshot(directory)
    with MorphologyBlobStore(directory,source[1]) as store:expected=json.loads(store.get(root,maximum=2*1024**2))
    from app import crop_leaf_population as population,crop_declared_leaf_births as births,crop_rational_leaf_area as leaf
    from app.job_store import JobStore
    import psycopg
    def forbidden(*a,**kw):raise AssertionError('manifest crossed compute/write boundary')
    monkeypatch.setattr(population,'initialize_leaf_population',forbidden);monkeypatch.setattr(population,'normalize_leaf_population_state',forbidden)
    monkeypatch.setattr(population,'advance_leaf_population',forbidden);monkeypatch.setattr(births,'create_declared_leaves',forbidden)
    monkeypatch.setattr(leaf,'initialize_rational_leaf_area',forbidden);monkeypatch.setattr(leaf,'advance_rational_leaf_area',forbidden)
    monkeypatch.setattr(MorphologyBlobStore,'put',forbidden);monkeypatch.setattr(JobStore,'connect',forbidden);monkeypatch.setattr(psycopg,'connect',forbidden)
    assert read_leaf_population_manifest(directory,source[1],root)==expected
    assert sha256(_canonical(expected)).hexdigest()==root and snapshot(directory)==before


@pytest.mark.parametrize('change',['schema','model','extra','source-pin','empty-samples','sample-index','sample-UTC','state-chain','terminal','source-stem','program-rights'])
def test_rehashed_unsupported_manifest_is_rejected(source,tmp_path,change):
    directory=tmp_path/'population';root=produce(directory,source)
    with MorphologyBlobStore(directory,source[1],write=True) as store:
        manifest=json.loads(store.get(root,maximum=2*1024**2));m=deepcopy(manifest)
        if change=='schema':m['schema_version']='unreviewed'
        elif change=='model':m['model_versions']['population']='unreviewed'
        elif change=='extra':m['yield_kg']=100
        elif change=='source-pin':m['code_sha256'][next(iter(m['code_sha256']))]='bad'
        elif change=='empty-samples':m['samples']=[]
        elif change=='sample-index':m['samples'][0]['index']=True
        elif change=='sample-UTC':m['samples'][0]['at']='2026-10-01T02:00:01Z'
        elif change=='state-chain':m['samples'][1]['input_state_sha256']='0'*64
        elif change=='terminal':m['terminal_state_sha256']='0'*64
        elif change=='source-stem':m['stem_artifact_sha256']='0'*64
        elif change=='program-rights':
            p=json.loads(store.get(m['program_sha256'],maximum=2*1024**2));p['rights']['use']=False;raw=_canonical(p)
            m['program_sha256']=store.put(raw,maximum=2*1024**2);m['program_bytes']=len(raw);m['program_rights']=p['rights']
        forged=store.put(_canonical(m),maximum=2*1024**2)
    with pytest.raises(MorphologyArtifactHold):read_leaf_population_manifest(directory,source[1],forged)
