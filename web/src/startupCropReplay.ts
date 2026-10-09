import { ApiError,need,object,closed,date,member } from './api-validation';
import { CARBON_UNIT,LAI_UNIT,type CropFarm } from './cropReplay';
import { FRUIT_NUMBER_UNIT,COUPLED_CUMULATIVE,utcMicroseconds,
  validateCropQuantity as quantity,validateCoupledCropState as state,
  validateCoupledCropEvent as event,validateCoupledCropPagination as page,
  type CoupledCropSample,type CoupledCropCumulative,type CoupledCropManifest,
  type CoupledCropHold,type CoupledCropPage,type CoupledCropEvent } from './coupledCropReplay';

export const STARTUP_CUMULATIVE=[...COUPLED_CUMULATIVE,'requested_fruit_carbohydrate',
  'realized_fruit_carbohydrate','deferred_fruit_carbohydrate','fruit_growth_respiration'] as const;
export const STARTUP_ASSUMPTIONS=[
  'entry_number_and_mass_are_explicit_not_automatic_fruit_set',
  'empty_tail_deferral_not_a_validated_sink_capacity_model',
  'discontinuous_startup_has_no_fourth_order_claim',
  'approximately_8_52_percent_small_cohort_error_observed_in_synthetic_test',
] as const;
const PROFILE_KEYS=['growth_profile','cohort_profile','transport_profile'] as const;
const CODE_KEYS=['integrator','coupled','startup','plant','cohorts','allocation','transport','legacy_helpers','original_rates'] as const;
const HASH_KEYS=['policy_sha256','allocation_policy_sha256','artifact_code_sha256','storage_code_sha256','binding_code_sha256',
  'input_sha256','raw_program_sha256','result_sha256','artifact_sha256','payload_sha256','notice_sha256'] as const;
const DIAGNOSTICS=['requested_residual','requested_budget','growth_respiration_residual','growth_respiration_budget'] as const;
const HOLD_REASONS=['NUMERIC_HOLD','DEPLETED_STATE_HOLD','BALANCE_HOLD','REMOVAL_EXCEEDS_STORAGE_HOLD',
  'COMPENSATION_POINT_HOLD','INPUT_HOLD','UNIT_HOLD','PROFILE_HOLD','FRUIT_COHORT_STATE_HOLD',
  'FRUIT_COHORT_DOMAIN_HOLD','FRUIT_TRANSPORT_DOMAIN_HOLD','EMPTY_FRUIT_SINK_HOLD','FRUIT_ENTRY_BUDGET_HOLD',
  'FRUIT_ENTRY_STATE_HOLD','STATE_MISMATCH_HOLD'] as const;
const CONFIRMED_PHASES=['step-end','boundary','boundary-after-event'] as const;
const HOLD_PHASES=['rk4-k1','rk4-k2','rk4-k3','rk4-k4','step-end','step-end-arithmetic',
  'balance','boundary','boundary-after-event','event'] as const;
type Carbon=CoupledCropSample['carbon_residual'];
export type StartupCropLookup=CropFarm & Readonly<{result_id:string}>;
export type StartupCropSample=Omit<CoupledCropSample,'cumulative'> & Readonly<{
  cumulative:CoupledCropCumulative & Readonly<Record<'requested_fruit_carbohydrate'|'realized_fruit_carbohydrate'
    |'deferred_fruit_carbohydrate'|'fruit_growth_respiration',Carbon>>;
  startup_diagnostics:Readonly<Record<typeof DIAGNOSTICS[number],Carbon>>}>;
export type StartupCropHold=Omit<CoupledCropHold,'last_confirmed'> & Readonly<{
  last_confirmed:(StartupCropSample & Readonly<{phase:typeof CONFIRMED_PHASES[number]}>)|null}>;
export type StartupCropManifest=Omit<CoupledCropManifest,'integrator_version'|'rate_model_version'|'code_sha256'> & Readonly<{
  program_version:'crop-plant-startup-program-v1';integrator_version:'crop-plant-startup-rk4-research-v1';
  rate_model_version:'explicit-entry-empty-sink-plant-rates-research-v1';allocation_policy_sha256:string;
  artifact_dependency_sha256:Readonly<Record<'legacy_artifact'|'canonical_json',string>>;
  code_sha256:Readonly<Record<typeof CODE_KEYS[number],string>>;
  startup_transition:'zero_or_positive_tail_research_only_not_validated_sink_capacity';
  startup_balance_rule:'64-ulp-per-operation-without-absolute-floor-v1';startup_assumptions:typeof STARTUP_ASSUMPTIONS}>;
type Shared=Omit<CoupledCropPage,'samples'|'events'|'sample_page'|'event_page'|'manifest'|'hold'> & Readonly<{
  schema_version:'crop-startup-replay-v1';floor_area:Readonly<{value:string;unit:'m²'}>;
  manifest:StartupCropManifest;hold:StartupCropHold|null}>;
export type StartupCropPage=Shared & Readonly<{samples:readonly StartupCropSample[];events:readonly CoupledCropEvent[];
  sample_page:CoupledCropPage['sample_page'];event_page:CoupledCropPage['event_page']}>;
export type StartupCropReplay=Shared & Readonly<{samples:readonly StartupCropSample[];events:readonly CoupledCropEvent[];
  total_samples:number;total_events:number}>;
export type StartupPageQuery=Readonly<{sample_offset:number;sample_limit:number;event_offset:number;event_limit:number}>;
export type StartupLoadOptions=Readonly<{signal?:AbortSignal;
  onProgress?:(p:{pages:number;samples:number;total:number;events:number;total_events:number})=>void}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;

function name(v:unknown):v is string{return typeof v==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function digest(v:unknown):v is string{return typeof v==='string' && /^[0-9a-f]{64}$/.test(v);}
function integer(v:unknown,min:number,max:number):v is number{return typeof v==='number' && Number.isSafeInteger(v) && v>=min && v<=max;}
function utc(v:unknown,whole=false):v is string{return date(v) && v.endsWith('Z') && (!whole || !v.includes('.'));}
export function validStartupCropLookup(v:StartupCropLookup):boolean{
  return object(v) && Object.keys(v).length===5 && typeof v.result_id==='string' && /^crop-result-v3:[0-9a-f]{64}$/.test(v.result_id)
    && name(v.scenario_id) && name(v.scenario_revision) && digest(v.registration_sha256) && name(v.crop_id);
}
function sample(v:unknown,confirmed=false):asserts v is StartupCropSample{
  need(object(v));closed(v,['at','state','cumulative','lai','fruit_carbohydrate_total','carbon_residual',
    'carbon_residual_budget','number_residual','number_residual_budget','startup_diagnostics',...(confirmed?['phase']:[])]);
  need(utc(v.at,!confirmed));if(confirmed)need(member(v.phase,CONFIRMED_PHASES));
  state(v.state);quantity(v.lai,LAI_UNIT);quantity(v.fruit_carbohydrate_total,CARBON_UNIT);
  need(object(v.cumulative));closed(v.cumulative,STARTUP_CUMULATIVE);
  for(const k of STARTUP_CUMULATIVE)quantity(v.cumulative[k],k.endsWith('number')?FRUIT_NUMBER_UNIT:CARBON_UNIT);
  quantity(v.carbon_residual,CARBON_UNIT,true);quantity(v.carbon_residual_budget,CARBON_UNIT);
  quantity(v.number_residual,FRUIT_NUMBER_UNIT,true);quantity(v.number_residual_budget,FRUIT_NUMBER_UNIT);
  need(object(v.startup_diagnostics));closed(v.startup_diagnostics,DIAGNOSTICS);
  for(const k of DIAGNOSTICS)quantity(v.startup_diagnostics[k],CARBON_UNIT,k.endsWith('residual'));
}
export { sample as validateStartupCropSample };
function manifest(v:unknown){
  need(object(v));closed(v,['program_version','integrator_version','rate_model_version','profiles','code_sha256',...HASH_KEYS,
    'artifact_dependency_sha256','startup_transition','startup_balance_rule','startup_assumptions','solver',
    'time_rule','python_version','convergence','temperature_sum_method','research_assumptions']);
  need(v.program_version==='crop-plant-startup-program-v1' && v.integrator_version==='crop-plant-startup-rk4-research-v1'
    && v.rate_model_version==='explicit-entry-empty-sink-plant-rates-research-v1'
    && v.startup_transition==='zero_or_positive_tail_research_only_not_validated_sink_capacity'
    && v.startup_balance_rule==='64-ulp-per-operation-without-absolute-floor-v1'
    && v.time_rule==='UTC_POSIX_whole_seconds_v1' && v.convergence==='not_evaluated_for_this_program'
    && v.temperature_sum_method==='analytic_piecewise_constant_fraction_v1'
    && typeof v.python_version==='string' && v.python_version.length<=32 && /^3\.\d+\.\d+$/.test(v.python_version));
  for(const k of HASH_KEYS)need(digest(v[k]));
  need(object(v.profiles));closed(v.profiles,PROFILE_KEYS);
  for(const k of PROFILE_KEYS){const p=v.profiles[k];need(object(p));closed(p,['profile_id','sha256']);need(name(p.profile_id) && digest(p.sha256));}
  need(object(v.code_sha256));closed(v.code_sha256,CODE_KEYS);for(const k of CODE_KEYS)need(digest(v.code_sha256[k]));
  need(object(v.artifact_dependency_sha256));closed(v.artifact_dependency_sha256,['legacy_artifact','canonical_json']);
  for(const vhash of Object.values(v.artifact_dependency_sha256))need(digest(vhash));
  need(object(v.solver));closed(v.solver,['method','max_step_seconds','max_steps','roundoff_rule']);
  need(v.solver.method==='rk4-fixed-v1' && v.solver.roundoff_rule==='64-ulp-per-operation-v1'
    && integer(v.solver.max_step_seconds,1,3600) && integer(v.solver.max_steps,1,10000));
  need(Array.isArray(v.research_assumptions) && v.research_assumptions.length===1
    && v.research_assumptions[0]==='leaf_stem_fixed_RGR_from_reference_profile_not_measured');
  need(Array.isArray(v.startup_assumptions) && v.startup_assumptions.length===4);
  for(const [i,label] of STARTUP_ASSUMPTIONS.entries())need(v.startup_assumptions[i]===label);
}
export function decodeStartupCropPage(v:unknown,lookup:StartupCropLookup):StartupCropPage{
  need(validStartupCropLookup(lookup) && object(v));
  closed(v,['schema_version','floor_area','result_id','recorded_at','study_id','revision','farm','batch_id','zone_id',
    'farm_sha256','source_binding_sha256','storage_status','claim_scope','scope','gates','normalization','profile_applicability',
    'temporal_provenance','start_utc','end_utc','status','steps','planned_steps','manifest','samples','events','sample_page','event_page','hold']);
  need(v.schema_version==='crop-startup-replay-v1' && v.result_id===lookup.result_id && utc(v.recorded_at)
    && name(v.study_id) && name(v.revision) && name(v.batch_id) && name(v.zone_id)
    && digest(v.farm_sha256) && digest(v.source_binding_sha256));
  need(object(v.floor_area));closed(v.floor_area,['value','unit']);
  need(v.floor_area.unit==='m²' && typeof v.floor_area.value==='string' && v.floor_area.value.length<=64
    && /^(?:[1-9][0-9]*(?:\.[0-9]+)?|0\.[0-9]*[1-9][0-9]*)$/.test(v.floor_area.value));
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
  return v as StartupCropPage;
}

function shared(v:StartupCropPage):Shared{
  const {samples:_samples,events:_events,sample_page:_samplePage,event_page:_eventPage,...rest}=v;return rest;
}
function stable(v:unknown):string{
  if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
  if(object(v))return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
  return JSON.stringify(v);
}
function same(a:StartupCropPage,b:StartupCropPage){need(stable(shared(a))===stable(shared(b)));}
function ordered(rows:readonly {at:string}[]){for(let i=1;i<rows.length;i++)need(utcMicroseconds(rows[i-1]!.at)<utcMicroseconds(rows[i]!.at));}
export function assembleStartupCropReplay(pages:readonly StartupCropPage[]):StartupCropReplay{
  need(pages.length>=1 && pages.length<=16);const first=pages[0]!;
  const samples:StartupCropSample[]=[],events:CoupledCropEvent[]=[];
  for(const [i,p] of pages.entries()){
    same(first,p);need(p.sample_page.offset===samples.length && p.event_page.offset===events.length
      && p.sample_page.limit===64 && p.event_page.limit===8
      && p.sample_page.total===first.sample_page.total && p.event_page.total===first.event_page.total);
    samples.push(...p.samples);events.push(...p.events);
    if(i===pages.length-1)need(p.sample_page.next_offset===null && p.event_page.next_offset===null);
    else need(p.sample_page.next_offset!==null || p.event_page.next_offset!==null);
  }
  need(samples.length===first.sample_page.total && events.length===first.event_page.total);ordered(samples);ordered(events);
  if(first.status==='completed')need(samples[0]?.at===first.start_utc && samples.at(-1)?.at===first.end_utc);
  return {...shared(first),samples,events,total_samples:samples.length,total_events:events.length};
}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
const FIRST_QUERY:StartupPageQuery={sample_offset:0,sample_limit:64,event_offset:0,event_limit:8};
export function createStartupCropReplayApi(request:Request){
  async function startupCropPage(lookup:StartupCropLookup,query:StartupPageQuery=FIRST_QUERY,signal?:AbortSignal):Promise<StartupCropPage>{
    need(validStartupCropLookup(lookup) && object(query));closed(query,['sample_offset','sample_limit','event_offset','event_limit']);
    need(integer(query.sample_offset,0,512) && integer(query.sample_limit,1,64)
      && integer(query.event_offset,0,128) && integer(query.event_limit,1,8));canceled(signal);
    const search=new URLSearchParams({scenario_id:lookup.scenario_id,scenario_revision:lookup.scenario_revision,
      registration_sha256:lookup.registration_sha256,crop_id:lookup.crop_id,
      sample_offset:String(query.sample_offset),sample_limit:String(query.sample_limit),
      event_offset:String(query.event_offset),event_limit:String(query.event_limit)});
    const raw=await request('/v1/crop-startup-research-results/'+encodeURIComponent(lookup.result_id)+'?'+search,
      'GET',undefined,200,2*1024*1024,30_000,signal);canceled(signal);
    const p=decodeStartupCropPage(raw,lookup);
    need(p.sample_page.offset===query.sample_offset && p.sample_page.limit===query.sample_limit
      && p.event_page.offset===query.event_offset && p.event_page.limit===query.event_limit);return p;
  }
  return {startupCropPage,
    async startupCropReplay(lookup:StartupCropLookup,options:StartupLoadOptions={}):Promise<StartupCropReplay>{
      const identity=stable(lookup),pages:StartupCropPage[]=[];let query=FIRST_QUERY;
      for(;;){
        canceled(options.signal);need(stable(lookup)===identity);
        const p=await startupCropPage(lookup,query,options.signal);
        if(pages.length){same(pages[0]!,p);need(p.sample_page.total===pages[0]!.sample_page.total
          && p.event_page.total===pages[0]!.event_page.total);
          const previous=pages.at(-1)!;
          if(previous.samples.length && p.samples.length)need(utcMicroseconds(previous.samples.at(-1)!.at)<utcMicroseconds(p.samples[0]!.at));
          if(previous.events.length && p.events.length)need(utcMicroseconds(previous.events.at(-1)!.at)<utcMicroseconds(p.events[0]!.at));}
        pages.push(p);need(pages.length<=16);
        options.onProgress?.({pages:pages.length,samples:p.sample_page.offset+p.samples.length,total:p.sample_page.total,
          events:p.event_page.offset+p.events.length,total_events:p.event_page.total});
        canceled(options.signal);need(stable(lookup)===identity);
        if(p.sample_page.next_offset===null && p.event_page.next_offset===null)return assembleStartupCropReplay(pages);
        query={...FIRST_QUERY,sample_offset:p.sample_page.next_offset??p.sample_page.total,
          event_offset:p.event_page.next_offset??p.event_page.total};
      }
    }
  };
}
