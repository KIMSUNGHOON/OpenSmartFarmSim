"""Manual registered calculation measurements; synthetic software evidence only."""
from copy import deepcopy
from datetime import datetime, timedelta
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import psycopg
import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_input_evidence import InputEvidenceAuthority
from app import crop_cycle_calculation_server_custody as custody
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from test_api_crop_cycle_calculation_tls import Inputs, SERVER_KEY, DB_KEY
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope, counts
from test_crop_cycle_artifact import PROFILES
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_input_evidence import authority
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring, request as farm_request
from test_farm_replay_scenario import farm_setup
from login_database import login_database

ROOT = Path(__file__).resolve().parents[2]
POLICY = {'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}


def save(name, value):
    directory = os.environ.get('OSSF_CALCULATION_PREFIX_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400); json.dump(value, handle, sort_keys=True, indent=2)
            handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def tree(directory):
    return {str(p.relative_to(directory)): (sha256(p.read_bytes()).hexdigest(), p.stat().st_mode,
        p.stat().st_dev, p.stat().st_ino) for p in directory.rglob('*') if p.is_file()}


@pytest.fixture(scope='module')
def audit_native(login_database, tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
        data = Path(conn.execute('SHOW data_directory').fetchone()[0])
    passfiles = list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    methods = [line.split()[-1] for line in (data/'pg_hba.conf').read_text().splitlines()
        if line.strip().startswith('host')]
    assert schemas == roles == len(passfiles) == 0 and set(methods) == {'scram-sha-256'}
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles, 'passfiles': len(passfiles),
        'actual_host_auth_methods': methods})


@pytest.fixture
def registered_case(audit_native, authoring, tmp_path):
    farms, farm_body, principal = authoring
    registered = farms.submit('tenant-1', farm_request(farm_body))
    principal['scopes'].update(WRITE_SCOPES)
    input_authority = authority(); rights = SyntheticInputRights(); inputs = Inputs(); packets = {}
    binding = CalculationFarmBinding(farms, input_authority, input_rights=rights)
    farm = {'scenario_id': farm_body['farm']['scenario_id'], 'scenario_revision': farm_body['farm']['scenario_revision'],
        'registration_sha256': registered.scenario_sha256, 'crop_id': 'crop-1'}
    def build(program, name):
        key = sha256(engine._canonical(program)).hexdigest()
        if key not in packets:
            value = deepcopy(program); anchors = value.pop('output_times'); directory = tmp_path/('inputs-'+name)
            packet = engine.inputs.write_input_packet(directory, **value, anchors=anchors, outputs=anchors,
                **PROFILES, program_id='owned-registered-prefix-v1')
            for path in directory.iterdir(): path.chmod(0o400)
            proof = input_authority.issue(directory, packet['root_sha256'])
            inputs.values[packet['root_sha256']] = (directory, proof)
            packets[key] = directory, packet
        directory, packet = packets[key]
        body = {'study_id': 'owned-prefix-'+name, 'revision': 'r1', 'farm': farm,
            'input': {'schema_version': engine.inputs.VERSION, 'root_sha256': packet['root_sha256'],
                'program_id': 'owned-registered-prefix-v1'},
            'rights': {'schema_version': 'crop-cycle-input-rights-v1', 'declaration_id': 'owned-prefix-'+name,
                'revision': 'r1', 'input_root_sha256': packet['root_sha256'],
                'available_at': farm_body['farm']['decision_at'], 'redistribute': False,
                **{k: True for k in ('ownership_asserted', 'access', 'store', 'transform', 'use', 'display')}}}
        root = tmp_path/('server-'+name); root.mkdir(mode=0o700)
        server = custody.CalculationServerCustody(binding, root, input_resolver=inputs, integrity_key=SERVER_KEY)
        return server, engine._canonical(body), directory
    yield build, binding, rights, principal
    assert all(c.reader.closed and not c._cache and not c.reader._cache for c in inputs.opened)


@pytest.fixture(scope='module')
def driver():
    path = ROOT / 'research/crop-cycle-calculation-prefix-cost.py'
    spec = importlib.util.spec_from_file_location('calculation_prefix_cost', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_observer_restores_real_functions_after_error_and_keeps_nested_costs_separate(driver):
    targets = [(engine, 'open_calculation_context'), (InputEvidenceAuthority, 'verify'),
        (artifact._Files, '_load_prefix'), (CalculationFarmBinding, 'current'),
        (engine.short._Evaluator, 'rhs'), (engine, '_canonical')]
    original = [getattr(owner, name) for owner, name in targets]
    with pytest.raises(RuntimeError, match='own observation failure'):
        with driver.observation() as costs:
            assert all(getattr(owner, name) is not fn
                for (owner, name), fn in zip(targets, original))
            with costs.measure('outer'):
                assert engine._canonical({'own': 1}) == b'{"own":1}'
                raise RuntimeError('own observation failure')
    assert all(getattr(owner, name) is fn
        for (owner, name), fn in zip(targets, original))
    assert not costs.stack
    assert costs.values['outer']['calls'] == costs.values['json.canonical']['calls'] == 1
    for metric in costs.values.values():
        assert metric['wall_seconds'] >= metric['exclusive_wall_seconds'] >= 0
        assert metric['cpu_seconds'] >= metric['exclusive_cpu_seconds'] >= 0


@pytest.mark.parametrize('budget', [None, {}, {'max_steps': True, 'max_transitions': 1},
    {'max_steps': 0, 'max_transitions': 1}, {'max_steps': -1, 'max_transitions': 1},
    {'max_steps': 10001, 'max_transitions': 1}, {'max_steps': 1, 'max_transitions': True},
    {'max_steps': 1, 'max_transitions': 0}, {'max_steps': 1, 'max_transitions': 129},
    {'max_steps': 1, 'max_transitions': 1, 'extra': 1}])
def test_invalid_budget_rejected_before_server_access_or_rhs(driver, budget, monkeypatch):
    def forbidden(*args, **kwargs): pytest.fail('invalid quota reached crop calculation')
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', forbidden)
    with pytest.raises(ValueError):
        driver.profile_registered_prefix(None, b'{}', tenant='tenant-1', budget=budget)


@pytest.mark.parametrize('field,value', [('max_advances', True), ('max_advances', 0),
    ('max_advances', 33), ('wall_budget_seconds', True), ('wall_budget_seconds', 0),
    ('wall_budget_seconds', 1201)])
def test_invalid_observation_limit_rejected_before_server_access(driver, field, value):
    with pytest.raises(ValueError):
        driver.profile_registered_prefix(None, b'{}', tenant='tenant-1',
            budget={'max_steps': 1, 'max_transitions': 1}, **{field: value})


@pytest.mark.parametrize('original_login_scope', [POLICY], indirect=True)
@pytest.mark.parametrize('kind', ['normal', 'hold'])
def test_actual_registered_one_and_bounded_calls_preserve_original_then_publish_without_rhs(
        driver, registered_case, monkeypatch, kind):
    build, binding, rights, principal = registered_case
    program = shifted('full-removal-reentry')
    if kind == 'hold': program['events'][1]['removals']['values']['leaf']['value'] = 1e6
    expected = engine.physical.integrate_plant_startup(**deepcopy(program), **PROFILES)
    assert expected['status'] == ('completed' if kind == 'normal' else 'hold')
    before = counts(binding); profiles = []; publications = []; saved = []
    original_rhs = engine.short._Evaluator.rhs
    for name, budget in [('one', {'max_steps': 10000, 'max_transitions': 128}),
                         ('bounded', {'max_steps': 17, 'max_transitions': 31})]:
        server, raw, directory = build(program, name); input_before = tree(directory); observed = []
        def sink(row):
            observed.append(row); save(f'{kind}-{name}-advance-{len(observed)}.json', row)
        report = driver.profile_registered_prefix(server, raw, tenant='tenant-1', budget=budget, on_advance=sink)
        assert report['growth_curve'] == observed and report['stop_reason'] == 'terminal'
        assert report['last_progress']['status'] == expected['status']
        assert report['last_progress']['steps'] == expected['steps']
        assert report['fresh_service_checkpoint_exact'] and report['read_rhs_calls'] == 0
        assert report['descriptors_before'] == report['descriptors_after']
        assert engine.short._Evaluator.rhs is original_rhs and tree(directory) == input_before
        if kind == 'normal': assert len(report['checkpoint']['y']) == 121
        def forbidden(*args, **kwargs): pytest.fail('publication, current read or used intent ran RHS')
        immutable = tree(server.directory); store = CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
        with monkeypatch.context() as no_math:
            no_math.setattr(engine.short._Evaluator, 'rhs', forbidden)
            publication = driver.profile_publication(store, raw, tenant='tenant-1')
            assert publication['checkpoint'] == report['checkpoint']
            assert publication['put_retry_read_rhs_calls'] == 0 and publication['same_retry_and_get_record']
            assert publication['descriptors_before'] == publication['descriptors_after']
            for rows in ('samples', 'events'):
                digest = sha256(b''.join(engine._canonical(row)+b'\n' for row in expected[rows])).hexdigest()
                assert publication['row_sha256'][rows] == digest
                assert publication['counts'][rows] == len(expected[rows])
            assert publication['hold'] == expected.get('hold')
            assert publication['last_confirmed'] == expected.get('last_confirmed')
            with pytest.raises(ValueError, match='unused execution intent'):
                driver.profile_registered_prefix(server, raw, tenant='tenant-1', budget=budget)
        assert tree(server.directory) == immutable and tree(directory) == input_before
        profiles.append(report); publications.append(publication); saved.append((server, raw, directory, immutable))
        save(f'{kind}-{name}-profile.json', {'calculation': report, 'publication': publication})
    assert profiles[0]['last_progress']['input_root_sha256'] == profiles[1]['last_progress']['input_root_sha256']
    semantics = [driver._PROFILE._semantics({'checkpoint': value['checkpoint']}) for value in profiles]
    assert semantics[0] == semantics[1]
    assert publications[0]['row_sha256'] == publications[1]['row_sha256']
    server, raw, directory, immutable = saved[0]; store = CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
    farm = json.loads(raw)['farm']; result_id = publications[0]['result_id']
    with monkeypatch.context() as no_math:
        no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('withdrawal ran RHS'))
        rights.allowed = False
        try:
            with pytest.raises(custody.CalculationCustodyHold): store.get('tenant-1', result_id, farm)
        finally: rights.allowed = True
        principal['scopes'].remove('crop_result_read')
        try:
            with pytest.raises(PermissionError): store.get('tenant-1', result_id, farm)
        finally: principal['scopes'].add('crop_result_read')
    with binding.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    assert tree(server.directory) == immutable and counts(binding) == (*before[:4], before[4]+2)
    save(kind+'-verified.json', {'actual_scram': True, 'status': expected['status'], 'steps': expected['steps'],
        'same_original_rows_state_seed_clock_and_cumulative': True, 'current_rights_and_principal_denied': True,
        'immutable_files_preserved': True, 'row_counts_before_after': [before, counts(binding)],
        'scope': 'owned_synthetic_registered_small_measurement_only', 'full166day_accepted': False})


@pytest.mark.parametrize('original_login_scope', [POLICY], indirect=True)
def test_actual_25h_prefix_cost_keeps_yielded_checkpoint_and_original_confirmed_rows(driver, registered_case, monkeypatch):
    build, binding, rights, principal = registered_case
    path = ROOT/'research/crop-cycle-stream-execution-reference.py'
    spec = importlib.util.spec_from_file_location('own_registered_prefix_reference', path)
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    program = reference.long_program()
    def stamp(value):
        return (datetime.fromisoformat(value.replace('Z', '+00:00'))+timedelta(days=273)).isoformat().replace('+00:00', 'Z')
    for segment in program['segments']:
        for key in ('start', 'end'): segment[key] = stamp(segment[key])
    for event in program['events']: event['at'] = stamp(event['at'])
    program['output_times'] = [stamp(value) for value in program['output_times']]
    fixture = ROOT/'web/e2e/calculation-cycle-crop-recorded-responses.json'
    assert sha256(fixture.read_bytes()).hexdigest() == 'a2d3e197b352bc51ab1dd66f520f38912032bb9a9e705733eb89919e47f4a80b'
    recorded = json.loads(fixture.read_text())['long']
    expected = {kind: [deepcopy(row) for response in recorded if response.get('page')
        and response['page']['kind'] == kind for row in response['page']['records']] for kind in ('samples', 'events')}
    for rows in expected.values():
        for row in rows: row['at'] = stamp(row['at'])
    for row, event in zip(expected['events'], program['events'], strict=True):
        assert row['at'] == event['at']
        row['input_id'] = event['removals']['input_id']
    server, raw, directory = build(program, 'long'); before = counts(binding); immutable_input = tree(directory)
    observed = []
    def sink(row):
        observed.append(row); save('long-advance-'+str(len(observed))+'.json', row)
    report = driver.profile_registered_prefix(server, raw, tenant='tenant-1',
        budget={'max_steps': 10000, 'max_transitions': 128}, max_advances=32, on_advance=sink)
    assert report['growth_curve'] == observed and len(observed) == 32 and report['stop_reason'] == 'advance_limit'
    assert report['last_progress']['status'] == 'yielded'
    assert 0 < report['last_progress']['steps'] < report['last_progress']['planned_steps'] == 11400
    assert report['read_rhs_calls'] == 0 and report['fresh_service_checkpoint_exact']
    assert report['descriptors_before'] == report['descriptors_after']
    assert report['costs']['rhs']['calls'] > 0 and report['costs']['artifact.prefix_verify']['calls'] > 32
    immutable = tree(server.directory)
    with monkeypatch.context() as no_math:
        no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('prefix read ran RHS'))
        with server._open('tenant-1', raw, False) as journal:
            head, _ = journal.writer._head()
            _, checkpoint, summary, index, count = journal.writer._load_prefix(journal.context, journal.notice, head)
            assert checkpoint == report['checkpoint'] and summary['status'] == 'yielded'
            for kind in ('samples', 'events'):
                rows = []
                for descriptor in index[kind]:
                    page, _ = journal.writer._records([{k: v for k, v in descriptor.items() if k != 'start'}])
                    rows.extend(page)
                assert rows == expected[kind][:count[kind]] and len(rows) == count[kind]
        store = CalculationCycleCropResultStore(server, integrity_key=DB_KEY)
        with pytest.raises(custody.CalculationCustodyHold): store.put('tenant-1', raw)
        rights.allowed = False
        try:
            with pytest.raises(custody.CalculationCustodyHold): server.inspect('tenant-1', raw)
        finally: rights.allowed = True
        principal['scopes'].remove('crop_result_read')
        try:
            with pytest.raises(PermissionError): server.inspect('tenant-1', raw)
        finally: principal['scopes'].add('crop_result_read')
    assert tree(server.directory) == immutable and tree(directory) == immutable_input and counts(binding) == before
    save('long-prefix-verified.json', {'calculation': report, 'original_confirmed_rows_equal': True,
        'yielded_not_published': True, 'current_rights_and_principal_denied': True,
        'input_and_result_files_preserved': True, 'row_counts_before_after': [before, counts(binding)],
        'full166day_accepted': False, 'gates': 'not_assessed'})
