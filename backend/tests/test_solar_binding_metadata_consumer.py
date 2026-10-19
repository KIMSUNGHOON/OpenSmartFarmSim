"""Actual registered farm input binding agrees with its original full-record reader."""
from hashlib import sha256
import json
import sys

from app import crop_greenhouse_solar_farm_binding as model
from test_crop_greenhouse_solar_farm_binding import (
    setup, authoring, profiles, login_database, login_scope, cleanup, pytestmark)


def test_actual_binding_metadata_matches_original_consumer_without_full_json_reparse(setup, monkeypatch):
    service, request, packet, receipt, _, _ = setup
    source = request['input']
    checked = service.input_authority.verify(packet[0], source['source_sha256'], receipt,
        expected_context_sha256=source['context_sha256'],
        expected_binding_sha256=source['time_binding_sha256'])
    record = checked.record
    expected = {
        'source_sha256': checked.source_sha256, 'program_id': record['program']['scenario']['input_id'],
        'period': {'start': record['binding']['start_utc'], 'end': record['binding']['end_utc']},
        'context_sha256': record['context_sha256'], 'time_binding_sha256': record['binding_sha256'],
        'evidence_sha256': sha256(receipt).hexdigest(), 'initial_state_sha256': record['initial_state_sha256'],
        'model_identity': record['manifest']['identity'], 'review': json.loads(receipt)['payload']['review'],
        'provenance': record['provenance'],
        'provenance_sha256': sha256(model.documents._canonical(record['provenance'])).hexdigest(),
        'normalization_version': model.evidence.NORMALIZATION_VERSION,
        'qc_version': model.evidence.QC_VERSION, 'input_evidence_version': model.evidence.VERSION,
    }
    original = model.evidence.files.inputs._json
    callers = []

    def decoded(raw):
        frame = sys._getframe(1)
        callers.append((frame.f_globals.get('__name__'), frame.f_code.co_name, len(raw)))
        return original(raw)

    monkeypatch.setattr(model.evidence.files.inputs, '_json', decoded)
    actual = service._input(request, packet[0], receipt)
    assert actual == expected and len(actual) == 14
    assert actual['evidence_sha256'] == sha256(receipt).hexdigest()
    assert not any((module == model.evidence.__name__ and name == 'record')
        or (module == model.__name__ and name == '_input') for module, name, _ in callers)
    assert any(name == 'binding_metadata' for _, name, _ in callers)
