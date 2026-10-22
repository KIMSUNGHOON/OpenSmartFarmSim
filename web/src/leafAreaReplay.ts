import { decodeMorphologyFrame,RATIONAL_MORPHOLOGY_SOURCE,sha256,type MorphologyFrame } from './morphologyReplay';
import { LEAF_AREA_FIXTURE } from './leafAreaReplayFixture';
import {STORED_LEAF_MAX_BYTES as MAX,need,object,closed,digest,id,utc,integer,flags,exact,area,constants,rights,readStoredLeafFile,parse} from './storedLeafReplayIO';

export type StoredLeafArea=Readonly<{leaf_id:string;attachment_internode_id:string;curve_sha256:string;
  emerged_elapsed_seconds_exact:{numerator:string;denominator:string;unit:'s'};
  age_exact:{numerator:string;denominator:string;unit:'degC_day'};area:{value:number;unit:'m2'}}>;
export type LeafAreaFrame={schema_version:'leaf-area-replay-frame-v1';scope:'software_research_only';
  claim_scope:'synthetic_crop_math_only';gates:'not_assessed';artifact_sha256:string;result_sha256:string;input_sha256:string;
  index:number;at:string;time_origin_utc:string;tracked_leaf_count:number;tracked_leaf_area:{value:number;unit:'m2'};
  leaves:StoredLeafArea[];stem:MorphologyFrame};
export type LeafAreaReplay={artifact_sha256:string;frames:LeafAreaFrame[]};
const DIRECTORY='./leaf-area-replay/';
const MODELS={rate:'leaf-logistic-thermal-area-rate-research-v1',change:'leaf-logistic-area-change-research-v1',
  point:'leaf-logistic-canonical-area-point-research-v1',area:'leaf-logistic-canonical-area-state-research-v1',
  clock:'leaf-rational-air-thermal-clock-research-v1',leaf_state:'leaf-rational-air-area-state-research-v1',inventory:'declared-leaf-inventory-research-v1'};
const DISPLAY={version:'stored-leaf-m2-authored-blade-triangles-v1',surface:'one_sided_authored_leaflet_triangles',
  petiole_rachis_area_excluded:true,placement:'declared_attachment_upper_end_authored_angles_v1',
  length_width_shape:'authored_uniform_scale_not_cultivar_prediction',leaf_count:'declared_initial_only'};
function manifest(v:unknown){
  const m=closed(v,['claim_scope','code_sha256','declared_leaves','display_policy','gates','initial_at_elapsed_seconds_exact',
    'initial_state_sha256','model_versions','parameter_scope','program_bytes','program_rights','program_sha256','samples','schema_version',
    'scope','status','stem_artifact_sha256','stem_program_sha256','terminal_state_sha256','time_kind','time_origin_utc']);
  flags(m);need(m.schema_version==='leaf-area-research-artifact-v1'&&m.status==='completed_software_fixture'&&
    m.parameter_scope==='synthetic_software_fixture_only'&&m.time_kind==='synthetic_model_clock_not_observation');
  constants(m.model_versions,MODELS);constants(m.display_policy,DISPLAY);rights(m.program_rights);utc(m.time_origin_utc);
  for(const k of ['initial_state_sha256','program_sha256','stem_artifact_sha256','stem_program_sha256','terminal_state_sha256'])digest(m[k]);
  exact(m.initial_at_elapsed_seconds_exact,'s');integer(m.program_bytes,1,MAX);
  const codes=object(m.code_sha256);need(Object.keys(codes).length===24);
  for(const [name,value]of Object.entries(codes)){need(/^backend\/app\/[a-z_]+\.py$/.test(name));digest(value);}
  need(Array.isArray(m.samples)&&m.samples.length===LEAF_AREA_FIXTURE.frames&&Array.isArray(m.declared_leaves)&&m.declared_leaves.length>0&&m.declared_leaves.length<=512);
  const ids=new Set<string>();for(const raw of m.declared_leaves){const q=closed(raw,['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact']);
    id(q.leaf_id);id(q.attachment_internode_id);digest(q.curve_sha256);exact(q.emerged_elapsed_seconds_exact,'s');need(!ids.has(q.leaf_id));ids.add(q.leaf_id);}
  return m;
}

export function decodeLeafAreaFrame(value:unknown,descriptor:unknown,root:unknown):LeafAreaFrame{
  const m=manifest(root),d=closed(descriptor,['index','at','path','sha256','bytes','result_sha256','stem_result_sha256']);
  integer(d.index,0,LEAF_AREA_FIXTURE.frames-1);utc(d.at);integer(d.bytes,1,MAX);digest(d.sha256);digest(d.result_sha256);digest(d.stem_result_sha256);
  need(d.path===`frame-${d.index}.json`);const sample=object((m.samples as unknown[])[d.index]);
  need(sample.index===d.index&&sample.at===d.at&&sample.result_sha256===d.result_sha256&&sample.stem_result_sha256===d.stem_result_sha256);
  const f=closed(value,['schema_version','scope','claim_scope','gates','artifact_sha256','result_sha256','input_sha256','index','at',
    'time_origin_utc','tracked_leaf_count','tracked_leaf_area','leaves','stem']);flags(f);
  need(f.schema_version==='leaf-area-replay-frame-v1'&&f.artifact_sha256===LEAF_AREA_FIXTURE.artifact_sha256&&
    f.index===d.index&&f.at===d.at&&f.result_sha256===d.result_sha256&&f.input_sha256===sample.input_sha256&&f.time_origin_utc===m.time_origin_utc);
  digest(f.input_sha256);area(f.tracked_leaf_area);integer(f.tracked_leaf_count,1,512);
  const declared=m.declared_leaves as unknown[];need(Array.isArray(f.leaves)&&f.leaves.length===declared.length&&f.tracked_leaf_count===declared.length);
  const stem=decodeMorphologyFrame(f.stem,{index:d.index,at:d.at,path:d.path,sha256:d.sha256,bytes:d.bytes,result_sha256:d.stem_result_sha256},
    {...RATIONAL_MORPHOLOGY_SOURCE,artifact_sha256:m.stem_artifact_sha256 as string});
  need(stem.schema_version==='morphology-replay-frame-v2'&&stem.at===f.at&&stem.time_origin_utc===f.time_origin_utc);
  const ids=new Set(stem.internodes.map(n=>n.internode_id)),elapsed=BigInt((Date.parse(d.at)-Date.parse(stem.time_origin_utc))/1000);
  for(let i=0;i<f.leaves.length;i++){
    const q=closed(f.leaves[i],['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact','age_exact','area']);
    const declaration=object(declared[i]);need(q.leaf_id===declaration.leaf_id&&q.attachment_internode_id===declaration.attachment_internode_id&&
      q.curve_sha256===declaration.curve_sha256&&ids.has(q.attachment_internode_id as string));
    const birth=exact(q.emerged_elapsed_seconds_exact,'s'),expected=exact(declaration.emerged_elapsed_seconds_exact,'s');
    need(birth.n===expected.n&&birth.d===expected.d&&birth.n<=elapsed*birth.d);exact(q.age_exact,'degC_day');area(q.area);
  }
  return {...f,stem} as LeafAreaFrame;
}

const read=(name:string,signal:AbortSignal)=>readStoredLeafFile(DIRECTORY,name,signal);

export async function loadLeafAreaReplay(signal:AbortSignal):Promise<LeafAreaReplay>{
  const raw=await read('index.json',signal);need(await sha256(raw)===LEAF_AREA_FIXTURE.index_sha256);
  const index=closed(parse(raw),['schema_version','scope','claim_scope','gates','model_versions','display_policy','artifact_sha256','program_sha256','stem_artifact_sha256','rights','stem_rights','frames']);
  flags(index);need(index.schema_version==='leaf-area-public-fixture-v1'&&index.artifact_sha256===LEAF_AREA_FIXTURE.artifact_sha256);
  constants(index.model_versions,MODELS);constants(index.display_policy,DISPLAY);rights(index.rights);rights(index.stem_rights);
  const rootRaw=await read('root.json',signal);need(await sha256(rootRaw)===LEAF_AREA_FIXTURE.artifact_sha256);const root=manifest(parse(rootRaw));
  need(root.program_sha256===index.program_sha256&&root.stem_artifact_sha256===index.stem_artifact_sha256);
  const input=await read('input.json',signal),stemRoot=await read('stem-root.json',signal),stemInput=await read('stem-input.json',signal);
  need(await sha256(input)===root.program_sha256&&await sha256(stemRoot)===root.stem_artifact_sha256&&await sha256(stemInput)===root.stem_program_sha256);
  need(Array.isArray(index.frames)&&index.frames.length===LEAF_AREA_FIXTURE.frames);const frames:LeafAreaFrame[]=[];
  for(let i=0;i<index.frames.length;i++){
    const d=object(index.frames[i]);need(d.index===i&&d.path===`frame-${i}.json`);const frame=await read(`frame-${i}.json`,signal);
    need(frame.length===d.bytes&&await sha256(frame)===d.sha256);frames.push(decodeLeafAreaFrame(parse(frame),d,root));
  }
  return {artifact_sha256:LEAF_AREA_FIXTURE.artifact_sha256,frames};
}
