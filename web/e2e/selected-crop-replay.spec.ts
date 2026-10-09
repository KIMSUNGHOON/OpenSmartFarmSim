import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import type {StoredCropSelection} from '../src/SelectedCropReplay';

const crops=JSON.parse(readFileSync(new URL('./calculation-cycle-crop-prefix-recorded-responses.json',import.meta.url),'utf8'));
const stored=JSON.parse(readFileSync(new URL('./harvest-recorded-responses.json',import.meta.url),'utf8'));
const token='owned-synthetic-selected-replay-test-only';
// Metadata and times rebound solely for this component contract; not a joint DB/HTTPS observation.
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
function choice(data:Data,kind:'growth'|'harvest'='harvest'):StoredCropSelection{
  const farm=structuredClone(data.crop.farm);
  return kind==='growth'?{kind:'calculation_cycle_v1',farm,result_id:data.crop.result_id}:
    {kind:'harvest_v1',farm,result_id:data.summary.result_id,parent_result_id:data.crop.result_id};
}
async function show(page:Page,selection:StoredCropSelection|null,credential:string|null=token){
  await page.evaluate(({selection,credential})=>window.__showSelectedCrop(credential,selection),{selection,credential});
}
async function mock(page:Page,data:Data,hold?:{harvest?:Promise<void>;entered?:()=>void}){
  const calls:{kind:string;view:string|null;offset:string|null;token:string|undefined}[]=[];let denied=false;
  await page.route('**/v1/crop-cycle-calculation-research-results/**',route=>{
    const url=new URL(route.request().url());calls.push({kind:'growth',view:url.searchParams.get('view'),offset:url.searchParams.get('offset'),token:route.request().headers().authorization});
    if(route.request().headers().authorization!=='Bearer '+token)return route.fulfill({status:403,json:{detail:'owned account refusal'}});
    expect(route.request().method()).toBe('GET');
    expect(decodeURIComponent(url.pathname.split('/').at(-1)!)).toBe(data.crop.result_id);
    for(const [key,value] of Object.entries(data.crop.farm))expect(url.searchParams.get(key)).toBe(value);
    return route.fulfill({json:url.searchParams.get('view')==='summary'?data.crop:data.page});
  });
  await page.route('**/v1/crop-harvest-research-results/**',async route=>{
    const url=new URL(route.request().url()),view=url.searchParams.get('view');
    calls.push({kind:'harvest',view,offset:url.searchParams.get('offset'),token:route.request().headers().authorization});
    expect(route.request().method()).toBe('GET');
    expect(decodeURIComponent(url.pathname.split('/').at(-1)!)).toBe(data.summary.result_id);
    for(const [key,value] of Object.entries(data.summary.farm))expect(url.searchParams.get(key)).toBe(value);
    if(view==='summary'&&hold?.harvest){hold.entered?.();await hold.harvest;}
    if(denied){await route.fulfill({status:403,json:{detail:'owned refusal'}}).catch(()=>{});return;}
    if(view!=='summary')expect(url.searchParams.get('limit')).toBe('3');
    await route.fulfill({json:view==='summary'?data.summary:url.searchParams.get('offset')==='0'?data.first:data.last}).catch(()=>{});
  });
  return {calls,deny:()=>{denied=true;}};
}
async function ready(page:Page,data:Data,harvest=true){
  await expect(page.locator('.cycle-replay')).toHaveAttribute('data-source-kind','calculation');
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-at',data.page.page.records[0].at);
  if(harvest)await expect(page.locator('.harvest-replay')).toHaveAttribute('data-phase','ready');
}
async function sameSample(page:Page,row:any){
  const canvas=page.locator('.coupled-canvas');await expect(canvas).toHaveAttribute('data-scene-at',row.at);
  const drawing=JSON.parse((await canvas.getAttribute('data-cohort-drawing'))!);
  for(const [kind,key] of [['carbon','fruit_carbohydrate'],['number','fruit_number']] as const)
    expect(drawing[kind].map((q:{value:number})=>q.value)).toEqual(row.state[key].map((q:{value:number})=>q.value));
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
}
const errors=new WeakMap<Page,string[]>();
test.use({viewport:{width:1024,height:768}});test.setTimeout(90_000);
test.beforeEach(async({page})=>{
  const messages:string[]=[];errors.set(page,messages);page.on('pageerror',e=>messages.push(e.message));
  page.on('console',message=>{if(message.type()==='error'&&!message.text().startsWith('Failed to load resource:'))messages.push(message.text());});
  await page.goto('/e2e/selected-crop-replay-harness.html');await page.waitForFunction(()=>typeof window.__showSelectedCrop==='function');
});
test.afterEach(({page})=>{expect(errors.get(page)).toEqual([]);});

test('a growth selection opens the exact verified parent without a format choice or harvest query',async({page})=>{
  const data=dataset(),api=await mock(page,data);await show(page,choice(data,'growth'));await ready(page,data,false);
  await sameSample(page,data.page.page.records[0]);expect(api.calls.map(v=>v.kind+':'+v.view)).toEqual(['growth:summary','growth:samples']);
  expect(api.calls.every(v=>v.token==='Bearer '+token)).toBe(true);await expect(page.getByLabel('저장 결과 판본')).toHaveCount(0);
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);
});
test('a harvest selection opens its same parent and exact stored quantities once without manual IDs',async({page})=>{
  const data=dataset(),api=await mock(page,data);await show(page,choice(data));await ready(page,data);
  const panel=page.locator('.harvest-replay');await expect(panel).toHaveAttribute('data-result-id',data.summary.result_id);
  for(const [i,row] of data.first.page.records.entries()){
    const tr=panel.locator(`[data-harvest-index="${i}"]`);
    await expect(tr.locator('[data-original-fresh]')).toHaveAttribute('data-raw-value',String(row.mass.fresh_matter.value));
    await expect(tr.locator('[data-unassigned-fresh]')).toHaveAttribute('data-unit',row.unassigned.quantities.fresh_matter.unit);
  }
  await panel.locator('[data-harvest-index="1"]').getByRole('button',{name:'생장 시점 보기',exact:true}).click();
  await sameSample(page,data.page.page.records[1]);expect(api.calls.map(v=>v.kind+':'+v.view)).toEqual(['growth:summary','growth:samples','harvest:summary','harvest:records']);
  expect(api.calls.every(v=>v.token==='Bearer '+token)).toBe(true);await expect(panel).toContainText('합성 환산');
  await expect(panel).toContainText('관문 미평가');
  const dir=process.env.OSSF_SELECTED_REPLAY_EVIDENCE;
  if(dir)await page.screenshot({path:join(dir,'selected-replay-component-desktop.png')});
});
test('equivalent copied selections and a stored page move do not repeat automatic reads',async({page})=>{
  const data=dataset(),api=await mock(page,data);await show(page,choice(data));await ready(page,data);
  await show(page,choice(data));await ready(page,data);await page.getByRole('button',{name:'다음 수확 범위',exact:true}).click();
  await expect(page.locator('.harvest-replay')).toHaveAttribute('data-offset','3');
  expect(api.calls.map(v=>v.kind+':'+v.view+':'+v.offset)).toEqual(['growth:summary:null','growth:samples:0','harvest:summary:null','harvest:records:0','harvest:records:3']);
});
test('invalid selection bindings are refused before any query and null clears a previously loaded scene',async({page})=>{
  const data=dataset(),api=await mock(page,data),valid=choice(data);
  for(const altered of [
    {...valid,result_id:data.crop.result_id},
    {...valid,parent_result_id:data.summary.result_id},
    {...valid,farm:{...valid.farm,registration_sha256:'A'.repeat(64)}},
    {...valid,farm:{...valid.farm,tenant_id:'foreign'}},
    {...valid,unexpected:true},
  ]){
    await show(page,altered);await expect(page.getByRole('alert')).toBeVisible();await expect(page.locator('.coupled-viewer')).toHaveCount(0);
  }
  expect(api.calls).toHaveLength(0);await show(page,choice(data));await ready(page,data);await show(page,null);
  await expect(page.locator('.cycle-replay,.harvest-replay,.coupled-canvas')).toHaveCount(0);
});
test('switching from harvest to growth during a late response cannot restore old harvest rows',async({page})=>{
  const data=dataset();let release!:()=>void,entered!:()=>void;
  const held=new Promise<void>(r=>release=r),started=new Promise<void>(r=>entered=r),api=await mock(page,data,{harvest:held,entered});
  await show(page,choice(data));await started;await show(page,choice(data,'growth'));await ready(page,data,false);release();
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);await sameSample(page,data.page.page.records[0]);
  expect(api.calls.filter(v=>v.kind==='harvest')).toHaveLength(1);
});
test('a current rights refusal or unrelated parent hash clears both selected views',async({page})=>{
  const data=dataset(),api=await mock(page,data);api.deny();await show(page,choice(data));
  await expect(page.getByRole('alert')).toBeVisible();await expect(page.locator('.coupled-viewer,[data-harvest-index]')).toHaveCount(0);
  data.crop.reference.payload_sha256='1'.repeat(64);data.page.reference.payload_sha256='1'.repeat(64);
  await page.unroute('**/v1/crop-harvest-research-results/**');await page.unroute('**/v1/crop-cycle-calculation-research-results/**');
  const fresh=await mock(page,data);await show(page,null);await expect(page.locator('.cycle-replay')).toHaveCount(0);await show(page,choice(data));
  await expect(page.getByRole('alert')).toBeVisible();await expect(page.locator('.coupled-viewer,[data-harvest-index]')).toHaveCount(0);
  expect(fresh.calls.filter(v=>v.kind==='harvest')).toHaveLength(1);
});
test('canceling the automatic harvest read refuses late data and preserves a fresh manual read',async({page})=>{
  const data=dataset();let release!:()=>void,entered!:()=>void;
  const held=new Promise<void>(r=>release=r),started=new Promise<void>(r=>entered=r);
  await mock(page,data,{harvest:held,entered});await show(page,choice(data));await started;
  await page.getByRole('button',{name:'수확 조회 취소',exact:true}).click();release();
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);
  await page.unroute('**/v1/crop-harvest-research-results/**');await page.unroute('**/v1/crop-cycle-calculation-research-results/**');await mock(page,data);
  await page.getByRole('button',{name:'저장 수확 조회',exact:true}).click();await expect(page.locator('.harvest-replay')).toHaveAttribute('data-phase','ready');
});
test('disconnecting the account during a late automatic response removes all old values',async({page})=>{
  const data=dataset();let release!:()=>void,entered!:()=>void;
  const held=new Promise<void>(r=>release=r),started=new Promise<void>(r=>entered=r);
  await mock(page,data,{harvest:held,entered});await show(page,choice(data));await started;
  await show(page,choice(data),null);await expect(page.locator('.cycle-replay,.harvest-replay,.coupled-canvas')).toHaveCount(0);release();
  await expect(page.locator('[data-harvest-index]')).toHaveCount(0);
});
test('account replacement during a late response rechecks the new account and cannot restore the old scene',async({page})=>{
  const data=dataset();let release!:()=>void,entered!:()=>void;
  const held=new Promise<void>(r=>release=r),started=new Promise<void>(r=>entered=r),api=await mock(page,data,{harvest:held,entered});
  await show(page,choice(data));await started;const replacement='owned-other-selected-replay-account-token';
  await show(page,choice(data),replacement);await expect(page.getByRole('alert')).toContainText('권한');release();
  await expect(page.locator('.coupled-viewer,[data-harvest-index]')).toHaveCount(0);
  expect(api.calls.filter(v=>v.kind==='growth').at(-1)?.token).toBe('Bearer '+replacement);
  expect(api.calls.filter(v=>v.kind==='harvest')).toHaveLength(1);
});
