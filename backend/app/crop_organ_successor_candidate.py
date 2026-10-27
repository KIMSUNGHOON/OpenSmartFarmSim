"""Current-prefix successor candidates; crop-organ-successor-candidate-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_organ_fractional_continuation as resume

capture, stock, candidate = resume.capture, resume.stock, resume.candidate
old, event = candidate.old, candidate.interval.event
Q, X, F = resume.Q, resume.X, Fraction.from_float
VERSION = 'individual-organ-successor-candidate-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2


class SuccessorCandidateHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise SuccessorCandidateHold(reason)


def _pins():
    pins = {**resume._pins(), 'backend/app/crop_organ_successor_candidate.py': CODE_SHA256}
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


def calculate_successor_candidate(context, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact):
    try:
        pins = _pins(); data = capture._context(context); saved = data['captured']; p = saved['program']
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
    except SuccessorCandidateHold:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise SuccessorCandidateHold(str(error)) from None
