"""Actual current authority remains at data and numerical consumption boundaries."""
import json

import pytest

from app import crop_greenhouse_solar_server_custody as model
from test_crop_greenhouse_solar_server_custody import (
    setup, authoring, profiles, login_database, login_scope, cleanup,
    settle_owned_database_backends, pytestmark)


def test_deferred_entry_is_strictly_read_only_and_rejects_invalid_modes(setup):
    server, raw, _ = setup
    before = set(server.directory.iterdir())
    for mode in (None, 0, 1, 'false', [], {}):
        with pytest.raises(model.SolarCustodyHold):
            with server._open('tenant-1', raw, False, entry_guard=mode):
                pytest.fail('invalid mode yielded a session')
    with pytest.raises(model.SolarCustodyHold):
        with server._open('tenant-1', raw, True, entry_guard=False):
            pytest.fail('write session deferred its entry validation')
    assert set(server.directory.iterdir()) == before


def test_default_binding_reader_is_eager_and_inspect_checks_before_load(setup, monkeypatch):
    server, raw, value = setup
    expected = server.advance('tenant-1', raw, budget=1)
    calls = []
    original_current = type(server.binding).current
    original_load = model._Session._load

    def current(binding, *args, **kwargs):
        answer = original_current(binding, *args, **kwargs)
        calls.append('current')
        return answer

    def load(session, *args, **kwargs):
        assert calls and calls[-1] == 'current'
        calls.append('load')
        return original_load(session, *args, **kwargs)

    monkeypatch.setattr(type(server.binding), 'current', current)
    monkeypatch.setattr(model._Session, '_load', load)
    with server._open('tenant-1', raw, False) as (session, _):
        assert calls == ['current']
        assert json.loads(session.binding_raw)['request'] == json.loads(raw)
    calls.clear()
    assert server.inspect('tenant-1', raw) == expected
    assert calls == ['current', 'load', 'current']
    calls.clear()
    value[5].allowed = False
    with pytest.raises(model.SolarCustodyHold):
        server.inspect('tenant-1', raw)
    assert 'load' not in calls


@pytest.mark.parametrize('revocation', ['physical_source', 'economic_source'])
def test_prepare_return_revocation_is_checked_before_any_continuation(setup, monkeypatch, revocation):
    server, raw, value = setup
    original = model._Session.advance
    calls = []

    def advance(session, budget, prepare):
        def revoke_after_return():
            proposal = prepare()
            if revocation == 'physical_source':
                value[5].allowed = False
            else:
                source = server.binding.farms.replay.candidates._source._source
                monkeypatch.setattr(source, 'get_input_rights', lambda *_: None)
            return proposal
        return original(session, budget, revoke_after_return)

    def forbidden(*args, **kwargs):
        calls.append('continuation')
        pytest.fail('revoked proposal entered numerical continuation')

    monkeypatch.setattr(model._Session, 'advance', advance)
    for name in ('start', 'restore_checkpoint', 'advance_chunk'):
        monkeypatch.setattr(model.continuation, name, forbidden)
    with pytest.raises(model.SolarCustodyHold):
        server.advance('tenant-1', raw, budget=1)
    identity = model._intent_id('tenant-1', json.loads(raw))
    assert not calls and not (server.directory / identity / 'artifact' / 'HEAD').exists()
