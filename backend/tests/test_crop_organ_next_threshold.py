from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json

import pytest

from app import crop_organ_next_threshold as model
from test_crop_organ_funded_continuation import roots, prepared, next_inputs
from test_crop_stem_root_initial_binding import stored, profiles

stock = model.stock
F = Fraction.from_float
TOLERANCE = {'numerator': '1', 'denominator': '1000000', 'unit': 's'}


def q(v, unit='s'):
    return {'numerator': str(v.numerator), 'denominator': str(v.denominator), 'unit': unit}


def frac(v): return Fraction(int(v['numerator']), int(v['denominator']))


def probe(ctx, cp, tolerance=None):
    return model.probe_next_shoot_threshold(ctx, stock.checkpoint_bytes(ctx, cp), expected_sha256=cp.sha256,
        time_tolerance_seconds_exact=TOLERANCE if tolerance is None else tolerance)


@pytest.fixture(scope='module')
def contexts(roots):
    return {(case, kind): prepared(roots[case], kind, 1) for case in range(6) for kind in ('leaf', 'internode')}


@pytest.mark.parametrize('case', range(6))
@pytest.mark.parametrize('kind', ['leaf', 'internode'])
@pytest.mark.parametrize('cut', [0, 1, 2])
def test_actual_next_step_matches_every_accepted_endpoint_field_and_preserves_input(contexts, case, kind, cut):
    ctx, _ = contexts[case, kind]; cp = stock.start(ctx)
    if cut: cp = stock.advance_chunk(ctx, cp, cut)['checkpoint']
    before = stock.context_bytes(ctx); raw = stock.checkpoint_bytes(ctx, cp)
    result = probe(ctx, cp); expected = stock.advance_chunk(ctx, cp, 1)
    assert result['status'] == 'no_crossing' and result['numerical_root_interval'] is None
    target = expected['checkpoint'].value
    for name, value in result['unadopted_endpoint'].items(): assert value == target[name], name
    assert result['step_index'] == cp.value['step_index'] and result['rhs_evaluations'] == 5
    assert result['past_intervals_reintegrated'] == 0 and result['integrator_checkpoint'] is None and result['new_internodes'] == 'not_created'
    assert result['redistribution_authorized'] is False and result['G0_G4'] == 'not_assessed'
    assert result['stage_air_temperatures'] == [{'value': r['state'][104], 'unit': 'degC'} for r in result['stages']]
    assert result['stage_state_layout'] == ctx.manifest['state_layout']
    assert result['stage_flux_order'] == [{'name': name, 'unit': unit} for name,unit in stock.short._flux_units(ctx.program).items()]
    assert result['stage_sha256'] == [sha256(stock._canonical(r)).hexdigest() for r in result['stages']]
    assert result['context_sha256'] == ctx.root_sha256 and result['checkpoint_sha256'] == cp.sha256
    clock = model.clock.derive_current_shoot_clock(ctx, raw, expected_sha256=cp.sha256)
    assert result['left_shoot_age_exact'] == clock['shoot']['age_exact'] and result['initial_binding_sha256'] == clock['initial_binding_sha256']
    assert result['calculation_sha256'] == sha256(stock._canonical({k: v for k, v in result.items() if k != 'calculation_sha256'})).hexdigest()
    assert stock.context_bytes(ctx) == before and stock.checkpoint_bytes(ctx, cp) == raw


@pytest.mark.parametrize('first,second', [('leaf','internode'), ('internode','leaf'), ('internode','internode')])
@pytest.mark.parametrize('gap', [0, 1])
def test_variable_lists_and_same_time_points_use_actual_current_layout(contexts, first, second, gap):
    ctx, kw = contexts[0, first]; cp = stock.start(ctx)
    if gap: cp = stock.advance_chunk(ctx, cp, gap)['checkpoint']
    inputs = next_inputs(ctx, cp, second, kw)
    ctx2 = stock.adopt_births(context=ctx, raw_checkpoint=stock.checkpoint_bytes(ctx, cp), expected_sha256=cp.sha256, kind=second, inputs=inputs)
    result = probe(ctx2, stock.start(ctx2)); expected = stock.advance_chunk(ctx2, stock.start(ctx2), 1)['checkpoint'].value
    assert result['event_sequence'] == 2
    assert result['unadopted_endpoint']['last_confirmed'] == expected['last_confirmed']
    assert result['unadopted_endpoint']['global_balance_residuals'] == expected['global_balance_residuals']


@pytest.fixture(scope='module')
def crossings(stored, profiles):
    result = []
    for case in (1, 4):
        root = stock.parent.prepare_context(program=stored[case][0].program, step_seconds=8., step_count=64, **profiles)
        for kind in ('leaf', 'internode'):
            ctx, _ = prepared((root, *stored[case][1:]), kind, 0); cp = stock.start(ctx)
            binding = stock._source(ctx); timeline = binding['stem_selection']['source_state']['timeline_state']
            initial = frac(timeline['age_exact']); threshold = frac(timeline['next_threshold_exact']); base = F(float(timeline['base_temperature']['value']))
            for _ in range(64):
                out = stock.advance_chunk(ctx, cp, 1); assert out['checkpoint'] is not None, out.get('hold')
                right = out['checkpoint']; age = initial+(F(right.value['integrated_transfers']['indoor_air_temperature_time']['value'])-base*frac(right.value['at_elapsed_seconds_exact']))/86400
                if age >= threshold:
                    result.append((ctx, cp, right)); break
                cp = right
            else: pytest.fail('actual near-threshold source must cross within its declared horizon')
    return result


@pytest.mark.parametrize('case', range(4))
def test_actual_crossing_with_independent_decimal200_root_and_all_endpoint_ledgers(crossings, case):
    from decimal import Decimal, localcontext
    ctx, cp, right = crossings[case]; result = probe(ctx, cp)
    assert result['status'] == 'threshold_bracket'
    for name, value in result['unadopted_endpoint'].items(): assert value == right.value[name], name
    assert result['source_timeline']['at'] == '2026-10-01T07:00:00Z' and frac(result['source_threshold_exact']) == 5
    root = result['numerical_root_interval']; lo = frac(root['lower_elapsed_seconds_exact']); hi = frac(root['upper_elapsed_seconds_exact'])
    start = frac(cp.value['at_elapsed_seconds_exact']); dt = F(ctx.manifest['numerical']['step_seconds'])
    assert start <= lo < hi <= start+dt and hi-lo <= frac(TOLERANCE)
    assert frac(root['lower_thermal_residual_exact']) < 0 <= frac(root['upper_thermal_residual_exact'])
    with localcontext() as precision:
        precision.prec = 200; D = lambda x: Decimal(x.numerator)/Decimal(x.denominator)
        air = [Decimal.from_float(r['state'][104]) for r in result['stages']]
        base = Decimal.from_float(float(result['source_timeline']['base_temperature']['value'])); age = D(frac(result['left_shoot_age_exact'])); threshold = D(frac(result['source_threshold_exact']))
        def residual(t):
            z = (t-D(start))/D(dt)
            weights = [z-3*z*z/2+2*z*z*z/3,z*z-2*z*z*z/3,z*z-2*z*z*z/3,-z*z/2+2*z*z*z/3]
            return age-threshold+(D(dt)*sum(a*b for a,b in zip(air,weights,strict=True))-base*(t-D(start)))/86400
        a,b=D(start),D(start+dt)
        for _ in range(256):
            mid=(a+b)/2
            if residual(mid)<0:a=mid
            else:b=mid
        assert D(lo)<(a+b)/2<=D(hi)


def test_current_validation_is_first_stage_and_no_old_advance_or_initialization(contexts, monkeypatch):
    ctx,_=contexts[0,'internode'];cp=stock.start(ctx);raw=stock.checkpoint_bytes(ctx,cp);evaluate=stock.short._evaluate;calls=[]
    def counted(*a,**k):calls.append(1);return evaluate(*a,**k)
    monkeypatch.setattr(stock.short,'_evaluate',counted)
    def forbidden(*a,**k):raise AssertionError('no replay or adopted checkpoint allowed')
    for owner,name in [(stock,'advance_chunk'),(stock,'adopt_births'),(stock,'prepare_context'),(stock,'_seal'),
        (stock.leaf,'_jump'),(stock.stem,'_jump'),(stock.short.old.leaf_area,'initialize_leaf_area'),(stock.short.old.leaf_area,'normalize_leaf_area_state')]:
        monkeypatch.setattr(owner,name,forbidden)
    result=model.probe_next_shoot_threshold(ctx,raw,expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)
    assert len(calls)==result['rhs_evaluations']==5


@pytest.mark.parametrize('tolerance', [q(Fraction(0)),q(Fraction(1)),q(Fraction(1,2**200)),
    {'numerator':'01','denominator':'2','unit':'s'},{'numerator':'1','denominator':'100','unit':'degC_day'},
    {'numerator':'1','denominator':'0','unit':'s'},True,1e-6])
def test_invalid_or_unresolvable_tolerance_holds_without_changing_cp(contexts,crossings,tolerance):
    ctx,cp,_=crossings[0] if isinstance(tolerance,dict)and tolerance.get('denominator')==str(2**200) else (*contexts[0,'leaf'][:1],stock.start(contexts[0,'leaf'][0]),None)
    with pytest.raises(model.NextThresholdHold):probe(ctx,cp,tolerance)


def test_completed_cp_cannot_supply_another_interval(contexts):
    ctx,_=contexts[0,'internode'];cp=stock.advance_chunk(ctx,stock.start(ctx),3)['checkpoint']
    with pytest.raises(model.NextThresholdHold,match='COMPLETED_HOLD'):probe(ctx,cp)


def test_already_crossed_pending_source_schedule_is_not_silently_skipped(crossings):
    ctx,_,right=crossings[0]
    with pytest.raises(model.NextThresholdHold,match='SCHEDULE_HOLD'):probe(ctx,right)


@pytest.mark.parametrize('coefficient,right,expected',[(Fraction(-1),Fraction(-1),'no_crossing'),(Fraction(0),Fraction(0),'threshold_bracket')])
def test_endpoint_classification_and_rounding_are_explicit(coefficient,right,expected):
    assert model._crossing_status(coefficient,right)==expected


@pytest.mark.parametrize('coefficient,right',[(Fraction(-1,2**100),Fraction(0)),(Fraction(0),Fraction(-1,2**100))])
def test_rounding_disagreement_cannot_be_repaired(coefficient,right):
    with pytest.raises(model.NextThresholdHold,match='ROUNDING_HOLD'):model._crossing_status(coefficient,right)


@pytest.mark.parametrize('change',['hash','bytes','typed','context','oversize'])
def test_raw_identity_and_limits_hold(contexts,change):
    ctx,_=contexts[0,'leaf'];cp=stock.start(ctx);raw=stock.checkpoint_bytes(ctx,cp);digest=cp.sha256
    if change=='hash':digest='0'*64
    elif change=='bytes':raw+=b'\n'
    elif change=='typed':raw=cp
    elif change=='context':ctx=contexts[1,'leaf'][0]
    else:raw=b'x'*(stock.MAX_CHECKPOINT_BYTES+1);digest=sha256(raw).hexdigest()
    with pytest.raises(model.NextThresholdHold):model.probe_next_shoot_threshold(ctx,raw,expected_sha256=digest,time_tolerance_seconds_exact=TOLERANCE)


@pytest.mark.parametrize('name',['MAX_BYTES','CODE_SHA256'])
def test_response_cap_or_own_code_change_withholds_result(contexts,monkeypatch,name):
    ctx,_=contexts[0,'leaf'];cp=stock.start(ctx);monkeypatch.setattr(model,name,100 if name=='MAX_BYTES'else'0'*64)
    with pytest.raises(model.NextThresholdHold):probe(ctx,cp)


@pytest.mark.parametrize('stage', [2,3,4,5])
def test_extra_new_stage_failure_never_changes_original_cp_or_context(contexts,monkeypatch,stage):
    ctx,_=contexts[0,'leaf'];cp=stock.start(ctx);raw=stock.checkpoint_bytes(ctx,cp);before=stock.context_bytes(ctx);evaluate=stock.short._evaluate;calls=[]
    def failed(*a,**k):
        calls.append(1)
        if len(calls)==stage:raise ValueError('DOMAIN_HOLD: explicit stage failure')
        return evaluate(*a,**k)
    monkeypatch.setattr(stock.short,'_evaluate',failed)
    with pytest.raises(model.NextThresholdHold,match='DOMAIN_HOLD'):probe(ctx,cp)
    assert len(calls)==stage and stock.checkpoint_bytes(ctx,cp)==raw and stock.context_bytes(ctx)==before


def test_extra_endpoint_profile_change_prevents_result(contexts,monkeypatch):
    from types import MappingProxyType
    ctx,_=contexts[0,'internode'];cp=stock.start(ctx);profile=ctx._root._profiles[0];original=profile.values;evaluate=stock.short._evaluate;calls=[]
    def changed(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==5:
            values=dict(original);key=next(iter(values));values[key]+=.001;object.__setattr__(profile,'values',MappingProxyType(values))
        return value
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    try:
        with pytest.raises(model.NextThresholdHold,match='PROFILE_HOLD'):probe(ctx,cp)
    finally:object.__setattr__(profile,'values',original)


def test_extra_final_original_rights_change_withholds_endpoint(contexts,monkeypatch):
    ctx,_=contexts[0,'internode'];cp=stock.start(ctx);original=stock.leaf.binding.bind_initial_stem_carbon;calls=[]
    def changed(*a,**k):
        value=original(*a,**k);calls.append(1)
        if len(calls)>=3:value['source_rights']['stem']['display']=False
        return value
    monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed)
    with pytest.raises(model.NextThresholdHold,match='SOURCE_HOLD'):probe(ctx,cp)


def test_extra_final_original_store_change_is_not_accepted(contexts,monkeypatch):
    ctx,_=contexts[0,'internode'];cp=stock.start(ctx);digest=stock._source(ctx)['stem_selection']['program_sha256'];store=stock.leaf.binding.MorphologyBlobStore;get=store.get;calls=[]
    def changed(self,key,**k):
        raw=get(self,key,**k)
        if key==digest:
            calls.append(1)
            if len(calls)==5:return raw+b' '
        return raw
    monkeypatch.setattr(store,'get',changed)
    with pytest.raises(model.NextThresholdHold):probe(ctx,cp)
    assert len(calls)>=5


def test_extra_pure_method_code_identity_changed_at_endpoint_is_held(contexts,monkeypatch):
    ctx,_=contexts[0,'leaf'];cp=stock.start(ctx);evaluate=stock.short._evaluate;calls=[]
    def changed(*a,**k):
        value=evaluate(*a,**k);calls.append(1)
        if len(calls)==5:monkeypatch.setattr(model.event,'CODE_SHA256','0'*64)
        return value
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    with pytest.raises(model.NextThresholdHold):probe(ctx,cp)


@pytest.mark.parametrize('field',['air','step','budget','derived'])
def test_extra_rehashed_cp_still_requires_original_time_state_and_books(contexts,field):
    ctx,_=contexts[0,'leaf'];cp=stock.start(ctx);v=cp.value
    if field=='air':v['integrated_transfers']['indoor_air_temperature_time']['value']+=1.
    elif field=='step':v['at_elapsed_seconds_exact']['numerator']='7'
    elif field=='budget':v['global_balance_budgets']['carbohydrate']['value']*=2
    else:v['last_confirmed']['derived']['air_capacity']['value']+=1.
    raw=stock._canonical(v)
    with pytest.raises(model.NextThresholdHold):model.probe_next_shoot_threshold(ctx,raw,expected_sha256=sha256(raw).hexdigest(),time_tolerance_seconds_exact=TOLERANCE)


def test_extra_prospective_endpoint_respects_original_checkpoint_byte_cap(contexts,monkeypatch):
    ctx,_=contexts[0,'internode'];cp=stock.start(ctx);raw=stock.checkpoint_bytes(ctx,cp)
    reference=stock.advance_chunk(ctx,cp,1)['checkpoint'];assert len(stock.checkpoint_bytes(ctx,reference))>len(raw)
    monkeypatch.setattr(stock,'MAX_CHECKPOINT_BYTES',len(raw))
    with pytest.raises(model.NextThresholdHold,match='CAPACITY_HOLD'):probe(ctx,cp)


def test_extra_unexpected_runtime_error_is_not_hidden_as_a_hold(contexts,monkeypatch):
    ctx,_=contexts[0,'internode'];cp=stock.start(ctx)
    def unexpected(*a,**k):raise RuntimeError('operator interruption')
    monkeypatch.setattr(stock.short,'_evaluate',unexpected)
    with pytest.raises(RuntimeError,match='operator interruption'):probe(ctx,cp)


def test_extra_returned_stage_copy_cannot_modify_original_input_or_next_result(contexts):
    ctx,_=contexts[0,'leaf'];cp=stock.start(ctx);result=probe(ctx,cp);changed=deepcopy(result)
    changed['stages'][0]['state'][104]=99.
    changed['unadopted_endpoint']['last_confirmed']['state'][0]=0.
    assert probe(ctx,cp)==result
