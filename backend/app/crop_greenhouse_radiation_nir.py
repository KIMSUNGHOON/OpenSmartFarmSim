"""Virtual solar NIR only; crop-greenhouse-radiation-nir-v1.md.

Source attribution: crop-nir-source-register-20261013.json and retained
LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
"""
from hashlib import sha256
import json
from math import exp, expm1, fsum, isfinite, ulp
from pathlib import Path

VERSION = 'prescribed-virtual-solar-nir-boundary-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256 = 'c0fb7a025533f15b80cb6cd60aafdc19be9fe42df6b8183cf97b83fc086138b3'
NOTICE_SHA256 = '96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a'
HEAT = 'W/m2_floor'
INPUT_UNITS = {'outdoor_global_radiation': HEAT, 'solar_nir_fraction': '1',
    'leaf_area_index': 'm2_leaf/m2_floor', 'nir_extinction_coefficient': 'm2_floor/m2_leaf',
    'cover_nir_reflectance': '1', 'canopy_nir_reflectance': '1', 'floor_nir_reflectance': '1',
    'construction_interception_fraction': '1'}
POLICY = {'optics': 'source_virtual_cover_canopy_then_floor',
    'algebra': 'positive_absorptance_and_passive_complement_denominators',
    'physical_cover_air_construction': 'no_derived_heat_credit',
    'claims': 'virtual_NIR_partition_only_not_whole_solar', 'balance_ulps': 32}


class RadiationNIRHold(ValueError):
    """The explicit virtual NIR calculation cannot support this input."""


def _need(condition, reason):
    if not condition:
        raise RadiationNIRHold(reason)


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def _product(*values):
    if 0 in values:
        return 0.0
    value = 1.0
    for factor in values:
        value *= factor
        _need(isfinite(value) and value > 0, 'NUMERIC_HOLD: product overflow or underflow')
    return value


def _divide(numerator, denominator):
    _need(isfinite(denominator) and denominator > 0, 'OPTICS_HOLD: singular reflection denominator')
    value = numerator/denominator
    _need(isfinite(value) and value >= 0 and (numerator == 0 or value > 0),
        'NUMERIC_HOLD: division overflow or underflow')
    return value


def _prepare(scenario):
    _need(type(scenario) is dict and set(scenario) == {'input_id', 'origin', 'values'},
        'INPUT_HOLD: closed scenario required')
    _need(type(scenario['input_id']) is str and 1 <= len(scenario['input_id']) <= 200
        and bool(scenario['input_id'].strip()) and type(scenario['origin']) is str
        and scenario['origin'] in ('synthetic', 'reference_calculation'),
        'INPUT_HOLD: explicit research provenance required')
    rows = scenario['values']
    _need(type(rows) is dict and set(rows) == set(INPUT_UNITS), 'INPUT_HOLD: explicit quantities required')
    values = {}
    for key, unit in INPUT_UNITS.items():
        q = rows[key]
        _need(type(q) is dict and set(q) == {'value', 'unit'}, 'INPUT_HOLD: closed quantity required')
        _need(type(q['unit']) is str and q['unit'] == unit, 'UNIT_HOLD: '+key)
        _need(type(q['value']) in (int, float), 'INPUT_HOLD: numeric quantity required')
        value = float(q['value'])
        _need(isfinite(value) and value >= 0, 'INPUT_HOLD: finite nonnegative quantity required')
        _need(unit != '1' or value <= 1, 'OPTICS_HOLD: fraction outside [0,1]')
        values[key] = value
    return values, {**scenario, 'values': {k: {'value': v, 'unit': INPUT_UNITS[k]} for k, v in values.items()}}


def calculate_nir(*, scenario):
    """Calculate the pinned virtual NIR partition without a thermal state advance."""
    try:
        v, normalized = _prepare(scenario)
        depth = _product(v['nir_extinction_coefficient'], v['leaf_area_index'])
        t, intercepted = exp(-depth), -expm1(-depth)
        _need(t > 0 and (depth == 0 or intercepted > 0), 'NUMERIC_HOLD: attenuation underflow')
        c, f = v['cover_nir_reflectance'], v['floor_nir_reflectance']
        x, y = 1-c, 1-f
        r = _product(v['canopy_nir_reflectance'], intercepted)
        a = _product(1-v['canopy_nir_reflectance'], intercepted)
        d1 = fsum((x, _product(c, fsum((t, a)))))
        T = _product(x, _divide(t, d1))
        Ru = fsum((c, _product(x, _divide(_product(x, r), d1))))
        Rd = fsum((r, _product(t, _divide(_product(t, c), d1))))
        Au = _product(x, _divide(a, d1))
        Ad = _product(a, fsum((1, _divide(_product(c, t), d1))))
        d2 = fsum((y, _product(f, fsum((T, Ad)))))
        floor = _product(T, _divide(y, d2))
        canopy = fsum((Au, _product(T, _divide(_product(f, Ad), d2))))
        reflected = fsum((Ru, _product(T, _divide(_product(f, T), d2))))
        fractions = {'virtual_cover_transmittance': x, 'virtual_floor_transmittance': y,
            'canopy_transmittance': t, 'canopy_reflectance': r, 'canopy_single_pass_absorptance': a,
            'cover_canopy_transmittance': T, 'cover_canopy_reflectance_up': Ru,
            'cover_canopy_reflectance_down': Rd, 'cover_canopy_absorptance_up': Au,
            'cover_canopy_absorptance_down': Ad,
            'canopy_absorptance': canopy, 'floor_absorptance': floor, 'upward_reflectance': reflected}
        _need(all(isfinite(q) and 0 <= q <= 1+32*ulp(1.0) for q in fractions.values()),
            'OPTICS_HOLD: unavailable passive coefficient')
        outside = _product(v['outdoor_global_radiation'], v['solar_nir_fraction'])
        available = _product(outside, 1-v['construction_interception_fraction'])
        energy = {'canopy_absorbed_nir': _product(available, canopy),
            'floor_absorbed_nir': _product(available, floor),
            'upward_virtual_nir': _product(available, reflected),
            'construction_unallocated_nir': _product(outside, v['construction_interception_fraction'])}
        rows = {'cover_canopy_top': (1.0, (T, Ru, Au), '1'),
            'cover_canopy_bottom': (1.0, (T, Rd, Ad), '1'),
            'virtual_nir_optics': (1.0, (canopy, floor, reflected), '1'),
            'virtual_nir_energy': (outside, tuple(energy.values()), HEAT)}
        residuals, budgets = {}, {}
        for key, (incoming, terms, unit) in rows.items():
            value = fsum((incoming, *(-q for q in terms)))
            budget = 32*ulp(max(incoming, *terms))
            _need(isfinite(value) and abs(value) <= budget, 'BALANCE_HOLD: unresolved '+key)
            residuals[key], budgets[key] = {'value': value, 'unit': unit}, {'value': budget, 'unit': unit}
        identity = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
            'policy_sha256': _hash(POLICY), 'source_sha256': SOURCE_SHA256, 'notice_sha256': NOTICE_SHA256,
            'input_sha256': _hash(normalized)}
        def quantities(values, unit):
            return {k: {'value': q, 'unit': unit} for k, q in values.items()}
        return {**identity, 'calculation_sha256': _hash(identity), 'scenario': normalized,
            'optics': quantities(fractions, '1'), 'reflection_denominators': quantities({'cover_canopy': d1,
                'cover_canopy_floor': d2}, '1'), 'heat_components': quantities(energy, HEAT),
            'diagnostics': quantities({'outdoor_nir': outside, 'available_virtual_nir': available}, HEAT),
            'partition_residuals': residuals, 'partition_budgets': budgets,
            'scope': 'software_research_only', 'claim_scope': 'synthetic_virtual_solar_NIR_math_only',
            'G0_G4': 'not_assessed', 'time_coordinate': 'instantaneous_no_state_advance'}
    except (OverflowError, ZeroDivisionError) as exc:
        raise RadiationNIRHold('NUMERIC_HOLD: unrepresentable arithmetic') from exc
