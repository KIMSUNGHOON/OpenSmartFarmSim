from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_harvest_replay as replay
from test_crop_harvest import OwnedPages, allocation_profile, mass_profile, sample
from test_crop_harvest import (stored_result, server_setup, bound_setup, counts, login_scope,
    original_login_scope, authoring, farm_setup, login_database, native_cleanup, forbid_calculation, save_native)


def source_and_parameters(large=False):
    reader = OwnedPages()
    if large:
        begin = datetime(2026, 10, 1, tzinfo=timezone.utc)
        reader.samples = [sample((begin + timedelta(minutes=i)).strftime('%Y-%m-%dT%H:%M:%SZ'), float(i), i / 4)
                          for i in range(130)]
        packet = replay.current.inputs._json(reader.original['record']['payload_raw'])
        packet['artifact']['sample_count'] = len(reader.samples)
        reader.original['record']['payload_raw'] = replay._canonical(packet)
    profile = mass_profile(replay.harvest._source(reader()))
    profile['segments'][0]['end_at'] = reader.samples[-1]['at']
    raw = replay._canonical(profile)
    allocation = allocation_profile(replay.harvest._mass_parameters(raw), last_sample=len(reader.samples)-1)
    return reader, raw, replay._canonical(allocation)


def owned_directory(tmp_path):
    path = tmp_path / 'harvest';path.mkdir(mode=0o700)
    return path


@pytest.mark.parametrize('large', [False, True])
def test_whole_stored_rows_split_pages_and_fresh_python_without_rederiving(tmp_path, monkeypatch, large):
    directory = owned_directory(tmp_path);reader, raw, allocation = source_and_parameters(large)
    expected = list(replay.harvest._read_allocations(reader, raw, allocation))
    before = len(os.listdir('/proc/self/fd'))
    result = replay._write(directory, reader, raw, allocation)
    assert result == replay._write(directory, reader, raw, allocation)
    assert result['row_count'] == len(expected) == (132 if large else 6)
    with replay._Reader(directory, result['artifact_sha256'], reader) as stored:
        actual = []
        for i in range(0, len(expected), 19):actual.extend(stored.page(i, 19)['records'])
        assert actual == expected
        assert stored.page(len(expected), 1)['records'] == []
        assert stored.summary()['row_chain_sha256'] == result['row_chain_sha256']
        assert len(stored._root['pages']) == (3 if large else 1)
        assert stored._root['parameter_raw_utf8'].encode() == raw
        assert stored._root['allocation_raw_utf8'].encode() == allocation
    code = '''
import sys,json
from hashlib import sha256
from test_crop_harvest_replay import replay,source_and_parameters
read,_,_=source_and_parameters(sys.argv[3]=='True')
def forbidden(*args,**kwargs):raise AssertionError('read rederived harvest quantities')
for name in ('_read_allocations','_mass_row','_allocation_row','_terminal_row','_event_row'):
    setattr(replay.harvest,name,forbidden)
chain=sha256();count=0
with replay._Reader(sys.argv[1],sys.argv[2],read) as stored:
    total=stored.summary()['row_count']
    for i in range(0,total,19):
        for row in stored.page(i,19)['records']:
            chain.update(replay._canonical(row)+b'\\n');count+=1
print(json.dumps({'rows':count,'chain':chain.hexdigest()}))
'''
    env = os.environ.copy();env['PYTHONPATH'] = '.:tests'
    child = subprocess.run([sys.executable, '-c', code, str(directory), result['artifact_sha256'], str(large)],
                           env=env, capture_output=True, text=True, timeout=30)
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout) == {'rows': len(expected), 'chain': result['row_chain_sha256']}
    assert len(os.listdir('/proc/self/fd')) == before
    assert all(path.stat().st_mode & 0o777 == (0o600 if path.name == '.writer-lock' else 0o400)
               for path in directory.iterdir())


@pytest.mark.parametrize('phase', ['before', 'after'])
def test_head_interruption_keeps_unpublished_or_complete_bytes_and_retry(tmp_path, monkeypatch, phase):
    directory = owned_directory(tmp_path);reader, raw, allocation = source_and_parameters()
    original = replay._publish
    def interrupted(*args):
        if phase == 'after':original(*args)
        raise RuntimeError('owned interruption at HEAD')
    with monkeypatch.context() as patch:
        patch.setattr(replay, '_publish', interrupted)
        with pytest.raises(RuntimeError):replay._write(directory, reader, raw, allocation)
    assert (directory / 'HEAD').exists() == (phase == 'after')
    result = replay._write(directory, reader, raw, allocation)
    with replay._Reader(directory, result['artifact_sha256'], reader) as stored:assert stored.summary()['row_count'] == 6


@pytest.mark.parametrize('phase', ['before', 'after'])
def test_actual_child_SIGKILL_before_after_HEAD_reopens_and_retries(tmp_path, phase):
    directory = owned_directory(tmp_path)
    code = '''
import sys,os,signal
from test_crop_harvest_replay import replay,source_and_parameters
read,raw,allocation=source_and_parameters()
publish=replay._publish
def interrupted(*args):
    if sys.argv[2]=='after':publish(*args)
    os.kill(os.getpid(),signal.SIGKILL)
replay._publish=interrupted
replay._write(sys.argv[1],read,raw,allocation)
'''
    env = os.environ.copy();env['PYTHONPATH'] = '.:tests'
    child = subprocess.run([sys.executable, '-c', code, str(directory), phase], env=env,
                           capture_output=True, text=True, timeout=30)
    assert child.returncode == -9, child.stderr
    assert (directory / 'HEAD').exists() == (phase == 'after')
    reader, raw, allocation = source_and_parameters()
    result = replay._write(directory, reader, raw, allocation)
    with replay._Reader(directory, result['artifact_sha256'], reader) as stored:
        assert stored.summary()['row_count'] == 6 and len(stored.page()['records']) == 6


def test_late_current_authority_change_blocks_head_and_existing_head_is_immutable(tmp_path):
    directory = owned_directory(tmp_path);reader, raw, allocation = source_and_parameters()
    def withdrawn(**kwargs):
        value = reader(**kwargs)
        if list(directory.glob('.head-*.tmp')):value['identity']['artifact_sha256'] = '9' * 64
        return value
    with pytest.raises(replay.harvest.CropRemovalHold):replay._write(directory, withdrawn, raw, allocation)
    assert not (directory / 'HEAD').exists()
    result = replay._write(directory, reader, raw, allocation);head = (directory / 'HEAD').read_bytes()
    changed = json.loads(allocation);changed['revision'] = '2'
    with pytest.raises(replay.HarvestArtifactHold):replay._write(directory, reader, raw, replay._canonical(changed))
    assert (directory / 'HEAD').read_bytes() == head
    with replay._Reader(directory, result['artifact_sha256'], reader) as stored:assert stored.summary()['row_count'] == 6


@pytest.mark.parametrize('change', ['page', 'HEAD', 'root', 'directory', 'rights'])
def test_changed_storage_or_current_source_closes_reader(tmp_path, change):
    directory = owned_directory(tmp_path);reader, raw, allocation = source_and_parameters()
    result = replay._write(directory, reader, raw, allocation)
    stored = replay._Reader(directory, result['artifact_sha256'], reader)
    if change == 'rights':reader.original['identity']['artifact_sha256'] = '9' * 64
    elif change == 'directory':directory.rename(tmp_path / 'old');directory.mkdir(mode=0o700)
    else:
        name = 'HEAD' if change == 'HEAD' else (result['artifact_sha256'] if change == 'root' else stored._root['pages'][0]['sha256']) + '.json'
        path = directory / name;path.chmod(0o600);path.write_bytes(b'{}');path.chmod(0o400)
    with pytest.raises(replay.HarvestArtifactHold):stored.page()
    assert stored._fd is None


@pytest.mark.parametrize('options', [(-1,1), (True,1), (7,1), (0,0), (0,65), (0,True)])
def test_invalid_page_bounds_are_not_silently_adjusted(tmp_path, options):
    directory = owned_directory(tmp_path);reader, raw, allocation = source_and_parameters()
    result = replay._write(directory, reader, raw, allocation)
    with replay._Reader(directory, result['artifact_sha256'], reader) as stored:
        with pytest.raises(replay.HarvestArtifactHold):stored.page(*options)


def test_current_type_lock_file_security_and_bounded_single_row(tmp_path, monkeypatch):
    directory = owned_directory(tmp_path);reader, raw, allocation = source_and_parameters()
    for arbitrary in (reader, {'approved': True}, object()):
        with pytest.raises(replay.HarvestArtifactHold):replay.write_harvest_artifact(directory, arbitrary, 'tenant', 'result', {}, raw, allocation)
        with pytest.raises(replay.HarvestArtifactHold):replay.open_harvest_artifact(directory, '0'*64, arbitrary, 'tenant', 'result', {})
    fd = replay.files._open_directory_nofollow(directory);lock = replay.files._file(fd, '.writer-lock', lock=True)
    try:
        with pytest.raises(replay.files.CalculationCustodyPending):replay._write(directory, reader, raw, allocation)
    finally:os.close(lock);os.close(fd)
    def oversized(*args, **kwargs):yield {'owned': 'x' * replay.LIMITS['page_bytes']}
    with monkeypatch.context() as patch:
        patch.setattr(replay.harvest, '_read_allocations', oversized)
        with pytest.raises(replay.HarvestArtifactHold):replay._write(directory, reader, raw, allocation)
    assert not (directory / 'HEAD').exists()
    target = tmp_path / 'symlink';target.symlink_to(directory, target_is_directory=True)
    with pytest.raises(OSError):replay._write(target, reader, raw, allocation)


@pytest.mark.parametrize('original_login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True,
    'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)
def test_actual_current_DB_artifact_rows_authority_and_preservation(stored_result, native_cleanup, tmp_path, monkeypatch):
    service, record, farm, rights, principal, expected = stored_result
    assert len(expected['samples']) == 3 and len(expected['events']) == 4
    forbid_calculation(monkeypatch)
    monkeypatch.setattr(type(service.authority), 'issue', lambda *a, **k: pytest.fail('artifact issued proof'))
    original = service.read('tenant-1', record['result_id'], farm)
    profile = mass_profile(replay.harvest._source(original))
    profile['segments'][0]['end_at'] = expected['samples'][-1]['at']
    raw = replay._canonical(profile)
    allocation = replay._canonical(allocation_profile(replay.harvest._mass_parameters(raw), last_sample=2, last_event=3))
    rows = list(replay.harvest.iter_harvest_allocations(service, 'tenant-1', record['result_id'], farm, raw, allocation))
    before = len(os.listdir('/proc/self/fd'));db_before = counts(service.store.server.binding)
    def inventory():
        return {str(p): (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o777, p.stat().st_ino)
            for directory in (service.store.server.directory, service.evidence_resolver.values['input_directory'])
            for p in directory.rglob('*') if p.is_file()}
    files_before = inventory();directory = owned_directory(tmp_path)
    result = replay.write_harvest_artifact(directory, service, 'tenant-1', record['result_id'], farm, raw, allocation)
    with replay.open_harvest_artifact(directory, result['artifact_sha256'], service, 'tenant-1', record['result_id'], farm) as stored:
        assert stored.page()['records'] == rows
        assert stored.page(0, 2)['records'] + stored.page(2, 4)['records'] == rows
        summary = stored.summary();assert summary['row_count'] == len(rows) == 6
        rights.allowed = False
        with pytest.raises(replay.HarvestArtifactHold):stored.page()
    rights.allowed = True
    for action in ('rights', 'scope', 'account'):
        scopes = set(principal['scopes']);tenant = principal['tenant_id']
        try:
            if action == 'rights':rights.allowed = False
            elif action == 'scope':principal['scopes'].remove('crop_result_read')
            else:principal['tenant_id'] = 'foreign'
            error = replay.HarvestArtifactHold if action == 'rights' else PermissionError
            with pytest.raises(error):replay.open_harvest_artifact(directory, result['artifact_sha256'], service, 'tenant-1', record['result_id'], farm)
        finally:rights.allowed = True;principal['scopes'] = scopes;principal['tenant_id'] = tenant
    assert len(os.listdir('/proc/self/fd')) == before and inventory() == files_before
    assert counts(service.store.server.binding) == db_before
    save_native('harvest-artifact-verified.json', {'actual_SCRAM': True, 'source': replay.harvest._source(original),
        'parameter_document': profile, 'allocation_document': json.loads(allocation), 'rows': rows,
        'artifact_result': result, 'summary': summary, 'stored_full_and_split_rows_identical': True,
        'RHS_calls': 0, 'new_proof_calls': 0, 'FD_before_after': [before, len(os.listdir('/proc/self/fd'))],
        'current_rights_scope_account_denied': True, 'open_reader_rights_withdrawal_denied': True,
        'input_custody_SHA_mode_inode_preserved': True, 'DB_counts_preserved': list(db_before),
        'artifact_files': {p.name: {'sha256': sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size,
            'mode': p.stat().st_mode & 0o777, 'canonical_utf8': p.read_text()} for p in directory.iterdir()},
        'actual_crop_Runs': 0, 'gates': 'not_assessed'})
