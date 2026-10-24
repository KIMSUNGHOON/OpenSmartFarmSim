import {decodeMorphologyFrame,RATIONAL_MORPHOLOGY_SOURCE,sha256,type MorphologyFrame} from './morphologyReplay';
import type {StoredLeafArea} from './leafAreaReplay';
import type {MorphologyLeafArea} from './morphologyGeometry';
import {LEAF_LIFECYCLE_FIXTURE as FIXTURE} from './leafLifecycleReplayFixture';
import {STORED_LEAF_MAX_BYTES as MAX,need,object,closed,digest,id,utc,integer,flags,exact,area,constants,rights,readStoredLeafFile,parse} from './storedLeafReplayIO';

export type LeafLifecycleScenario=keyof typeof FIXTURE.scenarios;
type Seconds=StoredLeafArea['emerged_elapsed_seconds_exact'];
type Removal=Readonly<{schema_version:'declared-whole-leaf-removal-event-v1';origin:'synthetic';action:'remove_whole_leaf';
 event_id:string;leaf_id:string;time_origin_utc:string;at_elapsed_seconds_exact:Seconds}>;
type RemovedLeaf=StoredLeafArea&Readonly<{last_at_elapsed_seconds_exact:Seconds;removal_declaration:Removal}>;
type PendingLeaf=Pick<StoredLeafArea,'leaf_id'|'attachment_internode_id'|'emerged_elapsed_seconds_exact'>;
type Area=StoredLeafArea['area'];
export type LeafLifecycleFrame={schema_version:'leaf-lifecycle-replay-frame-v1';scope:'software_research_only';claim_scope:'synthetic_crop_math_only';
 gates:'not_assessed';artifact_sha256:string;result_sha256:string;input_sha256:string;index:number;at:string;time_origin_utc:string;
 at_elapsed_seconds_exact:Seconds;declared_leaf_count:number;tracked_leaf_count:number;active_leaf_count:number;removed_leaf_count:number;
 scheduled_birth_count:number;emerged_new_leaf_count:number;pending_leaf_count:number;active_leaf_area:Area;removed_leaf_area:Area;last_tracked_leaf_area:Area;
 active_leaves:StoredLeafArea[];removed_leaves:RemovedLeaf[];pending_leaves:PendingLeaf[];stem:MorphologyFrame;
 appearance_program_sha256:string;management_program_sha256:string;preparation_sha256:string;display_policy:typeof FIXTURE.display_policy};
export type LeafLifecycleReplay={scenario:LeafLifecycleScenario;artifact_sha256:string;frames:LeafLifecycleFrame[]};
const REFERENCES=['appearance_program_sha256','management_program_sha256','preparation_sha256','initial_state_sha256','stem_artifact_sha256','stem_program_sha256'] as const;
const SOURCES={'root.json':'artifact_sha256','input.json':'appearance_program_sha256','management.json':'management_program_sha256',
 'preparation.json':'preparation_sha256','initial-state.json':'initial_state_sha256','stem-root.json':'stem_artifact_sha256','stem-input.json':'stem_program_sha256'} as const;
const DESCRIPTOR=['index','at','path','sha256','bytes','result_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256'];
const LEAF=['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact','age_exact','area'];
const COUNTS=['declared_leaf_count','tracked_leaf_count','active_leaf_count','removed_leaf_count','scheduled_birth_count','emerged_new_leaf_count','pending_leaf_count'];
const SUMS=['active_leaf_area','removed_leaf_area','last_tracked_leaf_area'];
const same=(a:unknown,b:unknown)=>JSON.stringify(a)===JSON.stringify(b);
const before=(a:ReturnType<typeof exact>,b:ReturnType<typeof exact>)=>a.n*b.d<=b.n*a.d;

function scenarioSpec(scenario:LeafLifecycleScenario){need(scenario==='no-removal'||scenario==='with-removal');return FIXTURE.scenarios[scenario];}
function sourceRights(value:unknown){const q=closed(value,['appearance','management','stem']);for(const v of Object.values(q))rights(v);return q;}
function codePins(value:unknown,names=Object.keys(FIXTURE.code_sha256)){
 const q=closed(value,names),expected:Record<string,string>=FIXTURE.code_sha256;
 for(const name of names)need(q[name]===expected[name]);
}

function manifest(value:unknown,scenario:LeafLifecycleScenario){
 const spec=scenarioSpec(scenario),m=closed(value,['schema_version','status','scope','claim_scope','gates','time_kind','parameter_scope','model_versions','display_policy',
  'appearance_program_sha256','appearance_program_bytes','management_program_sha256','management_program_bytes','preparation_sha256','preparation_bytes',
  'source_rights','stem_artifact_sha256','stem_program_sha256','code_sha256','time_origin_utc','initial_at_elapsed_seconds_exact','initial_state_sha256','initial_state_bytes','terminal_state_sha256','samples']);
 flags(m);need(m.schema_version==='leaf-lifecycle-research-artifact-v1'&&m.status==='completed_software_fixture'&&
  m.time_kind==='synthetic_model_clock_not_observation'&&m.parameter_scope==='synthetic_software_fixture_only');
 constants(m.model_versions,FIXTURE.model_versions);constants(m.display_policy,FIXTURE.display_policy);codePins(m.code_sha256);sourceRights(m.source_rights);
 for(const key of [...REFERENCES,'terminal_state_sha256'] as const)need(m[key]===spec[key]);
 need(m.time_origin_utc===FIXTURE.time_origin_utc&&same(m.initial_at_elapsed_seconds_exact,FIXTURE.initial_at_elapsed_seconds_exact));
 for(const key of ['appearance_program_bytes','management_program_bytes','preparation_bytes','initial_state_bytes'])integer(m[key],1,MAX);
 need(m.stem_artifact_sha256===RATIONAL_MORPHOLOGY_SOURCE.artifact_sha256&&Array.isArray(m.samples)&&m.samples.length===FIXTURE.frames);
 let previous=m.initial_state_sha256,last=Date.parse(FIXTURE.time_origin_utc);
 for(let i=0;i<m.samples.length;i++){
  const d=closed(m.samples[i],['index','at','result_sha256','result_bytes','input_state_sha256','state_sha256','input_sha256','stem_result_sha256']);
  need(d.index===i&&d.input_state_sha256===previous);utc(d.at);need(Date.parse(d.at)>last);last=Date.parse(d.at);previous=d.state_sha256;
  integer(d.result_bytes,1,MAX);for(const key of ['result_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256'])digest(d[key]);
 }
 need(previous===m.terminal_state_sha256);return m;
}

function areaSum(value:unknown,leaves:Record<string,unknown>[]){
 const q=closed(value,['value','unit']);need(q.unit==='m2'&&typeof q.value==='number'&&Number.isFinite(q.value)&&q.value>=0);
 let sum=0;for(const leaf of leaves)sum+=(object(leaf.area).value as number);
 need(Number.isFinite(sum)&&(leaves.length===0?q.value===0:
  Math.abs(sum-q.value)<=Number.EPSILON*Math.max(sum,q.value)*leaves.length));
}

export function decodeLeafLifecycleFrame(value:unknown,descriptor:unknown,root:unknown,scenario:LeafLifecycleScenario):LeafLifecycleFrame{
 const spec=scenarioSpec(scenario),m=manifest(root,scenario),d=closed(descriptor,DESCRIPTOR);
 integer(d.index,0,FIXTURE.frames-1);utc(d.at);integer(d.bytes,1,MAX);digest(d.sha256);need(d.path===`frame-${d.index}.json`);
 const sample=object((m.samples as unknown[])[d.index]);for(const key of DESCRIPTOR.filter(k=>!['path','sha256','bytes'].includes(k)))need(d[key]===sample[key]);
 const f=closed(value,['schema_version','scope','claim_scope','gates','artifact_sha256','result_sha256','input_sha256','index','at','time_origin_utc',
  'at_elapsed_seconds_exact',...COUNTS,...SUMS,'active_leaves','removed_leaves','pending_leaves','stem','appearance_program_sha256','management_program_sha256','preparation_sha256','display_policy']);
 flags(f);need(f.schema_version==='leaf-lifecycle-replay-frame-v1'&&f.artifact_sha256===spec.artifact_sha256&&f.index===d.index&&f.at===d.at&&
  f.result_sha256===d.result_sha256&&f.input_sha256===d.input_sha256&&f.time_origin_utc===m.time_origin_utc);
 for(const key of ['appearance_program_sha256','management_program_sha256','preparation_sha256'])need(f[key]===m[key]);
 constants(f.display_policy,FIXTURE.display_policy);
 const now=exact(f.at_elapsed_seconds_exact,'s');need(now.n===BigInt((Date.parse(d.at)-Date.parse(FIXTURE.time_origin_utc))/1000)*now.d);
 const stem=decodeMorphologyFrame(f.stem,{index:d.index,at:d.at,path:d.path,sha256:d.sha256,bytes:d.bytes,result_sha256:d.stem_result_sha256 as string},RATIONAL_MORPHOLOGY_SOURCE);
 need(stem.schema_version==='morphology-replay-frame-v2'&&stem.at===f.at&&stem.time_origin_utc===f.time_origin_utc);
 const active:Record<string,unknown>[]=[],removed:Record<string,unknown>[]=[],pending:Record<string,unknown>[]=[];
 need(Array.isArray(f.active_leaves)&&Array.isArray(f.removed_leaves)&&Array.isArray(f.pending_leaves));
 for(const declared of FIXTURE.declared_leaves){
  const birth=exact(declared.emerged_elapsed_seconds_exact,'s');
  if(!before(birth,now)){
   const q=closed(f.pending_leaves[pending.length],['leaf_id','attachment_internode_id','emerged_elapsed_seconds_exact']);
   need(q.leaf_id===declared.leaf_id&&q.attachment_internode_id===declared.attachment_internode_id&&same(q.emerged_elapsed_seconds_exact,declared.emerged_elapsed_seconds_exact));pending.push(q);continue;
  }
  const event=spec.removals.find(q=>q.leaf_id===declared.leaf_id),retired=event!==undefined&&before(exact(event.at_elapsed_seconds_exact,'s'),now);
  const q=closed(retired?f.removed_leaves[removed.length]:f.active_leaves[active.length],retired?[...LEAF,'last_at_elapsed_seconds_exact','removal_declaration']:LEAF);
  for(const key of ['leaf_id','attachment_internode_id','curve_sha256'] as const)need(q[key]===declared[key]);
  need(same(q.emerged_elapsed_seconds_exact,declared.emerged_elapsed_seconds_exact));exact(q.age_exact,'degC_day');area(q.area);
  const parent=stem.internodes.find(n=>n.internode_id===declared.attachment_internode_id);need(parent&&before(exact(parent.emerged_elapsed_seconds_exact,'s'),birth));
  if(retired){
   need(same(q.removal_declaration,event)&&same(q.last_at_elapsed_seconds_exact,event.at_elapsed_seconds_exact));
   const last=exact(q.last_at_elapsed_seconds_exact,'s');need(before(birth,last)&&before(last,now));removed.push(q);
  }else active.push(q);
 }
 need(f.active_leaves.length===active.length&&f.removed_leaves.length===removed.length&&f.pending_leaves.length===pending.length);
 const counts={declared_leaf_count:FIXTURE.declared_leaves.length,tracked_leaf_count:active.length+removed.length,active_leaf_count:active.length,
  removed_leaf_count:removed.length,scheduled_birth_count:FIXTURE.declared_leaves.length-FIXTURE.initial_leaves,
  emerged_new_leaf_count:active.length+removed.length-FIXTURE.initial_leaves,pending_leaf_count:pending.length};
 for(const [key,count]of Object.entries(counts)){integer(f[key],0,512);need(f[key]===count);}
 areaSum(f.active_leaf_area,active);areaSum(f.removed_leaf_area,removed);areaSum(f.last_tracked_leaf_area,[...active,...removed]);
 return {...f,stem} as LeafLifecycleFrame;
}

function evidence(documents:Record<string,unknown>,m:Record<string,unknown>,scenario:LeafLifecycleScenario){
 const spec=scenarioSpec(scenario),grants=sourceRights(m.source_rights);
 const input=closed(documents['input.json'],['schema_version','origin','program_id','rights','stem','initialization','policy','leaf_profile','display_policy']);
 need(input.schema_version==='leaf-appearance-software-program-v1'&&input.origin==='synthetic');id(input.program_id);rights(input.rights);need(same(input.rights,grants.appearance));
 const parent=closed(input.stem,['artifact_sha256','program_sha256']);need(parent.artifact_sha256===m.stem_artifact_sha256&&parent.program_sha256===m.stem_program_sha256);
 const management=closed(documents['management.json'],['schema_version','origin','program_id','rights','appearance_program_sha256','removals','display_policy']);
 need(management.schema_version==='leaf-lifecycle-management-program-v1'&&management.origin==='synthetic'&&management.appearance_program_sha256===m.appearance_program_sha256);
 id(management.program_id);rights(management.rights);need(same(management.rights,grants.management)&&same(management.removals,spec.removals));constants(management.display_policy,FIXTURE.display_policy);
 const p=closed(documents['preparation.json'],['model_version','scope','claim_scope','gates','model_versions','input_sha256','appearance_program_sha256','appearance_program_bytes',
  'management_program_sha256','management_program_bytes','management_program_id','appearance_preparation_sha256','appearance_preparation','lifecycle_initialization',
  'lifecycle_initialization_sha256','initial_state_sha256','stem','time_origin_utc','start_elapsed_seconds_exact','end_elapsed_seconds_exact','forcing','source_rights','display_policy','code_sha256']);
 flags(p);need(p.model_version===FIXTURE.model_versions.preparation&&p.management_program_id===management.program_id);
 constants(p.model_versions,Object.fromEntries(Object.entries(FIXTURE.model_versions).filter(([name])=>name!=='producer')));
 codePins(p.code_sha256,Object.keys(FIXTURE.code_sha256).filter(name=>!name.includes('crop_leaf_lifecycle_artifact_')));
 for(const key of ['appearance_program_sha256','appearance_program_bytes','management_program_sha256','management_program_bytes','initial_state_sha256','time_origin_utc'])need(p[key]===m[key]);
 need(same(p.source_rights,m.source_rights)&&same(p.stem,input.stem));constants(p.display_policy,FIXTURE.display_policy);
 for(const key of ['input_sha256','appearance_preparation_sha256','lifecycle_initialization_sha256'])digest(p[key]);
 const initial=closed(documents['initial-state.json'],['model_version','existing_inventory_state','birth_declarations','birth_declarations_sha256','removal_declarations','removal_declarations_sha256','new_leaf_checkpoints']);
 need(initial.model_version===FIXTURE.model_versions.lifecycle&&same(initial.removal_declarations,management.removals));
 const inputs=closed(p.lifecycle_initialization,['input_id','population_state','births','removals']);id(inputs.input_id);
 need(same(inputs.births,initial.birth_declarations)&&same(inputs.removals,management.removals)&&same(inputs.population_state,object(initial.existing_inventory_state).source_population));
 const old=object(p.appearance_preparation);flags(old);need(old.source_program_sha256===m.appearance_program_sha256&&old.source_program_bytes===m.appearance_program_bytes);
 const stem=object(documents['stem-root.json']),stemInput=object(documents['stem-input.json']);flags(stem);rights(stem.program_rights);rights(stemInput.rights);
 need(stem.schema_version==='morphology-research-artifact-v2'&&stem.program_sha256===m.stem_program_sha256&&same(stem.program_rights,grants.stem)&&same(stemInput.rights,grants.stem));
}

export async function loadLeafLifecycleReplay(scenario:LeafLifecycleScenario,signal:AbortSignal):Promise<LeafLifecycleReplay>{
 const spec=scenarioSpec(scenario),directory=`./leaf-lifecycle-replay/${scenario}/`;
 const checked=async(name:string,expected:unknown,bytes?:unknown)=>{
  signal.throwIfAborted();digest(expected);const raw=await readStoredLeafFile(directory,name,signal);signal.throwIfAborted();
  need(await sha256(raw)===expected);if(bytes!==undefined){integer(bytes,1,MAX);need(raw.length===bytes);}signal.throwIfAborted();return raw;
 };
 const index=closed(parse(await checked('index.json',spec.index_sha256)),['schema_version','scope','claim_scope','gates','time_kind','parameter_scope','model_versions','display_policy',
  'artifact_sha256',...REFERENCES,'source_rights','sources','frames']);flags(index);
 need(index.schema_version==='leaf-lifecycle-public-fixture-v1'&&index.artifact_sha256===spec.artifact_sha256&&
  index.time_kind==='synthetic_model_clock_not_observation'&&index.parameter_scope==='synthetic_software_fixture_only');
 constants(index.model_versions,FIXTURE.model_versions);constants(index.display_policy,FIXTURE.display_policy);sourceRights(index.source_rights);
 for(const key of REFERENCES)need(index[key]===spec[key]);
 need(Array.isArray(index.sources)&&index.sources.length===Object.keys(SOURCES).length);const documents:Record<string,unknown>={};
 for(const [i,[name,field]]of Object.entries(SOURCES).entries()){
  const d=closed(index.sources[i],['path','sha256','bytes']);need(d.path===name&&d.sha256===index[field]);
  documents[name]=parse(await checked(name,d.sha256,d.bytes));
 }
 const root=manifest(documents['root.json'],scenario);need(same(index.source_rights,root.source_rights));
 for(const [name,field]of Object.entries(SOURCES)){
  const sizeKey=field.replace('_sha256','_bytes');
  if(Object.hasOwn(root,sizeKey)){const d=object(index.sources.find(raw=>object(raw).path===name));need(d.bytes===root[sizeKey]);}
 }
 evidence(documents,root,scenario);need(Array.isArray(index.frames)&&index.frames.length===FIXTURE.frames);const frames:LeafLifecycleFrame[]=[];
 for(let i=0;i<index.frames.length;i++){
  const d=closed(index.frames[i],DESCRIPTOR);need(d.index===i&&d.path===`frame-${i}.json`);
  frames.push(decodeLeafLifecycleFrame(parse(await checked(`frame-${i}.json`,d.sha256,d.bytes)),d,root,scenario));
 }
 signal.throwIfAborted();return {scenario,artifact_sha256:spec.artifact_sha256,frames};
}

export function activeLifecycleLeafBinding(frame:LeafLifecycleFrame):{artifact_sha256:string;result_sha256:string;at:string;leaves:MorphologyLeafArea[]}{
 return {artifact_sha256:frame.artifact_sha256,result_sha256:frame.result_sha256,at:frame.at,
  leaves:frame.active_leaves.map(q=>({leaf_id:q.leaf_id,attachment_internode_id:q.attachment_internode_id,area:{...q.area}}))};
}
