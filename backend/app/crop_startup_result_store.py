"""Immutable farm-bound custody of server-calculated startup research artifacts."""
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re

from psycopg import sql

from . import crop_startup_artifact as artifact
from . import crop_result_store as previous
from .crop_startup_artifact import calculate_startup_artifact,read_startup_artifact
from .crop_result_store import (CropResultStore,CropResultHold,CropResultConflict,CropResultPending,
    READ_SCOPES,WRITE_SCOPES,_need,_hash,_name,DIGEST)
from .runtime_roles import RuntimeLoginPolicy,NAME
from .thermal_run_store import _canonical,_document,_time


VERSION='crop-result-v3'
MAX_REQUEST_BYTES=2*1024*1024
MAX_PACKET_BYTES=20*1024*1024
DOMAIN=b'ossf-crop-startup-research-custody-v3\0'
STORAGE_CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


def _intent_lock_key(tenant,study_id,revision):
    raw=_canonical({'domain':VERSION,'tenant_id':tenant,'study_id':study_id,'revision':revision})
    return int.from_bytes(sha256(raw).digest()[:8],'big',signed=True)


def install_startup_crop_result_schema(conn,schema):
    """Provisioner-only fresh table before explicit runtime role grants."""
    if type(schema) is not str or not NAME.fullmatch(schema):raise ValueError('invalid startup crop schema')
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL('''
        CREATE TABLE {}.crop_startup_research_results (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            study_id text NOT NULL CHECK (length(study_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            result_id text NOT NULL CHECK (result_id ~ '^crop-result-v3:[0-9a-f]{{64}}$'),
            scenario_id text NOT NULL, scenario_revision text NOT NULL,
            registration_job_id uuid NOT NULL, registration_sha256 char(64) NOT NULL,
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 20971520),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
            integrity_signature char(64) NOT NULL CHECK (integrity_signature ~ '^[0-9a-f]{{64}}$'),
            registered_by text NOT NULL, recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id,study_id,revision), UNIQUE (tenant_id,result_id),
            FOREIGN KEY (tenant_id,registration_job_id) REFERENCES {}.jobs (tenant_id,job_id),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'schema_version'='crop-result-v3') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'status'='stored_unpublished_research') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'claim_scope'='synthetic_crop_math_only') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'result_id'=result_id) IS TRUE)
        )
    ''').format(namespace,namespace))
    conn.execute(sql.SQL('''
        CREATE FUNCTION {}.reject_startup_crop_result_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'startup crop research result is immutable'; END $$
    ''').format(namespace))
    conn.execute(sql.SQL('''
        CREATE TRIGGER crop_startup_result_immutable BEFORE UPDATE OR DELETE ON {}.crop_startup_research_results
        FOR EACH ROW EXECUTE FUNCTION {}.reject_startup_crop_result_change()
    ''').format(namespace,namespace))


class StartupCropResultStore(CropResultStore):
    """Reuse frozen farm/right checks; keep v3 data and grants separate from v1/v2."""
    def __init__(self,farms,growth_profile,cohort_profile,transport_profile,notice_raw,*,program_rights,integrity_key):
        _need(type(cohort_profile) is artifact.PROFILE_TYPES['cohort_profile']
              and type(transport_profile) is artifact.PROFILE_TYPES['transport_profile'])
        self.cohort_profile,self.transport_profile=cohort_profile,transport_profile
        super().__init__(farms,growth_profile,notice_raw,program_rights=program_rights,integrity_key=integrity_key)

    def _pointers(self):
        return super()._pointers()+(self.cohort_profile,self.transport_profile)

    def _profiles(self):
        return {'growth_profile':self.profile,'cohort_profile':self.cohort_profile,'transport_profile':self.transport_profile}

    def _guard_binding(self):
        self.farms._binding();policy,kind=self.jobs.runtime_identity
        _need(self._pointers()==self._fixed and self.farms.replay.jobs is self.jobs
              and type(policy) is RuntimeLoginPolicy and kind=='authority'
              and policy.crop_startup_result_storage is True and self.jobs.audit_runtime_grants is True
              and _hash(Path(__file__).read_bytes())==STORAGE_CODE_SHA256
              and _hash(Path(previous.__file__).read_bytes())==previous.STORAGE_CODE_SHA256)
        artifact._profiles(self._profiles(),self.notice_raw)

    def _request(self,raw):
        request=_document(raw,max_size=MAX_REQUEST_BYTES)
        _need(set(request)=={'study_id','revision','farm','program','rights'}
              and _name(request['study_id']) and _name(request['revision']))
        farm,program,rights=request['farm'],request['program'],request['rights']
        _need(type(farm) is dict and set(farm)=={'scenario_id','scenario_revision','registration_sha256','crop_id'}
              and all(_name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
              and type(farm['registration_sha256']) is str and DIGEST.fullmatch(farm['registration_sha256']))
        _,normalized,_,blocks=artifact._program(_canonical(program))
        _need(all(_name(b['input_id']) for b in blocks))
        grants=('ownership_asserted','access','store','transform','use','display')
        _need(type(rights) is dict and set(rights)=={'declaration_id','revision','program_sha256','available_at','redistribute',*grants}
              and _name(rights['declaration_id']) and _name(rights['revision'])
              and all(rights[k] is True for k in grants) and rights['redistribute'] is False
              and rights['program_sha256']==_hash(_canonical(program)))
        _time(rights['available_at'])
        return request,normalized

    def _find(self,tenant,*,result_id=None,study_id=None,revision=None):
        with self.jobs.connect() as conn:
            target=self.jobs._table('crop_startup_research_results')
            if result_id is not None:
                return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
                    .format(target),(tenant,result_id)).fetchone()
            return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                .format(target),(tenant,study_id,revision)).fetchone()

    def _signature(self,payload):
        return hmac.new(self.integrity_key,DOMAIN+payload,'sha256').hexdigest()

    def _checked(self,row,tenant,farm_ref,write=False):
        _need(row is not None and row['tenant_id']==tenant and row['payload_sha256']==_hash(row['payload_raw'])
              and hmac.compare_digest(row['integrity_signature'],self._signature(row['payload_raw'])))
        packet=_document(row['payload_raw'],max_size=MAX_PACKET_BYTES)
        _need(set(packet)=={'schema_version','status','claim_scope','tenant_id','request','binding',
            'rights_policy_version','storage_code_sha256','binding_code_sha256','artifact','artifact_sha256','result_id'})
        request,_=self._request(_canonical(packet['request']))
        _need(request['farm']==farm_ref and packet['schema_version']==VERSION
              and packet['status']=='stored_unpublished_research' and packet['claim_scope']=='synthetic_crop_math_only'
              and packet['tenant_id']==tenant
              and packet['result_id']==VERSION+':'+_hash(_canonical({k:v for k,v in packet.items() if k!='result_id'}))
              and packet['rights_policy_version']==self.program_rights.policy_version
              and packet['storage_code_sha256']==STORAGE_CODE_SHA256
              and packet['binding_code_sha256']==previous.STORAGE_CODE_SHA256)
        document=read_startup_artifact(_canonical(packet['artifact']),expected_sha256=packet['artifact_sha256'],
            **self._profiles(),notice_raw=self.notice_raw)
        _need(document['program_raw_utf8'].encode()==_canonical(request['program'])
              and document['program_sha256']==request['rights']['program_sha256']
              and (row['study_id'],row['revision'],row['result_id'],row['scenario_id'],row['scenario_revision'],
                   str(row['registration_job_id']),row['registration_sha256'],row['registered_by'])==
                  (request['study_id'],request['revision'],packet['result_id'],farm_ref['scenario_id'],farm_ref['scenario_revision'],
                   packet['binding']['registration_job_id'],farm_ref['registration_sha256'],self.jobs.runtime_identity[0].roles['authority']))
        self._current(tenant,request,packet['binding'],write)
        return {'result_id':row['result_id'],'payload_raw':row['payload_raw'],
                'payload_sha256':row['payload_sha256'],'recorded_at':row['recorded_at']}

    def put(self,tenant,request_raw):
        """Calculate and commit outside HTTP; identical completed retries only read."""
        self._guard(tenant,True)
        try:
            request,_=self._request(request_raw);binding=self._references(tenant,request)
            self._current(tenant,request,binding,True)
            old=self._find(tenant,study_id=request['study_id'],revision=request['revision'])
            if old is not None:
                old_ref=_document(old['payload_raw'],max_size=MAX_PACKET_BYTES)['request']['farm']
                record=self._checked(old,tenant,old_ref,True)
                if _canonical(json.loads(record['payload_raw'])['request'])!=request_raw:
                    raise CropResultConflict('conflicting immutable startup research intent')
                self._current(tenant,request,binding,True);return record
            raw=calculate_startup_artifact(_canonical(request['program']),**self._profiles(),notice_raw=self.notice_raw)
            packet={'schema_version':VERSION,'status':'stored_unpublished_research','claim_scope':'synthetic_crop_math_only',
                'tenant_id':tenant,'request':request,'binding':binding,'rights_policy_version':self.program_rights.policy_version,
                'storage_code_sha256':STORAGE_CODE_SHA256,'binding_code_sha256':previous.STORAGE_CODE_SHA256,
                'artifact':json.loads(raw),'artifact_sha256':_hash(raw)}
            packet['result_id']=VERSION+':'+_hash(_canonical(packet));payload=_canonical(packet)
            _need(len(payload)<=MAX_PACKET_BYTES);self._current(tenant,request,binding,True)
            with self.jobs.connect() as conn:
                acquired=conn.execute('SELECT pg_try_advisory_xact_lock(%s) AS acquired',
                    (_intent_lock_key(tenant,request['study_id'],request['revision']),)).fetchone()['acquired']
                if not acquired:raise CropResultPending('startup research intent in progress; retry identical request')
                target=self.jobs._table('crop_startup_research_results')
                conn.execute(sql.SQL('''INSERT INTO {} (tenant_id,study_id,revision,result_id,scenario_id,scenario_revision,
                    registration_job_id,registration_sha256,payload_raw,payload_sha256,integrity_signature,registered_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING''').format(target),
                    (tenant,request['study_id'],request['revision'],packet['result_id'],request['farm']['scenario_id'],
                     request['farm']['scenario_revision'],binding['registration_job_id'],binding['registration_sha256'],
                     payload,_hash(payload),self._signature(payload),self.jobs.runtime_identity[0].roles['authority']))
                row=conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                    .format(target),(tenant,request['study_id'],request['revision'])).fetchone()
                record=self._checked(row,tenant,request['farm'],True)
                if row['payload_raw']!=payload:raise CropResultConflict('conflicting immutable startup research intent')
                self._current(tenant,request,binding,True)
            self._current(tenant,request,binding,True)
            return record
        except (PermissionError,CropResultConflict,CropResultPending):raise
        except Exception:raise CropResultHold('startup research storage unavailable') from None

    def get(self,tenant,result_id,farm_ref):
        self._guard(tenant)
        try:
            _need(type(result_id) is str and re.fullmatch(r'crop-result-v3:[0-9a-f]{64}',result_id))
            row=self._find(tenant,result_id=result_id)
            if row is None:self._guard(tenant);return None
            record=self._checked(row,tenant,farm_ref);packet=json.loads(record['payload_raw'])
            self._current(tenant,packet['request'],packet['binding']);return record
        except PermissionError:raise
        except Exception:raise CropResultHold('startup research read unavailable') from None
