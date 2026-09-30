"""Closed authenticated request for registered farm input review admission."""

from typing import Literal

from .farm_inputs import Identifier
from .provenance import Digest, FrozenContract


class FarmAuthoredReviewRequest(FrozenContract):
    schema_version: Literal['farm-authored-review-request-v1']
    scenario_id: Identifier
    scenario_revision: Identifier
    registration_sha256: Digest
    idempotency_key: Identifier
