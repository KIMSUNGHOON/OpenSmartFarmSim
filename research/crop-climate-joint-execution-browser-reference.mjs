import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash,X509Certificate} from 'node:crypto';
import {createInterface} from 'node:readline';
import {chromium,expect as baseExpect} from '../web/node_modules/@playwright/test/index.mjs';
const expect=baseExpect.configure({timeout:45_000});
const lines=createInterface({input:process.stdin})[Symbol.asyncIterator]();
const receive=async()=>{const line=await lines.next();assert(!line.done);return JSON.parse(line.value);};
const send=value=>process.stdout.write(JSON.stringify({...value,at_ms:Date.now()})+'\n');
const input=await receive(),request=JSON.parse(readFileSync(input.request_file,'utf8'));
const pin=createHash('sha256').update(new X509Certificate(readFileSync(input.certificate)).publicKey.export({type:'spki',format:'der'})).digest('base64');
const browser=await chromium.launch({headless:true,args:['--enable-unsafe-swiftshader','--single-process','--no-zygote',
  '--js-flags=--max-old-space-size=64 --max-semi-space-size=2 --expose-gc','--ignore-certificate-errors-spki-list='+pin]});
const context=await browser.newContext({viewport:{width:1024,height:768},ignoreHTTPSErrors:false}),page=await context.newPage();
process.once('SIGTERM',()=>{void browser.close().finally(()=>process.exit(143));});
page.setDefaultTimeout(45_000);
const errors=[],observations=[],displayChecks=[],inflight=new Map(),bodies=[];let activeReads=0,maxReads=0,nextRequest=0;
const directory=input.root+'/browser-wire';mkdirSync(directory,{mode:0o700});
const relevant=url=>/^\/v1\/(crop-climate-joint-executions|jobs\/[^/]+\/crop-climate-joint-execution(?:\/cancel)?|crop-climate-joint-research-results\/)/.test(new URL(url).pathname);
page.on('pageerror',error=>errors.push(error.message));
page.on('request',r=>{
  if(!relevant(r.url()))return;
  assert(r.headers().authorization==='Bearer '+input.token,'unexpected authorization header');
});
await page.exposeFunction('__executionReadStarted',item=>{
  const id=nextRequest++;inflight.set(id,item);if(item.progress)maxReads=Math.max(maxReads,++activeReads);return id;
});
await page.exposeFunction('__executionReadCompleted',(id,item,base64)=>{
  const started=inflight.get(id);assert(started);inflight.delete(id);if(started.progress)activeReads--;
  const url=new URL(started.url),metadata={path:url.pathname,query:url.search,...item,milliseconds:Date.now()-started.started,observed_at_ms:Date.now()};
  try{
    if(!item.failed)assert.equal(item.no_store,true);
    if(base64!==null){
      const raw=Buffer.from(base64,'base64');assert(raw.length<=(url.pathname.includes('research-results')?2*1024**2:16*1024));
      const wire=directory+'/'+String(id).padStart(3,'0')+'.wire';writeFileSync(wire,raw,{mode:0o400,flag:'wx'});
      bodies.push({path:url.pathname,query:url.searchParams,value:JSON.parse(raw),completed_at_ms:metadata.observed_at_ms});
      Object.assign(metadata,{bytes:raw.length,sha256:createHash('sha256').update(raw).digest('hex'),wire_file:wire.split('/').at(-1)});
    }
    observations.push(metadata);
  }catch(error){errors.push(error.message);throw error;}
});
await page.addInitScript(()=>{
  const original=globalThis.fetch.bind(globalThis);
  globalThis.fetch=async(...args)=>{
    const url=new URL(String(args[0]),location.href);
    if(!/^\/v1\/(crop-climate-joint-executions|jobs\/[^/]+\/crop-climate-joint-execution(?:\/cancel)?|crop-climate-joint-research-results\/)/.test(url.pathname))return original(...args);
    const id=await globalThis.__executionReadStarted({url:url.href,started:Date.now(),progress:/\/crop-climate-joint-execution$/.test(url.pathname)});
    let finished=false;
    const finish=async(item,raw=null)=>{if(finished)return;finished=true;let base64=null;
      if(raw!==null){let text='';for(let i=0;i<raw.length;i+=8192)text+=String.fromCharCode(...raw.subarray(i,i+8192));base64=btoa(text);}
      await globalThis.__executionReadCompleted(id,item,base64);};
    try{
      const response=await original(...args),metadata={status:response.status,no_store:response.headers.get('cache-control')==='no-store'};
      if(!response.ok||!response.body){await finish(metadata);return response;}
      const body=response.body,getReader=body.getReader.bind(body);
      Object.defineProperty(body,'getReader',{value:(...readerArgs)=>{
        const reader=getReader(...readerArgs),read=reader.read.bind(reader),cancel=reader.cancel.bind(reader),chunks=[];let bytes=0;
        Object.defineProperty(reader,'read',{value:async(...readArgs)=>{
          try{
            const result=await read(...readArgs);
            if(!result.done){bytes+=result.value.byteLength;if(bytes>(url.pathname.includes('research-results')?2*1024**2:16*1024))throw new Error('observation bound exceeded');chunks.push(result.value.slice());}
            else{const joined=new Uint8Array(bytes);let offset=0;for(const chunk of chunks){joined.set(chunk,offset);offset+=chunk.byteLength;}await finish(metadata,joined);}
            return result;
          }catch(error){await finish({...metadata,failed:true,aborted:error.name==='AbortError'});throw error;}
        }});
        Object.defineProperty(reader,'cancel',{value:async(...cancelArgs)=>{await finish({...metadata,failed:true,aborted:true});return cancel(...cancelArgs);}});
        return reader;
      }});return response;
    }catch(error){await finish({failed:true,aborted:error.name==='AbortError'});throw error;}
  };
});
async function settle(){assert.deepEqual(errors,[]);}
async function connection(){const box=page.locator('.connection');if(await box.getAttribute('open')===null)await box.locator('summary').click();
  await page.getByLabel('접근 토큰',{exact:true}).fill(input.token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();}
async function attach(job){const detail=page.locator('.joint-execution>.crop-lookup');if(await detail.getAttribute('open')===null)await detail.locator('summary').click();
  for(const [label,value] of Object.entries({'계산 작업 ID':job,'계산 농장 시나리오 ID':request.farm.scenario_id,'계산 농장 판본':request.farm.scenario_revision,
    '계산 농장 등록 SHA-256':request.farm.registration_sha256,'계산 작물 ID':request.farm.crop_id}))await page.getByLabel(label,{exact:true}).fill(value);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();}
function lastRead(){return bodies.filter(b=>/\/crop-climate-joint-execution$/.test(b.path)&&b.value.version).at(-1)?.value;}
async function sameCheckpoint(){await settle();const value=lastRead();assert(value);const panel=page.getByLabel('계산 진행 상태');
  await expect(panel).toContainText(value.job.job_id);await expect(panel).toContainText(value.observed_at);await expect(panel).toContainText(value.job.updated_at);
  if(value.checkpoint){const cp=page.getByLabel('서버 수용 체크포인트');await expect(cp).toContainText(value.checkpoint.steps+' / '+value.checkpoint.planned_steps);
    await expect(cp).toContainText(value.checkpoint.checkpoint_recorded_at);if(value.checkpoint.computed_through_utc)await expect(cp).toContainText(value.checkpoint.computed_through_utc);}
  const response=bodies.findLast(b=>b.value===value),checked=Date.now();
  displayChecks.push({job_id:value.job.job_id,state:value.job.state,observed_at:value.observed_at,
    steps:value.checkpoint?.steps??null,response_completed_at_ms:response.completed_at_ms,display_check_completed_at_ms:checked,
    response_to_display_check_upper_bound_ms:checked-response.completed_at_ms});
  return value;
}
async function sameSavedResult(result){
  await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();await expect(page.locator('.joint-replay')).toBeVisible();
  await expect.poll(()=>bodies.filter(b=>b.path.includes('research-results')).length).toBeGreaterThanOrEqual(2);await settle();
  const summary=bodies.filter(b=>b.query.get('view')==='summary').at(-1)?.value;
  const samplePage=bodies.filter(b=>b.query.get('view')!=='summary'&&b.value.page?.kind==='samples').at(-1)?.value;
  assert(summary&&samplePage);assert.equal(summary.result_id,result.result_id);assert.deepEqual(summary.farm,result.farm);
  const rows=samplePage.page.records;assert(rows.length>0);
  send({stage:'saved_loaded',samples:rows.length,result_id:summary.result_id});
  for(let i=0;i<rows.length;i++){
    if(i)await page.locator('.joint-samples').getByRole('button').nth(i).click();const row=rows[i],at=row.time.at;
    const viewer=page.locator('.joint-viewer');await expect(viewer).toHaveAttribute('data-result-id',result.result_id);
    await expect(viewer).toHaveAttribute('data-selected-at',at);assert.deepEqual(JSON.parse(await viewer.getAttribute('data-farm')),result.farm);
    const readout=await page.locator('.coupled-readout [data-raw-value]').evaluateAll(list=>Object.fromEntries(list.map(e=>[e.dataset.metric,e.dataset.rawValue])));
    assert.deepEqual(readout,Object.fromEntries(Object.entries({...row.value.plant_state,...row.value.climate_state,...row.value.derived}).map(([key,q])=>[key,String(q.value)])));
    const canvas=page.locator('.coupled-canvas');await canvas.scrollIntoViewIfNeeded();await expect(canvas).toBeVisible();
    await expect(canvas).toHaveAttribute('data-scene-at',at);
    await expect.poll(async()=>Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
    const drawing=JSON.parse(await canvas.getAttribute('data-cohort-drawing'));
    assert.deepEqual(drawing.carbon.map(q=>q.value),row.value.cohort_state.fruit_carbohydrate.map(q=>q.value));
    assert.deepEqual(drawing.number.map(q=>q.value),row.value.cohort_state.fruit_number.map(q=>q.value));
    assert(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-row.value.derived.leaf_area_index.value)<1e-6);
    const temperature=JSON.parse(await canvas.getAttribute('data-temperature-drawing'));
    for(const [kind,q] of Object.entries({canopy:row.value.derived.canopy_temperature,air:row.value.climate_state.air_temperature})){
      const marker=temperature.markers.find(m=>m.kind===kind);assert.equal(marker.value,q.value);assert.equal(marker.unit,q.unit);}
    const cohorts=await page.locator('.coupled-cohorts tbody tr').evaluateAll(list=>list.map(tr=>[...tr.querySelectorAll('[data-raw-value]')].map(td=>td.dataset.rawValue)));
    assert.deepEqual(cohorts,row.value.cohort_state.fruit_number.map((q,index)=>[String(row.value.cohort_state.fruit_carbohydrate[index].value),String(q.value)]));
    send({stage:'sample_verified',index:i,at});
  }
  if(input.mode==='hold')await expect(page.getByRole('region',{name:'공동 계산 보류 진단'})).toBeVisible();
  await page.locator('.coupled-canvas').scrollIntoViewIfNeeded();
  await page.screenshot({path:input.root+'/native-'+input.mode+'.png',fullPage:false});
  return {samples:rows.length,UTC:rows.map(row=>row.time.at),result_id:summary.result_id,actual_WebGL:true};
}
const deadline=setTimeout(()=>{browser.close().finally(()=>process.exit(2));},210_000);
try{
  await page.goto(input.origin);await connection();await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('joint-execution');
  await page.getByLabel('검토된 계산 접수 파일').setInputFiles(input.request_file);await page.getByRole('button',{name:'계산 접수',exact:true}).click();
  await expect(page.getByRole('heading',{name:'대기 중',exact:true})).toBeVisible();await expect(page.getByLabel('계산 진행 상태')).toContainText('자동 조회 연결');
  const admitted=await sameCheckpoint(),job=admitted.job.job_id;assert.equal(admitted.checkpoint_status,'none');send({stage:'admitted',job_id:job});
  assert.equal((await receive()).stage,'claimed');await expect(page.getByRole('heading',{name:'계산 중',exact:true})).toBeVisible();
  const running=await sameCheckpoint();assert.equal(running.job.job_id,job);assert.equal(running.job.state,'simulating');send({stage:'running_seen'});
  if(input.mode==='cancel'){
    assert.equal((await receive()).stage,'rights_revoked');await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();
    await expect(page.getByRole('alert')).toContainText('현재 자료 권리');
    await expect(page.getByLabel('서버 수용 체크포인트')).toHaveCount(0);await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();
    await expect(page.getByLabel('계산 진행 상태')).toContainText('취소 요청 수락');await settle();
    const cancellation=bodies.filter(b=>b.path.endsWith('/cancel')).at(-1)?.value;assert(cancellation?.cancel_accepted&&cancellation.cancel_requested);
    send({stage:'cancel_accepted'});assert.equal((await receive()).stage,'worker_finished');
    await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();await expect(page.getByRole('heading',{name:'취소됨',exact:true})).toBeVisible();
    await expect(page.getByLabel('계산 진행 상태')).not.toContainText('작업자의 취소 확인');await sameCheckpoint();
    assert.equal(lastRead().result,null);await expect(page.locator('.joint-viewer,.coupled-canvas')).toHaveCount(0);
  }else{
    const checkpoint=(await receive());assert.equal(checkpoint.stage,'checkpoint_ready');
    await expect(page.getByLabel('서버 수용 체크포인트')).toContainText(checkpoint.steps+' / '+checkpoint.planned_steps);
    const middle=await sameCheckpoint();assert.equal(middle.checkpoint.steps,checkpoint.steps);assert.equal(middle.checkpoint.status,'yielded');send({stage:'checkpoint_seen',checkpoint:middle.checkpoint});
    assert.equal((await receive()).stage,'worker_finished');await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true})).toBeVisible();
    const final=await sameCheckpoint();assert.equal(final.job.job_id,job);assert.equal(final.result.status,input.mode);
    const saved=await sameSavedResult(final.result);send({stage:'result_loaded',job_id:job,...saved});assert.equal((await receive()).stage,'result_compared');
    await page.getByRole('button',{name:'조회 연결 해제',exact:true}).click();await expect(page.locator('.joint-viewer')).toHaveCount(0);await attach(job);
    await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true})).toBeVisible();const reconnected=await sameCheckpoint();
    assert.deepEqual(reconnected.result,final.result);assert.deepEqual(reconnected.checkpoint,final.checkpoint);
    await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();await expect(page.getByLabel('계산 진행 상태')).toContainText('취소 요청으로 상태가 바뀌지 않음');
    await expect(page.getByRole('heading',{name:'취소됨',exact:true})).toHaveCount(0);
    await expect(page.getByLabel('계산 진행 상태')).toContainText('최종 상태 확인');
  }
  await settle();assert.equal(maxReads,1);assert.equal(activeReads,0);assert.deepEqual(errors,[]);
  const report={mode:input.mode,job_id:job,no_mocked_routes:true,pinned_browser_certificate:true,automatic_real_time_polling:true,
    max_simultaneous_progress_GET:maxReads,observations,display_checks:displayChecks,
    display_timing_scope:'Body capture completion to finished DOM equality assertions; includes driver scheduling and assertion cost, not pure render latency',
    errors,actual_crop_Runs:0,G0_G4:'not_assessed'};
  writeFileSync(input.root+'/browser-result.private.json',JSON.stringify(report),{mode:0o400,flag:'wx'});
  send({stage:'verified',mode:input.mode,job_id:job,network_requests:observations.length,max_simultaneous_progress_GET:maxReads});
}finally{clearTimeout(deadline);await context.close();await browser.close();}
