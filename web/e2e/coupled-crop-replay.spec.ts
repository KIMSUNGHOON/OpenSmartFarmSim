import { test,expect,type Page } from '@playwright/test';
import { coupledReference } from './coupled-crop-fixture';

const token='synthetic-coupled-browser-token-only';
test.setTimeout(90_000);
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',
  registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
async function connect(page:Page){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('v2');
}
async function lookup(page:Page,data:Pick<ReturnType<typeof coupledReference>,'result_id'|'farm'>=coupledReference()){
  await expect(page.locator('.coupled-replay')).toBeVisible();
  if(!await page.getByLabel(labels.result_id,{exact:true}).isVisible())await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:data.result_id,...data.farm}))
    await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function mock(page:Page,data:unknown=coupledReference(),status=200){
  await page.route('**/v1/crop-coupled-research-results/**',async route=>{
    expect(route.request().method()).toBe('GET');expect(route.request().headers().authorization).toBe('Bearer '+token);
    await route.fulfill({status,json:status===200?data:{error:'synthetic-denial'}});
  });
}
async function sameSample(page:Page,index:number,data=coupledReference(),scene=true){
  const sample=data.samples[index]!;
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-result-id',data.result_id);
  for(const target of ['.coupled-viewer','.coupled-readout','.coupled-cohorts','.coupled-history',...(scene?['.coupled-scene']:[])])
    await expect(page.locator(target)).toHaveAttribute('data-selected-at',sample.at);
  for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'] as const)
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(sample.state[key].value));
  const rows=page.locator('.coupled-cohort-table tbody tr');await expect(rows).toHaveCount(50);
  for(let i=0;i<50;i++){
    await expect(rows.nth(i).locator('[data-metric=carbon]')).toHaveAttribute('data-raw-value',String(sample.state.fruit_carbohydrate[i]!.value));
    await expect(rows.nth(i).locator('[data-metric=number]')).toHaveAttribute('data-raw-value',String(sample.state.fruit_number[i]!.value));
  }
  if(scene){
    const canvas=page.locator('.coupled-canvas');await expect(canvas).toHaveAttribute('data-scene-at',sample.at);
    const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!);
    for(let i=0;i<50;i++)for(const kind of ['carbon','number'] as const){
      const q=sample.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'][i]!;
      expect(drawing[kind][i].index).toBe(i+1);expect(drawing[kind][i].value).toBe(q.value);
      expect(drawing[kind][i].unit).toBe(q.unit);
      expect(drawing[kind][i].height).toBe(drawing.scales[kind]?q.value/drawing.scales[kind]:0);
      expect(drawing[kind][i].visible).toBe(q.value>0);
    }
    const area=Number(await canvas.getAttribute('data-leaf-surface-area'));
    expect(Math.abs(area-sample.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,sample.lai.value*1e-6));
    expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  }
}

test('saved C/N geometry, exact table and history share discrete UTC frames',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});
  for(let i=0;i<6;i++){
    if(i)await slider.focus(),await slider.press('ArrowRight');await sameSample(page,i);
    await page.getByLabel('연결 연구 그래프 항목').selectOption('fruit_number');
    await page.getByLabel('그래프 과실 구획').selectOption({value:'49'});
    await expect(page.locator('.coupled-history')).toHaveAttribute('data-selected-value',String(coupledReference().samples[i]!.state.fruit_number[49]!.value));
  }
  await slider.focus();await slider.press('Home');await sameSample(page,0);
  await page.getByRole('button',{name:'연결 연구 오른쪽에서 보기'}).click();await sameSample(page,0);
  await page.getByRole('button',{name:'연결 연구 자동 재생'}).click();await expect(slider).not.toHaveValue('0');
  await page.getByRole('button',{name:'연결 연구 일시 정지'}).click();
  expect(errors).toEqual([]);
});

// Cardinality and paging shapes only. Copied synthetic values do not simulate this extended period.
function capacity(){
  const d=coupledReference();const seed=d.samples[0]!;
  d.end_utc=new Date(Date.parse(d.start_utc)+511_000).toISOString().replace('.000Z','Z');
  d.samples=Array.from({length:512},(_,i)=>({...structuredClone(seed),at:new Date(Date.parse(d.start_utc)+i*1000).toISOString().replace('.000Z','Z')}));
  d.events=Array.from({length:128},(_,i)=>({...structuredClone(d.events[0]!),at:d.samples[i]!.at}));return d;
}
function paged(d:ReturnType<typeof coupledReference>,offset=0,eventOffset=0){
  return {...structuredClone(d),samples:d.samples.slice(offset,offset+64),events:d.events.slice(eventOffset,eventOffset+8),
    sample_page:{offset,limit:64,total:d.samples.length,next_offset:offset+64<d.samples.length?offset+64:null},
    event_page:{offset:eventOffset,limit:8,total:d.events.length,next_offset:eventOffset+8<d.events.length?eventOffset+8:null}};
}
test('complete 512-frame pages load sequentially and event-page refusal clears the scene',async({page})=>{
  const data=capacity(),calls:{sample:number;event:number}[]=[];
  await page.route('**/v1/crop-coupled-research-results/**',async route=>{
    const q=new URL(route.request().url()).searchParams,sample=Number(q.get('sample_offset')),event=Number(q.get('event_offset'));
    calls.push({sample,event});
    await route.fulfill({json:paged(data,sample,event)});
  });
  await connect(page);await lookup(page,data);
  await expect(page.locator('.coupled-viewer')).toBeVisible();
  expect(calls).toEqual(Array.from({length:8},(_,i)=>({sample:i*64,event:i?128:0})));
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});
  await slider.focus();await slider.press('End');await sameSample(page,511,data);
  await page.locator('.coupled-events>summary').click();
  await page.getByRole('button',{name:'다음 8사건',exact:true}).click();
  await expect(page.locator('.coupled-events')).toContainText('9–16 / 128');
  expect(calls.at(-1)).toEqual({sample:512,event:8});
  await page.unrouteAll();await mock(page,undefined,403);
  await page.getByRole('button',{name:'다음 8사건',exact:true}).click();
  await expect(page.locator('.coupled-replay [role=alert]')).toContainText('조회 권한');
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.coupled-events,.crop-evidence')).toHaveCount(0);
});

test('partial pages show progress and cancellation discards late data',async({page})=>{
  const data=capacity();let release:(()=>void)|undefined;
  await page.route('**/v1/crop-coupled-research-results/**',async route=>{
    const q=new URL(route.request().url()).searchParams,offset=Number(q.get('sample_offset'));
    if(offset)await new Promise<void>(r=>{release=r;});
    await route.fulfill({json:paged(data,offset,offset?128:0)});
  });
  await connect(page);await lookup(page,data);
  await expect(page.locator('.coupled-progress')).toContainText('1페이지 · 64/512시점');
  await expect(page.locator('.coupled-viewer,.coupled-canvas')).toHaveCount(0);
  await expect.poll(()=>!!release).toBe(true);await page.getByRole('button',{name:'연구 조회 취소'}).click();release!();
  await expect(page.locator('.coupled-replay [role=alert]')).toContainText('취소');
  await expect(page.locator('.coupled-viewer,.coupled-canvas')).toHaveCount(0);
});

test('fractional hold has only confirmed past frames and empty hold has no numeric scene',async({page})=>{
  const past=coupledReference('fractional');await mock(page,past);await connect(page);await lookup(page,past);await sameSample(page,0,past);
  await expect(page.locator('.coupled-hold')).toContainText(past.hold!.at);
  await expect(page.getByRole('slider',{name:'연결 연구 저장 시점 선택'})).toHaveAttribute('max','0');
  await expect(page.getByRole('button',{name:'연결 연구 자동 재생'})).toBeDisabled();
  await page.unrouteAll();const empty=coupledReference('empty');await mock(page,empty);await lookup(page,empty);
  await expect(page.locator('.coupled-hold')).toContainText('확인된 과거 sample');
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.coupled-history,.coupled-cohort-table')).toHaveCount(0);
});

test('editing a farm invalidates pending pages and account change clears previous results',async({page})=>{
  let release:(()=>void)|undefined;
  await page.route('**/v1/crop-coupled-research-results/**',async route=>{
    await new Promise<void>(r=>{release=r;});await route.fulfill({json:coupledReference()});
  });
  await connect(page);await lookup(page);await expect.poll(()=>!!release).toBe(true);
  await page.getByLabel('작물 ID',{exact:true}).fill('another-crop');release!();
  await expect(page.locator('.coupled-replay')).toHaveAttribute('aria-busy','false');
  await expect(page.locator('.coupled-viewer')).toHaveCount(0);
  await page.unrouteAll();await mock(page);await lookup(page);await sameSample(page,0);
  await page.getByLabel('접근 토큰').fill('another-synthetic-token');await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await expect(page.locator('.coupled-viewer,.coupled-canvas')).toHaveCount(0);
  expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
});

test('WebGL loss clears drawing evidence and restoration uses the selected saved frame',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0);
  const canvas=page.locator('.coupled-canvas');const extension=await canvas.evaluateHandle(element=>
    (element as HTMLCanvasElement).getContext('webgl2')!.getExtension('WEBGL_lose_context'));
  await extension.evaluate(x=>x!.loseContext());
  await expect(page.locator('.crop-scene-fallback')).toBeVisible();await expect(canvas).not.toHaveAttribute('data-scene-at');
  const slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});await slider.focus();await slider.press('End');await sameSample(page,5,coupledReference(),false);
  await extension.evaluate(x=>x!.restoreContext());await sameSample(page,5);await extension.dispose();
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();await expect(page.locator('.coupled-canvas')).toHaveCount(0);
});

test('HTML fallback, reduced motion, mobile and zoom keep exact quantities usable',async({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype,'getContext',{value:function(this:HTMLCanvasElement,kind:string,...args:unknown[]){
      return kind==='webgl2'?null:Reflect.apply(original,this,[kind,...args]);}});});
  await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:390,height:844});
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,coupledReference(),false);
  await expect(page.locator('.crop-scene-fallback')).toBeVisible();
  await expect(page.getByRole('button',{name:'연결 연구 자동 재생'})).toBeDisabled();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  for(const width of [320,768,1536]){
    await page.setViewportSize({width,height:900});await page.evaluate(()=>{document.documentElement.style.fontSize='32px';});
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  }
  await page.getByRole('slider',{name:'연결 연구 저장 시점 선택'}).focus();
  await page.keyboard.press('End');await sameSample(page,5,coupledReference(),false);
});

test('mixed later manifest rejects the whole result without a partial numeric scene',async({page})=>{
  const data=capacity();await page.route('**/v1/crop-coupled-research-results/**',async route=>{
    const offset=Number(new URL(route.request().url()).searchParams.get('sample_offset'));
    const value=paged(data,offset,offset?128:0);if(offset)value.manifest.result_sha256='f'.repeat(64);
    await route.fulfill({json:value});
  });
  await connect(page);await lookup(page,data);
  await expect(page.locator('.coupled-replay [role=alert]')).toContainText('페이지');
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.coupled-history')).toHaveCount(0);
});

test('unsafe positive GPU representation keeps original HTML values instead of a minimum bar',async({page})=>{
  const data=coupledReference();data.samples[0]!.state.fruit_number[0]!.value=Number.MIN_VALUE;
  await mock(page,data);await connect(page);await lookup(page);
  await expect(page.locator('.crop-scene-fallback')).toBeVisible();
  await expect(page.locator('.coupled-canvas')).not.toHaveAttribute('data-cohort-drawing');
  await expect(page.locator('.coupled-cohort-table [data-cohort="1"] [data-metric=number]')).toHaveAttribute('data-raw-value',String(Number.MIN_VALUE));
});
