import { test,expect,type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

const crops=JSON.parse(readFileSync(new URL('./calculation-cycle-crop-prefix-recorded-responses.json',import.meta.url),'utf8'));
const stored=JSON.parse(readFileSync(new URL('./harvest-recorded-responses.json',import.meta.url),'utf8'));
const token='owned-synthetic-harvest-browser-test-only';
// Rebound metadata/times exercise the UI contract; these are not an observed joint database run.
function dataset(){
  const summary=JSON.parse(stored.bodies_raw_utf8.summary),crop=structuredClone(crops.long[0]);
  const ref=crop.reference,source=summary.reference.source;crop.result_id=source.result_id;crop.farm=structuredClone(summary.farm);
  Object.assign(ref,{payload_sha256:source.payload_sha256,input_root_sha256:source.input_root_sha256,
    artifact_sha256:source.artifact_sha256,artifact_ref:'crop-cycle-verified-artifact-v1:'+source.artifact_sha256,
    context_sha256:source.math_manifest_sha256,start_utc:'2026-10-01T00:00:00Z',end_utc:'2026-10-01T00:02:00Z',
    sample_count:3,event_count:4,steps:120,planned_steps:120});
  ref.input_validation.context_sha256=source.math_manifest_sha256;
  crop.summary.manifest.input_root_sha256=source.input_root_sha256;crop.summary.manifest.planned_steps=120;
  const records=crops.long.find((p:any)=>p.page?.kind==='samples').page.records.slice(0,3)
    .map((s:any,i:number)=>({...structuredClone(s),at:`2026-10-01T00:0${i}:00Z`}));
  const page={...structuredClone(crop),summary:null,page:{kind:'samples',offset:0,limit:7,total:3,next_offset:null,records}};
  return {summary,crop,page,first:JSON.parse(stored.bodies_raw_utf8['split-0']),last:JSON.parse(stored.bodies_raw_utf8['split-3'])};
}
type Data=ReturnType<typeof dataset>;
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
test.use({viewport:{width:1024,height:768}});test.setTimeout(60_000);
const applicationErrors=new WeakMap<Page,string[]>();
test.beforeEach(({page})=>{const errors:string[]=[];applicationErrors.set(page,errors);page.on('pageerror',error=>errors.push(error.message));});
test.afterEach(({page})=>{expect(applicationErrors.get(page)).toEqual([]);});
async function connect(page:Page,data:Data){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('calculation-cycle');
  for(const [key,value] of Object.entries({result_id:data.crop.result_id,...data.crop.farm}))
    await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(String(value));
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-at',data.page.page.records[0].at);
}
async function mock(page:Page,data:Data){
  const calls:string[]=[];let denied=false;
  await page.route('**/v1/crop-cycle-calculation-research-results/**',route=>route.fulfill({json:new URL(route.request().url()).searchParams.get('view')==='summary'?data.crop:data.page}));
  await page.route('**/v1/crop-harvest-research-results/**',async route=>{
    expect(route.request().headers().authorization).toBe('Bearer '+token);
    const q=new URL(route.request().url()).searchParams,view=q.get('view');calls.push(view==='summary'?'summary':'records:'+q.get('offset'));
    if(denied){await route.fulfill({status:403,json:{detail:'forbidden'}});return;}
    if(view!=='summary')expect(q.get('limit')).toBe('3');
    await route.fulfill({json:view==='summary'?data.summary:q.get('offset')==='0'?data.first:data.last,headers:{'cache-control':'no-store'}});
  });return {calls,deny:()=>{denied=true;}};
}
async function read(page:Page,data:Data){
  await page.getByLabel('저장 수확 결과 ID').fill(data.summary.result_id);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();
  await expect(page.locator('.harvest-replay')).toHaveAttribute('data-phase','ready');
}
test('stored allocation rows preserve quantities, exact fractions and link only the original same UTC',async({page})=>{
  const data=dataset(),api=await mock(page,data),errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await connect(page,data);await read(page,data);const panel=page.locator('.harvest-replay');
  await expect(panel).toHaveAttribute('data-offset','0');await expect(panel).toHaveAttribute('data-count','3');
  await expect(panel).toHaveAttribute('data-total','6');await expect(panel.getByText('부분 범위',{exact:true})).toBeVisible();
  for(const [i,row] of data.first.page.records.entries()){
    const tr=panel.locator(`[data-harvest-index="${i}"]`);
    await expect(tr).toHaveAttribute('data-end-at',row.mass.removal.end_at);
    await expect(tr.locator('[data-original-fresh]')).toHaveAttribute('data-raw-value',String(row.mass.fresh_matter.value));
    await expect(tr.locator('[data-unassigned-fresh]')).toHaveAttribute('data-raw-value',String(row.unassigned.quantities.fresh_matter.value));
    await expect(tr.locator('[data-unassigned-fresh]')).toHaveAttribute('data-unit','kg_FW/m2_floor');
    await tr.getByText('원 수량·정확 분수',{exact:true}).click();
    await expect(tr.locator('pre')).toContainText(row.unassigned.quantities.fresh_matter.exact.denominator);
    await tr.getByText('원 수량·정확 분수',{exact:true}).click();
  }
  await panel.locator('[data-harvest-index="1"]').getByRole('button',{name:'생장 시점 보기',exact:true}).click();
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-at','2026-10-01T00:01:00Z');
  await expect(page.locator('.coupled-viewer')).toBeFocused();
  const sample=data.page.page.records[1],canvas=page.locator('.coupled-canvas');
  await expect(canvas).toHaveAttribute('data-scene-at',sample.at);
  const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!);
  for(const [kind,field] of [['carbon','fruit_carbohydrate'],['number','fruit_number']] as const)
    expect(drawing[kind].map((q:{value:number})=>q.value)).toEqual(sample.state[field].map((q:{value:number})=>q.value));
  await expect(panel).toHaveAttribute('data-selected-at','2026-10-01T00:01:00Z');
  expect(api.calls).toEqual(['summary','records:0']);expect(errors).toEqual([]);
  const dir=process.env.OSSF_HARVEST_VIEW_EVIDENCE;
  if(dir){await panel.getByRole('region',{name:'저장 제거·배정 수치'}).evaluate(el=>{el.scrollLeft=0;});
    await panel.screenshot({path:join(dir,'harvest-desktop.png')});}
});
test('bounded pages retain whole stored totals and disable the unsampled event',async({page})=>{
  const data=dataset(),api=await mock(page,data);await connect(page,data);await read(page,data);
  await page.getByRole('button',{name:'다음 수확 범위',exact:true}).click();const panel=page.locator('.harvest-replay');
  await expect(panel).toHaveAttribute('data-offset','3');const unmatched=panel.locator('[data-harvest-index="3"]');
  await expect(unmatched.getByRole('button')).toBeDisabled();await expect(unmatched).toContainText('현재 생장 범위에 대응 시점 없음');
  await panel.locator('[data-harvest-index="4"]').getByRole('button',{name:'생장 시점 보기',exact:true}).click();
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-at','2026-10-01T00:02:00Z');
  await panel.getByText('전체 저장 배정 합계',{exact:true}).click();await expect(panel.locator('[data-whole-summary]')).toHaveAttribute('data-row-count','6');
  await panel.getByText('합성 관측 비교',{exact:true}).click();await expect(panel.locator('[data-comparison-status]').first()).toHaveAttribute('data-comparison-status','compared_synthetic_fixture');
  await page.getByRole('button',{name:'이전 수확 범위',exact:true}).click();await expect(panel).toHaveAttribute('data-offset','0');
  expect(api.calls).toEqual(['summary','records:0','records:3','records:0']);
});
test('a current rights denial removes the harvest values and the parent 3D and table',async({page})=>{
  const data=dataset(),api=await mock(page,data);await connect(page,data);await read(page,data);api.deny();
  await page.getByRole('button',{name:'수확 권리 다시 조회',exact:true}).click();
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);await expect(page.locator('.coupled-viewer')).toHaveCount(0);
  await expect(page.getByRole('alert')).toContainText('권한');
});
test('an unrelated but valid source hash is refused and clears the parent',async({page})=>{
  const data=dataset();data.crop.reference.payload_sha256='1'.repeat(64);data.page.reference.payload_sha256='1'.repeat(64);
  await mock(page,data);await connect(page,data);await page.getByLabel('저장 수확 결과 ID').fill(data.summary.result_id);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('확인할 수 없어');
  await expect(page.locator('.coupled-viewer')).toHaveCount(0);await expect(page.locator('[data-harvest-index]')).toHaveCount(0);
});
test('editing the lookup clears old rows before any new request',async({page})=>{
  const data=dataset(),api=await mock(page,data);await connect(page,data);await read(page,data);
  await page.getByText('저장 수확 결과 조회',{exact:true}).click();
  await page.getByLabel('저장 수확 결과 ID').fill('crop-harvest-registered-result-v1:'+'f'.repeat(64));
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);expect(api.calls).toHaveLength(2);
  await expect(page.locator('.coupled-viewer')).toHaveCount(1);
});
test('changing the parent lookup clears the harvest and its stored 3D immediately',async({page})=>{
  const data=dataset();await mock(page,data);await connect(page,data);await read(page,data);
  await page.getByText('저장 연구 결과 조회',{exact:true}).click();await page.getByLabel('작물 ID',{exact:true}).fill('other');
  await expect(page.locator('.harvest-replay')).toHaveCount(0);await expect(page.locator('.coupled-viewer')).toHaveCount(0);
});
test('a held confirmed past keeps its explicit hold and synthetic scope',async({page})=>{
  const data=dataset(),ref=data.crop.reference;
  Object.assign(ref,{status:'hold',steps:119,end_utc:'2026-10-01T00:03:00Z'});data.page.reference=structuredClone(ref);
  data.crop.summary.status='hold';data.crop.summary.hold={reason_code:'NUMERIC_HOLD',phase:'step-end',
    at:'2026-10-01T00:03:00Z',time_meaning:'solver_evaluation_time',last_confirmed:{...structuredClone(data.page.page.records[2]),phase:'step-end'}};
  function visit(value:any){if(value&&typeof value==='object')for(const [key,child] of Object.entries(value)){
    if(key==='source_status')value[key]='hold';else visit(child);}}
  visit(data);await mock(page,data);await connect(page,data);await read(page,data);
  await expect(page.locator('.harvest-replay')).toContainText('확인된 과거 · 계산 보류');
  await expect(page.locator('.harvest-replay')).toContainText('관문 미평가');await expect(page.locator('[data-harvest-index]')).toHaveCount(3);
});
test('canceling a late response prevents old data and permits a fresh read',async({page})=>{
  const data=dataset();await mock(page,data);let release!:()=>void,seen!:()=>void;
  const started=new Promise<void>(r=>seen=r),held=new Promise<void>(r=>release=r);
  await page.route('**/v1/crop-harvest-research-results/**',async route=>{seen();await held;await route.fulfill({json:data.summary}).catch(()=>{});});
  await connect(page,data);await page.getByLabel('저장 수확 결과 ID').fill(data.summary.result_id);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();await started;
  await page.getByRole('button',{name:'수확 조회 취소',exact:true}).click();release();
  await page.unroute('**/v1/crop-harvest-research-results/**');await mock(page,data);
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);await read(page,data);
});
test('account replacement during a late response cannot restore old rows or 3D',async({page})=>{
  const data=dataset();await mock(page,data);let release!:()=>void,seen!:()=>void;
  const started=new Promise<void>(r=>seen=r),held=new Promise<void>(r=>release=r);
  await page.route('**/v1/crop-harvest-research-results/**',async route=>{seen();await held;await route.fulfill({json:data.summary}).catch(()=>{});});
  await connect(page,data);await page.getByLabel('저장 수확 결과 ID').fill(data.summary.result_id);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();await started;
  const connection=page.locator('.connection');if(await connection.getAttribute('open')===null)await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill('owned-replaced-account-token-only');await page.getByRole('button',{name:'연결 설정',exact:true}).click();release();
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);await expect(page.locator('.coupled-viewer')).toHaveCount(0);
});
test('mobile keyboard and enlarged text keep the table accessible without page overflow',async({page})=>{
  const data=dataset();await mock(page,data);await page.setViewportSize({width:390,height:844});await connect(page,data);await read(page,data);
  const dir=process.env.OSSF_HARVEST_VIEW_EVIDENCE;
  if(dir)await page.locator('.harvest-replay').screenshot({path:join(dir,'harvest-mobile.png')});
  await page.addStyleTag({content:'html { font-size: 200% !important; }'});const panel=page.locator('.harvest-replay');
  const region=panel.getByRole('region',{name:'저장 제거·배정 수치'});await region.focus();await expect(region).toBeFocused();
  const button=panel.locator('[data-harvest-index="1"]').getByRole('button',{name:'생장 시점 보기',exact:true});
  await button.focus();await button.press('Enter');await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-at','2026-10-01T00:01:00Z');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth+1)).toBe(true);
  if(dir)await panel.screenshot({path:join(dir,'harvest-mobile-large-text.png')});
});
