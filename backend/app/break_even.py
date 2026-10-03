"""Conditional finite-grid break-even scan over pinned full market scenarios.

Every point is a separately pinned joint shock and a fresh MarketScenarioService
calculation. The explicit grid proves only exact zeroes at its listed values;
crossings between points remain brackets, not inferred roots or forecasts.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, Inexact, localcontext
from hashlib import sha256
import json
import re
from typing import Literal

from pydantic import Field, field_validator

from app.economic_contracts import EconomicScenario, untrusted_data, utc
from app.economics import canonical_scenario_sha256
from app.market import UnavailableMarketContext
from app.market_scenario import (BaselineRef, JointShock, MarketScenarioResult,
                                 MarketScenarioService)
from app.provenance import Digest, FrozenContract, Name


_DECIMAL = re.compile(r"^(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_TARGETS = {"oi": "management_oi", "operating_cash": "operating_cash",
            "cumulative_equity_cash": "equity_cash"}


def _number(value: str) -> str:
    if type(value) is not str or len(value) > 64 or not _DECIMAL.fullmatch(value):
        raise ValueError("break-even grid value must be a nonnegative decimal string")
    return value


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


class BreakEvenRequest(FrozenContract):
    schema_version: Literal["1"]
    plan_id: Name
    baseline: BaselineRef
    market_context: UnavailableMarketContext
    decision_at: datetime
    period_start: date
    period_end: date
    target: Literal["oi", "operating_cash", "cumulative_equity_cash"]
    variable: Literal["kg", "KRW/kg"]
    sale_id: Name
    batch_id: Name
    grade: Name
    channel: Name
    dispatch_at: datetime
    delivery_at: datetime
    inspection_at: datetime
    recognized_at: datetime
    collection_id: Name
    collection_at: datetime
    minimum: str
    maximum: str
    step: str

    _times_utc = field_validator("decision_at", "dispatch_at", "delivery_at",
                                 "inspection_at", "recognized_at", "collection_at")(utc)
    _decimals = field_validator("minimum", "maximum", "step")(_number)


class TrialRef(FrozenContract):
    ordinal: int = Field(ge=0)
    value: str
    scenario_id: Name
    revision: Name
    scenario_sha256: Digest

    _value_decimal = field_validator("value")(_number)


class BreakEvenPlan(FrozenContract):
    plan_id: Name
    tenant_id: Name
    request_sha256: Digest
    fixed_inputs_sha256: Digest
    fixed_shock_sha256: Digest
    immutable: Literal[True]
    trials: tuple[TrialRef, ...] = Field(min_length=2, max_length=256)


@dataclass(frozen=True)
class TrialObservation:
    value: Decimal
    scenario_id: str
    market_result_id: str
    economic_result_id: str
    target_value: Decimal
    minimum_cash_balance: Decimal | None
    cash_shortage: Decimal | None


@dataclass(frozen=True)
class BreakEvenResult:
    status: Literal["zero_on_grid", "no_zero_on_grid", "bracket_only",
                    "nonmonotone_on_grid", "hold"]
    scope: Literal["conditional_user_grid_only"]
    assessment_status: Literal["hold"]
    target: str
    variable: str
    minimum: Decimal
    maximum: Decimal
    step: Decimal
    zero_values: tuple[Decimal, ...]
    brackets: tuple[tuple[Decimal, Decimal], ...]
    trials: tuple[TrialObservation, ...]
    hold_reasons: tuple[str, ...]


def canonical_request_sha256(value: object) -> str:
    request = BreakEvenRequest.model_validate(untrusted_data(value))
    return sha256(_canonical(request.model_dump(mode="json"))).hexdigest()


def fixed_trial_sha256(scenario: EconomicScenario, variable: str, sale_id: str) -> str:
    """Hash fields promised fixed across a trial family, excluding linked responses."""
    scenario = EconomicScenario.model_validate(untrusted_data(scenario))
    if variable not in ("kg", "KRW/kg"):
        raise ValueError("unsupported break-even variable")
    payload = scenario.model_dump(mode="json")
    payload.pop("scenario_id")
    payload.pop("scenario_revision")
    sales = [item for item in payload["sales"] if item["id"] == sale_id]
    if len(sales) != 1:
        raise ValueError("break-even sale missing or duplicated")
    mutable_number = sales[0]["quantity" if variable == "kg" else "price"]
    mutable_number.pop("value")
    mutable_number.pop("revision")
    for collection in payload["collections"] or ():
        if collection["sale_id"] == sale_id:
            collection["amount"].pop("value")
            collection["amount"].pop("revision")
    if variable == "kg":
        for cost in payload["variable_costs"] or ():
            if cost["sale_id"] == sale_id:
                for key in ("quantity", "payment"):
                    if cost[key] is not None:
                        cost[key].pop("value")
                        cost[key].pop("revision")
    return sha256(_canonical(payload)).hexdigest()


def fixed_shock_sha256(shock: JointShock, variable: str, sale_id: str,
                       collection_id: str) -> str:
    """Pin the joint shock, including contract caps, across all trial values."""
    shock = JointShock.model_validate(untrusted_data(shock))
    payload = shock.model_dump(mode="json")
    payload.pop("shock_id")
    payload.pop("revision")
    payload.pop("settlement_bindings")
    field = "quantity" if variable == "kg" else "price"
    for driver in payload["drivers"]:
        for edit in driver["changes"]:
            if ((edit["event_group"], edit["event_id"], edit["field"]) in
                    {("sales", sale_id, field),
                     ("collections", collection_id, "amount")}):
                edit["number"].pop("value")
                edit["number"].pop("revision")
    return sha256(_canonical(payload)).hexdigest()


def _grid(request: BreakEvenRequest) -> tuple[Decimal, ...]:
    lower, upper, step = map(Decimal, (request.minimum, request.maximum, request.step))
    if step <= 0 or upper <= lower:
        raise ValueError("break-even grid needs a positive step and range")
    try:
        with localcontext() as context:
            context.prec = 200
            context.traps[Inexact] = True
            intervals = (upper - lower) / step
            if intervals != intervals.to_integral_value() or not 1 <= intervals <= 255:
                raise ValueError("break-even grid must cover 2 to 256 exact points")
            return tuple(lower + step * i for i in range(int(intervals) + 1))
    except Inexact as exc:
        raise ValueError("break-even range is not an exact multiple of step") from exc


def _trusted(repository: object, method: str, *args):
    try:
        value = getattr(repository, method)(*args)
    except Exception as exc:
        raise ValueError(f"trusted {method} lookup failed") from exc
    if value is None:
        raise ValueError(f"trusted {method} reference missing")
    return value


def _sale_and_collection(request: BreakEvenRequest, scenario: EconomicScenario,
                         value: Decimal) -> None:
    sales = [item for item in scenario.sales if item.id == request.sale_id]
    collections = [item for item in scenario.collections or ()
                   if item.id == request.collection_id]
    if len(sales) != 1 or len(collections) != 1:
        raise ValueError("break-even sale or collection identity differs")
    sale, collection = sales[0], collections[0]
    amount = sale.quantity if request.variable == "kg" else sale.price
    if (amount.unit != request.variable or amount.amount != value or
            (sale.batch_id, sale.grade, sale.channel) !=
            (request.batch_id, request.grade, request.channel) or
            (sale.dispatch_at, sale.delivery_at, sale.inspection_at, sale.recognized_at) !=
            (request.dispatch_at, request.delivery_at, request.inspection_at,
             request.recognized_at) or
            (collection.sale_id, collection.at) !=
            (request.sale_id, request.collection_at)):
        raise ValueError("break-even trial changed sale scope or date")


class BreakEvenService:
    """Read only trusted pre-pinned trials; the client cannot supply a result."""

    def __init__(self, repository: object):
        self._repository = repository

    def scan(self, request_value: object, authenticated_tenant_id: str, *, check=None) -> BreakEvenResult:
        if check is not None and not callable(check):
            raise ValueError("break-even checkpoint invalid")
        if check is not None:
            check()
        request = BreakEvenRequest.model_validate(untrusted_data(request_value))
        if (_trusted(self._repository, "tenant_is_authenticated",
                     authenticated_tenant_id) is not True):
            raise ValueError("break-even tenant is not authenticated")
        values = _grid(request)
        plan = BreakEvenPlan.model_validate_json(_canonical(untrusted_data(_trusted(
            self._repository, "get_break_even_plan", request.plan_id))))
        if ((plan.plan_id, plan.tenant_id, plan.request_sha256) !=
                (request.plan_id, authenticated_tenant_id,
                 canonical_request_sha256(request)) or len(plan.trials) != len(values)):
            raise ValueError("break-even plan identity or grid differs")
        if len({(ref.scenario_id, ref.revision) for ref in plan.trials}) != len(values):
            raise ValueError("break-even plan repeats a scenario")
        observations = []
        for index, (value, ref) in enumerate(zip(values, plan.trials, strict=True)):
            if check is not None:
                check()
            if ref.ordinal != index or Decimal(ref.value) != value:
                raise ValueError("break-even trial grid differs")
            result = MarketScenarioService(self._repository).calculate_pinned(
                ref.scenario_id, ref.revision, authenticated_tenant_id)
            if not isinstance(result, MarketScenarioResult):
                raise ValueError("break-even trial is not a full market result")
            raw = _trusted(self._repository, "get_economic_scenario",
                           ref.scenario_id, ref.revision)
            scenario = EconomicScenario.model_validate(untrusted_data(raw))
            if ((scenario.tenant_id, scenario.scenario_id, scenario.scenario_revision,
                 scenario.decision_at, scenario.period_start, scenario.period_end,
                 scenario.market_context) !=
                    (authenticated_tenant_id, ref.scenario_id, ref.revision,
                     request.decision_at, request.period_start, request.period_end,
                     request.market_context) or result.baseline != request.baseline or
                    result.market_context != request.market_context or
                    result.assessment_status != "hold" or
                    canonical_scenario_sha256(scenario) != ref.scenario_sha256 or
                    result.economic_scenario_sha256 != ref.scenario_sha256 or
                    result.economic_result.scenario_sha256 != ref.scenario_sha256 or
                    fixed_trial_sha256(scenario, request.variable, request.sale_id) !=
                    plan.fixed_inputs_sha256):
                raise ValueError("break-even trial pin or fixed inputs differ")
            raw_shock = _trusted(self._repository, "get_joint_shock",
                                 result.joint_shock.shock_id, result.joint_shock.revision)
            if fixed_shock_sha256(raw_shock, request.variable, request.sale_id,
                                  request.collection_id) != plan.fixed_shock_sha256:
                raise ValueError("break-even fixed joint shock changed")
            _sale_and_collection(request, scenario, value)
            if check is not None:
                check()
            ledger = result.economic_result
            target_value = ledger.target_values.get(request.target)
            if (result.calculation_status != "conditional_user_assumption" or
                    target_value is None or
                    getattr(ledger, _TARGETS[request.target]) != target_value):
                return BreakEvenResult("hold", "conditional_user_grid_only", "hold",
                    request.target, request.variable, values[0], values[-1],
                    Decimal(request.step), (), (), (),
                    tuple(dict.fromkeys((*result.hold_reasons, "TARGET_UNRESOLVED"))))
            observations.append(TrialObservation(value, ref.scenario_id, result.result_id,
                ledger.result_id, target_value, ledger.minimum_cash_balance,
                ledger.cash_shortage))
        zeros = tuple(item.value for item in observations if item.target_value == 0)
        brackets = tuple((left.value, right.value)
                         for left, right in zip(observations, observations[1:])
                         if ((left.target_value < 0 < right.target_value) or
                             (right.target_value < 0 < left.target_value)))
        pairs = tuple(zip(observations, observations[1:]))
        if (any(right.target_value > left.target_value for left, right in pairs) and
                any(right.target_value < left.target_value for left, right in pairs)):
            status = "nonmonotone_on_grid"
        elif zeros:
            status = "zero_on_grid"
        elif brackets:
            status = "bracket_only"
        else:
            status = "no_zero_on_grid"
        return BreakEvenResult(status, "conditional_user_grid_only", "hold",
            request.target, request.variable, values[0], values[-1],
            Decimal(request.step), zeros, brackets, tuple(observations), ())
