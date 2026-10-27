"""Algebraic receipt verification without replay; crop-organ-repeat-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256

from . import crop_organ_successor_point as point

stock, capture, legacy = point.stock, point.capture, point.resume
candidate = legacy.candidate
Q, F, _fraction = legacy.Q, Fraction.from_float, legacy.X
_canonical = stock._canonical


def _need(condition, reason):
    if not condition: raise ValueError(reason)


def _packet(context, data, cp, packet, duration, steps):
    p = data['captured']['program']; y = packet['state']; units = stock.short._flux_units(p)
    stock.arithmetic._closed(packet['partial_interval_transfers'],set(units))
    transfers = tuple(stock.legacy._captured_quantity(packet['partial_interval_transfers'][name],unit) for name,unit in units.items())
    # The quantity checker validates; use the retained numeric values for arithmetic.
    transfers = tuple(packet['partial_interval_transfers'][name]['value'] for name in units)
    at = _fraction(cp['at']['elapsed_seconds_exact'])+duration
    _need(packet['at'] == {'time_origin_utc':data['captured']['simulation_origin_utc'],'elapsed_seconds_exact':Q(at,'s')}, 'TIME_HOLD: exact diagnostic time required')
    local = candidate._local(p,cp['last_confirmed']['state'],y,transfers,cp['last_confirmed']['derived'],packet['derived'],duration,context._source._root._profiles[-1].values['latent_heat'],steps)
    _need(packet['local_ledgers'] == local, 'BALANCE_HOLD: actual local receipt books required')
    prefixes = [('lifetime',cp['lifetime_transfers_exact']),('source_segment',cp['source_segment_transfers_exact'])]
    for label,prefix in prefixes:
        expected = {name:Q(_fraction(prefix[name])+F(q['value']),q['unit']) for name,q in packet['partial_interval_transfers'].items()}
        _need(packet['pending_'+label+'_transfers_exact'] == expected, 'FLOW_HOLD: exact pending '+label)
    branch = {name:Q(F(cp['branch_integrated_transfers'][name]['value'])+F(q['value']),q['unit']) for name,q in packet['partial_interval_transfers'].items()}
    _need(packet['pending_branch_transfers_exact'] == branch, 'FLOW_HOLD: exact pending branch required')
    t = {name:_fraction(q) for name,q in packet['pending_lifetime_transfers_exact'].items()}
    rows = point.candidate._global_rows(context,data,y,t,packet['derived'],at)
    _need(set(rows) == set(local) == set(packet['global_ledgers']) == set(packet['branch_ledgers']), 'BALANCE_HOLD: complete receipt ledgers required')
    for name,(terms,_,_,unit) in rows.items():
        residual = sum(terms,Fraction(0)); expected = _fraction(cp['global_ledgers'][name]['residual_exact'])+_fraction(local[name]['residual_exact'])
        budget = _fraction(cp['global_ledgers'][name]['budget_exact'])+_fraction(local[name]['budget_exact'])
        _need(residual == expected and abs(residual) <= budget and packet['global_ledgers'][name] == {'residual_exact':Q(residual,unit),'budget_exact':Q(budget,unit)}, 'BALANCE_HOLD: direct global receipt '+name)
        r = residual-_fraction(data['captured']['global_ledgers'][name]['residual_exact'])
        b = _fraction(cp['branch_ledgers'][name]['budget_exact'])+_fraction(local[name]['budget_exact'])
        _need(r == _fraction(cp['branch_ledgers'][name]['residual_exact'])+_fraction(local[name]['residual_exact']) and abs(r) <= b
            and packet['branch_ledgers'][name] == {'residual_exact':Q(r,unit),'budget_exact':Q(b,unit)}, 'BALANCE_HOLD: branch receipt '+name)
    timeline = data['point']['before_candidate']['source_root_certificate']['source_timeline']
    age = _fraction(timeline['age_exact'])+(t['indoor_air_temperature_time']-F(float(timeline['base_temperature']['value']))*at)/86400
    residual = age-_fraction(cp['schedule']['next_threshold_exact'])
    _need(packet['shoot_age_exact'] == Q(age,'degC_day') and packet['shoot_threshold_residual_exact'] == Q(residual,'degC_day')
        and packet['represented_threshold_status'] == ('crossed' if residual >= 0 else 'not_crossed'), 'TIME_HOLD: actual receipt air clock required')


def validate(context, data, result, *, first):
    from . import crop_organ_repeat_events as events
    headers = [(result,point.VERSION if first else events.MATERIAL_VERSION,point._pins() if first else events._pins(),point.CODE_SHA256 if first else events.CODE_SHA256),
        (result['before_candidate'],point.candidate.VERSION if first else events.VERSION,point.candidate._pins() if first else events._pins(),point.candidate.CODE_SHA256 if first else events.CODE_SHA256)]
    for row,version,pins,code in headers:
        _need(row['model_version'] == version and row['source_code_sha256'] == pins and row['code_sha256'] == code
            and row['calculation_sha256'] == stock._hash({k:v for k,v in row.items() if k != 'calculation_sha256'}), 'HASH_HOLD: original receipt version/hash/code required')
    p = data['captured']['program']; seed = data['captured']; before = result['before_candidate']; cp = before['source_prefix']; v = result['inputs']
    stock.arithmetic._closed(v,point.FIELDS); point.stem._rights(v['rights'])
    _need(v['schema_version'] == 'individual-organ-successor-material-point-input-v1' and v['origin'] == 'synthetic'
        and v['policy'] == point.POLICY and v['initial_binding_sha256'] == data['source_snapshot']['manifest']['initial_binding_sha256'], 'CONTEXT_HOLD: original receipt input/source required')
    for name in ('input_id','reviewer','parent_internode_id'): stock.short.stock.part._id(v[name])
    _need(result['context_sha256'] == before['context_sha256'] == v['context_sha256'] == context.root_sha256
        and result['checkpoint_sha256'] == before['checkpoint_sha256'] == v['checkpoint_sha256'] == stock._hash(cp)
        and result['input_sha256'] == stock._hash(v) and result['before_candidate_sha256'] == v['candidate_sha256'] == before['calculation_sha256'], 'HASH_HOLD: actual context/checkpoint/input/candidate required')
    event = point._source_event(data,before)
    _need(result['source_event'] == event and type(v['source_threshold_sequence']) is int and v['source_threshold_sequence'] == event['sequence']
        and v['source_threshold_exact'] == event['threshold_exact'] and v['source_event_id'] == event['source_event_id'], 'EVENT_HOLD: actual next logical event required')
    _need(v['parent_internode_id'] in {r['compartment_id'] for r in p['stem_root_compartments'] if r['kind'] == 'internode'}
        and event['internode_id'] not in {r['compartment_id'] for r in p['stem_root_compartments']}, 'EVENT_HOLD: unique new organ and actual current parent required')
    _need(v['model_floor_area'] == p['model_floor_area'] and result['at'] == before['at'] and v['at_elapsed_seconds_exact'] == before['at']['elapsed_seconds_exact'], 'TIME_HOLD: common footprint/exact point required')
    cert = before['source_interval']; stages = cert['stages']; dt = F(seed['original_numerical']['step_seconds'])
    left = _fraction(cp['at']['elapsed_seconds_exact']); step = dt*(cp['grid_index']+1)-left
    _need(cert['step_seconds_exact'] == Q(step,'s') and cert['stages'][0]['state'] == cp['last_confirmed']['state']
        and cert['stage_sha256'] == [stock._hash(row) for row in stages], 'HASH_HOLD: actual shared stages required')
    units = stock.short._flux_units(p)
    _need(cert['stage_flux_order'] == [{'name':name,'unit':unit} for name,unit in units.items()], 'LAYOUT_HOLD: actual stage flux order required')
    for index,factor,previous in [(1,Fraction(1,2),0),(2,Fraction(1,2),1),(3,Fraction(1),2)]:
        expected = candidate.old._combine(tuple(stages[0]['state']),(tuple(stages[previous]['rates']),),(Fraction(1),),step*factor)
        _need(list(expected) == stages[index]['state'], 'STATE_HOLD: shared RK4 stage states required')
    cumulative = candidate.old._combine(tuple(cp['branch_integrated_transfers'][name]['value'] for name in units),tuple(row['flux'] for row in stages),candidate.old.RK4_WEIGHTS,step)
    bracket = legacy._pending_event(data,cp,stages,cumulative,left+step)
    _need(bracket is not None and all(cert[name] == value for name,value in bracket.items()), 'EVENT_HOLD: actual original next-event bracket required')
    coefficients = tuple(_fraction(q) for q in cert['polynomial_coefficients']); root = before['numerical_root_interval']
    tolerance = _fraction(root['time_tolerance_seconds_exact']); _need(root['time_tolerance_seconds_exact']['unit'] == 's','UNIT_HOLD: exact seconds required')
    lo,hi,iterations = candidate.interval.event._root_interval(coefficients,step,tolerance)
    at = left+hi*step; duration = at-left
    expected_root = {'lower_elapsed_seconds_exact':Q(left+lo*step,'s'),'upper_elapsed_seconds_exact':Q(at,'s'),
        'time_tolerance_seconds_exact':deepcopy(root['time_tolerance_seconds_exact']),
        'lower_threshold_residual_exact':Q(candidate.interval.event._value(coefficients,lo),'degC_day'),
        'upper_threshold_residual_exact':Q(candidate.interval.event._value(coefficients,hi),'degC_day'),'bisections':iterations}
    _need(root == expected_root and before['at']['elapsed_seconds_exact'] == Q(at,'s')
        and before['partial_interval_seconds_exact'] == Q(duration,'s'), 'TIME_HOLD: actual original upper-bound candidate required')
    weights = candidate.old._weights(hi); dense = before['dense_candidate']
    y = candidate.old._combine(tuple(stages[0]['state']),tuple(row['rates'] for row in stages),weights,step)
    transfers = candidate.old._combine((0.,)*len(units),tuple(row['flux'] for row in stages),weights,step)
    partial = {name:stock.numeric._q(value,unit) for (name,unit),value in zip(units.items(),transfers,strict=True)}
    _need(dense['state'] == list(y) and dense['partial_interval_transfers'] == partial, 'STATE_HOLD: actual full dense state/transfers required')
    _packet(context,data,cp,dense,duration,1)
    _need(dense['represented_threshold_status'] == 'crossed', 'ROUNDING_HOLD: actual represented threshold crossing required')
    _need([row['substeps'] for row in before['refinements']] == [1,2,4], 'CONTEXT_HOLD: complete original diagnostics required')
    for row in before['refinements']:
        _need(row['step_seconds_exact'] == Q(duration/row['substeps'],'s') and row['rhs_evaluations'] == 4*row['substeps']+1, 'CONTEXT_HOLD: actual partial diagnostic scope required')
        _packet(context,data,cp,row,duration,row['substeps'])
    profiles = stock.parent._profiles(context._source._root); expected = deepcopy(p); n = len(p['leaves'])
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
    _need(result['redistribution_authorized'] is (seed['redistribution_authorized'] and v['rights']['redistribute']),
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
