import { ApiError,need,object,closed,date,uuid } from './api-validation';
import { decodeMorphologyFrame,sha256,type MorphologyReplay,type MorphologyReplaySource } from './morphologyReplay';

const FLAGS={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'} as const;
const STATES=['queued','simulating','succeeded','hold','failed','canceled'] as const;
const SUMMARY_KEYS=['result_sha256','numerical_root_sha256','calculated_at','study_id','revision','farm','profile_applicability',
  'binding_sha256','program_sha256','source_sha256','input_evidence_sha256'] as const;
const MAX_BYTES=2*1024**2;
export type MorphologyJob={job_id:string;stage:'simulation';state:typeof STATES[number];attempt_count:number;max_attempts:number;
  created_at:string;updated_at:string;reason_code:string|null};
type Farm={scenario_id:string;scenario_revision:string;registration_sha256:string;crop_id:string};
export type MorphologyResult={result_sha256:string;numerical_root_sha256:string;calculated_at:string;study_id:string;revision:string;
  farm:Farm;profile_applicability:'unvalidated_for_registered_crop';binding_sha256:string;program_sha256:string;
  source_sha256:string;input_evidence_sha256:string};
export type MorphologyStatus={schema_version:'morphology-execution-read-v1';observed_at:string;job:MorphologyJob;
  cancel_requested:boolean;result:MorphologyResult|null;manifest:unknown;frame:unknown;replay:unknown}&typeof FLAGS;
export type MorphologyRequest={study_id:string;revision:string;farm:Farm;input:{schema_version:'morphology-input-source-v1';program_id:string;
  program_sha256:string;source_sha256:string;evidence_sha256:string};rights:{schema_version:'morphology-input-rights-v1';
    declaration_id:string;revision:string;input_source_sha256:string;available_at:string;redistribute:false;
    ownership_asserted:true;access:true;store:true;transform:true;use:true;display:true}};

function record(value:unknown){need(object(value));return value;}
function digest(value:unknown):asserts value is string {need(typeof value==='string'&&/^[0-9a-f]{64}$/.test(value));}
function name(value:unknown):asserts value is string {need(typeof value==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value));}
function flags(value:Record<string,unknown>){for(const [key,v] of Object.entries(FLAGS))need(value[key]===v);}
function farm(value:unknown){const v=record(value);closed(v,['scenario_id','scenario_revision','registration_sha256','crop_id']);
  name(v.scenario_id);name(v.scenario_revision);name(v.crop_id);digest(v.registration_sha256);return v as Farm;}
function job(value:unknown,id?:string):MorphologyJob {
  const v=record(value);closed(v,['job_id','stage','state','attempt_count','max_attempts','created_at','updated_at','reason_code']);
  need(uuid(v.job_id)&&(!id||v.job_id===id)&&v.stage==='simulation'&&typeof v.state==='string'&&STATES.some(s=>s===v.state));
  need(typeof v.attempt_count==='number'&&Number.isSafeInteger(v.attempt_count)&&v.attempt_count>=0&&typeof v.max_attempts==='number'&&
    Number.isSafeInteger(v.max_attempts)&&v.max_attempts>=1&&v.max_attempts<=3&&v.attempt_count<=v.max_attempts);
  need(date(v.created_at)&&date(v.updated_at)&&(v.reason_code===null||typeof v.reason_code==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(v.reason_code)));
  return v as MorphologyJob;
}
function result(value:unknown):MorphologyResult {
  const v=record(value);closed(v,SUMMARY_KEYS);
  for(const key of ['result_sha256','numerical_root_sha256','binding_sha256','program_sha256','source_sha256','input_evidence_sha256'])digest(v[key]);
  need(date(v.calculated_at)&&v.profile_applicability==='unvalidated_for_registered_crop');name(v.study_id);name(v.revision);farm(v.farm);
  return v as MorphologyResult;
}
export function decodeMorphologyRequest(value:unknown):MorphologyRequest {
  const v=record(value);closed(v,['study_id','revision','farm','input','rights']);name(v.study_id);name(v.revision);farm(v.farm);
  const i=record(v.input);closed(i,['schema_version','program_id','program_sha256','source_sha256','evidence_sha256']);
  need(i.schema_version==='morphology-input-source-v1');name(i.program_id);for(const k of ['program_sha256','source_sha256','evidence_sha256'])digest(i[k]);
  const r=record(v.rights);closed(r,['schema_version','declaration_id','revision','input_source_sha256','available_at','redistribute',
    'ownership_asserted','access','store','transform','use','display']);
  need(r.schema_version==='morphology-input-rights-v1'&&r.redistribute===false&&r.input_source_sha256===i.source_sha256&&date(r.available_at));
  name(r.declaration_id);name(r.revision);for(const k of ['ownership_asserted','access','store','transform','use','display'])need(r[k]===true);
  return v as MorphologyRequest;
}
export function decodeMorphologyStatus(value:unknown,id:string):MorphologyStatus {
  const v=record(value);closed(v,['schema_version',...Object.keys(FLAGS),'observed_at','job','cancel_requested','result','manifest','frame','replay']);
  flags(v);need(v.schema_version==='morphology-execution-read-v1'&&date(v.observed_at)&&typeof v.cancel_requested==='boolean');
  const j=job(v.job,id);if(v.result!==null)result(v.result);
  need((j.state==='succeeded')===(v.result!==null));
  if(v.result===null)need(v.manifest===null&&v.frame===null&&v.replay===null);
  return v as MorphologyStatus;
}
function metadataCanonical(value:unknown):string {
  if(value===null||typeof value==='string'||typeof value==='boolean')return JSON.stringify(value);
  if(typeof value==='number'){need(Number.isSafeInteger(value));return JSON.stringify(value);}
  if(Array.isArray(value))return '['+value.map(metadataCanonical).join(',')+']';
  const v=record(value);return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+metadataCanonical(v[k])).join(',')+'}';
}
export async function decodeMorphologyReplay(value:unknown,id:string):Promise<{status:MorphologyStatus;replay:MorphologyReplay}>{
  const status=decodeMorphologyStatus(value,id);need(status.result&&status.manifest===null&&status.frame===null);
  const r=record(status.replay);closed(r,['manifest','frames']);const signed=record(r.manifest);
  closed(signed,['schema_version',...Object.keys(FLAGS),...SUMMARY_KEYS,'manifest']);flags(signed);
  need(signed.schema_version==='morphology-signed-manifest-v1');
  for(const k of SUMMARY_KEYS){if(k==='farm'){const f=farm(signed.farm);for(const key of Object.keys(f) as (keyof Farm)[])need(f[key]===status.result.farm[key]);}
    else need(signed[k]===status.result[k]);}
  const root=record(signed.manifest);flags(root);
  need(root.schema_version==='morphology-research-artifact-v2'&&root.status==='completed_software_fixture'&&
    root.parameter_scope==='synthetic_software_fixture_only'&&root.time_kind==='synthetic_model_clock_not_observation'&&
    root.program_sha256===status.result.program_sha256);
  need(await sha256(new TextEncoder().encode(metadataCanonical(root)))===status.result.numerical_root_sha256);
  need(Array.isArray(root.samples)&&root.samples.length>=1&&root.samples.length<=512&&Array.isArray(r.frames)&&r.frames.length===root.samples.length);
  const source:MorphologyReplaySource={version:'v2',directory:'./morphology-rational-replay',frames:r.frames.length,
    artifact_sha256:status.result.numerical_root_sha256,index_sha256:'0'.repeat(64)};
  let previous='';const frames=[];
  for(let index=0;index<r.frames.length;index++){
    const d=record(root.samples[index]);need(d.index===index&&date(d.at)&&d.at>previous);previous=d.at;
    digest(d.result_sha256);digest(d.input_sha256);
    const frame=decodeMorphologyFrame(r.frames[index],{index,at:d.at,path:'',sha256:'0'.repeat(64),bytes:1,result_sha256:d.result_sha256},source);
    need(frame.input_sha256===d.input_sha256);
    if(frames.length){const first=frames[0]!;need(frame.shoot_id===first.shoot_id&&frame.schema_version==='morphology-replay-frame-v2'&&
      first.schema_version==='morphology-replay-frame-v2'&&frame.time_origin_utc===first.time_origin_utc);}
    frames.push(frame);
  }
  return {status,replay:{artifact_sha256:source.artifact_sha256,frames}};
}

export function createMorphologyExecutionClient(token:string){
  need(/^[A-Za-z0-9_-]{32,128}$/.test(token));
  async function request(path:string,signal:AbortSignal,method='GET',body?:unknown){
    const headers:Record<string,string>={Authorization:'Bearer '+token};if(body!==undefined)headers['Content-Type']='application/json';
    const response=await fetch(path,{method,headers,body:body===undefined?undefined:JSON.stringify(body),signal,cache:'no-store',redirect:'error',credentials:'omit'});
    if(!response.ok)throw new ApiError('morphology_request_unavailable',response.status);
    need(response.body);const reader=response.body.getReader();let size=0;const chunks=[];
    try{while(true){const value=await reader.read();if(value.done)break;size+=value.value.byteLength;need(size<=MAX_BYTES);chunks.push(value.value);}}
    catch(error){await reader.cancel().catch(()=>{});throw error;}finally{reader.releaseLock();}
    const raw=new Uint8Array(size);let offset=0;for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.length;}
    return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)) as unknown;
  }
  function path(id:string){need(uuid(id));return `/v1/jobs/${id}/crop-morphology-execution`;}
  return Object.freeze({
    async submit(value:MorphologyRequest,signal:AbortSignal){decodeMorphologyRequest(value);return job(await request('/v1/crop-morphology-executions',signal,'POST',value));},
    async status(id:string,signal:AbortSignal){const v=decodeMorphologyStatus(await request(path(id),signal),id);
      need(v.manifest===null&&v.frame===null&&v.replay===null);return v;},
    async replay(id:string,signal:AbortSignal){return decodeMorphologyReplay(await request(path(id)+'/replay',signal),id);},
    async cancel(id:string,signal:AbortSignal){const v=record(await request(path(id)+'/cancel',signal,'POST'));
      closed(v,['schema_version',...Object.keys(FLAGS),'observed_at','job','cancel_requested','cancel_accepted']);flags(v);
      need(v.schema_version==='morphology-execution-cancel-v1'&&date(v.observed_at)&&typeof v.cancel_requested==='boolean'&&typeof v.cancel_accepted==='boolean');
      return {job:job(v.job,id),cancel_requested:v.cancel_requested,cancel_accepted:v.cancel_accepted};},
    async preview(signal:AbortSignal){const v=record(await request('/preview-input',signal));
      closed(v,['schema_version',...Object.keys(FLAGS),'label','request']);flags(v);
      need(v.schema_version==='owned-morphology-preview-input-v1'&&typeof v.label==='string'&&v.label.length>=1&&v.label.length<=120);
      return {label:v.label,request:decodeMorphologyRequest(v.request)};},
  });
}
export type MorphologyExecutionClient=ReturnType<typeof createMorphologyExecutionClient>;
