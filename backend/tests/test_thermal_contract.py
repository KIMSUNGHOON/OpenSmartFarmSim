"""Contract checks for the proposed synthetic G1 thermal trace."""

import json
import hashlib
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "contracts"
ARTIFACTS = (
    CONTRACTS / "thermal-v1.md",
    CONTRACTS / "thermal-v1.schema.json",
    CONTRACTS / "thermal-sources.md",
)


@pytest.fixture(scope="module")
def contract():
    missing = [str(path.relative_to(ROOT)) for path in ARTIFACTS if not path.is_file()]
    assert not missing, f"Missing thermal contract artifacts: {', '.join(missing)}"
    model_text = ARTIFACTS[0].read_text(encoding="utf-8")
    schema = json.loads(ARTIFACTS[1].read_text(encoding="utf-8"))
    sources_text = ARTIFACTS[2].read_text(encoding="utf-8")
    return schema, model_text, sources_text


def resolved(schema, node):
    while "$ref" in node:
        ref = node["$ref"]
        assert ref.startswith("#/$defs/"), f"Contract reference must be local: {ref}"
        node = schema["$defs"][ref.removeprefix("#/$defs/")]
    return node


def field(schema, node, name):
    parent = resolved(schema, node)
    assert name in parent["properties"], f"Missing contract field: {name}"
    return resolved(schema, parent["properties"][name])


def requires(schema, node, *names):
    parent = resolved(schema, node)
    assert parent["type"] == "object"
    assert set(names) <= set(parent["required"])
    assert parent["additionalProperties"] is False


def quantity(schema, node, unit, *, sourced=False):
    names = ("value", "unit", "origin", "basis_ref", "version") if sourced else ("value", "unit")
    requires(schema, node, *names)
    assert field(schema, node, "value")["type"] == "number"
    assert field(schema, node, "unit")["const"] == unit
    if sourced:
        assert {"measured", "literature", "assumed"} <= set(
            field(schema, node, "origin")["enum"]
        )


def test_schema_declares_project_scope_and_synthetic_claim_only(contract):
    schema, _, _ = contract
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    requires(
        schema, schema, "contract_version", "model_origin", "claim_scope", "scope",
        "interval", "initial_state", "parameters", "forcing", "heater",
        "condensation_policy", "integration", "steps",
    )
    assert field(schema, schema, "model_origin")["const"] == "project_aggregate_v1"
    assert field(schema, schema, "claim_scope")["const"] == "synthetic_g1_contract_trace"
    scope = field(schema, schema, "scope")
    requires(schema, scope, "thermal_control_volumes")
    assert field(schema, scope, "thermal_control_volumes")["const"] == 1


def test_accepted_shape_requires_explicit_decision_and_review_clocks(contract):
    schema, _, _ = contract
    requires(schema, schema, "decision_id", "decision_context_id", "decision_at_utc",
             "review_at_utc", "claim_mode", "decision_time_kind")
    assert field(schema, schema, "claim_mode")["enum"] == ["ex_ante", "ex_post_replay"]
    assert set(field(schema, schema, "decision_time_kind")["enum"]) == {"actual", "hypothetical"}
    for name in ("decision_at_utc", "review_at_utc"):
        timestamp = field(schema, schema, name)
        assert timestamp["type"] == "string"
        assert timestamp["format"] == "date-time"
        assert timestamp["pattern"].endswith("Z$")
    candidate = schema_shaped_synthetic_candidate(schema)
    validator = Draft202012Validator(schema)
    assert validator.is_valid(candidate)
    for name in ("decision_context_id", "decision_at_utc", "review_at_utc",
                 "claim_mode", "decision_time_kind"):
        stripped = deepcopy(candidate)
        stripped.pop(name)
        assert not validator.is_valid(stripped)


def test_utc_interval_and_two_required_initial_states(contract):
    schema, model, _ = contract
    interval = field(schema, schema, "interval")
    requires(schema, interval, "start_utc", "end_utc")
    for name in ("start_utc", "end_utc"):
        timestamp = field(schema, interval, name)
        assert timestamp["type"] == "string"
        assert timestamp["format"] == "date-time"
        assert timestamp["pattern"].endswith("Z$")
    assert "end_utc > start_utc" in model

    state = field(schema, schema, "initial_state")
    requires(schema, state, "temperature", "humidity_ratio")
    assert set(state["properties"]) == {"temperature", "humidity_ratio"}
    for name, unit in (("temperature", "K"), ("humidity_ratio", "kg_v/kg_da")):
        options = field(schema, state, name)["oneOf"]
        assert len(options) == 2
        quantity(schema, options[0], unit, sourced=True)
        carried = resolved(schema, options[1])
        requires(schema, carried, "value", "unit", "origin", "basis_ref", "version", "calculation_rule_ref",
                 "calculation_rule_version", "previous_trace_id", "previous_trace_sha256",
                 "previous_state_pointer")
        assert carried["properties"]["origin"]["const"] == "derived"
        assert carried["properties"]["version"]["const"] == "v1"
        assert "trace-sha256:" in carried["properties"]["basis_ref"]["pattern"]


def test_physical_parameters_have_units_and_external_basis_without_defaults(contract):
    schema, _, _ = contract
    parameters = field(schema, schema, "parameters")
    units = {
        "effective_heat_capacity": "J/K",
        "dry_air_mass": "kg_da",
        "dry_air_specific_heat": "J/(kg_da*K)",
        "latent_heat": "J/kg_v",
        "envelope_conductance": "W/K",
    }
    requires(schema, parameters, *units)
    for name, unit in units.items():
        quantity(schema, field(schema, parameters, name), unit, sourced=True)

    def no_defaults(node):
        if isinstance(node, dict):
            assert "default" not in node
            for child in node.values():
                no_defaults(child)
        elif isinstance(node, list):
            for child in node:
                no_defaults(child)

    no_defaults(schema)


def test_forcing_separates_vapor_and_heat_sources_with_units(contract):
    schema, _, _ = contract
    forcing = field(schema, schema, "forcing")
    units = {
        "outdoor_temperature": "K",
        "outdoor_humidity_ratio": "kg_v/kg_da",
        "ventilation_dry_air_flow": "kg_da/s",
        "canopy_evaporation": "kg_v/s",
        "solar_gain": "W",
        "ground_heat_flow": "W",
    }
    requires(schema, forcing, *units)
    for name, unit in units.items():
        quantity(
            schema, field(schema, forcing, name), unit,
            sourced=name not in {"outdoor_humidity_ratio", "solar_gain"},
        )


def test_heater_capacity_is_delivered_heat_and_unsupported_wet_modes_hold(contract):
    schema, model, _ = contract
    heater = field(schema, schema, "heater")
    requires(schema, heater, "mode", "capacity", "capacity_basis", "available", "setpoint")
    assert field(schema, heater, "mode")["const"] == "indirect_sensible"
    assert field(schema, heater, "capacity_basis")["const"] == "delivered_thermal_power"
    availability = field(schema, heater, "available")
    requires(schema, availability, "value", "unit", "origin", "basis_ref", "version")
    assert field(schema, availability, "value")["type"] == "boolean"
    assert field(schema, availability, "unit")["const"] == "1"
    assert "assumed" in field(schema, availability, "origin")["enum"]
    quantity(schema, field(schema, heater, "capacity"), "W_th", sourced=True)
    quantity(schema, field(schema, heater, "setpoint"), "K", sourced=True)
    assert field(schema, schema, "condensation_policy")["const"] == "hold_on_saturation"
    for decision in ("CONDENSATION_HOLD", "DIRECT_HEATER_HOLD", "heater_vapor"):
        assert decision in model


def test_integration_and_trace_expose_balances_with_correct_dimensions(contract):
    schema, model, _ = contract
    integration = field(schema, schema, "integration")
    requires(schema, integration, "method", "substep", "stability_rule_ref", "residual_rule_ref")
    assert field(schema, integration, "method")["const"] == "explicit_euler"
    quantity(schema, field(schema, integration, "substep"), "s", sourced=True)

    steps = field(schema, schema, "steps")
    assert steps["type"] == "array"
    assert steps["minItems"] >= 1
    step = resolved(schema, steps["items"])
    requires(
        schema, step, "state_end", "heat_demand", "heat_delivered", "heat_unmet",
        "delivered_heat_energy", "mass_terms", "heat_terms", "vapor_residual",
        "aggregate_energy_residual",
    )
    state_end = field(schema, step, "state_end")
    requires(schema, state_end, "temperature", "humidity_ratio")
    assert set(state_end["properties"]) == {"temperature", "humidity_ratio"}
    quantity(schema, field(schema, state_end, "temperature"), "K")
    quantity(schema, field(schema, state_end, "humidity_ratio"), "kg_v/kg_da")
    for name in ("heat_demand", "heat_delivered", "heat_unmet"):
        quantity(schema, field(schema, step, name), "W_th")
    quantity(schema, field(schema, step, "delivered_heat_energy"), "kWh_th")
    quantity(schema, field(schema, step, "vapor_residual"), "kg_v")
    quantity(schema, field(schema, step, "aggregate_energy_residual"), "J")

    mass = field(schema, step, "mass_terms")
    requires(schema, mass, "ventilation", "canopy_evaporation", "heater_vapor", "condensation")
    for name in mass["required"]:
        quantity(schema, field(schema, mass, name), "kg_v")
    heat = field(schema, step, "heat_terms")
    requires(schema, heat, "solar", "heater", "envelope", "ground", "ventilation_sensible", "canopy_latent")
    for name in heat["required"]:
        quantity(schema, field(schema, heat, name), "J")
    assert "vapor_residual" in model and "aggregate_energy_residual" in model


def test_model_document_states_boundary_latent_location_and_heat_limit(contract):
    _, model, _ = contract
    for term in ("C_eff", "M_da", "E_canopy", "latent_draw_from_aggregate", "Q_demand", "Q_delivered", "Q_unmet", "P_cap"):
        assert term in model
    assert "0 <= Q_delivered <= P_cap" in model
    assert "kWh_th" in model and "kWh_e" in model


def test_source_ledger_distinguishes_original_from_proposed_model(contract):
    _, model, sources = contract

    def row(identifier):
        rows = [line for line in sources.splitlines() if line.strip().startswith(f"| {identifier} |")]
        assert len(rows) == 1, f"Expected one source ledger row for {identifier}"
        return rows[0]

    original = row("WUR_ORIGINAL")
    aggregate = row("PROJECT_AGGREGATE")
    assert "https://edepot.wur.nl/170301" in original
    assert "original_reference" in original
    assert "proposed_aggregate" in aggregate
    assert "WUR_ORIGINAL" in model and "PROJECT_AGGREGATE" in model
    assert "https://handbook.ashrae.org/Handbooks/F17/SI/f17_ch01/f17_ch01_si.aspx" in sources
    assert "https://json-schema.org/draft/2020-12/json-schema-core" in sources
    assert "https://json-schema.org/draft/2020-12/json-schema-validation" in sources


def schema_shaped_synthetic_candidate(schema):
    """Build a nonphysical shape sentinel; this is never a thermal fixture."""

    def sentinel(node):
        node = resolved(schema, node)
        if "oneOf" in node:
            return sentinel(node["oneOf"][0])
        if "const" in node:
            return deepcopy(node["const"])
        if "enum" in node:
            return "assumed" if "assumed" in node["enum"] else node["enum"][0]
        if node["type"] == "object":
            return {name: sentinel(node["properties"][name]) for name in node["required"]}
        if node["type"] == "array":
            return [sentinel(node["items"]) for _ in range(node.get("minItems", 0))]
        if node["type"] == "boolean":
            return True
        if node["type"] == "null":
            return None
        if node["type"] == "number":
            return 0 if node.get("exclusiveMaximum") == 1 else 1
        if node["type"] == "integer":
            return 0
        if node["type"] == "string":
            if node.get("format") == "date-time":
                return "2026-01-01T00:00:00Z"
            if "[0-9a-f]{64}" in node.get("pattern", ""):
                return "0" * 64
            return "shape-only"
        raise AssertionError(f"Unsupported schema node: {node}")

    candidate = sentinel(schema)
    candidate["synthetic_input_review_id"] = "shape-only-synthetic-review"
    source = candidate["source_records"][0]
    source["synthetic"] = True
    source["source_locator"] = "urn:self-authored:shape-only"
    source["product_id"] = "shape-only"
    source["author"] = "shape-only-author"
    source["normalization_rule_ref"] = "shape-only-normalization"
    source["provider_qc"]["status"] = "not_applicable"
    source["project_qc"]["status"] = "pass"
    source["rights"] = {name: "allowed" for name in ("use", "display", "redistribute")}
    source["reviewer"] = "shape-only-reviewer"
    source["observed_start_utc"] = None
    source["observed_end_utc"] = None
    return candidate


def fixture_linked_temporal_candidate(schema, hour_index=0):
    """Schema-shaped sentinel with real fixture metadata; no engine output is implied."""
    manifest_raw = (ROOT / "fixtures/manifest-v2.json").read_bytes()
    weather_raw = (ROOT / "fixtures/synthetic-weather-v1.json").read_bytes()
    manifest = json.loads(manifest_raw)
    weather = json.loads(weather_raw)
    thermal = json.loads((ROOT / "fixtures/synthetic-thermal-parameters-v1.json").read_bytes())
    interval = thermal["intervals"][hour_index]
    candidate = candidate_with_derived_forcing(schema)
    candidate.update(decision_context_id="synthetic-context-sentinel",
                     decision_at_utc="2026-09-27T10:00:00Z",
                     review_at_utc="2026-09-27T10:00:00Z",
                     claim_mode="ex_ante", decision_time_kind="hypothetical")
    candidate["trace_id"] = f"synthetic-hour-{hour_index}"
    candidate["trace_sequence_index"] = hour_index
    candidate["manifest_sha256"] = hashlib.sha256(manifest_raw).hexdigest()
    candidate["synthetic_input_review_id"] = manifest["synthetic_input_review_id"]
    candidate["interval"] = {
        "start_utc": interval["start_utc"],
        "end_utc": interval["end_utc"],
    }
    candidate["steps"][0]["start_utc"] = candidate["interval"]["start_utc"]
    candidate["steps"][0]["end_utc"] = candidate["interval"]["end_utc"]
    candidate["initial_state"] = deepcopy(thermal["initial_state"])
    sources = []
    for fixture_id in (weather["fixture_id"], thermal["fixture_id"]):
        source = deepcopy(candidate["source_records"][0])
        entry = next(item for item in manifest["files"] if item["fixture_id"] == fixture_id)
        is_weather = fixture_id == weather["fixture_id"]
        source.update(
            id=f"{fixture_id}:/intervals/{hour_index}" if is_weather else fixture_id,
            source_locator=entry["source_locator"],
            product_id=entry["product_id"],
            author=entry["author"],
            observed_start_utc=entry["observed_start_utc"],
            observed_end_utc=entry["observed_end_utc"],
            applicability_start_utc=interval["start_utc"] if is_weather else entry["applicability_start_utc"],
            applicability_end_utc=interval["end_utc"] if is_weather else entry["applicability_end_utc"],
            published_at_utc=entry["published_at_utc"],
            available_at_utc=entry["available_at_utc"],
            retrieved_at_utc=entry["retrieved_at_utc"],
            vintage=entry["vintage_id"],
            revision=entry["revision_id"],
            original_unit=deepcopy(entry["variable_units"]),
            raw_sha256=entry["sha256"],
            reviewer=entry["review"]["reviewer"],
        )
        sources.append(source)
    candidate["source_records"] = sources
    for name in ("outdoor_humidity_ratio", "solar_gain"):
        plan = interval["derived_forcing"][name]
        rule = thermal["conversion_rules"][name]
        candidate["forcing"][name].update(
            basis_ref=f"{thermal['fixture_id']}:/conversion_rules/{name}",
            version=rule["version"],
            calculation_rule_ref=plan["calculation_rule_ref"],
            calculation_rule_version=plan["calculation_rule_version"],
            input_record_ids=plan["input_record_ids"][:],
        )
    if hour_index > 0:
        previous, _, _, _ = fixture_linked_temporal_candidate(schema, hour_index - 1)
        previous_raw = json.dumps(previous, sort_keys=True, separators=(",", ":")).encode()
        previous_hash = hashlib.sha256(previous_raw).hexdigest()
        for name in ("temperature", "humidity_ratio"):
            prior_final = previous["steps"][-1]["state_end"][name]
            pointer = f"/steps/{len(previous['steps']) - 1}/state_end/{name}"
            candidate["initial_state"][name] = {
                "value": prior_final["value"], "unit": prior_final["unit"], "origin": "derived",
                "basis_ref": f"trace-sha256:{previous_hash}#{pointer}", "version": "v1",
                "calculation_rule_ref": "thermal-state-carry-v1", "calculation_rule_version": "v1",
                "previous_trace_id": previous["trace_id"],
                "previous_trace_sha256": previous_hash,
                "previous_state_pointer": pointer,
            }
    return candidate, manifest, weather, weather_raw


def temporal_provenance_errors(candidate, manifest, weather, weather_raw, review_at_utc):
    """Test reference for time and immutable input links; no gate or engine."""
    errors = []

    def utc(value):
        if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", value
        ):
            raise ValueError("UTC timestamp required")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo != timezone.utc:
            raise ValueError("UTC timestamp required")
        return parsed

    try:
        manifest_raw = (ROOT / "fixtures/manifest-v2.json").read_bytes()
        thermal_raw = (ROOT / "fixtures/synthetic-thermal-parameters-v1.json").read_bytes()
        thermal = json.loads(thermal_raw)
        if manifest != json.loads(manifest_raw):
            errors.append("manifest/raw mismatch")
        if weather != json.loads(weather_raw):
            errors.append("weather/raw mismatch")
        raw_by_id = {weather["fixture_id"]: weather_raw, thermal["fixture_id"]: thermal_raw}
        fixture_by_id = {weather["fixture_id"]: weather, thermal["fixture_id"]: thermal}
        entries = {entry["fixture_id"]: entry for entry in manifest["files"]}
        decision_at = utc(candidate["decision_at_utc"])
        review_at = utc(review_at_utc)
        if candidate["review_at_utc"] != review_at_utc or decision_at > review_at:
            errors.append("decision/review clock mismatch")
        if candidate["claim_mode"] not in ("ex_ante", "ex_post_replay"):
            errors.append("claim mode")
        run_start, run_end = (utc(candidate["interval"][key]) for key in ("start_utc", "end_utc"))
        if run_start >= run_end:
            errors.append("run interval order")
        steps = candidate["steps"]
        if not steps or utc(steps[0]["start_utc"]) != run_start or utc(steps[-1]["end_utc"]) != run_end:
            errors.append("step coverage")
        previous_end = run_start
        for step in steps:
            start, end = utc(step["start_utc"]), utc(step["end_utc"])
            if start != previous_end or not start < end:
                errors.append("step gap, overlap, or order")
            previous_end = end
        if candidate["synthetic_input_review_id"] != manifest["synthetic_input_review_id"]:
            errors.append("review link")
        if candidate["manifest_sha256"] != hashlib.sha256(manifest_raw).hexdigest():
            errors.append("manifest pin")
        for record in (manifest, *entries.values()):
            if not (utc(record["published_at_utc"]) <= utc(record["available_at_utc"])
                    <= utc(record["retrieved_at_utc"]) <= review_at):
                errors.append("review chronology")
            if (candidate["claim_mode"] == "ex_ante" and
                    utc(record["available_at_utc"]) > decision_at):
                errors.append("decision availability")
        for fixture_id, raw in raw_by_id.items():
            if entries[fixture_id]["sha256"] != hashlib.sha256(raw).hexdigest():
                errors.append("raw pin")
        weather_intervals = weather["intervals"]
        if (not weather_intervals or
                utc(weather_intervals[0]["start_utc"]) != utc(weather["start_utc"]) or
                utc(weather_intervals[-1]["end_utc"]) != utc(weather["end_utc"])):
            errors.append("forcing interval coverage")
        previous_forcing_end = utc(weather["start_utc"])
        for interval in weather_intervals:
            start, end = utc(interval["start_utc"]), utc(interval["end_utc"])
            if start != previous_forcing_end or not start < end:
                errors.append("forcing interval gap, overlap, or order")
            previous_forcing_end = end
        matching = [i for i, interval in enumerate(weather_intervals) if
                    utc(interval["start_utc"]) == run_start and utc(interval["end_utc"]) == run_end]
        if len(matching) != 1:
            errors.append("forcing interval gap, overlap, or mismatch")
        else:
            hour_index = matching[0]
            linked = thermal["intervals"][hour_index]
            if hour_index == 0 and candidate["initial_state"] != thermal["initial_state"]:
                errors.append("first initial state link")
            if (linked["weather_ref"] != {"fixture_id": weather["fixture_id"], "interval_index": hour_index}
                    or utc(linked["start_utc"]) != run_start or utc(linked["end_utc"]) != run_end):
                errors.append("thermal/forcing interval link")
            expected_sources = {
                f"{weather['fixture_id']}:/intervals/{hour_index}": (weather["fixture_id"], linked),
                thermal["fixture_id"]: (thermal["fixture_id"], None),
            }
            actual_sources = {source["id"]: source for source in candidate["source_records"]}
            if len(actual_sources) != len(candidate["source_records"]) or set(actual_sources) != set(expected_sources):
                errors.append("source set")
            for source_id, (fixture_id, linked_interval) in expected_sources.items():
                source = actual_sources.get(source_id)
                if source is None:
                    continue
                entry = entries[fixture_id]
                if source["observed_start_utc"] is not None or source["observed_end_utc"] is not None:
                    errors.append("fabricated observation")
                expected_start = linked_interval["start_utc"] if linked_interval else entry["applicability_start_utc"]
                expected_end = linked_interval["end_utc"] if linked_interval else entry["applicability_end_utc"]
                expected = {
                    "source_locator": entry["source_locator"], "product_id": entry["product_id"],
                    "author": entry["author"], "raw_sha256": entry["sha256"],
                    "original_unit": entry["variable_units"],
                    "vintage": entry["vintage_id"], "revision": entry["revision_id"],
                    "published_at_utc": entry["published_at_utc"],
                    "available_at_utc": entry["available_at_utc"],
                    "retrieved_at_utc": entry["retrieved_at_utc"],
                    "applicability_start_utc": expected_start,
                    "applicability_end_utc": expected_end,
                    "reviewer": entry["review"]["reviewer"],
                }
                if any(source.get(key) != value for key, value in expected.items()):
                    errors.append("source/manifest link")
                start, end = utc(source["applicability_start_utc"]), utc(source["applicability_end_utc"])
                if not start < end:
                    errors.append("applicability order")
                if not start <= run_start < run_end <= end:
                    errors.append("run outside applicability")
                for step in steps:
                    if not start <= utc(step["start_utc"]) < utc(step["end_utc"]) <= end:
                        errors.append("step outside applicability")
                if not start <= run_start < run_end <= end:
                    errors.append("forcing outside applicability")
                if not (utc(source["published_at_utc"]) <= utc(source["available_at_utc"])
                        <= utc(source["retrieved_at_utc"]) <= review_at):
                    errors.append("review chronology")
                if (candidate["claim_mode"] == "ex_ante" and
                        utc(source["available_at_utc"]) > decision_at):
                    errors.append("decision availability")
            records = {record["record_id"]: record for record in thermal["input_records"]}
            if len(records) != len(thermal["input_records"]):
                errors.append("duplicate input record")
            for name in ("outdoor_humidity_ratio", "solar_gain"):
                derived = candidate["forcing"][name]
                plan = linked["derived_forcing"][name]
                rule = thermal["conversion_rules"][name]
                registered = {
                    "calculation_rule_ref": rule["rule_ref"],
                    "calculation_rule_version": rule["version"],
                    "basis_ref": f"{thermal['fixture_id']}:/conversion_rules/{name}",
                    "version": rule["version"],
                }
                if (plan["calculation_rule_ref"] != rule["rule_ref"] or
                        plan["calculation_rule_version"] != rule["version"] or
                        any(derived.get(key) != value for key, value in registered.items())):
                    errors.append(f"{name} rule registration")
                actual_ids = derived["input_record_ids"]
                expected_ids = plan["input_record_ids"]
                if len(actual_ids) != len(set(actual_ids)) or set(actual_ids) != set(expected_ids):
                    errors.append(f"{name} input record set")
                for record_id in actual_ids:
                    record = records.get(record_id)
                    if record is None or record["file_id"] not in raw_by_id:
                        errors.append("unresolved input record")
                        continue
                    fixture_id, pointer = record["file_id"], record["json_pointer"]
                    if record_id != f"{fixture_id}:{pointer}" or not pointer.startswith("/"):
                        errors.append("input record identity")
                        continue
                    node = fixture_by_id[fixture_id]
                    try:
                        for token in pointer.split("/")[1:]:
                            token = token.replace("~1", "/").replace("~0", "~")
                            node = node[int(token)] if isinstance(node, list) else node[token]
                    except (IndexError, KeyError, TypeError, ValueError):
                        errors.append("input record pointer")
                    if fixture_id == weather["fixture_id"] and not pointer.startswith(
                        f"/intervals/{hour_index}/"
                    ):
                        errors.append("cross-hour input record")
            if any(linked["weather_input_ids"][key] !=
                   f"{weather['fixture_id']}:/intervals/{hour_index}/values/{key}"
                   for key in ("T_o", "phi_o", "p_o", "solar_interval_energy")):
                errors.append("weather field link")
        if not utc(weather["start_utc"]) <= run_start < run_end <= utc(weather["end_utc"]):
            errors.append("fixture interval")
    except (KeyError, StopIteration, TypeError, ValueError, IndexError) as exc:
        errors.append(f"invalid temporal provenance: {exc}")
    return errors


def carried_state_errors(previous_raw, current):
    """Test reference for byte-pinned adjacent state carry; no engine verification."""
    errors = []
    try:
        previous = json.loads(previous_raw)
        previous_hash = hashlib.sha256(previous_raw).hexdigest()
        if previous["trace_id"] == current["trace_id"]:
            errors.append("trace identity")
        if previous["trace_sequence_index"] + 1 != current["trace_sequence_index"]:
            errors.append("trace sequence")
        for key in ("run_id", "model_version", "parameter_set_version", "manifest_sha256",
                    "engine_version", "unit_registry_version", "input_snapshot_id", "decision_id",
                    "decision_context_id", "decision_at_utc", "review_at_utc", "claim_mode",
                    "decision_time_kind"):
            if previous[key] != current[key]:
                errors.append(f"{key} mismatch")
        if previous["interval"]["end_utc"] != current["interval"]["start_utc"]:
            errors.append("trace adjacency")
        if (previous["steps"][-1]["end_utc"] != previous["interval"]["end_utc"] or
                current["steps"][0]["start_utc"] != current["interval"]["start_utc"]):
            errors.append("trace step boundary")
        final_index = len(previous["steps"]) - 1
        for field_name in ("temperature", "humidity_ratio"):
            initial = current["initial_state"][field_name]
            prior_final = previous["steps"][final_index]["state_end"][field_name]
            if (initial["origin"] != "derived" or initial["calculation_rule_ref"] != "thermal-state-carry-v1"
                    or initial["calculation_rule_version"] != "v1"):
                errors.append(f"{field_name} carry rule")
            expected_pointer = f"/steps/{final_index}/state_end/{field_name}"
            if (initial.get("basis_ref") != f"trace-sha256:{previous_hash}#{expected_pointer}"
                    or initial.get("version") != "v1"):
                errors.append(f"{field_name} carry basis")
            if (initial["previous_trace_id"] != previous["trace_id"] or
                    initial["previous_trace_sha256"] != previous_hash):
                errors.append(f"{field_name} prior trace pin")
            if initial["previous_state_pointer"] != expected_pointer:
                errors.append(f"{field_name} prior state pointer")
            if (initial["value"], initial["unit"]) != (prior_final["value"], prior_final["unit"]):
                errors.append(f"{field_name} state mismatch")
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        errors.append(f"invalid carried state: {exc}")
    return errors


def mutate(candidate, path, value):
    changed = deepcopy(candidate)
    target = changed
    for segment in path[:-1]:
        target = target[segment]
    if value is None:
        del target[path[-1]]
    else:
        target[path[-1]] = value
    return changed


def candidate_with_derived_forcing(schema):
    candidate = schema_shaped_synthetic_candidate(schema)
    thermal = json.loads((ROOT / "fixtures/synthetic-thermal-parameters-v1.json").read_bytes())
    for name in ("outdoor_humidity_ratio", "solar_gain"):
        value = candidate["forcing"][name]
        rule = thermal["conversion_rules"][name]
        value.update(
            origin="derived",
            basis_ref=f"{thermal['fixture_id']}:/conversion_rules/{name}",
            version=rule["version"],
            calculation_rule_ref=rule["rule_ref"],
            calculation_rule_version=rule["version"],
            input_record_ids=[f"immutable:{name}:input"],
        )
    return candidate


def test_generic_sourced_value_rejects_unexplained_derived_origin(contract):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    assert Draft202012Validator(schema).is_valid(candidate)
    candidate["initial_state"]["temperature"]["origin"] = "derived"
    assert not Draft202012Validator(schema).is_valid(candidate)


def test_saturation_coefficient_rejects_unexplained_derived_origin(contract):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    assert Draft202012Validator(schema).is_valid(candidate)
    coefficient = field(
        schema, field(schema, field(schema, schema, "parameters"), "saturation_pressure_rule"),
        "coefficients",
    )["items"]
    assert "derived" not in field(schema, coefficient, "origin")["enum"]
    candidate["parameters"]["saturation_pressure_rule"]["coefficients"][0]["origin"] = "derived"
    assert not Draft202012Validator(schema).is_valid(candidate)


def test_every_generic_sourced_definition_rejects_derived_origin(contract):
    schema, _, _ = contract
    names = [name for name in schema["$defs"] if name.startswith("sourced_")]
    assert names
    accepting_derived = []
    for name in names:
        definition = schema["$defs"][name]
        assert "derived" not in definition["properties"]["origin"]["enum"], name
        value = True if definition["properties"]["value"]["type"] == "boolean" else 1
        record = {
            "value": value,
            "unit": definition["properties"]["unit"]["const"],
            "origin": "assumed",
            "basis_ref": "immutable:shape-only",
            "version": "v1",
        }
        validator = Draft202012Validator(definition)
        assert validator.is_valid(record), name
        record["origin"] = "derived"
        if validator.is_valid(record):
            accepting_derived.append(name)
    assert not accepting_derived, accepting_derived


@pytest.mark.parametrize("name", ["outdoor_humidity_ratio", "solar_gain"])
def test_derived_forcing_requires_rule_version_and_immutable_input_ids(contract, name):
    schema, _, _ = contract
    derived = field(schema, field(schema, schema, "forcing"), name)
    requires(
        schema, derived, "value", "unit", "origin", "basis_ref", "version",
        "calculation_rule_ref", "calculation_rule_version", "input_record_ids",
    )
    assert field(schema, derived, "origin")["const"] == "derived"
    refs = field(schema, derived, "input_record_ids")
    assert refs["type"] == "array" and refs["minItems"] >= 1
    assert refs["items"]["type"] == "string" and refs["items"]["minLength"] >= 1
    candidate = candidate_with_derived_forcing(schema)
    assert Draft202012Validator(schema).is_valid(candidate)


@pytest.mark.parametrize("name", ["outdoor_humidity_ratio", "solar_gain"])
@pytest.mark.parametrize(
    ("property_name", "invalid"),
    [
        ("origin", "assumed"),
        ("calculation_rule_ref", None),
        ("calculation_rule_version", ""),
        ("input_record_ids", None),
        ("input_record_ids", []),
        ("input_record_ids", [""]),
    ],
)
def test_derived_forcing_rejects_missing_or_invalid_derivation(contract, name, property_name, invalid):
    schema, _, _ = contract
    candidate = candidate_with_derived_forcing(schema)
    assert Draft202012Validator(schema).is_valid(candidate)
    rejected = mutate(candidate, ("forcing", name, property_name), invalid)
    assert not Draft202012Validator(schema).is_valid(rejected)


@pytest.mark.parametrize("available", [True, False])
def test_heater_availability_accepts_sourced_boolean(contract, available):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    candidate["heater"]["available"] = {
        "value": available,
        "unit": "1",
        "origin": "assumed",
        "basis_ref": "immutable:heater-availability",
        "version": "v1",
    }
    assert Draft202012Validator(schema).is_valid(candidate)


@pytest.mark.parametrize(
    ("path", "invalid"),
    [
        (("heater", "available"), True),
        (("heater", "available", "value"), None),
        (("heater", "available", "value"), 1),
        (("heater", "available", "unit"), "boolean"),
        (("heater", "available", "origin"), None),
        (("heater", "available", "basis_ref"), ""),
        (("heater", "available", "version"), None),
    ],
)
def test_heater_availability_rejects_bare_or_incomplete_value(contract, path, invalid):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    candidate["heater"]["available"] = {
        "value": False,
        "unit": "1",
        "origin": "assumed",
        "basis_ref": "immutable:heater-availability",
        "version": "v1",
    }
    assert Draft202012Validator(schema).is_valid(candidate)
    assert not Draft202012Validator(schema).is_valid(mutate(candidate, path, invalid))


def test_draft_2020_12_schema_and_synthetic_shape(contract):
    schema, _, _ = contract
    Draft202012Validator.check_schema(schema)
    assert "synthetic_input_review_id" in schema["required"]
    assert "source_gate_id" not in schema["properties"]
    candidate = schema_shaped_synthetic_candidate(schema)
    assert not list(Draft202012Validator(schema).iter_errors(candidate))


def test_synthetic_source_null_observations_and_fixture_applicability_shape(contract):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema)
    source = candidate["source_records"][0]
    source_shape = schema["properties"]["source_records"]["items"]
    requires(
        schema, source_shape, "observed_start_utc", "observed_end_utc",
        "applicability_start_utc", "applicability_end_utc",
    )
    assert source["observed_start_utc"] is source["observed_end_utc"] is None
    assert hashlib.sha256(weather_raw).hexdigest() == source["raw_sha256"]
    assert manifest["files"][0]["fixture_id"] == weather["fixture_id"]
    assert not list(Draft202012Validator(schema).iter_errors(candidate))


@pytest.mark.parametrize("name", ["observed_start_utc", "observed_end_utc"])
def test_synthetic_source_rejects_fabricated_observation(contract, name):
    schema, _, _ = contract
    candidate, _, _, _ = fixture_linked_temporal_candidate(schema)
    assert Draft202012Validator(schema).is_valid(candidate)
    candidate["source_records"][0][name] = "2026-10-15T08:00:00Z"
    assert not Draft202012Validator(schema).is_valid(candidate)


@pytest.mark.parametrize("name", ["applicability_start_utc", "applicability_end_utc"])
@pytest.mark.parametrize("invalid", ["missing", None, "", "2026-10-15T17:00:00+09:00"])
def test_synthetic_source_rejects_missing_or_invalid_applicability(contract, name, invalid):
    schema, _, _ = contract
    candidate, _, _, _ = fixture_linked_temporal_candidate(schema)
    assert Draft202012Validator(schema).is_valid(candidate)
    if invalid == "missing":
        del candidate["source_records"][0][name]
    else:
        candidate["source_records"][0][name] = invalid
    assert not Draft202012Validator(schema).is_valid(candidate)


def test_temporal_reference_accepts_only_the_fixture_linked_interval(contract):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema)
    assert temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z"
    ) == []


def test_two_adjacent_fixture_hours_use_distinct_derived_input_sets(contract):
    schema, _, _ = contract
    thermal = json.loads((ROOT / "fixtures/synthetic-thermal-parameters-v1.json").read_bytes())
    candidates = []
    for hour_index in range(len(thermal["intervals"])):
        candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema, hour_index)
        candidates.append(candidate)
        fixture_interval = thermal["intervals"][hour_index]
        parameter_entry = next(entry for entry in manifest["files"] if entry["fixture_id"] == thermal["fixture_id"])
        assert candidate["interval"] == {key: fixture_interval[key] for key in ("start_utc", "end_utc")}
        assert candidate["source_records"][0]["applicability_start_utc"] == fixture_interval["start_utc"]
        assert candidate["source_records"][0]["applicability_end_utc"] == fixture_interval["end_utc"]
        assert candidate["source_records"][1]["applicability_start_utc"] == parameter_entry["applicability_start_utc"]
        assert candidate["source_records"][1]["applicability_end_utc"] == parameter_entry["applicability_end_utc"]
        for name in ("outdoor_humidity_ratio", "solar_gain"):
            assert candidate["forcing"][name]["input_record_ids"] == fixture_interval["derived_forcing"][name]["input_record_ids"]
        assert Draft202012Validator(schema).is_valid(candidate)
        assert temporal_provenance_errors(
            candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z"
        ) == []
    assert candidates[0]["interval"]["end_utc"] == candidates[1]["interval"]["start_utc"]
    assert candidates[0]["interval"]["start_utc"] == weather["start_utc"]
    assert candidates[-1]["interval"]["end_utc"] == weather["end_utc"]
    for name in ("outdoor_humidity_ratio", "solar_gain"):
        assert set(candidates[0]["forcing"][name]["input_record_ids"]) != set(
            candidates[1]["forcing"][name]["input_record_ids"]
        )
    assert set(candidates[0]["forcing"]["outdoor_humidity_ratio"]["input_record_ids"]) != set(
        candidates[0]["forcing"]["solar_gain"]["input_record_ids"]
    )


@pytest.mark.parametrize("hour_index", [0, 1])
def test_fixture_source_units_match_manifest_maps(contract, hour_index):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema, hour_index)
    entries = {entry["fixture_id"]: entry for entry in manifest["files"]}
    for source in candidate["source_records"]:
        fixture_id = source["id"].split(":", 1)[0]
        assert source["original_unit"] == entries[fixture_id]["variable_units"]
    assert Draft202012Validator(schema).is_valid(candidate)
    assert temporal_provenance_errors(candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z") == []


@pytest.mark.parametrize("hour_index", [0, 1])
@pytest.mark.parametrize("source_index", [0, 1])
@pytest.mark.parametrize("change", ["stringified", "bananas", "missing", "extra", "swapped_fields", "swapped_map", "missing_map"])
def test_fixture_source_units_reject_invalid_or_swapped_map(contract, hour_index, source_index, change):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema, hour_index)
    source = candidate["source_records"][source_index]
    units = source["original_unit"]
    if change == "stringified":
        source["original_unit"] = str(units)
    elif change == "bananas":
        units[next(iter(units))] = "bananas"
    elif change == "missing":
        del units[next(iter(units))]
    elif change == "extra":
        units["unexpected"] = "K"
    elif change == "swapped_fields":
        first, second = next(iter(units)), list(units)[1]
        units[first], units[second] = units[second], units[first]
    elif change == "swapped_map":
        source["original_unit"] = deepcopy(candidate["source_records"][1 - source_index]["original_unit"])
    else:
        del source["original_unit"]
    errors = temporal_provenance_errors(candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z")
    assert "source/manifest link" in errors
    if change != "swapped_map":
        assert not Draft202012Validator(schema).is_valid(candidate)


@pytest.mark.parametrize("hour_index", [0, 1])
@pytest.mark.parametrize("name", ["outdoor_humidity_ratio", "solar_gain"])
def test_fixture_derived_forcing_uses_registered_rule_and_basis(contract, hour_index, name):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema, hour_index)
    thermal = json.loads((ROOT / "fixtures/synthetic-thermal-parameters-v1.json").read_bytes())
    rule = thermal["conversion_rules"][name]
    plan = thermal["intervals"][hour_index]["derived_forcing"][name]
    derived = candidate["forcing"][name]
    assert derived["calculation_rule_ref"] == plan["calculation_rule_ref"] == rule["rule_ref"]
    assert derived["calculation_rule_version"] == plan["calculation_rule_version"] == rule["version"]
    assert derived["version"] == rule["version"]
    assert derived["basis_ref"] == f"{thermal['fixture_id']}:/conversion_rules/{name}"
    assert Draft202012Validator(schema).is_valid(candidate)
    assert temporal_provenance_errors(candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z") == []


@pytest.mark.parametrize("hour_index", [0, 1])
@pytest.mark.parametrize("name", ["outdoor_humidity_ratio", "solar_gain"])
@pytest.mark.parametrize(
    ("key", "change"),
    [(key, change) for key in ("calculation_rule_ref", "calculation_rule_version", "basis_ref", "version")
     for change in ("wrong", "missing")]
    + [(key, "swapped") for key in ("calculation_rule_ref", "basis_ref")],
)
def test_fixture_derived_forcing_rejects_wrong_missing_or_swapped_registration(
    contract, hour_index, name, key, change
):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema, hour_index)
    other = "solar_gain" if name == "outdoor_humidity_ratio" else "outdoor_humidity_ratio"
    derived = candidate["forcing"][name]
    if change == "missing":
        del derived[key]
    elif change == "swapped":
        derived[key] = candidate["forcing"][other][key]
    else:
        derived[key] = "unregistered"
    assert not Draft202012Validator(schema).is_valid(candidate)
    assert f"{name} rule registration" in temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z"
    )


def test_carried_initial_state_requires_previous_trace_provenance(contract):
    schema, _, _ = contract
    first, _, _, _ = fixture_linked_temporal_candidate(schema, 0)
    second, _, _, _ = fixture_linked_temporal_candidate(schema, 1)
    previous_raw = json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
    previous_hash = hashlib.sha256(previous_raw).hexdigest()
    for field_name in ("temperature", "humidity_ratio"):
        pointer = f"/steps/0/state_end/{field_name}"
        second["initial_state"][field_name] = {
            "value": first["steps"][-1]["state_end"][field_name]["value"],
            "unit": first["steps"][-1]["state_end"][field_name]["unit"],
            "origin": "derived",
            "basis_ref": f"trace-sha256:{previous_hash}#{pointer}", "version": "v1",
            "calculation_rule_ref": "thermal-state-carry-v1",
            "calculation_rule_version": "v1",
            "previous_trace_id": first["trace_id"],
            "previous_trace_sha256": previous_hash,
            "previous_state_pointer": pointer,
        }
    assert Draft202012Validator(schema).is_valid(second)
    assert carried_state_errors(previous_raw, second) == []


@pytest.mark.parametrize("field_name", ["temperature", "humidity_ratio"])
def test_carried_state_basis_binds_raw_trace_and_field(contract, field_name):
    schema, _, _ = contract
    first, _, _, _ = fixture_linked_temporal_candidate(schema, 0)
    second, _, _, _ = fixture_linked_temporal_candidate(schema, 1)
    previous_raw = json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
    carried = second["initial_state"][field_name]
    carried["basis_ref"] = (
        f"trace-sha256:{hashlib.sha256(previous_raw).hexdigest()}#"
        f"{carried['previous_state_pointer']}"
    )
    carried["version"] = "v1"
    assert Draft202012Validator(schema).is_valid(second)
    assert carried_state_errors(previous_raw, second) == []

    for missing in ("basis_ref", "version"):
        invalid = deepcopy(second)
        del invalid["initial_state"][field_name][missing]
        assert not Draft202012Validator(schema).is_valid(invalid)
        assert f"{field_name} carry basis" in carried_state_errors(previous_raw, invalid)

    for key, value in (("basis_ref", "trace-sha256:" + "f" * 64 + "#" + carried["previous_state_pointer"]),
                       ("basis_ref", "immutable:self-declared-carry"), ("version", "v2")):
        invalid = deepcopy(second)
        invalid["initial_state"][field_name][key] = value
        if value == "immutable:self-declared-carry" or key == "version":
            assert not Draft202012Validator(schema).is_valid(invalid)
        assert f"{field_name} carry basis" in carried_state_errors(previous_raw, invalid)


def test_first_trace_rejects_carried_initial_state(contract):
    schema, _, _ = contract
    first, _, _, _ = fixture_linked_temporal_candidate(schema, 0)
    second, _, _, _ = fixture_linked_temporal_candidate(schema, 1)
    first["initial_state"] = deepcopy(second["initial_state"])
    assert not Draft202012Validator(schema).is_valid(first)


def test_reference_rejects_unpinned_weather_bytes(contract):
    schema, _, _ = contract
    candidate, manifest, weather, _ = fixture_linked_temporal_candidate(schema, 0)
    errors = temporal_provenance_errors(candidate, manifest, weather, b"{}", "2026-09-27T10:00:00Z")
    assert "raw pin" in errors
    assert "weather/raw mismatch" in errors


@pytest.mark.parametrize("field_name", ["temperature", "humidity_ratio"])
@pytest.mark.parametrize("missing", ["previous_trace_id", "previous_trace_sha256", "previous_state_pointer", "calculation_rule_version", "basis_ref", "version"])
def test_carried_state_schema_rejects_missing_reference(contract, field_name, missing):
    schema, _, _ = contract
    first, _, _, _ = fixture_linked_temporal_candidate(schema, 0)
    second, _, _, _ = fixture_linked_temporal_candidate(schema, 1)
    for name in ("temperature", "humidity_ratio"):
        prior = first["steps"][-1]["state_end"][name]
        second["initial_state"][name] = {
            "value": prior["value"], "unit": prior["unit"], "origin": "derived",
            "basis_ref": f"trace-sha256:{'a' * 64}#/steps/0/state_end/{name}", "version": "v1",
            "calculation_rule_ref": "thermal-state-carry-v1", "calculation_rule_version": "v1",
            "previous_trace_id": first["trace_id"], "previous_trace_sha256": "a" * 64,
            "previous_state_pointer": f"/steps/0/state_end/{name}",
        }
    assert Draft202012Validator(schema).is_valid(second)
    del second["initial_state"][field_name][missing]
    assert not Draft202012Validator(schema).is_valid(second)


def test_source_labeled_assumed_state_cannot_bypass_carry(contract):
    schema, _, _ = contract
    first, _, _, _ = fixture_linked_temporal_candidate(schema, 0)
    second, _, _, _ = fixture_linked_temporal_candidate(schema, 1)
    second["initial_state"]["temperature"] = {
        **first["initial_state"]["temperature"], "basis_ref": "prior-trace-final-state",
    }
    assert not Draft202012Validator(schema).is_valid(second)
    assert carried_state_errors(json.dumps(first).encode(), second)


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("state_mismatch", "temperature state mismatch"),
        ("wrong_prior_hash", "temperature prior trace pin"),
        ("wrong_prior_id", "humidity_ratio prior trace pin"),
        ("broken_adjacency", "trace adjacency"),
        ("wrong_run", "run_id mismatch"),
        ("wrong_model", "model_version mismatch"),
        ("wrong_parameter_set", "parameter_set_version mismatch"),
        ("wrong_manifest", "manifest_sha256 mismatch"),
        ("wrong_engine", "engine_version mismatch"),
        ("wrong_unit_registry", "unit_registry_version mismatch"),
        ("wrong_context", "decision_context_id mismatch"),
        ("wrong_D", "decision_at_utc mismatch"),
        ("wrong_R", "review_at_utc mismatch"),
        ("wrong_mode", "claim_mode mismatch"),
        ("wrong_time_kind", "decision_time_kind mismatch"),
        ("wrong_pointer", "temperature prior state pointer"),
        ("wrong_sequence", "trace sequence"),
    ],
)
def test_carried_state_reference_rejects_broken_link(contract, change, expected):
    schema, _, _ = contract
    first, _, _, _ = fixture_linked_temporal_candidate(schema, 0)
    second, _, _, _ = fixture_linked_temporal_candidate(schema, 1)
    previous_raw = json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
    previous_hash = hashlib.sha256(previous_raw).hexdigest()
    for name in ("temperature", "humidity_ratio"):
        prior = first["steps"][-1]["state_end"][name]
        pointer = f"/steps/0/state_end/{name}"
        second["initial_state"][name] = {
            "value": prior["value"], "unit": prior["unit"], "origin": "derived",
            "basis_ref": f"trace-sha256:{previous_hash}#{pointer}", "version": "v1",
            "calculation_rule_ref": "thermal-state-carry-v1", "calculation_rule_version": "v1",
            "previous_trace_id": first["trace_id"],
            "previous_trace_sha256": previous_hash,
            "previous_state_pointer": pointer,
        }
    if change == "state_mismatch":
        second["initial_state"]["temperature"]["value"] += 1
    elif change == "wrong_prior_hash":
        second["initial_state"]["temperature"]["previous_trace_sha256"] = "f" * 64
    elif change == "wrong_prior_id":
        second["initial_state"]["humidity_ratio"]["previous_trace_id"] = "other-trace"
    elif change == "broken_adjacency":
        second["interval"]["start_utc"] = "2026-10-15T09:01:00Z"
    elif change == "wrong_pointer":
        second["initial_state"]["temperature"]["previous_state_pointer"] = "/steps/1/state_end/temperature"
    elif change == "wrong_sequence":
        second["trace_sequence_index"] = 2
    else:
        key = {
            "wrong_run": "run_id", "wrong_model": "model_version",
            "wrong_parameter_set": "parameter_set_version", "wrong_manifest": "manifest_sha256",
            "wrong_engine": "engine_version", "wrong_unit_registry": "unit_registry_version",
            "wrong_context": "decision_context_id", "wrong_D": "decision_at_utc",
            "wrong_R": "review_at_utc", "wrong_mode": "claim_mode",
            "wrong_time_kind": "decision_time_kind",
        }[change]
        second[key] = (
            "f" * 64 if key == "manifest_sha256" else
            "2026-09-27T11:00:00Z" if key in ("decision_at_utc", "review_at_utc") else
            "ex_post_replay" if key == "claim_mode" else
            "actual" if key == "decision_time_kind" else "other-version"
        )
    assert expected in carried_state_errors(previous_raw, second)


@pytest.mark.parametrize("name", ["outdoor_humidity_ratio", "solar_gain"])
@pytest.mark.parametrize("change", ["missing", "extra", "cross_hour", "swapped"])
def test_exact_fixture_input_sets_reject_bad_references(contract, name, change):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema, 0)
    ids = candidate["forcing"][name]["input_record_ids"]
    other = "solar_gain" if name == "outdoor_humidity_ratio" else "outdoor_humidity_ratio"
    if change == "missing":
        ids.pop()
    elif change == "extra":
        ids.append(candidate["forcing"][other]["input_record_ids"][0])
    elif change == "cross_hour":
        ids[0] = ids[0].replace("/intervals/0/", "/intervals/1/")
    else:
        candidate["forcing"][name]["input_record_ids"] = candidate["forcing"][other]["input_record_ids"][:]
    assert any("input record set" in error for error in temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z"
    ))


@pytest.mark.parametrize(
    ("change", "expected"),
    [
        ("reversed_applicability", "applicability order"),
        ("run_outside_applicability", "run outside applicability"),
        ("step_outside_applicability", "step outside applicability"),
        ("step_overlap", "step gap, overlap, or order"),
        ("forcing_outside_applicability", "forcing interval gap, overlap, or mismatch"),
        ("forcing_gap", "forcing interval gap, overlap, or order"),
        ("invalid_calendar_date", "invalid temporal provenance"),
        ("too_early_decision", "review chronology"),
        ("manifest_after_decision", "decision availability"),
        ("missing_forcing_link", "solar_gain input record set"),
        ("raw_pin_mismatch", "source/manifest link"),
        ("fixture_interval_mismatch", "forcing interval gap, overlap, or mismatch"),
    ],
)
def test_temporal_reference_rejects_unproven_intervals(contract, change, expected):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema)
    decision_at = "2026-09-27T10:00:00Z"
    source = candidate["source_records"][0]
    if change == "reversed_applicability":
        source["applicability_end_utc"] = source["applicability_start_utc"]
    elif change == "run_outside_applicability":
        source["applicability_start_utc"] = "2026-10-15T08:30:00Z"
    elif change == "step_outside_applicability":
        candidate["steps"][0]["end_utc"] = "2026-10-15T10:30:00Z"
    elif change == "step_overlap":
        candidate["steps"][0]["end_utc"] = "2026-10-15T08:45:00Z"
        second = deepcopy(candidate["steps"][0])
        second["start_utc"] = "2026-10-15T08:30:00Z"
        second["end_utc"] = "2026-10-15T09:00:00Z"
        candidate["steps"].append(second)
    elif change == "forcing_outside_applicability":
        source["applicability_end_utc"] = "2026-10-15T09:00:00Z"
        weather["intervals"][0]["end_utc"] = "2026-10-15T09:30:00Z"
    elif change == "forcing_gap":
        weather["intervals"][1]["start_utc"] = "2026-10-15T09:10:00Z"
    elif change == "invalid_calendar_date":
        source["applicability_start_utc"] = "2026-02-30T08:00:00Z"
    elif change == "too_early_decision":
        decision_at = "2026-09-27T07:00:00Z"
    elif change == "manifest_after_decision":
        manifest["available_at_utc"] = "2026-09-27T11:00:00Z"
    elif change == "missing_forcing_link":
        candidate["forcing"]["solar_gain"]["input_record_ids"] = ["other-source"]
    elif change == "raw_pin_mismatch":
        source["raw_sha256"] = "f" * 64
    elif change == "fixture_interval_mismatch":
        weather["intervals"][0]["end_utc"] = "2026-10-15T08:30:00Z"
    assert any(expected in error for error in temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, decision_at
    ))


def test_temporal_reference_separates_planning_availability_from_review_retrieval(contract):
    schema, _, _ = contract
    candidate, manifest, weather, weather_raw = fixture_linked_temporal_candidate(schema)
    candidate["decision_at_utc"] = "2026-09-27T08:00:00Z"
    assert "decision availability" in temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z"
    )
    candidate["claim_mode"] = "ex_post_replay"
    assert temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, "2026-09-27T10:00:00Z"
    ) == []
    candidate["review_at_utc"] = "2026-09-27T08:00:00Z"
    assert "review chronology" in temporal_provenance_errors(
        candidate, manifest, weather, weather_raw, "2026-09-27T08:00:00Z"
    )


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("source_records", 0, "synthetic"), False),
        (("source_records", 0, "project_qc", "status"), "hold"),
        (("source_records", 0, "project_qc", "status"), "fail"),
        (("source_records", 0, "provider_qc", "status"), "fail"),
        (("source_records", 0, "rights", "use"), "unknown"),
        (("source_records", 0, "rights", "display"), "denied"),
        (("source_records", 0, "rights", "redistribute"), "unknown"),
    ],
)
def test_accepted_synthetic_trace_rejects_unaccepted_sources(contract, path, value):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    rejected = mutate(candidate, path, value)
    assert not Draft202012Validator(schema).is_valid(rejected), path


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("heater", "mode"), "direct_combustion"),
        (("initial_state", "humidity_ratio"), None),
        (("heater", "capacity", "unit"), "W_e"),
        (("interval", "start_utc"), "2026-01-01T09:00:00+09:00"),
        (("integration", "residual_tolerances", "vapor_residual"), None),
        (("integration", "step_convergence_tolerances", "temperature"), None),
        (("source_records", 0, "author"), None),
        (("source_records", 0, "normalization_rule_ref"), None),
        (("source_records", 0, "raw_sha256"), None),
        (("source_records", 0, "reviewer"), None),
        (("source_records", 0, "observed_start_utc"), None),
        (("source_records", 0, "observed_end_utc"), None),
        (("source_records", 0, "vintage"), None),
        (("synthetic_input_review_id",), None),
    ],
)
def test_accepted_synthetic_trace_rejects_other_structural_errors(contract, path, value):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    rejected = mutate(candidate, path, value)
    assert not Draft202012Validator(schema).is_valid(rejected), path
