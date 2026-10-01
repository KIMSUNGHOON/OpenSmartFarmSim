// Actual browser/HTTPS/PG stores; the CLI/reviewer and all source inputs are synthetic.
import { chromium,expect } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { createInterface } from 'node:readline';
import { once } from 'node:events';

const [origin,thermal,lease,expectedPath]=process.argv.slice(2);
const workerLease=Number(lease);
if(new URL(origin).hostname!=='127.0.0.1' || !origin.startsWith('https://') ||
  !Number.isInteger(workerLease) || workerLease<1 || workerLease>300)throw new Error('Invalid isolated test configuration');
const expected=JSON.parse(await readFile(expectedPath,'utf8'));
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true});
const page=await context.newPage();const input=createInterface({input:process.stdin});
const errors=[],captureWarnings=[],posts=[],responses=[],started=new Map();
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{
  const text=message.text();
  const readback=/^\[\.WebGL-0x[0-9a-f]+\]GL Driver Message \(OpenGL, Performance, GL_CLOSE_PATH_NV, High\): GPU stall due to ReadPixels(?: \(this message will no longer repeat\))?$/;
  if(message.type()==='warning' && readback.test(text))captureWarnings.push('gpu_read_pixels_stall');
  else if(['error','warning'].includes(message.type()))errors.push(message.type()+': '+text);
});
page.on('request',request=>{if(request.url().includes('/v1/')){
  started.set(request,performance.now());
  if(request.method()==='POST')posts.push({path:new URL(request.url()).pathname,body:request.postDataJSON()});
}});
page.on('response',response=>{
  const request=response.request();
  if(started.has(request))responses.push({path:new URL(response.url()).pathname,status:response.status(),
    header_seconds:(performance.now()-started.get(request))/1000});
});
async function signal(name) {
  const stop=new AbortController(),timer=setTimeout(()=>stop.abort(),workerLease*1000);
  try {expect((await once(input,'line',{signal:stop.signal}))[0]).toBe(name);}
  finally {clearTimeout(timer);}
}
async function connect() {
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill('synthetic-authored-financial-browser-'+'a'.repeat(32));
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'07 작성 Run 경제·평가',exact:true}).click();
}
async function selectRun() {
  await page.getByRole('button',{name:'저장 Run 목록 조회',exact:true}).click();
  await page.getByRole('button',{name:/저장된 합성 열 Run.*경제·평가 선택/}).click();
  await expect(page.getByRole('button',{name:'같은 Run 3D 열기',exact:true})).toBeEnabled({timeout:90_000});
}
async function reference(name) {
  const summary=page.getByText(name,{exact:true});await summary.click();
  return (await summary.locator('..').locator('code').innerText()).trim();
}
try {
  await page.goto(origin);await connect();await selectRun();
  await expect(page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:/경제 계산 기록.*현재 기록 조회/}).click();
  await expect(page.getByText('경제 작업: 작업 완료',{exact:true})).toBeVisible({timeout:90_000});
  await page.getByRole('button',{name:'새 경제 요청 준비',exact:true}).click();
  await page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true}).click();
  await expect(page.getByText('경제 작업: 대기 중',{exact:true})).toBeVisible({timeout:90_000});
  const economic=await reference('경제 작업 ID');
  expect(posts[0].path).toBe('/v1/economic-results');
  const {idempotency_key,...submitted}=posts[0].body;
  expect(idempotency_key).toMatch(/^web-authored-money-v1:/);expect(submitted).toEqual(expected.input);
  process.stdout.write(JSON.stringify({event:'economic-queued',job_id:economic})+'\n');
  await signal('economic-ready');
  await page.getByRole('button',{name:'경제 상태·결과 확인',exact:true}).click();
  await expect(page.getByText('경제 작업: 작업 완료',{exact:true})).toBeVisible({timeout:90_000});
  await page.getByText('조건부 비용·현금 합계',{exact:true}).click();
  for(const field of ['revenue_krw','management_operating_income_krw','cash_shortage_krw',
    'variable_cost_krw','fixed_cost_krw','depreciation_krw','operating_cash_krw','business_cash_krw','equity_cash_krw']){
    const shown=await page.locator('[data-money-field="'+field+'"]').innerText();
    expect(expected.amounts[field]===null?shown:shown.replaceAll(',','').replace(/ 원$/,'')).toBe(expected.amounts[field]??'미확인');
  }
  await page.getByRole('button',{name:'작성 Run 월별 현금 조회',exact:true}).click();
  const first=expected.cash.monthly_cash[0];
  await expect(page.getByRole('rowheader',{name:first.month,exact:true})).toBeVisible({timeout:90_000});
  const row=page.getByRole('rowheader',{name:first.month,exact:true}).locator('..');
  const cells=await row.locator('td').allInnerTexts();
  expect(cells.map(value=>value.replaceAll(',','').replace(/ 원$/,''))).toEqual([
    first.opening_balance_krw,first.net_cash_krw,first.closing_balance_krw,first.minimum_balance_krw,first.minimum_at_utc,first.cash_shortage_krw]);
  await page.getByRole('button',{name:'작성 Run 평가 요청',exact:true}).click();
  await expect(page.getByText('평가 작업: 대기 중',{exact:true})).toBeVisible({timeout:90_000});
  const assessment=await reference('작성 평가 작업 ID');
  expect(posts[1].body).toEqual({run_job_id:thermal,economic_job_id:economic,idempotency_key:expect.stringMatching(/^web-authored-assessment-v1:/)});
  process.stdout.write(JSON.stringify({event:'assessment-queued',job_id:assessment,economic_job_id:economic})+'\n');
  await signal('assessment-ready');
  await page.getByRole('button',{name:'작성 평가 상태 확인',exact:true}).click();
  await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible({timeout:90_000});
  await page.reload();await connect();await selectRun();
  await page.getByRole('button',{name:/작성 평가 기록.*현재 기록 조회/}).click();
  await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible({timeout:90_000});
  expect(await reference('작성 평가 작업 ID')).toBe(assessment);
  await expect(page.getByText('서버가 기록한 누락 근거 6개입니다.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'같은 Run 3D 열기',exact:true}).click();
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',expected.run_id,{timeout:90_000});
  await expect(page.locator('.zone-canvas')).toBeVisible();
  expect(Number(await page.locator('.zone-canvas').getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  expect(posts).toHaveLength(2);expect(errors).toEqual([]);
  for(const path of ['/v1/authored-runs/catalog','/v1/jobs/'+thermal+'/authored-economic-input',
    '/v1/jobs/'+thermal+'/authored-financial-history','/v1/economic-results','/v1/jobs/'+economic,
    '/v1/jobs/'+economic+'/economic-result','/v1/jobs/'+economic+'/economic-cash-flow',
    '/v1/assessments','/v1/jobs/'+assessment,'/v1/jobs/'+assessment+'/hold-report',
    '/v1/jobs/'+thermal+'/authored-run','/v1/authored-runs/'+encodeURIComponent(expected.run_id)+'/series'])
    expect(responses.some(value=>value.path===path)).toBe(true);
  expect(responses.every(value=>[200,202].includes(value.status) && value.header_seconds<30)).toBe(true);
  process.stdout.write(JSON.stringify({event:'verified',post_count:posts.length,hold_count:6,
    https_responses:responses.length,max_response_header_seconds:Math.max(...responses.map(value=>value.header_seconds)),
    client_timeout_seconds:30,console_errors:errors.length,gpu_capture_warnings:captureWarnings.length,point_count:120})+'\n');
} finally {input.close();await context.close();await browser.close();}
