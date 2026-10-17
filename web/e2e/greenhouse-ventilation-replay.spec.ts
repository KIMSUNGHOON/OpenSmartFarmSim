import {revealConnectedControls} from './connection-fixture';
import { test,expect,type Page,type Route } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { need,object } from '../src/api-validation';
import { decodeGreenhouseVentilationResponse,validGreenhouseVentilationLookup,type GreenhouseVentilationLookup,type GreenhouseVentilationResponse } from '../src/greenhouseVentilationReplay';
import { jointSceneScales } from '../src/jointCropClimateGeometry';
import { temperaturePosition } from '../src/coupledCropGeometry';
const fixture=JSON.parse(readFileSync(new URL('./greenhouse-ventilation-recorded-responses.json',import.meta.url),'utf8'));
function dataset(name:'completed'|'hold'){
  const rows:GreenhouseVentilationResponse[]=fixture[name].map((raw:unknown)=>{need(object(raw)&&object(raw.farm));
    const {scenario_id,scenario_revision,registration_sha256,crop_id}=raw.farm;
    const lookup={result_id:raw.result_id,scenario_id,scenario_revision,registration_sha256,crop_id};need(validGreenhouseVentilationLookup(lookup));
    return decodeGreenhouseVentilationResponse(raw,lookup);});
  const summary=rows[0];need(summary&&summary.summary!==null);const s=rows[1],e=rows[2];need(s?.page?.kind==='samples'&&e?.page?.kind==='events');
  const {scenario_id,scenario_revision,registration_sha256,crop_id}=summary.farm;
  return {summary,samples:s.page.records,events:e.page.records,rows,lookup:{result_id:summary.result_id,scenario_id,scenario_revision,registration_sha256,crop_id} satisfies GreenhouseVentilationLookup};
}
const base=dataset('completed'),held=dataset('hold'),pattern='**/v1/crop-greenhouse-ventilation-research-results/**';
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
test.setTimeout(30_000);
test.afterEach(async({page})=>{const session=await page.context().newCDPSession(page);
  try{await session.send('HeapProfiler.collectGarbage');await session.send('HeapProfiler.collectGarbage');}finally{await session.detach();}});
async function designSnapshot(page:Page,name:string){
  const root=process.env.OSSF_JOINT_VIEW_EVIDENCE;if(!root)return;
  const canvas=page.locator('.coupled-canvas'),picture=await canvas.count()?(await canvas.screenshot()).toString('base64'):null;
  const html=await page.evaluate(picture=>{
    const clone=document.documentElement.cloneNode(true) as HTMLElement;
    clone.querySelectorAll('script,.connection').forEach(element=>element.remove());
    clone.querySelectorAll<HTMLLinkElement>('link[href]').forEach(link=>{
      const url=new URL(link.href);if(url.origin===location.origin)link.setAttribute('href',url.pathname+url.search+url.hash);});
    const originals=document.querySelectorAll('select');clone.querySelectorAll('select').forEach((select,i)=>{
      select.querySelectorAll('option').forEach(option=>{if(option.value===originals[i]!.value)option.setAttribute('selected','');else option.removeAttribute('selected');});});
    if(picture)clone.querySelectorAll('canvas').forEach(canvas=>{const image=document.createElement('img');
      for(const attribute of canvas.attributes)image.setAttribute(attribute.name,attribute.value);
      image.src='data:image/png;base64,'+picture;canvas.replaceWith(image);});
    return '<!doctype html>'+clone.outerHTML;
  },picture);
  await writeFile(join(root,name+'.html'),html);
}
async function connect(page:Page){
  await page.goto('/');const connection=page.locator('.connection');
  if(await connection.getAttribute('open')===null)await connection.locator(':scope>summary').click();
  await page.getByLabel('접근 토큰').fill('owned-joint-screen-test');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await revealConnectedControls(page);await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('ventilation');
}
async function lookup(page:Page,data=base){
  const details=page.locator('.joint-replay .crop-lookup');if(await details.getAttribute('open')===null)await details.locator(':scope>summary').click();
  for(const [key,value] of Object.entries(data.lookup))await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function mock(page:Page,data=base){
  const calls:string[]=[];
  await page.route(pattern,async route=>{
    const request=route.request(),q=new URL(request.url()).searchParams,kind=q.get('view')!;
    expect(request.headers().authorization).toBe('Bearer owned-joint-screen-test');expect(request.method()).toBe('GET');
    const expected=Object.fromEntries(Object.entries(data.lookup).filter(([k])=>k!=='result_id'));
    expect(Object.fromEntries([...q].filter(([k])=>!['view','offset','limit'].includes(k)))).toEqual(expected);
    const value=data.rows.find(row=>kind==='summary'?row.summary!==null:row.page?.kind===kind);need(value);
    if(value.page){expect(Number(q.get('offset'))).toBe(value.page.offset);expect(Number(q.get('limit'))).toBe(value.page.limit);}
    calls.push(kind);await route.fulfill({json:value,headers:{'cache-control':'no-store'}});
  });return calls;
}
async function sameSample(page:Page,index:number,data=base){
  const row=data.samples[index]!,at=row.time.at,viewer=page.locator('.joint-viewer');
  await expect(viewer).toHaveAttribute('data-result-id',data.summary.result_id);await expect(viewer).toHaveAttribute('data-selected-index',String(index));
  await expect(viewer).toHaveAttribute('data-farm',JSON.stringify(data.summary.farm));await expect(viewer).toHaveAttribute('data-reference',JSON.stringify(data.summary.reference));
  for(const selector of ['.joint-viewer','.coupled-readout:not(.ventilation-diagnostic)','.joint-history','.joint-distribution','.coupled-cohorts','.joint-ledgers','.coupled-scene'])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',at);
  for(const [key,q] of Object.entries({...row.value.plant_state,...row.value.climate_state,...row.value.derived}))
    await expect(page.locator(`.coupled-readout [data-metric="${key}"]`)).toHaveAttribute('data-raw-value',String(q.value));
  const cohorts=await page.locator('.coupled-cohorts tbody tr').evaluateAll(rows=>rows.map(row=>
    [...row.querySelectorAll<HTMLElement>('[data-raw-value]')].map(e=>e.dataset.rawValue)));
  expect(cohorts).toEqual(row.value.cohort_state.fruit_number.map((q,i)=>[String(row.value.cohort_state.fruit_carbohydrate[i]!.value),String(q.value)]));
  for(const kind of ['fruit_carbohydrate','fruit_number'] as const)expect(JSON.parse((await page.locator(`[data-distribution="${kind}"] .coupled-plot`).getAttribute('data-values'))!))
    .toEqual(row.value.cohort_state[kind].map(q=>q.value));
  const diagnostic=page.locator('.ventilation-diagnostic');await expect(diagnostic).toHaveAttribute('data-selected-at',at);
  expect(JSON.parse((await diagnostic.getAttribute('data-ventilation'))!)).toEqual(row.value.ventilation);
  for(const [key,q] of Object.entries({...row.value.ventilation.derived,...row.value.ventilation.forcing_contribution,latent_energy:row.value.ventilation.latent_energy}))
    await expect(diagnostic.locator(`[data-metric="${key}"]`)).toHaveAttribute('data-raw-value',String(q.value));
  const canvas=page.locator('.coupled-canvas');await expect(canvas).toHaveAttribute('data-scene-at',at);
  const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!),scales=jointSceneScales(data.samples);
  expect(JSON.stringify(drawing.scales)).toBe(JSON.stringify(scales));expect(drawing.carbon.map((v:{value:number})=>v.value)).toEqual(row.value.cohort_state.fruit_carbohydrate.map(q=>q.value));
  expect(drawing.number.map((v:{value:number})=>v.value)).toEqual(row.value.cohort_state.fruit_number.map(q=>q.value));
  expect(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-row.value.derived.leaf_area_index.value)).toBeLessThan(1e-6);
  const temperatures=JSON.parse((await canvas.getAttribute('data-temperature-drawing'))!);expect(temperatures.range).toEqual(scales.temperatures);
  for(const [kind,q] of Object.entries({canopy:row.value.derived.canopy_temperature,air:row.value.climate_state.air_temperature})){
    const marker=temperatures.markers.find((m:{kind:string})=>m.kind===kind);expect(marker.value).toBe(q.value);expect(marker.unit).toBe(q.unit);
    expect(marker.y).toBe(.1+temperaturePosition(q.value,scales.temperatures!));}
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  const ledger=await page.locator('.joint-ledgers [data-raw-value]').evaluateAll(rows=>rows.map(e=>[e.getAttribute('data-metric'),e.getAttribute('data-raw-value')]));
  expect(ledger).toEqual([row.value.integrated_transfers,row.value.event_totals,row.value.balance_residuals,row.value.balance_budgets].flatMap(values=>
    Object.entries(values).map(([k,q])=>[k,String(q.value)])));
}
test('all original completed samples share exact UTC/state/ledgers/chart and actual WebGL temperature markers',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));const calls=await mock(page);await connect(page);await lookup(page);
  for(let i=0;i<base.samples.length;i++){
    if(i)await page.getByRole('button',{name:'다음 저장 성장 시점',exact:true}).click();await sameSample(page,i);
    for(const metric of ['canopy_temperature','air_temperature','leaf_area_index','ventilation_sensible_heat','ventilation_vapor','ventilation_latent_energy']){
      await page.getByLabel('작물·기후 그래프 항목',{exact:true}).selectOption(metric);
      const quantities=base.samples.map(row=>metric==='air_temperature'?row.value.climate_state.air_temperature:metric.startsWith('ventilation_')?row.value.integrated_transfers[metric as 'ventilation_sensible_heat'|'ventilation_vapor'|'ventilation_latent_energy']:row.value.derived[metric as 'canopy_temperature'|'leaf_area_index']);
      await expect(page.locator('.joint-history .coupled-plot')).toHaveAttribute('data-values',JSON.stringify(quantities.map(q=>q.value)));
      await expect(page.locator('.joint-history')).toHaveAttribute('data-selected-value',String(quantities[i]!.value));}
  }
  await page.getByLabel('작물·기후 그래프 항목',{exact:true}).selectOption('fruit_number');await page.getByLabel('그래프 과실 구획',{exact:true}).selectOption({value:'49'});
  await expect(page.locator('.joint-history .coupled-plot')).toHaveAttribute('data-values',JSON.stringify(base.samples.map(s=>s.value.cohort_state.fruit_number[49]!.value)));
  expect(errors).toEqual([]);expect(calls).toEqual(['summary','samples']);
  const evidence=process.env.OSSF_JOINT_VIEW_EVIDENCE;
  if(evidence){await page.getByLabel('작물·기후 그래프 항목',{exact:true}).selectOption('canopy_temperature');
    const connection=page.locator('.connection');if(await connection.getAttribute('open')!==null)await connection.locator(':scope>summary').click();
    await page.locator('.coupled-scene').scrollIntoViewIfNeeded();
    await page.screenshot({path:join(evidence,'joint-completed-desktop.png'),fullPage:false});
    await writeFile(join(evidence,'original-frame-checks.json'),JSON.stringify({indices:base.samples.map((_,i)=>i),UTC:base.samples.map(s=>s.time.at),errors,actual_WebGL:true,scope:'synthetic_saved_screen_only'},null,2));}
  await designSnapshot(page,'joint-completed');
});
test('original management records retain removal/before/after states and return to saved sample mode',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);await page.getByRole('button',{name:'관리 사건 보기',exact:true}).click();
  await expect(page.locator('.joint-viewer')).toHaveCount(0);const articles=page.locator('.cycle-events article');await expect(articles).toHaveCount(base.events.length);
  for(let i=0;i<base.events.length;i++){await expect(articles.nth(i)).toContainText(base.events[i]!.time.at);
    expect(JSON.parse((await articles.nth(i).locator('pre').nth(0).textContent())!)).toEqual(base.events[i]!.value.ventilation_after);
    expect(JSON.parse((await articles.nth(i).locator('pre').nth(1).textContent())!)).toEqual(base.events[i]!.value.management);}
  await page.getByRole('button',{name:'저장 시점 보기',exact:true}).click();await sameSample(page,0);
});
test('hold displays only original confirmed outputs and separates failed boundary and last-confirmed diagnostics',async({page})=>{
  await mock(page,held);await connect(page);await lookup(page,held);await expect(page.getByRole('region',{name:'환기 계산 보류 진단'})).toBeVisible();
  for(let i=0;i<held.samples.length;i++){if(i)await page.getByRole('button',{name:'다음 저장 성장 시점',exact:true}).click();await sameSample(page,i,held);}
  await expect(page.locator('.joint-samples tbody tr')).toHaveCount(held.samples.length);
  await expect(page.locator('.joint-samples')).not.toContainText(held.summary.reference.failed_boundary!.at);
  const root=process.env.OSSF_JOINT_VIEW_EVIDENCE;if(root){await page.getByRole('region',{name:'환기 계산 보류 진단'}).scrollIntoViewIfNeeded();
    await page.screenshot({path:join(root,'joint-hold-desktop.png'),fullPage:false});}
  await designSnapshot(page,'joint-hold');
});
test('selection edit and cancelled pending reply remove all values; next lookup recovers',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  await page.locator('.joint-replay .crop-lookup>summary').click();await page.getByLabel('작물 ID',{exact:true}).fill('edited-crop');
  await expect(page.locator('.joint-viewer,.joint-evidence,.cycle-events')).toHaveCount(0);await lookup(page);await sameSample(page,0);
  let release!:()=>void;const gate=new Promise<void>(r=>{release=r;});let started!:()=>void;const begun=new Promise<void>(r=>{started=r;});
  const late=async(route:Route)=>{started();await gate;await route.fulfill({json:base.summary}).catch(()=>{});};await page.route(pattern,late);
  await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();await begun;
  await page.getByRole('button',{name:'연구 조회 취소',exact:true}).click();await expect(page.locator('.joint-viewer')).toHaveCount(0);release();
  await page.unroute(pattern,late);await lookup(page);await sameSample(page,0);
});
for(const status of [401,403,404,422])test(`current server denial ${status} clears previous display`,async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  await page.route(pattern,route=>route.fulfill({status,json:{detail:'owned-test-denial'}}));
  await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();await expect(page.getByRole('alert')).toBeVisible();
  await expect(page.locator('.joint-viewer,.joint-evidence,.cycle-events')).toHaveCount(0);
});
test('wrong response version clears all values and format choices coexist',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  await page.route(pattern,route=>route.fulfill({json:{...base.summary,schema_version:'crop-cycle-calculation-replay-v1'}}));
  await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();await expect(page.getByRole('alert')).toContainText('판본');
  await expect(page.locator('.joint-viewer')).toHaveCount(0);
  for(const format of ['v1','v2','v3','cycle','calculation-cycle']){
    await page.getByLabel('저장 결과 판본').selectOption(format);await expect(page.locator('.joint-replay')).toHaveCount(0);}
});
test('zero selected outputs create no start/end frame or automatic playback',async({page})=>{
  const original=base.rows[1];need(original?.page?.kind==='samples');
  const reference={...base.summary.reference,artifact:{...base.summary.reference.artifact,sample_count:0}};
  const summary={...base.summary,reference},samplePage={...original,reference,page:{...original.page,total:0,records:[],next_offset:null}};
  await page.route(pattern,route=>route.fulfill({json:new URL(route.request().url()).searchParams.get('view')==='summary'?summary:samplePage}));
  await connect(page);await lookup(page);await expect(page.getByRole('heading',{name:'선택 가능한 저장 시점이 없습니다',exact:true})).toBeVisible();
  await expect(page.locator('.joint-viewer,.coupled-canvas,.crop-timeline')).toHaveCount(0);
  const root=process.env.OSSF_JOINT_VIEW_EVIDENCE;if(root)await page.screenshot({path:join(root,'joint-empty-desktop.png'),fullPage:false});
  await designSnapshot(page,'joint-empty');
});
test('account change while a normal response is pending cannot restore old values',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  let release!:()=>void;const gate=new Promise<void>(r=>{release=r;});let started!:()=>void;const begun=new Promise<void>(r=>{started=r;});
  const late=async(route:Route)=>{started();await gate;await route.fulfill({json:base.summary}).catch(()=>{});};await page.route(pattern,late);
  await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();await begun;
  const connection=page.locator('.connection');if(await connection.getAttribute('open')===null)await connection.locator(':scope>summary').click();
  await page.getByLabel('접근 토큰',{exact:true}).fill('owned-joint-screen-account-change');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await revealConnectedControls(page);release();await page.unroute(pattern,late);
  await expect(page.locator('.joint-viewer,.joint-evidence,.cycle-events')).toHaveCount(0);
});
test('mobile keyboard/reduced motion and WebGL loss retain exact table and time navigation',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  await expect(page.getByRole('button',{name:'성장 자동 재생',exact:true})).toBeDisabled();
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');await sameSample(page,1);
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);expect(overflow).toBe(false);
  await page.locator('.coupled-canvas').evaluate(canvas=>(canvas as HTMLCanvasElement).getContext('webgl2')?.getExtension('WEBGL_lose_context')?.loseContext());
  await expect(page.locator('.crop-scene-fallback')).toBeVisible();await slider.focus();await slider.press('ArrowLeft');
  await expect(page.locator('.joint-viewer')).toHaveAttribute('data-selected-at',base.samples[0]!.time.at);
  await expect(page.locator('.coupled-readout [data-metric=canopy_temperature]')).toHaveAttribute('data-raw-value',String(base.samples[0]!.value.derived.canopy_temperature.value));
  const root=process.env.OSSF_JOINT_VIEW_EVIDENCE;if(root)await page.screenshot({path:join(root,'joint-mobile-fallback.png'),fullPage:false});
});
