"""Sequential producer and real HTTP reader share an owned SCRAM database.

The lightweight parent lets the production API and crop producer run separately
under the workspace memory guard. These are synthetic software checks only.
"""
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import tempfile

from test_crop_greenhouse_solar_current_fresh import PREPARE as BASE_PREPARE, CLEANUP

CURRENT_PREPARE = BASE_PREPARE.replace('test_crop_greenhouse_solar_result_store', 'test_crop_greenhouse_co2_result_store')


PREPARE = CURRENT_PREPARE.replace(
    "SimpleNamespace(param=None),patch)", "SimpleNamespace(param=config['case']),patch)"
).replace(
    "pack=t.verify_original_signed_result(setup,root,patch)",
    """store,raw,value,done=t.ready(setup);record=store.put('tenant-1',raw)
pack=t.producer.fresh_pack(root,value,done,store.server)
packed=json.loads(pack.read_bytes())
packed.update(result_id=record['result_id'],payload_sha256=record['payload_sha256'],
 recorded_at=record['recorded_at'].isoformat())
pack.write_text(json.dumps(packed))"""
)


HTTP_READ = r'''
import asyncio,http.client,ipaddress,os,ssl,threading
from datetime import datetime,timedelta,timezone
from urllib.parse import urlencode
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID
from app import api
from app.api_openapi import _SchemaOnlyStores
from app import crop_greenhouse_co2_result_store as result_model
from app import crop_greenhouse_co2_current_query as current_model
from app.crop_result_store import READ_SCOPES
from app.http_identity import BearerGrant,BearerRegistry,PrincipalMiddleware,token_digest
from app.https_service import HttpsApiService

result=result_model.Co2ResultStore(custody,integrity_key=b'owned-co2-result-store-key-32-bytes!')
query=current_model.Co2CurrentQuery(result);public=current_model.public
farm=p['body']['farm'];result_id=p['result_id'];before=counts(service)
with jobs.connect() as conn:
 assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
 rows=conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(result_model.schema.TABLE))).fetchone()['n']
 assert rows==1
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());calls['SQL_writes']=0
execute=psycopg.Connection.execute
def read_only(conn,statement,*args,**kwargs):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  calls['SQL_writes']+=1;raise AssertionError('HTTP query attempted SQL mutation')
 return execute(conn,statement,*args,**kwargs)
psycopg.Connection.execute=read_only

def inventory():
 found={}
 for path in Path('/proc/self/fd').iterdir():
  try:
   stat=path.stat();found[path.name]=(os.readlink(path),stat.st_dev,stat.st_ino)
  except FileNotFoundError:pass
 return found
initial=inventory()
expected={view:query.read('tenant-1',result_id,farm,view=view) for view in ('summary','samples','events')}
summary=json.loads(expected['summary']);status=summary['summary']['status']
assert status in ('completed','hold') and summary['reference']['G0_G4']=='not_assessed'
assert summary['reference']['rights_or_gate_approval'] is False
assert summary['summary']['last_confirmed']['time']['at'].endswith('.123456Z')
if status=='hold':assert summary['summary']['checkpoint_sha256'] is None and summary['summary']['hold'] is not None
assert inventory()==initial
app=api.create_app(jobs,holds,runs,_SchemaOnlyStores(),principal_provider=provider,
 thermal_scenario_store=replay.thermal,farm_scenario_service=replay,farm_authoring_service=service.farms,
 crop_greenhouse_co2_result_store=result,crop_greenhouse_co2_current_query=query)
TOKEN=b'owned-co2-http-native-test-'+b's'*40
NOW=datetime(2026,10,17,tzinfo=timezone.utc);clock={'now':NOW}
def protect(*,scopes=READ_SCOPES,tenant='tenant-1'):
 grant=BearerGrant(token_digest(TOKEN),tenant,frozenset(scopes),NOW,NOW+timedelta(hours=1))
 return PrincipalMiddleware(app,BearerRegistry((grant,),clock=lambda:clock['now']))
protected=protect();mode['preparing']=False
PATH='/v1/crop-greenhouse-co2-research-results/'

async def asgi(target,receive,send,*,identity=result_id,extra=''):
 path=PATH+identity
 await target({'type':'http','asgi':{'version':'3.0'},'method':'GET','path':path,
  'raw_path':path.encode(),'root_path':'','query_string':(urlencode(farm)+extra).encode(),
  'headers':[(b'authorization',b'Bearer '+TOKEN)],'scheme':'https','http_version':'1.1',
  'server':('test',443),'client':('test',1234),'state':{}},receive,send)

def get(target=protected,*,identity=result_id,extra='',body=b'',disconnect=False):
 sent=[]
 async def receive():
  return {'type':'http.disconnect'} if disconnect else {'type':'http.request','body':body,'more_body':False}
 async def send(message):sent.append(message)
 asyncio.run(asgi(target,receive,send,identity=identity,extra=extra))
 first=next(m for m in sent if m['type']=='http.response.start')
 wire=b''.join(m.get('body',b'') for m in sent if m['type']=='http.response.body')
 return first['status'],json.loads(wire)

root=Path(sys.argv[1]).parent;tls=root/'private-tls';tls.mkdir(mode=0o700)
key=ec.generate_private_key(ec.SECP256R1());now=datetime.now(timezone.utc)
name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Owned co2 HTTP test')])
certificate=(x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
 .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
 .not_valid_after(now+timedelta(minutes=10))
 .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),False)
 .sign(key,hashes.SHA256()))
cert=tls/'cert.pem';private=tls/'key.pem'
cert.write_bytes(certificate.public_bytes(serialization.Encoding.PEM));cert.chmod(0o644)
private.write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,
 serialization.NoEncryption()));private.chmod(0o600)
server=HttpsApiService(protected,cert,private,port=0).server();baseline=inventory()
assert baseline==initial
thread=threading.Thread(target=server.run,daemon=True);thread.start();replies={}
try:
 deadline=time.monotonic()+10
 while not server.started:
  assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
 port=server.servers[0].sockets[0].getsockname()[1]
 context=ssl.create_default_context(cafile=str(cert))
 for view,original in expected.items():
  connection=http.client.HTTPSConnection('127.0.0.1',port,context=context,timeout=30)
  try:
   started=time.monotonic()
   connection.request('GET',PATH+result_id+'?'+urlencode(farm)+('' if view=='summary' else '&view='+view),
    headers={'Authorization':'Bearer '+TOKEN.decode()})
   response=connection.getresponse();wire=response.read()
   assert response.status==200 and wire==original and len(wire)<=public.MAX_RESPONSE_BYTES
   assert response.getheader('Cache-Control')=='no-store'
   assert response.getheader('X-OSSF-CO2-Query-Version')==current_model.VERSION
   assert response.getheader('X-OSSF-CO2-Query-Code-SHA256')==current_model.CODE_SHA256
   assert response.getheader('X-OSSF-CO2-Projection-Code-SHA256')==public.CODE_SHA256
   replies[view]={'bytes':len(wire),'sha256':sha256(wire).hexdigest(),'seconds':time.monotonic()-started}
  finally:connection.close()
finally:
 server.should_exit=True;thread.join(15);assert not thread.is_alive()
assert inventory()==baseline and current_principal() is None

denied=[];transports=[]
if status=='completed':
 read=query.read;observed=[]
 def tracked(*args,**kwargs):observed.append(1);return read(*args,**kwargs)
 query.read=tracked
 try:
  for extra in ('&extra=x','&view=events&offset=129','&view=samples&limit=65'):
   assert get(extra=extra)[0]==422
  assert get(body=b'{}')[0]==422 and get(disconnect=True)[0]==422
  assert get(protect(scopes=READ_SCOPES[:-1]))[0]==403
  assert observed==[]
  assert get(identity='joint-co2-solar-result-v1:'+'0'*64)[0]==404
  assert get(protect(tenant='foreign'))[0] in (403,404)
  assert len(observed)==2
 finally:query.read=read
 source=replay.candidates._source._source;previous=source.get_input_rights;encode=public._public_bytes
 changes=[('input-rights',lambda:setattr(rights,'allowed',False),lambda:setattr(rights,'allowed',True)),
  ('review',lambda:review.update(status='revoked'),lambda:review.update(status=p['review']['status'])),
  ('farm-source',lambda:setattr(source,'get_input_rights',lambda *_:None),lambda:setattr(source,'get_input_rights',previous)),
  ('credential',lambda:clock.update(now=NOW+timedelta(hours=1)),lambda:clock.update(now=NOW))]
 for name,withdraw,restore in changes:
  for view in ('summary','samples','events'):
   observed=[]
   def serialized(value):
    wire=encode(value);observed.append(1)
    if len(observed)==2:withdraw()
    return wire
   try:
    public._public_bytes=serialized
    refused,value=get(extra='' if view=='summary' else '&view='+view)
    assert refused==(401 if name=='credential' else 422) and 'error' in value and len(observed)==2
    denied.append(name+':'+view)
   finally:public._public_bytes=encode;restore()
 for transport in ('cancel','send-failure'):
  entered=threading.Event();release=threading.Event();closed=threading.Event();wires=[];after=[]
  fd=inventory();read=query.read
  def serialized(value):
   wire=encode(value);wires.append(wire)
   if len(wires)==2:entered.set();assert release.wait(10)
   return wire
  def tracked(*args,**kwargs):
   try:return read(*args,**kwargs)
   finally:after.append(current_principal());closed.set()
  async def exercise():
   async def receive():return {'type':'http.request','body':b'','more_body':False}
   async def send(_):raise RuntimeError('owned transport failure')
   task=asyncio.create_task(asgi(protected,receive,send));deadline=time.monotonic()+20
   while not entered.is_set():
    assert time.monotonic()<deadline;await asyncio.sleep(.001)
   if transport=='cancel':task.cancel()
   else:release.set()
   try:
    try:await task
    except (asyncio.CancelledError,RuntimeError) as error:
     assert type(error) is (asyncio.CancelledError if transport=='cancel' else RuntimeError)
    else:raise AssertionError('transport unexpectedly completed')
   finally:release.set()
   while not closed.is_set():
    assert time.monotonic()<deadline;await asyncio.sleep(.001)
  try:
   public._public_bytes=serialized;query.read=tracked;asyncio.run(exercise())
  finally:release.set();public._public_bytes=encode;query.read=read
  mode['preparing']=True
  assert closed.is_set() and query.read('tenant-1',result_id,farm)==wires[1]
  assert current_principal() is None and inventory()==fd
  if transport=='cancel':assert after==[None]
  mode['preparing']=False;transports.append(transport)
mode['preparing']=True
assert all(v==0 for v in calls.values()) and counts(service)==before
with jobs.connect() as conn:
 assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(result_model.schema.TABLE))).fetchone()['n']==rows
assert inventory()==baseline and current_principal() is None
print(json.dumps({'PID':os.getpid(),'status':status,'actual_scram':True,'verified_TLS':True,
 'replies':replies,'original_response_bytes_equal':True,'original_values_units_UTC':True,
 'withdrawals_withheld':denied,'transports_released':transports,'calls':calls,
 'counts_unchanged':True,'FD_before_after':[len(baseline),len(inventory())],
 'actual_crop_Runs':0,'G0_G4':'not_assessed','rights_or_gate_approval':False}))
'''


def save(name, value):
    directory = os.environ.get('OSSF_CO2_HTTP_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as output:
            os.fchmod(output.fileno(), 0o400)
            json.dump(value, output, sort_keys=True, indent=2)
            output.flush(); os.fsync(output.fileno())


def exercise(tmp_path, case):
    if not os.environ.get('OSSF_TEST_PG_DSN') or not os.environ.get('OSSF_TEST_PG_BIN'):
        import pytest
        pytest.skip('owned PostgreSQL test configuration is unset')
    binary = Path(os.environ['OSSF_TEST_PG_BIN'])
    buffers = os.environ.get('OSSF_TEST_PG_SHARED_BUFFERS_MIB', '4')
    assert buffers in ('1', '4', '8', '16') and __debug__
    backend = Path(__file__).resolve().parents[1]
    env = dict(os.environ, PYTHONPATH=os.pathsep.join((str(backend), str(backend/'tests'))))
    with tempfile.TemporaryDirectory(prefix='ossf-login-pg-') as directory:
        root = Path(directory); data = root/'data'; sockets = root/'socket'
        sockets.mkdir(mode=0o700)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
        subprocess.run([str(binary/'initdb'), '-D', str(data), '-U', 'ossf_login_admin',
            '--auth-local=trust', '--auth-host=scram-sha-256', '--no-locale', '--encoding=UTF8'],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=30)
        options = (f'-h 127.0.0.1 -p {port} -k {shlex.quote(str(sockets))} '
            f'-c shared_buffers={buffers}MB -c jit=off -c work_mem=64kB '
            '-c max_connections=12 -c max_worker_processes=0 -c max_parallel_workers=0 -c autovacuum=off')
        subprocess.run([str(binary/'pg_ctl'), '-D', str(data), '-l', str(root/'server.log'),
            '-w', '-t', '10', 'start', '-o', options],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
        config = tmp_path/'cluster.private.json'
        config.write_text(json.dumps({'root':str(tmp_path), 'shared_buffers':buffers, 'case':case,
            'database':{'admin':f'host={sockets} port={port} dbname=postgres user=ossf_login_admin',
                'host':'127.0.0.1', 'port':port, 'database':'postgres'}})); config.chmod(0o600)
        try:
            first = subprocess.run([sys.executable, '-B', '-c', PREPARE, str(config)],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
            assert first.returncode == 0, first.stderr.decode()
            prepared = json.loads((tmp_path/'prepared.private.json').read_bytes())
            prefix = Path(prepared['script']).read_text().split('\nfrom app import crop_greenhouse_co2_result_store as result_model')[0]
            assert prefix.count('provider=lambda:principal') == 1
            prefix = 'from app.http_identity import current_principal\n' + prefix.replace(
                'provider=lambda:principal', "mode={'preparing':True}\ndef provider():return principal if mode['preparing'] else current_principal()")
            assert prefix.count("return tenant=='tenant-1' and") == 1
            prefix = prefix.replace("return tenant=='tenant-1' and", "return getattr(self,'allowed',True) is True and tenant=='tenant-1' and")
            verifier = tmp_path/'http-verifier.private.py'
            verifier.write_text(prefix+HTTP_READ); verifier.chmod(0o400)
            second = subprocess.run([sys.executable, '-B', str(verifier), prepared['pack']],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
            assert second.returncode == 0, second.stderr.decode()
            evidence = json.loads(second.stdout)
            assert evidence['PID'] != prepared['PID']
            assert not Path('/proc', str(prepared['PID'])).exists()
            assert not Path('/proc', str(evidence['PID'])).exists()
            assert evidence['actual_scram'] and evidence['verified_TLS']
            assert all(v == 0 for v in evidence['calls'].values())
            assert evidence['status'] == ('hold' if case else 'completed')
            save('native-'+evidence['status']+'.json', evidence)
            cleanup = subprocess.run([sys.executable, '-B', '-c', CLEANUP, str(config)],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
            assert cleanup.returncode == 0, cleanup.stderr.decode()
            save('database-cleanup-'+evidence['status']+'.json', json.loads(cleanup.stdout))
        finally:
            for passfile in tmp_path.rglob('*.pgpass'):
                passfile.unlink()
            subprocess.run([str(binary/'pg_ctl'), '-D', str(data), '-m', 'fast', '-w', '-t', '10', 'stop'],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)


def test_native_scram_verified_https_completed_and_current_withdrawals(tmp_path):
    exercise(tmp_path, None)


def test_native_scram_verified_https_hold(tmp_path):
    exercise(tmp_path, 'hold')
