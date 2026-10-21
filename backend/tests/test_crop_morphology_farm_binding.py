"""Closed morphology binding controls; actual registered-farm tests are separate."""
from copy import deepcopy
from hashlib import sha256
import importlib
import json

import pytest

import test_crop_morphology_input_evidence as inputs


@pytest.fixture
def model():
    return importlib.import_module('app.crop_morphology_farm_binding')


def prepared(model):
    raw, source = inputs.prepared(); authority = inputs.authority(model.evidence, source)
    proof = authority.issue(**inputs.arguments(raw, source)); p = json.loads(raw)
    body = {'study_id': 'synthetic-morphology-study', 'revision': 'r1',
        'farm': {'scenario_id': 'farm-1', 'scenario_revision': 'r1', 'registration_sha256': '1'*64, 'crop_id': 'crop-1'},
        'input': {'schema_version': model.evidence.SOURCE_VERSION, 'program_id': p['program_id'],
            'program_sha256': sha256(raw).hexdigest(), 'source_sha256': sha256(source).hexdigest(), 'evidence_sha256': sha256(proof).hexdigest()},
        'rights': {'schema_version': model.RIGHTS_VERSION, 'declaration_id': 'owned-morphology-rights', 'revision': 'r1',
            'input_source_sha256': sha256(source).hexdigest(), 'available_at': '2026-10-21T18:00:00Z', 'redistribute': False,
            **{k: True for k in ['ownership_asserted', 'access', 'store', 'transform', 'use', 'display']}}}
    registration = {'decision_at': '2026-10-21T18:00:00Z', 'crop': {'occupancy': {
        'start': '2026-10-01T00:00:00Z', 'end': '2026-10-02T00:00:00Z'}},
        'calendar_utc': {'start': '2026-09-30T15:00:00Z', 'end': '2026-10-02T15:00:00Z'}}
    shell = object.__new__(model.MorphologyFarmBinding); shell.input_authority = authority
    return shell, body, registration, {'program_raw': raw, 'source_raw': source, 'evidence_raw': proof}


def test_original_program_identity_and_tracked_shoot_are_bound_without_scaling(model):
    shell, body, registration, packet = prepared(model)
    assert shell._request(inputs.canonical(body)) == body
    source = shell._input(body, registration, **packet)
    shell._scope(body, registration, source)
    assert source['period'] == {'start': '2026-10-01T00:00:00Z', 'end': '2026-10-02T00:00:00Z'}
    assert source['time_origin_utc'] == '2026-10-01T00:00:00Z'
    assert source['source_record'] == json.loads(packet['source_raw'])['provenance']
    assert source['initial_state_sha256'] == sha256(inputs.canonical(json.loads(packet['program_raw'])['initial_state'])).hexdigest()
    assert source['shoot_id'] == json.loads(packet['program_raw'])['initial_state']['timeline_state']['shoot_id']
    assert source['program_sha256'] == body['input']['program_sha256'] and source['normalization'] == 'per_tracked_shoot'
    assert source['numerical_initial_state_validation'] is False
    assert 'yield' not in source and 'plant_count' not in source


@pytest.mark.parametrize('change', ['extra', 'study', 'farm-extra', 'farm-hash', 'crop', 'source-schema', 'source-extra',
    'source-hash', 'rights-schema', 'rights-hash', 'rights-use', 'rights-bool', 'rights-redistribute', 'rights-time', 'request-size'])
def test_closed_request_rejects_mixed_or_unbounded_identity(model, change):
    shell, body, _, _ = prepared(model)
    if change == 'extra': body['path'] = '/not-permitted'
    elif change == 'study': body['study_id'] = ''
    elif change == 'farm-extra': body['farm']['approved'] = True
    elif change == 'farm-hash': body['farm']['registration_sha256'] = 'invalid'
    elif change == 'crop': body['farm']['crop_id'] = True
    elif change == 'source-schema': body['input']['schema_version'] = 'joint-solar-input-source-v1'
    elif change == 'source-extra': body['input']['directory'] = '/not-permitted'
    elif change == 'source-hash': body['input']['program_sha256'] = 'invalid'
    elif change == 'rights-schema': body['rights']['schema_version'] = 'joint-solar-input-rights-v1'
    elif change == 'rights-hash': body['rights']['input_source_sha256'] = '0'*64
    elif change == 'rights-use': body['rights']['use'] = False
    elif change == 'rights-bool': body['rights']['display'] = 1
    elif change == 'rights-redistribute': body['rights']['redistribute'] = True
    elif change == 'rights-time': body['rights']['available_at'] = '2026-10-21T18:00:00+09:00'
    raw = b'x'*(128*1024+1) if change == 'request-size' else inputs.canonical(body)
    with pytest.raises(model.MorphologyFarmBindingHold): shell._request(raw)


@pytest.mark.parametrize('change', ['program', 'source', 'evidence', 'program-id', 'evidence-decision'])
def test_input_identity_and_registered_decision_must_match_original_proof(model, change):
    shell, body, registration, packet = prepared(model)
    if change == 'program-id': body['input']['program_id'] = 'other'
    elif change == 'evidence-decision': registration['decision_at'] = '2026-10-21T18:00:00.000001Z'
    else: packet[change+'_raw'] += b' '
    with pytest.raises(model.MorphologyFarmBindingHold): shell._input(body, registration, **packet)


@pytest.mark.parametrize('change', ['rights-late', 'source-late', 'crop-start', 'crop-end', 'calendar-start', 'calendar-end'])
def test_one_microsecond_scope_and_availability_excess_holds(model, change):
    shell, body, registration, packet = prepared(model); source = shell._input(body, registration, **packet)
    if change == 'rights-late': body['rights']['available_at'] = '2026-10-21T18:00:00.000001Z'
    elif change == 'source-late': source['source_record']['available_at'] = '2026-10-21T18:00:00.000001Z'
    elif change == 'crop-start': registration['crop']['occupancy']['start'] = '2026-10-01T00:00:00.000001Z'
    elif change == 'crop-end': registration['crop']['occupancy']['end'] = '2026-10-01T23:59:59.999999Z'
    elif change == 'calendar-start': registration['calendar_utc']['start'] = '2026-10-01T00:00:00.000001Z'
    elif change == 'calendar-end': registration['calendar_utc']['end'] = '2026-10-01T23:59:59.999999Z'
    with pytest.raises(model.MorphologyFarmBindingHold): shell._scope(body, registration, source)


def test_constructor_requires_actual_farm_authority(model):
    _, source = inputs.prepared()
    with pytest.raises(model.MorphologyFarmBindingHold):
        model.MorphologyFarmBinding(object(), inputs.authority(model.evidence, source), input_rights=lambda *a: True)
