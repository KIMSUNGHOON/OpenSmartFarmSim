from fractions import Fraction
from hashlib import sha256
from types import MappingProxyType
from copy import deepcopy
import json

import pytest

from app import crop_organ_successor_candidate as model
from test_crop_organ_fractional_continuation import (
    short_event_context, captured, candidates, crossings, contexts, roots, stored, profiles, TOLERANCE,
)

resume = model.resume
F = Fraction.from_float
X = resume.X


@pytest.fixture(scope='module')
def pending(short_event_context):
    context = short_event_context
    result = resume.advance_chunk(context, resume.start(context), 128)
    assert result['status'] == 'hold' and result['pending_event'] is not None
    raw = resume._canonical(result['last_confirmed'])
    return context, raw, sha256(raw).hexdigest(), result['pending_event']


def calculate(pending, tolerance=TOLERANCE):
    context, raw, digest, _ = pending
    return model.calculate_successor_candidate(context, raw, expected_sha256=digest,
        time_tolerance_seconds_exact=tolerance)


def test_actual_successor_uses_own_confirmed_prefix_without_adoption(pending):
    context, raw, digest, bracket = pending
    before = resume.capture.context_bytes(context)
    result = calculate(pending)
    assert result['checkpoint_sha256'] == digest and result['source_prefix'] == json.loads(raw)
    assert result['source_interval']['source_event_id'] == bracket['source_event_id']
    assert result['source_interval']['sequence'] == json.loads(raw)['schedule']['next_sequence']
    assert result['source_interval']['threshold_exact'] == bracket['threshold_exact']
    root = result['numerical_root_interval']
    assert 0 < X(root['upper_elapsed_seconds_exact'])-X(root['lower_elapsed_seconds_exact']) <= X(TOLERANCE)
    assert result['at']['elapsed_seconds_exact'] == root['upper_elapsed_seconds_exact']
    assert result['dense_candidate']['represented_threshold_status'] == 'crossed'
    assert len(result['dense_candidate']['state']) == len(result['state_coordinates']) == len(json.loads(raw)['last_confirmed']['state'])
    assert result['rhs_evaluations'] == 37 and result['past_intervals_reintegrated'] == 0
    assert result['integrator_checkpoint'] is None and result['schedule_consumed'] is result['new_organs_created'] is False
    assert result['scope'] == 'software_research_only' and result['G0_G4'] == 'not_assessed'
    assert resume.capture.context_bytes(context) == before


def test_shared_stage_dense_state_and_flows_match_independent_fraction_arithmetic(pending):
    result = calculate(pending); rows = result['source_interval']['stages']; cp = result['source_prefix']
    interval = result['source_interval']; h = X(interval['right_elapsed_seconds_exact'])-X(interval['left_elapsed_seconds_exact'])
    z = X(result['partial_interval_seconds_exact'])/h
    weights = (z-3*z*z/2+2*z*z*z/3, z*z-2*z*z*z/3, z*z-2*z*z*z/3, -z*z/2+2*z*z*z/3)
    for i, value in enumerate(result['dense_candidate']['state']):
        expected = float(F(rows[0]['state'][i])+h*sum((w*F(row['rates'][i]) for w,row in zip(weights,rows,strict=True)), Fraction(0)))
        assert value == expected
    for index, quantity in enumerate(interval['stage_flux_order']):
        value = result['dense_candidate']['partial_interval_transfers'][quantity['name']]
        expected = float(h*sum((w*F(row['flux'][index]) for w,row in zip(weights,rows,strict=True)), Fraction(0)))
        assert value['value'] == expected
    coefficients = tuple(X(q) for q in interval['polynomial_coefficients'])
    root = result['numerical_root_interval']
    for bound, comparison in [('lower', lambda v:v < 0), ('upper', lambda v:v >= 0)]:
        theta = (X(root[bound+'_elapsed_seconds_exact'])-X(cp['at']['elapsed_seconds_exact']))/h
        value = sum((c*theta**i for i,c in enumerate(coefficients)), Fraction(0))
        assert comparison(value) and value == X(root[bound+'_threshold_residual_exact'])


def test_all_pending_prefixes_and_global_branch_books_compose_exactly(pending):
    result = calculate(pending); cp = result['source_prefix']; selected = result['at']
    assert [r['rhs_evaluations'] for r in result['refinements']] == [5,9,17]
    for packet in [result['dense_candidate'], *result['refinements']]:
        assert packet['at'] == selected
        for name, q in packet['partial_interval_transfers'].items():
            for target, field in [('lifetime','lifetime_transfers_exact'), ('source_segment','source_segment_transfers_exact')]:
                assert X(packet['pending_'+target+'_transfers_exact'][name]) == X(cp[field][name])+F(q['value'])
            assert X(packet['pending_branch_transfers_exact'][name]) == F(cp['branch_integrated_transfers'][name]['value'])+F(q['value'])
        for name, local in packet['local_ledgers'].items():
            assert abs(X(local['residual_exact'])) <= X(local['budget_exact'])
            for kind in ['branch_ledgers','global_ledgers']:
                actual, prefix = packet[kind][name], cp[kind][name]
                for field in ['residual_exact','budget_exact']:
                    assert X(actual[field]) == X(prefix[field])+X(local[field])
                assert abs(X(actual['residual_exact'])) <= X(actual['budget_exact'])


def test_current_only_37_rhs_and_no_first_event_replay_or_initialization(pending,monkeypatch):
    calls = []; evaluate = resume.stock.short._evaluate
    def counted(*args,**kw): calls.append(1); return evaluate(*args,**kw)
    def forbidden(*args,**kw): raise AssertionError('no prior steps, points, handles or initialization')
    for owner,name in [(resume,'start'),(resume,'advance_chunk'),(resume,'restore_checkpoint'),
            (resume.capture,'start'),(resume.capture,'prepare_context'),(resume.capture.point,'apply_fractional_material_point'),
            (model.candidate,'calculate_fractional_shoot_candidate'),(model.old,'_ledgers'),(model.old,'_refine'),
            (resume.stock,'prepare_context'),(resume.stock,'advance_chunk'),(resume.stock,'adopt_births'),
            (resume.stock.short.old.leaf_area,'initialize_leaf_area')]: monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(resume.stock.short,'_evaluate',counted)
    assert calculate(pending)['rhs_evaluations'] == len(calls) == 37


def test_initial_checkpoint_has_no_next_crossing_and_no_candidate(pending,monkeypatch):
    context = pending[0]; cp = resume.start(context); raw = resume.checkpoint_bytes(context,cp)
    calls = []; evaluate = resume.stock.short._evaluate
    def counted(*args,**kw): calls.append(1); return evaluate(*args,**kw)
    monkeypatch.setattr(resume.stock.short,'_evaluate',counted)
    with pytest.raises(model.SuccessorCandidateHold,match='THRESHOLD_HOLD'):
        model.calculate_successor_candidate(context,raw,expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)
    assert len(calls) == 5


@pytest.mark.parametrize('kind',['zero','negative','wide','float','bool','unit','noncanonical'])
def test_invalid_exact_tolerance_rejects_without_rhs(pending,monkeypatch,kind):
    tolerance = deepcopy(TOLERANCE)
    if kind == 'zero': tolerance['numerator'] = '0'
    elif kind == 'negative': tolerance['numerator'] = '-1'
    elif kind == 'wide': tolerance = model.Q(Fraction(9),'s')
    elif kind == 'float': tolerance = .001
    elif kind == 'bool': tolerance = True
    elif kind == 'unit': tolerance['unit'] = 'degC_day'
    else: tolerance['numerator'] = '01'
    def forbidden(*args,**kw): raise AssertionError('invalid tolerance must not calculate')
    monkeypatch.setattr(resume.stock.short,'_evaluate',forbidden)
    with pytest.raises(model.SuccessorCandidateHold): calculate(pending,tolerance)


@pytest.mark.parametrize('kind',['hash','canonical','typed','duplicate','unit','state','budget','schedule','version','cap'])
def test_raw_trust_scope_and_current_checkpoint_changes_hold(pending,monkeypatch,kind):
    context,raw,digest,bracket = pending; value = json.loads(raw)
    if kind == 'hash': digest = '0'*64
    elif kind == 'canonical': raw += b' '; digest = sha256(raw).hexdigest()
    elif kind == 'typed': raw = value
    elif kind == 'duplicate': raw = b'{"a":1,"a":2}'; digest = sha256(raw).hexdigest()
    elif kind == 'cap': monkeypatch.setattr(resume,'MAX_CHECKPOINT_BYTES',len(raw)-1)
    else:
        if kind == 'unit': value['lifetime_transfers_exact']['photosynthesis']['unit'] = 'g_DM/plant'
        elif kind == 'state': value['last_confirmed']['state'][0] += 1
        elif kind == 'budget': value['global_ledgers']['carbohydrate']['budget_exact']['numerator'] += '0'
        elif kind == 'schedule': value['schedule']['next_sequence'] += 1
        else: value['version'] = resume.stock.VERSION
        raw = resume.stock._canonical(value); digest = sha256(raw).hexdigest()
    with pytest.raises(model.SuccessorCandidateHold): calculate((context,raw,digest,bracket))


@pytest.mark.parametrize('stage',[1,2,5,6,7,12,20,37])
def test_failed_current_dense_and_refinement_rhs_cannot_publish(pending,monkeypatch,stage):
    evaluate = resume.stock.short._evaluate; calls = []
    def failed(*args,**kw):
        calls.append(1)
        if len(calls) == stage: raise ValueError('DOMAIN_HOLD: explicit successor failure')
        return evaluate(*args,**kw)
    monkeypatch.setattr(resume.stock.short,'_evaluate',failed)
    with pytest.raises(model.SuccessorCandidateHold,match='DOMAIN_HOLD'): calculate(pending)
    assert len(calls) == stage


@pytest.mark.parametrize('kind',['profile','rights','code','context','runtime'])
def test_late_changes_and_unexpected_errors_do_not_publish(pending,monkeypatch,kind):
    context = pending[0]; evaluate = resume.stock.short._evaluate; calls = []
    profile = context._source._root._profiles[0]; original = profile.values; raw = context._raw
    binding = resume.stock.leaf.binding.bind_initial_stem_carbon
    def changed_binding(*args,**kw):
        result = binding(*args,**kw)
        if kind == 'rights' and len(calls) >= 37: result['source_rights']['stem']['display'] = False
        return result
    def changed(*args,**kw):
        calls.append(1)
        if kind == 'runtime' and len(calls) == 37: raise RuntimeError('unexpected successor failure')
        result = evaluate(*args,**kw)
        if len(calls) == 37:
            if kind == 'profile':
                values = dict(original); key = next(iter(values)); values[key] += .001
                object.__setattr__(profile,'values',MappingProxyType(values))
            elif kind == 'code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif kind == 'context': object.__setattr__(context,'_raw',b'{}')
        return result
    monkeypatch.setattr(resume.stock.short,'_evaluate',changed)
    monkeypatch.setattr(resume.stock.leaf.binding,'bind_initial_stem_carbon',changed_binding)
    try:
        with pytest.raises(RuntimeError if kind == 'runtime' else model.SuccessorCandidateHold): calculate(pending)
    finally:
        object.__setattr__(profile,'values',original); object.__setattr__(context,'_raw',raw)


def test_output_cap_holds_and_success_hash_is_reproducible(pending,monkeypatch):
    result = calculate(pending)
    assert result['calculation_sha256'] == resume.stock._hash({k:v for k,v in result.items() if k != 'calculation_sha256'})
    monkeypatch.setattr(model,'MAX_BYTES',len(resume.stock._canonical(result))-1)
    with pytest.raises(model.SuccessorCandidateHold,match='CAPACITY_HOLD'): calculate(pending)


@pytest.mark.parametrize('kind',['monotonicity','rounding'])
def test_source_interval_ambiguity_is_not_hidden(pending,monkeypatch,kind):
    step = resume._step
    def changed(*args,**kw):
        result = step(*args,**kw); state,cumulative,rates,rhs,rows = result
        if kind == 'monotonicity':
            for row in rows: row['state'][104] = -100.
        else:
            index = list(resume.stock.short._flux_units(args[0])).index('indoor_air_temperature_time')
            cumulative = list(cumulative); cumulative[index] = -1e8
        return state,cumulative,rates,rhs,rows
    monkeypatch.setattr(resume,'_step',changed)
    with pytest.raises(model.SuccessorCandidateHold,match='MONOTONICITY_HOLD' if kind == 'monotonicity' else 'ROUNDING_HOLD'):
        calculate(pending)


def test_original_horizon_cannot_create_successor(captured,monkeypatch):
    context = captured[1][1]; cp = resume.advance_chunk(context,resume.start(context),128)['checkpoint']
    assert cp is not None
    raw = resume.checkpoint_bytes(context,cp)
    def forbidden(*args,**kw): raise AssertionError('completed input must not calculate')
    monkeypatch.setattr(resume.stock.short,'_evaluate',forbidden)
    with pytest.raises(model.SuccessorCandidateHold,match='COMPLETED_HOLD'):
        model.calculate_successor_candidate(context,raw,expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)


@pytest.mark.parametrize('tolerance',[Fraction(1,8),Fraction(1,2**30)])
def test_explicit_different_tolerances_remain_same_time_diagnostics(pending,tolerance):
    result = calculate(pending,model.Q(tolerance,'s')); root = result['numerical_root_interval']
    assert X(root['upper_elapsed_seconds_exact'])-X(root['lower_elapsed_seconds_exact']) <= tolerance
    assert all(row['at'] == result['at'] for row in result['refinements'])


def test_bounded_precision_and_foreign_current_context_hold(pending,captured):
    with pytest.raises(model.SuccessorCandidateHold,match='PRECISION_HOLD'):
        calculate(pending,model.Q(Fraction(1,2**200),'s'))
    context,raw,digest,bracket = pending
    with pytest.raises(model.SuccessorCandidateHold): calculate((captured[1][1],raw,digest,bracket))
