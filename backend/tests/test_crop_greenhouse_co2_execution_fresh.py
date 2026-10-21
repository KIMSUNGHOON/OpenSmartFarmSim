"""Sequential owned processes prove discovery, atomic output and crash recovery."""
import json
import os
from pathlib import Path
import selectors
import shlex
import signal
import socket
import subprocess
import sys
import tempfile
import time

from test_crop_greenhouse_solar_current_fresh import PREPARE as BASE_PREPARE, CLEANUP

ORIGINAL_PREPARE = BASE_PREPARE.replace('crop_greenhouse_solar_result_store', 'crop_greenhouse_co2_result_store')


ADMISSION = '''
from app import crop_greenhouse_co2_execution_worker as worker_model
value=setup[2];value[4]['scopes'].update({'simulation_create','simulation_execute','cancel'})
admission=worker_model.checkpoints.execution.Co2ExecutionService(setup[0].binding,input_resolver=setup[0].input_resolver)
calls=t.producer.measured(patch)
job=admission.submit('tenant-1',setup[1]);assert admission.submit('tenant-1',setup[1])['job_id']==job['job_id']
other=admission.jobs.submit('tenant-1','simulation',{'input_version':'joint-solar-execution-input-v1','synthetic_unrelated':True},'owned-co2-unselected-v1')
assert all(v==0 for v in calls.values())
value[4]['scopes'].remove('simulation_create')
pack=t.producer.fresh_pack(root,value,b'not-yet-created',setup[0])
packed=json.loads(pack.read_bytes());packed.update(phase=config['phase'],other_job_id=str(other['job_id']))
if config['phase']=='producer':packed['job_id']=str(job['job_id'])
pack.write_text(json.dumps(packed))
'''
PREPARE = ORIGINAL_PREPARE.replace('SimpleNamespace(param=None),patch)', "SimpleNamespace(param=config['case']),patch)").replace(
    'pack=t.verify_original_signed_result(setup,root,patch)', ADMISSION
).replace("'PID':os.getpid()", "'PID':os.getpid(),'job_id':str(job['job_id']),'admission_calls':calls")


WORKER = r'''
import os
from threading import Event
from app import crop_greenhouse_co2_execution_worker as w
from app.deterministic_work import DeterministicWorkerLoop
from app.process_stop import process_stop
admission=w.checkpoints.execution.Co2ExecutionService(service,input_resolver=resolver)
checkpoints=w.checkpoints.Co2ExecutionCheckpointStore(admission,custody)
result=w.results.Co2ResultStore(custody,integrity_key=b'owned-co2-result-store-key-32-bytes!')
worker=w.Co2ExecutionWorker(checkpoints,result,tenant_id='tenant-1',chunk_budget=8 if p['phase']=='producer' else 128)
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());adopted=[]
if p['phase']=='producer':
 def before_confirm(self,lease):
  progress=json.loads(custody.inspect('tenant-1',_canonical(p['body'])))
  assert progress['status']=='yielded' and 0<progress['steps']<16
  print(json.dumps({'PID':os.getpid(),'progress':progress,'calls':calls}),flush=True)
  sys.stdin.readline();raise AssertionError('owned process should have been killed')
 w.Co2ExecutionWorker._confirm=before_confirm
 worker.run_once(p['job_id']);raise AssertionError('owned producer unexpectedly returned')
if p['phase']=='resume':
 original=w.checkpoints.Co2ExecutionCheckpointStore.confirm
 def confirm(self,*a,**kw):
  record=original(self,*a,**kw)
  if not adopted:adopted.append({'checkpoint':record['checkpoint'],'calls':dict(calls)})
  return record
 w.checkpoints.Co2ExecutionCheckpointStore.confirm=confirm
else:assert 'job_id' not in p
stop=Event();events=[]
def emit(value):events.append(value);stop.set()
loop=DeterministicWorkerLoop(worker,input_versions=frozenset({w.checkpoints.execution.INPUT_VERSION}))
with process_stop() as stop:loop.run(stop,emit=emit)
assert len(events)==1 and events[0]['state'] in ('succeeded','hold')
job_id=events[0]['job_id'];progress_raw=custody.inspect('tenant-1',_canonical(p['body']));progress=json.loads(progress_raw)
assert progress['rights_or_gate_approval'] is False and progress['G0_G4']=='not_assessed'
if p['phase']=='resume':
 assert events[0]['attempt']==2 and calls['start']==0 and calls['restore']>=1
 assert calls['step']==16-p['prefix_steps'] and all(v==0 for v in adopted[0]['calls'].values())
 assert adopted[0]['checkpoint']['head_sha256']==p['prefix_head_sha256']
else:assert events[0]['attempt']==1 and calls['start']==1 and calls['step']==16
with jobs.connect() as conn:
 registered=conn.execute(sql.SQL('SELECT reason FROM {} WHERE job_id=%s AND kind=%s').format(jobs._table('job_events')),(job_id,w.RESULT_EVENT_KIND)).fetchall()
 assert len(registered)==1
record=result.get('tenant-1',registered[0]['reason']['result_id'],p['body']['farm'])
assert record['progress_raw']==progress_raw
pages={kind:result.page('tenant-1',record['result_id'],p['body']['farm'],kind) for kind in ('samples','events')}
summary=result.summary('tenant-1',record['result_id'],p['body']['farm'])
with jobs.connect() as conn:
 assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
 assert conn.execute(sql.SQL('SELECT state FROM {} WHERE job_id=%s').format(jobs._table('jobs')),(p['other_job_id'],)).fetchone()['state']=='queued'
 links=conn.execute(sql.SQL('SELECT reason FROM {} WHERE job_id=%s AND kind=%s').format(jobs._table('job_events')),(job_id,w.RESULT_EVENT_KIND)).fetchall()
 assert len(links)==1 and links[0]['reason']['provenance_sha256']==progress['provenance_sha256']
 assert links[0]['reason']['rights_or_gate_approval'] is False and links[0]['reason']['result_id']==record['result_id']
 publication=conn.execute(sql.SQL('SELECT manifest FROM {} WHERE job_id=%s').format(jobs._table('job_publications')),(job_id,)).fetchone()
 assert publication['manifest']==links[0]['reason'] if progress['status']=='completed' else publication is None
assert calls['CLI']==0
p.update(job_id=job_id,state=events[0]['state'],result_id=record['result_id'],payload_sha256=record['payload_sha256'],
 recorded_at=record['recorded_at'].isoformat(),expected_progress_sha256=record['progress_sha256'],
 page_hashes={k:sha256(_canonical(v)).hexdigest() for k,v in pages.items()},summary_sha256=sha256(_canonical(summary)).hexdigest())
packed_value={**p,'principal':{**p['principal'],'scopes':sorted(p['principal']['scopes'])}}
packed=Path(sys.argv[1]).parent/'completed.private.json';packed.write_text(json.dumps(packed_value));packed.chmod(0o600)
print(json.dumps({'PID':os.getpid(),'actual_scram':True,'automatic_discovery':True,'unselected_queued':True,
 'job_id':job_id,'event':events[0],'calls':calls,'adopted':adopted,'original_result_progress_equal':True,
 'completed_pack':str(packed),'provenance_sha256':progress['provenance_sha256'],'actual_farm_Runs':0,
 'G0_G4':'not_assessed','rights_or_gate_approval':False}))
'''


READ_LINK = r'''
from app import crop_greenhouse_co2_execution_worker as w
with jobs.connect() as conn:
 job=jobs._locked_job(conn,'tenant-1',p['job_id'])
 assert job['state']==p['state']
 links=conn.execute(sql.SQL('SELECT reason FROM {} WHERE job_id=%s AND kind=%s').format(jobs._table('job_events')),(p['job_id'],w.RESULT_EVENT_KIND)).fetchall()
 assert len(links)==1 and links[0]['reason']['result_id']==record['result_id']
 assert links[0]['reason']['artifact_sha256']==record['payload_sha256']
 assert links[0]['reason']['provenance_sha256']==json.loads(record['progress_raw'])['provenance_sha256']
 assert links[0]['reason']['rights_or_gate_approval'] is False
 publication=conn.execute(sql.SQL('SELECT manifest FROM {} WHERE job_id=%s').format(jobs._table('job_publications')),(p['job_id'],)).fetchone()
 assert publication['manifest']==links[0]['reason'] if p['state']=='succeeded' else publication is None
assert all(v==0 for v in calls.values())
'''


EXPIRE = r'''
import json,sys,psycopg
from pathlib import Path
from psycopg import sql
config=json.loads(Path(sys.argv[1]).read_bytes());prepared=json.loads((Path(config['root'])/'prepared.private.json').read_bytes())
with psycopg.connect(config['database']['admin']) as conn:
 rows=conn.execute('SELECT nspname FROM pg_namespace WHERE nspname LIKE %s',('login_test_%',)).fetchall();assert len(rows)==1
 schema=rows[0][0];job_id=prepared['job_id']
 assert conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(schema,'crop_greenhouse_co2_research_results'))).fetchone()[0]==0
 assert conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE job_id=%s').format(sql.Identifier(schema,'job_publications')),(job_id,)).fetchone()[0]==0
 assert conn.execute(sql.SQL('SELECT count(*) FROM {} WHERE job_id=%s AND kind=%s').format(sql.Identifier(schema,'job_events')),(job_id,'co2_checkpoint_confirmed_v1')).fetchone()[0]==0
 conn.execute(sql.SQL("UPDATE {} SET lease_until=clock_timestamp()-interval '1 second' WHERE job_id=%s").format(sql.Identifier(schema,'jobs')),(job_id,))
print(json.dumps({'unconfirmed_HEAD_result_publication_rows':0,'lease_expired_by_owned_test_control':True}))
'''


def save(name, value):
    destination = os.environ.get('OSSF_SOLAR_EXECUTION_EVIDENCE')
    if destination:
        with (Path(destination)/name).open('x') as output:
            os.fchmod(output.fileno(), 0o400)
            json.dump(value, output, sort_keys=True, indent=2)
            output.flush(); os.fsync(output.fileno())


def exercise(tmp_path, *, case=None, crash=False):
    if not os.environ.get('OSSF_TEST_PG_DSN') or not os.environ.get('OSSF_TEST_PG_BIN'):
        import pytest
        pytest.skip('owned PostgreSQL test configuration is unset')
    assert __debug__
    binary = Path(os.environ['OSSF_TEST_PG_BIN'])
    backend = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(backend), str(backend/'tests'))))
    with tempfile.TemporaryDirectory(prefix='ossf-login-pg-') as directory:
        root = Path(directory); data = root/'data'; sockets = root/'socket'; sockets.mkdir(mode=0o700)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
        subprocess.run([str(binary/'initdb'), '-D', str(data), '-U', 'ossf_login_admin',
            '--auth-local=trust', '--auth-host=scram-sha-256', '--no-locale', '--encoding=UTF8'],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
        options = (f'-h 127.0.0.1 -p {port} -k {shlex.quote(str(sockets))} '
            '-c shared_buffers=1MB -c jit=off -c work_mem=64kB -c max_connections=12 '
            '-c max_worker_processes=0 -c max_parallel_workers=0 -c autovacuum=off')
        subprocess.run([str(binary/'pg_ctl'), '-D', str(data), '-l', str(root/'server.log'),
            '-w', '-t', '10', 'start', '-o', options], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
        config = tmp_path/'cluster.private.json'
        config.write_text(json.dumps({'root':str(tmp_path),'shared_buffers':'1','case':case,
            'phase':'producer' if crash else 'auto','database':{
                'admin':f'host={sockets} port={port} dbname=postgres user=ossf_login_admin',
                'host':'127.0.0.1','port':port,'database':'postgres'}})); config.chmod(0o600)
        child = None; pidfd = None
        try:
            first = subprocess.run([sys.executable,'-B','-c',PREPARE,str(config)],
                env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=300)
            assert first.returncode==0, first.stderr.decode()
            prepared=json.loads((tmp_path/'prepared.private.json').read_bytes())
            assert not Path('/proc',str(prepared['PID'])).exists()
            assert all(v==0 for v in prepared['admission_calls'].values())
            prefix=Path(prepared['script']).read_text().split('\nfrom app import crop_greenhouse_co2_result_store as result_model')[0]
            runner=tmp_path/'worker.private.py';runner.write_text(prefix+WORKER);runner.chmod(0o400)
            if crash:
                child=subprocess.Popen([sys.executable,'-B',str(runner),prepared['pack']],env=env,
                    stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                pidfd=os.pidfd_open(child.pid);deadline=time.monotonic()+180
                with selectors.DefaultSelector() as selector:
                    selector.register(child.stdout,selectors.EVENT_READ)
                    while not selector.select(min(30,max(0,deadline-time.monotonic()))):
                        assert child.poll() is None and time.monotonic()<deadline
                failed=json.loads(child.stdout.readline(131073));assert failed['PID']==child.pid
                signal.pidfd_send_signal(pidfd,signal.SIGKILL);_,stderr=child.communicate(timeout=10)
                assert child.returncode==-9 and not Path('/proc',str(child.pid)).exists(),stderr.decode()
                expired=subprocess.run([sys.executable,'-B','-c',EXPIRE,str(config)],env=env,
                    stdin=subprocess.DEVNULL,capture_output=True,timeout=30)
                assert expired.returncode==0,expired.stderr.decode()
                packed=json.loads(Path(prepared['pack']).read_bytes());packed.update(phase='resume',
                    prefix_steps=failed['progress']['steps'],prefix_head_sha256=failed['progress']['head_sha256'])
                Path(prepared['pack']).write_text(json.dumps(packed))
            second=subprocess.run([sys.executable,'-B',str(runner),prepared['pack']],env=env,
                stdin=subprocess.DEVNULL,capture_output=True,timeout=300)
            assert second.returncode==0,second.stderr.decode()
            done=json.loads(second.stdout);assert done['automatic_discovery'] and done['unselected_queued']
            assert done['job_id']==prepared['job_id'] and not Path('/proc',str(done['PID'])).exists()
            if crash:assert failed['calls']['step']+done['calls']['step']==16
            read_source=Path(prepared['script']).read_text()
            position=read_source.index("review['status']='revoked'")
            reader=tmp_path/'reader.private.py';reader.write_text(read_source[:position]+READ_LINK+read_source[position:]);reader.chmod(0o400)
            third=subprocess.run([sys.executable,'-B',str(reader),done['completed_pack']],env=env,
                stdin=subprocess.DEVNULL,capture_output=True,timeout=300)
            assert third.returncode==0,third.stderr.decode()
            read=json.loads(third.stdout);assert all(v==0 for v in read['calls'].values())
            assert not Path('/proc',str(read['PID'])).exists()
            proof={'admission_calls':prepared['admission_calls'],'worker':done,'fresh_reader':read,
                'same_owned_database_and_original_files':True,'sequential_processes':True}
            if crash:proof.update(killed=failed,actual_kill_exit=-9,no_prefix_reintegration=True,
                before_retry=json.loads(expired.stdout))
            save('fresh-'+('crash' if crash else 'hold' if case else 'normal')+'.json',proof)
            cleanup=subprocess.run([sys.executable,'-B','-c',CLEANUP,str(config)],env=env,
                stdin=subprocess.DEVNULL,capture_output=True,timeout=30)
            assert cleanup.returncode==0,cleanup.stderr.decode()
            save('cleanup-'+('crash' if crash else 'hold' if case else 'normal')+'.json',json.loads(cleanup.stdout))
        finally:
            if child is not None and child.poll() is None:
                signal.pidfd_send_signal(pidfd,signal.SIGKILL);child.communicate(timeout=10)
            if pidfd is not None:os.close(pidfd)
            for passfile in tmp_path.rglob('*.pgpass'):passfile.unlink()
            subprocess.run([str(binary/'pg_ctl'),'-D',str(data),'-m','fast','-w','-t','10','stop'],
                check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=20)


def test_independent_auto_normal_and_fresh_original_result(tmp_path):
    exercise(tmp_path)


def test_independent_auto_hold_and_fresh_original_result(tmp_path):
    exercise(tmp_path,case='hold')


def test_actual_SIGKILL_after_HEAD_and_automatic_fresh_resume(tmp_path):
    exercise(tmp_path,crash=True)
