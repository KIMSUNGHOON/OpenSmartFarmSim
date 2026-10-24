import {sha256} from './morphologyReplay';
import {GROWING_GEOMETRY_FIXTURE as FIXTURE} from './growingGeometryReplayFixture';
import {need,object,closed,digest,id,utc,integer,rights,exact,readStoredLeafFile,parse} from './storedLeafReplayIO';

const {scenarios:ANCHORS,...ROOT}=FIXTURE;
export type GrowingGeometryScenario=keyof typeof ANCHORS;
type Quantity={value:number;unit:string};
type Seconds={numerator:string;denominator:string;unit:'s'};
type At={time_origin_utc:string;elapsed_seconds_exact:Seconds};
type Receipt={leaf_id:string;requested_area:Quantity;canonical_area:Quantity;thermal_age:Quantity};
type Leaf={leaf_id:string;thermal_age:Quantity;area:Quantity;curve_sha256:string;initial_area_receipt:Receipt};
type Sample={step_index:number;elapsed_seconds:number;state:number[];derived:Record<string,Quantity>;
 curve_residuals:Quantity[];curve_invariant_changes:Quantity[]};
export type GrowingGeometryFrame=Omit<typeof ROOT,'schema_version'>&{
 schema_version:'growing-geometry-replay-frame-v1';artifact_sha256:string;input_id:string;input_sha256:string;
 context_sha256:string;checkpoint_sha256:string;sample_sha256:string;state_sha256:string;index:number;at:At;elapsed_seconds:number;
 leaf_ids:string[];state_layout:Record<string,unknown>;leaves:Leaf[];sample:Sample;source_rights:Record<string,unknown>;
 plant:Record<string,Quantity>;cohorts:Record<string,Quantity[]>;climate:Record<string,Quantity>;
 integrated_transfers:Record<string,Quantity>;balance_residuals:Record<string,Quantity>;balance_budgets:Record<string,Quantity>};
export type GrowingGeometryReplay={scenario:GrowingGeometryScenario;artifact_sha256:string;frames:GrowingGeometryFrame[]};
type Context={artifact_sha256:string;root:unknown;context:unknown;program:unknown;seed:unknown};
const SOURCE_ROLES=['inputs','request','program','seed','context','growth_profile','cohort_profile','transport_profile','exchange_profile','license_notice'];
const ROOT_FIELDS=[...Object.keys(ROOT),'input_id','source_rights','time_origin_utc','sources','code_sha256','context_sha256','initial_state_sha256','terminal_state_sha256','samples'];
const SAMPLE_DESCRIPTOR=['index','elapsed_seconds_exact','checkpoint_sha256','checkpoint_bytes','sample_sha256','state_sha256','previous_checkpoint_sha256'];
const FRAME_DESCRIPTOR=['index','at','context_sha256','checkpoint_sha256','sample_sha256','state_sha256','path','sha256','bytes'];
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

/** Exact display grid from the stored binary64 step; no crop calculation. */
export function growingGeometryOffset(dt:number,index:number):Seconds{
 finite(dt);need(dt>0);integer(index,0,511);
 const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,dt);const bits=view.getBigUint64(0);
 const exponent=Number((bits>>52n)&2047n),mantissa=(bits&((1n<<52n)-1n))|(exponent?1n<<52n:0n),power=exponent?exponent-1075:-1074;
 let n=mantissa*BigInt(index),d=1n;if(power>=0)n<<=BigInt(power);else d<<=BigInt(-power);
 let a=n,b=d;while(b){const r=a%b;a=b;b=r;}n/=a;d/=a;
 return {numerator:String(n),denominator:String(d),unit:'s'};
}

export function decodeGrowingGeometryFrame(value:unknown,checkpoint:unknown,descriptor:unknown,meta:Context):GrowingGeometryFrame{
 const m=closed(meta.root,ROOT_FIELDS);flags(m,ROOT.schema_version);const c=object(meta.context),p=object(meta.program),seed=object(meta.seed);
 const numerical=object(c.numerical);finite(numerical.step_seconds);integer(numerical.step_count,1,511);
 need(numerical.step_seconds>0&&numerical.step_seconds*numerical.step_count<=600);
 const q=closed(value,[...Object.keys(ROOT),'artifact_sha256','input_id','input_sha256','context_sha256','checkpoint_sha256','sample_sha256',
  'state_sha256','index','at','elapsed_seconds','leaf_ids','state_layout','leaves','sample','source_rights','plant','cohorts','climate',
  'integrated_transfers','balance_residuals','balance_budgets']);flags(q,'growing-geometry-replay-frame-v1');
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
 need(cp.version==='growing-geometry-companion-checkpoint-v1'&&cp.context_sha256===m.context_sha256&&cp.step_index===q.index&&cp.output_cursor===q.index+1);digest(cp.output_prefix_sha256);
 const sample=closed(q.sample,['step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes']);equal(sample,cp.last_confirmed);
 need(sample.step_index===q.index&&sample.elapsed_seconds===q.elapsed_seconds);const state=list(sample.state,108+2*n);state.forEach(finite);
 if(q.index===0){equal(state,seed.state);equal(sample.derived,object(object(seed.evaluation).joint).derived);}
 need([...state.slice(0,3),...state.slice(4,105),state[107]].every(v=>typeof v==='number'&&v>=0));
 block(sample.derived,DERIVED);for(const key of ['curve_residuals','curve_invariant_changes'])list(sample[key],n).forEach(v=>quantity(v,'m2'));
 const receipts=list(seed.initial_area_receipts,n),leaves=list(q.leaves,n);
 leaves.forEach((v,i)=>{const leaf=closed(v,['leaf_id','thermal_age','area','curve_sha256','initial_area_receipt']),declaration=declarations[i]!;
  need(leaf.leaf_id===ids[i]);digest(leaf.curve_sha256);
  const age=quantity(leaf.thermal_age,'degC_day'),area=quantity(leaf.area,'m2');
  need(age===state[108+i]&&area===state[108+n+i]&&age>=quantity(declaration.thermal_age,'degC_day')&&area>0);
  need(area<=quantity(object(object(declaration.curve).values).maximum_area,'m2'));equal(leaf.initial_area_receipt,receipts[i]);
 });
 for(const [key,units,start]of [['plant',PLANT,0],['climate',CLIMATE,105]] as const){
  const rows=block(q[key],units);Object.entries(units).forEach(([name,unit],j)=>need(quantity(rows[name],unit)===state[start+j]));}
 const cohorts=closed(q.cohorts,Object.keys(COHORT));Object.entries(COHORT).forEach(([key,unit],j)=>{
  list(cohorts[key],50).forEach((v,k)=>need(quantity(v,unit)===state[5+j*50+k]));});
 const balanceUnits={...BALANCES,...Object.fromEntries(ids.map((_,i)=>[`leaf_age_${i}`,'degC_day']))};
 block(q.integrated_transfers,FLUX);block(q.balance_residuals,balanceUnits);block(q.balance_budgets,balanceUnits);
 for(const k of ['integrated_transfers','balance_residuals','balance_budgets'])equal(q[k],cp[k]);
 for(const [key,unit]of Object.entries(balanceUnits)){
  const budget=quantity(object(q.balance_budgets)[key],unit);need(budget>=0&&Math.abs(quantity(object(q.balance_residuals)[key],unit))<=budget);}
 const original=object(list(m.samples,numerical.step_count+1)[q.index]);
 for(const k of ['index','checkpoint_sha256','sample_sha256','state_sha256'])need(q[k]===original[k]);equal(at.elapsed_seconds_exact,original.elapsed_seconds_exact);
 return structuredClone(q) as unknown as GrowingGeometryFrame;
}

export async function loadGrowingGeometryReplay(scenario:GrowingGeometryScenario,signal:AbortSignal):Promise<GrowingGeometryReplay>{
 signal.throwIfAborted();need(Object.hasOwn(ANCHORS,scenario));const anchor=ANCHORS[scenario];
 const read=(name:string)=>{signal.throwIfAborted();return readStoredLeafFile(`./growing-geometry-replay/${scenario}/`,name,signal);};
 const indexRaw=await read('index.json');need(await sha256(indexRaw)===anchor.index_sha256);
 const index=closed(parse(indexRaw),[...Object.keys(ROOT),'artifact_sha256','input_id','source_rights','exporter_sha256','sources','checkpoints','frames']);
 flags(index,'growing-geometry-public-fixture-v1');need(index.artifact_sha256===anchor.artifact_sha256);rights(index.source_rights);digest(index.exporter_sha256);
 const sources=list(index.sources,11),loaded:Record<string,Uint8Array<ArrayBuffer>>={};
 for(const source of sources){const d=closed(source,['role','path','sha256','bytes']);need(typeof d.role==='string'&&['root',...SOURCE_ROLES].includes(d.role)&&!Object.hasOwn(loaded,d.role));
  const path=d.role==='root'?'root.json':d.role==='license_notice'?'NOTICE.txt':`source-${d.role}.json`;need(d.path===path);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  const raw=await read(path);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);loaded[d.role]=raw;
 }
 const rawRoot=loaded.root!;need(await sha256(rawRoot)===anchor.artifact_sha256);const m=closed(parse(rawRoot),ROOT_FIELDS);flags(m,ROOT.schema_version);
 rights(m.source_rights);equal(m.source_rights,index.source_rights);need(m.input_id===index.input_id);utc(m.time_origin_utc);
 const rootSources=closed(m.sources,SOURCE_ROLES);
 for(const role of SOURCE_ROLES){const d=closed(rootSources[role],['sha256','bytes']);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  need(loaded[role]!.byteLength===d.bytes&&await sha256(loaded[role]!)===d.sha256);}
 const context=object(parse(loaded.context!)),program=object(parse(loaded.program!)),seed=object(parse(loaded.seed!)),input=object(parse(loaded.inputs!));
 need(await sha256(loaded.context!)===m.context_sha256&&input.input_id===m.input_id&&input.time_origin_utc===m.time_origin_utc);equal(input.rights,m.source_rights);
 equal(input.program,parse(loaded.request!));equal(input.program,program);
 for(const key of ['request','program','seed'])need(context[key+'_sha256']===object(rootSources[key]).sha256);
 const numerical=object(context.numerical);need(numerical.step_count===anchor.frames-1&&numerical.step_seconds===input.step_seconds&&numerical.step_count===input.step_count);
 const descriptors=list(index.frames,anchor.frames),cpDescriptors=list(index.checkpoints,anchor.frames),samples=list(m.samples,anchor.frames),frames:GrowingGeometryFrame[]=[];
 for(let i=0;i<anchor.frames;i++){
  const sample=closed(samples[i],SAMPLE_DESCRIPTOR),d=closed(cpDescriptors[i],[...SAMPLE_DESCRIPTOR,'path','sha256','bytes']);
  for(const key of SAMPLE_DESCRIPTOR)equal(d[key],sample[key]);
  need(d.index===i&&d.path===`checkpoint-${i}.json`&&d.sha256===d.checkpoint_sha256&&d.bytes===d.checkpoint_bytes);integer(d.bytes,1,256*1024);
  need(d.previous_checkpoint_sha256===(i?object(cpDescriptors[i-1]).checkpoint_sha256:null));
  const raw=await read(`checkpoint-${i}.json`);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);
  const descriptor=closed(descriptors[i],FRAME_DESCRIPTOR);need(descriptor.index===i&&descriptor.path===`frame-${i}.json`);integer(descriptor.bytes,1,2*1024**2);digest(descriptor.sha256);
  const dto=await read(`frame-${i}.json`);need(dto.byteLength===descriptor.bytes&&await sha256(dto)===descriptor.sha256);
  frames.push(decodeGrowingGeometryFrame(parse(dto),parse(raw),descriptor,{artifact_sha256:anchor.artifact_sha256,root:m,context,program,seed}));
 }
 signal.throwIfAborted();return {scenario,artifact_sha256:anchor.artifact_sha256,frames};
}
