"""Normal harvest registration on a preserved synthetic parent, then fresh DB restoration."""
from contextlib import contextmanager, ExitStack
from dataclasses import asdict
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import secrets
import socket
from unittest.mock import patch
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo

from app import crop_harvest_current_query as query
from test_crop_harvest import mass_profile, allocation_profile

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'owned-crop-harvest-storage-preservation-v1'
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
spec = importlib.util.spec_from_file_location('harvest_storage_parent_backup', ROOT/'research/crop-harvest-parent-backup.py')
backup = importlib.util.module_from_spec(spec);spec.loader.exec_module(backup)
runtime, need, canonical = backup.runtime, backup.need, backup.canonical
registry, harvest = query.registry, query.harvest
DEPENDENCIES = {str(Path(m.__file__).resolve()):sha256(Path(m.__file__).read_bytes()).hexdigest()
                for m in (backup, runtime, query, registry, registry.replay, harvest)}
FILES = {'harvest-key.private','publisher-dsn.private','reader-dsn.private',
         'publisher.pgpass','reader.pgpass','mass.private.json','allocation.private.json'}


def record(value):
    return {'result_id':value['result_id'],'payload_sha256':value['payload_sha256'],
            'payload_raw_utf8':value['payload_raw'].decode(),'recorded_at':value['recorded_at'].isoformat()}


def checked(path, digest):
    path = Path(path);raw = runtime.private_bytes(path);value = json.loads(raw)
    need(sha256(raw).hexdigest() == digest and canonical(value) == raw)
    need(set(value) == {'version','scope','code_sha256','dependencies','parent_backup','parent_backup_sha256',
        'policy','registry_directory','files_sha256','original_record','source','summary_sha256','pages'})
    need(value['version'] == VERSION and value['scope'] == 'owned_synthetic_only'
         and value['code_sha256'] == CODE_SHA256 == sha256(Path(__file__).read_bytes()).hexdigest()
         and value['dependencies'] == DEPENDENCIES
         and all(sha256(Path(p).read_bytes()).hexdigest() == h for p,h in DEPENDENCIES.items()))
    need(set(value['files_sha256']) == FILES)
    for name,d in value['files_sha256'].items():
        need(sha256(backup.private_read(path.parent/name,65536)).hexdigest() == d)
    parent = backup.checked(value['parent_backup'],value['parent_backup_sha256'])
    need(value['source']['result_id'] == parent['original_record']['result_id']
         and value['source']['payload_sha256'] == parent['original_record']['payload_sha256'])
    registry.schema.HarvestRegistryPolicy(**value['policy'])
    return value


def profiles(current, parent, farm):
    original = current.read('tenant-1',parent,farm);source = harvest._source(original)
    counts = json.loads(original['record']['payload_raw'])['policies']['server_progress']['counts']
    need(counts['samples'] >= 2 and counts['events'] >= 2)
    first = current.read('tenant-1',parent,farm,kind='samples',start=0,limit=1)['page']['records'][0]['at']
    last = current.read('tenant-1',parent,farm,kind='samples',start=counts['samples']-1,limit=1)['page']['records'][0]['at']
    mass = mass_profile(source);mass['revision'] = 'preserved-parent-synthetic-v1'
    mass['segments'][0].update(start_at=first,end_at=last)
    mass_raw = canonical(mass);parameters = harvest._mass_parameters(mass_raw)
    allocation = allocation_profile(parameters,last_sample=counts['samples']-1,last_event=counts['events']-1)
    allocation['revision'] = 'preserved-parent-synthetic-v1'
    raw = canonical(allocation);harvest._allocation_parameters(raw,parameters)
    harvest._allocation_scope(allocation,original)
    return source,mass_raw,raw


def pgpass(path, raw):
    fd = os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())


def install(context, directory):
    suffix = uuid4().hex
    policy = registry.schema.HarvestRegistryPolicy('harvest_saved_'+suffix,'harvest_owner_'+suffix,
        'harvest_pub_'+suffix,'harvest_read_'+suffix,'postgres')
    dsns = {}
    with psycopg.connect(context['admin']) as conn:
        registry.schema.install_harvest_registry(conn,policy)
        for name,role in (('publisher',policy.publisher),('reader',policy.reader)):
            password = secrets.token_hex(32);path = directory/(name+'.pgpass')
            pgpass(path,f"127.0.0.1:{context['port']}:postgres:{role}:{password}\n".encode())
            conn.execute("SET LOCAL log_statement='none'")
            conn.execute("SET LOCAL log_min_duration_statement=-1")
            conn.execute("SET LOCAL log_min_error_statement='panic'")
            verifier = conn.pgconn.encrypt_password(password.encode(),role.encode(),b'scram-sha-256')
            conn.execute(sql.SQL('ALTER ROLE {} PASSWORD {}').format(sql.Identifier(role),sql.Literal(verifier.decode())))
            dsns[name] = make_conninfo(host='127.0.0.1',port=context['port'],dbname='postgres',user=role,
                passfile=str(path),sslmode='disable',require_auth='scram-sha-256')
            backup.write(directory/(name+'-dsn.private'),dsns[name].encode())
    return policy,dsns


def selected(service, result_id, farm):
    before = len(os.listdir('/proc/self/fd'));args = ('tenant-1',result_id,farm)
    value = service.read(*args);total = value['summary']['row_count'];pages = {}
    for label,start,limit in (('first',0,min(64,total)),('last',total-1,1)):
        found = service.read(*args,start=start,limit=limit)
        need(found['record'] == value['record'] and found['identity'] == value['identity'])
        page = found['page'];pages[label] = {'start':start,'next':page['next'],'total':page['total'],
            'count':len(page['records']),'rows_sha256':sha256(b''.join(canonical(r)+b'\n' for r in page['records'])).hexdigest()}
    with service.store._connection() as conn:need(conn.pgconn.used_password)
    need(len(os.listdir('/proc/self/fd')) == before)
    return {'original_record':record(value['record']),'source':value['identity']['parent_source'],
        'summary_sha256':sha256(canonical(value['summary'])).hexdigest(),'pages':pages}


def register(parent_path, parent_sha, directory):
    parent = backup.checked(parent_path,parent_sha);directory = Path(directory);directory.mkdir(mode=0o700)
    with backup.readonly_guard():
        with backup.restored(parent_path,parent_sha,directory/'source-parent') as context:
            current = backup.current_query(parent_path,parent_sha,context)
            source,mass,allocation = profiles(current,parent['original_record']['result_id'],parent['farm'])
            policy,dsns = install(context,directory);key = os.urandom(32)
            backup.write(directory/'harvest-key.private',key)
            backup.write(directory/'mass.private.json',mass);backup.write(directory/'allocation.private.json',allocation)
            root = directory/'registry';root.mkdir(mode=0o700)
            publisher = registry.HarvestRegistry(current,policy,root,dsn=dsns['publisher'],integrity_key=key)
            result = publisher.put('tenant-1',source['result_id'],parent['farm'],mass,allocation)
            reader = query.HarvestCurrentQuery(registry.HarvestRegistry(current,policy,root,
                dsn=dsns['reader'],integrity_key=key))
            with read_guard():observed = selected(reader,result['result_id'],parent['farm'])
            need(observed['source'] == source)
            parent_record = current.read('tenant-1',source['result_id'],parent['farm'])['record']
            merged,merged_sha = backup.backup(directory/'merged-parent',admin_dsn=context['admin'],
                owned_data=context['directory']/'data',binary=Path(parent['binary']),
                config=context['config'],config_sha256=context['config_sha256'],
                db_key=runtime.private_bytes(Path(parent_path).parent/'DB-key.private'),
                result_key=runtime.private_bytes(Path(parent_path).parent/'result-key.private'),
                result_proof=runtime.private_bytes(Path(parent_path).parent/'result-proof.private'),
                record=parent_record,farm=parent['farm'])
    for name in ('publisher.pgpass','reader.pgpass'):(directory/name).chmod(0o400)
    value = {'version':VERSION,'scope':'owned_synthetic_only','code_sha256':CODE_SHA256,'dependencies':DEPENDENCIES,
        'parent_backup':str(merged),'parent_backup_sha256':merged_sha,'policy':asdict(policy),
        'registry_directory':str(root),'files_sha256':{name:sha256(backup.private_read(directory/name,65536)).hexdigest()
        for name in FILES},**observed}
    path = directory/'storage.private.json';raw = canonical(value);backup.write(path,raw)
    checked(path,sha256(raw).hexdigest())
    need(not (directory/'source-parent/data/postmaster.pid').exists())
    return path,sha256(raw).hexdigest()


@contextmanager
def restored_storage(value, directory):
    """Second restore uses a distinct bootstrap role because the dump retains the first one."""
    parent = backup.checked(value['parent_backup'],value['parent_backup_sha256'])
    binary = Path(parent['binary']);source = Path(value['parent_backup']).parent
    directory = Path(directory);directory.mkdir(mode=0o700);data = directory/'data'
    sockets = Path('/tmp')/('ossf-harvest-'+sha256(str(directory).encode()).hexdigest()[:16]);sockets.mkdir(mode=0o700)
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1',0));port = probe.getsockname()[1]
    running = False;commands = [];admin_user = 'ossf_harvest_restore_admin'
    try:
        commands.append(backup.command(binary/'initdb',['-D',data,'-U',admin_user,'--auth-local=trust',
            '--auth-host=scram-sha-256','--no-locale','--encoding=UTF8'],directory,'init'))
        running = True
        commands.append(backup.command(binary/'pg_ctl',['-D',data,'-l',directory/'PG.private.log','-w','-t','10',
            'start','-o',f'-h 127.0.0.1 -p {port} -k {sockets}'],directory,'start'))
        admin = make_conninfo(host=str(sockets),port=port,dbname='postgres',user=admin_user)
        commands.append(backup.command(binary/'psql',['--no-password','--no-psqlrc','--set','ON_ERROR_STOP=1',
            '--dbname',admin,'--file',source/'roles.private.sql'],directory,'roles-restore'))
        commands.append(backup.command(binary/'pg_restore',['--no-password','--exit-on-error','--clean','--if-exists',
            '--dbname',admin,source/'database.private.dump'],directory,'DB-restore'))
        config = json.loads(runtime.private_bytes(source/'original-runtime.private'))
        target,dsn,secret = backup.retarget(config,source_dsn_raw=runtime.private_bytes(config['dsn_file']),
            passfile_raw=runtime.private_bytes(source/'original-passfile.private'),port=port,
            dsn_file=directory/'dsn.private',passfile_file=directory/'authority.pgpass')
        backup.write(directory/'dsn.private',dsn);backup.write(directory/'authority.pgpass',secret)
        raw = canonical(target);backup.write(directory/'runtime.private.json',raw)
        yield {'config':directory/'runtime.private.json','config_sha256':sha256(raw).hexdigest(),
            'directory':directory,'port':port,'admin':admin}
    finally:
        if running and (data/'postmaster.pid').exists():
            commands.append(backup.command(binary/'pg_ctl',['-D',data,'-m','fast','-w','-t','10','stop'],directory,'stop'))
        sockets.rmdir()
        backup.write(directory/'terminal.private.json',canonical({'commands':commands,
            'postmaster_absent':not (data/'postmaster.pid').exists()}))


def reader(path, digest, context):
    value = checked(path,digest);path = Path(path)
    current = backup.current_query(value['parent_backup'],value['parent_backup_sha256'],context)
    dsn_raw = runtime.private_bytes(path.parent/'reader-dsn.private')
    _,dsn,secret = backup.retarget({'dsn_file':'old','static_sha256':{'old':sha256(dsn_raw).hexdigest()}},
        source_dsn_raw=dsn_raw,passfile_raw=runtime.private_bytes(path.parent/'reader.pgpass'),port=context['port'],
        dsn_file=context['directory']/'harvest-dsn.private',passfile_file=context['directory']/'harvest.pgpass')
    pgpass(context['directory']/'harvest.pgpass',secret)
    return query.HarvestCurrentQuery(registry.HarvestRegistry(current,
        registry.schema.HarvestRegistryPolicy(**value['policy']),Path(value['registry_directory']),
        dsn=dsn.decode(),integrity_key=runtime.private_bytes(path.parent/'harvest-key.private')))


@contextmanager
def read_guard():
    def forbidden(*args,**kwargs):raise AssertionError('stored harvest read attempted generation or publication')
    with ExitStack() as stack:
        for module,name in ((harvest,'_read_allocations'),(harvest,'_mass_row'),
                (harvest,'_allocation_row'),(registry.HarvestRegistry,'put')):
            stack.enter_context(patch.object(module,name,forbidden))
        yield


def denials(service, value, context):
    farm = backup.checked(value['parent_backup'],value['parent_backup_sha256'])['farm']
    args = ('tenant-1',value['original_record']['result_id'],farm)
    try:service.read('foreign',args[1],farm)
    except PermissionError:pass
    else:raise AssertionError('foreign tenant read stored harvest')
    document = json.loads(runtime.private_bytes(context['config']))
    for name in ('rights','principal'):
        path = Path(document[name+'_file']);saved = runtime.private_bytes(path);control = json.loads(saved)
        if name == 'rights':control['allowed'] = False
        else:control['scopes'].remove('crop_result_read')
        def replace(raw):
            path.chmod(0o600)
            with path.open('wb') as stream:
                stream.write(raw);stream.flush();os.fchmod(stream.fileno(),0o400);os.fsync(stream.fileno())
        replace(canonical(control))
        try:
            try:service.read(*args)
            except (PermissionError,query.HarvestCurrentQueryHold):pass
            else:raise AssertionError('withdrawn authority read stored harvest')
        finally:replace(saved)
        need(service.read(*args)['record']['payload_sha256'] == value['original_record']['payload_sha256'])
    return True


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--sha256',required=True)
    parser.add_argument('--restore-directory',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args();value = checked(args.manifest,args.sha256)
    with backup.readonly_guard(),read_guard():
        with restored_storage(value,args.restore_directory) as context:
            service = reader(args.manifest,args.sha256,context)
            observed = selected(service,value['original_record']['result_id'],backup.checked(
                value['parent_backup'],value['parent_backup_sha256'])['farm'])
            need(all(observed[k] == value[k] for k in observed))
            denied = denials(service,value,context)
    backup.write(args.output,canonical({**observed,'guarded_RHS_row_generation_publication_proof_calls':0,
        'current_rights_scope_tenant_denied_and_restored':denied,
        'restored_postmaster_absent':not (args.restore_directory/'data/postmaster.pid').exists()}))


if __name__ == '__main__':main()
