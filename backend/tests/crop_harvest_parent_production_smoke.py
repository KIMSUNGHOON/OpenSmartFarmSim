"""Manual normal producer, all-row comparison, publication and retained authority."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path

import pytest

from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_current_query import CalculationCurrentCycleQueryHold
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from crop_cycle_full_calendar_registration_smoke import farm_setup,POLICY,tree
from crop_cycle_registered_full_path_smoke import small_input,full_input
from crop_cycle_registered_runtime_smoke import rewrite
from crop_harvest_parent_backup_smoke import source_cleanup
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_calculation_result_store_farms import login_scope,original_login_scope,counts
from test_crop_cycle_input_evidence import authority
from test_farm_authoring_storage import authoring,request as farm_request
from login_database import login_database

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-harvest-parent-production.py'


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_owned_parent_normal_producer_all_rows_publication_and_retained_authority(authoring,login_database,tmp_path):
    spec=importlib.util.spec_from_file_location('manual_parent_production',SCRIPT)
    producer=importlib.util.module_from_spec(spec);spec.loader.exec_module(producer)
    stage=Path(os.environ['OSSF_PARENT_BACKUP_EVIDENCE']);runtime=producer.runtime
    full=os.environ.get('OSSF_PARENT_PRODUCER_FULL')=='1'
    prepared=(Path(os.environ['OSSF_PARENT_PRODUCER_PREPARATION']),os.environ['OSSF_PARENT_PRODUCER_PREPARATION_SHA256'])
    initial=producer.coordinator.checked(*prepared)
    assert initial['scope']==('owned_full166' if full else 'owned_small')
    issuer=authority()
    directory,root,program,proof,reference=full_input() if full else small_input(runtime,tmp_path,issuer)
    original_inputs=tree(directory);farms,body,principal=authoring;body=deepcopy(body)
    body['farm']['scenario_id']=body['rights']['scenario_id']='owned-harvest-parent-farm'
    body['rights']['declaration_id']='owned-harvest-parent-farm-rights'
    body['farm']['crops'][0]['occupancy']['end']='2027-03-16T00:00:00Z'
    body['farm']['crops'][0]['release_at']='2027-03-17T00:00:00Z'
    registration=farms.submit('tenant-1',farm_request(body));principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    binding=CalculationFarmBinding(farms,issuer,input_rights=SyntheticInputRights())
    proof_file=tmp_path/'input-proof.private';runtime.write_private(proof_file,proof)
    resolver=runtime.Resolver({'directory':str(directory),'root_sha256':root,'evidence_file':str(proof_file)},
        'owned-harvest-parent-input-v1')
    custody=tmp_path/'registered-server';custody.mkdir(mode=0o700)
    server=runtime.custody.CalculationServerCustody(binding,custody,input_resolver=resolver,integrity_key=os.urandom(32))
    raw=producer.canonical({'study_id':'owned-harvest-parent-study','revision':'r1','farm':{
        'scenario_id':body['farm']['scenario_id'],'scenario_revision':body['farm']['scenario_revision'],
        'registration_sha256':registration.scenario_sha256,'crop_id':'crop-1'},
        'input':{'schema_version':runtime.engine.inputs.VERSION,'root_sha256':root,'program_id':program},
        'rights':{'schema_version':'crop-cycle-input-rights-v1','declaration_id':'owned-harvest-parent-input-rights',
            'revision':'r1','input_root_sha256':root,'available_at':body['farm']['decision_at'],'redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}})
    reference_path=stage/'original-reference.json';reference_sha=producer.supervisor.immutable(reference_path,reference)
    before=counts(binding)
    result=producer.produce(server,raw,prepared=prepared,reference_file=reference_path,reference_sha256=reference_sha,
        evidence=stage,work=tmp_path,admin_dsn=login_database['admin'],binary=Path(os.environ['OSSF_TEST_PG_BIN']))
    assert result['compute_actual_exit']==0 and result['compute_progress']['counts']==reference['counts']
    assert result['compute_progress']['steps']==reference['steps'] and result['comparison']['checkpoint_state_count']==121
    assert result['comparison_counts_hashes']['all_rows_compared'] and result['comparison']['RHS_calls']==0
    assert counts(binding)==(*before[:4],1) and tree(directory)==original_inputs
    document=json.loads(Path(result['config']).read_bytes())
    with producer.backup.readonly_guard():
        query=producer.backup.current_query(result['backup'],result['backup_sha256'],
            {'config':result['config'],'config_sha256':result['config_sha256']})
        args=('tenant-1',result['current_query']['record']['result_id'],json.loads(raw)['farm'])
        with pytest.raises(PermissionError):query.read('foreign',args[1],args[2])
        for name,error in (('rights',CalculationCurrentCycleQueryHold),('principal',PermissionError)):
            path=Path(document[name+'_file']);saved=path.read_bytes();value=json.loads(saved)
            if name=='rights':value['allowed']=False
            else:value['scopes'].remove('crop_result_read')
            rewrite(path,producer.canonical(value))
            try:
                with pytest.raises(error):query.read(*args)
            finally:rewrite(path,saved)
            assert query.read(*args)['record']['payload_sha256']==result['current_query']['record']['payload_sha256']
    producer.backup.write(stage/'normal-producer.private.json',producer.canonical({**result,
        'current_rights_principal_foreign_denied':True,'source_inputs_preserved':True,'private_authority_retained':True}))
