"""Market unavailability is a server-owned record, not a CLI or client verdict."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import install_market_hold_schema
from app.market import UnavailableMarketContext, resolve_market_context
from app.market_hold_store import MarketHoldStore
from app.thermal_run_store import (ThermalRunStore, install_thermal_run_schema,
                                   snapshot_id_for)


CONTEXT_KEY = b"synthetic-market-context-key-32bytes"
HOLD_KEY = b"synthetic-market-hold-key-32bytes!!"
D = "2026-09-27T09:04:30Z"
SNAPSHOT_RAWS = (b'{"synthetic":"manifest"}', b'{"synthetic":"weather"}',
                 b'{"synthetic":"thermal"}')
SNAPSHOT_ID = snapshot_id_for(*SNAPSHOT_RAWS)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode()


def context_verifier(raw, signature):
    expected = hmac.new(CONTEXT_KEY, b"decision-context-v1\0" + raw,
                        sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    value = json.loads(raw)
    return {key: value[key] for key in
            ("authority_id", "planning_event_sha256", "decision_at_utc",
             "decision_time_kind")}


@pytest.fixture
def setup():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "market_hold_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(dsn) as conn:
            install_thermal_run_schema(conn, schema)
            install_market_hold_schema(conn, schema)
        principal = {"authenticated": True, "tenant_id": "tenant-a",
                     "scopes": {"market_hold_issue", "market_hold_context_read",
                                "market_hold_read"}}
        context_service = {"authenticated": True, "tenant_id": "tenant-a",
                           "scopes": {"decision_context_write", "decision_context_read",
                                      "thermal_snapshot_write"}}
        scope = {"tenant_id": "tenant-a", "snapshot_id": SNAPSHOT_ID,
                 "decision_context_id": "context-a", "candidate_ids": ["crop-a"],
                 "sales_start_utc": "2026-10-01T00:00:00Z",
                 "sales_end_utc": "2026-11-01T00:00:00Z", "scope_version": "v1"}
        context_store = ThermalRunStore(dsn, schema, gate_key=b"synthetic-gate-key-32-bytes-long!",
            release_verifier=lambda *_: None, principal_provider=lambda: context_service,
            context_verifier=context_verifier)
        assert context_store.put_snapshot("tenant-a", *SNAPSHOT_RAWS) == SNAPSHOT_ID
        document = {"context_version": "decision-context-v1", "tenant_id": "tenant-a",
                    "snapshot_id": SNAPSHOT_ID, "decision_context_id": "context-a",
                    "decision_at_utc": D, "claim_mode": "ex_post_replay",
                    "decision_time_kind": "hypothetical", "authority_id": "test-authority",
                    "issued_at_utc": datetime.now(timezone.utc).isoformat(
                        timespec="microseconds").replace("+00:00", "Z"),
                    "planning_event_sha256": sha256(b"synthetic planning event").hexdigest()}
        raw = canonical(document)
        signature = hmac.new(CONTEXT_KEY, b"decision-context-v1\0" + raw,
                             sha256).hexdigest()
        context_store.put_decision_context("tenant-a", raw, signature)

        def store():
            return MarketHoldStore(dsn, schema, context_store=context_store,
                scope_resolver=lambda *_: dict(scope), principal_provider=lambda: principal,
                signing_key=HOLD_KEY)

        yield store, principal, scope, dsn, schema
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_not_evaluated_report_is_immutable_and_resolves_market_context(setup):
    store, principal, scope, dsn, schema = setup
    first = store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")
    assert first["evaluation_status"] == "not_evaluated"
    assert first["reasons"] == ["market_g0_not_evaluated"]
    assert first["decision_at_utc"] == D
    assert first["claim_mode"] == "ex_post_replay"
    assert store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a") == first
    assert store().get_public_report("tenant-a", first["hold_report_id"]) == {
        "hold_report_id": first["hold_report_id"], "status": "hold",
        "reasons": ["market_g0_not_evaluated"],
        "missing_evidence": first["missing_evidence"]}
    market = UnavailableMarketContext(kind="unavailable", hold_report_id=first["hold_report_id"])
    assert resolve_market_context(market, tenant_id="tenant-a",
        decision_at=datetime.fromisoformat(D.replace("Z", "+00:00")),
        repository=store(), decision_context_id="context-a",
        input_snapshot_id=SNAPSHOT_ID, claim_mode="ex_post_replay",
        decision_time_kind="hypothetical") == market
    with pytest.raises(ValueError, match="decision context differs"):
        resolve_market_context(market, tenant_id="tenant-a",
            decision_at=datetime.fromisoformat(D.replace("Z", "+00:00")),
            repository=store())
    principal["scopes"].remove("market_hold_context_read")
    assert store().get_market_hold_report(first["hold_report_id"]) is None
    assert store().get_public_report("tenant-a", first["hold_report_id"])["status"] == "hold"
    with psycopg.connect(dsn) as conn, pytest.raises(psycopg.Error):
        conn.execute(sql.SQL("UPDATE {}.market_hold_reports SET payload_raw=%s").format(
            sql.Identifier(schema)), (b"{}",))


def test_retry_concurrency_and_new_scope_version_create_distinct_reports(setup):
    store, _, scope, _, _ = setup
    with ThreadPoolExecutor(max_workers=5) as pool:
        rows = list(pool.map(lambda _: store().issue_not_evaluated(
            "tenant-a", SNAPSHOT_ID, "context-a"), range(10)))
    assert len({row["hold_report_id"] for row in rows}) == 1
    scope["scope_version"] = "v2"
    newer = store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")
    assert newer["hold_report_id"] != rows[0]["hold_report_id"]
    old_market = UnavailableMarketContext(kind="unavailable",
        hold_report_id=rows[0]["hold_report_id"])
    with pytest.raises(ValueError, match="scope changed"):
        store().get_market_hold_report(rows[0]["hold_report_id"])
    with pytest.raises(ValueError):
        resolve_market_context(old_market, tenant_id="tenant-a",
            decision_at=datetime.fromisoformat(D.replace("Z", "+00:00")),
            repository=store(), decision_context_id="context-a",
            input_snapshot_id=SNAPSHOT_ID, claim_mode="ex_post_replay",
            decision_time_kind="hypothetical")
    assert store().get_public_report("tenant-a", rows[0]["hold_report_id"])["status"] == "hold"


def test_foreign_and_context_substitution_fail_without_raw_disclosure(setup):
    store, principal, _, _, _ = setup
    report = store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")
    principal["tenant_id"] = "tenant-b"
    assert store().get_public_report("tenant-b", report["hold_report_id"]) is None
    assert store().get_market_hold_report(report["hold_report_id"]) is None
    principal["tenant_id"] = "tenant-a"
    market = UnavailableMarketContext(kind="unavailable", hold_report_id=report["hold_report_id"])
    for changes in ({"decision_context_id": "other-context"},
                    {"claim_mode": "ex_ante"},
                    {"decision_time_kind": "actual"},
                    {"decision_at": datetime(2026, 9, 27, 9, 5, tzinfo=timezone.utc)}):
        request = {"tenant_id": "tenant-a",
                   "decision_at": datetime.fromisoformat(D.replace("Z", "+00:00")),
                   "repository": store(), "decision_context_id": "context-a",
                   "input_snapshot_id": SNAPSHOT_ID, "claim_mode": "ex_post_replay",
                   "decision_time_kind": "hypothetical"}
        request.update(changes)
        with pytest.raises(ValueError):
            resolve_market_context(market, **request)
    principal["scopes"].remove("market_hold_issue")
    with pytest.raises(ValueError):
        store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")


def test_signature_rejects_owner_tamper_after_reconnect(setup):
    store, _, _, dsn, schema = setup
    report = store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")
    assert store().get_public_report("tenant-a", report["hold_report_id"])
    altered = dict(report)
    altered["evaluated_at_utc"] = "2026-09-27T10:00:00Z"
    raw = canonical(altered)
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL("ALTER TABLE {}.market_hold_reports DISABLE TRIGGER USER").format(
            sql.Identifier(schema)))
        conn.execute(sql.SQL("""
            UPDATE {}.market_hold_reports SET payload_raw=%s, payload_sha256=%s
            WHERE tenant_id=%s AND hold_report_id=%s
        """).format(sql.Identifier(schema)),
            (raw, sha256(raw).hexdigest(), "tenant-a", report["hold_report_id"]))
    with pytest.raises(ValueError, match="integrity"):
        store().get_public_report("tenant-a", report["hold_report_id"])


def test_signed_context_without_input_snapshot_cannot_issue_report(setup):
    store, _, scope, dsn, schema = setup
    orphan = {"context_version": "decision-context-v1", "tenant_id": "tenant-a",
              "snapshot_id": "missing-snapshot", "decision_context_id": "orphan-context",
              "decision_at_utc": D, "claim_mode": "ex_post_replay",
              "decision_time_kind": "hypothetical", "authority_id": "test-authority",
              "issued_at_utc": datetime.now(timezone.utc).isoformat(
                  timespec="microseconds").replace("+00:00", "Z"),
              "planning_event_sha256": sha256(b"orphan planning event").hexdigest()}
    raw = canonical(orphan)
    signature = hmac.new(CONTEXT_KEY, b"decision-context-v1\0" + raw,
                         sha256).hexdigest()
    with psycopg.connect(dsn) as conn:
        conn.execute(sql.SQL("""
            INSERT INTO {}.decision_contexts (tenant_id, decision_context_id,
                snapshot_id, context_raw, context_sha256, context_signature, authority_id)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """).format(sql.Identifier(schema)),
            ("tenant-a", "orphan-context", "missing-snapshot", raw,
             sha256(raw).hexdigest(), signature, "test-authority"))
    scope["snapshot_id"] = "missing-snapshot"
    scope["decision_context_id"] = "orphan-context"
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        store().issue_not_evaluated("tenant-a", "missing-snapshot", "orphan-context")


def test_request_role_cannot_read_raw_or_insert_market_hold(setup):
    store, _, _, dsn, schema = setup
    report = store().issue_not_evaluated("tenant-a", SNAPSHOT_ID, "context-a")
    role = "market_request_" + uuid4().hex
    created = False
    try:
        with psycopg.connect(dsn) as conn:
            owner = conn.execute("SELECT current_user").fetchone()[0]
            try:
                conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(role)))
                conn.execute(sql.SQL("GRANT {} TO {}").format(
                    sql.Identifier(role), sql.Identifier(owner)))
            except psycopg.errors.InsufficientPrivilege:
                pytest.skip("test server does not permit isolated role creation")
            created = True
            conn.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                sql.Identifier(schema), sql.Identifier(role)))
        with psycopg.connect(dsn) as conn:
            conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            assert conn.execute("SELECT has_table_privilege(current_user, %s, 'SELECT')",
                (f"{schema}.market_hold_reports",)).fetchone()[0] is False
            assert conn.execute("SELECT has_table_privilege(current_user, %s, 'INSERT')",
                (f"{schema}.market_hold_reports",)).fetchone()[0] is False
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(sql.SQL("SELECT payload_raw FROM {}.market_hold_reports WHERE hold_report_id=%s").format(
                    sql.Identifier(schema)), (report["hold_report_id"],))
        with psycopg.connect(dsn) as conn:
            conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(role)))
            with pytest.raises(psycopg.errors.InsufficientPrivilege):
                conn.execute(sql.SQL("INSERT INTO {}.market_hold_reports SELECT * FROM {}.market_hold_reports WHERE false").format(
                    sql.Identifier(schema), sql.Identifier(schema)))
    finally:
        if created:
            with psycopg.connect(dsn) as conn:
                conn.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(role)))
                conn.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(role)))
