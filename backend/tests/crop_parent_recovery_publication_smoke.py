"""Manual actual interrupted pytest, same-data PG restart and preserved-key publication."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys
import time

import pytest

from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_cycle_calculation_current_query import CalculationCurrentCycleQueryHold
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from crop_cycle_full_calendar_registration_smoke import farm_setup, POLICY, tree
from crop_cycle_registered_full_path_smoke import small_input
from crop_cycle_registered_runtime_smoke import rewrite
from crop_harvest_parent_backup_smoke import source_cleanup
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope, counts
from test_crop_cycle_input_evidence import authority
from test_farm_authoring_storage import authoring, request as farm_request
from login_database import login_database

ROOT = Path(os.environ.get('OSSF_RECOVERY_IMPLEMENTATION_ROOT', str(Path(__file__).resolve().parents[2])))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


@pytest.mark.parametrize('original_login_scope', [POLICY], indirect=True)
def test_interrupted_parent_same_checkpoint_PG_plan_key_publish_backup_and_current_rights(
        authoring, login_database, tmp_path, monkeypatch):
    helper = module('native_parent_recovery', ROOT / 'research/crop-parent-recovery-publication.py')
    p = helper.load_producer(Path(os.environ['OSSF_RECOVERY_PRODUCER_SOURCE']))
    stage = Path(os.environ['OSSF_PARENT_BACKUP_EVIDENCE'])
    prepared = (Path(os.environ['OSSF_PARENT_PRODUCER_PREPARATION']), os.environ['OSSF_PARENT_PRODUCER_PREPARATION_SHA256'])
    initial = p.coordinator.checked(*prepared); assert initial['scope'] == 'owned_small'
    runtime, supervisor = p.runtime, p.supervisor
    issuer = authority()
    directory, root, program, proof, reference = small_input(runtime, tmp_path, issuer)
    original_inputs = tree(directory)
    farms, body, principal = authoring; body = deepcopy(body)
    body['farm']['scenario_id'] = body['rights']['scenario_id'] = 'owned-recovered-parent-farm'
    body['rights']['declaration_id'] = 'owned-recovered-parent-rights'
    body['farm']['crops'][0]['occupancy']['end'] = '2027-03-16T00:00:00Z'
    body['farm']['crops'][0]['release_at'] = '2027-03-17T00:00:00Z'
    registration = farms.submit('tenant-1', farm_request(body))
    principal['scopes'].update(set(READ_SCOPES) | set(WRITE_SCOPES))
    binding = CalculationFarmBinding(farms, issuer, input_rights=SyntheticInputRights())
    proof_file = tmp_path / 'input-proof.private'; runtime.write_private(proof_file, proof)
    resolver = runtime.Resolver({'directory':str(directory), 'root_sha256':root, 'evidence_file':str(proof_file)},
                               'owned-recovered-parent-input-v1')
    custody = tmp_path / 'registered-server'; custody.mkdir(mode=0o700)
    server = runtime.custody.CalculationServerCustody(binding, custody, input_resolver=resolver, integrity_key=os.urandom(32))
    raw = p.canonical({'study_id':'owned-recovered-parent-study', 'revision':'r1', 'farm':{
        'scenario_id':body['farm']['scenario_id'], 'scenario_revision':body['farm']['scenario_revision'],
        'registration_sha256':registration.scenario_sha256, 'crop_id':'crop-1'},
        'input':{'schema_version':runtime.engine.inputs.VERSION, 'root_sha256':root, 'program_id':program},
        'rights':{'schema_version':'crop-cycle-input-rights-v1', 'declaration_id':'owned-recovered-parent-input-rights',
            'revision':'r1', 'input_root_sha256':root, 'available_at':body['farm']['decision_at'], 'redistribute':False,
            **{k:True for k in ('ownership_asserted','access','store','transform','use','display')}}})
    original_counts = counts(binding)
    config, config_sha = runtime.export_runtime(server, raw, tmp_path / 'private-runtime')
    document = json.loads(runtime.private_bytes(config))
    pg_files = list(Path(os.environ['TMPDIR']).glob('ossf-login-pg-*/data/postmaster.pid')); assert len(pg_files) == 1
    data = pg_files[0].parent
    old_pg = {'process':supervisor.identity(int(pg_files[0].read_text().splitlines()[0])), 'data_directory':str(data)}
    old_dir = tmp_path / 'old-supervised'
    old = supervisor.initialize(old_dir, config=config, config_sha256=config_sha,
        max_steps=40, max_transitions=48, wall_seconds=int(p.coordinator.remaining(initial))-2, owned_pg=old_pg)
    declaration, decl_sha = p.publisher.declare(tmp_path / 'publication', supervision_directory=old_dir,
                                               supervision_sha256=old['supervision_sha256'])
    _, decl = supervisor.read_json(declaration)
    reference_path = stage / 'original-reference.json'; ref_sha = supervisor.immutable(reference_path, reference)
    execution = {'version':p.coordinator.VERSION, 'preparation_file':str(prepared[0]), 'preparation_sha256':prepared[1],
        'preparation_deadline_ns':initial['deadline_ns'], 'config_sha256':config_sha, 'publication_file':str(declaration),
        'publication_sha256':decl_sha, 'reference_file':str(reference_path), 'reference_sha256':ref_sha,
        'plan':decl['plan'], 'farm':json.loads(raw)['farm'], 'input_root_sha256':root}
    execution_path = stage / 'original-execution.json'; execution_sha = supervisor.immutable(execution_path, execution)
    p.coordinator.execution(execution_path, execution_sha)
    protected_files = (execution_path, declaration, Path(decl['DB_key_file']), config, reference_path)
    protected_raw = {str(path):path.read_bytes() for path in protected_files}
    partial = supervisor.run(old_dir, expected_sha256=old['supervision_sha256'], max_chunks=1)
    assert partial['worker_returncode'] == 0 and partial['result']['progress']['status'] == 'yielded'
    nested_test = tmp_path / 'test_interrupted_owner.py'
    nested_test.write_text('''import importlib.util
from pathlib import Path
def test_owned_interrupted_calculation():
 spec=importlib.util.spec_from_file_location('old_owner',Path(''' + repr(str(p.ROOT / 'research/crop-cycle-registered-supervisor.py')) + '''))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 m.run(Path(''' + repr(str(old_dir)) + '''),expected_sha256=''' + repr(old['supervision_sha256']) + ''',max_chunks=4,stop_after_recovery=True)
''')
    with (stage / 'interrupted-pytest.private.log').open('xb') as log:
        os.fchmod(log.fileno(), 0o600)
        owner = subprocess.Popen([sys.executable, '-m', 'pytest', '-q', str(nested_test)],
            cwd=p.ROOT / 'backend', stdout=log, stderr=subprocess.STDOUT)
        owner_identity = supervisor.identity(owner.pid); worker_identity = None
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                worker_file = old_dir / 'attempt-0002.worker.json'
                if worker_file.exists():
                    _, worker_identity = supervisor.read_json(worker_file)
                    stat = Path('/proc',str(worker_identity['pid']),'stat').read_text().rsplit(')',1)[1].split()
                    if stat[0] == 'T': break
                assert owner.poll() is None
                time.sleep(.02)
            else: pytest.fail('isolated nested pytest did not reach recovered checkpoint')
            fd = os.pidfd_open(owner.pid)
            try:
                assert supervisor.identity(owner.pid) == owner_identity
                signal.pidfd_send_signal(fd, signal.SIGTERM)
            finally: os.close(fd)
            assert owner.wait(timeout=5) == -15
        finally:
            if owner.poll() is None: owner.kill(); owner.wait(timeout=5)
            if worker_identity is not None:
                try:
                    fd = os.pidfd_open(worker_identity['pid'])
                    try:
                        if supervisor.identity(worker_identity['pid']) == worker_identity:
                            signal.pidfd_send_signal(fd, signal.SIGKILL)
                    finally: os.close(fd)
                except ProcessLookupError: pass
    assert not (old_dir / 'attempt-0002.receipt.json').exists()
    restored_server, restored_request = runtime.load_runtime(config, config_sha)
    assert restored_request == raw
    progress = json.loads(restored_server.inspect('tenant-1', raw)); assert progress == partial['result']['progress']
    binary = Path(os.environ['OSSF_TEST_PG_BIN']); options = shlex.split((data / 'postmaster.opts').read_text())[1:]
    index = options.index('-D'); del options[index:index+2]
    restart = []
    for label, argv in (('stop',[str(binary/'pg_ctl'),'-D',str(data),'-m','fast','-w','-t','10','stop']),
            ('start',[str(binary/'pg_ctl'),'-D',str(data),'-l',str(data.parent/'server.log'),'-w','-t','10','start','-o',shlex.join(options)])):
        with (stage / ('PG-'+label+'.private.log')).open('xb') as log:
            os.fchmod(log.fileno(),0o600); result = subprocess.run(argv,stdout=log,stderr=subprocess.STDOUT,timeout=20)
        restart.append(result.returncode); assert result.returncode == 0
    new_pg = {'process':supervisor.identity(int((data/'postmaster.pid').read_text().splitlines()[0])), 'data_directory':str(data)}
    assert new_pg['process'] != old_pg['process']
    new_dir = tmp_path / 'recovered-supervised'
    recovered = supervisor.initialize(new_dir, config=config, config_sha256=config_sha,
        max_steps=40,max_transitions=48,wall_seconds=int(supervisor.remaining(old['manifest']))-2,owned_pg=new_pg)
    incident = {'version':'owned-parent-interruption-v1', 'actual_pytest_exit':owner.returncode,
        'interrupted_HEAD_sha256':progress['head_sha256'], 'interrupted_steps':progress['steps'],
        'interrupted_commit_count':progress['commit_count'], 'original_completed_or_accepted':False,
        'original_deadline_ns':initial['deadline_ns'], 'deadline_not_extended':True,
        'private_material_sha256':{str(path):sha256(raw_bytes).hexdigest() for path,raw_bytes in
                                   ((Path(name),raw_bytes) for name,raw_bytes in protected_raw.items())}}
    incident_path = stage / 'interruption.private.json'; incident_sha = supervisor.immutable(incident_path, incident)
    computed = supervisor.run(new_dir, expected_sha256=recovered['supervision_sha256'], max_chunks=4)
    assert computed['outcome'] == 'recorded' and computed['worker_returncode'] == 0
    assert computed['result']['progress']['steps'] == reference['steps'] == 120
    assert computed['result']['progress']['counts'] == reference['counts']
    def forbidden(*_a, **_k): pytest.fail('derivation/query ran RHS')
    with monkeypatch.context() as pure:
        pure.setattr(runtime.engine.short._Evaluator,'rhs',forbidden)
        path, digest = helper.derive(p, execution_path=execution_path,execution_sha256=execution_sha,
            incident_path=incident_path,incident_sha256=incident_sha,recovery_directory=new_dir,
            recovery_sha256=recovered['supervision_sha256'],output_directory=stage/'derived')
        derived = helper.checked(p,path,digest)
    compared_path = stage / 'comparison.result.json'
    compared = p.coordinator.child([sys.executable,str(p.ROOT/'research/crop-cycle-registered-full-path.py'),
        '--compare','--execution',derived['execution']['file'],'--sha256',derived['execution']['sha256'],
        '--output',str(compared_path)],name='comparison',prepared=prepared,evidence=stage)
    comparison = json.loads(runtime.private_bytes(compared_path))
    assert comparison['comparison']['all_rows_compared'] and comparison['checkpoint_state_count'] == 121
    helper.checked(p,path,digest)
    publication_output = Path(derived['publication']['file']).parent / 'publication.result.json'
    published = p.coordinator.child([sys.executable,str(p.ROOT/'research/crop-cycle-registered-publication.py'),
        '--declaration',derived['publication']['file'],'--sha256',derived['publication']['sha256'],
        '--output',str(publication_output)],name='publication',prepared=prepared,evidence=stage)
    _, _, current, request_raw, db_key = p.publisher.load_declaration(derived['publication']['file'],derived['publication']['sha256'])
    assert db_key == protected_raw[decl['DB_key_file']] and request_raw == raw
    publication = json.loads(runtime.private_bytes(publication_output)); farm = json.loads(raw)['farm']
    record = CalculationCycleCropResultStore(current,integrity_key=db_key).get('tenant-1',publication['result_id'],farm)
    result_key = os.urandom(32)
    result_issuer = CalculationResultEvidenceAuthority(current.binding.input_authority,integrity_key=result_key,
        issuer_id='owned-parent-backup-result',key_id='result-v1')
    artifact = current.directory/runtime.custody._intent_id('tenant-1',json.loads(raw))/'artifact'
    result_proof = result_issuer.issue(artifact,computed['result']['progress']['artifact_sha256'],directory,root,proof)
    backup, backup_sha = p.backup.backup(stage/'backup',admin_dsn=login_database['admin'],owned_data=data,binary=binary,
        config=config,config_sha256=config_sha,db_key=db_key,result_key=result_key,result_proof=result_proof,record=record,farm=farm)
    with p.backup.readonly_guard():
        selected = p.selected_read(backup,backup_sha,{'config':config,'config_sha256':config_sha})
        query = p.backup.current_query(backup,backup_sha,{'config':config,'config_sha256':config_sha})
        with pytest.raises(PermissionError): query.read('foreign',record['result_id'],farm)
        for name,error in (('rights',CalculationCurrentCycleQueryHold),('principal',PermissionError)):
            target=Path(document[name+'_file']); saved=target.read_bytes(); value=json.loads(saved)
            if name=='rights':value['allowed']=False
            else:value['scopes'].remove('crop_result_read')
            rewrite(target,p.canonical(value))
            try:
                with pytest.raises(error):query.read('tenant-1',record['result_id'],farm)
            finally:rewrite(target,saved)
    assert counts(binding) == (*original_counts[:4],1) and tree(directory) == original_inputs
    assert all(Path(name).read_bytes() == original_raw for name,original_raw in protected_raw.items())
    p.coordinator.checked(*prepared)
    p.backup.write(stage/'recovered-parent.private.json',p.canonical({'version':helper.VERSION,
        'scope':'owned_small_interrupted_parent_recovery_only','backup':str(backup),'backup_sha256':backup_sha,
        'recovery':str(path),'recovery_sha256':digest,'actual_original_pytest_exit':owner.returncode,
        'original_worker':worker_identity,'PG_stop_start_exit_codes':restart,'old_new_PG':[old_pg,new_pg],
        'interrupted_progress':progress,'completed_progress':computed['result']['progress'],
        'compute_exit':computed['worker_returncode'],'comparison_command':compared,'publication_command':published,
        'all_rows_and_121state_compared':True,'original_plan_key_files_preserved':True,
        'source_read':selected,'current_rights_principal_foreign_denied':True,
        'original_preparation_deadline_ns':initial['deadline_ns'],'actual_crop_Runs':0,'G0_G4':'not_assessed'}))
