"""Actual leaf calculation, parent preservation and atomic completion under SCRAM."""
from hashlib import sha256
import json
from time import perf_counter

from psycopg import sql
import pytest

from app import crop_leaf_appearance_execution as execution
from app import crop_leaf_appearance_signed_producer as producer
from app import crop_leaf_appearance_execution_result as result
from app import crop_leaf_appearance_execution_worker as worker_module
from login_database import login_database, login_scope
from test_crop_leaf_appearance_signed_artifact_native import setup, PUBLIC
from test_crop_leaf_appearance_execution_native import Resolver
from test_crop_morphology_execution_native import counts
from test_crop_morphology_signed_artifact_native import final_cleanup
from leaf_appearance_farm_fresh import snapshot
import test_crop_leaf_appearance_farm_binding_native as leaf_factory
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


@pytest.fixture
def execution_setup(setup):
    authority, values = setup
    resolver = Resolver(values[2])
    service = execution.LeafAppearanceExecutionService(authority, input_resolver=resolver)
    worker = worker_module.LeafAppearanceExecutionWorker(service, tenant_id='tenant-1')
    return service, worker, values, resolver


def submit(value):
    service, _, values, _ = value
    return service.submit('tenant-1', execution.signed.reader._canonical(values[1]))


def events(service, job_id):
    with service.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT kind,reason FROM {} WHERE tenant_id=%s AND job_id=%s ORDER BY event_id')
            .format(service.jobs._table('job_events')), ('tenant-1', job_id)).fetchall()


def retained_rows(base, excluded=()):
    with base.connect() as conn:
        names = [r['table_name'] for r in conn.execute("SELECT table_name FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name", (base.schema,)).fetchall()]
        rows = {}
        for name in names:
            values = [r['row'] for r in conn.execute(sql.SQL('SELECT to_jsonb(x)::text AS row FROM {} x')
                .format(sql.Identifier(base.schema, name))).fetchall()]
            rows[name] = sorted(raw for raw in values if json.loads(raw).get('job_id') not in excluded)
    return sha256(execution.signed.reader._canonical(rows)).hexdigest(), len(names)


def test_actual_one_calculation_original_replay_atomic_completion_and_other_model(execution_setup, login_scope, monkeypatch):
    service, worker, values, _ = execution_setup; body = values[1]
    before = counts(service); original_rows = retained_rows(login_scope[0]); assert original_rows[1] == 25
    parent_before = snapshot(service.authority.farm_binding.parent_authority.directory)
    unrelated = service.jobs.submit('tenant-1', 'simulation', {'input_version': 'other-model-v1'}, 'other-model-leaf-test')
    assert worker.run_once(str(unrelated['job_id'])) is None
    job = submit(execution_setup); actual = producer.numerical.produce_leaf_appearance_artifact; calculated = []
    def calculate(*args, **kwargs):
        calculated.append(1); return actual(*args, **kwargs)
    monkeypatch.setattr(producer.numerical, 'produce_leaf_appearance_artifact', calculate)
    started = perf_counter(); outcome = worker.run_once(str(job['job_id'])); worker_seconds = perf_counter()-started
    assert outcome.state == 'succeeded' and outcome.result_sha256 and calculated == [1]
    assert service.jobs.get_job('tenant-1', unrelated['job_id']) == unrelated
    proof = service.authority.read_replay('tenant-1', outcome.result_sha256)
    assert proof['manifest'] == json.loads((PUBLIC/'root.json').read_bytes())
    assert len(proof['frames']) == 12 and sum(len(f['leaves']) for f in proof['frames']) == 47
    assert proof['parent_job_id'] == body['parent']['job_id'] and proof['parent_result_sha256'] == body['parent']['result_sha256']
    hashes = []
    for index, frame in enumerate(proof['frames']):
        raw = (PUBLIC/f'frame-{index}.json').read_bytes()
        assert execution.signed.reader._canonical(frame) == raw
        hashes.append(sha256(raw).hexdigest())
    raw = service.jobs.read_artifact('tenant-1', job['job_id']); link = result.read_link(raw, {**job, 'attempt_count': 1})
    assert link['result_sha256'] == outcome.result_sha256 and len(raw) < 1024
    pub = service.jobs.get_publication('tenant-1', job['job_id'])
    assert pub['decision_id'] is None and pub['artifact_sha256'] == sha256(raw).hexdigest()
    assert pub['manifest']['worker_code_sha256'] == worker.CODE_SHA256 and pub['manifest']['publication_version'] == result.VERSION
    rows = events(service, job['job_id'])
    started = [r['reason'] for r in rows if r['kind'] == result.START_EVENT_KIND]
    assert len(started) == 1 and started[0]['planned_outputs'] == 12
    assert started[0]['execution_kind'] == 'deterministic_leaf_appearance'
    assert [r['kind'] for r in rows].count(result.RESULT_EVENT_KIND) == 1
    assert [r['kind'] for r in rows].count('lease_renewed') == 1
    with service.jobs.connect() as conn:
        invocations = conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(service.jobs._table('attempt_invocations')), ('tenant-1', job['job_id'])).fetchone()['n']
    assert invocations == 0
    growth = leaf_factory.forbid_growth(monkeypatch)
    assert submit(execution_setup)['job_id'] == job['job_id']
    assert worker.run_once(str(job['job_id'])) is None and calculated == [1] and not any(growth.values())
    after = counts(service)
    assert after == {**before, 'jobs': before['jobs']+2, 'job_events': before['job_events']+7,
        'job_attempts': before['job_attempts']+1, 'attempt_outcomes': before['attempt_outcomes']+1,
        'job_publications': before['job_publications']+1}
    assert original_rows == retained_rows(login_scope[0], (str(job['job_id']), str(unrelated['job_id'])))
    assert parent_before == snapshot(service.authority.farm_binding.parent_authority.directory)
    factory.save('leaf-worker-normal.json', {'result_sha256': outcome.result_sha256, 'root_sha256': proof['numerical_root_sha256'],
        'calculated_at': proof['calculated_at'], 'parent_job_id': proof['parent_job_id'],
        'parent_result_sha256': proof['parent_result_sha256'], 'parent_calculated_at': proof['parent_calculated_at'],
        'original_frame_sha256': hashes, 'one_numeric_call': len(calculated), 'other_queued_model_preserved': True,
        'same_submit_and_completed_retry_growth_calls': growth, 'fake_CLI_invocations': invocations,
        'opaque_artifact_bytes': len(raw), 'planned_outputs_from_original_parent': 12,
        'original_frame_count': 12, 'original_leaf_area_count': 47,
        'counts_before_after': [before, after], 'all_retained_25_table_rows_sha256': original_rows[0],
        'parent_files_preserved': len(parent_before), 'signed_leaf_files': len(snapshot(service.authority.directory)),
        'worker_single_seconds': worker_seconds, 'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})


def test_current_hold_before_calculation_has_no_publication(execution_setup, monkeypatch):
    service, worker, values, _ = execution_setup; job = submit(execution_setup); before = counts(service)
    growth = leaf_factory.forbid_growth(monkeypatch); growth['signed_leaf_producer'] = 0
    def blocked(*args, **kwargs):
        growth['signed_leaf_producer'] += 1; raise AssertionError('hold called producer')
    monkeypatch.setattr(worker_module, 'produce_registered_leaf_appearance', blocked)
    values[8].allowed = False
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'hold' and outcome.result_sha256 is None and not any(growth.values())
    assert service.jobs.get_publication('tenant-1', job['job_id']) is None
    assert service.jobs.read_artifact('tenant-1', job['job_id']) is None
    after = counts(service); assert after['job_publications'] == before['job_publications']
    factory.save('leaf-worker-current-hold.json', {'state': outcome.state, 'growth_producer_CLI_calls': growth,
        'no_publication_or_result_reference': True, 'counts_before_after': [before, after]})


@pytest.mark.parametrize('fence', ['cancel', 'late_leaf_rights', 'late_parent_rights', 'late_leaf_review', 'late_parent_review', 'late_original_program', 'lease_expired'])
def test_late_changes_never_publish_completion(execution_setup, login_scope, monkeypatch, fence):
    service, worker, values, resolver = execution_setup; job = submit(execution_setup)
    before = counts(service); parent_before = snapshot(service.authority.farm_binding.parent_authority.directory)
    retained = retained_rows(login_scope[0], (str(job['job_id']),)); assert retained[1] == 25
    actual = worker_module.produce_registered_leaf_appearance; calculated = []
    def calculate(*args, **kwargs):
        root = actual(*args, **kwargs); calculated.append(root)
        if fence == 'cancel':
            assert service.jobs.cancel('tenant-1', job['job_id'])
        elif fence == 'lease_expired':
            with service.jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' "
                    'WHERE tenant_id=%s AND job_id=%s').format(service.jobs._table('jobs')), ('tenant-1', job['job_id']))
        return root
    monkeypatch.setattr(worker_module, 'produce_registered_leaf_appearance', calculate)
    if fence.startswith('late_'):
        insert = service.jobs._insert_publication
        def revoke(*args, **kwargs):
            value = insert(*args, **kwargs)
            if fence == 'late_leaf_rights': values[8].allowed = False
            elif fence == 'late_parent_rights': values[9].allowed = False
            elif fence == 'late_leaf_review': values[5]['status'] = 'revoked'
            elif fence == 'late_parent_review': values[6]['status'] = 'revoked'
            else: resolver.packet['program_raw'] += b' '
            return value
        monkeypatch.setattr(service.jobs, '_insert_publication', revoke)
    outcome = worker.run_once(str(job['job_id']))
    assert len(calculated) == 1 and outcome.result_sha256 is None
    expected = 'canceled' if fence == 'cancel' else 'unclosed' if fence == 'lease_expired' else 'hold'
    assert outcome.state == expected and service.jobs.get_publication('tenant-1', job['job_id']) is None
    after = counts(service); assert after['job_publications'] == before['job_publications']
    kinds = [r['kind'] for r in events(service, job['job_id'])]
    assert 'succeeded' not in kinds and result.RESULT_EVENT_KIND not in kinds
    assert service.jobs.read_artifact('tenant-1', job['job_id']) is None
    assert parent_before == snapshot(service.authority.farm_binding.parent_authority.directory)
    assert retained == retained_rows(login_scope[0], (str(job['job_id']),))
    factory.save('leaf-worker-'+fence+'.json', {'state': outcome.state,
        'all_retained_25_table_rows_sha256': retained[0],
        'fence_timing': 'after_publication_INSERT_before_commit' if fence.startswith('late_') else 'after_private_signed_calculation',
        'signed_private_files': len(snapshot(service.authority.directory)), 'one_private_calculated_artifact': True,
        'no_publication_or_success_events_or_query_reference': True, 'counts_before_after': [before, after],
        'events': kinds, 'parent_files_preserved': len(parent_before)})
