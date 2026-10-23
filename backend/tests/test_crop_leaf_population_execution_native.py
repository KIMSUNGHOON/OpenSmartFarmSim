"""Actual SCRAM leaf admission and current original parent/input commit fences."""
from copy import deepcopy
from hashlib import sha256
import json
from time import perf_counter

from psycopg import sql
import pytest

from app import crop_leaf_population_execution as model
from app import crop_leaf_population_signed_producer as producer
from app.job_store import JobIntentConflict
from login_database import login_database, login_scope
from test_crop_leaf_population_signed_artifact_native import setup
from test_crop_morphology_signed_artifact_native import schema_hash, final_cleanup
from test_crop_morphology_execution_native import counts
from leaf_population_farm_fresh import snapshot
import test_crop_leaf_population_farm_binding_native as leaf_factory
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


class Resolver:
    version = 'owned-leaf-population-immutable-input-resolver-v1'

    def __init__(self, packet):
        self.packet = dict(packet)
        self.calls = 0

    def __call__(self, tenant, reference):
        if tenant != 'tenant-1': raise PermissionError('foreign leaf input')
        assert set(reference) == {'schema_version', 'program_id', 'program_sha256', 'source_sha256', 'evidence_sha256'}
        self.calls += 1
        return dict(self.packet)


def retained_rows(base, excluded_job=None):
    with base.connect() as conn:
        names = [r['table_name'] for r in conn.execute("SELECT table_name FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name", (base.schema,)).fetchall()]
        rows = {}
        for name in names:
            values = [r['row'] for r in conn.execute(sql.SQL('SELECT to_jsonb(x)::text AS row FROM {} x')
                .format(sql.Identifier(base.schema, name))).fetchall()]
            rows[name] = sorted(raw for raw in values if not (name in ('jobs', 'job_events')
                and excluded_job is not None and json.loads(raw)['job_id'] == str(excluded_job)))
    return sha256(model.signed.reader._canonical(rows)).hexdigest(), len(names)


@pytest.fixture
def admission(setup, monkeypatch):
    authority, values = setup
    resolver = Resolver(values[2])
    service = model.LeafPopulationExecutionService(authority, input_resolver=resolver)
    calls = leaf_factory.forbid_growth(monkeypatch)
    calls['leaf_signed_producer'] = 0
    def forbidden(*args, **kwargs):
        calls['leaf_signed_producer'] += 1
        raise AssertionError('admission called signed producer')
    monkeypatch.setattr(producer, 'produce_registered_leaf_population', forbidden)
    yield service, values, resolver, calls
    assert not any(calls.values())


def test_actual_one_job_original_references_conflict_and_current_read(admission, login_scope):
    service, values, resolver, calls = admission
    binding, body, packet, _, _, review, _, principal, *_ = values
    before = counts(service); rows = retained_rows(login_scope[0]); assert rows[1] == 25
    parent_before = snapshot(binding.parent_authority.directory)
    raw = model.signed.reader._canonical(body); timings = {}
    started = perf_counter(); first = service.submit('tenant-1', raw); timings['submit'] = perf_counter()-started
    started = perf_counter(); second = service.submit('tenant-1', raw); timings['identical_retry'] = perf_counter()-started
    assert first == second and first['stage'] == 'simulation' and first['state'] == 'queued' and first['attempt_count'] == 0
    assert 'input_bytes' not in first
    with service.jobs.connect() as conn:
        row = service.jobs._locked_job(conn, 'tenant-1', first['job_id'])
        input_raw = service.jobs._verified_input(row)
    value = json.loads(input_raw)
    assert value['input_version'] == model.INPUT_VERSION and value['request']['parent'] == body['parent']
    assert len(input_raw) <= 64*1024 and b'program_raw' not in input_raw and service.authority.integrity_key not in input_raw
    with model.signed.MorphologyBlobStore(service.authority.directory, service.authority.access) as store:
        original_binding = store.get(value['farm_binding_sha256'], maximum=model.signed.farms.MAX_BINDING_BYTES)
    stored = json.loads(original_binding)
    assert stored['input']['program_sha256'] == body['input']['program_sha256']
    assert stored['parent']['job_id'] == body['parent']['job_id']
    assert len(list(service.authority.directory.iterdir())) == 1
    principal['scopes'].remove('simulation_create')
    started = perf_counter(); checked, checked_binding, checked_packet = service.current_input('tenant-1', input_raw)
    timings['current_read'] = perf_counter()-started
    assert checked == value and checked_binding == original_binding and checked_packet == packet
    with pytest.raises(PermissionError): service.submit('tenant-1', raw)
    principal['scopes'].add('simulation_create')
    changed = deepcopy(body); changed['rights']['revision'] = 'r2'
    with pytest.raises(JobIntentConflict): service.submit('tenant-1', model.signed.reader._canonical(changed))
    review['status'] = 'revoked'
    with pytest.raises(model.LeafPopulationExecutionHold): service.submit('tenant-1', raw)
    review['status'] = 'accepted_for_software_validation'
    after = counts(service)
    assert after == {**before, 'jobs': before['jobs']+1, 'job_events': before['job_events']+1}
    assert rows == retained_rows(login_scope[0], first['job_id'])
    assert parent_before == snapshot(binding.parent_authority.directory) and not any(calls.values())
    factory.save('leaf-admission-normal.json', {'job_id': str(first['job_id']), 'input_sha256': first['input_sha256'],
        'parent_job_id': body['parent']['job_id'], 'input_bytes': len(input_raw), 'binding_bytes': len(original_binding),
        'binding_sha256': value['farm_binding_sha256'], 'same_retry_one_job_event': True, 'conflict_rejected': True,
        'no_stale_job_return_after_review_revocation': True, 'read_without_create_scope': True,
        'single_operation_seconds': timings, 'counts_before_after': [before, after],
        'all_retained_25_table_rows_sha256': rows[0], 'parent_files_preserved': len(parent_before),
        'growth_producer_CLI_calls': calls, 'resolver_calls': resolver.calls, 'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})


def test_actual_current_inputs_and_commit_revocations_rollback(admission, login_scope, monkeypatch):
    service, values, resolver, calls = admission
    binding, body, _, _, _, review, parent_review, principal, rights, parent_rights = values
    before = counts(service); rows = schema_hash(login_scope[0]); assert rows[1] == 25
    parent_before = snapshot(binding.parent_authority.directory); raw = model.signed.reader._canonical(body)
    with pytest.raises(PermissionError): service.submit('foreign', raw)
    for item in (rights, parent_rights):
        item.allowed = False
        with pytest.raises(model.LeafPopulationExecutionHold): service.submit('tenant-1', raw)
        item.allowed = True
    for item in (review, parent_review):
        item['status'] = 'revoked'
        with pytest.raises(model.LeafPopulationExecutionHold): service.submit('tenant-1', raw)
        item['status'] = 'accepted_for_software_validation'
    for field in ('program_raw', 'source_raw', 'evidence_raw'):
        original = resolver.packet[field]; resolver.packet[field] += b' '
        with pytest.raises(model.LeafPopulationExecutionHold): service.submit('tenant-1', raw)
        resolver.packet[field] = original
    submit = service.jobs.submit; cases = []
    for case in ('create_scope', 'leaf_review', 'parent_review', 'leaf_rights', 'parent_rights', 'original_program'):
        def late(*args, **kwargs):
            guard = kwargs['commit_guard']
            def revoke():
                if case == 'create_scope': principal['scopes'].remove('simulation_create')
                elif case == 'leaf_review': review['status'] = 'revoked'
                elif case == 'parent_review': parent_review['status'] = 'revoked'
                elif case == 'leaf_rights': rights.allowed = False
                elif case == 'parent_rights': parent_rights.allowed = False
                elif case == 'original_program': resolver.packet['program_raw'] += b' '
                guard()
            return submit(*args, **{**kwargs, 'commit_guard': revoke})
        with monkeypatch.context() as patch:
            patch.setattr(service.jobs, 'submit', late)
            expected = PermissionError if case == 'create_scope' else model.LeafPopulationExecutionHold
            with pytest.raises(expected): service.submit('tenant-1', raw)
        principal['scopes'].add('simulation_create'); review['status'] = parent_review['status'] = 'accepted_for_software_validation'
        rights.allowed = parent_rights.allowed = True; resolver.packet = dict(values[2])
        assert counts(service) == before and rows == schema_hash(login_scope[0])
        cases.append(case)
    assert parent_before == snapshot(binding.parent_authority.directory) and not any(calls.values())
    assert len(list(service.authority.directory.iterdir())) == 1
    factory.save('leaf-admission-fences.json', {'foreign_current_rights_reviews_original_bytes_rejected': True,
        'post_insert_commit_revocation_rollback': cases, 'counts_before_after': [before, counts(service)],
        'all_25_table_rows_sha256': rows[0], 'parent_files_preserved': len(parent_before),
        'private_unpublished_binding_files': 1, 'growth_producer_CLI_calls': calls, 'actual_farm_Runs': 0, 'G0_G4': 'not_assessed'})
