"""Reference capture tests use synthetic values, not source or release authority."""

from copy import deepcopy
from datetime import date, datetime, timezone
from hashlib import sha256
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import break_even_replay
from app.break_even_replay import BreakEvenReplayEvidence, ReplayRead, ReplayReferences
from app.market_scenario import _json


def source(value):
    calls = []
    def get(*args):
        calls.append(args)
        return deepcopy(value)
    return SimpleNamespace(tenant_is_authenticated=lambda tenant: tenant == 'tenant-1',
        get_economic_input=get), calls


def test_reads_are_fresh_and_deduplicated_only_in_evidence():
    value = {'number': '12.50', 'date': date(2026, 9, 1),
        'at': datetime(2026, 9, 1, tzinfo=timezone.utc), 'label': '합성 가정'}
    provider, calls = source(value)
    captured = ReplayReferences(provider, 'tenant-1')
    assert captured.get_economic_input('price', 'r1') == value
    assert captured.get_economic_input('price', 'r1') == value
    reads = captured.recheck()
    assert calls == [('price', 'r1')] * 3
    assert reads == (ReplayRead(method='get_economic_input', args=('price', 'r1'),
        value_sha256=sha256(_json(value).encode()).hexdigest()),)
    assert 'number' not in reads[0].model_dump_json() and '합성 가정' not in reads[0].model_dump_json()
    with pytest.raises(AttributeError): captured.pin_market_candidate({})


@pytest.mark.parametrize('phase', ['repeated_read', 'recheck'])
def test_changed_references_are_refused(phase):
    value = {'value': '12.50'}
    provider, _ = source(value)
    captured = ReplayReferences(provider, 'tenant-1')
    captured.get_economic_input('price', 'r1')
    value['value'] = '12.51'
    with pytest.raises(ValueError, match='reference changed'):
        if phase == 'recheck': captured.recheck()
        else: captured.get_economic_input('price', 'r1')
    value['value'] = '12.50'
    with pytest.raises(ValueError, match='already failed'): captured.recheck()


def test_missing_revoked_or_invalid_references_do_not_return_evidence():
    provider, _ = source(None)
    captured = ReplayReferences(provider, 'tenant-1')
    with pytest.raises(ValueError, match='reference missing'):
        captured.get_economic_input('price', 'r1')
    with pytest.raises(ValueError, match='already failed'): captured.recheck()
    captured = ReplayReferences(provider, 'tenant-1')
    with pytest.raises(ValueError, match='empty'): captured.recheck()
    captured = ReplayReferences(provider, 'tenant-1')
    provider.get_economic_input = lambda *_: {'value': '12.50'}
    captured.get_economic_input('price', 'r1')
    provider.tenant_is_authenticated = lambda *_: False
    with pytest.raises(ValueError, match='tenant access denied'): captured.recheck()
    with pytest.raises(ValueError): captured.get_economic_input('price')


def test_checkpoint_interrupt_propagates_without_returning_partial_evidence():
    provider, _ = source({'value': '12.50'})
    captured = ReplayReferences(provider, 'tenant-1')
    captured.get_economic_input('price', 'r1')
    def canceled(): raise RuntimeError('synthetic cancellation')
    with pytest.raises(RuntimeError, match='synthetic cancellation'):
        captured.recheck(check=canceled)


@pytest.mark.parametrize('method,arity', list(break_even_replay._ARITY.items()))
def test_each_closed_lookup_requires_its_exact_reference_shape(method, arity):
    provider, _ = source({'value': '12.50'})
    setattr(provider, method, lambda *_: {'value': '12.50'})
    captured = ReplayReferences(provider, 'tenant-1')
    args = tuple('id-' + str(i) for i in range(arity))
    assert getattr(captured, method)(*args) == {'value': '12.50'}
    assert captured.recheck()[0].args == args
    with pytest.raises(ValueError): getattr(captured, method)(*(args + ('extra',)))
    fresh = ReplayReferences(provider, 'tenant-1')
    with pytest.raises(ValueError): getattr(fresh, method)(*('x' * 201 for _ in args))


@pytest.mark.parametrize('value', [float('nan'), float('inf'), {'unsupported': object()}])
def test_noncanonical_values_are_not_hashed(value):
    provider, _ = source(value)
    with pytest.raises(ValueError, match='not canonical'):
        ReplayReferences(provider, 'tenant-1').get_economic_input('price', 'r1')


def test_reference_budget_refuses_new_keys_without_returning_partial_evidence(monkeypatch):
    monkeypatch.setattr(break_even_replay, '_MAX_READS', 1)
    provider, _ = source({'value': '12.50'})
    captured = ReplayReferences(provider, 'tenant-1')
    captured.get_economic_input('price', 'r1')
    captured.get_economic_input('price', 'r1')
    with pytest.raises(ValueError, match='size limit'):
        captured.get_economic_input('price', 'r2')
    with pytest.raises(ValueError, match='already failed'): captured.recheck()


def test_manifest_shape_cannot_accept_empty_duplicate_or_wrong_plan_references():
    plan = ReplayRead(method='get_break_even_plan', args=('plan-1',), value_sha256='a' * 64)
    rights = ReplayRead(method='get_input_rights', args=('price', 'r1'), value_sha256='b' * 64)
    fields = dict(evidence_version='break-even-replay-evidence-v1',
        verification='full_grid_replay_evidence_only', tenant_id='tenant-1', plan_id='plan-1',
        request_sha256='c' * 64, plan_sha256='a' * 64, result_sha256='d' * 64,
        code_sha256='e' * 64, environment_sha256='f' * 64, trial_count=2)
    assert BreakEvenReplayEvidence(**fields, reads=(plan, rights)).trial_count == 2
    for reads in ((), (rights,), (plan, plan), (rights, plan)):
        with pytest.raises(ValueError): BreakEvenReplayEvidence(**fields, reads=reads)
    with pytest.raises(ValueError):
        BreakEvenReplayEvidence(**(fields | {'plan_sha256': 'b' * 64}), reads=(plan, rights))
