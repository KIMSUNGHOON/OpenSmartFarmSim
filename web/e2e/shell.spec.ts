import { test, expect } from '@playwright/test';

const jobId='11111111-1111-4111-8111-111111111111';
const token='synthetic-browser-test-token-only';
const queued={job_id:jobId,stage:'research',state:'queued',attempt_count:0,max_attempts:3,
  created_at:'2026-09-29T00:00:00Z',updated_at:'2026-09-29T00:00:00Z',reason_code:null};

test('keyboard admission, actual response state and bounded hold rendering',async ({page}) => {
  const errors:string[]=[]; page.on('pageerror',error=>errors.push(error.message));
  const requests:string[]=[];
  await page.route('**/v1/locations',async route=>{
    requests.push(route.request().postData() ?? '');
    expect(route.request().headers().authorization).toBe('Bearer '+token);
    await route.fulfill({status:202,json:{location_id:'location-v1-'+'a'.repeat(64),
      point:{latitude:37.5,longitude:127},spatial_support:'pending_research',research_job:queued}});
  });
  await page.route('**/v1/jobs/'+jobId,route=>route.fulfill({json:{...queued,state:'hold',
    attempt_count:1,reason_code:'ai_validated_hold'}}));
  await page.route('**/v1/jobs/'+jobId+'/hold-report',route=>route.fulfill({json:{
    job_id:jobId,stage:'research',hold_id:jobId,status:'hold',recorded_at:queued.updated_at,
    reason_code:'evidence_missing',missing_evidence:['research_source_evidence','signed_decision_context'],
    missing_evidence_count:2}}));
  await page.goto('/');
  await expect(page.getByRole('heading',{name:'시뮬레이션 입력 설정'})).toBeVisible();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).press('Enter');
  await page.getByRole('button',{name:'합성 예시 채우기'}).press('Enter');
  await page.getByRole('button',{name:'자료 조사 요청'}).press('Enter');
  await expect(page.locator('#viewport-1-b-progress').getByText('대기 중',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'현재 상태 확인'}).press('Enter');
  await expect(page.getByRole('heading',{name:'판단 보류',exact:true})).toBeVisible();
  await expect(page.getByText('결정 시각을 확인할 서명 근거')).toBeVisible();
  expect(requests).toHaveLength(1);
  expect(JSON.parse(requests[0] ?? '{}').idempotency_key).toMatch(/^web-location-v1:/);
  expect(errors).toEqual([]);
});

test('lost admission reply retains exactly the same intent and never displays invented completion',async ({page}) => {
  const bodies:string[]=[];
  await page.route('**/v1/locations',async route=>{
    bodies.push(route.request().postData() ?? '');
    if (bodies.length===1) { await route.abort();return; }
    await route.fulfill({status:202,json:{location_id:'location-v1-'+'a'.repeat(64),
      point:{latitude:37.5,longitude:127},spatial_support:'pending_research',research_job:queued}});
  });
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'합성 예시 채우기'}).click();
  await page.getByRole('button',{name:'자료 조사 요청'}).click();
  await expect(page.getByRole('alert')).toContainText('같은 요청');
  await expect(page.getByLabel('위도 (°N)')).not.toBeEditable();
  await expect(page.getByRole('button',{name:'새 입력'})).toBeDisabled();
  await page.getByRole('button',{name:'같은 요청 다시 확인'}).click();
  await expect(page.locator('#viewport-1-b-progress').getByText('대기 중',{exact:true})).toBeVisible();
  expect(bodies).toHaveLength(2); expect(bodies[1]).toBe(bodies[0]);
});

test('completed research advances through owned collection and review with stable retry keys',async ({page}) => {
  const collectionId='22222222-2222-4222-8222-222222222222';
  const reviewId='33333333-3333-4333-8333-333333333333';
  const bodies:string[]=[];
  await page.route('**/v1/locations',route=>route.fulfill({status:202,json:{
    location_id:'location-v1-'+'a'.repeat(64),point:{latitude:37.5,longitude:127},
    spatial_support:'pending_research',research_job:queued}}));
  await page.route('**/v1/jobs/'+jobId,route=>route.fulfill({json:{...queued,state:'succeeded'}}));
  await page.route('**/v1/ingestions',async route=>{
    bodies.push(route.request().postData() ?? '');
    if(bodies.length===1){await route.abort();return;}
    await route.fulfill({status:202,json:{...queued,job_id:collectionId,stage:'collection'}});
  });
  await page.route('**/v1/jobs/'+collectionId,route=>route.fulfill({json:{...queued,
    job_id:collectionId,stage:'collection',state:'succeeded'}}));
  await page.route('**/v1/collection-reviews',route=>route.fulfill({status:202,json:{...queued,
    job_id:reviewId,stage:'collection_review'}}));
  await page.route('**/v1/jobs/'+reviewId,route=>route.fulfill({json:{...queued,
    job_id:reviewId,stage:'collection_review',state:'hold'}}));
  await page.route('**/v1/jobs/'+reviewId+'/hold-report',route=>route.fulfill({json:{
    job_id:reviewId,stage:'collection_review',hold_id:reviewId,status:'hold',
    recorded_at:queued.updated_at,reason_code:'evidence_missing',
    missing_evidence:['real_source_g0'],missing_evidence_count:1}}));
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'합성 예시 채우기'}).click();
  await page.getByRole('button',{name:'자료 조사 요청'}).click();
  await page.getByRole('button',{name:'현재 상태 확인'}).click();
  await page.getByRole('button',{name:'원본 수집 요청'}).click();
  await expect(page.getByRole('alert')).toContainText('같은 버튼');
  await page.getByRole('button',{name:'같은 수집 요청 다시 확인'}).click();
  expect(bodies).toHaveLength(2);
  expect(bodies[1]).toBe(bodies[0]);
  expect(JSON.parse(bodies[1] ?? '{}')).toMatchObject({research_job_id:jobId});
  await page.getByRole('button',{name:'03 경제 가정·계산'}).click();
  await page.getByRole('button',{name:'02 작업과 근거'}).click();
  await page.getByRole('button',{name:'수집 상태 확인'}).click();
  await page.getByRole('button',{name:'수집 입력 검토 요청'}).click();
  await page.getByRole('button',{name:'검토 상태 확인'}).click();
  await expect(page.getByText('실제 원천의 권리와 품질')).toBeVisible();
  await expect(page.getByText('수집·검토 작업 완료는 실제 자료 G0 승인')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('saved source jobs return after reload and revoked authority blocks a new stage',async ({page}) => {
  const collectionId='22222222-2222-4222-8222-222222222222';
  const reviewId='33333333-3333-4333-8333-333333333333';
  const summary={job:{...queued,state:'succeeded'},point:{latitude:37.5,longitude:127},
    period_start_utc:'2026-10-15T08:00:00Z',period_end_utc:'2026-10-15T10:00:00Z',
    goal_id:'historical-thermal-replay',current_authority:'available'};
  const collection={...queued,job_id:collectionId,stage:'collection',state:'succeeded'};
  const review={...queued,job_id:reviewId,stage:'collection_review',state:'hold'};
  await page.route('**/v1/source-history',route=>route.fulfill({json:{items:[summary],next_cursor:null}}));
  await page.route('**/v1/source-history/'+jobId,route=>route.fulfill({json:{
    research:summary,collection,review}}));
  await page.route('**/v1/jobs/'+reviewId+'/hold-report',route=>route.fulfill({json:{
    job_id:reviewId,stage:'collection_review',hold_id:reviewId,status:'hold',
    recorded_at:queued.updated_at,reason_code:'evidence_missing',
    missing_evidence:['real_source_g0'],missing_evidence_count:1}}));
  await page.route('**/v1/jobs/'+reviewId,route=>route.fulfill({json:review}));
  await page.setViewportSize({width:390,height:844});
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'02 작업과 근거'}).click();
  await page.getByRole('button',{name:'저장된 조사 보기'}).click();
  await page.getByRole('button',{name:/37\.5° N · 127° E/}).click();
  await expect(page.getByText('작업 '+collectionId)).toBeVisible();
  await expect(page.getByText('작업 '+reviewId)).toBeVisible();
  await page.getByRole('button',{name:'검토 상태 확인'}).click();
  await expect(page.getByText('실제 원천의 권리와 품질')).toBeVisible();
  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'02 작업과 근거'}).click();
  await page.getByRole('button',{name:'저장된 조사 보기'}).click();
  await page.getByRole('button',{name:/37\.5° N · 127° E/}).click();
  await expect(page.getByText('작업 '+reviewId)).toBeVisible();
  summary.current_authority='hold';
  await page.getByRole('button',{name:'저장된 조사 보기'}).click();
  await page.getByRole('button',{name:/37\.5° N · 127° E/}).click();
  await expect(page.getByText('새 수집·검토 접수는 보류합니다.')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('input and work screens remain usable at 320px and with every text size doubled',async ({page}) => {
  for (const width of [320,768,1440]) {
    await page.setViewportSize({width,height:900});
    await page.goto('/');
    await page.evaluate(()=>document.fonts.ready);
    for (const doubled of [false,true]) {
      if (doubled) {
        const original=await page.getByRole('heading',{level:1}).evaluate(e=>parseFloat(getComputedStyle(e).fontSize));
        await page.addStyleTag({content:':root{font-size:32px}'});
        expect(await page.getByRole('heading',{level:1}).evaluate(e=>parseFloat(getComputedStyle(e).fontSize)))
          .toBe(original*2);
      }
      const fits=()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth);
      expect(await fits()).toBe(true);
      await page.getByRole('button',{name:'합성 예시 채우기'}).press('Enter');
      await expect(page.getByLabel('위도 (°N)')).toHaveValue('37.5');
      await expect(page.getByLabel('시작 날짜 (UTC)')).toHaveValue('2026-10-15');
      await expect(page.getByLabel('시작 시각 (UTC)')).toHaveValue('08:00');
      await page.getByRole('button',{name:'02 작업과 근거'}).press('Enter');
      await expect(page.getByRole('heading',{name:'서버 작업 기록'})).toBeVisible();
      expect(await fits()).toBe(true);
      await page.getByRole('button',{name:'01 입력 설정'}).press('Enter');
    }
  }
});
