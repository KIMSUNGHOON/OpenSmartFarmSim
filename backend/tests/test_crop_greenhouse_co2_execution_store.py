"""Real SCRAM immutable admission, rollback and scoped cancellation only."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest

from app import crop_greenhouse_co2_execution as model
from test_crop_greenhouse_co2_server_custody import (
    setup as producer_setup, authoring, profiles, login_database, login_scope,
    settle_owned_database_backends)
import test_crop_greenhouse_co2_server_custody as producer

pytestmark = producer.pytestmark
TABLES = ('jobs','job_events','job_attempts','job_publications','attempt_outcomes')


def save(name,value):
    if 'calls' in value:value={'actual_scram':True,**value}
    root=os.environ.get('OSSF_CO2_ADMISSION_EVIDENCE')
    if root:
        with (Path(root)/(name+'.json')).open('x') as output:
            os.fchmod(output.fileno(),0o400);json.dump(value,output,sort_keys=True,indent=2)
            output.flush();os.fsync(output.fileno())


@pytest.fixture(scope='module',autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas==roles==0;save('database-cleanup',{'schemas':schemas,'roles':roles})


def totals(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(t))).fetchone()['n'] for t in TABLES)


def events(service,job_id):
    with service.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s ORDER BY recorded_at,event_id').format(
            service.jobs._table('job_events')),('tenant-1',job_id)).fetchall()


@pytest.fixture
def setup(producer_setup,monkeypatch):
    server,raw,value=producer_setup;value[4]['scopes'].update({'simulation_create','simulation_execute','cancel'})
    service=model.Co2ExecutionService(server.binding,input_resolver=server.input_resolver)
    with service.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    before=len(os.listdir('/proc/self/fd'));calls=producer.reference.forbid(monkeypatch)
    yield service,server,raw,value,calls
    assert not any(calls.values()) and list(server.directory.iterdir())==[]
    assert len(os.listdir('/proc/self/fd'))==before


def test_same_intent_original_input_conflict_closed_request_and_revision(setup):
    service,server,raw,value,calls=setup
    first=service.submit('tenant-1',raw);job=str(first['job_id']);before=totals(service)
    again=service.submit('tenant-1',raw);assert again==first and totals(service)==before
    with service.jobs.connect() as conn:
        row=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(service.jobs._table('jobs')),('tenant-1',job)).fetchone()
        canonical=service.jobs._verified_input(row);body=json.loads(canonical)
    assert body['input_version']==model.INPUT_VERSION and body['request']==json.loads(raw)
    assert body['input_resolver_version']==server.input_resolver.version
    assert body['farm_binding_sha256']==sha256(model.documents._canonical(body['farm_binding'])).hexdigest()
    changed=deepcopy(json.loads(raw));changed['rights']['declaration_id']='changed-owned-declaration'
    with pytest.raises(model.JobIntentConflict,match='^co2 execution revision conflict$'):
        service.submit('tenant-1',model.documents._canonical(changed))
    bad=deepcopy(json.loads(raw));bad['unknown']=True
    other=deepcopy(json.loads(raw));other['input']['schema_version']='other-crop-input-v1'
    for invalid in (b'{',b' '*(model.MAX_INPUT_BYTES+1),model.documents._canonical(bad),model.documents._canonical(other)):
        with pytest.raises(model.Co2ExecutionHold,match='^co2 execution admission unavailable$'):
            service.submit('tenant-1',invalid)
    assert totals(service)==before
    new=deepcopy(json.loads(raw));new['revision']='r2';second=service.submit('tenant-1',model.documents._canonical(new))
    assert second['job_id']!=first['job_id'] and first['state']==second['state']=='queued'
    save('admission',{'idempotent_original_job_and_input':True,'different_input_same_revision_conflict':True,
        'different_revision_separate_job':True,'closed_requests':4,'actual_scram':True,'calls':calls})


@pytest.mark.parametrize('change',['rights','scope','review','resolver'])
def test_late_change_after_insert_rolls_back_job_input_and_event(setup,monkeypatch,change):
    service,server,raw,value,calls=setup;before=totals(service);observed=[]
    version=service.input_resolver.version;review=value[2][3];previous_review=deepcopy(review)
    original=service.jobs._event
    def event(conn,tenant,job,kind,*args,**kwargs):
        original(conn,tenant,job,kind,*args,**kwargs)
        if kind=='submitted':
            observed.append(str(job))
            if change=='rights':value[-1].allowed=False
            elif change=='scope':value[4]['scopes'].remove('simulation_create')
            elif change=='review':review['status']='revoked'
            else:service.input_resolver.version='changed-resolver-v1'
    try:
        with monkeypatch.context() as patch:
            patch.setattr(service.jobs,'_event',event)
            with pytest.raises((model.Co2ExecutionHold,PermissionError)):
                service.submit('tenant-1',raw)
    finally:
        value[-1].allowed=True;value[4]['scopes'].add('simulation_create')
        review.clear();review.update(previous_review);service.input_resolver.version=version
    assert len(observed)==1 and totals(service)==before and events(service,observed[0])==[]
    save('late-'+change,{'insert_observed':True,'job_input_event_rollback':True,'actual_scram':True,'calls':calls})


def test_current_rights_tenant_and_create_scope_deny_before_insert(setup):
    service,server,raw,value,calls=setup;before=totals(service)
    with pytest.raises(PermissionError):service.submit('foreign-tenant',raw)
    value[4]['scopes'].remove('simulation_create')
    try:
        with pytest.raises(PermissionError):service.submit('tenant-1',raw)
    finally:value[4]['scopes'].add('simulation_create')
    value[-1].allowed=False
    try:
        with pytest.raises((PermissionError,model.Co2ExecutionHold)):service.submit('tenant-1',raw)
    finally:value[-1].allowed=True
    assert totals(service)==before
    save('current-denied',{'denials':3,'no_job_input_event_insert':True,'calls':calls})


@pytest.mark.parametrize('active',[False,True])
def test_current_owner_can_cancel_after_data_rights_withdrawal_without_simulation_scopes(setup,active):
    service,server,raw,value,calls=setup;job=str(service.submit('tenant-1',raw)['job_id'])
    lease=service.jobs.claim(600,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=job) if active else None
    other=service.jobs.submit('tenant-1','simulation',{'input_version':'other-model'},uuid4().hex)
    assert not service.cancel('tenant-1',str(other['job_id'])) and not service.cancel('foreign',job)
    value[4]['scopes'].remove('cancel')
    try:assert not service.cancel('tenant-1',job)
    finally:value[4]['scopes'].add('cancel')
    scopes=set(value[4]['scopes']);value[4]['scopes'].difference_update({'simulation_create','simulation_execute'});value[-1].allowed=False
    try:
        assert service.cancel('tenant-1',job)
        if active:
            assert service.cancel('tenant-1',job)
            assert service.jobs.get_job('tenant-1',job)['cancel_requested']
            assert service.jobs.ack_cancel('tenant-1',job,lease['attempt'],lease['lease_token'])
        assert not service.cancel('tenant-1',job)
    finally:value[4]['scopes'].update(scopes);value[-1].allowed=True
    kinds=[r['kind'] for r in events(service,job)]
    assert kinds.count('canceled')==1 and kinds.count('cancel_requested')==int(active)
    assert service.jobs.get_job('tenant-1',job)['state']=='canceled'
    with service.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s').format(
            service.jobs._table('job_publications')),('tenant-1',job)).fetchone()['n']==0
    save('cancel-'+str(active),{'claimed':active,'revoked_rights_cancel_without_simulation_scopes':True,
        'different_model_tenant_scope_and_terminal_denied':True,'job_store_ack_only_no_CO2_worker':active,'calls':calls})


@pytest.mark.parametrize('active',[False,True])
def test_cancel_scope_withdrawal_after_event_rolls_back_cancel_state(setup,monkeypatch,active):
    service,server,raw,value,calls=setup;job=str(service.submit('tenant-1',raw)['job_id'])
    if active:service.jobs.claim(600,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=job)
    before=service.jobs.get_job('tenant-1',job);old_events=events(service,job);observed=[];original=service.jobs._event
    def event(conn,tenant,identity,kind,*args,**kwargs):
        original(conn,tenant,identity,kind,*args,**kwargs)
        if kind in ('cancel_requested','canceled'):observed.append(kind);value[4]['scopes'].remove('cancel')
    try:
        with monkeypatch.context() as patch:
            patch.setattr(service.jobs,'_event',event)
            with pytest.raises(PermissionError,match='^co2 cancellation access denied$'):service.cancel('tenant-1',job)
    finally:value[4]['scopes'].add('cancel')
    assert len(observed)==1 and service.jobs.get_job('tenant-1',job)==before and events(service,job)==old_events
    save('cancel-rollback-'+str(active),{'claimed':active,'late_cancel_scope_rollback':True,'calls':calls})


@pytest.mark.parametrize('field,value',[('INPUT_VERSION','other-model'),('INTENT_DOMAIN',b'other-domain'),('CODE_SHA256','0'*64)])
def test_cancel_rejects_changed_own_contract_without_validating_revoked_data(setup,monkeypatch,field,value):
    service,server,raw,original,calls=setup;job=str(service.submit('tenant-1',raw)['job_id']);before=events(service,job)
    with monkeypatch.context() as patch:
        patch.setattr(model,field,value)
        with pytest.raises(model.Co2ExecutionHold,match='^co2 cancellation authority unavailable$'):service.cancel('tenant-1',job)
    assert events(service,job)==before and service.jobs.get_job('tenant-1',job)['state']=='queued'
    save('cancel-contract-'+field,{'changed_contract_denied':True,'calls':calls})
