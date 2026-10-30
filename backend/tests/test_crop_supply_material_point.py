"""Explicit, source-bound new-organ funding on the current forcing candidate."""
from copy import deepcopy
from datetime import datetime,timezone
from decimal import Decimal,localcontext
from fractions import Fraction
from hashlib import sha256
from math import ulp
import json

import pytest

from app import crop_supply_material_point as model
from app import crop_supply_forcing_threshold_state as state
from app import crop_supply_forcing_owner as owner
from app import crop_supply_season as base
from app.crop_morphology_artifact_io import MorphologyBlobStore
from test_crop_supply_season import source,q,x,canonical
from test_crop_supply_forcing_owner import origin,setup_owner
from test_crop_supply_forcing_threshold import pending,stored_page,TOLERANCE
from test_crop_supply_forcing_threshold_state import calculated


def refresh(value):
    parameters={k:value[k]for k in ['parameter_source','parameter_revision','model_floor_area','internode','leaf']}
    units={}
    def visit(v,path):
        if type(v)is dict:
            if set(v)=={'value','unit'}:units[path]=v['unit']
            else:
                for key,item in v.items():visit(item,path+'.'+key if path else key)
    visit(parameters,'')
    value['parameter_provenance']['raw_sha256']=sha256(canonical(parameters)).hexdigest()
    value['parameter_provenance']['units']=units
    return value


def make_inputs(pending,calculated,*,leaf=True,length=0.):
    info=model.describe_material_source(pending['result'].handle)
    assert info['status']=='source_described',info.get('hold')
    with owner._session(pending['definition'],pending['workspace'])as s:p=deepcopy(s.math_basis['seed']['program'])
    event=info['event'];now=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    value={'schema_version':'supply-season-material-point-input-v1','input_id':'own-current-point-QA','origin':'synthetic','policy':model.POLICY,
        'parameter_source':'own_declared_synthetic_assumptions','parameter_revision':'QA-v1','reviewer':'native-software-QA-not-cultivar',
        'definition_sha256':pending['definition'],'cursor_sha256':pending['result'].handle.cursor_sha256,
        'pending_page_sha256':pending['result'].pending['page_sha256'],'candidate_sha256':calculated['calculation_sha256'],
        'initial_binding_sha256':info['initial_binding_sha256'],'at_elapsed_seconds_exact':deepcopy(calculated['at']['elapsed_seconds_exact']),
        'source_event_id':event['source_event_id'],'source_threshold_sequence':event['sequence'],'source_threshold_exact':deepcopy(event['threshold_exact']),
        'parent_internode_id':info['parent_internode_ids'][-1],'model_floor_area':deepcopy(p['model_floor_area']),
        'internode':{'declaration':{'compartment_id':event['internode_id'],'kind':'internode',
            'initial_carbon':{'value':.25,'unit':model.material.MASS},'sink_weight':{'value':1.,'unit':'1'},
            'carbon_removal':{'value':0.,'unit':model.material.MASS+'/s'}},
            'initial_length':{'value':length,'unit':'m'},'construction_cost':{'value':1e-6,'unit':'mg_CH2O/m_internode'}},
        'leaf':None,'rights':{'use':True,'display':True,'redistribute':True},
        'parameter_provenance':{'product_id':'own-current-point-QA','source_url':'urn:opensmartfarmsim:self-authored-software-fixture',
            'observed_at':None,'published_at':None,'available_at':now,'retrieved_at':now,'vintage':'own','revision':'QA-v1','qc':'software_fixture_only',
            'units':{},'raw_sha256':'0'*64,'reviewer':'native-software-QA-not-cultivar'}}
    if leaf:
        declaration=deepcopy(p['leaves'][0]);declaration.update(leaf_id=event['leaf_id'],thermal_age={'value':0.,'unit':'degC_day'},
            initial_carbon={'value':.125,'unit':model.material.MASS},sink_weight={'value':1.,'unit':'1'},carbon_removal={'value':0.,'unit':model.material.MASS+'/s'})
        declaration['initial_area']=model.material.arithmetic.resume.short.old.leaf_area._area_at(Fraction(0),declaration['curve'])
        value['leaf']={'declaration':declaration,'incoming_temperature':{'value':22.,'unit':'degC'},'construction_cost':{'value':1e-6,'unit':'mg_CH2O/m2_leaf'}}
    return refresh(value)


@pytest.fixture(scope='module')
def point_case(pending,calculated):
    inputs=make_inputs(pending,calculated)
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='point_ready',result.get('hold')
    return inputs,result


def test_source_descriptor_uses_original_binding_and_no_RHS_or_writes(pending,monkeypatch):
    monkeypatch.setattr(base.stage,'evaluate',lambda *a,**k:pytest.fail('descriptor ran RHS'))
    monkeypatch.setattr(MorphologyBlobStore,'put',lambda *a,**k:pytest.fail('descriptor wrote CAS'))
    result=model.describe_material_source(pending['result'].handle)
    assert result['status']=='source_described',result.get('hold')
    n=pending['result'].handle.current['numeric']
    assert result['event']['sequence']==n['schedule']['next_sequence']
    assert result['event']['threshold_exact']==n['schedule']['next_threshold_exact']
    assert result['effective_rights']['redistribute']is False
    assert result['schedule_consumed']is False


def test_actual_point_funds_new_organs_once_and_preserves_every_old_coordinate(pending,calculated,point_case):
    inputs,out=point_case;before=calculated['dense_candidate'];n0=calculated['source_current']['numeric']
    with owner._session(pending['definition'],pending['workspace'])as s:p=s.math_basis['seed']['program'];organs=s.math_basis['seed']['organs']
    n=len(p['leaves']);m=len(p['stem_root_compartments']);h=len(organs['internodes']);size=106+3*n+m
    nn=n+1;newsize=106+3*nn+m+1;z=out['after_state'];y=before['state']
    assert len(y)==176 and len(z)==182
    assert z[1:103]==y[1:103]and z[104:106]==y[104:106]
    for a,b,count in [(106,106,n),(106+n,106+nn,n),(106+2*n,106+2*nn,n),(106+3*n,106+3*nn,m),
                      (size,newsize,h),(size+h,newsize+h+1,h)]:assert z[b:b+count]==y[a:a+count]
    assert len(out['post_point_global_ledgers_preview'])==134
    assert len(out['post_point_lifetime_transfers_exact_preview'])==199
    with localcontext()as ctx:
        ctx.prec=2200
        D=Decimal.from_float;buffer=y[0]
        for kind,coefficient in [('internode','cStemG'),('leaf','cLeafG')]:
            mass=inputs[kind]['declaration']['initial_carbon']['value'];cost=out['growth_costs'][coefficient]
            structural=float(D(mass));resp=float(D(mass)*D(cost));debit=float(D(mass)*(1+D(cost)))
            components=out['flow_components'][kind]
            assert components['structural_carbon']['value']==structural
            assert components['growth_respiration']['value']==resp and components['buffer_debit']['value']==debit
            buffer=float(D(buffer)-D(debit))
        assert z[0]==buffer
        area=out['leaf_receipts'][0]['initialization']['state']['area']['value'];parameters=p['scenario']['parameters']
        capacity=float(D(parameters['leaf_heat_capacity']['value'])*D(area)/D(p['model_floor_area']['value']))
        heat=float(D(capacity)*(D(inputs['leaf']['incoming_temperature']['value'])-D(parameters['reference_temperature']['value'])))
        assert x(out['point_flows_exact']['capacity_in'])==Fraction(capacity)
        assert z[103]==float(D(y[103])+D(heat))
    for value in out['post_point_global_ledgers_preview'].values():assert abs(x(value['residual_exact']))<=x(value['budget_exact'])
    for name,value in before['pending_lifetime_transfers_exact'].items():assert out['post_point_lifetime_transfers_exact_preview'][name]==value
    assert out['candidate_sha256']==calculated['calculation_sha256']
    assert out['point_stage_RHS_evaluations']==2 and out['candidate_RHS_evaluations']==34
    assert out['effective_rights']['redistribute']is False
    assert out['at']==calculated['at']and out['elapsed_seconds_advanced']==q(0)
    assert out['checkpoint_issued']is out['history_committed']is out['material_consumed']is False
    assert out['source_current_sha256']==base._hash(pending['result'].handle.current)
    assert out['before_dense']['event_sequence']==n0['event_sequence']


def test_stateless_retry_counts_real_work_and_writes_nothing(pending,point_case,monkeypatch):
    inputs,expected=point_case;evaluate=base.stage.evaluate;calls=[]
    def count(*a,**k):calls.append(1);return evaluate(*a,**k)
    monkeypatch.setattr(base.stage,'evaluate',count)
    monkeypatch.setattr(MorphologyBlobStore,'put',lambda *a,**k:pytest.fail('point wrote CAS'))
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result==expected and len(calls)==36
    assert result['calculation_sha256']==base._hash({k:v for k,v in result.items()if k!='calculation_sha256'})


def test_stem_only_positive_seed_geometry_preserves_thermal_state(pending,calculated):
    inputs=make_inputs(pending,calculated,leaf=False,length=.01)
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='point_ready',result.get('hold')
    assert len(result['after_state'])==179 and len(result['post_point_global_ledgers_preview'])==129
    assert result['after_state'][103:106]==calculated['dense_candidate']['state'][103:106]
    assert result['after_derived']['canopy_capacity']==calculated['dense_candidate']['derived']['canopy_capacity']
    assert result['point_stage_RHS_evaluations']==1 and result['point_order']==['internode']
    assert len(result['post_point_lifetime_transfers_exact_preview'])==192


def test_independent_point_equations_growth_profile_and_exact_global_preview(pending,calculated,point_case):
    inputs,out=point_case;before=calculated['dense_candidate'];y=list(map(Fraction,before['state']));z=list(map(Fraction,out['after_state']))
    with owner._session(pending['definition'],pending['workspace'])as s:
        seed=s.math_basis['seed'];n=len(seed['program']['leaves']);m=len(seed['program']['stem_root_compartments']);h=len(seed['organs']['internodes'])
        profile=json.loads((s.origin.workspace.source_directory/s.math_basis['profile_sha256']['growth_profile']).read_bytes())
        lam=Fraction(s.profiles['exchange_profile'].values['latent_heat'])
    for key in ['cStemG','cLeafG']:assert out['growth_costs'][key]==profile['parameters'][key]['value']
    nn=n+1;size=106+3*nn+m+1;a=y[:106+3*n+m];b=z[:size]
    flow={k:x(v)for k,v in out['point_flows_exact'].items()};ca=Fraction(before['derived']['air_capacity']['value'])
    ref=Fraction(out['after_program']['scenario']['parameters']['reference_temperature']['value'])
    carbon=lambda v,count:v[0]+sum(v[3:53])+sum(v[106+2*count:])
    energy=lambda v:v[103]+ca*(v[104]-ref)+lam*v[105]
    stem=Fraction(inputs['internode']['declaration']['initial_carbon']['value']);leaf=Fraction(inputs['leaf']['declaration']['initial_carbon']['value'])
    terms={'buffer':(b[0],-a[0],flow['buffer_debit']),
           'whole_carbohydrate':(carbon(b,nn),-carbon(a,n),flow['growth_respiration']),
           'new_internode':(b[-1],-stem),
           'stem_root_carbon':(sum(b[106+3*nn:]),-sum(a[106+3*n:]),-stem),
           'capacity':(Fraction(out['after_derived']['canopy_capacity']['value']),-Fraction(before['derived']['canopy_capacity']['value']),-flow['capacity_in']),
           'canopy_sensible':(b[103],-a[103],-flow['sensible_in']),
           'air_sensible':(ca*b[104],-ca*a[104]),'vapor':(b[105],-a[105]),
           'fruit_number':(sum(b[53:103]),-sum(a[53:103])),
           'reduced_energy':(energy(b),-energy(a),-flow['sensible_in']),
           'new_leaf':(b[106+2*nn+n],-leaf)}
    assert set(terms)==set(out['point_balances'])
    for name,row in terms.items():
        residual=sum(row,Fraction(0));budget=64*Fraction(ulp(float(max(map(abs,row)))))
        assert x(out['point_balances'][name]['residual_exact'])==residual,name
        assert x(out['point_balances'][name]['budget_exact'])==budget,name
    mapping={'carbohydrate':'whole_carbohydrate','number':'fruit_number','canopy_sensible':'canopy_sensible','air_sensible':'air_sensible',
             'vapor':'vapor','area_capacity':'capacity','reduced_energy':'reduced_energy','stem_root_carbon':'stem_root_carbon',
             f'leaf_carbon_{n}':'new_leaf',f'stem_root_carbon_{m}':'new_internode'}
    for name,value in out['post_point_global_ledgers_preview'].items():
        old=before['pending_global_ledgers'].get(name);point=out['point_balances'].get(mapping.get(name))
        residual=(x(old['residual_exact'])if old else 0)+(x(point['residual_exact'])if point else 0)
        budget=(x(old['budget_exact'])if old else 0)+(x(point['budget_exact'])if point else 0)
        assert x(value['residual_exact'])==residual,name
        assert x(value['budget_exact'])==budget,name
    for key,old in before['point_totals_exact'].items():
        delta=flow.get(key,stem if key=='stem_structural_carbon'else leaf if key=='leaf_structural_carbon'else 0)
        assert x(out['post_point_point_totals_exact_preview'][key])==x(old)+delta,key
    for kind in ['leaf','stem_root']:assert out['after_birth_baselines'][kind][:-1]==seed['birth_bases'][kind]
    for kind in ['leaves','internodes']:assert out['after_geometry_baselines'][kind][:-1]==seed['geometry_baselines'][kind]
    for key,value in out['post_point_lifetime_transfers_exact_preview'].items():
        if key not in before['pending_lifetime_transfers_exact']:assert x(value)==0,key
    for value in out['seed_compatibility'].values():
        assert x(value['compatibility_budget_exact'])==0 and x(value['available_minus_required_exact'])>=0


@pytest.mark.parametrize('change',['rights','origin','definition','cursor','pending','binding','parent','sequence','event','floor','raw_hash','unit','leaf_id','seed_geometry'])
def test_invalid_source_parameters_or_rights_refuse_before_candidate(pending,point_case,monkeypatch,change):
    inputs=deepcopy(point_case[0]);event=point_case[1]['source_event']
    if change=='rights':inputs['rights']['use']=False
    elif change=='origin':inputs['origin']='observed'
    elif change in ['definition','cursor','pending','binding']:
        key={'definition':'definition_sha256','cursor':'cursor_sha256','pending':'pending_page_sha256','binding':'initial_binding_sha256'}[change];inputs[key]='0'*64
    elif change=='parent':inputs['parent_internode_id']='absent-parent'
    elif change=='sequence':inputs['source_threshold_sequence']=True
    elif change=='event':inputs['source_event_id']='old-consumed-event'
    elif change=='floor':inputs['model_floor_area']['value']*=2;refresh(inputs)
    elif change=='raw_hash':inputs['parameter_provenance']['raw_sha256']='0'*64
    elif change=='unit':inputs['internode']['construction_cost']['unit']='kg';refresh(inputs)
    elif change=='leaf_id':inputs['leaf']['declaration']['leaf_id']='wrong-new-leaf';refresh(inputs)
    elif change=='seed_geometry':inputs['internode']['initial_length']['value']=.01;inputs['internode']['construction_cost']['value']=1e12;refresh(inputs)
    monkeypatch.setattr(state,'calculate_threshold_state',lambda *a,**k:pytest.fail('invalid material reached candidate'))
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='hold'and result['after_state']is None
    assert result['progress']['candidate_RHS_evaluations']==0


@pytest.mark.parametrize('change',['candidate','time'])
def test_candidate_hash_and_exact_time_are_revalidated(pending,point_case,change):
    inputs=deepcopy(point_case[0])
    if change=='candidate':inputs['candidate_sha256']='0'*64
    else:inputs['at_elapsed_seconds_exact']=q(1)
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='hold'and result['after_state']is None
    assert result['progress']['candidate_RHS_evaluations']==34 and result['progress']['point_RHS_evaluations']==0


@pytest.mark.parametrize('kind',['internode','leaf'])
def test_insufficient_funding_never_returns_partial_material(pending,point_case,kind):
    inputs=deepcopy(point_case[0]);inputs[kind]['declaration']['initial_carbon']['value']=1e12;refresh(inputs)
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='hold'and result['hold'].startswith('FUNDING_HOLD:')
    assert result['after_state']is None and result['material_consumed']is False
    assert result['progress']['point_RHS_evaluations']==(0 if kind=='internode'else 1)


def test_late_material_input_change_clears_proposal(pending,point_case,monkeypatch):
    inputs=deepcopy(point_case[0]);stage=base.stage.evaluate;calls=[]
    def change(*a,**k):
        value=stage(*a,**k);calls.append(1)
        if len(calls)==35:inputs['reviewer']='changed-during-point'
        return value
    monkeypatch.setattr(base.stage,'evaluate',change)
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=inputs)
    assert result['status']=='hold'and result['hold'].startswith('SOURCE_HOLD:')
    assert result['after_state']is None and len(calls)==35


def test_cancel_after_stem_stage_does_not_publish_partial_leaf(pending,point_case,monkeypatch):
    stage=base.stage.evaluate;calls=[];cancel={'now':False}
    def stop(*a,**k):
        value=stage(*a,**k);calls.append(1)
        if len(calls)==35:cancel['now']=True
        return value
    monkeypatch.setattr(base.stage,'evaluate',stop)
    result=model.apply_material_point(pending['result'].handle,pending['result'].pending['page_sha256'],TOLERANCE,inputs=point_case[0],cancelled=lambda:cancel['now'])
    assert result['status']=='hold'and result['hold'].startswith('CANCELLED_HOLD:')and result['after_state']is None


def test_late_source_change_clears_point_authority(pending,point_case,tmp_path,monkeypatch):
    import shutil
    old=pending['workspace'];src=tmp_path/'source';parent=tmp_path/'parent';archive=tmp_path/'archive'
    shutil.copytree(old.source_workspace.source_directory,src);shutil.copytree(old.source_workspace.archive_directory,parent);shutil.copytree(old.archive_directory,archive)
    ws=owner.Workspace(base.Workspace(src,parent,old.access),archive,old.access)
    h=owner.open_season(owner.CursorRef(pending['result'].handle.cursor_sha256),pending['definition'],ws)
    path=src/h.basis['arithmetic_basis']['profile_sha256']['growth_profile'];stage=base.stage.evaluate;calls=[]
    def change(*a,**k):
        value=stage(*a,**k);calls.append(1)
        if len(calls)==35:path.write_bytes(path.read_bytes()+b' ')
        return value
    monkeypatch.setattr(base.stage,'evaluate',change)
    result=model.apply_material_point(h,pending['result'].pending['page_sha256'],TOLERANCE,inputs=point_case[0])
    assert result['status']=='hold'and result['after_state']is None and result['authority_hold']is not None


def test_selected_upper_bound_on_forcing_edge_is_not_a_material_order_policy(origin,tmp_path):
    ws,definition,document=setup_owner(origin,tmp_path,edge=528,end=536)
    start=owner.open_season(origin['source_ref'],definition,ws)
    result=owner.advance(start,base.AdvanceRequest(q(536),step_budget=10))
    assert result.status=='hold'and result.hold.startswith('ORDER_HOLD:')
    selected=state.calculate_threshold_state(result.handle,result.pending['page_sha256'],q(8))
    assert selected['status']=='candidate_ready',selected.get('hold')
    assert selected['at']['elapsed_seconds_exact']==q(528)
    current={'workspace':ws,'definition':definition,'document':document,'start':start,'result':result}
    inputs=make_inputs(current,selected)
    point=model.apply_material_point(result.handle,result.pending['page_sha256'],q(8),inputs=inputs)
    assert point['status']=='hold'and point['hold'].startswith('ORDER_HOLD:')
    assert point['after_state']is None and point['progress']['point_RHS_evaluations']==0
