"""Independent readonly progress readers follow an exited owned producer/worker."""
import ast

import test_crop_greenhouse_co2_execution_fresh as base


OBSERVE_QUERY = r'''
from app import crop_greenhouse_co2_execution_query as query_model
principal['scopes'].difference_update({'simulation_create','simulation_execute','crop_result_write'})
query=query_model.Co2ExecutionQuery(checkpoints,result)
worker_calls=dict(calls);execute_query=psycopg.Connection.execute
query_sql={'write_attempts':0}
def readonly_query(conn,statement,*a,**kw):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  query_sql['write_attempts']+=1;raise AssertionError('progress query attempted SQL mutation')
 return execute_query(conn,statement,*a,**kw)
psycopg.Connection.execute=readonly_query
try:observed_raw=query.read('tenant-1',job_id)
finally:psycopg.Connection.execute=execute_query
observed=json.loads(observed_raw)
assert observed['checkpoint_status']=='current' and observed['job']['state']==events[0]['state']
assert observed['result']['result_id']==record['result_id'] and observed['checkpoint']['provenance_sha256']==progress['provenance_sha256']
assert observed['rights_or_gate_approval'] is False and observed['result']['rights_or_gate_approval'] is False
assert observed['checkpoint']['computed_through_utc']==progress['times']['last_confirmed']['at']
assert calls==worker_calls and query_sql['write_attempts']==0
p['expected_progress_response']=observed
'''


QUERY_READ = r'''
from app import crop_greenhouse_co2_result_store as result_model
from app import crop_greenhouse_co2_execution_worker as worker_model
from app import crop_greenhouse_co2_execution_query as query_model
import os
admission=worker_model.checkpoints.execution.Co2ExecutionService(service,input_resolver=resolver)
checkpoint_store=worker_model.checkpoints.Co2ExecutionCheckpointStore(admission,custody)
result=result_model.Co2ResultStore(custody,integrity_key=b'owned-co2-result-store-key-32-bytes!')
query=query_model.Co2ExecutionQuery(checkpoint_store,result)
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());calls['SQL_write_attempts']=0
execute=psycopg.Connection.execute
def readonly_sql(conn,statement,*a,**kw):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  calls['SQL_write_attempts']+=1;raise AssertionError('fresh progress read attempted SQL mutation')
 return execute(conn,statement,*a,**kw)
psycopg.Connection.execute=readonly_sql
def no_write(name):
 calls[name]=0
 def blocked(*a,**kw):calls[name]+=1;raise AssertionError('fresh progress invoked '+name)
 return blocked
for cls,name in ((worker_model.checkpoints.Co2ExecutionCheckpointStore,'confirm'),
 (custody_model.Co2ServerCustody,'advance'),(result_model.Co2ResultStore,'put'),
 (result_model.Co2ResultStore,'_put_in_transaction')):
 setattr(cls,name,no_write(name))
for name in ('submit','claim','renew','fail','cancel','ack_cancel','_event','_outcome','_insert_publication','_durable_artifact'):
 setattr(type(jobs),name,no_write('jobs.'+name))
assert not {'simulation_create','simulation_execute','crop_result_write'}&principal['scopes']
expected=dict(p['expected_progress_response']);expected.pop('observed_at')
hashes=[];observations=[]
before=counts(service)
for _ in range(2):
 raw=query.read('tenant-1',p['job_id']);value=json.loads(raw)
 assert raw==_canonical(value) and 1<=len(raw)<=query_model.MAX_RESPONSE_BYTES
 observations.append(value.pop('observed_at'));assert value==expected
 hashes.append(sha256(_canonical(value)).hexdigest())
assert hashes[0]==hashes[1] and observations[0]<=observations[1]
review['status']='revoked'
try:query.read('tenant-1',p['job_id'])
except query_model.Co2ExecutionQueryHold:pass
else:raise AssertionError('fresh revoked review returned progress')
assert counts(service)==before and all(v==0 for v in calls.values())
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'PID':os.getpid(),'actual_scram':True,'calls':calls,
 'same_original_DTO_except_observation_time':True,'original_first_confirmation_UTC':True,
 'readonly_without_create_execute_write':True,'review_withdrawal_denied':True,
 'response_without_observation_sha256':hashes,'observation_times':observations}))
'''


def exercise(tmp_path, case):
    previous = base.PREPARE, base.WORKER, base.READ_LINK
    try:
        base.PREPARE=previous[0].replace('script.write_text(t.FRESH_SCRIPT)',
            'script.write_text(t.producer.FRESH_SETUP+'+repr(QUERY_READ)+')')
        marker="summary=result.summary('tenant-1',record['result_id'],p['body']['farm'])"
        assert previous[1].count(marker)==1
        base.WORKER=previous[1].replace(marker,marker+'\n'+OBSERVE_QUERY)
        base.READ_LINK=''
        ast.parse(base.PREPARE);ast.parse(base.WORKER);ast.parse(QUERY_READ)
        base.exercise(tmp_path,case=case)
    finally:
        base.PREPARE,base.WORKER,base.READ_LINK=previous


def test_completed_progress_same_original_DTO_in_fresh_readonly_process(tmp_path):
    exercise(tmp_path,None)


def test_held_progress_same_original_DTO_in_fresh_readonly_process(tmp_path):
    exercise(tmp_path,'hold')
