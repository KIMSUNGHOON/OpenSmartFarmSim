"""Bounded public projection after trusted cycle custody checked the original files."""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
from typing import Annotated,Literal
import re

from fastapi import Path,Query,Request,Response
from pydantic import Field,model_validator
from starlette.concurrency import run_in_threadpool

from .api_contracts import ErrorEnvelope
from .api_crop_replay import _Public,Digest,Name,UtcStamp,CropResearchFarm,NAME_PATTERN
from .api_crop_startup_replay import StartupFloorArea,StartupCropSample,StartupCropHold,StartupCodeHashes
from .api_crop_coupled_replay import CoupledCropEvent
from .crop_result_store import READ_SCOPES
from .crop_cycle_farm_binding import CycleFarmBindingHold
from .farm_authoring_storage import FarmAuthoringHold
from . import crop_cycle_stream_execution as engine
from . import crop_cycle_artifact as artifact
from .thermal_run_store import _canonical

RESULT_ID_PATTERN=r'^crop-cycle-result-v1:[0-9a-f]{64}$'
MAX_RESPONSE_BYTES=2*1024*1024


def _need(condition):
    if not condition:
        from .crop_cycle_server_custody import CycleCustodyHold
        raise CycleCustodyHold('cycle crop display unavailable')


def _at(value):return datetime.fromisoformat(value.replace('Z','+00:00'))


class CycleCodeHashes(_Public):
    stream_execution: Digest
    continuation: Digest
    input_stream: Digest


class CycleProfiles(_Public):
    growth_profile: Digest
    cohort_profile: Digest
    transport_profile: Digest


class CycleServerDependencies(_Public):
    artifact: Digest
    farm_binding: Digest
    input_stream: Digest
    execution: Digest
    directory_helper: Digest
    file_helper: Digest


class CycleSolver(_Public):
    method: Literal['rk4-fixed-v1']
    max_step_seconds: int = Field(strict=True,ge=1,le=3600)
    max_steps: int = Field(strict=True,ge=1,le=40000000)
    roundoff_rule: Literal['64-ulp-per-operation-v1']


class CycleCropManifest(_Public):
    engine_version: Literal['crop-cycle-stream-execution-research-v1']
    scope: Literal['software_research_only']
    physical_program_version: Literal['crop-plant-startup-program-v1']
    rate_model_version: Literal['explicit-entry-empty-sink-plant-rates-research-v1']
    input_root_sha256: Digest
    calculation_sha256: Digest
    grid_index_sha256: Digest
    grid_page_records: Literal[128]
    planned_steps: int = Field(strict=True,ge=1,le=40000000)
    boundary_count: int = Field(strict=True,ge=2,le=393216)
    code_sha256: CycleCodeHashes
    physical_code_sha256: StartupCodeHashes
    profile_sha256: CycleProfiles
    policy_sha256: Digest
    allocation_policy_sha256: Digest
    solver: CycleSolver
    python_version: Annotated[str,Field(strict=True,pattern=r'^3\.\d+\.\d+$',max_length=32)]
    time_rule: Literal['UTC_POSIX_whole_seconds_v1']
    temperature_sum_method: Literal['analytic_piecewise_constant_fraction_v1']


class CycleCropReference(_Public):
    storage_status: Literal['stored_unpublished_research']
    claim_scope: Literal['synthetic_crop_math_only']
    scope: Literal['software_research_only']
    gates: Literal['not_assessed']
    temporal_provenance: Literal['synthetic_research_program']
    batch_id: Name
    zone_id: Name
    floor_area: StartupFloorArea
    farm_sha256: Digest
    source_binding_sha256: Digest
    normalization: Literal['per_m2_floor']
    profile_applicability: Literal['unvalidated_for_registered_crop']
    start_utc: UtcStamp
    end_utc: UtcStamp
    artifact_ref: Annotated[str,Field(strict=True,pattern=r'^crop-cycle-artifact-v1:[0-9a-f]{64}$')]
    artifact_sha256: Digest
    header_sha256: Digest
    input_root_sha256: Digest
    calculation_sha256: Digest
    context_sha256: Digest
    binding_sha256: Digest
    intent_sha256: Digest
    head_sha256: Digest
    proof_sha256: Digest
    payload_sha256: Digest
    storage_code_sha256: Digest
    server_custody_code_sha256: Digest
    schema_code_sha256: Digest
    server_dependency_sha256: CycleServerDependencies
    binding_code_sha256: Digest
    notice_sha256: Digest
    input_rights_version: Name
    resolver_version: Name
    status: Literal['completed','hold']
    steps: int = Field(strict=True,ge=0,le=40000000)
    planned_steps: int = Field(strict=True,ge=1,le=40000000)
    sample_count: int = Field(strict=True,ge=0,le=131072)
    event_count: int = Field(strict=True,ge=0,le=131072)
    commit_count: int = Field(strict=True,ge=1,le=16384)
    storage_bytes: int = Field(strict=True,ge=1,le=512*1024*1024)
    file_count: int = Field(strict=True,ge=1,le=65536)

    @model_validator(mode='after')
    def consistent(self):
        start,end=_at(self.start_utc),_at(self.end_utc)
        _need(start<end and start.microsecond==end.microsecond==0
            and (end-start).total_seconds()<=366*86400 and self.steps<=self.planned_steps
            and (self.status!='completed' or self.steps==self.planned_steps)
            and self.artifact_ref==artifact.VERSION+':'+self.artifact_sha256)
        return self


class CycleCropSummary(_Public):
    status: Literal['completed','hold']
    manifest: CycleCropManifest
    hold: StartupCropHold | None


class CyclePage(_Public):
    offset: int = Field(strict=True,ge=0,le=131072)
    limit: int = Field(strict=True,ge=1,le=64)
    next_offset: Annotated[int,Field(strict=True,ge=0,le=131072)] | None
    total: int = Field(strict=True,ge=0,le=131072)

    @model_validator(mode='after')
    def consistent(self):
        count=len(self.records);following=self.offset+count
        _need(self.offset<=self.total and count<=min(self.limit,self.total-self.offset)
            and (count>0 or self.offset==self.total)
            and self.next_offset==(following if following<self.total else None))
        return self


class CycleSamplePage(CyclePage):
    kind: Literal['samples']
    records: list[StartupCropSample] = Field(max_length=64)


class CycleEventPage(CyclePage):
    kind: Literal['events']
    limit: int = Field(strict=True,ge=1,le=8)
    records: list[CoupledCropEvent] = Field(max_length=8)


class CycleCropReplay(_Public):
    schema_version: Literal['crop-cycle-replay-v1']
    result_id: Annotated[str,Field(strict=True,pattern=RESULT_ID_PATTERN)]
    recorded_at: UtcStamp
    study_id: Name
    revision: Name
    farm: CropResearchFarm
    reference: CycleCropReference
    summary: CycleCropSummary | None
    page: Annotated[CycleSamplePage | CycleEventPage,Field(discriminator='kind')] | None

    @model_validator(mode='after')
    def consistent(self):
        r=self.reference;start,end=_at(r.start_utc),_at(r.end_utc)
        _need((self.summary is None)!=(self.page is None))
        if self.summary is not None:
            s=self.summary;m=s.manifest
            _need(s.status==r.status and m.planned_steps==r.planned_steps<=m.solver.max_steps
                and m.input_root_sha256==r.input_root_sha256 and m.calculation_sha256==r.calculation_sha256
                and sha256(_canonical(m.model_dump(mode='json'))).hexdigest()==r.context_sha256)
            _need((s.hold is None)==(r.status=='completed'))
            if s.hold is not None:
                _need(start<=_at(s.hold.at)<=end and (s.hold.last_confirmed is None or
                    start<=_at(s.hold.last_confirmed.at)<=_at(s.hold.at)))
        if self.page is not None:
            p=self.page;_need(p.total==(r.sample_count if p.kind=='samples' else r.event_count))
            _need(all(start<=_at(v.at)<=end for v in p.records)
                and all(_at(a.at)<_at(b.at) for a,b in zip(p.records,p.records[1:])))
        return self


def _balances(sample):
    pairs=((sample.carbon_residual,sample.carbon_residual_budget),(sample.number_residual,sample.number_residual_budget),
        (sample.startup_diagnostics.requested_residual,sample.startup_diagnostics.requested_budget),
        (sample.startup_diagnostics.growth_respiration_residual,sample.startup_diagnostics.growth_respiration_budget))
    _need(all(abs(residual.value)<=budget.value for residual,budget in pairs))


def _public_bytes(projected):
    _need(type(projected) is CycleCropReplay)
    raw=projected.model_dump_json().encode();_need(1<=len(raw)<=MAX_RESPONSE_BYTES);return raw


def project_cycle_result(record,terminal,*,view='summary',page=None,limit=None):
    """Whitelist original quantities; this function does not grant source or farm rights."""
    from . import crop_cycle_result_store as storage
    from . import crop_cycle_server_custody as server
    try:
        _need(type(record) is dict and set(record)=={'result_id','payload_raw','payload_sha256','recorded_at'}
            and type(record['payload_raw']) is bytes and sha256(record['payload_raw']).hexdigest()==record['payload_sha256']
            and type(record['recorded_at']) is datetime and record['recorded_at'].utcoffset() is not None)
        packet=storage._decode(record['payload_raw']);_need(record['result_id']==packet['result_id'])
        binding=packet['binding'];request=binding['request'];registered=binding['registration'];source=binding['input']
        progress=packet['policies']['server_progress'];m=terminal['manifest'];held=progress['status']=='hold'
        keys={'status','scope','steps','planned_steps','output_start','event_start','checkpoint','manifest'}
        _need(type(terminal) is dict and set(terminal)==keys|({'hold','last_confirmed'} if held else set())
            and terminal['status']==progress['status'] and terminal['scope']=='software_research_only'
            and all(type(terminal[k]) is int for k in ('steps','planned_steps','output_start','event_start'))
            and terminal['steps']==progress['steps'] and terminal['planned_steps']==progress['planned_steps']
            and 0<=terminal['output_start']<=progress['counts']['samples']
            and 0<=terminal['event_start']<=progress['counts']['events'])
        manifest=CycleCropManifest.model_validate(m)
        _need(_canonical(manifest.model_dump(mode='json'))==_canonical(m)
            and sha256(_canonical(m)).hexdigest()==progress['context_sha256']
            and m['input_root_sha256']==packet['input_root_sha256']==source['root_sha256']
            and m['calculation_sha256']==source['calculation_sha256']
            and m['profile_sha256']==source['profile_sha256'] and m['python_version']==source['python_version']
            and m['planned_steps']==progress['planned_steps']<=m['solver']['max_steps']
            and m['code_sha256']=={'stream_execution':engine.CODE_SHA256,'continuation':engine.short.CODE_SHA256,'input_stream':engine.inputs.CODE_SHA256}
            and m['physical_code_sha256']==engine.physical.CODE_HASHES
            and m['policy_sha256']==engine.physical.startup.POLICY_SHA256
            and m['allocation_policy_sha256']==engine.physical.allocation.POLICY_SHA256
            and registered['crop']['crop_id']==request['farm']['crop_id'])
        if held:_need(terminal['checkpoint'] is None)
        else:
            cp=terminal['checkpoint'];_need(type(cp) is dict and cp['root_sha256']==progress['context_sha256']
                and cp['steps']==terminal['steps'] and cp['boundary_cursor']==m['boundary_count']
                and cp['output_cursor']==progress['counts']['samples'] and cp['event_cursor']==progress['counts']['events']
                and cp['at']==source['period']['end'] and cp['phase']=='boundary-committed')
        reference={'storage_status':packet['status'],'claim_scope':packet['claim_scope'],'scope':'software_research_only',
            'gates':'not_assessed','temporal_provenance':'synthetic_research_program',
            **{k:registered[k] for k in ('zone_id','farm_sha256','source_binding_sha256','normalization','profile_applicability')},
            'batch_id':registered['crop']['batch_id'],'floor_area':{k:registered['floor_area'][k] for k in ('value','unit')},
            'start_utc':source['period']['start'],'end_utc':source['period']['end'],
            **{k:progress[k] for k in ('header_sha256','input_root_sha256','context_sha256','binding_sha256',
                'intent_sha256','head_sha256','proof_sha256','status','steps','planned_steps','commit_count','storage_bytes','file_count')},
            'artifact_ref':packet['artifact']['ref'],'artifact_sha256':packet['artifact']['sha256'],
            'calculation_sha256':source['calculation_sha256'],'payload_sha256':record['payload_sha256'],
            **packet['code'],'binding_code_sha256':binding['binding_code_sha256'],
            **{k:packet['policies'][k] for k in ('notice_sha256','input_rights_version','resolver_version')},
            'sample_count':progress['counts']['samples'],'event_count':progress['counts']['events']}
        hold=None
        if held:
            diagnostic=terminal['hold'];_need(type(diagnostic) is dict and set(diagnostic)=={'at','phase','reason'}
                and type(diagnostic['reason']) is str and 1<=len(diagnostic['reason'])<=1000)
            hold={'reason_code':diagnostic['reason'].partition(':')[0],'at':diagnostic['at'],'phase':diagnostic['phase'],
                'time_meaning':'solver_evaluation_time','last_confirmed':terminal['last_confirmed']}
        original_summary=CycleCropSummary(status=terminal['status'],manifest=manifest,hold=hold)
        if original_summary.hold is not None and original_summary.hold.last_confirmed is not None:
            _balances(original_summary.hold.last_confirmed)
        public_page=None
        if view=='summary':_need(page is None and limit is None)
        else:
            _need(view in ('samples','events') and type(page) is dict and set(page)=={'kind','start','next','total','records'}
                and page['kind']==view and type(page['records']) is list
                and all(type(page[k]) is int for k in ('start','next','total'))
                and type(limit) is int and 1<=limit<=(64 if view=='samples' else 8)
                and page['next']==page['start']+len(page['records']))
            rows=page['records']
            if view=='events':
                _need(all(type(e) is dict and set(e)=={'at','input_id','before','after','removed'} for e in rows))
                rows=[{k:e[k] for k in ('at','before','after','removed')} for e in rows]
            cls=CycleSamplePage if view=='samples' else CycleEventPage
            public_page=cls(kind=view,offset=page['start'],limit=limit,total=page['total'],
                next_offset=page['next'] if page['next']<page['total'] else None,records=rows)
            _need(_canonical(public_page.model_dump(mode='json')['records'])==_canonical(rows))
            if view=='samples':
                for sample in public_page.records:_balances(sample)
            if held:
                cutoff=_at(original_summary.hold.at)
                _need(all(_at(row.at)<cutoff if view=='samples' else _at(row.at)<=cutoff for row in public_page.records))
        projected=CycleCropReplay(schema_version='crop-cycle-replay-v1',result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
            study_id=packet['study_id'],revision=packet['revision'],farm=request['farm'],reference=reference,
            summary=original_summary if view=='summary' else None,page=public_page)
        # Apply terminal consistency to page responses without exposing a second summary.
        CycleCropReplay(**{**projected.model_dump(mode='python'),'summary':original_summary,'page':None})
        _public_bytes(projected);return projected
    except Exception:raise server.CycleCustodyHold('cycle crop display unavailable') from None


def _read_cycle_response(store,tenant,result_id,farm_ref,view,offset,limit):
    with store._read(tenant,result_id,farm_ref) as (row,packet,journal):
        if row is None:return None
        expected=_canonical(packet['policies']['server_progress'])
        if view=='summary':
            journal._guard();_need(journal._progress()==expected);page=None
        else:page=journal.page(expected,view,offset,limit)
        terminal=deepcopy({**journal.writer._summary,'manifest':journal.context.manifest})
        projected=project_cycle_result(store._record(row),terminal,view=view,page=page,limit=limit)
        raw=_public_bytes(projected)
        store._current(tenant,_canonical(packet['binding']['request']),journal,expected)
        return raw


def _read_current_cycle_response(query,tenant,result_id,farm_ref,view,offset,limit):
    with query.open(tenant,result_id,farm_ref,kind=None if view=='summary' else view,
            start=offset,limit=limit) as value:
        if value is None:return None
        projected=project_cycle_result(value['record'],value['terminal'],view=view,page=value['page'],limit=limit)
        return _public_bytes(projected)


def install_cycle_crop_routes(app,*,jobs,farms,store,principal_provider,authorized_tenant,error,access,
        query=None):
    from . import crop_cycle_current_query as current_query
    if store is not None:
        from . import crop_cycle_result_store as storage
        if (type(store) is not storage.CycleCropResultStore or store.jobs is not jobs or farms is None
                or store.server.binding.farms is not farms or store.server.binding.jobs is not jobs
                or jobs.principal_provider is not principal_provider):
            raise ValueError('trusted cycle crop reader required')
        store._binding()
    if query is not None:
        if type(query) is not current_query.CurrentCycleQuery or store is None or query.store is not store:
            raise ValueError('trusted current cycle crop reader required')
        query._binding()
    reader=store if query is None else query
    read_response=_read_cycle_response if query is None else _read_current_cycle_response
    headers={} if query is None else {'X-OSSF-Crop-Query-Version':current_query.VERSION,
        'X-OSSF-Crop-Query-Code-SHA256':current_query.CODE_SHA256}

    @app.get('/v1/crop-cycle-research-results/{result_id}',response_model=CycleCropReplay,
        operation_id='getCycleCropResearchResult',openapi_extra=access(READ_SCOPES),
        responses={s:{'model':ErrorEnvelope} for s in (401,403,404,422,503)})
    async def get_cycle_crop(request:Request,result_id:Annotated[str,Path(pattern=RESULT_ID_PATTERN)],
            scenario_id:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            scenario_revision:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            registration_sha256:Annotated[str,Query(pattern=r'^[0-9a-f]{64}$')],
            crop_id:Annotated[str,Query(pattern=NAME_PATTERN,max_length=200)],
            view:Literal['summary','samples','events']='summary',
            offset:Annotated[int,Query(ge=0,le=131072)]=0,
            limit:Annotated[int|None,Query(ge=1,le=64)]=None):
        from .crop_cycle_server_custody import CycleCustodyHold
        tenant,denied=authorized_tenant(*READ_SCOPES)
        if denied is not None:return denied
        pairs=list(request.query_params.multi_items());keys=[k for k,_ in pairs]
        required={'scenario_id','scenario_revision','registration_sha256','crop_id'}
        if (len(keys)!=len(set(keys)) or not required<=set(keys)<=required|{'view','offset','limit'}
                or any(not re.fullmatch(r'0|[1-9][0-9]*',v) for k,v in pairs if k in ('offset','limit'))
                or (view=='summary' and bool({'offset','limit'}&set(keys)))
                or (view=='events' and limit is not None and limit>8)):
            return error(422,'invalid_request','Invalid request')
        async for chunk in request.stream():
            if chunk:return error(422,'invalid_request','Invalid request')
        if store is None:return error(503,'crop_research_unavailable','Crop research result unavailable')
        if view!='summary' and limit is None:limit=64 if view=='samples' else 8
        try:
            raw=await run_in_threadpool(read_response,reader,tenant,result_id,
                {'scenario_id':scenario_id,'scenario_revision':scenario_revision,
                 'registration_sha256':registration_sha256,'crop_id':crop_id},view,offset,limit)
            current,denied=authorized_tenant(*READ_SCOPES)
            if denied is not None:return denied
            if current!=tenant:return error(403,'forbidden','Resource access denied')
            if raw is None:return error(404,'not_found','Crop research result not found')
            return Response(raw,media_type='application/json',headers=headers)
        except PermissionError:return error(403,'forbidden','Resource access denied')
        except (CycleCustodyHold,CycleFarmBindingHold,FarmAuthoringHold,current_query.CurrentCycleQueryHold):
            return error(422,'crop_research_hold','Crop research evidence unavailable')
        except Exception:return error(503,'crop_research_unavailable','Crop research result unavailable')
