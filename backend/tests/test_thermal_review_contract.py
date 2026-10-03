"""Thermal review bridge tests use signed and CLI capture test doubles."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys
from uuid import uuid4

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_contracts import AuthoritySnapshot, ProposalHold
from app.job_store import JobStore
from app.thermal_publisher import collection_review_input, collection_review_proposal
from app.thermal_review_contract import ThermalReviewContract
from test_job_evidence import prepare_cli_capture
from test_jobs import pg_store
from test_thermal_publisher import canonical, setup


def authority(job, value):
    return AuthoritySnapshot(
        tenant_id=job["tenant_id"], stage="collection_review",
        input_sha256=job["input_sha256"],
        candidate_ids=frozenset({value["snapshot_id"]}), evidence={},
        allow_proceed=True, missing_evidence=(), approved_claims={},
        g3a_candidate_ids=frozenset(), g3b_ok=False,
        stage_bindings={key: value[key] for key in ThermalReviewContract.BINDING_FIELDS},
        decision_context_id=value["decision_context_id"],
        decision_at_utc=value["decision_at_utc"],
        claim_mode=value["claim_mode"],
        decision_time_kind=value["decision_time_kind"])


def final_for(job, value, *, status="proceed", selected=None, missing=None):
    return canonical({
        "schema_version": "decision_v1", "stage": "collection_review",
        "input_sha256": job["input_sha256"], "proposed_status": status,
        "selected_ids": [value["snapshot_id"]] if selected is None else selected,
        "rejected_ids": [], "claims": [],
        "missing_evidence": [] if missing is None else missing,
        "reason": "Synthetic snapshot review only.",
        **{key: value[key] for key in ("decision_context_id", "decision_at_utc",
                                      "claim_mode", "decision_time_kind")}})


def test_verified_thermal_review_artifact_links_to_publisher(setup):
    publisher, runs, old_store, _, snapshot_id, _, _, _ = setup
    snapshot = runs.get_snapshot("tenant-a", snapshot_id)
    with runs.connect() as conn:
        context_id = conn.execute("SELECT decision_context_id FROM " +
            runs.schema + ".decision_contexts WHERE tenant_id = %s",
            ("tenant-a",)).fetchone()["decision_context_id"]
    context = runs.get_decision_context("tenant-a", snapshot_id, context_id)
    contract = ThermalReviewContract(runs, authority)
    store = JobStore(old_store._dsn, old_store.schema, old_store.artifact_root,
                     decision_validator=contract, evidence_policy=old_store.evidence_policy,
                     principal_provider=old_store.principal_provider)
    value = collection_review_input(snapshot, context)
    job = store.submit("tenant-a", "collection_review", value, "thermal-bridge-" + uuid4().hex)
    lease = store.claim(60, allowed_stages=("collection_review",))
    final = final_for(lease, value)
    plan = contract.plan(lease, final)
    assert plan.artifact == canonical(collection_review_proposal(snapshot, context))
    prepare_cli_capture(store, job, lease, final_output=final)
    decision = store.record_decision("tenant-a", job["job_id"], lease["attempt"],
                                    lease["lease_token"], final, plan.artifact)
    assert decision is not None
    assert store.publish("tenant-a", job["job_id"], lease["attempt"],
                         lease["lease_token"], decision, plan.artifact,
                         sha256(plan.artifact).hexdigest(), {"schema_version": "1"})
    publisher.job_store = store
    assert publisher.publish("tenant-a", job["job_id"], snapshot_id)["run_id"]


def test_thermal_review_rejects_changed_pin_and_foreign_tenant(setup):
    _, runs, _, job, snapshot_id, _, _, _ = setup
    snapshot = runs.get_snapshot("tenant-a", snapshot_id)
    with runs.connect() as conn:
        context_id = conn.execute("SELECT decision_context_id FROM " +
            runs.schema + ".decision_contexts WHERE tenant_id = %s",
            ("tenant-a",)).fetchone()["decision_context_id"]
    context = runs.get_decision_context("tenant-a", snapshot_id, context_id)
    value = collection_review_input(snapshot, context)
    contract = ThermalReviewContract(runs, authority)
    changed = dict(value, weather_sha256="0" * 64)
    raw = canonical(changed)
    forged = {"tenant_id": "tenant-a", "stage": "collection_review",
              "input_bytes": raw, "input_sha256": sha256(raw).hexdigest()}
    with pytest.raises(ProposalHold, match="unknown_input_version"):
        contract.plan(forged, final_for(forged, changed))
    raw = canonical(value)
    foreign = dict(forged, tenant_id="tenant-b", input_bytes=raw,
                   input_sha256=sha256(raw).hexdigest())
    with pytest.raises(ProposalHold, match="unknown_input_version"):
        contract.plan(foreign, final_for(foreign, value))


def test_thermal_review_preserves_trusted_hold(setup):
    _, runs, store, job, snapshot_id, _, _, _ = setup
    snapshot = runs.get_snapshot("tenant-a", snapshot_id)
    with store.connect() as conn:
        row = conn.execute("SELECT * FROM " + store.schema + ".jobs WHERE tenant_id = %s AND job_id = %s",
                           ("tenant-a", job["job_id"])).fetchone()
    value = json.loads(row["input_bytes"])
    def held_authority(current, parsed):
        return replace(authority(current, parsed), allow_proceed=False,
                       missing_evidence=("independent_review",))
    contract = ThermalReviewContract(runs, held_authority)
    final = final_for(row, value, status="hold", selected=[],
                      missing=["independent_review"])
    plan = contract.plan(row, final)
    assert plan.disposition == "hold"
    assert json.loads(plan.artifact)["missing_evidence"] == ["independent_review"]
