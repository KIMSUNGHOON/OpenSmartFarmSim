"""Lossless canonical JSON for a conditional market and economic result."""

from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
import json
import re

from pydantic import TypeAdapter

from .market_scenario import MarketScenarioResult


_RESULT = TypeAdapter(MarketScenarioResult)
_DECIMAL = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]+)?\Z")
_ENTRY_KEYS = {"batch_id", "grade", "channel", "quantity_kg"}
_MAX_BYTES = 1048576


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("duplicate market result JSON key")
        value[key] = item
    return value


def _name(value):
    return (type(value) is str and bool(value) and value == value.strip() and
            all(ord(char) >= 32 for char in value))


def _inventory_entries(inventory):
    if inventory is None:
        return None
    if type(inventory) is not dict or len(inventory) > 10000:
        raise ValueError("market result inventory invalid")
    entries = []
    for key, amount in inventory.items():
        if (type(key) is not tuple or len(key) != 3 or
                not all(_name(item) for item in key) or
                not isinstance(amount, Decimal) or not amount.is_finite() or amount < 0):
            raise ValueError("market result inventory entry invalid")
        entries.append({"batch_id": key[0], "grade": key[1], "channel": key[2],
                        "quantity_kg": "0" if amount == 0 else format(amount, "f")})
    return sorted(entries, key=lambda item: (item["batch_id"], item["grade"], item["channel"]))


def encode_market_result(result):
    if not isinstance(result, MarketScenarioResult):
        raise ValueError("market result type invalid")
    payload = _RESULT.dump_python(result, mode="json")
    payload["economic_result"]["closing_inventory"] = _inventory_entries(
        result.economic_result.closing_inventory)
    raw = _canonical({"codec_version": "market-result-v1", "result": payload})
    if len(raw) > _MAX_BYTES:
        raise ValueError("market result exceeds size limit")
    return raw


def decode_market_result(raw):
    if type(raw) is not bytes or not 1 <= len(raw) <= _MAX_BYTES:
        raise ValueError("market result raw bytes invalid")
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
        if (_canonical(value) != raw or type(value) is not dict or
                set(value) != {"codec_version", "result"} or
                value["codec_version"] != "market-result-v1" or
                type(value["result"]) is not dict or
                type(value["result"].get("economic_result")) is not dict):
            raise ValueError("market result canonical envelope invalid")
        entries = value["result"]["economic_result"].get("closing_inventory")
        inventory = None
        if entries is not None:
            if type(entries) is not list or len(entries) > 10000:
                raise ValueError("market result inventory list invalid")
            inventory = {}
            for entry in entries:
                if (type(entry) is not dict or set(entry) != _ENTRY_KEYS or
                        not all(_name(entry[key]) for key in
                                ("batch_id", "grade", "channel")) or
                        type(entry["quantity_kg"]) is not str or
                        not _DECIMAL.fullmatch(entry["quantity_kg"])):
                    raise ValueError("market result inventory entry invalid")
                key = (entry["batch_id"], entry["grade"], entry["channel"])
                if key in inventory:
                    raise ValueError("market result inventory repeats a lane")
                inventory[key] = Decimal(entry["quantity_kg"])
        parsed = deepcopy(value["result"])
        parsed["economic_result"]["closing_inventory"] = None
        result = _RESULT.validate_json(_canonical(parsed))
        result = replace(result, economic_result=replace(
            result.economic_result, closing_inventory=inventory))
        if encode_market_result(result) != raw:
            raise ValueError("market result inventory order or value differs")
        return result
    except (UnicodeError, TypeError, KeyError, RecursionError, OverflowError) as exc:
        raise ValueError("market result JSON invalid") from exc
