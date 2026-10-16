"""Sequential independent processes retain one owned SCRAM DB and signed files."""
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import tempfile



PREPARE = '''
from pathlib import Path
from types import SimpleNamespace
import json,os,sys,psycopg,pytest
import test_crop_greenhouse_solar_result_store as t
from login_database import login_scope,assert_host_scram
config=json.loads(Path(sys.argv[1]).read_bytes());root=Path(config['root'])
database=config['database']
psycopg.Connection.close=t.producer.settled_close(database['port'])
with psycopg.connect(database['admin']) as conn:
 assert set(assert_host_scram(conn))=={'scram-sha-256'}
 assert conn.execute('SHOW shared_buffers').fetchone()[0]==config['shared_buffers']+'MB'
 assert conn.execute('SHOW jit').fetchone()[0]=='off'
patch=pytest.MonkeyPatch()
request=SimpleNamespace(param={k:True for k in ('market_calculation','market_source_storage',
 'thermal_scenario_storage','break_even_calculation','crop_cycle_result_storage')})
scope=login_scope.__wrapped__(database,root,request)
original=next(scope)
current=t.login_scope.__wrapped__(original,SimpleNamespace(param=True))
authoring=t.authoring.__wrapped__(current,patch)
setup=t.setup.__wrapped__(authoring,root,t.profiles.__wrapped__(),SimpleNamespace(param=None),patch)
pack=t.verify_original_signed_result(setup,root,patch)
script=root/'fresh-verifier.private.py';script.write_text(t.FRESH_SCRIPT);script.chmod(0o400)
output=root/'prepared.private.json'
with output.open('x') as f:
 os.fchmod(f.fileno(),0o400);json.dump({'pack':str(pack),'script':str(script),'PID':os.getpid()},f);f.flush();os.fsync(f.fileno())
# The test parent owns the cluster; preserve roles/files for the next process.
os._exit(0)
'''

CURRENT_READ = '''import os

from app import crop_greenhouse_solar_result_store as result_model
from app import crop_greenhouse_solar_current_query as current_model
result=result_model.SolarResultStore(custody,integrity_key=b'owned-solar-result-store-key-32-bytes!')
query=current_model.SolarCurrentQuery(result)
class Patch:
 def setattr(self,target,name,value):setattr(target,name,value)
calls=measured(Patch());calls['SQL_writes']=0
execute=psycopg.Connection.execute
def read_only(conn,statement,*args,**kwargs):
 text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
 if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
  calls['SQL_writes']+=1;raise AssertionError('current read attempted SQL mutation')
 return execute(conn,statement,*args,**kwargs)
psycopg.Connection.execute=read_only
farm=p['body']['farm'];before=counts(service)
record=result.get('tenant-1',p['result_id'],farm)
assert record['payload_sha256']==p['payload_sha256'] and record['recorded_at'].isoformat()==p['recorded_at']
assert record['progress_sha256']==p['expected_progress_sha256']
terminal=result.summary('tenant-1',p['result_id'],farm)
pages={k:result.page('tenant-1',p['result_id'],farm,k) for k in ('samples','events')}
public=current_model.public;responses={};sizes={}
for view in ('summary','samples','events'):
 expected=public._public_bytes(public.project_solar_result(record,terminal,view=view,
  page=None if view=='summary' else pages[view],limit=None if view=='summary' else 64 if view=='samples' else 8))
 raw=query.read('tenant-1',p['result_id'],farm,view=view);assert raw==expected
 value=json.loads(raw);assert value['reference']['rights_or_gate_approval'] is False
 assert value['reference']['input']['provenance_sha256']==json.loads(record['payload_raw'])['input']['provenance_sha256']
 if view=='summary':assert value['summary']['last_confirmed']=={'value':terminal['last_confirmed'],'time':terminal['times']['last_confirmed']}
 elif view=='samples':assert value['page']['records']==pages[view]['records']
 else:
  for got,saved in zip(value['page']['records'],pages[view]['records'],strict=True):
   assert got['time']==saved['time']
   for key in ('solar_before','solar_after'):assert got['value'][key]==saved['value'][key]
   assert 'event' not in got['value']['management'] and not {'combined_forcing_before','combined_forcing_after'}&set(got['value'])
 responses[view]=sha256(raw).hexdigest();sizes[view]=len(raw)
if 'solar_response_sha256' in p:assert responses==p['solar_response_sha256']
review['status']='revoked'
try:query.read('tenant-1',p['result_id'],farm)
except current_model.SolarCurrentQueryHold:pass
else:raise AssertionError('fresh current review withdrawal allowed')
assert all(v==0 for v in calls.values()) and counts(service)==before
with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
print(json.dumps({'PID':os.getpid(),'actual_scram':True,'calls':calls,'response_sha256':responses,'bytes':sizes,
 'original_values_units_UTC':True,'revoked_review_denied':True,'counts_unchanged':True}))
'''

CLEANUP = '''
import json,sys,psycopg
from pathlib import Path
from psycopg import sql
config=json.loads(Path(sys.argv[1]).read_bytes())
with psycopg.connect(config['database']['admin']) as conn:
 roles=[r[0] for r in conn.execute("SELECT rolname FROM pg_roles WHERE rolname LIKE 'login_%' ORDER BY rolname LIKE 'login_owner_%'")]
 for role in roles:
  conn.execute(sql.SQL('DROP OWNED BY {} CASCADE').format(sql.Identifier(role)))
  conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
 for (name,) in conn.execute("SELECT nspname FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchall():
  conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(name)))
 schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
 roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
 assert schemas==roles==0
 print(json.dumps({'schemas':schemas,'roles':roles}))
'''


def save(name, value):
    destination = os.environ.get('OSSF_SOLAR_PUBLIC_EVIDENCE')
    if destination:
        with (Path(destination)/name).open('x') as output:
            os.fchmod(output.fileno(), 0o400)
            json.dump(value, output, sort_keys=True, indent=2)
            output.flush(); os.fsync(output.fileno())


def test_original_current_wires_and_two_sequential_fresh_processes(tmp_path):
    if not os.environ.get('OSSF_TEST_PG_DSN') or not os.environ.get('OSSF_TEST_PG_BIN'):
        import pytest
        pytest.skip('owned PostgreSQL test configuration is unset')
    binary = Path(os.environ['OSSF_TEST_PG_BIN'])
    buffers = os.environ.get('OSSF_TEST_PG_SHARED_BUFFERS_MIB', '4')
    assert buffers in ('1', '4', '8', '16')
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
        config.write_text(json.dumps({'root':str(tmp_path), 'shared_buffers':buffers,
            'database':{'admin':f'host={sockets} port={port} dbname=postgres user=ossf_login_admin',
                'host':'127.0.0.1', 'port':port, 'database':'postgres'}})); config.chmod(0o600)
        try:
            first = subprocess.run([sys.executable, '-B', '-c', PREPARE, str(config)],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
            assert first.returncode == 0, first.stderr.decode()
            prepared = json.loads((tmp_path/'prepared.private.json').read_bytes())
            prefix = Path(prepared['script']).read_text().split('\nfrom app import crop_greenhouse_solar_result_store as result_model')[0]
            verifier = tmp_path/'current-verifier.private.py'; verifier.write_text(prefix+CURRENT_READ); verifier.chmod(0o400)
            second = subprocess.run([sys.executable, '-B', str(verifier), prepared['pack']],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
            assert second.returncode == 0, second.stderr.decode()
            evidence = json.loads(second.stdout)
            assert evidence['PID'] != prepared['PID']
            assert not Path('/proc', str(prepared['PID'])).exists()
            assert not Path('/proc', str(evidence['PID'])).exists()
            assert evidence['actual_scram'] and all(v == 0 for v in evidence['calls'].values())
            packed = json.loads(Path(prepared['pack']).read_bytes()); packed['solar_response_sha256'] = evidence['response_sha256']
            next_pack = tmp_path/'second-current.private.json'; next_pack.write_text(json.dumps(packed)); next_pack.chmod(0o600)
            third = subprocess.run([sys.executable, '-B', str(verifier), str(next_pack)],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=300)
            assert third.returncode == 0, third.stderr.decode()
            repeated = json.loads(third.stdout)
            assert repeated['PID'] != evidence['PID'] and not Path('/proc',str(repeated['PID'])).exists()
            assert repeated['response_sha256'] == evidence['response_sha256']
            assert all(v == 0 for v in repeated['calls'].values())
            save('fresh.json', {'first':evidence, 'second':repeated, 'sequential_processes_same_database':True})
            cleanup = subprocess.run([sys.executable, '-B', '-c', CLEANUP, str(config)],
                env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
            assert cleanup.returncode == 0, cleanup.stderr.decode()
            save('database-cleanup.json', json.loads(cleanup.stdout))
        finally:
            for passfile in tmp_path.rglob('*.pgpass'):
                passfile.unlink()
            subprocess.run([str(binary/'pg_ctl'), '-D', str(data), '-m', 'fast', '-w', '-t', '10', 'stop'],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=20)
