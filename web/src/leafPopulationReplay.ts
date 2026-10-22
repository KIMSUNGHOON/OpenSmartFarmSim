import {decodeMorphologyFrame,RATIONAL_MORPHOLOGY_SOURCE,sha256} from './morphologyReplay';
import type {LeafAreaFrame} from './leafAreaReplay';
import {LEAF_POPULATION_FIXTURE} from './leafPopulationReplayFixture';
import {STORED_LEAF_MAX_BYTES as MAX,need,object,closed,digest,utc,integer,flags,exact,area,constants,rights,readStoredLeafFile,parse} from './storedLeafReplayIO';

export type LeafPopulationFrame=Omit<LeafAreaFrame,'schema_version'>&{schema_version:'leaf-population-replay-frame-v1';binding_sha256:string};
export type LeafPopulationReplay={artifact_sha256:string;frames:LeafPopulationFrame[]};
const DIRECTORY='./leaf-population-replay/';
const MODELS={rate:'leaf-logistic-thermal-area-rate-research-v1',change:'leaf-logistic-area-change-research-v1',
 point:'leaf-logistic-canonical-area-point-research-v1',area:'leaf-logistic-canonical-area-state-research-v1',
 clock:'leaf-rational-air-thermal-clock-research-v1',leaf_state:'leaf-rational-air-area-state-research-v1',inventory:'declared-leaf-inventory-research-v1',
 births:'declared-leaf-births-research-v1',population:'declared-leaf-population-research-v1',
 binding:'stored-leaf-stem-attachment-binding-research-v1',producer:'leaf-population-artifact-producer-research-v1'};
const DISPLAY={version:'stored-leaf-m2-authored-blade-triangles-v1',surface:'one_sided_authored_leaflet_triangles',
 petiole_rachis_area_excluded:true,placement:'declared_attachment_upper_end_authored_angles_v1',
 length_width_shape:'authored_uniform_scale_not_cultivar_prediction',leaf_count:'declared_initial_and_births_only'};

function manifest(value:unknown){
 const m=closed(value,['schema_version','status','scope','claim_scope','gates','time_kind','parameter_scope','model_versions','display_policy',
  'program_sha256','program_bytes','program_rights','stem_artifact_sha256','stem_program_sha256','code_sha256','time_origin_utc',
  'initial_at_elapsed_seconds_exact','initial_state_sha256','terminal_state_sha256','samples']);flags(m);
 need(m.schema_version==='leaf-population-research-artifact-v1'&&m.status==='completed_software_fixture'&&
  m.time_kind==='synthetic_model_clock_not_observation'&&m.parameter_scope==='synthetic_software_fixture_only');
 constants(m.model_versions,MODELS);constants(m.display_policy,DISPLAY);rights(m.program_rights);utc(m.time_origin_utc);
 for(const k of ['program_sha256','stem_artifact_sha256','stem_program_sha256','initial_state_sha256','terminal_state_sha256'])digest(m[k]);
 need(m.stem_artifact_sha256===RATIONAL_MORPHOLOGY_SOURCE.artifact_sha256);integer(m.program_bytes,1,MAX);exact(m.initial_at_elapsed_seconds_exact,'s');
 const codes=object(m.code_sha256);need(Object.keys(codes).length===28);
 for(const [name,value]of Object.entries(codes)){need(/^backend\/app\/[a-z_]+\.py$/.test(name));digest(value);}
 need(Array.isArray(m.samples)&&m.samples.length===LEAF_POPULATION_FIXTURE.frames);let previous=m.initial_state_sha256,last=Date.parse(m.time_origin_utc);
 for(let i=0;i<m.samples.length;i++){
  const d=closed(m.samples[i],['index','at','result_sha256','result_bytes','binding_sha256','binding_bytes','input_state_sha256','state_sha256','input_sha256','stem_result_sha256']);
  need(d.index===i);utc(d.at);need(Date.parse(d.at)>last&&d.input_state_sha256===previous);last=Date.parse(d.at);previous=d.state_sha256;
  for(const key of ['result_bytes','binding_bytes'])integer(d[key],1,MAX);
  for(const key of ['result_sha256','binding_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256'])digest(d[key]);
 }
 need(previous===m.terminal_state_sha256);return m;
}

export function decodeLeafPopulationFrame(value:unknown,descriptor:unknown,root:unknown):LeafPopulationFrame{
 const m=manifest(root),d=closed(descriptor,['index','at','path','sha256','bytes','result_sha256','binding_sha256','stem_result_sha256']);
 integer(d.index,0,LEAF_POPULATION_FIXTURE.frames-1);utc(d.at);integer(d.bytes,1,MAX);
 digest(d.sha256);digest(d.result_sha256);digest(d.binding_sha256);digest(d.stem_result_sha256);
 need(d.path===`frame-${d.index}.json`);const sample=object((m.samples as unknown[])[d.index]);
 need(sample.index===d.index&&sample.at===d.at&&sample.result_sha256===d.result_sha256&&sample.binding_sha256===d.binding_sha256&&sample.stem_result_sha256===d.stem_result_sha256);
 const f=closed(value,['schema_version','scope','claim_scope','gates','artifact_sha256','result_sha256','binding_sha256','input_sha256',
  'index','at','time_origin_utc','tracked_leaf_count','tracked_leaf_area','leaves','stem']);flags(f);
 need(f.schema_version==='leaf-population-replay-frame-v1'&&f.artifact_sha256===LEAF_POPULATION_FIXTURE.artifact_sha256&&
  f.index===d.index&&f.at===d.at&&f.result_sha256===d.result_sha256&&f.binding_sha256===d.binding_sha256&&
  f.input_sha256===sample.input_sha256&&f.time_origin_utc===m.time_origin_utc);digest(f.input_sha256);area(f.tracked_leaf_area);integer(f.tracked_leaf_count,1,512);
 const stem=decodeMorphologyFrame(f.stem,{index:d.index,at:d.at,path:d.path,sha256:d.sha256,bytes:d.bytes,result_sha256:d.stem_result_sha256},RATIONAL_MORPHOLOGY_SOURCE);
 need(stem.schema_version==='morphology-replay-frame-v2'&&stem.at===f.at&&stem.time_origin_utc===f.time_origin_utc);
 const elapsed=BigInt((Date.parse(d.at)-Date.parse(stem.time_origin_utc))/1000);
 const declarations=LEAF_POPULATION_FIXTURE.declared_leaves.filter(q=>{const b=exact(q.emerged_elapsed_seconds_exact,'s');return b.n<=elapsed*b.d;});
 need(Array.isArray(f.leaves)&&f.leaves.length===declarations.length&&f.tracked_leaf_count===declarations.length);
 for(let i=0;i<f.leaves.length;i++){
  const q=closed(f.leaves[i],['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact','age_exact','area']),declared=declarations[i]!;
  need(q.leaf_id===declared.leaf_id&&q.attachment_internode_id===declared.attachment_internode_id&&q.curve_sha256===declared.curve_sha256);
  const birth=exact(q.emerged_elapsed_seconds_exact,'s'),original=exact(declared.emerged_elapsed_seconds_exact,'s');
  need(birth.n===original.n&&birth.d===original.d&&birth.n<=elapsed*birth.d);exact(q.age_exact,'degC_day');area(q.area);
  const parent=stem.internodes.find(node=>node.internode_id===q.attachment_internode_id);need(parent);
  const parentBirth=exact(parent.emerged_elapsed_seconds_exact,'s');need(parentBirth.n*birth.d<=birth.n*parentBirth.d);
 }
 return {...f,stem} as LeafPopulationFrame;
}

export async function loadLeafPopulationReplay(signal:AbortSignal):Promise<LeafPopulationReplay>{
 const read=(name:string)=>readStoredLeafFile(DIRECTORY,name,signal),raw=await read('index.json');
 need(await sha256(raw)===LEAF_POPULATION_FIXTURE.index_sha256);
 const index=closed(parse(raw),['schema_version','scope','claim_scope','gates','model_versions','display_policy','artifact_sha256','program_sha256','stem_artifact_sha256','rights','stem_rights','frames']);
 flags(index);need(index.schema_version==='leaf-population-public-fixture-v1'&&index.artifact_sha256===LEAF_POPULATION_FIXTURE.artifact_sha256);
 constants(index.model_versions,MODELS);constants(index.display_policy,DISPLAY);rights(index.rights);rights(index.stem_rights);
 const rootRaw=await read('root.json');need(await sha256(rootRaw)===LEAF_POPULATION_FIXTURE.artifact_sha256);const root=manifest(parse(rootRaw));
 need(index.program_sha256===root.program_sha256&&index.stem_artifact_sha256===root.stem_artifact_sha256);
 const input=await read('input.json'),stemRoot=await read('stem-root.json'),stemInput=await read('stem-input.json');
 need(input.length===root.program_bytes&&await sha256(input)===root.program_sha256&&await sha256(stemRoot)===root.stem_artifact_sha256&&await sha256(stemInput)===root.stem_program_sha256);
 need(Array.isArray(index.frames)&&index.frames.length===LEAF_POPULATION_FIXTURE.frames);const frames:LeafPopulationFrame[]=[];
 for(let i=0;i<index.frames.length;i++){
  const descriptor=object(index.frames[i]);need(descriptor.index===i&&descriptor.path===`frame-${i}.json`);const bytes=await read(`frame-${i}.json`);
  need(bytes.length===descriptor.bytes&&await sha256(bytes)===descriptor.sha256);frames.push(decodeLeafPopulationFrame(parse(bytes),descriptor,root));
 }
 return {artifact_sha256:LEAF_POPULATION_FIXTURE.artifact_sha256,frames};
}
