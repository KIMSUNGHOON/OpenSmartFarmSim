"""Actual SCRAM/TLS admission scopes retain every current source and commit fence."""
from copy import deepcopy
from datetime import timedelta
from hashlib import sha256
import json

from psycopg import sql

from app import crop_leaf_population_signed_producer as producer
from app import runtime_connection_scope as connections
from app.market_source_store import MarketSourceStore
from test_api_crop_leaf_population_execution import NOW, POST
from test_api_crop_leaf_population_execution_native import (
    http_setup, login_scope, login_database, final_cleanup, https, pytestmark)
from test_crop_leaf_population_execution_native import retained_rows
from test_crop_leaf_population_signed_artifact_native import PUBLIC
from test_crop_morphology_execution_native import counts
from test_crop_morphology_signed_artifact_native import schema_hash
from leaf_population_farm_fresh import snapshot
import morphology_farm_factory as factory
import test_crop_leaf_population_farm_binding_native as leaf_factory


def forbid_admission_execution(patch, worker):
    calls = leaf_factory.forbid_growth(patch)
    for owner, name, label in ((type(worker), 'run_once', 'leaf_worker'),
            (producer, 'produce_registered_leaf_population', 'leaf_signed_producer')):
        calls[label] = 0
        def forbidden(*args, _label=label, **kwargs):
            calls[_label] += 1
            raise AssertionError('admission invoked '+_label)
        patch.setattr(owner, name, forbidden)
    return calls


def stored_input(service, job_id):
    with service.jobs.connect() as conn:
        row = service.jobs._locked_job(conn, 'tenant-1', job_id)
        return service.jobs._verified_input(row)


def test_actual_https_first_admission_and_retry_each_reconstruct_once_with_all_current_sources(
        http_setup, login_scope, tmp_path, monkeypatch):
    service, _, worker, body, _, _, app, _ = http_setup
    farms = service.authority.farm_binding.farms.farms
    ref = body['farm']
    args = ('tenant-1', ref['scenario_id'], ref['scenario_revision'], ref['registration_sha256'])
    before = counts(service); retained = retained_rows(login_scope[0]); assert retained[1] == 25
    parent = snapshot(service.authority.farm_binding.parent_authority.directory)
    originals = {p.name: sha256(p.read_bytes()).hexdigest() for p in PUBLIC.iterdir()}
    prepare, read = farms._prepare, farms.read_registration
    source_read = MarketSourceStore._read_in_transaction
    records = []; inputs = []; witnesses = []; evidence = []; leaf = None

    def preparing(*a, **kw):
        observed['prepare'] += 1
        return prepare(*a, **kw)

    def reading(*a, **kw):
        start = len(observed['sources'])
        value = read(*a, **kw)
        witness, frame = farms._registration_read.get(), connections._CURRENT.get()
        assert witness is not None and witness.active and not witness.failed and witness.args == args
        assert witness.value is not None and witness.lookups
        assert frame is not None and frame.conn is not None
        observed['traces'].append(observed['sources'][start:])
        observed['witnesses'].append(witness)
        observed['connections'].append(frame.conn)
        return value

    def source(self, conn, tenant, kind, identity, revision, **kw):
        observed['sources'].append((tenant, kind, identity, revision, kw.get('pin', False)))
        return source_read(self, conn, tenant, kind, identity, revision, **kw)

    growth = forbid_admission_execution(monkeypatch, worker)
    monkeypatch.setattr(farms, '_prepare', preparing)
    monkeypatch.setattr(farms, 'read_registration', reading)
    monkeypatch.setattr(MarketSourceStore, '_read_in_transaction', source)
    with https(app, tmp_path/'tls') as (call, observations):
        for request_kind in ('first_admission', 'identical_retry'):
            observed = {'prepare': 0, 'sources': [], 'traces': [], 'witnesses': [], 'connections': []}
            status, job = call(POST, 'POST', body)
            assert status == 202 and job['stage'] == 'simulation' and job['state'] == 'queued'
            assert job['attempt_count'] == 0
            assert observed['prepare'] == 1
            assert len(observed['traces']) == 64 and len(observed['sources']) == 64*76
            trace = observed['traces'][0]
            assert len(trace) == 76 and all(value == trace for value in observed['traces'])
            witness = observed['witnesses'][0]
            assert all(value is witness for value in observed['witnesses'])
            assert not witness.active and witness.value is None and not witness.lookups
            connection = observed['connections'][0]
            assert all(value is connection and value.closed for value in observed['connections'])
            assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
            records.append(job); witnesses.append((witness, connection))
            inputs.append(stored_input(service, job['job_id']))
            assert json.loads(inputs[-1])['request'] == body
            assert service.jobs.get_publication('tenant-1', job['job_id']) is None
            current_leaf = snapshot(service.authority.directory)
            if leaf is None: leaf = current_leaf
            else: assert current_leaf == leaf
            evidence.append({'request': request_kind, 'registration_reconstructions': observed['prepare'],
                'current_registration_reads': len(observed['traces']), 'current_source_reads': len(observed['sources']),
                'ordered_source_trace_per_registration': trace, 'single_request_witness': True,
                'witness_inactive_after_response': True, 'source_owned_connection_closed': True})
    assert records[0] == records[1] and inputs[0] == inputs[1]
    assert evidence[0]['ordered_source_trace_per_registration'] == evidence[1]['ordered_source_trace_per_registration']
    assert witnesses[0][0] is not witnesses[1][0] and witnesses[0][1] is not witnesses[1][1]
    after = counts(service)
    assert after == {**before, 'jobs': before['jobs']+1, 'job_events': before['job_events']+1}
    assert retained_rows(login_scope[0], records[0]['job_id']) == retained
    assert snapshot(service.authority.farm_binding.parent_authority.directory) == parent
    assert {p.name: sha256(p.read_bytes()).hexdigest() for p in PUBLIC.iterdir()} == originals
    assert not any(growth.values())
    factory.save('leaf-admission-registration-scope-native-normal.json', {'actual_SCRAM': True,
        'certificate_verified': True, 'job_id': records[0]['job_id'], 'same_job_and_original_input_bytes': True,
        'input_sha256': sha256(inputs[0]).hexdigest(), 'counts_before_after': [before, after],
        'retained_25_table_rows_sha256': retained[0], 'request_scopes': evidence, 'requests': observations,
        'growth_worker_producer_CLI_calls': growth, 'original_parent_and_fixture_files_preserved': True,
        'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})


def test_actual_https_late_commit_source_grant_and_expiry_rollback_and_restore(
        http_setup, login_scope, tmp_path, monkeypatch):
    service, _, worker, body, _, _, app, clock = http_setup
    farms = service.authority.farm_binding.farms.farms
    base, policy, _ = login_scope
    target = sql.Identifier(policy.schema, 'market_source_records')
    role = sql.Identifier(policy.roles['authority'])
    original = service.current_input
    growth = forbid_admission_execution(monkeypatch, worker)
    parent = snapshot(service.authority.farm_binding.parent_authority.directory)
    originals = {p.name: sha256(p.read_bytes()).hexdigest() for p in PUBLIC.iterdir()}
    failures = []
    errors = {
        401: {'error': {'code': 'unauthenticated', 'message': 'Authentication required'}},
        422: {'error': {'code': 'leaf_population_execution_hold', 'message': 'LeafPopulation evidence unavailable'}}}

    with https(app, tmp_path/'tls') as (call, observations):
        status, job = call(POST, 'POST', body); assert status == 202 and job['state'] == 'queued'
        path = '/v1/jobs/'+job['job_id']+'/crop-leaf-population-execution'
        input_raw = stored_input(service, job['job_id'])
        before = schema_hash(base); assert before[1] == 25
        job_counts = counts(service)
        leaf = snapshot(service.authority.directory)
        for change in ('source', 'grant', 'expiry'):
            candidate = deepcopy(body); candidate['study_id'] = 'owned-leaf-admission-late-'+change
            invoked = []; captured = []; undo = []; recovered = []
            mutation = {}

            def late(tenant, raw, *, write=False):
                assert tenant == 'tenant-1' and write is True
                assert json.loads(raw)['request'] == candidate
                witness, frame = farms._registration_read.get(), connections._CURRENT.get()
                assert witness is not None and witness.active and not witness.failed
                assert witness.value is not None and witness.root is not None and witness.lookups
                assert frame is not None and frame.conn is not None
                captured.append((witness, frame.conn))
                invoked.append(change)
                assert len(invoked) == 1
                if change == 'source':
                    identity, revision = next(args for name, args, _ in witness.lookups if name == 'get_input_rights')
                    params = ('tenant-1', identity, revision)
                    where = sql.SQL("tenant_id=%s AND kind='input_rights' AND record_id=%s AND revision=%s")
                    with base.connect() as conn:
                        rows = conn.execute(sql.SQL('SELECT payload_raw,payload_sha256 FROM {} WHERE {}')
                            .format(target, where), params).fetchall()
                    assert len(rows) == 1
                    update = sql.SQL('UPDATE {} SET payload_raw=%s,payload_sha256=%s WHERE {}').format(target, where)

                    def replace(data):
                        with base.connect() as conn:
                            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(target))
                            assert conn.execute(update, (*data, *params)).rowcount == 1
                            conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(target))

                    undo.append(lambda: replace((rows[0]['payload_raw'], rows[0]['payload_sha256'])))
                    replace((b'{}', sha256(b'{}').hexdigest()))
                    mutation.update({'kind': 'input_rights', 'record_id': identity, 'revision': revision,
                        'original_payload_sha256': rows[0]['payload_sha256'], 'changed_payload_sha256': sha256(b'{}').hexdigest()})
                elif change == 'grant':
                    with base.connect() as conn:
                        assert conn.execute('SELECT has_table_privilege(%s,%s,%s) AS allowed',
                            (policy.roles['authority'], target.as_string(), 'UPDATE')).fetchone() == {'allowed': False}
                    def revoke():
                        with base.connect() as conn:
                            conn.execute(sql.SQL('REVOKE UPDATE ON {} FROM {}').format(target, role))
                    undo.append(revoke)
                    with base.connect() as conn:
                        conn.execute(sql.SQL('GRANT UPDATE ON {} TO {}').format(target, role))
                    mutation.update({'table': 'market_source_records', 'excess_authority_grant': 'UPDATE'})
                else:
                    clock['now'] = NOW+timedelta(hours=2)
                    mutation['reference_clock_expired_before_current_input'] = True
                return original(tenant, raw, write=write)

            try:
                with monkeypatch.context() as patch:
                    patch.setattr(service, 'current_input', late)
                    status, denied = call(POST, 'POST', candidate)
                assert status == (401 if change == 'expiry' else 422), change
                assert denied == errors[status], change
                assert invoked == [change] and len(captured) == 1
                assert all(not witness.active and connection.closed for witness, connection in captured)
                assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
            finally:
                clock['now'] = NOW
                for restore in reversed(undo): restore()
            assert schema_hash(base) == before and counts(service) == job_counts, change

            def recovering(*a, **kw):
                value = original(*a, **kw)
                witness, frame = farms._registration_read.get(), connections._CURRENT.get()
                assert witness is not None and witness.active and not witness.failed and witness.value is not None
                assert frame is not None and frame.conn is not None
                assert witness is not captured[0][0] and frame.conn is not captured[0][1]
                recovered.append((witness, frame.conn))
                return value

            with monkeypatch.context() as patch:
                patch.setattr(service, 'current_input', recovering)
                status, current = call(path)
                assert status == 200 and current['job'] == job
                assert current['result'] is current['manifest'] is current['frame'] is current['replay'] is None
                status, retried = call(POST, 'POST', body)
                assert status == 202 and retried == job
            assert recovered and all(not witness.active and connection.closed for witness, connection in recovered)
            assert farms._registration_read.get() is connections._CURRENT.get() is connections._REQUEST.get() is None
            assert stored_input(service, job['job_id']) == input_raw
            assert service.jobs.get_publication('tenant-1', job['job_id']) is None
            assert schema_hash(base) == before and counts(service) == job_counts, change
            assert snapshot(service.authority.farm_binding.parent_authority.directory) == parent
            current_leaf = snapshot(service.authority.directory)
            assert all(current_leaf.get(name) == value for name, value in leaf.items())
            failures.append({'late_fault': change, 'status': 401 if change == 'expiry' else 422,
                'mutation': mutation, 'original_registration_witness_populated_at_commit_guard': True,
                'failed_scope_inactive_and_connection_closed': True, 'all_25_table_rows_restored': before[0],
                'ordinary_read_and_identical_retry_original_job': True, 'original_input_sha256': sha256(input_raw).hexdigest()})
    assert {p.name: sha256(p.read_bytes()).hexdigest() for p in PUBLIC.iterdir()} == originals
    assert not any(growth.values())
    factory.save('leaf-admission-registration-scope-native-late.json', {'actual_SCRAM': True,
        'certificate_verified': True, 'job_id': job['job_id'], 'commit_guard_faults': failures,
        'requests': observations, 'database_sha256_before_after': [before, schema_hash(base)],
        'growth_worker_producer_CLI_calls': growth, 'original_parent_and_fixture_files_preserved': True,
        'prepared_unpublished_immutable_bindings_permitted': True, 'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})
