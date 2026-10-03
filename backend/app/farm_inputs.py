"""Explicit farm intent and scope checks for authored calculation inputs."""

from datetime import date, datetime, time, timedelta
from decimal import Context, Decimal, localcontext
from typing import Annotated, Literal, Self
from zoneinfo import ZoneInfo

from pydantic import Field, field_validator, model_validator

from .economic_contracts import EconomicScenario, untrusted_data, utc
from .economics import canonical_scenario_sha256
from .jobs import canonical_input_bytes
from .market import UnavailableMarketContext
from .provenance import Digest, FrozenContract, Name


Identifier = Annotated[str, Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$', max_length=200)]
Label = Annotated[Name, Field(max_length=200)]
Unit = Literal['m²','m³','J/K','kg_da','W/K','1','K','kg_v/kg_da','W_th',
               'kg_da/s','kg_v/s','W','KRW']
KST = ZoneInfo('Asia/Seoul')


class UserEvidence(FrozenContract):
    input_id: Identifier
    revision: Identifier
    source_ref: Identifier
    origin: Literal['user']
    evidence_level: Literal['assumed']
    available_at: datetime

    _utc = field_validator('available_at')(utc)


class FarmQuantity(UserEvidence):
    value: str = Field(pattern=r'^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$', max_length=64)
    unit: Unit

    @property
    def amount(self):
        return Decimal(self.value)


class FarmSwitch(UserEvidence):
    value: bool


def _quantity(item, unit, *, minimum=None, positive=False, maximum=None):
    if (item.unit != unit or positive and item.amount <= 0 or
            minimum is not None and item.amount < minimum or
            maximum is not None and item.amount > maximum):
        raise ValueError('farm quantity unit or domain rejected')


class Window(FrozenContract):
    start: datetime
    end: datetime

    _utc = field_validator('start','end')(utc)

    @model_validator(mode='after')
    def ordered(self) -> Self:
        if self.start >= self.end:
            raise ValueError('farm window must have positive duration')
        return self

    def contains(self, at):
        return self.start <= at < self.end


class FarmFacility(FrozenContract):
    zone_id: Identifier
    facility_type: Literal['single_zone_greenhouse']
    tenure: Literal['owned','leased','unknown']
    decision_basis: Literal['new_facility','existing_facility_crop_change']
    provenance: UserEvidence
    floor_area: FarmQuantity
    cultivable_area: FarmQuantity
    indoor_volume: FarmQuantity
    effective_heat_capacity: FarmQuantity
    dry_air_mass: FarmQuantity
    envelope_conductance: FarmQuantity
    absorbed_solar_fraction: FarmQuantity

    @model_validator(mode='after')
    def domains(self) -> Self:
        for name, unit in (('floor_area','m²'),('cultivable_area','m²'),('indoor_volume','m³'),
                           ('effective_heat_capacity','J/K'),('dry_air_mass','kg_da')):
            _quantity(getattr(self,name),unit,positive=True)
        _quantity(self.envelope_conductance,'W/K',minimum=0)
        _quantity(self.absorbed_solar_fraction,'1',minimum=0,maximum=1)
        if self.cultivable_area.amount > self.floor_area.amount:
            raise ValueError('cultivable area exceeds floor area')
        return self


class FarmInitialState(FrozenContract):
    temperature: FarmQuantity
    humidity_ratio: FarmQuantity

    @model_validator(mode='after')
    def domains(self) -> Self:
        _quantity(self.temperature,'K',positive=True)
        _quantity(self.humidity_ratio,'kg_v/kg_da',minimum=0)
        return self


class FarmHeater(FrozenContract):
    mode: Literal['indirect_sensible']
    capacity_basis: Literal['delivered_thermal_power']
    control_version: Literal['thermal-indirect-sensible-end-target-v1']
    capacity: FarmQuantity
    setpoint: FarmQuantity
    available: FarmSwitch
    efficiency_status: Literal['unavailable']
    metering_status: Literal['unavailable']

    @model_validator(mode='after')
    def domains(self) -> Self:
        _quantity(self.capacity,'W_th',minimum=0)
        _quantity(self.setpoint,'K',positive=True)
        return self


class FarmForcing(Window):
    ventilation_dry_air_flow: FarmQuantity
    canopy_evaporation: FarmQuantity
    ground_heat_flow: FarmQuantity

    @model_validator(mode='after')
    def domains(self) -> Self:
        _quantity(self.ventilation_dry_air_flow,'kg_da/s',minimum=0)
        _quantity(self.canopy_evaporation,'kg_v/s',minimum=0)
        _quantity(self.ground_heat_flow,'W')
        return self


class Cultivation(FrozenContract):
    crop_id: Identifier
    batch_id: Identifier
    species: Label
    variety: Label
    profile_status: Literal['unavailable']
    provenance: UserEvidence
    area: FarmQuantity
    occupancy: Window
    release_at: datetime
    harvest_window: Window
    sales_window: Window
    collection_window: Window
    grades: tuple[Identifier, ...] = Field(min_length=1,max_length=32)
    channels: tuple[Identifier, ...] = Field(min_length=1,max_length=32)

    _utc = field_validator('release_at')(utc)

    @model_validator(mode='after')
    def domains(self) -> Self:
        _quantity(self.area,'m²',positive=True)
        if (self.release_at < self.occupancy.end or
                not self.occupancy.start <= self.harvest_window.start < self.harvest_window.end <= self.occupancy.end or
                self.sales_window.start < self.harvest_window.start or
                self.collection_window.start < self.sales_window.start or
                len(set(self.grades)) != len(self.grades) or len(set(self.channels)) != len(self.channels)):
            raise ValueError('cultivation calendar or channels rejected')
        return self


class FarmConstraints(FrozenContract):
    capex_ceiling: FarmQuantity | None
    minimum_cash: FarmQuantity | None

    @model_validator(mode='after')
    def domains(self) -> Self:
        if self.capex_ceiling is not None:
            _quantity(self.capex_ceiling,'KRW',minimum=0)
        if self.minimum_cash is not None:
            _quantity(self.minimum_cash,'KRW')
        return self


class FarmEconomicPin(FrozenContract):
    scenario_id: Identifier
    revision: Identifier
    sha256: Digest
    candidate_id: Digest


def _records(value):
    if isinstance(value,UserEvidence):
        yield value
    elif isinstance(value,FrozenContract):
        for name in type(value).model_fields:
            yield from _records(getattr(value,name))
    elif isinstance(value,tuple):
        for item in value:
            yield from _records(item)


class FarmInputs(FrozenContract):
    schema_version: Literal['farm-inputs-v1']
    scenario_id: Identifier
    scenario_revision: Identifier
    research_job_id: str = Field(pattern=r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')
    snapshot_id: str = Field(pattern=r'^thermal-snapshot-v1:[0-9a-f]{64}$',max_length=84)
    decision_context_id: Identifier
    decision_at: datetime
    market_context: UnavailableMarketContext
    goal_id: Literal['historical-thermal-replay']
    period_start: date
    period_end: date
    economic: FarmEconomicPin
    facility: FarmFacility
    initial_state: FarmInitialState
    heater: FarmHeater
    forcing: tuple[FarmForcing, ...] = Field(min_length=1,max_length=32)
    crops: tuple[Cultivation, ...] = Field(max_length=32)
    objective: Literal['conditional_operating_profit','conditional_operating_margin','minimum_cash']
    constraints: FarmConstraints

    _utc = field_validator('decision_at')(utc)

    @model_validator(mode='after')
    def coherent(self) -> Self:
        if self.period_end < self.period_start or self.period_end == date.max:
            raise ValueError('farm evaluation dates rejected')
        start=datetime.combine(self.period_start,time(),KST)
        end=datetime.combine(self.period_end+timedelta(days=1),time(),KST)
        records={}
        for item in _records(self):
            key=(item.input_id,item.revision)
            row=item.model_dump(mode='json')
            if item.available_at > self.decision_at or key in records and records[key] != row:
                raise ValueError('farm record availability or identity rejected')
            records[key]=row
        if (len({crop.crop_id for crop in self.crops}) != len(self.crops) or
                len({crop.batch_id for crop in self.crops}) != len(self.crops)):
            raise ValueError('duplicate crop or batch')
        for entry in (*self.forcing,*self.crops):
            windows=(entry,) if isinstance(entry,FarmForcing) else (
                entry.harvest_window,entry.sales_window,entry.collection_window)
            if any(not start <= window.start < window.end <= end for window in windows):
                raise ValueError('farm window outside evaluation calendar')
        with localcontext(Context(prec=128)):
            for at in {crop.occupancy.start for crop in self.crops}:
                area=sum((crop.area.amount for crop in self.crops
                          if crop.occupancy.start <= at < crop.release_at),Decimal(0))
                if area > self.facility.cultivable_area.amount:
                    raise ValueError('simultaneous cultivated area exceeds facility area')
        return self


def canonical_farm_inputs(value):
    farm=FarmInputs.model_validate(untrusted_data(value))
    return canonical_input_bytes(farm.model_dump(mode='json'))


def validate_economic_scope(value, economic_value, authenticated_tenant):
    farm=FarmInputs.model_validate(untrusted_data(value))
    economic=EconomicScenario.model_validate(untrusted_data(economic_value))
    if (economic.tenant_id != authenticated_tenant or
            economic.scenario_id != farm.economic.scenario_id or economic.scenario_revision != farm.economic.revision or
            canonical_scenario_sha256(economic) != farm.economic.sha256 or
            economic.decision_at != farm.decision_at or economic.period_start != farm.period_start or
            economic.period_end != farm.period_end or economic.market_context != farm.market_context or
            economic.scenario_market_context != farm.market_context):
        raise ValueError('farm economic scope or pin rejected')
    crops={crop.batch_id:crop for crop in farm.crops}
    opening_batches={lot.batch_id for lot in economic.opening_inventory or () if lot.batch_id is not None}
    for harvest in economic.harvests:
        crop=crops.get(harvest.batch_id)
        if crop is None or not crop.harvest_window.contains(harvest.at):
            raise ValueError('harvest batch or calendar rejected')
    sales={sale.id:sale for sale in economic.sales}
    for sale in economic.sales:
        crop=crops.get(sale.batch_id)
        if crop is None and sale.batch_id not in opening_batches:
            raise ValueError('sale batch has no planting or opening inventory')
        if crop is not None and (sale.grade not in crop.grades or sale.channel not in crop.channels or
                any(not crop.sales_window.contains(at) for at in (
                    sale.dispatch_at,sale.delivery_at,sale.inspection_at,sale.recognized_at))):
            raise ValueError('sale crop scope or calendar rejected')
    for packout in economic.packouts:
        crop=crops.get(packout.batch_id)
        if crop is None or packout.grade not in crop.grades or packout.channel not in crop.channels:
            raise ValueError('packout crop scope rejected')
    for collection in economic.collections or ():
        sale=sales.get(collection.sale_id)
        if sale is None:
            raise ValueError('collection sale reference rejected')
        crop=crops.get(sale.batch_id)
        if crop is not None and not crop.collection_window.contains(collection.at):
            raise ValueError('collection crop calendar rejected')
