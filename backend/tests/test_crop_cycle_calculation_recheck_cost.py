"""Whole-byte checks at a server guard boundary, without cached approvals."""
import inspect
import json
import os

import pytest

from app import crop_cycle_input_evidence as evidence
from test_crop_cycle_calculation_server_custody import (
    journal_setup, open_journal, close_journal, custody, engine, BUDGET)


def save(name, value):
    directory = os.environ.get('OSSF_CALCULATION_RECHECK_EVIDENCE')
    if directory:
        from pathlib import Path
        with (Path(directory)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400)
            json.dump(value, handle, sort_keys=True, indent=2); handle.write('\n')
            handle.flush(); os.fsync(handle.fileno())


def change_input(context, kind):
    target = context._directory/'root.json'
    if kind == 'block':
        target = next(path for path in context._directory.glob('*.json') if path.name != 'root.json')
    raw = target.read_bytes(); before = target.stat()
    changed = raw[:-1]+(b']' if raw[-1:] == b'}' else b'}')
    target.chmod(0o600); target.write_bytes(changed); target.chmod(0o400)
    os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns))
    assert target.stat().st_size == before.st_size and target.stat().st_mtime_ns == before.st_mtime_ns


def test_guard_checks_current_policy_once_and_whole_bytes_once(journal_setup, monkeypatch):
    journal = open_journal(journal_setup); calls = []; policies = []
    original = evidence._current_bytes
    def measured(*args, **kwargs):
        frame = inspect.currentframe().f_back; chain = []
        while frame and len(chain) < 6:
            chain.append(frame.f_code.co_name); frame = frame.f_back
        calls.append(chain)
        return original(*args, **kwargs)
    def current():
        policies.append(True); return journal_setup[-1]
    monkeypatch.setattr(evidence, '_current_bytes', measured)
    journal.current = current
    try:
        journal._guard()
        save('guard-callers.json', {'whole_byte_calls':len(calls), 'policy_calls':len(policies),
            'caller_functions':calls, 'scope':'unregistered_synthetic_exact_context_guard_only'})
        assert len(policies) == 1
        assert len(calls) == 1
        assert calls[0][:4] == ['verify', 'recheck', '_secure_input', '_guard']
    finally:
        close_journal(journal)


@pytest.mark.parametrize('when', ['entry', 'current'])
@pytest.mark.parametrize('kind', ['root', 'block'])
def test_same_size_mtime_tampering_is_rejected_before_compute(journal_setup, monkeypatch, when, kind):
    journal = open_journal(journal_setup)
    head = (journal_setup[1]/'artifact/HEAD').read_bytes()
    def current():
        change_input(journal.context, kind); return journal_setup[-1]
    if when == 'entry': change_input(journal.context, kind)
    else: journal.current = current
    monkeypatch.setattr(engine, 'advance_chunk', lambda *a, **k: pytest.fail('tampered input reached calculation'))
    try:
        with pytest.raises(custody.CalculationCustodyHold): journal.advance(BUDGET)
        assert journal.context.reader.closed and not journal.context._cache and not journal.context.reader._cache
        assert (journal_setup[1]/'artifact/HEAD').read_bytes() == head
    finally:
        close_journal(journal)


@pytest.mark.parametrize('kind', ['closed', 'code'])
def test_structural_context_failure_precedes_policy_callback(journal_setup, monkeypatch, kind):
    journal = open_journal(journal_setup)
    journal.current = lambda: pytest.fail('invalid context reached policy callback')
    if kind == 'closed': journal.context.close()
    else: monkeypatch.setattr(engine, 'CODE_SHA256', '0'*64)
    try:
        with pytest.raises(custody.CalculationCustodyHold): journal.inspect()
    finally:
        close_journal(journal)


def test_current_policy_denial_does_not_select_or_return_result(journal_setup):
    journal = open_journal(journal_setup)
    head = (journal_setup[1]/'artifact/HEAD').read_bytes()
    def denied(): raise PermissionError('own test scope withdrawn')
    journal.current = denied
    try:
        with pytest.raises(PermissionError): journal.advance(BUDGET)
        assert (journal_setup[1]/'artifact/HEAD').read_bytes() == head
    finally:
        close_journal(journal)


@pytest.mark.parametrize('when', ['before-proof', 'after-proof'])
def test_input_changed_around_proof_write_preserves_selected_head(journal_setup, monkeypatch, when):
    journal = open_journal(journal_setup)
    head = (journal_setup[1]/'artifact/HEAD').read_bytes()
    if when == 'before-proof':
        def current():
            if any(frame.function == '_publish' for frame in inspect.stack()):
                change_input(journal.context, 'block')
            return journal_setup[-1]
        journal.current = current
    else:
        original = custody._immutable
        def changed(*args, **kwargs):
            value = original(*args, **kwargs)
            if args[-1] == '.proof-': change_input(journal.context, 'block')
            return value
        monkeypatch.setattr(custody, '_immutable', changed)
    try:
        with pytest.raises(custody.CalculationCustodyHold): journal.advance(BUDGET)
        assert (journal_setup[1]/'artifact/HEAD').read_bytes() == head
        assert journal.context.reader.closed
    finally:
        close_journal(journal)


def test_input_changed_during_inspect_prevents_normal_return(journal_setup, monkeypatch):
    journal = open_journal(journal_setup); original = journal._progress
    head = (journal_setup[1]/'artifact/HEAD').read_bytes()
    def changed():
        value = original(); change_input(journal.context, 'block'); return value
    monkeypatch.setattr(journal, '_progress', changed)
    try:
        with pytest.raises(custody.CalculationCustodyHold): journal.inspect()
        assert journal.context.reader.closed and (journal_setup[1]/'artifact/HEAD').read_bytes() == head
    finally:
        close_journal(journal)
