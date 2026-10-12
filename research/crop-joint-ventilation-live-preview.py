"""Prepare owned ventilation inputs and activate them on the preserved preview DB."""
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import importlib.util
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


common = module('owned_preview_common', ROOT/'research/crop-climate-joint-live-preview.py')
save = common.save


def prepare(args):
    from app.crop_result_store import WRITE_SCOPES
    from app.runtime_roles import RuntimeLoginPolicy
    import test_crop_greenhouse_ventilation_input_evidence as inputs
    original = args.original_directory
    previous_raw = (original/'runtime.private.json').read_bytes()
    previous = json.loads(previous_raw)
    directory = args.directory
    directory.mkdir(mode=0o700)
    packet_root = directory/'inputs'; packet_root.mkdir(mode=0o700)
    custody = directory/'custody'; custody.mkdir(mode=0o700)
    request_root = directory/'requests'; request_root.mkdir(mode=0o700)
    profiles = inputs.profiles.__wrapped__()
    input_key, custody_key, result_key = (secrets.token_bytes(32) for _ in range(3))
    assert len({input_key, custody_key, result_key, *(bytes.fromhex(previous[field])
        for field in ('input_key', 'custody_key', 'result_key'))}) == 6
    body = json.loads((original/'requests/normal-user.json').read_bytes())
    packets, reviews, requests = {}, {}, {}
    for mode in ('normal', 'hold'):
        case = deepcopy(inputs.reference.reference.CASES[6])
        case.update(step_count=64, output_steps=list(range(0, 65, 8)))
        for event in case['events']: event['step_index'] *= 4
        if mode == 'hold': case['events'][-1]['event']['values']['leaf']['value'] = 50000
        origin = inputs.reference.origin('2026-10-01T00:00:00.123456Z')
        packet = inputs.packet(packet_root/mode, profiles, case, origin)
        packet[3].update(evidence_id='owned-ventilation-preview-'+mode+'-review-v1',
            reviewer_id='codex-20261012-ventilation-software', decision_id='codex-20261012-ventilation-'+mode+'-v1')
        authority = inputs.authority(packet[3], key=input_key, issuer='owned-preview-ventilation',
                                     key_id='owned-preview-ventilation-v1')
        proof = inputs.issue(authority, packet)
        receipt = inputs.verify(authority, packet, proof)
        assert not receipt.rights_or_gate_approval
        proof_file = packet_root/(mode+'.proof.private.json'); save(proof_file, proof, raw=True)
        reviews[packet[3]['evidence_id']] = packet[3]
        packets[packet[1]] = {'directory':str(packet[0]), 'proof':str(proof_file)}
        request = deepcopy(body)
        request['input'].update(schema_version=inputs.model.SOURCE_VERSION,
            program_id=packet[2]._context.program['scenario']['input_id'], source_sha256=packet[1],
            context_sha256=packet[2]._context.root_sha256, time_binding_sha256=packet[2].sha256,
            evidence_sha256=sha256(proof).hexdigest())
        from app.crop_greenhouse_ventilation_farm_binding import RIGHTS_VERSION
        request['rights'].update(schema_version=RIGHTS_VERSION, declaration_id='owned-ventilation-preview-source',
                                 input_source_sha256=packet[1])
        requests[mode] = request
    rights_file, reviews_file = directory/'rights.private.json', directory/'reviews.private.json'
    save(rights_file, {source:True for source in packets}); save(reviews_file, reviews)
    for name, mode in [('normal-validation', 'normal'), ('hold-validation', 'hold'),
                       ('cancel-validation', 'normal'), ('normal-user', 'normal')]:
        request = deepcopy(requests[mode])
        request.update(study_id='ventilation-user-preview', revision=name+'-v1')
        save(request_root/(name+'.json'), request)
    policy = replace(RuntimeLoginPolicy(**previous['policy']), crop_greenhouse_ventilation_result_storage=True)
    config = {'runtime_version':'owned-joint-ventilation-preview-runtime-v1',
        'original_operator':str(original/'joint_prefix_live_operator_v1.py'),
        'original_operator_sha256':sha256((original/'joint_prefix_live_operator_v1.py').read_bytes()).hexdigest(),
        'original_runtime_sha256':sha256(previous_raw).hexdigest(), 'policy':asdict(policy),
        'worker_chunk_budget':8, 'scopes':sorted(set(previous['scopes']) | set(WRITE_SCOPES)
            | {'metadata', 'simulation_create', 'simulation_execute', 'cancel'}),
        'auth':{field:previous[field] for field in ('token_digest', 'issued_at', 'expires_at')},
        'ventilation':{'input_key':input_key.hex(), 'custody_key':custody_key.hex(), 'result_key':result_key.hex(),
            'custody':str(custody), 'inputs':packets, 'rights_file':str(rights_file), 'reviews_file':str(reviews_file)}}
    save(directory/'runtime.private.json', config)
    source = ROOT/'research/crop-joint-ventilation-live-operator.py'
    save(directory/'mixed_live_operator.py', source.read_bytes(), raw=True)
    operator = module('owned_mixed_preflight', directory/'mixed_live_operator.py')
    checked, old, _ = operator.load()
    assert checked == config and old == previous
    save(directory/'prepared.private.json', {'source_root':str(ROOT), 'synthetic':True, 'G0_G4':'not_assessed',
        'real_farm_runs':0, 'simulated_seconds':128, 'steps':64, 'input_sources':sorted(packets),
        'six_model_keys_distinct':True, 'original_runtime_sha256':sha256(previous_raw).hexdigest(),
        'operator_sha256':sha256(source.read_bytes()).hexdigest(), 'input_reviews':sorted(reviews)})
    print(json.dumps({'prepared':True, 'synthetic':True, 'models':2, 'new_inputs':2, 'G0_G4':'not_assessed'}))


def existing_schema(conn, policy):
    """Compare an installed table with a rolled-back fresh installation."""
    from psycopg import sql
    from uuid import uuid4
    from app.crop_greenhouse_ventilation_result_schema import install_joint_ventilation_result_schema, TABLE

    def fingerprint(schema):
        name = schema+'.'+TABLE
        relation = conn.execute('SELECT relkind,relpersistence,relrowsecurity,relforcerowsecurity '
            'FROM pg_class WHERE oid=to_regclass(%s)', (name,)).fetchone()
        columns = conn.execute('SELECT attname,format_type(atttypid,atttypmod) AS type,attnotnull,'
            'attidentity,attgenerated,pg_get_expr(adbin,adrelid) AS default_expression '
            'FROM pg_attribute LEFT JOIN pg_attrdef ON adrelid=attrelid AND adnum=attnum '
            'WHERE attrelid=to_regclass(%s) AND attnum>0 AND NOT attisdropped ORDER BY attnum', (name,)).fetchall()
        constraints = conn.execute('SELECT conname,convalidated,pg_get_constraintdef(oid) AS definition '
            'FROM pg_constraint WHERE conrelid=to_regclass(%s) ORDER BY conname', (name,)).fetchall()
        indexes = conn.execute('SELECT indisvalid,indisready,pg_get_indexdef(indexrelid) AS definition '
            'FROM pg_index WHERE indrelid=to_regclass(%s) ORDER BY pg_get_indexdef(indexrelid)', (name,)).fetchall()
        triggers = conn.execute('SELECT tgname,tgenabled,pg_get_triggerdef(oid) AS definition,'
            'pg_get_functiondef(tgfoid) AS function_definition FROM pg_trigger '
            'WHERE tgrelid=to_regclass(%s) AND NOT tgisinternal ORDER BY tgname', (name,)).fetchall()
        return json.dumps([relation,columns,constraints,indexes,triggers], sort_keys=True).replace(schema+'.', 'verified_schema.')

    installed = fingerprint(policy.schema)
    scratch = 'ossf_preview_check_'+uuid4().hex
    class RolledBackReference(Exception):
        pass
    try:
        with conn.transaction():
            conn.execute('RESET ROLE')
            conn.execute(sql.SQL('CREATE SCHEMA {} AUTHORIZATION {}').format(sql.Identifier(scratch), sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
            conn.execute(sql.SQL('CREATE TABLE {} (tenant_id text,job_id uuid,PRIMARY KEY(tenant_id,job_id))')
                .format(sql.Identifier(scratch,'jobs')))
            install_joint_ventilation_result_schema(conn, scratch)
            expected = fingerprint(scratch)
            raise RolledBackReference()
    except RolledBackReference:
        pass
    if installed != expected:
        raise ValueError('owned installed ventilation schema mismatch')


def provision(admin, policy, *, enabled=True):
    import psycopg
    from psycopg import sql
    from app.crop_greenhouse_ventilation_result_schema import install_joint_ventilation_result_schema, TABLE
    from app.runtime_roles import audit_runtime_roles
    if policy.crop_greenhouse_ventilation_result_storage is not enabled:
        raise ValueError('owned ventilation storage policy mismatch')
    with psycopg.connect(admin, row_factory=psycopg.rows.dict_row) as conn:
        conn.execute(sql.SQL('SET LOCAL ROLE {}').format(sql.Identifier(policy.owner)))
        if enabled:
            if conn.execute('SELECT to_regclass(%s) AS relation', (policy.schema+'.'+TABLE,)).fetchone()['relation']:
                existing_schema(conn, policy)
            else:
                install_joint_ventilation_result_schema(conn, policy.schema)
            conn.execute(sql.SQL('GRANT SELECT,INSERT ON {} TO {}').format(
                sql.Identifier(policy.schema, TABLE), sql.Identifier(policy.roles['authority'])))
        elif conn.execute('SELECT to_regclass(%s) AS relation', (policy.schema+'.'+TABLE,)).fetchone()['relation']:
            conn.execute(sql.SQL('REVOKE SELECT,INSERT ON {} FROM {}').format(
                sql.Identifier(policy.schema, TABLE), sql.Identifier(policy.roles['authority'])))
        audit_runtime_roles(conn, policy)


def stop_owned_process(process, *, timeout):
    """Wait on an unreaped direct child and escalate through its pinned pidfd."""
    forced = False
    if process.poll() is None:
        fd = os.pidfd_open(process.pid)
        try:
            try: signal.pidfd_send_signal(fd, signal.SIGTERM)
            except ProcessLookupError: pass
            try: process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                forced = True
                try: signal.pidfd_send_signal(fd, signal.SIGKILL)
                except ProcessLookupError: pass
                process.wait(timeout=5)
        finally: os.close(fd)
    return {'exit':process.returncode, 'forced':forced}


def stop_owned_services(workers, nginx, server, thread, logs):
    stopped, errors = [], []
    for child in (*workers, *((nginx,) if nginx is not None else ())):
        try: stopped.append(stop_owned_process(child, timeout=60 if child in workers else 15))
        except Exception: errors.append('child_cleanup_failed')
    server.should_exit = True
    try:
        thread.join(30)
        if thread.is_alive(): errors.append('api_cleanup_incomplete')
    except Exception: errors.append('api_cleanup_failed')
    for log in logs:
        try: log.close()
        except Exception: errors.append('log_cleanup_failed')
    return {'children':stopped, 'errors':errors, 'service_stopped':not errors}


def serve(args):
    from app import crop_greenhouse_ventilation_operator_config as loader
    from app.http_identity import token_digest
    from app.runtime_roles import RuntimeLoginPolicy
    directory, original = args.directory, args.original_directory
    operator = module('owned_mixed_operator', directory/'mixed_live_operator.py')
    value, previous, _ = operator.load()
    assert (directory/'mixed_live_operator.py').read_bytes() == (ROOT/'research/crop-joint-ventilation-live-operator.py').read_bytes()
    access = json.loads(args.original_access.read_bytes())
    assert token_digest(access['token'].encode()) == value['auth']['token_digest']
    expires = datetime.fromisoformat(value['auth']['expires_at'])
    assert expires > datetime.now(timezone.utc)+timedelta(minutes=1)
    run = directory/args.run; run.mkdir(mode=0o700)
    save(run/'access.private.json', access)
    cert, key = common.certificate(run, args.ttl_seconds)
    config = {'config_version':loader.MIXED_PREFIX_VERSION, 'policy':value['policy'],
        'artifact_root':previous['artifacts'], 'certificate':str(cert), 'private_key':str(key),
        'authored_run_gate_key_file':None, 'content_access':None, 'host':'127.0.0.1', 'port':args.api_port,
        'dependencies_factory':'mixed_live_operator:dependencies',
        **dict.fromkeys(('crop_climate_joint_execution', 'crop_climate_joint_prefix',
                        'crop_greenhouse_ventilation_execution', 'crop_greenhouse_ventilation_prefix'), True)}
    for field, raw in [('dsn_file', previous['dsn'].encode()),
                       ('thermal_gate_key_file', bytes.fromhex(previous['thermal_key'])),
                       ('market_hold_key_file', bytes.fromhex(previous['market_key']))]:
        path = run/field; save(path, raw, raw=True); config[field] = str(path)
    path = run/'operator.private.json'; save(path, config)
    sys.path.insert(0, str(directory)); stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT): signal.signal(sig, lambda *_:stop.set())
    with common.running_database(args, original, args.run) as (_, admin):
        try:
            provision(admin, RuntimeLoginPolicy(**value['policy']))
            runtime = loader.load_ventilation_api_runtime(path); server = runtime.service.server()
            with runtime.jobs.connect() as conn:
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
            thread = threading.Thread(target=server.run, daemon=True); thread.start()
            workers, logs, nginx = [], [], None
            try:
                env = {**os.environ, 'PYTHONPATH':os.pathsep.join([str(directory), str(ROOT/'backend'), str(ROOT/'backend/tests')])}
                for name in ('joint', 'ventilation'):
                    log = (run/('worker-'+name+'.private.log')).open('xb'); os.fchmod(log.fileno(), 0o600); logs.append(log)
                    workers.append(subprocess.Popen([sys.executable, '-B', '-m', 'app.deterministic_work',
                        '--factory', 'mixed_live_operator:worker_'+name], env=env,
                        stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT))
                template = (ROOT/'web/nginx.conf').read_text()
                mapping = {'/tmp/nginx.pid':str(run/'nginx.pid'), '/etc/nginx/mime.types':str(args.nginx.parents[1]/'conf/mime.types'),
                    'listen 8444 ssl;':f'listen 127.0.0.1:{args.web_port};', '/run/operator/web/cert.pem':str(cert),
                    '/run/operator/web/key.pem':str(key), '/run/operator/web/api-ca.pem':str(cert),
                    '/usr/share/nginx/html':str(args.dist), 'https://127.0.0.1:8443':f'https://127.0.0.1:{args.api_port}'}
                for name in ('client', 'proxy', 'fastcgi', 'uwsgi', 'scgi'): mapping['/tmp/'+name+'-temp'] = str(run/(name+'-temp'))
                for old, new in mapping.items(): assert old in template; template = template.replace(old, new)
                marker = '        location /assets/ {'
                status = ('        location = /development-status.json {\n'
                    f'            alias {args.status_file};\n            default_type application/json;\n'
                    '            add_header Cache-Control no-store always;\n        }\n\n')
                assert marker in template; template = template.replace(marker, status+marker, 1)
                (run/'logs').mkdir(mode=0o700); nginx_config = run/'nginx.conf'; save(nginx_config, template.encode(), raw=True)
                log = (run/'nginx.private.log').open('xb'); os.fchmod(log.fileno(), 0o600); logs.append(log)
                nginx = subprocess.Popen([str(args.nginx), '-p', str(run)+'/', '-c', str(nginx_config), '-g', 'daemon off;'],
                    stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                deadline = time.monotonic()+20
                def started_consumers():
                    for name in ('joint', 'ventilation'):
                        raw = (run/('worker-'+name+'.private.log')).read_text()
                        if not raw: return False
                        if json.loads(raw.splitlines()[0]) != {'version':1, 'event':'started'}:
                            raise ValueError('owned consumer startup rejected')
                    return True
                while not server.started or not started_consumers():
                    assert thread.is_alive() and nginx.poll() is None and all(w.poll() is None for w in workers)
                    assert time.monotonic() < deadline; time.sleep(.05)
                ready = {'service_pid':os.getpid(), 'worker_pid':workers[0].pid, 'ventilation_worker_pid':workers[1].pid,
                    'frontend':f'http://localhost:{args.web_port}/', 'backend':f'https://127.0.0.1:{args.api_port}',
                    'actual_SCRAM':True, 'automatic_consumers':2, 'test_checkpoint_pause':False,
                    'prefix_enabled':True, 'worker_chunk_budget':value['worker_chunk_budget'],
                    'expires_at':value['auth']['expires_at'], 'G0_G4':'not_assessed', 'real_farm_runs':0}
                save(run/'ready.private.json', ready)
                guide = ('URL: '+ready['frontend']+'#ventilation-execution\n내부 합성 계산 / 실제 농장 예측·추천 보류\n'
                    '접근 토큰(기존과 동일):\n'+access['token']+'\n계산 모델: 작물·기후·명시 환기 계산\n'
                    '새 계산 접수 파일: '+str(directory/'requests/normal-user.json')+'\n'
                    '계산 접수 → 자동 진행·확정 수치/UTC·3D → 저장 완료 결과\n'
                    '기존 공동 계산: 모델을 작물·기후 공동 계산으로 선택하고 기존 접수 파일/작업 ID 사용\n'
                    '유효 종료: '+value['auth']['expires_at']+'\n')
                save(run/'OPEN-UI-MIXED.private.txt', guide.encode(), raw=True)
                started = time.monotonic()
                while not stop.wait(.25):
                    assert thread.is_alive() and nginx.poll() is None and all(w.poll() is None for w in workers)
                    if time.monotonic()-started >= args.ttl_seconds-5 or datetime.now(timezone.utc) >= expires-timedelta(seconds=5): break
            finally:
                stopped = stop_owned_services(workers, nginx, server, thread, logs)
                common.dump(args, original, admin, 'after-'+args.run)
                save(run/'stopped.private.json', {**stopped, 'worker_exits':[w.returncode for w in workers],
                    'database_retained':True, 'artifacts_retained':True})
                if not stopped['service_stopped']: raise ValueError('owned preview cleanup incomplete')
        except BaseException:
            provision(admin, RuntimeLoginPolicy(**previous['policy']), enabled=False)
            raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'serve'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--original-directory', type=Path, required=True)
    parser.add_argument('--original-access', type=Path)
    parser.add_argument('--pg-bin', type=Path, required=True)
    parser.add_argument('--run', default='mixed-v1')
    parser.add_argument('--ttl-seconds', type=int, default=86400)
    parser.add_argument('--api-port', type=int, default=8446)
    parser.add_argument('--web-port', type=int, default=5174)
    parser.add_argument('--nginx', type=Path)
    parser.add_argument('--dist', type=Path)
    parser.add_argument('--status-file', type=Path)
    args = parser.parse_args()
    assert args.directory.is_absolute() and args.original_directory.is_absolute() and 60 <= args.ttl_seconds <= 86400
    prepare(args) if args.action == 'prepare' else serve(args)
