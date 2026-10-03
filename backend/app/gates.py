"""G0 admission using only server-resolved records, policies, and approvals."""

from datetime import datetime, timedelta
from hashlib import sha256
import json
from typing import Literal, Protocol, Self

from pydantic import Field, field_validator, model_validator

from app.provenance import Digest, FrozenContract, Name, RequestDetail, RightAction, SourceRecord, SourceScope, verify_raw_hash

RequiredTime = Literal["observed_at", "published_at", "available_at", "valid_from", "valid_to"]


class VariableRequirement(FrozenContract):
    name: Name
    original_unit: Name
    time_semantics: Literal["instant", "mean", "interval_total"]


class CheckRequirement(FrozenContract):
    variable: Name
    name: Name
    version: Name


class RequestAllowance(FrozenContract):
    name: Name
    values: tuple[str, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def unique_values(self) -> Self:
        if len(self.values) != len(set(self.values)):
            raise ValueError("duplicate allowed request value")
        for value in self.values:
            RequestDetail(name=self.name, value=value)
        return self


class G0Policy(FrozenContract):
    schema_version: Literal["1"]
    policy_id: Name
    policy_version: Name
    policy_digest: Digest
    scope: SourceScope
    intended_action: RightAction
    intended_use: Name
    required_variables: tuple[VariableRequirement, ...] = Field(min_length=1)
    required_checks: tuple[CheckRequirement, ...] = Field(min_length=1)
    required_rights: tuple[RightAction, ...] = Field(min_length=1)
    required_times: tuple[RequiredTime, ...] = Field(min_length=1)
    allowed_request_details: tuple[RequestAllowance, ...]
    reviewer: Name
    authenticated: bool
    approved: bool
    approved_at: datetime
    available_at: datetime
    valid_from: datetime
    valid_to: datetime
    revoked_at: datetime | None

    @field_validator("approved_at", "available_at", "valid_from", "valid_to", "revoked_at")
    @classmethod
    def utc_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() != timedelta(0):
            raise ValueError("policy time must be UTC-aware")
        return value

    @model_validator(mode="after")
    def complete_requirements(self) -> Self:
        if self.valid_from >= self.valid_to:
            raise ValueError("policy validity end must follow start")
        names = [item.name for item in self.required_variables]
        checks = [(item.variable, item.name, item.version) for item in self.required_checks]
        for items in (names, checks, self.required_rights, self.required_times, [x.name for x in self.allowed_request_details]):
            if len(items) != len(set(items)):
                raise ValueError("duplicate G0 requirement")
        if set(names) != {item.variable for item in self.required_checks}:
            raise ValueError("every required variable needs a named project check")
        if self.intended_action not in self.required_rights:
            raise ValueError("intended action must be a required right")
        if self.policy_digest != self.content_digest():
            raise ValueError("policy digest must bind approved requirements")
        return self

    def content_digest(self) -> str:
        metadata = self.model_dump(mode="json", exclude={"policy_digest"})
        canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(canonical.encode("utf-8")).hexdigest()


class ReviewedEvidence(FrozenContract):
    evidence_id: Name
    record_id: Name
    scope: SourceScope
    revision_id: Name
    raw_sha256: Digest
    reviewer: Name
    authenticated: bool
    approved: bool
    approved_at: datetime
    available_at: datetime
    valid_from: datetime
    valid_to: datetime
    revoked_at: datetime | None

    @field_validator("approved_at", "available_at", "valid_from", "valid_to", "revoked_at")
    @classmethod
    def utc_time(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() != timedelta(0):
            raise ValueError("evidence time must be UTC-aware")
        return value

    @model_validator(mode="after")
    def coherent_times(self) -> Self:
        if self.valid_from >= self.valid_to:
            raise ValueError("evidence validity end must follow start")
        return self


class SourceEvidence(ReviewedEvidence):
    pass


class CheckEvidence(ReviewedEvidence):
    variable: Name
    check_name: Name
    check_version: Name


class RightEvidence(ReviewedEvidence):
    action: RightAction
    use: Name
    conditions_met: bool


class G0Repository(Protocol):
    """Injected server store. Resolve authenticated approvals as of decision_at and publish atomically."""
    def get_record(self, record_id: str) -> SourceRecord | None: ...
    def get_raw_bytes(self, record_id: str) -> bytes | None: ...
    def get_approved_policy(self, scope: SourceScope, action: RightAction, use: str, decision_at: datetime) -> G0Policy | None: ...
    def get_source_evidence(self, evidence_id: str) -> SourceEvidence | None: ...
    def get_check_evidence(self, evidence_id: str) -> CheckEvidence | None: ...
    def get_right_evidence(self, evidence_id: str) -> RightEvidence | None: ...


class HoldReason(FrozenContract):
    code: Literal[
        "record_missing", "record_invalid", "record_id_mismatch", "raw_missing", "raw_hash_mismatch",
        "repository_error", "decision_time_invalid", "action_invalid", "use_invalid",
        "policy_missing", "policy_invalid", "policy_digest_mismatch", "policy_unapproved",
        "policy_unavailable", "policy_expired", "policy_revoked", "scope_mismatch",
        "synthetic_source", "source_review_missing", "record_unavailable", "required_time_missing",
        "variable_missing", "variable_unapproved", "unit_mismatch", "time_semantics_mismatch",
        "interval_missing", "provider_qc", "check_missing", "check_failed", "check_unapproved", "check_evidence_missing",
        "right_missing", "right_not_allowed", "right_evidence_missing", "request_not_allowed",
        "source_evidence_mismatch", "check_evidence_mismatch", "right_evidence_mismatch",
        "source_evidence_unapproved", "check_evidence_unapproved", "right_evidence_unapproved",
        "source_evidence_revoked", "check_evidence_revoked", "right_evidence_revoked",
        "source_evidence_unavailable", "check_evidence_unavailable", "right_evidence_unavailable",
        "source_evidence_expired", "check_evidence_expired", "right_evidence_expired", "right_conditions_unmet",
    ]
    subject: str


class G0Result(FrozenContract):
    gate_version: Literal["g0-v2"] = "g0-v2"
    record_id: str
    raw_sha256: Digest | None
    policy_id: Name | None
    policy_version: Name | None
    policy_digest: Digest | None
    decision_at: datetime | None
    intended_action: RightAction | None
    intended_use: str
    variables: tuple[Name, ...]
    required_checks: tuple[CheckRequirement, ...]
    required_rights: tuple[RightAction, ...]
    evidence_ids: tuple[Name, ...]
    status: Literal["pass", "hold"]
    reasons: tuple[HoldReason, ...]


def evaluate_g0(record_id: str, intended_action: RightAction, intended_use: str,
                decision_at: datetime, repository: G0Repository) -> G0Result:
    """Evaluate a server-owned snapshot. Production needs a durable authenticated store."""
    reasons: list[HoldReason] = []
    evidence_ids: list[str] = []
    record: SourceRecord | None = None
    policy: G0Policy | None = None
    variables: tuple[str, ...] = ()

    def hold(code: str, subject: str) -> None:
        reasons.append(HoldReason(code=code, subject=subject))

    def lookup(method: str, arg: object, missing_code: str, subject: str):
        try:
            value = getattr(repository, method)(arg)
        except Exception:
            hold("repository_error", method)
            return None
        if value is None:
            hold(missing_code, subject)
        return value

    def verified_proof(value, expected_type, expected_id: str, code: str, subject: str):
        if value is None:
            return None
        if not isinstance(value, expected_type):
            hold(code, subject)
            return None
        try:
            proof = expected_type.model_validate(value.model_dump(warnings="error"))
        except Exception:
            hold(code, subject)
            return None
        if proof.evidence_id != expected_id:
            hold(code, subject)
        return proof

    valid_time = isinstance(decision_at, datetime) and decision_at.utcoffset() == timedelta(0)
    if not valid_time:
        hold("decision_time_invalid", "decision_at")
    actions = ("access", "store", "transform", "display", "redistribute")
    if intended_action not in actions:
        hold("action_invalid", "intended_action")
    if not isinstance(intended_use, str) or not intended_use or intended_use != intended_use.strip():
        hold("use_invalid", "intended_use")
    valid_record_id = (isinstance(record_id, str) and len(record_id) == 64 and
                       all(c in "0123456789abcdef" for c in record_id))
    if not valid_record_id:
        hold("record_missing", "record_id")
    if reasons:
        return G0Result(record_id=record_id if valid_record_id else "", raw_sha256=None, policy_id=None, policy_version=None,
            policy_digest=None, decision_at=decision_at if valid_time else None,
            intended_action=intended_action if intended_action in actions else None,
            intended_use=intended_use if isinstance(intended_use, str) and intended_use == intended_use.strip() else "",
            variables=(), required_checks=(), required_rights=(),
            evidence_ids=(), status="hold", reasons=tuple(reasons))

    record = lookup("get_record", record_id, "record_missing", record_id)
    if not isinstance(record, SourceRecord):
        if record is not None:
            hold("record_invalid", record_id)
        record = None
    if record is not None:
        try:
            record_data = record.model_dump(warnings="error")
            if record.record_id != record_id or record.content_id() != record_id:
                hold("record_id_mismatch", record_id)
            record = SourceRecord.model_validate(record_data)
        except Exception:
            if not any(reason.code == "record_id_mismatch" for reason in reasons):
                hold("record_invalid", record_id)
            record = None
    if record is not None:
        raw = lookup("get_raw_bytes", record_id, "raw_missing", record_id)
        if raw is not None and (not isinstance(raw, bytes) or not verify_raw_hash(record, raw)):
            hold("raw_hash_mismatch", record_id)
        if record.synthetic:
            hold("synthetic_source", record_id)
        if record.available_at is None or record.available_at > decision_at or record.retrieved_at > decision_at:
            hold("record_unavailable", record_id)
        if record.valid_from is not None and not (record.valid_from <= decision_at < record.valid_to):
            hold("record_unavailable", record_id)
        try:
            policy = repository.get_approved_policy(record.scope, intended_action, intended_use, decision_at)
        except Exception:
            hold("repository_error", "get_approved_policy")
        if policy is None:
            hold("policy_missing", record_id)
        elif not isinstance(policy, G0Policy):
            hold("policy_invalid", record_id)
            policy = None
        else:
            try:
                policy_data = policy.model_dump(warnings="error")
                if policy.policy_digest != policy.content_digest():
                    hold("policy_digest_mismatch", policy.policy_id)
                policy = G0Policy.model_validate(policy_data)
            except Exception:
                hold("policy_invalid", record_id)
                policy = None
            if policy is not None:
                if policy.scope != record.scope:
                    hold("scope_mismatch", record_id)
                if policy.intended_action != intended_action or policy.intended_use != intended_use or intended_action not in policy.required_rights:
                    hold("policy_invalid", policy.policy_id)
                if not policy.authenticated or not policy.approved:
                    hold("policy_unapproved", policy.policy_id)
                if policy.approved_at > decision_at or policy.available_at > decision_at:
                    hold("policy_unavailable", policy.policy_id)
                if not (policy.valid_from <= decision_at < policy.valid_to):
                    hold("policy_expired", policy.policy_id)
                if policy.revoked_at is not None and policy.revoked_at <= decision_at:
                    hold("policy_revoked", policy.policy_id)

    if record is not None and policy is not None:
        for name in policy.required_times:
            if getattr(record, name) is None:
                hold("required_time_missing", name)
        if ("observed_at" not in policy.required_times and record.observed_at is None and
                any(item.time_semantics == "instant" for item in record.variables)):
            hold("required_time_missing", "observed_at")
        allowed = {item.name: set(item.values) for item in policy.allowed_request_details}
        for detail in record.request_details:
            if detail.name not in allowed or detail.value not in allowed[detail.name]:
                hold("request_not_allowed", detail.name)
        required = {item.name: item for item in policy.required_variables}
        actual = {item.name: item for item in record.variables}
        variables = tuple(sorted(required))
        for name in actual.keys() - required.keys():
            hold("variable_unapproved", name)
        for name, requirement in required.items():
            item = actual.get(name)
            if item is None:
                hold("variable_missing", name)
                continue
            if item.original_unit != requirement.original_unit:
                hold("unit_mismatch", name)
            if item.time_semantics != requirement.time_semantics:
                hold("time_semantics_mismatch", name)
            if item.time_semantics in ("mean", "interval_total") and item.interval_start is None:
                hold("interval_missing", name)
            if item.provider_qc_status in ("failed", "unknown"):
                hold("provider_qc", name)
        checks = {(item.variable, item.name, item.version): item for item in record.project_checks}
        required_checks = {(item.variable, item.name, item.version) for item in policy.required_checks}
        for key in sorted(checks.keys() - required_checks):
            hold("check_unapproved", ":".join(key))
        for requirement in policy.required_checks:
            subject = f"{requirement.variable}:{requirement.name}:{requirement.version}"
            item = checks.get((requirement.variable, requirement.name, requirement.version))
            if item is None:
                hold("check_missing", subject)
            elif item.status != "passed":
                hold("check_failed", subject)
            elif item.evidence_id is None or item.reviewer is None:
                hold("check_evidence_missing", subject)
            else:
                proof = verified_proof(lookup("get_check_evidence", item.evidence_id, "check_evidence_missing", subject), CheckEvidence, item.evidence_id, "check_evidence_mismatch", subject)
                if proof is not None:
                    evidence_ids.append(proof.evidence_id)
                    _check_proof(proof, record, item.reviewer, decision_at, "check_evidence", hold)
                    if (proof.variable, proof.check_name, proof.check_version) != (requirement.variable, requirement.name, requirement.version):
                        hold("check_evidence_mismatch", subject)
        rights = {item.action: item for item in record.rights}
        for action in policy.required_rights:
            item = rights.get(action)
            if item is None:
                hold("right_missing", action)
            elif item.status != "allowed":
                hold("right_not_allowed", action)
            elif item.evidence_id is None or item.reviewer is None:
                hold("right_evidence_missing", action)
            else:
                proof = verified_proof(lookup("get_right_evidence", item.evidence_id, "right_evidence_missing", action), RightEvidence, item.evidence_id, "right_evidence_mismatch", action)
                if proof is not None:
                    evidence_ids.append(proof.evidence_id)
                    _check_proof(proof, record, item.reviewer, decision_at, "right_evidence", hold)
                    if proof.action != action or proof.use != intended_use:
                        hold("right_evidence_mismatch", action)
                    if not proof.conditions_met:
                        hold("right_conditions_unmet", action)
        if record.source_reviewer is None or record.source_evidence_id is None:
            hold("source_review_missing", record_id)
        else:
            proof = verified_proof(lookup("get_source_evidence", record.source_evidence_id, "source_review_missing", record_id), SourceEvidence, record.source_evidence_id, "source_evidence_mismatch", record_id)
            if proof is not None:
                evidence_ids.append(proof.evidence_id)
                _check_proof(proof, record, record.source_reviewer, decision_at, "source_evidence", hold)

    return G0Result(record_id=record_id, raw_sha256=record.raw_sha256 if record else None,
        policy_id=policy.policy_id if policy else None, policy_version=policy.policy_version if policy else None,
        policy_digest=policy.policy_digest if policy else None, decision_at=decision_at,
        intended_action=intended_action, intended_use=intended_use, variables=variables,
        required_checks=policy.required_checks if policy else (),
        required_rights=policy.required_rights if policy else (),
        evidence_ids=tuple(evidence_ids), status="hold" if reasons else "pass", reasons=tuple(reasons))


def _check_proof(proof: ReviewedEvidence, record: SourceRecord, reviewer: str,
                 at: datetime, prefix: str, hold) -> None:
    if (proof.record_id != record.record_id or proof.scope != record.scope or
            proof.revision_id != record.revision_id or proof.raw_sha256 != record.raw_sha256 or
            proof.reviewer != reviewer):
        hold(f"{prefix}_mismatch", proof.evidence_id)
    if not proof.authenticated or not proof.approved:
        hold(f"{prefix}_unapproved", proof.evidence_id)
    if proof.revoked_at is not None and proof.revoked_at <= at:
        hold(f"{prefix}_revoked", proof.evidence_id)
    if proof.available_at > at or proof.approved_at > at:
        hold(f"{prefix}_unavailable", proof.evidence_id)
    if not (proof.valid_from <= at < proof.valid_to):
        hold(f"{prefix}_expired", proof.evidence_id)
