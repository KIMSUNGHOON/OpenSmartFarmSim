"""Real child execution, durable exit evidence and original checkpoint recovery."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime,timedelta
from copy import deepcopy
import signal

import pytest

ROOT=Path(__file__).resolve().parents[2]
SCRIPT=ROOT/'research/crop-cycle-full-rhs-durable.py'


@pytest.fixture
def supervisor():
    spec=importlib.util.spec_from_file_location('durable_full_rhs',SCRIPT)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_small_real_child_pause_resume_and_terminal_retry_preserve_spec_deadline_and_original_rows(supervisor,tmp_path):
    path=tmp_path/'durable';prepared=supervisor.initialize(path,intervals=4)
    def run(**kwargs):return supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'],**kwargs)
    before=len(os.listdir('/proc/self/fd'))
    first=run(max_chunks=1)
    assert first['worker_returncode']==0 and first['result']['reason']=='OPERATOR_CHUNK_PAUSE'
    spec=(path/'run/experiment.json').read_bytes();manifest=(path/'supervision.json').read_bytes()
    final=run()
    assert final['worker_returncode']==0 and final['result']['status']=='completed'
    assert final['result']['restored_checkpoint']==first['result']['committed_checkpoint']
    assert final['result']['sample_count']==5 and final['result']['read_rhs_calls']==0
    assert final['result']['full166day_math_completed'] is False and final['result']['gates']=='not_assessed'
    again=run()
    assert again['result']['artifact_sha256']==final['result']['artifact_sha256']
    assert again['result']['actual_rhs_calls']==0 and again['result']['read_rhs_calls']==0
    assert (path/'run/experiment.json').read_bytes()==spec and (path/'supervision.json').read_bytes()==manifest
    for attempt in (first,final,again):
        assert attempt['spec_sha256']==sha256(spec).hexdigest()
        assert attempt['result']['global_deadline_at_utc']==json.loads(spec)['deadline_at_utc']
        assert not Path('/proc/'+str(attempt['worker']['pid'])).exists()
        assert (path/attempt['result_file']).stat().st_mode&0o777==0o400
    assert len(os.listdir('/proc/self/fd'))==before
    assert (path/'attempt-0001.receipt.json').stat().st_mode&0o777==0o400


def test_changed_supervision_is_rejected_before_worker_or_state_change(supervisor,tmp_path):
    path=tmp_path/'durable';prepared=supervisor.initialize(path,intervals=4)
    head=(path/'run/artifact/HEAD').read_bytes()
    raw=json.loads((path/'supervision.json').read_bytes());raw['intervals']=5
    target=path/'supervision.json';target.chmod(0o600)
    target.write_bytes(json.dumps(raw,sort_keys=True,separators=(',',':')).encode());target.chmod(0o400)
    with pytest.raises(ValueError):supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'])
    assert (path/'run/artifact/HEAD').read_bytes()==head and not list(path.glob('attempt-*'))


def test_recanonicalized_original_deadline_cannot_be_extended_on_resume(supervisor,tmp_path):
    path=tmp_path/'durable';prepared=supervisor.initialize(path,intervals=4)
    supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'],max_chunks=1)
    target=path/'run/experiment.json';value=json.loads(target.read_bytes())
    for key in ('started_at_utc','deadline_at_utc'):
        value[key]=(datetime.fromisoformat(value[key])+timedelta(hours=1)).isoformat()
    target.chmod(0o600);target.write_bytes(json.dumps(value,sort_keys=True,separators=(',',':')).encode());target.chmod(0o400)
    head=(path/'run/artifact/HEAD').read_bytes()
    with pytest.raises(ValueError):supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'])
    assert (path/'run/artifact/HEAD').read_bytes()==head
    assert len(list(path.glob('attempt-*.request.json')))==1


def test_previous_result_tamper_rejects_before_new_worker_and_keeps_prior_receipt(supervisor,tmp_path):
    path=tmp_path/'durable';prepared=supervisor.initialize(path,intervals=4)
    first=supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'],max_chunks=1)
    receipt=(path/'attempt-0001.receipt.json').read_bytes();target=path/first['result_file']
    target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ');target.chmod(0o400)
    with pytest.raises(ValueError):supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'])
    assert (path/'attempt-0001.receipt.json').read_bytes()==receipt
    assert len(list(path.glob('attempt-*.request.json')))==1


def test_actual_killed_worker_has_durable_negative_exit_and_resumes_exact_original_checkpoint(supervisor,tmp_path):
    path=tmp_path/'killed';prepared=supervisor.initialize(path,intervals=20)
    args=[sys.executable,str(SCRIPT),'--directory',str(path),'--supervision-sha256',prepared['supervision_sha256']]
    parent=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    killed_pid=None
    try:
        deadline=time.monotonic()+30;worker_file=path/'attempt-0001.worker.json';log=path/'attempt-0001.log'
        while not (worker_file.exists() and log.exists() and 'actual_RHS' in log.read_text()):
            assert parent.poll() is None and time.monotonic()<deadline
            time.sleep(.01)
        worker=json.loads(worker_file.read_bytes());assert supervisor._identity(worker['pid'])==worker
        with pytest.raises(RuntimeError,match='already executing'):
            supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'])
        os.kill(worker['pid'],signal.SIGKILL);killed_pid=worker['pid']
        stdout,stderr=parent.communicate(timeout=30)
        assert parent.returncode==1,(stdout+stderr).decode(errors='replace')
    finally:
        if parent.poll() is None:
            if worker_file.exists():
                owned=json.loads(worker_file.read_bytes())
                try:
                    if supervisor._identity(owned['pid'])==owned:os.kill(owned['pid'],signal.SIGKILL)
                except FileNotFoundError:pass
            parent.terminate()
        parent.communicate(timeout=30)
    failed_raw=(path/'attempt-0001.receipt.json').read_bytes();failed=json.loads(failed_raw)
    assert failed['worker_returncode']==-signal.SIGKILL and failed['outcome']=='worker_failed'
    assert failed['result'] is None and failed['result_sha256'] is None
    assert not Path('/proc/'+str(killed_pid)).exists()
    spec_raw=(path/'run/experiment.json').read_bytes();spec=json.loads(spec_raw);driver=supervisor._driver()
    reference=driver.load_module('owned_durable_control',ROOT/'research/crop-cycle-stream-execution-reference.py')
    profiles=reference.profiles();notice=(ROOT/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt').read_bytes()
    with driver.inputs.open_input_packet(path/'run/inputs',spec['input_root_sha256'],**profiles) as source:
        context=driver.engine.prepare_context(source,**profiles)
        with driver.artifact.open_writer(path/'run/artifact',driver.current_head(path/'run'),context,notice_raw=notice) as writer:
            committed=deepcopy(writer._checkpoint)
    final=supervisor.run(path,expected_supervision_sha256=prepared['supervision_sha256'])
    assert final['result']['restored_checkpoint']==committed
    assert final['result']['status']=='completed' and final['result']['sample_count']==21
    control_path=tmp_path/'continuous';control=supervisor.initialize(control_path,intervals=20)
    baseline=supervisor.run(control_path,expected_supervision_sha256=control['supervision_sha256'])['result']
    for key in ('steps','planned_steps','sample_count','event_count','samples_sha256','events_sha256'):
        assert final['result'][key]==baseline[key],key
    assert final['result']['committed_checkpoint']['y']==baseline['committed_checkpoint']['y']
    assert final['result']['global_deadline_at_utc']==spec['deadline_at_utc']
    assert (path/'run/experiment.json').read_bytes()==spec_raw
    assert (path/'attempt-0001.receipt.json').read_bytes()==failed_raw
