"""Metadata-only admission request for a joined calculation assessment."""

from pydantic import Field

from .owned_fixture_collection import UUID_PATTERN
from .provenance import FrozenContract
from .thermal_scenario_store import IDENTIFIER


class CalculationAssessmentRequest(FrozenContract):
    run_job_id: str = Field(pattern=UUID_PATTERN)
    economic_job_id: str = Field(pattern=UUID_PATTERN)
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)
