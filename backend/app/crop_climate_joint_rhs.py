"""One shared crop/climate trial; crop-climate-joint-rhs-v1.md defines scope."""
from hashlib import sha256
import json
from math import exp, fsum, isfinite
from pathlib import Path

from . import crop_growth_rates as growth
from . import crop_fruit_cohorts as fruit
from . import crop_plant_cohort_rates as plant_contract
from . import crop_plant_startup_rates as crop
from . import crop_canopy_exchange as exchange
from . import crop_canopy_energy_transport as inventory
from .crop_fruit_transport import ReferenceFruitTransportParameters

VERSION = 'signed-energy-crop-climate-stage-research-v1'
STATE_SCHEMA = 'crop-climate-stage-state-v1'
CLOCK_CONTRACT = 'dynamic-canopy-temperature-history-rhs-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256 = {name: sha256(Path(__file__).with_name(name+'.py').read_bytes()).hexdigest()
    for name in ('crop_growth_rates','crop_fruit_cohorts','crop_fruit_transport','crop_fruit_allocation','crop_fruit_startup',
        'crop_plant_cohort_rates','crop_plant_startup_rates','crop_canopy_exchange','crop_canopy_energy_transport')}
CLIMATE_UNITS = {'canopy_sensible_energy':'J/m2_floor','air_temperature':'degC',
    'air_vapor_mass':'kg_water/m2_floor'}
PARAMETER_UNITS = {'leaf_heat_capacity':'J/m2_leaf/K','air_volume_per_floor_area':'m3/m2_floor',
    'air_capacity_density':'kg_air/m3','canopy_vapor_resistance':'s/m',
    'vapor_gas_constant':'J/kg_water/K','reference_temperature':'degC'}
FORCING_UNITS = {'canopy_external_heat':'W/m2_floor','air_external_sensible_heat':'W/m2_floor',
    'air_external_vapor':'kg_water/m2_floor/s','incoming_capacity_temperature':'degC',
    'par_above_canopy':'umol_photons/m2_floor/s','co2':'ppm'}
SCALAR_BLOCKS = {'plant_state':plant_contract.PLANT_UNITS,'climate_state':CLIMATE_UNITS,
    'parameters':PARAMETER_UNITS,'forcing':FORCING_UNITS,'removals':plant_contract.REMOVAL_UNITS,
    'fruit_entry':plant_contract.ENTRY_UNITS}
ARRAY_BLOCKS = {'cohort_state':{k:fruit.ARRAY_UNITS[k] for k in ('fruit_carbohydrate','fruit_number')},
    'relative_growth_rate':{'fruit_relative_growth_rate':'1/s'}}


class JointClimateHold(ValueError):
    """No joint trial result is supplied outside the explicit research boundary."""


def _need(condition, reason):
    if not condition:
        raise JointClimateHold(reason)


def _q(value, unit):
    return {'value':value,'unit':unit}


def _number(value):
    _need(type(value) in (int,float), 'INPUT_HOLD: explicit numeric value required')
    try:
        value = float(value)
    except OverflowError as exc:
        raise JointClimateHold('NUMERIC_HOLD: unrepresentable input') from exc
    _need(isfinite(value), 'INPUT_HOLD: finite quantity required')
    return value


def _quantities(block, units, *, arrays=False):
    _need(type(block) is dict and set(block)==set(units), 'INPUT_HOLD: closed quantities required')
    numbers, normalized = {}, {}
    for name,unit in units.items():
        records = block[name]
        if arrays:
            _need(type(records) is list and len(records)==50, 'INPUT_HOLD: exactly 50 cohort quantities required')
        else:
            records = [records]
        values = []
        for row in records:
            _need(type(row) is dict and set(row)=={'value','unit'}, 'INPUT_HOLD: closed quantity required')
            _need(type(row['unit']) is str and row['unit']==unit, 'UNIT_HOLD: '+name)
            values.append(_number(row['value']))
        numbers[name] = values if arrays else values[0]
        normalized[name] = [_q(v,unit) for v in values] if arrays else _q(values[0],unit)
    return numbers, normalized


def _sum(*values):
    try:
        value = fsum(values)
    except (OverflowError,ValueError) as exc:
        raise JointClimateHold('NUMERIC_HOLD: sum overflow') from exc
    _need(isfinite(value), 'NUMERIC_HOLD: nonfinite sum')
    return value


def _product(a,b):
    value = a*b
    _need(isfinite(value) and (a==0 or b==0 or value!=0), 'NUMERIC_HOLD: product overflow or underflow')
    return value


def _divide(a,b):
    value = a/b
    _need(isfinite(value) and (a==0 or value!=0), 'NUMERIC_HOLD: quotient overflow or underflow')
    return value


def _hash(value):
    return sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def _block(name, values, origin):
    return {'input_id':'joint-stage-'+name,'origin':origin,'values':values}


def _ledger(terms, *, scale_terms=None):
    residual = _sum(*terms)
    budget = _product(3e-13,_sum(*(abs(v) for v in (terms if scale_terms is None else scale_terms))))
    _need(abs(residual)<=budget, 'BALANCE_HOLD: unresolved joint ledger')
    return residual,budget


def evaluate_rhs(*, scenario, growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Evaluate crop, exchange and represented capacity from one closed shared trial."""
    _need(type(growth_profile) is growth.ReferenceParameters
        and type(cohort_profile) is fruit.ReferenceFruitCohortParameters
        and type(transport_profile) is ReferenceFruitTransportParameters
        and type(exchange_profile) is exchange.ReferenceParameters, 'PROFILE_HOLD: four pinned profiles required')
    _need(type(scenario) is dict and set(scenario)=={'input_id','origin',*SCALAR_BLOCKS,*ARRAY_BLOCKS},
        'INPUT_HOLD: closed joint scenario required')
    _need(type(scenario['input_id']) is str and 1<=len(scenario['input_id'])<=200
        and bool(scenario['input_id'].strip()) and type(scenario['origin']) is str
        and scenario['origin'] in ('synthetic','reference_calculation'), 'INPUT_HOLD: research provenance required')
    numbers,normalized = {}, {'input_id':scenario['input_id'],'origin':scenario['origin']}
    for name,units in {**SCALAR_BLOCKS,**ARRAY_BLOCKS}.items():
        numbers[name],normalized[name] = _quantities(scenario[name],units,arrays=name in ARRAY_BLOCKS)
    s,p,f,c = (numbers[k] for k in ('plant_state','parameters','forcing','climate_state'))
    _need(s['leaf']>=0, 'STATE_HOLD: negative leaf inventory')
    _need(s['leaf']>0, 'EMPTY_CANOPY_HOLD: no empty transition')
    _need(all(p[k]>0 for k in PARAMETER_UNITS if k!='reference_temperature'),
        'INPUT_HOLD: positive explicit parameters required')
    _need(c['air_vapor_mass']>=0, 'STATE_HOLD: negative vapor inventory')
    lai = _product(growth_profile.values['sla'],s['leaf'])
    ccan = _product(p['leaf_heat_capacity'],lai)
    offset = _divide(c['canopy_sensible_energy'],ccan)
    tc = _sum(p['reference_temperature'],offset)
    _need(abs(_sum(tc,-p['reference_temperature'],-offset))<=2e-13,
        'NUMERIC_HOLD: stored temperature resolution')
    low,high = exchange_profile.temperature_bounds
    _need(all(low<=v<=high for v in (tc,c['air_temperature'],f['incoming_capacity_temperature'])),
        'TEMPERATURE_HOLD: outside synthetic temperature window')
    cair = _product(_product(p['air_volume_per_floor_area'],p['air_capacity_density']),
        exchange_profile.values['air_heat_capacity'])
    pressure = _product(_product(_divide(c['air_vapor_mass'],p['air_volume_per_floor_area']),
        p['vapor_gas_constant']),_sum(c['air_temperature'],273.15))
    constants = exchange_profile.values
    saturation = constants['saturation_pressure_coefficient']*exp(
        constants['saturation_exponent_factor']*c['air_temperature'] /
        (c['air_temperature']+constants['saturation_denominator_offset']))
    _need(pressure<saturation, 'BULK_SATURATION_HOLD: no condensation closure')
    origin = scenario['origin']
    try:
        crop_forcing = {k:normalized['forcing'][k] for k in growth.FORCING_UNITS if k!='canopy_temperature'}
        crop_forcing['canopy_temperature'] = _q(tc,'degC')
        cohort_values = {**normalized['cohort_state'],**normalized['relative_growth_rate'],
            **{k:normalized['plant_state'][k] for k in fruit.SCALAR_UNITS}}
        plant = crop.calculate_plant_startup_rates(state=_block('plant',normalized['plant_state'],origin),
            cohort_state=_block('cohorts',cohort_values,origin),forcing=_block('crop-forcing',crop_forcing,origin),
            removals=_block('removals',normalized['removals'],origin),fruit_entry=_block('entry',normalized['fruit_entry'],origin),
            growth_profile=growth_profile,cohort_profile=cohort_profile,transport_profile=transport_profile)
        _need(plant['lai']['value']==lai, 'BALANCE_HOLD: conflicting same-stage LAI')
        transferred = exchange.calculate_exchange(profile=exchange_profile,forcing=_block('exchange',{
            'leaf_area_index':_q(lai,'m2_leaf/m2_floor'),'canopy_temperature':_q(tc,'degC'),
            'air_temperature':normalized['climate_state']['air_temperature'],'air_vapor_pressure':_q(pressure,'Pa'),
            'air_capacity_density':normalized['parameters']['air_capacity_density'],
            'canopy_vapor_resistance':normalized['parameters']['canopy_vapor_resistance']},origin))
        material = inventory.calculate_transport(profile=growth_profile,forcing=_block('capacity',{
            'leaf_carbohydrate':normalized['plant_state']['leaf'],'leaf_allocation':plant['allocation']['leaf'],
            'leaf_maintenance':plant['vegetative_maintenance']['leaf'],'leaf_removal':plant['removals']['leaf'],
            'leaf_heat_capacity':normalized['parameters']['leaf_heat_capacity'],'canopy_temperature':_q(tc,'degC'),
            'incoming_capacity_temperature':normalized['forcing']['incoming_capacity_temperature'],
            'reference_temperature':normalized['parameters']['reference_temperature']},origin))
    except (crop.PlantStartupHold,exchange.CanopyExchangeHold,inventory.CanopyEnergyHold) as exc:
        raise JointClimateHold(str(exc)) from exc
    _need(material['canopy_capacity']['value']==ccan, 'BALANCE_HOLD: conflicting same-stage capacity')
    e,h,le = (transferred['exchange'][k]['value'] for k in ('water_vapor','sensible_heat','latent_heat'))
    qmaterial = material['energy_flows']['net']['value']
    cdot = material['capacity_rates']['net']['value']
    du = _sum(f['canopy_external_heat'],-h,-le,qmaterial)
    da = _divide(_sum(f['air_external_sensible_heat'],h),cair)
    dm = _sum(e,f['air_external_vapor'])
    tc_rate = _divide(_sum(du,-_product(offset,cdot)),ccan)
    air_storage = _product(cair,da)
    latent_storage = _product(constants['latent_heat'],dm)
    external_latent = _product(constants['latent_heat'],f['air_external_vapor'])
    capacity_from_crop = _product(p['leaf_heat_capacity'],_product(growth_profile.values['sla'],plant['derivatives']['leaf']['value']))
    ledgers = {
        'canopy_sensible':_ledger((du,-f['canopy_external_heat'],h,le,-qmaterial)),
        'air_sensible':_ledger((air_storage,-f['air_external_sensible_heat'],-h)),
        'vapor_and_water_boundaries':_ledger((dm,-e,-f['air_external_vapor'])),
        'reduced_energy':_ledger((du,air_storage,latent_storage,-f['canopy_external_heat'],
            -f['air_external_sensible_heat'],-external_latent,-qmaterial)),
        'crop_capacity':_ledger((cdot,-capacity_from_crop),scale_terms=(cdot,capacity_from_crop,
            *(material['capacity_rates'][k]['value'] for k in ('allocation','maintenance','removal'))))}
    ledger_units = {'canopy_sensible':'W/m2_floor','air_sensible':'W/m2_floor',
        'vapor_and_water_boundaries':'kg_water/m2_floor/s','reduced_energy':'W/m2_floor',
        'crop_capacity':'J/m2_floor/K/s'}
    identity = {'model_version':VERSION,'state_schema_version':STATE_SCHEMA,'clock_contract':CLOCK_CONTRACT,
        'code_sha256':CODE_SHA256,'component_code_sha256':dict(COMPONENT_CODE_SHA256),
        'profile_sha256':{k:v.sha256 for k,v in (('growth',growth_profile),('cohort',cohort_profile),
            ('transport',transport_profile),('exchange',exchange_profile))},
        'policy_sha256':plant['policy_sha256'],'input_sha256':_hash(normalized)}
    return {**identity,'calculation_sha256':_hash(identity),'scenario':normalized,
        'scope':'software_research_only','claim_scope':'synthetic_joint_crop_climate_rhs_only','G0_G4':'not_assessed',
        'time_coordinate':'derivatives_per_second_no_time_advance',
        'derived':{'canopy_temperature':_q(tc,'degC'),'leaf_area_index':_q(lai,'m2_leaf/m2_floor'),
            'canopy_capacity':_q(ccan,'J/m2_floor/K'),'air_capacity':_q(cair,'J/m2_floor/K'),
            'air_vapor_pressure':_q(pressure,'Pa'),'canopy_temperature_rate':_q(tc_rate,'K/s')},
        'derivatives':{'plant':plant['derivatives'],'cohorts':plant['cohorts']['derivatives'],
            'climate':{'canopy_sensible_energy':_q(du,'W/m2_floor'),'air_temperature':_q(da,'K/s'),
                'air_vapor_mass':_q(dm,'kg_water/m2_floor/s')}},
        'crop':plant,'exchange':transferred,'capacity_transport':material,
        'canopy_water_boundary':_q(-e,'kg_water/m2_floor/s'),
        'balance_residuals':{**plant['balance_residual'],**{k:_q(v[0],ledger_units[k]) for k,v in ledgers.items()}},
        'balance_budgets':{**plant['balance_budget'],**{k:_q(v[1],ledger_units[k]) for k,v in ledgers.items()}}}
