"""App-free Decimal80 CO2/Solar153-vector RK4 with unrounded current gas state."""
import argparse
from copy import deepcopy
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[1]
D = Decimal
PRIOR = "research/crop-greenhouse-solar-integration-reference.py"
CASES = "fixtures/crop-greenhouse-solar-integration-reference-cases-v1.json"
POLICY = "research/crop-co2-stomatal-source-register-20261021.json"
INPUTS = {PRIOR: "22a3996d7b2ed0bbdf4187e349a84d1c4466c4dbdfb70451c258aa95ed178574",
          CASES: "511a791251ad9a4e100f2f7cecc79177f7e386c3ad8a6ccd9613214a0c367bf8",
          POLICY: "50531ff4a945be2c07734b5e1c6b4a179b6bed598cab8350e0e20a56620775ce"}
CO2_FIELDS = ("co2_ventilation_to_air", "co2_external_to_air", "co2_crop_to_air")


def environment():
    for name, digest in INPUTS.items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    prior = runpy.run_path(str(ROOT / PRIOR)); env = prior["environment"]()
    policy = json.loads((ROOT / POLICY).read_bytes())["interpretations"]
    p1, p2 = policy["P01"], policy["P02"]
    flows = env["base"]["prior"]["FLOW"] + env["base"]["vent"]["EXTRA"] + ("canopy_non_solar_heat",) + tuple(
        "solar_par_" + k for k in env["prior"]["PAR_FIELDS"]) + tuple("solar_nir_" + k for k in prior["NIR_FIELDS"])
    return {"prior": prior, "env": env, "flows": flows + CO2_FIELDS,
            "R": D(p1["R_Pa_m3_per_mol_K"]), "M": D(p1["M_CO2_kg_per_mol"]),
            "offset": D(p1["temperature_offset_K"]),
            "ratio": D(p2["mCo2_mg_per_umol"]) / D(p2["mCh2o_mg_per_umol"])}


def ppm(s, co2, y, e):
    h = D(str(s["parameters"]["air_volume_per_floor_area"]["value"]))
    rv = D(str(s["parameters"]["vapor_gas_constant"]["value"]))
    temperature = y[106] + e["offset"]
    pressure = D(str(co2["parameters"]["air_pressure"]["value"]))
    air_moles = pressure * h / (e["R"] * temperature)
    if co2["basis"] == "dry": air_moles -= y[107] * rv / e["R"]
    return (y[108] / D("1e6") / e["M"]) / air_moles * D("1e6")


def rhs(s, solar, weather, co2, y, e):
    legacy = {**s, "forcing": {**s["forcing"], "co2": {"value": ppm(s, co2, y, e), "unit": "ppm"}}}
    legacy["climate_state"] = {k: v for k, v in s["climate_state"].items() if k != "air_co2_mass"}
    old = e["prior"]["rhs"](legacy, solar, weather, y[:108], e["env"])
    h = D(str(s["parameters"]["air_volume_per_floor_area"]["value"]))
    flow = D(str(weather["forcing"]["volume_exchange_per_floor_area"]["value"]))
    outside = D(str(co2["forcing"]["outdoor_co2_density"]["value"]))
    ventilation = flow * (outside - y[108] / h)
    external = D(str(co2["forcing"]["external_co2_flux"]["value"]))
    crop = -(old[108] - old[109] - sum(old[110:113])) * e["ratio"]
    return old[:108] + (ventilation + external + crop,) + old[108:] + (ventilation, external, crop)


def trajectory(s, solar, weather, co2, dt, count, e):
    y = e["env"]["base"]["prior"]["initial"](s) + (
        D(str(s["climate_state"]["air_co2_mass"]["value"])),) + (D(0),) * len(e["flows"])
    for _ in range(count):
        a = rhs(s, solar, weather, co2, y, e)
        b = rhs(s, solar, weather, co2, tuple(v + dt*k/2 for v, k in zip(y, a, strict=True)), e)
        c = rhs(s, solar, weather, co2, tuple(v + dt*k/2 for v, k in zip(y, b, strict=True)), e)
        d = rhs(s, solar, weather, co2, tuple(v + dt*k for v, k in zip(y, c, strict=True)), e)
        y = tuple(v + dt*(p + 2*q + 2*r + t)/6 for v, p, q, r, t in zip(y, a, b, c, d, strict=True))
    params = {k: D(str(q["value"])) for k, q in s["parameters"].items()}
    capacity = params["leaf_heat_capacity"] * e["env"]["base"]["env"]["p"]["sla"] * y[1]
    return {"state": list(map(str, y[:109])), "integrated_transfers": dict(zip(e["flows"], map(str, y[109:]), strict=True)),
            "derived": {"canopy_temperature": str(params["reference_temperature"] + y[105]/capacity),
                        "leaf_area_index": str(e["env"]["base"]["env"]["p"]["sla"] * y[1]),
                        "canopy_capacity": str(capacity), "crop_co2_ppm": str(ppm(s, co2, y, e))}}


def references():
    e = environment(); originals = json.loads((ROOT / CASES).read_bytes())["cases"]; cases = []
    with localcontext() as context:
        context.prec = 80
        # Recompute the rational conversion at the declared80-digit precision.
        p2 = json.loads((ROOT / POLICY).read_bytes())["interpretations"]["P02"]
        e["ratio"] = D(p2["mCo2_mg_per_umol"]) / D(p2["mCh2o_mg_per_umol"])
        for index, original in enumerate([*originals, originals[2]]):
            s, solar, weather = (deepcopy(original[k]) for k in ("scenario", "solar", "ventilation"))
            del s["forcing"]["co2"]
            s["climate_state"]["air_co2_mass"] = {"value": 2500.0, "unit": "mg_CO2/m2_floor"}
            basis = "dry" if index % 2 else "wet"
            co2 = {"input_id": "synthetic-co2-" + str(index), "origin": s["origin"], "basis": basis,
                   "parameters": {"air_pressure": {"value": 101325.0, "unit": "Pa"}},
                   "forcing": {"outdoor_co2_density": {"value": 700.0 if index % 2 == 0 else 400.0, "unit": "mg_CO2/m3"},
                               "external_co2_flux": {"value": (0.4, -0.2, 0.0, 2.0, 0.4, 0.0, 1.0, 0.2)[index], "unit": "mg_CO2/m2_floor/s"}}}
            if index == 4:
                s["removals"]["leaf"]["value"] = 0.05; s["removals"]["stem_root"]["value"] = 0.02
            row = {"case_id": original["case_id"] + "-" + basis, "scenario": s, "solar": solar,
                   "ventilation": weather, "co2": co2, "step_seconds": 2, "step_count": 16,
                   "expected_decimal": trajectory(s, solar, weather, co2, D(2), 16, e)}
            if index < 3:
                row["fine_32s_dt0_25_decimal"] = trajectory(s, solar, weather, co2, D(".25"), 128, e)
            cases.append(row)
    return {"version": "crop-greenhouse-co2-integration-reference-cases-v1",
            "generator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(), "input_sha256": INPUTS,
            "oracle": "Decimal80_app_free153_vector_RK4_current_CO2_mass_air_temperature_and_vapor",
            "scope": "self_authored_synthetic_math_only", "G0_G4": "not_assessed", "cases": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.output.open("x") as output:
        output.write(json.dumps(references(), indent=2, sort_keys=True, allow_nan=False) + "\n")
