"""Current registered farm/source rights for authenticated joint inputs."""
from datetime import datetime,time,timedelta
from hashlib import sha256
import json
from pathlib import Path

from . import crop_climate_joint_input_evidence as evidence
from . import farm_authoring_storage as authored
from . import crop_result_store as permissions
from . import runtime_roles
from . import thermal_run_store as documents
from . import farm_inputs
from . import jobs

VERSION='joint-crop-climate-farm-binding-v1'
RIGHTS_VERSION='joint-crop-climate-input-rights-v1'
MAX_BINDING_BYTES=128*1024
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES={'input_evidence':evidence,'farm_authority':authored,'farm_inputs':farm_inputs,'job_inputs':jobs,
    'permission_scopes':permissions,'runtime_roles':runtime_roles,'canonical_documents':documents}
DEPENDENCY_SHA256={k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in _MODULES.items()}
_DEPENDENCY_RAW=documents._canonical(DEPENDENCY_SHA256)


class JointFarmBindingHold(ValueError):
    """No current farm/source binding for these authenticated joint inputs."""


def _need(condition):
    if not condition:raise JointFarmBindingHold('joint crop climate farm binding unavailable')


class JointFarmBinding:
    def __init__(self,farms,input_authority,*,input_rights):
        try:
            _need(type(farms) is authored.FarmAuthoringService
                and type(input_authority) is evidence.JointInputEvidenceAuthority
                and callable(input_rights) and permissions._name(input_rights.policy_version))
            self.farms=farms;self.jobs=farms.replay.jobs
            self.input_authority=input_authority;self.input_rights=input_rights
            self._fixed=self._pointers();self._binding()
        except Exception:raise JointFarmBindingHold('joint crop climate farm authority unavailable') from None

    def _pointers(self):
        return (self.farms,self.farms._pointers(),self.jobs,self.input_authority,self.input_rights,
            self.input_rights.policy_version,self.jobs._dsn,self.jobs.schema,
            self.jobs.runtime_identity,self.jobs.audit_runtime_grants)

    def _binding(self):
        self.farms._binding();self.input_authority._binding();policy,kind=self.jobs.runtime_identity
        _need(self._pointers()==self._fixed and self.farms.replay.jobs is self.jobs
            and type(policy) is runtime_roles.RuntimeLoginPolicy and kind=='authority'
            and policy.crop_cycle_result_storage is True and self.jobs.audit_runtime_grants is True
            and sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
            and documents._canonical(DEPENDENCY_SHA256)==_DEPENDENCY_RAW
            and {k:sha256(Path(m.__file__).read_bytes()).hexdigest() for k,m in _MODULES.items()}==DEPENDENCY_SHA256
            and MAX_BINDING_BYTES==128*1024)

    def _guard(self,tenant,write):
        self._binding()
        self.farms._guard(tenant,self._fixed[1],permissions.WRITE_SCOPES if write else permissions.READ_SCOPES)

    def _request(self,raw):
        request=documents._document(raw,max_size=MAX_BINDING_BYTES)
        _need(set(request)=={'study_id','revision','farm','input','rights'}
            and permissions._name(request['study_id']) and permissions._name(request['revision']))
        farm,source,rights=request['farm'],request['input'],request['rights']
        _need(type(farm) is dict and set(farm)=={'scenario_id','scenario_revision','registration_sha256','crop_id'}
            and all(permissions._name(farm[k]) for k in ('scenario_id','scenario_revision','crop_id'))
            and evidence.continuation._digest(farm['registration_sha256']))
        hashes=('source_sha256','context_sha256','time_binding_sha256','evidence_sha256')
        _need(type(source) is dict and set(source)=={'schema_version','program_id',*hashes}
            and source['schema_version']==evidence.SOURCE_VERSION and permissions._name(source['program_id'])
            and all(evidence.continuation._digest(source[k]) for k in hashes))
        grants=('ownership_asserted','access','store','transform','use','display')
        _need(type(rights) is dict and set(rights)=={'schema_version','declaration_id','revision',
            'input_source_sha256','available_at','redistribute',*grants}
            and rights['schema_version']==RIGHTS_VERSION and permissions._name(rights['declaration_id'])
            and permissions._name(rights['revision']) and all(rights[k] is True for k in grants)
            and rights['redistribute'] is False and rights['input_source_sha256']==source['source_sha256'])
        documents._time(rights['available_at']);return request

    def _input(self,request,directory,evidence_raw):
        source=request['input']
        _need(type(evidence_raw) is bytes and 0<len(evidence_raw)<=evidence.MAX_EVIDENCE_BYTES
            and sha256(evidence_raw).hexdigest()==source['evidence_sha256'])
        checked=self.input_authority.verify(directory,source['source_sha256'],evidence_raw,
            expected_context_sha256=source['context_sha256'],expected_binding_sha256=source['time_binding_sha256'])
        _need(type(checked) is evidence.VerifiedJointInputEvidence and checked.rights_or_gate_approval is False)
        record=checked.record;program=record['program'];binding=record['binding']
        _need(program['scenario']['input_id']==source['program_id'])
        review=evidence.files.inputs._json(evidence_raw)['payload']['review']
        return {'source_sha256':checked.source_sha256,'program_id':source['program_id'],
            'period':{'start':binding['start_utc'],'end':binding['end_utc']},
            'context_sha256':record['context_sha256'],'time_binding_sha256':record['binding_sha256'],
            'evidence_sha256':checked.evidence_sha256,'initial_state_sha256':record['initial_state_sha256'],
            'model_identity':record['manifest']['identity'],'review':review,
            'normalization_version':evidence.NORMALIZATION_VERSION,'qc_version':evidence.QC_VERSION,
            'input_evidence_version':evidence.VERSION}

    def _rights(self,tenant,request,source,write):
        for use in (('research_calculation','research_display') if write else ('research_display',)):
            declaration=json.loads(documents._canonical(request['rights']))
            _need(self.input_rights(tenant,declaration,source['source_sha256'],use) is True)
            _need(documents._canonical(declaration)==documents._canonical(request['rights']))

    def _registration(self,tenant,request,source):
        ref=request['farm']
        registration=self.farms.read_registration(tenant,ref['scenario_id'],ref['scenario_revision'],ref['registration_sha256'])
        farm=registration['farm'];crop=next((c for c in farm.crops if c.crop_id==ref['crop_id']),None)
        _need(crop is not None and documents._time(request['rights']['available_at'])<=farm.decision_at)
        start,end=(documents._time(source['period'][k]) for k in ('start','end'))
        begin=datetime.combine(farm.period_start,time(),farm_inputs.KST)
        finish=datetime.combine(farm.period_end+timedelta(days=1),time(),farm_inputs.KST)
        _need(crop.occupancy.start<=start<end<=crop.occupancy.end and begin<=start<end<=finish)
        row=self.farms._find(tenant,ref['scenario_id'],ref['scenario_revision'])
        _need(row is not None and row['input_sha256']==ref['registration_sha256'])
        return {'registration_job_id':str(row['job_id']),'registration_sha256':ref['registration_sha256'],
            'farm_sha256':sha256(farm_inputs.canonical_farm_inputs(farm)).hexdigest(),
            'source_binding_sha256':sha256(jobs.canonical_input_bytes(registration['binding'])).hexdigest(),
            'crop':crop.model_dump(mode='json'),'zone_id':farm.facility.zone_id,'normalization':'per_m2_floor',
            'floor_area':farm.facility.floor_area.model_dump(mode='json'),
            'profile_applicability':'unvalidated_for_registered_crop'}

    def _bind(self,tenant,request_raw,directory,evidence_raw,write):
        _need(type(write) is bool);self._guard(tenant,write)
        request=self._request(request_raw);source=self._input(request,directory,evidence_raw)
        registration=self._registration(tenant,request,source);self._rights(tenant,request,source,write)
        self._guard(tenant,write);self._rights(tenant,request,source,write);self._guard(tenant,write)
        _need(self._input(request,directory,evidence_raw)==source
            and self._registration(tenant,request,source)==registration)
        self._guard(tenant,write)
        result=documents._canonical({'version':VERSION,'scope':'synthetic_joint_crop_climate_math_only','G0_G4':'not_assessed',
            'tenant_id':tenant,'request':request,'registration':registration,'input':source,
            'rights_policy_version':self.input_rights.policy_version,'binding_code_sha256':CODE_SHA256,
            'binding_dependency_sha256':DEPENDENCY_SHA256})
        _need(len(result)<=MAX_BINDING_BYTES);return result

    def prepare(self,tenant,request_raw,directory,evidence_raw):
        try:return self._bind(tenant,request_raw,directory,evidence_raw,True)
        except PermissionError:raise
        except Exception:raise JointFarmBindingHold('joint crop climate farm binding unavailable') from None

    def current(self,tenant,request_raw,directory,evidence_raw,expected_binding_raw,*,write=False):
        try:
            _need(type(expected_binding_raw) is bytes and 0<len(expected_binding_raw)<=MAX_BINDING_BYTES)
            result=self._bind(tenant,request_raw,directory,evidence_raw,write)
            _need(result==expected_binding_raw);return result
        except PermissionError:raise
        except Exception:raise JointFarmBindingHold('joint crop climate farm binding unavailable') from None
