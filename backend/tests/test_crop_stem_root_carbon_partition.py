from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
from math import fsum, nextafter, ulp
from pathlib import Path
from types import MappingProxyType

import pytest

from app import crop_stem_root_carbon_partition as partition
from app.crop_growth_rates import ReferenceParameters, RATE_UNIT
from test_growing_geometry_leaf_removal_point import CASES, profiles
from app import crop_growing_geometry_continuation as parent

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def profile():
    return ReferenceParameters((ROOT / 'fixtures/crop-growth-reference-parameters-v1.json').read_bytes())


def inputs(growth=4., weights=(1., 3.), floor=1.):
    return {'input_id': 'own-stem-root-partition', 'origin': 'synthetic', 'policy': partition.POLICY_ID,
            'model_floor_area': {'value': floor, 'unit': 'm2_floor'},
            'requested_stem_root_growth': {'value': growth, 'unit': RATE_UNIT},
            'compartments': [{'compartment_id': 'roots' if i == 0 else f'internode-{i}',
                              'kind': 'root_system' if i == 0 else 'internode',
                              'sink_weight': {'value': weight, 'unit': '1'}} for i, weight in enumerate(weights)]}


def reference(growth, weights, cost):
    with localcontext() as context:
        context.prec = 450
        g, c = Decimal.from_float(float(growth)), Decimal.from_float(cost)
        w = [Decimal.from_float(float(x)) for x in weights]
        total = sum(w)
        effective = g if total else Decimal(0)
        deferred = g - effective
        return ([float(g * x / total) if total else 0. for x in w],
                [float(c * x) for x in [g, effective, deferred]], float(deferred + c * deferred))


@pytest.mark.parametrize('growth,weights', [(4., (1., 3.)), (0., (1., 3.)), (4., (0., 0.)), (0., (0., 0.)),
    (2., (1.,)), (30., (1., 2.)), (.125, (0., 1., 0., 3.)), (1e80, (1e-30, 1., 3.)),
    (1e-80, (.25, .5, .25)), (nextafter(1., 2.), (1., 7., 13.)), (10., tuple(float(i % 7) for i in range(512)))])
def test_independent_decimal_quantities_costs_and_input_preservation(profile, growth, weights):
    value = inputs(growth, weights)
    before = deepcopy(value)
    result = partition.calculate_partition(inputs=value, growth_profile=profile)
    flows, respiration, refund = reference(growth, weights, profile.values['cStemG'])
    assert profile.values['cStemG'] != profile.values['cLeafG']
    for actual, wanted in zip(result['allocation'], flows, strict=True):
        assert abs(actual['carbohydrate_inflow']['value'] - wanted) <= 2 * ulp(wanted)
        assert actual['carbohydrate_inflow']['unit'] == RATE_UNIT
    for key, wanted in zip(('requested', 'realized', 'avoided'), respiration, strict=True):
        assert result['growth_respiration'][key] == {'value': wanted, 'unit': RATE_UNIT}
    assert abs(result['derivative_adjustments']['buffer']['value'] - refund) <= 2 * ulp(refund)
    assert [x['compartment_id'] for x in result['allocation']] == [x['compartment_id'] for x in value['compartments']]
    assert [x['kind'] for x in result['allocation']] == [x['kind'] for x in value['compartments']]
    assert result['effective_stem_root_growth']['value'] == (growth if any(weights) else 0.)
    assert result['deferred_stem_root_growth']['value'] == (0. if any(weights) else growth)
    assert result['scope'] == 'software_research_only' and result['G0_G4'] == 'not_assessed'
    assert result['claim_scope'] == 'synthetic_stem_root_partition_math_only'
    for key, quantity in result['balance_residuals'].items():
        assert abs(quantity['value']) <= result['balance_budgets'][key]['value']
    assert value == before and partition.calculate_partition(inputs=value, growth_profile=profile) == result
    assert sha256(partition._canonical({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest() == result['calculation_sha256']


def test_weights_are_relative_not_demand_caps_and_footprint_is_not_a_hidden_multiplier(profile):
    original = partition.calculate_partition(inputs=inputs(30., (1., 2.), 1.), growth_profile=profile)
    changed = partition.calculate_partition(inputs=inputs(30., (10., 20.), 100.), growth_profile=profile)
    assert [q['carbohydrate_inflow']['value'] for q in original['allocation']] == [10., 20.]
    assert original['allocation'] == changed['allocation']
    value = inputs(30., (1., 2.)); value['compartments'].reverse()
    reordered = partition.calculate_partition(inputs=value, growth_profile=profile)
    assert reordered['allocation'] == list(reversed(original['allocation']))


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('weights', [(1., 2., 4.), (0., 0., 0.)])
def test_original_RHS_request_and_atomic_refund_preserve_whole_carbon(profiles, case, weights):
    context = parent.prepare_context(program=CASES[case]['program'], step_seconds=.125, step_count=1, **profiles)
    program, seed, metadata = parent._context(context)
    stage = seed['evaluation']['joint']['crop']
    growth = stage['allocation']['stem_root']['value']
    value = inputs(growth, weights)
    value['model_floor_area'] = deepcopy(program['model_floor_area'])
    result = partition.calculate_partition(inputs=value, growth_profile=profiles['growth_profile'])
    adjustments = result['derivative_adjustments']
    derivative = fsum((stage['derivatives']['stem_root']['value'], adjustments['stem_root']['value']))
    assert abs(fsum((derivative, stage['vegetative_maintenance']['stem_root']['value'], stage['removals']['stem_root']['value'],
                     *(-q['carbohydrate_inflow']['value'] for q in result['allocation'])))) <= result['balance_budgets']['allocation']['value'] + 64 * ulp(growth)
    assert abs(fsum((stage['balance_residual']['carbohydrate']['value'], *(q['value'] for q in adjustments.values())))) <= stage['balance_budget']['carbohydrate']['value'] + result['balance_budgets']['adjustments']['value']
    if not any(weights):
        assert adjustments['buffer']['value'] > growth and adjustments['stem_root']['value'] == -growth
        assert abs(fsum((adjustments['buffer']['value'], adjustments['stem_root']['value']))) > result['balance_budgets']['adjustments']['value']
    assert parent._context(context) == (program, seed, metadata)


@pytest.mark.parametrize('change', [
    lambda v: v.update(extra=1), lambda v: v.update(origin='measured'), lambda v: v.update(policy='auto'),
    lambda v: v.update(input_id=''), lambda v: v.update(input_id='bad id'), lambda v: v.pop('policy'),
    lambda v: v.update(compartments=[]), lambda v: v.update(compartments=tuple(v['compartments'])),
    lambda v: v['compartments'].append(deepcopy(v['compartments'][0])),
    lambda v: v['compartments'][0].update(kind='internode'), lambda v: v['compartments'][1].update(kind='root_system'),
    lambda v: v['compartments'][0].update(kind='implicit_root'), lambda v: v['compartments'][0].update(extra=1),
    lambda v: v['compartments'][0].update(compartment_id='bad id'),
    lambda v: v['model_floor_area'].update(value=0), lambda v: v['model_floor_area'].update(unit='m2_leaf'),
    lambda v: v['requested_stem_root_growth'].update(value=-1), lambda v: v['requested_stem_root_growth'].update(value=True),
    lambda v: v['requested_stem_root_growth'].update(value=float('nan')), lambda v: v['requested_stem_root_growth'].update(value=float('inf')),
    lambda v: v['requested_stem_root_growth'].update(unit='mg_CH2O/s'), lambda v: v['requested_stem_root_growth'].update(extra=1),
    lambda v: v['compartments'][0]['sink_weight'].update(value=-1), lambda v: v['compartments'][0]['sink_weight'].update(value=True),
    lambda v: v['compartments'][0]['sink_weight'].update(unit='mg_DM'), lambda v: v['compartments'][0]['sink_weight'].update(value=float('inf'))])
def test_invalid_scope_basis_units_and_root_inventory_hold(profile, change):
    value = inputs(); change(value)
    with pytest.raises(partition.StemRootPartitionHold):
        partition.calculate_partition(inputs=value, growth_profile=profile)


@pytest.mark.parametrize('growth,weights', [(1e-308, (1.,)), (1., (1e308, 1e308)),
    (1e-100, (1e-250, 1e100)), (1.7e308, (0., 0.)), (10**400, (1.,))])
def test_unrepresentable_positive_flows_costs_or_sums_hold(profile, growth, weights):
    with pytest.raises(partition.StemRootPartitionHold):
        partition.calculate_partition(inputs=inputs(growth, weights), growth_profile=profile)


def test_count_and_serialized_caps_are_separate_from_the_old_whole_RHS_hold(profile):
    with pytest.raises(partition.StemRootPartitionHold):
        partition.calculate_partition(inputs=inputs(1., (1.,) * 513), growth_profile=profile)
    value = inputs(1., (1.,) * 512)
    for i, row in enumerate(value['compartments']): row['compartment_id'] = str(i) + 'x' * 195
    with pytest.raises(partition.StemRootPartitionHold):
        partition.calculate_partition(inputs=value, growth_profile=profile)


def test_profile_cost_drift_and_code_drift_hold(profile, monkeypatch):
    wrong = ReferenceParameters(profile.raw_bytes)
    object.__setattr__(wrong, 'values', MappingProxyType({**wrong.values, 'cStemG': wrong.values['cLeafG']}))
    with pytest.raises(partition.StemRootPartitionHold): partition.calculate_partition(inputs=inputs(), growth_profile=wrong)
    monkeypatch.setattr(partition, 'SOURCE_SHA256', '0' * 64)
    with pytest.raises(partition.StemRootPartitionHold): partition.calculate_partition(inputs=inputs(), growth_profile=profile)


def test_profile_and_source_are_not_mutated_and_growth_is_not_evaluated(profile, monkeypatch):
    before = profile.raw_bytes, dict(profile.values)
    monkeypatch.setattr(partition.source, 'calculate_rates', lambda **_: pytest.fail('unexpected growth evaluation'))
    partition.calculate_partition(inputs=inputs(), growth_profile=profile)
    assert (profile.raw_bytes, dict(profile.values)) == before
