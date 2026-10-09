from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from functools import wraps
import importlib.util
import json
import gc
import os
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

import pytest

from app import crop_cycle_stream_execution as engine
from app import crop_plant_startup_integration as original
from test_crop_cycle_artifact import PROFILES, NOTICE, program

ROOT=Path(__file__).resolve().parents[2]

_ISOLATED_CHILD = 'OSSF_CROP_FULL_RHS_TEST_CHILD'


def _in_fresh_process(test):
    @wraps(test)
    def run(*args, **kwargs):
        if os.environ.get(_ISOLATED_CHILD) == '1':
            return test(*args, **kwargs)
        request = kwargs['request']
        env = dict(os.environ, **{_ISOLATED_CHILD: '1'})
        child = subprocess.run([sys.executable, '-m', 'pytest', '-q', request.node.nodeid],
            cwd=Path.cwd(), env=env, capture_output=True, timeout=60)
        assert child.returncode == 0, (child.stdout + child.stderr).decode(errors='replace')
    return run



@pytest.fixture(scope='module')
def driver():
    path=ROOT/'research/crop-cycle-full-rhs-reference.py'
    spec=importlib.util.spec_from_file_location('full_rhs_reference',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def digest(rows):
    return sha256(b''.join(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()+b'\n'
        for row in rows)).hexdigest()


def prepare(driver,path,raw=None):
    raw=raw or program('empty-entry')
    return driver.prepare_experiment(path,program=raw,intervals=2,interval_seconds=60,
        profiles=PROFILES,notice_raw=NOTICE,wall_seconds=21600,budget={'max_steps':3,'max_transitions':4})


def expanded(raw):
    raw=deepcopy(raw);first=raw['segments'][0];start=engine.physical._utc(first['start'])
    from datetime import timedelta
    raw['segments']=[]
    for i in range(2):
        row=deepcopy(first);row['start']=engine.physical._stamp(start+timedelta(seconds=60*i))
        row['end']=engine.physical._stamp(start+timedelta(seconds=60*(i+1)));raw['segments'].append(row)
    raw['output_times']=[r['start'] for r in raw['segments']]+[raw['segments'][-1]['end']]
    raw['events']=[e for e in raw['events'] if raw['output_times'][0]<=e['at']<=raw['output_times'][-1]]
    h=raw['solver']['max_step_seconds'];raw['solver']['max_steps']=2*((60+h-1)//h)+len(raw['events'])
    return raw


@pytest.mark.parametrize('name',['empty-entry','full-removal-reentry','positive-tail'])
@_in_fresh_process
def test_retained_writer_and_restart_preserve_all_original_rows_state_and_no_rhs_read(request,driver,tmp_path,name,monkeypatch):
    raw=program(name);before=deepcopy(raw);expected=original.integrate_plant_startup(**expanded(raw),**PROFILES)
    path=tmp_path/'run';prepared=prepare(driver,path,raw);fd=len(os.listdir('/proc/self/fd'))
    paused=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,
        notice_raw=NOTICE,max_chunks=1)
    assert paused['status']=='incomplete' and paused['reason']=='OPERATOR_CHUNK_PAUSE'
    assert paused['artifact_status']=='yielded' and paused['artifact_sha256'] is None
    assert paused['committed_checkpoint']['steps']>0
    final=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert raw==before and final['status']==expected['status']=='completed'
    assert final['steps']==expected['steps'] and final['read_rhs_calls']==0
    assert final['samples_sha256']==digest(expected['samples']) and final['events_sha256']==digest(expected['events'])
    assert final['sample_count']==len(expected['samples']) and final['event_count']==len(expected['events'])
    assert original._state(final['committed_checkpoint']['y'])==expected['samples'][-1]['state']
    assert final['full166day_math_completed'] is False and final['gates']=='not_assessed'
    assert len(os.listdir('/proc/self/fd'))==fd
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('terminal retry calculated'))
    retry=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert retry['artifact_sha256']==final['artifact_sha256'] and retry['actual_rhs_calls']==0


@_in_fresh_process
def test_global_deadline_does_not_reset_on_resume_or_create_terminal_future(request,driver,tmp_path,monkeypatch):
    path=tmp_path/'run';prepared=prepare(driver,path)
    paused=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE,max_chunks=1)
    spec=json.loads((path/'experiment.json').read_bytes())
    monkeypatch.setattr(driver,'utc_now',lambda:datetime.fromisoformat(spec['deadline_at_utc']))
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('expired deadline calculated'))
    expired=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert expired['status']=='incomplete' and expired['reason']=='GLOBAL_WALL_BUDGET'
    assert expired['head_sha256']==paused['head_sha256'] and expired['committed_checkpoint']==paused['committed_checkpoint']
    assert expired['actual_rhs_calls']==0 and expired['artifact_sha256'] is None


@pytest.mark.parametrize('seconds',[0,True,21601,1.5])
@_in_fresh_process
def test_invalid_global_budget_rejects_before_writing_or_rhs(request,driver,tmp_path,seconds):
    path=tmp_path/'rejected'
    with pytest.raises(ValueError):
        driver.prepare_experiment(path,program=program(),intervals=2,interval_seconds=60,
            profiles=PROFILES,notice_raw=NOTICE,wall_seconds=seconds)
    assert not path.exists()


@_in_fresh_process
def test_previous_peak_is_observed_but_does_not_pause_a_small_active_process(request,driver,tmp_path,monkeypatch):
    path=tmp_path/'run';prepared=prepare(driver,path)
    monkeypatch.setattr(driver,'peak_bytes',lambda:1024*1024*1024)
    result=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert result['status']=='completed' and result['process_peak_rss_bytes']==1024*1024*1024


@pytest.mark.parametrize('kind',['wall-budget','code','input'])
@_in_fresh_process
def test_changed_manifest_or_input_is_denied_before_rhs_and_leaves_original_head(request,driver,tmp_path,monkeypatch,kind):
    path=tmp_path/'run';prepared=prepare(driver,path);head=(path/'artifact'/'HEAD').read_bytes()
    expected=prepared['spec_sha256']
    if kind=='input':
        target=path/'inputs'/'root.json';target.chmod(0o600);target.write_bytes(target.read_bytes()+b' ')
    else:
        target=path/'experiment.json';spec=json.loads(target.read_bytes())
        if kind=='code':spec['driver_sha256']='0'*64
        else:
            from datetime import timedelta
            spec['global_wall_seconds']=21601
            spec['deadline_at_utc']=(datetime.fromisoformat(spec['started_at_utc'])+timedelta(seconds=21601)).isoformat()
        raw=json.dumps(spec,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        target.chmod(0o600);target.write_bytes(raw);expected=sha256(raw).hexdigest()
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('changed experiment calculated'))
    with pytest.raises(ValueError):driver.execute(path,expected_spec_sha256=expected,profiles=PROFILES,notice_raw=NOTICE)
    assert (path/'artifact'/'HEAD').read_bytes()==head


@_in_fresh_process
def test_numeric_hold_preserves_original_reason_confirmed_past_and_rows(request,driver,tmp_path):
    raw=program('positive-tail');raw['segments'][0]['removals']['values']['leaf']['value']=1e9
    expected=original.integrate_plant_startup(**expanded(raw),**PROFILES)
    path=tmp_path/'run';prepared=prepare(driver,path,raw)
    result=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert result['status']==expected['status']=='hold' and result['reason'] is None
    assert result['terminal']['hold']==expected['hold'] and result['terminal']['last_confirmed']==expected['last_confirmed']
    assert result['samples_sha256']==digest(expected['samples']) and result['committed_checkpoint'] is None
    assert result['full166day_math_completed'] is False


@_in_fresh_process
def test_exception_after_actual_head_commit_is_restarted_without_new_initial_state(request,driver,tmp_path):
    path=tmp_path/'run';prepared=prepare(driver,path);fd=len(os.listdir('/proc/self/fd'))
    def stop(value):raise RuntimeError('own operator interrupted after committed HEAD')
    with pytest.raises(RuntimeError,match='own operator interrupted'):
        driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE,progress=stop)
    assert len(os.listdir('/proc/self/fd'))==fd
    final=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert final['restored_checkpoint']['steps']==3 and final['restored_checkpoint']['phase']=='step-end'
    assert final['status']=='completed' and len(os.listdir('/proc/self/fd'))==fd
    expected=original.integrate_plant_startup(**expanded(program()),**PROFILES)
    assert final['samples_sha256']==digest(expected['samples'])


@_in_fresh_process
def test_active_resident_budget_keeps_initial_checkpoint_without_rhs_or_future(request,driver,tmp_path,monkeypatch):
    path=tmp_path/'run';prepared=prepare(driver,path);head=(path/'artifact'/'HEAD').read_bytes()
    monkeypatch.setattr(driver,'resident_bytes',lambda:257*1024*1024)
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('resident budget calculated'))
    result=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert result['status']=='incomplete' and result['reason']=='PROCESS_RESIDENT_BUDGET'
    assert result['steps']==result['actual_rhs_calls']==0 and result['artifact_sha256'] is None
    assert result['committed_checkpoint']['phase']=='initial-ready' and (path/'artifact'/'HEAD').read_bytes()==head


@_in_fresh_process
def test_physically_changed_commit_is_denied_before_restarted_rhs(request,driver,tmp_path,monkeypatch):
    path=tmp_path/'run';prepared=prepare(driver,path)
    driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE,max_chunks=1)
    head=(path/'artifact'/'HEAD').read_bytes();value=json.loads(head)
    target=path/'artifact'/(value['latest_commit_sha256']+'.json');target.chmod(0o600)
    target.write_bytes(target.read_bytes()+b' ')
    monkeypatch.setattr(engine.short._Evaluator,'rhs',lambda *a,**k:pytest.fail('changed commit calculated'))
    with pytest.raises(ValueError):driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert (path/'artifact'/'HEAD').read_bytes()==head


@_in_fresh_process
def test_original_resource_rejection_after_commit_recovers_actual_head_and_never_becomes_numeric_hold(request,driver,tmp_path,monkeypatch):
    from app import crop_cycle_artifact as artifact
    path=tmp_path/'run';prepared=prepare(driver,path);advance=artifact.ArtifactWriter.advance
    def interrupted(writer,budget):
        advance(writer,budget);writer.close()
        raise artifact.CycleArtifactRejected('RESOURCE_HOLD: own post-commit interruption')
    with monkeypatch.context() as patch:
        patch.setattr(artifact.ArtifactWriter,'advance',interrupted)
        result=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert result['status']=='incomplete' and result['reason']=='ORIGINAL_STORAGE_BUDGET'
    assert result['steps']==result['committed_checkpoint']['steps']==3 and result['artifact_status']=='yielded'
    assert result['artifact_sha256'] is None
    final=driver.execute(path,expected_spec_sha256=prepared['spec_sha256'],profiles=PROFILES,notice_raw=NOTICE)
    assert final['restored_checkpoint']==result['committed_checkpoint'] and final['status']=='completed'


def test_suite_parent_above_native_budget_still_runs_real_bounded_child(driver,tmp_path,monkeypatch):
    monkeypatch.delenv(_ISOLATED_CHILD, raising=False)
    size = max(0, 270*1024*1024-driver.resident_bytes())
    pressure = bytearray(size)
    try:
        for index in range(0, size, 4096):
            pressure[index] = 1
        assert driver.resident_bytes() > driver.MAX_PROCESS_RESIDENT_BYTES
        node = str(Path(__file__).relative_to(Path.cwd()))+'::test_retained_writer_and_restart_preserve_all_original_rows_state_and_no_rhs_read[empty-entry]'
        request = SimpleNamespace(node=SimpleNamespace(nodeid=node))
        test_retained_writer_and_restart_preserve_all_original_rows_state_and_no_rhs_read(
            request=request,driver=driver,tmp_path=tmp_path,name='empty-entry',monkeypatch=monkeypatch)
    finally:
        pressure.clear()
        gc.collect()
