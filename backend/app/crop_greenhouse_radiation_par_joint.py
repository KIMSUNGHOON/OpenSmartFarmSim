"""Current-state solar PAR composition; crop-greenhouse-radiation-par-joint-v1.md."""
from hashlib import sha256
from pathlib import Path

from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_radiation_par as radiation
from .crop_growth_rates import ReferenceParameters

VERSION = 'current-state-solar-par-joint-rhs-research-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
FORCING_UNITS = {k: v for k, v in joint.FORCING_UNITS.items()
    if k not in ('par_above_canopy', 'canopy_external_heat')}
FORCING_UNITS['canopy_non_par_heat'] = radiation.HEAT
SOLAR_UNITS = {k: v for k, v in radiation.INPUT_UNITS.items() if k != 'leaf_area_index'}
POLICY = {'LAI': 'pinned_SLA_times_current_leaf', 'crop': 'replace_incident_PAR_once',
    'heat': 'absorbed_PAR_plus_explicit_non_PAR_once', 'evaluation': 'one_PAR_then_one_joint_RHS',
    'unresolved_and_floor_radiation': 'no_canopy_or_air_credit'}


class RadiationPARJointHold(joint.JointClimateHold):
    """No current-state result outside the explicit PAR composition contract."""


def _need(condition, reason):
    if not condition:
        raise RadiationPARJointHold(reason)


def evaluate_rhs(*, scenario, solar, growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Compose current LAI, incident photons and absorbed PAR without advancing time."""
    try:
        _need(type(growth_profile) is ReferenceParameters, 'PROFILE_HOLD: pinned growth profile required')
        _need(type(scenario) is dict and set(scenario) == {'input_id', 'origin', *joint.SCALAR_BLOCKS,
            *joint.ARRAY_BLOCKS}, 'INPUT_HOLD: closed joint scenario required')
        _need(type(solar) is dict and set(solar) == {'input_id', 'origin', 'values'}
            and type(solar['values']) is dict and set(solar['values']) == set(SOLAR_UNITS),
            'INPUT_HOLD: solar values must exclude caller LAI')
        _need(solar['origin'] == scenario['origin'], 'INPUT_HOLD: mixed research origins')
        forcing, normalized_forcing = joint._quantities(scenario['forcing'], FORCING_UNITS)
        plant, _ = joint._quantities(scenario['plant_state'], joint.SCALAR_BLOCKS['plant_state'])
        _need(plant['leaf'] > 0, 'EMPTY_CANOPY_HOLD: positive current leaf inventory required')
        lai = joint._product(growth_profile.values['sla'], plant['leaf'])
        boundary = radiation.calculate_par(profile=growth_profile, scenario={**solar,
            'values': {**solar['values'], 'leaf_area_index': joint._q(lai, 'm2_leaf/m2_floor')}})
        par_heat = boundary['heat_components']['canopy_absorbed_par']
        combined_heat = joint._q(joint._sum(forcing['canopy_non_par_heat'], par_heat['value']), radiation.HEAT)
        composed = {k: v for k, v in normalized_forcing.items() if k != 'canopy_non_par_heat'}
        composed.update(canopy_external_heat=combined_heat,
            par_above_canopy=boundary['crop_forcing']['par_above_canopy'])
        result = joint.evaluate_rhs(scenario={**scenario, 'forcing': composed},
            growth_profile=growth_profile, cohort_profile=cohort_profile,
            transport_profile=transport_profile, exchange_profile=exchange_profile)
        _need(result['derived']['leaf_area_index']['value'] == lai, 'BALANCE_HOLD: different trial LAI')
        normalized = {**result['scenario'], 'forcing': normalized_forcing}
        normalized_solar = {**boundary['scenario'], 'values': {k: v for k, v in boundary['scenario']['values'].items()
            if k != 'leaf_area_index'}}
        identity = {'model_version': VERSION, 'code_sha256': CODE_SHA256,
            'policy_sha256': joint._hash(POLICY), 'radiation_code_sha256': radiation.CODE_SHA256,
            'joint_calculation_sha256': result['calculation_sha256'],
            'radiation_input_sha256': boundary['input_sha256'],
            'input_sha256': joint._hash({'scenario': normalized, 'solar': normalized_solar})}
        return {**identity, 'calculation_sha256': joint._hash(identity),
            'scenario': normalized, 'solar': normalized_solar,
            'scope': 'software_research_only', 'claim_scope': 'synthetic_current_state_PAR_joint_rhs_only',
            'G0_G4': 'not_assessed', 'time_coordinate': 'derivatives_per_second_no_time_advance',
            'heat_composition': {'canopy_non_par_heat': normalized_forcing['canopy_non_par_heat'],
                'canopy_absorbed_par': par_heat, 'canopy_external_heat': combined_heat},
            'radiation': boundary, 'joint_rhs': result}
    except (radiation.RadiationPARHold, joint.JointClimateHold) as exc:
        raise RadiationPARJointHold(str(exc)) from exc
