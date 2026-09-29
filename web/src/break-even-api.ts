import {need,object,closed,member,uuid,date} from './api-validation';
import {name,hash,day,utc,decimal,type Baseline,type ScenarioIntent} from './economic-api';
import type {JobStatus} from './api';
import {SOURCE_FIELDS} from './source-fields';

export const TARGETS=['oi','operating_cash','cumulative_equity_cash'] as const;
export const VARIABLES=['kg','KRW/kg'] as const;
export type SaleTerms={sale_id:string;batch_id:string;grade:string;channel:string;dispatch_at:string;delivery_at:string;
  inspection_at:string;recognized_at:string;collection_id:string;collection_at:string};
export type BreakEvenRequest=SaleTerms & {schema_version:'1';plan_id:string;baseline:ScenarioIntent['request']['baseline'];
  market_context:Baseline['market_context'];decision_at:string;period_start:string;period_end:string;
  target:typeof TARGETS[number];variable:typeof VARIABLES[number];minimum:string;maximum:string;step:string};
export type TrialPin={scenario_id:string;revision:string;scenario_sha256:string};
export type BreakEvenSubmission={request:BreakEvenRequest;trials:TrialPin[]};
export type BreakEvenAccepted={plan_id:string;request_sha256:string;plan_sha256:string;trial_count:number;
  registration_status:'pinned_user_grid_intent';intent_job:JobStatus};
export type BreakEvenReceipt={plan_id:string;submission_sha256:string;intent_status:'stored';intent_job:JobStatus};
export type BreakEvenTrial={value:string;target_value_krw:string;minimum_cash_balance_krw:string|null;cash_shortage_krw:string|null};
export type BreakEvenResult={plan_id:string;status:'zero_on_grid'|'no_zero_on_grid'|'bracket_only'|'nonmonotone_on_grid'|'hold';
  scope:'conditional_user_grid_only';assessment_status:'hold';input_origin:'user';evidence_level:'assumed';market_context_kind:'unavailable';
  market_hold_report_id:string;decision_at_utc:string;period_start:string;period_end:string;target:BreakEvenRequest['target'];
  variable_unit:BreakEvenRequest['variable'];minimum:string;maximum:string;step:string;zero_values:string[];brackets:[string,string][];
  trials:BreakEvenTrial[];hold_reason_codes:string[]};
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number)=>Promise<unknown>;
const SALE_FIELDS=['sale_id','batch_id','grade','channel','dispatch_at','delivery_at','inspection_at','recognized_at','collection_id','collection_at'] as const;
const TIMES=['dispatch_at','delivery_at','inspection_at','recognized_at','collection_at'] as const;
const GRID=['minimum','maximum','step'] as const;
const META=['kind','record_id','revision','payload_sha256','recorded_at','admission_kind'] as const;
function money(value:unknown):value is string {return typeof value==='string' && value.length<=256 && /^-?(?:0|[1-9]\d*)(?:\.\d+)?$/.test(value);}
function representation(value:string) {return value.replace(/(\.\d*?)0+$/,'$1').replace(/\.$/,'');}
function validateSubmission(value:BreakEvenSubmission) {
  need(object(value));closed(value,['request','trials']);const r=value.request;need(object(r));
  closed(r,[...SALE_FIELDS,'schema_version','plan_id','baseline','market_context','decision_at','period_start','period_end','target','variable',...GRID]);
  need(r.schema_version==='1' && name(r.plan_id) && member(r.target,TARGETS) && member(r.variable,VARIABLES)
    && utc(r.decision_at) && day(r.period_start) && day(r.period_end) && r.period_start<=r.period_end
    && GRID.every(key=>decimal(r[key])) && representation(r.step)!=='0'
    && TIMES.every(key=>utc(r[key])) && (['sale_id','batch_id','grade','channel','collection_id'] as const).every(key=>name(r[key])));
  need(object(r.baseline));closed(r.baseline,['scenario_id','revision','sha256']);
  need(name(r.baseline.scenario_id) && name(r.baseline.revision) && hash(r.baseline.sha256));
  need(object(r.market_context));closed(r.market_context,['kind','hold_report_id']);
  need(r.market_context.kind==='unavailable' && uuid(r.market_context.hold_report_id)
    && Array.isArray(value.trials) && value.trials.length>=2 && value.trials.length<=256);
  for(const pin of value.trials) {need(object(pin));closed(pin,['scenario_id','revision','scenario_sha256']);
    need(name(pin.scenario_id) && name(pin.revision) && hash(pin.scenario_sha256));}
  need(new Set(value.trials.map(pin=>JSON.stringify([pin.scenario_id,pin.revision]))).size===value.trials.length);
}
export function createBreakEvenApi(request:Request,decodeJob:(value:unknown)=>JobStatus) {
  return {
    async breakEvenReceipt(body:BreakEvenSubmission):Promise<BreakEvenReceipt> {
      const digest=await submissionDigest(body);
      const raw=await request('/v1/break-even-plans/receipt?'+new URLSearchParams({plan_id:body.request.plan_id,submission_sha256:digest}));
      need(object(raw));closed(raw,['plan_id','submission_sha256','intent_status','intent_job']);
      need(raw.plan_id===body.request.plan_id && raw.submission_sha256===digest && raw.intent_status==='stored');
      const intent_job=decodeJob(raw.intent_job);need(intent_job.stage==='simulation');return {...raw,intent_job} as BreakEvenReceipt;
    },
    async breakEvenSales(baseline:Baseline):Promise<SaleTerms[]> {
      const query=new URLSearchParams({kind:'economic_scenario',record_id:baseline.record_id,revision:baseline.revision});
      const raw=await request('/v1/market-user-sources/record?'+query,'GET',undefined,200,131072);need(object(raw));closed(raw,[...META,'input']);
      need(raw.kind==='economic_scenario' && raw.record_id===baseline.record_id && raw.revision===baseline.revision
        && raw.payload_sha256===baseline.payload_sha256 && date(raw.recorded_at) && raw.admission_kind==='contract_valid_user_assumption'
        && object(raw.input));const input=raw.input;closed(input,SOURCE_FIELDS.economic_scenario);
      need(input.scenario_id===baseline.record_id && input.scenario_revision===baseline.revision && input.decision_at===baseline.decision_at
        && input.period_start===baseline.period_start && input.period_end===baseline.period_end && object(input.market_context));
      closed(input.market_context,['kind','hold_report_id']);need(input.market_context.kind==='unavailable'
        && input.market_context.hold_report_id===baseline.market_context.hold_report_id && Array.isArray(input.sales)
        && (input.collections===null || Array.isArray(input.collections)));
      const sales=input.sales.map(sale=>{
        need(object(sale));closed(sale,['id','batch_id','grade','channel','dispatch_at','delivery_at','inspection_at','recognized_at','quantity','price','price_basis']);
        need(['id','batch_id','grade','channel'].every(key=>name(sale[key]))
          && TIMES.slice(0,4).every(key=>utc(sale[key])) && sale.price_basis==='gross_before_deductions');
        return sale;
      });
      need(new Set(sales.map(sale=>sale.id)).size===sales.length);
      if(input.collections===null)return [];
      const rows:SaleTerms[]=[];const ids=new Set<string>();
      for(const collection of input.collections) {
        need(object(collection));closed(collection,['id','sale_id','at','amount']);
        need(name(collection.id) && name(collection.sale_id) && utc(collection.at) && !ids.has(collection.id));ids.add(collection.id);
        const sale=sales.find(sale=>sale.id===collection.sale_id);need(sale);
        const terms={sale_id:sale.id,batch_id:sale.batch_id,grade:sale.grade,channel:sale.channel,dispatch_at:sale.dispatch_at,
          delivery_at:sale.delivery_at,inspection_at:sale.inspection_at,recognized_at:sale.recognized_at,
          collection_id:collection.id,collection_at:collection.at};
        rows.push(terms as SaleTerms);
      }
      return rows;
    },
    async breakEvenPlan(body:BreakEvenSubmission):Promise<BreakEvenAccepted> {
      validateSubmission(body);const raw=await request('/v1/break-even-plans','POST',body,202);need(object(raw));
      closed(raw,['plan_id','request_sha256','plan_sha256','trial_count','registration_status','intent_job']);
      need(raw.plan_id===body.request.plan_id && hash(raw.request_sha256) && hash(raw.plan_sha256)
        && raw.trial_count===body.trials.length && raw.registration_status==='pinned_user_grid_intent');
      const intent_job=decodeJob(raw.intent_job);need(intent_job.stage==='simulation');return {...raw,intent_job} as BreakEvenAccepted;
    },
    async breakEvenResult(id:string,body:BreakEvenSubmission):Promise<BreakEvenResult> {
      validateSubmission(body);need(uuid(id));const raw=await request('/v1/jobs/'+id+'/break-even-result','GET',undefined,200,524288);need(object(raw));
      closed(raw,['plan_id','status','scope','assessment_status','input_origin','evidence_level','market_context_kind','market_hold_report_id',
        'decision_at_utc','period_start','period_end','target','variable_unit',...GRID,'zero_values','brackets','trials','hold_reason_codes']);
      const r=body.request;
      need(raw.plan_id===r.plan_id && raw.decision_at_utc===r.decision_at && raw.period_start===r.period_start && raw.period_end===r.period_end
        && raw.target===r.target && raw.variable_unit===r.variable && raw.market_context_kind==='unavailable'
        && raw.market_hold_report_id===r.market_context.hold_report_id && raw.scope==='conditional_user_grid_only'
        && raw.assessment_status==='hold' && raw.input_origin==='user' && raw.evidence_level==='assumed'
        && member(raw.status,['zero_on_grid','no_zero_on_grid','bracket_only','nonmonotone_on_grid','hold'] as const)
        && GRID.every(key=>decimal(raw[key],256) && representation(raw[key])===representation(r[key])));
      need(Array.isArray(raw.zero_values) && raw.zero_values.length<=256 && raw.zero_values.every(value=>decimal(value,256))
        && Array.isArray(raw.brackets) && raw.brackets.length<=255 && raw.brackets.every(pair=>Array.isArray(pair)
          && pair.length===2 && pair.every(value=>decimal(value,256))) && Array.isArray(raw.trials) && raw.trials.length<=256
        && Array.isArray(raw.hold_reason_codes) && raw.hold_reason_codes.length<=100
        && raw.hold_reason_codes.every(code=>typeof code==='string' && /^[A-Z][A-Z0-9_]{0,79}$/.test(code)));
      if(raw.status==='hold')need(raw.trials.length===0 && raw.zero_values.length===0 && raw.brackets.length===0);
      else {
        need(raw.trials.length===body.trials.length);
        const values:string[]=[];
        for(const trial of raw.trials) {
          need(object(trial));closed(trial,['value','target_value_krw','minimum_cash_balance_krw','cash_shortage_krw']);
          need(decimal(trial.value,256) && money(trial.target_value_krw)
            && (trial.minimum_cash_balance_krw===null || money(trial.minimum_cash_balance_krw))
            && (trial.cash_shortage_krw===null || decimal(trial.cash_shortage_krw,256)));values.push(representation(trial.value));
        }
        need(new Set(values).size===values.length && values[0]===representation(r.minimum) && values.at(-1)===representation(r.maximum)
          && raw.zero_values.every(value=>values.includes(representation(value)))
          && raw.brackets.every(pair=>values.indexOf(representation(pair[0]))>=0
            && values.indexOf(representation(pair[1]))===values.indexOf(representation(pair[0]))+1));
        if(raw.status==='zero_on_grid')need(raw.zero_values.length>0);
        if(raw.status==='bracket_only')need(raw.zero_values.length===0 && raw.brackets.length>0);
        if(raw.status==='no_zero_on_grid')need(raw.zero_values.length===0 && raw.brackets.length===0);
      }
      return raw as BreakEvenResult;
    },
  };
}

export async function submissionDigest(body:BreakEvenSubmission) {
  validateSubmission(body);
  function canonical(value:unknown):unknown {
    if(Array.isArray(value))return value.map(canonical);
    if(object(value))return Object.fromEntries(Object.keys(value).sort().map(key=>[key,canonical(value[key])]));
    return value;
  }
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(JSON.stringify(canonical(body))));
  return Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
}
