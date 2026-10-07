"""Real SCRAM current farm rights for a verified context; no crop execution."""
from copy import deepcopy
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
from time import perf_counter

import psycopg
from psycopg import sql
import pytest

from app import crop_cycle_calculation_farm_binding as binding
from app import crop_cycle_calculation_context as calculation
from app import crop_cycle_input_stream as inputs
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from app.farm_authoring_storage import FarmAuthoringService
from app.thermal_run_store import _canonical
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_cycle_farm_binding import SyntheticInputRights, counts
from test_crop_cycle_input_evidence import authority
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring, request
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}], indirect=True)


def save_reference(name, value):
    directory = os.environ.get('OSSF_CALCULATION_FARM_EVIDENCE')
    if directory:
        path = Path(directory) / name
        with path.open('x') as handle:
            os.chmod(path, 0o400); json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


@pytest.fixture(scope='module', autouse=True)
def final_database_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save_reference('database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles})
    assert schemas == roles == 0


@pytest.fixture(autouse=True)
def no_crop_execution(monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('farm authority evaluated a crop result')
    monkeypatch.setattr(calculation, 'advance_chunk', forbidden)
    monkeypatch.setattr(calculation.short._Evaluator, 'rhs', forbidden)


@pytest.fixture
def setup(authoring, tmp_path):
    farms, farm_body, principal = authoring
    registered = farms.submit('tenant-1', request(farm_body))
    principal['scopes'].update(WRITE_SCOPES)
    value = shifted(); anchors = value.pop('output_times'); directory = tmp_path / 'inputs'
    packet = inputs.write_input_packet(directory, **value, anchors=anchors, outputs=anchors,
        **PROFILES, program_id='owned-verified-farm-fixture')
    for path in directory.iterdir(): path.chmod(0o400)
    server = authority(); proof = server.issue(directory, packet['root_sha256'])
    body = {'study_id': 'verified-cycle-study', 'revision': 'r1', 'farm': {
        'scenario_id': farm_body['farm']['scenario_id'], 'scenario_revision': farm_body['farm']['scenario_revision'],
        'registration_sha256': registered.scenario_sha256, 'crop_id': 'crop-1'},
        'input': {'schema_version': inputs.VERSION, 'root_sha256': packet['root_sha256'],
                  'program_id': 'owned-verified-farm-fixture'},
        'rights': {'schema_version': 'crop-cycle-input-rights-v1', 'declaration_id': 'owned-verified-input',
            'revision': 'r1', 'input_root_sha256': packet['root_sha256'],
            'available_at': farm_body['farm']['decision_at'],
            **{k: True for k in ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')},
            'redistribute': False}}
    rights = SyntheticInputRights(); service = binding.CalculationFarmBinding(farms, server, input_rights=rights)
    with calculation.open_calculation_context(directory, packet['root_sha256'], proof, authority=server) as context:
        yield service, body, context, principal, rights, directory, proof


def test_actual_scram_provenance_current_calls_and_no_new_rows(setup, monkeypatch):
    service, body, context, _, rights, _, proof = setup; before = counts(service)
    verify = service.input_authority.verify; checks = []
    def checked(*args, **kwargs): checks.append(True); return verify(*args, **kwargs)
    monkeypatch.setattr(service.input_authority, 'verify', checked)
    monkeypatch.setattr(inputs, 'open_input_packet', lambda *a, **k: pytest.fail('repeated full parser'))
    monkeypatch.setattr(calculation.legacy, 'prepare_context', lambda *a, **k: pytest.fail('repeated prepare'))
    started = perf_counter(); raw = service.prepare('tenant-1', _canonical(body), context)
    prepare_seconds = perf_counter() - started; value = json.loads(raw)
    assert _canonical(value) == raw and len(raw) <= binding.MAX_BINDING_BYTES
    assert value['version'] == 'crop-cycle-verified-farm-binding-v1'
    assert set(value) == {'version', 'scope', 'tenant_id', 'request', 'registration', 'input',
                         'rights_policy_version', 'binding_code_sha256', 'binding_dependency_sha256'}
    assert value['scope'] == 'synthetic_crop_math_only' and value['request'] == body
    assert value['binding_dependency_sha256'] == binding.DEPENDENCY_SHA256
    assert value['input']['root_sha256'] == context.reader.root_sha256
    assert value['input']['plan'] == context.reader.plan
    validation = value['input']['input_validation']
    assert set(validation) == {'context_sha256', 'evidence_sha256', 'validated_context_sha256', 'engine_version',
        'input_evidence_version', 'calculation_code_sha256', 'input_evidence_code_sha256', 'input_evidence_dependency_sha256'}
    assert validation['context_sha256'] == context.root_sha256
    assert validation['evidence_sha256'] == sha256(proof).hexdigest()
    assert validation['validated_context_sha256'] == context.manifest['input_validation']['validated_context_sha256']
    assert value['registration']['normalization'] == 'per_m2_floor'
    assert value['registration']['profile_applicability'] == 'unvalidated_for_registered_crop'
    assert value['registration']['crop']['crop_id'] == 'crop-1'
    assert value['registration']['crop']['batch_id'] and value['registration']['zone_id']
    assert value['registration']['floor_area']['unit'] == 'm²'
    assert len(checks) == 2 and [c[-1] for c in rights.calls] == ['research_calculation', 'research_display'] * 2
    checks.clear(); rights.calls.clear(); started = perf_counter()
    assert service.current('tenant-1', _canonical(body), context, raw) == raw
    current_seconds = perf_counter() - started
    assert len(checks) == 2 and [c[-1] for c in rights.calls] == ['research_display'] * 2
    assert service.current('tenant-1', _canonical(body), context, raw, write=True) == raw
    assert counts(service) == before and before[2:] == (0, 0)
    with service.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    assert not context.reader.closed
    save_reference('normal-binding.json', {'binding': value, 'binding_sha256': sha256(raw).hexdigest(),
        'binding_bytes': len(raw), 'prepare_seconds': prepare_seconds, 'current_seconds': current_seconds,
        'counts_before_after': [before, counts(service)], 'proof_checks_per_public_call': 2,
        'write_rights_observations': 4, 'read_rights_observations': 2, 'RHS_or_advance_calls': 0})


def test_current_read_and_write_scopes_and_provider_revocation(setup, monkeypatch):
    service, body, context, principal, rights, *_ = setup
    raw = service.prepare('tenant-1', _canonical(body), context); before = counts(service)
    principal['scopes'].remove('crop_result_write')
    assert service.current('tenant-1', _canonical(body), context, raw) == raw
    with pytest.raises(PermissionError): service.current('tenant-1', _canonical(body), context, raw, write=True)
    principal['scopes'].add('crop_result_write')
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): service.current('tenant-1', _canonical(body), context, raw)
        principal['scopes'].add(scope)
    rights.allowed = False
    with pytest.raises(binding.CalculationFarmBindingHold): service.current('tenant-1', _canonical(body), context, raw)
    rights.allowed = True
    source = service.farms.replay.candidates._source._source
    monkeypatch.setattr(source, 'get_input_rights', lambda *_: None)
    with pytest.raises(binding.CalculationFarmBindingHold): service.current('tenant-1', _canonical(body), context, raw)
    assert counts(service) == before and not context.reader.closed


def child_current(service, body, directory, proof, expected, queue):
    try:
        before = len(os.listdir('/proc/self/fd')); old = service.input_authority
        server = InputEvidenceAuthority(dict(old.profiles), old.notice_raw, integrity_key=old.integrity_key,
                                       issuer_id=old.issuer_id, key_id=old.key_id)
        fresh = binding.CalculationFarmBinding(FarmAuthoringService(service.farms.replay), server,
                                               input_rights=SyntheticInputRights())
        with calculation.open_calculation_context(directory, body['input']['root_sha256'], proof, authority=server) as context:
            actual = fresh.current('tenant-1', _canonical(body), context, expected)
        after = len(os.listdir('/proc/self/fd')); assert before == after
        queue.put({'raw': actual, 'pid': os.getpid(), 'FD': [before, after],
                   'context_closed_and_caches_empty': context.reader.closed and not context.reader._cache and not context._cache})
    except Exception as exc: queue.put({'error': type(exc).__name__})


def test_actual_fork_new_service_reconnection_and_fd_cleanup(setup):
    service, body, context, _, _, directory, proof = setup
    raw = service.prepare('tenant-1', _canonical(body), context)
    mp = multiprocessing.get_context('fork'); queue = mp.Queue()
    child = mp.Process(target=child_current, args=(service, body, directory, proof, raw, queue)); child.start()
    try:
        actual = queue.get(timeout=90); assert actual['raw'] == raw
        child.join(5); assert not child.is_alive() and child.exitcode == 0
        assert actual['context_closed_and_caches_empty'] and actual['FD'][0] == actual['FD'][1]
        actual.pop('raw'); save_reference('fork-binding.json', {**actual, 'actual_exit_code': child.exitcode,
            'same_binding_sha256': sha256(raw).hexdigest(), 'fresh_exec': False})
    finally:
        if child.is_alive(): child.kill(); child.join(5)
        queue.close(); queue.join_thread()
    before = len(os.listdir('/proc/self/fd'))
    for _ in range(2): assert service.current('tenant-1', _canonical(body), context, raw) == raw
    assert len(os.listdir('/proc/self/fd')) == before


def test_closed_request_and_registration_identity_errors_without_new_rows(setup):
    service, body, context, *_ = setup; before = counts(service)
    bad_raw = [_canonical(body) + b' ', b'{"x":1,"x":2}', b'{"x":NaN}', b'\xff', b'',
               b' ' * (binding.MAX_BINDING_BYTES + 1)]
    for raw in bad_raw:
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', raw, context)
    for kind in ('extra', 'root', 'program', 'rights-root', 'rights-type', 'available', 'crop', 'farm', 'identifier', 'null'):
        value = deepcopy(body)
        if kind == 'extra': value['unreviewed'] = True
        if kind == 'root': value['input']['root_sha256'] = '0' * 64
        if kind == 'program': value['input']['program_id'] = 'other-program'
        if kind == 'rights-root': value['rights']['input_root_sha256'] = '0' * 64
        if kind == 'rights-type': value['rights']['display'] = 1
        if kind == 'available': value['rights']['available_at'] = '2099-01-01T00:00:00Z'
        if kind == 'crop': value['farm']['crop_id'] = 'other-crop'
        if kind == 'farm': value['farm']['registration_sha256'] = '0' * 64
        if kind == 'identifier': value['study_id'] = 'unsafe id'
        if kind == 'null': value['input'] = None
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(value), context)
    with pytest.raises(PermissionError): service.prepare('foreign', _canonical(body), context)
    assert counts(service) == before and not context.reader.closed


def test_fixed_authority_versions_expected_bytes_and_wrong_contexts(setup, monkeypatch):
    from app.crop_cycle_input_read_context import open_input_read_context
    service, body, context, _, rights, directory, proof = setup
    raw = service.prepare('tenant-1', _canonical(body), context)
    for target, name, value in ((service, 'input_authority', object()), (service, 'farms', object()),
        (service, 'notice_raw', b'wrong'), (rights, 'policy_version', 'changed-policy'),
        (service.jobs, 'runtime_identity', (service.jobs.runtime_identity[0], 'request')),
        (binding, 'CODE_SHA256', '0' * 64),
        (service.input_authority, 'integrity_key', b'changed-owned-test-key-not-production')):
        with monkeypatch.context() as m:
            m.setattr(target, name, value)
            with pytest.raises(binding.CalculationFarmBindingHold): service.current('tenant-1', _canonical(body), context, raw)
    altered = _canonical({**json.loads(raw), 'tenant_id': 'foreign'})
    with pytest.raises(binding.CalculationFarmBindingHold): service.current('tenant-1', _canonical(body), context, altered)
    old = service.input_authority
    other = InputEvidenceAuthority(dict(old.profiles), old.notice_raw, integrity_key=old.integrity_key,
                                   issuer_id=old.issuer_id, key_id=old.key_id)
    with calculation.open_calculation_context(directory, body['input']['root_sha256'], proof, authority=other) as foreign:
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(body), foreign)
        assert not foreign.reader.closed
    with inputs.open_input_packet(directory, body['input']['root_sha256'], **PROFILES) as reader:
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(body), reader)
        original = calculation.legacy.prepare_context(reader, **PROFILES)
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(body), original)
    with open_input_read_context(directory, body['input']['root_sha256'], proof, authority=old) as read_only:
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(body), read_only)
        assert not read_only.reader.closed
    closed = calculation.open_calculation_context(directory, body['input']['root_sha256'], proof, authority=old)
    closed.close()
    with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(body), closed)
    assert not context.reader.closed


def test_callback_revocation_and_declaration_changes_cannot_return(setup, monkeypatch):
    service, body, context, principal, rights, *_ = setup
    raw = service.prepare('tenant-1', _canonical(body), context); before = counts(service)
    call = rights.__class__.__call__; source = service.farms.replay.candidates._source._source
    for kind in ('read-rights', 'write-rights', 'source', 'scope', 'declaration'):
        calls = []
        with monkeypatch.context() as m:
            def changed(self, tenant, declaration, root, use):
                answer = call(self, tenant, declaration, root, use); calls.append(use)
                if len(calls) == 1:
                    if kind in ('read-rights', 'write-rights'): self.allowed = False
                    elif kind == 'source': m.setattr(source, 'get_input_rights', lambda *_: None)
                    elif kind == 'scope': principal['scopes'].remove('crop_result_read')
                    else: declaration['display'] = False
                return answer
            m.setattr(rights.__class__, '__call__', changed)
            try:
                with pytest.raises((binding.CalculationFarmBindingHold, PermissionError)):
                    service.current('tenant-1', _canonical(body), context, raw, write=kind == 'write-rights')
            finally:
                rights.allowed = True; principal['scopes'].add('crop_result_read')
        assert not context.reader.closed
    assert counts(service) == before


@pytest.mark.parametrize('kind', ['root', 'blob', 'mode', 'symlink'])
def test_current_input_changes_close_invalid_context_and_prevent_binding(setup, kind):
    service, body, context, _, _, directory, _ = setup
    raw = service.prepare('tenant-1', _canonical(body), context); before = counts(service)
    target = directory / 'root.json' if kind == 'root' else next(p for p in directory.iterdir() if p.name != 'root.json')
    if kind in ('root', 'blob'):
        target.chmod(0o600); target.write_bytes(target.read_bytes() + b' '); target.chmod(0o400)
    elif kind == 'mode': directory.chmod(0o755)
    else:
        outside = directory.parent / 'outside-owned-file'; outside.write_bytes(target.read_bytes())
        outside.chmod(0o400); target.unlink(); target.symlink_to(outside)
    before_fd = len(os.listdir('/proc/self/fd'))
    with pytest.raises(binding.CalculationFarmBindingHold): service.current('tenant-1', _canonical(body), context, raw)
    assert context.reader.closed and not context._cache and not context.reader._cache
    assert len(os.listdir('/proc/self/fd')) == before_fd - 1 and counts(service) == before


def test_input_change_in_last_policy_callback_is_rechecked_before_return(setup, monkeypatch):
    service, body, context, _, rights, directory, _ = setup
    raw = service.prepare('tenant-1', _canonical(body), context); call = rights.__class__.__call__; calls = []
    def changed(self, *args):
        answer = call(self, *args); calls.append(True)
        if len(calls) == 2:
            target = directory / 'root.json'; target.chmod(0o600)
            target.write_bytes(target.read_bytes() + b' '); target.chmod(0o400)
        return answer
    monkeypatch.setattr(rights.__class__, '__call__', changed)
    with pytest.raises(binding.CalculationFarmBindingHold): service.current('tenant-1', _canonical(body), context, raw)
    assert len(calls) == 2 and context.reader.closed


def test_input_period_outside_registered_occupancy_is_rejected(setup, tmp_path):
    from test_crop_cycle_artifact import program
    service, body, _, _, _, _, _ = setup
    value = program('empty-entry'); anchors = value.pop('output_times'); directory = tmp_path / 'outside-period'
    packet = inputs.write_input_packet(directory, **value, anchors=anchors, outputs=anchors,
        **PROFILES, program_id='outside-period')
    for path in directory.iterdir(): path.chmod(0o400)
    server = service.input_authority; proof = server.issue(directory, packet['root_sha256'])
    value = deepcopy(body); value['input'].update(root_sha256=packet['root_sha256'], program_id='outside-period')
    value['rights']['input_root_sha256'] = packet['root_sha256']
    with calculation.open_calculation_context(directory, packet['root_sha256'], proof, authority=server) as context:
        with pytest.raises(binding.CalculationFarmBindingHold): service.prepare('tenant-1', _canonical(value), context)
