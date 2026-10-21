from copy import deepcopy
from datetime import datetime
from decimal import Decimal, localcontext
from fractions import Fraction
import json
from pathlib import Path

import pytest

from app.crop_rational_shoot_inventory import advance_rational_shoot_internode_inventory, RationalShootInventoryHold
from app.crop_rational_internode_length import initialize_rational_internode_length
from app.crop_shoot_inventory import advance_shoot_internode_inventory
from test_crop_shoot_inventory import inputs as old_inputs
from test_crop_rational_internode_length import exact, initial, reference
from test_crop_rational_new_internodes import fractional


REFERENCE = json.loads((Path(__file__).resolve().parents[2] / 'fixtures/crop-shoot-inventory-reference-v1.json').read_bytes())


def converted_inputs(index=0):
    case = deepcopy(REFERENCE['cases'][index]); origin = case['timeline_state']['started_at']; nodes = []
    for node in case['initial_internodes']:
        p = node['length_inputs']; clock = p['clock_state']
        def seconds(utc):
            delta = datetime.fromisoformat(utc) - datetime.fromisoformat(origin)
            return delta.days * 86400 + delta.seconds
        converted = {k: v for k, v in clock.items() if k not in ('at', 'emerged_at')}
        converted.update(time_origin_utc=origin, emerged_elapsed_seconds_exact=exact(seconds(clock['emerged_at'])),
                         at_elapsed_seconds_exact=exact(seconds(clock['at'])))
        state = initialize_rational_internode_length(inputs={**p, 'clock_state': converted})['state']
        nodes.append({'sequence': node['sequence'], 'birth_age_exact': node['birth_age_exact'], 'length_state': state})
    return {'input_id': case['input_id'], 'state': {'timeline_state': case['timeline_state'],
        'inventory_start_sequence': case['inventory_start_sequence'], 'internodes': nodes,
        'emergence_profile': case['emergence_profile']}, 'segments': case['segments']}


def fractional_inputs():
    p = fractional(); nodes = []
    for i in range(3):
        request = initial(birth=Fraction(0)); request['clock_state']['internode_id'] = 'synthetic-initial-' + str(i)
        nodes.append({'sequence': i, 'birth_age_exact': exact(unit='degC_day'),
                      'length_state': initialize_rational_internode_length(inputs=request)['state']})
    return {'input_id': 'fractional-inventory', 'state': {'timeline_state': p['timeline_state'],
        'inventory_start_sequence': 0, 'internodes': nodes,
        'emergence_profile': {k: p[k] for k in ('curve', 'initial_length')}}, 'segments': p['segments']}


@pytest.mark.parametrize('index', range(len(REFERENCE['cases'])))
def test_independent_lengths_sums_and_whole_second_legacy_outputs(index):
    p = converted_inputs(index); before = deepcopy(p); case = REFERENCE['cases'][index]
    result = advance_rational_shoot_internode_inventory(inputs=p)
    old = advance_shoot_internode_inventory(inputs=old_inputs(index))
    assert result['state']['timeline_state'] == case['timeline_checkpoint'] == old['state']['timeline_state']
    assert len(result['state']['internodes']) == len(case['expected'])
    for node, legacy, expected in zip(result['state']['internodes'], old['state']['internodes'], case['expected'], strict=True):
        assert node['sequence'] == expected['sequence']
        assert node['length_state']['clock_state']['age_exact'] == expected['end_age_exact']
        assert node['length_state']['clock_state']['internode_id'] == legacy['length_state']['clock_state']['internode_id']
        assert node['length_state']['length'] == legacy['length_state']['length']
        assert node['length_state']['length']['value'] == pytest.approx(float(expected['end_length_m']), rel=1e-12, abs=0)
    assert result['tracked_axis_length'] == old['tracked_axis_length']
    assert result['tracked_axis_length']['value'] == pytest.approx(float(case['expected_axis_length_m']), rel=1e-12, abs=0)
    assert len(result['step_receipts']) == len(result['state']['internodes'])
    assert result['scope'] == 'software_research_only' and result['gates'] == 'not_assessed'
    assert result['claim_scope'] == 'synthetic_crop_math_only' and 'height' not in result
    assert p == before and advance_rational_shoot_internode_inventory(inputs=p) == result


def test_fractional_new_then_existing_inventory_replays_to_same_state_and_independent_sum():
    p = fractional_inputs(); p['segments'][0]['end_utc'] = '2026-10-01T00:00:03Z'
    whole = advance_rational_shoot_internode_inventory(inputs=p)
    first_seg = {**p['segments'][0], 'end_utc': '2026-10-01T00:00:01Z'}
    second_seg = {**p['segments'][0], 'start_utc': first_seg['end_utc']}
    first = advance_rational_shoot_internode_inventory(inputs={**p, 'input_id': 'first', 'segments': [first_seg]})
    second = advance_rational_shoot_internode_inventory(inputs={**p, 'input_id': 'second', 'state': first['state'], 'segments': [second_seg]})
    assert len(first['state']['internodes']) == 6 and len(whole['state']['internodes']) == 12
    assert second['state'] == whole['state'] and second['tracked_axis_length'] == whole['tracked_axis_length']
    assert second['input_sha256'] != whole['input_sha256']
    ages = [Fraction(9, 86400)] * 3 + [Fraction(i, 86400) for i in range(8, -1, -1)]
    c = p['state']['emergence_profile']['curve']
    with localcontext() as ctx:
        ctx.prec = 800
        total = sum((reference(age, c) for age in ages), Decimal(0))
    assert whole['tracked_axis_length']['value'] == pytest.approx(float(total), rel=1e-12, abs=0)
    for node, age in zip(whole['state']['internodes'], ages, strict=True):
        assert node['length_state']['clock_state']['age_exact'] == exact(age, unit='degC_day')
        assert node['length_state']['length']['value'] == pytest.approx(float(reference(age, c)), rel=1e-12, abs=0)
    for a, b in zip(p['state']['internodes'], whole['state']['internodes']):
        assert a['length_state']['anchor'] == b['length_state']['anchor']


@pytest.mark.parametrize('change', ['missing', 'extra', 'node-count', 'sequence', 'id', 'origin', 'current-time',
    'birth-age', 'age-unit', 'base', 'anchor', 'curve', 'start-bool'])
def test_initial_inventory_cannot_be_silently_repaired(change):
    p = fractional_inputs(); state = p['state']; node = state['internodes'][0]; length = node['length_state']
    if change == 'missing': del state['internodes']
    elif change == 'extra': node['leaf_count'] = 1
    elif change == 'node-count': state['internodes'].pop()
    elif change == 'sequence': node['sequence'] = 1
    elif change == 'id':
        other = state['internodes'][1]['length_state']['clock_state']['internode_id']
        length['clock_state']['internode_id'] = length['anchor']['clock_state']['internode_id'] = other
    elif change == 'origin':
        length['clock_state']['time_origin_utc'] = length['anchor']['clock_state']['time_origin_utc'] = '2026-09-30T00:00:00Z'
    elif change == 'current-time': length['clock_state']['at_elapsed_seconds_exact'] = exact(1)
    elif change == 'birth-age': node['birth_age_exact'] = exact(1, unit='degC_day')
    elif change == 'age-unit': node['birth_age_exact']['unit'] = 's'
    elif change == 'base':
        length['clock_state']['base_temperature']['value'] = length['anchor']['clock_state']['base_temperature']['value'] = -1
    elif change == 'anchor': length['anchor']['requested_length']['value'] *= 2
    elif change == 'curve': length['curve']['values']['maximum_length']['value'] *= 2
    else: state['inventory_start_sequence'] = True
    before = deepcopy(p)
    with pytest.raises(RationalShootInventoryHold): advance_rational_shoot_internode_inventory(inputs=p)
    assert p == before


def test_fractional_birth_order_must_be_kept_on_resume():
    p = fractional_inputs(); first = advance_rational_shoot_internode_inventory(inputs=p)
    nodes = first['state']['internodes']; nodes[3], nodes[4] = nodes[4], nodes[3]
    nodes[3]['sequence'], nodes[4]['sequence'] = 3, 4
    segment = {**p['segments'][0], 'start_utc': '2026-10-01T00:00:01Z', 'end_utc': '2026-10-01T00:00:02Z'}
    with pytest.raises(RationalShootInventoryHold, match='birth order'):
        advance_rational_shoot_internode_inventory(inputs={**p, 'state': first['state'], 'segments': [segment]})


def large_inventory(count, air=0):
    p = fractional_inputs(); template = p['state']['internodes'][0]
    p['state']['internodes'] = []
    for i in range(count):
        node = deepcopy(template); node['sequence'] = i
        node['length_state']['clock_state']['internode_id'] = node['length_state']['anchor']['clock_state']['internode_id'] = 'capacity-' + str(i)
        p['state']['internodes'].append(node)
    p['state']['timeline_state']['next_sequence'] = count
    p['segments'][0]['air_temperature']['value'] = air
    return p


def test_512_nodes_and_513_count_boundaries():
    result = advance_rational_shoot_internode_inventory(inputs=large_inventory(512))
    assert len(result['state']['internodes']) == 512
    with pytest.raises(RationalShootInventoryHold, match='CAPACITY_HOLD'):
        advance_rational_shoot_internode_inventory(inputs=large_inventory(512, 3))


def test_finite_lengths_cannot_overflow_axis_sum():
    p = large_inventory(4); c = p['state']['emergence_profile']['curve']
    c['values'].update(maximum_length={'value': 1e308, 'unit': 'm'}, steepness={'value': 1, 'unit': '1/degC_day'},
                       inflection_age={'value': 0, 'unit': 'degC_day'})
    p['state']['emergence_profile']['initial_length'] = {'value': 5e307, 'unit': 'm'}
    for i, node in enumerate(p['state']['internodes']):
        request = initial(birth=Fraction(0), c=c); request['clock_state']['internode_id'] = 'overflow-' + str(i)
        node['length_state'] = initialize_rational_internode_length(inputs=request)['state']
    with pytest.raises(RationalShootInventoryHold, match='NUMERIC_HOLD'):
        advance_rational_shoot_internode_inventory(inputs=p)


def test_exact_age_receipts_cannot_exceed_two_mib():
    p = large_inventory(512); age = Fraction(10**998 + 1, 3 * 10**998 + 1)
    timeline = p['state']['timeline_state']; timeline.update(at='2026-10-01T00:00:01Z', age_exact=exact(age, unit='degC_day'),
        next_threshold_exact=exact(age + 1, unit='degC_day'), phyllochron_exact=exact(1, unit='degC_day'))
    p['segments'][0].update(start_utc=timeline['at'], end_utc='2026-10-01T00:00:02Z')
    request = initial(birth=Fraction(0), at=Fraction(1), age=age)
    template = initialize_rational_internode_length(inputs=request)['state']
    for i, node in enumerate(p['state']['internodes']):
        node['length_state'] = deepcopy(template)
        node['length_state']['clock_state']['internode_id'] = node['length_state']['anchor']['clock_state']['internode_id'] = 'large-' + str(i)
    with pytest.raises(RationalShootInventoryHold, match='CAPACITY_HOLD: rational inventory result exceeds 2MiB'):
        advance_rational_shoot_internode_inventory(inputs=p)
