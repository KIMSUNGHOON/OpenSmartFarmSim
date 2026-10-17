"""Read stored metadata from the owned synthetic probe after its actors stop."""
from datetime import timezone
from hashlib import sha256
import json
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row


def _need(value):
    if not value:
        raise ValueError('owned probe metadata unavailable')


def read_stored_checkpoint(config_path, data_directory):
    config_path, data_directory = Path(config_path), Path(data_directory)
    info = config_path.lstat()
    _need(not config_path.is_symlink() and info.st_uid == os.getuid()
        and info.st_mode & 0o077 == 0 and 0 < info.st_size <= 64*1024
        and not data_directory.is_symlink()
        and data_directory.parent.name.startswith('ossf-login-pg-'))
    config = json.loads(config_path.read_bytes())
    _need(Path(config['root']).resolve() == config_path.parent.resolve())
    configured = conninfo_to_dict(config['database']['admin'])
    _need(configured.get('host') == str(data_directory.parent/'socket')
        and configured.get('user') == 'ossf_login_admin'
        and configured.get('dbname') == 'postgres'
        and int(configured.get('port', 0)) == int(config['database']['port']))
    with psycopg.connect(config['database']['admin'], row_factory=dict_row, connect_timeout=2,
            options='-c statement_timeout=2000 -c default_transaction_read_only=on') as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        identity = conn.execute("SELECT current_setting('data_directory') AS directory, "
            "session_user AS authenticated, current_user AS effective, current_database() AS database, "
            "current_setting('transaction_read_only') AS read_only, "
            "current_setting('transaction_isolation') AS isolation").fetchone()
        _need(Path(identity['directory']).resolve() == data_directory.resolve()
            and identity['authenticated'] == identity['effective'] == 'ossf_login_admin'
            and identity['database'] == 'postgres' and identity['read_only'] == 'on'
            and identity['isolation'] == 'repeatable read')
        schemas = conn.execute('SELECT nspname FROM pg_namespace '
            'WHERE substring(nspname FROM 1 FOR 11)=%s LIMIT 2', ('login_test_',)).fetchall()
        _need(len(schemas) == 1)
        namespace = schemas[0]['nspname']
        from app import crop_greenhouse_solar_execution_checkpoint as checkpoints
        rows = conn.execute(sql.SQL("SELECT job_id,state,attempt_count,reason FROM {}.jobs "
            "WHERE tenant_id=%s AND stage='simulation' AND "
            "convert_from(input_bytes,'UTF8')::jsonb->>'input_version'=%s LIMIT 2")
            .format(sql.Identifier(namespace)), ('tenant-1', checkpoints.execution.INPUT_VERSION)).fetchall()
        _need(len(rows) <= 1)
        result = {'evidence_kind':'stored_owned_fixture_metadata_only',
            'normal_execution_accepted':False, 'rights_or_gate_approval':False, 'G0_G4':'not_assessed',
            'transaction_read_only':True, 'owned_cluster_identity_verified':True,
            'transaction_isolation':'repeatable read',
            'job':None, 'stored_checkpoint':None}
        if rows:
            job = rows[0]
            _need(job['state'] in ('queued','simulating','succeeded','hold','failed','canceled')
                and type(job['attempt_count']) is int and 0 <= job['attempt_count'] <= 3)
            result['job'] = {'state':job['state'], 'attempt':job['attempt_count']}
            code = job['reason'].get('code') if type(job['reason']) is dict else None
            if code in ('solar_execution_busy','solar_execution_hold','solar_execution_runtime_failure',
                    'solar_numerical_hold','completed','canceled_by_request','attempts_exhausted'):
                result['job']['reason_code'] = code
            row = conn.execute(sql.SQL("SELECT reason,recorded_at FROM {}.job_events "
                "WHERE tenant_id=%s AND job_id=%s AND kind=%s "
                "ORDER BY (reason->>'publication_sequence')::int DESC LIMIT 1")
                .format(sql.Identifier(namespace)), ('tenant-1', job['job_id'], checkpoints.EVENT_KIND)).fetchone()
            if row is not None:
                payload = checkpoints._payload(row['reason'])
                result['stored_checkpoint'] = {k:payload[k] for k in (
                    'steps','planned_steps','status','computed_through_utc','publication_sequence')}
                result['checkpoint_payload_sha256'] = sha256(
                    checkpoints.custody._canonical(payload)).hexdigest()
                result['checkpoint_recorded_at'] = row['recorded_at'].astimezone(timezone.utc).isoformat()
        result['observed_at'] = conn.execute('SELECT clock_timestamp() AS at').fetchone()['at'].astimezone(timezone.utc).isoformat()
    _need(len(json.dumps(result).encode()) <= 16*1024)
    return result
