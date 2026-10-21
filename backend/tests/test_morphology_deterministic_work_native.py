"""The existing foreground consumer discovers only the explicit morphology family."""
from threading import Event

import pytest

from app import crop_morphology_execution as execution
from app.crop_morphology_execution_query import MorphologyExecutionQuery
from app.deterministic_work import DeterministicWorkerLoop
from app import crop_morphology_signed_producer as producer
from login_database import login_database, login_scope
from test_crop_morphology_signed_artifact_native import setup
from test_crop_morphology_execution_native import final_cleanup
from test_crop_morphology_execution_worker_native import execution_setup, submit
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


def test_actual_automatic_discovery_calculation_publication_and_original_other_job(execution_setup, monkeypatch):
    service, worker, _, _, principal, *_ = execution_setup; principal['scopes'].add('simulation_execute')
    unrelated = service.jobs.submit('tenant-1', 'simulation', {'input_version':'other-morphology-neighbour-v1'}, 'morphology-neighbour')
    job = submit(execution_setup); stop = Event(); events = []; calls = []
    actual = producer.numerical.produce_rational_morphology_artifact
    def calculate(*a, **kw): calls.append(1); return actual(*a, **kw)
    monkeypatch.setattr(producer.numerical, 'produce_rational_morphology_artifact', calculate)
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({execution.INPUT_VERSION}), poll_seconds=1, page_size=50)
    def emit(value): events.append(value); stop.set()
    loop.run(stop, emit=emit)
    assert len(events) == 1 and events[0]['job_id'] == str(job['job_id']) and events[0]['state'] == 'succeeded' and calls == [1]
    assert service.jobs.get_job('tenant-1', unrelated['job_id']) == unrelated
    growth = factory.forbid_growth(monkeypatch)
    response = MorphologyExecutionQuery(service).read('tenant-1', str(job['job_id']), view='replay')
    assert len(response['replay']['frames']) == 12 and response['gates'] == 'not_assessed'
    cursor = None; remaining = []; pages = []
    for _ in range(8):
        page = loop.discovery.page(cursor=cursor, limit=50); remaining.extend(page.jobs); pages.append(page.scanned_count)
        if page.next_cursor is None: break
        cursor = page.next_cursor
    else: pytest.fail('bounded fixture discovery did not finish')
    assert not remaining and not any(growth.values()) and calls == [1]
    factory.save('morphology-automatic-consumer.json', {'explicit_version': execution.INPUT_VERSION,
        'one_actual_numeric_call': calls, 'events': events, 'result': response['result'], 'original_12_frames': True,
        'unrelated_queued_job_preserved': True, 'after_completion_selected_jobs': 0, 'page_scanned_counts': pages,
        'query_discovery_growth_CLI_calls': growth})
