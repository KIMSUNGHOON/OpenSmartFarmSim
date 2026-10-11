"""Prepare and serve a persistent loopback preview using owned synthetic inputs."""
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import argparse
import importlib.util
import ipaddress
import json
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'backend'), str(ROOT/'backend/tests')]


def save(path, value, *, raw=False):
    temporary = path.with_name(path.name+'.tmp')
    with temporary.open('xb') as output:
        os.fchmod(output.fileno(), 0o600)
        output.write(value if raw else json.dumps(value, sort_keys=True).encode())
        output.flush(); os.fsync(output.fileno())
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY); os.fsync(descriptor); os.close(descriptor)


def command(argv, directory, name, *, stdout=None):
    with (directory/(name+'.private.log')).open('xb') as errors:
        os.fchmod(errors.fileno(), 0o600)
        subprocess.run(list(map(str, argv)), stdin=subprocess.DEVNULL,
            stdout=stdout if stdout is not None else subprocess.DEVNULL, stderr=errors, check=True, timeout=45)


def database(args, directory, *, initialize=False):
    from psycopg.conninfo import make_conninfo
    if initialize:
        sockets = Path('/tmp')/('ossf-joint-live-'+secrets.token_hex(6)); sockets.mkdir(mode=0o700)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0)); port = probe.getsockname()[1]
        save(directory/'database.private.json', {'socket':str(sockets), 'port':port})
        command([args.pg_bin/'initdb','-D',directory/'database','-U','ossf_preview_admin',
            '--auth-local=trust','--auth-host=scram-sha-256','--no-locale','--encoding=UTF8'],directory,'initdb')
    config = json.loads((directory/'database.private.json').read_bytes())
    return config, make_conninfo(host=config['socket'], port=config['port'], dbname='postgres', user='ossf_preview_admin')


@contextmanager
def running_database(args, directory, label):
    config, dsn = database(args,directory)
    command([args.pg_bin/'pg_ctl','-D',directory/'database','-l',directory/('postgres-'+label+'.private.log'),
        '-w','-t','10','start','-o',f"-h 127.0.0.1 -p {config['port']} -k {config['socket']}"],directory,'pg-start-'+label)
    try:
        yield config, dsn
    finally:
        command([args.pg_bin/'pg_ctl','-D',directory/'database','-m','fast','-w','-t','10','stop'],directory,'pg-stop-'+label)


def dump(args, directory, dsn, name, *, roles=False):
    with (directory/(name+('.sql' if roles else '.dump'))).open('xb') as output:
        os.fchmod(output.fileno(), 0o600)
        argv = [args.pg_bin/('pg_dumpall' if roles else 'pg_dump'), '--dbname', dsn]
        argv += ['--roles-only'] if roles else ['--format=custom']
        command(argv,directory,name,stdout=output); output.flush(); os.fsync(output.fileno())


def prepare(args):
    import pytest
    import test_crop_climate_joint_execution_runtime as reference
    import test_crop_climate_joint_result_store as registered
    from psycopg.conninfo import conninfo_to_dict, make_conninfo
    directory = args.directory; directory.mkdir(mode=0o700)
    seed = directory/'seed'; seed.mkdir(mode=0o700)
    os.environ['OSSF_TEST_PG_DSN'] = 'host=/tmp/owned-joint-preview-seed dbname=postgres user=ossf_login_admin'
    os.environ['OSSF_TEST_PG_BIN'] = str(args.pg_bin)
    def fixture(value, *a):
        return value.__wrapped__(*a)
    with ExitStack() as stack:
        patch = stack.enter_context(pytest.MonkeyPatch.context())
        source_db = stack.enter_context(contextmanager(reference.login_database.__wrapped__)())
        options = SimpleNamespace(param={key:True for key in ('market_calculation','market_source_storage',
            'thermal_scenario_storage','break_even_calculation','crop_cycle_result_storage')})
        original_scope = stack.enter_context(contextmanager(reference.original_login_scope.__wrapped__)(source_db,seed,options))
        scope = fixture(reference.login_scope,original_scope,SimpleNamespace(param=True))
        authoring = fixture(reference.authoring,fixture(reference.farm_setup,scope,patch))
        profiles = fixture(reference.profiles)
        custody, raw, value = fixture(registered.producer.setup,authoring,seed,profiles,SimpleNamespace(param=None),patch)
        value[4]['scopes'].update(reference.SCOPES)
        binding, body, packet, _, principal, _ = value
        packet_root = directory/'inputs'; packet_root.mkdir(mode=0o700)
        input_key = secrets.token_bytes(32); reviews = {}; inputs = {}; requests = {}
        for mode in ('normal','hold'):
            case = deepcopy(registered.producer.reference.inputs.reference.reference.CASES[6])
            if mode == 'hold':case['events'][-1]['event']['values']['leaf']['value'] = 50000
            origin = registered.producer.reference.inputs.reference.origin('2026-10-01T00:00:00.123456Z')
            p = registered.producer.reference.inputs.packet(packet_root/mode,profiles,case,origin)
            p[3]['evidence_id'] = 'owned-preview-'+mode+'-review-v1'
            authority = registered.producer.reference.inputs.model.JointInputEvidenceAuthority(integrity_key=input_key,
                issuer_id='owned-preview',key_id='owned-preview-v1',review_resolver=lambda _, review=p[3]:deepcopy(review))
            proof = registered.producer.reference.inputs.issue(authority,p)
            proof_file = packet_root/(mode+'.proof.private.json'); save(proof_file,proof,raw=True)
            reviews[p[3]['evidence_id']] = p[3]
            inputs[p[1]] = {'directory':str(p[0]),'proof':str(proof_file)}
            request = deepcopy(body)
            request['input'].update(source_sha256=p[1],context_sha256=p[2]._context.root_sha256,
                time_binding_sha256=p[2].sha256,evidence_sha256=sha256(proof).hexdigest())
            request['rights']['input_source_sha256'] = p[1]
            requests[mode] = request
        pack_file = registered.producer.fresh_pack(seed,value,b'not-executed',custody)
        p = json.loads(pack_file.read_bytes()); original_dsn = conninfo_to_dict(p['dsn'])
        descriptor = binding.jobs._content_directory(create=True); os.close(descriptor)
        credentials = directory/'credentials'; credentials.mkdir(mode=0o700)
        passfile = credentials/'authority.pgpass'; save(passfile,Path(original_dsn['passfile']).read_bytes(),raw=True)
        dump(args,directory,source_db['admin'],'bootstrap-roles',roles=True)
        dump(args,directory,source_db['admin'],'bootstrap-database')
        database(args,directory,initialize=True)
        target = json.loads((directory/'database.private.json').read_bytes())
        pieces = passfile.read_text().rstrip('\n').split(':')
        pieces[1] = str(target['port']); save(passfile,(':'.join(pieces)+'\n').encode(),raw=True)
        dsn = make_conninfo(host='127.0.0.1',port=target['port'],dbname='postgres',user=original_dsn['user'],
            passfile=str(passfile),sslmode='disable')
        cfg = reference.config()
        legacy = directory/'legacy'; legacy.mkdir(mode=0o700)
        p.update(dsn=dsn,inputs=inputs,input_key=input_key.hex(),custody_key=secrets.token_hex(32),result_key=secrets.token_hex(32),
            thermal_key=cfg.thermal_gate_key.hex(),market_key=cfg.market_hold_key.hex(),legacy=str(legacy),
            scopes=sorted(reference.SCOPES),service_principal={**principal,'scopes':sorted(principal['scopes'])},root=str(ROOT))
        save(directory/'runtime.private.json',p); save(directory/'reviews.private.json',reviews)
        save(directory/'rights.private.json',{source:True for source in inputs})
        request_dir = directory/'requests'; request_dir.mkdir(mode=0o700)
        for name,mode in [('normal-validation','normal'),('hold-validation','hold'),('cancel-validation','normal'),('normal-user','normal')]:
            request = deepcopy(requests[mode]); request.update(study_id='joint-preview',revision=name+'-v1')
            save(request_dir/(name+'.json'),request)
        save(directory/'farm.private.json',body['farm'])
        pack_file.unlink(); (seed/'proof.private.json').unlink()
    with running_database(args,directory,'restore') as (_,dsn):
        command([args.pg_bin/'psql','--dbname',dsn,'-v','ON_ERROR_STOP=1','-f',directory/'bootstrap-roles.sql'],directory,'restore-roles')
        command([args.pg_bin/'pg_restore','--dbname',dsn,'--exit-on-error',directory/'bootstrap-database.dump'],directory,'restore-database')
    shutil.copyfile(ROOT/'research/crop-climate-joint-live-operator.py',directory/'joint_live_operator.py')
    (directory/'joint_live_operator.py').chmod(0o600)
    save(directory/'prepared.private.json',{'source_root':str(ROOT),'synthetic':True,'crop_Runs':0,'G0_G4':'not_assessed'})


def certificate(directory, lifetime):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes,serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import NameOID
    key = ec.generate_private_key(ec.SECP256R1()); now = datetime.now(timezone.utc)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Owned joint preview')])
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
        .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=1))
        .not_valid_after(now+timedelta(seconds=lifetime+300))
        .add_extension(x509.SubjectAlternativeName([x509.IPAddress(ipaddress.ip_address('127.0.0.1')),x509.DNSName('localhost')]),False)
        .sign(key,hashes.SHA256()))
    cert_file = directory/'cert.pem'; key_file = directory/'key.pem'
    save(cert_file,cert.public_bytes(serialization.Encoding.PEM),raw=True)
    save(key_file,key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()),raw=True)
    return cert_file,key_file


def serve(args):
    from app import crop_climate_joint_operator_config as loader
    from app.http_identity import token_digest
    if not args.enable_prefix and args.worker_chunk_budget != 16:
        raise ValueError('custom worker chunk budget requires the explicit prefix preview')
    factory = 'joint_live_operator'
    if args.enable_prefix:
        factory = 'joint_prefix_live_operator_v1'
        source = (ROOT/'research/crop-climate-joint-live-operator.py').read_bytes()
        target = args.directory/(factory+'.py')
        if target.exists():
            assert not target.is_symlink() and target.read_bytes() == source
        else:
            with target.open('xb') as output:
                os.fchmod(output.fileno(), 0o600)
                output.write(source); output.flush(); os.fsync(output.fileno())
    directory=args.directory; run=directory/args.run;run.mkdir(mode=0o700)
    p=json.loads((directory/'runtime.private.json').read_bytes()); now=datetime.now(timezone.utc); token=secrets.token_urlsafe(40)
    p.update(token_digest=token_digest(token.encode()),issued_at=now.isoformat(),expires_at=(now+timedelta(seconds=args.ttl_seconds)).isoformat(),
        worker_chunk_budget=args.worker_chunk_budget)
    save(directory/'runtime.private.json',p);save(run/'access.private.json',{'token':token,'farm':json.loads((directory/'farm.private.json').read_bytes())})
    cert,key=certificate(run,args.ttl_seconds)
    config={'config_version':loader.PREFIX_VERSION if args.enable_prefix else loader.EXECUTION_VERSION,'policy':p['policy'],'artifact_root':p['artifacts'],
        'certificate':str(cert),'private_key':str(key),'authored_run_gate_key_file':None,'content_access':None,
        'host':'127.0.0.1','port':args.api_port,'dependencies_factory':factory+':dependencies','crop_climate_joint_execution':True}
    if args.enable_prefix:config['crop_climate_joint_prefix']=True
    for field,data in [('dsn_file',p['dsn'].encode()),('thermal_gate_key_file',bytes.fromhex(p['thermal_key'])),('market_hold_key_file',bytes.fromhex(p['market_key']))]:
        path=run/field;save(path,data,raw=True);config[field]=str(path)
    config_file=run/'operator.private.json';save(config_file,config)
    sys.path.insert(0,str(directory));stop=threading.Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
    with running_database(args,directory,args.run) as (_,admin):
        runtime=loader.load_joint_api_runtime(config_file);server=runtime.service.server()
        with runtime.jobs.connect() as conn:
            assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
        thread=threading.Thread(target=server.run,daemon=True);thread.start();worker=nginx=None
        worker_log=(run/'worker.private.log').open('xb');os.fchmod(worker_log.fileno(),0o600)
        nginx_log=(run/'nginx.private.log').open('xb');os.fchmod(nginx_log.fileno(),0o600)
        try:
            env=dict(os.environ);env['PYTHONPATH']=os.pathsep.join([str(directory),str(ROOT/'backend'),str(ROOT/'backend/tests')])
            worker=subprocess.Popen([sys.executable,'-B','-m','app.deterministic_work','--factory',factory+':worker'],
                env=env,stdin=subprocess.DEVNULL,stdout=worker_log,stderr=subprocess.STDOUT)
            template=(ROOT/'web/nginx.conf').read_text()
            mapping={'/tmp/nginx.pid':str(run/'nginx.pid'),'/etc/nginx/mime.types':str(args.nginx.parents[1]/'conf/mime.types'),
                'listen 8444 ssl;':f'listen 127.0.0.1:{args.web_port};','/run/operator/web/cert.pem':str(cert),
                '/run/operator/web/key.pem':str(key),'/run/operator/web/api-ca.pem':str(cert),'/usr/share/nginx/html':str(args.dist),
                'https://127.0.0.1:8443':f'https://127.0.0.1:{args.api_port}'}
            for name in ('client','proxy','fastcgi','uwsgi','scgi'):mapping['/tmp/'+name+'-temp']=str(run/(name+'-temp'))
            for old,new in mapping.items():assert old in template;template=template.replace(old,new)
            (run/'logs').mkdir(mode=0o700);nginx_config=run/'nginx.conf';save(nginx_config,template.encode(),raw=True)
            nginx=subprocess.Popen([str(args.nginx),'-p',str(run)+'/', '-c',str(nginx_config),'-g','daemon off;'],
                stdin=subprocess.DEVNULL,stdout=nginx_log,stderr=subprocess.STDOUT)
            deadline=time.monotonic()+15
            while not server.started:
                assert thread.is_alive() and worker.poll() is None and nginx.poll() is None and time.monotonic()<deadline;time.sleep(.05)
            ready={'service_pid':os.getpid(),'worker_pid':worker.pid,'frontend':f'http://localhost:{args.web_port}/',
                'backend':f'https://127.0.0.1:{args.api_port}','actual_SCRAM':True,'issued_at':p['issued_at'],'expires_at':p['expires_at'],
                'automatic_consumer':True,'test_checkpoint_pause':False,'prefix_enabled':args.enable_prefix,
                'worker_chunk_budget':args.worker_chunk_budget,'G0_G4':'not_assessed','crop_Runs':0}
            save(run/'ready.private.json',ready)
            save(run/'OPEN-UI.private.txt',('URL: '+ready['frontend']+'\n내부 합성 실행 / 실제 농장 예측·추천 보류\n'
                '내부 시험 연결 → 접근 토큰 → 연결 설정\n'+token+'\n08 성장 연구 3D → 저장 결과 판본: joint 실행 · 계산 상태와 완료 3D\n'
                '검토된 계산 접수 파일: '+str(directory/'requests/normal-user.json')+'\n계산 접수 → 자동 상태/확정 체크포인트 확인 → 같은 저장 결과 3D 열기\n'
                '같은 파일 재접수는 같은 작업을 조회합니다. '+
                ('계산 중 확정 부분 결과3D가 켜진 검증 후보입니다. 실제 농장 예측이 아닙니다.' if args.enable_prefix else '계산 중 식물3D는 아직 없습니다.')+
                '\n유효 종료: '+p['expires_at']+'\n').encode(),raw=True)
            started=time.monotonic()
            while not stop.wait(.25):
                assert thread.is_alive() and worker.poll() is None and nginx.poll() is None
                if time.monotonic()-started>=args.ttl_seconds-5:break
        finally:
            if worker is not None and worker.poll() is None:worker.terminate();worker.wait(timeout=60)
            if nginx is not None and nginx.poll() is None:nginx.terminate();nginx.wait(timeout=15)
            server.should_exit=True;thread.join(30);assert not thread.is_alive()
            worker_log.close();nginx_log.close()
            dump(args,directory,admin,'after-'+args.run)
            save(run/'stopped.private.json',{'service_stopped':True,'worker_exit':worker.returncode if worker else None,
                'database_retained':True,'artifacts_retained':True,'snapshot':'after-'+args.run+'.dump'})


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','serve'])
    parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--pg-bin',type=Path,required=True)
    parser.add_argument('--run',default='live-v1');parser.add_argument('--ttl-seconds',type=int,default=86400)
    parser.add_argument('--api-port',type=int,default=8446);parser.add_argument('--web-port',type=int,default=5174)
    parser.add_argument('--enable-prefix',action='store_true')
    parser.add_argument('--worker-chunk-budget',type=int,choices=range(1,129),default=16)
    parser.add_argument('--nginx',type=Path);parser.add_argument('--dist',type=Path)
    args=parser.parse_args();assert args.directory.is_absolute() and 60<=args.ttl_seconds<=86400
    prepare(args) if args.action=='prepare' else serve(args)
