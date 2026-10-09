"""Trusted region-to-research admission; no source approval or model execution."""

from dataclasses import dataclass
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field

from .cli_contracts import _canonical, _id, _utc, parse_stage_input
from .job_store import JobStore
from .runtime_roles import RuntimeLoginPolicy, audit_runtime_roles


IDENTIFIER = r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$"
UTC_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"


class LocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, allow_inf_nan=False)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    period_start_utc: str = Field(pattern=UTC_PATTERN, max_length=27, json_schema_extra={"format": "date-time"})
    period_end_utc: str = Field(pattern=UTC_PATTERN, max_length=27, json_schema_extra={"format": "date-time"})
    goal_id: str = Field(pattern=IDENTIFIER, max_length=200)
    idempotency_key: str = Field(pattern=IDENTIFIER, max_length=200)


@dataclass(frozen=True)
class ResearchScope:
    tenant_id: str
    point: tuple[float, float]
    period_start_utc: str
    period_end_utc: str
    goal_id: str
    registry_sha256: str
    provider_ids: tuple[str, ...]


class ResearchRequestRejected(ValueError):
    pass


class LocationResearchService:
    def __init__(self, store, scope_resolver):
        binding = getattr(store, "runtime_identity", None)
        if (type(store) is not JobStore or type(binding) is not tuple or len(binding) != 2 or
                type(binding[0]) is not RuntimeLoginPolicy or binding[1] != "authority" or
                not callable(scope_resolver)):
            raise ValueError("authenticated research authority and read-only scope resolver required")
        self.store, self.scope_resolver = store, scope_resolver

    def submit(self, tenant, body):
        if type(body) is not LocationRequest or not self.store._has_scope(tenant, "location_create"):
            raise PermissionError("location registration denied")
        try:
            if _utc(body.period_start_utc) >= _utc(body.period_end_utc):
                raise ValueError("empty period")
        except ValueError:
            raise ResearchRequestRejected("invalid research period") from None
        with self.store.connect() as conn:
            audit_runtime_roles(conn, self.store.runtime_identity[0])
        scope = self.scope_resolver(tenant, body)
        if scope is None:
            raise ResearchRequestRejected("unsupported research scope")
        if (type(scope) is not ResearchScope or scope.tenant_id != tenant or
                type(scope.point) is not tuple or len(scope.point) != 2 or
                any(type(item) not in (int, float) for item in scope.point) or
                scope.point != (body.latitude, body.longitude) or scope.period_start_utc != body.period_start_utc or
                scope.period_end_utc != body.period_end_utc or scope.goal_id != body.goal_id or
                type(scope.registry_sha256) is not str or len(scope.registry_sha256) != 64 or
                any(char not in "0123456789abcdef" for char in scope.registry_sha256) or
                type(scope.provider_ids) is not tuple or not 1 <= len(scope.provider_ids) <= 20 or
                any(not _id(item) for item in scope.provider_ids) or len(set(scope.provider_ids)) != len(scope.provider_ids)):
            raise RuntimeError("research scope authority unavailable")
        point = {"latitude": body.latitude, "longitude": body.longitude}
        value = dict(input_version="research_input_v1", tenant_id=tenant,
            candidate_ids=[*scope.provider_ids, "research-registry-sha256:"+scope.registry_sha256],
            provider_ids=list(scope.provider_ids), evidence_refs=[], point=point,
            period_start_utc=body.period_start_utc, period_end_utc=body.period_end_utc, goal_id=body.goal_id,
            decision_context_id=None, decision_at_utc=None, claim_mode=None, decision_time_kind=None)
        raw = _canonical(value)
        parse_stage_input(raw, {"tenant_id": tenant, "stage": "research", "input_sha256": sha256(raw).hexdigest()})
        job = self.store.submit(tenant, "research", value, body.idempotency_key)
        location = "location-v1-"+sha256(_canonical({"tenant_id": tenant, "point": point})).hexdigest()
        return location, point, job
