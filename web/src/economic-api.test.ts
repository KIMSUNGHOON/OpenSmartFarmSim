import { describe, it, expect } from 'vitest';
import { createApi, ApiError } from './api';
import { SOURCE_FIELDS } from './source-fields';
import type { Candidate, NumericIntent, NumericInput, RightsIntent, JointInput, EconomicResult } from './economic-api';

const time='2026-09-29T08:00:00Z';const id='11111111-1111-4111-8111-111111111111';
const meta={kind:'economic_input',record_id:'수량/#?',revision:'r1',payload_sha256:'a'.repeat(64),
  recorded_at:time,admission_kind:'contract_valid_user_assumption'};
const number:NumericInput={value:'9007199254740993.0000000001',unit:'kg',input_id:meta.record_id,revision:'r1',origin:'user',
  evidence_level:'assumed',assumption_scope:'scope',source_ref:'user-entry',available_at:time,scope_start:'2026-10-01',scope_end:'2026-10-31'};
const job={job_id:id,stage:'collection',state:'queued',attempt_count:0,max_attempts:3,created_at:time,updated_at:time,reason_code:null} as const;
const token='synthetic-economic-test-token';
function api(value:unknown,status=200,capture?:(url:string,init:RequestInit)=>void) {
  return createApi(token,async (url,init)=>{capture?.(String(url),init ?? {});return Response.json(value,{status});});
}
describe('economic HTTP boundaries',()=>{
  it('preserves exact quantity strings and encodes identifiers as query data',async ()=>{
    const record=await api({...meta,input:number},200,(url,init)=>{
      const query=new URL(url,'https://test.invalid').searchParams;
      expect(query.get('record_id')).toBe(meta.record_id);expect(init.cache).toBe('no-store');
    }).numeric(meta);
    expect(record.input.value).toBe(number.value);
  });
  it.each([{value:42},{value:'NaN'},{unit:'USD'},{tenant_id:'foreign'},{input_id:'wrong'},
    {scope_end:'2026-09-01'},{available_at:'2026-09-29T08:00:00+09:00'}])('rejects invalid numeric data %j',async change=>{
    await expect(api({...meta,input:{...number,...change}}).numeric(meta)).rejects.toBeInstanceOf(ApiError);
  });
  it('accepts a source registration only with matching version and collection intent',async ()=>{
    const body:NumericIntent={kind:'economic_input',input:number,idempotency_key:'same'};
    const saved=await api({...meta,intent_job:job},200,(_,init)=>expect(JSON.parse(String(init.body))).toEqual(body)).saveNumeric(body);
    expect(saved.intent_job.state).toBe('queued');
    await expect(api({...meta,revision:'wrong',intent_job:job}).saveNumeric(body)).rejects.toBeInstanceOf(ApiError);
  });
  it('checks page kind and the last-item cursor',async ()=>{
    expect((await api({kind:'economic_input',items:[meta],next_cursor:null}).sources('economic_input')).items).toHaveLength(1);
    await expect(api({kind:'economic_input',items:[meta],next_cursor:{record_id:'wrong',revision:'r1'}})
      .sources('economic_input')).rejects.toBeInstanceOf(ApiError);
  });
  it('uses only explicit baseline fields and rejects unknown root fields',async ()=>{
    const input=Object.fromEntries(SOURCE_FIELDS.economic_scenario.map(key=>[key,null]));
    Object.assign(input,{scenario_id:meta.record_id,scenario_revision:meta.revision,decision_at:time,
      period_start:'2026-10-01',period_end:'2026-10-31',market_context:{kind:'unavailable',hold_report_id:id}});
    const raw={...meta,kind:'economic_scenario',input};
    expect((await api(raw).baseline(meta)).market_context.hold_report_id).toBe(id);
    await expect(api({...raw,input:{...input,tenant_id:'foreign'}}).baseline(meta)).rejects.toBeInstanceOf(ApiError);
  });
  it('keeps unknown result amounts as null and binds the selected scenario',async ()=>{
    const candidate:Candidate={candidate_id:'c'.repeat(64),scenario_id:'scenario',scenario_revision:'r1',scenario_sha256:'d'.repeat(64),
      registration_status:'pinned_user_assumption',recorded_at:time,intent_job:job};
    const context={decision_at:time,market_context:{kind:'unavailable',hold_report_id:id}} as const;
    const raw={economic_result_id:'a'.repeat(64),market_scenario_result_id:'b'.repeat(64),scenario_id:'scenario',scenario_revision:'r1',
      decision_at_utc:time,formula_version:'economic-ledger-v9-sales-settlement',market_context_kind:'unavailable',market_hold_report_id:id,
      calculation_status:'hold',assessment_status:'hold',sales_totals_status:'unverified_input_arithmetic',input_origin:'user',evidence_level:'assumed',
      quantities:{harvest_kg:'1',packout_kg:'1',recognized_kg:'1',net_sold_kg:null},amounts:{gross_sales_krw:'10',revenue_krw:null,
      variable_cost_krw:null,fixed_cost_krw:null,depreciation_krw:null,management_operating_income_krw:null,operating_cash_krw:null,
      business_cash_krw:null,equity_cash_krw:null,minimum_cash_balance_krw:null,cash_shortage_krw:null},hold_reason_codes:['DETAIL_WITHHELD']};
    const result=await api(raw).economicResult(id,candidate,context);expect(result.amounts.revenue_krw).toBeNull();
    await expect(api({...raw,decision_at_utc:'2026-09-28T08:00:00Z'}).economicResult(id,candidate,context)).rejects.toBeInstanceOf(ApiError);
    await expect(api({...raw,market_hold_report_id:'22222222-2222-4222-8222-222222222222'}).economicResult(id,candidate,context)).rejects.toBeInstanceOf(ApiError);
    await expect(api({...raw,scenario_id:'wrong'}).economicResult(id,candidate,context)).rejects.toBeInstanceOf(ApiError);
    await expect(api({...raw,amounts:{...raw.amounts,revenue_krw:10}}).economicResult(id,candidate,context)).rejects.toBeInstanceOf(ApiError);
  });
  it('registers complete rights using only the matching collection receipt',async ()=>{
    const intent:RightsIntent={kind:'input_rights',input:{input_id:number.input_id,revision:number.revision,raw_sha256:'b'.repeat(64),
      origin:'user',evidence_level:'assumed',rights:{use:'allowed',display:'allowed',redistribute:'denied'},available_at:time,
      effective_start:number.scope_start,effective_end:number.scope_end,immutable:true},idempotency_key:'rights'};
    const receipt={...meta,kind:'input_rights',intent_job:job};
    await expect(api(receipt).saveRights({...intent,input:null as unknown as RightsIntent['input']})).rejects.toBeInstanceOf(ApiError);
    expect((await api(receipt).saveRights(intent)).kind).toBe('input_rights');
    await expect(api({...receipt,kind:'economic_input'}).saveRights(intent)).rejects.toBeInstanceOf(ApiError);
    await expect(api({...receipt,intent_job:{...job,stage:'simulation'}}).saveRights(intent)).rejects.toBeInstanceOf(ApiError);
    await expect(api(receipt).saveRights({...intent,input:{...intent.input,tenant_id:'foreign'} as RightsIntent['input']})).rejects.toBeInstanceOf(ApiError);
  });
  it('reads complete canonical joint edits and refuses unknown nested fields',async ()=>{
    const {scope_start:_,scope_end:__,...inline}=number;
    const input:JointInput={schema_version:'1',shock_id:'joint',revision:'r1',baseline_sha256:'b'.repeat(64),decision_at:time,
      effective_start:number.scope_start,effective_end:number.scope_end,available_at:time,origin:'user',evidence_level:'assumed',
      rights:{use:'allowed',display:'allowed',redistribute:'denied'},drivers:[{kind:'macro',record_id:'macro',revision:'r1',origin:'user',
        evidence_level:'assumed',available_at:time,effective_start:number.scope_start,effective_end:number.scope_end,
        rights:{use:'allowed',display:'allowed',redistribute:'denied'},hypothesis:'Self-authored test',source_ref:'test',
        causal_status:'unvalidated_user_hypothesis',changes:[{event_group:'variable_costs',event_id:'production',field:'quantity',number:inline,time:null,reference:null}]}],
      contract_caps:[],settlement_bindings:[]};
    const receipt={...meta,kind:'joint_shock',record_id:'joint',input};
    const joint=await api(receipt).joint({record_id:'joint',revision:'r1'});expect(joint.input).toEqual(input);
    for(const change of [{number:{...inline,value:42}},{time:time},{tenant_id:'foreign'}]) {
      const altered=structuredClone(input);Object.assign(altered.drivers[0]!.changes[0]!,change);
      await expect(api({...receipt,input:altered}).joint({record_id:'joint',revision:'r1'})).rejects.toBeInstanceOf(ApiError);
    }
  });

});


it('binds cash pages to the exact completed result and preserves KST boundary UTC strings',async ()=>{
  const context={economic_result_id:'a'.repeat(64),market_scenario_result_id:'b'.repeat(64),scenario_id:'derived',scenario_revision:'r2',
    decision_at_utc:time,formula_version:'economic-ledger-v9-sales-settlement',market_context_kind:'unavailable',market_hold_report_id:id,
    calculation_status:'hold',assessment_status:'hold',input_origin:'user',evidence_level:'assumed'} as const;
  const completed:EconomicResult={...context,sales_totals_status:'unverified_input_arithmetic',
    quantities:{harvest_kg:'0',packout_kg:'0',recognized_kg:'0',net_sold_kg:null},
    amounts:{gross_sales_krw:null,revenue_krw:null,variable_cost_krw:null,fixed_cost_krw:null,depreciation_krw:null,
      management_operating_income_krw:null,operating_cash_krw:null,business_cash_krw:null,equity_cash_krw:null,
      minimum_cash_balance_krw:null,cash_shortage_krw:null},hold_reason_codes:[]};
  const row={month:'2026-10',opening_balance_krw:'-9007199254740993.0000000001',net_cash_krw:'0',
    closing_balance_krw:'-9007199254740993.0000000001',minimum_balance_krw:'-9007199254740993.0000000001',
    minimum_at_utc:'2026-09-30T15:00:00Z',cash_shortage_krw:'9007199254740993.0000000001'};
  const page={...context,schema_version:'economic-cash-page-v1',calendar_timezone:'Asia/Seoul',series_status:'available',total_months:1,
    limit:12,after_month:null,next_month_cursor:null,monthly_cash:[row],hold_reason_codes:[]};
  const read=await api(page,200,url=>expect(new URL(url,'https://test.invalid').searchParams.get('limit')).toBe('12')).economicCash(id,completed);
  expect(read.monthly_cash![0]!.opening_balance_krw).toBe(row.opening_balance_krw);
  expect(read.monthly_cash![0]!.minimum_at_utc).toBe(row.minimum_at_utc);
  for(const changes of [{economic_result_id:'c'.repeat(64)},{market_hold_report_id:'22222222-2222-4222-8222-222222222222'},
      {calendar_timezone:'UTC'},{next_month_cursor:'2026-11'},{monthly_cash:[{...row,net_cash_krw:0}]},
      {monthly_cash:[{...row,month:'2026-13'}]},{monthly_cash:[row,row]},{tenant_id:'foreign'}]) {
    await expect(api({...page,...changes}).economicCash(id,completed)).rejects.toBeInstanceOf(ApiError);
  }
  expect((await api({...page,series_status:'unavailable',total_months:null,monthly_cash:null}).economicCash(id,completed)).monthly_cash).toBeNull();
});
