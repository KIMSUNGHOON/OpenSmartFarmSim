"""Actual Unix RPC/process checks; no model or farm evidence is supplied."""

from contextlib import contextmanager
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_dispatch_loop import AuthorityDispatchLoop
from app.cli_dispatch_loop import main
from app.authority_rpc import AuthorityClient, AuthorityDispatchError
from app.cli_ipc import MAX_REQUEST, receive, send
from threading import Event


def reply(state=None):
    return {'version': 1, 'ok': True, 'tenant_id': 'tenant-a', 'result': None if state is None else {
        'job_id': str(uuid4()), 'attempt': 1, 'state': state, 'reason_code': 'validated_hold',
        'capture_id': str(uuid4()), 'decision_id': str(uuid4())}}


@contextmanager
def server(path, responses):
    requested, failures, stopped = [], [], Event()
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        listener.listen(2)
        listener.settimeout(0.1)
        def serve():
            while not stopped.is_set():
                try:
                    connection, _ = listener.accept()
                except socket.timeout:
                    continue
                try:
                    with connection:
                        assert receive(connection, MAX_REQUEST) == {'version': 1, 'op': 'run_next'}
                        requested.append(time.monotonic())
                        if responses:
                            response = responses.pop(0)
                            if response is not None:
                                send(connection, response, MAX_REQUEST)
                except BaseException as error:
                    failures.append(type(error).__name__)
        worker = threading.Thread(target=serve)
        worker.start()
        try:
            yield requested
        finally:
            stopped.set()
            worker.join(timeout=3)
            assert not worker.is_alive() and not failures


def process(path, extra=()):
    return subprocess.Popen([sys.executable, '-B', '-m', 'app.cli_dispatch_loop',
        '--socket', str(path), '--authority-uid', str(os.getuid()), '--tenant', 'tenant-a',
        '--wait-seconds', '2', '--poll-seconds', '1', *extra],
        cwd=Path(__file__).parents[1],
        env={'PATH': os.defpath, 'LANG': 'C.UTF-8'}, stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def finish(child):
    try:
        return child.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        child.kill()
        child.communicate(timeout=3)
        pytest.fail('owned dispatcher did not stop')


def test_actual_process_polls_null_then_hold_and_stops_promptly(tmp_path):
    target = tmp_path/'rpc'
    with server(target, [reply(), reply('hold')]) as requested:
        child = process(target)
        try:
            deadline = time.monotonic()+5
            while len(requested)<2 and child.poll() is None and time.monotonic()<deadline:
                time.sleep(0.02)
            assert len(requested)==2 and requested[1]-requested[0]>=0.95
            started = time.monotonic()
            child.terminate()
            output, error = finish(child)
            assert child.returncode==0 and not error and time.monotonic()-started<1
            events = [json.loads(line) for line in output.splitlines()]
            assert [value['event'] for value in events]==['started','dispatch','stopped']
            assert events[1]['result']['state']=='hold' and events[1]['tenant_id']=='tenant-a'
        finally:
            if child.poll() is None:
                child.kill(); finish(child)


@pytest.mark.parametrize('fault',['lost','tenant','unclosed'])
def test_unresolved_or_unclosed_actual_reply_stops_without_another_request(tmp_path,fault):
    value=reply('unclosed' if fault=='unclosed' else 'hold')
    if fault=='lost': value=None
    if fault=='tenant': value['tenant_id']='tenant-b'
    with server(tmp_path/'rpc',[value]) as requested:
        child=process(tmp_path/'rpc')
        output,error=finish(child)
        assert child.returncode==3 and len(requested)==1
        assert json.loads(error)=={'version':1,'ok':False,'code':'authority_dispatch_unresolved'}
        events=[json.loads(line) for line in output.splitlines()]
        assert [value['event'] for value in events]==(['started','dispatch'] if fault=='unclosed' else ['started'])


@pytest.mark.parametrize('extra',[('--poll-seconds','0'),('--poll-seconds','61'),
                                ('--unexpected','fixture-secret')])
def test_configuration_rejects_without_echo_or_connection(tmp_path,extra):
    child=process(tmp_path/'absent',extra)
    output,error=finish(child)
    assert child.returncode==2 and not output and 'fixture-secret' not in error
    assert json.loads(error)=={'version':1,'ok':False,'code':'dispatcher_loop_configuration_rejected'}


def test_binding_drift_stops_before_dispatch(tmp_path,monkeypatch):
    client=AuthorityClient(tmp_path/'rpc',authority_uid=os.getuid(),tenant_id='tenant-a')
    loop=AuthorityDispatchLoop(client)
    client.tenant_id='tenant-b'
    monkeypatch.setattr(client,'run_once',lambda:pytest.fail('changed binding dispatched'))
    with pytest.raises(AuthorityDispatchError): loop.run(Event(),emit=lambda *_:None)


@pytest.mark.parametrize('interval',[True,0,61,1.0])
def test_invalid_poll_values_are_rejected(tmp_path,interval):
    client=AuthorityClient(tmp_path/'rpc',authority_uid=os.getuid(),tenant_id='tenant-a')
    with pytest.raises(ValueError): AuthorityDispatchLoop(client,poll_seconds=interval)


@pytest.mark.parametrize('field,value',[('wait_seconds',661),('wait_seconds',True),
    ('authority_uid',-1),('tenant_id',''),('socket_path',Path('relative'))])
def test_already_changed_client_is_revalidated_before_use(tmp_path,field,value):
    client=AuthorityClient(tmp_path/'rpc',authority_uid=os.getuid(),tenant_id='tenant-a')
    setattr(client,field,value)
    with pytest.raises(ValueError): AuthorityDispatchLoop(client)


@pytest.mark.parametrize('fail',[False,True])
def test_command_restores_handlers_wakeup_and_owned_descriptors(monkeypatch,tmp_path,capsys,fail):
    read_fd,write_fd=os.pipe2(os.O_NONBLOCK|os.O_CLOEXEC)
    previous=signal.set_wakeup_fd(write_fd)
    handlers={sig:signal.getsignal(sig) for sig in (signal.SIGTERM,signal.SIGINT)}
    descriptors=set(Path('/proc/self/fd').iterdir())
    def run(self,stop,*,emit):
        if fail: raise AuthorityDispatchError('fixture-secret')
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
        assert stop.is_set()
    monkeypatch.setattr(AuthorityDispatchLoop,'run',run)
    try:
        code=main(['--socket',str(tmp_path/'rpc'),'--authority-uid',str(os.getuid()),'--tenant','tenant-a'])
        captured=capsys.readouterr()
        assert code==(3 if fail else 0)
        assert 'fixture-secret' not in captured.out+captured.err
        assert {sig:signal.getsignal(sig) for sig in handlers}==handlers
        assert set(Path('/proc/self/fd').iterdir())==descriptors
        assert signal.set_wakeup_fd(write_fd)==write_fd
    finally:
        signal.set_wakeup_fd(previous)
        os.close(read_fd);os.close(write_fd)
