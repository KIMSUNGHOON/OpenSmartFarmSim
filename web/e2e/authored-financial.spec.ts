import { test,expect,type Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import { financialResponses,economicId,assessmentId } from './authored-financial-fixture';
import { authoredJobId,authoredRunId,authoredResponses } from './authored-thermal-fixture';

const token='synthetic-authored-financial-browser-token';
async function install(page:Page,historyDelayMs=0) {
  const fixture=financialResponses(),posts:{path:string;body:string}[]=[];
  await page.route('**/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    if(route.request().headers().authorization==='Bearer '+token+'-foreign')
      return route.fulfill({status:403,json:{private:'another account'}});
    if(path==='/v1/authored-runs/catalog')return route.fulfill({json:fixture.catalog});
    if(path.endsWith('/authored-economic-input'))return route.fulfill({json:fixture.selected});
    if(path.endsWith('/authored-financial-history')){
      if(historyDelayMs)await new Promise<void>(resolve=>setTimeout(resolve,historyDelayMs));
      return route.fulfill({json:fixture.history});
    }
    if(path==='/v1/economic-results' || path==='/v1/assessments'){
      posts.push({path,body:route.request().postData()!});
      return route.fulfill({status:202,json:{...(path.endsWith('assessments')?fixture.assessment:fixture.economic),state:'queued',attempt_count:0,reason_code:null}});
    }
    if(path==='/v1/jobs/'+economicId)return route.fulfill({json:fixture.economic});
    if(path==='/v1/jobs/'+assessmentId)return route.fulfill({json:fixture.assessment});
    if(path.endsWith('/economic-result'))return route.fulfill({json:fixture.result});
    if(path.endsWith('/economic-cash-flow'))return route.fulfill({json:new URL(route.request().url()).searchParams.has('after_month')?fixture.lastCash:fixture.cash});
    if(path.endsWith('/hold-report'))return route.fulfill({json:fixture.report});
    if(path.endsWith('/authored-run') || path==='/v1/authored-runs/'+encodeURIComponent(authoredRunId))
      return route.fulfill({json:authoredResponses().summary});
    if(path.endsWith('/series'))return route.fulfill({json:authoredResponses().series});
    throw new Error('Unexpected contract request '+path);
  });
  return {fixture,posts};
}
async function connect(page:Page) {
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).press('Enter');
  await page.getByRole('button',{name:'07 작성 Run 경제·평가',exact:true}).press('Enter');
}
async function select(page:Page) {
  await page.getByRole('button',{name:'저장 Run 목록 조회',exact:true}).press('Enter');
  await page.getByRole('button',{name:/저장된 합성 열 Run.*경제·평가 선택/}).press('Enter');
  await expect(page.getByRole('button',{name:'같은 Run 3D 열기',exact:true})).toBeEnabled();
}
async function prepareNew(page:Page) {
  await expect(page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:/경제 계산 기록.*현재 기록 조회/})).toBeEnabled();
  await page.getByRole('button',{name:/경제 계산 기록.*현재 기록 조회/}).press('Enter');
  await expect(page.getByText('9,007,199,254,740,993.0000000001 원',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'새 경제 요청 준비',exact:true}).press('Enter');
  await expect(page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true})).toBeEnabled();
}
async function money(page:Page) {
  await prepareNew(page);
  await page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true}).click();
  await expect(page.getByText('경제 작업: 대기 중',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'경제 상태·결과 확인',exact:true}).click();
  await expect(page.getByText('9,007,199,254,740,993.0000000001 원',{exact:true})).toBeVisible();
}

test('saved Run keyboard selection, exact conditional money, cash pages and held assessment',async({page})=>{
  const {fixture,posts}=await install(page,500);const errors:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(['error','warning'].includes(message.type()))errors.push(message.type());});
  await page.setViewportSize({width:1440,height:1000});await connect(page);await select(page);
  await prepareNew(page);await page.getByRole('button',{name:'경제·평가 기록 새로고침',exact:true}).click();
  await expect(page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true})).toBeDisabled();
  await money(page);
  const income=page.getByRole('heading',{name:'관리용 영업이익',exact:true}).locator('..');
  await expect(income).toContainText('미확인');await expect(income).not.toContainText('0 원');
  await page.getByRole('button',{name:'작성 Run 월별 현금 조회',exact:true}).click();
  await expect(page.getByRole('rowheader',{name:'2026-12',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'다음 현금 페이지',exact:true}).click();
  await expect(page.getByRole('rowheader',{name:'2027-01',exact:true})).toBeVisible();
  await expect(page.getByRole('rowheader',{name:'2026-12',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'작성 Run 평가 요청',exact:true}).click();
  await page.getByRole('button',{name:'작성 평가 상태 확인',exact:true}).click();
  await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible();
  await expect(page.getByText('같은 조건의 작물 대응 비교',{exact:true})).toBeVisible();
  expect(posts).toHaveLength(2);
  expect(JSON.parse(posts[0]!.body)).toEqual({...fixture.selected.calculation_input,idempotency_key:expect.stringMatching(/^web-authored-money-v1:/)});
  expect(JSON.parse(posts[1]!.body)).toEqual({run_job_id:authoredJobId,economic_job_id:economicId,
    idempotency_key:expect.stringMatching(/^web-authored-assessment-v1:/)});
  await mkdir('../research/artifacts',{recursive:true});
  await page.screenshot({path:'../research/artifacts/authored-financial-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'../research/artifacts/authored-financial-phone.png',fullPage:true});
  await page.setViewportSize({width:320,height:900});await page.addStyleTag({content:'html {font-size:200%;}'});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  expect(errors).toEqual([]);
});

test('unresolved economic request preserves its body through navigation and blocks reset',async({page})=>{
  const {fixture}=await install(page);const bodies:string[]=[];
  await page.route('**/v1/economic-results',route=>{
    bodies.push(route.request().postData()!);return bodies.length===1?route.abort()
      :route.fulfill({status:202,json:{...fixture.economic,state:'queued'}});
  });
  await connect(page);await select(page);await prepareNew(page);await page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('같은 요청');
  await expect(page.getByRole('button',{name:'연결 해제',exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'저장 Run 목록 조회',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();
  await expect(page.getByRole('button',{name:'새 입력',exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'07 작성 Run 경제·평가',exact:true}).click();
  await page.getByRole('button',{name:'같은 경제 요청 다시 확인',exact:true}).click();
  await expect(page.getByText('경제 작업: 대기 중',{exact:true})).toBeVisible();
  expect(bodies).toHaveLength(2);expect(bodies[1]).toBe(bodies[0]);
  await expect(page.getByRole('button',{name:'연결 해제',exact:true})).toBeEnabled();
});

test('assessment response loss keeps exact parents and restores their current money before hold',async({page})=>{
  const {fixture}=await install(page);const bodies:string[]=[];
  await page.route('**/v1/assessments',route=>{
    bodies.push(route.request().postData()!);return bodies.length===1?route.abort()
      :route.fulfill({status:202,json:{...fixture.assessment,state:'queued'}});
  });
  await connect(page);await select(page);await money(page);
  await page.getByRole('button',{name:'작성 Run 평가 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('같은 요청');
  await expect(page.getByText('9,007,199,254,740,993.0000000001 원',{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'같은 작성 평가 다시 확인',exact:true}).click();
  await page.getByRole('button',{name:'작성 평가 상태 확인',exact:true}).click();
  await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible();
  expect(bodies).toHaveLength(2);expect(bodies[1]).toBe(bodies[0]);
});

test('history recovers after reload using GET and account reconnect clears results',async({page})=>{
  const {posts}=await install(page);await connect(page);await select(page);
  await page.getByRole('button',{name:/작성 평가 기록.*현재 기록 조회/}).click();
  await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible();
  await page.reload();await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'07 작성 Run 경제·평가',exact:true}).click();await select(page);
  await page.getByRole('button',{name:/경제 계산 기록.*현재 기록 조회/}).click();
  await expect(page.getByText('9,007,199,254,740,993.0000000001 원',{exact:true})).toBeVisible();
  await page.getByLabel('접근 토큰').fill(token+'-foreign');await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'07 작성 Run 경제·평가',exact:true}).click();
  await expect(page.getByText('9,007,199,254,740,993.0000000001 원',{exact:true})).toHaveCount(0);
  await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'저장 Run 목록 조회',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('권한');expect(posts).toHaveLength(0);
  expect(await page.locator('body').innerText()).not.toContain('another account');
});

test('bounded refusal releases the intent while malformed positive admission remains unresolved',async({page})=>{
  const {fixture}=await install(page);const bodies:string[]=[];
  await page.route('**/v1/economic-results',route=>{
    bodies.push(route.request().postData()!);return bodies.length===1
      ?route.fulfill({status:422,json:{private:'must not render'}})
      :route.fulfill({status:202,json:{...fixture.economic,stage:'research'}});
  });
  await connect(page);await select(page);await prepareNew(page);await page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('연결');
  await expect(page.getByRole('button',{name:'연결 해제',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('검증할 수 없어');
  await expect(page.getByRole('button',{name:'연결 해제',exact:true})).toBeDisabled();
  expect(JSON.parse(bodies[0]!).idempotency_key).not.toBe(JSON.parse(bodies[1]!).idempotency_key);
  expect(await page.locator('body').innerText()).not.toContain('must not render');
});

test('revoked result or altered selection clears money and disables further assessment',async({page})=>{
  const {fixture}=await install(page);await connect(page);await select(page);await money(page);
  await page.route('**/v1/jobs/'+economicId+'/economic-result',route=>route.fulfill({status:503,json:{private:'restricted source'}}));
  await page.getByRole('button',{name:'경제 상태·결과 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('근거');
  await expect(page.getByText('9,007,199,254,740,993.0000000001 원',{exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'작성 Run 평가 요청',exact:true})).toHaveCount(0);
  await page.route('**/v1/jobs/'+authoredJobId+'/authored-economic-input',route=>route.fulfill({json:{...fixture.selected,
    calculation_input:{...fixture.selected.calculation_input,thermal_job_id:economicId}}}));
  await page.getByRole('button',{name:/저장된 합성 열 Run.*경제·평가 선택/}).click();
  await expect(page.getByRole('alert')).toContainText('연결');
  await expect(page.getByRole('button',{name:'같은 Run 3D 열기',exact:true})).toHaveCount(0);
});

test('authored workspace opens the financial selection and the same saved 3D parent',async({page})=>{
  await install(page);await connect(page);await page.getByRole('button',{name:'04 작성 농장 실행',exact:true}).click();
  await page.getByRole('button',{name:'저장 Run 보기',exact:true}).click();
  await page.getByRole('button',{name:'경제·평가 열기',exact:true}).click();
  await expect(page.getByRole('heading',{name:'작성 Run의 비용과 평가',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'같은 Run 3D 열기',exact:true}).click();
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',authoredRunId);
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-replay-kind','authored');
  await expect(page.locator('.zone-canvas')).toBeVisible();
  expect(Number(await page.locator('.zone-canvas').getAttribute('data-draw-calls'))).toBeGreaterThan(0);
});
