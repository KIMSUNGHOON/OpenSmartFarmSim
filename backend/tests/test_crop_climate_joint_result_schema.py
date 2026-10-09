"""Actual SCRAM SQL boundaries; fixture hashes are not signed farm/crop evidence."""
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from uuid import uuid4

import psycopg
from psycopg import errors, sql
from psycopg.conninfo import make_conninfo
import pytest

from app import crop_climate_joint_result_schema as model
from app.crop_cycle_calculation_result_schema import install_calculation_cycle_crop_result_schema
from app.job_store import JobStore
from app.runtime_login import connect_runtime
from app.runtime_roles import audit_runtime_roles
from app.thermal_run_store import _canonical
from login_database import login_database, login_scope
from test_crop_cycle_result_schema import fixture_row, metadata as legacy_metadata, insert as insert_legacy


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_SCHEMA_EVIDENCE')
    if directory:
        with (Path(directory)/name).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400)
            json.dump(value, handle, sort_keys=True, indent=2); handle.flush(); os.fsync(handle.fileno())


def metadata(row):
    return {'schema_version': 'joint-crop-climate-result-v1', 'status': 'stored_unpublished_research',
        'claim_scope': 'synthetic_joint_crop_climate_math_only', 'G0_G4': 'not_assessed',
        **{k: row[k] for k in ('tenant_id', 'study_id', 'revision', 'result_id')},
        'farm': {k: str(row[k]) for k in model.FARM_KEYS},
        'input': {k: row[k] for k in model.INPUT_KEYS},
        'artifact': {**{k: row[v] for k, v in model.ARTIFACT_STRINGS.items()},
                     **{k: row[k] for k in model.COUNTER_BOUNDS}},
        'binding': {}, 'policies': {}, 'code': {}}


def payload(row, value=None, raw=None):
    raw = _canonical(metadata(row) if value is None else value) if raw is None else raw
    return {**row, 'payload_raw': raw, 'payload_sha256': sha256(raw).hexdigest()}


def insert(conn, policy, row, table=model.TABLE):
    conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(sql.Identifier(policy.schema, table),
        sql.SQL(',').join(map(sql.Identifier, row)), sql.SQL(',').join(sql.Placeholder() for _ in row)), tuple(row.values()))


def owner(conn, policy): conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))


def rejected(conn, policy, row, exception=errors.CheckViolation):
    with pytest.raises(exception), conn.transaction(): insert(conn, policy, row)


@pytest.fixture(scope='module')
def database_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles}); assert schemas == roles == 0


@pytest.fixture(autouse=True)
def forbid_equations(monkeypatch):
    from app import crop_climate_joint_continuation as c
    from app import crop_climate_joint_time as clock
    def forbidden(*args, **kwargs): pytest.fail('SQL schema evaluated crop/climate equations')
    for module, names in ((c, ('prepare_context', 'start', 'restore_checkpoint', 'advance_chunk')),
                          (c.driver.joint, ('evaluate_rhs',)), (c.driver.short, ('integrate',)),
                          (c.driver.management, ('apply_management',)),
                          (clock, ('prepare_binding',))):
        for name in names: monkeypatch.setattr(module, name, forbidden)


@pytest.fixture
def scram_scope(login_scope, login_database, tmp_path):
    original, policy, dsns = login_scope
    role = 'login_schema_provisioner_'+uuid4().hex
    password = secrets.token_hex(32); passfile = tmp_path/'provisioner.pgpass'
    database = login_database
    try:
        with original.connect() as conn:
            conn.execute("SET LOCAL log_statement='none'")
            conn.execute("SET LOCAL log_min_duration_statement=-1")
            conn.execute("SET LOCAL log_min_error_statement='panic'")
            verifier = conn.pgconn.encrypt_password(password.encode(), role.encode(), b'scram-sha-256')
            conn.execute(sql.SQL('CREATE ROLE {} LOGIN SUPERUSER PASSWORD {}').format(
                sql.Identifier(role), sql.Literal(verifier.decode())))
        passfile.write_text(f"{database['host']}:{database['port']}:{database['database']}:{role}:{password}\n")
        passfile.chmod(0o600)
        dsn = make_conninfo(host=database['host'], port=database['port'], dbname=database['database'],
            user=role, passfile=str(passfile), sslmode='disable', require_auth='scram-sha-256')
        yield JobStore(dsn, policy.schema, original.artifact_root, principal_provider=original.principal_provider), policy, dsns
    finally:
        passfile.unlink(missing_ok=True)
        with original.connect() as conn: conn.execute(sql.SQL('DROP ROLE IF EXISTS {}').format(sql.Identifier(role)))


@pytest.fixture
def joint_schema(scram_scope, database_cleanup, request):
    base, policy, dsns = scram_scope
    old = fixture_row(base, policy)
    verified = {**old, 'result_id': 'crop-cycle-verified-result-v1:'+'1'*64,
                'artifact_ref': 'crop-cycle-verified-artifact-v1:'+'3'*64}
    packet = legacy_metadata(verified); packet['schema_version'] = 'crop-cycle-verified-result-v1'
    verified_raw = _canonical(packet)
    verified.update(payload_raw=verified_raw, payload_sha256=sha256(verified_raw).hexdigest())
    tables = ('crop_cycle_research_results', 'crop_cycle_verified_research_results')
    with base.connect() as conn:
        assert conn.pgconn.used_password; owner(conn, policy)
        insert_legacy(conn, policy, old); install_calculation_cycle_crop_result_schema(conn, policy.schema)
        insert(conn, policy, verified, tables[1])
        before = [conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(policy.schema, t))).fetchall() for t in tables]
        model.install_joint_crop_climate_result_schema(conn, policy.schema)
    row = {'tenant_id': old['tenant_id'], 'study_id': 'joint-schema-study', 'revision': 'r1',
        'result_id': 'joint-crop-climate-result-v1:'+'1'*64,
        **{k: old[k] for k in ('scenario_id', 'scenario_revision', 'registration_job_id', 'registration_sha256')},
        'crop_id': 'schema-crop', 'batch_id': 'schema-batch', 'zone_id': 'schema-zone', 'program_id': 'schema-program',
        **{k: str(i)*64 for i, k in enumerate(('source_sha256', 'context_sha256', 'time_binding_sha256',
            'evidence_sha256', 'artifact_sha256', 'artifact_header_sha256', 'intent_sha256',
            'farm_binding_sha256', 'head_sha256'), 1)},
        'proof_sha256': 'a'*64, 'integrity_signature': 'b'*64,
        'artifact_ref': 'joint-crop-climate-storage-research-v1:'+'5'*64, 'artifact_status': 'completed',
        'steps': 16, 'planned_steps': 16, 'sample_count': 3, 'event_count': 3, 'commit_count': 4,
        'storage_bytes': 2048, 'file_count': 12, 'registered_by': policy.roles['authority'],
        'start_utc': '2026-10-01T00:00:00.123456Z', 'end_utc': '2026-10-01T00:00:32.123456Z'}
    yield base, policy, dsns, payload(row)
    with base.connect() as conn:
        owner(conn, policy)
        after = [conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(policy.schema, t))).fetchall() for t in tables]
    assert after == before
    save(request.node.name+'-preservation.json', {'legacy_tables': list(tables), 'unchanged_rows': [len(v) for v in after]})


def test_invalid_schema_identifiers_are_rejected_before_sql():
    cases = (None, True, 12, 'bad-name', 'x;DROP SCHEMA public', 'a'*64, 'Mixed', '')
    for schema in cases:
        with pytest.raises(ValueError): model.install_joint_crop_climate_result_schema(None, schema)
    save('identifiers.json', {'rejected': len(cases)})


@pytest.mark.parametrize('login_scope', [{'crop_cycle_result_storage': True}], indirect=True)
def test_scram_roundtrip_original_bytes_and_no_new_runtime_grants(joint_schema):
    base, policy, dsns, row = joint_schema
    row = payload(row, raw=row['payload_raw']+b' '*(131072-len(row['payload_raw'])))
    with base.connect() as conn:
        owner(conn, policy); insert(conn, policy, row)
        actual = conn.execute(sql.SQL('SELECT * FROM {}').format(sql.Identifier(policy.schema, model.TABLE))).fetchone()
        for key, value in row.items():
            assert (bytes(actual[key]) if key == 'payload_raw' else str(actual[key]) if key == 'registration_job_id' else actual[key]) == (
                str(value) if key == 'registration_job_id' else value)
        assert actual['recorded_at'].tzinfo is not None
    with base.connect() as conn: assert audit_runtime_roles(conn, policy)['tables'] > 0
    denied = 0; target = sql.Identifier(policy.schema, model.TABLE)
    for kind, dsn in dsns.items():
        for statement in (sql.SQL('SELECT * FROM {} LIMIT 0'), sql.SQL('INSERT INTO {} DEFAULT VALUES'),
                          sql.SQL('UPDATE {} SET revision=revision'), sql.SQL('DELETE FROM {}'), sql.SQL('TRUNCATE {}')):
            with connect_runtime(dsn, policy, kind) as conn, pytest.raises(errors.InsufficientPrivilege):
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
                if kind == 'supervisor': conn.execute('SET TRANSACTION READ WRITE')
                conn.execute(statement.format(target))
            denied += 1
    save('roundtrip.json', {'payload_sha256': row['payload_sha256'], 'raw_bytes': len(row['payload_raw']),
        'all_column_count': len(row), 'start_utc': actual['start_utc'], 'end_utc': actual['end_utc'],
        'runtime_denials': denied, 'roles': len(dsns), 'equation_calls': 0, 'actual_crop_Runs': 0})


@pytest.mark.parametrize('login_scope', [{'crop_cycle_result_storage': True}], indirect=True)
def test_matching_raw_cannot_bypass_bounds_ids_sha_or_utc(joint_schema):
    base, policy, _, row = joint_schema
    cases = [(k, v) for k in ('tenant_id', 'study_id', 'revision', 'scenario_id', 'scenario_revision',
             'crop_id', 'batch_id', 'zone_id', 'program_id', 'registered_by') for v in ('', 'a'*201, 'bad space', 'a\n')]
    cases += [(k, v) for k in ('registration_sha256', 'source_sha256', 'context_sha256', 'time_binding_sha256',
              'evidence_sha256', 'artifact_sha256', 'artifact_header_sha256', 'intent_sha256',
              'farm_binding_sha256', 'head_sha256', 'proof_sha256', 'integrity_signature') for v in ('G'*64, '1'*63, '1'*64+' ')]
    cases += [('result_id', 'crop-cycle-verified-result-v1:'+'1'*64), ('artifact_ref', '/tmp/result'),
              ('artifact_status', 'approved'), ('steps', -1), ('steps', 17), ('planned_steps', 0),
              ('planned_steps', 4097), ('sample_count', -1), ('sample_count', 513), ('event_count', -1),
              ('event_count', 129), ('commit_count', 0), ('commit_count', 4098), ('storage_bytes', 0),
              ('storage_bytes', 536870913), ('file_count', 0), ('file_count', 65537)]
    cases += [(k, v) for k in ('start_utc', 'end_utc') for v in ('2026-02-30T00:00:00.123456Z',
              '0000-01-01T00:00:00.000000Z', '2026-10-01T00:00:00.1234567Z', '2026-10-01T00:00:00Z',
              '2026-10-01T00:00:00.123456+00:00', '2026-10-01T00:00:60.123456Z')]
    cases += [('end_utc', row['start_utc']), ('end_utc', '2026-10-01T00:00:00.123455Z'),
              ('end_utc', '2026-10-01T00:10:00.123457Z')]
    with base.connect() as conn:
        owner(conn, policy)
        for key, value in cases:
            rejected(conn, policy, payload({**row, key: value}),
                     (errors.CheckViolation, psycopg.DataError) if key in ('start_utc', 'end_utc') else errors.CheckViolation)
        rejected(conn, policy, {**row, 'payload_sha256': '0'*64})
        for raw in (b'', b' '*131073): rejected(conn, policy, payload(row, raw=raw), (errors.CheckViolation, psycopg.DataError))
        upper = payload({**row, 'steps': 4096, 'planned_steps': 4096, 'sample_count': 512, 'event_count': 128,
            'commit_count': 4097, 'storage_bytes': 536870912, 'file_count': 65536,
            'end_utc': '2026-10-01T00:10:00.123456Z'})
        insert(conn, policy, upper)
    save('bounds.json', {'rejected_columns': len(cases), 'bad_payload_hash': 1, 'raw_size_rejections': 2,
        'accepted_exact_upper_bounds': True, 'one_microsecond_over_horizon_rejected': True})


@pytest.mark.parametrize('login_scope', [{'crop_cycle_result_storage': True}], indirect=True)
def test_rehashed_raw_closed_shape_duplicates_types_and_every_pin(joint_schema):
    base, policy, _, row = joint_schema; packets = []
    original = metadata(row)
    for path, replacement in ((('schema_version',), 'crop-cycle-verified-result-v1'), (('status',), 'approved'),
        (('claim_scope',), 'production_prediction'), (('G0_G4',), 'pass'), (('binding',), []), (('policies',), None), (('code',), 'x')):
        v = deepcopy(original); v[path[0]] = replacement; packets.append(v)
    for group in (None, 'farm', 'input', 'artifact'):
        for fault in ('extra', 'missing', 'null', 'array'):
            v = deepcopy(original); obj = v if group is None else v[group]
            if fault == 'extra': obj['unknown'] = True
            elif fault == 'missing': del obj[next(iter(obj))]
            elif group is None: v = None if fault == 'null' else []
            else: v[group] = None if fault == 'null' else []
            packets.append(v)
    pins = [(None, k) for k in ('tenant_id', 'study_id', 'revision', 'result_id')]
    pins += [(group, k) for group in ('farm', 'input', 'artifact') for k in original[group]]
    for group, key in pins:
        v = deepcopy(original); obj = v if group is None else v[group]
        obj[key] = obj[key]+1 if type(obj[key]) is int else str(obj[key])+'x'; packets.append(v)
    for key in ('steps', 'planned_steps', 'sample_count', 'event_count', 'commit_count', 'storage_bytes', 'file_count'):
        for value in (True, float(row[key]), str(row[key]), None):
            v = deepcopy(original); v['artifact'][key] = value; packets.append(v)
    raw_cases = [_canonical(v) for v in packets]
    raw_cases += [row['payload_raw'].replace(b'"steps":16', b'"steps":1.6e1'),
        row['payload_raw'].replace(b'"tenant_id":"tenant-a"', b'"tenant_id":"tenant-a","tenant_id":"tenant-a"'),
        row['payload_raw'].replace(b'"binding":{}', b'"binding":{"x":1,"x":1}'),
        row['payload_raw'].replace(b'"binding":{}', b'"binding":{"x":1,"\\u0078":1}'), b'{', b'\xff', b'null', b'[]']
    with base.connect() as conn:
        owner(conn, policy)
        for raw in raw_cases: rejected(conn, policy, payload(row, raw=raw), (errors.CheckViolation, psycopg.DataError))
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(policy.schema, model.TABLE))).fetchone()['n'] == 0
    save('raw.json', {'rehashed_rejections': len(raw_cases), 'individual_column_pins': len(pins),
        'duplicate_top_and_nested': True, 'inserted_rows': 0})


@pytest.mark.parametrize('login_scope', [{'crop_cycle_result_storage': True}], indirect=True)
def test_unique_intent_tenant_fk_hold_and_immutable_reinstall(joint_schema):
    base, policy, _, row = joint_schema; target = sql.Identifier(policy.schema, model.TABLE)
    with base.connect() as conn:
        owner(conn, policy)
        for changes in ({'tenant_id': 'tenant-b'}, {'registration_job_id': uuid4()}):
            rejected(conn, policy, payload({**row, **changes}), errors.ForeignKeyViolation)
        hold = payload({**row, 'artifact_status': 'hold', 'steps': 0, 'sample_count': 0, 'event_count': 0})
        insert(conn, policy, hold)
        for changes in ({}, {'study_id': 'other', 'result_id': 'joint-crop-climate-result-v1:'+'2'*64},
                        {'study_id': 'other', 'intent_sha256': 'c'*64}):
            rejected(conn, policy, payload({**row, **changes}), errors.UniqueViolation)
        for statement in (sql.SQL('UPDATE {} SET revision=revision'), sql.SQL('DELETE FROM {}')):
            with pytest.raises(errors.RaiseException, match='immutable'), conn.transaction(): conn.execute(statement.format(target))
        with pytest.raises(errors.DuplicateTable): model.install_joint_crop_climate_result_schema(conn, policy.schema)
        renamed = sql.Identifier(policy.schema, 'joint_schema_atomic_probe')
        conn.execute(sql.SQL('ALTER TABLE {} RENAME TO joint_schema_atomic_probe').format(target))
        with pytest.raises(errors.DuplicateFunction): model.install_joint_crop_climate_result_schema(conn, policy.schema)
        assert conn.execute('SELECT to_regclass(%s) AS name', (policy.schema+'.'+model.TABLE,)).fetchone()['name'] is None
        conn.execute(sql.SQL('ALTER TABLE {} RENAME TO {}').format(renamed, sql.Identifier(model.TABLE)))
        actual = conn.execute(sql.SQL('SELECT * FROM {}').format(target)).fetchone()
        assert bytes(actual['payload_raw']) == hold['payload_raw'] and actual['steps'] == 0
    save('identity.json', {'foreign_key_rejections': 2, 'unique_rejections': 3, 'immutable_rejections': 2,
        'duplicate_install_rejections': 1, 'partial_install_rollback': True,
        'hold_zero_steps_accepted': True, 'unchanged_payload_sha256': hold['payload_sha256']})
