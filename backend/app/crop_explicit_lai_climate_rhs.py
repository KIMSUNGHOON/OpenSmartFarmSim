"""Same-stage explicit geometry; crop-explicit-lai-climate-rhs-v1.md."""
from copy import deepcopy
from hashlib import sha256
import json
from math import exp, isfinite
from pathlib import Path
import re

from . import crop_explicit_lai_carbon_cohorts as carbon
from . import crop_area_canopy_energy as area
from . import crop_canopy_exchange as exchange

MODEL_VERSION='explicit-lai-crop-climate-stage-research-v1'
STATE_SCHEMA='explicit-lai-crop-climate-stage-v1'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
COMPONENT_CODE_SHA256={**carbon.COMPONENT_CODE_SHA256,
    **{m.__name__:sha256(Path(m.__file__).read_bytes()).hexdigest()for m in (carbon,area,area.numeric,exchange)}}
CLIMATE_UNITS={'canopy_sensible_energy':'J/m2_floor','air_temperature':'degC','air_vapor_mass':'kg_water/m2_floor'}
PARAMETER_UNITS={'leaf_heat_capacity':'J/m2_leaf/K','air_volume_per_floor_area':'m3/m2_floor',
    'air_capacity_density':'kg_air/m3','canopy_vapor_resistance':'s/m',
    'vapor_gas_constant':'J/kg_water/K','reference_temperature':'degC'}
FORCING_UNITS={'canopy_external_heat':'W/m2_floor','air_external_sensible_heat':'W/m2_floor',
    'air_external_vapor':'kg_water/m2_floor/s','incoming_capacity_temperature':'degC',
    'outgoing_capacity_temperature':'degC','par_above_canopy':'umol_photons/m2_floor/s','co2':'ppm'}
GEOMETRY_UNITS={'model_floor_area':'m2_floor','leaf_area_index':'m2_leaf/m2_floor',
    'leaf_area_index_rate':'m2_leaf/m2_floor/s'}
SCALAR_BLOCKS={'plant_state':carbon.original.PLANT_UNITS,'climate_state':CLIMATE_UNITS,
    'parameters':PARAMETER_UNITS,'forcing':FORCING_UNITS,'removals':carbon.original.REMOVAL_UNITS,
    'fruit_entry':carbon.original.ENTRY_UNITS,'geometry':GEOMETRY_UNITS,
    'capacity_transport':{name:area.numeric.CAPACITY_RATE for name in ('capacity_inflow','capacity_outflow')}}
ARRAY_BLOCKS={'cohort_state':{name:carbon.fruit.ARRAY_UNITS[name]for name in ('fruit_carbohydrate','fruit_number')},
    'relative_growth_rate':{'fruit_relative_growth_rate':'1/s'}}
numeric=area.numeric


class ExplicitLaiClimateHold(ValueError):
    pass


def _need(condition,reason):
    if not condition:raise ExplicitLaiClimateHold(reason)


def _canonical(value):
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
    _need(len(raw)<=128*1024,'CAPACITY_HOLD: bounded explicit joint input/output required')
    return raw


def _quantities(block,units,arrays=False):
    _need(type(block)is dict and set(block)==set(units),'INPUT_HOLD: closed quantity block required')
    numbers,normalized={},{}
    for name,unit in units.items():
        rows=block[name]if arrays else[block[name]]
        _need(type(rows)is list and len(rows)==(50 if arrays else 1),'INPUT_HOLD: exactly 50 array quantities required')
        values=[]
        for row in rows:
            _need(type(row)is dict and set(row)=={'value','unit'},'INPUT_HOLD: closed quantity required')
            _need(row['unit']==unit,'UNIT_HOLD: '+name)
            _need(type(row['value'])in(int,float),'INPUT_HOLD: numeric quantity required')
            v=float(row['value']);_need(isfinite(v),'NUMERIC_HOLD: finite quantity required');values.append(v)
        numbers[name]=values if arrays else values[0]
        normalized[name]=[numeric._q(v,unit)for v in values]if arrays else numeric._q(values[0],unit)
    return numbers,normalized


def _block(name,values):return {'input_id':'explicit-joint-'+name,'origin':'synthetic','values':values}


def _ledger(terms):
    residual=numeric._sum(*terms);budget=numeric._multiply(3e-13,numeric._sum(*map(abs,terms)))
    _need(abs(residual)<=budget,'BALANCE_HOLD: unresolved explicit joint ledger')
    return residual,budget


def evaluate_rhs(*,scenario,growth_profile,cohort_profile,transport_profile,exchange_profile):
    try:
        _need(type(growth_profile)is carbon.source.ReferenceParameters
            and type(cohort_profile)is carbon.fruit.ReferenceFruitCohortParameters
            and type(transport_profile)is carbon.transport.ReferenceFruitTransportParameters
            and type(exchange_profile)is exchange.ReferenceParameters,'PROFILE_HOLD: four pinned profiles required')
        raw=_canonical(scenario);captured=json.loads(raw)
        _need(type(captured)is dict and set(captured)=={'input_id','origin',*SCALAR_BLOCKS,*ARRAY_BLOCKS},
              'INPUT_HOLD: closed explicit joint scenario required')
        _need(type(captured['input_id'])is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}',captured['input_id'])
            and captured['origin']=='synthetic','SCOPE_HOLD: bounded explicitly synthetic stage required')
        n={};normalized={name:captured[name]for name in ('input_id','origin')}
        for name,units in {**SCALAR_BLOCKS,**ARRAY_BLOCKS}.items():
            n[name],normalized[name]=_quantities(captured[name],units,name in ARRAY_BLOCKS)
        s,c,p,f,g,flow=(n[name]for name in ('plant_state','climate_state','parameters','forcing','geometry','capacity_transport'))
        _need(all(p[name]>0 for name in PARAMETER_UNITS if name!='reference_temperature'),
              'INPUT_HOLD: positive explicit physical parameters required')
        _need(g['model_floor_area']>0 and g['leaf_area_index']>0,'EMPTY_CANOPY_HOLD: positive explicit area/basis required')
        _need(c['air_vapor_mass']>=0,'STATE_HOLD: negative vapor inventory')
        capacity=numeric._multiply(p['leaf_heat_capacity'],g['leaf_area_index'])
        offset=numeric._divide(c['canopy_sensible_energy'],capacity)
        tc=numeric._sum(p['reference_temperature'],offset)
        _need(abs(numeric._sum(tc,-p['reference_temperature'],-offset))<=numeric.TEMPERATURE_TOLERANCE,
              'NUMERIC_HOLD: stored canopy temperature resolution')
        for value in (tc,c['air_temperature'],f['incoming_capacity_temperature'],f['outgoing_capacity_temperature']):numeric._temperature(value)
        constants=exchange_profile.values
        air_capacity=numeric._multiply(numeric._multiply(p['air_volume_per_floor_area'],p['air_capacity_density']),constants['air_heat_capacity'])
        pressure=numeric._multiply(numeric._multiply(numeric._divide(c['air_vapor_mass'],p['air_volume_per_floor_area']),
            p['vapor_gas_constant']),numeric._sum(c['air_temperature'],273.15))
        saturation=numeric._multiply(constants['saturation_pressure_coefficient'],exp(
            constants['saturation_exponent_factor']*c['air_temperature']/(c['air_temperature']+constants['saturation_denominator_offset'])))
        _need(pressure<saturation,'BULK_SATURATION_HOLD: no condensation closure')
        q=numeric._q;canopy_temperature=q(tc,'degC')
        plant=carbon.calculate_plant_rates(state=_block('plant',normalized['plant_state']),
            cohort_state=_block('cohorts',{**normalized['cohort_state'],**normalized['relative_growth_rate'],
                **{name:normalized['plant_state'][name]for name in carbon.fruit.SCALAR_UNITS}}),
            forcing=_block('crop-forcing',{'canopy_temperature':canopy_temperature,
                **{name:normalized['forcing'][name]for name in ('par_above_canopy','co2')}}),
            removals=_block('removals',normalized['removals']),fruit_entry=_block('entry',normalized['fruit_entry']),
            geometry=_block('geometry',{'leaf_area_index':normalized['geometry']['leaf_area_index']}),
            growth_profile=growth_profile,cohort_profile=cohort_profile,transport_profile=transport_profile)
        transferred=exchange.calculate_exchange(profile=exchange_profile,forcing=_block('exchange',{
            'leaf_area_index':normalized['geometry']['leaf_area_index'],'canopy_temperature':canopy_temperature,
            'air_temperature':normalized['climate_state']['air_temperature'],'air_vapor_pressure':q(pressure,'Pa'),
            **{name:normalized['parameters'][name]for name in ('air_capacity_density','canopy_vapor_resistance')}}))
        e,h,le=(transferred['exchange'][name]['value']for name in ('water_vapor','sensible_heat','latent_heat'))
        nonmaterial=numeric._sum(f['canopy_external_heat'],-h,-le)
        material=area.calculate_area_energy(inputs=_block('area-energy',{
            **{name:normalized['geometry'][name]for name in ('leaf_area_index','leaf_area_index_rate')},
            **{name:normalized['parameters'][name]for name in ('leaf_heat_capacity','reference_temperature')},
            **normalized['capacity_transport'],'canopy_temperature':canopy_temperature,
            **{name:normalized['forcing'][name]for name in ('incoming_capacity_temperature','outgoing_capacity_temperature')},
            'nonmaterial_heat':q(nonmaterial,numeric.POWER)}))
        _need(plant['lai']['value']==g['leaf_area_index']and material['canopy_capacity']['value']==capacity,
              'STATE_MISMATCH_HOLD: shared area or capacity differs')
        _need(abs(numeric._sum(numeric._divide(material['canopy_sensible_energy']['value'],capacity),-offset))<=numeric.TEMPERATURE_TOLERANCE,
              'NUMERIC_HOLD: reconstructed canopy energy resolution')
        du=material['energy_flows']['total']['value'];qmaterial=material['energy_flows']['material']['value']
        da=numeric._divide(numeric._sum(f['air_external_sensible_heat'],h),air_capacity)
        dm=numeric._sum(e,f['air_external_vapor'])
        _need(c['air_vapor_mass']!=0 or dm>=0,'DEPLETED_STATE_HOLD: outward vapor derivative at zero storage')
        air_storage=numeric._multiply(air_capacity,da);latent_storage=numeric._multiply(constants['latent_heat'],dm)
        external_latent=numeric._multiply(constants['latent_heat'],f['air_external_vapor'])
        ledgers={name:(_ledger(terms),unit)for name,terms,unit in (
            ('canopy_sensible',(du,-f['canopy_external_heat'],h,le,-qmaterial),numeric.POWER),
            ('air_sensible',(air_storage,-f['air_external_sensible_heat'],-h),numeric.POWER),
            ('vapor_and_water_boundaries',(dm,-e,-f['air_external_vapor']),exchange.WATER_UNIT),
            ('reduced_energy',(du,air_storage,latent_storage,-f['canopy_external_heat'],
                -f['air_external_sensible_heat'],-external_latent,-qmaterial),numeric.POWER))}
        identity={'model_version':MODEL_VERSION,'state_schema_version':STATE_SCHEMA,'code_sha256':CODE_SHA256,
            'component_code_sha256':dict(COMPONENT_CODE_SHA256),'profile_sha256':{name:profile.sha256 for name,profile in (
                ('growth',growth_profile),('cohort',cohort_profile),('transport',transport_profile),('exchange',exchange_profile))},
            'policy_id':'explicit-area-gross-capacity-shared-stage-v1','scenario':deepcopy(normalized),
            'component_input_sha256':{'carbon':plant['input_sha256'],'exchange':transferred['input_sha256'],'area':material['input_sha256']}}
        result={**identity,'input_sha256':sha256(_canonical(identity)).hexdigest(),'raw_input_sha256':sha256(raw).hexdigest(),
            'scope':'software_research_only','claim_scope':'synthetic_explicit_lai_joint_rhs_only','G0_G4':'not_assessed',
            'time_coordinate':'derivatives_per_second_no_time_advance',
            'derived':{'canopy_temperature':canopy_temperature,'leaf_area_index':q(g['leaf_area_index'],'m2_leaf/m2_floor'),
                'leaf_area_index_rate':q(g['leaf_area_index_rate'],'m2_leaf/m2_floor/s'),'canopy_capacity':q(capacity,numeric.CAPACITY),
                'air_capacity':q(air_capacity,numeric.CAPACITY),'air_vapor_pressure':q(pressure,'Pa'),
                'canopy_temperature_rate':deepcopy(material['canopy_temperature_rate'])},
            'derivatives':{'plant':plant['derivatives'],'cohorts':plant['cohorts']['derivatives'],
                'climate':{'canopy_sensible_energy':q(du,numeric.POWER),'air_temperature':q(da,'K/s'),'air_vapor_mass':q(dm,exchange.WATER_UNIT)}},
            'crop':plant,'exchange':transferred,'capacity_transport':material,'canopy_water_boundary':q(-e,exchange.WATER_UNIT),
            'balance_residuals':{**plant['balance_residual'],**{'area_'+name:row for name,row in material['balance_residuals'].items()},
                **{name:q(pair[0],unit)for name,(pair,unit)in ledgers.items()}},
            'balance_budgets':{**plant['balance_budget'],**{'area_'+name:row for name,row in material['balance_budgets'].items()},
                **{name:q(pair[1],unit)for name,(pair,unit)in ledgers.items()}}}
        result['calculation_sha256']=sha256(_canonical(result)).hexdigest();_canonical(result)
        return result
    except ExplicitLaiClimateHold:
        raise
    except(carbon.ExplicitLaiCarbonHold,area.AreaCanopyEnergyHold,exchange.CanopyExchangeHold,numeric.CanopyEnergyHold)as exc:
        raise ExplicitLaiClimateHold(str(exc))from None
    except(TypeError,ValueError,OverflowError,ZeroDivisionError,RecursionError):
        raise ExplicitLaiClimateHold('INPUT_HOLD: invalid or unrepresentable explicit joint stage')from None
