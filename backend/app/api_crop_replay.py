"""Typed, authenticated projection of immutable synthetic crop research math."""
from datetime import datetime, timezone
from hashlib import sha256
from typing import Annotated, Literal

from fastapi import Path, Query, Request
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from . import crop_growth_integration as integration
from .api_contracts import ErrorEnvelope
from .crop_result_store import (CropResultStore, CropResultHold, READ_SCOPES,
    MAX_PACKET_BYTES, NOTICE_SHA256, STORAGE_CODE_SHA256)
from .thermal_run_store import _canonical, _document

RESULT_ID_PATTERN = r'^crop-result-v1:[0-9a-f]{64}$'
NAME_PATTERN = r'^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$'
Digest = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$', strict=True)]
Name = Annotated[str, Field(pattern=NAME_PATTERN, max_length=200, strict=True)]


def _valid_utc(value):
    datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value


UtcStamp = Annotated[str, Field(strict=True,
    pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$',
    json_schema_extra={'format':'date-time'}), AfterValidator(_valid_utc)]


class _Public(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True, allow_inf_nan=False)


class CropMass(_Public):
    value: float = Field(strict=True, ge=0)
    unit: Literal['mg_CH2O/m2_floor']


class CropCarbonResidual(_Public):
    value: float = Field(strict=True)
    unit: Literal['mg_CH2O/m2_floor']


class CropTemperature(_Public):
    value: float = Field(strict=True, ge=0)
    unit: Literal['degC']


class CropTemperatureSum(_Public):
    value: float = Field(strict=True, ge=0)
    unit: Literal['degC_day']


class CropLeafAreaIndex(_Public):
    value: float = Field(strict=True, ge=0)
    unit: Literal['m2_leaf/m2_floor']


class CropResearchState(_Public):
    buffer: CropMass
    leaf: CropMass
    stem_root: CropMass
    fruit: CropMass
    temperature_filtered_24h: CropTemperature
    temperature_sum: CropTemperatureSum


class CropResearchCumulative(_Public):
    photosynthesis: CropMass
    growth_respiration: CropMass
    maintenance_leaf: CropMass
    maintenance_stem_root: CropMass
    maintenance_fruit: CropMass
    removal_leaf: CropMass
    removal_stem_root: CropMass
    removal_fruit: CropMass


class CropResearchSample(_Public):
    at: UtcStamp
    state: CropResearchState
    lai: CropLeafAreaIndex
    cumulative: CropResearchCumulative
    carbon_residual: CropCarbonResidual
    carbon_residual_budget: CropMass


class CropResearchRemovals(_Public):
    leaf: CropMass
    stem_root: CropMass
    fruit: CropMass


class CropResearchEvent(_Public):
    at: UtcStamp
    removals: CropResearchRemovals
    before: CropResearchState
    after: CropResearchState


class CropFailedMass(_Public):
    value: float | None = Field(strict=True)
    unit: Literal['mg_CH2O/m2_floor']


class CropFailedTemperature(_Public):
    value: float | None = Field(strict=True)
    unit: Literal['degC']


class CropFailedTemperatureSum(_Public):
    value: float | None = Field(strict=True)
    unit: Literal['degC_day']


class CropFailedState(_Public):
    buffer: CropFailedMass
    leaf: CropFailedMass
    stem_root: CropFailedMass
    fruit: CropFailedMass
    temperature_filtered_24h: CropFailedTemperature
    temperature_sum: CropFailedTemperatureSum


class CropResearchHold(_Public):
    reason_code: Literal['NUMERIC_HOLD','DEPLETED_STATE_HOLD','BALANCE_HOLD',
        'REMOVAL_EXCEEDS_STORAGE_HOLD','COMPENSATION_POINT_HOLD',
        'INPUT_HOLD','UNIT_HOLD','PROFILE_HOLD']
    attempted_at: UtcStamp
    phase: Literal['rk4-k1','rk4-k2','rk4-k3','rk4-k4','step-end',
        'step-end-arithmetic','balance','boundary','boundary-after-event','event','arithmetic']
    time_meaning: Literal['solver_evaluation_time']
    last_confirmed: CropResearchSample | None
    failed_state: CropFailedState


class CropResearchFarm(_Public):
    scenario_id: Name
    scenario_revision: Name
    registration_sha256: Digest
    crop_id: Name


class CropResearchCodeHashes(_Public):
    integrator: Digest
    rates: Digest


class CropResearchSolver(_Public):
    method: Literal['rk4-fixed-v1']
    max_step_seconds: int = Field(strict=True, ge=1, le=86400)
    max_steps: int = Field(strict=True, ge=1, le=1000000)
    roundoff_rule: Literal['64-ulp-per-operation-v1']


class CropResearchManifest(_Public):
    integrator_version: Literal['crop-rk4-research-v1']
    rate_model_version: Literal['vanthoor-greenlight-carbon-rates-v1']
    domain_policy: Literal['vanthoor-bounded-photosynthesis-v1']
    profile_id: Name
    profile_sha256: Digest
    code_sha256: CropResearchCodeHashes
    storage_code_sha256: Digest
    input_sha256: Digest
    raw_program_sha256: Digest
    result_sha256: Digest
    payload_sha256: Digest
    notice_sha256: Digest
    solver: CropResearchSolver
    time_rule: Literal['UTC_POSIX_whole_seconds_v1']
    python_version: Annotated[str, Field(pattern=r'^3\.\d+\.\d+$',max_length=32)]
    convergence: Literal['not_evaluated_for_this_program']
    temperature_sum_method: Literal['analytic_piecewise_constant_fraction_v1']


class CropResearchReplay(_Public):
    result_id: Annotated[str, Field(pattern=RESULT_ID_PATTERN)]
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
    steps: int = Field(strict=True, ge=0, le=1000000)
    planned_steps: int = Field(strict=True, ge=0, le=1000000)
    manifest: CropResearchManifest
    samples: list[CropResearchSample] = Field(max_length=20000)
    events: list[CropResearchEvent] = Field(max_length=20000)
    hold: CropResearchHold | None

    @model_validator(mode='after')
    def consistent(self):
        if self.start_utc >= self.end_utc or self.steps > self.planned_steps:
            raise ValueError('crop research display unavailable')
        if self.status == 'hold':
            if self.hold is None or self.samples or self.events:
                raise ValueError('crop research display unavailable')
        elif (self.hold is not None or len(self.samples)<2 or
                self.samples[0].at != self.start_utc or self.samples[-1].at != self.end_utc or
                any(a.at>=b.at for a,b in zip(self.samples,self.samples[1:]))):
            raise ValueError('crop research display unavailable')
        return self


def _need(value):
    if not value:
        raise CropResultHold('crop research display unavailable')


def project_crop_result(record):
    """Whitelist display fields after CropResultStore checked current custody/rights."""
    try:
        _need(type(record) is dict and set(record)=={'result_id','payload_raw','payload_sha256','recorded_at'}
            and type(record['payload_raw']) is bytes
            and sha256(record['payload_raw']).hexdigest()==record['payload_sha256']
            and type(record['recorded_at']) is datetime and record['recorded_at'].utcoffset() is not None)
        packet=_document(record['payload_raw'],max_size=MAX_PACKET_BYTES)
        result=packet['result']; manifest=result['manifest']; program=packet['request']['program']
        _need(packet['result_id']==record['result_id']=='crop-result-v1:'+sha256(
            _canonical({k:v for k,v in packet.items() if k!='result_id'})).hexdigest()
            and result['result_sha256']==integration._hash({k:v for k,v in result.items() if k!='result_sha256'})
            and packet['storage_code_sha256']==STORAGE_CODE_SHA256
            and manifest['code_sha256']==integration.CODE_HASHES
            and sha256(packet['profile_raw_utf8'].encode()).hexdigest()==manifest['profile_sha256']==integration.rates.PROFILE_SHA256
            and sha256(packet['notice_raw_utf8'].encode()).hexdigest()==NOTICE_SHA256)
        _need(manifest['origins']==['synthetic'] and packet['request']['rights']['program_sha256']==sha256(_canonical(program)).hexdigest())
        if result['status']=='completed':
            _need([s['at'] for s in result['samples']]==program['output_times'])
        public_manifest={k:manifest[k] for k in ('integrator_version','rate_model_version','domain_policy',
            'profile_id','profile_sha256','code_sha256','input_sha256','solver','time_rule','python_version',
            'convergence','temperature_sum_method')}
        public_manifest.update(storage_code_sha256=packet['storage_code_sha256'],
            raw_program_sha256=packet['request']['rights']['program_sha256'],
            result_sha256=result['result_sha256'],payload_sha256=record['payload_sha256'],notice_sha256=NOTICE_SHA256)
        hold=None
        if result['status']=='hold':
            diagnostic=result['hold']; last=diagnostic['last_confirmed']
            hold={'reason_code':diagnostic['reason'].partition(':')[0],
                **{k:diagnostic[k] for k in ('attempted_at','phase','time_meaning','failed_state')},
                'last_confirmed':None if last is None else {k:last[k] for k in CropResearchSample.model_fields}}
        binding=packet['binding']
        return CropResearchReplay(result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
            study_id=packet['request']['study_id'],revision=packet['request']['revision'],farm=packet['request']['farm'],
            batch_id=binding['crop']['batch_id'],zone_id=binding['zone_id'],farm_sha256=binding['farm_sha256'],
            source_binding_sha256=binding['source_binding_sha256'],storage_status=packet['status'],
            claim_scope=packet['claim_scope'],scope=result['scope'],gates='not_assessed',
            normalization=binding['normalization'],profile_applicability=binding['profile_applicability'],
            temporal_provenance='synthetic_research_program',start_utc=program['segments'][0]['start'],
            end_utc=program['segments'][-1]['end'],status=result['status'],steps=result['steps'],
            planned_steps=result['planned_steps'],manifest=public_manifest,samples=result['samples'],
            events=[{k:e[k] for k in ('at','removals','before','after')} for e in result['events']],hold=hold)
    except Exception:
        raise CropResultHold('crop research display unavailable') from None


def install_crop_routes(app, *, jobs, farms, store, principal_provider, authorized_tenant, error, access):
    if store is not None and (type(store) is not CropResultStore or store.jobs is not jobs
            or store.farms is not farms or farms is None or jobs.principal_provider is not principal_provider):
        raise ValueError('trusted crop research reader required')

    @app.get('/v1/crop-research-results/{result_id}',response_model=CropResearchReplay,
        operation_id='getCropResearchResult',openapi_extra=access(READ_SCOPES),
        responses={s:{'model':ErrorEnvelope} for s in (401,403,404,422,503)})
    def get_crop_research(request:Request,
            result_id:Annotated[str,Path(pattern=RESULT_ID_PATTERN)],
            scenario_id:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            scenario_revision:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            registration_sha256:Annotated[str,Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)]):
        tenant,denied=authorized_tenant(*READ_SCOPES)
        if denied is not None:return denied
        pairs=list(request.query_params.multi_items())
        if len(pairs)!=4 or {k for k,_ in pairs}!={'scenario_id','scenario_revision','registration_sha256','crop_id'}:
            return error(422,'invalid_request','Invalid request')
        if store is None:return error(503,'crop_research_unavailable','Crop research result unavailable')
        try:
            record=store.get(tenant,result_id,{'scenario_id':scenario_id,'scenario_revision':scenario_revision,
                'registration_sha256':registration_sha256,'crop_id':crop_id})
            if record is None:return error(404,'not_found','Crop research result not found')
            projected=project_crop_result(record)
            current,denied=authorized_tenant(*READ_SCOPES)
            if denied is not None:return denied
            if current!=tenant:return error(403,'forbidden','Resource access denied')
            return projected
        except PermissionError:return error(403,'forbidden','Resource access denied')
        except CropResultHold:return error(422,'crop_research_hold','Crop research evidence unavailable')
        except Exception:return error(503,'crop_research_unavailable','Crop research result unavailable')
