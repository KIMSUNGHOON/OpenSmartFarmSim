"""Current SCRAM job reads, original bytes, late fences and independent read-only replay."""
from copy import deepcopy
import ctypes
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from time import perf_counter

import psycopg
from psycopg import sql
import pytest

from app import crop_leaf_appearance_execution_query as query
from app import crop_leaf_appearance_execution as execution
from login_database import login_database, login_scope
from test_crop_leaf_appearance_signed_artifact_native import setup, PUBLIC
from test_crop_leaf_appearance_execution_worker_native import execution_setup, submit
from test_crop_morphology_signed_artifact_native import schema_hash, final_cleanup
from leaf_appearance_farm_fresh import snapshot
import test_crop_leaf_appearance_farm_binding_native as leaf_factory
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


def readonly(patch):
    growth = leaf_factory.forbid_growth(patch); writes = {}
    for name in ('submit', 'publish', 'record_decision', '_insert_publication', '_event', '_durable_content', '_durable_artifact', 'artifact.put'):
        writes[name] = 0
        def blocked(*args, _name=name, **kwargs):
            writes[_name] += 1; raise AssertionError('query wrote persistent data')
        if name == 'artifact.put': patch.setattr(execution.signed.MorphologyBlobStore, 'put', blocked)
        else: patch.setattr(execution.JobStore, name, blocked)
    sql_writes = []; execute = psycopg.Cursor.execute
    def read(self, statement, *args, **kwargs):
        text = statement if type(statement) is str else statement.as_string(self.connection)
        if re.match(r'^\s*(INSERT|UPDATE|DELETE|MERGE|CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COPY|CALL|DO)\b', text, re.I):
            sql_writes.append(text.split()[0]); raise AssertionError('query persistent SQL write')
        return execute(self, statement, *args, **kwargs)
    patch.setattr(psycopg.Cursor, 'execute', read)
    return growth, writes, sql_writes


@pytest.fixture
def completed(execution_setup):
    service, worker, values, resolver = execution_setup
    job = submit(execution_setup); outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'succeeded'
    return service, query.LeafAppearanceExecutionQuery(service), values, resolver, job, outcome


def test_queued_and_all_completed_views_original_bytes_no_writes(execution_setup, login_scope, monkeypatch):
    service, worker, _, _ = execution_setup; reader = query.LeafAppearanceExecutionQuery(service)
    job = submit(execution_setup); job_id = str(job['job_id']); timings = {}; before_queued = schema_hash(login_scope[0])
    with monkeypatch.context() as patch:
        growth, writes, sql_writes = readonly(patch)
        started = perf_counter(); queued = reader.read('tenant-1', job_id); timings['queued_status'] = perf_counter()-started
        assert queued['job']['state'] == 'queued' and queued['result'] is queued['manifest'] is queued['frame'] is queued['replay'] is None
        assert not any(growth.values()) and not any(writes.values()) and not sql_writes
    assert before_queued == schema_hash(login_scope[0])
    outcome = worker.run_once(job_id); assert outcome.state == 'succeeded'
    before = schema_hash(login_scope[0]); parent = snapshot(service.authority.farm_binding.parent_authority.directory)
    leaf = snapshot(service.authority.directory); growth, writes, sql_writes = readonly(monkeypatch)
    started = perf_counter(); manifest = reader.read('tenant-1', job_id, view='manifest'); timings['manifest'] = perf_counter()-started
    assert manifest['result']['result_sha256'] == outcome.result_sha256
    assert manifest['manifest']['manifest'] == json.loads((PUBLIC/'root.json').read_bytes())
    started = perf_counter(); status = reader.read('tenant-1', job_id); timings['completed_status'] = perf_counter()-started
    assert status['result'] == manifest['result'] and status['manifest'] is status['frame'] is status['replay'] is None
    frames = {}
    for index in (0, 11):
        started = perf_counter(); value = reader.read('tenant-1', job_id, view='frame', index=index)
        timings['frame_'+str(index)] = perf_counter()-started
        raw = (PUBLIC/f'frame-{index}.json').read_bytes(); frame = value['frame']
        assert execution.signed.reader._canonical(frame['frame']) == raw and frame['frame_sha256'] == sha256(raw).hexdigest()
        assert frame['calculated_at'] == manifest['result']['calculated_at']; frames[index] = frame
    started = perf_counter(); replay = reader.read('tenant-1', job_id, view='replay'); timings['replay'] = perf_counter()-started
    assert replay['replay']['manifest'] == manifest['manifest']
    assert len(replay['replay']['frames']) == 12 and sum(len(f['leaves']) for f in replay['replay']['frames']) == 47
    hashes = []
    for index, frame in enumerate(replay['replay']['frames']):
        raw = (PUBLIC/f'frame-{index}.json').read_bytes(); assert execution.signed.reader._canonical(frame) == raw
        hashes.append(sha256(raw).hexdigest())
        if index in frames: assert frame == frames[index]['frame']
    assert schema_hash(login_scope[0]) == before and not any(growth.values()) and not any(writes.values()) and not sql_writes
    assert parent == snapshot(service.authority.farm_binding.parent_authority.directory) and leaf == snapshot(service.authority.directory)
    factory.save('leaf-query-normal.json', {'result': manifest['result'], 'original_12_frame_sha256': hashes,
        'single_query_seconds': timings, 'replay_bytes': len(execution.signed.reader._canonical(replay)),
        'growth_CLI_calls': growth, 'job_artifact_write_calls': writes, 'persistent_SQL_write_calls': sql_writes,
        'database_before_after': [before, schema_hash(login_scope[0])], 'parent_files_preserved': len(parent),
        'leaf_files_preserved': len(leaf), 'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})


def test_current_inputs_and_scope_never_return_old_result(completed, login_scope, monkeypatch):
    service, reader, values, resolver, job, _ = completed; job_id = str(job['job_id'])
    before = schema_hash(login_scope[0]); growth, writes, sql_writes = readonly(monkeypatch)
    with pytest.raises(PermissionError): reader.read('foreign', job_id)
    for item in (values[8], values[9]):
        item.allowed = False
        with pytest.raises(query.LeafAppearanceExecutionQueryHold): reader.read('tenant-1', job_id)
        item.allowed = True
    for item in (values[5], values[6]):
        item['status'] = 'revoked'
        with pytest.raises(query.LeafAppearanceExecutionQueryHold): reader.read('tenant-1', job_id)
        item['status'] = 'accepted_for_software_validation'
    for name in ('program_raw', 'source_raw', 'evidence_raw'):
        original = resolver.packet[name]; resolver.packet[name] += b' '
        with pytest.raises(query.LeafAppearanceExecutionQueryHold): reader.read('tenant-1', job_id)
        resolver.packet[name] = original
    values[7]['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError): reader.read('tenant-1', job_id)
    values[7]['scopes'].add('crop_result_read')
    restored = reader.read('tenant-1', job_id, view='manifest')
    assert restored['job']['state'] == 'succeeded' and restored['result']['parent_job_id'] == values[1]['parent']['job_id']
    assert before == schema_hash(login_scope[0]) and not any(growth.values()) and not any(writes.values()) and not sql_writes
    factory.save('leaf-query-current.json', {'foreign_both_rights_reviews_three_originals_scope_rejected': True,
        'restored_original_result': restored['result'], 'growth_CLI_calls': growth, 'job_artifact_write_calls': writes,
        'persistent_SQL_write_calls': sql_writes, 'database_before_after': [before, schema_hash(login_scope[0])]})


def test_last_frame_and_resolver_late_changes_reject_whole_response(completed, login_scope, monkeypatch):
    service, reader, values, resolver, job, _ = completed; before = schema_hash(login_scope[0])
    growth, writes, sql_writes = readonly(monkeypatch); original_frame = execution.signed.reader.read_leaf_appearance_frame
    cases = []
    for case in ('leaf_rights', 'parent_rights', 'leaf_review', 'parent_review', 'resolver_source'):
        seen = []
        def late(*args, **kwargs):
            value = original_frame(*args, **kwargs); seen.append(kwargs['index'])
            if kwargs['index'] == 11:
                if case == 'leaf_rights': values[8].allowed = False
                elif case == 'parent_rights': values[9].allowed = False
                elif case == 'leaf_review': values[5]['status'] = 'revoked'
                elif case == 'parent_review': values[6]['status'] = 'revoked'
                else: resolver.packet['source_raw'] += b' '
            return value
        with monkeypatch.context() as patch:
            patch.setattr(execution.signed.reader, 'read_leaf_appearance_frame', late)
            with pytest.raises(query.LeafAppearanceExecutionQueryHold): reader.read('tenant-1', str(job['job_id']), view='replay')
        assert seen == list(range(12))
        values[8].allowed = values[9].allowed = True
        values[5]['status'] = values[6]['status'] = 'accepted_for_software_validation'
        resolver.packet = dict(values[2]); cases.append(case)
    assert before == schema_hash(login_scope[0]) and not any(growth.values()) and not any(writes.values()) and not sql_writes
    factory.save('leaf-query-late.json', {'late_after_last_frame_whole_response_rejected': cases,
        'growth_CLI_calls': growth, 'job_artifact_write_calls': writes, 'persistent_SQL_write_calls': sql_writes,
        'database_before_after': [before, schema_hash(login_scope[0])]})


def test_independent_cancel_returns_pending_then_current_canceled(execution_setup, monkeypatch):
    service, _, _, _ = execution_setup; reader = query.LeafAppearanceExecutionQuery(service); job = submit(execution_setup)
    growth = leaf_factory.forbid_growth(monkeypatch); original = reader._bundle; seen = []
    def changed(*args, **kwargs):
        seen.append(1)
        if len(seen) == 2: assert service.jobs.cancel('tenant-1', job['job_id'])
        return original(*args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(reader, '_bundle', changed)
        with pytest.raises(query.LeafAppearanceExecutionQueryPending): reader.read('tenant-1', str(job['job_id']))
    value = reader.read('tenant-1', str(job['job_id']))
    assert value['job']['state'] == 'canceled' and value['result'] is None and not value['cancel_requested'] and not any(growth.values())
    factory.save('leaf-query-pending-cancel.json', {'actual_cancel_on_independent_connection': True,
        'pending_instead_of_stale_queued': True, 'next_current_state': 'canceled', 'growth_CLI_calls': growth})


def test_fresh_current_job_all_modes_no_growth_imports_or_writes(completed, login_scope, tmp_path, monkeypatch):
    service, _, values, resolver, job, outcome = completed
    binding, body, packet, parent_body, parent_packet, review, parent_review, principal, *_ = values
    parent = binding.parent_authority
    payload = json.loads((parent.directory/body['parent']['result_sha256']).read_bytes())['payload']
    parent_binding = (parent.directory/payload['binding_sha256']).read_bytes()
    directory = tmp_path/'fresh'
    config = factory.fresh_config(parent.farm_binding, principal, parent_body, parent_packet, parent_review, parent_binding, directory)
    p = json.loads(Path(config).read_bytes())
    p['signed'] = {'directory': str(parent.directory), 'key_file': factory.private_file(directory, 'parent-key.private', parent.integrity_key),
        'issuer_id': parent.issuer_id, 'key_id': parent.key_id}
    p['execution'] = {'job_id': body['parent']['job_id'], 'resolver_version': binding.parent_query.service.input_resolver.version}
    p['leaf'] = {'key_file': factory.private_file(directory, 'leaf-input-key.private', binding.input_authority.integrity_key),
        'issuer_id': binding.input_authority.issuer_id, 'key_id': binding.input_authority.key_id, 'review': review,
        'packet_files': {k: factory.private_file(directory, 'leaf-'+k+'.private', v) for k, v in packet.items()}}
    leaf_payload = json.loads((service.authority.directory/outcome.result_sha256).read_bytes())['payload']
    p['leaf_signed'] = {'directory': str(service.authority.directory), 'result_sha256': outcome.result_sha256,
        'root_sha256': leaf_payload['numerical_root_sha256'], 'calculated_at': leaf_payload['calculated_at'],
        'parent_result_sha256': body['parent']['result_sha256'],
        'key_file': factory.private_file(directory, 'leaf-result-key.private', service.authority.integrity_key),
        'issuer_id': service.authority.issuer_id, 'key_id': service.authority.key_id}
    p['leaf_execution'] = {'job_id': str(job['job_id']), 'resolver_version': resolver.version}
    path = factory.private_file(directory, 'leaf-query-configuration.private.json', execution.signed.reader._canonical(p))
    before = schema_hash(login_scope[0]); growth = leaf_factory.forbid_growth(monkeypatch)
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    done = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('leaf_appearance_execution_fresh.py')), path],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=210,
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])})
    assert done.returncode == 0, done.stderr
    fresh = json.loads(done.stdout)
    assert fresh['job_id'] == str(job['job_id']) and fresh['growth_import_attempts'] == []
    assert before == schema_hash(login_scope[0]) and not any(growth.values())
    factory.save('leaf-query-fresh.json', {'fresh': fresh, 'growth_CLI_calls': growth,
        'database_before_after': [before, schema_hash(login_scope[0])]})


def test_completion_after_job_statement_stays_one_snapshot_and_returns_pending(execution_setup, monkeypatch):
    service, worker, _, _ = execution_setup; reader = query.LeafAppearanceExecutionQuery(service)
    job = submit(execution_setup); job_id = str(job['job_id']); execute = psycopg.Cursor.execute
    initial = reader._bundle('tenant-1', job_id)
    assert initial[0]['state'] == 'queued' and not any(initial[1:])
    actor = []; statements = []
    def interleave(self, statement, *args, **kwargs):
        text = statement if type(statement) is str else statement.as_string(self.connection)
        result = execute(self, statement, *args, **kwargs)
        params = args[0] if args else kwargs.get('params', ())
        if not actor and text.lstrip().startswith(('SELECT * FROM ', 'SELECT j.*,')) \
                and '"jobs"' in text and any(str(v) == job_id for v in (params or ())):
            actor.append(None); statements.append(text)
            actor[0] = worker.run_once(job_id)
        return result
    caught = None
    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Cursor, 'execute', interleave)
        try: reader.read('tenant-1', job_id)
        except Exception as error: caught = error
    assert len(actor) == 1 and actor[0].state == 'succeeded'
    assert isinstance(caught, query.LeafAppearanceExecutionQueryPending), type(caught).__name__
    assert service.jobs.get_job('tenant-1', job['job_id'])['state'] == 'succeeded'
    factory.save('leaf-query-atomic-snapshot.json', {'worker_completed_after_initial_job_statement': True,
        'independent_worker_state': actor[0].state, 'query_returned_pending': True,
        'single_bundle_statement': 'AS _query_publications' in statements[0],
        'old_queued_new_publication_mixture_not_returned': True})


def test_accepted_publication_claim_cannot_be_updated_and_original_still_reads(completed, login_scope, monkeypatch):
    service, reader, _, _, job, outcome = completed
    base = login_scope[0]; before = schema_hash(base)
    with pytest.raises(psycopg.errors.RaiseException, match='immutable'):
        with base.connect() as conn:
            conn.execute(sql.SQL("UPDATE {} SET manifest=jsonb_set(manifest, '{{gates}}', '\"G1\"'::jsonb) "
                'WHERE tenant_id=%s AND job_id=%s').format(sql.Identifier(base.schema, 'job_publications')),
                ('tenant-1', job['job_id']))
    assert before == schema_hash(base)
    growth, writes, sql_writes = readonly(monkeypatch)
    value = reader.read('tenant-1', str(job['job_id']), view='manifest')
    assert value['result']['result_sha256'] == outcome.result_sha256
    assert value['gates'] == value['manifest']['gates'] == 'not_assessed'
    assert before == schema_hash(base) and not any(growth.values()) and not any(writes.values()) and not sql_writes
    factory.save('leaf-query-immutable-publication.json', {'actual_owner_UPDATE_rejected_by_immutable_trigger': True,
        'original_result_and_unassessed_gates_retained': True, 'growth_CLI_calls': growth,
        'job_artifact_write_calls': writes, 'persistent_SQL_write_calls': sql_writes,
        'database_before_after': [before, schema_hash(base)]})
