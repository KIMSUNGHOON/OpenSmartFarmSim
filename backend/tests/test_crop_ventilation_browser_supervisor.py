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
