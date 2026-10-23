"""Opaque job links cannot change the original simulation or result identity."""
from hashlib import sha256
import importlib
import json
from uuid import UUID

import pytest

import test_crop_morphology_input_evidence as inputs


@pytest.fixture
def model():
    return importlib.import_module('app.crop_leaf_appearance_execution_result')


def job():
    return {'job_id': UUID('00000000-0000-4000-8000-000000000017'), 'input_sha256': '1'*64, 'attempt_count': 1}


def test_reference_is_small_opaque_and_tied_to_job_input(model):
    raw = model.result_link(job(), '2'*64); value = model.read_link(raw, job())
    assert value['result_sha256'] == '2'*64 and value['job_id'] == str(job()['job_id'])
    assert len(raw) < 1024 and 'farm' not in value and 'frame' not in value
    manifest = model.publication_manifest(job(), raw, '2'*64, '3'*64)
    assert manifest['artifact_sha256'] == sha256(raw).hexdigest() and manifest['attempt'] == 1
    assert manifest['gates'] == 'not_assessed' and manifest['stage'] == 'simulation'


@pytest.mark.parametrize('change', ['job', 'input', 'result', 'scope', 'schema', 'extra', 'space', 'capacity'])
def test_changed_reference_cannot_select_another_result_or_claim(model, change):
    raw = model.result_link(job(), '2'*64); v = json.loads(raw)
    if change == 'job': v['job_id'] = '00000000-0000-4000-8000-000000000018'
    elif change == 'input': v['input_sha256'] = '0'*64
    elif change == 'result': v['result_sha256'] = 'invalid'
    elif change == 'scope': v['gates'] = 'G1'
    elif change == 'schema': v['schema_version'] = 'other'
    elif change == 'extra': v['yield_kg'] = 1
    raw = b' '+raw if change == 'space' else b'x'*4097 if change == 'capacity' else inputs.canonical(v)
    with pytest.raises(model.LeafAppearanceResultLinkHold): model.read_link(raw, job())
