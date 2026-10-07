"""Publish actual signed synthetic farm calculations through SCRAM, without forecasts."""
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
from time import perf_counter

from psycopg import sql
import pytest

from app import crop_cycle_calculation_result_store as storage
from app import crop_cycle_calculation_result_schema as schema
from app import crop_cycle_calculation_server_custody as custody
from app import crop_cycle_calculation_context as engine
from app.thermal_run_store import _canonical
from app.runtime_roles import audit_runtime_roles
from app.crop_result_store import _intent_lock_key
from test_crop_cycle_calculation_server_custody_farms import server_setup, OwnInputResolver, KEY, BUDGET
from test_crop_cycle_calculation_farm_binding import setup as bound_setup, final_database_cleanup
from test_crop_cycle_farm_binding import counts as original_counts
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope as original_login_scope

DB_KEY = b'own-verified-result-db-key-00000001'
pytestmark = pytest.mark.parametrize('original_login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}], indirect=True)


@pytest.fixture
def login_scope(original_login_scope, request):
    base, policy, dsns = original_login_scope
    enabled = getattr(request, 'param', True)
    current = replace(policy, crop_cycle_calculation_result_storage=enabled)
    with base.connect() as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        schema.install_calculation_cycle_crop_result_schema(conn, policy.schema)
        if enabled:
            conn.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(
                sql.Identifier(policy.schema, schema.TABLE), sql.Identifier(policy.roles['authority'])))
    with base.connect() as conn: audit_runtime_roles(conn, current)
    return base, current, dsns


def counts(binding):
    with binding.jobs.connect() as conn:
        n = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(binding.jobs._table(schema.TABLE))).fetchone()['n']
    return original_counts(binding) + (n,)


def save_reference(name, value):
    root = os.environ.get('OSSF_CALCULATION_PUBLICATION_EVIDENCE')
    if root:
        with (Path(root)/name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.write('\n'); f.flush(); os.fsync(f.fileno())


def fresh(store):
    old = store.server
    server = custody.CalculationServerCustody(old.binding, old.directory,
        input_resolver=old.input_resolver, integrity_key=old.integrity_key)
    return storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)


def forbid_math(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('publication/read ran crop equations')
    monkeypatch.setattr(engine, 'advance_chunk', forbidden)
    monkeypatch.setattr(engine.legacy, 'advance_chunk', forbidden)
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)


def fork_read(store, result_id, farm, queue):
    try:
        restarted = fresh(store)
        queue.put({'record': restarted.get('tenant-1', result_id, farm),
            'page': restarted.page('tenant-1', result_id, farm, 'samples', 0, 64)})
    except Exception as exc: queue.put({'error': type(exc).__name__})


def test_signed_calculation_publication_roundtrip_retry_summary_and_fork_without_rhs(server_setup, monkeypatch):
    server, raw, rights, principal, expected = server_setup
    started = perf_counter(); progress = server.advance('tenant-1', raw, budget=BUDGET)
    calculate_seconds = perf_counter()-started; before = counts(server.binding)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
    forbid_math(monkeypatch); measured = {}; farm = json.loads(raw)['farm']
    started = perf_counter(); record = store.put('tenant-1', raw); measured['put'] = perf_counter()-started
    packet = json.loads(record['payload_raw'])
    assert packet['schema_version'] == 'crop-cycle-verified-result-v1'
    assert packet['policies']['server_progress'] == json.loads(progress)
    assert packet['artifact']['status'] == 'completed' and packet['artifact']['steps'] == 120
    assert packet['binding']['input']['input_validation']['context_sha256'] == json.loads(progress)['context_sha256']
    assert counts(server.binding) == (*before[:4], 1) and before[2:] == (0, 0, 0)
    started = perf_counter(); assert store.put('tenant-1', raw) == record; measured['retry'] = perf_counter()-started
    restarted = fresh(store)
    started = perf_counter(); assert restarted.get('tenant-1', record['result_id'], farm) == record
    measured['get'] = perf_counter()-started
    for kind, limit in (('samples', 64), ('events', 8)):
        started = perf_counter(); page = restarted.page('tenant-1', record['result_id'], farm, kind, 0, limit)
        measured[kind] = perf_counter()-started
        assert page['next'] == page['total'] and _canonical(page['records']) == _canonical(expected[kind])
    started = perf_counter(); summary = restarted.summary('tenant-1', record['result_id'], farm)
    measured['summary'] = perf_counter()-started
    assert summary['status'] == 'completed' and summary['manifest']['engine_version'] == engine.VERSION
    context = multiprocessing.get_context('fork'); queue = context.Queue()
    child = context.Process(target=fork_read, args=(store, record['result_id'], farm, queue))
    child.start()
    try:
        result = queue.get(timeout=120); child.join(120)
        assert child.exitcode == 0 and result['record'] == record
        assert _canonical(result['page']['records']) == _canonical(expected['samples'])
    finally:
        if child.is_alive(): child.terminate(); child.join(30)
        queue.close(); queue.join_thread()
    rights.allowed = False
    with pytest.raises(custody.CalculationCustodyHold): store.get('tenant-1', record['result_id'], farm)
    rights.allowed = True; principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError): store.get('tenant-1', record['result_id'], farm)
    assert counts(server.binding) == (*before[:4], 1)
    save_reference('normal-publication.json', {'scope': 'synthetic_registered_signed_result_software_only',
        'calculate_seconds': calculate_seconds, 'seconds': measured, 'payload_bytes': len(record['payload_raw']),
        'payload_sha256': record['payload_sha256'], 'packet': packet,
        'same_original_samples_events_UTC': True, 'current_read_rights_withdrawal_denied': True,
        'put_retry_read_RHS_zero': True, 'fork_exitcode': child.exitcode, 'fork_PID_gone': not Path('/proc', str(child.pid)).exists(),
        'fork_only_not_fresh_exec': True, 'counts_before': before, 'counts_after': counts(server.binding),
        'actual_crop_Runs': 0, 'all_owned_contexts_closed': all(c.reader.closed for c in server.input_resolver.opened)})


@pytest.mark.parametrize('login_scope', [False], indirect=True)
def test_default_new_flag_refuses_store_with_unchanged_current_farm_binding(server_setup):
    server, _, _, _, _ = server_setup
    with pytest.raises(custody.CalculationCustodyHold): storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)


def test_uncreated_yielded_foreign_tenant_and_server_key_cannot_publish(server_setup, monkeypatch):
    server, raw, _, _, _ = server_setup
    for key in (KEY, b'x'*31, 'not-bytes'):
        with pytest.raises(custody.CalculationCustodyHold): storage.CalculationCycleCropResultStore(server, integrity_key=key)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
    with pytest.raises(custody.CalculationCustodyHold): store.put('tenant-1', raw)
    assert json.loads(server.advance('tenant-1', raw, budget={'max_steps': 1, 'max_transitions': 1}))['status'] == 'yielded'
    forbid_math(monkeypatch)
    with pytest.raises(custody.CalculationCustodyHold): store.put('tenant-1', raw)
    with pytest.raises(PermissionError): store.put('foreign', raw)
    assert counts(server.binding)[2:] == (0, 0, 0)


@pytest.mark.parametrize('phase', ['before-commit', 'after-commit'])
@pytest.mark.parametrize('kind', ['input', 'write-scope', 'source'])
def test_actual_transaction_rights_withdrawal_rolls_back_or_keeps_private_audit(server_setup, monkeypatch, phase, kind):
    server, raw, rights, principal, _ = server_setup; server.advance('tenant-1', raw, budget=BUDGET)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY); forbid_math(monkeypatch)
    connect = store.jobs.connect
    source = server.binding.farms.replay.candidates._source._source
    original_source = source.get_input_rights
    def withdraw():
        if kind == 'input': rights.allowed = False
        elif kind == 'write-scope': principal['scopes'].remove('crop_result_write')
        else: monkeypatch.setattr(source, 'get_input_rights', lambda *_: None)
    class ObservedConnection:
        inserted = False
        def __init__(self, conn): self.conn = conn
        def __getattr__(self, name): return getattr(self.conn, name)
        def execute(self, query, *args, **kwargs):
            result = self.conn.execute(query, *args, **kwargs)
            if hasattr(query, 'as_string') and query.as_string(self.conn).startswith('INSERT INTO'):
                self.inserted = True
                if phase == 'before-commit': withdraw()
            return result
    @contextmanager
    def connected():
        with connect() as conn:
            observed = ObservedConnection(conn); yield observed
        if phase == 'after-commit' and observed.inserted: withdraw()
    monkeypatch.setattr(store.jobs, 'connect', connected)
    with pytest.raises((custody.CalculationCustodyHold, PermissionError)): store.put('tenant-1', raw)
    assert counts(server.binding)[-1] == (phase == 'after-commit')
    rights.allowed = True; monkeypatch.setattr(store.jobs, 'connect', connect)
    principal['scopes'].add('crop_result_write'); monkeypatch.setattr(source, 'get_input_rights', original_source)
    row = store._find('tenant-1', study_id=json.loads(raw)['study_id'], revision='r1')
    if phase == 'after-commit':
        assert store.get('tenant-1', row['result_id'], json.loads(raw)['farm'])['payload_raw'] == row['payload_raw']


def test_actual_db_advisory_lock_pending_and_missing_id_stays_missing(server_setup, login_scope, monkeypatch):
    server, raw, _, _, _ = server_setup; server.advance('tenant-1', raw, budget=BUDGET)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY); forbid_math(monkeypatch)
    body = json.loads(raw); base, _, _ = login_scope
    with base.connect() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(%s)', (_intent_lock_key('tenant-1', body['study_id'], body['revision']),))
        with pytest.raises(custody.CalculationCustodyPending): store.put('tenant-1', raw)
    assert counts(server.binding)[-1] == 0
    assert store.get('tenant-1', storage.VERSION+':'+'0'*64, body['farm']) is None
    store.put('tenant-1', raw)


def test_valid_hmac_cannot_replace_context_proof_or_farm_and_wrong_key_is_held(server_setup, monkeypatch):
    server, raw, _, _, _ = server_setup; server.advance('tenant-1', raw, budget=BUDGET)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY); forbid_math(monkeypatch)
    first = store.put('tenant-1', raw); farm = json.loads(raw)['farm']; original = store._find('tenant-1', result_id=first['result_id'])
    find = store._find
    for kind in ('signature', 'authority', 'proof', 'validation', 'code', 'farm'):
        changed = deepcopy(original); packet = json.loads(original['payload_raw'])
        if kind == 'signature': changed['integrity_signature'] = '0'*64
        elif kind == 'authority': changed['registered_by'] = store.jobs.runtime_identity[0].roles['worker']
        else:
            if kind == 'proof': packet['policies']['server_progress']['proof_sha256'] = '0'*64
            elif kind == 'validation': packet['binding']['input']['input_validation']['evidence_sha256'] = '0'*64
            elif kind == 'code': packet['code']['runtime_roles_code_sha256'] = '0'*64
            else: packet['binding']['registration']['floor_area']['value'] = '12345'
            packet['policies']['server_progress']['binding_sha256'] = sha256(_canonical(packet['binding'])).hexdigest()
            packet.pop('result_id'); packet['result_id'] = storage.VERSION+':'+sha256(_canonical(packet)).hexdigest()
            payload = _canonical(packet)
            changed.update(payload_raw=payload, payload_sha256=sha256(payload).hexdigest(),
                integrity_signature=store._signature(payload), result_id=packet['result_id'])
        monkeypatch.setattr(store, '_find', lambda *a, **k: changed)
        with pytest.raises(custody.CalculationCustodyHold): store.get('tenant-1', changed['result_id'], farm)
    monkeypatch.setattr(store, '_find', find)
    other = storage.CalculationCycleCropResultStore(server, integrity_key=b'other-owned-verified-db-key-000001')
    with pytest.raises(custody.CalculationCustodyHold): other.get('tenant-1', first['result_id'], farm)


def test_resumed_calculation_checkpoint_is_exact_and_published_pages_match_continuous(server_setup, monkeypatch):
    server, raw, _, _, expected = server_setup
    partial = json.loads(server.advance('tenant-1', raw, budget={'max_steps': 7, 'max_transitions': 11}))
    assert partial['status'] == 'yielded' and partial['steps'] == 7
    with server._open('tenant-1', raw, False) as journal: before = deepcopy(journal.writer._checkpoint)
    restarted = custody.CalculationServerCustody(server.binding, server.directory,
        input_resolver=server.input_resolver, integrity_key=KEY)
    with restarted._open('tenant-1', raw, False) as journal: assert journal.writer._checkpoint == before
    progress = restarted.advance('tenant-1', raw, budget=BUDGET)
    assert json.loads(progress)['steps'] == 120
    store = storage.CalculationCycleCropResultStore(restarted, integrity_key=DB_KEY); forbid_math(monkeypatch)
    record = store.put('tenant-1', raw); farm = json.loads(raw)['farm']
    for kind, limit in (('samples', 64), ('events', 8)):
        page = fresh(store).page('tenant-1', record['result_id'], farm, kind, 0, limit)
        assert _canonical(page['records']) == _canonical(expected[kind])
    save_reference('resumed-publication.json', {'scope': 'synthetic_registered_software_only', 'paused_steps': 7,
        'completed_steps': 120, 'exact_whole_checkpoint_clock_counters': True,
        'same_process_new_service_not_fresh_exec': True, 'same_continuous_original_pages_UTC': True,
        'publication_read_RHS_zero': True, 'payload_sha256': record['payload_sha256']})


def test_numeric_hold_preserves_reason_manifest_and_summary_withdrawal_denies(server_setup, tmp_path, monkeypatch):
    from app import crop_cycle_input_stream as inputs
    from app import crop_plant_startup_integration as original
    from test_crop_startup_result_store import shifted
    from test_crop_cycle_artifact import PROFILES
    base, raw, rights, _, _ = server_setup
    program = shifted(); program['initial_state']['values']['temperature_sum']['value'] = 0
    expected = original.integrate_plant_startup(**program, **PROFILES); assert expected['status'] == 'hold'
    anchors = program.pop('output_times'); directory = tmp_path/'hold-inputs'
    packet = inputs.write_input_packet(directory, **program, anchors=anchors, outputs=anchors,
        **PROFILES, program_id='own-verified-db-hold')
    for p in directory.iterdir(): p.chmod(0o400)
    proof = base.binding.input_authority.issue(directory, packet['root_sha256'])
    body = json.loads(raw); body['input'].update(root_sha256=packet['root_sha256'], program_id='own-verified-db-hold')
    body['rights']['input_root_sha256'] = packet['root_sha256']; raw = _canonical(body)
    root = tmp_path/'hold-server'; root.mkdir(mode=0o700)
    resolver = OwnInputResolver(directory, packet['root_sha256'], proof)
    server = custody.CalculationServerCustody(base.binding, root, input_resolver=resolver, integrity_key=KEY)
    assert json.loads(server.advance('tenant-1', raw, budget=BUDGET))['status'] == 'hold'
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY); forbid_math(monkeypatch)
    record = store.put('tenant-1', raw); summary = store.summary('tenant-1', record['result_id'], body['farm'])
    for key in ('hold', 'last_confirmed'): assert _canonical(summary[key]) == _canonical(expected[key])
    assert summary['status'] == 'hold' and summary['manifest']['engine_version'] == engine.VERSION
    copied = storage.deepcopy
    def withdrawn(value):
        result = copied(value); rights.allowed = False; return result
    monkeypatch.setattr(storage, 'deepcopy', withdrawn)
    with pytest.raises(custody.CalculationCustodyHold): store.summary('tenant-1', record['result_id'], body['farm'])
    assert all(c.reader.closed for c in resolver.opened)
    save_reference('hold-publication.json', {'scope': 'synthetic_numerical_hold_software_only',
        'same_original_reason_and_confirmed_past': True, 'manifest_retained': True,
        'summary_withdrawal_denied': True, 'payload_sha256': record['payload_sha256'], 'RHS_read_zero': True})


def test_legacy_signed_result_and_verified_result_coexist_without_reissuing_old_history(server_setup, monkeypatch):
    from app import crop_cycle_farm_binding as old_binding
    from app import crop_cycle_server_custody as old_server
    from app import crop_cycle_result_store as old_storage
    from test_crop_cycle_server_custody_farms import OwnInputResolver as OldResolver
    from test_crop_cycle_artifact import PROFILES, NOTICE
    server, raw, rights, _, expected = server_setup; farm = json.loads(raw)['farm']
    binding = old_binding.CycleFarmBinding(server.binding.farms, **PROFILES, notice_raw=NOTICE, input_rights=rights)
    resolver = OldResolver(server.input_resolver.directory, server.input_resolver.root)
    legacy = old_server.CycleServerCustody(binding, server.directory, input_resolver=resolver, integrity_key=KEY)
    old_progress = legacy.advance('tenant-1', raw, budget=BUDGET)
    old = old_storage.CycleCropResultStore(legacy, integrity_key=DB_KEY)
    original = old.put('tenant-1', raw)
    old_id = old_server._intent_id('tenant-1', json.loads(raw))
    files = {str(p.relative_to(server.directory)): (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode & 0o777)
        for p in (server.directory/old_id).rglob('*') if p.is_file()}
    progress = server.advance('tenant-1', raw, budget=BUDGET)
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY); forbid_math(monkeypatch)
    current = store.put('tenant-1', raw)
    assert original['result_id'].startswith('crop-cycle-result-v1:')
    assert current['result_id'].startswith('crop-cycle-verified-result-v1:')
    assert old.get('tenant-1', original['result_id'], farm) == original
    assert store.get('tenant-1', current['result_id'], farm) == current
    assert all((sha256((server.directory/p).read_bytes()).hexdigest(), (server.directory/p).stat().st_mode & 0o777) == v for p,v in files.items())
    with pytest.raises(custody.CalculationCustodyHold): storage.CalculationCycleCropResultStore(legacy, integrity_key=DB_KEY)
    with pytest.raises(old_server.CycleCustodyHold): old_storage.CycleCropResultStore(server, integrity_key=DB_KEY)
    assert counts(server.binding)[2:] == (1, 0, 1)
    save_reference('legacy-coexistence.json', {'scope': 'synthetic_actual_signed_history_software_only',
        'same_tenant_study_revision': True, 'original_record_bytes_hash_time_preserved': True,
        'original_file_hashes_modes_preserved': True, 'legacy_file_count': len(files),
        'original_progress_sha256': sha256(old_progress).hexdigest(), 'verified_progress_sha256': sha256(progress).hexdigest(),
        'old_payload_sha256': original['payload_sha256'], 'new_payload_sha256': current['payload_sha256'],
        'mixed_constructor_types_refused': True, 'actual_crop_Runs': 0})


def test_persisted_db_file_tamper_and_new_grant_withdrawal_hold_without_fd_leak(server_setup, login_scope, monkeypatch):
    server, raw, _, _, _ = server_setup; progress = json.loads(server.advance('tenant-1', raw, budget=BUDGET))
    store = storage.CalculationCycleCropResultStore(server, integrity_key=DB_KEY); forbid_math(monkeypatch)
    first = store.put('tenant-1', raw); farm = json.loads(raw)['farm']; base, policy, _ = login_scope
    original = store._find('tenant-1', result_id=first['result_id']); before_fd = len(os.listdir('/proc/self/fd'))
    table = sql.Identifier(policy.schema, schema.TABLE)
    def overwrite(changes):
        with base.connect() as conn:
            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER verified_cycle_crop_result_immutable').format(table))
            conn.execute(sql.SQL('UPDATE {} SET {} WHERE tenant_id=%s AND result_id=%s').format(table,
                sql.SQL(',').join(sql.SQL('{}=%s').format(sql.Identifier(k)) for k in changes)),
                (*changes.values(), 'tenant-1', first['result_id']))
            conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER verified_cycle_crop_result_immutable').format(table))
    for changes in ({'payload_raw': original['payload_raw']+b' ', 'payload_sha256': sha256(original['payload_raw']+b' ').hexdigest()},
            {'integrity_signature': '0'*64}, {'registered_by': policy.roles['worker']}):
        try:
            overwrite(changes)
            with pytest.raises(custody.CalculationCustodyHold): store.get('tenant-1', first['result_id'], farm)
            assert len(os.listdir('/proc/self/fd')) == before_fd
        finally: overwrite({k:original[k] for k in changes})
    where = server.directory/custody._intent_id('tenant-1', json.loads(raw))
    paths = [where/'artifact'/'HEAD', where/'artifact'/(progress['header_sha256']+'.json'),
        where/'proofs'/(progress['head_sha256']+'.json'), server.input_resolver.directory/'root.json']
    for path in paths:
        previous = path.read_bytes(); mode = path.stat().st_mode & 0o777
        try:
            path.chmod(0o600); path.write_bytes(previous+b' '); path.chmod(mode)
            with pytest.raises(custody.CalculationCustodyHold): store.get('tenant-1', first['result_id'], farm)
            assert len(os.listdir('/proc/self/fd')) == before_fd
        finally: path.chmod(0o600); path.write_bytes(previous); path.chmod(mode)
    try:
        with base.connect() as conn: conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(table, sql.Identifier(policy.roles['authority'])))
        with pytest.raises(custody.CalculationCustodyHold): store.get('tenant-1', first['result_id'], farm)
    finally:
        with base.connect() as conn: conn.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(table, sql.Identifier(policy.roles['authority'])))
    assert store.get('tenant-1', first['result_id'], farm) == first and len(os.listdir('/proc/self/fd')) == before_fd
    save_reference('tamper-cleanup.json', {'actual_DB_mutations': 3, 'actual_file_mutations': 4,
        'new_grant_withdrawal_denied': True, 'FD_before_after': [before_fd, len(os.listdir('/proc/self/fd'))],
        'original_record_restored': True, 'RHS_read_zero': True})
