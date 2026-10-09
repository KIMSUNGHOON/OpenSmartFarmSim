"""Fixed-LAI research dynamics; crop-climate-coupling-v1.md defines the boundary.

Exchange attribution: crop-canopy-exchange-reference-parameters-v1.json and
LICENSES/GreenLight-BSD-3-Clause-Clear.txt. Storage/closures are project choices.
"""
from hashlib import sha256
import json
from math import exp, fsum, isfinite
from pathlib import Path

from .crop_canopy_exchange import CanopyExchangeHold, ReferenceParameters, calculate_exchange

VERSION = 'fixed-lai-canopy-air-mass-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
STATE_UNITS = {'canopy_temperature': 'degC', 'air_temperature': 'degC',
    'air_vapor_mass': 'kg_water/m2_floor'}
PARAMETER_UNITS = {'leaf_area_index': 'm2_leaf/m2_floor',
    'leaf_heat_capacity': 'J/m2_leaf/K', 'air_volume_per_floor_area': 'm3/m2_floor',
    'air_capacity_density': 'kg_air/m3', 'canopy_vapor_resistance': 's/m',
    'vapor_gas_constant': 'J/kg_water/K'}
FORCING_UNITS = {'canopy_external_heat': 'W/m2_floor',
    'air_external_sensible_heat': 'W/m2_floor', 'air_external_vapor': 'kg_water/m2_floor/s'}


class CanopyAirHold(ValueError):
    """The bounded synthetic subsystem cannot support this calculation."""


def _need(condition, reason):
    if not condition:
        raise CanopyAirHold(reason)


def _q(value, unit):
    return {'value': value, 'unit': unit}


def _divide(numerator, denominator):
    value = numerator / denominator
    _need(numerator == 0 or value != 0, 'NUMERIC_HOLD: derivative underflow')
    return value


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _number(value):
    _need(type(value) in (int, float), 'INPUT_HOLD: explicit numeric value required')
    try:
        value = float(value)
    except OverflowError as exc:
        raise CanopyAirHold('NUMERIC_HOLD: unrepresentable input') from exc
    _need(isfinite(value), 'INPUT_HOLD: finite value required')
    return value


def _quantities(block, units):
    _need(type(block) is dict and set(block) == set(units), 'INPUT_HOLD: closed quantities required')
    numbers = {}
    for name, unit in units.items():
        row = block[name]
        _need(type(row) is dict and set(row) == {'value', 'unit'}, 'INPUT_HOLD: closed quantity required')
        _need(type(row['unit']) is str and row['unit'] == unit, 'UNIT_HOLD: ' + name)
        numbers[name] = _number(row['value'])
    return numbers


def _prepare(scenario, profile):
    _need(type(profile) is ReferenceParameters, 'PROFILE_HOLD: pinned exchange profile required')
    _need(type(scenario) is dict and set(scenario) == {'input_id', 'origin', 'state', 'parameters', 'forcing'},
          'INPUT_HOLD: closed scenario required')
    _need(type(scenario['input_id']) is str and 1 <= len(scenario['input_id']) <= 200
          and bool(scenario['input_id'].strip()) and type(scenario['origin']) is str
          and scenario['origin'] in ('synthetic', 'reference_calculation'),
          'INPUT_HOLD: explicit research origin required')
    blocks = {name: _quantities(scenario[name], units) for name, units in
        (('state', STATE_UNITS), ('parameters', PARAMETER_UNITS), ('forcing', FORCING_UNITS))}
    p = blocks['parameters']
    _need(p['leaf_area_index'] > 0, 'EMPTY_CANOPY_HOLD: positive fixed LAI required')
    _need(all(value > 0 for value in p.values()), 'INPUT_HOLD: positive explicit parameters required')
    ccan = p['leaf_heat_capacity'] * p['leaf_area_index']
    cair = p['air_volume_per_floor_area'] * p['air_capacity_density'] * profile.values['air_heat_capacity']
    _need(all(isfinite(value) and value > 0 for value in (ccan, cair)),
          'NUMERIC_HOLD: capacity overflow or underflow')
    normalized = {'input_id': scenario['input_id'], 'origin': scenario['origin'],
        **{name: {key: _q(blocks[name][key], unit) for key, unit in units.items()}
           for name, units in (('state', STATE_UNITS), ('parameters', PARAMETER_UNITS), ('forcing', FORCING_UNITS))}}
    return tuple(blocks['state'].values()), p, blocks['forcing'], (ccan, cair), normalized


def _rhs(state, p, f, capacities, profile):
    tc, ta, mass = state
    low, high = profile.temperature_bounds
    _need(all(map(isfinite, state)) and low <= tc <= high and low <= ta <= high,
          'STATE_HOLD: outside synthetic temperature window or nonfinite state')
    _need(mass >= 0, 'STATE_HOLD: negative vapor mass')
    constants = profile.values
    try:
        pressure = mass / p['air_volume_per_floor_area'] * p['vapor_gas_constant'] * (ta + 273.15)
        _need(isfinite(pressure) and (mass == 0 or pressure > 0),
              'NUMERIC_HOLD: vapor pressure overflow or underflow')
        sat_air = constants['saturation_pressure_coefficient'] * exp(
            constants['saturation_exponent_factor'] * ta / (ta + constants['saturation_denominator_offset']))
        _need(pressure < sat_air, 'BULK_SATURATION_HOLD: no condensation closure')
        exchange = calculate_exchange(profile=profile, forcing={
            'input_id': 'same-stage-canopy-exchange', 'origin': 'synthetic', 'values': {
                'leaf_area_index': _q(p['leaf_area_index'], 'm2_leaf/m2_floor'),
                'canopy_temperature': _q(tc, 'degC'), 'air_temperature': _q(ta, 'degC'),
                'air_vapor_pressure': _q(pressure, 'Pa'),
                'air_capacity_density': _q(p['air_capacity_density'], 'kg_air/m3'),
                'canopy_vapor_resistance': _q(p['canopy_vapor_resistance'], 's/m')}})['exchange']
        e, h, le = (exchange[key]['value'] for key in ('water_vapor', 'sensible_heat', 'latent_heat'))
        rates = (_divide(fsum((f['canopy_external_heat'], -h, -le)), capacities[0]),
            _divide(fsum((f['air_external_sensible_heat'], h)), capacities[1]),
            fsum((e, f['air_external_vapor'])))
        _need(all(map(isfinite, rates)), 'NUMERIC_HOLD: nonfinite derivative')
        energy_residual = fsum((capacities[0]*rates[0], capacities[1]*rates[1],
            constants['latent_heat']*rates[2], -f['canopy_external_heat'],
            -f['air_external_sensible_heat'], -constants['latent_heat']*f['air_external_vapor']))
        water_residual = fsum((rates[2], -e, -f['air_external_vapor']))
    except (CanopyExchangeHold, OverflowError, ZeroDivisionError, ValueError) as exc:
        if isinstance(exc, CanopyAirHold):
            raise
        raise CanopyAirHold('NUMERIC_HOLD: RHS evaluation failed') from exc
    _need(all(map(isfinite, (energy_residual, water_residual))), 'NUMERIC_HOLD: nonfinite balance')
    return rates, (e, h, le), pressure, (energy_residual, water_residual)


def _identity(normalized, profile):
    return {'model_version': VERSION, 'code_sha256': CODE_SHA256, 'input_sha256': _hash(normalized),
        'profile_sha256': profile.sha256, 'source_sha256': profile.source_sha256,
        'notice_sha256': profile.notice_sha256, 'scenario': normalized,
        'scope': 'software_research_only', 'claim_scope': 'synthetic_canopy_air_dynamics_only',
        'G0_G4': 'not_assessed'}


def evaluate_rhs(*, scenario, profile):
    """Evaluate all three storage rates from a single shared exchange evaluation."""
    state, p, f, capacities, normalized = _prepare(scenario, profile)
    rates, transfers, pressure, residuals = _rhs(state, p, f, capacities, profile)
    return {**_identity(normalized, profile),
        'capacities': dict(zip(('canopy', 'air'), (_q(c, 'J/m2_floor/K') for c in capacities))),
        'air_vapor_pressure': _q(pressure, 'Pa'),
        'derivatives': {name: _q(value, unit) for name, value, unit in zip(STATE_UNITS, rates,
            ('K/s', 'K/s', 'kg_water/m2_floor/s'))},
        'exchange': dict(zip(('water_vapor', 'sensible_heat', 'latent_heat'),
            (_q(value, unit) for value, unit in zip(transfers,
                ('kg_water/m2_floor/s', 'W/m2_floor', 'W/m2_floor'))))),
        'canopy_water_boundary': _q(-transfers[0], 'kg_water/m2_floor/s'),
        'balance_residuals': {'reduced_energy': _q(residuals[0], 'W/m2_floor'),
            'vapor_and_water_boundaries': _q(residuals[1], 'kg_water/m2_floor/s')}}


def _sample(index, seconds, state):
    return {'step_index': index, 'elapsed_seconds': seconds,
        'state': {name: _q(value, unit) for (name, unit), value in zip(STATE_UNITS.items(), state)}}


def integrate(*, scenario, profile, step_seconds, step_count):
    """Advance one bounded constant-forcing interval with common-stage RK4."""
    dt = _number(step_seconds)
    _need(dt > 0 and type(step_count) is int and 1 <= step_count <= 4096,
          'BUDGET_HOLD: positive step and 1..4096 integer steps required')
    duration = dt * step_count
    _need(isfinite(duration) and 0 < duration <= 600, 'BUDGET_HOLD: 600s synthetic horizon')
    initial, p, f, capacities, normalized = _prepare(scenario, profile)
    state = initial
    current = _rhs(state, p, f, capacities, profile)
    samples = [_sample(0, 0.0, state)]
    cumulative = (0.0, 0.0, 0.0)
    for index in range(1, step_count + 1):
        stage = 'k2'
        try:
            k1, j1 = current[:2]
            k2, j2, _, _ = _rhs(tuple(y+dt*k/2 for y,k in zip(state,k1)), p, f, capacities, profile)
            stage = 'k3'
            k3, j3, _, _ = _rhs(tuple(y+dt*k/2 for y,k in zip(state,k2)), p, f, capacities, profile)
            stage = 'k4'
            k4, j4, _, _ = _rhs(tuple(y+dt*k for y,k in zip(state,k3)), p, f, capacities, profile)
            slopes = tuple(fsum((a,2*b,2*c,d))/6 for a,b,c,d in zip(k1,k2,k3,k4))
            increments = tuple(dt*k for k in slopes)
            candidate = tuple(y+change for y,change in zip(state,increments))
            _need(all(k == 0 or change != 0 for k,change in zip(slopes,increments)),
                  'NUMERIC_HOLD: state increment underflow')
            _need(all(change == 0 or value != old for change,value,old in zip(increments,candidate,state)),
                  'NUMERIC_HOLD: state increment lost to rounding')
            stage = 'endpoint'
            next_rhs = _rhs(candidate, p, f, capacities, profile)
            cumulative = tuple(fsum((old, dt*(fsum((a,2*b,2*c,d))/6)))
                for old,a,b,c,d in zip(cumulative,j1,j2,j3,j4))
            _need(all(map(isfinite,cumulative)), 'NUMERIC_HOLD: cumulative transfer overflow')
        except (CanopyAirHold, OverflowError, ValueError, ZeroDivisionError) as exc:
            held = CanopyAirHold(f'{exc}: step={index}; stage={stage}; last_confirmed_elapsed_seconds={(index-1)*dt}')
            held.step_index = index
            held.failed_stage = stage
            held.last_confirmed_elapsed_seconds = (index-1)*dt
            held.last_confirmed_state = _sample(index-1, (index-1)*dt, state)['state']
            raise held from exc
        state, current = candidate, next_rhs
        samples.append(_sample(index, index*dt, state))
    e, h, le = cumulative
    latent = profile.values['latent_heat']
    try:
        qcan = duration*f['canopy_external_heat']
        qair = duration*f['air_external_sensible_heat']
        vapor = duration*f['air_external_vapor']
        dc, da, dm = (end-start for end,start in zip(state,initial))
        residuals = {'canopy_sensible': fsum((capacities[0]*dc,-qcan,h,le)),
            'air_sensible': fsum((capacities[1]*da,-qair,-h)),
            'vapor_and_water_boundaries': fsum((dm,-e,-vapor)),
            'reduced_energy': fsum((capacities[0]*dc,capacities[1]*da,latent*dm,-qcan,-qair,-latent*vapor))}
        _need(all(map(isfinite,(*residuals.values(),qcan,qair,vapor))), 'NUMERIC_HOLD: nonfinite final ledger')
    except (OverflowError, ValueError) as exc:
        if isinstance(exc, CanopyAirHold):
            raise
        raise CanopyAirHold('NUMERIC_HOLD: final ledger evaluation failed') from exc
    numerical = {'method': 'fixed-common-stage-rk4-v1', 'step_seconds': dt,
        'step_count': step_count, 'duration_seconds': duration, 'rhs_evaluations': 4*step_count+1}
    identity = _identity(normalized,profile)
    return {**identity, 'calculation_sha256': _hash({'input_sha256':identity['input_sha256'],
            'model_version':VERSION,'code_sha256':CODE_SHA256,'profile_sha256':profile.sha256,'numerical':numerical}),
        'numerical': numerical, 'samples': samples,
        'capacities': dict(zip(('canopy','air'),(_q(c,'J/m2_floor/K') for c in capacities))),
        'integrated_transfers': {name: _q(value,unit) for name,value,unit in (
            ('canopy_to_air_vapor',e,'kg_water/m2_floor'), ('canopy_to_air_sensible',h,'J/m2_floor'),
            ('canopy_to_vapor_latent',le,'J/m2_floor'), ('canopy_water_boundary',-e,'kg_water/m2_floor'),
            ('canopy_external_heat',qcan,'J/m2_floor'), ('air_external_sensible_heat',qair,'J/m2_floor'),
            ('air_external_vapor',vapor,'kg_water/m2_floor'), ('air_external_vapor_latent',latent*vapor,'J/m2_floor'))},
        'balance_residuals': {name: _q(value,'kg_water/m2_floor' if name=='vapor_and_water_boundaries'
            else 'J/m2_floor') for name,value in residuals.items()}}
