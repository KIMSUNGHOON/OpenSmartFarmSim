"""Foreground startup errors must not echo operator credentials or arguments."""

import json
import sys
from pathlib import Path
from types import ModuleType
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.simulation_work import main
from app.thermal_simulation_worker import ThermalSimulationWorker, SimulationResult
from uuid import UUID


@pytest.mark.parametrize('args', [[], ['--factory', 'private-secret'],
    ['--factory', 'private-secret', '--job-id', 'not-a-job'],
    ['--factory', 'private-secret:call', '--job-id', '00000000-0000-0000-0000-000000000000']])
def test_invalid_arguments_and_factories_are_masked(args, capsys):
    assert main(args) == 2
    output = capsys.readouterr()
    assert output.out == '' and 'private-secret' not in output.err
    assert json.loads(output.err)['code'] == 'simulation_startup_rejected'


def test_wrong_factory_object_is_rejected(monkeypatch, capsys):
    module = ModuleType('synthetic_sim_factory')
    module.build = lambda: object()
    monkeypatch.setitem(sys.modules, module.__name__, module)
    assert main(['--factory', module.__name__+':build', '--job-id', '00000000-0000-0000-0000-000000000000']) == 2
    assert json.loads(capsys.readouterr().err)['code'] == 'simulation_startup_rejected'


@pytest.mark.parametrize('fault', ['exception', 'unclosed'])
def test_unresolved_execution_is_masked_without_retry(monkeypatch, capsys, fault):
    worker = object.__new__(ThermalSimulationWorker)
    calls = []
    def execute(job_id):
        calls.append(job_id)
        if fault == 'exception': raise ValueError('synthetic-private-error')
        return SimulationResult(UUID(job_id), 1, 'unclosed', 'simulation_lease_lost')
    worker.run_once = execute
    module = ModuleType('synthetic_sim_factory')
    module.build = lambda: worker
    monkeypatch.setitem(sys.modules, module.__name__, module)
    assert main(['--factory', module.__name__+':build', '--job-id', '00000000-0000-0000-0000-000000000000']) == 3
    output = capsys.readouterr()
    assert output.out == '' and 'synthetic-private' not in output.err
    assert json.loads(output.err)['code'] == 'simulation_execution_unresolved' and len(calls) == 1
