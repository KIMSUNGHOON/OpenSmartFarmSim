"""Fixed individual organ stocks; crop-stem-root-stock-dynamics-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from math import isfinite, ulp
from pathlib import Path
from sys import modules

from . import crop_leaf_carbon_stock_dynamics as leaf
from . import crop_stem_root_carbon_stock_rhs as stock

old = leaf.old
numeric = old.numeric
MODEL_VERSION = 'dynamic-individual-stem-root-leaf-carbon-climate-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256 = {**leaf.COMPONENT_CODE_SHA256, leaf.__name__: leaf.CODE_SHA256,
                         **stock.COMPONENT_CODE_SHA256, stock.__name__: stock.CODE_SHA256}
POLICIES = {**leaf.POLICIES, 'stem_root_stock_policy': stock.POLICY_ID}
PLANT = tuple(k for k in leaf.PLANT if k != 'stem_root')
COHORT = leaf.COHORT
CLIMATE = leaf.CLIMATE
MAX_BYTES = 2*1024**2
STOCK_FIELDS = {'initial_carbon': stock.part.source.MASS_UNIT, 'sink_weight': '1', 'carbon_removal': stock.part.source.RATE_UNIT}


class StemRootDynamicsHold(ValueError):
    pass


def _need(condition, reason):
    if not condition: raise StemRootDynamicsHold(reason)


def _canonical(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: 2MiB stem/root dynamics input/output required')
    return raw


def _fence():
    for name,digest in {**COMPONENT_CODE_SHA256, __name__: CODE_SHA256}.items():
        path = Path(modules[name].__file__) if name.startswith('app.') else Path(__file__).with_name(name+'.py')
        _need(sha256(path.read_bytes()).hexdigest() == digest, 'CODE_HOLD: original organ dynamics sources required')


def _prepare(program):
    _need(type(program) is dict and type(program.get('leaves')) is list and type(program.get('stem_root_compartments')) is list,
          'INPUT_HOLD: declared leaf and stem/root stock lists required')
    raw = _canonical(program); p = json.loads(raw); part = stock.part
    part._closed(p, {'input_id', 'origin', *POLICIES, 'scenario', 'leaves', 'model_floor_area', 'capacity_outflow', 'stem_root_compartments'})
    _need(p['stem_root_stock_policy'] == stock.POLICY_ID, 'POLICY_HOLD: explicit stem/root stock policy required')
    part._closed(p['scenario']['plant_state'], set(old.SCALAR['plant_state'])-{'leaf','stem_root'})
    part._closed(p['scenario']['removals'], set(old.SCALAR['removals'])-{'leaf','stem_root'})
    _need(1 <= len(p['stem_root_compartments']) <= 512, 'CAPACITY_HOLD: 1..512 explicit organ stocks required')
    rows = []
    for row in p['stem_root_compartments']:
        part._closed(row, {'compartment_id', 'kind', *STOCK_FIELDS}); part._id(row['compartment_id'])
        _need(row['kind'] in ('internode','root_system'), 'INVENTORY_HOLD: explicit organ kind required')
        rows.append({'compartment_id':row['compartment_id'], 'kind':row['kind'],
                     **{k:part._q(part._number(row[k],unit),unit) for k,unit in STOCK_FIELDS.items()}})
    _need(len({r['compartment_id'] for r in rows}) == len(rows) and sum(r['kind']=='root_system' for r in rows) == 1,
          'INVENTORY_HOLD: unique IDs and exactly one root system required')
    adapter = {k:deepcopy(v) for k,v in p.items() if k not in ('stem_root_stock_policy','stem_root_compartments')}
    adapter['scenario']['plant_state']['stem_root'] = part._q(stock._sum(r['initial_carbon']['value'] for r in rows), part.source.MASS_UNIT)
    adapter['scenario']['removals']['stem_root'] = part._q(stock._sum(r['carbon_removal']['value'] for r in rows))
    _,normalized,y,receipts = leaf._prepare(adapter)
    normalized['scenario']['plant_state'].pop('stem_root'); normalized['scenario']['removals'].pop('stem_root')
    normalized.update(stem_root_stock_policy=stock.POLICY_ID, stem_root_compartments=rows)
    state = tuple([y[0], *y[2:], *(r['initial_carbon']['value'] for r in rows)])
    return raw,normalized,state,receipts


def _project(p,y):
    n,m = len(p['leaves']),len(p['stem_root_compartments']); offset = 106+3*n
    _need(len(y) == offset+m, 'STATE_HOLD: explicit organ vector shape required')
    return leaf._project(p, tuple([y[0], stock._sum(y[offset:]), *y[1:offset]]))


def _evaluate(p,y,profiles):
    n = len(p['leaves']); q = numeric._q; ages,areas,canonical,gaps = [],[],[],[]
    for i,row in enumerate(p['leaves']):
        age,area,curve = y[106+i],y[106+n+i],row['curve']
        _need(age >= 0 and 0 < area <= curve['values']['maximum_area']['value'], 'STATE_HOLD: supported leaf age/area required')
        delta = numeric._sum(y[104], -row['base_temperature']['value'])
        _need(delta >= 0, 'TEMPERATURE_DOMAIN_HOLD: indoor air below leaf base')
        rate = numeric._divide(delta,86400)
        per_age = old.expansion.calculate_leaf_expansion_rate(inputs={'input_id':row['leaf_id'], 'origin':'synthetic',
            'thermal_age_basis':'since_leaf_emergence', 'values':{**curve['values'], 'thermal_age':q(age,'degC_day')}})['expansion_per_thermal_age']['value']
        ages.append(rate); areas.append(numeric._multiply(per_age,rate))
        point = old.leaf_area._area_at(Fraction.from_float(age),curve)['value']; canonical.append(point); gaps.append(numeric._sum(area,-point))
    lai = numeric._divide(numeric._sum(*y[106+n:106+2*n]),p['model_floor_area']['value'])
    ldot = numeric._divide(numeric._sum(*areas),p['model_floor_area']['value']); gout = p['capacity_outflow']['value']
    scenario = old._scenario(p,_project(p,y)); scenario['plant_state'].pop('leaf'); scenario['plant_state'].pop('stem_root')
    scenario.update(geometry={'model_floor_area':p['model_floor_area'], 'leaf_area_index':q(lai,'m2_leaf/m2_floor'),
        'leaf_area_index_rate':q(ldot,'m2_leaf/m2_floor/s')}, capacity_transport={'capacity_outflow':q(gout,numeric.CAPACITY_RATE),
        'capacity_inflow':q(numeric._sum(gout,numeric._multiply(p['scenario']['parameters']['leaf_heat_capacity']['value'],ldot)),numeric.CAPACITY_RATE)})
    r = stock.evaluate_rhs(scenario=scenario, leaf_stocks={'input_id':p['input_id'], 'origin':'synthetic', 'policy':leaf.stock.POLICY_ID,
        'model_floor_area':p['model_floor_area'], 'leaf_ids':[row['leaf_id'] for row in p['leaves']],
        'leaves':[{'leaf_id':row['leaf_id'], 'carbon':q(y[106+2*n+i],stock.part.source.MASS_UNIT),
            'sink_weight':row['sink_weight'], 'removal':row['carbon_removal']} for i,row in enumerate(p['leaves'])]},
        stem_root_stocks={'input_id':p['input_id'], 'origin':'synthetic', 'policy':stock.POLICY_ID, 'model_floor_area':p['model_floor_area'],
            'compartments':[{'compartment_id':row['compartment_id'], 'kind':row['kind'],
                'carbon':q(y[106+3*n+i],stock.part.source.MASS_UNIT), 'sink_weight':row['sink_weight'], 'removal':row['carbon_removal']}
                for i,row in enumerate(p['stem_root_compartments'])]}, **profiles)
    leaves = r['source_stage']['source_stage']['leaf_rates']
    rates = tuple([r['derivatives']['plant'][k]['value'] for k in PLANT] +
        [row['value'] for k in COHORT for row in r['derivatives']['cohorts'][k]] +
        [r['derivatives']['climate'][k]['value'] for k in CLIMATE] + ages + areas +
        [row['derivative']['value'] for row in leaves] + [row['derivative']['value'] for row in r['stem_root_rates']])
    return rates,{'stock_rhs':r, 'leaf_age_rates':[q(v,'degC_day/s') for v in ages], 'leaf_area_rates':[q(v,'m2/s') for v in areas],
                  'canonical_leaf_areas':[q(v,'m2') for v in canonical], 'curve_residuals':[q(v,'m2') for v in gaps]}


def _view(e):
    r = e['stock_rhs']; leaves = r['source_stage']['source_stage']; j = leaves['source_stage']['source_joint']; c = j['crop']
    return {'curve_residuals':e['curve_residuals'], 'joint':{
        'derived':{**j['derived'], 'leaf_carbohydrate':leaves['leaf_totals']['carbon'], 'stem_root_carbohydrate':r['stem_root_totals']['carbon']},
        'exchange':j['exchange'], 'capacity_transport':j['capacity_transport'],
        'crop':{'photosynthesis':c['photosynthesis'], 'growth_respiration':r['adjusted_carbon']['growth_respiration'],
            'vegetative_maintenance':{'leaf':leaves['leaf_totals']['maintenance'], 'stem_root':r['stem_root_totals']['maintenance']},
            'fruit_maintenance':c['fruit_maintenance'], 'removals':{'leaf':leaves['leaf_totals']['removal'], 'stem_root':r['stem_root_totals']['removal']},
            'cohorts':c['cohorts']}}}


def _flux_units(p):
    return {**leaf._flux_units(p), **{f'stem_root_{i}_{k}':stock.part.source.MASS_UNIT for i in range(len(p['stem_root_compartments'])) for k in ('inflow','maintenance','removal')}}


def _flux(p,y,e):
    r = e['stock_rhs']; leaves = r['source_stage']['source_stage']['leaf_rates']
    return old._flux(p,_project(p,y),_view(e)) + tuple(row[k]['value'] for row in leaves+r['stem_root_rates'] for k in ('inflow','maintenance','removal'))


def _sample(index,dt,y,e,gaps): return old._sample(index,dt,y,_view(e),gaps)
_advance = old._advance
_weighted = old._weighted


def _balances(p,initial,final,totals,first,last,index,duration,latent):
    residuals,budgets = old._balances(p,_project(p,initial),_project(p,final),totals[:21],_view(first),_view(last),index,duration,latent)
    n,m = len(p['leaves']),len(p['stem_root_compartments']); rows = []
    for label,start,count,flow_start in [('leaf',106+2*n,n,21), ('stem_root',106+3*n,m,21+3*n)]:
        for i in range(count):
            a,b = initial[start+i],final[start+i]; g,M,R = totals[flow_start+3*i:flow_start+3*i+3]
            rows.append((f'{label}_carbon_{i}',a,b,(numeric._sum(b,-a),-g,M,R)))
    a,b = (stock._sum(y[106+3*n:]) for y in (initial,final))
    g,M,R = (numeric._sum(*totals[21+3*n+k::3]) for k in range(3))
    rows.append(('stem_root_carbon',a,b,(numeric._sum(b,-a),-g,M,R)))
    for name,a,b,terms in rows:
        residual = numeric._sum(*terms); budget = numeric._multiply(64*(index+1),ulp(max(abs(a),abs(b),numeric._sum(*map(abs,terms)))))
        _need(abs(residual) <= budget, 'BALANCE_HOLD: unresolved integrated '+name)
        residuals[name] = numeric._q(residual,stock.part.source.MASS_UNIT); budgets[name] = numeric._q(budget,stock.part.source.MASS_UNIT)
    return residuals,budgets


def _layout(p):
    layout = leaf._layout(p); layout['plant'] = list(PLANT); layout['units']['plant'].pop('stem_root')
    return {**layout, 'stem_root_compartments':[{k:r[k] for k in ('compartment_id','kind')} for r in p['stem_root_compartments']],
            'stem_root_blocks':['carbon'], 'units':{**layout['units'], 'stem_root_blocks':{'carbon':stock.part.source.MASS_UNIT}}}


def _translate(error):
    if isinstance(error,StemRootDynamicsHold): return error
    if isinstance(error,(stock.StemRootCarbonStockHold,stock.part.StemRootPartitionHold,leaf.StockDynamicsHold,
        old.GrowingGeometryHold,numeric.CanopyEnergyHold,old.leaf_area.LeafAreaHold,old.expansion.LeafExpansionHold,old.leaf_area.LeafAreaChangeHold)):
        return StemRootDynamicsHold(str(error))
    return StemRootDynamicsHold('INPUT_HOLD: invalid individual organ dynamics input/arithmetic')


def evaluate_rhs(*,program,**profiles):
    try:
        _fence(); raw,p,y,receipts = _prepare(program); rates,e = _evaluate(p,y,profiles)
        r = {**e, 'model_version':MODEL_VERSION, 'code_sha256':CODE_SHA256, 'component_code_sha256':dict(COMPONENT_CODE_SHA256),
             'raw_input_sha256':sha256(raw).hexdigest(), 'program':p, 'initial_area_receipts':receipts, 'state':list(y), 'rates':list(rates),
             'state_layout':_layout(p), 'scope':'software_research_only', 'claim_scope':'synthetic_individual_stem_root_dynamic_rhs_only', 'G0_G4':'not_assessed'}
        r['calculation_sha256'] = sha256(_canonical(r)).hexdigest(); _canonical(r); _fence(); return r
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error: raise _translate(error) from None


def integrate(*,program,step_seconds,step_count,**profiles):
    index = 0; phase = 'initial'; confirmed = confirmed_totals = residuals = budgets = None
    try:
        _fence(); _need(type(step_seconds) in (int,float), 'BUDGET_HOLD: explicit numeric step required'); dt = float(step_seconds)
        _need(isfinite(dt) and dt > 0 and type(step_count) is int and 1 <= step_count <= 4096, 'BUDGET_HOLD: positive step/1..4096 steps required')
        duration = numeric._multiply(dt,step_count); _need(0 < duration <= 600, 'BUDGET_HOLD: 600s research horizon')
        raw,p,state,receipts = _prepare(program); n = len(p['leaves']); initial = state; units = _flux_units(p)
        _need((step_count+1)*(len(state)+2*n+9) <= 32768, 'CAPACITY_HOLD: sample scalar budget exceeded')
        rates,current = _evaluate(p,state,profiles); first = current; gaps = first['curve_residuals']; latent = profiles['exchange_profile'].values['latent_heat']
        totals = (0.,)*len(units); flux = _flux(p,state,current)
        residuals,budgets = _balances(p,initial,state,totals,first,current,0,0,latent)
        samples = [_sample(0,dt,state,current,gaps)]; confirmed = samples[-1]; confirmed_totals = totals
        for index in range(1,step_count+1):
            phase = 'k2'; y2 = _advance(state,rates,dt/2); k2,r2 = _evaluate(p,y2,profiles)
            phase = 'k3'; y3 = _advance(state,k2,dt/2); k3,r3 = _evaluate(p,y3,profiles)
            phase = 'k4'; y4 = _advance(state,k3,dt); k4,r4 = _evaluate(p,y4,profiles)
            phase = 'endpoint'; candidate = _advance(state,_weighted(rates,k2,k3,k4),dt)
            cumulative = _advance(totals,_weighted(flux,_flux(p,y2,r2),_flux(p,y3,r3),_flux(p,y4,r4)),dt)
            next_rates,next_rhs = _evaluate(p,candidate,profiles)
            phase = 'endpoint_balance'; new_residuals,new_budgets = _balances(p,initial,candidate,cumulative,first,next_rhs,index,index*dt,latent)
            sample = _sample(index,dt,candidate,next_rhs,gaps)
            state,totals,rates,current = candidate,cumulative,next_rates,next_rhs; flux = _flux(p,state,current)
            residuals,budgets = new_residuals,new_budgets; samples.append(sample); confirmed = sample; confirmed_totals = totals
        phase = 'output'; result = {'model_version':MODEL_VERSION, 'code_sha256':CODE_SHA256, 'component_code_sha256':dict(COMPONENT_CODE_SHA256),
            'raw_input_sha256':sha256(raw).hexdigest(), 'profile_sha256':first['stock_rhs']['profile_sha256'],
            'initial_stage_calculation_sha256':first['stock_rhs']['calculation_sha256'], 'program':p, 'initial_area_receipts':receipts,
            'numerical':{'method':'shared-stage-fixed-rk4-leaf-stem-root-carbon-area-v1', 'step_seconds':dt, 'step_count':step_count,
                'duration_seconds':duration, 'rhs_evaluations':4*step_count+1, 'sample_scalar_budget':32768,
                'forcing_sampling':'explicit_constant_except_joint_dynamic_states', 'roundoff_rule':'64-ulp-per-step-ledger-v1',
                'time_coordinate':'elapsed_seconds_no_UTC_checkpoint'}, 'samples':samples, 'state_layout':_layout(p),
            'integrated_transfers':{name:numeric._q(v,unit) for (name,unit),v in zip(units.items(),totals,strict=True)},
            'canopy_water_boundary':numeric._q(-totals[list(units).index('vapor')],'kg_water/m2_floor'),
            'balance_residuals':residuals, 'balance_budgets':budgets, 'scope':'software_research_only',
            'claim_scope':'synthetic_stem_root_stock_short_integration_only', 'G0_G4':'not_assessed'}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest(); _canonical(result); _fence(); return result
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
        held = _translate(error); held.step_index = index; held.failed_stage = phase; held.last_confirmed_sample = deepcopy(confirmed)
        held.last_confirmed_elapsed_seconds = None if confirmed is None else confirmed['elapsed_seconds']
        held.last_confirmed_integrated_transfers = None if confirmed_totals is None else {
            name:numeric._q(v,unit) for (name,unit),v in zip(units.items(),confirmed_totals,strict=True)}
        held.last_confirmed_balance_residuals = deepcopy(residuals); held.last_confirmed_balance_budgets = deepcopy(budgets)
        raise held from None
