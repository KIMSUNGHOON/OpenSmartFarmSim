from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
from math import ulp
from types import MappingProxyType

import pytest

from app import crop_stem_root_partition_climate_rhs as model
from test_crop_leaf_carbon_stock_rhs import inputs as leaf_inputs
from test_growing_geometry_leaf_removal_point import profiles
from test_crop_leaf_partition_climate_rhs import raw


def inputs(p, case=0, leaf_weights=(1., 2., 4.), stem_weights=(1., 2., 3., 4.)):
    scenario, leaves = leaf_inputs(p, case, weights=leaf_weights)
    stem = {'input_id': scenario['input_id'], 'origin': 'synthetic', 'policy': model.partition.POLICY_ID,
            'model_floor_area': deepcopy(scenario['geometry']['model_floor_area']),
            'compartments': [{'compartment_id': 'own-roots' if i == 0 else f'own-internode-{i}',
                              'kind': 'root_system' if i == 0 else 'internode',
                              'sink_weight': {'value': w, 'unit': '1'}} for i, w in enumerate(stem_weights)]}
    return scenario, leaves, stem


def run(s, leaves, stem, p):
    return model.evaluate_rhs(scenario=s, leaf_stocks=leaves, stem_root_stage=stem, **p)


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('leaf_weights', [(1., 2., 4.), (0., 0., 0.), (0., 1., 2.)])
@pytest.mark.parametrize('stem_weights', [(1., 2., 3., 4.), (0., 0., 0., 0.), (0., 1., 0., 3.)])
def test_same_stage_independent_Decimal_ledger_and_original_values(profiles, case, leaf_weights, stem_weights):
    s, leaves, stem = inputs(profiles, case, leaf_weights, stem_weights)
    before = raw([s, leaves, stem])
    original = model.source.evaluate_rhs(scenario=s, leaf_stocks=leaves, **profiles)
    result = run(s, leaves, stem, profiles)
    assert result['source_stage'] == original
    assert result['source_stage_calculation_sha256'] == original['calculation_sha256']
    crop = original['source_stage']['source_joint']['crop']
    g = crop['allocation']['stem_root']['value']
    allocated = result['stem_root_partition']
    assert allocated['inputs']['requested_stem_root_growth'] == crop['allocation']['stem_root']
    with localcontext() as ctx:
        ctx.prec = 200
        d = Decimal.from_float
        total = sum(d(w) for w in stem_weights)
        want_flows = [float(d(g) * d(w) / total) if total else 0. for w in stem_weights]
        for row, wanted in zip(allocated['allocation'], want_flows, strict=True):
            assert abs(row['carbohydrate_inflow']['value'] - wanted) <= 2 * ulp(wanted)
        deferred = d(0.) if total else d(g)
        avoided = d(profiles['growth_profile'].values['cStemG']) * deferred
        expected = {'buffer': d(original['derivatives']['plant']['buffer']['value']) + deferred + avoided,
                    'stem_root': d(original['derivatives']['plant']['stem_root']['value']) - deferred,
                    'growth_respiration': d(original['source_stage']['adjusted_carbon']['growth_respiration']['value']) - avoided}
        actual = {k: result['derivatives']['plant'][k]['value'] for k in ('buffer', 'stem_root')}
        actual['growth_respiration'] = result['adjusted_carbon']['growth_respiration']['value']
        for name in actual:
            scale = max(1., abs(float(expected[name])), abs(g))
            assert abs(d(actual[name]) - expected[name]) <= d(8 * ulp(scale))
        plant = result['derivatives']['plant']
        terms = [d(plant[k]['value']) for k in ('buffer', 'leaf', 'stem_root')]
        terms += [d(q['value']) for q in result['derivatives']['cohorts']['fruit_carbohydrate']]
        terms += [d(actual['growth_respiration']), d(original['leaf_totals']['maintenance']['value']),
                  d(crop['vegetative_maintenance']['stem_root']['value']), d(crop['fruit_maintenance']['value']),
                  d(original['leaf_totals']['removal']['value']), d(crop['removals']['stem_root']['value']),
                  d(crop['cohorts']['terminal_outflow']['fruit_carbohydrate']['value']), -d(crop['photosynthesis']['value'])]
        assert abs(sum(terms)) <= d(result['balance_budgets']['carbohydrate']['value'])
        st = d(plant['stem_root']['value']) + d(crop['vegetative_maintenance']['stem_root']['value']) + d(crop['removals']['stem_root']['value'])
        st -= sum(d(row['carbohydrate_inflow']['value']) for row in allocated['allocation'])
        assert abs(st) <= d(result['balance_budgets']['stem_root_compartment']['value'])
    for field in ('leaf_rates', 'leaf_totals', 'aggregation_residuals', 'aggregation_budgets'):
        assert result['source_stage'][field] == original[field]
    for field in ('cohorts', 'climate'):
        assert result['derivatives'][field] == original['derivatives'][field]
    for field, value in original['derivatives']['plant'].items():
        if field not in ('buffer', 'stem_root'): assert result['derivatives']['plant'][field] == value
    if any(stem_weights):
        assert raw(result['derivatives']) == raw(original['derivatives'])
        assert result['adjusted_carbon']['growth_respiration'] == original['source_stage']['adjusted_carbon']['growth_respiration']
    assert result['G0_G4'] == 'not_assessed' and result['geometry_binding'] == 'declared_synthetic_sinks_only'
    assert result['claim_scope'] == 'synthetic_stem_root_partition_joint_rhs_only'
    assert result['calculation_sha256'] == sha256(raw({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
    assert raw([s, leaves, stem]) == before and run(s, leaves, stem, profiles) == result


def test_source_and_partition_each_once_and_no_caller_growth_override(profiles, monkeypatch):
    s, leaves, stem = inputs(profiles); calls = {}
    leaf = model.source.source; climate = leaf.source
    targets = [(model.source, 'evaluate_rhs', 'leaf_stocks'), (leaf, 'evaluate_rhs', 'leaf_joint'),
               (climate, 'evaluate_rhs', 'climate'), (leaf.partition, 'calculate_partition', 'leaf_partition'),
               (model.partition, 'calculate_partition', 'stem_partition'),
               (climate.carbon, 'calculate_plant_rates', 'carbon'), (climate.carbon.optical, 'calculate_photosynthesis', 'photosynthesis'),
               (climate.area, 'calculate_area_energy', 'heat_area'), (climate.exchange, 'calculate_exchange', 'vapor_exchange')]
    for module, name, key in targets:
        fn = getattr(module, name)
        def counted(*, _fn=fn, _key=key, **kwargs): calls[_key] = calls.get(_key, 0) + 1; return _fn(**kwargs)
        monkeypatch.setattr(module, name, counted)
    run(s, leaves, stem, profiles)
    expected = {key: 1 for _, _, key in targets}
    assert calls == expected
    stem['requested_stem_root_growth'] = {'value': 99., 'unit': 'mg_CH2O/m2_floor/s'}
    with pytest.raises(model.StemRootClimateHold): run(s, leaves, stem, profiles)
    assert calls == expected


@pytest.mark.parametrize('change', [
    lambda s, l, t: t.update(extra=1), lambda s, l, t: t.update(origin='measured'), lambda s, l, t: t.update(input_id='other'),
    lambda s, l, t: t.update(policy='auto'), lambda s, l, t: t['model_floor_area'].update(value=2),
    lambda s, l, t: t['model_floor_area'].update(value=True), lambda s, l, t: t['model_floor_area'].update(unit='m2_leaf'),
    lambda s, l, t: l['model_floor_area'].update(value=2), lambda s, l, t: t.update(compartments=[]),
    lambda s, l, t: t['compartments'][0].update(kind='internode'), lambda s, l, t: t['compartments'][1].update(kind='root_system'),
    lambda s, l, t: t['compartments'].append(deepcopy(t['compartments'][0])),
    lambda s, l, t: t['compartments'][0]['sink_weight'].update(value=-1),
    lambda s, l, t: t['compartments'][0]['sink_weight'].update(value=float('nan')),
    lambda s, l, t: t['compartments'][0]['sink_weight'].update(unit='mg_DM')])
def test_invalid_stage_footprint_or_root_holds(profiles, change):
    s, leaves, stem = inputs(profiles); change(s, leaves, stem)
    with pytest.raises(model.StemRootClimateHold): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('field,value', [('model_version', 'wrong'), ('code_sha256', '0' * 64), ('raw_input_sha256', '0' * 64),
    ('scope', 'production'), ('claim_scope', 'actual_growth'), ('G0_G4', 'approved'), ('calculation_sha256', '0' * 64)])
def test_source_metadata_drift_rejected_even_after_rehash(profiles, monkeypatch, field, value):
    fn = model.source.evaluate_rhs
    def changed(**kwargs):
        result = fn(**kwargs); result[field] = value
        if field != 'calculation_sha256': result['calculation_sha256'] = sha256(model.source._canonical({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
        return result
    monkeypatch.setattr(model.source, 'evaluate_rhs', changed)
    with pytest.raises(model.StemRootClimateHold, match='SOURCE_HOLD'): run(*inputs(profiles), profiles)


@pytest.mark.parametrize('kind', ['source_profile', 'source_input_mutation', 'partition_code', 'partition_profile', 'partition_input',
    'partition_scope', 'partition_identity', 'partition_unit', 'partition_imbalanced_flow'])
def test_source_or_partition_binding_and_ledger_faults_hold(profiles, monkeypatch, kind):
    if kind.startswith('source_'):
        fn = model.source.evaluate_rhs
        def changed(**kwargs):
            result = fn(**kwargs)
            if kind == 'source_profile': result['profile_sha256']['growth'] = '0' * 64
            else: kwargs['leaf_stocks']['leaves'][0]['carbon']['value'] += 1
            result['calculation_sha256'] = sha256(model.source._canonical({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
            return result
        monkeypatch.setattr(model.source, 'evaluate_rhs', changed)
    else:
        fn = model.partition.calculate_partition
        def changed(**kwargs):
            result = fn(**kwargs)
            if kind == 'partition_code': result['code_sha256'] = '0' * 64
            elif kind == 'partition_profile': result['profile_sha256'] = '0' * 64
            elif kind == 'partition_input': result['inputs']['requested_stem_root_growth']['value'] += 1
            elif kind == 'partition_scope': result['claim_scope'] = 'actual_growth'
            elif kind == 'partition_identity': result['allocation'][0]['compartment_id'] = 'other'
            elif kind == 'partition_unit': result['allocation'][0]['carbohydrate_inflow']['unit'] = 'mg_DM/s'
            else: result['allocation'][0]['carbohydrate_inflow']['value'] += 1
            result['calculation_sha256'] = sha256(model.partition._canonical({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
            return result
        monkeypatch.setattr(model.partition, 'calculate_partition', changed)
    with pytest.raises(model.StemRootClimateHold): run(*inputs(profiles), profiles)


def test_original_depleted_state_hold_is_not_rescued_or_allocated(profiles, monkeypatch):
    s, leaves, stem = inputs(profiles, stem_weights=(0., 0., 0., 0.))
    for row in leaves['leaves']: row['carbon']['value'] = 0.
    monkeypatch.setattr(model.partition, 'calculate_partition', lambda **_: pytest.fail('partition called after source hold'))
    with pytest.raises(model.StemRootClimateHold, match='STATE_HOLD'): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('kind', ['own_code', 'source_code', 'profile_values'])
def test_source_code_and_profile_fences(profiles, monkeypatch, kind):
    s, leaves, stem = inputs(profiles)
    if kind == 'own_code': monkeypatch.setattr(model, 'CODE_SHA256', '0' * 64)
    elif kind == 'source_code': monkeypatch.setitem(model.COMPONENT_CODE_SHA256, model.source.__name__, '0' * 64)
    else:
        p = dict(profiles); current = p['growth_profile']; wrong = type(current)(current.raw_bytes)
        object.__setattr__(wrong, 'values', MappingProxyType({**wrong.values, 'cStemG': wrong.values['cLeafG']})); profiles = {**p, 'growth_profile': wrong}
    with pytest.raises(model.StemRootClimateHold): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('count', [1, 512])
def test_explicit_compartment_count_boundaries_without_claiming_whole_leaf_RHS_maximum(profiles, count):
    result = run(*inputs(profiles, stem_weights=(1.,) * count), profiles)
    assert len(result['stem_root_partition']['allocation']) == count
    assert result['organ_carbon_stocks'] == 'not_allocated_in_this_instantaneous_inflow_stage'


def test_declared_count_and_actual_serialized_caps(profiles):
    with pytest.raises(model.StemRootClimateHold, match='CAPACITY_HOLD'):
        run(*inputs(profiles, stem_weights=(1.,) * 513), profiles)
    s, leaves, stem = inputs(profiles); stem['extra'] = 'x' * model.MAX_BYTES
    with pytest.raises(model.StemRootClimateHold, match='CAPACITY_HOLD'): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('mode', ['receiving_growth', 'no_growth_no_removal', 'deferred_growth_with_removal'])
def test_zero_stem_stock_cannot_gain_an_outward_derivative_after_deferral(profiles, mode):
    s, leaves, stem = inputs(profiles)
    s['plant_state']['stem_root']['value'] = 0.
    s['removals']['stem_root']['value'] = 0.
    original = model.source.evaluate_rhs(scenario=s, leaf_stocks=leaves, **profiles)
    g = original['source_stage']['source_joint']['crop']['allocation']['stem_root']['value']
    if mode != 'no_growth_no_removal': s['removals']['stem_root']['value'] = g / 2
    if mode != 'receiving_growth':
        for row in stem['compartments']: row['sink_weight']['value'] = 0.
    baseline = model.source.evaluate_rhs(scenario=s, leaf_stocks=leaves, **profiles)
    assert baseline['derivatives']['plant']['stem_root']['value'] >= 0
    if mode == 'deferred_growth_with_removal':
        with pytest.raises(model.StemRootClimateHold, match='DEPLETED_STATE_HOLD'): run(s, leaves, stem, profiles)
    else:
        result = run(s, leaves, stem, profiles)
        assert result['derivatives']['plant']['stem_root']['value'] >= 0
        if mode == 'no_growth_no_removal': assert result['derivatives']['plant']['stem_root']['value'] == 0
