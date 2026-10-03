"""PostgreSQL pins for a self-authored conditional market candidate."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import os
from pathlib import Path
import sys
from uuid import uuid4

import psycopg
from psycopg import errors, sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.market_candidate_store import (MarketCandidateStore,
                                        install_market_candidate_schema)
from app.economic_contracts import EconomicScenario
from app.economics import canonical_scenario_sha256
from app.market_scenario import MarketScenarioService
from test_market_scenario import case, digest


@pytest.fixture
def saved_market():
    dsn = os.environ.get("OSSF_TEST_PG_DSN")
    if not dsn:
        pytest.skip("OSSF_TEST_PG_DSN is unset")
    schema = "market_candidate_test_" + uuid4().hex
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        with psycopg.connect(dsn) as conn:
            install_market_candidate_schema(conn, schema)
        source, request = case()
        principal = {"authenticated": True, "tenant_id": "tenant-1",
                     "scopes": {"market_candidate_read", "market_candidate_write"}}
        def store():
            return MarketCandidateStore(dsn, schema, source,
                                        principal_provider=lambda: principal)
        yield store, source, request, principal
    finally:
        with psycopg.connect(dsn, autocommit=True) as conn:
            conn.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))


def test_candidate_and_numeric_revisions_survive_new_store_instance(saved_market):
    factory, source, request, _ = saved_market
    first_store = factory()
    candidate = MarketScenarioService(first_store).build_candidate(request, "tenant-1")
    assert candidate.status == "pinned"
    assert (candidate.scenario_id, candidate.revision) not in source.scenarios
    resumed = factory()
    result = MarketScenarioService(resumed).calculate_pinned(
        candidate.scenario_id, candidate.revision, "tenant-1")
    assert result.assessment_status == "hold"
    assert result.calculation_status == "conditional_user_assumption"
    assert result.economic_scenario_sha256 == candidate.economic_scenario_sha256
    assert MarketScenarioService(resumed).build_candidate(request, "tenant-1") == candidate
    with resumed.connect() as conn:
        pin_count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {}")
            .format(resumed._table("market_candidate_pins"))).fetchone()["n"]
        input_count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {}")
            .format(resumed._table("market_candidate_inputs"))).fetchone()["n"]
    assert pin_count == 1 and input_count > 0


def test_candidate_pin_is_atomic_and_immutable(saved_market):
    factory, _, request, _ = saved_market
    store = factory()
    candidate = MarketScenarioService(store).build_candidate(request, "tenant-1")
    with store.connect() as conn:
        with pytest.raises(errors.RaiseException, match="immutable"):
            conn.execute(sql.SQL("UPDATE {} SET record_raw = record_raw")
                .format(store._table("market_candidate_pins")))
    with store.connect() as conn:
        with pytest.raises(errors.RaiseException, match="immutable"):
            conn.execute(sql.SQL("DELETE FROM {}")
                .format(store._table("market_candidate_inputs")))
    assert store.get_market_candidate(candidate.scenario_id, candidate.revision)


def test_conflicting_numeric_revision_rolls_back_entire_new_candidate(saved_market):
    factory, _, request, _ = saved_market
    store = factory()
    candidate = MarketScenarioService(store).build_candidate(request, "tenant-1")
    scenario = deepcopy(store.get_economic_scenario(candidate.scenario_id,
                                                    candidate.revision))
    record = deepcopy(store.get_market_candidate(candidate.scenario_id,
                                                 candidate.revision))
    with store.connect() as conn:
        rows = conn.execute(sql.SQL("SELECT * FROM {} ORDER BY input_id, revision")
            .format(store._table("market_candidate_inputs"))).fetchall()
    new_records = [store._checked_input(row) for row in rows]
    new_shock_sha = "0" * 64
    record["request"]["shock"]["sha256"] = new_shock_sha
    record["shock_sha256"] = new_shock_sha
    identity = digest({"baseline": record["request"]["baseline"]["sha256"],
                       "shock": new_shock_sha,
                       "rights": record["rights_manifest_sha256"],
                       "bindings": record["binding_manifest_sha256"]})
    scenario["scenario_id"] = f"market-{identity[:32]}"
    scenario["sales"][0]["price"]["value"] = "91"
    next(item for item in new_records if item["input_id"] == "price")["value"] = "91"
    scenario_sha = canonical_scenario_sha256(EconomicScenario.model_validate(scenario))
    candidate_id = digest({"shock": (record["request"]["shock"]["shock_id"],
                                     record["request"]["shock"]["revision"], new_shock_sha),
                           "rights": record["rights_manifest_sha256"],
                           "bindings": record["binding_manifest_sha256"],
                           "economic_scenario": scenario_sha})
    record.update(candidate_id=candidate_id, scenario_id=scenario["scenario_id"],
                  economic_scenario_sha256=scenario_sha,
                  immutable_job_input_ref=f"market-job-{candidate_id[:32]}",
                  immutable_job_input_sha256=scenario_sha)
    with pytest.raises(ValueError, match="numeric revision conflict"):
        store.pin_market_candidate(record, scenario, new_records)
    with store.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {}")
            .format(store._table("market_candidate_pins"))).fetchone()["n"]
    assert count == 1
    assert store.get_market_candidate(scenario["scenario_id"], "r1") is None


def test_store_rejects_forged_candidate_and_job_identities(saved_market):
    factory, _, request, _ = saved_market
    store = factory()
    candidate = MarketScenarioService(store).build_candidate(request, "tenant-1")
    scenario = store.get_economic_scenario(candidate.scenario_id, candidate.revision)
    record = store.get_market_candidate(candidate.scenario_id, candidate.revision)
    with store.connect() as conn:
        rows = conn.execute(sql.SQL("SELECT * FROM {}")
            .format(store._table("market_candidate_inputs"))).fetchall()
    new_records = [store._checked_input(row) for row in rows]
    for changed in ({"candidate_id": "0" * 64},
                    {"immutable_job_input_ref": "market-job-forged"},
                    {"immutable_job_input_sha256": "0" * 64}):
        with pytest.raises(ValueError, match="record derivation differs"):
            store.pin_market_candidate({**record, **changed}, scenario, new_records)


def test_tenant_scope_and_concurrent_retry_do_not_fork_candidate(saved_market):
    factory, source, request, principal = saved_market
    with ThreadPoolExecutor(max_workers=2) as pool:
        candidates = list(pool.map(lambda _: MarketScenarioService(factory()).build_candidate(
            request, "tenant-1"), range(2)))
    assert candidates[0] == candidates[1]
    principal["tenant_id"] = "tenant-2"
    assert factory().get_market_candidate(candidates[0].scenario_id,
                                          candidates[0].revision) is None
    assert factory().get_joint_shock("joint-1", "r1") is None
    assert factory().get_market_hold_report("hold-1") is None
    with pytest.raises(ValueError, match="authenticated"):
        MarketScenarioService(factory()).calculate_pinned(
            candidates[0].scenario_id, candidates[0].revision, "tenant-1")
    principal["tenant_id"] = "tenant-1"
    principal["scopes"] = {"market_candidate_write"}
    assert factory().get_joint_shock("joint-1", "r1") is None
    principal["scopes"] = {"market_candidate_read"}
    source.authenticated = False
    assert factory().get_market_candidate(candidates[0].scenario_id,
                                          candidates[0].revision) is None
