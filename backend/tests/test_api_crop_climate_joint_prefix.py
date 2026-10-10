"""Original numerical projection fixtures and separate authenticated P1 reads."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

import pytest

from app import api_crop_climate_joint_prefix as model
import test_api_crop_climate_joint_replay as terminal
import test_crop_climate_joint_prefix as prefix
from test_crop_climate_joint_prefix import (
    setup, progress_setup, worker_setup, producer_setup, authoring, farm_setup, profiles,
    login_database, original_login_scope, login_scope, query_cleanup)


def save(name, value):
    root = os.environ.get('OSSF_JOINT_PREFIX_PROJECTION_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


def record(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
    return model.current.PrefixRead(raw, sha256(raw).hexdigest())


def project(value):
    result = model.project_prefix(record(value)); raw = model._public_bytes(result)
    assert model.PrefixReplay.model_validate_json(raw).model_dump(mode='json') == result.model_dump(mode='json')
    assert 0 < len(raw) <= model.MAX_RESPONSE_BYTES
    return json.loads(raw)


@pytest.fixture(scope='module')
def original(tmp_path_factory, profiles):
    saved, result, pages = terminal.owned_result(tmp_path_factory.mktemp('owned-prefix-projection'), profiles)
    packet = json.loads(saved['payload_raw']); p = packet['policies']['server_progress']; cp_store = model.current.checkpoints
    cp = {'version': cp_store.VERSION, 'scope': model.current.custody.SCOPE, 'G0_G4': 'not_assessed',
        'publication_sequence': 1, 'input_sha256': sha256(b'unregistered projection fixture').hexdigest(),
        **{k: p[k] for k in ('head_sha256', 'proof_sha256', 'intent_sha256', 'source_sha256', 'context_sha256',
            'time_binding_sha256', 'header_sha256', 'artifact_sha256', 'custody_code_sha256', 'status', 'steps', 'planned_steps', 'counts')},
        'farm_binding_sha256': p['binding_sha256'], 'execution_code_sha256': cp_store.execution.CODE_SHA256,
        'checkpoint_code_sha256': cp_store.CODE_SHA256, 'custody_sequence': 1,
        'computed_through_utc': result['times']['last_confirmed']['at']}
    cp_store._payload(cp)
    value = {'version': model.current.VERSION, 'scope': model.current.custody.SCOPE, 'claim_scope': model.current.CLAIM_SCOPE,
        'G0_G4': 'not_assessed', 'job': {'job_id': str(uuid4()), 'stage': 'simulation', 'state': 'simulating',
            'attempt_count': 1, 'max_attempts': 3, 'created_at': '2026-10-09T00:00:00Z',
            'updated_at': '2026-10-10T00:00:00Z', 'reason_code': None},
        'cancel_requested': False, 'observed_at': '2026-10-10T01:00:00Z', 'prefix_status': 'accepted',
        'selection': {'checkpoint': cp, 'checkpoint_recorded_at': '2026-10-10T00:00:00Z', 'checkpoint_attempt': 1},
        'binding': packet['binding'], 'manifest': result['manifest'], 'time_binding': result['time_binding'],
        'summary': {'counts': result['counts'], 'last_sample_utc': pages['samples']['records'][-1]['time']['at'],
            'last_event_utc': pages['events']['records'][-1]['time']['at']}, 'page': None}
    public_pages = {k: {'kind': k, 'start': 0, 'limit': 64 if k == 'samples' else 8,
        'total': p['total'], 'next_offset': None, 'records': p['records']} for k, p in pages.items()}
    return value, public_pages


def page_case(original, kind):
    value = deepcopy(original[0]); value.update(summary=None, page=deepcopy(original[1][kind])); return value


def inspect_private(value):
    forbidden = {'tenant_id', 'registration_job_id', 'rights', 'review', 'reviewer_id', 'parameters', 'forcing',
        'scenario', 'origin', 'event', 'payload_raw', 'integrity_signature', 'hmac_sha256', 'input_sha256_private',
        'intent_sha256', 'farm_binding_sha256', 'lease_token', 'dsn'}
    if isinstance(value, dict):
        assert not forbidden.intersection(value)
        for item in value.values(): inspect_private(item)
    elif isinstance(value, list):
        for item in value: inspect_private(item)


def test_original_values_units_and_UTC_whitelist_and_fresh(original, tmp_path, monkeypatch):
    before = deepcopy(original); output = {}; fd = len(os.listdir('/proc/self/fd'))
    with monkeypatch.context() as patch:
        calls = prefix.reference.forbid(patch)
        for kind in ('summary', 'samples', 'events'):
            case = original[0] if kind == 'summary' else page_case(original, kind)
            value = project(case); output[kind] = value
            assert value['reference']['checkpoint']['checkpoint_recorded_at'] == case['selection']['checkpoint_recorded_at']
            assert value['reference']['selector'] == prefix.selector(case)
            if kind == 'summary': assert value['summary'] == case['summary'] and value['page'] is None
            elif kind == 'samples': assert model.current.execution._same(value['page'], case['page'])
            else:
                expected = [model.public._event(row, case['manifest']['identity']) for row in case['page']['records']]
                assert model.current.execution._same(value['page']['records'], expected)
            inspect_private(value)
        assert all(n == 0 for n in calls.values())
    assert original == before and len(os.listdir('/proc/self/fd')) == fd
    pack = tmp_path/'projection.private.json'; pack.write_bytes(model.public.storage._canonical({'original': original, 'output': output})); pack.chmod(0o600)
    script = '''
import json,sys
from pathlib import Path
from pytest import MonkeyPatch
import test_api_crop_climate_joint_prefix as t
p=json.loads(Path(sys.argv[1]).read_bytes())
with MonkeyPatch.context() as patch:
 calls=t.prefix.reference.forbid(patch)
 for kind,expected in p['output'].items():
  case=p['original'][0] if kind=='summary' else t.page_case(p['original'],kind)
  assert t.model.current.execution._same(t.project(case),expected)
 assert all(n==0 for n in calls.values())
print(json.dumps({'same_original_public_responses':True,'authenticated_current_read':False,'calls':calls}))
'''
    try:
        child = subprocess.run([sys.executable, '-B', '-c', script, str(pack)], stdin=subprocess.DEVNULL,
            capture_output=True, timeout=120, env=dict(os.environ, PYTHONPATH=prefix.reference.reference.producer.FRESH_PYTHONPATH))
        assert child.returncode == 0, child.stderr.decode(); fresh = json.loads(child.stdout)
    finally: pack.unlink()
    save('original', {'original_values_units_UTC': True, 'private_fields_absent': True, 'calls': calls,
        'canonical_payload_bytes': {k: len(model.public.storage._canonical(v)) for k, v in output.items()},
        'fresh': fresh, 'FD_unchanged': True, 'authenticated_current_read': False, 'unregistered_projection_fixture': True})


@pytest.mark.parametrize('bad', [True, False, 1, '1.0', None, float('nan'), float('inf'), -float('inf')])
def test_non_binary64_is_rejected(original, monkeypatch, bad):
    calls = prefix.reference.forbid(monkeypatch); case = page_case(original, 'samples')
    case['page']['records'][0]['value']['plant_state']['leaf']['value'] = bad
    with pytest.raises(model.ProjectionHold): project(case)
    assert all(n == 0 for n in calls.values())


@pytest.mark.parametrize('fault', ['extra-envelope', 'scope', 'claim', 'gate', 'extra-quantity', 'unit', 'array', 'negative',
    'UTC', 'elapsed', 'order', 'total', 'start-bool', 'limit-bool', 'next', 'extra-page', 'summary-and-page',
    'binding', 'manifest', 'grid', 'checkpoint-time', 'checkpoint-count', 'attempt', 'job-state', 'cancel',
    'event-input', 'event-code', 'event-state-extra'])
def test_mixed_invalid_projection_is_rejected(original, monkeypatch, fault):
    calls = prefix.reference.forbid(monkeypatch); case = page_case(original, 'samples'); page = case['page']; row = page['records'][0]
    if fault == 'extra-envelope': case['secret'] = 'hidden'
    elif fault == 'scope': case['scope'] = 'approved'
    elif fault == 'claim': case['claim_scope'] = 'crop_prediction'
    elif fault == 'gate': case['G0_G4'] = 'passed'
    elif fault == 'extra-quantity': row['value']['plant_state']['leaf']['secret'] = 'hidden'
    elif fault == 'unit': row['value']['plant_state']['leaf']['unit'] = 'kg'
    elif fault == 'array': row['value']['cohort_state']['fruit_number'].pop()
    elif fault == 'negative': row['value']['plant_state']['leaf']['value'] = -1.0
    elif fault == 'UTC': row['time']['at'] = '2026-10-01T00:00:00.123457Z'
    elif fault == 'elapsed': row['value']['elapsed_seconds'] += .000001
    elif fault == 'order': page['records'].reverse()
    elif fault == 'total': page['total'] += 1
    elif fault == 'start-bool': page['start'] = True
    elif fault == 'limit-bool': page['limit'] = True
    elif fault == 'next': page['next_offset'] = 1
    elif fault == 'extra-page': page['private'] = 'hidden'
    elif fault == 'summary-and-page': case['summary'] = original[0]['summary']
    elif fault == 'binding': case['binding']['request']['study_id'] = 'mixed-study'
    elif fault == 'manifest': case['manifest']['identity']['rhs_code_sha256'] = '0'*64
    elif fault == 'grid': case['time_binding']['step_microseconds'] += 1
    elif fault == 'checkpoint-time': case['selection']['checkpoint']['computed_through_utc'] = '2026-10-01T00:00:00Z'
    elif fault == 'checkpoint-count': case['selection']['checkpoint']['counts']['samples'] = 513
    elif fault == 'attempt': case['selection']['checkpoint_attempt'] = 2
    elif fault == 'job-state': case['job']['state'] = 'succeeded'
    elif fault == 'cancel': case['cancel_requested'] = True
    else:
        case = page_case(original, 'events'); m = case['page']['records'][0]['value']['management']
        if fault == 'event-input': m['event']['secret'] = 'changed'
        elif fault == 'event-code': m['code_sha256'] = '0'*64
        else: m['before']['scenario']['extra'] = 'hidden'
    with pytest.raises(model.ProjectionHold): project(case)
    assert all(n == 0 for n in calls.values())


def test_end_pages_limits_summary_and_byte_revalidation(original, monkeypatch):
    calls = prefix.reference.forbid(monkeypatch)
    for kind in ('samples', 'events'):
        case = page_case(original, kind); page = case['page']; page.update(start=1, limit=1, records=page['records'][1:2], next_offset=2)
        assert project(case)['page']['next_offset'] == 2
        page.update(start=page['total'], records=[], next_offset=None)
        assert project(case)['page']['records'] == []
        for bad in (0, 65 if kind == 'samples' else 9):
            page['limit'] = bad
            with pytest.raises(model.ProjectionHold): project(case)
    for name, bad in [('last_sample_utc', None), ('last_event_utc', '2026-10-01T00:00:00.123457Z')]:
        case = deepcopy(original[0]); case['summary'][name] = bad
        with pytest.raises(model.ProjectionHold): project(case)
    projected = model.project_prefix(record(page_case(original, 'samples')))
    projected.root.page.records.append(projected.root.page.records[0])
    with pytest.raises(model.ProjectionHold): model._public_bytes(projected)
    with pytest.raises(model.ProjectionHold): model.project_prefix(model.current.PrefixRead(b'{}', '0'*64))
    with pytest.raises(model.ProjectionHold): model.project_prefix({})
    assert all(n == 0 for n in calls.values())


def test_closed_discriminated_schema_and_UTF8_cap(original, monkeypatch):
    prefix.reference.forbid(monkeypatch); schema = model.PrefixReplay.model_json_schema()
    assert set(schema['discriminator']['mapping']) == {'none', 'closed', 'accepted'}
    assert all(schema['$defs'][name]['additionalProperties'] is False for name in ('NoPrefix', 'AcceptedPrefix', 'PrefixReference'))
    assert schema['$defs']['JointCohorts']['properties']['fruit_number']['minItems'] == 50
    projected = model.project_prefix(record(original[0])); wire = model._public_bytes(projected).decode()
    with monkeypatch.context() as patch:
        patch.setattr(model.PrefixReplay, 'model_dump_json', lambda *_: wire+' '*(model.MAX_RESPONSE_BYTES-len(wire.encode())))
        assert len(model._public_bytes(projected)) == model.MAX_RESPONSE_BYTES
        patch.setattr(model.PrefixReplay, 'model_dump_json', lambda *_: wire+' '*(model.MAX_RESPONSE_BYTES-len(wire.encode())+1))
        with pytest.raises(model.ProjectionHold): model._public_bytes(projected)
    save('schema', {'discriminators': ['none', 'closed', 'accepted'], 'closed_allowlists': True,
        'array_length': 50, 'actual_serialized_UTF8_cap': model.MAX_RESPONSE_BYTES, 'serialization_fault_injection': True})


@pytest.mark.parametrize('status', ['none', 'closed', 'ready'])
def test_empty_none_closed_ready_without_invented_rows(original, monkeypatch, status):
    calls = prefix.reference.forbid(monkeypatch); case = deepcopy(original[0])
    if status != 'ready':
        case.update(prefix_status=status, **dict.fromkeys(('selection', 'binding', 'manifest', 'time_binding', 'summary', 'page')))
        case['job']['state'] = 'queued' if status == 'none' else 'canceled'
        case['cancel_requested'] = status == 'closed'
        result = project(case); assert result['reference'] is result['summary'] is result['page'] is None
    else:
        cp = case['selection']['checkpoint']; cp.update(status='ready', steps=0, counts={'samples': 0, 'events': 0}, artifact_sha256=None, computed_through_utc=None)
        case['summary'] = {'counts': cp['counts'], 'last_sample_utc': None, 'last_event_utc': None}
        assert project(case)['summary'] == case['summary']
        case.update(summary=None, page={'kind': 'samples', 'start': 0, 'limit': 64, 'total': 0, 'next_offset': None, 'records': []})
        assert project(case)['page']['records'] == []
    assert all(n == 0 for n in calls.values())


@prefix.reference.reference.pytestmark
@pytest.mark.usefixtures('query_cleanup')
class TestAuthenticated:
    def test_running_older_original_pages_current_rights_and_cancel(self, setup, tmp_path, monkeypatch):
        query, worker, job_id, raw, value = setup
        lease = prefix.reference.confirm(worker, job_id); _, accepted = prefix.advance(worker, job_id, raw, lease, 8)
        pin = {k: accepted['checkpoint'][k] for k in model.Selector.model_fields}
        prefix.reference.readonly(value); before = prefix.reference.persisted_digest(worker.jobs)
        with monkeypatch.context() as patch:
            calls = prefix.reference.forbid(patch); outputs = {}; lengths = {}; projection_seconds = []
            for kind in ('summary', 'samples', 'events'):
                original = query.read('tenant-1', job_id, **({} if kind == 'summary' else {'selector': pin, 'view': kind}))
                source = json.loads(original.payload_raw); began = time.monotonic(); out = model.project_prefix(original)
                wire = model._public_bytes(out); projection_seconds.append(time.monotonic()-began)
                result = json.loads(wire); lengths[kind] = len(wire)
                assert result['reference']['selector'] == pin and result['reference']['checkpoint']['checkpoint_recorded_at'] == source['selection']['checkpoint_recorded_at']
                if kind == 'samples': assert model.current.execution._same(result['page'], source['page'])
                if kind == 'events': assert model.current.execution._same(result['page']['records'], [model.public._event(r, source['manifest']['identity']) for r in source['page']['records']])
                inspect_private(result); outputs[kind] = result
            assert all(n == 0 for n in calls.values())
        assert prefix.reference.persisted_digest(worker.jobs) == before
        prefix.writable(value); prefix.advance(worker, job_id, raw, lease, 2); prefix.reference.readonly(value)
        with monkeypatch.context() as patch:
            calls = prefix.reference.forbid(patch); previous = model.project_prefix(query.read('tenant-1', job_id, selector=pin))
            assert previous.root.reference.selector.model_dump() == pin
            value[5].allowed = False
            with pytest.raises(model.current.JointPrefixHold): query.read('tenant-1', job_id)
            value[5].allowed = True
            assert all(n == 0 for n in calls.values())
        pack = prefix.reference.reference.producer.fresh_pack(tmp_path, value, worker.server.inspect('tenant-1', raw), worker.server)
        p = json.loads(pack.read_bytes()); p.update(job_id=job_id, phase='reader', selector=pin, expected=previous.model_dump(mode='json')); pack.write_text(json.dumps(p))
        script = prefix.reference.reference.FRESH_WORKER.split('with MonkeyPatch.context()')[0] + '''
import test_crop_climate_joint_execution_query as q
from app import crop_climate_joint_prefix as reader
from app import api_crop_climate_joint_prefix as projection
prefix=reader.JointExecutionPrefixQuery(q.model.JointExecutionQuery(checkpoint_store,result_store))
before=q.persisted_digest(jobs)
with MonkeyPatch.context() as patch:
 calls=q.forbid(patch);actual=projection.project_prefix(prefix.read('tenant-1',p['job_id'],selector=p['selector'])).model_dump(mode='json')
 expected=p['expected'];actual.pop('observed_at');expected.pop('observed_at')
 assert q.model._same(actual,expected) and all(n==0 for n in calls.values())
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
assert q.persisted_digest(jobs)==before
print(json.dumps({'actual_scram':True,'same_public_response_except_observation':True,'calls':calls,'DB_unchanged':True}))
'''
        try:
            child = subprocess.run([sys.executable, '-B', '-c', script, str(pack)], capture_output=True,
                stdin=subprocess.DEVNULL, timeout=120, env=dict(os.environ, PYTHONPATH=prefix.reference.reference.producer.FRESH_PYTHONPATH))
            assert child.returncode == 0, child.stderr.decode(); fresh = json.loads(child.stdout)
        finally: pack.unlink(); (tmp_path/'proof.private.json').unlink()
        assert worker.jobs.cancel('tenant-1', job_id)
        with monkeypatch.context() as patch:
            calls = prefix.reference.forbid(patch); closed = model.project_prefix(query.read('tenant-1', job_id))
            assert closed.root.prefix_status == 'closed' and closed.root.reference is None and all(n == 0 for n in calls.values())
        with worker.jobs.connect() as conn: assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        save('actual-running', {'actual_scram': True, 'original_values_UTC_selector': True, 'old_accepted_after_new_tail': True,
            'rights_revoked_rejected': True, 'cancel_closes_values': True, 'calls': calls,
            'response_bytes': lengths, 'projection_and_serialization_seconds': projection_seconds, 'fresh': fresh})

    @pytest.mark.parametrize('producer_setup', ['dense'], indirect=True)
    def test_actual_64_plus_one_page_with_original_values(self, setup, monkeypatch):
        query, worker, job_id, raw, value = setup
        c = model.current.custody.continuation; context = value[2][2]._context
        expected = c.advance_chunk(context, c.start(context), 128)
        lease = prefix.reference.confirm(worker, job_id)
        prefix.advance(worker, job_id, raw, lease, 64); prefix.advance(worker, job_id, raw, lease, 1)
        prefix.reference.readonly(value); before = prefix.reference.persisted_digest(worker.jobs)
        with monkeypatch.context() as patch:
            calls = prefix.reference.forbid(patch); summary = model.project_prefix(query.read('tenant-1', job_id))
            pin = summary.root.reference.selector.model_dump(); rows = []; lengths = []
            for start in (0, 64):
                result = model.project_prefix(query.read('tenant-1', job_id, selector=pin, view='samples', start=start))
                page = result.root.page; rows.extend(page.records); lengths.append(len(model._public_bytes(result)))
                assert page.next_offset == (64 if start == 0 else None)
            assert len(rows) == 65 and model.current.execution._same([r.value.model_dump(mode='json') for r in rows], expected['samples'])
            assert [r.time.at for r in rows] == [model.current.custody.clock.at_index(value[2][2], r['step_index']) for r in expected['samples']]
            assert all(n == 0 for n in calls.values())
        assert prefix.reference.persisted_digest(worker.jobs) == before
        save('actual-dense', {'actual_scram': True, 'original_samples': 65, 'page_counts': [64, 1],
            'same_original_values_and_UTC': True, 'response_bytes': lengths, 'calls': calls, 'DB_unchanged': True})
