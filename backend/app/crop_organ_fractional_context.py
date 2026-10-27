"""Immutable material-point capture; crop-organ-fractional-context-v1.md."""
from copy import deepcopy
from dataclasses import dataclass, field
from fractions import Fraction
from functools import wraps
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path

from . import crop_organ_fractional_point as point

stock = point.stock
candidate = point.candidate
clock = candidate.interval.clock
Q = point.Q
F = Fraction.from_float
VERSION = 'individual-organ-fractional-context-research-v1'
CHECKPOINT_VERSION = 'fractional-individual-organ-checkpoint-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
MAX_CHECKPOINT_BYTES = stock.MAX_CHECKPOINT_BYTES
_TOKEN = object()


class FractionalContextHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise FractionalContextHold(reason)


def _public(fn):
    @wraps(fn)
    def checked(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except FractionalContextHold:
            raise
        except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
            raise FractionalContextHold(str(error)) from None
    return checked


def _canonical(value):
    raw = stock._canonical(value)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB fractional context required')
    return raw


def _hash(value):
    return sha256(_canonical(value)).hexdigest()


def _pins():
    pins = {**point._pins(), 'backend/app/crop_organ_fractional_context.py': CODE_SHA256}
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256, 'CODE_HOLD: original fractional context required')
    return pins


def _fraction(q):
    value = clock.stem._fraction(q)
    _need(q == Q(value, q['unit']), 'UNIT_HOLD: canonical exact quantity required')
    return value


def _schedule(result):
    before = result['before_candidate']; timeline = before['source_root_certificate']['source_timeline']
    event = point.source_event(before); age = _fraction(before['dense_candidate']['shoot_age_exact'])
    threshold = _fraction(event['threshold_exact']); spacing = _fraction(timeline['phyllochron_exact'])
    _need(spacing > 0 and threshold <= age < threshold+spacing,
          'PHASE_HOLD: consume only the first source threshold; another due threshold cannot be skipped')
    return {'consumed_event_id': event['source_event_id'], 'consumed_sequence': event['sequence'],
        'consumed_threshold_exact': deepcopy(event['threshold_exact']), 'next_sequence': event['sequence']+1,
        'next_threshold_exact': Q(threshold+spacing, 'degC_day'), 'age_exact': deepcopy(before['dense_candidate']['shoot_age_exact']),
        'source_schedule_id': timeline['schedule_id'], 'policy': 'first_source_event_once_no_threshold_snap',
        'age_basis': 'numerical_air_integral_not_physical_emergence'}


def _bases(source, result, seed, binding):
    dt = F(source.manifest['numerical']['step_seconds']); timeline = binding['stem_selection']['source_state']['timeline_state']
    initial = {node['length_state']['clock_state']['internode_id']: node['length_state']['clock_state']
        for node in binding['stem_selection']['source_state']['internodes']}
    history = {item['compartment_id']: row for row in source.point_history if row['kind'] == 'internode' for item in row['new_items']}
    bases = {'leaf': [], 'stem_root': []}
    for item, base in zip(source.program['leaves'], seed['birth_bases']['leaf'], strict=True):
        bases['leaf'].append({'leaf_id': base['leaf_id'], 'at_elapsed_seconds_exact': Q(dt*base['step_index'], 's'),
            'thermal_age_exact': Q(F(base['thermal_age']), 'degC_day'), 'carbon': stock.numeric._q(base['carbon'], point.MASS),
            'air_temperature_integral_exact': Q(F(base['air_temperature_integral']), 'degC_s'),
            'base_temperature': deepcopy(item['base_temperature']), 'basis_kind': 'original_initial_or_declared_baseline'})
    for base in seed['birth_bases']['stem_root']:
        identifier = base['compartment_id']; row = history.get(identifier)
        age = initial[identifier]['age_exact'] if identifier in initial else Q(Fraction(0), 'degC_day')
        bases['stem_root'].append({'compartment_id': identifier, 'kind': base['kind'],
            'at_elapsed_seconds_exact': Q(dt*base['step_index'], 's'), 'carbon': stock.numeric._q(base['carbon'], point.MASS),
            'air_temperature_integral_exact': Q(F(row['air_temperature_integral']) if row else Fraction(0), 'degC_s'),
            'thermal_age_exact': deepcopy(age) if base['kind'] == 'internode' else None,
            'base_temperature': deepcopy(timeline['base_temperature']) if base['kind'] == 'internode' else None,
            'basis_kind': 'selected_initial_clock' if identifier in initial else 'declared_material_baseline'})
    at = result['at']['elapsed_seconds_exact']; air = result['before_candidate']['dense_candidate']['pending_lifetime_transfers_exact']['indoor_air_temperature_time']
    event = result['source_event']; p = result['after_program']
    bases['stem_root'].append({'compartment_id': event['internode_id'], 'kind': 'internode',
        'at_elapsed_seconds_exact': deepcopy(at), 'carbon': deepcopy(p['stem_root_compartments'][-1]['initial_carbon']),
        'air_temperature_integral_exact': deepcopy(air), 'thermal_age_exact': Q(Fraction(0), 'degC_day'),
        'base_temperature': deepcopy(timeline['base_temperature']), 'basis_kind': 'numerical_material_point_not_physical_emergence'})
    if result['inputs']['leaf'] is not None:
        bases['leaf'].append({'leaf_id': event['leaf_id'], 'at_elapsed_seconds_exact': deepcopy(at),
            'carbon': deepcopy(p['leaves'][-1]['initial_carbon']), 'air_temperature_integral_exact': deepcopy(air),
            'thermal_age_exact': Q(Fraction(0), 'degC_day'), 'base_temperature': deepcopy(p['leaves'][-1]['base_temperature']),
            'basis_kind': 'numerical_material_point_not_physical_emergence'})
    return bases


def _direct_point(source, result, p, seed, binding):
    for row, version, pins, code in [(result, point.VERSION, point._pins(), point.CODE_SHA256),
        (result['before_candidate'], candidate.VERSION, candidate._pins(), candidate.CODE_SHA256)]:
        _need(row['model_version'] == version and row['source_code_sha256'] == pins
            and row['code_sha256'] == code
            and row['calculation_sha256'] == _hash({k:v for k,v in row.items() if k != 'calculation_sha256'}),
            'CONTEXT_HOLD: original captured calculation hash/code required')
    before = result['before_candidate']; cert = before['source_root_certificate']; cp = before['source_prefix']
    v = result['inputs']; point.leaf.arithmetic._closed(v, point.FIELDS); point.stem._rights(v['rights'])
    _need(v['schema_version'] == 'individual-organ-fractional-material-point-input-v1' and v['origin'] == 'synthetic'
        and v['policy'] == point.POLICY and v['initial_binding_sha256'] == source.manifest['initial_binding_sha256'],
        'CONTEXT_HOLD: original point input schema/source required')
    for name in ('input_id', 'reviewer', 'parent_internode_id'): stock.short.stock.part._id(v[name])
    _need(result['input_sha256'] == _hash(v) and result['context_sha256'] == before['context_sha256'] == v['context_sha256'] == source.root_sha256
        and result['checkpoint_sha256'] == before['checkpoint_sha256'] == v['checkpoint_sha256'] == _hash(cp)
        and v['candidate_sha256'] == result['before_candidate_sha256'] == before['calculation_sha256'],
        'CONTEXT_HOLD: actual source context/checkpoint/candidate/input required')
    _need(cert['model_version'] == candidate.interval.VERSION and cert['code_sha256'] == candidate.interval.CODE_SHA256
        and cert['source_code_sha256'] == candidate.interval._pins()
        and cert['source_timeline'] == binding['stem_selection']['source_state']['timeline_state']
        and cert['calculation_sha256'] == _hash({k:v for k,v in cert.items() if k != 'calculation_sha256'})
        and cert['stage_sha256'] == [_hash(row) for row in cert['stages']], 'CONTEXT_HOLD: original source/stages required')
    _need(v['model_floor_area'] == p['model_floor_area'] and result['at'] == before['at']
        and v['at_elapsed_seconds_exact'] == before['at']['elapsed_seconds_exact']
        and result['at']['time_origin_utc'] == binding['crop_selection']['time_origin_utc'], 'TIME_HOLD: actual common floor/origin/point required')
    event = point.source_event(before)
    _need(result['source_event'] == event and type(v['source_threshold_sequence']) is int
        and v['source_threshold_sequence'] == event['sequence'] and v['source_threshold_exact'] == event['threshold_exact']
        and v['source_event_id'] == event['source_event_id'], 'EVENT_HOLD: original first logical event required')
    seen = {e['event_id'] for row in source.point_history for e in row['inputs']['events']}
    _need(not seen.intersection(event[k] for k in ('source_event_id','internode_event_id','leaf_event_id'))
        and v['parent_internode_id'] in {r['compartment_id'] for r in p['stem_root_compartments'] if r['kind'] == 'internode'}
        and event['internode_id'] not in {r['compartment_id'] for r in p['stem_root_compartments']}, 'EVENT_HOLD: unique event/organ and actual parent required')
    dense = before['dense_candidate']; dt = F(source.manifest['numerical']['step_seconds'])
    at = _fraction(result['at']['elapsed_seconds_exact']); left = _fraction(cp['at_elapsed_seconds_exact']); duration = at-left
    _need(type(cp['step_index']) is int and left == cp['step_index']*dt and 0 < duration <= dt
        and cert['stages'][0]['state'] == cp['last_confirmed']['state'], 'TIME_HOLD: original left grid and candidate interval required')
    weights = candidate.old._weights(duration/dt); stages = cert['stages']
    y = candidate.old._combine(tuple(stages[0]['state']), tuple(row['rates'] for row in stages), weights, dt)
    transfers = candidate.old._combine((0.,)*len(stages[0]['flux']), tuple(row['flux'] for row in stages), weights, dt)
    _need(_canonical(list(y)) == _canonical(dense['state']), 'CONTEXT_HOLD: original captured dense state required')
    units = stock.short._flux_units(p)
    partial = {name:stock.numeric._q(value,unit) for (name,unit),value in zip(units.items(),transfers,strict=True)}
    _need(dense['partial_interval_transfers'] == partial, 'CONTEXT_HOLD: original partial transfers required')
    for field, origin in [('pending_lifetime_transfers_exact','integrated_transfers'), ('pending_segment_transfers_exact','segment_integrated_transfers')]:
        _need(dense[field] == {name:Q(F(cp[origin][name]['value'])+F(q['value']),q['unit']) for name,q in partial.items()},
            'CONTEXT_HOLD: original exact prefix plus partial flows required')
    _need(before['partial_interval_seconds_exact'] == Q(duration,'s')
        and before['at']['elapsed_seconds_exact'] == cert['numerical_root_interval']['upper_elapsed_seconds_exact'],
        'TIME_HOLD: captured original crossed-side coordinate required')
    timeline = cert['source_timeline']
    event_math = candidate.interval.event; base = F(float(timeline['base_temperature']['value']))
    left_age = _fraction(timeline['age_exact'])+(F(cp['integrated_transfers']['indoor_air_temperature_time']['value'])-base*left)/86400
    coefficients = event_math._thermal_polynomial(tuple(F(row['state'][104]) for row in stages),dt,base,left_age,_fraction(event['threshold_exact']))
    clock.stem._elapsed(cert['requested_time_tolerance_seconds_exact']); tolerance = _fraction(cert['requested_time_tolerance_seconds_exact'])
    _need(0 < tolerance <= dt and event_math._minimum_derivative(coefficients) > 0,
        'TIME_HOLD: original positive-tolerance increasing source cubic required')
    lo,hi,iterations = event_math._root_interval(coefficients,dt,tolerance)
    root = {'time_origin_utc':result['at']['time_origin_utc'],'lower_elapsed_seconds_exact':Q(left+lo*dt,'s'),
        'upper_elapsed_seconds_exact':Q(left+hi*dt,'s'),'width_seconds_exact':Q((hi-lo)*dt,'s'),
        'lower_thermal_residual_exact':Q(event_math._value(coefficients,lo),'degC_day'),
        'upper_thermal_residual_exact':Q(event_math._value(coefficients,hi),'degC_day')}
    _need(cert['polynomial_coefficients'] == [Q(value,'degC_day') for value in coefficients]
        and cert['numerical_root_interval'] == root and cert['bisections'] == iterations,
        'TIME_HOLD: original captured cubic root certificate required')
    age = clock._age(_fraction(timeline['age_exact']),_fraction(dense['pending_lifetime_transfers_exact']['indoor_air_temperature_time']),at,timeline['base_temperature']['value'])
    _need(dense['shoot_age_exact'] == age and dense['shoot_threshold_residual_exact'] == Q(_fraction(age)-_fraction(event['threshold_exact']),'degC_day'),
        'TIME_HOLD: exact captured source air clock required')
    source_books = candidate._source_global(source,p,seed,cp)
    local = candidate._local(p,cp['last_confirmed']['state'],dense['state'],transfers,cp['last_confirmed']['derived'],
        dense['derived'],duration,source._root._profiles[-1].values['latent_heat'],1)
    rows = candidate._global_rows(source,p,seed,cp,dense['state'],
        {k:_fraction(q) for k,q in dense['pending_lifetime_transfers_exact'].items()},dense['derived'],at)
    expected_books = {}
    for name,(terms,_,_,unit) in rows.items():
        residual = sum(terms,Fraction(0)); expected_residual = _fraction(source_books[name]['residual_exact'])+_fraction(local[name]['residual_exact'])
        budget = _fraction(source_books[name]['budget_exact'])+_fraction(local[name]['budget_exact'])
        _need(residual == expected_residual and abs(residual) <= budget, 'BALANCE_HOLD: original dense composition '+name)
        expected_books[name] = {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    _need(before['source_global_ledgers'] == source_books and dense['local_ledgers'] == local and dense['global_ledgers'] == expected_books,
        'BALANCE_HOLD: captured original exact source/local budgets required')
    profiles = stock.parent._profiles(source._root); expected = deepcopy(p); n = len(p['leaves'])
    item = result['after_program']['stem_root_compartments'][-1]; stock._stem_declaration(item,v['internode'])
    _need(item['compartment_id'] == event['internode_id'], 'EVENT_HOLD: canonical internode required')
    stem_event = {'event_id':event['internode_event_id'],'parent_internode_id':v['parent_internode_id'],'compartment':v['internode']}
    _need(len(result['internode_receipts']) == 1, 'CONTEXT_HOLD: one internode receipt required')
    stock._receipt(result['internode_receipts'][0],stem_event,item,'internode'); expected['stem_root_compartments'].append(item)
    s,r,d,b = stock.arithmetic._fund(y[0],[item['initial_carbon']['value']],point.stem._cost(profiles))
    state = [b,*y[1:],s]; components = {'internode':point._components({'structural':s,'respiration':r,'debit':d},'internode')}
    anchors = deepcopy(seed['anchors']); new_area = None
    if v['leaf'] is not None:
        stock.arithmetic._closed(v['leaf'],{'declaration','incoming_temperature'})
        item = result['after_program']['leaves'][-1]; stock.legacy._leaf_declaration(item,v['leaf']['declaration'])
        _need(item['leaf_id'] == event['leaf_id'] and item['leaf_id'] not in {r['leaf_id'] for r in p['leaves']}, 'EVENT_HOLD: unique canonical leaf required')
        leaf_event = {'event_id':event['leaf_event_id'],'parent_internode_id':event['internode_id'],
            'leaf':v['leaf']['declaration'],'incoming_temperature':v['leaf']['incoming_temperature']}
        _need(len(result['leaf_receipts']) == 1, 'CONTEXT_HOLD: one leaf receipt required')
        receipt = result['leaf_receipts'][0]; stock._receipt(receipt,leaf_event,item,'leaf')
        new_area = receipt['initialization']['state']['area']['value']
        _need(receipt['initialization']['state']['area'] == stock.short.old.leaf_area._area_at(Fraction(0),item['curve']),
            'CONTEXT_HOLD: canonical captured F0 required')
        incoming = stock.arithmetic._quantity(v['leaf']['incoming_temperature'],'degC'); stock.numeric._temperature(incoming)
        params = p['scenario']['parameters']; K = stock.arithmetic._rounded(F(params['leaf_heat_capacity']['value'])*F(new_area)/F(p['model_floor_area']['value']))
        E = stock.arithmetic._rounded(F(K)*(F(incoming)-F(params['reference_temperature']['value'])))
        _need(receipt['capacity_in'] == stock.numeric._q(K,stock.numeric.CAPACITY) and receipt['sensible_in'] == stock.numeric._q(E,stock.numeric.ENERGY),
            'CONTEXT_HOLD: original leaf thermal receipt required')
        s,r,d,b = stock.arithmetic._fund(state[0],[item['initial_carbon']['value']],point.leaf._cost(profiles))
        components['leaf'] = point._components({'structural':s,'respiration':r,'debit':d,'capacity':K,'energy':E},'leaf')
        base = state[:106]; base[0] = b; base[103] = stock.arithmetic._rounded(F(base[103])+F(E))
        state = [*base,*state[106:106+n],0.,*state[106+n:106+2*n],new_area,*state[106+2*n:106+3*n],s,*state[106+3*n:]]
        expected['leaves'].append(item); anchors.append(stock.numeric._q(0.,'m2'))
    else:
        _need(result['leaf_receipts'] == [], 'CONTEXT_HOLD: no absent-leaf receipts required')
    _need(_canonical(result['after_program']) == _canonical(expected) and _canonical(result['after_state']) == _canonical(state)
        and result['flow_components'] == components and result['after_anchors'] == anchors
        and result['after_state_layout'] == stock.short._layout(expected), 'CONTEXT_HOLD: direct point state/flow/program/anchors required')
    _need(len(expected['leaves']) <= 512 and len(expected['stem_root_compartments']) <= 512,
        'CAPACITY_HOLD: bounded actual inventories required')
    _need(result['redistribution_authorized'] is (source.manifest['redistribution_authorized'] and v['rights']['redistribute']),
        'RIGHTS_HOLD: current source and point rights required')
    exact_flows = {name:sum((F(row[name]['value']) for row in components.values()),Fraction(0)) for name in stock.FLOW_UNITS}
    _need(result['point_flows_exact'] == {name:Q(value,stock.FLOW_UNITS[name]) for name,value in exact_flows.items()}
        and result['point_flows'] == {name:stock.numeric._q(stock.arithmetic._rounded(value),stock.FLOW_UNITS[name]) for name,value in exact_flows.items()},
        'CONTEXT_HOLD: original sequential flow components and exact totals required')
    a,b = tuple(map(F,y)),tuple(map(F,state)); nn = len(expected['leaves']); last = result['after_derived']
    Ca = F(dense['derived']['air_capacity']['value']); ref = F(p['scenario']['parameters']['reference_temperature']['value'])
    _need(F(last['air_capacity']['value']) == Ca, 'CONTEXT_HOLD: constant air capacity required')
    lam = F(profiles['exchange_profile'].values['latent_heat']); energy = lambda z:z[103]+Ca*(z[104]-ref)+lam*z[105]
    terms = {'buffer':([b[0],-a[0],*(F(q['buffer_debit']['value']) for q in components.values())],point.MASS),
        'whole_carbohydrate':([candidate._carbon(b,nn),-candidate._carbon(a,n),*(F(q['growth_respiration']['value']) for q in components.values())],point.MASS),
        'new_internode':([b[-1],-F(components['internode']['structural_carbon']['value'])],point.MASS),
        'stem_root_carbon':([sum(b[106+3*nn:]),-sum(a[106+3*n:]),-F(components['internode']['structural_carbon']['value'])],point.MASS),
        'capacity':([F(last['canopy_capacity']['value']),-F(dense['derived']['canopy_capacity']['value']),-exact_flows['capacity_in']],stock.numeric.CAPACITY),
        'canopy_sensible':([b[103],-a[103],-exact_flows['sensible_in']],stock.numeric.ENERGY),
        'air_sensible':([Ca*b[104],-Ca*a[104]],stock.numeric.ENERGY),'vapor':([b[105],-a[105]],'kg_water/m2_floor'),
        'fruit_number':([sum(b[53:103]),-sum(a[53:103])],'fruits_equivalent/m2_floor'),
        'reduced_energy':([energy(b),-energy(a),-exact_flows['sensible_in']],stock.numeric.ENERGY)}
    if v['leaf'] is not None: terms['new_leaf'] = ([b[106+2*nn+n],-F(components['leaf']['structural_carbon']['value'])],point.MASS)
    _need(result['point_balances'] == {name:point._balance(values,unit) for name,(values,unit) in terms.items()},
        'BALANCE_HOLD: original exact point residuals and ULP budgets required')
    costs = {'cStemG':point.stem._cost(profiles),**({'cLeafG':point.leaf._cost(profiles)} if v['leaf'] is not None else {}),
        'unit':'mg_CH2O/mg_CH2O','profile_sha256':profiles['growth_profile'].sha256}
    _need(result['growth_costs'] == costs and result['point_order'] == list(components)
        and result['after_curve_residuals'] == [*dense['curve_residuals'],*([stock.numeric._q(0.,'m2')] if v['leaf'] is not None else [])]
        and result['after_curve_invariant_changes'] == [*dense['curve_invariant_changes'],*([stock.numeric._q(0.,'m2')] if v['leaf'] is not None else [])],
        'CONTEXT_HOLD: original costs, curve residuals and point order required')
    _need(result['scope'] == 'software_research_only' and result['G0_G4'] == 'not_assessed'
        and result['time_kind'] == 'synthetic_model_clock_not_observation' and result['schedule_adoption'] == 'not_performed'
        and result['integrator_checkpoint'] is None and result['elapsed_seconds_advanced'] == Q(Fraction(0),'s'),
        'SCOPE_HOLD: original research-only point capture required')
    return at, dt, cp


def _global(source, result, bases, pending, points, at):
    p = result['after_program']; n = len(p['leaves']); b = tuple(map(F,result['after_state']))
    original, root_seed, _ = stock.parent._context(source._root); n0 = len(original['leaves'])
    a = tuple(map(F,root_seed['state'])); first = stock.short._view(root_seed['evaluation'])['joint']['derived']
    t = {name:_fraction(q) for name,q in pending.items()}; latent = source._root._profiles[-1].values['latent_heat']
    rows = candidate._physical(p,a,b,t,first,result['after_derived'],latent,n0,{k:_fraction(v) for k,v in points.items()})
    for i,base in enumerate(bases['leaf']):
        duration = at-_fraction(base['at_elapsed_seconds_exact'])
        _need(duration >= 0, 'TIME_HOLD: current point cannot precede any organ baseline')
        terms = (b[106+i]-_fraction(base['thermal_age_exact']),
            -(t['indoor_air_temperature_time']-_fraction(base['air_temperature_integral_exact'])-F(base['base_temperature']['value'])*duration)/86400)
        rows['leaf_age_'+str(i)] = (terms,Fraction(0),Fraction(0),'degC_day')
    for label,start in [('leaf',106+2*n),('stem_root',106+3*n)]:
        for i,base in enumerate(bases[label]):
            terms = (b[start+i]-F(base['carbon']['value']),-t[f'{label}_{i}_inflow'],t[f'{label}_{i}_maintenance'],t[f'{label}_{i}_removal'])
            rows[f'{label}_carbon_{i}'] = (terms,Fraction(0),Fraction(0),point.MASS)
    m = len(p['stem_root_compartments'])
    rows['stem_root_carbon'] = ((sum(b[106+3*n:])-sum(a[106+3*n0:]),
        -sum(t[f'stem_root_{i}_inflow'] for i in range(m)),
        sum(t[f'stem_root_{i}_maintenance']+t[f'stem_root_{i}_removal'] for i in range(m)),
        -_fraction(points['stem_structural_carbon'])),Fraction(0),Fraction(0),point.MASS)
    before = result['before_candidate']['dense_candidate']['global_ledgers']; point_rows = result['point_balances']
    additions = {'carbohydrate':'whole_carbohydrate','number':'fruit_number','canopy_sensible':'canopy_sensible',
        'air_sensible':'air_sensible','vapor':'vapor','area_capacity':'capacity','reduced_energy':'reduced_energy',
        'stem_root_carbon':'stem_root_carbon',f'stem_root_carbon_{m-1}':'new_internode'}
    if result['inputs']['leaf'] is not None: additions[f'leaf_carbon_{n-1}'] = 'new_leaf'
    ledgers = {}
    for name,(terms,_,_,unit) in rows.items():
        residual = sum(terms,Fraction(0)); old = before.get(name); new = point_rows.get(additions.get(name))
        expected = sum((_fraction(row['residual_exact']) for row in (old,new) if row is not None),Fraction(0))
        budget = sum((_fraction(row['budget_exact']) for row in (old,new) if row is not None),Fraction(0))
        _need(residual == expected and abs(residual) <= budget, 'BALANCE_HOLD: exact captured source/local/point '+name)
        ledgers[name] = {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}
    return ledgers


def _captured(source, result):
    p, seed, manifest = stock._context(source); binding = stock._source(source)
    at, dt, cp = _direct_point(source,result,p,seed,binding)
    after = result['after_program']; n = len(after['leaves']); m = len(after['stem_root_compartments'])
    state = result['after_state']; _need(type(state) is list and len(state) == 106+3*n+m
        and all(type(v) is float and isfinite(v) for v in state), 'STATE_HOLD: finite captured binary64 state required')
    schedule = _schedule(result); bases = _bases(source,result,seed,binding); dense = result['before_candidate']['dense_candidate']
    units = stock.short._flux_units(after)
    pending = {name:deepcopy(dense['pending_lifetime_transfers_exact'].get(name,Q(Fraction(0),unit))) for name,unit in units.items()}
    segment = {name:deepcopy(dense['pending_segment_transfers_exact'].get(name,Q(Fraction(0),unit))) for name,unit in units.items()}
    points = {name:Q(F(q['value']),q['unit']) for name,q in cp['point_totals'].items()}
    for kind, part in result['flow_components'].items():
        for name,q in part.items(): points[name] = Q(_fraction(points[name])+F(q['value']),q['unit'])
        name = ('stem' if kind == 'internode' else 'leaf')+'_structural_carbon'
        points[name] = Q(_fraction(points[name])+F(part['structural_carbon']['value']),point.MASS)
    completed = int(at//dt); count = manifest['numerical']['step_count']
    _need(0 <= completed <= count and at <= dt*count, 'TIME_HOLD: actual original grid horizon required')
    remaining = count-completed
    _need((remaining+1)*(len(state)+2*n+9) <= 32768, 'CAPACITY_HOLD: original remaining sample scalar budget required')
    next_at = dt*(completed+1) if completed < count else None
    timeline = binding['stem_selection']['source_state']['timeline_state']
    return {'source_context_sha256':source.root_sha256,'source_checkpoint_sha256':result['checkpoint_sha256'],
        'program':deepcopy(after),'anchors':deepcopy(result['after_anchors']),'state_layout':stock.short._layout(after),
        'birth_bases':bases,'schedule':schedule,'at':deepcopy(result['at']),
        'simulation_origin_utc':binding['crop_selection']['time_origin_utc'],'development_origin_utc':timeline['started_at'],
        'original_numerical':deepcopy(manifest['numerical']),
        'original_grid_position':{'source_left_index':cp['step_index'],'completed_grid_index':completed,
            'step_seconds_exact':Q(dt,'s'),'partial_interval_seconds_exact':Q(at-dt*cp['step_index'],'s'),
            'next_grid_index':completed+1 if next_at is not None else None,
            'next_grid_elapsed_seconds_exact':Q(next_at,'s') if next_at is not None else None,
            'remaining_to_next_grid_seconds_exact':Q(next_at-at if next_at is not None else Fraction(0),'s')},
        'pending_lifetime_transfers_exact':pending,'pending_source_segment_transfers_exact':segment,
        'source_point_totals':deepcopy(cp['point_totals']),'new_point_components':deepcopy(result['flow_components']),
        'point_totals_exact':points,'global_ledgers':_global(source,result,bases,pending,points,at),
        'redistribution_authorized':result['redistribution_authorized']}


@dataclass(frozen=True)
class Context:
    _source: stock.Context = field(repr=False)
    _raw: bytes = field(repr=False)
    root_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _fence(context, data):
    _need(context._token is _TOKEN and _canonical(data) == context._raw and _hash(data) == context.root_sha256
        and stock.context_bytes(context._source) == _canonical(data['source_snapshot']),
        'SOURCE_HOLD: original context/source/rights/profile required before return')
    _need(_pins() == data['source_code_sha256'], 'CODE_HOLD: original fractional capture dependencies required before return')


def _context(context):
    _need(type(context) is Context and context._token is _TOKEN, 'CONTEXT_HOLD: prepared fractional context required')
    pins = _pins(); data = stock._parse(context._raw,context.root_sha256,MAX_BYTES)
    stock.arithmetic._closed(data,{'version','source_code_sha256','source_snapshot','source_snapshot_sha256','point','captured'})
    snapshot = stock.context_bytes(context._source)
    _need(data['version'] == VERSION and data['source_code_sha256'] == pins and _hash(data['source_snapshot']) == data['source_snapshot_sha256']
        and _canonical(data['source_snapshot']) == snapshot, 'CONTEXT_HOLD: original source snapshot/code required')
    _need(_canonical(data['captured']) == _canonical(_captured(context._source,data['point'])),
        'CONTEXT_HOLD: original captured state/time/bases/schedule/flows/ledgers required')
    _fence(context,data)
    return data


@_public
def prepare_context(source_context, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact, inputs):
    pins = _pins(); snapshot = stock.context_bytes(source_context)
    result = point.apply_fractional_material_point(source_context,raw_checkpoint,expected_sha256=expected_sha256,
        time_tolerance_seconds_exact=time_tolerance_seconds_exact,inputs=inputs)
    data = {'version':VERSION,'source_code_sha256':pins,'source_snapshot':json.loads(snapshot),
        'source_snapshot_sha256':sha256(snapshot).hexdigest(),'point':result,'captured':_captured(source_context,result)}
    raw = _canonical(data); context = Context(source_context,raw,sha256(raw).hexdigest(),_TOKEN)
    _context(context); return context


@_public
def context_bytes(context):
    _context(context); return context._raw


@_public
def restore_context(*, root_context, raw_bytes, expected_sha256, crop_directory, stem_directory, access):
    data = stock._parse(raw_bytes,expected_sha256,MAX_BYTES)
    source = stock.restore_context(root_context=root_context,raw_bytes=_canonical(data['source_snapshot']),
        expected_sha256=data['source_snapshot_sha256'],crop_directory=crop_directory,stem_directory=stem_directory,access=access)
    context = Context(source,raw_bytes,expected_sha256,_TOKEN); _context(context); return context


@dataclass(frozen=True)
class Checkpoint:
    _raw: bytes = field(repr=False)
    sha256: str
    context_sha256: str
    _token: object = field(repr=False)

    @property
    def value(self): return json.loads(self._raw)


def _sample(point_result, before=False):
    if before:
        dense = point_result['before_candidate']['dense_candidate']
        return {'at':deepcopy(point_result['at']),**{name:deepcopy(dense[name]) for name in
            ('state','derived','curve_residuals','curve_invariant_changes')}}
    return {'at':deepcopy(point_result['at']),**{name:deepcopy(point_result['after_'+name]) for name in
        ('state','derived','curve_residuals','curve_invariant_changes')}}


def _initial(context, data):
    point_result = data['point']; saved = data['captured']; cp = point_result['before_candidate']['source_prefix']
    sequence = cp['event_sequence']+1; before = _sample(point_result,True); after = _sample(point_result)
    prefix = stock._prefix(cp['output_prefix_sha256'],before,cp['event_sequence'],'fractional_before_material_point')
    prefix = stock._prefix(prefix,after,sequence,'fractional_after_material_point')
    return {'version':CHECKPOINT_VERSION,'context_sha256':context.root_sha256,'at':deepcopy(saved['at']),
        'phase':'fractional_after_material_point','event_sequence':sequence,'schedule':deepcopy(saved['schedule']),
        'original_grid_position':deepcopy(saved['original_grid_position']),'last_confirmed':after,
        'output_cursor':cp['output_cursor']+2,'output_prefix_sha256':prefix,'branch_steps':0,
        'branch_integrated_transfers_exact':{name:Q(Fraction(0),unit) for name,unit in stock.short._flux_units(saved['program']).items()},
        **{name:deepcopy(saved[name]) for name in ('pending_lifetime_transfers_exact','pending_source_segment_transfers_exact','point_totals_exact','global_ledgers')},
        'scope':'software_research_only','G0_G4':'not_assessed','time_kind':'synthetic_model_clock_not_observation',
        'redistribution_authorized':saved['redistribution_authorized']}


def _seal(context, payload):
    raw = _canonical(payload)
    _need(len(raw) <= MAX_CHECKPOINT_BYTES, 'CAPACITY_HOLD: bounded 512KiB fractional checkpoint required')
    data = _context(context)
    _need(raw == _canonical(_initial(context,data)), 'CHECKPOINT_HOLD: original captured checkpoint required')
    _fence(context,data)
    return Checkpoint(raw,sha256(raw).hexdigest(),context.root_sha256,_TOKEN)


@_public
def start(context):
    return _seal(context,_initial(context,_context(context)))


@_public
def checkpoint_bytes(context, checkpoint):
    data = _context(context)
    _need(type(checkpoint) is Checkpoint and checkpoint._token is _TOKEN and checkpoint.context_sha256 == context.root_sha256
        and type(checkpoint._raw) is bytes and len(checkpoint._raw) <= MAX_CHECKPOINT_BYTES
        and sha256(checkpoint._raw).hexdigest() == checkpoint.sha256, 'CHECKPOINT_HOLD: matching immutable fractional checkpoint required')
    _need(checkpoint._raw == _canonical(_initial(context,data)), 'CHECKPOINT_HOLD: original captured fractional payload required')
    _fence(context,data)
    return checkpoint._raw


@_public
def restore_checkpoint(context, raw_bytes, *, expected_sha256):
    data = _context(context); payload = stock._parse(raw_bytes,expected_sha256,MAX_CHECKPOINT_BYTES)
    _need(_canonical(payload) == _canonical(_initial(context,data)), 'CHECKPOINT_HOLD: exact captured fractional checkpoint required')
    p = data['captured']['program']; y = tuple(payload['last_confirmed']['state']); profiles = stock.parent._profiles(context._source._root)
    rates, rhs = stock.short._evaluate(p,y,profiles); view = stock.short._view(rhs)
    point_result = data['point']
    _need(list(rates) == point_result['after_rates'] and view['joint']['derived'] == point_result['after_derived']
        and view['curve_residuals'] == point_result['after_curve_residuals'], 'CHECKPOINT_HOLD: actual current RHS/sample required')
    _context(context)
    return _seal(context,payload)
