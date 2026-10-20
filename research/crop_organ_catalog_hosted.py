"""Own and bound a hosted live organ integration; never claim WSL capacity."""
import ctypes
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    with path.open('x') as stream:
        os.fchmod(stream.fileno(),0o400)
        json.dump(value,stream,sort_keys=True,indent=2)


def supervise(directory):
    assert os.environ.get('GITHUB_ACTIONS')=='true','hosted only; preserve protected WSL services'
    evidence=Path(directory).resolve()
    evidence.mkdir(mode=0o700)
    spec=importlib.util.spec_from_file_location('organ_scope',ROOT/'research/owned-research-process-scope.py')
    guard=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    assert ctypes.CDLL(None).prctl(36,1,0,0,0)==0
    scope=guard.OwnedProcessScope()
    before=len(os.listdir('/proc/self/fd'))
    process=None
    started=time.monotonic()
    single=combined=samples=0
    reason=None
    owned_tmp=evidence/'owned-tmp'
    owned_tmp.mkdir(mode=0o700)
    env=dict(os.environ,OSSF_ORGAN_NATIVE_EVIDENCE=str(evidence),TMPDIR=str(owned_tmp),
        OSSF_TEST_PG_SHARED_BUFFERS_MIB='1')
    pins={name:sha256((ROOT/name).read_bytes()).hexdigest() for name in (
        'backend/tests/web_crop_organ_catalog_smoke.py','web/e2e/real-organ-catalog-smoke.mjs',
        'research/crop_organ_catalog_hosted.py')}
    try:
        with (evidence/'case.private.log').open('xb') as log:
            os.fchmod(log.fileno(),0o600)
            process=subprocess.Popen([sys.executable,'-B','-m','pytest',
                'tests/web_crop_organ_catalog_smoke.py','-q','-rf','--maxfail=1',
                '--basetemp',str(evidence/'pytest')],cwd=ROOT/'backend',env=env,
                stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
            while process.poll() is None:
                rss=scope.sample()
                samples+=1
                single=max(single,max(rss.values(),default=0))
                combined=max(combined,sum(rss.values()))
                if single>512*1024**2 or combined>1024**3:
                    reason='RSS_limit'
                elif time.monotonic()-started>600:
                    reason='wall_limit'
                if reason:
                    break
                time.sleep(.25)
    finally:
        scope.signal_owned(signal.SIGTERM)
        if process is not None and process.poll() is None:
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                scope.signal_owned(signal.SIGKILL)
                process.wait(timeout=5)
        deadline=time.monotonic()+10
        while scope.remaining() and time.monotonic()<deadline:
            time.sleep(.1)
        if scope.remaining():
            scope.signal_owned(signal.SIGKILL)
        while True:
            try:
                if os.waitpid(-1,os.WNOHANG)[0]==0:
                    break
            except ChildProcessError:
                break
    remaining=[i._asdict() for i in scope.remaining()]
    if not remaining:
        for path in (evidence/'pytest',owned_tmp):
            if path.exists():
                shutil.rmtree(path)
    temporary_remaining=[p.name for p in (evidence/'pytest',owned_tmp) if p.exists()]
    after=len(os.listdir('/proc/self/fd'))
    unchanged=all(sha256((ROOT/n).read_bytes()).hexdigest()==digest for n,digest in pins.items())
    result={'actual_child_exit':process.returncode if process else None,'reason':reason,
        'wall_seconds':time.monotonic()-started,'single_PID_peak_RSS_bytes':single,
        'combined_peak_RSS_bytes':combined,'RSS_samples':samples,'sample_interval_seconds':.25,
        'owned_non_zombie_remaining':remaining,'FD_before_after':[before,after],
        'owned_temp_or_credentials_remaining':temporary_remaining,
        'source_preserved':unchanged,'source_SHA256':pins,'hosted_only':True,
        'WSL_capacity_accepted':False,'actual_crop_Runs':0,'G0_G4':'not_assessed','U1_accepted':False}
    save(evidence/'resource-organ.json',result)
    if process is not None and process.returncode:
        lines=(evidence/'case.private.log').read_text(errors='replace').splitlines()
        errors=[re.sub(r'[A-Za-z0-9_-]{32,}','[redacted-id]',line)[:500]
            for line in lines if line.startswith('E ') or line.startswith('FAILED ')][-16:]
        save(evidence/'native-failure-summary.json',{'error_lines':errors,
            'private_log_SHA256':sha256((evidence/'case.private.log').read_bytes()).hexdigest()})
    assert process is not None and process.returncode==0 and reason is None and not remaining and not temporary_remaining and before==after and unchanged,result
    native=json.loads((evidence/'native-organ.json').read_bytes())
    assert native['actual_API_DB_browser'] and not native['mock_API_used']
    assert native['HTTPS_server_joined'] and all(n==0 for n in native['query_calls'].values())
    print(json.dumps({'accepted_hosted_live_organ_software_child':True,'WSL_capacity_accepted':False,
        'responses':len(native['responses']),'frames':len(native['browser']['frames']),
        'combined_peak_RSS_bytes':combined,'actual_crop_Runs':0,'G0_G4':'not_assessed'}))


if __name__=='__main__':
    supervise(sys.argv[1])
