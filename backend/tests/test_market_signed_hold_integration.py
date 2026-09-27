"""A signed Market hold report reaches the actual joint market and ledger path."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import hmac
import os
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db import install_market_hold_schema
from app.break_even_store import BreakEvenStore, install_break_even_store_schema
from app.economic_contracts import EconomicScenario
from app.economics import canonical_scenario_sha256
from app.market_candidate_store import MarketCandidateStore, install_market_candidate_schema
from app.market_hold_store import MarketHoldStore
from app.market_scenario import MarketScenarioService
from app.thermal_run_store import ThermalRunStore, install_thermal_run_schema, snapshot_id_for
from test_economics import DECISION
from test_market_hold_store import (CONTEXT_KEY, HOLD_KEY, SNAPSHOT_RAWS,
                                    canonical, context_verifier)
from test_market_scenario import case, digest, repin_shock
from test_break_even import trial_plan


@pytest.fixture
def signed_market():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "market_signed_hold_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(dsn) as conn:
            install_thermal_run_schema(conn, schema)
            install_market_hold_schema(conn, schema)
            install_market_candidate_schema(conn, schema)
            install_break_even_store_schema(conn, schema)
        principal = {"authenticated": True, "tenant_id": "tenant-1",
                     "scopes": {"market_hold_issue", "market_hold_context_read",
                                "market_candidate_read", "market_candidate_write",
                                "break_even_read", "break_even_write"}}
        context_principal = {"authenticated": True, "tenant_id": "tenant-1",
                             "scopes": {"decision_context_write", "decision_context_read",
                                        "thermal_snapshot_write"}}
        snapshot_id = snapshot_id_for(*SNAPSHOT_RAWS)
        scope = {"tenant_id": "tenant-1", "snapshot_id": snapshot_id,
                 "decision_context_id": "context-1", "candidate_ids": ["crop-1"],
                 "sales_start_utc": "2026-10-01T00:00:00Z",
                 "sales_end_utc": "2026-12-01T00:00:00Z", "scope_version": "v1"}
        context_store = ThermalRunStore(dsn, schema,
            gate_key=b"synthetic-gate-key-32-bytes-long!",
            release_verifier=lambda *_: None,
            principal_provider=lambda: context_principal,
            context_verifier=context_verifier)
        assert context_store.put_snapshot("tenant-1", *SNAPSHOT_RAWS) == snapshot_id
        document = {"context_version": "decision-context-v1", "tenant_id": "tenant-1",
                    "snapshot_id": snapshot_id, "decision_context_id": "context-1",
                    "decision_at_utc": DECISION.isoformat().replace("+00:00", "Z"),
                    "claim_mode": "ex_post_replay", "decision_time_kind": "hypothetical",
                    "authority_id": "test-authority", "issued_at_utc": datetime.now(
                        timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                    "planning_event_sha256": sha256(b"self-authored plan").hexdigest()}
        raw = canonical(document)
        signature = hmac.new(CONTEXT_KEY, b"decision-context-v1\0" + raw,
                             sha256).hexdigest()
        context_store.put_decision_context("tenant-1", raw, signature)

        def hold_store():
            return MarketHoldStore(dsn, schema, context_store=context_store,
                scope_resolver=lambda *_: dict(scope), principal_provider=lambda: principal,
                signing_key=HOLD_KEY)

        issued = hold_store().issue_not_evaluated("tenant-1", snapshot_id, "context-1")
        market = {"kind": "unavailable", "hold_report_id": issued["hold_report_id"]}
        source, request = case()
        baseline_data = deepcopy(source.scenarios[("scenario-1", "r1")])
        baseline_data["market_context"] = market
        baseline_data["scenario_market_context"] = market
        baseline = EconomicScenario.model_validate(baseline_data)
        baseline_sha = canonical_scenario_sha256(baseline)
        source.scenarios[("scenario-1", "r1")] = baseline.model_dump(mode="python")
        source.pins[("scenario-1", "r1")].update(
            payload_sha256=baseline_sha, immutable_job_input_sha256=baseline_sha)
        shock = source.shocks[("joint-1", "r1")]
        shock["baseline_sha256"] = baseline_sha
        repin_shock(source)
        request["baseline"]["sha256"] = baseline_sha
        request["shock"]["sha256"] = digest(shock)
        request["market_context"] = market

        class SignedSource:
            def get_market_hold_report(self, report_id):
                return hold_store().get_market_hold_report(report_id)

            def get_decision_context(self, tenant, snapshot, context_id):
                return hold_store().get_decision_context(tenant, snapshot, context_id)

            def __getattr__(self, name):
                return getattr(source, name)

        trusted = SignedSource()

        def candidate_store():
            return MarketCandidateStore(dsn, schema, trusted,
                principal_provider=lambda: principal)

        yield candidate_store, source, request, principal, scope
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_signed_hold_survives_candidate_pin_and_replay(signed_market):
    factory, _, request, principal, scope = signed_market
    candidate = MarketScenarioService(factory()).build_candidate(request, "tenant-1")
    result = MarketScenarioService(factory()).calculate_pinned(
        candidate.scenario_id, candidate.revision, "tenant-1")
    assert result.candidate_id == candidate.candidate_id
    assert result.assessment_status == "hold"
    assert result.calculation_status == "conditional_user_assumption"
    principal["scopes"].remove("market_hold_context_read")
    with pytest.raises(ValueError):
        MarketScenarioService(factory()).calculate_pinned(
            candidate.scenario_id, candidate.revision, "tenant-1")
    principal["scopes"].add("market_hold_context_read")
    scope["scope_version"] = "v2"
    with pytest.raises(ValueError):
        MarketScenarioService(factory()).calculate_pinned(
            candidate.scenario_id, candidate.revision, "tenant-1")


def test_signed_hold_replays_three_persisted_break_even_trials(signed_market):
    candidate_factory, source, market_request, principal, scope = signed_market
    candidate_store, request = trial_plan([20, 26, 32],
        candidate_repository_factory=lambda _: candidate_factory(),
        case_factory=lambda: (source, market_request))
    assert len(source.scenarios) == 1

    def plan_store():
        return BreakEvenStore(candidate_store.dsn, candidate_store.schema,
            candidate_factory(), principal_provider=lambda: principal)

    pinned = plan_store().pin_break_even_plan(request, source.break_even_plan)
    assert pinned.status == "zero_on_grid"
    assert pinned.assessment_status == "hold"
    assert tuple(str(item.target_value) for item in pinned.trials) == ("-54", "0", "54")
    assert plan_store().get_break_even_result(request["plan_id"]) == pinned
    with candidate_store.connect() as conn:
        candidate_count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {}")
            .format(candidate_store._table("market_candidate_pins"))).fetchone()["n"]
        plan_count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {}")
            .format(plan_store()._table())).fetchone()["n"]
    assert (candidate_count, plan_count) == (3, 1)
    scope["scope_version"] = "v2"
    with pytest.raises(ValueError):
        plan_store().get_break_even_result(request["plan_id"])
