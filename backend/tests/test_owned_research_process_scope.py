"""Real isolated process trees; no crop worker, database or browser is stopped."""
import importlib.util
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'research/owned-research-process-scope.py'
spec = importlib.util.spec_from_file_location('owned_process_scope', SCRIPT)
scope_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scope_module)

FAMILY = '''import json,os,signal,subprocess,sys,threading,time
child=None
ready=threading.Event()
stop=threading.Event()
def spawn():
 global child
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
 ready.set();stop.wait()
if sys.argv[1]=='thread':
 threading.Thread(target=spawn,daemon=True).start();ready.wait()
else:
 child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'])
def cleanup(*_):
 stop.set()
 if child.poll() is None:child.terminate()
 child.wait(timeout=3)
 raise SystemExit(0)
signal.signal(signal.SIGTERM,cleanup)
print(json.dumps({'root':os.getpid(),'child':child.pid}),flush=True)
if sys.argv[1]=='orphan':
 sys.stdin.readline();os._exit(0)
while True:time.sleep(.05)
'''


@pytest.fixture
def families():
    made = []
    def spawn(mode='normal'):
        process = subprocess.Popen([sys.executable, '-c', FAMILY, mode],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        assert select.select([process.stdout], [], [], 5)[0], 'family readiness timeout'
        ids = json.loads(process.stdout.readline())
        identities = tuple(scope_module.identity(ids[name]) for name in ('root', 'child'))
        made.append((process, identities))
        return process, identities
    yield spawn
    for process, identities in made:
        if process.poll() is None:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill(); process.wait(timeout=5)
        for item in identities:
            if scope_module.live(item):
                fd = os.pidfd_open(item.pid)
                try:
                    if scope_module.live(item):
                        signal.pidfd_send_signal(fd, signal.SIGKILL)
                finally:
                    os.close(fd)
        process.stdin.close(); process.stdout.close()


def until_stopped(scope):
    deadline = time.monotonic() + 5
    while scope.remaining() and time.monotonic() < deadline:
        time.sleep(.01)
    assert scope.remaining() == frozenset()


@pytest.mark.parametrize('mode', ['normal', 'thread'])
def test_cleanup_preserves_entire_protected_tree_and_stops_only_owned(families, mode):
    _, protected = families(mode)
    owned_process, owned = families()
    scope = scope_module.OwnedProcessScope(protected=(protected[0],))
    observed = scope.sample()
    assert {item.pid for item in (*protected, *owned)} <= observed.keys()
    assert sum(observed.values()) > 0
    sent = scope.signal_owned(signal.SIGTERM)
    assert set(sent) <= set(owned) and sent
    until_stopped(scope); owned_process.wait(timeout=5)
    assert all(scope_module.live(item) for item in protected)


def test_protected_descendant_remains_excluded_after_parent_exit(families):
    parent, protected = families('orphan')
    scope = scope_module.OwnedProcessScope(protected=(protected[0],))
    assert protected[1].pid in scope.sample()
    parent.stdin.write('exit\n'); parent.stdin.flush(); parent.wait(timeout=5)
    _, owned = families()
    assert scope.signal_owned(signal.SIGKILL)
    until_stopped(scope)
    assert scope_module.live(protected[1])
    assert not any(scope_module.live(item) for item in owned)


def test_post_exit_cleanup_keeps_protected_children(families):
    _, protected = families()
    parent, owned = families('orphan')
    scope = scope_module.OwnedProcessScope(protected=(protected[0],))
    scope.sample()
    parent.stdin.write('exit\n'); parent.stdin.flush(); parent.wait(timeout=5)
    assert scope.signal_owned(signal.SIGTERM) == (owned[1],)
    until_stopped(scope)
    assert all(scope_module.live(item) for item in protected)


def test_observation_dict_cannot_authorize_signals(families):
    _, protected = families()
    scope = scope_module.OwnedProcessScope(protected=(protected[0],))
    sample = scope.sample()
    sample[protected[1].pid] = 2 ** 40
    assert scope.signal_owned(signal.SIGTERM) == ()
    assert all(scope_module.live(item) for item in protected)


def test_incomplete_protected_walk_still_prunes_its_entire_owned_branch(families, monkeypatch):
    _, protected = families()
    original_tree = scope_module._tree
    def partial(root, excluded=()):
        records = original_tree(root, excluded)
        if root == protected[0] and not excluded:
            return {pid: row for pid, row in records.items() if pid == root.pid}
        return records
    monkeypatch.setattr(scope_module, '_tree', partial)
    scope = scope_module.OwnedProcessScope(protected=(protected[0],))
    assert scope.signal_owned(signal.SIGTERM) == ()
    assert all(scope_module.live(item) for item in protected)


def test_pid_identity_change_after_pidfd_open_refuses_signal_and_closes_fd(families, monkeypatch):
    _, owned = families()
    scope = scope_module.OwnedProcessScope()
    original_open, original_live = os.pidfd_open, scope_module.live
    opened = []
    def open_then_change(pid):
        fd = original_open(pid); opened.append(fd)
        return fd
    monkeypatch.setattr(os, 'pidfd_open', open_then_change)
    monkeypatch.setattr(scope_module, 'live', lambda item: False if opened else original_live(item))
    monkeypatch.setattr(signal, 'pidfd_send_signal', lambda *_: pytest.fail('identity changed before signal'))
    assert scope.signal_owned(signal.SIGKILL) == ()
    assert opened
    for fd in opened:
        with pytest.raises(OSError): os.fstat(fd)
    assert all(original_live(item) for item in owned)


def test_pidfd_send_failure_closes_fd_and_has_no_numeric_pid_fallback(families, monkeypatch):
    families()
    scope = scope_module.OwnedProcessScope()
    original_open = os.pidfd_open
    opened = []
    def record_open(pid):
        fd = original_open(pid); opened.append(fd); return fd
    def refused(*_):
        raise PermissionError('isolated signal refusal')
    monkeypatch.setattr(os, 'pidfd_open', record_open)
    monkeypatch.setattr(signal, 'pidfd_send_signal', refused)
    monkeypatch.setattr(os, 'kill', lambda *_: pytest.fail('numeric PID fallback'))
    with pytest.raises(PermissionError): scope.signal_owned(signal.SIGTERM)
    assert opened
    for fd in opened:
        with pytest.raises(OSError): os.fstat(fd)


def test_controller_or_stale_protected_identity_is_refused():
    with pytest.raises(PermissionError):
        scope_module.OwnedProcessScope(protected=(scope_module.identity(os.getpid()),))
    current = scope_module.identity(os.getpid())
    with pytest.raises(ValueError):
        scope_module.OwnedProcessScope(protected=(current._replace(start_ticks=current.start_ticks + 1),))


def test_pidfd_support_is_required_and_other_signals_are_refused(monkeypatch):
    scope = scope_module.OwnedProcessScope()
    with pytest.raises(ValueError): scope.signal_owned(signal.SIGSTOP)
    monkeypatch.delattr(signal, 'pidfd_send_signal')
    with pytest.raises(RuntimeError): scope_module.OwnedProcessScope()
