"""Calculation-free current reads of original server-calculated leaf appearance results."""
from functools import wraps
from hashlib import sha256
import hmac
from pathlib import Path
from uuid import UUID

from . import crop_leaf_appearance_farm_binding as farms
from . import crop_leaf_appearance_artifact_reader as reader
from . import crop_morphology_signed_artifact as parent_signed
from .crop_morphology_artifact_reader import FLAGS
from .crop_morphology_artifact_io import MorphologyBlobStore
from .content_access import ContentAccess


VERSION='leaf-appearance-server-calculated-artifact-v1'
DOMAIN=b'ossf-leaf-appearance-server-calculated-artifact-v1\0'
PROOF_MAX=128*1024
RETURN_MAX=2*1024**2
PROGRAM_MAX=2*1024**2
_ROOT=Path(__file__).resolve().parents[2]
_PATHS=tuple('backend/app/'+name+'.py' for name in ('crop_leaf_appearance_signed_artifact',
    'crop_leaf_appearance_signed_producer','crop_leaf_appearance_farm_binding','crop_leaf_appearance_input_evidence',
    'crop_leaf_appearance_artifact_reader','crop_morphology_artifact_io','content_access'))
_HASH_FIELDS=('program_sha256','source_sha256','input_evidence_sha256','binding_sha256','numerical_root_sha256',
    'parent_result_sha256','parent_numerical_root_sha256')
_FIELDS={'schema_version',*FLAGS,'issuer_id','key_id','tenant_id','study_id','revision','calculated_at',
    'code_sha256','parent_job_id','parent_calculated_at',*_HASH_FIELDS}
_FLAGS=dict(FLAGS)


class LeafAppearanceSignedArtifactHold(ValueError):
    """No currently permitted original server-calculated leaf appearance result."""


def _need(condition):
    if not condition:
        raise LeafAppearanceSignedArtifactHold('signed leaf appearance artifact unavailable')


def _checked(fn):
    @wraps(fn)
    def run(*args,**kwargs):
        try:return fn(*args,**kwargs)
        except PermissionError:raise
        except Exception:raise LeafAppearanceSignedArtifactHold('signed leaf appearance artifact unavailable') from None
    return run


def _code_pins():
    return {p:sha256((_ROOT/p).read_bytes()).hexdigest() for p in _PATHS}


_CODE_PINS=_code_pins()


def _linked(manifest,binding,program_raw):
    source,parent=binding['input'],binding['parent'];program=reader._parse(program_raw,PROGRAM_MAX)
    _need(manifest['source_program_sha256']==sha256(program_raw).hexdigest()==source['program_sha256']
        and manifest['source_program_bytes']==len(program_raw)
        and manifest['model_versions']==source['model_versions']==reader.ROOT_CONSTANTS['model_versions']
        and manifest['code_sha256']=={p:source['code_sha256'][p] for p in reader.SOURCE_PATHS}
        and manifest['stem_artifact_sha256']==parent['numerical_root_sha256']==source['stem_artifact_sha256']
        and manifest['stem_program_sha256']==parent['program_sha256']==source['parent_stem_program_sha256']
        and all(sha256(reader._canonical(program[key])).hexdigest()==source[key+'_sha256']
                for key in ('initialization','policy','leaf_profile'))
        and manifest['time_origin_utc']==source['time_origin_utc']
        and manifest['initial_at_elapsed_seconds_exact']==program['initialization']['initial_inventory']['at_elapsed_seconds_exact']
        and type(manifest['sample_count']) is int and 1<=manifest['sample_count']<=64)


def _frame_scope(frame,binding,*,last=False):
    period=binding['input']['period'];at=farms.farms.documents._time(frame['at'])
    start,end=(farms.farms.documents._time(period[key]) for key in ('start','end'))
    _need(start<=at<=end and (not last or at==end))


class LeafAppearanceArtifactAuthority:
    @_checked
    def __init__(self,farm_binding,*,directory,access,integrity_key,issuer_id,key_id):
        _need(type(farm_binding) is farms.LeafAppearanceFarmBinding and type(access) is ContentAccess
            and type(integrity_key) is bytes and 32<=len(integrity_key)<=4096
            and farms.evidence.stem._identifier(issuer_id) and farms.evidence.stem._identifier(key_id))
        directory=Path(directory)
        resolved,parent=directory.resolve(),farm_binding.parent_authority.directory.resolve()
        _need(directory.is_absolute() and '..' not in directory.parts
            and not resolved.is_relative_to(parent) and not parent.is_relative_to(resolved)
            and access==farm_binding.parent_authority.access)
        self.farm_binding,self.directory,self.access=farm_binding,directory,access
        self.integrity_key,self.issuer_id,self.key_id=integrity_key,issuer_id,key_id
        self._fixed=self._pointers();self._binding()

    def _pointers(self):
        return (self.farm_binding,self.farm_binding._fixed,self.directory,self.access,self.integrity_key,self.issuer_id,self.key_id,
            self.directory.resolve(),self.farm_binding.parent_authority.directory.resolve())

    def _binding(self):
        self.farm_binding._binding()
        _need(self._pointers()==self._fixed and _code_pins()==_CODE_PINS
            and FLAGS==_FLAGS and PROOF_MAX==128*1024 and RETURN_MAX==2*1024**2
            and PROGRAM_MAX==reader.program.MAX==2*1024**2)

    def _signed(self,payload):
        return reader._canonical({'payload':payload,'hmac_sha256':hmac.new(self.integrity_key,DOMAIN+reader._canonical(payload),'sha256').hexdigest()})

    def _load(self,tenant,result_sha256):
        self._binding();reader._hash(result_sha256)
        with MorphologyBlobStore(self.directory,self.access) as store:
            raw=store.get(result_sha256,maximum=PROOF_MAX);doc=reader._parse(raw,PROOF_MAX)
            reader._closed(doc,{'payload','hmac_sha256'});reader._hash(doc['hmac_sha256']);payload=doc['payload'];reader._closed(payload,_FIELDS)
            _need(hmac.compare_digest(self._signed(payload),raw)
                and payload['schema_version']==VERSION and all(payload[k]==v for k,v in FLAGS.items())
                and payload['issuer_id']==self.issuer_id and payload['key_id']==self.key_id and payload['code_sha256']==_CODE_PINS)
            for key in _HASH_FIELDS:reader._hash(payload[key])
            _need(type(payload['parent_job_id']) is str and str(UUID(payload['parent_job_id']))==payload['parent_job_id'])
            calculated=parent_signed._calculated_at(payload['calculated_at'])
            _need(parent_signed._calculated_at(payload['parent_calculated_at'])<=calculated)
            if payload['tenant_id']!=tenant:raise PermissionError('signed leaf appearance tenant unavailable')
            packet={name:store.get(payload[field],maximum=maximum) for name,field,maximum in (
                ('program_raw','program_sha256',PROGRAM_MAX),('source_raw','source_sha256',farms.evidence.SOURCE_MAX),
                ('evidence_raw','input_evidence_sha256',farms.evidence.EVIDENCE_MAX))}
            binding_raw=store.get(payload['binding_sha256'],maximum=farms.MAX_BINDING_BYTES)
        binding=reader._parse(binding_raw,farms.MAX_BINDING_BYTES);request_raw=reader._canonical(binding['request'])
        _need(self.farm_binding.current(tenant,request_raw,binding_raw,**packet)==binding_raw)
        _need(binding['tenant_id']==tenant and binding['request']['study_id']==payload['study_id']
            and binding['request']['revision']==payload['revision'] and binding['parent_result_binding_verified'] is True
            and binding['input']['program_sha256']==payload['program_sha256']
            and binding['input']['source_sha256']==payload['source_sha256']
            and binding['input']['evidence_sha256']==payload['input_evidence_sha256']
            and binding['parent']['job_id']==payload['parent_job_id']
            and binding['parent']['result_sha256']==payload['parent_result_sha256']
            and binding['parent']['numerical_root_sha256']==payload['parent_numerical_root_sha256']
            and binding['parent']['calculated_at']==payload['parent_calculated_at']
            and farms.farms.documents._time(binding['registration']['decision_at'])
                <=parent_signed._calculated_at(payload['parent_calculated_at'])<=calculated)
        self._binding()
        return payload,binding_raw,binding,packet

    def _read(self,tenant,result_sha256,view,index=None):
        payload,binding_raw,binding,packet=self._load(tenant,result_sha256);root=payload['numerical_root_sha256']
        manifest=reader.read_leaf_appearance_manifest(self.directory,self.access,root);_linked(manifest,binding,packet['program_raw'])
        common={**FLAGS,'result_sha256':result_sha256,'numerical_root_sha256':root,
            **{k:payload[k] for k in ('calculated_at','parent_job_id','parent_result_sha256','parent_numerical_root_sha256','parent_calculated_at')},
            'study_id':payload['study_id'],'revision':payload['revision'],'farm':binding['request']['farm'],
            'profile_applicability':'unvalidated_for_registered_crop','normalization':'per_tracked_shoot',
            **{k:payload[k] for k in ('program_sha256','source_sha256','input_evidence_sha256','binding_sha256')}}
        if view=='frame':
            frame=reader.read_leaf_appearance_frame(self.directory,self.access,root,index=index)
            _frame_scope(frame,binding,last=index==manifest['sample_count']-1)
            result={**common,'schema_version':'leaf-appearance-signed-frame-v1','frame':frame,
                'frame_sha256':sha256(reader._canonical(frame)).hexdigest()}
        elif view=='replay':
            result={**common,'schema_version':'leaf-appearance-signed-replay-v1','manifest':manifest,'frames':[]}
            for i in range(manifest['sample_count']):
                result['frames'].append(reader.read_leaf_appearance_frame(self.directory,self.access,root,index=i))
                _frame_scope(result['frames'][-1],binding,last=i==manifest['sample_count']-1)
                _need(len(reader._canonical(result))<=RETURN_MAX)
        else:
            last=reader.read_leaf_appearance_frame(self.directory,self.access,root,index=manifest['sample_count']-1)
            _frame_scope(last,binding,last=True)
            result={**common,'schema_version':'leaf-appearance-signed-manifest-v1','manifest':manifest}
        after=self._load(tenant,result_sha256)
        _need(after[0]==payload and after[1]==binding_raw and after[3]==packet and len(reader._canonical(result))<=RETURN_MAX)
        return result

    @_checked
    def read_manifest(self,tenant,result_sha256):return self._read(tenant,result_sha256,'manifest')

    @_checked
    def read_frame(self,tenant,result_sha256,*,index):
        _need(type(index) is int and index>=0)
        return self._read(tenant,result_sha256,'frame',index)

    @_checked
    def read_replay(self,tenant,result_sha256):return self._read(tenant,result_sha256,'replay')
