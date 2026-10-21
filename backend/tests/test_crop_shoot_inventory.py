from copy import deepcopy
import json
from pathlib import Path

import pytest

from app.crop_internode_length import initialize_internode_length
from app.crop_shoot_inventory import ShootInventoryHold, advance_shoot_internode_inventory

REFERENCE = json.loads((Path(__file__).resolve().parents[2] /
    'fixtures/crop-shoot-inventory-reference-v1.json').read_bytes())


def inputs(index=0):
    c = deepcopy(REFERENCE['cases'][index])
    nodes = [{'sequence': n['sequence'], 'birth_age_exact': n['birth_age_exact'],
              'length_state': initialize_internode_length(inputs=n['length_inputs'])['state']}
             for n in c['initial_internodes']]
    return {'input_id': c['input_id'], 'state': {'timeline_state': c['timeline_state'],
        'inventory_start_sequence': c['inventory_start_sequence'], 'internodes': nodes,
        'emergence_profile': c['emergence_profile']}, 'segments': c['segments']}


@pytest.mark.parametrize('index', range(len(REFERENCE['cases'])))
def test_independent_direct_lengths_and_sum_with_explicit_initial_inventory(index):
    p, c = inputs(index), REFERENCE['cases'][index]
    original = deepcopy(p)
    out = advance_shoot_internode_inventory(inputs=p)
    assert out['state']['timeline_state'] == c['timeline_checkpoint']
    assert len(out['state']['internodes']) == len(c['expected'])
    for a,e in zip(out['state']['internodes'], c['expected'], strict=True):
        assert a['sequence'] == e['sequence']
        assert a['length_state']['clock_state']['age_exact'] == e['end_age_exact']
        assert a['length_state']['clock_state']['at'] == c['timeline_checkpoint']['at']
        assert a['length_state']['length']['value'] == pytest.approx(float(e['end_length_m']), rel=1e-12, abs=0)
    for before,after in zip(p['state']['internodes'], out['state']['internodes']):
        assert before['length_state']['anchor'] == after['length_state']['anchor']
    assert out['tracked_axis_length']['unit'] == 'm'
    assert out['tracked_axis_length']['value'] == pytest.approx(float(c['expected_axis_length_m']), rel=1e-12, abs=0)
    assert out['model_version'] == 'shoot-internode-inventory-research-v1'
    assert out['scope'] == 'software_research_only' and out['claim_scope'] == 'synthetic_crop_math_only'
    assert out['gates'] == 'not_assessed' and 'height' not in out
    assert len(out['step_receipts']) == len(out['state']['internodes'])
    assert p == original
    assert advance_shoot_internode_inventory(inputs=p) == out


def test_split_inventory_keeps_initial_nodes_new_births_and_exact_final_state():
    p = inputs()
    whole = advance_shoot_internode_inventory(inputs=p)
    first_segment, second_segment = deepcopy(p['segments'][0]), deepcopy(p['segments'][0])
    first_segment['end_utc'] = second_segment['start_utc'] = '2026-10-01T08:00:00Z'
    first = advance_shoot_internode_inventory(inputs={**p, 'input_id':'part1', 'segments':[first_segment]})
    second = advance_shoot_internode_inventory(inputs={**p, 'input_id':'part2', 'state':first['state'], 'segments':[second_segment]})
    assert second['state'] == whole['state']
    assert second['tracked_axis_length'] == whole['tracked_axis_length']
    assert second['input_sha256'] != whole['input_sha256']


def test_numeric_base_type_does_not_change_normalized_model_identity():
    p = inputs()
    p['state']['timeline_state']['base_temperature']['value'] = 5
    integer = advance_shoot_internode_inventory(inputs=p)
    p['state']['timeline_state']['base_temperature']['value'] = 5.0
    assert advance_shoot_internode_inventory(inputs=p) == integer


@pytest.mark.parametrize('change', ['missing-inventory', 'missing-node', 'duplicate-sequence', 'duplicate-id',
    'birth-age', 'birth-unit', 'clock-time', 'base', 'curve', 'initial-receipt', 'extra-node', 'bad-start'])
def test_inconsistent_initial_or_resumed_inventory_holds_without_mutation(change):
    p = inputs()
    s = p['state']
    node = s['internodes'][0]
    if change == 'missing-inventory': del s['internodes']
    elif change == 'missing-node': s['internodes'].pop()
    elif change == 'duplicate-sequence': s['internodes'][1]['sequence'] = 0
    elif change == 'duplicate-id':
        for clock in ('clock_state',): s['internodes'][1]['length_state'][clock]['internode_id'] = node['length_state'][clock]['internode_id']
        s['internodes'][1]['length_state']['anchor']['clock_state']['internode_id'] = node['length_state']['clock_state']['internode_id']
    elif change == 'birth-age': node['birth_age_exact']['numerator'] = '1'
    elif change == 'birth-unit': node['birth_age_exact']['unit'] = 'day'
    elif change == 'clock-time': node['length_state']['clock_state']['at'] = '2026-10-01T00:00:01Z'
    elif change == 'base':
        node['length_state']['clock_state']['base_temperature']['value'] = 4
        node['length_state']['anchor']['clock_state']['base_temperature']['value'] = 4
    elif change == 'curve': node['length_state']['curve']['values']['maximum_length']['value'] *= 2
    elif change == 'initial-receipt': node['length_state']['anchor']['requested_length']['value'] = 0
    elif change == 'extra-node': node['leaf_count'] = 1
    else: s['inventory_start_sequence'] = True
    original = deepcopy(p)
    with pytest.raises(ShootInventoryHold):
        advance_shoot_internode_inventory(inputs=p)
    assert p == original


def large_inventory(count, has_event):
    p = inputs()
    template = p['state']['internodes'][0]
    p['state']['internodes'] = []
    for i in range(count):
        node = deepcopy(template)
        node['sequence'] = i
        node['length_state']['clock_state']['internode_id'] = 'synthetic-' + str(i)
        node['length_state']['anchor']['clock_state']['internode_id'] = 'synthetic-' + str(i)
        p['state']['internodes'].append(node)
    p['state']['timeline_state']['next_sequence'] = count
    if has_event:
        p['state']['timeline_state']['next_threshold_exact'] = {'numerator':'15','denominator':'1','unit':'degC_day'}
    else:
        p['segments'][0]['air_temperature']['value'] = 5
    return p


def test_512_total_tracked_nodes_are_accepted():
    out = advance_shoot_internode_inventory(inputs=large_inventory(512,False))
    assert len(out['state']['internodes']) == 512


def test_513_total_tracked_nodes_hold():
    with pytest.raises(ShootInventoryHold, match='CAPACITY_HOLD'):
        advance_shoot_internode_inventory(inputs=large_inventory(512,True))


def test_finite_individual_lengths_cannot_overflow_total_silently():
    p = large_inventory(4,False)
    base = deepcopy(REFERENCE['cases'][0]['initial_internodes'][0]['length_inputs'])
    base['curve']['values'].update(maximum_length={'value':1e308,'unit':'m'},
        steepness={'value':1,'unit':'1/degC_day'}, inflection_age={'value':0,'unit':'degC_day'})
    base['initial_length'] = {'value':5e307,'unit':'m'}
    for i,node in enumerate(p['state']['internodes']):
        base['clock_state']['internode_id'] = 'overflow-' + str(i)
        node['length_state'] = initialize_internode_length(inputs=base)['state']
    with pytest.raises(ShootInventoryHold, match='NUMERIC_HOLD'):
        advance_shoot_internode_inventory(inputs=p)
