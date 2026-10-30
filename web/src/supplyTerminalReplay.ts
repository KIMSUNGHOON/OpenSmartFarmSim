import {digest,integer,need,object,readStoredLeafFile,STORED_LEAF_MAX_BYTES} from './storedLeafReplayIO';
import {equal} from './leafFundedBirthReplaySchema';
import {wireHash} from './fundedLeafReplayWire';
import {add,binary64,exactAt,fraction,list,sub,type Row} from './supplyMorphologyGraphValues';
import {exactRecord,MASS,type ExactQuantity} from './supplyMorphologyQuantityCore';
import {readSupplyMorphologyStoredQuantities} from './supplyMorphologyStoredQuantities';
import {type SupplyGraphAnchor} from './supplyMorphologySourceGraph';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';

const NUMBER='fruits_equivalent/m2_floor';
const BACKEND_REFERENCE={schema_version:'supply-terminal-window-v1',
 code_sha256:'7fa58c6a6e1f4088fb97924a556ff7e46e0467f3bf5354cf2fb2671bd8e7bf83'};
type At={time_origin_utc:string;elapsed_seconds_exact:ExactQuantity};
type FrameReference={index:number;context_sha256:string;checkpoint_sha256:string|null;receipt_sha256:string|null;
 event_sequence:number;output_cursor:number;output_prefix_sha256:string;frame_sha256:string};
export type SupplyTerminalFrame={reference:FrameReference;at:At;phase:string;state_sha256:string;
 fruit_carbohydrate:{values:number[];unit:string};fruit_number:{values:number[];unit:string};
 carbohydrate_stock_exact:ExactQuantity;number_stock_exact:ExactQuantity;
 terminal_carbohydrate_exact:ExactQuantity;terminal_number_exact:ExactQuantity};
export type SupplyTerminalReplay=Awaited<ReturnType<typeof readSupplyTerminalReplay>>;

function hash(value:unknown){digest(value);return value;}
function nullableHash(value:unknown){return value===null?null:hash(value);}
function at(value:unknown):At{
 const t=exactAt(value);return {time_origin_utc:t.origin,elapsed_seconds_exact:exactRecord(t.elapsed,'s')};
}
function nonnegative(value:unknown,unit:string){const q=fraction(value,unit);need(q.n>=0n);return exactRecord(q,unit);}
function stock(values:number[],unit:string){
 return exactRecord(values.reduce((sum,v)=>add(sum,binary64(v)),{n:0n,d:1n}),unit);
}
function interval(left:SupplyTerminalFrame,right:SupplyTerminalFrame){
 need(left.at.time_origin_utc===right.at.time_origin_utc);
 const dt=sub(fraction(right.at.elapsed_seconds_exact,'s'),fraction(left.at.elapsed_seconds_exact,'s'));
 const c=sub(fraction(right.terminal_carbohydrate_exact,MASS),fraction(left.terminal_carbohydrate_exact,MASS));
 const n=sub(fraction(right.terminal_number_exact,NUMBER),fraction(left.terminal_number_exact,NUMBER));
 need(dt.n>=0n&&c.n>=0n&&n.n>=0n);
 if(dt.n===0n)need(c.n===0n&&n.n===0n&&left.phase==='fractional_before_compatible_material_point'
  &&right.phase==='fractional_after_compatible_material_point');
 return {from_frame:left.reference,to_frame:right.reference,start_at:left.at,end_at:right.at,
  kind:dt.n===0n?'zero_duration_material_boundary':'model_terminal_outflow',
  carbohydrate_exact:exactRecord(c,MASS),number_exact:exactRecord(n,NUMBER)};
}

/** Recorded source quantities only; no crop equation or Python execution. */
export async function readSupplyTerminalReplay(readFile:(name:string)=>Promise<Uint8Array>,anchor:SupplyGraphAnchor,signal:AbortSignal){
 anchor={...anchor};signal.throwIfAborted();
 const g=await readSupplyMorphologyStoredQuantities(readFile,anchor,signal),root=g.root.value;
 const checkpoints=new Map<string,Row>(),material=new Map<string,Row>();
 for(const context of g.contexts){
  for(const cp of context.checkpoints){
   signal.throwIfAborted();checkpoints.set(await wireHash(cp.raw),object(cp.value.lifetime_transfers_exact));
  }
 }
 for(const [i,receipt]of g.receipts.entries()){
  material.set(hash(g.contexts[i+1]!.descriptor.value.point_sha256),object(object(receipt.before.value.dense_candidate).pending_lifetime_transfers_exact));
 }
 const descriptors=list(g.index.value.frames),frames:SupplyTerminalFrame[]=[],basis=object(g.frames[0]).model_floor_area;
 for(const [index,value]of g.frames.entries()){
  const f=object(value);
  signal.throwIfAborted();equal(f.model_floor_area,basis);
  const layout=object(object(f.state_layout).original);
  equal(layout.plant,['buffer','temperature_filtered_24h','temperature_sum']);
  equal(layout.cohort_arrays,['fruit_carbohydrate','fruit_number']);
  equal(object(layout.units).cohort_arrays,{fruit_carbohydrate:MASS,fruit_number:NUMBER});
  const carbon=value.snapshot.state.slice(3,53),number=value.snapshot.state.slice(53,103);
  need(carbon.length===50&&number.length===50&&carbon.every((c,i)=>c>=0&&number[i]!>=0&&(c===0||number[i]!>0)));
  const cp=nullableHash(f.checkpoint_sha256),receipt=nullableHash(f.receipt_sha256);
  const lifetime=cp===null?material.get(hash(receipt)):checkpoints.get(cp);need(lifetime);
  const sequence=f.event_sequence,cursor=f.output_cursor;integer(sequence,0,Number.MAX_SAFE_INTEGER);integer(cursor,1,Number.MAX_SAFE_INTEGER);
  need(f.index===index&&typeof f.phase==='string');
  const descriptor=object(descriptors[index]);
  frames.push({reference:{index,context_sha256:hash(f.context_sha256),checkpoint_sha256:cp,receipt_sha256:receipt,
   event_sequence:sequence,output_cursor:cursor,output_prefix_sha256:hash(f.output_prefix_sha256),frame_sha256:hash(descriptor.frame_sha256)},
   at:at(f.at),phase:f.phase,state_sha256:hash(descriptor.state_sha256),
   fruit_carbohydrate:{values:carbon,unit:MASS},fruit_number:{values:number,unit:NUMBER},
   carbohydrate_stock_exact:stock(carbon,MASS),number_stock_exact:stock(number,NUMBER),
   terminal_carbohydrate_exact:nonnegative(lifetime.terminal_carbon,MASS),terminal_number_exact:nonnegative(lifetime.terminal_number,NUMBER)});
 }
 const intervals=frames.slice(1).map((right,i)=>interval(frames[i]!,right));
 const source={artifact_sha256:g.artifact_sha256,model_code_sha256:root.code_sha256,root_inputs:root.root_inputs,
  source_rights:root.source_rights,redistribution_authorized:root.redistribution_authorized,model_floor_area:basis,terminal:root.terminal};
 function window(first=0,last=frames.length-1){
  integer(first,0,frames.length-1);integer(last,first,frames.length-1);
  const selected=frames.slice(first,last+1),rows=intervals.slice(first,last),left=selected[0]!,right=selected.at(-1)!;
  const c=sub(fraction(right.terminal_carbohydrate_exact,MASS),fraction(left.terminal_carbohydrate_exact,MASS));
  const n=sub(fraction(right.terminal_number_exact,NUMBER),fraction(left.terminal_number_exact,NUMBER));
  need(sub(rows.reduce((v,row)=>add(v,fraction(row.carbohydrate_exact,MASS)),{n:0n,d:1n}),c).n===0n);
  need(sub(rows.reduce((v,row)=>add(v,fraction(row.number_exact,NUMBER)),{n:0n,d:1n}),n).n===0n);
  const result={schema_version:'supply-terminal-browser-window-v1' as const,backend_reference:BACKEND_REFERENCE,
   scope:'software_research_only' as const,claim_scope:'synthetic_terminal_quantities_only' as const,G0_G4:root.G0_G4,R2:root.R2,
   source,window:{first_frame:first,last_frame:last,start_at:left.at,end_at:right.at},frames:selected,intervals:rows,
   totals:{terminal_carbohydrate_exact:exactRecord(c,MASS),terminal_number_exact:exactRecord(n,NUMBER)}};
  need(new TextEncoder().encode(JSON.stringify(result)).byteLength<=STORED_LEAF_MAX_BYTES);
  return structuredClone(result);
 }
 window();signal.throwIfAborted();
 const morphology=g.frames;
 const summary={schema_version:'supply-terminal-browser-replay-v1' as const,validation_scope:'stored_source_and_terminal_quantities_only' as const,
  artifact_sha256:g.artifact_sha256,index_sha256:anchor.index_sha256,frames:frames.length,sample_scalars:g.sample_scalars,
  downloaded_bytes:g.downloaded_bytes,scope:'software_research_only' as const,claim_scope:'synthetic_terminal_quantities_only' as const,
  source_rights:root.source_rights,code_sha256:root.code_sha256,terminal:root.terminal,G0_G4:root.G0_G4,R2:root.R2,backend_reference:BACKEND_REFERENCE};
 return {summary:()=>structuredClone(summary),frame:(index:number)=>{
  integer(index,0,frames.length-1);return structuredClone({morphology:morphology[index]!,quantities:frames[index]!});
 },window};
}
export function loadSupplyTerminalReplay(signal:AbortSignal){
 return readSupplyTerminalReplay(name=>readStoredLeafFile('./supply-morphology-replay/own-public-v1/',name,signal),{...F.anchor},signal);
}
export class SupplyTerminalRequest{
 private generation=0;private controller?:AbortController;
 cancel(){this.generation++;this.controller?.abort();this.controller=undefined;}
 async load(){
  this.cancel();const generation=this.generation,controller=new AbortController();this.controller=controller;
  try{
   const replay=await loadSupplyTerminalReplay(controller.signal);controller.signal.throwIfAborted();need(generation===this.generation);return replay;
  }finally{if(generation===this.generation)this.controller=undefined;}
 }
}
