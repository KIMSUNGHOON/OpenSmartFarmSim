import {ApiError,need,object,closed,date,uuid} from './api-validation';
import {decodeMorphologyFrame,sha256,type MorphologyReplaySource} from './morphologyReplay';
import {MODELS,DISPLAY,type LeafPopulationFrame,type LeafPopulationReplay} from './leafPopulationReplay';
import {area,exact,constants,integer,utc} from './storedLeafReplayIO';
import type {MorphologyJob} from './morphologyExecution';

const FLAGS={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'} as const;
const STATES=['queued','simulating','succeeded','hold','failed','canceled'] as const;
const SUMMARY_KEYS=['result_sha256','numerical_root_sha256','calculated_at','parent_job_id','parent_result_sha256',
  'parent_numerical_root_sha256','parent_calculated_at','normalization','study_id','revision','farm','profile_applicability',
  'binding_sha256','program_sha256','source_sha256','input_evidence_sha256'] as const;
const MAX_BYTES=2*1024**2;
type Farm={scenario_id:string;scenario_revision:string;registration_sha256:string;crop_id:string};
export type LeafPopulationJob=MorphologyJob;
export type LeafPopulationRequest={study_id:string;revision:string;farm:Farm;
  parent:{job_id:string;result_sha256:string;numerical_root_sha256:string};
  input:{schema_version:'leaf-population-input-source-v1';program_id:string;program_sha256:string;source_sha256:string;evidence_sha256:string};
  rights:{schema_version:'leaf-population-input-rights-v1';declaration_id:string;revision:string;input_source_sha256:string;
    available_at:string;redistribute:false;ownership_asserted:true;access:true;store:true;transform:true;use:true;display:true}};
export type LeafPopulationResult={result_sha256:string;numerical_root_sha256:string;calculated_at:string;
  parent_job_id:string;parent_result_sha256:string;parent_numerical_root_sha256:string;parent_calculated_at:string;
  normalization:'per_tracked_shoot';study_id:string;revision:string;farm:Farm;profile_applicability:'unvalidated_for_registered_crop';
  binding_sha256:string;program_sha256:string;source_sha256:string;input_evidence_sha256:string};
export type LeafPopulationStatus={schema_version:'leaf-population-execution-read-v1';observed_at:string;job:LeafPopulationJob;
  cancel_requested:boolean;result:LeafPopulationResult|null;manifest:unknown;frame:unknown;replay:unknown}&typeof FLAGS;

function record(value:unknown){need(object(value));return value;}
function shape(value:unknown,keys:readonly string[]){const v=record(value);closed(v,keys);return v;}
function digest(value:unknown):asserts value is string{need(typeof value==='string'&&/^[0-9a-f]{64}$/.test(value));}
function name(value:unknown):asserts value is string{need(typeof value==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value));}
function stamp(value:unknown):asserts value is string{need(date(value)&&value.endsWith('Z'));}
function flags(value:Record<string,unknown>){for(const [k,v]of Object.entries(FLAGS))need(value[k]===v);}
function farm(value:unknown){const v=shape(value,['scenario_id','scenario_revision','registration_sha256','crop_id']);
  name(v.scenario_id);name(v.scenario_revision);name(v.crop_id);digest(v.registration_sha256);return v as Farm;}
function job(value:unknown,id?:string):LeafPopulationJob{
  const v=shape(value,['job_id','stage','state','attempt_count','max_attempts','created_at','updated_at','reason_code']);
  need(uuid(v.job_id)&&(!id||v.job_id===id)&&v.stage==='simulation'&&STATES.some(s=>s===v.state));
  integer(v.max_attempts,1,3);integer(v.attempt_count,0,v.max_attempts);need(date(v.created_at)&&date(v.updated_at));
  need(v.reason_code===null||typeof v.reason_code==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(v.reason_code));
  return v as LeafPopulationJob;
}
function result(value:unknown):LeafPopulationResult{
  const v=shape(value,SUMMARY_KEYS);
  for(const k of ['result_sha256','numerical_root_sha256','parent_result_sha256','parent_numerical_root_sha256',
    'binding_sha256','program_sha256','source_sha256','input_evidence_sha256'])digest(v[k]);
  stamp(v.calculated_at);stamp(v.parent_calculated_at);need(uuid(v.parent_job_id));
  need(v.normalization==='per_tracked_shoot'&&v.profile_applicability==='unvalidated_for_registered_crop');
  name(v.study_id);name(v.revision);farm(v.farm);return v as LeafPopulationResult;
}
export function decodeLeafPopulationRequest(value:unknown):LeafPopulationRequest{
  const v=shape(value,['study_id','revision','farm','parent','input','rights']);name(v.study_id);name(v.revision);farm(v.farm);
  const p=shape(v.parent,['job_id','result_sha256','numerical_root_sha256']);need(uuid(p.job_id));digest(p.result_sha256);digest(p.numerical_root_sha256);
  const i=shape(v.input,['schema_version','program_id','program_sha256','source_sha256','evidence_sha256']);
  need(i.schema_version==='leaf-population-input-source-v1');name(i.program_id);for(const k of ['program_sha256','source_sha256','evidence_sha256'])digest(i[k]);
  const r=shape(v.rights,['schema_version','declaration_id','revision','input_source_sha256','available_at','redistribute',
    'ownership_asserted','access','store','transform','use','display']);
  need(r.schema_version==='leaf-population-input-rights-v1'&&r.redistribute===false&&r.input_source_sha256===i.source_sha256);
  stamp(r.available_at);name(r.declaration_id);name(r.revision);for(const k of ['ownership_asserted','access','store','transform','use','display'])need(r[k]===true);
  return v as LeafPopulationRequest;
}
export function decodeLeafPopulationStatus(value:unknown,id:string):LeafPopulationStatus{
  const v=shape(value,['schema_version',...Object.keys(FLAGS),'observed_at','job','cancel_requested','result','manifest','frame','replay']);
  flags(v);need(v.schema_version==='leaf-population-execution-read-v1'&&typeof v.cancel_requested==='boolean');stamp(v.observed_at);
  const j=job(v.job,id);if(v.result!==null){const r=result(v.result);need(r.parent_job_id!==j.job_id);}
  need((j.state==='succeeded')===(v.result!==null));
  if(v.result===null)need(v.manifest===null&&v.frame===null&&v.replay===null);
  else need(v.cancel_requested===false&&j.attempt_count>=1);
  return v as LeafPopulationStatus;
}
function canonical(value:unknown):string{
  if(value===null||typeof value==='string'||typeof value==='boolean')return JSON.stringify(value);
  if(typeof value==='number'){need(Number.isSafeInteger(value));return JSON.stringify(value);}
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  const v=record(value);return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
}
function rootManifest(value:unknown){
  const m=shape(value,['schema_version','status','scope','claim_scope','gates','time_kind','parameter_scope','model_versions','display_policy',
    'program_sha256','program_bytes','program_rights','stem_artifact_sha256','stem_program_sha256','code_sha256','time_origin_utc',
    'initial_at_elapsed_seconds_exact','initial_state_sha256','terminal_state_sha256','samples']);flags(m);
  need(m.schema_version==='leaf-population-research-artifact-v1'&&m.status==='completed_software_fixture'&&
    m.time_kind==='synthetic_model_clock_not_observation'&&m.parameter_scope==='synthetic_software_fixture_only');
  constants(m.model_versions,MODELS);constants(m.display_policy,DISPLAY);utc(m.time_origin_utc);
  for(const k of ['program_sha256','stem_artifact_sha256','stem_program_sha256','initial_state_sha256','terminal_state_sha256'])digest(m[k]);
  integer(m.program_bytes,1,MAX_BYTES);const initial=exact(m.initial_at_elapsed_seconds_exact,'s');
  const r=shape(m.program_rights,['access','declaration_id','declared_at_utc','display','ownership_asserted','redistribute','revision','store','transform','use']);
  for(const k of ['access','display','ownership_asserted','store','transform','use'])need(r[k]===true);
  need(typeof r.redistribute==='boolean');name(r.declaration_id);name(r.revision);utc(r.declared_at_utc);
  const codes=record(m.code_sha256);need(Object.keys(codes).length===28);
  for(const [path,hash]of Object.entries(codes)){need(/^backend\/app\/[a-z_]+\.py$/.test(path));digest(hash);}
  need(Array.isArray(m.samples)&&m.samples.length>=1&&m.samples.length<=512);let previous=m.initial_state_sha256,last='';
  for(let index=0;index<m.samples.length;index++){
    const d=shape(m.samples[index],['index','at','result_sha256','result_bytes','binding_sha256','binding_bytes','input_state_sha256','state_sha256','input_sha256','stem_result_sha256']);
    utc(d.at);need(d.index===index&&d.at>last&&d.input_state_sha256===previous);last=d.at;previous=d.state_sha256 as string;
    const elapsed=BigInt((Date.parse(d.at)-Date.parse(m.time_origin_utc))/1000);need(elapsed*initial.d>initial.n);
    integer(d.result_bytes,1,MAX_BYTES);integer(d.binding_bytes,1,MAX_BYTES);
    for(const k of ['result_sha256','binding_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256'])digest(d[k]);
  }
  need(previous===m.terminal_state_sha256);return m;
}
function sumAgrees(values:number[],total:number){
  const sum=values.reduce((a,b)=>a+b,0);need(Number.isFinite(sum)&&Math.abs(sum-total)<=Number.EPSILON*(values.length+1)*Math.max(sum,total));
}
function decodeFrame(value:unknown,m:Record<string,unknown>,sample:unknown,rootSha:string,count:number):LeafPopulationFrame{
  const d=record(sample),f=shape(value,['schema_version','scope','claim_scope','gates','artifact_sha256','result_sha256','binding_sha256','input_sha256',
    'index','at','time_origin_utc','tracked_leaf_count','tracked_leaf_area','leaves','stem']);flags(f);
  need(f.schema_version==='leaf-population-replay-frame-v1'&&f.artifact_sha256===rootSha&&f.result_sha256===d.result_sha256&&
    f.binding_sha256===d.binding_sha256&&f.input_sha256===d.input_sha256&&f.index===d.index&&f.at===d.at&&f.time_origin_utc===m.time_origin_utc);
  integer(f.tracked_leaf_count,1,512);area(f.tracked_leaf_area);const source:MorphologyReplaySource={version:'v2',directory:'./morphology-rational-replay',
    artifact_sha256:m.stem_artifact_sha256 as string,index_sha256:'0'.repeat(64),frames:count};
  const stem=decodeMorphologyFrame(f.stem,{index:d.index as number,at:d.at as string,path:'',sha256:'0'.repeat(64),bytes:1,result_sha256:d.stem_result_sha256 as string},source);
  need(stem.schema_version==='morphology-replay-frame-v2'&&stem.at===f.at&&stem.time_origin_utc===f.time_origin_utc);
  need(Array.isArray(f.leaves)&&f.leaves.length===f.tracked_leaf_count);const ids=new Set<string>();
  const elapsed=BigInt((Date.parse(stem.at)-Date.parse(stem.time_origin_utc))/1000);
  for(const raw of f.leaves){
    const q=shape(raw,['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact','age_exact','area']);
    name(q.leaf_id);name(q.attachment_internode_id);digest(q.curve_sha256);need(!ids.has(q.leaf_id));ids.add(q.leaf_id);
    const birth=exact(q.emerged_elapsed_seconds_exact,'s');need(birth.n<=elapsed*birth.d);exact(q.age_exact,'degC_day');area(q.area);
    const parent=stem.internodes.find(node=>node.internode_id===q.attachment_internode_id);need(parent);
    const parentBirth=exact(parent.emerged_elapsed_seconds_exact,'s');need(parentBirth.n*birth.d<=birth.n*parentBirth.d);
  }
  const decoded={...f,stem} as LeafPopulationFrame;
  sumAgrees(decoded.leaves.map(q=>q.area.value),decoded.tracked_leaf_area.value);
  sumAgrees(stem.internodes.map(q=>q.length.value),stem.tracked_axis_length.value);return decoded;
}
export async function decodeLeafPopulationExecutionReplay(value:unknown,id:string):Promise<{status:LeafPopulationStatus;replay:LeafPopulationReplay}>{
  const status=decodeLeafPopulationStatus(value,id);need(status.result&&status.manifest===null&&status.frame===null);
  const r=shape(status.replay,['manifest','frames']),signed=shape(r.manifest,['schema_version',...Object.keys(FLAGS),...SUMMARY_KEYS,'manifest']);flags(signed);
  need(signed.schema_version==='leaf-population-signed-manifest-v1');const summary=result(status.result);
  for(const key of SUMMARY_KEYS)need(canonical(signed[key])===canonical(summary[key]));
  const root=rootManifest(signed.manifest);need(root.program_sha256===summary.program_sha256&&root.stem_artifact_sha256===summary.parent_numerical_root_sha256);
  need(await sha256(new TextEncoder().encode(canonical(root)))===summary.numerical_root_sha256);
  const samples=root.samples as unknown[];need(Array.isArray(r.frames)&&r.frames.length===samples.length);
  const frames=r.frames.map((v,index)=>decodeFrame(v,root,samples[index],summary.numerical_root_sha256,samples.length));
  for(let index=1;index<frames.length;index++){
    const previous=frames[index-1]!,current=frames[index]!;need(previous.stem.shoot_id===current.stem.shoot_id&&current.leaves.length>=previous.leaves.length);
    for(let i=0;i<previous.leaves.length;i++){
      const a=previous.leaves[i]!,b=current.leaves[i]!;need(a.leaf_id===b.leaf_id&&a.attachment_internode_id===b.attachment_internode_id&&
        a.curve_sha256===b.curve_sha256&&canonical(a.emerged_elapsed_seconds_exact)===canonical(b.emerged_elapsed_seconds_exact));
    }
  }
  return {status,replay:{artifact_sha256:summary.numerical_root_sha256,frames}};
}

export function createLeafPopulationExecutionClient(token:string){
  need(/^[A-Za-z0-9_-]{32,128}$/.test(token));
  async function request(path:string,signal:AbortSignal,method='GET',body?:unknown){
    const headers:Record<string,string>={Authorization:'Bearer '+token};if(body!==undefined)headers['Content-Type']='application/json';
    const response=await fetch(path,{method,headers,body:body===undefined?undefined:JSON.stringify(body),
      signal:AbortSignal.any([signal,AbortSignal.timeout(30000)]),cache:'no-store',redirect:'error',credentials:'omit'});
    if(!response.ok)throw new ApiError('leaf_population_request_unavailable',response.status);
    need(response.headers.get('Content-Type')?.split(';')[0]?.trim()==='application/json'&&response.headers.get('Cache-Control')?.split(',').some(v=>v.trim()==='no-store'));
    need(response.body);const reader=response.body.getReader(),chunks:Uint8Array[]=[];let size=0;
    try{while(true){const part=await reader.read();if(part.done)break;size+=part.value.byteLength;need(size<=MAX_BYTES);chunks.push(part.value);}}
    catch(error){await reader.cancel().catch(()=>{});throw error;}finally{reader.releaseLock();}
    const raw=new Uint8Array(size);let offset=0;for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.length;}
    return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)) as unknown;
  }
  function path(id:string){need(uuid(id));return `/v1/jobs/${id}/crop-leaf-population-execution`;}
  async function readStatus(id:string,signal:AbortSignal){const v=decodeLeafPopulationStatus(await request(path(id),signal),id);
    need(v.manifest===null&&v.frame===null&&v.replay===null);return v;}
  return Object.freeze({
    async submit(value:LeafPopulationRequest,signal:AbortSignal){decodeLeafPopulationRequest(value);return job(await request('/v1/crop-leaf-population-executions',signal,'POST',value));},
    status:readStatus,
    async observe(id:string,signal:AbortSignal){const status=await readStatus(id,signal);
      if(!status.result)return {status,replay:null};
      const completed=await decodeLeafPopulationExecutionReplay(await request(path(id)+'/replay',signal),id);
      need(canonical(completed.status.result)===canonical(status.result));return completed;},
    async replay(id:string,signal:AbortSignal){return decodeLeafPopulationExecutionReplay(await request(path(id)+'/replay',signal),id);},
    async cancel(id:string,signal:AbortSignal){const v=shape(await request(path(id)+'/cancel',signal,'POST'),
      ['schema_version',...Object.keys(FLAGS),'observed_at','job','cancel_requested','cancel_accepted']);flags(v);stamp(v.observed_at);
      need(v.schema_version==='leaf-population-execution-cancel-v1'&&typeof v.cancel_requested==='boolean'&&typeof v.cancel_accepted==='boolean');
      return {job:job(v.job,id),cancel_requested:v.cancel_requested,cancel_accepted:v.cancel_accepted};},
    async preview(signal:AbortSignal){const v=shape(await request('/leaf-preview-input',signal),['schema_version',...Object.keys(FLAGS),'label','request']);flags(v);
      need(v.schema_version==='owned-leaf-population-preview-input-v1'&&typeof v.label==='string'&&v.label.length>=1&&v.label.length<=160);
      return {label:v.label,request:decodeLeafPopulationRequest(v.request)};},
  });
}
export type LeafPopulationExecutionClient=ReturnType<typeof createLeafPopulationExecutionClient>;
