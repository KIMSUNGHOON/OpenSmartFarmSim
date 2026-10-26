"""Research candidate at a certified cubic threshold time; no checkpoint adoption."""
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path

from . import crop_funded_event_time as event
from .crop_morphology_artifact_io import MorphologyArtifactHold, MorphologyBlobStore, _need
from .crop_morphology_artifact_reader import _canonical, _parse

MODEL_VERSION = 'funded-air-dense-event-state-and-exact-time-refinement-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
MAX_BYTES = 2*1024**2
REFINEMENTS = (1, 2, 4)
F = Fraction.from_float
RK4_WEIGHTS = (Fraction(1, 6), Fraction(1, 3), Fraction(1, 3), Fraction(1, 6))
dynamics = event.dynamics


class FundedEventStateHold(MorphologyArtifactHold):
    pass


def _pins():
    return {**event._pins(), 'backend/app/crop_funded_event_state.py': sha256(Path(__file__).read_bytes()).hexdigest()}


def _rounded(value, prior=None):
    rounded = float(value)
    _need(isfinite(rounded) and (value == 0 or rounded != 0), 'NUMERIC_HOLD: finite representable candidate required')
    _need(prior is None or value == F(prior) or rounded != prior,
          'NUMERIC_HOLD: nonzero state change lost to rounding')
    return rounded


def _combine(initial, rates, weights, duration):
    return tuple(_rounded(F(prior)+duration*sum((w*F(v) for w, v in zip(weights, row, strict=True)), Fraction(0)), prior)
                 for prior, row in zip(initial, zip(*rates, strict=True), strict=True))


def _weights(theta):
    return (theta-3*theta**2/2+2*theta**3/3, theta**2-2*theta**3/3,
            theta**2-2*theta**3/3, -theta**2/2+2*theta**3/3)


def _collect(p, state, profiles, dt):
    rows = []
    y = state
    for i in range(4):
        k, rhs = dynamics._evaluate(p, y, profiles)
        rows.append((y, k, dynamics._flux(p, y, rhs), rhs))
        if i < 3:
            y = dynamics._advance(state, k, dt/2 if i < 2 else dt)
    return rows


def _ledgers(p, initial, state, transfers, first, last, duration, latent, steps):
    a, b = tuple(map(F, initial)), tuple(map(F, state))
    t = {k: F(v) for k, v in zip(dynamics._flux_units(p), transfers, strict=True)}
    views = [dynamics._view(rhs)['joint']['derived'] for rhs in (first, last)]
    ca = F(views[0]['air_capacity']['value'])
    _need(ca == F(views[1]['air_capacity']['value']), 'BALANCE_HOLD: original air capacity required')
    cap0, cap1 = (F(v['canopy_capacity']['value']) for v in views)
    carbon = lambda y: sum((y[0], y[1], *y[4:54], *y[107+2*len(p['leaves']):]), Fraction(0))
    number = lambda y: sum(y[54:104], Fraction(0))
    du, da, dw = b[104]-a[104], ca*(b[105]-a[105]), b[106]-a[106]
    lam = F(latent)
    reference = F(p['scenario']['parameters']['reference_temperature']['value'])
    energy = lambda y: y[104]+ca*(y[105]-reference)+lam*y[106]
    rows = {
        'carbohydrate': ((carbon(b)-carbon(a), -t['photosynthesis'], *(t[k] for k in (
            'growth_respiration', 'maintenance_leaf', 'maintenance_stem', 'maintenance_fruit', 'removal_leaf', 'removal_stem', 'terminal_carbon'))), carbon(a), carbon(b), 'mg_CH2O/m2_floor'),
        'number': ((number(b)-number(a), -t['entry_number'], t['terminal_number']), number(a), number(b), 'fruits_equivalent/m2_floor'),
        'canopy_sensible': ((du, -t['canopy_external'], t['sensible'], t['latent'], -t['incoming_heat'], t['outgoing_heat']), a[104], b[104], 'J/m2_floor'),
        'air_sensible': ((da, -t['air_external'], -t['sensible']), ca*(a[105]-reference), ca*(b[105]-reference), 'J/m2_floor'),
        'vapor': ((dw, -t['vapor'], -t['external_vapor']), a[106], b[106], 'kg_water/m2_floor'),
        'area_capacity': ((cap1-cap0, -t['capacity_in'], t['capacity_out']), cap0, cap1, 'J/m2_floor/K'),
        'reduced_energy': ((du, da, lam*dw, -t['canopy_external'], -t['air_external'], -lam*t['external_vapor'], -t['incoming_heat'], t['outgoing_heat']), energy(a), energy(b), 'J/m2_floor')}
    n = len(p['leaves'])
    for i, leaf in enumerate(p['leaves']):
        rows[f'leaf_age_{i}'] = ((b[107+i]-a[107+i], -t['indoor_air_temperature_time']/86400,
            F(leaf['base_temperature']['value'])*duration/86400), a[107+i], b[107+i], 'degC_day')
        rows[f'leaf_carbon_{i}'] = ((b[107+2*n+i]-a[107+2*n+i], -t[f'leaf_{i}_inflow'],
            t[f'leaf_{i}_maintenance'], t[f'leaf_{i}_removal']), a[107+2*n+i], b[107+2*n+i], 'mg_CH2O/m2_floor')
    result = {}
    for name, (terms, start, end, unit) in rows.items():
        residual = sum(terms, Fraction(0))
        scale = max(abs(start), abs(end), sum(map(abs, terms), Fraction(0)))
        budget = 64*(steps+1)*F(ulp(_rounded(scale)))
        _need(abs(residual) <= budget, 'BALANCE_HOLD: unresolved exact candidate '+name)
        result[name] = {'residual_exact': event._rational(residual, unit), 'budget_exact': event._rational(budget, unit)}
    return result


def _refine(p, initial, profiles, duration, count):
    state = initial
    totals = (0.,)*len(dynamics._flux_units(p))
    rates, first = dynamics._evaluate(p, state, profiles)
    current = first
    step = duration/count
    latent = profiles['exchange_profile'].values['latent_heat']
    ledgers = None
    for i in range(count):
        f1 = dynamics._flux(p, state, current)
        y2 = _combine(state, (rates,), (Fraction(1),), step/2)
        k2, r2 = dynamics._evaluate(p, y2, profiles)
        y3 = _combine(state, (k2,), (Fraction(1),), step/2)
        k3, r3 = dynamics._evaluate(p, y3, profiles)
        y4 = _combine(state, (k3,), (Fraction(1),), step)
        k4, r4 = dynamics._evaluate(p, y4, profiles)
        candidate = _combine(state, (rates, k2, k3, k4), RK4_WEIGHTS, step)
        cumulative = _combine(totals, (f1, dynamics._flux(p, y2, r2), dynamics._flux(p, y3, r3),
                                      dynamics._flux(p, y4, r4)), RK4_WEIGHTS, step)
        next_rates, last = dynamics._evaluate(p, candidate, profiles)
        ledgers = _ledgers(p, initial, candidate, cumulative, first, last, step*(i+1), latent, i+1)
        state, totals, rates, current = candidate, cumulative, next_rates, last
    return state, totals, ledgers


def _packet(p, state, transfers, ledgers):
    return {'state': list(state), 'partial_interval_transfers': {k: {'value': v, 'unit': unit}
            for (k, unit), v in zip(dynamics._flux_units(p).items(), transfers, strict=True)}, 'local_ledgers': ledgers}


def calculate_funded_threshold_state(leaf_directory, stem_directory, access, **selection):
    try:
        selection = deepcopy(selection)
        pins = _pins()
        _need(pins['backend/app/crop_funded_event_state.py'] == CODE_SHA256, 'CODE_HOLD: original candidate source required')
        certificate = event.locate_funded_shoot_threshold(leaf_directory, stem_directory, access, **selection)
        root_sha = selection['leaf_root_sha256']
        bracket = certificate['source_bracket']
        li = bracket['left_frame_index']
        frac = event.epochs.stem._fraction
        with MorphologyBlobStore(leaf_directory, access) as store:
            raw = store.get(root_sha, maximum=event.leaf.MAX)
            manifest = _parse(raw, event.leaf.MAX)
            _, _, _, _, frames, _, raws = event.leaf._graph(store, manifest)
            descriptor = manifest['samples'][li]
            _need(descriptor['checkpoint_sha256'] == bracket['left_checkpoint_sha256'], 'HASH_HOLD: original left checkpoint required')
            p = frames[li]['program']
            cp = frames[li]['checkpoint']
            initial = tuple(cp['last_confirmed']['state'])
            profiles = {name: kind(raws[name]) for name, kind in (
                ('growth_profile', event.Growth), ('cohort_profile', event.Cohort),
                ('transport_profile', event.Transport), ('exchange_profile', event.Exchange))}
            dt = frac(bracket['end_at']['elapsed_seconds_exact'])-frac(bracket['start_at']['elapsed_seconds_exact'])
            rows = _collect(p, initial, profiles, float(dt))
            hashes = [sha256(_canonical({'state': y, 'rates': k, 'flux': f})).hexdigest() for y, k, f, _ in rows]
            _need(hashes == certificate['stage_sha256'], 'REPLAY_HOLD: original shared stage hashes required')
            selected = frac(certificate['numerical_root_interval']['upper_elapsed_seconds_exact'])
            duration = selected-frac(bracket['start_at']['elapsed_seconds_exact'])
            theta = duration/dt
            _need(0 < theta <= 1, 'TIME_HOLD: selected crossed-side coordinate must be inside the original interval')
            weights = _weights(theta)
            state = _combine(initial, tuple(row[1] for row in rows), weights, dt)
            transfers = _combine((0.,)*len(rows[0][2]), tuple(row[2] for row in rows), weights, dt)
            _, last = dynamics._evaluate(p, state, profiles)
            ledgers = _ledgers(p, initial, state, transfers, rows[0][3], last, duration,
                               profiles['exchange_profile'].values['latent_heat'], 1)
            dense = _packet(p, state, transfers, ledgers)
            refined = []
            for count in REFINEMENTS:
                refined_state, refined_transfers, refined_ledgers = _refine(p, initial, profiles, duration, count)
                refined.append({'substeps': count, 'step_seconds_exact': event._rational(duration/count, 's'),
                    'rhs_evaluations': 4*count+1, **_packet(p, refined_state, refined_transfers, refined_ledgers)})
            result = {'model_version': MODEL_VERSION, 'scope': 'software_research_only', 'G0_G4': 'not_assessed',
                'claim_scope': 'synthetic_selected_cubic_event_candidate_and_local_refinement_only', 'code_sha256': CODE_SHA256,
                'source_code_sha256': pins, 'selection': deepcopy(selection), 'source_root_certificate': certificate,
                'at': {'time_origin_utc': bracket['start_at']['time_origin_utc'], 'elapsed_seconds_exact': event._rational(selected, 's')},
                'selection_policy': 'certified_cubic_root_upper_bound_no_threshold_snap',
                'source_left_checkpoint_sha256': descriptor['checkpoint_sha256'], 'source_left_step_index': descriptor['step_index'],
                'source_event_sequence': descriptor['event_sequence'], 'state_layout': frames[li]['layout'],
                'source_prefix': {k: deepcopy(cp[k]) for k in ('integrated_transfers', 'balance_residuals', 'balance_budgets',
                    'segment_integrated_transfers', 'global_balance_residuals', 'global_balance_budgets',
                    'point_totals', 'point_history_sha256', 'output_prefix_sha256', 'output_cursor') if k in cp},
                'partial_interval_seconds_exact': event._rational(duration, 's'), 'dense_candidate': dense,
                'refinement_method': 'shared_stage_classical_RK4_exact_rational_time_round_once_per_combination_v1',
                'refinements': refined, 'refinement_scope': 'same_exact_time_local_differences_not_certified_ODE_error_bounds',
                'domain_scope': 'selected_dense_state_and_refinement_RHS_stages_only',
                'ledger_rule': 'exact_represented_input_sums_original_64_ULP_per_step_budget',
                'rhs_evaluations': 10+sum(4*n+1 for n in REFINEMENTS),
                'global_prefix_composition': 'not_adopted_source_prefix_plus_pending_local_transfers_only',
                'new_internodes': 'not_created', 'integrator_checkpoint': None}
            _need(len(_canonical(result)) <= MAX_BYTES, 'CAPACITY_HOLD: bounded candidate and refinements required')
            raws['root'] = raw
            event.leaf._fence(store, manifest, raws)
        projection = event.epochs.project_funded_shoot_from_stored_state(leaf_directory, stem_directory, access,
            **{k: selection[k] for k in ('leaf_root_sha256', 'stem_root_sha256', 'stem_start_index')})
        _need(sha256(_canonical(projection)).hexdigest() == certificate['projection_sha256'], 'HASH_HOLD: original source projection changed')
        _need(_pins() == pins, 'CODE_HOLD: candidate sources changed')
        return deepcopy(result)
    except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, ZeroDivisionError, RecursionError) as error:
        raise FundedEventStateHold(str(error)) from None
