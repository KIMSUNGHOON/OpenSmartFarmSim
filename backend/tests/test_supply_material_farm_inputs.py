"""Actual owned Farm inputs and genuine original seed lineage; synthetic QA only."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from fractions import Fraction
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import socket
import subprocess
import sys
from threading import Barrier, Event, local

import pytest
from psycopg import Connection, sql

from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.crop_morphology_artifact_io import MorphologyBlobStore
from app.farm_authoring_storage import FarmAuthoringRequest
from app import crop_leaf_carbon_stock_artifact_reader as carbon
from app import crop_stem_root_initial_binding as initial
from app.crop_leaf_carbon_stock_artifact_producer import produce_leaf_carbon_stock_artifact
from app.crop_rational_morphology_artifact_producer import produce_rational_morphology_artifact
from app.job_store import JobIntentConflict
from login_database import login_database, login_scope
import morphology_farm_factory as factory
from test_crop_leaf_carbon_stock_artifact import inputs as carbon_inputs, profiles, ACCESS


ROOT = Path(__file__).resolve().parents[2]
PROFILE = {'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}
PG = pytest.mark.parametrize('login_scope', [PROFILE], indirect=True)
DECISION = datetime(2026, 10, 25, tzinfo=timezone.utc)
AVAILABLE = '2026-10-31T00:00:00Z'
RETRIEVED = '2026-10-31T00:01:00Z'


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode()


def feature():
    return import_module('app.crop_supply_material_farm_inputs')


def seed_feature():
    return import_module('app.crop_supply_material_farm_seed')


def source_packet():
    source = carbon_inputs(0, dt=.125, count=1)
    identifier = 'own-material-farm-seed-QA'
    source['input_id'] = source['program']['input_id'] = identifier
    source['program']['scenario']['input_id'] = identifier
    stem = json.loads((ROOT/'web/public/morphology-rational-replay/input.json').read_bytes())
    stem['program_id'] = identifier+'-stem'
    stem['output_times'] = ['2026-10-01T00:00:01Z']
    stem['segments'][0]['end_utc'] = stem['output_times'][-1]
    individual = deepcopy(source['program'])
    individual['scenario']['plant_state'].pop('stem_root')
    individual['scenario']['removals'].pop('stem_root')
    individual['stem_root_stock_policy'] = initial.crop.short.stock.POLICY_ID
    identifiers = [node['length_state']['clock_state']['internode_id']
        for node in stem['initial_state']['internodes']]
    individual['stem_root_compartments'] = [
        {'compartment_id': name, 'kind': 'root_system' if i == 0 else 'internode',
            'initial_carbon': {'value': amount, 'unit': 'mg_CH2O/m2_floor'},
            'sink_weight': {'value': i+1., 'unit': '1'},
            'carbon_removal': {'value': 0., 'unit': 'mg_CH2O/m2_floor/s'}}
        for i, (name, amount) in enumerate(zip(['explicit-root', *identifiers],
            [2000., 4000., 6000., 8000.], strict=True))]
    return {'carbon_stock_inputs': source, 'stem_program': stem, 'stem_start_index': -1,
        'individual_program': individual, 'numerical': {'step_seconds': .125, 'step_count': 1},
        'tracking_basis': {'kind': initial.BASIS, 'shoot_id': 'synthetic-shoot',
            'model_floor_area': deepcopy(individual['model_floor_area']),
            'tracked_shoot_count': {'value': 1, 'unit': 'tracked_shoot'}},
        'profile_sha256': dict(carbon.PROFILE_SHA)}


def request_for(farm_body, registration_sha256):
    return {'schema_version': 'supply-material-farm-input-request-v1',
        'study_id': 'own-material-farm-seed-QA', 'revision': 'r1',
        'farm': {'scenario_id': farm_body['farm']['scenario_id'],
            'scenario_revision': farm_body['farm']['scenario_revision'],
            'registration_sha256': registration_sha256, 'crop_id': 'crop-1',
            'zone_id': farm_body['farm']['facility']['zone_id']},
        'source': source_packet(),
        'rights': {'schema_version': 'supply-material-farm-input-rights-v1',
            'declaration_id': 'owned-material-input-rights', 'revision': 'r1',
            **dict.fromkeys(('ownership_asserted', 'access', 'store', 'transform', 'use', 'display'), True),
            'redistribute': False, 'available_at': AVAILABLE,
            'reviewer': 'native-software-QA-not-farm-validation'},
        'provenance': {'origin': 'own_declared_synthetic_assumptions',
            'product_id': 'own-material-farm-seed-QA', 'source_ref': 'urn:ossf:own-material-farm-seed-QA',
            'revision': 'r1', 'observed_at': None, 'published_at': None,
            'available_at': AVAILABLE, 'retrieved_at': RETRIEVED,
            'qc': 'software_contract_only_not_farm_measurements',
            'reviewer': 'native-software-QA-not-farm-validation'}}


@pytest.fixture
def registered(login_scope, monkeypatch):
    farms, body, principal = factory.create_farm(login_scope, monkeypatch, DECISION)
    body['farm']['facility']['floor_area']['value'] = '1'
    body['farm']['facility']['cultivable_area']['value'] = '1'
    body['farm']['crops'][0]['area']['value'] = '1'
    registration = farms.submit('tenant-1', FarmAuthoringRequest.model_validate_json(raw(body)))
    principal['scopes'].update(set(WRITE_SCOPES) | {'simulation_create', 'cancel'})
    return farms, request_for(body, registration.scenario_sha256), principal, body


def counts(jobs):
    with jobs.connect() as conn:
        return tuple(conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
            jobs._table(name))).fetchone()['n']
            for name in ('jobs', 'job_events', 'job_publications'))


def original_seed(directory, packet, reference_profiles):
    directory.mkdir(mode=0o750)
    cd, sd = directory/'carbon', directory/'stem'
    cr = produce_leaf_carbon_stock_artifact(cd, ACCESS,
        inputs_raw=raw(packet['carbon_stock_inputs']), **reference_profiles)
    sr = produce_rational_morphology_artifact(sd, ACCESS, program_raw=raw(packet['stem_program']))
    context = initial.crop.prepare_context(program=packet['individual_program'],
        **packet['numerical'], **reference_profiles)
    cm = carbon.read_leaf_carbon_stock_manifest(cd, ACCESS, cr)
    sm = initial.stem.read_rational_morphology_manifest(sd, ACCESS, sr)
    declaration = {'schema_version': 'stem-root-initial-source-binding-input-v1',
        'input_id': 'own-material-seed-original-oracle', 'origin': 'synthetic',
        'context_sha256': context.root_sha256, 'crop_root_sha256': cr,
        'crop_initial_state_sha256': cm['initial_state_sha256'], 'stem_root_sha256': sr,
        'stem_start_index': packet['stem_start_index'], 'stem_source_state_sha256': sm['initial_state_sha256'],
        'time_origin_utc': cm['time_origin_utc'],
        'model_floor_area': deepcopy(packet['individual_program']['model_floor_area']),
        'tracking_basis': deepcopy(packet['tracking_basis']),
        'rights': deepcopy(packet['carbon_stock_inputs']['rights']),
        'reviewer': 'native-software-QA-not-farm-validation'}
    binding = initial.bind_initial_stem_carbon(context, cd, sd, ACCESS,
        crop_root_sha256=cr, stem_root_sha256=sr, stem_start_index=-1, declaration=declaration)
    assert binding['balance']['carbon']['once_rounded_matches_source'] is True
    assert binding['balance']['removal']['once_rounded_matches_source'] is True
    return cr, sr, context, binding


@PG
def test_actual_owned_Farm_input_drives_genuine_seed_and_preserves_original_artifacts(
        registered, profiles, tmp_path):
    farms, body, principal, farm_body = registered
    jobs = farms.replay.jobs
    assert len(raw(body)) < 65536
    assert farm_body['farm']['facility']['floor_area']['value'] == '1'
    assert body['source']['individual_program']['model_floor_area'] == {'value': 1.0, 'unit': 'm2_floor'}
    oracle = original_seed(tmp_path/'original-oracle', body['source'], profiles)
    with jobs.connect() as conn:
        assert conn.pgconn.used_password
    module = feature()
    service = module.MaterialFarmInputService(farms)
    before = counts(jobs)
    status = service.submit('tenant-1', raw(body))
    job_id = str(status.job_id)
    row = jobs.get_job('tenant-1', status.job_id)
    checked = service.current('tenant-1', job_id, row['input_sha256'])
    payload = json.loads(checked.input_bytes)
    assert set(payload) == {'input_version', 'tenant_id', 'request', 'content_witness', 'content_witness_sha256'}
    assert payload['request'] == checked.request == body
    assert len(checked.input_bytes) <= 65536 and sha256(checked.input_bytes).hexdigest() == row['input_sha256']
    assert payload['input_version'] == 'supply-material-owned-input-v1'
    assert payload['content_witness_sha256'] == sha256(raw(payload['content_witness'])).hexdigest()
    content = payload['content_witness']
    assert content['normalization']['mapping_version'] == 'same_registered_single_zone_floor_v1'
    assert content['time_scope']['assumption_mode'] == 'supplemental_ex_post_synthetic_material_assumptions'
    assert content['time_scope']['declared_availability_vs_farm_decision'] == 'after'
    assert content['time_scope']['ex_ante_validity'] == 'not_established'
    assert content['time_scope']['carbon_duration_seconds_exact'] == {'numerator': '1', 'denominator': '8', 'unit': 's'}
    assert content['time_scope']['individual_duration_seconds_exact'] == {'numerator': '1', 'denominator': '8', 'unit': 's'}
    assert content['farm'] == body['farm'] and content['registration']['registration_sha256'] == body['farm']['registration_sha256']
    for name in ('carbon_stock_inputs', 'stem_program', 'individual_program'):
        assert content['components'][name]['sha256'] == sha256(raw(body['source'][name])).hexdigest()
        assert content['components'][name]['bytes'] == len(raw(body['source'][name]))
    assert set(checked.witness['owned_input']) == {'job_id', 'input_version', 'input_sha256', 'created_at', 'stage', 'state'}
    assert checked.witness['owned_input']['job_id'] == job_id
    assert checked.witness['owned_input']['input_sha256'] == row['input_sha256']
    assert checked.witness['owned_input']['stage'] == 'collection'
    assert checked.witness['owned_input']['state'] == 'queued'
    recorded = datetime.fromisoformat(checked.witness['owned_input']['created_at'].replace('Z', '+00:00'))
    assert recorded == status.created_at and recorded > DECISION
    assert service.submit('tenant-1', raw(body)) == status
    assert counts(jobs) == (before[0]+1, before[1]+1, before[2])
    seed_module = seed_feature()
    workspace = tmp_path/'owned-seed'
    workspace.mkdir(mode=0o750)
    producer = seed_module.MaterialFarmSeedProducer(service, workspace, ACCESS)
    seed = producer.produce('tenant-1', job_id, row['input_sha256'])
    assert seed.carbon_root_sha256 == oracle[0] and seed.stem_root_sha256 == oracle[1]
    assert type(seed.context) is initial.crop.Context
    assert (seed.context._request, seed.context._program, seed.context._seed, seed.context._manifest) == (
        oracle[2]._request, oracle[2]._program, oracle[2]._seed, oracle[2]._manifest)
    binding = json.loads(seed.initial_binding_bytes)
    assert raw(binding) == seed.initial_binding_bytes
    assert binding['context_sha256'] == seed.context.root_sha256
    assert binding['crop_selection']['root_sha256'] == seed.carbon_root_sha256
    assert binding['stem_selection']['root_sha256'] == seed.stem_root_sha256
    assert binding['initial_inventory'] == body['source']['individual_program']['stem_root_compartments']
    assert binding['initial_inventory'] == oracle[3]['initial_inventory']
    assert binding['basis_receipt']['perplant_mass_conversion'] == 'not_performed'
    assert binding['basis_receipt']['biological_density_validation'] == 'not_assessed'
    assert binding['redistribution_authorized'] is False and binding['G0_G4'] == 'not_assessed'
    witness = seed.witness
    assert witness['farm'] == body['farm'] and witness['owned_input'] == checked.witness['owned_input']
    assert witness['resolved_witness_sha256'] == sha256(raw(checked.witness)).hexdigest()
    assert witness['source']['initial_binding_sha256'] == sha256(seed.initial_binding_bytes).hexdigest()
    assert witness['source']['individual_context_sha256'] == seed.context.root_sha256
    assert witness['producer']['version'] == 'supply-material-farm-seed-v1'
    assert sha256(Path(seed_module.__file__).read_bytes()).hexdigest() in witness['producer']['code_sha256'].values()
    assert witness['producer']['original_dependency_sha256'] == {
        'carbon_stock': carbon.read_leaf_carbon_stock_manifest(workspace/row['input_sha256']/'carbon', ACCESS,
            seed.carbon_root_sha256)['code_sha256'],
        'stem': initial.stem.read_rational_morphology_manifest(workspace/row['input_sha256']/'stem', ACCESS,
            seed.stem_root_sha256)['code_sha256']}
    assert witness['scope'] == 'synthetic_farm_bound_initial_inputs_only'
    assert witness['profile_applicability'] == 'unvalidated_for_registered_crop'
    assert witness['ex_ante_validity'] == 'not_established' and witness['recording_vs_farm_decision'] == 'after'
    assert witness['effective_rights'] == {'use': True, 'display': True, 'redistribute': False}
    assert jobs.get_publication('tenant-1', status.job_id) is None
    assert counts(jobs) == (before[0]+1, before[1]+1, before[2])
    assert module.MaterialFarmInputService(farms).current('tenant-1', job_id, row['input_sha256']).witness == checked.witness
    proof = {'version': 'owned-material-farm-seed-proof-v1', 'synthetic': True,
        'farm': body['farm'], 'job_id': job_id, 'input_sha256': row['input_sha256'],
        'immutable_input_bytes': len(checked.input_bytes), 'actual_created_at': recorded.isoformat(),
        'content_witness_sha256': payload['content_witness_sha256'],
        'carbon_root_sha256': seed.carbon_root_sha256, 'stem_root_sha256': seed.stem_root_sha256,
        'original_bulk_roots_equal': True, 'context_sha256': seed.context.root_sha256,
        'initial_binding_sha256': sha256(seed.initial_binding_bytes).hexdigest(),
        'original_Farm_decision_at': DECISION.isoformat(), 'declared_available_at': AVAILABLE,
        'input_witness': checked.witness, 'seed_witness': seed.witness,
        'DB_simulation_publication': None, 'G0_G4': 'not_assessed', 'R2': 'not_approved'}
    (tmp_path/'owned-material-farm-seed-proof-v1.private.json').write_bytes(raw(proof))
    (tmp_path/'owned-material-farm-request-v1.private.json').write_bytes(raw(body))
    (tmp_path/'owned-material-farm-input-v1.private.json').write_bytes(checked.input_bytes)
    (tmp_path/'owned-material-farm-initial-binding-v1.private.json').write_bytes(seed.initial_binding_bytes)


def declared_request():
    return request_for({'farm': {'scenario_id': 'farm-1', 'scenario_revision': 'r1',
        'facility': {'zone_id': 'zone-1'}}}, 'a'*64)


def renamed(body, suffix):
    value = deepcopy(body)
    value['study_id'] += suffix
    value['provenance']['product_id'] = value['study_id']
    return value


def model_codes():
    leaf = import_module('app.crop_leaf_carbon_stock_continuation')
    inventory = import_module('app.crop_rational_shoot_inventory')
    return {fn.__code__: name for name, fn in (
        ('carbon_context', leaf.prepare_context), ('carbon_start', leaf.start),
        ('carbon_advance', leaf.advance_chunk), ('individual_context', initial.crop.prepare_context),
        ('individual_prepare', initial.crop.short._prepare),
        ('individual_advance', initial.crop.advance_chunk),
        ('stem_advance', inventory.advance_rational_shoot_internode_inventory),
        ('initial_binding', initial.bind_initial_stem_carbon),
        ('old_carbon_bulk', produce_leaf_carbon_stock_artifact),
        ('old_stem_bulk', produce_rational_morphology_artifact),
        ('store_open', MorphologyBlobStore.__init__), ('CAS_put', MorphologyBlobStore.put))}


@contextmanager
def observed_codes(*, extra=None, event=None):
    codes = model_codes()
    codes.update(extra or {})
    counts = Counter({name: 0 for name in codes.values()})
    prior = sys.getprofile()
    def observe(frame, kind, value):
        name = codes.get(frame.f_code)
        if name is not None:
            if kind == 'call': counts[name] += 1
            if event is not None: event(name, kind, frame, value)
    sys.setprofile(observe)
    try:
        yield counts
    finally:
        sys.setprofile(prior)


def stored_files(directory):
    return {str(path.relative_to(directory)): sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob('*') if path.is_file()}


@pytest.fixture
def owned(registered):
    farms, body, principal, farm_body = registered
    service = feature().MaterialFarmInputService(farms)
    status = service.submit('tenant-1', raw(body))
    row = service.jobs.get_job('tenant-1', status.job_id)
    checked = service.current('tenant-1', str(status.job_id), row['input_sha256'])
    return service, body, principal, status, checked


def producer_for(owned, directory):
    directory.mkdir(mode=0o750)
    producer = seed_feature().MaterialFarmSeedProducer(owned[0], directory, ACCESS)
    return producer, str(owned[3].job_id), owned[4].witness['owned_input']['input_sha256']


def test_pure_closed_request_retains_complete_original_source_types_and_values():
    body = declared_request()
    with observed_codes() as calls:
        parsed = feature()._request(raw(body))
    assert parsed == body and raw(parsed) == raw(body) and not any(calls.values())
    assert type(parsed['source']['numerical']['step_seconds']) is float
    assert type(parsed['source']['numerical']['step_count']) is int
    assert len(parsed['source']['carbon_stock_inputs']['program']['scenario']['cohort_state']['fruit_carbohydrate']) == 50
    assert parsed['provenance']['observed_at'] is parsed['provenance']['published_at'] is None


@pytest.mark.parametrize('fault', ['tenant', 'directory', 'source_root', 'opaque_source',
    'bool_step', 'bool_count', 'bool_index', 'two_shoots', 'wrong_floor_unit', 'profile',
    'individual_extra', 'integer_grant', 'measured', 'naive_time', 'submicrosecond_time',
    'uppercase_registration', 'long_identifier'])
def test_pure_request_rejects_untrusted_selectors_ambiguous_types_and_unsupported_source(fault):
    body = declared_request()
    source = body['source']
    if fault == 'tenant': body['tenant_id'] = 'tenant-2'
    elif fault == 'directory': body['directory'] = '/tmp/caller-choice'
    elif fault == 'source_root': source['carbon_root_sha256'] = 'b'*64
    elif fault == 'opaque_source': source['carbon_stock_inputs'] = raw(source['carbon_stock_inputs']).decode()
    elif fault == 'bool_step': source['numerical']['step_seconds'] = True
    elif fault == 'bool_count': source['numerical']['step_count'] = True
    elif fault == 'bool_index': source['stem_start_index'] = True
    elif fault == 'two_shoots': source['tracking_basis']['tracked_shoot_count']['value'] = 2
    elif fault == 'wrong_floor_unit': source['tracking_basis']['model_floor_area']['unit'] = 'm2'
    elif fault == 'profile': source['profile_sha256']['growth_profile'] = '0'*64
    elif fault == 'individual_extra': source['individual_program']['schema_version'] = 'caller-model-v1'
    elif fault == 'integer_grant': body['rights']['use'] = 1
    elif fault == 'measured': body['provenance']['origin'] = 'measured'
    elif fault == 'naive_time': body['provenance']['available_at'] = '2026-10-31T00:00:00'
    elif fault == 'submicrosecond_time': body['provenance']['available_at'] = '2026-10-31T00:00:00.0000001Z'
    elif fault == 'uppercase_registration': body['farm']['registration_sha256'] = 'A'*64
    else: body['study_id'] = body['provenance']['product_id'] = 'x'*201
    with pytest.raises(feature().MaterialFarmInputHold): feature()._request(raw(body))


@pytest.mark.parametrize('fault', ['noncanonical', 'duplicate', 'nonfinite', 'utf8', 'array', 'capacity'])
def test_pure_request_rejects_noncanonical_transport_and_hard_capacity(fault):
    body = declared_request()
    value = raw(body)
    if fault == 'noncanonical': value = json.dumps(body, ensure_ascii=False).encode()
    elif fault == 'duplicate': value = value[:-1]+b',"revision":"r1"}'
    elif fault == 'nonfinite': value = value.replace(b'"step_seconds":0.125', b'"step_seconds":NaN')
    elif fault == 'utf8': value = b'\xff'
    elif fault == 'array': value = b'[]'
    else: value = b' '*65537
    with pytest.raises(feature().MaterialFarmInputHold): feature()._request(value)


def test_exact_aware_UTC_keeps_KST_and_pre_epoch_microseconds():
    module = feature()
    left = datetime.fromisoformat('2026-11-01T00:00:00.000001+09:00')
    same = datetime.fromisoformat('2026-10-31T15:00:00.000001+00:00')
    with observed_codes() as calls:
        assert module._utc_fraction(left) == module._utc_fraction(same)
        assert module._utc_fraction(datetime(1969, 12, 31, 23, 59, 59, 999999,
            tzinfo=timezone.utc)) == Fraction(-1, 1000000)
        assert module._utc_fraction(same)-module._utc_fraction(same-timedelta(microseconds=1)) == Fraction(1, 1000000)
    assert not any(calls.values())
    with pytest.raises(module.MaterialFarmInputHold): module._utc_fraction(datetime(2026, 1, 1))
    with pytest.raises(module.MaterialFarmInputHold): module._utc_fraction(True)


@PG
def test_admission_and_read_current_do_not_evaluate_models_write_CAS_or_rewrite_rows(
        registered, monkeypatch, tmp_path):
    farms, body, principal, _ = registered
    service = feature().MaterialFarmInputService(farms)
    with observed_codes() as admission_calls:
        status = service.submit('tenant-1', raw(body))
    assert not any(admission_calls.values())
    job_id = str(status.job_id)
    row = service.jobs.get_job('tenant-1', status.job_id)
    before = counts(service.jobs)
    original_execute = Connection.execute
    reads, writes, external = [], [], []
    def execute(conn, query, params=None, **kwargs):
        text = query.as_string(conn) if isinstance(query, sql.Composable) else str(query)
        verb = text.lstrip().split(None, 1)[0].upper()
        if verb in {'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER', 'TRUNCATE', 'GRANT', 'REVOKE'}:
            writes.append(verb)
        elif verb == 'SELECT': reads.append(1)
        return original_execute(conn, query, params, **kwargs)
    def forbidden(*args, **kwargs):
        external.append(1)
        raise AssertionError('current material-input read started external work')
    principal['scopes'].difference_update({'crop_result_write', 'simulation_create'})
    monkeypatch.setattr(Connection, 'execute', execute)
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    with observed_codes() as read_calls:
        first = feature().MaterialFarmInputService(farms).current('tenant-1', job_id, row['input_sha256'])
        changed = first.witness
        changed['owned_input']['job_id'] = '00000000-0000-4000-8000-000000000000'
        changed_request = first.request
        changed_request['rights']['use'] = False
        again = service.current('tenant-1', job_id, row['input_sha256'])
    assert first.witness == again.witness and first.request == again.request == body
    with pytest.raises((AttributeError, TypeError)): first.input_bytes = b'{}'
    assert reads and not writes and not external and not any(read_calls.values())
    assert counts(service.jobs) == before
    (tmp_path/'actual-owned-material-input-v1.private.json').write_bytes(first.input_bytes)
    (tmp_path/'input-current-read-proof-v1.private.json').write_bytes(raw({
        'version': 'owned-material-input-current-read-proof-v1', 'input_sha256': row['input_sha256'],
        'input_bytes': len(first.input_bytes), 'witness': first.witness,
        'SQL_reads': len(reads), 'SQL_writes': len(writes), 'extra_nonDB_network_or_process': len(external),
        'new_seed_work': dict(read_calls), 'G0_G4': 'not_assessed', 'R2': 'not_approved'}))


@PG
def test_every_current_and_submit_scope_is_enforced_without_metadata_side_effects(registered):
    farms, body, principal, _ = registered
    module = feature()
    service = module.MaterialFarmInputService(farms)
    before = counts(service.jobs)
    for scope in WRITE_SCOPES:
        principal['scopes'].remove(scope)
        try:
            with pytest.raises(PermissionError): service.submit('tenant-1', raw(body))
        finally: principal['scopes'].add(scope)
    assert counts(service.jobs) == before
    status = service.submit('tenant-1', raw(body))
    digest = service.jobs.get_job('tenant-1', status.job_id)['input_sha256']
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        try:
            with pytest.raises(PermissionError): service.current('tenant-1', str(status.job_id), digest)
        finally: principal['scopes'].add(scope)
    assert service.current('tenant-1', str(status.job_id), digest).request == body
    with pytest.raises(PermissionError): service.current('tenant-other', str(status.job_id), digest)


@PG
def test_producer_missing_write_or_execution_permission_has_zero_model_store_and_CAS_effects(owned, tmp_path):
    service, _, principal, _, checked = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    for scope in ('crop_result_write', 'simulation_create'):
        principal['scopes'].remove(scope)
        try:
            with observed_codes() as calls:
                assert service.current('tenant-1', job_id, digest).witness == checked.witness
                with pytest.raises(PermissionError): producer.produce('tenant-1', job_id, digest)
            assert not any(calls.values()) and list(directory.iterdir()) == []
        finally: principal['scopes'].add(scope)


@PG
def test_exact_Farm_crop_zone_epoch_floor_and_complete_support_are_required(registered):
    farms, body, _, original_farm = registered
    module = feature()
    service = module.MaterialFarmInputService(farms)
    before = counts(service.jobs)
    for field, value in [('scenario_id', 'other'), ('scenario_revision', 'r2'),
            ('registration_sha256', '0'*64), ('crop_id', 'other'), ('zone_id', 'other')]:
        changed = deepcopy(body)
        changed['farm'][field] = value
        with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(changed))
    changed = deepcopy(body)
    for obj in (changed['source']['carbon_stock_inputs']['program'],
            changed['source']['individual_program'], changed['source']['tracking_basis']):
        obj['model_floor_area']['value'] = 2.0
    with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(changed))
    changed = deepcopy(body)
    changed['source']['carbon_stock_inputs']['time_origin_utc'] = '2026-10-01T00:00:01Z'
    with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(changed))
    changed = deepcopy(body)
    stem = changed['source']['stem_program']
    stem['output_times'] = ['2026-10-26T00:00:00Z']
    stem['segments'][0]['end_utc'] = stem['output_times'][-1]
    with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(changed))
    assert counts(service.jobs) == before
    decimal_farm = deepcopy(original_farm)
    decimal_farm['farm']['scenario_revision'] = 'decimal-footprint-r2'
    decimal_farm['rights']['scenario_revision'] = 'decimal-footprint-r2'
    decimal_farm['farm']['facility']['floor_area']['value'] = '0.1'
    decimal_farm['farm']['facility']['cultivable_area']['value'] = '0.1'
    decimal_farm['farm']['crops'][0]['area']['value'] = '0.1'
    selected = farms.submit('tenant-1', FarmAuthoringRequest.model_validate_json(raw(decimal_farm)))
    changed = renamed(body, '-binary64-floor')
    changed['farm']['scenario_revision'] = 'decimal-footprint-r2'
    changed['farm']['registration_sha256'] = selected.scenario_sha256
    for obj in (changed['source']['carbon_stock_inputs']['program'],
            changed['source']['individual_program'], changed['source']['tracking_basis']):
        obj['model_floor_area']['value'] = .1
    assert module._request(raw(changed)) == changed
    after_registration = counts(service.jobs)
    with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(changed))
    assert counts(service.jobs) == after_registration


@PG
def test_future_grants_sources_and_reversed_times_cannot_be_admitted(registered):
    farms, body, _, _ = registered
    module = feature()
    service = module.MaterialFarmInputService(farms)
    before = counts(service.jobs)
    for fault in ('future', 'reversed', 'grant'):
        changed = deepcopy(body)
        if fault == 'future':
            changed['rights']['available_at'] = changed['provenance']['available_at'] = '2099-01-01T00:00:00Z'
            changed['provenance']['retrieved_at'] = '2099-01-01T00:01:00Z'
        elif fault == 'reversed': changed['provenance']['retrieved_at'] = '2026-10-30T00:00:00Z'
        else: changed['source']['stem_program']['rights']['declared_at_utc'] = '2099-01-01T00:00:00Z'
        with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(changed))
    assert counts(service.jobs) == before


@PG
def test_declared_past_availability_does_not_backdate_actual_recording_or_ex_ante_status(registered):
    farms, body, _, _ = registered
    changed = deepcopy(body)
    changed['rights']['available_at'] = changed['provenance']['available_at'] = '2026-10-24T08:00:00Z'
    changed['provenance']['retrieved_at'] = '2026-10-24T09:00:00Z'
    service = feature().MaterialFarmInputService(farms)
    status = service.submit('tenant-1', raw(changed))
    digest = service.jobs.get_job('tenant-1', status.job_id)['input_sha256']
    checked = service.current('tenant-1', str(status.job_id), digest)
    time_scope = checked.witness['content_witness']['time_scope']
    assert time_scope['declared_availability_vs_farm_decision'] == 'before_or_at'
    assert time_scope['assumption_mode'] == 'supplemental_ex_post_synthetic_material_assumptions'
    assert time_scope['ex_ante_validity'] == 'not_established'
    assert status.created_at > DECISION
    assert datetime.fromisoformat(checked.witness['owned_input']['created_at'].replace('Z', '+00:00')) == status.created_at


@PG
def test_request_that_fits_the_hard_cap_cannot_overflow_the_complete_stored_intent(registered):
    farms, body, _, _ = registered
    value = deepcopy(body)
    for index in range(512):
        candidate = deepcopy(value)
        leaf = deepcopy(value['source']['carbon_stock_inputs']['program']['leaves'][0])
        leaf['leaf_id'] = 'owned-input-capacity-leaf-'+str(index)
        candidate['source']['carbon_stock_inputs']['program']['leaves'].append(leaf)
        candidate['source']['individual_program']['leaves'].append(deepcopy(leaf))
        if len(raw(candidate)) > 65536: break
        value = candidate
    encoded = raw(value)
    assert 62000 < len(encoded) <= 65536
    module = feature()
    assert module._request(encoded) == value
    service = module.MaterialFarmInputService(farms)
    before = counts(service.jobs)
    with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', encoded)
    assert counts(service.jobs) == before


@PG
def test_actual_input_cancellation_invalidates_current_and_production_before_seed_work(owned, tmp_path):
    service, _, _, status, _ = owned
    producer, job_id, digest = producer_for(owned, tmp_path/'producer')
    assert service.jobs.cancel('tenant-1', status.job_id)
    with observed_codes() as calls:
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
        with pytest.raises(seed_feature().MaterialFarmSeedHold): producer.produce('tenant-1', job_id, digest)
    assert not any(calls.values()) and list((tmp_path/'producer').iterdir()) == []


@PG
def test_claimed_registry_input_cannot_be_consumed_as_a_current_owned_seed_input(owned, tmp_path):
    service, _, _, status, _ = owned
    producer, job_id, digest = producer_for(owned, tmp_path/'producer')
    lease = service.jobs.claim(60, allowed_stages=('collection',), tenant_id='tenant-1', job_id=job_id)
    assert lease is not None and str(lease['job_id']) == job_id
    with observed_codes() as calls:
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
        with pytest.raises(seed_feature().MaterialFarmSeedHold): producer.produce('tenant-1', job_id, digest)
    assert not any(calls.values()) and service.jobs.get_job('tenant-1', status.job_id)['state'] == 'collecting'
    assert list((tmp_path/'producer').iterdir()) == []


@PG
def test_current_owned_Farm_research_source_cancellation_invalidates_dependent_input(owned, registered):
    service, _, _, status, checked = owned
    research_job_id = registered[3]['farm']['research_job_id']
    assert service.jobs.cancel('tenant-1', research_job_id)
    digest = checked.witness['owned_input']['input_sha256']
    with observed_codes() as calls:
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', str(status.job_id), digest)
    assert not any(calls.values())
    assert service.jobs.get_job('tenant-1', status.job_id)['state'] == 'queued'


@PG
def test_fixed_workspace_inode_and_current_job_hash_are_checked_before_production(owned, tmp_path):
    import shutil
    service, _, _, _, checked = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    for reference, expected in [(job_id.replace('-', ''), digest),
            ('AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA', digest), (job_id, '0'*64), (job_id, 'A'*64)]:
        with pytest.raises((feature().MaterialFarmInputHold, seed_feature().MaterialFarmSeedHold)):
            producer.produce('tenant-1', reference, expected)
    held = tmp_path/'held-original-workspace'
    directory.rename(held)
    shutil.copytree(held, directory)
    try:
        with observed_codes() as calls:
            with pytest.raises(seed_feature().MaterialFarmSeedHold): producer.produce('tenant-1', job_id, digest)
        assert not any(calls.values()) and list(directory.iterdir()) == []
    finally:
        shutil.rmtree(directory)
        held.rename(directory)
    assert service.current('tenant-1', job_id, digest).witness == checked.witness


@PG
def test_current_source_provider_parser_and_profile_drift_hold_and_restore_same_witness(owned, monkeypatch):
    service, _, principal, status, checked = owned
    job_id, digest = str(status.job_id), checked.witness['owned_input']['input_sha256']
    with monkeypatch.context() as patch:
        patch.setattr(service.jobs, 'principal_provider', lambda: principal)
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
    forged = []
    with monkeypatch.context() as patch:
        patch.setattr(feature(), '_request', lambda *_: forged.append(1))
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
    assert not forged
    with monkeypatch.context() as patch:
        patch.setitem(carbon.PROFILE_SHA, 'growth_profile', '0'*64)
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
    assert service.current('tenant-1', job_id, digest).witness == checked.witness


@PG
def test_actual_concurrent_same_intent_retry_and_changed_intent_conflict(registered):
    farms, body, _, _ = registered
    service = feature().MaterialFarmInputService(farms)
    baseline_body = renamed(body, '-concurrency-baseline')
    baseline = service.submit('tenant-1', raw(baseline_body))
    baseline_sha = service.jobs.get_job('tenant-1', baseline.job_id)['input_sha256']
    assert service.current('tenant-1', str(baseline.job_id), baseline_sha).request == baseline_body
    before = counts(service.jobs)
    barrier = Barrier(2)
    second_entry = Event()
    submit_entries = []
    thread_profile = local()
    submit_code = service.jobs.submit.__func__.__code__
    def observe_submit(frame, kind, result):
        if kind == 'call' and frame.f_code is submit_code:
            submit_entries.append(True)
            if len(submit_entries) == 1: second_entry.wait(timeout=2)
            else: second_entry.set()
    def profile_worker():
        thread_profile.previous = sys.getprofile()
        sys.setprofile(observe_submit)
    def submit(value):
        try:
            barrier.wait(timeout=30)
            try: return service.submit('tenant-1', raw(value))
            except JobIntentConflict: return 'conflict'
        finally: sys.setprofile(getattr(thread_profile, 'previous', None))
    with ThreadPoolExecutor(max_workers=2, initializer=profile_worker) as pool:
        futures = [pool.submit(submit, deepcopy(body)) for _ in range(2)]
        replies = [future.result(timeout=120) for future in futures]
    assert replies[0] != 'conflict' and replies[0] == replies[1]
    assert counts(service.jobs) == (before[0]+1, before[1]+1, before[2])
    candidate = renamed(body, '-conflict')
    changed = deepcopy(candidate)
    changed['rights']['declaration_id'] += '-different'
    barrier = Barrier(2)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(submit, value) for value in (candidate, changed)]
        replies = [future.result(timeout=120) for future in futures]
    assert replies.count('conflict') == 1
    assert counts(service.jobs) == (before[0]+2, before[1]+2, before[2])


@PG
def test_actual_submitted_event_scope_loss_rolls_back_uncommitted_input_and_event(registered):
    farms, body, principal, _ = registered
    service = feature().MaterialFarmInputService(farms)
    before = counts(service.jobs)
    staged = []
    def withdraw(name, kind, frame, result):
        if name == 'job_event' and kind == 'return' and frame.f_locals.get('kind') == 'submitted' and not staged:
            staged.append(True)
            principal['scopes'].remove('crop_result_write')
    try:
        with observed_codes(extra={service.jobs._event.__func__.__code__: 'job_event'}, event=withdraw):
            with pytest.raises(PermissionError): service.submit('tenant-1', raw(body))
    finally: principal['scopes'].add('crop_result_write')
    assert staged and counts(service.jobs) == before


@PG
def test_late_parser_replacement_inside_real_commit_staging_uses_captured_dispatch(registered, monkeypatch):
    farms, body, _, _ = registered
    module = feature()
    service = module.MaterialFarmInputService(farms)
    baseline = service.submit('tenant-1', raw(body))
    digest = service.jobs.get_job('tenant-1', baseline.job_id)['input_sha256']
    expected = service.current('tenant-1', str(baseline.job_id), digest).witness
    before = counts(service.jobs)
    staged, forged = [], []
    with monkeypatch.context() as patch:
        def replace(name, kind, frame, result):
            if name == 'job_event' and kind == 'return' and frame.f_locals.get('kind') == 'submitted' and not staged:
                staged.append(True)
                patch.setattr(module, '_request', lambda *_: forged.append(True))
        with observed_codes(extra={service.jobs._event.__func__.__code__: 'job_event'}, event=replace):
            with pytest.raises(module.MaterialFarmInputHold): service.submit('tenant-1', raw(renamed(body, '-late-parser')))
    assert staged and not forged and counts(service.jobs) == before
    assert service.current('tenant-1', str(baseline.job_id), digest).witness == expected


@PG
def test_postcommit_response_loss_keeps_first_intent_and_idempotent_retry(registered):
    farms, body, principal, _ = registered
    service = feature().MaterialFarmInputService(farms)
    before = counts(service.jobs)
    committed = []
    def withdraw(name, kind, frame, result):
        if name == 'job_submit' and kind == 'return' and isinstance(result, dict) and not committed:
            committed.append(result)
            principal['scopes'].remove('crop_result_write')
    try:
        with observed_codes(extra={service.jobs.submit.__func__.__code__: 'job_submit'}, event=withdraw):
            with pytest.raises(PermissionError): service.submit('tenant-1', raw(body))
    finally: principal['scopes'].add('crop_result_write')
    assert committed and counts(service.jobs) == (before[0]+1, before[1]+1, before[2])
    status = service.submit('tenant-1', raw(body))
    assert status.job_id == committed[0]['job_id'] and status.created_at == committed[0]['created_at']
    checked = service.current('tenant-1', str(status.job_id), committed[0]['input_sha256'])
    assert checked.request == body and counts(service.jobs) == (before[0]+1, before[1]+1, before[2])


@PG
@pytest.mark.parametrize('boundary', ['numerical', 'put', 'link_dispatch'])
def test_genuine_late_producer_boundaries_suppress_output_and_do_not_claim_file_rollback(owned, tmp_path, boundary):
    service, _, principal, _, _ = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    before = counts(service.jobs)
    triggered, later, forged = [], [], []
    target = 'CAS_put' if boundary == 'put' else 'carbon_context'
    def withdraw(name, kind, frame, result):
        if triggered and kind == 'call' and name in {'carbon_context', 'carbon_advance',
                'individual_context', 'individual_advance', 'stem_advance', 'CAS_put'}:
            later.append(name)
        if name == target and kind == 'return' and not triggered:
            triggered.append(True)
            if boundary == 'link_dispatch': producer._link = lambda *a, **k: forged.append(True)
            else: principal['scopes'].remove('simulation_create' if boundary == 'put' else 'crop_result_write')
    expected = seed_feature().MaterialFarmSeedHold if boundary == 'link_dispatch' else PermissionError
    try:
        with observed_codes(event=withdraw) as calls:
            with pytest.raises(expected): producer.produce('tenant-1', job_id, digest)
    finally:
        principal['scopes'].update({'crop_result_write', 'simulation_create'})
    assert triggered and not later and not forged
    assert calls['old_carbon_bulk'] == calls['old_stem_bulk'] == 0
    assert counts(service.jobs) == before
    if boundary == 'put':
        assert calls['CAS_put'] == 1 and stored_files(directory)
        assert all((path.stat().st_mode & 0o777) == 0o640 for path in directory.rglob('*') if path.is_file())


@PG
def test_genuine_other_source_and_Context_cannot_pass_owned_linkage_or_mint_verified_seed(owned, profiles, tmp_path):
    service, body, _, _, checked = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    with observed_codes() as calls:
        seed = producer.produce('tenant-1', job_id, digest)
    assert calls['carbon_context'] > 0 and calls['individual_context'] > 0 and calls['stem_advance'] > 0
    assert calls['old_carbon_bulk'] == calls['old_stem_bulk'] == 0
    assert producer._link(checked, context=seed.context, carbon_root_sha256=seed.carbon_root_sha256,
        stem_root_sha256=seed.stem_root_sha256, initial_binding_bytes=seed.initial_binding_bytes) == seed.witness['source']
    other = deepcopy(body['source'])
    other['carbon_stock_inputs']['input_id'] = 'genuine-other-source'
    other['carbon_stock_inputs']['program']['input_id'] = 'genuine-other-source'
    other['carbon_stock_inputs']['program']['scenario']['input_id'] = 'genuine-other-source'
    other['individual_program']['input_id'] = 'genuine-other-source'
    other['individual_program']['scenario']['input_id'] = 'genuine-other-source'
    other['stem_program']['program_id'] = 'genuine-other-stem'
    foreign = original_seed(tmp_path/'genuine-independent-source', other, profiles)
    for name in ('carbon', 'stem'):
        with MorphologyBlobStore(directory/digest/name, ACCESS, write=True) as store:
            for path in (tmp_path/'genuine-independent-source'/name).iterdir():
                assert store.put(path.read_bytes(), maximum=2*1024**2) == path.name
    before = stored_files(directory)
    variants = [dict(context=seed.context, carbon_root_sha256=foreign[0], stem_root_sha256=seed.stem_root_sha256,
            initial_binding_bytes=seed.initial_binding_bytes),
        dict(context=seed.context, carbon_root_sha256=seed.carbon_root_sha256, stem_root_sha256=foreign[1],
            initial_binding_bytes=seed.initial_binding_bytes),
        dict(context=foreign[2], carbon_root_sha256=seed.carbon_root_sha256, stem_root_sha256=seed.stem_root_sha256,
            initial_binding_bytes=seed.initial_binding_bytes),
        dict(context=seed.context, carbon_root_sha256=seed.carbon_root_sha256, stem_root_sha256=seed.stem_root_sha256,
            initial_binding_bytes=raw(foreign[3]))]
    for fields in variants:
        with pytest.raises(seed_feature().MaterialFarmSeedHold): producer._link(checked, **fields)
    with pytest.raises(seed_feature().MaterialFarmSeedHold): producer._link(checked.witness, **variants[0])
    assert stored_files(directory) == before
    changed = seed.witness
    changed['source']['carbon_root_sha256'] = foreign[0]
    assert seed.witness['source']['carbon_root_sha256'] == seed.carbon_root_sha256
    assert service.jobs.get_publication('tenant-1', owned[3].job_id) is None


@PG
def test_late_Farm_method_shadows_are_rejected_before_the_forged_current_callback(owned, monkeypatch):
    service, body, _, status, checked = owned
    farms = service.farms
    reference = body['farm']
    genuine_registration = farms.read_registration('tenant-1', reference['scenario_id'],
        reference['scenario_revision'], reference['registration_sha256'])
    genuine_row = farms._find('tenant-1', reference['scenario_id'], reference['scenario_revision'])
    job_id, digest = str(status.job_id), checked.witness['owned_input']['input_sha256']
    assert service.current('tenant-1', job_id, digest).witness == checked.witness
    for name, value in [('read_registration', genuine_registration), ('_find', genuine_row)]:
        triggered, forged = [], []
        with monkeypatch.context() as patch:
            def replace(label, kind, frame, result):
                row = frame.f_locals.get('row')
                if (label == 'verified_input' and kind == 'return' and isinstance(row, dict)
                        and str(row.get('job_id')) == job_id and not triggered):
                    triggered.append(True)
                    def forged_read(*args, **kwargs):
                        forged.append(True)
                        return value
                    patch.setattr(farms, name, forged_read)
            with observed_codes(extra={service.jobs._verified_input.__code__: 'verified_input'}, event=replace):
                with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
        assert triggered and not forged
        assert service.current('tenant-1', job_id, digest).witness == checked.witness


@PG
def test_actual_input_cancel_during_current_Farm_read_suppresses_stale_queued_witness(owned):
    service, _, _, status, checked = owned
    job_id, digest = str(status.job_id), checked.witness['owned_input']['input_sha256']
    assert service.current('tenant-1', job_id, digest).witness == checked.witness
    cancelled = []
    def cancel(label, kind, frame, result):
        if label == 'Farm_read' and kind == 'return' and isinstance(result, dict) and not cancelled:
            cancelled.append(service.jobs.cancel('tenant-1', status.job_id))
    with observed_codes(extra={service.farms.read_registration.__func__.__code__: 'Farm_read'}, event=cancel):
        with pytest.raises(feature().MaterialFarmInputHold): service.current('tenant-1', job_id, digest)
    assert cancelled == [True]
    assert service.jobs.get_job('tenant-1', status.job_id)['state'] == 'canceled'


@PG
def test_same_original_program_and_profiles_with_a_different_genuine_grid_cannot_pass_owned_link(owned, profiles, tmp_path):
    service, body, _, _, checked = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    seed = producer.produce('tenant-1', job_id, digest)
    assert producer._link(checked, context=seed.context, carbon_root_sha256=seed.carbon_root_sha256,
        stem_root_sha256=seed.stem_root_sha256, initial_binding_bytes=seed.initial_binding_bytes) == seed.witness['source']
    alternate = initial.crop.prepare_context(program=body['source']['individual_program'],
        step_seconds=.25, step_count=body['source']['numerical']['step_count'], **profiles)
    assert alternate._request == seed.context._request
    assert alternate._program == seed.context._program
    assert alternate.manifest['identity']['profile_sha256'] == seed.context.manifest['identity']['profile_sha256']
    assert alternate.manifest['numerical'] != seed.context.manifest['numerical']
    declaration = deepcopy(json.loads(seed.initial_binding_bytes)['declaration'])
    declaration['context_sha256'] = alternate.root_sha256
    proof = initial.bind_initial_stem_carbon(alternate, directory/digest/'carbon', directory/digest/'stem', ACCESS,
        crop_root_sha256=seed.carbon_root_sha256, stem_root_sha256=seed.stem_root_sha256,
        stem_start_index=body['source']['stem_start_index'], declaration=declaration)
    assert proof['context_sha256'] == alternate.root_sha256
    assert proof['balance']['carbon']['once_rounded_matches_source'] is True
    assert proof['balance']['removal']['once_rounded_matches_source'] is True
    before = stored_files(directory)
    with pytest.raises(seed_feature().MaterialFarmSeedHold):
        producer._link(checked, context=alternate, carbon_root_sha256=seed.carbon_root_sha256,
            stem_root_sha256=seed.stem_root_sha256, initial_binding_bytes=raw(proof))
    assert stored_files(directory) == before
    assert service.current('tenant-1', job_id, digest).witness == checked.witness


@PG
@pytest.mark.parametrize('method', ['validate', 'prepare_new', 'require_writer'])
def test_live_ContentAccess_class_dispatch_drift_is_rejected_before_forged_method(owned, tmp_path, monkeypatch, method):
    from app.content_access import ContentAccess
    service, body, _, _, checked = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    seed = producer.produce('tenant-1', job_id, digest)
    assert producer._link(checked, context=seed.context, carbon_root_sha256=seed.carbon_root_sha256,
        stem_root_sha256=seed.stem_root_sha256, initial_binding_bytes=seed.initial_binding_bytes) == seed.witness['source']
    other_body = renamed(body, '-class-dispatch-'+method)
    other = service.submit('tenant-1', raw(other_body))
    other_sha = service.jobs.get_job('tenant-1', other.job_id)['input_sha256']
    assert service.current('tenant-1', str(other.job_id), other_sha).request == other_body
    assert not (directory/other_sha).exists()
    original = getattr(ContentAccess, method)
    forged = []
    before = stored_files(directory)
    def changed_policy(self, *args, **kwargs):
        forged.append(method)
        return original(self, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(ContentAccess, method, changed_policy)
        with pytest.raises(seed_feature().MaterialFarmSeedHold):
            producer.produce('tenant-1', str(other.job_id), other_sha)
    assert not forged
    assert stored_files(directory) == before
    assert not (directory/other_sha).exists()
    assert service.current('tenant-1', job_id, digest).witness == checked.witness


@PG
def test_rejected_late_ContentAccess_policy_never_runs_during_store_unwind_and_can_recover(owned, tmp_path, monkeypatch):
    from app.content_access import ContentAccess
    service, body, _, _, checked = owned
    directory = tmp_path/'producer'
    producer, job_id, digest = producer_for(owned, directory)
    baseline = producer.produce('tenant-1', job_id, digest)
    assert producer._link(checked, context=baseline.context, carbon_root_sha256=baseline.carbon_root_sha256,
        stem_root_sha256=baseline.stem_root_sha256, initial_binding_bytes=baseline.initial_binding_bytes) == baseline.witness['source']
    request = renamed(body, '-late-storage-policy')
    status = service.submit('tenant-1', raw(request))
    other_id = str(status.job_id)
    other_sha = service.jobs.get_job('tenant-1', status.job_id)['input_sha256']
    original_input = service.current('tenant-1', other_id, other_sha)
    assert original_input.request == request and not (directory/other_sha).exists()
    original_validate = ContentAccess.validate
    prior_profile = sys.getprofile()
    first_put, held_store, forged = [], [], []
    before_rows = counts(service.jobs)
    with monkeypatch.context() as patch:
        def replaced_validate(self, *args, **kwargs):
            forged.append(True)
            return original_validate(self, *args, **kwargs)
        def change_after_put(name, kind, frame, result):
            if name == 'CAS_put' and kind == 'return' and not first_put:
                first_put.append(result)
                held_store.append(frame.f_locals['self'])
                patch.setattr(ContentAccess, 'validate', replaced_validate)
        with observed_codes(event=change_after_put) as calls:
            with pytest.raises(seed_feature().MaterialFarmSeedHold):
                producer.produce('tenant-1', other_id, other_sha)
    assert sys.getprofile() is prior_profile
    assert len(first_put) == calls['CAS_put'] == 1
    assert all(store._fd is None for store in held_store)
    orphan = directory/other_sha/'carbon'/first_put[0]
    assert orphan.is_file() and sha256(orphan.read_bytes()).hexdigest() == first_put[0]
    assert orphan.stat().st_mode & 0o777 == 0o640
    assert counts(service.jobs) == before_rows
    assert service.jobs.get_publication('tenant-1', status.job_id) is None
    assert not forged
    recovered = producer.produce('tenant-1', other_id, other_sha)
    assert recovered.witness['owned_input'] == original_input.witness['owned_input']
    assert recovered.carbon_root_sha256 == baseline.carbon_root_sha256
    assert recovered.stem_root_sha256 == baseline.stem_root_sha256
    assert service.current('tenant-1', other_id, other_sha).witness == original_input.witness
    assert counts(service.jobs) == before_rows
    assert service.jobs.get_publication('tenant-1', status.job_id) is None
