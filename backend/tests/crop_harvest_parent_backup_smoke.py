"""Manual private authority backup and actual SCRAM restore for a small crop parent."""
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import psycopg
import pytest

from app.crop_cycle_calculation_current_query import CalculationCurrentCycleQueryHold
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from crop_cycle_registered_runtime_smoke import rewrite,files
from test_crop_cycle_calculation_server_custody_farms import server_setup,BUDGET
from test_crop_cycle_calculation_farm_binding import setup as bound_setup
from test_crop_cycle_calculation_result_store_farms import login_scope,original_login_scope,counts
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database,assert_host_scram

SCRIPT = Path(__file__).resolve().parents[2]/'research/crop-harvest-parent-backup.py'
POLICY = {'market_calculation':True,'market_source_storage':True,'thermal_scenario_storage':True,
          'break_even_calculation':True,'crop_cycle_result_storage':True}


def module():
    spec=importlib.util.spec_from_file_location('manual_owned_parent_backup',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


@pytest.fixture(scope='module',autouse=True)
def source_cleanup(login_database):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname LIKE 'login_test_%'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname LIKE 'login_%'").fetchone()[0]
        data=Path(conn.execute('SHOW data_directory').fetchone()[0]);methods=assert_host_scram(conn)
    stage=Path(os.environ['OSSF_PARENT_BACKUP_EVIDENCE'])
    assert schemas==roles==0
    module().write(stage/'source-cleanup.private.json',module().canonical({
        'schemas':schemas,'roles':roles,'source_data':str(data),
        'source_pid':int((data/'postmaster.pid').read_text().splitlines()[0]),'host_auth':methods}))


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_owned_parent_random_authority_backup_and_same_result_actual_restore(server_setup,login_database,tmp_path,monkeypatch):
    owned=module();runtime=owned.runtime;stage=Path(os.environ['OSSF_PARENT_BACKUP_EVIDENCE'])
    original,raw,_,principal,expected=server_setup;principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    # Declare the random server key before any calculation or signed intent exists.
    original=runtime.custody.CalculationServerCustody(original.binding,original.directory,
        input_resolver=original.input_resolver,integrity_key=os.urandom(32))
    config,digest=runtime.export_runtime(original,raw,stage/'source-authority')
    server,loaded=runtime.load_runtime(config,digest);assert loaded==raw
    calls=[];rhs=runtime.engine.short._Evaluator.rhs
    def counted(*args,**kwargs):calls.append(1);return rhs(*args,**kwargs)
    with monkeypatch.context() as creation:
        creation.setattr(runtime.engine.short._Evaluator,'rhs',counted)
        progress=json.loads(server.advance('tenant-1',raw,budget=BUDGET))
    assert progress['status']=='completed' and progress['steps']==expected['steps']==120 and calls
    db_key=os.urandom(32);result_key=os.urandom(32)
    store=CalculationCycleCropResultStore(server,integrity_key=db_key);record=store.put('tenant-1',raw)
    document=json.loads(config.read_bytes());farm=json.loads(raw)['farm']
    result_dir=server.directory/runtime.custody._intent_id('tenant-1',json.loads(raw))/'artifact'
    issuer=CalculationResultEvidenceAuthority(server.binding.input_authority,integrity_key=result_key,
        issuer_id='owned-parent-backup-result',key_id='result-v1')
    proof=issuer.issue(result_dir,progress['artifact_sha256'],Path(document['input']['directory']),
        document['input']['root_sha256'],runtime.private_bytes(document['input']['evidence_file']))
    before=counts(server.binding);source_files=files(server.directory)
    source_inputs=files(Path(document['input']['directory']))
    fd_before=len(os.listdir('/proc/self/fd'))
    with psycopg.connect(login_database['admin']) as conn:
        data=Path(conn.execute('SHOW data_directory').fetchone()[0])
    path,checksum=owned.backup(stage/'backup',admin_dsn=login_database['admin'],owned_data=data,
        binary=Path(os.environ['OSSF_TEST_PG_BIN']),config=config,config_sha256=digest,
        db_key=db_key,result_key=result_key,result_proof=proof,record=record,farm=farm)
    metadata=owned.checked(path,checksum)
    expected_hashes={kind:{'count':len(expected[kind]),
        'sha256':sha256(b''.join(owned.canonical(r)+b'\n' for r in expected[kind])).hexdigest()}
        for kind in ('samples','events')}
    source_context={'config':config,'config_sha256':digest}
    with owned.readonly_guard():
        source=owned.read_receipt(path,checksum,source_context)
        assert source['rows']==expected_hashes
        with owned.restored(path,checksum,stage/'restore-first') as context:
            restored=owned.read_receipt(path,checksum,context)
            assert {k:v for k,v in source.items() if k!='FD_before_after'}=={
                k:v for k,v in restored.items() if k!='FD_before_after'}
            query=owned.current_query(path,checksum,context);args=('tenant-1',record['result_id'],farm)
            with pytest.raises(PermissionError):query.read('foreign',record['result_id'],farm)
            for name,error in (('rights',CalculationCurrentCycleQueryHold),('principal',PermissionError)):
                target=Path(document[name+'_file']);saved=target.read_bytes();value=json.loads(saved)
                if name=='rights':value['allowed']=False
                else:value['scopes'].remove('crop_result_read')
                rewrite(target,owned.canonical(value))
                try:
                    with pytest.raises(error):query.read(*args)
                finally:rewrite(target,saved)
                assert query.read(*args)['record']==record
            worker=stage/'fresh-read.private.json'
            command=owned.command(Path(sys.executable),[SCRIPT,'--backup',path,'--sha256',checksum,
                '--config',context['config'],'--config-sha256',context['config_sha256'],'--output',worker],
                stage,'fresh-read',timeout=180)
            fresh=json.loads(worker.read_bytes())
            assert {k:v for k,v in source.items() if k!='FD_before_after'}=={
                k:v for k,v in fresh.items() if k!='FD_before_after'}
    assert not (stage/'restore-first/data/postmaster.pid').exists()
    assert counts(server.binding)==before and files(server.directory)==source_files
    assert files(Path(document['input']['directory']))==source_inputs
    assert len(os.listdir('/proc/self/fd'))==fd_before
    with pytest.raises(ValueError):owned.checked(path,'0'*64)
    denied=[]
    for name,filename in (('missing-key','DB-key.private'),('dump-bytes','database.private.dump'),
                          ('runtime-bytes','original-runtime.private')):
        target=stage/('tampered-'+name);shutil.copytree(path.parent,target)
        altered=target/filename
        if name=='missing-key':altered.unlink()
        else:rewrite(altered,altered.read_bytes()+b'X')
        with pytest.raises((ValueError,OSError)):owned.checked(target/path.name,checksum)
        shutil.rmtree(target);denied.append(name)
    owned.write(stage/'accepted-small.private.json',owned.canonical({
        'version':owned.VERSION,'scope':'owned_synthetic_small_parent_backup_only',
        'backup':str(path),'backup_sha256':checksum,'source_config_sha256':digest,
        'source':source,'compute_RHS_calls':len(calls),'compute_steps':progress['steps'],
        'raw_backup_bytes':sum((path.parent/name).stat().st_size for name in metadata['files_sha256']),
        'fresh_python_command':command,'restored_rows_exact':True,'current_rights_principal_denied':True,
        'wrong_tenant_denied':True,'tamper_denied':denied,'source_record_files_inputs_preserved':True,
        'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))],
        'retained_private_material_intentional':True,'G0_G4':'not_assessed','actual_crop_Runs':0}))
