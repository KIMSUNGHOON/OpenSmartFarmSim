"""Current registered farm and explicit synthetic input-root rights binding."""
from datetime import datetime,time,timedelta
from hashlib import sha256
import json
from pathlib import Path

from . import crop_cycle_input_stream as inputs
from . import crop_result_store as previous
from . import crop_startup_artifact as startup
from .crop_result_store import READ_SCOPES,WRITE_SCOPES,_name
from .farm_authoring_storage import FarmAuthoringService
from .farm_inputs import KST,canonical_farm_inputs
from .jobs import canonical_input_bytes
from .runtime_roles import RuntimeLoginPolicy
from .thermal_run_store import _canonical,_document,_time

VERSION='crop-cycle-farm-binding-v1'
RIGHTS_VERSION='crop-cycle-input-rights-v1'
MAX_BINDING_BYTES=128*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()


class CycleFarmBindingHold(ValueError):
    pass


def _need(condition):
    if not condition:raise CycleFarmBindingHold('cycle farm input binding unavailable')


class CycleFarmBinding:
    def __init__(self,farms,growth_profile,cohort_profile,transport_profile,notice_raw,*,input_rights):
        try:
            _need(type(farms) is FarmAuthoringService and callable(input_rights) and _name(input_rights.policy_version))
            self.farms=farms;self.jobs=farms.replay.jobs
            self.growth_profile,self.cohort_profile,self.transport_profile=growth_profile,cohort_profile,transport_profile
            self.notice_raw,self.input_rights=notice_raw,input_rights
            self._fixed=self._pointers();self._binding()
        except Exception:raise CycleFarmBindingHold('cycle farm input authority unavailable') from None

    def _profiles(self):
        return dict(growth_profile=self.growth_profile,cohort_profile=self.cohort_profile,
            transport_profile=self.transport_profile)

    def _pointers(self):
        return (self.farms,self.farms._pointers(),self.jobs,self.growth_profile,self.cohort_profile,
            self.transport_profile,self.notice_raw,self.input_rights,self.input_rights.policy_version,
            self.jobs._dsn,self.jobs.schema,self.jobs.runtime_identity,self.jobs.audit_runtime_grants)

    def _binding(self):
        self.farms._binding();policy,kind=self.jobs.runtime_identity
        _need(self._pointers()==self._fixed and self.farms.replay.jobs is self.jobs
            and type(policy) is RuntimeLoginPolicy and kind=='authority'
            and policy.crop_cycle_result_storage is True and self.jobs.audit_runtime_grants is True
            and sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
            and sha256(Path(previous.__file__).read_bytes()).hexdigest()==previous.STORAGE_CODE_SHA256
            and sha256(Path(inputs.__file__).read_bytes()).hexdigest()==inputs.CODE_SHA256
            and type(self.notice_raw) is bytes and sha256(self.notice_raw).hexdigest()==previous.NOTICE_SHA256)
        startup._profiles(self._profiles(),self.notice_raw)

    def _guard(self,tenant,write):
        self._binding()
        self.farms._guard(tenant,self._fixed[1],WRITE_SCOPES if write else READ_SCOPES)

    def _request(self,raw):
        request=_document(raw,max_size=MAX_BINDING_BYTES)
        _need(set(request)=={'study_id','revision','farm','input','rights'}
            and _name(request['study_id']) and _name(request['revision']))
        farm,source,rights=request['farm'],request['input'],request['rights']
        _need(type(farm) is dict and set(farm)=={'scenario_id','scenario_revision','registration_sha256','crop_id'}
            and all(_name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
            and inputs._digest(farm['registration_sha256']))
        _need(type(source) is dict and set(source)=={'schema_version','root_sha256','program_id'}
            and source['schema_version']==inputs.VERSION and inputs._digest(source['root_sha256'])
            and _name(source['program_id']))
        grants=('ownership_asserted','access','store','transform','use','display')
        _need(type(rights) is dict and set(rights)=={'schema_version','declaration_id','revision',
            'input_root_sha256','available_at','redistribute',*grants}
            and rights['schema_version']==RIGHTS_VERSION and _name(rights['declaration_id']) and _name(rights['revision'])
            and all(rights[k] is True for k in grants) and rights['redistribute'] is False
            and rights['input_root_sha256']==source['root_sha256'])
        _time(rights['available_at'])
        return request

    def _input(self,request,reader):
        _need(type(reader) is inputs.InputPacket and not reader.closed)
        root=reader.manifest
        _need(reader.root_sha256==request['input']['root_sha256']
            and root['program_id']==request['input']['program_id'] and root['version']==inputs.VERSION
            and _canonical(root)==reader._raw and reader._root==root
            and sha256(inputs._read(reader._fd,'root.json',inputs.MAX_ROOT_BYTES)).hexdigest()==reader.root_sha256)
        reader._validate_root(inputs._profiles(**self._profiles()))
        reader._cache.clear();reader._seen.clear();reader._referenced_bytes=len(reader._raw)
        reader._preflight()
        _need(inputs._hash({**root,'streams':{k:v for k,v in root['streams'].items() if k!='outputs'}})
            ==reader.calculation_sha256)
        return {'root_sha256':reader.root_sha256,'calculation_sha256':reader.calculation_sha256,
            'program_id':root['program_id'],'period':root['period'],'plan':reader.plan,
            'profile_sha256':root['profile_sha256'],'normalization_sha256':root['normalization_sha256'],
            'python_version':root['python_version']}

    def _registration(self,tenant,request,source):
        ref=request['farm']
        registration=self.farms.read_registration(tenant,ref['scenario_id'],ref['scenario_revision'],ref['registration_sha256'])
        farm=registration['farm'];crop=next((c for c in farm.crops if c.crop_id==ref['crop_id']),None)
        _need(crop is not None and _time(request['rights']['available_at'])<=farm.decision_at)
        start,end=(inputs.physical._utc(source['period'][k]) for k in ('start','end'))
        begin=datetime.combine(farm.period_start,time(),KST)
        finish=datetime.combine(farm.period_end+timedelta(days=1),time(),KST)
        _need(crop.occupancy.start<=start<end<=crop.occupancy.end and begin<=start<end<=finish)
        row=self.farms._find(tenant,ref['scenario_id'],ref['scenario_revision'])
        _need(row is not None and row['input_sha256']==ref['registration_sha256'])
        return {'registration_job_id':str(row['job_id']),'registration_sha256':ref['registration_sha256'],
            'farm_sha256':sha256(canonical_farm_inputs(farm)).hexdigest(),
            'source_binding_sha256':sha256(canonical_input_bytes(registration['binding'])).hexdigest(),
            'crop':crop.model_dump(mode='json'),'zone_id':farm.facility.zone_id,'normalization':'per_m2_floor',
            'floor_area':farm.facility.floor_area.model_dump(mode='json'),
            'profile_applicability':'unvalidated_for_registered_crop'}

    def _bind(self,tenant,raw,reader,write):
        _need(type(write) is bool)
        self._guard(tenant,write);request=self._request(raw);source=self._input(request,reader)
        registration=self._registration(tenant,request,source)
        for use in (('research_calculation','research_display') if write else ('research_display',)):
            declaration=json.loads(_canonical(request['rights']))
            _need(self.input_rights(tenant,declaration,source['root_sha256'],use) is True)
            _need(_canonical(declaration)==_canonical(request['rights']))
        self._guard(tenant,write)
        _need(self._input(request,reader)==source)
        _need(self._registration(tenant,request,source)==registration)
        self._guard(tenant,write)
        binding={'version':VERSION,'scope':'synthetic_crop_math_only','tenant_id':tenant,'request':request,
            'registration':registration,'input':source,'rights_policy_version':self.input_rights.policy_version,
            'binding_code_sha256':CODE_SHA256}
        result=_canonical(binding);_need(len(result)<=MAX_BINDING_BYTES)
        return result

    def prepare(self,tenant,request_raw,reader):
        try:return self._bind(tenant,request_raw,reader,True)
        except PermissionError:raise
        except Exception:raise CycleFarmBindingHold('cycle farm input binding unavailable') from None

    def current(self,tenant,request_raw,reader,expected_binding_raw,*,write=False):
        try:
            _need(type(expected_binding_raw) is bytes and 1<=len(expected_binding_raw)<=MAX_BINDING_BYTES)
            result=self._bind(tenant,request_raw,reader,write)
            _need(result==expected_binding_raw)
            return result
        except PermissionError:raise
        except Exception:raise CycleFarmBindingHold('cycle farm input binding unavailable') from None
