"""Deterministic thermal-v1 calculations against pinned synthetic bytes."""

import copy
import json
from pathlib import Path
import sys

import pytest
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.thermal import ThermalHold, calculate_fixture, euler_step
from app.thermal_units import quantity as q
from app.thermal_units import saturation_pressure_pa


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
DECISION_AT = "2026-09-28T00:00:00Z"
REVIEW_AT = "2026-09-28T01:00:00Z"
CONTEXT_ID = "synthetic-decision-context-v1"


def raw_inputs():
    return tuple((FIXTURES / name).read_bytes() for name in (
        "manifest-v2.json", "synthetic-weather-v1.json", "synthetic-thermal-parameters-v1.json"
    ))


def run(*raw):
    return calculate_fixture(*(raw or raw_inputs()), decision_id="synthetic-decision-v1",
                             decision_at_utc=DECISION_AT,
                             decision_context_id=CONTEXT_ID,
                             claim_mode="ex_ante", decision_time_kind="hypothetical",
                             review_at_utc=REVIEW_AT,
                             input_snapshot_id="synthetic-input-snapshot-v1")


def test_nws_formula_and_two_candidate_hour_traces():
    thermal = json.loads(raw_inputs()[2])
    law = thermal["parameters"]["saturation_pressure_rule"]
    assert saturation_pressure_pa(290, law) == pytest.approx(1919.93679, abs=1e-5)
    traces = [json.loads(raw) for raw in run()]
    schema = json.loads((ROOT / "contracts/thermal-v1.schema.json").read_bytes())
    validator = Draft202012Validator(schema)
    assert len(traces) == 2
    for index, trace in enumerate(traces):
        assert trace["run_status"] == "candidate"
        assert not validator.is_valid(trace)
        accepted_shape = copy.deepcopy(trace)
        accepted_shape["run_status"] = "accepted"
        assert validator.is_valid(accepted_shape)
        assert trace["decision_context_id"] == CONTEXT_ID
        assert trace["decision_at_utc"] == DECISION_AT
        assert trace["review_at_utc"] == REVIEW_AT
        assert trace["claim_mode"] == "ex_ante"
        assert trace["decision_time_kind"] == "hypothetical"
        assert trace["trace_sequence_index"] == index
        assert len(trace["steps"]) == 60
        assert trace["source_records"][0]["observed_start_utc"] is None
        assert trace["forcing"]["solar_gain"]["value"] == (50 if index == 0 else 0)
        assert trace["forcing"]["outdoor_humidity_ratio"]["value"] == pytest.approx(
            (0.006034303321, 0.006802623257)[index], abs=1e-12)
        for step in trace["steps"]:
            assert step["heat_delivered"]["value"] <= 500
            assert step["heat_demand"]["value"] >= step["heat_delivered"]["value"]
            assert step["mass_terms"]["heater_vapor"]["value"] == 0
            assert step["mass_terms"]["condensation"]["value"] == 0
            assert abs(step["vapor_residual"]["value"]) <= 1.2e-13
            assert abs(step["aggregate_energy_residual"]["value"]) <= 4.5e-6
            assert step["convergence_deltas"]["temperature"]["value"] <= 8.1e-5
            assert step["convergence_deltas"]["humidity_ratio"]["value"] <= 5.4e-10
            assert step["convergence_deltas"]["delivered_heat_energy"]["value"] == 0
    assert traces[0]["interval"]["end_utc"] == traces[1]["interval"]["start_utc"]
    assert traces[0]["steps"][-1]["state_end"]["temperature"]["value"] == traces[1]["initial_state"]["temperature"]["value"]


def test_legacy_candidate_cannot_pass_accepted_trace_schema():
    legacy = json.loads(calculate_fixture(*raw_inputs(), decision_id="legacy-review",
                                          decision_at_utc=DECISION_AT,
                                          input_snapshot_id="legacy-snapshot")[0])
    legacy["run_status"] = "accepted"
    schema = json.loads((ROOT / "contracts/thermal-v1.schema.json").read_bytes())
    assert not Draft202012Validator(schema).is_valid(legacy)


def test_later_material_requires_ex_post_replay_label_and_review_cutoff():
    base = dict(decision_id="review-decision-1", decision_context_id="context-1",
                decision_at_utc="2026-09-27T08:00:00Z",
                decision_time_kind="hypothetical", input_snapshot_id="snapshot-1",
                review_at_utc="2026-09-27T10:00:00Z")
    with pytest.raises(ThermalHold, match="TIMESTAMP_HOLD"):
        calculate_fixture(*raw_inputs(), **base, claim_mode="ex_ante")
    replay = [json.loads(raw) for raw in calculate_fixture(
        *raw_inputs(), **base, claim_mode="ex_post_replay"
    )]
    assert all(trace["claim_mode"] == "ex_post_replay" for trace in replay)
    assert all(trace["decision_at_utc"] == base["decision_at_utc"] for trace in replay)
    assert all(trace["review_at_utc"] == base["review_at_utc"] for trace in replay)
    with pytest.raises(ThermalHold, match="TIMESTAMP_HOLD"):
        calculate_fixture(*raw_inputs(), **{**base, "review_at_utc": "2026-09-27T08:00:00Z"},
                          claim_mode="ex_post_replay")


@pytest.mark.parametrize("change", [
    {"decision_context_id": "context-2"},
    {"decision_at_utc": "2026-09-28T00:01:00Z"},
    {"review_at_utc": "2026-09-28T01:01:00Z"},
    {"claim_mode": "ex_post_replay"},
    {"decision_time_kind": "actual"},
])
def test_context_and_both_clocks_bind_run_identity_and_replay(change):
    from app.thermal import verify_replay

    base = dict(decision_id="review-decision-1", decision_context_id="context-1",
                decision_at_utc=DECISION_AT, review_at_utc=REVIEW_AT,
                claim_mode="ex_ante", decision_time_kind="hypothetical",
                input_snapshot_id="snapshot-1")
    raw = calculate_fixture(*raw_inputs(), **base)
    altered = calculate_fixture(*raw_inputs(), **{**base, **change})
    assert json.loads(raw[0])["run_id"] != json.loads(altered[0])["run_id"]
    with pytest.raises(ThermalHold, match="REPLAY_HOLD"):
        verify_replay(raw, *raw_inputs(), **{**base, **change})


@pytest.mark.parametrize("change", [
    {"decision_context_id": ""}, {"decision_context_id": 1},
    {"claim_mode": "unknown"}, {"claim_mode": 1},
    {"decision_time_kind": "claimed_actual"}, {"decision_time_kind": 1},
    {"review_at_utc": "2026-09-28T01:00:00+00:00"},
    {"decision_at_utc": "2026-09-28T02:00:00Z"},
])
def test_invalid_context_or_clock_is_controlled_hold(change):
    base = dict(decision_id="review-decision-1", decision_context_id="context-1",
                decision_at_utc=DECISION_AT, review_at_utc=REVIEW_AT,
                claim_mode="ex_ante", decision_time_kind="hypothetical",
                input_snapshot_id="snapshot-1")
    with pytest.raises(ThermalHold):
        calculate_fixture(*raw_inputs(), **{**base, **change})


def test_euler_controls_and_signed_ledger():
    raw = raw_inputs()
    thermal = json.loads(raw[2])
    params = thermal["parameters"]
    forcing = json.loads(run()[0])["forcing"]
    state = {"temperature": q(293.0, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")}
    on = euler_step(state, params, forcing, thermal["heater"], q(60, "s"))
    off_heater = copy.deepcopy(thermal["heater"])
    off_heater["available"]["value"] = False
    off = euler_step(state, params, forcing, off_heater, q(60, "s"))
    assert on["heat_delivered"]["value"] == 500
    assert on["heat_unmet"]["value"] > 0
    assert off["heat_delivered"]["value"] == 0
    assert off["heat_unmet"]["value"] == off["heat_demand"]["value"]
    assert on["heat_terms"]["canopy_latent"]["value"] == pytest.approx(-1500)
    assert on["heat_terms"]["ventilation_sensible"]["value"] == -3600
    assert on["mass_terms"]["ventilation"]["value"] < 0
    assert on["state_end"]["temperature"]["value"] > off["state_end"]["temperature"]["value"]
    low_target = copy.deepcopy(thermal["heater"])
    low_target["setpoint"]["value"] = 289
    cooling_request = euler_step(state, params, forcing, low_target, q(60, "s"))
    assert cooling_request["heat_demand"]["value"] == 0
    assert cooling_request["heat_delivered"]["value"] == 0


def test_saturation_and_nonoscillation_holds_before_a_step():
    thermal = json.loads(raw_inputs()[2])
    forcing = json.loads(run()[0])["forcing"]
    with pytest.raises(ThermalHold, match="CONDENSATION_HOLD"):
        euler_step({"temperature": q(293, "K"), "humidity_ratio": q(0.1, "kg_v/kg_da")},
                   thermal["parameters"], forcing, thermal["heater"], q(60, "s"))
    with pytest.raises(ThermalHold, match="STABILITY_HOLD"):
        euler_step({"temperature": q(293, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")},
                   thermal["parameters"], forcing, thermal["heater"], q(100_000, "s"))


@pytest.mark.parametrize("part,field,unit", [
    ("forcing", "solar_gain", "J/m²"),
    ("forcing", "ventilation_dry_air_flow", "kg_v/s"),
    ("parameters", "effective_heat_capacity", "J"),
    ("heater", "capacity", "kWh_th"),
    ("state", "temperature", "°C"),
    ("dt", None, "min"),
])
def test_public_step_rejects_unit_substitution(part, field, unit):
    trace = json.loads(run()[0])
    inputs = {
        "state": {"temperature": q(293, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")},
        "parameters": trace["parameters"], "forcing": trace["forcing"],
        "heater": trace["heater"], "dt": q(60, "s"),
    }
    (inputs[part] if field is None else inputs[part][field])["unit"] = unit
    with pytest.raises(ThermalHold, match="UNIT_HOLD"):
        euler_step(**inputs)


@pytest.mark.parametrize("part,field", [
    ("state", "temperature"), ("parameters", "effective_heat_capacity"),
])
def test_public_step_overflowing_integer_is_controlled_hold(part, field):
    trace = json.loads(run()[0])
    inputs = {
        "state": {"temperature": q(293, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")},
        "parameters": trace["parameters"], "forcing": trace["forcing"],
        "heater": trace["heater"], "dt": q(60, "s"),
    }
    inputs[part][field]["value"] = 10 ** 1000
    with pytest.raises(ThermalHold, match="INPUT_HOLD"):
        euler_step(**inputs)


@pytest.mark.parametrize("temperature,humidity_ratio", [
    (0, 0.008), (293, -0.001),
])
def test_public_step_invalid_aggregate_state_holds(temperature, humidity_ratio):
    trace = json.loads(run()[0])
    state = {"temperature": q(temperature, "K"),
             "humidity_ratio": q(humidity_ratio, "kg_v/kg_da")}
    with pytest.raises(ThermalHold, match="CONDENSATION_HOLD"):
        euler_step(state, trace["parameters"], trace["forcing"], trace["heater"], q(60, "s"))


def test_public_step_malformed_law_is_controlled_hold():
    trace = json.loads(run()[0])
    trace["parameters"]["saturation_pressure_rule"]["coefficients"][0] = None
    state = {"temperature": q(293, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")}
    with pytest.raises(ThermalHold, match="LAW_HOLD"):
        euler_step(state, trace["parameters"], trace["forcing"], trace["heater"], q(60, "s"))


@pytest.mark.parametrize("part,field,key,value", [
    ("parameters", "effective_heat_capacity", "basis_ref", 123),
    ("heater", "capacity", "version", 99),
    ("forcing", "solar_gain", "basis_ref", {"unresolved": "source"}),
])
def test_public_step_rejects_nonstring_provenance(part, field, key, value):
    trace = json.loads(run()[0])
    trace[part][field][key] = value
    state = {"temperature": q(293, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")}
    with pytest.raises(ThermalHold, match="INPUT_HOLD"):
        euler_step(state, trace["parameters"], trace["forcing"], trace["heater"], q(60, "s"))


def test_public_step_rejects_unregistered_derived_basis():
    trace = json.loads(run()[0])
    trace["forcing"]["solar_gain"]["basis_ref"] = "unregistered-rule-location"
    state = {"temperature": q(293, "K"), "humidity_ratio": q(0.008, "kg_v/kg_da")}
    with pytest.raises(ThermalHold, match="REFERENCE_HOLD"):
        euler_step(state, trace["parameters"], trace["forcing"], trace["heater"], q(60, "s"))


@pytest.mark.parametrize("path", [
    ("law_source",),
    ("integration", "residual_tolerances"),
])
def test_malformed_pinned_structure_is_controlled_hold(path):
    raw = list(raw_inputs())
    payload = json.loads(raw[2])
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = None
    raw[2] = json.dumps(payload).encode()
    with pytest.raises(ThermalHold, match="INPUT_HOLD"):
        run(*raw)


@pytest.mark.parametrize("path,value,reason", [
    (("heater", "mode"), "direct_combustion", "DIRECT_HEATER_HOLD"),
    (("heater", "mode"), "wet_heater", "DIRECT_HEATER_HOLD"),
    (("intervals", 0, "assumed_forcing", "ventilation_dry_air_flow", "unit"), "kg/s", "UNIT_HOLD"),
    (("intervals", 0, "assumed_forcing", "canopy_evaporation", "value"), -1, "INPUT_HOLD"),
    (("intervals", 0, "start_utc"), "2026-10-15T08:00:01Z", "TIMESTAMP_HOLD"),
])
def test_bad_thermal_input_holds(path, value, reason):
    raw = list(raw_inputs())
    payload = json.loads(raw[2])
    target = payload
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    raw[2] = json.dumps(payload).encode()
    with pytest.raises(ThermalHold, match=reason):
        run(*raw)


@pytest.mark.parametrize("field,value,reason", [
    ("solar_interval_energy", None, "INPUT_HOLD"),
    ("solar_interval_energy", -1, "SOLAR_HOLD"),
    ("T_o", {"value": 290, "unit": "°C"}, "UNIT_HOLD"),
    ("phi_o", {"value": 1.1, "unit": "1"}, "INPUT_HOLD"),
])
def test_bad_weather_holds(field, value, reason):
    raw = list(raw_inputs())
    weather = json.loads(raw[1])
    if value is None:
        del weather["intervals"][0]["values"][field]
    elif isinstance(value, dict):
        weather["intervals"][0]["values"][field].update(value)
    else:
        weather["intervals"][0]["values"][field]["value"] = value
    raw[1] = json.dumps(weather).encode()
    with pytest.raises(ThermalHold, match=reason):
        run(*raw)


def test_missing_review_or_source_qc_holds():
    raw = list(raw_inputs())
    manifest = json.loads(raw[0])
    manifest["files"][0]["review"]["status"] = "missing"
    raw[0] = json.dumps(manifest).encode()
    with pytest.raises(ThermalHold, match="REVIEW_HOLD"):
        run(*raw)


def test_gap_between_source_hours_holds():
    raw = list(raw_inputs())
    thermal = json.loads(raw[2])
    weather = json.loads(raw[1])
    thermal["intervals"][1]["start_utc"] = "2026-10-15T09:01:00Z"
    weather["intervals"][1]["start_utc"] = "2026-10-15T09:01:00Z"
    raw[1] = json.dumps(weather).encode()
    raw[2] = json.dumps(thermal).encode()
    with pytest.raises(ThermalHold, match="TIMESTAMP_HOLD"):
        run(*raw)
