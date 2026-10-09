// Tokens arrive on stdin and stay inside this isolated synthetic browser test.
import { createInterface } from 'node:readline';
import { mkdir } from 'node:fs/promises';
import { chromium,expect as assertions } from '@playwright/test';
import { observeApiBodies } from './observe-api-body.mjs';

const expect=assertions.configure({timeout:40_000});
const lines=createInterface({input:process.stdin})[Symbol.asyncIterator]();
async function next(){const line=await lines.next();if(line.done)throw new Error('test protocol ended');return JSON.parse(line.value);}
const config=await next(),origin=process.argv[2],screens=process.argv[3];
await mkdir(screens,{recursive:true});
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1440,height:1100}});
const page=await context.newPage(),network=[],consumed=[],errors=[],verified=[];
await observeApiBodies(page,item=>{consumed.push(item);});
page.on('pageerror',error=>errors.push(error.message));
page.on('response',response=>{if(new URL(response.url()).pathname.startsWith('/v1/crop-research-results/'))
  network.push({method:response.request().method(),status:response.status(),cache:response.headers()['cache-control']});});
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',
  registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
async function connect(token){
  if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await expect(page.locator('.crop-replay')).toBeVisible();
}
async function lookup(result){
  if(!await page.getByLabel('저장 연구 결과 ID',{exact:true}).isVisible())await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  for(const [key,value] of Object.entries({result_id:result.result_id,...result.farm}))await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
}
async function sample(index){
  const row=config.result.samples[index];
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});
  await slider.focus();await slider.press('Home');for(let i=0;i<index;i++)await slider.press('ArrowRight');
  const canvas=page.locator('.crop-canvas');
  await expect(page.locator('.crop-viewer')).toHaveAttribute('data-result-id',config.result.result_id);
  for(const selector of ['.crop-viewer','.crop-readout','.crop-scene','.crop-chart'])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',row.at);
  await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  const area=Number(await canvas.getAttribute('data-leaf-surface-area'));
  expect(Math.abs(area-row.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,row.lai.value*1e-6));
  const carbon={};
  for(const key of ['leaf','stem_root','fruit','buffer']){
    const value=row.state[key].value;carbon[key]=value;
    await expect(canvas).toHaveAttribute('data-carbon-'+key.replace('_','-'),String(value));
    await expect(page.locator('.crop-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(value));
    await expect(page.locator('.crop-table tr[aria-selected=true] [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(value));
  }
  await expect(page.locator('.crop-readout [data-metric=lai]')).toHaveAttribute('data-raw-value',String(row.lai.value));
  await expect(page.locator('.crop-table tr[aria-selected=true] [data-metric=lai]')).toHaveAttribute('data-raw-value',String(row.lai.value));
  await page.getByLabel('성장 그래프 항목').selectOption('lai');
  await expect(page.locator('.crop-chart')).toHaveAttribute('data-selected-value',String(row.lai.value));
  await expect(page.locator('.crop-plot svg')).toBeVisible();
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  verified.push({at:row.at,lai:row.lai.value,triangle_surface_area:area,carbon,
    maximum_carbon:Number(await canvas.getAttribute('data-maximum-carbon')),
    bar_heights:JSON.parse(await canvas.getAttribute('data-carbon-heights'))});
}
try{
  await page.goto(origin);await connect(config.tokens.owner);await lookup(config.result);
  for(let i=0;i<config.result.samples.length;i++)await sample(i);
  await page.screenshot({path:screens+'/crop-replay-desktop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:screens+'/crop-replay-mobile.png',fullPage:true});
  await page.setViewportSize({width:1440,height:1100});
  await lookup(config.held);
  await expect(page.locator('.crop-hold')).toContainText(config.held.hold.reason_code);
  await expect(page.locator('.crop-canvas,.crop-chart,.crop-table')).toHaveCount(0);
  await page.screenshot({path:screens+'/crop-replay-hold.png',fullPage:true});
  await lookup(config.result);await sample(0);
  process.stdout.write(JSON.stringify({stage:'geometry_verified',sample_count:config.result.samples.length})+'\n');
  expect((await next()).stage).toBe('rights_revoked');
  await lookup(config.result);
  await expect(page.locator('.crop-replay [role=alert]')).toContainText('현재 권리');
  await expect(page.locator('.crop-viewer,.crop-canvas')).toHaveCount(0);
  process.stdout.write(JSON.stringify({stage:'rights_hold_verified'})+'\n');
  expect((await next()).stage).toBe('rights_restored');
  await connect(config.tokens.denied);await lookup(config.result);
  await expect(page.locator('.crop-replay [role=alert]')).toContainText('조회 권한');
  await expect(page.locator('.crop-viewer')).toHaveCount(0);
  await connect(config.tokens.owner);await lookup(config.result);await sample(5);
  expect(errors).toEqual([]);
  await expect(page.getByLabel('접근 토큰')).toHaveValue('');
  expect(await page.evaluate(()=>({local:localStorage.length,session:sessionStorage.length}))).toEqual({local:0,session:0});
  process.stdout.write(JSON.stringify({stage:'verified',sample_count:config.result.samples.length,
    result_id:config.result.result_id,verified,network,consumed,errors,account_change:true,reconnected:true})+'\n');
}finally{
  await context.close();await browser.close();await lines.return?.();
}
