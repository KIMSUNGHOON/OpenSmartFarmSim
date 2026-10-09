// Actual owned DB/HTTPS App; no routes, response substitutions or crop calculation.
import {createInterface} from 'node:readline';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium,expect as assertions} from '@playwright/test';
const expect=assertions.configure({timeout:40_000}),input=createInterface({input:process.stdin}),lines=input[Symbol.asyncIterator]();
async function next(stage){const r=await lines.next();if(r.done)throw Error('owned native protocol ended');const v=JSON.parse(r.value);if(stage)expect(v.stage).toBe(stage);return v;}
const config=await next(),data=config.data,origin=process.argv[2],screens=process.argv[3];
const sampleByIndex=new Map(Object.entries(data.pages).flatMap(([offset,rows])=>rows.map((row,i)=>[Number(offset)+i,row])));
await mkdir(screens,{recursive:true});
const args=['--enable-unsafe-swiftshader','--no-zygote','--in-process-gpu','--single-process','--js-flags=--max-old-space-size=32 --max-semi-space-size=1','--num-raster-threads=1','--disable-gpu-shader-disk-cache'];
const browser=await chromium.launch({args}),context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1024,height:768}});
const page=await context.newPage(),network=[],errors=[],samples=new Set(),verified=[],collections=[];
page.on('pageerror',e=>errors.push(e.message));
await page.exposeFunction('__ownedHarvestSettled',row=>network.push(row));
await page.addInitScript(()=>{
  let active=0,peak=0;const original=globalThis.fetch.bind(globalThis);
  globalThis.fetch=async(...args)=>{
    const u=new URL(args[0] instanceof Request?args[0].url:String(args[0]),location.href);
    const endpoint=u.pathname.startsWith('/v1/crop-harvest-research-results/')?'harvest':
      u.pathname.startsWith('/v1/crop-cycle-calculation-research-results/')?'crop':null;
    if(!endpoint)return original(...args);
    const row={endpoint,view:u.searchParams.get('view'),offset:u.searchParams.get('offset'),status:null,
      bytes:0,complete:false,outcome:null,body_sha256:null,cache:null},chunks=[],started=performance.now();
    active++;peak=Math.max(peak,active);let settled=false;
    async function settle(outcome){
      if(settled)return;settled=true;active--;row.outcome=outcome;row.complete=outcome==='complete';
      row.seconds=(performance.now()-started)/1000;
      if(row.complete){const bytes=new Uint8Array(row.bytes);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
        row.body_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');}
      await globalThis.__ownedHarvestSettled(row);
    }
    try{
      const response=await original(...args);row.status=response.status;row.cache=response.headers.get('cache-control');
      if(!response.ok||!response.body){await settle('headers');return response;}
      const body=response.body,getReader=body.getReader.bind(body);
      Object.defineProperty(body,'getReader',{value:(...a)=>{
        const reader=getReader(...a),read=reader.read.bind(reader),cancel=reader.cancel.bind(reader);
        Object.defineProperty(reader,'read',{value:async(...a)=>{try{const r=await read(...a);
          if(r.done)await settle('complete');else{row.bytes+=r.value.byteLength;chunks.push(r.value.slice());}return r;
        }catch(error){await settle('read-error');throw error;}}});
        Object.defineProperty(reader,'cancel',{value:async(...a)=>{try{return await cancel(...a);}finally{await settle('canceled');}}});
        return reader;
      }});return response;
    }catch(error){await settle('fetch-error');throw error;}
  };
  globalThis.__ownedHarvestReads=()=>({active,peak});
});
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const panel=page.locator('.harvest-replay'),cdp=await context.newCDPSession(page);
await cdp.send('Performance.enable');
let collecting=false;const gcTimer=setInterval(async()=>{if(collecting)return;collecting=true;try{await cdp.send('HeapProfiler.collectGarbage');}catch{}finally{collecting=false;}},250);gcTimer.unref();
async function stage(name){await writeFile(screens+'/harvest-native-stage.json',JSON.stringify({stage:name,
  network,verified,node_memory_bytes:process.memoryUsage(),viewport:await page.evaluate(()=>({width:innerWidth,
    document_scroll_width:document.documentElement.scrollWidth}))}),{mode:0o600});}
async function idle(){await expect.poll(()=>page.evaluate(()=>globalThis.__ownedHarvestReads().active)).toBe(0);}
async function collect(phase){
  const metrics=async()=>Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics
    .filter(m=>['JSHeapUsedSize','JSHeapTotalSize','Nodes','Documents'].includes(m.name)).map(m=>[m.name,m.value]));
  const before=await metrics();await cdp.send('HeapProfiler.collectGarbage');globalThis.gc();
  collections.push({phase,method:'HeapProfiler.collectGarbage_and_owned_Node_gc',before,after:await metrics()});
  await writeFile(screens+'/harvest-native-collections.json',JSON.stringify(collections),{mode:0o600});
}
async function connect(token){
  if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
}
async function submitCrop(){
  await page.getByLabel('저장 결과 판본').selectOption('calculation-cycle');
  if(await page.locator('.crop-lookup').getAttribute('open')===null)await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:data.summary.result_id,...data.summary.farm}))
    await page.getByLabel(labels[key],{exact:true}).fill(String(value));
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function readCrop(){await stage('crop_lookup');await submitCrop();await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','ready');await idle();await collect('crop_loaded_before_harvest');await stage('crop_ready');}
async function readHarvest(){
  await stage('harvest_lookup');
  await page.getByLabel('저장 수확 결과 ID').fill(data.harvest_result_id);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();await expect(panel).toHaveAttribute('data-phase','ready');await idle();
  await collect('harvest_loaded_before_row_checks');await stage('harvest_ready');
}
async function sample(index){
  const row=sampleByIndex.get(index),canvas=page.locator('.coupled-canvas');expect(row).toBeDefined();
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-at',row.at);
  await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  const drawing=JSON.parse(await canvas.getAttribute('data-cohort-drawing'));
  for(const [kind,key] of [['carbon','fruit_carbohydrate'],['number','fruit_number']]){
    expect(drawing[kind].map(q=>q.value)).toEqual(row.state[key].map(q=>q.value));
    expect(drawing[kind].map(q=>q.unit)).toEqual(row.state[key].map(q=>q.unit));
  }
  expect(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  expect(await canvas.evaluate(c=>{const gl=c.getContext('webgl2');return !!gl&&!gl.isContextLost();})).toBe(true);samples.add(index);
}
async function rows(offset){
  await expect(panel).toHaveAttribute('data-offset',String(offset));await expect(panel).toHaveAttribute('data-count','3');
  await expect(panel).toHaveAttribute('data-total','47813');
  await expect(panel.getByText('부분 범위',{exact:true})).toBeVisible();
  for(let index=offset;index<offset+3;index++){
    const row=data.rows[index],tr=panel.locator('[data-harvest-index="'+index+'"]');
    await expect(tr).toHaveAttribute('data-end-at',row.mass.removal.end_at);
    for(const [selector,q] of [['[data-original-fresh]',row.mass.fresh_matter],['[data-unassigned-fresh]',row.unassigned.quantities.fresh_matter]]){
      await expect(tr.locator(selector)).toHaveAttribute('data-raw-value',String(q.value));await expect(tr.locator(selector)).toHaveAttribute('data-unit',q.unit);
    }
    const quantities=await tr.locator('li [data-raw-value]').evaluateAll(items=>items.map(el=>({value:el.dataset.rawValue,unit:el.dataset.unit})));
    expect(quantities).toEqual(row.allocations.map(a=>({value:String(a.quantities.fresh_matter.value),unit:a.quantities.fresh_matter.unit})));
    await tr.getByText('원 수량·정확 분수',{exact:true}).click();
    expect(JSON.parse(await tr.locator('pre').textContent())).toEqual({carbohydrate:row.mass.removal.carbohydrate,
      number:row.mass.removal.number,dry_matter:row.mass.dry_matter,fresh_matter:row.mass.fresh_matter,
      allocations:row.allocations,unassigned:row.unassigned});
    await tr.getByText('원 수량·정확 분수',{exact:true}).click();
    const frame=data.pages['0'].findIndex(s=>s.at===row.mass.removal.end_at),button=tr.getByRole('button',{name:'생장 시점 보기',exact:true});
    if(frame<0){await expect(button).toBeDisabled();await expect(tr).toContainText('현재 생장 범위에 대응 시점 없음');}
    else{await button.focus();await button.press('Enter');await sample(frame);await expect(page.locator('.coupled-viewer')).toBeFocused();}
    verified.push({index,row_id:row.row_id,at:row.mass.removal.end_at,sample_index:frame<0?null:frame});
    await stage('row_'+index+'_verified');
  }
}
async function cleared(){await expect(page.locator('.harvest-replay,.coupled-canvas,.coupled-viewer,.coupled-plot')).toHaveCount(0);await idle();}
const events=[];
async function extraFramesAndEvents(){
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.press('Home');await sample(0);
  for(let i=1;i<7;i++){await slider.press('ArrowRight');await sample(i);}
  await page.getByLabel('원 저장 시점 번호',{exact:true}).fill('23905');
  await page.getByRole('button',{name:'저장 시점으로 이동',exact:true}).click();
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','23904');await idle();await sample(23904);
  await page.getByRole('slider',{name:'저장 성장 시점 선택'}).press('End');await sample(23910);await collect('middle_frame');
  await page.getByRole('button',{name:'마지막 저장 시점',exact:true}).click();
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset','47808');await idle();await sample(47808);
  await readHarvest();
  await expect(panel.locator('[data-frame-status=outside_loaded_samples]')).toHaveCount(3);
  await page.locator('.coupled-scene').scrollIntoViewIfNeeded();await page.screenshot({path:screens+'/harvest-full-last-growth.png',mask:[page.getByLabel('접근 토큰')]});
  await page.getByRole('button',{name:'관리 사건 보기',exact:true}).click();let offset=0;
  while(offset<data.events.length){
    await expect(page.locator('.cycle-range')).toHaveAttribute('data-kind','events');
    await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));await idle();
    const articles=page.locator('.cycle-events article'),count=await articles.count();expect(count).toBe(Math.min(2,data.events.length-offset));
    for(let i=0;i<count;i++){
      const row=data.events[offset+i],article=articles.nth(i);await expect(article).toContainText(row.at);
      for(const key of ['leaf','stem_root'])await expect(article.locator('[data-event-metric='+key+']')).toHaveAttribute('data-raw-value',String(row.removed[key].value));
      const tables=article.locator('.coupled-diagnostic-table');expect(await tables.count()).toBe(3);
      for(const [position,kind] of ['removed','before','after'].entries()){
        const values=await tables.nth(position).locator('tbody tr').evaluateAll(rows=>rows.map(r=>[r.querySelector('[data-metric=carbon]').dataset.rawValue,r.querySelector('[data-metric=number]').dataset.rawValue]));
        expect(values).toEqual(row[kind].fruit_number.map((q,j)=>[String(row[kind].fruit_carbohydrate[j].value),String(q.value)]));
      }
      events.push({index:offset+i,at:row.at,original_C_N_states_verified:3});
    }
    const nextOffset=await page.locator('.cycle-range').getAttribute('data-next-offset');if(!nextOffset)break;
    offset=Number(nextOffset);await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await readHarvest();await collect('management_events');
}
const send=stage=>process.stdout.write(JSON.stringify({stage})+'\n');
try{
  await page.goto(origin);
  expect(data.summary.reference.sample_count).toBe(47809);expect(data.whole_summary.row_count).toBe(47813);
  const scripts=await page.evaluate(()=>Array.from(document.scripts).map(s=>s.src).filter(Boolean));
  expect(scripts.length).toBeGreaterThan(0);expect(scripts.every(s=>new URL(s).pathname.startsWith('/assets/'))).toBe(true);
  await connect(config.tokens.owner);await readCrop();await sample(0);await readHarvest();await rows(0);
  await collect('first_rows_before_next_API');await stage('next_harvest_page');
  await page.getByRole('button',{name:'다음 수확 범위',exact:true}).click();await expect(panel).toHaveAttribute('data-phase','ready');await idle();await rows(3);
  await panel.getByText('전체 저장 배정 합계',{exact:true}).click();await expect(panel.locator('[data-whole-summary]')).toHaveAttribute('data-row-count','47813');
  const totals=await panel.locator('.harvest-whole [data-raw-value]').evaluateAll(items=>items.map(e=>({value:e.dataset.rawValue,unit:e.dataset.unit})));
  expect(totals).toEqual(['model_terminal_outflow','explicit_fruit_removal'].flatMap(kind=>
    ['harvest','thinning','disposal','sampling','unassigned'].map(purpose=>{
      const q=data.whole_summary.totals_by_kind_and_purpose[kind][purpose].quantities.fresh_matter;return {value:String(q.value),unit:q.unit};})));
  await panel.getByText('전체 저장 배정 합계',{exact:true}).click();
  await panel.getByText('합성 관측 비교',{exact:true}).click();
  for(const c of data.whole_summary.observation_comparisons)
    await expect(panel.locator('[data-comparison-status="'+c.status+'"]')).toHaveCount(data.whole_summary.observation_comparisons.filter(v=>v.status===c.status).length);
  await panel.getByText('합성 관측 비교',{exact:true}).click();
  await expect(panel).toContainText('합성 환산');await expect(panel).toContainText('관문 미평가');
  await collect('before_captures');
  if(await page.locator('.connection').getAttribute('open')!==null)await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.locator('.coupled-scene').scrollIntoViewIfNeeded();await page.screenshot({path:screens+'/harvest-native-3d-desktop.png',mask:[page.getByLabel('접근 토큰')]});
  await panel.screenshot({path:screens+'/harvest-native-table-desktop.png'});
  await page.setViewportSize({width:390,height:844});await stage('mobile_viewport_requested');
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await stage('mobile_layout_stable');
  await panel.screenshot({path:screens+'/harvest-native-table-mobile.png'});
  await page.setViewportSize({width:1024,height:768});await collect('after_captures');await extraFramesAndEvents();await idle();send('geometry_verified');
  await next('rights_revoked');await page.getByRole('button',{name:'수확 권리 다시 조회',exact:true}).click();
  await expect(page.locator('.cycle-replay [role=alert]')).toBeVisible();await cleared();send('rights_denied');
  await next('rights_restored');await readCrop();await readHarvest();await sample(0);send('restored_verified');
  await next('hold_next_summary');await page.getByRole('button',{name:'수확 권리 다시 조회',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>globalThis.__ownedHarvestReads().active)).toBe(1);send('held_request_started');
  await next('cancel_now');await page.getByRole('button',{name:'수확 조회 취소',exact:true}).click();
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);await connect(config.tokens.denied);await cleared();send('canceled_account_changed');
  await next('old_request_settled');await cleared();
  const denied=await page.evaluate(async({id,farm,token})=>{
    const url='/v1/crop-harvest-research-results/'+encodeURIComponent(id)+'?'+new URLSearchParams({...farm,view:'summary'});
    const response=await fetch(url,{headers:{Authorization:'Bearer '+token}});await response.text();return response.status;
  },{id:data.harvest_result_id,farm:data.summary.farm,token:config.tokens.denied});expect(denied).toBe(403);await idle();
  const foreign=await page.evaluate(async({id,farm,token})=>{
    const url='/v1/crop-harvest-research-results/'+encodeURIComponent(id)+'?'+new URLSearchParams({...farm,view:'summary'});
    const response=await fetch(url,{headers:{Authorization:'Bearer '+token}});await response.text();return response.status;
  },{id:data.harvest_result_id,farm:data.summary.farm,token:config.tokens.foreign});expect(foreign).toBe(404);await idle();
  await submitCrop();await expect(page.locator('.cycle-replay [role=alert]')).toBeVisible();await cleared();
  expect(errors).toEqual([]);const peak=await page.evaluate(()=>globalThis.__ownedHarvestReads().peak);expect(peak).toBe(1);
  expect(network.filter(r=>r.status===200).every(r=>r.complete&&r.bytes<=2*1024*1024&&r.cache==='no-store')).toBe(true);
  process.stdout.write(JSON.stringify({stage:'verified',verified_rows:verified.length,verified,
    verified_sample_indices:[...samples].sort((a,b)=>a-b),verified_events:events,actual_WebGL:true,same_UTC:true,network,errors,peak_active_reads:peak,
    current_rights_revoked_restored:true,canceled_late_request_then_account_change_no_old_restore:true,
    direct_denied_harvest_status:denied,direct_foreign_harvest_status:foreign,denied_crop_UI:true,source_response_replacement:false,full_row_count:47813,partial_browser_harvest_rows:6,
    production_scripts:scripts,browser_launch_args:args,explicit_collections:collections,unmounted:true,
    scope:'owned_synthetic_same_DB_actual_API_WebGL_not_agricultural_validation'})+'\n');
}catch(error){
  let message=String(error.stack??error);for(const token of Object.values(config.tokens))message=message.replaceAll(token,'[REDACTED_OWNED_TOKEN]');
  await writeFile(screens+'/harvest-native-failure.json',JSON.stringify({message,network,errors,verified,accepted:false},null,2),{mode:0o600});
  process.stderr.write(message+'\n');process.exitCode=1;
  await collect('failure_before_viewport_capture').catch(()=>{});
  await page.screenshot({path:screens+'/harvest-native-failure.png',mask:[page.getByLabel('접근 토큰')]}).catch(()=>{});
}finally{clearInterval(gcTimer);await context.close();await browser.close();input.close();process.stdin.destroy();}
