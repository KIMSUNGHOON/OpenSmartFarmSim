"""Capture the actual saved-result HTTPS bytes for the web reader contract."""
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path

import pytest

import test_crop_greenhouse_ventilation_runtime as runtime_checks
from test_crop_greenhouse_ventilation_runtime import (
    native, ventilation_config, tls_files, database_cleanup, setup, login_scope,
    login_database, original_login_scope, authoring, farm_setup, profiles, private_config,
)


@runtime_checks.LOGIN
@pytest.mark.parametrize('setup', [None, 'hold'], indirect=True)
def test_capture_original_verified_https_saved_result_for_web(native, monkeypatch):
    original = http.client.HTTPResponse.read
    captured = []

    def read(response, *args, **kwargs):
        raw = original(response, *args, **kwargs)
        if response.status == 200:
            captured.append(raw)
        return raw

    monkeypatch.setattr(http.client.HTTPResponse, 'read', read)
    runtime_checks.test_native_verified_tls_runtime_completed_and_hold_original_bytes(native)
    assert captured == list(native.expected.values())
    rows = [json.loads(raw) for raw in captured]
    assert len(rows) == 3
    assert {r['schema_version'] for r in rows} == {'joint-ventilation-replay-v1'}
    assert len({r['result_id'] for r in rows}) == 1
    assert all(r['reference']['G0_G4'] == 'not_assessed' for r in rows)
    directory = os.environ.get('OSSF_VENTILATION_WEB_EVIDENCE')
    if directory:
        status = native.done['status']
        root = Path(directory)
        for view, raw in zip(native.expected, captured, strict=True):
            with (root/(status+'-'+view+'.wire.json')).open('xb') as stream:
                os.fchmod(stream.fileno(), 0o400)
                stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        evidence = {'actual_scram': True, 'verified_TLS': True, 'original_wire_bytes_equal': True,
            'status': status, 'responses': {view: {'sha256': sha256(raw).hexdigest(), 'bytes': len(raw)}
                for view, raw in zip(native.expected, captured, strict=True)}, 'calls': native.calls,
            'scope': 'owned_synthetic_verified_HTTPS_original_wire_not_measured_data_or_gate_acceptance'}
        with (root/(status+'-capture.json')).open('x') as stream:
            os.fchmod(stream.fileno(), 0o400)
            json.dump(evidence, stream, sort_keys=True); stream.flush(); os.fsync(stream.fileno())
