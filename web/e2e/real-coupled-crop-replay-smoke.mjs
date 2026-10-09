// Only own synthetic public projections; credentials arrive on stdin and remain private.
import { createInterface } from 'node:readline';
import { mkdir } from 'node:fs/promises';
import { chromium,expect as assertions } from '@playwright/test';
import { observeApiBodies } from './observe-api-body.mjs';
const expect=assertions.configure({timeout:40_000});
const lines=createInterface({input:process.stdin})[Symbol.asyncIterator]();
async function next(){const line=await lines.next();if(line.done)throw new Error('test protocol ended');return JSON.parse(line.value);}
const config=await next(),origin=process.argv[2],screens=process.argv[3];await mkdir(screens,{recursive:true});
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1536,height:1024}});
const page=await context.newPage(),network=[],consumed=[],errors=[],verified=[];
await observeApiBodies(page,item=>consumed.push(item));page.on('pageerror',e=>errors.push(e.message));
page.on('response',response=>{if(new URL(response.url()).pathname.startsWith('/v1/crop-coupled-research-results/'))
  network.push({method:response.request().method(),status:response.status(),cache:response.headers()['cache-control']});});
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
async function connect(token){
  if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();await page.getByLabel('저장 결과 판본').selectOption('v2');
  await expect(page.locator('.coupled-replay')).toBeVisible();
}
async function lookup(result){
  if(!await page.getByLabel(labels.result_id,{exact:true}).isVisible())await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:result.result_id,...result.farm}))await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function sample(index,result=config.result){
  const row=result.samples[index],slider=page.getByRole('slider',{name:'연결 연구 저장 시점 선택'});
  await slider.focus();await slider.press('Home');for(let i=0;i<index;i++)await slider.press('ArrowRight');
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-result-id',result.result_id);
  for(const selector of ['.coupled-viewer','.coupled-readout','.coupled-scene','.coupled-cohorts','.coupled-history','.coupled-distribution'])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',row.at);
  const canvas=page.locator('.coupled-canvas');await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  const drawing=JSON.parse(await canvas.getAttribute('data-cohort-drawing'));
  for(const kind of ['carbon','number']){
    const values=row.state[kind==='carbon'?'fruit_carbohydrate':'fruit_number'];
    for(let i=0;i<50;i++){
      const q=values[i],mesh=drawing[kind][i];expect(mesh.index).toBe(i+1);expect(mesh.value).toBe(q.value);expect(mesh.unit).toBe(q.unit);
      expect(mesh.height).toBe(drawing.scales[kind]?q.value/drawing.scales[kind]:0);expect(mesh.y).toBe(mesh.height/2);expect(mesh.visible).toBe(q.value>0);
      await expect(page.locator('.coupled-cohort-table [data-cohort="'+(i+1)+'"] [data-metric="'+kind+'"]')).toHaveAttribute('data-raw-value',String(q.value));
    }
    expect(JSON.parse(await page.locator('[data-distribution="'+kind+'"] .coupled-plot').getAttribute('data-values'))).toEqual(values.map(q=>q.value));
  }
  for(const key of ['buffer','leaf','stem_root','temperature_filtered_24h','temperature_sum'])
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(row.state[key].value));
  for(const key of ['lai','fruit_carbohydrate_total'])
    await expect(page.locator('.coupled-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(row[key].value));
  const area=Number(await canvas.getAttribute('data-leaf-surface-area'));
  expect(Math.abs(area-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));
  await page.getByLabel('연결 연구 그래프 항목').selectOption('lai');
  await expect(page.locator('.coupled-history')).toHaveAttribute('data-selected-value',String(row.lai.value));
  await expect(page.locator('.coupled-history svg')).toBeVisible();expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  verified.push({result_id:result.result_id,at:row.at,lai:row.lai.value,triangle_surface_area:area,drawing});
}
try{
  await page.goto(origin);await connect(config.tokens.owner);await lookup(config.result);
  for(let i=0;i<config.result.samples.length;i++)await sample(i);
  await page.locator('.connection>summary').click();
  await page.screenshot({path:screens+'/coupled-crop-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:screens+'/coupled-crop-mobile.png',fullPage:true});
  await page.setViewportSize({width:1536,height:1024});await lookup(config.past);await sample(0,config.past);
  await expect(page.locator('.coupled-hold')).toContainText(config.past.hold.at);
  await expect(page.getByRole('slider',{name:'연결 연구 저장 시점 선택'})).toHaveAttribute('max','0');
  await page.screenshot({path:screens+'/coupled-crop-past-hold.png',fullPage:true});
  await lookup(config.empty);await expect(page.locator('.coupled-hold')).toContainText(config.empty.hold.reason_code);
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.coupled-history,.coupled-cohort-table')).toHaveCount(0);
  await page.screenshot({path:screens+'/coupled-crop-empty-hold.png',fullPage:true});
  await lookup(config.result);await sample(0);
  process.stdout.write(JSON.stringify({stage:'geometry_verified',sample_count:config.result.samples.length})+'\n');
  expect((await next()).stage).toBe('rights_revoked');await lookup(config.result);
  await expect(page.locator('.coupled-replay [role=alert]')).toContainText('현재 권리');
  await expect(page.locator('.coupled-viewer,.coupled-canvas,.crop-evidence')).toHaveCount(0);
  process.stdout.write(JSON.stringify({stage:'rights_hold_verified'})+'\n');
  expect((await next()).stage).toBe('rights_restored');await connect(config.tokens.denied);await lookup(config.result);
  await expect(page.locator('.coupled-replay [role=alert]')).toContainText('조회 권한');await expect(page.locator('.coupled-viewer')).toHaveCount(0);
  await connect(config.tokens.owner);await lookup(config.result);await sample(5);
  expect(errors).toEqual([]);await expect(page.getByLabel('접근 토큰')).toHaveValue('');
  expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
  process.stdout.write(JSON.stringify({stage:'verified',sample_count:config.result.samples.length,result_id:config.result.result_id,
    verified,network,consumed,errors,account_change:true,reconnected:true})+'\n');
}finally{await context.close();await browser.close();await lines.return?.();}
