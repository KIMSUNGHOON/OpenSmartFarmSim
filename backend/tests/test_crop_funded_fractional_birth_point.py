from copy import deepcopy
from dataclasses import replace
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256

import pytest

from app import crop_funded_fractional_birth_point as model
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_funded_event_time import sources, ACCESS, TOLERANCE
from test_crop_leaf_funded_birth_artifact import profiles
from test_crop_leaf_funded_birth_point import setup_point


@pytest.fixture(scope='module')
def contexts(sources):
    base, sr, lr, root_lr = sources
    return {label: model.prepare_fractional_birth_context(base/label, base/'stem', ACCESS,
        leaf_root_sha256=digest, stem_root_sha256=sr, stem_start_index=0, bracket_index=0,
        time_tolerance_seconds_exact=TOLERANCE) for label, digest in [('leaf', lr), ('root-leaf', root_lr)]}


def inputs(context, count=1, mass=.25):
    data = context.value
    events = []
    for i in range(count):
        leaf = deepcopy(data['program']['leaves'][0])
        leaf.update(leaf_id='fractional-leaf-'+str(i), thermal_age={'value': 0., 'unit': 'degC_day'},
                    initial_area=model.short.old.leaf_area._area_at(Fraction(0), leaf['curve']),
                    initial_carbon={'value': mass, 'unit': model.point.MASS})
        events.append({'event_id': 'fractional-event-'+str(i), 'attachment_internode_id': 'declared-node-'+str(i),
                       'incoming_temperature': {'value': 22.+i%3, 'unit': 'degC'}, 'leaf': leaf})
    return {'schema_version': 'funded-fractional-birth-point-input-v1', 'input_id': 'fractional-test-point',
            'origin': 'synthetic', 'policy': model.point.POLICY, 'context_sha256': context.sha256,
            'candidate_sha256': model._digest(data['candidate']),
            'at_elapsed_seconds_exact': deepcopy(data['candidate']['at']['elapsed_seconds_exact']),
            'model_floor_area': deepcopy(data['program']['model_floor_area']), 'events': events}


@pytest.mark.parametrize('label', ['leaf', 'root-leaf'])
def test_actual_fractional_point_preserves_blocks_anchors_prefix_and_exact_time(contexts, monkeypatch, label):
    context = contexts[label]; before = context.value; kw = inputs(context, 2); original = deepcopy(kw)
    evaluate = model.short._evaluate; calls = []
    def counted(*a, **k):
        calls.append(1)
        return evaluate(*a, **k)
    monkeypatch.setattr(model.short, '_evaluate', counted)
    result = model.apply_fractional_births(context=context, inputs=kw)
    assert len(calls) == result['rhs_evaluations'] == 2
    a, b = result['before_sample'], result['after_sample']; y, z = a['state'], b['state']; n = len(before['program']['leaves'])
    assert a['at'] == b['at'] == before['candidate']['at']
    assert a['at']['elapsed_seconds_exact']['denominator'] != '1' and 'step_index' not in a
    assert z[1:104] == y[1:104] and z[105:107] == y[105:107]
    assert z[107:107+n] == y[107:107+n] and z[107+n:107+n+2] == [0., 0.]
    assert z[107+n+2:107+2*n+2] == y[107+n:107+2*n]
    assert z[107+2*n+4:107+3*n+4] == y[107+2*n:]
    assert z[-2:] == [.25, .25]
    assert b['curve_invariant_changes'][:n] == a['curve_invariant_changes'] and b['curve_invariant_changes'][n:] == [{'value': 0., 'unit': 'm2'}]*2
    assert result['source_candidate'] == before['candidate'] and context.value == before and kw == original
    assert result['checkpoint'] is None and result['elapsed_seconds_advanced'] == 0
    assert result['attachment_status'] == 'declared_not_bound_to_stem' and result['G0_G4'] == 'not_assessed'
    for value in result['balances'].values():
        assert abs(value['residual']['value']) <= value['budget']['value']
    with localcontext() as dc:
        dc.prec = 200; d = Decimal.from_float
        profile = context._profiles[0]
        structural = Decimal('.5'); respiration = structural*d(profile.values['cLeafG'])
        assert result['point_flows']['structural_carbon']['value'] == float(structural)
        assert result['point_flows']['growth_respiration']['value'] == float(respiration)
        assert result['point_flows']['buffer_debit']['value'] == float(structural+respiration)
        assert z[0] == float(d(y[0])-d(result['point_flows']['buffer_debit']['value']))
    result['source_candidate']['dense_candidate']['state'][0] = 0.
    assert model.apply_fractional_births(context=context, inputs=kw)['before_sample'] == a


@pytest.mark.parametrize('case', range(6))
def test_shared_jump_matches_all_original_whole_grid_material_fields(profiles, case):
    kw = setup_point(profiles, case=case, count=2)
    old = model.point.apply_births(**kw)
    p, seed, _ = model.point.resume._context(kw['context'])
    y = old['before_checkpoint']['last_confirmed']['state']
    _, first = model.short._evaluate(p, tuple(y), profiles)
    values = model._jump(p, y, first, seed['evaluation']['curve_residuals'], profiles, kw['inputs']['events'], [])
    program, after, rates, _, _, receipts, flows, balances = values
    assert program == old['after_program'] and after == old['after_sample']['state'] and list(rates) == old['after_rates']
    assert receipts == old['birth_receipts'] and flows == old['point_flows'] and balances == old['balances']


@pytest.mark.parametrize('change', [
    lambda v: v.update(schema_version='leaf-funded-birth-point-input-v1'),
    lambda v: v.update(extra=True), lambda v: v.update(candidate_sha256='0'*64),
    lambda v: v.update(context_sha256='0'*64), lambda v: v.update(origin='observed'),
    lambda v: v['at_elapsed_seconds_exact'].update(numerator='1'),
    lambda v: v['at_elapsed_seconds_exact'].update(unit='h'),
    lambda v: v['model_floor_area'].update(value=99.),
    lambda v: v.update(events=[]), lambda v: v['events'].append(deepcopy(v['events'][0])),
    lambda v: v['events'][0]['leaf']['thermal_age'].update(value=1.),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=True),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=0.),
    lambda v: v['events'][0]['leaf']['initial_carbon'].update(value=1e9),
    lambda v: v['events'][0]['leaf']['initial_area'].update(value=0.),
    lambda v: v['events'][0].pop('incoming_temperature')])
def test_closed_inputs_policy_time_hash_units_domain_and_funding_are_atomic(contexts, change):
    context = contexts['leaf']; before = context._raw; value = inputs(context); change(value)
    with pytest.raises(model.FractionalBirthHold):
        model.apply_fractional_births(context=context, inputs=value)
    assert context._raw == before


def test_previously_applied_source_event_and_leaf_ids_cannot_be_used_again(contexts):
    context = contexts['leaf']; data = context.value
    value = inputs(context); value['events'][0]['event_id'] = data['past_event_ids'][0]
    with pytest.raises(model.FractionalBirthHold, match='EVENT_HOLD'):
        model.apply_fractional_births(context=context, inputs=value)
    value = inputs(context); value['events'][0]['leaf']['leaf_id'] = data['program']['leaves'][0]['leaf_id']
    with pytest.raises(model.FractionalBirthHold, match='EVENT_HOLD'):
        model.apply_fractional_births(context=context, inputs=value)


def test_actual_fractional_time_result_512_and_output_capacity(contexts, monkeypatch):
    context = contexts['root-leaf']; value = inputs(context, 509, .001)
    result = model.apply_fractional_births(context=context, inputs=value)
    assert len(result['after_program']['leaves']) == 512 and len(result['after_sample']['state']) == 107+3*512
    assert len(model._canonical(result)) < 2*1024**2
    value['events'].append(deepcopy(value['events'][0]))
    with pytest.raises(model.FractionalBirthHold, match='CAPACITY_HOLD'):
        model.apply_fractional_births(context=context, inputs=value)
    monkeypatch.setattr(model, 'MAX_BYTES', 32)
    with pytest.raises(model.FractionalBirthHold):
        model.apply_fractional_births(context=context, inputs=inputs(context))


def test_long_identifiers_at_512_preserve_lower_component_size_holds(contexts):
    context = contexts['root-leaf']; value = inputs(context, 509, .001); before = context._raw
    for i, event in enumerate(value['events']):
        event['leaf']['leaf_id'] = 'long-leaf-identity-'+('x'*64)+'-'+str(i)
    with pytest.raises(model.FractionalBirthHold, match='CAPACITY_HOLD'):
        model.apply_fractional_births(context=context, inputs=value)
    assert context._raw == before


@pytest.mark.parametrize('kind', ['context', 'rehashed-program', 'late-code', 'late-rights', 'after-RHS'])
def test_context_and_late_source_domain_fences(contexts, monkeypatch, kind):
    context = contexts['leaf']; value = inputs(context)
    if kind == 'context':
        context = replace(context, _raw=context._raw+b' ')
    elif kind == 'rehashed-program':
        data = context.value; data['program']['model_floor_area']['value'] += 1.
        raw = model._canonical(data); context = replace(context, _raw=raw, sha256=sha256(raw).hexdigest())
        value['context_sha256'] = context.sha256
    elif kind == 'late-code':
        original = model._pins; calls = []
        def changed():
            v = original(); calls.append(1)
            if len(calls) > 1:
                v[next(iter(v))] = '0'*64
            return v
        monkeypatch.setattr(model, '_pins', changed)
    elif kind == 'after-RHS':
        original = model.short._evaluate; calls = []
        def changed(*a, **k):
            calls.append(1)
            if len(calls) == 2:
                raise ValueError('DOMAIN_HOLD: unconfirmed after state')
            return original(*a, **k)
        monkeypatch.setattr(model.short, '_evaluate', changed)
    else:
        jump = model._jump; done = []
        def counted(*a, **k):
            value = jump(*a, **k); done.append(1)
            return value
        monkeypatch.setattr(model, '_jump', counted)
        read = model.leaf.read_funded_leaf_manifest
        def changed(*a, **k):
            v = read(*a, **k)
            if done:
                v['source_rights']['display'] = False
            return v
        monkeypatch.setattr(model.leaf, 'read_funded_leaf_manifest', changed)
    with pytest.raises(model.FractionalBirthHold):
        model.apply_fractional_births(context=context, inputs=value)


def test_no_old_grid_context_application_advance_DB_CLI_network_or_writes(contexts, monkeypatch):
    import os, socket, subprocess, psycopg
    context = contexts['leaf']; value = inputs(context)
    def forbidden(*a, **k):
        raise AssertionError('no external effects or old-grid emulation')
    for owner, name in ((model.point, '_apply_current'), (model.point, 'apply_births'),
                        (model.point.resume, 'advance_chunk'), (MorphologyBlobStore, 'put'),
                        (subprocess, 'Popen'), (socket, 'socket'), (psycopg, 'connect')):
        monkeypatch.setattr(owner, name, forbidden)
    opened = os.open
    def readonly(path, flags, *a, **k):
        if flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
            return forbidden()
        return opened(path, flags, *a, **k)
    monkeypatch.setattr(os, 'open', readonly)
    assert model.apply_fractional_births(context=context, inputs=value)['checkpoint'] is None
