"""One real mixed-organ RK4 step; crop-organ-next-threshold-v1.md."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from pathlib import Path

from . import crop_organ_current_shoot_clock as clock
from . import crop_funded_event_time as event

stock = clock.stock
VERSION = 'individual-organ-next-rk4-threshold-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
F = Fraction.from_float
ENDPOINT_FIELDS = stock.CP_FIELDS-{'version','context_sha256','scope','G0_G4','time_kind','redistribution_authorized'}


class NextThresholdHold(ValueError):
    pass


def _need(condition, reason):
    if not condition:
        raise NextThresholdHold(reason)


def _pins():
    expected = {**clock._pins(), 'backend/app/crop_funded_event_time.py': event.CODE_SHA256,
                'backend/app/crop_organ_next_threshold.py': CODE_SHA256}
    root = Path(__file__).resolve().parents[2]
    actual = {name: sha256((root/name).read_bytes()).hexdigest() for name in expected}
    _need(actual == expected, 'CODE_HOLD: original next-step threshold sources required')
    return actual


def _crossing_status(cubic_residual, stored_residual):
    _need((cubic_residual >= 0) == (stored_residual >= 0),
          'ROUNDING_HOLD: ideal cubic and original stored endpoint disagree on threshold crossing')
    return 'threshold_bracket' if cubic_residual >= 0 else 'no_crossing'


def _step(context, p, seed, m, current, state, totals, rates, first):
    dt = m['numerical']['step_seconds']; profiles = stock.parent._profiles(context._root)
    rows = []; y, k, evaluated = state, rates, first
    for index in range(4):
        rows.append({'state': list(y), 'rates': list(k), 'flux': list(stock.short._flux(p, y, evaluated))})
        if index < 3:
            y = stock.short._advance(state, k, dt/2 if index < 2 else dt)
            k, evaluated = stock.short._evaluate(p, y, profiles)
    candidate = stock.short._advance(state, stock.short._weighted(*(r['rates'] for r in rows)), dt)
    cumulative = stock.short._advance(totals, stock.short._weighted(*(r['flux'] for r in rows)), dt)
    _, last = stock.short._evaluate(p, candidate, profiles)
    sample = stock.short._sample(current['step_index']+1, dt, candidate, last, seed['anchors'])
    prefix = stock._prefix(current['output_prefix_sha256'], sample, current['event_sequence'], 'funded_birth_interval')
    endpoint = stock._build(context, p, seed, m, sample, cumulative, prefix)
    _need(len(stock._canonical(endpoint)) <= stock.MAX_CHECKPOINT_BYTES,
          'CAPACITY_HOLD: prospective endpoint exceeds original 512KiB checkpoint cap')
    return rows, endpoint


def probe_next_shoot_threshold(context, raw_checkpoint, *, expected_sha256, time_tolerance_seconds_exact):
    try:
        pins = _pins(); p, seed, m = stock._context(context); before = clock._snapshot(context)
        clock.stem._elapsed(time_tolerance_seconds_exact); tolerance = clock.stem._fraction(time_tolerance_seconds_exact)
        dt = F(m['numerical']['step_seconds'])
        _need(0 < tolerance <= dt, 'TOLERANCE_HOLD: positive explicit exact tolerance no larger than original step required')
        current = stock._parse(raw_checkpoint, expected_sha256, stock.MAX_CHECKPOINT_BYTES)
        state, totals, rates, first = stock._validate(context, current, p, seed, m)
        _need(current['step_index'] < m['numerical']['step_count'], 'COMPLETED_HOLD: no original next interval remains')
        binding = stock._source(context); timeline = binding['stem_selection']['source_state']['timeline_state']
        start = clock.stem._fraction(current['at_elapsed_seconds_exact'])
        base = float(timeline['base_temperature']['value'])
        initial_age = clock.stem._fraction(timeline['age_exact'])
        left_age = clock._age(initial_age, clock._integral(current['integrated_transfers']['indoor_air_temperature_time']), start, base)
        threshold = clock.stem._fraction(timeline['next_threshold_exact'])
        _need(clock.stem._fraction(left_age) < threshold,
              'SCHEDULE_HOLD: original unconsumed threshold already due at or before this checkpoint')
        rows, endpoint = _step(context, p, seed, m, current, state, totals, rates, first)
        temperatures = [row['state'][104] for row in rows]
        coefficients = event._thermal_polynomial(tuple(map(F, temperatures)), dt, F(base), clock.stem._fraction(left_age), threshold)
        minimum = event._minimum_derivative(coefficients)
        _need(minimum > 0, 'MONOTONICITY_HOLD: strictly increasing original interval cubic required')
        right_age = clock._age(initial_age, clock._integral(endpoint['integrated_transfers']['indoor_air_temperature_time']), start+dt, base)
        right_residual = clock.stem._fraction(right_age)-threshold
        cubic_residual = event._value(coefficients, Fraction(1))
        status = _crossing_status(cubic_residual, right_residual)
        root = None; iterations = 0
        if status == 'threshold_bracket':
            lower, upper, iterations = event._root_interval(coefficients, dt, tolerance)
            root = {'time_origin_utc': binding['crop_selection']['time_origin_utc'],
                'lower_elapsed_seconds_exact': event._rational(start+lower*dt, 's'),
                'upper_elapsed_seconds_exact': event._rational(start+upper*dt, 's'),
                'width_seconds_exact': event._rational((upper-lower)*dt, 's'),
                'lower_thermal_residual_exact': event._rational(event._value(coefficients, lower), 'degC_day'),
                'upper_thermal_residual_exact': event._rational(event._value(coefficients, upper), 'degC_day')}
        result = {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'source_code_sha256': pins,
            'scope': 'software_research_only', 'time_kind': 'synthetic_model_clock_not_observation', 'G0_G4': 'not_assessed',
            'claim_scope': 'one_next_rk4_interval_and_first_unconsumed_threshold_cubic_only', 'status': status,
            'context_sha256': context.root_sha256, 'root_context_sha256': context._root.root_sha256,
            'checkpoint_sha256': expected_sha256, 'initial_binding_sha256': m['initial_binding_sha256'],
            **{name: current[name] for name in ('step_index','event_sequence','phase','output_cursor','output_prefix_sha256')},
            'crop_selection': deepcopy(binding['crop_selection']),
            'stem_selection': {name: deepcopy(value) for name,value in binding['stem_selection'].items() if name != 'source_state'},
            'source_rights': deepcopy(binding['source_rights']), 'point_rights': [deepcopy(r['inputs']['rights']) for r in context.point_history],
            'redistribution_authorized': m['redistribution_authorized'], 'source_timeline': deepcopy(timeline),
            'clock_model_version': clock.VERSION, 'clock_policy': clock.POLICY,
            'left_elapsed_seconds_exact': deepcopy(current['at_elapsed_seconds_exact']),
            'right_elapsed_seconds_exact': deepcopy(endpoint['at_elapsed_seconds_exact']),
            'step_seconds_exact': event._rational(dt, 's'), 'left_shoot_age_exact': left_age, 'stored_right_shoot_age_exact': right_age,
            'source_threshold_exact': deepcopy(timeline['next_threshold_exact']), 'source_threshold_sequence': timeline['next_sequence'],
            'schedule_status': 'original_first_threshold_not_consumed_or_advanced',
            'method_reference': event.METHOD_REFERENCE,
            'method': 'classical_rk4_third_order_continuous_extension_eq28_exact_rational_bisection',
            'stage_state_layout': deepcopy(m['state_layout']),
            'stage_flux_order': [{'name': name, 'unit': unit} for name,unit in stock.short._flux_units(p).items()],
            'stages': rows, 'stage_sha256': [sha256(stock._canonical(row)).hexdigest() for row in rows],
            'stage_air_temperatures': [{'value': t, 'unit': 'degC'} for t in temperatures],
            'polynomial_coefficients': [event._rational(c, 'degC_day') for c in coefficients],
            'minimum_derivative_per_theta': event._rational(minimum, 'degC_day'),
            'ideal_cubic_minus_stored_endpoint_age': event._rational(cubic_residual-right_residual, 'degC_day'),
            'requested_time_tolerance_seconds_exact': deepcopy(time_tolerance_seconds_exact),
            'numerical_root_interval': root, 'bisections': iterations,
            'unadopted_endpoint': {name: deepcopy(endpoint[name]) for name in sorted(ENDPOINT_FIELDS)},
            'endpoint_status': 'prospective_original_step_not_adopted',
            'rhs_evaluations': 5, 'checkpoint_validation_stage_evaluations': 1, 'new_stage_evaluations': 4,
            'past_intervals_reintegrated': 0, 'new_internodes': 'not_created', 'integrator_checkpoint': None,
            'time_error_scope': 'root_width_only_not_ODE_or_accumulation_or_physical_event_error'}
        result['calculation_sha256'] = sha256(stock._canonical(result)).hexdigest()
        _need(len(stock._canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded 2MiB next-threshold response required')
        _need(stock._source(context) == binding and clock._snapshot(context) == before,
              'SOURCE_HOLD: original current source/rights/context required before return')
        _need(_pins() == pins, 'CODE_HOLD: next-threshold sources changed before return')
        return deepcopy(result)
    except NextThresholdHold:
        raise
    except (ValueError, TypeError, KeyError, AttributeError, OSError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise NextThresholdHold(str(error)) from None
