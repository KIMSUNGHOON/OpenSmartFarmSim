"""Closed metadata requests for existing owned ingestion and review admission."""

from pydantic import Field

from .owned_fixture_collection import UUID_PATTERN
from .provenance import FrozenContract
from .thermal_scenario_store import IDENTIFIER


class OwnedIngestionRequest(FrozenContract):
    research_job_id: str = Field(pattern=UUID_PATTERN)
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


class OwnedReviewRequest(FrozenContract):
    collection_job_id: str = Field(pattern=UUID_PATTERN)
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)
