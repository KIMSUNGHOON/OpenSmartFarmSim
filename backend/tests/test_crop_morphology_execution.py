"""Admission witness controls; actual database admission is tested separately."""
from copy import deepcopy
from hashlib import sha256
import hmac
import importlib
from types import SimpleNamespace

import pytest

import test_crop_morphology_input_evidence as inputs
import test_crop_morphology_farm_binding as controls
from app import crop_morphology_farm_binding as farms


KEY = b'owned-morphology-admission-test-key-32!'


@pytest.fixture
def model():
    return importlib.import_module('app.crop_morphology_execution')


def authority():
    return SimpleNamespace(integrity_key=KEY, issuer_id='owned-intent', key_id='owned-key')


def request():
    return controls.prepared(farms)[1]


def test_intent_binds_exact_request_code_binding_key_and_resolver(model):
    body = request(); before = deepcopy(body)
    value = model._signed_input(authority(), body, '1'*64, 'owned-resolver-v1')
    raw = inputs.canonical(value)
    assert model._verified_input(authority(), raw, 'owned-resolver-v1') == value
    assert value['request'] == before and body == before and KEY not in raw
    assert value['input_version'] == model.INPUT_VERSION and value['farm_binding_sha256'] == '1'*64
    assert 'program_raw' not in raw.decode() and len(raw) < 64*1024
    wrong = authority(); wrong.integrity_key = b'other-owned-admission-test-key-32!'
    with pytest.raises(model.MorphologyExecutionHold): model._verified_input(wrong, raw, 'owned-resolver-v1')


@pytest.mark.parametrize('change', ['version', 'binding', 'code', 'issuer', 'key-id', 'resolver', 'signature', 'extra', 'noncanonical', 'oversize'])
def test_current_intent_cannot_silently_accept_altered_metadata(model, change):
    value = model._signed_input(authority(), request(), '1'*64, 'owned-resolver-v1')
    if change == 'version': value['input_version'] = 'other'
    elif change == 'binding': value['farm_binding_sha256'] = 'invalid'
    elif change == 'code': value['admission_code_sha256'] = '0'*64
    elif change == 'issuer': value['authority']['issuer_id'] = 'other'
    elif change == 'key-id': value['authority']['key_id'] = 'other'
    elif change == 'resolver': value['input_resolver_version'] = 'other'
    elif change == 'signature': value['intent_hmac_sha256'] = '0'*64
    elif change == 'extra': value['accepted_G0'] = True
    if change not in ('signature', 'noncanonical', 'oversize'):
        payload = {k: v for k, v in value.items() if k != 'intent_hmac_sha256'}
        value['intent_hmac_sha256'] = hmac.new(KEY, model.INTENT_DOMAIN+inputs.canonical(payload), 'sha256').hexdigest()
    raw = inputs.canonical(value)
    if change == 'noncanonical': raw = b' '+raw
    elif change == 'oversize': raw = b'x'*(64*1024+1)
    with pytest.raises(model.MorphologyExecutionHold): model._verified_input(authority(), raw, 'owned-resolver-v1')
