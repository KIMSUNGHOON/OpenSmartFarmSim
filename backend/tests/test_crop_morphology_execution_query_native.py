"""Stored published job reads preserve original frames and reject current changes."""
from hashlib import sha256
import ctypes
import gc
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from app import crop_morphology_execution_query as query
from app import crop_morphology_execution as execution
from login_database import login_database, login_scope
from test_crop_morphology_signed_artifact_native import setup, PUBLIC, schema_hash
from test_crop_morphology_execution_native import final_cleanup
from test_crop_morphology_execution_worker_native import execution_setup, submit
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


def test_queued_completed_manifest_all_original_frames_zero_calculation_or_write(execution_setup, login_scope, monkeypatch):
    service, worker, *_ = execution_setup; reader = query.MorphologyExecutionQuery(service); job = submit(execution_setup)
    queued = reader.read('tenant-1', str(job['job_id']))
    assert queued['job']['state'] == 'queued' and queued['result'] is queued['manifest'] is queued['frame'] is None
    outcome = worker.run_once(str(job['job_id'])); assert outcome.state == 'succeeded'
    growth = factory.forbid_growth(monkeypatch); before = schema_hash(login_scope[0])
    manifest = reader.read('tenant-1', str(job['job_id']), view='manifest')
    assert manifest['result']['result_sha256'] == outcome.result_sha256
    frames = []
    for index in range(12):
        value = reader.read('tenant-1', str(job['job_id']), view='frame', index=index)
        raw = (PUBLIC/f'frame-{index}.json').read_bytes(); frame = value['frame']
        assert execution.signed.reader._canonical(frame['frame']) == raw
        assert frame['frame_sha256'] == sha256(raw).hexdigest()
        assert frame['calculated_at'] == manifest['result']['calculated_at']; frames.append(frame['frame_sha256'])
    started = time.monotonic(); replay = reader.read('tenant-1', str(job['job_id']), view='replay'); replay_seconds = time.monotonic()-started
    assert [sha256(execution.signed.reader._canonical(v)).hexdigest() for v in replay['replay']['frames']] == frames
    assert schema_hash(login_scope[0]) == before and not any(growth.values())
    factory.save('execution-query-normal.json', {'result': manifest['result'], 'original_12_frame_sha256': frames,
        'query_growth_CLI_calls': growth, 'database_sha256_before_after': [before, schema_hash(login_scope[0])],
        'single_replay_seconds': replay_seconds, 'single_replay_bytes': len(execution.signed.reader._canonical(replay))})


def test_current_and_late_changes_no_old_result_fallback(execution_setup, login_scope, monkeypatch):
    service, worker, _, packet, principal, rights, resolver = execution_setup
    reader = query.MorphologyExecutionQuery(service); job = submit(execution_setup)
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    growth = factory.forbid_growth(monkeypatch); before = schema_hash(login_scope[0]); job_id = str(job['job_id'])
    with pytest.raises(PermissionError): reader.read('foreign', job_id)
    rights.allowed = False
    with pytest.raises(query.MorphologyExecutionQueryHold): reader.read('tenant-1', job_id)
    rights.allowed = True; packet['review']['status'] = 'revoked'
    with pytest.raises(query.MorphologyExecutionQueryHold): reader.read('tenant-1', job_id, view='frame', index=0)
    packet['review']['status'] = 'accepted_for_software_validation'; original = resolver.packet['source_raw']
    resolver.packet['source_raw'] += b' '
    with pytest.raises(query.MorphologyExecutionQueryHold): reader.read('tenant-1', job_id)
    resolver.packet['source_raw'] = original; principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError): reader.read('tenant-1', job_id)
    principal['scopes'].add('crop_result_read')
    read_frame = service.authority.read_frame
    def late(*a, **kw):
        value = read_frame(*a, **kw); rights.allowed = False; return value
    with monkeypatch.context() as patch:
        patch.setattr(service.authority, 'read_frame', late)
        with pytest.raises(query.MorphologyExecutionQueryHold): reader.read('tenant-1', job_id, view='frame', index=11)
    rights.allowed = True
    assert reader.read('tenant-1', job_id)['job']['state'] == 'succeeded'
    assert schema_hash(login_scope[0]) == before and not any(growth.values())
    factory.save('execution-query-current.json', {'foreign_rights_review_original_scope_late_rejected': True,
        'restored_original_result': True, 'query_growth_CLI_calls': growth, 'database_sha256_before_after': [before, schema_hash(login_scope[0])]})


def test_replay_late_frame_revocation_rejects_whole_bundle(execution_setup, login_scope, monkeypatch):
    service, worker, _, _, _, rights, _ = execution_setup; reader = query.MorphologyExecutionQuery(service)
    job = submit(execution_setup); assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    growth = factory.forbid_growth(monkeypatch); before = schema_hash(login_scope[0])
    read_frame = execution.signed.reader.read_rational_morphology_frame; seen = []
    def late(*a, **kw):
        value = read_frame(*a, **kw); seen.append(kw['index'])
        if kw['index'] == 11: rights.allowed = False
        return value
    monkeypatch.setattr(execution.signed.reader, 'read_rational_morphology_frame', late)
    with pytest.raises(query.MorphologyExecutionQueryHold): reader.read('tenant-1', str(job['job_id']), view='replay')
    assert seen == list(range(12)) and schema_hash(login_scope[0]) == before and not any(growth.values())
    factory.save('execution-query-replay-late.json', {'late_last_frame_rights_rejected_whole_response': True,
        'query_growth_CLI_calls': growth, 'database_sha256_before_after': [before, schema_hash(login_scope[0])]})


def test_fresh_exec_no_worker_growth_imports_writes_or_cli(execution_setup, login_scope, tmp_path, monkeypatch):
    service, worker, body, packet, principal, _, resolver = execution_setup; job = submit(execution_setup)
    outcome = worker.run_once(str(job['job_id'])); assert outcome.state == 'succeeded'
    authority = service.authority; payload = json.loads((authority.directory/outcome.result_sha256).read_bytes())['payload']
    binding_raw = (authority.directory/payload['binding_sha256']).read_bytes()
    config = factory.fresh_config(authority.farm_binding, principal, body, packet['packet'], packet['review'], binding_raw, tmp_path/'fresh')
    p = json.loads(Path(config).read_bytes())
    p['signed'] = {'directory': str(authority.directory), 'result_sha256': outcome.result_sha256,
        'key_file': factory.private_file(tmp_path/'fresh', 'signed-key.private', authority.integrity_key),
        'issuer_id': authority.issuer_id, 'key_id': authority.key_id,
        'expected_numerical_root_sha256': payload['numerical_root_sha256'], 'expected_calculated_at': payload['calculated_at']}
    p['execution'] = {'job_id': str(job['job_id']), 'resolver_version': resolver.version}
    path = factory.private_file(tmp_path/'fresh', 'execution-configuration.private.json', execution.signed.reader._canonical(p))
    before = schema_hash(login_scope[0]); growth = factory.forbid_growth(monkeypatch)
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    done = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('morphology_execution_fresh.py')), path],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=90,
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])})
    assert done.returncode == 0, done.stderr
    fresh = json.loads(done.stdout)
    assert fresh['new_growth_modules_imported'] == 0 and fresh['job_id'] == str(job['job_id'])
    assert schema_hash(login_scope[0]) == before and not any(growth.values())
    factory.save('execution-query-fresh.json', {'fresh': fresh, 'query_growth_CLI_calls': growth,
        'database_sha256_before_after': [before, schema_hash(login_scope[0])]})


def test_concurrent_queued_cancel_yields_pending_then_current_cancelled_status(execution_setup, monkeypatch):
    service, _, *_ = execution_setup; reader = query.MorphologyExecutionQuery(service); job = submit(execution_setup)
    growth = factory.forbid_growth(monkeypatch); bundle = reader._bundle; reads = []
    def changed(*a, **kw):
        reads.append(1)
        if len(reads) == 2: assert service.jobs.cancel('tenant-1', job['job_id'])
        return bundle(*a, **kw)
    with monkeypatch.context() as patch:
        patch.setattr(reader, '_bundle', changed)
        with pytest.raises(query.MorphologyExecutionQueryPending): reader.read('tenant-1', str(job['job_id']))
    value = reader.read('tenant-1', str(job['job_id']))
    assert value['job']['state'] == 'canceled' and value['result'] is None and not value['cancel_requested']
    assert not any(growth.values())
    factory.save('execution-query-pending-cancel.json', {'actual_independent_cancel_between_reads': True,
        'pending_not_stale_queued': True, 'next_current_state': value['job']['state'], 'query_growth_CLI_calls': growth})
