"""Manual actual SCRAM prefix costs; owned synthetic inputs, no terminal Run."""
from copy import deepcopy
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path
import shutil
from time import perf_counter

import pytest

from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_server_custody as custody
from app.crop_cycle_calculation_farm_binding import CalculationFarmBinding
from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
from app.crop_result_store import READ_SCOPES, WRITE_SCOPES
from app.thermal_run_store import _canonical
from crop_cycle_full_prefix_cost_smoke import packet, original_rows, same_checkpoint_values
from crop_cycle_full_calendar_registration_smoke import audit_registration, farm_setup, authoring, save, POLICY
from crop_cycle_calculation_prefix_cost_smoke import driver, tree
from test_crop_cycle_calculation_result_store_farms import login_scope, original_login_scope, counts
from test_crop_cycle_farm_binding import SyntheticInputRights
from test_crop_cycle_input_evidence import authority
from test_api_crop_cycle_calculation_tls import Inputs, SERVER_KEY, DB_KEY
from test_farm_authoring_storage import request as farm_request
from login_database import login_database

BUDGET = {'max_steps':10000, 'max_transitions':4096}


def measured_advance(server, raw, driver):
    descriptors = len(os.listdir('/proc/self/fd'))
    with server.binding.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth'] == 'scram-sha-256'
    with driver.observation() as costs:
        tick = perf_counter()
        with costs.measure('server.advance'):
            progress = server.advance('tenant-1', raw, budget=BUDGET)
        advance_seconds = perf_counter()-tick
        advance_costs = deepcopy(costs.values)
        rhs_before = costs.values['rhs']['calls']
        tick = perf_counter()
        current, checkpoint = driver._checkpoint(server, 'tenant-1', raw)
        read_seconds = perf_counter()-tick
        assert progress == current and costs.values['rhs']['calls'] == rhs_before
        read_costs = driver._difference(costs.values, advance_costs)
        assert read_costs.get('artifact.delta_qc', {}).get('calls', 0) == 0
        assert read_costs.get('artifact.prefix_verify', {}).get('calls', 0) == 0
        assert read_costs['prefix.current_blob']['successful_bytes'] > 0
    assert len(os.listdir('/proc/self/fd')) == descriptors
    stat = Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()
    return {'progress':json.loads(progress), 'progress_sha256':sha256(progress).hexdigest(),
        'checkpoint':checkpoint, 'advance_seconds':advance_seconds, 'advance_costs':advance_costs,
        'read_seconds':read_seconds, 'read_costs':read_costs, 'read_RHS_calls':0,
        'FD_before_after':[descriptors, descriptors], 'pid':os.getpid(), 'start_ticks':stat[19],
        'actual_scram_used_password':True, 'effective_nice':os.getpriority(os.PRIO_PROCESS, 0),
        'measurement_version':driver.VERSION, 'measurement_code_sha256':sha256(Path(driver.__file__).read_bytes()).hexdigest(),
        'cost_definition':'unchanged_v2_wrappers_nested_times_not_additive_advance_and_read_separated'}


def resumed_child(server, raw, expected, expected_checkpoint, sender, cost_driver):
    try:
        fresh = custody.CalculationServerCustody(server.binding, server.directory,
            input_resolver=server.input_resolver, integrity_key=server.integrity_key)
        rhs = engine.short._Evaluator.rhs
        def forbidden(*args, **kwargs): raise AssertionError('fork recovery ran RHS')
        engine.short._Evaluator.rhs = forbidden
        with cost_driver.observation() as costs:
            current, checkpoint = cost_driver._checkpoint(fresh, 'tenant-1', raw)
            recovery_costs = deepcopy(costs.values)
        assert recovery_costs.get('rhs', {}).get('calls', 0) == 0
        assert recovery_costs.get('artifact.delta_qc', {}).get('calls', 0) == 0
        assert recovery_costs.get('artifact.prefix_verify', {}).get('calls', 0) == 0
        assert recovery_costs['prefix.current_blob']['successful_bytes'] > 0
        assert json.loads(current) == expected and checkpoint == expected_checkpoint
        engine.short._Evaluator.rhs = rhs
        result = measured_advance(fresh, raw, cost_driver)
        result.update(recovered_checkpoint_exact=True, recovery_RHS_calls=0, recovery_costs=recovery_costs,
            fork_only_not_fresh_exec=True)
        assert all(c.reader.closed and not c._cache and not c.reader._cache for c in fresh.input_resolver.opened)
        save('registered-chunk-child.json', result)
        sender.send({'ok':True})
    except BaseException as exc:
        sender.send({'error':type(exc).__name__})
        sender.close(); os._exit(71)
    finally: sender.close()


@pytest.mark.parametrize('original_login_scope', [POLICY], indirect=True)
def test_registered_two_large_chunks_fork_resume_current_rights_and_cost(
        audit_registration, authoring, tmp_path, driver, monkeypatch):
    paths, receipt, proof = packet()
    preserved = {key:tree(paths[key]) for key in ('derived', 'original', 'artifact')}
    prior_path = Path(__file__).resolve().parents[2]/'research/artifacts/crop-cycle-calculation-bounded-chunks-reference-20261008.json'
    prior_raw = prior_path.read_bytes()
    assert sha256(prior_raw).hexdigest() == 'd294aed1c22c7e4df2141b9e566fe63e760d55aab06f9e6b82d3cd7a53f6cf7b'
    farms, farm_body, principal = authoring
    body = deepcopy(farm_body)
    body['farm']['scenario_id'] = body['rights']['scenario_id'] = 'owned-full166-large-chunk-farm'
    body['rights']['declaration_id'] = 'owned-full166-large-chunk-rights'
    body['farm']['crops'][0]['occupancy']['end'] = '2027-03-16T00:00:00Z'
    body['farm']['crops'][0]['release_at'] = '2027-03-17T00:00:00Z'
    registered = farms.submit('tenant-1', farm_request(body))
    principal['scopes'].update(set(READ_SCOPES) | set(WRITE_SCOPES))
    issuer = authority(); rights = SyntheticInputRights(); resolver = Inputs()
    resolver.values[receipt['target_root_sha256']] = (paths['derived'], proof)
    binding = CalculationFarmBinding(farms, issuer, input_rights=rights)
    request = {'study_id':'owned-full166-large-chunk-cost', 'revision':'r1', 'farm':{
        'scenario_id':body['farm']['scenario_id'], 'scenario_revision':body['farm']['scenario_revision'],
        'registration_sha256':registered.scenario_sha256, 'crop_id':'crop-1'},
        'input':{'schema_version':engine.inputs.VERSION, 'root_sha256':receipt['target_root_sha256'],
                 'program_id':receipt['target_program_id']},
        'rights':{'schema_version':'crop-cycle-input-rights-v1', 'declaration_id':'owned-full166-large-input-rights',
            'revision':'r1', 'input_root_sha256':receipt['target_root_sha256'],
            'available_at':body['farm']['decision_at'], 'redistribute':False,
            **{key:True for key in ('ownership_asserted','access','store','transform','use','display')}}}
    raw = _canonical(request); directory = tmp_path/'registered-server'; directory.mkdir(mode=0o700)
    server = custody.CalculationServerCustody(binding, directory, input_resolver=resolver, integrity_key=SERVER_KEY)
    before = counts(binding); descriptors = len(os.listdir('/proc/self/fd')); started = perf_counter()
    first = measured_advance(server, raw, driver)
    assert first['checkpoint'] == json.loads(prior_raw)['stored_prefix']['checkpoint']
    assert first['checkpoint']['sequence'] == 4096 and first['progress']['counts'] == {'samples':105, 'events':2}
    save('registered-chunk-parent.json', first)
    context = multiprocessing.get_context('fork'); receiver, sender = context.Pipe(duplex=False)
    child = context.Process(target=resumed_child, args=(server, raw, first['progress'], first['checkpoint'], sender, driver))
    child.start(); sender.close()
    try:
        assert receiver.poll(240), 'owned fork observation budget expired'
        assert receiver.recv() == {'ok':True}
        child.join(10); assert child.exitcode == 0
        child_pid = child.pid
    finally:
        if child.is_alive(): child.terminate(); child.join(10)
        if child.is_alive(): child.kill(); child.join(10)
        receiver.close(); child.close()
    second = json.loads((Path(os.environ['OSSF_FULL_CALENDAR_EVIDENCE'])/'registered-chunk-child.json').read_bytes())
    assert second['pid'] == child_pid != os.getpid() and second['checkpoint']['sequence'] == 8192
    assert second['progress']['commit_count'] == 2 and second['progress']['status'] == 'yielded'
    for result in (first, second):
        assert result['advance_costs']['artifact.delta_qc']['calls'] == 2
        assert result['advance_costs'].get('artifact.prefix_verify', {}).get('calls', 0) == 0
        assert result['advance_costs']['rhs']['calls'] > 0 and result['read_RHS_calls'] == 0
        assert result['advance_costs']['prefix.current_blob']['successful_bytes'] > 0
        assert result['advance_costs']['farm.current_rights']['calls'] > 0
        assert result['advance_costs']['journal.selected_proof']['calls'] > 0
    immutable = tree(directory)
    with monkeypatch.context() as no_math:
        no_math.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('read/denial RHS'))
        no_math.setattr(engine, 'advance_chunk', lambda *a, **k: pytest.fail('read/denial calculation'))
        with server._open('tenant-1', raw, False) as journal:
            head, _ = journal.writer._head()
            _, checkpoint, summary, index, count = journal.writer._load_prefix(journal.context, journal.notice, head)
            selected = {kind:[] for kind in ('samples', 'events')}
            for kind in selected:
                for descriptor in index[kind]:
                    values, _ = journal.writer._records([{key:value for key,value in descriptor.items() if key != 'start'}])
                    selected[kind].extend(values)
        assert checkpoint == second['checkpoint'] and summary['status'] == 'yielded'
        expected, reference = original_rows(paths, count, advance_count=64)
        assert selected == expected and same_checkpoint_values(checkpoint, reference['shifted_source_checkpoint'])
        current = server.inspect('tenant-1', raw)
        assert json.loads(current) == second['progress']
        with pytest.raises(custody.CalculationCustodyHold): CalculationCycleCropResultStore(server, integrity_key=DB_KEY).put('tenant-1', raw)
        rights.allowed = False
        try:
            with pytest.raises(custody.CalculationCustodyHold): server.inspect('tenant-1', raw)
            with pytest.raises(custody.CalculationCustodyHold): server.advance('tenant-1', raw, budget=BUDGET)
        finally: rights.allowed = True
        principal['scopes'].remove('crop_result_read')
        try:
            with pytest.raises(PermissionError): server.inspect('tenant-1', raw)
        finally: principal['scopes'].add('crop_result_read')
        for kind in ('root', 'block'):
            copied = tmp_path/('tamper-copy-'+kind)
            shutil.copytree(paths['derived'], copied); copied.chmod(0o700)
            resolver.values[receipt['target_root_sha256']] = (copied, proof)
            try:
                assert server.inspect('tenant-1', raw) == current
                target = copied/'root.json' if kind == 'root' else next(p for p in copied.iterdir() if p.name != 'root.json')
                original = target.read_bytes(); metadata = target.stat()
                target.chmod(0o600); target.write_bytes(original[:-1]+(b']' if original[-1:] == b'}' else b'}')); target.chmod(0o400)
                os.utime(target, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))
                with pytest.raises(custody.CalculationCustodyHold): server.inspect('tenant-1', raw)
                with pytest.raises(custody.CalculationCustodyHold): server.advance('tenant-1', raw, budget=BUDGET)
            finally:
                resolver.values[receipt['target_root_sha256']] = (paths['derived'], proof)
                shutil.rmtree(copied)
        assert server.inspect('tenant-1', raw) == current
    assert tree(directory) == immutable and counts(binding) == before
    assert all(preserved[key] == tree(paths[key]) for key in preserved)
    assert prior_path.read_bytes() == prior_raw
    assert all(c.reader.closed and not c._cache and not c.reader._cache for c in resolver.opened)
    assert len(os.listdir('/proc/self/fd')) == descriptors
    save('registered-chunk-cost-verified.json', {'version':'crop-cycle-calculation-registered-chunk-cost-v1',
        'scope':'owned_synthetic_registered_initial8192_prefix_only', 'first':first, 'second':second,
        'reference':reference, 'counts':count, 'child_exit_code':0, 'fork_only_not_fresh_exec':True,
        'row_sha256':{kind:sha256(b''.join(_canonical(row)+b'\n' for row in selected[kind])).hexdigest() for kind in selected},
        'parent_requery_RHS_calls':0, 'yielded_publication_held':True,
        'current_input_root_block_tamper_rights_scope_denials':True, 'selected_history_preserved':True,
        'original_and_derived_files_preserved':True, 'prior_acceptance_preserved':True,
        'database_counts_before_after':[list(before),list(before)], 'FD_before_after':[descriptors,descriptors],
        'all_parent_and_child_contexts_closed_caches_empty':True, 'wall_seconds':perf_counter()-started,
        'whole166day_accepted':False, 'gates':'not_assessed', 'forecast_and_ranking':'hold'})
