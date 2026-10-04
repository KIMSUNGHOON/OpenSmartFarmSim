from copy import deepcopy
from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from math import fsum, ulp
from pathlib import Path

import pytest

from app.crop_fruit_transport import (
    FruitTransportHold, ReferenceFruitTransportParameters, calculate_transport_rates,
)


FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"
RAW_PROFILE = (FIXTURES / "crop-fruit-transport-reference-parameters-v1.json").read_bytes()
REFERENCE = json.loads((FIXTURES / "crop-fruit-transport-reference-cases-v1.json").read_bytes())
UNITS = {"fruit_number": "fruits_equivalent/m2_floor", "fruit_carbohydrate": "mg_CH2O/m2_floor"}


def inputs(pattern="multiple", temperature=20):
    return deepcopy(next(c["state"] for c in REFERENCE["cases"]
        if c["case_id"] == f"synthetic-{temperature}C-{pattern}"))


def run(state, profile=None):
    return calculate_transport_rates(state=state,
        profile=ReferenceFruitTransportParameters(RAW_PROFILE) if profile is None else profile)


@pytest.mark.parametrize("case", REFERENCE["cases"], ids=lambda c: c["case_id"])
def test_independent_decimal_reference_and_number_carbohydrate_balances(case):
    result = run(case["state"])
    expected = case["expected"]
    assert result["scope"] == "software_research_only"
    assert result["model_version"] == "vanthoor-fruit-transport-research-v1"
    assert result["profile_sha256"] == REFERENCE["profile_sha256"]
    for field in ("development_rate", "transport_rate"):
        assert result[field]["value"] == pytest.approx(float(expected[field]), rel=5e-12, abs=5e-14)
        assert result[field]["unit"] == "1/s"
    for group, unit in UNITS.items():
        derivatives = result["derivatives"][group]
        outflows = result["outflows"][group]
        assert len(derivatives) == len(outflows) == 50
        for field, quantities in (("derivative_", derivatives), ("outflow_", outflows)):
            for actual, target in zip(quantities, expected[field + group], strict=True):
                assert actual["value"] == pytest.approx(float(target), rel=5e-12, abs=5e-14)
                assert actual["unit"] == unit + "/s"
        assert result["terminal_outflow"][group] == outflows[-1]
        assert result["terminal_outflow"][group]["value"] == pytest.approx(
            float(expected["terminal_" + group]), rel=5e-12, abs=5e-14)
        assert result["totals"][group]["unit"] == unit
        assert result["totals"][group]["value"] == pytest.approx(float(expected["total_" + group]), rel=5e-12, abs=5e-14)
        residual = fsum([*(q["value"] for q in derivatives), outflows[-1]["value"]])
        scale = max(q["value"] for q in outflows)
        assert abs(residual) <= 102 * ulp(scale)
        assert result["balance_residual"][group]["value"] == residual
        assert result["balance_residual"][group]["unit"] == unit + "/s"
        assert abs(residual) <= result["balance_budget"][group]["value"]
    assert "harvest" not in result and "fresh_kg" not in result


def test_profile_bytes_pinned_and_values_immutable():
    profile = ReferenceFruitTransportParameters(RAW_PROFILE)
    assert profile.sha256 == sha256(RAW_PROFILE).hexdigest()
    assert profile.profile_id == "vanthoor-fruit-transport-reference-v1"
    assert profile.stages == 50
    assert profile.filtered_temperature_bounds == (17, 23)
    with pytest.raises(TypeError):
        profile.values["cDev1"] = 0
    with pytest.raises(FrozenInstanceError):
        profile.stages = 1
    for raw in (RAW_PROFILE + b" ", b"{}", "not bytes", None):
        with pytest.raises(FruitTransportHold, match="PROFILE_HOLD"):
            ReferenceFruitTransportParameters(raw)
    same_size_change = RAW_PROFILE.replace(b"1.16e-08", b"1.16e-07")
    assert same_size_change != RAW_PROFILE and len(same_size_change) == len(RAW_PROFILE)
    with pytest.raises(FruitTransportHold, match="PROFILE_HOLD: unreviewed"):
        ReferenceFruitTransportParameters(same_size_change)
    for path, value in (("cDev1", 0), ("cDev2", 1e-8), ("nDev", 1)):
        doc = json.loads(RAW_PROFILE)
        doc["parameters"][path]["value"] = value
        with pytest.raises(FruitTransportHold, match="PROFILE_HOLD"):
            ReferenceFruitTransportParameters(json.dumps(doc).encode())
    with pytest.raises(FruitTransportHold, match="PROFILE_HOLD"):
        run(inputs(), profile={})


def test_repeat_hash_origin_and_input_are_bound_without_mutation():
    state = inputs()
    original = deepcopy(state)
    result = run(state)
    assert state == original and run(deepcopy(state)) == result
    for field, replacement in (("input_id", "another-version"), ("origin", "reference_calculation")):
        changed = deepcopy(state)
        changed[field] = replacement
        other = run(changed)
        assert other["input_sha256"] != result["input_sha256"]
        assert other["derivatives"] == result["derivatives"]
    changed = deepcopy(state)
    changed["values"]["temperature_sum"]["value"] = 2
    assert run(changed)["input_sha256"] != result["input_sha256"]
    for group in UNITS:
        changed = deepcopy(state)
        changed["values"][group][0]["value"] *= 2
        assert run(changed)["input_sha256"] != result["input_sha256"]


@pytest.mark.parametrize("factor", [0, 0.001, 2, 1e100])
def test_scaling_preserves_transport_and_telescoping_balances(factor):
    state = inputs()
    original = run(state)
    for group in UNITS:
        for q in state["values"][group]:
            q["value"] *= factor
    scaled = run(state)
    for group in UNITS:
        assert scaled["totals"][group]["value"] == pytest.approx(original["totals"][group]["value"] * factor)
        for a, b in zip(original["derivatives"][group], scaled["derivatives"][group], strict=True):
            assert b["value"] == pytest.approx(a["value"] * factor)
        assert abs(scaled["balance_residual"][group]["value"]) <= scaled["balance_budget"][group]["value"]


@pytest.mark.parametrize("group", list(UNITS))
@pytest.mark.parametrize("size", [0, 49, 51])
def test_exact_compartment_count_required(group, size):
    state = inputs()
    state["values"][group] = [{"value": 1, "unit": UNITS[group]}] * size
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("field", [*UNITS, "temperature_filtered_24h", "temperature_sum"])
@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -1, True, "1", None])
def test_wrong_numeric_type_negative_and_nonfinite_rejected(field, bad):
    state = inputs()
    quantity = state["values"][field][0] if field in UNITS else state["values"][field]
    quantity["value"] = bad
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("field", [*UNITS, "temperature_filtered_24h", "temperature_sum"])
def test_wrong_units_and_quantity_shape_rejected(field):
    state = inputs()
    q = state["values"][field][0] if field in UNITS else state["values"][field]
    q["unit"] = "unknown"
    with pytest.raises(FruitTransportHold, match="UNIT_HOLD"):
        run(state)
    q["unit"] = UNITS[field] if field in UNITS else ("degC" if field == "temperature_filtered_24h" else "degC_day")
    q["extra"] = 0
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("temperature", [16.99, 23.01])
def test_outside_shared_reference_temperature_domain_held(temperature):
    state = inputs()
    state["values"]["temperature_filtered_24h"]["value"] = temperature
    with pytest.raises(FruitTransportHold, match="FRUIT_TRANSPORT_DOMAIN_HOLD"):
        run(state)


def test_onset_boundary_and_mass_without_number_are_held():
    state = inputs()
    state["values"]["temperature_sum"]["value"] = 0
    with pytest.raises(FruitTransportHold, match="FRUIT_TRANSPORT_DOMAIN_HOLD"):
        run(state)
    state = inputs("zero")
    state["values"]["fruit_carbohydrate"][0]["value"] = 1
    with pytest.raises(FruitTransportHold, match="FRUIT_COHORT_STATE_HOLD"):
        run(state)


@pytest.mark.parametrize("bad", [None, [], {}, {"origin": "synthetic"}])
def test_closed_block_required(bad):
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(bad)


@pytest.mark.parametrize("field", ["input_id", "origin", "values"])
def test_missing_closed_fields_rejected(field):
    state = inputs()
    del state[field]
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("field", [*UNITS, "temperature_filtered_24h", "temperature_sum"])
def test_missing_or_extra_quantity_rejected(field):
    state = inputs()
    del state["values"][field]
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)
    state = inputs()
    state["values"]["extra"] = {"value": 0, "unit": "1"}
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("group", list(UNITS))
@pytest.mark.parametrize("bad", [None, {}, 1, (1,) * 50, [1] * 50])
def test_malformed_array_or_quantity_rejected(group, bad):
    state = inputs()
    state["values"][group] = bad
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


def test_no_extra_state_blocks_are_admitted():
    state = inputs()
    state["management"] = {}
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


def test_derivative_underflow_with_nonzero_edge_flows_is_held():
    state = inputs("multiple")
    for group in UNITS:
        for q in state["values"][group]:
            q["value"] = 1e-315
    state["values"]["fruit_number"][1]["value"] += 5e-324
    with pytest.raises(FruitTransportHold, match="NUMERIC_HOLD: compartment derivative underflow"):
        run(state)


@pytest.mark.parametrize("value", ["", "  ", 1, None, "x" * 257])
def test_explicit_bounded_id_required(value):
    state = inputs()
    state["input_id"] = value
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("bad", ["approved", "", [], {}])
def test_origin_not_approval_and_enum_required(bad):
    state = inputs()
    state["origin"] = bad
    with pytest.raises(FruitTransportHold, match="INPUT_HOLD"):
        run(state)


@pytest.mark.parametrize("group", list(UNITS))
def test_numeric_sum_overflow_and_positive_transport_underflow_are_held(group):
    state = inputs("first")
    for name in UNITS:
        for q in state["values"][name]:
            q["value"] = 1
    for q in state["values"][group]:
        q["value"] = 1e308
    with pytest.raises(FruitTransportHold, match="NUMERIC_HOLD"):
        run(state)
    state = inputs("first")
    state["values"][group][0]["value"] = 1e-320
    with pytest.raises(FruitTransportHold, match="NUMERIC_HOLD"):
        run(state)
    state = inputs()
    state["values"][group][0]["value"] = 10 ** 10000
    with pytest.raises(FruitTransportHold, match="NUMERIC_HOLD"):
        run(state)
