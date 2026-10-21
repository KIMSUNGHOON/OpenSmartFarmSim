"""Private source bytes bind to an owner/response; fixtures grant no DB access."""
from dataclasses import replace
from hashlib import sha256
import json
from uuid import uuid4

import pytest

from app import crop_greenhouse_co2_prefix as model


def owned_record(*, accepted=True):
    query = object.__new__(model.Co2ExecutionPrefixQuery)
    job_id = str(uuid4())
    program = {'forcing_program': [{'step_index': 0, 'co2': {'basis': 'wet'}}]}
    source = model.storage._canonical(program)
    value = {'prefix_status': 'accepted' if accepted else 'none',
        'manifest': {'program_sha256': sha256(source).hexdigest()} if accepted else None}
    payload = model.storage._canonical(value)
    digest = sha256(payload).hexdigest()
    witness = model._ReadWitness(query, 'tenant-1', job_id,
        ({'tenant_id': 'tenant-1', 'job_id': job_id}, None, None, None, None, None), digest,
        {} if accepted else None, {} if accepted else None, source if accepted else None)
    return query, job_id, model.PrefixRead(payload, digest, witness), program


def test_accepted_source_returns_copy_and_stays_out_of_wire():
    query, job_id, record, program = owned_record()
    result = query._source_program('tenant-1', job_id, record)
    assert result == program
    result['forcing_program'][0]['co2']['basis'] = 'dry'
    assert query._source_program('tenant-1', job_id, record) == program
    assert 'forcing_program' not in record.payload_raw.decode()
    assert 'forcing_program' not in repr(record._witness)


def test_missing_owner_and_changed_response_cannot_supply_source():
    query, job_id, record, _ = owned_record()
    other = object.__new__(model.Co2ExecutionPrefixQuery)
    for owner, candidate in ((other, record), (query, replace(record, _witness=None)),
            (query, replace(record, payload_raw=record.payload_raw+b' '))):
        with pytest.raises(model.Co2PrefixPending):
            owner._source_program('tenant-1', job_id, candidate)


def test_source_bytes_must_be_canonical_and_match_response_manifest():
    query, job_id, record, program = owned_record()
    for source in (None, bytearray(record._witness.program_raw), b'{}',
            record._witness.program_raw+b' ', json.dumps(program).encode()):
        candidate = replace(record, _witness=replace(record._witness, program_raw=source))
        with pytest.raises(model.Co2PrefixHold):
            query._source_program('tenant-1', job_id, candidate)
    assert query._source_program('tenant-1', job_id, record) == program


def test_absent_prefix_has_no_source_fallback():
    query, job_id, record, _ = owned_record(accepted=False)
    assert query._source_program('tenant-1', job_id, record) is None
    candidate = replace(record, _witness=replace(record._witness, program_raw=b'{}'))
    with pytest.raises(model.Co2PrefixHold):
        query._source_program('tenant-1', job_id, candidate)
