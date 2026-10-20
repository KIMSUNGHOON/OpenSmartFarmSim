import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {revealConnection,revealConnectedControls} from './connection-fixture';
import {STORES} from '../src/cropReplay';

const fixture=JSON.parse(readFileSync(new URL('./organ-catalog-recorded-responses.json',import.meta.url),'utf8'));
const metadata=JSON.parse(fixture.bodies_raw_utf8.organ);
const replay=fixture.replay_value,token='owned-synthetic-organ-browser-token-only';
// Authored-farm envelopes are software fixtures; recorded organ/crop metadata is unchanged.
const farm={scenario_id:metadata.farm.scenario_id,scenario_revision:metadata.farm.scenario_revision,
  scenario_sha256:metadata.farm.registration_sha256,farm_sha256:replay.farm_sha256,
  numeric_input_sha256:'b'.repeat(64),rights_sha256:'c'.repeat(64),registration_status:'registered_unpublished_inputs',
  intent_job:{job_id:'11111111-1111-4111-8111-111111111111',stage:'collection',state:'queued',attempt_count:0,
    max_attempts:3,created_at:'2026-10-01T00:00:00Z',updated_at:'2026-10-01T00:00:00Z',reason_code:null}};
function gate(){let release!:()=>void;const promise=new Promise<void>(r=>{release=r;});return {promise,release};}
async function mocked(page:Page,held?:ReturnType<typeof gate>){
  const entered=gate(),settled=gate(),calls:{path:string;kind:string|null}[]=[];let denied=false;
  await page.route('**/v1/**',async route=>{
    const url=new URL(route.request().url()),path=url.pathname;calls.push({path,kind:url.searchParams.get('kind')});
    expect(route.request().method()).toBe('GET');
    if(route.request().headers().authorization!=='Bearer '+token)
      return route.fulfill({status:403,body:fixture.bodies_raw_utf8.scope_denied,contentType:'application/json'});
    if(path==='/v1/farm-authored-inputs/catalog')return route.fulfill({json:{items:[farm],next_cursor:null}});
    if(path==='/v1/farm-authored-inputs')return route.fulfill({json:farm});
    if(path==='/v1/crop-research-result-catalog/farm-crops')return route.fulfill({body:fixture.bodies_raw_utf8.farm_crops,contentType:'application/json'});
    if(path==='/v1/crop-research-result-catalog'){
      if(url.searchParams.get('kind')==='organ_v1')return route.fulfill({body:fixture.bodies_raw_utf8.organ,contentType:'application/json'});
      return route.fulfill({json:{...metadata,kind:url.searchParams.get('kind'),items:[],next_cursor:null}});
    }
    expect(path.startsWith('/v1/crop-research-results/')).toBe(true);
    expect(decodeURIComponent(path.split('/').at(-1)!)).toBe(replay.result_id);
    expect(Object.fromEntries(url.searchParams)).toEqual(replay.farm);
    entered.release();if(held)await held.promise;
    try{
      if(denied)await route.fulfill({status:422,body:fixture.bodies_raw_utf8.withdrawn,contentType:'application/json'});
      else await route.fulfill({json:replay});
    }catch{}finally{settled.release();}
  });
  return {calls,entered:entered.promise,settled:settled.promise,deny:()=>{denied=true;}};
}
async function selected(page:Page){
  await page.goto('/');await revealConnection(page);await page.getByLabel('접근 토큰',{exact:true}).fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await revealConnectedControls(page);
  await page.getByRole('button',{name:/08 성장 연구 3D/}).click();
  await page.getByRole('button',{name:'저장 결과 목록에서 선택',exact:true}).click();
  const panel=page.locator('.crop-result-catalog');
  await panel.getByRole('button',{name:'이전 생장 연구',exact:true}).click();
  await panel.getByRole('button',{name:'농장 목록 조회',exact:true}).click();
  await panel.getByLabel('등록된 농장 판본',{exact:true}).selectOption(farm.intent_job.job_id);
  await expect(panel.getByLabel('등록된 작물과 재배 기간')).toBeEnabled();
  await panel.getByLabel('등록된 작물과 재배 기간').selectOption(metadata.farm.crop_id);
  await expect(panel.locator('.catalog-results tbody tr')).toHaveCount(1);return panel;
}
async function open(page:Page){
  const panel=await selected(page);await panel.getByRole('button',{name:/생장 결과 열기/}).focus();
  await page.keyboard.press('Enter');await expect(panel.locator('.crop-viewer')).toBeVisible();return panel;
}
async function sameSample(page:Page,index:number){
  const row=replay.samples[index];
  for(const selector of ['.crop-viewer','.crop-readout','.crop-chart','.crop-scene'])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',row.at);
  const canvas=page.locator('.crop-canvas');await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  for(const store of STORES){
    const value=String(row.state[store].value);
    await expect(canvas).toHaveAttribute('data-carbon-'+store.replace('_','-'),value);
    await expect(page.locator('.crop-readout [data-metric="'+store+'"]')).toHaveAttribute('data-raw-value',value);
    await expect(page.locator('.crop-table tr[aria-selected=true] [data-metric="'+store+'"]')).toHaveAttribute('data-raw-value',value);
  }
  await expect(page.locator('.crop-readout [data-metric=lai]')).toHaveAttribute('data-raw-value',String(row.lai.value));
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
}
test.beforeEach(({page})=>{page.on('pageerror',error=>{throw error;});});
test('opens original organ metadata into its own six saved WebGL frames without calculation-cycle or harvest reads',async({page})=>{
  const api=await mocked(page),panel=await open(page);
  await expect(panel.locator('.crop-viewer')).toHaveAttribute('data-result-id',replay.result_id);
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();
  for(let i=0;i<replay.samples.length;i++){if(i)await slider.press('ArrowRight');await sameSample(page,i);}
  expect(await page.locator('.crop-canvas').evaluate(e=>{const gl=(e as HTMLCanvasElement).getContext('webgl2');return !!gl&&!gl.isContextLost();})).toBe(true);
  expect(api.calls.filter(c=>c.path.startsWith('/v1/crop-research-results/'))).toHaveLength(1);
  expect(api.calls.some(c=>c.path.includes('cycle-calculation')||c.path.includes('harvest-research'))).toBe(false);
  await expect(panel.getByText('합성 계산 · 품종 미검증',{exact:true})).toBeVisible();
});
test('clears the original numerical scene and table when the current lookup is denied',async({page})=>{
  const api=await mocked(page),panel=await open(page);await sameSample(page,0);api.deny();
  await panel.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(panel.locator('.crop-viewer')).toHaveCount(0);await expect(panel.locator('.crop-table')).toHaveCount(0);
  await expect(panel.getByRole('alert')).toBeVisible();
});
test('changing result kind removes organ replay and does not automatically reopen an old selection',async({page})=>{
  await mocked(page);const panel=await open(page);
  await panel.getByRole('button',{name:'수확 배정',exact:true}).click();
  await expect(panel.locator('.crop-viewer')).toHaveCount(0);
  await expect(panel.getByRole('heading',{name:'저장된 연구 결과가 없습니다'})).toBeVisible();
  await panel.getByRole('button',{name:'이전 생장 연구',exact:true}).click();
  await expect(panel.locator('.catalog-results tbody tr')).toHaveCount(1);
  await expect(panel.locator('.crop-viewer')).toHaveCount(0);
});
test('a late numerical reply after kind change never restores the previous organ scene',async({page})=>{
  const held=gate(),api=await mocked(page,held),panel=await selected(page);
  await panel.getByRole('button',{name:/생장 결과 열기/}).click();await api.entered;
  await panel.getByRole('button',{name:'수확 배정',exact:true}).click();held.release();await api.settled;
  await expect(panel.locator('.crop-viewer')).toHaveCount(0);
  await expect(panel.getByRole('heading',{name:'저장된 연구 결과가 없습니다'})).toBeVisible();
});
test('a late reply from the old account cannot restore organ data after reconnect',async({page})=>{
  const held=gate(),api=await mocked(page,held),panel=await selected(page);
  await panel.getByRole('button',{name:/생장 결과 열기/}).click();await api.entered;
  await revealConnection(page);await page.getByLabel('접근 토큰',{exact:true}).fill(token+'-other');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();held.release();await api.settled;
  await expect(page.locator('.crop-result-catalog')).toHaveCount(0);await expect(page.locator('.crop-viewer')).toHaveCount(0);
});
test('keeps organ selection and saved-frame keyboard controls usable at 390px',async({page})=>{
  await page.setViewportSize({width:390,height:844});await mocked(page);await open(page);
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('End');
  await sameSample(page,replay.samples.length-1);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
