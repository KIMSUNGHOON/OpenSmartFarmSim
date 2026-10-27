from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from dataclasses import replace
from types import MappingProxyType
from math import nextafter, inf
import json

import pytest

from app import crop_organ_fractional_continuation as model
from test_crop_organ_fractional_context import captured, candidates, crossings, contexts, roots, stored, profiles, TOLERANCE

capture = model.capture
stock = capture.stock
F = Fraction.from_float
X = capture._fraction


def test_initial_own_checkpoint_keeps_actual_capture_prefix_state_and_zero_branch(captured):
    for _,context in captured:
        original = capture.start(context); cp = model.start(context)
        assert cp.value['version'] == model.CHECKPOINT_VERSION
        assert cp.value['source_initial_checkpoint_sha256'] == original.sha256
        for name in ['last_confirmed','at','event_sequence','point_totals_exact','output_cursor','output_prefix_sha256','global_ledgers']:
            assert cp.value[name] == original.value[name]
        assert all(X(row['budget_exact']) == 0 for row in cp.value['branch_ledgers'].values())


@pytest.mark.parametrize('case',range(4))
def test_real_first_remainder_targets_original_grid_and_preserves_capture(captured,case):
    _,context = captured[case]; raw = capture.context_bytes(context); original = capture.start(context)
    start = model.start(context); first = model.advance_chunk(context,start,1)
    assert first['status'] == 'yielded' and first['checkpoint'] is not None
    cp = first['checkpoint'].value; data = context.value['captured']; dt = F(data['original_numerical']['step_seconds'])
    assert cp['at']['elapsed_seconds_exact'] == data['original_grid_position']['next_grid_elapsed_seconds_exact']
    assert first['intervals'][0]['step_seconds_exact'] == data['original_grid_position']['remaining_to_next_grid_seconds_exact']
    assert cp['grid_index'] == data['original_grid_position']['completed_grid_index']+1 and cp['branch_steps'] == 1
    assert cp['output_cursor'] == original.value['output_cursor']+1 and len(first['samples']) == 1
    assert first['checkpoint_validation_RHS_evaluations'] == 1 and first['new_RHS_evaluations'] == 4
    assert X(cp['at']['elapsed_seconds_exact']) == cp['grid_index']*dt
    assert cp['point_totals_exact'] == original.value['point_totals_exact']
    assert cp['schedule']['consumed_event_id'] == data['schedule']['consumed_event_id']
    assert capture.context_bytes(context) == raw and capture.start(context).sha256 == original.sha256
    for row in cp['global_ledgers'].values(): assert abs(X(row['residual_exact'])) <= X(row['budget_exact'])


def test_start_and_restore_keep_same_capture_without_initialization(captured,monkeypatch):
    context = captured[1][1]; original = capture.start(context); calls = []; evaluate = stock.short._evaluate
    def counted(*args,**kw): calls.append(1); return evaluate(*args,**kw)
    def forbidden(*args,**kw): raise AssertionError('no old integration, point or initialization')
    for owner,name in [(capture.point,'apply_fractional_material_point'),(capture.point.stem,'_jump'),(capture.point.leaf,'_jump'),
        (stock,'start'),(stock,'advance_chunk'),(stock,'adopt_births'),(stock.short.old.leaf_area,'initialize_leaf_area'),
        (stock.short.old.leaf_area,'normalize_leaf_area_state')]:monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(stock.short,'_evaluate',counted)
    cp = model.start(context); raw = model.checkpoint_bytes(context,cp)
    assert cp.value['source_initial_checkpoint_sha256'] == original.sha256 and calls == []
    restored = model.restore_checkpoint(context,raw,expected_sha256=cp.sha256)
    assert model.checkpoint_bytes(context,restored) == raw and calls == [1]


def compositions(total):
    for mask in range(1 << (total-1)):
        parts = []; last = 0
        for cut in range(1,total):
            if mask & (1 << (cut-1)): parts.append(cut-last); last = cut
        yield [*parts,total-last]


@pytest.mark.parametrize('case',range(4))
def test_all_four_endpoint_partitions_have_identical_states_flows_books_and_bytes(captured,case):
    context = captured[case][1]; expected = model.advance_chunk(context,model.start(context),4)
    final = model.checkpoint_bytes(context,expected['checkpoint'])
    for parts in compositions(4):
        cp = model.start(context); samples = []; intervals = []
        for count in parts:
            result = model.advance_chunk(context,cp,count); assert result['checkpoint'] is not None, result['hold']
            cp = result['checkpoint']; samples.extend(result['samples']); intervals.extend(result['intervals'])
        assert model.checkpoint_bytes(context,cp) == final
        assert samples == expected['samples'] and intervals == expected['intervals']


@pytest.mark.parametrize('case',range(4))
def test_real_remainder_shared_rk4_states_and_flows_match_independent_fraction_arithmetic(captured,monkeypatch,case):
    context = captured[case][1]; traces = []; step = model._step
    def measured(*args,**kw):
        result = step(*args,**kw); traces.append((args,result)); return result
    monkeypatch.setattr(model,'_step',measured)
    result = model.advance_chunk(context,model.start(context),1); assert result['checkpoint'] is not None
    args,output = traces[0]; initial,totals,h,rows = args[1],args[2],args[6],output[4]
    for index,factor,previous in [(1,Fraction(1,2),0),(2,Fraction(1,2),1),(3,Fraction(1),2)]:
        assert rows[index]['state'] == [float(F(y)+h*factor*F(k)) for y,k in zip(initial,rows[previous]['rates'],strict=True)]
    weights = (1,2,2,1)
    for before,after,key in [(initial,output[0],'rates'),(totals,output[1],'flux')]:
        expected = [float(F(value)+h*sum((weight*F(row[key][i]) for weight,row in zip(weights,rows,strict=True)),Fraction(0))/6)
            for i,value in enumerate(before)]
        assert list(after) == expected


@pytest.fixture(scope='module')
def advanced(captured):
    return [(context,model.advance_chunk(context,model.start(context),3)['checkpoint']) for _,context in captured]


@pytest.mark.parametrize('kind',['state','flow','age','time','grid','steps','cursor','prefix','link','scope','code','point','budget','extra','unit','source'])
def test_self_rehashed_advanced_checkpoint_changes_reject(advanced,kind):
    context,cp = advanced[1]; value = cp.value
    if kind == 'state': value['last_confirmed']['state'][0] += 1
    elif kind == 'flow': value['branch_integrated_transfers']['photosynthesis']['value'] += 1
    elif kind == 'age': value['schedule']['age_exact']['numerator'] += '0'
    elif kind == 'time': value['at']['elapsed_seconds_exact']['numerator'] += '0'
    elif kind == 'grid': value['grid_index'] += 1
    elif kind == 'steps': value['branch_steps'] = True
    elif kind == 'cursor': value['output_cursor'] += 1
    elif kind == 'prefix': value['output_prefix_sha256'] = '0'*64
    elif kind == 'link': value['output_prefix_link']['previous_output_prefix_sha256'] = '0'*64
    elif kind == 'scope': value['G0_G4'] = 'approved'
    elif kind == 'code': value['source_code_sha256']['backend/app/crop_organ_fractional_continuation.py'] = '0'*64
    elif kind == 'point': value['point_totals_exact']['buffer_debit']['numerator'] += '0'
    elif kind == 'budget': value['global_ledgers']['carbohydrate']['budget_exact']['numerator'] += '0'
    elif kind == 'extra': value['extra'] = True
    elif kind == 'unit': value['branch_integrated_transfers']['photosynthesis']['unit'] = 'g_DM/plant'
    else: value['source_initial_checkpoint_sha256'] = '0'*64
    raw = model._canonical(value)
    with pytest.raises(model.FractionalContinuationHold): model.restore_checkpoint(context,raw,expected_sha256=sha256(raw).hexdigest())


@pytest.mark.parametrize('budget',[False,0,-1,129,1.5,'1',None])
def test_invalid_endpoint_budget_rejects_before_rhs(captured,monkeypatch,budget):
    context = captured[1][1]; cp = model.start(context)
    def forbidden(*args,**kw): raise AssertionError('invalid budget must not calculate')
    monkeypatch.setattr(stock.short,'_evaluate',forbidden)
    with pytest.raises(model.FractionalContinuationHold,match='BUDGET_HOLD'): model.advance_chunk(context,cp,budget)


@pytest.mark.parametrize('stage',range(1,5))
def test_failed_second_interval_keeps_only_first_confirmed_prefix(captured,monkeypatch,stage):
    context = captured[1][1]; cp = model.start(context); first = model.advance_chunk(context,cp,1)
    evaluate = stock.short._evaluate; calls = []
    def changed(*args,**kw):
        calls.append(1)
        if len(calls) == 5+stage: raise ValueError('DOMAIN_HOLD: explicit unconfirmed stage')
        return evaluate(*args,**kw)
    monkeypatch.setattr(stock.short,'_evaluate',changed)
    result = model.advance_chunk(context,cp,3)
    assert result['status'] == 'hold' and result['checkpoint'] is None and result['last_confirmed'] == first['checkpoint'].value
    assert result['samples'] == first['samples'] and result['new_RHS_evaluations'] == 4+stage
    assert result['hold']['stage'] == ['k2','k3','k4','endpoint'][stage-1]


@pytest.mark.parametrize('kind',['profile','rights','code','context','runtime'])
def test_late_mutation_or_unexpected_failure_cannot_publish_endpoint(captured,monkeypatch,kind):
    context = captured[1][1]; cp = model.start(context); raw = capture.context_bytes(context)
    evaluate = stock.short._evaluate; profile = context._source._root._profiles[0]; original = profile.values; calls = []
    bind = stock.leaf.binding.bind_initial_stem_carbon
    def changed_bind(*args,**kw):
        result = bind(*args,**kw)
        if len(calls) >= 5 and kind == 'rights': result['source_rights']['stem']['display'] = False
        return result
    def changed(*args,**kw):
        calls.append(1)
        if len(calls) == 5 and kind == 'runtime': raise RuntimeError('unexpected stage failure')
        result = evaluate(*args,**kw)
        if len(calls) == 5:
            if kind == 'profile':
                values = dict(original); key = next(iter(values)); values[key] += .001; object.__setattr__(profile,'values',MappingProxyType(values))
            elif kind == 'code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif kind == 'context': object.__setattr__(context,'_raw',b'{}')
        return result
    monkeypatch.setattr(stock.short,'_evaluate',changed); monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed_bind)
    try:
        with pytest.raises(RuntimeError if kind == 'runtime' else model.FractionalContinuationHold): model.advance_chunk(context,cp,1)
    finally:
        object.__setattr__(profile,'values',original); object.__setattr__(context,'_raw',raw)


def test_completed_horizon_mid_and_final_restore_and_no_further_advance(captured):
    context = captured[1][1]; original = model.start(context); mid = model.advance_chunk(context,original,3)['checkpoint']
    restored = model.restore_checkpoint(context,model.checkpoint_bytes(context,mid),expected_sha256=mid.sha256)
    split = model.advance_chunk(context,restored,128); whole = model.advance_chunk(context,original,128)
    assert split['status'] == whole['status'] == 'completed'
    assert model.checkpoint_bytes(context,split['checkpoint']) == model.checkpoint_bytes(context,whole['checkpoint'])
    final = model.restore_checkpoint(context,model.checkpoint_bytes(context,whole['checkpoint']),expected_sha256=whole['checkpoint'].sha256)
    with pytest.raises(model.FractionalContinuationHold,match='COMPLETED_HOLD'): model.advance_chunk(context,final,1)


@pytest.mark.parametrize('kind',['hash','canonical','duplicate','typed','foreign','CP_cap','response_cap','handle'])
def test_raw_trust_format_scope_and_limits(advanced,monkeypatch,kind):
    context,cp = advanced[1]; raw = model.checkpoint_bytes(context,cp); digest = cp.sha256
    if kind == 'hash': digest = '0'*64
    elif kind == 'canonical': raw += b' '; digest = sha256(raw).hexdigest()
    elif kind == 'duplicate': raw = b'{"a":1,"a":2}'; digest = sha256(raw).hexdigest()
    elif kind == 'typed': raw = cp
    elif kind == 'foreign': context = advanced[3][0]
    elif kind == 'CP_cap': monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',len(raw)-1)
    elif kind == 'response_cap':
        one = model.advance_chunk(context,cp,1); view = {**one,'checkpoint':one['checkpoint'].value}
        limit = len(stock._canonical(view))+100; monkeypatch.setattr(model,'MAX_BYTES',limit)
        result = model.advance_chunk(context,cp,3)
        assert result['status'] == 'hold' and result['checkpoint'] is None and result['samples'] == one['samples']
        assert result['last_confirmed'] == one['last_confirmed']; return
    else:
        value = cp.value; value['last_confirmed']['state'][0] += 1; raw = model._canonical(value)
        bad = replace(cp,_raw=raw,sha256=sha256(raw).hexdigest())
        with pytest.raises(model.FractionalContinuationHold): model.checkpoint_bytes(context,bad)
        return
    with pytest.raises(model.FractionalContinuationHold): model.restore_checkpoint(context,raw,expected_sha256=digest)


def build_short_event_context(directory, root, crop_directory, crop_root_sha256, profiles):
    from test_crop_stem_root_initial_binding import ROOT, ACCESS, encoded, produce_rational_morphology_artifact
    from test_crop_organ_funded_continuation import prepared
    from test_crop_organ_fractional_point import inputs as point_inputs
    program = json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_text())
    program['program_id'] = 'own-short-phyllochron-policy-fixture-not-cultivar'
    program['output_times'] = ['2026-10-01T07:00:00Z']; program['segments'][0]['end_utc'] = program['output_times'][0]
    program['initial_state']['timeline_state']['phyllochron_exact'] = {'numerator':'1','denominator':'100','unit':'degC_day'}
    program['initial_state']['timeline_state']['schedule_id'] = 'own-short-next-event-policy-fixture'
    stem_directory = directory/'stem'; stem_root = produce_rational_morphology_artifact(stem_directory,ACCESS,program_raw=encoded(program))
    source,_ = prepared((root,crop_directory,stem_directory,crop_root_sha256,stem_root,0),'leaf',0)
    cp = stock.start(source); timeline = stock._source(source)['stem_selection']['source_state']['timeline_state']
    for _ in range(64):
        result = stock.advance_chunk(source,cp,1); right = result['checkpoint']; assert right is not None, result.get('hold')
        at = X(right.value['at_elapsed_seconds_exact']); air = F(right.value['integrated_transfers']['indoor_air_temperature_time']['value'])
        age = X(timeline['age_exact'])+(air-F(float(timeline['base_temperature']['value']))*at)/86400
        if age >= X(timeline['next_threshold_exact']): break
        cp = right
    else: raise AssertionError('actual first event must be reached in the explicit short fixture')
    before = model.candidate.calculate_fractional_shoot_candidate(source,stock.checkpoint_bytes(source,cp),expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)
    context = capture.prepare_context(source,stock.checkpoint_bytes(source,cp),expected_sha256=cp.sha256,
        time_tolerance_seconds_exact=TOLERANCE,inputs=point_inputs((source,cp,before)))
    return context


@pytest.fixture(scope='module')
def short_event_context(tmp_path_factory,stored,profiles):
    root = stock.parent.prepare_context(program=stored[1][0].program,step_seconds=8.,step_count=64,**profiles)
    return build_short_event_context(tmp_path_factory.mktemp('own-short-next-event'),root,stored[1][1],stored[1][3],profiles)


def test_actual_next_event_holds_after_confirmed_prefix_without_consuming_or_creating(short_event_context):
    context = short_event_context; raw = capture.context_bytes(context); cp = model.start(context)
    result = model.advance_chunk(context,cp,128)
    assert result['status'] == 'hold' and result['checkpoint'] is None and result['hold']['reason'].startswith('NEXT_EVENT_HOLD')
    assert result['samples'] and result['last_confirmed']['branch_steps'] == len(result['samples'])
    pending = result['pending_event']; assert pending['sequence'] == context.value['captured']['schedule']['next_sequence']
    assert pending['threshold_exact'] == context.value['captured']['schedule']['next_threshold_exact']
    assert pending['schedule_consumed'] is pending['new_organs_created'] is pending['checkpoint_issued'] is False
    assert X(pending['left_age_exact']) < X(pending['threshold_exact']) <= X(pending['represented_right_age_exact'])
    last = model._canonical(result['last_confirmed']); restored = model.restore_checkpoint(context,last,expected_sha256=sha256(last).hexdigest())
    retried = model.advance_chunk(context,restored,1)
    assert retried['pending_event'] == pending and retried['last_confirmed'] == result['last_confirmed'] and retried['samples'] == []
    assert capture.context_bytes(context) == raw


@pytest.mark.parametrize('kind',['monotonicity','rounding'])
def test_pending_event_policy_does_not_hide_nonmonotone_or_rounding_ambiguity(captured,monkeypatch,kind):
    context = captured[1][1]; step = model._step; traces = []
    def measured(*args,**kw):
        result = step(*args,**kw); traces.append(result); return result
    monkeypatch.setattr(model,'_step',measured); start = model.start(context); result = model.advance_chunk(context,start,1)
    data = context.value; rows = deepcopy(traces[0][4]); cumulative = list(traces[0][1]); target = X(result['last_confirmed']['at']['elapsed_seconds_exact'])
    timeline = data['point']['before_candidate']['source_root_certificate']['source_timeline']; base = F(float(timeline['base_temperature']['value']))
    if kind == 'monotonicity':
        for row in rows: row['state'][104] = float(base-1)
    else:
        at = X(start.value['at']['elapsed_seconds_exact']); h = target-at
        ideal = X(start.value['schedule']['age_exact'])+(h*sum((w*F(row['state'][104]) for w,row in zip((1,2,2,1),rows,strict=True)),Fraction(0))/6-base*h)/86400
        units = list(stock.short._flux_units(data['captured']['program'])); index = units.index('indoor_air_temperature_time')
        cumulative[index] = nextafter(cumulative[index],inf)
        represented = X(timeline['age_exact'])+(X(data['captured']['pending_lifetime_transfers_exact']['indoor_air_temperature_time'])+F(cumulative[index])-base*target)/86400
        assert ideal != represented
        data['captured']['schedule']['next_threshold_exact'] = model.Q((ideal+represented)/2,'degC_day')
    with pytest.raises(model.FractionalContinuationHold,match='MONOTONICITY_HOLD' if kind == 'monotonicity' else 'ROUNDING_HOLD'):
        model._pending_event(data,start.value,rows,cumulative,target)
