"""Preserve real signed planning timestamps across generic CLI stage contracts."""

from hashlib import sha256
from dataclasses import replace
import json
from pathlib import Path
import sys

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.cli_contracts import DecisionContract, ProposalHold
from app.jobs import canonical_input_bytes
from app.planning_events import PlanningAuthority, DecisionContextVerifier
from test_cli_contracts import input_for, resolver
from test_planning_roles import scope, login_database


def job_for(value):
    raw = canonical_input_bytes(value)
    return {"tenant_id": "tenant-a", "stage": value["input_version"].removesuffix("_input_v1"),
            "input_bytes": raw, "input_sha256": sha256(raw).hexdigest()}


@pytest.mark.parametrize("stage", ["research", "collection_review", "assessment"])
def test_signed_server_microsecond_context_is_usable_without_truncation(scope, stage):
    _admin, _policy, stores, _dsns = scope
    key = Ed25519PrivateKey.generate()
    authority = PlanningAuthority(stores["authority"], "test-planning-v1", key)
    raw, signature = authority.issue("tenant-a", "snapshot-a", claim_mode="ex_post_replay", decision_time_kind="actual")
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, stores["supervisor"].read_event)
    assert verifier(raw, signature) is not None
    context = json.loads(raw)
    value = input_for(stage)
    value.update({name: context[name] for name in ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")})
    parsed, _authority = DecisionContract(resolver).input_context(job_for(value))
    assert parsed["decision_at_utc"] == context["decision_at_utc"]


@pytest.mark.parametrize("instant", ["2026-01-01T00:00:00Z", "2026-01-01T00:00:00.1Z",
                                     "2026-01-01T00:00:00.123Z", "2026-01-01T00:00:00.123456Z"])
def test_supported_utc_precision_remains_exact_input_text(instant):
    value = input_for("research")
    value.update(decision_context_id="context-a", decision_at_utc=instant,
                 claim_mode="ex_post_replay", decision_time_kind="actual")
    parsed, _authority = DecisionContract(resolver).input_context(job_for(value))
    assert parsed["decision_at_utc"] == instant


@pytest.mark.parametrize("instant", ["2026-01-01T00:00:00.1234567Z", "2026-02-30T00:00:00.123456Z",
                                     "2026-01-01T00:00:00.123456+00:00", "2026-01-01T00:00:00.Z"])
def test_unsupported_precision_or_invalid_utc_holds(instant):
    value = input_for("research")
    value.update(decision_context_id="context-a", decision_at_utc=instant,
                 claim_mode="ex_post_replay", decision_time_kind="actual")
    with pytest.raises(ProposalHold, match="^invalid_utc$"):
        DecisionContract(resolver).input_context(job_for(value))


def test_ex_ante_evidence_one_microsecond_after_d_remains_late():
    value = input_for("research")
    value.update(decision_context_id="context-a", decision_at_utc="2026-01-01T00:00:00.123456Z",
                 claim_mode="ex_ante", decision_time_kind="hypothetical")
    def late_registry(job, parsed):
        authority = resolver(job, parsed)
        return replace(authority, evidence={name: replace(grant, available_at_utc="2026-01-01T00:00:00.123457Z")
            for name, grant in authority.evidence.items()})
    with pytest.raises(ProposalHold, match="^late_evidence$"):
        DecisionContract(late_registry).input_context(job_for(value))
