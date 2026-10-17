"""Unaccepted guarded experiment; failed resource evidence remains an explicit hold."""
import ast
import http.client as http_client
import json
import os
from pathlib import Path
import shlex
import signal
import socket
import ssl
import subprocess
import sys
import tempfile
import time
from urllib.parse import urlencode

from test_crop_greenhouse_solar_current_fresh import PREPARE as BASE_PREPARE, CLEANUP
import test_crop_greenhouse_solar_execution_runtime_native as assembly


PREPARE = BASE_PREPARE.replace(
    'setup=t.setup.__wrapped__', '''
from copy import deepcopy
inputs=t.producer.reference.inputs
case=deepcopy(inputs.reference.reference.CASES[6])
case.update(step_count=64,output_steps=list(range(0,65,8)))
packet=inputs.packet
patch.setattr(inputs,'packet',lambda directory,profiles,origin=None:packet(directory,profiles,case,origin))
setup=t.setup.__wrapped__''').replace(
    'pack=t.verify_original_signed_result(setup,root,patch)', '''
value=setup[2];value[4]['scopes'].update({'simulation_create','simulation_execute','cancel'})
pack=t.producer.fresh_pack(root,value,b'not-yet-created',setup[0])''')


API = r'''
import contextvars,http.client,ipaddress,os,ssl,threading
from datetime import datetime,timedelta,timezone
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from app import crop_greenhouse_solar_result_store as result_model
from app import crop_greenhouse_solar_current_query as current_model
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from app.http_identity import BearerGrant,BearerRegistry,PrincipalMiddleware,token_digest
result=result_model.SolarResultStore(custody,integrity_key=b'owned-solar-result-store-key-32-bytes!')
query=current_model.SolarCurrentQuery(result)
TOKEN=b'owned-solar-concurrent-native-'+b'c'*40
NOW=datetime(2026,10,17,tzinfo=timezone.utc);clock={'now':NOW}
def inventory():
 found={}
 for path in Path('/proc/self/fd').iterdir():
  try:
   st=path.stat();found[path.name]=(os.readlink(path),st.st_dev,st.st_ino)
  except FileNotFoundError:pass
 return found
key=ec.generate_private_key(ec.SECP256R1())
subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'owned-solar-concurrent')])
certificate=(x509.CertificateBuilder().subject_name(subject).issuer_name(subject).public_key(key.public_key())
 .serial_number(x509.random_serial_number()).not_valid_before(NOW-timedelta(days=1))
 .not_valid_after(NOW+timedelta(days=365)).add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),False)
 .sign(key,hashes.SHA256()))
root=Path(sys.argv[1]).parent;cert=root/'api.crt';private=root/'api.key'
cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM));cert.chmod(0o600)
private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()));private.chmod(0o600)
initial=inventory()
__ASSEMBLY__
del seed,original_query,sources,runs,holds,view,candidates,registry,owned
import gc,ctypes
gc.collect();ctypes.CDLL(None).malloc_trim(0)
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());calls['SQL_writes_in_GET']=0
readonly=contextvars.ContextVar('owned_solar_readonly',default=False)
execute=psycopg.Connection.execute
def checked_execute(conn,statement,*a,**kw):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if readonly.get() and text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  calls['SQL_writes_in_GET']+=1;raise AssertionError('API GET attempted mutation')
 return execute(conn,statement,*a,**kw)
psycopg.Connection.execute=checked_execute
class ReadFence:
 def __init__(self,app):self.app=app
 async def __call__(self,scope,receive,send):
  token=readonly.set(scope.get('method')=='GET')
  try:await self.app(scope,receive,send)
  finally:readonly.reset(token)
server=runtime.service.server();server.config.app=ReadFence(runtime.service.app)
baseline=inventory();thread=threading.Thread(target=server.run,daemon=True);thread.start()
try:
 deadline=time.monotonic()+15
 while not server.started:
  assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
 port=server.servers[0].sockets[0].getsockname()[1]
ready=root/'api-ready.private.json'
with ready.open('x') as f:os.fchmod(f.fileno(),0o400);json.dump({'port':port,'PID':os.getpid()},f);f.flush();os.fsync(f.fileno())
while not (root/'api-stop').exists():
 assert thread.is_alive();time.sleep(.05)
finally:
 server.should_exit=True;thread.join(20);assert not thread.is_alive()
 mode['preparing']=True
 assert inventory()==baseline and all(v==0 for v in calls.values())
proof=root/'api-proof.private.json'
with proof.open('x') as f:os.fchmod(f.fileno(),0o400);json.dump({'calls':calls,'FD_unchanged':True,'actual_scram':True,'actual_runtime':True},f);f.flush();os.fsync(f.fileno())
'''


WORKER = r'''
import os
from threading import Event
from app import crop_greenhouse_solar_execution_worker as w
from app.deterministic_work import DeterministicWorkerLoop
admission=w.checkpoints.execution.SolarExecutionService(service,input_resolver=resolver)
checkpoints=w.checkpoints.SolarExecutionCheckpointStore(admission,custody)
result=w.results.SolarResultStore(custody,integrity_key=b'owned-solar-result-store-key-32-bytes!')
worker=w.SolarExecutionWorker(checkpoints,result,tenant_id='tenant-1',chunk_budget=1)
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());stop=Event();events=[]
def emit(value):events.append(value);stop.set()
loop=DeterministicWorkerLoop(worker,input_versions=frozenset({w.checkpoints.execution.INPUT_VERSION}))
import gc,ctypes
gc.collect();ctypes.CDLL(None).malloc_trim(0)
loop.run(stop,emit=emit)
assert len(events)==1 and events[0]['state']=='succeeded' and events[0]['attempt']==1
assert calls['step']==64 and calls['start']==1 and calls['CLI']==0
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
root=Path(sys.argv[1]).parent
with (root/'worker-proof.private.json').open('x') as f:
 os.fchmod(f.fileno(),0o400);json.dump({'PID':os.getpid(),'events':events,'calls':calls,'actual_scram':True,'unpaused':True},f);f.flush();os.fsync(f.fileno())
'''


def scripts(prefix):
    original=assembly.native_script()
    start=original.index('from dataclasses import asdict,replace')
    end=original.index('misassemblies=[]',start)
    bootstrap=original[start:end]
    bootstrap=bootstrap.replace('frozenset(READ_SCOPES)',"frozenset((*READ_SCOPES,*WRITE_SCOPES,'simulation_create','cancel'))")
    source=API.replace('__ASSEMBLY__',bootstrap)
    # The server loop belongs to the try block; final shutdown always closes its thread.
    a=source.index("ready=root/'api-ready.private.json'");z=source.index('\nfinally:',a)
    source=source[:a]+'\n'.join(' '+line for line in source[a:z].splitlines())+source[z:]
    for text in (prefix+source,prefix+WORKER):ast.parse(text)
    return prefix+source,prefix+WORKER


def exercise(tmp_path):
    binary=Path(os.environ['OSSF_TEST_PG_BIN']);backend=Path(__file__).resolve().parents[1]/'backend'
    env=dict(os.environ,PYTHONPATH=os.pathsep.join((str(backend),str(backend/'tests'))))
    actors=[];outputs=[];requests=[];observed=[]
    with tempfile.TemporaryDirectory(prefix='ossf-login-pg-') as directory:
        cluster=Path(directory);data=cluster/'data';sockets=cluster/'socket';sockets.mkdir(mode=0o700)
        with socket.socket() as probe:probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
        subprocess.run([str(binary/'initdb'),'-D',str(data),'-U','ossf_login_admin','--auth-local=trust','--auth-host=scram-sha-256','--no-locale','--encoding=UTF8'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=30)
        options=f'-h 127.0.0.1 -p {port} -k {shlex.quote(str(sockets))} -c shared_buffers=1MB -c jit=off -c work_mem=64kB -c max_connections=12 -c max_worker_processes=0 -c max_parallel_workers=0 -c autovacuum=off'
        subprocess.run([str(binary/'pg_ctl'),'-D',str(data),'-l',str(cluster/'server.log'),'-w','-t','10','start','-o',options],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=20)
        config=tmp_path/'cluster.private.json';config.write_text(json.dumps({'root':str(tmp_path),'shared_buffers':'1','database':{'admin':f'host={sockets} port={port} dbname=postgres user=ossf_login_admin','host':'127.0.0.1','port':port,'database':'postgres'}}));config.chmod(0o600)
        try:
            first=subprocess.run([sys.executable,'-B','-c',PREPARE,str(config)],env=env,stdin=subprocess.DEVNULL,capture_output=True,timeout=300)
            assert first.returncode==0,'owned preparation failed'
            prepared=json.loads((tmp_path/'prepared.private.json').read_bytes());pack=Path(prepared['pack']);p=json.loads(pack.read_bytes())
            prefix=Path(prepared['script']).read_text().split('\nfrom app import crop_greenhouse_solar_result_store as result_model')[0]
            prefix=prefix.replace('original(conn)', 'original(conn);__import__("ctypes").CDLL(None).malloc_trim(0)')
            api_prefix='from app.http_identity import current_principal\n'+prefix.replace('provider=lambda:principal',"mode={'preparing':True}\ndef provider():return principal if mode['preparing'] else current_principal()")
            api_source,worker_source=scripts(api_prefix)
            worker_source=prefix+WORKER
            for name,source in (('api',api_source),('worker',worker_source)):
                path=tmp_path/(name+'.private.py');ast.parse(source);path.write_text(source);path.chmod(0o400)
            def launch(name):
                log=(tmp_path/(name+'.private.log')).open('xb');os.fchmod(log.fileno(),0o600);outputs.append(log)
                actor=subprocess.Popen([sys.executable,'-B',str(tmp_path/(name+'.private.py')),str(pack)],env=dict(env,PYTHONMALLOC='pymalloc'),stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT);actors.append(actor);return actor
            api=launch('api');deadline=time.monotonic()+90
            while not (tmp_path/'api-ready.private.json').exists():
                assert api.poll() is None and time.monotonic()<deadline,'owned API startup failed';time.sleep(.05)
            ready=json.loads((tmp_path/'api-ready.private.json').read_bytes());context=ssl.create_default_context(cafile=str(tmp_path/'api.crt'))
            def http(method,path,body=None):
                connection=http_client.HTTPSConnection('127.0.0.1',ready['port'],context=context,timeout=60)
                try:
                    headers={'Authorization':'Bearer '+('owned-solar-concurrent-native-'+'c'*40)}
                    if body is not None:headers['Content-Type']='application/json'
                    connection.request(method,path,body=body,headers=headers);response=connection.getresponse();raw=response.read(2*1024*1024+1)
                    assert len(raw)<=2*1024*1024 and response.getheader('Cache-Control')=='no-store'
                    requests.append({'status':response.status,'bytes':len(raw)});return response.status,json.loads(raw)
                finally:connection.close()
            status,value=http('POST','/v1/crop-greenhouse-solar-executions',json.dumps(p['body']).encode())
            assert status==202;job=value['job_id'];path='/v1/jobs/'+job+'/crop-greenhouse-solar-execution'
            worker=launch('worker');deadline=time.monotonic()+360
            while True:
                time.sleep(10)
                assert api.poll() is None and time.monotonic()<deadline,'owned calculation timed out'
                status,progress=http('GET',path);assert status in (200,503)
                if status==200 and progress['job']['state']=='succeeded':break
                status,value=http('GET',path+'/prefix')
                if status==200 and value['prefix_status']=='accepted' and value['reference']['checkpoint']['computed_through_utc'] is not None:
                    pin=value['reference']['selector'];status,page=http('GET',path+'/prefix/samples?'+urlencode(pin))
                    if status==200 and page['prefix_status']=='accepted':observed.append(page)
                else:assert status in (200,503)
                assert worker.poll() in (None,0),'owned worker failed'
            worker.wait(timeout=20);assert worker.returncode==0
            result=progress['result'];assert result and result['rights_or_gate_approval'] is False
            status,saved=http('GET','/v1/crop-greenhouse-solar-research-results/'+result['result_id']+'?'+urlencode({**p['body']['farm'],'view':'samples'}));assert status==200
            assert len({v['reference']['checkpoint']['computed_through_utc'] for v in observed})>=2,'two advancing original prefixes not observed'
            for value in observed:
                records=value['page']['records'];assert records==saved['page']['records'][:len(records)]
            (tmp_path/'api-stop').touch(mode=0o600);api.wait(timeout=30);assert api.returncode==0
            proof=json.loads((tmp_path/'worker-proof.private.json').read_bytes());assert proof['PID']!=ready['PID'] and proof['unpaused']
            api_proof=json.loads((tmp_path/'api-proof.private.json').read_bytes());assert not any(api_proof['calls'].values())
            root=Path(os.environ['OSSF_SOLAR_EXECUTION_RUNTIME_EVIDENCE'])
            with (root/'unpaused-normal.private.json').open('x') as f:os.fchmod(f.fileno(),0o400);json.dump({'actual_SCRAM_TLS':True,'worker':proof,'api':api_proof,'advancing_prefixes':len(observed),'original_values_UTC_equal':True,'requests':requests},f,sort_keys=True)
            cleanup=subprocess.run([sys.executable,'-B','-c',CLEANUP,str(config)],env=env,capture_output=True,timeout=30);assert cleanup.returncode==0
        finally:
            (tmp_path/'api-stop').touch(mode=0o600)
            for actor in reversed(actors):
                if actor.poll() is None:actor.send_signal(signal.SIGTERM)
                try:actor.wait(timeout=30)
                except subprocess.TimeoutExpired:actor.kill();actor.wait(timeout=10)
            for output in outputs:output.close()
            for path in tmp_path.rglob('*.pgpass'):path.unlink()
            subprocess.run([str(binary/'pg_ctl'),'-D',str(data),'-m','fast','-w','-t','10','stop'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,timeout=20)

