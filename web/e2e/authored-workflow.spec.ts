import { test,expect,type Page } from '@playwright/test';
import { authoredJobId,authoredRunId,authoredResponses } from './authored-thermal-fixture';

const token='synthetic-authored-workflow-token-only';
const reviewId='33333333-3333-4333-8333-333333333333';
const digest='a'.repeat(64);
const stamp='2026-09-30T00:00:00Z';
const job=(id:string,stage:'collection'|'collection_review'|'simulation',state:'queued'|'succeeded')=>({
  job_id:id,stage,state,attempt_count:state==='queued'?0:1,max_attempts:3,
  created_at:stamp,updated_at:stamp,reason_code:null,
});
const registration={scenario_id:'farm-1',scenario_revision:'r1',scenario_sha256:digest,
  farm_sha256:'b'.repeat(64),numeric_input_sha256:'c'.repeat(64),
  rights_sha256:'d'.repeat(64),registration_status:'registered_unpublished_inputs',
  intent_job:job('22222222-2222-4222-8222-222222222222','collection','queued')};

async function connect(page:Page) {
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await page.getByLabel('시나리오 ID').fill('farm-1');
  await page.getByLabel('판본',{exact:true}).fill('r1');
  await page.getByRole('button',{name:'등록 기록 확인'}).click();
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible();
}

test('saved farm catalog opens a server rechecked registration',async({page})=>{
  let allowed=true;
  const paths:string[]=[];
  await page.route('**/v1/**',route=>{
    const path=new URL(route.request().url()).pathname;
    paths.push(path);
    if(path==='/v1/farm-authored-inputs/catalog')
      return route.fulfill({json:{items:[registration],next_cursor:null}});
    if(path==='/v1/farm-authored-inputs')
      return allowed ? route.fulfill({json:registration})
        : route.fulfill({status:422,json:{error:{code:'farm_authoring_hold',message:'Unavailable'}}});
    throw new Error('unexpected API path '+path);
  });
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await page.getByRole('button',{name:'목록 보기'}).click();
  await expect(page.locator('.authored-catalog-list button')).toHaveCount(1);
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  allowed=false;
  await page.locator('.authored-catalog-list button').click();
  await expect(page.getByRole('alert')).toContainText('현재 입력·권리·해제 근거');
  await expect(page.getByText('입력 등록됨 · 계산 전')).toHaveCount(0);
  allowed=true;
  await page.locator('.authored-catalog-list button').click();
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible();
  expect(paths).toEqual(['/v1/farm-authored-inputs/catalog',
    '/v1/farm-authored-inputs','/v1/farm-authored-inputs']);
});

test('saved authored jobs reopen a completed server Run after reconnect',async({page})=>{
  const calls:string[]=[];
  const data=authoredResponses();
  await page.route('**/v1/**',route=>{
    const path=new URL(route.request().url()).pathname;
    calls.push(route.request().method()+' '+path);
    if(path==='/v1/farm-authored-inputs')return route.fulfill({json:registration});
    if(path==='/v1/farm-authored-inputs/activity')return route.fulfill({json:{
      scenario_id:'farm-1',scenario_revision:'r1',registration_sha256:digest,
      items:[{kind:'simulation',job:job(authoredJobId,'simulation','succeeded'),
        review_job:job(reviewId,'collection_review','succeeded')}],next_cursor:null}});
    if(path==='/v1/jobs/'+authoredJobId)
      return route.fulfill({json:job(authoredJobId,'simulation','succeeded')});
    if(path==='/v1/jobs/'+reviewId)
      return route.fulfill({json:job(reviewId,'collection_review','succeeded')});
    if(path==='/v1/jobs/'+authoredJobId+'/authored-run' ||
       path==='/v1/authored-runs/'+encodeURIComponent(authoredRunId))
      return route.fulfill({json:data.summary});
    if(path==='/v1/authored-runs/'+encodeURIComponent(authoredRunId)+'/series')
      return route.fulfill({json:data.series});
    throw new Error('unexpected API path '+path);
  });
  await connect(page);
  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible();
  await page.getByRole('button',{name:'작업 이력 보기'}).click();
  await expect(page.locator('.authored-catalog-list button')).toHaveCount(1);
  await page.setViewportSize({width:390,height:844});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.locator('.authored-catalog-list button').click();
  await expect(page.getByRole('button',{name:'3D 재생 열기'})).toBeEnabled();
  await page.getByRole('button',{name:'3D 재생 열기'}).click();
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',authoredRunId);
  expect(calls.every(value=>value.startsWith('GET '))).toBe(true);
});

test('stored farm moves through review and simulation jobs into authored 3D',async({page})=>{
  const calls:{path:string;method:string;body:unknown}[]=[];
  const errors:string[]=[];
  const data=authoredResponses();
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/v1/**',async route=>{
    const request=route.request();
    expect(request.headers().authorization).toBe('Bearer '+token);
    const url=new URL(request.url()),path=url.pathname;
    const method=request.method();
    const body=request.postDataJSON() as unknown;
    calls.push({path,method,body});
    if(path==='/v1/farm-authored-inputs' && method==='GET') {
      expect(url.searchParams.get('scenario_id')).toBe('farm-1');
      expect(url.searchParams.get('scenario_revision')).toBe('r1');
      return route.fulfill({json:registration});
    }
    if(path==='/v1/farm-authored-reviews' && method==='POST')
      return route.fulfill({status:202,json:job(reviewId,'collection_review','queued')});
    if(path==='/v1/jobs/'+reviewId)
      return route.fulfill({json:job(reviewId,'collection_review','succeeded')});
    if(path==='/v1/authored-runs' && method==='POST')
      return route.fulfill({status:202,json:job(authoredJobId,'simulation','queued')});
    if(path==='/v1/jobs/'+authoredJobId)
      return route.fulfill({json:job(authoredJobId,'simulation','succeeded')});
    if(path==='/v1/jobs/'+authoredJobId+'/authored-run' ||
       path==='/v1/authored-runs/'+encodeURIComponent(authoredRunId))
      return route.fulfill({json:data.summary});
    if(path==='/v1/authored-runs/'+encodeURIComponent(authoredRunId)+'/series')
      return route.fulfill({json:data.series});
    throw new Error('unexpected API path '+path);
  });
  await connect(page);
  await page.getByRole('button',{name:'입력 검토 요청'}).click();
  await expect(page.getByText(reviewId,{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'상태 다시 확인'}).first().click();
  await expect(page.getByRole('button',{name:'열 계산 요청'})).toBeEnabled();
  await page.getByRole('button',{name:'열 계산 요청'}).click();
  await expect(page.getByRole('button',{name:'상태 다시 확인'})).toHaveCount(2);
  await page.getByRole('button',{name:'상태 다시 확인'}).last().click();
  await expect(page.getByRole('button',{name:'3D 재생 열기'})).toBeEnabled();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.setViewportSize({width:1440,height:1000});
  await page.getByRole('heading',{name:'작성 농장 실행',exact:true}).scrollIntoViewIfNeeded();
  await page.screenshot({path:'../research/artifacts/authored-workflow-desktop.png'});
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('heading',{name:'작성 농장 실행',exact:true}).scrollIntoViewIfNeeded();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:'../research/artifacts/authored-workflow-phone.png'});
  await page.getByRole('button',{name:'3D 재생 열기'}).click();
  await expect(page.getByLabel('완료된 열 작업 ID')).toHaveValue(authoredJobId);
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',authoredRunId);
  expect(calls.find(item=>item.path==='/v1/farm-authored-reviews')?.body).toEqual({
    schema_version:'farm-authored-review-request-v1',scenario_id:'farm-1',
    scenario_revision:'r1',registration_sha256:digest,
    idempotency_key:expect.stringMatching(/^review-[0-9a-f-]+$/),
  });
  expect(calls.find(item=>item.path==='/v1/authored-runs')?.body).toEqual({
    schema_version:'authored-thermal-simulation-request-v1',review_job_id:reviewId,
    scenario_id:'farm-1',scenario_revision:'r1',registration_sha256:digest,
    idempotency_key:expect.stringMatching(/^run-[0-9a-f-]+$/),
  });
  expect(errors).toEqual([]);
});

test('missing independent release stays a hold and retries preserve one intent key',async({page})=>{
  const keys:string[]=[];
  await page.route('**/v1/**',async route=>{
    const request=route.request(),path=new URL(request.url()).pathname;
    if(path==='/v1/farm-authored-inputs')return route.fulfill({json:registration});
    if(path==='/v1/farm-authored-reviews')
      return route.fulfill({status:202,json:job(reviewId,'collection_review','queued')});
    if(path==='/v1/jobs/'+reviewId)
      return route.fulfill({json:job(reviewId,'collection_review','succeeded')});
    if(path==='/v1/authored-runs') {
      keys.push((request.postDataJSON() as {idempotency_key:string}).idempotency_key);
      return route.fulfill({status:422,json:{code:'authored_simulation_hold'}});
    }
    throw new Error('unexpected API path '+path);
  });
  await connect(page);
  await page.getByRole('button',{name:'입력 검토 요청'}).click();
  await page.getByRole('button',{name:'상태 다시 확인'}).first().click();
  await page.getByRole('button',{name:'열 계산 요청'}).click();
  await expect(page.getByRole('alert')).toContainText('현재 입력·권리·해제 근거');
  await expect(page.getByRole('button',{name:'3D 재생 열기'})).toBeDisabled();
  await page.getByRole('button',{name:'열 계산 요청'}).click();
  expect(keys).toHaveLength(2);
  expect(keys[0]).toBe(keys[1]);
});

test('last farm is rechecked on reconnect and cleared when access is revoked',async({page})=>{
  let allowed=true;
  let reads=0;
  await page.route('**/v1/**',async route=>{
    const request=route.request();
    expect(request.headers().authorization).toBe('Bearer '+token);
    expect(new URL(request.url()).pathname).toBe('/v1/farm-authored-inputs');
    expect(request.method()).toBe('GET');
    reads++;
    return allowed ? route.fulfill({json:registration})
      : route.fulfill({status:403,json:{code:'access_denied'}});
  });
  await connect(page);
  const stored=await page.evaluate(()=>sessionStorage.getItem('ossf.authored.last-farm.v1'));
  expect(JSON.parse(stored ?? 'null')).toEqual({scenario_id:'farm-1',
    scenario_revision:'r1',scenario_sha256:digest});
  expect(stored).not.toContain(token);

  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible();
  await expect(page.getByLabel('시나리오 ID')).toHaveValue('farm-1');
  expect(reads).toBe(2);

  await page.evaluate(key=>sessionStorage.setItem(key,JSON.stringify({scenario_id:'farm-1',
    scenario_revision:'r1',scenario_sha256:'e'.repeat(64)})),'ossf.authored.last-farm.v1');
  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await expect(page.getByRole('alert')).toContainText('서버 응답의 판본');
  await expect(page.getByText('입력 등록됨 · 계산 전')).toHaveCount(0);
  expect(await page.evaluate(()=>sessionStorage.getItem('ossf.authored.last-farm.v1'))).toBeNull();
  await page.getByLabel('시나리오 ID').fill('farm-1');
  await page.getByLabel('판본',{exact:true}).fill('r1');
  await page.getByRole('button',{name:'등록 기록 확인'}).click();
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible();
  expect(reads).toBe(4);

  allowed=false;
  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await expect(page.getByRole('alert')).toContainText('필요한 권한이 없습니다');
  await expect(page.getByText('입력 등록됨 · 계산 전')).toHaveCount(0);
  await expect.poll(()=>page.evaluate(()=>sessionStorage.getItem('ossf.authored.last-farm.v1')))
    .toBeNull();
  expect(reads).toBe(5);
});
