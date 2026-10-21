"""Completed numeric signatures and query controls; farm callbacks are unit doubles."""
from copy import deepcopy
from hashlib import sha256
import hmac
import importlib
import json
import os
from pathlib import Path

import pytest

from app.content_access import ContentAccess
from app import crop_morphology_farm_binding as farms
import test_crop_morphology_farm_binding as controls
import test_crop_morphology_input_evidence as inputs


KEY = b'owned-morphology-result-software-key-32!'
PUBLIC = inputs.ROOT/'web/public/morphology-rational-replay'


@pytest.fixture
def prepared(tmp_path, monkeypatch, request):
    model = importlib.import_module('app.crop_morphology_signed_artifact')
    producer = importlib.import_module('app.crop_morphology_signed_producer')
    shell, body, registration, packet = controls.prepared(farms)
    if getattr(request, 'param', None) == 'invalid-initial':
        program, source = json.loads(packet['program_raw']), json.loads(packet['source_raw'])
        program['program_id'] = 'owned-invalid-initial-length-control'
        program['initial_state']['internodes'][0]['length_state']['length']['value'] *= 2
        raw = inputs.canonical(program); digest = sha256(raw).hexdigest()
        source['program_sha256'] = source['provenance']['raw_sha256'] = digest
        source['provenance']['scope']['product_id'] = program['program_id']
        source_raw = inputs.reidentify(source); source_authority = inputs.authority(farms.evidence, source_raw)
        evidence_raw = source_authority.issue(**inputs.arguments(raw, source_raw))
        packet.update(program_raw=raw, source_raw=source_raw, evidence_raw=evidence_raw)
        shell.input_authority = source_authority
        body['input'].update(program_id=program['program_id'], program_sha256=digest,
            source_sha256=sha256(source_raw).hexdigest(), evidence_sha256=sha256(evidence_raw).hexdigest())
        body['rights']['input_source_sha256'] = body['input']['source_sha256']
    source = shell._input(body, registration, **packet)
    binding = {'version': farms.VERSION, 'scope': 'synthetic_morphology_input_binding_only', 'G0_G4': 'not_assessed',
        'rights_or_gate_approval': False, 'numerical_initial_state_validation': False, 'tenant_id': 'tenant-1',
        'request': body, 'registration': {**registration, 'profile_applicability': 'unvalidated_for_registered_crop'}, 'input': source,
        'rights_policy_version': 'owned-control-only', 'binding_code_sha256': farms.CODE_SHA256,
        'binding_dependency_sha256': farms.DEPENDENCY_SHA256}
    binding_raw = inputs.canonical(binding); state = {'allowed': True, 'prepare': 0, 'current': []}
    def checked(tenant, request, expected=None, **kw):
        if not state['allowed']: raise farms.MorphologyFarmBindingHold('owned current revoked')
        if tenant != 'tenant-1': raise PermissionError('foreign tenant')
        assert request == inputs.canonical(body)
        assert {k: kw[k] for k in packet} == packet
        if expected is None: state['prepare'] += 1
        else:
            assert expected == binding_raw
            state['current'].append(kw.get('write', False))
        return binding_raw
    monkeypatch.setattr(farms.MorphologyFarmBinding, '_binding', lambda self: None)
    monkeypatch.setattr(farms.MorphologyFarmBinding, 'prepare', lambda self, tenant, request, **kw: checked(tenant, request, **kw))
    monkeypatch.setattr(farms.MorphologyFarmBinding, 'current', lambda self, tenant, request, expected, **kw: checked(tenant, request, expected, **kw))
    shell._fixed = ('owned-unit-double',)
    authority = model.MorphologyArtifactAuthority(shell, directory=tmp_path/'signed', access=ContentAccess(os.getuid(), os.getgid()),
        integrity_key=KEY, issuer_id='owned-software', key_id='owned-result-key')
    return model, producer, authority, body, packet, state


def publish(p):
    _, producer, authority, body, packet, _ = p
    return producer.produce_registered_morphology(authority, 'tenant-1', inputs.canonical(body), **packet)


def test_actual_producer_original_root_all_frames_and_query_calculation_zero(prepared, monkeypatch):
    model, producer, authority, body, packet, state = prepared
    numerical = importlib.import_module('app.crop_rational_morphology_artifact_producer')
    previous = numerical.produce_rational_morphology_artifact; calls = []
    def calculate(*a, **kw):
        calls.append(1)
        return previous(*a, **kw)
    monkeypatch.setattr(numerical, 'produce_rational_morphology_artifact', calculate)
    result_id = publish(prepared); assert calls == [1] and state['prepare'] == 1
    assert state['current'] and all(state['current'])
    original = json.loads((PUBLIC/'root.json').read_bytes())
    assert KEY not in (authority.directory/result_id).read_bytes()
    monkeypatch.setattr(numerical, 'produce_rational_morphology_artifact', lambda *a, **kw: pytest.fail('query calculated'))
    manifest = authority.read_manifest('tenant-1', result_id)
    assert manifest['result_sha256'] == result_id and manifest['manifest'] == original
    assert manifest['numerical_root_sha256'] == sha256(inputs.canonical(original)).hexdigest()
    assert manifest['farm'] == body['farm'] and manifest['gates'] == 'not_assessed'
    assert manifest['profile_applicability'] == 'unvalidated_for_registered_crop'
    for index in range(12):
        frame = authority.read_frame('tenant-1', result_id, index=index)
        original_raw = (PUBLIC/f'frame-{index}.json').read_bytes()
        assert inputs.canonical(frame['frame']) == original_raw
        assert frame['frame_sha256'] == sha256(original_raw).hexdigest()
        assert frame['calculated_at'] == manifest['calculated_at'] and frame['result_sha256'] == result_id
    assert calls == [1] and state['current'][-2:] == [False, False]


@pytest.mark.parametrize('change', ['hmac', 'issuer', 'key-id', 'tenant', 'scope', 'gates', 'code', 'root', 'binding', 'time', 'extra'])
def test_signed_proof_changes_hold_even_with_known_fixture_key(prepared, change):
    model, _, authority, _, _, _ = prepared; result_id = publish(prepared)
    doc = json.loads((authority.directory/result_id).read_bytes()); payload = doc['payload']
    if change == 'hmac': doc['hmac_sha256'] = '0'*64
    elif change == 'issuer': payload['issuer_id'] = 'other'
    elif change == 'key-id': payload['key_id'] = 'other'
    elif change == 'tenant': payload['tenant_id'] = 'other'
    elif change == 'scope': payload['scope'] = 'validated_crop'
    elif change == 'gates': payload['gates'] = 'G1'
    elif change == 'code': payload['code_sha256'][next(iter(payload['code_sha256']))] = '0'*64
    elif change == 'root': payload['numerical_root_sha256'] = '0'*64
    elif change == 'binding': payload['binding_sha256'] = '0'*64
    elif change == 'time': payload['calculated_at'] = '2099-01-01T00:00:00.000000Z'
    else: payload['predicted_yield'] = 1
    if change != 'hmac': doc['hmac_sha256'] = hmac.new(KEY, model.DOMAIN+inputs.canonical(payload), 'sha256').hexdigest()
    raw = inputs.canonical(doc); bad = sha256(raw).hexdigest(); path = authority.directory/bad; path.write_bytes(raw); path.chmod(0o400)
    with pytest.raises((model.MorphologySignedArtifactHold, PermissionError)): authority.read_manifest('tenant-1', bad)


@pytest.mark.parametrize('change', ['program', 'source', 'evidence', 'binding', 'numerical-root', 'result', 'symlink'])
def test_original_file_hash_metadata_and_path_integrity(prepared, change):
    model, _, authority, _, _, _ = prepared; result_id = publish(prepared)
    payload = json.loads((authority.directory/result_id).read_bytes())['payload']
    key = {'program': 'program_sha256', 'source': 'source_sha256', 'evidence': 'input_evidence_sha256',
        'binding': 'binding_sha256', 'numerical-root': 'numerical_root_sha256'}.get(change)
    path = authority.directory/(payload[key] if key else result_id)
    if change == 'symlink':
        outside = authority.directory.parent/'outside'; outside.write_bytes(path.read_bytes()); path.unlink(); path.symlink_to(outside)
    else:
        path.chmod(0o600); path.write_bytes(path.read_bytes()+b' '); path.chmod(0o400)
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_manifest('tenant-1', result_id)


def test_current_revocation_and_late_read_mutation_never_return_stale_frame(prepared, monkeypatch):
    model, _, authority, _, _, state = prepared; result_id = publish(prepared); state['allowed'] = False
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_frame('tenant-1', result_id, index=0)
    state['allowed'] = True
    previous = model.reader.read_rational_morphology_frame
    def revoke(*a, **kw):
        value = previous(*a, **kw); state['allowed'] = False
        return value
    monkeypatch.setattr(model.reader, 'read_rational_morphology_frame', revoke)
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_frame('tenant-1', result_id, index=0)


def test_late_producer_revocation_returns_no_result_identifier(prepared, monkeypatch):
    model, _, authority, _, _, state = prepared
    numerical = importlib.import_module('app.crop_rational_morphology_artifact_producer')
    previous = numerical.produce_rational_morphology_artifact
    def revoke(*a, **kw):
        value = previous(*a, **kw); state['allowed'] = False
        return value
    monkeypatch.setattr(numerical, 'produce_rational_morphology_artifact', revoke)
    with pytest.raises(model.MorphologySignedArtifactHold): publish(prepared)
    assert not any(json.loads(p.read_bytes()).get('payload', {}).get('schema_version') == model.VERSION for p in authority.directory.iterdir())


@pytest.mark.parametrize('index', [-1, 12, True, '0', None])
def test_only_original_bounded_frame_indexes_are_read(prepared, index):
    model, _, authority, *_ = prepared; result_id = publish(prepared)
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_frame('tenant-1', result_id, index=index)


def test_foreign_tenant_and_changed_server_identity_hold(prepared):
    model, _, authority, *_ = prepared; result_id = publish(prepared)
    with pytest.raises(PermissionError): authority.read_manifest('foreign', result_id)
    authority.key_id = 'changed'
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_manifest('tenant-1', result_id)


@pytest.mark.parametrize('prepared', ['invalid-initial'], indirect=True)
def test_structure_proof_cannot_bypass_the_actual_numerical_initial_state_check(prepared, monkeypatch):
    model, _, authority, _, _, state = prepared
    numerical = importlib.import_module('app.crop_rational_morphology_artifact_producer')
    previous = numerical.produce_rational_morphology_artifact; calls = []
    def calculate(*a, **kw):
        calls.append(1)
        return previous(*a, **kw)
    monkeypatch.setattr(numerical, 'produce_rational_morphology_artifact', calculate)
    with pytest.raises(model.MorphologySignedArtifactHold): publish(prepared)
    assert calls == [1] and state['prepare'] == 1
    assert not any(json.loads(p.read_bytes()).get('payload', {}).get('schema_version') == model.VERSION for p in authority.directory.iterdir())


def test_valid_other_numeric_root_cannot_be_attached_to_the_original_input(prepared):
    model, _, authority, _, packet, _ = prepared; result_id = publish(prepared)
    from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
    other = json.loads(packet['program_raw']); other['program_id'] = 'different-owned-software-program'
    other_root = produce_rational_morphology_artifact(authority.directory, authority.access, program_raw=inputs.canonical(other))
    doc = json.loads((authority.directory/result_id).read_bytes()); doc['payload']['numerical_root_sha256'] = other_root
    doc['hmac_sha256'] = hmac.new(KEY, model.DOMAIN+inputs.canonical(doc['payload']), 'sha256').hexdigest()
    raw = inputs.canonical(doc); digest = sha256(raw).hexdigest(); path = authority.directory/digest; path.write_bytes(raw); path.chmod(0o400)
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_manifest('tenant-1', digest)


def test_final_revocation_returns_no_id_and_private_signed_object_is_not_readable(prepared, monkeypatch):
    model, _, authority, _, _, state = prepared; previous = model.MorphologyBlobStore.put; stored = []
    def revoke(self, raw, **kw):
        digest = previous(self, raw, **kw)
        if json.loads(raw).get('payload', {}).get('schema_version') == model.VERSION:
            stored.append(digest); state['allowed'] = False
        return digest
    monkeypatch.setattr(model.MorphologyBlobStore, 'put', revoke)
    with pytest.raises(model.MorphologySignedArtifactHold): publish(prepared)
    assert len(stored) == 1
    with pytest.raises(model.MorphologySignedArtifactHold): authority.read_manifest('tenant-1', stored[0])
