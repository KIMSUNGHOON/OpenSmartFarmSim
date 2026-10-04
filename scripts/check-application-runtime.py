"""Hosted Compose/SCRAM proof using existing self-authored software fixtures."""

import argparse
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import runpy
import secrets
import shutil
import ssl
import sys
import tempfile
import time
from types import SimpleNamespace
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'backend'), str(ROOT / 'backend/tests')]

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo
from login_database import login_database, login_scope
from test_api_economic_scenario import economic_api
from test_economic_calculation_worker import calculation_setup
from test_market_hold_store import CONTEXT_KEY, HOLD_KEY
from test_research_registry import document as research_document

IMAGE_TOOLS = runpy.run_path(str(ROOT / 'scripts/check-application-images.py'))
command, event = IMAGE_TOOLS['command'], IMAGE_TOOLS['event']


# Installed only inside private disposable operator mounts, never in the images.
PLUGIN = '''from datetime import datetime
from hashlib import sha256
import hmac, json
from pathlib import Path
from app.operator_config import _private_bytes
from app.api_runtime import ApiRuntimeDependencies
from app.cli_contracts import _canonical
from app.http_identity import BearerRegistry, BearerGrant, current_principal, token_digest
from app.research_registry import ResearchRegistry
from app.owned_fixture_registry import OwnedFixtureRegistry
from app.runtime_roles import RuntimeLoginPolicy
from app.job_store import JobStore
from app.thermal_run_store import ThermalRunStore
from app.market_hold_store import MarketHoldStore
from app.market_source_store import MarketSourceStore
from app.market_candidate_store import MarketCandidateStore
from app.market_result_store import MarketResultStore
from app.api_market_source import _MarketSources
from app.economic_calculation_worker import EconomicCalculationWorker
from app.deterministic_work import DeterministicWorkerLoop

def data():
    root = Path(__file__).resolve().parent.parent
    return json.loads(_private_bytes(root/'fixture.json', maximum=65536)), root

def verify(raw, signature):
    value, root = data()
    key = _private_bytes(root/'context.key', minimum=32, maximum=4096)
    if not hmac.compare_digest(signature, hmac.new(key, b'decision-context-v1\\0'+raw, sha256).hexdigest()):
        return None
    context = json.loads(raw)
    return {name: context[name] for name in ('authority_id','planning_event_sha256',
                                          'decision_at_utc','decision_time_kind')}

def dependencies_factory(*, config):
    value, root = data()
    raw = _canonical(value['research_registry'])
    token = _private_bytes(root/'bearer', maximum=4096).decode()
    grant = BearerGrant(token_digest(token.encode()), 'tenant-1', frozenset(value['scopes']),
        datetime.fromisoformat(value['not_before']), datetime.fromisoformat(value['expires_at']))
    return ApiRuntimeDependencies(research_registry=ResearchRegistry(raw, sha256(raw).hexdigest()),
        owned_fixture_registry=OwnedFixtureRegistry('/app') if value['collection_enabled'] else None,
        bearer_registry=BearerRegistry((grant,)), context_verifier=verify,
        release_verifier=lambda *_: None,
        market_scope_resolver=lambda *_: dict(value['hold_scope']),
        market_source_factory=lambda *, principal_provider: MarketSourceStore(config.dsn,
            config.policy.schema, runtime_identity=(config.policy,'authority'),
            principal_provider=principal_provider))

def build():
    value, root = data()
    policy = RuntimeLoginPolicy(**value['policy'])
    dsn = _private_bytes(root/'authority.dsn', maximum=8192).decode().strip()
    principal = {'authenticated':True,'tenant_id':'tenant-1','scopes':frozenset(value['scopes'])}
    provider = lambda: principal
    binding = (policy,'authority')
    jobs = JobStore(dsn, policy.schema, Path('/artifacts'), runtime_identity=binding,
        audit_runtime_grants=True, principal_provider=provider)
    contexts = ThermalRunStore(dsn,policy.schema,
        gate_key=_private_bytes(root/'thermal.key',minimum=32,maximum=4096),
        release_verifier=lambda *_:None,context_verifier=verify,
        runtime_identity=binding,principal_provider=provider)
    holds = MarketHoldStore(dsn,policy.schema,context_store=contexts,
        scope_resolver=lambda *_:dict(value['hold_scope']),
        signing_key=_private_bytes(root/'market.key',minimum=32,maximum=4096),
        runtime_identity=binding,principal_provider=provider)
    sources = MarketSourceStore(dsn,policy.schema,runtime_identity=binding,principal_provider=provider)
    candidates = MarketCandidateStore(dsn,policy.schema,_MarketSources(sources,holds,principal_provider=provider),
        runtime_identity=binding,principal_provider=provider)
    results = MarketResultStore(dsn,policy.schema,candidates,
        runtime_identity=binding,principal_provider=provider)
    worker = EconomicCalculationWorker(jobs,results,tenant_id='tenant-1')
    return DeterministicWorkerLoop(worker,input_versions=frozenset({'economic-calculation-input-v1'}))
'''


def private(path, value):
    path.write_bytes(value if type(value) is bytes else value.encode())
    path.chmod(0o600)


def operator_files(root, policy, dsns, worker, principal, certificates, token, *, collection=False):
    scopes = sorted(principal['scopes'] | {'auditor', 'market_hold_read'})
    catalog = research_document()
    catalog['registrations'][0]['tenant_id'] = 'tenant-1'
    now = datetime.now(timezone.utc)
    value = {'policy': asdict(policy), 'hold_scope': worker.results._candidates._source._holds._scope_resolver(),
        'scopes': scopes, 'research_registry': catalog, 'collection_enabled': collection,
        'not_before': (now - timedelta(seconds=1)).isoformat(),
        'expires_at': (now + timedelta(hours=1)).isoformat()}
    authority = conninfo_to_dict(dsns['authority'])
    for service in ('api', 'simulation'):
        directory = root / service
        directory.mkdir(mode=0o700)
        plugins = directory / 'plugins'
        plugins.mkdir(mode=0o700)
        private(plugins / 'synthetic_operator.py', PLUGIN)
        private(directory / 'fixture.json', json.dumps(value))
        private(directory / 'thermal.key', b'synthetic-gate-key-32-bytes-long!')
        private(directory / 'market.key', HOLD_KEY)
        private(directory / 'context.key', CONTEXT_KEY)
        password = Path(authority['passfile']).read_text().strip().rsplit(':', 1)[1]
        private(directory / 'authority.pgpass', f'db:5432:{policy.database}:{policy.roles["authority"]}:{password}\n')
        private(directory / 'authority.dsn', make_conninfo(host='db', port=5432,
            dbname=policy.database, user=policy.roles['authority'],
            passfile=f'/run/operator/{service}/authority.pgpass', sslmode='disable'))
        if service == 'api':
            private(directory / 'bearer', token)
            for source, target in [('api.pem', 'cert.pem'), ('api.key', 'key.pem'), ('ca.pem', 'api-ca.pem')]:
                private(directory / target, (certificates / source).read_bytes())
            config = {'config_version': 'operator-api-config-v1', 'policy': asdict(policy),
                'dsn_file': '/run/operator/api/authority.dsn', 'artifact_root': '/artifacts',
                'certificate': '/run/operator/api/cert.pem', 'private_key': '/run/operator/api/key.pem',
                'thermal_gate_key_file': '/run/operator/api/thermal.key',
                'market_hold_key_file': '/run/operator/api/market.key',
                'authored_run_gate_key_file': None, 'content_access': None,
                'host': '127.0.0.1', 'port': 8443,
                'dependencies_factory': 'synthetic_operator:dependencies_factory'}
            private(directory / 'operator.json', json.dumps(config))
        command('sudo', 'chown', '-R', '11001:11010', str(directory))
    IMAGE_TOOLS['private_directory'](root / 'web', 11002,
        [(certificates / 'web.pem', 'cert.pem'), (certificates / 'web.key', 'key.pem'),
         (certificates / 'ca.pem', 'api-ca.pem')])


def main(*, collection=False):
    os.chdir(ROOT)
    prefix = 'ossf-app-' + uuid4().hex[:12]
    root = Path(tempfile.mkdtemp(prefix=prefix + '-'))
    images, fixtures = {}, []
    compose = ['docker', 'compose', '--project-name', prefix, '-f', str(ROOT / 'compose.yaml'),
        '-f', str(ROOT / 'compose.application.yaml')]
    if collection:
        compose.extend(['-f', str(ROOT / 'compose.collection.yaml')])
    compose.extend(['-f', str(root / 'ci.json'), '--profile', 'runtime'])
    services = ('api', 'web', 'simulation', 'collector') if collection else ('api', 'web', 'simulation')
    collection_tools = None
    previous = {key: os.environ.get(key) for key in ('OSSF_TEST_PG_DSN', 'DB_ADMIN_PASSWORD_FILE',
        'DB_APP_PASSWORD_FILE', 'OSSF_API_PRIVATE_DIR', 'OSSF_SIMULATION_PRIVATE_DIR',
        'OSSF_WEB_PRIVATE_DIR', 'OSSF_ARTIFACT_DIR', 'OSSF_SIMULATION_FACTORY',
        'OSSF_WEB_PORT', 'OSSF_BACKEND_IMAGE', 'OSSF_WEB_IMAGE',
        'OSSF_COLLECTION_PRIVATE_DIR', 'OSSF_COLLECTION_FACTORY')}
    try:
        if collection:
            collection_tools=runpy.run_path(str(ROOT/'scripts/application-collection-fixture.py'))
        IMAGE_TOOLS['image_checks'](root, prefix, images)
        certs = root / 'certificates'
        certs.mkdir(mode=0o700)
        IMAGE_TOOLS['certificates'](certs)
        admin_password = secrets.token_hex(32)
        private(root / 'admin', admin_password)
        private(root / 'unused-app', secrets.token_hex(32))
        command('sudo', 'chown', '999:999', str(root / 'admin'))
        (root / 'ci.json').write_text(json.dumps({'services': {'db': {'ports': ['127.0.0.1::5432']}}}))
        os.environ.update({'DB_ADMIN_PASSWORD_FILE': str(root / 'admin'),
            'DB_APP_PASSWORD_FILE': str(root / 'unused-app'),
            'OSSF_API_PRIVATE_DIR': str(root / 'api'), 'OSSF_SIMULATION_PRIVATE_DIR': str(root / 'simulation'),
            'OSSF_WEB_PRIVATE_DIR': str(root / 'web'), 'OSSF_ARTIFACT_DIR': str(root / 'artifacts'),
            'OSSF_SIMULATION_FACTORY': 'synthetic_operator:build', 'OSSF_WEB_PORT': '0',
            'OSSF_BACKEND_IMAGE': images['backend'], 'OSSF_WEB_IMAGE': images['web']})
        if collection:
            os.environ.update({'OSSF_COLLECTION_PRIVATE_DIR':str(root/'collection'),
                               'OSSF_COLLECTION_FACTORY':'synthetic_collection:build'})
        command(*compose, 'config', '--quiet')
        model = json.loads(command(*compose, 'config', '--format', 'json').stdout)
        for service in services:
            assert model['services'][service]['tmpfs'] == ['/tmp:rw,noexec,nosuid,size=32m,mode=1777']
        command(*compose, 'up', '--no-deps', '--wait', '--wait-timeout', '120', 'db')
        db_port = command(*compose, 'port', 'db', '5432').stdout.strip().rsplit(':', 1)[1]
        private(root / 'admin.pgpass', f'127.0.0.1:{db_port}:opensmartfarmsim:opensmartfarmsim_admin:{admin_password}\n')
        os.environ['OSSF_TEST_PG_DSN'] = make_conninfo(host='127.0.0.1', port=db_port,
            dbname='opensmartfarmsim', user='opensmartfarmsim_admin', passfile=str(root / 'admin.pgpass'))
        database_fixture = login_database.__wrapped__()
        database = next(database_fixture)
        fixtures.append(database_fixture)
        scope_fixture = login_scope.__wrapped__(database, root,
            SimpleNamespace(param={'market_calculation': True, 'break_even_calculation': True,
                                   'market_source_storage': True}))
        scope = next(scope_fixture)
        fixtures.append(scope_fixture)
        base, policy, dsns = scope
        worker, jobs, results, unused_job, data, principal = calculation_setup.__wrapped__(economic_api.__wrapped__(scope))
        # Leave a canceled neighbor; the consumer must not execute it as the new HTTP job.
        assert jobs.cancel('tenant-1', unused_job['job_id'])
        ingestion = (collection_tools['prepare'](root,scope,principal,private=private,command=command)
                     if collection else None)
        token = 'synthetic-' + secrets.token_hex(32)
        operator_files(root, policy, dsns, worker, principal, certs, token, collection=collection)
        command('sudo', 'chown', '-R', '11001:11010', str(root / 'artifacts'))
        startup = command(*compose, 'up', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '120',
                          *services, check=False)
        if startup.returncode:
            for service in services:
                identity = command(*compose, 'ps', '--all', '--quiet', service).stdout.strip()
                if identity:
                    state = json.loads(command('docker', 'inspect', '--format', '{{json .State}}', identity).stdout)
                    event('startup_state', service=service, status=state['Status'], exit_code=state['ExitCode'],
                          health_status=state.get('Health', {}).get('Status'))
            diagnostic = '''import json, sys
records=[]
def trace(frame,event,arg):
    if event=='exception' and (frame.f_code.co_filename.startswith('/app/backend/app/') or
                             frame.f_code.co_filename.startswith('/run/operator/api/plugins/')):
        records.append({'file':frame.f_code.co_filename.rsplit('/',1)[-1],
                        'line':frame.f_lineno,'exception':arg[0].__name__})
    return trace
sys.settrace(trace)
try:
    from app.operator_config import api_service
    api_service()
except BaseException:
    pass
finally:
    sys.settrace(None)
print(json.dumps(records[-30:]))
'''
            diagnostic_result = command(*compose, 'run', '--rm', '--no-deps', '--entrypoint', 'python',
                                        'api', '-c', diagnostic, check=False)
            if diagnostic_result.returncode == 0:
                event('private_assembly_exception_locations', locations=json.loads(diagnostic_result.stdout))
            raise RuntimeError('application_compose_startup_failed')
        port = int(command(*compose, 'port', 'api', '8444').stdout.strip().rsplit(':', 1)[1])
        ca = ssl.create_default_context(cafile=str(certs / 'ca.pem'))
        def call(path, body=None, *, authenticated=True):
            connection = http.client.HTTPSConnection('127.0.0.1', port, timeout=30, context=ca)
            try:
                headers = {'Authorization': 'Bearer ' + token} if authenticated else {}
                if body is not None:
                    headers['Content-Type'] = 'application/json'
                connection.request('POST' if body is not None else 'GET', path,
                                   None if body is None else json.dumps(body), headers)
                response = connection.getresponse()
                raw = response.read()
                return response.status, json.loads(raw)
            finally:
                connection.close()
        def web_ready():
            deadline = time.monotonic() + 30
            while True:
                try:
                    assert call('/openapi.json', authenticated=False)[0] == 401
                    return
                except (ConnectionRefusedError, ConnectionResetError, http.client.RemoteDisconnected):
                    assert time.monotonic() < deadline, 'web_tls_readiness_timeout'
                    time.sleep(0.25)
        web_ready()
        assert call('/openapi.json', authenticated=False)[0] == 401
        assert call('/openapi.json')[1] == json.loads((ROOT / 'contracts/openapi-v1.json').read_bytes())
        body = data | {'idempotency_key': 'compose-economic-intake'}
        status, accepted = call('/v1/economic-results', body)
        assert status == 202
        route = '/v1/jobs/' + accepted['job_id']
        deadline = time.monotonic() + 180
        while True:
            status, job = call(route)
            assert status == 200 and job['state'] not in ('failed', 'hold', 'canceled')
            if job['state'] == 'succeeded':
                break
            assert time.monotonic() < deadline, 'automatic_completion_timeout'
            time.sleep(0.5)
        result_route = route + '/economic-result'
        status, first_result = call(result_route)
        assert status == 200 and first_result['assessment_status'] == 'hold'
        assert first_result['input_origin'] == 'user' and first_result['evidence_level'] == 'assumed'
        assert call('/v1/economic-results', body)[1]['job_id'] == accepted['job_id']
        if collection:
            status,collected=call('/v1/ingestions',ingestion)
            assert status==202 and collected['stage']=='collection'
            collection_route='/v1/jobs/'+collected['job_id']
            deadline=time.monotonic()+120
            while True:
                status,current=call(collection_route)
                assert status==200 and current['state'] not in ('failed','hold','canceled')
                if current['state']=='succeeded': break
                assert time.monotonic()<deadline,'automatic_collection_timeout'
                time.sleep(0.5)
            collection_record=collection_tools['inspect_record'](compose,collected['job_id'],command=command)
            assert call('/v1/ingestions',ingestion)[1]['job_id']==collected['job_id']
            assert current['attempt_count']==1
            event('automatic_owned_collection',assessment='hold',source_count=3,scope='software_fixture_only')
        for service in services:
            identity = command(*compose, 'ps', '--quiet', service).stdout.strip()
            info = json.loads(command('docker', 'inspect', identity).stdout)[0]
            expected_user = '11002:11002' if service == 'web' else '11001:11010'
            assert info['Config']['User'] == expected_user
            assert info['HostConfig']['ReadonlyRootfs'] and 'ALL' in info['HostConfig']['CapDrop']
            assert info['HostConfig']['PidsLimit'] == 64 and info['HostConfig']['Memory'] > 0
            assert info['HostConfig']['NanoCpus'] > 0
            mounts = {item['Destination']: item for item in info['Mounts']}
            private_mount = mounts[f'/run/operator/{service}']
            assert not private_mount['RW']
            if service == 'web':
                assert '/artifacts' not in mounts and '/run/operator/api' not in mounts
            if service == 'collector':
                assert '/run/operator/api' not in mounts and '/run/operator/simulation' not in mounts
                assert mounts['/artifacts']['RW'] and info['HostConfig']['Memory']==256*1024*1024
                assert info['HostConfig']['NanoCpus']==500000000
            event('actual_compose_process', service=service, uid=info['Config']['User'],
                  readonly=True, memory_bytes=info['HostConfig']['Memory'],
                  nano_cpus=info['HostConfig']['NanoCpus'])
        event('tls_scram_automatic_economic_completion', assessment='hold', scope='software_fixture_only')
        command(*compose, 'stop', *reversed(services))
        command(*compose, 'up', '--no-build', '--pull', 'never', '--wait', '--wait-timeout', '120',
                *services)
        port = int(command(*compose, 'port', 'api', '8444').stdout.strip().rsplit(':', 1)[1])
        web_ready()
        assert call(result_route) == (200, first_result)
        event('restart_current_completed_result', unchanged=True)
        if collection:
            assert call(collection_route)==(200,current)
            assert collection_tools['inspect_record'](compose,collected['job_id'],command=command)==collection_record
            collection_tools['withdraw_parent'](compose,ingestion['research_job_id'],command=command)
            assert call('/v1/ingestions',ingestion | {'idempotency_key':'revoked-parent'})[0]==422
            event('collection_restart_and_parent_withdrawal',unchanged=True,status=422)
        with base.connect() as connection:
            connection.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}').format(
                sql.Identifier(policy.schema), sql.Identifier(policy.roles['worker'])))
        assert call(result_route)[0] == 503
        event('current_grant_drift_refused', status=503)
        if collection:
            deadline=time.monotonic()+15
            while True:
                identity=command(*compose,'ps','--all','--quiet','collector').stdout.strip()
                state=json.loads(command('docker','inspect','--format','{{json .State}}',identity).stdout)
                if state['Status']=='exited': break
                assert time.monotonic()<deadline,'collector_grant_refusal_timeout'
                time.sleep(0.25)
            assert state['ExitCode']==3
            logs=command(*compose,'logs','--no-log-prefix','collector')
            raw=logs.stdout+logs.stderr
            assert len(raw)<65536
            events=[json.loads(line) for line in raw.splitlines() if line.startswith('{')]
            assert {'version':1,'ok':False,'code':'collection_consumer_execution_unresolved'} in events
            event('collector_current_grant_refused',exit_code=3)
    finally:
        cleanup_ok = True
        if (root / 'ci.json').exists():
            cleanup_ok &= command(*compose, 'stop', *reversed(services), check=False).returncode == 0
        # Services are stopped before fixture role/schema removal.
        for fixture in reversed(fixtures):
            try:
                next(fixture)
            except StopIteration:
                pass
            except Exception:
                cleanup_ok = False
        if (root / 'ci.json').exists():
            cleanup_ok &= command(*compose, 'down', '--volumes', '--remove-orphans', check=False).returncode == 0
            cleanup_ok &= not command('docker', 'ps', '--all', '--quiet', '--filter',
                f'label=com.docker.compose.project={prefix}').stdout.strip()
            cleanup_ok &= not command('docker', 'volume', 'ls', '--quiet', '--filter',
                f'label=com.docker.compose.project={prefix}').stdout.strip()
        for image in images.values():
            if command('docker', 'image', 'inspect', image, check=False).returncode == 0:
                cleanup_ok &= command('docker', 'image', 'rm', image, check=False).returncode == 0
        command('sudo', 'chown', '-R', f'{os.getuid()}:{os.getgid()}', str(root))
        shutil.rmtree(root)
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        assert cleanup_ok and not root.exists(), 'application_runtime_cleanup_failed'
        event('compose_cleanup', processes_volumes_credentials_removed=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Verify actual application Compose with synthetic inputs.')
    parser.add_argument('--collection',action='store_true')
    main(collection=parser.parse_args().collection)
