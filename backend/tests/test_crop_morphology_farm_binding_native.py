"""Actual SCRAM registration and current permissions, entirely synthetic replay."""
from copy import deepcopy
import ctypes
import gc
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

import psycopg
from psycopg import sql
import pytest

from app import crop_morphology_farm_binding as model
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.farm_authoring_storage import FarmAuthoringRequest
from login_database import login_database, login_scope
import morphology_farm_factory as factory


pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'market_source_storage': True,
    'thermal_scenario_storage': True, 'break_even_calculation': True, 'crop_cycle_result_storage': True}], indirect=True)


@pytest.fixture(scope='module', autouse=True)
def final_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    factory.save('database-cleanup.json', {'schemas_after': schemas, 'roles_after': roles})


@pytest.fixture
def setup(login_scope, monkeypatch):
    packet = factory.source_packet()
    farms, farm_body, principal = factory.create_farm(login_scope, monkeypatch, packet['decision'])
    registered = farms.submit('tenant-1', FarmAuthoringRequest.model_validate_json(model.documents._canonical(farm_body)))
    principal['scopes'].update(WRITE_SCOPES)
    rights = factory.SyntheticMorphologyRights()
    service = model.MorphologyFarmBinding(farms, packet['authority'], input_rights=rights)
    body = factory.study(farm_body, registered.scenario_sha256, packet['packet'], packet['decision'])
    calls = factory.forbid_growth(monkeypatch)
    yield service, body, packet, principal, rights, calls
    assert not any(calls.values())


def prepare(value):
    service, body, packet, *_ = value
    return service.prepare('tenant-1', model.documents._canonical(body), **packet['packet'])


def current(value, expected, *, write=False, tenant='tenant-1', body=None):
    service, original, packet, *_ = value
    return service.current(tenant, model.documents._canonical(original if body is None else body), expected,
        **packet['packet'], write=write)


def test_original_registered_replay_read_write_and_lean_fresh_exec(setup, tmp_path, monkeypatch):
    service, body, packet, principal, rights, calls = setup
    before = factory.counts(service); checked = []; original = service.input_authority.verify
    def verify(*a, **kw):
        checked.append(1)
        return original(*a, **kw)
    monkeypatch.setattr(service.input_authority, 'verify', verify)
    started = perf_counter(); raw = prepare(setup); prepare_seconds = perf_counter()-started; doc = json.loads(raw)
    assert len(checked) == 2 and rights.calls == ['research_calculation', 'research_display']*2
    assert doc['scope'] == 'synthetic_morphology_input_binding_only' and doc['G0_G4'] == 'not_assessed'
    assert doc['rights_or_gate_approval'] is False and doc['numerical_initial_state_validation'] is False
    assert doc['input']['source_record'] == json.loads(packet['packet']['source_raw'])['provenance']
    assert doc['input']['program_sha256'] == sha256(packet['packet']['program_raw']).hexdigest()
    assert doc['input']['period'] == {'start': '2026-10-01T00:00:00Z', 'end': '2026-10-02T00:00:00Z'}
    assert doc['registration']['decision_at'] == packet['decision'].isoformat().replace('+00:00', 'Z')
    assert doc['registration']['normalization'] == 'per_tracked_shoot'
    assert doc['registration']['profile_applicability'] == 'unvalidated_for_registered_crop'
    rights.calls.clear(); checked.clear(); started = perf_counter()
    assert current(setup, raw) == raw
    current_seconds = perf_counter()-started
    assert len(checked) == 2 and rights.calls == ['research_display']*2
    assert current(setup, raw, write=True) == raw
    config = factory.fresh_config(service, principal, body, packet['packet'], packet['review'], raw, tmp_path/'fresh')
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    script = Path(__file__).with_name('morphology_farm_fresh.py')
    done = subprocess.run([sys.executable, '-B', str(script), config], stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=60, env={**os.environ, 'PYTHONPATH': str(Path(__file__).resolve().parents[1])})
    assert done.returncode == 0, done.stderr
    fresh = json.loads(done.stdout)
    assert fresh['binding_sha256'] == sha256(raw).hexdigest() and fresh['actual_SCRAM']
    assert not any(fresh['calls'].values()) and factory.counts(service) == before and before[2:] == (0, 0)
    factory.save('normal-fresh.json', {'binding_bytes': len(raw), 'binding_sha256': sha256(raw).hexdigest(),
        'program_sha256': doc['input']['program_sha256'], 'source_sha256': doc['input']['source_sha256'],
        'source_record_sha256': sha256(model.documents._canonical(doc['input']['source_record'])).hexdigest(),
        'decision_at': doc['registration']['decision_at'], 'model_period': doc['input']['period'],
        'retrospective_synthetic_replay_not_past_prediction': True, 'normalization': 'per_tracked_shoot',
        'prepare_seconds': prepare_seconds, 'current_seconds': current_seconds, 'fresh': fresh,
        'counts_before_after': [before, factory.counts(service)], 'calls': calls, 'rights_or_gate_approval': False})


def test_current_scopes_sources_reviews_and_late_changes(setup, monkeypatch):
    service, body, packet, principal, rights, calls = setup
    raw = prepare(setup); before = factory.counts(service); cases = []
    principal['scopes'].remove('crop_result_write'); assert current(setup, raw) == raw
    with pytest.raises(PermissionError): current(setup, raw, write=True)
    principal['scopes'].add('crop_result_write')
    for scope in READ_SCOPES:
        principal['scopes'].remove(scope)
        with pytest.raises(PermissionError): current(setup, raw)
        principal['scopes'].add(scope); cases.append('missing:'+scope)
    with pytest.raises(PermissionError): current(setup, raw, tenant='foreign')
    rights.allowed = False
    with pytest.raises(model.MorphologyFarmBindingHold): current(setup, raw)
    rights.allowed = True; packet['review']['status'] = 'revoked'
    with pytest.raises(model.MorphologyFarmBindingHold): current(setup, raw)
    packet['review']['status'] = 'accepted_for_software_validation'
    for path, value in [('crop_id', 'other'), ('scenario_revision', 'other'), ('registration_sha256', '0'*64)]:
        changed = deepcopy(body); changed['farm'][path] = value
        with pytest.raises(model.MorphologyFarmBindingHold): current(setup, raw, body=changed)
        cases.append('farm:'+path)
    for kind in ('rights', 'review', 'scope', 'declaration', 'farm-source'):
        with monkeypatch.context() as patch:
            previous = factory.SyntheticMorphologyRights.__call__; seen = []
            def changed(self, tenant, declaration, source, use):
                answer = previous(self, tenant, declaration, source, use); seen.append(1)
                if len(seen) == 1:
                    if kind == 'rights': self.allowed = False
                    elif kind == 'review': packet['review']['status'] = 'revoked'
                    elif kind == 'scope': principal['scopes'].remove('crop_result_read')
                    elif kind == 'declaration': declaration['display'] = False
                    else: patch.setattr(service.farms.replay.candidates._source._source, 'get_input_rights', lambda *_: None)
                return answer
            patch.setattr(factory.SyntheticMorphologyRights, '__call__', changed)
            with pytest.raises((model.MorphologyFarmBindingHold, PermissionError)): current(setup, raw, write=True)
            rights.allowed = True; packet['review']['status'] = 'accepted_for_software_validation'; principal['scopes'].add('crop_result_read')
        cases.append('late:'+kind)
    assert current(setup, raw) == raw and factory.counts(service) == before and not any(calls.values())
    factory.save('current-late.json', {'cases': cases, 'foreign_tenant_rejected': True, 'current_rights_review_revoked_rejected': True,
        'counts_before_after': [before, factory.counts(service)], 'calls': calls})


def test_actual_owned_database_registration_and_grant_changes(setup, login_scope):
    service, body, *_ = setup; raw = prepare(setup); before = factory.counts(service); base, policy, _ = login_scope
    row = service.farms._find('tenant-1', body['farm']['scenario_id'], body['farm']['scenario_revision'])
    with pytest.raises(psycopg.errors.RaiseException, match='job identity is immutable'):
        with base.connect() as conn:
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
                (row['input_bytes']+b' ', row['job_id']))
    with pytest.raises(psycopg.errors.CheckViolation, match='jobs_input_digest_matches'):
        with base.connect() as conn:
            conn.execute("SET LOCAL session_replication_role='replica'")
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
                (row['input_bytes']+b' ', row['job_id']))
    with base.connect() as conn:
        conn.execute("SET LOCAL session_replication_role='replica'")
        conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
            (row['input_bytes']+b' ', sha256(row['input_bytes']+b' ').hexdigest(), row['job_id']))
    try:
        with pytest.raises(model.MorphologyFarmBindingHold): current(setup, raw)
    finally:
        with base.connect() as conn:
            conn.execute("SET LOCAL session_replication_role='replica'")
            conn.execute(sql.SQL('UPDATE {} SET input_bytes=%s,input_sha256=%s WHERE job_id=%s').format(service.jobs._table('jobs')),
                (row['input_bytes'], row['input_sha256'], row['job_id']))
    assert current(setup, raw) == raw
    table, role = service.jobs._table('jobs'), sql.Identifier(policy.roles['authority'])
    with base.connect() as conn: conn.execute(sql.SQL('GRANT DELETE ON {} TO {}').format(table, role))
    try:
        with pytest.raises(model.MorphologyFarmBindingHold): current(setup, raw)
    finally:
        with base.connect() as conn: conn.execute(sql.SQL('REVOKE DELETE ON {} FROM {}').format(table, role))
    assert current(setup, raw) == raw and factory.counts(service) == before
    factory.save('database-current.json', {'immutable_trigger': True, 'digest_constraint': True,
        'rehashed_corruption_only_in_owned_scratch_database': True, 'current_registration_and_grant_rejected': True,
        'restored_original_binding': True, 'counts_before_after': [before, factory.counts(service)]})
