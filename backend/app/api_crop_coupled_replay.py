"""Bounded authenticated pages of immutable coupled research quantities."""
from datetime import datetime, timezone
from hashlib import sha256
from typing import Annotated, Literal
import re

from fastapi import Path, Query, Request, Response
from pydantic import Field, model_validator
from starlette.concurrency import run_in_threadpool

from .api_contracts import ErrorEnvelope
from .api_crop_replay import (_Public, Digest, Name, UtcStamp, NAME_PATTERN,
    CropMass, CropCarbonResidual, CropTemperature, CropTemperatureSum,
    CropLeafAreaIndex, CropResearchFarm)
from . import crop_coupled_artifact as artifact
from . import crop_coupled_result_store as storage
from . import crop_result_store as previous
from .crop_result_store import CropResultHold, READ_SCOPES
from .farm_authoring_storage import FarmAuthoringHold
from .thermal_run_store import _canonical, _document


RESULT_ID_PATTERN=r'^crop-result-v2:[0-9a-f]{64}$'
MAX_RESPONSE_BYTES=2*1024*1024


def _need(condition):
    if not condition:raise CropResultHold('coupled crop display unavailable')


def _at(stamp):
    return datetime.fromisoformat(stamp.replace('Z','+00:00'))


class CoupledFruitNumber(_Public):
    value: float = Field(strict=True,ge=0)
    unit: Literal['fruits_equivalent/m2_floor']


class CoupledNumberResidual(_Public):
    value: float = Field(strict=True)
    unit: Literal['fruits_equivalent/m2_floor']


class CoupledCropState(_Public):
    buffer: CropMass
    leaf: CropMass
    stem_root: CropMass
    temperature_filtered_24h: CropTemperature
    temperature_sum: CropTemperatureSum
    fruit_number: list[CoupledFruitNumber] = Field(min_length=50,max_length=50)
    fruit_carbohydrate: list[CropMass] = Field(min_length=50,max_length=50)


class CoupledCropCumulative(_Public):
    photosynthesis: CropMass
    growth_respiration: CropMass
    maintenance_leaf: CropMass
    maintenance_stem_root: CropMass
    maintenance_fruit: CropMass
    removal_leaf: CropMass
    removal_stem_root: CropMass
    terminal_carbohydrate: CropMass
    terminal_number: CoupledFruitNumber
    entry_number: CoupledFruitNumber
    event_carbohydrate: CropMass
    event_number: CoupledFruitNumber


class CoupledCropSample(_Public):
    at: UtcStamp
    state: CoupledCropState
    cumulative: CoupledCropCumulative
    lai: CropLeafAreaIndex
    fruit_carbohydrate_total: CropMass
    carbon_residual: CropCarbonResidual
    carbon_residual_budget: CropMass
    number_residual: CoupledNumberResidual
    number_residual_budget: CoupledFruitNumber


class CoupledConfirmedSample(CoupledCropSample):
    phase: Literal['step-end','boundary','boundary-after-event']


class CoupledCropRemoved(_Public):
    leaf: CropMass
    stem_root: CropMass
    fruit_number: list[CoupledFruitNumber] = Field(min_length=50,max_length=50)
    fruit_carbohydrate: list[CropMass] = Field(min_length=50,max_length=50)


class CoupledCropEvent(_Public):
    at: UtcStamp
    before: CoupledCropState
    after: CoupledCropState
    removed: CoupledCropRemoved


class CoupledCropHold(_Public):
    reason_code: Literal['NUMERIC_HOLD','DEPLETED_STATE_HOLD','BALANCE_HOLD',
        'REMOVAL_EXCEEDS_STORAGE_HOLD','COMPENSATION_POINT_HOLD','INPUT_HOLD',
        'UNIT_HOLD','PROFILE_HOLD','FRUIT_COHORT_STATE_HOLD','FRUIT_COHORT_DOMAIN_HOLD',
        'FRUIT_TRANSPORT_DOMAIN_HOLD','EMPTY_FRUIT_SINK_HOLD','FRUIT_ENTRY_BUDGET_HOLD',
        'FRUIT_ENTRY_STATE_HOLD','STATE_MISMATCH_HOLD']
    at: UtcStamp
    phase: Literal['rk4-k1','rk4-k2','rk4-k3','rk4-k4','step-end',
        'step-end-arithmetic','balance','boundary','boundary-after-event','event']
    time_meaning: Literal['solver_evaluation_time']
    last_confirmed: CoupledConfirmedSample | None


class CoupledProfile(_Public):
    profile_id: Name
    sha256: Digest


class CoupledProfiles(_Public):
    growth_profile: CoupledProfile
    cohort_profile: CoupledProfile
    transport_profile: CoupledProfile


class CoupledCodeHashes(_Public):
    integrator: Digest
    coupled: Digest
    plant: Digest
    cohorts: Digest
    allocation: Digest
    transport: Digest


class CoupledSolver(_Public):
    method: Literal['rk4-fixed-v1']
    max_step_seconds: int = Field(strict=True,ge=1,le=3600)
    max_steps: int = Field(strict=True,ge=1,le=10000)
    roundoff_rule: Literal['64-ulp-per-operation-v1']


class CoupledCropManifest(_Public):
    integrator_version: Literal['crop-plant-cohort-rk4-research-v1']
    rate_model_version: Literal['vanthoor-greenlight-explicit-entry-plant-rates-research-v1']
    profiles: CoupledProfiles
    policy_sha256: Digest
    code_sha256: CoupledCodeHashes
    artifact_code_sha256: Digest
    storage_code_sha256: Digest
    binding_code_sha256: Digest
    input_sha256: Digest
    raw_program_sha256: Digest
    result_sha256: Digest
    artifact_sha256: Digest
    payload_sha256: Digest
    notice_sha256: Digest
    solver: CoupledSolver
    time_rule: Literal['UTC_POSIX_whole_seconds_v1']
    python_version: Annotated[str,Field(pattern=r'^3\.\d+\.\d+$',max_length=32,strict=True)]
    convergence: Literal['not_evaluated_for_this_program']
    temperature_sum_method: Literal['analytic_piecewise_constant_fraction_v1']
    research_assumptions: list[Literal['leaf_stem_fixed_RGR_from_reference_profile_not_measured']] = Field(min_length=1,max_length=1)


class CoupledSamplePage(_Public):
    offset: int = Field(strict=True,ge=0,le=512)
    limit: int = Field(strict=True,ge=1,le=64)
    total: int = Field(strict=True,ge=0,le=512)
    next_offset: Annotated[int,Field(strict=True,ge=0,le=512)] | None


class CoupledEventPage(_Public):
    offset: int = Field(strict=True,ge=0,le=128)
    limit: int = Field(strict=True,ge=1,le=8)
    total: int = Field(strict=True,ge=0,le=128)
    next_offset: Annotated[int,Field(strict=True,ge=0,le=128)] | None


class CoupledCropReplay(_Public):
    result_id: Annotated[str,Field(pattern=RESULT_ID_PATTERN,strict=True)]
    recorded_at: UtcStamp
    study_id: Name
    revision: Name
    farm: CropResearchFarm
    batch_id: Name
    zone_id: Name
    farm_sha256: Digest
    source_binding_sha256: Digest
    storage_status: Literal['stored_unpublished_research']
    claim_scope: Literal['synthetic_crop_math_only']
    scope: Literal['software_research_only']
    gates: Literal['not_assessed']
    normalization: Literal['per_m2_floor']
    profile_applicability: Literal['unvalidated_for_registered_crop']
    temporal_provenance: Literal['synthetic_research_program']
    start_utc: UtcStamp
    end_utc: UtcStamp
    status: Literal['completed','hold']
    steps: int = Field(strict=True,ge=0,le=10000)
    planned_steps: int = Field(strict=True,ge=1,le=10000)
    manifest: CoupledCropManifest
    samples: list[CoupledCropSample] = Field(max_length=64)
    events: list[CoupledCropEvent] = Field(max_length=8)
    sample_page: CoupledSamplePage
    event_page: CoupledEventPage
    hold: CoupledCropHold | None

    @model_validator(mode='after')
    def consistent(self):
        start,end=_at(self.start_utc),_at(self.end_utc)
        _need(start<end and self.steps<=self.planned_steps)
        for page,items in ((self.sample_page,self.samples),(self.event_page,self.events)):
            _need(page.offset<=page.total and len(items)==min(page.limit,page.total-page.offset))
            next_at=page.offset+len(items)
            _need(page.next_offset==(next_at if next_at<page.total else None)
                  and all(start<=_at(s.at)<=end for s in items)
                  and all(_at(a.at)<_at(b.at) for a,b in zip(items,items[1:])))
        if self.status=='completed':
            _need(self.hold is None and self.steps==self.planned_steps and self.sample_page.total>=2)
        else:
            _need(self.hold is not None and start<=_at(self.hold.at)<=end)
            _need(all(_at(s.at)<_at(self.hold.at) for s in self.samples)
                  and all(_at(e.at)<=_at(self.hold.at) for e in self.events)
                  and (self.hold.last_confirmed is None or
                       start<=_at(self.hold.last_confirmed.at)<=_at(self.hold.at)))
        return self


def _page(items,offset,limit,maximum):
    _need(type(offset) is int and 0<=offset<=len(items)
          and type(limit) is int and 1<=limit<=maximum)
    selected=items[offset:offset+limit];following=offset+len(selected)
    return selected,{'offset':offset,'limit':limit,'total':len(items),
        'next_offset':following if following<len(items) else None}


def _public_bytes(projected):
    _need(type(projected) is CoupledCropReplay)
    raw=projected.model_dump_json().encode()
    _need(len(raw)<=MAX_RESPONSE_BYTES)
    return raw


def project_coupled_result(record,*,growth_profile,cohort_profile,transport_profile,notice_raw,
        sample_offset=0,sample_limit=64,event_offset=0,event_limit=8):
    """Whitelist display fields after the store checked HMAC/current farm rights."""
    try:
        _need(type(record) is dict and set(record)=={'result_id','payload_raw','payload_sha256','recorded_at'}
              and type(record['payload_raw']) is bytes
              and sha256(record['payload_raw']).hexdigest()==record['payload_sha256']
              and type(record['recorded_at']) is datetime and record['recorded_at'].utcoffset() is not None)
        packet=_document(record['payload_raw'],max_size=storage.MAX_PACKET_BYTES)
        _need(set(packet)=={'schema_version','status','claim_scope','tenant_id','request','binding',
              'rights_policy_version','storage_code_sha256','binding_code_sha256','artifact','artifact_sha256','result_id'}
              and packet['schema_version']=='crop-result-v2'
              and packet['result_id']==record['result_id']=='crop-result-v2:'+sha256(
                  _canonical({k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
              and packet['storage_code_sha256']==storage.STORAGE_CODE_SHA256
              and packet['binding_code_sha256']==previous.STORAGE_CODE_SHA256)
        profiles={'growth_profile':growth_profile,'cohort_profile':cohort_profile,'transport_profile':transport_profile}
        doc=artifact.read_coupled_artifact(_canonical(packet['artifact']),expected_sha256=packet['artifact_sha256'],
            **profiles,notice_raw=notice_raw)
        request=packet['request'];binding=packet['binding'];result=doc['result'];manifest=result['manifest']
        program=request['program']
        _need(doc['program_raw_utf8'].encode()==_canonical(program)
              and doc['program_sha256']==request['rights']['program_sha256']
              and request['farm']['crop_id']==binding['crop']['crop_id'])
        public_manifest={k:manifest[k] for k in ('integrator_version','rate_model_version','policy_sha256',
            'code_sha256','input_sha256','solver','time_rule','python_version','convergence',
            'temperature_sum_method','research_assumptions')}
        public_manifest.update(profiles={k:{'profile_id':p.profile_id,'sha256':p.sha256} for k,p in profiles.items()},
            artifact_code_sha256=doc['artifact_code_sha256'],storage_code_sha256=packet['storage_code_sha256'],
            binding_code_sha256=packet['binding_code_sha256'],raw_program_sha256=doc['program_sha256'],
            result_sha256=result['result_sha256'],artifact_sha256=packet['artifact_sha256'],
            payload_sha256=record['payload_sha256'],notice_sha256=artifact.NOTICE_SHA256)
        samples,sample_page=_page(result['samples'],sample_offset,sample_limit,64)
        journal,event_page=_page(result['events'],event_offset,event_limit,8)
        hold=None
        if result['status']=='hold':
            diagnostic=result['hold']
            hold={'reason_code':diagnostic['reason'].partition(':')[0],'at':diagnostic['at'],
                'phase':diagnostic['phase'],'time_meaning':'solver_evaluation_time',
                'last_confirmed':result['last_confirmed']}
        projected=CoupledCropReplay(result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
            study_id=request['study_id'],revision=request['revision'],farm=request['farm'],
            batch_id=binding['crop']['batch_id'],zone_id=binding['zone_id'],
            farm_sha256=binding['farm_sha256'],source_binding_sha256=binding['source_binding_sha256'],
            storage_status=packet['status'],claim_scope=packet['claim_scope'],scope=result['scope'],
            gates='not_assessed',normalization=binding['normalization'],
            profile_applicability=binding['profile_applicability'],temporal_provenance='synthetic_research_program',
            start_utc=program['segments'][0]['start'],end_utc=program['segments'][-1]['end'],
            status=result['status'],steps=result['steps'],planned_steps=result['planned_steps'],
            manifest=public_manifest,samples=samples,
            events=[{k:e[k] for k in ('at','before','after','removed')} for e in journal],
            sample_page=sample_page,event_page=event_page,hold=hold)
        _public_bytes(projected)
        return projected
    except Exception:raise CropResultHold('coupled crop display unavailable') from None


def install_coupled_crop_routes(app,*,jobs,farms,store,principal_provider,authorized_tenant,error,access):
    if store is not None:
        if (type(store) is not storage.CoupledCropResultStore or store.jobs is not jobs
                or store.farms is not farms or farms is None or jobs.principal_provider is not principal_provider):
            raise ValueError('trusted coupled crop reader required')
        store._guard_binding()

    @app.get('/v1/crop-coupled-research-results/{result_id}',response_model=CoupledCropReplay,
        operation_id='getCoupledCropResearchResult',openapi_extra=access(READ_SCOPES),
        responses={s:{'model':ErrorEnvelope} for s in (401,403,404,422,503)})
    async def get_coupled_crop(request:Request,result_id:Annotated[str,Path(pattern=RESULT_ID_PATTERN)],
            scenario_id:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            scenario_revision:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            registration_sha256:Annotated[str,Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            sample_offset:Annotated[int,Query(ge=0,le=512)]=0,
            sample_limit:Annotated[int,Query(ge=1,le=64)]=64,
            event_offset:Annotated[int,Query(ge=0,le=128)]=0,
            event_limit:Annotated[int,Query(ge=1,le=8)]=8):
        tenant,denied=authorized_tenant(*READ_SCOPES)
        if denied is not None:return denied
        pairs=list(request.query_params.multi_items());keys=[k for k,_ in pairs]
        required={'scenario_id','scenario_revision','registration_sha256','crop_id'}
        pages={'sample_offset','sample_limit','event_offset','event_limit'}
        if (len(keys)!=len(set(keys)) or not required<=set(keys)<=required|pages
                or any(not re.fullmatch(r'0|[1-9][0-9]*',v) for k,v in pairs if k in pages)):
            return error(422,'invalid_request','Invalid request')
        async for chunk in request.stream():
            if chunk:return error(422,'invalid_request','Invalid request')
        if store is None:return error(503,'crop_research_unavailable','Crop research result unavailable')
        try:
            def read_page():
                record=store.get(tenant,result_id,{'scenario_id':scenario_id,'scenario_revision':scenario_revision,
                    'registration_sha256':registration_sha256,'crop_id':crop_id})
                if record is None:return None
                projected=project_coupled_result(record,**store._profiles(),notice_raw=store.notice_raw,
                    sample_offset=sample_offset,sample_limit=sample_limit,event_offset=event_offset,event_limit=event_limit)
                raw=_public_bytes(projected)
                packet=_document(record['payload_raw'],max_size=storage.MAX_PACKET_BYTES)
                store._current(tenant,packet['request'],packet['binding'])
                return raw
            raw=await run_in_threadpool(read_page)
            current,denied=authorized_tenant(*READ_SCOPES)
            if denied is not None:return denied
            if current!=tenant:return error(403,'forbidden','Resource access denied')
            if raw is None:return error(404,'not_found','Crop research result not found')
            return Response(raw,media_type='application/json')
        except PermissionError:return error(403,'forbidden','Resource access denied')
        except (CropResultHold,FarmAuthoringHold):return error(422,'crop_research_hold','Crop research evidence unavailable')
        except Exception:return error(503,'crop_research_unavailable','Crop research result unavailable')
