import {closed,digest,need,object} from './storedLeafReplayIO';
import {wireItems,wireHash} from './fundedLeafReplayWire';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {equal} from './leafFundedBirthReplaySchema';
import {binary64,compare,counter,document,exactAt,fraction,mul,sub,wireObject,type WireDocument} from './supplyMorphologyGraphValues';

export const CONTEXT='supply-morphology-repeat-context-v2',AUTHORITY='supply-morphology-repeat-authority-research-v2';
export const MODEL='supply-morphology-repeat-continuation-research-v1',CHECKPOINT='supply-morphology-repeat-checkpoint-v1';
const installed:Readonly<Record<string,string>>=F.code_sha256;
export const MODEL_PINS_RAW=wireObject(Object.fromEntries(F.model_paths.map(name=>[name,JSON.stringify(installed[name])])));
export function modelPins(value:unknown){const q=closed(value,[...F.model_paths]);for(const path of F.model_paths)need(q[path]===installed[path]);}
export type SupplyContext={sha256:string;doc:WireDocument;descriptor:WireDocument;seed:WireDocument;packed:string[];checkpoints:WireDocument[]};

export async function readSupplyContext(raw:string,sha256:string):Promise<SupplyContext>{
 digest(sha256);need(await wireHash(raw)===sha256);
 const doc=document(raw),q=closed(doc.value,[...F.schema_keys.context]);need(q.version===CONTEXT);
 const descriptor=document(doc.fields.descriptor!),d=closed(descriptor.value,[...F.schema_keys.descriptor]);
 need(d.version===CONTEXT&&d.model_version===AUTHORITY&&d.scope==='software_research_only'&&d.G0_G4==='not_assessed');modelPins(d.source_code_sha256);
 for(const key of ['origin_context_sha256','root_checkpoint_sha256','point_sha256'])digest(d[key]);
 need(await wireHash(doc.fields.root_checkpoint!)===d.root_checkpoint_sha256);
 const packed=wireItems(doc.fields.receipts!),hashes=JSON.parse(descriptor.fields.receipt_sha256!)as unknown;
 need(Array.isArray(hashes)&&hashes.length===packed.length&&packed.length<=511);
 for(const [i,p]of packed.entries()){digest(hashes[i]);need(object(JSON.parse(p)).receipt_sha256===hashes[i]);}
 need(d.point_sha256===(hashes.at(-1)??d.root_checkpoint_sha256));
 const seed=document(descriptor.fields.seed!),s=closed(seed.value,[...F.schema_keys.seed]);
 const numerical=document(seed.fields.original_numerical!),n=closed(numerical.value,[...F.schema_keys.numerical]);
 need(n.method==='shared-stage-fixed-rk4-leaf-stem-root-carbon-area-v1'&&n.sample_scalar_budget===32768);
 const count=counter(numerical,'step_count',1),dt=binary64(n.step_seconds);need(dt.n>0n);
 counter(seed,'event_sequence');counter(seed,'output_cursor',1);need(s.redistribution_authorized===true);
 const at=exactAt(object(s.initial_sample).at),gridDoc=document(seed.fields.original_grid_position!);
 const grid=closed(gridDoc.value,['completed_grid_index','at_original_grid','next_grid_index','next_grid_elapsed_seconds_exact','remaining_to_next_grid_seconds_exact']);
 const completed=counter(gridDoc,'completed_grid_index',0,count);
 need(BigInt(completed)===at.elapsed.n*dt.d/(at.elapsed.d*dt.n)&&compare(at.elapsed,mul(dt,{n:BigInt(count),d:1n}))<=0);
 need(grid.at_original_grid===(compare(at.elapsed,mul(dt,{n:BigInt(completed),d:1n}))===0));
 if(completed<count){
  const next=mul(dt,{n:BigInt(completed+1),d:1n});
  need(counter(gridDoc,'next_grid_index',0,count)===completed+1&&compare(fraction(grid.next_grid_elapsed_seconds_exact,'s'),next)===0);
  need(compare(fraction(grid.remaining_to_next_grid_seconds_exact,'s'),sub(next,at.elapsed))===0);
 }else need(grid.next_grid_index===null&&grid.next_grid_elapsed_seconds_exact===null&&fraction(grid.remaining_to_next_grid_seconds_exact,'s').n===0n);
 return {sha256,doc,descriptor,seed,packed,checkpoints:[]};
}

export async function readSupplyCheckpoint(raw:string,context:SupplyContext,previous:WireDocument|undefined):Promise<WireDocument>{
 need(new TextEncoder().encode(raw).byteLength<=512*1024);
 const doc=document(raw),q=closed(doc.value,[...F.schema_keys.checkpoint]),seed=context.seed.value,d=context.descriptor.value;
 need(q.version===CHECKPOINT&&q.model_version===MODEL&&q.context_sha256===context.sha256&&q.scope==='software_research_only'&&q.G0_G4==='not_assessed');modelPins(q.source_code_sha256);
 need(q.origin_context_sha256===d.origin_context_sha256&&q.point_sha256===d.point_sha256&&q.redistribution_authorized===true);
 const seedSHA=await wireHash(wireObject({version:JSON.stringify(AUTHORITY),context_sha256:JSON.stringify(context.sha256),seed:context.seed.raw}));
 need(q.seed_checkpoint_sha256===seedSHA);
 const n=object(seed.original_numerical),steps=counter(doc,'branch_steps',0,Number(n.step_count)),grid=counter(doc,'grid_index',0,Number(n.step_count));
 need(grid===Number(object(seed.original_grid_position).completed_grid_index)+steps);
 counter(doc,'event_sequence');counter(doc,'output_cursor',1);
 const at=exactAt(q.at),initial=exactAt(object(seed.initial_sample).at);
 need(at.origin===initial.origin&&q.event_sequence===seed.event_sequence&&q.output_cursor===Number(seed.output_cursor)+steps);
 need(compare(at.elapsed,steps===0?initial.elapsed:mul(binary64(n.step_seconds),{n:BigInt(grid),d:1n}))===0);
 equal(object(q.last_confirmed).at,q.at);
 need(q.phase===(steps===0?'fractional_after_compatible_material_point':'original_grid_endpoint'));
 equal(q.point_totals_exact,seed.point_totals_exact);equal(q.transfer_origins,seed.transfer_origins);
 if(previous===undefined){
  need(steps===0&&doc.fields.last_confirmed===context.seed.fields.initial_sample&&q.output_prefix_link===null&&q.output_prefix_sha256===seed.output_prefix_sha256);
  for(const quantity of Object.values(object(q.branch_integrated_transfers)))need(object(quantity).value===0);
 }else{
  const sampleSHA=await wireHash(doc.fields.last_confirmed!);
  equal(q.output_prefix_link,{previous_output_prefix_sha256:previous.value.output_prefix_sha256,sample_sha256:sampleSHA});
  need(steps===Number(previous.value.branch_steps)+1);
  const prefix=wireObject({context_sha256:JSON.stringify(context.sha256),seed_checkpoint_sha256:JSON.stringify(seedSHA),
   previous:JSON.stringify(previous.value.output_prefix_sha256),sample_sha256:JSON.stringify(sampleSHA),steps:String(steps),phase:'"original_grid_endpoint"',model_version:JSON.stringify(MODEL)});
  need(q.output_prefix_sha256===await wireHash(prefix));
 }
 const schedule=closed(q.schedule,[...F.schema_keys.schedule]);fraction(schedule.age_exact,'degC_day');fraction(schedule.next_threshold_exact,'degC_day');
 need(compare(fraction(schedule.age_exact,'degC_day'),fraction(schedule.next_threshold_exact,'degC_day'))<0);
 return doc;
}
