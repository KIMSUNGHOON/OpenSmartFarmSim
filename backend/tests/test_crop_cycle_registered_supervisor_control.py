"""Actual Python process controls; these tests perform no DB or crop calculation."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

import pytest

from test_crop_cycle_registered_runtime_config import private_config, runtime

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-supervisor.py'


@pytest.fixture
def supervisor():
    spec=importlib.util.spec_from_file_location('registered_control',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


@pytest.fixture
def configured(supervisor,private_config,tmp_path,monkeypatch):
    config,value=private_config
    value['input']['root_sha256']='0'*64
    supervisor.immutable(config,value)
    digest=sha256(config.read_bytes()).hexdigest()
    worker=tmp_path/'controlled-worker.py'
    def prepare(mode='normal',**limits):
        worker.write_text('''import importlib.util,json,os,signal,sys,time
from pathlib import Path
s=importlib.util.spec_from_file_location('control',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
p=Path(sys.argv[2]);prefix=sys.argv[3];_,v=m.read_json(p/'supervision.json')
print(json.dumps({'stage':'ready','pid':os.getpid()}),flush=True)
MODE='''+repr(mode)+'''
if MODE=='rss': allocation=bytearray(32*1024*1024)
if MODE=='log': print('x'*(2*1024*1024),flush=True)
if MODE in ('wait','rss','log'):
 while True: time.sleep(.02)
if MODE=='pause':
 while not (p/(prefix+'.control.json')).exists(): time.sleep(.02)
r={'version':m.VERSION,'supervision_sha256':m.digest(p/'supervision.json'),'config_sha256':v['config_sha256'],
 'deadline_ns':v['deadline_ns'],'input_root_sha256':v['input_root_sha256'],'reason':'OPERATOR_CHUNK_PAUSE',
 'progress':{'status':'yielded'},'restored_checkpoint':{'owned_control_only':True},'checkpoint':{'owned_control_only':True},
 'actual_RHS_calls':0,'recovery_RHS_calls':0,'chunks':1,'gates':'not_assessed'}
m.immutable(p/(prefix+'.result.json'),r)
''')
        monkeypatch.setattr(supervisor,'sources',lambda:{str(worker):sha256(worker.read_bytes()).hexdigest()})
        monkeypatch.setattr(supervisor,'worker_argv',lambda path,prefix,manifest,max_chunks:
            [sys.executable,str(worker),str(SCRIPT),str(path),prefix])
        path=tmp_path/'supervised'
        prepared=supervisor.initialize(path,config=config,config_sha256=digest,wall_seconds=limits.pop('wall_seconds',30),**limits)
        return path,prepared['supervision_sha256']
    yield prepare
    for record in tmp_path.glob('supervised/attempt-*.worker.json'):
        worker=json.loads(record.read_bytes())
        try:
            if supervisor.identity(worker['pid'])==worker:os.killpg(worker['pid'],signal.SIGKILL)
        except (OSError,ValueError):pass


def wait_worker(path):
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        files=list(path.glob('attempt-*.worker.json'))
        if files:
            worker=json.loads(sorted(files)[-1].read_bytes())
            log=path/(sorted(files)[-1].name.removesuffix('.worker.json')+'.log')
            try:
                fields=Path('/proc',str(worker['pid']),'stat').read_text().rsplit(')',1)[1].split()
                live=fields[0]!='Z' and int(fields[19])==worker['start_ticks']
            except (OSError,ValueError):live=False
            if live and log.exists() and b'"ready"' in log.read_bytes(): return worker
        time.sleep(.01)
    pytest.fail('owned worker did not become ready')


def run_background(supervisor,path,digest):
    result=[]
    def run():
        try:result.append(supervisor.run(path,expected_sha256=digest,max_chunks=1))
        except BaseException as exc:result.append(exc)
    thread=threading.Thread(target=run);thread.start()
    return thread,result


def test_original_deadline_logs_and_exit_survive_two_explicit_attempts(supervisor,configured):
    path,digest=configured();before=len(os.listdir('/proc/self/fd'))
    original=(path/'supervision.json').read_bytes()
    first=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    second=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    for receipt in (first,second):
        assert receipt['worker_returncode']==0 and receipt['outcome']=='recorded'
        assert receipt['supervision_sha256']==digest and receipt['deadline_ns']==json.loads(original)['deadline_ns']
        assert not Path('/proc',str(receipt['worker']['pid'])).exists()
        assert receipt['sampled_primary_RSS_max_bytes']>0
        assert receipt['worker_nice']==19
    assert (path/'supervision.json').read_bytes()==original
    assert len(os.listdir('/proc/self/fd'))==before
    assert (path/'attempt-0001.receipt.json').stat().st_mode&0o777==0o400


@pytest.mark.parametrize('fault',['spec','source','config','log','result','missing-exit'])
def test_changed_original_evidence_denies_dispatch(supervisor,configured,fault):
    path,digest=configured();supervisor.run(path,expected_sha256=digest,max_chunks=1)
    _,manifest=supervisor.read_json(path/'supervision.json')
    target={'spec':path/'supervision.json','source':Path(next(iter(manifest['source_sha256']))),
        'config':Path(manifest['config']),'log':path/'attempt-0001.log',
        'result':path/'attempt-0001.result.json','missing-exit':path/'attempt-0001.receipt.json'}[fault]
    if fault=='missing-exit':target.unlink()
    else:target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
    with pytest.raises(ValueError):supervisor.run(path,expected_sha256=digest,max_chunks=1)
    assert not (path/'attempt-0002.request.json').exists()


def test_lock_refuses_concurrent_attempt_and_cancel_records_actual_exit(supervisor,configured):
    path,digest=configured('wait');thread,result=run_background(supervisor,path,digest)
    worker=wait_worker(path)
    try:
        with pytest.raises(RuntimeError):supervisor.run(path,expected_sha256=digest,max_chunks=1)
        supervisor.request_control(path,expected_sha256=digest,action='cancel')
    finally:
        thread.join(15)
        if thread.is_alive():os.kill(worker['pid'],signal.SIGKILL);thread.join(10)
    assert not thread.is_alive() and len(result)==1 and isinstance(result[0],dict)
    assert result[0]['reason']=='cancel' and result[0]['worker_returncode']!=0
    assert result[0]['outcome']=='held' and result[0]['result_sha256'] is None
    assert result[0]['signals'][0]['signal']==signal.SIGINT
    assert not Path('/proc',str(worker['pid'])).exists()


@pytest.mark.parametrize('mode,limits,reason',[('wait',{'wall_seconds':1},'deadline'),
    ('rss',{'primary_RSS_limit_bytes':16*1024*1024},'primary_RSS'),
    ('rss',{'pipeline_RSS_limit_bytes':16*1024*1024},'pipeline_RSS')])
def test_actual_wall_or_RSS_limit_stops_owned_child(supervisor,configured,mode,limits,reason):
    path,digest=configured(mode,**limits)
    receipt=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    assert receipt['outcome']=='held' and receipt['reason']==reason and receipt['worker_returncode']!=0
    assert not Path('/proc',str(receipt['worker']['pid'])).exists()
    if reason=='deadline':
        with pytest.raises(ValueError):supervisor.run(path,expected_sha256=digest,max_chunks=1)
        assert not (path/'attempt-0002.request.json').exists()


def test_pause_is_cooperative_and_SIGKILL_negative_exit_can_be_explicitly_resumed(supervisor,configured):
    path,digest=configured('pause');thread,result=run_background(supervisor,path,digest)
    worker=wait_worker(path)
    supervisor.request_control(path,expected_sha256=digest,action='pause');thread.join(15)
    assert not thread.is_alive() and result[0]['outcome']=='recorded'
    thread,result=run_background(supervisor,path,digest);worker=wait_worker(path)
    os.kill(worker['pid'],signal.SIGKILL);thread.join(15)
    assert not thread.is_alive() and result[0]['worker_returncode']==-9 and result[0]['outcome']=='held'
    original=(path/'supervision.json').read_bytes()
    thread,result=run_background(supervisor,path,digest);wait_worker(path)
    supervisor.request_control(path,expected_sha256=digest,action='pause');thread.join(15)
    assert not thread.is_alive() and result[0]['outcome']=='recorded'
    assert (path/'supervision.json').read_bytes()==original


def test_oversized_log_preserves_original_exit_and_hash_before_hold(supervisor,configured):
    path,digest=configured('log')
    receipt=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    assert receipt['outcome']=='held' and receipt['reason']=='log_limit' and receipt['worker_returncode']!=0
    assert (path/'attempt-0001.log').stat().st_size>1024*1024
    assert receipt['log_sha256']==sha256((path/'attempt-0001.log').read_bytes()).hexdigest()
    assert not Path('/proc',str(receipt['worker']['pid'])).exists()


@pytest.mark.parametrize('fault',['config','deadline'])
def test_final_reference_or_deadline_change_holds_without_losing_original_zero_exit(supervisor,configured,monkeypatch,fault):
    path,digest=configured();_,manifest=supervisor.read_json(path/'supervision.json')
    original_freeze=supervisor.freeze
    def freeze_then_change(target):
        original_freeze(target)
        if target.name.endswith('.log'):
            if fault=='config':
                config=Path(manifest['config']);config.chmod(0o600);config.write_bytes(config.read_bytes()+b' ');config.chmod(0o400)
            else:monkeypatch.setattr(supervisor,'remaining',lambda _: -1)
    monkeypatch.setattr(supervisor,'freeze',freeze_then_change)
    receipt=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    assert receipt['outcome']=='held' and receipt['worker_returncode']==0
    assert receipt['reason']==('changed_final_supervision' if fault=='config' else 'deadline')
    assert receipt['result_sha256'] is not None and (path/'attempt-0001.receipt.json').exists()
