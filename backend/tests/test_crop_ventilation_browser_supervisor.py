"""Exercise private rights handshakes and cleanup without a second supervisor."""
import importlib.util
import json
from pathlib import Path
import os

import pytest

spec = importlib.util.spec_from_file_location('browser_supervisor',
    Path(__file__).resolve().parents[2]/'research/crop-ventilation-browser-supervisor.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


@pytest.fixture
def inputs(tmp_path):
    source = 'a'*64
    paths = {k:tmp_path/(k+'.json') for k in ('request','access','rights')}
    for key,value in [('request',{'input':{'source_sha256':source}}),
                      ('access',{'token':'private-owned-test'}),
                      ('rights',{source:True,'b'*64:False})]:
        paths[key].write_text(json.dumps(value,indent=2)+'\n'); paths[key].chmod(0o600)
    evidence = module.BrowserEvidence(tmp_path/'browser', **paths,
        driver=tmp_path/'driver.mjs',playwright=tmp_path/'playwright.mjs',
        mode='profile',origin='http://127.0.0.1:5174',job_id='owned-test')
    return evidence,paths,source


def test_revoke_restore_preserves_original_bytes_and_unrelated_source(inputs):
    evidence,paths,source = inputs
    original=paths['rights'].read_bytes()
    for event,expected in [('rights-revoke',False),('rights-restore',True)]:
        (evidence.directory/event).touch(mode=0o600)
        evidence.poll()
        assert json.loads(paths['rights'].read_bytes())=={source:expected,'b'*64:False}
        assert (evidence.directory/(event+'-ack')).read_bytes()==b''
        evidence.poll()
    evidence.close()
    assert paths['rights'].read_bytes()==original


def test_aborted_browser_restores_rights_in_owning_supervisor(inputs):
    evidence,paths,_=inputs; original=paths['rights'].read_bytes()
    with pytest.raises(RuntimeError,match='owned browser failure'):
        try:
            (evidence.directory/'rights-revoke').touch(mode=0o600); evidence.poll()
            raise RuntimeError('owned browser failure')
        finally:
            evidence.close()
    assert paths['rights'].read_bytes()==original
    assert not list(paths['rights'].parent.glob('.browser-owned-*'))


@pytest.mark.parametrize('kind',['symlink','payload','shared_link'])
def test_rights_request_cannot_replace_private_files(inputs,kind):
    evidence,paths,_=inputs;original=paths['rights'].read_bytes()
    event=evidence.directory/'rights-revoke'
    if kind=='symlink':event.symlink_to(paths['access'])
    elif kind=='shared_link':os.link(paths['access'],event)
    else:event.write_text('unexpected');event.chmod(0o600)
    with pytest.raises(ValueError,match='rights event rejected'):evidence.poll()
    assert paths['rights'].read_bytes()==original


def test_profile_command_has_no_secret_argument_or_python_wrapper(inputs):
    evidence,_,_=inputs
    assert 'private-owned-test' not in ' '.join(evidence.command)
    assert evidence.command[3]=='node' and 'python' not in evidence.command
    assert evidence.context.stat().st_mode&0o777==0o600


def test_memory_evidence_is_closed_and_bounded(inputs):
    evidence,_,_=inputs
    values=dict.fromkeys(('rss','heapUsed','heapTotal','external','arrayBuffers'),10)
    path=evidence.directory/'node-memory.private.json'
    module.atomic_bytes(path,json.dumps({'stage':'running','memory':values}).encode())
    assert evidence.node_memory()['memory']==values
    values['token']='must-not-be-recorded'
    module.atomic_bytes(path,json.dumps({'stage':'running','memory':values}).encode())
    with pytest.raises(ValueError,match='memory evidence rejected'):evidence.node_memory()


@pytest.mark.parametrize('exit_code',[0,7])
def test_direct_browser_exit_restores_rights_and_keeps_runtime_children(inputs,exit_code):
    import subprocess
    import sys
    import time
    import signal
    evidence,paths,_=inputs; original=paths['rights'].read_bytes()
    spec=importlib.util.spec_from_file_location('browser_child_owned_scope',
        Path(__file__).resolve().parents[2]/'research/owned-research-process-scope.py')
    processes=importlib.util.module_from_spec(spec); spec.loader.exec_module(processes)
    services=[subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']) for _ in range(3)]
    identities=[processes.identity(child.pid) for child in services]
    driver=evidence.directory/'failure.py'
    driver.write_text("import pathlib,sys,time\np=pathlib.Path(sys.argv[1]);(p/'rights-revoke').touch(mode=0o600)\nwhile not (p/'rights-revoke-ack').exists():time.sleep(.01)\nsys.exit("+str(exit_code)+")\n")
    evidence.command=[sys.executable,str(driver),str(evidence.directory)]
    child=module.BrowserChild(evidence,processes=processes,env=os.environ.copy())
    try:
        deadline=time.monotonic()+5; result=None
        while result is None:
            assert time.monotonic()<deadline
            result=child.poll();time.sleep(.01)
        assert result['actual_child_exit']==exit_code and result['current_rights_restored']
        assert result['log_closed'] and not result['owned_remaining']
        assert paths['rights'].read_bytes()==original
        assert all(processes.live(identity) for identity in identities)
    finally:
        child.finish('test_cleanup')
        for identity,service in zip(identities,services):
            fd=processes._pidfd_open(identity.pid)
            try:processes._pidfd_send_signal(fd,signal.SIGTERM)
            finally:os.close(fd)
            service.wait(timeout=5)


@pytest.mark.parametrize('invalid_event',[False,True])
def test_browser_abort_stops_only_its_remembered_tree_and_restores_rights(inputs,invalid_event):
    import subprocess
    import sys
    import time
    import signal
    evidence,paths,_=inputs; original=paths['rights'].read_bytes()
    spec=importlib.util.spec_from_file_location('browser_abort_scope',
        Path(__file__).resolve().parents[2]/'research/owned-research-process-scope.py')
    processes=importlib.util.module_from_spec(spec);spec.loader.exec_module(processes)
    sibling=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)'])
    identity=processes.identity(sibling.pid);before=len(os.listdir('/proc/self/fd'))
    driver=evidence.directory/'waiting.py'
    descendant="import pathlib,signal,sys,time;"+("signal.signal(signal.SIGTERM,signal.SIG_IGN);" if invalid_event else '')+"pathlib.Path(sys.argv[1]).touch(mode=0o600);time.sleep(30)"
    driver.write_text("import pathlib,subprocess,sys,time\np=pathlib.Path(sys.argv[1]);subprocess.Popen([sys.executable,'-c',"+repr(descendant)+",str(p/'descendant-ready')]);(p/'rights-revoke').touch(mode=0o600)\nwhile not (p/'rights-revoke-ack').exists():time.sleep(.01)\n(p/'waiting').touch(mode=0o600)\ntime.sleep(30)\n")
    evidence.command=[sys.executable,str(driver),str(evidence.directory)]
    child=module.BrowserChild(evidence,processes=processes,env=os.environ.copy())
    try:
        deadline=time.monotonic()+5
        while not ((evidence.directory/'waiting').exists() and (evidence.directory/'descendant-ready').exists()):
            assert time.monotonic()<deadline;assert child.poll() is None;time.sleep(.01)
        child.remember();assert len(child.identities)==2
        if invalid_event:
            (evidence.directory/'rights-restore').write_text('invalid')
            with pytest.raises(ValueError):child.poll()
        result=child.finish('invalid_event' if invalid_event else 'requested_stop')
        assert result['current_rights_restored'] and result['log_closed']
        assert result['forced_kill']==invalid_event
        assert not result['owned_remaining'] and processes.live(identity)
        assert paths['rights'].read_bytes()==original
        assert len(os.listdir('/proc/self/fd'))==before
    finally:
        child.finish('test_cleanup');fd=processes._pidfd_open(identity.pid)
        try:processes._pidfd_send_signal(fd,signal.SIGTERM)
        finally:os.close(fd)
        sibling.wait(timeout=5)
