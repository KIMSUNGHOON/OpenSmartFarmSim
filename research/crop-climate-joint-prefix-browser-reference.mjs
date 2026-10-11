import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';

const input=JSON.parse(readFileSync(process.argv[2],'utf8'));
const {chromium}=await import(pathToFileURL(input.playwright).href);
const token=JSON.parse(readFileSync(input.access_file,'utf8')).token;
const responses=[],pending=new Set(),errors=[],warnings=[];
const digest=raw=>createHash('sha256').update(raw).digest('hex');
const save=(name,value)=>writeFileSync(join(input.directory,name),JSON.stringify(value),{flag:'wx',mode:0o400});
async function until(read,check,timeout=45_000){
  const end=Date.now()+timeout;
  while(true){const value=await read();if(check(value))return value;
    assert(Date.now()<end,'browser observation timeout');await new Promise(resolve=>setTimeout(resolve,100));}
}
const browser=await chromium.launch({headless:true,args:['--enable-unsafe-swiftshader','--single-process',
  '--no-zygote','--js-flags=--max-old-space-size=32 --max-semi-space-size=1']});
let record;
try{
  const context=await browser.newContext({viewport:{width:1024,height:768},deviceScaleFactor:0.5});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  page.on('console',message=>{if(message.type()==='error')errors.push(message.text());
    else if(message.type()==='warning')warnings.push(message.text());});
  page.on('response',response=>{if(!new URL(response.url()).pathname.startsWith('/v1/'))return;
    const task=(async()=>{const raw=await response.body();assert(raw.length<=2*1024**2);
      responses.push({url:response.url(),status:response.status(),sha256:digest(raw),bytes:raw.length,
        no_store:response.headers()['cache-control']==='no-store',value:JSON.parse(raw.toString('utf8'))});})();
    pending.add(task);task.finally(()=>pending.delete(task)).catch(error=>errors.push(String(error)));});
  await page.goto(input.origin,{waitUntil:'networkidle'});
  await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('joint-execution');
  const labels={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',
    registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
  for(const [key,value] of Object.entries({job_id:input.job_id,...input.farm}))
    await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();
  await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();
  const canvas=page.locator('.coupled-canvas');await canvas.waitFor({state:'visible'});
  const drawing=await until(()=>canvas.evaluate(e=>({at:e.dataset.sceneAt,drawCalls:Number(e.dataset.drawCalls),
    cohorts:JSON.parse(e.dataset.cohortDrawing??'null')})),v=>v.drawCalls>0&&v.cohorts!==null);
  await Promise.all([...pending]);
  const samplePage=responses.find(r=>r.status===200&&r.value.page?.kind==='samples');assert(samplePage);
  const sample=samplePage.value.page.records[0];assert.equal(drawing.at,sample.time.at);
  assert.deepEqual(drawing.cohorts.carbon.map(q=>q.value),sample.value.cohort_state.fruit_carbohydrate.map(q=>q.value));
  assert.deepEqual(drawing.cohorts.number.map(q=>q.value),sample.value.cohort_state.fruit_number.map(q=>q.value));
  for(const metric of ['leaf_area_index','canopy_temperature'])
    assert.equal(await page.locator(`.joint-viewer [data-metric="${metric}"]`).first().getAttribute('data-raw-value'),String(sample.value.derived[metric].value));
  assert.equal(await page.locator('.joint-history').getAttribute('data-selected-at'),sample.time.at);
  assert.equal(await page.locator('.coupled-cohort-table tbody tr').count(),50);
  assert(responses.every(r=>r.status===200&&r.no_store));assert.deepEqual(errors,[]);
  assert(warnings.every(text=>text.includes('GL Driver Message')&&text.includes('GPU stall due to ReadPixels')));
  await canvas.scrollIntoViewIfNeeded();await page.screenshot({path:join(input.directory,'profile.png')});
  record={mode:input.mode,selected_UTC:sample.time.at,actual_WebGL_draw_calls:drawing.drawCalls,cohorts:50,
    original_C_N_and_LAI_canopy_temperature:true,console_errors:errors,driver_warnings:warnings,
    viewport:{width:1024,height:768,deviceScaleFactor:0.5},running_prefix_acceptance:false};
  await context.close();
}finally{
  await browser.close();await Promise.allSettled([...pending]);save('browser-responses.private.json',responses);
  save('browser-observation.private.json',record??{mode:input.mode,console_errors:errors,warnings,accepted:false});
}
console.log(JSON.stringify(record));
