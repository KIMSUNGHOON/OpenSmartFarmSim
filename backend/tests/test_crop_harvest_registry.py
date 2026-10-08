from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import secrets
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
import pytest

from app import crop_harvest_registry as registry
from app.runtime_roles import audit_runtime_roles
from test_crop_harvest import (mass_profile, allocation_profile, stored_result, server_setup, bound_setup,
    counts, login_scope, original_login_scope, authoring, farm_setup, login_database, native_cleanup,
    forbid_calculation, save_native)
from login_database import assert_host_scram


def owned_packet():
    parent = registry.current.storage.VERSION+':'+'1'*64
    farm = {'scenario_id':'owned-farm','scenario_revision':'1','registration_sha256':'2'*64,'crop_id':'owned-crop'}
    source = {'result_id':parent,'payload_sha256':'3'*64,'input_root_sha256':'4'*64,
        'artifact_sha256':'5'*64,'math_manifest_sha256':'6'*64,'source_status':'completed'}
    base = registry._base('tenant-1',parent,farm,source,{'mass_sha256':'7'*64,'allocation_sha256':'8'*64})
    raw = registry._packet(base,{'artifact_sha256':'9'*64,'row_count':6,'row_chain_sha256':'a'*64})
    return registry._decode(raw),raw


def owned_codec():
    codec = object.__new__(registry.HarvestRegistry)
    codec.policy = registry.schema.HarvestRegistryPolicy('owned_schema','owned_owner','owned_pub','owned_read','owned_database')
    codec.integrity_key = b'owned-harvest-registry-codec-key-000001'
    return codec


def test_server_key_packet_HMAC_and_columns_are_deterministic_and_bound():
    packet,raw = owned_packet();codec = owned_codec();row = codec._values(packet,raw)
    assert codec._row(row,'tenant-1',packet['farm']) == packet
    assert registry._decode(raw) == packet and row['payload_sha256'] == sha256(raw).hexdigest()
    seed = {k:v for k,v in packet.items() if k not in ('result_id','artifact')}
    assert packet['artifact']['key'] == sha256(registry._canonical(seed)).hexdigest()
    assert packet['result_id'] == registry.VERSION+':'+packet['artifact']['key']
    assert packet['rights_or_gate_approval'] is False


@pytest.mark.parametrize('change',['extra','missing','code','approval','source','farm','bool-count','negative-count',
    'large-count','root-hash','writer-code','path','result','mass-hash','status','noncanonical','duplicate','oversize','invalid-UTF8'])
def test_changed_or_unbounded_metadata_is_rejected(change):
    packet,raw = owned_packet()
    if change=='extra':packet['approved']=True
    elif change=='missing':del packet['source']
    elif change=='code':packet['code']['publication_code_sha256']='0'*64
    elif change=='approval':packet['rights_or_gate_approval']=True
    elif change=='source':packet['source']['result_id']='foreign'
    elif change=='farm':del packet['farm']['crop_id']
    elif change=='bool-count':packet['artifact']['row_count']=True
    elif change=='negative-count':packet['artifact']['row_count']=-1
    elif change=='large-count':packet['artifact']['row_count']=registry.schema.MAX_ROWS+1
    elif change=='root-hash':packet['artifact']['sha256']='unknown'
    elif change=='writer-code':packet['artifact']['writer_code_sha256']='0'*64
    elif change=='path':packet['artifact']['key']='../escape'
    elif change=='result':packet['result_id']=registry.VERSION+':'+'0'*64
    elif change=='mass-hash':packet['parameters']['mass_sha256']='0'*64
    elif change=='status':packet['source']['source_status']='forecast'
    altered = registry._canonical(packet)
    if change=='noncanonical':altered += b'\n'
    elif change=='duplicate':altered = raw[:-1]+b',"tenant_id":"tenant-1"}'
    elif change=='oversize':altered = b' '*registry.schema.MAX_METADATA_BYTES+raw
    elif change=='invalid-UTF8':altered = b'\xff'
    with pytest.raises(registry.HarvestRegistrationHold):registry._decode(altered)


@pytest.mark.parametrize('change',['signature','hash','tenant','farm-column','parameter-column','publisher','raw'])
def test_signed_packet_and_SQL_columns_cannot_be_mixed(change):
    packet,raw = owned_packet();codec = owned_codec();row = codec._values(packet,raw)
    field = {'signature':'integrity_signature','hash':'payload_sha256','tenant':'tenant_id',
        'farm-column':'scenario_revision','parameter-column':'mass_parameter_sha256','publisher':'registered_by','raw':'payload_raw'}[change]
    row[field] = raw+b' ' if change=='raw' else '0'*64
    with pytest.raises(registry.HarvestRegistrationHold):codec._row(row,'tenant-1',packet['farm'])


@pytest.mark.parametrize('name',['DOMAIN','CODE_SHA256','LIMITS'])
def test_runtime_code_policy_mutation_is_rejected(monkeypatch,name):
    monkeypatch.setattr(registry,name,{'root_bytes':1} if name=='LIMITS' else b'foreign-domain' if name=='DOMAIN' else '0'*64)
    with pytest.raises(registry.HarvestRegistrationHold):registry._pins()


@pytest.mark.parametrize('query',[None,{},object()])
def test_implicit_query_configuration_never_opens_a_database(query,tmp_path):
    with pytest.raises(registry.HarvestRegistrationHold):
        registry.HarvestRegistry(query,None,tmp_path,dsn='password=owned-must-not-be-logged',integrity_key=b'x'*32)


@pytest.mark.parametrize('entry',['escape','unknown.json','symlink','oversize'])
def test_private_root_entries_and_storage_bounds(tmp_path,entry):
    root = tmp_path/'root';root.mkdir(mode=0o700)
    if entry=='symlink':(root/('0'*64)).symlink_to(tmp_path,target_is_directory=True)
    elif entry=='oversize':
        child = root/('0'*64);child.mkdir(mode=0o700);path = child/('1'*64+'.json')
        with path.open('wb') as f:f.truncate(registry.replay.LIMITS['directory_bytes']+1)
        path.chmod(0o400)
    else:(root/entry).write_text('owned')
    fd = registry.files._open_directory_nofollow(root)
    try:
        with pytest.raises((ValueError,OSError)):registry._root_usage(fd)
    finally:os.close(fd)


@pytest.fixture
def harvest_scope(login_database,tmp_path):
    database = login_database;suffix = uuid4().hex
    policy = registry.schema.HarvestRegistryPolicy('harvest_reg_'+suffix,'harvest_owner_'+suffix,
        'harvest_pub_'+suffix,'harvest_read_'+suffix,database['database'])
    paths = [];dsns = {};installed = False
    try:
        with psycopg.connect(database['admin']) as conn:
            assert_host_scram(conn);registry.schema.install_harvest_registry(conn,policy)
            for role in (policy.publisher,policy.reader):
                password = secrets.token_hex(32);path = tmp_path/(role+'.pgpass');paths.append(path)
                fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
                with os.fdopen(fd,'w') as f:f.write(f"{database['host']}:{database['port']}:{database['database']}:{role}:{password}\n")
                conn.execute("SET LOCAL log_statement='none'");conn.execute("SET LOCAL log_min_duration_statement=-1");conn.execute("SET LOCAL log_min_error_statement='panic'")
                verifier = conn.pgconn.encrypt_password(password.encode(),role.encode(),b'scram-sha-256')
                conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role),sql.Literal(verifier.decode())))
                dsns[role] = make_conninfo(host=database['host'],port=database['port'],dbname=database['database'],
                    user=role,passfile=str(path),sslmode='disable',require_auth='scram-sha-256')
        installed = True;directory = tmp_path/'harvest-registry';directory.mkdir(mode=0o700)
        yield policy,dsns,directory
    finally:
        for path in paths:path.unlink(missing_ok=True)
        if installed:
            with psycopg.connect(database['admin']) as conn:
                conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(policy.schema)))
                for role in (policy.publisher,policy.reader):
                    conn.execute(sql.SQL('REVOKE CONNECT ON DATABASE {} FROM {}').format(sql.Identifier(policy.database),sql.Identifier(role)))
                for role in (policy.publisher,policy.reader,policy.owner):conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(role)))
        with psycopg.connect(database['admin']) as conn:
            schemas = conn.execute('SELECT count(*) FROM pg_namespace WHERE nspname=%s',(policy.schema,)).fetchone()[0]
            roles = conn.execute('SELECT count(*) FROM pg_roles WHERE rolname=ANY(%s)',([policy.owner,policy.publisher,policy.reader],)).fetchone()[0]
        assert schemas == roles == 0 and not any(p.exists() for p in paths)
        save_native('harvest-registry-cleanup.json',{'schemas_after':schemas,'roles_after':roles,'passfiles_after':0})


@pytest.mark.parametrize('original_login_scope',[{'market_calculation':True,'market_source_storage':True,
    'thermal_scenario_storage':True,'break_even_calculation':True,'crop_cycle_result_storage':True}],indirect=True)
def test_actual_registration_rollback_calc_rights_retry_and_parent_preservation(stored_result,native_cleanup,harvest_scope,monkeypatch):
    query,parent,farm,rights,principal,expected = stored_result
    policy,dsns,directory = harvest_scope;forbid_calculation(monkeypatch)
    monkeypatch.setattr(type(query.authority),'issue',lambda *a,**k:pytest.fail('registration issued crop proof'))
    original = query.read('tenant-1',parent['result_id'],farm);source = registry.harvest._source(original)
    profile = mass_profile(source);profile['segments'][0]['end_at'] = expected['samples'][-1]['at']
    raw = registry._canonical(profile)
    allocation = registry._canonical(allocation_profile(registry.harvest._mass_parameters(raw),last_sample=2,last_event=3))
    db_before = counts(query.store.server.binding)
    def inventory():
        return {str(p):(sha256(p.read_bytes()).hexdigest(),p.stat().st_mode & 0o777,p.stat().st_ino)
            for d in (query.store.server.directory,query.evidence_resolver.values['input_directory']) for p in d.rglob('*') if p.is_file()}
    files_before = inventory();fd_before = len(os.listdir('/proc/self/fd'))
    key = b'owned-harvest-registry-native-key-00001'
    store = registry.HarvestRegistry(query,policy,directory,dsn=dsns[policy.publisher],integrity_key=key)
    def row_count():
        with store._connection() as conn:
            return conn.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(policy.schema,registry.schema.TABLE))).fetchone()['n']
    original_uses = rights.uses;original_insert = registry._insert
    def revoke_calculation_after_insert(*args):
        original_insert(*args);rights.uses = ('research_display',)
    with monkeypatch.context() as patch:
        patch.setattr(registry,'_insert',revoke_calculation_after_insert)
        try:
            with pytest.raises(registry.HarvestRegistrationHold):store.put('tenant-1',parent['result_id'],farm,raw,allocation)
            assert rights.allowed and rights.uses == ('research_display',) and row_count() == 0
            assert len(list(directory.glob('*/HEAD'))) == 1
        finally:rights.uses = original_uses
    registered = store.put('tenant-1',parent['result_id'],farm,raw,allocation)
    assert row_count() == 1;packet = registry._decode(registered['payload_raw'])
    with monkeypatch.context() as patch:
        for name in ('_read_allocations','_mass_row','_allocation_row'):
            patch.setattr(registry.harvest,name,lambda *a,**k:pytest.fail('registered retry regenerated harvest rows'))
        patch.setattr(registry.replay,'write_harvest_artifact',lambda *a,**k:pytest.fail('registered retry rewrote artifact'))
        assert store.put('tenant-1',parent['result_id'],farm,raw,allocation) == registered
    assert row_count() == 1
    rejected = []
    for case in ('write-scope','account','calculation-right','mixed-source','mixed-farm','reader','signature'):
        scopes = set(principal['scopes']);tenant = principal['tenant_id']
        try:
            call_store = store;call_farm = farm;call_raw = raw
            if case=='write-scope':principal['scopes'].remove('crop_result_write')
            elif case=='account':principal['tenant_id']='foreign'
            elif case=='calculation-right':rights.uses=('research_display',)
            elif case=='mixed-source':
                altered = deepcopy(profile);altered['source']['payload_sha256']='0'*64;call_raw=registry._canonical(altered)
            elif case=='mixed-farm':call_farm={**farm,'crop_id':'foreign'}
            elif case=='reader':call_store=registry.HarvestRegistry(query,policy,directory,dsn=dsns[policy.reader],integrity_key=key)
            elif case=='signature':
                forged = store._find('tenant-1',registered['result_id']);forged['integrity_signature']='0'*64
                with pytest.raises(registry.HarvestRegistrationHold):store._row(forged,'tenant-1',farm)
                rejected.append(case);continue
            error = PermissionError if case in ('write-scope','account') else registry.HarvestRegistrationHold
            with pytest.raises(error):call_store.put('tenant-1',parent['result_id'],call_farm,call_raw,allocation)
            rejected.append(case)
        finally:principal['scopes']=scopes;principal['tenant_id']=tenant;rights.uses=original_uses
    stored_files = {p.name:{'sha256':sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size,
        'mode':p.stat().st_mode & 0o777,'canonical_utf8':p.read_text()} for p in (directory/packet['artifact']['key']).iterdir()}
    root = json.loads(stored_files[packet['artifact']['sha256']+'.json']['canonical_utf8'])
    rows = [row for page in root['pages'] for row in json.loads(stored_files[page['sha256']+'.json']['canonical_utf8'])]
    assert len(rows) == packet['artifact']['row_count'] == 6
    with query.store.jobs.connect() as conn:audit_runtime_roles(conn,query.store.jobs.runtime_identity[0])
    assert query.read('tenant-1',parent['result_id'],farm) == original
    assert counts(query.store.server.binding) == db_before and inventory() == files_before and row_count() == 1
    assert len(os.listdir('/proc/self/fd')) == fd_before
    saved = store._find('tenant-1',registered['result_id'])
    save_native('harvest-registration-verified.json',{'actual_SCRAM':True,'schema_policy':policy.__dict__,
        'source':source,'farm':farm,'parameter_document':profile,'allocation_document':json.loads(allocation),
        'registered_record':{**{k:v for k,v in registered.items() if k not in ('payload_raw','recorded_at')},
            'payload_raw_utf8':registered['payload_raw'].decode(),'recorded_at':registered['recorded_at'].isoformat()},
        'stored_signature':saved['integrity_signature'],'registered_by':saved['registered_by'],'rows':rows,'artifact_files':stored_files,
        'after_INSERT_calc_only_withdrawal_rolled_back':True,'rolled_back_row_count':0,'private_orphan_HEAD_count':1,
        'same_retry_preserves_record_and_first_time':True,'registered_retry_harvest_regeneration_calls':0,'final_registered_rows':1,
        'rejected_cases':rejected,'RHS_calls':0,'new_proof_calls':0,'FD_before_after':[fd_before,len(os.listdir('/proc/self/fd'))],
        'existing_parent_query_and_role_audit_preserved':True,'input_custody_SHA_mode_inode_preserved':True,
        'DB_counts_preserved':list(db_before),'actual_signed_synthetic_harvest_registrations':1,
        'actual_coefficients_adopted':0,'actual_crop_Runs':0,'gates':'not_assessed'})
