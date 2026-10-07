"""Closed public quantities preserving verified calculation provenance."""
from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
from typing import Annotated,Literal

from pydantic import Field,model_validator

from . import api_crop_cycle_replay as original
from .api_crop_replay import _Public,Digest
from .thermal_run_store import _canonical

VERSION='crop-cycle-calculation-replay-v1'
RESULT_ID_PATTERN=r'^crop-cycle-verified-result-v1:[0-9a-f]{64}$'
MAX_RESPONSE_BYTES=2*1024*1024
_at,_balances=original._at,original._balances


def _need(condition):
    if not condition:
        from .crop_cycle_calculation_server_custody import CalculationCustodyHold
        raise CalculationCustodyHold('cycle crop display unavailable')


class InputEvidenceDependencies(_Public):
    input_stream: Digest
    stream_execution: Digest
    continuation: Digest
    file_custody: Digest
    directory_helper: Digest
    file_metadata: Digest
    integrator: Digest
    coupled: Digest
    startup: Digest
    plant: Digest
    cohorts: Digest
    allocation: Digest
    transport: Digest
    legacy_helpers: Digest
    original_rates: Digest


class CalculationManifestValidation(_Public):
    version: Literal['crop-cycle-input-evidence-v1']
    evidence_sha256: Digest
    validated_context_sha256: Digest
    validation_engine_version: Literal['crop-cycle-stream-execution-research-v1']
    validation_code_sha256: original.CycleCodeHashes
    input_evidence_code_sha256: Digest
    input_evidence_dependency_sha256: InputEvidenceDependencies


class CalculationInputValidation(_Public):
    context_sha256: Digest
    evidence_sha256: Digest
    validated_context_sha256: Digest
    engine_version: Literal['crop-cycle-verified-execution-research-v1']
    input_evidence_version: Literal['crop-cycle-input-evidence-v1']
    calculation_code_sha256: Digest
    input_evidence_code_sha256: Digest
    input_evidence_dependency_sha256: InputEvidenceDependencies


class CalculationCycleCropManifest(original.CycleCropManifest):
    engine_version: Literal['crop-cycle-verified-execution-research-v1']
    input_validation: CalculationManifestValidation


class CalculationServerDependencies(original.CycleServerDependencies):
    input_read_context: Digest


class CalculationCycleCropReference(original.CycleCropReference):
    artifact_ref: Annotated[str,Field(strict=True,pattern=r'^crop-cycle-verified-artifact-v1:[0-9a-f]{64}$')]
    server_dependency_sha256: CalculationServerDependencies
    runtime_roles_code_sha256: Digest
    input_validation: CalculationInputValidation

    @model_validator(mode='after')
    def consistent(self):
        start,end=_at(self.start_utc),_at(self.end_utc)
        _need(start<end and start.microsecond==end.microsecond==0
            and (end-start).total_seconds()<=366*86400 and self.steps<=self.planned_steps
            and (self.status!='completed' or self.steps==self.planned_steps)
            and self.artifact_ref=='crop-cycle-verified-artifact-v1:'+self.artifact_sha256
            and self.input_validation.context_sha256==self.context_sha256)
        return self


class CalculationCycleCropSummary(original.CycleCropSummary):
    manifest: CalculationCycleCropManifest


class CalculationCycleCropReplay(original.CycleCropReplay):
    schema_version: Literal['crop-cycle-calculation-replay-v1']
    result_id: Annotated[str,Field(strict=True,pattern=RESULT_ID_PATTERN)]
    reference: CalculationCycleCropReference
    summary: CalculationCycleCropSummary | None

    @model_validator(mode='after')
    def validated_provenance(self):
        if self.summary is not None:
            m=self.summary.manifest;v=m.input_validation;r=self.reference.input_validation
            _need(r.evidence_sha256==v.evidence_sha256 and r.validated_context_sha256==v.validated_context_sha256
                and r.engine_version==m.engine_version and r.input_evidence_version==v.version
                and r.calculation_code_sha256==m.code_sha256.stream_execution
                and r.input_evidence_code_sha256==v.input_evidence_code_sha256
                and r.input_evidence_dependency_sha256==v.input_evidence_dependency_sha256)
        return self


def _public_bytes(projected):
    _need(type(projected) is CalculationCycleCropReplay)
    raw=projected.model_dump_json().encode();_need(1<=len(raw)<=MAX_RESPONSE_BYTES);return raw


def project_calculation_cycle_result(record,terminal,*,view='summary',page=None,limit=None):
    """Whitelist original quantities; this function does not grant source or farm rights."""
    from . import crop_cycle_calculation_result_store as storage
    from . import crop_cycle_calculation_server_custody as server
    from . import crop_cycle_calculation_context as engine
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
        manifest=CalculationCycleCropManifest.model_validate(m)
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
        validation=m['input_validation'];source_validation=source['input_validation']
        origin_manifest=deepcopy(m);del origin_manifest['input_validation']
        origin_manifest.update(engine_version=validation['validation_engine_version'],code_sha256=validation['validation_code_sha256'])
        _need(validation['version']==engine.evidence.VERSION
            and validation['validation_engine_version']==engine.legacy.VERSION
            and validation['validation_code_sha256']=={'stream_execution':engine.legacy.CODE_SHA256,
                'continuation':engine.short.CODE_SHA256,'input_stream':engine.inputs.CODE_SHA256}
            and validation['validated_context_sha256']==sha256(_canonical(origin_manifest)).hexdigest()
            and validation['input_evidence_code_sha256']==engine.evidence.CODE_SHA256
            and validation['input_evidence_dependency_sha256']==engine.evidence.DEPENDENCY_SHA256
            and source_validation=={'context_sha256':progress['context_sha256'],
                'evidence_sha256':validation['evidence_sha256'],'validated_context_sha256':validation['validated_context_sha256'],
                'engine_version':engine.VERSION,'input_evidence_version':engine.evidence.VERSION,
                'calculation_code_sha256':engine.CODE_SHA256,'input_evidence_code_sha256':engine.evidence.CODE_SHA256,
                'input_evidence_dependency_sha256':engine.evidence.DEPENDENCY_SHA256})
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
            'sample_count':progress['counts']['samples'],'event_count':progress['counts']['events'],
            'input_validation':source['input_validation']}
        hold=None
        if held:
            diagnostic=terminal['hold'];_need(type(diagnostic) is dict and set(diagnostic)=={'at','phase','reason'}
                and type(diagnostic['reason']) is str and 1<=len(diagnostic['reason'])<=1000)
            hold={'reason_code':diagnostic['reason'].partition(':')[0],'at':diagnostic['at'],'phase':diagnostic['phase'],
                'time_meaning':'solver_evaluation_time','last_confirmed':terminal['last_confirmed']}
        original_summary=CalculationCycleCropSummary(status=terminal['status'],manifest=manifest,hold=hold)
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
            cls=original.CycleSamplePage if view=='samples' else original.CycleEventPage
            public_page=cls(kind=view,offset=page['start'],limit=limit,total=page['total'],
                next_offset=page['next'] if page['next']<page['total'] else None,records=rows)
            _need(_canonical(public_page.model_dump(mode='json')['records'])==_canonical(rows))
            if view=='samples':
                for sample in public_page.records:_balances(sample)
            if held:
                cutoff=_at(original_summary.hold.at)
                _need(all(_at(row.at)<cutoff if view=='samples' else _at(row.at)<=cutoff for row in public_page.records))
        projected=CalculationCycleCropReplay(schema_version=VERSION,result_id=record['result_id'],
            recorded_at=record['recorded_at'].astimezone(timezone.utc).isoformat().replace('+00:00','Z'),
            study_id=packet['study_id'],revision=packet['revision'],farm=request['farm'],reference=reference,
            summary=original_summary if view=='summary' else None,page=public_page)
        # Apply terminal consistency to page responses without exposing a second summary.
        CalculationCycleCropReplay(**{**projected.model_dump(mode='python'),'summary':original_summary,'page':None})
        _public_bytes(projected);return projected
    except Exception:raise server.CalculationCustodyHold('cycle crop display unavailable') from None
