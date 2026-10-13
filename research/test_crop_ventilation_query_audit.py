"""The resident audit patches every existing query test target."""
import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'backend/tests'))
from crop_ventilation_query_audit import forbid
from test_crop_greenhouse_ventilation_execution_query import forbid as original_forbid
from crop_ventilation_query_audit import install, query_calls
from app.job_store import JobStore
from concurrent.futures import ThreadPoolExecutor


def test_same_targets_and_separate_advance_counters():
    class Recorder:
        def __init__(self): self.targets = {}
        def setattr(self, target, name, value): self.targets[target, name] = value
    original, current = Recorder(), Recorder()
    original_forbid(original)
    counters = forbid(current)
    assert current.targets.keys() == original.targets.keys()
    assert len(current.targets) == len(counters) == 23
    for action in current.targets.values():
        with pytest.raises(AssertionError, match='query invoked '): action()
    assert all(count == 1 for count in counters.values())


def test_query_audit_does_not_block_an_independent_request(monkeypatch):
    monkeypatch.setattr(JobStore, 'submit', lambda *args: 'independent-write')
    install(monkeypatch)
    with query_calls() as calls:
        with pytest.raises(AssertionError, match='jobs.submit'): JobStore.submit()
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(JobStore.submit).result() == 'independent-write'
    assert calls['jobs.submit'] == 1 and sum(calls.values()) == 1
    assert JobStore.submit() == 'independent-write'
