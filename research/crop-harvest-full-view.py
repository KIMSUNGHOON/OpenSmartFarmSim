"""Owned native browser acceptance against preserved full synthetic crop/harvest."""
from contextlib import contextmanager, ExitStack
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import select
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def asset_inventory(directory):
    return {str(p.relative_to(directory)): sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def frontend_sources(asset_source):
    paths = [*list((ROOT/'web/src').rglob('*')), *list((ROOT/'web/public').rglob('*'))]
    paths += [ROOT/'web'/n for n in ('package.json', 'package-lock.json', 'index.html',
                                    'vite.config.ts', 'tsconfig.json', 'nginx.conf')]
    pins = {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
    assert pins and all(sha256((asset_source/n).read_bytes()).hexdigest() == h for n,h in pins.items())
    return pins


@contextmanager
def frontend(cost, directory, asset_source, binary, api_port, cert, key):
    directory.mkdir(mode=0o700); (directory/'logs').mkdir(mode=0o700)
    sources = frontend_sources(asset_source); assets = asset_inventory(asset_source/'web/dist')
    assert assets and 'index.html' in assets
    with socket.socket() as probe:
        probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
    template = (ROOT/'web/nginx.conf').read_text()
    mapping = {'/tmp/nginx.pid':str(directory/'nginx.pid'),
        '/etc/nginx/mime.types':str(binary.parents[1]/'conf/mime.types'),
        'listen 8444 ssl;':f'listen 127.0.0.1:{port} ssl;',
        '/run/operator/web/cert.pem':str(cert), '/run/operator/web/key.pem':str(key),
        '/run/operator/web/api-ca.pem':str(cert), '/usr/share/nginx/html':str(asset_source/'web/dist'),
        'https://127.0.0.1:8443':f'https://127.0.0.1:{api_port}'}
    for name in ('client','proxy','fastcgi','uwsgi','scgi'):
        mapping['/tmp/'+name+'-temp'] = str(directory/(name+'-temp'))
    for old,new in mapping.items(): assert old in template; template = template.replace(old,new)
    cost.operator_file(directory/'nginx.conf', template.encode())
    argv = [str(binary), '-p', str(directory)+'/', '-c', str(directory/'nginx.conf'), '-g', 'daemon off;']
    with (directory/'nginx.private.log').open('xb') as log:
        os.fchmod(log.fileno(),0o600); child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic()+10
            while True:
                assert child.poll() is None and time.monotonic() < deadline
                try:
                    with socket.create_connection(('127.0.0.1',port),timeout=.5): break
                except OSError: time.sleep(.05)
            yield f'https://127.0.0.1:{port}'
        finally:
            if child.poll() is None:
                import signal
                child.send_signal(signal.SIGQUIT); child.wait(timeout=10)
            log.flush(); os.fsync(log.fileno())
            cost.operator_file(directory/'frontend-command.private.json', json.dumps({'argv':argv,
                'actual_exit_code':child.returncode, 'binary_sha256':sha256(binary.read_bytes()).hexdigest(),
                'source_sha256':sources, 'asset_sha256':assets, 'source_and_assets_preserved':
                    frontend_sources(asset_source)==sources and asset_inventory(asset_source/'web/dist')==assets},sort_keys=True).encode())
            assert child.returncode == 0 and frontend_sources(asset_source)==sources and asset_inventory(asset_source/'web/dist')==assets


def browser(cost, runtime, original, saved, parent, tokens, origin, directory, observed):
    from app import api_crop_cycle_calculation_replay as public
    from app import crop_harvest_current_query as current
    from unittest.mock import patch
    data = {'pages':{}}; rid = parent['original_record']['result_id']; farm = parent['farm']
    for label,kind,offset,limit in [('summary',None,0,None),('first','samples',0,7),
            ('middle','samples',23904,7),('last','samples',47808,7),('events','events',0,8)]:
        value = original.read('tenant-1',rid,farm,kind=kind,start=offset,limit=limit)
        assert value['record']['payload_sha256'] == parent['original_record']['payload_sha256']
        if kind is None: data['summary'] = public.project_calculation_cycle_result(value['record'],value['terminal']).model_dump(mode='json')
        elif kind == 'samples': data['pages'][str(offset)] = value['page']['records']
        else: data['events'] = value['page']['records']
    store=runtime.harvest_crop_query.store
    comparison=current.HarvestCurrentQuery(current.registry.HarvestRegistry(original,store.policy,store.directory,
        dsn=store._dsn,integrity_key=store.integrity_key))
    harvest = comparison.read('tenant-1',saved['original_record']['result_id'],farm,start=0,limit=6)
    record=harvest['record']
    assert {'result_id':record['result_id'],'payload_sha256':record['payload_sha256'],
        'payload_raw_utf8':record['payload_raw'].decode(),'recorded_at':record['recorded_at'].isoformat()} == saved['original_record']
    assert sha256(json.dumps(harvest['summary'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest() == saved['summary_sha256']
    data.update(harvest_result_id=harvest['record']['result_id'], rows=harvest['page']['records'], whole_summary=harvest['summary'])
    assert len(data['rows'])==6 and data['whole_summary']['row_count']==47813
    assert data['summary']['reference']['sample_count']==47809 and len(data['events'])==5
    rights = runtime.harvest_crop_query.store.query.store.server.binding.input_rights
    original_call = type(rights).__call__
    def denied(instance,*args): return False if instance is rights else original_call(instance,*args)
    argv = ['taskset','-c',str(min(os.sched_getaffinity(0))),'nice','-n','19','node','--expose-gc',
            '--max-old-space-size=64','--max-semi-space-size=2','e2e/harvest-full-replay-native-smoke.mjs',origin,str(directory/'screens')]
    started = time.monotonic(); child = None; report = None
    import gc,ctypes
    gc.collect(); ctypes.CDLL(None).malloc_trim(0)
    with (directory/'browser.private.log').open('xb') as log:
        os.fchmod(log.fileno(),0o600)
        try:
            child = subprocess.Popen(argv,cwd=ROOT/'web',stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=log,text=True,
                env={**os.environ,'MALLOC_ARENA_MAX':'2'})
            def send(value): child.stdin.write(json.dumps(value)+'\n'); child.stdin.flush()
            def receive(name,timeout):
                assert select.select([child.stdout],[],[],timeout)[0], 'owned browser timeout: '+name
                raw = child.stdout.readline(); assert raw, 'owned browser stopped: '+name
                value = json.loads(raw); assert value['stage']==name; return value
            send({'data':data,'tokens':{k:v.decode() for k,v in tokens.items()}})
            receive('geometry_verified',300)
            with patch.object(type(rights),'__call__',denied):
                send({'stage':'rights_revoked'}); receive('rights_denied',45)
            send({'stage':'rights_restored'}); receive('restored_verified',120)
            observed.hold_next=True; send({'stage':'hold_next_summary'})
            receive('held_request_started',15); assert observed.entered.wait(10)
            send({'stage':'cancel_now'}); receive('canceled_account_changed',15)
            observed.release.set(); deadline=time.monotonic()+30
            while observed.active: assert time.monotonic()<deadline; time.sleep(.01)
            send({'stage':'old_request_settled'}); report=receive('verified',60)
            child.communicate(timeout=15); assert child.returncode==0
        finally:
            observed.release.set()
            if child is not None:
                if child.poll() is None: child.terminate()
                try: child.communicate(timeout=15)
                except subprocess.TimeoutExpired: child.kill(); child.communicate(timeout=10)
            log.flush(); os.fsync(log.fileno())
            cost.operator_file(directory/'browser-command.private.json',json.dumps({'argv':argv,
                'actual_exit_code':child.returncode if child is not None else None,
                'seconds':time.monotonic()-started,'stderr_sha256':sha256((directory/'browser.private.log').read_bytes()).hexdigest()},sort_keys=True).encode())
    assert report['errors']==[] and report['actual_WebGL'] and report['verified_rows']==6
    assert set(report['verified_sample_indices'])=={0,1,2,3,4,5,6,23904,23910,47808}
    assert [v['at'] for v in report['verified_events']]==[v['at'] for v in data['events']]
    assert not any(v.decode() in json.dumps(report) for v in tokens.values())
    assert report['peak_active_reads']==observed.peak==1 and observed.active==0
    client_ok=[r for r in report['network'] if r['complete'] and r['status']==200]
    server_ok=[r for r in observed.responses if r['complete'] and r['status']==200 and not r['delayed']]
    assert len(client_ok)==len(server_ok)
    for client,server in zip(client_ok,server_ok):
        assert all(client[k]==server[k] for k in ('endpoint','view','offset','status','bytes','body_sha256','cache'))
    assert len(observed.responses)==len(report['network'])
    assert all(r['complete'] and r['seconds']<=30 and r['bytes']<=2*1024**2 and r['cache']=='no-store' for r in observed.responses)
    assert [r['status'] for r in observed.responses if r['delayed']]==[200]
    assert {r['status'] for r in observed.responses if r['status']!=200}=={403,404,422}
    return report


def run(original_root, manifest, digest, asset_source, nginx, directory):
    import secrets
    directory=Path(directory);directory.mkdir(mode=0o700)
    cost=module('owned_full_harvest_view_cost',ROOT/'research/crop-harvest-api-cost.py')
    saved=cost.original_manifest(original_root,ROOT,manifest,digest,directory)
    storage=cost.load_storage(ROOT,sha256((ROOT/'research/crop-harvest-storage-preservation.py').read_bytes()).hexdigest())
    backup=storage.backup; h=backup.runtime
    from crop_harvest_storage_preservation_smoke import source_inventory
    from test_api_crop_cycle_calculation_tls import fd_inventory
    from crop_harvest_view_native_smoke import Observation
    from app.http_identity import current_principal
    from psycopg import sql
    from unittest.mock import patch
    parent=backup.checked(saved['parent_backup'],saved['parent_backup_sha256'])
    document=json.loads(h.private_bytes(Path(saved['parent_backup']).parent/'original-runtime.private'))
    roots=[Path(manifest).parent,Path(document['input']['directory']),Path(document['server_directory']),
           Path(document['rights_file']),Path(document['principal_file'])]
    before=source_inventory(roots);fds=fd_inventory();cert,key=cost.certificate(backup,directory)
    tokens={n:secrets.token_urlsafe(40).encode() for n in ('owner','denied','foreign')}
    def forbidden(*_,**__): raise AssertionError('full view read attempted calculation, publication or proof')
    with ExitStack() as stack:
        stack.enter_context(backup.readonly_guard());stack.enter_context(storage.read_guard())
        for owner,name in ((h.engine.evidence.InputEvidenceAuthority,'issue'),
                (storage.query.current.storage.server.CalculationServerCustody,'advance'),
                (storage.query.current.storage.CalculationCycleCropResultStore,'put')):
            stack.enter_context(patch.object(owner,name,forbidden))
        context=stack.enter_context(storage.restored_storage(saved,directory/'database'))
        runtime,original,doc,cfg=cost.assemble(storage,saved,manifest,context,directory,tokens,cert,key,0)
        assert runtime.harvest_crop_query.store.query is runtime.calculation_cycle_crop_query
        assert runtime.calculation_cycle_crop_query.store.jobs is runtime.jobs
        assert runtime.calculation_cycle_crop_query.store.server.binding.farms is runtime.farm_authoring
        endpoints=[]
        for connect in (runtime.jobs.connect,runtime.harvest_crop_query.store._connection):
            with connect() as conn:
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
                endpoints.append((conn.info.host,conn.info.port,conn.info.dbname))
        assert endpoints[0]==endpoints[1]
        def counts():
            with runtime.jobs.connect() as conn:
                v={n:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(runtime.jobs._table(n))).fetchone()['n']
                   for n in ('jobs','job_events','crop_cycle_verified_research_results','thermal_g1_runs')}
            with runtime.harvest_crop_query.store._connection() as conn:
                v['harvest']=conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    sql.Identifier(saved['policy']['schema'],storage.registry.schema.TABLE))).fetchone()['n']
            return v
        class ReceivedObservation(Observation):
            async def __call__(self,scope,receive,send):
                hold=self.hold_next and scope['type']=='http' and scope['path'].startswith('/v1/crop-harvest-research-results/')
                if not hold:return await super().__call__(scope,receive,send)
                self.hold_next=False;index=len(self.responses);paused=False
                async def received():
                    nonlocal paused
                    message=await receive()
                    if not paused and message['type']=='http.request' and not message.get('more_body',False):
                        import asyncio
                        paused=True;self.entered.set()
                        assert await asyncio.to_thread(self.release.wait,15), 'owned received request not released'
                    return message
                try:return await super().__call__(scope,received,send)
                finally:
                    assert paused and len(self.responses)==index+1
                    self.responses[index]['delayed']=True
        before_counts=counts(); api=runtime.service.server(); observed=ReceivedObservation(api.config.app);api.config.app=observed
        class Service:
            def server(self):return api
        with cost.serving(Service()) as (_,port):
            with frontend(cost,directory/'frontend',Path(asset_source),Path(nginx),port,cert,key) as origin:
                report=browser(cost,runtime,original,saved,parent,tokens,origin,directory,observed)
        assert counts()==before_counts and current_principal() is None
    assert source_inventory(roots)==before and not (directory/'database/data/postmaster.pid').exists()
    deadline=time.monotonic()+5
    while fd_inventory()!=fds and time.monotonic()<deadline:time.sleep(.05)
    assert fd_inventory()==fds
    result={'scope':'owned_synthetic_same_DB_full_harvest_representative_WebGL','same_actual_SCRAM_DB':True,
        'browser':report,'server_responses':observed.responses,'DB_counts_before_after':[before_counts,before_counts],
        'original_sources_preserved':True,'source_entries':len(before),'FD_before_after':[len(fds),len(fd_inventory())],
        'original_manifest_sha256':digest,'read_RHS_generation_registration_publication_proof_calls':0,
        'shared_control_files_changed':False,'PG_stopped':True,'HTTPS_Nginx_browser_closed':True,
        'realtime_progress':False,'actual_crop_Runs':0,'G0_G4':'not_assessed'}
    backup.write(directory/'view-verified.private.json',backup.canonical(result));return result


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('original-source-root','manifest','asset-source','nginx','directory'):parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--sha256',required=True);args=parser.parse_args()
    run(args.original_source_root,args.manifest,args.sha256,args.asset_source,args.nginx,args.directory)
    print(json.dumps({'owned_full_API_representative_WebGL_verified':True,'root_review_required':True}),flush=True)


if __name__=='__main__':main()
