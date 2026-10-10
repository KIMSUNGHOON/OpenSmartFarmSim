"""Actual SCRAM admission and rollback; numerical work is forbidden after setup."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
import os
from pathlib import Path
from threading import Barrier

import psycopg
import pytest
from psycopg import sql

from app import crop_climate_joint_execution as model
from app import crop_climate_joint_server_custody as custody
from app import crop_climate_joint_result_store as results
from app.job_store import JobIntentConflict
from app.thermal_run_store import _canonical
from test_crop_climate_joint_farm_binding import authoring, farm_setup, profiles, login_database, login_scope
import test_crop_climate_joint_farm_binding as reference
from test_crop_climate_joint_server_custody import Resolver

pytestmark = reference.pytestmark


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_EXECUTION_EVIDENCE')
    if directory:
        with (Path(directory) / (name + '.json')).open('x') as f:
            os.fchmod(f.fileno(), 0o400)
            json.dump(value, f, sort_keys=True, indent=2)
            f.flush(); os.fsync(f.fileno())


@pytest.fixture(scope='module', autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup', {'schemas': schemas, 'roles': roles})
    assert schemas == roles == 0


@pytest.fixture
def setup(authoring, tmp_path, profiles, monkeypatch):
    value = reference.build(authoring, tmp_path / 'inputs', profiles)
    binding, body, packet, proof, principal, _ = value
    principal['scopes'].add('simulation_create')
    resolver = Resolver(packet, proof)
    service = model.JointCropClimateExecutionService(binding, input_resolver=resolver)
    calls = reference.forbid(monkeypatch)
    def forbidden(key):
        def fail(*args, **kwargs):
            calls[key] += 1
            pytest.fail('admission invoked ' + key)
        calls[key] = 0
        return fail
    monkeypatch.setattr(custody.JointServerCustody, 'advance', forbidden('custody_advance'))
    monkeypatch.setattr(results.JointCropClimateResultStore, 'put', forbidden('result_put'))
    yield service, _canonical(body), value, calls
    assert all(n == 0 for n in calls.values())


def counts(service):
    with service.jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            service.jobs._table(name))).fetchone()['n'] for name in
            ('jobs', 'job_events', 'job_attempts', 'job_publications'))


def test_normal_admission_duplicate_and_original_binding(setup):
    service, raw, value, calls = setup
    before = counts(service)
    first = service.submit('tenant-1', raw)
    assert first['stage'] == 'simulation' and first['state'] == 'queued' and first['attempt_count'] == 0
    assert first == service.submit('tenant-1', raw)
    fresh = model.JointCropClimateExecutionService(service.binding, input_resolver=service.input_resolver)
    assert first == fresh.submit('tenant-1', raw)
    with service.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
        row = service.jobs._locked_job(conn, 'tenant-1', first['job_id'])
    stored = json.loads(row['input_bytes'])
    assert stored['input_version'] == model.INPUT_VERSION and stored['request'] == json.loads(raw)
    original = service.binding.prepare('tenant-1', raw, value[2][0], value[3])
    assert _canonical(stored['farm_binding']) == original
    assert stored['farm_binding_sha256'] == sha256(original).hexdigest()
    assert stored['farm_binding']['G0_G4'] == 'not_assessed'
    farm = stored['request']['farm']
    registered = service.binding.farms.read_registration('tenant-1', farm['scenario_id'],
        farm['scenario_revision'], farm['registration_sha256'])
    assert stored['farm_binding']['registration']['crop']['batch_id'] == registered['farm'].crops[0].batch_id
    assert row['input_sha256'] == sha256(row['input_bytes']).hexdigest() and len(row['input_bytes']) <= 65536
    assert counts(service) == (before[0] + 1, before[1] + 1, before[2], before[3])
    save('normal', {'input_bytes': len(row['input_bytes']), 'input_sha256': row['input_sha256'],
        'same_job_three_requests': True, 'actual_scram': True, 'calls': calls, 'G0_G4': 'not_assessed'})


def test_conflict_and_new_revision_do_not_restart_terminal_job(setup):
    service, raw, value, _ = setup
    first = service.submit('tenant-1', raw)
    before = counts(service)
    changed = json.loads(raw)
    changed['rights']['declaration_id'] = 'other-owned-declaration'
    with pytest.raises(JobIntentConflict):
        service.submit('tenant-1', _canonical(changed))
    resolver = Resolver(value[2], value[3])
    resolver.version = 'different-owned-resolver-v1'
    different = model.JointCropClimateExecutionService(service.binding, input_resolver=resolver)
    with pytest.raises(JobIntentConflict):
        different.submit('tenant-1', raw)
    assert counts(service) == before
    assert not service.jobs.cancel('tenant-1', first['job_id'])
    assert counts(service) == before
    value[4]['scopes'].add('cancel')
    assert service.jobs.cancel('tenant-1', first['job_id'])
    canceled = service.submit('tenant-1', raw)
    assert canceled['job_id'] == first['job_id'] and canceled['state'] == 'canceled'
    assert canceled['attempt_count'] == 0
    changed = json.loads(raw); changed['revision'] = 'r2'
    second = service.submit('tenant-1', _canonical(changed))
    assert second['job_id'] != first['job_id'] and second['state'] == 'queued'
    assert counts(service) == (before[0] + 1, before[1] + 2, before[2], before[3])
    save('conflict', {'different_request_and_resolver_conflicts': 2,
        'terminal_duplicate_stays_canceled': True, 'new_revision_new_job': True})


def test_access_current_scopes_rights_review_and_source(setup):
    service, raw, value, _ = setup
    principal, rights = value[4:]
    before = counts(service)
    for scope in ('simulation_create', *reference.WRITE_SCOPES):
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): service.submit('tenant-1', raw)
        principal['scopes'].add(scope)
    with pytest.raises(PermissionError): service.submit('other-tenant', raw)
    rights.allowed = False
    with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', raw)
    rights.allowed = True
    review = value[2][3]; original_status = review['status']; review['status'] = 'revoked'
    with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', raw)
    review['status'] = original_status
    source = value[2][0] / 'source.json'
    original = source.read_bytes(); source.chmod(0o600); source.write_bytes(original + b'\n'); source.chmod(0o400)
    with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', raw)
    source.chmod(0o600); source.write_bytes(original); source.chmod(0o400)
    assert counts(service) == before
    assert service.submit('tenant-1', raw)['state'] == 'queued'
    save('access', {'scopes_checked': 1 + len(reference.WRITE_SCOPES),
        'cross_tenant_rights_review_source_rejected': True, 'recovery_same_inputs': True})


@pytest.mark.parametrize('change', ('rights', 'scope', 'resolver'))
def test_late_change_rolls_back_inserted_job_and_event(setup, monkeypatch, change):
    service, raw, value, _ = setup
    principal, rights = value[4:]; before = counts(service); inserted = []
    original_event = service.jobs._event
    resolver_version = service.input_resolver.version
    def event(conn, tenant, job, kind, *args, **kwargs):
        original_event(conn, tenant, job, kind, *args, **kwargs)
        if kind == 'submitted':
            inserted.append(job)
            if change == 'rights': rights.allowed = False
            elif change == 'scope': principal['scopes'].remove('simulation_create')
            else: service.input_resolver.version = 'changed-at-commit-v1'
    with monkeypatch.context() as patch:
        patch.setattr(service.jobs, '_event', event)
        with pytest.raises((PermissionError, model.JointCropClimateExecutionHold)):
            service.submit('tenant-1', raw)
    assert len(inserted) == 1 and counts(service) == before
    rights.allowed = True; principal['scopes'].add('simulation_create')
    service.input_resolver.version = resolver_version
    recovered = service.submit('tenant-1', raw)
    assert recovered['state'] == 'queued' and recovered['job_id'] != inserted[0]
    save('late-' + change, {'insert_seen_inside_transaction': True,
        'job_and_event_rolled_back': True, 'same_intent_recovered': True})


def test_closed_request_size_and_resolver_failures_are_private(setup, monkeypatch):
    service, raw, value, _ = setup
    before = counts(service); original = json.loads(raw)
    changed = deepcopy(original); changed['rights']['ownership_asserted'] = 1
    invalid = [None, raw.decode(), raw + b'\n', _canonical(changed),
        _canonical({**original, 'tenant_id': 'other-tenant'}),
        _canonical({**original, 'directory': '/private-untrusted-path'}),
        _canonical({**original, 'extra': 'x' * 65536})]
    for body in invalid:
        with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', body)
    class BadResolver:
        version = 'owned-bad-resolver-v1'
        def __init__(self, result): self.result = result
        def __call__(self, *args): return self.result
    for resolved in (None, [], (value[2][0],), (value[2][0], 'not-bytes'),
                     (value[2][0], b'bad-proof'), ('/private-absent-path', value[3])):
        bad = model.JointCropClimateExecutionService(service.binding, input_resolver=BadResolver(resolved))
        with pytest.raises(model.JointCropClimateExecutionHold) as error: bad.submit('tenant-1', raw)
        assert str(error.value) == 'joint execution admission unavailable'
    class Unavailable:
        version = 'owned-unavailable-resolver-v1'
        def __call__(self, *args): raise PermissionError('private-error-marker')
    bad = model.JointCropClimateExecutionService(service.binding, input_resolver=Unavailable())
    with pytest.raises(PermissionError, match='^joint execution access denied$'): bad.submit('tenant-1', raw)
    with monkeypatch.context() as patch:
        prepare = service.binding.prepare
        def oversized(*args, **kwargs):
            packet = json.loads(prepare(*args, **kwargs)); packet['oversized_fault'] = 'x' * 65536
            return _canonical(packet)
        patch.setattr(service.binding, 'prepare', oversized)
        with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', raw)
    assert counts(service) == before
    save('closed', {'invalid_requests': len(invalid), 'invalid_resolvers': 6,
        'private_error_sanitized': True, 'oversized_binding_fault_rejected_before_job': True})


def test_authority_configuration_changes_rejected_before_insert(setup, monkeypatch):
    service, raw, _, _ = setup
    before = counts(service)
    for bad in (None, object()):
        with pytest.raises(model.JointCropClimateExecutionHold):
            model.JointCropClimateExecutionService(bad, input_resolver=service.input_resolver)
    for name, new in [('INPUT_VERSION', 'wrong-v1'), ('INTENT_DOMAIN', b'wrong'),
                      ('MAX_INPUT_BYTES', 131072), ('CODE_SHA256', '0' * 64)]:
        with monkeypatch.context() as patch:
            patch.setattr(model, name, new)
            with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', raw)
    with monkeypatch.context() as patch:
        patch.setattr(service.jobs, 'principal_provider', lambda: None)
        with pytest.raises(model.JointCropClimateExecutionHold): service.submit('tenant-1', raw)
    class NotExact(model.JointFarmBinding): pass
    with pytest.raises(model.JointCropClimateExecutionHold):
        model.JointCropClimateExecutionService(object.__new__(NotExact), input_resolver=service.input_resolver)
    assert counts(service) == before
    save('authority', {'changed_contract_and_code_rejected': 4,
        'changed_principal_provider_rejected': True, 'nonexact_binding_rejected': True})


def test_concurrent_intent_duplicate_and_conflict(setup, monkeypatch):
    service, raw, _, _ = setup
    before = counts(service); submit = service.jobs.submit; barrier = Barrier(2)
    def synchronized(*args, **kwargs):
        barrier.wait(timeout=20)
        return submit(*args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(service.jobs, 'submit', synchronized)
        with ThreadPoolExecutor(max_workers=2) as executor:
            a, b = list(executor.map(lambda body: service.submit('tenant-1', body), (raw, raw)))
        assert a == b and counts(service) == (before[0] + 1, before[1] + 1, before[2], before[3])
        left = json.loads(raw); left['study_id'] = 'parallel-conflict'
        right = deepcopy(left); right['rights']['declaration_id'] = 'other-valid-owned-declaration'
        def admit(body):
            try: return ('queued', service.submit('tenant-1', body)['job_id'])
            except JobIntentConflict: return ('conflict', None)
        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(admit, (_canonical(left), _canonical(right))))
        assert sorted(state for state, _ in outcomes) == ['conflict', 'queued']
    assert counts(service) == (before[0] + 2, before[1] + 2, before[2], before[3])
    save('concurrent', {'same_intent_one_job': True, 'different_content_one_job_one_conflict': True})
