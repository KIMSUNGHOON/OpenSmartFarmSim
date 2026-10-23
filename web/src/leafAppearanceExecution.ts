import {ApiError,need,object,closed,date,uuid} from './api-validation';
import {decodeMorphologyFrame,sha256,type MorphologyReplaySource} from './morphologyReplay';
import type {LeafAppearanceFrame} from './leafAppearanceReplay';
import {area,exact,constants,integer,utc} from './storedLeafReplayIO';
import type {MorphologyJob} from './morphologyExecution';

const FLAGS={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'} as const;
const STATES=['queued','simulating','succeeded','hold','failed','canceled'] as const;
const SUMMARY_KEYS=['result_sha256','numerical_root_sha256','calculated_at','parent_job_id','parent_result_sha256',
  'parent_numerical_root_sha256','parent_calculated_at','normalization','study_id','revision','farm','profile_applicability',
  'binding_sha256','program_sha256','source_sha256','input_evidence_sha256'] as const;
const MAX_BYTES=2*1024**2;
type Farm={scenario_id:string;scenario_revision:string;registration_sha256:string;crop_id:string};
export type LeafAppearanceJob=MorphologyJob;
export type LeafAppearanceRequest={study_id:string;revision:string;farm:Farm;
  parent:{job_id:string;result_sha256:string;numerical_root_sha256:string};
  input:{schema_version:'leaf-appearance-input-source-v1';program_id:string;program_sha256:string;source_sha256:string;evidence_sha256:string};
  rights:{schema_version:'leaf-appearance-input-rights-v1';declaration_id:string;revision:string;input_source_sha256:string;
    available_at:string;redistribute:false;ownership_asserted:true;access:true;store:true;transform:true;use:true;display:true}};
export type LeafAppearanceResult={result_sha256:string;numerical_root_sha256:string;calculated_at:string;
  parent_job_id:string;parent_result_sha256:string;parent_numerical_root_sha256:string;parent_calculated_at:string;
  normalization:'per_tracked_shoot';study_id:string;revision:string;farm:Farm;profile_applicability:'unvalidated_for_registered_crop';
  binding_sha256:string;program_sha256:string;source_sha256:string;input_evidence_sha256:string};
export type LeafAppearanceStatus={schema_version:'leaf-appearance-execution-read-v1';observed_at:string;job:LeafAppearanceJob;
  cancel_requested:boolean;result:LeafAppearanceResult|null;manifest:unknown;frame:unknown;replay:unknown}&typeof FLAGS;

function record(value:unknown){need(object(value));return value;}
function shape(value:unknown,keys:readonly string[]){const v=record(value);closed(v,keys);return v;}
function digest(value:unknown):asserts value is string{need(typeof value==='string'&&/^[0-9a-f]{64}$/.test(value));}
function name(value:unknown):asserts value is string{need(typeof value==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value));}
function stamp(value:unknown):asserts value is string{need(date(value)&&value.endsWith('Z'));}
function flags(value:Record<string,unknown>){for(const [k,v]of Object.entries(FLAGS))need(value[k]===v);}
function farm(value:unknown){const v=shape(value,['scenario_id','scenario_revision','registration_sha256','crop_id']);
  name(v.scenario_id);name(v.scenario_revision);name(v.crop_id);digest(v.registration_sha256);return v as Farm;}
function job(value:unknown,id?:string):LeafAppearanceJob{
  const v=shape(value,['job_id','stage','state','attempt_count','max_attempts','created_at','updated_at','reason_code']);
  need(uuid(v.job_id)&&(!id||v.job_id===id)&&v.stage==='simulation'&&STATES.some(s=>s===v.state));
  integer(v.max_attempts,1,3);integer(v.attempt_count,0,v.max_attempts);need(date(v.created_at)&&date(v.updated_at));
  need(v.reason_code===null||typeof v.reason_code==='string'&&/^[a-z][a-z0-9_]{0,63}$/.test(v.reason_code));
  return v as LeafAppearanceJob;
}
function result(value:unknown):LeafAppearanceResult{
  const v=shape(value,SUMMARY_KEYS);
  for(const k of ['result_sha256','numerical_root_sha256','parent_result_sha256','parent_numerical_root_sha256',
    'binding_sha256','program_sha256','source_sha256','input_evidence_sha256'])digest(v[k]);
  stamp(v.calculated_at);stamp(v.parent_calculated_at);need(uuid(v.parent_job_id));
  need(v.normalization==='per_tracked_shoot'&&v.profile_applicability==='unvalidated_for_registered_crop');
  name(v.study_id);name(v.revision);farm(v.farm);return v as LeafAppearanceResult;
}
export function decodeLeafAppearanceRequest(value:unknown):LeafAppearanceRequest{
  const v=shape(value,['study_id','revision','farm','parent','input','rights']);name(v.study_id);name(v.revision);farm(v.farm);
  const p=shape(v.parent,['job_id','result_sha256','numerical_root_sha256']);need(uuid(p.job_id));digest(p.result_sha256);digest(p.numerical_root_sha256);
  const i=shape(v.input,['schema_version','program_id','program_sha256','source_sha256','evidence_sha256']);
  need(i.schema_version==='leaf-appearance-input-source-v1');name(i.program_id);for(const k of ['program_sha256','source_sha256','evidence_sha256'])digest(i[k]);
  const r=shape(v.rights,['schema_version','declaration_id','revision','input_source_sha256','available_at','redistribute',
    'ownership_asserted','access','store','transform','use','display']);
  need(r.schema_version==='leaf-appearance-input-rights-v1'&&r.redistribute===false&&r.input_source_sha256===i.source_sha256);
  stamp(r.available_at);name(r.declaration_id);name(r.revision);for(const k of ['ownership_asserted','access','store','transform','use','display'])need(r[k]===true);
  return v as LeafAppearanceRequest;
}
export function decodeLeafAppearanceStatus(value:unknown,id:string):LeafAppearanceStatus{
  const v=shape(value,['schema_version',...Object.keys(FLAGS),'observed_at','job','cancel_requested','result','manifest','frame','replay']);
  flags(v);need(v.schema_version==='leaf-appearance-execution-read-v1'&&typeof v.cancel_requested==='boolean');stamp(v.observed_at);
  const j=job(v.job,id);if(v.result!==null){const r=result(v.result);need(r.parent_job_id!==j.job_id);}
  need((j.state==='succeeded')===(v.result!==null));
  if(v.result===null)need(v.manifest===null&&v.frame===null&&v.replay===null);
  else need(v.cancel_requested===false&&j.attempt_count>=1);
  need([v.manifest,v.frame,v.replay].every(q=>q===null||object(q))&&[v.manifest,v.frame,v.replay].filter(q=>q!==null).length<=1);
  return v as LeafAppearanceStatus;
}
function canonical(value:unknown):string{
  if(value===null||typeof value==='string'||typeof value==='boolean')return JSON.stringify(value);
  if(typeof value==='number'){need(Number.isSafeInteger(value));return JSON.stringify(value);}
  if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
  const v=record(value);return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(v[k])).join(',')+'}';
}

export type LeafAppearanceExecutionReplay={artifact_sha256:string;frames:LeafAppearanceFrame[]};
const MODELS={air_adapter:'whole-second-utc-to-rational-air-segments-research-v1',
 appearance_producer:'leaf-appearance-artifact-producer-research-v1',birth_inputs:'stored-shoot-leaf-birth-inputs-research-v1',
 declared_births:'declared-leaf-births-research-v1',kind:'phytomer-kind-research-v1',leaf:'leaf-rational-air-area-state-research-v1',
 population:'declared-leaf-population-research-v1',population_producer:'leaf-population-artifact-producer-research-v1',
 preparation:'leaf-appearance-program-preparation-research-v1',stem:'morphology-research-artifact-v2',timeline:'shoot-air-phytomer-timeline-research-v1'};
const DISPLAY={version:'stored-leaf-m2-authored-blade-triangles-v1',surface:'one_sided_authored_leaflet_triangles',
 petiole_rachis_area_excluded:true,placement:'declared_attachment_upper_end_authored_angles_v1',
 length_width_shape:'authored_uniform_scale_not_cultivar_prediction',leaf_count:'computed_from_explicit_phytomer_policy_v1'} as const;
type RuntimeRoot=Record<string,unknown>&{sample_count:number;time_origin_utc:string;source_program_sha256:string;
 preparation_sha256:string;population_artifact_sha256:string;stem_artifact_sha256:string};

function rootManifest(value:unknown):RuntimeRoot{
 const m=shape(value,['schema_version','status',...Object.keys(FLAGS),'time_kind','parameter_scope','model_versions','display_policy',
  'source_program_sha256','source_program_bytes','preparation_sha256','preparation_bytes','generated_program_sha256','generated_program_bytes',
  'population_artifact_sha256','stem_artifact_sha256','stem_program_sha256','program_rights','code_sha256','time_origin_utc',
  'initial_at_elapsed_seconds_exact','initial_state_sha256','terminal_state_sha256','sample_count']);flags(m);
 need(m.schema_version==='leaf-appearance-research-artifact-v1'&&m.status==='completed_software_fixture'&&
  m.time_kind==='synthetic_model_clock_not_observation'&&m.parameter_scope==='synthetic_software_fixture_only');
 constants(m.model_versions,MODELS);constants(m.display_policy,DISPLAY);utc(m.time_origin_utc);
 for(const k of ['source_program_sha256','preparation_sha256','generated_program_sha256','population_artifact_sha256',
  'stem_artifact_sha256','stem_program_sha256','initial_state_sha256','terminal_state_sha256'])digest(m[k]);
 for(const k of ['source_program_bytes','preparation_bytes','generated_program_bytes'])integer(m[k],1,MAX_BYTES);
 integer(m.sample_count,1,64);exact(m.initial_at_elapsed_seconds_exact,'s');
 const rights=shape(m.program_rights,['access','declaration_id','declared_at_utc','display','ownership_asserted','redistribute','revision','store','transform','use']);
 for(const k of ['access','display','ownership_asserted','store','transform','use'])need(rights[k]===true);
 need(typeof rights.redistribute==='boolean');name(rights.declaration_id);name(rights.revision);utc(rights.declared_at_utc);
 const codes=record(m.code_sha256);need(Object.keys(codes).length===33);
 for(const [key,value]of Object.entries(codes)){need(/^backend\/app\/[a-z_]+\.py$/.test(key));digest(value);}
 return m as RuntimeRoot;
}
async function signedManifest(value:unknown,summary:LeafAppearanceResult):Promise<RuntimeRoot>{
 const v=shape(value,['schema_version',...Object.keys(FLAGS),...SUMMARY_KEYS,'manifest']);flags(v);
 need(v.schema_version==='leaf-appearance-signed-manifest-v1');
 for(const key of SUMMARY_KEYS)need(canonical(v[key])===canonical(summary[key]));
 const root=rootManifest(v.manifest);need(root.source_program_sha256===summary.program_sha256&&root.stem_artifact_sha256===summary.parent_numerical_root_sha256);
 need(await sha256(new TextEncoder().encode(canonical(root)))===summary.numerical_root_sha256);return root;
}
function sumAgrees(values:number[],total:number){
 const sum=values.reduce((a,b)=>a+b,0);need(Number.isFinite(sum)&&Math.abs(sum-total)<=Number.EPSILON*(values.length+1)*Math.max(sum,total));
}
function decodeFrame(value:unknown,root:RuntimeRoot,summary:LeafAppearanceResult,index:number):LeafAppearanceFrame{
 const f=shape(value,['schema_version',...Object.keys(FLAGS),'artifact_sha256','result_sha256','binding_sha256','input_sha256',
  'index','at','time_origin_utc','tracked_leaf_count','tracked_leaf_area','leaves','stem','population_artifact_sha256',
  'source_program_sha256','preparation_sha256','policy_sha256','leaf_profile_sha256','display_policy']);flags(f);
 need(f.schema_version==='leaf-appearance-replay-frame-v1'&&f.artifact_sha256===summary.numerical_root_sha256&&f.index===index&&
  f.time_origin_utc===root.time_origin_utc&&f.population_artifact_sha256===root.population_artifact_sha256&&
  f.source_program_sha256===root.source_program_sha256&&f.preparation_sha256===root.preparation_sha256);
 for(const k of ['result_sha256','binding_sha256','input_sha256','policy_sha256','leaf_profile_sha256'])digest(f[k]);
 utc(f.at);integer(f.tracked_leaf_count,1,512);area(f.tracked_leaf_area);constants(f.display_policy,DISPLAY);
 const initial=exact(root.initial_at_elapsed_seconds_exact,'s');
 const elapsed=BigInt((Date.parse(f.at)-Date.parse(root.time_origin_utc))/1000);need(elapsed*initial.d>initial.n);
 const stemRaw=record(f.stem);digest(stemRaw.result_sha256);
 const source:MorphologyReplaySource={version:'v2',directory:'./morphology-rational-replay',artifact_sha256:root.stem_artifact_sha256,index_sha256:'0'.repeat(64),frames:root.sample_count};
 const stem=decodeMorphologyFrame(f.stem,{index,at:f.at,path:'',sha256:'0'.repeat(64),bytes:1,result_sha256:stemRaw.result_sha256},source);
 need(stem.schema_version==='morphology-replay-frame-v2'&&stem.time_origin_utc===f.time_origin_utc);
 need(Array.isArray(f.leaves)&&f.leaves.length===f.tracked_leaf_count);const ids=new Set<string>();
 for(const raw of f.leaves){
  const leaf=shape(raw,['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact','age_exact','area']);
  name(leaf.leaf_id);name(leaf.attachment_internode_id);digest(leaf.curve_sha256);need(!ids.has(leaf.leaf_id));ids.add(leaf.leaf_id);
  const birth=exact(leaf.emerged_elapsed_seconds_exact,'s');need(birth.n<=elapsed*birth.d);exact(leaf.age_exact,'degC_day');area(leaf.area);
  const parent=stem.internodes.find(q=>q.internode_id===leaf.attachment_internode_id);need(parent);
  const parentBirth=exact(parent.emerged_elapsed_seconds_exact,'s');need(parentBirth.n*birth.d<=birth.n*parentBirth.d);
 }
 const frame={...f,stem} as LeafAppearanceFrame;
 sumAgrees(frame.leaves.map(q=>q.area.value),frame.tracked_leaf_area.value);sumAgrees(stem.internodes.map(q=>q.length.value),stem.tracked_axis_length.value);return frame;
}
function sequence(frames:LeafAppearanceFrame[]){
 for(let index=1;index<frames.length;index++){
  const a=frames[index-1]!,b=frames[index]!;
  need(b.at>a.at&&a.stem.shoot_id===b.stem.shoot_id&&a.policy_sha256===b.policy_sha256&&a.leaf_profile_sha256===b.leaf_profile_sha256&&
   b.leaves.length>=a.leaves.length&&b.stem.internodes.length>=a.stem.internodes.length);
  for(let i=0;i<a.leaves.length;i++){
   const old=a.leaves[i]!,next=b.leaves[i]!;need(old.leaf_id===next.leaf_id&&old.attachment_internode_id===next.attachment_internode_id&&
    old.curve_sha256===next.curve_sha256&&canonical(old.emerged_elapsed_seconds_exact)===canonical(next.emerged_elapsed_seconds_exact));
  }
  const previous=BigInt((Date.parse(a.at)-Date.parse(a.time_origin_utc))/1000);
  for(const leaf of b.leaves.slice(a.leaves.length)){const birth=exact(leaf.emerged_elapsed_seconds_exact,'s');need(birth.n>previous*birth.d);}
  for(let i=0;i<a.stem.internodes.length;i++){
   const old=a.stem.internodes[i]!,next=b.stem.internodes[i]!;need(old.sequence===next.sequence&&old.internode_id===next.internode_id&&
    'emerged_elapsed_seconds_exact' in old&&'emerged_elapsed_seconds_exact' in next&&canonical(old.emerged_elapsed_seconds_exact)===canonical(next.emerged_elapsed_seconds_exact));
  }
 }
}
export async function decodeLeafAppearanceExecutionReplay(value:unknown,id:string):Promise<{status:LeafAppearanceStatus;replay:LeafAppearanceExecutionReplay}>{
 const status=decodeLeafAppearanceStatus(value,id);need(status.result&&status.manifest===null&&status.frame===null);
 const body=shape(status.replay,['manifest','frames']),root=await signedManifest(body.manifest,status.result);
 need(Array.isArray(body.frames)&&body.frames.length===root.sample_count);
 const frames=body.frames.map((f,index)=>decodeFrame(f,root,status.result!,index));sequence(frames);
 return {status,replay:{artifact_sha256:status.result.numerical_root_sha256,frames}};
}

export function createLeafAppearanceExecutionClient(token:string){
 need(/^[A-Za-z0-9_-]{32,128}$/.test(token));
 async function request(path:string,signal:AbortSignal,method='GET',body?:unknown,expected=200){
  signal.throwIfAborted();const headers:Record<string,string>={Authorization:'Bearer '+token};if(body!==undefined)headers['Content-Type']='application/json';
  const response=await fetch(path,{method,headers,body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.any([signal,AbortSignal.timeout(30000)]),cache:'no-store',redirect:'error',credentials:'omit'});
  if(!response.ok){await response.body?.cancel().catch(()=>{});throw new ApiError('leaf_appearance_request_unavailable',response.status);}
  const accepted=response.status===expected&&response.headers.get('Content-Type')?.split(';')[0]?.trim()==='application/json'&&response.headers.get('Cache-Control')?.split(',').some(v=>v.trim()==='no-store');
  if(!accepted){await response.body?.cancel().catch(()=>{});need(false);}
  need(response.body);const reader=response.body.getReader(),chunks:Uint8Array[]=[];let size=0;
  try{while(true){const q=await reader.read();if(q.done)break;size+=q.value.byteLength;need(size<=MAX_BYTES);chunks.push(q.value);}}
  catch(error){await reader.cancel().catch(()=>{});throw error;}finally{reader.releaseLock();}
  signal.throwIfAborted();const raw=new Uint8Array(size);let offset=0;for(const q of chunks){raw.set(q,offset);offset+=q.byteLength;}
  return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)) as unknown;
 }
 function path(id:string){need(uuid(id));return `/v1/jobs/${id}/crop-leaf-appearance-execution`;}
 async function readStatus(id:string,signal:AbortSignal){const status=decodeLeafAppearanceStatus(await request(path(id),signal),id);need(status.manifest===null&&status.frame===null&&status.replay===null);return status;}
 async function readManifest(id:string,signal:AbortSignal){
  const status=decodeLeafAppearanceStatus(await request(path(id)+'/manifest',signal),id);need(status.result&&status.frame===null&&status.replay===null);
  const root=await signedManifest(status.manifest,status.result);signal.throwIfAborted();return {status,root};
 }
 return Object.freeze({
  async submit(value:LeafAppearanceRequest,signal:AbortSignal){decodeLeafAppearanceRequest(value);const row=job(await request('/v1/crop-leaf-appearance-executions',signal,'POST',value,202));need(row.job_id!==value.parent.job_id);return row;},
  status:readStatus,manifest:readManifest,
  async frame(id:string,index:number,signal:AbortSignal){
   integer(index,0,63);const first=await readManifest(id,signal);need(index<first.root.sample_count);
   const status=decodeLeafAppearanceStatus(await request(path(id)+`/frames/${index}`,signal),id);need(status.result&&status.manifest===null&&status.replay===null&&canonical(status.result)===canonical(first.status.result));
   const signed=shape(status.frame,['schema_version',...Object.keys(FLAGS),...SUMMARY_KEYS,'frame','frame_sha256']);flags(signed);need(signed.schema_version==='leaf-appearance-signed-frame-v1');digest(signed.frame_sha256);
   for(const key of SUMMARY_KEYS)need(canonical(signed[key])===canonical(status.result[key]));
   return {status,frame:decodeFrame(signed.frame,first.root,status.result,index),frame_sha256:signed.frame_sha256};
  },
  async replay(id:string,signal:AbortSignal){const value=await decodeLeafAppearanceExecutionReplay(await request(path(id)+'/replay',signal),id);signal.throwIfAborted();return value;},
  async observe(id:string,signal:AbortSignal){
   const status=await readStatus(id,signal);if(!status.result)return {status,replay:null};
   const completed=await decodeLeafAppearanceExecutionReplay(await request(path(id)+'/replay',signal),id);
   need(canonical(completed.status.result)===canonical(status.result));signal.throwIfAborted();return completed;
  },
  async cancel(id:string,signal:AbortSignal){
   const value=shape(await request(path(id)+'/cancel',signal,'POST'),['schema_version',...Object.keys(FLAGS),'observed_at','job','cancel_requested','cancel_accepted']);flags(value);stamp(value.observed_at);
   need(value.schema_version==='leaf-appearance-execution-cancel-v1'&&typeof value.cancel_requested==='boolean'&&typeof value.cancel_accepted==='boolean'&&(!value.cancel_accepted||value.cancel_requested));
   return {job:job(value.job,id),cancel_requested:value.cancel_requested,cancel_accepted:value.cancel_accepted};
  },
  async preview(signal:AbortSignal){
   const value=shape(await request('/leaf-appearance-preview-input',signal),['schema_version',...Object.keys(FLAGS),'label','request']);flags(value);
   need(value.schema_version==='owned-leaf-appearance-preview-input-v1'&&typeof value.label==='string'&&value.label.length>=1&&value.label.length<=160);
   return {label:value.label,request:decodeLeafAppearanceRequest(value.request)};
  },
 });
}
export type LeafAppearanceExecutionClient=ReturnType<typeof createLeafAppearanceExecutionClient>;
