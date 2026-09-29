import {it,expect} from 'vitest';
import {createApi,ApiError} from './api';
import {SOURCE_FIELDS} from './source-fields';
import type {Baseline} from './economic-api';
import {submissionDigest} from './break-even-api';

const id='11111111-1111-4111-8111-111111111111',time='2026-09-27T08:00:00Z';
const baseline:Baseline={kind:'economic_scenario',record_id:'기준/#?',revision:'r1',payload_sha256:'a'.repeat(64),recorded_at:time,
  admission_kind:'contract_valid_user_assumption',decision_at:time,period_start:'2026-10-01',period_end:'2026-10-31',
  market_context:{kind:'unavailable',hold_report_id:id}};
const sale={sale_id:'sale',batch_id:'batch',grade:'grade',channel:'direct',dispatch_at:'2026-10-01T03:00:00Z',
  delivery_at:'2026-10-01T04:00:00Z',inspection_at:'2026-10-01T05:00:00Z',recognized_at:'2026-10-01T06:00:00Z',
  collection_id:'collection',collection_at:'2026-10-02T06:00:00Z'};
const request={schema_version:'1',plan_id:'plan',baseline:{scenario_id:baseline.record_id,revision:'r1',sha256:baseline.payload_sha256},
  market_context:baseline.market_context,decision_at:time,period_start:baseline.period_start,period_end:baseline.period_end,
  target:'oi',variable:'KRW/kg',minimum:'20',maximum:'32',step:'12',...sale} as const;
const submission={request,trials:[{scenario_id:'trial-0',revision:'r1',scenario_sha256:'b'.repeat(64)},
  {scenario_id:'trial-1',revision:'r1',scenario_sha256:'c'.repeat(64)}]};

it('matches the Python canonical full-submission digest and reads only its historical intent',async ()=>{
  const digest=await submissionDigest(submission);
  expect(digest).toBe('47279b8132aad8daaf58650c7004f5e84c374af57145c204295bf53c0c3a3543');
  const receipt={plan_id:'plan',submission_sha256:digest,intent_status:'stored',intent_job:job};
  const read=await api(receipt,path=>{
    const url=new URL(path,'https://test.invalid');expect(url.pathname).toBe('/v1/break-even-plans/receipt');
    expect(url.searchParams.get('submission_sha256')).toBe(digest);
  }).breakEvenReceipt(submission);
  expect(read.intent_status).toBe('stored');
  await expect(api({...receipt,submission_sha256:'f'.repeat(64)}).breakEvenReceipt(submission)).rejects.toBeInstanceOf(ApiError);
});
const job={job_id:id,stage:'simulation',state:'queued',attempt_count:0,max_attempts:3,created_at:time,updated_at:time,reason_code:null};
const accepted={plan_id:'plan',request_sha256:'d'.repeat(64),plan_sha256:'e'.repeat(64),trial_count:2,
  registration_status:'pinned_user_grid_intent',intent_job:job};
function api(payload:unknown,inspect?:(path:string,body:unknown)=>void) {
  const fetcher:typeof fetch=async (url,options)=>{inspect?.(String(url),options?.body ? JSON.parse(String(options.body)) : undefined);
    return new Response(JSON.stringify(payload),{status:200,headers:{'content-type':'application/json'}});};
  return createApi('synthetic-token-abcdefghijklmnopqrstuvwxyz',fetcher);
}

it('projects only exact stored sale/collection terms without inventing missing collections',async ()=>{
  const {kind:_,decision_at:__,period_start:___,period_end:____,market_context:_____,...meta}=baseline;
  const raw={...meta,kind:'economic_scenario',input:{...Object.fromEntries(SOURCE_FIELDS.economic_scenario.map(key=>[key,null])),
    scenario_id:baseline.record_id,scenario_revision:'r1',decision_at:time,period_start:baseline.period_start,period_end:baseline.period_end,
    market_context:baseline.market_context,sales:[{id:'sale',batch_id:'batch',grade:'grade',channel:'direct',dispatch_at:sale.dispatch_at,
      delivery_at:sale.delivery_at,inspection_at:sale.inspection_at,recognized_at:sale.recognized_at,quantity:{},price:{},price_basis:'gross_before_deductions'}],
    collections:[{id:'collection',sale_id:'sale',at:sale.collection_at,amount:{}}]}};
  expect(await api(raw,path=>expect(new URL(path,'https://test.invalid').searchParams.get('record_id')).toBe(baseline.record_id)).breakEvenSales(baseline)).toEqual([sale]);
  expect(await api({...raw,input:{...raw.input,collections:null}}).breakEvenSales(baseline)).toEqual([]);
  await expect(api({...raw,payload_sha256:'f'.repeat(64)}).breakEvenSales(baseline)).rejects.toBeInstanceOf(ApiError);
  await expect(api({...raw,input:{...raw.input,sales:[{...raw.input.sales[0],dispatch_at:'not-time'}]}}).breakEvenSales(baseline)).rejects.toBeInstanceOf(ApiError);
});

it('submits only the request and exact pins and binds the admitted simulation',async ()=>{
  const client=createApi('synthetic-token-abcdefghijklmnopqrstuvwxyz',async (url,options)=>{
    expect(url).toBe('/v1/break-even-plans');expect(JSON.parse(String(options?.body))).toEqual(submission);
    return new Response(JSON.stringify(accepted),{status:202,headers:{'content-type':'application/json'}});
  });
  expect((await client.breakEvenPlan(submission)).intent_job.job_id).toBe(id);
  for(const changed of [{...accepted,plan_id:'wrong'},{...accepted,trial_count:3},{...accepted,intent_job:{...job,stage:'research'}}]) {
    const forged=createApi('synthetic-token-abcdefghijklmnopqrstuvwxyz',async ()=>new Response(JSON.stringify(changed),{status:202,headers:{'content-type':'application/json'}}));
    await expect(forged.breakEvenPlan(submission)).rejects.toBeInstanceOf(ApiError);
  }
});

const result={plan_id:'plan',status:'bracket_only',scope:'conditional_user_grid_only',assessment_status:'hold',input_origin:'user',evidence_level:'assumed',
  market_context_kind:'unavailable',market_hold_report_id:id,decision_at_utc:time,period_start:baseline.period_start,period_end:baseline.period_end,
  target:'oi',variable_unit:'KRW/kg',minimum:'20',maximum:'32',step:'12',zero_values:[],brackets:[['20','32']],
  trials:[{value:'20',target_value_krw:'-9007199254740993.0000000001',minimum_cash_balance_krw:null,cash_shortage_krw:null},
    {value:'32',target_value_krw:'9007199254740993.0000000001',minimum_cash_balance_krw:'0',cash_shortage_krw:'0'}],hold_reason_codes:[]};
it('binds completed grid results and preserves precise money, null cash and brackets',async ()=>{
  const read=await api(result).breakEvenResult(id,submission);expect(read.trials[0]!.target_value_krw).toBe(result.trials[0]!.target_value_krw);
  expect(read.trials[0]!.cash_shortage_krw).toBeNull();expect(read.brackets).toEqual([['20','32']]);
  for(const change of [{plan_id:'wrong'},{target:'operating_cash'},{market_hold_report_id:'22222222-2222-4222-8222-222222222222'},
    {scope:'forecast'},{trials:[{...result.trials[0],target_value_krw:0}]},{zero_values:['20']},{tenant_id:'foreign'}])
    await expect(api({...result,...change}).breakEvenResult(id,submission)).rejects.toBeInstanceOf(ApiError);
  const held={...result,status:'hold',trials:[],brackets:[],hold_reason_codes:['TARGET_UNRESOLVED']};
  expect((await api(held).breakEvenResult(id,submission)).trials).toEqual([]);
});
