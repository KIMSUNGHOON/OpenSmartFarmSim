"""Foreground read-only loopback App using original preserved growth and harvest."""
from contextlib import ExitStack
from datetime import timedelta
from hashlib import sha256
import argparse
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import threading
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def run(args):
    directory = Path(args.directory); directory.mkdir(mode=0o700)
    cost = module('owned_user_preview_cost', ROOT/'research/crop-harvest-api-cost.py')
    view = module('owned_user_preview_assets', ROOT/'research/crop-harvest-full-view.py')
    saved = cost.original_manifest(args.original_source_root, ROOT, args.manifest, args.manifest_sha256, directory)
    storage = cost.load_storage(ROOT, sha256((ROOT/'research/crop-harvest-storage-preservation.py').read_bytes()).hexdigest())
    backup = storage.backup; h = backup.runtime
    from crop_harvest_storage_preservation_smoke import source_inventory
    from crop_harvest_view_native_smoke import Observation
    from test_api_crop_cycle_calculation_tls import fd_inventory
    from psycopg import sql
    parent = backup.checked(saved['parent_backup'], saved['parent_backup_sha256'])
    original_doc = json.loads(h.private_bytes(Path(saved['parent_backup']).parent/'original-runtime.private'))
    roots = [Path(args.manifest).parent, Path(original_doc['input']['directory']),
             Path(original_doc['server_directory']), Path(original_doc['rights_file']), Path(original_doc['principal_file'])]
    original_files = source_inventory(roots); sources = view.frontend_sources(Path(args.asset_source))
    assets = view.asset_inventory(Path(args.asset_source)/'web/dist'); assert assets and 'index.html' in assets
    backup.write(directory/'original-files.private.json', backup.canonical(original_files))
    backup.write(directory/'web-pins.private.json', backup.canonical({'sources': sources, 'assets': assets}))
    cert, key = cost.certificate(backup, directory)
    tokens = {n: secrets.token_urlsafe(40).encode() for n in ('owner', 'denied', 'foreign')}
    access = {'token': tokens['owner'].decode(), 'tokens': {n:t.decode() for n,t in tokens.items()},
        'crop': {'result_id': parent['original_record']['result_id'], **parent['farm']},
        'harvest_result_id': saved['original_record']['result_id']}
    backup.write(directory/'access.private.json', backup.canonical(access))
    backup.write(directory/'OPEN-UI.private.txt', ('URL: http://localhost:5173/\n'
        '완료 합성166일 / 생장47,809시점·수확47,813행 / 실시간 진행 기능 아님 / 실제 예측·추천 보류\n'
        '1. 내부 시험 연결 → 접근 토큰 → 연결 설정\n'+access['token']+'\n'
        '2. 08 성장 연구 3D → 저장 결과 판본: calculation cycle v1\n'
        +json.dumps(access['crop'],ensure_ascii=False,indent=2)+'\n'
        '3. 저장 연구 조회 → 저장 수확 결과 ID에 아래 값 → 저장 수확 조회\n'
        +access['harvest_result_id']+'\n'
        '현재 수확3행·다음 범위 / 같은 UTC의 생장 시점 보기\n'
        '생장 범위를 바꾸면 수확 선택이 초기화될 수 있어 수확 ID를 다시 조회합니다.\n'
        '읽기 전용 내부 계정 / 24시간 이내 유효 / 후보 검증 전에는 기존 안내를 사용합니다.\n').encode())
    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM): signal.signal(sig, lambda *_: stop.set())
    attempted = []
    def forbidden(*_, **__):
        attempted.append(True); raise AssertionError('preview attempted calculation or publication')
    with ExitStack() as stack:
        stack.enter_context(backup.readonly_guard()); stack.enter_context(storage.read_guard())
        for owner, name in ((h.engine.evidence.InputEvidenceAuthority, 'issue'),
                (storage.query.current.storage.server.CalculationServerCustody, 'advance'),
                (storage.query.current.storage.CalculationCycleCropResultStore, 'put')):
            stack.enter_context(patch.object(owner, name, forbidden))
        context = stack.enter_context(storage.restored_storage(saved, directory/'database'))
        runtime, original, doc, cfg = cost.assemble(storage, saved, args.manifest, context, directory,
            tokens, cert, key, args.api_port, credential_lifetime=timedelta(seconds=args.ttl_seconds))
        assert runtime.harvest_crop_query.store.query is runtime.calculation_cycle_crop_query
        assert runtime.calculation_cycle_crop_query.store.jobs is runtime.jobs
        endpoints = []
        for connect in (runtime.jobs.connect, runtime.harvest_crop_query.store._connection):
            with connect() as conn:
                assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
                endpoints.append((conn.info.host, conn.info.port, conn.info.dbname))
        assert endpoints[0] == endpoints[1]
        def counts():
            with runtime.jobs.connect() as conn:
                value = {n:conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(runtime.jobs._table(n))).fetchone()['n']
                    for n in ('jobs','job_events','crop_cycle_verified_research_results','thermal_g1_runs')}
            with runtime.harvest_crop_query.store._connection() as conn:
                value['harvest'] = conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(
                    sql.Identifier(saved['policy']['schema'],storage.registry.schema.TABLE))).fetchone()['n']
            return value
        baseline_counts = counts(); api = runtime.service.server(); observed = Observation(api.config.app)
        api.config.app = observed; thread = threading.Thread(target=api.run, daemon=True); thread.start()
        binary = Path(args.nginx); template = (ROOT/'web/nginx.conf').read_text()
        mapping = {'/tmp/nginx.pid':str(directory/'nginx.pid'), '/etc/nginx/mime.types':str(binary.parents[1]/'conf/mime.types'),
            '/run/operator/web/cert.pem':str(cert), '/run/operator/web/key.pem':str(key),
            '/run/operator/web/api-ca.pem':str(cert), '/usr/share/nginx/html':str(Path(args.asset_source)/'web/dist'),
            'https://127.0.0.1:8443':f'https://127.0.0.1:{args.api_port}'}
        for n in ('client','proxy','fastcgi','uwsgi','scgi'): mapping['/tmp/'+n+'-temp']=str(directory/(n+'-temp'))
        for old,new in mapping.items(): assert old in template; template=template.replace(old,new)
        for port in (args.candidate_port,5173):
            backup.write(directory/f'nginx-{port}.conf', template.replace('listen 8444 ssl;',f'listen 127.0.0.1:{port};').encode())
        (directory/'nginx.conf').symlink_to(f'nginx-{args.candidate_port}.conf'); (directory/'logs').mkdir(mode=0o700)
        argv = [str(binary),'-p',str(directory)+'/', '-c',str(directory/'nginx.conf'),'-g','daemon off;']
        fd_before = fd_inventory(); started = time.monotonic()
        with (directory/'nginx.private.log').open('xb') as log:
            os.fchmod(log.fileno(),0o600)
            nginx = subprocess.Popen(argv,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            try:
                deadline=time.monotonic()+15
                while not api.started:
                    assert thread.is_alive() and nginx.poll() is None and time.monotonic()<deadline; time.sleep(.05)
                backup.write(directory/'ready.private.json',backup.canonical({'service_pid':os.getpid(),
                    'frontend_candidate':f'http://localhost:{args.candidate_port}/','backend':f'https://127.0.0.1:{args.api_port}',
                    'api_port':args.api_port,'nginx_pid':nginx.pid,'database_port':context['port'],
                    'same_actual_SCRAM_DB':True,'scope':'owned_completed_full166_synthetic_growth_harvest',
                    'sample_count':47809,'event_count':5,'harvest_row_count':47813,'realtime_progress':False,
                    'source_manifest_sha256':args.manifest_sha256,'DB_counts':baseline_counts,
                    'guarded_math_publication_calls':0,'ttl_seconds':args.ttl_seconds,'G0_G4':'not_assessed'}))
                while not stop.wait(.25):
                    assert thread.is_alive() and nginx.poll() is None and not attempted
                    if time.monotonic()-started>=args.ttl_seconds-5: break
                    live={'service_pid':os.getpid(),'active_requests':observed.active,'responses':observed.responses[-64:],
                        'response_count':len(observed.responses),'FD_count':len(fd_inventory()),'guarded_math_publication_calls':len(attempted)}
                    raw=backup.canonical(live); temporary=directory/'live.private.tmp'
                    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
                    with os.fdopen(fd,'wb') as f:f.write(raw)
                    os.replace(temporary,directory/'live.private.json')
            finally:
                if nginx.poll() is None:nginx.send_signal(signal.SIGQUIT);nginx.wait(timeout=15)
                api.should_exit=True;thread.join(timeout=30);assert not thread.is_alive()
        assert counts()==baseline_counts and not attempted
        assert source_inventory(roots)==original_files and view.frontend_sources(Path(args.asset_source))==sources
        assert view.asset_inventory(Path(args.asset_source)/'web/dist')==assets
    assert not (directory/'database/data/postmaster.pid').exists()
    removed=sum(p.stat().st_size for p in (directory/'database/data').rglob('*') if p.is_file())
    shutil.rmtree(directory/'database/data')
    backup.write(directory/'service-terminal.private.json',backup.canonical({'service_exit':0,'PG_and_HTTPS_stopped':True,
        'nginx_exit':nginx.returncode,'DB_counts_unchanged':True,'originals_preserved':True,
        'guarded_math_publication_calls':0,'owned_stopped_data_removed_bytes':removed,'G0_G4':'not_assessed'}))


def main():
    p=argparse.ArgumentParser()
    for name in ('original-source-root','manifest','manifest-sha256','asset-source','nginx','directory'):p.add_argument('--'+name,required=True)
    p.add_argument('--api-port',type=int,default=8445);p.add_argument('--candidate-port',type=int,default=5174)
    p.add_argument('--ttl-seconds',type=int,default=86340)
    args=p.parse_args();assert 60<=args.ttl_seconds<=86400 and args.candidate_port!=5173
    run(args)


if __name__=='__main__': main()
