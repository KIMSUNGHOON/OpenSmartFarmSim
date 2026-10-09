from copy import deepcopy
from hashlib import sha256
import importlib.util
import os
from pathlib import Path

import pytest
from psycopg.conninfo import conninfo_to_dict

SCRIPT = Path(__file__).resolve().parents[2]/'research/crop-harvest-parent-backup.py'
spec = importlib.util.spec_from_file_location('owned_parent_backup_tests',SCRIPT)
backup = importlib.util.module_from_spec(spec);spec.loader.exec_module(backup)


def transport():
    raw = b'host=127.0.0.1 port=15432 dbname=postgres user=owned_authority passfile=/owned/original.pgpass require_auth=scram-sha-256'
    password = b'a'*64
    passfile = b'127.0.0.1:15432:postgres:owned_authority:'+password+b'\n'
    document = {'dsn_file':'/owned/old.private','static_sha256':{'/owned/old.private':sha256(raw).hexdigest(),'/owned/input': '1'*64},
                'input':{'directory':'/owned/unchanged-input'},'server_directory':'/owned/unchanged-artifact','keys':{'server':'/owned/key'}}
    return raw,passfile,document


def test_transport_changes_only_port_passfile_and_explicit_config_pin():
    raw,passfile,document = transport();before = deepcopy(document)
    target,dsn,secret = backup.retarget(document,source_dsn_raw=raw,passfile_raw=passfile,
        port=25432,dsn_file='/owned/new.private',passfile_file='/owned/new.pgpass')
    params = conninfo_to_dict(dsn.decode())
    assert params['port']=='25432' and params['passfile']=='/owned/new.pgpass' and params['require_auth']=='scram-sha-256'
    assert secret.replace(b':25432:',b':15432:')==passfile and document==before
    assert target['input']==before['input'] and target['keys']==before['keys'] and target['server_directory']==before['server_directory']
    assert target['static_sha256']=={'/owned/new.private':sha256(dsn).hexdigest(),'/owned/input':'1'*64}


@pytest.mark.parametrize('change',['inline-password','remote-host','missing-passfile','wrong-role','extra-row','escaped','bad-port','bool-port'])
def test_transport_refuses_general_or_mixed_credentials(change):
    raw,passfile,document = transport();port = 25432
    if change=='inline-password':raw+=b' password=must_not_be_used'
    elif change=='remote-host':raw=raw.replace(b'127.0.0.1',b'example.org')
    elif change=='missing-passfile':raw=raw.replace(b' passfile=/owned/original.pgpass',b'')
    elif change=='wrong-role':passfile=passfile.replace(b'owned_authority',b'other')
    elif change=='extra-row':passfile*=2
    elif change=='escaped':passfile=passfile.replace(b'a'*64,b'a'*62+b'\\:')
    elif change=='bad-port':port=65536
    else:port=True
    with pytest.raises(ValueError):backup.retarget(document,source_dsn_raw=raw,passfile_raw=passfile,
        port=port,dsn_file='/owned/new.private',passfile_file='/owned/new.pgpass')


def test_private_hash_is_bounded_and_refuses_changed_mode_or_symlink(tmp_path):
    tmp_path.chmod(0o700);path=tmp_path/'private';raw=b'x'*(1024**2+1);backup.write(path,raw)
    fds=len(os.listdir('/proc/self/fd'));assert backup.private_hash(path)==sha256(raw).hexdigest()
    assert backup.private_read(path,len(raw))==raw
    with pytest.raises(ValueError):backup.private_read(path,len(raw)-1)
    path.chmod(0o644)
    with pytest.raises(backup.runtime.custody.CalculationCustodyHold):backup.private_hash(path)
    path.unlink();path.symlink_to(SCRIPT)
    with pytest.raises(OSError):backup.private_hash(path)
    assert len(os.listdir('/proc/self/fd'))==fds


def test_source_guard_refuses_a_remote_or_password_admin_without_connecting(monkeypatch,tmp_path):
    monkeypatch.setattr(backup.psycopg,'connect',lambda *a,**k:pytest.fail('unowned admin opened DB'))
    for dsn in ('host=127.0.0.1 dbname=postgres','host=/owned password=not_allowed'):
        with pytest.raises(ValueError):backup.protect_source(dsn,tmp_path,tmp_path)
