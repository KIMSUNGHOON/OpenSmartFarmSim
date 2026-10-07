"""Persist original RHS worker exit evidence without changing its calculation."""
from argparse import ArgumentParser
from datetime import datetime,timezone
import fcntl
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/'research/crop-cycle-full-rhs-reference.py'
VERSION='crop-cycle-full-rhs-durable-v2'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def _canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _driver():
    spec=importlib.util.spec_from_file_location('original_full_rhs_durable_worker',ORIGINAL)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def _sources():
    paths=dict(_driver().dependencies())
    for path in (Path(__file__),ORIGINAL,ROOT/'research/crop-cycle-stream-execution-reference.py',
                 ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt'):
        paths[str(path.relative_to(ROOT))]=sha256(path.read_bytes()).hexdigest()
    if paths[str(Path(__file__).relative_to(ROOT))]!=CODE_SHA256:raise ValueError('supervisor source changed')
    return paths


def _sync(path):
    fd=os.open(path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
    try:os.fsync(fd)
    finally:os.close(fd)


def _immutable(path,value):
    raw=_canonical(value)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as handle:
        handle.write(raw);handle.flush();os.fchmod(handle.fileno(),0o400);os.fsync(handle.fileno())
    _sync(path.parent)
    return sha256(raw).hexdigest()


def _read(path):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as handle:
        info=os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or info.st_nlink!=1 or stat.S_IMODE(info.st_mode)!=0o400:
            raise ValueError('owned immutable evidence required')
        raw=handle.read(1024*1024+1)
    if len(raw)>1024*1024:raise ValueError('bounded evidence required')
    value=json.loads(raw)
    if _canonical(value)!=raw:raise ValueError('canonical evidence required')
    return raw,value


def initialize(path,*,intervals=47808):
    if type(intervals) is not int or not 1<=intervals<=47808:raise ValueError('bounded explicit intervals required')
    path=Path(path);sources=_sources();path.mkdir(mode=0o700)
    intent={'version':VERSION,'requested_at_utc':datetime.now(timezone.utc).isoformat(),
        'intervals':intervals,'source_sha256':sources,'independent_new_experiment':True}
    _immutable(path/'preparation.request.json',intent)
    driver=_driver();reference=driver.load_module('owned_durable_input',ROOT/'research/crop-cycle-stream-execution-reference.py')
    prepared=driver.prepare_experiment(path/'run',program=reference.long_program(),intervals=intervals,
        interval_seconds=300,profiles=reference.profiles(),notice_raw=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes())
    for directory in (path/'run/inputs',path/'run/artifact',path/'run'):_sync(directory)
    value={'version':VERSION,'scope':'own_synthetic_numeric_experiment_only','gates':'not_assessed',
        'initialized_at_utc':datetime.now(timezone.utc).isoformat(),'intervals':intervals,
        'python_version':platform.python_version(),'source_sha256':sources,'independent_new_experiment':True,
        'spec_sha256':prepared['spec_sha256'],'input_root_sha256':prepared['input_root_sha256'],
        'deadline_at_utc':prepared['spec']['deadline_at_utc']}
    digest=_immutable(path/'supervision.json',value);_sync(path.parent)
    return {'supervision_sha256':digest,'manifest':value}


def _identity(pid):
    tail=Path('/proc/'+str(pid)+'/stat').read_text().rsplit(')',1)[1].split()
    return {'pid':pid,'start_ticks':int(tail[19]),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip()}


def run(path,*,expected_supervision_sha256,max_chunks=None):
    path=Path(path).absolute();info=path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)!=0o700:
        raise ValueError('owned private experiment directory required')
    raw,manifest=_read(path/'supervision.json')
    if (sha256(raw).hexdigest()!=expected_supervision_sha256 or manifest['version']!=VERSION
        or manifest['source_sha256']!=_sources() or manifest['python_version']!=platform.python_version()
        or manifest['scope']!='own_synthetic_numeric_experiment_only' or manifest['gates']!='not_assessed'):
        raise ValueError('original supervision required')
    if max_chunks is not None and (type(max_chunks) is not int or not 1<=max_chunks<=16384):
        raise ValueError('bounded explicit chunk pause required')
    lock=os.open(path/'worker.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('owned experiment already executing') from None
        attempts=list(path.glob('attempt-*.request.json'));number=1+max((int(p.name.split('.')[0].split('-')[1]) for p in attempts),default=0)
        if number>9999:raise ValueError('attempt limit reached')
        prefix='attempt-'+str(number).zfill(4);result_path=path/(prefix+'.result.json')
        argv=[sys.executable,str(ORIGINAL)]
        spec_raw,spec=_read(path/'run/experiment.json');expected_spec=manifest['spec_sha256']
        if (sha256(spec_raw).hexdigest()!=expected_spec or spec['intervals']!=manifest['intervals']
            or spec['deadline_at_utc']!=manifest['deadline_at_utc'] or spec['input_root_sha256']!=manifest['input_root_sha256']):
            raise ValueError('original interval plan and deadline required')
        for previous in path.glob('attempt-*.receipt.json'):
            _,saved=_read(previous)
            if saved['result_sha256'] is not None:
                name=previous.name.removesuffix('.receipt.json')+'.result.json'
                if saved['result_file']!=name:raise ValueError('original result filename required')
                previous_raw,_=_read(path/name)
                if sha256(previous_raw).hexdigest()!=saved['result_sha256']:raise ValueError('previous result changed')
        argv+=['--resume-run',str(path/'run'),'--spec-sha256',expected_spec]
        argv+=['--output',str(result_path)]
        if max_chunks is not None:argv+=['--max-chunks',str(max_chunks)]
        request={'version':VERSION,'supervision_sha256':expected_supervision_sha256,
            'requested_at_utc':datetime.now(timezone.utc).isoformat(),'argv':argv,'spec_sha256_at_dispatch':expected_spec}
        request_sha=_immutable(path/(prefix+'.request.json'),request)
        log_path=path/(prefix+'.log');log_fd=os.open(log_path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        worker=None
        with os.fdopen(log_fd,'wb') as log:
            try:
                worker=subprocess.Popen(argv,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,pass_fds=(lock,))
                identity=_identity(worker.pid);_immutable(path/(prefix+'.worker.json'),identity)
                while line:=worker.stdout.readline(65537):
                    if len(line)>65536:raise ValueError('worker log line limit exceeded')
                    log.write(line);log.flush();os.fsync(log.fileno())
                returncode=worker.wait()
            finally:
                if worker is not None:
                    if worker.poll() is None:
                        worker.terminate()
                        try:worker.wait(timeout=10)
                        except subprocess.TimeoutExpired:worker.kill();worker.wait()
                    worker.stdout.close()
        log_path.chmod(0o400);_sync(path)
        result=None;result_sha=None;outcome='worker_failed'
        if returncode==0 and result_path.exists():
            try:
                result_raw,result=_read(result_path);current_spec_raw,_=_read(path/'run/experiment.json')
                result_sha=sha256(result_raw).hexdigest()
                if (sha256(current_spec_raw).hexdigest()!=expected_spec or result['spec_sha256']!=expected_spec
                    or result['input_root_sha256']!=spec['input_root_sha256']
                    or result['driver_sha256']!=manifest['source_sha256'][str(ORIGINAL.relative_to(ROOT))]
                    or result['global_deadline_at_utc']!=spec['deadline_at_utc'] or result['gates']!='not_assessed'):
                    raise ValueError('original worker result required')
                outcome='recorded'
            except (ValueError,KeyError,OSError):result=None;outcome='unverifiable_result'
        receipt={'version':VERSION,'supervision_sha256':expected_supervision_sha256,'request_sha256':request_sha,
            'worker':identity,'worker_returncode':returncode,'outcome':outcome,'spec_sha256':expected_spec,
            'log_sha256':sha256(log_path.read_bytes()).hexdigest(),'result_file':result_path.name,
            'result_sha256':result_sha,'result':result,'recorded_at_utc':datetime.now(timezone.utc).isoformat()}
        _immutable(path/(prefix+'.receipt.json'),receipt)
        return receipt
    finally:os.close(lock)


def main():
    parser=ArgumentParser(description=__doc__);parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--initialize',action='store_true');parser.add_argument('--intervals',type=int,default=47808)
    parser.add_argument('--supervision-sha256');parser.add_argument('--max-chunks',type=int);args=parser.parse_args()
    if args.initialize:
        if args.supervision_sha256 or args.max_chunks is not None:parser.error('initialization does not execute RHS')
        value=initialize(args.directory,intervals=args.intervals)
        print(json.dumps({'version':VERSION,'supervision_sha256':value['supervision_sha256'],'gates':'not_assessed'}),flush=True)
    else:
        if not args.supervision_sha256:parser.error('original supervision SHA required')
        receipt=run(args.directory,expected_supervision_sha256=args.supervision_sha256,max_chunks=args.max_chunks)
        print(json.dumps({'version':VERSION,'worker_returncode':receipt['worker_returncode'],'outcome':receipt['outcome'],
            'spec_sha256':receipt['spec_sha256'],'result_sha256':receipt['result_sha256']}),flush=True)
        if receipt['outcome']!='recorded':raise SystemExit(1)


if __name__=='__main__':main()
