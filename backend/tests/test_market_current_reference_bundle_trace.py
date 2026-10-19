"""Malformed private traces cannot open any database reader."""
import pytest

from app.market_candidate_store import MarketCandidateStore


@pytest.mark.parametrize('bad', [[], [('delete', (), b'x' * 32)], [('get_decision_context', (), b'bad')],
    [('get_decision_context', (), b'x' * 32)], [('get_decision_context', ('a',) * 4, b'x' * 32)]])
def test_trace_is_closed_and_bounded_before_reading(bad, monkeypatch):
    store = MarketCandidateStore('unreachable', 'unused', object(), principal_provider=lambda: None)
    def forbidden(*a, **kw): pytest.fail('malformed trace opened a reader')
    monkeypatch.setattr(store, 'read_scope', forbidden)
    with pytest.raises(ValueError): store.verify_current_reads('tenant-1', bad)
