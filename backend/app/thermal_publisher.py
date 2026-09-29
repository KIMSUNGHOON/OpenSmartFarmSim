"""Server-side synthetic thermal G1 gate. No external-source or field claim is issued."""

from datetime import datetime, timezone, timedelta
from hashlib import sha256
import hmac
import json
from math import isclose, isfinite
from pathlib import Path
import re

from jsonschema import Draft202012Validator, FormatChecker
from psycopg import sql

from .thermal import calculate_fixture, verify_replay, ThermalHold, MANIFEST_SHA256, LIMITS
from .thermal_run_store import snapshot_id_for, ThermalStoreHold


HEX = re.compile(r"^[0-9a-f]{64}$")
CODE_FILES = ("backend/app/thermal.py", "backend/app/thermal_units.py",
              "backend/app/thermal_publisher.py", "backend/app/thermal_run_store.py",
              "backend/app/job_store.py", "backend/app/jobs.py", "backend/app/db.py",
              "backend/app/cli_contracts.py", "backend/app/cli_contract_router.py", "backend/app/cli_worker.py",
              "backend/app/cli_supervisor.py",
              "backend/app/cli_attestation_issuer.py",
              "backend/app/cli_ipc.py", "backend/app/cli_supervisor_service.py",
              "backend/app/cli_supervisor_client.py",
              "backend/app/runtime_roles.py",
              "backend/app/authority_rpc.py",
              "backend/app/runtime_login.py",
              "backend/app/market_runtime.py", "backend/app/market_hold_store.py",
              "backend/app/market_candidate_store.py", "backend/app/market_result_store.py",
              "backend/app/market_scenario.py",
              "backend/app/economics.py",
              "backend/app/economic_calculation_worker.py", "backend/app/economic_work.py",
              "backend/app/break_even_store.py", "backend/app/api_break_even.py",
              "backend/app/api_economics.py", "backend/app/api_economic_cash_flow.py", "backend/app/break_even.py",
              "backend/app/content_access.py",
              "backend/app/execution_attestation.py", "backend/app/execution_verifier.py",
              "backend/app/thermal_review_contract.py",
              "backend/app/planning_events.py",
              "backend/app/planning_roles.py",
              "backend/app/planning_rpc.py",
              "backend/app/cli_plan.py",
              "backend/app/orchestration.py",
              "backend/app/research_registry.py",
              "backend/app/http_identity.py",
              "backend/app/https_service.py", "backend/app/api_serve.py",
              "backend/app/api.py", "backend/app/api_contracts.py",
              "backend/app/api_json.py", "backend/app/api_scenario.py",
              "backend/app/api_market_source.py",
              "backend/app/api_economic_scenario.py", "backend/app/farm_replay_scenario.py",
              "backend/app/api_economic_calculation.py",
              "backend/app/break_even_plan_submission.py",
              "backend/app/break_even_calculation_worker.py", "backend/app/break_even_work.py",
              "backend/app/api_job_break_even_result.py",
              "backend/app/owned_fixture_registry.py", "backend/app/owned_fixture_collection.py",
              "backend/app/collection_work.py",
              "backend/app/owned_collection_review.py",
              "backend/app/owned_research.py",
              "backend/app/owned_cli_contracts.py",
              "backend/app/calculation_assessment.py",
              "backend/app/api_assessment.py",
              "backend/app/api_owned_collection.py",
              "backend/app/api_runtime.py",
              "backend/app/api_job_run.py",
              "backend/app/thermal_scenario_store.py",
              "backend/app/thermal_scenario_execution.py",
              "backend/app/farm_thermal_execution.py",
              "backend/app/farm_economic_execution.py",
              "backend/app/thermal_run_submission.py",
              "contracts/thermal-scenario-v1.schema.json",
              "backend/app/market_source_store.py",
              "backend/app/thermal_simulation_worker.py",
              "backend/app/simulation_work.py",
              "contracts/thermal-v1.schema.json", "contracts/decision-v1.schema.json")
WEATHER_ID = "synthetic-weather-v1"
THERMAL_ID = "synthetic-thermal-parameters-v1"
RELEASE_HOLDS = ["NO_ENGINE_OPERATION_ORDER_REVIEW", "NO_SERVER_INPUT_LINKAGE_REVIEW"]
SOURCE_UNITS = {
    WEATHER_ID: {"T_o": "K", "phi_o": "1", "p_o": "Pa", "solar_interval_energy": "J/m²"},
    THERMAL_ID: {"temperature": "K", "humidity_ratio": "kg_v/kg_da", "heat": "W_th", "time": "s"},
}


class ThermalPublishHold(ValueError):
    """The server cannot issue a two-trace synthetic G1 Run."""


def _need(ok, reason):
    if not ok:
        raise ThermalPublishHold(reason)


def _hash(raw):
    return sha256(raw).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _pairs(items):
    result = {}
    for key, value in items:
        _need(key not in result, "FORMAT_HOLD: duplicate JSON key")
        result[key] = value
    return result


def _parse(raw, *, canonical=False):
    _need(type(raw) is bytes and 0 < len(raw) <= 1048576, "FORMAT_HOLD: invalid raw bytes")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        _need(type(value) is dict and (not canonical or raw == _json(value)),
              "FORMAT_HOLD: noncanonical document")
        return value
    except (UnicodeError, ValueError, TypeError, RecursionError, OverflowError) as exc:
        if isinstance(exc, ThermalPublishHold):
            raise
        raise ThermalPublishHold("FORMAT_HOLD: invalid JSON") from exc


def _utc(value):
    _need(type(value) is str and value.endswith("Z"), "TIME_HOLD: non-UTC timestamp")
    try:
        result = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ThermalPublishHold("TIME_HOLD: invalid UTC timestamp") from exc
    _need(result.utcoffset() == timedelta(0), "TIME_HOLD: offset mismatch")
    return result


def _iso(value):
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def _number(record, unit):
    _need(type(record) is dict and record.get("unit") == unit and
          type(record.get("value")) in (int, float) and isfinite(record["value"]),
          "PHYSICS_HOLD: nonfinite or wrong unit")
    return float(record["value"])


def _same(record, unit, expected, tolerance=1e-12):
    actual = _number(record, unit)
    _need(isclose(actual, expected, rel_tol=1e-12, abs_tol=tolerance),
          "PHYSICS_HOLD: independently recomputed value differs")


def runtime_digests(root):
    """Pin the exact implementation bytes and locked Python environment bytes."""
    root = Path(root)
    code = {name: _hash((root / name).read_bytes()) for name in CODE_FILES}
    return _hash(_json(code)), _hash((root / "backend/uv.lock").read_bytes())


CONTEXT_FIELDS = ("decision_context_id", "decision_at_utc", "claim_mode", "decision_time_kind")


def collection_review_input(snapshot, context):
    return {"input_version": "thermal-g1-collection-review-input-v1",
            "snapshot_id": snapshot["snapshot_id"],
            "manifest_sha256": snapshot["manifest_sha256"],
            "weather_sha256": snapshot["weather_sha256"],
            "thermal_sha256": snapshot["thermal_sha256"],
            "context_sha256": context["context_sha256"],
            **{key: context[key] for key in CONTEXT_FIELDS}}


def collection_review_proposal(snapshot, context):
    return {"proposal_version": "thermal-g1-collection-review-proposal-v1",
            "snapshot_id": snapshot["snapshot_id"],
            "manifest_sha256": snapshot["manifest_sha256"],
            "weather_sha256": snapshot["weather_sha256"],
            "thermal_sha256": snapshot["thermal_sha256"],
            "context_sha256": context["context_sha256"],
            **{key: context[key] for key in CONTEXT_FIELDS}}


def _pointer(document, pointer):
    _need(type(pointer) is str and pointer.startswith("/"), "SOURCE_HOLD: invalid JSON pointer")
    node = document
    try:
        for token in pointer[1:].split("/"):
            _need(token == token.replace("~1", "/").replace("~0", "~"),
                  "SOURCE_HOLD: unsupported escaped pointer")
            node = node[int(token)] if isinstance(node, list) else node[token]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise ThermalPublishHold("SOURCE_HOLD: unresolved source pointer") from exc
    return node


def _source_checks(manifest, weather, thermal, raw_hashes, decision_at, review_at, claim_mode):
    _need(manifest.get("claim_scope") == "synthetic_g1_software_input_only" and
          manifest.get("assessment_intent") == "hold" and
          all(code in manifest.get("unresolved", ()) for code in RELEASE_HOLDS),
          "SOURCE_HOLD: manifest scope or original holds differ")
    rows = {row["fixture_id"]: row for row in manifest["files"]}
    _need(len(rows) == len(manifest["files"]) and set(SOURCE_UNITS) <= set(rows),
          "SOURCE_HOLD: fixture inventory differs")
    _need(weather.get("fixture_id") == WEATHER_ID and thermal.get("fixture_id") == THERMAL_ID and
          weather.get("synthetic") is True and thermal.get("synthetic") is True,
          "SOURCE_HOLD: actual input in synthetic path")
    author = manifest.get("author")
    review_id = manifest.get("synthetic_input_review_id")
    _need(type(author) is str and author and type(review_id) is str and review_id,
          "SOURCE_HOLD: missing author/review")
    for fixture, digest in zip((weather, thermal), raw_hashes[1:]):
        identifier = fixture["fixture_id"]
        row = rows[identifier]
        _need(row.get("sha256") == digest and row.get("content_id") == "sha256:" + digest and
              row.get("synthetic") is True and row.get("product_id") == identifier and
              row.get("source_locator") == f"fixtures/{identifier}.json" and
              row.get("observed_start_utc") is None and row.get("observed_end_utc") is None and
              row.get("variable_units") == SOURCE_UNITS[identifier] and
              row.get("author") == author and row.get("qc", {}).get("status") == "self_checked_synthetic" and
              row.get("review", {}).get("review_id") == review_id and
              row.get("review", {}).get("status") == "self_reviewed_synthetic" and
              row.get("review", {}).get("reviewer") == author and
              row.get("rights", {}).get("holder") == author and
              row.get("rights", {}).get("license") == "Apache-2.0" and
              all(row["rights"].get(action) == "allowed" for action in
                  ("access", "store", "transform", "display", "redistribute")),
              "SOURCE_HOLD: synthetic raw pin, rights, QC or provenance")
        for source in (manifest, row):
            _need(_utc(source["published_at_utc"]) <= _utc(source["available_at_utc"])
                  <= _utc(source["retrieved_at_utc"]) <= review_at,
                  "SOURCE_HOLD: source chronology or review cutoff")
            if claim_mode == "ex_ante":
                _need(_utc(source["available_at_utc"]) <= decision_at,
                      "SOURCE_HOLD: source unavailable at planning decision")
        _need(_utc(row["applicability_start_utc"]) < _utc(row["applicability_end_utc"]),
              "SOURCE_HOLD: invalid applicability")
    law = thermal.get("law_source", {})
    _need(law.get("source_locator") == "https://www.weather.gov/media/epz/wxcalc/vaporPressure.pdf" and
          law.get("raw_pdf_sha256") == "74e5a28ee21bde51d5ffad17f2418dc5c827c338d1bc11a09cbd7c623b87b621" and
          law.get("published_at_utc") is None and law.get("available_at_utc") is None and
          law.get("rights", {}).get("status") ==
          "nws_public_domain_disclaimer_independent_cli_reviewed_conditional" and
          law.get("rights", {}).get("redistribute") == "allowed_with_conditions" and
          _utc(law["retrieved_at_utc"]) <= review_at,
          "SOURCE_HOLD: law source is unverified or rights misstated")
    return rows


def _check_trace_sources(traces, weather, thermal, rows, review_at, identity):
    run_identity = {**identity, "engine_version": "thermal-euler-v1",
                    "unit_registry_version": "thermal-si-nws-v1",
                    "model_version": "thermal-v1", "parameter_set_version": THERMAL_ID}
    run_id = "synthetic-thermal-v1:" + _hash(_json(run_identity))
    record_map = {}
    files = {WEATHER_ID: weather, THERMAL_ID: thermal}
    for entry in thermal["input_records"]:
        identifier, file_id, pointer = entry["record_id"], entry["file_id"], entry["json_pointer"]
        _need(file_id in files and identifier == f"{file_id}:{pointer}" and
              identifier not in record_map and _pointer(files[file_id], pointer) is not None,
              "SOURCE_HOLD: unresolved or duplicate input record")
        record_map[identifier] = _pointer(files[file_id], pointer)
    for hour, trace in enumerate(traces):
        start, end = weather["intervals"][hour]["start_utc"], weather["intervals"][hour]["end_utc"]
        _need(trace.get("contract_version") == "thermal-v1" and
              trace.get("run_id") == run_id and
              trace.get("trace_id") == f"{run_id}:hour-{hour}" and
              trace.get("decision_id") == identity["decision_id"] and
              all(trace.get(key) == identity[key] for key in
                  ("decision_context_id", "decision_at_utc", "review_at_utc",
                   "claim_mode", "decision_time_kind")) and
              trace.get("input_snapshot_id") == identity["input_snapshot_id"] and
              trace.get("manifest_sha256") == identity["manifest_sha256"] and
              trace.get("synthetic_input_review_id") ==
              rows[WEATHER_ID]["review"]["review_id"] ==
              rows[THERMAL_ID]["review"]["review_id"] and
              trace.get("model_version") == "thermal-v1" and
              trace.get("model_origin") == "project_aggregate_v1" and
              trace.get("parameter_set_version") == THERMAL_ID and
              trace.get("engine_version") == "thermal-euler-v1" and
              trace.get("unit_registry_version") == "thermal-si-nws-v1" and
              trace.get("trace_sequence_index") == hour and
              trace.get("claim_scope") == "synthetic_g1_contract_trace",
              "SOURCE_HOLD: trace version or scope differs")
        if hour == 0:
            _need(trace.get("initial_state") == thermal["initial_state"],
                  "SOURCE_HOLD: first initial state differs from raw bytes")
        else:
            previous = traces[hour - 1]
            previous_sha = _hash(_json(previous))
            for field in ("temperature", "humidity_ratio"):
                carry = trace["initial_state"][field]
                pointer = f"/steps/{len(previous['steps']) - 1}/state_end/{field}"
                _need(carry == {"value": previous["steps"][-1]["state_end"][field]["value"],
                      "unit": previous["steps"][-1]["state_end"][field]["unit"],
                      "origin": "derived", "basis_ref": f"trace-sha256:{previous_sha}#{pointer}",
                      "version": "v1", "calculation_rule_ref": "thermal-state-carry-v1",
                      "calculation_rule_version": "v1", "previous_trace_id": previous["trace_id"],
                      "previous_trace_sha256": previous_sha, "previous_state_pointer": pointer},
                      "SOURCE_HOLD: candidate carry is not linked to prior raw bytes")
        _need(trace["interval"] == {"start_utc": start, "end_utc": end} and
              _utc(start) < _utc(end) and
              rows[WEATHER_ID]["applicability_start_utc"] <= start < end <= rows[WEATHER_ID]["applicability_end_utc"] and
              rows[THERMAL_ID]["applicability_start_utc"] <= start < end <= rows[THERMAL_ID]["applicability_end_utc"],
              "SOURCE_HOLD: source/trace interval mismatch")
        sources = trace["source_records"]
        _need(type(sources) is list and len(sources) == 2, "SOURCE_HOLD: source inventory")
        for source, identifier, source_start, source_end in zip(sources,
            (WEATHER_ID, THERMAL_ID), (start, rows[THERMAL_ID]["applicability_start_utc"]),
            (end, rows[THERMAL_ID]["applicability_end_utc"])):
            row = rows[identifier]
            expected_id = f"{WEATHER_ID}:/intervals/{hour}" if identifier == WEATHER_ID else THERMAL_ID
            _need(source.get("id") == expected_id and source.get("source_locator") == row["source_locator"] and
                  source.get("product_id") == identifier and source.get("raw_sha256") == row["sha256"] and
                  source.get("original_unit") == row["variable_units"] and
                  source.get("observed_start_utc") is None and source.get("observed_end_utc") is None and
                  source.get("applicability_start_utc") == source_start and
                  source.get("applicability_end_utc") == source_end and
                  source.get("synthetic") is True and source.get("author") == row["author"] and
                  source.get("vintage") == row["vintage_id"] and
                  source.get("revision") == row["revision_id"] and
                  source.get("published_at_utc") == row["published_at_utc"] and
                  source.get("available_at_utc") == row["available_at_utc"] and
                  source.get("retrieved_at_utc") == row["retrieved_at_utc"] and
                  source.get("normalization_rule_ref") == "synthetic-identity-si-v1" and
                  source.get("project_qc") == {"status": "pass",
                      "rule_version": "synthetic-fixture-qc-v1",
                      "detail": "Pinned author self-check; server review remains separate"} and
                  source.get("provider_qc") == {"status": "not_applicable",
                      "detail": "self-authored synthetic input"} and
                  source.get("reviewer") == row["review"]["reviewer"] and
                  source.get("rights") == {"use": "allowed", "display": "allowed", "redistribute": "allowed"} and
                  _utc(source["retrieved_at_utc"]) <= review_at,
                  "SOURCE_HOLD: source record metadata differs from pinned manifest")
        expected = {
            "outdoor_humidity_ratio": [
                *(f"{WEATHER_ID}:/intervals/{hour}/values/{field}" for field in ("T_o", "phi_o", "p_o")),
                *(f"{THERMAL_ID}:/parameters/{field}" for field in
                  ("dry_air_gas_constant", "vapor_gas_constant", "saturation_pressure_rule"))],
            "solar_gain": [
                f"{WEATHER_ID}:/intervals/{hour}/values/solar_interval_energy",
                f"{WEATHER_ID}:/intervals/{hour}/start_utc",
                f"{WEATHER_ID}:/intervals/{hour}/end_utc",
                f"{THERMAL_ID}:/parameters/floor_area",
                f"{THERMAL_ID}:/parameters/absorbed_solar_fraction"],
        }
        for name, ids in expected.items():
            forcing = trace["forcing"][name]
            plan = thermal["intervals"][hour]["derived_forcing"][name]
            rule = thermal["conversion_rules"][name]
            _need(forcing.get("input_record_ids") == ids == plan["input_record_ids"] and
                  all(identifier in record_map for identifier in ids) and
                  forcing.get("basis_ref") == f"{THERMAL_ID}:/conversion_rules/{name}" and
                  forcing.get("calculation_rule_ref") == plan["calculation_rule_ref"] == rule["rule_ref"] and
                  forcing.get("calculation_rule_version") == plan["calculation_rule_version"] == rule["version"] == "v1" and
                  forcing.get("origin") == "derived" and forcing.get("version") == "v1",
                  "SOURCE_HOLD: derived forcing IDs or rule differ")


def _physical_step(t, w, seconds, p, f, heater):
    c = _number(p["effective_heat_capacity"], "J/K")
    m = _number(p["dry_air_mass"], "kg_da")
    cp = _number(p["dry_air_specific_heat"], "J/(kg_da*K)")
    latent = _number(p["latent_heat"], "J/kg_v")
    conductance = _number(p["envelope_conductance"], "W/K")
    airflow = _number(f["ventilation_dry_air_flow"], "kg_da/s")
    evaporation = _number(f["canopy_evaporation"], "kg_v/s")
    outdoor_t = _number(f["outdoor_temperature"], "K")
    outdoor_w = _number(f["outdoor_humidity_ratio"], "kg_v/kg_da")
    solar = _number(f["solar_gain"], "W")
    ground = _number(f["ground_heat_flow"], "W")
    _need(seconds > 0 and seconds * airflow / m <= 1 and
          seconds * (conductance + airflow * cp) / c <= 1,
          "PHYSICS_HOLD: stability screen")
    q0 = solar + conductance * (outdoor_t - t) + ground + airflow * cp * (outdoor_t - t) - latent * evaporation
    demand = max(0., c * (_number(heater["setpoint"], "K") - t) / seconds - q0)
    delivered = min(demand, _number(heater["capacity"], "W_th")) if heater["available"]["value"] else 0.
    next_w = w + seconds * (airflow * (outdoor_w - w) + evaporation) / m
    next_t = t + seconds * (q0 + delivered) / c
    mass = {"ventilation": seconds * airflow * (outdoor_w - w),
            "canopy_evaporation": seconds * evaporation, "heater_vapor": 0., "condensation": 0.}
    heat = {"solar": seconds * solar, "heater": seconds * delivered,
            "envelope": seconds * conductance * (outdoor_t - t), "ground": seconds * ground,
            "ventilation_sensible": seconds * airflow * cp * (outdoor_t - t),
            "canopy_latent": -seconds * latent * evaporation}
    vapor_residual = m * (next_w - w) - sum(mass.values())
    energy_residual = c * (next_t - t) + latent * m * (next_w - w) - (sum(heat.values()) + latent * sum(mass.values()))
    return next_t, next_w, demand, delivered, mass, heat, vapor_residual, energy_residual


def _check_physics(traces, weather, thermal):
    p = thermal["parameters"]
    heater = thermal["heater"]
    _need(heater.get("mode") == "indirect_sensible" and
          thermal.get("condensation_policy") == "hold_on_saturation",
          "PHYSICS_HOLD: unsupported mode")
    for name, (limit, unit) in LIMITS.items():
        group = ("residual_tolerances" if name in ("vapor_residual", "aggregate_energy_residual")
                 else "step_convergence_tolerances")
        _need(_number(thermal["integration"][group][name], unit) == limit,
              "PHYSICS_HOLD: preregistered limit differs")
    for hour, trace in enumerate(traces):
        _need(trace.get("parameters") == thermal["parameters"] and
              trace.get("heater") == thermal["heater"] and
              trace.get("integration") == thermal["integration"] and
              trace.get("condensation_policy") == thermal["condensation_policy"],
              "SOURCE_HOLD: trace parameters, control or integration differ from raw bytes")
        forcing = trace["forcing"]
        weather_row = weather["intervals"][hour]
        for weather_field, trace_field, unit in (("T_o", "outdoor_temperature", "K"),
            ("phi_o", "outdoor_relative_humidity", "1"), ("p_o", "outdoor_pressure", "Pa"),
            ("solar_interval_energy", "solar_interval_energy", "J/m²")):
            expected = weather_row["values"][weather_field]
            _need({key: forcing[trace_field][key] for key in
                ("value", "unit", "origin", "basis_ref", "version")} ==
                {key: expected[key] for key in ("value", "unit", "origin", "basis_ref", "version")},
                "SOURCE_HOLD: forcing does not match weather raw bytes")
            _number(forcing[trace_field], unit)
        for name in ("ventilation_dry_air_flow", "canopy_evaporation", "ground_heat_flow"):
            _need(forcing[name] == thermal["intervals"][hour]["assumed_forcing"][name],
                  "SOURCE_HOLD: assumed forcing does not match raw bytes")
        outdoor_t = _number(forcing["outdoor_temperature"], "K")
        celsius = outdoor_t - 273.15
        saturation = 100 * 6.11 * 10 ** (7.5 * celsius / (237.3 + celsius))
        vapor = _number(forcing["outdoor_relative_humidity"], "1") * saturation
        outdoor_p = _number(forcing["outdoor_pressure"], "Pa")
        _need(outdoor_p > vapor and vapor >= 0, "PHYSICS_HOLD: outdoor vapor pressure")
        outdoor_w = (_number(p["dry_air_gas_constant"], "J/(kg_da*K)") /
                     _number(p["vapor_gas_constant"], "J/(kg_v*K)")) * vapor / (outdoor_p - vapor)
        _same(forcing["outdoor_humidity_ratio"], "kg_v/kg_da", outdoor_w, 1e-14)
        solar = (_number(forcing["solar_interval_energy"], "J/m²") *
                 _number(p["floor_area"], "m²") * _number(p["absorbed_solar_fraction"], "1") / 3600)
        _same(forcing["solar_gain"], "W", solar, 1e-10)
        state = trace["initial_state"]
        t, w = _number(state["temperature"], "K"), _number(state["humidity_ratio"], "kg_v/kg_da")
        law = p["saturation_pressure_rule"]
        law_min = _number(law["temperature_min"], "K")
        law_max = _number(law["temperature_max"], "K")
        _need(law_min <= t <= law_max and w >= 0,
              "PHYSICS_HOLD: initial state outside law domain")
        first_celsius = t - 273.15
        first_saturation = 100 * 6.11 * 10 ** (7.5 * first_celsius / (237.3 + first_celsius))
        first_vapor = ((_number(p["dry_air_mass"], "kg_da") /
                        _number(p["indoor_volume"], "m³")) * w *
                       _number(p["vapor_gas_constant"], "J/(kg_v*K)") * t)
        _need(first_vapor < first_saturation,
              "PHYSICS_HOLD: initial aggregate saturation")
        start = _utc(trace["interval"]["start_utc"])
        end = _utc(trace["interval"]["end_utc"])
        _need(len(trace["steps"]) == 60 and end - start == timedelta(hours=1),
              "TIME_HOLD: wrong trace coverage")
        for step in trace["steps"]:
            seconds = (_utc(step["end_utc"]) - _utc(step["start_utc"])).total_seconds()
            _need(_utc(step["start_utc"]) == start and seconds == 60,
                  "TIME_HOLD: noncontiguous or wrong duration step")
            start = _utc(step["end_utc"])
            _same(step["state_start"]["temperature"], "K", t)
            _same(step["state_start"]["humidity_ratio"], "kg_v/kg_da", w, 1e-15)
            result = _physical_step(t, w, seconds, p, forcing, heater)
            next_t, next_w, demand, delivered, mass, heat, vapor_residual, energy_residual = result
            _same(step["state_end"]["temperature"], "K", next_t)
            _same(step["state_end"]["humidity_ratio"], "kg_v/kg_da", next_w, 1e-15)
            _same(step["heat_demand"], "W_th", demand)
            _same(step["heat_delivered"], "W_th", delivered)
            _same(step["heat_unmet"], "W_th", max(demand - delivered, 0.))
            _same(step["delivered_heat_energy"], "kWh_th", delivered * seconds / 3600000)
            for name, value in mass.items():
                _same(step["mass_terms"][name], "kg_v", value, 1e-13)
            for name, value in heat.items():
                _same(step["heat_terms"][name], "J", value, 1e-8)
            _same(step["vapor_residual"], "kg_v", vapor_residual, 1e-13)
            _same(step["aggregate_energy_residual"], "J", energy_residual, 4.5e-6)
            _need(abs(vapor_residual) <= LIMITS["vapor_residual"][0] and
                  abs(energy_residual) <= LIMITS["aggregate_energy_residual"][0],
                  "PHYSICS_HOLD: preregistered residual exceeded")
            half1 = _physical_step(t, w, seconds / 2, p, forcing, heater)
            half2 = _physical_step(half1[0], half1[1], seconds / 2, p, forcing, heater)
            deltas = {"temperature": abs(next_t - half2[0]),
                      "humidity_ratio": abs(next_w - half2[1]),
                      "delivered_heat_energy": abs(delivered * seconds - half1[3] * seconds / 2 - half2[3] * seconds / 2)}
            for name, delta in deltas.items():
                _same(step["convergence_deltas"][name], LIMITS[name][1], delta, 1e-10)
                _need(delta <= LIMITS[name][0], "PHYSICS_HOLD: preregistered half-step limit")
            m = _number(p["dry_air_mass"], "kg_da")
            rd = _number(p["dry_air_gas_constant"], "J/(kg_da*K)")
            rv = _number(p["vapor_gas_constant"], "J/(kg_v*K)")
            volume = _number(p["indoor_volume"], "m³")
            pressure = (m / volume) * (rd + next_w * rv) * next_t
            vapor_pressure = (m / volume) * next_w * rv * next_t
            tc = next_t - 273.15
            sat = 100 * 6.11 * 10 ** (7.5 * tc / (237.3 + tc))
            _need(vapor_pressure < sat and law_min <= next_t <= law_max and next_w >= 0,
                  "PHYSICS_HOLD: saturation or invalid state")
            _same(step["indoor_pressure_end"], "Pa", pressure, 1e-7)
            _same(step["relative_humidity_end"], "1", vapor_pressure / sat, 1e-12)
            t, w = next_t, next_w
        _need(start == end, "TIME_HOLD: incomplete steps")


class ThermalG1Publisher:
    """The only intended path from candidate bytes to an accepted synthetic Run."""

    def __init__(self, run_store, job_store, release_resolver, *, root, gate_key,
                 release_verifier=None, execution_verifier=None, collection_review_service=None):
        _need(callable(release_resolver) and type(gate_key) is bytes and len(gate_key) >= 32,
              "ACCESS_HOLD: missing trusted release/gate configuration")
        self.run_store, self.job_store = run_store, job_store
        self.release_resolver = release_resolver
        self.release_verifier = release_verifier
        self.execution_verifier = execution_verifier
        self.collection_review_service = collection_review_service
        self.root = Path(root)
        _need(self.root.resolve() == Path(__file__).resolve().parents[2],
              "PIN_HOLD: runtime digest root differs from loaded publisher")
        self._gate_key = gate_key

    def _review(self, tenant, job_id, snapshot):
        table = self.job_store._table
        with self.job_store.connect() as conn:
            job = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s")
                               .format(table("jobs")), (tenant, job_id)).fetchone()
            _need(job is not None and job["stage"] == "collection_review" and
                  job["state"] == "succeeded", "REVIEW_HOLD: no completed collection review")
            submitted = _parse(job["input_bytes"], canonical=True)
            context_id = submitted.get("decision_context_id")
            _need(type(context_id) is str and bool(context_id),
                  "CONTEXT_HOLD: review lacks decision context")
            context = self.run_store.get_decision_context(tenant, snapshot["snapshot_id"], context_id)
            _need(context is not None and context["tenant_id"] == tenant and
                  context["snapshot_id"] == snapshot["snapshot_id"],
                  "CONTEXT_HOLD: no trusted tenant/snapshot decision context")
            if submitted.get('input_version') == 'owned-collection-review-input-v1':
                from .owned_collection_review import OwnedCollectionReviewService
                service = self.collection_review_service
                _need(type(service) is OwnedCollectionReviewService and service.runs is self.run_store and
                      service.collection.jobs is self.job_store,
                      'REVIEW_HOLD: collection review service unavailable')
                service.verify_input(job, submitted)
            else:
                _need(job["input_bytes"] == _json(collection_review_input(snapshot, context)),
                      "REVIEW_HOLD: no exact completed collection review")
            _need(_hash(job["input_bytes"]) == job["input_sha256"],
                  "REVIEW_HOLD: no exact completed collection review")
            publication = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s")
                                       .format(table("job_publications")), (tenant, job_id)).fetchone()
            _need(publication is not None and publication["decision_id"] is not None and
                  publication["manifest"].get("input_sha256") == job["input_sha256"] and
                  publication["manifest"].get("stage") == "collection_review",
                  "REVIEW_HOLD: missing publication link")
            attempt = publication["attempt"]
            decision = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s")
                                    .format(table("ai_decisions")), (tenant, job_id, attempt)).fetchone()
            invocation = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s")
                                      .format(table("attempt_invocations")), (tenant, job_id, attempt)).fetchone()
            outcome = conn.execute(sql.SQL("SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND attempt=%s")
                                   .format(table("attempt_outcomes")), (tenant, job_id, attempt)).fetchone()
            _need(decision is not None and invocation is not None and outcome is not None and
                  decision["decision_id"] == publication["decision_id"] and
                  snapshot["recorded_at"] <= job["created_at"] <= decision["recorded_at"] <= publication["published_at"] and
                  context["recorded_at"] <= job["created_at"] and
                  _utc(context["issued_at_utc"]) <= job["created_at"] and
                  _utc(context["decision_at_utc"]) <= decision["recorded_at"],
                  "REVIEW_HOLD: invalid context/review chronology")
            _need(decision["decision_id"] == publication["decision_id"] and
                  decision["artifact_sha256"] == publication["artifact_sha256"] and
                  decision["disposition"] == "proceed" and
                  invocation["execution_kind"] == "codex_cli" and
                  invocation["model"] == "gpt-6-sol" and invocation["reasoning_effort"] == "xhigh" and
                  outcome["state"] == "succeeded" and outcome["exit_code"] == 0 and
                  outcome["decision_id"] == decision["decision_id"] and
                  self.job_store._verify_decision_final(conn, job, attempt,
                      decision["decision_id"], publication["artifact_sha256"]),
                  "REVIEW_HOLD: CLI capture, decision or validation is not trusted")
            capture = self.job_store._valid_cli_capture(conn, job, attempt, decision["output_sha256"])
            _need(capture is not None and capture["capture_id"] == decision["capture_id"] and
                  invocation["created_at"] <= capture["sealed_at"] <= decision["recorded_at"] and
                  callable(self.execution_verifier) and
                  self.execution_verifier(tenant, job_id, attempt,
                      capture["capture_id"], snapshot["snapshot_id"], decision["decision_id"]) is True,
                  "REVIEW_HOLD: no independently observed CLI worker execution")
        artifact = self.job_store.read_artifact(tenant, job_id)
        _need(artifact == _json(collection_review_proposal(snapshot, context)) and
              _hash(artifact) == publication["artifact_sha256"],
              "REVIEW_HOLD: review proposal does not bind snapshot")
        if submitted.get('input_version') == 'owned-collection-review-input-v1':
            _need(service is self.collection_review_service and service.runs is self.run_store and
                  service.collection.jobs is self.job_store,
                  'REVIEW_HOLD: collection review service changed')
            service.verify_input(job, submitted)
        return context, str(decision["decision_id"]), _iso(decision["recorded_at"]), str(capture["capture_id"])

    def _checked_snapshot(self, tenant, snapshot_id, decision_at, review_at, claim_mode):
        snapshot = self.run_store.get_snapshot(tenant, snapshot_id)
        _need(snapshot is not None and snapshot_id_for(snapshot["manifest_raw"],
            snapshot["weather_raw"], snapshot["thermal_raw"]) == snapshot_id,
            "PIN_HOLD: immutable snapshot missing or changed")
        raw = (snapshot["manifest_raw"], snapshot["weather_raw"], snapshot["thermal_raw"])
        _need(_hash(raw[0]) == MANIFEST_SHA256 and _hash(raw[1]) == snapshot["weather_sha256"] and
              _hash(raw[2]) == snapshot["thermal_sha256"],
              "PIN_HOLD: input bytes differ")
        manifest, weather, thermal = map(_parse, raw)
        rows = _source_checks(manifest, weather, thermal, tuple(map(_hash, raw)),
                              decision_at, review_at, claim_mode)
        _need(rows[WEATHER_ID]["byte_length"] == len(raw[1]) and
              rows[THERMAL_ID]["byte_length"] == len(raw[2]),
              "PIN_HOLD: fixture length differs")
        return manifest, weather, thermal

    def _release(self, tenant, snapshot_id, snapshot, context, review_at, code_sha, env_sha):
        result = self.release_resolver(tenant, snapshot_id)
        _need(type(result) is tuple and len(result) == 2,
              "RELEASE_HOLD: no independently issued release evidence")
        raw, signature = result
        release = _parse(raw, canonical=True)
        _need(type(signature) is str and 1 <= len(signature) <= 1024,
              "RELEASE_HOLD: missing authority signature")
        try:
            attestation = (self.release_verifier(raw, signature)
                           if callable(self.release_verifier) else None)
        except Exception as exc:
            raise ThermalPublishHold("RELEASE_HOLD: release verifier failed") from exc
        _need(type(attestation) is dict and
              set(attestation) == {"authority_id", "reviewer", "review_evidence_raw",
                                   "issued_at_utc"} and
              type(attestation["authority_id"]) is str and attestation["authority_id"] and
              type(attestation["reviewer"]) is str and attestation["reviewer"] and
              type(attestation["review_evidence_raw"]) is bytes and
              1 <= len(attestation["review_evidence_raw"]) <= 1048576 and
              _hash(attestation["review_evidence_raw"]) == release.get("review_evidence_sha256") and
              attestation["authority_id"] == release.get("authority_id") and
              attestation["reviewer"] == release.get("reviewer") and
              attestation["issued_at_utc"] == release.get("issued_at_utc"),
              "RELEASE_HOLD: untrusted release authority or review evidence")
        evidence = _parse(attestation["review_evidence_raw"], canonical=True)
        required = {"release_version", "scope", "manifest_sha256", "weather_sha256",
                    "thermal_sha256", "code_sha256", "environment_sha256", "reviewer",
                    "authority_id", "reviewed_at_utc", "issued_at_utc",
                    "review_evidence_sha256",
                    "cleared_holds", "source_verdict", "snapshot_id", "context_sha256",
                    *CONTEXT_FIELDS}
        _need(set(release) == required and release["release_version"] == "thermal-g1-release-v1" and
              release["scope"] == "synthetic_only" and
              release["manifest_sha256"] == snapshot["manifest_sha256"] and
              release["weather_sha256"] == snapshot["weather_sha256"] and
              release["thermal_sha256"] == snapshot["thermal_sha256"] and
              release["snapshot_id"] == snapshot_id and
              release["context_sha256"] == context["context_sha256"] and
              all(release[key] == context[key] for key in CONTEXT_FIELDS) and
              release["code_sha256"] == code_sha and
              release["environment_sha256"] == env_sha and
              release["cleared_holds"] == RELEASE_HOLDS and
              release["source_verdict"] == "synthetic_qc_rights_and_links_checked" and
              release["authority_id"] == evidence.get("authority_id") and
              type(release["reviewer"]) is str and release["reviewer"] !=
              "OpenSmartFarmSim fixture authors" and bool(release["reviewer"]) and
              type(release["review_evidence_sha256"]) is str and
              HEX.fullmatch(release["review_evidence_sha256"]) and
              _utc(release["reviewed_at_utc"]) >=
              max(_utc(snapshot_row["retrieved_at_utc"]) for snapshot_row in
                  (_parse(snapshot["manifest_raw"]),
                   self._manifest_row(snapshot, WEATHER_ID),
                   self._manifest_row(snapshot, THERMAL_ID),
                   _parse(snapshot["thermal_raw"])["law_source"])) and
              _utc(release["reviewed_at_utc"]) >=
              max(context["recorded_at"], _utc(context["issued_at_utc"])) and
              _utc(release["reviewed_at_utc"]) <= _utc(release["issued_at_utc"]) <= review_at,
              "RELEASE_HOLD: wrong scope, authority, code, source or time")
        evidence_required = {"review_version", "authority_id", "reviewer", "reviewed_at_utc",
                             "issued_at_utc", "review_method", "manifest_sha256", "weather_sha256",
                             "thermal_sha256", "code_sha256", "environment_sha256",
                             "cleared_holds", "operation_order", "input_linkage", "source_rights_qc",
                             "snapshot_id", "context_sha256", *CONTEXT_FIELDS}
        _need(set(evidence) == evidence_required and
              evidence["review_version"] == "thermal-g1-review-evidence-v1" and
              evidence["review_method"] == "codex_cli_gpt-6-sol_xhigh" and
              evidence["reviewer"] == release["reviewer"] and
              evidence["reviewed_at_utc"] == release["reviewed_at_utc"] and
              evidence["issued_at_utc"] == release["issued_at_utc"] and
              all(evidence[key] == release[key] for key in
                  ("manifest_sha256", "weather_sha256", "thermal_sha256",
                   "code_sha256", "environment_sha256", "cleared_holds",
                   "snapshot_id", "context_sha256", *CONTEXT_FIELDS)) and
              evidence["operation_order"] == {"status": "pass", "version": "thermal-euler-v1"} and
              evidence["input_linkage"] == {"status": "pass", "version": "thermal-g1-publisher-v1"} and
              evidence["source_rights_qc"] == {"status": "pass", "scope": "synthetic_only"},
              "RELEASE_HOLD: independent review content does not clear both holds")
        return raw, signature

    @staticmethod
    def _manifest_row(snapshot, fixture_id):
        manifest = _parse(snapshot["manifest_raw"])
        rows = [row for row in manifest["files"] if row["fixture_id"] == fixture_id]
        _need(len(rows) == 1, "RELEASE_HOLD: source record missing")
        return rows[0]

    def _validated_inputs(self, tenant, review_job_id, snapshot_id):
        try:
            snapshot = self.run_store.get_snapshot(tenant, snapshot_id)
            _need(snapshot is not None, "PIN_HOLD: no tenant-scoped snapshot")
            context, decision_id, review_time, capture_id = self._review(tenant, review_job_id, snapshot)
            decision_at, review_at = _utc(context["decision_at_utc"]), _utc(review_time)
            if context["claim_mode"] == "ex_ante":
                raise ThermalPublishHold("SOURCE_HOLD: no durable D-time vintage/rights evidence protocol")
            manifest, weather, thermal = self._checked_snapshot(
                tenant, snapshot_id, decision_at, review_at, context["claim_mode"])
            _source_checks(manifest, weather, thermal,
                (snapshot["manifest_sha256"], snapshot["weather_sha256"], snapshot["thermal_sha256"]),
                decision_at, review_at, context["claim_mode"])
            code_sha, env_sha = runtime_digests(self.root)
            release_raw, release_signature = self._release(tenant, snapshot_id, snapshot,
                                                          context, review_at, code_sha, env_sha)
            return (snapshot, context, decision_id, review_time, capture_id, manifest,
                    weather, thermal, code_sha, env_sha, release_raw, release_signature)
        except Exception as exc:
            if isinstance(exc, ThermalPublishHold):
                raise
            raise ThermalPublishHold("G1_HOLD: source, trace or publication failed") from exc

    def validate_submission(self, tenant, review_job_id, snapshot_id):
        """Check admission evidence without calculating, publishing or granting G1."""
        snapshot, context, *_ = self._validated_inputs(tenant, review_job_id, snapshot_id)
        return {"tenant_id": tenant, "snapshot_id": snapshot_id,
                "decision_context_id": context["decision_context_id"],
                "context_sha256": context["context_sha256"],
                "manifest_sha256": snapshot["manifest_sha256"]}

    def prepare(self, tenant, review_job_id, snapshot_id):
        try:
            (snapshot, context, decision_id, review_time, capture_id, manifest,
             weather, thermal, code_sha, env_sha, release_raw, release_signature) = self._validated_inputs(
                tenant, review_job_id, snapshot_id)
            review_at = _utc(review_time)
            clock = {"decision_id": decision_id, "decision_at_utc": context["decision_at_utc"],
                     "input_snapshot_id": snapshot_id,
                     "decision_context_id": context["decision_context_id"],
                     "claim_mode": context["claim_mode"],
                     "decision_time_kind": context["decision_time_kind"],
                     "review_at_utc": review_time}
            candidate = calculate_fixture(snapshot["manifest_raw"], snapshot["weather_raw"],
                snapshot["thermal_raw"], **clock)
            verify_replay(candidate, snapshot["manifest_raw"], snapshot["weather_raw"],
                snapshot["thermal_raw"], **clock)
            traces = [_parse(raw, canonical=True) for raw in candidate]
            rows = {row["fixture_id"]: row for row in manifest["files"]}
            _check_trace_sources(traces, weather, thermal, rows, review_at,
                {"decision_id": decision_id, "decision_at_utc": context["decision_at_utc"],
                 "review_at_utc": review_time,
                 "decision_context_id": context["decision_context_id"],
                 "claim_mode": context["claim_mode"],
                 "decision_time_kind": context["decision_time_kind"],
                 "input_snapshot_id": snapshot_id,
                 "manifest_sha256": snapshot["manifest_sha256"]})
            _check_physics(traces, weather, thermal)
            _need(traces[0]["run_status"] == traces[1]["run_status"] == "candidate" and
                  traces[0]["interval"]["end_utc"] == traces[1]["interval"]["start_utc"],
                  "TRACE_HOLD: candidate identity or adjacency")
            first, second = traces
            first["run_status"] = "accepted"
            first_raw = _json(first)
            first_sha = _hash(first_raw)
            second["run_status"] = "accepted"
            for field in ("temperature", "humidity_ratio"):
                carry = second["initial_state"][field]
                pointer = f"/steps/{len(first['steps']) - 1}/state_end/{field}"
                _need(carry["previous_trace_id"] == first["trace_id"] and
                      carry["previous_state_pointer"] == pointer and
                      carry["value"] == first["steps"][-1]["state_end"][field]["value"],
                      "TRACE_HOLD: untrusted candidate carry")
                carry["previous_trace_sha256"] = first_sha
                carry["basis_ref"] = f"trace-sha256:{first_sha}#{pointer}"
            second_raw = _json(second)
            _need(runtime_digests(self.root) == (code_sha, env_sha),
                  "PIN_HOLD: code or environment changed during calculation")
            schema = _parse((self.root / "contracts/thermal-v1.schema.json").read_bytes())
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            for accepted in (first, second):
                _need(not list(validator.iter_errors(accepted)),
                      "TRACE_HOLD: final bytes fail accepted schema")
            hashes = [_hash(first_raw), _hash(second_raw)]
            report = {
                "gate_version": "thermal-g1-publisher-v1", "status": "pass",
                "tenant_id": tenant,
                "run_id": first["run_id"], "snapshot_id": snapshot_id,
                "decision_id": decision_id,
                "decision_context_id": context["decision_context_id"],
                "context_sha256": context["context_sha256"],
                "decision_at_utc": context["decision_at_utc"],
                "review_at_utc": review_time,
                "claim_mode": context["claim_mode"],
                "decision_time_kind": context["decision_time_kind"],
                "review_job_id": str(review_job_id), "review_capture_id": capture_id,
                "manifest_sha256": snapshot["manifest_sha256"],
                "code_sha256": code_sha, "environment_sha256": env_sha,
                "release_sha256": _hash(release_raw), "trace_sha256": hashes,
            }
            report_raw = _json(report)
            gate_signature = hmac.new(self._gate_key,
                b"thermal-g1-gate-v1\0" + report_raw + b"\0" +
                hashes[0].encode() + hashes[1].encode(), sha256).hexdigest()
            return dict(report_raw=report_raw, gate_signature=gate_signature,
                release_raw=release_raw, release_signature=release_signature,
                trace_raws=(first_raw, second_raw))
        except Exception as exc:
            if isinstance(exc, ThermalPublishHold):
                raise
            raise ThermalPublishHold("G1_HOLD: source, trace or publication failed") from exc

    def publish(self, tenant, review_job_id, snapshot_id):
        try:
            return self.run_store.publish_verified(tenant,
                **self.prepare(tenant, review_job_id, snapshot_id))
        except Exception as exc:
            if isinstance(exc, ThermalPublishHold):
                raise
            raise ThermalPublishHold("G1_HOLD: source, trace or publication failed") from exc
