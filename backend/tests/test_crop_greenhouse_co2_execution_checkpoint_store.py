"""Actual SCRAM confirmation of existing signed files, without another crop step."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import pytest

from app import crop_greenhouse_co2_execution_checkpoint as model
from test_crop_greenhouse_co2_server_custody import (
    setup as producer_setup, authoring, profiles, login_database, login_scope,
    settle_owned_database_backends)
import test_crop_greenhouse_co2_server_custody as producer

pytestmark=producer.pytestmark


def save(name,value):
    if 'calls' in value:value={'actual_scram':True,**value}
    directory=os.environ.get('OSSF_CO2_CHECKPOINT_EVIDENCE')
    if directory:
        with (Path(directory)/(name+'.json')).open('x') as output:
            os.fchmod(output.fileno(),0o400);json.dump(value,output,sort_keys=True,indent=2)
            output.flush();os.fsync(output.fileno())


@pytest.fixture(scope='module',autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas==roles==0;save('database-cleanup',{'schemas':schemas,'roles':roles})


@pytest.fixture
def setup(producer_setup):
    server,raw,value=producer_setup;value[4]['scopes'].update({'simulation_create','simulation_execute','cancel'})
    admission=model.execution.Co2ExecutionService(server.binding,input_resolver=server.input_resolver)
    job=str(admission.submit('tenant-1',raw)['job_id'])
    lease=admission.jobs.claim(600,allowed_stages=('simulation',),tenant_id='tenant-1',job_id=job)
    store=model.Co2ExecutionCheckpointStore(admission,server)
    with store.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    fd=len(os.listdir('/proc/self/fd'))
    yield store,job,lease,raw,value
    assert len(os.listdir('/proc/self/fd'))==fd


def confirm(setup,store=None):
    original,job,lease,_,_=setup
    return (original if store is None else store).confirm('tenant-1',job,attempt=lease['attempt'],lease_token=lease['lease_token'])


def events(store,job):
    with store.jobs.connect() as conn:
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s AND kind=%s ORDER BY recorded_at,event_id').format(
            store.jobs._table('job_events')),('tenant-1',job,model.EVENT_KIND)).fetchall()


def no_result(store,job):
    with store.jobs.connect() as conn:
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s').format(
            store.jobs._table('job_publications')),('tenant-1',job)).fetchone()['n']==0
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {} WHERE tenant_id=%s AND job_id=%s').format(
            store.jobs._table('attempt_outcomes')),('tenant-1',job)).fetchone()['n']==0


def files(server):
    return {str(p.relative_to(server.directory)):sha256(p.read_bytes()).hexdigest() for p in server.directory.rglob('*') if p.is_file()}


@pytest.mark.parametrize('producer_setup,budget,status',[(None,None,'ready'),(None,1,'yielded'),(None,128,'completed'),('hold',128,'hold')],indirect=['producer_setup'])
def test_original_ready_yielded_completed_hold_and_duplicate_first_time(setup,monkeypatch,budget,status):
    store,job,lease,raw,value=setup;server=store.server
    if budget is None:
        create=model.custody.storage.ArtifactWriter._create
        def stop(*args,**kwargs):create(*args,**kwargs);raise RuntimeError('owned ready-state stop')
        with monkeypatch.context() as patch:
            patch.setattr(model.custody.storage.ArtifactWriter,'_create',stop)
            with pytest.raises(model.custody.Co2CustodyHold):server.advance('tenant-1',raw,budget=1)
        progress=json.loads(server.inspect('tenant-1',raw))
    else:progress=json.loads(server.advance('tenant-1',raw,budget=budget))
    assert progress['status']==status;before=files(server)
    with monkeypatch.context() as patch:
        calls=producer.reference.forbid(patch)
        first=confirm(setup);assert first==confirm(setup)
        new=model.Co2ExecutionCheckpointStore(store.admission,server)
        assert first==confirm(setup,new)
        assert store.jobs.renew('tenant-1',job,lease['attempt'],lease['lease_token'],600)
        assert first==confirm(setup,new) and not any(calls.values())
    metadata=first['checkpoint']
    for field in ('head_sha256','proof_sha256','source_sha256','context_sha256','time_binding_sha256',
                  'header_sha256','artifact_sha256','provenance_sha256','status','steps','planned_steps','counts'):
        assert metadata[field]==progress[field]
    expected_time=None if progress['times'] is None else progress['times']['last_confirmed']['at']
    assert metadata['computed_through_utc']==expected_time
    if expected_time is not None:assert expected_time.endswith('.123456Z')
    assert metadata['rights_or_gate_approval'] is False and metadata['G0_G4']=='not_assessed'
    assert len(events(store,job))==1 and files(server)==before;no_result(store,job)
    save('original-'+status,{'status':status,'original_metadata_time_and_file_hashes':True,
        'duplicate_event_and_first_recorded_at':True,'new_object_not_fresh_process':True,
        'fixture_ready_stop_not_SIGKILL':budget is None,'publications':0,'calls':calls})


def test_later_signed_head_extends_one_history_without_modifying_first(setup,monkeypatch):
    store,job,lease,raw,value=setup
    first_progress=json.loads(store.server.advance('tenant-1',raw,budget=1));first=confirm(setup)
    second_progress=json.loads(store.server.advance('tenant-1',raw,budget=1));before=files(store.server)
    with monkeypatch.context() as patch:
        calls=producer.reference.forbid(patch);second=confirm(setup);assert second==confirm(setup)
        assert not any(calls.values())
    assert first['checkpoint']['publication_sequence']==1 and second['checkpoint']['publication_sequence']==2
    assert first['checkpoint']['steps']==first_progress['steps']<second['checkpoint']['steps']==second_progress['steps']
    assert second['checkpoint']['custody_sequence']>first['checkpoint']['custody_sequence']
    assert second['checkpoint']['computed_through_utc']==second_progress['times']['last_confirmed']['at']
    rows=events(store,job);assert len(rows)==2 and model.Co2ExecutionCheckpointStore._record(rows[0],job)==first
    assert files(store.server)==before;no_result(store,job)
    save('history',{'signed_descendant_and_sequence':True,'first_event_time_preserved':True,'calls':calls})


def test_missing_head_cannot_initialize_or_publish_a_calculation(setup,monkeypatch):
    store,job,_,_,_=setup;before=files(store.server)
    with monkeypatch.context() as patch:
        calls=producer.reference.forbid(patch)
        with pytest.raises((model.Co2CheckpointHold,model.custody.Co2CustodyPending)):confirm(setup)
        assert not any(calls.values())
    assert events(store,job)==[] and files(store.server)==before=={};no_result(store,job)
    save('missing-head',{'no_initialization_or_checkpoint':True,'calls':calls})


def test_current_data_rights_execution_scope_and_tenant_are_checked(setup,monkeypatch):
    store,job,lease,raw,value=setup;store.server.advance('tenant-1',raw,budget=1)
    with monkeypatch.context() as patch:
        calls=producer.reference.forbid(patch);value[-1].allowed=False
        try:
            with pytest.raises((model.Co2CheckpointHold,PermissionError)):confirm(setup)
        finally:value[-1].allowed=True
        value[4]['scopes'].remove('simulation_execute')
        try:
            with pytest.raises(PermissionError):confirm(setup)
        finally:value[4]['scopes'].add('simulation_execute')
        with pytest.raises(PermissionError):store.confirm('foreign',job,attempt=lease['attempt'],lease_token=lease['lease_token'])
        assert not any(calls.values())
    assert events(store,job)==[];no_result(store,job)
    save('current-denied',{'denials':3,'no_checkpoint_or_result':True,'calls':calls})


@pytest.mark.parametrize('fault',['provenance','approval'])
def test_actual_owner_metadata_tampering_cannot_authorize_another_checkpoint(setup,monkeypatch,login_database,fault):
    store,job,_,raw,_=setup;store.server.advance('tenant-1',raw,budget=1);first=confirm(setup)
    original=first['checkpoint'];bad=deepcopy(original)
    if fault=='provenance':bad['provenance_sha256']='0'*64
    else:bad['rights_or_gate_approval']=True
    policy=store.jobs.runtime_identity[0]
    def write(value):
        with psycopg.connect(login_database['admin']) as conn:
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('UPDATE {} SET reason=%s WHERE tenant_id=%s AND job_id=%s AND event_id=%s').format(
                store.jobs._table('job_events')),(Jsonb(value),'tenant-1',job,first['event_id']))
    write(bad)
    try:
        with monkeypatch.context() as patch:
            calls=producer.reference.forbid(patch)
            with pytest.raises(model.Co2CheckpointHold):confirm(setup)
            assert not any(calls.values())
    finally:write(original)
    assert len(events(store,job))==1 and confirm(setup)==first;no_result(store,job)
    save('tamper-'+fault,{'actual_owner_metadata_mutations':2,'forgery_denied':True,'original_event_restored':True,'calls':calls})


@pytest.mark.parametrize('change',['cancel','expire','input','scope'])
def test_changes_after_second_current_validation_roll_back_checkpoint(setup,monkeypatch,change):
    store,job,_,raw,value=setup;store.server.advance('tenant-1',raw,budget=1)
    original=model.Co2ExecutionCheckpointStore._current;observed=[];before=files(store.server)
    def current(instance,*args,**kwargs):
        result=original(instance,*args,**kwargs);observed.append(1)
        if len(observed)==2:
            if change=='cancel':assert store.admission.cancel('tenant-1',job)
            elif change=='scope':value[4]['scopes'].remove('simulation_execute')
            else:
                with store.jobs.connect() as conn:
                    if change=='expire':
                        conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE tenant_id=%s AND job_id=%s").format(
                            store.jobs._table('jobs')),('tenant-1',job))
                    else:
                        row=conn.execute(sql.SQL('SELECT input_bytes FROM {} WHERE tenant_id=%s AND job_id=%s').format(
                            store.jobs._table('jobs')),('tenant-1',job)).fetchone()
                        doc=json.loads(bytes(row['input_bytes']));doc['input_resolver_version']+='-changed'
                        new=model.execution.canonical_input_bytes(doc)
                        conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE tenant_id=%s AND job_id=%s').format(
                            store.jobs._table('jobs')),(new,sha256(new).hexdigest(),'tenant-1',job))
        return result
    try:
        with monkeypatch.context() as patch:
            calls=producer.reference.forbid(patch)
            patch.setattr(model.Co2ExecutionCheckpointStore,'_current',current)
            with pytest.raises((model.Co2CheckpointHold,PermissionError)):confirm(setup)
            assert not any(calls.values())
    finally:value[4]['scopes'].add('simulation_execute')
    assert len(observed)==2 and events(store,job)==[] and files(store.server)==before;no_result(store,job)
    save('late-'+change,{'after_second_current_validation':True,'checkpoint_rollback':True,
        'intentional_other_connection_change':change!='scope','calls':calls})
