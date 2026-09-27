"""Adversarial G0 contract tests; the repository here is a fixture only."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.gates import (
    CheckEvidence, CheckRequirement, G0Policy, RequestAllowance, RightEvidence,
    SourceEvidence, VariableRequirement, evaluate_g0,
)
from app.provenance import ProjectCheck, RequestDetail, Right, SourceRecord, SourceScope, Variable

T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
T1 = T0 + timedelta(days=1)
T2 = T1 + timedelta(days=1)
T3 = T2 + timedelta(days=1)
RAW = b"fixture bytes only, no external rights proven"
SCOPE = SourceScope(provider="example-provider", product_id="hourly-observations", product_version="v1", source_url="https://example.org/product", station_or_grid_id="station-1")


def source(raw=RAW, **changes):
    data = dict(schema_version="1", scope=SCOPE, revision_id="revision-1",
        request_details=(RequestDetail(name="station", value="station-1"),),
        observed_at=T0, published_at=T0, available_at=T0, retrieved_at=T1,
        valid_from=T0, valid_to=T3 + timedelta(days=1),
        variables=(Variable(name="solar", original_unit="MJ/m2", time_semantics="interval_total", interval_start=T0, interval_end=T1, provider_qc_status="not_supplied", provider_qc_value=None),),
        project_checks=(ProjectCheck(variable="solar", name="physical-range", version="v1", status="passed", evidence_id="check-1", reviewer="reviewer-1"),),
        rights=(Right(action="display", status="allowed", evidence_id="right-1", reviewer="reviewer-1"),),
        raw_sha256=sha256(raw).hexdigest(), synthetic=False, synthetic_author=None,
        synthetic_method=None, source_reviewer="reviewer-1", source_evidence_id="source-1")
    data.update(changes)
    draft = SourceRecord.model_construct(record_id="placeholder", **data)
    return SourceRecord(record_id=draft.content_id(), **data)


def policy(**changes):
    data = dict(schema_version="1", policy_id="policy-1", policy_version="v1", scope=SCOPE,
        intended_action="display", intended_use="internal-preview",
        required_variables=(VariableRequirement(name="solar", original_unit="MJ/m2", time_semantics="interval_total"),),
        required_checks=(CheckRequirement(variable="solar", name="physical-range", version="v1"),),
        required_rights=("display",), required_times=("observed_at", "published_at", "available_at"),
        allowed_request_details=(RequestAllowance(name="station", values=("station-1",)),),
        reviewer="policy-reviewer", authenticated=True, approved=True,
        approved_at=T1, available_at=T1, valid_from=T1,
        valid_to=T3 + timedelta(days=1), revoked_at=None)
    data.update(changes)
    draft = G0Policy.model_construct(policy_digest="0" * 64, **data)
    return G0Policy(policy_digest=draft.content_digest(), **data)


def evidence(cls, record, **changes):
    data = dict(evidence_id="source-1" if cls is SourceEvidence else "check-1" if cls is CheckEvidence else "right-1",
        record_id=record.record_id, scope=record.scope, revision_id=record.revision_id,
        raw_sha256=record.raw_sha256, reviewer="reviewer-1", authenticated=True,
        approved=True, approved_at=T1, available_at=T1, valid_from=T1,
        valid_to=T3 + timedelta(days=1), revoked_at=None)
    if cls is CheckEvidence:
        data.update(variable="solar", check_name="physical-range", check_version="v1")
    if cls is RightEvidence:
        data.update(action="display", use="internal-preview", conditions_met=True)
    data.update(changes)
    return cls(**data)


class FixtureRepository:
    """Test fixture. No persistent or production trusted store exists in this slice."""
    def __init__(self, record=None, raw=RAW, approved_policy=None):
        self.record = record or source()
        self.raw = raw
        self.policy = approved_policy or policy()
        self.source_reviews = {"source-1": evidence(SourceEvidence, self.record)}
        self.checks = {"check-1": evidence(CheckEvidence, self.record)}
        self.rights = {"right-1": evidence(RightEvidence, self.record)}
        self.policy_lookup_at = None

    def get_record(self, record_id):
        return self.record if self.record.record_id == record_id else None

    def get_raw_bytes(self, record_id):
        return self.raw

    def get_approved_policy(self, scope, action, use, decision_at):
        self.policy_lookup_at = decision_at
        return self.policy

    def get_source_evidence(self, evidence_id):
        return self.source_reviews.get(evidence_id)

    def get_check_evidence(self, evidence_id):
        return self.checks.get(evidence_id)

    def get_right_evidence(self, evidence_id):
        return self.rights.get(evidence_id)


def decide(repo, *, record_id=None, action="display", use="internal-preview", at=T3):
    return evaluate_g0(record_id or repo.record.record_id, action, use, at, repo)


def codes(result):
    assert result.status == "hold"
    return {reason.code for reason in result.reasons}


def test_trusted_fixture_pass_is_narrowly_bound():
    repo = FixtureRepository()
    result = decide(repo)
    assert result.status == "pass" and result.reasons == ()
    assert result.record_id == repo.record.record_id
    assert result.raw_sha256 == repo.record.raw_sha256
    assert result.policy_id == repo.policy.policy_id
    assert result.policy_version == repo.policy.policy_version
    assert result.policy_digest == repo.policy.policy_digest
    assert result.required_checks == repo.policy.required_checks
    assert result.required_rights == repo.policy.required_rights
    assert repo.policy_lookup_at == T3
    assert result.decision_at == T3 and result.intended_action == "display"
    assert result.intended_use == "internal-preview" and result.variables == ("solar",)


def test_public_api_rejects_caller_authored_record_policy_and_raw():
    repo = FixtureRepository()
    with pytest.raises(TypeError):
        evaluate_g0(repo.record, repo.policy, RAW)
    with pytest.raises(TypeError):
        evaluate_g0(repo.record.record_id, "display", "internal-preview", T3, repo, raw_bytes=RAW)


def test_invalid_record_id_is_not_echoed_into_a_hold():
    result = evaluate_g0("Bearer-secret-value", "display", "internal-preview", T3, FixtureRepository())
    assert "record_missing" in codes(result)
    assert result.record_id == ""
    assert "Bearer-secret-value" not in result.model_dump_json()


def test_instant_value_requires_observation_time_even_if_policy_omits_it():
    instant = Variable(name="solar", original_unit="MJ/m2", time_semantics="instant",
                       provider_qc_status="not_supplied", provider_qc_value=None)
    record = source(observed_at=None, variables=(instant,))
    approved_policy = policy(
        required_variables=(VariableRequirement(name="solar", original_unit="MJ/m2",
                                                time_semantics="instant"),),
        required_times=("published_at", "available_at"),
    )
    assert "required_time_missing" in codes(decide(FixtureRepository(record, approved_policy=approved_policy)))


def test_invented_evidence_ids_and_false_synthetic_declaration_hold():
    made_up = source(project_checks=(ProjectCheck(variable="solar", name="physical-range", version="v1", status="passed", evidence_id="invented", reviewer="reviewer-1"),), rights=(Right(action="display", status="allowed", evidence_id="invented", reviewer="reviewer-1"),), synthetic=False)
    repo = FixtureRepository(made_up)
    assert {"check_evidence_missing", "right_evidence_missing"} <= codes(decide(repo))
    repo.source_reviews.clear()
    assert "source_review_missing" in codes(decide(repo))


def test_caller_cannot_replace_approved_policy_or_weaken_rights():
    repo = FixtureRepository()
    repo.policy = repo.policy.model_copy(update={"required_rights": ("access",)})
    assert "policy_invalid" in codes(decide(repo))
    repo.policy = policy(scope=SCOPE.model_copy(update={"product_id": "other"}))
    assert "scope_mismatch" in codes(decide(repo))


def test_same_id_cannot_represent_different_raw_or_manifest():
    repo = FixtureRepository()
    repo.raw = RAW + b"changed"
    assert "raw_hash_mismatch" in codes(decide(repo))
    repo = FixtureRepository()
    repo.record = repo.record.model_copy(update={"revision_id": "changed"})
    assert "record_id_mismatch" in codes(decide(repo))


def test_missing_repository_objects_and_lookup_fail_closed():
    repo = FixtureRepository()
    repo.policy = None
    assert "policy_missing" in codes(decide(repo))
    repo = FixtureRepository()
    repo.raw = None
    assert "raw_missing" in codes(decide(repo))
    repo = FixtureRepository()
    assert "record_missing" in codes(decide(repo, record_id="0" * 64))
    repo = FixtureRepository()
    repo.get_source_evidence = lambda evidence_id: 1 / 0
    assert "repository_error" in codes(decide(repo))


@pytest.mark.parametrize("change,expected", [
    ({"scope": SCOPE.model_copy(update={"station_or_grid_id": "other"})}, "source_evidence_mismatch"),
    ({"revision_id": "other"}, "source_evidence_mismatch"),
    ({"raw_sha256": "0" * 64}, "source_evidence_mismatch"),
    ({"reviewer": "other"}, "source_evidence_mismatch"),
    ({"authenticated": False}, "source_evidence_unapproved"),
    ({"approved": False}, "source_evidence_unapproved"),
    ({"revoked_at": T2}, "source_evidence_revoked"),
    ({"available_at": T3 + timedelta(seconds=1)}, "source_evidence_unavailable"),
    ({"valid_to": T2}, "source_evidence_expired"),
])
def test_source_attestation_must_match_and_be_current(change, expected):
    repo = FixtureRepository()
    repo.source_reviews["source-1"] = evidence(SourceEvidence, repo.record, **change)
    assert expected in codes(decide(repo))


@pytest.mark.parametrize("change,expected", [
    ({"scope": SCOPE.model_copy(update={"product_version": "v2"})}, "check_evidence_mismatch"),
    ({"raw_sha256": "0" * 64}, "check_evidence_mismatch"),
    ({"check_version": "v2"}, "check_evidence_mismatch"),
    ({"variable": "other"}, "check_evidence_mismatch"),
    ({"reviewer": "other"}, "check_evidence_mismatch"),
    ({"approved": False}, "check_evidence_unapproved"),
    ({"revoked_at": T2}, "check_evidence_revoked"),
    ({"available_at": T3 + timedelta(seconds=1)}, "check_evidence_unavailable"),
    ({"valid_to": T2}, "check_evidence_expired"),
])
def test_check_evidence_is_specific(change, expected):
    repo = FixtureRepository()
    repo.checks["check-1"] = evidence(CheckEvidence, repo.record, **change)
    assert expected in codes(decide(repo))


@pytest.mark.parametrize("change,expected", [
    ({"action": "redistribute"}, "right_evidence_mismatch"),
    ({"use": "public"}, "right_evidence_mismatch"),
    ({"revision_id": "other"}, "right_evidence_mismatch"),
    ({"reviewer": "other"}, "right_evidence_mismatch"),
    ({"conditions_met": False}, "right_conditions_unmet"),
    ({"authenticated": False}, "right_evidence_unapproved"),
    ({"revoked_at": T2}, "right_evidence_revoked"),
    ({"available_at": T3 + timedelta(seconds=1)}, "right_evidence_unavailable"),
    ({"valid_to": T2}, "right_evidence_expired"),
])
def test_right_evidence_is_action_and_use_specific(change, expected):
    repo = FixtureRepository()
    repo.rights["right-1"] = evidence(RightEvidence, repo.record, **change)
    assert expected in codes(decide(repo))


def test_missing_requested_right_and_other_actions_are_distinct():
    repo = FixtureRepository()
    repo.record = source(rights=())
    assert "right_missing" in codes(decide(repo))
    repo = FixtureRepository()
    assert "policy_missing" in codes(decide(repo, action="redistribute")) or "policy_invalid" in codes(decide(repo, action="redistribute"))


def test_bad_decision_time_and_temporal_source_hold():
    repo = FixtureRepository()
    assert "decision_time_invalid" in codes(decide(repo, at=datetime(2026, 1, 4)))
    assert "decision_time_invalid" in codes(decide(repo, at="tomorrow"))
    assert "record_unavailable" in codes(decide(repo, at=T0))
    late = source(available_at=T2, retrieved_at=T2)
    repo = FixtureRepository(late)
    assert "record_unavailable" in codes(decide(repo, at=T1))


def test_extra_variable_with_bad_qc_or_missing_check_fails_closed():
    extra = Variable(name="temperature", original_unit="C", time_semantics="instant", provider_qc_status="failed", provider_qc_value="bad")
    repo = FixtureRepository(source(variables=source().variables + (extra,)))
    assert "variable_unapproved" in codes(decide(repo))
    repo = FixtureRepository(source(variables=source().variables + (extra.model_copy(update={"provider_qc_status": "unknown"}),)))
    assert "variable_unapproved" in codes(decide(repo))
    repo = FixtureRepository(source(variables=source().variables + (extra.model_copy(update={"provider_qc_status": "passed"}),)))
    assert "variable_unapproved" in codes(decide(repo))


def test_check_version_and_status_are_required():
    repo = FixtureRepository(source(project_checks=(ProjectCheck(variable="solar", name="physical-range", version="v2", status="passed", evidence_id="check-1", reviewer="reviewer-1"),)))
    assert "check_missing" in codes(decide(repo))
    repo = FixtureRepository(source(project_checks=(ProjectCheck(variable="solar", name="physical-range", version="v1", status="failed", evidence_id="check-1", reviewer="reviewer-1"),)))
    assert "check_failed" in codes(decide(repo))


@pytest.mark.parametrize("status", ["passed", "failed", "unknown"])
def test_extra_project_check_is_not_silently_included_in_record_pass(status):
    base = source()
    extra = ProjectCheck(variable="solar", name="night-range", version="v1",
        status=status, evidence_id="extra-check", reviewer="reviewer-1")
    repo = FixtureRepository(source(project_checks=base.project_checks + (extra,)))
    assert "check_unapproved" in codes(decide(repo))


@pytest.mark.parametrize("status", ["allowed", "denied", "unknown"])
def test_extra_right_is_outside_approved_action_scope(status):
    base = source()
    extra = Right(action="redistribute", status=status, evidence_id=None, reviewer=None)
    repo = FixtureRepository(source(rights=base.rights + (extra,)))
    result = decide(repo)
    assert result.status == "pass"
    assert result.required_rights == ("display",)
    assert "redistribute" not in result.required_rights
    assert "policy_invalid" in codes(decide(repo, action="redistribute"))


@pytest.mark.parametrize("change,expected", [
    ({"authenticated": False}, "policy_unapproved"),
    ({"approved": False}, "policy_unapproved"),
    ({"approved_at": T3 + timedelta(seconds=1)}, "policy_unavailable"),
    ({"available_at": T3 + timedelta(seconds=1)}, "policy_unavailable"),
    ({"valid_from": T3 + timedelta(seconds=1)}, "policy_expired"),
    ({"valid_to": T3}, "policy_expired"),
    ({"revoked_at": T2}, "policy_revoked"),
])
def test_policy_approval_must_be_valid_as_of_decision(change, expected):
    repo = FixtureRepository(approved_policy=policy(**change))
    assert expected in codes(decide(repo))


def test_policy_revocation_after_decision_does_not_rewrite_history():
    repo = FixtureRepository(approved_policy=policy(revoked_at=T3 + timedelta(seconds=1)))
    assert decide(repo).status == "pass"


def test_policy_approval_times_require_utc():
    for name in ("approved_at", "available_at", "valid_from", "valid_to", "revoked_at"):
        with pytest.raises(ValidationError):
            policy(**{name: datetime(2026, 1, 2)})


def test_request_allowlist_controls_names_and_values():
    repo = FixtureRepository(source(request_details=(RequestDetail(name="page", value="1"),)))
    assert "request_not_allowed" in codes(decide(repo))
    repo = FixtureRepository(source(request_details=(RequestDetail(name="station", value="station-2"),)))
    assert "request_not_allowed" in codes(decide(repo))


def test_policy_allowlist_itself_cannot_contain_secret_metadata():
    with pytest.raises(ValidationError):
        RequestAllowance(name="apiKey", values=("credential",))
    with pytest.raises(ValidationError):
        RequestAllowance(name="station", values=("Bearer credential",))


def test_policy_digest_cannot_be_changed_without_new_digest():
    repo = FixtureRepository()
    repo.policy = repo.policy.model_copy(update={"required_rights": ("display", "store")})
    assert "policy_digest_mismatch" in codes(decide(repo))
    repo.policy = policy().model_copy(update={"approved_at": T2})
    assert "policy_digest_mismatch" in codes(decide(repo))


@pytest.mark.parametrize("kind", ["source", "check", "right"])
def test_repository_evidence_id_must_match_requested_id(kind):
    repo = FixtureRepository()
    if kind == "source":
        repo.source_reviews["source-1"] = repo.source_reviews["source-1"].model_copy(update={"evidence_id": "other"})
        expected = "source_evidence_mismatch"
    elif kind == "check":
        repo.checks["check-1"] = repo.checks["check-1"].model_copy(update={"evidence_id": "other"})
        expected = "check_evidence_mismatch"
    else:
        repo.rights["right-1"] = repo.rights["right-1"].model_copy(update={"evidence_id": "other"})
        expected = "right_evidence_mismatch"
    assert expected in codes(decide(repo))


def test_invalid_repository_models_hold_without_raising():
    repo = FixtureRepository()
    repo.source_reviews["source-1"] = repo.source_reviews["source-1"].model_copy(update={"valid_to": None})
    assert "source_evidence_mismatch" in codes(decide(repo))
    repo = FixtureRepository()
    repo.policy = repo.policy.model_copy(update={"required_variables": "bad"})
    assert "policy_invalid" in codes(decide(repo))
    repo = FixtureRepository()
    repo.record = repo.record.model_copy(update={"variables": "bad"})
    assert "record_invalid" in codes(decide(repo))
