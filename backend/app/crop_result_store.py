"""Immutable, tenant/farm-bound custody of server-calculated synthetic crop math."""
from datetime import datetime, time, timedelta
from hashlib import sha256
import hmac
import json
from pathlib import Path
import re

from psycopg import sql

from . import crop_growth_integration as integration
from .crop_growth_integration import integrate_crop
from .crop_growth_rates import ReferenceParameters
from .farm_authoring_storage import FarmAuthoringService, READ_SCOPES as FARM_READ
from .farm_inputs import KST, canonical_farm_inputs
from .jobs import canonical_input_bytes
from .runtime_roles import RuntimeLoginPolicy, NAME
from .thermal_run_store import _canonical, _document, _time


VERSION = 'crop-result-v1'
NOTICE_SHA256 = '96ce8c1f3d7b5473f473417c2785c63b74148edaddc2b9b6d40a6bbe3b7f4b6a'
MAX_REQUEST_BYTES = 16 * 1024 * 1024
MAX_PACKET_BYTES = 64 * 1024 * 1024
READ_SCOPES = FARM_READ + ('crop_result_read',)
WRITE_SCOPES = READ_SCOPES + ('crop_result_write',)
IDENTIFIER = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
DOMAIN = b'ossf-crop-research-custody-v1\0'
STORAGE_CODE_SHA256 = sha256(Path(__file__).read_bytes()).hexdigest()


class CropResultHold(ValueError):
    pass


class CropResultConflict(CropResultHold):
    pass


class CropResultPending(CropResultHold):
    """Another transaction holds this intent; retry the same immutable request."""


def _need(condition):
    if not condition:
        raise CropResultHold('crop research result unavailable')


def _hash(raw):
    return sha256(raw).hexdigest()


def _name(value):
    return type(value) is str and IDENTIFIER.fullmatch(value) is not None


def _intent_lock_key(tenant, study_id, revision):
    raw = _canonical({'domain':VERSION,'tenant_id':tenant,'study_id':study_id,'revision':revision})
    return int.from_bytes(sha256(raw).digest()[:8],'big',signed=True)


def install_crop_result_schema(conn, schema):
    """Provisioner-only additive table; install before fresh explicit role grants."""
    if type(schema) is not str or not NAME.fullmatch(schema):
        raise ValueError('invalid crop result schema')
    namespace = sql.Identifier(schema)
    conn.execute(sql.SQL('''
        CREATE TABLE {}.crop_research_results (
            tenant_id text NOT NULL CHECK (length(tenant_id) BETWEEN 1 AND 200),
            study_id text NOT NULL CHECK (length(study_id) BETWEEN 1 AND 200),
            revision text NOT NULL CHECK (length(revision) BETWEEN 1 AND 200),
            result_id text NOT NULL CHECK (result_id ~ '^crop-result-v1:[0-9a-f]{{64}}$'),
            scenario_id text NOT NULL,
            scenario_revision text NOT NULL,
            registration_job_id uuid NOT NULL,
            registration_sha256 char(64) NOT NULL,
            payload_raw bytea NOT NULL CHECK (octet_length(payload_raw) BETWEEN 1 AND 67108864),
            payload_sha256 char(64) NOT NULL CHECK (payload_sha256=encode(sha256(payload_raw),'hex')),
            integrity_signature char(64) NOT NULL CHECK (integrity_signature ~ '^[0-9a-f]{{64}}$'),
            registered_by text NOT NULL,
            recorded_at timestamptz NOT NULL DEFAULT clock_timestamp(),
            PRIMARY KEY (tenant_id, study_id, revision),
            UNIQUE (tenant_id, result_id),
            FOREIGN KEY (tenant_id, registration_job_id) REFERENCES {}.jobs (tenant_id, job_id),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'schema_version'='crop-result-v1') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'status'='stored_unpublished_research') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'claim_scope'='synthetic_crop_math_only') IS TRUE),
            CHECK ((convert_from(payload_raw,'UTF8')::jsonb->>'result_id'=result_id) IS TRUE)
        )
    ''').format(namespace, namespace))
    conn.execute(sql.SQL('''
        CREATE FUNCTION {}.reject_crop_result_change() RETURNS trigger LANGUAGE plpgsql AS $$
        BEGIN RAISE EXCEPTION 'crop research result is immutable'; END $$
    ''').format(namespace))
    conn.execute(sql.SQL('''
        CREATE TRIGGER crop_result_immutable BEFORE UPDATE OR DELETE ON {}.crop_research_results
        FOR EACH ROW EXECUTE FUNCTION {}.reject_crop_result_change()
    ''').format(namespace, namespace))


class CropResultStore:
    def __init__(self, farms, profile, notice_raw, *, program_rights, integrity_key):
        try:
            _need(type(farms) is FarmAuthoringService and type(profile) is ReferenceParameters
                  and type(notice_raw) is bytes and _hash(notice_raw) == NOTICE_SHA256
                  and type(integrity_key) is bytes and len(integrity_key) >= 32
                  and callable(program_rights) and _name(program_rights.policy_version))
            self.farms, self.profile, self.notice_raw = farms, profile, notice_raw
            self.program_rights, self.integrity_key = program_rights, integrity_key
            self.jobs = farms.replay.jobs
            self._fixed = self._pointers()
            self._guard_binding()
        except Exception:
            raise CropResultHold('crop research authority unavailable') from None

    def _pointers(self):
        return (self.farms, self.farms._pointers(), self.jobs, self.profile, self.notice_raw,
                self.program_rights, self.program_rights.policy_version, self.integrity_key,
                self.jobs._dsn, self.jobs.schema, self.jobs.runtime_identity, self.jobs.audit_runtime_grants)

    def _guard_binding(self):
        self.farms._binding()
        policy, kind = self.jobs.runtime_identity
        _need(self._pointers() == self._fixed and self.farms.replay.jobs is self.jobs
              and type(policy) is RuntimeLoginPolicy and kind == 'authority'
              and policy.crop_result_storage is True and self.jobs.audit_runtime_grants is True
              and _hash(Path(__file__).read_bytes()) == STORAGE_CODE_SHA256
              and integration.CODE_HASHES == {
                  'integrator': _hash(Path(integration.__file__).read_bytes()),
                  'rates': _hash(Path(integration.rates.__file__).read_bytes())})

    def _guard(self, tenant, write=False):
        try:
            self._guard_binding()
            self.farms._guard(tenant,self._fixed[1],WRITE_SCOPES if write else READ_SCOPES)
        except PermissionError:
            raise
        except Exception:
            raise CropResultHold('crop research authority unavailable') from None

    def _request(self, raw):
        request = _document(raw,max_size=MAX_REQUEST_BYTES)
        _need(set(request) == {'study_id','revision','farm','program','rights'}
              and _name(request['study_id']) and _name(request['revision']))
        farm, program, rights = request['farm'], request['program'], request['rights']
        _need(type(farm) is dict and set(farm) == {'scenario_id','scenario_revision','registration_sha256','crop_id'}
              and all(_name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
              and type(farm['registration_sha256']) is str and DIGEST.fullmatch(farm['registration_sha256']))
        _need(type(program) is dict and set(program) == {'initial_state','segments','events','output_times','solver'})
        _, normalized, _, _ = integration._prepare(**program,profile=self.profile)
        blocks = [normalized['initial_state']] + [b for s in normalized['segments'] for b in (s['forcing'],s['removals'])]
        blocks += [e['removals'] for e in normalized['events']]
        seen = {}
        for block in blocks:
            _need(block['origin'] == 'synthetic' and _name(block['input_id'])
                  and (block['input_id'] not in seen or seen[block['input_id']] == block))
            seen[block['input_id']] = block
        grants = ('ownership_asserted','access','store','transform','use','display')
        _need(type(rights) is dict and set(rights) == {'declaration_id','revision','program_sha256','available_at','redistribute',*grants}
              and _name(rights['declaration_id']) and _name(rights['revision'])
              and all(rights[k] is True for k in grants) and rights['redistribute'] is False
              and rights['program_sha256'] == _hash(_canonical(program)))
        _time(rights['available_at'])
        return request, normalized

    def _references(self, tenant, request):
        ref = request['farm']
        registration = self.farms.read_registration(tenant,ref['scenario_id'],
            ref['scenario_revision'],ref['registration_sha256'])
        farm = registration['farm']
        crop = next((c for c in farm.crops if c.crop_id == ref['crop_id']),None)
        _need(crop is not None and _time(request['rights']['available_at']) <= farm.decision_at)
        program = request['program']
        start, end = integration._utc(program['segments'][0]['start']), integration._utc(program['segments'][-1]['end'])
        begin = datetime.combine(farm.period_start,time(),KST)
        finish = datetime.combine(farm.period_end+timedelta(days=1),time(),KST)
        _need(crop.occupancy.start <= start < end <= crop.occupancy.end and begin <= start < end <= finish)
        row = self.farms._find(tenant,ref['scenario_id'],ref['scenario_revision'])
        _need(row is not None and row['input_sha256'] == ref['registration_sha256'])
        return {'registration_job_id':str(row['job_id']), 'registration_sha256':ref['registration_sha256'],
                'farm_sha256':_hash(canonical_farm_inputs(farm)),
                'source_binding_sha256':_hash(canonical_input_bytes(registration['binding'])),
                'crop':crop.model_dump(mode='json'), 'zone_id':farm.facility.zone_id,
                'normalization':'per_m2_floor', 'floor_area':farm.facility.floor_area.model_dump(mode='json'),
                'profile_applicability':'unvalidated_for_registered_crop'}

    def _current(self, tenant, request, binding, write=False):
        self._guard(tenant,write)
        _need(self._references(tenant,request) == binding)
        declaration = json.loads(_canonical(request['rights']))
        uses = ('research_calculation','research_display') if write else ('research_display',)
        for intended_use in uses:
            _need(self.program_rights(tenant,json.loads(_canonical(declaration)),
                  request['rights']['program_sha256'],intended_use) is True)
        self._guard(tenant,write)

    def _find(self, tenant, *, result_id=None, study_id=None, revision=None):
        with self.jobs.connect() as conn:
            if result_id is not None:
                return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND result_id=%s')
                    .format(self.jobs._table('crop_research_results')),(tenant,result_id)).fetchone()
            return conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                .format(self.jobs._table('crop_research_results')),(tenant,study_id,revision)).fetchone()

    def _signature(self, payload):
        return hmac.new(self.integrity_key,DOMAIN+payload,'sha256').hexdigest()

    def _checked(self, row, tenant, farm_ref, write=False):
        _need(row is not None and row['tenant_id'] == tenant and row['payload_sha256'] == _hash(row['payload_raw'])
              and hmac.compare_digest(row['integrity_signature'],self._signature(row['payload_raw'])))
        packet = _document(row['payload_raw'],max_size=MAX_PACKET_BYTES)
        _need(set(packet) == {'schema_version','status','claim_scope','tenant_id','request','binding',
                  'rights_policy_version','storage_code_sha256','profile_raw_utf8','notice_raw_utf8','result','result_id'})
        request, normalized = self._request(_canonical(packet['request']))
        result, manifest = packet['result'], packet['result']['manifest']
        _need(request['farm'] == farm_ref and packet['schema_version'] == VERSION
              and packet['status'] == 'stored_unpublished_research' and packet['claim_scope'] == 'synthetic_crop_math_only'
              and packet['tenant_id'] == tenant
              and packet['result_id'] == VERSION+':'+_hash(_canonical({k:v for k,v in packet.items() if k!='result_id'}))
              and packet['profile_raw_utf8'].encode() == self.profile.raw_bytes
              and packet['notice_raw_utf8'].encode() == self.notice_raw
              and packet['rights_policy_version'] == self.program_rights.policy_version
              and packet['storage_code_sha256'] == STORAGE_CODE_SHA256
              and result['scope'] == 'software_research_only' and result['status'] in ('completed','hold')
              and result['result_sha256'] == integration._hash({k:v for k,v in result.items() if k!='result_sha256'})
              and manifest['profile_sha256'] == self.profile.sha256 and manifest['code_sha256'] == integration.CODE_HASHES
              and manifest['input_sha256'] == integration._hash({'program':normalized,
                  'integrator_version':integration.INTEGRATOR_VERSION,'rate_model_version':integration.rates.MODEL_VERSION,
                  'domain_policy':integration.DOMAIN_POLICY,'profile_sha256':self.profile.sha256,'code_sha256':integration.CODE_HASHES})
              and (row['study_id'],row['revision'],row['result_id'],row['scenario_id'],row['scenario_revision'],
                   str(row['registration_job_id']),row['registration_sha256'],row['registered_by']) ==
                  (request['study_id'],request['revision'],packet['result_id'],farm_ref['scenario_id'],farm_ref['scenario_revision'],
                   packet['binding']['registration_job_id'],farm_ref['registration_sha256'],self.jobs.runtime_identity[0].roles['authority']))
        self._current(tenant,request,packet['binding'],write)
        return {'result_id':row['result_id'],'payload_raw':row['payload_raw'],
                'payload_sha256':row['payload_sha256'],'recorded_at':row['recorded_at']}

    def put(self, tenant, request_raw):
        self._guard(tenant,True)
        try:
            request, _ = self._request(request_raw)
            binding = self._references(tenant,request)
            self._current(tenant,request,binding,True)
            previous = self._find(tenant,study_id=request['study_id'],revision=request['revision'])
            if previous is not None:
                previous_ref = _document(previous['payload_raw'],max_size=MAX_PACKET_BYTES)['request']['farm']
                record = self._checked(previous,tenant,previous_ref,True)
                if _canonical(json.loads(record['payload_raw'])['request']) != request_raw:
                    raise CropResultConflict('conflicting immutable crop research intent')
                self._current(tenant,request,binding,True)
                return record
            result = integrate_crop(**request['program'],profile=self.profile)
            packet = {'schema_version':VERSION,'status':'stored_unpublished_research',
                'claim_scope':'synthetic_crop_math_only','tenant_id':tenant,'request':request,'binding':binding,
                'rights_policy_version':self.program_rights.policy_version,'storage_code_sha256':STORAGE_CODE_SHA256,
                'profile_raw_utf8':self.profile.raw_bytes.decode(),'notice_raw_utf8':self.notice_raw.decode(),'result':result}
            packet['result_id'] = VERSION+':'+_hash(_canonical(packet))
            payload = _canonical(packet); _need(len(payload) <= MAX_PACKET_BYTES)
            self._current(tenant,request,binding,True)
            with self.jobs.connect() as conn:
                locked = conn.execute('SELECT pg_try_advisory_xact_lock(%s) AS acquired',
                    (_intent_lock_key(tenant,request['study_id'],request['revision']),)).fetchone()['acquired']
                if not locked:
                    raise CropResultPending('crop research intent in progress; retry identical request')
                conn.execute(sql.SQL('''
                    INSERT INTO {} (tenant_id,study_id,revision,result_id,scenario_id,scenario_revision,
                        registration_job_id,registration_sha256,payload_raw,payload_sha256,integrity_signature,registered_by)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
                ''').format(self.jobs._table('crop_research_results')),
                    (tenant,request['study_id'],request['revision'],packet['result_id'],request['farm']['scenario_id'],
                     request['farm']['scenario_revision'],binding['registration_job_id'],binding['registration_sha256'],
                     payload,_hash(payload),self._signature(payload),self.jobs.runtime_identity[0].roles['authority']))
                row = conn.execute(sql.SQL('SELECT * FROM {} WHERE tenant_id=%s AND study_id=%s AND revision=%s')
                    .format(self.jobs._table('crop_research_results')),(tenant,request['study_id'],request['revision'])).fetchone()
                record = self._checked(row,tenant,request['farm'],True)
                if row['payload_raw'] != payload:
                    raise CropResultConflict('conflicting immutable crop research intent')
                self._current(tenant,request,binding,True)
                return record
        except (PermissionError,CropResultConflict,CropResultPending):
            raise
        except Exception:
            raise CropResultHold('crop research storage unavailable') from None

    def get(self, tenant, result_id, farm_ref):
        self._guard(tenant)
        try:
            _need(type(result_id) is str and re.fullmatch(r'crop-result-v1:[0-9a-f]{64}',result_id))
            row = self._find(tenant,result_id=result_id)
            if row is None:
                self._guard(tenant)
                return None
            record = self._checked(row,tenant,farm_ref)
            packet = json.loads(record['payload_raw'])
            self._current(tenant,packet['request'],packet['binding'])
            return record
        except PermissionError:
            raise
        except Exception:
            raise CropResultHold('crop research read unavailable') from None
