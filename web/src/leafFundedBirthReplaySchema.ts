import {LEAF_FUNDED_BIRTH_FIXTURE as FIXTURE} from './leafFundedBirthReplayFixture';
import {need,object,closed,id,integer,rights,utc} from './storedLeafReplayIO';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';

export const {scenarios:ANCHORS,code_sha256:PINS,engine_identity:IDENTITY,notice_sha256:NOTICE,
 exporter_sha256:EXPORTER,declaration_sha256:DECLARATION,...ROOT}=FIXTURE;
export type Row=Record<string,unknown>;
export type Quantity={value:number;unit:string};
export type Seconds={numerator:string;denominator:string;unit:'s'};
export type FundedLeafFrame=Omit<typeof ROOT,'schema_version'>&{
 schema_version:'funded-leaf-replay-frame-v1';artifact_sha256:string;input_id:string;input_sha256:string;
 index:number;step_index:number;event_sequence:number;phase:'root_interval'|'after_birth'|'funded_birth_interval';
 context_sha256:string;checkpoint_sha256:string;sample_sha256:string;state_sha256:string;source_rights:Row;
 at:{time_origin_utc:string;elapsed_seconds_exact:Seconds};leaf_ids:string[];state_layout:Row;
 leaves:{leaf_id:string;thermal_age:Quantity;area:Quantity;carbon:Quantity;curve_sha256:string;
  creation_receipt:Row;creation_basis:Row;attachment:{status:'separate_authored_asset_required'|'declared_not_bound';internode_id:string|null}}[];
 sample:{step_index:number;elapsed_seconds:number;state:number[];derived:Record<string,Quantity>;curve_residuals:Quantity[];curve_invariant_changes:Quantity[]};
 plant:Record<string,Quantity>;cohorts:Record<string,Quantity[]>;climate:Record<string,Quantity>;
 integrated_transfers:Record<string,Quantity>;balance_residuals:Record<string,Quantity>;balance_budgets:Record<string,Quantity>;
 segment_integrated_transfers:Record<string,Quantity>|null;point_totals:Record<string,Quantity>|null;
 global_balance_residuals:Record<string,Quantity>|null;global_balance_budgets:Record<string,Quantity>|null};
export const PLANT={buffer:'mg_CH2O/m2_floor',stem_root:'mg_CH2O/m2_floor',temperature_filtered_24h:'degC',temperature_sum:'degC_day'};
export const COHORT={fruit_carbohydrate:'mg_CH2O/m2_floor',fruit_number:'fruits_equivalent/m2_floor'};
export const CLIMATE={canopy_sensible_energy:'J/m2_floor',air_temperature:'degC',air_vapor_mass:'kg_water/m2_floor'};
const DERIVED={canopy_temperature:'degC',leaf_area_index:'m2_leaf/m2_floor',leaf_area_index_rate:'m2_leaf/m2_floor/s',
 canopy_capacity:'J/m2_floor/K',air_capacity:'J/m2_floor/K',air_vapor_pressure:'Pa',canopy_temperature_rate:'K/s',leaf_carbohydrate:'mg_CH2O/m2_floor'};
export const POINT={structural_carbon:'mg_CH2O/m2_floor',growth_respiration:'mg_CH2O/m2_floor',buffer_debit:'mg_CH2O/m2_floor',capacity_in:'J/m2_floor/K',sensible_in:'J/m2_floor'};
export const POINT_BALANCE={buffer:'mg_CH2O/m2_floor',new_stock:'mg_CH2O/m2_floor',whole_carbon:'mg_CH2O/m2_floor',sensible:'J/m2_floor',capacity:'J/m2_floor/K'};
const BALANCE={carbohydrate:'mg_CH2O/m2_floor',number:'fruits_equivalent/m2_floor',canopy_sensible:'J/m2_floor',air_sensible:'J/m2_floor',vapor:'kg_water/m2_floor',area_capacity:'J/m2_floor/K',reduced_energy:'J/m2_floor'};
const POLICIES={capacity_policy:'declared_outflow_plus_area_capacity_derivative_v1',leaf_stock_policy:'leaf-stocks-uniform-maintenance-explicit-removal-v1',normalization:'zero_lower_asymptote_sigmoid_v1',thermal_age_policy:'dynamic_indoor_air_no_clip_v1'};
const SCALAR={climate_state:CLIMATE,plant_state:PLANT,removals:{stem_root:'mg_CH2O/m2_floor/s'},
 forcing:{air_external_sensible_heat:'W/m2_floor',air_external_vapor:'kg_water/m2_floor/s',canopy_external_heat:'W/m2_floor',co2:'ppm',incoming_capacity_temperature:'degC',outgoing_capacity_temperature:'degC',par_above_canopy:'umol_photons/m2_floor/s'},
 fruit_entry:{fruit_entry_carbohydrate:'mg_CH2O/fruit_equivalent',fruit_number_inflow:'fruits_equivalent/m2_floor/s'},
 parameters:{air_capacity_density:'kg_air/m3',air_volume_per_floor_area:'m3/m2_floor',canopy_vapor_resistance:'s/m',leaf_heat_capacity:'J/m2_leaf/K',reference_temperature:'degC',vapor_gas_constant:'J/kg_water/K'}};
export function equal(a:unknown,b:unknown):void{
 if(a===b)return;
 if(Array.isArray(a)){need(Array.isArray(b)&&a.length===b.length);a.forEach((v,i)=>equal(v,b[i]));return;}
 const x=object(a),y=closed(b,Object.keys(x));for(const k of Object.keys(x))equal(x[k],y[k]);
}
export function list(v:unknown,length?:number):unknown[]{need(Array.isArray(v)&&(length===undefined||v.length===length));return v;}
export function finite(v:unknown):asserts v is number{need(typeof v==='number'&&Number.isFinite(v));}
export function quantity(v:unknown,unit:string){const q=closed(v,['value','unit']);finite(q.value);need(q.unit===unit);return q.value;}
export function block(v:unknown,units:Record<string,string>){const q=closed(v,Object.keys(units));for(const [k,u]of Object.entries(units))quantity(q[k],u);return q;}
export function flags(v:Row,schema:string){for(const [k,val]of Object.entries(ROOT))equal(v[k],k==='schema_version'?schema:val);}
export function fluxUnits(n:number):Record<string,string>{return {
 ...Object.fromEntries(['photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem','maintenance_fruit','removal_leaf','removal_stem','terminal_carbon'].map(k=>[k,'mg_CH2O/m2_floor'])),
 ...Object.fromEntries(['entry_number','terminal_number'].map(k=>[k,'fruits_equivalent/m2_floor'])),
 ...Object.fromEntries(['sensible','latent','incoming_heat','outgoing_heat','canopy_external','air_external'].map(k=>[k,'J/m2_floor'])),
 vapor:'kg_water/m2_floor',external_vapor:'kg_water/m2_floor',capacity_in:'J/m2_floor/K',capacity_out:'J/m2_floor/K',indoor_air_temperature_time:'degC_s',
 ...Object.fromEntries(Array.from({length:n},(_,i)=>['inflow','maintenance','removal'].map(k=>[`leaf_${i}_${k}`,'mg_CH2O/m2_floor'])).flat())};}
export function balances(cp:Row,n:number,global=false){
 const units:Record<string,string>={...BALANCE};for(let i=0;i<n;i++){units[`leaf_age_${i}`]='degC_day';units[`leaf_carbon_${i}`]='mg_CH2O/m2_floor';}
 const r=block(cp[global?'global_balance_residuals':'balance_residuals'],units),b=block(cp[global?'global_balance_budgets':'balance_budgets'],units);
 for(const [k,u]of Object.entries(units))need(quantity(b[k],u)>=0&&Math.abs(quantity(r[k],u))<=quantity(b[k],u));
}
export type ProgramInfo={program:Row;leaves:Row[];curveHashes:string[];areaCurveHashes:string[];layout:Row};
export async function programInfo(raw:string):Promise<ProgramInfo>{
 const p=closed(JSON.parse(raw),['input_id','origin','model_floor_area','capacity_outflow','scenario','leaves',...Object.keys(POLICIES)]);
 id(p.input_id);need(p.origin==='synthetic');for(const [k,v]of Object.entries(POLICIES))need(p[k]===v);
 need(quantity(p.model_floor_area,'m2_floor')>0&&quantity(p.capacity_outflow,'J/m2_floor/K/s')>=0);
 const scenario=closed(p.scenario,['input_id','origin',...Object.keys(SCALAR),'cohort_state','relative_growth_rate']);
 need(scenario.input_id===p.input_id&&scenario.origin==='synthetic');for(const [k,u]of Object.entries(SCALAR))block(scenario[k],u);
 const arrays={cohort_state:COHORT,relative_growth_rate:{fruit_relative_growth_rate:'1/s'}};
 for(const [k,units]of Object.entries(arrays)){const row=closed(scenario[k],Object.keys(units));for(const [name,u]of Object.entries(units))list(row[name],50).forEach(v=>quantity(v,u));}
 const leaves=list(p.leaves).map(object);need(leaves.length>=1&&leaves.length<=512);const ids=leaves.map(l=>{id(l.leaf_id);return l.leaf_id;});need(new Set(ids).size===ids.length);
 const originals=wireItems(wireFields(raw).leaves!),curveHashes:string[]=[],areaCurveHashes:string[]=[];
 for(const [i,leaf]of leaves.entries()){
  closed(leaf,['leaf_id','curve','thermal_age','base_temperature','initial_area','initial_carbon','sink_weight','carbon_removal']);
  need(quantity(leaf.thermal_age,'degC_day')>=0&&quantity(leaf.initial_area,'m2')>0&&quantity(leaf.initial_carbon,'mg_CH2O/m2_floor')>=0);
  quantity(leaf.base_temperature,'degC');need(quantity(leaf.sink_weight,'1')>=0&&quantity(leaf.carbon_removal,'mg_CH2O/m2_floor/s')>=0);
  const c=closed(leaf.curve,['profile_id','origin','values']);id(c.profile_id);need(c.origin==='synthetic');
  const v=block(c.values,{maximum_area:'m2',steepness:'1/degC_day',inflection_age:'degC_day'});
  need(quantity(v.maximum_area,'m2')>0&&quantity(v.steepness,'1/degC_day')>0&&quantity(v.inflection_age,'degC_day')>=0);
  const curveRaw=wireFields(originals[i]!).curve!;curveHashes.push(await wireHash(curveRaw));
  areaCurveHashes.push(await wireHash('{"curve":'+curveRaw+',"rate_model_version":"leaf-logistic-thermal-area-rate-research-v1"}'));
 }
 const layout={plant:Object.keys(PLANT),cohort_arrays:Object.keys(COHORT),climate:Object.keys(CLIMATE),leaf_ids:ids,leaf_blocks:['thermal_age','area','carbon'],
  units:{plant:PLANT,cohort_arrays:COHORT,climate:CLIMATE,leaf_blocks:{thermal_age:'degC_day',area:'m2',carbon:'mg_CH2O/m2_floor'}}};
 return {program:p,leaves,curveHashes,areaCurveHashes,layout};
}
export function sample(value:unknown,info:ProgramInfo,step:number,dt:number){
 const q=closed(value,['step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes']);
 need(q.step_index===step&&q.elapsed_seconds===step*dt);const n=info.leaves.length,y=list(q.state,107+3*n);y.forEach(finite);
 need([...y.slice(0,2),...y.slice(3,104),y[106],...y.slice(107+2*n)].every(v=>typeof v==='number'&&v>=0));
 info.leaves.forEach((leaf,i)=>{
  const age=y[107+i];need(typeof age==='number'&&age>=quantity(leaf.thermal_age,'degC_day'));
  const a=y[107+n+i];need(typeof a==='number'&&a>0&&a<=quantity(object(object(leaf.curve).values).maximum_area,'m2'));
 });
 block(q.derived,DERIVED);for(const k of ['curve_residuals','curve_invariant_changes'])list(q[k],n).forEach(v=>quantity(v,'m2'));return q;
}
export function rootSeed(value:unknown,info:ProgramInfo){
 const seed=closed(value,['state','evaluation','initial_area_receipts']),n=info.leaves.length,s=object(info.program.scenario);
 const e=closed(seed.evaluation,['stock_rhs','leaf_age_rates','leaf_area_rates','canonical_leaf_areas','curve_residuals']);
 for(const [k,u]of [['leaf_age_rates','degC_day/s'],['leaf_area_rates','m2/s'],['canonical_leaf_areas','m2'],['curve_residuals','m2']]as const)list(e[k],n).forEach(v=>quantity(v,u));
 const receipts=list(seed.initial_area_receipts,n).map((v,i)=>{
  const r=closed(v,['leaf_id','requested_area','canonical_area','thermal_age']),leaf=info.leaves[i]!;
  need(r.leaf_id===leaf.leaf_id&&quantity(r.canonical_area,'m2')>0);equal(r.requested_area,leaf.initial_area);equal(r.thermal_age,leaf.thermal_age);equal(r.canonical_area,list(e.canonical_leaf_areas,n)[i]);return {kind:'initial',value:r};
 });
 const initial=[...Object.entries(PLANT).map(([k,u])=>quantity(object(s.plant_state)[k],u)),
  ...Object.entries(COHORT).flatMap(([k,u])=>list(object(s.cohort_state)[k],50).map(v=>quantity(v,u))),
  ...Object.entries(CLIMATE).map(([k,u])=>quantity(object(s.climate_state)[k],u)),...info.leaves.map(l=>quantity(l.thermal_age,'degC_day')),
  ...receipts.map(r=>quantity(r.value.canonical_area,'m2')),...info.leaves.map(l=>quantity(l.initial_carbon,'mg_CH2O/m2_floor'))];
 equal(seed.state,initial);return {seed,receipts};
}
export function frame(value:unknown,cp:Row,d:Row,root:Row,artifact:string,info:ProgramInfo,receipts:Row[],bases:Row[]):FundedLeafFrame{
 const q=closed(value,[...Object.keys(ROOT),'artifact_sha256','input_id','input_sha256','source_rights','index','step_index','phase','event_sequence','context_sha256','checkpoint_sha256','sample_sha256','state_sha256','at','leaf_ids','state_layout','leaves','sample','plant','cohorts','climate','integrated_transfers','balance_residuals','balance_budgets','segment_integrated_transfers','point_totals','global_balance_residuals','global_balance_budgets']);
 flags(q,'funded-leaf-replay-frame-v1');need(q.artifact_sha256===artifact&&q.input_id===root.input_id&&q.input_sha256===object(object(root.sources).inputs).sha256);
 rights(q.source_rights);equal(q.source_rights,root.source_rights);
 for(const key of ['index','step_index','phase','event_sequence','context_sha256','checkpoint_sha256','sample_sha256','state_sha256'])equal(q[key],d[key]);
 const at=closed(q.at,['time_origin_utc','elapsed_seconds_exact']);utc(at.time_origin_utc);equal(at,{time_origin_utc:root.time_origin_utc,elapsed_seconds_exact:d.elapsed_seconds_exact});
 equal(q.state_layout,info.layout);equal(q.leaf_ids,info.layout.leaf_ids);equal(q.sample,cp.last_confirmed);
 const y=list(object(q.sample).state),n=info.leaves.length;
 list(q.leaves,n).forEach((v,i)=>{
  const leaf=closed(v,['leaf_id','thermal_age','area','carbon','curve_sha256','creation_receipt','creation_basis','attachment']),receipt=receipts[i]!;
  need(leaf.leaf_id===info.leaves[i]!.leaf_id&&leaf.curve_sha256===info.curveHashes[i]);
  need(quantity(leaf.thermal_age,'degC_day')===y[107+i]&&quantity(leaf.area,'m2')===y[107+n+i]&&quantity(leaf.carbon,'mg_CH2O/m2_floor')===y[107+2*n+i]);
  equal(leaf.creation_receipt,receipt);equal(leaf.creation_basis,bases[i]);
  equal(leaf.attachment,receipt.kind==='initial'?{status:'separate_authored_asset_required',internode_id:null}:{status:'declared_not_bound',internode_id:object(receipt.value).attachment_internode_id});
 });
 for(const [key,units,start]of [['plant',PLANT,0],['climate',CLIMATE,104]]as const){const row=block(q[key],units);Object.entries(units).forEach(([k,u],j)=>need(quantity(row[k],u)===y[start+j]));}
 const cohorts=closed(q.cohorts,Object.keys(COHORT));Object.entries(COHORT).forEach(([k,u],j)=>list(cohorts[k],50).forEach((v,i)=>need(quantity(v,u)===y[4+j*50+i])));
 for(const k of ['integrated_transfers','balance_residuals','balance_budgets','segment_integrated_transfers','point_totals','global_balance_residuals','global_balance_budgets'])equal(q[k],cp[k]??null);
 return structuredClone(q) as unknown as FundedLeafFrame;
}
export function grid(value:unknown,input:Row,n:number){
 const g=closed(value,['step_seconds','step_count','duration_seconds','method','sample_scalar_budget','roundoff_rule','time_coordinate']);
 finite(g.step_seconds);integer(g.step_count,1,510);need(g.step_seconds>0&&g.step_seconds===input.step_seconds&&g.step_count===input.step_count);
 need(g.duration_seconds===g.step_seconds*g.step_count&&g.duration_seconds>0&&g.duration_seconds<=600&&(g.step_count+1)*(115+5*n)<=32768);
 need(g.method==='shared-stage-fixed-rk4-individual-carbon-area-v1'&&g.sample_scalar_budget===32768&&g.roundoff_rule==='64-ulp-per-step-ledger-v1'&&g.time_coordinate==='elapsed_seconds_no_UTC_checkpoint');
 return {dt:g.step_seconds,count:g.step_count};
}
