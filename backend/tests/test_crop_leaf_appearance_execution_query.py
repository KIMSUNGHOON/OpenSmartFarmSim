"""A valid signed result still needs its own original completed job publication."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import UUID

import pytest

import importlib

@pytest.fixture
def model():
    return importlib.import_module('app.crop_leaf_appearance_execution_query')
from app import crop_leaf_appearance_execution_result as wire


def candidate(query):
    job = {'job_id': UUID('00000000-0000-4000-8000-000000000017'), 'attempt_count': 1,
        'input_sha256': '1'*64, 'reason': None}
    request = {'study_id': 'study', 'revision': 'r1', 'farm': {'crop_id': 'crop-1'},
        'parent': {'job_id': '00000000-0000-4000-8000-000000000016', 'result_sha256': '8'*64, 'numerical_root_sha256': '9'*64},
        'input': {'program_sha256': '5'*64, 'source_sha256': '6'*64, 'evidence_sha256': '7'*64}}
    value = {'request': request, 'farm_binding_sha256': '4'*64}
    proof = {'result_sha256': '2'*64, 'binding_sha256': '4'*64, 'manifest': {'sample_count': 2},
        'parent_job_id': request['parent']['job_id'], 'parent_result_sha256': '8'*64, 'parent_numerical_root_sha256': '9'*64,
        'study_id': 'study', 'revision': 'r1', 'farm': request['farm'], **{k: request['input'][f] for k, f in
            [('program_sha256', 'program_sha256'), ('source_sha256', 'source_sha256'), ('input_evidence_sha256', 'evidence_sha256')]}}
    raw = wire.result_link(job, '2'*64); manifest = wire.publication_manifest(job, raw, '2'*64, query.WORKER_SHA256)
    publication = {'attempt': 1, 'decision_id': None, 'artifact_sha256': manifest['artifact_sha256'], 'artifact_size': len(raw), 'manifest': manifest}
    outcome = {'state': 'succeeded', 'reason': None, 'decision_id': None, 'termination_reason': 'leaf_appearance_completed'}
    events = [{'kind': wire.RESULT_EVENT_KIND, 'attempt': 1, 'reason': deepcopy(manifest)},
        {'kind': 'succeeded', 'attempt': 1, 'reason': None}, {'kind': wire.START_EVENT_KIND, 'attempt': 1, 'reason': {
            'execution_kind': 'deterministic_leaf_appearance', 'worker_code_sha256': query.WORKER_SHA256,
            'input_sha256': job['input_sha256'], 'planned_outputs': 2}}]
    reader = object.__new__(query.LeafAppearanceExecutionQuery)
    reader.jobs = SimpleNamespace(read_artifact=lambda *_: raw)
    reader._stored = lambda *_: (deepcopy(proof), None, None)
    return reader, (job, [publication], events, [outcome], []), value, proof


def test_original_publication_and_signed_identity_are_both_required(model):
    query = model
    reader, bundle, value, proof = candidate(query)
    assert reader._completed('tenant-1', bundle, value, 'manifest', None) == (proof, None, None)


@pytest.mark.parametrize('change', ['missing_publication', 'wrong_attempt', 'claim', 'wrong_link',
    'old_result', 'missing_outcome', 'fake_cli', 'failed_event', 'parent_job', 'parent_result', 'parent_root',
    'wrong_start_attempt', 'wrong_terminal_attempt', 'planned_outputs', 'termination'])
def test_valid_result_cannot_be_used_as_another_or_unpublished_job(model, change):
    query = model
    reader, bundle, value, proof = candidate(query); _, pubs, events, outcomes, invocations = bundle
    if change == 'missing_publication': pubs.clear()
    elif change == 'wrong_attempt': pubs[0]['attempt'] = 2
    elif change == 'claim': pubs[0]['manifest']['gates'] = 'G1'
    elif change == 'wrong_link': reader.jobs.read_artifact = lambda *_: b'{}'
    elif change == 'old_result': proof['binding_sha256'] = '0'*64
    elif change == 'missing_outcome': outcomes.clear()
    elif change == 'fake_cli': invocations.append({'execution_kind': 'codex_cli'})
    elif change == 'failed_event': events[1]['kind'] = 'failed'
    elif change == 'parent_job': proof['parent_job_id'] = '00000000-0000-4000-8000-000000000019'
    elif change == 'parent_result': proof['parent_result_sha256'] = '0'*64
    elif change == 'parent_root': proof['parent_numerical_root_sha256'] = '0'*64
    elif change == 'wrong_start_attempt': events[2]['attempt'] = 2
    elif change == 'wrong_terminal_attempt': events[1]['attempt'] = 2
    elif change == 'planned_outputs': events[2]['reason']['planned_outputs'] = 1
    elif change == 'termination': outcomes[0]['termination_reason'] = 'morphology_completed'
    with pytest.raises((query.LeafAppearanceExecutionQueryHold, wire.LeafAppearanceResultLinkHold)):
        reader._completed('tenant-1', bundle, value, 'manifest', None)


def stored_candidate(model, monkeypatch):
    signed = model.execution.signed
    frames = [{'at': '2026-10-23T00:00:00Z'}, {'at': '2026-10-23T00:00:02Z'}]
    payload = {k: '1'*64 for k in ('program_sha256', 'source_sha256', 'input_evidence_sha256',
        'binding_sha256', 'numerical_root_sha256', 'parent_result_sha256', 'parent_numerical_root_sha256')}
    payload.update(parent_job_id='00000000-0000-4000-8000-000000000016', calculated_at='2026-10-23T01:00:00Z',
        parent_calculated_at='2026-10-23T00:30:00Z', study_id='study', revision='r1')
    binding = {'request': {'farm': {'crop_id': 'crop-1'}},
        'input': {'period': {'start': frames[0]['at'], 'end': frames[1]['at']}}}
    original = (payload, b'original-binding', binding, {'program_raw': b'original-program'})
    authority = SimpleNamespace(directory=None, access=None, _load=lambda *_: deepcopy(original))
    reader = object.__new__(model.LeafAppearanceExecutionQuery)
    reader.service = SimpleNamespace(authority=authority)
    monkeypatch.setattr(signed, '_linked', lambda *_: None)
    monkeypatch.setattr(signed.reader, 'read_leaf_appearance_manifest', lambda *_: {'sample_count': 2})
    monkeypatch.setattr(signed.reader, 'read_leaf_appearance_frame', lambda *_, index: deepcopy(frames[index]))
    return reader, frames


@pytest.mark.parametrize('view,index', [('status', None), ('manifest', None), ('frame', 0), ('replay', None)])
def test_new_manifest_count_and_original_period_are_used(model, monkeypatch, view, index):
    reader, frames = stored_candidate(model, monkeypatch)
    proof, frame, replay = reader._stored('tenant-1', '2'*64, view, index)
    assert proof['manifest'] == {'sample_count': 2}
    if view == 'frame': assert frame['frame'] == frames[0]
    if view == 'replay': assert replay['frames'] == frames


@pytest.mark.parametrize('view,index,changed', [
    ('status', None, 1), ('manifest', None, 1), ('frame', 0, 0), ('frame', 1, 1), ('replay', None, 0)])
def test_selected_or_last_frame_outside_original_period_is_rejected(model, monkeypatch, view, index, changed):
    reader, frames = stored_candidate(model, monkeypatch)
    frames[changed]['at'] = '2026-10-22T23:59:59Z' if changed == 0 else '2026-10-23T00:00:01Z'
    with pytest.raises(model.execution.signed.LeafAppearanceSignedArtifactHold):
        reader._stored('tenant-1', '2'*64, view, index)
