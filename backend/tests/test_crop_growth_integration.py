from copy import deepcopy
from hashlib import sha256
import json
from math import exp
from pathlib import Path

import pytest

from app.crop_growth_integration import CropIntegrationHold, integrate_crop
from app.crop_growth_rates import ReferenceParameters


ROOT = Path(__file__).resolve().parents[2]
REFERENCE = json.loads((ROOT / "fixtures/crop-integration-reference-v1.json").read_bytes())
PROFILE = ReferenceParameters((ROOT / "fixtures/crop-growth-reference-parameters-v1.json").read_bytes())


def program():
    return deepcopy(REFERENCE["program"])


def run(p):
    return integrate_crop(**p, profile=PROFILE)


@pytest.mark.parametrize("case", ["events", "night"])
def test_independent_decimal_curve_units_carbon_balance_and_pulse_journal(case):
    reference=REFERENCE if case=="events" else REFERENCE["convergence_case"]
    result = run(deepcopy(reference["program"]))
    assert result["status"] == "completed"
    assert result["scope"] == "software_research_only"
    assert result["manifest"]["convergence"] == "not_evaluated_for_this_program"
    assert len(result["samples"]) == len(reference["expected"])
    for actual, expected in zip(result["samples"], reference["expected"]):
        assert actual["at"] == expected["at"]
        for name, value in expected["state"].items():
            tolerance = (5e-12 if name == "temperature_filtered_24h" else
                         5e-15 if name == "temperature_sum" else 5e-9)
            assert actual["state"][name]["value"] == pytest.approx(float(value), rel=0, abs=tolerance)
        for name, value in expected["cumulative"].items():
            assert actual["cumulative"][name]["value"] == pytest.approx(float(value), rel=0, abs=5e-9)
            assert actual["cumulative"][name]["unit"] == "mg_CH2O/m2_floor"
        assert actual["lai"]["value"] == pytest.approx(float(expected["lai"]), rel=0, abs=5e-13)
        assert abs(actual["carbon_residual"]["value"]) <= actual["carbon_residual_budget"]["value"]
        assert actual["state"]["temperature_sum"]["unit"] == "degC_day"
    assert len(result["events"]) == (2 if case=="events" else 0)
    for event in result["events"]:
        for organ, mass in event["removals"].items():
            assert event["before"][organ]["value"] - event["after"][organ]["value"] == pytest.approx(mass["value"], abs=1e-10)
    if case=="events":assert result["samples"][-1]["state"]["fruit"] == result["events"][-1]["after"]["fruit"]


def test_filtered_temperature_and_sum_match_independent_piecewise_analytic_solution():
    p = program(); seconds_per_day = PROFILE.values["seconds_per_day"]
    filtered = p["initial_state"]["values"]["temperature_filtered_24h"]["value"]
    for duration, temperature in ((120, 20), (120, 23), (60, 17)):
        filtered = temperature + (filtered - temperature) * exp(-duration / seconds_per_day)
    final = run(p)["samples"][-1]["state"]
    assert final["temperature_filtered_24h"]["value"] == pytest.approx(filtered, rel=0, abs=5e-12)
    assert final["temperature_sum"]["value"] == pytest.approx((120*20+120*23+60*17)/seconds_per_day, rel=0, abs=5e-15)


def test_smaller_steps_converge_toward_fixed_independent_reference():
    reference=REFERENCE["convergence_case"]
    errors=[]
    for step in (240, 120, 60):
        p=deepcopy(reference["program"]); p["solver"]["max_step_seconds"]=step
        p["output_times"]=[p["output_times"][0],p["output_times"][-1]]
        result=run(p); assert result["status"]=="completed"
        errors.append(abs(result["samples"][-1]["state"]["buffer"]["value"]-float(reference["expected"][-1]["state"]["buffer"])))
    assert errors[0] > errors[1] > errors[2]
    assert errors[0]/errors[1] > 12 and errors[1]/errors[2] > 12


def test_replay_digest_input_nonmutation_and_solver_source_event_time_binding():
    p=program(); original=deepcopy(p); first=run(p)
    assert p==original and run(deepcopy(p))==first
    raw={k:v for k,v in first.items() if k!="result_sha256"}
    assert first["result_sha256"]==sha256(json.dumps(raw,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    for mutate in (lambda x:x["solver"].update(max_step_seconds=5),
                   lambda x:x["segments"][0]["forcing"].update(input_id="new-vintage"),
                   lambda x:x["events"][0].update(at="2026-01-01T00:03:01Z")):
        p=program(); mutate(p); result=run(p)
        assert result["status"]=="completed"
        assert result["manifest"]["input_sha256"]!=first["manifest"]["input_sha256"]


def test_start_and_end_removals_occur_once_and_outputs_are_after_event():
    p=program(); p["events"][0]["at"]=p["output_times"][0]
    result=run(p); assert result["status"]=="completed"
    assert result["samples"][0]["state"]["leaf"]["value"]==4268
    assert result["samples"][0]["cumulative"]["removal_leaf"]["value"]==100
    assert result["samples"][-1]["cumulative"]["removal_fruit"]["value"]==pytest.approx(23)
    assert [e["at"] for e in result["events"]]==[p["output_times"][0],p["output_times"][-1]]


@pytest.mark.parametrize("kind", ["domain_switch","depleted_initial","negative_trial","excessive_event","overflow_balance"])
def test_equation_failure_returns_diagnostics_without_completed_samples(kind):
    p=program()
    if kind=="domain_switch":p["segments"][1]["forcing"]["values"]["canopy_temperature"]["value"]=10
    elif kind=="depleted_initial":
        p["initial_state"]["values"]["buffer"]["value"]=0
        p["segments"][0]["forcing"]["values"]["par_above_canopy"]["value"]=0
    elif kind=="negative_trial":p["segments"][0]["removals"]["values"]["leaf"]["value"]=1000
    elif kind=="excessive_event":p["events"][0]["removals"]["values"]["leaf"]["value"]=5000
    else:
        for organ in ("buffer","leaf","stem_root","fruit"):p["initial_state"]["values"][organ]["value"]=1e308
    result=run(p)
    assert result["status"]=="hold" and result["samples"]==[] and result["events"]==[]
    assert result["hold"]["time_meaning"]=="solver_evaluation_time"
    assert result["hold"]["reason"] and result["hold"]["attempted_at"]
    assert result["manifest"]["input_sha256"]
    json.dumps(result,allow_nan=False)
    if kind=="domain_switch":
        assert result["hold"]["attempted_at"]==p["segments"][1]["start"]
        assert result["hold"]["reason"].startswith("COMPENSATION_POINT_HOLD")
        assert result["hold"]["last_confirmed"]["forcing_input_id"]==p["segments"][0]["forcing"]["input_id"]
    if kind=="negative_trial":
        assert result["hold"]["phase"].startswith("rk4-")
        assert result["hold"]["last_confirmed"]["at"]==p["output_times"][0]
    if kind=="excessive_event":assert result["hold"]["reason"].startswith("REMOVAL_EXCEEDS_STORAGE_HOLD")


@pytest.mark.parametrize("kind", ["gap","overlap","order","offset","duplicate_output","outside_output",
                                   "missing_endpoint","duplicate_event","outside_event","event_unit","event_negative",
                                   "method","zero_step","bool_step","extra_solver","missing_rule","budget"])
def test_invalid_or_unbounded_program_is_rejected_before_execution(kind):
    p=program()
    if kind=="gap":p["segments"][1]["start"]="2026-01-01T00:02:01Z"
    elif kind=="overlap":p["segments"][1]["start"]="2026-01-01T00:01:59Z"
    elif kind=="order":p["segments"].reverse()
    elif kind=="offset":p["segments"][0]["start"]="2026-01-01T09:00:00+09:00"
    elif kind=="duplicate_output":p["output_times"].insert(0,p["output_times"][0])
    elif kind=="outside_output":p["output_times"][0]="2025-12-31T23:59:59Z"
    elif kind=="missing_endpoint":p["output_times"].pop()
    elif kind=="duplicate_event":p["events"].insert(0,deepcopy(p["events"][0]))
    elif kind=="outside_event":p["events"][0]["at"]="2025-12-31T23:59:59Z"
    elif kind=="event_unit":p["events"][0]["removals"]["values"]["leaf"]["unit"]="kg_fresh/m2"
    elif kind=="event_negative":p["events"][0]["removals"]["values"]["leaf"]["value"]=-1
    elif kind=="method":p["solver"]["method"]="invented"
    elif kind=="zero_step":p["solver"]["max_step_seconds"]=0
    elif kind=="bool_step":p["solver"]["max_step_seconds"]=True
    elif kind=="extra_solver":p["solver"]["adaptive"]=True
    elif kind=="missing_rule":del p["solver"]["roundoff_rule"]
    else:p["solver"]["max_steps"]=1
    with pytest.raises(CropIntegrationHold):run(p)
