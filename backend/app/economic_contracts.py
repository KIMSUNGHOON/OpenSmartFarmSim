"""Strict, immutable inputs for the first conditional economic ledger.

The API payload contains references, never a repository. A trusted server binds the
repository at service construction; the test fake is not a production authority.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
import re
from typing import Literal, Self

from pydantic import BaseModel, field_validator, model_validator

from app.market import MarketContext
from app.provenance import Digest, FrozenContract, Name

Unit = Literal["kg", "KRW", "KRW/kg", "month", "KRW/month", "kWh_e", "KRW/kWh_e", "L", "KRW/L", "day"]
_DECIMAL = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("economic event time must be UTC-aware")
    return value


class EconomicNumber(FrozenContract):
    value: str
    unit: Unit
    input_id: Name
    revision: Name
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    assumption_scope: Name
    source_ref: Name
    available_at: datetime

    @field_validator("value")
    @classmethod
    def decimal_string(cls, value: str) -> str:
        if not isinstance(value, str) or len(value) > 64 or not _DECIMAL.fullmatch(value):
            raise ValueError("value must be a nonnegative finite JSON decimal string")
        if not Decimal(value).is_finite():
            raise ValueError("value must be finite")
        return value

    @field_validator("available_at")
    @classmethod
    def availability_utc(cls, value: datetime) -> datetime:
        return utc(value)

    @property
    def amount(self) -> Decimal:
        return Decimal(self.value)


class OwnedEconomicRecord(EconomicNumber):
    tenant_id: Name
    scope_start: date
    scope_end: date


class OwnedScenarioPin(FrozenContract):
    tenant_id: Name
    scenario_id: Name
    scenario_revision: Name
    decision_at: datetime
    payload_sha256: Digest
    immutable_job_input_ref: Name
    immutable_job_input_sha256: Digest
    immutable: Literal[True]

    @field_validator("decision_at")
    @classmethod
    def decision_utc(cls, value: datetime) -> datetime:
        return utc(value)


class PriorBatchCostRecord(FrozenContract):
    cost_ref: Name
    tenant_id: Name
    batch_id: Name
    grade: Name
    channel: Name
    cost_amount: EconomicNumber
    allocation_basis_kg: EconomicNumber
    opening_quantity_kg: EconomicNumber
    allocation_policy: Literal["proportional_saleable_kg_v1"]
    rights: Literal["conditional_g1_use"]
    available_at: datetime
    scope_start: date
    scope_end: date

    @field_validator("available_at")
    @classmethod
    def availability_utc(cls, value: datetime) -> datetime:
        return utc(value)


class Harvest(FrozenContract):
    id: Name
    batch_id: Name
    at: datetime
    quantity: EconomicNumber

    _at_utc = field_validator("at")(utc)


class Packout(FrozenContract):
    id: Name
    harvest_id: Name
    batch_id: Name
    grade: Name
    channel: Name
    at: datetime
    quantity: EconomicNumber

    _at_utc = field_validator("at")(utc)


class Cull(FrozenContract):
    id: Name
    harvest_id: Name
    at: datetime
    quantity: EconomicNumber

    _at_utc = field_validator("at")(utc)


class CullDisposal(FrozenContract):
    id: Name
    cull_id: Name
    at: datetime
    quantity: EconomicNumber

    _at_utc = field_validator("at")(utc)


class OpeningLot(FrozenContract):
    grade: Name | None
    batch_id: Name | None
    channel: Name | None
    prior_cost_ref: Name | None
    quantity: EconomicNumber
    prior_cost_amount: EconomicNumber | None = None
    allocation_basis: EconomicNumber | None = None
    allocation_policy: Literal["proportional_saleable_kg_v1"] | None = None


class Sale(FrozenContract):
    id: Name
    batch_id: Name
    grade: Name
    channel: Name
    dispatch_at: datetime
    delivery_at: datetime
    inspection_at: datetime
    recognized_at: datetime
    quantity: EconomicNumber
    price: EconomicNumber
    price_basis: Literal["gross_before_deductions"]

    @field_validator("dispatch_at", "delivery_at", "inspection_at", "recognized_at")
    @classmethod
    def sale_time_utc(cls, value: datetime) -> datetime:
        return utc(value)


class Collection(FrozenContract):
    id: Name
    sale_id: Name
    at: datetime
    amount: EconomicNumber

    _at_utc = field_validator("at")(utc)


class Return(FrozenContract):
    id: Name
    sale_id: Name
    at: datetime
    quantity: EconomicNumber
    disposition: Literal["resaleable", "disposed"]
    refund: EconomicNumber
    refund_paid_at: datetime

    @field_validator("at", "refund_paid_at")
    @classmethod
    def return_time_utc(cls, value: datetime) -> datetime:
        return utc(value)


class Discount(FrozenContract):
    id: Name
    sale_id: Name
    at: datetime
    amount: EconomicNumber

    _at_utc = field_validator("at")(utc)


class SettlementSetoff(FrozenContract):
    id: Name
    sale_id: Name
    cost_id: Name
    at: datetime
    amount: EconomicNumber
    settlement_ref: Name
    evidence_revision: Name
    evidence_sha256: Digest

    _at_utc = field_validator("at")(utc)


class OwnedSettlementRecord(FrozenContract):
    settlement_ref: Name
    revision: Name
    tenant_id: Name
    sale_id: Name
    cost_id: Name
    at: datetime
    amount: EconomicNumber
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    rights: Literal["conditional_g1_use"]
    immutable: Literal[True]
    available_at: datetime
    scope_start: date
    scope_end: date
    raw_sha256: Digest

    @field_validator("at", "available_at")
    @classmethod
    def settlement_time_utc(cls, value: datetime) -> datetime:
        return utc(value)


class Disposal(FrozenContract):
    id: Name
    batch_id: Name
    grade: Name
    channel: Name
    at: datetime
    quantity: EconomicNumber

    _at_utc = field_validator("at")(utc)


class Cost(FrozenContract):
    id: Name
    purpose: Literal["production", "sale", "period"]
    batch_id: Name | None
    sale_id: Name | None
    incurred_at: datetime
    quantity: EconomicNumber
    unit_cost: EconomicNumber
    paid_at: datetime | None
    payment: EconomicNumber | None

    @field_validator("incurred_at", "paid_at")
    @classmethod
    def cost_time_utc(cls, value: datetime | None) -> datetime | None:
        return utc(value) if value is not None else None

    @model_validator(mode="after")
    def cost_links_and_payment(self) -> Self:
        if (self.paid_at is None) != (self.payment is None):
            raise ValueError("cost payment amount and date must be declared together")
        if self.purpose == "production" and (self.batch_id is None or self.sale_id is not None):
            raise ValueError("production cost needs a batch and no sale link")
        if self.purpose == "sale" and self.sale_id is None:
            raise ValueError("sale cost needs a sale link")
        if self.purpose == "period" and (self.batch_id is not None or self.sale_id is not None):
            raise ValueError("period cost cannot link a batch or sale")
        return self


class AmountEvent(FrozenContract):
    id: Name
    at: datetime
    amount: EconomicNumber
    asset_id: Name | None = None
    loan_id: Name | None = None

    _at_utc = field_validator("at")(utc)


class AssetAccount(FrozenContract):
    id: Name
    opening_basis: EconomicNumber
    acquisition_cost: EconomicNumber | None = None
    acquired_at: datetime | None = None
    installed_at: datetime | None = None
    residual_value: EconomicNumber | None = None
    useful_life_days: EconomicNumber | None = None
    opening_accumulated_depreciation: EconomicNumber | None = None

    @field_validator("acquired_at", "installed_at")
    @classmethod
    def asset_time_utc(cls, value: datetime | None) -> datetime | None:
        return utc(value) if value is not None else None


class DebtAccount(FrozenContract):
    id: Name
    opening_principal: EconomicNumber


ZeroGroup = Literal[
    "cull_disposals", "opening_inventory", "collections", "returns", "discounts", "setoffs",
    "disposals", "variable_costs", "fixed_costs", "depreciation", "assets",
    "grants", "asset_disposals", "taxes", "capex", "loan_draws",
    "principal_payments", "interest_payments", "debt_accounts",
]
ZERO_GROUP_UNITS = {
    "cull_disposals": "kg", "opening_inventory": "kg", "collections": "KRW",
    "returns": "kg", "discounts": "KRW", "setoffs": "KRW", "disposals": "kg",
    "variable_costs": "KRW", "fixed_costs": "KRW", "depreciation": "KRW",
    "assets": "KRW", "grants": "KRW", "asset_disposals": "KRW",
    "taxes": "KRW", "capex": "KRW", "loan_draws": "KRW",
    "principal_payments": "KRW", "interest_payments": "KRW", "debt_accounts": "KRW",
}


class ZeroDeclaration(FrozenContract):
    group: ZeroGroup
    zero: EconomicNumber

    @model_validator(mode="after")
    def scoped_zero(self) -> Self:
        if self.zero.amount != 0 or self.zero.unit != ZERO_GROUP_UNITS[self.group]:
            raise ValueError("zero declaration needs a zero in its group unit")
        return self


class EconomicScenario(FrozenContract):
    schema_version: Literal["3"]
    scenario_id: Name
    scenario_revision: Name
    tenant_id: Name
    decision_at: datetime
    period_start: date
    period_end: date
    scenario_market_context: MarketContext
    market_context: MarketContext
    harvests: tuple[Harvest, ...]
    packouts: tuple[Packout, ...]
    culls: tuple[Cull, ...]
    cull_disposals: tuple[CullDisposal, ...] | None = None
    opening_inventory: tuple[OpeningLot, ...] | None = None
    sales: tuple[Sale, ...]
    collections: tuple[Collection, ...] | None = None
    returns: tuple[Return, ...] | None = None
    discounts: tuple[Discount, ...] | None = None
    setoffs: tuple[SettlementSetoff, ...] | None = None
    disposals: tuple[Disposal, ...] | None = None
    variable_costs: tuple[Cost, ...] | None = None
    fixed_costs: tuple[Cost, ...] | None = None
    depreciation: tuple[AmountEvent, ...] | None = None
    assets: tuple[AssetAccount, ...] | None = None
    grants: tuple[AmountEvent, ...] | None = None
    asset_disposals: tuple[AmountEvent, ...] | None = None
    taxes: tuple[AmountEvent, ...] | None = None
    capex: tuple[AmountEvent, ...] | None = None
    loan_draws: tuple[AmountEvent, ...] | None = None
    principal_payments: tuple[AmountEvent, ...] | None = None
    interest_payments: tuple[AmountEvent, ...] | None = None
    debt_accounts: tuple[DebtAccount, ...] | None = None
    opening_cash: EconomicNumber | None = None
    opening_receivable: EconomicNumber | None = None
    opening_refund_payable: EconomicNumber | None = None
    opening_operating_payable: EconomicNumber | None = None
    zero_declarations: tuple[ZeroDeclaration, ...] = ()

    @field_validator("decision_at")
    @classmethod
    def decision_utc(cls, value: datetime) -> datetime:
        return utc(value)

    @model_validator(mode="after")
    def period_order(self) -> Self:
        if self.period_end < self.period_start:
            raise ValueError("period end precedes start")
        declared = set()
        for item in self.zero_declarations:
            if item.group in declared:
                raise ValueError("duplicate zero declaration")
            declared.add(item.group)
            if getattr(self, item.group) != ():
                raise ValueError("zero declaration requires an empty group")
        return self


def untrusted_data(value: object) -> object:
    """Revalidate even model_construct/model_copy objects at the server boundary."""
    if isinstance(value, BaseModel):
        fields = dict(vars(value))
        if value.model_extra:
            fields.update(value.model_extra)
        return {key: untrusted_data(item) for key, item in fields.items()}
    if isinstance(value, dict):
        return {key: untrusted_data(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return type(value)(untrusted_data(item) for item in value)
    return value


def iter_economic_numbers(scenario: EconomicScenario):
    """Yield every raw numeric input; the server checks all before arithmetic."""
    def visit(value):
        if isinstance(value, EconomicNumber):
            yield value
        elif isinstance(value, BaseModel):
            for field in type(value).model_fields:
                yield from visit(getattr(value, field))
        elif isinstance(value, (tuple, list)):
            for item in value:
                yield from visit(item)
    yield from visit(scenario)
