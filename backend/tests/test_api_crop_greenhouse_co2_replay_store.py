"""Actual SCRAM storage supplies original CO2 projection inputs; no HTTP claim."""
from datetime import datetime
from hashlib import sha256
import ctypes
import gc
import json
import os
from pathlib import Path
import subprocess

import psycopg
import pytest

from app import api_crop_greenhouse_co2_replay as public
import test_crop_greenhouse_co2_result_store as registered
from test_crop_greenhouse_co2_result_store import (authoring, profiles, login_database as original_login_database,
    original_login_scope, login_scope, setup, settle_owned_database_backends)
from test_api_crop_greenhouse_co2_replay import private_fields_absent

pytestmark = registered.pytestmark


def save(name, value):
    directory = os.environ.get('OSSF_JOINT_PREFIX_SDK_EVIDENCE')
    if directory:
        with (Path(directory)/('co2-projection-store-'+name)).open('x') as handle:
            os.fchmod(handle.fileno(), 0o400)
            json.dump(value, handle, sort_keys=True, indent=2)
            handle.flush(); os.fsync(handle.fileno())


@pytest.fixture(scope='module')
def login_database():
    run = subprocess.run; owned = []
    def launch(argv, *args, **kwargs):
        binary = os.environ.get('OSSF_TEST_PG_BIN')
        if binary and Path(argv[0]) == Path(binary)/'pg_ctl' and 'start' in argv and '-o' in argv:
            argv = list(argv); index = argv.index('-o')+1
            argv[index] += ' -c work_mem=64kB -c jit=off'
            owned.append(True)
        return run(argv, *args, **kwargs)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(subprocess, 'run', launch)
        fixture = original_login_database.__wrapped__()
        try:
            database = next(fixture)
            with psycopg.connect(database['admin'], options='-c statement_timeout=5000') as conn:
                settings = conn.execute("SELECT current_setting('work_mem'), current_setting('jit'), current_setting('shared_buffers')").fetchone()
                if owned: assert settings == ('64kB', 'off', '4MB')
            save('database-settings.json', {'explicit_options': True, 'work_mem': settings[0],
                'jit': settings[1], 'shared_buffers': settings[2], 'owned_test_database_only': bool(owned)})
            yield {**database, 'co2_projection_owned_budget': bool(owned)}
        finally:
            fixture.close()


@pytest.fixture(scope='module', autouse=True)
def cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas = conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles = conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
    assert schemas == roles == 0
    save('database-cleanup.json', {'schemas': schemas, 'roles': roles})


@pytest.mark.parametrize('setup', [pytest.param(None, id='normal'), pytest.param('hold', id='hold')], indirect=True)
def test_actual_scram_original_result_projection(setup, monkeypatch, login_database):
    result, request_raw, value, done = registered.ready(setup)
    rss = lambda: int(next(line for line in Path('/proc/self/status').read_text().splitlines()
        if line.startswith('VmRSS:')).split()[1])*1024
    allocation_before = rss()
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    allocation_after = rss()
    record = result.put('tenant-1', request_raw); farm = value[1]['farm']
    before = registered.producer.reference.counts(result.server.binding)
    fd = len(os.listdir('/proc/self/fd')); calls = registered.producer.reference.forbid(monkeypatch)
    calls['SQL_writes'] = 0; execute = psycopg.Connection.execute
    def read_only(conn, query, *args, **kwargs):
        text = query.as_string(conn) if hasattr(query, 'as_string') else query
        if text.split(None, 1)[0].upper() in ('INSERT', 'UPDATE', 'DELETE', 'TRUNCATE', 'CREATE', 'ALTER', 'DROP', 'GRANT', 'REVOKE'):
            calls['SQL_writes'] += 1
            pytest.fail('projection or current read attempted a SQL mutation')
        return execute(conn, query, *args, **kwargs)
    with monkeypatch.context() as patch:
        patch.setattr(psycopg.Connection, 'execute', read_only)
        with result.jobs.connect() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
            if login_database['co2_projection_owned_budget']:
                assert conn.execute("SELECT current_setting('work_mem') AS work_mem, current_setting('jit') AS jit").fetchone() == {'work_mem': '64kB', 'jit': 'off'}
        with result._read('tenant-1', record['result_id'], farm) as (row, packet, session):
            assert result._record(row) == record and record['progress_raw'] == done
            with public.storage.artifact.open_artifact(session.path, packet['artifact']['sha256']) as reader:
                terminal = {**reader.summary, 'manifest': reader._context['manifest'],
                    'time_binding': reader._header['binding']}
                program = reader._context['program']
                pages = {kind: reader.page(kind) for kind in ('samples', 'events')}
                responses = {}
                for view in ('summary', 'samples', 'events'):
                    projected = public.project_co2_result(record, terminal, source_program=program, view=view,
                        page=None if view == 'summary' else pages[view],
                        limit=None if view == 'summary' else 64 if view == 'samples' else 8)
                    body = public._public_bytes(projected); parsed = json.loads(body)
                    assert parsed['recorded_at'] == record['recorded_at'].isoformat(timespec='microseconds').replace('+00:00', 'Z')
                    assert parsed['reference']['progress_sha256'] == record['progress_sha256']
                    assert parsed['reference']['rights_or_gate_approval'] is False
                    if view == 'summary':
                        assert parsed['summary']['last_confirmed']['value'] == terminal['last_confirmed']
                        assert parsed['summary']['last_confirmed']['time'] == terminal['times']['last_confirmed']
                    elif view == 'samples':
                        assert [{'value': row['value'], 'time': row['time']} for row in parsed['page']['records']] == pages[view]['records']
                    private_fields_absent(parsed)
                    responses[view] = {'bytes': len(body), 'sha256': sha256(body).hexdigest()}
        assert result.get('tenant-1', record['result_id'], farm) == record
    assert registered.producer.reference.counts(result.server.binding) == before
    assert all(value == 0 for value in calls.values()) and len(os.listdir('/proc/self/fd')) == fd
    status = json.loads(done)['status']
    save(status+'.json', {'actual_scram': True, 'registered_original_record': True,
        'producer_GC_RSS_before_after': [allocation_before, allocation_after],
        'status': status, 'responses': responses, 'progress_original_bytes': len(done),
        'original_counts_and_times': terminal['counts'], 'counts_before_after': [before, before],
        'private_fields_absent': True, 'basis_from_same_verified_reader_program': True,
        'calls': calls, 'FD_before_after': [fd, fd], 'G0_G4': 'not_assessed'})
    save(status+'-fresh-pack.private.json', {'record': {key: item.decode() if isinstance(item, bytes)
        else item.isoformat() if isinstance(item, datetime) else item for key, item in record.items()},
        'terminal': terminal, 'pages': pages, 'program': program, 'expected': responses,
        'captured_from_actual_SCRAM_record': True, 'scope': 'projection_only_no_current_DB_authorization'})
