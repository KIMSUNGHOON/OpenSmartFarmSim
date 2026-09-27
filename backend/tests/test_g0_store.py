"""Durable G0 contract checks against a disposable PostgreSQL schema."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.gates import G0Policy, CheckRequirement, RequestAllowance, VariableRequirement
from app.provenance import ProjectCheck, RequestDetail, Right, SourceRecord, SourceScope, Variable
from app.g0_store import G0Store, ReviewProof, _scope_digest, install_g0_schema
from app.g0_authority import G0Authority

RAW = b"self-authored bytes for a software contract test"
SCOPE = SourceScope(provider="fixture-provider", product_id="hourly", product_version="v1",
                    source_url="https://example.org/hourly", station_or_grid_id="station-1")


def source(raw=RAW, **changes):
    now = datetime.now(timezone.utc)
    data = dict(schema_version="1", scope=SCOPE, revision_id="revision-1",
        request_details=(RequestDetail(name="station", value="station-1"),),
        observed_at=now - timedelta(days=3), published_at=now - timedelta(days=2),
        available_at=now - timedelta(days=2), retrieved_at=now - timedelta(days=1),
        valid_from=now - timedelta(days=3), valid_to=now + timedelta(days=3),
        variables=(Variable(name="solar", original_unit="MJ/m2", time_semantics="interval_total",
            interval_start=now - timedelta(days=3), interval_end=now - timedelta(days=2),
            provider_qc_status="not_supplied", provider_qc_value=None),),
        project_checks=(ProjectCheck(variable="solar", name="range", version="v1",
            status="passed", evidence_id="check-1", reviewer="reviewer-1"),),
        rights=(Right(action="display", status="allowed", evidence_id="right-1",
            reviewer="reviewer-1"),), raw_sha256=sha256(raw).hexdigest(),
        synthetic=False, synthetic_author=None, synthetic_method=None,
        source_reviewer="reviewer-1", source_evidence_id="source-1")
    data.update(changes)
    draft = SourceRecord.model_construct(record_id="placeholder", **data)
    return SourceRecord(record_id=draft.content_id(), **data)


def policy(**changes):
    now = datetime.now(timezone.utc)
    data = dict(schema_version="1", policy_id="policy-1", policy_version="v1", scope=SCOPE,
        intended_action="display", intended_use="internal-preview",
        required_variables=(VariableRequirement(name="solar", original_unit="MJ/m2",
            time_semantics="interval_total"),),
        required_checks=(CheckRequirement(variable="solar", name="range", version="v1"),),
        required_rights=("display",), required_times=("observed_at", "published_at", "available_at"),
        allowed_request_details=(RequestAllowance(name="station", values=("station-1",)),),
        reviewer="caller-claim", authenticated=True, approved=True,
        approved_at=now - timedelta(days=1), available_at=now - timedelta(days=1),
        valid_from=now - timedelta(days=1), valid_to=now + timedelta(days=3), revoked_at=None)
    data.update(changes)
    draft = G0Policy.model_construct(policy_digest="0" * 64, **data)
    return G0Policy(policy_digest=draft.content_digest(), **data)


def fake_review(record, kind, *, use=None, conditions_met=None, **changes):
    """Self-authored test wiring; these bytes establish no real source QC or rights."""
    evidence_id = {"source": "source-1", "check": "check-1", "right": "right-1"}[kind]
    content = f"synthetic {kind} review for software testing".encode()
    data = dict(tenant_id="tenant-a", kind=kind, evidence_id=evidence_id,
        record_id=record.record_id, scope=record.scope, revision_id=record.revision_id,
        raw_sha256=record.raw_sha256, reviewer="reviewer-1",
        evidence_content=content, content_sha256=sha256(content).hexdigest())
    if kind == "check":
        data.update(variable="solar", check_name="range", check_version="v1")
    if kind == "right":
        data.update(action="display", use=use or "internal-preview",
            conditions_met=True if conditions_met is None else conditions_met)
    data.update(changes)
    return ReviewProof(**data)


@pytest.fixture
def env():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "g0_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(dsn) as conn:
            install_g0_schema(conn, schema)
        raw = {}
        proofs = {}
        principal = {"authenticated": True, "tenant_id": "tenant-a", "subject": "reviewer-1",
                     "scopes": {"g0_ingest", "g0_policy", "g0_source", "g0_check", "g0_right",
                                "g0_evaluate", "g0_revoke"}}
        def build():
            return G0Store(dsn, schema, signing_key=b"synthetic-test-key-32-bytes-long!",
                raw_reader=lambda tenant, digest: raw.get((tenant, digest)),
                principal_provider=lambda: principal.copy(),
                review_resolver=lambda tenant, evidence_id: proofs.get((tenant, evidence_id)))
        build.proofs = proofs
        yield build, raw, principal, schema, dsn
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def approved(env, *, tenant="tenant-a", record=None):
    build, raw, principal, _, _ = env
    record = record or source()
    raw[(tenant, record.raw_sha256)] = RAW
    authority = G0Authority(build())
    authority.register_record(tenant, record)
    authority.approve_policy(tenant, policy())
    for kind in ("source", "check", "right"):
        proof = fake_review(record, kind)
        build.proofs[(tenant, proof.evidence_id)] = proof
    deadline = datetime.now(timezone.utc) + timedelta(days=2)
    authority.approve_source(tenant, record.record_id, valid_to=deadline)
    authority.approve_check(tenant, record.record_id, "solar", "range", valid_to=deadline)
    authority.approve_right(tenant, record.record_id, "display", "internal-preview",
                            valid_to=deadline)
    return authority, record


def test_restart_and_per_purpose_decision_are_durable(env):
    authority, record = approved(env)
    first = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert first["status"] == "pass"
    assert first["approved_policy_digest"] == first["gate"]["policy_digest"]
    with authority.store.connect() as conn:
        row = conn.execute(sql.SQL("""
            SELECT payload FROM {}.g0_entries
            WHERE tenant_id = %s AND kind = 'right' AND entry_id = %s
        """).format(sql.Identifier(env[3])), ("tenant-a", "right-1")).fetchone()
    stored = json.loads(row["payload"])
    assert stored["proof_binding"]["content_sha256"] == env[0].proofs[
        ("tenant-a", "right-1")].content_sha256
    assert stored["proof_binding"]["use"] == "internal-preview"
    assert "evidence_content" not in row["payload"]
    restarted = G0Authority(env[0]())
    assert restarted.get_decision("tenant-a", first["decision_id"]) == first
    wrong_key = G0Authority(G0Store(env[4], env[3], signing_key=b"wrong-test-key-32-bytes-long!!!!",
        raw_reader=lambda tenant, digest: env[1].get((tenant, digest)),
        principal_provider=lambda: env[2].copy(),
        review_resolver=lambda tenant, evidence_id: env[0].proofs.get((tenant, evidence_id))))
    with pytest.raises(ValueError):
        wrong_key.get_decision("tenant-a", first["decision_id"])
    wrong_use = restarted.evaluate("tenant-a", record.record_id, "display", "public-site")
    assert wrong_use["status"] == "hold"
    assert "policy_missing" in wrong_use["reasons"]
    restarted.approve_policy("tenant-a", policy(policy_id="policy-public",
        policy_version="v1-public", intended_use="public-site"))
    no_right = restarted.evaluate("tenant-a", record.record_id, "display", "public-site")
    assert no_right["status"] == "hold"
    assert "right_evidence_mismatch" in no_right["reasons"]


def test_parallel_decisions_and_policy_generation(env):
    authority, record = approved(env)
    with ThreadPoolExecutor(max_workers=6) as pool:
        decisions = list(pool.map(lambda _: G0Authority(env[0]()).evaluate(
            "tenant-a", record.record_id, "display", "internal-preview"), range(12)))
    assert len({row["decision_id"] for row in decisions}) == 12
    assert all(row["status"] == "pass" for row in decisions)
    newer = policy(policy_id="policy-2", policy_version="v2", required_rights=("display", "store"))
    authority.approve_policy("tenant-a", newer)
    stale = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert stale["status"] == "hold"
    assert "right_missing" in stale["reasons"]
    assert authority.get_decision("tenant-a", decisions[0]["decision_id"])["status"] == "pass"
    with ThreadPoolExecutor(max_workers=5) as pool:
        list(pool.map(lambda number: G0Authority(env[0]()).approve_policy("tenant-a",
            policy(policy_id=f"parallel-{number}", policy_version=f"parallel-v{number}")), range(5)))
    with authority.store.connect() as conn:
        generations = conn.execute(sql.SQL("""
            SELECT generation FROM {}.g0_entries WHERE tenant_id = 'tenant-a'
                AND kind = 'policy' ORDER BY generation
        """).format(sql.Identifier(env[3]))).fetchall()
    assert [row["generation"] for row in generations] == list(range(1, 8))


def test_rows_are_immutable_and_tamper_is_detected(env):
    authority, record = approved(env)
    decision = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    _, _, _, schema, dsn = env
    with psycopg.connect(dsn) as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("UPDATE {}.g0_entries SET payload = payload WHERE entry_id = %s")
                     .format(sql.Identifier(schema)), (record.record_id,))
    with psycopg.connect(dsn) as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("DELETE FROM {}.g0_entries WHERE entry_id = %s")
                     .format(sql.Identifier(schema)), (record.record_id,))
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL("ALTER TABLE {}.g0_entries DISABLE TRIGGER USER")
                     .format(sql.Identifier(schema)))
        conn.execute(sql.SQL("""
            UPDATE {}.g0_entries SET payload = %s, payload_sha256 = %s
            WHERE kind = 'record' AND entry_id = %s
        """).format(sql.Identifier(schema)),
            ('{}', sha256(b'{}').hexdigest(), record.record_id))
        conn.execute(sql.SQL("ALTER TABLE {}.g0_entries ENABLE TRIGGER USER")
                     .format(sql.Identifier(schema)))
    tampered = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert tampered["status"] == "hold"
    assert "repository_error" in tampered["reasons"]
    assert authority.get_decision("tenant-a", decision["decision_id"]) == decision


def test_unsigned_policy_row_cannot_authorize(env):
    authority, record = approved(env)
    forged = policy(policy_id="forged-policy", policy_version="forged-v2")
    payload = json.dumps(forged.model_dump(mode="json"), sort_keys=True,
                         separators=(",", ":"), ensure_ascii=False)
    with authority.store.connect() as conn:
        conn.execute(sql.SQL("""
            INSERT INTO {}.g0_entries (tenant_id, kind, entry_id, scope_digest, action,
                intended_use, generation, payload, payload_sha256, signature, recorded_at)
            VALUES (%s, 'policy', %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """).format(sql.Identifier(env[3])), (
            "tenant-a", forged.policy_id, _scope_digest(forged.scope),
            forged.intended_action, forged.intended_use, 2, payload,
            sha256(payload.encode()).hexdigest(), "0" * 64, datetime.now(timezone.utc)))
    result = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert result["status"] == "hold" and "repository_error" in result["reasons"]


def test_concurrent_revocation_serializes_with_decisions(env):
    authority, record = approved(env)

    def decide(_):
        return G0Authority(env[0]()).evaluate(
            "tenant-a", record.record_id, "display", "internal-preview")

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(decide, number) for number in range(12)]
        revoked = pool.submit(authority.revoke_evidence, "tenant-a", "right-1")
        decisions = [future.result() for future in futures]
        revoked.result()
    assert len({item["decision_id"] for item in decisions}) == len(decisions)
    assert {item["status"] for item in decisions} <= {"pass", "hold"}
    assert all(authority.get_decision("tenant-a", item["decision_id"]) == item
               for item in decisions)
    after = authority.evaluate("tenant-a", record.record_id, "display", "internal-preview")
    assert after["status"] == "hold"
    assert "right_evidence_revoked" in after["reasons"]
