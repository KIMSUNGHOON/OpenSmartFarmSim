// Manual native proof. Only own synthetic public data leave this isolated browser.
import { createInterface } from 'node:readline';
import { mkdir, writeFile } from 'node:fs/promises';
import { chromium, expect as assertions } from '@playwright/test';
const expect = assertions.configure({timeout:40_000});
const lines = createInterface({input:process.stdin})[Symbol.asyncIterator]();
async function next(){const line=await lines.next();if(line.done)throw new Error('native protocol ended');return JSON.parse(line.value);}
const config=await next(),origin=process.argv[2],screens=process.argv[3];await mkdir(screens,{recursive:true});
const calculation=config.format==='calculation-cycle',format=calculation?'calculation-cycle':'cycle';
const resultPath=calculation?'/v1/crop-cycle-calculation-research-results/':'/v1/crop-cycle-research-results/';
const capturePrefix=calculation?'calculation-cycle-native':'cycle-native';
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1536,height:1024}});
const page=await context.newPage(),network=[],errors=[],windows=[],verified=[],eventsVerified=[];
page.on('pageerror',e=>errors.push(e.message));
const consoleMessages=[];page.on('console',message=>{if(['error','warning'].includes(message.type()))consoleMessages.push({type:message.type(),text:message.text()});});
let fixtureRights=true,fixtureTampered=false;
if(config.transport==='own-recorded-response-fixture')await page.route('**'+resultPath+'**',async route=>{
  const url=new URL(route.request().url()),data=Object.values(config.results).find(item=>decodeURIComponent(url.pathname).endsWith(item.summary.result_id));
  const status=route.request().headers().authorization==='Bearer '+config.tokens.denied?403:fixtureRights && !fixtureTampered?200:422;
  if(status!==200)return route.fulfill({status,json:{error:{code:'own-fixture-denial',message:'own synthetic test'}}});
  if(!data)throw new Error('unknown own fixture result');
  const kind=url.searchParams.get('view');let value=data.summary;
  if(kind!=='summary'){
    const offset=Number(url.searchParams.get('offset')),limit=Number(url.searchParams.get('limit')),rows=data[kind],next=Math.min(offset+limit,rows.length);
    value={...data.summary,summary:null,page:{kind,offset,limit,total:rows.length,next_offset:next<rows.length?next:null,records:rows.slice(offset,next)}};
  }
  return route.fulfill({json:value,headers:{'cache-control':'no-store'}});
});
await page.exposeFunction('__cycleReadSettled',item=>network.push(item));
await page.addInitScript(({resultPath})=>{
  // Weak references and integer counters avoid keeping disposed DOM/GPU objects alive.
  const objects=new WeakMap(),callbacks=new WeakMap();let serial=0;
  function id(map,value){if(!map.has(value))map.set(value,++serial);return map.get(value);}
  const observers=new Map(),listeners=new Map(),timers=new Map(),frames=new Map(),contexts=[],charts=[];
  let activeReads=0,maxActiveReads=0;
  const root=()=>document.querySelector('.cycle-replay');
  const stack=()=>new Error().stack??'';
  const cropCode=s=>/\/src\/(CycleCropReplay|CoupledCropScene|CoupledCropChart)\./.test(s);
  const nativeObserver=globalThis.ResizeObserver;
  globalThis.ResizeObserver=class extends nativeObserver{
    observe(target,options){
      if(target.closest?.('.cycle-replay'))observers.set(id(objects,this),{observer:new WeakRef(this),target:new WeakRef(target)});
      return super.observe(target,options);
    }
    unobserve(target){observers.delete(id(objects,this));return super.unobserve(target);}
    disconnect(){observers.delete(id(objects,this));return super.disconnect();}
  };
  const add=EventTarget.prototype.addEventListener,remove=EventTarget.prototype.removeEventListener;
  const capture=options=>typeof options==='boolean'?options:!!options?.capture;
  function listenerKey(target,type,callback,options){return `${id(objects,target)}:${type}:${id(callbacks,callback)}:${capture(options)}`;}
  EventTarget.prototype.addEventListener=function(type,callback,options){
    if(callback && (typeof callback==='object' || typeof callback==='function')){
      const s=stack(),local=this instanceof Element && !!this.closest('.cycle-replay .coupled-canvas,.cycle-replay .coupled-plot');
      const globalTarget=this===document || this===globalThis || this instanceof MediaQueryList;
      const caller=s.split('\n')[3]??'',automation=/InjectedScript|HitTargetInterceptor|__playwright/.test(s.split('\n').slice(0,6).join('\n'));
      if((local || globalTarget && root()) && !automation && !/react-dom|addEventBubbleListener|addEventCaptureListener/.test(caller))
        listeners.set(listenerKey(this,type,callback,options),{target:new WeakRef(this),callback:new WeakRef(callback),type,source:s.split('\n').slice(1,5)});
    }
    return add.call(this,type,callback,options);
  };
  EventTarget.prototype.removeEventListener=function(type,callback,options){
    if(callback && (typeof callback==='object' || typeof callback==='function'))listeners.delete(listenerKey(this,type,callback,options));
    return remove.call(this,type,callback,options);
  };
  const timeout=globalThis.setTimeout.bind(globalThis),clear=globalThis.clearTimeout.bind(globalThis);
  globalThis.setTimeout=(callback,delay,...args)=>{
    const owned=!!root() && (cropCode(stack()) || /\/src\/api\./.test(stack()));
    let key;key=timeout((...values)=>{timers.delete(key);callback(...values);},delay,...args);
    if(owned)timers.set(key,delay);return key;
  };
  globalThis.clearTimeout=key=>{timers.delete(key);clear(key);};
  const request=globalThis.requestAnimationFrame.bind(globalThis),cancel=globalThis.cancelAnimationFrame.bind(globalThis);
  globalThis.requestAnimationFrame=callback=>{
    const owned=cropCode(stack());let key;key=request(at=>{frames.delete(key);callback(at);});if(owned)frames.set(key,true);return key;
  };
  globalThis.cancelAnimationFrame=key=>{frames.delete(key);cancel(key);};
  const getContext=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(kind,...args){
    const gl=getContext.call(this,kind,...args);
    if(kind==='webgl2' && gl && this.closest('.cycle-replay') && !contexts.some(c=>c.gl.deref()===gl)){
      const data={gl:new WeakRef(gl),canvas:new WeakRef(this),created:{},deleted:{},live:{}};contexts.push(data);
      for(const kind of ['Buffer','Texture','Program','Shader','Framebuffer','Renderbuffer','VertexArray']){
        const make=gl['create'+kind].bind(gl),drop=gl['delete'+kind].bind(gl),ids=new WeakMap(),live=new Set();
        data.live[kind]=live;data.created[kind]=data.deleted[kind]=0;
        gl['create'+kind]=(...a)=>{const value=make(...a);if(value){ids.set(value,++serial);live.add(ids.get(value));data.created[kind]++;}return value;};
        gl['delete'+kind]=value=>{if(value && live.delete(ids.get(value)))data.deleted[kind]++;return drop(value);};
      }
    }
    return gl;
  };
  const fetch=globalThis.fetch.bind(globalThis);
  globalThis.fetch=async(...args)=>{
    const url=new URL(args[0] instanceof Request?args[0].url:String(args[0]),location.href);
    if(!url.pathname.startsWith(resultPath))return fetch(...args);
    const began=performance.now(),item={view:url.searchParams.get('view'),offset:url.searchParams.get('offset'),limit:url.searchParams.get('limit'),
      method:args[1]?.method??'GET',status:null,cache:null,bytes:0,seconds:0,outcome:null};
    activeReads++;maxActiveReads=Math.max(maxActiveReads,activeReads);let settled=false;
    async function settle(outcome){if(settled)return;settled=true;activeReads--;item.outcome=outcome;item.seconds=(performance.now()-began)/1000;await globalThis.__cycleReadSettled(item);}
    try{
      const response=await fetch(...args);item.status=response.status;item.cache=response.headers.get('cache-control');
      if(!response.ok || !response.body){await settle('headers');return response;}
      const body=response.body,getReader=body.getReader.bind(body);
      Object.defineProperty(body,'getReader',{value:(...a)=>{
        const reader=getReader(...a),read=reader.read.bind(reader),cancel=reader.cancel.bind(reader);
        Object.defineProperty(reader,'read',{value:async(...r)=>{try{const value=await read(...r);
          if(value.done)await settle('complete');else item.bytes+=value.value.byteLength;return value;
        }catch(e){await settle('read-error');throw e;}}});
        Object.defineProperty(reader,'cancel',{value:async(...r)=>{try{return await cancel(...r);}finally{await settle('canceled');}}});
        return reader;
      }});return response;
    }catch(e){await settle('fetch-error');throw e;}
  };
  globalThis.__cycleLifecycle=()=>{
    for(const element of document.querySelectorAll('.cycle-replay .coupled-plot')){
      const chartId=element.getAttribute('_echarts_instance_');
      if(chartId && !charts.some(c=>c.id===chartId))charts.push({id:chartId,element:new WeakRef(element)});
    }
    const gpu=contexts.map(c=>({connected:!!c.canvas.deref()?.isConnected,context_alive:!!c.gl.deref(),context_lost:!!c.gl.deref()?.isContextLost(),
      created:c.created,deleted:c.deleted,live:c.gl.deref()?Object.fromEntries(Object.entries(c.live).map(([k,v])=>[k,v.size])):{}}));
    return {active_reads:activeReads,max_active_reads:maxActiveReads,timers:timers.size,frames:frames.size,
      observers:[...observers.values()].filter(o=>o.observer.deref()).length,
      listeners:[...listeners.values()].filter(l=>l.target.deref() && l.callback.deref()).map(l=>({type:l.type,target:l.target.deref().constructor.name,
        connected:l.target.deref() instanceof Node?l.target.deref().isConnected:null,source:l.source})),gpu,
      charts:charts.map(c=>({id:c.id,connected:!!c.element.deref()?.isConnected,instance:c.element.deref()?.getAttribute('_echarts_instance_')??null})),
      canvas_count:document.querySelectorAll('.cycle-replay .coupled-canvas').length,
      plot_count:document.querySelectorAll('.cycle-replay .coupled-plot').length};
  };
},{resultPath});
const cdp=await context.newCDPSession(page);await cdp.send('Performance.enable');
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const lifecycle={scope:'instrumented_current_scene_and_chart_GPU_DOM_observer_listener_crop_timer_RAF_request_cleanup_GC_eligibility_not_driver_memory',transitions:[]};
async function probe(){return page.evaluate(()=>globalThis.__cycleLifecycle());}
async function collected(){await cdp.send('HeapProfiler.collectGarbage');return probe();}
async function ready(data,offset=0){
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-result-id',data.summary.result_id);
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','ready');
}
async function connect(token){
  if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();await page.getByLabel('저장 결과 판본').selectOption(format);
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-source-kind',calculation?'calculation':'original');
}
async function lookup(data){
  if(!await page.getByLabel(labels.result_id,{exact:true}).isVisible())await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:data.summary.result_id,...data.summary.farm}))await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
function bounds(samples,kind){
  const values=samples.flatMap(s=>s.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'].map(q=>q.value)).filter(v=>v>0);
  if(!values.length)return null;
  const upper=Math.ceil(Math.log10(Math.max(...values)));
  return {lower:Math.floor(Math.log10(Math.min(...values)))-1,upper:Object.is(upper,-0)?0:upper};
}
async function sample(data,index,offset){
  const row=data.samples[index],canvas=page.locator('.coupled-canvas');
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-result-id',data.summary.result_id);
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-index',String(index));
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-farm',JSON.stringify(data.summary.farm));
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-reference',JSON.stringify(data.summary.reference));
  for(const target of ['.coupled-viewer','.coupled-readout','.coupled-scene','.coupled-cohorts','.coupled-history','.coupled-distribution'])
    await expect(page.locator(target)).toHaveAttribute('data-selected-at',row.at);
  const rows=await page.locator('.coupled-cohort-table tbody tr').evaluateAll(rows=>rows.map(r=>[
    r.querySelector('[data-metric=carbon]').dataset.rawValue,r.querySelector('[data-metric=number]').dataset.rawValue]));
  expect(rows).toEqual(row.state.fruit_number.map((q,i)=>[String(row.state.fruit_carbohydrate[i].value),String(q.value)]));
  for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'])
    await expect(page.locator('.coupled-readout [data-metric='+key+']')).toHaveAttribute('data-raw-value',String(row.state[key].value));
  for(const key of ['lai','fruit_carbohydrate_total'])
    await expect(page.locator('.coupled-readout [data-metric='+key+']')).toHaveAttribute('data-raw-value',String(row[key].value));
  await page.locator('.crop-cumulative>summary').click();
  const raw=await page.locator('.crop-cumulative [data-cumulative],.crop-cumulative [data-startup-diagnostic],.crop-cumulative [data-balance]').evaluateAll(items=>items.map(e=>({
    key:e.dataset.cumulative??e.dataset.startupDiagnostic??e.dataset.balance,value:e.dataset.rawValue})));
  const expectedFlows=[...Object.entries(row.cumulative),...Object.entries(row.startup_diagnostics),
    ...['carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'].map(k=>[k,row[k]])].map(([key,q])=>({key,value:String(q.value)}));
  expect(raw.sort((a,b)=>a.key.localeCompare(b.key))).toEqual(expectedFlows.sort((a,b)=>a.key.localeCompare(b.key)));
  await page.locator('.crop-cumulative>summary').click();await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  const drawing=JSON.parse(await canvas.getAttribute('data-cohort-drawing'));
  const count=Number(await page.locator('.cycle-range').getAttribute('data-count')),current=data.samples.slice(offset,offset+count);
  for(const kind of ['carbon','number']){
    const values=row.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'],b=bounds(current,kind);
    expect(drawing.scales.logarithmic[kind]).toEqual(b);expect(drawing[kind]).toHaveLength(50);
    expect(drawing.scales[kind]).toBe(Math.max(...current.flatMap(s=>s.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'].map(q=>q.value))));
    for(let i=0;i<50;i++){
      const q=values[i],mesh=drawing[kind][i],height=q.value===0?0:(Math.log10(q.value)-b.lower)/(b.upper-b.lower);
      expect(mesh.index).toBe(i+1);expect(mesh.value).toBe(q.value);expect(mesh.unit).toBe(q.unit);expect(mesh.visible).toBe(q.value>0);
      expect(Math.abs(mesh.height-height)).toBeLessThanOrEqual(4*Number.EPSILON);expect(mesh.y).toBe(mesh.height/2);
    }
    expect(JSON.parse(await page.locator('[data-distribution='+kind+'] .coupled-plot').getAttribute('data-values'))).toEqual(values.map(q=>q.value));
  }
  await expect(page.locator('.coupled-history')).toHaveAttribute('data-selected-value',String(row.lai.value));
  expect(JSON.parse(await page.locator('.coupled-history .coupled-plot').getAttribute('data-values'))).toEqual(current.map(s=>s.lai.value));
  await expect(page.locator('.coupled-history svg')).toBeVisible();
  expect(JSON.parse(await page.locator('.cycle-evidence pre').textContent())).toEqual({farm:data.summary.farm,reference:data.summary.reference,manifest:data.summary.summary.manifest});
  const area=Number(await canvas.getAttribute('data-leaf-surface-area'));
  expect(Math.abs(area-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  verified.push({result_id:data.summary.result_id,index,offset,at:row.at,triangle_surface_area:area,C_N_mesh_values_verified:100});
}
async function bounded(phase){
  await expect(page.locator('.coupled-canvas')).toHaveCount(1);await expect(page.locator('.coupled-plot')).toHaveCount(3);
  const p=await collected();expect(p.active_reads).toBe(0);expect(p.observers).toBe(4);
  expect(p.gpu.filter(g=>g.connected)).toHaveLength(1);expect(p.gpu.filter(g=>g.context_alive && !g.context_lost && !g.connected)).toHaveLength(0);
  expect(p.charts.filter(c=>c.connected)).toHaveLength(3);expect(p.charts.filter(c=>!c.connected && c.instance)).toHaveLength(0);
  lifecycle.transitions.push({phase,...p});
}
async function cleared(phase,unmounted=false){
  await expect(page.locator('.coupled-canvas,.coupled-plot')).toHaveCount(0);
  await expect.poll(async()=>{const p=await collected();return p.observers+p.frames+p.timers+p.active_reads+p.gpu.filter(g=>g.context_alive && !g.context_lost).length+
    p.charts.filter(c=>c.instance).length+(unmounted?p.listeners.length:0);}).toBe(0);
  const p=await probe();lifecycle.transitions.push({phase,...p});return p;
}
try{
  await page.goto(origin);await connect(config.tokens.owner);const data=config.results.long;await lookup(data);
  for(const offset of [0,7,14,21]){
    await ready(data,offset);await expect(page.locator('.cycle-range')).toHaveAttribute('data-kind','samples');
    for(let i=0;i<Math.min(7,27-offset);i++){
      if(i){const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');}
      await sample(data,offset+i,offset);
    }
    const metrics=await cdp.send('Performance.getMetrics');windows.push({offset,count:Math.min(7,27-offset),js_heap_used_bytes:metrics.metrics.find(m=>m.name==='JSHeapUsedSize').value});
    await bounded('samples-'+offset);
    if(offset<21)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await expect(page.getByRole('button',{name:'다음 저장 범위',exact:true})).toBeDisabled();
  await page.locator('.connection>summary').click();await page.screenshot({path:screens+'/'+capturePrefix+'-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:screens+'/'+capturePrefix+'-mobile.png',fullPage:true});await page.setViewportSize({width:1536,height:1024});
  await page.getByRole('button',{name:'관리 사건 보기',exact:true}).click();
  for(const offset of [0,2,4]){
    await ready(data,offset);await expect(page.locator('.cycle-range')).toHaveAttribute('data-kind','events');
    const articles=page.locator('.cycle-events article');await expect(articles).toHaveCount(Math.min(2,5-offset));
    for(let i=0;i<Math.min(2,5-offset);i++){
      const event=data.events[offset+i],article=articles.nth(i);await expect(article).toContainText(event.at);
      for(const key of ['leaf','stem_root'])await expect(article.locator('[data-event-metric='+key+']')).toHaveAttribute('data-raw-value',String(event.removed[key].value));
      for(const [n,state] of [event.removed,event.before,event.after].entries()){
        const rows=await article.locator('details').nth(n).locator('tbody tr').evaluateAll(rows=>rows.map(r=>[
          r.querySelector('[data-metric=carbon]').dataset.rawValue,r.querySelector('[data-metric=number]').dataset.rawValue]));
        expect(rows).toEqual(state.fruit_number.map((q,j)=>[String(state.fruit_carbohydrate[j].value),String(q.value)]));
      }
      for(const [n,state] of [event.before,event.after].entries())for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'])
        await expect(article.locator('details').nth(n+1).locator('[data-event-state='+key+']')).toHaveAttribute('data-raw-value',String(state[key].value));
      eventsVerified.push({index:offset+i,at:event.at,original_before_after_removed_C_N_verified:true});
    }
    await cleared('events-'+offset);if(offset<4)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await page.getByRole('button',{name:'저장 시점 보기',exact:true}).click();await ready(data,21);await sample(data,21,21);await bounded('return-actual-offset-21');
  for(const name of ['past','empty','empty_completed']){
    const item=config.results[name];await lookup(item);await ready(item);
    if(name==='past'){
      await sample(item,0,0);await expect(page.locator('.coupled-hold')).toContainText(item.summary.summary.hold.at);
      await expect(page.locator('.coupled-time-table')).not.toContainText(item.summary.summary.hold.at);
      await expect(page.locator('.coupled-time-table tbody tr')).toHaveCount(item.samples.length);
      await page.locator('.coupled-hold summary').click();await expect(page.locator('[data-confirmed-cumulative]')).toHaveCount(16);
      await expect(page.locator('[data-confirmed-startup-diagnostic]')).toHaveCount(4);await bounded('actual-fractional-past-hold');
    }else{await expect(page.locator('.cycle-no-samples')).toBeVisible();await cleared('actual-'+name);}
    await page.screenshot({path:screens+'/'+capturePrefix+'-'+name+'.png',fullPage:true});
  }
  const shapePerformance=[];
  if(config.transport==='own-recorded-response-fixture' && config.results.many){
    const many=config.results.many;await lookup(many);await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
    for(let i=0;i<20;i++){
      await ready(many,i*7);await sample(many,i*7,i*7);await bounded('shape-only-'+i);
      await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-samples','7');
      await expect(page.locator('.cycle-replay')).toHaveAttribute('data-retained-events','0');
      const tick=performance.now(),slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');
      await expect(page.locator('.coupled-canvas')).toHaveAttribute('data-scene-at',many.samples[i*7+1].at);
      const metrics=await cdp.send('Performance.getMetrics');shapePerformance.push({window:i,selected_input_response_ms:performance.now()-tick,
        js_heap_used_bytes:metrics.metrics.find(m=>m.name==='JSHeapUsedSize').value});
      if(i<19)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
    }
    await cdp.send('Emulation.setCPUThrottlingRate',{rate:1});
  }
  await lookup(data);await ready(data);await sample(data,0,0);await bounded('before-current-rights');
  process.stdout.write(JSON.stringify({stage:'geometry_verified',sample_count:27,event_count:5})+'\n');
  expect((await next()).stage).toBe('rights_revoked');fixtureRights=false;await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();
  await expect(page.locator('.cycle-replay [role=alert]')).toContainText('현재 권리');await cleared('current-rights-denied');
  process.stdout.write(JSON.stringify({stage:'rights_hold_verified'})+'\n');expect((await next()).stage).toBe('rights_restored');fixtureRights=true;
  await connect(config.tokens.denied);await lookup(data);await expect(page.locator('.cycle-replay [role=alert]')).toContainText('조회 권한');await cleared('account-denied');
  await connect(config.tokens.owner);await lookup(data);await ready(data);await sample(data,0,0);await bounded('reconnected');
  if(calculation){
    process.stdout.write(JSON.stringify({stage:'tamper_ready'})+'\n');expect((await next()).stage).toBe('result_tampered');fixtureTampered=true;
    await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();
    await expect(page.locator('.cycle-replay [role=alert]')).toContainText('현재 권리');await cleared('valid-HMAC-result-tamper-denied');
    process.stdout.write(JSON.stringify({stage:'tamper_hold_verified'})+'\n');expect((await next()).stage).toBe('result_restored');fixtureTampered=false;
    await lookup(data);await ready(data);await sample(data,0,0);
    await page.locator('.coupled-canvas').evaluate(canvas=>{
      globalThis.__nativeCycleLoss=canvas.getContext('webgl2').getExtension('WEBGL_lose_context');globalThis.__nativeCycleLoss.loseContext();
    });
    await expect(page.locator('.crop-scene-fallback')).toBeVisible();
    const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');
    await expect(page.locator('.coupled-readout')).toHaveAttribute('data-selected-at',data.samples[1].at);
    await page.evaluate(()=>{globalThis.__nativeCycleLoss.restoreContext();delete globalThis.__nativeCycleLoss;});
    await expect(page.locator('.crop-scene-fallback')).toHaveCount(0);await sample(data,1,0);await bounded('actual-WebGL-loss-restored-current-UTC');
    await page.emulateMedia({reducedMotion:'reduce'});await expect(page.getByRole('button',{name:'성장 자동 재생'})).toBeDisabled();
    await slider.focus();await slider.press('ArrowRight');await sample(data,2,0);await page.emulateMedia({reducedMotion:'no-preference'});
  }
  // Exercise the real crop player timer before unmount; all data remain current original UTCs.
  await page.getByRole('button',{name:'성장 자동 재생'}).click();await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();
  const final=await cleared('unmount',true);lifecycle.unmount_zero=final.listeners.length===0;
  expect(errors).toEqual([]);await expect(page.getByLabel('접근 토큰')).toHaveValue('');
  expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
  process.stdout.write(JSON.stringify({stage:'verified',transport:config.transport??'native_PG_TLS',original_samples_verified:27,original_events_verified:5,verified,events_verified:eventsVerified,
    windows,shape_performance:{scope:'shape_only_repeated_rows_CPU4x_not_whole_cycle_or_actual_low_end_device',measurements:shapePerformance},
    network,errors,console_messages:consoleMessages,max_active_reads:final.max_active_reads,lifecycle,actual_account_change:true,reconnected:true,
    format,result_path:resultPath,actual_WebGL_loss_restore:calculation,reduced_motion_keyboard:calculation,result_tamper_protocol:calculation})+'\n');
}catch(error){await writeFile(screens+'/failure-lifecycle.json',JSON.stringify({scope:config.transport??'native_PG_TLS',lifecycle:await probe(),
  network,verified,events_verified:eventsVerified,errors,whole_browser_accepted:false},null,2));throw error;
}finally{await cdp.detach();await context.close();await browser.close();await lines.return?.();}
