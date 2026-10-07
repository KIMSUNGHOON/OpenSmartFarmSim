import { test,expect,type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
import { need,object } from '../src/api-validation';
import { decodeCalculationCycleCropResponse,validCalculationCycleCropLookup } from '../src/calculationCycleCropReplay';
import { startupCohortScales } from '../src/coupledCropGeometry';

declare global { interface Window { __calculationReadState:()=>{active:number;peak:number}; } }
type Case='long'|'short'|'past'|'empty'|'fractional'|'zero';
const fixture:Record<Case,unknown[]>=JSON.parse(readFileSync(new URL('./calculation-cycle-crop-recorded-responses.json',import.meta.url),'utf8'));
function dataset(name:Case){
  const values=fixture[name].map(raw=>{need(object(raw) && object(raw.farm));
    const lookup={...raw.farm,result_id:raw.result_id};need(validCalculationCycleCropLookup(lookup));
    return decodeCalculationCycleCropResponse(raw,lookup);});
  const summary=values[0];need(summary && summary.summary!==null);
  const rows=values.filter(row=>row.result_id===summary.result_id);
  return {summary,rows,samples:rows.flatMap(row=>row.page?.kind==='samples'?row.page.records:[]),
    events:rows.flatMap(row=>row.page?.kind==='events'?row.page.records:[])};
}
const base=dataset('long'),token='own-synthetic-calculation-view-test-only';
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const routePattern='**/v1/crop-cycle-calculation-research-results/**';
test.setTimeout(90_000);
async function connect(page:Page){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
}
async function lookup(page:Page,data=base){
  await page.getByLabel('저장 결과 판본').selectOption('calculation-cycle');
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-source-kind','calculation');
  if(await page.locator('.crop-lookup').getAttribute('open')===null)await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  await expect(page.getByLabel(labels.result_id,{exact:true})).toBeVisible();
  for(const [key,value] of Object.entries({result_id:data.summary.result_id,...data.summary.farm}))
    await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function mock(page:Page,data=base){
  const calls:{kind:string;offset:number;limit:number}[]=[];
  await page.route(routePattern,async route=>{
    const request=route.request();expect(request.method()).toBe('GET');expect(request.headers().authorization).toBe('Bearer '+token);
    const url=new URL(request.url()),q=url.searchParams,kind=q.get('view')!,offset=Number(q.get('offset')),limit=Number(q.get('limit'));
    expect(decodeURIComponent(url.pathname)).toBe('/v1/crop-cycle-calculation-research-results/'+data.summary.result_id);
    expect(Object.fromEntries([...q].filter(([k])=>!['view','offset','limit'].includes(k)))).toEqual(data.summary.farm);
    calls.push({kind,offset,limit});const value=kind==='summary'?data.summary:data.rows.find(row=>row.page?.kind===kind && row.page.offset===offset);
    need(value);if(value.page)expect(value.page.limit).toBe(limit);
    await route.fulfill({json:value,headers:{'cache-control':'no-store'}});
  });return calls;
}
async function observeReads(page:Page){
  await page.addInitScript(()=>{
    let active=0,peak=0;const original=globalThis.fetch.bind(globalThis);
    globalThis.fetch=async(input,init)=>{
      const url=new URL(input instanceof Request?input.url:String(input),location.href);
      if(!url.pathname.startsWith('/v1/crop-cycle-calculation-research-results/'))return original(input,init);
      active++;peak=Math.max(peak,active);let settled=false;
      const settle=()=>{if(!settled){settled=true;active--;}};
      try{
        const response=await original(input,init);if(!response.ok || !response.body){settle();return response;}
        const body=response.body,getReader=body.getReader.bind(body);
        Object.defineProperty(body,'getReader',{value:()=>{
          const reader=getReader(),read=reader.read.bind(reader),cancel=reader.cancel.bind(reader);
          Object.defineProperty(reader,'read',{value:async()=>{try{const value=await read();if(value.done)settle();return value;}catch(error){settle();throw error;}}});
          Object.defineProperty(reader,'cancel',{value:async(reason?:unknown)=>{try{return await cancel(reason);}finally{settle();}}});
          return reader;
        }});return response;
      }catch(error){settle();throw error;}
    };
    Object.defineProperty(window,'__calculationReadState',{value:()=>({active,peak})});
  });
  return ()=>page.evaluate(()=>window.__calculationReadState());
}
async function sameSample(page:Page,index:number,offset:number,data=base){
  const row=data.samples[index]!,viewer=page.locator('.coupled-viewer');
  await expect(viewer).toHaveAttribute('data-result-id',data.summary.result_id);await expect(viewer).toHaveAttribute('data-selected-index',String(index));
  await expect(viewer).toHaveAttribute('data-farm',JSON.stringify(data.summary.farm));await expect(viewer).toHaveAttribute('data-reference',JSON.stringify(data.summary.reference));
  for(const target of ['.coupled-viewer','.coupled-readout','.coupled-history','.coupled-distribution','.coupled-scene'])
    await expect(page.locator(target)).toHaveAttribute('data-selected-at',row.at);
  for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'] as const)
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(row.state[key].value));
  for(const key of ['lai','fruit_carbohydrate_total'] as const)
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(row[key].value));
  const cohorts=await page.locator('.coupled-cohorts tbody tr').evaluateAll(rows=>rows.map(r=>[
    r.querySelector<HTMLElement>('[data-metric=carbon]')!.dataset.rawValue,r.querySelector<HTMLElement>('[data-metric=number]')!.dataset.rawValue]));
  expect(cohorts).toEqual(row.state.fruit_number.map((q,i)=>[String(row.state.fruit_carbohydrate[i]!.value),String(q.value)]));
  for(const kind of ['carbon','number'] as const)expect(JSON.parse((await page.locator(`[data-distribution=${kind}] .coupled-plot`).getAttribute('data-values'))!))
    .toEqual(row.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'].map(q=>q.value));
  const count=Number(await page.locator('.cycle-range').getAttribute('data-count')),canvas=page.locator('.coupled-canvas');
  expect(JSON.parse((await page.locator('.coupled-history .coupled-plot').getAttribute('data-values'))!)).toEqual(data.samples.slice(offset,offset+count).map(s=>s.lai.value));
  await expect(canvas).toHaveAttribute('data-scene-at',row.at);const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!);
  expect(JSON.stringify(drawing.scales)).toBe(JSON.stringify(startupCohortScales(data.samples.slice(offset,offset+count))));
  for(const kind of ['carbon','number'] as const)expect(drawing[kind].map((q:{value:number})=>q.value))
    .toEqual(row.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'].map(q=>q.value));
  const flows=await page.locator('.crop-cumulative [data-cumulative],.crop-cumulative [data-startup-diagnostic],.crop-cumulative [data-balance]').evaluateAll(items=>items.map(e=>({
    key:e.getAttribute('data-cumulative')??e.getAttribute('data-startup-diagnostic')??e.getAttribute('data-balance'),value:e.getAttribute('data-raw-value')})));
  const expectedFlows=[...Object.entries(row.cumulative),...Object.entries(row.startup_diagnostics),
    ...(['carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'] as const).map(k=>[k,row[k]] as const)]
    .map(([key,q])=>({key,value:String(q.value)}));
  expect(flows.sort((a,b)=>String(a.key).localeCompare(String(b.key)))).toEqual(expectedFlows.sort((a,b)=>a.key.localeCompare(b.key)));
  expect(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));
  expect(JSON.parse((await page.locator('.cycle-evidence pre').textContent())!)).toEqual({farm:data.summary.farm,reference:data.summary.reference,manifest:data.summary.summary.manifest});
}
async function capture(page:Page,name:string){
  const root=process.env.OSSF_CALCULATION_VIEW_EVIDENCE;if(!root)return;
  const details=page.locator('.connection');if(await details.getAttribute('open')!==null)await details.locator(':scope>summary').click();
  await page.screenshot({path:join(root,name+'.png'),fullPage:true});
}

test('explicit verified choice preserves the four original choices and the entire 94-character ID',async({page})=>{
  const calls=await mock(page);await connect(page);const format=page.getByLabel('저장 결과 판본');
  for(const value of ['v1','v2','v3','cycle'])await expect(format.locator(`option[value="${value}"]`)).toHaveCount(1);
  await expect(format.locator('option[value="calculation-cycle"]')).toHaveCount(1);
  await lookup(page);await sameSample(page,0,0);expect(base.summary.result_id).toHaveLength(94);
  await page.getByText('저장 연구 결과 조회',{exact:true}).click();await expect(page.getByLabel(labels.result_id,{exact:true})).toHaveValue(base.summary.result_id);
  expect(calls).toEqual([{kind:'summary',offset:0,limit:0},{kind:'samples',offset:0,limit:7}]);
});

test('all 27 original UTC frames preserve raw state, flows, chart and WebGL values across four windows',async({page})=>{
  const errors:string[]=[],warnings:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text());});
  const reads=await observeReads(page),calls=await mock(page);await connect(page);await lookup(page);
  for(const offset of [0,7,14,21]){
    await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));
    await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-samples',String(Math.min(7,27-offset)));
    for(let i=0;i<Math.min(7,27-offset);i++){
      if(i){const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');}
      await sameSample(page,offset+i,offset);
    }
    if(offset<21)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await expect(page.getByRole('button',{name:'다음 저장 범위',exact:true})).toBeDisabled();
  expect(calls).toEqual([{kind:'summary',offset:0,limit:0},...[0,7,14,21].map(offset=>({kind:'samples',offset,limit:7}))]);
  await expect.poll(reads).toEqual({active:0,peak:1});
  expect(errors).toEqual([]);
  expect(warnings.filter(w=>!/^\[\.WebGL-0x[0-9a-f]+\]GL Driver Message \(OpenGL, Performance, GL_CLOSE_PATH_NV, High\): GPU stall due to ReadPixels(?: \(this message will no longer repeat\))?$/.test(w))).toEqual([]);
  const evidence=process.env.OSSF_CALCULATION_VIEW_EVIDENCE;
  if(evidence)await writeFile(join(evidence,'browser-console-and-reads.json'),JSON.stringify({application_errors:errors,
    driver_performance_warnings:warnings,read_state:await reads(),scope:'owned_synthetic_browser_software_driver_not_production_performance'},null,2));
  await capture(page,'calculation-cycle-desktop');
});
test('five original events preserve removal and before-after quantities, then return to the visited sample window',async({page})=>{
  const calls=await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','7');
  await page.getByRole('button',{name:'관리 사건 보기',exact:true}).click();
  for(const offset of [0,2,4]){
    await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));await expect(page.locator('.coupled-canvas')).toHaveCount(0);
    const articles=page.locator('.cycle-events article');await expect(articles).toHaveCount(Math.min(2,5-offset));
    for(let i=0;i<Math.min(2,5-offset);i++){
      const event=base.events[offset+i]!,article=articles.nth(i);await expect(article).toContainText(event.at);
      for(const key of ['leaf','stem_root'] as const)await expect(article.locator(`[data-event-metric=${key}]`)).toHaveAttribute('data-raw-value',String(event.removed[key].value));
      for(const [n,state] of [event.removed,event.before,event.after].entries()){
        const rows=await article.locator('details').nth(n).locator('tbody tr').evaluateAll(rows=>rows.map(r=>[
          r.querySelector<HTMLElement>('[data-metric=carbon]')!.dataset.rawValue,r.querySelector<HTMLElement>('[data-metric=number]')!.dataset.rawValue]));
        expect(rows).toEqual(state.fruit_number.map((q,j)=>[String(state.fruit_carbohydrate[j]!.value),String(q.value)]));
      }
    }
    if(offset<4)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await page.getByRole('button',{name:'이전 저장 범위',exact:true}).click();await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','2');
  await page.getByRole('button',{name:'저장 시점 보기',exact:true}).click();await sameSample(page,7,7);
  expect(calls.map(c=>[c.kind,c.offset])).toEqual([['summary',0],['samples',0],['samples',7],['events',0],['events',2],['events',4],['events',2],['samples',7]]);
});
for(const name of ['short','past','fractional'] as const)test(name+' retains actual confirmed samples and separate hold diagnostics',async({page})=>{
  const data=dataset(name);await mock(page,data);await connect(page);await lookup(page,data);await sameSample(page,0,0,data);
  const hold=data.summary.summary.hold;
  if(hold){
    await expect(page.locator('.coupled-hold')).toContainText(hold.at);await expect(page.locator('.coupled-time-table')).not.toContainText(hold.at);
    if(hold.last_confirmed){
      await page.locator('.coupled-hold summary').click();await expect(page.locator('[data-confirmed-cumulative]')).toHaveCount(16);
      await expect(page.locator('[data-confirmed-startup-diagnostic]')).toHaveCount(4);
    }
    if(name==='past')await capture(page,'calculation-cycle-past-hold');
  }
});
for(const name of ['empty','zero'] as const)test(name+' has no invented endpoint, diagnostic or future frame',async({page})=>{
  const data=dataset(name);await mock(page,data);await connect(page);await lookup(page,data);
  await expect(page.locator('.cycle-no-samples')).toBeVisible();await expect(page.locator('.coupled-canvas')).toHaveCount(0);
  await expect(page.getByRole('slider')).toHaveCount(0);await expect(page.locator('.coupled-plot')).toHaveCount(0);
  expect(JSON.parse((await page.locator('.cycle-evidence pre').textContent())!)).toEqual({farm:data.summary.farm,reference:data.summary.reference,manifest:data.summary.summary.manifest});
  if(name==='empty'){await expect(page.locator('.coupled-hold')).toContainText(data.summary.summary.hold!.at);await capture(page,'calculation-cycle-empty-hold');}
});
for(const status of [403,422,503,'validation'] as const)test('current '+status+' refusal clears numeric state and autoplay',async({page})=>{
  await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);
  await page.getByRole('button',{name:'성장 자동 재생'}).click();await page.unroute(routePattern);
  await page.route(routePattern,route=>{
    if(status!=='validation')return route.fulfill({status,json:{error:{code:'own-synthetic-refusal',message:'own software test'}}});
    const value=base.rows.find(row=>row.page?.kind==='samples' && row.page.offset===7)!;
    return route.fulfill({json:{...value,reference:{...value.reference,input_validation:{...value.reference.input_validation,evidence_sha256:'a'.repeat(64)}}}});
  });
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await expect(page.getByRole('alert')).toBeVisible();
  for(const target of ['.coupled-canvas','.coupled-viewer','.coupled-plot','.cycle-range'])await expect(page.locator(target)).toHaveCount(0);
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-samples','0');
});
test('cancel waits out the old response without restoring a scene, and a fresh query recovers',async({page})=>{
  const reads=await observeReads(page);await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);await page.unroute(routePattern);
  let release!:()=>void,entered!:()=>void;const waiting=new Promise<void>(r=>{release=r;}),started=new Promise<void>(r=>{entered=r;});
  await page.route(routePattern,async route=>{entered();await waiting;
    await route.fulfill({json:base.rows.find(row=>row.page?.kind==='samples' && row.page.offset===7)}).catch(()=>{});
  });
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();await started;
  await expect(page.locator('.coupled-canvas')).toHaveCount(0);await page.getByRole('button',{name:'연구 조회 취소',exact:true}).click();release();
  await expect(page.getByRole('alert')).toContainText('취소');await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','idle');
  await page.unroute(routePattern);await mock(page);await lookup(page);await sameSample(page,0,0);
  await expect.poll(reads).toEqual({active:0,peak:1});
});
test('format, ID and account changes remove old scene, chart and playback state',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));await mock(page);await connect(page);await lookup(page);await sameSample(page,0,0);
  await page.getByRole('button',{name:'성장 자동 재생'}).click();await page.getByLabel('저장 결과 판본').selectOption('cycle');
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-source-kind','original');await expect(page.locator('.coupled-canvas')).toHaveCount(0);
  await expect(page.locator('.coupled-plot')).toHaveCount(0);await lookup(page);await sameSample(page,0,0);
  await page.getByText('저장 연구 결과 조회',{exact:true}).click();await page.getByLabel(labels.result_id,{exact:true}).fill(base.summary.result_id.slice(0,-1)+'0');
  await expect(page.locator('.coupled-canvas')).toHaveCount(0);await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','idle');
  await lookup(page);await sameSample(page,0,0);await page.getByLabel('접근 토큰').fill('own-synthetic-other-calculation-account');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('calculation-cycle');await expect(page.locator('.coupled-canvas')).toHaveCount(0);
  await expect(page.locator('.coupled-plot')).toHaveCount(0);expect(errors).toEqual([]);
});
test('mobile, keyboard, reduced motion and 200 percent text preserve exact HTML and same UTC',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.emulateMedia({reducedMotion:'reduce'});await mock(page);await connect(page);await lookup(page);
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');await sameSample(page,1,0);
  await expect(page.getByRole('button',{name:'성장 자동 재생'})).toBeDisabled();
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await capture(page,'calculation-cycle-mobile');
  await page.setViewportSize({width:780,height:844});await page.evaluate(()=>{document.documentElement.style.fontSize='200%';});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.getByRole('button',{name:'다음 저장 범위',exact:true}).focus();await page.keyboard.press('Enter');await sameSample(page,7,7);
});
