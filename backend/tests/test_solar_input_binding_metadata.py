"""A small binding view preserves the original signed input record and authority."""
from dataclasses import FrozenInstanceError, replace
import json

import pytest

from test_crop_greenhouse_solar_input_evidence import (
    prepared, profiles, authority, issue, verify, model)


def test_binding_metadata_matches_signed_record_and_returns_detached_values(prepared):
    server = authority(prepared[3])
    raw = issue(server, prepared)
    checked = verify(server, prepared, raw)
    signed = json.loads(raw)['payload']
    record = signed['record']
    expected = {
        'program_id': record['program']['scenario']['input_id'],
        'period': {'start': record['binding']['start_utc'], 'end': record['binding']['end_utc']},
        'context_sha256': record['context_sha256'], 'time_binding_sha256': record['binding_sha256'],
        'initial_state_sha256': record['initial_state_sha256'],
        'model_identity': record['manifest']['identity'],
        'review': signed['review'], 'provenance': record['provenance'],
    }
    assert checked.binding_metadata == expected
    assert checked._raw_record == model._canonical(record) and checked.record == record
    assert len(checked._raw_binding_metadata) < len(checked._raw_record)
    view = checked.binding_metadata
    view['period']['start'] = 'different'
    view['review'].clear()
    view['provenance'].clear()
    view['model_identity'].clear()
    assert checked.binding_metadata == expected and checked.record == record
    with pytest.raises(FrozenInstanceError):
        checked._raw_binding_metadata = b'{}'
    assert checked.rights_or_gate_approval is False


def test_binding_metadata_requires_same_authority_token_as_full_record(prepared):
    server = authority(prepared[3])
    checked = verify(server, prepared, issue(server, prepared))
    forged = replace(checked, _token=object())
    for name in ('record', 'binding_metadata'):
        with pytest.raises(model.SolarInputEvidenceHold):
            getattr(forged, name)


@pytest.mark.parametrize('invalid', [None, b'', bytearray(b'{}'), '{}', b'x' * (model.MAX_EVIDENCE_BYTES + 1)])
def test_binding_metadata_rejects_non_bytes_empty_and_unbounded_storage(prepared, invalid):
    server = authority(prepared[3])
    checked = verify(server, prepared, issue(server, prepared))
    forged = replace(checked, _raw_binding_metadata=invalid)
    with pytest.raises(model.SolarInputEvidenceHold):
        _ = forged.binding_metadata
