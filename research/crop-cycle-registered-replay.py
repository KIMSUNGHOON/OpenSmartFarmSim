"""Keep a completed owned farm DB alive through its real protected replay UI."""
from dataclasses import asdict
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import json
import http.client
import os
from pathlib import Path
import secrets
import select
import signal
import socket
import ssl
import subprocess
import sys
import threading
from time import monotonic,sleep
from types import SimpleNamespace

from app import api_crop_cycle_calculation_replay as public
from app import calculation_operator_config as loader
from app import crop_cycle_calculation_current_query as current
from app import crop_cycle_calculation_result_store as storage
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.crop_result_store import READ_SCOPES
from app.http_identity import BearerGrant,BearerRegistry,current_principal,token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_api_crop_cycle_calculation_tls import (Evidence,custody_fds,fd_inventory,
    CycleFarmBinding,CycleServerCustody,CycleCropResultStore)
from test_crop_cycle_artifact import PROFILES,NOTICE
from test_api_runtime import config,dependencies
from test_operator_config import store as store_config
from crop_cycle_registered_runtime_smoke import files,rewrite,save,counts
from web_crop_cycle_calculation_replay_smoke import HTTPObservation
from web_shell_smoke import WEB

VERSION='owned-same-registered-DB-replay-harness-v2'


@contextmanager
def production_frontend(origin,certificate,private_key,publisher,evidence_root):
    manifest_path=Path(os.environ['OSSF_REGISTERED_REPLAY_BUILD_MANIFEST'])
    manifest_raw=publisher.runtime.private_bytes(manifest_path)
    assert sha256(manifest_raw).hexdigest()==os.environ['OSSF_REGISTERED_REPLAY_BUILD_SHA256']
    manifest=json.loads(manifest_raw);directory=Path(manifest['directory'])
    before=files(directory)
    assert {name:item[0] for name,item in before.items()}==manifest['files']
    assert manifest['command']['exit_code']==0
    preparation_path=Path(os.environ['OSSF_REGISTERED_REPLAY_NGINX_PREPARATION'])
    preparation_raw=publisher.runtime.private_bytes(preparation_path)
    assert sha256(preparation_raw).hexdigest()==os.environ['OSSF_REGISTERED_REPLAY_NGINX_SHA256']
    preparation=json.loads(preparation_raw);binary=Path(preparation['binary'])
    assert preparation['nginx_version']=='1.30.5' and preparation['official_signature_valid']
    assert sha256(binary.read_bytes()).hexdigest()==preparation['binary_sha256']
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    frontend_root=Path(os.environ['TMPDIR'])/'registered-replay-nginx';frontend_root.mkdir(mode=0o700)
    (frontend_root/'logs').mkdir(mode=0o700)
    template=(WEB/'nginx.conf').read_text()
    replacements={'/tmp/nginx.pid':str(frontend_root/'nginx.pid'),
        '/etc/nginx/mime.types':str(binary.parents[1]/'conf/mime.types'),
        'listen 8444 ssl;':f'listen 127.0.0.1:{port} ssl;',
        '/run/operator/web/cert.pem':str(certificate),'/run/operator/web/key.pem':str(private_key),
        '/run/operator/web/api-ca.pem':str(certificate),'/usr/share/nginx/html':str(directory),
        'https://127.0.0.1:8443':origin}
    for name in ('client','proxy','fastcgi','uwsgi','scgi'):
        replacements['/tmp/'+name+'-temp']=str(frontend_root/(name+'-temp'))
    for source,target in replacements.items():
        assert source in template;template=template.replace(source,target)
    nginx_config=frontend_root/'nginx.conf';publisher.runtime.write_private(nginx_config,template.encode())
    env={name:os.environ[name] for name in ('PATH','HOME','LANG','TMPDIR') if name in os.environ}
    argv=[str(binary),'-p',str(frontend_root)+'/', '-c',str(nginx_config),'-g','daemon off;']
    log=evidence_root/'registered-replay-frontend.log';started=monotonic();receipt={}
    with log.open('xb') as output:
        os.fchmod(output.fileno(),0o600)
        child=subprocess.Popen(argv,cwd=WEB,env=env,stdout=output,stderr=subprocess.STDOUT)
        identity=publisher.supervisor.identity(child.pid)
        try:
            context=ssl.create_default_context(cafile=str(certificate));deadline=monotonic()+20
            while monotonic()<deadline and child.poll() is None:
                client=http.client.HTTPSConnection('127.0.0.1',port,timeout=1,context=context)
                try:
                    client.request('GET','/');response=client.getresponse();body=response.read()
                    if response.status==200:
                        assert body==(directory/'index.html').read_bytes();break
                except (OSError,http.client.HTTPException):sleep(.1)
                finally:client.close()
            else:raise AssertionError('owned production build frontend did not start')
            yield port,receipt
        finally:
            if child.poll() is None:
                assert publisher.supervisor.identity(child.pid)==identity;child.send_signal(signal.SIGQUIT)
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    assert publisher.supervisor.identity(child.pid)==identity;child.kill();child.wait(timeout=10)
            output.flush();os.fsync(output.fileno());log.chmod(0o400)
            receipt.update(argv=argv,worker=identity,actual_exit_code=child.returncode,
                wall_seconds=monotonic()-started,log_sha256=sha256(log.read_bytes()).hexdigest(),
                build_manifest_sha256=sha256(manifest_raw).hexdigest(),actual_built_index_verified=True,
                nginx_preparation_sha256=sha256(preparation_raw).hexdigest(),
                config_sha256=sha256(nginx_config.read_bytes()).hexdigest(),frontend='native-nginx-1.30.5')
            save('registered-replay-frontend-command.json',receipt)
    assert files(directory)==before


def replay(publisher,declaration,digest,published,*,expected,private_config,request,monkeypatch,tmp_path):
    runtime=publisher.runtime
    value,manifest,server,raw,key=publisher.load_declaration(declaration,digest)
    document=json.loads(runtime.private_bytes(manifest['config']))
    jobs=server.binding.jobs;farms=server.binding.farms;research=farms.replay.owned_research
    authority=server.binding.input_authority;rights=server.binding.input_rights
    selected_root=Path(server.directory);input_root=Path(document['input']['directory'])
    result_key=secrets.token_bytes(32)
    while result_key in (key,server.integrity_key):result_key=secrets.token_bytes(32)
    issuer=CalculationResultEvidenceAuthority(authority,integrity_key=result_key,
        issuer_id='owned-registered-replay-results',key_id='result-v1')
    input_proof=runtime.private_bytes(document['input']['evidence_file'])
    result_root=selected_root/runtime.custody._intent_id('tenant-1',json.loads(raw))/'artifact'
    result_proof=issuer.issue(result_root,published['progress']['artifact_sha256'],input_root,
        value['input_root_sha256'],input_proof)
    evidence=Evidence();evidence.values[published['result_id']]={'input_directory':input_root,
        'input_evidence_raw':input_proof,'result_evidence_raw':result_proof}
    store=storage.CalculationCycleCropResultStore(server,integrity_key=key)
    query=current.CalculationCurrentCycleQuery(store,issuer,evidence_resolver=evidence)
    farm=json.loads(raw)['farm'];prepared=query.read('tenant-1',published['result_id'],farm)
    assert prepared['record']['payload_sha256']==published['payload_sha256']
    summary=public.project_calculation_cycle_result(prepared['record'],prepared['terminal']).model_dump(mode='json')
    for kind,limit in (('samples',64),('events',8)):
        page=store.page('tenant-1',published['result_id'],farm,kind,0,limit)
        assert _canonical(page['records'])==_canonical(expected[kind][:len(page['records'])])
    assert summary['reference']['sample_count']>=len(expected['samples'])
    data={'summary':summary,'samples':expected['samples'][:14],
        'events':[{k:r[k] for k in ('at','before','after','removed')} for r in expected['events'][:8]]}
    os.close(jobs._content_directory(create=True))
    now=datetime.now(timezone.utc);tokens={name:secrets.token_urlsafe(40).encode() for name in ('owner','denied')}
    grants=tuple(BearerGrant(token_digest(tokens[name]),'tenant-1',frozenset(scopes),now-timedelta(seconds=1),
        now+timedelta(hours=1)) for name,scopes in (('owner',READ_SCOPES),('denied',READ_SCOPES[:-1])))
    def sources(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def crops(*,farm_authoring_service):
        bound=CalculationFarmBinding(farm_authoring_service,authority,input_rights=rights)
        selected=runtime.custody.CalculationServerCustody(bound,selected_root,
            input_resolver=runtime.Resolver(document['input'],document['resolver_version']),integrity_key=server.integrity_key)
        return storage.CalculationCycleCropResultStore(selected,integrity_key=key)
    def queries(*,result_store):return current.CalculationCurrentCycleQuery(result_store,issuer,evidence_resolver=evidence)
    legacy_root=tmp_path/'unused-legacy';legacy_root.mkdir(mode=0o700)
    class Unused:
        version='owned-replay-unused-legacy-v1'
        def __call__(self,*a,**k):raise AssertionError('verified replay used original calculation resolver')
    def legacy(*,farm_authoring_service):
        bound=CycleFarmBinding(farm_authoring_service,**PROFILES,notice_raw=NOTICE,input_rights=rights)
        return CycleCropResultStore(CycleServerCustody(bound,legacy_root,input_resolver=Unused(),
            integrity_key=server.integrity_key),integrity_key=key)
    certificate,private_key,_=request.getfixturevalue('tls_files')
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        thermal_gate_key=runtime.private_bytes(document['keys']['thermal']),
        market_hold_key=runtime.private_bytes(document['keys']['market']),certificate=certificate,private_key=private_key,port=0)
    deps=dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry(grants),owned_fixture_registry=research.registry,
        owned_research_contexts=dict(research._contexts),market_scope_resolver=farms.replay.thermal.holds._scope_resolver,
        market_source_factory=sources,crop_cycle_result_store_factory=legacy,
        crop_cycle_calculation_result_store_factory=crops,crop_cycle_calculation_current_query_factory=queries)
    path,doc=private_config
    doc.update(config_version=loader.VERSION,policy=asdict(cfg.policy),artifact_root=str(cfg.artifact_root),
        certificate=str(certificate),private_key=str(private_key),port=0)
    Path(doc['dsn_file']).write_text(cfg.dsn);Path(doc['thermal_gate_key_file']).write_bytes(cfg.thermal_gate_key)
    Path(doc['market_hold_key_file']).write_bytes(cfg.market_hold_key);store_config(path,doc)
    def factory(*,config):assert config==cfg;return deps
    monkeypatch.setitem(sys.modules,'trusted_operator',SimpleNamespace(dependencies=factory))
    def forbidden(*a,**k):raise AssertionError('replay GET calculated, issued or published crop output')
    engine=runtime.engine;custody=runtime.custody
    for module,name in ((engine.inputs,'open_input_packet'),(engine.legacy,'prepare_context'),(engine,'open_calculation_context'),
        (engine,'advance_chunk'),(engine.short._Evaluator,'rhs'),(storage.artifact,'open_artifact'),
        (storage.artifact._Files,'_load_prefix'),(storage.artifact,'_validate_delta'),(custody._Journal,'__init__'),
        (custody.CalculationServerCustody,'advance'),(storage.CalculationCycleCropResultStore,'put'),
        (engine.evidence.InputEvidenceAuthority,'issue'),(CalculationResultEvidenceAuthority,'issue')):
        monkeypatch.setattr(module,name,forbidden)
    selected=loader.load_calculation_api_runtime(path)
    assert selected.calculation_cycle_crop_results.jobs is selected.jobs
    assert selected.jobs._dsn==jobs._dsn and selected.jobs.schema==jobs.schema
    https=selected.service.server();observed=HTTPObservation(https.config.app);https.config.app=observed
    before=counts(server.binding);history=files(selected_root);inputs_before=files(input_root)
    config_before=files(Path(manifest['config']).parent);fds=fd_inventory()
    thread=threading.Thread(target=https.run,daemon=True);browser=None;thread.start()
    rights_path=Path(document['rights_file']);original_rights=runtime.private_bytes(rights_path)
    evidence_root=Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE']);log=evidence_root/'registered-replay-browser.log'
    report=None;browser_receipt=None;identity=None;argv=None;started=None;communicated=False
    try:
        deadline=monotonic()+15
        while not https.started:assert thread.is_alive() and monotonic()<deadline;sleep(.01)
        port=https.servers[0].sockets[0].getsockname()[1]
        with production_frontend(f'https://127.0.0.1:{port}',certificate,private_key,publisher,evidence_root) as (web_port,frontend_receipt):
            env={name:os.environ[name] for name in ('PATH','HOME','LANG','PLAYWRIGHT_BROWSERS_PATH','TMPDIR') if name in os.environ}
            argv=['node','--max-old-space-size=64','--max-semi-space-size=2',
                'e2e/registered-cycle-replay-smoke.mjs',f'https://127.0.0.1:{web_port}',str(evidence_root/'screens')]
            with log.open('xb') as errors:
                os.fchmod(errors.fileno(),0o600);started=monotonic()
                browser=subprocess.Popen(argv,cwd=WEB,env=env,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=errors,text=True)
                identity=publisher.supervisor.identity(browser.pid)
                def send(v):browser.stdin.write(json.dumps(v)+'\n');browser.stdin.flush()
                def receive(stage,timeout):
                    assert select.select([browser.stdout],[],[],timeout)[0],'owned replay browser deadline: '+stage
                    line=browser.stdout.readline();assert line,'owned replay browser ended: '+stage
                    v=json.loads(line);assert v['stage']==stage;return v
                send({'data':data,'tokens':{k:v.decode() for k,v in tokens.items()}})
                receive('geometry_verified',240);rewrite(rights_path,_canonical({'allowed':False}));send({'stage':'rights_revoked'})
                receive('rights_hold_verified',45);rewrite(rights_path,original_rights);send({'stage':'rights_restored'})
                report=receive('verified',120)
                assert not any(token.decode() in json.dumps(report) for token in tokens.values())
                browser.communicate(timeout=15);communicated=True;assert browser.returncode==0
                errors.flush();os.fsync(errors.fileno())
                browser_receipt={'argv':argv,'worker':identity,'actual_exit_code':browser.returncode,
                    'wall_seconds':monotonic()-started,'stderr_log_sha256':sha256(log.read_bytes()).hexdigest()}
            log.chmod(0o400)
            assert report['errors']==[] and report['peak_active_reads']==1 and report['unmounted']
            assert observed.peak==1 and observed.active==0 and len(observed.responses)==len(report['network'])
            assert all(r['complete'] and r['seconds']<30 and r['bytes']<=public.MAX_RESPONSE_BYTES for r in observed.responses)
            assert [r['status'] for r in observed.responses].count(422)==1 and [r['status'] for r in observed.responses].count(403)==1
            assert counts(server.binding)==before and current_principal() is None
            with jobs.connect() as conn:assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    finally:
        rewrite(rights_path,original_rights)
        if browser is not None:
            if browser.poll() is None:
                assert publisher.supervisor.identity(browser.pid)==identity
                browser.kill()
            if not communicated:browser.communicate(timeout=10)
            fd=os.open(log,os.O_RDONLY|os.O_NOFOLLOW)
            try:os.fsync(fd)
            finally:os.close(fd)
            log.chmod(0o400)
            browser_receipt={'argv':argv,'worker':identity,'actual_exit_code':browser.returncode,
                'wall_seconds':monotonic()-started,'stderr_log_sha256':sha256(log.read_bytes()).hexdigest()}
            save('registered-replay-browser-command.json',browser_receipt)
        https.should_exit=True;thread.join(15);assert not thread.is_alive()
    assert fd_inventory()==fds and custody_fds([selected_root,input_root])==0
    assert files(selected_root)==history and files(input_root)==inputs_before
    assert files(Path(manifest['config']).parent)==config_before and counts(server.binding)==before
    assert not Path('/proc',str(browser_receipt['worker']['pid'])).exists()
    assert server.input_resolver.last.reader.closed and not server.input_resolver.last._cache
    return {'version':VERSION,'scope':'owned_same_registered_DB_protected_replay_only','browser':report,
        'browser_command':browser_receipt,'actual_same_DB':True,'actual_SCRAM':True,'protected_loader':True,
        'frontend_command':frontend_receipt,'production_build_verified':True,
        'published_result_id':published['result_id'],'payload_sha256':published['payload_sha256'],
        'result_evidence_sha256':sha256(result_proof).hexdigest(),'read_RHS_calls':0,
        'HTTPS_responses':observed.responses,'server_peak_active_reads':observed.peak,
        'current_rights_and_account_denied':True,'custody_fds_after':0,'FD_inventory_preserved':True,
        'current_input_config_artifact_preserved':True,'HTTPS_joined':True,'frontend_stopped':True,
        'browser_and_Chromium_stopped':True,'first_two_sample_windows_only':True}
