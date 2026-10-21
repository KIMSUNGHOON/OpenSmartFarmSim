"""Real original numeric producer and current SCRAM signed-result queries."""
from copy import deepcopy
import ctypes
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys

from psycopg import sql
import pytest

from app import crop_morphology_signed_artifact as signed
from app import crop_morphology_signed_producer as producer
from app.content_access import ContentAccess
from app.crop_result_store import WRITE_SCOPES
from app.farm_authoring_storage import FarmAuthoringRequest
from login_database import login_database, login_scope
import morphology_farm_factory as factory


KEY = b'owned-signed-morphology-native-test-key-32!'
PUBLIC = Path(__file__).resolve().parents[2]/'web/public/morphology-rational-replay'
pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


def schema_hash(base):
    with base.connect() as conn:
        names = [r['table_name'] for r in conn.execute("SELECT table_name FROM information_schema.tables "
            "WHERE table_schema=%s AND table_type='BASE TABLE' ORDER BY table_name", (base.schema,)).fetchall()]
        rows = {name: sorted(r['row'] for r in conn.execute(sql.SQL('SELECT to_jsonb(x)::text AS row FROM {} x')
            .format(sql.Identifier(base.schema, name))).fetchall()) for name in names}
    return sha256(signed.reader._canonical(rows)).hexdigest(), len(names)


@pytest.fixture(scope='module', autouse=True)
def final_cleanup(login_database):
    yield
    import psycopg
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    factory.save('signed-database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles})


@pytest.fixture
def setup(login_scope, tmp_path, monkeypatch):
    packet = factory.source_packet()
    farms, body, principal = factory.create_farm(login_scope, monkeypatch, packet['decision'])
    registered = farms.submit('tenant-1', FarmAuthoringRequest.model_validate_json(signed.reader._canonical(body)))
    principal['scopes'].update(WRITE_SCOPES); rights = factory.SyntheticMorphologyRights()
    binding = signed.farms.MorphologyFarmBinding(farms, packet['authority'], input_rights=rights)
    request = factory.study(body, registered.scenario_sha256, packet['packet'], packet['decision'])
    authority = signed.MorphologyArtifactAuthority(binding, directory=tmp_path/'signed', access=ContentAccess(os.getuid(), os.getgid()),
        integrity_key=KEY, issuer_id='owned-native-research', key_id='owned-signed-result-key-v1')
    return authority, request, packet, principal, rights


def publish(value):
    authority, request, packet, *_ = value
    return producer.produce_registered_morphology(authority, 'tenant-1', signed.reader._canonical(request), **packet['packet'])


def test_actual_numeric_root_original_twelve_frames_and_fresh_current_query(setup, login_scope, tmp_path, monkeypatch):
    authority, request, packet, principal, _, = setup; base = login_scope[0]
    before = schema_hash(base); originals = {p.name: sha256(p.read_bytes()).hexdigest() for p in PUBLIC.iterdir()}
    actual = producer.numerical.produce_rational_morphology_artifact; calls = []
    def calculate(*a, **kw):
        calls.append(1)
        return actual(*a, **kw)
    monkeypatch.setattr(producer.numerical, 'produce_rational_morphology_artifact', calculate)
    result_id = publish(setup); assert calls == [1]
    payload = json.loads((authority.directory/result_id).read_bytes())['payload']
    binding_raw = (authority.directory/payload['binding_sha256']).read_bytes()
    growth = factory.forbid_growth(monkeypatch)
    manifest = authority.read_manifest('tenant-1', result_id)
    assert manifest['manifest'] == json.loads((PUBLIC/'root.json').read_bytes())
    assert manifest['numerical_root_sha256'] == sha256((PUBLIC/'root.json').read_bytes()).hexdigest()
    assert manifest['gates'] == 'not_assessed' and manifest['profile_applicability'] == 'unvalidated_for_registered_crop'
    for index in range(12):
        response = authority.read_frame('tenant-1', result_id, index=index); raw = (PUBLIC/f'frame-{index}.json').read_bytes()
        assert signed.reader._canonical(response['frame']) == raw and response['frame_sha256'] == sha256(raw).hexdigest()
        assert response['calculated_at'] == payload['calculated_at']
    config = factory.fresh_config(authority.farm_binding, principal, request, packet['packet'], packet['review'], binding_raw, tmp_path/'fresh')
    p = json.loads(Path(config).read_bytes()); p['signed'] = {'directory': str(authority.directory), 'result_sha256': result_id,
        'key_file': factory.private_file(tmp_path/'fresh', 'signed-key.private', KEY), 'issuer_id': authority.issuer_id,
        'key_id': authority.key_id, 'expected_numerical_root_sha256': payload['numerical_root_sha256'],
        'expected_calculated_at': payload['calculated_at']}
    path = factory.private_file(tmp_path/'fresh', 'signed-configuration.private.json', signed.reader._canonical(p))
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    done = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('morphology_signed_fresh.py')), path],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=60,
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])})
    assert done.returncode == 0, done.stderr
    fresh = json.loads(done.stdout)
    assert fresh['new_growth_modules_imported'] == 0 and fresh['result_sha256'] == result_id
    assert not any(growth.values()) and schema_hash(base) == before and calls == [1]
    assert {p.name: sha256(p.read_bytes()).hexdigest() for p in PUBLIC.iterdir()} == originals
    factory.save('signed-normal-fresh.json', {'result_sha256': result_id, 'numerical_root_sha256': payload['numerical_root_sha256'],
        'signature_bytes': (authority.directory/result_id).stat().st_size, 'calculated_at': payload['calculated_at'],
        'all_12_original_frames': True, 'original_15_files_preserved': True, 'numeric_producer_calls': 1,
        'query_growth_CLI_calls': growth, 'owned_database_sha256_before_after': [before, schema_hash(base)], 'fresh': fresh})


def test_actual_current_and_late_revocation_no_result_or_stale_query(setup, login_scope, monkeypatch):
    authority, _, packet, principal, rights = setup; before = schema_hash(login_scope[0]); result_id = publish(setup)
    growth = factory.forbid_growth(monkeypatch)
    rights.allowed = False
    with pytest.raises(signed.MorphologySignedArtifactHold): authority.read_manifest('tenant-1', result_id)
    rights.allowed = True; packet['review']['status'] = 'revoked'
    with pytest.raises(signed.MorphologySignedArtifactHold): authority.read_frame('tenant-1', result_id, index=0)
    packet['review']['status'] = 'accepted_for_software_validation'
    principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError): authority.read_manifest('tenant-1', result_id)
    principal['scopes'].add('crop_result_read')
    previous = signed.reader.read_rational_morphology_frame
    def revoke(*a, **kw):
        value = previous(*a, **kw); rights.allowed = False
        return value
    with monkeypatch.context() as patch:
        patch.setattr(signed.reader, 'read_rational_morphology_frame', revoke)
        with pytest.raises(signed.MorphologySignedArtifactHold): authority.read_frame('tenant-1', result_id, index=0)
    rights.allowed = True
    assert authority.read_manifest('tenant-1', result_id)['result_sha256'] == result_id
    assert not any(growth.values()) and schema_hash(login_scope[0]) == before
    factory.save('signed-current-late.json', {'current_rights_review_scope_rejected': True, 'late_scene_query_revocation_rejected': True,
        'original_result_after_restore': result_id, 'query_growth_CLI_calls': growth,
        'owned_database_sha256_before_after': [before, schema_hash(login_scope[0])]})
