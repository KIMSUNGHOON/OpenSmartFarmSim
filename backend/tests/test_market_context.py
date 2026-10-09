"""RED contracts for the small market-context API, without a market data claim."""

from pathlib import Path
import sys

import pytest
from pydantic import TypeAdapter, ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.market import (
    MarketContext,
    UnavailableMarketContext,
    UserAssumptionProjection,
    validate_first_g1_use,
    validate_forecast_market_context,
    validate_market_context_chain,
)


def context(kind="unavailable", identifier="hold-1"):
    key = "snapshot_id" if kind == "available" else "hold_report_id"
    return TypeAdapter(MarketContext).validate_python({"kind": kind, key: identifier})


def chain(*contexts):
    return validate_market_context_chain(
        scenario_context=contexts[0],
        economic_scenario_context=contexts[1],
        economic_result_context=contexts[2],
        assessment_context=contexts[3],
    )


def test_exact_two_variant_strict_frozen_discriminated_union():
    adapter = TypeAdapter(MarketContext)
    schema = adapter.json_schema()
    assert schema["discriminator"]["propertyName"] == "kind"
    assert set(schema["discriminator"]["mapping"]) == {"available", "unavailable"}

    available = context("available", "snapshot-1")
    unavailable = context()
    assert type(available) is not type(unavailable)
    assert available.model_dump() == {"kind": "available", "snapshot_id": "snapshot-1"}
    assert unavailable.model_dump() == {"kind": "unavailable", "hold_report_id": "hold-1"}
    for value, fields in ((available, {"kind", "snapshot_id"}),
                          (unavailable, {"kind", "hold_report_id"})):
        assert set(type(value).model_fields) == fields
        assert type(value).model_config["strict"] is True
        assert type(value).model_config["frozen"] is True
        assert type(value).model_config["extra"] == "forbid"
        with pytest.raises(ValidationError):
            value.kind = "changed"


@pytest.mark.parametrize("payload", [
    None,
    {},
    {"kind": "unknown", "snapshot_id": "snapshot-1"},
    {"kind": "available"},
    {"kind": "unavailable"},
    {"kind": "available", "snapshot_id": None},
    {"kind": "unavailable", "hold_report_id": None},
    {"kind": "available", "snapshot_id": "snapshot-1", "hold_report_id": "hold-1"},
    {"kind": "unavailable", "hold_report_id": "hold-1", "snapshot_id": "snapshot-1"},
    {"kind": "available", "hold_report_id": "hold-1"},
    {"kind": "unavailable", "snapshot_id": "snapshot-1"},
    {"kind": "available", "snapshot_id": "snapshot-1", "extra": True},
    {"kind": "available", "snapshot_id": 1},
    {"kind": "available", "snapshot_id": True},
    {"kind": "unavailable", "hold_report_id": 1},
    {"kind": "unavailable", "hold_report_id": ["hold-1"]},
    {"kind": 1, "snapshot_id": "snapshot-1"},
])
def test_invalid_market_context_payloads_are_rejected(payload):
    with pytest.raises(ValidationError):
        TypeAdapter(MarketContext).validate_python(payload)


@pytest.mark.parametrize("kind,identifier", [
    ("available", "snapshot-1"),
    ("unavailable", "hold-1"),
])
def test_all_four_linked_contexts_can_agree(kind, identifier):
    same = context(kind, identifier)
    chain(same, same, same, same)


@pytest.mark.parametrize("position", range(4))
@pytest.mark.parametrize("replacement", [
    ("unavailable", "hold-2"),
    ("available", "snapshot-1"),
])
def test_every_link_must_match_both_kind_and_id(position, replacement):
    contexts = [context()] * 4
    contexts[position] = context(*replacement)
    with pytest.raises(ValueError):
        chain(*contexts)


def test_first_g1_unavailable_allows_only_user_assumptions_and_ends_on_hold():
    market = context()
    inputs = ({"origin": "user", "evidence_level": "assumed", "assumption_scope": "test fixture"},)
    assert validate_first_g1_use(market, economic_inputs=inputs, assessment_status="hold") == market
    assert validate_first_g1_use(
        market, economic_inputs=[UserAssumptionProjection(**inputs[0])], assessment_status="hold",
    ) == market


def test_first_g1_projection_is_exact_strict_and_frozen():
    projection = UserAssumptionProjection(
        origin="user", evidence_level="assumed", assumption_scope="test fixture",
    )
    assert set(type(projection).model_fields) == {
        "origin", "evidence_level", "assumption_scope",
    }
    assert type(projection).model_config["strict"] is True
    assert type(projection).model_config["frozen"] is True
    assert type(projection).model_config["extra"] == "forbid"
    with pytest.raises(ValidationError):
        projection.assumption_scope = "changed"


@pytest.mark.parametrize("inputs", [(), []])
def test_first_g1_rejects_empty_economic_projections(inputs):
    with pytest.raises(ValueError):
        validate_first_g1_use(context(), economic_inputs=inputs, assessment_status="hold")


@pytest.mark.parametrize("extra", [
    {"market_snapshot_id": "snapshot-1"},
    {"source_url": "https://example.org/market"},
    {"approved": True},
    {"value": "hidden market price"},
])
def test_first_g1_rejects_client_fields_outside_provenance_projection(extra):
    projection = {
        "origin": "user", "evidence_level": "assumed", "assumption_scope": "test fixture",
        **extra,
    }
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context(), economic_inputs=(projection,), assessment_status="hold",
        )


@pytest.mark.parametrize("scope", ["", " ", " test fixture ", "bad\nname", 1, None])
def test_first_g1_requires_a_valid_nonempty_assumption_scope(scope):
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context(), economic_inputs=({
                "origin": "user", "evidence_level": "assumed", "assumption_scope": scope,
            },), assessment_status="hold",
        )


def test_first_g1_checks_every_projection_in_a_sequence():
    valid = {"origin": "user", "evidence_level": "assumed", "assumption_scope": "test fixture"}
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context(), economic_inputs=[valid, {**valid, "approved": True}],
            assessment_status="hold",
        )


def test_first_g1_revalidates_a_constructed_projection():
    forged = UserAssumptionProjection.model_construct(
        origin="source", evidence_level="assumed", assumption_scope="test fixture",
    )
    with pytest.raises(ValueError):
        validate_first_g1_use(context(), economic_inputs=(forged,), assessment_status="hold")


def test_first_g1_needs_a_scoped_assumption_and_unavailable_context():
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context(), economic_inputs=({"origin": "user", "evidence_level": "assumed"},),
            assessment_status="hold",
        )
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context("available", "snapshot-1"),
            economic_inputs=({"origin": "user", "evidence_level": "assumed", "assumption_scope": "test fixture"},),
            assessment_status="hold",
        )


@pytest.mark.parametrize("origin,evidence_level", [
    ("source", "assumed"),
    ("user", "quoted"),
    ("user", "measured"),
    ("model", "modeled"),
])
def test_first_g1_unavailable_rejects_non_user_or_non_assumed_input(origin, evidence_level):
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context(), economic_inputs=({
                "origin": origin, "evidence_level": evidence_level, "assumption_scope": "test fixture",
            },),
            assessment_status="hold",
        )


@pytest.mark.parametrize("status", ["conditional", "pass", None])
def test_first_g1_unavailable_requires_final_assessment_hold(status):
    with pytest.raises(ValueError):
        validate_first_g1_use(
            context(), economic_inputs=({
                "origin": "user", "evidence_level": "assumed", "assumption_scope": "test fixture",
            },), assessment_status=status,
        )


def test_unavailable_context_cannot_start_a_forecast_run():
    with pytest.raises(ValueError):
        validate_forecast_market_context(context())


def test_constructed_market_context_must_be_revalidated_at_use():
    forged = UnavailableMarketContext.model_construct(
        kind="unavailable", hold_report_id=None,
    )
    with pytest.raises(ValueError):
        chain(forged, forged, forged, forged)
    with pytest.raises(ValueError):
        validate_first_g1_use(
            forged,
            economic_inputs=({
                "origin": "user", "evidence_level": "assumed",
                "assumption_scope": "test fixture",
            },),
            assessment_status="hold",
        )
