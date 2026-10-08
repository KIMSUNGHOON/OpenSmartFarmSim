"""Manual same-DB fresh Python recovery, killed before calculation, current denial."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
from time import monotonic, sleep

import pytest

from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_server_custody as custody
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.thermal_run_store import _canonical
from crop_cycle_full_calendar_registration_smoke import audit_registration, save, tree, POLICY
from test_crop_cycle_calculation_server_custody_farms import server_setup
from test_crop_cycle_calculation_farm_binding import setup as bound_setup
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope, counts, DB_KEY
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database

SCRIPT = Path(__file__).resolve().parents[2]/'research/crop-cycle-registered-runtime.py'
BUDGET = {'max_steps':40,'max_transitions':48}


def module():
    spec = importlib.util.spec_from_file_location('owned_registered_runtime', SCRIPT)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def rewrite(path, raw):
    path.chmod(0o600); path.write_bytes(raw); path.chmod(0o400)


def events(path):
    try: return [json.loads(line) for line in path.read_text().splitlines()]
    except (ValueError, FileNotFoundError): return []


def run_worker(runtime, config, digest, directory, name, *, advance=False, kill_after_recovery=False):
    argv = [sys.executable, str(SCRIPT), '--config', str(config), '--sha256', digest,
            '--max-steps',str(BUDGET['max_steps']),'--max-transitions',str(BUDGET['max_transitions'])]
    if advance: argv.append('--advance')
    if kill_after_recovery: argv.append('--stop-after-recovery')
    path = directory/(name+'.log'); started = monotonic(); recovered = None
    with path.open('xb') as log:
        os.fchmod(log.fileno(),0o600)
        child = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        worker_stat = Path('/proc')/str(child.pid)/'stat'
        initial_ticks = worker_stat.read_text().rsplit(')',1)[1].split()[19]
        try:
            if kill_after_recovery:
                deadline = monotonic()+30
                while True:
                    assert child.poll() is None and monotonic() < deadline, 'owned recovery did not reach stop point'
                    records = events(path)
                    fields = worker_stat.read_text().rsplit(')',1)[1].split()
                    if records and records[0]['stage']=='recovered' and fields[0]=='T':
                        recovered = records[0]; break
                    sleep(.01)
                assert recovered['worker']['pid']==child.pid and recovered['worker']['start_ticks']==initial_ticks
                os.kill(child.pid,signal.SIGKILL)
            child.wait(timeout=60)
        finally:
            if child.poll() is None: child.kill(); child.wait(timeout=10)
            log.flush(); os.fsync(log.fileno())
    path.chmod(0o400)
    raw = path.read_bytes()
    target = Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])/(name+'.log')
    runtime.write_private(target, raw)
    record = {'argv':argv,'pid':child.pid,'start_ticks':initial_ticks,'exit_code':child.returncode,
        'wall_seconds':monotonic()-started,'log_sha256':sha256(raw).hexdigest(),
        'kill_after_recovery_before_calculation':kill_after_recovery,'fresh_python_exec':True,
        'same_primary_alive_after':worker_stat.exists(),'records':events(path)}
    save(name+'.json', record)
    return record


def checkpoint(server, raw, monkeypatch):
    with monkeypatch.context() as no_math:
        def forbidden(*a,**k): pytest.fail('parent read ran RHS/delta QC')
        no_math.setattr(engine.short._Evaluator,'rhs',forbidden)
        no_math.setattr(artifact,'_validate_delta',forbidden)
        with server._open('tenant-1',raw,False) as journal:
            return json.loads(journal.inspect()), deepcopy(journal.writer._checkpoint)


def files(directory):
    return {str(p.relative_to(directory)):(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode,p.stat().st_ino)
            for p in directory.rglob('*') if p.is_file()}


@pytest.mark.parametrize('original_login_scope',[POLICY],indirect=True)
def test_registered_fresh_python_same_DB_checkpoint_kill_and_current_denials(
        server_setup, audit_registration, tmp_path, monkeypatch):
    original, raw, _, principal, _ = server_setup
    principal['scopes'].update(set(READ_SCOPES)|set(WRITE_SCOPES))
    runtime = module(); source = original.input_resolver.directory; source_before = tree(source)
    config, digest = runtime.export_runtime(original, raw, tmp_path/'private-runtime')
    document = json.loads(config.read_bytes()); config_raw = config.read_bytes()
    descriptors = len(os.listdir('/proc/self/fd'))
    server, request = runtime.load_runtime(config, digest); assert request==raw
    before = counts(server.binding)
    first = json.loads(server.advance('tenant-1',raw,budget=BUDGET))
    current, first_cp = checkpoint(server,raw,monkeypatch)
    assert first==current and first['status']=='yielded'
    history = files(server.directory)
    killed = run_worker(runtime,config,digest,tmp_path,'fresh-runtime-killed',kill_after_recovery=True)
    assert killed['exit_code']==-9 and not killed['same_primary_alive_after']
    assert len(killed['records'])==1 and killed['records'][0]['checkpoint']==first_cp
    assert killed['records'][0]['RHS_calls']==killed['records'][0]['delta_QC_calls']==0
    assert files(server.directory)==history
    resumed = run_worker(runtime,config,digest,tmp_path,'fresh-runtime-resumed',advance=True)
    assert resumed['exit_code']==0 and not resumed['same_primary_alive_after']
    assert resumed['records'][0]['checkpoint']==first_cp
    final = resumed['records'][-1]
    assert final['stage']=='result' and final['actual_RHS_calls']>0
    second, second_cp = checkpoint(server,raw,monkeypatch)
    assert final['progress']==second and final['checkpoint']==second_cp and second['status']=='yielded'
    assert second['steps']>first['steps'] and second['commit_count']==2
    control_root = tmp_path/'continuous-control'; control_root.mkdir(mode=0o700)
    control = custody.CalculationServerCustody(server.binding,control_root,
        input_resolver=runtime.Resolver(document['input'],document['resolver_version']),integrity_key=server.integrity_key)
    control.advance('tenant-1',raw,budget=BUDGET)
    assert checkpoint(control,raw,monkeypatch)[1]==first_cp
    control.advance('tenant-1',raw,budget=BUDGET)
    assert checkpoint(control,raw,monkeypatch)[1]==second_cp
    selected = {}
    with server._open('tenant-1',raw,False) as journal:
        head,_ = journal.writer._head()
        _, _, summary, index, total = journal.writer._load_prefix(journal.context,journal.notice,head)
        for kind in ('samples','events'):
            selected[kind] = [r for descriptor in index[kind] for r in journal.writer._records(
                [{k:v for k,v in descriptor.items() if k!='start'}])[0]]
    with control._open('tenant-1',raw,False) as journal:
        head,_ = journal.writer._head()
        _, _, _, index, _ = journal.writer._load_prefix(journal.context,journal.notice,head)
        for kind in selected:
            expected = [r for descriptor in index[kind] for r in journal.writer._records(
                [{k:v for k,v in descriptor.items() if k!='start'}])[0]]
            assert selected[kind]==expected
    with pytest.raises(custody.CalculationCustodyHold):
        CalculationCycleCropResultStore(server,integrity_key=DB_KEY).put('tenant-1',raw)
    history = files(server.directory)
    for name in ('rights','principal'):
        path = Path(document[name+'_file']); original_bytes=path.read_bytes(); value=json.loads(original_bytes)
        if name=='rights': value['allowed']=False
        else: value['scopes'].remove('crop_result_read')
        rewrite(path,_canonical(value))
        try:
            denied = run_worker(runtime,config,digest,tmp_path,'fresh-runtime-'+name+'-denied',advance=True)
            assert denied['exit_code']==71 and [r['stage'] for r in denied['records']]==['error']
        finally: rewrite(path,original_bytes)
    path = Path(document['keys']['server']); original_bytes=path.read_bytes()
    rewrite(path,bytes([original_bytes[0]^1])+original_bytes[1:])
    try:
        calls=[]
        with monkeypatch.context() as no_assembly:
            no_assembly.setattr(runtime,'_assemble',lambda *_:calls.append(True))
            with pytest.raises(ValueError): runtime.load_runtime(config,digest)
        assert calls==[]
    finally: rewrite(path,original_bytes)
    assert files(server.directory)==history and config.read_bytes()==config_raw
    assert counts(server.binding)==before and tree(source)==source_before
    assert runtime.load_runtime(config,digest)[1]==raw
    assert server.input_resolver.last.reader.closed and not server.input_resolver.last._cache
    assert control.input_resolver.last.reader.closed and not control.input_resolver.last._cache
    assert len(os.listdir('/proc/self/fd'))==descriptors
    save('registered-runtime-verified.json',{'version':runtime.VERSION,'scope':'owned_synthetic_small_same_DB_fresh_exec_only',
        'config_sha256':digest,'first_progress':first,'second_progress':second,
        'first_checkpoint_sha256':first_cp['checkpoint_sha256'],'second_checkpoint_sha256':second_cp['checkpoint_sha256'],
        'fresh_recovery_checkpoint_exact':True,'killed_worker_exit_code':-9,'resumed_worker_exit_code':0,
        'kill_point':'after_authenticated_recovery_before_new_RHS_not_mid_calculation',
        'same_DB_farm_and_continuous_control_checkpoint_rows_match':True,'counts':total,
        'row_sha256':{k:sha256(b''.join(_canonical(row)+b'\n' for row in v)).hexdigest() for k,v in selected.items()},
        'current_input_rights_and_read_scope_denied':True,'static_key_tamper_denied_before_assembly':True,
        'yielded_publication_held':True,'database_counts_before_after':[list(before),list(counts(server.binding))],
        'source_inputs_and_selected_history_preserved':True,'FD_before_after':[descriptors,descriptors],
        'bounded_resolver_contexts_closed':True,'durable_supervisor_deadline_cancel_RSS_not_accepted':True,
        'whole166_registered_accepted':False,'actual_product_CLI_or_independent_G1_accepted':False,
        'gates':'not_assessed','forecast_and_ranking':'hold'})
