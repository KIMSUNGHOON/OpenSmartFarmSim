// Self-authored browser DTOs; actual server/worker proof is a separate TLS/PG smoke.
import {test,expect} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {SOURCE_FIELDS} from '../src/source-fields';
import {submissionDigest,type BreakEvenSubmission} from '../src/break-even-api';

const time='2026-09-27T08:00:00Z',id='11111111-1111-4111-8111-111111111111';
const job={job_id:id,stage:'simulation',state:'queued',attempt_count:0,max_attempts:3,created_at:time,updated_at:time,reason_code:null};
const collection={...job,stage:'collection'};
const baselineId='기준 원장 '+('long-id-'.repeat(18));
function meta(kind:string,record_id:string,hash='a') {return {kind,record_id,revision:'r1',payload_sha256:hash.repeat(64),
  recorded_at:time,admission_kind:'contract_valid_user_assumption'};}
const baseline={...Object.fromEntries(SOURCE_FIELDS.economic_scenario.map(key=>[key,null])),scenario_id:baselineId,scenario_revision:'r1',
  decision_at:time,period_start:'2026-10-01',period_end:'2026-10-31',market_context:{kind:'unavailable',hold_report_id:id},
  sales:[{id:'sale',batch_id:'batch',grade:'grade',channel:'direct',dispatch_at:'2026-10-01T03:00:00Z',delivery_at:'2026-10-01T04:00:00Z',
    inspection_at:'2026-10-01T05:00:00Z',recognized_at:'2026-10-01T06:00:00Z',quantity:{},price:{},price_basis:'gross_before_deductions'}],
  collections:[{id:'collection',sale_id:'sale',at:'2026-10-02T06:00:00Z',amount:{}}]};
function shock(index:number) {
  const rights={use:'allowed',display:'allowed',redistribute:'denied'};
  const scope={origin:'user',evidence_level:'assumed',available_at:time,effective_start:'2026-10-01',effective_end:'2026-10-31',rights};
  return {schema_version:'1',shock_id:'joint-'+index,revision:'r1',baseline_sha256:'a'.repeat(64),decision_at:time,...scope,
    drivers:['demand','supply','macro'].map((kind,position)=>({...scope,kind,record_id:kind,revision:'r1',hypothesis:'직접 작성한 시험 가설',
      source_ref:'self-authored',causal_status:'unvalidated_user_hypothesis',changes:[{event_group:'sales',event_id:'sale',field:'price',
        number:{value:String(index===0 ? 20 : 32),unit:'KRW/kg',input_id:'price-'+position,revision:'r1',origin:'user',evidence_level:'assumed',
          assumption_scope:'test',source_ref:'self-authored',available_at:time},time:null,reference:null}]})),contract_caps:[],settlement_bindings:[]};
}
async function setup(page:import('@playwright/test').Page,missing=false) {
  await page.route('**/v1/market-user-sources?*',async route=>{
    const kind=new URL(route.request().url()).searchParams.get('kind');
    await route.fulfill({json:{kind,items:kind==='economic_scenario' ? [meta(kind,baselineId)] : [meta('joint_shock','joint-0','b'),meta('joint_shock','joint-1','c')],next_cursor:null}});
  });
  await page.route('**/v1/market-user-sources/record?*',async route=>{
    const query=new URL(route.request().url()).searchParams,kind=query.get('kind'),record=query.get('record_id');
    const index=record==='joint-0' ? 0 : 1;
    await route.fulfill({json:kind==='economic_scenario' ? {...meta(kind,baselineId),input:{...baseline,collections:missing ? null : baseline.collections}}
      : {...meta('joint_shock','joint-'+index,index===0 ? 'b' : 'c'),input:shock(index)}});
  });
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill('synthetic-browser-token-abcdefghijklmnopqrstuvwxyz');
  await page.getByRole('button',{name:'연결 설정'}).click();await page.getByRole('button',{name:'03 경제 가정·계산'}).click();
  const area=page.getByRole('region',{name:'손익분기 계획과 결과',exact:true});
  const picker=area.getByRole('region',{name:'손익분기 기준 원장',exact:true});await picker.getByRole('button',{name:'목록 조회'}).click();await picker.locator('li button').click();
  await expect(area.getByLabel('손익분기 판매·수금')).toBeVisible();return area;
}
for(const lost of ['trial','plan'] as const)test(`break-even lost ${lost} preserves exact acknowledged phases and actual result semantics`,async({page})=>{
  const scenarioCalls:{body:Record<string,unknown>;key:string}[]=[];const plans:Record<string,unknown>[]=[];let aborted=false,completed=false,receiptReads=0,malformedResult=false;
  await page.route('**/v1/break-even-plans/receipt?*',async route=>{
    receiptReads++;const digest=await submissionDigest(plans[0] as unknown as BreakEvenSubmission);
    expect(new URL(route.request().url()).searchParams.get('submission_sha256')).toBe(digest);
    if(receiptReads===1){await route.fulfill({status:404,json:{error:{code:'not_found',message:'not found'}}});return;}
    const r=plans[0]!.request as Record<string,unknown>;
    await route.fulfill({json:{plan_id:r.plan_id,submission_sha256:digest,intent_status:'stored',intent_job:job}});
  });
  await page.route('**/v1/economic-scenarios',async route=>{
    const body=route.request().postDataJSON(),index=body.request.shock.shock_id==='joint-0' ? 0 : 1;scenarioCalls.push({body,key:body.idempotency_key});
    if(lost==='trial' && index===1 && !aborted){aborted=true;await route.abort();return;}
    await route.fulfill({json:{candidate_id:(index===0 ? 'd' : 'e').repeat(64),scenario_id:'trial-'+index,scenario_revision:'r1',scenario_sha256:(index===0 ? 'f' : 'a').repeat(64),
      registration_status:'pinned_user_assumption',recorded_at:time,intent_job:collection}});
  });
  await page.route('**/v1/break-even-plans',async route=>{
    const body=route.request().postDataJSON();plans.push(body);
    expect(Object.keys(body).sort()).toEqual(['request','trials']);expect(body.trials.map((pin:{scenario_id:string})=>pin.scenario_id)).toEqual(['trial-0','trial-1']);
    if(lost==='plan' && !aborted){aborted=true;await route.abort();return;}
    await route.fulfill({status:202,json:{plan_id:body.request.plan_id,request_sha256:'b'.repeat(64),plan_sha256:'c'.repeat(64),trial_count:2,
      registration_status:'pinned_user_grid_intent',intent_job:job}});
  });
  await page.route('**/v1/jobs/'+id,async route=>route.fulfill({json:{...job,state:completed ? 'succeeded' : 'queued'}}));
  await page.route('**/v1/jobs/'+id+'/break-even-result',async route=>{
    const r=plans.at(-1)!.request as Record<string,unknown>;
    await route.fulfill({json:{plan_id:malformedResult ? 'different-plan' : r.plan_id,status:lost==='trial' ? 'bracket_only' : 'zero_on_grid',scope:'conditional_user_grid_only',assessment_status:'hold',
      input_origin:'user',evidence_level:'assumed',market_context_kind:'unavailable',market_hold_report_id:id,decision_at_utc:time,
      period_start:baseline.period_start,period_end:baseline.period_end,target:r.target,variable_unit:r.variable,minimum:r.minimum,maximum:r.maximum,step:r.step,
      zero_values:lost==='trial' ? [] : ['32'],brackets:lost==='trial' ? [['20','32']] : [],
      trials:[{value:'20',target_value_krw:'-9007199254740993.0000000001',minimum_cash_balance_krw:null,cash_shortage_krw:null},
        {value:'32',target_value_krw:lost==='trial' ? '9007199254740993.0000000001' : '0',minimum_cash_balance_krw:'0',cash_shortage_krw:'0'}],hold_reason_codes:[]}});
  });
  const area=await setup(page);
  await expect(area.getByRole('button',{name:'선택한 시험으로 손익분기 요청'})).toBeDisabled();expect(scenarioCalls).toHaveLength(0);
  await area.getByLabel('손익분기 판매·수금').selectOption(JSON.stringify(['sale','collection']));
  await area.getByLabel('손익분기 목표').selectOption('oi');await area.getByLabel('바꿀 변수').selectOption('KRW/kg');
  await area.getByLabel(/^최소 시험값/).fill('20');await area.getByLabel(/^최대 시험값/).fill('32');await area.getByLabel(/^시험값 증분/).fill('12');
  const picker=area.getByRole('region',{name:'손익분기 시험 공동 가정',exact:true});await picker.getByRole('button',{name:'목록 조회'}).click();
  for(const index of [0,1]) {await picker.locator('li button').nth(index).click();await area.getByRole('button',{name:'이 공동 가정을 시험에 추가'}).click();}
  await expect(area.locator('.break-even-trials li')).toHaveCount(2);
  await area.getByRole('button',{name:'선택한 시험으로 손익분기 요청'}).press('Enter');await expect(area.getByRole('alert')).toContainText('같은 계획 요청');
  await expect(area.getByLabel(/^최소 시험값/)).toHaveAttribute('readonly','');await expect(page.getByRole('button',{name:'연결 해제'})).toBeDisabled();
  await expect(area.getByRole('button',{name:'새 손익분기 계획 작성'})).toHaveCount(0);await expect(area.locator('tbody')).toHaveCount(0);
  await page.getByRole('button',{name:'02 작업과 근거'}).click();await page.getByRole('button',{name:'03 경제 가정·계산'}).click();
  await area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'}).press('Enter');
  if(lost==='plan') {
    await expect(area.getByRole('alert')).toContainText('저장된 계획 접수를 아직 확인하지 못했습니다');
    await expect(page.getByRole('button',{name:'연결 해제'})).toBeDisabled();await expect(area.getByRole('button',{name:'새 손익분기 계획 작성'})).toHaveCount(0);
    await area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'}).press('Enter');
  }
  await expect(area.getByText('손익분기 작업: 대기 중',{exact:true})).toBeVisible();
  expect(scenarioCalls).toHaveLength(lost==='trial' ? 3 : 2);if(lost==='trial')expect(scenarioCalls[1]).toEqual(scenarioCalls[2]);else {expect(plans).toHaveLength(1);expect(receiptReads).toBe(2);}
  const refresh=area.getByRole('button',{name:'손익분기 상태·결과 확인'}),queued=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/jobs/'+id);
  await refresh.click();await queued;await expect(refresh).toBeEnabled();await expect(area.locator('tbody')).toHaveCount(0);
  completed=true;await refresh.press('Enter');await expect(area.getByRole('heading',{name:'손익분기 결과 · 평가 상태: 판단 보류'})).toBeVisible();
  await expect(area.getByText('완료된 서버 손익분기 결과를 확인했습니다.',{exact:true})).toBeVisible();
  const first=area.locator('tbody tr').first();await expect(first.locator('td')).toHaveText(['-9,007,199,254,740,993.0000000001 원','미확인','미확인']);
  if(lost==='trial'){await expect(area.getByText(/정확한 손익분기점이 아닙니다/)).toBeVisible();await expect(area.getByRole('list',{name:'교차 구간'})).toContainText('20 ~ 32');}
  else await expect(area.getByText('나열한 시험의 0인 값: 32 KRW/kg',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeEnabled();
  if(lost==='plan') {
    malformedResult=true;await refresh.click();
    await expect(area.getByRole('alert')).toContainText('서버 응답이 고정한 계획과 맞지 않아');
    await expect(area.getByText('요청 응답을 확인하지 못했습니다. 보류 사유를 확인하세요.',{exact:true})).toBeVisible();
    await expect(area.locator('tbody')).toHaveCount(0);
    await expect(area.getByRole('heading',{name:'손익분기 결과 · 평가 상태: 판단 보류'})).toHaveCount(0);
  }
  if(lost==='trial')for(const width of [320,768,1440]) {
    await page.setViewportSize({width,height:900});await page.evaluate(()=>document.fonts.ready);
    for(const size of ['16px','32px']) {
      await page.addStyleTag({content:':root{font-size:'+size+'}'});
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      const table=area.getByRole('region',{name:'손익분기 시험 표 가로 스크롤'});await table.evaluate(element=>{element.scrollLeft=0;});
      if(await table.evaluate(element=>element.scrollWidth>element.clientWidth)) {await table.focus();await page.keyboard.press('ArrowRight');await expect.poll(()=>table.evaluate(element=>element.scrollLeft)).toBeGreaterThan(0);}
      const capture=process.env.OSSF_UI_CAPTURE_DIR;if(capture){await mkdir(capture,{recursive:true});await area.screenshot({path:`${capture}/break-even-${width}-${size}.png`});}
    }
  }
});
test('missing collection records cannot become zero cash or a fabricated sale selection',async({page})=>{
  const area=await setup(page,true);await expect(area.getByText('선택할 판매·수금 기록이 없습니다. 실제 원장 기록을 먼저 등록해야 합니다.',{exact:true})).toBeVisible();
  await expect(area.getByLabel('손익분기 판매·수금').locator('option')).toHaveCount(1);await expect(area.getByRole('button',{name:'선택한 시험으로 손익분기 요청'})).toBeDisabled();
  await expect(area.locator('tbody')).toHaveCount(0);
});
