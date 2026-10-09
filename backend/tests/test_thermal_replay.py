"""Raw-byte replay and adjacent trace carry are distinct from gate acceptance."""

import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.thermal import ThermalHold, calculate_fixture, verify_replay


ROOT = Path(__file__).resolve().parents[2]


def inputs():
    return tuple((ROOT / "fixtures" / name).read_bytes() for name in (
        "manifest-v2.json", "synthetic-weather-v1.json", "synthetic-thermal-parameters-v1.json"
    ))


def kwargs():
    return dict(decision_id="synthetic-decision-v1", decision_at_utc="2026-09-28T00:00:00Z",
                input_snapshot_id="synthetic-input-snapshot-v1")


def test_replay_is_byte_identical_and_second_hour_carries_raw_previous_trace():
    raw = calculate_fixture(*inputs(), **kwargs())
    assert raw == calculate_fixture(*inputs(), **kwargs())
    assert verify_replay(raw, *inputs(), **kwargs())
    first, second = map(json.loads, raw)
    digest = hashlib.sha256(raw[0]).hexdigest()
    assert first["trace_id"] != second["trace_id"]
    for field in ("temperature", "humidity_ratio"):
        carried = second["initial_state"][field]
        pointer = f"/steps/{len(first['steps']) - 1}/state_end/{field}"
        assert carried["value"] == first["steps"][-1]["state_end"][field]["value"]
        assert carried["previous_trace_id"] == first["trace_id"]
        assert carried["previous_trace_sha256"] == digest
        assert carried["previous_state_pointer"] == pointer
        assert carried["basis_ref"] == f"trace-sha256:{digest}#{pointer}"


def test_tampered_raw_trace_and_incomplete_set_fail_replay():
    raw = list(calculate_fixture(*inputs(), **kwargs()))
    with pytest.raises(ThermalHold, match="REPLAY_HOLD"):
        verify_replay(raw[:1], *inputs(), **kwargs())
    first = json.loads(raw[0])
    first["steps"][-1]["state_end"]["temperature"]["value"] += 1
    raw[0] = json.dumps(first, sort_keys=True).encode()
    with pytest.raises(ThermalHold, match="REPLAY_HOLD"):
        verify_replay(raw, *inputs(), **kwargs())


def test_accepted_status_cannot_be_inserted_before_server_gate():
    raw = list(calculate_fixture(*inputs(), **kwargs()))
    first = json.loads(raw[0])
    assert first["run_status"] == "candidate"
    first["run_status"] = "accepted"
    raw[0] = json.dumps(first, sort_keys=True, separators=(",", ":")).encode()
    with pytest.raises(ThermalHold, match="REPLAY_HOLD"):
        verify_replay(raw, *inputs(), **kwargs())
    second = json.loads(raw[1])
    assert second["initial_state"]["temperature"]["previous_trace_sha256"] != hashlib.sha256(raw[0]).hexdigest()


def test_run_identity_disambiguates_fields_and_decision_time():
    first = json.loads(calculate_fixture(*inputs(), decision_id="a",
                                         decision_at_utc="2026-09-28T00:00:00Z",
                                         input_snapshot_id="bc")[0])
    split = json.loads(calculate_fixture(*inputs(), decision_id="ab",
                                         decision_at_utc="2026-09-28T00:00:00Z",
                                         input_snapshot_id="c")[0])
    later_raw = calculate_fixture(*inputs(), decision_id="a",
                                  decision_at_utc="2026-10-01T00:00:00Z",
                                  input_snapshot_id="bc")
    later = json.loads(later_raw[0])
    assert len({first["run_id"], split["run_id"], later["run_id"]}) == 3
    with pytest.raises(ThermalHold, match="REPLAY_HOLD"):
        verify_replay(later_raw, *inputs(), decision_id="a",
                      decision_at_utc="2026-09-28T00:00:00Z", input_snapshot_id="bc")


@pytest.mark.parametrize("field,value", [
    ("decision_id", 1), ("input_snapshot_id", 1),
    ("decision_id", ""), ("input_snapshot_id", ""),
])
def test_nonstring_or_empty_identity_is_controlled_hold(field, value):
    arguments = kwargs()
    arguments[field] = value
    with pytest.raises(ThermalHold, match="INPUT_HOLD"):
        calculate_fixture(*inputs(), **arguments)


def test_manifest_or_weather_raw_byte_mutation_holds():
    raw = list(inputs())
    raw[1] += b"\n"
    with pytest.raises(ThermalHold, match="PIN_HOLD"):
        calculate_fixture(*raw, **kwargs())
