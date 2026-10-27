"""Current-prefix successor candidates; crop-organ-successor-candidate-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json

from . import crop_organ_repeat as resume

capture, stock, candidate = resume.capture, resume.stock, resume.candidate
old, event = candidate.old, candidate.interval.event
Q, X, F = resume.Q, resume.X, Fraction.from_float
VERSION = 'individual-organ-repeat-candidate-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2


class RepeatEventHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise RepeatEventHold(reason)


def _canonical(value):
    raw = stock._canonical(value)
    _need(len(raw) <= MAX_BYTES, 'CAPACITY_HOLD: bounded repeated-event input/output required')
    return raw


def _pins():
    pins = {**resume._pins(), 'backend/app/crop_organ_repeat_events.py': CODE_SHA256}
    _need(sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256,
        'CODE_HOLD: original successor candidate required')
    return pins


def _global_rows(context, data, state, lifetime, last, at):
    saved = data['captured']; p = saved['program']
    original, seed, _ = stock.parent._context(context._source._root)
    a, b = tuple(map(F, seed['state'])), tuple(map(F, state))
    n0, n, m = len(original['leaves']), len(p['leaves']), len(p['stem_root_compartments'])
    first = stock.short._view(seed['evaluation'])['joint']['derived']
    points = {name: X(q) for name, q in saved['point_totals_exact'].items()}
    latent = context._source._root._profiles[-1].values['latent_heat']
    rows = candidate._physical(p, a, b, lifetime, first, last, latent, n0, points)
    for i, base in enumerate(saved['birth_bases']['leaf']):
        elapsed = at-X(base['at_elapsed_seconds_exact'])
        _need(elapsed >= 0, 'TIME_HOLD: successor precedes actual leaf baseline')
        terms = (b[106+i]-X(base['thermal_age_exact']),
            -(lifetime['indoor_air_temperature_time']-X(base['air_temperature_integral_exact'])
              -F(base['base_temperature']['value'])*elapsed)/86400)
        rows[f'leaf_age_{i}'] = (terms, Fraction(0), Fraction(0), 'degC_day')
    for label, start in [('leaf', 106+2*n), ('stem_root', 106+3*n)]:
        for i, base in enumerate(saved['birth_bases'][label]):
            terms = (b[start+i]-F(base['carbon']['value']), -lifetime[f'{label}_{i}_inflow'],
                lifetime[f'{label}_{i}_maintenance'], lifetime[f'{label}_{i}_removal'])
            rows[f'{label}_carbon_{i}'] = (terms, Fraction(0), Fraction(0), candidate.MASS)
    rows['stem_root_carbon'] = ((sum(b[106+3*n:])-sum(a[106+3*n0:]),
        -sum(lifetime[f'stem_root_{i}_inflow'] for i in range(m)),
        sum(lifetime[f'stem_root_{i}_maintenance']+lifetime[f'stem_root_{i}_removal'] for i in range(m)),
        -points['stem_structural_carbon']), Fraction(0), Fraction(0), candidate.MASS)
    return rows


def _packet(context, data, cp, state, transfers, rhs, duration, steps):
    saved = data['captured']; p = saved['program']; at = X(cp['at']['elapsed_seconds_exact'])+duration
    sample = resume._sample(data, at, state, rhs)
    latent = context._source._root._profiles[-1].values['latent_heat']
    local = candidate._local(p, cp['last_confirmed']['state'], state, transfers,
        cp['last_confirmed']['derived'], sample['derived'], duration, latent, steps)
    partial = {name: stock.numeric._q(v, unit) for (name, unit), v in
        zip(stock.short._flux_units(p).items(), transfers, strict=True)}
    pending = {}
    for target, prefix in [('lifetime', cp['lifetime_transfers_exact']),
            ('source_segment', cp['source_segment_transfers_exact'])]:
        pending[target] = {name: Q(X(prefix[name])+F(q['value']), q['unit']) for name, q in partial.items()}
    pending['branch'] = {name: Q(F(cp['branch_integrated_transfers'][name]['value'])+F(q['value']), q['unit'])
        for name, q in partial.items()}
    rows = _global_rows(context, data, state, {name: X(q) for name, q in pending['lifetime'].items()}, sample['derived'], at)
    _need(set(rows) == set(local) == set(cp['global_ledgers']) == set(cp['branch_ledgers']),
        'BALANCE_HOLD: complete current and pending ledger inventory required')
    global_books, branch_books = {}, {}
    for name, (terms, _, _, unit) in rows.items():
        residual = sum(terms, Fraction(0))
        expected = X(cp['global_ledgers'][name]['residual_exact'])+X(local[name]['residual_exact'])
        budget = X(cp['global_ledgers'][name]['budget_exact'])+X(local[name]['budget_exact'])
        _need(residual == expected and abs(residual) <= budget,
            'GLOBAL_COMPOSITION_HOLD: exact current plus local '+name)
        global_books[name] = {'residual_exact': Q(residual, unit), 'budget_exact': Q(budget, unit)}
        branch_residual = residual-X(saved['global_ledgers'][name]['residual_exact'])
        branch_expected = X(cp['branch_ledgers'][name]['residual_exact'])+X(local[name]['residual_exact'])
        branch_budget = X(cp['branch_ledgers'][name]['budget_exact'])+X(local[name]['budget_exact'])
        _need(branch_residual == branch_expected and abs(branch_residual) <= branch_budget,
            'BRANCH_COMPOSITION_HOLD: exact current branch plus local '+name)
        branch_books[name] = {'residual_exact': Q(branch_residual, unit), 'budget_exact': Q(branch_budget, unit)}
    timeline = data['point']['before_candidate']['source_root_certificate']['source_timeline']
    age = X(timeline['age_exact'])+(X(pending['lifetime']['indoor_air_temperature_time'])
        -F(float(timeline['base_temperature']['value']))*at)/86400
    residual = age-X(cp['schedule']['next_threshold_exact'])
    return {**sample, 'partial_interval_transfers': partial,
        **{'pending_'+name+'_transfers_exact': value for name, value in pending.items()},
        'local_ledgers': local, 'branch_ledgers': branch_books, 'global_ledgers': global_books,
        'shoot_age_exact': Q(age, 'degC_day'), 'shoot_threshold_residual_exact': Q(residual, 'degC_day'),
        'represented_threshold_status': 'crossed' if residual >= 0 else 'not_crossed'}


def _refine(context, data, cp, profiles, duration, count):
    p = data['captured']['program']; state = tuple(cp['last_confirmed']['state'])
    totals = (0.,)*len(stock.short._flux_units(p)); rates, rhs = stock.short._evaluate(p, state, profiles)
    progress = {'stage': 'initial', 'new_RHS_evaluations': 0}
    for i in range(count):
        state, totals, rates, rhs, _ = resume._step(p, state, totals, rates, rhs, profiles, duration/count, progress)
        packet = _packet(context, data, cp, state, totals, rhs, duration*(i+1)/count, i+1)
    return {'substeps': count, 'step_seconds_exact': Q(duration/count, 's'),
        'rhs_evaluations': 1+progress['new_RHS_evaluations'], **packet}


def calculate_candidate(context, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact):
    try:
        pins = _pins(); data = resume._context(context); saved = data['captured']; p = saved['program']
        cp = stock._parse(raw_checkpoint, expected_sha256, resume.MAX_CHECKPOINT_BYTES)
        tolerance = X(time_tolerance_seconds_exact)
        _need(time_tolerance_seconds_exact['unit'] == 's', 'TOLERANCE_HOLD: exact seconds required')
        at = X(cp['at']['elapsed_seconds_exact']); dt = F(saved['original_numerical']['step_seconds'])
        _need(at < dt*saved['original_numerical']['step_count'], 'COMPLETED_HOLD: original horizon exhausted')
        step = dt*(cp['grid_index']+1)-at
        _need(0 < tolerance <= step, 'TOLERANCE_HOLD: positive tolerance within actual interval required')
        state, totals, rates, rhs = resume._validate(context, data, cp)
        profiles = stock.parent._profiles(context._source._root)
        progress = {'stage': 'initial', 'new_RHS_evaluations': 0}
        endpoint, cumulative, _, _, rows = resume._step(p, state, totals, rates, rhs, profiles, step, progress)
        bracket = resume._pending_event(data, cp, rows, cumulative, at+step)
        _need(bracket is not None, 'THRESHOLD_HOLD: actual next unconsumed threshold bracket required')
        coefficients = tuple(X(q) for q in bracket['polynomial_coefficients'])
        lower, upper, iterations = event._root_interval(coefficients, step, tolerance)
        duration = step*upper; selected = at+duration; weights = old._weights(upper)
        y = old._combine(state, tuple(row['rates'] for row in rows), weights, step)
        partial = old._combine((0.,)*len(rows[0]['flux']), tuple(row['flux'] for row in rows), weights, step)
        _, dense_rhs = stock.short._evaluate(p, y, profiles)
        dense = _packet(context, data, cp, y, partial, dense_rhs, duration, 1)
        _need(dense['represented_threshold_status'] == 'crossed',
            'ROUNDING_HOLD: represented successor air integral has not crossed')
        refinements = [_refine(context, data, cp, profiles, duration, count) for count in (1, 2, 4)]
        coordinates = candidate._coordinates(saved['state_layout'])
        _need(len(coordinates) == len(y), 'LAYOUT_HOLD: complete actual successor state required')
        root = {'lower_elapsed_seconds_exact': Q(at+step*lower, 's'),
            'upper_elapsed_seconds_exact': Q(selected, 's'), 'time_tolerance_seconds_exact': deepcopy(time_tolerance_seconds_exact),
            'lower_threshold_residual_exact': Q(event._value(coefficients, lower), 'degC_day'),
            'upper_threshold_residual_exact': Q(event._value(coefficients, upper), 'degC_day'), 'bisections': iterations}
        result = {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'source_code_sha256': pins,
            'scope': 'software_research_only', 'time_kind': 'synthetic_model_clock_not_observation', 'G0_G4': 'not_assessed',
            'context_sha256': context.root_sha256, 'checkpoint_sha256': expected_sha256,
            'redistribution_authorized': saved['redistribution_authorized'], 'source_prefix': deepcopy(cp),
            'source_interval': {**bracket, 'stage_sha256': [stock._hash(row) for row in rows],
                'step_seconds_exact': Q(step, 's'),
                'stage_flux_order': [{'name': name, 'unit': unit} for name, unit in stock.short._flux_units(p).items()]},
            'numerical_root_interval': root, 'at': {'time_origin_utc': saved['simulation_origin_utc'],
                'elapsed_seconds_exact': Q(selected, 's')}, 'development_origin_utc': saved['development_origin_utc'],
            'partial_interval_seconds_exact': Q(duration, 's'), 'state_layout': deepcopy(saved['state_layout']),
            'state_coordinates': coordinates, 'dense_candidate': dense, 'refinements': refinements,
            'unadopted_original_endpoint_state': list(endpoint),
            'selection_policy': 'original_cubic_upper_bound_no_threshold_snap',
            'refinement_scope': 'same_time_local_differences_not_certified_ODE_error_bounds',
            'ledger_rule': 'exact_current_plus_local_residual_and_original_budget_sum',
            'rhs_evaluations': 6+sum(row['rhs_evaluations'] for row in refinements),
            'past_intervals_reintegrated': 0, 'schedule_consumed': False, 'new_organs_created': False,
            'integrator_checkpoint': None}
        result['calculation_sha256'] = stock._hash(result)
        _need(len(stock._canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB successor candidate required')
        resume._fence(context, data)
        _need(_pins() == pins, 'CODE_HOLD: original successor sources required before return')
        return deepcopy(result)
    except RepeatEventHold:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise RepeatEventHold(str(error)) from None


from . import crop_organ_successor_point as first_material
stem, leaf, point = stock.stem, stock.leaf, first_material.point
MASS, POLICY, FIELDS = first_material.MASS, first_material.POLICY, first_material.FIELDS
MATERIAL_VERSION = 'individual-organ-repeat-material-point-research-v1'
_source_event = first_material._source_event
_balance, _components = first_material._balance, first_material._components


def apply_material_point(context,raw_checkpoint,*,expected_sha256,time_tolerance_seconds_exact,inputs):
    try:
        pins = _pins(); leaf.arithmetic._closed(inputs,FIELDS); raw = _canonical(inputs); v = json.loads(raw)
        data = resume._context(context); saved = data['captured']; p = saved['program']
        for name in ('input_id','reviewer','parent_internode_id'):stock.short.stock.part._id(v[name])
        stem._rights(v['rights'])
        _need(v['schema_version'] == 'individual-organ-successor-material-point-input-v1' and v['origin'] == 'synthetic' and v['policy'] == POLICY,
              'POLICY_HOLD: explicit source-bound synthetic material point required')
        for name in ('context_sha256','checkpoint_sha256','candidate_sha256','initial_binding_sha256'):
            _need(stock.parent._digest(v[name]), 'HASH_HOLD: explicit canonical '+name+' required')
        _need(v['context_sha256'] == context.root_sha256 and v['checkpoint_sha256'] == expected_sha256,
              'HASH_HOLD: original current context/checkpoint required')
        _need(leaf.arithmetic._quantity(v['model_floor_area'],'m2_floor') == p['model_floor_area']['value'],
              'BASIS_HOLD: original common declared footprint required')
        tolerance = deepcopy(time_tolerance_seconds_exact)
        calculation = calculate_candidate(context,raw_checkpoint,expected_sha256=expected_sha256,time_tolerance_seconds_exact=tolerance)
        _need(v['candidate_sha256'] == calculation['calculation_sha256'] and v['initial_binding_sha256'] == data['source_snapshot']['manifest']['initial_binding_sha256'],
              'HASH_HOLD: actual complete fractional candidate/source required')
        resume.X(v['at_elapsed_seconds_exact'])
        _need(v['at_elapsed_seconds_exact'] == calculation['at']['elapsed_seconds_exact'], 'TIME_HOLD: actual candidate exact time required')
        event = _source_event(data,calculation)
        _need(type(v['source_threshold_sequence']) is int and v['source_threshold_sequence'] == event['sequence']
              and v['source_threshold_exact'] == event['threshold_exact'] and v['source_event_id'] == event['source_event_id'],
              'EVENT_HOLD: original next source threshold/schedule/sequence required')
        past = {e['event_id'] for row in data['source_snapshot']['history'] for e in row['inputs']['events']}
        past.update(data['point']['source_event'][k] for k in ('source_event_id','internode_event_id','leaf_event_id'))
        _need(not past.intersection(event[k] for k in ('source_event_id','internode_event_id','leaf_event_id')),
              'EVENT_HOLD: logical source event already present in original history')
        _need(v['internode']['compartment_id'] == event['internode_id'], 'EVENT_HOLD: original canonical source internode ID required')
        parents = {row['compartment_id'] for row in p['stem_root_compartments'] if row['kind'] == 'internode'}
        _need(v['parent_internode_id'] in parents, 'PARENT_HOLD: actual current pre-point internode parent required')
        _need(event['internode_id'] not in {row['compartment_id'] for row in p['stem_root_compartments']},
              'EVENT_HOLD: canonical source internode already exists')
        leaf_packet = v['leaf']
        if leaf_packet is not None:
            leaf.arithmetic._closed(leaf_packet,{'incoming_temperature','declaration'})
            _need(leaf_packet['declaration']['leaf_id'] == event['leaf_id'] and event['leaf_id'] not in {row['leaf_id'] for row in p['leaves']},
                  'EVENT_HOLD: unique canonical source leaf required')
        before = calculation['dense_candidate']; y = before['state']; n = len(p['leaves']); old_m = len(p['stem_root_compartments'])
        profiles = stock.parent._profiles(context._source._root)
        stem_event = {'event_id':event['internode_event_id'],'parent_internode_id':v['parent_internode_id'],'compartment':v['internode']}
        first = stem._jump(p,y,profiles,[stem_event]); components = {'internode':_components(first,'internode')}
        after_program,after,rates,evaluation = (first[k] for k in ('program','state','rates','evaluation'))
        anchors = deepcopy(saved['anchors']); leaf_receipts = []; leaf_jump = None
        if leaf_packet is not None:
            leaf_event = {'event_id':event['leaf_event_id'],'parent_internode_id':event['internode_id'],
                'incoming_temperature':leaf_packet['incoming_temperature'],'leaf':leaf_packet['declaration']}
            leaf_jump = leaf._jump(after_program,after,profiles,[leaf_event],anchors)
            _need(leaf_jump['before_capacity'] == before['derived']['canopy_capacity']['value'], 'STATE_HOLD: original current canopy capacity required')
            after_program,after,rates,evaluation = (leaf_jump[k] for k in ('program','state','rates','evaluation'))
            anchors,leaf_receipts = leaf_jump['anchors'],leaf_jump['receipts']; components['leaf'] = _components(leaf_jump,'leaf')
        nn = len(after_program['leaves']); view = stock.short._view(evaluation); derived = view['joint']['derived']
        _need(after[1:103] == y[1:103] and after[104:106] == y[104:106]
              and after[106:106+n] == y[106:106+n] and after[106+nn:106+nn+n] == y[106+n:106+2*n]
              and after[106+2*nn:106+2*nn+n] == y[106+2*n:106+3*n]
              and after[106+3*nn:106+3*nn+old_m] == y[106+3*n:] and anchors[:n] == saved['anchors'],
              'STATE_HOLD: original non-target scalars/ages/areas/C/root inventory and D0 required')
        if leaf_packet is None:
            _need(after[103] == y[103] and derived['canopy_capacity'] == before['derived']['canopy_capacity'], 'STATE_HOLD: no leaf thermal jump without a leaf')
        units = {name:q['unit'] for name,q in components['internode'].items()}
        exact_flows = {name:sum((F(part[name]['value']) for part in components.values()),Fraction(0)) for name in units}
        flows = {name:stock.numeric._q(leaf.arithmetic._rounded(value),units[name]) for name,value in exact_flows.items()}
        a,b = tuple(map(F,y)),tuple(map(F,after)); C0 = point.candidate._carbon(a,n); C1 = point.candidate._carbon(b,nn)
        Ca = F(before['derived']['air_capacity']['value']); _need(Ca == F(derived['air_capacity']['value']), 'STATE_HOLD: original air capacity required')
        latent = F(profiles['exchange_profile'].values['latent_heat']); reference = F(p['scenario']['parameters']['reference_temperature']['value'])
        energy = lambda state:state[103]+Ca*(state[104]-reference)+latent*state[105]
        terms = {
            'buffer':([b[0],-a[0],*(F(part['buffer_debit']['value']) for part in components.values())],MASS),
            'whole_carbohydrate':([C1,-C0,*(F(part['growth_respiration']['value']) for part in components.values())],MASS),
            'new_internode':([b[-1],-F(first['structural'])],MASS),
            'stem_root_carbon':([sum(b[106+3*nn:]),-sum(a[106+3*n:]),-F(first['structural'])],MASS),
            'capacity':([F(derived['canopy_capacity']['value']),-F(before['derived']['canopy_capacity']['value']),-exact_flows['capacity_in']],stock.numeric.CAPACITY),
            'canopy_sensible':([b[103],-a[103],-exact_flows['sensible_in']],stock.numeric.ENERGY),
            'air_sensible':([Ca*b[104],-Ca*a[104]],stock.numeric.ENERGY),
            'vapor':([b[105],-a[105]],'kg_water/m2_floor'),
            'fruit_number':([sum(b[53:103]),-sum(a[53:103])],'fruits_equivalent/m2_floor'),
            'reduced_energy':([energy(b),-energy(a),-exact_flows['sensible_in']],stock.numeric.ENERGY)}
        if leaf_packet is not None:
            terms['new_leaf'] = ([b[106+2*nn+n],-F(leaf_jump['structural'])],MASS)
        balances = {name:_balance(values,unit) for name,(values,unit) in terms.items()}
        result = {'model_version':MATERIAL_VERSION,'policy':POLICY,'code_sha256':CODE_SHA256,'source_code_sha256':pins,
            'scope':'software_research_only','time_kind':'synthetic_model_clock_not_observation','G0_G4':'not_assessed',
            'claim_scope':'source_bound_next_fractional_material_point_only_no_schedule_or_checkpoint_adoption',
            'context_sha256':context.root_sha256,'checkpoint_sha256':expected_sha256,'input_sha256':sha256(raw).hexdigest(),'inputs':v,
            'before_candidate_sha256':calculation['calculation_sha256'],'before_candidate':calculation,'source_event':event,
            'at':deepcopy(calculation['at']),'after_program':after_program,'after_state':after,'after_rates':list(rates),'after_derived':deepcopy(derived),
            'after_state_layout':stock.short._layout(after_program),'after_anchors':anchors,'after_curve_residuals':deepcopy(view['curve_residuals']),
            'after_curve_invariant_changes':[stock.numeric._q(stock.numeric._sum(q['value'],-anchor['value']),'m2') for q,anchor in zip(view['curve_residuals'],anchors,strict=True)],
            'internode_receipts':first['receipts'],'leaf_receipts':leaf_receipts,'flow_components':components,
            'point_flows':flows,'point_flows_exact':{name:Q(value,units[name]) for name,value in exact_flows.items()},'point_balances':balances,
            'point_order':['internode','leaf'] if leaf_packet is not None else ['internode'],
            'growth_costs':{'cStemG':first['cost'],**({'cLeafG':leaf_jump['cost']} if leaf_packet is not None else {}),
                'unit':'mg_CH2O/mg_CH2O','profile_sha256':profiles['growth_profile'].sha256},
            'redistribution_authorized':saved['redistribution_authorized'] and v['rights']['redistribute'],
            'initialization_scope':'only_declared_new_leaf_canonical_F0_no_existing_or_stem_geometry_initialization',
            'new_organ_age_basis':'since_this_numerical_material_point_not_exact_physical_emergence',
            'parent_link_scope':'declared_actual_inventory_link_not_validated_anatomical_axis_assignment',
            'past_intervals_reintegrated':0,'rhs_evaluations':38+(leaf_packet is not None),'elapsed_seconds_advanced':Q(Fraction(0),'s'),
            'schedule_adoption':'not_performed','integrator_checkpoint':None,'post_point_global_prefix_adoption':'not_performed',
            'geometry':'not_derived','effects':'read_only_stateless_same_before_input_repeats_identical_result'}
        result['calculation_sha256'] = sha256(_canonical(result)).hexdigest(); _canonical(result)
        resume._fence(context,data)
        _need(_canonical(inputs) == raw, 'INPUT_HOLD: original explicit material inputs required before return')
        _need(_pins() == pins, 'CODE_HOLD: original point dependencies required before return')
        return deepcopy(result)
    except RepeatEventHold:
        raise
    except (ValueError,TypeError,KeyError,AttributeError,OSError,OverflowError,ZeroDivisionError,RecursionError) as error:
        raise RepeatEventHold(str(error)) from None
