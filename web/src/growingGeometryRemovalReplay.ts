import {sha256} from './morphologyReplay';
import {growingGeometryOffset,type GrowingGeometryFrame} from './growingGeometryReplay';
import {GROWING_GEOMETRY_REMOVAL_FIXTURE as FIXTURE} from './growingGeometryRemovalReplayFixture';
import {need,object,closed,digest,id,utc,integer,rights,exact,readStoredLeafFile,parse} from './storedLeafReplayIO';

const {scenarios:ANCHORS,...ROOT}=FIXTURE;
export type GrowingGeometryRemovalScenario=keyof typeof ANCHORS;
type Quantity={value:number;unit:string};
type Block=Record<string,Quantity>;
type Phase='before_removal'|'after_removal_before_next_step'|'post_removal_interval';
export type GrowingGeometryRemovalFrame=Omit<typeof ROOT,'schema_version'>&Pick<GrowingGeometryFrame,
 'artifact_sha256'|'input_id'|'input_sha256'|'checkpoint_sha256'|'sample_sha256'|'state_sha256'|'index'|'at'|'elapsed_seconds'|
 'leaf_ids'|'state_layout'|'leaves'|'sample'|'source_rights'|'plant'|'cohorts'|'climate'>&{
 schema_version:'growing-geometry-removal-replay-frame-v1';global_step_index:number;phase:Phase;
 parent_context_sha256:string;post_context_sha256:string;point_calculation_sha256:string;
 original_curve_invariant:Quantity[];active_original_curve_invariant:Quantity[];
 removed_last_states:Array<{leaf_id:string;thermal_age:Quantity;area:Quantity}>|null;
 original_interval_transfers:Block;point_outflows:Block|null;segment_integrated_transfers:Block|null;
 segment_balance_residuals:Block|null;segment_balance_budgets:Block|null;global_balance_residuals:Block;global_balance_budgets:Block};
export type GrowingGeometryRemovalReplay={scenario:GrowingGeometryRemovalScenario;artifact_sha256:string;frames:GrowingGeometryRemovalFrame[]};
type Context={artifact_sha256:string;root:unknown;context:unknown;program:unknown;seed:unknown;postContext:unknown;
 postProgram:unknown;postSeed:unknown;point:unknown;inputs:unknown;curveHashes:Record<string,string>};
const SOURCE_ROLES=['inputs','request','program','seed','context','growth_profile','cohort_profile','transport_profile','exchange_profile',
 'license_notice','point_inputs','point_result','post_context','post_program','post_seed','post_snapshot'];
const ROOT_FIELDS=[...Object.keys(ROOT),'input_id','source_rights','time_origin_utc','sources','code_sha256','parent_context_sha256',
 'post_context_sha256','point_calculation_sha256','initial_state_sha256','terminal_state_sha256','event_step_index','samples'];
const SAMPLE_DESCRIPTOR=['index','global_step_index','phase','elapsed_seconds_exact','checkpoint_sha256','checkpoint_bytes','sample_sha256','state_sha256','previous_checkpoint_sha256'];
const FRAME_DESCRIPTOR=['index','global_step_index','phase','at','parent_context_sha256','post_context_sha256','point_calculation_sha256',
 'checkpoint_sha256','sample_sha256','state_sha256','path','sha256','bytes'];
const PLANT={buffer:'mg_CH2O/m2_floor',leaf:'mg_CH2O/m2_floor',stem_root:'mg_CH2O/m2_floor',temperature_filtered_24h:'degC',temperature_sum:'degC_day'};
const COHORT={fruit_carbohydrate:'mg_CH2O/m2_floor',fruit_number:'fruits_equivalent/m2_floor'};
const CLIMATE={canopy_sensible_energy:'J/m2_floor',air_temperature:'degC',air_vapor_mass:'kg_water/m2_floor'};
const DERIVED={canopy_temperature:'degC',leaf_area_index:'m2_leaf/m2_floor',leaf_area_index_rate:'m2_leaf/m2_floor/s',
 canopy_capacity:'J/m2_floor/K',air_capacity:'J/m2_floor/K',air_vapor_pressure:'Pa',canopy_temperature_rate:'K/s'};
const FLUX:Record<string,string>={...Object.fromEntries(['photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem',
 'maintenance_fruit','removal_leaf','removal_stem','terminal_carbon'].map(k=>[k,'mg_CH2O/m2_floor'])),
 ...Object.fromEntries(['entry_number','terminal_number'].map(k=>[k,'fruits_equivalent/m2_floor'])),
 ...Object.fromEntries(['sensible','latent','incoming_heat','outgoing_heat','canopy_external','air_external'].map(k=>[k,'J/m2_floor'])),
 vapor:'kg_water/m2_floor',external_vapor:'kg_water/m2_floor',capacity_in:'J/m2_floor/K',capacity_out:'J/m2_floor/K',indoor_air_temperature_time:'degC_s'};
const BALANCES={carbohydrate:'mg_CH2O/m2_floor',number:'fruits_equivalent/m2_floor',canopy_sensible:'J/m2_floor',
 air_sensible:'J/m2_floor',vapor:'kg_water/m2_floor',area_capacity:'J/m2_floor/K',reduced_energy:'J/m2_floor'};
const POINT={carbohydrate:'mg_CH2O/m2_floor',capacity:'J/m2_floor/K',sensible_energy:'J/m2_floor'};

function equal(a:unknown,b:unknown):void{
 if(Object.is(a,b))return;
 if(Array.isArray(a)){need(Array.isArray(b)&&a.length===b.length);a.forEach((v,i)=>equal(v,b[i]));return;}
 const x=object(a),y=closed(b,Object.keys(x));for(const k of Object.keys(x))equal(x[k],y[k]);
}
function list(v:unknown,length:number):unknown[]{need(Array.isArray(v)&&v.length===length);return v;}
function finite(v:unknown):asserts v is number{need(typeof v==='number'&&Number.isFinite(v));}
function quantity(v:unknown,unit:string){const q=closed(v,['value','unit']);finite(q.value);need(q.unit===unit);return q.value;}
function block(v:unknown,units:Record<string,string>){const q=closed(v,Object.keys(units));for(const [k,u]of Object.entries(units))quantity(q[k],u);return q;}
function flags(v:Record<string,unknown>,schema:string){for(const [k,val]of Object.entries(ROOT))equal(v[k],k==='schema_version'?schema:val);}
function balances(residual:unknown,budget:unknown,units:Record<string,string>){
 const r=block(residual,units),b=block(budget,units);
 for(const [k,u]of Object.entries(units)){const bound=quantity(b[k],u);need(bound>=0&&Math.abs(quantity(r[k],u))<=bound);}
}

/** Copies the authenticated stored phase; never advances or interpolates the model. */
export function decodeGrowingGeometryRemovalFrame(value:unknown,checkpoint:unknown,descriptor:unknown,meta:Context):GrowingGeometryRemovalFrame{
 const m=closed(meta.root,ROOT_FIELDS);flags(m,ROOT.schema_version);const inputs=object(meta.inputs),original=object(meta.program),seed=object(meta.seed);
 const parent=object(meta.context),post=object(meta.postContext),postSeed=object(meta.postSeed),point=object(meta.point);
 const numerical=object(parent.numerical);finite(numerical.step_seconds);integer(numerical.step_count,1,511);
 need(numerical.step_seconds>0&&numerical.step_seconds*numerical.step_count<=600);integer(m.event_step_index,0,numerical.step_count);
 const q=closed(value,[...Object.keys(ROOT),'artifact_sha256','input_id','input_sha256','parent_context_sha256','post_context_sha256',
  'point_calculation_sha256','index','global_step_index','phase','checkpoint_sha256','sample_sha256','state_sha256','at','elapsed_seconds',
  'leaf_ids','state_layout','leaves','sample','source_rights','plant','cohorts','climate','original_curve_invariant','active_original_curve_invariant',
  'removed_last_states','original_interval_transfers','point_outflows','segment_integrated_transfers','segment_balance_residuals',
  'segment_balance_budgets','global_balance_residuals','global_balance_budgets']);flags(q,'growing-geometry-removal-replay-frame-v1');
 integer(q.index,0,numerical.step_count+1);const cut=m.event_step_index,after=q.index>cut,globalIndex=after?q.index-1:q.index;
 const phase:Phase=after?(q.index===cut+1?'after_removal_before_next_step':'post_removal_interval'):'before_removal';
 need(q.global_step_index===globalIndex&&q.phase===phase);const d=closed(descriptor,FRAME_DESCRIPTOR);
 for(const k of FRAME_DESCRIPTOR.filter(k=>!['path','sha256','bytes'].includes(k)))equal(q[k],d[k]);
 need(d.path===`frame-${q.index}.json`);digest(d.sha256);integer(d.bytes,1,2*1024**2);
 for(const k of ['artifact_sha256','input_sha256','parent_context_sha256','post_context_sha256','point_calculation_sha256','checkpoint_sha256','sample_sha256','state_sha256'])digest(q[k]);
 need(q.artifact_sha256===meta.artifact_sha256&&q.input_id===m.input_id&&inputs.input_id===m.input_id);id(q.input_id);
 for(const k of ['parent_context_sha256','post_context_sha256','point_calculation_sha256'])need(q[k]===m[k]);
 need(q.input_sha256===object(object(m.sources).inputs).sha256);rights(q.source_rights);equal(q.source_rights,m.source_rights);
 const at=closed(q.at,['time_origin_utc','elapsed_seconds_exact']);utc(m.time_origin_utc);need(at.time_origin_utc===m.time_origin_utc);
 exact(at.elapsed_seconds_exact,'s');equal(at.elapsed_seconds_exact,growingGeometryOffset(numerical.step_seconds,globalIndex));
 need(q.elapsed_seconds===globalIndex*numerical.step_seconds);
 const program=object(after?meta.postProgram:meta.program),context=after?post:parent,layout=object(context.state_layout);equal(q.state_layout,layout);
 need(Array.isArray(original.leaves)&&original.leaves.length>=2&&original.leaves.length<=512&&Array.isArray(program.leaves));
 const declarations=program.leaves.map(object),all=original.leaves.map(object),n=declarations.length;
 need(n>=1&&n<=all.length&&(numerical.step_count+2)*(115+4*all.length)<=32768);
 const ids=declarations.map(leaf=>{id(leaf.leaf_id);return leaf.leaf_id;});need(new Set(ids).size===n);equal(q.leaf_ids,ids);equal(layout.leaf_ids,ids);
 const indices=ids.map(leafId=>{const i=all.findIndex(leaf=>leaf.leaf_id===leafId);need(i>=0);return i;});
 const pointInputs=object(inputs.point_inputs);need(Array.isArray(pointInputs.events));const removedIds=pointInputs.events.map(e=>object(e).leaf_id);
 equal(ids,all.filter(leaf=>!after||!removedIds.includes(leaf.leaf_id)).map(leaf=>leaf.leaf_id));
 if(after){equal(indices,post.original_leaf_indices);equal(program,{...original,leaves:indices.map(i=>all[i])});}
 const cp=after?closed(checkpoint,['context_sha256','original_global_step_index','phase','segment_step_index','at_elapsed_seconds_exact','last_confirmed',
  'active_original_curve_invariant','original_interval_transfers','point_outflows','segment_integrated_transfers','event_snapshot_sha256',
  'original_curve_invariant_sha256','original_initial_area_receipts_sha256','removed_last_states_sha256','scope','G0_G4','version','engine_identity',
  'global_step_index','output_cursor','output_prefix_sha256','balance_residuals','balance_budgets','global_balance_residuals','global_balance_budgets','claim_scope']):
  closed(checkpoint,['version','context_sha256','step_index','output_cursor','output_prefix_sha256','last_confirmed','integrated_transfers','balance_residuals','balance_budgets']);
 digest(cp.output_prefix_sha256);
 if(after){
  need(cp.version==='growing-geometry-post-removal-continuation-checkpoint-v1'&&cp.context_sha256===m.post_context_sha256&&cp.phase===phase&&
   cp.global_step_index===globalIndex&&cp.original_global_step_index===cut&&cp.segment_step_index===q.index-cut-1&&cp.output_cursor===q.index-cut);
  need(cp.scope==='software_research_only'&&cp.claim_scope==='synthetic_post_removal_joint_continuation_only'&&cp.G0_G4==='not_assessed');
  const pins=object(m.code_sha256);equal(cp.engine_identity,{model_version:'growing-geometry-removal-next-interval-research-v1',
   code_sha256:pins['backend/app/crop_growing_geometry_removal_next_interval.py'],post_context_code_sha256:pins['backend/app/crop_growing_geometry_post_removal_context.py']});
  equal(cp.at_elapsed_seconds_exact,at.elapsed_seconds_exact);need(cp.event_snapshot_sha256===object(object(m.sources).post_snapshot).sha256);
  for(const key of ['original_curve_invariant_sha256','original_initial_area_receipts_sha256','removed_last_states_sha256'])digest(cp[key]);
 }else need(cp.version==='growing-geometry-companion-checkpoint-v1'&&cp.context_sha256===m.parent_context_sha256&&cp.step_index===globalIndex&&cp.output_cursor===q.index+1);
 const sample=closed(q.sample,['step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes']);equal(sample,cp.last_confirmed);
 need(sample.step_index===globalIndex&&sample.elapsed_seconds===q.elapsed_seconds);const state=list(sample.state,108+2*n);state.forEach(finite);
 if(q.index===0){equal(state,seed.state);equal(sample.derived,object(object(seed.evaluation).joint).derived);}
 if(q.index===cut+1){equal(sample,postSeed.last_confirmed);equal(sample.state,object(point.after).state);}
 need([...state.slice(0,3),...state.slice(4,105),state[107]].every(v=>typeof v==='number'&&v>=0));
 block(sample.derived,DERIVED);for(const key of ['curve_residuals','curve_invariant_changes'])list(sample[key],n).forEach(v=>quantity(v,'m2'));
 const receipts=list(seed.initial_area_receipts,all.length);
 list(q.leaves,n).forEach((v,i)=>{const leaf=closed(v,['leaf_id','thermal_age','area','curve_sha256','initial_area_receipt']),declaration=declarations[i]!;
  need(leaf.leaf_id===ids[i]&&leaf.curve_sha256===meta.curveHashes[ids[i]!]);digest(leaf.curve_sha256);
  const age=quantity(leaf.thermal_age,'degC_day'),area=quantity(leaf.area,'m2');
  need(age===state[108+i]&&area===state[108+n+i]&&age>=quantity(declaration.thermal_age,'degC_day')&&area>0);
  need(area<=quantity(object(object(declaration.curve).values).maximum_area,'m2'));equal(leaf.initial_area_receipt,receipts[indices[i]!]);
 });
 for(const [key,units,start]of [['plant',PLANT,0],['climate',CLIMATE,105]]as const){
  const rows=block(q[key],units);Object.entries(units).forEach(([name,unit],j)=>need(quantity(rows[name],unit)===state[start+j]));}
 const cohorts=closed(q.cohorts,Object.keys(COHORT));Object.entries(COHORT).forEach(([key,unit],j)=>{
  list(cohorts[key],50).forEach((v,k)=>need(quantity(v,unit)===state[5+j*50+k]));});
 const invariant=list(object(seed.evaluation).curve_residuals,all.length);equal(q.original_curve_invariant,invariant);
 equal(q.active_original_curve_invariant,indices.map(i=>invariant[i]));
 const units={...BALANCES,...Object.fromEntries(ids.map((_,i)=>[`leaf_age_${i}`,'degC_day']))};
 block(q.original_interval_transfers,FLUX);equal(q.original_interval_transfers,after?cp.original_interval_transfers:cp.integrated_transfers);
 balances(q.global_balance_residuals,q.global_balance_budgets,units);
 equal(q.global_balance_residuals,after?cp.global_balance_residuals:cp.balance_residuals);equal(q.global_balance_budgets,after?cp.global_balance_budgets:cp.balance_budgets);
 if(after){
  block(q.point_outflows,POINT);block(q.segment_integrated_transfers,FLUX);balances(q.segment_balance_residuals,q.segment_balance_budgets,units);
  for(const k of ['point_outflows','segment_integrated_transfers','active_original_curve_invariant'])equal(q[k],cp[k]);
  equal(q.segment_balance_residuals,cp.balance_residuals);equal(q.segment_balance_budgets,cp.balance_budgets);
  for(const k of ['point_outflows','original_interval_transfers','removed_last_states'])equal(q[k],postSeed[k]);
  equal(q.removed_last_states,point.removed_last_states);
 }else for(const key of ['point_outflows','segment_integrated_transfers','segment_balance_residuals','segment_balance_budgets','removed_last_states'])need(q[key]===null);
 const originalDescriptor=closed(list(m.samples,numerical.step_count+2)[q.index],SAMPLE_DESCRIPTOR);
 for(const k of ['index','global_step_index','phase','checkpoint_sha256','sample_sha256','state_sha256'])need(q[k]===originalDescriptor[k]);equal(at.elapsed_seconds_exact,originalDescriptor.elapsed_seconds_exact);
 return structuredClone(q)as unknown as GrowingGeometryRemovalFrame;
}

export async function loadGrowingGeometryRemovalReplay(scenario:GrowingGeometryRemovalScenario,signal:AbortSignal):Promise<GrowingGeometryRemovalReplay>{
 signal.throwIfAborted();need(Object.hasOwn(ANCHORS,scenario));const anchor=ANCHORS[scenario];
 const read=(name:string)=>{signal.throwIfAborted();return readStoredLeafFile(`./growing-geometry-removal-replay/${scenario}/`,name,signal);};
 const indexRaw=await read('index.json');need(await sha256(indexRaw)===anchor.index_sha256);
 const index=closed(parse(indexRaw),[...Object.keys(ROOT),'artifact_sha256','input_id','source_rights','exporter_sha256','sources','checkpoints','frames']);
 flags(index,'growing-geometry-removal-public-fixture-v1');need(index.artifact_sha256===anchor.artifact_sha256);rights(index.source_rights);digest(index.exporter_sha256);
 const loaded:Record<string,Uint8Array<ArrayBuffer>>={};
 for(const source of list(index.sources,17)){const d=closed(source,['role','path','sha256','bytes']);
  need(typeof d.role==='string'&&['root',...SOURCE_ROLES].includes(d.role)&&!Object.hasOwn(loaded,d.role));
  const path=d.role==='root'?'root.json':d.role==='license_notice'?'NOTICE.txt':`source-${d.role}.json`;need(d.path===path);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  const raw=await read(path);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);loaded[d.role]=raw;
 }
 need(await sha256(loaded.root!)===anchor.artifact_sha256);const m=closed(parse(loaded.root!),ROOT_FIELDS);flags(m,ROOT.schema_version);
 rights(m.source_rights);equal(m.source_rights,index.source_rights);need(m.input_id===index.input_id);utc(m.time_origin_utc);
 const sources=closed(m.sources,SOURCE_ROLES),pins=object(m.code_sha256);need(Object.keys(pins).length===31);Object.values(pins).forEach(digest);
 for(const role of SOURCE_ROLES){const d=closed(sources[role],['sha256','bytes']);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  need(loaded[role]!.byteLength===d.bytes&&await sha256(loaded[role]!)===d.sha256);}
 const context=object(parse(loaded.context!)),program=object(parse(loaded.program!)),seed=object(parse(loaded.seed!)),inputs=object(parse(loaded.inputs!));
 const postContext=object(parse(loaded.post_context!)),postProgram=parse(loaded.post_program!),postSeed=parse(loaded.post_seed!),point=object(parse(loaded.point_result!));
 need(await sha256(loaded.context!)===m.parent_context_sha256&&await sha256(loaded.post_context!)===m.post_context_sha256&&point.calculation_sha256===m.point_calculation_sha256);
 need(inputs.input_id===m.input_id&&inputs.time_origin_utc===m.time_origin_utc&&inputs.event_step_index===m.event_step_index);equal(inputs.rights,m.source_rights);
 equal(inputs.program,parse(loaded.request!));equal(inputs.program,program);equal(inputs.point_inputs,parse(loaded.point_inputs!));equal(point.inputs,inputs.point_inputs);
 for(const key of ['request','program','seed'])need(context[key+'_sha256']===object(sources[key]).sha256);
 for(const [field,role]of [['program_sha256','post_program'],['seed_sha256','post_seed'],['point_sha256','point_result'],['point_input_sha256','point_inputs']]as const)
  need(postContext[field]===object(sources[role]).sha256);
 need(postContext.parent_context_sha256===m.parent_context_sha256&&postContext.point_calculation_sha256===m.point_calculation_sha256);
 const numerical=object(context.numerical);need(numerical.step_count===anchor.frames-2&&numerical.step_seconds===inputs.step_seconds&&numerical.step_count===inputs.step_count);
 const descriptors=list(index.frames,anchor.frames),cpDescriptors=list(index.checkpoints,anchor.frames),samples=list(m.samples,anchor.frames),frames:GrowingGeometryRemovalFrame[]=[];
 need(m.initial_state_sha256===object(samples[0]).state_sha256&&m.terminal_state_sha256===object(samples.at(-1)).state_sha256);
 for(let i=0;i<anchor.frames;i++){
  const sample=closed(samples[i],SAMPLE_DESCRIPTOR),d=closed(cpDescriptors[i],[...SAMPLE_DESCRIPTOR,'path','sha256','bytes']);
  for(const key of SAMPLE_DESCRIPTOR)equal(d[key],sample[key]);
  need(d.index===i&&d.path===`checkpoint-${i}.json`&&d.sha256===d.checkpoint_sha256&&d.bytes===d.checkpoint_bytes);integer(d.bytes,1,256*1024);
  need(d.previous_checkpoint_sha256===(i?object(cpDescriptors[i-1]).checkpoint_sha256:null));
  const raw=await read(`checkpoint-${i}.json`);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);
  const descriptor=closed(descriptors[i],FRAME_DESCRIPTOR);need(descriptor.index===i&&descriptor.path===`frame-${i}.json`);integer(descriptor.bytes,1,2*1024**2);digest(descriptor.sha256);
  const dto=await read(`frame-${i}.json`);need(dto.byteLength===descriptor.bytes&&await sha256(dto)===descriptor.sha256);
  frames.push(decodeGrowingGeometryRemovalFrame(parse(dto),parse(raw),descriptor,{artifact_sha256:anchor.artifact_sha256,root:m,
   context,program,seed,postContext,postProgram,postSeed,point,inputs,curveHashes:anchor.leaf_curve_sha256}));
 }
 signal.throwIfAborted();return {scenario,artifact_sha256:anchor.artifact_sha256,frames};
}
