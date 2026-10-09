"""Authenticated market persistence; source records and keys are synthetic fixtures."""

from dataclasses import replace
from pathlib import Path
import sys

import psycopg
from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api import create_app
from app.market_candidate_store import MarketCandidateStore
from app.market_hold_store import MarketHoldStore
from app.market_result_store import MarketResultStore
from app.market_scenario import MarketScenarioService
from app.runtime_login import connect_runtime
from app.runtime_roles import (RuntimeLoginPolicy, RolePolicyHold, MARKET_TABLES, audit_runtime_roles)
from login_database import login_database, login_scope
from test_api_job_status import get, UnusedThermalRunStore
from test_api_market_hold import UnusedJobStore
from test_market_signed_hold_integration import signed_market_assembly


def stores(policy, dsn):
    class Source:
        def get_decision_context(self, *_): return None
    source = Source()
    return (
        MarketHoldStore(dsn, policy.schema, context_store=source, scope_resolver=lambda *_: None,
            principal_provider=lambda: None, signing_key=b"synthetic-market-test-key-32-bytes!",
            runtime_identity=(policy, "authority")),
        MarketCandidateStore(dsn, policy.schema, source, principal_provider=lambda: None,
            runtime_identity=(policy, "authority")),
        MarketResultStore(dsn, policy.schema, source, principal_provider=lambda: None,
            runtime_identity=(policy, "authority")))


@pytest.mark.parametrize("login_scope", [{"market_calculation": True}], indirect=True)
def test_v3_authority_matrix_and_v2_downgrade_denial(login_scope):
    _, policy, dsns = login_scope
    with connect_runtime(dsns["authority"], policy, "authority") as conn:
        assert audit_runtime_roles(conn, policy)["policy_version"] == "runtime-market-login-policy-v3"
        for table in MARKET_TABLES:
            for privilege in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
                assert conn.execute("SELECT has_table_privilege(current_user,%s,%s) AS allowed",
                    (policy.schema+"."+table, privilege)).fetchone()["allowed"] == (privilege in {"SELECT", "INSERT"})
        with pytest.raises(RolePolicyHold): audit_runtime_roles(conn, replace(policy, market_calculation=False))


@pytest.mark.parametrize("login_scope", [{"market_calculation": True}], indirect=True)
@pytest.mark.parametrize("kind", ["request", "worker", "supervisor"])
def test_general_authenticated_roles_cannot_read_market_tables(login_scope, kind):
    _, policy, dsns = login_scope
    for table in MARKET_TABLES:
        with connect_runtime(dsns[kind], policy, kind) as conn, pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(sql.SQL("SELECT * FROM {}.{} LIMIT 0").format(sql.Identifier(policy.schema), sql.Identifier(table)))


@pytest.mark.parametrize("login_scope", [{"market_calculation": True}], indirect=True)
@pytest.mark.parametrize("index", [0, 1, 2])
def test_each_store_uses_matching_scram_authority_and_rejects_wrong_login(login_scope, index):
    _, policy, dsns = login_scope
    with stores(policy, dsns["authority"])[index].connect() as conn:
        assert conn.info.user == policy.roles["authority"] and conn.pgconn.used_password
        assert conn.info.transaction_status == psycopg.pq.TransactionStatus.IDLE
    with pytest.raises(RolePolicyHold, match="^runtime_login_rejected$"):
        stores(policy, dsns["request"])[index].connect()


@pytest.mark.parametrize("login_scope", [{"market_calculation": True}], indirect=True)
@pytest.mark.parametrize("fault", ["worker_select", "authority_update", "grant_option", "missing_insert", "public_column", "future_grant"])
def test_effective_market_grant_drift_blocks_connection_before_reads(login_scope, fault):
    base, policy, dsns = login_scope
    target = sql.SQL("{}.market_candidate_pins").format(sql.Identifier(policy.schema))
    with base.connect() as conn:
        if fault == "worker_select":
            command = sql.SQL("GRANT SELECT ON {} TO {}").format(target, sql.Identifier(policy.roles["worker"]))
        elif fault == "authority_update":
            command = sql.SQL("GRANT UPDATE ON {} TO {}").format(target, sql.Identifier(policy.roles["authority"]))
        elif fault == "grant_option":
            command = sql.SQL("GRANT SELECT ON {} TO {} WITH GRANT OPTION").format(target, sql.Identifier(policy.roles["authority"]))
        elif fault == "missing_insert":
            command = sql.SQL("REVOKE INSERT ON {} FROM {}").format(target, sql.Identifier(policy.roles["authority"]))
        elif fault == "public_column":
            command = sql.SQL("GRANT SELECT (tenant_id) ON {} TO PUBLIC").format(target)
        else:
            conn.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL("CREATE TABLE {}.future_market (value text)").format(sql.Identifier(policy.schema)))
            command = sql.SQL("GRANT SELECT ON {}.future_market TO {}").format(sql.Identifier(policy.schema), sql.Identifier(policy.roles["authority"]))
        conn.execute(command)
    with pytest.raises(RolePolicyHold, match="^market_runtime_grants_rejected$"):
        stores(policy, dsns["authority"])[1].connect()


@pytest.mark.parametrize("flag", [None, 1, "true"])
def test_market_opt_in_requires_an_exact_boolean(flag):
    with pytest.raises(RolePolicyHold): RuntimeLoginPolicy("schema", "owner", "roles", "database", market_calculation=flag)


def test_v2_rejects_calculation_store_binding_and_v3_missing_tables(login_scope):
    _, policy, dsns = login_scope
    with pytest.raises(ValueError, match="^market runtime identity rejected$"):
        stores(policy, dsns["authority"])
    v3 = replace(policy, market_calculation=True)
    with pytest.raises(RolePolicyHold, match="^market_runtime_grants_rejected$"):
        stores(v3, dsns["authority"])[0].connect()


@pytest.mark.parametrize("login_scope", [{"market_calculation": True}], indirect=True)
def test_signed_hold_candidate_result_and_http_replay_with_actual_scram(login_scope):
    base, policy, dsns = login_scope
    factory, _, request, principal, scope = signed_market_assembly(dsns["authority"], policy.schema,
        runtime_identity=(policy, "authority"))
    principal["scopes"].add("market_hold_read")
    candidate = MarketScenarioService(factory()).build_candidate(request, "tenant-1")
    def results():
        return MarketResultStore(dsns["authority"], policy.schema, factory(),
            principal_provider=lambda: principal, runtime_identity=(policy, "authority"))
    pinned = results().pin_market_result(candidate.scenario_id, candidate.revision)
    assert results().get_market_result(candidate.scenario_id, candidate.revision) == pinned
    assert results().get_economic_result("tenant-1", pinned.economic_result.result_id) == pinned
    assert results().get_economic_result("tenant-2", pinned.economic_result.result_id) is None
    app = create_app(UnusedJobStore(), factory()._source, UnusedThermalRunStore(), results(), principal_provider=lambda: principal)
    status, body = get(app, "/v1/economic-results/"+pinned.economic_result.result_id)
    assert status == 200 and body["assessment_status"] == "hold" and body["evidence_level"] == "assumed"
    assert body["amounts"]["management_operating_income_krw"] == format(pinned.economic_result.management_oi, "f")
    assert get(app, "/v1/market-hold-reports/"+request["market_context"]["hold_report_id"])[0] == 200
    assert results().pin_market_result(candidate.scenario_id, candidate.revision) == pinned
    with base.connect() as conn:
        count = conn.execute(sql.SQL("SELECT count(*) AS n FROM {}.market_result_records").format(sql.Identifier(policy.schema))).fetchone()["n"]
        assert count == 1
    scope["scope_version"] = "v2"
    with pytest.raises(ValueError): results().get_market_result(candidate.scenario_id, candidate.revision)
