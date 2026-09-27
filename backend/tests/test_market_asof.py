"""RED as-of and tenant contracts using a TEST FAKE server repository only.

The positive fixture is invented contract data; it proves no real market G0 approval.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest
from pydantic import TypeAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.market import MarketContext, _Rights, resolve_market_context, validate_forecast_market_context


DECISION = datetime(2026, 1, 3, tzinfo=timezone.utc)
BEFORE = DECISION - timedelta(days=1)
AFTER = DECISION + timedelta(seconds=1)
RIGHTS = {"access": "allowed", "store": "allowed", "transform": "allowed", "display": "allowed"}


class FakeMarketRepository:
    """TEST FAKE server store; no production database or real G0 source."""

    def __init__(self):
        self.authenticated_tenants = {"tenant-1", "tenant-2"}
        self.snapshots = {
            "snapshot-1": {
                "market_snapshot_id": "snapshot-1", "tenant_id": "tenant-1",
                "decision_at": DECISION,
                "pinned_vintages": (
                    {"vintage_id": "vintage-1", "revision_id": "revision-1", "g0_evidence_id": "market-g0-1"},
                    {"vintage_id": "vintage-2", "revision_id": "revision-2", "g0_evidence_id": "market-g0-2"},
                ),
            },
        }
        self.hold_reports = {
            "hold-1": {
                "hold_report_id": "hold-1", "tenant_id": "tenant-1",
                "decision_at": DECISION,
                "reasons": ("market G0 evidence pending",),
                "missing_evidence": ("approved source vintage",),
            },
        }
        self.vintages = {
            ("vintage-1", "revision-1"): {
                "vintage_id": "vintage-1", "revision_id": "revision-1",
                "available_at": BEFORE, "retrieved_at": BEFORE, "rights": RIGHTS.copy(),
            },
            ("vintage-2", "revision-2"): {
                "vintage_id": "vintage-2", "revision_id": "revision-2",
                "available_at": DECISION, "retrieved_at": DECISION, "rights": RIGHTS.copy(),
            },
        }
        self.market_g0_evidence = {
            f"market-g0-{number}": {
                "evidence_id": f"market-g0-{number}", "tenant_id": "tenant-1",
                "vintage_id": f"vintage-{number}", "revision_id": f"revision-{number}",
                "authenticated": True, "approved": True, "status": "pass",
            }
            for number in (1, 2)
        }

    def tenant_is_authenticated(self, tenant_id):
        return tenant_id in self.authenticated_tenants

    def get_market_snapshot(self, snapshot_id):
        return self.snapshots.get(snapshot_id)

    def get_market_hold_report(self, hold_report_id):
        return self.hold_reports.get(hold_report_id)

    def get_market_vintage(self, vintage_id, revision_id):
        return self.vintages.get((vintage_id, revision_id))

    def get_market_g0_evidence(self, evidence_id):
        return self.market_g0_evidence.get(evidence_id)


def context(kind="available", identifier="snapshot-1"):
    key = "snapshot_id" if kind == "available" else "hold_report_id"
    return TypeAdapter(MarketContext).validate_python({"kind": kind, key: identifier})


def resolve(repository, market=None, tenant_id="tenant-1", decision_at=DECISION):
    return resolve_market_context(
        market or context(), tenant_id=tenant_id, decision_at=decision_at,
        repository=repository,
    )


def test_fake_server_resolves_both_tenant_owned_contexts():
    repository = FakeMarketRepository()
    assert resolve(repository) == context()
    unavailable = context("unavailable", "hold-1")
    assert resolve(repository, unavailable) == unavailable


@pytest.mark.parametrize("kind,identifier", [
    ("available", "unknown-snapshot"),
    ("unavailable", "unknown-hold"),
])
def test_unknown_server_reference_is_rejected(kind, identifier):
    with pytest.raises(ValueError):
        resolve(FakeMarketRepository(), context(kind, identifier))


@pytest.mark.parametrize("market", [context(), context("unavailable", "hold-1")])
def test_unauthenticated_or_foreign_tenant_is_rejected(market):
    repository = FakeMarketRepository()
    with pytest.raises(ValueError):
        resolve(repository, market, tenant_id="intruder")
    with pytest.raises(ValueError):
        resolve(repository, market, tenant_id="tenant-2")


@pytest.mark.parametrize("kind,field,identifier", [
    ("available", "market_snapshot_id", "snapshot-1"),
    ("unavailable", "hold_report_id", "hold-1"),
])
def test_resolver_rejects_mismatched_server_id_or_decision(kind, field, identifier):
    repository = FakeMarketRepository()
    record = repository.snapshots[identifier] if kind == "available" else repository.hold_reports[identifier]
    record[field] = "different-id"
    with pytest.raises(ValueError):
        resolve(repository, context(kind, identifier))
    record[field] = identifier
    record["decision_at"] = BEFORE
    with pytest.raises(ValueError):
        resolve(repository, context(kind, identifier))


def test_hold_report_must_explain_the_hold_and_missing_evidence():
    repository = FakeMarketRepository()
    report = repository.hold_reports["hold-1"]
    report["reasons"] = ()
    with pytest.raises(ValueError):
        resolve(repository, context("unavailable", "hold-1"))
    report["reasons"] = ("market G0 evidence pending",)
    report["missing_evidence"] = ()
    with pytest.raises(ValueError):
        resolve(repository, context("unavailable", "hold-1"))


def test_every_pinned_vintage_and_revision_must_be_known():
    repository = FakeMarketRepository()
    repository.vintages.pop(("vintage-2", "revision-2"))
    with pytest.raises(ValueError):
        resolve(repository)
    repository = FakeMarketRepository()
    repository.snapshots["snapshot-1"]["pinned_vintages"][1]["revision_id"] = "unknown-revision"
    with pytest.raises(ValueError):
        resolve(repository)


def test_snapshot_requires_a_nonempty_and_unique_pinned_vintage_list():
    repository = FakeMarketRepository()
    repository.snapshots["snapshot-1"]["pinned_vintages"] = ()
    with pytest.raises(ValueError):
        resolve(repository)
    repository = FakeMarketRepository()
    first = repository.snapshots["snapshot-1"]["pinned_vintages"][0]
    repository.snapshots["snapshot-1"]["pinned_vintages"] = (first, first.copy())
    with pytest.raises(ValueError):
        resolve(repository)


@pytest.mark.parametrize("change", [
    {"rights": {**RIGHTS, "display": "denied"}},
    {"available_at": AFTER},
    {"available_at": datetime(2026, 1, 2)},
    {"available_at": datetime(2026, 1, 2, 9, tzinfo=timezone(timedelta(hours=9)))},
    {"retrieved_at": AFTER},
    {"retrieved_at": datetime(2026, 1, 2)},
    {"retrieved_at": BEFORE - timedelta(days=2)},
    {"rights": {"access": "allowed", "store": "allowed", "transform": "allowed"}},
    {"rights": {**RIGHTS, "access": "unknown"}},
])
def test_each_available_vintage_needs_rights_utc_availability_and_asof_retrieval(change):
    repository = FakeMarketRepository()
    repository.vintages[("vintage-2", "revision-2")].update(change)
    with pytest.raises(ValueError):
        resolve(repository)


@pytest.mark.parametrize("change", [
    {"authenticated": False},
    {"approved": False},
    {"status": "hold"},
    {"vintage_id": "different-vintage"},
    {"revision_id": "different-revision"},
])
def test_each_vintage_needs_trusted_matching_market_g0_evidence(change):
    repository = FakeMarketRepository()
    repository.market_g0_evidence["market-g0-2"].update(change)
    with pytest.raises(ValueError):
        resolve(repository)


def test_missing_market_g0_evidence_is_rejected():
    repository = FakeMarketRepository()
    repository.market_g0_evidence.pop("market-g0-2")
    with pytest.raises(ValueError):
        resolve(repository)


def test_missing_approval_or_evidence_reference_is_rejected():
    repository = FakeMarketRepository()
    repository.market_g0_evidence["market-g0-2"].pop("approved")
    with pytest.raises(ValueError):
        resolve(repository)
    repository = FakeMarketRepository()
    repository.snapshots["snapshot-1"]["pinned_vintages"][1].pop("g0_evidence_id")
    with pytest.raises(ValueError):
        resolve(repository)


def test_repository_errors_and_malformed_records_fail_closed():
    repository = FakeMarketRepository()
    repository.get_market_vintage = lambda *args: 1 / 0
    with pytest.raises(ValueError):
        resolve(repository)
    repository = FakeMarketRepository()
    repository.market_g0_evidence["market-g0-2"] = {"approved": True}
    with pytest.raises(ValueError):
        resolve(repository)


def test_available_forecast_requires_server_verification():
    repository = FakeMarketRepository()
    available = context()
    with pytest.raises(ValueError):
        validate_forecast_market_context(available)
    assert validate_forecast_market_context(
        available, tenant_id="tenant-1", decision_at=DECISION, repository=repository
    ) == available
    repository.market_g0_evidence["market-g0-2"]["approved"] = False
    with pytest.raises(ValueError):
        validate_forecast_market_context(
            available, tenant_id="tenant-1", decision_at=DECISION, repository=repository
        )


def test_client_approved_field_cannot_admit_forecast():
    repository = FakeMarketRepository()
    forged = {"kind": "available", "snapshot_id": "snapshot-1", "approved": True}
    with pytest.raises(ValueError):
        validate_forecast_market_context(
            forged, tenant_id="tenant-1", decision_at=DECISION, repository=repository
        )


@pytest.mark.parametrize("decision_at", [
    datetime(2026, 1, 3),
    datetime(2026, 1, 3, 9, tzinfo=timezone(timedelta(hours=9))),
])
def test_decision_time_itself_must_be_utc_aware(decision_at):
    with pytest.raises(ValueError):
        resolve(FakeMarketRepository(), decision_at=decision_at)


def test_nested_constructed_rights_cannot_bypass_validation():
    repository = FakeMarketRepository()
    repository.vintages[("vintage-2", "revision-2")]["rights"] = _Rights.model_construct(
        access="denied", store="allowed", transform="allowed", display="allowed",
    )
    with pytest.raises(ValueError):
        validate_forecast_market_context(
            context(), tenant_id="tenant-1", decision_at=DECISION, repository=repository,
        )


def test_copied_market_context_extra_field_cannot_bypass_validation():
    forged = context().model_copy(update={"approved": True})
    with pytest.raises(ValueError):
        resolve(FakeMarketRepository(), forged)
