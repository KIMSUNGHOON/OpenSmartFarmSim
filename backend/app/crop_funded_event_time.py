"""Bound a stored interval's thermal threshold in the shared RK4 cubic only."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import crop_funded_shoot_epochs as epochs
from . import crop_leaf_carbon_stock_dynamics as dynamics
from .crop_growth_rates import ReferenceParameters as Growth
from .crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from .crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from .crop_canopy_exchange import ReferenceParameters as Exchange
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse

MODEL_VERSION = 'funded-air-rk4-cubic-threshold-root-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
MAX_BISECTIONS = 128
METHOD_REFERENCE = 'https://doi.org/10.1007/s42967-025-00480-8'
leaf = epochs.leaf


class FundedEventTimeHold(MorphologyArtifactHold):
    pass


def _pins():
    return {**epochs._pins(), 'backend/app/crop_funded_event_time.py':
            sha256(Path(__file__).read_bytes()).hexdigest()}


def _rational(value, unit):
    return {'numerator': str(value.numerator), 'denominator': str(value.denominator), 'unit': unit}


def _value(coefficients, theta):
    result = Fraction(0)
    for coefficient in reversed(coefficients):
        result = result*theta+coefficient
    return result


def _thermal_polynomial(temperatures, dt, base, left_age, threshold):
    a, b, c, d = temperatures
    return (left_age-threshold, dt*(a-base)/86400,
            dt*(-3*a/2+b+c-d/2)/86400,
            dt*2*(a-b-c+d)/(3*86400))


def _minimum_derivative(coefficients):
    _, c, b, a = coefficients
    a *= 3
    b *= 2
    candidates = [c, a+b+c]
    if a > 0 and 0 < -b/(2*a) < 1:
        theta = -b/(2*a)
        candidates.append((a*theta+b)*theta+c)
    return min(candidates)


def _root_interval(coefficients, dt, tolerance):
    _need(type(tolerance) is Fraction and 0 < tolerance <= dt,
          'TOLERANCE_HOLD: positive exact tolerance no wider than the source step required')
    _need(_minimum_derivative(coefficients) > 0,
          'MONOTONICITY_HOLD: strictly increasing cubic thermal age required')
    _need(_value(coefficients, Fraction(0)) < 0 <= _value(coefficients, Fraction(1)),
          'ROOT_HOLD: cubic must bracket the original threshold')
    lower, upper = Fraction(0), Fraction(1)
    iterations = 0
    while (upper-lower)*dt > tolerance:
        _need(iterations < MAX_BISECTIONS, 'PRECISION_HOLD: bounded exact root isolation exhausted')
        middle = (lower+upper)/2
        if _value(coefficients, middle) < 0:
            lower = middle
        else:
            upper = middle
        iterations += 1
    return lower, upper, iterations


def _stages(p, checkpoint, right, root_seed, archive, profiles, dt):
    state = tuple(checkpoint['last_confirmed']['state'])
    k1, r1 = dynamics._evaluate(p, state, profiles)
    y2 = dynamics._advance(state, k1, dt/2)
    k2, r2 = dynamics._evaluate(p, y2, profiles)
    y3 = dynamics._advance(state, k2, dt/2)
    k3, r3 = dynamics._evaluate(p, y3, profiles)
    y4 = dynamics._advance(state, k3, dt)
    k4, r4 = dynamics._evaluate(p, y4, profiles)
    end = dynamics._advance(state, dynamics._weighted(k1, k2, k3, k4), dt)
    _, end_rhs = dynamics._evaluate(p, end, profiles)
    anchors = root_seed['evaluation']['curve_residuals'] if archive is None else archive['seed']['anchors']
    sample = dynamics._sample(right['step_index'], dt, end, end_rhs, anchors)
    _need(_canonical(sample) == _canonical(right['last_confirmed']),
          'REPLAY_HOLD: all original endpoint sample values required')
    pairs = ((state, r1), (y2, r2), (y3, r3), (y4, r4))
    fluxes = [dynamics._flux(p, y, rhs) for y, rhs in pairs]
    block = 'integrated_transfers' if archive is None else 'segment_integrated_transfers'
    units = dynamics._flux_units(p)
    totals = tuple(checkpoint[block][name]['value'] for name in units)
    advanced = dynamics._advance(totals, dynamics._weighted(*fluxes), dt)
    expected = {name: {'value': value, 'unit': unit} for (name, unit), value in zip(units.items(), advanced, strict=True)}
    _need(_canonical(expected) == _canonical(right[block]),
          'REPLAY_HOLD: all original endpoint transfer values required')
    if archive is not None:
        lifetime = {name: {'value': dynamics.numeric._sum(archive['seed']['base_transfers'][name]['value'], value), 'unit': unit}
                    for (name, unit), value in zip(units.items(), advanced, strict=True)}
        _need(_canonical(lifetime) == _canonical(right['integrated_transfers']),
              'REPLAY_HOLD: original lifetime transfers required')
    return [y[105] for y, _ in pairs], [sha256(_canonical({'state': y, 'rates': k, 'flux': f})).hexdigest()
        for (y, _), k, f in zip(pairs, (k1, k2, k3, k4), fluxes, strict=True)]


def locate_funded_shoot_threshold(leaf_directory, stem_directory, access, *, leaf_root_sha256,
                                  stem_root_sha256, stem_start_index, bracket_index,
                                  time_tolerance_seconds_exact):
    try:
        pins = _pins()
        _need(pins['backend/app/crop_funded_event_time.py'] == CODE_SHA256,
              'CODE_HOLD: original event-time source required')
        epochs.stem._elapsed(time_tolerance_seconds_exact)
        tolerance = epochs.stem._fraction(time_tolerance_seconds_exact)
        _need(type(bracket_index) is int and bracket_index >= 0, 'INDEX_HOLD: explicit threshold bracket required')
        projection = epochs.project_funded_shoot_from_stored_state(leaf_directory, stem_directory, access,
            leaf_root_sha256=leaf_root_sha256, stem_root_sha256=stem_root_sha256, stem_start_index=stem_start_index)
        _need(bracket_index < len(projection['event_brackets']), 'INDEX_HOLD: original bracket absent')
        bracket = projection['event_brackets'][bracket_index]
        li, ri = bracket['left_frame_index'], bracket['right_frame_index']
        with MorphologyBlobStore(leaf_directory, access) as store:
            raw = store.get(leaf_root_sha256, maximum=leaf.MAX)
            manifest = _parse(raw, leaf.MAX)
            _, _, _, root_seed, frames, _, raws = leaf._graph(store, manifest)
            _need(all(manifest['source_rights'][name] is True for name in ('use', 'transform', 'display')),
                  'RIGHTS_HOLD: calculation and display grants required')
            ld, rd = (manifest['samples'][i] for i in (li, ri))
            left, right = (frames[i]['checkpoint'] for i in (li, ri))
            _need(rd['step_index'] == ld['step_index']+1 and ri == li+1
                  and ld['context_sha256'] == rd['context_sha256']
                  and ld['event_sequence'] == rd['event_sequence'],
                  'TIME_HOLD: one consecutive unchanged-population interval required')
            _need(ld['checkpoint_sha256'] == bracket['left_checkpoint_sha256']
                  and rd['checkpoint_sha256'] == bracket['right_checkpoint_sha256'],
                  'HASH_HOLD: original bracket checkpoint pair required')
            profiles = {name: kind(raws[name]) for name, kind in (
                ('growth_profile', Growth), ('cohort_profile', Cohort),
                ('transport_profile', Transport), ('exchange_profile', Exchange))}
            dt_float = float(_parse(raws['inputs'], leaf.MAX)['step_seconds'])
            _need(isfinite(dt_float) and dt_float > 0, 'TIME_HOLD: original finite step required')
            temperatures, stage_hashes = _stages(frames[li]['program'], left, right, root_seed,
                frames[li]['context'], profiles, dt_float)
            dt = Fraction.from_float(dt_float)
            left_frame, right_frame = (projection['frames'][i] for i in (li, ri))
            start = epochs.stem._fraction(left_frame['at']['elapsed_seconds_exact'])
            _need(epochs.stem._fraction(right_frame['at']['elapsed_seconds_exact']) == start+dt,
                  'TIME_HOLD: original exact step duration required')
            base = Fraction.from_float(float(projection['stem_source_state']['timeline_state']['base_temperature']['value']))
            age = epochs.stem._fraction(left_frame['shoot_age_exact'])
            threshold = epochs.stem._fraction(bracket['thermal_age_exact'])
            coefficients = _thermal_polynomial(tuple(map(Fraction.from_float, temperatures)), dt, base, age, threshold)
            lower, upper, iterations = _root_interval(coefficients, dt, tolerance)
            right_age = epochs.stem._fraction(right_frame['shoot_age_exact'])
            result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'G0_G4': 'not_assessed',
                'claim_scope': 'stored_interval_cubic_threshold_root_only', 'code_sha256': CODE_SHA256,
                'source_code_sha256': pins, 'method_reference': METHOD_REFERENCE,
                'method': 'classical_rk4_third_order_continuous_extension_eq28_exact_rational_bisection',
                'leaf_artifact_sha256': leaf_root_sha256, 'stem_artifact_sha256': stem_root_sha256,
                'projection_sha256': sha256(_canonical(projection)).hexdigest(), 'bracket_index': bracket_index,
                'source_bracket': deepcopy(bracket), 'stage_sha256': stage_hashes,
                'stage_air_temperatures': [{'value': t, 'unit': 'degC'} for t in temperatures],
                'polynomial_coefficients': [_rational(c, 'degC_day') for c in coefficients],
                'minimum_derivative_per_theta': _rational(_minimum_derivative(coefficients), 'degC_day'),
                'numerical_root_interval': {'time_origin_utc': projection['simulation_origin_utc'],
                    'lower_elapsed_seconds_exact': _rational(start+lower*dt, 's'),
                    'upper_elapsed_seconds_exact': _rational(start+upper*dt, 's'),
                    'width_seconds_exact': _rational((upper-lower)*dt, 's'),
                    'lower_thermal_residual_exact': _rational(_value(coefficients, lower), 'degC_day'),
                    'upper_thermal_residual_exact': _rational(_value(coefficients, upper), 'degC_day')},
                'requested_time_tolerance_seconds_exact': deepcopy(time_tolerance_seconds_exact),
                'bisections': iterations, 'endpoint_sample_and_all_transfers': 'exact_original_binary64_replay',
                'ideal_cubic_minus_stored_endpoint_age': _rational(_value(coefficients, Fraction(1))+threshold-right_age, 'degC_day'),
                'rhs_evaluations': 5, 'past_intervals_reintegrated': 0,
                'time_error_scope': 'bracket_width_bounds_only_this_cubic_root_not_ODE_or_physical_event_error',
                'event_state': 'not_created', 'new_internodes': 'not_created', 'integrator_checkpoint': None}
            _need(len(_canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded event-time result required')
            raws['root'] = raw
            leaf._fence(store, manifest, raws)
        _need(epochs.project_funded_shoot_from_stored_state(leaf_directory, stem_directory, access,
            leaf_root_sha256=leaf_root_sha256, stem_root_sha256=stem_root_sha256,
            stem_start_index=stem_start_index) == projection, 'HASH_HOLD: original source projection changed')
        _need(_pins() == pins, 'CODE_HOLD: event-time calculation sources changed')
        return deepcopy(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FundedEventTimeHold(str(error)) from None
