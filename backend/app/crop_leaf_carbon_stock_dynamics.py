"""Fixed-list Ci/a/A dynamics; crop-leaf-carbon-stock-dynamics-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite,ulp
from pathlib import Path
from sys import modules

from . import crop_growing_geometry_climate as old
from . import crop_leaf_carbon_stock_rhs as stock

MODEL_VERSION='dynamic-individual-leaf-carbon-area-climate-research-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256={**stock.COMPONENT_CODE_SHA256,stock.__name__:stock.CODE_SHA256,
    **old.COMPONENT_CODE_SHA256,old.__name__:old.CODE_SHA256}
POLICIES={**old.POLICIES,'leaf_stock_policy':stock.POLICY_ID}
PLANT=tuple(k for k in old.PLANT if k!='leaf');COHORT=old.COHORT;CLIMATE=old.CLIMATE
STOCK_FIELDS={'initial_carbon':stock.part.source.MASS_UNIT,'sink_weight':'1','carbon_removal':stock.part.source.RATE_UNIT}
numeric=old.numeric
MAX_BYTES=2*1024**2


class StockDynamicsHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise StockDynamicsHold(reason)


def _canonical(v):
    raw=json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=MAX_BYTES,'CAPACITY_HOLD: 2MiB stock dynamics input/output required');return raw


def _fence():
    for name,h in {**COMPONENT_CODE_SHA256,__name__:CODE_SHA256}.items():
        path=Path(modules[name].__file__)if name.startswith('app.')else Path(__file__).with_name(name+'.py')
        _need(sha256(path.read_bytes()).hexdigest()==h,'CODE_HOLD: original dynamics and component sources required')


def _prepare(program):
    _need(type(program)is dict and type(program.get('leaves'))is list,'INPUT_HOLD: declared stock program/list required')
    raw=_canonical(program);p=json.loads(raw)
    stock.part._closed(p,{'input_id','origin',*POLICIES,'scenario','leaves','model_floor_area','capacity_outflow'})
    _need(p['leaf_stock_policy']==stock.POLICY_ID,'POLICY_HOLD: explicit individual stock policy required')
    _need(1<=len(p['leaves'])<=512,'CAPACITY_HOLD: 1..512 existing leaves required')
    stock.part._closed(p['scenario']['plant_state'],set(old.SCALAR['plant_state'])-{'leaf'})
    stock.part._closed(p['scenario']['removals'],set(old.SCALAR['removals'])-{'leaf'})
    stocks=[];leaves=[]
    for leaf in p['leaves']:
        stock.part._closed(leaf,{'leaf_id','curve',*old.LEAF_UNITS,*STOCK_FIELDS})
        stocks.append({k:stock.part._q(stock.part._number(leaf[k],unit),unit)for k,unit in STOCK_FIELDS.items()})
        leaves.append({k:deepcopy(v)for k,v in leaf.items()if k not in STOCK_FIELDS})
    adapter={k:deepcopy(v)for k,v in p.items()if k!='leaf_stock_policy'};adapter['leaves']=leaves
    adapter['scenario']['plant_state']['leaf']=stock.part._q(stock._sum(x['initial_carbon']['value']for x in stocks),stock.part.source.MASS_UNIT)
    adapter['scenario']['removals']['leaf']=stock.part._q(stock._sum(x['carbon_removal']['value']for x in stocks))
    _,normalized,y,receipts=old._prepare(adapter)
    normalized['scenario']['plant_state'].pop('leaf');normalized['scenario']['removals'].pop('leaf')
    normalized['leaf_stock_policy']=stock.POLICY_ID
    normalized['leaves']=[{**leaf,**s}for leaf,s in zip(normalized['leaves'],stocks,strict=True)]
    state=tuple([y[0],*y[2:],*(x['initial_carbon']['value']for x in stocks)])
    return raw,normalized,state,receipts


def _project(p,y):
    n=len(p['leaves']);_need(len(y)==107+3*n,'STATE_HOLD: stock vector shape required')
    return tuple([y[0],stock._sum(y[107+2*n:]),*y[1:107+2*n]])


def _evaluate(p,y,profiles):
    n=len(p['leaves']);ages=[];areas=[];canonical=[];gaps=[];q=numeric._q
    for i,leaf in enumerate(p['leaves']):
        age=y[107+i];area=y[107+n+i];curve=leaf['curve']
        _need(age>=0 and 0<area<=curve['values']['maximum_area']['value'],'STATE_HOLD: supported leaf age/area required')
        delta=numeric._sum(y[105],-leaf['base_temperature']['value']);_need(delta>=0,'TEMPERATURE_DOMAIN_HOLD: indoor air below leaf base')
        rate=numeric._divide(delta,86400)
        per_age=old.expansion.calculate_leaf_expansion_rate(inputs={'input_id':leaf['leaf_id'],'origin':'synthetic',
            'thermal_age_basis':'since_leaf_emergence','values':{**curve['values'],'thermal_age':q(age,'degC_day')}})['expansion_per_thermal_age']['value']
        ages.append(rate);areas.append(numeric._multiply(per_age,rate))
        point=old.leaf_area._area_at(Fraction.from_float(age),curve)['value'];canonical.append(point);gaps.append(numeric._sum(area,-point))
    lai=numeric._divide(numeric._sum(*y[107+n:107+2*n]),p['model_floor_area']['value'])
    ldot=numeric._divide(numeric._sum(*areas),p['model_floor_area']['value']);gout=p['capacity_outflow']['value']
    scenario=old._scenario(p,_project(p,y));scenario['plant_state'].pop('leaf')
    scenario.update(geometry={'model_floor_area':p['model_floor_area'],'leaf_area_index':q(lai,'m2_leaf/m2_floor'),
        'leaf_area_index_rate':q(ldot,'m2_leaf/m2_floor/s')},capacity_transport={'capacity_outflow':q(gout,numeric.CAPACITY_RATE),
        'capacity_inflow':q(numeric._sum(gout,numeric._multiply(p['scenario']['parameters']['leaf_heat_capacity']['value'],ldot)),numeric.CAPACITY_RATE)})
    r=stock.evaluate_rhs(scenario=scenario,leaf_stocks={'input_id':p['input_id'],'origin':'synthetic','policy':stock.POLICY_ID,
        'model_floor_area':p['model_floor_area'],'leaf_ids':[x['leaf_id']for x in p['leaves']],
        'leaves':[{'leaf_id':leaf['leaf_id'],'carbon':q(y[107+2*n+i],stock.part.source.MASS_UNIT),
            'sink_weight':leaf['sink_weight'],'removal':leaf['carbon_removal']}for i,leaf in enumerate(p['leaves'])]},**profiles)
    rates=tuple([r['derivatives']['plant'][k]['value']for k in PLANT]+
        [row['value']for k in COHORT for row in r['derivatives']['cohorts'][k]]+
        [r['derivatives']['climate'][k]['value']for k in CLIMATE]+ages+areas+[x['derivative']['value']for x in r['leaf_rates']])
    return rates,{'stock_rhs':r,'leaf_age_rates':[q(v,'degC_day/s')for v in ages],'leaf_area_rates':[q(v,'m2/s')for v in areas],
        'canonical_leaf_areas':[q(v,'m2')for v in canonical],'curve_residuals':[q(v,'m2')for v in gaps]}


def _view(e):
    r=e['stock_rhs'];s=r['source_stage'];j=s['source_joint'];c=j['crop']
    return {'curve_residuals':e['curve_residuals'],'joint':{
        'derived':{**j['derived'],'leaf_carbohydrate':r['leaf_totals']['carbon']},'exchange':j['exchange'],'capacity_transport':j['capacity_transport'],
        'crop':{'photosynthesis':c['photosynthesis'],'growth_respiration':s['adjusted_carbon']['growth_respiration'],
            'vegetative_maintenance':{**c['vegetative_maintenance'],'leaf':r['leaf_totals']['maintenance']},
            'fruit_maintenance':c['fruit_maintenance'],'removals':{**c['removals'],'leaf':r['leaf_totals']['removal']},'cohorts':c['cohorts']}}}


def _flux_units(p):return {**old.FLUX_UNITS,**{f'leaf_{i}_{k}':stock.part.source.MASS_UNIT for i in range(len(p['leaves']))for k in('inflow','maintenance','removal')}}
def _flux(p,y,e):return old._flux(p,_project(p,y),_view(e))+tuple(x[k]['value']for x in e['stock_rhs']['leaf_rates']for k in('inflow','maintenance','removal'))
def _sample(index,dt,y,e,gaps):return old._sample(index,dt,y,_view(e),gaps)
_advance=old._advance
_weighted=old._weighted


def _balances(p,initial,final,totals,first,last,index,duration,latent):
    residuals,budgets=old._balances(p,_project(p,initial),_project(p,final),totals[:21],_view(first),_view(last),index,duration,latent)
    n=len(p['leaves'])
    for i in range(n):
        a,b=initial[107+2*n+i],final[107+2*n+i];g,m,r=totals[21+3*i:24+3*i]
        terms=(numeric._sum(b,-a),-g,m,r);residual=numeric._sum(*terms)
        budget=numeric._multiply(64*(index+1),ulp(max(abs(a),abs(b),numeric._sum(*map(abs,terms)))))
        _need(abs(residual)<=budget,'BALANCE_HOLD: unresolved individual integrated carbon')
        residuals['leaf_carbon_'+str(i)]=numeric._q(residual,stock.part.source.MASS_UNIT)
        budgets['leaf_carbon_'+str(i)]=numeric._q(budget,stock.part.source.MASS_UNIT)
    return residuals,budgets


def _layout(p):
    return {'plant':list(PLANT),'cohort_arrays':list(COHORT),'climate':list(CLIMATE),'leaf_ids':[x['leaf_id']for x in p['leaves']],
        'leaf_blocks':['thermal_age','area','carbon'],'units':{'plant':{k:old.SCALAR['plant_state'][k]for k in PLANT},
            'cohort_arrays':old.joint.ARRAY_BLOCKS['cohort_state'],'climate':old.joint.CLIMATE_UNITS,
            'leaf_blocks':{'thermal_age':'degC_day','area':'m2','carbon':stock.part.source.MASS_UNIT}}}


def _translate(error):
    if isinstance(error,StockDynamicsHold):return error
    if isinstance(error,(stock.LeafCarbonStockHold,old.GrowingGeometryHold,numeric.CanopyEnergyHold,
        old.leaf_area.LeafAreaHold,old.expansion.LeafExpansionHold,old.leaf_area.LeafAreaChangeHold)):return StockDynamicsHold(str(error))
    return StockDynamicsHold('INPUT_HOLD: invalid stock dynamics input/arithmetic')


def evaluate_rhs(*,program,**profiles):
    try:
        _fence();raw,p,y,receipts=_prepare(program);rates,e=_evaluate(p,y,profiles)
        r={**e,'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'raw_input_sha256':sha256(raw).hexdigest(),'program':p,'initial_area_receipts':receipts,'state':list(y),'rates':list(rates),
            'state_layout':_layout(p),'scope':'software_research_only','claim_scope':'synthetic_leaf_carbon_stock_dynamic_rhs_only','G0_G4':'not_assessed'}
        r['calculation_sha256']=sha256(_canonical(r)).hexdigest();_canonical(r);_fence();return r
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:raise _translate(error)from None


def integrate(*,program,step_seconds,step_count,**profiles):
    index=0;phase='initial';confirmed=None;confirmed_totals=None;residuals=budgets=None
    try:
        _fence();_need(type(step_seconds)in(int,float),'BUDGET_HOLD: explicit numeric step required');dt=float(step_seconds)
        _need(isfinite(dt)and dt>0 and type(step_count)is int and 1<=step_count<=4096,'BUDGET_HOLD: positive step/1..4096 steps required')
        duration=numeric._multiply(dt,step_count);_need(0<duration<=600,'BUDGET_HOLD: 600s research horizon')
        raw,p,state,receipts=_prepare(program);n=len(p['leaves']);initial=state;units=_flux_units(p)
        _need((step_count+1)*(len(state)+2*n+8)<=32768,'CAPACITY_HOLD: sample scalar budget exceeded')
        rates,current=_evaluate(p,state,profiles);first=current;gaps=first['curve_residuals'];latent=profiles['exchange_profile'].values['latent_heat']
        totals=(0.,)*len(units);flux=_flux(p,state,current)
        residuals,budgets=_balances(p,initial,state,totals,first,current,0,0,latent)
        samples=[_sample(0,dt,state,current,gaps)];confirmed=samples[-1];confirmed_totals=totals
        for index in range(1,step_count+1):
            phase='k2';y2=_advance(state,rates,dt/2);k2,r2=_evaluate(p,y2,profiles)
            phase='k3';y3=_advance(state,k2,dt/2);k3,r3=_evaluate(p,y3,profiles)
            phase='k4';y4=_advance(state,k3,dt);k4,r4=_evaluate(p,y4,profiles)
            phase='endpoint';candidate=_advance(state,_weighted(rates,k2,k3,k4),dt)
            cumulative=_advance(totals,_weighted(flux,_flux(p,y2,r2),_flux(p,y3,r3),_flux(p,y4,r4)),dt)
            next_rates,next_rhs=_evaluate(p,candidate,profiles)
            phase='endpoint_balance';new_residuals,new_budgets=_balances(p,initial,candidate,cumulative,first,next_rhs,index,index*dt,latent)
            sample=_sample(index,dt,candidate,next_rhs,gaps)
            state,totals,rates,current=candidate,cumulative,next_rates,next_rhs;flux=_flux(p,state,current)
            residuals,budgets=new_residuals,new_budgets;samples.append(sample);confirmed=sample;confirmed_totals=totals
        phase='output';result={'model_version':MODEL_VERSION,'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'raw_input_sha256':sha256(raw).hexdigest(),'profile_sha256':first['stock_rhs']['profile_sha256'],
            'initial_stage_calculation_sha256':first['stock_rhs']['calculation_sha256'],'program':p,'initial_area_receipts':receipts,
            'numerical':{'method':'shared-stage-fixed-rk4-individual-carbon-area-v1','step_seconds':dt,'step_count':step_count,
                'duration_seconds':duration,'rhs_evaluations':4*step_count+1,'sample_scalar_budget':32768,
                'forcing_sampling':'explicit_constant_except_joint_dynamic_states','roundoff_rule':'64-ulp-per-step-ledger-v1',
                'time_coordinate':'elapsed_seconds_no_UTC_checkpoint'},'samples':samples,'state_layout':_layout(p),
            'integrated_transfers':{name:numeric._q(v,unit)for(name,unit),v in zip(units.items(),totals,strict=True)},
            'canopy_water_boundary':numeric._q(-totals[list(units).index('vapor')],'kg_water/m2_floor'),
            'balance_residuals':residuals,'balance_budgets':budgets,'scope':'software_research_only',
            'claim_scope':'synthetic_leaf_carbon_stock_short_integration_only','G0_G4':'not_assessed'}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result);_fence();return result
    except(ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError)as error:
        held=_translate(error);held.step_index=index;held.failed_stage=phase;held.last_confirmed_sample=deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds=None if confirmed is None else confirmed['elapsed_seconds']
        held.last_confirmed_integrated_transfers=None if confirmed_totals is None else{
            name:numeric._q(v,unit)for(name,unit),v in zip(units.items(),confirmed_totals,strict=True)}
        held.last_confirmed_balance_residuals=deepcopy(residuals);held.last_confirmed_balance_budgets=deepcopy(budgets)
        raise held from None
