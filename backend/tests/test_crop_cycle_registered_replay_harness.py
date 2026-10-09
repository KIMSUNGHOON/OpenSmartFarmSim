"""The owned same-DB replay consumer imports without DB or browser side effects."""
import importlib.util
from pathlib import Path
import subprocess
import threading

import psycopg


def test_registered_replay_consumer_imports_without_starting_resources(monkeypatch):
    def forbidden(*a,**k):raise AssertionError('consumer import started a resource')
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    monkeypatch.setattr(psycopg,'connect',forbidden)
    monkeypatch.setattr(threading.Thread,'start',forbidden)
    path=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-replay.py'
    spec=importlib.util.spec_from_file_location('owned_replay_consumer',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    assert callable(module.replay)
