"""Independent153-vector trajectories and real evolving current-stage feedback."""
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
from importlib import import_module
import json
from math import fsum, inf
from pathlib import Path
import runpy

import pytest

from app import crop_greenhouse_co2_joint as rhs
from app.crop_growth_rates import ReferenceParameters as Growth
from app.crop_fruit_cohorts import ReferenceFruitCohortParameters as Cohort
from app.crop_fruit_transport import ReferenceFruitTransportParameters as Transport
from app.crop_canopy_exchange import ReferenceParameters as Exchange

ROOT = Path(__file__).resolve().parents[2]
DOC = json.loads((ROOT / "fixtures/crop-greenhouse-co2-integration-reference-cases-v1.json").read_bytes())
CASES = DOC["cases"]
BLOCKS = ("scenario", "solar", "ventilation", "co2")


@pytest.fixture(scope="module")
def model():
    return import_module("app.crop_greenhouse_co2_integration")


@pytest.fixture(scope="module")
def profiles():
    return {key: kind((ROOT / "fixtures" / name).read_bytes()) for key, kind, name in (
        ("growth_profile", Growth, "crop-growth-reference-parameters-v1.json"),
        ("cohort_profile", Cohort, "crop-fruit-cohort-reference-parameters-v1.json"),
        ("transport_profile", Transport, "crop-fruit-transport-reference-parameters-v1.json"),
        ("exchange_profile", Exchange, "crop-canopy-exchange-reference-parameters-v1.json"))}


def run(model, profiles, case=None, dt=2, count=16):
    c = CASES[0] if case is None else case
    return model.integrate(**{key: c[key] for key in BLOCKS}, step_seconds=dt, step_count=count, **profiles)


@pytest.fixture(scope="module")
def results(model, profiles):
    return [run(model, profiles, c) for c in CASES]


def state(sample):
    return [q["value"] for q in [*[sample["plant_state"][k] for k in
        ("buffer", "leaf", "stem_root", "temperature_filtered_24h", "temperature_sum")],
        *sample["cohort_state"]["fruit_carbohydrate"], *sample["cohort_state"]["fruit_number"],
        *[sample["climate_state"][k] for k in ("canopy_sensible_energy", "air_temperature", "air_vapor_mass", "air_co2_mass")]]]


@pytest.mark.parametrize("index", range(8), ids=[c["case_id"] for c in CASES])
def test_independent_state_transfers_derived_and17_balances(results, index):
    actual, expected = results[index], CASES[index]["expected_decimal"]
    assert len(state(actual["samples"][-1])) == 109
    for found, wanted in zip(state(actual["samples"][-1]), expected["state"], strict=True):
        assert found == pytest.approx(float(wanted), rel=5e-12, abs=5e-14)
    assert len(actual["integrated_transfers"]) == 44
    for key, text in expected["integrated_transfers"].items():
        assert actual["integrated_transfers"][key]["value"] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    for key, text in expected["derived"].items():
        assert actual["samples"][-1]["derived"][key]["value"] == pytest.approx(float(text), rel=5e-12, abs=5e-14)
    assert actual["samples"][-1]["derived"]["canopy_temperature"]["value"] == pytest.approx(
        float(expected["derived"]["canopy_temperature"]), rel=0, abs=2e-10)
    assert len(actual["balance_residuals"]) == 17
    for key, quantity in actual["balance_residuals"].items():
        value = abs(quantity["value"])
        assert value <= actual["balance_budgets"][key]["value"]
        limit = 1e-12 if key == "number" else 1e-13 if quantity["unit"] == "kg_water/m2_floor" else 1e-8 if key == "crop_capacity" else 1e-7
        assert value <= limit
    assert actual["G0_G4"] == "not_assessed" and actual["scope"] == "software_research_only"
    assert actual["state_schema_version"] == rhs.STATE_SCHEMA
    assert "co2" not in actual["scenario"]["forcing"]


def metrics(sample, transfers):
    y = state(sample)
    return [sample["derived"]["canopy_temperature"]["value"], y[106], y[107], y[3], y[4],
            y[0], fsum(y[5:55]), *[transfers[k]["value"] for k in
            ("canopy_to_air_sensible", "canopy_to_vapor_latent", "canopy_to_air_vapor", "ventilation_sensible_heat", "ventilation_vapor")],
            y[108], sample["derived"]["crop_co2_ppm"]["value"],
            transfers["co2_crop_to_air"]["value"], transfers["co2_ventilation_to_air"]["value"]]


def fine_metrics(row):
    y = list(map(Decimal, row["state"])); t = row["integrated_transfers"]
    return [Decimal(row["derived"]["canopy_temperature"]), y[106], y[107], y[3], y[4], y[0], sum(y[5:55]),
            *[Decimal(t[k]) for k in ("canopy_to_air_sensible", "canopy_to_vapor_latent", "canopy_to_air_vapor", "ventilation_sensible_heat", "ventilation_vapor")],
            y[108], Decimal(row["derived"]["crop_co2_ppm"]), Decimal(t["co2_crop_to_air"]), Decimal(t["co2_ventilation_to_air"])]


@pytest.mark.parametrize("index", range(3), ids=[c["case_id"] for c in CASES[:3]])
def test_all96_step_halving_ratios_above8(model, profiles, results, index):
    with localcontext() as context:
        context.prec = 80
        target = fine_metrics(CASES[index]["fine_32s_dt0_25_decimal"])
        series = [run(model, profiles, CASES[index], dt=8, count=4), run(model, profiles, CASES[index], dt=4, count=8), results[index]]
        errors = [[abs(Decimal(str(value)) - expected) for value, expected in
                   zip(metrics(result["samples"][-1], result["integrated_transfers"]), target, strict=True)] for result in series]
        for column in range(16):
            a, b, c = (row[column] for row in errors)
            assert a > b > c > 0, (index, column, a, b, c)
            assert a / b > 8 and b / c > 8, (index, column, a / b, b / c)


def test_generator_exact_fixture_replay_and_pins():
    path = ROOT / "research/crop-greenhouse-co2-integration-reference.py"
    assert sha256(path.read_bytes()).hexdigest() == DOC["generator_sha256"]
    for name, digest in DOC["input_sha256"].items(): assert sha256((ROOT / name).read_bytes()).hexdigest() == digest
    assert runpy.run_path(str(path))["references"]() == DOC


def test_actual_evolving_trials_counts_samples_and_input_preservation(model, profiles, monkeypatch):
    calls = []
    original = rhs.evaluate_rhs
    def capture(**kwargs):
        result = original(**kwargs); calls.append(result); return result
    monkeypatch.setattr(rhs, "evaluate_rhs", capture)
    case = deepcopy(CASES[0]); before = deepcopy(case); result = run(model, profiles, case)
    assert len(calls) == 65 and result["numerical"]["coupled_rhs_evaluations"] == 65
    assert result["numerical"]["extra_validation_RHS_evaluations"] == 0
    assert len({r["scenario"]["climate_state"]["air_co2_mass"]["value"] for r in calls}) > 2
    assert len({r["derived"]["crop_co2_ppm"]["value"] for r in calls}) > 2
    for index, sample in enumerate(result["samples"]):
        assert sample["derived"]["crop_co2_ppm"] == calls[4 * index]["derived"]["crop_co2_ppm"]
        assert sample["climate_state"]["air_co2_mass"] == calls[4 * index]["scenario"]["climate_state"]["air_co2_mass"]
    assert case == before and run(model, profiles, case) == result


def test_event_free_numerical_split(model, profiles, results):
    first = run(model, profiles, dt=2, count=8)
    case = deepcopy(CASES[0])
    for block in ("plant_state", "cohort_state", "climate_state"): case["scenario"][block] = first["samples"][-1][block]
    second = run(model, profiles, case, dt=2, count=8)
    assert state(second["samples"][-1]) == state(results[0]["samples"][-1])
    for key, quantity in results[0]["integrated_transfers"].items():
        joined = first["integrated_transfers"][key]["value"] + second["integrated_transfers"][key]["value"]
        assert joined == pytest.approx(quantity["value"], rel=5e-12, abs=5e-14)


@pytest.mark.parametrize("external,later", [(-1e6, False), (-300, True)])
def test_real_depletion_keeps_only_last_confirmed_prefix(model, profiles, external, later):
    case = deepcopy(CASES[0]); case["co2"]["forcing"]["external_co2_flux"]["value"] = external
    with pytest.raises(model.Co2IntegrationHold) as caught: run(model, profiles, case, dt=1, count=16)
    error = caught.value
    assert error.step_index >= (2 if later else 1)
    assert error.failed_stage in ("k2", "k3", "k4", "endpoint", "endpoint_balance")
    assert error.last_confirmed_sample["step_index"] == error.step_index - 1
    assert error.last_confirmed_elapsed_seconds == error.step_index - 1
    assert error.last_confirmed_sample["climate_state"]["air_co2_mass"]["value"] > 0
    if later:
        prefix = run(model, profiles, case, dt=1, count=error.step_index - 1)
        assert prefix["samples"][-1] == error.last_confirmed_sample


@pytest.mark.parametrize("dt,count", [(0, 1), (True, 1), (inf, 1), (10**1000, 1), (1, 0), (1, True), (1, 4097), (601, 1)])
def test_budget_rejected_before_rhs(model, profiles, monkeypatch, dt, count):
    def forbidden(**kwargs): raise AssertionError("invalid budget evaluated RHS")
    monkeypatch.setattr(rhs, "evaluate_rhs", forbidden)
    with pytest.raises(model.Co2IntegrationHold): run(model, profiles, dt=dt, count=count)


def test_bad_initial_state_has_no_confirmed_prefix(model, profiles):
    case = deepcopy(CASES[0]); case["scenario"]["climate_state"]["air_co2_mass"]["value"] = 0
    with pytest.raises(model.Co2IntegrationHold) as caught: run(model, profiles, case)
    assert caught.value.failed_stage == "initial" and caught.value.last_confirmed_sample is None
