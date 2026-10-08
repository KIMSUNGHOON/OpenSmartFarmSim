"""Server-owned files and signed PostgreSQL references for synthetic harvest math."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import hmac
import os
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict
from psycopg.rows import dict_row

from . import crop_harvest_replay as replay
from . import crop_harvest_registry_schema as schema

current, harvest, files = replay.current, replay.harvest, replay.files
_canonical = replay._canonical
VERSION = schema.VERSION
DOMAIN = b'ossf-crop-harvest-registration-v1\0'
LIMITS = {'root_bytes': 1024**3, 'root_files': 131072, 'registrations': 128}
CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()
CODE = {'publication_code_sha256': CODE_SHA256,
        'registry_schema_code_sha256': sha256(Path(schema.__file__).read_bytes()).hexdigest(),
        'artifact_code_sha256': replay.CODE_SHA256}
_DECLARATIONS = _canonical([VERSION, DOMAIN.hex(), LIMITS, CODE, schema.MAX_METADATA_BYTES, schema.MAX_ROWS])


class HarvestRegistrationHold(ValueError):
    """No currently authorized server registration for this harvest calculation."""


def _need(condition):
    if not condition:raise HarvestRegistrationHold('harvest research registration unavailable')


def _pins():
    _need(_canonical([VERSION, DOMAIN.hex(), LIMITS, CODE, schema.MAX_METADATA_BYTES, schema.MAX_ROWS]) == _DECLARATIONS
          and sha256(Path(__file__).read_bytes()).hexdigest() == CODE_SHA256
          and sha256(Path(schema.__file__).read_bytes()).hexdigest() == CODE['registry_schema_code_sha256']
          and sha256(Path(replay.__file__).read_bytes()).hexdigest() == CODE['artifact_code_sha256'])
    replay._pins()


def _base(tenant, parent, farm, source, parameters):
    _pins();_need(current.storage._name(tenant) and type(farm) is dict
        and set(farm) == {'scenario_id','scenario_revision','registration_sha256','crop_id'})
    _need(all(current.storage._name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
        and current.inputs._digest(farm['registration_sha256']))
    _need(type(parent) is str and parent.startswith(current.storage.VERSION+':')
        and current.inputs._digest(parent[len(current.storage.VERSION)+1:]))
    _need(type(source) is dict and set(source) == {'result_id','payload_sha256','input_root_sha256',
        'artifact_sha256','math_manifest_sha256','source_status'} and source['result_id'] == parent
        and source['source_status'] in ('completed','hold'))
    _need(all(current.inputs._digest(source[k]) for k in ('payload_sha256','input_root_sha256','artifact_sha256','math_manifest_sha256')))
    _need(type(parameters) is dict and set(parameters) == {'mass_sha256','allocation_sha256'}
        and all(current.inputs._digest(v) for v in parameters.values()))
    return deepcopy({'schema_version': VERSION, 'status':'stored_unpublished_research',
        'claim_scope':'synthetic_harvest_allocation_math_only', 'rights_or_gate_approval':False,
        'tenant_id':tenant, 'parent_result_id':parent, 'farm':farm, 'source':source,
        'parameters':parameters, 'code':CODE})


def _key(base):return sha256(_canonical(base)).hexdigest()


def _decode(raw):
    try:
        _pins();value = current.storage._document(raw,max_size=schema.MAX_METADATA_BYTES)
        _need(type(value) is dict and set(value) == {'schema_version','status','claim_scope','rights_or_gate_approval',
            'tenant_id','result_id','parent_result_id','farm','source','artifact','parameters','code'} and _canonical(value) == raw)
        base = _base(value['tenant_id'],value['parent_result_id'],value['farm'],value['source'],value['parameters'])
        _need(all(value[k] == v for k,v in base.items()) and value['rights_or_gate_approval'] is False)
        artifact = value['artifact'];key = _key(base)
        _need(type(artifact) is dict and set(artifact) == {'key','sha256','row_count','row_chain_sha256','writer_code_sha256'}
            and artifact['key'] == key and value['result_id'] == VERSION+':'+key
            and artifact['writer_code_sha256'] == replay.CODE_SHA256
            and all(current.inputs._digest(artifact[k]) for k in ('sha256','row_chain_sha256'))
            and type(artifact['row_count']) is int and 0 <= artifact['row_count'] <= schema.MAX_ROWS)
        return value
    except Exception:raise HarvestRegistrationHold('harvest research registration unavailable') from None


def _packet(base, result):
    key = _key(base)
    raw = _canonical({**base,'result_id':VERSION+':'+key,'artifact':{'key':key,
        'sha256':result['artifact_sha256'],'row_count':result['row_count'],
        'row_chain_sha256':result['row_chain_sha256'],'writer_code_sha256':replay.CODE_SHA256}})
    _decode(raw);return raw


def _root_usage(fd):
    files._secure(fd,directory=True);names = os.listdir(fd)
    _need(len(names) <= LIMITS['registrations']+1)
    size = count = directories = 0
    for name in names:
        if name == '.registry-lock':
            child = files._file(fd,name,modes=(0o600,))
            try:_need(os.fstat(child).st_size == 0);count += 1
            finally:os.close(child)
        else:
            _need(current.inputs._digest(name));child = files._directory(fd,name)
            try:n,c = files._usage(child,'artifact');size += n;count += c;directories += 1
            finally:os.close(child)
    _need(size <= LIMITS['root_bytes'] and count <= LIMITS['root_files'] and directories <= LIMITS['registrations'])
    return size,count,directories


def _insert(conn, policy, values):
    conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING').format(
        sql.Identifier(policy.schema,schema.TABLE),sql.SQL(',').join(map(sql.Identifier,values)),
        sql.SQL(',').join(sql.Placeholder() for _ in values)),tuple(values.values()))


class HarvestRegistry:
    def __init__(self, query, policy, directory, *, dsn, integrity_key):
        try:
            _pins();_need(type(query) is current.CalculationCurrentCycleQuery and type(policy) is schema.HarvestRegistryPolicy
                and type(dsn) is str and type(integrity_key) is bytes and 32 <= len(integrity_key) <= 4096)
            upstream = query.store.server
            _need(integrity_key not in (query.store.integrity_key,upstream.integrity_key,
                upstream.binding.input_authority.integrity_key,query.authority.integrity_key,query.authority.input_authority.integrity_key))
            config = conninfo_to_dict(dsn)
            _need(config.get('dbname') == policy.database and config.get('user') in (policy.publisher,policy.reader)
                and config.get('host') and not config['host'].startswith('/') and 'password' not in config
                and config.get('passfile') and Path(config['passfile']).is_absolute())
            self.query,self.policy,self.directory,self._dsn,self.integrity_key = query,policy,Path(directory),dsn,integrity_key
            _need(self.directory.is_absolute());self.role = config['user'];self._passfile = Path(config['passfile'])
            self._credential_identity = self._credential()
            fd = files._open_directory_nofollow(self.directory)
            try:info = files._secure(fd,directory=True);self._identity = (info.st_dev,info.st_ino);_root_usage(fd)
            finally:os.close(fd)
            self._fixed = self._pointers();self._binding()
        except Exception:raise HarvestRegistrationHold('harvest research registration configuration unavailable') from None

    def _credential(self):
        parent = files._open_directory_nofollow(self._passfile.parent)
        try:
            fd = files._file(parent,self._passfile.name,modes=(0o600,))
            try:info = os.fstat(fd);return info.st_dev,info.st_ino
            finally:os.close(fd)
        finally:os.close(parent)

    def _pointers(self):
        return self.query,self.query._pointers(),self.policy,self.directory,self._dsn,self.integrity_key,self.role,self._passfile

    def _binding(self):
        _pins();_need(self._pointers() == self._fixed and self._credential() == self._credential_identity)
        self.query._binding();fd = files._open_directory_nofollow(self.directory)
        try:info = files._secure(fd,directory=True);_need((info.st_dev,info.st_ino) == self._identity)
        finally:os.close(fd)

    @contextmanager
    def _connection(self, write=False):
        self._binding();_need(not write or self.role == self.policy.publisher)
        with psycopg.connect(self._dsn,require_auth='scram-sha-256',row_factory=dict_row,connect_timeout=5,
                options='-c statement_timeout=10000 -c lock_timeout=2000') as conn:
            _need(conn.pgconn.used_password and conn.info.user == self.role and conn.info.dbname == self.policy.database)
            schema.audit_harvest_registry(conn,self.policy)
            yield conn
            schema.audit_harvest_registry(conn,self.policy);self._binding()

    def _find_on(self, conn, tenant, result_id):
        return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
            .format(sql.Identifier(self.policy.schema,schema.TABLE)),(tenant,result_id)).fetchone()

    def _find(self, tenant, result_id):
        with self._connection() as conn:return self._find_on(conn,tenant,result_id)

    def _signature(self, raw):return hmac.new(self.integrity_key,DOMAIN+raw,'sha256').hexdigest()

    def _values(self, packet, raw):
        values = {k:packet[k] for k in ('tenant_id','result_id','parent_result_id')};values.update(packet['farm'])
        artifact = packet['artifact']
        values.update(artifact_key=artifact['key'],artifact_sha256=artifact['sha256'],row_count=artifact['row_count'],
            row_chain_sha256=artifact['row_chain_sha256'],mass_parameter_sha256=packet['parameters']['mass_sha256'],
            allocation_parameter_sha256=packet['parameters']['allocation_sha256'],payload_raw=raw,
            payload_sha256=sha256(raw).hexdigest(),integrity_signature=self._signature(raw),registered_by=self.policy.publisher)
        return values

    def _row(self, row, tenant, farm):
        _need(row is not None and row['tenant_id'] == tenant and type(row['payload_raw']) is bytes)
        packet = _decode(row['payload_raw']);expected = self._values(packet,row['payload_raw'])
        _need(packet['tenant_id'] == tenant and packet['farm'] == farm
            and type(row['integrity_signature']) is str
            and hmac.compare_digest(row['integrity_signature'],expected['integrity_signature'])
            and all(row[k] == v for k,v in expected.items()))
        return packet

    def _authority(self, tenant, parent, farm, original=None):
        self._binding();self.query.store._guard(tenant,True)
        value = self.query.read(tenant,parent,farm);_need(value is not None)
        if original is not None:harvest._same(value,original)
        packet = current.inputs._json(value['record']['payload_raw']);binding = self.query.store.server.binding
        binding._rights(tenant,packet['binding']['request'],packet['binding']['input'],True)
        self.query.store._guard(tenant,True);return value

    @staticmethod
    def _record(row):
        return {k:row[k] for k in ('result_id','payload_raw','payload_sha256','recorded_at')}

    def _verify_artifact(self, packet, parameter_raw, allocation_raw, *, full):
        artifact = packet['artifact'];directory = self.directory/artifact['key']
        with replay.open_harvest_artifact(directory,artifact['sha256'],self.query,packet['tenant_id'],
                packet['parent_result_id'],packet['farm']) as reader:
            _need(reader._root['parameter_raw_utf8'].encode() == parameter_raw
                and reader._root['allocation_raw_utf8'].encode() == allocation_raw
                and reader._root['source'] == packet['source'])
            summary = reader.summary()
            _need(summary['row_count'] == artifact['row_count'] and summary['row_chain_sha256'] == artifact['row_chain_sha256'])
            if full:
                chain = sha256();count = 0
                for start in range(0,artifact['row_count'],replay.LIMITS['page_records']):
                    for row in reader.page(start,replay.LIMITS['page_records'])['records']:
                        chain.update(_canonical(row)+b'\n');count += 1
                _need(count == artifact['row_count'] and chain.hexdigest() == artifact['row_chain_sha256'])

    def put(self, tenant, parent_result_id, farm_ref, parameter_raw, allocation_raw):
        fd = lock = child = None
        try:
            self._binding();_need(self.role == self.policy.publisher)
            original = self._authority(tenant,parent_result_id,farm_ref)
            mass = harvest._mass_parameters(parameter_raw);allocation = harvest._allocation_parameters(allocation_raw,mass)
            harvest._allocation_scope(allocation[0],original)
            base = _base(tenant,parent_result_id,farm_ref,harvest._source(original),
                {'mass_sha256':mass[1],'allocation_sha256':allocation[1]})
            key = _key(base);result_id = VERSION+':'+key
            fd = files._open_directory_nofollow(self.directory);lock = files._file(fd,'.registry-lock',lock=True)
            self._binding();_root_usage(fd)
            row = self._find(tenant,result_id)
            if row is not None:
                packet = self._row(row,tenant,farm_ref)
                _need(all(packet[k] == v for k,v in base.items()))
                self._verify_artifact(packet,parameter_raw,allocation_raw,full=False)
                self._authority(tenant,parent_result_id,farm_ref,original);_root_usage(fd)
                return self._record(row)
            size,count,number = _root_usage(fd)
            _need(size+replay.LIMITS['directory_bytes'] <= LIMITS['root_bytes']
                and count+replay.LIMITS['files'] <= LIMITS['root_files']
                and (files._exists(fd,key) or number < LIMITS['registrations']))
            child = files._directory(fd,key,create=True)
            result = replay.write_harvest_artifact(self.directory/key,self.query,tenant,parent_result_id,farm_ref,parameter_raw,allocation_raw)
            files._same_directory(fd,key,child)
            raw = _packet(base,result);packet = _decode(raw)
            self._verify_artifact(packet,parameter_raw,allocation_raw,full=True)
            self._authority(tenant,parent_result_id,farm_ref,original);_root_usage(fd)
            with self._connection(write=True) as conn:
                _insert(conn,self.policy,self._values(packet,raw))
                row = self._find_on(conn,tenant,result_id);saved = self._row(row,tenant,farm_ref)
                _need(saved == packet and row['payload_raw'] == raw)
                self._authority(tenant,parent_result_id,farm_ref,original)
                files._same_directory(fd,key,child);_root_usage(fd)
            return self._record(row)
        except (PermissionError,files.CalculationCustodyPending):raise
        except Exception:raise HarvestRegistrationHold('harvest research registration unavailable') from None
        finally:
            for handle in (child,lock,fd):
                if handle is not None:os.close(handle)
