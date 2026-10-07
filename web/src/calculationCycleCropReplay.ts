import { ApiError,need,object,closed,date,member } from './api-validation';
import { type CropFarm } from './cropReplay';
import { utcMicroseconds,validateCoupledCropEvent,type CoupledCropEvent } from './coupledCropReplay';
import { validateStartupCropSample,type StartupCropSample,type StartupCropHold } from './startupCropReplay';

const MAX_RECORDS=131072,MAX_STEPS=40000000;
const FARM_KEYS=['scenario_id','scenario_revision','registration_sha256','crop_id'] as const;
const REFERENCE_LITERALS={storage_status:'stored_unpublished_research',claim_scope:'synthetic_crop_math_only',
  scope:'software_research_only',gates:'not_assessed',temporal_provenance:'synthetic_research_program',
  normalization:'per_m2_floor',profile_applicability:'unvalidated_for_registered_crop'} as const;
const REFERENCE_HASHES=['farm_sha256','source_binding_sha256','artifact_sha256','header_sha256','input_root_sha256',
  'calculation_sha256','context_sha256','binding_sha256','intent_sha256','head_sha256','proof_sha256','payload_sha256',
  'storage_code_sha256','server_custody_code_sha256','schema_code_sha256','binding_code_sha256','notice_sha256','runtime_roles_code_sha256'] as const;
const SERVER_KEYS=['artifact','farm_binding','input_stream','execution','directory_helper','file_helper','input_read_context'] as const;
const PHYSICAL_KEYS=['integrator','coupled','startup','plant','cohorts','allocation','transport','legacy_helpers','original_rates'] as const;
const PROFILE_KEYS=['growth_profile','cohort_profile','transport_profile'] as const;
const CODE_KEYS=['stream_execution','continuation','input_stream'] as const;
const EVIDENCE_KEYS=['input_stream','stream_execution','continuation','file_custody','directory_helper','file_metadata',
  'integrator','coupled','startup','plant','cohorts','allocation','transport','legacy_helpers','original_rates'] as const;
type InputEvidenceDependencies=Readonly<Record<typeof EVIDENCE_KEYS[number],string>>;
export type CalculationCycleCropInputValidation=Readonly<{context_sha256:string;evidence_sha256:string;
  validated_context_sha256:string;engine_version:'crop-cycle-verified-execution-research-v1';
  input_evidence_version:'crop-cycle-input-evidence-v1';calculation_code_sha256:string;
  input_evidence_code_sha256:string;input_evidence_dependency_sha256:InputEvidenceDependencies}>;
export type CalculationCycleCropManifestValidation=Readonly<{version:'crop-cycle-input-evidence-v1';
  evidence_sha256:string;validated_context_sha256:string;validation_engine_version:'crop-cycle-stream-execution-research-v1';
  validation_code_sha256:Readonly<Record<typeof CODE_KEYS[number],string>>;
  input_evidence_code_sha256:string;input_evidence_dependency_sha256:InputEvidenceDependencies}>;

const MANIFEST_LITERALS={engine_version:'crop-cycle-verified-execution-research-v1',scope:'software_research_only',
  physical_program_version:'crop-plant-startup-program-v1',rate_model_version:'explicit-entry-empty-sink-plant-rates-research-v1',
  time_rule:'UTC_POSIX_whole_seconds_v1',temperature_sum_method:'analytic_piecewise_constant_fraction_v1'} as const;
const MANIFEST_HASHES=['input_root_sha256','calculation_sha256','grid_index_sha256','policy_sha256','allocation_policy_sha256'] as const;
const HOLD_REASONS=['NUMERIC_HOLD','DEPLETED_STATE_HOLD','BALANCE_HOLD','REMOVAL_EXCEEDS_STORAGE_HOLD',
  'COMPENSATION_POINT_HOLD','INPUT_HOLD','UNIT_HOLD','PROFILE_HOLD','FRUIT_COHORT_STATE_HOLD',
  'FRUIT_COHORT_DOMAIN_HOLD','FRUIT_TRANSPORT_DOMAIN_HOLD','EMPTY_FRUIT_SINK_HOLD','FRUIT_ENTRY_BUDGET_HOLD',
  'FRUIT_ENTRY_STATE_HOLD','STATE_MISMATCH_HOLD'] as const;
const HOLD_PHASES=['rk4-k1','rk4-k2','rk4-k3','rk4-k4','step-end','step-end-arithmetic',
  'balance','boundary','boundary-after-event','event'] as const;
export type CalculationCycleCropLookup=CropFarm & Readonly<{result_id:string}>;
export type CalculationCycleCropManifest=Readonly<typeof MANIFEST_LITERALS & Record<typeof MANIFEST_HASHES[number],string> & {
  grid_page_records:128;planned_steps:number;boundary_count:number;
  code_sha256:Readonly<Record<typeof CODE_KEYS[number],string>>;
  physical_code_sha256:Readonly<Record<typeof PHYSICAL_KEYS[number],string>>;
  profile_sha256:Readonly<Record<typeof PROFILE_KEYS[number],string>>;
  solver:Readonly<{method:'rk4-fixed-v1';max_step_seconds:number;max_steps:number;roundoff_rule:'64-ulp-per-operation-v1'}>;
  python_version:string;input_validation:CalculationCycleCropManifestValidation}>;
export type CalculationCycleCropReference=Readonly<typeof REFERENCE_LITERALS & Record<typeof REFERENCE_HASHES[number],string> & {
  batch_id:string;zone_id:string;floor_area:Readonly<{value:string;unit:'m²'}>;start_utc:string;end_utc:string;
  artifact_ref:string;server_dependency_sha256:Readonly<Record<typeof SERVER_KEYS[number],string>>;
  input_validation:CalculationCycleCropInputValidation;input_rights_version:string;resolver_version:string;status:'completed'|'hold';steps:number;planned_steps:number;
  sample_count:number;event_count:number;commit_count:number;storage_bytes:number;file_count:number}>;
type Shared=Readonly<{schema_version:'crop-cycle-calculation-replay-v1';result_id:string;recorded_at:string;
  study_id:string;revision:string;farm:CropFarm;reference:CalculationCycleCropReference}>;
type PageMeta=Readonly<{offset:number;limit:number;next_offset:number|null;total:number}>;
export type CalculationCycleCropDataPage=PageMeta & (Readonly<{kind:'samples';records:readonly StartupCropSample[]}>
  | Readonly<{kind:'events';records:readonly CoupledCropEvent[]}>);
export type CalculationCycleCropSummaryResponse=Shared & Readonly<{page:null;
  summary:Readonly<{status:'completed'|'hold';manifest:CalculationCycleCropManifest;hold:StartupCropHold|null}>}>;
export type CalculationCycleCropPageResponse=Shared & Readonly<{summary:null;page:CalculationCycleCropDataPage}>;
export type CalculationCycleCropResponse=CalculationCycleCropSummaryResponse|CalculationCycleCropPageResponse;
export type CalculationCycleCropPageQuery=Readonly<{kind:'samples'|'events';offset:number;limit:number}>;
export type CalculationCycleCropLoadOptions=Readonly<{signal?:AbortSignal;summary?:CalculationCycleCropSummaryResponse}>;
export type CalculationCycleCropIterationOptions=Readonly<{signal?:AbortSignal;limit?:number;
  onSummary?:(summary:CalculationCycleCropSummaryResponse)=>void}>;
export type CalculationCycleCropCompletion=Readonly<{kind:'samples'|'events';count:number;total:number;complete:true}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;

function name(v:unknown):v is string{return typeof v==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function digest(v:unknown):v is string{return typeof v==='string' && /^[0-9a-f]{64}$/.test(v);}
function integer(v:unknown,min:number,max:number):v is number{return typeof v==='number' && Number.isSafeInteger(v) && v>=min && v<=max;}
function utc(v:unknown,whole=false):v is string{return date(v) && v.endsWith('Z') && (!whole || !v.includes('.'));}
function hashes(v:unknown,keys:readonly string[]){need(object(v));closed(v,keys);for(const k of keys)need(digest(v[k]));}
export function validCalculationCycleCropLookup(v:unknown):v is CalculationCycleCropLookup{
  return object(v) && Object.keys(v).length===5 && typeof v.result_id==='string'
    && /^crop-cycle-verified-result-v1:[0-9a-f]{64}$/.test(v.result_id) && name(v.scenario_id)
    && name(v.scenario_revision) && digest(v.registration_sha256) && name(v.crop_id);
}
function reference(v:unknown):asserts v is CalculationCycleCropReference{
  need(object(v));closed(v,[...Object.keys(REFERENCE_LITERALS),...REFERENCE_HASHES,'batch_id','zone_id','floor_area',
    'start_utc','end_utc','artifact_ref','server_dependency_sha256','input_rights_version','resolver_version','status',
    'steps','planned_steps','sample_count','event_count','commit_count','storage_bytes','file_count','input_validation']);
  for(const [k,label] of Object.entries(REFERENCE_LITERALS))need(v[k]===label);
  for(const k of REFERENCE_HASHES)need(digest(v[k]));hashes(v.server_dependency_sha256,SERVER_KEYS);
  for(const k of ['batch_id','zone_id','input_rights_version','resolver_version'])need(name(v[k]));
  need(object(v.floor_area));closed(v.floor_area,['value','unit']);
  need(v.floor_area.unit==='m²' && typeof v.floor_area.value==='string' && v.floor_area.value.length<=64
    && /^(?:[1-9][0-9]*(?:\.[0-9]+)?|0\.[0-9]*[1-9][0-9]*)$/.test(v.floor_area.value));
  need(utc(v.start_utc,true) && utc(v.end_utc,true));const start=utcMicroseconds(v.start_utc),end=utcMicroseconds(v.end_utc);
  need(start<end && end-start<=366n*86400n*1000000n && member(v.status,['completed','hold'] as const)
    && integer(v.steps,0,MAX_STEPS) && integer(v.planned_steps,1,MAX_STEPS) && v.steps<=v.planned_steps
    && (v.status!=='completed' || v.steps===v.planned_steps) && v.artifact_ref==='crop-cycle-verified-artifact-v1:'+v.artifact_sha256
    && integer(v.sample_count,0,MAX_RECORDS) && integer(v.event_count,0,MAX_RECORDS)
    && integer(v.commit_count,1,16384) && integer(v.storage_bytes,1,512*1024*1024) && integer(v.file_count,1,65536));
  inputValidation(v.input_validation,v.context_sha256);
}
function inputValidation(v:unknown,context:unknown):asserts v is CalculationCycleCropInputValidation{
  need(object(v));closed(v,['context_sha256','evidence_sha256','validated_context_sha256','engine_version',
    'input_evidence_version','calculation_code_sha256','input_evidence_code_sha256','input_evidence_dependency_sha256']);
  for(const key of ['context_sha256','evidence_sha256','validated_context_sha256','calculation_code_sha256',
    'input_evidence_code_sha256'])need(digest(v[key]));
  hashes(v.input_evidence_dependency_sha256,EVIDENCE_KEYS);
  need(v.context_sha256===context && v.engine_version==='crop-cycle-verified-execution-research-v1'
    && v.input_evidence_version==='crop-cycle-input-evidence-v1');
}
function manifestValidation(v:unknown,r:CalculationCycleCropInputValidation,code:unknown){
  need(object(v) && object(code));closed(v,['version','evidence_sha256','validated_context_sha256','validation_engine_version',
    'validation_code_sha256','input_evidence_code_sha256','input_evidence_dependency_sha256']);
  for(const key of ['evidence_sha256','validated_context_sha256','input_evidence_code_sha256'])need(digest(v[key]));
  hashes(v.validation_code_sha256,CODE_KEYS);hashes(v.input_evidence_dependency_sha256,EVIDENCE_KEYS);
  need(object(v.validation_code_sha256) && object(v.input_evidence_dependency_sha256));
  for(const key of CODE_KEYS)need(v.validation_code_sha256[key]===v.input_evidence_dependency_sha256[key]);
  need(v.version==='crop-cycle-input-evidence-v1' && v.validation_engine_version==='crop-cycle-stream-execution-research-v1'
    && r.evidence_sha256===v.evidence_sha256 && r.validated_context_sha256===v.validated_context_sha256
    && r.input_evidence_version===v.version && r.input_evidence_code_sha256===v.input_evidence_code_sha256
    && stable(r.input_evidence_dependency_sha256)===stable(v.input_evidence_dependency_sha256)
    && r.calculation_code_sha256===code.stream_execution
    && v.validation_code_sha256.continuation===code.continuation && v.validation_code_sha256.input_stream===code.input_stream);
}
function manifest(v:unknown,r:CalculationCycleCropReference){
  need(object(v));closed(v,[...Object.keys(MANIFEST_LITERALS),...MANIFEST_HASHES,'grid_page_records','planned_steps',
    'boundary_count','code_sha256','physical_code_sha256','profile_sha256','solver','python_version','input_validation']);
  for(const [k,label] of Object.entries(MANIFEST_LITERALS))need(v[k]===label);
  for(const k of MANIFEST_HASHES)need(digest(v[k]));hashes(v.code_sha256,CODE_KEYS);
  hashes(v.physical_code_sha256,PHYSICAL_KEYS);hashes(v.profile_sha256,PROFILE_KEYS);
  need(v.grid_page_records===128 && integer(v.planned_steps,1,MAX_STEPS) && v.planned_steps===r.planned_steps
    && integer(v.boundary_count,2,393216) && v.input_root_sha256===r.input_root_sha256
    && v.calculation_sha256===r.calculation_sha256 && typeof v.python_version==='string'
    && v.python_version.length<=32 && /^3\.\d+\.\d+$/.test(v.python_version));
  need(object(v.solver));closed(v.solver,['method','max_step_seconds','max_steps','roundoff_rule']);
  need(v.solver.method==='rk4-fixed-v1' && v.solver.roundoff_rule==='64-ulp-per-operation-v1'
    && integer(v.solver.max_step_seconds,1,3600) && integer(v.solver.max_steps,1,MAX_STEPS)
    && v.planned_steps<=v.solver.max_steps);
  manifestValidation(v.input_validation,r.input_validation,v.code_sha256);
}
function sample(v:unknown,confirmed=false):asserts v is StartupCropSample{
  validateStartupCropSample(v,confirmed);
  const pairs=[[v.carbon_residual,v.carbon_residual_budget],[v.number_residual,v.number_residual_budget],
    [v.startup_diagnostics.requested_residual,v.startup_diagnostics.requested_budget],
    [v.startup_diagnostics.growth_respiration_residual,v.startup_diagnostics.growth_respiration_budget]];
  for(const pair of pairs)need(Math.abs(pair[0]!.value)<=pair[1]!.value);
}
function hold(v:unknown,r:CalculationCycleCropReference){
  if(r.status==='completed'){need(v===null);return;}
  need(object(v));closed(v,['reason_code','at','phase','time_meaning','last_confirmed']);
  need(member(v.reason_code,HOLD_REASONS) && member(v.phase,HOLD_PHASES)
    && v.time_meaning==='solver_evaluation_time' && utc(v.at));
  const at=utcMicroseconds(v.at);need(at>=utcMicroseconds(r.start_utc) && at<=utcMicroseconds(r.end_utc));
  if(v.last_confirmed!==null){sample(v.last_confirmed,true);const past=utcMicroseconds(v.last_confirmed.at);
    need(past>=utcMicroseconds(r.start_utc) && past<=at);}
}
function dataPage(v:unknown,r:CalculationCycleCropReference){
  need(object(v));closed(v,['kind','offset','limit','next_offset','total','records']);
  need(member(v.kind,['samples','events'] as const) && integer(v.offset,0,MAX_RECORDS)
    && integer(v.total,0,MAX_RECORDS) && integer(v.limit,1,v.kind==='samples'?64:8)
    && v.total===(v.kind==='samples'?r.sample_count:r.event_count) && v.offset<=v.total
    && Array.isArray(v.records) && v.records.length<=Math.min(v.limit,v.total-v.offset)
    && (v.records.length>0 || v.offset===v.total));
  const next=v.offset+v.records.length;need(v.next_offset===(next<v.total?next:null));
  let previous:bigint|null=null;const start=utcMicroseconds(r.start_utc),end=utcMicroseconds(r.end_utc);
  for(const row of v.records){if(v.kind==='samples')sample(row);else validateCoupledCropEvent(row);
    const at=utcMicroseconds(row.at);need(at>=start && at<=end && (previous===null || at>previous));previous=at;}
}
export function decodeCalculationCycleCropResponse(v:unknown,lookup:CalculationCycleCropLookup):CalculationCycleCropResponse{
  need(validCalculationCycleCropLookup(lookup) && object(v));
  closed(v,['schema_version','result_id','recorded_at','study_id','revision','farm','reference','summary','page']);
  need(v.schema_version==='crop-cycle-calculation-replay-v1' && v.result_id===lookup.result_id && utc(v.recorded_at)
    && name(v.study_id) && name(v.revision) && object(v.farm));closed(v.farm,FARM_KEYS);
  for(const k of FARM_KEYS)need(v.farm[k]===lookup[k]);reference(v.reference);
  need((v.summary===null)!==(v.page===null));
  if(v.summary!==null){need(object(v.summary));closed(v.summary,['status','manifest','hold']);
    need(v.summary.status===v.reference.status);manifest(v.summary.manifest,v.reference);hold(v.summary.hold,v.reference);
  }else dataPage(v.page,v.reference);
  return v as CalculationCycleCropResponse;
}
function stable(v:unknown):string{
  if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
  if(object(v))return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
  return JSON.stringify(v);
}
function shared(v:CalculationCycleCropResponse){const {summary:_summary,page:_page,...rest}=v;return rest;}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
function matched(summary:CalculationCycleCropSummaryResponse,p:CalculationCycleCropPageResponse){
  need(stable(shared(summary))===stable(shared(p)));
  if(summary.summary.hold!==null){const at=utcMicroseconds(summary.summary.hold.at);
    for(const row of p.page.records)need(p.page.kind==='samples'?utcMicroseconds(row.at)<at:utcMicroseconds(row.at)<=at);}
}
export function createCalculationCycleCropReplayApi(request:Request){
  let inFlight=false;
  async function read(lookup:CalculationCycleCropLookup,view:'summary'|'samples'|'events',signal?:AbortSignal,query?:CalculationCycleCropPageQuery){
    need(validCalculationCycleCropLookup(lookup));canceled(signal);need(!inFlight);
    const identity=stable(lookup),search=new URLSearchParams({...lookup});search.delete('result_id');search.set('view',view);
    if(query){search.set('offset',String(query.offset));search.set('limit',String(query.limit));}
    inFlight=true;
    try{
      const raw=await request('/v1/crop-cycle-calculation-research-results/'+encodeURIComponent(lookup.result_id)+'?'+search,
        'GET',undefined,200,2*1024*1024,30_000,signal);
      canceled(signal);need(stable(lookup)===identity);return decodeCalculationCycleCropResponse(raw,lookup);
    }finally{inFlight=false;}
  }
  async function calculationCycleCropSummary(lookup:CalculationCycleCropLookup,signal?:AbortSignal):Promise<CalculationCycleCropSummaryResponse>{
    const value=await read(lookup,'summary',signal);need(value.summary!==null);return value;
  }
  async function calculationCycleCropPage(lookup:CalculationCycleCropLookup,query:CalculationCycleCropPageQuery,options:CalculationCycleCropLoadOptions={}):Promise<CalculationCycleCropPageResponse>{
    need(object(query));closed(query,['kind','offset','limit']);
    need(member(query.kind,['samples','events'] as const) && integer(query.offset,0,MAX_RECORDS)
      && integer(query.limit,1,query.kind==='samples'?64:8));
    need(object(options) && Object.keys(options).every(k=>k==='signal' || k==='summary'));
    const summary=options.summary,queryIdentity=stable(query),summaryIdentity=stable(summary);
    if(summary){need(decodeCalculationCycleCropResponse(summary,lookup).summary!==null);
      need(query.offset<=(query.kind==='samples'?summary.reference.sample_count:summary.reference.event_count));}
    const value=await read(lookup,query.kind,options.signal,query);need(value.page!==null);
    need(stable(query)===queryIdentity && stable(summary)===summaryIdentity && value.page.kind===query.kind
      && value.page.offset===query.offset && value.page.limit===query.limit);
    if(summary)matched(summary,value);return value;
  }
  async function* calculationCycleCropPages(lookup:CalculationCycleCropLookup,kind:'samples'|'events',options:CalculationCycleCropIterationOptions={}):
    AsyncGenerator<CalculationCycleCropPageResponse,CalculationCycleCropCompletion|undefined,void>{
    need(validCalculationCycleCropLookup(lookup) && member(kind,['samples','events'] as const) && object(options)
      && Object.keys(options).every(k=>k==='signal' || k==='limit' || k==='onSummary'));
    const limit=options.limit??(kind==='samples'?64:8),signal=options.signal,identity=stable(lookup);
    need(integer(limit,1,kind==='samples'?64:8) && (options.onSummary===undefined || typeof options.onSummary==='function'));
    const summary=await calculationCycleCropSummary(lookup,signal),summaryIdentity=stable(summary);
    const total=kind==='samples'?summary.reference.sample_count:summary.reference.event_count;
    options.onSummary?.(summary);
    let offset=0,pages=0,previous:bigint|null=null;
    for(;;){
      canceled(signal);need(stable(lookup)===identity && stable(summary)===summaryIdentity);
      const value=await calculationCycleCropPage(lookup,{kind,offset,limit},{signal,summary});
      need(++pages<=Math.max(total,1));
      for(const row of value.page.records){const at=utcMicroseconds(row.at);
        need(previous===null || previous<at);previous=at;}
      const count=offset+value.page.records.length,next=value.page.next_offset;
      yield value;
      canceled(signal);need(stable(lookup)===identity && stable(summary)===summaryIdentity);
      if(next===null){need(count===total);return {kind,count,total,complete:true};}
      offset=next;
    }
  }
  return {calculationCycleCropSummary,calculationCycleCropPage,calculationCycleCropPages};
}
