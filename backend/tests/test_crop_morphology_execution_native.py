"""Actual SCRAM admission, immutable references, and rollback at the commit fence."""
from copy import deepcopy
from hashlib import sha256
import json

from psycopg import sql
import pytest

from app import crop_morphology_execution as model
from app.job_store import JobIntentConflict
from login_database import login_database, login_scope
from test_crop_morphology_signed_artifact_native import setup
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


class Resolver:
    version = 'owned-morphology-immutable-input-resolver-v1'

    def __init__(self, packet):
        self.packet = dict(packet)
        self.calls = 0

    def __call__(self, tenant, reference):
        self.calls += 1
        if tenant != 'tenant-1': raise PermissionError('foreign input')
        return dict(self.packet)


def counts(service):
    with service.jobs.connect() as conn:
        return {table: conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(service.jobs._table(table))).fetchone()['n']
            for table in ('jobs', 'job_events', 'job_attempts', 'attempt_outcomes', 'job_publications', 'crop_cycle_research_results', 'thermal_g1_runs')}


@pytest.fixture(scope='module', autouse=True)
def final_cleanup(login_database):
    yield
    import psycopg
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    factory.save('admission-database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles})


@pytest.fixture
def admission(setup, monkeypatch):
    authority, body, packet, principal, rights = setup
    principal['scopes'].add('simulation_create'); resolver = Resolver(packet['packet'])
    service = model.MorphologyExecutionService(authority, input_resolver=resolver)
    calls = factory.forbid_growth(monkeypatch)
    yield service, body, packet, principal, rights, resolver, calls
    assert not any(calls.values())


def test_actual_idempotent_one_row_conflict_and_current_original_references(admission):
    service, body, packet, principal, _, resolver, calls = admission
    before = counts(service); raw = model.signed.reader._canonical(body)
    first = service.submit('tenant-1', raw); second = service.submit('tenant-1', raw)
    assert first == second and first['stage'] == 'simulation' and first['state'] == 'queued' and first['attempt_count'] == 0
    assert 'input_bytes' not in first
    with service.jobs.connect() as conn:
        row = service.jobs._locked_job(conn, 'tenant-1', first['job_id'])
        input_raw = service.jobs._verified_input(row)
    value = json.loads(input_raw); assert value['input_version'] == model.INPUT_VERSION
    assert 'program_raw' not in input_raw.decode() and service.authority.integrity_key not in input_raw
    with model.signed.MorphologyBlobStore(service.authority.directory, service.authority.access) as store:
        binding = store.get(value['farm_binding_sha256'], maximum=model.signed.farms.MAX_BINDING_BYTES)
    assert json.loads(binding)['input']['program_sha256'] == body['input']['program_sha256']
    assert len(list(service.authority.directory.iterdir())) == 1
    checked, checked_binding, checked_packet = service.current_input('tenant-1', input_raw)
    assert checked == value and checked_binding == binding and checked_packet == packet['packet']
    principal['scopes'].remove('simulation_create')
    assert service.current_input('tenant-1', input_raw)[0] == value
    with pytest.raises(PermissionError): service.submit('tenant-1', raw)
    principal['scopes'].add('simulation_create')
    changed = deepcopy(body); changed['rights']['revision'] = 'r2'
    with pytest.raises(JobIntentConflict): service.submit('tenant-1', model.signed.reader._canonical(changed))
    after = counts(service)
    assert after == {**before, 'jobs': before['jobs']+1, 'job_events': before['job_events']+1}
    assert not any(calls.values()) and resolver.calls >= 4
    factory.save('admission-normal.json', {'job_id': str(first['job_id']), 'input_sha256': first['input_sha256'],
        'input_bytes': len(input_raw), 'binding_sha256': value['farm_binding_sha256'], 'binding_bytes': len(binding),
        'one_job_event_no_attempt_or_publication': True, 'current_original_references': True,
        'read_without_create_scope': True, 'revision_conflict_rejected': True, 'counts_before_after': [before, after], 'calls': calls})


def test_current_and_late_commit_revocations_rollback_without_math(admission, monkeypatch):
    service, body, packet, principal, rights, resolver, calls = admission
    before = counts(service); raw = model.signed.reader._canonical(body)
    with pytest.raises(PermissionError): service.submit('foreign', raw)
    rights.allowed = False
    with pytest.raises(model.MorphologyExecutionHold): service.submit('tenant-1', raw)
    rights.allowed = True; packet['review']['status'] = 'revoked'
    with pytest.raises(model.MorphologyExecutionHold): service.submit('tenant-1', raw)
    packet['review']['status'] = 'accepted_for_software_validation'
    original = resolver.packet['program_raw']; resolver.packet['program_raw'] += b' '
    with pytest.raises(model.MorphologyExecutionHold): service.submit('tenant-1', raw)
    resolver.packet['program_raw'] = original
    submit = service.jobs.submit
    def late(*a, **kw):
        guard = kw['commit_guard']
        def revoke():
            principal['scopes'].remove('simulation_create')
            guard()
        return submit(*a, **{**kw, 'commit_guard': revoke})
    with monkeypatch.context() as patch:
        patch.setattr(service.jobs, 'submit', late)
        with pytest.raises(PermissionError): service.submit('tenant-1', raw)
    principal['scopes'].add('simulation_create')
    assert counts(service) == before and not any(calls.values())
    factory.save('admission-fences.json', {'foreign_current_rights_review_original_bytes_rejected': True,
        'commit_scope_revocation_rolled_back': True, 'counts_before_after': [before, counts(service)], 'calls': calls})
