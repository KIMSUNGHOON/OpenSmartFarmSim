import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {setTimeout as delay} from 'node:timers/promises';

const config=JSON.parse(readFileSync(process.argv[2],'utf8'));
const request=JSON.parse(readFileSync(config.request_file,'utf8'));
const {chromium}=await import(pathToFileURL(config.playwright).href);
const assert=(value,message)=>{if(!value)throw Error(message);};
const save=(name,value)=>writeFileSync(config.directory+'/'+name,JSON.stringify(value,null,2),{mode:0o600,flag:'wx'});
const started=Date.now(),errors=[],responses=[],frames=[],warnings=[];
let browser,context,page,cdp,gc,jobId=null,cancelAccepted=false;
async function until(read,message,seconds=300){
  const deadline=Date.now()+seconds*1000;
  while(true){const value=await read();if(value)return value;assert(Date.now()<deadline,message);await delay(200);}
}
async function capture(prefix=true){
  return page.evaluate(prefix=>{
    const root=document.querySelector(prefix?'.joint-prefix-viewer':'.ventilation-viewer');
    if(!root)return null;
    const canvas=root.querySelector('.coupled-canvas'),at=root.dataset.selectedAt;
    if(!canvas||canvas.dataset.sceneAt!==at||Number(canvas.dataset.drawCalls)<=0)return null;
    const chart=root.querySelector('.joint-history');if(chart?.dataset.selectedAt!==at)return null;
    const quantities=selector=>Object.fromEntries([...root.querySelectorAll(selector+' [data-metric]')].map(q=>
      [q.dataset.metric,{value:Number(q.dataset.rawValue),unit:q.querySelector('small').textContent.trim()}]));
    return {at,scene_at:canvas.dataset.sceneAt,chart_at:chart.dataset.selectedAt,
      reference:JSON.parse((prefix?root.closest('.joint-prefix').dataset.prefixReference:root.dataset.reference)),
      draw_calls:Number(canvas.dataset.drawCalls),leaf_surface_area:Number(canvas.dataset.leafSurfaceArea),
      drawing:JSON.parse(canvas.dataset.cohortDrawing),
      cohorts:[...root.querySelectorAll('.coupled-cohort-table tbody tr')].map(row=>
        [...row.querySelectorAll('td')].map(q=>Number(q.dataset.rawValue))),
      quantities:quantities(prefix?'dl[aria-label="확정 작물·기후 원값"]':'dl[aria-label="작물·기후 원값"]'),
      ventilation:JSON.parse(root.querySelector('[data-ventilation]').dataset.ventilation),
      ledgers:quantities(prefix?'dl[aria-label="확정 누적25장부"]':'dl[aria-label="누적25장부"]'),
      residuals:quantities(prefix?'dl[aria-label="확정 수지 잔차"]':'dl[aria-label="수지 잔차"]')};
  },prefix);
}
async function screenshot(name){
  await cdp.send('HeapProfiler.collectGarbage');
  const scene=page.locator('.coupled-top-grid').first();if(await scene.count())await scene.evaluate(e=>e.scrollIntoView({block:'start'}));
  await page.screenshot({path:config.directory+'/'+name+'.private.png',fullPage:false});
}
async function reconnect(){
  const labels={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',
    registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
  await page.getByRole('button',{name:'조회 연결 해제',exact:true}).click();
  for(const [key,value] of Object.entries({job_id:jobId,...request.farm}))
    await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();
}
async function rights(name){
  writeFileSync(config.directory+'/'+name,'',{mode:0o600,flag:'wx'});
  await until(()=>existsSync(config.directory+'/'+name+'-ack'),'current rights control not acknowledged',10);
}
try{
  browser=await chromium.launch({args:['--enable-unsafe-swiftshader','--single-process','--no-zygote',
    '--num-raster-threads=1','--js-flags=--max-old-space-size=24 --max-semi-space-size=1 --expose-gc']});
  context=await browser.newContext({viewport:{width:800,height:600},timezoneId:'Asia/Seoul'});
  page=await context.newPage();page.setDefaultTimeout(10000);cdp=await context.newCDPSession(page);
  gc=setInterval(async()=>{try{await cdp.send('HeapProfiler.collectGarbage');globalThis.gc?.();}catch{}},250);gc.unref();
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',e=>{if(['warning','error'].includes(e.type()))warnings.push(e.text().slice(0,200));});
  page.on('response',async response=>{
    const url=new URL(response.url());if(!url.pathname.startsWith('/v1/'))return;
    responses.push({path:url.pathname,query:url.search,status:response.status(),method:response.request().method()});
    if(url.pathname==='/v1/crop-greenhouse-ventilation-executions'&&response.status()===202)
      jobId=(await response.json()).job_id;
    if(url.pathname.endsWith('/cancel')&&response.status()===200)
      cancelAccepted=(await response.json()).cancel_accepted===true;
  });
  await page.goto(config.origin+'/#ventilation-execution');
  if(await page.locator('.connection').getAttribute('open')===null)
    await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(config.token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  assert(await page.getByLabel('계산 모델',{exact:true}).inputValue()==='ventilation','wrong product model');
  await page.getByLabel('검토된 계산 접수 파일').setInputFiles(config.request_file);
  const submit=page.getByRole('button',{name:'계산 접수',exact:true});
  await until(()=>submit.isEnabled(),'registered request was rejected by product client',15);
  await submit.click();await until(()=>jobId,'actual admission did not return a job ID',45);
  const loopDeadline=Date.now()+270000;
  let terminal=false,canceled=false,selectionVerified=false;
  while(Date.now()<loopDeadline){
    const frame=await capture();
    if(frame&&!frames.some(old=>old.at===frame.at&&old.reference.selector.publication_sequence===frame.reference.selector.publication_sequence)){
      frame.observed_at=new Date().toISOString();frame.selection='automatic_latest';frames.push(frame);
      if(frames.length===1){
        await screenshot('running');
        if(config.mode==='cancel'){
          await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();
          await until(()=>cancelAccepted,'server did not acknowledge cancellation',45);
          await until(async()=>await page.getByRole('heading',{name:'취소됨',exact:true}).count(),'worker did not settle canceled',90);
          assert(await page.locator('.coupled-canvas').count()===0,'canceled scene remains');
          canceled=true;break;
        }
        const slider=page.getByLabel('확정 생장 시점 선택');
        if(Number(await slider.getAttribute('max'))>0){
          await slider.fill('0');const first=await until(()=>capture(),'selected original frame missing',10);
          first.selection='manual_saved_point';frames.push(first);selectionVerified=true;
          await page.getByRole('button',{name:'최신 확정 시점',exact:true}).click();
        }
      }
    }
    if(await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).count()){terminal=true;break;}
    await delay(300);
  }
  assert(frames.length>0,'no actual running confirmed WebGL frame observed');
  assert(!errors.length,'product JavaScript page error');
  const result={mode:config.mode,job_id:jobId,running_frames:frames,selection_verified:selectionVerified,
    cancel_accepted:cancelAccepted,scene_cleared:canceled,pageerrors:errors,responses,warnings,
    test_pause:false,wall_seconds:(Date.now()-started)/1000};
  if(config.mode!=='cancel'){
    assert(terminal&&!canceled,'no original terminal result offered');
    await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();
    result.terminal_frame=await until(()=>capture(false),'original terminal WebGL frame missing',45);
    result.result_id=await page.locator('.ventilation-viewer').getAttribute('data-result-id');
    await screenshot('terminal');
    await reconnect();
    await until(()=>page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).count(),'same completed job reconnect missing',45);
    await page.getByRole('button',{name:'같은 저장 결과 3D 열기',exact:true}).click();
    await until(()=>capture(false),'reconnected terminal WebGL missing',45);
    assert(await page.locator('.ventilation-viewer').getAttribute('data-result-id')===result.result_id,'reconnect changed result');
    result.reconnected=true;
    await rights('rights-revoke');
    await page.getByRole('button',{name:'현재 권리 다시 조회',exact:true}).click();
    await until(async()=>responses.some(r=>r.status===422&&r.path.startsWith('/v1/crop-greenhouse-ventilation-research-results/'))
      &&await page.getByRole('alert').count()>0,'actual current-rights denial missing',45);
    assert(await page.locator('.coupled-canvas').count()===0,'revoked original scene remains');result.rights_cleared=true;
    await screenshot('rights-blocked');
    await rights('rights-restore');
    await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
    result.restored_frame=await until(()=>capture(false),'same result did not restore after current rights',45);
    assert(await page.locator('.ventilation-viewer').getAttribute('data-result-id')===result.result_id,'restored result changed');
    result.rights_restored=true;
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'mobile page overflow');
    await screenshot('mobile');
  }else assert(canceled,'cancel did not settle');
  assert(!errors.length,'product JavaScript page error');
  result.wall_seconds=(Date.now()-started)/1000;
  save('browser-result.private.json',result);
  console.log(JSON.stringify({mode:config.mode,running_frames:frames.length,wall_seconds:result.wall_seconds,pageerrors:0}));
}catch(cause){
  save('browser-failure.private.json',{message:String(cause),job_id:jobId,running_frames:frames,responses,warnings,pageerrors:errors});
  if(page){try{await screenshot('failure');}catch{}}
  throw cause;
}finally{
  clearInterval(gc);
  if(cdp)await cdp.detach().catch(()=>{});
  if(context)await context.close();
  if(browser)await browser.close();
}
