"""RED contract checks for the proposed synthetic G1 thermal trace."""

import json
from copy import deepcopy
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
    quantity(schema, field(schema, state, "temperature"), "K", sourced=True)
    quantity(schema, field(schema, state, "humidity_ratio"), "kg_v/kg_da", sourced=True)


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
        if node["type"] == "number":
            return 0 if node.get("exclusiveMaximum") == 1 else 1
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
    return candidate


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
    for name in ("outdoor_humidity_ratio", "solar_gain"):
        value = candidate["forcing"][name]
        value.update(
            origin="derived",
            calculation_rule_ref=f"thermal-v1:{name}",
            calculation_rule_version="v1",
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
        (("source_records", 0, "vintage"), None),
        (("synthetic_input_review_id",), None),
    ],
)
def test_accepted_synthetic_trace_rejects_other_structural_errors(contract, path, value):
    schema, _, _ = contract
    candidate = schema_shaped_synthetic_candidate(schema)
    rejected = mutate(candidate, path, value)
    assert not Draft202012Validator(schema).is_valid(rejected), path
