"""Pre-engine checks for immutable synthetic thermal input and numerical rules."""

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
LAW_TEXT = (
    "p_sat_hPa=6.11*10^(7.5*t_C/(237.3+t_C)); "
    "t_C=T_K-273.15; p_sat_Pa=100*p_sat_hPa"
)
LAW_URL = "https://www.weather.gov/media/epz/wxcalc/vaporPressure.pdf"
LAW_RAW_SHA = "74e5a28ee21bde51d5ffad17f2418dc5c827c338d1bc11a09cbd7c623b87b621"
LAW_TEXT_SHA = "ea8d52e0bb02e36afb796b245f7df5dd3ce267fb7f0ea5c57dfa9b4e491e6b4b"
SI_BASIS = "bipm-si-unit-conversions"
SI_VERSION = "bipm-si-conversion-transcription-v1"
SI_SOURCE_URLS = {
    "kelvin_to_celsius_offset": "https://www.bipm.org/documents/20126/41489682/SI-App2-kelvin.pdf/",
    "hpa_to_pa_factor": "https://www.bipm.org/en/measurement-units/si-prefixes",
}
LAW_BASIS = "nws-epz-vapor-pressure-pdf"
REVIEW_SESSION = "01a0e210-df86-7e10-8c8e-d29a946c0e7d"
REVIEWED_FIXTURE_SHA = "4787a2dee823f6ea4b64922e08f8aa618f9f1f499f22236e4282d9cef0b0071a"
REVIEWED_MANIFEST_SHA = "1c2e5cd0f286118c46b5ed7b066e501cbd658ad197dc77b8cf4e95a0076461fb"
OLD_PINS = {
    "synthetic-weather-v1.json": (3295, "867cae5170ef49e768a9aeb0eb2315f69ab069b485e3b84ddc912c8e58cab5da"),
    "synthetic-economics-v1.json": (8538, "51d7241ff442fed1d8a8aafd16f4f15efa8b8e0e1cd2ec50f5954f53359c44e2"),
}
LIMITS = {
    "vapor_residual": (1.2e-13, "kg_v"),
    "aggregate_energy_residual": (4.5e-6, "J"),
    "temperature": (8.1e-5, "K"),
    "humidity_ratio": (5.4e-10, "kg_v/kg_da"),
    "delivered_heat_energy": (0, "J"),
}


@pytest.fixture(scope="module")
def data():
    paths = [FIXTURES / "synthetic-thermal-parameters-v1.json", FIXTURES / "manifest-v2.json"]
    assert all(path.is_file() for path in paths), "thermal fixture and manifest v2 are required"
    fixture, manifest = (json.loads(path.read_bytes()) for path in paths)
    weather = json.loads((FIXTURES / "synthetic-weather-v1.json").read_bytes())
    schema = json.loads((ROOT / "contracts/thermal-v1.schema.json").read_bytes())
    return fixture, manifest, weather, schema


def value(record):
    return record["value"]


def timestamp(text):
    assert text.endswith("Z")
    result = datetime.fromisoformat(text.replace("Z", "+00:00"))
    assert result.tzinfo == timezone.utc
    return result


def saturation(t):
    celsius = t - 273.15
    return 100 * 6.11 * 10 ** (7.5 * celsius / (237.3 + celsius))


def schema_section(schema, name, instance):
    subsection = {"$schema": schema["$schema"], "$defs": schema["$defs"],
                  **schema["properties"][name]}
    Draft202012Validator(subsection).validate(instance)


def schema_property(schema, parent, name, instance):
    node = parent["properties"][name]
    Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"],
                          **node}).validate(instance)


def numerical_bounds(fixture, weather):
    p = fixture["parameters"]
    C, M, c, latent, K = (value(p[key]) for key in (
        "effective_heat_capacity", "dry_air_mass", "dry_air_specific_heat",
        "latent_heat", "envelope_conductance"))
    assert len(fixture["intervals"]) == len(weather["intervals"]) == 2
    assert [(value(interval["assumed_forcing"]["ventilation_dry_air_flow"]),
             value(interval["assumed_forcing"]["canopy_evaporation"]))
            for interval in fixture["intervals"]] == [(0.02, 1e-5)] * 2
    F = value(fixture["intervals"][0]["assumed_forcing"]["ventilation_dry_air_flow"])
    E = value(fixture["intervals"][0]["assumed_forcing"]["canopy_evaporation"])
    cap = value(fixture["heater"]["capacity"])
    dt = value(fixture["integration"]["substep"])
    t0 = value(fixture["initial_state"]["temperature"])
    w0 = value(fixture["initial_state"]["humidity_ratio"])
    a_t = (K + F * c) / C
    a_w = F / M
    equilibria = []
    for index, weather_interval in enumerate(weather["intervals"]):
        raw = weather_interval["values"]
        to, phi, po, solar = (value(raw[key]) for key in
                              ("T_o", "phi_o", "p_o", "solar_interval_energy"))
        eo = phi * saturation(to)
        wo = (value(p["dry_air_gas_constant"]) / value(p["vapor_gas_constant"])) * eo / (po - eo)
        qsolar = solar * value(p["floor_area"]) * value(p["absorbed_solar_fraction"]) / 3600
        ground = value(fixture["intervals"][index]["assumed_forcing"]["ground_heat_flow"])
        teq = to + (qsolar + ground - latent * E + cap) / (K + F * c)
        weq = wo + E / F
        equilibria.append((teq, weq, wo, qsolar))
    return dt, a_t, a_w, t0, w0, equilibria


def assert_limits(fixture):
    integration = fixture["integration"]
    residual = integration["residual_tolerances"]
    convergence = integration["step_convergence_tolerances"]
    assert integration["residual_rule_ref"] == "thermal-binary64-residual-v1"
    assert residual["rule_version"] == "v1"
    assert integration["stability_rule_ref"] == "thermal-euler-stability-v1"
    assert convergence["rule_version"] == "v1"
    for group in (residual, convergence):
        assert "pre-registered" in group["rationale"]
        assert "absolute" in group["rationale"]
        assert "<= " in group["rationale"]
    for name, (expected, unit) in LIMITS.items():
        record = residual.get(name, convergence.get(name))
        assert record is not None
        assert record["value"] == expected and record["unit"] == unit
        assert record["origin"] == "assumed" and record["basis_ref"]
        assert record["version"] == "v1"


def assert_manifest_v2_pins(fixture, manifest):
    assert manifest["manifest_id"] == "synthetic-fixture-manifest-v2"
    assert manifest["market_context"] == {"kind": "unavailable", "hold_report_id": "market-hold-synthetic-v1"}
    assert manifest["market_hold_report"]["status"] == "hold"
    files = {Path(row["path"]).name: row for row in manifest["files"]}
    assert len(files) == len(manifest["files"])
    assert set(files) == {*OLD_PINS, "synthetic-thermal-parameters-v1.json"}
    for name, row in files.items():
        assert row["path"] == row["source_locator"] == f"fixtures/{name}"
        assert row["product_id"] == row["fixture_id"]
        assert row["review"]["review_id"] == manifest["synthetic_input_review_id"]
        raw = (FIXTURES / name).read_bytes()
        assert json.loads(raw)["fixture_id"] == row["fixture_id"]
        digest = hashlib.sha256(raw).hexdigest()
        assert row["byte_length"] == len(raw)
        assert row["sha256"] == digest
        assert row["content_id"] == f"sha256:{digest}"
        assert row["synthetic"] is True
        if name in OLD_PINS:
            assert (len(raw), digest) == OLD_PINS[name]
    assert fixture["fixture_id"] == files["synthetic-thermal-parameters-v1.json"]["fixture_id"]
    assert "sha256" not in manifest and "content_id" not in manifest
    assert "manifest-v2.json" not in {row["path"] for row in manifest["files"]}


def test_three_raw_byte_pins_and_noncircular_manifest(data):
    fixture, manifest, _, _ = data
    assert_manifest_v2_pins(fixture, manifest)


@pytest.mark.parametrize("mutation", [
    lambda m: m["files"][0].update(path="fixtures/../fixtures/synthetic-weather-v1.json"),
    lambda m: m["files"][0].update(source_locator="fixtures/weather-alias.json"),
    lambda m: m["files"][1]["review"].update(review_id="self-review-synthetic-fixtures-v1"),
])
def test_manifest_path_or_review_mutation_is_rejected(data, mutation):
    fixture, manifest, _, _ = copy.deepcopy(data)
    mutation(manifest)
    with pytest.raises((AssertionError, KeyError)):
        assert_manifest_v2_pins(fixture, manifest)


def test_schema_required_sourced_sections_and_assumptions(data):
    fixture, _, _, schema = data
    for name in ("initial_state", "parameters", "heater", "integration"):
        schema_section(schema, name, fixture[name])
    assert fixture["condensation_policy"] == schema["properties"]["condensation_policy"]["const"]
    basis = fixture["assumption_basis"]["basis_ref"]
    for group in (fixture["initial_state"], fixture["parameters"], fixture["heater"],
                  fixture["integration"], *(i["assumed_forcing"] for i in fixture["intervals"])):
        for item in group.values():
            if isinstance(item, dict) and "value" in item:
                assert {"value", "unit", "origin", "basis_ref", "version"} <= set(item)
                assert item["origin"] == "assumed" and item["basis_ref"] == basis
                assert item["version"] == "v1"
    assert value(fixture["intervals"][1]["assumed_forcing"]["ground_heat_flow"]) == 0
    assert value(fixture["heater"]["available"]) is True
    forcing_schema = schema["properties"]["forcing"]
    for interval in fixture["intervals"]:
        for name, record in interval["assumed_forcing"].items():
            schema_property(schema, forcing_schema, name, record)
    for group in (fixture["integration"]["residual_tolerances"],
                  fixture["integration"]["step_convergence_tolerances"]):
        for item in group.values():
            if isinstance(item, dict) and "value" in item:
                assert item["origin"] == "assumed" and item["basis_ref"] == basis
                assert item["version"] == "v1" and item["unit"]


def assert_nws_law(fixture, schema):
    law = fixture["parameters"]["saturation_pressure_rule"]
    source = fixture["law_source"]
    assert source["url"] == source["source_locator"] == source["final_url"] == LAW_URL
    assert source["basis_ref"] == LAW_BASIS
    assert source["version"] is None and source["vintage_id"] is None
    assert source["revision_id"] is None and source["published_at_utc"] is None
    assert source["available_at_utc"] is None and source["quantitative_accuracy"] is None
    assert source["declared_validity_interval"] is None
    assert source["raw_pdf_sha256"] == LAW_RAW_SHA
    assert source["raw_pdf_byte_length"] == 72617
    assert source["http_status"] == 200 and source["http_content_type"] == "application/pdf"
    assert source["http_last_modified_utc"] == "2017-02-04T01:36:33Z"
    assert source["retrieved_at_utc"] == "2026-09-27T08:33:51Z"
    assert source["observation_status"] == "not_applicable_published_equation"
    assert source["observed_start_utc"] is None and source["observed_end_utc"] is None
    reviewer = source["reviewer"]
    assert reviewer["session_id"] == REVIEW_SESSION
    assert reviewer["model"] == "gpt-6-sol"
    assert reviewer["model_reasoning_effort"] == "xhigh"
    assert reviewer["reviewed_at_utc_minute"] == "2026-09-27T08:59Z"
    assert reviewer["reviewed_fixture_raw_sha256"] == REVIEWED_FIXTURE_SHA
    assert reviewer["reviewed_manifest_raw_sha256"] == REVIEWED_MANIFEST_SHA
    assert "formula" in reviewer["scope"] and "conditional rights" in reviewer["scope"]
    assert "fresh remote byte comparison" in reviewer["limitations"]
    assert "server G0/G1" in reviewer["limitations"]
    assert "new metadata bytes" in reviewer["limitations"]
    assert source["review_status"] == "independent_cli_source_and_conditional_rights_review_completed"
    assert "independent CLI review" in source["project_qc_status"]
    assert source["original_unit"] == "hPa" and source["provider_qc_status"] == "not_specified"
    rights = source["rights"]
    assert rights["basis_url"] == "https://www.weather.gov/disclaimer"
    assert rights["use"] == rights["display"] == rights["redistribute"] == "allowed_with_conditions"
    assert rights["status"] == "nws_public_domain_disclaimer_independent_cli_reviewed_conditional"
    assert "do not claim NWS content as own" in rights["conditions"]
    assert "do not imply endorsement or affiliation" in rights["conditions"]
    assert "do not present modified information as official" in rights["conditions"]
    assert "attribute NWS" not in rights["conditions"]
    assert "voluntarily credit" not in rights["conditions"]
    assert "no special notice" in rights["third_party_caveat"]
    assert "independent CLI review" in rights["third_party_caveat"]
    assert "license" not in rights and "no Apache relicensing" in rights["scope"]
    assert fixture["unit_basis"]["basis_ref"] == SI_BASIS
    assert fixture["unit_basis"]["version"] == SI_VERSION
    assert fixture["unit_basis"]["source_urls"] == SI_SOURCE_URLS
    assert source["formula_text"] == LAW_TEXT
    assert law["formula_sha256"] == LAW_TEXT_SHA == hashlib.sha256(LAW_TEXT.encode("utf-8")).hexdigest()
    assert law["formula_id"] == law["formula_ref"] == source["basis_ref"]
    assert law["formula_version"] == "nws-formula-transcription-v1"
    assert value(law["temperature_min"]) == 289
    assert value(law["temperature_max"]) == 293
    assert law["temperature_min"]["unit"] == law["temperature_max"]["unit"] == "K"
    assert all(law[key]["origin"] == "assumed" and
               law[key]["basis_ref"] == fixture["assumption_basis"]["basis_ref"] and
               law[key]["version"] == "v1" for key in ("temperature_min", "temperature_max"))
    assert [(r["name"], r["value"], r["unit"]) for r in law["coefficients"]] == [
        ("pressure_coefficient", 6.11, "hPa"),
        ("exponent_factor", 7.5, "1"),
        ("denominator_offset", 237.3, "°C_interval"),
        ("exponential_base", 10, "1"),
        ("kelvin_to_celsius_offset", 273.15, "K"),
        ("hpa_to_pa_factor", 100, "Pa/hPa"),
    ]
    assert all(r["origin"] == "literature" and r["basis_ref"] == LAW_BASIS and
               r["version"] == "nws-formula-transcription-v1" for r in law["coefficients"][:4])
    assert all(r["origin"] == "literature" and r["basis_ref"] == SI_BASIS and
               r["version"] == SI_VERSION and
               r["name"] in SI_SOURCE_URLS for r in law["coefficients"][4:])
    assert saturation(289) == pytest.approx(1801.4593275266452, rel=1e-14)
    assert saturation(290) == pytest.approx(1919.9367926255202, rel=1e-14)
    assert saturation(293) == pytest.approx(2317.3064040894465, rel=1e-14)
    assert saturation(289) < saturation(290) < saturation(293)
    schema_section(schema, "parameters", fixture["parameters"])


def test_nws_law_source_formula_units_and_project_domain(data):
    fixture, _, _, schema = data
    assert_nws_law(fixture, schema)


@pytest.mark.parametrize("mutation", [
    lambda f: f["law_source"].update(raw_pdf_sha256="0" * 64),
    lambda f: f["law_source"].update(raw_pdf_byte_length=72618),
    lambda f: f["law_source"].update(url="https://example.invalid/vapor.pdf"),
    lambda f: f["law_source"]["rights"].update(redistribute="unverified"),
    lambda f: f["law_source"].update(published_at_utc="2017-02-04T01:36:33Z"),
    lambda f: f["parameters"]["saturation_pressure_rule"]["temperature_min"].update(value=273.16),
    lambda f: f["parameters"]["saturation_pressure_rule"]["coefficients"][4].update(value=273.16),
    lambda f: f["law_source"].update(formula_text=f["law_source"]["formula_text"].replace("7.5", "7.4")),
    lambda f: f["parameters"]["saturation_pressure_rule"].update(formula_sha256="0" * 64),
])
def test_nws_source_or_law_mutation_is_rejected(data, mutation):
    fixture, _, _, schema = copy.deepcopy(data)
    mutation(fixture)
    with pytest.raises((AssertionError, KeyError)):
        assert_nws_law(fixture, schema)


def assert_weather_links_and_derived_conversion_plan(fixture, manifest, weather):
    assert_manifest_v2_pins(fixture, manifest)
    records = {r["record_id"]: r for r in fixture["input_records"]}
    assert len(records) == len(fixture["input_records"])
    files_by_id = {row["fixture_id"]: row for row in manifest["files"]}
    assert len(files_by_id) == len(manifest["files"])
    file_contents = {fixture["fixture_id"]: fixture, weather["fixture_id"]: weather}
    expected_records = {
        f"{fixture['fixture_id']}:/parameters/{name}" for name in (
            "dry_air_gas_constant", "vapor_gas_constant", "saturation_pressure_rule",
            "floor_area", "absorbed_solar_fraction")
    }
    for i, interval in enumerate(weather["intervals"]):
        expected_records.update(
            f"{weather['fixture_id']}:/intervals/{i}/values/{name}"
            for name in interval["values"]
        )
        expected_records.update(
            f"{weather['fixture_id']}:/intervals/{i}/{name}"
            for name in ("start_utc", "end_utc")
        )
    assert set(records) == expected_records
    for record in records.values():
        assert record["record_id"] == f"{record['file_id']}:{record['json_pointer']}"
        assert record["file_id"] in files_by_id
        assert record["file_id"] in file_contents
        target = file_contents[record["file_id"]]
        for segment in record["json_pointer"].split("/")[1:]:
            target = target[int(segment)] if isinstance(target, list) else target[segment]
        assert target is not None
    assert len(fixture["intervals"]) == len(weather["intervals"]) == 2
    rules = fixture["conversion_rules"]
    assert rules["outdoor_humidity_ratio"]["formula"] == (
        "t_C=T_o_K-273.15; p_sat_hPa=6.11*10^(7.5*t_C/(237.3+t_C)); "
        "p_sat_Pa=100*p_sat_hPa; e_o=phi_o*p_sat_Pa; w_o=(R_da/R_v)*e_o/(p_o-e_o)"
    )
    assert rules["outdoor_humidity_ratio"]["saturation_rule_input_record_id"] == (
        f"{fixture['fixture_id']}:/parameters/saturation_pressure_rule"
    )
    assert rules["outdoor_humidity_ratio"]["unit_conversion_basis_ref"] == SI_BASIS
    assert rules["outdoor_humidity_ratio"]["input_domain"] == (
        "289<=T_o_K<=293 project synthetic range; 0<=phi_o<=1; p_o>e_o; same weather interval"
    )
    assert rules["solar_gain"]["formula"] == "Q_solar=H_solar*A_floor*f_abs/(end_utc-start_utc)"
    for i, interval in enumerate(fixture["intervals"]):
        raw = weather["intervals"][i]
        assert (interval["start_utc"], interval["end_utc"]) == (raw["start_utc"], raw["end_utc"])
        assert interval["weather_ref"] == {"fixture_id": weather["fixture_id"], "interval_index": i}
        assert "values" not in interval and "forcing" not in interval
        assert interval["weather_input_ids"] == {
            field: f"{weather['fixture_id']}:/intervals/{i}/values/{field}"
            for field in raw["values"]
        }
        assert set(interval["derived_forcing"]) == set(rules) == {
            "outdoor_humidity_ratio", "solar_gain"
        }
        for kind, plan in interval["derived_forcing"].items():
            assert plan["calculation_rule_ref"] == rules[kind]["rule_ref"]
            assert plan["calculation_rule_version"] == rules[kind]["version"] == "v1"
            assert plan["status"] == "pending_deterministic_engine"
            assert len(plan["input_record_ids"]) == len(set(plan["input_record_ids"]))
            assert all(rid in records for rid in plan["input_record_ids"])
        humid = interval["derived_forcing"]["outdoor_humidity_ratio"]["input_record_ids"]
        solar = interval["derived_forcing"]["solar_gain"]["input_record_ids"]
        assert set(humid) == {
            *(interval["weather_input_ids"][x] for x in ("T_o", "phi_o", "p_o")),
            *(f"{fixture['fixture_id']}:/parameters/{x}" for x in (
                "dry_air_gas_constant", "vapor_gas_constant", "saturation_pressure_rule")),
        }
        assert rules["outdoor_humidity_ratio"]["saturation_rule_input_record_id"] in humid
        assert set(solar) == {
            interval["weather_input_ids"]["solar_interval_energy"],
            f"{weather['fixture_id']}:/intervals/{i}/start_utc",
            f"{weather['fixture_id']}:/intervals/{i}/end_utc",
            f"{fixture['fixture_id']}:/parameters/floor_area",
            f"{fixture['fixture_id']}:/parameters/absorbed_solar_fraction",
        }
    assert fixture["intervals"][0]["end_utc"] == fixture["intervals"][1]["start_utc"]
    assert manifest["files"][0]["sha256"] == OLD_PINS["synthetic-weather-v1.json"][1]


def test_weather_links_and_derived_conversion_plan(data):
    fixture, manifest, weather, _ = data
    assert_weather_links_and_derived_conversion_plan(fixture, manifest, weather)


@pytest.mark.parametrize("mutation", [
    lambda f: f["conversion_rules"]["outdoor_humidity_ratio"].update(
        formula=f["conversion_rules"]["outdoor_humidity_ratio"]["formula"].replace("100*p_sat_hPa", "1000*p_sat_hPa")),
    lambda f: f["conversion_rules"]["outdoor_humidity_ratio"].update(
        formula=f["conversion_rules"]["outdoor_humidity_ratio"]["formula"].replace("273.15", "273.16")),
    lambda f: f["conversion_rules"]["outdoor_humidity_ratio"].update(
        saturation_rule_input_record_id="synthetic-thermal-parameters-v1:/parameters/floor_area"),
    lambda f: f["conversion_rules"]["outdoor_humidity_ratio"].update(version="v2"),
])
def test_conversion_mutation_is_rejected(data, mutation):
    fixture, manifest, weather, _ = copy.deepcopy(data)
    mutation(fixture)
    with pytest.raises((AssertionError, KeyError)):
        assert_weather_links_and_derived_conversion_plan(fixture, manifest, weather)


@pytest.mark.parametrize("mutation", [
    lambda f: f["intervals"][0]["derived_forcing"]["outdoor_humidity_ratio"]
    ["input_record_ids"].remove("synthetic-thermal-parameters-v1:/parameters/vapor_gas_constant"),
    lambda f: f["intervals"][0]["derived_forcing"]["solar_gain"]
    ["input_record_ids"].remove("synthetic-weather-v1:/intervals/0/end_utc"),
    lambda f: f["intervals"][0]["derived_forcing"]["outdoor_humidity_ratio"]
    ["input_record_ids"].__setitem__(0, "synthetic-weather-v1:/intervals/1/values/T_o"),
    lambda f: f["intervals"][0]["derived_forcing"]["outdoor_humidity_ratio"]
    ["input_record_ids"].append("synthetic-thermal-parameters-v1:/parameters/floor_area"),
    lambda f: f["input_records"][0].update(record_id="unsupported-alias"),
])
def test_derived_reference_mutation_is_rejected(data, mutation):
    fixture, manifest, weather, _ = copy.deepcopy(data)
    mutation(fixture)
    with pytest.raises((AssertionError, KeyError)):
        assert_weather_links_and_derived_conversion_plan(fixture, manifest, weather)


def test_exact_tiling_stability_bulk_bound_and_heater_cap(data):
    fixture, _, weather, _ = data
    dt, at, aw, t0, w0, equilibria = numerical_bounds(fixture, weather)
    assert value(fixture["heater"]["setpoint"]) == t0 == 293
    assert value(fixture["heater"]["available"]) is True
    assert dt == 60 and 3600 % dt == 0 and 3600 // dt == 60
    assert 0 < dt * at < 1 and dt * at == pytest.approx(0.0132)
    assert 0 < dt * aw < 1 and dt * aw == pytest.approx(0.0012)
    tmin = min(t0, *(entry[0] for entry in equilibria))
    wmin = min(w0, *(entry[1] for entry in equilibria))
    wmax = max(w0, *(entry[1] for entry in equilibria))
    assert equilibria[1][0] <= equilibria[0][0] <= t0
    assert [row[1] for row in equilibria] == pytest.approx(
        [0.006534303321127682, 0.007302623256965339], rel=1e-14
    )
    assert [row[2] for row in equilibria] == pytest.approx(
        [0.006034303321127682, 0.0068026232569653395], rel=1e-14
    )
    assert 291 < tmin < 292 and 0 < wmin <= wmax == w0
    p = fixture["parameters"]
    ei_max = value(p["dry_air_mass"]) / value(p["indoor_volume"]) * wmax * value(p["vapor_gas_constant"]) * t0
    assert ei_max / saturation(tmin) == pytest.approx(0.6154042772996245, rel=1e-14)
    assert ei_max / saturation(tmin) < 0.616
    # Positive Euler weights keep every full/half step between its start and fixed-cap equilibrium.
    for i, weather_interval in enumerate(weather["intervals"]):
        to = value(weather_interval["values"]["T_o"])
        teq, _, _, qsolar = equilibria[i]
        forcing = fixture["intervals"][i]["assumed_forcing"]
        slope = value(p["envelope_conductance"]) + (
            value(forcing["ventilation_dry_air_flow"]) * value(p["dry_air_specific_heat"]))
        cap = value(fixture["heater"]["capacity"])

        def q0(t):
            return (qsolar + slope * (to - t) + value(forcing["ground_heat_flow"])
                    - value(p["latent_heat"]) * value(forcing["canopy_evaporation"]))

        assert teq <= t0 == 293
        assert q0(teq) == pytest.approx(-cap, abs=1e-10)
        for substep in (60, 30):
            # Demand decreases with T on [T_eq, 293], so its minimum is at 293 K.
            assert value(p["effective_heat_capacity"]) / substep > slope
            demand_at_max_t = max(0, value(p["effective_heat_capacity"]) *
                                  (t0 - t0) / substep - q0(t0))
            demand_at_eq = max(0, value(p["effective_heat_capacity"]) *
                               (t0 - teq) / substep - q0(teq))
            assert demand_at_eq >= demand_at_max_t > cap


@pytest.mark.parametrize("field,replacement", [
    ("ventilation_dry_air_flow", 0.03),
    ("canopy_evaporation", 2e-5),
])
def test_second_interval_forcing_change_is_rejected(data, field, replacement):
    fixture, _, weather, _ = copy.deepcopy(data)
    fixture["intervals"][1]["assumed_forcing"][field]["value"] = replacement
    with pytest.raises(AssertionError):
        numerical_bounds(fixture, weather)


def test_preregistered_limits_have_independent_upstream_bounds(data):
    fixture, _, weather, schema = data
    assert_limits(fixture)
    schema_section(schema, "integration", fixture["integration"])
    dt, at, aw, t0, w0, eq = numerical_bounds(fixture, weather)
    max_t_distance = max(abs(t0 - row[0]) for row in eq)
    max_w_distance = max(abs(w0 - row[1]) for row in eq)
    assert (dt * at / 2) ** 2 * max_t_distance < LIMITS["temperature"][0]
    assert (dt * aw / 2) ** 2 * max_w_distance < LIMITS["humidity_ratio"][0]
    assert 500 * 60 == 2 * 500 * 30
    u = 2 ** -53
    gamma64 = 64 * u / (1 - 64 * u)
    assert gamma64 * 16.1 < LIMITS["vapor_residual"][0]
    assert gamma64 * 6.28e8 < LIMITS["aggregate_energy_residual"][0]
    # Both endpoint storage magnitudes enter the residual operand sums.
    p = fixture["parameters"]
    max_heat_terms = 60 * (50 + 500 + 4 * (200 + 0.02 * 1000) + 25)
    assert 2 * 1000 * w0 + 60 * (0.02 * (w0 - min(row[2] for row in eq)) + 1e-5) < 16.1
    assert 2 * value(p["effective_heat_capacity"]) * t0 + 2 * 2_500_000 * 1000 * w0 + max_heat_terms + 10_000 < 6.28e8


@pytest.mark.parametrize("mutation", [
    lambda f: f["integration"]["residual_tolerances"].pop("vapor_residual"),
    lambda f: f["integration"]["residual_tolerances"]["vapor_residual"].update(value=1e-9),
    lambda f: f["integration"]["step_convergence_tolerances"]["temperature"].update(value=1e-2),
    lambda f: f["integration"]["step_convergence_tolerances"]["delivered_heat_energy"].update(value=1),
    lambda f: f["integration"]["step_convergence_tolerances"].update(rule_version="v2"),
])
def test_missing_loose_or_mutated_limit_is_rejected(data, mutation):
    changed = copy.deepcopy(data[0])
    mutation(changed)
    with pytest.raises((AssertionError, KeyError)):
        assert_limits(changed)


def test_times_rights_and_claim_holds(data):
    fixture, manifest, weather, _ = data
    decision = timestamp(manifest["market_hold_report"]["decision_at_utc"])
    for row in manifest["files"]:
        assert timestamp(row["published_at_utc"]) <= timestamp(row["available_at_utc"]) <= decision
        assert timestamp(row["retrieved_at_utc"]) <= decision
        assert row["review"]["status"] == "self_reviewed_synthetic"
    assert fixture["synthetic"] is True and fixture["claim_scope"] == "synthetic_g1_software_input_only"
    assert fixture["law_source"]["rights"]["status"] == "nws_public_domain_disclaimer_independent_cli_reviewed_conditional"
    assert timestamp(fixture["law_source"]["retrieved_at_utc"]) <= timestamp(fixture["generated_at_utc"]) <= decision
    assert weather["intervals"][0]["start_utc"] > manifest["files"][0]["published_at_utc"]
    assert "hypothetical" in manifest["files"][0]["observation_status"]
    assert set(manifest["unresolved"]) == {
        "NO_REAL_SOURCE_G0", "NO_ACCEPTED_THERMAL_RUN",
        "NO_ENGINE_OPERATION_ORDER_REVIEW", "NO_SERVER_INPUT_LINKAGE_REVIEW",
        "NO_LOCAL_G2_MEASUREMENTS", "NO_G3_CROP_ECONOMIC_VALIDATION",
        "NO_G4_DEPLOYMENT_PROOF",
    }
    assert manifest["files"][2]["review"]["review_id"] == manifest["synthetic_input_review_id"]
    assert manifest["files"][2]["review"]["status"] == "self_reviewed_synthetic"
    assert "separate independent CLI source" in manifest["files"][2]["review"]["scope"]
    assert not any("IAPWS" in reason for reason in manifest["unresolved"])
    text = (ROOT / "contracts/thermal-sources.md").read_text(encoding="utf-8")
    assert LAW_URL in text and REVIEW_SESSION in text
    assert REVIEWED_FIXTURE_SHA in text and REVIEWED_MANIFEST_SHA in text
    assert "NO_INDEPENDENT_NWS_SOURCE_REVIEW" not in text
    assert "voluntarily credit NWS" in text
    assert "general attribution requirement" in text
    readme = (FIXTURES / "README.md").read_text(encoding="utf-8")
    assert "voluntarily credit NWS" in readme
    assert "general attribution requirement" in readme
    assert "Independent source review is pending" not in readme
    assert all(name in text and url in text for name, url in SI_SOURCE_URLS.items())
    assert "rejected/unadopted" in text and "IAPWS" in text
    assert "thermal-binary64-residual-v1" in text and "thermal-euler-stability-v1" in text
