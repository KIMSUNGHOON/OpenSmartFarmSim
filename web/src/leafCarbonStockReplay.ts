import {sha256} from './morphologyReplay';
import {LEAF_CARBON_STOCK_FIXTURE as FIXTURE} from './leafCarbonStockReplayFixture';
import {growingGeometryOffset} from './growingGeometryReplay';
import {need,object,closed,digest,id,utc,integer,rights,exact,readStoredLeafFile,parse} from './storedLeafReplayIO';

const {scenarios:ANCHORS,code_sha256:PINS,engine_identity:IDENTITY,notice_sha256:NOTICE_SHA,exporter_sha256:EXPORTER,...ROOT}=FIXTURE;
export type LeafCarbonStockScenario=keyof typeof ANCHORS;
type Quantity={value:number;unit:string};
type Seconds={numerator:string;denominator:string;unit:'s'};
type At={time_origin_utc:string;elapsed_seconds_exact:Seconds};
type Receipt={leaf_id:string;requested_area:Quantity;canonical_area:Quantity;thermal_age:Quantity};
type Leaf={leaf_id:string;thermal_age:Quantity;area:Quantity;carbon:Quantity;curve_sha256:string;initial_area_receipt:Receipt};
type Sample={step_index:number;elapsed_seconds:number;state:number[];derived:Record<string,Quantity>;
 curve_residuals:Quantity[];curve_invariant_changes:Quantity[]};
export type LeafCarbonStockFrame=Omit<typeof ROOT,'schema_version'>&{
 schema_version:'leaf-carbon-stock-replay-frame-v1';artifact_sha256:string;input_id:string;input_sha256:string;
 context_sha256:string;checkpoint_sha256:string;sample_sha256:string;state_sha256:string;index:number;at:At;elapsed_seconds:number;
 leaf_ids:string[];state_layout:Record<string,unknown>;leaves:Leaf[];sample:Sample;source_rights:Record<string,unknown>;
 plant:Record<string,Quantity>;cohorts:Record<string,Quantity[]>;climate:Record<string,Quantity>;
 integrated_transfers:Record<string,Quantity>;balance_residuals:Record<string,Quantity>;balance_budgets:Record<string,Quantity>};
export type LeafCarbonStockReplay={scenario:LeafCarbonStockScenario;artifact_sha256:string;frames:LeafCarbonStockFrame[]};
type Context={artifact_sha256:string;root:unknown;context:unknown;program:unknown;seed:unknown;inputs:unknown;request:unknown;curveHashes:Record<string,string>};
const SOURCE_ROLES=['inputs','request','program','seed','context','growth_profile','cohort_profile','transport_profile','exchange_profile','license_notice'];
const ROOT_FIELDS=[...Object.keys(ROOT),'input_id','source_rights','time_origin_utc','sources','code_sha256','context_sha256','initial_state_sha256','terminal_state_sha256','samples'];
const SAMPLE_DESCRIPTOR=['index','elapsed_seconds_exact','checkpoint_sha256','checkpoint_bytes','sample_sha256','state_sha256','previous_checkpoint_sha256'];
const FRAME_DESCRIPTOR=['index','at','context_sha256','checkpoint_sha256','sample_sha256','state_sha256','path','sha256','bytes'];
const PLANT={buffer:'mg_CH2O/m2_floor',stem_root:'mg_CH2O/m2_floor',temperature_filtered_24h:'degC',temperature_sum:'degC_day'};
const COHORT={fruit_carbohydrate:'mg_CH2O/m2_floor',fruit_number:'fruits_equivalent/m2_floor'};
const CLIMATE={canopy_sensible_energy:'J/m2_floor',air_temperature:'degC',air_vapor_mass:'kg_water/m2_floor'};
const DERIVED={canopy_temperature:'degC',leaf_area_index:'m2_leaf/m2_floor',leaf_area_index_rate:'m2_leaf/m2_floor/s',
 canopy_capacity:'J/m2_floor/K',air_capacity:'J/m2_floor/K',air_vapor_pressure:'Pa',canopy_temperature_rate:'K/s',leaf_carbohydrate:'mg_CH2O/m2_floor'};
const FLUX:Record<string,string>={...Object.fromEntries(['photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem',
 'maintenance_fruit','removal_leaf','removal_stem','terminal_carbon'].map(k=>[k,'mg_CH2O/m2_floor'])),
 ...Object.fromEntries(['entry_number','terminal_number'].map(k=>[k,'fruits_equivalent/m2_floor'])),
 ...Object.fromEntries(['sensible','latent','incoming_heat','outgoing_heat','canopy_external','air_external'].map(k=>[k,'J/m2_floor'])),
 vapor:'kg_water/m2_floor',external_vapor:'kg_water/m2_floor',capacity_in:'J/m2_floor/K',capacity_out:'J/m2_floor/K',indoor_air_temperature_time:'degC_s'};
const BALANCES={carbohydrate:'mg_CH2O/m2_floor',number:'fruits_equivalent/m2_floor',canopy_sensible:'J/m2_floor',
 air_sensible:'J/m2_floor',vapor:'kg_water/m2_floor',area_capacity:'J/m2_floor/K',reduced_energy:'J/m2_floor'};


const SCALAR={"climate_state":{"air_temperature":"degC","air_vapor_mass":"kg_water/m2_floor","canopy_sensible_energy":"J/m2_floor"},"forcing":{"air_external_sensible_heat":"W/m2_floor","air_external_vapor":"kg_water/m2_floor/s","canopy_external_heat":"W/m2_floor","co2":"ppm","incoming_capacity_temperature":"degC","outgoing_capacity_temperature":"degC","par_above_canopy":"umol_photons/m2_floor/s"},"fruit_entry":{"fruit_entry_carbohydrate":"mg_CH2O/fruit_equivalent","fruit_number_inflow":"fruits_equivalent/m2_floor/s"},"parameters":{"air_capacity_density":"kg_air/m3","air_volume_per_floor_area":"m3/m2_floor","canopy_vapor_resistance":"s/m","leaf_heat_capacity":"J/m2_leaf/K","reference_temperature":"degC","vapor_gas_constant":"J/kg_water/K"},"plant_state":{"buffer":"mg_CH2O/m2_floor","stem_root":"mg_CH2O/m2_floor","temperature_filtered_24h":"degC","temperature_sum":"degC_day"},"removals":{"stem_root":"mg_CH2O/m2_floor/s"}};
const ARRAYS={"cohort_state":{"fruit_carbohydrate":"mg_CH2O/m2_floor","fruit_number":"fruits_equivalent/m2_floor"},"relative_growth_rate":{"fruit_relative_growth_rate":"1/s"}};
const POLICIES={"capacity_policy":"declared_outflow_plus_area_capacity_derivative_v1","leaf_stock_policy":"leaf-stocks-uniform-maintenance-explicit-removal-v1","normalization":"zero_lower_asymptote_sigmoid_v1","thermal_age_policy":"dynamic_indoor_air_no_clip_v1"};

export function isLeafCarbonStockScenario(value:unknown):value is LeafCarbonStockScenario{
 return typeof value==='string'&&Object.hasOwn(ANCHORS,value);
}
function fluxUnits(n:number):Record<string,string>{
 return {...FLUX,...Object.fromEntries(Array.from({length:n},(_,i)=>['inflow','maintenance','removal'].map(k=>[`leaf_${i}_${k}`,'mg_CH2O/m2_floor'])).flat())};
}
function seedDerived(seed:Record<string,unknown>){
 const r=object(object(seed.evaluation).stock_rhs);
 return {...object(object(object(r.source_stage).source_joint).derived),leaf_carbohydrate:object(r.leaf_totals).carbon};
}
function validateSources(meta:Context){
 const m=closed(meta.root,ROOT_FIELDS);flags(m,ROOT.schema_version);equal(m.code_sha256,PINS);digest(meta.artifact_sha256);
 const input=closed(meta.inputs,['schema_version','input_id','origin','program','rights','time_origin_utc','step_seconds','step_count']);
 need(input.schema_version==='leaf-carbon-stock-artifact-input-v1'&&input.origin==='synthetic'&&input.input_id===m.input_id);
 rights(input.rights);equal(input.rights,m.source_rights);utc(input.time_origin_utc);need(input.time_origin_utc===m.time_origin_utc);
 const p=closed(meta.program,['input_id','origin','model_floor_area','capacity_outflow','scenario','leaves',...Object.keys(POLICIES)]);
 equal(input.program,meta.request);equal(meta.request,p);need(p.input_id===m.input_id&&p.origin==='synthetic');
 for(const [k,v]of Object.entries(POLICIES))need(p[k]===v);
 need(quantity(p.model_floor_area,'m2_floor')>0&&quantity(p.capacity_outflow,'J/m2_floor/K/s')>=0);
 const scenario=closed(p.scenario,['input_id','origin',...Object.keys(SCALAR),...Object.keys(ARRAYS)]);
 need(scenario.input_id===p.input_id&&scenario.origin==='synthetic');
 for(const [k,units]of Object.entries(SCALAR))block(scenario[k],units);
 for(const [k,units]of Object.entries(ARRAYS)){
  const row=closed(scenario[k],Object.keys(units));for(const [name,unit]of Object.entries(units))list(row[name],50).forEach(v=>quantity(v,unit));
 }
 need(Array.isArray(p.leaves)&&p.leaves.length>=1&&p.leaves.length<=512);const leaves=p.leaves.map(object),n=leaves.length;
 const ids=leaves.map(l=>{id(l.leaf_id);return l.leaf_id;});need(new Set(ids).size===n);equal(Object.keys(meta.curveHashes).sort(),[...ids].sort());
 for(const leaf of leaves){
  closed(leaf,['leaf_id','curve','thermal_age','base_temperature','initial_area','initial_carbon','sink_weight','carbon_removal']);
  need(quantity(leaf.thermal_age,'degC_day')>=0&&quantity(leaf.initial_area,'m2')>0);quantity(leaf.base_temperature,'degC');
  need(quantity(leaf.initial_carbon,'mg_CH2O/m2_floor')>=0&&quantity(leaf.sink_weight,'1')>=0&&quantity(leaf.carbon_removal,'mg_CH2O/m2_floor/s')>=0);
  const curve=closed(leaf.curve,['profile_id','origin','values']);id(curve.profile_id);need(curve.origin==='synthetic');
  const v=block(curve.values,{maximum_area:'m2',steepness:'1/degC_day',inflection_age:'degC_day'});
  need(quantity(v.maximum_area,'m2')>0&&quantity(v.steepness,'1/degC_day')>0&&quantity(v.inflection_age,'degC_day')>=0);
 }
 const c=closed(meta.context,['identity','request_sha256','program_sha256','seed_sha256','numerical','state_layout','flux_units']);equal(c.identity,IDENTITY);
 const sources=closed(m.sources,SOURCE_ROLES);for(const [name,v]of Object.entries(sources)){
  const d=closed(v,['sha256','bytes']);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  if(['request','program','seed'].includes(name))need(c[name+'_sha256']===d.sha256);
 }
 need(m.context_sha256===object(sources.context).sha256&&object(sources.license_notice).sha256===NOTICE_SHA);
 for(const [k,h]of Object.entries(IDENTITY.profile_sha256))need(object(sources[k+'_profile']).sha256===h);
 const grid=closed(c.numerical,['step_seconds','step_count','duration_seconds','method','sample_scalar_budget','roundoff_rule','time_coordinate']);
 finite(grid.step_seconds);integer(grid.step_count,1,511);need(grid.step_seconds>0&&grid.step_seconds===input.step_seconds&&grid.step_count===input.step_count);
 need(grid.duration_seconds===grid.step_seconds*grid.step_count&&grid.duration_seconds>0&&grid.duration_seconds<=600&&
  grid.method==='shared-stage-fixed-rk4-individual-carbon-area-v1'&&grid.sample_scalar_budget===32768&&
  grid.roundoff_rule==='64-ulp-per-step-ledger-v1'&&grid.time_coordinate==='elapsed_seconds_no_UTC_checkpoint'&&(grid.step_count+1)*(115+5*n)<=32768);
 equal(c.flux_units,fluxUnits(n));equal(c.state_layout,{plant:Object.keys(PLANT),cohort_arrays:Object.keys(COHORT),climate:Object.keys(CLIMATE),
  leaf_ids:ids,leaf_blocks:['thermal_age','area','carbon'],units:{plant:PLANT,cohort_arrays:COHORT,climate:CLIMATE,leaf_blocks:{thermal_age:'degC_day',area:'m2',carbon:'mg_CH2O/m2_floor'}}});
 const seed=closed(meta.seed,['state','evaluation','initial_area_receipts']),receipts=list(seed.initial_area_receipts,n);
 const evaluation=closed(seed.evaluation,['stock_rhs','leaf_age_rates','leaf_area_rates','canonical_leaf_areas','curve_residuals']);
 for(const [k,unit]of [['leaf_age_rates','degC_day/s'],['leaf_area_rates','m2/s'],['canonical_leaf_areas','m2'],['curve_residuals','m2']]as const)list(evaluation[k],n).forEach(q=>quantity(q,unit));
 receipts.forEach((v,i)=>{const row=closed(v,['leaf_id','requested_area','canonical_area','thermal_age']),l=leaves[i]!;
  need(row.leaf_id===ids[i]);equal(row.requested_area,l.initial_area);equal(row.thermal_age,l.thermal_age);need(quantity(row.canonical_area,'m2')>0);
  equal(row.canonical_area,list(evaluation.canonical_leaf_areas,n)[i]);});
 const initial=[...Object.entries(PLANT).map(([k,u])=>quantity(object(scenario.plant_state)[k],u)),
  ...Object.entries(COHORT).flatMap(([k,u])=>list(object(scenario.cohort_state)[k],50).map(v=>quantity(v,u))),
  ...Object.entries(CLIMATE).map(([k,u])=>quantity(object(scenario.climate_state)[k],u)),
  ...leaves.map(l=>quantity(l.thermal_age,'degC_day')),...receipts.map(r=>quantity(object(r).canonical_area,'m2')),
  ...leaves.map(l=>quantity(l.initial_carbon,'mg_CH2O/m2_floor'))];
 equal(seed.state,initial);block(seedDerived(seed),DERIVED);
}

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

function validateFrame(value:unknown,checkpoint:unknown,descriptor:unknown,meta:Context):asserts value is LeafCarbonStockFrame{
 validateSources(meta);
 const m=closed(meta.root,ROOT_FIELDS);flags(m,ROOT.schema_version);const c=object(meta.context),p=object(meta.program),seed=object(meta.seed);
 const numerical=object(c.numerical);finite(numerical.step_seconds);integer(numerical.step_count,1,511);
 need(numerical.step_seconds>0&&numerical.step_seconds*numerical.step_count<=600);
 const q=closed(value,[...Object.keys(ROOT),'artifact_sha256','input_id','input_sha256','context_sha256','checkpoint_sha256','sample_sha256',
  'state_sha256','index','at','elapsed_seconds','leaf_ids','state_layout','leaves','sample','source_rights','plant','cohorts','climate',
  'integrated_transfers','balance_residuals','balance_budgets']);flags(q,'leaf-carbon-stock-replay-frame-v1');
 const d=closed(descriptor,FRAME_DESCRIPTOR);integer(q.index,0,numerical.step_count);need(d.index===q.index&&d.path===`frame-${q.index}.json`);
 for(const k of ['artifact_sha256','input_sha256','context_sha256','checkpoint_sha256','sample_sha256','state_sha256'])digest(q[k]);
 for(const k of ['context_sha256','checkpoint_sha256','sample_sha256','state_sha256'])need(q[k]===d[k]);
 digest(d.sha256);integer(d.bytes,1,2*1024**2);id(q.input_id);utc(m.time_origin_utc);
 need(q.artifact_sha256===meta.artifact_sha256&&q.input_id===m.input_id&&p.input_id===m.input_id&&q.context_sha256===m.context_sha256);
 need(q.input_sha256===object(object(m.sources).inputs).sha256);rights(q.source_rights);equal(q.source_rights,m.source_rights);
 const at=closed(q.at,['time_origin_utc','elapsed_seconds_exact']);need(at.time_origin_utc===m.time_origin_utc);
 exact(at.elapsed_seconds_exact,'s');equal(at.elapsed_seconds_exact,growingGeometryOffset(numerical.step_seconds,q.index));equal(q.at,d.at);
 need(q.elapsed_seconds===q.index*numerical.step_seconds);
 const layout=object(c.state_layout);equal(q.state_layout,layout);
 need(Array.isArray(p.leaves)&&p.leaves.length>=1&&p.leaves.length<=512);const declarations=p.leaves.map(object),n=declarations.length;
 const ids=declarations.map(leaf=>{id(leaf.leaf_id);return leaf.leaf_id;});need(new Set(ids).size===n);equal(q.leaf_ids,ids);equal(layout.leaf_ids,ids);
 const cp=closed(checkpoint,['version','context_sha256','step_index','output_cursor','output_prefix_sha256','last_confirmed','integrated_transfers','balance_residuals','balance_budgets']);
 need(cp.version==='individual-leaf-carbon-area-checkpoint-v1'&&cp.context_sha256===m.context_sha256&&cp.step_index===q.index&&cp.output_cursor===q.index+1);digest(cp.output_prefix_sha256);
 const sample=closed(q.sample,['step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes']);equal(sample,cp.last_confirmed);
 need(sample.step_index===q.index&&sample.elapsed_seconds===q.elapsed_seconds);const state=list(sample.state,107+3*n);state.forEach(finite);
 if(q.index===0){equal(state,seed.state);equal(sample.derived,seedDerived(seed));}
 need([...state.slice(0,2),...state.slice(3,104),state[106],...state.slice(107+2*n)].every(v=>typeof v==='number'&&v>=0));
 block(sample.derived,DERIVED);for(const key of ['curve_residuals','curve_invariant_changes'])list(sample[key],n).forEach(v=>quantity(v,'m2'));
 const receipts=list(seed.initial_area_receipts,n),leaves=list(q.leaves,n);
 leaves.forEach((v,i)=>{const leaf=closed(v,['leaf_id','thermal_age','area','carbon','curve_sha256','initial_area_receipt']),declaration=declarations[i]!;
  need(leaf.leaf_id===ids[i]&&leaf.curve_sha256===meta.curveHashes[ids[i]!]);digest(leaf.curve_sha256);
  const age=quantity(leaf.thermal_age,'degC_day'),area=quantity(leaf.area,'m2'),carbon=quantity(leaf.carbon,'mg_CH2O/m2_floor');
  need(age===state[107+i]&&area===state[107+n+i]&&carbon===state[107+2*n+i]&&carbon>=0&&age>=quantity(declaration.thermal_age,'degC_day')&&area>0);
  need(area<=quantity(object(object(declaration.curve).values).maximum_area,'m2'));equal(leaf.initial_area_receipt,receipts[i]);
 });
 for(const [key,units,start]of [['plant',PLANT,0],['climate',CLIMATE,104]] as const){
  const rows=block(q[key],units);Object.entries(units).forEach(([name,unit],j)=>need(quantity(rows[name],unit)===state[start+j]));}
 const cohorts=closed(q.cohorts,Object.keys(COHORT));Object.entries(COHORT).forEach(([key,unit],j)=>{
  list(cohorts[key],50).forEach((v,k)=>need(quantity(v,unit)===state[4+j*50+k]));});
 const balanceUnits={...BALANCES,...Object.fromEntries(ids.map((_,i)=>[`leaf_age_${i}`,'degC_day'])),
  ...Object.fromEntries(ids.map((_,i)=>[`leaf_carbon_${i}`,'mg_CH2O/m2_floor']))};
 block(q.integrated_transfers,fluxUnits(n));block(q.balance_residuals,balanceUnits);block(q.balance_budgets,balanceUnits);
 for(const k of ['integrated_transfers','balance_residuals','balance_budgets'])equal(q[k],cp[k]);
 for(const [key,unit]of Object.entries(balanceUnits)){
  const budget=quantity(object(q.balance_budgets)[key],unit);need(budget>=0&&Math.abs(quantity(object(q.balance_residuals)[key],unit))<=budget);}
 const original=object(list(m.samples,numerical.step_count+1)[q.index]);
 for(const k of ['index','checkpoint_sha256','sample_sha256','state_sha256'])need(q[k]===original[k]);equal(at.elapsed_seconds_exact,original.elapsed_seconds_exact);
 }

export function decodeLeafCarbonStockFrame(value:unknown,checkpoint:unknown,descriptor:unknown,meta:Context):LeafCarbonStockFrame{
 validateFrame(value,checkpoint,descriptor,meta);return structuredClone(value);
}

export async function loadLeafCarbonStockReplay(scenario:string,signal:AbortSignal):Promise<LeafCarbonStockReplay>{
 signal.throwIfAborted();need(isLeafCarbonStockScenario(scenario));const anchor=ANCHORS[scenario];
 const read=(name:string)=>{signal.throwIfAborted();return readStoredLeafFile(`./leaf-carbon-stock-replay/${scenario}/`,name,signal);};
 const indexRaw=await read('index.json');need(await sha256(indexRaw)===anchor.index_sha256);
 const index=closed(parse(indexRaw),[...Object.keys(ROOT),'artifact_sha256','input_id','source_rights','exporter_sha256','sources','checkpoints','frames']);
 flags(index,'leaf-carbon-stock-public-fixture-v1');need(index.artifact_sha256===anchor.artifact_sha256);rights(index.source_rights);need(index.exporter_sha256===EXPORTER);
 const sources=list(index.sources,11),loaded:Record<string,Uint8Array<ArrayBuffer>>={};
 for(const source of sources){const d=closed(source,['role','path','sha256','bytes']);need(typeof d.role==='string'&&['root',...SOURCE_ROLES].includes(d.role)&&!Object.hasOwn(loaded,d.role));
  const path=d.role==='root'?'root.json':d.role==='license_notice'?'NOTICE.txt':`source-${d.role}.json`;need(d.path===path);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  const raw=await read(path);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);loaded[d.role]=raw;
 }
 const rawRoot=loaded.root!;need(await sha256(rawRoot)===anchor.artifact_sha256);const m=closed(parse(rawRoot),ROOT_FIELDS);flags(m,ROOT.schema_version);
 equal(m.code_sha256,PINS);rights(m.source_rights);equal(m.source_rights,index.source_rights);need(m.input_id===index.input_id);utc(m.time_origin_utc);
 const rootSources=closed(m.sources,SOURCE_ROLES);
 for(const role of SOURCE_ROLES){const d=closed(rootSources[role],['sha256','bytes']);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  need(loaded[role]!.byteLength===d.bytes&&await sha256(loaded[role]!)===d.sha256);}
 const context=object(parse(loaded.context!)),program=object(parse(loaded.program!)),seed=object(parse(loaded.seed!)),input=object(parse(loaded.inputs!));
 need(object(rootSources.license_notice).sha256===NOTICE_SHA);
 const meta={artifact_sha256:anchor.artifact_sha256,root:m,context,program,seed,inputs:input,request:parse(loaded.request!),curveHashes:anchor.leaf_curve_sha256};
 validateSources(meta);
 need(await sha256(loaded.context!)===m.context_sha256&&input.input_id===m.input_id&&input.time_origin_utc===m.time_origin_utc);equal(input.rights,m.source_rights);
 equal(input.program,parse(loaded.request!));equal(input.program,program);
 for(const key of ['request','program','seed'])need(context[key+'_sha256']===object(rootSources[key]).sha256);
 const numerical=object(context.numerical);need(numerical.step_count===anchor.frames-1&&numerical.step_seconds===input.step_seconds&&numerical.step_count===input.step_count);
 const descriptors=list(index.frames,anchor.frames),cpDescriptors=list(index.checkpoints,anchor.frames),samples=list(m.samples,anchor.frames),frames:LeafCarbonStockFrame[]=[];
 need(m.initial_state_sha256===object(samples[0]).state_sha256&&m.terminal_state_sha256===object(samples.at(-1)).state_sha256);
 for(let i=0;i<anchor.frames;i++){
  const sample=closed(samples[i],SAMPLE_DESCRIPTOR),d=closed(cpDescriptors[i],[...SAMPLE_DESCRIPTOR,'path','sha256','bytes']);
  for(const key of SAMPLE_DESCRIPTOR)equal(d[key],sample[key]);
  need(d.index===i&&d.path===`checkpoint-${i}.json`&&d.sha256===d.checkpoint_sha256&&d.bytes===d.checkpoint_bytes);integer(d.bytes,1,512*1024);
  need(d.previous_checkpoint_sha256===(i?object(cpDescriptors[i-1]).checkpoint_sha256:null));
  const raw=await read(`checkpoint-${i}.json`);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);
  const descriptor=closed(descriptors[i],FRAME_DESCRIPTOR);need(descriptor.index===i&&descriptor.path===`frame-${i}.json`);integer(descriptor.bytes,1,2*1024**2);digest(descriptor.sha256);
  const dto=await read(`frame-${i}.json`);need(dto.byteLength===descriptor.bytes&&await sha256(dto)===descriptor.sha256);
  frames.push(decodeLeafCarbonStockFrame(parse(dto),parse(raw),descriptor,meta));
 }
 signal.throwIfAborted();return {scenario,artifact_sha256:anchor.artifact_sha256,frames};
}
