"""Signed completion candidates are bound to the durable CLI attempt."""

from dataclasses import replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import sys
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.execution_attestation import (DOMAIN, ExecutionAttestation,
    ExecutionAttestationStore, decode_attestation, encode_attestation,
    install_execution_attestation_schema, verify_signature)
from app.execution_verifier import ExecutionVerifier
from test_cli_contracts import input_for, resolver
from test_cli_worker import _worker
from test_jobs import pg_store


def test_authored_review_snapshot_field_is_exact():
    assert ExecutionVerifier._snapshot_matches(
        {'input_version':'farm-authored-review-input-v1',
         'base_snapshot_id':'source-snapshot'}, 'source-snapshot')
    assert not ExecutionVerifier._snapshot_matches(
        {'input_version':'farm-authored-review-input-v1',
         'snapshot_id':'source-snapshot'}, 'source-snapshot')
    assert ExecutionVerifier._snapshot_matches(
        {'input_version':'owned-collection-review-input-v1',
         'snapshot_id':'source-snapshot'}, 'source-snapshot')


def _completed(pg_store, tmp_path, *, misrecorded_kind=None):
    def approved(job, value):
        return replace(resolver(job, value), allow_proceed=True, missing_evidence=())

    store, worker = _worker(pg_store, tmp_path, authority=approved)
    with store.connect() as conn:
        install_execution_attestation_schema(conn, store.schema)
    seen = {}
    original = store.record_cli_launch

    def captured_launch(*args, **kwargs):
        seen["argv"] = list(kwargs["argv"])
        return original(*args, **kwargs)

    store.record_cli_launch = captured_launch
    if misrecorded_kind is not None:
        assert misrecorded_kind in {"prompt", "output_schema"}
        original_append = store.append_evidence

        def misrecorded_evidence(*args, **kwargs):
            if kwargs.get("kind") == misrecorded_kind:
                kwargs["payload"] += b" "
            return original_append(*args, **kwargs)

        store.append_evidence = misrecorded_evidence
    review_input = input_for("collection_review")
    review_input.update(decision_context_id="attestation-context-a",
                        decision_at_utc="2026-01-03T00:00:00Z",
                        claim_mode="ex_post_replay", decision_time_kind="hypothetical")
    job = store.submit("tenant-a", "collection_review", review_input,
                       "attested-" + uuid4().hex)
    worked = worker.run_once()
    assert worked.state == "succeeded" and worked.capture_id and worked.decision_id, (
        worked.state, worked.reason_code)
    with store.connect() as conn:
        rows = {}
        for name in ("jobs", "attempt_invocations", "attempt_cli_launches",
                     "attempt_cli_captures"):
            rows[name] = conn.execute(sql.SQL("""
                SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s
            """).format(store._table(name)), ("tenant-a", job["job_id"])).fetchone()
    return store, worker, worked, rows, seen["argv"]


def _signed(store, worker, worked, rows, argv, *, private=None, observed_hashes=None):
    private = private or Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    job = rows["jobs"]
    invocation = rows["attempt_invocations"]
    launch = rows["attempt_cli_launches"]
    capture = rows["attempt_cli_captures"]
    binary_sha = sha256(Path(worker.cli_path).read_bytes()).hexdigest()
    env_sha = sha256(b"synthetic-test-environment").hexdigest()
    assert job["created_at"] <= capture["sealed_at"], (
        job["created_at"], capture["sealed_at"])
    prompt_hash, schema_hash = observed_hashes or (
        (Path(worker.cli_path).parent / "actual-prompt.sha256").read_text(),
        (Path(worker.cli_path).parent / "actual-schema.sha256").read_text())
    record = ExecutionAttestation(
        record_version="cli-execution-attestation-v1", key_id="test-observer-v1",
        tenant_id=job["tenant_id"], job_id=worked.job_id, attempt=worked.attempt,
        attempt_id=invocation["attempt_id"], nonce=uuid4(),
        input_sha256=job["input_sha256"],
        prompt_sha256=prompt_hash,
        schema_sha256=schema_hash,
        cli_version=invocation["cli_version"],
        executable_sha256=binary_sha, argv=argv, environment_sha256=env_sha,
        launch_id=launch["launch_id"], capture_id=worked.capture_id,
        jsonl_sha256=capture["jsonl_sha256"],
        final_output_sha256=capture["final_output_sha256"],
        process_id=launch["process_id"], process_start_token="test-process-start",
        started_at_utc=job["created_at"].astimezone(timezone.utc),
        ended_at_utc=capture["sealed_at"].astimezone(timezone.utc),
        signed_at_utc=datetime.now(timezone.utc),
        exit_code=0,
        termination_reason="completed", usage=capture["usage"])
    raw = encode_attestation(record)
    signature = private.sign(DOMAIN + raw)
    attestations = ExecutionAttestationStore(store, {"test-observer-v1": public})
    verifier = ExecutionVerifier(attestations, executable_sha256=binary_sha,
                                 environment_sha256=env_sha)
    return record, raw, signature, attestations, verifier, private


def test_attestation_with_recorded_hashes_needs_no_fake_cli_sidecars(pg_store, tmp_path):
    data = _completed(pg_store, tmp_path)
    _, worker, _, rows, _ = data
    for name in ("actual-prompt.sha256", "actual-schema.sha256"):
        (Path(worker.cli_path).parent / name).unlink()
    invocation = rows["attempt_invocations"]
    record, *_ = _signed(*data, observed_hashes=(
        invocation["prompt_sha256"], invocation["schema_sha256"]))
    assert (record.prompt_sha256, record.schema_sha256) == (
        invocation["prompt_sha256"], invocation["schema_sha256"])


def test_signed_cli_completion_binds_exact_job_capture_and_decision(pg_store, tmp_path):
    data = _completed(pg_store, tmp_path)
    store, _, worked, _, _ = data
    record, raw, signature, attestations, verifier, _ = _signed(*data)
    assert decode_attestation(raw) == record
    args = ("tenant-a", worked.job_id, worked.attempt, worked.capture_id,
            "snapshot-a", worked.decision_id)
    assert verifier(*args) is False  # A plausible JobStore capture is insufficient.
    assert attestations.put(raw, signature) == record
    assert attestations.put(raw, signature) == record
    assert attestations.get("tenant-a", worked.job_id, worked.attempt) == record
    assert verifier(*args) is True
    assert verifier("tenant-b", *args[1:]) is False
    assert verifier(*args[:-2], "other-snapshot", args[-1]) is False
    assert verifier(*args[:-1], uuid4()) is False
    assert verifier("tenant-a", worked.job_id, worked.attempt, uuid4(),
                    "snapshot-a", worked.decision_id) is False
    with store.connect() as conn, pytest.raises(errors.RaiseException):
        conn.execute(sql.SQL("""
            DELETE FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
        """).format(attestations._table()),
            ("tenant-a", worked.job_id, worked.attempt))


def test_attestation_rejects_forgery_and_nonce_reuse(pg_store, tmp_path):
    data = _completed(pg_store, tmp_path)
    store, _, worked, _, _ = data
    record, raw, signature, attestations, verifier, private = _signed(*data)
    changed = record.model_copy(update={"final_output_sha256": "0" * 64})
    with pytest.raises(ValueError, match="signature invalid"):
        verify_signature(encode_attestation(changed), signature, attestations.public_keys)
    signed_wrong = encode_attestation(changed)
    attestations.put(signed_wrong, private.sign(DOMAIN + signed_wrong))
    assert verifier("tenant-a", worked.job_id, worked.attempt,
                    worked.capture_id, "snapshot-a", worked.decision_id) is False
    with pytest.raises(ValueError, match="immutable pin conflict"):
        attestations.put(raw, signature)
    unsafe_argv = list(record.argv)
    unsafe_argv[9] = "workspace-write"
    assert ExecutionVerifier._argv_ok(unsafe_argv) is False
    other_job = store.submit("tenant-a", "collection_review", input_for("collection_review"),
                             "nonce-reuse-" + uuid4().hex)
    other_lease = store.claim(60, allowed_stages=("collection_review",))
    assert other_lease["job_id"] == other_job["job_id"]
    with store.connect() as conn:
        other_attempt = conn.execute(sql.SQL("""
            SELECT attempt_id FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s
        """).format(store._table("job_attempts")),
            ("tenant-a", other_job["job_id"], other_lease["attempt"])).fetchone()
    replay = record.model_copy(update={"job_id": other_job["job_id"],
                                      "attempt": other_lease["attempt"],
                                      "attempt_id": other_attempt["attempt_id"]})
    replay_raw = encode_attestation(replay)
    with pytest.raises(ValueError, match="immutable pin conflict"):
        attestations.put(replay_raw, private.sign(DOMAIN + replay_raw))
    with pytest.raises(ValueError, match="canonical"):
        decode_attestation(raw + b" ")
    with pytest.raises(ValueError, match="duplicate"):
        decode_attestation(b'{"key_id":"one","key_id":"two"}')
    assert ExecutionVerifier(attestations, executable_sha256="0" * 64,
                             environment_sha256=record.environment_sha256)(
        "tenant-a", worked.job_id, worked.attempt, worked.capture_id,
        "snapshot-a", worked.decision_id) is False


@pytest.mark.parametrize("kind,digest_field", [
    ("prompt", "prompt_sha256"), ("output_schema", "schema_sha256")])
def test_actual_cli_input_bytes_must_match_durable_invocation(
        pg_store, tmp_path, kind, digest_field):
    data = _completed(pg_store, tmp_path, misrecorded_kind=kind)
    store, _, worked, rows, _ = data
    record, raw, signature, attestations, verifier, _ = _signed(*data)
    assert getattr(record, digest_field) != rows["attempt_invocations"][digest_field]
    attestations.put(raw, signature)
    assert verifier("tenant-a", worked.job_id, worked.attempt,
                    worked.capture_id, "snapshot-a", worked.decision_id) is False
    assert store.get_job("tenant-a", worked.job_id)["state"] == "succeeded"


def test_request_role_cannot_insert_execution_attestation(pg_store, tmp_path):
    store, _, _, _, _ = _completed(pg_store, tmp_path)
    role = "ossf_attestation_request_" + uuid4().hex
    created = False
    try:
        with store.connect() as conn:
            owner = conn.execute("SELECT current_user AS name").fetchone()["name"]
            try:
                conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
                conn.execute(sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(role), sql.Identifier(owner)))
            except errors.InsufficientPrivilege:
                pytest.skip("test server cannot create isolated role")
            created = True
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(store.schema), sql.Identifier(role)))
            conn.execute(sql.SQL("GRANT SELECT ON {}.execution_attestations TO {}").format(
                sql.Identifier(store.schema), sql.Identifier(role)))
        with store.connect() as conn:
            conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            with pytest.raises(errors.InsufficientPrivilege):
                conn.execute(sql.SQL("""
                    INSERT INTO {}.execution_attestations
                    SELECT * FROM {}.execution_attestations WHERE false
                """).format(sql.Identifier(store.schema), sql.Identifier(store.schema)))
    finally:
        if created:
            with store.connect() as conn:
                conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
