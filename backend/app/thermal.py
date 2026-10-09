"""Thermal-v1 synthetic candidate calculation; server gate acceptance is separate."""

from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json
from math import isfinite

from .thermal_units import quantity as q, saturation_pressure_pa, sourced, utc, validate_law_source


MANIFEST_SHA256 = "c84e3774bcfaa8904d3d96a5d00876ade6b6890271c8f614ef5e5f20ca79566f"
ENGINE_VERSION = "thermal-euler-v1"
UNIT_REGISTRY_VERSION = "thermal-si-nws-v1"
LIMITS = {
    "vapor_residual": (1.2e-13, "kg_v"),
    "aggregate_energy_residual": (4.5e-6, "J"),
    "temperature": (8.1e-5, "K"),
    "humidity_ratio": (5.4e-10, "kg_v/kg_da"),
    "delivered_heat_energy": (0, "J"),
}
PARAMETER_UNITS = {
    "effective_heat_capacity": ("J/K", 0), "dry_air_mass": ("kg_da", 0),
    "dry_air_specific_heat": ("J/(kg_da*K)", 0), "latent_heat": ("J/kg_v", 0),
    "envelope_conductance": ("W/K", 0), "indoor_volume": ("m³", 0),
    "floor_area": ("m²", 0), "absorbed_solar_fraction": ("1", 0),
    "dry_air_gas_constant": ("J/(kg_da*K)", 0),
    "vapor_gas_constant": ("J/(kg_v*K)", 0),
}
WEATHER_UNITS = {"T_o": "K", "phi_o": "1", "p_o": "Pa", "solar_interval_energy": "J/m²"}
SOURCE_UNITS = {
    "synthetic-weather-v1": WEATHER_UNITS,
    "synthetic-thermal-parameters-v1": {
        "temperature": "K", "humidity_ratio": "kg_v/kg_da", "heat": "W_th", "time": "s"
    },
}
DERIVED_RULE_BASIS = {
    "thermal-outdoor-w-v1": "synthetic-thermal-parameters-v1:/conversion_rules/outdoor_humidity_ratio",
    "thermal-solar-interval-v1": "synthetic-thermal-parameters-v1:/conversion_rules/solar_gain",
}


class ThermalHold(ValueError):
    """A candidate that cannot satisfy the frozen synthetic contract."""


def _need(condition, reason):
    if not condition:
        raise ThermalHold(reason)


def _value(record):
    return float(record["value"])


def _state(t, w):
    return {"temperature": q(t, "K"), "humidity_ratio": q(w, "kg_v/kg_da")}


def _indoor(state, parameters):
    t, w = state
    if not all(map(isfinite, state)) or t <= 0 or w < 0:
        raise ThermalHold("CONDENSATION_HOLD: invalid aggregate state")
    mass = _value(parameters["dry_air_mass"])
    volume = _value(parameters["indoor_volume"])
    rd = _value(parameters["dry_air_gas_constant"])
    rv = _value(parameters["vapor_gas_constant"])
    pressure = (mass / volume) * (rd + w * rv) * t
    vapor_pressure = (mass / volume) * w * rv * t
    try:
        saturation = saturation_pressure_pa(t, parameters["saturation_pressure_rule"])
    except ValueError as exc:
        raise ThermalHold("CONDENSATION_HOLD: indoor law domain") from exc
    except (AttributeError, KeyError, TypeError, OverflowError) as exc:
        raise ThermalHold("LAW_HOLD: malformed saturation rule") from exc
    if not isfinite(pressure) or not isfinite(vapor_pressure) or vapor_pressure >= saturation:
        raise ThermalHold("CONDENSATION_HOLD: bulk saturation or nonfinite pressure")
    return pressure, vapor_pressure / saturation


def _step_record(record, unit, *, lower=None, upper=None, sourced_input=False, derived_rule=None,
                 boolean=False):
    _need(isinstance(record, dict) and record.get("unit") == unit, f"UNIT_HOLD: expected {unit}")
    if sourced_input or derived_rule is not None:
        _need(type(record.get("basis_ref")) is str and bool(record["basis_ref"]) and
              type(record.get("version")) is str and bool(record["version"]),
              "INPUT_HOLD: malformed step provenance")
    if sourced_input:
        try:
            return sourced(record, unit, lower=lower, upper=upper, boolean=boolean)
        except ValueError as exc:
            raise ThermalHold(str(exc)) from exc
        except (OverflowError, TypeError) as exc:
            raise ThermalHold("INPUT_HOLD: malformed sourced step value") from exc
    if derived_rule is not None:
        identifiers = record.get("input_record_ids")
        _need(record.get("origin") == "derived" and
              record.get("basis_ref") == DERIVED_RULE_BASIS[derived_rule] and
              record.get("version") == "v1" and record.get("calculation_rule_ref") == derived_rule and
              record.get("calculation_rule_version") == "v1" and isinstance(identifiers, list) and
              bool(identifiers) and all(isinstance(identifier, str) and identifier for identifier in identifiers) and
              len(identifiers) == len(set(identifiers)),
              "REFERENCE_HOLD: incomplete derived forcing provenance")
    value = record.get("value")
    _need(type(value) in (int, float), "INPUT_HOLD: nonfinite or missing step value")
    try:
        numeric = float(value)
    except OverflowError as exc:
        raise ThermalHold("INPUT_HOLD: nonfinite or missing step value") from exc
    _need(isfinite(numeric), "INPUT_HOLD: nonfinite or missing step value")
    _need((lower is None or numeric >= lower) and (upper is None or numeric <= upper),
          "INPUT_HOLD: step value outside declared domain")
    return numeric


def euler_step(state, parameters, forcing, heater, dt):
    """Calculate one SI step from unit-bearing records; this does not approve a Run."""
    _need(all(isinstance(item, dict) for item in (state, parameters, forcing, heater)),
          "INPUT_HOLD: malformed step inputs")
    t = _step_record(state.get("temperature"), "K")
    w = _step_record(state.get("humidity_ratio"), "kg_v/kg_da")
    _need(t > 0 and w >= 0, "CONDENSATION_HOLD: invalid aggregate state")
    seconds = _step_record(dt, "s", lower=0)
    for name, (unit, lower) in PARAMETER_UNITS.items():
        value = _step_record(parameters.get(name), unit, lower=lower, sourced_input=True)
        _need(value > 0 if name not in ("envelope_conductance", "absorbed_solar_fraction") else True,
              "INPUT_HOLD: impossible parameter sign")
    _need(_value(parameters["absorbed_solar_fraction"]) <= 1,
          "INPUT_HOLD: solar fraction")
    _need(isinstance(parameters.get("saturation_pressure_rule"), dict),
          "LAW_HOLD: missing saturation rule")
    for name, unit, lower, upper in (
        ("outdoor_temperature", "K", 0, None),
        ("outdoor_relative_humidity", "1", 0, 1),
        ("outdoor_pressure", "Pa", 0, None),
        ("solar_interval_energy", "J/m²", 0, None),
        ("ventilation_dry_air_flow", "kg_da/s", 0, None),
        ("canopy_evaporation", "kg_v/s", 0, None),
        ("ground_heat_flow", "W", None, None),
    ):
        value = _step_record(forcing.get(name), unit, lower=lower, upper=upper, sourced_input=True)
        if name in ("outdoor_temperature", "outdoor_pressure"):
            _need(value > 0, "INPUT_HOLD: nonpositive outdoor value")
    _step_record(forcing.get("outdoor_humidity_ratio"), "kg_v/kg_da", lower=0,
                 derived_rule="thermal-outdoor-w-v1")
    _step_record(forcing.get("solar_gain"), "W", lower=0, derived_rule="thermal-solar-interval-v1")
    _need(heater.get("mode") == "indirect_sensible", "DIRECT_HEATER_HOLD")
    _need(heater.get("capacity_basis") == "delivered_thermal_power" and
          heater.get("control_version") == "thermal-indirect-sensible-end-target-v1",
          "INPUT_HOLD: unregistered heater control")
    _step_record(heater.get("capacity"), "W_th", lower=0, sourced_input=True)
    _step_record(heater.get("setpoint"), "K", lower=0, sourced_input=True)
    _step_record(heater.get("available"), "1", sourced_input=True, boolean=True)
    return _euler_step((t, w), parameters, forcing, heater, seconds)


def _euler_step(state, parameters, forcing, heater, dt):
    """Fixed operation-order binary64 arithmetic on validated SI values."""
    t, w = state
    C = _value(parameters["effective_heat_capacity"])
    M = _value(parameters["dry_air_mass"])
    cp = _value(parameters["dry_air_specific_heat"])
    latent = _value(parameters["latent_heat"])
    K = _value(parameters["envelope_conductance"])
    F = _value(forcing["ventilation_dry_air_flow"])
    E = _value(forcing["canopy_evaporation"])
    To = _value(forcing["outdoor_temperature"])
    wo = _value(forcing["outdoor_humidity_ratio"])
    solar = _value(forcing["solar_gain"])
    ground = _value(forcing["ground_heat_flow"])
    _need(isfinite(dt) and dt > 0 and dt * F / M <= 1 and dt * (K + F * cp) / C <= 1,
          "STABILITY_HOLD: invalid Euler substep")
    _indoor(state, parameters)
    sensible_without_heater = solar + K * (To - t) + ground + F * cp * (To - t) - latent * E
    demand = max(0.0, C * (_value(heater["setpoint"]) - t) / dt - sensible_without_heater)
    delivered = min(demand, _value(heater["capacity"])) if heater["available"]["value"] else 0.0
    unmet = max(demand - delivered, 0.0)
    mass_rate = F * (wo - w) + E
    next_w = w + dt * mass_rate / M
    next_t = t + dt * (sensible_without_heater + delivered) / C
    pressure, rh = _indoor((next_t, next_w), parameters)
    mass_terms = {
        "ventilation": q(dt * F * (wo - w), "kg_v"),
        "canopy_evaporation": q(dt * E, "kg_v"),
        "heater_vapor": q(0.0, "kg_v"),
        "condensation": q(0.0, "kg_v"),
    }
    heat_terms = {
        "solar": q(dt * solar, "J"), "heater": q(dt * delivered, "J"),
        "envelope": q(dt * K * (To - t), "J"), "ground": q(dt * ground, "J"),
        "ventilation_sensible": q(dt * F * cp * (To - t), "J"),
        "canopy_latent": q(-dt * latent * E, "J"),
    }
    mass_change = M * (next_w - w)
    mass_sum = sum(item["value"] for item in mass_terms.values())
    heat_sum = sum(item["value"] for item in heat_terms.values())
    vapor_residual = mass_change - mass_sum
    energy_residual = C * (next_t - t) + latent * mass_change - (heat_sum + latent * mass_sum)
    return {
        "state_start": _state(t, w), "state_end": _state(next_t, next_w),
        "indoor_pressure_end": q(pressure, "Pa"), "relative_humidity_end": q(rh, "1"),
        "heat_demand": q(demand, "W_th"), "heat_delivered": q(delivered, "W_th"),
        "heat_unmet": q(unmet, "W_th"),
        "delivered_heat_energy": q(delivered * dt / 3_600_000, "kWh_th"),
        "mass_terms": mass_terms, "heat_terms": heat_terms,
        "vapor_residual": q(vapor_residual, "kg_v"),
        "aggregate_energy_residual": q(energy_residual, "J"),
    }


def _field(record, unit, *, lower=None, upper=None):
    return sourced(record, unit, lower=lower, upper=upper)


def _preflight(thermal, weather):
    _need(thermal.get("heater", {}).get("mode") == "indirect_sensible", "DIRECT_HEATER_HOLD")
    _need(thermal["heater"].get("capacity_basis") == "delivered_thermal_power" and
          thermal["heater"].get("control_version") == "thermal-indirect-sensible-end-target-v1",
          "INPUT_HOLD: unregistered heater control")
    p = thermal["parameters"]
    for name, (unit, lower) in PARAMETER_UNITS.items():
        value = _field(p.get(name), unit, lower=lower)
        _need(value > 0 if name not in ("envelope_conductance", "absorbed_solar_fraction") else True,
              "INPUT_HOLD: impossible parameter sign")
    _need(_value(p["absorbed_solar_fraction"]) <= 1, "INPUT_HOLD: solar fraction")
    _field(thermal["initial_state"].get("temperature"), "K", lower=0)
    _field(thermal["initial_state"].get("humidity_ratio"), "kg_v/kg_da", lower=0)
    _field(thermal["heater"].get("capacity"), "W_th", lower=0)
    _field(thermal["heater"].get("setpoint"), "K", lower=0)
    sourced(thermal["heater"].get("available"), "1", boolean=True)
    _need(thermal.get("condensation_policy") == "hold_on_saturation", "CONDENSATION_HOLD")
    integration = thermal["integration"]
    _need(integration.get("method") == "explicit_euler" and
          integration.get("stability_rule_ref") == "thermal-euler-stability-v1" and
          integration.get("residual_rule_ref") == "thermal-binary64-residual-v1",
          "RULE_HOLD: missing numerical rule")
    dt = _field(integration.get("substep"), "s", lower=0)
    _need(dt == 60, "RULE_HOLD: fixed 60 s step required")
    for group, names in (("residual_tolerances", ("vapor_residual", "aggregate_energy_residual")),
                         ("step_convergence_tolerances", ("temperature", "humidity_ratio", "delivered_heat_energy"))):
        entry = integration[group]
        _need(entry.get("rule_version") == "v1" and "pre-registered" in entry.get("rationale", ""),
              "RULE_HOLD: unregistered limit rationale")
        for name in names:
            expected, unit = LIMITS[name]
            _need(_field(entry.get(name), unit, lower=0) == expected, "RULE_HOLD: changed preregistered limit")
    validate_law_source(thermal["law_source"])
    for hour in weather["intervals"]:
        values = hour.get("values", {})
        for name, unit in WEATHER_UNITS.items():
            if name not in values:
                raise ThermalHold("INPUT_HOLD: missing weather value")
            value = _field(values[name], unit)
            if name == "solar_interval_energy" and value < 0:
                raise ThermalHold("SOLAR_HOLD: negative interval energy")
            if name == "phi_o":
                _need(0 <= value <= 1, "INPUT_HOLD: relative humidity outside [0,1]")
            if name in ("T_o", "p_o"):
                _need(value > 0, "INPUT_HOLD: nonpositive weather value")
    for interval in thermal["intervals"]:
        forcing = interval["assumed_forcing"]
        _field(forcing.get("ventilation_dry_air_flow"), "kg_da/s", lower=0)
        _field(forcing.get("canopy_evaporation"), "kg_v/s", lower=0)
        _field(forcing.get("ground_heat_flow"), "W")
    if len(thermal["intervals"]) != len(weather["intervals"]) or not all(
        left.get("start_utc") == right.get("start_utc") and
        left.get("end_utc") == right.get("end_utc")
        for left, right in zip(thermal["intervals"], weather["intervals"])
    ):
        raise ThermalHold("TIMESTAMP_HOLD: thermal/weather forcing interval differs")
    previous_end = utc(weather["start_utc"])
    for hour in weather["intervals"]:
        start, end = utc(hour["start_utc"]), utc(hour["end_utc"])
        if start != previous_end or not start < end or (end - start).total_seconds() != 3600:
            raise ThermalHold("TIMESTAMP_HOLD: forcing gap, overlap, or duration")
        previous_end = end
    if previous_end != utc(weather["end_utc"]):
        raise ThermalHold("TIMESTAMP_HOLD: weather coverage differs")


def _read_inputs(manifest_raw, weather_raw, thermal_raw, review_at_utc, *,
                 decision_at_utc=None, claim_mode=None):
    try:
        manifest, weather, thermal = (json.loads(raw) for raw in (manifest_raw, weather_raw, thermal_raw))
        review_at = utc(review_at_utc)
        decision_at = utc(decision_at_utc) if decision_at_utc is not None else None
        _preflight(thermal, weather)
        _need(manifest.get("claim_scope") == "synthetic_g1_software_input_only" and
              manifest.get("synthetic_input_review_id"), "REVIEW_HOLD: synthetic scope/review missing")
        rows = {row["fixture_id"]: row for row in manifest["files"]}
        _need(len(rows) == len(manifest["files"]) and set(rows) == set(SOURCE_UNITS) | {"synthetic-economics-v1"},
              "PIN_HOLD: fixture inventory differs")
        for row in (rows["synthetic-weather-v1"], rows["synthetic-thermal-parameters-v1"]):
            _need(row["review"]["review_id"] == manifest["synthetic_input_review_id"] and
                  row["review"]["status"] == "self_reviewed_synthetic" and
                  row["review"]["reviewer"] and row["qc"]["status"] == "self_checked_synthetic",
                  "REVIEW_HOLD: source self-review/QC")
        _need(sha256(manifest_raw).hexdigest() == MANIFEST_SHA256, "PIN_HOLD: manifest bytes differ")
        for fixture, raw in ((weather, weather_raw), (thermal, thermal_raw)):
            row = rows[fixture["fixture_id"]]
            digest = sha256(raw).hexdigest()
            _need(row["sha256"] == digest and row["byte_length"] == len(raw) and
                  row["content_id"] == f"sha256:{digest}" and
                  row["path"] == row["source_locator"] == f"fixtures/{fixture['fixture_id']}.json",
                  "PIN_HOLD: fixture raw bytes differ")
            _need(row["synthetic"] is True and fixture["synthetic"] is True and
                  row["observed_start_utc"] is None and row["observed_end_utc"] is None and
                  row["variable_units"] == SOURCE_UNITS[fixture["fixture_id"]],
                  "SOURCE_HOLD: synthetic source metadata")
            _need(row["review"]["review_id"] == manifest["synthetic_input_review_id"] and
                  row["review"]["status"] == "self_reviewed_synthetic" and row["review"]["reviewer"] and
                  row["qc"]["status"] == "self_checked_synthetic", "REVIEW_HOLD: source self-review/QC")
            _need(row["rights"].get("license") == "Apache-2.0" and
                  row["rights"].get("holder") == manifest["author"] and
                  all(row["rights"].get(key) == "allowed" for key in
                      ("access", "store", "transform", "display", "redistribute")),
                  "RIGHTS_HOLD: source use rights")
            for item in (manifest, row):
                _need(utc(item["published_at_utc"]) <= utc(item["available_at_utc"])
                      <= utc(item["retrieved_at_utc"]) <= review_at,
                      "TIMESTAMP_HOLD: source chronology or review cutoff")
                if claim_mode == "ex_ante":
                    _need(utc(item["available_at_utc"]) <= decision_at,
                          "TIMESTAMP_HOLD: source unavailable at planning decision")
            _need(utc(row["applicability_start_utc"]) < utc(row["applicability_end_utc"]),
                  "TIMESTAMP_HOLD: invalid applicability")
        return manifest, weather, thermal, rows
    except ThermalHold:
        raise
    except (ValueError, KeyError, TypeError, IndexError, AttributeError, OverflowError,
            ZeroDivisionError) as exc:
        if isinstance(exc, ValueError) and "_HOLD" in str(exc):
            raise ThermalHold(str(exc)) from exc
        raise ThermalHold("INPUT_HOLD: malformed synthetic input") from exc


def _resolve_records(thermal, weather, hour):
    file_by_id = {thermal["fixture_id"]: thermal, weather["fixture_id"]: weather}
    records = thermal["input_records"]
    ids = [record["record_id"] for record in records]
    _need(len(ids) == len(set(ids)), "REFERENCE_HOLD: duplicate input ID")
    by_id = {}
    for record in records:
        file_id, pointer = record["file_id"], record["json_pointer"]
        _need(record["record_id"] == f"{file_id}:{pointer}" and file_id in file_by_id and pointer.startswith("/"),
              "REFERENCE_HOLD: unpinned input ID")
        node = file_by_id[file_id]
        try:
            for token in pointer[1:].split("/"):
                node = node[int(token)] if isinstance(node, list) else node[token]
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise ThermalHold("REFERENCE_HOLD: unresolved input pointer") from exc
        by_id[record["record_id"]] = node
    interval = thermal["intervals"][hour]
    weather_prefix = f"{weather['fixture_id']}:/intervals/{hour}"
    parameter_prefix = f"{thermal['fixture_id']}:/parameters/"
    expected = {
        "outdoor_humidity_ratio": [
            *(weather_prefix + "/values/" + name for name in ("T_o", "phi_o", "p_o")),
            *(parameter_prefix + name for name in ("dry_air_gas_constant", "vapor_gas_constant", "saturation_pressure_rule")),
        ],
        "solar_gain": [
            weather_prefix + "/values/solar_interval_energy", weather_prefix + "/start_utc",
            weather_prefix + "/end_utc", parameter_prefix + "floor_area",
            parameter_prefix + "absorbed_solar_fraction",
        ],
    }
    for name, expected_ids in expected.items():
        plan = interval["derived_forcing"][name]
        rule = thermal["conversion_rules"][name]
        _need(plan["input_record_ids"] == expected_ids and all(identifier in by_id for identifier in expected_ids)
              and plan["calculation_rule_ref"] == rule["rule_ref"]
              and plan["calculation_rule_version"] == rule["version"] == "v1",
              "REFERENCE_HOLD: derived forcing IDs/rule mismatch")
    return interval


def _source_record(row, source_id, start, end):
    return {
        "id": source_id, "source_locator": row["source_locator"], "product_id": row["product_id"],
        "author": row["author"], "synthetic": True,
        "observed_start_utc": None, "observed_end_utc": None,
        "applicability_start_utc": start, "applicability_end_utc": end,
        "published_at_utc": row["published_at_utc"], "available_at_utc": row["available_at_utc"],
        "retrieved_at_utc": row["retrieved_at_utc"], "vintage": row["vintage_id"],
        "revision": row["revision_id"], "original_unit": deepcopy(row["variable_units"]),
        "provider_qc": {"status": "not_applicable", "detail": "self-authored synthetic input"},
        "project_qc": {"status": "pass", "rule_version": "synthetic-fixture-qc-v1",
                       "detail": "Pinned author self-check; server review remains separate"},
        "raw_sha256": row["sha256"], "normalization_rule_ref": "synthetic-identity-si-v1",
        "rights": {"use": "allowed", "display": row["rights"]["display"],
                   "redistribute": row["rights"]["redistribute"]},
        "reviewer": row["review"]["reviewer"],
    }


def _sourced_copy(record):
    return {key: record[key] for key in ("value", "unit", "origin", "basis_ref", "version")}


def _iso(moment):
    return moment.isoformat(timespec="seconds").replace("+00:00", "Z")


def calculate_fixture(manifest_raw, weather_raw, thermal_raw, *, decision_id, decision_at_utc,
                      input_snapshot_id, decision_context_id=None, claim_mode=None,
                      decision_time_kind=None, review_at_utc=None):
    """Build two immutable synthetic candidates; only a server can issue G1 acceptance."""
    _need(type(decision_id) is str and bool(decision_id) and
          type(input_snapshot_id) is str and bool(input_snapshot_id),
          "INPUT_HOLD: invalid decision/snapshot ID")
    context_fields = (decision_context_id, claim_mode, decision_time_kind, review_at_utc)
    contextual = any(value is not None for value in context_fields)
    if contextual:
        _need(type(decision_context_id) is str and bool(decision_context_id) and
              type(claim_mode) is str and claim_mode in ("ex_ante", "ex_post_replay") and
              type(decision_time_kind) is str and decision_time_kind in ("actual", "hypothetical") and
              type(review_at_utc) is str,
              "INPUT_HOLD: incomplete or invalid decision context")
        try:
            _need(utc(decision_at_utc) <= utc(review_at_utc),
                  "TIMESTAMP_HOLD: planning decision after review")
        except ValueError as exc:
            raise ThermalHold(str(exc)) from exc
    manifest, weather, thermal, rows = _read_inputs(
        manifest_raw, weather_raw, thermal_raw,
        review_at_utc if contextual else decision_at_utc,
        decision_at_utc=decision_at_utc if contextual else None,
        claim_mode=claim_mode if contextual else None,
    )
    _need(len(weather["intervals"]) == len(thermal["intervals"]) == 2,
          "TIMESTAMP_HOLD: exactly two forcing hours required")
    _need(weather["start_utc"] == thermal["intervals"][0]["start_utc"] and
          weather["end_utc"] == thermal["intervals"][-1]["end_utc"],
          "TIMESTAMP_HOLD: fixture coverage differs")
    parameter_row = rows[thermal["fixture_id"]]
    weather_row = rows[weather["fixture_id"]]
    parameter_start, parameter_end = (utc(parameter_row[key]) for key in
                                      ("applicability_start_utc", "applicability_end_utc"))
    manifest_digest = sha256(manifest_raw).hexdigest()
    run_identity = {
        "decision_at_utc": decision_at_utc, "decision_id": decision_id,
        "engine_version": ENGINE_VERSION, "input_snapshot_id": input_snapshot_id,
        "manifest_sha256": manifest_digest, "unit_registry_version": UNIT_REGISTRY_VERSION,
    }
    if contextual:
        run_identity.update(decision_context_id=decision_context_id,
                            claim_mode=claim_mode, decision_time_kind=decision_time_kind,
                            review_at_utc=review_at_utc, model_version="thermal-v1",
                            parameter_set_version=thermal["fixture_id"])
    run_id = "synthetic-thermal-v1:" + sha256(json.dumps(
        run_identity, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")).hexdigest()
    raw_traces = []
    state = (_value(thermal["initial_state"]["temperature"]),
             _value(thermal["initial_state"]["humidity_ratio"]))
    _indoor(state, thermal["parameters"])
    previous = None
    for hour, (weather_hour, thermal_hour) in enumerate(zip(weather["intervals"], thermal["intervals"])):
        start, end = utc(weather_hour["start_utc"]), utc(weather_hour["end_utc"])
        _need(start < end and (end - start).total_seconds() == 3600 and
              weather_hour["start_utc"] == thermal_hour["start_utc"] and
              weather_hour["end_utc"] == thermal_hour["end_utc"] and
              thermal_hour["weather_ref"] == {"fixture_id": weather["fixture_id"], "interval_index": hour} and
              (hour == 0 or start == utc(weather["intervals"][hour - 1]["end_utc"])) and
              parameter_start <= start < end <= parameter_end and
              utc(weather_row["applicability_start_utc"]) <= start < end <= utc(weather_row["applicability_end_utc"]),
              "TIMESTAMP_HOLD: gap, overlap, or source interval mismatch")
        _resolve_records(thermal, weather, hour)
        raw = weather_hour["values"]
        p = thermal["parameters"]
        outdoor_t = _value(raw["T_o"])
        outdoor_p = _value(raw["p_o"])
        phi = _value(raw["phi_o"])
        eo = phi * saturation_pressure_pa(outdoor_t, p["saturation_pressure_rule"])
        _need(outdoor_p > eo, "INPUT_HOLD: outdoor pressure <= vapor pressure")
        outdoor_w = (_value(p["dry_air_gas_constant"]) / _value(p["vapor_gas_constant"])) * eo / (outdoor_p - eo)
        solar = (_value(raw["solar_interval_energy"]) * _value(p["floor_area"])
                 * _value(p["absorbed_solar_fraction"]) / (end - start).total_seconds())
        forcing = {
            "outdoor_temperature": _sourced_copy(raw["T_o"]),
            "outdoor_relative_humidity": _sourced_copy(raw["phi_o"]),
            "outdoor_pressure": _sourced_copy(raw["p_o"]),
            "solar_interval_energy": _sourced_copy(raw["solar_interval_energy"]),
            **deepcopy(thermal_hour["assumed_forcing"]),
        }
        for name, value, unit in (("outdoor_humidity_ratio", outdoor_w, "kg_v/kg_da"),
                                  ("solar_gain", solar, "W")):
            plan = thermal_hour["derived_forcing"][name]
            rule = thermal["conversion_rules"][name]
            forcing[name] = {
                "value": value, "unit": unit, "origin": "derived",
                "basis_ref": f"{thermal['fixture_id']}:/conversion_rules/{name}",
                "version": rule["version"], "calculation_rule_ref": rule["rule_ref"],
                "calculation_rule_version": plan["calculation_rule_version"],
                "input_record_ids": plan["input_record_ids"][:],
            }
        initial = deepcopy(thermal["initial_state"]) if hour == 0 else {}
        if previous is not None:
            previous_raw, previous_trace = previous
            digest = sha256(previous_raw).hexdigest()
            for name in ("temperature", "humidity_ratio"):
                pointer = f"/steps/{len(previous_trace['steps']) - 1}/state_end/{name}"
                initial[name] = {
                    "value": previous_trace["steps"][-1]["state_end"][name]["value"],
                    "unit": previous_trace["steps"][-1]["state_end"][name]["unit"],
                    "origin": "derived", "basis_ref": f"trace-sha256:{digest}#{pointer}",
                    "version": "v1", "calculation_rule_ref": "thermal-state-carry-v1",
                    "calculation_rule_version": "v1", "previous_trace_id": previous_trace["trace_id"],
                    "previous_trace_sha256": digest, "previous_state_pointer": pointer,
                }
        steps = []
        step_start = start
        dt = _value(thermal["integration"]["substep"])
        while step_start < end:
            step_end = step_start + timedelta(seconds=dt)
            _need(step_end <= end, "TIMESTAMP_HOLD: nonintegral final step")
            whole = euler_step(_state(*state), p, forcing, thermal["heater"], q(dt, "s"))
            first_half = euler_step(_state(*state), p, forcing, thermal["heater"], q(dt / 2, "s"))
            half_state = (first_half["state_end"]["temperature"]["value"],
                          first_half["state_end"]["humidity_ratio"]["value"])
            second_half = euler_step(_state(*half_state), p, forcing, thermal["heater"], q(dt / 2, "s"))
            deltas = {
                "temperature": q(abs(whole["state_end"]["temperature"]["value"] -
                                     second_half["state_end"]["temperature"]["value"]), "K"),
                "humidity_ratio": q(abs(whole["state_end"]["humidity_ratio"]["value"] -
                                        second_half["state_end"]["humidity_ratio"]["value"]), "kg_v/kg_da"),
                "delivered_heat_energy": q(abs(whole["heat_terms"]["heater"]["value"] -
                                               first_half["heat_terms"]["heater"]["value"] -
                                               second_half["heat_terms"]["heater"]["value"]), "J"),
            }
            for name, record in (("vapor_residual", whole["vapor_residual"]),
                                 ("aggregate_energy_residual", whole["aggregate_energy_residual"]),
                                 *deltas.items()):
                _need(record["value"] <= LIMITS[name][0] if name in deltas else abs(record["value"]) <= LIMITS[name][0],
                      "NUMERICAL_HOLD: preregistered residual/convergence limit exceeded")
            whole.update(start_utc=_iso(step_start), end_utc=_iso(step_end),
                         convergence_deltas=deltas, acceptance_rule_version="v1")
            steps.append(whole)
            state = (whole["state_end"]["temperature"]["value"],
                     whole["state_end"]["humidity_ratio"]["value"])
            step_start = step_end
        trace = {
            "contract_version": "thermal-v1", "model_origin": "project_aggregate_v1",
            "claim_scope": "synthetic_g1_contract_trace", "run_status": "candidate",
            "scope": {"thermal_control_volumes": 1, "boundary": "dry_air_plus_canopy",
                      "dynamic_states": ["temperature", "humidity_ratio"]},
            "run_id": run_id, "trace_id": f"{run_id}:hour-{hour}", "trace_sequence_index": hour,
            "input_snapshot_id": input_snapshot_id, "decision_id": decision_id,
            "model_version": "thermal-v1", "parameter_set_version": thermal["fixture_id"],
            "engine_version": ENGINE_VERSION, "unit_registry_version": UNIT_REGISTRY_VERSION,
            "manifest_sha256": manifest_digest,
            "synthetic_input_review_id": manifest["synthetic_input_review_id"],
            "source_records": [
                _source_record(weather_row, f"{weather['fixture_id']}:/intervals/{hour}",
                               weather_hour["start_utc"], weather_hour["end_utc"]),
                _source_record(parameter_row, thermal["fixture_id"],
                               parameter_row["applicability_start_utc"],
                               parameter_row["applicability_end_utc"]),
            ],
            "interval": {"start_utc": weather_hour["start_utc"], "end_utc": weather_hour["end_utc"]},
            "initial_state": initial, "parameters": deepcopy(p), "forcing": forcing,
            "heater": deepcopy(thermal["heater"]), "condensation_policy": "hold_on_saturation",
            "integration": deepcopy(thermal["integration"]), "steps": steps,
        }
        if contextual:
            trace.update(decision_context_id=decision_context_id,
                         decision_at_utc=decision_at_utc,
                         review_at_utc=review_at_utc, claim_mode=claim_mode,
                         decision_time_kind=decision_time_kind)
        trace_raw = json.dumps(trace, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                               allow_nan=False).encode("utf-8")
        raw_traces.append(trace_raw)
        previous = trace_raw, trace
    return tuple(raw_traces)


def verify_replay(trace_raw_bytes, manifest_raw, weather_raw, thermal_raw, *, decision_id,
                  decision_at_utc, input_snapshot_id, decision_context_id=None,
                  claim_mode=None, decision_time_kind=None, review_at_utc=None):
    """Compare complete immutable trace bytes against a fresh deterministic calculation."""
    expected = calculate_fixture(manifest_raw, weather_raw, thermal_raw,
                                 decision_id=decision_id, decision_at_utc=decision_at_utc,
                                 input_snapshot_id=input_snapshot_id,
                                 decision_context_id=decision_context_id,
                                 claim_mode=claim_mode,
                                 decision_time_kind=decision_time_kind,
                                 review_at_utc=review_at_utc)
    if not isinstance(trace_raw_bytes, (tuple, list)) or len(trace_raw_bytes) != 2 or any(
        type(raw) is not bytes or raw != generated for raw, generated in zip(trace_raw_bytes, expected)
    ):
        raise ThermalHold("REPLAY_HOLD: trace set or raw bytes differ")
    return True
