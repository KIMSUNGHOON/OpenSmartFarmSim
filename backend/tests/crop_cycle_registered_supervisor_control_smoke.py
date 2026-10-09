"""Manual owned SCRAM bridge for durable fresh workers and original deadline."""
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import threading
from time import monotonic,sleep

import pytest

from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from app.thermal_run_store import _canonical
from crop_cycle_registered_runtime_smoke import (module as runtime_module,checkpoint,files,rewrite,
    server_setup,bound_setup,login_scope,original_login_scope,authoring,farm_setup,login_database,
    audit_registration,save,tree,counts,DB_KEY,POLICY)


def supervisor_module():
    runtime=runtime_module()
    import importlib.util
    path=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-supervisor.py'
    spec=importlib.util.spec_from_file_location('native_registered_control',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return runtime,value


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_registered_supervisor_actual_SCRAM_initialization_kill_resume_and_denial(
        server_setup,audit_registration,tmp_path,monkeypatch):
    original,raw,_,principal,_=server_setup
    principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    runtime,supervisor=supervisor_module();source=original.input_resolver.directory;source_before=tree(source)
    config,config_sha=runtime.export_runtime(original,raw,tmp_path/'private-runtime')
    document=json.loads(config.read_bytes())
    pg_files=list(Path(os.environ['TMPDIR']).glob('ossf-login-pg-*/data/postmaster.pid'))
    assert len(pg_files)==1
    pg={'process':supervisor.identity(int(pg_files[0].read_text().splitlines()[0])),
        'data_directory':str(pg_files[0].parent)}
    path=tmp_path/'supervised'
    prepared=supervisor.initialize(path,config=config,config_sha256=config_sha,max_steps=20,max_transitions=24,
        wall_seconds=500,owned_pg=pg)
    digest=prepared['supervision_sha256'];manifest_raw=(path/'supervision.json').read_bytes()
    server,request=runtime.load_runtime(config,config_sha);before=counts(server.binding)
    descriptors=len(os.listdir('/proc/self/fd'))
    first=supervisor.run(path,expected_sha256=digest,max_chunks=2)
    assert first['outcome']=='recorded' and first['worker_returncode']==0
    assert first['result']['restored_checkpoint']['steps']==0 and first['result']['progress']['steps']==40
    second=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    assert second['outcome']=='recorded' and second['result']['restored_checkpoint']==first['result']['checkpoint']
    assert second['result']['progress']['steps']==60
    history=files(server.directory)
    def stopped_attempt(number,action):
        result=[]
        def run():
            try:result.append(supervisor.run(path,expected_sha256=digest,max_chunks=1,stop_after_recovery=True))
            except BaseException as exc:result.append(exc)
        thread=threading.Thread(target=run);thread.start();worker=None
        try:
            deadline=monotonic()+30
            while monotonic()<deadline:
                target=path/('attempt-'+str(number).zfill(4)+'.worker.json')
                if target.exists():
                    worker=json.loads(target.read_bytes())
                    fields=Path('/proc',str(worker['pid']),'stat').read_text().rsplit(')',1)[1].split()
                    if fields[0]=='T':break
                sleep(.02)
            else:pytest.fail('owned native worker did not stop after recovery')
            assert supervisor.identity(worker['pid'])==worker
            if action=='kill':os.kill(worker['pid'],signal.SIGKILL)
            else:
                supervisor.request_control(path,expected_sha256=digest,action=action)
                if action=='pause':os.kill(worker['pid'],signal.SIGCONT)
            thread.join(35)
        finally:
            if thread.is_alive() and worker is not None:
                if supervisor.identity(worker['pid'])==worker:os.killpg(worker['pid'],signal.SIGKILL)
                thread.join(10)
        assert not thread.is_alive() and len(result)==1 and isinstance(result[0],dict)
        return result[0]
    killed=stopped_attempt(3,'kill')
    assert killed['worker_returncode']==-9 and killed['outcome']=='held' and killed['result_sha256'] is None
    assert files(server.directory)==history
    resumed=supervisor.run(path,expected_sha256=digest,max_chunks=1)
    assert resumed['outcome']=='recorded' and resumed['result']['restored_checkpoint']==second['result']['checkpoint']
    assert resumed['result']['progress']['steps']==80
    control_root=tmp_path/'continuous-control';control_root.mkdir(mode=0o700)
    control=runtime.custody.CalculationServerCustody(server.binding,control_root,
        input_resolver=runtime.Resolver(document['input'],document['resolver_version']),integrity_key=server.integrity_key)
    for receipt in (first,second,resumed):
        for _ in range(receipt['result']['chunks']):control.advance('tenant-1',raw,budget=prepared['manifest']['budget'])
        assert checkpoint(control,raw,monkeypatch)[1]==receipt['result']['checkpoint']
        assert receipt['result']['recovery_RHS_calls']==0 and receipt['result']['actual_RHS_calls']>0
        assert receipt['result']['actual_scram_used_password'] and receipt['worker_nice']==19
        assert receipt['result']['FD_before_after'][0]==receipt['result']['FD_before_after'][1]
        assert receipt['sampled_owned_pipeline_RSS_sum_max_bytes']>receipt['sampled_primary_RSS_max_bytes']
    def rows(target):
        with target._open('tenant-1',raw,False) as journal:
            head,_=journal.writer._head()
            _,_,_,index,total=journal.writer._load_prefix(journal.context,journal.notice,head)
            return {kind:[row for part in index[kind] for row in journal.writer._records(
                [{k:v for k,v in part.items() if k!='start'}])[0]] for kind in ('samples','events')},total
    selected,total=rows(server);expected,_=rows(control);assert selected==expected
    with pytest.raises(runtime.custody.CalculationCustodyHold):
        CalculationCycleCropResultStore(server,integrity_key=DB_KEY).put('tenant-1',raw)
    history=files(server.directory);denials=[]
    paused=stopped_attempt(5,'pause')
    assert paused['outcome']=='recorded' and paused['worker_returncode']==0
    assert paused['result']['reason']=='OPERATOR_PAUSE' and paused['result']['actual_RHS_calls']==0
    assert paused['result']['checkpoint']==resumed['result']['checkpoint']
    cancelled=stopped_attempt(6,'cancel')
    assert cancelled['outcome']=='held' and cancelled['reason']=='cancel' and cancelled['worker_returncode']==-9
    assert [s['signal'] for s in cancelled['signals']]==[signal.SIGINT,signal.SIGTERM,signal.SIGKILL]
    assert files(server.directory)==history
    for name in ('rights','principal'):
        target=Path(document[name+'_file']);saved=target.read_bytes();value=json.loads(saved)
        if name=='rights':value['allowed']=False
        else:value['scopes'].remove('crop_result_read')
        rewrite(target,_canonical(value))
        try:
            denied=supervisor.run(path,expected_sha256=digest,max_chunks=1)
            assert denied['outcome']=='held' and denied['worker_returncode']!=0 and denied['result_sha256'] is None
            denials.append(denied)
        finally:rewrite(target,saved)
    assert files(server.directory)==history and tree(source)==source_before and counts(server.binding)==before
    assert (path/'supervision.json').read_bytes()==manifest_raw
    assert len(os.listdir('/proc/self/fd'))==descriptors
    receipts=(first,second,killed,resumed,paused,cancelled,*denials)
    evidence=Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])/'supervisor-original-attempts';evidence.mkdir(mode=0o700)
    for target in path.iterdir():
        if target.name=='worker.lock':continue
        runtime.write_private(evidence/target.name,target.read_bytes())
    for receipt in receipts:
        assert receipt['deadline_ns']==prepared['manifest']['deadline_ns'] and receipt['supervision_sha256']==digest
        assert not Path('/proc',str(receipt['worker']['pid'])).exists()
    save('registered-supervisor-verified.json',{'version':supervisor.VERSION,'scope':'owned_synthetic_small_same_DB_control_only',
        'supervision_sha256':digest,'config_sha256':config_sha,'manifest_preserved':True,
        'same_original_deadline_all_attempts':True,'actual_original_exits':[r['worker_returncode'] for r in receipts],
        'killed_worker':killed['worker'],'kill_point':'after_recovery_before_new_RHS',
        'checkpoint_sha256':[r['result']['checkpoint']['checkpoint_sha256'] for r in (first,second,resumed)],
        'progress':[r['result']['progress'] for r in (first,second,resumed)],
        'fresh_recovery_RHS_calls':[r['result']['recovery_RHS_calls'] for r in (first,second,resumed)],
        'actual_RHS_calls':[r['result']['actual_RHS_calls'] for r in (first,second,resumed)],
        'continuous_checkpoint_rows_UTC_exact':True,'counts':total,
        'native_pause_without_extra_RHS':True,'native_cancel_signals':[s['signal'] for s in cancelled['signals']],
        'row_sha256':{k:sha256(b''.join(_canonical(r)+b'\n' for r in v)).hexdigest() for k,v in selected.items()},
        'current_input_rights_and_principal_denied':True,'yielded_DB_publication_held':True,
        'DB_counts_before_after':[list(before),list(counts(server.binding))],'FD_before_after':[descriptors,descriptors],
        'owned_PG_identity_in_RSS':pg,'original_attempt_evidence_files':len(list(evidence.iterdir())),
        'whole166_registered_accepted':False,'product_CLI_independent_G1_accepted':False,'G0_G4':'not_assessed'})
