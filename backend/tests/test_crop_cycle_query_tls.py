"""Actual selected query/runtime, SCRAM and full HTTPS bodies; synthetic only."""
from copy import deepcopy
from dataclasses import replace
from datetime import datetime,timedelta,timezone
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import ssl
import threading
import time
from urllib.parse import urlencode

from psycopg import sql
import pytest

from app import api_crop_cycle_replay as public
from app import crop_cycle_current_query as query
from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_plant_startup_integration as original
from app.crop_cycle_farm_binding import CycleFarmBinding
from app.api_runtime import ApiRuntime
from app.http_identity import BearerGrant,BearerRegistry,current_principal,token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_crop_cycle_current_query import prepared,forbid_calculation,audit_query_cleanup
from test_crop_cycle_result_evidence import authority
from test_crop_cycle_server_custody_farms import server_setup,KEY,BUDGET
from test_crop_cycle_result_store_farms import DB_KEY
from test_crop_cycle_artifact import PROFILES,NOTICE
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database,login_scope
from test_api_runtime import config,dependencies
from test_api_serve import tls_files
from test_market_hold_store import context_verifier
from test_api_crop_cycle_tls import OwnInputs,custody_fds

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)


class OwnEvidencePaths:
    version='owned-current-cycle-runtime-evidence-v1'
    def __init__(self,paths):self.paths=paths
    def __call__(self,tenant,packet):
        assert tenant=='tenant-1'
        return dict(self.paths[packet['input_root_sha256']])


def test_actual_query_runtime_TLS_original_values_hold_restart_withdrawal_and_cleanup(prepared,tls_files,tmp_path,monkeypatch,login_scope):
    service,record,farm,rights,_,expected=prepared;initial=service.store.server
    body=json.loads(record['payload_raw'])['binding']['request']
    managed=shifted('full-removal-reentry');expected=original.integrate_plant_startup(**managed,**PROFILES)
    assert expected['events']
    anchors=managed.pop('output_times');managed_path=tmp_path/'managed-input'
    managed_input=inputs.write_input_packet(managed_path,**managed,anchors=anchors,outputs=anchors,**PROFILES,program_id='owned-current-query-managed')
    managed_body=deepcopy(body);managed_body['study_id']='owned-current-query-managed-study'
    managed_body['input'].update(root_sha256=managed_input['root_sha256'],program_id='owned-current-query-managed')
    managed_body['rights']['input_root_sha256']=managed_input['root_sha256']
    held=shifted('empty-entry');held['initial_state']['values']['temperature_sum']['value']=0
    anchors=held.pop('output_times');hold_path=tmp_path/'held-input'
    hold_input=inputs.write_input_packet(hold_path,**held,anchors=anchors,outputs=anchors,**PROFILES,program_id='owned-current-query-held')
    hold_body=deepcopy(body);hold_body['study_id']='owned-current-query-held-study'
    hold_body['input'].update(root_sha256=hold_input['root_sha256'],program_id='owned-current-query-held')
    hold_body['rights']['input_root_sha256']=hold_input['root_sha256'];hold_raw=_canonical(hold_body)
    resolver=OwnInputs({body['input']['root_sha256']:initial.input_resolver.directory,
        managed_input['root_sha256']:managed_path,hold_input['root_sha256']:hold_path})
    server=custody.CycleServerCustody(initial.binding,initial.directory,input_resolver=resolver,integrity_key=KEY)
    managed_progress=json.loads(server.advance('tenant-1',_canonical(managed_body),budget=BUDGET))
    assert managed_progress['status']=='completed'
    progress=json.loads(server.advance('tenant-1',hold_raw,budget=BUDGET));assert progress['status']=='hold'
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY)
    record=store.put('tenant-1',_canonical(managed_body));hold_record=store.put('tenant-1',hold_raw)
    control=store.summary('tenant-1',record['result_id'],farm);hold_control=store.summary('tenant-1',hold_record['result_id'],farm)
    issuer=authority();proofs={body['input']['root_sha256']:service.evidence_resolver.values}
    for request,path,selected in ((hold_body,hold_path,progress),(managed_body,managed_path,managed_progress)):
        for file in path.iterdir():file.chmod(0o400)
        root=request['input']['root_sha256'];input_raw=issuer.input_authority.issue(path,root)
        directory=server.directory/custody._intent_id('tenant-1',request)/'artifact'
        result_raw=issuer.issue(directory,selected['artifact_sha256'],path,root,input_raw)
        proofs[root]={'input_directory':path,'input_evidence_raw':input_raw,'result_evidence_raw':result_raw}
    evidence_resolver=OwnEvidencePaths(proofs);body=managed_body
    jobs=store.jobs;replay=server.binding.farms.replay;research=replay.owned_research;cert,key,_=tls_files
    now=datetime.now(timezone.utc);tokens={name:('owned-current-query-'+name+'-'+'d'*40).encode() for name in ('owner','denied','foreign')}
    subjects=(('owner','tenant-1',public.READ_SCOPES),('denied','tenant-1',set(public.READ_SCOPES)-{'crop_result_read'}),
        ('foreign','foreign',public.READ_SCOPES))
    grants=tuple(BearerGrant(token_digest(tokens[name]),tenant,frozenset(scopes),now-timedelta(seconds=1),now+timedelta(hours=1))
        for name,tenant,scopes in subjects)
    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,runtime_identity=jobs.runtime_identity)
    def crop_factory(*,farm_authoring_service):
        binding=CycleFarmBinding(farm_authoring_service,**PROFILES,notice_raw=NOTICE,input_rights=rights)
        owned=custody.CycleServerCustody(binding,server.directory,input_resolver=resolver,integrity_key=KEY)
        return storage.CycleCropResultStore(owned,integrity_key=DB_KEY)
    def query_factory(*,result_store):
        return query.CurrentCycleQuery(result_store,authority(),evidence_resolver=evidence_resolver)
    cfg=config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,artifact_root=jobs.artifact_root,certificate=cert,private_key=key,port=0)
    deps=dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry(grants),
        owned_fixture_registry=research.registry,owned_research_contexts=dict(research._contexts),context_verifier=context_verifier,
        market_scope_resolver=replay.thermal.holds._scope_resolver,market_source_factory=source_factory,
        crop_cycle_result_store_factory=crop_factory,crop_cycle_current_query_factory=query_factory)
    descriptor=jobs._content_directory(create=True);os.close(descriptor)
    forbid_calculation(monkeypatch)
    trust=ssl.create_default_context(cafile=str(cert));observed=[];joined=0
    paths=[server.directory,*resolver.paths.values()]
    def target(which=record,view='summary',**pages):
        return '/v1/crop-cycle-research-results/'+which['result_id']+'?'+urlencode({**farm,'view':view,**pages})
    for restart in range(2):
        runtime=ApiRuntime(cfg,deps)
        assert runtime.cycle_crop_query.store is runtime.cycle_crop_results
        assert runtime.cycle_crop_query.store.jobs is runtime.jobs
        for bad in (lambda **_:service,lambda **_:object()):
            with pytest.raises(ValueError,match='^API runtime assembly rejected$'):
                ApiRuntime(cfg,replace(deps,crop_cycle_current_query_factory=bad))
        https=runtime.service.server();thread=threading.Thread(target=https.run,daemon=True);thread.start()
        try:
            deadline=time.monotonic()+15
            while not https.started:
                assert thread.is_alive() and time.monotonic()<deadline;time.sleep(.01)
            port=https.servers[0].sockets[0].getsockname()[1]
            def call(where=None,bearer='owner'):
                connection=http.client.HTTPSConnection('127.0.0.1',port,timeout=30,context=trust)
                try:
                    headers={} if bearer is None else {'Authorization':'Bearer '+tokens[bearer].decode()}
                    tick=time.monotonic();connection.request('GET',where or target(),headers=headers)
                    response=connection.getresponse();raw=response.read();seconds=time.monotonic()-tick
                    assert seconds<30 and len(raw)<=public.MAX_RESPONSE_BYTES
                    assert response.getheader('cache-control')=='no-store'
                    if response.status==200:
                        assert response.getheader('X-OSSF-Crop-Query-Version')==query.VERSION
                        assert response.getheader('X-OSSF-Crop-Query-Code-SHA256')==query.CODE_SHA256
                    observed.append({'status':response.status,'seconds':seconds,'bytes':len(raw),'sha256':sha256(raw).hexdigest()})
                    assert custody_fds(paths)==0
                    return response.status,json.loads(raw)
                finally:connection.close()
            status,value=call();assert status==200 and value['result_id']==record['result_id']
            assert _canonical(value['summary']['manifest'])==_canonical(control['manifest'])
            if not restart:
                assert call(bearer=None)[0]==401 and call(bearer='denied')[0]==403 and call(bearer='foreign')[0]==404
                for kind,limit in (('samples',2),('events',1)):
                    rows=[];offset=0
                    while True:
                        status,value=call(target(view=kind,offset=offset,limit=limit));assert status==200
                        page=value['page'];rows.extend(page['records'])
                        if page['next_offset'] is None:break
                        offset=page['next_offset']
                    original_rows=expected[kind]
                    if kind=='events':original_rows=[{k:e[k] for k in ('at','before','after','removed')} for e in original_rows]
                    assert _canonical(rows)==_canonical(original_rows)
                    assert call(target(view=kind,offset=len(rows),limit=limit))[1]['page']['records']==[]
                status,value=call(target(hold_record));assert status==200 and value['summary']['hold']['at']==hold_control['hold']['at']
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
                        raw=original_bytes(value);rights.allowed=False;return raw
                    patch.setattr(public,'_public_bytes',withdraw)
                    try:assert call()[0]==422
                    finally:rights.allowed=True
                owner,policy,_=login_scope;table=jobs._table(storage.schema.TABLE)
                worker=sql.Identifier(policy.roles['worker'])
                with owner.connect() as conn:conn.execute(sql.SQL('GRANT SELECT ON {} TO {}').format(table,worker))
                try:assert call()[0]==503
                finally:
                    with owner.connect() as conn:conn.execute(sql.SQL('REVOKE SELECT ON {} FROM {}').format(table,worker))
                intent=server.directory/custody._intent_id('tenant-1',body)/'intent.json';raw=intent.read_bytes()
                try:
                    intent.chmod(0o600);intent.write_bytes(raw+b' ');intent.chmod(0o400)
                    assert call()[0]==422
                finally:intent.chmod(0o600);intent.write_bytes(raw);intent.chmod(0o400)
            assert call()[0]==200
        finally:
            https.should_exit=True;thread.join(timeout=15);assert not thread.is_alive();joined+=1
    assert current_principal() is None and custody_fds(paths)==0 and joined==2
    with jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        research_rows=conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table(storage.schema.TABLE))).fetchone()['n']
        actual_runs=conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(jobs._table('thermal_g1_runs'))).fetchone()['n']
    assert research_rows==3 and actual_runs==0
    destination=os.environ.get('OSSF_CURRENT_QUERY_TLS_REFERENCE')
    if destination:
        value={'scope':'synthetic_registered_farm_query_software_only','actual_scram_tls':True,
            'steps':control['steps'],'counts':{'samples':len(expected['samples']),'events':len(expected['events'])},
            'original_checkpoint_sha256':control['checkpoint']['checkpoint_sha256'],
            'original_manifest_sha256':sha256(_canonical(control['manifest'])).hexdigest(),
            'responses':observed,'max_response_seconds':max(r['seconds'] for r in observed),
            'max_response_bytes':max(r['bytes'] for r in observed),'query_version':query.VERSION,
            'query_code_sha256':query.CODE_SHA256,'parser_context_QC_RHS_calls_during_query':0,
            'servers_joined':joined,'custody_FDs_after':0,'research_rows_before_cleanup':research_rows,
            'actual_crop_runs':actual_runs,'whole166_accepted':False}
        with Path(destination).open('x') as handle:json.dump(value,handle,sort_keys=True,indent=2);handle.write('\n')
        Path(destination).chmod(0o400)
