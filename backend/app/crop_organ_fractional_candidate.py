"""Exact-time mixed-organ candidates; crop-organ-fractional-candidate-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import ulp
from pathlib import Path

from . import crop_organ_next_threshold as interval
from . import crop_funded_event_state as old

stock = interval.stock
VERSION = 'individual-organ-fractional-candidate-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
REFINEMENTS = (1,2,4)
F = Fraction.from_float
Q = interval.event._rational
MASS = stock.leaf.MASS


class FractionalCandidateHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise FractionalCandidateHold(reason)


def _pins():
    expected = {**interval._pins(), 'backend/app/crop_funded_event_state.py': old.CODE_SHA256,
                'backend/app/crop_organ_fractional_candidate.py': CODE_SHA256}
    root = Path(__file__).resolve().parents[2]
    actual = {name: sha256((root/name).read_bytes()).hexdigest() for name in expected}
    _need(actual == expected, 'CODE_HOLD: original fractional candidate sources required')
    return actual


def _carbon(y,n):
    return sum((y[0],*y[3:53],*y[106+2*n:]),Fraction(0))


def _physical(p,a,b,t,first,last,latent,n0,points):
    n = len(p['leaves']); ca = F(first['air_capacity']['value'])
    _need(ca == F(last['air_capacity']['value']), 'BALANCE_HOLD: original constant air capacity required')
    cap0,cap1 = (F(view['canopy_capacity']['value']) for view in (first,last))
    du,da,dw = b[103]-a[103],ca*(b[104]-a[104]),b[105]-a[105]
    reference = F(p['scenario']['parameters']['reference_temperature']['value']); lam = F(latent)
    energy = lambda y:y[103]+ca*(y[104]-reference)+lam*y[105]
    return {
        'carbohydrate': ((_carbon(b,n)-_carbon(a,n0),-t['photosynthesis'],*(t[k] for k in
            ('growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon')),
            points.get('growth_respiration',Fraction(0))),_carbon(a,n0),_carbon(b,n),MASS),
        'number': ((sum(b[53:103])-sum(a[53:103]),-t['entry_number'],t['terminal_number']),sum(a[53:103]),sum(b[53:103]),'fruits_equivalent/m2_floor'),
        'canopy_sensible': ((du,-t['canopy_external'],t['sensible'],t['latent'],-t['incoming_heat'],t['outgoing_heat'],-points.get('sensible_in',Fraction(0))),a[103],b[103],'J/m2_floor'),
        'air_sensible': ((da,-t['air_external'],-t['sensible']),ca*(a[104]-reference),ca*(b[104]-reference),'J/m2_floor'),
        'vapor': ((dw,-t['vapor'],-t['external_vapor']),a[105],b[105],'kg_water/m2_floor'),
        'area_capacity': ((cap1-cap0,-t['capacity_in'],t['capacity_out'],-points.get('capacity_in',Fraction(0))),cap0,cap1,'J/m2_floor/K'),
        'reduced_energy': ((du,da,lam*dw,-t['canopy_external'],-t['air_external'],-lam*t['external_vapor'],-t['incoming_heat'],t['outgoing_heat'],-points.get('sensible_in',Fraction(0))),energy(a),energy(b),'J/m2_floor')}


def _local(p,initial,state,transfers,first,last,duration,latent,steps):
    a,b = tuple(map(F,initial)),tuple(map(F,state)); n = len(p['leaves']); m = len(p['stem_root_compartments'])
    t = {name:F(v) for name,v in zip(stock.short._flux_units(p),transfers,strict=True)}
    rows = _physical(p,a,b,t,first,last,latent,n,{})
    for i,leaf in enumerate(p['leaves']):
        rows[f'leaf_age_{i}'] = ((b[106+i]-a[106+i],-t['indoor_air_temperature_time']/86400,F(leaf['base_temperature']['value'])*duration/86400),a[106+i],b[106+i],'degC_day')
    for label,start,count in [('leaf',106+2*n,n),('stem_root',106+3*n,m)]:
        for i in range(count):
            rows[f'{label}_carbon_{i}'] = ((b[start+i]-a[start+i],-t[f'{label}_{i}_inflow'],t[f'{label}_{i}_maintenance'],t[f'{label}_{i}_removal']),a[start+i],b[start+i],MASS)
    rows['stem_root_carbon'] = ((sum(b[106+3*n:])-sum(a[106+3*n:]),
        -sum(t[f'stem_root_{i}_inflow'] for i in range(m)),sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal'] for i in range(m))),sum(a[106+3*n:]),sum(b[106+3*n:]),MASS)
    result = {}
    for name,(terms,start,end,unit) in rows.items():
        residual = sum(terms,Fraction(0)); scale = max(abs(start),abs(end),sum(map(abs,terms),Fraction(0)))
        budget = 64*(steps+1)*F(ulp(old._rounded(scale)))
        _need(abs(residual) <= budget, 'BALANCE_HOLD: exact local fractional '+name)
        result[name] = {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    return result


def _global_rows(context,p,seed,cp,state,lifetime,last,at):
    original,root_seed,_ = stock.parent._context(context._root)
    a,b = tuple(map(F,root_seed['state'])),tuple(map(F,state)); n0 = len(original['leaves']); n = len(p['leaves']); m = len(p['stem_root_compartments'])
    first = stock.short._view(root_seed['evaluation'])['joint']['derived']
    points = {name:F(v['value']) for name,v in cp['point_totals'].items()}
    rows = _physical(p,a,b,lifetime,first,last,context._root._profiles[-1].values['latent_heat'],n0,points)
    dt = F(context.manifest['numerical']['step_seconds'])
    for i,birth in enumerate(seed['birth_bases']['leaf']):
        duration = at-dt*birth['step_index']; _need(duration >= 0, 'TIME_HOLD: pending state precedes an actual leaf point')
        rows[f'leaf_age_{i}'] = ((b[106+i]-F(birth['thermal_age']),-(lifetime['indoor_air_temperature_time']-F(birth['air_temperature_integral'])-F(p['leaves'][i]['base_temperature']['value'])*duration)/86400),Fraction(0),Fraction(0),'degC_day')
    for label,start,bases in [('leaf',106+2*n,seed['birth_bases']['leaf']),('stem_root',106+3*n,seed['birth_bases']['stem_root'])]:
        for i,birth in enumerate(bases):
            rows[f'{label}_carbon_{i}'] = ((b[start+i]-F(birth['carbon']),-lifetime[f'{label}_{i}_inflow'],lifetime[f'{label}_{i}_maintenance'],lifetime[f'{label}_{i}_removal']),Fraction(0),Fraction(0),MASS)
    rows['stem_root_carbon'] = ((sum(b[106+3*n:])-sum(a[106+3*n0:]),
        -sum(lifetime[f'stem_root_{i}_inflow'] for i in range(m)),sum(lifetime[f'stem_root_{i}_maintenance']+lifetime[f'stem_root_{i}_removal'] for i in range(m)),-points['stem_structural_carbon']),Fraction(0),Fraction(0),MASS)
    return rows


def _source_global(context,p,seed,cp):
    lifetime = {name:F(q['value']) for name,q in cp['integrated_transfers'].items()}
    at = interval.clock.stem._fraction(cp['at_elapsed_seconds_exact'])
    rows = _global_rows(context,p,seed,cp,cp['last_confirmed']['state'],lifetime,cp['last_confirmed']['derived'],at)
    result = {}
    _need(set(rows) == set(cp['global_balance_budgets']), 'BALANCE_HOLD: complete original global ledger required')
    for name,(terms,_,_,unit) in rows.items():
        residual = sum(terms,Fraction(0)); budget = F(cp['global_balance_budgets'][name]['value'])
        _need(abs(residual) <= budget, 'GLOBAL_PREFIX_HOLD: exact original global '+name)
        result[name] = {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    return result


def _packet(context,p,seed,cp,source,certificate,state,transfers,rhs,duration,steps):
    first = cp['last_confirmed']['derived']; view = stock.short._view(rhs); last = view['joint']['derived']
    local = _local(p,cp['last_confirmed']['state'],state,transfers,first,last,duration,context._root._profiles[-1].values['latent_heat'],steps)
    partial = {name:stock.numeric._q(v,unit) for (name,unit),v in zip(stock.short._flux_units(p).items(),transfers,strict=True)}
    pending = {name:F(cp['integrated_transfers'][name]['value'])+F(q['value']) for name,q in partial.items()}
    segment = {name:F(cp['segment_integrated_transfers'][name]['value'])+F(q['value']) for name,q in partial.items()}
    at = interval.clock.stem._fraction(cp['at_elapsed_seconds_exact'])+duration
    rows = _global_rows(context,p,seed,cp,state,pending,last,at); global_ledgers = {}
    for name,(terms,_,_,unit) in rows.items():
        residual = sum(terms,Fraction(0)); expected = interval.clock.stem._fraction(source[name]['residual_exact'])+interval.clock.stem._fraction(local[name]['residual_exact'])
        budget = interval.clock.stem._fraction(source[name]['budget_exact'])+interval.clock.stem._fraction(local[name]['budget_exact'])
        _need(residual == expected, 'GLOBAL_COMPOSITION_HOLD: exact source plus local '+name)
        _need(abs(residual) <= budget, 'GLOBAL_BALANCE_HOLD: exact pending fractional '+name)
        global_ledgers[name] = {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    timeline = certificate['source_timeline']; shoot = interval.clock._age(interval.clock.stem._fraction(timeline['age_exact']),pending['indoor_air_temperature_time'],at,timeline['base_temperature']['value'])
    threshold_residual = interval.clock.stem._fraction(shoot)-interval.clock.stem._fraction(timeline['next_threshold_exact'])
    gaps = deepcopy(view['curve_residuals'])
    return {'state':list(state),'derived':deepcopy(last),'curve_residuals':gaps,
        'curve_invariant_changes':[stock.numeric._q(stock.numeric._sum(q['value'],-anchor['value']),'m2') for q,anchor in zip(gaps,seed['anchors'],strict=True)],
        'partial_interval_transfers':partial,'pending_lifetime_transfers_exact':{name:Q(v,partial[name]['unit']) for name,v in pending.items()},
        'pending_segment_transfers_exact':{name:Q(v,partial[name]['unit']) for name,v in segment.items()},
        'local_ledgers':local,'global_ledgers':global_ledgers,'shoot_age_exact':shoot,'shoot_threshold_residual_exact':Q(threshold_residual,'degC_day'),
        'represented_threshold_status':'crossed' if threshold_residual >= 0 else 'not_crossed'}


def _refine(context,p,seed,cp,source,certificate,profiles,duration,count):
    initial = tuple(cp['last_confirmed']['state']); state = initial; totals = (0.,)*len(stock.short._flux_units(p))
    rates,current = stock.short._evaluate(p,state,profiles); step = duration/count
    for i in range(count):
        f1 = stock.short._flux(p,state,current)
        y2 = old._combine(state,(rates,),(Fraction(1),),step/2); k2,r2 = stock.short._evaluate(p,y2,profiles)
        y3 = old._combine(state,(k2,),(Fraction(1),),step/2); k3,r3 = stock.short._evaluate(p,y3,profiles)
        y4 = old._combine(state,(k3,),(Fraction(1),),step); k4,r4 = stock.short._evaluate(p,y4,profiles)
        candidate = old._combine(state,(rates,k2,k3,k4),old.RK4_WEIGHTS,step)
        cumulative = old._combine(totals,(f1,stock.short._flux(p,y2,r2),stock.short._flux(p,y3,r3),stock.short._flux(p,y4,r4)),old.RK4_WEIGHTS,step)
        next_rates,last = stock.short._evaluate(p,candidate,profiles)
        packet = _packet(context,p,seed,cp,source,certificate,candidate,cumulative,last,step*(i+1),i+1)
        state,totals,rates,current = candidate,cumulative,next_rates,last
    return packet


def _coordinates(layout):
    rows = []
    for name in layout['plant']: rows.append({'name':'plant.'+name,'unit':layout['units']['plant'][name]})
    for name in layout['cohort_arrays']:
        rows.extend({'name':f'{name}[{i}]','unit':layout['units']['cohort_arrays'][name]} for i in range(50))
    for name in layout['climate']: rows.append({'name':'climate.'+name,'unit':layout['units']['climate'][name]})
    for block in layout['leaf_blocks']:
        rows.extend({'name':f'leaf.{identifier}.{block}','unit':layout['units']['leaf_blocks'][block]} for identifier in layout['leaf_ids'])
    rows.extend({'name':'stem_root.'+row['compartment_id']+'.carbon','unit':MASS} for row in layout['stem_root_compartments'])
    return rows


def calculate_fractional_shoot_candidate(context,raw_checkpoint,*,expected_sha256,time_tolerance_seconds_exact):
    try:
        pins = _pins(); p,seed,m = stock._context(context); before = interval.clock._snapshot(context)
        certificate = interval.probe_next_shoot_threshold(context,raw_checkpoint,expected_sha256=expected_sha256,time_tolerance_seconds_exact=time_tolerance_seconds_exact)
        _need(certificate['status'] == 'threshold_bracket', 'THRESHOLD_HOLD: actual first threshold bracket required')
        _need(sha256(stock._canonical({k:v for k,v in certificate.items() if k != 'calculation_sha256'})).hexdigest() == certificate['calculation_sha256'], 'HASH_HOLD: original threshold certificate required')
        rows = certificate['stages']; _need([sha256(stock._canonical(row)).hexdigest() for row in rows] == certificate['stage_sha256'], 'HASH_HOLD: actual original stage vectors required')
        cp = stock._parse(raw_checkpoint,expected_sha256,stock.MAX_CHECKPOINT_BYTES)
        source = _source_global(context,p,seed,cp); selected = interval.clock.stem._fraction(certificate['numerical_root_interval']['upper_elapsed_seconds_exact'])
        duration = selected-interval.clock.stem._fraction(cp['at_elapsed_seconds_exact']); dt = interval.clock.stem._fraction(certificate['step_seconds_exact']); theta = duration/dt
        _need(0 < theta <= 1, 'TIME_HOLD: actual crossed-side coordinate within source interval required')
        profiles = stock.parent._profiles(context._root); weights = old._weights(theta)
        state = old._combine(tuple(rows[0]['state']),tuple(row['rates'] for row in rows),weights,dt)
        transfers = old._combine((0.,)*len(rows[0]['flux']),tuple(row['flux'] for row in rows),weights,dt)
        _,rhs = stock.short._evaluate(p,state,profiles)
        dense = _packet(context,p,seed,cp,source,certificate,state,transfers,rhs,duration,1)
        _need(dense['represented_threshold_status'] == 'crossed', 'ROUNDING_HOLD: represented dense air integral has not crossed the source threshold')
        refined = [{'substeps':count,'step_seconds_exact':Q(duration/count,'s'),'rhs_evaluations':4*count+1,
            **_refine(context,p,seed,cp,source,certificate,profiles,duration,count)} for count in REFINEMENTS]
        coordinates = _coordinates(m['state_layout']); _need(len(coordinates) == len(state), 'LAYOUT_HOLD: complete actual state coordinates required')
        full_state = old._combine(tuple(rows[0]['state']),tuple(row['rates'] for row in rows),old._weights(Fraction(1)),dt)
        full_flux = old._combine((0.,)*len(rows[0]['flux']),tuple(row['flux'] for row in rows),old._weights(Fraction(1)),dt)
        endpoint = certificate['unadopted_endpoint']
        comparison = {'state_differences_exact':[Q(F(a)-F(b),q['unit']) for a,b,q in zip(full_state,endpoint['last_confirmed']['state'],coordinates,strict=True)],
            'partial_transfer_differences_exact':{q['name']:Q(F(v)-(F(endpoint['segment_integrated_transfers'][q['name']]['value'])-F(cp['segment_integrated_transfers'][q['name']]['value'])),q['unit']) for q,v in zip(certificate['stage_flux_order'],full_flux,strict=True)},
            'scope':'dense_full_step_minus_original_binary64_endpoint_no_repair'}
        result = {'model_version':VERSION,'code_sha256':CODE_SHA256,'source_code_sha256':pins,'scope':'software_research_only','time_kind':'synthetic_model_clock_not_observation','G0_G4':'not_assessed',
            'claim_scope':'same_exact_time_mixed_state_pending_transfers_local_global_ledgers_and_local_refinement_only',
            'context_sha256':context.root_sha256,'checkpoint_sha256':expected_sha256,'redistribution_authorized':m['redistribution_authorized'],
            'source_root_certificate':certificate,'source_prefix':deepcopy(cp),'source_global_ledgers':source,
            'at':{'time_origin_utc':certificate['crop_selection']['time_origin_utc'],'elapsed_seconds_exact':Q(selected,'s')},
            'partial_interval_seconds_exact':Q(duration,'s'),'selection_policy':'original_cubic_upper_bound_no_threshold_snap',
            'state_layout':deepcopy(m['state_layout']),'state_coordinates':coordinates,'dense_candidate':dense,'refinements':refined,
            'full_step_dense_comparison':comparison,'refinement_method':'shared_stage_RK4_exact_time_round_once_per_combination_v1',
            'refinement_scope':'same_time_local_differences_not_certified_ODE_error_bounds',
            'domain_scope':'selected_dense_state_and_all_refinement_RHS_stages_only',
            'ledger_rule':'exact_source_plus_local_residual_identity_budget_source_plus_original_64_ULP_local',
            'global_prefix_composition':'original_represented_prefix_plus_pending_partial_exact_not_checkpoint',
            'rhs_evaluations':37,'past_intervals_reintegrated':0,'new_internodes':'not_created','schedule_adoption':'not_performed','integrator_checkpoint':None}
        result['calculation_sha256'] = sha256(stock._canonical(result)).hexdigest()
        _need(len(stock._canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB fractional candidate required')
        _need(stock._hash(stock._source(context)) == m['initial_binding_sha256'], 'SOURCE_HOLD: original current source required before return')
        _need(interval.clock._snapshot(context) == before and _pins() == pins, 'SOURCE_HOLD: original context/code required before return')
        return deepcopy(result)
    except FractionalCandidateHold:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise FractionalCandidateHold(str(error)) from None
