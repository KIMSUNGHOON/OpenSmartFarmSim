"""Independent lightweight actors and owner-bound post-projection witnesses."""
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import pytest

from test_crop_greenhouse_co2_prefix import (
    setup, producer_setup, progress_setup, worker_setup, authoring, profiles,
    login_database, original_login_scope, login_scope,
    model, reference, read, save, selector, advance, writable)

pytestmark = [reference.reference.pytestmark, pytest.mark.usefixtures('query_cleanup')]


@pytest.fixture(scope='module')
def query_cleanup(login_database):
    yield
    with reference.psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas==roles==0
    save('database-cleanup-concurrent',{'schemas':schemas,'roles':roles})


ACTOR = r'''
import fcntl,json,os,sys,tempfile
from pathlib import Path
from uuid import uuid4
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
p=json.loads(Path(sys.argv[1]).read_bytes())
with open(os.environ['OSSF_OWNED_DATABASE_SAMPLE_LOCK'],'rb') as lock:
 fcntl.flock(lock,fcntl.LOCK_SH)
 conn=psycopg.connect(p['dsn'],row_factory=dict_row)
with conn:
 assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
 table=sql.Identifier(p['schema'],'jobs')
 before=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(table),('tenant-1',p['job_id'])).fetchone()
 if p['action']=='heartbeat':
  updated=conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()+interval '600 seconds', updated_at=clock_timestamp() WHERE tenant_id=%s AND job_id=%s AND state='simulating' AND lease_token=%s RETURNING job_id").format(table),('tenant-1',p['job_id'],before['lease_token'])).fetchone()
  assert updated
 elif p['action']=='cancel':
  updated=conn.execute(sql.SQL("UPDATE {} SET cancel_requested=true,updated_at=clock_timestamp() WHERE tenant_id=%s AND job_id=%s AND state='simulating' RETURNING job_id").format(table),('tenant-1',p['job_id'])).fetchone()
  assert updated
 elif p['action']=='publish-original':
  path=Path(p['head_path']);fd,name=tempfile.mkstemp(prefix='.owned-publish-',dir=path.parent)
  try:
   with os.fdopen(fd,'wb') as f:
    os.fchmod(f.fileno(),p['head_mode']);f.write(p['head_raw'].encode());f.flush();os.fsync(f.fileno())
   os.replace(name,path);directory=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
   try:os.fsync(directory)
   finally:os.close(directory)
  finally:Path(name).unlink(missing_ok=True)
  if p['checkpoint'] is not None:
   conn.execute(sql.SQL('INSERT INTO {} (tenant_id,job_id,event_id,attempt,kind,reason) VALUES (%s,%s,%s,%s,%s,%s)').format(sql.Identifier(p['schema'],'job_events')),('tenant-1',p['job_id'],uuid4(),before['attempt_count'],p['event_kind'],Jsonb(p['checkpoint'])))
 else:raise AssertionError('unknown owned actor')
 after=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND job_id=%s').format(table),('tenant-1',p['job_id'])).fetchone()
 changed=sorted(k for k in before if before[k]!=after[k])
 assert changed==({'heartbeat':['lease_until','updated_at'],'cancel':['cancel_requested','updated_at'],'publish-original':[]}[p['action']])
 if p['action']=='heartbeat':assert all(before[k]<after[k] for k in changed)
print(json.dumps({'actual_scram':True,'action':p['action'],'changed_job_fields':changed,'updated_at':after['updated_at'].isoformat().replace('+00:00','Z'),'independent_PID':os.getpid(),'precomputed_original_HEAD_published':p['action']=='publish-original','original_snapshot_event_inserted':p.get('checkpoint') is not None,'new_numerical_calculation':False}))
'''


@contextmanager
def lightweight_actor(worker, job_id, tmp_path, action, **data):
    with worker.jobs.connect() as conn:
        assert conn.pgconn.used_password
        dsn=conn.info.dsn
    config=tmp_path/('actor-'+uuid4().hex+'.private.json')
    with config.open('x') as f:
        os.fchmod(f.fileno(),0o600)
        json.dump({'dsn':dsn,'schema':worker.jobs.schema,'job_id':job_id,'action':action,**data},f)
    def run():
        child=subprocess.run([sys.executable,'-B','-c',ACTOR,str(config)],stdin=subprocess.DEVNULL,
            capture_output=True,timeout=30)
        assert child.returncode==0, 'owned metadata actor failed'
        result=json.loads(child.stdout);assert not Path('/proc',str(result['independent_PID'])).exists()
        return result
    try:yield run
    finally:config.unlink()


@pytest.mark.parametrize('confirmed',[False,True],ids=['private','confirmed'])
def test_independent_original_HEAD_publication_during_read_preserves_page(setup,tmp_path,monkeypatch,confirmed):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);_,first=advance(worker,job_id,raw,lease,2)
    pin={k:first['checkpoint'][k] for k in ('publication_sequence','head_sha256','proof_sha256')}
    _,artifact,_=reference.reference.producer.locations(worker.server,raw);path=artifact/'HEAD'
    old=path.read_bytes();progress=worker.server.advance('tenant-1',raw,budget=8);new=path.read_bytes();mode=path.stat().st_mode&0o777
    tail=json.loads(progress)
    assert all(tail['counts'][k]>first['checkpoint']['counts'][k] for k in ('samples','events'))
    with worker.server._open('tenant-1',raw,False) as (session,_):
        checkpoint,_=worker.checkpoints._snapshot(session,progress,2,lease['input_sha256'])
    assert old!=new
    try:
        path.chmod(0o600);path.write_bytes(old);path.chmod(mode)
        reference.readonly(value);expected=read(query,job_id,selector=pin,view='samples')
        original=query.query._bundle;observed=[];count=0
        with lightweight_actor(worker,job_id,tmp_path,'publish-original',head_path=str(path),head_raw=new.decode(),head_mode=mode,
                checkpoint=checkpoint if confirmed else None,event_kind=model.checkpoints.EVENT_KIND) as publish:
            def changed(*args):
                nonlocal count
                count+=1
                if count==2:observed.append(publish())
                return original(*args)
            with monkeypatch.context() as patch:
                calls=reference.forbid(patch);patch.setattr(query.query,'_bundle',changed)
                record=query.read('tenant-1',job_id,selector=pin,view='samples')
                query._after_projection('tenant-1',job_id,record)
                actual=json.loads(record.payload_raw)
                assert all(n==0 for n in calls.values())
        expected['observed_at']=actual['observed_at'];assert model.storage._canonical(actual)==model.storage._canonical(expected)
        assert len(observed)==1 and observed[0]['original_snapshot_event_inserted'] is confirmed
        save('concurrent-original-'+str(confirmed),{'actor':observed[0],'same_original_page_binary64_UTC':True,
            'parent_product_query_calls':calls,'actor_publication_is_precomputed_original_not_new_calculation':True,
            'same_selector':pin,'after_projection_witness_checked':True,
            'original_and_tail_counts':[first['checkpoint']['counts'],tail['counts']]})
    finally:path.chmod(0o600);path.write_bytes(new);path.chmod(mode)


@pytest.mark.parametrize('action',['heartbeat','cancel'])
def test_independent_metadata_change_during_read(setup,tmp_path,monkeypatch,action):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,2)
    reference.readonly(value);expected=read(query,job_id);pin=selector(expected)
    original=query.query._bundle;observed=[];count=0
    with lightweight_actor(worker,job_id,tmp_path,action) as change:
        def changed(*args):
            nonlocal count
            count+=1
            if count==2:observed.append(change())
            return original(*args)
        with monkeypatch.context() as patch:
            calls=reference.forbid(patch);patch.setattr(query.query,'_bundle',changed)
            if action=='cancel':
                with pytest.raises(model.Co2PrefixPending):query.read('tenant-1',job_id,selector=pin,view='samples')
            else:
                actual=read(query,job_id,selector=pin,view='samples')
                assert actual['selection']==expected['selection'] and actual['job']['updated_at']==observed[0]['updated_at']
                assert datetime.fromisoformat(actual['observed_at'])>=datetime.fromisoformat(actual['job']['updated_at'])
            assert all(n==0 for n in calls.values())
    assert len(observed)==1
    if action=='cancel':assert read(query,job_id)['prefix_status']=='closed'
    save('concurrent-'+action,{'actor':observed[0],'product_query_calls':calls,
        'heartbeat_original_selection_or_cancel_pending':True,'actor_SQL_is_intentional_test_control':True})


def test_owner_bound_witness_and_late_rights_after_read(setup,monkeypatch):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,2)
    reference.readonly(value);before=reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch);record=query.read('tenant-1',job_id)
        query._after_projection('tenant-1',job_id,record)
        forged=model.PrefixRead(record.payload_raw,record.payload_sha256)
        other=model.Co2ExecutionPrefixQuery(query.query)
        for owner,candidate in ((query,forged),(other,record),(query,model.PrefixRead(record.payload_raw+b' ',record.payload_sha256,record._witness))):
            with pytest.raises(model.Co2PrefixPending):owner._after_projection('tenant-1',job_id,candidate)
        value[5].allowed=False
        with pytest.raises(ValueError):query._after_projection('tenant-1',job_id,record)
        value[5].allowed=True
        assert all(n==0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    save('witness',{'owner_payload_hash_and_unforgeable_witness_required':True,'late_rights_after_read_rejected':True,'calls':calls,'DB_unchanged':True})


@pytest.mark.parametrize('fault',['provenance','approval'])
def test_selected_checkpoint_binding_drift_is_rejected(setup,monkeypatch,fault):
    query,worker,job_id,raw,value=setup
    lease=reference.confirm(worker,job_id);advance(worker,job_id,raw,lease,2)
    reference.readonly(value);original=query._chosen;before=reference.persisted_digest(worker.jobs)
    with monkeypatch.context() as patch:
        calls=reference.forbid(patch)
        def altered(*a,**kw):
            row=deepcopy(original(*a,**kw))
            if fault=='provenance':row['reason']['provenance_sha256']='0'*64
            else:row['reason']['rights_or_gate_approval']=True
            return row
        patch.setattr(query,'_chosen',altered)
        with pytest.raises(model.Co2PrefixHold):query.read('tenant-1',job_id)
        assert all(n==0 for n in calls.values())
    assert reference.persisted_digest(worker.jobs)==before
    save('selected-'+fault,{'returned_selected_row_fault_only':True,'fault_rejected':True,'calls':calls,'DB_unchanged':True})
