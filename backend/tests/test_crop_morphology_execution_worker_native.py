"""Actual deterministic calculation and atomic job completion, under SCRAM."""
from hashlib import sha256
import json

from psycopg import sql
import pytest

from app import crop_morphology_execution as execution
from app import crop_morphology_signed_producer as producer
from login_database import login_database, login_scope
from test_crop_morphology_signed_artifact_native import setup, PUBLIC
from test_crop_morphology_execution_native import Resolver, counts, final_cleanup
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


@pytest.fixture
def execution_setup(setup):
    from app.crop_morphology_execution_worker import MorphologyExecutionWorker
    authority, body, packet, principal, rights = setup
    principal['scopes'].update({'simulation_create', 'cancel'})
    resolver = Resolver(packet['packet'])
    service = execution.MorphologyExecutionService(authority, input_resolver=resolver)
    worker = MorphologyExecutionWorker(service, tenant_id='tenant-1')
    return service, worker, body, packet, principal, rights, resolver


def submit(value):
    service, _, body, *_ = value
    return service.submit('tenant-1', execution.signed.reader._canonical(body))


def test_actual_producer_one_original_result_atomic_completion_and_unrelated_job(execution_setup, monkeypatch):
    service, worker, body, *_ = execution_setup; before = counts(service)
    unrelated = service.jobs.submit('tenant-1', 'simulation', {'input_version': 'other-model-v1'}, 'other-model-morphology-test')
    assert worker.run_once(str(unrelated['job_id'])) is None
    job = submit(execution_setup); actual = producer.numerical.produce_rational_morphology_artifact; calls = []
    def calculate(*a, **kw):
        calls.append(1); return actual(*a, **kw)
    monkeypatch.setattr(producer.numerical, 'produce_rational_morphology_artifact', calculate)
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'succeeded' and outcome.result_sha256 and calls == [1]
    assert service.jobs.get_job('tenant-1', unrelated['job_id']) == unrelated
    proof = service.authority.read_manifest('tenant-1', outcome.result_sha256)
    assert proof['manifest'] == json.loads((PUBLIC/'root.json').read_bytes())
    raw = service.jobs.read_artifact('tenant-1', job['job_id'])
    assert json.loads(raw)['result_sha256'] == outcome.result_sha256 and len(raw) < 1024
    pub = service.jobs.get_publication('tenant-1', job['job_id'])
    assert pub['decision_id'] is None and pub['artifact_sha256'] == sha256(raw).hexdigest()
    assert pub['manifest']['worker_code_sha256'] == worker.CODE_SHA256
    growth = factory.forbid_growth(monkeypatch)
    assert submit(execution_setup)['job_id'] == job['job_id']
    assert worker.run_once(str(job['job_id'])) is None and calls == [1] and not any(growth.values())
    after = counts(service)
    assert after['job_publications'] == before['job_publications']+1
    assert after['attempt_outcomes'] == before['attempt_outcomes']+1
    assert after['crop_cycle_research_results'] == before['crop_cycle_research_results']
    factory.save('execution-worker-normal.json', {'result_sha256': outcome.result_sha256,
        'numerical_root_sha256': proof['numerical_root_sha256'], 'calculated_at': proof['calculated_at'],
        'one_numeric_call': calls, 'unrelated_queued_job_preserved': True, 'completed_repeat_growth_calls': growth,
        'opaque_artifact_bytes': len(raw), 'counts_before_after': [before, after]})


def test_current_hold_before_calculation_has_no_publication(execution_setup, monkeypatch):
    service, worker, _, _, _, rights, _ = execution_setup; job = submit(execution_setup); before = counts(service)
    growth = factory.forbid_growth(monkeypatch); rights.allowed = False
    outcome = worker.run_once(str(job['job_id']))
    assert outcome.state == 'hold' and outcome.result_sha256 is None and not any(growth.values())
    assert service.jobs.get_publication('tenant-1', job['job_id']) is None
    after = counts(service); assert after['job_publications'] == before['job_publications']
    factory.save('execution-worker-current-hold.json', {'state': outcome.state, 'growth_calls': growth,
        'counts_before_after': [before, after]})


@pytest.mark.parametrize('fence', ['cancel', 'late_rights', 'lease_expired'])
def test_calculation_late_fences_never_publish_a_partial_completion(execution_setup, monkeypatch, fence):
    from app import crop_morphology_execution_worker as worker_module
    service, worker, _, _, _, rights, _ = execution_setup; job = submit(execution_setup)
    before = counts(service); actual = worker_module.produce_registered_morphology; calculated = []
    def calculate(*a, **kw):
        root = actual(*a, **kw); calculated.append(root)
        if fence == 'cancel':
            assert service.jobs.cancel('tenant-1', job['job_id'])
        elif fence == 'lease_expired':
            with service.jobs.connect() as conn:
                conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' "
                    'WHERE tenant_id=%s AND job_id=%s').format(service.jobs._table('jobs')), ('tenant-1', job['job_id']))
        return root
    monkeypatch.setattr(worker_module, 'produce_registered_morphology', calculate)
    if fence == 'late_rights':
        insert = service.jobs._insert_publication
        def revoke(*a, **kw):
            value = insert(*a, **kw); rights.allowed = False; return value
        monkeypatch.setattr(service.jobs, '_insert_publication', revoke)
    outcome = worker.run_once(str(job['job_id']))
    assert len(calculated) == 1 and outcome.result_sha256 is None
    assert outcome.state == {'cancel': 'canceled', 'late_rights': 'hold', 'lease_expired': 'unclosed'}[fence]
    assert service.jobs.get_publication('tenant-1', job['job_id']) is None
    after = counts(service); assert after['job_publications'] == before['job_publications']
    with service.jobs.connect() as conn:
        kinds = [r['kind'] for r in conn.execute(sql.SQL('SELECT kind FROM {} WHERE tenant_id=%s AND job_id=%s')
            .format(service.jobs._table('job_events')), ('tenant-1', job['job_id'])).fetchall()]
    assert 'succeeded' not in kinds and 'morphology_result_registered_v1' not in kinds
    assert service.jobs.read_artifact('tenant-1', job['job_id']) is None
    factory.save('execution-worker-'+fence+'.json', {'state': outcome.state, 'one_private_calculated_artifact': True,
        'no_publication_or_success_events': True, 'counts_before_after': [before, after], 'events': kinds})
