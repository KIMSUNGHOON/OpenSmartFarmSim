"""Public fields for the first durable-job HTTP read path."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from .jobs import require_reason_code


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
