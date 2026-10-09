"""Operator boundary errors remain bounded and precede untrusted imports."""

from pathlib import Path
import json
import sys
import types
from uuid import UUID

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import break_even_verify_work
from app.break_even_verification_worker import BreakEvenVerificationWorker, BreakEvenVerificationOutcome


ID = '00000000-0000-4000-8000-000000000001'


@pytest.mark.parametrize('args', [[], ['--factory', 'unsafe/path:build', '--job-id', ID],
    ['--factory', 'module:build', '--job-id', 'invalid'],
    ['--factory', 'module:build', '--job-id', ID.upper().replace('00000001', 'ABCDEF01')],
    ['--factory', 'module:build', '--job-id', ID, '--unknown', 'private']])
def test_configuration_rejection_does_not_import_or_leak(args, monkeypatch, capsys):
    def forbidden(*_): raise AssertionError('must not import')
    monkeypatch.setattr(break_even_verify_work.importlib, 'import_module', forbidden)
    assert break_even_verify_work.main(args) == 2
    out = capsys.readouterr()
    assert not out.out and json.loads(out.err)['code'] == 'break_even_verification_startup_rejected'
    assert 'private' not in out.err


@pytest.mark.parametrize('case', ['wrong_type', 'exception', 'unclosed', 'success', 'none'])
def test_factory_worker_and_outcome_boundaries(case, monkeypatch, capsys):
    worker = object() if case == 'wrong_type' else BreakEvenVerificationWorker.__new__(BreakEvenVerificationWorker)
    if case != 'wrong_type':
        def run(job_id):
            assert job_id == ID
            if case == 'exception': raise RuntimeError('private exception detail')
            if case == 'none': return None
            return BreakEvenVerificationOutcome(UUID(ID), 1,
                'unclosed' if case == 'unclosed' else 'succeeded', 'completed', ID)
        worker.run_once = run
    monkeypatch.setattr(break_even_verify_work.importlib, 'import_module', lambda *_: types.SimpleNamespace(build=lambda: worker))
    code = break_even_verify_work.main(['--factory', 'module:build', '--job-id', ID])
    output = capsys.readouterr()
    expected = 2 if case == 'wrong_type' else 3 if case in ('exception', 'unclosed') else 0
    assert code == expected and 'private' not in output.out+output.err
    if not expected:
        data = json.loads(output.out)
        assert data['ok'] and not output.err
        if case == 'success': assert data['result']['job_id'] == ID
        else: assert data['result'] is None
