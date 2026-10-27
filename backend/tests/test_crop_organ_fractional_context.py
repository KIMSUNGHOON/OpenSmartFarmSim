from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from dataclasses import replace
from types import MappingProxyType

import pytest

from app import crop_organ_fractional_context as model
from test_crop_organ_fractional_point import candidates, inputs, apply, crossings, contexts, roots, stored, profiles, TOLERANCE, frac

stock = model.stock


def test_first_schedule_consumes_one_actual_threshold_and_holds_the_next(candidates):
    source = candidates[0][2]
    result = {'before_candidate': source}
    schedule = model._schedule(result)
    assert schedule['next_sequence'] == source['source_root_certificate']['source_timeline']['next_sequence']+1
    forged = deepcopy(result)
    forged['before_candidate']['dense_candidate']['shoot_age_exact'] = deepcopy(schedule['next_threshold_exact'])
    with pytest.raises(model.FractionalContextHold, match='PHASE_HOLD'): model._schedule(forged)


def test_direct_captured_transition_uses_no_rhs_point_or_initialization(candidates, monkeypatch):
    row = candidates[0]; source = row[0]; result = apply(row, inputs(row))
    p, seed, _ = stock._context(source); binding = stock._source(source)
    def forbidden(*args, **kw): raise AssertionError('direct capture must not replay any RHS or point')
    for owner, name in [(stock.short,'_evaluate'),(model.point.stem,'_jump'),(model.point.leaf,'_jump'),
        (stock.short.old.leaf_area,'initialize_leaf_area'),(stock.short.old.leaf_area,'normalize_leaf_area_state')]:
        monkeypatch.setattr(owner,name,forbidden)
    at,dt,cp = model._direct_point(source,result,p,seed,binding)
    assert model.Q(at,'s') == result['at']['elapsed_seconds_exact'] and dt == 8
    assert cp == row[1].value
    bad = deepcopy(result); bad['after_state'][0] += 1
    bad['calculation_sha256'] = model._hash({k:v for k,v in bad.items() if k != 'calculation_sha256'})
    with pytest.raises(model.FractionalContextHold, match='direct point'): model._direct_point(source,bad,p,seed,binding)


@pytest.fixture(scope='module')
def captured(candidates):
    result = []
    for case in (0, 2):
        row = candidates[case]
        for with_leaf in (False, True):
            source, cp, _ = row
            context = model.prepare_context(source, stock.checkpoint_bytes(source, cp), expected_sha256=cp.sha256,
                time_tolerance_seconds_exact=TOLERANCE, inputs=inputs(row, with_leaf))
            result.append((row, context))
    return result


def test_current_after_state_is_captured_with_exact_global_books(captured):
    for row, context in captured:
        data = context.value; saved = data['captured']; result = data['point']
        assert saved['program'] == result['after_program']
        assert saved['at'] == row[2]['at']
        assert model.context_bytes(context) == context._raw
        for book in saved['global_ledgers'].values():
            assert abs(frac(book['residual_exact'])) <= frac(book['budget_exact'])


@pytest.mark.parametrize('case', range(4))
def test_capture_real_point_exact_time_state_bases_books_and_schedule(captured, case):
    (source, cp, candidate), context = captured[case]
    data = context.value; point = data['point']; saved = data['captured']; after = point['after_state']
    checkpoint = model.start(context).value
    assert checkpoint['version'] == model.CHECKPOINT_VERSION
    assert checkpoint['at'] == candidate['at'] == point['at']
    assert checkpoint['last_confirmed']['state'] == after
    assert saved['program'] == point['after_program'] and saved['anchors'] == point['after_anchors']
    assert saved['source_context_sha256'] == source.root_sha256
    assert saved['source_checkpoint_sha256'] == cp.sha256
    assert checkpoint['output_cursor'] == cp.value['output_cursor']+2
    assert checkpoint['event_sequence'] == cp.value['event_sequence']+1
    event = point['source_event']; schedule = saved['schedule']
    assert schedule['consumed_event_id'] == event['source_event_id']
    assert schedule['next_sequence'] == event['sequence']+1
    timeline = candidate['source_root_certificate']['source_timeline']
    assert frac(schedule['next_threshold_exact']) == frac(event['threshold_exact'])+frac(timeline['phyllochron_exact'])
    assert frac(schedule['age_exact']) < frac(schedule['next_threshold_exact'])
    assert len(saved['birth_bases']['leaf']) == len(saved['program']['leaves'])
    assert saved['birth_bases']['stem_root'][-1]['at_elapsed_seconds_exact'] == point['at']['elapsed_seconds_exact']
    assert saved['birth_bases']['stem_root'][-1]['thermal_age_exact'] == model.Q(Fraction(0), 'degC_day')
    for name, q in saved['pending_lifetime_transfers_exact'].items():
        previous = candidate['dense_candidate']['pending_lifetime_transfers_exact'].get(name, model.Q(Fraction(0), q['unit']))
        assert q == previous
    for q in checkpoint['branch_integrated_transfers_exact'].values(): assert frac(q) == 0
    for ledger in saved['global_ledgers'].values(): assert abs(frac(ledger['residual_exact'])) <= frac(ledger['budget_exact'])
    assert checkpoint['G0_G4'] == 'not_assessed' and checkpoint['redistribution_authorized'] is False


def test_restore_current_only_without_point_cost_or_past_initialization(captured, monkeypatch):
    (source, _, _), context = captured[1]
    raw = model.context_bytes(context); cp = model.start(context); cpraw = model.checkpoint_bytes(context, cp)
    calls = []; evaluate = stock.short._evaluate
    def counted(*args, **kw): calls.append(1); return evaluate(*args, **kw)
    def forbidden(*args, **kw): raise AssertionError('no past replay, point execution or initialization')
    for owner, name in [(model.point, 'apply_fractional_material_point'), (model.point.stem, '_jump'),
        (model.point.leaf, '_jump'), (stock, 'start'), (stock, 'advance_chunk'), (stock, 'adopt_births'),
        (stock.short.old.leaf_area, 'initialize_leaf_area'), (stock.short.old.leaf_area, 'normalize_leaf_area_state')]:
        monkeypatch.setattr(owner, name, forbidden)
    monkeypatch.setattr(stock.short, '_evaluate', counted)
    cd, sd, access = source._directories
    restored = model.restore_context(root_context=source._root, raw_bytes=raw, expected_sha256=sha256(raw).hexdigest(),
        crop_directory=cd, stem_directory=sd, access=access)
    assert model.context_bytes(restored) == raw and calls == []
    assert model.start(restored).sha256 == cp.sha256 and calls == []
    restored_cp = model.restore_checkpoint(restored, cpraw, expected_sha256=cp.sha256)
    assert model.checkpoint_bytes(restored, restored_cp) == cpraw and calls == [1]


def restore(context, data=None, raw=None, digest=None):
    source = context._source; cd,sd,access = source._directories
    raw = model._canonical(data) if data is not None else (model.context_bytes(context) if raw is None else raw)
    return model.restore_context(root_context=source._root,raw_bytes=raw,expected_sha256=sha256(raw).hexdigest() if digest is None else digest,
        crop_directory=cd,stem_directory=sd,access=access)


@pytest.mark.parametrize('path',[
    ('version',),('source_snapshot_sha256',),('source_code_sha256','backend/app/crop_organ_fractional_context.py'),
    ('captured','program','leaves',0,'initial_carbon','value'),('captured','anchors',0,'value'),
    ('captured','state_layout','leaf_ids',0),('captured','schedule','next_sequence'),
    ('captured','schedule','consumed_event_id'),('captured','schedule','next_threshold_exact','numerator'),
    ('captured','at','elapsed_seconds_exact','numerator'),('captured','original_grid_position','completed_grid_index'),
    ('captured','original_grid_position','remaining_to_next_grid_seconds_exact','unit'),
    ('captured','birth_bases','leaf',0,'thermal_age_exact','numerator'),
    ('captured','birth_bases','stem_root',-1,'carbon','value'),
    ('captured','birth_bases','stem_root',-1,'air_temperature_integral_exact','numerator'),
    ('captured','pending_lifetime_transfers_exact','photosynthesis','numerator'),
    ('captured','point_totals_exact','growth_respiration','numerator'),
    ('captured','global_ledgers','carbohydrate','budget_exact','numerator'),
    ('captured','redistribution_authorized',)])
def test_self_rehashed_captured_state_flow_time_basis_ledger_and_rights_reject(captured,path):
    context = captured[1][1]; data = context.value; target = data
    for key in path[:-1]: target = target[key]
    value = target[path[-1]]
    target[path[-1]] = (not value) if type(value) is bool else value+1 if type(value) in (int,float) else value+'1'
    with pytest.raises(model.FractionalContextHold): restore(context,data=data)


def rehash_point(data):
    p = data['point']; before = p['before_candidate']
    before['calculation_sha256'] = model._hash({k:v for k,v in before.items() if k != 'calculation_sha256'})
    p['before_candidate_sha256'] = p['inputs']['candidate_sha256'] = before['calculation_sha256']
    p['input_sha256'] = model._hash(p['inputs'])
    p['calculation_sha256'] = model._hash({k:v for k,v in p.items() if k != 'calculation_sha256'})


@pytest.mark.parametrize('kind',['state','flow','parent','cost','point_budget','dense_budget','source_budget','clock','scope'])
def test_rehashed_original_point_and_ledger_corruption_reject_without_replay(captured,kind):
    context = captured[1][1]; data = context.value; p = data['point']
    if kind == 'state': p['after_state'][0] += 1
    elif kind == 'flow': p['flow_components']['internode']['buffer_debit']['value'] += 1
    elif kind == 'parent': p['inputs']['parent_internode_id'] = 'placeholder'
    elif kind == 'cost': p['growth_costs']['cStemG'] += 1
    elif kind == 'point_budget': p['point_balances']['whole_carbohydrate']['budget_exact']['numerator'] += '0'
    elif kind == 'dense_budget': p['before_candidate']['dense_candidate']['global_ledgers']['carbohydrate']['budget_exact']['numerator'] += '0'
    elif kind == 'source_budget': p['before_candidate']['source_global_ledgers']['carbohydrate']['budget_exact']['numerator'] += '0'
    elif kind == 'clock': p['before_candidate']['dense_candidate']['shoot_age_exact']['numerator'] += '0'
    else: p['G0_G4'] = 'approved'
    rehash_point(data)
    with pytest.raises(model.FractionalContextHold): restore(context,data=data)


@pytest.mark.parametrize('kind',['state','time','phase','sequence','cursor','prefix','ledger','flow','units','extra','version','context','branch'])
def test_rehashed_checkpoint_changes_reject_before_current_rhs(captured,monkeypatch,kind):
    context = captured[1][1]; cp = model.start(context); data = cp.value
    if kind == 'state': data['last_confirmed']['state'][0] += 1
    elif kind == 'time': data['at']['elapsed_seconds_exact']['numerator'] += '0'
    elif kind == 'phase': data['phase'] = 'complete'
    elif kind == 'sequence': data['event_sequence'] += 1
    elif kind == 'cursor': data['output_cursor'] += 1
    elif kind == 'prefix': data['output_prefix_sha256'] = '0'*64
    elif kind == 'ledger': data['global_ledgers']['carbohydrate']['budget_exact']['numerator'] += '0'
    elif kind == 'flow': data['pending_lifetime_transfers_exact']['photosynthesis']['numerator'] += '0'
    elif kind == 'units': data['point_totals_exact']['buffer_debit']['unit'] = 'g_DM/plant'
    elif kind == 'extra': data['extra'] = True
    elif kind == 'version': data['version'] = stock.CHECKPOINT_VERSION
    elif kind == 'context': data['context_sha256'] = context._source.root_sha256
    else: data['branch_steps'] = True
    def forbidden(*args,**kw): raise AssertionError('invalid CP must reject before RHS')
    monkeypatch.setattr(stock.short,'_evaluate',forbidden)
    raw = model._canonical(data)
    with pytest.raises(model.FractionalContextHold): model.restore_checkpoint(context,raw,expected_sha256=sha256(raw).hexdigest())


def test_late_profile_change_after_pure_capture_prevents_export(captured,monkeypatch):
    context = captured[1][1]; profile = context._source._root._profiles[0]; original = profile.values; build = model._global
    def changed(*args,**kw):
        result = build(*args,**kw); values = dict(original); key = next(iter(values)); values[key] += .001
        object.__setattr__(profile,'values',MappingProxyType(values)); return result
    monkeypatch.setattr(model,'_global',changed)
    try:
        with pytest.raises(model.FractionalContextHold): model.context_bytes(context)
    finally: object.__setattr__(profile,'values',original)


def test_rights_revoked_during_prefix_construction_prevent_checkpoint(captured,monkeypatch):
    context = captured[1][1]; prefix = stock._prefix; bind = stock.leaf.binding.bind_initial_stem_carbon; revoked = []
    def changed_prefix(*args,**kw):
        result = prefix(*args,**kw); revoked.append(True); return result
    def changed_binding(*args,**kw):
        result = bind(*args,**kw)
        if revoked: result['source_rights']['stem']['display'] = False
        return result
    monkeypatch.setattr(stock,'_prefix',changed_prefix); monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed_binding)
    with pytest.raises(model.FractionalContextHold): model.start(context)


def test_late_internal_snapshot_rewrite_cannot_issue_old_identity(captured,monkeypatch):
    context = captured[1][1]; raw = context._raw; build = model._global
    def changed(*args,**kw):
        result = build(*args,**kw); object.__setattr__(context,'_raw',b'{}'); return result
    monkeypatch.setattr(model,'_global',changed)
    try:
        with pytest.raises(model.FractionalContextHold): model.context_bytes(context)
    finally: object.__setattr__(context,'_raw',raw)


@pytest.mark.parametrize('kind',['profile','rights','code','runtime'])
def test_changes_after_current_rhs_or_runtime_error_issue_no_checkpoint(captured,monkeypatch,kind):
    context = captured[1][1]; cp = model.start(context); raw = model.checkpoint_bytes(context,cp)
    evaluate = stock.short._evaluate; profile = context._source._root._profiles[0]; original = profile.values
    bind = stock.leaf.binding.bind_initial_stem_carbon; changed = []
    def new_binding(*args,**kw):
        result = bind(*args,**kw)
        if changed and kind == 'rights': result['source_rights']['stem']['display'] = False
        return result
    def new_rhs(*args,**kw):
        if kind == 'runtime': raise RuntimeError('unexpected current RHS failure')
        result = evaluate(*args,**kw); changed.append(True)
        if kind == 'code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
        if kind == 'profile':
            values = dict(original); key = next(iter(values)); values[key] += .001; object.__setattr__(profile,'values',MappingProxyType(values))
        return result
    monkeypatch.setattr(stock.short,'_evaluate',new_rhs); monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',new_binding)
    try:
        with pytest.raises(RuntimeError if kind == 'runtime' else model.FractionalContextHold): model.restore_checkpoint(context,raw,expected_sha256=cp.sha256)
    finally: object.__setattr__(profile,'values',original)


@pytest.mark.parametrize('kind',['hash','canonical','duplicate','typed','context_cap','checkpoint_cap','wrong_root','extra'])
def test_snapshot_and_checkpoint_trust_format_bounds_and_root(captured,monkeypatch,kind):
    context = captured[1][1]; raw = model.context_bytes(context)
    if kind == 'hash':
        with pytest.raises(model.FractionalContextHold): restore(context,raw=raw,digest='0'*64)
    elif kind == 'canonical':
        with pytest.raises(model.FractionalContextHold): restore(context,raw=raw+b' ')
    elif kind == 'duplicate':
        with pytest.raises(model.FractionalContextHold): restore(context,raw=b'{"version":1,"version":2}')
    elif kind == 'typed':
        with pytest.raises(model.FractionalContextHold): restore(context,raw=context,digest=sha256(raw).hexdigest())
    elif kind == 'context_cap':
        monkeypatch.setattr(model,'MAX_BYTES',len(raw)-1)
        with pytest.raises(model.FractionalContextHold): restore(context,raw=raw)
    elif kind == 'checkpoint_cap':
        monkeypatch.setattr(model,'MAX_CHECKPOINT_BYTES',100)
        with pytest.raises(model.FractionalContextHold): model.start(context)
    elif kind == 'wrong_root':
        row, other = captured[3]
        with pytest.raises(model.FractionalContextHold): restore(other,raw=raw)
    else:
        data = context.value; data['extra'] = True
        with pytest.raises(model.FractionalContextHold): restore(context,data=data)


def test_corrupted_current_rates_require_actual_current_rhs_not_past_replay(captured):
    context = captured[1][1]; data = context.value; data['point']['after_rates'][0] += 1; rehash_point(data)
    restored = restore(context,data=data); cp = model.start(restored); raw = model.checkpoint_bytes(restored,cp)
    with pytest.raises(model.FractionalContextHold,match='current RHS'): model.restore_checkpoint(restored,raw,expected_sha256=cp.sha256)


def test_checkpoint_handle_rewrite_does_not_export_rehashed_changed_state(captured):
    context = captured[1][1]; cp = model.start(context); value = cp.value; value['last_confirmed']['state'][0] += 1; raw = model._canonical(value)
    fake = replace(cp,_raw=raw,sha256=sha256(raw).hexdigest())
    with pytest.raises(model.FractionalContextHold): model.checkpoint_bytes(context,fake)


def test_repeated_start_and_restore_leave_original_source_point_and_cost_unchanged(captured):
    row,context = captured[1]; original = model.context_bytes(context); cp = model.start(context); raw = model.checkpoint_bytes(context,cp)
    source_raw = stock.context_bytes(row[0]); source_cp = stock.checkpoint_bytes(row[0],row[1])
    for _ in range(2):
        restored = restore(context); new = model.restore_checkpoint(restored,raw,expected_sha256=cp.sha256)
        assert new.sha256 == cp.sha256 and model.context_bytes(restored) == original
    assert stock.context_bytes(row[0]) == source_raw and stock.checkpoint_bytes(row[0],row[1]) == source_cp


@pytest.mark.parametrize('kind',['point_code','candidate_code','certificate_code','polynomial'])
def test_rehashed_reported_code_and_cubic_certificate_must_match_actual_sources(captured,kind):
    context = captured[1][1]; data = context.value; point = data['point']; before = point['before_candidate']; cert = before['source_root_certificate']
    if kind == 'point_code': point['code_sha256'] = '0'*64
    elif kind == 'candidate_code': before['code_sha256'] = '0'*64
    elif kind == 'certificate_code': cert['code_sha256'] = '0'*64
    else: cert['polynomial_coefficients'][0]['numerator'] += '0'
    cert['calculation_sha256'] = model._hash({k:v for k,v in cert.items() if k != 'calculation_sha256'})
    rehash_point(data)
    with pytest.raises(model.FractionalContextHold): restore(context,data=data)


@pytest.mark.parametrize('kind',['leaf','internode'])
def test_existing_organ_born_after_start_keeps_its_own_exact_air_and_carbon_basis(crossings,stored,kind):
    from test_crop_organ_funded_continuation import prepared, next_inputs
    root = crossings[0][0]._root
    source,kw = prepared((root,*stored[1][1:]),'leaf',0)
    oldcp = stock.advance_chunk(source,stock.start(source),1)['checkpoint']
    v = next_inputs(source,oldcp,kind,kw,suffix='nonzero-birth')
    source = stock.adopt_births(context=source,raw_checkpoint=stock.checkpoint_bytes(source,oldcp),expected_sha256=oldcp.sha256,kind=kind,inputs=v)
    cp = stock.start(source); timeline = stock._source(source)['stem_selection']['source_state']['timeline_state']
    threshold = frac(timeline['next_threshold_exact']); base = Fraction.from_float(float(timeline['base_temperature']['value']))
    for _ in range(63):
        right = stock.advance_chunk(source,cp,1)['checkpoint']; assert right is not None
        age = frac(timeline['age_exact'])+(Fraction.from_float(right.value['integrated_transfers']['indoor_air_temperature_time']['value'])-base*frac(right.value['at_elapsed_seconds_exact']))/86400
        if age >= threshold: break
        cp = right
    else: pytest.fail('declared source must have an actual next crossing')
    before = model.candidate.calculate_fractional_shoot_candidate(source,stock.checkpoint_bytes(source,cp),expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)
    row = (source,cp,before); result = model.prepare_context(source,stock.checkpoint_bytes(source,cp),expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE,inputs=inputs(row))
    bases = result.value['captured']['birth_bases']['leaf' if kind == 'leaf' else 'stem_root']; idkey = 'leaf_id' if kind == 'leaf' else 'compartment_id'
    birth = next(row for row in bases if row[idkey] == 'nonzero-birth-'+kind)
    assert frac(birth['at_elapsed_seconds_exact']) == 8 and frac(birth['thermal_age_exact']) == 0
    assert frac(birth['air_temperature_integral_exact']) == Fraction.from_float(source.point_history[-1]['air_temperature_integral']) > 0
    cp = model.start(result); restored = restore(result); assert model.restore_checkpoint(restored,model.checkpoint_bytes(result,cp),expected_sha256=cp.sha256).sha256 == cp.sha256
