"""Authorization, scope, time, and revocation checks for G0 approvals."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from test_g0_store import RAW, SCOPE, approved, env, fake_review, policy, source
from app.g0_authority import G0Authority
from app.g0_store import _scope_digest
from app.provenance import RequestDetail, SourceScope


def test_review_resolver_requires_independent_exact_digest_without_database():
    record = source()
    proof = fake_review(record, "right", use="internal-preview")
    holder = {"proof": None}
    authority = G0Authority(SimpleNamespace(
        review_resolver=lambda tenant, evidence_id: holder["proof"]))
    args = ("tenant-a", record, "reviewer-1", "right", "right-1")
    with pytest.raises(PermissionError, match="unavailable"):
        authority._review(*args, action="display", use="internal-preview")
    holder["proof"] = proof.model_copy(update={"content_sha256": "0" * 64})
    with pytest.raises(PermissionError, match="invalid"):
        authority._review(*args, action="display", use="internal-preview")
    holder["proof"] = fake_review(record, "right", use="public-site")
    with pytest.raises(PermissionError, match="purpose"):
        authority._review(*args, action="display", use="internal-preview")
    holder["proof"] = proof
    assert authority._review(*args, action="display", use="internal-preview") == proof


def test_caller_claims_cannot_create_approvals(env):
    build, raw, principal, _, _ = env
    record = source()
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    principal["scopes"] = {"g0_evaluate"}
    with pytest.raises(PermissionError):
        authority.approve_policy("tenant-a", policy())
    with pytest.raises(PermissionError):
        authority.approve_source("tenant-a", record.record_id,
                                 valid_to=datetime.now(timezone.utc) + timedelta(days=1))
    decision = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert decision["status"] == "hold"
    assert "policy_missing" in decision["reasons"]
    principal["scopes"].add("g0_policy")
    approved_policy = authority.approve_policy("tenant-a", policy())
    assert approved_policy.reviewer == principal["subject"]
    assert approved_policy.reviewer != "caller-claim"


def test_tenant_and_reviewer_are_resolved_from_principal(env):
    authority, record = approved(env)
    principal = env[2]
    principal["tenant_id"] = "tenant-b"
    with pytest.raises(PermissionError):
        authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    other = authority.evaluate("tenant-b", record.record_id, "display", "internal-preview")
    assert other["status"] == "hold" and "record_missing" in other["reasons"]
    principal["tenant_id"] = "tenant-a"
    principal["subject"] = "impostor"
    with pytest.raises(PermissionError):
        authority.approve_source("tenant-a", record.record_id,
                                 valid_to=datetime.now(timezone.utc) + timedelta(days=1))


def test_missing_raw_and_historical_decision_hold(env):
    authority, record = approved(env)
    env[1].clear()
    missing = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert missing["status"] == "hold" and "raw_missing" in missing["reasons"]
    env[1][("tenant-a", record.raw_sha256)] = RAW
    past = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview",
                              decision_at=datetime.now(timezone.utc) - timedelta(days=1))
    assert past["status"] == "hold" and "record_missing" in past["reasons"]
    future = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview",
                                decision_at=datetime.now(timezone.utc) + timedelta(days=1))
    assert future["status"] == "hold" and "decision_time_invalid" in future["reasons"]
    env[1][("tenant-a", record.raw_sha256)] = RAW + b"tampered"
    changed = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert changed["status"] == "hold" and "raw_hash_mismatch" in changed["reasons"]


def test_product_location_and_expired_policy_hold(env):
    other_scope = SourceScope(provider=SCOPE.provider, product_id=SCOPE.product_id,
        product_version="v2", source_url=SCOPE.source_url, station_or_grid_id="station-2")
    authority, record = approved(env, record=source(scope=other_scope))
    scoped = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert scoped["status"] == "hold" and "policy_missing" in scoped["reasons"]
    expired = policy(policy_id="policy-expired", policy_version="v1-expired",
        scope=other_scope, valid_to=datetime.now(timezone.utc) - timedelta(hours=1))
    authority.approve_policy("tenant-a", expired)
    result = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert result["status"] == "hold" and "policy_expired" in result["reasons"]


def test_revocation_and_expiry_hold_without_rewriting_decisions(env):
    authority, record = approved(env)
    first = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert first["status"] == "pass"
    authority.revoke_evidence("tenant-a", "right-1")
    revoked = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert revoked["status"] == "hold" and "right_evidence_revoked" in revoked["reasons"]
    assert authority.get_decision("tenant-a", first["decision_id"]) == first
    authority.revoke_policy("tenant-a", "policy-1")
    revoked_policy = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert "policy_revoked" in revoked_policy["reasons"]
    assert revoked_policy["approved_policy_digest"] == first["approved_policy_digest"]


def test_self_attested_labels_and_conditions_cannot_approve(env):
    build, raw, _, _, _ = env
    record = source()
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    authority.approve_policy("tenant-a", policy())
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    with pytest.raises(PermissionError, match="independent"):
        authority.approve_source("tenant-a", record.record_id, valid_to=deadline)
    with pytest.raises(PermissionError, match="independent"):
        authority.approve_check("tenant-a", record.record_id, "solar", "range", valid_to=deadline)
    with pytest.raises(ValueError, match="independent"):
        authority.approve_right("tenant-a", record.record_id, "display", "internal-preview",
            valid_to=deadline, conditions_met=True)
    with pytest.raises(PermissionError, match="independent"):
        authority.approve_right("tenant-a", record.record_id, "display", "internal-preview",
            valid_to=deadline)
    decision = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert decision["status"] == "hold"
    assert "source_review_missing" in decision["reasons"]


@pytest.mark.parametrize("change", [
    {"tenant_id": "tenant-b"}, {"raw_sha256": "0" * 64},
    {"revision_id": "wrong-revision"}, {"reviewer": "another-reviewer"},
    {"record_id": "wrong-record"},
])
def test_independent_source_binding_must_match_exact_record(env, change):
    authority, record = approved(env)
    # A new record keeps the same caller claims but has no review proof yet.
    changed = source(revision_id="revision-2")
    env[1][("tenant-a", changed.raw_sha256)] = RAW
    authority.register_record("tenant-a", changed)
    proof = fake_review(changed, "source", **change)
    env[0].proofs[("tenant-a", "source-1")] = proof
    with pytest.raises(PermissionError, match="independent"):
        authority.approve_source("tenant-a", changed.record_id,
            valid_to=datetime.now(timezone.utc) + timedelta(days=1))
    assert authority.get_decision("tenant-a", authority.evaluate(
        "tenant-a", changed.record_id, "display", "internal-preview")["decision_id"])["status"] == "hold"


def test_independent_right_must_cover_exact_use_and_conditions(env):
    build, raw, _, _, _ = env
    record = source()
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    authority.approve_policy("tenant-a", policy())
    authority.approve_policy("tenant-a", policy(policy_id="public-policy",
        policy_version="public-v1", intended_use="public-site"))
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    for kind in ("source", "check"):
        proof = fake_review(record, kind)
        build.proofs[("tenant-a", proof.evidence_id)] = proof
    authority.approve_source("tenant-a", record.record_id, valid_to=deadline)
    authority.approve_check("tenant-a", record.record_id, "solar", "range", valid_to=deadline)
    build.proofs[("tenant-a", "right-1")] = fake_review(record, "right", use="internal-preview")
    with pytest.raises(PermissionError, match="purpose"):
        authority.approve_right("tenant-a", record.record_id, "display", "public-site",
            valid_to=deadline)
    build.proofs[("tenant-a", "right-1")] = fake_review(record, "right",
        use="public-site", conditions_met=False)
    with pytest.raises(PermissionError, match="purpose"):
        authority.approve_right("tenant-a", record.record_id, "display", "public-site",
            valid_to=deadline)
    held = authority.evaluate("tenant-a", record.record_id, "display", "public-site")
    assert held["status"] == "hold" and "right_evidence_missing" in held["reasons"]


def test_review_digest_and_check_version_cannot_be_substituted(env):
    build, raw, _, _, _ = env
    record = source()
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    valid = fake_review(record, "source")
    build.proofs[("tenant-a", "source-1")] = valid.model_copy(
        update={"content_sha256": "0" * 64})
    with pytest.raises(PermissionError, match="invalid"):
        authority.approve_source("tenant-a", record.record_id, valid_to=deadline)
    build.proofs[("tenant-a", "check-1")] = fake_review(record, "check",
        check_version="v2")
    with pytest.raises(PermissionError, match="scope"):
        authority.approve_check("tenant-a", record.record_id, "solar", "range",
            valid_to=deadline)


@pytest.mark.parametrize("scope", [
    SourceScope(provider=SCOPE.provider, product_id="other-product",
        product_version=SCOPE.product_version, source_url=SCOPE.source_url,
        station_or_grid_id=SCOPE.station_or_grid_id),
    SourceScope(provider=SCOPE.provider, product_id=SCOPE.product_id,
        product_version="v2", source_url=SCOPE.source_url,
        station_or_grid_id=SCOPE.station_or_grid_id),
    SourceScope(provider=SCOPE.provider, product_id=SCOPE.product_id,
        product_version=SCOPE.product_version, source_url="https://example.org/other",
        station_or_grid_id=SCOPE.station_or_grid_id),
    SourceScope(provider=SCOPE.provider, product_id=SCOPE.product_id,
        product_version=SCOPE.product_version, source_url=SCOPE.source_url,
        station_or_grid_id="other-station"),
])
def test_review_product_version_url_and_location_must_match(env, scope):
    build, raw, _, _, _ = env
    record = source()
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    build.proofs[("tenant-a", "source-1")] = fake_review(record, "source", scope=scope)
    with pytest.raises(PermissionError, match="scope"):
        authority.approve_source("tenant-a", record.record_id,
            valid_to=datetime.now(timezone.utc) + timedelta(days=1))


def test_policy_cannot_omit_mandatory_provenance_times(env):
    build, raw, _, _, _ = env
    record = source(observed_at=None, published_at=None)
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    approved_policy = authority.approve_policy("tenant-a", policy(required_times=("available_at",)))
    assert {"observed_at", "published_at", "available_at"}.issubset(approved_policy.required_times)
    for kind in ("source", "check", "right"):
        proof = fake_review(record, kind)
        build.proofs[("tenant-a", proof.evidence_id)] = proof
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    authority.approve_source("tenant-a", record.record_id, valid_to=deadline)
    authority.approve_check("tenant-a", record.record_id, "solar", "range", valid_to=deadline)
    authority.approve_right("tenant-a", record.record_id, "display", "internal-preview",
        valid_to=deadline)
    held = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert held["status"] == "hold" and "required_time_missing" in held["reasons"]


def test_legacy_signed_policy_still_enforces_mandatory_times(env):
    build, raw, _, _, _ = env
    record = source(observed_at=None, published_at=None)
    raw[("tenant-a", record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record("tenant-a", record)
    old = policy(required_times=("available_at",))
    with authority.store.connect() as conn:
        authority.store._lock(conn, "tenant-a")
        authority.store._append(conn, tenant="tenant-a", kind="policy",
            entry_id=old.policy_id, value=old.model_dump(mode="json"),
            scope_digest=_scope_digest(old.scope), action=old.intended_action,
            intended_use=old.intended_use, generation=1)
    for kind in ("source", "check", "right"):
        proof = fake_review(record, kind)
        build.proofs[("tenant-a", proof.evidence_id)] = proof
    deadline = datetime.now(timezone.utc) + timedelta(days=1)
    authority.approve_source("tenant-a", record.record_id, valid_to=deadline)
    authority.approve_check("tenant-a", record.record_id, "solar", "range", valid_to=deadline)
    authority.approve_right("tenant-a", record.record_id, "display", "internal-preview",
        valid_to=deadline)
    held = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert held["status"] == "hold" and "required_time_missing" in held["reasons"]
    assert held["approved_policy_digest"] == old.policy_digest


def test_independent_reviews_do_not_override_request_detail_allowlist(env):
    record = source(request_details=(RequestDetail(name="station", value="other-station"),))
    authority, record = approved(env, record=record)
    held = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert held["status"] == "hold" and "request_not_allowed" in held["reasons"]
