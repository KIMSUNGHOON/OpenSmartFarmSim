"""Closed leaf admission intent controls; registered database admission is separate."""
from copy import deepcopy
from hashlib import sha256
import hmac
import importlib
from types import SimpleNamespace

import pytest

from app import crop_leaf_appearance_farm_binding as farms
import test_crop_leaf_appearance_farm_binding as controls
import test_crop_leaf_appearance_input_evidence as inputs


KEY=b'owned-leaf-appearance-admission-test-key-32!'


@pytest.fixture
def model():return importlib.import_module('app.crop_leaf_appearance_execution')


def authority():return SimpleNamespace(integrity_key=KEY,issuer_id='owned-leaf-intent',key_id='owned-key')


def test_intent_binds_original_request_code_parent_binding_and_resolver(model):
    body=controls.prepared(farms)[1];before=deepcopy(body)
    value=model._signed_input(authority(),body,'1'*64,'owned-leaf-resolver-v1');raw=inputs.canonical(value)
    assert model._verified_input(authority(),raw,'owned-leaf-resolver-v1')==value
    assert value['request']==before and body==before and KEY not in raw and len(raw)<64*1024
    assert value['request']['parent']==body['parent'] and value['input_version']==model.INPUT_VERSION
    assert value['farm_binding_sha256']=='1'*64 and b'program_raw' not in raw
    wrong=authority();wrong.integrity_key=b'other-owned-leaf-appearance-admission-key!'
    with pytest.raises(model.LeafAppearanceExecutionHold):model._verified_input(wrong,raw,'owned-leaf-resolver-v1')


@pytest.mark.parametrize('change',['version','binding','code','artifact-code','issuer','key-id','resolver','signature','parent','extra','noncanonical','oversize'])
def test_changed_intent_metadata_never_silently_changes_lineage(model,change):
    value=model._signed_input(authority(),controls.prepared(farms)[1],'1'*64,'owned-leaf-resolver-v1')
    if change=='version':value['input_version']='leaf-population-execution-input-v1'
    elif change=='binding':value['farm_binding_sha256']='invalid'
    elif change=='code':value['admission_code_sha256']='0'*64
    elif change=='artifact-code':value['authority']['artifact_code_sha256'][next(iter(value['authority']['artifact_code_sha256']))]='0'*64
    elif change=='issuer':value['authority']['issuer_id']='other'
    elif change=='key-id':value['authority']['key_id']='other'
    elif change=='resolver':value['input_resolver_version']='other'
    elif change=='signature':value['intent_hmac_sha256']='0'*64
    elif change=='parent':value['request']['parent']['result_sha256']='0'*64
    elif change=='extra':value['approved_G0']=True
    if change not in ('signature','parent','noncanonical','oversize'):
        payload={k:v for k,v in value.items() if k!='intent_hmac_sha256'}
        value['intent_hmac_sha256']=hmac.new(KEY,model.INTENT_DOMAIN+inputs.canonical(payload),'sha256').hexdigest()
    raw=inputs.canonical(value)
    if change=='noncanonical':raw=b' '+raw
    elif change=='oversize':raw=b'x'*(64*1024+1)
    with pytest.raises(model.LeafAppearanceExecutionHold):model._verified_input(authority(),raw,'owned-leaf-resolver-v1')
