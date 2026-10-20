"""API diagnostics expose actual statuses and exception locations, never bodies."""
import json
import os
from pathlib import Path
import subprocess
import sys

TRACE = Path(__file__).resolve().parents[2]/'research/crop-solar-api-response-trace.py'


def command(directory, body):
    target = str(directory/'api.private.py')
    script = ('from pathlib import Path\n__file__='+repr(target)+'\n'
        'exec(compile(Path('+repr(str(TRACE))+').read_text(),'+repr(str(TRACE))+',"exec"))\n'
        'exec(compile('+repr(body)+','+repr(target)+',"exec"))\n')
    return [sys.executable, '-B', '-c', script, str(directory/'pack')]


def read(directory):
    raw = (directory/'api-response-diagnostics.private.json').read_bytes()
    assert len(raw) <= 64*1024 and b'controlled_secret_never_export' not in raw
    return json.loads(raw)


def test_actual_http_status_and_fixed_code_exclude_raw_body(tmp_path):
    body = '''
def request_http():
 return 422, {'error':{'code':'solar_prefix_hold','message':'controlled_secret_never_export'},'private':'controlled_secret_never_export'}
request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['responses']) == 1
    assert value['responses'][0]['status'] == 422
    assert value['responses'][0]['code'] == 'solar_prefix_hold'
    assert value['responses'][0]['caller_line'] == 4
    assert value['diagnostic_only'] is True and value['normal_execution_accepted'] is False


def test_actual_threaded_prefix_exception_has_only_type_and_locations(tmp_path):
    body = r'''
import threading
exec(compile("def failed():\n try:raise ValueError('controlled_secret_never_export')\n except ValueError:pass\n", '/owned/app/crop_greenhouse_solar_prefix.py','exec'))
thread=threading.Thread(target=failed);thread.start();thread.join(2)
assert not thread.is_alive()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert value['responses'] == []
    assert value['exceptions'][0]['exception_type'] == 'ValueError'
    assert value['exceptions'][0]['locations'] == [
        {'file':'crop_greenhouse_solar_prefix.py','line':2,'function':'failed'}]


def test_response_journal_is_bounded_and_unknown_codes_are_omitted(tmp_path):
    body = '''
def request_http():return 503, {'error':{'code':'controlled_secret_never_export'}}
for _ in range(100):request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['responses']) == 32 and value['dropped_responses'] == 68
    assert all(row['status'] == 503 and 'code' not in row for row in value['responses'])
    assert (tmp_path/'api-response-diagnostics.private.json').stat().st_mode & 0o777 == 0o600
    assert not list(tmp_path.glob('*.tmp'))


def test_client_durations_and_fixed_routes_do_not_export_paths(tmp_path):
    body = '''
def request_http(method,path,body=None):
 sum(range(2000))
 return 200, {'private':'controlled_secret_never_export'}
for path in ('/v1/crop-greenhouse-solar-executions',
 '/v1/jobs/controlled_secret_never_export/crop-greenhouse-solar-execution',
 '/v1/jobs/controlled_secret_never_export/crop-greenhouse-solar-execution/prefix',
 '/v1/jobs/controlled_secret_never_export/crop-greenhouse-solar-execution/prefix/samples?secret=controlled_secret_never_export',
 '/v1/crop-greenhouse-solar-research-results/controlled_secret_never_export?view=samples',
 '/controlled_secret_never_export'):
 request_http('GET',path,b'controlled_secret_never_export')
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert [row['route'] for row in value['responses']] == [
        'admission', 'progress', 'prefix', 'samples', 'saved_result', 'other']
    for row in value['responses']:
        assert row['finished_monotonic_ns'] > row['started_monotonic_ns']
        assert row['wall_ns'] == row['finished_monotonic_ns'] - row['started_monotonic_ns']
        assert row['client_thread_CPU_ns'] >= 0
        assert row['response_returned'] is True
    assert value['active_client_requests'] == value['active_server_operations'] == []


SERVER_FUNCTIONS = r'''
def controlled(module,filename,source):
 namespace={'__name__':module}
 exec(compile(source,filename,'exec'),namespace)
 return namespace
execute=controlled('psycopg.connection','/owned/psycopg/connection.py',
 "def execute(query):\n sum(range(2000))\n return 1\n")['execute']
unknown=controlled('unrelated','/owned/unrelated/connection.py',
 "def execute(query):return 1\n")['execute']
checked=controlled('app.api_crop_greenhouse_solar_execution_http',
 '/owned/app/api_crop_greenhouse_solar_execution_http.py',
 "def checked(action):return action()\n")['checked']
prefix=controlled('app.api_crop_greenhouse_solar_prefix_routes',
 '/owned/app/api_crop_greenhouse_solar_prefix_routes.py',
 "def read(action):return action()\n")['read']
current=controlled('app.crop_greenhouse_solar_farm_binding',
 '/owned/app/crop_greenhouse_solar_farm_binding.py',
 "def current():pass\n")['current']
loading=controlled('app.crop_greenhouse_solar_storage',
 '/owned/app/crop_greenhouse_solar_storage.py',
 "def _load():pass\n")['_load']
source=controlled('app.market_source_store','/owned/app/market_source_store.py',
 "def _select_with_job():pass\n")['_select_with_job']
'''


def test_server_thread_counts_ignore_nested_roots_and_unrelated_sql(tmp_path):
    body = SERVER_FUNCTIONS + r'''
import threading
def action():
 current();loading();source();unknown('controlled_secret_never_export')
 execute('controlled_secret_never_export');execute('controlled_secret_never_export')
def work():
 for _ in range(2):checked(lambda:prefix(action))
 execute('controlled_secret_never_export')
thread=threading.Thread(target=work);thread.start();thread.join(3)
assert not thread.is_alive()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert value['responses'] == [] and len(value['server_operations']) == 2
    for row in value['server_operations']:
        assert row['operation'] == 'execution'
        assert row['SQL_calls'] == 2
        assert row['current_calls'] == row['storage_loads'] == row['source_selects'] == 1
        assert 0 < row['SQL_wall_ns'] <= row['wall_ns']
        assert row['SQL_thread_CPU_ns'] >= 0
        assert row['thread_CPU_ns'] >= 0
    assert value['active_server_operations'] == []


def test_exception_cleans_server_lifetime_before_reused_thread(tmp_path):
    body = SERVER_FUNCTIONS + r'''
def failed():
 execute('controlled_secret_never_export')
 raise ValueError('controlled_secret_never_export')
try:prefix(failed)
except ValueError:pass
prefix(lambda:execute('controlled_secret_never_export'))
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['server_operations']) == 2
    assert [row['SQL_calls'] for row in value['server_operations']] == [1, 1]
    assert value['server_operations'][0]['exception_events'] >= 1
    assert value['server_operations'][1]['exception_events'] == 0
    assert value['active_server_operations'] == []


def test_overlapping_threads_keep_separate_operation_counters(tmp_path):
    body = SERVER_FUNCTIONS + r'''
import threading
barrier=threading.Barrier(2)
def work(n):
 def action():
  barrier.wait(2)
  for _ in range(n):current();source()
  for _ in range(n+1):execute('controlled_secret_never_export')
 checked(action)
threads=[threading.Thread(target=work,args=(n,)) for n in (1,2)]
for thread in threads:thread.start()
for thread in threads:thread.join(3)
assert not any(thread.is_alive() for thread in threads)
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert sorted((row['SQL_calls'], row['current_calls'], row['source_selects'])
                  for row in value['server_operations']) == [(2, 1, 1), (3, 2, 2)]
    assert value['active_server_operations'] == []


def test_nested_sql_counts_calls_and_times_only_the_outer_execution(tmp_path):
    body = SERVER_FUNCTIONS + r'''
recursive=controlled('psycopg.connection','/owned/psycopg/connection.py',
 "def execute(n):\n if n:execute(n-1)\n sum(range(1000000))\n")['execute']
checked(lambda:recursive(2))
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['server_operations']) == 1
    row = value['server_operations'][0]
    assert row['SQL_calls'] == 3 and row['SQL_unfinished_calls'] == 0
    assert 0 < row['SQL_wall_ns'] <= row['wall_ns']


def test_mixed_journal_enforces_total_bytes_with_maximum_unicode_locations(tmp_path):
    body = SERVER_FUNCTIONS + r'''
name='界'*96
recursive=controlled('controlled','/owned/'+name+'.py',
 'def '+name+'(n):\n if n:return '+name+'(n-1)\n raise ValueError("controlled_secret_never_export")\n')[name]
def request_http():return 503,{'error':{'code':'controlled_secret_never_export'}}
for _ in range(40):
 try:prefix(lambda:recursive(20))
 except ValueError:pass
 request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['responses']) <= 32 and len(value['server_operations']) <= 32
    assert len(value['exceptions']) <= 16 and value['dropped_exceptions'] > 24
    assert value['active_client_requests'] == value['active_server_operations'] == []
    assert not list(tmp_path.glob('*.tmp'))


def test_active_operations_are_bounded_without_exporting_frame_or_thread_ids(tmp_path):
    body = '''
def request_http(depth):
 if depth:return request_http(depth-1)
 Path(__file__).with_name('during.json').write_bytes(Path(__file__).with_name('api-response-diagnostics.private.json').read_bytes())
 return 200,{}
request_http(20)
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    during = json.loads((tmp_path/'during.json').read_bytes())
    assert len(during['active_client_requests']) == 16
    assert during['dropped_active_operations'] >= 5
    value = read(tmp_path)
    assert len(value['responses']) == 16 and value['active_client_requests'] == []
    for row in during['active_client_requests']:
        assert 'frame' not in repr(row) and 'thread_id' not in row
        assert 'finished_monotonic_ns' not in row and 'status' not in row


def test_interrupted_root_is_kept_incomplete_without_fabricated_response(tmp_path):
    body = SERVER_FUNCTIONS + '''
import os
def request_http():
 checked(lambda:os._exit(0))
request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert value['responses'] == value['server_operations'] == []
    assert len(value['active_client_requests']) == len(value['active_server_operations']) == 1
    assert all('finished_monotonic_ns' not in row and 'status' not in row
               for row in value['active_client_requests'] + value['active_server_operations'])


PROJECTION_FUNCTIONS = SERVER_FUNCTIONS + r'''
projection=controlled('app.crop_greenhouse_solar_prefix',
 '/owned/app/crop_greenhouse_solar_prefix.py',
 "def _after_projection(action):return action()\n")['_after_projection']
'''


def test_nested_projection_preserves_parent_counts_and_original_return(tmp_path):
    body = PROJECTION_FUNCTIONS + r'''
seen=[]
def action():
 seen.append('child');current();source();execute('controlled_secret_never_export')
 return 17
def reading():
 seen.append('parent');current();source();execute('controlled_secret_never_export')
 return projection(action)
assert prefix(reading)==17 and seen==['parent','child']
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['server_operations']) == 2
    assert value['schema_version'] == 'solar-api-response-cost-v3'
    child, parent = value['server_operations']
    assert child['operation'] == 'prefix_projection' and parent['operation'] == 'prefix'
    assert child['parent_operation'] == 'prefix'
    assert child['parent_started_monotonic_ns'] == parent['started_monotonic_ns']
    assert parent['projection_calls'] == 1 and parent['projection_spans_dropped'] == 0
    for key in ('SQL_calls', 'current_calls', 'source_selects'):
        assert child[key] == 1 and parent[key] == 2
    assert child['storage_loads'] == parent['storage_loads'] == 0
    assert 0 < child['SQL_wall_ns'] <= child['wall_ns'] <= parent['wall_ns']
    assert 0 <= child['thread_CPU_ns'] <= parent['thread_CPU_ns']
    assert value['active_server_operations'] == []


def test_projection_exception_and_reused_thread_close_both_lifetimes(tmp_path):
    body = PROJECTION_FUNCTIONS + r'''
def failed():
 current();execute('controlled_secret_never_export')
 raise ValueError('controlled_secret_never_export')
try:prefix(lambda:projection(failed))
except ValueError:pass
prefix(lambda:projection(lambda:execute('controlled_secret_never_export')))
projection(lambda:execute('controlled_secret_never_export'))
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    rows = read(tmp_path)['server_operations']
    assert [r['operation'] for r in rows] == [
        'prefix_projection', 'prefix', 'prefix_projection', 'prefix', 'prefix_projection']
    assert [r['SQL_calls'] for r in rows] == [1, 1, 1, 1, 1]
    assert all(r['exception_events'] >= 1 for r in rows[:2])
    assert all(r['exception_events'] == 0 for r in rows[2:])
    assert rows[-1].get('parent_operation') is None
    assert read(tmp_path)['active_server_operations'] == []


def test_projection_response_correlation_exposes_window_exclusions(tmp_path):
    body = PROJECTION_FUNCTIONS + r'''
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=1) as executor:
 def request_http(method,path,body=None):
  executor.submit(lambda:prefix(lambda:projection(lambda:execute('controlled_secret_never_export')))).result(2)
  return 200,{'prefix_status':'accepted','private':'controlled_secret_never_export'}
 for _ in range(40):request_http('GET','/v1/jobs/controlled_secret_never_export/crop-greenhouse-solar-execution/prefix')
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=10)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert len(value['responses']) == len(value['server_operations']) == 32
    assert value['dropped_responses'] == 8 and value['dropped_server_operations'] == 48
    parents = [r for r in value['server_operations'] if r['operation'] == 'prefix']
    children = [r for r in value['server_operations'] if r['operation'] == 'prefix_projection']
    assert len(parents) == len(children) == 16
    matched = 0
    for response in value['responses']:
        matches = [p for p in parents if response['started_monotonic_ns'] <=
                   p['started_monotonic_ns'] <= p['finished_monotonic_ns'] <= response['finished_monotonic_ns']]
        if not matches:
            continue
        assert len(matches) == 1
        parent = matches[0]
        child, = [c for c in children if c['parent_operation'] == parent['operation']
                  and c['parent_started_monotonic_ns'] == parent['started_monotonic_ns']]
        assert parent['started_monotonic_ns'] <= child['started_monotonic_ns'] <= child['finished_monotonic_ns'] <= parent['finished_monotonic_ns']
        matched += 1
    assert matched == 16 and len(value['responses'])-matched == 16


def test_projection_child_shares_existing_active_limit(tmp_path):
    body = PROJECTION_FUNCTIONS + r'''
def action():
 current();execute('controlled_secret_never_export')
 Path(__file__).with_name('during.json').write_bytes(Path(__file__).with_name('api-response-diagnostics.private.json').read_bytes())
def request_http(n):
 if n:return request_http(n-1)
 prefix(lambda:projection(action));return 200,{}
request_http(14)
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    during = json.loads((tmp_path/'during.json').read_bytes())
    assert len(during['active_client_requests'])+len(during['active_server_operations']) == 16
    value = read(tmp_path)
    assert value['dropped_active_operations'] == 1
    parent, = value['server_operations']
    assert parent['operation'] == 'prefix' and parent['current_calls'] == parent['SQL_calls'] == 1
    assert parent['projection_calls'] == parent['projection_spans_dropped'] == 1
    assert value['active_client_requests'] == value['active_server_operations'] == []


def test_interrupted_projection_preserves_parent_and_child_as_incomplete(tmp_path):
    body = PROJECTION_FUNCTIONS + r'''
import os
def request_http():prefix(lambda:projection(lambda:os._exit(0)))
request_http()
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    assert value['responses'] == value['server_operations'] == []
    assert len(value['active_client_requests']) == 1
    assert [r['operation'] for r in value['active_server_operations']] == ['prefix', 'prefix_projection']
    assert all('finished_monotonic_ns' not in r and 'status' not in r for r in value['active_server_operations'])


def test_concurrent_projection_children_keep_their_own_parent(tmp_path):
    body = PROJECTION_FUNCTIONS + r'''
import threading
barrier=threading.Barrier(2)
def work(n):
 def action():
  barrier.wait(2)
  for _ in range(n):current();source();execute('controlled_secret_never_export')
 prefix(lambda:projection(action))
threads=[threading.Thread(target=work,args=(n,)) for n in (1,2)]
for thread in threads:thread.start()
for thread in threads:thread.join(3)
assert not any(thread.is_alive() for thread in threads)
'''
    result = subprocess.run(command(tmp_path, body), capture_output=True, timeout=5)
    assert result.returncode == 0, result.stderr.decode()
    value = read(tmp_path)
    rows = value['server_operations']
    parents = [r for r in rows if r['operation'] == 'prefix']
    children = [r for r in rows if r['operation'] == 'prefix_projection']
    assert len(parents) == len(children) == 2
    for parent in parents:
        child, = [c for c in children if c['parent_started_monotonic_ns'] == parent['started_monotonic_ns']]
        assert child['SQL_calls'] == parent['SQL_calls'] == child['current_calls'] == parent['current_calls']
    assert value['active_server_operations'] == []
