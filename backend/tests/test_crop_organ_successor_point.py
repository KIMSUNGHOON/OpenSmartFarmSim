from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from decimal import Decimal, localcontext
from types import MappingProxyType
import json

import pytest

from app import crop_organ_successor_point as model
from test_crop_organ_successor_candidate import (
    pending, short_event_context, captured, candidates, crossings, contexts, roots, stored, profiles, TOLERANCE,
)

resume = model.resume
X, F = resume.X, Fraction.from_float


@pytest.fixture(scope='module')
def row(pending):
    context,raw,digest,_ = pending
    before = model.candidate.calculate_successor_candidate(context,raw,expected_sha256=digest,
        time_tolerance_seconds_exact=TOLERANCE)
    return context,raw,digest,before


def inputs(row,with_leaf=True,stem_C=.25,leaf_C=.125,temperature=22.):
    context,raw,digest,before = row; data = context.value; p = data['captured']['program']
    event = model._source_event(data,before)
    result = {'schema_version':'individual-organ-successor-material-point-input-v1','input_id':'own-successor-material-fixture',
        'origin':'synthetic','policy':model.POLICY,'context_sha256':context.root_sha256,'checkpoint_sha256':digest,
        'candidate_sha256':before['calculation_sha256'],'initial_binding_sha256':data['source_snapshot']['manifest']['initial_binding_sha256'],
        'at_elapsed_seconds_exact':deepcopy(before['at']['elapsed_seconds_exact']),'model_floor_area':deepcopy(p['model_floor_area']),
        'source_event_id':event['source_event_id'],'source_threshold_sequence':event['sequence'],'source_threshold_exact':deepcopy(event['threshold_exact']),
        'parent_internode_id':[q['compartment_id'] for q in p['stem_root_compartments'] if q['kind']=='internode'][-1],
        'internode':{'compartment_id':event['internode_id'],'kind':'internode','initial_carbon':{'value':stem_C,'unit':model.MASS},
            'sink_weight':{'value':1.,'unit':'1'},'carbon_removal':{'value':0.,'unit':model.MASS+'/s'}},
        'leaf':None,'rights':deepcopy(data['point']['inputs']['rights']),'reviewer':'native-software-QA-not-cultivar-validation'}
    if with_leaf:
        leaf = deepcopy(p['leaves'][0]); area = model.leaf.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0),leaf['curve'])
        leaf.update(leaf_id=event['leaf_id'],thermal_age={'value':0.,'unit':'degC_day'},initial_area=area,initial_carbon={'value':leaf_C,'unit':model.MASS})
        result['leaf'] = {'declaration':leaf,'incoming_temperature':{'value':temperature,'unit':'degC'}}
    return result


def apply(row,value):
    context,raw,digest,_ = row
    return model.apply_successor_material_point(context,raw,expected_sha256=digest,
        time_tolerance_seconds_exact=TOLERANCE,inputs=value)


@pytest.mark.parametrize('with_leaf',[False,True])
def test_genuine_successor_funds_new_organs_and_preserves_existing_inventory(row,with_leaf):
    context,raw,digest,before = row; value = inputs(row,with_leaf); old = before['dense_candidate']['state']
    saved = context.value['captured']; p = saved['program']; n = len(p['leaves']); m = len(p['stem_root_compartments']); nn = n+with_leaf
    snapshot = resume.capture.context_bytes(context); out = apply(row,value); new = out['after_state']
    assert out['before_candidate']==before and out['at']==before['at'] and out['source_event']['sequence']==json.loads(raw)['schedule']['next_sequence']
    assert new[1:103]==old[1:103] and new[104:106]==old[104:106]
    assert new[106:106+n]==old[106:106+n] and new[106+nn:106+nn+n]==old[106+n:106+2*n]
    assert new[106+2*nn:106+2*nn+n]==old[106+2*n:106+3*n] and new[106+3*nn:106+3*nn+m]==old[106+3*n:]
    assert out['after_anchors'][:n]==saved['anchors'] and new[-1]==.25 and len(new)==106+3*nn+m+1
    assert out['rhs_evaluations']==38+with_leaf and out['integrator_checkpoint']is None and out['schedule_adoption']=='not_performed'
    assert out['G0_G4']=='not_assessed' and out['redistribution_authorized']is False and out['elapsed_seconds_advanced']==model.Q(Fraction(0),'s')
    if with_leaf:
        assert new[106+n]==0. and new[106+2*nn+n]==.125
        assert out['leaf_receipts'][0]['parent_internode_id']==out['source_event']['internode_id']
    else:assert new[103]==old[103] and out['after_derived']['canopy_capacity']==before['dense_candidate']['derived']['canopy_capacity']
    assert all(abs(X(q['residual_exact']))<=X(q['budget_exact']) for q in out['point_balances'].values())
    assert out['calculation_sha256']==resume.stock._hash({k:v for k,v in out.items()if k!='calculation_sha256'})
    assert resume.capture.context_bytes(context)==snapshot and resume.stock._canonical(json.loads(raw))==raw


@pytest.mark.parametrize('temperature',[10.,22.,34.])
@pytest.mark.parametrize('masses',[(.1,.2),(3.5,2.25)])
def test_decimal200_sequential_funding_original_costs_K_U_and_exact_point_residual(row,temperature,masses):
    value = inputs(row,True,*masses,temperature); out = apply(row,value); before = row[3]['dense_candidate']; after = out['after_state']
    p = row[0].value['captured']['program']; n = len(p['leaves']); profile = resume.stock.parent._profiles(row[0]._source._root)['growth_profile']
    params = json.loads(profile.raw_bytes)['parameters']
    with localcontext() as precision:
        precision.prec = 200; D = Decimal.from_float; stem_C,leaf_C = map(D,masses)
        cS,cL = (D(float(params[name]['value'])) for name in ['cStemG','cLeafG'])
        ds,dl,rs,rl = float((1+cS)*stem_C),float((1+cL)*leaf_C),float(cS*stem_C),float(cL*leaf_C)
        assert after[0] == float(D(float(D(before['state'][0])-D(ds)))-D(dl))
        for kind,expected in [('internode',(float(stem_C),rs,ds)),('leaf',(float(leaf_C),rl,dl))]:
            assert [out['flow_components'][kind][k]['value'] for k in ['structural_carbon','growth_respiration','buffer_debit']] == list(expected)
        area = out['leaf_receipts'][0]['initialization']['state']['area']['value']
        k,reference = (p['scenario']['parameters'][name]['value'] for name in ['leaf_heat_capacity','reference_temperature'])
        capacity = float(D(k)*D(area)/D(p['model_floor_area']['value'])); energy = float(D(capacity)*(D(temperature)-D(reference)))
        assert out['point_flows']['capacity_in']['value']==capacity and out['point_flows']['sensible_in']['value']==energy
        assert after[103] == float(D(before['state'][103])+D(energy))
    whole = lambda state,count:F(state[0])+sum(map(F,state[3:53]),Fraction(0))+sum(map(F,state[106+2*count:]),Fraction(0))
    residual = whole(after,n+1)-whole(before['state'],n)+F(rs)+F(rl)
    assert residual == X(out['point_balances']['whole_carbohydrate']['residual_exact'])
    assert abs(residual)<=X(out['point_balances']['whole_carbohydrate']['budget_exact'])


@pytest.mark.parametrize('with_leaf',[False,True])
def test_only_declared_new_leaf_initialized_and_actual_38_or_39_rhs(row,monkeypatch,with_leaf):
    value = inputs(row,with_leaf); calls = []; initialized = []
    evaluate = resume.stock.short._evaluate; initialize = resume.stock.short.old.leaf_area.initialize_leaf_area
    def counted(*args,**kw): calls.append(1); return evaluate(*args,**kw)
    def allowed(*,inputs):
        assert with_leaf and inputs['leaf_id']==value['leaf']['declaration']['leaf_id']; initialized.append(inputs['leaf_id'])
        return initialize(inputs=inputs)
    def forbidden(*args,**kw): raise AssertionError('no past point, old handle, CP or geometry creation')
    for owner,name in [(resume,'start'),(resume,'advance_chunk'),(resume,'restore_checkpoint'),(resume.capture,'prepare_context'),
            (model.point,'apply_fractional_material_point'),(resume.candidate,'calculate_fractional_shoot_candidate'),
            (resume.stock,'prepare_context'),(resume.stock,'adopt_births'),(resume.stock,'_seal'),
            (model.stem,'apply_internode_births'),(model.leaf,'apply_leaf_births'),
            (resume.stock.short.old.leaf_area,'normalize_leaf_area_state'),(model.source_ids,'create_rational_internodes_from_shoot_events')]:
        monkeypatch.setattr(owner,name,forbidden)
    monkeypatch.setattr(resume.stock.short,'_evaluate',counted)
    monkeypatch.setattr(resume.stock.short.old.leaf_area,'initialize_leaf_area',allowed)
    out = apply(row,value)
    assert len(calls)==out['rhs_evaluations']==38+with_leaf and len(initialized)==with_leaf


@pytest.mark.parametrize('kind',['stem','leaf','combined','lost'])
def test_insufficient_or_lost_funding_never_changes_current_prefix(row,kind):
    value = inputs(row); before = resume.capture.context_bytes(row[0]); current = row[3]['dense_candidate']['state'][0]
    if kind == 'stem': value['internode']['initial_carbon']['value'] = 1e100
    elif kind == 'leaf': value['leaf']['declaration']['initial_carbon']['value'] = 1e100
    elif kind == 'lost': value['internode']['initial_carbon']['value'] = 1e-100
    else:
        costs = json.loads(resume.stock.parent._profiles(row[0]._source._root)['growth_profile'].raw_bytes)['parameters']
        value['internode']['initial_carbon']['value'] = .75*current/(1+float(costs['cStemG']['value']))
        value['leaf']['declaration']['initial_carbon']['value'] = .75*current/(1+float(costs['cLeafG']['value']))
    with pytest.raises(model.SuccessorPointHold,match='NUMERIC_HOLD' if kind=='lost' else 'FUNDING_HOLD'): apply(row,value)
    assert resume.capture.context_bytes(row[0])==before


@pytest.mark.parametrize('kind',[
    'candidate','binding','context','checkpoint','time','consumed_event','sequence','threshold','parent_root','parent_future',
    'internode','leaf_id','leaf_age','leaf_area','mass_unit','temperature_unit','kind','rights','redistribute','origin','policy','extra','floor'])
def test_foreign_identity_units_scope_and_rights_reject(row,kind):
    value = inputs(row); data = row[0].value
    if kind in ['candidate','binding','context','checkpoint']:
        field = {'candidate':'candidate_sha256','binding':'initial_binding_sha256','context':'context_sha256','checkpoint':'checkpoint_sha256'}[kind]
        value[field] = '0'*64
    elif kind=='time': value['at_elapsed_seconds_exact']=model.Q(Fraction(1),'s')
    elif kind=='consumed_event': value['source_event_id']=data['captured']['schedule']['consumed_event_id']
    elif kind=='sequence': value['source_threshold_sequence']=True
    elif kind=='threshold': value['source_threshold_exact']=data['captured']['schedule']['consumed_threshold_exact']
    elif kind=='parent_root': value['parent_internode_id']=next(q['compartment_id'] for q in data['captured']['program']['stem_root_compartments'] if q['kind']=='root_system')
    elif kind=='parent_future': value['parent_internode_id']=value['internode']['compartment_id']
    elif kind=='internode': value['internode']['compartment_id']=value['parent_internode_id']
    elif kind=='leaf_id': value['leaf']['declaration']['leaf_id']=data['captured']['program']['leaves'][0]['leaf_id']
    elif kind=='leaf_age': value['leaf']['declaration']['thermal_age']['value']=1.
    elif kind=='leaf_area': value['leaf']['declaration']['initial_area']['value']=0.
    elif kind=='mass_unit': value['internode']['initial_carbon']['unit']='g_DM/plant'
    elif kind=='temperature_unit': value['leaf']['incoming_temperature']['unit']='K'
    elif kind=='kind': value['internode']['kind']='root_system'
    elif kind=='rights': value['rights']['display']=False
    elif kind=='redistribute': value['rights']['redistribute']=1
    elif kind=='origin': value['origin']='observed'
    elif kind=='policy': value['policy']=model.point.POLICY
    elif kind=='extra': value['extra']=True
    else: value['model_floor_area']['value']*=2
    with pytest.raises(model.SuccessorPointHold): apply(row,value)


@pytest.mark.parametrize('last_stage',[38,39])
def test_point_stage_domain_failure_cannot_publish_partial_material_result(row,monkeypatch,last_stage):
    evaluate = resume.stock.short._evaluate; calls = []; before = resume.capture.context_bytes(row[0])
    def changed(*args,**kw):
        calls.append(1)
        if len(calls)==last_stage: raise ValueError('DOMAIN_HOLD: explicit material stage failure')
        return evaluate(*args,**kw)
    monkeypatch.setattr(resume.stock.short,'_evaluate',changed)
    with pytest.raises(model.SuccessorPointHold,match='DOMAIN_HOLD'): apply(row,inputs(row))
    assert len(calls)==last_stage and resume.capture.context_bytes(row[0])==before


@pytest.mark.parametrize('kind',['profile','rights','code','ID_code','context','input','runtime'])
def test_current_and_late_fences_include_explicit_input(row,monkeypatch,kind):
    context=row[0]; value=inputs(row); evaluate=resume.stock.short._evaluate; calls=[]
    profile=context._source._root._profiles[0]; original=profile.values; raw=context._raw
    binding=resume.stock.leaf.binding.bind_initial_stem_carbon
    def changed_binding(*args,**kw):
        result=binding(*args,**kw)
        if kind=='rights' and len(calls)>=39: result['source_rights']['stem']['display']=False
        return result
    def changed(*args,**kw):
        calls.append(1)
        if kind=='runtime' and len(calls)==39: raise RuntimeError('unexpected material failure')
        result=evaluate(*args,**kw)
        if len(calls)==39:
            if kind=='profile':
                values=dict(original); key=next(iter(values)); values[key]+=.001; object.__setattr__(profile,'values',MappingProxyType(values))
            elif kind=='code': monkeypatch.setattr(model,'CODE_SHA256','0'*64)
            elif kind=='ID_code': monkeypatch.setattr(model,'ID_CODE_SHA256','0'*64)
            elif kind=='context': object.__setattr__(context,'_raw',b'{}')
            elif kind=='input': value['internode']['initial_carbon']['value']*=2
        return result
    monkeypatch.setattr(resume.stock.short,'_evaluate',changed)
    monkeypatch.setattr(resume.stock.leaf.binding,'bind_initial_stem_carbon',changed_binding)
    try:
        with pytest.raises(RuntimeError if kind=='runtime' else model.SuccessorPointHold): apply(row,value)
    finally:
        object.__setattr__(profile,'values',original); object.__setattr__(context,'_raw',raw)


def test_retry_is_identical_and_caps_never_publish_partial_state(row,monkeypatch):
    value=inputs(row); before=resume.capture.context_bytes(row[0]); first=apply(row,value); second=apply(row,value)
    assert first==second and resume.capture.context_bytes(row[0])==before
    monkeypatch.setattr(model,'MAX_BYTES',len(resume.stock._canonical(value))+1)
    with pytest.raises(model.SuccessorPointHold,match='CAPACITY_HOLD'): apply(row,value)


@pytest.mark.parametrize('kind',['next_ID','next_sequence','due_age'])
def test_source_entity_and_multiple_due_checks_do_not_snap_or_skip(row,kind):
    data=row[0].value; candidate=deepcopy(row[3])
    if kind=='next_ID': candidate['source_interval']['internode_id']='invented'
    elif kind=='next_sequence': candidate['source_interval']['sequence']+=1
    else:
        threshold=X(candidate['source_prefix']['schedule']['next_threshold_exact'])
        spacing=X(data['point']['before_candidate']['source_root_certificate']['source_timeline']['phyllochron_exact'])
        candidate['dense_candidate']['shoot_age_exact']=model.Q(threshold+spacing,'degC_day')
    with pytest.raises(model.SuccessorPointHold,match='PHASE_HOLD' if kind=='due_age' else 'EVENT_HOLD'):
        model._source_event(data,candidate)
