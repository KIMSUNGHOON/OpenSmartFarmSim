import { need, object, member, date, uuid, closed } from './api-validation';
import type { JobStatus } from './api';
import { SOURCE_FIELDS } from './source-fields';

export type SourceKind='economic_input'|'economic_scenario'|'joint_shock';
export type SourceType=SourceKind|'input_rights';
export type Cursor={record_id:string;revision:string};
export type SourceMeta<K extends SourceType=SourceKind>=Cursor & {kind:K;payload_sha256:string;recorded_at:string;
  admission_kind:'contract_valid_user_assumption'};
export type SourcePage={kind:SourceKind;items:SourceMeta[];next_cursor:Cursor|null};
export const UNITS=['kg','KRW','KRW/kg','month','KRW/month','kWh_e','KRW/kWh_e','L','KRW/L','day'] as const;
export type NumericInput={value:string;unit:typeof UNITS[number];input_id:string;revision:string;
  origin:'user';evidence_level:'assumed';assumption_scope:string;source_ref:string;available_at:string;
  scope_start:string;scope_end:string};
export type NumericRecord=SourceMeta & {kind:'economic_input';input:NumericInput};
export type NumericIntent={kind:'economic_input';input:NumericInput;idempotency_key:string};
export type SourceSaved<K extends SourceType=SourceKind>=SourceMeta<K> & {intent_job:JobStatus};
export type Baseline=SourceMeta & {kind:'economic_scenario';decision_at:string;
  market_context:{kind:'unavailable';hold_report_id:string};period_start:string;period_end:string};
export type Shock=SourceMeta & {kind:'joint_shock';decision_at:string;baseline_sha256:string};
export type EconomicNumber=Omit<NumericInput,'scope_start'|'scope_end'>;
export type Rights={use:'allowed';display:'allowed';redistribute:'allowed'|'denied'};
export type Edit={event_group:string;event_id:string;field:string;number:EconomicNumber|null;time:string|null;reference:string|null};
export type Driver={kind:'demand'|'supply'|'macro';record_id:string;revision:string;origin:'user';evidence_level:'assumed';
  available_at:string;effective_start:string;effective_end:string;rights:Rights;hypothesis:string;source_ref:string;
  causal_status:'unvalidated_user_hypothesis';changes:Edit[]};
export type ContractCap={record_id:string;revision:string;contract_id:string;sale_ids:string[];grade:string;channel:string;
  accepted_kg:EconomicNumber;origin:'user';evidence_level:'assumed';available_at:string;effective_start:string;effective_end:string;rights:Rights};
export type JointInput={schema_version:'1';shock_id:string;revision:string;baseline_sha256:string;decision_at:string;
  effective_start:string;effective_end:string;available_at:string;origin:'user';evidence_level:'assumed';rights:Rights;
  drivers:Driver[];contract_caps:ContractCap[];settlement_bindings:{binding_id:string;revision:string;sha256:string}[]};
export type JointRecord=Shock & {input:JointInput};
export type InputRights={input_id:string;revision:string;raw_sha256:string;origin:'user';evidence_level:'assumed';rights:Rights;
  available_at:string;effective_start:string;effective_end:string;immutable:true};
export type RightsIntent={kind:'input_rights';input:InputRights;idempotency_key:string};
export type JointIntent={kind:'joint_shock';input:JointInput;idempotency_key:string};
export type Candidate={candidate_id:string;scenario_id:string;scenario_revision:string;scenario_sha256:string;
  registration_status:'pinned_user_assumption';recorded_at:string;intent_job:JobStatus};
export type ScenarioIntent={request:{schema_version:'1';baseline:{scenario_id:string;revision:string;sha256:string};
  shock:{shock_id:string;revision:string;sha256:string};decision_at:string;market_context:Baseline['market_context']};
  idempotency_key:string};
export type CalculationIntent={input_version:'economic-calculation-input-v1';scenario_id:string;scenario_revision:string;
  scenario_sha256:string;candidate_id:string;formula_version:'economic-ledger-v9-sales-settlement';idempotency_key:string};
export const AMOUNTS=['gross_sales_krw','revenue_krw','variable_cost_krw','fixed_cost_krw','depreciation_krw',
  'management_operating_income_krw','operating_cash_krw','business_cash_krw','equity_cash_krw',
  'minimum_cash_balance_krw','cash_shortage_krw'] as const;
export type EconomicResult={economic_result_id:string;market_scenario_result_id:string;scenario_id:string;
  scenario_revision:string;decision_at_utc:string;formula_version:'economic-ledger-v9-sales-settlement';
  market_context_kind:'unavailable';market_hold_report_id:string;calculation_status:'conditional_user_assumption'|'hold';
  assessment_status:'hold';sales_totals_status:'inventory_reconciled'|'unverified_input_arithmetic';input_origin:'user';
  evidence_level:'assumed';quantities:{harvest_kg:string;packout_kg:string;recognized_kg:string;net_sold_kg:string|null};
  amounts:Record<typeof AMOUNTS[number],string|null>;hold_reason_codes:string[]};
export type MonthlyCash={month:string;opening_balance_krw:string;net_cash_krw:string;closing_balance_krw:string;
  minimum_balance_krw:string;minimum_at_utc:string;cash_shortage_krw:string};
export type CashPage=Pick<EconomicResult,'economic_result_id'|'market_scenario_result_id'|'scenario_id'|'scenario_revision'|
  'decision_at_utc'|'formula_version'|'market_context_kind'|'market_hold_report_id'|'calculation_status'|'assessment_status'|
  'input_origin'|'evidence_level'|'hold_reason_codes'> & {schema_version:'economic-cash-page-v1';calendar_timezone:'Asia/Seoul';
  series_status:'available'|'unavailable';total_months:number|null;limit:12;after_month:string|null;next_month_cursor:string|null;
  monthly_cash:MonthlyCash[]|null};
const CASH_IDENTITY=['economic_result_id','market_scenario_result_id','scenario_id','scenario_revision','decision_at_utc',
  'formula_version','market_context_kind','market_hold_report_id','calculation_status','assessment_status','input_origin','evidence_level'] as const;
const CASH_AMOUNTS=['opening_balance_krw','net_cash_krw','closing_balance_krw','minimum_balance_krw','cash_shortage_krw'] as const;
function month(value:unknown):value is string {return typeof value==='string' && /^\d{4}-(?:0[1-9]|1[0-2])$/.test(value) && day(value+'-01');}
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number)=>Promise<unknown>;
const META=['kind','record_id','revision','payload_sha256','recorded_at','admission_kind'] as const;
const NUMBER=['value','unit','input_id','revision','origin','evidence_level','assumption_scope','source_ref',
  'available_at','scope_start','scope_end'] as const;
export function name(value:unknown,max=200):value is string {
  return typeof value==='string' && value.length>0 && Array.from(value).length<=max
    && value.trim()===value && !/[\u0000-\u001f]/.test(value);
}
export function hash(value:unknown):value is string {return typeof value==='string' && /^[0-9a-f]{64}$/.test(value);}
export function day(value:unknown):value is string {
  return typeof value==='string' && /^\d{4}-\d\d-\d\d$/.test(value) && date(value+'T00:00:00Z');
}
export function utc(value:unknown):value is string {return date(value) && /(?:Z|\+00:00)$/.test(value);}
export function decimal(value:unknown,max=64):value is string {
  return typeof value==='string' && value.length<=max && /^(?:0|[1-9]\d*)(?:\.\d+)?$/.test(value);
}
function metadata<K extends SourceType>(value:unknown,kind:K):SourceMeta<K> {
  need(object(value));
  need(value.kind===kind && name(value.record_id) && name(value.revision) && hash(value.payload_sha256)
    && date(value.recorded_at) && value.admission_kind==='contract_valid_user_assumption');
  return {kind,record_id:value.record_id,revision:value.revision,payload_sha256:value.payload_sha256,
    recorded_at:value.recorded_at,admission_kind:value.admission_kind};
}
function cursor(value:unknown):Cursor {need(object(value));closed(value,['record_id','revision']);
  need(name(value.record_id) && name(value.revision));return {record_id:value.record_id,revision:value.revision};}
function number(value:unknown):EconomicNumber {
  need(object(value));closed(value,NUMBER.slice(0,9));
  need(decimal(value.value) && member(value.unit,UNITS) && name(value.input_id) && name(value.revision)
    && value.origin==='user' && value.evidence_level==='assumed' && name(value.assumption_scope,65536)
    && name(value.source_ref,65536) && utc(value.available_at));
  return value as EconomicNumber;
}
function numeric(value:unknown):NumericInput {
  need(object(value));closed(value,NUMBER);
  number(Object.fromEntries(NUMBER.slice(0,9).map(key=>[key,value[key]])));
  need(day(value.scope_start) && day(value.scope_end) && value.scope_start<=value.scope_end);
  return value as NumericInput;
}
function rights(value:unknown):Rights {
  need(object(value));closed(value,['use','display','redistribute']);
  need(value.use==='allowed' && value.display==='allowed' && member(value.redistribute,['allowed','denied'] as const));
  return value as Rights;
}
function scope(value:Record<string,unknown>) {
  need(value.origin==='user' && value.evidence_level==='assumed' && utc(value.available_at)
    && day(value.effective_start) && day(value.effective_end) && value.effective_start<=value.effective_end);
  rights(value.rights);
}
function joint(value:unknown):JointInput {
  need(object(value));closed(value,SOURCE_FIELDS.joint_shock);scope(value);
  need(value.schema_version==='1' && name(value.shock_id) && name(value.revision) && hash(value.baseline_sha256)
    && utc(value.decision_at) && Array.isArray(value.drivers) && Array.isArray(value.contract_caps) && Array.isArray(value.settlement_bindings));
  for(const driver of value.drivers) {
    need(object(driver));closed(driver,['kind','record_id','revision','origin','evidence_level','available_at','effective_start',
      'effective_end','rights','hypothesis','source_ref','causal_status','changes']);scope(driver);
    need(member(driver.kind,['demand','supply','macro'] as const) && name(driver.record_id) && name(driver.revision)
      && typeof driver.hypothesis==='string' && driver.hypothesis.trim().length>0 && name(driver.source_ref,65536)
      && driver.causal_status==='unvalidated_user_hypothesis' && Array.isArray(driver.changes));
    for(const edit of driver.changes) {
      need(object(edit));closed(edit,['event_group','event_id','field','number','time','reference']);
      need(name(edit.event_group) && name(edit.event_id) && name(edit.field)
        && [edit.number,edit.time,edit.reference].filter(v=>v!==null).length===1);
      if(edit.number!==null)number(edit.number);
      if(edit.time!==null)need(utc(edit.time));
      if(edit.reference!==null)need(name(edit.reference,65536));
    }
  }
  for(const cap of value.contract_caps) {
    need(object(cap));closed(cap,['record_id','revision','contract_id','sale_ids','grade','channel','accepted_kg','origin',
      'evidence_level','available_at','effective_start','effective_end','rights']);scope(cap);number(cap.accepted_kg);
    need(name(cap.record_id) && name(cap.revision) && name(cap.contract_id) && name(cap.grade) && name(cap.channel)
      && Array.isArray(cap.sale_ids) && cap.sale_ids.length>0 && cap.sale_ids.every(id=>name(id)));
  }
  for(const binding of value.settlement_bindings) {
    need(object(binding));closed(binding,['binding_id','revision','sha256']);
    need(name(binding.binding_id) && name(binding.revision) && hash(binding.sha256));
  }
  return value as JointInput;
}
export function createEconomicApi(request:Request,job:(value:unknown)=>JobStatus) {
  async function record(kind:SourceKind,ref:Cursor) {
    need(name(ref.record_id) && name(ref.revision));
    const raw=await request('/v1/market-user-sources/record?'+new URLSearchParams({kind,...ref}), 'GET',undefined,200,131072);
    need(object(raw));closed(raw,[...META,'input']);
    const meta=metadata(raw,kind);need(meta.record_id===ref.record_id && meta.revision===ref.revision && object(raw.input));
    closed(raw.input,SOURCE_FIELDS[kind]);
    return {meta,input:raw.input};
  }
  async function saveSource<K extends SourceType>(intent:{kind:K;input:unknown;idempotency_key:string},id:string,revision:string):Promise<SourceSaved<K>> {
    const raw=await request('/v1/market-user-sources','POST',intent,200);
    need(object(raw));closed(raw,[...META,'intent_job']);const result=metadata(raw,intent.kind);
    need(result.record_id===id && result.revision===revision);
    const intent_job=job(raw.intent_job);need(intent_job.stage==='collection');return {...result,intent_job};
  }
  return {
    async sources(kind:SourceKind,after?:Cursor):Promise<SourcePage> {
      const query=new URLSearchParams({kind,limit:'20'});
      if(after) {need(name(after.record_id) && name(after.revision));query.set('after_record_id',after.record_id);query.set('after_revision',after.revision);}
      const raw=await request('/v1/market-user-sources?'+query,'GET',undefined,200,131072);
      need(object(raw));closed(raw,['kind','items','next_cursor']);need(raw.kind===kind && Array.isArray(raw.items) && raw.items.length<=20);
      const items=raw.items.map(item=>{need(object(item));closed(item,META);return metadata(item,kind);});
      const next=raw.next_cursor===null ? null : cursor(raw.next_cursor);
      need(next===null || items.length>0 && next.record_id===items.at(-1)?.record_id && next.revision===items.at(-1)?.revision);
      return {kind,items,next_cursor:next};
    },
    async numeric(ref:Cursor):Promise<NumericRecord> {
      const {meta,input}=await record('economic_input',ref);const value=numeric(input);
      need(value.input_id===meta.record_id && value.revision===meta.revision);
      return {...meta,kind:'economic_input',input:value};
    },
    async saveNumeric(intent:NumericIntent):Promise<SourceSaved> {
      numeric(intent.input);
      return saveSource(intent,intent.input.input_id,intent.input.revision);
    },
    async saveRights(intent:RightsIntent):Promise<SourceSaved<'input_rights'>> {
      const input=intent.input;need(object(input));closed(input,SOURCE_FIELDS.input_rights);scope(input);
      need(name(input.input_id) && name(input.revision) && hash(input.raw_sha256) && input.immutable===true);
      return saveSource(intent,input.input_id,input.revision);
    },
    async saveJoint(intent:JointIntent):Promise<SourceSaved<'joint_shock'>> {
      joint(intent.input);return saveSource(intent,intent.input.shock_id,intent.input.revision);
    },
    async joint(ref:Cursor):Promise<JointRecord> {
      const {meta,input}=await record('joint_shock',ref);const value=joint(input);
      need(value.shock_id===meta.record_id && value.revision===meta.revision);
      return {...meta,kind:'joint_shock',decision_at:value.decision_at,baseline_sha256:value.baseline_sha256,input:value};
    },
    async baseline(ref:Cursor):Promise<Baseline> {
      const {meta,input}=await record('economic_scenario',ref);
      need(input.scenario_id===meta.record_id && input.scenario_revision===meta.revision && utc(input.decision_at)
        && day(input.period_start) && day(input.period_end) && input.period_start<=input.period_end && object(input.market_context));
      closed(input.market_context,['kind','hold_report_id']);need(input.market_context.kind==='unavailable' && uuid(input.market_context.hold_report_id));
      return {...meta,kind:'economic_scenario',decision_at:input.decision_at,period_start:input.period_start,
        period_end:input.period_end,market_context:{kind:'unavailable',hold_report_id:input.market_context.hold_report_id}};
    },
    async shock(ref:Cursor):Promise<Shock> {
      const {meta,input}=await record('joint_shock',ref);
      need(input.shock_id===meta.record_id && input.revision===meta.revision && hash(input.baseline_sha256) && utc(input.decision_at));
      return {...meta,kind:'joint_shock',decision_at:input.decision_at,baseline_sha256:input.baseline_sha256};
    },
    async scenario(intent:ScenarioIntent):Promise<Candidate> {
      const raw=await request('/v1/economic-scenarios','POST',intent,200);need(object(raw));
      closed(raw,['candidate_id','scenario_id','scenario_revision','scenario_sha256','registration_status','recorded_at','intent_job']);
      need(hash(raw.candidate_id) && name(raw.scenario_id) && name(raw.scenario_revision) && hash(raw.scenario_sha256)
        && raw.registration_status==='pinned_user_assumption' && date(raw.recorded_at));
      const intent_job=job(raw.intent_job);need(intent_job.stage==='collection');
      return {candidate_id:raw.candidate_id,scenario_id:raw.scenario_id,scenario_revision:raw.scenario_revision,
        scenario_sha256:raw.scenario_sha256,registration_status:raw.registration_status,recorded_at:raw.recorded_at,intent_job};
    },
    async calculate(intent:CalculationIntent) {
      const result=job(await request('/v1/economic-results','POST',intent));need(result.stage==='simulation');return result;
    },
    async economicCash(id:string,result:EconomicResult,after?:string):Promise<CashPage> {
      need(uuid(id) && (after===undefined || month(after)));
      const query=new URLSearchParams({limit:'12'});if(after!==undefined)query.set('after_month',after);
      const raw=await request('/v1/jobs/'+id+'/economic-cash-flow?'+query);need(object(raw));
      closed(raw,[...CASH_IDENTITY,'hold_reason_codes','schema_version','calendar_timezone','series_status','total_months',
        'limit','after_month','next_month_cursor','monthly_cash']);
      need(CASH_IDENTITY.every(key=>raw[key]===result[key]) && raw.schema_version==='economic-cash-page-v1'
        && raw.calendar_timezone==='Asia/Seoul' && raw.limit===12 && raw.after_month===(after ?? null));
      need(Array.isArray(raw.hold_reason_codes) && raw.hold_reason_codes.length<=100 && raw.hold_reason_codes.every(code=>
        typeof code==='string' && /^[A-Z][A-Z0-9_]{0,79}$/.test(code)));
      if(raw.series_status==='unavailable')need(raw.monthly_cash===null && raw.total_months===null && raw.next_month_cursor===null && after===undefined);
      else {
        need(raw.series_status==='available' && typeof raw.total_months==='number' && Number.isSafeInteger(raw.total_months)
          && raw.total_months>=1 && raw.total_months<=119988 && Array.isArray(raw.monthly_cash)
          && raw.monthly_cash.length<=12 && raw.monthly_cash.length<=raw.total_months && (after!==undefined || raw.monthly_cash.length>0));
        let previous=after ?? '';
        for(const row of raw.monthly_cash) {
          need(object(row));closed(row,['month',...CASH_AMOUNTS,'minimum_at_utc']);
          need(month(row.month) && row.month>previous && utc(row.minimum_at_utc));previous=row.month;
          need(CASH_AMOUNTS.every(key=>typeof row[key]==='string' && row[key].length<=256 && /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/.test(row[key]))
            && decimal(row.cash_shortage_krw,256));
        }
        need(raw.next_month_cursor===null || month(raw.next_month_cursor) && raw.monthly_cash.length>0 && raw.next_month_cursor===previous);
      }
      return raw as CashPage;
    },
    async economicResult(id:string,candidate:Candidate,context:Pick<ScenarioIntent['request'],'decision_at'|'market_context'>):Promise<EconomicResult> {
      need(uuid(id));const raw=await request('/v1/jobs/'+id+'/economic-result');need(object(raw));
      closed(raw,['economic_result_id','market_scenario_result_id','scenario_id','scenario_revision','decision_at_utc',
        'formula_version','market_context_kind','market_hold_report_id','calculation_status','assessment_status',
        'sales_totals_status','input_origin','evidence_level','quantities','amounts','hold_reason_codes']);
      need(hash(raw.economic_result_id) && hash(raw.market_scenario_result_id) && raw.scenario_id===candidate.scenario_id
        && raw.scenario_revision===candidate.scenario_revision && utc(raw.decision_at_utc)
        && raw.formula_version==='economic-ledger-v9-sales-settlement' && raw.market_context_kind==='unavailable'
        && raw.decision_at_utc===context.decision_at && raw.market_hold_report_id===context.market_context.hold_report_id
        && uuid(raw.market_hold_report_id) && member(raw.calculation_status,['conditional_user_assumption','hold'] as const)
        && raw.assessment_status==='hold' && member(raw.sales_totals_status,['inventory_reconciled','unverified_input_arithmetic'] as const)
        && raw.input_origin==='user' && raw.evidence_level==='assumed' && object(raw.quantities) && object(raw.amounts));
      closed(raw.quantities,['harvest_kg','packout_kg','recognized_kg','net_sold_kg']);closed(raw.amounts,AMOUNTS);
      need(Object.values(raw.quantities).every(value=>value===null || decimal(value,256)) && raw.quantities.harvest_kg!==null
        && raw.quantities.packout_kg!==null && raw.quantities.recognized_kg!==null);
      need(Object.values(raw.amounts).every(value=>value===null || typeof value==='string' && value.length<=256
        && /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/.test(value)) && raw.amounts.gross_sales_krw!==null);
      need(Array.isArray(raw.hold_reason_codes) && raw.hold_reason_codes.length<=100 && raw.hold_reason_codes.every(code=>
        typeof code==='string' && /^[A-Z][A-Z0-9_]{0,79}$/.test(code)));
      return raw as EconomicResult;
    },
  };
}
