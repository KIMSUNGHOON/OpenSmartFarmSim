"""Actual SCRAM parent selection/recovery; fake reviewers do not prove G1."""

import json
from hashlib import sha256
from pathlib import Path
import sys
from urllib.parse import urlencode
from uuid import UUID

from psycopg import sql
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api import create_app
from app.api_economic_calculation import ECONOMIC_REQUEST
from app.authored_financial_selection import AuthoredFinancialSelectionService, READ_SCOPES
from app.jobs import canonical_input_bytes
from test_authored_calculation_assessment import (authored_pair, authored_economic, authoring,
    farm_setup, login_database, login_scope, PROFILE, full_job)
from test_farm_replay_scenario import call


pytestmark = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)


@pytest.fixture
def financial(authored_pair):
    assessments, _, intent, principal, economic, _ = authored_pair
    app = create_app(assessments.jobs, assessments.scenario_store.holds, assessments.runs,
        assessments.results, principal_provider=assessments.jobs.principal_provider,
        thermal_scenario_store=assessments.scenario_store,
        farm_scenario_service=assessments.farm_scenario_service,
        authored_run_store=assessments.authored_run_store,
        economic_calculation_service=economic, assessment_service=assessments)
    base = '/v1/jobs/' + intent['run_job_id']
    return AuthoredFinancialSelectionService(economic), app, assessments, intent, principal, base


def test_current_selection_and_paginated_exact_economic_assessment_links(financial):
    service, app, assessments, intent, principal, base = financial
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        assert call(app, path=base+'/authored-economic-input')[0] == 403
        assert call(app, path=base+'/authored-financial-history')[0] == 403
        principal['scopes'].add(scope)
    status, selection = call(app, path=base+'/authored-economic-input')
    assert status == 200 and selection['verification'] == 'requires_admission_recheck'
    selected = selection['calculation_input']
    assert selected['thermal_job_id'] == intent['run_job_id']
    parent = full_job(assessments.jobs, intent['economic_job_id'])
    assert selected == ECONOMIC_REQUEST.validate_python(selected | {'idempotency_key': 'read-parent'}).model_dump(
        mode='json', exclude={'idempotency_key'})
    assert assessments.jobs._verified_input(parent) == canonical_input_bytes(selected)
    assert set(selection) == {'schema_version', 'thermal_run', 'calculation_input', 'verification'}
    assert not any(key in selection for key in ('amounts', 'rights', 'input_records', 'selected_crop'))
    _, initial = call(app, path=base+'/authored-financial-history')
    assert initial['verification'] == 'requires_current_read'
    assert [item['job']['job_id'] for item in initial['items']] == [intent['economic_job_id']]
    extra = [service.economic.submit('tenant-1', ECONOMIC_REQUEST.validate_python(
        selected | {'idempotency_key': 'recover-money-' + str(index)})) for index in range(2)]
    held = assessments.submit('tenant-1', intent['run_job_id'], intent['economic_job_id'], 'recover-assessment')
    expected = [str(held['job_id']), str(extra[1]['job_id']), str(extra[0]['job_id']), intent['economic_job_id']]
    ids = []
    path = base+'/authored-financial-history?limit=1'
    for index in range(4):
        status, page = call(app, path=path)
        assert status == 200 and page['thermal_job_id'] == intent['run_job_id']
        assert page['run_id'] == selection['thermal_run']['run_id'] and len(page['items']) == 1
        item = page['items'][0]
        ids.append(item['job']['job_id'])
        if index == 0:
            assert item['kind'] == 'assessment' and item['job']['state'] == 'queued'
            assert item['economic_job']['job_id'] == intent['economic_job_id']
        else:
            assert item['kind'] == 'economic' and item['economic_job'] is None
        cursor = page['next_cursor']
        if cursor:
            path = base+'/authored-financial-history?'+urlencode({'limit': 1,
                'before_created_at': cursor['created_at'], 'before_job_id': cursor['job_id']})
        else:
            assert index == 3
    assert ids == expected
    with assessments.jobs.connect() as conn:
        count = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            assessments.jobs._table('jobs'))).fetchone()['n']
    assert call(app, path=base+'/authored-economic-input')[1] == selection
    with assessments.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            assessments.jobs._table('jobs'))).fetchone()['n'] == count


def test_foreign_pending_corrupt_and_revoked_reads_refuse_without_projection(financial, login_scope, monkeypatch):
    service, app, assessments, intent, principal, base = financial
    for job_id in (intent['economic_job_id'], '11111111-1111-4111-8111-111111111111'):
        for tail in ('authored-economic-input', 'authored-financial-history'):
            assert call(app, path='/v1/jobs/'+job_id+'/'+tail)[0] == 404
    row = full_job(assessments.jobs, intent['run_job_id'])
    pending = assessments.jobs.submit('tenant-1', 'simulation', json.loads(row['input_bytes']), 'pending-selection')
    assert call(app, path='/v1/jobs/'+str(pending['job_id'])+'/authored-economic-input')[0] == 404
    principal['tenant_id'] = 'other-tenant'
    assert call(app, path=base+'/authored-financial-history')[0] == 404
    principal['tenant_id'] = 'tenant-1'
    missing = create_app(assessments.jobs, assessments.scenario_store.holds, assessments.runs,
        assessments.results, principal_provider=assessments.jobs.principal_provider,
        authored_run_store=assessments.authored_run_store)
    assert call(missing, path=base+'/authored-economic-input')[0] == 503
    for query in ('limit=0', 'limit=51', 'before_created_at=2026-10-01T00:00:00Z',
            'before_job_id='+intent['run_job_id'], 'before_created_at=2026-10-01T00:00:00&before_job_id='+intent['run_job_id']):
        assert call(app, path=base+'/authored-financial-history?'+query)[0] == 422
    job = full_job(assessments.jobs, intent['economic_job_id'])
    owner = login_scope[0]
    table = assessments.jobs._table('jobs')
    def set_input(target, raw):
        with owner.connect() as conn:
            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(table),
                (raw, sha256(raw).hexdigest(), target))
            conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
    try:
        set_input(job['job_id'], canonical_input_bytes(json.loads(job['input_bytes']) | {'scenario_sha256': 'f' * 64}))
        assert call(app, path=base+'/authored-financial-history')[0] == 503
    finally:
        set_input(job['job_id'], job['input_bytes'])
    held = assessments.submit('tenant-1', intent['run_job_id'], intent['economic_job_id'], 'noncanonical-history')
    assessment = full_job(assessments.jobs, held['job_id'])
    try:
        set_input(assessment['job_id'], json.dumps(json.loads(assessment['input_bytes']), indent=2).encode())
        assert call(app, path=base+'/authored-financial-history')[0] == 503
    finally:
        set_input(assessment['job_id'], assessment['input_bytes'])
    assert call(app, path=base+'/authored-financial-history')[0] == 200
    source = service.economic.results._candidates._source._source
    with monkeypatch.context() as patch:
        patch.setattr(source, 'get_input_rights', lambda *_: None)
        for tail in ('authored-economic-input', 'authored-financial-history'):
            status, result = call(app, path=base+'/'+tail)
            assert status == 503 and set(result) == {'error'}
    assert call(app, path=base+'/authored-economic-input')[0] == 200


def test_final_scope_store_and_parent_recheck_refuse_late_changes(financial, monkeypatch):
    service, _, assessments, intent, principal, _ = financial
    original = service._prepare
    store = service.economic.authored_run_store
    for mutation in ('scope', 'store'):
        def changed(*args):
            value = original(*args)
            if mutation == 'scope':
                principal['scopes'].remove('authored_run_read')
            else:
                service.economic.authored_run_store = None
            return value
        try:
            with monkeypatch.context() as patch:
                patch.setattr(service, '_prepare', changed)
                with pytest.raises((PermissionError, RuntimeError)):
                    service.read('tenant-1', UUID(intent['run_job_id']))
        finally:
            principal['scopes'].add('authored_run_read')
            service.economic.authored_run_store = store
    source = service.economic.results._candidates._source._source
    calls = []
    def revoked(*args):
        value = original(*args)
        calls.append(1)
        if len(calls) == 1:
            patch.setattr(source, 'get_input_rights', lambda *_: None)
        return value
    with monkeypatch.context() as patch:
        patch.setattr(service, '_prepare', revoked)
        with pytest.raises(ValueError):
            service.history('tenant-1', UUID(intent['run_job_id']))
    assert len(calls) == 1
