import { MORPHOLOGY_FIXTURE } from './morphologyReplayFixture';
import { MORPHOLOGY_RATIONAL_FIXTURE } from './morphologyRationalReplayFixture';

type Quantity={value:number;unit:'m'};
type Age={numerator:string;denominator:string;unit:'degC_day'};
type Elapsed={numerator:string;denominator:string;unit:'s'};
type Internode={sequence:number;internode_id:string;birth_age_exact:Age;age_exact:Age;length:Quantity};
type FrameFields={scope:'software_research_only';
  claim_scope:'synthetic_crop_math_only';gates:'not_assessed';artifact_sha256:string;result_sha256:string;
  input_sha256:string;index:number;at:string;shoot_id:string;tracked_axis_length:Quantity};
export type MorphologyFrame=FrameFields&(
  {schema_version:'morphology-replay-frame-v1';internodes:(Internode&{emerged_at:string})[]}|
  {schema_version:'morphology-replay-frame-v2';time_origin_utc:string;internodes:(Internode&{emerged_elapsed_seconds_exact:Elapsed})[]});
export type MorphologyReplaySource={artifact_sha256:string;index_sha256:string;frames:number}&(
  {version:'v1';directory:'./morphology-replay'}|{version:'v2';directory:'./morphology-rational-replay'});
export const LEGACY_MORPHOLOGY_SOURCE:MorphologyReplaySource={...MORPHOLOGY_FIXTURE,version:'v1',directory:'./morphology-replay'};
export const RATIONAL_MORPHOLOGY_SOURCE:MorphologyReplaySource={...MORPHOLOGY_RATIONAL_FIXTURE,version:'v2',directory:'./morphology-rational-replay'};
export type MorphologyReplay={frames:MorphologyFrame[];artifact_sha256:string};
type Descriptor={index:number;at:string;path:string;sha256:string;bytes:number;result_sha256:string};

function need(condition:unknown):asserts condition {if(!condition)throw Error('저장된 형태 결과의 무결성·형식을 확인할 수 없습니다.');}
function object(v:unknown):Record<string,unknown>{need(v!==null&&typeof v==='object'&&!Array.isArray(v));return v as Record<string,unknown>;}
function closed(v:unknown,keys:string[]){const o=object(v);need(Object.keys(o).length===keys.length&&keys.every(k=>Object.hasOwn(o,k)));return o;}
function digest(v:unknown){need(typeof v==='string'&&/^[0-9a-f]{64}$/.test(v));}
function utc(v:unknown){need(typeof v==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$/.test(v)&&
  Number.isFinite(Date.parse(v))&&new Date(v).toISOString().replace('.000Z','Z')===v);}
function id(v:unknown){need(typeof v==='string'&&/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v));}
function quantity(v:unknown,positive:boolean){const q=closed(v,['value','unit']);need(q.unit==='m'&&typeof q.value==='number'&&
  Number.isFinite(q.value)&&(positive?q.value>0:q.value>=0));}
function age(v:unknown){const a=closed(v,['numerator','denominator','unit']);need(a.unit==='degC_day');
  for(const k of ['numerator','denominator'])need(typeof a[k]==='string'&&/^(0|[1-9][0-9]{0,1023})$/.test(a[k]));
  need(a.denominator!=='0');}

function exact(v:unknown,unit:'s'|'degC_day'){
  const a=closed(v,['numerator','denominator','unit']);need(a.unit===unit);
  for(const k of ['numerator','denominator'])need(typeof a[k]==='string'&&/^(0|[1-9][0-9]{0,1023})$/.test(a[k]));
  const numerator=BigInt(a.numerator as string),denominator=BigInt(a.denominator as string);need(denominator>0n);
  let x=numerator,y=denominator;while(y!==0n){const remainder=x%y;x=y;y=remainder;}need(x===1n);
  return {numerator,denominator};
}

export function decodeMorphologyFrame(value:unknown,d:Descriptor,source:MorphologyReplaySource=LEGACY_MORPHOLOGY_SOURCE):MorphologyFrame {
  const rational=source.version==='v2';
  const f=closed(value,['schema_version','scope','claim_scope','gates','artifact_sha256','result_sha256','input_sha256',
    'index','at','shoot_id','internodes','tracked_axis_length',...(rational?['time_origin_utc']:[])]);
  need(f.schema_version===`morphology-replay-frame-${source.version}`&&f.scope==='software_research_only'&&
    f.claim_scope==='synthetic_crop_math_only'&&f.gates==='not_assessed'&&f.artifact_sha256===source.artifact_sha256&&
    f.index===d.index&&f.at===d.at&&f.result_sha256===d.result_sha256);
  digest(f.input_sha256);utc(f.at);id(f.shoot_id);quantity(f.tracked_axis_length,false);
  let elapsed=0n;
  if(rational){utc(f.time_origin_utc);need((f.time_origin_utc as string)<=(f.at as string));
    elapsed=BigInt((Date.parse(f.at as string)-Date.parse(f.time_origin_utc as string))/1000);}
  need(Array.isArray(f.internodes)&&f.internodes.length<=512);
  let previous=-1,lastBirth:{numerator:bigint;denominator:bigint}|null=null;const ids=new Set<string>();
  for(const raw of f.internodes){const n=closed(raw,['sequence','internode_id',rational?'emerged_elapsed_seconds_exact':'emerged_at','birth_age_exact','age_exact','length']);
    need(typeof n.sequence==='number'&&Number.isSafeInteger(n.sequence)&&n.sequence>=0&&n.sequence<=2**31-1&&
      (previous<0||n.sequence===previous+1));previous=n.sequence;
    id(n.internode_id);need(!ids.has(n.internode_id as string));ids.add(n.internode_id as string);
    if(rational){const birth=exact(n.emerged_elapsed_seconds_exact,'s');
      need(birth.numerator<=elapsed*birth.denominator&&(!lastBirth||birth.numerator*lastBirth.denominator>=lastBirth.numerator*birth.denominator));
      lastBirth=birth;exact(n.birth_age_exact,'degC_day');exact(n.age_exact,'degC_day');
    }else{utc(n.emerged_at);need((n.emerged_at as string)<=(f.at as string));age(n.birth_age_exact);age(n.age_exact);}
    quantity(n.length,true);
  }
  return f as MorphologyFrame;
}

export async function sha256(raw:Uint8Array<ArrayBuffer>){
  return [...new Uint8Array(await crypto.subtle.digest('SHA-256',raw))].map(n=>n.toString(16).padStart(2,'0')).join('');
}
async function read(url:string,maximum:number,signal:AbortSignal){
  const response=await fetch(url,{signal,cache:'no-store'});need(response.ok&&response.body);
  const reader=response.body.getReader(),chunks:Uint8Array[]=[];let total=0;
  try{while(true){const value=await reader.read();if(value.done)break;total+=value.value.byteLength;
    need(total<=maximum);chunks.push(value.value);}}
  catch(error){await reader.cancel().catch(()=>{});throw error;}finally{reader.releaseLock();}
  const raw=new Uint8Array(total);let offset=0;for(const chunk of chunks){raw.set(chunk,offset);offset+=chunk.byteLength;}return raw;
}
function parse(raw:Uint8Array){return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)) as unknown;}

export async function loadMorphologyReplay(signal:AbortSignal,source:MorphologyReplaySource=LEGACY_MORPHOLOGY_SOURCE):Promise<MorphologyReplay>{
  const raw=await read(source.directory+'/index.json',128*1024,signal);
  need(await sha256(raw)===source.index_sha256);const index=object(parse(raw));
  need(index.schema_version===`morphology-public-fixture-${source.version}`&&index.artifact_sha256===source.artifact_sha256&&
    index.scope==='software_research_only'&&index.claim_scope==='synthetic_crop_math_only'&&index.gates==='not_assessed');
  const rights=object(index.rights);need(rights.redistribute===true&&rights.display===true&&rights.use===true);
  need(Array.isArray(index.frames)&&index.frames.length===source.frames);
  const frames:MorphologyFrame[]=[];let bytes=raw.byteLength;let previous='';
  for(let i=0;i<index.frames.length;i++){
    const d=closed(index.frames[i],['index','at','path','sha256','bytes','result_sha256']);
    need(d.index===i&&d.path===`frame-${i}.json`&&typeof d.bytes==='number'&&Number.isSafeInteger(d.bytes)&&d.bytes>0&&d.bytes<=2*1024**2);
    utc(d.at);need((d.at as string)>previous);previous=d.at as string;digest(d.sha256);digest(d.result_sha256);
    const body=await read(source.directory+'/'+d.path,d.bytes,signal);bytes+=body.byteLength;
    need(bytes<=8*1024**2&&body.byteLength===d.bytes&&await sha256(body)===d.sha256);
    const frame=decodeMorphologyFrame(parse(body),d as Descriptor,source);
    if(frames.length){const first=frames[0]!;need(frame.shoot_id===first.shoot_id);
      if(frame.schema_version==='morphology-replay-frame-v2')need(first.schema_version==='morphology-replay-frame-v2'&&frame.time_origin_utc===first.time_origin_utc);}
    frames.push(frame);
  }
  return {frames,artifact_sha256:source.artifact_sha256};
}
