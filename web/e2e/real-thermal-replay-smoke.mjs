// Real HTTPS API and SCRAM storage; test-owned synthetic CLI/release authorities.
import {chromium,expect} from '@playwright/test';
import {createInterface} from 'node:readline';
import {mkdir} from 'node:fs/promises';
const input=createInterface({input:process.stdin});
const inputLines=input[Symbol.asyncIterator]();
const firstLine=await inputLines.next();
const configuration=firstLine.done?null:JSON.parse(firstLine.value);
if(!configuration)throw new Error('synthetic browser configuration required');
if(configuration.kind!==undefined && configuration.kind!=='authored')throw new Error('replay kind rejected');
if(!configuration.workflow)input.close();
const authored=configuration.kind==='authored';
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1440,height:1000}});
if(configuration.workflow){
  if(!authored || !configuration.farm)throw new Error('authored workflow requires farm lookup');
  await context.addInitScript(({review_uuid,run_uuid})=>{
    const ids=[review_uuid,run_uuid];let index=0;
    Object.defineProperty(Crypto.prototype,'randomUUID',{configurable:true,
      value:()=>{if(index>=ids.length)throw new Error('unexpected synthetic retry key');
        return ids[index++];}});
  },configuration.workflow);
}
const page=await context.newPage();const errors=[],captureWarnings=[],network=[],responses=[];
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{
  const text=message.text().replaceAll(configuration.token,'<redacted>');
  const readback=/^\[\.WebGL-0x[0-9a-f]+\]GL Driver Message \(OpenGL, Performance, GL_CLOSE_PATH_NV, High\): GPU stall due to ReadPixels(?: \(this message will no longer repeat\))?$/;
  if(message.type()==='warning' && readback.test(text))captureWarnings.push('gpu_read_pixels_stall');
  else if(['error','warning'].includes(message.type()))errors.push(message.type()+': '+text);
});
page.on('response',response=>{if(new URL(response.url()).pathname.startsWith('/v1/'))responses.push(response);});
try{
  await page.goto(process.argv[2]);
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(configuration.token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await expect(page.getByLabel('접근 토큰')).toHaveValue('');
  if(configuration.farm){
    if(!authored)throw new Error('authored farm lookup requires authored replay');
    await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
    await page.getByLabel('시나리오 ID').fill(configuration.farm.scenario_id);
    await page.getByLabel('판본',{exact:true}).fill(configuration.farm.revision);
    const lookup=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/farm-authored-inputs');
    await page.getByRole('button',{name:'등록 기록 확인'}).click();
    const lookupResponse=await lookup;
    if(lookupResponse.status()!==200){
      const result=await lookupResponse.json();
      throw new Error('authored farm lookup status '+lookupResponse.status()+' code '+result.code);
    }
    await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible({timeout:60_000});
    await expect(page.locator('.authored-facts code').first())
      .toHaveText(configuration.farm.registration_sha256);
  }
  if(configuration.workflow){
    const reviewReply=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/farm-authored-reviews'
      && response.request().method()==='POST',{timeout:200_000});
    await page.getByRole('button',{name:'입력 검토 요청'}).click();
    const reviewResponse=await reviewReply;
    if(reviewResponse.status()!==202){
      const result=await reviewResponse.json();
      throw new Error('authored review status '+reviewResponse.status()+' code '+result.error?.code);
    }
    expect(reviewResponse.request().postDataJSON().idempotency_key)
      .toBe('review-'+configuration.workflow.review_uuid);
    await expect(page.locator('.authored-job-id code')).toHaveCount(1);
    const reviewId=await page.locator('.authored-job-id code').first().textContent();
    expect(reviewId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    await expect(page.getByText(reviewId,{exact:true})).toBeVisible();
    process.stdout.write(JSON.stringify({event:'review_admitted',job_id:reviewId})+'\n');
    const reviewLine=await inputLines.next();
    if(reviewLine.done)throw new Error('review result missing');
    const reviewWorker=JSON.parse(reviewLine.value);
    if(reviewWorker.event!=='review_succeeded' || reviewWorker.job_id!==reviewId)
      throw new Error('review result does not match admitted job');
    await page.getByRole('button',{name:'상태 다시 확인'}).first().click();
    await expect(page.getByRole('button',{name:'열 계산 요청'})).toBeEnabled();
    const runReply=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/authored-runs'
      && response.request().method()==='POST',{timeout:200_000});
    await page.getByRole('button',{name:'열 계산 요청'}).click();
    const runResponse=await runReply;
    if(runResponse.status()!==202){
      const result=await runResponse.json();
      throw new Error('authored run status '+runResponse.status()+' code '+result.error?.code);
    }
    expect(runResponse.request().postDataJSON().idempotency_key)
      .toBe('run-'+configuration.workflow.run_uuid);
    await expect(page.locator('.authored-job-id code')).toHaveCount(2);
    const jobId=await page.locator('.authored-job-id code').last().textContent();
    expect(jobId).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
    await expect(page.getByText(jobId,{exact:true})).toBeVisible();
    process.stdout.write(JSON.stringify({event:'run_admitted',job_id:jobId})+'\n');
    const workerLine=await inputLines.next();
    if(workerLine.done)throw new Error('worker result missing');
    const worker=JSON.parse(workerLine.value);
    input.close();
    if(worker.event!=='worker_succeeded' || worker.job_id!==jobId)
      throw new Error('worker result does not match admitted job');
    configuration.job_id=jobId;configuration.run_id=worker.run_id;
    configuration.series=worker.series;
    await page.getByRole('button',{name:'상태 다시 확인'}).last().click();
    await expect(page.getByRole('button',{name:'3D 재생 열기'})).toBeEnabled();
    await page.getByRole('button',{name:'3D 재생 열기'}).click();
    await expect(page.getByLabel('완료된 열 작업 ID')).toHaveValue(configuration.job_id);
  }else{
    await page.getByRole('button',{name:'05 3D 열 재생'}).click();
    if(authored)await page.getByRole('radio',{name:'작성한 농장 열 재생'}).check();
    await page.getByLabel('완료된 열 작업 ID').fill(configuration.job_id);
  }
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',configuration.run_id,{timeout:60_000});
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-replay-kind',authored?'authored':'fixed');
  await expect(page.getByText('3D 준비됨',{exact:true})).toBeVisible();
  for(const response of responses){
    expect(response.request().method()).toBe(response.status()===202?'POST':'GET');
    expect([200,202]).toContain(response.status());
    expect(response.headers()['cache-control']).toBe('no-store');
    network.push({path:new URL(response.url()).pathname,status:response.status()});
  }
  expect(responses.length).toBe(configuration.workflow?8:authored?(configuration.farm?4:3):4);
  // Compare with the server projection of the verified immutable Run supplied by
  // the harness. The SDK releases response bodies after its bounded read.
  const series=configuration.series;
  expect(series.run_id).toBe(configuration.run_id);expect(series.points.length).toBe(120);
  const slider=page.getByRole('slider',{name:'저장 시각 선택'});
  for(const [key,index] of [['Home',0],['End',119]]){
    await slider.focus();await slider.press(key);const point=series.points[index];
    for(const selector of ['.replay-viewer','.zone-scene','.replay-summary','.replay-chart'])
      await expect(page.locator(selector)).toHaveAttribute('data-selected-at',point.at_utc);
    await expect(page.locator('.zone-canvas')).toHaveAttribute('data-scene-at-utc',point.at_utc);
    expect(Number(await page.locator('.zone-canvas').getAttribute('data-draw-calls'))).toBeGreaterThan(0);
    for(const metric of ['temperature_k','relative_humidity_fraction','humidity_ratio_kg_v_per_kg_da',
      'heat_demand_w_th','heat_delivered_w_th','delivered_heat_energy_kwh_th']){
      await expect(page.locator('.replay-summary [data-metric="'+metric+'"]')).toHaveAttribute('data-raw-value',String(point[metric]));
      await expect(page.locator('.replay-table tr[aria-selected=true] [data-metric="'+metric+'"]')).toHaveAttribute('data-raw-value',String(point[metric]));
    }
  }
  await slider.press('Home');await slider.press('ArrowRight');
  await expect(page.locator('.zone-canvas')).toHaveAttribute('data-scene-at-utc',series.points[1].at_utc);
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await mkdir(process.argv[3],{recursive:true});await documentReady();
  await page.locator('.replay-top-grid').screenshot({path:process.argv[3]+'/replay-scene-summary.png'});
  for(const width of [1440,768,320]){
    await page.setViewportSize({width,height:1000});
    await expect(page.getByText('3D 준비됨',{exact:true})).toBeVisible();
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollHeight<=document.body.getBoundingClientRect().height+1)).toBe(true);
    await page.evaluate(()=>scrollTo(0,0));
    await page.screenshot({path:process.argv[3]+'/replay-'+width+'-top.png'});
    await page.screenshot({path:process.argv[3]+'/replay-'+width+'.png',fullPage:true});
  }
  expect(errors).toEqual([]);
  process.stdout.write(JSON.stringify({stage:'verified',points:series.points.length,network,
    console_errors:0,gpu_capture_warnings:captureWarnings.length})+'\n');
}finally{await context.close();await browser.close();}
async function documentReady(){await page.evaluate(()=>document.fonts.ready);}
