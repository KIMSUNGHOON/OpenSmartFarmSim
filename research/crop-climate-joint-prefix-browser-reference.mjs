import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const input=JSON.parse(readFileSync(process.argv[2],'utf8'));
const {chromium}=await import(pathToFileURL(input.playwright).href);
const token=JSON.parse(readFileSync(input.access_file,'utf8')).token;
const responses=[],errors=[],warnings=[],consoleErrors=[];
assert.equal(typeof global.gc,'function');let gcCalls=0;
const gcTimer=setInterval(()=>{global.gc();gcCalls++;},250);gcTimer.unref();
const digest=raw=>createHash('sha256').update(raw).digest('hex');
const save=(name,value)=>writeFileSync(join(input.directory,name),JSON.stringify(value),{flag:'wx',mode:0o400});
let phase='launch';const phases=[];
function progress(next){phase=next;phases.push({phase,at:new Date().toISOString()});
  writeFileSync(join(input.directory,'browser-live.private.json'),JSON.stringify({phase,phases,
    responses:responses.map(r=>({path:new URL(r.url).pathname,status:r.status,code:r.value.error?.code})),errors,consoleErrors}),{mode:0o600});}
const labels={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',
  registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
function bits(value,out=[]){
  if(typeof value==='number'){const raw=Buffer.alloc(8);raw.writeDoubleBE(value);out.push(raw.toString('hex'));}
  else if(Array.isArray(value))value.forEach(v=>bits(v,out));
  else if(value&&typeof value==='object')Object.values(value).forEach(v=>bits(v,out));
  return out;
}
async function until(read,check,timeout=45_000){
  const end=performance.now()+timeout;
  while(true){const value=await read();if(check(value))return value;
    assert(performance.now()<end,'browser observation timeout');await new Promise(resolve=>setTimeout(resolve,500));}
}
async function enter(page){
  progress('load-app');
  await page.goto(input.origin,{waitUntil:'networkidle'});
  progress('connect-token');
  await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  progress('open-growth');
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('joint-execution');
  progress('collect-startup-garbage');
  const cdp=await page.context().newCDPSession(page);
  try{await cdp.send('HeapProfiler.collectGarbage');}finally{await cdp.detach();}
}
async function reconnect(page,job){
  await enter(page);
  for(const [key,value] of Object.entries({job_id:job,...input.farm}))
    await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();
}
async function scene(page,selector){
  return page.evaluate(selector=>{
    const root=document.querySelector(selector),canvas=root?.querySelector('.coupled-canvas');
    if(!root||!canvas||Number(canvas.dataset.drawCalls)<=0)return null;
    const history=root.querySelector('.joint-history'),section=root.closest('.joint-prefix');
    if(!history?.querySelector('[data-values]'))return null;
    return {at:canvas.dataset.sceneAt,drawCalls:Number(canvas.dataset.drawCalls),
      cohorts:JSON.parse(canvas.dataset.cohortDrawing??'null'),leafArea:Number(canvas.dataset.leafSurfaceArea),
      temperatures:JSON.parse(canvas.dataset.temperatureDrawing??'null'),
      selected:root.dataset.selectedAt,chartAt:history?.dataset.selectedAt,chartValue:Number(history?.dataset.selectedValue),
      chartRaw:JSON.parse(history?.querySelector('[data-values]')?.dataset.values??'null'),
      values:Object.fromEntries([...root.querySelectorAll('.coupled-readout [data-metric]')].map(e=>[e.dataset.metric,Number(e.dataset.rawValue)])),
      carbon:[...root.querySelectorAll('.coupled-cohort-table [data-metric="carbon"]')].map(e=>Number(e.dataset.rawValue)),
      number:[...root.querySelectorAll('.coupled-cohort-table [data-metric="number"]')].map(e=>Number(e.dataset.rawValue)),
      selector:section?JSON.parse(section.dataset.prefixSelector):null,
      eventTimes:section?[...section.querySelectorAll('.cycle-events article h3')].map(e=>e.textContent.replace(' · UTC','')):[]};
  },selector);
}
function matches(drawing,records){
  const sample=records.find(r=>r.time.at===drawing.at);assert(sample,'scene must have an original sample');
  assert(drawing.drawCalls>0);assert.equal(drawing.selected,sample.time.at);assert.equal(drawing.chartAt,sample.time.at);
  const carbon=sample.value.cohort_state.fruit_carbohydrate.map(q=>q.value),number=sample.value.cohort_state.fruit_number.map(q=>q.value);
  assert.equal(carbon.length,50);assert.equal(number.length,50);
  assert.deepEqual(drawing.carbon,carbon);assert.deepEqual(drawing.number,number);
  assert.deepEqual(drawing.cohorts.carbon.map(q=>q.value),carbon);assert.deepEqual(drawing.cohorts.number.map(q=>q.value),number);
  for(const [name,quantity] of Object.entries({...sample.value.plant_state,...sample.value.climate_state,...sample.value.derived}))
    assert.equal(drawing.values[name],quantity.value,name);
  assert.equal(drawing.chartValue,sample.value.derived.leaf_area_index.value);
  assert.deepEqual(drawing.chartRaw,records.map(row=>row.value.derived.leaf_area_index.value));
  assert(Math.abs(drawing.leafArea-sample.value.derived.leaf_area_index.value)<=Math.max(1e-8,sample.value.derived.leaf_area_index.value*1e-6));
  assert.equal(drawing.temperatures.markers.find(m=>m.kind==='canopy').value,sample.value.derived.canopy_temperature.value);
  assert.equal(drawing.temperatures.markers.find(m=>m.kind==='air').value,sample.value.climate_state.air_temperature.value);
  return sample;
}
const browser=await chromium.launch({headless:true,args:['--enable-unsafe-swiftshader','--single-process',
  '--no-zygote','--js-flags=--max-old-space-size=32 --max-semi-space-size=1']});
let record,job,prefixSeen=[];
try{
  const context=await browser.newContext({viewport:{width:1024,height:768},deviceScaleFactor:0.5});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  page.on('console',message=>{if(message.type()==='error')consoleErrors.push(message.text());
    else if(message.type()==='warning')warnings.push(message.text());});
  await page.exposeBinding('__ossfObserveFetch',(_source,reply)=>{
    const raw=Buffer.from(reply.raw);assert(raw.length<=2*1024**2);assert(responses.length<150);
      writeFileSync(join(input.directory,'browser-'+String(responses.length).padStart(4,'0')+'.wire'),raw,{flag:'wx',mode:0o400});
    responses.push({url:reply.url,status:reply.status,sha256:digest(raw),bytes:raw.length,
      no_store:reply.no_store,value:JSON.parse(raw.toString('utf8'))});progress(phase);
  });
  await page.addInitScript(()=>{
    const original=globalThis.fetch.bind(globalThis);
    globalThis.fetch=async(...args)=>{
      const response=await original(...args);
      if(new URL(response.url).pathname.startsWith('/v1/')){
        void response.clone().arrayBuffer().then(raw=>{
          if(raw.byteLength>2*1024**2)throw Error('observer body too large');
          return globalThis.__ossfObserveFetch({url:response.url,status:response.status,
            no_store:response.headers.get('cache-control')==='no-store',raw:Array.from(new Uint8Array(raw))});
        }).catch(error=>console.error('owned response observation: '+String(error)));
      }
      return response;
    };
  });
  if(input.mode==='profile'){
    await reconnect(page,input.job_id);await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();
  }else{
    await enter(page);progress('choose-request');await page.getByLabel('검토된 계산 접수 파일').setInputFiles(input.request_file);
    progress('submit-request');
    await page.getByRole('button',{name:'계산 접수',exact:true}).click();
    progress('await-admission');
    const admitted=await until(()=>responses.find(r=>r.status===202&&r.url.endsWith('/crop-climate-joint-executions')),v=>Boolean(v));
    job=admitted.value.job_id;save('browser-job.private.json',{job_id:job});
    progress('observe-running');
    const end=performance.now()+240_000;let screenshot=false,cancelRequested=false;
    while(true){
      const drawing=await scene(page,'.joint-prefix-viewer');
      if(drawing&&drawing.cohorts&&!prefixSeen.some(v=>JSON.stringify(v.selector)===JSON.stringify(drawing.selector))){
        prefixSeen.push(drawing);
        if(!screenshot){await page.locator('.joint-prefix .coupled-top-grid').scrollIntoViewIfNeeded();
          await page.screenshot({path:join(input.directory,'running-prefix.png')});screenshot=true;}
      }
      if(input.mode==='live-cancel'&&prefixSeen.length&&!cancelRequested){
        await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();cancelRequested=true;
        assert.equal(await page.locator('.joint-prefix').count(),0);
      }
      if(input.mode==='live-cancel'){
        if(await page.getByRole('heading',{name:'취소됨',exact:true}).count())break;
      }else if(await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).count())break;
      assert(performance.now()<end,'actual running/terminal observation timeout');await new Promise(resolve=>setTimeout(resolve,500));
    }
    assert(prefixSeen.length>0,'must observe an actual running prefix WebGL scene');
    for(const drawing of prefixSeen){
      const same=r=>JSON.stringify(r.value.reference?.selector)===JSON.stringify(drawing.selector);
      const samplePage=responses.find(r=>r.status===200&&r.value.page?.kind==='samples'&&same(r)&&r.url.includes('/prefix/'));
      const eventPage=responses.find(r=>r.status===200&&r.value.page?.kind==='events'&&same(r)&&r.url.includes('/prefix/'));
      assert(samplePage&&eventPage,'same-selector original sample and event prefix200 required');
      assert(['queued','simulating'].includes(samplePage.value.job.state));matches(drawing,samplePage.value.page.records);
      assert.deepEqual(drawing.eventTimes,eventPage.value.page.records.map(r=>r.time.at));
    }
    if(input.mode==='live-cancel'){
      assert.equal(await page.locator('.joint-prefix').count(),0);
      assert.equal(await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).count(),0);
      record={mode:input.mode,job_id:job,running_prefixes:prefixSeen,canceled:true,terminal_result_created:false};
    }else{
      assert.equal(await page.locator('.joint-prefix').count(),0);
      await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();
    }
  }
  if(input.mode!=='live-cancel'){
    const drawing=await until(()=>scene(page,'.joint-viewer'),v=>Boolean(v?.cohorts));
    const pages=responses.filter(r=>r.status===200&&r.value.page?.kind==='samples'&&!r.url.includes('/prefix/'));
    assert(pages.length);const sample=matches(drawing,pages.at(-1).value.page.records);
    const finalEvents=responses.findLast(r=>r.status===200&&r.value.page?.kind==='events'&&!r.url.includes('/prefix/'));
    assert(finalEvents);
    for(const prior of responses.filter(r=>r.status===200&&r.url.includes('/prefix/')&&r.value.page)){
      const originals=prior.value.page.kind==='samples'?pages.at(-1).value.page.records:finalEvents.value.page.records;
      for(const row of prior.value.page.records){const final=originals.find(v=>v.time.step_index===row.time.step_index);
        assert.deepEqual(row,final);assert.deepEqual(bits(row),bits(final));}
    }
    const terminal=responses.findLast(r=>r.status===200&&r.value.checkpoint?.status===
      (input.mode==='live-hold'?'hold':'completed')&&r.value.result!=null);assert(terminal);
    const storedID=await page.locator('.joint-viewer').getAttribute('data-result-id');
    await page.locator('.joint-viewer .coupled-top-grid').scrollIntoViewIfNeeded();await page.screenshot({path:join(input.directory,'terminal.png')});
    if(input.mode!=='profile'){
      await reconnect(page,job);await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();
      const reopened=await until(()=>scene(page,'.joint-viewer'),v=>Boolean(v?.cohorts));
      assert.equal(await page.locator('.joint-viewer').getAttribute('data-result-id'),storedID);matches(reopened,pages.at(-1).value.page.records);
    }
    record={mode:input.mode,job_id:job??input.job_id,running_prefixes:prefixSeen,stored_result_id:storedID,
      terminal_status:terminal.value.checkpoint.status,selected_UTC:sample.time.at,original_prefix_rows_equal_terminal:true,
      original_binary64_and_UTC_preserved:true,reconnect:input.mode!=='profile',actual_WebGL_draw_calls:drawing.drawCalls,cohorts:50};
  }
  assert.deepEqual(errors,[]);assert(responses.every(r=>r.no_store));
  assert(responses.every(r=>[200,202,409,503].includes(r.status)));
  assert(warnings.every(text=>text.includes('GL Driver Message')&&text.includes('GPU stall due to ReadPixels')));
  assert(consoleErrors.every(text=>/Failed to load resource.*(?:409|503)/.test(text)));
  record={...record,console_errors:errors,expected_transient_console_errors:consoleErrors,driver_warnings:warnings,
    viewport:{width:1024,height:768,deviceScaleFactor:0.5},running_prefix_acceptance:input.mode!=='profile',test_checkpoint_pause:false,
    owned_Node_gc_250ms_calls:gcCalls,response_capture:'actual_fetch_Response_clone_bytes',API_mocking:false};
  progress('accepted-case');await context.close();
}finally{
  await browser.close();save('browser-responses.private.json',responses);
  save('browser-observation.private.json',record??{mode:input.mode,job_id:job,running_prefixes:prefixSeen,console_errors:errors,
    console_resource_errors:consoleErrors,warnings,accepted:false});
  save('browser-phases.private.json',phases);
}
clearInterval(gcTimer);
console.log(JSON.stringify(record));
