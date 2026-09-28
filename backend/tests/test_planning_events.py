"""Durable clock/signature contracts with a test key, not independent production custody."""

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
from uuid import uuid4
from types import SimpleNamespace

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.planning_events import (DOMAIN, PlanningEventStore, PlanningAuthority, DecisionContextVerifier,
                                 PlanningHold, install_planning_schema)
from app.thermal_run_store import _canonical
from app.db import install_market_hold_schema
from app.market_hold_store import MarketHoldStore
from test_thermal_run_store import run_store, raw_inputs


@pytest.fixture
def planning():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "planning_test_" + uuid4().hex
    principal = {"authenticated": True, "tenant_id": "tenant-a",
                 "scopes": ("planning_event_issue", "planning_event_read")}
    store = PlanningEventStore(dsn, schema, principal_provider=lambda: principal)
    with store.connect() as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        install_planning_schema(conn, schema)
    key = Ed25519PrivateKey.generate()
    authority = PlanningAuthority(store, "test-planning-v1", key)
    public = key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, store.read_event)
    try:
        yield store, authority, verifier, key, public, principal
    finally:
        with store.connect() as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def issue(authority, **kwargs):
    return authority.issue("tenant-a", "snapshot-a", claim_mode="ex_post_replay",
                           decision_time_kind="actual", **kwargs)


def test_actual_time_comes_from_server_event_and_replays_after_restart(planning):
    store, authority, verifier, _key, public, principal = planning
    before = datetime.now(timezone.utc)
    raw, signature = issue(authority)
    after = datetime.now(timezone.utc)
    context = json.loads(raw)
    row = store.read_event("tenant-a", context["planning_event_sha256"])
    event = json.loads(row["event_raw"])
    assert context["decision_at_utc"] == event["observed_at_utc"]
    assert before <= datetime.fromisoformat(context["decision_at_utc"].replace("Z", "+00:00")) <= after
    assert row["event_sha256"] == sha256(row["event_raw"]).hexdigest()
    fresh = PlanningEventStore(store.dsn, store.schema, principal_provider=lambda: principal)
    replay = DecisionContextVerifier({"test-planning-v1": public}, fresh.read_event)
    expected = {name: context[name] for name in
                ("authority_id", "planning_event_sha256", "decision_at_utc", "decision_time_kind")}
    assert verifier(raw, signature) == replay(raw, signature) == expected


def test_signed_planning_receipt_connects_to_existing_context_store(planning, run_store):
    _store, authority, verifier, *_ = planning
    snapshot = run_store.put_snapshot("tenant-a", *raw_inputs())
    raw, signature = authority.issue("tenant-a", snapshot, claim_mode="ex_post_replay",
                                    decision_time_kind="actual")
    context = json.loads(raw)
    run_store._context_verifier = verifier
    assert run_store.put_decision_context("tenant-a", raw, signature) == context["decision_context_id"]
    stored = run_store.get_decision_context("tenant-a", snapshot, context["decision_context_id"])
    assert stored["context_sha256"] == sha256(raw).hexdigest()
    assert stored["decision_at_utc"] == context["decision_at_utc"]


def test_actual_time_override_is_rejected_without_a_row(planning):
    store, authority, *_ = planning
    with pytest.raises(PlanningHold, match="actual_time_override_rejected"):
        issue(authority, hypothetical_at=datetime(2000, 1, 1, tzinfo=timezone.utc))
    with store.connect() as conn:
        assert conn.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(store._table())).fetchone()["n"] == 0


def test_historical_hypothesis_keeps_server_observation_and_explicit_kind(planning):
    store, authority, verifier, *_ = planning
    hypothetical = datetime(2020, 1, 2, 9, tzinfo=timezone(timedelta(hours=9)))
    raw, signature = authority.issue("tenant-a", "snapshot-a", claim_mode="ex_ante",
        decision_time_kind="hypothetical", hypothetical_at=hypothetical)
    context = json.loads(raw)
    row = store.read_event("tenant-a", context["planning_event_sha256"])
    event = json.loads(row["event_raw"])
    assert context["decision_at_utc"] == "2020-01-02T00:00:00.000000Z"
    assert context["decision_time_kind"] == "hypothetical"
    assert event["observed_at_utc"] != context["decision_at_utc"]
    assert verifier(raw, signature)["decision_time_kind"] == "hypothetical"


@pytest.mark.parametrize("when", [None, datetime(2020, 1, 1)])
def test_hypothetical_requires_an_explicit_aware_instant(planning, when):
    _, authority, *_ = planning
    with pytest.raises(PlanningHold, match="hypothetical_time_required"):
        authority.issue("tenant-a", "snapshot-a", claim_mode="ex_post_replay",
                        decision_time_kind="hypothetical", hypothetical_at=when)


@pytest.mark.parametrize("fault", ["unauthenticated", "tenant", "scope", "provider_error"])
def test_issue_and_read_require_their_own_authenticated_tenant_scope(planning, fault):
    store, authority, _, _, _, principal = planning
    raw, _ = issue(authority)
    digest = json.loads(raw)["planning_event_sha256"]
    if fault == "unauthenticated": principal["authenticated"] = False
    elif fault == "tenant": principal["tenant_id"] = "tenant-b"
    elif fault == "scope": principal["scopes"] = ()
    else:
        def broken(): raise RuntimeError("private fixture detail")
        store.principal_provider = broken
    assert store.read_event("tenant-a", digest) is None
    with pytest.raises(PlanningHold, match="planning_issue_denied"):
        issue(authority)


def test_public_read_configuration_cannot_issue_and_foreign_digest_is_hidden(planning):
    store, authority, _, _, public, _ = planning
    raw, signature = issue(authority)
    principal = {"authenticated": True, "tenant_id": "tenant-a", "scopes": ("planning_event_read",)}
    reader = PlanningEventStore(store.dsn, store.schema, principal_provider=lambda: principal)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, reader.read_event)
    assert verifier(raw, signature) is not None
    assert reader.read_event("tenant-b", json.loads(raw)["planning_event_sha256"]) is None
    with pytest.raises(PlanningHold, match="planning_issue_denied"):
        issue(PlanningAuthority(reader, "test-planning-v1", Ed25519PrivateKey.generate()))


@pytest.mark.parametrize("fault", ["signature", "unknown_key", "noncanonical", "duplicate_key", "missing_event",
    "event_bytes", "event_hash", "context_bytes", "context_hash", "tenant", "context_id", "recorded_time"])
def test_verifier_rejects_bad_signature_missing_or_changed_durable_binding(planning, fault):
    store, authority, _, _, public, _ = planning
    raw, signature = issue(authority)
    row = dict(store.read_event("tenant-a", json.loads(raw)["planning_event_sha256"]))
    keys = {"test-planning-v1": public}
    if fault == "signature": signature = "0" * 128
    elif fault == "unknown_key": keys = {"other-key": public}
    elif fault == "noncanonical": raw += b"\n"
    elif fault == "duplicate_key": raw = b'{"tenant_id":"tenant-a",' + raw[1:]
    elif fault == "missing_event": row = None
    elif fault == "event_bytes": row["event_raw"] += b"\n"
    elif fault == "event_hash": row["event_sha256"] = "a" * 64
    elif fault == "context_bytes": row["context_raw"] += b"\n"
    elif fault == "context_hash": row["context_sha256"] = "a" * 64
    elif fault == "tenant": row["tenant_id"] = "tenant-b"
    elif fault == "context_id": row["decision_context_id"] = str(uuid4())
    else: row["recorded_at"] = datetime(2000, 1, 1, tzinfo=timezone.utc)
    verifier = DecisionContextVerifier(keys, lambda tenant, digest: row)
    assert verifier(raw, signature) is None


@pytest.mark.parametrize("fault", ["actual_backdate", "kind", "snapshot", "mode", "issued_before_event"])
def test_even_a_valid_signature_requires_matching_event_time_and_scope(planning, fault):
    store, authority, _, key, public, _ = planning
    raw, _ = issue(authority)
    context = json.loads(raw)
    row = dict(store.read_event("tenant-a", context["planning_event_sha256"]))
    if fault == "actual_backdate": context["decision_at_utc"] = "2000-01-01T00:00:00.000000Z"
    elif fault == "kind": context["decision_time_kind"] = "hypothetical"
    elif fault == "snapshot": context["snapshot_id"] = "snapshot-b"
    elif fault == "mode": context["claim_mode"] = "ex_ante"
    else: context["issued_at_utc"] = "2000-01-01T00:00:00.000000Z"
    changed = _canonical(context)
    signature = key.sign(DOMAIN + changed).hex()
    row.update(context_raw=changed, context_sha256=sha256(changed).hexdigest(), context_signature=signature)
    verifier = DecisionContextVerifier({"test-planning-v1": public}, lambda tenant, digest: row)
    assert verifier(changed, signature) is None


@pytest.mark.parametrize("mutation", ["UPDATE", "DELETE"])
def test_database_blocks_event_replacement_or_deletion(planning, mutation):
    store, authority, *_ = planning
    issue(authority)
    query = (sql.SQL("UPDATE {} SET context_signature=%s").format(store._table()) if mutation == "UPDATE"
             else sql.SQL("DELETE FROM {}").format(store._table()))
    with store.connect() as conn, pytest.raises(errors.RaiseException, match="immutable planning event"):
        conn.execute(query, ("0" * 128,) if mutation == "UPDATE" else ())
    with store.connect() as conn:
        assert conn.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(store._table())).fetchone()["n"] == 1


@pytest.mark.parametrize("fault", ["issued", "recorded"])
def test_clock_reversal_rolls_back_the_complete_receipt(planning, monkeypatch, fault):
    store, authority, *_ = planning
    connect = store.connect
    future = datetime.now(timezone.utc) + timedelta(minutes=1)
    times = [future, future - timedelta(seconds=1) if fault == "issued" else future]
    @contextmanager
    def controlled_clock():
        with connect() as conn:
            def execute(query, *args):
                if type(query) is str and query == "SELECT clock_timestamp() AS now":
                    instant = times.pop(0)
                    return SimpleNamespace(fetchone=lambda: {"now": instant})
                return conn.execute(query, *args)
            yield SimpleNamespace(execute=execute)
    monkeypatch.setattr(store, "connect", controlled_clock)
    with pytest.raises(PlanningHold, match="planning_clock_reversed"):
        issue(authority)
    with connect() as conn:
        assert conn.execute(sql.SQL("SELECT count(*) AS n FROM {}").format(store._table())).fetchone()["n"] == 0


def test_database_hash_constraint_rejects_changed_event_bytes(planning):
    store, authority, *_ = planning
    raw, _ = issue(authority)
    row = store.read_event("tenant-a", json.loads(raw)["planning_event_sha256"])
    with store.connect() as conn, pytest.raises(errors.CheckViolation):
        conn.execute(sql.SQL('''INSERT INTO {} (tenant_id, decision_context_id, event_raw, event_sha256,
            context_raw, context_sha256, context_signature) VALUES (%s,%s,%s,%s,%s,%s,%s)
        ''').format(store._table()), ("tenant-a", str(uuid4()), row["event_raw"] + b"\n", "a" * 64,
                                    row["context_raw"], row["context_sha256"], row["context_signature"]))


def test_real_planning_record_binds_market_unavailability_without_a_market_snapshot(planning, run_store):
    _, authority, verifier, *_ = planning
    snapshot = run_store.put_snapshot("tenant-a", *raw_inputs())
    raw, signature = authority.issue("tenant-a", snapshot, claim_mode="ex_post_replay", decision_time_kind="actual")
    context = json.loads(raw)
    run_store._context_verifier = verifier
    context_id = run_store.put_decision_context("tenant-a", raw, signature)
    with run_store.connect() as conn:
        install_market_hold_schema(conn, run_store.schema)
    scope = {"tenant_id": "tenant-a", "snapshot_id": snapshot, "decision_context_id": context_id,
             "candidate_ids": ["candidate-a"], "scope_version": "fixture-v1",
             "sales_start_utc": "2026-10-01T00:00:00Z", "sales_end_utc": "2026-11-01T00:00:00Z"}
    market = MarketHoldStore(run_store.dsn, run_store.schema, context_store=run_store,
        scope_resolver=lambda *_: scope, signing_key=b"synthetic-market-key-32-bytes-long!",
        principal_provider=lambda: {"authenticated": True, "tenant_id": "tenant-a",
            "scopes": ("market_hold_issue", "market_hold_context_read", "market_hold_read")})
    report = market.issue_not_evaluated("tenant-a", snapshot, context_id)
    assert report["status"] == "hold" and report["reasons"] == ["market_g0_not_evaluated"]
    assert report["decision_at_utc"] == context["decision_at_utc"]
    assert report["context_sha256"] == sha256(raw).hexdigest()
    assert market.issue_not_evaluated("tenant-a", snapshot, context_id) == report
