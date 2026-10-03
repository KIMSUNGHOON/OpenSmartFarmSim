import { describe,it,expect } from 'vitest';
import { createApi,ApiError } from './api';
import { authoredJobId } from '../e2e/authored-thermal-fixture';
import { financialResponses,economicId,assessmentId } from '../e2e/authored-financial-fixture';

function api(value:unknown,status=200,capture?:(url:string,init:RequestInit)=>void) {
  return createApi('synthetic-financial-test-token',async(url,init)=>{
    capture?.(String(url),init ?? {});return Response.json(value,{status});
  });
}
describe('authored financial boundaries',()=>{
  it('derives only a currently bound V3 input and sends a closed identical intent',async()=>{
    const fixture=financialResponses();let body='';
    const selected=await api(fixture.selected,200,(url,init)=>{
      expect(url).toBe('/v1/jobs/'+authoredJobId+'/authored-economic-input');expect(init.cache).toBe('no-store');
    }).authoredEconomicSelection(authoredJobId);
    const intent={...selected.calculation_input,idempotency_key:'web-authored-money-v1:retry'};
    const client=api({...fixture.economic,state:'queued'},202,(_,init)=>{
      expect(init.method).toBe('POST');if(body)expect(String(init.body)).toBe(body);body=String(init.body);
    });
    expect((await client.calculateAuthored(intent)).job_id).toBe(economicId);
    await client.calculateAuthored(intent);expect(JSON.parse(body)).toEqual(intent);
  });
  it.each(['parent','farm','revision','registration','scope','version','extra'])('refuses %s selection mismatch',async kind=>{
    const fixture=financialResponses(),value=fixture.selected;
    if(kind==='parent')value.calculation_input.thermal_job_id=economicId;
    if(kind==='farm')value.calculation_input.authored_scenario_id='other';
    if(kind==='revision')value.calculation_input.authored_scenario_revision='r2';
    if(kind==='registration')value.calculation_input.registration_sha256='0'.repeat(64);
    if(kind==='scope')Object.assign(value.thermal_run,{claim_scope:'crop_forecast'});
    if(kind==='version')Object.assign(value.calculation_input,{input_version:'economic-calculation-input-v1'});
    if(kind==='extra')Object.assign(value.calculation_input,{tenant_id:'foreign'});
    await expect(api(value).authoredEconomicSelection(authoredJobId)).rejects.toBeInstanceOf(ApiError);
  });
  it('reads recovery links as metadata and respects sub-millisecond ordering',async()=>{
    const fixture=financialResponses();
    fixture.history.items[0]!.job.created_at='2026-10-01T00:00:00.123457Z';
    fixture.history.items[1]!.job.job_id='eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee';
    const page=await api(fixture.history).authoredFinancialHistory(fixture.selected);
    expect(page.verification).toBe('requires_current_read');expect(page.items[0]!.economic_job!.job_id).toBe(economicId);
    expect(page.items.map(item=>item.kind)).toEqual(['assessment','economic']);
  });
  it.each(['run','parent','duplicate','stage','state','cursor','order','extra'])('refuses %s history mismatch',async kind=>{
    const fixture=financialResponses(),value=fixture.history;
    if(kind==='run')value.run_id='authored-thermal-run-v1:'+'0'.repeat(64);
    if(kind==='parent')value.thermal_job_id=economicId;
    if(kind==='duplicate')value.items[1]!.job.job_id=assessmentId;
    if(kind==='stage')value.items[0]!.job.stage='research';
    if(kind==='state')value.items[0]!.job.state='succeeded';
    if(kind==='cursor')Object.assign(value,{next_cursor:{created_at:value.items[1]!.job.created_at,job_id:economicId}});
    if(kind==='order')value.items.reverse();
    if(kind==='extra')Object.assign(value,{amounts:{profit:'1'}});
    await expect(api(value).authoredFinancialHistory(fixture.selected)).rejects.toBeInstanceOf(ApiError);
  });
  it('preserves exact money/null values and reuses the verified monthly cash identity',async()=>{
    const fixture=financialResponses();
    const result=await api(fixture.result).authoredEconomicResult(economicId,fixture.selected);
    expect(result.amounts.revenue_krw).toBe('9007199254740993.0000000001');
    expect(result.amounts.management_operating_income_krw).toBeNull();
    expect((await api(fixture.cash).economicCash(economicId,result)).next_month_cursor).toBe('2026-12');
    expect((await api(fixture.lastCash).economicCash(economicId,result,'2026-12')).monthly_cash![0]!.month).toBe('2027-01');
  });
  it('reads the exact current economic job before any completed money',async()=>{
    const fixture=financialResponses();
    expect(await api(fixture.economic).authoredEconomicJob(economicId)).toEqual(fixture.economic);
  });
  it.each(['id','stage','state'])('refuses %s current economic job mismatch',async kind=>{
    const value={...financialResponses().economic};
    if(kind==='id')value.job_id=assessmentId;
    if(kind==='stage')value.stage='assessment';
    if(kind==='state')value.state='researching';
    await expect(api(value).authoredEconomicJob(economicId)).rejects.toBeInstanceOf(ApiError);
  });
  it.each(['scenario','revision','time','microseconds','claim','number','extra'])('refuses %s economic result mismatch',async kind=>{
    const fixture=financialResponses(),value=fixture.result;
    if(kind==='scenario')value.scenario_id='wrong';
    if(kind==='revision')value.scenario_revision='r2';
    if(kind==='time')value.decision_at_utc='2026-01-02T00:00:00Z';
    if(kind==='microseconds'){
      fixture.selected.thermal_run.decision_at_utc='2026-10-15T08:00:00.123456Z';
      value.decision_at_utc='2026-10-15T08:00:00.123457Z';
    }
    if(kind==='claim')Object.assign(value,{assessment_status:'proceed'});
    if(kind==='number')Object.assign(value.amounts,{revenue_krw:42});
    if(kind==='extra')Object.assign(value,{selected_crop:'tomato'});
    await expect(api(value).authoredEconomicResult(economicId,fixture.selected)).rejects.toBeInstanceOf(ApiError);
  });
});
