"""The market result wire format preserves tuple-key inventory without ambiguity."""

from dataclasses import replace
from decimal import Decimal
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.market_result_codec import decode_market_result, encode_market_result
from app.market_scenario import MarketScenarioService
from test_market_scenario import case


def result():
    repository, request = case()
    candidate = MarketScenarioService(repository).build_candidate(request, "tenant-1")
    return MarketScenarioService(repository).calculate_pinned(
        candidate.scenario_id, candidate.revision, "tenant-1")


def test_actual_market_and_economic_result_round_trips():
    calculated = result()
    raw = encode_market_result(calculated)
    assert decode_market_result(raw) == calculated
    assert encode_market_result(decode_market_result(raw)) == raw
    assert b'"codec_version":"market-result-v1"' in raw
    unresolved = replace(calculated, economic_result=replace(
        calculated.economic_result, closing_inventory=None))
    assert decode_market_result(encode_market_result(unresolved)) == unresolved


def test_inventory_lanes_with_commas_remain_distinct_and_sorted():
    calculated = result()
    inventory = {("batch,one", "grade", "direct"): Decimal("3.00"),
                 ("batch", "one,grade", "direct"): Decimal("4")}
    calculated = replace(calculated, economic_result=replace(
        calculated.economic_result, closing_inventory=inventory))
    raw = encode_market_result(calculated)
    assert decode_market_result(raw) == calculated
    entries = json.loads(raw)["result"]["economic_result"]["closing_inventory"]
    assert len(entries) == 2
    assert entries[0]["batch_id"] == "batch"
    assert entries[1]["batch_id"] == "batch,one"
    reordered = replace(calculated, economic_result=replace(
        calculated.economic_result, closing_inventory=dict(reversed(list(inventory.items())))))
    assert encode_market_result(reordered) == raw


def test_unknown_inventory_and_noncanonical_bytes_fail_closed():
    calculated = result()
    raw = encode_market_result(calculated)
    for changed in (
        lambda value: value["result"]["economic_result"]["closing_inventory"].append(
            value["result"]["economic_result"]["closing_inventory"][0].copy()),
        lambda value: value["result"]["economic_result"]["closing_inventory"][0].update(
            quantity_kg=3.0),
        lambda value: value["result"].update(unexpected=True),
    ):
        value = json.loads(raw)
        changed(value)
        altered = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
        with pytest.raises(ValueError):
            decode_market_result(altered)
    with pytest.raises(ValueError):
        decode_market_result(raw + b" ")
    with pytest.raises(ValueError):
        decode_market_result(b'{"codec_version":"market-result-v1",'
                             b'"codec_version":"market-result-v1","result":{}}')
