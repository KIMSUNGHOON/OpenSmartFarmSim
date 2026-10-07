"""Current SCRAM farm authority around separately verified stored crop queries."""
from hashlib import sha256
from copy import deepcopy
import json
import multiprocessing
import os
from pathlib import Path
from time import perf_counter

import psycopg
from psycopg import sql

import pytest

from app import crop_cycle_calculation_current_query as query
from app import crop_cycle_calculation_result_store as storage
from app import crop_cycle_calculation_server_custody as custody
from app import crop_cycle_input_stream as inputs
from app import crop_cycle_calculation_context as engine
from app import crop_cycle_calculation_artifact as artifact
from app import crop_cycle_calculation_result_read_context as result_read
from app.thermal_run_store import _canonical
from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
from test_crop_cycle_calculation_farm_binding import setup as bound_setup
from test_crop_cycle_calculation_result_store_farms import DB_KEY,fresh,counts,login_scope,original_login_scope
from test_crop_cycle_calculation_server_custody_farms import server_setup, BUDGET
from test_farm_authoring_storage import authoring
from test_farm_replay_scenario import farm_setup
from login_database import login_database

pytestmark=pytest.mark.parametrize('original_login_scope',[{'market_calculation':True,
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


RESULT_KEY=b'own-verified-query-result-key-000001'


def save_reference(name,value):
    destination=os.environ.get('OSSF_CALCULATION_QUERY_EVIDENCE')
    if destination:
        with (Path(destination)/name).open('x') as handle:
            os.fchmod(handle.fileno(),0o400)
            json.dump(value,handle,sort_keys=True);handle.write('\n');handle.flush();os.fsync(handle.fileno())


def authority(issuer,key=RESULT_KEY):
    return CalculationResultEvidenceAuthority(issuer,integrity_key=key,
        issuer_id='owned-verified-current-query',key_id='result-v1')


class OwnEvidenceResolver:
    version='owned-verified-current-cycle-query-evidence-v1'
    def __init__(self, values):self.values=values
    def __call__(self, tenant, packet):
        assert tenant=='tenant-1'
        return dict(self.values)


@pytest.fixture
def prepared(server_setup,request):
    server, raw, rights, principal, expected=server_setup
    started=perf_counter()
    progress=json.loads(server.advance('tenant-1',raw,budget=BUDGET))
    calculation_seconds=perf_counter()-started
    store=storage.CalculationCycleCropResultStore(server,integrity_key=DB_KEY)
    started=perf_counter()
    record=store.put('tenant-1',raw);packet=json.loads(record['payload_raw'])
    publication_seconds=perf_counter()-started
    directory=server.input_resolver.directory
    for path in directory.iterdir():path.chmod(0o400)
    issuer=authority(server.binding.input_authority);input_raw=server.input_resolver.proof
    result_directory=server.directory/custody._intent_id('tenant-1',json.loads(raw))/'artifact'
    started=perf_counter()
    result_raw=issuer.issue(result_directory,progress['artifact_sha256'],directory,packet['input_root_sha256'],input_raw)
    issue_seconds=perf_counter()-started
    resolver=OwnEvidenceResolver({'input_directory':directory,'input_evidence_raw':input_raw,'result_evidence_raw':result_raw})
    service=query.CalculationCurrentCycleQuery(store,issuer,evidence_resolver=resolver)
    save_reference(request.node.name+'.setup.json',{
        'calculation_seconds':calculation_seconds,'publication_seconds':publication_seconds,
        'result_proof_issue_seconds':issue_seconds,'input_proof_sha256':sha256(input_raw).hexdigest(),
        'result_proof_sha256':sha256(result_raw).hexdigest(),
        'calculation_context_sha256':packet['binding']['input']['input_validation']['context_sha256'],
        'original_validated_context_sha256':packet['binding']['input']['input_validation']['validated_context_sha256'],
        'status':progress['status'],'steps':progress['steps'],'counts':progress['counts'],
        'input_fields':len(packet['binding']['input']),
        'validation_fields':len(packet['binding']['input']['input_validation'])})
    return service,record,json.loads(raw)['farm'],rights,principal,expected


def forbid_calculation(monkeypatch):
    def forbidden(*a,**k):pytest.fail('current query repeated parser/context/QC/RHS')
    for module,name in ((inputs,'open_input_packet'),(engine.legacy,'prepare_context'),(engine,'open_calculation_context'),(engine,'advance_chunk'),(artifact._Files,'_load_prefix'),(artifact,'_validate_delta'),
            (artifact,'open_artifact'),(engine.short._Evaluator,'rhs'),(custody.CalculationServerCustody,'_open'),
            (custody._Journal,'__init__')):
        monkeypatch.setattr(module,name,forbidden)


def test_actual_registered_original_result_pages_and_current_provenance_without_math(prepared,monkeypatch):
    service,record,farm,_,_,expected=prepared;forbid_calculation(monkeypatch)
    before=len(os.listdir('/proc/self/fd'));db_before=counts(service.store.server.binding)
    def inventory():
        return {str(path):(sha256(path.read_bytes()).hexdigest(),path.stat().st_mode&0o777,path.stat().st_ino)
            for directory in (service.store.server.directory,service.evidence_resolver.values['input_directory'])
            for path in directory.rglob('*') if path.is_file()}
    files_before=inventory()
    started=perf_counter();value=service.read('tenant-1',record['result_id'],farm)
    summary_seconds=perf_counter()-started;page_seconds={}
    assert value['record']==record and value['page'] is None
    assert value['terminal']['steps']==expected['steps'] and value['terminal']['status']=='completed'
    assert value['identity']['query_version']==query.VERSION
    assert value['identity']['query_code_sha256']==query.CODE_SHA256
    assert value['identity']['math_context_sha256']==engine._hash(value['terminal']['manifest'])
    assert value['identity']['original_binding_sha256']==sha256(_canonical(json.loads(record['payload_raw'])['binding'])).hexdigest()
    assert value['identity']['rights_or_gate_approval'] is False
    packet=json.loads(record['payload_raw'])
    original_summary=json.loads(service.evidence_resolver.values['result_evidence_raw'])['payload']['summary']
    assert value['terminal']=={key:original_summary[key] for key in value['terminal']}
    assert value['identity']['input_evidence_sha256']==packet['binding']['input']['input_validation']['evidence_sha256']
    for kind in ('samples','events'):
        started=perf_counter();page=service.read('tenant-1',record['result_id'],farm,kind=kind)['page']
        page_seconds[kind]=perf_counter()-started
        assert _canonical(page['records'])==_canonical(expected[kind]) and page['next']==page['total']
    assert counts(service.store.server.binding)==db_before and len(os.listdir('/proc/self/fd'))==before
    assert inventory()==files_before
    with service.store.jobs.connect() as conn:assert conn.pgconn.used_password
    save_reference('normal-query.json',{'summary_seconds':summary_seconds,'page_seconds':page_seconds,
        'actual_scram':True,'steps':value['terminal']['steps'],
        'counts':{kind:len(expected[kind]) for kind in ('samples','events')},'identity':value['identity'],
        'read_equations_forbidden':True,'fd_before':before,'fd_after':len(os.listdir('/proc/self/fd')),
        'database_counts_unchanged':True,'all_original_pages_equal':True,
        'custody_and_input_files_SHA_mode_inode_unchanged':True,'files_checked':len(files_before)})


def test_missing_id_returns_none_but_invalid_id_or_foreign_tenant_denies(prepared):
    service,record,farm,*_=prepared
    assert service.read('tenant-1',storage.VERSION+':'+'0'*64,farm) is None
    with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1','invalid',farm)
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
                with pytest.raises((query.CalculationCurrentCycleQueryHold,PermissionError)):
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
            with pytest.raises(query.CalculationCurrentCycleQueryHold):
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
    original=result_read.CalculationResultReadContext.page
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
            patch.setattr(result_read.CalculationResultReadContext,'page',changed)
            before=len(os.listdir('/proc/self/fd'))
            try:
                with pytest.raises((query.CalculationCurrentCycleQueryHold,PermissionError)):
                    service.read('tenant-1',record['result_id'],farm,kind='samples')
                assert calls==[True] and len(os.listdir('/proc/self/fd'))==before,change
            finally:
                rights.allowed=True;principal['scopes']=scopes
                if not target.exists():target.write_bytes(raw);target.chmod(0o400)
        assert service.read('tenant-1',record['result_id'],farm)['record']==record
    before=len(os.listdir('/proc/self/fd'))
    try:
        with pytest.raises(query.CalculationCurrentCycleQueryHold):
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
            with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
            assert len(os.listdir('/proc/self/fd'))==before
        finally:
            with owner.connect() as conn:
                conn.execute(sql.SQL('UPDATE {} SET {}=%s WHERE result_id=%s').format(table,sql.Identifier(column)),
                    (old,record['result_id']))
                conn.execute(sql.SQL('ALTER TABLE {} ENABLE TRIGGER USER').format(table))
        assert service.read('tenant-1',record['result_id'],farm)['record']==record


def restarted_read(service,result_id,farm,queue):
    try:
        restarted=query.CalculationCurrentCycleQuery(fresh(service.store),authority(service.store.server.binding.input_authority),evidence_resolver=service.evidence_resolver)
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
    with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
    assert len(calls)==2 and len(os.listdir('/proc/self/fd'))==before


def test_query_declarations_and_authority_mixing_are_rejected(prepared,monkeypatch):
    from app import crop_cycle_result_evidence as old_evidence
    from app import crop_cycle_result_store as old_storage
    from app.crop_cycle_input_evidence import InputEvidenceAuthority
    service,record,farm,*_=prepared;forbid_calculation(monkeypatch)
    issuer=service.authority.input_authority
    for name,value in (('VERSION','unreviewed-query-v2'),('CODE_SHA256','0'*64),
            ('DEPENDENCY_SHA256',{**query.DEPENDENCY_SHA256,'result_read_context':'0'*64})):
        with monkeypatch.context() as patch:
            patch.setattr(query,name,value)
            with pytest.raises(query.CalculationCurrentCycleQueryHold):
                query.CalculationCurrentCycleQuery(service.store,service.authority,evidence_resolver=service.evidence_resolver)
    old=old_evidence.ResultEvidenceAuthority(issuer,integrity_key=RESULT_KEY,issuer_id='owned-old-query',key_id='old-v1')
    for store,proof in ((service.store,old),(object.__new__(old_storage.CycleCropResultStore),service.authority)):
        with pytest.raises(query.CalculationCurrentCycleQueryHold):
            query.CalculationCurrentCycleQuery(store,proof,evidence_resolver=service.evidence_resolver)
    for key in (service.store.integrity_key,service.store.server.integrity_key):
        with pytest.raises(query.CalculationCurrentCycleQueryHold):
            query.CalculationCurrentCycleQuery(service.store,authority(issuer,key),evidence_resolver=service.evidence_resolver)
    duplicate=InputEvidenceAuthority(issuer.profiles,issuer.notice_raw,integrity_key=service.store.integrity_key,
        issuer_id='owned-duplicate-input',key_id='input-v1')
    with pytest.raises(query.CalculationCurrentCycleQueryHold):
        query.CalculationCurrentCycleQuery(service.store,authority(duplicate),evidence_resolver=service.evidence_resolver)
    for kwargs in ({'kind':'unknown'},{'kind':None,'start':True},{'kind':None,'limit':1},
            {'kind':'samples','start':True},{'kind':'events','limit':9},{'kind':'samples','limit':65}):
        with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm,**kwargs)
    before=len(os.listdir('/proc/self/fd'))
    original=OwnEvidenceResolver.__call__
    def mutate(self,tenant,packet):
        value=original(self,tenant,packet);packet['binding']['input']['program_id']='changed';return value
    with monkeypatch.context() as patch:
        patch.setattr(OwnEvidenceResolver,'__call__',mutate)
        with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
    assert len(os.listdir('/proc/self/fd'))==before
    assert service.read('tenant-1',record['result_id'],farm)['record']==record


def test_valid_HMAC_wrong_validation_and_parent_trace_reject(prepared,monkeypatch):
    service,record,farm,*_=prepared;forbid_calculation(monkeypatch)
    original=service.store._find
    row=original('tenant-1',result_id=record['result_id'])
    for field in ('context_sha256','evidence_sha256','validated_context_sha256'):
        changed=deepcopy(row);packet=json.loads(changed['payload_raw'])
        packet['binding']['input']['input_validation'][field]='0'*64
        if field=='context_sha256':packet['policies']['server_progress']['context_sha256']='0'*64
        packet['policies']['server_progress']['binding_sha256']=sha256(_canonical(packet['binding'])).hexdigest()
        packet['result_id']=storage.VERSION+':'+sha256(_canonical({k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
        changed['result_id']=packet['result_id']
        changed['payload_raw']=_canonical(packet);changed['payload_sha256']=sha256(changed['payload_raw']).hexdigest()
        changed['integrity_signature']=service.store._signature(changed['payload_raw'])
        assert storage._decode(changed['payload_raw'])==packet
        with monkeypatch.context() as patch:
            patch.setattr(service.store,'_find',lambda *a,**k:deepcopy(changed))
            with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',changed['result_id'],farm)
    packet=json.loads(record['payload_raw']);progress=packet['policies']['server_progress']
    intent=service.store.server.directory/custody._intent_id('tenant-1',packet['binding']['request'])
    selected=intent/'proofs'/(progress['head_sha256']+'.json')
    parent=json.loads(selected.read_bytes())['payload']['parent']['head_sha256']
    assert parent
    for target in (selected,intent/'proofs'/(parent+'.json')):
        raw=target.read_bytes();signed=json.loads(raw)
        signed['payload']['binding_sha256']='0'*64
        tampered=custody._signed(signed['payload'],service.store.server.integrity_key,custody.PROOF_DOMAIN)
        try:
            target.chmod(0o600);target.write_bytes(tampered);target.chmod(0o400)
            before=len(os.listdir('/proc/self/fd'))
            with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
            assert len(os.listdir('/proc/self/fd'))==before
        finally:target.chmod(0o600);target.write_bytes(raw);target.chmod(0o400)
    values=service.evidence_resolver.values;original_input=values['input_evidence_raw']
    rebound=deepcopy(json.loads(original_input));rebound['payload']['validated_at']='2026-01-01T00:00:00Z'
    rebound['hmac_sha256']=service.authority.input_authority._signature(rebound['payload'])
    reissued=_canonical(rebound)
    assert reissued!=original_input
    issuer=service.authority.input_authority
    assert issuer.verify(values['input_directory'],packet['input_root_sha256'],reissued).context==issuer.verify(
        values['input_directory'],packet['input_root_sha256'],original_input).context
    try:
        values['input_evidence_raw']=reissued
        with pytest.raises(query.CalculationCurrentCycleQueryHold):service.read('tenant-1',record['result_id'],farm)
    finally:values['input_evidence_raw']=original_input
    assert service.read('tenant-1',record['result_id'],farm)['record']==record


@pytest.mark.parametrize('mode',['completed-events','numeric-hold'])
def test_actual_nonempty_events_and_numeric_hold_keep_original_confirmed_past(server_setup,tmp_path,monkeypatch,mode):
    from test_crop_startup_result_store import shifted
    from test_crop_cycle_artifact import PROFILES
    from test_crop_cycle_calculation_server_custody_farms import OwnInputResolver,KEY
    from app import crop_plant_startup_integration as original
    base,raw,rights,_,_=server_setup
    program=shifted('full-removal-reentry')
    if mode=='numeric-hold':program['events'][1]['removals']['values']['leaf']['value']=1e6
    expected=original.integrate_plant_startup(**program,**PROFILES)
    assert expected['events'] and expected['status']==('hold' if mode=='numeric-hold' else 'completed')
    anchors=program.pop('output_times');directory=tmp_path/'event-inputs'
    root=inputs.write_input_packet(directory,**program,anchors=anchors,outputs=anchors,**PROFILES,program_id='owned-event-query')['root_sha256']
    for path in directory.iterdir():path.chmod(0o400)
    input_raw=base.binding.input_authority.issue(directory,root)
    body=json.loads(raw);body['input'].update(root_sha256=root,program_id='owned-event-query');body['rights']['input_root_sha256']=root
    server_root=tmp_path/'event-server';server_root.mkdir(mode=0o700)
    resolver=OwnInputResolver(directory,root,input_raw)
    server=custody.CalculationServerCustody(base.binding,server_root,input_resolver=resolver,integrity_key=KEY)
    progress=json.loads(server.advance('tenant-1',_canonical(body),budget=BUDGET))
    store=storage.CalculationCycleCropResultStore(server,integrity_key=DB_KEY);record=store.put('tenant-1',_canonical(body))
    issuer=authority(base.binding.input_authority)
    result_directory=server_root/custody._intent_id('tenant-1',body)/'artifact'
    result_raw=issuer.issue(result_directory,progress['artifact_sha256'],directory,root,input_raw)
    service=query.CalculationCurrentCycleQuery(store,issuer,evidence_resolver=OwnEvidenceResolver({
        'input_directory':directory,'input_evidence_raw':input_raw,'result_evidence_raw':result_raw}))
    forbid_calculation(monkeypatch);before=len(os.listdir('/proc/self/fd'));db_before=counts(server.binding)
    started=perf_counter();value=service.read('tenant-1',record['result_id'],body['farm']);seconds={'summary':perf_counter()-started}
    assert value['terminal']['status']==expected['status'] and value['terminal']['steps']==expected['steps']
    if mode=='numeric-hold':
        assert expected['last_confirmed'] is not None
        for key in ('hold','last_confirmed'):assert _canonical(value['terminal'][key])==_canonical(expected[key])
    for kind in ('samples','events'):
        started=perf_counter();page=service.read('tenant-1',record['result_id'],body['farm'],kind=kind)['page']
        seconds[kind]=perf_counter()-started
        assert _canonical(page['records'])==_canonical(expected[kind]) and page['next']==page['total']
    assert len(os.listdir('/proc/self/fd'))==before and counts(server.binding)==db_before
    assert all(context.reader.closed for context in resolver.opened)
    save_reference(mode+'-query.json',{'status':expected['status'],'steps':expected['steps'],
        'counts':{kind:len(expected[kind]) for kind in ('samples','events')},'seconds':seconds,
        'same_original_confirmed_past_and_events':True,'RHS_parser_context_QC_forbidden':True,
        'all_resolved_contexts_closed':True,'database_counts_unchanged':True,'fd_before':before,
        'fd_after':len(os.listdir('/proc/self/fd')),'identity':value['identity']})
