"""Compile explicit user intent to unpublished, immutable thermal kernel inputs."""

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite

from .economic_contracts import untrusted_data
from .farm_inputs import FarmInputs, canonical_farm_inputs
from .jobs import canonical_input_bytes
from .thermal import (ENGINE_VERSION, UNIT_REGISTRY_VERSION, ThermalHold, _indoor,
                      _read_inputs, _sourced_copy)
from .thermal_run_store import snapshot_id_for
from .thermal_units import saturation_pressure_pa, utc


VERSION = 'farm-input-compiler-v1'


@dataclass(frozen=True)
class CompiledFarmInputs:
    farm_bytes: bytes
    thermal_bytes: bytes

    @property
    def farm_sha256(self):
        return sha256(self.farm_bytes).hexdigest()

    @property
    def thermal_sha256(self):
        return sha256(self.thermal_bytes).hexdigest()


def _record(item, pointer, farm_sha256):
    value=float(item.amount) if hasattr(item,'amount') else item.value
    if type(value) is float and (not isfinite(value) or item.amount != 0 and value == 0):
        raise ThermalHold('INPUT_HOLD: farm quantity not representable in binary64')
    return dict(value=value,unit=getattr(item,'unit','1'),origin='assumed',
                basis_ref=f'farm-inputs-sha256:{farm_sha256}#{pointer}',version=item.revision,
                user_evidence=item.model_dump(mode='json'))


def compile_farm_inputs(value, manifest_bytes, weather_bytes, parameter_bytes, *, review_at_utc):
    farm=FarmInputs.model_validate(untrusted_data(value))
    raw_sources=(manifest_bytes,weather_bytes,parameter_bytes)
    if any(type(raw) is not bytes or not 1 <= len(raw) <= 131072 for raw in raw_sources):
        raise ValueError('farm template bytes rejected')
    if farm.decision_at > utc(review_at_utc):
        raise ValueError('farm review precedes decision')
    _,weather,template,_=_read_inputs(*raw_sources,review_at_utc,
        decision_at_utc=farm.decision_at.isoformat().replace('+00:00','Z'),claim_mode='ex_post_replay')
    if snapshot_id_for(*raw_sources) != farm.snapshot_id:
        raise ValueError('farm template snapshot differs')
    farm_bytes=canonical_farm_inputs(farm)
    digest=sha256(farm_bytes).hexdigest()
    parameters=deepcopy(template['parameters'])
    for name in ('floor_area','indoor_volume','effective_heat_capacity','dry_air_mass',
                 'envelope_conductance','absorbed_solar_fraction'):
        parameters[name]=_record(getattr(farm.facility,name),f'/facility/{name}',digest)
    initial={name:_record(getattr(farm.initial_state,name),f'/initial_state/{name}',digest)
             for name in ('temperature','humidity_ratio')}
    heater={name:getattr(farm.heater,name) for name in ('mode','capacity_basis','control_version')}
    heater.update({name:_record(getattr(farm.heater,name),f'/heater/{name}',digest)
                   for name in ('capacity','setpoint','available')})
    _indoor((initial['temperature']['value'],initial['humidity_ratio']['value']),parameters)
    if len(farm.forcing) != len(weather['intervals']):
        raise ValueError('farm forcing coverage differs')
    intervals=[]
    for index,(entry,weather_hour) in enumerate(zip(farm.forcing,weather['intervals'])):
        start,end=(utc(weather_hour[key]) for key in ('start_utc','end_utc'))
        if entry.start != start or entry.end != end:
            raise ValueError('farm forcing interval differs')
        raw=weather_hour['values']
        forcing={name:_sourced_copy(raw[key]) for name,key in (
            ('outdoor_temperature','T_o'),('outdoor_relative_humidity','phi_o'),
            ('outdoor_pressure','p_o'),('solar_interval_energy','solar_interval_energy'))}
        for name in ('ventilation_dry_air_flow','canopy_evaporation','ground_heat_flow'):
            forcing[name]=_record(getattr(entry,name),f'/forcing/{index}/{name}',digest)
        ventilation=forcing['ventilation_dry_air_flow']['value']
        mass=parameters['dry_air_mass']['value']
        conductance=parameters['envelope_conductance']['value']
        capacity=parameters['effective_heat_capacity']['value']
        specific_heat=parameters['dry_air_specific_heat']['value']
        if 60*ventilation/mass > 1 or 60*(conductance+ventilation*specific_heat)/capacity > 1:
            raise ThermalHold('STABILITY_HOLD: authored Euler step unstable')
        outdoor_t=float(raw['T_o']['value'])
        pressure=float(raw['p_o']['value'])
        vapor=float(raw['phi_o']['value'])*saturation_pressure_pa(
            outdoor_t,parameters['saturation_pressure_rule'])
        if pressure <= vapor:
            raise ThermalHold('INPUT_HOLD: outdoor pressure <= vapor pressure')
        humidity=(parameters['dry_air_gas_constant']['value']/parameters['vapor_gas_constant']['value']
                  *vapor/(pressure-vapor))
        solar=(float(raw['solar_interval_energy']['value'])*parameters['floor_area']['value']
               *parameters['absorbed_solar_fraction']['value']/(end-start).total_seconds())
        for name,result,unit in (('outdoor_humidity_ratio',humidity,'kg_v/kg_da'),('solar_gain',solar,'W')):
            plan=template['intervals'][index]['derived_forcing'][name]
            identifiers=[]
            for identifier in plan['input_record_ids']:
                prefix='synthetic-thermal-parameters-v1:/parameters/'
                parameter=identifier.removeprefix(prefix)
                identifiers.append(parameters[parameter]['basis_ref'] if identifier.startswith(prefix)
                    and parameter in ('floor_area','absorbed_solar_fraction') else identifier)
            forcing[name]=dict(value=result,unit=unit,origin='derived',
                basis_ref=f'synthetic-thermal-parameters-v1:/conversion_rules/{name}',version='v1',
                calculation_rule_ref=plan['calculation_rule_ref'],calculation_rule_version='v1',
                input_record_ids=identifiers)
        intervals.append(dict(start=weather_hour['start_utc'],end=weather_hour['end_utc'],forcing=forcing))
    compiled=dict(schema_version='farm-thermal-input-v1',compiler_version=VERSION,
        status='unpublished_candidate',farm_sha256=digest,base_snapshot_id=farm.snapshot_id,
        review_at_utc=review_at_utc,
        base_source_sha256=[sha256(raw).hexdigest() for raw in raw_sources],
        model_version='thermal-v1',engine_version=ENGINE_VERSION,unit_registry_version=UNIT_REGISTRY_VERSION,
        initial_state=initial,parameters=parameters,heater=heater,intervals=intervals,
        missing_evidence=['authored_input_review','authored_snapshot_release'])
    return CompiledFarmInputs(farm_bytes,canonical_input_bytes(compiled))
