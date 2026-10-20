"""Explicit capacity checks using normal producers, signed rows and real TLS/SCRAM."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import http.client
import json
import os
from pathlib import Path
import secrets
import ssl
import threading
import time
from urllib.parse import urlencode

import psycopg
from psycopg import sql
import pytest

from app.api_runtime import ApiRuntime
from app.crop_result_store import CropResultStore, READ_SCOPES, MAX_PACKET_BYTES
from app.http_identity import BearerGrant, BearerRegistry, token_digest
from app.market_source_store import MarketSourceStore
from app.thermal_run_store import _canonical
from test_api_crop_replay import CROP_POLICY
from test_api_runtime import config, dependencies
from test_api_serve import tls_files
from test_crop_result_store import (crop_setup, authoring, farm_setup, login_scope,
    login_database, PROFILE, NOTICE, KEY, put, count)
from test_market_hold_store import context_verifier

pytestmark=pytest.mark.parametrize('login_scope',[CROP_POLICY],indirect=True)


def stamp(value):
    return value.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')


def save(path,value):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(),0o400)
        json.dump(value,stream,sort_keys=True,indent=2)


def load_request(original):
    body=deepcopy(original)
    program=body['program']
    parse=lambda value:datetime.fromisoformat(value.replace('Z','+00:00'))
    text=lambda value:value.isoformat().replace('+00:00','Z')
    start=parse(program['segments'][0]['start'])
    boundary=parse(program['segments'][0]['end'])
    delta=timedelta(seconds=3600)-(parse(program['segments'][-1]['end'])-start)
    assert delta.total_seconds()>0
    for segment in program['segments']:
        for field in ('start','end'):
            at=parse(segment[field])
            if at>=boundary:
                segment[field]=text(at+delta)
    for event in program['events']:
        at=parse(event['at'])
        if at>=boundary:
            event['at']=text(at+delta)
    program['output_times']=[text(start+timedelta(seconds=n)) for n in range(3601)]
    body['rights']['program_sha256']=sha256(_canonical(program)).hexdigest()
    return body


def fingerprint(store,result_id):
    row=store._find('tenant-1',result_id=result_id)
    raw=row['payload_raw']
    assert sha256(raw).hexdigest()==row['payload_sha256']
    fields={k:str(v) for k,v in row.items() if k!='payload_raw'}
    fields['actual_payload_SHA256']=sha256(raw).hexdigest()
    return sha256(_canonical(fields)).hexdigest()


def exercise(setup,tls,tmp_path,monkeypatch,total):
    store,original,_,rights=setup
    evidence=Path(os.environ['OSSF_JOINT_PREFIX_RUNTIME_EVIDENCE'])
    body=load_request(original)
    records=[]
    preparation=time.monotonic()
    for index in range(total):
        request=deepcopy(body)
        request['study_id']='capacity-'+str(index).zfill(2)
        started=time.monotonic()
        record=put(store,request)
        packet=json.loads(record['payload_raw'])
        assert packet['result']['status']=='completed','normal load producer returned a numeric hold'
        assert len(packet['result']['samples'])==3601
        size=len(record['payload_raw'])
        assert 65536<size<=MAX_PACKET_BYTES,'normal load packet size is outside declared test range'
        records.append({'result_id':record['result_id'],'recorded_at':stamp(record['recorded_at']),
            'packet_bytes':size,'payload_SHA256':record['payload_sha256'],
            'samples':len(packet['result']['samples']),'steps':packet['result']['steps'],
            'planned_steps':packet['result']['planned_steps'],'producer_seconds':time.monotonic()-started,
            'row_fingerprint':fingerprint(store,record['result_id'])})
        del packet,record
        progress={'phase':'normal_producer_preparation','completed':len(records),'target':total,
            'preparation_seconds':time.monotonic()-preparation,'records':records}
        target=evidence/('organ-capacity-'+str(total)+'-progress.private.json')
        temporary=target.with_suffix('.tmp')
        temporary.write_text(json.dumps(progress,indent=2))
        temporary.chmod(0o600)
        os.replace(temporary,target)
    preparation_seconds=time.monotonic()-preparation
    jobs,replay=store.jobs,store.farms.replay
    research,holds=replay.owned_research,replay.thermal.holds
    cert,key,_=tls
    now=datetime.now(timezone.utc)
    token=secrets.token_urlsafe(40).encode()
    grant=BearerGrant(token_digest(token),'tenant-1',frozenset(READ_SCOPES),
        now-timedelta(seconds=1),now+timedelta(minutes=10))

    def source_factory(*,principal_provider):
        return MarketSourceStore(jobs._dsn,jobs.schema,principal_provider=principal_provider,
            runtime_identity=jobs.runtime_identity)

    def crop_factory(*,farm_authoring_service):
        return CropResultStore(farm_authoring_service,PROFILE,NOTICE,program_rights=rights,integrity_key=KEY)

    os.close(jobs._content_directory(create=True))
    runtime=ApiRuntime(config(policy=jobs.runtime_identity[0],dsn=jobs._dsn,
        artifact_root=jobs.artifact_root,certificate=cert,private_key=key,port=0),
        dependencies(research_registry=research.catalog,bearer_registry=BearerRegistry((grant,)),
            owned_fixture_registry=research.registry,owned_research_contexts=dict(research._contexts),
            context_verifier=context_verifier,market_scope_resolver=holds._scope_resolver,
            market_source_factory=source_factory,crop_result_store_factory=crop_factory))

    def counts():
        with jobs.connect() as conn:
            return {name:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}')
                .format(jobs._table(name))).fetchone()['n'] for name in (
                'jobs','job_events','crop_research_results','thermal_g1_runs')}

    before=counts()
    assert before['crop_research_results']==total
    calls={'put':0,'integrate':0,'RHS':0,'SQL_writes':0}

    def forbidden(name):
        def reject(*args,**kwargs):
            calls[name]+=1
            raise AssertionError('capacity GET attempted '+name)
        return reject

    monkeypatch.setattr(CropResultStore,'put',forbidden('put'))
    monkeypatch.setattr('app.crop_result_store.integrate_crop',forbidden('integrate'))
    monkeypatch.setattr('app.crop_growth_integration.rates.calculate_rates',forbidden('RHS'))
    execute=psycopg.Connection.execute

    def no_writes(conn,statement,*args,**kwargs):
        text=statement.as_string(conn) if hasattr(statement,'as_string') else statement
        if text.split(None,1)[0].upper() in ('INSERT','UPDATE','DELETE','TRUNCATE','CREATE','ALTER','DROP','GRANT','REVOKE'):
            calls['SQL_writes']+=1
            raise AssertionError('capacity GET attempted SQL mutation')
        return execute(conn,statement,*args,**kwargs)

    server=runtime.service.server()
    thread=threading.Thread(target=server.run,daemon=True)
    observations=[]
    result={'scope':'owned synthetic organ metadata capacity only','records':records,
        'record_count':total,'program_SHA256':body['rights']['program_sha256'],
        'period_seconds':3600,'output_interval_seconds':1,'samples_per_result':3601,
        'packet_bytes_sum':sum(r['packet_bytes'] for r in records),
        'preparation_seconds':preparation_seconds,'observations':observations,
        'request_deadline_seconds':30,'metadata_max_bytes':65536,
        'actual_TLS_SCRAM_Bearer':True,'accepted':False,'browser_performed':False,
        'WSL_browser_capacity_accepted':False,'actual_crop_Runs':0,'G0_G4':'not_assessed','U1_accepted':False}
    thread.start()
    try:
        end=time.monotonic()+15
        while not server.started:
            assert thread.is_alive() and time.monotonic()<end
            time.sleep(.01)
        port=server.servers[0].sockets[0].getsockname()[1]
        trust=ssl.create_default_context(cafile=str(cert))

        def call(extra=None,expected=200):
            query={'kind':'organ_v1',**body['farm'],'limit':20,**(extra or {})}
            path='/v1/crop-research-result-catalog?'+urlencode(query)
            began=time.monotonic()
            deadline=began+30
            conn=http.client.HTTPSConnection('127.0.0.1',port,context=trust,timeout=30)
            observation={'path':path,'expected_status':expected}
            observations.append(observation)
            try:
                conn.connect()
                def remaining():
                    left=deadline-time.monotonic()
                    assert left>0,'capacity whole-response deadline exceeded'
                    return left
                conn.sock.settimeout(remaining())
                conn.request('GET',path,headers={'Authorization':'Bearer '+token.decode()})
                conn.sock.settimeout(remaining())
                response=conn.getresponse()
                channel=conn.sock or response.fp.raw._sock
                channel.settimeout(remaining())
                wire=response.read(65537)
                elapsed=time.monotonic()-began
                observation.update(status=response.status,bytes=len(wire),body_SHA256=sha256(wire).hexdigest(),
                    full_response_seconds=elapsed,cache_control=response.getheader('Cache-Control'))
                assert elapsed<30 and len(wire)<=65536 and observation['cache_control']=='no-store'
                assert response.status==expected,'capacity status differs'
                return json.loads(wire)
            except Exception as error:
                observation.update(error_type=type(error).__name__,full_response_seconds=time.monotonic()-began)
                raise
            finally:
                conn.close()

        with monkeypatch.context() as read_patch:
            read_patch.setattr(psycopg.Connection,'execute',no_writes)
            page=call()
            assert page['kind']=='organ_v1' and page['farm']==body['farm']
            assert len(page['items'])==total and page['next_cursor'] is None
            ordered=sorted(records,key=lambda r:(r['recorded_at'],r['result_id']),reverse=True)
            assert [i['result_id'] for i in page['items']]==[r['result_id'] for r in ordered]
            assert all(i['sample_count']==3601 and i['calculation_status']=='completed' for i in page['items'])
            assert page['rights_or_gate_approval'] is False and page['selection_validation_required'] is True
            last=page['items'][-1]
            tail=call({'before_recorded_at':last['recorded_at'],'before_result_id':last['result_id']})
            assert tail['items']==[] and tail['next_cursor'] is None
            rights.allowed=False
            call(expected=422)
            rights.allowed=True
            assert call()==page
        assert counts()==before and all(n==0 for n in calls.values())
        assert all(fingerprint(store,r['result_id'])==r['row_fingerprint'] for r in records)
        with jobs.connect() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        result.update(accepted=True,query_calls=calls,selected_DB_counts_before_after=[before,counts()],
            original_rows_payloads_hashes_signatures_unchanged=True)
    finally:
        rights.allowed=True
        server.should_exit=True
        thread.join(timeout=15)
        result.update(HTTPS_server_joined=not thread.is_alive(),query_calls=calls)
        save(evidence/('organ-capacity-'+str(total)+'.private.json'),result)
        assert not thread.is_alive(),'owned capacity HTTPS server did not stop'


def test_normal_large_producer_size_and_single_metadata_preflight(crop_setup,tls_files,tmp_path,monkeypatch):
    exercise(crop_setup,tls_files,tmp_path,monkeypatch,1)


def test_twenty_normal_large_signed_results_actual_HTTPS_capacity(crop_setup,tls_files,tmp_path,monkeypatch):
    exercise(crop_setup,tls_files,tmp_path,monkeypatch,20)
