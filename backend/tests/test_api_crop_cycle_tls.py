"""Real owned SCRAM/TLS short-cycle custody; software proof, no crop validation."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta,timezone
import http.client
import json
import os
from pathlib import Path
import ssl
import stat
import threading
import time
from urllib.parse import urlencode

from psycopg import sql
import pytest

from app import api_crop_cycle_replay as public
from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.api_runtime import ApiRuntime
from app.http_identity import BearerGrant,BearerRegistry,current_principal,token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_crop_cycle_server_custody_farms import server_setup,OwnInputResolver,KEY,BUDGET
from test_crop_cycle_result_store_farms import DB_KEY
from test_crop_cycle_artifact import PROFILES,NOTICE
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database,login_scope
from test_api_runtime import config,dependencies
from test_api_serve import tls_files
from test_market_hold_store import context_verifier

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


class OwnInputs:
    version=OwnInputResolver.version
    def __init__(self,paths):self.paths=dict(paths)
    def __call__(self,root,**profiles):return inputs.open_input_packet(self.paths[root],root,**profiles)


def custody_fds(paths):
    count=0
    for fd in Path('/proc/self/fd').iterdir():
        try:target=os.readlink(fd)
        except FileNotFoundError:continue
        count+=any(target==str(p) or target.startswith(str(p)+'/') for p in paths)
    return count


def test_real_runtime_tls_scram_original_pages_hold_restart_withdrawal_tamper_and_cleanup(server_setup,tls_files,login_scope,tmp_path,monkeypatch):
    initial,raw,rights,_,expected=server_setup;body=json.loads(raw)
    held=shifted('empty-entry');held['initial_state']['values']['temperature_sum']['value']=0
    anchors=held.pop('output_times');hold_path=tmp_path/'hold-input'
    hold_packet=inputs.write_input_packet(hold_path,**held,anchors=anchors,outputs=anchors,**PROFILES,program_id='own-held-cycle')
    hold_body=deepcopy(body);hold_body['study_id']='own-held-cycle-study'
    hold_body['input'].update(root_sha256=hold_packet['root_sha256'],program_id='own-held-cycle')
    hold_body['rights']['input_root_sha256']=hold_packet['root_sha256'];hold_raw=_canonical(hold_body)
    resolver=OwnInputs({initial.input_resolver.root:initial.input_resolver.directory,hold_packet['root_sha256']:hold_path})
    server=custody.CycleServerCustody(initial.binding,initial.directory,input_resolver=resolver,integrity_key=KEY)
    assert json.loads(server.advance('tenant-1',raw,budget=BUDGET))['status']=='completed'
    assert json.loads(server.advance('tenant-1',hold_raw,budget=BUDGET))['status']=='hold'
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY)
    record=store.put('tenant-1',raw);hold_record=store.put('tenant-1',hold_raw)
    terminal=store.summary('tenant-1',record['result_id'],body['farm'])
    held_terminal=store.summary('tenant-1',hold_record['result_id'],body['farm'])
    assert held_terminal['last_confirmed'] is None
    cert,key,_=tls_files;jobs=store.jobs;replay=server.binding.farms.replay;research=replay.owned_research
    now=datetime.now(timezone.utc)
    subjects=[('owner','tenant-1',set(public.READ_SCOPES)),('foreign','foreign',set(public.READ_SCOPES)),
        ('denied','tenant-1',set(public.READ_SCOPES)-{'crop_result_read'})]
    tokens={name:('own-cycle-tls-'+name+'-'+'c'*32).encode() for name,_,_ in subjects}
    grants=tuple(BearerGrant(token_digest(tokens[name]),tenant,frozenset(scopes),now-timedelta(seconds=1),
        now+timedelta(hours=1)) for name,tenant,scopes in subjects)
    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def crop_factory(*,farm_authoring_service):
        binding=CycleFarmBinding(farm_authoring_service,**PROFILES,notice_raw=NOTICE,input_rights=rights)
        owned=custody.CycleServerCustody(binding,server.directory,input_resolver=resolver,integrity_key=KEY)
        return storage.CycleCropResultStore(owned,integrity_key=DB_KEY)
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,
        certificate=cert,private_key=key,port=0)
    deps=dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry(grants),
        owned_fixture_registry=research.registry,owned_research_contexts=dict(research._contexts),
        context_verifier=context_verifier,market_scope_resolver=replay.thermal.holds._scope_resolver,
        market_source_factory=source_factory,crop_cycle_result_store_factory=crop_factory)
    descriptor=jobs._content_directory(create=True);os.close(descriptor)
    runtime=ApiRuntime(cfg,deps)
    assert runtime.cycle_crop_results.jobs is runtime.jobs
    assert runtime.cycle_crop_results.server.binding.farms is runtime.farm_authoring
    for bad in (None,lambda **_:store,lambda **_:object()):
        with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
            ApiRuntime(cfg,replace(deps,crop_cycle_result_store_factory=bad))
    def forbidden(*a,**kw):pytest.fail('HTTPS executed crop math')
    monkeypatch.setattr(engine,'advance_chunk',forbidden);monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)
    trust=ssl.create_default_context(cafile=str(cert));observed=[];joined=0
    paths=[server.directory,*resolver.paths.values()]
    def target(which=record,view='summary',**pages):
        return '/v1/crop-cycle-research-results/'+which['result_id']+'?'+urlencode({**body['farm'],'view':view,**pages})
    for restart in range(2):
        if restart:runtime=ApiRuntime(cfg,deps)
        https=runtime.service.server();thread=threading.Thread(target=https.run,daemon=True);thread.start()
        try:
            deadline=time.monotonic()+15
            while not https.started:
                assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
            port=https.servers[0].sockets[0].getsockname()[1]
            def call(where=None,bearer='owner'):
                connection=http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=trust)
                try:
                    tick=time.monotonic();headers={} if bearer is None else {'Authorization':'Bearer '+tokens[bearer].decode()}
                    connection.request('GET',where or target(),headers=headers);response=connection.getresponse();full=response.read()
                    seconds=time.monotonic()-tick;value=json.loads(full)
                    assert seconds<30 and len(full)<=public.MAX_RESPONSE_BYTES and response.getheader('cache-control')=='no-store'
                    observed.append({'status':response.status,'seconds':seconds,'bytes':len(full),'value':value})
                    assert custody_fds(paths)==0
                    return response.status,value
                finally:connection.close()
            status,value=call();assert status==200 and value['result_id']==record['result_id']
            assert _canonical(value['summary']['manifest'])==_canonical(terminal['manifest'])
            if not restart:
                assert call(bearer=None)[0]==401 and call(bearer='denied')[0]==403 and call(bearer='foreign')[0]==404
                for kind,limit in (('samples',2),('events',1)):
                    rows=[];offset=0
                    while True:
                        status,value=call(target(view=kind,offset=offset,limit=limit));assert status==200
                        page=value['page'];rows.extend(page['records'])
                        if page['next_offset'] is None:break
                        offset=page['next_offset']
                    source=expected[kind]
                    if kind=='events':source=[{k:e[k] for k in ('at','before','after','removed')} for e in source]
                    assert _canonical(rows)==_canonical(source)
                    assert call(target(view=kind,offset=len(rows),limit=limit))[1]['page']['records']==[]
                status,value=call(target(hold_record));assert status==200 and value['summary']['hold']['last_confirmed'] is None
                assert value['summary']['hold']['at']==held_terminal['hold']['at']
                for kind in ('samples','events'):assert call(target(hold_record,kind))[1]['page']['records']==[]
                rights.allowed=False
                try:assert call()[0]==422
                finally:rights.allowed=True
                with monkeypatch.context() as patch:
                    patch.setattr(runtime.farm_scenarios.candidates._source._source,'get_input_rights',lambda *_:None)
                    assert call()[0]==422
                with monkeypatch.context() as patch:
                    original_bytes=public._public_bytes
                    def withdraw(value):
                        result=original_bytes(value);rights.allowed=False;return result
                    patch.setattr(public,'_public_bytes',withdraw)
                    try:assert call()[0]==422
                    finally:rights.allowed=True
                owner,policy,_=login_scope;table=jobs._table(storage.schema.TABLE);worker=sql.Identifier(policy.roles['worker'])
                with owner.connect() as conn:conn.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(table,worker))
                try:
                    status,value=call()
                    assert status==503 and value['error']['code']=='crop_research_unavailable'
                finally:
                    with owner.connect() as conn:conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(table,worker))
                path=initial.input_resolver.directory/'root.json';original=path.read_bytes();mode=stat.S_IMODE(path.stat().st_mode)
                path.chmod(0o600)
                try:path.write_bytes(original+b'\n');assert call()[0]==422
                finally:path.write_bytes(original);path.chmod(mode)
                with owner.connect() as conn:
                    signature=conn.execute(sql.SQL('SELECT integrity_signature FROM {} WHERE result_id=%s').format(table),(record['result_id'],)).fetchone()['integrity_signature']
                    conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
                    conn.execute(sql.SQL('UPDATE {} SET integrity_signature=%s WHERE result_id=%s').format(table),('0'*64,record['result_id']))
                try:assert call()[0]==422
                finally:
                    with owner.connect() as conn:
                        conn.execute(sql.SQL('UPDATE {} SET integrity_signature=%s WHERE result_id=%s').format(table),(signature,record['result_id']))
                        conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
            assert call()[0]==200
        finally:
            https.should_exit=True;thread.join(timeout=15);assert not thread.is_alive();joined+=1
    with jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(storage.schema.TABLE))).fetchone()['n']==2
        assert conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table('thermal_g1_runs'))).fetchone()['n']==0
    assert current_principal() is None and custody_fds(paths)==0 and joined==2
    Path('/tmp/ossf-cycle-api-tls-short-reference-20261006.json').write_text(json.dumps({
        'scope':'synthetic_registered_farm_software_only','actual_tls_scram':True,'responses':observed,
        'original_samples':len(expected['samples']),'original_events':len(expected['events']),
        'actual_steps':terminal['steps'],'whole25h_http_budget_accepted':False,'rhs_during_https':0,
        'https_servers_joined':joined,'custody_fds_after':0,'research_rows':2,'actual_crop_runs':0,
        'max_response_seconds':max(r['seconds'] for r in observed),'max_response_bytes':max(r['bytes'] for r in observed)
    },ensure_ascii=False,indent=2)+'\n')
