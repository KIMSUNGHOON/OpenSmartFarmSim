"""Authenticated bounded pages of saved startup research quantities."""
from datetime import datetime, timezone
from hashlib import sha256
from typing import Annotated, Literal
import re

from fastapi import Path, Query, Request, Response
from pydantic import Field
from starlette.concurrency import run_in_threadpool

from .api_contracts import ErrorEnvelope
from .api_crop_replay import _Public, Digest, CropMass, CropCarbonResidual
from .api_crop_coupled_replay import (CoupledCropCumulative, CoupledCropSample,
    CoupledCropHold, CoupledCodeHashes, CoupledCropManifest, CoupledCropReplay, _page)
from .api_crop_replay import NAME_PATTERN
from . import crop_startup_artifact as artifact
from . import crop_startup_result_store as storage
from . import crop_result_store as previous
from .crop_result_store import CropResultHold, READ_SCOPES
from .farm_authoring_storage import FarmAuthoringHold
from .thermal_run_store import _canonical, _document

RESULT_ID_PATTERN=r'^crop-result-v3:[0-9a-f]{64}$'
MAX_RESPONSE_BYTES=2*1024*1024
STARTUP_ASSUMPTIONS=[
    'entry_number_and_mass_are_explicit_not_automatic_fruit_set',
    'empty_tail_deferral_not_a_validated_sink_capacity_model',
    'discontinuous_startup_has_no_fourth_order_claim',
    'approximately_8_52_percent_small_cohort_error_observed_in_synthetic_test',
]


def _need(condition):
    if not condition:raise CropResultHold('startup crop display unavailable')


class StartupFloorArea(_Public):
    value: Annotated[str,Field(strict=True,pattern=r'^(?:[1-9][0-9]*(?:\.[0-9]+)?|0\.[0-9]*[1-9][0-9]*)$',max_length=64)]
    unit: Literal['m²']


class StartupCropCumulative(CoupledCropCumulative):
    requested_fruit_carbohydrate: CropMass
    realized_fruit_carbohydrate: CropMass
    deferred_fruit_carbohydrate: CropMass
    fruit_growth_respiration: CropMass


class StartupDiagnostics(_Public):
    requested_residual: CropCarbonResidual
    requested_budget: CropMass
    growth_respiration_residual: CropCarbonResidual
    growth_respiration_budget: CropMass


class StartupCropSample(CoupledCropSample):
    cumulative: StartupCropCumulative
    startup_diagnostics: StartupDiagnostics


class StartupConfirmedSample(StartupCropSample):
    phase: Literal['step-end','boundary','boundary-after-event']


class StartupCropHold(CoupledCropHold):
    last_confirmed: StartupConfirmedSample | None


class StartupCodeHashes(CoupledCodeHashes):
    startup: Digest
    legacy_helpers: Digest
    original_rates: Digest


class StartupArtifactDependencies(_Public):
    legacy_artifact: Digest
    canonical_json: Digest


class StartupCropManifest(CoupledCropManifest):
    program_version: Literal['crop-plant-startup-program-v1']
    integrator_version: Literal['crop-plant-startup-rk4-research-v1']
    rate_model_version: Literal['explicit-entry-empty-sink-plant-rates-research-v1']
    code_sha256: StartupCodeHashes
    artifact_dependency_sha256: StartupArtifactDependencies
    allocation_policy_sha256: Digest
    startup_transition: Literal['zero_or_positive_tail_research_only_not_validated_sink_capacity']
    startup_balance_rule: Literal['64-ulp-per-operation-without-absolute-floor-v1']
    startup_assumptions: list[Literal[
        'entry_number_and_mass_are_explicit_not_automatic_fruit_set',
        'empty_tail_deferral_not_a_validated_sink_capacity_model',
        'discontinuous_startup_has_no_fourth_order_claim',
        'approximately_8_52_percent_small_cohort_error_observed_in_synthetic_test',
    ]] = Field(min_length=4,max_length=4)


class StartupCropReplay(CoupledCropReplay):
    schema_version: Literal['crop-startup-replay-v1']
    result_id: Annotated[str,Field(pattern=RESULT_ID_PATTERN,strict=True)]
    floor_area: StartupFloorArea
    manifest: StartupCropManifest
    samples: list[StartupCropSample] = Field(max_length=64)
    hold: StartupCropHold | None


def _public_bytes(projected):
    _need(type(projected) is StartupCropReplay)
    raw=projected.model_dump_json().encode()
    _need(len(raw)<=MAX_RESPONSE_BYTES)
    return raw

def project_startup_result(record,*,growth_profile,cohort_profile,transport_profile,notice_raw,
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
              and packet['schema_version']=='crop-result-v3'
              and packet['result_id']==record['result_id']=='crop-result-v3:'+sha256(
                  _canonical({k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
              and packet['storage_code_sha256']==storage.STORAGE_CODE_SHA256
              and packet['binding_code_sha256']==previous.STORAGE_CODE_SHA256)
        profiles={'growth_profile':growth_profile,'cohort_profile':cohort_profile,'transport_profile':transport_profile}
        doc=artifact.read_startup_artifact(_canonical(packet['artifact']),expected_sha256=packet['artifact_sha256'],
            **profiles,notice_raw=notice_raw)
        request=packet['request'];binding=packet['binding'];result=doc['result'];manifest=result['manifest']
        program=request['program']
        _need(doc['program_raw_utf8'].encode()==_canonical(program)
              and doc['program_sha256']==request['rights']['program_sha256']
              and request['farm']['crop_id']==binding['crop']['crop_id'])
        public_manifest={k:manifest[k] for k in ('program_version','integrator_version','rate_model_version','policy_sha256',
            'allocation_policy_sha256','startup_transition','startup_balance_rule',
            'code_sha256','input_sha256','solver','time_rule','python_version','convergence',
            'temperature_sum_method','research_assumptions')}
        public_manifest.update(profiles={k:{'profile_id':p.profile_id,'sha256':p.sha256} for k,p in profiles.items()},
            artifact_code_sha256=doc['artifact_code_sha256'],artifact_dependency_sha256=doc['artifact_dependency_sha256'],
            startup_assumptions=list(STARTUP_ASSUMPTIONS),storage_code_sha256=packet['storage_code_sha256'],
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
        projected=StartupCropReplay(schema_version='crop-startup-replay-v1',result_id=record['result_id'],
            floor_area={k:binding['floor_area'][k] for k in ('value','unit')},
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
    except Exception:raise CropResultHold('startup crop display unavailable') from None


def install_startup_crop_routes(app,*,jobs,farms,store,principal_provider,authorized_tenant,error,access):
    if store is not None:
        if (type(store) is not storage.StartupCropResultStore or store.jobs is not jobs
                or store.farms is not farms or farms is None or jobs.principal_provider is not principal_provider):
            raise ValueError('trusted startup crop reader required')
        store._guard_binding()

    @app.get('/v1/crop-startup-research-results/{result_id}',response_model=StartupCropReplay,
        operation_id='getStartupCropResearchResult',openapi_extra=access(READ_SCOPES),
        responses={s:{'model':ErrorEnvelope} for s in (401,403,404,422,503)})
    async def get_startup_crop(request:Request,result_id:Annotated[str,Path(pattern=RESULT_ID_PATTERN)],
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
                projected=project_startup_result(record,**store._profiles(),notice_raw=store.notice_raw,
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
