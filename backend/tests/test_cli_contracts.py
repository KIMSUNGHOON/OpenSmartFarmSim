"""Deterministic checks for CLI proposals; synthetic authorities grant no farm claims."""

from hashlib import sha256
from dataclasses import replace
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contracts import (AuthoritySnapshot, DecisionContract, EvidenceGrant,
                               ProposalHold, parse_stage_input)
from app.jobs import canonical_input_bytes


def input_for(stage):
    base = {
        "input_version": stage + "_input_v1", "tenant_id": "tenant-a",
        "candidate_ids": ["candidate-a"],
        "evidence_refs": [{"id": "source-a", "sha256": "a" * 64}],
        "decision_context_id": None, "decision_at_utc": None, "claim_mode": None,
        "decision_time_kind": None,
    }
    if stage == "research":
        base.update(point={"latitude": 37.5, "longitude": 127.0},
                    period_start_utc="2026-01-01T00:00:00Z",
                    period_end_utc="2026-01-02T00:00:00Z",
                    provider_ids=["candidate-a"], goal_id="goal-a")
    elif stage == "collection_review":
        base.update(collection_plan_id="plan-a", record_sha256="b" * 64,
                    qc_report_id="source-a", rights_evidence_id="source-a",
                    snapshot_id="snapshot-a")
    else:
        base.update(run_id="run-a", economic_result_id="econ-a",
                    profile_id="profile-a", gate_evidence_ids=["source-a"])
    return base


def job_for(stage):
    value = input_for(stage)
    raw = canonical_input_bytes(value)
    return {"tenant_id": "tenant-a", "stage": stage, "input_bytes": raw,
            "input_sha256": sha256(raw).hexdigest(), "job_id": "job-a"}


def resolver(job, value):
    return AuthoritySnapshot(
        tenant_id=job["tenant_id"], stage=job["stage"],
        input_sha256=job["input_sha256"], candidate_ids=frozenset({"candidate-a"}),
        evidence={"source-a": EvidenceGrant("source-a", "tenant-a", "a" * 64,
                                              job["stage"], True, True, None)},
        allow_proceed=False, missing_evidence=("real_source_g0",),
        approved_claims={}, g3a_candidate_ids=frozenset(), g3b_ok=False,
        stage_bindings={key: value[key] for key in (
            {"research": {"point", "period_start_utc", "period_end_utc", "provider_ids", "goal_id"},
             "collection_review": {"collection_plan_id", "record_sha256", "qc_report_id",
                                   "rights_evidence_id", "snapshot_id"},
             "assessment": {"run_id", "economic_result_id", "profile_id",
                            "gate_evidence_ids"}}[job["stage"]])},
        decision_context_id=value["decision_context_id"],
        decision_at_utc=value["decision_at_utc"], claim_mode=value["claim_mode"],
        decision_time_kind=value["decision_time_kind"],
    )


def proposal(job, *, status="hold"):
    return {"schema_version": "decision_v1", "stage": job["stage"],
            "input_sha256": job["input_sha256"], "proposed_status": status,
            "selected_ids": [], "rejected_ids": [], "claims": [],
            "missing_evidence": ["real_source_g0"] if status == "hold" else [],
            "reason": "Synthetic evidence is insufficient.",
            "decision_context_id": None, "decision_at_utc": None,
            "claim_mode": None, "decision_time_kind": None}


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
def test_three_stage_inputs_and_server_derived_hold(stage):
    job = job_for(stage)
    assert parse_stage_input(job["input_bytes"], job)["input_version"] == stage + "_input_v1"
    contract = DecisionContract(resolver)
    final = encoded(proposal(job))
    plan = contract.plan(job, final)
    assert plan.disposition == "hold"
    assert json.loads(plan.artifact) == {
        "schema_version": "hold_v1", "reason_code": "evidence_missing",
        "missing_evidence": ["real_source_g0"]}
    result = contract(job, final, plan.artifact)
    assert result["passed"] and result["hold_report"] == plan.artifact


def test_proposal_rejects_duplicate_keys_wrong_stage_and_forged_reference():
    job = job_for("research")
    contract = DecisionContract(resolver)
    with pytest.raises(ProposalHold):
        contract.plan(job, b'{"stage":"research","stage":"assessment"}')
    value = proposal(job)
    value["stage"] = "assessment"
    with pytest.raises(ProposalHold):
        contract.plan(job, encoded(value))
    value = proposal(job)
    value["selected_ids"] = ["foreign-candidate"]
    with pytest.raises(ProposalHold):
        contract.plan(job, encoded(value))


def test_input_ref_and_context_are_bound_to_authority():
    job = job_for("collection_review")
    value = proposal(job)
    value["decision_context_id"] = "thermal-decision-context-v1:" + "a" * 64
    with pytest.raises(ProposalHold):
        DecisionContract(resolver).plan(job, encoded(value))
    bad = input_for("collection_review")
    bad["decision_context_id"] = "ctx-a"
    with pytest.raises(ProposalHold):
        parse_stage_input(canonical_input_bytes(bad), job)


def test_assessment_cannot_proceed_without_independent_candidate_gates():
    job = job_for("assessment")
    with pytest.raises(ProposalHold):
        DecisionContract(resolver).plan(job, encoded(proposal(job, status="proceed")))


def test_research_selection_must_be_in_registered_provider_requests():
    source = input_for("research")
    source["candidate_ids"].append("other-candidate")
    raw = canonical_input_bytes(source)
    job = dict(job_for("research"), input_bytes=raw,
               input_sha256=sha256(raw).hexdigest())
    value = proposal(job)
    value["selected_ids"] = ["other-candidate"]
    def expanded(current, parsed):
        return replace(resolver(current, parsed),
                       candidate_ids=frozenset({"candidate-a", "other-candidate"}))
    with pytest.raises(ProposalHold, match="provider_scope_mismatch"):
        DecisionContract(expanded).plan(job, encoded(value))


def test_authority_must_bind_stage_identity_and_tenant():
    job = job_for("collection_review")
    def wrong_snapshot(current, value):
        authority = resolver(current, value)
        return replace(authority, stage_bindings=authority.stage_bindings |
                       {"snapshot_id": "foreign-snapshot"})
    with pytest.raises(ProposalHold, match="stage_identity_mismatch"):
        DecisionContract(wrong_snapshot).plan(job, encoded(proposal(job)))

    def foreign_evidence(current, value):
        authority = resolver(current, value)
        grant = replace(authority.evidence["source-a"], tenant_id="tenant-b")
        return replace(authority, evidence={"source-a": grant})
    with pytest.raises(ProposalHold, match="evidence_scope_mismatch"):
        DecisionContract(foreign_evidence).plan(job, encoded(proposal(job)))


def test_proceed_requires_server_bound_decision_time_and_ex_ante_vintage():
    job = job_for("research")
    value = proposal(job, status="proceed")
    value["selected_ids"] = ["candidate-a"]
    def undated(current, parsed):
        return replace(resolver(current, parsed), allow_proceed=True,
                       missing_evidence=())
    with pytest.raises(ProposalHold, match="gate_hold"):
        DecisionContract(undated).plan(job, encoded(value))

    source = input_for("research")
    source.update(decision_context_id="decision-context-v1:" + "d" * 64,
                  decision_at_utc="2026-01-03T00:00:00Z",
                  claim_mode="ex_ante", decision_time_kind="actual")
    raw = canonical_input_bytes(source)
    dated_job = dict(job, input_bytes=raw, input_sha256=sha256(raw).hexdigest())
    dated = proposal(dated_job, status="proceed")
    dated.update(selected_ids=["candidate-a"],
                 decision_context_id=source["decision_context_id"],
                 decision_at_utc=source["decision_at_utc"],
                 claim_mode=source["claim_mode"],
                 decision_time_kind=source["decision_time_kind"])
    def late(current, parsed):
        authority = resolver(current, parsed)
        grant = replace(authority.evidence["source-a"],
                        available_at_utc="2026-01-04T00:00:00Z")
        return replace(authority, allow_proceed=True, missing_evidence=(),
                       evidence={"source-a": grant})
    with pytest.raises(ProposalHold, match="late_evidence"):
        DecisionContract(late).plan(dated_job, encoded(dated))
