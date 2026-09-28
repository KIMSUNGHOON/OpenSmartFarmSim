"""Immutable server registration facts shared by admission and initial research."""

from hashlib import sha256
from dataclasses import dataclass
from collections.abc import Mapping
from types import MappingProxyType

from .cli_contracts import AuthoritySnapshot, _canonical, _id, _json, _utc, parse_stage_input
from .orchestration import LocationRequest, ResearchScope


PREFIX = "research-registry-sha256:"
REGISTRATION_FIELDS = frozenset({"tenant_id", "point", "period_start_utc",
                                 "period_end_utc", "goal_id", "provider_ids"})
CONTEXT_FIELDS = ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")


def _scope_key(tenant, point, start, end, goal):
    return tenant, point[0], point[1], start, end, goal


@dataclass(frozen=True, init=False)
class ResearchRegistry:
    _sha256: str
    _scopes: Mapping

    def __init__(self, raw, expected_sha256):
        try:
            if (type(raw) is not bytes or not 0 < len(raw) <= 65536 or
                    type(expected_sha256) is not str or sha256(raw).hexdigest() != expected_sha256):
                raise ValueError()
            value = _json(raw)
            if (type(value) is not dict or set(value) != {"registry_version", "registrations"} or
                    value["registry_version"] != "research-registry-v1" or raw != _canonical(value) or
                    type(value["registrations"]) is not list or not 1 <= len(value["registrations"]) <= 64):
                raise ValueError()
            scopes = {}
            for item in value["registrations"]:
                if (type(item) is not dict or set(item) != REGISTRATION_FIELDS or not _id(item["tenant_id"]) or
                        type(item["point"]) is not dict or set(item["point"]) != {"latitude", "longitude"} or
                        type(item["provider_ids"]) is not list or not 1 <= len(item["provider_ids"]) <= 20 or
                        any(not _id(provider) or provider.startswith(PREFIX) for provider in item["provider_ids"]) or
                        len(set(item["provider_ids"])) != len(item["provider_ids"])):
                    raise ValueError()
                body = LocationRequest.model_validate({**item["point"],
                    **{name: item[name] for name in ("period_start_utc", "period_end_utc", "goal_id")},
                    "idempotency_key": "registry-validation"})
                if _utc(body.period_start_utc) >= _utc(body.period_end_utc):
                    raise ValueError()
                scope = ResearchScope(item["tenant_id"], (body.latitude, body.longitude),
                    body.period_start_utc, body.period_end_utc, body.goal_id, expected_sha256,
                    tuple(item["provider_ids"]))
                key = _scope_key(scope.tenant_id, scope.point, scope.period_start_utc,
                                 scope.period_end_utc, scope.goal_id)
                if key in scopes:
                    raise ValueError()
                scopes[key] = scope
        except (ValueError, TypeError, KeyError, UnicodeError, RecursionError, OverflowError):
            raise ValueError("research registry rejected") from None
        object.__setattr__(self, "_sha256", expected_sha256)
        object.__setattr__(self, "_scopes", MappingProxyType(scopes))

    @property
    def sha256(self):
        return self._sha256

    def scope_for_location(self, tenant, body):
        if type(body) is not LocationRequest or type(tenant) is not str:
            return None
        return self._scopes.get(_scope_key(tenant, (body.latitude, body.longitude),
            body.period_start_utc, body.period_end_utc, body.goal_id))

    def authority_snapshot(self, job, value):
        try:
            if job.get("stage") != "research":
                return None
            checked = parse_stage_input(job["input_bytes"], job)
            if (checked != value or checked["evidence_refs"] or
                    any(checked[name] is not None for name in CONTEXT_FIELDS)):
                return None
            body = LocationRequest.model_validate({**checked["point"],
                **{name: checked[name] for name in ("period_start_utc", "period_end_utc", "goal_id")},
                "idempotency_key": "registry-validation"})
            scope = self.scope_for_location(job["tenant_id"], body)
            if (scope is None or checked["provider_ids"] != list(scope.provider_ids) or
                    checked["candidate_ids"] != [*scope.provider_ids, PREFIX+self.sha256]):
                return None
            bindings = {"point": {"latitude": scope.point[0], "longitude": scope.point[1]},
                "period_start_utc": scope.period_start_utc, "period_end_utc": scope.period_end_utc,
                "goal_id": scope.goal_id, "provider_ids": list(scope.provider_ids)}
            return AuthoritySnapshot(tenant_id=scope.tenant_id, stage="research",
                input_sha256=job["input_sha256"], candidate_ids=frozenset(checked["candidate_ids"]),
                evidence={}, allow_proceed=False,
                missing_evidence=("research_source_evidence", "signed_decision_context"),
                approved_claims={}, g3a_candidate_ids=frozenset(), g3b_ok=False,
                stage_bindings=bindings, decision_context_id=None, decision_at_utc=None,
                claim_mode=None, decision_time_kind=None)
        except (ValueError, TypeError, KeyError, AttributeError):
            return None
