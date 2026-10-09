"""Private owned-fixture DB/runtime backup, with exact original authority retained."""
from contextlib import contextmanager, ExitStack
from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shlex
import socket
import stat
import subprocess
from unittest.mock import patch
from time import perf_counter

import psycopg
from psycopg.conninfo import conninfo_to_dict, make_conninfo

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'owned-crop-parent-backup-v1'
MAX_DUMP_BYTES = 128 * 1024**2
spec = importlib.util.spec_from_file_location('parent_backup_owned_runtime', ROOT/'research/crop-cycle-registered-runtime.py')
runtime = importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
canonical = runtime._canonical


def need(value, message='owned parent backup unavailable'):
    if not value:
        raise ValueError(message)


def write(path, raw):
    runtime.write_private(path, raw)


def private_read(path, maximum, *, modes=(0o400,)):
    path = Path(path);fd = runtime.custody.job_store._open_directory_nofollow(path.parent)
    try:
        runtime.custody._secure(fd,directory=True)
        handle = runtime.custody._file(fd,path.name,modes=modes)
        try:
            before = runtime.custody._secure(handle,modes=modes)
            need(1 <= before.st_size <= maximum)
            with os.fdopen(handle,'rb',closefd=False) as stream:raw = stream.read(maximum+1)
            after = os.fstat(handle)
            need(len(raw) == before.st_size
                 and (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)
                 == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns))
            return raw
        finally:os.close(handle)
    finally:
        os.close(fd)


def private_hash(path):
    path = Path(path);parent = runtime.custody.job_store._open_directory_nofollow(path.parent)
    try:
        runtime.custody._secure(parent,directory=True)
        fd = os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=parent)
        try:
            info = runtime.custody._secure(fd)
            need(stat.S_ISREG(info.st_mode) and info.st_size <= MAX_DUMP_BYTES)
            digest = sha256()
            with os.fdopen(fd,'rb',closefd=False) as stream:
                while block := stream.read(1024**2):digest.update(block)
            after = os.fstat(fd)
            need((info.st_dev,info.st_ino,info.st_size,info.st_mtime_ns,info.st_ctime_ns)
                 == (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns))
            return digest.hexdigest()
        finally:os.close(fd)
    finally:os.close(parent)


def command(binary, arguments, directory, name, *, timeout=60):
    """Errors stay private; credentials/SQL must not enter exception messages."""
    log = directory/(name+'.private-log')
    started = perf_counter()
    try:
        with log.open('xb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            result = subprocess.run([str(binary), *map(str, arguments)], stdin=subprocess.DEVNULL,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise ValueError('owned backup command deadline exceeded') from None
    finally:
        log.chmod(0o400)
    need(result.returncode == 0, 'owned backup command failed; private log retained')
    return {'tool': binary.name, 'actual_exit_code': result.returncode,
            'wall_seconds': perf_counter()-started, 'log_sha256': sha256(log.read_bytes()).hexdigest()}


def protect_source(admin_dsn, owned_data, binary):
    params = conninfo_to_dict(admin_dsn)
    need('password' not in params and params.get('host', '').startswith('/'), 'owned local admin required')
    with psycopg.connect(admin_dsn) as conn:
        data = Path(conn.execute('SHOW data_directory').fetchone()[0])
        major = conn.execute('SHOW server_version').fetchone()[0]
        names = {r[0] for r in conn.execute('SELECT datname FROM pg_database').fetchall()}
    need(data == Path(owned_data) and data.is_dir() and not data.is_symlink()
         and data.stat().st_uid == os.getuid() and major == '16.15'
         and names == {'postgres', 'template0', 'template1'}, 'explicit owned PostgreSQL16.15 cluster required')
    pid = int((data/'postmaster.pid').read_text().splitlines()[0])
    need(Path('/proc', str(pid)).stat().st_uid == os.getuid()
         and Path('/proc', str(pid), 'exe').resolve() == (Path(binary)/'postgres').resolve(), 'owned PG identity mismatch')
    need(Path(shlex.split((data/'postmaster.opts').read_text())[0]).resolve() == (Path(binary)/'postgres').resolve())
    return {'server_version': major, 'source_PID': pid,
            'binary_sha256': {name: sha256((Path(binary)/name).read_bytes()).hexdigest()
                              for name in ('postgres','initdb','pg_ctl','pg_dump','pg_dumpall','pg_restore','psql')}}


def backup(directory, *, admin_dsn, owned_data, binary, config, config_sha256,
           db_key, result_key, result_proof, record, farm):
    binary = Path(binary); checked = protect_source(admin_dsn, owned_data, binary)
    server, request_raw = runtime.load_runtime(config, config_sha256)
    need(json.loads(request_raw)['farm'] == farm and type(record['payload_raw']) is bytes
         and sha256(record['payload_raw']).hexdigest() == record['payload_sha256'])
    need(type(db_key) is bytes and type(result_key) is bytes and len(db_key) >= 32 and len(result_key) >= 32
         and len({db_key, result_key, server.integrity_key, server.binding.input_authority.integrity_key}) == 4)
    directory = Path(directory);directory.mkdir(mode=0o700)
    need(directory.stat().st_mode & 0o777 == 0o700 and directory.stat().st_uid == os.getuid())
    config_raw = runtime.private_bytes(config);document = json.loads(config_raw)
    for name, raw in (('DB-key.private',db_key),('result-key.private',result_key),
                      ('result-proof.private',result_proof),('original-runtime.private',config_raw)):
        write(directory/name, raw)
    dsn = conninfo_to_dict(runtime.private_bytes(document['dsn_file']).decode())
    need(dsn.get('host') == '127.0.0.1' and 'password' not in dsn and dsn.get('passfile'))
    passfile = private_read(dsn['passfile'],8192,modes=(0o400,0o600))
    write(directory/'original-passfile.private', passfile)
    commands = [command(binary/'pg_dumpall',['--roles-only','--no-password','--dbname',admin_dsn,
                        '--file',directory/'roles.private.sql'],directory,'roles-dump'),
                command(binary/'pg_dump',['--no-password','--format=custom','--lock-wait-timeout=10s',
                        '--dbname',admin_dsn,'--file',directory/'database.private.dump'],directory,'DB-dump')]
    for name in ('roles.private.sql','database.private.dump'):
        (directory/name).chmod(0o400)
    raw_files = {name: private_hash(directory/name) for name in (
        'roles.private.sql','database.private.dump','DB-key.private','result-key.private',
        'result-proof.private','original-runtime.private','original-passfile.private')}
    need(sum((directory/name).stat().st_size for name in raw_files) <= MAX_DUMP_BYTES, 'owned backup byte limit exceeded')
    manifest = {'version': VERSION, 'scope':'owned_synthetic_backup_only', 'binary':str(binary),
        'binary_sha256':checked['binary_sha256'], 'config_sha256':config_sha256,
        'original_record':{'result_id':record['result_id'],'payload_sha256':record['payload_sha256']},
        'farm':farm, 'files_sha256':raw_files, 'commands':commands, 'limits':{'raw_bytes':MAX_DUMP_BYTES},
        'original_server_version':checked['server_version'], 'rights_or_gate_approval':False}
    raw = canonical(manifest);path = directory/'backup.private.json';write(path,raw)
    return path, sha256(raw).hexdigest()


def checked(path, digest):
    path = Path(path);raw = runtime.private_bytes(path);value = json.loads(raw)
    need(sha256(raw).hexdigest() == digest and canonical(value) == raw and value['version'] == VERSION
         and value['scope'] == 'owned_synthetic_backup_only' and value['rights_or_gate_approval'] is False)
    need(value['limits'] == {'raw_bytes':MAX_DUMP_BYTES})
    expected = {'roles.private.sql','database.private.dump','DB-key.private','result-key.private',
                'result-proof.private','original-runtime.private','original-passfile.private'}
    need(set(value['files_sha256']) == expected)
    need(sum((path.parent/name).stat().st_size for name in expected) <= MAX_DUMP_BYTES)
    for name, checksum in value['files_sha256'].items():
        need(private_hash(path.parent/name) == checksum, 'owned backup file hash mismatch')
    need(value['binary_sha256'] == {name:sha256((Path(value['binary'])/name).read_bytes()).hexdigest()
                                  for name in ('postgres','initdb','pg_ctl','pg_dump','pg_dumpall','pg_restore','psql')})
    return value


def retarget(document, *, source_dsn_raw, passfile_raw, port, dsn_file, passfile_file):
    """Transport-only new config; original signed model/farm data is unchanged."""
    need(type(port) is int and 1 <= port <= 65535)
    params = conninfo_to_dict(source_dsn_raw.decode())
    need(params.get('host') == '127.0.0.1' and 'password' not in params and params.get('passfile'))
    rows = passfile_raw.decode().splitlines()
    need(len(rows) == 1)
    # Fixture credentials are generated hex; deliberately reject escaped/general pgpass input.
    parts = rows[0].split(':')
    need(len(parts) == 5 and parts[:4] == [params['host'],params['port'],params['dbname'],params['user']]
         and len(parts[4]) == 64 and all(c in '0123456789abcdef' for c in parts[4]))
    parts[1] = str(port);new_passfile = (':'.join(parts)+'\n').encode()
    params.update(port=str(port), passfile=str(passfile_file))
    dsn_raw = make_conninfo(**params).encode();target = deepcopy(document)
    previous = target['dsn_file'];target['dsn_file'] = str(dsn_file)
    target['static_sha256'].pop(previous);target['static_sha256'][str(dsn_file)] = sha256(dsn_raw).hexdigest()
    return target, dsn_raw, new_passfile


@contextmanager
def restored(path, digest, directory):
    value = checked(path, digest);parent = Path(path).parent;binary = Path(value['binary'])
    directory = Path(directory);directory.mkdir(mode=0o700)
    data = directory/'data'
    # Unix socket addresses are bounded; the retained authority path can be long.
    sockets = Path('/tmp')/('ossf-parent-'+sha256(str(directory).encode()).hexdigest()[:16])
    sockets.mkdir(mode=0o700)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1',0));port = probe.getsockname()[1]
    commands = []
    running = False
    try:
        commands.append(command(binary/'initdb',['-D',data,'-U','ossf_restore_admin',
                 '--auth-local=trust','--auth-host=scram-sha-256','--no-locale','--encoding=UTF8'],directory,'init'))
        running = True
        commands.append(command(binary/'pg_ctl',['-D',data,'-l',directory/'PG.private.log','-w','-t','10',
            'start','-o',f'-h 127.0.0.1 -p {port} -k {sockets}'],directory,'start'))
        admin = make_conninfo(host=str(sockets),port=port,dbname='postgres',user='ossf_restore_admin')
        commands.append(command(binary/'psql',['--no-password','--no-psqlrc','--set','ON_ERROR_STOP=1',
            '--dbname',admin,'--file',parent/'roles.private.sql'],directory,'roles-restore'))
        commands.append(command(binary/'pg_restore',['--no-password','--exit-on-error','--clean','--if-exists',
            '--dbname',admin,parent/'database.private.dump'],directory,'DB-restore'))
        config = json.loads(runtime.private_bytes(parent/'original-runtime.private'))
        source_dsn = runtime.private_bytes(config['dsn_file'])
        target,dsn,passfile = retarget(config,source_dsn_raw=source_dsn,
            passfile_raw=runtime.private_bytes(parent/'original-passfile.private'),port=port,
            dsn_file=directory/'dsn.private',passfile_file=directory/'authority.pgpass')
        write(directory/'dsn.private',dsn);write(directory/'authority.pgpass',passfile)
        raw = canonical(target);write(directory/'runtime.private.json',raw)
        checked(path,digest)
        yield {'config':directory/'runtime.private.json','config_sha256':sha256(raw).hexdigest(),
               'backup':value,'directory':directory,'port':port,'admin':admin,'commands':commands}
    finally:
        if running and (data/'postmaster.pid').exists():
            commands.append(command(binary/'pg_ctl',['-D',data,'-m','fast','-w','-t','10','stop'],directory,'stop'))
        sockets.rmdir()
        write(directory/'terminal.private.json',canonical({'commands':commands,'postmaster_absent':not (data/'postmaster.pid').exists()}))


def current_query(backup_path, backup_sha, context):
    from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    from app.crop_cycle_calculation_current_query import CalculationCurrentCycleQuery
    value = checked(backup_path, backup_sha);parent = Path(backup_path).parent
    server, _ = runtime.load_runtime(context['config'],context['config_sha256'])
    issuer = CalculationResultEvidenceAuthority(server.binding.input_authority,
        integrity_key=runtime.private_bytes(parent/'result-key.private'),
        issuer_id='owned-parent-backup-result',key_id='result-v1')
    document = json.loads(runtime.private_bytes(context['config']))
    class Evidence:
        version = 'owned-parent-backup-evidence-v1'
        def __call__(self, tenant, packet):
            need(tenant == 'tenant-1' and packet['result_id'] == value['original_record']['result_id'])
            return {'input_directory':Path(document['input']['directory']),
                    'input_evidence_raw':runtime.private_bytes(document['input']['evidence_file']),
                    'result_evidence_raw':private_read(parent/'result-proof.private',8*1024**2)}
    store = CalculationCycleCropResultStore(server,integrity_key=runtime.private_bytes(parent/'DB-key.private'))
    return CalculationCurrentCycleQuery(store,issuer,evidence_resolver=Evidence())


@contextmanager
def readonly_guard():
    from app import crop_cycle_input_stream as inputs
    from app.crop_cycle_calculation_result_store import CalculationCycleCropResultStore
    from app.crop_cycle_calculation_result_evidence import CalculationResultEvidenceAuthority
    def forbidden(*args, **kwargs):raise AssertionError('restore/read attempted calculation or publication')
    targets = ((inputs,'open_input_packet'),(runtime.engine.legacy,'prepare_context'),
        (runtime.engine,'open_calculation_context'),(runtime.engine,'advance_chunk'),
        (runtime.artifact._Files,'_load_prefix'),(runtime.artifact,'_validate_delta'),
        (runtime.artifact,'open_artifact'),(runtime.engine.short._Evaluator,'rhs'),
        (runtime.custody.CalculationServerCustody,'_open'),(runtime.custody._Journal,'__init__'),
        (CalculationCycleCropResultStore,'put'),(CalculationResultEvidenceAuthority,'issue'))
    with ExitStack() as stack:
        for target,name in targets:stack.enter_context(patch.object(target,name,forbidden))
        yield


def read_receipt(path, digest, context):
    """All original rows for the small acceptance case; no result regeneration."""
    service = current_query(path,digest,context);value = checked(path,digest)
    args = ('tenant-1',value['original_record']['result_id'],value['farm'])
    before = len(os.listdir('/proc/self/fd'));metadata = service.read(*args)
    record = metadata['record'];need(record['payload_sha256']==value['original_record']['payload_sha256'])
    rows = {}
    for kind in ('samples','events'):
        result = service.read(*args,kind=kind,start=0,limit=64 if kind=='samples' else 8)
        page = result['page'];need(page['next']==page['total'], 'small acceptance rows only')
        rows[kind] = {'count':len(page['records']),
            'sha256':sha256(b''.join(canonical(row)+b'\n' for row in page['records'])).hexdigest()}
        need(result['record']==record)
    with service.store.jobs.connect() as conn:
        need(conn.pgconn.used_password and conn.info.get_parameters()['require_auth']=='scram-sha-256')
    after = len(os.listdir('/proc/self/fd'));need(before==after)
    return {'record':{'result_id':record['result_id'],'payload_sha256':record['payload_sha256'],
                'recorded_at':record['recorded_at'].isoformat()},
        'identity':metadata['identity'],'status':metadata['terminal']['status'],'rows':rows,
        'actual_host_SCRAM':True,'FD_before_after':[before,after],
        'guarded_calculation_publication_proof_issue_calls':0}


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup',required=True,type=Path);parser.add_argument('--sha256',required=True)
    parser.add_argument('--config',type=Path);parser.add_argument('--config-sha256')
    parser.add_argument('--restore-directory',type=Path);parser.add_argument('--output',required=True,type=Path)
    args = parser.parse_args()
    need(bool(args.restore_directory) != bool(args.config))
    with readonly_guard():
        if args.restore_directory:
            with restored(args.backup,args.sha256,args.restore_directory) as context:
                result = read_receipt(args.backup,args.sha256,context)
            result['restored_postmaster_absent'] = not (args.restore_directory/'data/postmaster.pid').exists()
        else:
            need(args.config_sha256)
            result = read_receipt(args.backup,args.sha256,{'config':args.config,'config_sha256':args.config_sha256})
    write(args.output,canonical(result))


if __name__=='__main__':main()
