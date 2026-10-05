"""Immutable DB references to current-rights, server-signed crop research files."""
from contextlib import contextmanager
from copy import deepcopy
from hashlib import sha256
import hmac
import json
from pathlib import Path
from uuid import UUID

from psycopg import sql

from . import crop_cycle_artifact as artifact
from . import crop_cycle_farm_binding as farms
from . import crop_cycle_input_stream as inputs
from . import crop_cycle_result_schema as schema
from . import crop_cycle_server_custody as server
from .crop_result_store import _intent_lock_key,_name
from .thermal_run_store import _canonical,_document

VERSION=schema.VERSION
MAX_PACKET_BYTES=schema.MAX_METADATA_BYTES
DOMAIN=b'ossf-crop-cycle-result-v1\0'
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
SCHEMA_SHA256=sha256(Path(schema.__file__).read_bytes()).hexdigest()
CODE={'storage_code_sha256':CODE_SHA256,'server_custody_code_sha256':server.CODE_SHA256,
    'schema_code_sha256':SCHEMA_SHA256,'server_dependency_sha256':server.DEPENDENCY_SHA256}
_CODE_RAW=_canonical(CODE)


def _need(condition):
    if not condition:raise server.CycleCustodyHold('cycle research result unavailable')


def _closed(value,keys):_need(type(value) is dict and set(value)==set(keys))


def _integer(value,minimum,maximum):_need(type(value) is int and minimum<=value<=maximum)


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
        and sha256(Path(schema.__file__).read_bytes()).hexdigest()==SCHEMA_SHA256
        and _canonical(CODE)==_CODE_RAW and MAX_PACKET_BYTES==schema.MAX_METADATA_BYTES)
    server._pins()


def _progress(value):
    _closed(value,('version','scope','intent_sha256','binding_sha256','input_root_sha256','context_sha256',
        'custody_code_sha256','head_sha256','proof_sha256','header_sha256','artifact_sha256','status',
        'commit_count','steps','planned_steps','counts','storage_bytes','file_count'))
    _need(value['version']==server.VERSION and value['scope']==server.SCOPE
        and value['custody_code_sha256']==server.CODE_SHA256 and value['status'] in ('completed','hold'))
    for k in ('intent_sha256','binding_sha256','input_root_sha256','context_sha256','custody_code_sha256',
        'head_sha256','proof_sha256','header_sha256','artifact_sha256'):_need(inputs._digest(value[k]))
    _integer(value['planned_steps'],1,40000000);_integer(value['steps'],0,value['planned_steps'])
    _need(value['status']!='completed' or value['steps']==value['planned_steps'])
    _integer(value['commit_count'],1,artifact.LIMITS['commits'])
    _integer(value['storage_bytes'],1,artifact.LIMITS['directory_bytes']);_integer(value['file_count'],1,artifact.LIMITS['files'])
    _closed(value['counts'],('samples','events'))
    for v in value['counts'].values():_integer(v,0,inputs.MAX_RECORDS)
    return {'ref':artifact.VERSION+':'+value['artifact_sha256'],'sha256':value['artifact_sha256'],
        'header_sha256':value['header_sha256'],'status':value['status'],'steps':value['steps'],
        'planned_steps':value['planned_steps'],'sample_count':value['counts']['samples'],
        'event_count':value['counts']['events'],'commit_count':value['commit_count'],
        'storage_bytes':value['storage_bytes'],'file_count':value['file_count']}


def _packet(binding_raw,progress_raw,resolver_version,notice_raw):
    binding=json.loads(binding_raw);request=binding['request'];registration=binding['registration']
    progress=json.loads(progress_raw)
    value={'schema_version':VERSION,'status':'stored_unpublished_research','claim_scope':server.SCOPE,
        'tenant_id':binding['tenant_id'],'study_id':request['study_id'],'revision':request['revision'],
        'farm':{'scenario_id':request['farm']['scenario_id'],'scenario_revision':request['farm']['scenario_revision'],
            'registration_job_id':registration['registration_job_id'],'registration_sha256':registration['registration_sha256']},
        'input_root_sha256':binding['input']['root_sha256'],'artifact':_progress(progress),'binding':binding,
        'policies':{'input_rights_version':binding['rights_policy_version'],'resolver_version':resolver_version,
            'notice_sha256':sha256(notice_raw).hexdigest(),'server_progress':progress},'code':CODE}
    value['result_id']=VERSION+':'+sha256(_canonical(value)).hexdigest()
    raw=_canonical(value);_decode(raw);return raw


def _decode(raw):
    try:
        _pins();value=_document(raw,max_size=MAX_PACKET_BYTES)
        _closed(value,('schema_version','status','claim_scope','result_id','tenant_id','study_id','revision',
            'farm','input_root_sha256','artifact','binding','policies','code'))
        _need(value['schema_version']==VERSION and value['status']=='stored_unpublished_research'
            and value['claim_scope']==server.SCOPE and value['code']==CODE)
        _closed(value['code'],CODE);_closed(value['farm'],('scenario_id','scenario_revision','registration_job_id','registration_sha256'))
        _closed(value['binding'],('version','scope','tenant_id','request','registration','input','rights_policy_version','binding_code_sha256'))
        binding=value['binding'];request=binding['request'];registration=binding['registration']
        _need(binding['version']==farms.VERSION and binding['scope']==server.SCOPE
            and binding['binding_code_sha256']==farms.CODE_SHA256)
        _closed(request,('study_id','revision','farm','input','rights'))
        _closed(request['farm'],('scenario_id','scenario_revision','registration_sha256','crop_id'))
        _need(all(_name(value[k]) and value[k]==v for k,v in (
            ('tenant_id',binding['tenant_id']),('study_id',request['study_id']),('revision',request['revision']))))
        _need(value['farm']=={'scenario_id':request['farm']['scenario_id'],'scenario_revision':request['farm']['scenario_revision'],
            'registration_job_id':registration['registration_job_id'],'registration_sha256':registration['registration_sha256']}
            and value['farm']['registration_sha256']==request['farm']['registration_sha256']
            and str(UUID(value['farm']['registration_job_id']))==value['farm']['registration_job_id'])
        _closed(value['policies'],('input_rights_version','resolver_version','notice_sha256','server_progress'))
        policies=value['policies'];progress=policies['server_progress']
        _need(policies['input_rights_version']==binding['rights_policy_version'] and _name(policies['input_rights_version'])
            and _name(policies['resolver_version']) and inputs._digest(policies['notice_sha256']))
        _need(_canonical(value['artifact'])==_canonical(_progress(progress)) and value['input_root_sha256']==progress['input_root_sha256']
            ==binding['input']['root_sha256']==request['input']['root_sha256']
            and progress['binding_sha256']==sha256(_canonical(binding)).hexdigest())
        _need(value['result_id']==VERSION+':'+sha256(_canonical({k:v for k,v in value.items() if k!='result_id'})).hexdigest())
        return value
    except server.CycleCustodyHold:raise
    except Exception:raise server.CycleCustodyHold('cycle research result unavailable') from None


class CycleCropResultStore:
    def __init__(self,custody,*,integrity_key):
        try:
            _need(type(custody) is server.CycleServerCustody and type(integrity_key) is bytes
                and 32<=len(integrity_key)<=4096 and integrity_key!=custody.integrity_key)
            self.server,self.jobs,self.integrity_key=custody,custody.binding.jobs,integrity_key
            self._fixed=self._pointers();self._binding()
        except Exception:raise server.CycleCustodyHold('cycle research authority unavailable') from None

    def _pointers(self):
        return (self.server,self.server._pointers(),self.server.binding,self.jobs,self.integrity_key,
            self.jobs._dsn,self.jobs.schema,self.jobs.runtime_identity,self.jobs.audit_runtime_grants)

    def _binding(self):
        _pins();_need(self._pointers()==self._fixed and self.jobs is self.server.binding.jobs);self.server._binding()

    def _guard(self,tenant,write=False):
        self._binding();self.server.binding._guard(tenant,write)

    def _find(self,tenant,*,result_id=None,study_id=None,revision=None):
        with self.jobs.connect() as conn:
            table=self.jobs._table(schema.TABLE)
            if result_id is not None:
                return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
                    .format(table),(tenant,result_id)).fetchone()
            return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                .format(table),(tenant,study_id,revision)).fetchone()

    def _signature(self,raw):return hmac.new(self.integrity_key,DOMAIN+raw,'sha256').hexdigest()

    def _row(self,row,tenant,farm_ref):
        _need(row is not None and row['tenant_id']==tenant and type(row['payload_raw']) is bytes
            and row['payload_sha256']==sha256(row['payload_raw']).hexdigest()
            and hmac.compare_digest(row['integrity_signature'],self._signature(row['payload_raw'])))
        packet=_decode(row['payload_raw']);request=self.server.binding._request(_canonical(packet['binding']['request']))
        _need(packet['tenant_id']==tenant and request['farm']==farm_ref)
        columns={k:packet[k] for k in ('tenant_id','study_id','revision','result_id','input_root_sha256')}
        columns.update(packet['farm']);columns['registration_job_id']=str(row['registration_job_id'])
        _need(columns['registration_job_id']==packet['farm']['registration_job_id'])
        columns.update({k:v for k,v in packet['artifact'].items() if k not in ('ref','sha256','header_sha256','status')})
        columns.update(artifact_ref=packet['artifact']['ref'],artifact_sha256=packet['artifact']['sha256'],
            artifact_header_sha256=packet['artifact']['header_sha256'],artifact_status=packet['artifact']['status'],
            registered_by=self.jobs.runtime_identity[0].roles['authority'])
        _need(all(str(row[k])==v if k=='registration_job_id' else row[k]==v for k,v in columns.items()))
        return packet

    def _record(self,row):
        return {k:row[k] for k in ('result_id','payload_raw','payload_sha256','recorded_at')}

    def _current(self,tenant,request_raw,journal,progress_raw,write=False):
        self._guard(tenant,write)
        self.server.binding.current(tenant,request_raw,journal.context.reader,journal.binding_raw,write=write)
        journal._guard();_need(journal._progress()==progress_raw)

    def put(self,tenant,request_raw):
        try:
            self._guard(tenant,True);request=self.server.binding._request(request_raw)
            with self.server._open(tenant,request_raw,False) as journal:
                progress=journal.inspect();self._current(tenant,request_raw,journal,progress,True)
                payload=_packet(journal.binding_raw,progress,self.server.input_resolver.version,self.server.binding.notice_raw)
                packet=_decode(payload)
                with self.jobs.connect() as conn:
                    acquired=conn.execute('SELECT pg_try_advisory_xact_lock(%s) AS acquired',
                        (_intent_lock_key(tenant,request['study_id'],request['revision']),)).fetchone()['acquired']
                    if not acquired:raise server.CycleCustodyPending('cycle research publication busy')
                    values={k:packet[k] for k in ('tenant_id','study_id','revision','result_id','input_root_sha256')}
                    values.update(packet['farm'])
                    values.update({k:v for k,v in packet['artifact'].items() if k not in ('ref','sha256','header_sha256','status')})
                    values.update(artifact_ref=packet['artifact']['ref'],artifact_sha256=packet['artifact']['sha256'],
                        artifact_header_sha256=packet['artifact']['header_sha256'],artifact_status=packet['artifact']['status'],
                        payload_raw=payload,payload_sha256=sha256(payload).hexdigest(),integrity_signature=self._signature(payload),
                        registered_by=self.jobs.runtime_identity[0].roles['authority'])
                    table=self.jobs._table(schema.TABLE)
                    conn.execute(sql.SQL('INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING').format(table,
                        sql.SQL(',').join(map(sql.Identifier,values)),sql.SQL(',').join(sql.Placeholder() for _ in values)),tuple(values.values()))
                    row=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                        .format(table),(tenant,request['study_id'],request['revision'])).fetchone()
                    self._row(row,tenant,request['farm'])
                    if row['payload_raw']!=payload:raise server.CycleCustodyConflict('cycle research revision conflict')
                    self._current(tenant,request_raw,journal,progress,True)
                self._current(tenant,request_raw,journal,progress,True);return self._record(row)
        except (PermissionError,server.CycleCustodyConflict,server.CycleCustodyPending):raise
        except Exception:raise server.CycleCustodyHold('cycle research publication unavailable') from None

    @contextmanager
    def _read(self,tenant,result_id,farm_ref):
        self._guard(tenant)
        _need(type(result_id) is str and result_id.startswith(VERSION+':') and inputs._digest(result_id[len(VERSION)+1:]))
        row=self._find(tenant,result_id=result_id)
        if row is None:self._guard(tenant);yield None,None,None;return
        packet=self._row(row,tenant,farm_ref);request_raw=_canonical(packet['binding']['request'])
        with self.server._open(tenant,request_raw,False) as journal:
            _need(journal.binding_raw==_canonical(packet['binding'])
                and packet['policies']['resolver_version']==self.server.input_resolver.version
                and packet['policies']['notice_sha256']==sha256(self.server.binding.notice_raw).hexdigest())
            yield row,packet,journal
            self._guard(tenant)

    def get(self,tenant,result_id,farm_ref):
        try:
            with self._read(tenant,result_id,farm_ref) as (row,packet,journal):
                if row is None:return None
                _need(journal.inspect()==_canonical(packet['policies']['server_progress']))
                return self._record(row)
        except (PermissionError,server.CycleCustodyConflict,server.CycleCustodyPending):raise
        except Exception:raise server.CycleCustodyHold('cycle research read unavailable') from None

    def page(self,tenant,result_id,farm_ref,kind,start=0,limit=None):
        try:
            with self._read(tenant,result_id,farm_ref) as (row,packet,journal):
                if row is None:return None
                return journal.page(_canonical(packet['policies']['server_progress']),kind,start,limit)
        except (PermissionError,server.CycleCustodyConflict,server.CycleCustodyPending):raise
        except Exception:raise server.CycleCustodyHold('cycle research page unavailable') from None

    def summary(self,tenant,result_id,farm_ref):
        """Read original terminal manifest/hold evidence for the later typed API."""
        try:
            with self._read(tenant,result_id,farm_ref) as (row,packet,journal):
                if row is None:return None
                expected=_canonical(packet['policies']['server_progress'])
                journal._guard();_need(journal._progress()==expected)
                value=deepcopy(journal.writer._summary)
                _need(type(value) is dict and 1<=len(_canonical(value))<=artifact.LIMITS['root_bytes'])
                journal._guard();_need(journal._progress()==expected)
                return value
        except (PermissionError,server.CycleCustodyConflict,server.CycleCustodyPending):raise
        except Exception:raise server.CycleCustodyHold('cycle research summary unavailable') from None
