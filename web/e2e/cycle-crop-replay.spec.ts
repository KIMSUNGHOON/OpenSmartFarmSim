import { test,expect,type Page } from '@playwright/test';
import { mkdir,writeFile } from 'node:fs/promises';
import { cycleReference,cyclePage } from './cycle-crop-fixture';
import { startupCohortScales } from '../src/coupledCropGeometry';
type Dataset=ReturnType<typeof cycleReference>;
const token='synthetic-cycle-browser-token-only',base=cycleReference();
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
test.setTimeout(90_000);
async function connect(page:Page){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('cycle');await expect(page.locator('.cycle-replay')).toBeVisible();
}
async function lookup(page:Page,data=base){
  if(!await page.getByLabel(labels.result_id,{exact:true}).isVisible())await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:data.summary.result_id,...data.summary.farm}))
    await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function mock(page:Page,data=base,shortCount?:number){
  const calls:{kind:string;offset:number;limit:number}[]=[];
  await page.route('**/v1/crop-cycle-research-results/**',async route=>{
    expect(route.request().method()).toBe('GET');expect(route.request().headers().authorization).toBe('Bearer '+token);
    const q=new URL(route.request().url()).searchParams,kind=q.get('view')!,offset=Number(q.get('offset')),limit=Number(q.get('limit'));
    calls.push({kind,offset,limit});await route.fulfill({json:kind==='summary'?data.summary:cyclePage(data,kind as 'samples'|'events',offset,limit,shortCount)});
  });return calls;
}
async function sameSample(page:Page,globalIndex:number,offset:number,data:Dataset=base,scene=true){
  const row=data.samples[globalIndex]!,canvas=page.locator('.coupled-canvas');
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-result-id',data.summary.result_id);
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-index',String(globalIndex));
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-farm',JSON.stringify(data.summary.farm));
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-reference',JSON.stringify(data.summary.reference));
  for(const target of ['.coupled-viewer','.coupled-readout','.coupled-history','.coupled-distribution',...(scene?['.coupled-scene']:[])])
    await expect(page.locator(target)).toHaveAttribute('data-selected-at',row.at);
  const values=await page.locator('.coupled-cohort-table tbody tr').evaluateAll(rows=>rows.map(r=>({
    carbon:r.querySelector<HTMLElement>('[data-metric=carbon]')!.dataset.rawValue,number:r.querySelector<HTMLElement>('[data-metric=number]')!.dataset.rawValue})));
  expect(values).toEqual(row.state.fruit_number.map((n,i)=>({carbon:String(row.state.fruit_carbohydrate[i]!.value),number:String(n.value)})));
  for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'] as const)
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(row.state[key].value));
  for(const key of ['lai','fruit_carbohydrate_total'] as const)
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(row[key].value));
  const details=page.locator('.crop-cumulative');await details.locator('summary').click();
  const raw=await details.locator('[data-cumulative],[data-startup-diagnostic],[data-balance]').evaluateAll(items=>items.map(e=>({
    key:e.getAttribute('data-cumulative')??e.getAttribute('data-startup-diagnostic')??e.getAttribute('data-balance'),value:e.getAttribute('data-raw-value')})));
  expect(raw).toEqual([...Object.entries(row.cumulative),...Object.entries(row.startup_diagnostics),
    ...(['carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'] as const).map(k=>[k,row[k]] as const)].map(([key,q])=>({key,value:String(q.value)})));
  await details.locator('summary').click();
  for(const kind of ['carbon','number'] as const)expect(JSON.parse((await page.locator(`[data-distribution=${kind}] .coupled-plot`).getAttribute('data-values'))!))
    .toEqual(row.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'].map(q=>q.value));
  const count=Number(await page.locator('.cycle-range').getAttribute('data-count'));
  expect(JSON.parse((await page.locator('.coupled-history .coupled-plot').getAttribute('data-values'))!)).toEqual(data.samples.slice(offset,offset+count).map(s=>s.lai.value));
  if(scene){await expect(canvas).toHaveAttribute('data-scene-at',row.at);const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!);
    expect(drawing.scales).toEqual(startupCohortScales(data.samples.slice(offset,offset+count)));
    for(const kind of ['carbon','number'] as const){expect(drawing[kind]).toHaveLength(50);
      for(let i=0;i<50;i++){const q=row.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'][i]!,mesh=drawing[kind][i],b=drawing.scales.logarithmic[kind];
        expect(mesh.index).toBe(i+1);expect(mesh.value).toBe(q.value);expect(mesh.unit).toBe(q.unit);expect(mesh.visible).toBe(q.value>0);
        const height=q.value===0?0:(Math.log10(q.value)-b.lower)/(b.upper-b.lower);
        expect(Math.abs(mesh.height-height)).toBeLessThanOrEqual(4*Number.EPSILON);expect(mesh.y).toBe(mesh.height/2);}}
    expect(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));
    expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);}
}
test('original 25h 27 UTC rows use four bounded pages and 100 C/N meshes per selected frame',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));const calls=await mock(page);await connect(page);await lookup(page);
  for(const offset of [0,7,14,21]){
    await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));
    await expect(page.locator('.coupled-time-table tbody tr')).toHaveCount(Math.min(7,27-offset));
    for(let i=0;i<Math.min(7,27-offset);i++){
      if(i){await page.getByRole('slider',{name:'저장 성장 시점 선택'}).focus();await page.getByRole('slider',{name:'저장 성장 시점 선택'}).press('ArrowRight');}
      await sameSample(page,offset+i,offset);}
    if(offset<21)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await expect(page.getByRole('button',{name:'다음 저장 범위',exact:true})).toBeDisabled();
  expect(calls).toEqual([{kind:'summary',offset:0,limit:0},...[0,7,14,21].map(offset=>({kind:'samples',offset,limit:7}))]);
  await expect(page.locator('.startup-log-scale')).toContainText('현재 읽은 범위');expect(errors).toEqual([]);
  await page.locator('.connection>summary').click();await page.screenshot({path:'../research/artifacts/cycle-crop-desktop.png',fullPage:true});
});
test('original five events have 2/2/1 rows, clear numeric scene, and return to the actually visited sample page',async({page})=>{
  const calls=await mock(page);await connect(page);await lookup(page);await expect(page.locator('.coupled-viewer')).toBeVisible();
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','7');
  await page.getByRole('button',{name:'관리 사건 보기',exact:true}).click();
  for(const offset of [0,2,4]){
    await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));await expect(page.locator('.coupled-canvas')).toHaveCount(0);
    const articles=page.locator('.cycle-events article');await expect(articles).toHaveCount(Math.min(2,5-offset));
    for(let i=0;i<Math.min(2,5-offset);i++){const event=base.events[offset+i]!,article=articles.nth(i);await expect(article).toContainText(event.at);
      for(const key of ['leaf','stem_root'] as const)await expect(article.locator(`[data-event-metric=${key}]`)).toHaveAttribute('data-raw-value',String(event.removed[key].value));
      for(const [n,state] of [event.removed,event.before,event.after].entries()){
        const rows=await article.locator('details').nth(n).locator('tbody tr').evaluateAll(rows=>rows.map(r=>[r.querySelector<HTMLElement>('[data-metric=carbon]')!.dataset.rawValue,r.querySelector<HTMLElement>('[data-metric=number]')!.dataset.rawValue]));
        expect(rows).toEqual(state.fruit_number.map((q,j)=>[String(state.fruit_carbohydrate[j]!.value),String(q.value)]));}
      for(const [n,state] of [event.before,event.after].entries())for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'] as const)
        await expect(article.locator('details').nth(n+1).locator(`[data-event-state=${key}]`)).toHaveAttribute('data-raw-value',String(state[key].value));}
    if(offset<4)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();}
  await page.getByRole('button',{name:'이전 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','2');
  await page.getByRole('button',{name:'저장 시점 보기',exact:true}).click();await sameSample(page,7,7);
  expect(calls.map(c=>[c.kind,c.offset])).toEqual([['summary',0],['samples',0],['samples',7],['events',0],['events',2],['events',4],['events',2],['samples',7]]);
});
test('byte-short pages use actual next and visited prior offsets, without filling the requested limit',async({page})=>{
  const calls=await mock(page,base,2);await connect(page);await lookup(page);await expect(page.locator('.cycle-range')).toHaveAttribute('data-count','2');
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','2');
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','4');
  await page.getByRole('button',{name:'이전 저장 범위',exact:true}).click();await sameSample(page,2,2);
  expect(calls.filter(c=>c.kind==='samples').map(c=>c.offset)).toEqual([0,2,4,2]);
});
for(const kind of ['empty-hold','empty-completed'] as const)test(kind+' keeps the valid empty output without inventing start/end or failed frames',async({page})=>{
  const data=cycleReference(kind);await mock(page,data);await connect(page);await lookup(page,data);
  await expect(page.locator('.cycle-no-samples')).toBeVisible();await expect(page.locator('.coupled-canvas')).toHaveCount(0);
  await expect(page.getByRole('slider')).toHaveCount(0);await expect(page.locator('.coupled-plot')).toHaveCount(0);
  if(kind==='empty-hold'){await expect(page.locator('.coupled-hold')).toContainText(data.summary.summary.hold!.at);
    await page.screenshot({path:'../research/artifacts/cycle-crop-empty-hold.png',fullPage:true});}
});
test('shape-only past hold keeps fractional last confirmed diagnosis separate from original selected UTC',async({page})=>{
  const data=cycleReference('past-hold');await mock(page,data);await connect(page);await lookup(page,data);await sameSample(page,0,0,data);
  await expect(page.locator('.coupled-hold')).toContainText(data.summary.summary.hold!.at);
  await expect(page.locator('.coupled-time-table')).not.toContainText(data.summary.summary.hold!.last_confirmed!.at);
  await page.locator('.coupled-hold summary').click();await expect(page.locator('[data-confirmed-cumulative]')).toHaveCount(16);
  await expect(page.locator('[data-confirmed-startup-diagnostic]')).toHaveCount(4);
  await page.screenshot({path:'../research/artifacts/cycle-crop-past-hold-shape.png',fullPage:true});
});
for(const status of [403,404,422,503])test('current page '+status+' clears all old numeric values and stops playback',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);
  await page.getByRole('button',{name:'성장 자동 재생'}).click();await page.unroute('**/v1/crop-cycle-research-results/**');
  await page.route('**/v1/crop-cycle-research-results/**',route=>route.fulfill({status,json:{error:{code:'synthetic-denial',message:'synthetic'}}}));
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.getByRole('alert')).toBeVisible();
  for(const target of ['.coupled-canvas','.coupled-viewer','.coupled-plot','.cycle-range'])await expect(page.locator(target)).toHaveCount(0);
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-samples','0');
});
test('mixed reference on a later page fails closed rather than drawing old or mixed quantities',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);await page.unroute('**/v1/crop-cycle-research-results/**');
  await page.route('**/v1/crop-cycle-research-results/**',route=>{const value=cyclePage(base,'samples',7,7);
    return route.fulfill({json:{...value,reference:{...value.reference,proof_sha256:'f'.repeat(64)}}});});
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.getByRole('alert')).toContainText('표시를 보류');
  await expect(page.locator('.coupled-canvas')).toHaveCount(0);await expect(page.locator('.coupled-time-table')).toHaveCount(0);
});
test('cancel and late full response cannot restore a cleared scene; fresh query recovers',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);await page.unroute('**/v1/crop-cycle-research-results/**');
  let release!:()=>void,entered!:()=>void;const waiting=new Promise<void>(r=>release=r),started=new Promise<void>(r=>entered=r);
  await page.route('**/v1/crop-cycle-research-results/**',async route=>{entered();await waiting;
    await route.fulfill({json:cyclePage(base,'samples',7,7)}).catch(()=>{});});
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await started;
  await expect(page.locator('.coupled-canvas')).toHaveCount(0);await page.getByRole('button',{name:'연구 조회 취소',exact:true}).click();release();
  await expect(page.getByRole('alert')).toContainText('취소');await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','idle');
  await page.unroute('**/v1/crop-cycle-research-results/**');await mock(page);await lookup(page);await sameSample(page,0,0);
});
test('ID edit and account change clear scene and prevent old autoplay from selecting another frame',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);await page.getByRole('button',{name:'성장 자동 재생'}).click();
  await page.getByText('저장 연구 결과 조회',{exact:true}).click();await page.getByLabel(labels.result_id,{exact:true}).fill(base.summary.result_id.slice(0,-1)+'0');
  await expect(page.locator('.coupled-canvas')).toHaveCount(0);await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','idle');
  await lookup(page);await sameSample(page,0,0);await page.getByLabel('접근 토큰').fill('synthetic-other-cycle-account-only');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('cycle');await expect(page.locator('.coupled-canvas')).toHaveCount(0);
});
test('mobile, 200 percent text enlargement, keyboard and reduced motion retain exact HTML access',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});await mock(page);await connect(page);await lookup(page);
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');await sameSample(page,1,0);
  await expect(page.getByRole('button',{name:'성장 자동 재생'})).toBeDisabled();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:'../research/artifacts/cycle-crop-mobile.png',fullPage:true});
  await page.setViewportSize({width:780,height:844});await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).focus();await page.keyboard.press('Enter');await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','7');
});
test('actual WebGL context loss keeps HTML values and restores only the current original UTC',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);
  await page.locator('.coupled-canvas').evaluate(el=>{const gl=(el as HTMLCanvasElement).getContext('webgl2')!;
    (globalThis as any).__cycleLose=gl.getExtension('WEBGL_lose_context');(globalThis as any).__cycleLose.loseContext();});
  await expect(page.locator('.crop-scene-fallback')).toBeVisible();await page.getByRole('slider',{name:'저장 성장 시점 선택'}).focus();
  await page.getByRole('slider',{name:'저장 성장 시점 선택'}).press('ArrowRight');await sameSample(page,1,0,base,false);
  await page.evaluate(()=>{(globalThis as any).__cycleLose.restoreContext();delete (globalThis as any).__cycleLose;});await sameSample(page,1,0);
});
test('shape-only many windows retain one page/canvas; CPU4x records response and JS heap, then unmounts',async({page})=>{
  const data=cycleReference('many');await mock(page,data);await connect(page);await lookup(page,data);
  const cdp=await page.context().newCDPSession(page);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});await cdp.send('Performance.enable');
  const timings:number[]=[],heaps:number[]=[];
  for(let i=0;i<20;i++){
    await expect(page.locator('.coupled-canvas')).toHaveAttribute('data-scene-at',data.samples[i*7]!.at);await expect(page.locator('.coupled-canvas')).toHaveCount(1);
    await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-samples','7');await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-events','0');
    const drawing=JSON.parse((await page.locator('.coupled-canvas').getAttribute('data-cohort-drawing'))!);expect(drawing.carbon.length+drawing.number.length).toBe(100);
    const metrics=await cdp.send('Performance.getMetrics');heaps.push(metrics.metrics.find(m=>m.name==='JSHeapUsedSize')!.value);
    const t=performance.now();await page.getByRole('slider',{name:'저장 성장 시점 선택'}).focus();await page.getByRole('slider',{name:'저장 성장 시점 선택'}).press('ArrowRight');
    await expect(page.locator('.coupled-canvas')).toHaveAttribute('data-scene-at',data.samples[i*7+1]!.at);timings.push(performance.now()-t);
    if(i<19){await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String((i+1)*7));}}
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});await cdp.detach();
  await mkdir('/tmp/ossf-cycle-browser-20261006',{recursive:true});await writeFile('/tmp/ossf-cycle-browser-20261006/shape-performance.json',JSON.stringify({
    scope:'shape_only_fixture_CPU4x_emulation_not_real_low_end_device_or_whole_WSL_memory',windows:20,selected_input_response_ms:timings,js_heap_used_bytes:heaps,max_input_response_ms:Math.max(...timings),max_js_heap_used_bytes:Math.max(...heaps)},null,2));
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();await expect(page.locator('.coupled-canvas')).toHaveCount(0);
});
