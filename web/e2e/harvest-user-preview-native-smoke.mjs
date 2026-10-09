// Actual current user origin and App; no routes or response substitutions.
import {createInterface} from 'node:readline';
import {mkdir,writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {chromium,expect as assertions} from '@playwright/test';
const expect=assertions.configure({timeout:40_000}),lines=createInterface({input:process.stdin})[Symbol.asyncIterator]();
const input=await lines.next();if(input.done)throw Error('owned preview input missing');
const {data,token}=JSON.parse(input.value),origin=process.argv[2],directory=process.argv[3];
await mkdir(directory,{recursive:true});
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader','--no-zygote','--in-process-gpu',
  '--single-process','--js-flags=--max-old-space-size=32 --max-semi-space-size=1','--num-raster-threads=1','--disable-gpu-shader-disk-cache']});
const page=await browser.newPage({viewport:{width:1024,height:768}}),errors=[],network=[],pending=[];
page.on('pageerror',e=>errors.push(e.message));
page.on('response',response=>{
  const u=new URL(response.url());if(!u.pathname.includes('-research-results/'))return;
  pending.push((async()=>{const raw=await response.body();network.push({status:response.status(),bytes:raw.length,
    sha256:createHash('sha256').update(raw).digest('hex'),endpoint:u.pathname.includes('/crop-harvest-')?'harvest':'crop',
    view:u.searchParams.get('view')??'summary',offset:u.searchParams.get('offset')});})());
});
const cdp=await page.context().newCDPSession(page);let collecting=false;
const timer=setInterval(async()=>{if(collecting)return;collecting=true;try{await cdp.send('HeapProfiler.collectGarbage');}catch{}finally{collecting=false;}},250);timer.unref();
try{
  await page.goto(origin);await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('calculation-cycle');
  if(await page.locator('.crop-lookup').getAttribute('open')===null)await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
  for(const [key,value] of Object.entries({result_id:data.summary.result_id,...data.summary.farm}))await page.getByLabel(labels[key],{exact:true}).fill(value);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-window-phase','ready');
  await page.getByLabel('저장 수확 결과 ID').fill(data.harvest_result_id);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();
  const panel=page.locator('.harvest-replay');await expect(panel).toHaveAttribute('data-phase','ready');
  await expect(panel).toHaveAttribute('data-total','47813');await expect(panel).toHaveAttribute('data-count','3');
  let selected;
  for(let i=0;i<3;i++){
    const original=data.rows[i],row=panel.locator('[data-harvest-index="'+i+'"]');
    await expect(row).toHaveAttribute('data-end-at',original.mass.removal.end_at);
    await expect(row.locator('[data-original-fresh]')).toHaveAttribute('data-raw-value',String(original.mass.fresh_matter.value));
    await expect(row.locator('[data-original-fresh]')).toHaveAttribute('data-unit',original.mass.fresh_matter.unit);
    const index=data.samples.findIndex(sample=>sample.at===original.mass.removal.end_at);
    if(selected===undefined&&index>=0){
      await row.getByRole('button',{name:'생장 시점 보기',exact:true}).click();selected=index;
      const canvas=page.locator('.coupled-canvas'),sample=data.samples[index];
      await expect(canvas).toHaveAttribute('data-scene-at',sample.at);
      const drawing=JSON.parse(await canvas.getAttribute('data-cohort-drawing'));
      expect(drawing.carbon.map(q=>q.value)).toEqual(sample.state.fruit_carbohydrate.map(q=>q.value));
      expect(drawing.number.map(q=>q.value)).toEqual(sample.state.fruit_number.map(q=>q.value));
      expect(Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-sample.lai.value)).toBeLessThanOrEqual(Math.max(1e-8,sample.lai.value*1e-6));
      expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
      expect(await canvas.evaluate(c=>{const gl=c.getContext('webgl2');return !!gl&&!gl.isContextLost();})).toBe(true);
    }
  }
  expect(selected).toBeDefined();expect(data.summary.reference.sample_count).toBe(47809);
  await page.screenshot({path:directory+'/full-harvest-user-desktop.png',fullPage:false,mask:[page.locator('input,textarea')]});
  await Promise.all(pending);expect(errors).toEqual([]);expect(network).toHaveLength(4);
  expect(network.every(r=>r.status===200&&r.bytes<=2*1024**2)).toBe(true);
  const report={accepted:true,actual_origin:origin,actual_WebGL:true,sample_count:47809,harvest_total:47813,
    harvest_rows_checked:3,selected_sample_index:selected,same_UTC_original_50_C_N_and_LAI:true,network,errors,
    routes_or_response_substitutions:0,realtime_progress:false,G0_G4:'not_assessed'};
  await writeFile(directory+'/browser.private.json',JSON.stringify(report),{mode:0o600});
  process.stdout.write(JSON.stringify({accepted:true,actual_origin:origin,actual_WebGL:true,harvest_rows_checked:3})+'\n');
}finally{clearInterval(timer);await browser.close();}
