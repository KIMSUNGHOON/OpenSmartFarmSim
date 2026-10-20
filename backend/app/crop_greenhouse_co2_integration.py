"""Shared109-state/44-ledger RK4; crop-greenhouse-co2-integration-v1.md."""
from hashlib import sha256
from math import isfinite, ulp
from pathlib import Path

from . import crop_climate_joint_integration as core
from . import crop_climate_joint_rhs as joint
from . import crop_greenhouse_solar_integration as previous
from . import crop_greenhouse_co2_joint as rhs

VERSION = "joint-crop-climate-co2-solar-rk4-research-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
CO2_UNIT = "mg_CO2/m2_floor"
CO2_FIELDS = ("co2_ventilation_to_air", "co2_external_to_air", "co2_crop_to_air")
FLUX_UNITS = {**previous.FLUX_UNITS, **dict.fromkeys(CO2_FIELDS, CO2_UNIT)}
POLICY = {"composition": "current109_state_CO2_solar_crop_RHS_each_trial",
          "sampling": "constant_external_solar_weather_pressure_basis_current_mass_air_vapor",
          "initial": "initial_and_endpoint_RHS_reused_as_k1_no_extra_validation",
          "ledgers": "old41_plus3_CO2_same_RK_weights",
          "failure": "last_confirmed_endpoint_only"}


class Co2IntegrationHold(core.JointIntegrationHold):
    """An unsupported trial exposes only its last confirmed research sample."""


def _need(condition, reason):
    if not condition:
        raise Co2IntegrationHold(reason)


def _held(exc, index, phase, last):
    reason = str(exc) if isinstance(exc, (joint.JointClimateHold, core.JointIntegrationHold)) else "NUMERIC_HOLD: arithmetic failed"
    held = Co2IntegrationHold(f"{reason}: step={index}; stage={phase}")
    held.step_index, held.failed_stage, held.last_confirmed_sample = index, phase, last
    held.last_confirmed_elapsed_seconds = None if last is None else last["elapsed_seconds"]
    return held


def _scenario(base, state):
    result = core._scenario(base, state[:108])
    return {**result, "climate_state": {**result["climate_state"], "air_co2_mass": core._q(state[108], CO2_UNIT)}}


def _values(result):
    rates, flux, _ = previous._values(result["solar_rhs"])
    mass = result["air_co2_rhs"]
    return (rates + (mass["derivatives"]["air_co2_mass"]["value"],),
            flux + tuple(mass["transfers"][key]["value"] for key in
                         ("ventilation_to_air", "external_to_air", "crop_to_air")), result)


def _evaluate(base, sun, weather, co2, state, profiles):
    return _values(rhs.evaluate_rhs(scenario=_scenario(base, state), solar=sun,
                                   ventilation=weather, co2=co2, **profiles))


def _sample(index, dt, base, state, result):
    sample = previous._sample(index, dt, base, state[:108], result["solar_rhs"])
    return {**sample, "climate_state": {**sample["climate_state"], "air_co2_mass": core._q(state[108], CO2_UNIT)},
            "derived": {**sample["derived"], **result["derived"]},
            "co2_exchange": {"net": result["net_exchange"]["co2"],
                             "air": result["air_co2_rhs"]["transfers"]}}


def _co2_balances(initial, final, totals, index, carbohydrate_budget):
    t = dict(zip(FLUX_UNITS, totals, strict=True))
    carbon = lambda y: core._sum((*y[:3], *y[5:55]))
    c0, c1 = carbon(initial), carbon(final)
    dm = final[108] - initial[108]
    ratio = rhs.net.CO2_MOLAR_MASS / rhs.net.CH2O_MOLAR_MASS
    mass_terms = (dm, *(-t[k] for k in CO2_FIELDS))
    mass_residual = core._sum(mass_terms)
    mass_scale = max(abs(initial[108]), abs(final[108]), core._sum(map(abs, mass_terms)))
    mass_budget = 64 * (index + 1) * ulp(mass_scale)
    combined_terms = (dm, ratio * (c1 - c0), *(ratio * t[k] for k in
        ("removal_leaf", "removal_stem_root", "terminal_fruit_carbohydrate")),
        -t["co2_ventilation_to_air"], -t["co2_external_to_air"])
    combined_residual = core._sum(combined_terms)
    combined_scale = max(abs(core._sum((initial[108], ratio * c0))),
                         abs(core._sum((final[108], ratio * c1))), core._sum(map(abs, combined_terms)))
    combined_budget = core._sum((mass_budget, ratio * carbohydrate_budget,
                                64 * (index + 1) * ulp(combined_scale)))
    _need(isfinite(mass_budget) and isfinite(combined_budget) and abs(mass_residual) <= mass_budget
          and abs(combined_residual) <= combined_budget, "BALANCE_HOLD: unresolved CO2 inventory/carbon equivalent")
    return ({"air_co2": core._q(mass_residual, CO2_UNIT),
             "crop_air_carbon_equivalent": core._q(combined_residual, CO2_UNIT)},
            {"air_co2": core._q(mass_budget, CO2_UNIT),
             "crop_air_carbon_equivalent": core._q(combined_budget, CO2_UNIT)})


def integrate(*, scenario, solar, ventilation, co2, step_seconds, step_count,
              growth_profile, cohort_profile, transport_profile, exchange_profile):
    """Advance one bounded event-free interval with actual current CO2 feedback."""
    _need(type(step_seconds) in (int, float), "BUDGET_HOLD: numeric step required")
    try:
        dt = float(step_seconds)
    except OverflowError as exc:
        raise Co2IntegrationHold("BUDGET_HOLD: unrepresentable step") from exc
    _need(isfinite(dt) and dt > 0 and type(step_count) is int and 1 <= step_count <= 4096,
          "BUDGET_HOLD: positive step and1..4096 integer steps required")
    _need(isfinite(dt * step_count) and 0 < dt * step_count <= 600, "BUDGET_HOLD:600s research horizon")
    profiles = dict(growth_profile=growth_profile, cohort_profile=cohort_profile,
                    transport_profile=transport_profile, exchange_profile=exchange_profile)
    errors = (joint.JointClimateHold, core.JointIntegrationHold, OverflowError, ValueError, ZeroDivisionError)
    try:
        first = rhs.evaluate_rhs(scenario=scenario, solar=solar, ventilation=ventilation, co2=co2, **profiles)
        base, sun, weather, boundary = (first[key] for key in ("scenario", "solar", "ventilation", "co2"))
        initial = state = core._state(base) + (base["climate_state"]["air_co2_mass"]["value"],)
        cumulative = (0.0,) * len(FLUX_UNITS); current = _values(first)
        samples = [_sample(0, dt, base, state, first)]
        latent, reference = exchange_profile.values["latent_heat"], base["parameters"]["reference_temperature"]["value"]
        def balances(candidate, totals, following, index):
            a, b = core._balances(initial[:108], candidate[:108], totals[:22], first["solar_rhs"]["joint_rhs"],
                following[2]["solar_rhs"]["joint_rhs"], index, latent, reference)
            c, d = previous.vent_joint._partitions(totals[:25], base, index, dt, latent)
            e, f = previous._partitions(totals[:41], index)
            g, h = _co2_balances(initial, candidate, totals, index, b["carbohydrate"]["value"])
            return {**a, **c, **e, **g}, {**b, **d, **f, **h}
        residuals, budgets = balances(state, cumulative, current, 0)
    except errors as exc:
        raise _held(exc, 0, "initial", None) from exc
    for index in range(1, step_count + 1):
        phase = "k2"
        try:
            k1, j1, _ = current
            k2, j2, _ = _evaluate(base, sun, weather, boundary, core._advance(state, k1, dt / 2), profiles)
            phase = "k3"
            k3, j3, _ = _evaluate(base, sun, weather, boundary, core._advance(state, k2, dt / 2), profiles)
            phase = "k4"
            k4, j4, _ = _evaluate(base, sun, weather, boundary, core._advance(state, k3, dt), profiles)
            phase = "endpoint"
            candidate = core._advance(state, core._weighted(k1, k2, k3, k4), dt)
            totals = core._advance(cumulative, core._weighted(j1, j2, j3, j4), dt)
            following = _evaluate(base, sun, weather, boundary, candidate, profiles)
            phase = "endpoint_balance"
            residuals, budgets = balances(candidate, totals, following, index)
        except errors as exc:
            raise _held(exc, index, phase, samples[-1]) from exc
        state, cumulative, current = candidate, totals, following
        samples.append(_sample(index, dt, base, state, current[2]))
    numerical = {"method": "shared-stage-fixed-rk4-v1", "step_seconds": dt, "step_count": step_count,
                 "duration_seconds": dt * step_count, "state_count": 109, "ledger_count": 44,
                 "coupled_rhs_evaluations": 4 * step_count + 1, "extra_validation_RHS_evaluations": 0,
                 "component_evaluations_each": 4 * step_count + 1, "forcing_sampling": POLICY["sampling"],
                 "roundoff_rule": "64-ulp-per-step-ledger-v1", "time_coordinate": "elapsed_seconds_no_UTC_checkpoint"}
    components = {**joint.COMPONENT_CODE_SHA256, "core_integration": core.CODE_SHA256,
                  "solar_integration_primitives": previous.CODE_SHA256, "ventilation_integration_primitives": previous.vent_joint.CODE_SHA256,
                  "CO2_RHS": rhs.CODE_SHA256, **first["component_code_sha256"]}
    bound = {"model_version": VERSION, "code_sha256": CODE_SHA256, "input_sha256": first["input_sha256"],
             "component_code_sha256": components, "profile_sha256": first["profile_sha256"],
             "policy_sha256": core._hash({"RHS": first["policy_sha256"], "solar": first["solar_rhs"]["policy_sha256"],
                                          "integration": POLICY}), "numerical": numerical}
    transfers = {k: core._q(v, FLUX_UNITS[k]) for k, v in zip(FLUX_UNITS, cumulative, strict=True)}
    return {**bound, "calculation_sha256": core._hash(bound), "source_sha256": {**first["source_sha256"],
            "solar": first["solar_rhs"]["source_sha256"]}, "notice_sha256": first["solar_rhs"]["notice_sha256"],
            "initial_RHS_calculation_sha256": first["calculation_sha256"], "state_schema_version": rhs.STATE_SCHEMA,
            "clock_contract": joint.CLOCK_CONTRACT, "ledger_schema_version": "joint-solar-co2-ledgers-v1",
            "scenario": base, "solar": sun, "ventilation": weather, "co2": boundary, "samples": samples,
            "integrated_transfers": transfers, "canopy_water_boundary": core._q(-transfers["canopy_to_air_vapor"]["value"], core.WATER),
            "balance_residuals": residuals, "balance_budgets": budgets, "scope": "software_research_only",
            "claim_scope": "synthetic_joint_co2_solar_integration_only", "G0_G4": "not_assessed"}
