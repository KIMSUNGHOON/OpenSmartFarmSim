from decimal import Decimal, localcontext
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import ulp

import pytest

from app import crop_leaf_funded_birth_point as model
from test_crop_leaf_carbon_stock_dynamics import program, q
from test_crop_growing_geometry_climate import profiles


def setup_point(profiles, case=0, cut=2, count=1, dt=.125):
    ctx = model.resume.prepare_context(program=program(case), step_seconds=dt, step_count=4, **profiles)
    cp = model.resume.start(ctx)
    if cut:
        cp = model.resume.advance_chunk(ctx, cp, cut)['checkpoint']
    raw = model.resume.checkpoint_bytes(ctx, cp)
    at = Fraction.from_float(dt)*cut
    events = []
    for i in range(count):
        leaf = deepcopy(ctx.program['leaves'][0])
        area = model.resume.short.old.leaf_area._area_at(Fraction(0), leaf['curve'])
        leaf.update(leaf_id='new-leaf-'+str(i), thermal_age=q(0., 'degC_day'), initial_area=area,
                    initial_carbon=q(.25*(i+1), model.MASS))
        events.append({'event_id': 'event-'+str(i), 'attachment_internode_id': 'internode-'+str(i),
                       'incoming_temperature': q(22.+i%3, 'degC'), 'leaf': leaf})
    inputs = {'schema_version': 'leaf-funded-birth-point-input-v1', 'input_id': 'funded-birth-point',
              'origin': 'synthetic', 'policy': model.POLICY, 'context_sha256': ctx.root_sha256,
              'checkpoint_sha256': cp.sha256, 'model_floor_area': ctx.program['model_floor_area'],
              'at_elapsed_seconds_exact': {'numerator': str(at.numerator), 'denominator': str(at.denominator), 'unit': 's'},
              'events': events}
    return dict(context=ctx, raw_checkpoint=raw, expected_sha256=sha256(raw).hexdigest(), inputs=inputs)


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('cut', [0, 2])
def test_atomic_point_preserves_original_blocks_and_past_ledgers(profiles, case, cut):
    kw = setup_point(profiles, case, cut, 2)
    before_input = deepcopy(kw['inputs'])
    before = model.resume.restore_checkpoint(kw['context'], kw['raw_checkpoint'], expected_sha256=kw['expected_sha256']).value
    r = model.apply_births(**kw)
    old = before['last_confirmed']['state']
    new = r['after_sample']['state']
    assert len(new) == 122
    assert new[1:104] == old[1:104] and new[105:107] == old[105:107]
    assert new[107:110] == old[107:110] and new[110:112] == [0., 0.]
    assert new[112:115] == old[110:113] and new[117:120] == old[113:116]
    assert new[120:] == [.25, .5]
    assert r['before_checkpoint'] == before
    assert r['after_sample']['curve_invariant_changes'][:3] == before['last_confirmed']['curve_invariant_changes']
    assert r['after_sample']['curve_invariant_changes'][3:] == [q(0., 'm2')]*2
    assert r['after_sample']['elapsed_seconds'] == before['last_confirmed']['elapsed_seconds']
    assert all(abs(v['residual']['value']) <= v['budget']['value'] for v in r['balances'].values())
    assert kw['inputs'] == before_input and model.apply_births(**kw) == r
    assert r['checkpoint'] is None and r['elapsed_steps_advanced'] == 0 and r['G0_G4'] == 'not_assessed'


@pytest.mark.parametrize('masses', [(1.,), (.1, .2), (3.5, 2.25, .125)])
def test_explicit_same_floor_structural_growth_has_one_debit_and_respiration(masses):
    with localcontext() as ctx:
        ctx.prec = 110
        total = sum(map(Decimal.from_float, masses), Decimal(0))
        cost = Decimal.from_float(.28)
        structural, respiration, debit, after = model._fund(100., masses, .28)
        assert structural == float(total)
        assert respiration == float(total*cost)
        assert debit == float(total*(1+cost))
        assert after == float(Decimal(100)-Decimal.from_float(debit))
        assert abs(after-100+structural+respiration) <= 64*ulp(100.)


@pytest.mark.parametrize('mass', [100., 101., 1e-320])
def test_depleted_or_unrepresentable_funding_is_held(mass):
    with pytest.raises(model.FundedBirthHold):
        model._fund(100., [mass], .28)


@pytest.mark.parametrize('temperature', [10., 22., 34.])
def test_decimal_carbon_and_sensible_energy_are_independent_of_area_to_mass(profiles, temperature):
    kw = setup_point(profiles, count=2, dt=1/3)
    for event in kw['inputs']['events']:
        event['incoming_temperature']['value'] = temperature
    r = model.apply_births(**kw)
    p = r['after_program']
    before, after = deepcopy(r['before_checkpoint']['last_confirmed']), r['after_sample']
    with localcontext() as ctx:
        ctx.prec = 110
        dec = Decimal.from_float
        masses = [dec(e['leaf']['initial_carbon']['value']) for e in kw['inputs']['events']]
        growth = dec(profiles['growth_profile'].values['cLeafG'])*sum(masses)
        assert r['point_flows']['growth_respiration']['value'] == float(growth)
        k = dec(p['scenario']['parameters']['leaf_heat_capacity']['value'])
        floor = dec(p['model_floor_area']['value'])
        ref = dec(p['scenario']['parameters']['reference_temperature']['value'])
        caps, energies = [], []
        for row in r['birth_receipts']:
            area = dec(row['initialization']['state']['area']['value'])
            assert area > 0
            capacity = float(k*area/floor)
            energy = float(dec(capacity)*(dec(temperature)-ref))
            assert row['capacity_in']['value'] == capacity and row['sensible_in']['value'] == energy
            caps.append(dec(capacity)); energies.append(dec(energy))
        assert r['point_flows']['capacity_in']['value'] == float(sum(caps))
        assert after['state'][104] == float(dec(before['state'][104])+dec(float(sum(energies))))
        remaining = dec(after['state'][0])-dec(before['state'][0])+sum(masses)+growth
        assert abs(remaining) <= dec(r['balances']['buffer']['budget']['value'])
    before_raw = kw['raw_checkpoint']
    r['after_program']['leaves'][0]['curve']['values']['maximum_area']['value'] = 999.
    r['before_checkpoint']['last_confirmed']['state'][0] = 0.
    assert kw['raw_checkpoint'] == before_raw
    again = model.apply_births(**kw)
    assert again['before_checkpoint']['last_confirmed'] == before


@pytest.mark.parametrize('change', [
    lambda v: v.update(origin='observed'), lambda v: v.update(policy='unfunded'),
    lambda v: v.update(extra=1), lambda v: v.pop('model_floor_area'),
    lambda v: v.update(events=[]), lambda v: v.update(events={}),
    lambda v: v.update(context_sha256='0'*64), lambda v: v.update(checkpoint_sha256='0'*64),
    lambda v: v['model_floor_area'].update(value=9.), lambda v: v['model_floor_area'].update(unit='m2'),
    lambda v: v['at_elapsed_seconds_exact'].update(numerator='3'),
    lambda v: v['at_elapsed_seconds_exact'].update(denominator='2'),
    lambda v: v['at_elapsed_seconds_exact'].update(unit='min'),
    lambda v: v['events'][0].update(event_id=''), lambda v: v['events'][0].update(attachment_internode_id=''),
    lambda v: v['events'][0].update(extra=1), lambda v: v['events'][0]['leaf'].update(leaf_id=''),
    lambda v: v['events'][0]['leaf'].update(extra=1), lambda v: v['events'][0]['leaf'].pop('initial_carbon'),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=0.),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=-1.),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(unit='mg_CH2O'),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=True),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=1e-320),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=1e100),
    lambda v: v['events'][0]['leaf']['thermal_age'].update(value=1.),
    lambda v: v['events'][0]['leaf']['sink_weight'].update(value=-1.),
    lambda v: v['events'][0]['leaf']['carbon_removal'].update(value=-1.),
    lambda v: v['events'][0]['leaf']['base_temperature'].update(value=35.),
    lambda v: v['events'][0]['leaf']['initial_area'].update(value=0.),
    lambda v: v['events'][0]['leaf']['initial_area'].update(value=.25),
    lambda v: v['events'][0]['leaf']['curve'].update(extra=1),
    lambda v: v['events'][0]['incoming_temperature'].update(value=9.),
    lambda v: v['events'][0]['incoming_temperature'].update(value=35.),
    lambda v: v['events'][0]['incoming_temperature'].update(value=float('nan')),
    lambda v: v['events'][0]['incoming_temperature'].update(value=float('inf')),
    lambda v: v['events'][0]['incoming_temperature'].update(value=True),
    lambda v: v['events'][0]['incoming_temperature'].update(unit='K'),
])
def test_closed_inputs_and_unsupported_point_fail_atomically(profiles, change):
    kw = setup_point(profiles)
    original = kw['raw_checkpoint']
    change(kw['inputs'])
    with pytest.raises(model.FundedBirthHold):
        model.apply_births(**kw)
    assert kw['raw_checkpoint'] == original


def test_current_only_evaluation_no_reinitialization_or_past_replay(profiles, monkeypatch):
    kw = setup_point(profiles)
    calls = []
    evaluate = model.resume.short._evaluate
    def counted(p, y, profiles):
        calls.append((len(p['leaves']), tuple(y)))
        return evaluate(p, y, profiles)
    def forbidden(*a, **k):
        raise AssertionError('no reprepare or past integration')
    monkeypatch.setattr(model.resume.short, '_evaluate', counted)
    monkeypatch.setattr(model.resume.short, '_prepare', forbidden)
    monkeypatch.setattr(model.resume.short.old, '_prepare', forbidden)
    monkeypatch.setattr(model.resume.short.old, '_evaluate', forbidden)
    monkeypatch.setattr(model.resume, 'advance_chunk', forbidden)
    monkeypatch.setattr(model.resume.short, 'integrate', forbidden)
    r = model.apply_births(**kw)
    assert [n for n, _ in calls] == [3, 4]
    assert r['checkpoint_validation_stage_evaluations'] == r['after_stage_evaluations'] == 1


@pytest.mark.parametrize('kind', ['old_leaf', 'new_leaf', 'event'])
def test_duplicate_identity_has_no_committed_transfer(profiles, kind):
    kw = setup_point(profiles, count=2)
    events = kw['inputs']['events']
    if kind == 'old_leaf':
        events[0]['leaf']['leaf_id'] = kw['context'].program['leaves'][0]['leaf_id']
    elif kind == 'new_leaf':
        events[1]['leaf']['leaf_id'] = events[0]['leaf']['leaf_id']
    else:
        events[1]['event_id'] = events[0]['event_id']
    with pytest.raises(model.FundedBirthHold, match='EVENT_HOLD'):
        model.apply_births(**kw)


def test_512_resulting_leaves_and_2mib_boundary(profiles):
    kw = setup_point(profiles, count=509)
    for event in kw['inputs']['events']:
        event['leaf']['initial_carbon']['value'] = .001
    r = model.apply_births(**kw)
    assert len(r['after_program']['leaves']) == 512
    assert len(r['after_sample']['state']) == 107+3*512
    assert len(model._canonical(r)) < 2*1024**2
    kw['inputs']['events'].append(deepcopy(kw['inputs']['events'][0]))
    with pytest.raises(model.FundedBirthHold, match='CAPACITY_HOLD'):
        model.apply_births(**kw)
    with pytest.raises(model.FundedBirthHold, match='CAPACITY_HOLD'):
        model._canonical({'oversized': 'a'*(2*1024**2)})


@pytest.mark.parametrize('which', ['point', 'clock', 'parent'])
def test_source_code_fences(profiles, monkeypatch, which):
    kw = setup_point(profiles)
    name = model.__file__ if which == 'point' else model.clock.__file__ if which == 'clock' else model.resume.__file__
    original = model.Path.read_bytes
    def changed(path):
        return b'changed source' if str(path) == name else original(path)
    monkeypatch.setattr(model.Path, 'read_bytes', changed)
    with pytest.raises(model.FundedBirthHold, match='CODE_HOLD'):
        model.apply_births(**kw)


@pytest.mark.parametrize('kind', ['digest', 'bytes', 'profile'])
def test_trusted_digest_and_original_profile_are_required(profiles, kind):
    from dataclasses import replace
    from types import SimpleNamespace
    kw = setup_point(profiles)
    if kind == 'digest':
        kw['expected_sha256'] = '0'*64
    elif kind == 'bytes':
        kw['raw_checkpoint'] += b' '
    else:
        ctx = kw['context']
        altered = SimpleNamespace(sha256='0'*64)
        kw['context'] = replace(ctx, _profiles=(altered, *ctx._profiles[1:]))
    with pytest.raises(model.FundedBirthHold):
        model.apply_births(**kw)


def test_after_rhs_failure_cannot_publish_partial_point(profiles, monkeypatch):
    kw = setup_point(profiles)
    original = model.resume.short._evaluate
    def fail_after(p, y, profiles):
        if len(p['leaves']) > 3:
            raise model.resume.short.StockDynamicsHold('after failure')
        return original(p, y, profiles)
    monkeypatch.setattr(model.resume.short, '_evaluate', fail_after)
    with pytest.raises(model.FundedBirthHold, match='after failure'):
        model.apply_births(**kw)
    assert sha256(kw['raw_checkpoint']).hexdigest() == kw['expected_sha256']


def test_one_existing_leaf_and_one_new_leaf_preserve_general_layout(profiles):
    kw = setup_point(profiles, cut=0)
    p = program()
    area_share = p['leaves'][0]['initial_area']['value']/sum(x['initial_area']['value'] for x in p['leaves'])
    p['scenario']['climate_state']['canopy_sensible_energy']['value'] *= area_share
    p['leaves'] = p['leaves'][:1]
    ctx = model.resume.prepare_context(program=p, step_seconds=.125, step_count=4, **profiles)
    cp = model.resume.start(ctx)
    kw.update(context=ctx, raw_checkpoint=model.resume.checkpoint_bytes(ctx, cp), expected_sha256=cp.sha256)
    kw['inputs'].update(context_sha256=ctx.root_sha256, checkpoint_sha256=cp.sha256)
    r = model.apply_births(**kw)
    y, z = cp.value['last_confirmed']['state'], r['after_sample']['state']
    assert len(z) == 113 and z[107:109] == [y[107], 0.]
    assert z[109] == y[108] and z[111:] == [y[109], .25]


def test_new_initial_area_receipt_snaps_once_without_touching_old_current_area(profiles):
    kw = setup_point(profiles)
    requested = kw['inputs']['events'][0]['leaf']['initial_area']
    canonical = requested['value']
    requested['value'] *= 1+2e-13
    r = model.apply_births(**kw)
    assert r['after_sample']['state'][114] == canonical
    assert r['birth_receipts'][0]['initialization']['state']['anchor']['requested_area'] == requested
    assert r['after_sample']['state'][111:114] == r['before_checkpoint']['last_confirmed']['state'][110:113]


def test_source_identity_is_checked_again_after_calculation(profiles, monkeypatch):
    kw = setup_point(profiles)
    evaluate = model.resume.short._evaluate
    def changed_after(p, y, profiles):
        result = evaluate(p, y, profiles)
        if len(p['leaves']) > 3:
            monkeypatch.setattr(model, 'CODE_SHA256', '0'*64)
        return result
    monkeypatch.setattr(model.resume.short, '_evaluate', changed_after)
    with pytest.raises(model.FundedBirthHold, match='CODE_HOLD'):
        model.apply_births(**kw)
