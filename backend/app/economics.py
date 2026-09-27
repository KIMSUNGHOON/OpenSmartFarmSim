"""Deterministic first G1 economic ledger for conditional user assumptions only.

EconomicLedger is constructed by trusted server code with a tenant-aware repository.
The test fake proves this boundary contract, not a production database or G0 approval.
No repository can be supplied in a client EconomicScenario or calculate call.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, Inexact, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
from typing import Literal
from zoneinfo import ZoneInfo

from app.economic_contracts import (
    EconomicNumber, EconomicScenario, OwnedEconomicRecord, OwnedScenarioPin, OwnedSettlementRecord,
    PriorBatchCostRecord,
    ZERO_GROUP_UNITS, iter_economic_numbers,
    untrusted_data,
)
from app.market import (
    UnavailableMarketContext, resolve_market_context, validate_first_g1_use,
    validate_market_context_chain,
)

KST = ZoneInfo("Asia/Seoul")
ZERO = Decimal("0")
FORMULA_VERSION = "economic-ledger-v9-sales-settlement"
SalesTotalsStatus = Literal["inventory_reconciled", "unverified_input_arithmetic"]


def day(at: datetime) -> date:
    return at.astimezone(KST).date()


def in_period(at: datetime, scenario: EconomicScenario) -> bool:
    return scenario.period_start <= day(at) <= scenario.period_end


def month(at: datetime) -> str:
    return day(at).strftime("%Y-%m")


def money(value: EconomicNumber) -> Decimal:
    if value.unit != "KRW":
        raise ValueError("amount must use KRW")
    return value.amount


def quantity(value: EconomicNumber) -> Decimal:
    if value.unit != "kg":
        raise ValueError("quantity must use kg")
    return value.amount


def total(items) -> Decimal:
    return sum(items, ZERO)


def required_sum(events, converter=money) -> Decimal | None:
    return None if events is None else total(converter(item.amount) for item in events)


def remittance_per_kg(amount: Decimal, kg: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 128
        context.rounding = ROUND_HALF_UP
        context.traps[Inexact] = False
        return amount / kg


def canonical_scenario_sha256(scenario: EconomicScenario) -> str:
    payload = json.dumps(scenario.model_dump(mode="json"), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MonthlyCash:
    month: str
    opening: Decimal
    net: Decimal
    closing: Decimal
    minimum_balance: Decimal
    minimum_at: datetime
    shortage: Decimal


@dataclass(frozen=True)
class FutureCashEvent:
    event_id: str
    at: datetime
    amount: Decimal
    category: str


@dataclass(frozen=True)
class FutureSetoffEvent:
    event_id: str
    sale_id: str
    cost_id: str
    at: datetime
    amount: Decimal


@dataclass(frozen=True)
class SaleNetRemittance:
    sale_id: str
    amount: Decimal | None
    per_kg: Decimal | None
    status: Literal["conditional_user_assumption", "hold"]
    hold_reason: str | None


@dataclass(frozen=True)
class EconomicResult:
    """Conditional ledger result.

    ``recognized_kg`` and ``gross_sales`` sum supplied sale quantities and gross
    prices. ``sales_totals_status`` marks them as inventory-reconciled only when
    lot-level stock balances reconcile; otherwise they are unverified input
    arithmetic and sale-dependent revenue and cash remain held.
    """

    result_id: str
    scenario_id: str
    scenario_revision: str
    scenario_sha256: str
    decision_at: datetime
    formula_version: str
    market_context: UnavailableMarketContext
    assessment_market_context: UnavailableMarketContext
    assessment_status: str
    forecast_run_id: None
    input_versions: tuple[tuple[str, str], ...]
    input_provenance: tuple[EconomicNumber, ...]
    hold_reasons: tuple[str, ...]
    harvest_kg: Decimal
    packout_kg: Decimal
    cull_disposed_kg: Decimal | None
    recognized_kg: Decimal
    net_sold_kg: Decimal | None
    closing_inventory: dict[tuple[str, str, str], Decimal] | None
    closing_inventory_cost_by_batch: dict[str, Decimal] | None
    gross_sales: Decimal
    sales_totals_status: SalesTotalsStatus
    revenue: Decimal | None
    variable_cost: Decimal | None
    fixed_cost: Decimal | None
    depreciation: Decimal | None
    management_oi: Decimal | None
    operating_cash: Decimal | None
    receivable_begin: Decimal | None
    receivable_end: Decimal | None
    refund_payable_begin: Decimal | None
    refund_payable_end: Decimal | None
    operating_payable_begin: Decimal | None
    operating_payable_end: Decimal | None
    operating_cash_bridge: Decimal | None
    future_cash_schedule: tuple[FutureCashEvent, ...]
    future_setoff_schedule: tuple[FutureSetoffEvent, ...]
    sale_net_remittances: tuple[SaleNetRemittance, ...]
    business_cash: Decimal | None
    equity_cash: Decimal | None
    monthly_cash: tuple[MonthlyCash, ...] | None
    minimum_cash_balance: Decimal | None
    minimum_cash_at: datetime | None
    cash_shortage: Decimal | None
    target_values: dict[str, Decimal | None]


class EconomicLedger:
    """Trusted server injection boundary; request data never chooses this repository."""

    def __init__(self, repository: object):
        self._repository = repository

    def calculate(self, scenario: EconomicScenario) -> EconomicResult:
        scenario = EconomicScenario.model_validate(untrusted_data(scenario))
        scenario_sha256 = self._verify_scenario_pin(scenario)
        market = resolve_market_context(
            scenario.market_context, tenant_id=scenario.tenant_id,
            decision_at=scenario.decision_at, repository=self._repository,
        )
        if not isinstance(market, UnavailableMarketContext):
            raise ValueError("first G1 ledger requires an unavailable market context")
        validate_market_context_chain(
            scenario_context=scenario.scenario_market_context,
            economic_scenario_context=scenario.market_context,
            economic_result_context=market, assessment_context=market,
        )
        inputs = tuple(iter_economic_numbers(scenario))
        if not inputs:
            raise ValueError("economic scenario needs scoped user inputs")
        self._verify_inputs(scenario, inputs)
        self._verify_settlement_evidence(scenario)
        validate_first_g1_use(
            market,
            economic_inputs=tuple({"origin": item.origin, "evidence_level": item.evidence_level,
                                   "assumption_scope": item.assumption_scope} for item in inputs),
            assessment_status="hold",
        )
        try:
            with localcontext() as context:
                context.prec = 128
                context.traps[Inexact] = True
                return self._calculate_verified(scenario, market, inputs, scenario_sha256)
        except Inexact as exc:
            raise ValueError("economic arithmetic exceeds exact 128-digit domain") from exc

    def _verify_scenario_pin(self, scenario: EconomicScenario) -> str:
        digest = canonical_scenario_sha256(scenario)
        try:
            raw = self._repository.get_economic_scenario_pin(
                scenario.scenario_id, scenario.scenario_revision)
            if raw is None or not isinstance(raw, dict):
                raise ValueError("missing scenario pin")
            pin = OwnedScenarioPin.model_validate(untrusted_data(raw))
        except Exception as exc:
            raise ValueError("trusted scenario pin lookup failed") from exc
        if ((pin.tenant_id, pin.scenario_id, pin.scenario_revision, pin.decision_at) !=
                (scenario.tenant_id, scenario.scenario_id, scenario.scenario_revision,
                 scenario.decision_at)
                or pin.payload_sha256 != digest
                or pin.immutable_job_input_sha256 != digest):
            raise ValueError("scenario pin does not match immutable job input")
        return digest

    def _verify_inputs(self, scenario: EconomicScenario, inputs: tuple[EconomicNumber, ...]) -> None:
        seen = set()
        for item in inputs:
            key = (item.input_id, item.revision)
            if key in seen:
                raise ValueError("duplicate economic input reference")
            seen.add(key)
            if item.available_at > scenario.decision_at:
                raise ValueError("economic input unavailable at decision time")
            try:
                raw = self._repository.get_economic_input(*key)
                if raw is None or not isinstance(raw, dict):
                    raise ValueError("missing economic input")
                record = OwnedEconomicRecord.model_validate(untrusted_data(raw))
            except Exception as exc:
                raise ValueError("trusted economic input lookup failed") from exc
            if record.tenant_id != scenario.tenant_id:
                raise ValueError("foreign economic input")
            if (record.scope_start > scenario.period_start or
                    record.scope_end < scenario.period_end):
                raise ValueError("economic input scope does not cover evaluation period")
            if record.model_dump(exclude={"tenant_id", "scope_start", "scope_end"}) != item.model_dump():
                raise ValueError("economic input does not match owned revision")
        for lot in scenario.opening_inventory or ():
            if lot.prior_cost_ref is None:
                continue
            if None in (lot.prior_cost_amount, lot.allocation_basis, lot.allocation_policy):
                continue
            try:
                raw = self._repository.get_prior_batch_cost(lot.prior_cost_ref)
                if raw is None or not isinstance(raw, dict):
                    raise ValueError("missing prior batch cost")
                prior = PriorBatchCostRecord.model_validate(untrusted_data(raw))
            except Exception as exc:
                raise ValueError("trusted prior batch cost lookup failed") from exc
            if ((prior.cost_ref, prior.tenant_id, prior.batch_id, prior.grade, prior.channel) !=
                    (lot.prior_cost_ref, scenario.tenant_id, lot.batch_id, lot.grade, lot.channel)
                    or prior.available_at > scenario.decision_at
                    or prior.scope_start > scenario.period_start
                    or prior.scope_end < scenario.period_end
                    or prior.cost_amount != lot.prior_cost_amount
                    or prior.allocation_basis_kg != lot.allocation_basis
                    or prior.opening_quantity_kg != lot.quantity
                    or prior.allocation_policy != lot.allocation_policy):
                raise ValueError("prior batch cost reference does not match opening inventory")

    def _verify_settlement_evidence(self, scenario: EconomicScenario) -> None:
        for item in scenario.setoffs or ():
            try:
                raw = self._repository.get_settlement_evidence(
                    item.settlement_ref, item.evidence_revision)
                if raw is None or not isinstance(raw, dict):
                    raise ValueError("missing settlement evidence")
                record = OwnedSettlementRecord.model_validate(untrusted_data(raw))
            except Exception as exc:
                raise ValueError("trusted settlement evidence lookup failed") from exc
            payload = json.dumps(record.model_dump(mode="json", exclude={"raw_sha256"}),
                                 sort_keys=True, separators=(",", ":"), ensure_ascii=False)
            digest = sha256(payload.encode("utf-8")).hexdigest()
            if (record.raw_sha256 != digest or item.evidence_sha256 != digest
                    or (record.settlement_ref, record.revision, record.tenant_id,
                        record.sale_id, record.cost_id, record.at, record.amount) !=
                       (item.settlement_ref, item.evidence_revision, scenario.tenant_id,
                        item.sale_id, item.cost_id, item.at, item.amount)
                    or record.available_at > scenario.decision_at
                    or record.scope_start > scenario.period_start
                    or record.scope_end < max(scenario.period_end, day(item.at))):
                raise ValueError("settlement evidence does not match owned immutable revision, rights, or period")

    def _calculate_verified(self, s, market, inputs, scenario_sha256):
        declared_zeros = {item.group for item in s.zero_declarations}
        missing_zeros = {
            group for group in ZERO_GROUP_UNITS
            if getattr(s, group) == () and group not in declared_zeros
        }
        s = s.model_copy(update={group: None for group in missing_zeros})
        holds = ["MARKET_CONTEXT_UNAVAILABLE"]
        event_ids = []
        for events in (s.harvests, s.packouts, s.culls, s.cull_disposals, s.sales, s.collections,
                       s.returns, s.discounts, s.setoffs, s.disposals, s.variable_costs, s.fixed_costs,
                       s.depreciation, s.grants, s.asset_disposals, s.taxes, s.capex,
                       s.loan_draws, s.principal_payments, s.interest_payments):
            event_ids.extend(item.id for item in (events or ()))
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("duplicate economic event ID")
        cash_times = ([item.at for item in s.collections or ()]
                      + [item.refund_paid_at for item in s.returns or ()]
                      + [item.paid_at for item in (*(s.variable_costs or ()), *(s.fixed_costs or ()))
                         if item.paid_at is not None])
        if any(day(at) < s.period_start for at in cash_times):
            raise ValueError("before-period cash unsupported for first G1")

        for field in ("cull_disposals", "opening_inventory", "collections", "returns", "discounts", "setoffs", "disposals",
                      "variable_costs", "fixed_costs", "depreciation", "assets", "grants",
                      "asset_disposals", "taxes", "capex", "loan_draws",
                      "principal_payments", "interest_payments", "debt_accounts", "opening_cash"):
            if getattr(s, field) is None:
                holds.append(f"{field.upper()}_UNDECLARED")
        asset_schedules_complete = self._validate_accounts(s)
        if not asset_schedules_complete:
            holds.append("DEPRECIATION_SCHEDULE_INCOMPLETE")

        harvest_by_id = {item.id: item for item in s.harvests}
        if len(harvest_by_id) != len(s.harvests):
            raise ValueError("duplicate harvest")
        harvested_batches = {item.batch_id for item in s.harvests}
        if len(harvested_batches) != len(s.harvests):
            raise ValueError("batch harvest must be unique in this first ledger")
        opening_batches = [lot.batch_id for lot in s.opening_inventory or () if lot.batch_id is not None]
        if len(opening_batches) != len(set(opening_batches)) or harvested_batches.intersection(opening_batches):
            raise ValueError("opening inventory batch overlaps or duplicates another lot")
        for item in s.harvests:
            self._event_in_period(item.at, s)
            quantity(item.quantity)
        for item in (*s.packouts, *s.culls):
            self._event_in_period(item.at, s)
            harvest = harvest_by_id.get(item.harvest_id)
            if harvest is None or item.at < harvest.at:
                raise ValueError("packout or cull does not follow a harvest")
            if hasattr(item, "batch_id") and item.batch_id != harvest.batch_id:
                raise ValueError("packout batch differs from harvest")
            quantity(item.quantity)
        for harvest in s.harvests:
            packed = total(quantity(item.quantity) for item in s.packouts if item.harvest_id == harvest.id)
            culled = total(quantity(item.quantity) for item in s.culls if item.harvest_id == harvest.id)
            if packed + culled != quantity(harvest.quantity):
                raise ValueError("harvest must equal saleable packout plus cull")
        culls = {item.id: item for item in s.culls}
        for item in s.cull_disposals or ():
            self._event_in_period(item.at, s)
            cull = culls.get(item.cull_id)
            if cull is None or item.at < cull.at:
                raise ValueError("cull disposal needs an earlier cull")
            quantity(item.quantity)
        for cull in s.culls:
            if total(quantity(item.quantity) for item in s.cull_disposals or ()
                     if item.cull_id == cull.id) > quantity(cull.quantity):
                raise ValueError("cull disposal exceeds culled quantity")

        sales = {sale.id: sale for sale in s.sales}
        if len(sales) != len(s.sales):
            raise ValueError("duplicate sale")
        gross_by_sale = {}
        for sale in s.sales:
            stamps = (sale.dispatch_at, sale.delivery_at, sale.inspection_at, sale.recognized_at)
            if tuple(sorted(stamps)) != stamps or len({day(stamp) for stamp in stamps}) != 1:
                raise ValueError("first G1 requires ordered transfer events on one KST date")
            self._event_in_period(sale.recognized_at, s)
            if quantity(sale.quantity) == ZERO or sale.price.unit != "KRW/kg":
                raise ValueError("sale needs positive kg and gross KRW/kg contract price")
            gross_by_sale[sale.id] = quantity(sale.quantity) * sale.price.amount

        returned_by_sale = defaultdict(lambda: ZERO)
        refunds_by_sale = defaultdict(lambda: ZERO)
        for item in s.returns or ():
            sale = sales.get(item.sale_id)
            if sale is None or item.at < sale.recognized_at or item.refund_paid_at < item.at:
                raise ValueError("return needs an earlier original sale")
            self._event_in_period(item.at, s)
            returned_by_sale[item.sale_id] += quantity(item.quantity)
            refunds_by_sale[item.sale_id] += money(item.refund)
        discounts_by_sale = defaultdict(lambda: ZERO)
        for item in s.discounts or ():
            sale = sales.get(item.sale_id)
            if sale is None or item.at < sale.recognized_at:
                raise ValueError("discount needs an earlier original sale")
            self._event_in_period(item.at, s)
            discounts_by_sale[item.sale_id] += money(item.amount)
        costs_by_id = {cost.id: cost for cost in s.variable_costs or ()}
        setoff_by_cost = {}
        setoff_by_sale = defaultdict(lambda: ZERO)
        for item in s.setoffs or ():
            sale = sales.get(item.sale_id)
            cost = costs_by_id.get(item.cost_id)
            if (sale is None or cost is None or cost.purpose != "sale"
                    or cost.sale_id != item.sale_id
                    or cost.batch_id not in (None, sale.batch_id)):
                raise ValueError("setoff needs the same sale's variable sale cost")
            if item.cost_id in setoff_by_cost:
                raise ValueError("one settlement setoff per cost")
            if cost.payment is not None or cost.paid_at is not None:
                raise ValueError("setoff cost cannot also have bank payment")
            if item.at < max(sale.recognized_at, cost.incurred_at):
                raise ValueError("setoff precedes recognized sale or incurred cost")
            if money(item.amount) != cost.quantity.amount * cost.unit_cost.amount:
                raise ValueError("setoff must fully equal incurred sale cost")
            setoff_by_cost[item.cost_id] = item
            setoff_by_sale[item.sale_id] += money(item.amount)
        for sale in s.sales:
            if returned_by_sale[sale.id] > quantity(sale.quantity):
                raise ValueError("returns exceed original sale quantity")
            if refunds_by_sale[sale.id] + discounts_by_sale[sale.id] > gross_by_sale[sale.id]:
                raise ValueError("sale adjusted more than once or beyond gross value")
        for item in s.discounts or ():
            if (money(item.amount) > ZERO and total(
                money(collection.amount) for collection in s.collections or ()
                if collection.sale_id == item.sale_id and collection.at < item.at
            ) > ZERO):
                raise ValueError("DISCOUNT_AFTER_COLLECTION_CASH_CORRECTION_UNSUPPORTED")
        for item in s.collections or ():
            sale = sales.get(item.sale_id)
            if sale is None or item.at < sale.recognized_at:
                raise ValueError("collection needs an earlier recognized sale")
            money(item.amount)
        for sale in s.sales:
            collected = total(money(item.amount) for item in s.collections or () if item.sale_id == sale.id)
            if collected + setoff_by_sale[sale.id] + discounts_by_sale[sale.id] > gross_by_sale[sale.id]:
                raise ValueError("collections, discounts, and setoffs exceed gross sale")

        closing_inventory = self._inventory(s, holds)
        sale_net_remittances = []
        for sale in s.sales:
            net_amount = (gross_by_sale[sale.id] - discounts_by_sale[sale.id] - setoff_by_sale[sale.id]
                          if s.setoffs is not None and s.discounts is not None else None)
            related_collections = [item for item in s.collections or () if item.sale_id == sale.id]
            if s.setoffs is None:
                reason = "SETTLEMENT_UNDECLARED"
            elif s.discounts is None:
                reason = "DISCOUNTS_UNDECLARED"
            elif s.returns is None:
                reason = "RETURNS_UNDECLARED"
            elif any(item.sale_id == sale.id for item in s.returns):
                reason = "RETURN_PRESENT"
            elif closing_inventory is None:
                reason = "INVENTORY_UNRECONCILED"
            elif any(item.sale_id == sale.id and not in_period(item.at, s) for item in s.setoffs):
                reason = "SETTLEMENT_AFTER_PERIOD"
            elif s.collections is None:
                reason = "COLLECTIONS_UNDECLARED"
            elif any(not in_period(item.at, s) for item in related_collections):
                reason = "COLLECTION_AFTER_PERIOD"
            elif total(money(item.amount) for item in related_collections) != net_amount:
                reason = "COLLECTION_INCOMPLETE"
            else:
                reason = None
            sale_net_remittances.append(SaleNetRemittance(
                sale_id=sale.id, amount=net_amount,
                per_kg=(remittance_per_kg(net_amount, quantity(sale.quantity))
                        if reason is None else None),
                status="conditional_user_assumption" if reason is None else "hold",
                hold_reason=reason,
            ))
            if reason is not None:
                holds.append(f"SALE_NET_REMITTANCE_{sale.id}:{reason}")

        variable_cost = self._costs(s.variable_costs, s, harvested_batches, sales)
        fixed_cost = self._costs(s.fixed_costs, s, harvested_batches, sales)
        depreciation = required_sum(s.depreciation) if asset_schedules_complete else None
        closing_inventory_cost = (self._inventory_cost(s, closing_inventory)
                                  if variable_cost is not None and fixed_cost is not None else None)
        gross = total(gross_by_sale.values())
        revenue = (gross - total(refunds_by_sale.values()) - total(discounts_by_sale.values())
                   if s.returns is not None and s.discounts is not None
                   and closing_inventory is not None else None)
        oi = (revenue - variable_cost - fixed_cost - depreciation
              if None not in (revenue, variable_cost, fixed_cost, depreciation)
              and closing_inventory is not None and s.assets is not None
              and s.cull_disposals is not None else None)

        op_events = []
        future_events = []
        future_setoffs = tuple(sorted((FutureSetoffEvent(
            item.id, item.sale_id, item.cost_id, item.at, money(item.amount))
            for item in s.setoffs or () if not in_period(item.at, s)), key=lambda event: event.at))
        operating_cash = None
        cash_rows = (
            [(item.id, item.at, money(item.amount), "collection") for item in s.collections or ()]
            + [(item.id, item.refund_paid_at, -money(item.refund), "refund") for item in s.returns or ()]
            + [(item.id, item.paid_at, -money(item.payment), category)
               for name, category in (("variable_costs", "variable_cost_payment"),
                                      ("fixed_costs", "fixed_cost_payment"))
               for item in getattr(s, name) or () if item.paid_at is not None]
        )
        for event_id, at, amount, category in cash_rows:
            if day(at) < s.period_start:
                raise ValueError("before-period cash unsupported for first G1")
            if day(at) > s.period_end:
                future_events.append(FutureCashEvent(event_id, at, amount, category))
            else:
                op_events.append((at, amount))
        future_events.sort(key=lambda event: event.at)
        bridge_opening_names = ("opening_receivable", "opening_refund_payable", "opening_operating_payable")
        for name in bridge_opening_names:
            value = getattr(s, name)
            if value is None:
                holds.append(f"{name.upper()}_UNDECLARED")
            elif money(value) != ZERO:
                raise ValueError(f"unsupported nonzero opening {name}")
        if (s.collections is not None and s.returns is not None and s.setoffs is not None
                and s.variable_costs is not None
                and s.fixed_costs is not None and s.discounts is not None
                and s.cull_disposals is not None and s.opening_inventory is not None
                and s.disposals is not None and closing_inventory is not None
                and all(getattr(s, name) is not None for name in bridge_opening_names)
                and all(cost.payment is not None or cost.id in setoff_by_cost
                        for cost in (*s.variable_costs, *s.fixed_costs))):
            operating_cash = total(amount for _, amount in op_events)
        elif any(cost.payment is None and cost.id not in setoff_by_cost
                 for cost in (*(s.variable_costs or ()), *(s.fixed_costs or ()))):
            holds.append("OPERATING_PAYMENT_UNDECLARED")

        ar_begin = money(s.opening_receivable) if s.opening_receivable is not None else None
        refund_begin = money(s.opening_refund_payable) if s.opening_refund_payable is not None else None
        payable_begin = money(s.opening_operating_payable) if s.opening_operating_payable is not None else None
        ar_end = refund_end = payable_end = bridge = None
        if (operating_cash is not None and None not in (ar_begin, refund_begin, payable_begin,
                                                       revenue, variable_cost, fixed_cost)):
            ar_end = ar_begin + gross - total(discounts_by_sale.values()) - total(
                money(item.amount) for item in s.collections if in_period(item.at, s)) - total(
                money(item.amount) for item in s.setoffs if in_period(item.at, s))
            refund_end = refund_begin + total(refunds_by_sale.values()) - total(
                money(item.refund) for item in s.returns if in_period(item.refund_paid_at, s))
            payable_end = payable_begin + variable_cost + fixed_cost - total(
                money(item.payment) for item in (*s.variable_costs, *s.fixed_costs)
                if item.paid_at is not None and in_period(item.paid_at, s)) - total(
                money(item.amount) for item in s.setoffs if in_period(item.at, s))
            if min(ar_end, refund_end, payable_end) < ZERO:
                raise ValueError("cash bridge balance is negative")
            if oi is not None:
                bridge = (oi + depreciation - (ar_end - ar_begin)
                          + (refund_end - refund_begin) + (payable_end - payable_begin))
                if bridge != operating_cash:
                    raise ValueError("operating income to cash bridge does not reconcile")

        business_events = []
        business_cash = None
        if operating_cash is not None and all(getattr(s, name) is not None for name in
                                               ("assets", "grants", "asset_disposals", "taxes", "capex")):
            for name, sign in (("grants", 1), ("asset_disposals", 1), ("taxes", -1), ("capex", -1)):
                business_events += [(item.at, sign * money(item.amount)) for item in getattr(s, name)]
            business_cash = operating_cash + total(amount for at, amount in business_events if in_period(at, s))

        equity_events = []
        equity_cash = None
        if business_cash is not None and all(getattr(s, name) is not None for name in
                                              ("debt_accounts", "loan_draws", "principal_payments", "interest_payments")):
            for name, sign in (("loan_draws", 1), ("principal_payments", -1), ("interest_payments", -1)):
                equity_events += [(item.at, sign * money(item.amount)) for item in getattr(s, name)]
            equity_cash = business_cash + total(amount for at, amount in equity_events if in_period(at, s))

        monthly_cash = None
        minimum_cash_balance = minimum_cash_at = cash_shortage = None
        if equity_cash is not None and s.opening_cash is not None:
            opening = money(s.opening_cash)
            events = op_events + business_events + equity_events
            monthly = []
            year, month_number = s.period_start.year, s.period_start.month
            while (year, month_number) <= (s.period_end.year, s.period_end.month):
                key = f"{year:04d}-{month_number:02d}"
                boundary = (s.period_start if (year, month_number) ==
                            (s.period_start.year, s.period_start.month)
                            else date(year, month_number, 1))
                minimum_at = datetime.combine(boundary, datetime.min.time(), tzinfo=KST).astimezone(timezone.utc)
                minimum_balance = balance = opening
                by_instant = defaultdict(lambda: ZERO)
                for at, amount in events:
                    if in_period(at, s) and month(at) == key:
                        by_instant[at] += amount
                for at, amount in sorted(by_instant.items()):
                    balance += amount
                    if balance < minimum_balance:
                        minimum_balance, minimum_at = balance, at
                net = balance - opening
                monthly.append(MonthlyCash(key, opening, net, balance, minimum_balance,
                                           minimum_at, max(ZERO, -minimum_balance)))
                opening += net
                month_number += 1
                if month_number == 13:
                    year, month_number = year + 1, 1
            monthly_cash = tuple(monthly)
            if total(item.net for item in monthly_cash) != equity_cash:
                raise ValueError("monthly cash does not reconcile to equity cash")
            worst = min(monthly_cash, key=lambda item: (item.minimum_balance, item.minimum_at))
            minimum_cash_balance = worst.minimum_balance
            minimum_cash_at = worst.minimum_at
            cash_shortage = worst.shortage

        net_sold = (total(quantity(sale.quantity) for sale in s.sales) -
                    total(quantity(item.quantity) for item in s.returns)
                    if s.returns is not None else None)
        result_id = sha256(json.dumps({"scenario_sha256": scenario_sha256,
                                      "formula_version": FORMULA_VERSION},
                                     sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        targets = {"oi": oi, "operating_cash": operating_cash,
                   "cumulative_equity_cash": equity_cash}
        return EconomicResult(
            result_id=result_id, scenario_id=s.scenario_id,
            scenario_revision=s.scenario_revision, scenario_sha256=scenario_sha256,
            decision_at=s.decision_at,
            formula_version=FORMULA_VERSION, market_context=market,
            assessment_market_context=market, assessment_status="hold", forecast_run_id=None,
            input_versions=tuple((item.input_id, item.revision) for item in inputs),
            input_provenance=inputs,
            hold_reasons=tuple(holds), harvest_kg=total(quantity(item.quantity) for item in s.harvests),
            packout_kg=total(quantity(item.quantity) for item in s.packouts),
            cull_disposed_kg=(total(quantity(item.quantity) for item in s.cull_disposals)
                              if s.cull_disposals is not None else None),
            recognized_kg=total(quantity(item.quantity) for item in s.sales),
            net_sold_kg=net_sold, closing_inventory=closing_inventory,
            closing_inventory_cost_by_batch=closing_inventory_cost, gross_sales=gross,
            sales_totals_status=("inventory_reconciled" if closing_inventory is not None
                                 else "unverified_input_arithmetic"),
            revenue=revenue, variable_cost=variable_cost, fixed_cost=fixed_cost,
            depreciation=depreciation, management_oi=oi, operating_cash=operating_cash,
            receivable_begin=ar_begin, receivable_end=ar_end,
            refund_payable_begin=refund_begin, refund_payable_end=refund_end,
            operating_payable_begin=payable_begin, operating_payable_end=payable_end,
            operating_cash_bridge=bridge, future_cash_schedule=tuple(future_events),
            future_setoff_schedule=future_setoffs, sale_net_remittances=tuple(sale_net_remittances),
            business_cash=business_cash, equity_cash=equity_cash, monthly_cash=monthly_cash,
            minimum_cash_balance=minimum_cash_balance, minimum_cash_at=minimum_cash_at,
            cash_shortage=cash_shortage,
            target_values=targets,
        )

    @staticmethod
    def _event_in_period(at, scenario):
        if not in_period(at, scenario):
            raise ValueError("economic event falls outside evaluation period")

    def _costs(self, events, scenario, harvested_batches, sales):
        if events is None:
            return None
        amounts = []
        for cost in events:
            self._event_in_period(cost.incurred_at, scenario)
            if cost.purpose == "production" and cost.batch_id not in harvested_batches:
                raise ValueError("production batch cost cannot be charged again for opening inventory")
            if cost.purpose == "sale":
                sale = sales.get(cost.sale_id)
                if sale is None or (cost.batch_id is not None and cost.batch_id != sale.batch_id):
                    raise ValueError("sale cost needs an existing sale and matching batch")
            expected = {"kg": "KRW/kg", "month": "KRW/month", "kWh_e": "KRW/kWh_e", "L": "KRW/L"}
            if expected.get(cost.quantity.unit) != cost.unit_cost.unit:
                raise ValueError("cost driver and unit price do not match")
            incurred = cost.quantity.amount * cost.unit_cost.amount
            if cost.payment is not None and money(cost.payment) > incurred:
                raise ValueError("single cost payment exceeds incurred cost")
            amounts.append(incurred)
        return total(amounts)

    def _validate_accounts(self, s):
        for name in ("depreciation", "capex", "asset_disposals", "grants", "taxes",
                     "loan_draws", "principal_payments", "interest_payments"):
            for item in getattr(s, name) or ():
                self._event_in_period(item.at, s)
        asset_ids = {account.id for account in s.assets or ()}
        if s.assets is not None and len(asset_ids) != len(s.assets):
            raise ValueError("duplicate asset account")
        basis = {account.id: money(account.opening_basis) for account in s.assets or ()}
        for name in ("depreciation", "capex", "asset_disposals"):
            for item in getattr(s, name) or ():
                if item.asset_id is None or item.asset_id not in asset_ids or item.loan_id is not None:
                    raise ValueError("asset event needs a declared matching asset account")
                money(item.amount)
        disposal_at = {}
        for item in s.asset_disposals or ():
            if item.asset_id in disposal_at:
                raise ValueError("duplicate asset disposal")
            disposal_at[item.asset_id] = item.at
        basis_events = (
            [(item.at, 0, item.asset_id, money(item.amount)) for item in s.capex or ()]
            + [(item.at, 1, item.asset_id, money(item.amount)) for item in s.depreciation or ()]
            + [(item.at, 2, item.asset_id, ZERO) for item in s.asset_disposals or ()]
        )
        for at, kind, asset_id, amount in sorted(basis_events):
            if kind == 2:
                basis[asset_id] = ZERO
                continue
            if asset_id in disposal_at and at >= disposal_at[asset_id]:
                raise ValueError("asset event at or after disposal")
            basis[asset_id] += amount if kind == 0 else -amount
            if basis[asset_id] < ZERO:
                raise ValueError("depreciation exceeds available asset basis")
        schedules_complete = all(getattr(s, name) is not None for name in
                                 ("assets", "capex", "depreciation", "asset_disposals"))
        for account in s.assets or ():
            if account.installed_at is not None and any(
                event.asset_id == account.id and event.at < account.installed_at
                for event in s.depreciation or ()
            ):
                raise ValueError("depreciation event before installation")
            fields = (account.acquisition_cost, account.acquired_at, account.installed_at,
                      account.residual_value, account.useful_life_days,
                      account.opening_accumulated_depreciation)
            if any(value is None for value in fields):
                schedules_complete = False
                continue
            acquisition = money(account.acquisition_cost)
            residual = money(account.residual_value)
            accumulated = money(account.opening_accumulated_depreciation)
            if account.useful_life_days.unit != "day" or account.useful_life_days.amount != account.useful_life_days.amount.to_integral_value():
                raise ValueError("depreciation schedule needs whole useful life days")
            life = int(account.useful_life_days.amount)
            if (life <= 0 or acquisition <= ZERO or residual > acquisition
                    or account.installed_at < account.acquired_at):
                raise ValueError("invalid depreciation schedule parameters")
            before_start = s.period_start - timedelta(days=1)
            if day(account.acquired_at) < s.period_start:
                if (money(account.opening_basis) != acquisition - accumulated
                        or accumulated != self._schedule_cumulative(account, before_start)):
                    raise ValueError("depreciation schedule opening book basis mismatch")
                if any(item.asset_id == account.id for item in s.capex or ()):
                    raise ValueError("opening asset cannot be acquired again")
            else:
                if money(account.opening_basis) != ZERO or accumulated != ZERO:
                    raise ValueError("depreciation schedule opening book basis mismatch")
                purchases = [item for item in s.capex or () if item.asset_id == account.id]
                if (s.capex is not None and
                        (len(purchases) != 1 or purchases[0].at != account.acquired_at
                         or money(purchases[0].amount) != acquisition)):
                    raise ValueError("capex does not match pinned asset acquisition")
            if schedules_complete:
                limit = (day(disposal_at[account.id]) - timedelta(days=1)
                         if account.id in disposal_at else s.period_end)
                limit = min(limit, s.period_end)
                prior = accumulated
                for item in sorted((event for event in s.depreciation or ()
                                    if event.asset_id == account.id), key=lambda event: event.at):
                    expected = self._schedule_cumulative(account, min(day(item.at), limit)) - prior
                    if money(item.amount) != expected:
                        raise ValueError("depreciation schedule event amount mismatch")
                    prior += expected
                if prior != self._schedule_cumulative(account, limit):
                    raise ValueError("depreciation schedule period amount incomplete")
        for name in ("grants", "taxes"):
            for item in getattr(s, name) or ():
                if item.asset_id is not None or item.loan_id is not None:
                    raise ValueError("grant or tax cannot claim an asset or loan account")
                money(item.amount)

        debt = {account.id: money(account.opening_principal) for account in s.debt_accounts or ()}
        if s.debt_accounts is not None and len(debt) != len(s.debt_accounts):
            raise ValueError("duplicate debt account")
        debt_events = []
        for name, sign in (("loan_draws", 1), ("principal_payments", -1), ("interest_payments", 0)):
            for item in getattr(s, name) or ():
                if item.loan_id is None or item.loan_id not in debt or item.asset_id is not None:
                    raise ValueError("debt event needs a declared matching debt account")
                amount = money(item.amount)
                if sign:
                    debt_events.append((item.at, sign, item.loan_id, amount))
        for _, sign, loan_id, amount in sorted(debt_events):
            debt[loan_id] += sign * amount
            if debt[loan_id] < ZERO:
                raise ValueError("principal repayment exceeds declared debt")
        return schedules_complete

    @staticmethod
    def _schedule_cumulative(account, through):
        life = int(account.useful_life_days.amount)
        elapsed = min(life, max(0, (through - day(account.installed_at)).days + 1))
        if elapsed == 0:
            return ZERO
        depreciable = money(account.acquisition_cost) - money(account.residual_value)
        if elapsed == life:
            return depreciable
        with localcontext() as context:
            context.traps[Inexact] = False
            return (depreciable * Decimal(elapsed) / Decimal(life)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _inventory(self, s, holds):
        if s.opening_inventory is not None and any(
            None in (lot.grade, lot.batch_id, lot.channel, lot.prior_cost_ref)
            for lot in s.opening_inventory
        ):
            holds.append("OPENING_INVENTORY_LINKAGE_UNKNOWN")
            return None
        if s.opening_inventory is not None and any(
            None in (lot.prior_cost_amount, lot.allocation_basis, lot.allocation_policy)
            for lot in s.opening_inventory
        ):
            holds.append("OPENING_INVENTORY_COST_UNKNOWN")
            return None
        if s.opening_inventory is None or s.disposals is None or s.returns is None:
            return None
        balances = defaultdict(lambda: ZERO)
        for lot in s.opening_inventory:
            if (money(lot.prior_cost_amount) < ZERO or quantity(lot.allocation_basis) <= ZERO
                    or quantity(lot.quantity) <= ZERO
                    or quantity(lot.quantity) > quantity(lot.allocation_basis)):
                raise ValueError("invalid opening inventory cost allocation basis")
            balances[(lot.batch_id, lot.grade, lot.channel)] += quantity(lot.quantity)
        events = []
        for item in s.packouts:
            events.append((item.at, 0, (item.batch_id, item.grade, item.channel), quantity(item.quantity)))
        for item in s.disposals:
            self._event_in_period(item.at, s)
            events.append((item.at, 1, (item.batch_id, item.grade, item.channel), -quantity(item.quantity)))
        for sale in s.sales:
            events.append((sale.dispatch_at, 2, (sale.batch_id, sale.grade, sale.channel), -quantity(sale.quantity)))
        sales = {sale.id: sale for sale in s.sales}
        for item in s.returns:
            if item.disposition == "resaleable":
                sale = sales[item.sale_id]
                events.append((item.at, 3, (sale.batch_id, sale.grade, sale.channel), quantity(item.quantity)))
        for _, _, key, delta in sorted(events):
            balances[key] += delta
            if balances[key] < ZERO:
                raise ValueError("sale or disposal exceeds available saleable stock")
        return dict(balances)

    def _inventory_cost(self, s, balances):
        if balances is None:
            return None
        costs = defaultdict(lambda: ZERO)
        def proportional(amount, remaining, basis):
            with localcontext() as context:
                context.traps[Inexact] = False
                return (amount * remaining / basis).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        for lot in s.opening_inventory:
            remaining = balances[(lot.batch_id, lot.grade, lot.channel)]
            costs[lot.batch_id] += proportional(money(lot.prior_cost_amount), remaining,
                                                quantity(lot.allocation_basis))
        by_batch = defaultdict(lambda: ZERO)
        for item in (*s.variable_costs, *s.fixed_costs):
            if item.purpose == "production":
                by_batch[item.batch_id] += item.quantity.amount * item.unit_cost.amount
        packed = defaultdict(lambda: ZERO)
        remaining = defaultdict(lambda: ZERO)
        for item in s.packouts:
            packed[item.batch_id] += quantity(item.quantity)
        for (batch, _, _), amount in balances.items():
            remaining[batch] += amount
        for batch in {item.batch_id for item in s.harvests}:
            if packed[batch] <= ZERO:
                if remaining[batch] > ZERO:
                    raise ValueError("saleable stock has no packout allocation basis")
                costs[batch] += ZERO
            else:
                costs[batch] += proportional(by_batch[batch], remaining[batch], packed[batch])
        return dict(costs)
