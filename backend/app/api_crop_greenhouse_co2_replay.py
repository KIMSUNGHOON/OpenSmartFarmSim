"""Closed projection of original joint quantities; custody authorizes the read."""
from datetime import datetime, timezone
from hashlib import sha256
from fractions import Fraction
from math import isfinite
from pathlib import Path
import re
from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, create_model, model_validator

from .api_crop_replay import _Public, Digest, Name, UtcStamp
from . import crop_greenhouse_co2_result_store as storage

server = storage.server
continuation = server.continuation
driver = continuation.driver
joint = driver.stage.joint
rhs = driver.stage.rhs
solar = rhs.solar_rhs
VERSION = 'joint-co2-solar-replay-v1'
RESULT_ID_PATTERN = r'^joint-co2-solar-result-v1:[0-9a-f]{64}$'
MAX_RESPONSE_BYTES = 2*1024**2
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class ProjectionHold(ValueError):
    """No publishable projection of this original research result."""


def _need(condition):
    if not condition: raise ProjectionHold('joint CO2 display unavailable')


def _float(value):
    _need(type(value) is float and isfinite(value)); return value


def _false(value):
    _need(value is False); return value


FalseApproval = Annotated[Literal[False], BeforeValidator(_false)]
Float = Annotated[float, BeforeValidator(_float)]
Index = Annotated[int, Field(strict=True, ge=0, le=4096)]
_quantities = {}


def _block(name, units, *, arrays=False):
    fields = {}
    for key, unit in units.items():
        if unit not in _quantities:
            _quantities[unit] = create_model('Co2Quantity'+str(len(_quantities)), __base__=_Public,
                value=(Float, ...), unit=(Literal[unit], ...))
        cls = _quantities[unit]
        fields[key] = (Annotated[list[cls], Field(min_length=50, max_length=50)] if arrays else cls, ...)
    return create_model(name, __base__=_Public, **fields)


Plant = _block('Co2Plant', joint.SCALAR_BLOCKS['plant_state'])
Cohorts = _block('Co2Cohorts', joint.ARRAY_BLOCKS['cohort_state'], arrays=True)
Climate = _block('Co2Climate', rhs.CLIMATE_UNITS)
Derived = _block('Co2Derived', {'canopy_temperature': 'degC', 'leaf_area_index': 'm2_leaf/m2_floor',
    'canopy_capacity': 'J/m2_floor/K', 'air_capacity': 'J/m2_floor/K', 'air_vapor_pressure': 'Pa',
    'canopy_temperature_rate': 'K/s', 'air_co2_density': 'mg_CO2/m3', 'crop_co2_ppm': 'ppm'})
Transfers = _block('Co2Transfers', driver.stage.FLUX_UNITS)
EventTotals = _block('Co2EventTotals', driver.EVENT_UNITS)
Balance = _block('Co2Balance', {'carbohydrate': driver.stage.core.MASS, 'number': driver.stage.core.NUMBER,
    **dict.fromkeys(('canopy_sensible', 'air_sensible', 'reduced_energy'), driver.stage.core.ENERGY),
    'vapor_and_water_boundaries': driver.stage.core.WATER, 'crop_capacity': 'J/m2_floor/K',
    'ventilation_sensible_partition': driver.stage.core.ENERGY,
    'ventilation_vapor_partition': driver.stage.core.WATER, 'ventilation_latent_partition': driver.stage.core.ENERGY,
    **dict.fromkeys(('canopy_solar_heat_partition', 'interior_PAR_partition', 'exterior_PAR_partition',
        'virtual_NIR_partition', 'exterior_virtual_NIR_partition'), driver.stage.core.ENERGY),
    'air_co2': driver.stage.CO2_UNIT, 'crop_air_carbon_equivalent': driver.stage.CO2_UNIT})
EventBalance = _block('Co2EventBalance', {'carbohydrate': driver.stage.core.MASS,
    'number': driver.stage.core.NUMBER, 'canopy_sensible': driver.stage.core.ENERGY,
    'crop_capacity': 'J/m2_floor/K', 'temperature': 'K', 'air_co2': driver.stage.CO2_UNIT,
    'air_vapor': driver.stage.core.WATER, 'air_temperature': 'K', 'co2_ppm': 'ppm',
    'crop_air_carbon_equivalent': driver.stage.CO2_UNIT})
Removed = create_model('Co2Removed', __base__=_Public,
    **{k: (v.annotation, ...) for k, v in EventTotals.model_fields.items() if k not in ('fruit_carbohydrate', 'fruit_number')},
    **{k: (v.annotation, ...) for k, v in Cohorts.model_fields.items()})
RemovedTotals = _block('Co2RemovedTotals', {'carbohydrate': driver.stage.core.MASS,
    'number': driver.stage.core.NUMBER, 'co2_basis_carbohydrate': driver.stage.CO2_UNIT})
Profiles = create_model('Co2Profiles', __base__=_Public, **{k: (Digest, ...) for k in continuation.PROFILE_NAMES})
Components = create_model('Co2BaseComponents', __base__=_Public,
    **{k: (Digest, ...) for k in joint.COMPONENT_CODE_SHA256})
_EVENT_COMPONENTS = {**joint.COMPONENT_CODE_SHA256, 'solar': solar.CODE_SHA256, 'gas': rhs.gas.CODE_SHA256,
    'net': rhs.net.CODE_SHA256, 'air_mass': rhs.air.CODE_SHA256,
    'event_primitives': driver.management.previous.CODE_SHA256, 'CO2_RHS': rhs.CODE_SHA256}
EventComponents = create_model('Co2EventComponents', __base__=_Public,
    **{k: (Digest, ...) for k in _EVENT_COMPONENTS})
Co2NetFlows = _block('Co2NetFlows', dict.fromkeys(('air_flux', 'net_crop_uptake'), rhs.air.RATE_UNIT))
Co2AirFlows = _block('Co2AirFlows', dict.fromkeys(('crop_to_air', 'crop_uptake', 'external_to_air',
    'ventilation_to_air', 'ventilation_to_outdoor'), rhs.air.RATE_UNIT))
Co2Exchange = create_model('Co2Exchange', __base__=_Public, net=(Co2NetFlows, ...), air=(Co2AirFlows, ...))


Co2Densities = _block('Co2Densities', dict.fromkeys(('indoor_vapor_density', 'outdoor_vapor_density'), 'kg_water/m3'))
Co2Forcing = _block('Co2Forcing', {'air_external_sensible_heat': 'W/m2_floor', 'air_external_vapor': 'kg_water/m2_floor/s'})



class Co2Diagnostic(_Public):
    input_sha256: Digest
    derived: Co2Densities
    forcing_contribution: Co2Forcing
    latent_energy: _quantities['W/m2_floor']


Co2Heat = _block('Co2Heat', dict.fromkeys(('canopy_non_solar_heat', 'canopy_absorbed_nir',
    'canopy_absorbed_par', 'canopy_external_heat'), 'W/m2_floor'))
Co2PARHeat = _block('Co2PARHeat', dict.fromkeys(('canopy_non_par_heat', 'canopy_absorbed_par', 'canopy_external_heat'), 'W/m2_floor'))
Co2PARForcing = _block('Co2PARForcing', {'par_above_canopy': 'umol_photons/m2_floor/s'})
Co2PARDerived = _block('Co2PARDerived', dict.fromkeys(('outdoor_PAR', 'above_canopy_PAR',
    'canopy_direct_absorbed_PAR', 'canopy_floor_absorbed_PAR'), 'W/m2_floor'))
Co2PARInterior = _block('Co2PARInterior', dict.fromkeys(('canopy_absorbed', 'floor_absorbed',
    'unresolved_reflected', 'upward_transmitted'), 'W/m2_floor'))
Co2PARExterior = _block('Co2PARExterior', dict.fromkeys(('cover_reflected', 'cover_absorbed',
    'construction_intercepted', *Co2PARInterior.model_fields), 'W/m2_floor'))
Co2NIROptics = _block('Co2NIROptics', dict.fromkeys(('virtual_cover_transmittance', 'virtual_floor_transmittance',
    'canopy_transmittance', 'canopy_reflectance', 'canopy_single_pass_absorptance', 'cover_canopy_transmittance',
    'cover_canopy_reflectance_up', 'cover_canopy_reflectance_down', 'cover_canopy_absorptance_up',
    'cover_canopy_absorptance_down', 'canopy_absorptance', 'floor_absorptance', 'upward_reflectance'), '1'))
Co2NIRDenominators = _block('Co2NIRDenominators', dict.fromkeys(('cover_canopy', 'cover_canopy_floor'), '1'))
Co2NIRHeat = _block('Co2NIRHeat', dict.fromkeys(('canopy_absorbed_nir', 'floor_absorbed_nir',
    'upward_virtual_nir', 'construction_unallocated_nir'), 'W/m2_floor'))
Co2NIRDerived = _block('Co2NIRDerived', dict.fromkeys(('outdoor_nir', 'available_virtual_nir'), 'W/m2_floor'))
Co2NIRBalance = _block('Co2NIRBalance', {'cover_canopy_top': '1', 'cover_canopy_bottom': '1',
    'virtual_nir_optics': '1', 'virtual_nir_energy': 'W/m2_floor'})


class Co2PAR(_Public):
    input_sha256: Digest
    crop_forcing: Co2PARForcing
    heat_composition: Co2PARHeat
    diagnostics: Co2PARDerived
    interior_partition: Co2PARInterior
    exterior_PAR_partition: Co2PARExterior


class Co2NIR(_Public):
    input_sha256: Digest
    optics: Co2NIROptics
    reflection_denominators: Co2NIRDenominators
    heat_components: Co2NIRHeat
    diagnostics: Co2NIRDerived
    partition_residuals: Co2NIRBalance
    partition_budgets: Co2NIRBalance





class Co2State(_Public):
    plant_state: Plant
    cohort_state: Cohorts
    climate_state: Climate
    derived: Derived

    @model_validator(mode='after')
    def nonnegative_inventories(self):
        _need(all(getattr(self.plant_state, k).value >= 0 for k in ('buffer', 'leaf', 'stem_root', 'temperature_sum'))
            and all(q.value >= 0 for k in Cohorts.model_fields for q in getattr(self.cohort_state, k))
            and self.climate_state.air_vapor_mass.value >= 0 and self.climate_state.air_co2_mass.value > 0
            and self.derived.air_co2_density.value > 0 and self.derived.crop_co2_ppm.value > 0
            and self.derived.leaf_area_index.value > 0 and self.derived.canopy_capacity.value > 0
            and self.derived.air_capacity.value > 0)
        return self


class Co2Snapshot(Co2State):
    ventilation: Co2Diagnostic
    solar_heat_composition: Co2Heat
    solar_par: Co2PAR
    solar_nir: Co2NIR
    step_index: Index
    elapsed_seconds: Float
    forcing_step_index: Index
    co2_exchange: Co2Exchange
    integrated_transfers: Transfers
    event_totals: EventTotals
    event_count: Annotated[int, Field(strict=True, ge=0, le=128)]
    balance_residuals: Balance
    balance_budgets: Balance
    phase: Literal['initial', 'step-end', 'boundary-after-event', 'forcing-boundary']


class Co2Point(_Public):
    step_index: Index
    at: UtcStamp


class Co2Sample(_Public):
    value: Co2Snapshot
    time: Co2Point
    co2_basis: Literal['wet', 'dry']


class Co2EventState(Co2State):
    input_sha256: Digest
    calculation_sha256: Digest


_CO2_MODULES = (driver, driver.stage, driver.management, rhs, rhs.gas, rhs.net, rhs.air,
    solar, solar.par, solar.par.radiation, solar.nir, solar.vent,
    driver.stage.previous, driver.stage.previous.vent_joint)
_CO2_POLICIES = tuple(module for module in _CO2_MODULES if hasattr(module, 'POLICY'))
Co2SourceDigests = create_model('Co2SourceDigests', __base__=_Public,
    **{k: (Digest, ...) for k in ('gas', 'net', 'air_mass', 'PAR', 'NIR', 'exchange')})
Co2NoticeDigests = create_model('Co2NoticeDigests', __base__=_Public,
    **{k: (Digest, ...) for k in ('PAR', 'NIR', 'exchange')})
Co2ManagementSources = create_model('Co2ManagementSources', __base__=_Public,
    gas=(Digest, ...), net=(Digest, ...), air_mass=(Digest, ...), solar=(Co2NoticeDigests, ...))
Co2ComponentDigests = create_model('Co2ComponentDigests', __base__=_Public,
    **{module.__name__.rsplit('.', 1)[-1]: (Digest, ...) for module in _CO2_MODULES})
Co2PolicyDigests = create_model('Co2PolicyDigests', __base__=_Public,
    **{module.__name__.rsplit('.', 1)[-1]: (Digest, ...) for module in _CO2_POLICIES})


class Co2Management(_Public):
    model_version: Literal['joint-co2-solar-management-research-v1']
    state_schema_version: Literal['crop-solar-co2-stage-state-v1']
    code_sha256: Digest
    component_code_sha256: EventComponents
    event_sha256: Digest
    input_sha256: Digest
    calculation_sha256: Digest
    before_calculation_sha256: Digest
    after_calculation_sha256: Digest
    quantity_rule: Literal['cohort-decimal-rational-removal-v1']
    roundoff_rule: Literal['64-ulp-event-inventory-v1']
    bulk_air_invariants: Literal['exact_zero']
    time_coordinate: Literal['instantaneous_no_clock']
    before: Co2EventState
    after: Co2EventState
    profile_sha256: Profiles
    policy_sha256: Digest
    removed: Removed
    removed_totals: RemovedTotals
    balance_residuals: EventBalance
    balance_budgets: EventBalance
    source_sha256: Co2ManagementSources
    notice_sha256: Co2NoticeDigests
    scope: Literal['software_research_only']
    claim_scope: Literal['synthetic_joint_co2_solar_management_only']
    G0_G4: Literal['not_assessed']


class Co2EventValue(_Public):
    step_index: Index
    elapsed_seconds: Float
    forcing_step_index: Index
    management: Co2Management


class Co2Event(_Public):
    value: Co2EventValue
    time: Co2Point
    co2_basis: Literal['wet', 'dry']


class Co2Identity(_Public):
    engine_version: Literal['joint-co2-solar-continuation-research-v2']
    engine_code_sha256: Digest
    transport_helpers_code_sha256: Digest
    driver_code_sha256: Digest
    short_code_sha256: Digest
    management_code_sha256: Digest
    rhs_code_sha256: Digest
    component_code_sha256: Components
    co2_solar_component_code_sha256: Co2ComponentDigests
    co2_solar_policy_sha256: Co2PolicyDigests
    source_sha256: Co2SourceDigests
    notice_sha256: Co2NoticeDigests
    ledger_schema: Literal['joint-solar-co2-ledgers-v1']
    event_schema: Literal['joint-co2-solar-event-ledgers-v1']
    journal_schema: Literal['joint-co2-solar-event-journal-v2']
    balance_count: Literal[17]
    policy_sha256: Digest
    profile_sha256: Profiles
    state_schema: Literal['crop-solar-co2-stage-state-v1']
    physical_clock_contract: Literal['dynamic-canopy-temperature-history-rhs-v1']
    python_version: Annotated[str, Field(strict=True, max_length=40)]
    platform_machine: Annotated[str, Field(strict=True, max_length=100)]
    platform_system: Annotated[str, Field(strict=True, max_length=100)]
    byteorder: Literal['little', 'big']
    float_mant_dig: Literal[53]
    float_radix: Literal[2]


class Co2Numerical(_Public):
    step_seconds: Float
    step_count: Annotated[int, Field(strict=True, ge=1, le=4096)]
    duration_seconds: Float
    method: Literal['single-step-current-co2-solar-rk4-piecewise-events-v1']
    roundoff_rule: Literal['64-ulp-per-step-and-event-global-ledger-v1']


class Co2Manifest(_Public):
    identity: Co2Identity
    program_sha256: Digest
    initial_rhs_sha256: Digest
    initial_calculation_sha256: Digest
    policy_sha256: Digest
    numerical: Co2Numerical
    scope: Literal['software_research_only']
    clock_contract: Literal['elapsed-grid-current-co2-solar-events-v1']


class Co2TimeGrid(_Public):
    version: Literal['joint-co2-solar-time-binding-research-v1']
    time_rule: Literal['UTC_POSIX_integer_microseconds_decimal_step_v1']
    time_code_sha256: Digest
    start_utc: UtcStamp
    end_utc: UtcStamp
    step_seconds_decimal: Annotated[str, Field(strict=True, max_length=40)]
    step_microseconds: Annotated[int, Field(strict=True, ge=1, le=600000000)]
    step_count: Annotated[int, Field(strict=True, ge=1, le=4096)]


Farm = create_model('Co2Farm', __base__=_Public, **{k: (Digest if k == 'registration_sha256' else Name, ...)
    for k in storage.schema.FARM_KEYS if k != 'registration_job_id'})
Input = create_model('Co2Input', __base__=_Public, **{k: (UtcStamp if k.endswith('_utc') else
    Digest if k.endswith('_sha256') else Name, ...) for k in storage.schema.INPUT_KEYS})
Artifact = create_model('Co2Artifact', __base__=_Public,
    **{k: (Literal['completed', 'hold'] if k == 'status' else Annotated[str, Field(strict=True,
        pattern=r'^joint-co2-solar-storage-research-v1:[0-9a-f]{64}$')] if k == 'ref' else Digest, ...)
        for k in storage.schema.ARTIFACT_STRINGS},
    **{k: (Annotated[int, Field(strict=True, ge=lo, le=hi)], ...) for k, (lo, hi) in storage.schema.COUNTER_BOUNDS.items()})
Code = create_model('Co2ResultCode', __base__=_Public,
    **{k: (create_model('Co2ServerDependencies', __base__=_Public,
        **{n: (Digest, ...) for n in server.DEPENDENCY_SHA256}) if k == 'server_dependency_sha256' else Digest, ...)
        for k in storage.CODE})


class Co2Reference(_Public):
    storage_status: Literal['stored_unpublished_research']
    claim_scope: Literal['synthetic_joint_co2_solar_math_only']
    G0_G4: Literal['not_assessed']
    input: Input
    artifact: Artifact
    code: Code
    payload_sha256: Digest
    progress_sha256: Digest
    rights_or_gate_approval: FalseApproval
    normalization: Literal['per_m2_floor']
    profile_applicability: Literal['unvalidated_for_registered_crop']
    normalization_version: Literal['joint-current-co2-solar-float64-series-provenance-v1']
    qc_version: Literal['joint-initial-co2-solar-packet-schema-utc-v1']
    input_evidence_version: Literal['joint-co2-solar-input-evidence-v1']
    model: Co2Identity
    time_grid: Co2TimeGrid
    last_confirmed: Co2Point
    failed_boundary: Co2Point | None


class Co2Hold(_Public):
    reason_code: Annotated[str, Field(strict=True, pattern=r'^[A-Z][A-Z0-9_]{0,99}$')]
    phase: Literal['initial', 'interval', 'global-step-balance', 'forcing', 'event', 'global-event-balance']
    inner_failed_stage: Literal['initial', 'k2', 'k3', 'k4', 'endpoint', 'endpoint_balance'] | None
    time_meaning: Literal['failed_grid_boundary']
    time: Co2Point


class Co2Summary(_Public):
    status: Literal['completed', 'hold']
    manifest: Co2Manifest
    last_confirmed: Co2Sample
    checkpoint_sha256: Digest | None
    hold: Co2Hold | None


class Co2SamplePage(_Public):
    kind: Literal['samples']
    offset: Index
    limit: Annotated[int, Field(strict=True, ge=1, le=64)]
    total: Annotated[int, Field(strict=True, ge=0, le=512)]
    next_offset: Index | None
    records: Annotated[list[Co2Sample], Field(max_length=64)]


class Co2EventPage(_Public):
    kind: Literal['events']
    offset: Index
    limit: Annotated[int, Field(strict=True, ge=1, le=8)]
    total: Annotated[int, Field(strict=True, ge=0, le=128)]
    next_offset: Index | None
    records: Annotated[list[Co2Event], Field(max_length=8)]


class Co2Replay(_Public):
    schema_version: Literal['joint-co2-solar-replay-v1']
    result_id: Annotated[str, Field(strict=True, pattern=RESULT_ID_PATTERN)]
    recorded_at: UtcStamp
    study_id: Name
    revision: Name
    farm: Farm
    reference: Co2Reference
    summary: Co2Summary | None
    page: Annotated[Co2SamplePage | Co2EventPage, Field(discriminator='kind')] | None

    @model_validator(mode='after')
    def consistent(self):
        _need((self.summary is None) != (self.page is None))
        a = self.reference.artifact
        _need(a.ref == server.storage.VERSION + ':' + a.sha256
            and a.steps <= a.planned_steps and (a.status != 'completed' or a.steps == a.planned_steps))
        grid = self.reference.time_grid.model_dump(mode='json')
        dt = float(grid['step_seconds_decimal'])
        identity = self.reference.model.model_dump(mode='json')
        _need(self.reference.code.model_dump(mode='json') == storage.CODE and _current_identity(identity))
        _need(isfinite(dt) and dt > 0 and grid['step_count'] == a.planned_steps
            and grid['time_code_sha256'] == server.clock.CODE_SHA256
            and grid['step_microseconds'] == Fraction(grid['step_seconds_decimal'])*1000000
            and grid['start_utc'] == self.reference.input.start_utc
            and grid['end_utc'] == self.reference.input.end_utc == server.clock._at(grid, grid['step_count']))
        point = self.reference.last_confirmed
        _need(point.step_index == a.steps and point.at == server.clock._at(grid, a.steps)
            and (self.reference.failed_boundary is not None) == (a.status == 'hold'))
        failed = self.reference.failed_boundary
        if failed is not None:
            _need(a.steps <= failed.step_index and failed.at == server.clock._at(grid, failed.step_index))
        if self.summary is not None:
            s = self.summary
            _need(s.status == a.status and (s.hold is not None) == (a.status == 'hold')
                and (s.checkpoint_sha256 is None) == (a.status == 'hold')
                and s.manifest.identity == self.reference.model
                and continuation._hash(s.manifest.model_dump(mode='json')) == self.reference.input.context_sha256
                and s.manifest.numerical.step_seconds == dt and s.manifest.numerical.step_count == a.planned_steps
                and s.manifest.numerical.duration_seconds == dt*a.planned_steps)
            _point(s.last_confirmed.time.model_dump(mode='json'), s.last_confirmed.value.model_dump(mode='json'), grid, dt)
            _need(s.last_confirmed.value.step_index == a.steps)
            _need(s.last_confirmed.time == point and (s.hold is None or s.hold.time == failed))
        if self.page is not None:
            p = self.page; end = p.offset + len(p.records)
            _need(p.total == (a.sample_count if p.kind == 'samples' else a.event_count)
                and p.offset <= p.total and len(p.records) == min(p.limit, p.total-p.offset)
                and p.next_offset == (end if end < p.total else None))
            previous = -1
            for row in p.records:
                _point(row.time.model_dump(mode='json'), row.value.model_dump(mode='json'), grid, dt)
                _need(previous < row.value.step_index <= a.steps
                    and (failed is None or row.value.step_index < failed.step_index)); previous = row.value.step_index
        return self


def _current_identity(identity):
    base = continuation.transport.driver
    expected = {'engine_code_sha256': continuation.CODE_SHA256,
        'transport_helpers_code_sha256': continuation.transport.CODE_SHA256,
        'driver_code_sha256': base.CODE_SHA256, 'short_code_sha256': base.short.CODE_SHA256,
        'management_code_sha256': base.management.CODE_SHA256, 'rhs_code_sha256': joint.CODE_SHA256,
        'component_code_sha256': joint.COMPONENT_CODE_SHA256,
        'policy_sha256': joint.crop.startup.POLICY_SHA256,
        'profile_sha256': server.evidence._PROFILE_HASHES,
        'co2_solar_component_code_sha256': {module.__name__.rsplit('.', 1)[-1]: module.CODE_SHA256
            for module in _CO2_MODULES},
        'co2_solar_policy_sha256': {module.__name__.rsplit('.', 1)[-1]: continuation._hash(module.POLICY)
            for module in _CO2_POLICIES}}
    return all(identity.get(key) == value for key, value in expected.items())


def _basis_map(program, manifest):
    _need(type(program) is dict and set(program) == {'scenario', 'forcing_program', 'events',
        'output_steps', 'step_seconds', 'step_count'}
        and len(continuation._canonical(program)) <= continuation.MAX_CONTEXT_BYTES
        and continuation._hash(program) == manifest['program_sha256']
        and type(program['step_count']) is int and program['step_count'] == manifest['numerical']['step_count']
        and type(program['step_seconds']) is float and program['step_seconds'] == manifest['numerical']['step_seconds'])
    rows = program['forcing_program']
    _need(type(rows) is list and 1 <= len(rows) <= 512)
    result = {}; previous = -1
    for row in rows:
        _need(type(row) is dict and set(row) == {'step_index', *driver.BOUNDARIES}
            and type(row['step_index']) is int and previous < row['step_index'] <= program['step_count']
            and (previous != -1 or row['step_index'] == 0) and type(row['co2']) is dict
            and set(row['co2']) == {'input_id', 'origin', 'basis', 'parameters', 'forcing'}
            and type(row['co2']['basis']) is str and row['co2']['basis'] in ('wet', 'dry'))
        result[row['step_index']] = row['co2']['basis']; previous = row['step_index']
    return result


def _basis(value, bases):
    index = value['forcing_step_index']
    _need(type(index) is int and type(value['step_index']) is int and 0 <= index <= value['step_index']
        and index in bases)
    return bases[index]


def _parsed(cls, value):
    parsed = cls.model_validate(value)
    _need(storage._canonical(parsed.model_dump(mode='json')) == storage._canonical(value)); return parsed


def _point(time, value, grid, dt):
    _parsed(Co2Point, time)
    _need(type(value['step_index']) is int and time['step_index'] == value['step_index']
        and type(value['elapsed_seconds']) is float and value['elapsed_seconds'] == value['step_index']*dt
        and time['at'] == server.clock._at(grid, value['step_index']))
    if 'forcing_step_index' in value:
        _need(type(value['forcing_step_index']) is int and 0 <= value['forcing_step_index'] <= value['step_index'])


def _event(row, identity, bases):
    _need(type(row) is dict and set(row) == {'value', 'time'}
        and set(row['value']) == {'step_index', 'elapsed_seconds', 'forcing_step_index', 'management'})
    basis = _basis(row['value'], bases)
    m = row['value']['management']
    _need(type(m) is dict and set(m) == set(Co2Management.model_fields) | {'event'}
        and m['code_sha256'] == driver.management.CODE_SHA256
        and m['component_code_sha256'] == _EVENT_COMPONENTS
        and m['profile_sha256'] == identity['profile_sha256'])
    keys = ('model_version', 'code_sha256', 'state_schema_version', 'component_code_sha256',
        'profile_sha256', 'policy_sha256', 'event_sha256', 'input_sha256',
        'before_calculation_sha256', 'after_calculation_sha256', 'quantity_rule',
        'roundoff_rule', 'bulk_air_invariants', 'time_coordinate')
    _need(continuation._hash(m['event']) == m['event_sha256']
        and continuation._hash({key: m[key] for key in keys}) == m['calculation_sha256'])
    copied = {key: value for key, value in m.items() if key != 'event'}
    for key in ('before', 'after'):
        state = m[key]
        _need(type(state) is dict and set(state) == {'scenario', 'solar', 'ventilation', 'co2',
                'derived', 'input_sha256', 'calculation_sha256'}
            and type(state['scenario']) is dict
            and set(state['scenario']) == {'input_id', 'origin', *joint.SCALAR_BLOCKS, *joint.ARRAY_BLOCKS}
            and type(state['co2']) is dict and state['co2'].get('basis') == basis)
        copied[key] = {**{name: state[name] for name in ('derived', 'input_sha256', 'calculation_sha256')},
            **{name: state['scenario'][name] for name in ('plant_state', 'cohort_state', 'climate_state')}}
        _need(copied[key]['calculation_sha256'] == m[key+'_calculation_sha256'])
    _need(m['input_sha256'] == m['before']['input_sha256'])
    return {'time': row['time'], 'co2_basis': basis, 'value': {
        **{key: row['value'][key] for key in ('step_index', 'elapsed_seconds', 'forcing_step_index')},
        'management': copied}}


def _public_bytes(projected):
    try:
        storage._pins()
        _need(type(projected) is Co2Replay and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
            and MAX_RESPONSE_BYTES == server.storage.LIMITS['page_bytes'] == 2*1024**2)
        checked = _parsed(Co2Replay, projected.model_dump(mode='json'))
        raw = checked.model_dump_json().encode(); _need(1 <= len(raw) <= MAX_RESPONSE_BYTES); return raw
    except Exception: raise ProjectionHold('joint CO2 display unavailable') from None


def project_co2_result(record, terminal, *, source_program, view='summary', page=None, limit=None):
    try:
        _need(type(record) is dict and set(record) == {'result_id', 'payload_raw', 'payload_sha256', 'progress_raw', 'progress_sha256', 'recorded_at'}
            and type(record['payload_raw']) is bytes and sha256(record['payload_raw']).hexdigest() == record['payload_sha256']
            and type(record['recorded_at']) is datetime and record['recorded_at'].utcoffset() is not None)
        packet = storage._decode(record['payload_raw']); _need(record['result_id'] == packet['result_id']
            and type(record['progress_raw']) is bytes and 0 < len(record['progress_raw']) <= storage.MAX_PROGRESS_BYTES
            and sha256(record['progress_raw']).hexdigest() == record['progress_sha256'] == packet['progress_sha256']
            and record['progress_raw'] == storage._canonical(packet['policies']['server_progress']))
        progress = packet['policies']['server_progress']; source = packet['binding']['input']
        _need(type(terminal) is dict and set(terminal) == {'version', 'scope', 'G0_G4', 'artifact_sha256',
            'context_sha256', 'binding_sha256', 'status', 'counts', 'checkpoint', 'last_confirmed', 'hold', 'times', 'manifest', 'time_binding'}
            and terminal['version'] == server.storage.VERSION and terminal['scope'] == 'software_research_only'
            and terminal['G0_G4'] == 'not_assessed' and terminal['binding_sha256'] == source['time_binding_sha256']
            and all(storage._canonical(terminal[k]) == storage._canonical(progress[k]) for k in
                ('artifact_sha256', 'context_sha256', 'status', 'counts', 'checkpoint', 'last_confirmed', 'hold', 'times')))
        manifest = terminal['manifest']; _parsed(Co2Manifest, manifest); identity = manifest['identity']
        _need(continuation._hash(manifest) == source['context_sha256']
            and identity == source['model_identity'] and _current_identity(identity))
        bases = _basis_map(source_program, manifest)
        grid = terminal['time_binding']; numerical = manifest['numerical']; dt = numerical['step_seconds']
        _need(continuation._hash(grid) == source['time_binding_sha256'] and grid['context_sha256'] == source['context_sha256']
            and grid['version'] == server.clock.VERSION and grid['time_rule'] == server.clock.TIME_RULE
            and grid['time_code_sha256'] == server.clock.CODE_SHA256 and grid['step_count'] == numerical['step_count'] == progress['planned_steps']
            and grid['start_utc'] == packet['input']['start_utc'] and grid['end_utc'] == packet['input']['end_utc']
            and numerical['duration_seconds'] == dt*numerical['step_count'] and 0 < numerical['duration_seconds'] <= 600)
        last = terminal['last_confirmed']; times = terminal['times']; _parsed(Co2Snapshot, last)
        _point(times['last_confirmed'], last, grid, dt); _need(last['step_index'] == progress['steps'])
        held = terminal['hold']; cp = terminal['checkpoint']; hold = None
        if progress['status'] == 'hold':
            _need(cp is None and type(held) is dict and set(held) == {'step_index', 'elapsed_seconds', 'phase', 'reason', 'inner_failed_stage'})
            _point(times['hold'], held, grid, dt)
            _need(type(held['reason']) is str and 0 < len(held['reason']) <= 4096)
            reason = held['reason'].partition(':')[0]
            hold = {'reason_code': reason if re.fullmatch(r'[A-Z][A-Z0-9_]{0,99}', reason) else 'CALCULATION_HOLD', 'phase': held['phase'],
                'time_meaning': 'failed_grid_boundary', 'time': times['hold'], 'inner_failed_stage': held['inner_failed_stage']}
            _need(last['step_index'] <= held['step_index'])
        else:
            _need(held is None and times['hold'] is None and type(cp) is dict and set(cp) == {'sha256', 'value'}
                and continuation._hash(cp['value']) == cp['sha256'] and cp['value']['context_sha256'] == source['context_sha256']
                and cp['value']['next_index'] == numerical['step_count']+1 and cp['value']['last_confirmed'] == last
                and cp['value']['output_cursor'] == progress['counts']['samples'] and cp['value']['event_cursor'] == progress['counts']['events'])
        summary = _parsed(Co2Summary, {'status': progress['status'], 'manifest': manifest,
            'last_confirmed': {'value': last, 'time': times['last_confirmed'], 'co2_basis': _basis(last, bases)},
            'checkpoint_sha256': None if cp is None else cp['sha256'], 'hold': hold})
        projected_page = None
        if view == 'summary': _need(page is None and limit is None)
        else:
            _need(view in ('samples', 'events') and type(page) is dict and set(page) == {'version', 'artifact_sha256', 'kind', 'start', 'total', 'records'}
                and page['version'] == server.storage.VERSION and page['artifact_sha256'] == packet['artifact']['sha256'] and page['kind'] == view
                and type(page['start']) is int and type(page['total']) is int and type(page['records']) is list
                and type(limit) is int and 1 <= limit <= (64 if view == 'samples' else 8))
            rows = page['records']; previous = -1
            for row in rows:
                _need(type(row) is dict and set(row) == {'value', 'time'}); value = row['value']
                _point(row['time'], value, grid, dt)
                _need(previous < value['step_index'] <= progress['steps'] and (held is None or value['step_index'] < held['step_index']))
                previous = value['step_index']
            rows = [{**row, 'co2_basis': _basis(row['value'], bases)} for row in rows] if view == 'samples' else [_event(row, identity, bases) for row in rows]
            end = page['start'] + len(rows)
            projected_page = _parsed(Co2SamplePage if view == 'samples' else Co2EventPage,
                {'kind': view, 'offset': page['start'], 'limit': limit, 'total': page['total'],
                    'next_offset': end if end < page['total'] else None, 'records': rows})
        registration = packet['binding']['registration']
        value = Co2Replay(schema_version=VERSION, result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00', 'Z'),
            study_id=packet['study_id'], revision=packet['revision'], farm={k: packet['farm'][k] for k in Farm.model_fields},
            reference={'storage_status': packet['status'], 'claim_scope': packet['claim_scope'], 'G0_G4': packet['G0_G4'],
                'input': packet['input'], 'artifact': packet['artifact'], 'code': packet['code'], 'payload_sha256': record['payload_sha256'],
                'progress_sha256': record['progress_sha256'], 'rights_or_gate_approval': packet['rights_or_gate_approval'],
                **{k: registration[k] for k in ('normalization', 'profile_applicability')},
                **{k: source[k] for k in ('normalization_version', 'qc_version', 'input_evidence_version')},
                'model': identity, 'time_grid': {k: grid[k] for k in Co2TimeGrid.model_fields},
                'last_confirmed': times['last_confirmed'], 'failed_boundary': times['hold']},
            summary=summary if view == 'summary' else None, page=projected_page)
        _public_bytes(value); return value
    except Exception: raise ProjectionHold('joint CO2 display unavailable') from None
