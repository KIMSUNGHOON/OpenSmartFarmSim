"""Growing fixed leaf list; crop-growing-geometry-climate-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import isclose,isfinite,ulp
from pathlib import Path

from . import crop_explicit_lai_climate_rhs as joint
from . import crop_leaf_area as leaf_area
from . import crop_leaf_expansion as expansion

MODEL_VERSION='dynamic-air-growing-leaf-climate-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256={**joint.COMPONENT_CODE_SHA256,joint.__name__:joint.CODE_SHA256,
    **{name:sha256(Path(__file__).with_name(name+'.py').read_bytes()).hexdigest()for name in (
        'crop_leaf_area','crop_leaf_area_change','crop_leaf_expansion','crop_morphology_thermal_clock')}}
POLICIES={'normalization':leaf_area.NORMALIZATION,'thermal_age_policy':'dynamic_indoor_air_no_clip_v1',
    'capacity_policy':'declared_outflow_plus_area_capacity_derivative_v1'}
PLANT=tuple(joint.SCALAR_BLOCKS['plant_state']);COHORT=tuple(joint.ARRAY_BLOCKS['cohort_state']);CLIMATE=tuple(joint.CLIMATE_UNITS)
SCALAR={k:v for k,v in joint.SCALAR_BLOCKS.items()if k not in ('geometry','capacity_transport')}
LEAF_UNITS={'thermal_age':'degC_day','base_temperature':'degC','initial_area':'m2'}
numeric=joint.numeric


class GrowingGeometryHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise GrowingGeometryHold(reason)


def _canonical(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=2*1024**2,'CAPACITY_HOLD: 2MiB growing geometry input/output required')
    return raw


def _prepare(program):
    raw=_canonical(program);p=json.loads(raw)
    _need(type(p)is dict and set(p)=={'input_id','origin',*POLICIES,'scenario','leaves','model_floor_area','capacity_outflow'},
          'INPUT_HOLD: closed explicit growing-geometry program required')
    leaf_area._identifier(p['input_id'])
    _need(p['origin']=='synthetic'and all(p[k]==v for k,v in POLICIES.items()),'POLICY_HOLD: explicit new research policies required')
    basis,normalized=joint._quantities({k:p[k]for k in ('model_floor_area','capacity_outflow')},
        {'model_floor_area':'m2_floor','capacity_outflow':numeric.CAPACITY_RATE})
    _need(basis['model_floor_area']>0 and basis['capacity_outflow']>=0,'INPUT_HOLD: positive floor and nonnegative declared outflow required')
    s=p['scenario'];_need(type(s)is dict and set(s)=={'input_id','origin',*SCALAR,*joint.ARRAY_BLOCKS},'INPUT_HOLD: closed unassembled scenario required')
    _need(s['input_id']==p['input_id']and s['origin']=='synthetic','SCOPE_HOLD: one declared synthetic case required')
    ns={k:s[k]for k in ('input_id','origin')}
    for name,units in {**SCALAR,**joint.ARRAY_BLOCKS}.items():
        _,ns[name]=joint._quantities(s[name],units,name in joint.ARRAY_BLOCKS)
    _need(type(p['leaves'])is list and 1<=len(p['leaves'])<=512,'CAPACITY_HOLD: 1..512 explicit existing leaves required')
    leaves=[];ids=set();ages=[];areas=[];receipts=[]
    for leaf in p['leaves']:
        _need(type(leaf)is dict and set(leaf)=={'leaf_id','curve',*LEAF_UNITS},'INPUT_HOLD: closed declared existing leaf required')
        identifier=leaf['leaf_id'];leaf_area._identifier(identifier)
        _need(identifier not in ids,'INPUT_HOLD: duplicate leaf ID');ids.add(identifier)
        v,n=joint._quantities({k:leaf[k]for k in LEAF_UNITS},LEAF_UNITS)
        _need(v['thermal_age']>=0 and v['initial_area']>0,'INPUT_HOLD: nonnegative age and positive requested area required')
        curve=leaf_area.normalize_leaf_area_curve(curve=leaf['curve'])['curve']
        canonical=leaf_area._area_at(Fraction.from_float(v['thermal_age']),curve)
        _need(isclose(v['initial_area'],canonical['value'],rel_tol=1e-12,abs_tol=0),
              'INITIAL_AREA_HOLD: requested initial area differs from canonical curve')
        leaves.append({'leaf_id':identifier,'curve':curve,**n});ages.append(v['thermal_age']);areas.append(canonical['value'])
        receipts.append({'leaf_id':identifier,'requested_area':deepcopy(n['initial_area']),'canonical_area':canonical,
            'thermal_age':deepcopy(n['thermal_age'])})
    normalized={**p,**normalized,'scenario':ns,'leaves':leaves}
    y=tuple([ns['plant_state'][k]['value']for k in PLANT]+
        [q['value']for k in COHORT for q in ns['cohort_state'][k]]+[ns['climate_state'][k]['value']for k in CLIMATE]+ages+areas)
    return raw,normalized,y,receipts


def _scenario(p,y):
    s=p['scenario'];q=numeric._q
    return {**s,'plant_state':{k:q(y[i],SCALAR['plant_state'][k])for i,k in enumerate(PLANT)},
        'cohort_state':{k:[q(v,joint.ARRAY_BLOCKS['cohort_state'][k])for v in y[5+i*50:55+i*50]]for i,k in enumerate(COHORT)},
        'climate_state':{k:q(y[105+i],joint.CLIMATE_UNITS[k])for i,k in enumerate(CLIMATE)}}


def _evaluate(p,y,profiles):
    n=len(p['leaves']);age_rates=[];area_rates=[];canonical=[];gaps=[];ta=y[106];q=numeric._q
    for i,leaf in enumerate(p['leaves']):
        age=y[108+i];area=y[108+n+i];curve=leaf['curve'];maximum=curve['values']['maximum_area']['value']
        _need(age>=0 and 0<area<=maximum,'STATE_HOLD: unsupported leaf age or represented area')
        difference=numeric._sum(ta,-leaf['base_temperature']['value'])
        _need(difference>=0,'TEMPERATURE_DOMAIN_HOLD: dynamic indoor air below explicit leaf base')
        rate=numeric._divide(difference,86400)
        per_age=expansion.calculate_leaf_expansion_rate(inputs={'input_id':leaf['leaf_id'],'origin':'synthetic',
            'thermal_age_basis':'since_leaf_emergence','values':{**curve['values'],'thermal_age':q(age,'degC_day')}})['expansion_per_thermal_age']['value']
        age_rates.append(rate);area_rates.append(numeric._multiply(per_age,rate))
        point=leaf_area._area_at(Fraction.from_float(age),curve)['value'];canonical.append(point);gaps.append(numeric._sum(area,-point))
    floor=p['model_floor_area']['value'];lai=numeric._divide(numeric._sum(*y[108+n:]),floor)
    ldot=numeric._divide(numeric._sum(*area_rates),floor)
    net=numeric._multiply(p['scenario']['parameters']['leaf_heat_capacity']['value'],ldot)
    gout=p['capacity_outflow']['value'];gin=numeric._sum(gout,net)
    scenario={**_scenario(p,y),'geometry':{'model_floor_area':p['model_floor_area'],
        'leaf_area_index':q(lai,'m2_leaf/m2_floor'),'leaf_area_index_rate':q(ldot,'m2_leaf/m2_floor/s')},
        'capacity_transport':{'capacity_inflow':q(gin,numeric.CAPACITY_RATE),'capacity_outflow':q(gout,numeric.CAPACITY_RATE)}}
    r=joint.evaluate_rhs(scenario=scenario,**profiles)
    rates=tuple([r['derivatives']['plant'][k]['value']for k in PLANT]+
        [row['value']for k in COHORT for row in r['derivatives']['cohorts'][k]]+
        [r['derivatives']['climate'][k]['value']for k in CLIMATE]+age_rates+area_rates)
    return rates,{'joint':r,'leaf_age_rates':[q(v,'degC_day/s')for v in age_rates],
        'leaf_area_rates':[q(v,'m2/s')for v in area_rates],'canonical_leaf_areas':[q(v,'m2')for v in canonical],
        'curve_residuals':[q(v,'m2')for v in gaps]}


def _translate(error):
    if isinstance(error,GrowingGeometryHold):return error
    return GrowingGeometryHold(str(error)if isinstance(error,(joint.ExplicitLaiClimateHold,numeric.CanopyEnergyHold,
        leaf_area.LeafAreaHold,expansion.LeafExpansionHold,leaf_area.LeafAreaChangeHold))else'INPUT_HOLD: invalid growing geometry arithmetic/input')


def evaluate_rhs(*,program,**profiles):
    try:
        raw,p,y,receipts=_prepare(program);rates,result=_evaluate(p,y,profiles)
        result={**result,'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'raw_input_sha256':sha256(raw).hexdigest(),'program':p,'initial_area_receipts':receipts,'state':list(y),'rates':list(rates),
            'scope':'software_research_only','claim_scope':'synthetic_growing_geometry_joint_rhs_only','G0_G4':'not_assessed'}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();return result
    except(ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError,RecursionError)as error:
        raise _translate(error)from None


FLUX_UNITS={**dict.fromkeys(('photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem',
    'maintenance_fruit','removal_leaf','removal_stem','terminal_carbon'),'mg_CH2O/m2_floor'),
    **dict.fromkeys(('entry_number','terminal_number'),'fruits_equivalent/m2_floor'),
    **dict.fromkeys(('sensible','latent','incoming_heat','outgoing_heat','canopy_external','air_external'),numeric.ENERGY),
    **dict.fromkeys(('vapor','external_vapor'),'kg_water/m2_floor'),
    **dict.fromkeys(('capacity_in','capacity_out'),numeric.CAPACITY),'indoor_air_temperature_time':'degC_s'}


def _flux(p,y,evaluated):
    r=evaluated['joint'];c=r['crop'];f=p['scenario']['forcing'];x=r['exchange']['exchange'];m=r['capacity_transport']
    flow={'photosynthesis':c['photosynthesis']['value'],'growth_respiration':c['growth_respiration']['value'],
        'maintenance_leaf':c['vegetative_maintenance']['leaf']['value'],'maintenance_stem':c['vegetative_maintenance']['stem_root']['value'],
        'maintenance_fruit':c['fruit_maintenance']['value'],'removal_leaf':c['removals']['leaf']['value'],
        'removal_stem':c['removals']['stem_root']['value'],'terminal_carbon':c['cohorts']['terminal_outflow']['fruit_carbohydrate']['value'],
        'entry_number':p['scenario']['fruit_entry']['fruit_number_inflow']['value'],
        'terminal_number':c['cohorts']['terminal_outflow']['fruit_number']['value'],
        'sensible':x['sensible_heat']['value'],'latent':x['latent_heat']['value'],
        'incoming_heat':m['energy_flows']['incoming']['value'],'outgoing_heat':m['energy_flows']['outgoing']['value'],
        'canopy_external':f['canopy_external_heat']['value'],'air_external':f['air_external_sensible_heat']['value'],
        'vapor':x['water_vapor']['value'],'external_vapor':f['air_external_vapor']['value'],
        'capacity_in':m['capacity_rates']['incoming']['value'],'capacity_out':m['capacity_rates']['outgoing']['value'],
        'indoor_air_temperature_time':y[106]}
    return tuple(flow[name]for name in FLUX_UNITS)


def _advance(y,rates,dt):
    values=[]
    for old,rate in zip(y,rates,strict=True):
        increment=numeric._multiply(dt,rate);value=numeric._sum(old,increment)
        _need(increment==0 or value!=old,'NUMERIC_HOLD: nonzero increment lost to rounding')
        values.append(value)
    return tuple(values)


def _weighted(a,b,c,d):
    return tuple(numeric._divide(numeric._sum(w,numeric._multiply(2,x),numeric._multiply(2,y),z),6)
                 for w,x,y,z in zip(a,b,c,d,strict=True))


def _sample(index,dt,y,evaluated,initial_gaps):
    gaps=evaluated['curve_residuals'];q=numeric._q
    return {'step_index':index,'elapsed_seconds':index*dt,'state':list(y),'derived':deepcopy(evaluated['joint']['derived']),
        'curve_residuals':deepcopy(gaps),'curve_invariant_changes':[q(numeric._sum(row['value'],-old['value']),'m2')
            for row,old in zip(gaps,initial_gaps,strict=True)]}


def _balances(p,initial,final,totals,first,last,index,duration,latent):
    t=dict(zip(FLUX_UNITS,totals,strict=True));ca=first['joint']['derived']['air_capacity']['value'];q=numeric._q
    carbon=lambda y:numeric._sum(*y[:3],*y[5:55]);number=lambda y:numeric._sum(*y[55:105])
    dc=numeric._sum(carbon(final),-carbon(initial));dn=numeric._sum(number(final),-number(initial))
    du=numeric._sum(final[105],-initial[105]);da=numeric._multiply(ca,numeric._sum(final[106],-initial[106]))
    dw=numeric._sum(final[107],-initial[107]);ref=p['scenario']['parameters']['reference_temperature']['value']
    air0=numeric._multiply(ca,numeric._sum(initial[106],-ref));air1=numeric._multiply(ca,numeric._sum(final[106],-ref))
    cap0,cap1=(r['joint']['derived']['canopy_capacity']['value']for r in (first,last))
    sources=(t['canopy_external'],t['air_external'],numeric._multiply(latent,t['external_vapor']),t['incoming_heat'],-t['outgoing_heat'])
    rows={
        'carbohydrate':((dc,-t['photosynthesis'],t['growth_respiration'],t['maintenance_leaf'],t['maintenance_stem'],
            t['maintenance_fruit'],t['removal_leaf'],t['removal_stem'],t['terminal_carbon']),carbon(initial),carbon(final),'mg_CH2O/m2_floor'),
        'number':((dn,-t['entry_number'],t['terminal_number']),number(initial),number(final),'fruits_equivalent/m2_floor'),
        'canopy_sensible':((du,-t['canopy_external'],t['sensible'],t['latent'],-t['incoming_heat'],t['outgoing_heat']),initial[105],final[105],numeric.ENERGY),
        'air_sensible':((da,-t['air_external'],-t['sensible']),air0,air1,numeric.ENERGY),
        'vapor':((dw,-t['vapor'],-t['external_vapor']),initial[107],final[107],'kg_water/m2_floor'),
        'area_capacity':((numeric._sum(cap1,-cap0),-t['capacity_in'],t['capacity_out']),cap0,cap1,numeric.CAPACITY),
        'reduced_energy':((du,da,numeric._multiply(latent,dw),*(-v for v in sources)),
            numeric._sum(initial[105],air0,numeric._multiply(latent,initial[107])),
            numeric._sum(final[105],air1,numeric._multiply(latent,final[107])),numeric.ENERGY)}
    for i,leaf in enumerate(p['leaves']):
        age0,age1=initial[108+i],final[108+i]
        clock=numeric._divide(t['indoor_air_temperature_time'],86400)
        base=numeric._divide(numeric._multiply(leaf['base_temperature']['value'],duration),86400)
        rows['leaf_age_'+str(i)]=((numeric._sum(age1,-age0),-clock,base),age0,age1,'degC_day')
    residuals,budgets={},{}
    for name,(terms,start,end,unit)in rows.items():
        residual=numeric._sum(*terms);scale=max(abs(start),abs(end),numeric._sum(*map(abs,terms)))
        budget=numeric._multiply(64*(index+1),ulp(scale))
        _need(abs(residual)<=budget,'BALANCE_HOLD: unresolved growing '+name)
        residuals[name]=q(residual,unit);budgets[name]=q(budget,unit)
    return residuals,budgets


def integrate(*,program,step_seconds,step_count,**profiles):
    index=0;phase='initial';confirmed=None
    try:
        _need(type(step_seconds)in(int,float),'BUDGET_HOLD: explicit numeric step required');dt=float(step_seconds)
        _need(isfinite(dt)and dt>0 and type(step_count)is int and 1<=step_count<=4096,
              'BUDGET_HOLD: positive step and 1..4096 integer steps required')
        duration=numeric._multiply(dt,step_count);_need(0<duration<=600,'BUDGET_HOLD: 600s research horizon')
        raw,p,initial,receipts=_prepare(program);n=len(p['leaves'])
        _need((step_count+1)*(len(initial)+2*n+7)<=32768,'CAPACITY_HOLD: sample scalar budget exceeded')
        state=initial;rates,current=_evaluate(p,state,profiles);first=current
        initial_gaps=current['curve_residuals'];samples=[_sample(0,dt,state,current,initial_gaps)];confirmed=samples[-1]
        totals=(0.0,)*len(FLUX_UNITS);flux=_flux(p,state,current);latent=profiles['exchange_profile'].values['latent_heat']
        residuals,budgets=_balances(p,initial,state,totals,first,current,0,0,latent)
        for index in range(1,step_count+1):
            phase='k2';y2=_advance(state,rates,dt/2);k2,r2=_evaluate(p,y2,profiles)
            phase='k3';y3=_advance(state,k2,dt/2);k3,r3=_evaluate(p,y3,profiles)
            phase='k4';y4=_advance(state,k3,dt);k4,r4=_evaluate(p,y4,profiles)
            phase='endpoint';candidate=_advance(state,_weighted(rates,k2,k3,k4),dt)
            cumulative=_advance(totals,_weighted(flux,_flux(p,y2,r2),_flux(p,y3,r3),_flux(p,y4,r4)),dt)
            next_rates,next_rhs=_evaluate(p,candidate,profiles)
            phase='endpoint_balance';residuals,budgets=_balances(p,initial,candidate,cumulative,first,next_rhs,index,index*dt,latent)
            state,totals,rates,current=candidate,cumulative,next_rates,next_rhs;flux=_flux(p,state,current)
            samples.append(_sample(index,dt,state,current,initial_gaps));confirmed=samples[-1]
        numerical={'method':'shared-stage-fixed-rk4-growing-area-v1','step_seconds':dt,'step_count':step_count,
            'duration_seconds':duration,'rhs_evaluations':4*step_count+1,'sample_scalar_budget':32768,
            'forcing_sampling':'explicit_constant_except_joint_dynamic_states',
            'roundoff_rule':'64-ulp-per-step-ledger-v1','time_coordinate':'elapsed_seconds_no_UTC_checkpoint'}
        result={'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'raw_input_sha256':sha256(raw).hexdigest(),'profile_sha256':first['joint']['profile_sha256'],
            'initial_stage_calculation_sha256':first['joint']['calculation_sha256'],'program':p,
            'initial_area_receipts':receipts,'numerical':numerical,'samples':samples,
            'state_layout':{'plant':list(PLANT),'cohort_arrays':list(COHORT),'climate':list(CLIMATE),
                'leaf_ids':[leaf['leaf_id']for leaf in p['leaves']],'leaf_blocks':['thermal_age','area'],
                'units':{'plant':SCALAR['plant_state'],'cohort_arrays':joint.ARRAY_BLOCKS['cohort_state'],
                    'climate':joint.CLIMATE_UNITS,'leaf_blocks':{'thermal_age':'degC_day','area':'m2'}}},
            'integrated_transfers':{name:numeric._q(value,unit)for(name,unit),value in zip(FLUX_UNITS.items(),totals,strict=True)},
            'canopy_water_boundary':numeric._q(-dict(zip(FLUX_UNITS,totals))['vapor'],'kg_water/m2_floor'),
            'balance_residuals':residuals,'balance_budgets':budgets,'scope':'software_research_only',
            'claim_scope':'synthetic_growing_geometry_short_integration_only','G0_G4':'not_assessed'}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result)
        return result
    except(ValueError,TypeError,KeyError,OverflowError,ZeroDivisionError,RecursionError)as error:
        held=_translate(error);held.step_index=index;held.failed_stage=phase
        held.last_confirmed_sample=deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds=None if confirmed is None else confirmed['elapsed_seconds']
        raise held from None
