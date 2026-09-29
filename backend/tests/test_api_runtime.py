"""All implemented HTTP stores share request identity and actual SCRAM authority."""

from dataclasses import FrozenInstanceError, asdict, replace
from datetime import datetime, timezone, timedelta
from pathlib import Path
from hashlib import sha256
import http.client
import json
import os
import signal
import socket
import ssl
import subprocess
import sys
import time
from uuid import uuid4

import pytest
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.api_runtime import ApiRuntimeConfig, ApiRuntimeDependencies, ApiRuntime
from app.http_identity import BearerRegistry, BearerGrant, current_principal, token_digest
from app.research_registry import ResearchRegistry
from app.runtime_roles import RuntimeLoginPolicy
from app.cli_contracts import _canonical
from test_research_registry import document
from test_market_signed_hold_integration import HOLD_KEY, context_verifier
from test_market_scenario import case
from app.content_access import ContentAccess
from app.job_store import JobStore
from login_database import login_database, login_scope
from test_api_serve import tls_files


TOKEN = b'synthetic-runtime-bearer-'+b'r'*32
SCOPES = frozenset({'location_create', 'metadata', 'artifact', 'auditor', 'thermal_run_read',
    'thermal_snapshot_read', 'decision_context_read', 'market_hold_read', 'market_hold_context_read',
    'market_candidate_read', 'market_result_read', 'break_even_read'})


def policy():
    return RuntimeLoginPolicy('project', 'project_owner', 'project_role', 'project_database',
        market_calculation=True, break_even_calculation=True)


def config(**changes):
    values = dict(policy=policy(), dsn='dbname=private_db user=private_user password=synthetic-secret',
        artifact_root=Path('/private/artifacts'), certificate=Path('/private/cert.pem'),
        private_key=Path('/private/key.pem'), thermal_gate_key=b'synthetic-gate-key-32-bytes-long!', market_hold_key=HOLD_KEY)
    values.update(changes)
    return ApiRuntimeConfig(**values)


def dependencies(source=None, **changes):
    raw = _canonical(document())
    now = datetime.now(timezone.utc)
    grant = BearerGrant(token_digest(TOKEN), 'tenant-1', SCOPES, now-timedelta(seconds=1), now+timedelta(hours=1))
    source = source or case()[0]
    values = dict(research_registry=ResearchRegistry(raw, sha256(raw).hexdigest()),
        bearer_registry=BearerRegistry((grant,)), context_verifier=context_verifier,
        release_verifier=lambda *_: None, market_scope_resolver=lambda *_: None,
        market_source_factory=lambda *, principal_provider: source)
    values.update(changes)
    return ApiRuntimeDependencies(**values)


@pytest.mark.parametrize('changes', [dict(policy=replace(policy(), break_even_calculation=False)),
    dict(dsn=''), dict(artifact_root=Path('relative')), dict(certificate=Path('relative')),
    dict(private_key=Path('/private/../key')), dict(thermal_gate_key=b'short'),
    dict(market_hold_key='private string'), dict(host='0.0.0.0'), dict(port=True),
    dict(content_access=object())])
def test_configuration_rejects_invalid_or_unbound_operating_values(changes):
    with pytest.raises(ValueError, match='^API runtime configuration rejected$'): config(**changes)


def test_config_hides_private_values_and_is_frozen():
    value = config()
    assert 'private' not in repr(value) and 'synthetic' not in repr(value)
    with pytest.raises(FrozenInstanceError): value.dsn = 'other'


@pytest.mark.parametrize('changes', [dict(research_registry=None), dict(bearer_registry=None),
    dict(context_verifier=None), dict(release_verifier=None), dict(market_scope_resolver=None),
    dict(market_source_factory=None), dict(thermal_publisher_factory=True), dict(owned_fixture_registry=object())])
def test_missing_dependencies_are_rejected(changes):
    with pytest.raises(ValueError, match='^API runtime dependencies rejected$'): dependencies(**changes)


def test_assembly_rejects_untyped_config_without_provider_calls():
    calls = []
    deps = dependencies(market_source_factory=lambda **_: calls.append('called'))
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'): ApiRuntime(object(), deps)
    assert calls == [] and current_principal() is None


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
@pytest.mark.parametrize('fault', ['identity', 'grant', 'root_mode', 'root_missing', 'root_symlink', 'source', 'source_exit', 'content_owner'])
def test_assembly_rejects_bad_identity_grants_artifacts_or_sources(login_scope, tls_files, tmp_path, fault):
    base, actual_policy, dsns = login_scope
    cert, key, _ = tls_files
    root = base.artifact_root
    root.mkdir(mode=0o700)
    if fault == 'root_mode': root.chmod(0o750)
    elif fault == 'root_missing': root.rmdir()
    elif fault == 'root_symlink':
        actual = tmp_path/'actual'; root.rename(actual); root.symlink_to(actual, target_is_directory=True)
    elif fault == 'grant':
        with base.connect() as conn:
            conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}').format(sql.Identifier(actual_policy.schema),
                sql.Identifier(actual_policy.roles['worker'])))
    calls = []
    def source_factory(*, principal_provider):
        calls.append(principal_provider)
        if fault == 'source_exit': raise SystemExit('synthetic private adapter details')
        return object() if fault == 'source' else case()[0]
    cfg = config(policy=actual_policy, dsn=dsns['request' if fault == 'identity' else 'authority'],
        artifact_root=root, certificate=cert, private_key=key,
        content_access=ContentAccess(os.geteuid()+1, os.getegid()) if fault == 'content_owner' else None)
    with pytest.raises(ValueError, match='^API runtime assembly rejected$'): ApiRuntime(cfg, dependencies(market_source_factory=source_factory))
    assert len(calls) == (1 if fault in {'source', 'source_exit'} else 0)
    assert current_principal() is None


@pytest.mark.parametrize('login_scope', [{'market_calculation': True, 'break_even_calculation': True}], indirect=True)
def test_real_foreground_cli_assembles_all_stores_and_reads_signed_economics(login_scope, tls_files, tmp_path):
    base, actual_policy, dsns = login_scope
    cert, key, _ = tls_files
    base.artifact_root.mkdir(mode=0o700)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    directory = tmp_path/'operator'
    directory.mkdir(mode=0o700)
    private = directory/'private.json'
    private.write_text(json.dumps({'policy': asdict(actual_policy), 'dsn': dsns['authority'],
        'artifacts': str(base.artifact_root), 'certificate': str(cert), 'private_key': str(key),
        'port': port, 'token': TOKEN.decode()})); private.chmod(0o600)
    (directory/'synthetic_runtime_factory.py').write_text('''from pathlib import Path
import json,os
from dataclasses import replace
from app.api_runtime import ApiRuntime
from app.http_identity import current_principal
from app.runtime_roles import RuntimeLoginPolicy
from app.market_scenario import MarketScenarioService
from app.market_result_store import MarketResultStore
from app.break_even_store import BreakEvenStore
from test_api_runtime import config,dependencies,SCOPES
from test_break_even import trial_plan
from test_market_signed_hold_integration import signed_market_assembly
from test_research_registry import document
from app.research_registry import ResearchRegistry
from app.cli_contracts import _canonical
from hashlib import sha256

def build():
    directory=Path(__file__).parent
    value=json.loads((directory/'private.json').read_text())
    policy=RuntimeLoginPolicy(**value['policy'])
    candidate_factory,source,market_request,principal,scope=signed_market_assembly(value['dsn'],policy.schema,runtime_identity=(policy,'authority'))
    candidate=MarketScenarioService(candidate_factory()).build_candidate(market_request,'tenant-1')
    result=MarketResultStore(value['dsn'],policy.schema,candidate_factory(),principal_provider=lambda:principal,runtime_identity=(policy,'authority')).pin_market_result(candidate.scenario_id,candidate.revision)
    _,request=trial_plan([20,26,32],candidate_repository_factory=lambda _:candidate_factory(),case_factory=lambda:(source,market_request))
    BreakEvenStore(value['dsn'],policy.schema,candidate_factory(),principal_provider=lambda:principal,runtime_identity=(policy,'authority')).pin_break_even_plan(request,source.break_even_plan)
    source.get_market_hold_report=lambda *_: (_ for _ in ()).throw(AssertionError('source must not supply hold authority'))
    source.get_decision_context=lambda *_: (_ for _ in ()).throw(AssertionError('source must not supply context authority'))
    facts=document();facts['registrations'][0]['tenant_id']='tenant-1'
    raw=_canonical(facts)
    def factory(*,principal_provider):
        assert principal_provider is current_principal and principal_provider() is None
        return source
    deps=dependencies(source,research_registry=ResearchRegistry(raw,sha256(raw).hexdigest()),market_scope_resolver=lambda *_:dict(scope),market_source_factory=factory)
    cfg=config(policy=policy,dsn=value['dsn'],artifact_root=Path(value['artifacts']),certificate=Path(value['certificate']),private_key=Path(value['private_key']),port=value['port'])
    runtime=ApiRuntime(cfg,deps)
    assert runtime.jobs.principal_provider is current_principal and runtime.jobs.audit_runtime_grants
    for store in (runtime.thermal,runtime.market_holds,runtime.market_candidates,runtime.market_results,runtime.break_even):
        assert store._principal_provider is current_principal and store.runtime_identity==(policy,'authority')
    assert not runtime.market_candidates.tenant_is_authenticated('tenant-1')
    assert runtime.jobs.allow_synthetic_invocation is False
    assert current_principal() is None
    boot=directory/'boot.json'
    fd=os.open(boot,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as stream:
        json.dump({'economic_id':result.economic_result.result_id,'hold_id':market_request['market_context']['hold_report_id'],'plan_id':request['plan_id'],'snapshot_id':scope['snapshot_id']},stream)
    return runtime.service
''')
    backend = Path(__file__).resolve().parents[1]
    environment = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'PYTHONPATH': os.pathsep.join(map(str, (backend, backend/'tests', directory)))}
    process = subprocess.Popen([sys.executable, '-m', 'app.api_serve', '--factory', 'synthetic_runtime_factory:build'],
        cwd=backend, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    context = ssl.create_default_context(cafile=str(cert))
    def call(path='/openapi.json', *, method='GET', body=None, authenticated=True):
        conn = http.client.HTTPSConnection('127.0.0.1', port, timeout=45, context=context)
        try:
            headers = {'Authorization': 'Bearer '+TOKEN.decode()} if authenticated else {}
            if body is not None: headers['Content-Type'] = 'application/json'
            conn.request(method, path, json.dumps(body) if body is not None else None, headers)
            response = conn.getresponse()
            return response.status, json.loads(response.read())
        finally: conn.close()
    try:
        deadline = time.monotonic()+120
        while True:
            assert process.poll() is None, 'synthetic full API child exited early'
            if (directory/'boot.json').exists():
                try: response = call(authenticated=False); break
                except OSError: pass
            assert time.monotonic()<deadline, 'synthetic full API child not ready'
            time.sleep(0.05)
        assert response[0] == 401
        boot = json.loads((directory/'boot.json').read_text())
        assert call()[1] == json.loads((backend.parent/'contracts/openapi-v1.json').read_bytes())
        from test_api_location_research import BODY
        accepted = call('/v1/locations', method='POST', body=BODY)
        assert accepted[0] == 202
        assert call('/v1/jobs/'+accepted[1]['research_job']['job_id'])[1] == accepted[1]['research_job']
        assert call('/v1/jobs/'+accepted[1]['research_job']['job_id']+'/hold-report')[0] == 404
        assert call('/v1/market-hold-reports/'+boot['hold_id'])[1]['status'] == 'hold'
        money = call('/v1/economic-results/'+boot['economic_id'])
        assert money[0] == 200 and money[1]['assessment_status'] == 'hold' and money[1]['evidence_level'] == 'assumed'
        assert type(money[1]['amounts']['management_operating_income_krw']) is str
        grid = call('/v1/break-even-results?plan_id='+boot['plan_id'])
        assert grid[0] == 200 and grid[1]['zero_values'] == ['26'] and grid[1]['assessment_status'] == 'hold'
        path='/v1/runs/synthetic-thermal-v1:'+'0'*64
        for suffix in ('', '/series', '/manifest'): assert call(path+suffix)[0] == 404
        with base.connect() as conn:
            conn.execute(sql.SQL('GRANT SELECT ON {}.jobs TO {}').format(sql.Identifier(actual_policy.schema), sql.Identifier(actual_policy.roles['worker'])))
        assert call('/v1/jobs/'+accepted[1]['research_job']['job_id'])[0] == 503
    finally:
        process.terminate()
        try: stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired: process.kill(); stdout, stderr = process.communicate(timeout=5)
    assert process.returncode == -signal.SIGTERM and stdout == b'' and TOKEN not in stderr
    assert b'private.json' not in stderr and b'passfile' not in stderr


@pytest.mark.parametrize('flag', [None, 1, 'true', True])
def test_job_grant_audit_flag_rejects_nonboolean_or_unbound_configuration(tmp_path, flag):
    with pytest.raises(ValueError, match='^runtime grant audit requires explicit login binding$'):
        JobStore(None, 'schema', tmp_path/'artifacts', audit_runtime_grants=flag)
