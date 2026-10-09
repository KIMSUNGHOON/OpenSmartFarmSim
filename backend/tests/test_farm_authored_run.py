"""Synthetic release and candidate prove preparation bytes, not G1 acceptance."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.farm_authored_run import AuthoredRunHold, build_authored_run_packet
from test_authored_thermal_candidate import pure
from test_farm_authored_release import _fixture, _signed


def _released_candidate(tmp_path):
    candidate = pure()
    first = json.loads(candidate.trace_raws[0])
    service, proof, reviewer, _, _ = _fixture(tmp_path)
    proof = replace(proof,
        registration_sha256=candidate.registration_sha256,
        farm_sha256=first['farm_sha256'],
        numeric_input_sha256=candidate.numeric_input_sha256,
        binding_sha256=first['binding_sha256'],
        base_snapshot_id=first['base_snapshot_id'],
        base_source_sha256=first['base_source_sha256'],
        candidate_id=candidate.candidate_id,
        code_sha256=candidate.code_sha256,
        trace_sha256=candidate.trace_sha256)
    service.completion.verify = lambda *args: proof
    released = service.verify('tenant-1', proof.review_job_id,
        proof.registration_sha256, *_signed(service, proof, reviewer))
    return candidate, released


def test_preparation_binds_final_two_hour_trace_and_review(tmp_path):
    candidate, release = _released_candidate(tmp_path)
    packet = build_authored_run_packet(candidate, release, tenant='tenant-1',
        scenario_id='farm-1', revision='r1',
        registration_sha256=candidate.registration_sha256)
    again = build_authored_run_packet(candidate, release, tenant='tenant-1',
        scenario_id='farm-1', revision='r1',
        registration_sha256=candidate.registration_sha256)
    assert packet == again
    report = json.loads(packet.report_raw)
    traces = [json.loads(raw) for raw in packet.trace_raws]
    assert report['status'] == 'prepared_unpublished'
    assert report['run_id'] == packet.run_id
    assert report['trace_sha256'] == list(packet.trace_sha256)
    assert [len(trace['steps']) for trace in traces] == [60, 60]
    assert all(trace['run_id'] == packet.run_id and trace['status'] == 'accepted'
        and trace['claim_scope'] == 'synthetic_thermal_replay_only'
        and 'purchased_energy' not in trace and 'crop_growth' not in trace
        for trace in traces)
    assert traces[1]['initial_state']['temperature']['previous_trace_sha256'] == sha256(packet.trace_raws[0]).hexdigest()
    assert traces[1]['initial_state']['humidity_ratio']['previous_trace_id'] == traces[0]['trace_id']
    assert traces[1]['initial_state']['temperature']['basis_ref'] == (
        f"trace-sha256:{packet.trace_sha256[0]}#/steps/59/state_end/temperature")
    assert traces[1]['steps'] == json.loads(candidate.trace_raws[1])['steps']
    assert packet.trace_raws[0] != candidate.trace_raws[0]


def test_preparation_holds_mismatched_authority_or_trace(tmp_path):
    candidate, release = _released_candidate(tmp_path)
    kwargs = dict(tenant='tenant-1', scenario_id='farm-1', revision='r1',
                  registration_sha256=candidate.registration_sha256)
    with pytest.raises(AuthoredRunHold):
        build_authored_run_packet(candidate, release, **{**kwargs, 'revision': 'r2'})
    with pytest.raises(AuthoredRunHold):
        build_authored_run_packet(candidate, release, **{**kwargs, 'tenant': 'tenant-2'})
    changed = replace(candidate,
        trace_raws=(candidate.trace_raws[0] + b' ', candidate.trace_raws[1]))
    with pytest.raises(AuthoredRunHold):
        build_authored_run_packet(changed, release, **kwargs)
