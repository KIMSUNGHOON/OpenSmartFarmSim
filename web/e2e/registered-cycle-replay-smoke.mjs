// Own synthetic DB/HTTPS only. No response routing or replacement calculation.
import {createInterface} from 'node:readline';
import {mkdir,writeFile} from 'node:fs/promises';
import {chromium,expect as assertions} from '@playwright/test';
const expect=assertions.configure({timeout:40_000});
const lines=createInterface({input:process.stdin})[Symbol.asyncIterator]();
async function next(){const line=await lines.next();if(line.done)throw new Error('owned replay protocol ended');return JSON.parse(line.value);}
const config=await next(),data=config.data,origin=process.argv[2],screens=process.argv[3];
await mkdir(screens,{recursive:true});
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1536,height:1024}});
const page=await context.newPage(),network=[],errors=[],consoleMessages=[],verified=[],events=[];
const path='/v1/crop-cycle-calculation-research-results/';
page.on('pageerror',e=>errors.push(e.message));
page.on('console',m=>{if(['error','warning'].includes(m.type()))consoleMessages.push({type:m.type(),text:m.text()});});
await page.exposeFunction('__ownedReplaySettled',item=>network.push(item));
await page.addInitScript(({path})=>{
  let active=0,peak=0;const fetch=globalThis.fetch.bind(globalThis);
  globalThis.fetch=async(...args)=>{
    const u=new URL(args[0] instanceof Request?args[0].url:String(args[0]),location.href);
    if(!u.pathname.startsWith(path))return fetch(...args);
    const started=performance.now(),item={view:u.searchParams.get('view'),offset:u.searchParams.get('offset'),
      status:null,bytes:0,cache:null,complete:false,outcome:null,seconds:0};
    active++;peak=Math.max(peak,active);let settled=false;
    async function settle(outcome){if(settled)return;settled=true;active--;item.outcome=outcome;
      item.complete=outcome==='complete';item.seconds=(performance.now()-started)/1000;await globalThis.__ownedReplaySettled(item);}
    try{
      const response=await fetch(...args);item.status=response.status;item.cache=response.headers.get('cache-control');
      if(!response.ok||!response.body){await settle('headers');return response;}
      const body=response.body,getReader=body.getReader.bind(body);
      Object.defineProperty(body,'getReader',{value:(...a)=>{
        const reader=getReader(...a),read=reader.read.bind(reader),cancel=reader.cancel.bind(reader);
        Object.defineProperty(reader,'read',{value:async(...r)=>{try{const value=await read(...r);
          if(value.done)await settle('complete');else item.bytes+=value.value.byteLength;return value;
        }catch(error){await settle('read-error');throw error;}}});
        Object.defineProperty(reader,'cancel',{value:async(...r)=>{try{return await cancel(...r);}finally{await settle('canceled');}}});
        return reader;
      }});return response;
    }catch(error){await settle('fetch-error');throw error;}
  };
  globalThis.__registeredReplayReads=()=>({active,peak});
},{path});
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
async function idle(){await expect.poll(()=>page.evaluate(()=>globalThis.__registeredReplayReads().active)).toBe(0);}
async function connect(token){
  if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('calculation-cycle');
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-source-kind','calculation');
}
async function lookup(){
  if(await page.locator('.crop-lookup').getAttribute('open')===null)await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  await expect(page.getByLabel(labels.result_id,{exact:true})).toBeVisible();
  for(const [key,value] of Object.entries({result_id:data.summary.result_id,...data.summary.farm}))await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function ready(kind,offset){
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','ready');
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-result-id',data.summary.result_id);
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-kind',kind);
  await expect(page.locator('.cycle-range')).toHaveAttribute('data-offset',String(offset));await idle();
}
function bounds(rows,key){
  const positive=rows.flatMap(row=>row.state[key].map(q=>q.value)).filter(v=>v>0);
  if(!positive.length)return null;
  const upper=Math.ceil(Math.log10(Math.max(...positive)));
  return {lower:Math.floor(Math.log10(Math.min(...positive)))-1,upper:Object.is(upper,-0)?0:upper};
}
async function sample(index,offset,count){
  const row=data.samples[index],canvas=page.locator('.coupled-canvas'),rows=data.samples.slice(offset,offset+count);
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-index',String(index));
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-reference',JSON.stringify(data.summary.reference));
  for(const target of ['.coupled-viewer','.coupled-readout','.coupled-scene','.coupled-cohorts','.coupled-history','.coupled-distribution'])
    await expect(page.locator(target)).toHaveAttribute('data-selected-at',row.at);
  for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'])
    await expect(page.locator('.coupled-readout [data-metric='+key+']')).toHaveAttribute('data-raw-value',String(row.state[key].value));
  for(const key of ['lai','fruit_carbohydrate_total'])
    await expect(page.locator('.coupled-readout [data-metric='+key+']')).toHaveAttribute('data-raw-value',String(row[key].value));
  const table=await page.locator('.coupled-cohort-table tbody tr').evaluateAll(rows=>rows.map(r=>[
    r.querySelector('[data-metric=carbon]').dataset.rawValue,r.querySelector('[data-metric=number]').dataset.rawValue]));
  expect(table).toEqual(row.state.fruit_number.map((q,i)=>[String(row.state.fruit_carbohydrate[i].value),String(q.value)]));
  await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  const drawing=JSON.parse(await canvas.getAttribute('data-cohort-drawing'));
  for(const kind of ['carbon','number']){
    const key=kind==='carbon'?'fruit_carbohydrate':'fruit_number',b=bounds(rows,key);
    expect(drawing.scales.logarithmic[kind]).toEqual(b);expect(drawing[kind]).toHaveLength(50);
    for(const [i,q] of row.state[key].entries()){
      const mesh=drawing[kind][i],height=q.value===0?0:(Math.log10(q.value)-b.lower)/(b.upper-b.lower);
      expect(mesh.value).toBe(q.value);expect(mesh.unit).toBe(q.unit);expect(mesh.visible).toBe(q.value>0);
      expect(Math.abs(mesh.height-height)).toBeLessThanOrEqual(4*Number.EPSILON);
    }
    expect(JSON.parse(await page.locator('[data-distribution='+kind+'] .coupled-plot').getAttribute('data-values'))).toEqual(row.state[key].map(q=>q.value));
  }
  expect(JSON.parse(await page.locator('.coupled-history .coupled-plot').getAttribute('data-values'))).toEqual(rows.map(r=>r.lai.value));
  expect(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  expect(await canvas.evaluate(c=>{const gl=c.getContext('webgl2');return !!gl&&!gl.isContextLost();})).toBe(true);
  await expect(page.locator('.coupled-history svg')).toBeVisible();
  verified.push({index,at:row.at,C_N_mesh_values_verified:100});
}
async function cleared(){await expect(page.locator('.coupled-canvas,.coupled-plot')).toHaveCount(0);await idle();}
try{
  await page.goto(origin);await connect(config.tokens.owner);await lookup();
  let offset=0;
  for(let window=0;window<2;window++){
    await ready('samples',offset);const count=Number(await page.locator('.cycle-range').getAttribute('data-count'));
    expect(count).toBeGreaterThan(0);expect(count).toBeLessThanOrEqual(7);expect(offset+count).toBeLessThanOrEqual(data.samples.length);
    for(let i=0;i<count;i++){
      if(i){const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('ArrowRight');}
      await sample(offset+i,offset,count);
    }
    const nextOffset=await page.locator('.cycle-range').getAttribute('data-next-offset');
    if(!nextOffset||window===1)break;
    offset=Number(nextOffset);await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await page.screenshot({path:screens+'/registered-cycle-desktop.png',fullPage:true,mask:[page.getByLabel('접근 토큰')]});
  await page.setViewportSize({width:390,height:844});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:screens+'/registered-cycle-mobile.png',fullPage:true,mask:[page.getByLabel('접근 토큰')]});
  await page.setViewportSize({width:1536,height:1024});
  await page.getByRole('button',{name:'관리 사건 보기',exact:true}).click();offset=0;
  while(offset<data.events.length){
    await ready('events',offset);const articles=page.locator('.cycle-events article');
    const count=await articles.count();expect(count).toBeGreaterThan(0);expect(count).toBeLessThanOrEqual(2);
    for(let i=0;i<count;i++){
      const row=data.events[offset+i],article=articles.nth(i);await expect(article).toContainText(row.at);
      for(const key of ['leaf','stem_root'])await expect(article.locator('[data-event-metric='+key+']')).toHaveAttribute('data-raw-value',String(row.removed[key].value));
      for(const [n,state] of [row.removed,row.before,row.after].entries()){
        const actual=await article.locator('details').nth(n).locator('tbody tr').evaluateAll(rows=>rows.map(r=>[
          r.querySelector('[data-metric=carbon]').dataset.rawValue,r.querySelector('[data-metric=number]').dataset.rawValue]));
        expect(actual).toEqual(state.fruit_number.map((q,i)=>[String(state.fruit_carbohydrate[i].value),String(q.value)]));
      }
      events.push({index:offset+i,at:row.at,original_removal_before_after_verified:true});
    }
    await cleared();offset+=count;if(offset<data.events.length)await page.getByRole('button',{name:'다음 저장 범위',exact:true}).click();
  }
  await idle();process.stdout.write(JSON.stringify({stage:'geometry_verified'})+'\n');
  expect((await next()).stage).toBe('rights_revoked');
  await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();
  await expect(page.locator('.cycle-replay [role=alert]')).toBeVisible();await cleared();
  process.stdout.write(JSON.stringify({stage:'rights_hold_verified'})+'\n');expect((await next()).stage).toBe('rights_restored');
  await lookup();await ready('samples',0);await sample(0,0,Math.min(7,data.samples.length));
  await connect(config.tokens.denied);await lookup();await expect(page.locator('.cycle-replay [role=alert]')).toBeVisible();await cleared();
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();await cleared();
  const peak=await page.evaluate(()=>globalThis.__registeredReplayReads().peak);
  expect(errors).toEqual([]);expect(peak).toBe(1);
  expect(network.filter(r=>r.status===422)).toHaveLength(1);expect(network.filter(r=>r.status===403)).toHaveLength(1);
  expect(network.filter(r=>r.status===200).every(r=>r.complete&&r.bytes<=2*1024*1024&&r.cache==='no-store')).toBe(true);
  process.stdout.write(JSON.stringify({stage:'verified',samples_verified:new Set(verified.map(v=>v.index)).size,
    total_samples:data.summary.reference.sample_count,events_verified:events.length,total_events:data.summary.reference.event_count,
    verified,events,same_UTC_geometry:true,actual_WebGL:true,network,errors,console_messages:consoleMessages,
    peak_active_reads:peak,current_rights_hold_and_restored:true,actual_account_denied:true,unmounted:true,
    coverage:'first_two_sample_windows_and_up_to_eight_events_not_all_frames'})+'\n');
}catch(error){
  const observed=await page.evaluate(()=>({source:document.querySelector('.cycle-replay')?.dataset.sourceKind,
    phase:document.querySelector('.cycle-replay')?.dataset.windowPhase,lookup_open:document.querySelector('.crop-lookup')?.open}));
  await writeFile(screens+'/registered-cycle-failure.json',JSON.stringify({network,errors,verified,events,observed,accepted:false},null,2));
  await page.screenshot({path:screens+'/registered-cycle-failure.png',fullPage:true,mask:[page.getByLabel('접근 토큰')]});
  let message=String(error.stack??error);for(const token of Object.values(config.tokens))message=message.replaceAll(token,'[REDACTED_OWNED_TOKEN]');
  process.stderr.write(message+'\n');process.exitCode=1;
}
finally{await context.close();await browser.close();await lines.return?.();}
