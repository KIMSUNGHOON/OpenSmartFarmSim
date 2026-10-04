import { need,object,closed,date,member } from './api-validation';

export const CARBON_UNIT='mg_CH2O/m2_floor';
export const LAI_UNIT='m2_leaf/m2_floor';
export const STORES=['leaf','stem_root','fruit','buffer'] as const;
export const CUMULATIVE=['photosynthesis','growth_respiration','maintenance_leaf',
  'maintenance_stem_root','maintenance_fruit','removal_leaf','removal_stem_root','removal_fruit'] as const;
export type Store=typeof STORES[number];
type Quantity<U extends string>=Readonly<{value:number;unit:U}>;
export type CropState=Readonly<Record<Store,Quantity<typeof CARBON_UNIT>> & {
  temperature_filtered_24h:Quantity<'degC'>;temperature_sum:Quantity<'degC_day'>}>;
export type CropSample=Readonly<{at:string;state:CropState;lai:Quantity<typeof LAI_UNIT>;
  cumulative:Readonly<Record<typeof CUMULATIVE[number],Quantity<typeof CARBON_UNIT>>>;
  carbon_residual:Quantity<typeof CARBON_UNIT>;carbon_residual_budget:Quantity<typeof CARBON_UNIT>}>;
export type CropFarm={scenario_id:string;scenario_revision:string;registration_sha256:string;crop_id:string};
export type CropLookup=CropFarm & {result_id:string};
export type CropEvent=Readonly<{at:string;removals:Readonly<Record<Exclude<Store,'buffer'>,Quantity<typeof CARBON_UNIT>>>;
  before:CropState;after:CropState}>;
type FailedQuantity<U extends string>=Readonly<{value:number|null;unit:U}>;
export type CropHold=Readonly<{reason_code:string;attempted_at:string;phase:string;
  time_meaning:'solver_evaluation_time';last_confirmed:CropSample|null;
  failed_state:Readonly<Record<Store,FailedQuantity<typeof CARBON_UNIT>> & {
    temperature_filtered_24h:FailedQuantity<'degC'>;temperature_sum:FailedQuantity<'degC_day'>}>}>;
export type CropManifest=Readonly<{integrator_version:'crop-rk4-research-v1';
  rate_model_version:'vanthoor-greenlight-carbon-rates-v1';domain_policy:'vanthoor-bounded-photosynthesis-v1';
  profile_id:string;profile_sha256:string;code_sha256:{integrator:string;rates:string};storage_code_sha256:string;
  input_sha256:string;raw_program_sha256:string;result_sha256:string;payload_sha256:string;notice_sha256:string;
  solver:{method:'rk4-fixed-v1';max_step_seconds:number;max_steps:number;roundoff_rule:'64-ulp-per-operation-v1'};
  time_rule:'UTC_POSIX_whole_seconds_v1';python_version:string;convergence:'not_evaluated_for_this_program';
  temperature_sum_method:'analytic_piecewise_constant_fraction_v1'}>;
export type CropReplay=Readonly<{result_id:string;recorded_at:string;study_id:string;revision:string;
  farm:CropFarm;batch_id:string;zone_id:string;farm_sha256:string;source_binding_sha256:string;
  storage_status:'stored_unpublished_research';claim_scope:'synthetic_crop_math_only';scope:'software_research_only';
  gates:'not_assessed';normalization:'per_m2_floor';profile_applicability:'unvalidated_for_registered_crop';
  temporal_provenance:'synthetic_research_program';start_utc:string;end_utc:string;status:'completed'|'hold';
  steps:number;planned_steps:number;manifest:CropManifest;samples:readonly CropSample[];
  events:readonly CropEvent[];hold:CropHold|null}>;

export const STORE_LABELS:Record<Store,string>={leaf:'잎',stem_root:'줄기·뿌리',fruit:'과실',buffer:'버퍼'};
export const STORE_COLORS:Record<Store,string>={leaf:'#367744',stem_root:'#aa8732',fruit:'#ba605a',buffer:'#658389'};
export const METRICS=['lai',...STORES] as const;
export type CropMetric=typeof METRICS[number];
export function metricValue(sample:CropSample,metric:CropMetric){
  return metric==='lai'?sample.lai.value:sample.state[metric].value;
}
export function metricUnit(metric:CropMetric){return metric==='lai'?LAI_UNIT:CARBON_UNIT;}
export function metricLabel(metric:CropMetric){return metric==='lai'?'잎 면적 지수 (LAI)':STORE_LABELS[metric]+' 탄소량';}
export function displayNumber(value:number){return new Intl.NumberFormat('ko-KR',{maximumSignificantDigits:7}).format(value);}

const NAME=/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/;
function name(v:unknown):v is string{return typeof v==='string' && NAME.test(v) && v.trim()===v;}
function digest(v:unknown):v is string{return typeof v==='string' && v.length===64 && /^[0-9a-f]{64}$/.test(v);}
function resultId(v:unknown):v is string{return typeof v==='string' && v.length===79 && /^crop-result-v1:[0-9a-f]{64}$/.test(v);}
function utc(v:unknown,whole=false):v is string{return date(v) && v.endsWith('Z') && (!whole || !v.includes('.'));}
function finite(v:unknown):v is number{return typeof v==='number' && Number.isFinite(v);}
function integer(v:unknown,min:number,max:number):v is number{return finite(v) && Number.isSafeInteger(v) && v>=min && v<=max;}
function quantity(v:unknown,unit:string,{signed=false,nullable=false}={}){
  need(object(v));closed(v,['value','unit']);
  need(v.unit===unit && (nullable && v.value===null || finite(v.value) && (signed || v.value>=0)));
}
const STATE_KEYS=[...STORES,'temperature_filtered_24h','temperature_sum'] as const;
function state(v:unknown,failed=false){
  need(object(v));closed(v,STATE_KEYS);
  for(const k of STATE_KEYS)quantity(v[k],k==='temperature_filtered_24h'?'degC':k==='temperature_sum'?'degC_day':CARBON_UNIT,
    {signed:failed,nullable:failed});
}
function sample(v:unknown):asserts v is CropSample{
  need(object(v));closed(v,['at','state','lai','cumulative','carbon_residual','carbon_residual_budget']);
  need(utc(v.at,true));state(v.state);quantity(v.lai,LAI_UNIT);
  need(object(v.cumulative));closed(v.cumulative,CUMULATIVE);
  for(const k of CUMULATIVE)quantity(v.cumulative[k],CARBON_UNIT);
  quantity(v.carbon_residual,CARBON_UNIT,{signed:true});quantity(v.carbon_residual_budget,CARBON_UNIT);
}
function manifest(v:unknown){
  need(object(v));closed(v,['integrator_version','rate_model_version','domain_policy','profile_id','profile_sha256',
    'code_sha256','storage_code_sha256','input_sha256','raw_program_sha256','result_sha256','payload_sha256',
    'notice_sha256','solver','time_rule','python_version','convergence','temperature_sum_method']);
  need(v.integrator_version==='crop-rk4-research-v1' && v.rate_model_version==='vanthoor-greenlight-carbon-rates-v1'
    && v.domain_policy==='vanthoor-bounded-photosynthesis-v1' && name(v.profile_id)
    && v.time_rule==='UTC_POSIX_whole_seconds_v1' && v.convergence==='not_evaluated_for_this_program'
    && v.temperature_sum_method==='analytic_piecewise_constant_fraction_v1'
    && typeof v.python_version==='string' && v.python_version.length<=32 && /^3\.\d+\.\d+$/.test(v.python_version)
    && v.python_version.trim()===v.python_version);
  for(const key of ['profile_sha256','storage_code_sha256','input_sha256','raw_program_sha256',
    'result_sha256','payload_sha256','notice_sha256'])need(digest(v[key]));
  need(object(v.code_sha256));closed(v.code_sha256,['integrator','rates']);
  need(digest(v.code_sha256.integrator) && digest(v.code_sha256.rates));
  need(object(v.solver));closed(v.solver,['method','max_step_seconds','max_steps','roundoff_rule']);
  need(v.solver.method==='rk4-fixed-v1' && v.solver.roundoff_rule==='64-ulp-per-operation-v1'
    && integer(v.solver.max_step_seconds,1,86400) && integer(v.solver.max_steps,1,1_000_000));
}
export function validCropLookup(v:CropLookup):boolean{
  return resultId(v.result_id) && name(v.scenario_id) && name(v.scenario_revision) && digest(v.registration_sha256) && name(v.crop_id);
}
export function decodeCropReplay(v:unknown,lookup:CropLookup):CropReplay{
  need(validCropLookup(lookup) && object(v));
  closed(v,['result_id','recorded_at','study_id','revision','farm','batch_id','zone_id','farm_sha256',
    'source_binding_sha256','storage_status','claim_scope','scope','gates','normalization','profile_applicability',
    'temporal_provenance','start_utc','end_utc','status','steps','planned_steps','manifest','samples','events','hold']);
  need(v.result_id===lookup.result_id && utc(v.recorded_at) && name(v.study_id) && name(v.revision)
    && name(v.batch_id) && name(v.zone_id) && digest(v.farm_sha256) && digest(v.source_binding_sha256));
  need(object(v.farm));closed(v.farm,['scenario_id','scenario_revision','registration_sha256','crop_id']);
  for(const key of ['scenario_id','scenario_revision','registration_sha256','crop_id'] as const)need(v.farm[key]===lookup[key]);
  need(v.storage_status==='stored_unpublished_research' && v.claim_scope==='synthetic_crop_math_only'
    && v.scope==='software_research_only' && v.gates==='not_assessed' && v.normalization==='per_m2_floor'
    && v.profile_applicability==='unvalidated_for_registered_crop' && v.temporal_provenance==='synthetic_research_program');
  need(utc(v.start_utc,true) && utc(v.end_utc,true) && Date.parse(v.start_utc)<Date.parse(v.end_utc)
    && member(v.status,['completed','hold'] as const) && integer(v.steps,0,1_000_000)
    && integer(v.planned_steps,0,1_000_000) && v.steps<=v.planned_steps);
  manifest(v.manifest);
  need(Array.isArray(v.samples) && v.samples.length<=20000 && Array.isArray(v.events) && v.events.length<=20000);
  const start=Date.parse(v.start_utc),end=Date.parse(v.end_utc);
  if(v.status==='completed'){
    need(v.hold===null && v.samples.length>=2);
    let previous=-Infinity;
    for(const row of v.samples){sample(row);const at=Date.parse(row.at);
      need(at>previous && at>=start && at<=end);previous=at;}
    need(v.samples[0].at===v.start_utc && v.samples.at(-1).at===v.end_utc);
    let eventAt=-Infinity;
    for(const event of v.events){
      need(object(event));closed(event,['at','removals','before','after']);
      need(utc(event.at,true));const at=Date.parse(event.at);need(at>=start && at<=end && at>=eventAt);eventAt=at;
      state(event.before);state(event.after);need(object(event.removals));closed(event.removals,['leaf','stem_root','fruit']);
      for(const k of ['leaf','stem_root','fruit'])quantity(event.removals[k],CARBON_UNIT);
    }
  }else{
    need(v.samples.length===0 && v.events.length===0 && object(v.hold));
    const h=v.hold;closed(h,['reason_code','attempted_at','phase','time_meaning','last_confirmed','failed_state']);
    need(member(h.reason_code,['NUMERIC_HOLD','DEPLETED_STATE_HOLD','BALANCE_HOLD','REMOVAL_EXCEEDS_STORAGE_HOLD',
      'COMPENSATION_POINT_HOLD','INPUT_HOLD','UNIT_HOLD','PROFILE_HOLD'] as const)
      && member(h.phase,['rk4-k1','rk4-k2','rk4-k3','rk4-k4','step-end','step-end-arithmetic',
        'balance','boundary','boundary-after-event','event','arithmetic'] as const)
      && h.time_meaning==='solver_evaluation_time' && utc(h.attempted_at)
      && Date.parse(h.attempted_at)>=start && Date.parse(h.attempted_at)<=end);
    state(h.failed_state,true);
    if(h.last_confirmed!==null){sample(h.last_confirmed);need(Date.parse(h.last_confirmed.at)>=start
      && Date.parse(h.last_confirmed.at)<=Date.parse(h.attempted_at));}
  }
  return v as CropReplay;
}
export function createCropReplayApi(request:(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number)=>Promise<unknown>){
  return {async cropReplay(lookup:CropLookup):Promise<CropReplay>{
    need(validCropLookup(lookup));
    const query=new URLSearchParams({scenario_id:lookup.scenario_id,scenario_revision:lookup.scenario_revision,
      registration_sha256:lookup.registration_sha256,crop_id:lookup.crop_id});
    const raw=await request('/v1/crop-research-results/'+encodeURIComponent(lookup.result_id)+'?'+query,'GET',undefined,200,64*1024*1024);
    return decodeCropReplay(raw,lookup);
  }};
}
