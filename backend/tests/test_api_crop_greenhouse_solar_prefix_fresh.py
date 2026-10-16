"""Independent current public responses after an actual producer appends new rows."""
import ast

import test_crop_greenhouse_solar_execution_fresh as base


WORKER = r'''
import os
from app import crop_greenhouse_solar_execution_worker as w
from app import crop_greenhouse_solar_execution_query as q
from app import crop_greenhouse_solar_prefix as m
from app import api_crop_greenhouse_solar_prefix as projection
from app.deterministic_job_discovery import DeterministicJobDiscovery
admission=w.checkpoints.execution.SolarExecutionService(service,input_resolver=resolver)
checkpoint_store=w.checkpoints.SolarExecutionCheckpointStore(admission,custody)
result=w.results.SolarResultStore(custody,integrity_key=b'owned-solar-result-store-key-32-bytes!')
prefix=m.SolarExecutionPrefixQuery(q.SolarExecutionQuery(checkpoint_store,result))
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch())
discovery=DeterministicJobDiscovery(jobs,tenant_id='tenant-1',input_versions=frozenset({w.checkpoints.execution.INPUT_VERSION}))
cursor=None;found=[]
while True:
 page=discovery.page(cursor=cursor);found.extend(page.jobs)
 if page.next_cursor is None:break
 cursor=page.next_cursor
assert len(found)==1
job_id=found[0].job_id;lease=jobs.claim(600,tenant_id='tenant-1',allowed_stages=('simulation',),job_id=job_id)
assert lease and lease['attempt']==1
raw=_canonical(p['body']);first_progress=json.loads(custody.advance('tenant-1',raw,budget=2))
first=checkpoint_store.confirm('tenant-1',job_id,attempt=1,lease_token=lease['lease_token'])
pin={k:first['checkpoint'][k] for k in ('publication_sequence','head_sha256','proof_sha256')}
principal['scopes'].difference_update({'simulation_create','simulation_execute','crop_result_write'})
expected={};before_calls=dict(calls);execute=psycopg.Connection.execute;sql_calls={'write_attempts':0}
def readonly_sql(conn,statement,*a,**kw):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  sql_calls['write_attempts']+=1;raise AssertionError('prefix query SQL mutation')
 return execute(conn,statement,*a,**kw)
psycopg.Connection.execute=readonly_sql
try:
 for view in ('summary','samples','events'):
  wire=projection.read_prefix(prefix,'tenant-1',job_id,selector=pin,view=view)
  expected[view]=json.loads(wire)
  assert expected[view]['reference']['checkpoint']['checkpoint_recorded_at']==q._utc(first['recorded_at'])
 assert calls==before_calls and sql_calls['write_attempts']==0
finally:psycopg.Connection.execute=execute
principal['scopes'].update({'simulation_execute','crop_result_write'})
second_progress=json.loads(custody.advance('tenant-1',raw,budget=8))
second=checkpoint_store.confirm('tenant-1',job_id,attempt=1,lease_token=lease['lease_token'])
assert second_progress['steps']>first_progress['steps'] and second['checkpoint']['publication_sequence']==2
assert second_progress['head_sha256']!=first_progress['head_sha256']
assert all(second_progress['counts'][k]>first_progress['counts'][k] for k in ('samples','events'))
principal['scopes'].difference_update({'simulation_create','simulation_execute','crop_result_write'})
with jobs.connect() as conn:
 assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
 assert conn.execute(sql.SQL('SELECT state FROM {} WHERE job_id=%s').format(jobs._table('jobs')),(p['other_job_id'],)).fetchone()['state']=='queued'
p.update(job_id=job_id,selector=pin,expected_original=expected)
packed_value={**p,'principal':{**p['principal'],'scopes':sorted(p['principal']['scopes'])}}
packed=Path(sys.argv[1]).parent/'completed.private.json';packed.write_text(json.dumps(packed_value));packed.chmod(0o600)
print(json.dumps({'PID':os.getpid(),'actual_scram':True,'automatic_discovery':True,'unselected_queued':True,
 'job_id':job_id,'calls':calls,'completed_pack':str(packed),'actual_producer_tail_advance':True,
 'prefix_steps_before_after':[first_progress['steps'],second_progress['steps']],
 'original_and_tail_counts':[first_progress['counts'],second_progress['counts']],
 'first_recorded_at':q._utc(first['recorded_at']),'query_numerical_calls_zero':True,'query_SQL_writes':0,
 'G0_G4':'not_assessed','rights_or_gate_approval':False}))
'''


READ = r'''
import os
from app import crop_greenhouse_solar_result_store as result_model
from app import crop_greenhouse_solar_execution_worker as w
from app import crop_greenhouse_solar_execution_query as q
from app import crop_greenhouse_solar_prefix as m
from app import api_crop_greenhouse_solar_prefix as projection
admission=w.checkpoints.execution.SolarExecutionService(service,input_resolver=resolver)
checkpoints=w.checkpoints.SolarExecutionCheckpointStore(admission,custody)
result=result_model.SolarResultStore(custody,integrity_key=b'owned-solar-result-store-key-32-bytes!')
prefix=m.SolarExecutionPrefixQuery(q.SolarExecutionQuery(checkpoints,result))
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());calls['SQL_write_attempts']=0
execute=psycopg.Connection.execute
def readonly_sql(conn,statement,*a,**kw):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  calls['SQL_write_attempts']+=1;raise AssertionError('fresh prefix SQL mutation')
 return execute(conn,statement,*a,**kw)
psycopg.Connection.execute=readonly_sql
def no_write(name):
 calls[name]=0
 def blocked(*a,**kw):calls[name]+=1;raise AssertionError('fresh prefix invoked '+name)
 return blocked
for cls,name in ((w.checkpoints.SolarExecutionCheckpointStore,'confirm'),(custody_model.SolarServerCustody,'advance'),
 (result_model.SolarResultStore,'put'),(result_model.SolarResultStore,'_put_in_transaction')):
 setattr(cls,name,no_write(name))
for name in ('submit','claim','renew','fail','cancel','ack_cancel','_event','_outcome','_insert_publication','_durable_artifact'):
 setattr(type(jobs),name,no_write('jobs.'+name))
assert not {'simulation_create','simulation_execute','crop_result_write'}&principal['scopes']
before=counts(service);hashes={};sizes={};observations=[]
for view in ('summary','samples','events','summary'):
 wire=projection.read_prefix(prefix,'tenant-1',p['job_id'],selector=p['selector'],view=view)
 value=json.loads(wire);expected=dict(p['expected_original'][view])
 observations.append(value.pop('observed_at'));expected.pop('observed_at')
 assert value==expected
 assert value['rights_or_gate_approval'] is False
 digest=sha256(_canonical(value)).hexdigest()
 if view in hashes:assert digest==hashes[view]
 hashes[view]=digest;sizes[view]=len(wire)
review['status']='revoked'
try:projection.read_prefix(prefix,'tenant-1',p['job_id'],selector=p['selector'],view='samples')
except projection.ProjectionHold:pass
else:raise AssertionError('fresh prefix returned revoked review')
assert counts(service)==before and all(n==0 for n in calls.values())
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'PID':os.getpid(),'actual_scram':True,'calls':calls,'original_record_except_observation_equal':True,
 'original_page_values_UTC_and_first_confirmation':True,'actual_producer_tail_not_mixed_into_old_selector':True,
 'owner_bound_after_projection_checked':True,'review_withdrawal_denied':True,'DB_unchanged':True,
 'readonly_without_create_execute_write':True,'response_without_observation_sha256':hashes,'response_bytes':sizes,'observation_times':observations}))
'''


def test_actual_producer_tail_and_independent_current_public_prefix(tmp_path):
    previous=base.PREPARE,base.WORKER,base.READ_LINK
    try:
        base.PREPARE=previous[0].replace('script.write_text(t.FRESH_SCRIPT)',
            'script.write_text(t.producer.FRESH_SETUP+'+repr(READ)+')')
        base.WORKER=WORKER
        base.READ_LINK=''
        ast.parse(base.PREPARE);ast.parse(WORKER);ast.parse(READ)
        base.exercise(tmp_path)
    finally:base.PREPARE,base.WORKER,base.READ_LINK=previous
