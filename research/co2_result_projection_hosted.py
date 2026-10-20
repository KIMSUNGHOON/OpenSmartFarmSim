"""Bound the closed CO2 projection/current-query verification on hosted CI."""
import ctypes
from datetime import datetime
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time

RUNTIME_TARGETS = ['tests/test_crop_greenhouse_co2_runtime.py',
 'tests/test_crop_greenhouse_co2_runtime_native.py',
 'tests/test_crop_greenhouse_solar_runtime.py',
 'tests/test_crop_greenhouse_solar_runtime_native.py',
 'tests/test_crop_greenhouse_co2_result_roles.py::test_flag_is_explicit_exact_boolean_and_defaults_false',
 'tests/test_crop_greenhouse_co2_result_roles.py::test_existing_operator_versions_accept_only_missing_or_false_co2_flag',
 'tests/test_crop_greenhouse_co2_result_roles.py::test_existing_runtime_config_cannot_enable_co2_without_assembly',
 'tests/test_api_runtime.py::test_configuration_rejects_invalid_or_unbound_operating_values',
 'tests/test_api_runtime.py::test_config_hides_private_values_and_is_frozen',
 'tests/test_api_runtime.py::test_missing_dependencies_are_rejected',
 'tests/test_api_runtime.py::test_assembly_rejects_untyped_config_without_provider_calls',
 'tests/test_api_runtime.py::test_authored_option_pair_and_profile_fail_before_source_factory',
 'tests/test_api_runtime.py::test_job_grant_audit_flag_rejects_nonboolean_or_unbound_configuration']

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]


def save(path, value):
    with path.open('x') as output:
        os.fchmod(output.fileno(), 0o400)
        json.dump(value, output, sort_keys=True, indent=2)


def fresh(pack_path, destination):
    import psycopg
    import pytest
    from app import api_crop_greenhouse_co2_replay as public
    import test_crop_greenhouse_co2_result_store as registered
    raw = pack_path.read_bytes(); assert len(raw) <= 8*1024**2
    data = json.loads(raw); record = data['record']
    assert data['captured_from_actual_SCRAM_record'] is True
    record['payload_raw'] = record['payload_raw'].encode()
    record['progress_raw'] = record['progress_raw'].encode()
    record['recorded_at'] = datetime.fromisoformat(record['recorded_at'])
    before = len(os.listdir('/proc/self/fd')); responses = {}
    with pytest.MonkeyPatch.context() as patch:
        calls = registered.producer.reference.forbid(patch); calls['SQL_calls'] = 0
        def forbidden(*args, **kwargs):
            calls['SQL_calls'] += 1
            raise AssertionError('projection-only fresh reader attempted SQL')
        patch.setattr(psycopg.Connection, 'execute', forbidden)
        for view in ('summary', 'samples', 'events'):
            value = public.project_co2_result(record, data['terminal'], source_program=data['program'],
                view=view, page=None if view == 'summary' else data['pages'][view],
                limit=None if view == 'summary' else 64 if view == 'samples' else 8)
            body = public._public_bytes(value)
            responses[view] = {'bytes': len(body), 'sha256': sha256(body).hexdigest()}
        assert responses == data['expected'] and all(value == 0 for value in calls.values())
    after = len(os.listdir('/proc/self/fd')); assert before == after
    save(destination, {'fresh_exec': True, 'responses': responses, 'same_original_wire_SHA': True,
        'captured_from_actual_SCRAM_record': True, 'calls': calls, 'FD_before_after': [before, after],
        'input_pack_sha256': sha256(raw).hexdigest(), 'scope': 'projection_only_no_current_DB_authorization',
        'G0_G4': 'not_assessed'})


def pins():
    paths = list((ROOT/'backend/app').glob('*.py')) + [ROOT/name for name in (
        'backend/tests/test_api_crop_greenhouse_co2_replay.py',
        'backend/tests/test_api_crop_greenhouse_co2_replay_store.py',
        'fixtures/synthetic-co2-result-projection-template-v1.json',
        'research/co2_result_projection_hosted.py')]
    paths += [p for p in (ROOT/'backend/tests').glob('test_crop_greenhouse_co2_current_query*.py')]
    paths += [ROOT/name for name in (
        'backend/tests/test_api_crop_greenhouse_co2_route.py',
        'backend/tests/test_api_crop_greenhouse_co2_native.py',
        'backend/tests/test_api_crop_greenhouse_solar_route.py',
        'backend/tests/test_api_crop_greenhouse_solar_native.py',
        'backend/tests/test_crop_greenhouse_solar_current_fresh.py',
        'backend/tests/test_api_openapi.py', 'contracts/openapi-v1.json',
        'research/artifacts/co2-route-openapi-baseline-20261021.json',
        'backend/tests/test_crop_greenhouse_co2_runtime.py',
        'backend/tests/test_crop_greenhouse_co2_runtime_native.py',
        'backend/tests/test_crop_greenhouse_solar_runtime.py',
        'backend/tests/test_crop_greenhouse_solar_runtime_native.py',
        'backend/tests/test_crop_greenhouse_co2_result_roles.py',
        'backend/tests/test_api_runtime.py', 'backend/tests/test_operator_config.py')]
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def supervise(directory):
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'hosted only; preserve WSL previews'
    mode = os.environ.get('OSSF_CO2_VERIFICATION_SCOPE', 'co2-result-projection')
    assert mode in ('co2-result-projection', 'co2-current-query', 'co2-http', 'co2-runtime')
    current = mode == 'co2-current-query'
    runtime = mode == 'co2-runtime'
    http = mode in ('co2-http', 'co2-runtime')
    directory.mkdir(mode=0o700)
    spec = importlib.util.spec_from_file_location('co2_projection_scope', ROOT/'research/owned-research-process-scope.py')
    owned = importlib.util.module_from_spec(spec); spec.loader.exec_module(owned)
    assert ctypes.CDLL(None).prctl(36, 1, 0, 0, 0) == 0
    scope = owned.OwnedProcessScope(); before = len(os.listdir('/proc/self/fd'))
    original = pins(); started = time.monotonic(); child = None
    single = combined = samples = 0; reason = None; exits = {}
    temporary = directory/'owned-tmp'; temporary.mkdir(mode=0o700)
    env = dict(os.environ, TMPDIR=str(temporary), PYTHONDONTWRITEBYTECODE='1', PYTHONMALLOC='malloc',
        MALLOC_ARENA_MAX='2', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
        OSSF_TEST_PG_SHARED_BUFFERS_MIB='4', PGOPTIONS='-c work_mem=64kB -c jit=off',
        OSSF_JOINT_PREFIX_SDK_EVIDENCE=str(directory))
    for key in ('PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PGPASSWORD', 'PGPASSFILE', 'PGSERVICE', 'PGSERVICEFILE'):
        env.pop(key, None)
    if runtime:
        env['OSSF_CO2_RUNTIME_EVIDENCE'] = str(directory/'http')
    if http:
        for name, variable in (('http', 'OSSF_CO2_HTTP_EVIDENCE'), ('legacy-solar', 'OSSF_SOLAR_HTTP_EVIDENCE')):
            target = directory/name; target.mkdir(mode=0o700); env[variable] = str(target)
    targets = ['tests/test_crop_greenhouse_co2_current_query.py', 'tests/test_crop_greenhouse_co2_current_query_store.py'] if current else [
        'tests/test_api_crop_greenhouse_co2_replay.py', 'tests/test_api_crop_greenhouse_co2_replay_store.py']
    if http:
        targets = ['tests/test_api_crop_greenhouse_co2_route.py', 'tests/test_api_crop_greenhouse_co2_native.py',
            'tests/test_api_crop_greenhouse_solar_route.py', 'tests/test_api_openapi.py']
    if runtime: targets = RUNTIME_TARGETS
    expected = 177 if runtime else 215 if http else 11 if current else 39
    plans = [('tests', [sys.executable, '-B', '-m', 'pytest', *targets,
        '-q', '-rf', '--tb=short', '--maxfail=1', '--basetemp', str(directory/'pytest')])]
    for status in (() if current or http else ('completed', 'hold')):
        plans.append(('fresh-'+status, [sys.executable, '-B', str(Path(__file__).resolve()), 'fresh',
            str(directory/('co2-projection-store-'+status+'-fresh-pack.private.json')),
            str(directory/('fresh-'+status+'.json'))]))
    try:
        for phase, argv in plans:
            log = directory/(phase+'.private.log')
            with log.open('xb') as output:
                os.fchmod(output.fileno(), 0o600)
                child = subprocess.Popen(argv, cwd=ROOT/'backend', env=env, stdin=subprocess.DEVNULL,
                    stdout=output, stderr=subprocess.STDOUT)
                while child.poll() is None:
                    rss = scope.sample(); samples += 1
                    single = max(single, max(rss.values(), default=0)); combined = max(combined, sum(rss.values()))
                    if single > 512*1024**2 or combined > 1024**3: reason = 'RSS_limit'
                    elif time.monotonic()-started > 600: reason = 'wall_limit'
                    elif os.fstat(output.fileno()).st_size > 4*1024**2: reason = 'log_limit'
                    if reason: break
                    time.sleep(.25)
            if reason: break
            exits[phase] = child.returncode
            if child.returncode:
                lines = log.read_text(errors='replace').splitlines()
                save(directory/'failure.json', {'phase': phase, 'exit': child.returncode,
                    'log_sha256': sha256(log.read_bytes()).hexdigest(),
                    'failed_nodes': [line.split(' - ', 1)[0] for line in lines if line.startswith('FAILED ')]})
                break
            if phase == 'tests':
                text = log.read_text(errors='replace')
                assert re.search(rf'\b{expected} passed\b', text) and ' skipped' not in text
                if http:
                    for status in ('completed', 'hold'):
                        assert json.loads((directory/'http'/('database-cleanup-'+status+'.json')).read_bytes()) == {'schemas': 0, 'roles': 0}
                        native = json.loads((directory/'http'/('native-'+status+'.json')).read_bytes())
                        assert native['actual_scram'] and native['verified_TLS'] and native['original_response_bytes_equal']
                        assert all(value == 0 for value in native['calls'].values())
                    assert len(json.loads((directory/'http/native-completed.json').read_bytes())['withdrawals_withheld']) == 12
                    if runtime:
                        for status in ('completed', 'hold'):
                            for folder in ('http', 'legacy-solar'):
                                native = json.loads((directory/folder/('native-'+status+'.json')).read_bytes())
                                assert native['runtime_assembled'] and native['actual_scram'] and native['verified_TLS']
                                assert native['original_response_bytes_equal'] and native['protected_files_preserved']
                                assert native['legacy_custody_unused'] and not any(native['calls'].values())
                                assert len(native['misassemblies_denied']) == (9 if status == 'completed' else 0)
                                assert native['test_owner_grant_mutations'] == (2 if status == 'completed' else 0)
                                assert json.loads((directory/folder/('database-cleanup-'+status+'.json')).read_bytes()) == {'schemas': 0, 'roles': 0}
                        assert json.loads((directory/'co2-roles-database-cleanup.json').read_bytes()) == {'schemas': 0, 'roles': 0}

                else:
                    cleanup = 'co2-current-query-database-cleanup.json' if current else 'co2-projection-store-database-cleanup.json'
                    assert json.loads((directory/cleanup).read_bytes()) == {'schemas': 0, 'roles': 0}
                if current:
                    for status in ('completed', 'hold'):
                        result = json.loads((directory/('co2-current-query-fresh-'+status+'.json')).read_bytes())
                        assert result['actual_scram'] and result['current_DB_authorization'] and result['actual_exit'] == 0
                        assert all(value == 0 for value in result['calls'].values())
                counts_record = {'passed': expected, 'skipped': 0, 'mode': mode,
                    'pytest_log_sha256': sha256(log.read_bytes()).hexdigest()}
                counts_record.update({'control_contract': 173, 'actual_SCRAM_TLS': 4} if runtime else
                    {'pure': 213 if http else 5 if current else 37, 'actual_SCRAM': 6 if current else 2})
                save(directory/'tests.json', counts_record)
    finally:
        scope.signal_owned(signal.SIGTERM)
        if child is not None and child.poll() is None:
            try: child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                scope.signal_owned(signal.SIGKILL); child.wait(timeout=5)
        deadline = time.monotonic()+10
        while scope.remaining() and time.monotonic() < deadline: time.sleep(.1)
        if scope.remaining(): scope.signal_owned(signal.SIGKILL)
        while True:
            try:
                if os.waitpid(-1, os.WNOHANG)[0] == 0: break
            except ChildProcessError: break
        remaining = [i._asdict() for i in scope.remaining()]
        passfiles = sum(1 for _ in directory.rglob('*.pgpass'))
        temporary_entries = len(list(temporary.iterdir()))
        if not remaining:
            for path in (directory/'pytest', temporary):
                if path.exists(): shutil.rmtree(path)
        after = len(os.listdir('/proc/self/fd')); preserved = pins() == original
        result = {'phase_exits': exits, 'reason': reason, 'wall_seconds': time.monotonic()-started,
            'single_PID_peak_RSS_bytes': single, 'combined_peak_RSS_bytes': combined,
            'RSS_samples': samples, 'sample_interval_seconds': .25, 'FD_before_after': [before, after],
            'owned_non_zombie_remaining': remaining, 'passfiles_before_cleanup': passfiles,
            'temporary_entries_before_cleanup': temporary_entries, 'source_preserved': preserved,
            'hosted_only': True, 'mode': mode, 'WSL_capacity_accepted': False, 'new_CO2_deployed': False,
            'actual_crop_Runs': 0, 'G0_G4': 'not_assessed'}
        save(directory/'resource.json', result)
    assert reason is None and exits == {phase: 0 for phase, _ in plans}
    assert before == after and not remaining and passfiles == temporary_entries == 0 and preserved
    save(directory/'provenance.json', {'source_commit': os.environ['GITHUB_SHA'],
        'run_id': os.environ['GITHUB_RUN_ID'], 'run_attempt': os.environ['GITHUB_RUN_ATTEMPT'],
        'source_SHA256': original, 'python': sys.version, 'test_scope': mode,
        'current_query_tested': current or http, 'HTTP_tested': http, 'runtime_tested': runtime, 'worker_browser': 'not_tested', 'G0_G4': 'not_assessed'})
    print(json.dumps({'accepted_hosted_tests': expected, 'mode': mode,
        'fresh_registered_readers': 0 if http else 2, 'native_HTTPS_readers': 4 if runtime else 2 if http else 0,
        'WSL_capacity_accepted': False, 'new_CO2_deployed': False}))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'fresh': fresh(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        assert len(sys.argv) == 2
        supervise(Path(sys.argv[1]).resolve())
