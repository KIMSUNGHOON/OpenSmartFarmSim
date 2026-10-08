"""Manual one-DB preparation/comparison/publication/native replay, small before full166."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest

from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from app.thermal_run_store import _canonical
from crop_cycle_full_calendar_registration_smoke import (farm_setup,authoring,login_database,
    audit_registration,save,tree,POLICY)
from crop_cycle_full_prefix_cost_smoke import packet as full_packet
from crop_cycle_registered_replay_smoke import tls_files,loopback_tls_files
from test_crop_cycle_artifact import PROFILES
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_calculation_result_store_farms import login_scope,original_login_scope,counts
from test_crop_cycle_input_evidence import authority
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import request as farm_request
from test_operator_config import private_config

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-full-path.py'


def module():
    spec=importlib.util.spec_from_file_location('native_registered_full_path',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def small_input(runtime,tmp_path,issuer):
    program=shifted('full-removal-reentry');expected=runtime.engine.physical.integrate_plant_startup(**deepcopy(program),**PROFILES)
    anchors=program.pop('output_times');directory=tmp_path/'managed-inputs';program_id='owned-full-path-small-managed'
    packet=runtime.engine.inputs.write_input_packet(directory,**program,anchors=anchors,outputs=anchors,**PROFILES,program_id=program_id)
    for path in directory.iterdir():path.chmod(0o400)
    with runtime.engine.inputs.open_input_packet(directory,packet['root_sha256'],**PROFILES) as reader:
        context=runtime.engine.legacy.prepare_context(reader,**PROFILES)
        result=runtime.engine.legacy.advance_chunk(context,runtime.engine.legacy.start(context),{'max_steps':10000,'max_transitions':4096})
    assert result['status']=='completed' and result['samples']==expected['samples'] and result['events']==expected['events']
    reference={'kind':'owned_small_legacy_reference','rows':{k:expected[k] for k in ('samples','events')},
        'counts':{k:len(expected[k]) for k in ('samples','events')},'steps':expected['steps'],'checkpoint':result['checkpoint'],'offset_days':0}
    return directory,packet['root_sha256'],program_id,issuer.issue(directory,packet['root_sha256']),reference


def full_input():
    paths,receipt,proof=full_packet()
    reference={'kind':'owned_original166','counts':{'samples':47809,'events':5},'steps':1816704,'offset_days':273,
        'artifact_directory':str(paths['artifact']),'artifact_sha256':'15b609576243c73b67a4947b5affc2db14047787e4851064b3aabeafd3d0286d',
        'input_directory':str(paths['original']),'input_root_sha256':'ab24eda4d763d7fe3faff1ae3c7c2f84fbec030af71a494bf284fef1f2cdcd98',
        'row_sha256':{'samples':'b00e63d96debcbfc2c80eb5c17b71a9a9bd7bd0634acdb1d6ffe47655ae53dbd',
                      'events':'0900f8ff0753d3d7746a2ea32b75ed579ba0c07a7789d99e4b4cee01850e1eb8'}}
    for name in ('input','result'):
        path=paths['proofs']/(name+'-evidence.json')
        reference[name+'_evidence_file']=str(path);reference[name+'_evidence_sha256']=sha256(path.read_bytes()).hexdigest()
    return paths['derived'],receipt['target_root_sha256'],receipt['target_program_id'],proof,reference


def run_path(authoring,tmp_path,monkeypatch,request,private_config,*,full):
    coordinator=module();runtime=coordinator.runtime
    prepared=(Path(os.environ['OSSF_FULL_PATH_PREPARATION']),os.environ['OSSF_FULL_PATH_PREPARATION_SHA256'])
    initial=coordinator.checked(*prepared);assert initial['scope']==('owned_full166' if full else 'owned_small')
    issuer=authority()
    directory,root,program_id,proof,reference=full_input() if full else small_input(runtime,tmp_path,issuer)
    source_before=tree(directory);farms,body,principal=authoring;body=deepcopy(body)
    body['farm']['scenario_id']=body['rights']['scenario_id']='owned-full-path-farm'
    body['rights']['declaration_id']='owned-full-path-farm-rights'
    body['farm']['crops'][0]['occupancy']['end']='2027-03-16T00:00:00Z'
    body['farm']['crops'][0]['release_at']='2027-03-17T00:00:00Z'
    registered=farms.submit('tenant-1',farm_request(body))
    principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    binding=CalculationFarmBinding(farms,issuer,input_rights=SyntheticInputRights())
    proof_file=tmp_path/'input-proof.private';runtime.write_private(proof_file,proof)
    resolver=runtime.Resolver({'directory':str(directory),'root_sha256':root,'evidence_file':str(proof_file)},'owned-full-path-input-v1')
    server_root=Path(os.environ['OSSF_FULL_PATH_CUSTODY']) if full else tmp_path/'registered-server'
    server_root.mkdir(mode=0o700)
    server=runtime.custody.CalculationServerCustody(binding,server_root,input_resolver=resolver,integrity_key=os.urandom(32))
    raw=_canonical({'study_id':'owned-full-path-study','revision':'r1','farm':{
        'scenario_id':body['farm']['scenario_id'],'scenario_revision':body['farm']['scenario_revision'],
        'registration_sha256':registered.scenario_sha256,'crop_id':'crop-1'},
        'input':{'schema_version':runtime.engine.inputs.VERSION,'root_sha256':root,'program_id':program_id},
        'rights':{'schema_version':'crop-cycle-input-rights-v1','declaration_id':'owned-full-path-input-rights','revision':'r1',
            'input_root_sha256':root,'available_at':body['farm']['decision_at'],'redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}})
    evidence=Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE']);reference_file=evidence/'original-reference.json'
    reference_sha256=coordinator.supervisor.immutable(reference_file,reference)
    before=counts(binding)
    report=coordinator.run(server,raw,prepared=prepared,reference_file=reference_file,reference_sha256=reference_sha256,
        evidence=evidence,tmp_path=tmp_path,private_config=private_config,request=request,monkeypatch=monkeypatch)
    assert counts(binding)==(*before[:4],1) and tree(directory)==source_before
    assert report['compute_progress']['counts']==reference['counts'] and report['compute_progress']['steps']==reference['steps']
    assert report['comparison_counts_hashes']['counts']==reference['counts'] and report['comparison']['checkpoint_state_count']==121
    assert report['comparison']['RHS_calls']==0 and report['replay']['read_RHS_calls']==0
    assert resolver.last.reader.closed and not resolver.last._cache
    assert report['preparation_deadline_ns']==initial['deadline_ns']
    assert report['inner_supervision_deadline_ns']<=initial['deadline_ns']
    save('registered-full-path-verified.json',{**report,'DB_counts_before_after':[list(before),list(counts(binding))],
        'source_input_preserved':True,'whole166_registered_DB_API_3D_observed':full,
        'actual_product_CLI_independent_G1_accepted':False})


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_small_managed_same_DB_original_stream_comparison_publication_TLS_and_WebGL(
        authoring,audit_registration,tmp_path,monkeypatch,request,private_config):
    run_path(authoring,tmp_path,monkeypatch,request,private_config,full=False)


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_full166_same_DB_original_stream_comparison_publication_TLS_and_WebGL(
        authoring,audit_registration,tmp_path,monkeypatch,request,private_config):
    run_path(authoring,tmp_path,monkeypatch,request,private_config,full=True)
