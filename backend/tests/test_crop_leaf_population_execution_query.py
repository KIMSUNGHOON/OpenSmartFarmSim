"""A valid signed result still needs its own original completed job publication."""
from copy import deepcopy
from types import SimpleNamespace
from uuid import UUID

import pytest

import importlib

@pytest.fixture
def model():
    return importlib.import_module('app.crop_leaf_population_execution_query')
from app import crop_leaf_population_execution_result as wire


def candidate(query):
    job = {'job_id': UUID('00000000-0000-4000-8000-000000000017'), 'attempt_count': 1,
        'input_sha256': '1'*64, 'reason': None}
    request = {'study_id': 'study', 'revision': 'r1', 'farm': {'crop_id': 'crop-1'},
        'parent': {'job_id': '00000000-0000-4000-8000-000000000016', 'result_sha256': '8'*64, 'numerical_root_sha256': '9'*64},
        'input': {'program_sha256': '5'*64, 'source_sha256': '6'*64, 'evidence_sha256': '7'*64}}
    value = {'request': request, 'farm_binding_sha256': '4'*64}
    proof = {'result_sha256': '2'*64, 'binding_sha256': '4'*64, 'manifest': {'samples': [1, 2]},
        'parent_job_id': request['parent']['job_id'], 'parent_result_sha256': '8'*64, 'parent_numerical_root_sha256': '9'*64,
        'study_id': 'study', 'revision': 'r1', 'farm': request['farm'], **{k: request['input'][f] for k, f in
            [('program_sha256', 'program_sha256'), ('source_sha256', 'source_sha256'), ('input_evidence_sha256', 'evidence_sha256')]}}
    raw = wire.result_link(job, '2'*64); manifest = wire.publication_manifest(job, raw, '2'*64, query.WORKER_SHA256)
    publication = {'attempt': 1, 'decision_id': None, 'artifact_sha256': manifest['artifact_sha256'], 'artifact_size': len(raw), 'manifest': manifest}
    outcome = {'state': 'succeeded', 'reason': None, 'decision_id': None, 'termination_reason': 'leaf_population_completed'}
    events = [{'kind': wire.RESULT_EVENT_KIND, 'attempt': 1, 'reason': deepcopy(manifest)},
        {'kind': 'succeeded', 'attempt': 1, 'reason': None}, {'kind': wire.START_EVENT_KIND, 'attempt': 1, 'reason': {
            'execution_kind': 'deterministic_leaf_population', 'worker_code_sha256': query.WORKER_SHA256,
            'input_sha256': job['input_sha256'], 'planned_outputs': 2}}]
    reader = object.__new__(query.LeafPopulationExecutionQuery)
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
    with pytest.raises((query.LeafPopulationExecutionQueryHold, wire.LeafPopulationResultLinkHold)):
        reader._completed('tenant-1', bundle, value, 'manifest', None)
