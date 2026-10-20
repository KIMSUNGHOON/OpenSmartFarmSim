// Owned synthetic credentials arrive only over stdin. Every API response is live.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {createInterface} from 'node:readline';
import {writeFile} from 'node:fs/promises';
import {chromium,expect as assertions} from '@playwright/test';

const expect=assertions.configure({timeout:30_000});
const reader=createInterface({input:process.stdin}),lines=reader[Symbol.asyncIterator]();
async function next(){const line=await lines.next();assert(!line.done,'owned browser protocol ended');return JSON.parse(line.value);}
const config=await next(),origin=process.argv[2],directory=process.argv[3];
const clean=value=>Object.values(config.tokens).reduce((s,token)=>s.replaceAll(token,'[owned-token]'),String(value));
const network=[],errors=[],frames=[],pending=new Set(),started=new Map();
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader','--single-process','--no-zygote']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1536,height:1024},deviceScaleFactor:.5});
const page=await context.newPage();
page.on('pageerror',error=>errors.push(clean(error.message)));
page.on('request',request=>started.set(request,performance.now()));
page.on('response',response=>{
  const url=new URL(response.url());if(!url.pathname.startsWith('/v1/'))return;
  const task=(async()=>{
    assert(url.origin===origin,'unexpected API origin');
    const request=response.request();assert(request.method()==='GET','unexpected API mutation');
    assert(Object.values(config.tokens).some(token=>request.headers().authorization==='Bearer '+token),'unexpected owned account');
    const raw=await response.body(),bodySeconds=(performance.now()-started.get(request))/1000;
    const limit=url.pathname.startsWith('/v1/crop-research-result-catalog')?65536:2*1024**2;
    assert(raw.length<=limit&&bodySeconds<30,'native response size or deadline exceeded');
    assert(response.headers()['cache-control']==='no-store','native cache policy differs');
    network.push({path:url.pathname+url.search,method:'GET',status:response.status(),bytes:raw.length,
      body_SHA256:hash(raw),body_seconds:bodySeconds,cache_control:'no-store'});
  })().catch(error=>errors.push(clean(error.message))).finally(()=>pending.delete(task));pending.add(task);
});
const send=stage=>console.log(JSON.stringify({stage}));
async function connect(token){
  if(!await page.getByLabel('접근 토큰',{exact:true}).isVisible())await page.locator('.connection summary').click();
  await page.getByLabel('접근 토큰',{exact:true}).fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await expect(page.getByLabel('접근 토큰',{exact:true})).toHaveValue('');
  await page.getByRole('button',{name:/08 성장 연구 3D/}).click();
}
async function chooseResult(stamp){
  const button=page.locator('.catalog-results tbody tr:has(time[datetime='+JSON.stringify(stamp)+']) button');
  await expect(button).toHaveCount(1);await button.focus();await page.keyboard.press('Enter');
}
async function selectNormal(){
  await page.getByRole('button',{name:'저장 결과 목록에서 선택',exact:true}).click();
  const panel=page.locator('.crop-result-catalog');
  await panel.getByRole('button',{name:'이전 생장 연구',exact:true}).click();
  await panel.getByRole('button',{name:'농장 목록 조회',exact:true}).click();
  await panel.getByLabel('등록된 농장 판본',{exact:true}).selectOption(config.farm_job_id);
  await expect(panel.getByLabel('등록된 작물과 재배 기간')).toBeEnabled();
  await panel.getByLabel('등록된 작물과 재배 기간').selectOption(config.result.farm.crop_id);
  await expect(panel.locator('.catalog-results tbody tr')).toHaveCount(2);
  await chooseResult(config.recorded_at);
  await expect(panel.locator('.crop-viewer')).toBeVisible();
}
async function sample(index,label){
  const row=config.result.samples[index],canvas=page.locator('.crop-canvas');
  await expect(page.locator('.crop-viewer')).toHaveAttribute('data-result-id',config.result.result_id);
  for(const selector of ['.crop-viewer','.crop-readout','.crop-chart','.crop-scene'])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',row.at);
  await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  for(const name of ['leaf','stem_root','fruit','buffer']){
    const value=String(row.state[name].value);
    await expect(canvas).toHaveAttribute('data-carbon-'+name.replace('_','-'),value);
    await expect(page.locator('.crop-readout [data-metric="'+name+'"]')).toHaveAttribute('data-raw-value',value);
    await expect(page.locator('.crop-table tr[aria-selected=true] [data-metric="'+name+'"]')).toHaveAttribute('data-raw-value',value);
  }
  await expect(page.locator('.crop-readout [data-metric=lai]')).toHaveAttribute('data-raw-value',String(row.lai.value));
  const area=Number(await canvas.getAttribute('data-leaf-surface-area'));
  assert(Math.abs(area-row.lai.value)<=Math.max(1e-8,row.lai.value*1e-6),'LAI geometry differs');
  assert(Number(await canvas.getAttribute('data-draw-calls'))>0,'no actual WebGL draw');
  assert(await canvas.evaluate(e=>{const gl=e.getContext('webgl2');return !!gl&&!gl.isContextLost();}),'WebGL unavailable');
  frames.push({label,index,at:row.at,source_sample_SHA256:hash(JSON.stringify(row)),
    carbon_values:4,LAI:row.lai.value,same_original_values_and_UTC:true,actual_WebGL:true});
}
async function lookup(){
  const details=page.locator('.catalog-replay .crop-lookup');
  if(!await details.evaluate(e=>e.open))await details.locator('summary').click();
  await details.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function screenshot(name){
  await page.evaluate(()=>document.fonts.ready.then(()=>true));
  await page.locator('.catalog-replay').scrollIntoViewIfNeeded();
  await page.screenshot({path:directory+'/organ-'+name+'.private.png'});
}
async function sized(width,height){
  await page.setViewportSize({width,height});
  await expect.poll(()=>page.evaluate(()=>{
    const e=document.querySelector('.crop-plot'),c=e?.firstElementChild;
    return !!e&&!!c&&Math.abs(c.getBoundingClientRect().width-e.clientWidth)<1;
  })).toBe(true);
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'settled document overflow');
}
try{
  await page.goto(origin);await connect(config.tokens.owner);await selectNormal();
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();
  for(let i=0;i<config.result.samples.length;i++){
    if(i)await slider.press('ArrowRight');await sample(i,'desktop-'+i);
    if(i===0)await screenshot('desktop-first');
  }
  await screenshot('desktop-last');
  await sized(390,844);await sample(config.result.samples.length-1,'mobile-last');await screenshot('mobile-last');
  await sized(320,900);
  await page.reload();await connect(config.tokens.owner);await selectNormal();await sample(0,'reloaded-original');
  send('geometry_verified');assert((await next()).stage==='rights_revoked');
  await lookup();await expect(page.locator('.crop-viewer')).toHaveCount(0);
  await expect(page.locator('.crop-table')).toHaveCount(0);await expect(page.locator('.catalog-replay [role=alert]')).toBeVisible();
  send('rights_hold_verified');assert((await next()).stage==='rights_restored');
  await lookup();await sample(0,'rights-restored-original');
  await chooseResult(config.held_recorded_at);
  await expect(page.locator('.crop-hold')).toBeVisible();await expect(page.locator('.crop-canvas')).toHaveCount(0);
  await expect(page.locator('.crop-table')).toHaveCount(0);
  await expect(page.locator('.crop-hold-reason')).toContainText(config.held.hold.reason_code);
  await connect(config.tokens.denied);await expect(page.locator('.crop-viewer')).toHaveCount(0);
  const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',
    registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
  const details=page.locator('.crop-lookup');
  if(!await details.evaluate(e=>e.open))await details.locator('summary').click();
  for(const [key,value] of Object.entries({result_id:config.result.result_id,...config.result.farm}))
    await details.getByLabel(labels[key],{exact:true}).fill(value);
  await details.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.crop-viewer')).toHaveCount(0);await expect(page.locator('.crop-replay [role=alert]')).toBeVisible();
  await connect(config.tokens.owner);await selectNormal();await sample(0,'account-restored-original');
  await Promise.all([...pending]);assert.deepEqual(errors,[]);
  assert(network.some(r=>r.status===403)&&network.some(r=>r.status===422),'missing real current denial');
  assert(network.length<64,'unexpected request repetition');
  assert(!network.some(r=>r.path.includes('cycle-calculation')||r.path.includes('harvest-research')),'organ selection used another model');
  const result={stage:'verified',scope:'live synthetic organ catalogue/API/DB/browser only',mock_API_used:false,
    actual_WebGL:true,frames,network,errors,current_rights_scene_removed:true,rights_restored_original:true,
    reconnect_same_original_result:true,account_denied_and_restored:true,numeric_hold_has_no_scene:true,
    widths:[1536,390,320],DPR:.5,U1_accepted:false,WSL_capacity_accepted:false,deployed:false};
  assert(!JSON.stringify(result).includes(config.tokens.owner)&&!JSON.stringify(result).includes(config.tokens.denied));
  console.log(JSON.stringify(result));
}catch(error){
  await writeFile(directory+'/browser-failure.private.json',JSON.stringify({name:error.name,message:clean(error.message),frames,network,errors}),{flag:'wx',mode:0o400});
  await page.screenshot({path:directory+'/organ-failure.private.png'}).catch(()=>{});
  console.error(clean(error.stack));process.exitCode=1;
}finally{
  await browser.close();reader.close();process.stdin.destroy();
}
