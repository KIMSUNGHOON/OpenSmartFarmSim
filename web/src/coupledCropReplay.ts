import { ApiError,need,object,closed,date,member } from './api-validation';
import { CARBON_UNIT,LAI_UNIT,type CropFarm } from './cropReplay';

export const FRUIT_NUMBER_UNIT='fruits_equivalent/m2_floor';
export const COUPLED_CUMULATIVE=['photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root',
  'maintenance_fruit','removal_leaf','removal_stem_root','terminal_carbohydrate','terminal_number',
  'entry_number','event_carbohydrate','event_number'] as const;
const NUMBER_CUMULATIVE=new Set<string>(['terminal_number','entry_number','event_number']);
const PROFILE_KEYS=['growth_profile','cohort_profile','transport_profile'] as const;
const CODE_KEYS=['integrator','coupled','plant','cohorts','allocation','transport'] as const;
const HASH_KEYS=['policy_sha256','artifact_code_sha256','storage_code_sha256','binding_code_sha256','input_sha256',
  'raw_program_sha256','result_sha256','artifact_sha256','payload_sha256','notice_sha256'] as const;
const HOLD_REASONS=['NUMERIC_HOLD','DEPLETED_STATE_HOLD','BALANCE_HOLD','REMOVAL_EXCEEDS_STORAGE_HOLD',
  'COMPENSATION_POINT_HOLD','INPUT_HOLD','UNIT_HOLD','PROFILE_HOLD','FRUIT_COHORT_STATE_HOLD',
  'FRUIT_COHORT_DOMAIN_HOLD','FRUIT_TRANSPORT_DOMAIN_HOLD','EMPTY_FRUIT_SINK_HOLD','FRUIT_ENTRY_BUDGET_HOLD',
  'FRUIT_ENTRY_STATE_HOLD','STATE_MISMATCH_HOLD'] as const;
const CONFIRMED_PHASES=['step-end','boundary','boundary-after-event'] as const;
const HOLD_PHASES=['rk4-k1','rk4-k2','rk4-k3','rk4-k4','step-end','step-end-arithmetic',
  'balance','boundary','boundary-after-event','event'] as const;
type Quantity<U extends string>=Readonly<{value:number;unit:U}>;
type Carbon=Quantity<typeof CARBON_UNIT>;
type FruitNumber=Quantity<typeof FRUIT_NUMBER_UNIT>;
export type CoupledCropLookup=CropFarm & {result_id:string};
export type CoupledCropState=Readonly<{buffer:Carbon;leaf:Carbon;stem_root:Carbon;
  temperature_filtered_24h:Quantity<'degC'>;temperature_sum:Quantity<'degC_day'>;
  fruit_number:readonly FruitNumber[];fruit_carbohydrate:readonly Carbon[]}>;
type NumberCumulative='terminal_number'|'entry_number'|'event_number';
export type CoupledCropCumulative=Readonly<Record<Exclude<typeof COUPLED_CUMULATIVE[number],NumberCumulative>,Carbon>
  & Record<NumberCumulative,FruitNumber>>;
export type CoupledCropSample=Readonly<{at:string;state:CoupledCropState;cumulative:CoupledCropCumulative;
  lai:Quantity<typeof LAI_UNIT>;fruit_carbohydrate_total:Carbon;
  carbon_residual:Carbon;carbon_residual_budget:Carbon;number_residual:FruitNumber;number_residual_budget:FruitNumber}>;
export type CoupledCropEvent=Readonly<{at:string;before:CoupledCropState;after:CoupledCropState;
  removed:Readonly<Pick<CoupledCropState,'leaf'|'stem_root'|'fruit_number'|'fruit_carbohydrate'>>}>;
export type CoupledCropHold=Readonly<{reason_code:typeof HOLD_REASONS[number];at:string;phase:typeof HOLD_PHASES[number];
  time_meaning:'solver_evaluation_time';last_confirmed:(CoupledCropSample & {phase:typeof CONFIRMED_PHASES[number]})|null}>;
export type CoupledCropManifest=Readonly<Record<typeof HASH_KEYS[number],string> & {
  integrator_version:'crop-plant-cohort-rk4-research-v1';
  rate_model_version:'vanthoor-greenlight-explicit-entry-plant-rates-research-v1';
  profiles:Readonly<Record<typeof PROFILE_KEYS[number],Readonly<{profile_id:string;sha256:string}>>>;
  code_sha256:Readonly<Record<typeof CODE_KEYS[number],string>>;
  solver:Readonly<{method:'rk4-fixed-v1';max_step_seconds:number;max_steps:number;roundoff_rule:'64-ulp-per-operation-v1'}>;
  time_rule:'UTC_POSIX_whole_seconds_v1';python_version:string;convergence:'not_evaluated_for_this_program';
  temperature_sum_method:'analytic_piecewise_constant_fraction_v1';
  research_assumptions:readonly ['leaf_stem_fixed_RGR_from_reference_profile_not_measured']}>;
type Page=Readonly<{offset:number;limit:number;total:number;next_offset:number|null}>;
type Shared=Readonly<{result_id:string;recorded_at:string;study_id:string;revision:string;farm:CropFarm;
  batch_id:string;zone_id:string;farm_sha256:string;source_binding_sha256:string;
  storage_status:'stored_unpublished_research';claim_scope:'synthetic_crop_math_only';scope:'software_research_only';
  gates:'not_assessed';normalization:'per_m2_floor';profile_applicability:'unvalidated_for_registered_crop';
  temporal_provenance:'synthetic_research_program';start_utc:string;end_utc:string;status:'completed'|'hold';
  steps:number;planned_steps:number;manifest:CoupledCropManifest;hold:CoupledCropHold|null}>;
export type CoupledCropPage=Shared & Readonly<{samples:readonly CoupledCropSample[];events:readonly CoupledCropEvent[];
  sample_page:Page;event_page:Page}>;
export type CoupledCropReplay=Shared & Readonly<{samples:readonly CoupledCropSample[];events:readonly CoupledCropEvent[];
  total_samples:number;total_events:number}>;
export type CoupledPageQuery=Readonly<{sample_offset:number;sample_limit:number;event_offset:number;event_limit:number}>;
export type CoupledLoadOptions=Readonly<{signal?:AbortSignal;onProgress?:(p:{pages:number;samples:number;total:number})=>void}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;

function name(v:unknown):v is string{return typeof v==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function digest(v:unknown):v is string{return typeof v==='string' && /^[0-9a-f]{64}$/.test(v);}
function finite(v:unknown):v is number{return typeof v==='number' && Number.isFinite(v);}
function integer(v:unknown,min:number,max:number):v is number{return finite(v) && Number.isSafeInteger(v) && v>=min && v<=max;}
function utc(v:unknown,whole=false):v is string{return date(v) && v.endsWith('Z') && (!whole || !v.includes('.'));}
export function utcMicroseconds(stamp:string):bigint{
  need(utc(stamp));
  const fraction=stamp.includes('.')?stamp.slice(20,-1):'';
  return BigInt(Date.parse(stamp.slice(0,19)+'Z'))*1000n+BigInt(fraction.padEnd(6,'0'));
}
function quantity(v:unknown,unit:string,signed=false){
  need(object(v));closed(v,['value','unit']);need(v.unit===unit && finite(v.value) && (signed || v.value>=0));
}
function quantities(v:unknown,unit:string){need(Array.isArray(v) && v.length===50);for(const q of v)quantity(q,unit);}
const STATE_KEYS=['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum','fruit_number','fruit_carbohydrate'] as const;
function state(v:unknown){
  need(object(v));closed(v,STATE_KEYS);
  for(const k of ['buffer','leaf','stem_root'])quantity(v[k],CARBON_UNIT);
  quantity(v.temperature_filtered_24h,'degC');quantity(v.temperature_sum,'degC_day');
  quantities(v.fruit_number,FRUIT_NUMBER_UNIT);quantities(v.fruit_carbohydrate,CARBON_UNIT);
}
function sample(v:unknown,confirmed=false):asserts v is CoupledCropSample{
  need(object(v));closed(v,['at','state','cumulative','lai','fruit_carbohydrate_total','carbon_residual',
    'carbon_residual_budget','number_residual','number_residual_budget',...(confirmed?['phase']:[])]);
  need(utc(v.at,!confirmed));if(confirmed)need(member(v.phase,CONFIRMED_PHASES));
  state(v.state);quantity(v.lai,LAI_UNIT);quantity(v.fruit_carbohydrate_total,CARBON_UNIT);
  need(object(v.cumulative));closed(v.cumulative,COUPLED_CUMULATIVE);
  for(const k of COUPLED_CUMULATIVE)quantity(v.cumulative[k],NUMBER_CUMULATIVE.has(k)?FRUIT_NUMBER_UNIT:CARBON_UNIT);
  quantity(v.carbon_residual,CARBON_UNIT,true);quantity(v.carbon_residual_budget,CARBON_UNIT);
  quantity(v.number_residual,FRUIT_NUMBER_UNIT,true);quantity(v.number_residual_budget,FRUIT_NUMBER_UNIT);
}
function event(v:unknown):asserts v is CoupledCropEvent{
  need(object(v));closed(v,['at','before','after','removed']);need(utc(v.at,true));state(v.before);state(v.after);
  need(object(v.removed));closed(v.removed,['leaf','stem_root','fruit_number','fruit_carbohydrate']);
  quantity(v.removed.leaf,CARBON_UNIT);quantity(v.removed.stem_root,CARBON_UNIT);
  quantities(v.removed.fruit_number,FRUIT_NUMBER_UNIT);quantities(v.removed.fruit_carbohydrate,CARBON_UNIT);
}
function manifest(v:unknown){
  need(object(v));closed(v,['integrator_version','rate_model_version','profiles','code_sha256',...HASH_KEYS,'solver',
    'time_rule','python_version','convergence','temperature_sum_method','research_assumptions']);
  need(v.integrator_version==='crop-plant-cohort-rk4-research-v1'
    && v.rate_model_version==='vanthoor-greenlight-explicit-entry-plant-rates-research-v1'
    && v.time_rule==='UTC_POSIX_whole_seconds_v1' && v.convergence==='not_evaluated_for_this_program'
    && v.temperature_sum_method==='analytic_piecewise_constant_fraction_v1'
    && typeof v.python_version==='string' && v.python_version.length<=32 && /^3\.\d+\.\d+$/.test(v.python_version));
  for(const k of HASH_KEYS)need(digest(v[k]));
  need(object(v.profiles));closed(v.profiles,PROFILE_KEYS);
  for(const k of PROFILE_KEYS){const p=v.profiles[k];need(object(p));closed(p,['profile_id','sha256']);need(name(p.profile_id) && digest(p.sha256));}
  need(object(v.code_sha256));closed(v.code_sha256,CODE_KEYS);for(const k of CODE_KEYS)need(digest(v.code_sha256[k]));
  need(object(v.solver));closed(v.solver,['method','max_step_seconds','max_steps','roundoff_rule']);
  need(v.solver.method==='rk4-fixed-v1' && v.solver.roundoff_rule==='64-ulp-per-operation-v1'
    && integer(v.solver.max_step_seconds,1,3600) && integer(v.solver.max_steps,1,10000));
  need(Array.isArray(v.research_assumptions) && v.research_assumptions.length===1
    && v.research_assumptions[0]==='leaf_stem_fixed_RGR_from_reference_profile_not_measured');
}
function page(v:unknown,count:number,totalMax:number,limitMax:number):asserts v is Page{
  need(object(v));closed(v,['offset','limit','total','next_offset']);
  need(integer(v.offset,0,totalMax) && integer(v.total,0,totalMax) && integer(v.limit,1,limitMax)
    && v.offset<=v.total && count===Math.min(v.limit,v.total-v.offset));
  const following=v.offset+count;need(v.next_offset===(following<v.total?following:null));
}
export { quantity as validateCropQuantity,state as validateCoupledCropState,
  event as validateCoupledCropEvent,page as validateCoupledCropPagination };
export function validCoupledCropLookup(v:CoupledCropLookup):boolean{
  return object(v) && typeof v.result_id==='string' && /^crop-result-v2:[0-9a-f]{64}$/.test(v.result_id)
    && name(v.scenario_id) && name(v.scenario_revision) && digest(v.registration_sha256) && name(v.crop_id);
}
export function decodeCoupledCropPage(v:unknown,lookup:CoupledCropLookup):CoupledCropPage{
  need(validCoupledCropLookup(lookup) && object(v));
  closed(v,['result_id','recorded_at','study_id','revision','farm','batch_id','zone_id','farm_sha256','source_binding_sha256',
    'storage_status','claim_scope','scope','gates','normalization','profile_applicability','temporal_provenance',
    'start_utc','end_utc','status','steps','planned_steps','manifest','samples','events','sample_page','event_page','hold']);
  need(v.result_id===lookup.result_id && utc(v.recorded_at) && name(v.study_id) && name(v.revision)
    && name(v.batch_id) && name(v.zone_id) && digest(v.farm_sha256) && digest(v.source_binding_sha256));
  need(object(v.farm));closed(v.farm,['scenario_id','scenario_revision','registration_sha256','crop_id']);
  for(const k of ['scenario_id','scenario_revision','registration_sha256','crop_id'] as const)need(v.farm[k]===lookup[k]);
  need(v.storage_status==='stored_unpublished_research' && v.claim_scope==='synthetic_crop_math_only'
    && v.scope==='software_research_only' && v.gates==='not_assessed' && v.normalization==='per_m2_floor'
    && v.profile_applicability==='unvalidated_for_registered_crop' && v.temporal_provenance==='synthetic_research_program');
  need(utc(v.start_utc,true) && utc(v.end_utc,true) && utcMicroseconds(v.start_utc)<utcMicroseconds(v.end_utc)
    && member(v.status,['completed','hold'] as const) && integer(v.steps,0,10000)
    && integer(v.planned_steps,1,10000) && v.steps<=v.planned_steps);
  manifest(v.manifest);
  need(Array.isArray(v.samples) && v.samples.length<=64 && Array.isArray(v.events) && v.events.length<=8);
  page(v.sample_page,v.samples.length,512,64);page(v.event_page,v.events.length,128,8);
  const start=utcMicroseconds(v.start_utc),end=utcMicroseconds(v.end_utc);
  for(const rows of [v.samples,v.events]){
    let previous:bigint|null=null;
    for(const row of rows){if(rows===v.samples)sample(row);else event(row);
      const at=utcMicroseconds(row.at);need(at>=start && at<=end && (previous===null || at>previous));previous=at;}
  }
  if(v.status==='completed')need(v.hold===null && v.steps===v.planned_steps && v.sample_page.total>=2);
  else{
    need(object(v.hold));const h=v.hold;closed(h,['reason_code','at','phase','time_meaning','last_confirmed']);
    need(member(h.reason_code,HOLD_REASONS) && member(h.phase,HOLD_PHASES)
      && h.time_meaning==='solver_evaluation_time' && utc(h.at));
    const at=utcMicroseconds(h.at);need(at>=start && at<=end
      && v.samples.every(s=>utcMicroseconds(s.at)<at) && v.events.every(e=>utcMicroseconds(e.at)<=at));
    if(h.last_confirmed!==null){sample(h.last_confirmed,true);
      need(utcMicroseconds(h.last_confirmed.at)>=start && utcMicroseconds(h.last_confirmed.at)<=at);}
  }
  return v as CoupledCropPage;
}

function shared(v:CoupledCropPage|CoupledCropReplay):Shared{
  const {samples:_samples,events:_events,...rest}=v;
  const copy={...rest} as Record<string,unknown>;
  for(const k of ['sample_page','event_page','total_samples','total_events'])delete copy[k];
  return copy as Shared;
}
function stable(v:unknown):string{
  if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
  if(object(v))return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
  return JSON.stringify(v);
}
function same(a:CoupledCropPage|CoupledCropReplay,b:CoupledCropPage|CoupledCropReplay){need(stable(shared(a))===stable(shared(b)));}
function ordered(rows:readonly {at:string}[]){for(let i=1;i<rows.length;i++)need(utcMicroseconds(rows[i-1]!.at)<utcMicroseconds(rows[i]!.at));}
export function assembleCoupledCropReplay(pages:readonly CoupledCropPage[]):CoupledCropReplay{
  need(pages.length>=1 && pages.length<=8);const first=pages[0]!;
  need(first.sample_page.offset===0 && first.sample_page.limit===64 && first.event_page.offset===0 && first.event_page.limit===8);
  const samples:CoupledCropSample[]=[];
  for(const [i,p] of pages.entries()){
    same(first,p);need(p.sample_page.offset===samples.length && p.sample_page.limit===64
      && p.sample_page.total===first.sample_page.total && p.event_page.total===first.event_page.total);
    if(i)need(p.event_page.offset===p.event_page.total && p.event_page.limit===8 && p.events.length===0);
    samples.push(...p.samples);
    need(i===pages.length-1?p.sample_page.next_offset===null:p.sample_page.next_offset===samples.length);
  }
  need(samples.length===first.sample_page.total);ordered(samples);
  if(first.status==='completed')need(samples[0]?.at===first.start_utc && samples.at(-1)?.at===first.end_utc);
  return {...shared(first),samples,events:[...first.events],total_samples:samples.length,total_events:first.event_page.total};
}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
const FIRST_QUERY:CoupledPageQuery={sample_offset:0,sample_limit:64,event_offset:0,event_limit:8};
export function createCoupledCropReplayApi(request:Request){
  async function coupledCropPage(lookup:CoupledCropLookup,query:CoupledPageQuery=FIRST_QUERY,signal?:AbortSignal):Promise<CoupledCropPage>{
    need(validCoupledCropLookup(lookup) && integer(query.sample_offset,0,512) && integer(query.sample_limit,1,64)
      && integer(query.event_offset,0,128) && integer(query.event_limit,1,8));canceled(signal);
    const search=new URLSearchParams({scenario_id:lookup.scenario_id,scenario_revision:lookup.scenario_revision,
      registration_sha256:lookup.registration_sha256,crop_id:lookup.crop_id,
      sample_offset:String(query.sample_offset),sample_limit:String(query.sample_limit),
      event_offset:String(query.event_offset),event_limit:String(query.event_limit)});
    const raw=await request('/v1/crop-coupled-research-results/'+encodeURIComponent(lookup.result_id)+'?'+search,
      'GET',undefined,200,2*1024*1024,30_000,signal);canceled(signal);
    const p=decodeCoupledCropPage(raw,lookup);
    need(p.sample_page.offset===query.sample_offset && p.sample_page.limit===query.sample_limit
      && p.event_page.offset===query.event_offset && p.event_page.limit===query.event_limit);return p;
  }
  return {coupledCropPage,
    async coupledCropReplay(lookup:CoupledCropLookup,options:CoupledLoadOptions={}):Promise<CoupledCropReplay>{
      const pages:CoupledCropPage[]=[];let query=FIRST_QUERY;
      for(;;){
        canceled(options.signal);const p=await coupledCropPage(lookup,query,options.signal);
        if(pages.length){same(pages[0]!,p);need(p.sample_page.total===pages[0]!.sample_page.total
          && p.event_page.total===pages[0]!.event_page.total && p.events.length===0);
          const previous=pages.at(-1)!;need(previous.samples.length>0 && p.samples.length>0
            && utcMicroseconds(previous.samples.at(-1)!.at)<utcMicroseconds(p.samples[0]!.at));}
        pages.push(p);need(pages.length<=8);
        options.onProgress?.({pages:pages.length,samples:p.sample_page.offset+p.samples.length,total:p.sample_page.total});
        canceled(options.signal);
        if(p.sample_page.next_offset===null){const result=assembleCoupledCropReplay(pages);canceled(options.signal);return result;}
        query={...FIRST_QUERY,sample_offset:p.sample_page.next_offset,event_offset:p.event_page.total};
      }
    },
    async coupledCropEvents(result:CoupledCropReplay,eventOffset:number,signal?:AbortSignal):Promise<CoupledCropPage>{
      const p=await coupledCropPage({result_id:result.result_id,...result.farm},
        {...FIRST_QUERY,sample_offset:result.total_samples,event_offset:eventOffset},signal);
      same(result,p);need(p.sample_page.total===result.total_samples && p.event_page.total===result.total_events
        && p.samples.length===0);return p;
    }
  };
}
