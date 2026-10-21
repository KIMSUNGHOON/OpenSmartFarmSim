import { decodeMorphologyFrame,RATIONAL_MORPHOLOGY_SOURCE,sha256,type MorphologyFrame } from './morphologyReplay';
import { LEAF_AREA_FIXTURE } from './leafAreaReplayFixture';

export type StoredLeafArea=Readonly<{leaf_id:string;attachment_internode_id:string;curve_sha256:string;
  emerged_elapsed_seconds_exact:{numerator:string;denominator:string;unit:'s'};
  age_exact:{numerator:string;denominator:string;unit:'degC_day'};area:{value:number;unit:'m2'}}>;
export type LeafAreaFrame={schema_version:'leaf-area-replay-frame-v1';scope:'software_research_only';
  claim_scope:'synthetic_crop_math_only';gates:'not_assessed';artifact_sha256:string;result_sha256:string;input_sha256:string;
  index:number;at:string;time_origin_utc:string;tracked_leaf_count:number;tracked_leaf_area:{value:number;unit:'m2'};
  leaves:StoredLeafArea[];stem:MorphologyFrame};
export type LeafAreaReplay={artifact_sha256:string;frames:LeafAreaFrame[]};
const MAX=2*1024**2,DIRECTORY='./leaf-area-replay/';
const MODELS={rate:'leaf-logistic-thermal-area-rate-research-v1',change:'leaf-logistic-area-change-research-v1',
  point:'leaf-logistic-canonical-area-point-research-v1',area:'leaf-logistic-canonical-area-state-research-v1',
  clock:'leaf-rational-air-thermal-clock-research-v1',leaf_state:'leaf-rational-air-area-state-research-v1',inventory:'declared-leaf-inventory-research-v1'};
const DISPLAY={version:'stored-leaf-m2-authored-blade-triangles-v1',surface:'one_sided_authored_leaflet_triangles',
  petiole_rachis_area_excluded:true,placement:'declared_attachment_upper_end_authored_angles_v1',
  length_width_shape:'authored_uniform_scale_not_cultivar_prediction',leaf_count:'declared_initial_only'};
function need(c:unknown):asserts c{if(!c)throw Error('저장된 잎 면적의 원 파일·범위·무결성을 확인할 수 없습니다.');}
function object(v:unknown):Record<string,unknown>{need(v!==null&&typeof v==='object'&&!Array.isArray(v));return v as Record<string,unknown>;}
function closed(v:unknown,keys:string[]){const q=object(v);need(Object.keys(q).length===keys.length&&keys.every(k=>Object.hasOwn(q,k)));return q;}
function digest(v:unknown):asserts v is string{need(typeof v==='string'&&/^[0-9a-f]{64}$/.test(v));}
function id(v:unknown):asserts v is string{need(typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v));}
function utc(v:unknown):asserts v is string{need(typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(v)&&
  Number.isFinite(Date.parse(v))&&new Date(v).toISOString().replace('.000Z','Z')===v);}
function integer(v:unknown,min:number,max:number):asserts v is number{need(typeof v==='number'&&Number.isSafeInteger(v)&&v>=min&&v<=max);}
function flags(q:Record<string,unknown>){need(q.scope==='software_research_only'&&q.claim_scope==='synthetic_crop_math_only'&&q.gates==='not_assessed');}
function exact(v:unknown,unit:'s'|'degC_day'){
  const q=closed(v,['numerator','denominator','unit']);need(q.unit===unit);
  for(const k of ['numerator','denominator'])need(typeof q[k]==='string'&&/^(0|[1-9][0-9]{0,1023})$/.test(q[k]));
  const n=BigInt(q.numerator as string),d=BigInt(q.denominator as string);need(d>0n);let x=n,y=d;
  while(y){const r=x%y;x=y;y=r;}need(x===1n);return {n,d};
}
function area(v:unknown){const q=closed(v,['value','unit']);need(q.unit==='m2'&&typeof q.value==='number'&&Number.isFinite(q.value)&&q.value>0);}
function constants(v:unknown,expected:Record<string,unknown>){const q=closed(v,Object.keys(expected));need(Object.entries(expected).every(([k,value])=>q[k]===value));}
function rights(v:unknown){const q=closed(v,['access','declaration_id','declared_at_utc','display','ownership_asserted','redistribute','revision','store','transform','use']);
  for(const k of ['access','display','ownership_asserted','redistribute','store','transform','use'])need(q[k]===true);
  id(q.declaration_id);id(q.revision);utc(q.declared_at_utc);}
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

async function read(name:string,signal:AbortSignal){
  const response=await fetch(DIRECTORY+name,{signal,cache:'no-store',redirect:'error',credentials:'omit'});need(response.ok&&response.body);
  const reader=response.body.getReader(),chunks:Uint8Array[]=[];let size=0;
  try{while(true){const value=await reader.read();if(value.done)break;size+=value.value.byteLength;need(size<=MAX);chunks.push(value.value);}}
  catch(error){await reader.cancel();throw error;}
  finally{reader.releaseLock();}
  const raw=new Uint8Array(size);let offset=0;for(const part of chunks){raw.set(part,offset);offset+=part.length;}return raw;
}
function parse(raw:Uint8Array){return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)) as unknown;}
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
