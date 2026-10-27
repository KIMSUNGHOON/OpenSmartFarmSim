from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from types import MappingProxyType

import pytest

from app import crop_organ_fractional_clocks as model
from test_crop_organ_fractional_continuation import captured, candidates, crossings, contexts, roots, stored, profiles, TOLERANCE

resume = model.resume
capture = resume.capture
stock = resume.stock
X = capture._fraction
F = Fraction.from_float


def derive(context, cp):
    return model.derive_current_organ_clocks(context,resume.checkpoint_bytes(context,cp),expected_sha256=cp.sha256)


@pytest.fixture(scope='module')
def checkpoints(captured):
    result = []
    for _,context in captured:
        start = resume.start(context); mid = resume.advance_chunk(context,start,2)['checkpoint']
        result.append((context,start,mid))
    return result


@pytest.mark.parametrize('case',range(4))
@pytest.mark.parametrize('cut',[1,2])
def test_actual_complete_current_ids_exact_clocks_and_leaf_residual_identity(checkpoints,case,cut):
    row = checkpoints[case]; context,cp = row[0],row[cut]; before = capture.context_bytes(context); raw = resume.checkpoint_bytes(context,cp)
    output = derive(context,cp); data = context.value['captured']; payload = cp.value; at = X(payload['at']['elapsed_seconds_exact']); air = X(payload['lifetime_transfers_exact']['indoor_air_temperature_time'])
    assert output['checkpoint_sha256'] == cp.sha256 and output['context_sha256'] == context.root_sha256
    assert output['shoot']['age_exact'] == payload['schedule']['age_exact'] and output['at'] == payload['at']
    assert [r['compartment_id']for r in output['internodes']] == [r['compartment_id']for r in data['program']['stem_root_compartments']if r['kind']=='internode']
    assert [r['leaf_id']for r in output['leaves']] == [r['leaf_id']for r in data['program']['leaves']]
    for row,base in zip(output['leaves'],data['birth_bases']['leaf'],strict=True):
        expected = X(base['thermal_age_exact'])+(air-X(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*(at-X(base['at_elapsed_seconds_exact'])))/86400
        assert X(row['age_exact']) == expected
        i = row['state_leaf_index']; residual = F(payload['last_confirmed']['state'][106+i])-expected
        assert X(row['represented_minus_clock_exact']) == residual == X(payload['global_ledgers'][f'leaf_age_{i}']['residual_exact'])
        assert abs(residual) <= X(row['age_roundoff_budget_exact'])
    assert all(row['age_exact']is None for row in output['root_systems'])
    assert capture.context_bytes(context) == before and resume.checkpoint_bytes(context,cp) == raw
    assert output['G0_G4'] == 'not_assessed' and output['redistribution_authorized']is False


def test_only_current_rhs_no_growth_point_or_initialization(checkpoints,monkeypatch):
    context,_,cp = checkpoints[1]; raw = resume.checkpoint_bytes(context,cp); calls = []; evaluate = stock.short._evaluate
    def counted(*args,**kw): calls.append(1); return evaluate(*args,**kw)
    def forbidden(*args,**kw): raise AssertionError('read clocks must not replay, grow, initialize or create a point')
    for owner,name in [(resume,'advance_chunk'),(stock,'advance_chunk'),(stock,'adopt_births'),(capture.point,'apply_fractional_material_point'),
        (capture.point.leaf,'_jump'),(capture.point.stem,'_jump'),(stock.short.old.leaf_area,'initialize_leaf_area'),(stock.short.old.leaf_area,'normalize_leaf_area_state')]:
        monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(stock.short,'_evaluate',counted)
    output = model.derive_current_organ_clocks(context,raw,expected_sha256=cp.sha256)
    assert calls == [1] and output['checkpoint_validation_RHS_evaluations'] == 1 and output['new_growth_steps'] == 0


def test_initial_node_sequence_does_not_claim_a_threshold_event(checkpoints):
    context,_,cp = checkpoints[1]; result = derive(context,cp)
    initial = [row for row in result['internodes']if row['lineage_kind']=='selected_source_initial']
    assert [row['source_node_sequence']for row in initial] == [0,1,2]
    assert all(row['source_threshold_sequence']is None and row['event_id']is None for row in initial)


def test_initial_leaf_parents_unbound_and_other_parents_use_only_actual_receipts(checkpoints):
    context,_,cp = checkpoints[1]; result = derive(context,cp); data = context.value
    root_p,_,_ = stock.parent._context(context._source._root); initial = {row['leaf_id']for row in root_p['leaves']}
    expected = {item['leaf_id']:(event['parent_internode_id'],event['event_id']) for record in context._source.point_history if record['kind']=='leaf'
        for item,event in zip(record['new_items'],record['inputs']['events'],strict=True)}
    point = data['point']; event = point['source_event']
    if point['inputs']['leaf'] is not None: expected[event['leaf_id']] = (event['internode_id'],event['leaf_event_id'])
    for row in result['leaves']:
        attachment = row['attachment']
        if row['leaf_id']in initial:
            assert attachment == {'status':'unbound_initial_leaf','parent_internode_id':None,'event_id':None}
        else:
            assert (attachment['parent_internode_id'],attachment['event_id']) == expected[row['leaf_id']]
            assert attachment['status'] == 'declared_material_parent_not_validated_anatomy'


def test_numerical_node_age_uses_actual_material_clock_without_threshold_snap(checkpoints):
    context,start,mid = checkpoints[1]; initial = derive(context,start); current = derive(context,mid)
    node0 = next(row for row in initial['internodes']if row['lineage_kind']=='numerical_threshold_material')
    node1 = next(row for row in current['internodes']if row['lineage_kind']=='numerical_threshold_material')
    assert X(node0['age_exact']) == 0
    assert X(node1['age_exact']) == X(current['shoot']['age_exact'])-X(initial['shoot']['age_exact'])
    assert node0['baseline']['at_elapsed_seconds_exact'] == context.value['point']['at']['elapsed_seconds_exact']


@pytest.mark.parametrize('kind',['negative','future','time_unit','air_unit','age_unit','temperature_unit'])
def test_signed_clock_policy_rejects_negative_future_and_wrong_units(kind):
    base = {'at_elapsed_seconds_exact':model.Q(Fraction(0),'s'),'air_temperature_integral_exact':model.Q(Fraction(0),'degC_s'),
        'thermal_age_exact':model.Q(Fraction(0),'degC_day'),'base_temperature':{'value':5.,'unit':'degC'}}
    if kind=='future': base['at_elapsed_seconds_exact'] = model.Q(Fraction(2),'s')
    if kind=='time_unit': base['at_elapsed_seconds_exact']['unit'] = 'h'
    if kind=='air_unit': base['air_temperature_integral_exact']['unit'] = 'degC_h'
    if kind=='age_unit': base['thermal_age_exact']['unit'] = 'degC_s'
    if kind=='temperature_unit': base['base_temperature']['unit'] = 'K'
    with pytest.raises(model.OrganClockHold): model._age(base,Fraction(1),Fraction(0 if kind=='negative'else 22))


@pytest.mark.parametrize('kind',['hash','canonical','duplicate','typed','state','age','unit','code','foreign','context_type','response_cap','CP_cap'])
def test_raw_scope_shape_trust_and_bounds_reject(checkpoints,monkeypatch,kind):
    context,_,cp = checkpoints[1]; raw = resume.checkpoint_bytes(context,cp); digest = cp.sha256
    if kind=='hash': digest = '0'*64
    elif kind=='canonical': raw += b' '; digest = sha256(raw).hexdigest()
    elif kind=='duplicate': raw = b'{"a":1,"a":2}'; digest = sha256(raw).hexdigest()
    elif kind=='typed': raw = cp
    elif kind in ('state','age','unit'):
        value = cp.value
        if kind=='state': value['last_confirmed']['state'][106] += 1
        elif kind=='age': value['global_ledgers']['leaf_age_0']['budget_exact']['numerator'] += '0'
        else: value['lifetime_transfers_exact']['indoor_air_temperature_time']['unit'] = 'degC_h'
        raw = stock._canonical(value); digest = sha256(raw).hexdigest()
    elif kind=='code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
    elif kind=='foreign': context = checkpoints[3][0]
    elif kind=='context_type': context = context._source
    elif kind=='response_cap': monkeypatch.setattr(model,'MAX_BYTES',100)
    else: monkeypatch.setattr(resume,'MAX_CHECKPOINT_BYTES',len(raw)-1)
    with pytest.raises(model.OrganClockHold): model.derive_current_organ_clocks(context,raw,expected_sha256=digest)


@pytest.mark.parametrize('kind',['profile','rights','code','context','runtime'])
def test_changes_at_current_rhs_prevent_clock_return(checkpoints,monkeypatch,kind):
    context,_,cp = checkpoints[1]; raw = resume.checkpoint_bytes(context,cp); original_raw = context._raw
    evaluate = stock.short._evaluate; profile = context._source._root._profiles[0]; original = profile.values; fired = []
    bind = stock.leaf.binding.bind_initial_stem_carbon
    def changed_bind(*args,**kw):
        result = bind(*args,**kw)
        if fired and kind=='rights': result['source_rights']['stem']['display'] = False
        return result
    def changed_rhs(*args,**kw):
        if kind=='runtime': raise RuntimeError('unexpected current RHS failure')
        result = evaluate(*args,**kw); fired.append(True)
        if kind=='profile':
            values = dict(original); key = next(iter(values)); values[key] += .001; object.__setattr__(profile,'values',MappingProxyType(values))
        elif kind=='code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
        elif kind=='context': object.__setattr__(context,'_raw',b'{}')
        return result
    monkeypatch.setattr(stock.short,'_evaluate',changed_rhs); monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed_bind)
    try:
        with pytest.raises(RuntimeError if kind=='runtime'else model.OrganClockHold): model.derive_current_organ_clocks(context,raw,expected_sha256=cp.sha256)
    finally: object.__setattr__(profile,'values',original); object.__setattr__(context,'_raw',original_raw)


@pytest.mark.parametrize('kind',['rights','code','context','runtime'])
def test_late_change_during_pure_age_derivation_prevents_return(checkpoints,monkeypatch,kind):
    context,_,cp = checkpoints[1]; raw = resume.checkpoint_bytes(context,cp); original_raw = context._raw
    age = model._age; calls = []; bind = stock.leaf.binding.bind_initial_stem_carbon
    def changed_bind(*args,**kw):
        result = bind(*args,**kw)
        if len(calls)>=2 and kind=='rights': result['source_rights']['stem']['display'] = False
        return result
    def changed_age(*args,**kw):
        calls.append(1); result = age(*args,**kw)
        if len(calls)==2:
            if kind=='runtime': raise RuntimeError('unexpected pure clock failure')
            if kind=='code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            if kind=='context': object.__setattr__(context,'_raw',b'{}')
        return result
    monkeypatch.setattr(model,'_age',changed_age); monkeypatch.setattr(stock.leaf.binding,'bind_initial_stem_carbon',changed_bind)
    try:
        with pytest.raises(RuntimeError if kind=='runtime'else model.OrganClockHold): model.derive_current_organ_clocks(context,raw,expected_sha256=cp.sha256)
    finally: object.__setattr__(context,'_raw',original_raw)


@pytest.mark.parametrize('kind',['leaf','internode'])
def test_actual_nonzero_source_material_birth_uses_own_baseline(crossings,stored,kind):
    from test_crop_organ_funded_continuation import prepared, next_inputs
    from test_crop_organ_fractional_point import inputs as point_inputs
    root = crossings[0][0]._root; source,kw = prepared((root,*stored[1][1:]),'leaf',0)
    before = stock.advance_chunk(source,stock.start(source),1)['checkpoint']; v = next_inputs(source,before,kind,kw,suffix='own-clock-nonzero')
    source = stock.adopt_births(context=source,raw_checkpoint=stock.checkpoint_bytes(source,before),expected_sha256=before.sha256,kind=kind,inputs=v)
    cp = stock.start(source); timeline = stock._source(source)['stem_selection']['source_state']['timeline_state']
    for _ in range(63):
        result = stock.advance_chunk(source,cp,1); right = result['checkpoint']; assert right is not None
        at = X(right.value['at_elapsed_seconds_exact']); air = F(right.value['integrated_transfers']['indoor_air_temperature_time']['value'])
        if X(timeline['age_exact'])+(air-F(float(timeline['base_temperature']['value']))*at)/86400 >= X(timeline['next_threshold_exact']): break
        cp = right
    else: pytest.fail('own source must reach the actual first event')
    raw = stock.checkpoint_bytes(source,cp); candidate = capture.candidate.calculate_fractional_shoot_candidate(source,raw,expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE)
    context = capture.prepare_context(source,raw,expected_sha256=cp.sha256,time_tolerance_seconds_exact=TOLERANCE,inputs=point_inputs((source,cp,candidate)))
    current = resume.advance_chunk(context,resume.start(context),1)['checkpoint']; output = derive(context,current)
    rows = output['leaves']if kind=='leaf'else output['internodes']; key = 'leaf_id'if kind=='leaf'else'compartment_id'
    item = next(row for row in rows if row[key]=='own-clock-nonzero-'+kind)
    assert X(item['baseline']['at_elapsed_seconds_exact']) == 8 and X(item['baseline']['air_temperature_integral_exact']) > 0
    expected = (X(output['air_temperature_integral_exact'])-X(item['baseline']['air_temperature_integral_exact'])-F(float(item['baseline']['base_temperature']['value']))*(X(output['at']['elapsed_seconds_exact'])-8))/86400
    assert X(item['age_exact']) == expected > 0
