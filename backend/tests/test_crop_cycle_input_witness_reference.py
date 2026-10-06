from hashlib import sha256
import importlib.util
import hmac
import json
import os
from pathlib import Path

import pytest

from test_crop_cycle_artifact import PROFILES,NOTICE,program

ROOT=Path(__file__).resolve().parents[2]
KEY=b'own-test-only-witness-key-32-bytes!'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


@pytest.fixture(scope='module')
def candidate():return load('own_input_witness',ROOT/'research/crop-cycle-input-witness-reference.py')


@pytest.fixture
def experiment(tmp_path,candidate):
    driver=candidate.driver();path=tmp_path/'run'
    spec=driver.prepare_experiment(path,program=program('empty-entry'),intervals=2,interval_seconds=60,
        profiles=PROFILES,notice_raw=NOTICE)
    return path,spec['spec_sha256']


def test_certified_original_context_is_returned_only_after_all_current_bytes_match(candidate,experiment,monkeypatch):
    path,digest=experiment;before=len(os.listdir('/proc/self/fd'))
    monkeypatch.setattr(candidate.driver().engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('witness called RHS'))
    raw=candidate.certify(path,digest,PROFILES,NOTICE,key=KEY)
    result=candidate.verify(path,digest,PROFILES,NOTICE,raw,key=KEY)
    assert result['context']==json.loads(raw)['payload']['context']
    assert result['context']['manifest']['grid_index_sha256']==sha256(candidate.driver().inputs._canonical(result['context']['index'])).hexdigest()
    assert result['current_blob_bytes_match'] is True and result['rights_or_gate_approval'] is False
    assert result['referenced_bytes']==result['context']['plan']['packet_referenced_bytes']
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',['root','blob','missing','file-symlink','directory-symlink','extra-file'])
def test_unchanged_input_check_rejects_physical_tamper_and_closes_descriptors(candidate,experiment,kind):
    path,digest=experiment;raw=candidate.certify(path,digest,PROFILES,NOTICE,key=KEY)
    root=path/'inputs';target=next(p for p in root.iterdir() if p.name!='root.json')
    if kind=='root':target=root/'root.json'
    if kind in ('root','blob'):
        target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ')
    elif kind=='missing':target.unlink()
    elif kind=='file-symlink':
        outside=path/'outside.json';outside.write_bytes(target.read_bytes());target.unlink();target.symlink_to(outside)
    elif kind=='directory-symlink':
        root.rename(path/'original-inputs');root.symlink_to(path/'original-inputs',target_is_directory=True)
    else:(root/'unreferenced.json').write_bytes(b'[]')
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(ValueError):candidate.verify(path,digest,PROFILES,NOTICE,raw,key=KEY)
    assert len(os.listdir('/proc/self/fd'))==before


@pytest.mark.parametrize('kind',['payload','mac','wrong-key','oversize','duplicate-key','nonfinite','wrong-version'])
def test_untrusted_witness_never_supplies_context(candidate,experiment,kind):
    path,digest=experiment;raw=candidate.certify(path,digest,PROFILES,NOTICE,key=KEY);key=KEY
    value=json.loads(raw)
    if kind=='payload':value['payload']['context']['seed'][0]+=1;raw=json.dumps(value).encode()
    elif kind=='mac':value['hmac_sha256']='0'*64;raw=json.dumps(value).encode()
    elif kind=='wrong-key':key=b'other-own-test-key-only-32-bytes!!'
    elif kind=='oversize':raw=b' '* (candidate.MAX_WITNESS_BYTES+1)
    elif kind=='duplicate-key':raw=b'{"payload":{},"payload":{},"hmac_sha256":""}'
    elif kind=='nonfinite':raw=b'{"payload":NaN,"hmac_sha256":""}'
    else:
        value['payload']['version']='unreviewed'
        value['hmac_sha256']=hmac.new(KEY,candidate.DOMAIN+candidate.driver().inputs._canonical(value['payload']),'sha256').hexdigest()
        raw=json.dumps(value).encode()
    with pytest.raises(ValueError):candidate.verify(path,digest,PROFILES,NOTICE,raw,key=key)


def test_changed_experiment_or_witness_code_requires_new_evidence(candidate,experiment,tmp_path,monkeypatch):
    path,digest=experiment;raw=candidate.certify(path,digest,PROFILES,NOTICE,key=KEY)
    file=path/'experiment.json';old=file.read_bytes();file.chmod(0o600);file.write_bytes(old+b' ')
    with pytest.raises(ValueError):candidate.verify(path,digest,PROFILES,NOTICE,raw,key=KEY)
    file.write_bytes(old)
    changed=tmp_path/'changed-witness.py';changed.write_text('changed source')
    monkeypatch.setattr(candidate,'__file__',str(changed))
    with pytest.raises(ValueError):candidate.verify(path,digest,PROFILES,NOTICE,raw,key=KEY)


def test_failed_original_preflight_never_issues_witness(candidate,experiment):
    path,digest=experiment;target=path/'inputs'/'root.json';target.chmod(0o600);target.write_bytes(b'{}')
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(ValueError):candidate.certify(path,digest,PROFILES,NOTICE,key=KEY)
    assert len(os.listdir('/proc/self/fd'))==before
