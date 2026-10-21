"""Bound the closed CO2 projection/current-query verification on hosted CI."""
import ctypes
import fcntl
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
QUERY_PROGRESS = ['test_none_unstarted_cancelled_and_missing_have_no_calculation',
    'test_checkpoint_original_counts_utc_first_time_survives_heartbeat_and_new_attempt',
    'test_checkpoint_unconfirmed_descendant_and_real_lock_are_unavailable',
    'test_terminal_original_result_success_or_numerical_hold_and_fresh_reader',
    'test_rights_readonly_scopes_and_late_revocation_fail_closed',
    'test_corrupt_appended_checkpoint_event_rejects_without_mutation']
QUERY_FENCES = ['test_binding_bad_ids_and_dependency_drift_are_rejected',
    'test_rights_job_change_during_read_is_pending_without_partial_response',
    'test_source_rights_revoked_during_serialization_rejects_response',
    'test_terminal_bundle_faults_reject_without_mutation',
    'test_checkpoint_lock_is_released_during_followup_checks',
    'test_checkpoint_changed_after_snapshot_never_returns_partial_response',
    'test_checkpoint_directory_identity_survives_the_unlocked_interval']
PREFIX_CORE = ['test_missing_unstarted_scope_and_readonly_contract',
    'test_running_original_pages_and_sparse_utc',
    'test_ready_has_no_stored_sample_or_invented_time',
    'test_dense_64_row_page_terminal_checkpoint_before_publication',
    'test_terminal_uses_existing_result_and_prefix_is_closed']
PREFIX_FENCES = ['test_signed_private_HEAD_rollback_during_read_is_rejected',
    'test_actual_audit_immutability_and_returned_event_faults',
    'test_older_accepted_after_private_and_confirmed_tails_retry_and_fresh',
    'test_signed_rollback_behind_latest_acceptance_rejects_old_selector',
    'test_current_scopes_review_rights_and_late_revocation',
    'test_late_farm_registration_denial_still_blocks_prefix',
    'test_cancel_request_and_ack_close_prefix_without_result',
    'test_selector_bounds_missing_unaccepted_and_actual_lock',
    'test_original_signed_head_proof_commit_page_tampering_rejected',
    'test_selected_page_tampered_after_read_is_rejected_before_serialized_response']
PREFIX_SCOPES = ('co2-prefix-core', 'co2-prefix-fences', 'co2-prefix-concurrent')


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
        'backend/tests/test_api_runtime.py', 'backend/tests/test_operator_config.py',
        'backend/tests/test_crop_greenhouse_co2_execution.py',
        'backend/tests/test_crop_greenhouse_co2_execution_store.py',
        'backend/tests/test_crop_greenhouse_co2_execution_checkpoint.py',
        'backend/tests/test_crop_greenhouse_co2_execution_checkpoint_store.py',
        'backend/tests/test_crop_greenhouse_co2_execution_worker_control.py',
        'backend/tests/test_crop_greenhouse_co2_execution_worker.py',
        'backend/tests/test_co2_deterministic_work.py',
        'backend/tests/test_solar_deterministic_work.py',
        'backend/tests/test_crop_greenhouse_co2_execution_fresh.py',
        'backend/tests/test_crop_greenhouse_co2_result_store.py',
        'backend/tests/test_crop_greenhouse_co2_server_custody.py',
        'backend/tests/test_owned_research_process_scope.py',
        'research/owned-research-process-scope.py',
        'backend/tests/test_crop_greenhouse_co2_execution_query_control.py',
        'backend/tests/test_crop_greenhouse_co2_execution_query.py',
        'backend/tests/test_crop_greenhouse_co2_execution_query_fresh.py',
        'backend/tests/test_crop_greenhouse_co2_prefix_control.py',
        'backend/tests/test_crop_greenhouse_co2_prefix.py',
        'backend/tests/test_crop_greenhouse_co2_prefix_concurrent.py',
        'backend/tests/test_crop_greenhouse_co2_prefix_fresh.py',
        'backend/tests/test_crop_greenhouse_co2_farm_binding.py',
        'backend/tests/test_crop_greenhouse_co2_input_evidence.py',
        'backend/tests/test_crop_greenhouse_co2_continuation.py',
        'backend/tests/test_crop_greenhouse_co2_program.py',
        'fixtures/crop-greenhouse-co2-program-reference-cases-v1.json',
        'fixtures/crop-growth-reference-parameters-v1.json',
        'fixtures/crop-fruit-cohort-reference-parameters-v1.json',
        'fixtures/crop-fruit-transport-reference-parameters-v1.json',
        'fixtures/crop-canopy-exchange-reference-parameters-v1.json',
        'backend/tests/test_crop_solar_custody_file_locks.py')]
    return {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}


def supervise(directory):
    assert os.environ.get('GITHUB_ACTIONS') == 'true', 'hosted only; preserve WSL previews'
    mode = os.environ.get('OSSF_CO2_VERIFICATION_SCOPE', 'co2-result-projection')
    assert mode in ('co2-result-projection', 'co2-current-query', 'co2-http', 'co2-runtime', 'co2-admission', 'co2-checkpoint', 'co2-worker-core', 'co2-worker-consumer', 'co2-execution-query', 'co2-execution-query-fences', *PREFIX_SCOPES)
    prefix = mode in PREFIX_SCOPES
    current = mode == 'co2-current-query'
    runtime = mode == 'co2-runtime'
    admission = mode == 'co2-admission'
    checkpoint = mode == 'co2-checkpoint'
    worker = mode == 'co2-worker-core'
    consumer = mode == 'co2-worker-consumer'
    query_fences = mode == 'co2-execution-query-fences'
    query = mode in ('co2-execution-query', 'co2-execution-query-fences')
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
    if prefix:
        sample_lock = directory/'database-sample-lock.private'; sample_lock.touch(mode=0o600)
        env['OSSF_OWNED_DATABASE_SAMPLE_LOCK'] = str(sample_lock)
        raw_sample = scope.sample
        def sampled():
            with sample_lock.open('rb') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX)
                return raw_sample()
        scope.sample = sampled
        for name, variable in (('prefix', 'OSSF_CO2_PREFIX_EVIDENCE'), ('prefix-fresh', 'OSSF_CO2_EXECUTION_EVIDENCE')):
            target = directory/name; target.mkdir(mode=0o700); env[variable] = str(target)
    for key in ('PYTEST_ADDOPTS', 'PYTEST_PLUGINS', 'PGPASSWORD', 'PGPASSFILE', 'PGSERVICE', 'PGSERVICEFILE'):
        env.pop(key, None)
    if admission or checkpoint or worker:
        name = 'worker' if worker else 'checkpoint' if checkpoint else 'admission'
        target = directory/name; target.mkdir(mode=0o700)
        env['OSSF_CO2_'+name.upper()+'_EVIDENCE'] = str(target)
    if consumer:
        target = directory/'consumer'; target.mkdir(mode=0o700)
        env['OSSF_CO2_EXECUTION_EVIDENCE'] = str(target)
    if query:
        target = directory/'execution-query'; target.mkdir(mode=0o700)
        env['OSSF_CO2_EXECUTION_QUERY_EVIDENCE'] = str(target)
        target = directory/'query-fresh'; target.mkdir(mode=0o700)
        env['OSSF_CO2_EXECUTION_EVIDENCE'] = str(target)
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
    if admission:
        targets = ['tests/test_crop_greenhouse_co2_execution.py', 'tests/test_crop_greenhouse_co2_execution_store.py']
    if checkpoint:
        targets = ['tests/test_crop_greenhouse_co2_execution_checkpoint.py', 'tests/test_crop_greenhouse_co2_execution_checkpoint_store.py']
    if worker:
        targets = ['tests/test_crop_greenhouse_co2_execution_worker_control.py', 'tests/test_crop_greenhouse_co2_execution_worker.py']
    if consumer:
        targets = ['tests/test_co2_deterministic_work.py', 'tests/test_solar_deterministic_work.py',
            'tests/test_crop_greenhouse_co2_execution_fresh.py',
            'tests/test_owned_research_process_scope.py::test_real_libc_pidfd_signal0_and_owned_cleanup_preserve_protected_tree']
    if query:
        targets = ['tests/test_crop_greenhouse_co2_execution_query.py::'+name for name in (QUERY_FENCES if query_fences else QUERY_PROGRESS)]
        targets += ['tests/test_crop_greenhouse_co2_execution_query_fresh.py'] if query_fences else ['tests/test_crop_greenhouse_co2_execution_query_control.py']
    if prefix:
        if mode == 'co2-prefix-concurrent':
            targets = ['tests/test_crop_greenhouse_co2_prefix_concurrent.py', 'tests/test_crop_greenhouse_co2_prefix_fresh.py']
        else:
            targets = ['tests/test_crop_greenhouse_co2_prefix.py::'+name
                for name in (PREFIX_CORE if mode == 'co2-prefix-core' else PREFIX_FENCES)]
            if mode == 'co2-prefix-core': targets += ['tests/test_crop_greenhouse_co2_prefix_control.py']
    expected = (11 if query_fences else 24) if query else 37 if consumer else 20 if worker else 26 if checkpoint else 17 if admission else 177 if runtime else 215 if http else 11 if current else 39
    if prefix: expected = {'co2-prefix-core': 13, 'co2-prefix-fences': 10, 'co2-prefix-concurrent': 8}[mode]
    plans = [('tests', [sys.executable, '-B', '-m', 'pytest', *targets,
        '-q', '-rf', '--tb=short', '--maxfail=1', '--basetemp', str(directory/'pytest')])]
    for status in (() if current or http or admission or checkpoint or worker or consumer or query or prefix else ('completed', 'hold')):
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
                if prefix:
                    folder = directory/'prefix'
                    concurrent = mode == 'co2-prefix-concurrent'
                    cleanup = 'database-cleanup-concurrent.json' if concurrent else 'database-cleanup.json'
                    assert json.loads((folder/cleanup).read_bytes()) == {'schemas': 0, 'roles': 0}
                    records = [json.loads(path.read_bytes()) for path in folder.glob('*.json') if path.name != cleanup]
                    assert len(records) == (7 if concurrent else 6 if mode == 'co2-prefix-core' else 10)
                    for record in records:
                        calls = next((record[key] for key in ('calls', 'read_calls', 'parent_product_query_calls', 'product_query_calls') if key in record), None)
                        assert calls and len(calls) == 31 and not any(calls.values())
                    if mode == 'co2-prefix-core':
                        running = json.loads((folder/'running.json').read_bytes())
                        assert running['actual_scram'] and running['original_values_and_UTC'] and running['DB_unchanged'] and running['FD_unchanged']
                        dense = json.loads((folder/'dense.json').read_bytes())
                        assert dense['original_sample_count'] == 65 and dense['page_counts'] == [64, 1]
                        assert dense['same_original_values_UTC'] and dense['no_result_publication']
                        assert all(n <= 2*1024**2 for n in dense['page_bytes'])
                    elif mode == 'co2-prefix-fences':
                        audit = json.loads((folder/'selected-previous-event-changes.json').read_bytes())
                        assert len(audit['actual_audit_trigger_rejections']) == len(audit['reader_rejected']) == 6
                        assert audit['fault_actor_used_password'] and audit['fault_actor_require_auth'] == 'scram-sha-256'
                        assert audit['fault_actor_owner_session_verified'] and audit['temporary_fault_actor_removed_before_query']
                        assert audit['actual_DB_event_rows_unchanged']
                        late = json.loads((folder/'late-page.json').read_bytes())
                        assert late['selected_page_changed_after_successful_read_rejected'] and late['original_owned_page_restored']
                    else:
                        for confirmed in (False, True):
                            record = json.loads((folder/('concurrent-original-'+str(confirmed)+'.json')).read_bytes())
                            assert record['actor']['actual_scram'] and record['same_original_page_binary64_UTC']
                            assert record['actor_publication_is_precomputed_original_not_new_calculation'] and record['after_projection_witness_checked']
                        assert json.loads((directory/'prefix-fresh/cleanup-normal.json').read_bytes()) == {'schemas': 0, 'roles': 0}
                        record = json.loads((directory/'prefix-fresh/fresh-normal.json').read_bytes())
                        read = record['fresh_reader']
                        assert record['same_owned_database_and_original_files'] and record['sequential_processes']
                        assert read['actual_scram'] and len(read['calls']) == 31 and not any(read['calls'].values())
                        assert read['original_page_values_UTC_and_first_confirmation'] and read['actual_producer_tail_not_mixed_into_old_selector']
                        assert read['owner_bound_after_projection_checked'] and read['review_withdrawal_denied']
                elif query:
                    folder = directory/'execution-query'
                    assert json.loads((folder/'database-cleanup.json').read_bytes()) == {'schemas': 0, 'roles': 0}
                    records = [json.loads(path.read_bytes()) for path in folder.glob('*.json') if path.name != 'database-cleanup.json']
                    assert len(records) == 9
                    for record in records:
                        calls = record.get('calls', record.get('query_calls'))
                        assert calls and not any(calls.values())
                        assert record.get('query_database_unchanged') is True or (record.get('separate_actor_cancel') == 1 and record.get('pending_no_partial_response') is True)
                    if query_fences:
                        for case in ('normal', 'hold'):
                            assert json.loads((directory/'query-fresh'/('cleanup-'+case+'.json')).read_bytes()) == {'schemas': 0, 'roles': 0}
                            record = json.loads((directory/'query-fresh'/('fresh-'+case+'.json')).read_bytes())
                            read = record['fresh_reader']
                            assert record['sequential_processes'] and read['actual_scram'] and not any(read['calls'].values())
                            assert read['same_original_DTO_except_observation_time'] and read['original_first_confirmation_UTC']
                            assert read['readonly_without_create_execute_write'] and read['review_withdrawal_denied']
                elif consumer:
                    folder = directory/'consumer'
                    assert len(list(folder.glob('*.json'))) == 6
                    for case in ('normal', 'hold', 'crash'):
                        assert json.loads((folder/('cleanup-'+case+'.json')).read_bytes()) == {'schemas': 0, 'roles': 0}
                        record = json.loads((folder/('fresh-'+case+'.json')).read_bytes())
                        actual, reader = record['worker'], record['fresh_reader']
                        assert record['same_owned_database_and_original_files'] and record['sequential_processes']
                        assert not any(record['admission_calls'].values())
                        assert actual['actual_scram'] and actual['automatic_discovery'] and actual['unselected_queued']
                        assert actual['original_result_progress_equal'] and actual['calls']['CLI'] == 0
                        assert actual['event']['state'] == ('hold' if case == 'hold' else 'succeeded')
                        assert reader['actual_scram'] and reader['original_bytes_pages_UTC'] and reader['review_revocation_rejected']
                        assert not any(reader['calls'].values())
                        if case == 'crash':
                            assert record['actual_kill_exit'] == -9 and record['no_prefix_reintegration']
                            assert record['pidfd_backend'] in ('python', 'libc')
                            assert record['killed']['calls']['step'] + actual['calls']['step'] == 16
                            assert actual['event']['attempt'] == 2 and actual['calls']['start'] == 0
                            assert not any(actual['adopted'][0]['calls'].values())
                elif worker:
                    folder = directory/'worker'
                    assert json.loads((folder/'database-cleanup.json').read_bytes()) == {'schemas': 0, 'roles': 0}
                    records = [json.loads(path.read_bytes()) for path in folder.glob('*.json') if path.name != 'database-cleanup.json']
                    assert len(records) == 11 and all(record['actual_scram'] and record['scope'] == 'worker_core_only'
                        and record['independent_fresh_reader'] is False and record['actual_SIGKILL'] is False for record in records)
                    for status in ('completed', 'hold'):
                        record = json.loads((folder/('normal-'+status+'.json')).read_bytes())
                        assert record['same_original_checkpoint_rows_all_states_utc']
                        assert len(record['read_calls']) == 17 and not any(record['read_calls'].values())
                        assert record['calls']['CLI'] == 0 and record['calls']['step'] == 16
                        assert record['counts'] == {'registry': 1, 'publication': int(status == 'completed'), 'outcome': 1, 'result_links': 1}
                    expiry = json.loads((folder/'expiry.json').read_bytes())
                    assert not any(expiry['first_adoption_calls_zero'].values())
                    assert expiry['first_calls']['step'] + expiry['remaining_calls']['step'] == 16
                    assert expiry['remaining_calls']['start'] == 0 and expiry['final_attempt'] == 2
                    for name in ('rollback-event', 'rollback-final_update', 'late-scope', 'late-rights', 'late-resolver', 'late-after-update-scope'):
                        assert not any(json.loads((folder/(name+'.json')).read_bytes())['calls'].values())
                elif admission or checkpoint:
                    folder = directory/('checkpoint' if checkpoint else 'admission')
                    assert json.loads((folder/'database-cleanup.json').read_bytes()) == {'schemas': 0, 'roles': 0}
                    records = [json.loads(path.read_bytes()) for path in folder.glob('*.json') if path.name != 'database-cleanup.json']
                    assert len(records) == 13 and all(value['actual_scram'] and len(value['calls']) == 17 and not any(value['calls'].values()) for value in records)
                elif http:
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
                counts_record.update({'control': 7 if mode == 'co2-prefix-core' else 0,
                    'actual_SCRAM': 7 if mode == 'co2-prefix-concurrent' else 6 if mode == 'co2-prefix-core' else 10,
                    'actual_independent_SCRAM': 1 if mode == 'co2-prefix-concurrent' else 0} if prefix else
                    {'control': 0 if query_fences else 15, 'actual_SCRAM': 9, 'actual_independent_SCRAM': 2 if query_fences else 0} if query else
                    {'new_consumer_control': 17, 'legacy_solar_control': 14, 'actual_independent_SCRAM': 3, 'pidfd_libc_regression': 3} if consumer else
                    {'control_contract': 9, 'actual_SCRAM': 11} if worker else
                    {'control_contract': 13 if checkpoint else 4, 'actual_SCRAM': 13} if admission or checkpoint else
                    {'control_contract': 173, 'actual_SCRAM_TLS': 4} if runtime else
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
        'current_query_tested': current or http, 'HTTP_tested': http, 'runtime_tested': runtime, 'admission_tested': admission, 'checkpoint_tested': checkpoint, 'worker_core_tested': worker,
        'execution_query_tested': query, 'execution_query_fences_tested': query_fences,
        'confirmed_prefix_tested': mode if prefix else False,
        'worker_discovery_independent_restart': 'tested' if consumer else 'not_tested', 'worker_browser': 'not_tested', 'G0_G4': 'not_assessed'})
    print(json.dumps({'accepted_hosted_tests': expected, 'mode': mode,
        'fresh_registered_readers': (1 if mode == 'co2-prefix-concurrent' else 0) if prefix else (2 if query_fences else 0) if query else 3 if consumer else 0 if http or admission or checkpoint or worker else 2,
        'native_HTTPS_readers': 4 if runtime else 2 if http else 0,
        'WSL_capacity_accepted': False, 'new_CO2_deployed': False}))


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'fresh': fresh(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        assert len(sys.argv) == 2
        supervise(Path(sys.argv[1]).resolve())
