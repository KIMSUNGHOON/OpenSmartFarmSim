"""Small market-context contract and fail-closed server-reference checks.

The repository argument is a trusted server boundary, not a client-supplied store.
The test fake establishes this contract only. Actual source authenticity and market
G0 approval require the later market-source-g0 implementation; this module does
not create or approve MarketSnapshots.
"""

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter, field_validator

from app.provenance import FrozenContract, Name


class AvailableMarketContext(FrozenContract):
    kind: Literal["available"]
    snapshot_id: Name


class UnavailableMarketContext(FrozenContract):
    kind: Literal["unavailable"]
    hold_report_id: Name


class UserAssumptionProjection(FrozenContract):
    origin: Literal["user"]
    evidence_level: Literal["assumed"]
    assumption_scope: Name


MarketContext = Annotated[
    AvailableMarketContext | UnavailableMarketContext, Field(discriminator="kind")
]
_context_adapter = TypeAdapter(MarketContext)


class _PinnedVintage(FrozenContract):
    vintage_id: Name
    revision_id: Name
    g0_evidence_id: Name


class _Snapshot(FrozenContract):
    market_snapshot_id: Name
    tenant_id: Name
    decision_at: datetime
    pinned_vintages: tuple[_PinnedVintage, ...] = Field(min_length=1)

    @field_validator("decision_at")
    @classmethod
    def utc_decision(cls, value: datetime) -> datetime:
        return _require_utc(value)


class _HoldReport(FrozenContract):
    hold_report_id: Name
    tenant_id: Name
    decision_at: datetime
    reasons: tuple[Name, ...] = Field(min_length=1)
    missing_evidence: tuple[Name, ...] = Field(min_length=1)
    decision_context_id: Name | None = None
    snapshot_id: Name | None = None
    claim_mode: Literal["ex_ante", "ex_post_replay"] | None = None
    decision_time_kind: Literal["actual", "hypothetical"] | None = None

    @field_validator("decision_at")
    @classmethod
    def utc_decision(cls, value: datetime) -> datetime:
        return _require_utc(value)


class _Rights(FrozenContract):
    access: Literal["allowed"]
    store: Literal["allowed"]
    transform: Literal["allowed"]
    display: Literal["allowed"]


class _Vintage(FrozenContract):
    vintage_id: Name
    revision_id: Name
    available_at: datetime
    retrieved_at: datetime
    rights: _Rights

    @field_validator("available_at", "retrieved_at")
    @classmethod
    def utc_time(cls, value: datetime) -> datetime:
        return _require_utc(value)


class _MarketG0Evidence(FrozenContract):
    evidence_id: Name
    tenant_id: Name
    vintage_id: Name
    revision_id: Name
    authenticated: Literal[True]
    approved: Literal[True]
    status: Literal["pass"]


def _require_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() != timedelta(0):
        raise ValueError("market time must be UTC-aware")
    return value


def _lookup(repository: object, method: str, *args: str) -> object:
    try:
        result = getattr(repository, method)(*args)
    except Exception as exc:
        raise ValueError("market repository lookup failed") from exc
    if result is None:
        raise ValueError("market repository reference is missing")
    return result


def _untrusted_data(value: object) -> object:
    """Expose even forged Pydantic fields before validating a boundary object.

    Pydantic accepts an existing model without checking model_construct or
    model_copy(update=...) mutations. model_dump would also discard forbidden
    attributes inserted by model_copy, so read the instance's raw fields.
    """
    if isinstance(value, BaseModel):
        fields = dict(vars(value))
        if value.model_extra:
            fields.update(value.model_extra)
        return {key: _untrusted_data(item) for key, item in fields.items()}
    if isinstance(value, Mapping):
        return {key: _untrusted_data(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return tuple(_untrusted_data(item) for item in value)
    if isinstance(value, list):
        return [_untrusted_data(item) for item in value]
    return value


def _validated_context(value: object) -> MarketContext:
    return _context_adapter.validate_python(_untrusted_data(value))


def _record(record_type: type, value: object) -> object:
    if not isinstance(value, Mapping):
        raise ValueError("market repository record is malformed")
    try:
        return record_type.model_validate(_untrusted_data(value))
    except ValueError as exc:
        raise ValueError("market repository record is malformed") from exc


def resolve_market_context(
    market: MarketContext,
    *,
    tenant_id: str,
    decision_at: datetime,
    repository: object,
    decision_context_id: str | None = None,
    input_snapshot_id: str | None = None,
    claim_mode: str | None = None,
    decision_time_kind: str | None = None,
) -> MarketContext:
    """Verify an ID against tenant-owned server records at a UTC decision time."""
    market = _validated_context(market)
    if not isinstance(tenant_id, str) or not tenant_id or tenant_id != tenant_id.strip():
        raise ValueError("tenant ID is invalid")
    _require_utc(decision_at)
    if _lookup(repository, "tenant_is_authenticated", tenant_id) is not True:
        raise ValueError("tenant is not authenticated")

    if isinstance(market, UnavailableMarketContext):
        report = _record(
            _HoldReport, _lookup(repository, "get_market_hold_report", market.hold_report_id)
        )
        if (report.hold_report_id, report.tenant_id, report.decision_at) != (
            market.hold_report_id, tenant_id, decision_at
        ):
            raise ValueError("market hold report does not match the request")
        context_fields = (decision_context_id, input_snapshot_id,
                          claim_mode, decision_time_kind)
        report_fields = (report.decision_context_id, report.snapshot_id,
                         report.claim_mode, report.decision_time_kind)
        if any(value is not None for value in (*context_fields, *report_fields)):
            if not all(isinstance(value, str) and value for value in report_fields):
                raise ValueError("market hold report decision context differs")
            signed = _lookup(repository, "get_decision_context", tenant_id,
                             report.snapshot_id, report.decision_context_id)
            if not isinstance(signed, Mapping):
                raise ValueError("market hold decision context is malformed")
            try:
                signed_decision = datetime.fromisoformat(
                    signed["decision_at_utc"].replace("Z", "+00:00"))
            except (KeyError, AttributeError, ValueError) as exc:
                raise ValueError("market hold signed decision time is invalid") from exc
            signed_fields = (signed.get("decision_context_id"),
                             signed.get("snapshot_id"), signed.get("claim_mode"),
                             signed.get("decision_time_kind"))
            if (signed.get("tenant_id") != tenant_id or
                    signed_decision != decision_at or signed_fields != report_fields or
                    (any(value is not None for value in context_fields) and
                     context_fields != signed_fields)):
                raise ValueError("market hold report decision context differs")
        return market

    snapshot = _record(
        _Snapshot, _lookup(repository, "get_market_snapshot", market.snapshot_id)
    )
    if (snapshot.market_snapshot_id, snapshot.tenant_id, snapshot.decision_at) != (
        market.snapshot_id, tenant_id, decision_at
    ):
        raise ValueError("market snapshot does not match the request")

    seen: set[tuple[str, str]] = set()
    for pin in snapshot.pinned_vintages:
        key = (pin.vintage_id, pin.revision_id)
        if key in seen:
            raise ValueError("duplicate pinned market vintage")
        seen.add(key)
        vintage = _record(
            _Vintage, _lookup(repository, "get_market_vintage", *key)
        )
        if (vintage.vintage_id, vintage.revision_id) != key:
            raise ValueError("market vintage does not match its pin")
        if not vintage.available_at <= vintage.retrieved_at <= decision_at:
            raise ValueError("market vintage was not known at decision time")
        evidence = _record(
            _MarketG0Evidence,
            _lookup(repository, "get_market_g0_evidence", pin.g0_evidence_id),
        )
        if (evidence.evidence_id, evidence.tenant_id, evidence.vintage_id, evidence.revision_id) != (
            pin.g0_evidence_id, tenant_id, *key
        ):
            raise ValueError("market G0 evidence does not match its pin")
    return market


def validate_market_context_chain(
    *,
    scenario_context: MarketContext,
    economic_scenario_context: MarketContext,
    economic_result_context: MarketContext,
    assessment_context: MarketContext,
) -> MarketContext:
    """Require the same variant and ID on all four linked objects."""
    contexts = tuple(
        _validated_context(value)
        for value in (
            scenario_context,
            economic_scenario_context,
            economic_result_context,
            assessment_context,
        )
    )
    if any(value != contexts[0] for value in contexts[1:]):
        raise ValueError("linked market contexts differ")
    return contexts[0]


def validate_first_g1_use(
    market: MarketContext, *, economic_inputs: object, assessment_status: object
) -> MarketContext:
    """Check unavailable-market provenance and Assessment hold, not run admission.

    Economic callers must separately validate each full economic input, then pass
    its server-extracted provenance projection here. This helper neither authorizes
    nor validates raw economic values and must not be the sole admission control.
    """
    market = _validated_context(market)
    if not isinstance(market, UnavailableMarketContext):
        raise ValueError("first G1 unavailable policy requires a hold report")
    if assessment_status != "hold":
        raise ValueError("unavailable market context requires Assessment hold")
    if type(economic_inputs) not in (tuple, list) or not economic_inputs:
        raise ValueError("economic provenance projections must be a nonempty tuple/list")
    for item in economic_inputs:
        if type(item) is UserAssumptionProjection:
            item = vars(item)
        elif type(item) is not dict:
            raise ValueError("economic provenance projection is malformed")
        try:
            UserAssumptionProjection.model_validate(item)
        except ValueError as exc:
            raise ValueError("first G1 accepts only exact scoped user assumptions") from exc
    return market


def validate_forecast_market_context(
    market: MarketContext,
    *,
    tenant_id: str | None = None,
    decision_at: datetime | None = None,
    repository: object | None = None,
) -> MarketContext:
    """Admit only an available context verified again at the server boundary."""
    market = _validated_context(market)
    if not isinstance(market, AvailableMarketContext):
        raise ValueError("ForecastRun requires an available market context")
    if repository is None or tenant_id is None or decision_at is None:
        raise ValueError("ForecastRun requires server market verification")
    return resolve_market_context(
        market, tenant_id=tenant_id, decision_at=decision_at, repository=repository
    )
