from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from app import crop_cycle_input_evidence as evidence
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_cycle_input_stream import write

KEY = b'owned-server-evidence-test-key-32-bytes!'


def authority(key=KEY, issuer='owned-server-test', key_id='test-key-v1'):
    return evidence.InputEvidenceAuthority(PROFILES, NOTICE,
        integrity_key=key, issuer_id=issuer, key_id=key_id)


@pytest.fixture
def packet(tmp_path):
    directory = tmp_path/'inputs'
    receipt = write(directory)
    for path in directory.iterdir():
        path.chmod(0o400)
    return directory, receipt['root_sha256']


def test_original_full_check_then_current_bytes_without_reparsing(packet, monkeypatch):
    directory, root = packet
    before = len(os.listdir('/proc/self/fd'))
    server = authority()
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('RHS called'))
    with inputs.open_input_packet(directory, root, **PROFILES) as reader:
        original = engine.prepare_context(reader, **PROFILES)
        expected = original.manifest
        original_initial = original._initial
    calls = []
    preflight = inputs.InputPacket._preflight
    def checked(reader):
        calls.append('full-check')
        return preflight(reader)
    monkeypatch.setattr(inputs.InputPacket, '_preflight', checked)
    raw = server.issue(directory, root)
    assert calls == ['full-check']
    monkeypatch.setattr(inputs, 'open_input_packet', lambda *a, **k: pytest.fail('full parser called on verify'))
    checked = server.verify(directory, root, raw)
    assert type(checked) is evidence.VerifiedInputEvidence
    assert checked.context['manifest'] == expected
    assert inputs._canonical(checked.context['initial']) == original_initial
    assert checked.context['plan']['packet_referenced_bytes'] == checked.referenced_bytes
    assert checked.evidence_sha256 == sha256(raw).hexdigest()
    assert checked.rights_or_gate_approval is False
    returned = checked.context
    returned['seed'][0] += 1.0
    assert returned != checked.context
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('change', ['root', 'blob', 'missing', 'file-symlink', 'directory-symlink',
    'extra', 'writable', 'hardlink', 'directory-mode'])
def test_current_physical_input_failure_never_reuses_proof(packet, tmp_path, change):
    directory, root = packet
    server = authority()
    raw = server.issue(directory, root)
    target = next(path for path in directory.iterdir() if path.name != 'root.json')
    if change == 'root':
        target = directory/'root.json'
    if change in ('root', 'blob'):
        old = target.read_bytes()
        target.chmod(0o600); target.write_bytes(old+b' '); target.chmod(0o400)
    elif change == 'missing':
        target.unlink()
    elif change == 'file-symlink':
        outside = tmp_path/'outside'; outside.write_bytes(target.read_bytes())
        target.unlink(); target.symlink_to(outside)
    elif change == 'directory-symlink':
        directory.rename(tmp_path/'original')
        directory.symlink_to(tmp_path/'original', target_is_directory=True)
    elif change == 'extra':
        (directory/'extra.json').write_bytes(b'[]')
    elif change == 'writable':
        target.chmod(0o600)
    elif change == 'hardlink':
        os.link(target, tmp_path/'second-link')
    else:
        directory.chmod(0o755)
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(evidence.InputEvidenceHold):
        server.verify(directory, root, raw)
    assert len(os.listdir('/proc/self/fd')) == before


@pytest.mark.parametrize('change', ['payload', 'mac', 'wrong-key', 'wrong-key-id', 'wrong-issuer',
    'wrong-version', 'wrong-root', 'noncanonical', 'duplicate', 'NaN', 'oversize'])
def test_untrusted_or_mismatched_evidence_is_rejected(packet, change):
    directory, root = packet
    server = authority()
    raw = server.issue(directory, root)
    value = json.loads(raw)
    if change == 'payload':
        value['payload']['context']['seed'][0] += 1.0; raw = inputs._canonical(value)
    elif change == 'mac':
        value['hmac_sha256'] = '0'*64; raw = inputs._canonical(value)
    elif change == 'wrong-key':
        server = authority(key=b'other-owned-test-key-32-bytes-long!')
    elif change == 'wrong-key-id':
        server = authority(key_id='rotated-key')
    elif change == 'wrong-issuer':
        server = authority(issuer='other-server')
    elif change == 'wrong-version':
        value['payload']['version'] = 'unknown'
        value['hmac_sha256'] = hmac.new(KEY, evidence.DOMAIN+inputs._canonical(value['payload']), 'sha256').hexdigest()
        raw = inputs._canonical(value)
    elif change == 'wrong-root':
        root = '0'*64
    elif change == 'noncanonical':
        raw += b'\n'
    elif change == 'duplicate':
        raw = b'{"payload":{},"payload":{},"hmac_sha256":""}'
    elif change == 'NaN':
        raw = b'{"payload":NaN,"hmac_sha256":""}'
    else:
        raw = b' '*(evidence.MAX_EVIDENCE_BYTES+1)
    with pytest.raises(evidence.InputEvidenceHold):
        server.verify(directory, root, raw)


def test_failed_preflight_does_not_issue_and_closes_reader(packet, monkeypatch):
    directory, root = packet
    before = len(os.listdir('/proc/self/fd'))
    def fail(reader):
        raise inputs.CycleInputRejected('own failed full check')
    monkeypatch.setattr(inputs.InputPacket, '_preflight', fail)
    with pytest.raises(evidence.InputEvidenceHold):
        authority().issue(directory, root)
    assert len(os.listdir('/proc/self/fd')) == before


def test_issue_checks_owned_readonly_bytes_before_legacy_parser(packet, monkeypatch):
    directory, root = packet
    server = authority()
    (directory/'root.json').chmod(0o600)
    monkeypatch.setattr(inputs, 'open_input_packet', lambda *a, **k: pytest.fail('untrusted ownership parsed'))
    with pytest.raises(evidence.InputEvidenceHold): server.issue(directory, root)


@pytest.mark.parametrize('change', ['seed', 'clock-prefix', 'context-fields'])
def test_authenticated_but_invalid_context_cannot_be_a_typed_evidence(packet, change):
    directory, root = packet
    server = authority(); value = json.loads(server.issue(directory, root))
    context = value['payload']['context']
    if change == 'seed': context['seed'][0] += 1.0
    elif change == 'clock-prefix': context['initial_clock']['prefix']['numerator'] = '999'
    else: context['extra'] = 'unknown'
    value['hmac_sha256'] = hmac.new(KEY, evidence.DOMAIN+inputs._canonical(value['payload']), 'sha256').hexdigest()
    with pytest.raises(evidence.InputEvidenceHold): server.verify(directory, root, inputs._canonical(value))


def test_changed_dependency_on_disk_is_rejected_before_byte_reuse(packet, tmp_path, monkeypatch):
    directory, root = packet
    server = authority(); raw = server.issue(directory, root)
    changed = tmp_path/'changed-input.py'; changed.write_text('owned changed input parser')
    monkeypatch.setattr(inputs, '__file__', str(changed))
    with pytest.raises(evidence.InputEvidenceHold): server.verify(directory, root, raw)


def test_changed_source_or_server_configuration_requires_new_evidence(packet, tmp_path, monkeypatch):
    directory, root = packet
    server = authority(); raw = server.issue(directory, root)
    changed = tmp_path/'changed.py'; changed.write_text('owned changed code')
    monkeypatch.setattr(evidence, '__file__', str(changed))
    with pytest.raises(evidence.InputEvidenceHold): server.verify(directory, root, raw)
    monkeypatch.undo()
    server.key_id = 'drifted'
    with pytest.raises(evidence.InputEvidenceHold): server.verify(directory, root, raw)


@pytest.mark.parametrize('key,issuer,key_id', [(None, 'server', 'key'), (b'short', 'server', 'key'),
    (KEY, '', 'key'), (KEY, 'server', '../key')])
def test_missing_secret_or_invalid_configuration_is_a_hold(key, issuer, key_id):
    with pytest.raises(evidence.InputEvidenceHold): authority(key, issuer, key_id)


def test_separate_process_retained_key_reuses_exact_context(packet, tmp_path):
    directory, root = packet
    raw = authority().issue(directory, root)
    private_key = tmp_path/'private-key'; private_key.write_bytes(KEY); private_key.chmod(0o400)
    source = '''
from pathlib import Path
import json,sys
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from test_crop_cycle_artifact import PROFILES,NOTICE
server=InputEvidenceAuthority(PROFILES,NOTICE,integrity_key=Path(sys.argv[3]).read_bytes(),
 issuer_id='owned-server-test',key_id='test-key-v1')
result=server.verify(sys.argv[1],sys.argv[2],sys.stdin.buffer.read())
print(json.dumps({'context':result.context,'sha256':result.evidence_sha256,'approval':result.rights_or_gate_approval}))
'''
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).parents[1])+os.pathsep+str(Path(__file__).parent))
    child = subprocess.run([sys.executable, '-c', source, str(directory), root, str(private_key)],
        input=raw, capture_output=True, timeout=30, env=env)
    assert child.returncode == 0, child.stderr.decode()
    actual = json.loads(child.stdout)
    assert actual['context'] == authority().verify(directory, root, raw).context
    assert actual['sha256'] == sha256(raw).hexdigest() and actual['approval'] is False
