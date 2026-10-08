"""Manual same registered DB, fresh terminal publisher, actual HTTPS and WebGL."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path

import pytest

from app.crop_result_store import READ_SCOPES,WRITE_SCOPES
from app.thermal_run_store import _canonical
from test_crop_cycle_artifact import PROFILES
from test_crop_startup_result_store import shifted
from test_crop_cycle_calculation_server_custody_farms import OwnInputResolver
from crop_cycle_registered_terminal_publication_smoke import (module as publication_module,publish_child,
    server_setup,bound_setup,login_scope,original_login_scope,authoring,farm_setup,login_database,
    audit_registration,save,tree,counts,POLICY)
from test_operator_config import private_config
from test_api_serve import tls_files

SCRIPT=Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-replay.py'


def consumer():
    spec=importlib.util.spec_from_file_location('registered_native_replay',SCRIPT)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_same_DB_registered_managed_calculation_publication_TLS_and_native_3D(
        server_setup,audit_registration,private_config,tmp_path,monkeypatch,request):
    replay=consumer();publisher=publication_module();runtime=publisher.runtime
    original,raw,_,principal,_=server_setup
    principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    program=shifted('full-removal-reentry')
    expected=runtime.engine.physical.integrate_plant_startup(**deepcopy(program),**PROFILES)
    assert expected['status']=='completed' and len(expected['samples'])==len(expected['events'])==3
    anchors=program.pop('output_times');directory=tmp_path/'managed-inputs';program_id='owned-registered-replay-managed'
    packet=runtime.engine.inputs.write_input_packet(directory,**program,anchors=anchors,outputs=anchors,
        **PROFILES,program_id=program_id)
    for path in directory.iterdir():path.chmod(0o400)
    authority=original.binding.input_authority;proof=authority.issue(directory,packet['root_sha256'])
    root=tmp_path/'managed-server';root.mkdir(mode=0o700)
    server=runtime.custody.CalculationServerCustody(original.binding,root,
        input_resolver=OwnInputResolver(directory,packet['root_sha256'],proof),integrity_key=original.integrity_key)
    body=json.loads(raw);body['study_id']=program_id
    body['input'].update(root_sha256=packet['root_sha256'],program_id=program_id)
    body['rights'].update(declaration_id=program_id,input_root_sha256=packet['root_sha256']);raw=_canonical(body)
    before=counts(server.binding);source_before=tree(directory)
    config,config_sha=runtime.export_runtime(server,raw,tmp_path/'private-runtime')
    pg_files=list(Path(os.environ['TMPDIR']).glob('ossf-login-pg-*/data/postmaster.pid'));assert len(pg_files)==1
    pg={'process':publisher.supervisor.identity(int(pg_files[0].read_text().splitlines()[0])),
        'data_directory':str(pg_files[0].parent)}
    supervised=tmp_path/'supervised'
    prepared=publisher.supervisor.initialize(supervised,config=config,config_sha256=config_sha,
        max_steps=10000,max_transitions=4096,wall_seconds=500,owned_pg=pg)
    path,digest=publisher.declare(tmp_path/'publication',supervision_directory=supervised,
        supervision_sha256=prepared['supervision_sha256'])
    completed=publisher.supervisor.run(supervised,expected_sha256=prepared['supervision_sha256'],max_chunks=2)
    assert completed['outcome']=='recorded' and completed['worker_returncode']==0
    assert completed['result']['progress']['status']=='completed'
    assert completed['result']['progress']['counts']=={'samples':3,'events':3}
    published=publish_child(publisher,path,digest,'replay-publication-completed')
    assert published['exit_code']==0 and counts(server.binding)==(*before[:4],1)
    report=replay.replay(publisher,path,digest,published['result'],expected=expected,
        private_config=private_config,request=request,monkeypatch=monkeypatch,tmp_path=tmp_path)
    assert report['browser']['samples_verified']==report['browser']['events_verified']==3
    assert report['browser']['same_UTC_geometry'] and report['browser']['actual_WebGL']
    assert report['actual_same_DB'] and report['read_RHS_calls']==0
    assert tree(directory)==source_before and counts(server.binding)==(*before[:4],1)
    save('registered-replay-verified.json',{**report,'compute_progress':completed['result']['progress'],
        'compute_worker':completed['worker'],'compute_actual_exit':completed['worker_returncode'],
        'publication_worker':published['worker'],'publication_actual_exit':published['exit_code'],
        'publication_log_sha256':published['log_sha256'],
        'input_root_sha256':packet['root_sha256'],'source_input_preserved':True,
        'DB_counts_before_after':[list(before),list(counts(server.binding))],
        'whole166_registered_DB_API_3D_accepted':False,'G0_G4':'not_assessed','actual_crop_Runs':0})
    evidence=Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])/'supervisor-original-attempts';evidence.mkdir(mode=0o700)
    for target in supervised.iterdir():
        if target.name!='worker.lock':runtime.write_private(evidence/target.name,target.read_bytes())
