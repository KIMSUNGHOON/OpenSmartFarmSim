from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
from math import nextafter, ulp
from types import MappingProxyType

import pytest

from app import crop_stem_root_carbon_stock_rhs as model
from test_crop_stem_root_partition_climate_rhs import inputs as joint_inputs
from test_growing_geometry_leaf_removal_point import profiles
from test_crop_leaf_partition_climate_rhs import raw

STOCKS = ((.1, .2, .3, .4), (0., .5, 0., .5), (1/3, 1/3, 1/3, 0.), (0., 0., 0., 0.))


def inputs(p, case=0, stock=STOCKS[0], weights=(1., 2., 3., 4.), leaf_weights=(1., 2., 4.)):
    s, leaves, stem = joint_inputs(p, case, leaf_weights=leaf_weights, stem_weights=weights)
    total = s['plant_state'].pop('stem_root')['value']; s['removals'].pop('stem_root')
    stem['policy'] = model.POLICY_ID
    stem['compartments'] = [{**r, 'carbon': {'value': total * share, 'unit': 'mg_CH2O/m2_floor'},
                             'removal': {'value': .001 * (i+1) if share else 0., 'unit': 'mg_CH2O/m2_floor/s'}}
                            for i, (r, share) in enumerate(zip(stem['compartments'], stock, strict=True))]
    return s, leaves, stem


def run(s, leaves, stem, p):
    return model.evaluate_rhs(scenario=s, leaf_stocks=leaves, stem_root_stocks=stem, **p)


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('stock', STOCKS)
@pytest.mark.parametrize('weights', [(1., 2., 3., 4.), (0., 0., 0., 0.), (0., 1., 0., 3.)])
@pytest.mark.parametrize('leaf_weights', [(1., 2., 4.), (0., 0., 0.), (0., 1., 2.)])
def test_independent_organ_maintenance_derivatives_and_whole_carbon(profiles, case, stock, weights, leaf_weights):
    s, leaves, stem = inputs(profiles, case, stock, weights, leaf_weights); before = raw([s, leaves, stem])
    result = run(s, leaves, stem, profiles); original = result['source_stage']
    crop = original['source_stage']['source_stage']['source_joint']['crop']
    d = lambda x: Decimal.from_float(float(x))
    with localcontext() as ctx:
        ctx.prec = 200
        cs = [d(row['carbon']['value']) for row in stem['compartments']]; total = sum(cs)
        agg = float(total); aggregate_M = crop['vegetative_maintenance']['stem_root']['value']
        assert result['stem_root_totals']['carbon']['value'] == agg == original['inputs']['scenario']['plant_state']['stem_root']['value']
        p = {k: d(v) for k, v in profiles['growth_profile'].values.items()}
        phi = (1 - (-p['cRgr'] * p['rgr']).exp()) * (p['q10m'].ln() * (d(s['plant_state']['temperature_filtered_24h']['value']) - p['maintenance_temperature_reference_c']) / p['q10_temperature_interval_c']).exp()
        independent_M = phi * d(agg) * p['cStemM']
        assert abs(d(aggregate_M) - independent_M) <= max(abs(independent_M)*d(5e-12), d(64*ulp(float(independent_M))))
        ms, ds, gs, rs = [], [], [], []
        for row, state, c, allocation in zip(result['stem_root_rates'], stem['compartments'], cs, original['stem_root_partition']['allocation'], strict=True):
            m = float(d(aggregate_M) * c / total) if total else 0.
            g = allocation['carbohydrate_inflow']['value']; r = state['removal']['value']
            expected = d(g) - d(m) - d(r); scale = max(abs(g), abs(m), abs(r))
            assert abs(row['maintenance']['value']-m) <= 2*ulp(m)
            assert abs(d(row['derivative']['value'])-expected) <= d(4*ulp(scale))
            assert row['inflow'] == allocation['carbohydrate_inflow'] and row['removal'] == state['removal']
            assert (row['compartment_id'], row['kind']) == (state['compartment_id'], state['kind'])
            ms.append(d(row['maintenance']['value'])); ds.append(d(row['derivative']['value'])); gs.append(d(g)); rs.append(d(r))
        for name, values in [('maintenance', ms), ('derivative', ds), ('inflow', gs), ('removal', rs)]:
            assert result['stem_root_totals'][name]['value'] == float(sum(values))
        assert result['derivatives']['plant']['stem_root']['value'] == float(sum(ds))
        terms = [d(result['derivatives']['plant'][k]['value']) for k in ('buffer', 'leaf', 'stem_root')]
        terms += [d(q['value']) for q in result['derivatives']['cohorts']['fruit_carbohydrate']]
        old_leaves = original['source_stage']['leaf_totals']
        terms += [d(original['adjusted_carbon']['growth_respiration']['value']), d(old_leaves['maintenance']['value']),
                  sum(ms), d(crop['fruit_maintenance']['value']), d(old_leaves['removal']['value']), sum(rs),
                  d(crop['cohorts']['terminal_outflow']['fruit_carbohydrate']['value']), -d(crop['photosynthesis']['value'])]
        assert abs(sum(terms)) <= d(result['balance_budgets']['carbohydrate']['value'])
        assert abs(sum(ds)+sum(ms)+sum(rs)-sum(gs)) <= d(result['balance_budgets']['stem_root_compartment']['value'])
    for name, value in original['derivatives']['plant'].items():
        if name != 'stem_root': assert result['derivatives']['plant'][name] == value
    for name in ('cohorts', 'climate'): assert result['derivatives'][name] == original['derivatives'][name]
    assert result['adjusted_carbon']['derivatives'] == result['derivatives']['plant']
    assert result['adjusted_carbon']['growth_respiration'] == original['adjusted_carbon']['growth_respiration']
    assert 'stem_root' not in result['inputs']['scenario']['plant_state'] and 'stem_root' not in result['inputs']['scenario']['removals']
    assert result['claim_scope'] == 'synthetic_individual_stem_root_carbon_rhs_only' and result['G0_G4'] == 'not_assessed'
    assert result['calculation_sha256'] == sha256(raw({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
    assert raw([s, leaves, stem]) == before and run(s, leaves, stem, profiles) == result


def test_individual_zero_stock_hold_even_when_aggregate_stage_is_feasible(profiles):
    s, leaves, stem = inputs(profiles, stock=STOCKS[1]); initial = run(s, leaves, stem, profiles)
    g = initial['stem_root_rates'][0]['inflow']['value']; stem['compartments'][0]['removal']['value'] = g
    assert run(s, leaves, stem, profiles)['stem_root_rates'][0]['derivative']['value'] == 0.
    stem['compartments'][0]['removal']['value'] = nextafter(g, float('inf'))
    with pytest.raises(model.StemRootCarbonStockHold, match='DEPLETED_STATE_HOLD'): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('field', ['plant_state', 'removals'])
def test_duplicate_aggregate_is_rejected_before_source_even_if_matching(profiles, monkeypatch, field):
    s, leaves, stem = inputs(profiles)
    unit = 'mg_CH2O/m2_floor' if field == 'plant_state' else 'mg_CH2O/m2_floor/s'
    s[field]['stem_root'] = {'value': sum(r['carbon' if field == 'plant_state' else 'removal']['value'] for r in stem['compartments']), 'unit': unit}
    monkeypatch.setattr(model.source, 'evaluate_rhs', lambda **_: pytest.fail('duplicate aggregate reached source'))
    with pytest.raises(model.StemRootCarbonStockHold): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('field', ['cStemM', 'rgr'])
def test_profile_values_must_match_their_pinned_raw_bytes(profiles, field):
    current = profiles['growth_profile']; wrong = type(current)(current.raw_bytes)
    object.__setattr__(wrong, 'values', MappingProxyType({**wrong.values, field: wrong.values[field]*2}))
    p = {**profiles, 'growth_profile': wrong}
    with pytest.raises(model.StemRootCarbonStockHold, match='PROFILE_HOLD'): run(*inputs(profiles), p)


@pytest.mark.parametrize('change', [
    lambda s, l, t: t.update(extra=1), lambda s, l, t: t.update(origin='measured'), lambda s, l, t: t.update(input_id='other'),
    lambda s, l, t: t.update(policy='automatic'), lambda s, l, t: t['model_floor_area'].update(value=0),
    lambda s, l, t: t['model_floor_area'].update(value=2), lambda s, l, t: t['model_floor_area'].update(unit='m2_leaf'),
    lambda s, l, t: t['model_floor_area'].update(value=True), lambda s, l, t: l['model_floor_area'].update(value=2),
    lambda s, l, t: t.update(compartments=[]), lambda s, l, t: t.update(compartments=tuple(t['compartments'])),
    lambda s, l, t: t['compartments'][0].update(kind='internode'), lambda s, l, t: t['compartments'][1].update(kind='root_system'),
    lambda s, l, t: t['compartments'][1].update(compartment_id=t['compartments'][0]['compartment_id']),
    lambda s, l, t: t['compartments'][0].update(extra=1), lambda s, l, t: t['compartments'][0]['carbon'].update(unit='mg_C'),
    lambda s, l, t: t['compartments'][0]['carbon'].update(value=-1), lambda s, l, t: t['compartments'][0]['carbon'].update(value=True),
    lambda s, l, t: t['compartments'][0]['carbon'].update(value=float('nan')),
    lambda s, l, t: t['compartments'][0]['sink_weight'].update(value=-1),
    lambda s, l, t: t['compartments'][0]['removal'].update(unit='mg_CH2O/s'),
    lambda s, l, t: t['compartments'][0]['removal'].update(value=-1),
    lambda s, l, t: s['plant_state'].update(leaf={'value':1, 'unit':'mg_CH2O/m2_floor'})])
def test_invalid_inventory_does_not_evaluate_source(profiles, monkeypatch, change):
    s, leaves, stem = inputs(profiles); change(s, leaves, stem)
    monkeypatch.setattr(model.source, 'evaluate_rhs', lambda **_: pytest.fail('invalid inventory reached source'))
    with pytest.raises(model.StemRootCarbonStockHold): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('kind', ['model_version', 'code_sha256', 'component_code_sha256', 'profile_sha256', 'raw_input_sha256',
    'scope', 'claim_scope', 'G0_G4', 'calculation_sha256', 'assembled_stock', 'assembled_removal', 'assembled_sinks',
    'source_input_mutation', 'allocation_identity', 'allocation_flow', 'positive_stock_zero_M', 'zero_stock_positive_M'])
def test_rehashed_source_faults_and_actual_binding_hold(profiles, monkeypatch, kind):
    s, leaves, stem = inputs(profiles, stock=STOCKS[3] if kind == 'zero_stock_positive_M' else STOCKS[0])
    fn = model.source.evaluate_rhs
    def changed(**kwargs):
        r = fn(**kwargs)
        if kind == 'assembled_stock': r['inputs']['scenario']['plant_state']['stem_root']['value'] += 1
        elif kind == 'assembled_removal': r['inputs']['scenario']['removals']['stem_root']['value'] += 1
        elif kind == 'assembled_sinks': r['inputs']['stem_root_stage']['compartments'].reverse()
        elif kind == 'source_input_mutation': kwargs['leaf_stocks']['leaves'][0]['carbon']['value'] += 1
        elif kind == 'allocation_identity': r['stem_root_partition']['allocation'][0]['compartment_id'] = 'other'
        elif kind == 'allocation_flow': r['stem_root_partition']['allocation'][0]['carbohydrate_inflow']['value'] += 1
        elif kind in ('positive_stock_zero_M', 'zero_stock_positive_M'):
            r['source_stage']['source_stage']['source_joint']['crop']['vegetative_maintenance']['stem_root']['value'] = 0. if kind == 'positive_stock_zero_M' else 1.
        elif kind in ('component_code_sha256', 'profile_sha256'): r[kind] = {k:'0'*64 for k in r[kind]}
        else: r[kind] = 'wrong'
        if kind != 'calculation_sha256': r['calculation_sha256'] = sha256(model.source._canonical({k:v for k,v in r.items() if k != 'calculation_sha256'})).hexdigest()
        return r
    monkeypatch.setattr(model.source, 'evaluate_rhs', changed)
    with pytest.raises(model.StemRootCarbonStockHold): run(s, leaves, stem, profiles)


def test_each_component_once_and_detached_original_source(profiles, monkeypatch):
    s, leaves, stem = inputs(profiles); leaf = model.source.source.source; climate = leaf.source; calls = {}
    targets = [(model.source, 'evaluate_rhs', 'stem_joint'), (model.source.source, 'evaluate_rhs', 'leaf_stocks'),
               (leaf, 'evaluate_rhs', 'leaf_joint'), (climate, 'evaluate_rhs', 'climate'),
               (leaf.partition, 'calculate_partition', 'leaf_partition'), (model.part, 'calculate_partition', 'stem_partition'),
               (climate.carbon, 'calculate_plant_rates', 'carbon'), (climate.carbon.optical, 'calculate_photosynthesis', 'photosynthesis'),
               (climate.area, 'calculate_area_energy', 'heat_area'), (climate.exchange, 'calculate_exchange', 'vapor_exchange')]
    for module, name, key in targets:
        fn = getattr(module, name)
        def counted(*, _fn=fn, _key=key, **kwargs): calls[_key] = calls.get(_key, 0)+1; return _fn(**kwargs)
        monkeypatch.setattr(module, name, counted)
    r = run(s, leaves, stem, profiles); assert calls == {key:1 for _, _, key in targets}
    saved = raw(r['source_stage']); r['derivatives']['plant']['stem_root']['value'] = 9
    r['adjusted_carbon']['derivatives']['buffer']['value'] = 9
    r['inputs']['stem_root_stocks']['compartments'][0]['carbon']['value'] = 0
    assert raw(r['source_stage']) == saved and stem['compartments'][0]['carbon']['value'] > 0


@pytest.mark.parametrize('kind', ['own_code', 'source_code', 'positive_maintenance_underflow', 'aggregate_overflow', 'count_overflow', 'bytes_overflow', 'original_source_hold'])
def test_code_numeric_capacity_and_original_source_holds(profiles, monkeypatch, kind):
    s, leaves, stem = inputs(profiles)
    if kind == 'own_code': monkeypatch.setattr(model, 'CODE_SHA256', '0'*64)
    elif kind == 'source_code': monkeypatch.setitem(model.COMPONENT_CODE_SHA256, model.source.__name__, '0'*64)
    elif kind == 'positive_maintenance_underflow': stem['compartments'][0]['carbon']['value'] = float.fromhex('0x1.0p-1022')
    elif kind == 'aggregate_overflow':
        for row in stem['compartments']: row['carbon']['value'] = float.fromhex('0x1.fffffffffffffp+1023')
    elif kind == 'count_overflow':
        stem['compartments'] = [dict(deepcopy(stem['compartments'][1]), compartment_id=f'i{i}') for i in range(512)] + [stem['compartments'][0]]
    elif kind == 'bytes_overflow': stem['extra'] = 'x'*model.MAX_BYTES
    elif kind == 'original_source_hold':
        for row in leaves['leaves']: row['carbon']['value'] = 0.
    with pytest.raises(model.StemRootCarbonStockHold): run(s, leaves, stem, profiles)


def test_root_only_stock_and_whole_zero_stock_zero_sinks_are_explicit(profiles):
    for stock, weights in [((1.,), (1.,)), ((0.,), (1.,)), ((0.,), (0.,))]:
        r = run(*inputs(profiles, stock=stock, weights=weights), profiles)
        assert len(r['stem_root_rates']) == 1 and r['stem_root_rates'][0]['kind'] == 'root_system'
        if not any(stock):
            assert r['stem_root_totals']['maintenance']['value'] == 0.
            assert r['stem_root_rates'][0]['derivative']['value'] >= 0
        if not any(stock) and not any(weights): assert r['stem_root_rates'][0]['derivative']['value'] == 0.


@pytest.mark.parametrize('field', ['leaf_ids', 'leaves'])
def test_original_leaf_list_contract_is_checked_before_JSON_capture(profiles, field):
    s, leaves, stem = inputs(profiles); leaves[field] = tuple(leaves[field])
    with pytest.raises(model.StemRootCarbonStockHold, match='INPUT_HOLD'): run(s, leaves, stem, profiles)


@pytest.mark.parametrize('count', [1, 256, 512])
def test_actual_inventory_output_capacity_without_raising_caps(profiles, count):
    s, leaves, stem = inputs(profiles); total = sum(r['carbon']['value'] for r in stem['compartments']); template = stem['compartments'][0]
    rows = []
    for i in range(count):
        row = deepcopy(template); row.update(compartment_id=f'c{i}', kind='root_system' if i == 0 else 'internode')
        row['carbon']['value'] = total/count; row['sink_weight']['value'] = 1.; row['removal']['value'] = 0.; rows.append(row)
    stem['compartments'] = rows
    if count == 512:
        with pytest.raises(model.StemRootCarbonStockHold, match='CAPACITY_HOLD: 512KiB stem/root stock'): run(s, leaves, stem, profiles)
    else:
        r = run(s, leaves, stem, profiles)
        assert len(r['stem_root_rates']) == count and len(model._canonical(r)) <= 524288


def test_same_per_floor_quantities_are_not_multiplied_by_the_footprint(profiles):
    s, leaves, stem = inputs(profiles); first = run(s, leaves, stem, profiles)
    for quantity in (s['geometry']['model_floor_area'], leaves['model_floor_area'], stem['model_floor_area']): quantity['value'] *= 2
    second = run(s, leaves, stem, profiles)
    assert second['stem_root_totals'] == first['stem_root_totals'] and second['stem_root_rates'] == first['stem_root_rates']


def test_root_may_appear_last_and_input_order_is_preserved(profiles):
    s, leaves, stem = inputs(profiles); first = run(s, leaves, stem, profiles)
    stem['compartments'].reverse(); second = run(s, leaves, stem, profiles)
    assert second['stem_root_rates'] == list(reversed(first['stem_root_rates']))
    assert second['stem_root_totals'] == first['stem_root_totals']


def test_total_zero_stock_with_exactly_funded_removal_is_flow_through(profiles):
    s, leaves, stem = inputs(profiles, stock=STOCKS[3]); initial = run(s, leaves, stem, profiles)
    g = initial['stem_root_rates'][0]['inflow']['value']; stem['compartments'][0]['removal']['value'] = g
    balanced = run(s, leaves, stem, profiles)
    assert balanced['stem_root_rates'][0]['derivative']['value'] == 0. and balanced['stem_root_totals']['maintenance']['value'] == 0.
    stem['compartments'][0]['removal']['value'] = nextafter(g, float('inf'))
    with pytest.raises(model.StemRootCarbonStockHold, match='DEPLETED_STATE_HOLD'): run(s, leaves, stem, profiles)
