import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';

const catalog=JSON.parse(readFileSync(new URL('./crop-result-catalog-recorded-responses.json',import.meta.url),'utf8'));
const crops=JSON.parse(readFileSync(new URL('./crop-farm-selection-recorded-responses.json',import.meta.url),'utf8'));
const growth=JSON.parse(catalog.bodies_raw_utf8.growth_max),tail=JSON.parse(catalog.bodies_raw_utf8.growth_tail);
const harvest=JSON.parse(catalog.bodies_raw_utf8.harvest),registration=JSON.parse(crops.bodies_raw_utf8.registered);
const records=[...growth.items,...tail.items],token='owned-synthetic-crop-catalog-browser-token';
const job={job_id:'11111111-1111-4111-8111-111111111111',stage:'collection',state:'queued',attempt_count:0,
  max_attempts:3,created_at:'2026-10-01T00:00:00Z',updated_at:'2026-10-01T00:00:00Z',reason_code:null};
const farm={scenario_id:growth.farm.scenario_id,scenario_revision:growth.farm.scenario_revision,
  scenario_sha256:growth.farm.registration_sha256,farm_sha256:'a'.repeat(64),numeric_input_sha256:'b'.repeat(64),
  rights_sha256:'c'.repeat(64),registration_status:'registered_unpublished_inputs',intent_job:job};
function deferred(){let release!:()=>void;const promise=new Promise<void>(r=>{release=r;});return {promise,release};}
async function mocked(page:Page,options:{emptyFarms?:boolean;emptyResults?:boolean}={}){
  const calls:{path:string;query:URLSearchParams;method:string}[]=[];
  let held:Promise<void>|null=null,entered:(()=>void)|null=null;
  await page.route('**/v1/**',async route=>{
    const url=new URL(route.request().url()),path=url.pathname;
    calls.push({path,query:url.searchParams,method:route.request().method()});
    expect(route.request().method()).toBe('GET');
    if(route.request().headers().authorization!=='Bearer '+token)return route.fulfill({status:403,json:{detail:'owned account denial'}});
    let value:unknown;
    if(path==='/v1/farm-authored-inputs/catalog')value={items:options.emptyFarms?[]:[farm],next_cursor:null};
    else if(path==='/v1/farm-authored-inputs')value=farm;
    else if(path==='/v1/crop-research-result-catalog/farm-crops')value=registration;
    else if(path==='/v1/crop-research-result-catalog'){
      if(held){entered?.();await held;}
      if(url.searchParams.get('kind')==='harvest_v1')value=harvest;
      else{
        const before=url.searchParams.get('before_result_id'),start=before?records.findIndex(row=>row.result_id===before)+1:0;
        const items=options.emptyResults?[]:records.slice(start,start+10),last=items.at(-1);
        value={...growth,items,next_cursor:!options.emptyResults&&start+10<records.length?
          {recorded_at:last.recorded_at,result_id:last.result_id}:null};
      }
    }else return route.fulfill({status:403,json:{detail:'owned current result denial'}}).catch(()=>{});
    await route.fulfill({json:value}).catch(()=>{});
  });
  return {calls,hold:(promise:Promise<void>,onEnter:()=>void)=>{held=promise;entered=onEnter;},release:()=>{held=null;entered=null;}};
}
async function connected(page:Page){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰',{exact:true}).fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:/08 성장 연구 3D/}).click();
  await page.getByRole('button',{name:'저장 결과 목록에서 선택',exact:true}).click();
}
async function selected(page:Page){
  const panel=page.locator('.crop-result-catalog');await panel.getByRole('button',{name:'농장 목록 조회',exact:true}).click();
  await panel.getByLabel('등록된 농장 판본',{exact:true}).selectOption(job.job_id);
  await expect(panel.getByLabel('등록된 작물과 재배 기간')).toBeEnabled();
  await panel.getByLabel('등록된 작물과 재배 기간').selectOption(growth.farm.crop_id);
  await expect(panel.locator('tbody tr')).toHaveCount(10);return panel;
}
const pageErrors=new WeakMap<Page,string[]>();
test.beforeEach(({page})=>{const errors:string[]=[];pageErrors.set(page,errors);page.on('pageerror',e=>errors.push(e.message));});
test.afterEach(({page})=>expect(pageErrors.get(page)).toEqual([]));
test('reads exact current farm and crop metadata and keyset pages without manual result IDs',async({page})=>{
  const api=await mocked(page);await connected(page);const panel=await selected(page);
  await expect(panel.getByText(/실시간 계산 미연동/)).toBeVisible();
  await expect(panel.locator('tbody tr').first()).toContainText(records[0].recorded_at.replace('T',' ').replace('Z',''));
  await panel.getByRole('button',{name:'결과 다음 페이지',exact:true}).click();
  await expect(panel.locator('tbody tr').first()).toContainText(records[10].recorded_at.replace('T',' ').replace('Z',''));
  const request=api.calls.filter(c=>c.path==='/v1/crop-research-result-catalog').at(-1)!;
  expect(request.query.get('before_result_id')).toBe(records[9].result_id);expect(request.query.get('limit')).toBe('10');
  await panel.getByRole('button',{name:'결과 이전 페이지',exact:true}).click();await expect(panel.locator('tbody tr')).toHaveCount(10);
});
test('opens the listed growth ID with its exact farm and clears numerical views on current denial',async({page})=>{
  const api=await mocked(page);await connected(page);const panel=await selected(page);
  await panel.getByRole('button',{name:/생장 결과 열기/}).first().click();
  await expect(panel.locator('.cycle-replay')).toHaveAttribute('data-window-phase','error');
  const request=api.calls.find(c=>c.path.startsWith('/v1/crop-cycle-calculation-research-results/'))!;
  expect(decodeURIComponent(request.path.split('/').at(-1)!)).toBe(records[0].result_id);
  for(const [key,value] of Object.entries(growth.farm))expect(request.query.get(key)).toBe(value);
  await expect(panel.locator('.coupled-viewer')).toHaveCount(0);
});
test('opens the harvest parent first and refuses harvest replay when that parent is denied',async({page})=>{
  const api=await mocked(page);await connected(page);const panel=await selected(page);
  await panel.getByRole('button',{name:'수확 배정',exact:true}).click();await expect(panel.locator('tbody tr')).toHaveCount(1);
  await panel.getByRole('button',{name:/수확 결과 열기/}).click();
  await expect(panel.locator('.cycle-replay')).toHaveAttribute('data-window-phase','error');
  const parent=api.calls.find(c=>c.path.startsWith('/v1/crop-cycle-calculation-research-results/'))!;
  expect(decodeURIComponent(parent.path.split('/').at(-1)!)).toBe(harvest.items[0].parent_result_id);
  expect(api.calls.some(c=>c.path.startsWith('/v1/crop-harvest-research-results/'))).toBe(false);
});
test('shows empty registered farms with the existing authoring route',async({page})=>{
  await mocked(page,{emptyFarms:true});await connected(page);const panel=page.locator('.crop-result-catalog');
  await panel.getByRole('button',{name:'농장 목록 조회',exact:true}).click();
  await expect(panel.getByText('이 페이지에 등록된 농장이 없습니다.')).toBeVisible();
  await panel.getByRole('button',{name:'작성 농장 화면 열기'}).click();
  await expect(page.getByRole('heading',{name:'작성 농장 실행',exact:true})).toBeVisible();
});
test('uses the approved empty illustration and leaves an empty result unselected',async({page})=>{
  await mocked(page,{emptyResults:true});await connected(page);const panel=page.locator('.crop-result-catalog');
  await panel.getByRole('button',{name:'농장 목록 조회',exact:true}).click();
  await panel.getByLabel('등록된 농장 판본',{exact:true}).selectOption(job.job_id);
  await expect(panel.getByLabel('등록된 작물과 재배 기간')).toBeEnabled();
  await panel.getByLabel('등록된 작물과 재배 기간').selectOption(growth.farm.crop_id);
  await expect(panel.getByRole('heading',{name:'저장된 연구 결과가 없습니다'})).toBeVisible();
  await expect(panel.locator('.catalog-empty img')).toHaveJSProperty('naturalWidth',570);
  await expect(panel.locator('.cycle-replay')).toHaveCount(0);await expect(panel.getByRole('button',{name:'결과 다음 페이지'})).toBeDisabled();
});
test('ignores a late list reply after the user cancels a refresh',async({page})=>{
  const api=await mocked(page);await connected(page);const panel=await selected(page),g=deferred(),entered=deferred();
  api.hold(g.promise,entered.release);await panel.getByRole('button',{name:'결과 목록 새로고침',exact:true}).click();await entered.promise;
  await panel.getByRole('button',{name:'조회 취소',exact:true}).click();api.release();g.release();
  await expect(panel).toHaveAttribute('data-picker-phase','idle');await expect(panel.locator('tbody tr')).toHaveCount(0);
});
test('clears catalogue and replay on reconnect while a previous list reply is pending',async({page})=>{
  const api=await mocked(page);await connected(page);const panel=await selected(page),g=deferred(),entered=deferred();
  api.hold(g.promise,entered.release);await panel.getByRole('button',{name:'결과 목록 새로고침',exact:true}).click();await entered.promise;
  await page.getByLabel('접근 토큰',{exact:true}).fill(token+'-other');await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  api.release();g.release();await expect(page.locator('.crop-result-catalog')).toHaveCount(0);
  await page.getByRole('button',{name:/08 성장 연구 3D/}).click();await expect(page.locator('.crop-result-catalog')).toHaveCount(0);
});
test('keeps keyboard controls and the table within a narrow app viewport',async({page})=>{
  await page.setViewportSize({width:390,height:844});await mocked(page);await connected(page);const panel=await selected(page);
  await panel.getByRole('region',{name:/저장 결과 표/}).focus();await expect(panel.getByRole('region',{name:/저장 결과 표/})).toBeFocused();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await panel.getByRole('button',{name:'결과 다음 페이지'}).focus();await page.keyboard.press('Enter');
  await expect(panel.locator('tbody tr').first()).toContainText(records[10].recorded_at.replace('T',' ').replace('Z',''));
});
