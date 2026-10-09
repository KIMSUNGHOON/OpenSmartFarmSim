"""Real isolated process trees; no crop worker, database or browser is stopped."""
import importlib.util
import errno
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
def families(request):
    made = []
    def spawn(mode='normal'):
        process = subprocess.Popen([sys.executable, '-c', FAMILY, mode],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        assert select.select([process.stdout], [], [], 5)[0], 'family readiness timeout'
        ids = json.loads(process.stdout.readline())
        identities = tuple(scope_module.identity(ids[name]) for name in ('root', 'child'))
        made.append((process, identities))
        return process, identities
    preexisting = ()
    if getattr(request, 'param', None):
        _, preexisting = spawn(request.param)
    controller = scope_module.identity(os.getpid())
    baseline = tuple(item for item, _ in scope_module._tree(controller).values() if item != controller)
    def new_scope(protected=()):
        return scope_module.OwnedProcessScope(protected=(*baseline, *protected))
    spawn.scope = new_scope
    spawn.preexisting = preexisting
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
                fd = scope_module._pidfd_open(item.pid)
                try:
                    if scope_module.live(item):
                        scope_module._pidfd_send_signal(fd, signal.SIGKILL)
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
    scope = families.scope(protected=(protected[0],))
    observed = scope.sample()
    assert {item.pid for item in (*protected, *owned)} <= observed.keys()
    assert sum(observed.values()) > 0
    sent = scope.signal_owned(signal.SIGTERM)
    assert set(sent) <= set(owned) and sent
    until_stopped(scope); owned_process.wait(timeout=5)
    assert all(scope_module.live(item) for item in protected)


@pytest.mark.parametrize('families', ['normal', 'thread'], indirect=True)
def test_preexisting_family_is_protected_and_only_later_owned_family_is_stopped(families):
    owned_process, owned = families()
    before = len(os.listdir('/proc/self/fd'))
    scope = families.scope()
    assert {item.pid for item in (*families.preexisting, *owned)} <= scope.sample().keys()
    sent = scope.signal_owned(signal.SIGTERM)
    assert sent and set(sent) <= set(owned)
    until_stopped(scope); owned_process.wait(timeout=5)
    assert all(scope_module.live(item) for item in families.preexisting)
    assert len(os.listdir('/proc/self/fd')) == before


def test_protected_descendant_remains_excluded_after_parent_exit(families):
    parent, protected = families('orphan')
    scope = families.scope(protected=(protected[0],))
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
    scope = families.scope(protected=(protected[0],))
    scope.sample()
    parent.stdin.write('exit\n'); parent.stdin.flush(); parent.wait(timeout=5)
    assert scope.signal_owned(signal.SIGTERM) == (owned[1],)
    until_stopped(scope)
    assert all(scope_module.live(item) for item in protected)


def test_observation_dict_cannot_authorize_signals(families):
    _, protected = families()
    scope = families.scope(protected=(protected[0],))
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
    scope = families.scope(protected=(protected[0],))
    assert scope.signal_owned(signal.SIGTERM) == ()
    assert all(scope_module.live(item) for item in protected)


def test_pid_identity_change_after_pidfd_open_refuses_signal_and_closes_fd(families, monkeypatch):
    _, owned = families()
    scope = families.scope()
    original_open, original_live = scope_module._pidfd_open, scope_module.live
    opened = []
    def open_then_change(pid):
        fd = original_open(pid); opened.append(fd)
        return fd
    monkeypatch.setattr(scope_module, '_pidfd_open', open_then_change)
    monkeypatch.setattr(scope_module, 'live', lambda item: False if opened else original_live(item))
    monkeypatch.setattr(scope_module, '_pidfd_send_signal', lambda *_: pytest.fail('identity changed before signal'))
    assert scope.signal_owned(signal.SIGKILL) == ()
    assert opened
    for fd in opened:
        with pytest.raises(OSError): os.fstat(fd)
    assert all(original_live(item) for item in owned)


def test_pidfd_send_failure_closes_fd_and_has_no_numeric_pid_fallback(families, monkeypatch):
    families()
    scope = families.scope()
    original_open = scope_module._pidfd_open
    opened = []
    def record_open(pid):
        fd = original_open(pid); opened.append(fd); return fd
    def refused(*_):
        raise PermissionError('isolated signal refusal')
    monkeypatch.setattr(scope_module, '_pidfd_open', record_open)
    monkeypatch.setattr(scope_module, '_pidfd_send_signal', refused)
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
    monkeypatch.delattr(signal, 'pidfd_send_signal', raising=False)
    def unavailable():
        raise RuntimeError('Linux pidfd support is required')
    import ctypes
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **k: unavailable())
    with pytest.raises(RuntimeError): scope_module.OwnedProcessScope()


def test_python_pair_is_preferred_without_library_loading(monkeypatch):
    import ctypes
    calls = []
    monkeypatch.setattr(os, 'pidfd_open', lambda pid: calls.append(('open', pid)) or 37, raising=False)
    monkeypatch.setattr(signal, 'pidfd_send_signal', lambda fd, sig: calls.append(('send', fd, sig)), raising=False)
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **k: pytest.fail('unexpected libc load'))
    assert scope_module._pidfd_open(123) == 37
    assert scope_module._pidfd_send_signal(37, signal.SIGTERM) is None
    assert calls == [('open', 123), ('send', 37, signal.SIGTERM)]


@pytest.mark.parametrize('missing', ['open', 'send', 'both'])
def test_real_libc_pidfd_signal0_and_owned_cleanup_preserve_protected_tree(families, monkeypatch, missing):
    _, protected = families('thread')
    owned_process, owned = families()
    if missing in ('open', 'both'):monkeypatch.delattr(os, 'pidfd_open', raising=False)
    if missing in ('send', 'both'):monkeypatch.delattr(signal, 'pidfd_send_signal', raising=False)
    before = len(os.listdir('/proc/self/fd'))
    fd = scope_module._pidfd_open(owned[0].pid)
    try:
        assert not os.get_inheritable(fd)
        scope_module._pidfd_send_signal(fd, 0)
        assert all(scope_module.live(item) for item in (*protected, *owned))
    finally:
        os.close(fd)
    assert len(os.listdir('/proc/self/fd')) == before
    scope = families.scope(protected=(protected[0],))
    sent = scope.signal_owned(signal.SIGTERM)
    assert sent and set(sent) <= set(owned)
    until_stopped(scope); owned_process.wait(timeout=5)
    assert all(scope_module.live(item) for item in protected)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('fault', ['open-symbol', 'send-symbol', 'load'])
def test_missing_libc_support_fails_closed_without_numeric_pid_signal(monkeypatch, fault):
    import ctypes
    from types import SimpleNamespace
    monkeypatch.delattr(os, 'pidfd_open', raising=False)
    monkeypatch.delattr(signal, 'pidfd_send_signal', raising=False)
    monkeypatch.setattr(os, 'kill', lambda *_: pytest.fail('numeric PID fallback'))
    def load(*args, **kwargs):
        assert args == (None,) and kwargs == {'use_errno': True}
        if fault == 'load':raise OSError('owned unavailable libc')
        return SimpleNamespace(**{'pidfd_send_signal' if fault == 'open-symbol' else 'pidfd_open': lambda *_: 0})
    monkeypatch.setattr(ctypes, 'CDLL', load)
    with pytest.raises(RuntimeError, match='^Linux pidfd support is required$'):
        scope_module.OwnedProcessScope()


@pytest.mark.parametrize('operation', ['open', 'send'])
@pytest.mark.parametrize('error', [errno.ESRCH, errno.EPERM, errno.ENOSYS, errno.EBADF])
def test_libc_errors_keep_errno_and_explicit_zero_flags(monkeypatch, operation, error):
    import ctypes
    from types import SimpleNamespace
    monkeypatch.delattr(os, 'pidfd_open', raising=False)
    monkeypatch.delattr(signal, 'pidfd_send_signal', raising=False)
    monkeypatch.setattr(os, 'kill', lambda *_: pytest.fail('numeric PID fallback'))
    calls = []
    def failed(*args):
        calls.append(args);ctypes.set_errno(error);return -1
    library = SimpleNamespace(pidfd_open=failed, pidfd_send_signal=failed)
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **k: library)
    with pytest.raises(OSError) as caught:
        if operation == 'open':scope_module._pidfd_open(123)
        else:scope_module._pidfd_send_signal(37, signal.SIGTERM)
    assert caught.value.errno == error
    if error == errno.ESRCH:assert type(caught.value) is ProcessLookupError
    if error == errno.EPERM:assert type(caught.value) is PermissionError
    assert calls == ([(123, 0)] if operation == 'open' else [(37, signal.SIGTERM, None, 0)])
    assert library.pidfd_open.restype is ctypes.c_int


def test_python_call_failure_does_not_try_another_backend(monkeypatch):
    import ctypes
    def refused(*_):raise PermissionError('owned pidfd refusal')
    monkeypatch.setattr(os, 'pidfd_open', refused, raising=False)
    monkeypatch.setattr(signal, 'pidfd_send_signal', refused, raising=False)
    monkeypatch.setattr(ctypes, 'CDLL', lambda *a, **k: pytest.fail('failure retried through libc'))
    with pytest.raises(PermissionError):scope_module._pidfd_open(123)
    with pytest.raises(PermissionError):scope_module._pidfd_send_signal(37, signal.SIGTERM)


@pytest.mark.parametrize('error', [errno.ESRCH, errno.EPERM, errno.ENOSYS])
def test_libc_signal_error_closes_real_owned_pidfds_without_retry(families, monkeypatch, error):
    import ctypes
    _, owned = families()
    before = len(os.listdir('/proc/self/fd'))
    with monkeypatch.context() as patch:
        patch.delattr(os, 'pidfd_open', raising=False)
        patch.delattr(signal, 'pidfd_send_signal', raising=False)
        opened, _, libc = scope_module._pidfd_backend()
        assert libc is True
        calls = []
        def refused(fd, sig, info, flags):
            calls.append((fd, sig, info, flags));ctypes.set_errno(error);return -1
        patch.setattr(scope_module, '_pidfd_backend', lambda: (opened, refused, True))
        patch.setattr(os, 'kill', lambda *_: pytest.fail('numeric PID fallback'))
        scope = families.scope()
        if error == errno.ESRCH:assert scope.signal_owned(signal.SIGTERM) == ()
        else:
            with pytest.raises(OSError) as caught:scope.signal_owned(signal.SIGTERM)
            assert caught.value.errno == error
        assert calls and all(row[1:] == (signal.SIGTERM, None, 0) for row in calls)
        for fd, *_ in calls:
            with pytest.raises(OSError):os.fstat(fd)
        assert all(scope_module.live(item) for item in owned)
        assert len(os.listdir('/proc/self/fd')) == before


def test_fresh_import_does_not_load_libc_or_open_descriptors():
    code = '''import ctypes,importlib.util,json,os,sys
def forbidden(*a,**k):raise AssertionError('libc loaded during import')
ctypes.CDLL=forbidden
before=len(os.listdir('/proc/self/fd'))
spec=importlib.util.spec_from_file_location('owned_import',sys.argv[1])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert len(os.listdir('/proc/self/fd'))==before
print(json.dumps({'FD_before_after':[before,before],'libc_loaded':False}))
'''
    child = subprocess.run([sys.executable, '-c', code, str(SCRIPT)], capture_output=True, text=True, timeout=10)
    assert child.returncode == 0 and child.stderr == ''
    assert json.loads(child.stdout)['libc_loaded'] is False
