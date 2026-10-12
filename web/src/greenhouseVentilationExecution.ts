import { ApiError,need,object,closed,date,member,uuid } from './api-validation';
import { utcMicroseconds } from './coupledCropReplay';
import type { JobStatus } from './api';
import type { GreenhouseVentilationLookup } from './greenhouseVentilationReplay';

const FARM=['scenario_id','scenario_revision','registration_sha256','crop_id'] as const;
const INPUT_HASHES=['source_sha256','context_sha256','time_binding_sha256','evidence_sha256'] as const;
const GRANTS=['ownership_asserted','access','store','transform','use','display'] as const;
const STATES=['queued','simulating','succeeded','hold','failed','canceled'] as const;
const VERSION='joint-ventilation-execution-query-v1',CANCEL_VERSION='joint-ventilation-execution-cancel-v1';
const SCOPE='synthetic_joint_ventilation_math_only',MAX_RESPONSE=16*1024,TIMEOUT=30_000;

export type VentilationExecutionFarm=Readonly<{scenario_id:string;scenario_revision:string;registration_sha256:string;crop_id:string}>;
export type VentilationExecutionLookup=Readonly<{job_id:string;farm:VentilationExecutionFarm}>;
export type VentilationExecutionRequest=Readonly<{study_id:string;revision:string;farm:VentilationExecutionFarm;
  input:Readonly<{schema_version:'joint-ventilation-input-source-v1';program_id:string;
    source_sha256:string;context_sha256:string;time_binding_sha256:string;evidence_sha256:string}>;
  rights:Readonly<{schema_version:'joint-ventilation-input-rights-v1';declaration_id:string;revision:string;
    input_source_sha256:string;available_at:string;redistribute:false;
    ownership_asserted:true;access:true;store:true;transform:true;use:true;display:true}>}>;
export type VentilationExecutionJob=JobStatus & {stage:'simulation';state:typeof STATES[number]};
export type VentilationExecutionCheckpoint=Readonly<{head_sha256:string;proof_sha256:string;artifact_sha256:string|null;
  status:'ready'|'yielded'|'completed'|'hold';steps:number;planned_steps:number;
  counts:Readonly<{samples:number;events:number}>;computed_through_utc:string|null;
  checkpoint_recorded_at:string;publication_sequence:number}>;
export type VentilationExecutionResult=Readonly<{result_id:string;farm:VentilationExecutionFarm & {batch_id:string;zone_id:string};
  status:'completed'|'hold'}>;
export type VentilationExecutionRead=Readonly<{version:typeof VERSION;scope:typeof SCOPE;G0_G4:'not_assessed';
  job:VentilationExecutionJob;cancel_requested:boolean;observed_at:string;checkpoint_status:'none'|'current'|'unavailable';
  checkpoint:VentilationExecutionCheckpoint|null;result:VentilationExecutionResult|null}>;
export type VentilationExecutionCancellation=Readonly<{version:typeof CANCEL_VERSION;scope:typeof SCOPE;G0_G4:'not_assessed';
  job:VentilationExecutionJob;cancel_requested:boolean;cancel_accepted:boolean;observed_at:string}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;
type DecodeJob=(value:unknown)=>JobStatus;

function name(v:unknown):v is string{return typeof v==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function digest(v:unknown):v is string{return typeof v==='string' && /^[0-9a-f]{64}$/.test(v);}
function utc(v:unknown):v is string{return date(v) && v.endsWith('Z');}
export function ventilationExecutionJobInstant(stamp:string):bigint{
  need(date(stamp));const fraction=/\.(\d{1,6})/.exec(stamp)?.[1]??'';
  return BigInt(Date.parse(stamp.replace(/\.\d{1,6}/,'')))*1000n+BigInt(fraction.padEnd(6,'0'));
}
function counter(v:unknown,min=0,max=Number.MAX_SAFE_INTEGER):v is number{
  return typeof v==='number' && Number.isSafeInteger(v) && v>=min && v<=max;
}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
function farm(v:unknown,result=false):asserts v is VentilationExecutionFarm{
  need(object(v));closed(v,result?[...FARM,'batch_id','zone_id']:FARM);
  for(const k of FARM)need(k==='registration_sha256'?digest(v[k]):name(v[k]));
  if(result)need(name(v.batch_id) && name(v.zone_id));
}
export function checkVentilationExecutionLookup(v:unknown):asserts v is VentilationExecutionLookup{
  need(object(v));closed(v,['job_id','farm']);need(uuid(v.job_id));farm(v.farm);
}
export function validVentilationExecutionRequest(v:unknown):v is VentilationExecutionRequest{
  try{
    need(object(v));closed(v,['study_id','revision','farm','input','rights']);need(name(v.study_id) && name(v.revision));farm(v.farm);
    const i=v.input,r=v.rights;need(object(i) && object(r));
    closed(i,['schema_version','program_id',...INPUT_HASHES]);
    need(i.schema_version==='joint-ventilation-input-source-v1' && name(i.program_id));
    for(const k of INPUT_HASHES)need(digest(i[k]));
    closed(r,['schema_version','declaration_id','revision','input_source_sha256','available_at','redistribute',...GRANTS]);
    need(r.schema_version==='joint-ventilation-input-rights-v1' && name(r.declaration_id) && name(r.revision)
      && r.input_source_sha256===i.source_sha256 && utc(r.available_at) && r.redistribute===false);
    for(const k of GRANTS)need(r[k]===true);
    return true;
  }catch(error){if(error instanceof ApiError)return false;throw error;}
}
function job(v:unknown,decode:DecodeJob,id?:string):VentilationExecutionJob{
  const j=decode(v);need(j.stage==='simulation' && member(j.state,STATES) && (!id || j.job_id===id)
    && ventilationExecutionJobInstant(j.updated_at)>=ventilationExecutionJobInstant(j.created_at));
  if(j.state==='simulating' || j.state==='succeeded')need(j.attempt_count>=1);
  return {...j,stage:j.stage,state:j.state};
}
function checkpoint(v:unknown):asserts v is VentilationExecutionCheckpoint{
  need(object(v));closed(v,['head_sha256','proof_sha256','artifact_sha256','status','steps','planned_steps',
    'counts','computed_through_utc','checkpoint_recorded_at','publication_sequence']);
  need(digest(v.head_sha256) && digest(v.proof_sha256) && member(v.status,['ready','yielded','completed','hold'] as const)
    && counter(v.steps,0,4096) && counter(v.planned_steps,1,4096) && v.steps<=v.planned_steps
    && utc(v.checkpoint_recorded_at) && counter(v.publication_sequence,1,4099));
  need(object(v.counts));closed(v.counts,['samples','events']);need(counter(v.counts.samples,0,512) && counter(v.counts.events,0,128));
  const terminal=v.status==='completed' || v.status==='hold';need(terminal?digest(v.artifact_sha256):v.artifact_sha256===null);
  need(v.status==='ready'?v.computed_through_utc===null && v.steps===0:utc(v.computed_through_utc));
  if(v.status==='completed')need(v.steps===v.planned_steps);
}
export function decodeVentilationExecutionCheckpoint(v:unknown):VentilationExecutionCheckpoint{checkpoint(v);return v;}
function result(v:unknown,expected:VentilationExecutionFarm):asserts v is VentilationExecutionResult{
  need(object(v));closed(v,['result_id','farm','status']);farm(v.farm,true);
  need(typeof v.result_id==='string' && /^joint-ventilation-result-v1:[0-9a-f]{64}$/.test(v.result_id)
    && member(v.status,['completed','hold'] as const));
  for(const k of FARM)need(v.farm[k]===expected[k]);
}
function envelope(v:Record<string,unknown>,version:string,j:VentilationExecutionJob){
  need(v.version===version && v.scope===SCOPE && v.G0_G4==='not_assessed'
    && typeof v.cancel_requested==='boolean' && utc(v.observed_at)
    && utcMicroseconds(v.observed_at)>=ventilationExecutionJobInstant(j.updated_at));
}
export function decodeVentilationExecutionRead(v:unknown,select:VentilationExecutionLookup,decode:DecodeJob):VentilationExecutionRead{
  checkVentilationExecutionLookup(select);need(object(v));closed(v,['version','scope','G0_G4','job','cancel_requested','observed_at','checkpoint_status','checkpoint','result']);
  const j=job(v.job,decode,select.job_id);envelope(v,VERSION,j);
  need(member(v.checkpoint_status,['none','current','unavailable'] as const));
  if(v.checkpoint!==null){
    checkpoint(v.checkpoint);need(v.checkpoint_status==='current'
      && utcMicroseconds(v.checkpoint.checkpoint_recorded_at)>=ventilationExecutionJobInstant(j.created_at)
      && utcMicroseconds(v.checkpoint.checkpoint_recorded_at)<=utcMicroseconds(String(v.observed_at)));
  }else need(v.checkpoint_status!=='current');
  if(v.result!==null){
    result(v.result,select.farm);need(v.checkpoint!==null && v.checkpoint.status===v.result.status
      && j.state===(v.result.status==='completed'?'succeeded':'hold'));
  }
  if(j.state==='succeeded' || j.state==='hold' && j.reason_code==='ventilation_numerical_hold'){
    need(v.checkpoint_status!=='none');if(v.checkpoint_status==='current')need(v.result!==null);
  }
  need(utc(v.observed_at) && typeof v.cancel_requested==='boolean');
  return {version:VERSION,scope:SCOPE,G0_G4:'not_assessed',job:j,cancel_requested:v.cancel_requested,
    observed_at:v.observed_at,checkpoint_status:v.checkpoint_status,checkpoint:v.checkpoint,result:v.result};
}
export function decodeVentilationExecutionCancellation(v:unknown,id:string,decode:DecodeJob):VentilationExecutionCancellation{
  need(uuid(id) && object(v));closed(v,['version','scope','G0_G4','job','cancel_requested','cancel_accepted','observed_at']);
  const j=job(v.job,decode,id);envelope(v,CANCEL_VERSION,j);
  need(typeof v.cancel_accepted==='boolean' && typeof v.cancel_requested==='boolean' && utc(v.observed_at));
  return {version:CANCEL_VERSION,scope:SCOPE,G0_G4:'not_assessed',job:j,cancel_requested:v.cancel_requested,
    cancel_accepted:v.cancel_accepted,observed_at:v.observed_at};
}
export function ventilationExecutionResultLookup(v:VentilationExecutionRead):GreenhouseVentilationLookup|null{
  if(v.result===null)return null;
  const {scenario_id,scenario_revision,registration_sha256,crop_id}=v.result.farm;
  return {result_id:v.result.result_id,scenario_id,scenario_revision,registration_sha256,crop_id};
}
export function createGreenhouseVentilationExecutionApi(request:Request,decode:DecodeJob){
  return {
    async submitGreenhouseVentilationExecution(input:VentilationExecutionRequest,signal?:AbortSignal):Promise<VentilationExecutionJob>{
      need(validVentilationExecutionRequest(input));canceled(signal);
      const identity=JSON.stringify(input);need(new TextEncoder().encode(identity).byteLength<=64*1024);
      const raw=await request('/v1/crop-greenhouse-ventilation-executions','POST',JSON.parse(identity),202,MAX_RESPONSE,TIMEOUT,signal);
      canceled(signal);need(JSON.stringify(input)===identity);return job(raw,decode);
    },
    async greenhouseVentilationExecution(select:VentilationExecutionLookup,signal?:AbortSignal):Promise<VentilationExecutionRead>{
      checkVentilationExecutionLookup(select);canceled(signal);const identity=JSON.stringify(select),id=select.job_id;
      const raw=await request('/v1/jobs/'+id+'/crop-greenhouse-ventilation-execution','GET',undefined,200,MAX_RESPONSE,TIMEOUT,signal);
      canceled(signal);need(JSON.stringify(select)===identity);return decodeVentilationExecutionRead(raw,select,decode);
    },
    async cancelGreenhouseVentilationExecution(id:string,signal?:AbortSignal):Promise<VentilationExecutionCancellation>{
      need(uuid(id));canceled(signal);
      const raw=await request('/v1/jobs/'+id+'/crop-greenhouse-ventilation-execution/cancel','POST',undefined,200,MAX_RESPONSE,TIMEOUT,signal);
      canceled(signal);return decodeVentilationExecutionCancellation(raw,id,decode);
    },
  };
}
