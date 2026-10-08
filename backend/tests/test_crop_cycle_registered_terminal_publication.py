"""Private publication declarations reject changed evidence before runtime assembly."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-publication.py'


@pytest.fixture
def publisher():
    spec=importlib.util.spec_from_file_location('registered_publication',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def rewrite(path,value):
    path.chmod(0o600);path.write_bytes(value);path.chmod(0o400)


@pytest.fixture
def declaration(publisher,tmp_path,monkeypatch):
    key=tmp_path/'DB-key.private';publisher.runtime.write_private(key,b'p'*32)
    server_key=tmp_path/'server-key.private';publisher.runtime.write_private(server_key,b's'*32)
    manifest={'config':'owned-config','config_sha256':'c'*64,'input_root_sha256':'0'*64}
    monkeypatch.setattr(publisher.supervisor,'verified',lambda *a,**k:(tmp_path,manifest))
    monkeypatch.setattr(publisher.supervisor,'configuration',lambda *a,**k:{'keys':{'server':str(server_key)}})
    value={'version':publisher.VERSION,'scope':publisher.SCOPE,'code_sha256':publisher.CODE_SHA256,
        'supervision_directory':str(tmp_path),'supervision_sha256':'a'*64,'DB_key_file':str(key),
        'DB_key_sha256':sha256(key.read_bytes()).hexdigest(),'source_sha256':publisher.sources(),
        'input_root_sha256':'0'*64,'plan':{'steps':120,'counts':{'samples':3,'events':0}}}
    path=tmp_path/'publication.json';publisher.supervisor.immutable(path,value)
    return path,value,key


@pytest.mark.parametrize('fault',['SHA','version','field','mode','source','key','server-key'])
def test_declaration_fault_rejects_before_runtime(publisher,declaration,monkeypatch,fault):
    path,value,key=declaration;calls=[]
    monkeypatch.setattr(publisher,'assemble',lambda *a:calls.append(True))
    checksum=sha256(path.read_bytes()).hexdigest()
    publisher.load_declaration(path,checksum);assert calls==[True];calls.clear()
    if fault=='SHA':checksum='f'*64
    elif fault=='version':value['version']='old-publication-v0'
    elif fault=='field':value['unexpected']=True
    elif fault=='source':value['source_sha256']={}
    elif fault=='key':rewrite(key,b'q'*32)
    elif fault=='server-key':
        rewrite(key,b's'*32);value['DB_key_sha256']=sha256(key.read_bytes()).hexdigest()
    if fault in ('version','field','source','server-key'):
        raw=publisher.supervisor.durable._canonical(value);rewrite(path,raw);checksum=sha256(raw).hexdigest()
    if fault=='mode':path.chmod(0o644)
    with pytest.raises(ValueError):publisher.load_declaration(path,checksum)
    assert calls==[]


def test_expired_original_supervision_denies_before_runtime(publisher,declaration,monkeypatch):
    path,_,_=declaration;calls=[];monkeypatch.setattr(publisher,'assemble',lambda *a:calls.append(True))
    checksum=sha256(path.read_bytes()).hexdigest();publisher.load_declaration(path,checksum);assert calls==[True];calls.clear()
    def expired(*a,**k):raise ValueError('original deadline expired')
    monkeypatch.setattr(publisher.supervisor,'verified',expired)
    with pytest.raises(ValueError):publisher.load_declaration(path,checksum)
    assert calls==[]
