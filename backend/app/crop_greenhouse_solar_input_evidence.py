"""Authenticated solar input checks; crop-greenhouse-solar-input-evidence-v1.md."""
from dataclasses import dataclass,field
from datetime import datetime,timezone
from functools import wraps
from hashlib import sha256
import hmac
import os
from pathlib import Path
import re

from . import crop_greenhouse_solar_time as clock
from . import crop_cycle_server_custody as files
from . import crop_fruit_transport as transport
from . import provenance

continuation=clock.continuation
joint=continuation.driver.stage.joint
VERSION='joint-solar-input-evidence-v1'
SOURCE_VERSION='joint-solar-input-source-v1'
SCOPE='synthetic_solar_input_math_validation_only'
NORMALIZATION_VERSION='joint-current-solar-float64-grid-provenance-v1'
QC_VERSION='joint-initial-rhs-solar-provenance-schedule-utc-v1'
DOMAIN=b'ossf-joint-solar-input-evidence-v1\0'
MAX_SOURCE_BYTES=1024**2
MAX_PROFILE_BYTES=128*1024
MAX_EVIDENCE_BYTES=2*1024**2
CODE_SHA256=sha256(Path(__file__).read_bytes()).hexdigest()
_MODULES={'time':clock,'continuation':continuation,'driver':continuation.driver,
    'stage':continuation.driver.stage,'base_integration':continuation.driver.stage.core,
    'base_driver':continuation.driver.previous,'management':continuation.driver.previous.management,'rhs':joint,
    'ventilation':continuation.driver.stage.solar_rhs.vent,
    'solar_rhs':continuation.driver.stage.solar_rhs,'PAR_joint':continuation.driver.stage.solar_rhs.par,
    'PAR':continuation.driver.stage.solar_rhs.par.radiation,'NIR':continuation.driver.stage.solar_rhs.nir,
    'ventilation_joint':continuation.driver.stage.vent_joint,'provenance':provenance,'continuation_helpers':continuation.transport,
    'calendar_helpers':clock.clock_helpers,
    'secure_files':files,'directory_helper':files.job_store,'file_metadata':files.operator_config,
    'strict_json':files.inputs}
_SOURCES={**{k:Path(m.__file__) for k,m in _MODULES.items()},
    **{k:Path(__file__).with_name(k+'.py') for k in joint.COMPONENT_CODE_SHA256},
    'notice':Path(__file__).resolve().parents[2]/'LICENSES/GreenLight-BSD-3-Clause-Clear.txt'}
DEPENDENCY_SHA256={k:sha256(p.read_bytes()).hexdigest() for k,p in _SOURCES.items()}
_CLASSES=(joint.growth.ReferenceParameters,joint.fruit.ReferenceFruitCohortParameters,
    joint.ReferenceFruitTransportParameters,joint.exchange.ReferenceParameters)
_PROFILE_HASHES=dict(zip(continuation.PROFILE_NAMES,
    (joint.growth.PROFILE_SHA256,joint.fruit.PROFILE_SHA256,
     transport.PROFILE_SHA256,joint.exchange.PROFILE_SHA256),strict=True))
PROGRAM_FIELDS=('scenario','solar','ventilation','events','output_steps','step_seconds','step_count','time_origin')
_TOKEN=object()
_canonical=continuation._canonical
_hash=continuation._hash


class SolarInputEvidenceHold(ValueError):
    """No current original input-check evidence for the requested identity."""


def _need(condition):
    if not condition:raise SolarInputEvidenceHold('solar input validation evidence unavailable')


def _identifier(v):return type(v) is str and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}',v) is not None


def _pins():
    _need(sha256(Path(__file__).read_bytes()).hexdigest()==CODE_SHA256
        and {k:sha256(p.read_bytes()).hexdigest() for k,p in _SOURCES.items()}==DEPENDENCY_SHA256
        and all(Path(m.__file__)==_SOURCES[k] for k,m in _MODULES.items()))


def _operation(fn):
    @wraps(fn)
    def run(self,*args,**kw):
        try:
            self._binding();result=fn(self,*args,**kw);self._binding();return result
        except (OSError,ValueError,TypeError,KeyError,AttributeError,OverflowError,RecursionError) as exc:
            raise SolarInputEvidenceHold('solar input validation evidence unavailable') from None
    return run


def _current(directory,expected_source_sha256):
    _need(continuation._digest(expected_source_sha256))
    fd=files.job_store._open_directory_nofollow(Path(directory))
    try:
        before=files._secure(fd,directory=True)
        names={'source.json','notice.txt',*(k+'.json' for k in continuation.PROFILE_NAMES)}
        _need(set(os.listdir(fd))==names)
        raw={name:files._read(fd,name,MAX_SOURCE_BYTES if name=='source.json' else MAX_PROFILE_BYTES)
             for name in sorted(names)}
        hashes={k:sha256(v).hexdigest() for k,v in raw.items()}
        _need(hashes['source.json']==expected_source_sha256
            and hashes['notice.txt']==DEPENDENCY_SHA256['notice']
            and all(hashes[k+'.json']==v for k,v in _PROFILE_HASHES.items()))
        after=files._secure(fd,directory=True)
        _need(files.operator_config._metadata(before)==files.operator_config._metadata(after)
            and set(os.listdir(fd))==names)
        return raw,hashes
    finally:os.close(fd)


def _source(raw):
    v=files.inputs._json(raw)
    _need(type(v) is dict and set(v)=={'version','provenance',*PROGRAM_FIELDS}
        and _canonical(v)==raw and v['version']==SOURCE_VERSION and v['scenario']['origin']=='synthetic'
        and v['solar']['origin']=='synthetic' and v['ventilation']['origin']=='synthetic' and v['time_origin']['origin']=='synthetic' and type(v['events']) is list
        and all(row['event']['origin']=='synthetic' for row in v['events']))
    return v


def _variables(source):
    units={}
    blocks={**joint.SCALAR_BLOCKS,**joint.ARRAY_BLOCKS,
        'forcing':continuation.driver.stage.solar_rhs.FORCING_UNITS}
    for block,mapping in blocks.items():
        units.update({'scenario.'+block+'.'+k:u for k,u in mapping.items()})
    units.update({'solar.values.'+k:u for k,u in continuation.driver.stage.solar_rhs.SOLAR_UNITS.items()})
    units.update({'ventilation.forcing.'+k:u for k,u in continuation.driver.stage.solar_rhs.vent.FORCING_UNITS.items()})
    for i,_ in enumerate(source['events']):
        units.update({f'events.{i}.event.values.'+k:u for k,u in
            {'leaf':'mg_CH2O/m2_floor','stem_root':'mg_CH2O/m2_floor','fruit_fraction':'1'}.items()})
    return {**units,'step_seconds':'s','step_count':'1'}


def _provenance(source,review):
    record=provenance.SourceRecord.model_validate_json(_canonical(source['provenance']))
    value=record.model_dump(mode='json')
    _need(_canonical(value)==_canonical(source['provenance']) and record.synthetic is True
        and record.scope.station_or_grid_id is None and not record.request_details
        and record.source_reviewer==review['reviewer_id'] and record.source_evidence_id==review['evidence_id']
        and record.raw_sha256==_hash({k:source[k] for k in PROGRAM_FIELDS}))
    times=(record.observed_at,record.published_at,record.available_at,record.retrieved_at)
    _need(all(v is not None for v in times) and all(v<=datetime.now(timezone.utc) for v in times))
    expected=_variables(source)
    _need({v.name:v.original_unit for v in record.variables}==expected
        and all(v.time_semantics=='instant' and v.provider_qc_status=='not_supplied'
            and v.provider_qc_value is None for v in record.variables))
    _need(len(record.project_checks)==len(expected) and {v.variable for v in record.project_checks}==set(expected)
        and all(v.name=='initial_software_contract' and v.version==QC_VERSION and v.status=='passed'
            and v.evidence_id==review['evidence_id'] and v.reviewer==review['reviewer_id'] for v in record.project_checks))
    _need({v.action for v in record.rights}=={'access','store','transform','display','redistribute'}
        and all(v.status=='allowed' and v.evidence_id==review['evidence_id']
            and v.reviewer==review['reviewer_id'] for v in record.rights))
    return value


def _record(binding,source_provenance):
    clock._binding(binding);ctx=binding._context
    return {'provenance':source_provenance,'context_sha256':ctx.root_sha256,'program':ctx.program,'manifest':ctx.manifest,
        'initial_calculation':files.inputs._json(ctx._first),'binding_sha256':binding.sha256,'binding':binding.manifest,
        'initial_state_sha256':_hash({k:ctx.program['scenario'][k] for k in ('plant_state','cohort_state','climate_state')})}


def _record_hashes(record,expected_context,expected_binding,identity,source_provenance):
    _need(type(record) is dict and set(record)=={'context_sha256','program','manifest','initial_calculation',
        'binding_sha256','binding','initial_state_sha256','provenance'} and continuation._digest(expected_context)
        and continuation._digest(expected_binding))
    manifest=record['manifest'];binding=record['binding'];program=record['program']
    _need(_hash(manifest)==record['context_sha256']==expected_context
        and _hash(binding)==record['binding_sha256']==expected_binding
        and binding['context_sha256']==expected_context and binding['time_code_sha256']==clock.CODE_SHA256
        and manifest['program_sha256']==_hash(program) and manifest['initial_rhs_sha256']==_hash(record['initial_calculation'])
        and record['initial_state_sha256']==_hash({k:program['scenario'][k] for k in ('plant_state','cohort_state','climate_state')})
        and manifest['identity']==identity and identity['profile_sha256']==_PROFILE_HASHES
        and manifest['scope']=='software_research_only' and binding['scope']=='software_research_only'
        and binding['G0_G4']=='not_assessed' and program['scenario']['origin']=='synthetic'
        and program['ventilation']['origin']=='synthetic'
        and program['solar']['origin']=='synthetic'
        and _canonical(record['provenance'])==_canonical(source_provenance)
        and identity['ledger_schema']=='joint-solar-ventilation-ledgers-v1'
        and binding['calendar_helpers_code_sha256']==clock.clock_helpers.CODE_SHA256
        and type(record['initial_calculation']) is dict and set(record['initial_calculation'])=={
            'model_version','code_sha256','source_sha256','notice_sha256','component_code_sha256','policy_sha256',
            'input_sha256','PAR_joint_calculation_sha256','NIR_calculation_sha256','ventilation_input_sha256',
            'calculation_sha256','scenario','solar','ventilation','PAR_joint','NIR','outdoor','joint_rhs',
            'heat_composition','scope','claim_scope','G0_G4','time_coordinate'}
        and record['initial_calculation']['model_version']==continuation.driver.stage.solar_rhs.VERSION)


@dataclass(frozen=True)
class VerifiedSolarInputEvidence:
    _raw_record:bytes=field(repr=False)
    evidence_sha256:str
    source_sha256:str
    review_id:str
    referenced_bytes:int
    _token:object=field(repr=False)

    @property
    def record(self):
        _need(self._token is _TOKEN);return files.inputs._json(self._raw_record)

    @property
    def rights_or_gate_approval(self):return False


class SolarInputEvidenceAuthority:
    def __init__(self,*,integrity_key,issuer_id,key_id,review_resolver):
        _need(type(integrity_key) is bytes and 32<=len(integrity_key)<=4096
            and _identifier(issuer_id) and _identifier(key_id) and callable(review_resolver))
        self.integrity_key=integrity_key;self.issuer_id=issuer_id;self.key_id=key_id;self.review_resolver=review_resolver
        self._fixed=(integrity_key,issuer_id,key_id,review_resolver)

    def _binding(self):
        _pins();_need((self.integrity_key,self.issuer_id,self.key_id,self.review_resolver)==self._fixed)

    def _review(self,review_id,source_sha256):
        _need(_identifier(review_id))
        try:value=self.review_resolver(review_id)
        except Exception:raise SolarInputEvidenceHold('solar input validation evidence unavailable') from None
        _need(type(value) is dict and set(value)=={'evidence_id','reviewer_id','decision_id','source_sha256','status','scope'}
            and value['evidence_id']==review_id and all(_identifier(value[k]) for k in ('evidence_id','reviewer_id','decision_id'))
            and value['source_sha256']==source_sha256 and value['status']=='accepted_for_software_validation'
            and value['scope']==SCOPE)
        return files.inputs._json(_canonical(value))

    def _signature(self,payload):return hmac.new(self.integrity_key,DOMAIN+_canonical(payload),'sha256').hexdigest()

    @_operation
    def issue(self,directory,expected_source_sha256,*,binding,review_id):
        raw,hashes=_current(directory,expected_source_sha256);review=self._review(review_id,expected_source_sha256)
        source=_source(raw['source.json']);source_provenance=_provenance(source,review);record=_record(binding,source_provenance)
        profiles={name+'_profile':cls(raw[name+'.json'])
            for name,cls in zip(continuation.PROFILE_NAMES,_CLASSES,strict=True)}
        checked=continuation.prepare_context(**{k:source[k] for k in ('scenario','solar','ventilation','events','output_steps','step_seconds','step_count')},**profiles)
        checked_binding=clock.prepare_binding(checked,origin=source['time_origin'])
        _need(_canonical(record)==_canonical(_record(checked_binding,source_provenance)))
        _record_hashes(record,binding._context.root_sha256,binding.sha256,continuation._identity(checked._profiles),source_provenance)
        payload={'version':VERSION,'scope':SCOPE,'G0_G4':'not_assessed','issuer_id':self.issuer_id,'key_id':self.key_id,
            'validated_at':datetime.now(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z'),
            'code_sha256':CODE_SHA256,'dependencies':DEPENDENCY_SHA256,'source_schema':SOURCE_VERSION,
            'normalization_version':NORMALIZATION_VERSION,'qc_version':QC_VERSION,
            'source_sha256':expected_source_sha256,'source_files':hashes,'review':review,'record':record}
        _need(self._review(review_id,expected_source_sha256)==review
            and _current(directory,expected_source_sha256)==(raw,hashes))
        result=_canonical({'payload':payload,'hmac_sha256':self._signature(payload)})
        _need(len(result)<=MAX_EVIDENCE_BYTES);return result

    @_operation
    def verify(self,directory,expected_source_sha256,evidence_raw,*,expected_context_sha256,expected_binding_sha256):
        _need(type(evidence_raw) is bytes and 0<len(evidence_raw)<=MAX_EVIDENCE_BYTES)
        value=files.inputs._json(evidence_raw)
        _need(type(value) is dict and set(value)=={'payload','hmac_sha256'} and _canonical(value)==evidence_raw
            and continuation._digest(value['hmac_sha256']))
        p=value['payload'];_need(type(p) is dict and set(p)=={'version','scope','G0_G4','issuer_id','key_id',
            'validated_at','code_sha256','dependencies','source_schema','normalization_version','qc_version',
            'source_sha256','source_files','review','record'} and hmac.compare_digest(self._signature(p),value['hmac_sha256']))
        stamp=p['validated_at'];_need(type(stamp) is str and re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{6}Z',stamp) is not None)
        datetime.fromisoformat(stamp.replace('Z','+00:00'))
        _need(p['version']==VERSION and p['scope']==SCOPE and p['G0_G4']=='not_assessed'
            and p['issuer_id']==self.issuer_id and p['key_id']==self.key_id and p['code_sha256']==CODE_SHA256
            and p['dependencies']==DEPENDENCY_SHA256 and p['source_schema']==SOURCE_VERSION
            and p['normalization_version']==NORMALIZATION_VERSION and p['qc_version']==QC_VERSION
            and p['source_sha256']==expected_source_sha256)
        review=self._review(p['review']['evidence_id'],expected_source_sha256);_need(review==p['review'])
        raw,hashes=_current(directory,expected_source_sha256);_need(hashes==p['source_files'])
        source=_source(raw['source.json']);source_provenance=_provenance(source,review)
        profiles=tuple(cls(raw[name+'.json']) for name,cls in zip(continuation.PROFILE_NAMES,_CLASSES,strict=True))
        _record_hashes(p['record'],expected_context_sha256,expected_binding_sha256,continuation._identity(profiles),source_provenance)
        _need(self._review(review['evidence_id'],expected_source_sha256)==review
            and _current(directory,expected_source_sha256)==(raw,hashes))
        return VerifiedSolarInputEvidence(_canonical(p['record']),sha256(evidence_raw).hexdigest(),
            expected_source_sha256,review['evidence_id'],sum(map(len,raw.values())),_TOKEN)
