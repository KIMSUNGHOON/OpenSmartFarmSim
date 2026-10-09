"""Manual completed owned calculation publication through fresh Python and SCRAM."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic

import pytest

from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.thermal_run_store import _canonical
from crop_cycle_registered_runtime_smoke import (files, rewrite, server_setup, bound_setup,
    login_scope, original_login_scope, authoring, farm_setup, login_database,
    audit_registration, save, tree, counts, POLICY)

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-publication.py'


def module():
    spec=importlib.util.spec_from_file_location('native_terminal_publication',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def publish_child(publisher,path,digest,name):
    log=path.parent/(name+'.log');output=path.parent/(name+'.result.json')
    argv=[sys.executable,str(SCRIPT),'--declaration',str(path),'--sha256',digest,'--output',str(output)]
    started=monotonic()
    with log.open('xb') as stream:
        os.fchmod(stream.fileno(),0o600)
        child=subprocess.Popen(argv,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
        identity=publisher.supervisor.identity(child.pid)
        try:child.wait(timeout=60)
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=10)
            stream.flush();os.fsync(stream.fileno())
    log.chmod(0o400)
    evidence=Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])
    publisher.runtime.write_private(evidence/log.name,log.read_bytes())
    result=None
    if output.exists():
        publisher.runtime.write_private(evidence/output.name,output.read_bytes())
        result=json.loads(output.read_bytes())
        assert result['worker']==identity
    record={'argv':argv,'worker':identity,'exit_code':child.returncode,'wall_seconds':monotonic()-started,
        'fresh_python_exec':True,'log_sha256':sha256(log.read_bytes()).hexdigest(),
        'result_sha256':sha256(output.read_bytes()).hexdigest() if output.exists() else None,
        'worker_gone':not Path('/proc',str(child.pid)).exists(),'result':result}
    assert record['worker_gone']
    save(name+'.json',record)
    return record


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_terminal_fresh_python_same_DB_publish_retry_rows_and_current_denials(
        server_setup,audit_registration,tmp_path,monkeypatch):
    original,raw,_,principal,expected=server_setup
    principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    publisher=module();runtime=publisher.runtime;supervisor=publisher.supervisor
    source=original.input_resolver.directory;source_before=tree(source)
    config,config_sha=runtime.export_runtime(original,raw,tmp_path/'private-runtime')
    document=json.loads(config.read_bytes());config_before=files(config.parent)
    pg_files=list(Path(os.environ['TMPDIR']).glob('ossf-login-pg-*/data/postmaster.pid'));assert len(pg_files)==1
    pg={'process':supervisor.identity(int(pg_files[0].read_text().splitlines()[0])),
        'data_directory':str(pg_files[0].parent)}
    supervised=tmp_path/'supervised'
    prepared=supervisor.initialize(supervised,config=config,config_sha256=config_sha,
        max_steps=40,max_transitions=48,wall_seconds=500,owned_pg=pg)
    supervision_sha=prepared['supervision_sha256'];supervision_raw=(supervised/'supervision.json').read_bytes()
    def forbidden(*a,**k):pytest.fail('publication or read ran RHS')
    with monkeypatch.context() as no_math:
        no_math.setattr(runtime.engine.short._Evaluator,'rhs',forbidden)
        path,digest=publisher.declare(tmp_path/'publication',supervision_directory=supervised,
            supervision_sha256=supervision_sha)
    declaration_raw=path.read_bytes();value=json.loads(declaration_raw)
    key=runtime.private_bytes(value['DB_key_file']);assert len(key)==32 and key!=original.integrity_key
    server,request=runtime.load_runtime(config,config_sha);assert request==raw
    before=counts(server.binding);descriptors=len(os.listdir('/proc/self/fd'))
    absent=publish_child(publisher,path,digest,'publication-before-calculation')
    assert absent['exit_code']==71 and absent['result'] is None and counts(server.binding)==before
    partial=supervisor.run(supervised,expected_sha256=supervision_sha,max_chunks=1)
    assert partial['worker_returncode']==0 and partial['result']['progress']['status']=='yielded'
    yielded=publish_child(publisher,path,digest,'publication-yielded')
    assert yielded['exit_code']==71 and yielded['result'] is None and counts(server.binding)==before
    completed=supervisor.run(supervised,expected_sha256=supervision_sha,max_chunks=3)
    progress=completed['result']['progress']
    assert completed['worker_returncode']==0 and completed['outcome']=='recorded'
    assert progress['status']=='completed' and progress['steps']==progress['planned_steps']==expected['steps']==120
    assert progress['counts']==value['plan']['counts']=={'samples':3,'events':0}
    first=publish_child(publisher,path,digest,'publication-completed')
    retry=publish_child(publisher,path,digest,'publication-retry')
    assert first['exit_code']==retry['exit_code']==0
    assert {k:first['result'][k] for k in ('result_id','payload_sha256','recorded_at')}=={
        k:retry['result'][k] for k in ('result_id','payload_sha256','recorded_at')}
    for record in (first,retry):
        assert record['result']['RHS_calls']==0 and record['result']['actual_scram_used_password']
        assert record['result']['FD_before_after'][0]==record['result']['FD_before_after'][1]
        assert record['result']['deadline_ns']==prepared['manifest']['deadline_ns']
    assert counts(server.binding)==(*before[:4],1)
    monkeypatch.setattr(runtime.engine.short._Evaluator,'rhs',forbidden)
    store=CalculationCycleCropResultStore(server,integrity_key=key);farm=json.loads(raw)['farm']
    stored=store.get('tenant-1',first['result']['result_id'],farm)
    assert stored['payload_sha256']==first['result']['payload_sha256']
    for kind,limit in (('samples',64),('events',8)):
        page=store.page('tenant-1',stored['result_id'],farm,kind,0,limit)
        assert page['total']==page['next']==len(expected[kind])
        assert _canonical(page['records'])==_canonical(expected[kind])
    history=files(server.directory);denials=[]
    for name,error in (('rights',runtime.custody.CalculationCustodyHold),('principal',PermissionError)):
        target=Path(document[name+'_file']);saved=target.read_bytes();current=json.loads(saved)
        if name=='rights':current['allowed']=False
        else:current['scopes'].remove('crop_result_read')
        rewrite(target,_canonical(current))
        try:
            denied=publish_child(publisher,path,digest,'publication-denied-'+name)
            assert denied['exit_code']==71 and denied['result'] is None
            with pytest.raises(error):store.get('tenant-1',stored['result_id'],farm)
            denials.append(denied)
        finally:rewrite(target,saved)
    assert store.get('tenant-1',stored['result_id'],farm)==stored
    assert files(server.directory)==history and tree(source)==source_before
    assert counts(server.binding)==(*before[:4],1) and files(config.parent)==config_before
    assert path.read_bytes()==declaration_raw and (supervised/'supervision.json').read_bytes()==supervision_raw
    assert len(os.listdir('/proc/self/fd'))==descriptors
    assert server.input_resolver.last.reader.closed and not server.input_resolver.last._cache
    evidence=Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])/'supervisor-original-attempts';evidence.mkdir(mode=0o700)
    for target in supervised.iterdir():
        if target.name!='worker.lock':runtime.write_private(evidence/target.name,target.read_bytes())
    for receipt in (partial,completed):assert not Path('/proc',str(receipt['worker']['pid'])).exists()
    records=(absent,yielded,first,retry,*denials)
    save('registered-publication-verified.json',{'version':publisher.VERSION,
        'scope':'owned_synthetic_small_completed_DB_publication_only','actual_crop_Runs':0,'G0_G4':'not_assessed',
        'declaration_sha256':digest,'supervision_sha256':supervision_sha,'config_sha256':config_sha,
        'publication_actual_exits':[r['exit_code'] for r in records],'compute_actual_exits':[0,0],
        'compute_progress':[partial['result']['progress'],progress],
        'compute_recovery_RHS_calls':[r['result']['recovery_RHS_calls'] for r in (partial,completed)],
        'compute_actual_RHS_calls':[r['result']['actual_RHS_calls'] for r in (partial,completed)],
        'same_original_plan_deadline_and_declaration':True,'separate_random_DB_key':True,
        'precalculation_and_yielded_publication_denied':True,'fresh_publish_retry_RHS_zero':True,
        'same_result_id_payload_and_recorded_at':True,'same_original_all_rows_UTC':True,
        'current_rights_principal_denied':True,'selected_history_config_input_preserved':True,
        'row_sha256':{k:sha256(b''.join(_canonical(r)+b'\n' for r in expected[k])).hexdigest() for k in ('samples','events')},
        'DB_counts_before_after':[list(before),list(counts(server.binding))],
        'FD_before_after':[descriptors,descriptors],
        'all_owned_contexts_closed':True,'whole166_registered_DB_API_3D_accepted':False,
        'actual_product_CLI_independent_G1_accepted':False})
