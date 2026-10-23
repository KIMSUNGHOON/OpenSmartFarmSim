from copy import deepcopy
import json

import pytest

from app.crop_phytomer_kind import PhytomerKindHold, classify_phytomer_sequences


def inputs(first=5, between=2, sequences=None):
    return {'input_id': 'kind-probe', 'policy': {'origin': 'synthetic',
        'sequence_basis': 'explicit_emergence_schedule', 'policy_id': 'declared-phase',
        'shoot_id': 'shoot-1', 'schedule_id': 'schedule-1',
        'first_generative_sequence': first, 'vegetative_between_generative': between},
        'sequences': list(range(14)) if sequences is None else sequences}


def kinds(value):
    return [item['kind'] for item in classify_phytomer_sequences(inputs=value)['phytomers']]


def test_hand_enumerated_phase_and_period_and_preserved_sequences():
    p = inputs(); original = deepcopy(p)
    out = classify_phytomer_sequences(inputs=p)
    assert [v['sequence'] for v in out['phytomers']] == list(range(14))
    assert [v['kind'] for v in out['phytomers']] == [
        'vegetative', 'vegetative', 'vegetative', 'vegetative', 'vegetative',
        'generative', 'vegetative', 'vegetative', 'generative', 'vegetative',
        'vegetative', 'generative', 'vegetative', 'vegetative']
    assert out['model_version'] == 'phytomer-kind-research-v1'
    assert out['scope'] == 'software_research_only' and out['claim_scope'] == 'synthetic_crop_math_only'
    assert out['gates'] == 'not_assessed' and p == original
    out['policy']['shoot_id'] = 'changed'; out['phytomers'][0]['sequence'] = 10
    assert p == original


@pytest.mark.parametrize('first,between', [(0, 0), (0, 3), (1, 1), (5, 2), (8, 3), (50, 4)])
def test_independent_remaining_vegetative_counter_and_batch_restart(first, between):
    remaining = first; expected = []
    for _ in range(45):
        if remaining:
            expected.append('vegetative'); remaining -= 1
        else:
            expected.append('generative'); remaining = between
    p = inputs(first, between, list(range(45)))
    out = classify_phytomer_sequences(inputs=p)
    assert [v['kind'] for v in out['phytomers']] == expected
    chunks = []; policy_hashes = []
    for start, end in [(0, 7), (7, 18), (18, 45)]:
        part = deepcopy(p); part['input_id'] = 'part-'+str(start); part['sequences'] = list(range(start, end))
        value = classify_phytomer_sequences(inputs=part)
        chunks.extend(value['phytomers']); policy_hashes.append(value['policy_sha256'])
    assert chunks == out['phytomers'] and all(v == out['policy_sha256'] for v in policy_hashes)


def test_empty_and_large_integer_boundaries_do_not_need_prefix_enumeration():
    assert kinds(inputs(sequences=[])) == []
    top = 2**31-1
    assert kinds(inputs(top, top, [top-2, top-1, top])) == ['vegetative', 'vegetative', 'generative']
    assert kinds(inputs(0, 0, [top-1, top])) == ['generative', 'generative']


def test_policy_change_and_batch_identity_have_distinct_fingerprints():
    p = inputs(); out = classify_phytomer_sequences(inputs=p)
    reordered = json.loads(json.dumps(p, sort_keys=True))
    assert classify_phytomer_sequences(inputs=reordered) == out
    changed = deepcopy(p); changed['input_id'] = 'another-batch'
    value = classify_phytomer_sequences(inputs=changed)
    assert value['input_sha256'] != out['input_sha256'] and value['policy_sha256'] == out['policy_sha256']
    changed = deepcopy(p); changed['policy']['first_generative_sequence'] = 4
    value = classify_phytomer_sequences(inputs=changed)
    assert value['policy_sha256'] != out['policy_sha256'] and value['phytomers'] != out['phytomers']


@pytest.mark.parametrize('field', ['first_generative_sequence', 'vegetative_between_generative'])
@pytest.mark.parametrize('bad', [True, False, -1, 2**31, 3.0, '3', None])
def test_integer_policy_is_explicit_and_bounded(field, bad):
    p = inputs(); p['policy'][field] = bad; original = deepcopy(p)
    with pytest.raises(PhytomerKindHold): classify_phytomer_sequences(inputs=p)
    assert p == original


@pytest.mark.parametrize('bad', [(0, 1), [0, 0], [2, 1], [1, 3], [True], [-1], [2**31], [1.0], ['1'], None])
def test_sequence_container_order_and_integer_types(bad):
    p = inputs(); p['sequences'] = bad
    with pytest.raises(PhytomerKindHold): classify_phytomer_sequences(inputs=p)


@pytest.mark.parametrize('field', ['input_id', 'policy_id', 'shoot_id', 'schedule_id'])
@pytest.mark.parametrize('bad', ['', '한글', 'bad value', 'x'*201, 1])
def test_bounded_explicit_identifiers(field, bad):
    p = inputs(); target = p if field == 'input_id' else p['policy']; target[field] = bad
    with pytest.raises(PhytomerKindHold): classify_phytomer_sequences(inputs=p)


@pytest.mark.parametrize('field', ['origin', 'sequence_basis', 'policy_id', 'shoot_id', 'schedule_id',
    'first_generative_sequence', 'vegetative_between_generative'])
def test_no_missing_policy_defaults(field):
    p = inputs(); del p['policy'][field]
    with pytest.raises(PhytomerKindHold): classify_phytomer_sequences(inputs=p)


@pytest.mark.parametrize('fault', ['top-extra', 'policy-extra', 'origin', 'basis', 'missing-policy', 'missing-sequences'])
def test_closed_scope_and_required_fields(fault):
    p = inputs()
    if fault == 'top-extra': p['implicit_default'] = 3
    elif fault == 'policy-extra': p['policy']['cultivar'] = 'Axiany'
    elif fault == 'origin': p['policy']['origin'] = 'observed'
    elif fault == 'basis': p['policy']['sequence_basis'] = 'leaf_rank'
    elif fault == 'missing-policy': del p['policy']
    else: del p['sequences']
    with pytest.raises(PhytomerKindHold): classify_phytomer_sequences(inputs=p)


def test_512_bound_is_software_capacity_and_513_is_entire_hold():
    out = classify_phytomer_sequences(inputs=inputs(sequences=list(range(512))))
    assert len(out['phytomers']) == 512 and len(json.dumps(out).encode()) < 2*1024**2
    with pytest.raises(PhytomerKindHold, match='CAPACITY_HOLD'):
        classify_phytomer_sequences(inputs=inputs(sequences=list(range(513))))
