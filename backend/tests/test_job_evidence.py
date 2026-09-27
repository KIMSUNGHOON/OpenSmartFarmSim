"""Synthetic storage-contract tests; these do not certify an actual CLI run or G0–G4."""

from hashlib import sha256
import json
import os
from uuid import UUID, uuid4

from psycopg import errors, sql
import pytest

from test_jobs import (pg_store, prepare_synthetic_invocation, submit,
                       synthetic_decision_bytes, validated_decision)


def test_attempt_ids_and_failure_outcomes_need_no_ai_decision(pg_store):
    job = submit(pg_store, max_attempts=2)
    first = pg_store.claim(60)
    assert UUID(str(first["attempt_id"]))
    assert pg_store.fail("tenant-a", job["job_id"], 1, first["lease_token"],
                         "transient", "cli_timeout", retry_delay_seconds=0)
    outcomes = pg_store.list_attempt_outcomes("tenant-a", job["job_id"])
    assert len(outcomes) == 1
    assert outcomes[0]["attempt_id"] == first["attempt_id"]
    assert outcomes[0]["state"] == "queued"
    assert outcomes[0]["reason"]["code"] == "cli_timeout"
    assert outcomes[0]["decision_id"] is None
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []
    second = pg_store.claim(60)
    assert second["attempt_id"] != first["attempt_id"]
    assert pg_store.fail("tenant-a", job["job_id"], 2, second["lease_token"],
                         "hold", "rights_missing")
    assert [row["state"] for row in pg_store.list_attempt_outcomes("tenant-a", job["job_id"])] == ["queued", "hold"]
    assert pg_store.list_attempt_outcomes("tenant-b", job["job_id"]) == []


def test_private_evidence_is_hashed_tenant_scoped_and_withheld_is_explicit(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    evidence = pg_store.append_evidence(
        "tenant-a", job["job_id"], 1, lease["lease_token"],
        kind="prompt", payload=b"synthetic prompt", rights_ref="self_authored_fixture",
    )
    assert evidence["sha256"] == sha256(b"synthetic prompt").hexdigest()
    assert evidence["size"] == len(b"synthetic prompt")
    assert pg_store.read_evidence("tenant-a", job["job_id"], evidence["evidence_id"],
                                  access="auditor") == b"synthetic prompt"
    assert pg_store.read_evidence("tenant-b", job["job_id"], evidence["evidence_id"],
                                  access="auditor") is None
    assert pg_store.read_evidence("tenant-a", job["job_id"], evidence["evidence_id"],
                                  access="public") is None
    withheld = pg_store.append_evidence(
        "tenant-a", job["job_id"], 1, lease["lease_token"], kind="tool_event",
        payload=None, withhold_reason="rights_not_granted", rights_ref="restricted_fixture",
    )
    assert withheld["sha256"] is None and withheld["size"] is None
    assert withheld["withhold_reason"] == "rights_not_granted"
    assert pg_store.read_evidence("tenant-a", job["job_id"], withheld["evidence_id"],
                                  access="auditor") is None
    assert b"synthetic prompt" not in str(pg_store.list_evidence("tenant-a", job["job_id"])).encode()


def test_decision_requires_final_bytes_server_validation_and_exact_publication(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prepare_synthetic_invocation(pg_store, job, lease)
    public = b"synthetic result artifact"
    final = synthetic_decision_bytes(job)
    with pytest.raises((TypeError, ValueError)):
        pg_store.record_decision("tenant-a", job["job_id"], 1,
                                 lease["lease_token"], sha256(final).hexdigest(), public)
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
                                    lease["lease_token"], b"invalid JSON", public) is None
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        lease["lease_token"], final, public)
    assert UUID(str(decision))
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
                                    lease["lease_token"], final, public) is None
    rows = pg_store.list_decisions("tenant-a", job["job_id"])
    assert len(rows) == 1 and rows[0]["output_sha256"] == sha256(final).hexdigest()
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                            decision, b"changed artifact", sha256(b"changed artifact").hexdigest(),
                            {"schema_version": "1"}) is None
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                            decision, public, sha256(public).hexdigest(),
                            {"schema_version": "1"})
    assert pg_store.list_attempt_outcomes("tenant-a", job["job_id"])[0]["decision_id"] == decision


def test_expired_attempt_has_auditable_outcome_and_cannot_publish(pg_store):
    job = submit(pg_store, max_attempts=2)
    first = pg_store.claim(60)
    prepare_synthetic_invocation(pg_store, job, first)
    public = b"synthetic old result"
    decision = pg_store.record_decision("tenant-a", job["job_id"], 1,
                                        first["lease_token"], synthetic_decision_bytes(job), public)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second' WHERE job_id = %s")
                     .format(sql.Identifier(pg_store.schema)), (job["job_id"],))
    restarted = type(pg_store)(os.environ["OSSF_TEST_PG_DSN"], pg_store.schema,
                               pg_store.artifact_root,
                               decision_validator=pg_store.decision_validator,
                               evidence_policy=pg_store.evidence_policy,
                               principal_provider=pg_store.principal_provider,
                               allow_synthetic_invocation=True)
    second = restarted.claim(60)
    assert second["attempt_id"] != first["attempt_id"]
    outcomes = restarted.list_attempt_outcomes("tenant-a", job["job_id"])
    assert len(outcomes) == 1 and outcomes[0]["reason"]["code"] == "lease_expired"
    assert outcomes[0]["termination_reason"] == "lease_expired"
    assert outcomes[0]["exit_code"] is None and outcomes[0]["usage"] is None
    assert outcomes[0]["decision_id"] == decision
    assert restarted.publish("tenant-a", job["job_id"], 1, first["lease_token"],
                             decision, public, sha256(public).hexdigest(),
                             {"schema_version": "1"}) is None
    assert restarted.get_publication("tenant-a", job["job_id"]) is None


def test_cancel_and_publication_outcomes_are_append_only(pg_store):
    queued = submit(pg_store, key="queued")
    assert pg_store.cancel("tenant-a", queued["job_id"])
    assert pg_store.list_attempt_outcomes("tenant-a", queued["job_id"]) == []
    active = submit(pg_store, key="active")
    lease = pg_store.claim(60)
    assert pg_store.cancel("tenant-a", active["job_id"])
    assert pg_store.ack_cancel("tenant-a", active["job_id"], 1, lease["lease_token"])
    rows = pg_store.list_attempt_outcomes("tenant-a", active["job_id"])
    assert len(rows) == 1 and rows[0]["state"] == "canceled"
    assert rows[0]["decision_id"] is None
    with pg_store.connect() as conn, pytest.raises(Exception):
        conn.execute(sql.SQL("DELETE FROM {}.attempt_outcomes").format(sql.Identifier(pg_store.schema)))


def test_missing_policy_validator_and_reader_fail_closed(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    default_store = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root)
    withheld = default_store.append_evidence(
        "tenant-a", job["job_id"], 1, lease["lease_token"], kind="prompt",
        payload=b"synthetic denied raw", rights_ref="self_authored_fixture")
    assert withheld["withhold_reason"] == "policy_denied"
    assert withheld["sha256"] is None and withheld["size"] is None
    assert default_store.record_decision("tenant-a", job["job_id"], 1,
        lease["lease_token"], synthetic_decision_bytes(job), b"synthetic public") is None
    prepare_synthetic_invocation(pg_store, job, lease)
    policyless = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root,
                                decision_validator=pg_store.decision_validator,
                                principal_provider=pg_store.principal_provider)
    assert policyless.record_decision("tenant-a", job["job_id"], 1,
        lease["lease_token"], synthetic_decision_bytes(job), b"synthetic public") is None
    finals = [row for row in policyless.list_evidence("tenant-a", job["job_id"])
              if row["kind"] == "final_output"]
    assert len(finals) == 1 and finals[0]["withhold_reason"] == "policy_denied"
    allowed = pg_store.append_evidence(
        "tenant-a", job["job_id"], 1, lease["lease_token"], kind="prompt",
        payload=b"synthetic allowed raw", rights_ref="self_authored_fixture")
    assert default_store.read_evidence("tenant-a", job["job_id"],
                                       allowed["evidence_id"], access="auditor") is None


def test_evidence_corruption_and_late_upload_are_audit_only(pg_store):
    job = submit(pg_store, max_attempts=2)
    first = pg_store.claim(60)
    evidence = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        first["lease_token"], kind="jsonl", payload=b"synthetic event",
        rights_ref="self_authored_fixture")
    location = (pg_store.artifact_root / ".evidence" /
                sha256(b"tenant-a").hexdigest() / evidence["sha256"])
    location.write_bytes(b"corrupt bytes")
    with pytest.raises(ValueError, match="corrupt"):
        pg_store.read_evidence("tenant-a", job["job_id"],
                               evidence["evidence_id"], access="auditor")
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("""
            UPDATE {}.jobs SET lease_until = clock_timestamp() - interval '1 second'
            WHERE tenant_id = %s AND job_id = %s
        """).format(sql.Identifier(pg_store.schema)), ("tenant-a", job["job_id"]))
    second = pg_store.claim(60)
    late = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        first["lease_token"], kind="tool_event", payload=b"synthetic late event",
        rights_ref="self_authored_fixture")
    assert late["late"] is True
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
        first["lease_token"], synthetic_decision_bytes(job), b"synthetic old") is None
    assert second["attempt_id"] != first["attempt_id"]
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []


def test_failed_validation_has_report_without_decision(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prepare_synthetic_invocation(pg_store, job, lease)
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
        lease["lease_token"], b"invalid JSON", b"synthetic proposed") is None
    evidence = pg_store.list_evidence("tenant-a", job["job_id"])
    assert [row["kind"] for row in evidence if row["kind"] in
            ("final_output", "validation_report")] == ["final_output", "validation_report"]
    assert all(row["sha256"] is not None for row in evidence)
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None


def test_evidence_bounds_and_history_never_store_plain_lease(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    with pytest.raises(ValueError, match="size limit"):
        pg_store.append_evidence("tenant-a", job["job_id"], 1,
            lease["lease_token"], kind="final_output", payload=b"x" * (1048576 + 1),
            rights_ref="self_authored_fixture")
    with pg_store.connect() as conn:
        row = conn.execute(sql.SQL("""
            SELECT * FROM {}.job_attempts WHERE tenant_id = %s AND job_id = %s
        """).format(sql.Identifier(pg_store.schema)), ("tenant-a", job["job_id"])).fetchone()
    assert "lease_token" not in row
    assert lease["lease_token"] not in str(row)


def test_invocation_binds_input_prompt_schema_version_and_execution_identity(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
        lease["lease_token"], synthetic_decision_bytes(job), b"synthetic result") is None
    prepare_synthetic_invocation(pg_store, job, lease)
    manifest = pg_store.get_invocation("tenant-a", job["job_id"], 1)
    assert manifest["attempt_id"] == lease["attempt_id"]
    assert manifest["input_sha256"] == job["input_sha256"]
    assert manifest["prompt_version"] == "synthetic-v1"
    assert manifest["schema_version"] == "synthetic-v1"
    assert manifest["prompt_sha256"] == sha256(b"synthetic instruction v1").hexdigest()
    assert manifest["schema_sha256"] == sha256(b'{"fixture":"synthetic"}').hexdigest()
    assert manifest["execution_kind"] == "synthetic_fixture"
    assert manifest["cli_version"] == "synthetic_fixture"
    assert manifest["model"] is None and manifest["reasoning_effort"] is None
    assert pg_store.get_invocation("tenant-b", job["job_id"], 1) is None
    with pg_store.connect() as conn, pytest.raises(Exception):
        conn.execute(sql.SQL("UPDATE {}.attempt_invocations SET prompt_version = 'changed'")
                     .format(sql.Identifier(pg_store.schema)))


def test_runtime_invocation_requires_exact_model_effort_and_real_version(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prompt = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="prompt", payload=b"synthetic prompt",
        rights_ref="self_authored_fixture")
    schema = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="output_schema", payload=b"synthetic schema",
        rights_ref="self_authored_fixture")
    args = dict(prompt_evidence_id=prompt["evidence_id"],
                schema_evidence_id=schema["evidence_id"], prompt_version="v1",
                schema_version="v1", execution_kind="codex_cli",
                cli_version="codex-cli 0.157.1", model="gpt-6-sol",
                reasoning_effort="xhigh")
    for override in ({"model": "other"}, {"reasoning_effort": "high"},
                     {"cli_version": "unverified"}):
        with pytest.raises(ValueError):
            pg_store.register_invocation("tenant-a", job["job_id"], 1,
                lease["lease_token"], **(args | override))
    assert pg_store.register_invocation("tenant-a", job["job_id"], 1,
        lease["lease_token"], **args)
    manifest = pg_store.get_invocation("tenant-a", job["job_id"], 1)
    assert (manifest["model"], manifest["reasoning_effort"], manifest["cli_version"]) == (
        "gpt-6-sol", "xhigh", "codex-cli 0.157.1")
    assert pg_store.get_invocation("tenant-b", job["job_id"], 1) is None


def test_outcome_binds_usage_exit_reason_jsonl_and_survives_restart(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prepare_synthetic_invocation(pg_store, job, lease)
    jsonl = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="jsonl", payload=b"synthetic JSONL event",
        rights_ref="self_authored_fixture")
    assert pg_store.fail("tenant-a", job["job_id"], 1, lease["lease_token"],
        "fatal", "cli_exit_nonzero", exit_code=2, termination_reason="cli_exit_nonzero",
        usage={"input_tokens": 7, "output_tokens": 3, "total_tokens": 10},
        jsonl_evidence_id=jsonl["evidence_id"])
    restarted = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root,
        principal_provider=pg_store.principal_provider)
    outcome = restarted.list_attempt_outcomes("tenant-a", job["job_id"])[0]
    assert outcome["attempt_id"] == lease["attempt_id"]
    assert outcome["exit_code"] == 2
    assert outcome["termination_reason"] == "cli_exit_nonzero"
    assert outcome["usage"] == {"input_tokens": 7, "output_tokens": 3, "total_tokens": 10}
    assert outcome["jsonl_evidence_id"] == jsonl["evidence_id"]
    assert restarted.get_invocation("tenant-a", job["job_id"], 1)["input_sha256"] == job["input_sha256"]
    assert restarted.read_evidence("tenant-a", job["job_id"], jsonl["evidence_id"],
                                   access="auditor") == b"synthetic JSONL event"
    assert restarted.list_attempt_outcomes("tenant-b", job["job_id"]) == []


def test_queued_cancel_after_failed_attempt_keeps_original_outcome(pg_store):
    job = submit(pg_store, max_attempts=2)
    lease = pg_store.claim(60)
    assert pg_store.fail("tenant-a", job["job_id"], 1, lease["lease_token"],
                         "transient", "provider_503", retry_delay_seconds=30)
    assert pg_store.cancel("tenant-a", job["job_id"])
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "canceled"
    assert [row["state"] for row in pg_store.list_attempt_outcomes("tenant-a", job["job_id"])] == ["queued"]


def test_invocation_rejects_wrong_evidence_and_default_denies_synthetic(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prompt = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="prompt", payload=b"synthetic prompt",
        rights_ref="self_authored_fixture")
    schema = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="output_schema", payload=b"synthetic schema",
        rights_ref="self_authored_fixture")
    wrong_kind = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="tool_event", payload=b"synthetic event",
        rights_ref="self_authored_fixture")
    other = submit(pg_store, tenant="tenant-b")
    other_lease = pg_store.claim(60)
    other_prompt = pg_store.append_evidence("tenant-b", other["job_id"], 1,
        other_lease["lease_token"], kind="prompt", payload=b"synthetic other prompt",
        rights_ref="self_authored_fixture")
    args = dict(prompt_evidence_id=prompt["evidence_id"],
                schema_evidence_id=schema["evidence_id"], prompt_version="v1",
                schema_version="v1", execution_kind="synthetic_fixture",
                cli_version="synthetic_fixture", model=None, reasoning_effort=None)
    for bad_id in (wrong_kind["evidence_id"], other_prompt["evidence_id"]):
        with pytest.raises(ValueError, match="retained current prompt"):
            pg_store.register_invocation("tenant-a", job["job_id"], 1,
                lease["lease_token"], **(args | {"prompt_evidence_id": bad_id}))
    default_store = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root,
        evidence_policy=pg_store.evidence_policy)
    with pytest.raises(ValueError, match="synthetic invocation"):
        default_store.register_invocation("tenant-a", job["job_id"], 1,
            lease["lease_token"], **args)
    assert pg_store.get_invocation("tenant-a", job["job_id"], 1) is None


def test_outcome_rejects_wrong_jsonl_reference_and_secret_usage(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    wrong_kind = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="tool_event", payload=b"synthetic event",
        rights_ref="self_authored_fixture")
    other = submit(pg_store, tenant="tenant-b")
    other_lease = pg_store.claim(60)
    other_jsonl = pg_store.append_evidence("tenant-b", other["job_id"], 1,
        other_lease["lease_token"], kind="jsonl", payload=b"synthetic JSONL",
        rights_ref="self_authored_fixture")
    for bad_id in (wrong_kind["evidence_id"], other_jsonl["evidence_id"]):
        with pytest.raises(ValueError, match="JSONL evidence"):
            pg_store.fail("tenant-a", job["job_id"], 1, lease["lease_token"],
                "fatal", "cli_error", jsonl_evidence_id=bad_id)
    for bad_usage in ({"api_key": 1}, {"input_tokens": True}, {"input_tokens": -1}):
        with pytest.raises(ValueError, match="usage"):
            pg_store.fail("tenant-a", job["job_id"], 1, lease["lease_token"],
                "fatal", "cli_error", usage=bad_usage)
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "researching"
    assert pg_store.list_attempt_outcomes("tenant-a", job["job_id"]) == []


def test_direct_decision_insert_requires_current_attempt_manifest(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    final = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="final_output", payload=synthetic_decision_bytes(job),
        rights_ref="self_authored_fixture")
    report = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="validation_report", payload=b"synthetic report",
        rights_ref="self_authored_fixture")
    with pg_store.connect() as conn, pytest.raises(errors.CheckViolation,
                                                   match="decision needs retained"):
        conn.execute(sql.SQL("""
            INSERT INTO {}.ai_decisions
                (tenant_id, job_id, attempt, decision_id, output_sha256,
                 artifact_sha256, final_evidence_id, validation_evidence_id)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", job["job_id"], UUID("00000000-0000-0000-0000-000000000001"),
             final["sha256"], sha256(b"synthetic result").hexdigest(),
             final["evidence_id"], report["evidence_id"]))
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []


def test_corrupt_validation_report_blocks_publication(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    payload = b"synthetic public result"
    decision = validated_decision(pg_store, job, lease, payload)
    decision_row = pg_store.list_decisions("tenant-a", job["job_id"])[0]
    report = next(row for row in pg_store.list_evidence("tenant-a", job["job_id"])
                  if row["evidence_id"] == decision_row["validation_evidence_id"])
    location = (pg_store.artifact_root / ".evidence" /
                sha256(b"tenant-a").hexdigest() / report["sha256"])
    location.write_bytes(b"corrupted report")
    try:
        publication = pg_store.publish("tenant-a", job["job_id"], 1,
            lease["lease_token"], decision, payload, sha256(payload).hexdigest(),
            {"schema_version": "1"})
    except (OSError, ValueError):
        publication = None
    assert publication is None
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None
    assert pg_store.get_job("tenant-a", job["job_id"])["state"] == "researching"


def test_database_rejects_decision_insert_after_attempt_failed(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prepare_synthetic_invocation(pg_store, job, lease)
    invocation = pg_store.get_invocation("tenant-a", job["job_id"], 1)
    artifact_digest = sha256(b"synthetic public").hexdigest()
    final = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="final_output",
        payload=synthetic_decision_bytes(job), rights_ref="self_authored_fixture")
    report_bytes = pg_store._canonical_report({
        "report_version": "decision-validation-v1", "passed": True,
        "validator_version": "synthetic-storage-v1", "validator_code": "synthetic_pass",
        **pg_store._validation_context(job, invocation, final["sha256"], artifact_digest),
    })
    report = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="validation_report",
        payload=report_bytes, rights_ref="server_validation")
    receipt_id, decision_id = uuid4(), uuid4()
    direct_insert = sql.SQL("""
        INSERT INTO {}.ai_decisions
            (tenant_id, job_id, attempt, decision_id, output_sha256,
             artifact_sha256, final_evidence_id, validation_evidence_id, receipt_id)
        VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s)
    """).format(sql.Identifier(pg_store.schema))
    direct_args = ("tenant-a", job["job_id"], decision_id, final["sha256"],
                   artifact_digest, final["evidence_id"], report["evidence_id"], receipt_id)
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("""
            INSERT INTO {}.validation_receipts
                (tenant_id, job_id, attempt, attempt_id, receipt_id,
                 final_evidence_id, validation_evidence_id, report_sha256,
                 output_sha256, artifact_sha256, input_sha256,
                 prompt_evidence_id, schema_evidence_id, prompt_sha256,
                 schema_sha256, prompt_version, schema_version,
                 execution_kind, cli_version, model, reasoning_effort, stage,
                 validator_version, validator_code, passed)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", job["job_id"], lease["attempt_id"], receipt_id,
             final["evidence_id"], report["evidence_id"], report["sha256"],
             final["sha256"], artifact_digest, job["input_sha256"],
             invocation["prompt_evidence_id"], invocation["schema_evidence_id"],
             invocation["prompt_sha256"], invocation["schema_sha256"],
             invocation["prompt_version"], invocation["schema_version"],
             invocation["execution_kind"], invocation["cli_version"],
             invocation["model"], invocation["reasoning_effort"], job["stage"],
             "synthetic-storage-v1", "synthetic_pass"))
        conn.execute("SAVEPOINT live_decision_probe")
        conn.execute(direct_insert, direct_args)
        conn.execute("ROLLBACK TO SAVEPOINT live_decision_probe")
    assert pg_store.fail("tenant-a", job["job_id"], 1, lease["lease_token"],
                         "fatal", "unreviewed_output")
    with pg_store.connect() as conn, pytest.raises(errors.CheckViolation,
                                                   match="live current attempt"):
        conn.execute(direct_insert, direct_args)
    assert pg_store.list_decisions("tenant-a", job["job_id"]) == []


def test_caller_hints_cannot_launder_restricted_payload_or_read_scope(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    raw = b"restricted third party source bytes"
    row = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="tool_event", payload=raw,
        rights_ref="self_authored_fixture", classification="private",
        source_id="synthetic_self_authored")
    assert row["receipt_state"] == "received_but_withheld"
    assert row["classification"] == "restricted"
    assert row["rights_ref"] == "synthetic_denial"
    assert row["sha256"] == sha256(raw).hexdigest()
    assert row["size"] is None and row["withhold_reason"] == "policy_denied"
    assert pg_store.read_evidence("tenant-a", job["job_id"], row["evidence_id"],
                                  access="auditor") is None
    with pg_store.connect() as conn:
        authority = conn.execute(sql.SQL("""
            SELECT * FROM {}.evidence_authorizations WHERE authorization_id = %s
        """).format(sql.Identifier(pg_store.schema)), (row["authorization_id"],)).fetchone()
    assert authority["payload_sha256"] == sha256(raw).hexdigest()
    assert authority["source_id"] == "unverified"
    assert authority["retain_raw"] is False


def test_withheld_digest_permission_and_never_received_are_distinct(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    raw = b"restricted original bytes"

    def no_digest(tenant_id, source_id, intended_use, kind, payload, digest):
        return dict(tenant_id=tenant_id, source_id="restricted_source",
                    intended_use=intended_use, payload_sha256=digest,
                    rights_proof_id="synthetic_denial", rights_version="fixture-v1",
                    policy_version="synthetic-deny-v1", classification="restricted",
                    read_scope="none", retain_raw=False, retain_digest=False)

    denied_store = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root,
        evidence_policy=no_digest, principal_provider=pg_store.principal_provider)
    denied = denied_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="tool_event", payload=raw,
        rights_ref="self_authored_fixture")
    absent = denied_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="jsonl", payload=None,
        withhold_reason="not_emitted", rights_ref="self_authored_fixture")
    assert denied["receipt_state"] == "received_but_withheld"
    assert denied["sha256"] is None and denied["size"] is None
    assert denied["hash_withheld_reason"] == "digest_not_authorized"
    assert denied["withhold_reason"] == "policy_denied"
    assert absent["receipt_state"] == "not_received"
    assert absent["sha256"] is None and absent["hash_withheld_reason"] is None
    assert absent["withhold_reason"] == "not_emitted"
    with pg_store.connect() as conn:
        denied_authority = conn.execute(sql.SQL("""
            SELECT payload_sha256 FROM {}.evidence_authorizations WHERE authorization_id = %s
        """).format(sql.Identifier(pg_store.schema)), (denied["authorization_id"],)).fetchone()
        absent_authority = conn.execute(sql.SQL("""
            SELECT payload_sha256 FROM {}.evidence_authorizations WHERE authorization_id = %s
        """).format(sql.Identifier(pg_store.schema)), (absent["authorization_id"],)).fetchone()
    assert denied_authority["payload_sha256"] is None
    assert absent_authority["payload_sha256"] is None
    restarted = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root,
        principal_provider=pg_store.principal_provider)
    recovered = {row["evidence_id"]: row for row in restarted.list_evidence("tenant-a", job["job_id"])}
    assert recovered[denied["evidence_id"]]["sha256"] is None
    assert recovered[denied["evidence_id"]]["hash_withheld_reason"] == "digest_not_authorized"
    with pg_store.connect() as conn, pytest.raises(errors.CheckViolation):
        conn.execute(sql.SQL("""
            INSERT INTO {}.evidence_authorizations
                (authorization_id, tenant_id, source_id, intended_use, payload_sha256,
                 rights_proof_id, rights_version, policy_version, classification,
                 read_scope, retain_raw, retain_digest)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, false, false)
        """).format(sql.Identifier(pg_store.schema)),
            (uuid4(), "tenant-a", "restricted_source", "decision_evidence",
             sha256(raw).hexdigest(), "synthetic_denial", "fixture-v1",
             "synthetic-deny-v1", "restricted", "none"))


def test_external_reads_require_server_authenticated_principal(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    evidence = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="prompt", payload=b"synthetic private bytes",
        rights_ref="self_authored_fixture")
    unauthenticated = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root)
    assert unauthenticated.get_job("tenant-a", job["job_id"]) is None
    assert unauthenticated.list_evidence("tenant-a", job["job_id"]) == []
    assert unauthenticated.read_evidence("tenant-a", job["job_id"],
        evidence["evidence_id"], access="auditor") is None
    assert unauthenticated.get_publication("tenant-a", job["job_id"]) is None
    assert unauthenticated.read_artifact("tenant-a", job["job_id"]) is None


def test_artifact_bytes_require_artifact_scope(pg_store):
    job = submit(pg_store, stage="simulation")
    lease = pg_store.claim(60)
    artifact = b"synthetic private simulation artifact"
    digest = sha256(artifact).hexdigest()
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
                            None, artifact, digest, {"schema_version": "1"})
    metadata_only = type(pg_store)(pg_store._dsn, pg_store.schema,
        pg_store.artifact_root, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a", "scopes": ("metadata",)})
    assert metadata_only.get_publication("tenant-a", job["job_id"]) is not None
    assert metadata_only.read_artifact("tenant-a", job["job_id"]) is None
    artifact_only = type(pg_store)(pg_store._dsn, pg_store.schema,
        pg_store.artifact_root, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a", "scopes": ("artifact",)})
    assert artifact_only.get_publication("tenant-a", job["job_id"]) is None
    assert artifact_only.read_artifact("tenant-a", job["job_id"]) == artifact
    assert pg_store.read_artifact("tenant-a", job["job_id"]) == artifact


def test_metadata_scope_does_not_reveal_restricted_evidence_digest(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    raw = b"hypothetical restricted source value"
    evidence = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="tool_event", payload=raw,
        rights_ref="self_authored_fixture", classification="private")
    assert evidence["receipt_state"] == "received_but_withheld"
    assert evidence["sha256"] == sha256(raw).hexdigest()
    metadata_only = type(pg_store)(pg_store._dsn, pg_store.schema,
        pg_store.artifact_root, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a", "scopes": ("metadata",)})
    listed = metadata_only.list_evidence("tenant-a", job["job_id"])
    assert len(listed) == 1 and listed[0]["receipt_state"] == "received_but_withheld"
    assert "sha256" not in listed[0]
    assert pg_store.list_evidence("tenant-a", job["job_id"])[0]["sha256"] == sha256(raw).hexdigest()
    prepare_synthetic_invocation(pg_store, job, lease)
    assert pg_store.record_decision("tenant-a", job["job_id"], 1,
        lease["lease_token"], synthetic_decision_bytes(job), b"synthetic result")
    assert metadata_only.get_invocation("tenant-a", job["job_id"], 1) is None
    assert metadata_only.list_decisions("tenant-a", job["job_id"]) == []
    assert pg_store.get_invocation("tenant-a", job["job_id"], 1) is not None
    assert len(pg_store.list_decisions("tenant-a", job["job_id"])) == 1


def test_evidence_list_uses_one_authenticated_principal_snapshot(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="tool_event", payload=b"synthetic private source",
        rights_ref="self_authored_fixture")
    scopes = iter((("metadata",), ("auditor",)))
    alternating = type(pg_store)(pg_store._dsn, pg_store.schema,
        pg_store.artifact_root, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a", "scopes": next(scopes)})
    listed = alternating.list_evidence("tenant-a", job["job_id"])
    assert len(listed) == 1 and "sha256" not in listed[0]


def test_external_cancel_requires_authenticated_cancel_scope(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    unauthenticated = type(pg_store)(pg_store._dsn, pg_store.schema, pg_store.artifact_root)
    metadata_only = type(pg_store)(pg_store._dsn, pg_store.schema,
        pg_store.artifact_root, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-a", "scopes": ("metadata",)})
    wrong_tenant = type(pg_store)(pg_store._dsn, pg_store.schema,
        pg_store.artifact_root, principal_provider=lambda: {
            "authenticated": True, "tenant_id": "tenant-b", "scopes": ("cancel",)})
    for store in (unauthenticated, metadata_only, wrong_tenant):
        assert store.cancel("tenant-a", job["job_id"]) is False
    assert pg_store.get_job("tenant-a", job["job_id"])["cancel_requested"] is False
    assert pg_store.cancel("tenant-a", job["job_id"])
    assert pg_store.ack_cancel("tenant-a", job["job_id"], 1, lease["lease_token"])


def test_forged_report_binding_cannot_publish_even_with_matching_receipt_hash(pg_store):
    job = submit(pg_store)
    lease = pg_store.claim(60)
    prepare_synthetic_invocation(pg_store, job, lease)
    invocation = pg_store.get_invocation("tenant-a", job["job_id"], 1)
    artifact = b"synthetic artifact"
    final = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="final_output", payload=synthetic_decision_bytes(job),
        rights_ref="self_authored_fixture")
    binding = pg_store._validation_context(job, invocation, final["sha256"],
                                           sha256(artifact).hexdigest())
    forged = {"report_version": "decision-validation-v1", "passed": True,
              "validator_version": "synthetic-storage-v1", "validator_code": "synthetic_pass",
              **binding, "input_sha256": "0" * 64}
    report = pg_store.append_evidence("tenant-a", job["job_id"], 1,
        lease["lease_token"], kind="validation_report",
        payload=json.dumps(forged, sort_keys=True, separators=(",", ":")).encode(),
        rights_ref="server_validation")
    assert report["receipt_state"] == "retained"
    receipt_id, decision_id = uuid4(), uuid4()
    with pg_store.connect() as conn:
        conn.execute(sql.SQL("""
            INSERT INTO {}.validation_receipts
                (tenant_id, job_id, attempt, attempt_id, receipt_id,
                 final_evidence_id, validation_evidence_id, report_sha256,
                 output_sha256, artifact_sha256, input_sha256,
                 prompt_evidence_id, schema_evidence_id, prompt_sha256,
                 schema_sha256, prompt_version, schema_version,
                 execution_kind, cli_version, model, reasoning_effort, stage,
                 validator_version, validator_code, passed)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, true)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", job["job_id"], lease["attempt_id"], receipt_id,
             final["evidence_id"], report["evidence_id"], report["sha256"],
             final["sha256"], sha256(artifact).hexdigest(), job["input_sha256"],
             invocation["prompt_evidence_id"], invocation["schema_evidence_id"],
             invocation["prompt_sha256"], invocation["schema_sha256"],
             invocation["prompt_version"], invocation["schema_version"],
             invocation["execution_kind"], invocation["cli_version"],
             invocation["model"], invocation["reasoning_effort"],
             job["stage"], "synthetic-storage-v1", "synthetic_pass"))
        conn.execute(sql.SQL("""
            INSERT INTO {}.ai_decisions
                (tenant_id, job_id, attempt, decision_id, output_sha256,
                 artifact_sha256, final_evidence_id, validation_evidence_id, receipt_id)
            VALUES (%s, %s, 1, %s, %s, %s, %s, %s, %s)
        """).format(sql.Identifier(pg_store.schema)),
            ("tenant-a", job["job_id"], decision_id, final["sha256"],
             sha256(artifact).hexdigest(), final["evidence_id"],
             report["evidence_id"], receipt_id))
    assert pg_store.publish("tenant-a", job["job_id"], 1, lease["lease_token"],
        decision_id, artifact, sha256(artifact).hexdigest(), {"schema_version": "1"}) is None
    assert pg_store.get_publication("tenant-a", job["job_id"]) is None
