"""Current-state solar/ventilation composition; crop-greenhouse-solar-joint-v1.md."""
from hashlib import sha256
from pathlib import Path

from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_radiation_par_joint as par
from . import crop_greenhouse_radiation_nir as nir
from . import crop_greenhouse_ventilation as vent
from .crop_growth_rates import ReferenceParameters

VERSION = 'current-state-solar-ventilation-joint-rhs-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FORCING_UNITS = {k: v for k, v in par.FORCING_UNITS.items() if k != 'canopy_non_par_heat'}
FORCING_UNITS['canopy_non_solar_heat'] = nir.HEAT
SOLAR_UNITS = {**par.SOLAR_UNITS, **{k: v for k, v in nir.INPUT_UNITS.items() if k != 'leaf_area_index'}}
POLICY = {'LAI': 'pinned_SLA_times_current_leaf', 'solar': 'explicit_shared_two_band_input',
    'heat': 'other_plus_NIR_then_PAR_once', 'ventilation': 'other_air_plus_current_vent_once',
    'evaluation': 'one_NIR_one_vent_one_PAR_one_joint_RHS',
    'unallocated': 'no_floor_cover_reflection_construction_heat_credit'}


class SolarJointHold(joint.JointClimateHold):
    """No mixed or unavailable shared current-state composition is accepted."""


def _need(condition, reason):
    if not condition:
        raise SolarJointHold(reason)


def evaluate_rhs(*, scenario, solar, ventilation, growth_profile, cohort_profile,
        transport_profile, exchange_profile):
    """Evaluate solar PAR/NIR, ventilation and crop/heat at the same current state."""
    try:
        _need(type(growth_profile) is ReferenceParameters, 'PROFILE_HOLD: pinned growth profile required')
        _need(type(scenario) is dict and set(scenario) == {'input_id', 'origin', *joint.SCALAR_BLOCKS,
            *joint.ARRAY_BLOCKS}, 'INPUT_HOLD: closed joint scenario required')
        _need(type(solar) is dict and set(solar) == {'input_id', 'origin', 'values'},
            'INPUT_HOLD: closed shared solar input required')
        _need(type(ventilation) is dict and set(ventilation) == {'input_id', 'origin', 'forcing'},
            'INPUT_HOLD: closed outdoor ventilation input required')
        _need(solar['origin'] == ventilation['origin'] == scenario['origin'], 'INPUT_HOLD: mixed research origins')
        sv, normalized_solar = joint._quantities(solar['values'], SOLAR_UNITS)
        _need(joint._sum(sv['solar_par_fraction'], sv['solar_nir_fraction']) == 1,
            'SPECTRUM_HOLD: explicit PAR plus NIR fractions must equal one')
        forcing, normalized_forcing = joint._quantities(scenario['forcing'], FORCING_UNITS)
        plant, _ = joint._quantities(scenario['plant_state'], joint.SCALAR_BLOCKS['plant_state'])
        _need(plant['leaf'] > 0, 'EMPTY_CANOPY_HOLD: positive current leaf inventory required')
        lai = joint._product(growth_profile.values['sla'], plant['leaf'])
        boundary = nir.calculate_nir(scenario={**solar, 'values': {
            **{k: v for k, v in normalized_solar.items() if k in nir.INPUT_UNITS},
            'leaf_area_index': joint._q(lai, nir.INPUT_UNITS['leaf_area_index'])}})
        _, climate = joint._quantities(scenario['climate_state'], joint.CLIMATE_UNITS)
        _, parameters = joint._quantities(scenario['parameters'], joint.PARAMETER_UNITS)
        outdoor = vent.calculate_ventilation(scenario={**ventilation,
            'state': {k: climate[k] for k in vent.STATE_UNITS},
            'parameters': {k: parameters[k] for k in vent.PARAMETER_UNITS}}, profile=exchange_profile)
        composed = {k: v for k, v in normalized_forcing.items() if k != 'canopy_non_solar_heat'}
        nir_heat = boundary['heat_components']['canopy_absorbed_nir']
        composed['canopy_non_par_heat'] = joint._q(joint._sum(forcing['canopy_non_solar_heat'],
            nir_heat['value']), nir.HEAT)
        for key, q in outdoor['forcing_contribution'].items():
            composed[key] = joint._q(joint._sum(forcing[key], q['value']), q['unit'])
        result = par.evaluate_rhs(scenario={**scenario, 'forcing': composed},
            solar={**solar, 'values': {k: normalized_solar[k] for k in par.SOLAR_UNITS}},
            growth_profile=growth_profile, cohort_profile=cohort_profile,
            transport_profile=transport_profile, exchange_profile=exchange_profile)
        _need(result['joint_rhs']['derived']['leaf_area_index']['value'] == lai,
            'BALANCE_HOLD: different trial LAI')
        base = {**result['scenario'], 'forcing': normalized_forcing}
        sun = {**solar, 'values': normalized_solar}
        weather = {k: outdoor['scenario'][k] for k in ('input_id', 'origin', 'forcing')}
        identity = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
            'source_sha256': {'PAR': par.radiation.SOURCE_SHA256, 'NIR': nir.SOURCE_SHA256,
                'exchange': exchange_profile.source_sha256},
            'notice_sha256': {'PAR': par.radiation.NOTICE_SHA256, 'NIR': nir.NOTICE_SHA256,
                'exchange': exchange_profile.notice_sha256},
            'component_code_sha256': {'PAR_joint': par.CODE_SHA256, 'PAR': par.radiation.CODE_SHA256,
                'NIR': nir.CODE_SHA256, 'ventilation': vent.CODE_SHA256, 'joint_RHS': joint.CODE_SHA256},
            'policy_sha256': joint._hash({'composition': POLICY, 'PAR': result['policy_sha256'],
                'NIR': boundary['policy_sha256'], 'ventilation': outdoor['policy_sha256']}),
            'input_sha256': joint._hash({'scenario': base, 'solar': sun, 'ventilation': weather}),
            'PAR_joint_calculation_sha256': result['calculation_sha256'],
            'NIR_calculation_sha256': boundary['calculation_sha256'],
            'ventilation_input_sha256': outdoor['input_sha256']}
        return {**identity, 'calculation_sha256': joint._hash(identity), 'scenario': base,
            'solar': sun, 'ventilation': weather, 'PAR_joint': result, 'NIR': boundary, 'outdoor': outdoor,
            'joint_rhs': result['joint_rhs'], 'heat_composition': {
                'canopy_non_solar_heat': normalized_forcing['canopy_non_solar_heat'],
                'canopy_absorbed_nir': nir_heat,
                'canopy_absorbed_par': result['heat_composition']['canopy_absorbed_par'],
                'canopy_external_heat': result['heat_composition']['canopy_external_heat']},
            'scope': 'software_research_only', 'claim_scope': 'synthetic_current_state_solar_ventilation_rhs_only',
            'G0_G4': 'not_assessed', 'time_coordinate': 'derivatives_per_second_no_time_advance'}
    except (joint.JointClimateHold, nir.RadiationNIRHold, vent.VentilationHold) as exc:
        raise SolarJointHold(str(exc)) from exc
    except (OverflowError, ZeroDivisionError) as exc:
        raise SolarJointHold('NUMERIC_HOLD: unrepresentable arithmetic') from exc
