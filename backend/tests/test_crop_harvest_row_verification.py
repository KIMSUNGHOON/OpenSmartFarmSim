from copy import deepcopy
from hashlib import sha256
import os

import pytest

from app import crop_harvest_registry as registry
from test_crop_harvest_replay import owned_directory, replay, source_and_parameters


@pytest.mark.parametrize('large', [False, True])
def test_all_rows_match_original_chain_and_page_reads_without_rederivation(tmp_path, monkeypatch, large):
    directory = owned_directory(tmp_path);read, raw, allocation = source_and_parameters(large)
    original = list(replay.harvest._read_allocations(read, raw, allocation))
    expected = {'row_count': len(original), 'row_chain_sha256': sha256(
        b''.join(replay._canonical(row) + b'\n' for row in original)).hexdigest()}
    result = replay._write(directory, read, raw, allocation);calls = []
    def observed(**kwargs):
        calls.append(kwargs);return read(**kwargs)
    before = len(os.listdir('/proc/self/fd'))
    with replay._Reader(directory, result['artifact_sha256'], observed) as stored:
        calls.clear();chain = sha256();count = 0
        for start in range(0, len(original), replay.LIMITS['page_records']):
            for row in stored.page(start, replay.LIMITS['page_records'])['records']:
                chain.update(replay._canonical(row) + b'\n');count += 1
        assert {'row_count': count, 'row_chain_sha256': chain.hexdigest()} == expected
        assert len(calls) == 2 * len(stored._root['pages'])
        calls.clear()
        def forbidden(*args, **kwargs):pytest.fail('stored verification rederived quantities')
        for name in ('_read_allocations', '_mass_row', '_allocation_row', '_terminal_row', '_event_row'):
            monkeypatch.setattr(replay.harvest, name, forbidden)
        assert stored.verify_all_rows() == expected
        assert calls == [{}, {}]
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('page_index', [0, 1, 2])
def test_every_page_is_hashed_and_failure_closes_handle(tmp_path, page_index):
    directory = owned_directory(tmp_path);read, raw, allocation = source_and_parameters(True)
    result = replay._write(directory, read, raw, allocation)
    with replay._Reader(directory, result['artifact_sha256'], read) as stored:
        descriptor = stored._root['pages'][page_index]
        path = directory / (descriptor['sha256'] + '.json')
        path.chmod(0o600);path.write_bytes(b'[]');path.chmod(0o400)
        with pytest.raises(replay.HarvestArtifactHold):stored.verify_all_rows()
        assert stored._fd is None


@pytest.mark.parametrize('change', ['rights', 'account', 'HEAD', 'root', 'directory'])
def test_changes_after_last_page_are_rejected_before_success(tmp_path, monkeypatch, change):
    directory = owned_directory(tmp_path);read, raw, allocation = source_and_parameters(True)
    result = replay._write(directory, read, raw, allocation);revoked = False
    def current(**kwargs):
        if revoked:
            if change == 'account':raise PermissionError('owned account revoked')
            value = read(**kwargs);value['identity']['artifact_sha256'] = '9' * 64;return value
        return read(**kwargs)
    stored = replay._Reader(directory, result['artifact_sha256'], current)
    original_blob = replay._blob;last = stored._root['pages'][-1]['sha256']
    def changed(fd, digest, maximum):
        nonlocal revoked
        value = original_blob(fd, digest, maximum)
        if digest == last:
            if change in ('rights', 'account'):revoked = True
            elif change == 'directory':directory.rename(tmp_path / 'old');directory.mkdir(mode=0o700)
            else:
                path = directory / ('HEAD' if change == 'HEAD' else result['artifact_sha256'] + '.json')
                path.chmod(0o600);path.write_bytes(b'{}');path.chmod(0o400)
        return value
    monkeypatch.setattr(replay, '_blob', changed)
    error = PermissionError if change == 'account' else replay.HarvestArtifactHold
    with pytest.raises(error):stored.verify_all_rows()
    assert stored._fd is None


@pytest.mark.parametrize('change', ['count', 'chain', 'page-count', 'row-order'])
def test_invalid_row_sequence_or_totals_are_rejected(tmp_path, monkeypatch, change):
    directory = owned_directory(tmp_path);read, raw, allocation = source_and_parameters(True)
    result = replay._write(directory, read, raw, allocation)
    with replay._Reader(directory, result['artifact_sha256'], read) as stored:
        original_blob = replay._blob;first = stored._root['pages'][0]['sha256']
        if change == 'count':stored._root['row_count'] += 1
        elif change == 'chain':stored._root['row_chain_sha256'] = '0' * 64
        def altered(fd, digest, maximum):
            value = original_blob(fd, digest, maximum)
            if digest == first:
                value = deepcopy(value)
                if change == 'page-count':value.pop()
                elif change == 'row-order':value[0], value[1] = value[1], value[0]
            return value
        monkeypatch.setattr(replay, '_blob', altered)
        with pytest.raises(replay.HarvestArtifactHold):stored.verify_all_rows()
        assert stored._fd is None


def test_registry_checks_complete_stored_rows_and_metadata(tmp_path, monkeypatch):
    directory = owned_directory(tmp_path);read, raw, allocation = source_and_parameters(True)
    result = replay._write(directory, read, raw, allocation);codec = object.__new__(registry.HarvestRegistry)
    codec.query = None;codec.directory = tmp_path
    packet = {'tenant_id': 'owned', 'parent_result_id': 'owned', 'farm': {},
        'source': replay.harvest._source(read()), 'artifact': {'key': directory.name,
            'sha256': result['artifact_sha256'], 'row_count': result['row_count'],
            'row_chain_sha256': result['row_chain_sha256']}}
    monkeypatch.setattr(replay, 'open_harvest_artifact', lambda path, expected, *args:
        replay._Reader(path, expected, read))
    codec._verify_artifact(packet, raw, allocation, full=True)
    with replay._Reader(directory, result['artifact_sha256'], read) as stored:
        path = directory / (stored._root['pages'][-1]['sha256'] + '.json')
    path.chmod(0o600);path.write_bytes(b'[]');path.chmod(0o400)
    with pytest.raises(replay.HarvestArtifactHold):codec._verify_artifact(packet, raw, allocation, full=True)


def test_byte_split_blobs_still_enforce_existing_logical_page_response_limit(tmp_path, monkeypatch):
    directory = owned_directory(tmp_path);read, raw, allocation = source_and_parameters(True)
    rows = list(replay.harvest._read_allocations(read, raw, allocation))
    for row in rows:row['owned_test_padding'] = 'x' * 40000
    with monkeypatch.context() as patch:
        patch.setattr(replay.harvest, '_read_allocations', lambda *args: iter(rows))
        result = replay._write(directory, read, raw, allocation)
    with replay._Reader(directory, result['artifact_sha256'], read) as stored:
        assert stored._root['pages'][0]['count'] < replay.LIMITS['page_records']
        with pytest.raises(replay.HarvestArtifactHold):stored.page(0, replay.LIMITS['page_records'])
    with replay._Reader(directory, result['artifact_sha256'], read) as stored:
        with pytest.raises(replay.HarvestArtifactHold):stored.verify_all_rows()
        assert stored._fd is None
