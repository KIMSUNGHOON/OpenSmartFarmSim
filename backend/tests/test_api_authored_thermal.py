"""Only an owned completed authored Run reaches the bounded HTTP projection."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_authored_thermal import (AUTHORED_READ_SCOPES, project_authored_run,
    read_authored_job_run)
from test_api_job_status import get, UnusedMarketResultStore
from test_api_thermal_run import UnusedMarketHoldStore
from test_farm_authored_simulation_worker import _admit, PROFILE
from login_database import login_database, login_scope


class UnusedThermalRunStore:
    def get_run(self, *_):
        raise AssertionError('authored read crossed fixed-fixture Run store')

    def get_snapshot(self, *_):
        raise AssertionError('authored read crossed fixed-fixture snapshot store')


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_authored_http_job_run_and_series_are_bound_and_bounded(login_scope, tmp_path):
    jobs, _, packet, preparer, store, job, worker = _admit(login_scope, tmp_path)
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    principal = jobs.principal_provider()
    principal['scopes'].update(AUTHORED_READ_SCOPES)
    jobs.principal_provider = lambda: principal
    stored_probe = store.get_run('tenant-a', packet.run_id)
    report_probe = stored_probe['report']
    trace_probe = json.loads(stored_probe['trace_raws'][0])
    assert [(key, trace_probe.get(key), report_probe.get(key)) for key in (
        'tenant_id', 'scenario_id', 'scenario_revision', 'registration_sha256',
        'review_job_id', 'decision_context_id', 'context_sha256',
        'decision_at_utc', 'review_at_utc', 'release_sha256')
        if trace_probe.get(key) != report_probe.get(key)] == []
    assert read_authored_job_run(jobs, store, 'tenant-a', job['job_id'])['run_id'] == packet.run_id
    app = create_app(jobs, UnusedMarketHoldStore(), UnusedThermalRunStore(),
        UnusedMarketResultStore(), principal_provider=jobs.principal_provider,
        authored_run_store=store)
    base = '/v1/authored-runs/' + packet.run_id
    job_path = f"/v1/jobs/{job['job_id']}/authored-run"
    status, discovered = get(app, job_path)
    assert status == 200
    assert discovered['run_id'] == packet.run_id
    assert discovered['claim_scope'] == 'synthetic_thermal_replay_only'
    assert discovered['point_count'] == 120
    assert get(app, base) == (200, discovered)
    status, series = get(app, base + '/series')
    assert status == 200 and len(series['points']) == 120
    first_trace = json.loads(packet.trace_raws[0])
    assert series['points'][0]['at_utc'].replace('+00:00', 'Z') == (
        first_trace['steps'][0]['end_utc'])
    assert series['points'][-1]['at_utc'] == discovered['end_utc']
    assert set(series['points'][0]) == {'at_utc', 'temperature_k',
        'humidity_ratio_kg_v_per_kg_da', 'relative_humidity_fraction',
        'heat_demand_w_th', 'heat_delivered_w_th',
        'delivered_heat_energy_kwh_th'}
    assert not any(key in discovered for key in ('tenant_id', 'raw', 'gate_signature',
        'purchased_energy', 'crop_growth', 'future_margin', 'rank'))
    assert get(app, '/v1/runs/' + packet.run_id)[0] == 422

    stored = store.get_run('tenant-a', packet.run_id)
    corrupted = deepcopy(stored)
    corrupted['trace_raws'] = (stored['trace_raws'][0] + b' ', stored['trace_raws'][1])
    with pytest.raises(ValueError, match='^authored thermal display unavailable$'):
        project_authored_run(corrupted)
    preparer.prepare = lambda *args: None
    assert get(app, base)[0] == 503
    assert get(app, job_path)[0] == 503


@pytest.mark.parametrize('login_scope', PROFILE, indirect=True)
def test_authored_http_owner_scope_and_missing_job(login_scope, tmp_path):
    jobs, _, packet, _, store, job, worker = _admit(login_scope, tmp_path)
    assert worker.run_once(str(job['job_id'])).state == 'succeeded'
    principal = jobs.principal_provider()
    principal['scopes'].update(AUTHORED_READ_SCOPES)
    jobs.principal_provider = lambda: principal
    app = create_app(jobs, UnusedMarketHoldStore(), UnusedThermalRunStore(),
        UnusedMarketResultStore(), principal_provider=jobs.principal_provider,
        authored_run_store=store)
    base = '/v1/authored-runs/' + packet.run_id
    job_path = f"/v1/jobs/{job['job_id']}/authored-run"
    assert get(app, '/v1/authored-runs/authored-thermal-run-v1:' + 'a' * 64)[0] == 404
    assert get(app, '/v1/jobs/00000000-0000-4000-8000-000000000001/authored-run')[0] == 404
    for scope in AUTHORED_READ_SCOPES:
        principal['scopes'].remove(scope)
        assert get(app, base)[0] == 403
        assert get(app, job_path)[0] == 403
        principal['scopes'].add(scope)
    principal['tenant_id'] = 'tenant-b'
    assert get(app, base)[0] == 404
    assert get(app, job_path)[0] == 404
    principal['authenticated'] = False
    assert get(app, base)[0] == 401
    assert get(app, job_path)[0] == 401
    assert get(app, '/v1/authored-runs/invalid')[0] == 422
