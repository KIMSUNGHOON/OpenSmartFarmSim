import { test, expect, type Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { SOURCE_FIELDS } from '../src/source-fields';

const time='2026-09-29T08:00:00Z';
const id='11111111-1111-4111-8111-111111111111';
const token='synthetic-economic-browser-token';
const exact='9007199254740993.0000000001';
const recordId='입력-'+ 'long-id-'.repeat(20);
const job={job_id:id,stage:'collection',state:'queued',attempt_count:0,max_attempts:3,created_at:time,updated_at:time,reason_code:null};
function meta(kind:string,record_id:string) {
  return {kind,record_id,revision:'r1',payload_sha256:'a'.repeat(64),recorded_at:time,admission_kind:'contract_valid_user_assumption'};
}
const number={value:exact,unit:'KRW',input_id:recordId,revision:'r1',origin:'user',evidence_level:'assumed',
  assumption_scope:'synthetic scope',source_ref:'self-authored test',available_at:time,scope_start:'2026-10-01',scope_end:'2027-10-31'};
// These mocks exercise browser projection/retry only. Actual source validation is covered by the TLS/PG integration.
const baseline={...Object.fromEntries(SOURCE_FIELDS.economic_scenario.map(key=>[key,null])),scenario_id:'baseline',scenario_revision:'r1',
  decision_at:time,period_start:'2026-10-01',period_end:'2027-10-31',market_context:{kind:'unavailable',hold_report_id:id}};
const shock={...Object.fromEntries(SOURCE_FIELDS.joint_shock.map(key=>[key,null])),shock_id:'shock',revision:'r1',decision_at:time,baseline_sha256:'a'.repeat(64)};
const candidate={candidate_id:'b'.repeat(64),scenario_id:'candidate',scenario_revision:'r2',scenario_sha256:'c'.repeat(64),
  registration_status:'pinned_user_assumption',recorded_at:time,intent_job:job};
const calculation={...job,stage:'simulation'};
const result={economic_result_id:'d'.repeat(64),market_scenario_result_id:'e'.repeat(64),scenario_id:'candidate',scenario_revision:'r2',decision_at_utc:time,
  formula_version:'economic-ledger-v9-sales-settlement',market_context_kind:'unavailable',market_hold_report_id:id,
  calculation_status:'hold',assessment_status:'hold',sales_totals_status:'unverified_input_arithmetic',input_origin:'user',evidence_level:'assumed',
  quantities:{harvest_kg:'1',packout_kg:'1',recognized_kg:'1',net_sold_kg:null},amounts:{gross_sales_krw:exact,revenue_krw:exact,
  variable_cost_krw:null,fixed_cost_krw:null,depreciation_krw:null,management_operating_income_krw:'-'+exact,
  operating_cash_krw:null,business_cash_krw:null,equity_cash_krw:null,minimum_cash_balance_krw:null,cash_shortage_krw:null},hold_reason_codes:['DETAIL_WITHHELD']};
async function connect(page:Page) {
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정'}).press('Enter');
  await page.getByRole('button',{name:'03 경제 가정·계산'}).press('Enter');
}
async function reads(page:Page) {
  await page.route('**/v1/market-user-sources?*',async route=>{
    const kind=new URL(route.request().url()).searchParams.get('kind')!;
    await route.fulfill({json:{kind,items:[meta(kind,kind==='economic_input' ? recordId : kind==='economic_scenario' ? 'baseline' : 'shock')],next_cursor:null}});
  });
  await page.route('**/v1/market-user-sources/record?*',async route=>{
    const kind=new URL(route.request().url()).searchParams.get('kind')!;
    const input=kind==='economic_input' ? number : kind==='economic_scenario' ? baseline : shock;
    await route.fulfill({json:{...meta(kind,kind==='economic_input' ? recordId : kind==='economic_scenario' ? 'baseline' : 'shock'),input}});
  });
}
async function choose(page:Page,name:string) {
  const picker=page.getByRole('region',{name,exact:true});
  const list=picker.getByRole('button',{name:'목록 조회'});
  await expect(list).toBeEnabled();await list.press('Enter');
  const item=picker.locator('li button').first();await expect(item).toBeEnabled();await item.press('Enter');
  if(name==='숫자 가정') await expect(page.getByLabel(/^새 가정값/)).toBeVisible();
  else await expect(page.locator('.selected-source').filter({hasText:name==='기준 원장' ? '선택 원장:' : '선택 공동 가정:'})).toBeVisible();
}
async function fillNumber(page:Page) {
  await choose(page,'숫자 가정');
  await page.getByLabel(/^새 가정값/).fill(exact);
  await page.getByLabel('가정을 알게 된 날짜 (UTC)').fill('2026-09-29');
  await page.getByLabel('가정을 알게 된 시각 (UTC)').fill('08:00');
}

test('lost numeric registration keeps exact decimal, canonical time and immutable retry across navigation',async ({page})=>{
  await reads(page);const bodies:string[]=[];
  await page.route('**/v1/market-user-sources',async route=>{
    bodies.push(route.request().postData()!);
    if(bodies.length===1){await route.abort();return;}
    const input=route.request().postDataJSON().input;
    await route.fulfill({json:{...meta('economic_input',recordId),revision:input.revision,intent_job:job}});
  });
  await connect(page);await fillNumber(page);
  await page.getByRole('button',{name:'새 가정 판본 등록'}).press('Enter');
  await expect(page.getByRole('alert')).toContainText('같은 요청');
  await expect(page.getByLabel(/^새 가정값/)).not.toBeEditable();
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeDisabled();
  await expect(page.getByRole('button',{name:'새 수정 시작'})).toHaveCount(0);
  await page.getByRole('button',{name:'02 작업과 근거'}).click();
  await page.getByRole('button',{name:'03 경제 가정·계산'}).click();
  await page.getByRole('button',{name:'같은 가정 요청 다시 확인'}).press('Enter');
  await expect(page.getByText('새 가정 판본 접수됨',{exact:true})).toBeVisible();
  expect(bodies).toHaveLength(2);expect(bodies[1]).toBe(bodies[0]);
  expect(JSON.parse(bodies[0]!).input.available_at).toBe(time);
  expect(JSON.parse(bodies[0]!).input.value).toBe(exact);
  expect(JSON.parse(bodies[0]!).input.revision).not.toBe('r1');
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeEnabled();
});

for(const lostPhase of ['scenario','calculation'] as const) {
test(`lost ${lostPhase} after a saved numeric revision retries only the pending phase and renders actual completion`,async ({page})=>{
  await reads(page);const scenarioBodies:string[]=[];const calculationBodies:string[]=[];let completed=false;
  await page.route('**/v1/market-user-sources',async route=>{
    await route.fulfill({json:{...meta('economic_input',recordId),revision:route.request().postDataJSON().input.revision,intent_job:job}});
  });
  await page.route('**/v1/economic-scenarios',async route=>{
    scenarioBodies.push(route.request().postData()!);
    if(lostPhase==='scenario' && scenarioBodies.length===1){await route.abort();return;}
    await route.fulfill({json:candidate});
  });
  await page.route('**/v1/economic-results',async route=>{
    calculationBodies.push(route.request().postData()!);
    if(lostPhase==='calculation' && calculationBodies.length===1){await route.abort();return;}
    await route.fulfill({status:202,json:calculation});
  });
  await page.route('**/v1/jobs/'+id,async route=>{
    const state=completed ? 'succeeded' : 'queued';
    await new Promise(resolve=>setTimeout(resolve,200));
    await route.fulfill({json:{...calculation,state}});
  });
  await page.route('**/v1/jobs/'+id+'/economic-result',async route=>route.fulfill({json:result}));
  const cashQueries:string[]=[];
  await page.route('**/v1/jobs/'+id+'/economic-cash-flow?*',async route=>{
    const query=new URL(route.request().url()).searchParams;cashQueries.push(query.toString());
    const after=query.get('after_month');
    const rows=Array.from({length:13},(_,offset)=>{
      const at=new Date(Date.UTC(2026,9+offset,1));const month=at.toISOString().slice(0,7);
      return {month,opening_balance_krw:'-'+exact,net_cash_krw:'0',closing_balance_krw:'-'+exact,
        minimum_balance_krw:'-'+exact,minimum_at_utc:new Date(at.getTime()-9*3600000).toISOString(),cash_shortage_krw:exact};
    });
    const common=Object.fromEntries(['economic_result_id','market_scenario_result_id','scenario_id','scenario_revision','decision_at_utc',
      'formula_version','market_context_kind','market_hold_report_id','calculation_status','assessment_status','input_origin','evidence_level',
      'hold_reason_codes'].map(key=>[key,result[key as keyof typeof result]]));
    await route.fulfill({json:{...common,schema_version:'economic-cash-page-v1',calendar_timezone:'Asia/Seoul',limit:12,after_month:after,
      series_status:lostPhase==='scenario' ? 'unavailable' : 'available',total_months:lostPhase==='scenario' ? null : 13,
      monthly_cash:lostPhase==='scenario' ? null : after ? rows.slice(12) : rows.slice(0,12),
      next_month_cursor:lostPhase==='scenario' || after ? null : '2027-09'}});
  });
  await connect(page);await fillNumber(page);await page.getByRole('button',{name:'새 가정 판본 등록'}).click();
  await expect(page.getByText('새 가정 판본 접수됨',{exact:true})).toBeVisible();
  await choose(page,'기준 원장');await choose(page,'수급·거시 공동 가정');
  await page.getByRole('button',{name:'선택한 가정으로 계산 요청'}).click();
  await expect(page.getByRole('alert')).toContainText('같은 요청');
  const retry=page.getByRole('button',{name:'같은 계산 요청 다시 확인'});
  await expect(retry).toBeEnabled();await retry.press('Enter');
  await expect(page.getByText('계산 작업: 대기 중',{exact:true})).toBeVisible();
  expect(scenarioBodies).toHaveLength(lostPhase==='scenario' ? 2 : 1);
  expect(calculationBodies).toHaveLength(lostPhase==='calculation' ? 2 : 1);
  const repeated=lostPhase==='scenario' ? scenarioBodies : calculationBodies;expect(repeated[1]).toBe(repeated[0]);
  await expect(page.locator('.economic-totals')).toHaveCount(0);
  const refresh=page.getByRole('button',{name:'계산 상태·결과 확인'});
  const queuedRead=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/jobs/'+id);
  await refresh.click();
  expect((await (await queuedRead).json()).state).toBe('queued');
  await expect(refresh).toBeEnabled();
  await expect(page.locator('.economic-totals')).toHaveCount(0);
  completed=true;await refresh.press('Enter');
  await expect(page.getByRole('heading',{name:'경제 결과의 평가 상태: 판단 보류',exact:true})).toBeVisible();
  await expect(page.locator('.economic-totals strong')).toHaveText(['9,007,199,254,740,993.0000000001 원','-9,007,199,254,740,993.0000000001 원','미확인']);
  expect(cashQueries).toHaveLength(0);await expect(page.locator('.cash-table')).toHaveCount(0);
  const cash=page.getByRole('region',{name:'월별 현금흐름',exact:true});
  await cash.getByRole('button',{name:'월별 현금흐름 조회'}).press('Enter');
  if(lostPhase==='scenario') {
    await expect(cash.getByRole('status')).toContainText('미확인');await expect(cash.locator('table')).toHaveCount(0);
  } else {
    await expect(cash.locator('tbody tr')).toHaveCount(12);
    const first=cash.locator('tbody tr').first();await expect(first.locator('th')).toHaveText('2026-10');
    await expect(first.locator('td').first()).toHaveText('-9,007,199,254,740,993.0000000001 원');
    await expect(first.locator('td').last()).toHaveText('2026-09-30T15:00:00.000Z');
    await cash.getByRole('button',{name:'다음 월 기록'}).press('Enter');
    await expect(cash.locator('tbody tr')).toHaveCount(1);await expect(cash.locator('tbody th')).toHaveText('2027-10');
    expect(cashQueries[1]).toBe('limit=12&after_month=2027-09');
    await expect(cash.getByRole('button',{name:'다음 월 기록'})).toHaveCount(0);
  }

  for(const width of [320,768,1440]) {
    await page.setViewportSize({width,height:900});await page.evaluate(()=>document.fonts.ready);
    for(const size of ['16px','32px']) {
      await page.addStyleTag({content:':root{font-size:'+size+'}'});
      const overflow=await page.evaluate(()=>Array.from(document.querySelectorAll('main *')).filter(e=>
        (!e.closest('.cash-table-scroll') || e.closest('.cash-table-scroll')===e) && e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,class:e.className})).slice(0,8));
      expect(overflow,`${width}px with ${size} root text`).toEqual([]);
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      await expect(page.getByRole('button',{name:'계산 상태·결과 확인'})).toBeVisible();
      if(lostPhase==='calculation') {
        const table=cash.getByRole('region',{name:'월별 현금흐름 표 가로 스크롤'});
        await table.evaluate(element=>{element.scrollLeft=0;});await table.focus();await page.keyboard.press('ArrowRight');
        await expect.poll(()=>table.evaluate(element=>element.scrollLeft)).toBeGreaterThan(0);
        await table.evaluate(element=>{element.scrollLeft=0;});
      }
      const capture=process.env.OSSF_UI_CAPTURE_DIR;
      if(capture && lostPhase==='calculation') {
        await mkdir(capture,{recursive:true});
        await page.evaluate(()=>scrollTo(0,0));
        await page.screenshot({path:`${capture}/economics-${width}-${size}.png`,fullPage:true});
        await cash.screenshot({path:`${capture}/cash-${width}-${size}.png`});
      }
    }
  }
});
}
