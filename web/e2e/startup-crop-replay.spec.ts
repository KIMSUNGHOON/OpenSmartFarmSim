import { test,expect,type Page } from '@playwright/test';
import { startupReference } from './startup-crop-fixture';
import { decodeStartupCropPage,type StartupCropPage } from '../src/startupCropReplay';

function saved(kind:Parameters<typeof startupReference>[0]='empty-entry'){
  const data=startupReference(kind);return decodeStartupCropPage(data,{result_id:data.result_id,...data.farm});
}

const token='synthetic-startup-browser-token-only';
test.setTimeout(90_000);
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',
  registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
async function connect(page:Page){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('v3');
  await expect(page.locator('.startup-replay')).toBeVisible();
}
async function lookup(page:Page,data:Pick<StartupCropPage,'result_id'|'farm'>=saved()){
  if(!await page.getByLabel(labels.result_id,{exact:true}).isVisible())await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:data.result_id,...data.farm}))
    await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function mock(page:Page,data:unknown=startupReference(),status=200){
  await page.route('**/v1/crop-startup-research-results/**',async route=>{
    expect(route.request().method()).toBe('GET');expect(route.request().headers().authorization).toBe('Bearer '+token);
    await route.fulfill({status,json:status===200?data:{error:'synthetic-denial'}});
  });
}
async function sameSample(page:Page,index:number,data:StartupCropPage=saved(),scene=true){
  const sample=data.samples[index]!;
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-result-id',data.result_id);
  for(const target of ['.coupled-viewer','.coupled-readout','.coupled-cohorts','.coupled-history',...(scene?['.coupled-scene']:[])])
    await expect(page.locator(target)).toHaveAttribute('data-selected-at',sample.at);
  const rows=page.locator('.coupled-cohort-table tbody tr');await expect(rows).toHaveCount(50);
  for(let i=0;i<50;i++){
    await expect(rows.nth(i).locator('[data-metric=carbon]')).toHaveAttribute('data-raw-value',String(sample.state.fruit_carbohydrate[i]!.value));
    await expect(rows.nth(i).locator('[data-metric=number]')).toHaveAttribute('data-raw-value',String(sample.state.fruit_number[i]!.value));
  }
  await page.locator('.crop-cumulative>summary').click();
  for(const [key,q] of Object.entries(sample.cumulative))
    await expect(page.locator('[data-cumulative="'+key+'"]')).toHaveAttribute('data-raw-value',String(q.value));
  for(const [key,q] of Object.entries(sample.startup_diagnostics))
    await expect(page.locator('[data-startup-diagnostic="'+key+'"]')).toHaveAttribute('data-raw-value',String(q.value));
  await page.locator('.crop-cumulative>summary').click();
  if(scene){
    const canvas=page.locator('.coupled-canvas');await expect(canvas).toHaveAttribute('data-scene-at',sample.at);
    const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!);
    for(let i=0;i<50;i++)for(const kind of ['carbon','number'] as const){
      const q=sample.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'][i]!;
      expect(drawing[kind][i].value).toBe(q.value);expect(drawing[kind][i].unit).toBe(q.unit);
      const bound=drawing.scales.logarithmic[kind];
      const height=q.value===0?0:(Math.log10(q.value)-bound.lower)/(bound.upper-bound.lower);
      if(q.value===0)expect(drawing[kind][i].height).toBe(0);
      else expect(Math.abs(drawing[kind][i].height-height)).toBeLessThanOrEqual(4*Number.EPSILON);
      expect(drawing[kind][i].visible).toBe(q.value>0);
    }
    const area=Number(await canvas.getAttribute('data-leaf-surface-area'));
    expect(Math.abs(area-sample.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,sample.lai.value*1e-6));
    expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  }
}

test('v3 saved empty entry connects exact quantities and discrete UTC to actual WebGL',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  await expect(page.locator('.startup-assumptions')).toContainText('약 8.52%');
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});
  for(let i=1;i<3;i++){await slider.focus();await slider.press('ArrowRight');await sameSample(page,i);}
  await page.getByLabel('연결 연구 그래프 항목').selectOption('fruit_number');
  await page.getByLabel('그래프 과실 구획').selectOption({value:'49'});
  await expect(page.locator('.coupled-history')).toHaveAttribute('data-selected-value',String(startupReference().samples[2]!.state.fruit_number[49]!.value));
  expect(errors).toEqual([]);
});

test('full removal hides actual zero cohorts and reentry renders saved tiny quantities without a seed',async({page})=>{
  const data=saved('full-removal-reentry');await mock(page,data);await connect(page);await lookup(page,data);
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});
  for(let i=0;i<3;i++){if(i){await slider.focus();await slider.press('ArrowRight');}await sameSample(page,i,data);}
  await expect(page.locator('.startup-log-scale')).toContainText('로그 비교 척도');
});

// Explicit shape capacity only; copying saved quantities does not simulate this longer period.
function capacity():StartupCropPage{
  const p=saved('positive-tail'),seed=p.samples[0]!;
  const samples=Array.from({length:512},(_,i)=>({...structuredClone(seed),at:new Date(Date.parse(p.start_utc)+i*1000).toISOString().replace('.000Z','Z')}));
  const events=Array.from({length:128},(_,i)=>({...structuredClone(p.events[0]!),at:samples[i]!.at}));
  return {...p,end_utc:new Date(Date.parse(p.start_utc)+511000).toISOString().replace('.000Z','Z'),samples,events};
}
function paged(p:StartupCropPage,s=0,e=0){return {...p,samples:p.samples.slice(s,s+64),events:p.events.slice(e,e+8),
  sample_page:{offset:s,limit:64,total:p.samples.length,next_offset:s+64<p.samples.length?s+64:null},
  event_page:{offset:e,limit:8,total:p.events.length,next_offset:e+8<p.events.length?e+8:null}};}

test('all 512 frames and 128 events load before the scene and local event pages add no requests',async({page})=>{
  const data=capacity(),calls:{sample:number;event:number}[]=[];
  await page.route('**/v1/crop-startup-research-results/**',async route=>{
    const q=new URL(route.request().url()).searchParams,s=Number(q.get('sample_offset')),e=Number(q.get('event_offset'));
    calls.push({sample:s,event:e});await route.fulfill({json:paged(data,s,e)});
  });
  await connect(page);await lookup(page,data);
  await expect(page.locator('.coupled-viewer')).toBeVisible();
  expect(calls).toEqual(Array.from({length:16},(_,i)=>({sample:Math.min(i*64,512),event:i*8})));
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});await slider.focus();await slider.press('End');
  await sameSample(page,511,data);await page.locator('.coupled-events>summary').click();
  await page.getByRole('button',{name:'다음 8사건',exact:true}).click();
  await expect(page.locator('.coupled-events')).toContainText('9–16 / 128');expect(calls).toHaveLength(16);
});

test('canceling while remaining events load rejects late pages and leaves no partial scene',async({page})=>{
  const data=capacity();let release:(()=>void)|undefined;
  await page.route('**/v1/crop-startup-research-results/**',async route=>{
    const q=new URL(route.request().url()).searchParams,s=Number(q.get('sample_offset')),e=Number(q.get('event_offset'));
    if(e===64)await new Promise<void>(r=>{release=r;});await route.fulfill({json:paged(data,s,e)});
  });
  await connect(page);await lookup(page,data);await expect.poll(()=>!!release).toBe(true);
  await expect(page.locator('.coupled-progress')).toContainText('512/512시점');
  await expect(page.locator('.coupled-viewer,.coupled-canvas')).toHaveCount(0);
  await page.getByRole('button',{name:'연구 조회 취소'}).click();release!();
  await expect(page.locator('.startup-replay [role=alert]')).toContainText('취소');
  await expect(page.locator('.coupled-viewer,.coupled-canvas')).toHaveCount(0);
});

test('fractional hold keeps one past frame and separate diagnostics; empty hold has no numeric scene',async({page})=>{
  const past=saved('fractional');await mock(page,past);await connect(page);await lookup(page,past);await sameSample(page,0,past);
  await expect(page.locator('.coupled-hold')).toContainText(past.hold!.at);
  await expect(page.getByRole('slider',{name:'연결 연구 저장 시점 선택'})).toHaveAttribute('max','0');
  await page.getByText('마지막 확인 진단',{exact:false}).click();
  for(const [key,q] of Object.entries(past.hold!.last_confirmed!.startup_diagnostics))
    await expect(page.locator('[data-confirmed-startup-diagnostic="'+key+'"]')).toHaveAttribute('data-raw-value',String(q.value));
  await page.unrouteAll();const empty=saved('empty');await mock(page,empty);await lookup(page,empty);
  await expect(page.locator('.coupled-hold')).toContainText('확인된 과거 sample');
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.coupled-history,.coupled-cohort-table')).toHaveCount(0);
});

test('changing farm or format invalidates late results and an account change clears current geometry',async({page})=>{
  let release:(()=>void)|undefined;
  await page.route('**/v1/crop-startup-research-results/**',async route=>{
    await new Promise<void>(r=>{release=r;});await route.fulfill({json:startupReference()});
  });
  await connect(page);await lookup(page);await expect.poll(()=>!!release).toBe(true);
  await page.getByLabel('작물 ID',{exact:true}).fill('another-crop');release!();
  await expect(page.locator('.startup-replay')).toHaveAttribute('aria-busy','false');await expect(page.locator('.coupled-viewer')).toHaveCount(0);
  await page.unrouteAll();await mock(page);await lookup(page);await sameSample(page,0);
  await page.getByLabel('저장 결과 판본').selectOption('v2');await expect(page.locator('.startup-replay,.coupled-viewer')).toHaveCount(0);
  await page.getByLabel('저장 결과 판본').selectOption('v3');await lookup(page);await sameSample(page,0);
  await page.getByLabel('접근 토큰').fill('another-synthetic-token');await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();await expect(page.locator('.coupled-viewer,.coupled-canvas')).toHaveCount(0);
  expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
});

for(const status of [401,403,422])test('current HTTP '+status+' denial on requery clears previous values and scene',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  await page.unrouteAll();await mock(page,undefined,status);await lookup(page);
  await expect(page.locator('.startup-replay [role=alert]')).toBeVisible();
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.crop-evidence')).toHaveCount(0);
});

test('mixed event manifest rejects the entire result after completed samples',async({page})=>{
  const data=capacity();await page.route('**/v1/crop-startup-research-results/**',async route=>{
    const q=new URL(route.request().url()).searchParams,s=Number(q.get('sample_offset')),e=Number(q.get('event_offset'));
    const value=structuredClone(paged(data,s,e));
    if(e===64)value.manifest={...value.manifest,allocation_policy_sha256:'f'.repeat(64)};
    await route.fulfill({json:value});
  });
  await connect(page);await lookup(page,data);await expect(page.locator('.startup-replay [role=alert]')).toContainText('페이지');
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.coupled-history')).toHaveCount(0);
});

test('WebGL loss and restoration use the selected saved log-scale frame',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  const canvas=page.locator('.coupled-canvas'),extension=await canvas.evaluateHandle(element=>
    (element as HTMLCanvasElement).getContext('webgl2')!.getExtension('WEBGL_lose_context'));
  await extension.evaluate(x=>x!.loseContext());await expect(page.locator('.crop-scene-fallback')).toBeVisible();
  await expect(canvas).not.toHaveAttribute('data-scene-at');
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});await slider.focus();await slider.press('End');await sameSample(page,2,saved(),false);
  await extension.evaluate(x=>x!.restoreContext());await sameSample(page,2);await extension.dispose();
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();await expect(page.locator('.coupled-canvas')).toHaveCount(0);
});

test('HTML fallback, reduced motion, keyboard and narrow or enlarged layouts retain raw values',async({page})=>{
  await page.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype,'getContext',{value:function(this:HTMLCanvasElement,kind:string,...args:unknown[]){
      return kind==='webgl2'?null:Reflect.apply(get,this,[kind,...args]);}});});
  await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,saved(),false);
  await expect(page.locator('.crop-scene-fallback')).toBeVisible();await expect(page.getByRole('button',{name:'연결 연구 자동 재생'})).toBeDisabled();
  for(const width of [320,768,1536]){
    await page.setViewportSize({width,height:900});await page.evaluate(()=>{document.documentElement.style.fontSize='32px';});
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});await slider.focus();await slider.press('End');await sameSample(page,2,saved(),false);
});
