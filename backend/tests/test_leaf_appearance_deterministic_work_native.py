"""Actual bounded discovery, one leaf calculation and no completed reselection."""
from hashlib import sha256
from threading import Event
from time import perf_counter

import pytest

from app import crop_leaf_appearance_execution as execution
from app.crop_leaf_appearance_execution_query import LeafAppearanceExecutionQuery
from app.deterministic_work import DeterministicWorkerLoop
from app.deterministic_job_discovery import DiscoveryHold
from app import crop_leaf_appearance_signed_producer as producer
from login_database import login_database, login_scope
from test_crop_leaf_appearance_signed_artifact_native import setup, PUBLIC
from test_crop_leaf_appearance_execution_worker_native import execution_setup, submit, retained_rows
from test_crop_morphology_signed_artifact_native import final_cleanup
from leaf_appearance_farm_fresh import snapshot
import test_crop_leaf_appearance_farm_binding_native as leaf_factory
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


def test_actual_discovery_one_leaf_result_and_completed_reselection_zero(execution_setup, login_scope, monkeypatch):
    service, worker, values, _ = execution_setup; values[7]['scopes'].add('simulation_execute')
    before = retained_rows(login_scope[0]); assert before[1] == 25
    parent = snapshot(service.authority.farm_binding.parent_authority.directory)
    unrelated = service.jobs.submit('tenant-1', 'simulation', {'input_version': 'other-leaf-neighbour-v1'}, 'leaf-neighbour')
    previous_leaf = service.jobs.submit('tenant-1', 'simulation',
        {'input_version': 'leaf-population-execution-input-v1'}, 'previous-leaf-family')
    job = submit(execution_setup); stop = Event(); events = []; calls = []
    actual = producer.numerical.produce_leaf_appearance_artifact
    def calculate(*args, **kwargs):
        calls.append(1); return actual(*args, **kwargs)
    monkeypatch.setattr(producer.numerical, 'produce_leaf_appearance_artifact', calculate)
    loop = DeterministicWorkerLoop(worker, input_versions=frozenset({execution.INPUT_VERSION}), poll_seconds=1, page_size=50)
    before_denials = retained_rows(login_scope[0]); denied = []
    with monkeypatch.context() as patch:
        denied_growth = leaf_factory.forbid_growth(patch)
        for scope in ('metadata', 'simulation_execute'):
            values[7]['scopes'].remove(scope)
            with pytest.raises(DiscoveryHold): loop.discovery.page()
            values[7]['scopes'].add(scope); denied.append(scope)
        assert not any(denied_growth.values()) and before_denials == retained_rows(login_scope[0])
    def emit(value): events.append(value); stop.set()
    started = perf_counter(); loop.run(stop, emit=emit); consumer_seconds = perf_counter()-started
    assert len(events) == 1 and events[0]['job_id'] == str(job['job_id']) and events[0]['state'] == 'succeeded' and calls == [1]
    assert service.jobs.get_job('tenant-1', unrelated['job_id']) == unrelated
    assert service.jobs.get_job('tenant-1', previous_leaf['job_id']) == previous_leaf
    monkeypatch.setattr(producer.numerical, 'produce_leaf_appearance_artifact', actual)
    growth = leaf_factory.forbid_growth(monkeypatch)
    response = LeafAppearanceExecutionQuery(service).read('tenant-1', str(job['job_id']), view='replay')
    assert len(response['replay']['frames']) == 12 and response['gates'] == 'not_assessed'
    assert sum(len(frame['leaves']) for frame in response['replay']['frames']) == 47
    hashes = []
    for index, frame in enumerate(response['replay']['frames']):
        raw = (PUBLIC/f'frame-{index}.json').read_bytes()
        assert execution.signed.reader._canonical(frame) == raw; hashes.append(sha256(raw).hexdigest())
    cursor = None; remaining = []; pages = []
    for _ in range(8):
        page = loop.discovery.page(cursor=cursor, limit=50); remaining.extend(page.jobs); pages.append(page.scanned_count)
        if page.next_cursor is None: break
        cursor = page.next_cursor
    else: pytest.fail('bounded fixture discovery did not finish')
    assert not remaining and not any(growth.values()) and calls == [1]
    assert before == retained_rows(login_scope[0], (str(job['job_id']), str(unrelated['job_id']), str(previous_leaf['job_id'])))
    assert parent == snapshot(service.authority.farm_binding.parent_authority.directory)
    factory.save('leaf-automatic-consumer.json', {'explicit_version': execution.INPUT_VERSION,
        'one_actual_numeric_call': len(calls), 'events': events, 'result': response['result'], 'original_12_frame_sha256': hashes,
        'unrelated_queued_job_preserved': True, 'after_completion_selected_jobs': 0, 'page_scanned_counts': pages,
        'previous_leaf_family_queued_preserved': True, 'current_scope_revocations_rejected': denied,
        'denied_discovery_growth_CLI_calls': denied_growth, 'denied_discovery_database_unchanged': True,
        'original_leaf_area_count': 47,
        'query_discovery_growth_CLI_calls': growth, 'consumer_single_seconds': consumer_seconds,
        'retained_25_table_rows_sha256': before[0], 'parent_files_preserved': len(parent),
        'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})
