"""Source C9 net gas exchange; contracts/crop-co2-net-exchange-v1.md defines scope.

Equation attribution: research/crop-co2-stomatal-source-register-20261021.json
and LICENSES/GreenLight-BSD-3-Clause-Clear.txt.
"""
from hashlib import sha256
import json
from math import fsum, isfinite
from pathlib import Path
import re

from . import crop_growth_rates as organ
from . import crop_plant_cohort_rates as cohort
from . import crop_plant_startup_rates as startup
from . import crop_fruit_cohorts as fruit
from . import crop_fruit_startup as fruit_startup
from . import crop_fruit_transport as transport

VERSION = "greenlight-net-crop-co2-exchange-v1"
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
SOURCE_SHA256 = "272a589edf0bb40d1a91b34e883f8e94b9adf747a576be4620c50296c03d7033"
CO2_MOLAR_MASS = 44e-3  # mg/umol, C9; deliberately distinct from the C8 gas helper
CH2O_MOLAR_MASS = 30e-3  # mg/umol, C9 Table9.1
CO2_UNIT = "mg_CO2/m2_floor/s"
PRODUCER_CODE_SHA256 = {module.MODEL_VERSION: sha256(Path(module.__file__).read_bytes()).hexdigest()
                        for module in (organ, cohort, startup)}
PROFILES = {"growth_profile": organ.PROFILE_SHA256, "cohort_profile": fruit.PROFILE_SHA256,
            "transport_profile": transport.PROFILE_SHA256}


class Co2NetExchangeHold(ValueError):
    """The producer/quantity cannot support a net gas exchange calculation."""


def _need(condition, reason):
    if not condition:
        raise Co2NetExchangeHold(reason)


def _quantity(value, unit=organ.RATE_UNIT):
    return {"value": value, "unit": unit}


def _rate(row):
    _need(type(row) is dict and set(row) == {"value", "unit"}, "INPUT_HOLD: closed rate quantity required")
    _need(type(row["unit"]) is str and row["unit"] == organ.RATE_UNIT, "UNIT_HOLD: CH2O floor-area rate required")
    _need(type(row["value"]) in (int, float), "INPUT_HOLD: explicit numeric rate required")
    try:
        value = float(row["value"])
    except OverflowError as exc:
        raise Co2NetExchangeHold("NUMERIC_HOLD: unrepresentable input rate") from exc
    _need(isfinite(value) and value >= 0, "INPUT_HOLD: finite nonnegative source rate required")
    return value


def _identity(rates):
    _need(type(rates) is dict, "INPUT_HOLD: producer rate dictionary required")
    version = rates.get("model_version")
    _need(type(version) is str and version in PRODUCER_CODE_SHA256, "MODEL_HOLD: unsupported crop rate producer")
    _need(rates.get("scope") == "software_research_only", "SCOPE_HOLD: research rate result required")
    digest = rates.get("input_sha256")
    _need(type(digest) is str and re.fullmatch("[0-9a-f]{64}", digest), "IDENTITY_HOLD: canonical input SHA required")
    profiles = rates.get("profile_sha256")
    if version == organ.MODEL_VERSION:
        _need(type(profiles) is str and profiles == organ.PROFILE_SHA256, "PROFILE_HOLD: pinned organ profile required")
        identity = {"profile_sha256": profiles}
    else:
        _need(type(profiles) is dict and profiles == PROFILES, "PROFILE_HOLD: three pinned profiles required")
        components = {"plant": organ.MODEL_VERSION, "cohorts": fruit.MODEL_VERSION}
        if version == startup.MODEL_VERSION:
            components["startup"] = fruit_startup.MODEL_VERSION
            _need(rates.get("policy_sha256") == fruit_startup.POLICY_SHA256,
                  "POLICY_HOLD: pinned startup policy required")
        _need(type(rates.get("component_model_versions")) is dict and rates["component_model_versions"] == components,
              "MODEL_HOLD: incompatible crop component versions")
        identity = {"profile_sha256": dict(profiles), "component_model_versions": components}
        if version == startup.MODEL_VERSION:
            identity["policy_sha256"] = fruit_startup.POLICY_SHA256
    return {"model_version": version, "input_sha256": digest,
            "producer_code_sha256": PRODUCER_CODE_SHA256[version], **identity}


def calculate_exchange(*, rates):
    """Convert consumed same-stage crop rates to paired signed CO2 transfers."""
    identity = _identity(rates)
    photosynthesis = _rate(rates.get("photosynthesis"))
    growth = _rate(rates.get("growth_respiration"))
    if identity["model_version"] == organ.MODEL_VERSION:
        mapping = rates.get("maintenance_respiration")
        _need(type(mapping) is dict and set(mapping) == {"leaf", "stem_root", "fruit"},
              "INPUT_HOLD: three organ maintenance rates required")
    else:
        mapping = rates.get("vegetative_maintenance")
        _need(type(mapping) is dict and set(mapping) == {"leaf", "stem_root"},
              "INPUT_HOLD: leaf/stem maintenance rates required")
        mapping = {**mapping, "fruit": rates.get("fruit_maintenance")}
    maintenance = {name: _rate(mapping[name]) for name in ("leaf", "stem_root", "fruit")}
    try:
        net = fsum((photosynthesis, -growth, *(-value for value in maintenance.values())))
        uptake = net * (CO2_MOLAR_MASS / CH2O_MOLAR_MASS)
    except (OverflowError, ValueError) as exc:
        raise Co2NetExchangeHold("NUMERIC_HOLD: net gas exchange overflow") from exc
    _need(isfinite(net) and isfinite(uptake) and (net == 0 or uptake != 0),
          "NUMERIC_HOLD: unrepresentable net gas exchange")
    carbohydrate = {"photosynthesis": _quantity(photosynthesis), "growth_respiration": _quantity(growth),
                    "maintenance_respiration": {k: _quantity(v) for k, v in maintenance.items()}}
    bound = {"model_version": VERSION, "code_sha256": CODE_SHA256, "source_identity": identity,
             "stoichiometry_version": "c9-co2-44g-ch2o-30g-v1", "carbohydrate": carbohydrate}
    return {**bound, "carbohydrate": {**carbohydrate, "net": _quantity(net)},
            "input_sha256": sha256(json.dumps(bound, sort_keys=True, separators=(",", ":"),
                                                       allow_nan=False).encode()).hexdigest(),
            "source_sha256": SOURCE_SHA256, "scope": "software_research_only",
            "claim_scope": "instantaneous_net_crop_co2_exchange_only", "G0_G4": "not_assessed",
            "co2": {"net_crop_uptake": _quantity(uptake, CO2_UNIT), "air_flux": _quantity(-uptake, CO2_UNIT)},
            "transfer_residual": _quantity(fsum((uptake, -uptake)), CO2_UNIT)}
