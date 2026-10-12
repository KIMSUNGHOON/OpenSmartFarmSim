import { ApiError,need,object,closed,date,member } from './api-validation';
import { utcMicroseconds } from './coupledCropReplay';
import { checkVentilationExecutionLookup,decodeVentilationExecutionCheckpoint,ventilationExecutionJobInstant,
  type VentilationExecutionLookup,type VentilationExecutionCheckpoint,type VentilationExecutionJob } from './greenhouseVentilationExecution';
import { decodeGreenhouseVentilationTimeGrid,decodeGreenhouseVentilationManifest,checkGreenhouseVentilationSample,checkGreenhouseVentilationEvent,
  type GreenhouseVentilationSample,type GreenhouseVentilationEvent,type GreenhouseVentilationFarm,type GreenhouseVentilationReference,
  type GreenhouseVentilationManifest,type GreenhouseVentilationTimeGrid } from './greenhouseVentilationReplay';
import type { JobStatus } from './api';

const VERSION='joint-ventilation-prefix-replay-v1',SCOPE='synthetic_joint_ventilation_math_only';
const CLAIM='synthetic_joint_ventilation_confirmed_prefix_only',MAX_BYTES=2*1024*1024,TIMEOUT=30_000;
const FARM=['scenario_id','scenario_revision','registration_sha256','crop_id'] as const;
const HASHES=['source_sha256','context_sha256','time_binding_sha256','evidence_sha256'] as const;
export type VentilationPrefixSelector=Readonly<{publication_sequence:number;head_sha256:string;proof_sha256:string}>;
export type VentilationPrefixReference=Readonly<{selector:VentilationPrefixSelector;checkpoint:VentilationExecutionCheckpoint;
  checkpoint_attempt:number;study_id:string;revision:string;farm:GreenhouseVentilationFarm;
  input:GreenhouseVentilationReference['input'];manifest:GreenhouseVentilationManifest;time_grid:GreenhouseVentilationTimeGrid}>;
type Counts=Readonly<{samples:number;events:number}>;
export type VentilationPrefixSummary=Readonly<{counts:Counts;last_sample_utc:string|null;last_event_utc:string|null}>;
type Meta=Readonly<{start:number;limit:number;total:number;next_offset:number|null}>;
export type VentilationPrefixPage=Meta & (Readonly<{kind:'samples';records:readonly GreenhouseVentilationSample[]}>
  | Readonly<{kind:'events';records:readonly GreenhouseVentilationEvent[]}>);
type Envelope=Readonly<{schema_version:typeof VERSION;scope:typeof SCOPE;claim_scope:typeof CLAIM;G0_G4:'not_assessed';
  job:VentilationExecutionJob;cancel_requested:boolean;observed_at:string}>;
export type VentilationPrefixAbsent=Envelope & Readonly<{prefix_status:'none'|'closed';reference:null;summary:null;page:null}>;
export type VentilationPrefixSummaryResponse=Envelope & Readonly<{prefix_status:'accepted';reference:VentilationPrefixReference;summary:VentilationPrefixSummary;page:null}>;
export type VentilationPrefixPageResponse=Envelope & Readonly<{prefix_status:'accepted';reference:VentilationPrefixReference;summary:null;page:VentilationPrefixPage}>;
export type VentilationPrefixResponse=VentilationPrefixAbsent|VentilationPrefixSummaryResponse|VentilationPrefixPageResponse;
export type VentilationPrefixPageQuery=Readonly<{kind:'samples'|'events';start:number;limit:number}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;
type DecodeJob=(v:unknown)=>JobStatus;

function integer(v:unknown,min:number,max:number):v is number{return typeof v==='number' && Number.isSafeInteger(v) && min<=v && v<=max;}
function digest(v:unknown):v is string{return typeof v==='string' && /^[0-9a-f]{64}$/.test(v);}
function name(v:unknown):v is string{return typeof v==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function utc(v:unknown):v is string{return date(v) && v.endsWith('Z');}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
function stable(v:unknown):string{
  if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
  if(object(v))return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
  return JSON.stringify(v);
}
function selector(v:unknown):asserts v is VentilationPrefixSelector{
  need(object(v));closed(v,['publication_sequence','head_sha256','proof_sha256']);
  need(integer(v.publication_sequence,1,4099) && digest(v.head_sha256) && digest(v.proof_sha256));
}
function pageQuery(v:unknown):asserts v is VentilationPrefixPageQuery{
  need(object(v));closed(v,['kind','start','limit']);need(member(v.kind,['samples','events'] as const)
    && integer(v.start,0,v.kind==='samples'?512:128) && integer(v.limit,1,v.kind==='samples'?64:8));
}
function at(stamp:unknown,r:VentilationPrefixReference){
  need(utc(stamp));const delta=utcMicroseconds(stamp)-utcMicroseconds(r.time_grid.start_utc);
  need(delta>=0n && delta%BigInt(r.time_grid.step_microseconds)===0n
    && delta/BigInt(r.time_grid.step_microseconds)<=BigInt(r.checkpoint.steps));
}
function reference(v:unknown,lookup:VentilationExecutionLookup,j:VentilationExecutionJob,observed:string):asserts v is VentilationPrefixReference{
  need(object(v));closed(v,['selector','checkpoint','checkpoint_attempt','study_id','revision','farm','input','manifest','time_grid']);
  selector(v.selector);const cp=decodeVentilationExecutionCheckpoint(v.checkpoint);
  need(integer(cp.steps,0,4096) && integer(cp.planned_steps,1,4096)
    && integer(cp.counts.samples,0,512) && integer(cp.counts.events,0,128)
    && integer(v.checkpoint_attempt,1,3) && v.checkpoint_attempt<=j.attempt_count && name(v.study_id) && name(v.revision));
  for(const k of ['publication_sequence','head_sha256','proof_sha256'] as const)need(v.selector[k]===cp[k]);
  need(utcMicroseconds(cp.checkpoint_recorded_at)>=ventilationExecutionJobInstant(j.created_at)
    && utcMicroseconds(cp.checkpoint_recorded_at)<=utcMicroseconds(observed));
  need(object(v.farm));closed(v.farm,[...FARM,'batch_id','zone_id']);
  for(const k of FARM)need(v.farm[k]===lookup.farm[k]);need(name(v.farm.batch_id) && name(v.farm.zone_id));
  need(object(v.input));closed(v.input,[...HASHES,'program_id','start_utc','end_utc']);
  for(const k of HASHES)need(digest(v.input[k]));need(name(v.input.program_id) && utc(v.input.start_utc) && utc(v.input.end_utc));
  const input=v.input as GreenhouseVentilationReference['input'];const grid=decodeGreenhouseVentilationTimeGrid(v.time_grid,input,cp.planned_steps);
  decodeGreenhouseVentilationManifest(v.manifest,grid);
  if(cp.status==='ready')need(cp.steps===0 && cp.counts.samples===0 && cp.counts.events===0);
  else need(utc(cp.computed_through_utc) && utcMicroseconds(cp.computed_through_utc)
    ===utcMicroseconds(grid.start_utc)+BigInt(cp.steps)*BigInt(grid.step_microseconds));
}
export function decodeGreenhouseVentilationPrefix(v:unknown,lookup:VentilationExecutionLookup,decodeJob:DecodeJob):VentilationPrefixResponse{
  checkVentilationExecutionLookup(lookup);need(object(v));closed(v,['schema_version','scope','claim_scope','G0_G4','job',
    'cancel_requested','observed_at','prefix_status','reference','summary','page']);
  const j=decodeJob(v.job);need(j.job_id===lookup.job_id && j.stage==='simulation'
    && member(j.state,['queued','simulating','succeeded','hold','failed','canceled'] as const));
  need(ventilationExecutionJobInstant(j.updated_at)>=ventilationExecutionJobInstant(j.created_at));
  if(j.state==='simulating' || j.state==='succeeded')need(j.attempt_count>=1);
  need(v.schema_version===VERSION && v.scope===SCOPE && v.claim_scope===CLAIM && v.G0_G4==='not_assessed'
    && typeof v.cancel_requested==='boolean' && utc(v.observed_at)
    && utcMicroseconds(v.observed_at)>=ventilationExecutionJobInstant(j.updated_at));
  need(member(v.prefix_status,['none','closed','accepted'] as const));
  const active=!v.cancel_requested && (j.state==='queued' || j.state==='simulating');
  if(v.prefix_status!=='accepted'){
    need((v.prefix_status==='none')===active && v.reference===null && v.summary===null && v.page===null);
    return v as VentilationPrefixAbsent;
  }
  need(active);reference(v.reference,lookup,j as VentilationExecutionJob,v.observed_at);const r=v.reference;
  need((v.summary===null)!==(v.page===null));
  if(v.summary!==null){
    need(object(v.summary));closed(v.summary,['counts','last_sample_utc','last_event_utc']);
    need(stable(v.summary.counts)===stable(r.checkpoint.counts));
    for(const [kind,key] of [['samples','last_sample_utc'],['events','last_event_utc']] as const){
      if(r.checkpoint.counts[kind]===0)need(v.summary[key]===null);else at(v.summary[key],r);
    }
  }else{
    need(object(v.page));const p=v.page;closed(p,['kind','start','limit','total','next_offset','records']);
    need(member(p.kind,['samples','events'] as const) && integer(p.start,0,r.checkpoint.counts[p.kind])
      && integer(p.limit,1,p.kind==='samples'?64:8) && p.total===r.checkpoint.counts[p.kind]
      && Array.isArray(p.records) && p.records.length===Math.min(p.limit,p.total-p.start));
    const end=p.start+p.records.length;need(p.next_offset===(end<p.total?end:null));let previous=-1;
    for(const row of p.records){
      if(p.kind==='samples')checkGreenhouseVentilationSample(row,r);
      else checkGreenhouseVentilationEvent(row,{time_grid:r.time_grid,model:r.manifest.identity});
      need(row.value.step_index>previous && row.value.step_index<=r.checkpoint.steps);previous=row.value.step_index;
    }
  }
  return v as VentilationPrefixSummaryResponse|VentilationPrefixPageResponse;
}
export function matchVentilationPrefixPage(summary:VentilationPrefixSummaryResponse,page:VentilationPrefixPageResponse){
  need(summary.job.job_id===page.job.job_id && stable(summary.reference)===stable(page.reference)
    && utcMicroseconds(page.observed_at)>=utcMicroseconds(summary.observed_at));
  if(page.page.records.length && page.page.next_offset===null){
    const last=page.page.records.at(-1)!;need(last.time.at===summary.summary[page.page.kind==='samples'?'last_sample_utc':'last_event_utc']);
  }
}
export function createGreenhouseVentilationPrefixApi(request:Request,decodeJob:DecodeJob){
  return {
    async greenhouseVentilationPrefix(lookup:VentilationExecutionLookup,signal?:AbortSignal):Promise<VentilationPrefixAbsent|VentilationPrefixSummaryResponse>{
      checkVentilationExecutionLookup(lookup);canceled(signal);const identity=JSON.stringify(lookup);
      const raw=await request('/v1/jobs/'+lookup.job_id+'/crop-greenhouse-ventilation-execution/prefix','GET',undefined,200,MAX_BYTES,TIMEOUT,signal);
      canceled(signal);need(JSON.stringify(lookup)===identity);const value=decodeGreenhouseVentilationPrefix(raw,lookup,decodeJob);
      need(value.page===null);return value as VentilationPrefixAbsent|VentilationPrefixSummaryResponse;
    },
    async greenhouseVentilationPrefixPage(lookup:VentilationExecutionLookup,pin:VentilationPrefixSelector,query:VentilationPrefixPageQuery,
      options:Readonly<{signal?:AbortSignal;summary?:VentilationPrefixSummaryResponse}>={}):Promise<VentilationPrefixPageResponse>{
      checkVentilationExecutionLookup(lookup);selector(pin);pageQuery(query);canceled(options.signal);
      if(options.summary)need(options.summary.job.job_id===lookup.job_id && stable(options.summary.reference.selector)===stable(pin));
      const identity=JSON.stringify([lookup,pin,query,options.summary]);
      const params=new URLSearchParams({...pin,publication_sequence:String(pin.publication_sequence),start:String(query.start),limit:String(query.limit)});
      const raw=await request('/v1/jobs/'+lookup.job_id+'/crop-greenhouse-ventilation-execution/prefix/'+query.kind+'?'+params,'GET',undefined,200,MAX_BYTES,TIMEOUT,options.signal);
      canceled(options.signal);need(JSON.stringify([lookup,pin,query,options.summary])===identity);
      const value=decodeGreenhouseVentilationPrefix(raw,lookup,decodeJob);need(value.prefix_status==='accepted' && value.page!==null);
      need(stable(value.reference.selector)===stable(pin) && value.page.kind===query.kind && value.page.start===query.start && value.page.limit===query.limit);
      if(options.summary)matchVentilationPrefixPage(options.summary,value);return value;
    },
  };
}
