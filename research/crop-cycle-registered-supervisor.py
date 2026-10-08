"""Owned synthetic registered calculation controls, never a product CLI worker."""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import fcntl
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'backend'),str(ROOT/'backend/tests')]
VERSION='owned-registered-calculation-supervisor-v1'
SCOPE='owned_synthetic_registered_calculation_only'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


runtime=module('owned_supervised_runtime',ROOT/'research/crop-cycle-registered-runtime.py')
durable=module('owned_supervised_evidence',ROOT/'research/crop-cycle-full-rhs-durable.py')
immutable=durable._immutable
identity=durable._identity


def digest(path):
    path=runtime.operator_config._path(str(path))
    parent=runtime.custody.job_store._open_directory_nofollow(path.parent)
    fd=None
    try:
        runtime.custody._secure(parent,directory=True)
        fd=runtime.custody._file(parent,path.name);before=runtime.custody._secure(fd)
        checksum=sha256();size=0
        while raw:=os.read(fd,65536):checksum.update(raw);size+=len(raw)
        after=runtime.custody._secure(fd)
        if size!=before.st_size or runtime.operator_config._metadata(before)!=runtime.operator_config._metadata(after):
            raise ValueError('original immutable evidence required')
        return checksum.hexdigest()
    finally:
        if fd is not None:os.close(fd)
        os.close(parent)


def read_json(path):
    raw=runtime.private_bytes(path);value=json.loads(raw)
    if durable._canonical(value)!=raw:raise ValueError('original canonical evidence required')
    return raw,value


def sources():
    reference=ROOT/'research/artifacts/crop-cycle-calculation-registered-runtime-reference-20261008.json'
    expected=json.loads(reference.read_bytes())['source_sha256']
    if any(sha256((ROOT/name).read_bytes()).hexdigest()!=value for name,value in expected.items()):
        raise ValueError('accepted runtime sources changed')
    paths=(Path(__file__),ROOT/'research/crop-cycle-full-rhs-durable.py',reference,
           ROOT/'contracts/crop-cycle-calculation-registered-supervisor-control-v1.md')
    return {**expected,**{str(p.relative_to(ROOT)):sha256(p.read_bytes()).hexdigest() for p in paths}}


def directory(path):
    path=Path(path).absolute();fd=runtime.custody.job_store._open_directory_nofollow(path)
    try:runtime.custody._secure(fd,directory=True)
    finally:os.close(fd)
    return path


def configuration(path,expected):
    raw,value=read_json(path)
    if (sha256(raw).hexdigest()!=expected or type(value) is not dict or set(value)!=runtime.FIELDS
        or value['version']!=runtime.VERSION or value['scope']!='owned_synthetic_only'
        or value['code_sha256']!=runtime.CODE_SHA256):raise ValueError('original owned runtime required')
    if any(digest(p)!=checksum for p,checksum in value['static_sha256'].items()):
        raise ValueError('original fixed runtime references required')
    return value


def remaining(manifest):
    wall=(manifest['deadline_ns']-time.time_ns())/1e9
    if manifest['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip():
        wall=min(wall,(manifest['wall_ns']-(time.monotonic_ns()-manifest['started_monotonic_ns']))/1e9)
    return wall


def pg_identity(value):
    if value is None:return None
    if set(value)!={'process','data_directory'}:raise ValueError('explicit owned PG identity required')
    data=directory(value['data_directory'])
    if int((data/'postmaster.pid').read_text().splitlines()[0])!=value['process']['pid']:
        raise ValueError('owned PG directory/PID mismatch')
    if identity(value['process']['pid'])!=value['process']:raise ValueError('owned PG start identity mismatch')
    return value


def initialize(path,*,config,config_sha256,wall_seconds=600,max_steps=40,max_transitions=48,
               primary_RSS_limit_bytes=512*1024*1024,pipeline_RSS_limit_bytes=1024*1024*1024,owned_pg=None):
    started=time.time_ns();monotonic=time.monotonic_ns()
    if type(wall_seconds) is not int or not 1<=wall_seconds<=32400:raise ValueError('bounded original wall budget required')
    for value,maximum in ((max_steps,10000),(max_transitions,4096),
                          (primary_RSS_limit_bytes,512*1024*1024),(pipeline_RSS_limit_bytes,1024*1024*1024)):
        if type(value) is not int or not 1<=value<=maximum:raise ValueError('bounded explicit controls required')
    config=Path(config).absolute();value=configuration(config,config_sha256);pins=sources()
    path=Path(path).absolute();path.mkdir(mode=0o700);directory(path)
    durable_free=shutil.disk_usage(path).free;temporary_free=shutil.disk_usage(tempfile.gettempdir()).free
    if min(durable_free,temporary_free)<2*1024**3:raise ValueError('two GiB in each storage space required')
    memory=next(int(line.split()[1])*1024 for line in Path('/proc/meminfo').read_text().splitlines() if line.startswith('MemAvailable:'))
    manifest={'version':VERSION,'scope':SCOPE,'gates':'not_assessed','started_at_utc':datetime.fromtimestamp(started/1e9,timezone.utc).isoformat(),
        'started_ns':started,'started_monotonic_ns':monotonic,'wall_ns':wall_seconds*10**9,
        'deadline_ns':started+wall_seconds*10**9,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
        'python_version':platform.python_version(),'source_sha256':pins,'config':str(config),'config_sha256':config_sha256,
        'input_root_sha256':value['input']['root_sha256'],'DB_reference_file':value['dsn_file'],
        'budget':{'max_steps':max_steps,'max_transitions':max_transitions},'owned_pg':pg_identity(owned_pg),
        'primary_RSS_limit_bytes':primary_RSS_limit_bytes,'pipeline_RSS_limit_bytes':pipeline_RSS_limit_bytes,
        'log_limit_bytes':1024*1024,'preflight':{'durable_free_bytes':durable_free,'temporary_free_bytes':temporary_free,
        'MemAvailable_bytes':memory,'temporary_directory':tempfile.gettempdir()}}
    checksum=immutable(path/'supervision.json',manifest);durable._sync(path.parent)
    return {'supervision_sha256':checksum,'manifest':manifest}


def verified(path,expected,*,allow_expired=False):
    path=directory(path);raw,value=read_json(path/'supervision.json')
    if (sha256(raw).hexdigest()!=expected or value['version']!=VERSION or value['scope']!=SCOPE
        or value['gates']!='not_assessed' or value['python_version']!=platform.python_version()
        or value['source_sha256']!=sources()):raise ValueError('original supervision and sources required')
    config=configuration(value['config'],value['config_sha256'])
    if config['input']['root_sha256']!=value['input_root_sha256']:raise ValueError('original input required')
    pg_identity(value['owned_pg'])
    if not allow_expired and remaining(value)<=0:raise ValueError('original deadline expired')
    return path,value


def history(path,expected):
    requests=sorted(path.glob('attempt-*.request.json'))
    for number,request_file in enumerate(requests,1):
        prefix='attempt-'+str(number).zfill(4)
        if request_file.name!=prefix+'.request.json':raise ValueError('complete original attempt history required')
        try:
            request_raw,request=read_json(request_file)
            _,receipt=read_json(path/(prefix+'.receipt.json'))
            _,worker=read_json(path/(prefix+'.worker.json'))
            if (request['supervision_sha256']!=expected or receipt['supervision_sha256']!=expected
                or receipt['request_sha256']!=sha256(request_raw).hexdigest() or receipt['worker']!=worker
                or receipt['log_sha256']!=digest(path/(prefix+'.log'))
                or receipt['result_file']!=prefix+'.result.json'):
                raise ValueError()
            if receipt['result_sha256'] is not None and receipt['result_sha256']!=digest(path/receipt['result_file']):raise ValueError()
            if receipt['result_sha256'] is None and (path/receipt['result_file']).exists():raise ValueError()
        except (OSError,KeyError,ValueError):raise ValueError('original exit/log/result evidence required') from None
    if len(requests)>=9999:raise ValueError('attempt limit reached')
    return 'attempt-'+str(len(requests)+1).zfill(4)


def worker_argv(path,prefix,manifest,max_chunks):
    return [sys.executable,str(Path(__file__).resolve()),'--worker','--directory',str(path),
        '--sha256',digest(path/'supervision.json'),'--attempt',prefix,'--max-chunks',str(max_chunks)]


def control(path,prefix,expected):
    target=path/(prefix+'.control.json')
    if not target.exists():return None
    _,value=read_json(target)
    if (set(value)!={'supervision_sha256','action','requested_at_utc'} or value['supervision_sha256']!=expected
        or value['action'] not in ('pause','cancel')):raise ValueError('owned current control required')
    return value['action']


def request_control(path,*,expected_sha256,action):
    if action not in ('pause','cancel'):raise ValueError('explicit pause or cancel required')
    path,_=verified(path,expected_sha256,allow_expired=True)
    workers=sorted(path.glob('attempt-*.worker.json'))
    if not workers:raise ValueError('no owned active worker')
    _,worker=read_json(workers[-1])
    if identity(worker['pid'])!=worker:raise ValueError('original active worker required')
    prefix=workers[-1].name.removesuffix('.worker.json')
    immutable(path/(prefix+'.control.json'),{'supervision_sha256':expected_sha256,'action':action,
        'requested_at_utc':datetime.now(timezone.utc).isoformat()})


def sample(worker,pg):
    processes={}
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            fields=(path/'stat').read_text().rsplit(')',1)[1].split()
            if path.stat().st_uid==os.geteuid():
                processes[int(path.name)]={'parent':int(fields[1]),'start_ticks':int(fields[19]),
                    'RSS_bytes':int(fields[21])*os.sysconf('SC_PAGE_SIZE')}
        except (OSError,ValueError,IndexError):continue
    roots=[worker]
    if pg is not None:pg_identity(pg);roots.append(pg['process'])
    owned={r['pid'] for r in roots if r['pid'] in processes and processes[r['pid']]['start_ticks']==r['start_ticks']}
    while True:
        added={pid for pid,info in processes.items() if info['parent'] in owned}-owned
        if not added:break
        owned.update(added)
    return processes.get(worker['pid'],{}).get('RSS_bytes',0),sum(processes[p]['RSS_bytes'] for p in owned)


def owned_signal(worker,original,signum):
    if worker.poll() is not None:return False
    if identity(worker.pid)!=original:raise ValueError('original owned signal target required')
    os.killpg(worker.pid,signum)
    return True


def stop(worker,original):
    sent=[]
    for signum in (signal.SIGINT,signal.SIGTERM,signal.SIGKILL):
        if owned_signal(worker,original,signum):
            sent.append({'signal':int(signum),'sent_at_utc':datetime.now(timezone.utc).isoformat(),'worker':original})
        try:worker.wait(timeout=10);return sent
        except subprocess.TimeoutExpired:pass
    raise RuntimeError('owned worker did not terminate')


def freeze(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        info=os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1:raise ValueError('owned evidence required')
        os.fchmod(fd,0o400);os.fsync(fd)
    finally:os.close(fd)
    durable._sync(path.parent)


def run(path,*,expected_sha256,max_chunks=1,stop_after_recovery=False):
    if type(max_chunks) is not int or not 1<=max_chunks<=16384:raise ValueError('explicit bounded chunk pause required')
    if type(stop_after_recovery) is not bool:raise ValueError('explicit owned fault switch required')
    path,manifest=verified(path,expected_sha256)
    lock=os.open(path/'worker.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        info=os.fstat(lock)
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o600:
            raise ValueError('owned exclusive lock required')
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('owned registered experiment already executing') from None
        path,manifest=verified(path,expected_sha256);prefix=history(path,expected_sha256)
        argv=['/usr/bin/nice','-n','19',*worker_argv(path,prefix,manifest,max_chunks)]
        if stop_after_recovery:argv.append('--stop-after-recovery')
        request={'version':VERSION,'supervision_sha256':expected_sha256,'requested_at_utc':datetime.now(timezone.utc).isoformat(),
            'argv':argv,'max_chunks':max_chunks,'deadline_ns':manifest['deadline_ns'],
            'stop_after_recovery':stop_after_recovery}
        request_sha=immutable(path/(prefix+'.request.json'),request)
        log_path=path/(prefix+'.log');result_path=path/(prefix+'.result.json')
        reason=None;worker=None;original=None;primary_max=pipeline_max=0;nice=0;signals=[]
        fd=os.open(log_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as log:
            try:
                worker=subprocess.Popen(argv,cwd=ROOT/'backend',stdout=log,stderr=subprocess.STDOUT,
                    pass_fds=(lock,),start_new_session=True)
                original=identity(worker.pid);immutable(path/(prefix+'.worker.json'),original)
                while worker.poll() is None:
                    primary,pipeline=sample(original,manifest['owned_pg'])
                    primary_max=max(primary_max,primary);pipeline_max=max(pipeline_max,pipeline)
                    nice=max(nice,os.getpriority(os.PRIO_PROCESS,worker.pid))
                    action=control(path,prefix,expected_sha256)
                    if action=='cancel':reason='cancel'
                    elif remaining(manifest)<=0:reason='deadline'
                    elif primary>manifest['primary_RSS_limit_bytes']:reason='primary_RSS'
                    elif pipeline>manifest['pipeline_RSS_limit_bytes']:reason='pipeline_RSS'
                    elif os.fstat(log.fileno()).st_size>manifest['log_limit_bytes']:reason='log_limit'
                    if reason is not None:signals.extend(stop(worker,original));break
                    time.sleep(.05)
                worker.wait()
            except BaseException as exc:
                reason='supervisor_'+type(exc).__name__
            finally:
                if worker is not None and worker.poll() is None:signals.extend(stop(worker,original))
                log.flush();os.fsync(log.fileno())
        freeze(log_path)
        result=None;result_sha=None;outcome='held'
        if result_path.exists():
            freeze(result_path);result_sha=digest(result_path)
            try:
                _,result=read_json(result_path)
                if (result['version']!=VERSION or result['supervision_sha256']!=expected_sha256
                    or result['config_sha256']!=manifest['config_sha256'] or result['deadline_ns']!=manifest['deadline_ns']
                    or result['input_root_sha256']!=manifest['input_root_sha256'] or result['gates']!='not_assessed'):
                    raise ValueError()
                if worker.returncode==0 and reason is None:
                    try:verified(path,expected_sha256,allow_expired=True)
                    except Exception:reason='changed_final_supervision'
                    if remaining(manifest)<=0:reason=reason or 'deadline'
                    if reason is None:outcome='recorded'
            except (KeyError,ValueError):reason=reason or 'unverifiable_result'
        if outcome!='recorded':reason=reason or 'worker_failed_or_missing_result'
        receipt={'version':VERSION,'supervision_sha256':expected_sha256,'request_sha256':request_sha,'worker':original,
            'worker_returncode':worker.returncode if worker is not None else None,'worker_nice':nice,'signals':signals,
            'deadline_ns':manifest['deadline_ns'],'outcome':outcome,'reason':reason,'log_sha256':digest(log_path),
            'result_file':result_path.name,'result_sha256':result_sha,'result':result,
            'sampled_primary_RSS_max_bytes':primary_max,'sampled_owned_pipeline_RSS_sum_max_bytes':pipeline_max,
            'RSS_scope':'sampled_owned_tree_sum_shared_pages_may_double_count_not_WSL_total_or_PSS',
            'recorded_at_utc':datetime.now(timezone.utc).isoformat()}
        immutable(path/(prefix+'.receipt.json'),receipt)
        return receipt
    finally:os.close(lock)


def calculation_worker(path,expected,prefix,max_chunks,*,stop_after_recovery=False):
    descriptors=len(os.listdir('/proc/self/fd'))
    path,manifest=verified(path,expected);server,raw=runtime.load_runtime(manifest['config'],manifest['config_sha256'])
    with server.binding.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    rhs,validate=runtime.engine.short._Evaluator.rhs,runtime.artifact._validate_delta
    def forbidden(*a,**k):raise AssertionError('recovery ran RHS/delta QC')
    def current(*,create=False):
        runtime.engine.short._Evaluator.rhs=runtime.artifact._validate_delta=forbidden
        try:
            with server._open('tenant-1',raw,create) as journal:
                return json.loads(journal.inspect()),deepcopy(journal.writer._checkpoint)
        finally:runtime.engine.short._Evaluator.rhs, runtime.artifact._validate_delta=rhs,validate
    progress,restored=current(create=True);calls=0;chunks=0
    runtime.emit({'stage':'recovered','worker':identity(os.getpid()),'checkpoint':restored,
        'progress':progress,'RHS_calls':0,'delta_QC_calls':0})
    if stop_after_recovery:signal.raise_signal(signal.SIGSTOP)
    def measured(*a,**k):
        nonlocal calls
        calls+=1;return rhs(*a,**k)
    reason='OPERATOR_CHUNK_PAUSE'
    while progress['status']=='yielded' and chunks<max_chunks:
        if control(path,prefix,expected)=='pause':reason='OPERATOR_PAUSE';break
        verified(path,expected)
        runtime.engine.short._Evaluator.rhs=measured
        try:progress=json.loads(server.advance('tenant-1',raw,budget=manifest['budget']))
        finally:runtime.engine.short._Evaluator.rhs=rhs
        chunks+=1
        runtime.emit({'stage':'chunk','chunks':chunks,'actual_RHS_calls':calls,'progress':progress})
    if progress['status']!='yielded':reason='TERMINAL_CALCULATION'
    progress,checkpoint=current()
    result={'version':VERSION,'supervision_sha256':expected,'config_sha256':manifest['config_sha256'],
        'deadline_ns':manifest['deadline_ns'],'input_root_sha256':manifest['input_root_sha256'],'reason':reason,
        'progress':progress,'restored_checkpoint':restored,'checkpoint':checkpoint,'actual_RHS_calls':calls,
        'recovery_RHS_calls':0,'chunks':chunks,'gates':'not_assessed','actual_scram_used_password':True,
        'FD_before_after':[descriptors,len(os.listdir('/proc/self/fd'))]}
    assert server.input_resolver.last.reader.closed and not server.input_resolver.last._cache
    assert len(os.listdir('/proc/self/fd'))==descriptors
    immutable(path/(prefix+'.result.json'),result)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--worker',action='store_true');parser.add_argument('--attempt');parser.add_argument('--max-chunks',type=int,default=1)
    parser.add_argument('--stop-after-recovery',action='store_true')
    parser.add_argument('--control',choices=('pause','cancel'));args=parser.parse_args()
    if args.worker:
        if args.attempt is None or not (len(args.attempt)==12 and args.attempt.startswith('attempt-') and args.attempt[8:].isdigit()):
            parser.error('original attempt required')
        calculation_worker(args.directory,args.sha256,args.attempt,args.max_chunks,stop_after_recovery=args.stop_after_recovery)
    elif args.control:request_control(args.directory,expected_sha256=args.sha256,action=args.control)
    else:
        receipt=run(args.directory,expected_sha256=args.sha256,max_chunks=args.max_chunks,stop_after_recovery=args.stop_after_recovery)
        print(json.dumps({k:receipt[k] for k in ('outcome','reason','worker_returncode','deadline_ns')}),flush=True)
        if receipt['outcome']!='recorded':raise SystemExit(1)


if __name__=='__main__':main()
