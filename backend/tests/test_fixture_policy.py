"""Policy checks for self-authored inputs, not thermal/economic engine or G1 results."""

import copy
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from pydantic import TypeAdapter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.market import MarketContext, validate_first_g1_use


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "fixtures"
FILES = ("synthetic-weather-v1.json", "synthetic-economics-v1.json")
UTC_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
DECIMAL_TEXT = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
UNITS = {
    "T_o": "K", "phi_o": "1", "p_o": "Pa",
    "solar_interval_energy": "J/m²",
}
ECON_UNITS = {"kg", "KRW", "KRW/kg"}
KST = ZoneInfo("Asia/Seoul")
FORBIDDEN_CLAIM_KEYS = {
    "g0_evidence_id", "g2_evidence_id", "g3a_evidence_id", "g3b_evidence_id",
    "market_snapshot_id", "forecast_run_id", "run_status", "g0_status",
}


def read_fixtures():
    manifest = json.loads((FIXTURES / "manifest-v1.json").read_bytes())
    weather = json.loads((FIXTURES / FILES[0]).read_bytes())
    economics = json.loads((FIXTURES / FILES[1]).read_bytes())
    return manifest, weather, economics


def utc(value):
    assert isinstance(value, str) and UTC_STAMP.fullmatch(value), value
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo == timezone.utc
    return parsed


def economic_value(record, unit):
    assert set(record) == {
        "value", "unit", "origin", "evidence_level", "assumption_scope"
    }
    assert record["unit"] == unit
    assert record["origin"] == "user"
    assert record["evidence_level"] == "assumed"
    assert record["assumption_scope"] == "self-authored algebraic sentinel v1"
    assert isinstance(record["value"], str) and DECIMAL_TEXT.fullmatch(record["value"])
    return Decimal(record["value"])


def all_economic_records(obj):
    if isinstance(obj, dict):
        if "value" in obj:
            yield obj
        else:
            for item in obj.values():
                yield from all_economic_records(item)
    elif isinstance(obj, list):
        for item in obj:
            yield from all_economic_records(item)


def reject_bare_economic_numbers(obj, key=None):
    if isinstance(obj, dict):
        for name, item in obj.items():
            reject_bare_economic_numbers(item, name)
    elif isinstance(obj, list):
        for item in obj:
            reject_bare_economic_numbers(item, key)
    elif type(obj) in (int, float, Decimal):
        raise AssertionError(f"bare economic number at {key}")
    elif isinstance(obj, str) and key != "value":
        try:
            Decimal(obj.strip())
        except InvalidOperation:
            pass
        else:
            raise AssertionError(f"unwrapped numeric text at {key}")


def exact_keys(obj, expected):
    assert isinstance(obj, dict) and set(obj) == set(expected), expected


def check_pinned_bytes(entry, raw):
    digest = hashlib.sha256(raw).hexdigest()
    assert entry["sha256"] == digest
    assert entry["content_id"] == f"sha256:{digest}"
    assert entry["byte_length"] == len(raw)


def check_economic_input_shape(economics):
    exact_keys(economics, {
        "fixture_id", "synthetic", "claim_scope", "author_intent", "decision_at_utc",
        "accounting_timezone", "accounting_day_kst", "units", "market_context",
        "assessment_intent", "baseline", "joint_stress",
    })
    exact_keys(economics["units"], {"quantity", "money", "unit_price"})
    exact_keys(economics["market_context"], {"kind", "hold_report_id"})
    base = economics["baseline"]
    exact_keys(base, {
        "harvest_at_utc", "packout_at_utc", "disposal_at_utc", "harvest",
        "saleable_packout", "unsaleable_cull", "cull_disposal",
        "opening_saleable_inventory", "closing_saleable_inventory", "sale",
        "collection", "costs", "returns_policy",
    })
    exact_keys(base["sale"], {
        "grade", "channel", "dispatch_at_utc", "delivery_at_utc", "inspection_at_utc",
        "recognized_at_utc", "recognized_quantity",
        "farm_contract_price_before_deductions", "revenue_rule",
    })
    exact_keys(base["collection"], {"collected_at_utc", "amount"})
    assert isinstance(base["costs"], list) and len(base["costs"]) == 2
    for cost in base["costs"]:
        exact_keys(cost, {
            "id", "incurred_at_utc", "paid_at_utc", "quantity", "unit_cost",
            "payment_amount", "scope",
        })
    shock = economics["joint_stress"]
    exact_keys(shock, {
        "id", "application", "conditional_only", "drivers", "consequences",
        "timing", "collection_at_utc", "cost_payment_timing", "no_probability",
        "retains_baseline", "dispatch_at_utc", "delivery_at_utc", "inspection_at_utc",
        "recognized_at_utc", "production_payment_at_utc", "dispatch_payment_at_utc",
    })
    exact_keys(shock["drivers"], {"demand", "supply", "macro"})
    for driver in shock["drivers"].values():
        exact_keys(driver, {"assumption", "consequence_ref"})
    exact_keys(shock["consequences"], {
        "sale_cap", "farm_contract_price_before_deductions", "production_unit_cost",
        "recognized_quantity", "closing_saleable_inventory", "collection_amount",
        "production_payment_amount", "dispatch_service_payment_amount",
    })


def reject_forbidden_claims(obj):
    if isinstance(obj, dict):
        assert not FORBIDDEN_CLAIM_KEYS.intersection(obj)
        assert obj.get("status") != "pass"
        for item in obj.values():
            reject_forbidden_claims(item)
    elif isinstance(obj, list):
        for item in obj:
            reject_forbidden_claims(item)


def check_weather(weather):
    reject_forbidden_claims(weather)
    assert weather["fixture_id"] == "synthetic-weather-v1"
    assert weather["synthetic"] is True
    assert weather["claim_scope"] == "synthetic_g1_software_input_only"
    assert "run_status" not in weather
    intervals = weather["intervals"]
    assert len(intervals) >= 2
    assert intervals[0]["start_utc"] == weather["start_utc"]
    assert intervals[-1]["end_utc"] == weather["end_utc"]
    previous_end = None
    zero_solar = False
    for interval in intervals:
        start, end = utc(interval["start_utc"]), utc(interval["end_utc"])
        assert start < end
        if previous_end is not None:
            assert start == previous_end, "weather gap or overlap"
        previous_end = end
        assert set(interval["values"]) == set(UNITS)
        for name, unit in UNITS.items():
            value = interval["values"][name]
            assert set(value) == {"value", "unit", "origin", "basis_ref", "version", "method"}
            assert value["unit"] == unit
            assert value["origin"] == "assumed"
            assert value["basis_ref"] == weather["assumption_id"]
            assert value["version"] == "v1"
            assert value["method"].startswith("Self-authored algebraic sentinel")
            assert type(value["value"]) in (int, float)
        vals = interval["values"]
        assert vals["T_o"]["value"] > 0
        assert 0 <= vals["phi_o"]["value"] <= 1
        assert vals["p_o"]["value"] > 0
        assert vals["solar_interval_energy"]["value"] >= 0
        zero_solar |= vals["solar_interval_energy"]["value"] == 0
    assert zero_solar
    assert weather["solar_semantics"] == "interval_total_J_per_m2_not_instantaneous_W_per_m2"
    assert "w_o" not in weather and "solar_W" not in weather
    assert all("w_o" not in item["values"] and "solar_W" not in item["values"]
               for item in intervals)


def check_economics(economics):
    reject_forbidden_claims(economics)
    check_economic_input_shape(economics)
    assert economics["fixture_id"] == "synthetic-economics-v1"
    assert economics["synthetic"] is True
    assert economics["claim_scope"] == "conditional_algebraic_sentinel_input_only"
    assert economics["assessment_intent"] == "hold"
    assert economics["accounting_timezone"] == "Asia/Seoul"
    assert economics["market_context"] == {
        "kind": "unavailable", "hold_report_id": "market-hold-synthetic-v1"
    }
    market = TypeAdapter(MarketContext).validate_python(economics["market_context"])
    records = list(all_economic_records(economics))
    assert records
    reject_bare_economic_numbers(economics)
    for record in records:
        assert record["unit"] in ECON_UNITS
        economic_value(record, record["unit"])
    validate_first_g1_use(
        market,
        economic_inputs=[{key: r[key] for key in ("origin", "evidence_level", "assumption_scope")}
                         for r in records],
        assessment_status=economics["assessment_intent"],
    )

    decision = utc(economics["decision_at_utc"])
    base = economics["baseline"]
    sale = base["sale"]
    ordered = ["harvest_at_utc", "packout_at_utc", "dispatch_at_utc",
               "delivery_at_utc", "inspection_at_utc", "recognized_at_utc"]
    times = [utc(base[name]) if name in base else utc(sale[name]) for name in ordered]
    assert decision < times[0]
    assert times == sorted(times)
    assert {t.astimezone(KST).date() for t in times} == {
        datetime.fromisoformat(economics["accounting_day_kst"]).date()
    }
    assert utc(base["disposal_at_utc"]).date() == times[0].date()
    assert utc(base["collection"]["collected_at_utc"]) > times[-1]
    assert utc(base["collection"]["collected_at_utc"]).astimezone(
        KST).date() != times[-1].astimezone(KST).date()

    h = economic_value(base["harvest"], "kg")
    p = economic_value(base["saleable_packout"], "kg")
    s = economic_value(sale["recognized_quantity"], "kg")
    opening = economic_value(base["opening_saleable_inventory"], "kg")
    closing = economic_value(base["closing_saleable_inventory"], "kg")
    cull = economic_value(base["unsaleable_cull"], "kg")
    disposal = economic_value(base["cull_disposal"], "kg")
    assert h >= p >= s
    assert h == p + cull and cull == disposal
    assert closing == opening + p - s
    assert economic_value(base["collection"]["amount"], "KRW") == (
        s * economic_value(sale["farm_contract_price_before_deductions"], "KRW/kg")
    )
    assert closing > 0 and s < p
    assert sale["grade"] == "sentinel_grade" and sale["channel"] == "sentinel_channel"
    assert sale["revenue_rule"] == "recognized_quantity_times_contract_price_only"
    assert "inventory_revenue" not in str(base)
    for cost in base["costs"]:
        assert utc(cost["incurred_at_utc"]) >= decision
        assert utc(cost["paid_at_utc"]) > utc(cost["incurred_at_utc"])
        assert utc(cost["paid_at_utc"]) != utc(base["collection"]["collected_at_utc"])
        assert economic_value(cost["payment_amount"], "KRW") == (
            economic_value(cost["quantity"], "kg")
            * economic_value(cost["unit_cost"], "KRW/kg")
        )

    shock = economics["joint_stress"]
    assert shock["application"] == "apply_demand_supply_macro_together_only"
    assert set(shock["drivers"]) == {"demand", "supply", "macro"}
    assert set(shock["consequences"]) == {
        "sale_cap", "farm_contract_price_before_deductions", "production_unit_cost",
        "recognized_quantity", "closing_saleable_inventory", "collection_amount",
        "production_payment_amount", "dispatch_service_payment_amount",
    }
    assert set(shock["retains_baseline"]) == {
        "harvest", "saleable_packout", "unsaleable_cull", "cull_disposal",
        "opening_saleable_inventory", "grade", "channel",
    }
    assert shock["drivers"]["demand"]["consequence_ref"] == "sale_cap"
    assert shock["drivers"]["supply"]["consequence_ref"] == "farm_contract_price_before_deductions"
    assert shock["drivers"]["macro"]["consequence_ref"] == "production_unit_cost"
    c = shock["consequences"]
    cap = economic_value(c["sale_cap"], "kg")
    ss = economic_value(c["recognized_quantity"], "kg")
    assert ss <= cap and ss <= p
    assert economic_value(c["closing_saleable_inventory"], "kg") == opening + p - ss
    assert economic_value(c["collection_amount"], "KRW") == (
        ss * economic_value(c["farm_contract_price_before_deductions"], "KRW/kg")
    )
    assert economic_value(c["production_unit_cost"], "KRW/kg") > (
        economic_value(base["costs"][0]["unit_cost"], "KRW/kg")
    )
    assert economic_value(c["production_payment_amount"], "KRW") == (
        h * economic_value(c["production_unit_cost"], "KRW/kg")
    )
    assert economic_value(c["dispatch_service_payment_amount"], "KRW") == (
        ss * economic_value(base["costs"][1]["unit_cost"], "KRW/kg")
    )
    stress_times = [utc(shock[name]) for name in (
        "dispatch_at_utc", "delivery_at_utc", "inspection_at_utc", "recognized_at_utc"
    )]
    assert stress_times == sorted(stress_times)
    assert {t.astimezone(KST).date() for t in stress_times} == {
        times[-1].astimezone(KST).date()
    }
    assert utc(shock["collection_at_utc"]) > stress_times[-1]
    for key in ("production_payment_at_utc", "dispatch_payment_at_utc"):
        assert utc(shock[key]) > stress_times[-1]
        assert utc(shock[key]) != utc(shock["collection_at_utc"])
    assert "probability" not in shock


def check_manifest(manifest, weather, economics):
    reject_forbidden_claims(manifest)
    assert manifest["manifest_id"] == "synthetic-fixture-manifest-v1"
    assert manifest["claim_scope"] == "synthetic_g1_software_input_only"
    assert manifest["assessment_intent"] == "hold"
    assert manifest["synthetic_input_review_id"] == "self-review-synthetic-fixtures-v1"
    assert manifest["market_context"] == economics["market_context"]
    report = manifest["market_hold_report"]
    assert report["hold_report_id"] == economics["market_context"]["hold_report_id"]
    assert report["decision_at_utc"] == economics["decision_at_utc"]
    assert report["reasons"] and report["missing_evidence"]
    assert "NO_APPROVED_MARKET_SNAPSHOT" in report["reasons"]
    assert "G0_APPROVED_MARKET_SOURCE" in report["missing_evidence"]
    assert "market_snapshot_id" not in str(manifest).lower()
    assert "g0_pass" not in str(manifest).lower()
    assert "g2_pass" not in str(manifest).lower()
    assert "g3_pass" not in str(manifest).lower()
    assert "run_status" not in str(manifest).lower()

    entries = manifest["files"]
    decision = utc(economics["decision_at_utc"])
    assert [entry["path"] for entry in entries] == [f"fixtures/{name}" for name in FILES]
    for entry, fixture in zip(entries, (weather, economics), strict=True):
        raw = (ROOT / entry["path"]).read_bytes()
        check_pinned_bytes(entry, raw)
        assert entry["fixture_id"] == fixture["fixture_id"]
        assert entry["synthetic"] is True
        assert entry["author"] == "OpenSmartFarmSim fixture authors"
        assert entry["method"].startswith("Self-authored algebraic sentinel")
        assert entry["vintage_id"] and entry["revision_id"] == "r1"
        stamps = [utc(entry[key]) for key in (
            "generated_at_utc", "published_at_utc", "available_at_utc", "retrieved_at_utc"
        )]
        assert stamps == sorted(stamps)
        assert all(stamp <= decision for stamp in stamps)
        assert entry["source_locator"] == entry["path"]
        assert entry["product_id"] == entry["fixture_id"]
        assert entry["rights"] == {
            "license": "Apache-2.0", "holder": "OpenSmartFarmSim fixture authors",
            "access": "allowed", "store": "allowed", "transform": "allowed",
            "display": "allowed", "redistribute": "allowed",
        }
        assert entry["qc"]["status"] == "self_checked_synthetic"
        assert entry["review"]["status"] == "self_reviewed_synthetic"
        assert entry["review"]["reviewer"] == "OpenSmartFarmSim fixture authors"
        assert entry["review"]["review_id"]
        assert entry["review"]["review_id"] == manifest["synthetic_input_review_id"]
        assert entry["time_semantics"] and entry["variable_units"]
    assert entries[0]["observed_start_utc"] == weather["start_utc"]
    assert entries[0]["observed_end_utc"] == weather["end_utc"]
    assert entries[0]["observation_status"] == "hypothetical interval, not observed"
    assert decision < utc(weather["start_utc"]) < utc(weather["end_utc"])
    assert entries[0]["variable_units"] == UNITS
    assert entries[0]["time_semantics"]["solar_interval_energy"] == weather["solar_semantics"]
    assert entries[1]["variable_units"] == economics["units"]
    assert entries[1]["observed_start_utc"] is None
    assert entries[1]["observed_end_utc"] is None
    assert entries[1]["observation_status"] == "not observed; user conditional event assumptions"
    assert entries[1]["time_semantics"]["accounting_timezone"] == "Asia/Seoul"
    assert "sha256" not in weather and "sha256" not in economics


def test_fixture_policy():
    manifest, weather, economics = read_fixtures()
    check_weather(weather)
    check_economics(economics)
    check_manifest(manifest, weather, economics)


def test_changed_byte_rejected():
    manifest, _, _ = read_fixtures()
    for entry in manifest["files"]:
        raw = (ROOT / entry["path"]).read_bytes()
        check_pinned_bytes(entry, raw)
        changed = bytearray(raw)
        changed[0] ^= 1
        with pytest.raises(AssertionError):
            check_pinned_bytes(entry, changed)


def test_weather_intervals_convert_to_kst_algebraic_sentinels():
    _, weather, _ = read_fixtures()
    intervals = weather["intervals"]
    kst = ZoneInfo("Asia/Seoul")
    assert [
        (utc(item["start_utc"]).astimezone(kst).isoformat(),
         utc(item["end_utc"]).astimezone(kst).isoformat(),
         item["values"]["solar_interval_energy"]["value"])
        for item in intervals
    ] == [
        ("2026-10-15T17:00:00+09:00", "2026-10-15T18:00:00+09:00", 3600),
        ("2026-10-15T18:00:00+09:00", "2026-10-15T19:00:00+09:00", 0),
    ]


@pytest.mark.parametrize("change", ["gap", "overlap", "solar_unit", "temperature_unit", "non_utc"])
def test_weather_mutations_rejected(change):
    _, weather, _ = read_fixtures()
    weather = copy.deepcopy(weather)
    second = weather["intervals"][1]
    if change == "gap":
        second["start_utc"] = "2026-10-15T09:01:00Z"
    elif change == "overlap":
        second["start_utc"] = "2026-10-15T08:59:00Z"
    elif change == "solar_unit":
        second["values"]["solar_interval_energy"]["unit"] = "W/m²"
    elif change == "temperature_unit":
        second["values"]["T_o"]["unit"] = "°C"
    else:
        second["start_utc"] = "2026-10-15T22:00:00+09:00"
    with pytest.raises(AssertionError):
        check_weather(weather)


@pytest.mark.parametrize("change", ["inspection_day", "sales_exceed_packout", "inventory",
                                    "missing_origin", "forged_origin", "missing_scope", "market_hold",
                                    "stress_price_unit", "bare_number", "collection_mismatch",
                                    "forged_g0_pass"])
def test_economic_mutations_rejected(change):
    _, _, economics = read_fixtures()
    economics = copy.deepcopy(economics)
    base = economics["baseline"]
    if change == "inspection_day":
        base["sale"]["inspection_at_utc"] = "2026-10-16T03:00:00Z"
    elif change == "sales_exceed_packout":
        base["sale"]["recognized_quantity"]["value"] = "9"
    elif change == "inventory":
        base["closing_saleable_inventory"]["value"] = "99"
    elif change == "missing_origin":
        del economics["joint_stress"]["consequences"]["sale_cap"]["origin"]
    elif change == "forged_origin":
        base["sale"]["farm_contract_price_before_deductions"]["origin"] = "source"
    elif change == "missing_scope":
        del base["costs"][0]["unit_cost"]["assumption_scope"]
    elif change == "stress_price_unit":
        economics["joint_stress"]["consequences"]["farm_contract_price_before_deductions"]["unit"] = "KRW"
    elif change == "bare_number":
        economics["joint_stress"]["bare_sale_cap"] = 4
    elif change == "collection_mismatch":
        economics["joint_stress"]["consequences"]["collection_amount"]["value"] = "999"
    elif change == "forged_g0_pass":
        economics["g0_status"] = "pass"
    else:
        economics["market_context"]["hold_report_id"] = "forged-hold"
    with pytest.raises((AssertionError, ValueError)):
        check_economics(economics)


@pytest.mark.parametrize("location,value", [
    ("baseline", 123),
    ("baseline", "123"),
    ("baseline", "-123"),
    ("joint_stress", 123),
    ("joint_stress", "123"),
    ("driver", 123),
    ("baseline", {"value": "123", "unit": "KRW/kg", "origin": "user",
                  "evidence_level": "assumed",
                  "assumption_scope": "self-authored algebraic sentinel v1"}),
])
def test_unlisted_economic_input_rejected(location, value):
    _, _, economics = read_fixtures()
    target = (economics["joint_stress"]["drivers"]["demand"] if location == "driver"
              else economics[location])
    target["rogue_price"] = value
    with pytest.raises((AssertionError, ValueError)):
        check_economics(economics)


def test_manifest_hash_and_hold_mutations_rejected():
    manifest, weather, economics = read_fixtures()
    for field, bad in (("sha256", "0" * 64), ("content_id", "sha256:" + "0" * 64),
                       ("byte_length", 1)):
        changed = copy.deepcopy(manifest)
        changed["files"][0][field] = bad
        with pytest.raises(AssertionError):
            check_manifest(changed, weather, economics)
    changed = copy.deepcopy(manifest)
    changed["market_hold_report"]["hold_report_id"] = "forged-hold"
    with pytest.raises(AssertionError):
        check_manifest(changed, weather, economics)


def test_manifest_rejects_observed_or_decision_time_weather():
    manifest, weather, economics = read_fixtures()
    observed = copy.deepcopy(manifest)
    observed["files"][0]["observation_status"] = "observed"
    with pytest.raises(AssertionError):
        check_manifest(observed, weather, economics)

    later_decision = copy.deepcopy(economics)
    later_decision["decision_at_utc"] = "2026-10-16T00:00:00Z"
    late_manifest = copy.deepcopy(manifest)
    late_manifest["market_hold_report"]["decision_at_utc"] = later_decision["decision_at_utc"]
    with pytest.raises(AssertionError):
        check_manifest(late_manifest, weather, later_decision)


@pytest.mark.parametrize("field", ["available_at_utc", "retrieved_at_utc"])
def test_manifest_rejects_input_unavailable_at_decision(field):
    manifest, weather, economics = read_fixtures()
    changed = copy.deepcopy(manifest)
    changed["files"][0][field] = "2026-09-28T00:00:01Z"
    with pytest.raises(AssertionError):
        check_manifest(changed, weather, economics)
