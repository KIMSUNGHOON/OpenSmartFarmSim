from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2]/'research/crop-harvest-storage-preservation.py'
spec = importlib.util.spec_from_file_location('harvest_storage_preservation_tests',SCRIPT)
storage = importlib.util.module_from_spec(spec);spec.loader.exec_module(storage)


@pytest.mark.parametrize('change',['extra','approval','scope','code','dependencies','files','noncanonical','wrong-hash'])
def test_manifest_refuses_unbound_or_approved_authority_before_any_database(tmp_path,monkeypatch,change):
    tmp_path.chmod(0o700)
    value = {'version':storage.VERSION,'scope':'owned_synthetic_only','code_sha256':storage.CODE_SHA256,
        'dependencies':storage.DEPENDENCIES,'parent_backup':'unused','parent_backup_sha256':'1'*64,
        'policy':{},'registry_directory':'unused','files_sha256':{name:'0'*64 for name in storage.FILES},
        'original_record':{},'source':{},'summary_sha256':'2'*64,'pages':{}}
    if change == 'extra':value['extra'] = True
    elif change == 'approval':value['rights_or_gate_approval'] = True
    elif change == 'scope':value['scope'] = 'production'
    elif change == 'code':value['code_sha256'] = '0'*64
    elif change == 'dependencies':value['dependencies'] = {}
    elif change == 'files':value['files_sha256'] = {}
    raw = storage.canonical(value)+(b'\n' if change == 'noncanonical' else b'')
    path = tmp_path/'storage.private.json';storage.backup.write(path,raw)
    monkeypatch.setattr(storage.backup,'checked',lambda *a:pytest.fail('invalid authority reached DB backup'))
    with pytest.raises(ValueError):storage.checked(path,'0'*64 if change == 'wrong-hash' else sha256(raw).hexdigest())


def test_reader_guard_prevents_new_harvest_rows_and_publication():
    with storage.read_guard():
        for target,name in ((storage.harvest,'_read_allocations'),(storage.harvest,'_mass_row'),
                (storage.harvest,'_allocation_row'),(storage.registry.HarvestRegistry,'put')):
            with pytest.raises(AssertionError):getattr(target,name)()


def test_registry_credentials_are_private_and_cannot_overwrite_existing_file(tmp_path):
    path = tmp_path/'reader.pgpass';storage.pgpass(path,b'owned-not-production')
    assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):storage.pgpass(path,b'changed')
    assert path.read_bytes() == b'owned-not-production'
