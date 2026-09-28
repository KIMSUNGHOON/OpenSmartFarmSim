"""A test key signs only a process the observer ran and the store sealed."""

from dataclasses import replace
from copy import copy
from hashlib import sha256
from pathlib import Path
import sys
import time
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.cli_attestation_issuer import ExecutionAttestationIssuer
from app.cli_contracts import SCHEMA_BYTES
from app.cli_supervisor import CliProcessSupervisor
from app.cli_worker import EFFORT, MODEL, PROMPT_VERSION, SCHEMA_VERSION
from app.execution_attestation import (ExecutionAttestationStore,
    install_execution_attestation_schema)
from app.execution_verifier import ExecutionVerifier
from test_cli_contracts import input_for, resolver
from test_cli_worker import _worker
from test_jobs import pg_store


def _completed_observation(pg_store, tmp_path, *, misrecorded_pid=False,
                           misrecorded_jsonl=False, misrecorded_input_kind=None,
                           stage="collection_review", proceed=True,
                           sign_before_closure=False, store_connect=None,
                           issuer_connect=None, install_attestation=True):
    def approved(job, value):
        original = resolver(job, value)
        return replace(original, allow_proceed=True, missing_evidence=()) if proceed else original

    store, worker = _worker(pg_store, tmp_path, mode="valid_slow", authority=approved)
    if install_attestation:
        with store.connect() as conn:
            install_execution_attestation_schema(conn, store.schema)
    if store_connect is not None:
        store.connect = store_connect
    review_input = input_for(stage)
    review_input.update(decision_context_id="issuer-context-a",
                        decision_at_utc="2026-01-03T00:00:00Z",
                        claim_mode="ex_post_replay", decision_time_kind="hypothetical")
    submitted = store.submit("tenant-a", stage, review_input,
                             "issuer-" + uuid4().hex)
    lease = store.claim(30, allowed_stages=(stage,))
    assert lease["job_id"] == submitted["job_id"]
    tenant, job_id, attempt, token = (lease["tenant_id"], lease["job_id"],
                                      lease["attempt"], lease["lease_token"])
    raw_input = store.read_input(tenant, job_id, attempt, token)
    job = dict(lease, input_bytes=raw_input)
    value, authority = worker.contract.input_context(job)
    prompt = worker._prompt(job, value, authority)
    prompt_row = store.append_evidence(tenant, job_id, attempt, token,
        kind="prompt", payload=(b" " + prompt if misrecorded_input_kind == "prompt" else prompt),
        rights_ref="server_cli_prompt")
    schema_row = store.append_evidence(tenant, job_id, attempt, token,
        kind="output_schema",
        payload=(b" " + SCHEMA_BYTES if misrecorded_input_kind == "schema" else SCHEMA_BYTES),
        rights_ref="server_cli_schema")
    invocation = store.register_invocation(tenant, job_id, attempt, token,
        prompt_evidence_id=prompt_row["evidence_id"],
        schema_evidence_id=schema_row["evidence_id"],
        prompt_version=PROMPT_VERSION, schema_version=SCHEMA_VERSION,
        execution_kind="codex_cli", cli_version=worker._version(),
        model=MODEL, reasoning_effort=EFFORT)
    assert invocation is not None

    observer = CliProcessSupervisor(worker.cli_path, worker.codex_home,
        child_env=worker.child_env, timeout_seconds=5)
    private = Ed25519PrivateKey.generate()
    environment_sha = sha256(b"test-supervisor-image-and-lock").hexdigest()
    issuer_store = copy(store)
    if issuer_connect is not None:
        issuer_store.connect = issuer_connect
    issuer = ExecutionAttestationIssuer(issuer_store, observer, private, "test-supervisor-v1",
        executable_sha256=sha256(worker.cli_path.read_bytes()).hexdigest(),
        environment_sha256=environment_sha)
    launch_observation = issuer.start(tenant, job_id, attempt)
    launch = store.record_cli_launch(tenant, job_id, attempt, token,
        argv=list(launch_observation.argv),
        process_id=launch_observation.process_id + (1 if misrecorded_pid else 0))
    assert launch is not None
    result = None
    for _ in range(300):
        result = observer.poll()
        if result is not None:
            break
        time.sleep(0.02)
    assert result is not None and result.termination_reason == "completed"
    with pytest.raises(ValueError, match="durable"):
        issuer.issue(uuid4(), uuid4())

    jsonl = (b" " + result.jsonl) if misrecorded_jsonl else result.jsonl
    jsonl_row = store.append_evidence(tenant, job_id, attempt, token,
        kind="jsonl", payload=jsonl, rights_ref="server_cli_jsonl")
    capture = store.seal_cli_capture(tenant, job_id, attempt, token,
        launch_id=launch["launch_id"], jsonl_evidence_id=jsonl_row["evidence_id"],
        final_output=result.final_output, exit_code=result.exit_code,
        termination_reason="completed", completed=True)
    assert capture is not None
    plan = worker.contract.plan(job, result.final_output)
    assert plan.disposition == ("proceed" if proceed else "hold")
    decision = store.record_decision(tenant, job_id, attempt, token,
                                     result.final_output, plan.artifact)
    assert decision is not None
    if sign_before_closure:
        signed_raw, signed_signature = issuer.issue(capture["capture_id"], decision)
        public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        attestations = ExecutionAttestationStore(store, {"test-supervisor-v1": public})
        attestations.put(signed_raw, signed_signature)
        assert store.get_job(tenant, job_id)["state"] in {"researching", "reviewing", "assessing"}
        assert not ExecutionVerifier(attestations,
            executable_sha256=launch_observation.executable_sha256,
            environment_sha256=environment_sha)(tenant, job_id, attempt,
                capture["capture_id"], "snapshot-a", decision)
    if proceed:
        closed = store.publish(tenant, job_id, attempt, token,
            decision, plan.artifact, sha256(plan.artifact).hexdigest(),
            {"schema_version": "1"})
    else:
        closed = store.finish_validated_hold(tenant, job_id, attempt, token,
                                             decision, plan.artifact)
    assert closed is not None
    return (store, observer, issuer, private, environment_sha,
            tenant, job_id, attempt, capture["capture_id"], decision,
            launch_observation, result)


@pytest.mark.parametrize("path_kind", ["ascii", "unicode"])
def test_issuer_signs_only_after_observed_bytes_are_durable(pg_store, tmp_path, path_kind):
    if path_kind == "unicode":
        tmp_path = tmp_path / "관측자"
        tmp_path.mkdir()
    data = _completed_observation(pg_store, tmp_path, sign_before_closure=True)
    (store, observer, issuer, private, env_sha, tenant, job_id, attempt,
     capture_id, decision_id, launch, result) = data
    raw, signature = issuer.issue(capture_id, decision_id)
    assert issuer.issue(capture_id, decision_id) == (raw, signature)
    with pytest.raises(ValueError, match="immutable"):
        issuer.issue(uuid4(), decision_id)
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    attestations = ExecutionAttestationStore(store, {"test-supervisor-v1": public})
    record = attestations.put(raw, signature)
    assert record.process_id == launch.process_id
    assert record.process_start_token == launch.process_start_token
    assert record.prompt_sha256 == launch.prompt_sha256
    assert record.schema_sha256 == launch.schema_sha256
    assert record.jsonl_sha256 == result.jsonl_sha256
    assert ExecutionVerifier(attestations,
        executable_sha256=launch.executable_sha256,
        environment_sha256=env_sha)(tenant, job_id, attempt, capture_id,
                                    "snapshot-a", decision_id)
    observer.close()


@pytest.mark.parametrize("kind", ["prompt", "schema"])
def test_issuer_refuses_noncontract_input_before_launch(pg_store, tmp_path, kind):
    with pytest.raises(ValueError, match="server contract"):
        _completed_observation(pg_store, tmp_path, misrecorded_input_kind=kind)
    assert not (tmp_path / "actual-prompt.sha256").exists()
    assert not (tmp_path / "actual-schema.sha256").exists()


@pytest.mark.parametrize("stage,proceed", [
    ("research", True), ("assessment", False), ("collection_review", False)])
def test_issuer_records_all_ai_stages_and_validated_hold(
        pg_store, tmp_path, stage, proceed):
    data = _completed_observation(pg_store, tmp_path, stage=stage, proceed=proceed,
                                   sign_before_closure=True)
    (store, observer, issuer, private, _, tenant, job_id, attempt,
     capture_id, decision_id, _, _) = data
    raw, signature = issuer.issue(capture_id, decision_id)
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    attestations = ExecutionAttestationStore(store, {"test-supervisor-v1": public})
    assert attestations.put(raw, signature).job_id == job_id
    assert store.get_job(tenant, job_id)["state"] == ("succeeded" if proceed else "hold")
    observer.close()


@pytest.mark.parametrize("alteration", ["pid", "jsonl"])
def test_issuer_rejects_plausible_store_capture_that_differs_from_child(
        pg_store, tmp_path, alteration):
    data = _completed_observation(pg_store, tmp_path,
        misrecorded_pid=alteration == "pid",
        misrecorded_jsonl=alteration == "jsonl")
    (_, observer, issuer, _, _, tenant, job_id, attempt,
     capture_id, decision_id, _, _) = data
    with pytest.raises(ValueError, match="observation"):
        issuer.issue(capture_id, decision_id)
    observer.close()
