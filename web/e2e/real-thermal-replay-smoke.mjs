// Real HTTPS API and SCRAM storage; test-owned synthetic CLI/release authorities.
import {chromium,expect} from '@playwright/test';
import {createInterface} from 'node:readline';
import {mkdir} from 'node:fs/promises';
import {observeApiBodies} from './observe-api-body.mjs';
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
  await context.addInitScript(({review_uuid,run_uuid,financial,money_uuid,assessment_uuid})=>{
    const ids=financial?[review_uuid,run_uuid,money_uuid,assessment_uuid]:[review_uuid,run_uuid];let index=0;
    Object.defineProperty(Crypto.prototype,'randomUUID',{configurable:true,
      value:()=>{if(index>=ids.length)throw new Error('unexpected synthetic retry key');
        return ids[index++];}});
  },configuration.workflow);
}
const page=await context.newPage();const errors=[],captureWarnings=[],network=[],responses=[];
const consumedBodies=[];
if(configuration.workflow?.financial)await observeApiBodies(page,record=>consumedBodies.push(record));
async function financialContinuation(){
  const posts=[],requests=[],observationStart=consumedBodies.length;
  const requested=request=>{if(new URL(request.url()).pathname.startsWith('/v1/')){
    requests.push({path:new URL(request.url()).pathname,method:request.method()});
    if(request.method()==='POST')posts.push({path:new URL(request.url()).pathname,body:request.postDataJSON()});
  }};
  page.on('request',requested);
  async function reference(label){
    const summary=page.getByText(label,{exact:true});await summary.click();
    return (await summary.locator('..').locator('code').innerText()).trim();
  }
  async function workerResult(event,id){
    const next=await inputLines.next();if(next.done)throw new Error(event+' result missing');
    const value=JSON.parse(next.value);expect(value.event).toBe(event);expect(value.job_id).toBe(id);return value;
  }
  async function selectRun(){
    await page.getByRole('button',{name:'07 작성 Run 경제·평가',exact:true}).click();
    await page.getByRole('button',{name:'저장 Run 목록 조회',exact:true}).click();
    await page.getByRole('button',{name:/저장된 합성 열 Run.*경제·평가 선택/}).click();
    await expect(page.getByRole('button',{name:'같은 Run 3D 열기',exact:true})).toBeEnabled({timeout:90_000});
  }
  try{
    await page.setViewportSize({width:1440,height:1000});await selectRun();
    await expect(page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true})).toBeEnabled();
    await page.getByRole('button',{name:'선택 Run 경제 계산 요청',exact:true}).click();
    await expect(page.getByText('경제 작업: 대기 중',{exact:true})).toBeVisible({timeout:90_000});
    const money=await reference('경제 작업 ID');
    const {idempotency_key,...submitted}=posts[0].body;
    expect(posts[0].path).toBe('/v1/economic-results');expect(submitted).toEqual(configuration.financial);
    expect(idempotency_key).toBe('web-authored-money-v1:'+configuration.workflow.money_uuid);
    process.stdout.write(JSON.stringify({event:'economic_admitted',job_id:money})+'\n');
    const expected=await workerResult('economic_succeeded',money);
    await page.getByRole('button',{name:'경제 상태·결과 확인',exact:true}).click();
    await expect(page.getByText('경제 작업: 작업 완료',{exact:true})).toBeVisible({timeout:90_000});
    await page.getByText('조건부 비용·현금 합계',{exact:true}).click();
    for(const field of ['revenue_krw','management_operating_income_krw','cash_shortage_krw',
      'variable_cost_krw','fixed_cost_krw','depreciation_krw','operating_cash_krw','business_cash_krw','equity_cash_krw']){
      const shown=await page.locator('[data-money-field="'+field+'"]').innerText();
      expect(expected.amounts[field]===null?shown:shown.replaceAll(',','').replace(/ 원$/,''))
        .toBe(expected.amounts[field]??'미확인');
    }
    await page.getByRole('button',{name:'작성 Run 월별 현금 조회',exact:true}).click();
    const rows=expected.cash.monthly_cash;expect(rows.length).toBeGreaterThan(0);
    await expect(page.getByRole('rowheader',{name:rows[0].month,exact:true})).toBeVisible({timeout:90_000});
    await expect(page.locator('.cash-table tbody tr')).toHaveCount(rows.length);
    for(const row of rows){
      const cells=await page.getByRole('rowheader',{name:row.month,exact:true}).locator('..').locator('td').allInnerTexts();
      expect(cells.map(value=>value.replaceAll(',','').replace(/ 원$/,''))).toEqual([
        row.opening_balance_krw,row.net_cash_krw,row.closing_balance_krw,row.minimum_balance_krw,row.minimum_at_utc,row.cash_shortage_krw]);
    }
    await page.getByRole('button',{name:'작성 Run 평가 요청',exact:true}).click();
    await expect(page.getByText('평가 작업: 대기 중',{exact:true})).toBeVisible({timeout:90_000});
    const assessment=await reference('작성 평가 작업 ID');
    expect(posts[1]).toEqual({path:'/v1/assessments',body:{run_job_id:configuration.job_id,economic_job_id:money,
      idempotency_key:'web-authored-assessment-v1:'+configuration.workflow.assessment_uuid}});
    process.stdout.write(JSON.stringify({event:'assessment_admitted',job_id:assessment})+'\n');
    await workerResult('assessment_held',assessment);
    await page.getByRole('button',{name:'작성 평가 상태 확인',exact:true}).click();
    await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible({timeout:90_000});
    await page.reload();
    await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill(configuration.token);
    await page.getByRole('button',{name:'연결 설정',exact:true}).click();await selectRun();
    await page.getByRole('button',{name:/작성 평가 기록.*현재 기록 조회/}).click();
    await expect(page.getByRole('heading',{name:'작성 Run 판단 보류 근거',exact:true})).toBeVisible({timeout:90_000});
    expect(await reference('작성 평가 작업 ID')).toBe(assessment);
    await expect(page.getByText('서버가 기록한 누락 근거 6개입니다.',{exact:true})).toBeVisible();
    await page.screenshot({path:process.argv[3]+'/source-farm-financial.png',fullPage:true});
    await page.getByRole('button',{name:'같은 Run 3D 열기',exact:true}).click();
    await expect(page.locator('.replay-viewer')).toHaveAttribute('data-run-id',configuration.run_id,{timeout:90_000});
    expect(Number(await page.locator('.zone-canvas').getAttribute('data-draw-calls'))).toBeGreaterThan(0);
    const slider=page.getByRole('slider',{name:'저장 시각 선택'});await slider.focus();await slider.press('End');
    const point=configuration.series.points[119];
    await expect(page.locator('.zone-canvas')).toHaveAttribute('data-scene-at-utc',point.at_utc);
    for(const selector of ['.replay-viewer','.zone-scene','.replay-summary','.replay-chart'])
      await expect(page.locator(selector)).toHaveAttribute('data-selected-at',point.at_utc);
    for(const metric of ['temperature_k','relative_humidity_fraction','humidity_ratio_kg_v_per_kg_da',
      'heat_demand_w_th','heat_delivered_w_th','delivered_heat_energy_kwh_th']){
      await expect(page.locator('.replay-summary [data-metric="'+metric+'"]')).toHaveAttribute('data-raw-value',String(point[metric]));
      await expect(page.locator('.replay-table tr[aria-selected=true] [data-metric="'+metric+'"]')).toHaveAttribute('data-raw-value',String(point[metric]));
    }
    await expect.poll(()=>consumedBodies.length-observationStart,{timeout:30_000}).toBe(requests.length);
    const checked=consumedBodies.slice(observationStart);expect(posts).toHaveLength(2);
    const identity=value=>JSON.stringify([value.path,value.method]);
    expect(checked.map(identity).sort()).toEqual(requests.map(identity).sort());
    expect(checked.filter(value=>![200,202].includes(value.status)||value.cache!=='no-store'||
      !Number.isFinite(value.body_seconds)||value.body_seconds<0||value.body_seconds>=30)).toEqual([]);
    for(const path of ['/v1/authored-runs/catalog','/v1/jobs/'+configuration.job_id+'/authored-economic-input',
      '/v1/jobs/'+configuration.job_id+'/authored-financial-history','/v1/economic-results','/v1/jobs/'+money,
      '/v1/jobs/'+money+'/economic-result','/v1/jobs/'+money+'/economic-cash-flow','/v1/assessments',
      '/v1/jobs/'+assessment,'/v1/jobs/'+assessment+'/hold-report','/v1/jobs/'+configuration.job_id+'/authored-run',
      '/v1/authored-runs/'+encodeURIComponent(configuration.run_id)+'/series'])
      expect(checked.some(value=>value.path===path)).toBe(true);
    return {run_id:configuration.run_id,economic_job_id:money,assessment_job_id:assessment,
      hold_count:6,cash_rows:rows.length,post_count:posts.length,network:checked,
      body_observation:'client_reader_eof',
      max_body_seconds:Math.max(...checked.map(value=>value.body_seconds))};
  }finally{page.off('request',requested);}
}
async function registerAuthoredFarm(document){
  const farm=document.farm,rights=document.rights;
  await page.getByRole('button',{name:'새 입력 판본 작성'}).click();
  if(configuration.source_selection){
    const selection=configuration.source_selection;
    await page.getByRole('button',{name:'저장 조사 조회',exact:true}).click();
    await page.getByRole('region',{name:'완료 조사 선택'}).getByRole('button')
      .filter({hasText:selection.research_id}).click();
    await page.getByRole('region',{name:'해당 조사의 완료 수집 선택'}).getByRole('button')
      .filter({hasText:selection.collection_id}).click();
    await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
    await page.getByRole('button',{name:selection.economic.scenario_id+' '+selection.economic.revision+' 현재 참조 확인',exact:true}).click();
    await expect(page.getByRole('region',{name:'작성에 연결된 경제 판본'})).toBeVisible({timeout:40_000});
    await expect(page.getByRole('region',{name:'선택한 원천 참조'})).toContainText('G0/G1 미수용');
    await expect(page.locator('input[name="floor_area"]')).toHaveValue('');
    await expect(page.locator('.authored-rights input')).not.toBeChecked();
  }else await page.getByRole('button',{name:'참조 직접 입력',exact:true}).click();
  const fields={scenario_id:farm.scenario_id,scenario_revision:farm.scenario_revision,
    research_job_id:farm.research_job_id,snapshot_id:farm.snapshot_id,
    decision_context_id:farm.decision_context_id,decision_at:farm.decision_at,
    market_hold_report_id:farm.market_context.hold_report_id,
    period_start:farm.period_start,period_end:farm.period_end,
    economic_scenario_id:farm.economic.scenario_id,economic_revision:farm.economic.revision,
    economic_sha256:farm.economic.sha256,economic_candidate_id:farm.economic.candidate_id,
    source_ref:farm.facility.floor_area.source_ref,
    record_revision:farm.facility.floor_area.revision,
    available_at:farm.facility.floor_area.available_at,zone_id:farm.facility.zone_id,
    ...Object.fromEntries(['floor_area','cultivable_area','indoor_volume',
      'effective_heat_capacity','dry_air_mass','envelope_conductance',
      'absorbed_solar_fraction'].map(key=>[key,farm.facility[key].value])),
    initial_temperature:farm.initial_state.temperature.value,
    initial_humidity_ratio:farm.initial_state.humidity_ratio.value,
    heater_capacity:farm.heater.capacity.value,heater_setpoint:farm.heater.setpoint.value,
    declaration_id:rights.declaration_id,rights_revision:rights.revision};
  for(const [key,value] of Object.entries(fields)){
    const field=page.locator(`.authored-composer input[name="${key}"]`);
    if(await field.getAttribute('readonly')!==null)await expect(field).toHaveValue(String(value));
    else await field.fill(String(value));
  }
  for(const [key,value] of Object.entries({tenure:farm.facility.tenure,
    decision_basis:farm.facility.decision_basis,
    heater_available:farm.heater.available.value?'yes':'no',objective:farm.objective,
    capex_mode:farm.constraints.capex_ceiling?'known':'unknown',
    cash_mode:farm.constraints.minimum_cash?'known':'unknown'}))
    await page.locator(`.authored-composer select[name="${key}"]`).selectOption(value);
  for(const [key,value] of Object.entries({capex_ceiling:farm.constraints.capex_ceiling?.value,
    minimum_cash:farm.constraints.minimum_cash?.value}))
    if(value!==undefined)await page.locator(`.authored-composer input[name="${key}"]`).fill(value);
  for(let i=0;i<farm.forcing.length;i++){
    if(i)await page.getByRole('button',{name:'원본 구간 추가'}).click();
    const row=page.locator('.authored-repeat-row').nth(i),item=farm.forcing[i];
    for(const [key,value] of Object.entries({start:item.start,end:item.end,
      ventilation:item.ventilation_dry_air_flow.value,
      canopy:item.canopy_evaporation.value,ground:item.ground_heat_flow.value}))
      await row.locator(`input[name="${key}"]`).fill(value);
  }
  for(let i=0;i<farm.crops.length;i++){
    await page.getByRole('button',{name:'작물 의도 추가'}).click();
    const row=page.locator('.authored-repeat-row').nth(farm.forcing.length+i),item=farm.crops[i];
    const cropFields={crop_id:item.crop_id,batch_id:item.batch_id,species:item.species,
      variety:item.variety,area:item.area.value,
      occupancy_start:item.occupancy.start,occupancy_end:item.occupancy.end,
      release_at:item.release_at,harvest_start:item.harvest_window.start,
      harvest_end:item.harvest_window.end,sales_start:item.sales_window.start,
      sales_end:item.sales_window.end,collection_start:item.collection_window.start,
      collection_end:item.collection_window.end,
      grades:item.grades.join(','),channels:item.channels.join(',')};
    for(const [key,value] of Object.entries(cropFields))
      await row.locator(`input[name="${key}"]`).fill(value);
  }
  await page.locator('.authored-rights input').check();
  await page.getByRole('button',{name:'입력 내용 검토'}).click();
  await expect(page.getByRole('region',{name:'제출 전 확인'})).toBeVisible();
  const reply=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/farm-authored-inputs'
    && response.request().method()==='POST',{timeout:200_000});
  await page.getByRole('button',{name:'불변 입력 판본 등록'}).click();
  const response=await reply;
  if(response.status()!==200)throw new Error('authored farm registration status '+response.status());
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible({timeout:60_000});
  const scenario_sha256=await page.locator('.authored-facts code').first().textContent();
  expect(scenario_sha256).toMatch(/^[0-9a-f]{64}$/);
  return {scenario_sha256};
}
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
    if(configuration.farm.document){
      const result=await registerAuthoredFarm(configuration.farm.document);
      configuration.farm.registration_sha256=result.scenario_sha256;
      process.stdout.write(JSON.stringify({event:'farm_registered',
        scenario_sha256:result.scenario_sha256})+'\n');
    }else{
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
    if(!configuration.workflow.financial)input.close();
    if(worker.event!=='worker_succeeded' || worker.job_id!==jobId)
      throw new Error('worker result does not match admitted job');
    configuration.job_id=jobId;configuration.run_id=worker.run_id;
    configuration.series=worker.series;
    configuration.financial=worker.financial;
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
    const registeredFarm=response.status()===200 &&
      new URL(response.url()).pathname==='/v1/farm-authored-inputs' &&
      Boolean(configuration.farm?.document);
    expect(response.request().method()).toBe(response.status()===202 || registeredFarm?'POST':'GET');
    expect([200,202]).toContain(response.status());
    expect(response.headers()['cache-control']).toBe('no-store');
    network.push({path:new URL(response.url()).pathname,status:response.status()});
  }
  expect(responses.length).toBe(configuration.workflow?(configuration.source_selection?14:8):authored?(configuration.farm?4:3):4);
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
  const financial=configuration.workflow?.financial?await financialContinuation():null;
  expect(errors).toEqual([]);
  process.stdout.write(JSON.stringify({stage:'verified',points:series.points.length,network,
    console_errors:0,gpu_capture_warnings:captureWarnings.length,...(financial?{financial}:{})})+'\n');
}catch(error){
  await mkdir(process.argv[3],{recursive:true});
  await page.screenshot({path:process.argv[3]+'/failure.png',fullPage:true}).catch(()=>{});
  throw error;
}finally{input.close();await context.close();await browser.close();}
async function documentReady(){await page.evaluate(()=>document.fonts.ready);}
