"""Owned scope/lifecycle and immutable page checks; native SCRAM proof stays separate."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from types import SimpleNamespace

import pytest

from app import crop_harvest_current_query as query
from test_crop_harvest import OwnedPages, mass_profile, allocation_profile
from test_crop_harvest_replay import owned_directory


@pytest.fixture
def case(tmp_path, monkeypatch):
    registry = query.registry; replay = registry.replay; raw = registry._canonical
    pages = OwnedPages(); state = {'allowed': True, 'display': True, 'valid_row': True, 'farm': True,
        'mutate_rights': False, 'final_failure': False, 'opens': 0, 'closes': 0, 'checks': 0}
    farm = {'scenario_id': 'owned-farm', 'scenario_revision': '1', 'registration_sha256': '2' * 64, 'crop_id': 'owned-crop'}
    packet = json.loads(pages.original['record']['payload_raw'])
    packet.update(binding={'request': {'rights': {'kind': 'owned-synthetic'}}, 'registration': {'owned': True},
        'input': {'root_sha256': packet['input_root_sha256']}})
    packet['policies'] = {'input_rights_version': 'owned-rights-v1', 'resolver_version': 'owned-resolver-v1',
                         'notice_sha256': sha256(b'owned-notice').hexdigest()}
    record = pages.original['record']; record['result_id'] = query.current.storage.VERSION + ':' + '1' * 64
    record.update(payload_raw=raw(packet), payload_sha256=sha256(raw(packet)).hexdigest())
    record['recorded_at'] = datetime(2026, 10, 9, tzinfo=timezone.utc)
    def guard(*_):
        state['checks'] += 1
        if not state['allowed']: raise PermissionError('owned scope withdrawn')
    class Rights:
        policy_version = 'owned-rights-v1'
        def __call__(self, tenant, declaration, root, use):
            assert tenant == 'tenant-1' and root == packet['input_root_sha256'] and use == 'research_display'
            if state['mutate_rights']: declaration['changed'] = True
            return state['display']
    binding = SimpleNamespace(input_rights=Rights(), notice_raw=b'owned-notice',
        _registration=lambda *_: {'owned': state['farm']})
    parent = object.__new__(query.current.CalculationCurrentCycleQuery)
    parent.store = SimpleNamespace(_guard=guard, _find=lambda *a, **k: record,
        _record=lambda r: deepcopy(r), _row=lambda *_: deepcopy(packet) if state['valid_row'] else {},
        server=SimpleNamespace(binding=binding, input_resolver=SimpleNamespace(version='owned-resolver-v1')))
    monkeypatch.setattr(parent, '_binding', guard)
    @contextmanager
    def opened(*args):
        assert args == ('tenant-1', record['result_id'], farm)
        state['opens'] += 1
        try:
            guard(); yield deepcopy(pages.original)
            if state['final_failure']: raise ValueError('owned final parent snapshot changed')
            guard()
        finally: state['closes'] += 1
    monkeypatch.setattr(parent, 'open', opened)
    monkeypatch.setattr(parent, 'read', lambda *_a, **_k: pytest.fail('new parent read inside request'))
    mass = raw(mass_profile(replay.harvest._source(pages())))
    allocation = raw(allocation_profile(replay.harvest._mass_parameters(mass)))
    directory = owned_directory(tmp_path); result = replay._write(directory, pages, mass, allocation)
    source = replay.harvest._source(pages())
    packet_raw = registry._packet(registry._base('tenant-1', record['result_id'], farm, source,
        {'mass_sha256': sha256(mass).hexdigest(), 'allocation_sha256': sha256(allocation).hexdigest()}), result)
    codec = object.__new__(registry.HarvestRegistry)
    codec.policy = registry.schema.HarvestRegistryPolicy('owned_s', 'owned_o', 'owned_p', 'owned_r', 'owned_db')
    codec.integrity_key = b'owned-current-read-key-' + b'x' * 32
    row = codec._values(json.loads(packet_raw), packet_raw); row['recorded_at'] = record['recorded_at']
    artifact = tmp_path / 'registry'; artifact.mkdir(mode=0o700); directory.rename(artifact / json.loads(packet_raw)['artifact']['key'])
    codec.directory = artifact; codec.query = parent
    monkeypatch.setattr(codec, '_find', lambda *_: deepcopy(row))
    service = object.__new__(query.HarvestCurrentQuery); service.store = codec
    monkeypatch.setattr(service, '_guard', guard)
    root = artifact / json.loads(packet_raw)['artifact']['key']
    document = json.loads((root / (result['artifact_sha256'] + '.json')).read_bytes())
    return SimpleNamespace(service=service, parent=parent, parent_id=record['result_id'], farm=farm,
        result_id=json.loads(packet_raw)['result_id'], state=state, root=root, document=document, row=row,
        parent_packet=packet, binding=binding)


@pytest.mark.parametrize('limit', [None, 1, 64])
def test_whole_harvest_request_opens_parent_once_and_preserves_values(case, limit):
    before = len(os.listdir('/proc/self/fd'))
    value = case.service.read('tenant-1', case.result_id, case.farm, limit=limit)
    assert value['summary']['row_count'] == 6
    assert value['page'] is None if limit is None else len(value['page']['records']) == min(limit, 6)
    assert case.state['opens'] == case.state['closes'] == 1 and case.state['checks'] > 8
    assert before == len(os.listdir('/proc/self/fd'))


def test_parent_snapshot_copy_and_expired_callback(case):
    with case.service._parent_read('tenant-1', case.parent_id, case.farm) as read:
        original = read(); read()['identity']['changed'] = True
        assert read() == original
    with pytest.raises(query.HarvestCurrentQueryHold): read()


@pytest.mark.parametrize('fault', ['scope', 'row', 'farm', 'display', 'rights-version', 'resolver', 'notice', 'declaration'])
def test_each_internal_read_checks_current_authority(case, fault):
    before = len(os.listdir('/proc/self/fd'))
    with case.service._parent_read('tenant-1', case.parent_id, case.farm) as read:
        read()
        if fault == 'scope': case.state['allowed'] = False
        elif fault == 'row': case.state['valid_row'] = False
        elif fault == 'farm': case.state['farm'] = False
        elif fault == 'display': case.state['display'] = False
        elif fault == 'rights-version': case.binding.input_rights.policy_version = 'changed'
        elif fault == 'resolver': case.parent.store.server.input_resolver.version = 'changed'
        elif fault == 'notice': case.binding.notice_raw = b'changed'
        else: case.state['mutate_rights'] = True
        with pytest.raises((PermissionError, query.HarvestCurrentQueryHold)): read()
        case.state['allowed'] = True
    assert before == len(os.listdir('/proc/self/fd'))


@pytest.mark.parametrize('fault', ['parent-final', 'scope', 'display', 'signed-row', 'HEAD', 'page'])
def test_after_yield_changes_never_return_a_successful_result(case, monkeypatch, fault):
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises((PermissionError, query.HarvestCurrentQueryHold)):
        with case.service.open('tenant-1', case.result_id, case.farm, limit=64) as value:
            assert len(value['page']['records']) == 6
            if fault == 'parent-final': case.state['final_failure'] = True
            elif fault == 'scope': case.state['allowed'] = False
            elif fault == 'display': case.state['display'] = False
            elif fault == 'signed-row': monkeypatch.setattr(case.service.store, '_find', lambda *_: None)
            else:
                path = case.root / ('HEAD' if fault == 'HEAD' else case.document['pages'][0]['sha256'] + '.json')
                path.chmod(0o600); path.write_bytes(path.read_bytes() + b' '); path.chmod(0o400)
    assert case.state['opens'] == case.state['closes'] == 1
    assert before == len(os.listdir('/proc/self/fd'))


def test_caller_failure_closes_parent_and_expires_callback(case):
    with pytest.raises(RuntimeError):
        with case.service._parent_read('tenant-1', case.parent_id, case.farm) as read:
            raise RuntimeError('owned caller canceled')
    assert case.state['closes'] == 1
    with pytest.raises(query.HarvestCurrentQueryHold): read()
