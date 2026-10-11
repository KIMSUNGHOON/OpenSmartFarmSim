import { ApiError,need,object,closed,date,member } from './api-validation';
import { utcMicroseconds } from './coupledCropReplay';

const MASS='mg_CH2O/m2_floor',NUMBER='fruits_equivalent/m2_floor',ENERGY='J/m2_floor',WATER='kg_water/m2_floor',CAPACITY='J/m2_floor/K';
const PLANT={buffer:MASS,leaf:MASS,stem_root:MASS,temperature_filtered_24h:'degC',temperature_sum:'degC_day'} as const;
const COHORT={fruit_carbohydrate:MASS,fruit_number:NUMBER} as const;
const CLIMATE={canopy_sensible_energy:ENERGY,air_temperature:'degC',air_vapor_mass:WATER} as const;
const DERIVED={canopy_temperature:'degC',leaf_area_index:'m2_leaf/m2_floor',canopy_capacity:CAPACITY,
  air_capacity:CAPACITY,air_vapor_pressure:'Pa',canopy_temperature_rate:'K/s'} as const;
const TRANSFERS={photosynthesis:MASS,growth_respiration:MASS,maintenance_leaf:MASS,maintenance_stem_root:MASS,
  maintenance_fruit:MASS,removal_leaf:MASS,removal_stem_root:MASS,terminal_fruit_carbohydrate:MASS,
  fruit_number_inflow:NUMBER,terminal_fruit_number:NUMBER,canopy_to_air_sensible:ENERGY,canopy_to_vapor_latent:ENERGY,
  incoming_capacity_heat:ENERGY,maintenance_capacity_heat:ENERGY,removal_capacity_heat:ENERGY,
  canopy_external_heat:ENERGY,air_external_sensible_heat:ENERGY,canopy_to_air_vapor:WATER,air_external_vapor:WATER,
  capacity_allocation:CAPACITY,capacity_maintenance:CAPACITY,capacity_removal:CAPACITY,
  ventilation_sensible_heat:ENERGY,ventilation_vapor:WATER,ventilation_latent_energy:ENERGY} as const;
const EVENT_TOTALS={leaf:MASS,stem_root:MASS,fruit_carbohydrate:MASS,fruit_number:NUMBER,canopy_sensible_energy:ENERGY,canopy_capacity:CAPACITY} as const;
const BALANCE={carbohydrate:MASS,number:NUMBER,canopy_sensible:ENERGY,air_sensible:ENERGY,reduced_energy:ENERGY,
  vapor_and_water_boundaries:WATER,crop_capacity:CAPACITY,
  ventilation_sensible_partition:ENERGY,ventilation_vapor_partition:WATER,ventilation_latent_partition:ENERGY} as const;
const EVENT_BALANCE={carbohydrate:MASS,number:NUMBER,canopy_sensible:ENERGY,crop_capacity:CAPACITY,temperature:'K'} as const;
const REMOVED={leaf:MASS,stem_root:MASS,canopy_sensible_energy:ENERGY,canopy_capacity:CAPACITY} as const;
const REMOVED_TOTALS={carbohydrate:MASS,number:NUMBER} as const;
const COMPONENTS=['crop_growth_rates','crop_fruit_cohorts','crop_fruit_transport','crop_fruit_allocation','crop_fruit_startup',
  'crop_plant_cohort_rates','crop_plant_startup_rates','crop_canopy_exchange','crop_canopy_energy_transport'] as const;
const PROFILES=['growth','cohort','transport','exchange'] as const;
const DEPENDENCIES=['farm_binding','input_evidence','storage','time','continuation','secure_files','directory_helper','file_metadata'] as const;
const MODEL_HASHES=['engine_code_sha256','driver_code_sha256','short_code_sha256','management_code_sha256','rhs_code_sha256','policy_sha256',
  'transport_helpers_code_sha256','base_driver_code_sha256','base_integration_code_sha256','ventilation_code_sha256',
  'ventilation_policy_sha256','stage_policy_sha256','source_sha256','notice_sha256'] as const;
const INPUT_HASHES=['source_sha256','context_sha256','time_binding_sha256','evidence_sha256'] as const;
const ARTIFACT_HASHES=['sha256','header_sha256','intent_sha256','farm_binding_sha256','head_sha256','proof_sha256'] as const;
const CODE_HASHES=['storage_code_sha256','schema_code_sha256','runtime_roles_code_sha256','server_custody_code_sha256'] as const;
const FARM_KEYS=['scenario_id','scenario_revision','registration_sha256','crop_id'] as const;
const MODEL_LITERALS={ledger_schema:'joint-ventilation-ledgers-v1',engine_version:'joint-ventilation-continuation-research-v1',state_schema:'crop-climate-stage-state-v1',
  physical_clock_contract:'dynamic-canopy-temperature-history-rhs-v1',float_mant_dig:53,float_radix:2} as const;
const REFERENCE_LITERALS={storage_status:'stored_unpublished_research',claim_scope:'synthetic_joint_ventilation_math_only',G0_G4:'not_assessed',
  normalization:'per_m2_floor',profile_applicability:'unvalidated_for_registered_crop',normalization_version:'joint-current-ventilation-float64-grid-v1',
  qc_version:'joint-initial-rhs-ventilation-schedule-utc-v1',input_evidence_version:'joint-ventilation-input-evidence-v1'} as const;
type Hashes<K extends readonly string[]>=Readonly<Record<K[number],string>>;
export type JointQuantity<U extends string=string>=Readonly<{value:number;unit:U}>;
type Block<U extends Record<string,string>>=Readonly<{[K in keyof U]:JointQuantity<U[K]>}>;
const DENSITIES={indoor_vapor_density:'kg_water/m3',outdoor_vapor_density:'kg_water/m3'} as const;
const VENTILATION_FORCING={air_external_sensible_heat:'W/m2_floor',air_external_vapor:'kg_water/m2_floor/s'} as const;
export type GreenhouseVentilationDiagnostic=Readonly<{input_sha256:string;derived:Block<typeof DENSITIES>;
  forcing_contribution:Block<typeof VENTILATION_FORCING>;latent_energy:JointQuantity<'W/m2_floor'>}>;
export type GreenhouseVentilationState=Readonly<{plant_state:Block<typeof PLANT>;cohort_state:Readonly<{
  fruit_carbohydrate:readonly JointQuantity<typeof MASS>[];fruit_number:readonly JointQuantity<typeof NUMBER>[]}>
  ;climate_state:Block<typeof CLIMATE>;derived:Block<typeof DERIVED>}>;
export type GreenhouseVentilationSnapshot=GreenhouseVentilationState & Readonly<{step_index:number;elapsed_seconds:number;
  ventilation:GreenhouseVentilationDiagnostic;integrated_transfers:Block<typeof TRANSFERS>;event_totals:Block<typeof EVENT_TOTALS>;event_count:number;
  balance_residuals:Block<typeof BALANCE>;balance_budgets:Block<typeof BALANCE>;phase:'initial'|'step-end'|'boundary-after-event'}>;
export type GreenhouseVentilationPoint=Readonly<{step_index:number;at:string}>;
export type GreenhouseVentilationSample=Readonly<{value:GreenhouseVentilationSnapshot;time:GreenhouseVentilationPoint}>;
export type GreenhouseVentilationIdentity=Readonly<typeof MODEL_LITERALS & Hashes<typeof MODEL_HASHES> & {
  component_code_sha256:Hashes<typeof COMPONENTS>;profile_sha256:Hashes<typeof PROFILES>;
  python_version:string;platform_machine:string;platform_system:string;byteorder:'little'|'big'}>;
type EventState=GreenhouseVentilationState & Readonly<{input_sha256:string;calculation_sha256:string}>;
export type GreenhouseVentilationManagement=Readonly<{model_version:'joint-crop-climate-management-research-v1';code_sha256:string;rhs_code_sha256:string;
  component_code_sha256:Hashes<typeof COMPONENTS>;profile_sha256:Hashes<typeof PROFILES>;policy_sha256:string;
  event_sha256:string;calculation_sha256:string;before_calculation_sha256:string;after_calculation_sha256:string;
  quantity_rule:'cohort-decimal-rational-removal-v1';roundoff_rule:'64-ulp-event-inventory-v1';time_coordinate:'instantaneous_no_clock';
  before:EventState;after:EventState;removed:Block<typeof REMOVED> & GreenhouseVentilationState['cohort_state'];
  removed_totals:Block<typeof REMOVED_TOTALS>;balance_residuals:Block<typeof EVENT_BALANCE>;balance_budgets:Block<typeof EVENT_BALANCE>;
  scope:'software_research_only';claim_scope:'synthetic_joint_crop_climate_management_only';G0_G4:'not_assessed'}>;
export type GreenhouseVentilationEvent=Readonly<{value:Readonly<{step_index:number;elapsed_seconds:number;management:GreenhouseVentilationManagement;ventilation_after:GreenhouseVentilationDiagnostic}>;time:GreenhouseVentilationPoint}>;
export type GreenhouseVentilationLookup=Readonly<Record<typeof FARM_KEYS[number],string> & {result_id:string}>;
export type GreenhouseVentilationFarm=Readonly<Record<typeof FARM_KEYS[number]|'batch_id'|'zone_id',string>>;
export type GreenhouseVentilationTimeGrid=Readonly<{version:'joint-ventilation-time-binding-research-v1';
  time_rule:'UTC_POSIX_integer_microseconds_decimal_step_v1';time_code_sha256:string;start_utc:string;end_utc:string;
  step_seconds_decimal:string;step_microseconds:number;step_count:number}>;
export type GreenhouseVentilationArtifact=Readonly<Hashes<typeof ARTIFACT_HASHES> & {ref:string;status:'completed'|'hold';steps:number;
  planned_steps:number;sample_count:number;event_count:number;commit_count:number;storage_bytes:number;file_count:number}>;
export type GreenhouseVentilationReference=Readonly<typeof REFERENCE_LITERALS & {input:Hashes<typeof INPUT_HASHES> & {
  program_id:string;start_utc:string;end_utc:string};artifact:GreenhouseVentilationArtifact;
  code:Hashes<typeof CODE_HASHES> & {server_dependency_sha256:Hashes<typeof DEPENDENCIES>};payload_sha256:string;
  model:GreenhouseVentilationIdentity;time_grid:GreenhouseVentilationTimeGrid;last_confirmed:GreenhouseVentilationPoint;failed_boundary:GreenhouseVentilationPoint|null}>;
export type GreenhouseVentilationManifest=Readonly<{identity:GreenhouseVentilationIdentity;program_sha256:string;initial_rhs_sha256:string;
  initial_calculation_sha256:string;policy_sha256:string;scope:'software_research_only';clock_contract:'elapsed-grid-current-ventilation-rk4-events-v1';
  numerical:Readonly<{step_seconds:number;step_count:number;duration_seconds:number;method:'single-step-current-ventilation-rk4-events-v1';
    quantity_rule:'cohort-decimal-rational-removal-v1';roundoff_rule:'64-ulp-per-step-and-event-global-ledger-v1'}>}>;
export type GreenhouseVentilationHold=Readonly<{reason_code:string;phase:'initial'|'interval'|'global-step-balance'|'event'|'event-after-ventilation'|'global-event-balance';
  inner_failed_stage:'initial'|'k2'|'k3'|'k4'|'endpoint'|'endpoint_balance'|null;
  time_meaning:'failed_grid_boundary';time:GreenhouseVentilationPoint}>;
type Shared=Readonly<{schema_version:'joint-ventilation-replay-v1';result_id:string;recorded_at:string;study_id:string;revision:string;
  farm:GreenhouseVentilationFarm;reference:GreenhouseVentilationReference}>;
type PageMeta=Readonly<{offset:number;limit:number;total:number;next_offset:number|null}>;
export type GreenhouseVentilationDataPage=PageMeta & (Readonly<{kind:'samples';records:readonly GreenhouseVentilationSample[]}>
  | Readonly<{kind:'events';records:readonly GreenhouseVentilationEvent[]}>);
export type GreenhouseVentilationSummaryResponse=Shared & Readonly<{page:null;summary:Readonly<{status:'completed'|'hold';manifest:GreenhouseVentilationManifest;
  last_confirmed:GreenhouseVentilationSample;checkpoint_sha256:string|null;hold:GreenhouseVentilationHold|null}>}>;
export type GreenhouseVentilationPageResponse=Shared & Readonly<{summary:null;page:GreenhouseVentilationDataPage}>;
export type GreenhouseVentilationResponse=GreenhouseVentilationSummaryResponse|GreenhouseVentilationPageResponse;
export type GreenhouseVentilationPageQuery=Readonly<{kind:'samples'|'events';offset:number;limit:number}>;
export type GreenhouseVentilationLoadOptions=Readonly<{signal?:AbortSignal;summary?:GreenhouseVentilationSummaryResponse}>;
export type GreenhouseVentilationIterationOptions=Readonly<{signal?:AbortSignal;limit?:number;onSummary?:(value:GreenhouseVentilationSummaryResponse)=>void}>;
export type GreenhouseVentilationCompletion=Readonly<{kind:'samples'|'events';count:number;total:number;complete:true}>;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,timeoutMs?:number,signal?:AbortSignal)=>Promise<unknown>;

function finite(v:unknown):v is number{return typeof v==='number' && Number.isFinite(v);}
function integer(v:unknown,min:number,max:number):v is number{return finite(v) && Number.isSafeInteger(v) && v>=min && v<=max;}
function name(v:unknown):v is string{return typeof v==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(v);}
function digest(v:unknown):v is string{return typeof v==='string' && /^[0-9a-f]{64}$/.test(v);}
function utc(v:unknown):v is string{return date(v) && v.endsWith('Z');}
function decimalMicroseconds(v:string):bigint{
  need(v.length<=40 && /^\d+(?:\.\d+)?(?:[eE][+-]?\d+)?$/.test(v) && finite(Number(v)) && Number(v)>0 && Number(v)<=600);
  const [coefficient,exponent='0']=v.split(/[eE]/),[whole,fraction='']=coefficient!.split('.'),power=Number(exponent);
  need(integer(power,-1000,1000));const digits=BigInt(whole!+fraction),scale=power+6-fraction.length;
  if(scale>=0)return digits*10n**BigInt(scale);
  const divisor=10n**BigInt(-scale);need(digits%divisor===0n);return digits/divisor;
}
function hashes<K extends readonly string[]>(v:unknown,keys:K):asserts v is Hashes<K>{need(object(v));closed(v,keys);for(const k of keys)need(digest(v[k]));}
function literals(v:Record<string,unknown>,expected:Record<string,string|number>){for(const [k,x] of Object.entries(expected))need(v[k]===x);}
function quantities(v:unknown,units:Record<string,string>){need(object(v));closed(v,Object.keys(units));for(const [k,u] of Object.entries(units))quantity(v[k],u);}
function quantity(v:unknown,unit:string){need(object(v));closed(v,['value','unit']);need(v.unit===unit && finite(v.value));}
function cohorts(v:Record<string,unknown>){for(const [k,u] of Object.entries(COHORT)){
  const rows=v[k];need(Array.isArray(rows) && rows.length===50);for(const q of rows){quantity(q,u);need(q.value>=0);}}}
function state(v:Record<string,unknown>){
  quantities(v.plant_state,PLANT);quantities(v.climate_state,CLIMATE);quantities(v.derived,DERIVED);
  need(object(v.cohort_state));closed(v.cohort_state,Object.keys(COHORT));cohorts(v.cohort_state);
  const plant=v.plant_state as Block<typeof PLANT>,climate=v.climate_state as Block<typeof CLIMATE>,derived=v.derived as Block<typeof DERIVED>;
  for(const k of ['buffer','leaf','stem_root','temperature_sum'] as const)need(plant[k].value>=0);
  need(climate.air_vapor_mass.value>=0 && derived.leaf_area_index.value>0 && derived.canopy_capacity.value>0 && derived.air_capacity.value>0);
}
function diagnostic(v:unknown):asserts v is GreenhouseVentilationDiagnostic{
  need(object(v));closed(v,['input_sha256','derived','forcing_contribution','latent_energy']);need(digest(v.input_sha256));
  quantities(v.derived,DENSITIES);quantities(v.forcing_contribution,VENTILATION_FORCING);quantity(v.latent_energy,'W/m2_floor');
}
function budgets(residual:unknown,budget:unknown,units:Record<string,string>){
  quantities(residual,units);quantities(budget,units);need(object(residual) && object(budget));
  for(const k of Object.keys(units)){const r=residual[k] as JointQuantity,b=budget[k] as JointQuantity;need(b.value>=0 && Math.abs(r.value)<=b.value);}
}
function stable(v:unknown):string{
  if(Array.isArray(v))return '['+v.map(stable).join(',')+']';
  if(object(v))return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+stable(v[k])).join(',')+'}';
  return JSON.stringify(v);
}
export function validGreenhouseVentilationLookup(v:unknown):v is GreenhouseVentilationLookup{
  return object(v) && Object.keys(v).length===5 && typeof v.result_id==='string'
    && ['result_id',...FARM_KEYS].every(k=>Object.hasOwn(v,k))
    && /^joint-ventilation-result-v1:[0-9a-f]{64}$/.test(v.result_id) && name(v.scenario_id)
    && name(v.scenario_revision) && digest(v.registration_sha256) && name(v.crop_id);
}
function identity(v:unknown):asserts v is GreenhouseVentilationIdentity{
  need(object(v));closed(v,[...Object.keys(MODEL_LITERALS),...MODEL_HASHES,'component_code_sha256','profile_sha256',
    'python_version','platform_machine','platform_system','byteorder']);literals(v,MODEL_LITERALS);
  for(const k of MODEL_HASHES)need(digest(v[k]));hashes(v.component_code_sha256,COMPONENTS);hashes(v.profile_sha256,PROFILES);
  need(typeof v.python_version==='string' && v.python_version.length<=40 && typeof v.platform_machine==='string'
    && v.platform_machine.length<=100 && typeof v.platform_system==='string' && v.platform_system.length<=100
    && member(v.byteorder,['little','big'] as const));
}
function point(v:unknown,grid:GreenhouseVentilationTimeGrid):asserts v is GreenhouseVentilationPoint{
  need(object(v));closed(v,['step_index','at']);need(integer(v.step_index,0,grid.step_count) && utc(v.at)
    && utcMicroseconds(v.at)===utcMicroseconds(grid.start_utc)+BigInt(v.step_index)*BigInt(grid.step_microseconds));
}
export function decodeGreenhouseVentilationTimeGrid(v:unknown,input:Readonly<{start_utc:string;end_utc:string}>,plannedSteps:number):GreenhouseVentilationTimeGrid{
  need(integer(plannedSteps,1,4096) && object(v));const g=v;
  closed(g,['version','time_rule','time_code_sha256','start_utc','end_utc','step_seconds_decimal','step_microseconds','step_count']);
  need(g.version==='joint-ventilation-time-binding-research-v1' && g.time_rule==='UTC_POSIX_integer_microseconds_decimal_step_v1'
    && digest(g.time_code_sha256) && utc(g.start_utc) && utc(g.end_utc) && g.start_utc===input.start_utc && g.end_utc===input.end_utc
    && typeof g.step_seconds_decimal==='string'
    && integer(g.step_microseconds,1,600000000) && g.step_count===plannedSteps);
  need(decimalMicroseconds(g.step_seconds_decimal)===BigInt(g.step_microseconds));
  const duration=utcMicroseconds(g.end_utc)-utcMicroseconds(g.start_utc);
  need(duration>0n && duration<=600000000n && duration===BigInt(g.step_microseconds)*BigInt(plannedSteps));
  return g as GreenhouseVentilationTimeGrid;
}
function reference(v:unknown):asserts v is GreenhouseVentilationReference{
  need(object(v));closed(v,[...Object.keys(REFERENCE_LITERALS),'input','artifact','code','payload_sha256','model','time_grid','last_confirmed','failed_boundary']);
  literals(v,REFERENCE_LITERALS);need(digest(v.payload_sha256));identity(v.model);
  need(object(v.input));closed(v.input,[...INPUT_HASHES,'program_id','start_utc','end_utc']);
  for(const k of INPUT_HASHES)need(digest(v.input[k]));need(name(v.input.program_id) && utc(v.input.start_utc) && utc(v.input.end_utc));
  need(object(v.code));closed(v.code,[...CODE_HASHES,'server_dependency_sha256']);
  for(const k of CODE_HASHES)need(digest(v.code[k]));hashes(v.code.server_dependency_sha256,DEPENDENCIES);
  need(object(v.artifact));const a=v.artifact;closed(a,[...ARTIFACT_HASHES,'ref','status','steps','planned_steps','sample_count','event_count','commit_count','storage_bytes','file_count']);
  for(const k of ARTIFACT_HASHES)need(digest(a[k]));
  need(member(a.status,['completed','hold'] as const) && integer(a.steps,0,4096) && integer(a.planned_steps,1,4096)
    && a.steps<=a.planned_steps && (a.status!=='completed' || a.steps===a.planned_steps)
    && a.ref==='joint-ventilation-storage-research-v1:'+a.sha256 && integer(a.sample_count,0,512) && integer(a.event_count,0,128)
    && integer(a.commit_count,1,4097) && integer(a.storage_bytes,1,512*1024*1024) && integer(a.file_count,1,65536));
  const g=decodeGreenhouseVentilationTimeGrid(v.time_grid,v.input as GreenhouseVentilationReference['input'],a.planned_steps);
  need(v.code.server_dependency_sha256.continuation===v.model.engine_code_sha256
    && v.code.server_dependency_sha256.time===g.time_code_sha256);
  const grid=g as GreenhouseVentilationTimeGrid;point(v.last_confirmed,grid);need(v.last_confirmed.step_index===a.steps);
  if(a.status==='hold'){point(v.failed_boundary,grid);need(v.failed_boundary.step_index>=a.steps);}
  else need(v.failed_boundary===null);
}
const STATE_KEYS=['plant_state','cohort_state','climate_state','derived'] as const;
export function checkGreenhouseVentilationSample(v:unknown,r:Pick<GreenhouseVentilationReference,'time_grid'>):asserts v is GreenhouseVentilationSample{
  need(object(v));closed(v,['value','time']);point(v.time,r.time_grid);need(object(v.value));const s=v.value;
  closed(s,[...STATE_KEYS,'ventilation','step_index','elapsed_seconds','integrated_transfers','event_totals','event_count','balance_residuals','balance_budgets','phase']);
  state(s);diagnostic(s.ventilation);need(s.step_index===v.time.step_index && finite(s.elapsed_seconds) && s.elapsed_seconds===s.step_index*Number(r.time_grid.step_seconds_decimal)
    && integer(s.event_count,0,128) && member(s.phase,['initial','step-end','boundary-after-event'] as const));
  quantities(s.integrated_transfers,TRANSFERS);quantities(s.event_totals,EVENT_TOTALS);budgets(s.balance_residuals,s.balance_budgets,BALANCE);
}
export function checkGreenhouseVentilationEvent(v:unknown,r:Pick<GreenhouseVentilationReference,'time_grid'|'model'>):asserts v is GreenhouseVentilationEvent{
  need(object(v));closed(v,['value','time']);point(v.time,r.time_grid);need(object(v.value));closed(v.value,['step_index','elapsed_seconds','management','ventilation_after']);diagnostic(v.value.ventilation_after);
  need(v.value.step_index===v.time.step_index && finite(v.value.elapsed_seconds)
    && v.value.elapsed_seconds===v.value.step_index*Number(r.time_grid.step_seconds_decimal) && object(v.value.management));
  const m=v.value.management;closed(m,['model_version','code_sha256','rhs_code_sha256','component_code_sha256','event_sha256','calculation_sha256',
    'before_calculation_sha256','after_calculation_sha256','quantity_rule','roundoff_rule','time_coordinate','before','after',
    'profile_sha256','policy_sha256','removed','removed_totals','balance_residuals','balance_budgets','scope','claim_scope','G0_G4']);
  hashes(m.component_code_sha256,COMPONENTS);hashes(m.profile_sha256,PROFILES);
  need(m.model_version==='joint-crop-climate-management-research-v1' && m.code_sha256===r.model.management_code_sha256
    && m.rhs_code_sha256===r.model.rhs_code_sha256 && stable(m.component_code_sha256)===stable(r.model.component_code_sha256)
    && stable(m.profile_sha256)===stable(r.model.profile_sha256) && m.policy_sha256===r.model.policy_sha256
    && m.quantity_rule==='cohort-decimal-rational-removal-v1' && m.roundoff_rule==='64-ulp-event-inventory-v1'
    && m.time_coordinate==='instantaneous_no_clock' && m.scope==='software_research_only'
    && m.claim_scope==='synthetic_joint_crop_climate_management_only' && m.G0_G4==='not_assessed');
  for(const k of ['event_sha256','calculation_sha256','before_calculation_sha256','after_calculation_sha256'])need(digest(m[k]));
  for(const k of ['before','after'] as const){const s=m[k];need(object(s));closed(s,[...STATE_KEYS,'input_sha256','calculation_sha256']);
    state(s);need(digest(s.input_sha256) && s.calculation_sha256===m[k+'_calculation_sha256']);}
  need(object(m.removed));closed(m.removed,[...Object.keys(REMOVED),...Object.keys(COHORT)]);cohorts(m.removed);
  for(const [k,u] of Object.entries(REMOVED))quantity(m.removed[k],u);
  quantities(m.removed_totals,REMOVED_TOTALS);budgets(m.balance_residuals,m.balance_budgets,EVENT_BALANCE);
}
export function decodeGreenhouseVentilationManifest(v:unknown,grid:GreenhouseVentilationTimeGrid,model?:GreenhouseVentilationIdentity):GreenhouseVentilationManifest{
  need(object(v));const m=v;closed(m,['identity','program_sha256','initial_rhs_sha256','initial_calculation_sha256','policy_sha256','numerical','scope','clock_contract']);
  identity(m.identity);
  need((model===undefined || stable(m.identity)===stable(model)) && digest(m.policy_sha256) && m.scope==='software_research_only'
    && m.clock_contract==='elapsed-grid-current-ventilation-rk4-events-v1');for(const k of ['program_sha256','initial_rhs_sha256','initial_calculation_sha256'])need(digest(m[k]));
  need(object(m.numerical));const n=m.numerical;closed(n,['step_seconds','step_count','duration_seconds','method','quantity_rule','roundoff_rule']);
  need(n.step_seconds===Number(grid.step_seconds_decimal) && n.step_count===grid.step_count
    && n.duration_seconds===Number(grid.step_seconds_decimal)*grid.step_count
    && n.method==='single-step-current-ventilation-rk4-events-v1' && n.quantity_rule==='cohort-decimal-rational-removal-v1'
    && n.roundoff_rule==='64-ulp-per-step-and-event-global-ledger-v1');
  return m as GreenhouseVentilationManifest;
}
function summary(v:unknown,r:GreenhouseVentilationReference):asserts v is GreenhouseVentilationSummaryResponse['summary']{
  need(object(v));closed(v,['status','manifest','last_confirmed','checkpoint_sha256','hold']);need(v.status===r.artifact.status && object(v.manifest));
  decodeGreenhouseVentilationManifest(v.manifest,r.time_grid,r.model);
  checkGreenhouseVentilationSample(v.last_confirmed,r);need(stable(v.last_confirmed.time)===stable(r.last_confirmed));
  if(v.status==='completed'){need(digest(v.checkpoint_sha256) && v.hold===null);return;}
  need(v.checkpoint_sha256===null && object(v.hold));const h=v.hold;closed(h,['reason_code','phase','inner_failed_stage','time_meaning','time']);
  need(h.inner_failed_stage===null || member(h.inner_failed_stage,['initial','k2','k3','k4','endpoint','endpoint_balance'] as const));
  point(h.time,r.time_grid);
  need(typeof h.reason_code==='string' && /^[A-Z][A-Z0-9_]{0,99}$/.test(h.reason_code)
    && member(h.phase,['initial','interval','global-step-balance','event','event-after-ventilation','global-event-balance'] as const)
    && h.time_meaning==='failed_grid_boundary' && stable(h.time)===stable(r.failed_boundary));
}
function page(v:unknown,r:GreenhouseVentilationReference):asserts v is GreenhouseVentilationDataPage{
  need(object(v));closed(v,['kind','offset','limit','total','next_offset','records']);need(member(v.kind,['samples','events'] as const));
  const total=v.kind==='samples'?r.artifact.sample_count:r.artifact.event_count;
  need(integer(v.offset,0,total) && integer(v.limit,1,v.kind==='samples'?64:8) && v.total===total && Array.isArray(v.records)
    && v.records.length===Math.min(v.limit,total-v.offset));const end=v.offset+v.records.length;
  need(v.next_offset===(end<total?end:null));let previous=-1;
  for(const row of v.records){if(v.kind==='samples')checkGreenhouseVentilationSample(row,r);else checkGreenhouseVentilationEvent(row,r);const at=row.time.step_index;
    need(at>previous && at<=r.artifact.steps && (r.failed_boundary===null || at<r.failed_boundary.step_index));previous=at;}
}
export function decodeGreenhouseVentilationResponse(v:unknown,lookup:GreenhouseVentilationLookup):GreenhouseVentilationResponse{
  need(validGreenhouseVentilationLookup(lookup) && object(v));closed(v,['schema_version','result_id','recorded_at','study_id','revision','farm','reference','summary','page']);
  need(v.schema_version==='joint-ventilation-replay-v1' && v.result_id===lookup.result_id && utc(v.recorded_at) && name(v.study_id) && name(v.revision) && object(v.farm));
  closed(v.farm,[...FARM_KEYS,'batch_id','zone_id']);for(const k of FARM_KEYS)need(v.farm[k]===lookup[k]);need(name(v.farm.batch_id) && name(v.farm.zone_id));
  reference(v.reference);need((v.summary===null)!==(v.page===null));if(v.summary!==null)summary(v.summary,v.reference);else page(v.page,v.reference);
  return v as GreenhouseVentilationResponse;
}
function shared(v:GreenhouseVentilationResponse){const {summary:_s,page:_p,...rest}=v;return rest;}
export function matchGreenhouseVentilationPage(summary:GreenhouseVentilationSummaryResponse,p:GreenhouseVentilationPageResponse){need(stable(shared(summary))===stable(shared(p)));}
function canceled(signal?:AbortSignal){if(signal?.aborted)throw new ApiError('request_canceled');}
export function createGreenhouseVentilationReplayApi(request:Request){
  let inFlight=false;
  async function read(lookup:GreenhouseVentilationLookup,view:'summary'|'samples'|'events',signal?:AbortSignal,query?:GreenhouseVentilationPageQuery){
    need(validGreenhouseVentilationLookup(lookup));canceled(signal);need(!inFlight);const identity=stable(lookup);
    const search=new URLSearchParams({...lookup});search.delete('result_id');search.set('view',view);
    if(query){search.set('offset',String(query.offset));search.set('limit',String(query.limit));}inFlight=true;
    try{const raw=await request('/v1/crop-greenhouse-ventilation-research-results/'+encodeURIComponent(lookup.result_id)+'?'+search,
      'GET',undefined,200,2*1024*1024,30_000,signal);canceled(signal);need(stable(lookup)===identity);return decodeGreenhouseVentilationResponse(raw,lookup);}
    finally{inFlight=false;}
  }
  async function greenhouseVentilationSummary(lookup:GreenhouseVentilationLookup,signal?:AbortSignal):Promise<GreenhouseVentilationSummaryResponse>{
    const v=await read(lookup,'summary',signal);need(v.summary!==null);return v;
  }
  async function greenhouseVentilationPage(lookup:GreenhouseVentilationLookup,query:GreenhouseVentilationPageQuery,options:GreenhouseVentilationLoadOptions={}):Promise<GreenhouseVentilationPageResponse>{
    need(object(query));closed(query,['kind','offset','limit']);need(member(query.kind,['samples','events'] as const)
      && integer(query.offset,0,query.kind==='samples'?512:128) && integer(query.limit,1,query.kind==='samples'?64:8));
    need(object(options) && Object.keys(options).every(k=>k==='signal'||k==='summary'));
    const s=options.summary,qIdentity=stable(query);
    if(s!==undefined){need(decodeGreenhouseVentilationResponse(s,lookup).summary!==null);need(query.offset<=(query.kind==='samples'?s.reference.artifact.sample_count:s.reference.artifact.event_count));}
    const sIdentity=stable(s);
    const v=await read(lookup,query.kind,options.signal,query);need(v.page!==null && stable(query)===qIdentity && stable(s)===sIdentity
      && v.page.kind===query.kind && v.page.offset===query.offset && v.page.limit===query.limit);if(s)matchGreenhouseVentilationPage(s,v);return v;
  }
  async function* greenhouseVentilationPages(lookup:GreenhouseVentilationLookup,kind:'samples'|'events',options:GreenhouseVentilationIterationOptions={}):
    AsyncGenerator<GreenhouseVentilationPageResponse,GreenhouseVentilationCompletion|undefined,void>{
    need(validGreenhouseVentilationLookup(lookup) && member(kind,['samples','events'] as const) && object(options)
      && Object.keys(options).every(k=>k==='signal'||k==='limit'||k==='onSummary'));
    const limit=options.limit??(kind==='samples'?64:8),signal=options.signal,identity=stable(lookup);
    need(integer(limit,1,kind==='samples'?64:8) && (options.onSummary===undefined || typeof options.onSummary==='function'));
    const s=await greenhouseVentilationSummary(lookup,signal),sIdentity=stable(s),total=kind==='samples'?s.reference.artifact.sample_count:s.reference.artifact.event_count;
    options.onSummary?.(s);let offset=0,pages=0,previous=-1;
    for(;;){canceled(signal);need(stable(lookup)===identity && stable(s)===sIdentity);
      const v=await greenhouseVentilationPage(lookup,{kind,offset,limit},{signal,summary:s});need(++pages<=Math.max(total,1));
      for(const row of v.page.records){need(row.time.step_index>previous);previous=row.time.step_index;}
      const count=offset+v.page.records.length,next=v.page.next_offset;yield v;
      canceled(signal);need(stable(lookup)===identity && stable(s)===sIdentity);
      if(next===null){need(count===total);return {kind,count,total,complete:true};}offset=next;
    }
  }
  return {greenhouseVentilationSummary,greenhouseVentilationPage,greenhouseVentilationPages};
}
