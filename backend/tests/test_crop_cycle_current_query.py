"""Current SCRAM farm authority around separately verified stored crop queries."""
from hashlib import sha256
import json
import multiprocessing
import os
from pathlib import Path

import psycopg
from psycopg import sql

import pytest

from app import crop_cycle_current_query as query
from app import crop_cycle_result_store as storage
from app import crop_cycle_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_stream_execution as engine
from app import crop_cycle_artifact as artifact
from app import crop_cycle_result_read_context as result_read
from app.thermal_run_store import _canonical
from test_crop_cycle_result_evidence import authority
from test_crop_cycle_result_store_farms import DB_KEY,fresh
from test_crop_cycle_server_custody_farms import server_setup, BUDGET
from test_crop_cycle_farm_binding import counts
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database, login_scope

pytestmark=pytest.mark.parametrize('login_scope',[{'market_calculation':True,
    'market_source_storage':True,'thermal_scenario_storage':True,'break_even_calculation':True,
    'crop_cycle_result_storage':True}],indirect=True)


@pytest.fixture(scope='module',autouse=True)
def audit_query_cleanup(login_database,tmp_path_factory):
    yield
    with psycopg.connect(login_database['admin']) as conn:
        schemas=conn.execute("SELECT count(*) FROM pg_namespace WHERE nspname ~ '^login_test_'").fetchone()[0]
        roles=conn.execute("SELECT count(*) FROM pg_roles WHERE rolname ~ '^login_(owner_|[0-9a-f]{32}_)'").fetchone()[0]
        directory=Path(conn.execute('SHOW data_directory').fetchone()[0])
    secrets=list(tmp_path_factory.getbasetemp().rglob('*.pgpass'))
    assert schemas==roles==len(secrets)==0
    destination=os.environ.get('OSSF_CURRENT_QUERY_CLEANUP_REFERENCE')
    if destination:
        value={'schemas_after':schemas,'roles_after':roles,'passfiles_after':len(secrets),
            'pg_pid':int((directory/'postmaster.pid').read_text().splitlines()[0]),
            'private_pg_directory':str(directory)}
        with Path(destination).open('x') as handle:json.dump(value,handle,sort_keys=True);handle.write('\n')
        Path(destination).chmod(0o400)


class OwnEvidenceResolver:
    version='owned-current-cycle-query-evidence-v1'
    def __init__(self, values):self.values=values
    def __call__(self, tenant, packet):
        assert tenant=='tenant-1'
        return dict(self.values)


@pytest.fixture
def prepared(server_setup):
    server, raw, rights, principal, expected=server_setup
    progress=json.loads(server.advance('tenant-1',raw,budget=BUDGET))
    store=storage.CycleCropResultStore(server,integrity_key=DB_KEY)
    record=store.put('tenant-1',raw);packet=json.loads(record['payload_raw'])
    directory=server.input_resolver.directory
    for path in directory.iterdir():path.chmod(0o400)
    issuer=authority();input_raw=issuer.input_authority.issue(directory,packet['input_root_sha256'])
    result_directory=server.directory/custody._intent_id('tenant-1',json.loads(raw))/'artifact'
    result_raw=issuer.issue(result_directory,progress['artifact_sha256'],directory,packet['input_root_sha256'],input_raw)
    resolver=OwnEvidenceResolver({'input_directory':directory,'input_evidence_raw':input_raw,'result_evidence_raw':result_raw})
    service=query.CurrentCycleQuery(store,issuer,evidence_resolver=resolver)
    return service,record,json.loads(raw)['farm'],rights,principal,expected


def forbid_calculation(monkeypatch):
    def forbidden(*a,**k):pytest.fail('current query repeated parser/context/QC/RHS')
    for module,name in ((inputs,'open_input_packet'),(engine,'prepare_context'),
            (artifact,'open_artifact'),(engine.short._Evaluator,'rhs'),(custody.CycleServerCustody,'_open')):
        monkeypatch.setattr(module,name,forbidden)


def test_actual_registered_original_result_pages_and_current_provenance_without_math(prepared,monkeypatch):
    service,record,farm,_,_,expected=prepared;forbid_calculation(monkeypatch)
    before=len(os.listdir('/proc/self/fd'));db_before=counts(service.store.server.binding)
    value=service.read('tenant-1',record['result_id'],farm)
    assert value['record']==record and value['page'] is None
    assert value['terminal']['steps']==expected['steps'] and value['terminal']['status']=='completed'
    assert value['identity']['query_version']==query.VERSION
    assert value['identity']['query_code_sha256']==query.CODE_SHA256
    assert value['identity']['math_context_sha256']==engine._hash(value['terminal']['manifest'])
    assert value['identity']['original_binding_sha256']==sha256(_canonical(json.loads(record['payload_raw'])['binding'])).hexdigest()
    assert value['identity']['rights_or_gate_approval'] is False
    for kind in ('samples','events'):
        page=service.read('tenant-1',record['result_id'],farm,kind=kind)['page']
        assert _canonical(page['records'])==_canonical(expected[kind]) and page['next']==page['total']
    assert counts(service.store.server.binding)==db_before and len(os.listdir('/proc/self/fd'))==before
    with service.store.jobs.connect() as conn:assert conn.pgconn.used_password


def test_missing_id_returns_none_but_invalid_id_or_foreign_tenant_denies(prepared):
    service,record,farm,*_=prepared
    assert service.read('tenant-1',storage.VERSION+':'+'0'*64,farm) is None
    with pytest.raises(query.CurrentCycleQueryHold):service.read('tenant-1','invalid',farm)
    with pytest.raises(PermissionError):service.read('foreign',record['result_id'],farm)


def test_current_authority_withdrawals_reject_without_leaking_FD(prepared,monkeypatch):
    service,record,farm,rights,principal,_=prepared;forbid_calculation(monkeypatch)
    binding=service.store.server.binding
    for change in ('input-rights','source-rights','scope','account','registration','rights-mutation','resolver-version','farm'):
        original_scopes=set(principal['scopes']);tenant=principal['tenant_id']
        with monkeypatch.context() as patch:
            ref=farm
            if change=='input-rights':rights.allowed=False
            elif change=='source-rights':patch.setattr(binding.farms.replay.candidates._source._source,'get_input_rights',lambda *_:None)
            elif change=='scope':principal['scopes'].remove('crop_result_read')
            elif change=='account':principal['tenant_id']='foreign'
            elif change=='registration':patch.setattr(binding.farms,'_find',lambda *_:None)
            elif change=='resolver-version':patch.setattr(service.evidence_resolver,'version','changed-v2')
            elif change=='rights-mutation':
                def changed(self,tenant,declaration,root,use):declaration['revision']='changed';return True
                patch.setattr(type(rights),'__call__',changed)
            else:ref={**farm,'crop_id':'other'}
            before=len(os.listdir('/proc/self/fd'))
            try:
                with pytest.raises((query.CurrentCycleQueryHold,PermissionError)):
                    service.read('tenant-1',record['result_id'],ref)
                assert len(os.listdir('/proc/self/fd'))==before,change
            finally:
                rights.allowed=True;principal['scopes']=original_scopes;principal['tenant_id']=tenant
        assert service.read('tenant-1',record['result_id'],farm)['record']==record


def test_actual_custody_trace_and_physical_tampering_reject(prepared,monkeypatch,tmp_path):
    service,record,farm,*_=prepared;forbid_calculation(monkeypatch)
    packet=json.loads(record['payload_raw']);progress=packet['policies']['server_progress']
    intent=service.store.server.directory/custody._intent_id('tenant-1',packet['binding']['request'])
    selected=intent/'proofs'/(progress['head_sha256']+'.json')
    parent=json.loads(selected.read_bytes())['payload']['parent']['head_sha256']
    targets={'intent':intent/'intent.json','selected-proof':selected,
        'parent-proof':intent/'proofs'/(parent+'.json'),'HEAD':intent/'artifact'/'HEAD',
        'input':service.evidence_resolver.values['input_directory']/'root.json',
        'result':intent/'artifact'/(progress['artifact_sha256']+'.json'),
        'proof-missing':selected,'proof-symlink':selected}
    for change,target in targets.items():
        raw=target.read_bytes();before=len(os.listdir('/proc/self/fd'));moved=tmp_path/'outside-proof'
        try:
            if change=='proof-missing':target.unlink()
            elif change=='proof-symlink':target.rename(moved);target.symlink_to(moved)
            else:target.chmod(0o600);target.write_bytes(raw+b' ');target.chmod(0o400)
            with pytest.raises(query.CurrentCycleQueryHold):
                service.read('tenant-1',record['result_id'],farm,kind='samples')
            assert len(os.listdir('/proc/self/fd'))==before,change
        finally:
            if target.is_symlink():target.unlink();moved.rename(target)
            else:
                if target.exists():target.chmod(0o600)
                target.write_bytes(raw);target.chmod(0o400)
        assert service.read('tenant-1',record['result_id'],farm)['record']==record


def test_withdrawal_after_page_preparation_cannot_return(prepared,monkeypatch):
    service,record,farm,rights,principal,_=prepared;forbid_calculation(monkeypatch)
    original=result_read.ResultReadContext.page
    packet=json.loads(record['payload_raw']);intent=service.store.server.directory/custody._intent_id('tenant-1',packet['binding']['request'])
    target=intent/'intent.json';raw=target.read_bytes()
    for change in ('rights','scope','row','trace'):
        calls=[];scopes=set(principal['scopes'])
        with monkeypatch.context() as patch:
            def changed(self,*a,**k):
                page=original(self,*a,**k);calls.append(True)
                if change=='rights':rights.allowed=False
                elif change=='scope':principal['scopes'].remove('crop_result_read')
                elif change=='row':patch.setattr(service.store,'_find',lambda *a,**k:None)
                else:target.unlink()
                return page
            patch.setattr(result_read.ResultReadContext,'page',changed)
            before=len(os.listdir('/proc/self/fd'))
            try:
                with pytest.raises((query.CurrentCycleQueryHold,PermissionError)):
                    service.read('tenant-1',record['result_id'],farm,kind='samples')
                assert calls==[True] and len(os.listdir('/proc/self/fd'))==before,change
            finally:
                rights.allowed=True;principal['scopes']=scopes
                if not target.exists():target.write_bytes(raw);target.chmod(0o400)
        assert service.read('tenant-1',record['result_id'],farm)['record']==record
    before=len(os.listdir('/proc/self/fd'))
    try:
        with pytest.raises(query.CurrentCycleQueryHold):
            with service.open('tenant-1',record['result_id'],farm) as value:
                assert value['record']==record;rights.allowed=False
    finally:rights.allowed=True
    assert len(os.listdir('/proc/self/fd'))==before


def test_actual_DB_signature_and_column_tampering_reject(prepared,login_scope,monkeypatch):
    service,record,farm,*_=prepared;forbid_calculation(monkeypatch)
    owner,_,_=login_scope;table=service.store.jobs._table(storage.schema.TABLE)
    for column,replacement in (('integrity_signature','0'*64),('registered_by','foreign-owner')):
        with owner.connect() as conn:
            old=conn.execute(sql.SQL('SELECT {} FROM {} WHERE result_id=%s').format(sql.Identifier(column),table),
                (record['result_id'],)).fetchone()[column]
            conn.execute(sql.SQL('ALTER TABLE {} DISABLE TRIGGER USER').format(table))
            conn.execute(sql.SQL('UPDATE {} SET {}=%s WHERE result_id=%s').format(table,sql.Identifier(column)),
                (replacement,record['result_id']))
        before=len(os.listdir('/proc/self/fd'))
        try:
            with pytest.raises(query.CurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
            assert len(os.listdir('/proc/self/fd'))==before
        finally:
            with owner.connect() as conn:
                conn.execute(sql.SQL('UPDATE {} SET {}=%s WHERE result_id=%s').format(table,sql.Identifier(column)),
                    (old,record['result_id']))
                conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
        assert service.read('tenant-1',record['result_id'],farm)['record']==record


def restarted_read(service,result_id,farm,queue):
    try:
        restarted=query.CurrentCycleQuery(fresh(service.store),authority(),evidence_resolver=service.evidence_resolver)
        queue.put(restarted.read('tenant-1',result_id,farm,kind='samples'))
    except Exception as exc:queue.put({'error':type(exc).__name__})


def test_fresh_authority_and_fork_process_keep_original_values(prepared,monkeypatch):
    service,record,farm,*_=prepared;forbid_calculation(monkeypatch)
    expected=service.read('tenant-1',record['result_id'],farm,kind='samples')
    context=multiprocessing.get_context('fork');queue=context.Queue()
    process=context.Process(target=restarted_read,args=(service,record['result_id'],farm,queue));process.start()
    try:
        assert queue.get(timeout=60)==expected
        process.join(5);assert process.exitcode==0
    finally:
        if process.is_alive():process.kill();process.join(5)
        queue.close();queue.join_thread()


def test_source_withdrawal_inside_final_input_rights_review_cannot_return(prepared,monkeypatch):
    service,record,farm,rights,_,_=prepared;forbid_calculation(monkeypatch)
    source=service.store.server.binding.farms.replay.candidates._source._source
    original=type(rights).__call__;calls=[]
    def reviewed(self,*args):
        allowed=original(self,*args);calls.append(True)
        if len(calls)==2:monkeypatch.setattr(source,'get_input_rights',lambda *_:None)
        return allowed
    monkeypatch.setattr(type(rights),'__call__',reviewed)
    before=len(os.listdir('/proc/self/fd'))
    with pytest.raises(query.CurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
    assert len(calls)==2 and len(os.listdir('/proc/self/fd'))==before
