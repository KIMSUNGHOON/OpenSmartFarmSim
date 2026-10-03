import { test,expect,type Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

const thermal='11111111-1111-4111-8111-111111111111';
const economic='22222222-2222-4222-8222-222222222222';
const id='33333333-3333-4333-8333-333333333333';
const token='synthetic-assessment-browser-token';
const queued={job_id:id,stage:'assessment',state:'queued',attempt_count:0,max_attempts:3,
  created_at:'2026-10-01T00:00:00Z',updated_at:'2026-10-01T00:00:00Z',reason_code:null};
const held={...queued,state:'hold',attempt_count:1,reason_code:'validated_hold'};
const report={job_id:id,stage:'assessment',hold_id:thermal,status:'hold',recorded_at:held.updated_at,
  reason_code:'evidence_missing',missing_evidence:['market_source_g0','eligible_crop_candidates',
    'farm_scenario_binding','local_measurements_g2','future_validation_g3a','paired_comparison_g3b'],
  missing_evidence_count:6};

async function connect(page:Page) {
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).press('Enter');
  await page.getByRole('button',{name:'06 계산 평가'}).press('Enter');
}
async function parents(page:Page) {
  await page.getByLabel('완료 열 계산 작업 ID').fill(thermal);
  await page.getByLabel('완료 경제 계산 작업 ID').fill(economic);
}

test('keyboard admission and held evidence render on desktop and phone without recommending a crop',async({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  page.on('console',message=>{if(message.type()==='error'||message.type()==='warning')errors.push(message.text());});
  const requests:string[]=[];
  await page.route('**/v1/assessments',route=>{
    expect(route.request().headers().authorization).toBe('Bearer '+token);
    requests.push(route.request().postData()!);
    return route.fulfill({status:202,json:queued});
  });
  await page.route('**/v1/jobs/'+id,route=>route.fulfill({json:held}));
  await page.route('**/v1/jobs/'+id+'/hold-report',route=>route.fulfill({json:report}));
  await page.setViewportSize({width:1440,height:1000});
  await connect(page);await parents(page);
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).press('Enter');
  await expect(page.getByText('대기 중',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'평가 상태 확인',exact:true}).press('Enter');
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toBeVisible();
  await expect(page.getByText('같은 조건의 작물 대응 비교',{exact:true})).toBeVisible();
  expect(requests).toHaveLength(1);
  expect(JSON.parse(requests[0]!)).toEqual({run_job_id:thermal,economic_job_id:economic,
    idempotency_key:expect.stringMatching(/^web-assessment-v1:/)});
  await mkdir('../research/artifacts',{recursive:true});
  await page.screenshot({path:'../research/artifacts/calculation-assessment-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await expect(page.getByRole('heading',{name:'계산 평가와 보류 근거'})).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'../research/artifacts/calculation-assessment-phone.png',fullPage:true});
  expect(errors).toEqual([]);
});

test('lost response locks connection and inputs, keeps exactly one intent across navigation and retry',async({page})=>{
  const bodies:string[]=[];
  await page.route('**/v1/assessments',route=>{
    bodies.push(route.request().postData()!);
    return bodies.length===1?route.abort():route.fulfill({status:202,json:queued});
  });
  await connect(page);await parents(page);
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('같은 내용');
  await expect(page.getByLabel('완료 열 계산 작업 ID')).not.toBeEditable();
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeDisabled();
  await expect(page.getByRole('button',{name:'새 평가 입력'})).toBeDisabled();
  await expect(page.getByRole('button',{name:'저장 평가 조회'})).toBeDisabled();
  await page.getByRole('button',{name:'02 작업과 근거'}).click();
  await page.getByRole('button',{name:'06 계산 평가'}).click();
  await page.getByRole('button',{name:'같은 평가 요청 다시 확인'}).click();
  await expect(page.getByText('대기 중',{exact:true})).toBeVisible();
  expect(bodies).toHaveLength(2);expect(bodies[1]).toBe(bodies[0]);
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeEnabled();
});

test('bounded refusal permits a new intent while a positive response remains unconfirmed',async({page})=>{
  const bodies:string[]=[];
  await page.route('**/v1/assessments',route=>{
    bodies.push(route.request().postData()!);
    return bodies.length===1?route.fulfill({status:422,json:{private:'must not display'}})
      :route.fulfill({status:202,json:{...queued,state:'succeeded'}});
  });
  await connect(page);await parents(page);
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('같은 조건');
  await page.getByRole('button',{name:'새 평가 입력'}).click();
  await expect(page.getByLabel('완료 열 계산 작업 ID')).toBeEditable();
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('검증할 수 없어');
  await expect(page.getByRole('button',{name:'새 평가 입력'})).toBeDisabled();
  await expect(page.getByText('작업 완료',{exact:true})).toHaveCount(0);
  expect(JSON.parse(bodies[0]!).idempotency_key).not.toBe(JSON.parse(bodies[1]!).idempotency_key);
  expect(await page.locator('body').innerText()).not.toContain('must not display');
});

test('saved assessment reopens after reload using only GET and reconnect clears the previous account',async({page})=>{
  let posts=0;let foreign=false;
  await page.route('**/v1/assessments',route=>{posts++;return route.fulfill({status:202,json:queued});});
  await page.route('**/v1/jobs/'+id,route=>foreign
    ?route.fulfill({status:403,json:{private:'another account'}}):route.fulfill({json:held}));
  await page.route('**/v1/jobs/'+id+'/hold-report',route=>route.fulfill({json:report}));
  await connect(page);
  await page.getByLabel('저장 평가 작업 ID').fill(id);
  await page.getByRole('button',{name:'저장 평가 조회'}).click();
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toBeVisible();
  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'06 계산 평가'}).click();
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toHaveCount(0);
  await page.getByLabel('저장 평가 작업 ID').fill(id);
  await page.getByRole('button',{name:'저장 평가 조회'}).click();
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toBeVisible();
  foreign=true;
  await page.getByLabel('접근 토큰').fill('synthetic-another-account-token');
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'06 계산 평가'}).click();
  await expect(page.getByLabel('저장 평가 작업 ID')).toHaveValue('');
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toHaveCount(0);
  await page.getByLabel('저장 평가 작업 ID').fill(id);
  await page.getByRole('button',{name:'저장 평가 조회'}).click();
  await expect(page.getByRole('alert')).toContainText('권한');
  expect(posts).toBe(0);
});

test('read failure retries the known job without another POST or an admission uncertainty lock',async({page})=>{
  let posts=0;let reads=0;
  await page.route('**/v1/assessments',route=>{posts++;return route.fulfill({status:202,json:queued});});
  await page.route('**/v1/jobs/'+id,route=>++reads===1?route.abort():route.fulfill({json:held}));
  await page.route('**/v1/jobs/'+id+'/hold-report',route=>route.fulfill({json:report}));
  await connect(page);await parents(page);
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).click();
  await page.getByRole('button',{name:'평가 상태 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('응답을 받지 못했습니다');
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeEnabled();
  await expect(page.getByText('대기 중',{exact:true})).toHaveCount(0);
  await page.getByRole('button',{name:'평가 상태 확인',exact:true}).click();
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toBeVisible();
  expect(posts).toBe(1);expect(reads).toBe(2);
});

test('double click admits once and a wrong report stage never supplies assessment evidence',async({page})=>{
  let posts=0;let release:()=>void=()=>{};
  const wait=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/v1/assessments',async route=>{
    posts++;await wait;await route.fulfill({status:202,json:queued});
  });
  await page.route('**/v1/jobs/'+id,route=>route.fulfill({json:held}));
  await page.route('**/v1/jobs/'+id+'/hold-report',route=>route.fulfill({json:{...report,stage:'research'}}));
  await connect(page);await parents(page);
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).dblclick();
  await expect(page.getByRole('button',{name:'같은 평가 요청 다시 확인',exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'연결 해제'})).toBeDisabled();
  expect(posts).toBe(1);release();
  await expect(page.getByText('대기 중',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'평가 상태 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('검증할 수 없어');
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toHaveCount(0);
  expect(posts).toBe(1);
});
