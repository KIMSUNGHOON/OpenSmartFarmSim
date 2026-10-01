import { test,expect } from '@playwright/test';
import { source,candidate,research,selected,sourcePath,sourceToken,routeSourceFixture,
  openComposer,chooseSource,chooseEconomics,fillExplicitFarm } from './source-farm-fixture';

test('exact saved source and economic pin reach registration with an identical uncertain retry',async({page},testInfo)=>{
  const calls:string[]=[];await routeSourceFixture(page);
  await page.route('**/v1/farm-authored-inputs',async route=>{
    expect(route.request().headers().authorization).toBe('Bearer '+sourceToken);
    calls.push(route.request().postData()??'');
    if(calls.length===1)return route.abort('failed');
    return route.fulfill({status:200,json:{scenario_id:'farm-browser',scenario_revision:'r1',scenario_sha256:'a'.repeat(64),
      farm_sha256:'b'.repeat(64),numeric_input_sha256:'c'.repeat(64),rights_sha256:'d'.repeat(64),
      registration_status:'registered_unpublished_inputs',intent_job:{...research.job,stage:'collection',
        job_id:'55555555-5555-4555-8555-555555555555',state:'queued',attempt_count:0}}});
  });
  await openComposer(page);
  await page.getByRole('button',{name:'02 작업과 근거',exact:true}).click();
  await page.getByRole('button',{name:'저장된 조사 보기',exact:true}).click();
  await page.getByRole('button',{name:/35° N · 127° E/}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행',exact:true}).click();
  await chooseSource(page);await chooseEconomics(page);
  await expect(page.getByRole('region',{name:'선택한 원천 참조'})).toContainText('G0/G1 미수용');
  await expect(page.locator('input[name="decision_at"]')).toHaveValue(source.decision_at_utc);
  await expect(page.locator('input[name="decision_at"]')).toHaveAttribute('readonly','');
  await expect(page.locator('input[name="floor_area"]')).toHaveValue('');
  await expect(page.locator('.authored-rights input')).not.toBeChecked();
  await fillExplicitFarm(page);await page.locator('.authored-rights input').check();
  await page.getByRole('button',{name:'입력 내용 검토',exact:true}).click();
  await page.getByRole('button',{name:'불변 입력 판본 등록',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('같은 입력과 판본');
  for(const name of ['원천 다시 선택','경제 판본 다시 선택','참조 직접 입력','저장된 판본 찾기',
    '연결 설정','연결 해제'])
    await expect(page.getByRole('button',{name,exact:true})).toBeDisabled();
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();
  await expect(page.getByRole('button',{name:'자료 조사 요청',exact:true})).toBeDisabled();
  await expect(page.getByRole('button',{name:'새 입력',exact:true})).toBeDisabled();
  await expect(page.getByRole('status').filter({hasText:'농장 입력의 등록 접수'})).toBeVisible();
  await page.getByRole('button',{name:'02 작업과 근거',exact:true}).click();
  for(const name of ['현재 상태 확인','저장된 조사 보기','수집 상태 확인','검토 상태 확인','저장된 시도 보기'])
    await expect(page.getByRole('button',{name,exact:true})).toBeDisabled();
  await expect(page.getByLabel('접근 토큰')).toHaveValue('');
  await page.evaluate(()=>window.scrollTo(0,0));
  await page.screenshot({path:testInfo.outputPath('source-farm-registration-lock.png')});
  await page.getByRole('button',{name:'04 작성 농장 실행',exact:true}).click();
  await page.getByRole('button',{name:'같은 입력으로 등록 재확인',exact:true}).click();
  await expect(page.getByText('입력 등록됨 · 계산 전', {exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'연결 설정',exact:true})).toBeEnabled();
  expect(calls).toHaveLength(2);expect(calls[0]).toBe(calls[1]);
  const body=JSON.parse(calls[1]!);
  expect(body.farm.research_job_id).toBe(source.research_job_id);
  expect(body.farm.decision_at).toBe(source.decision_at_utc);
  expect(body.farm.economic).toEqual(candidate.economic);
  expect(body.farm.facility.floor_area.value).toBe('100');expect(body.farm.crops).toEqual([]);
  expect(body.rights.redistribute).toBe(false);
  const storage=await page.evaluate(()=>({...sessionStorage,...localStorage}));
  expect(JSON.stringify(storage)).not.toContain(sourceToken);
  expect(JSON.stringify(storage)).not.toContain('1000000');
});

test('invalid farm registration acknowledgement stays pinned until a bounded refusal',async({page})=>{
  const calls:string[]=[];await routeSourceFixture(page);
  await page.route('**/v1/farm-authored-inputs',route=>{
    calls.push(route.request().postData()??'');
    return calls.length===1?route.fulfill({status:200,json:{unexpected:'not-an-acknowledgement'}}):
      route.fulfill({status:422,json:{code:'invalid_request'}});
  });
  await openComposer(page);await chooseSource(page);await chooseEconomics(page);
  await fillExplicitFarm(page);await page.locator('.authored-rights input').check();
  await page.getByRole('button',{name:'입력 내용 검토',exact:true}).click();
  await page.getByRole('button',{name:'불변 입력 판본 등록',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('같은 입력과 판본');
  await expect(page.getByRole('button',{name:'연결 설정',exact:true})).toBeDisabled();
  await expect(page.locator('input[name="scenario_id"]')).toBeDisabled();
  await page.getByRole('button',{name:'같은 입력으로 등록 재확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('서버가 입력·현재 출처·권리를 확인하지 못했습니다');
  await expect(page.getByRole('button',{name:'연결 설정',exact:true})).toBeEnabled();
  await expect(page.locator('input[name="scenario_id"]')).toBeEditable();
  await expect(page.getByRole('button',{name:'입력 내용 검토',exact:true})).toBeEnabled();
  await expect(page.getByRole('region',{name:'제출 전 확인'})).toHaveCount(0);
  expect(calls).toHaveLength(2);expect(calls[0]).toBe(calls[1]);
});

test('changing a source or economic choice removes preview and rights but preserves explicit physical inputs',async({page})=>{
  await routeSourceFixture(page);await openComposer(page);await chooseSource(page);await chooseEconomics(page);
  await fillExplicitFarm(page);await page.locator('.authored-rights input').check();
  await page.getByRole('button',{name:'입력 내용 검토',exact:true}).click();
  await expect(page.getByRole('region',{name:'제출 전 확인'})).toBeVisible();
  await page.getByRole('button',{name:'경제 판본 다시 선택',exact:true}).click();
  await expect(page.getByRole('region',{name:'제출 전 확인'})).toHaveCount(0);
  await expect(page.locator('input[name="economic_candidate_id"]')).toHaveCount(0);
  await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();
  await expect(page.locator('.authored-rights input')).not.toBeChecked();
  await expect(page.locator('input[name="floor_area"]')).toHaveValue('100');
  await page.locator('.authored-rights input').check();
  await page.getByRole('button',{name:'원천 다시 선택',exact:true}).click();
  await expect(page.locator('input[name="decision_at"]')).toHaveCount(0);
  await page.getByRole('button',{name:/좌표 35, 127/}).click();
  await page.getByRole('button',{name:/원본 수집 · 작업 완료/}).click();await chooseEconomics(page);
  await expect(page.locator('.authored-rights input')).not.toBeChecked();
  await expect(page.locator('input[name="floor_area"]')).toHaveValue('100');
});

test('empty history, absent economics and held current selection remain separate from approval',async({page})=>{
  await routeSourceFixture(page);
  await page.route('**/v1/source-history',route=>route.fulfill({status:200,json:{items:[],next_cursor:null}}));
  await openComposer(page);await page.getByRole('button',{name:'저장 조사 조회',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('저장된 조사 기록이 없습니다');
  await page.unroute('**/v1/source-history');await chooseSource(page);
  await page.route('**/economic-candidates?*',route=>route.fulfill({status:200,json:{verification:'requires_current_selection',
    source,items:[],next_cursor:null}}));
  await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
  await expect(page.getByRole('status')).toContainText('저장 경제 판본이 없습니다');
  await expect(page.locator('input[name="floor_area"]')).toHaveCount(0);
  await page.unroute('**/economic-candidates?*');
  await page.getByRole('button',{name:'경제 목록 새로고침',exact:true}).click();
  await page.route('**/economic-candidates/'+candidate.economic.candidate_id,
    route=>route.fulfill({status:422,json:{code:'selection_held'}}));
  await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('선택을 보류');
  await expect(page.locator('input[name="economic_candidate_id"]')).toHaveCount(0);
});

test('foreign current economics and revoked source references cannot populate the form',async({page})=>{
  await routeSourceFixture(page);await openComposer(page);await chooseSource(page);
  await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
  await page.route('**/economic-candidates/'+candidate.economic.candidate_id,route=>route.fulfill({status:200,
    json:{...selected,source:{...source,context_sha256:'b'.repeat(64)}}}));
  await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('응답 연결을 검증하지 못했습니다');
  await page.getByRole('button',{name:'원천 다시 선택',exact:true}).click();
  await page.route('**'+sourcePath+'/farm-input-references',route=>route.fulfill({status:403,json:{code:'access_denied'}}));
  await page.getByRole('button',{name:/원본 수집 · 작업 완료/}).click();
  await expect(page.getByRole('alert')).toContainText('권한이 없습니다');
  await expect(page.locator('input[name="snapshot_id"]')).toHaveCount(0);
});

test('economic pagination preserves the exact microsecond cursor and checks the chosen older version',async({page})=>{
  await routeSourceFixture(page);await openComposer(page);await chooseSource(page);
  const items=Array.from({length:21},(_,index)=>({...candidate,economic:{...candidate.economic,revision:'r'+(21-index),
    candidate_id:index.toString(16).padStart(64,'0')},recorded_at:'2026-10-01T00:00:00.'+(123456-index).toString()+'Z'}));
  let pages=0;
  await page.route('**/economic-candidates?*',async route=>{
    const params=new URL(route.request().url()).searchParams;expect(params.get('limit')).toBe('20');pages++;
    if(pages===1)return route.fulfill({status:200,json:{verification:'requires_current_selection',source,
      items:items.slice(0,20),next_cursor:{recorded_at:items[19]!.recorded_at,candidate_id:items[19]!.economic.candidate_id}}});
    expect(params.get('before_recorded_at')).toBe('2026-10-01T00:00:00.123437Z');
    expect(params.get('before_candidate_id')).toBe(items[19]!.economic.candidate_id);
    return route.fulfill({status:200,json:{verification:'requires_current_selection',source,items:[items[20]],next_cursor:null}});
  });
  await page.route('**/economic-candidates/'+items[20]!.economic.candidate_id,route=>route.fulfill({status:200,
    json:{...items[20],source,verification:'requires_registration_recheck'}}));
  await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
  await page.getByRole('button',{name:'이전 경제 판본 더 보기',exact:true}).click();
  await expect(page.locator('.source-farm-economic-list>li')).toHaveCount(21);
  await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();
  await expect(page.locator('input[name="economic_candidate_id"]')).toHaveValue(items[20]!.economic.candidate_id);
  expect(pages).toBe(2);
});

test('late old-account response is discarded and reconnect requires a fresh server selection',async({page})=>{
  await routeSourceFixture(page);await openComposer(page);await chooseSource(page);
  await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
  let release:()=>void=()=>{};const gate=new Promise<void>(resolve=>{release=resolve;});
  let entered:()=>void=()=>{};const ready=new Promise<void>(resolve=>{entered=resolve;});
  await page.route('**/economic-candidates/'+candidate.economic.candidate_id,async route=>{
    entered();await gate;await route.fulfill({status:200,json:selected});
  });
  try {
    await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();await ready;
    await page.getByLabel('접근 토큰').fill('synthetic-second-account-token');
    await page.getByRole('button',{name:'연결 설정',exact:true}).click();
    await page.getByRole('button',{name:'04 작성 농장 실행',exact:true}).click();
    await page.getByRole('button',{name:'새 입력 판본 작성',exact:true}).click();
  } finally {release();}
  await expect(page.getByRole('button',{name:'저장 조사 조회',exact:true})).toBeEnabled();
  await expect(page.getByRole('region',{name:'작성에 연결된 경제 판본'})).toHaveCount(0);
  await expect(page.locator('input[name="research_job_id"]')).toHaveCount(0);
  await chooseSource(page);await chooseEconomics(page);
  await expect(page.locator('input[name="research_job_id"]')).toHaveValue(source.research_job_id);
});

test('source and economics are keyboard reachable without overflow at supported widths',async({page},testInfo)=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await routeSourceFixture(page);await openComposer(page);
  const load=page.getByRole('button',{name:'저장 조사 조회',exact:true});await load.focus();await page.keyboard.press('Enter');
  const researchButton=page.getByRole('button',{name:/좌표 35, 127/});await researchButton.focus();await page.keyboard.press('Enter');
  const collectionButton=page.getByRole('button',{name:/원본 수집 · 작업 완료/});await collectionButton.focus();
  await expect(collectionButton).toBeFocused();
  for(const width of [320,768,1024,1440]) {
    await page.setViewportSize({width,height:1000});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await page.screenshot({path:testInfo.outputPath('source-farm-source-desktop.png'),fullPage:true});
  await page.keyboard.press('Enter');await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
  await page.screenshot({path:testInfo.outputPath('source-farm-economic-desktop.png'),fullPage:true});
  await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();
  const sourceDetails=page.getByText('조사·수집 식별자 상세',{exact:true});
  await sourceDetails.focus();await page.keyboard.press('Enter');
  await expect(page.getByRole('region',{name:'선택한 원천 참조'}).getByText(source.research_job_id,{exact:true})).toBeVisible();
  await sourceDetails.focus();await page.keyboard.press('Enter');
  const referenceDetails=page.getByText('원천·경제 참조 상세 · 읽기 전용',{exact:true});
  await referenceDetails.focus();await page.keyboard.press('Enter');
  await expect(page.locator('input[name="decision_at"]')).toBeVisible();
  await expect(page.locator('input[name="decision_at"]')).toHaveValue(source.decision_at_utc);
  await expect(page.locator('input[name="decision_at"]')).toHaveAttribute('readonly','');
  await referenceDetails.focus();await page.keyboard.press('Enter');
  await expect(page.locator('input[name="scenario_id"]')).toBeVisible();
  for(const [link,section] of [
    ['01 기준 판본','01 기준 판본과 공통 가정'],['02 시설·제어','02 온실 시설과 열 제어'],
    ['03 구간·재배','03 원본 구간과 재배 의도'],['04 목표·권리','04 목표와 사용 권리'],
  ]) {
    await page.getByRole('navigation',{name:'입력 구역',exact:true}).getByRole('link',{name:link,exact:true}).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByText(section!,{exact:true})).toBeFocused();
  }
  for(const width of [320,768,1024,1440]) {
    await page.setViewportSize({width,height:1000});
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await page.screenshot({path:testInfo.outputPath('source-farm-form-desktop.png'),fullPage:true});
  expect(errors).toEqual([]);
});
