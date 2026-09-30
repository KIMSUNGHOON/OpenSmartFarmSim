// Real HTTPS API and SCRAM storage; test-owned synthetic CLI/release authorities.
import {chromium,expect} from '@playwright/test';
import {createInterface} from 'node:readline';
import {mkdir} from 'node:fs/promises';
const input=createInterface({input:process.stdin});
let configuration;
for await(const line of input){configuration=JSON.parse(line);break;}
input.close();
if(!configuration)throw new Error('synthetic browser configuration required');
if(configuration.kind!==undefined && configuration.kind!=='authored')throw new Error('replay kind rejected');
const authored=configuration.kind==='authored';
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const context=await browser.newContext({ignoreHTTPSErrors:true,viewport:{width:1440,height:1000}});
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
  await page.getByRole('button',{name:'05 3D 열 재생'}).click();
  if(authored)await page.getByRole('radio',{name:'작성한 농장 열 재생'}).check();
  await page.getByLabel('완료된 열 작업 ID').fill(configuration.job_id);
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',configuration.run_id,{timeout:60_000});
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-replay-kind',authored?'authored':'fixed');
  await expect(page.getByText('3D 준비됨',{exact:true})).toBeVisible();
  for(const response of responses){
    expect(response.request().method()).toBe('GET');expect(response.status()).toBe(200);
    expect(response.headers()['cache-control']).toBe('no-store');
    network.push({path:new URL(response.url()).pathname,status:response.status()});
  }
  expect(responses.length).toBe(authored?(configuration.farm?4:3):4);
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
