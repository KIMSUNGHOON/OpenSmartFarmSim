"""Public fields for versioned, tenant-scoped HTTP read paths."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .jobs import require_reason_code
from .job_store import JobStore


class JobStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    job_id: UUID
    stage: Literal["research", "collection", "collection_review", "simulation", "assessment"]
    state: Literal["queued", "researching", "collecting", "reviewing", "simulating",
                   "assessing", "succeeded", "hold", "failed", "canceled"]
    attempt_count: int = Field(ge=0)
    max_attempts: int = Field(ge=1, le=3)
    created_at: datetime
    updated_at: datetime
    reason_code: str | None


class MarketHoldStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    hold_report_id: UUID
    status: Literal["hold"]
    reasons: list[str]
    missing_evidence: list[str]


PublicMissingEvidence = Literal["research_source_evidence", "signed_decision_context",
    "real_source_g0", "market_source_g0", "eligible_crop_candidates", "farm_scenario_binding",
    "local_measurements_g2", "future_validation_g3a", "paired_comparison_g3b", "other_evidence"]
PUBLIC_MISSING_EVIDENCE = frozenset({"research_source_evidence", "signed_decision_context", "real_source_g0",
    "market_source_g0", "eligible_crop_candidates", "farm_scenario_binding",
    "local_measurements_g2", "future_validation_g3a", "paired_comparison_g3b"})


class JobHoldStatus(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    job_id: UUID
    stage: Literal["research", "collection_review", "assessment"]
    hold_id: UUID
    status: Literal["hold"]
    recorded_at: datetime
    reason_code: Literal["evidence_missing", "decision_held"]
    missing_evidence: list[PublicMissingEvidence]
    missing_evidence_count: int = Field(ge=0, le=50)


class LocationPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class LocationAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    location_id: str = Field(pattern=r"^location-v1-[0-9a-f]{64}$")
    point: LocationPoint
    spatial_support: Literal["pending_research"]
    research_job: JobStatus


class ThermalRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    status: Literal["accepted"]
    synthetic: Literal[True]
    temporal_provenance: Literal["ex_post_replay"]
    decision_at_utc: datetime
    review_at_utc: datetime
    start_utc: datetime
    end_utc: datetime
    model_version: Literal["thermal-v1"]
    parameter_set_version: Literal["synthetic-thermal-parameters-v1"]
    engine_version: Literal["thermal-euler-v1"]
    unit_registry_version: Literal["thermal-si-nws-v1"]
    manifest_sha256: str
    trace_sha256: list[str]
    point_count: int = Field(ge=1)


class ThermalSeriesPoint(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    at_utc: datetime
    temperature_k: float
    humidity_ratio_kg_v_per_kg_da: float
    relative_humidity_fraction: float
    heat_demand_w_th: float
    heat_delivered_w_th: float
    delivered_heat_energy_kwh_th: float


class ThermalRunSeries(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    temporal_provenance: Literal["ex_post_replay"]
    points: list[ThermalSeriesPoint]


class AuthoredThermalRunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str = Field(pattern=r'^authored-thermal-run-v1:[0-9a-f]{64}$')
    status: Literal['accepted']
    synthetic: Literal[True]
    claim_scope: Literal['synthetic_thermal_replay_only']
    temporal_provenance: Literal['ex_post_replay']
    scenario_id: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$', max_length=200)
    scenario_revision: str = Field(pattern=r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$', max_length=200)
    registration_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    release_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    decision_at_utc: datetime
    review_at_utc: datetime
    start_utc: datetime
    end_utc: datetime
    model_version: Literal['thermal-v1']
    engine_version: Literal['thermal-euler-v1']
    unit_registry_version: Literal['thermal-si-nws-v1']
    trace_sha256: list[str] = Field(min_length=2, max_length=2)
    point_count: Literal[120]


class ThermalManifestSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fixture_id: str
    product_id: str
    source_locator: str
    raw_sha256: str
    vintage_id: str
    revision_id: str
    available_at_utc: datetime
    retrieved_at_utc: datetime
    observed_start_utc: datetime | None
    observed_end_utc: datetime | None
    qc_status: Literal["self_checked_synthetic"]
    review_status: Literal["self_reviewed_synthetic"]
    display_right: Literal["allowed"]
    synthetic: Literal[True]


class ThermalLawReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    product_id: str
    source_url: str
    raw_pdf_sha256: str
    published_at_utc: datetime | None
    available_at_utc: datetime | None
    retrieved_at_utc: datetime
    publication_time_status: str
    version_status: str
    rights_status: str
    display_right: Literal["allowed_with_conditions"]
    display_conditions: str


class ThermalRunManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    synthetic: Literal[True]
    temporal_provenance: Literal["ex_post_replay"]
    snapshot_id: str
    manifest_sha256: str
    code_sha256: str
    environment_sha256: str
    release_sha256: str
    trace_sha256: list[str]
    source_unresolved_at_creation: list[str]
    used_sources: list[ThermalManifestSource]
    excluded_fixture_ids: list[str]
    law_reference: ThermalLawReference


class EconomicQuantities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    harvest_kg: str
    packout_kg: str
    recognized_kg: str
    net_sold_kg: str | None


class EconomicAmounts(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gross_sales_krw: str
    revenue_krw: str | None
    variable_cost_krw: str | None
    fixed_cost_krw: str | None
    depreciation_krw: str | None
    management_operating_income_krw: str | None
    operating_cash_krw: str | None
    business_cash_krw: str | None
    equity_cash_krw: str | None
    minimum_cash_balance_krw: str | None
    cash_shortage_krw: str | None


class EconomicResultRead(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    economic_result_id: str
    market_scenario_result_id: str
    scenario_id: str
    scenario_revision: str
    decision_at_utc: datetime
    formula_version: str
    market_context_kind: Literal["unavailable"]
    market_hold_report_id: UUID
    calculation_status: Literal["conditional_user_assumption", "hold"]
    assessment_status: Literal["hold"]
    sales_totals_status: Literal["inventory_reconciled", "unverified_input_arithmetic"]
    input_origin: Literal["user"]
    evidence_level: Literal["assumed"]
    quantities: EconomicQuantities
    amounts: EconomicAmounts
    hold_reason_codes: list[str]


class ErrorDetail(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str
    message: str


class ErrorEnvelope(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    error: ErrorDetail


def public_job_status(row: dict) -> JobStatus:
    """Select an explicit allowlist; never serialize a JobStore row directly."""
    reason = row.get("reason")
    if reason is not None and type(reason) is not dict:
        raise ValueError("job reason is not safe for public status")
    reason_code = require_reason_code(reason["code"]) if reason is not None else None
    return JobStatus.model_validate({
        "job_id": row["job_id"], "stage": row["stage"], "state": row["state"],
        "attempt_count": row["attempt_count"], "max_attempts": row["max_attempts"],
        "created_at": row["created_at"], "updated_at": row["updated_at"],
        "reason_code": reason_code,
    })


def public_market_hold(row: dict) -> MarketHoldStatus:
    """The display projection cannot carry signed context or raw report bytes."""
    return MarketHoldStatus.model_validate({
        "hold_report_id": row["hold_report_id"], "status": row["status"],
        "reasons": row["reasons"], "missing_evidence": row["missing_evidence"],
    })


def public_job_hold(job, held, raw) -> JobHoldStatus:
    if (job["state"] != "hold" or job["reason"] != {"code": "ai_validated_hold"} or
            held["tenant_id"] != job["tenant_id"] or held["job_id"] != job["job_id"] or
            held["attempt"] != job["attempt_count"]):
        raise ValueError("inconsistent held job")
    report = JobStore._parse_hold_report(raw)
    categories = []
    for code in report["missing_evidence"]:
        category = code if code in PUBLIC_MISSING_EVIDENCE else "other_evidence"
        if category not in categories:
            categories.append(category)
    return JobHoldStatus.model_validate({
        "job_id": job["job_id"], "stage": job["stage"], "hold_id": held["hold_id"],
        "status": "hold", "recorded_at": held["recorded_at"],
        "reason_code": report["reason_code"], "missing_evidence": categories,
        "missing_evidence_count": len(report["missing_evidence"]),
    })
