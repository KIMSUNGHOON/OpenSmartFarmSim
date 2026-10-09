"""Actual SCRAM farms around server-owned verified research calculations."""
from hashlib import sha256
import json
import os
from pathlib import Path
from time import perf_counter

import pytest

from app import crop_cycle_calculation_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_artifact as artifact
from app import crop_plant_startup_integration as original
from app.thermal_run_store import _canonical
from test_crop_cycle_artifact import PROFILES, NOTICE
from test_crop_cycle_farm_binding import counts
from test_crop_cycle_calculation_farm_binding import setup as bound_setup, final_database_cleanup
from test_crop_startup_result_store import shifted
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope

pytestmark = pytest.mark.parametrize('login_scope', [{'market_calculation': True,
    'market_source_storage': True, 'thermal_scenario_storage': True, 'break_even_calculation': True,
    'crop_cycle_result_storage': True}], indirect=True)
KEY = b'own-verified-cycle-server-farm-key-01'
BUDGET = {'max_steps': 10000, 'max_transitions': 128}


def save_reference(name, value):
    directory = os.environ.get('OSSF_CALCULATION_SERVER_EVIDENCE')
    if directory:
        with (Path(directory) / name).open('x') as f:
            os.fchmod(f.fileno(), 0o400); json.dump(value, f, sort_keys=True, indent=2)
            f.write('\n'); f.flush(); os.fsync(f.fileno())


class OwnInputResolver:
    version = 'own-verified-server-context-resolver-v1'
    def __init__(self, directory, root, proof):
        self.directory, self.root, self.proof = directory, root, proof
        self.opened = []; self.factory_seconds = []
    def __call__(self, root, *, authority):
        assert root == self.root
        started = perf_counter()
        context = engine.open_calculation_context(self.directory, root, self.proof, authority=authority)
        self.factory_seconds.append(perf_counter() - started); self.opened.append(context)
        return context


@pytest.fixture
def server_setup(bound_setup, tmp_path):
    binding, body, _, principal, rights, directory, proof = bound_setup
    expected = original.integrate_plant_startup(**shifted(), **PROFILES)
    root = tmp_path / 'server'; root.mkdir(mode=0o700)
    resolver = OwnInputResolver(directory, body['input']['root_sha256'], proof)
    service = custody.CalculationServerCustody(binding, root, input_resolver=resolver, integrity_key=KEY)
    yield service, _canonical(body), rights, principal, expected
    assert all(c.reader.closed and not c._cache and not c.reader._cache for c in resolver.opened)


def test_actual_scram_registered_farm_signed_server_equations_and_no_rhs_read_retry(server_setup,monkeypatch):
    service,raw,rights,principal,expected=server_setup;before=counts(service.binding)
    measured={'farm_prepare':[],'farm_current':[],'actual_calculation':[],'journal_publish':[]}
    def timed(label, function):
        def call(*args, **kwargs):
            started=perf_counter()
            try:return function(*args, **kwargs)
            finally:measured[label].append(perf_counter()-started)
        return call
    for target,name,label in ((service.binding,'prepare','farm_prepare'),(service.binding,'current','farm_current'),
        (engine,'advance_chunk','actual_calculation'),(custody._Journal,'_publish','journal_publish')):
        monkeypatch.setattr(target,name,timed(label,getattr(target,name)))
    def no_reprepare(*args, **kwargs):pytest.fail('server repeated original input parser/preflight')
    monkeypatch.setattr(inputs,'open_input_packet',no_reprepare)
    monkeypatch.setattr(engine.legacy,'prepare_context',no_reprepare)
    started=perf_counter();progress=service.advance('tenant-1',raw,budget=BUDGET);advance_seconds=perf_counter()-started
    value=json.loads(progress)
    assert value['status']=='completed' and value['scope']=='synthetic_crop_math_only'
    assert value['steps']==expected['steps'] and value['artifact_sha256'] and value['commit_count']==1
    assert counts(service.binding)==before and before[2:]==(0,0)
    fresh=custody.CalculationServerCustody(service.binding,service.directory,input_resolver=service.input_resolver,integrity_key=KEY)
    def forbidden(*args,**kwargs):pytest.fail('completed retry/read must not execute RHS')
    monkeypatch.setattr(engine.short._Evaluator,'rhs',forbidden)
    monkeypatch.setattr(engine,'advance_chunk',forbidden)
    tick=perf_counter();assert fresh.inspect('tenant-1',raw)==progress;inspect_seconds=perf_counter()-tick
    ticks={}
    for kind,limit in (('samples',64),('events',8)):
        tick=perf_counter();page=fresh.page('tenant-1',raw,progress,kind,0,limit);ticks[kind]=perf_counter()-tick
        assert page['next']==page['total'] and _canonical(page['records'])==_canonical(expected[kind])
    assert fresh.advance('tenant-1',raw,budget=BUDGET)==progress
    with service.binding.jobs.connect() as conn:
        assert conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256'
    principal['scopes'].remove('crop_result_read')
    with pytest.raises(PermissionError):fresh.inspect('tenant-1',raw)
    principal['scopes'].add('crop_result_read')
    rights.allowed=False
    with pytest.raises(custody.CalculationCustodyHold):fresh.inspect('tenant-1',raw)
    assert counts(service.binding)==before
    rights.allowed=True; original_page=artifact.ArtifactReader.page
    def withdraw_after_page(*args, **kwargs):
        result=original_page(*args, **kwargs); rights.allowed=False; return result
    monkeypatch.setattr(artifact.ArtifactReader, 'page', withdraw_after_page)
    with pytest.raises(custody.CalculationCustodyHold):fresh.page('tenant-1',raw,progress,'samples',0,1)
    assert counts(service.binding)==before
    save_reference('normal-server.json', {
        'scope':'synthetic_server_farm_custody_software_only','actual_scram':True,
        'progress_bytes':len(progress),'progress_sha256':sha256(progress).hexdigest(),'progress':value,
        'advance_seconds':advance_seconds,'inspect_seconds':inspect_seconds,'page_seconds':ticks,
        'same_fresh_service_bytes':True,'complete_retry_and_reads_rhs_zero':True,
        'current_scope_and_input_withdrawal_held':True,'crop_rows_and_runs':list(before[2:]),'factory_seconds':service.input_resolver.factory_seconds,
        'rights_withdrawn_after_page_prevented_return':True,
        'component_seconds_nested_not_additive':measured,'actual_calculation_calls':len(measured['actual_calculation']),
        'opened_contexts':len(service.input_resolver.opened),'all_resolved_contexts_closed':all(c.reader.closed for c in service.input_resolver.opened)})


def test_actual_registered_input_withdrawn_after_equations_does_not_select_new_head(server_setup,monkeypatch):
    service,raw,rights,_,_=server_setup;before=counts(service.binding);advance=engine.advance_chunk;calls=0
    def withdrawn(*args,**kwargs):
        nonlocal calls
        result=advance(*args,**kwargs);calls+=1;rights.allowed=False;return result
    monkeypatch.setattr(engine,'advance_chunk',withdrawn)
    with pytest.raises(custody.CalculationCustodyHold):service.advance('tenant-1',raw,budget=BUDGET)
    assert calls==1
    where=service.directory/custody._intent_id('tenant-1',json.loads(raw))
    head=json.loads((where/'artifact'/'HEAD').read_bytes())
    assert head['commit_count']==0 and head['artifact_sha256'] is None
    assert len(list((where/'proofs').glob('*.json')))==1
    rights.allowed=True;monkeypatch.setattr(engine,'advance_chunk',advance)
    zero=json.loads(service.inspect('tenant-1',raw));assert zero['commit_count']==zero['steps']==0
    assert counts(service.binding)==before and before[2:]==(0,0)


def test_foreign_tenant_wrong_expected_progress_and_changed_resolver_are_held(server_setup,monkeypatch):
    service,raw,_,_,_=server_setup
    with pytest.raises(PermissionError):service.inspect('foreign',raw)
    progress=service.advance('tenant-1',raw,budget=BUDGET)
    with pytest.raises(custody.CalculationCustodyHold):service.page('tenant-1',raw,progress+b' ','samples',0,1)
    monkeypatch.setattr(service.input_resolver,'version','changed-v2')
    with pytest.raises(custody.CalculationCustodyHold):service.inspect('tenant-1',raw)


def test_rejected_input_reader_subclass_releases_its_descriptor_without_rhs(server_setup,monkeypatch):
    service,raw,_,_,_=server_setup
    class UnsupportedReader(inputs.InputPacket):pass
    def unsupported(self,root,**profiles):
        return UnsupportedReader(self.directory,root,**PROFILES)
    monkeypatch.setattr(OwnInputResolver,'__call__',unsupported)
    before=len(os.listdir('/proc/self/fd'));calls=0;advance=engine.advance_chunk
    def counted(*args,**kwargs):
        nonlocal calls
        calls+=1;return advance(*args,**kwargs)
    monkeypatch.setattr(engine,'advance_chunk',counted)
    with pytest.raises(custody.CalculationCustodyHold):service.advance('tenant-1',raw,budget=BUDGET)
    assert calls==0 and len(os.listdir('/proc/self/fd'))==before


def test_real_root_lock_different_revision_conflict_and_current_source_withdrawal(server_setup,monkeypatch):
    service,raw,_,_,_=server_setup
    directory=custody._open_directory_nofollow(service.directory);lock=custody._file(directory,'.custody-lock',lock=True)
    try:
        with pytest.raises(custody.CalculationCustodyPending):service.advance('tenant-1',raw,budget=BUDGET)
    finally:os.close(lock);os.close(directory)
    service.advance('tenant-1',raw,budget=BUDGET)
    changed=json.loads(raw);changed['rights']['declaration_id']='other-declaration'
    with pytest.raises(custody.CalculationCustodyConflict):service.advance('tenant-1',_canonical(changed),budget=BUDGET)
    source=service.binding.farms.replay.candidates._source._source
    monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
    with pytest.raises(custody.CalculationCustodyHold):service.inspect('tenant-1',raw)


def test_actual_rights_withdrawal_after_proof_does_not_select_head(server_setup, monkeypatch):
    service, raw, rights, _, _ = server_setup; before = counts(service.binding)
    put = custody._immutable; calls = []
    def withdrawn(parent, name, data, maximum, prefix):
        result = put(parent, name, data, maximum, prefix)
        if prefix == '.proof-' and json.loads(data)['payload']['action'] == 'advance':
            rights.allowed = False; calls.append(True)
        return result
    monkeypatch.setattr(custody, '_immutable', withdrawn)
    with pytest.raises(custody.CalculationCustodyHold): service.advance('tenant-1', raw, budget=BUDGET)
    where = service.directory / custody._intent_id('tenant-1', json.loads(raw))
    head = json.loads((where / 'artifact' / 'HEAD').read_bytes())
    assert calls == [True] and head['commit_count'] == 0 and head['artifact_sha256'] is None
    assert len(list((where / 'proofs').glob('*.json'))) == 2
    rights.allowed = True; monkeypatch.setattr(custody, '_immutable', put)
    current = json.loads(service.inspect('tenant-1', raw))
    assert current['steps'] == current['commit_count'] == 0 and counts(service.binding) == before
    save_reference('after-proof-withdrawal.json', {'actual_computation_before_withdrawal': True,
        'selected_commits': 0, 'selected_steps': 0, 'orphan_proofs': 1,
        'rights_restored_inspect_original_zero_head': True, 'crop_rows_and_runs': list(before[2:])})


@pytest.mark.parametrize('kind', ['read-only', 'legacy', 'foreign-authority', 'context-subclass'])
def test_wrong_owned_resolver_contexts_close_without_rhs(server_setup, monkeypatch, kind):
    from dataclasses import fields
    from app.crop_cycle_input_read_context import open_input_read_context
    from test_crop_cycle_input_evidence import authority
    service, raw, *_ = server_setup; resolved = []
    def wrong(self, root, **kwargs):
        if kind == 'read-only':
            c = open_input_read_context(self.directory, root, self.proof, authority=kwargs['authority'])
        elif kind == 'legacy':
            reader = inputs.open_input_packet(self.directory, root, **PROFILES)
            c = engine.legacy.prepare_context(reader, **PROFILES)
        else:
            c = engine.open_calculation_context(self.directory, root, self.proof,
                authority=authority() if kind == 'foreign-authority' else kwargs['authority'])
            if kind == 'context-subclass':
                class Unsupported(engine.CalculationContext): pass
                c = Unsupported(**{f.name: getattr(c, f.name) for f in fields(c)})
        resolved.append(c); return c
    monkeypatch.setattr(OwnInputResolver, '__call__', wrong)
    monkeypatch.setattr(engine, 'advance_chunk', lambda *a, **k: pytest.fail('wrong context RHS'))
    before = len(os.listdir('/proc/self/fd'))
    with pytest.raises(custody.CalculationCustodyHold): service.advance('tenant-1', raw, budget=BUDGET)
    assert len(resolved) == 1 and resolved[0].reader.closed
    assert len(os.listdir('/proc/self/fd')) == before


def test_original_farm_type_and_new_binding_cannot_cross_versions(server_setup, tmp_path):
    from app.crop_cycle_farm_binding import CycleFarmBinding
    from app.crop_cycle_server_custody import CycleServerCustody, CycleCustodyHold
    service, _, rights, *_ = server_setup
    old = CycleFarmBinding(service.binding.farms, **PROFILES, notice_raw=NOTICE, input_rights=rights)
    with pytest.raises(custody.CalculationCustodyHold):
        custody.CalculationServerCustody(old, service.directory, input_resolver=service.input_resolver, integrity_key=KEY)
    with pytest.raises(CycleCustodyHold):
        CycleServerCustody(service.binding, service.directory, input_resolver=service.input_resolver, integrity_key=KEY)
    for budget in (None, {'max_steps': True, 'max_transitions': 1}, {'max_steps': 1, 'max_transitions': 129}):
        with pytest.raises(custody.CalculationCustodyHold): service.advance('tenant-1', b'{}', budget=budget)
    assert not service.input_resolver.opened and not list(service.directory.iterdir())


def test_actual_registered_pause_new_service_restores_exact_checkpoint(server_setup, monkeypatch):
    service, raw, _, _, expected = server_setup; before = counts(service.binding)
    paused_raw = service.advance('tenant-1', raw, budget={'max_steps': 7, 'max_transitions': 11})
    paused = json.loads(paused_raw)
    assert paused['status'] == 'yielded' and 0 < paused['steps'] < expected['steps']
    where = service.directory / custody._intent_id('tenant-1', json.loads(raw))
    head = json.loads((where / 'artifact' / 'HEAD').read_bytes())
    data = (where / 'artifact' / (head['latest_commit_sha256'] + '.json')).read_bytes()
    assert sha256(data).hexdigest() == head['latest_commit_sha256']
    checkpoint = json.loads(data)['result']['checkpoint']; restored = []; advance = engine.advance_chunk
    def resume(context, current, budget):
        assert current == checkpoint; restored.append(True)
        return advance(context, current, budget)
    monkeypatch.setattr(engine, 'advance_chunk', resume)
    fresh = custody.CalculationServerCustody(service.binding, service.directory,
        input_resolver=service.input_resolver, integrity_key=KEY)
    done_raw = fresh.advance('tenant-1', raw, budget=BUDGET); done = json.loads(done_raw)
    assert restored == [True] and done['status'] == 'completed' and done['steps'] == expected['steps']
    monkeypatch.setattr(engine.short._Evaluator, 'rhs', lambda *a, **k: pytest.fail('resume read RHS'))
    for kind, limit in (('samples', 64), ('events', 8)):
        assert fresh.page('tenant-1', raw, done_raw, kind, 0, limit)['records'] == expected[kind]
    assert counts(service.binding) == before and before[2:] == (0, 0)
    save_reference('registered-pause-resume.json', {'actual_scram': True, 'paused_steps': paused['steps'],
        'checkpoint_sha256': checkpoint['checkpoint_sha256'], 'same_checkpoint_vector_clock_counters': True,
        'checkpoint_vector_size': len(checkpoint['y']), 'completed_steps': done['steps'], 'counts': done['counts'],
        'new_service_same_process': True, 'fresh_python_exec': False, 'read_RHS_calls': 0,
        'crop_rows_and_runs': list(before[2:])})
