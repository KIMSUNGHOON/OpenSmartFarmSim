"""Closed request for a released authored thermal simulation intent."""

from typing import Literal

from pydantic import Field

from .farm_inputs import Identifier
from .owned_fixture_collection import UUID_PATTERN
from .provenance import Digest, FrozenContract


class AuthoredSimulationRequest(FrozenContract):
    schema_version: Literal['authored-thermal-simulation-request-v1']
    review_job_id: str = Field(pattern=UUID_PATTERN)
    scenario_id: Identifier
    scenario_revision: Identifier
    registration_sha256: Digest
    idempotency_key: Identifier
