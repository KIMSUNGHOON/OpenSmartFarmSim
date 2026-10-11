import { test,expect,type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';

// New envelopes are software fixtures containing the original owned recorded values, not live server evidence.
const recorded=JSON.parse(readFileSync(new URL('./joint-crop-climate-recorded-responses.json',import.meta.url),'utf8'));
const ID='11111111-1111-4111-8111-111111111111',AT='2026-10-10T12:30:00.123456Z',OBS='2026-10-10T12:30:00.123457Z';
const TOKEN='owned-prefix-screen-test';
const jobPath='**/v1/jobs/'+ID+'/crop-climate-joint-execution',prefixPath=jobPath+'/prefix';
function fixture(sequence=1,samples=2,events=2,kind:'completed'|'hold'='completed'){
  const records=recorded[kind],s=records[0];
  const {scenario_id,scenario_revision,registration_sha256,crop_id}=s.farm;
  const farm={scenario_id,scenario_revision,registration_sha256,crop_id};
  const selector={publication_sequence:sequence,head_sha256:String(sequence).repeat(64),proof_sha256:String(sequence+1).repeat(64)};
  const cp={...selector,artifact_sha256:null,status:'yielded',steps:15,planned_steps:16,counts:{samples,events},
    computed_through_utc:'2026-10-01T00:00:30.123456Z',checkpoint_recorded_at:AT};
  const job={job_id:ID,stage:'simulation',state:'simulating',attempt_count:1,max_attempts:3,created_at:AT,updated_at:AT,reason_code:null};
  const summary={schema_version:'joint-crop-climate-prefix-replay-v1',scope:'synthetic_joint_crop_climate_math_only',
    claim_scope:'synthetic_joint_crop_climate_confirmed_prefix_only',G0_G4:'not_assessed',job,cancel_requested:false,observed_at:OBS,prefix_status:'accepted',
    reference:{selector,checkpoint:cp,checkpoint_attempt:1,study_id:s.study_id,revision:s.revision,farm:s.farm,
      input:s.reference.input,manifest:s.summary.manifest,time_grid:s.reference.time_grid},
    summary:{counts:{samples,events},last_sample_utc:samples?records[1].page.records[samples-1].time.at:null,
      last_event_utc:events?records[2].page.records[events-1].time.at:null},page:null};
  const progress={version:'joint-crop-climate-execution-query-v1',scope:summary.scope,G0_G4:'not_assessed',job,
    cancel_requested:false,observed_at:OBS,checkpoint_status:'current',checkpoint:cp,result:null};
  const page=(kind:'samples'|'events',start=0,limit=kind==='samples'?64:8)=>{
    const total=kind==='samples'?samples:events,rows=records[kind==='samples'?1:2].page.records;
    return {...summary,summary:null,page:{kind,start,limit,total,next_offset:start+limit<total?start+limit:null,records:rows.slice(start,Math.min(total,start+limit))}};
  };
  const final=(kind:'completed'|'hold')=>{const s=recorded[kind][0],a=s.reference.artifact;
    return {...progress,job:{...job,state:kind==='completed'?'succeeded':'hold',reason_code:kind==='hold'?'joint_numerical_hold':null},checkpoint:{...cp,status:kind,artifact_sha256:a.sha256,
      steps:a.steps,planned_steps:a.planned_steps,computed_through_utc:s.reference.last_confirmed.at,
      counts:{samples:a.sample_count,events:a.event_count}},result:{result_id:s.result_id,farm:s.farm,status:kind}};};
  return {farm,summary,progress,page,final,job};
}
test.setTimeout(30_000);
type Diagnostics={console:{text:string;url:string}[];requests:string[];responses:{url:string;status:number}[]};
const diagnostics=new WeakMap<Page,Diagnostics>();
test.beforeEach(async({page})=>{const value:Diagnostics={console:[],requests:[],responses:[]};diagnostics.set(page,value);
  page.on('pageerror',e=>value.console.push({text:e.message,url:''}));
  page.on('console',e=>{if(['error','warning'].includes(e.type()))value.console.push({text:e.text(),url:e.location().url});});
  page.on('request',r=>{const url=new URL(r.url());if(url.pathname.startsWith('/v1/'))value.requests.push(r.method()+' '+url.pathname+url.search);});
  page.on('response',r=>{if(new URL(r.url()).pathname.includes('/crop-climate-joint-execution'))value.responses.push({url:r.url(),status:r.status()});});
});
test.afterEach(async({page},info)=>{const value=diagnostics.get(page)!;
  const expectedStatus=info.title.includes('P5 05 rejection ')?Number(info.title.match(/rejection (\d+)/)?.[1]):
    info.title.includes('P5 06 ')?503:info.title.includes('P5 07 ')?409:0;
  const driverWarnings=value.console.filter(e=>/^\[\.WebGL-0x[0-9a-f]+\]GL Driver Message \(OpenGL, Performance, GL_CLOSE_PATH_NV, High\): GPU stall due to ReadPixels(?: \(this message will no longer repeat\))?$/.test(e.text));
  const expectedStatuses=info.title.startsWith('P6 00')?[503]:info.title.startsWith('P6 01')?[503,422]:info.title.startsWith('P6 02')?[403]:[expectedStatus];
  const expectedHttpErrors=value.console.filter(e=>expectedStatuses.some(status=>status>0&&
    e.text.startsWith('Failed to load resource: the server responded with a status of '+status+' ')
    &&value.responses.some(r=>r.url===e.url&&r.status===status)));
  const unexpected=value.console.filter(e=>!driverWarnings.includes(e)&&!expectedHttpErrors.includes(e));
  if(process.env.OSSF_JOINT_VIEW_EVIDENCE)await writeFile(join(process.env.OSSF_JOINT_VIEW_EVIDENCE,'browser-check.json'),JSON.stringify({
    title:info.title,status:info.status,console:value.console,driverWarnings,expectedHttpErrors,unexpected,requests:value.requests,responses:value.responses,
    selected_UTC:await page.locator('.joint-prefix-viewer').count()?await page.locator('.joint-prefix-viewer').getAttribute('data-selected-at'):null}));
  expect(unexpected).toEqual([]);const cdp=await page.context().newCDPSession(page);
  try{await cdp.send('HeapProfiler.collectGarbage');}finally{await cdp.detach();}});
async function enter(page:Page,d=fixture()){
  await page.clock.install();await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(TOKEN);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();await page.getByLabel('저장 결과 판본').selectOption('joint-execution');
  const labels={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
  for(const [key,value] of Object.entries({job_id:ID,...d.farm}))await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();
}
async function routes(page:Page,d=fixture()){
  const order:string[]=[];
  await page.route(jobPath,r=>{order.push('progress');return r.fulfill({json:d.progress});});
  await page.route(prefixPath,r=>{order.push('summary');return r.fulfill({json:d.summary});});
  await page.route(prefixPath+'/*?*',r=>{
    const url=new URL(r.request().url()),kind=url.pathname.endsWith('/events')?'events':'samples';order.push(kind);
    expect(url.searchParams.get('publication_sequence')).toBe(String(d.summary.reference.selector.publication_sequence));
    expect(url.searchParams.get('head_sha256')).toBe(d.summary.reference.selector.head_sha256);
    expect(url.searchParams.get('proof_sha256')).toBe(d.summary.reference.selector.proof_sha256);
    expect(r.request().headers().authorization).toBe('Bearer '+TOKEN);
    return r.fulfill({json:d.page(kind,Number(url.searchParams.get('start')),Number(url.searchParams.get('limit')))});
  });return order;
}
async function snapshot(page:Page,name:string){
  const root=process.env.OSSF_JOINT_VIEW_EVIDENCE;if(!root)return;
  const scene=page.locator('.joint-prefix .coupled-top-grid'),prefix=page.locator('.joint-prefix');
  if(await scene.count())await scene.evaluate(e=>e.scrollIntoView({block:'start'}));
  else if(await prefix.count())await prefix.evaluate(e=>e.scrollIntoView({block:'start'}));
  await page.screenshot({path:join(root,name+'.png'),fullPage:false});
  const html=await page.evaluate(()=>{const clone=document.documentElement.cloneNode(true) as HTMLElement;
    clone.querySelectorAll('script,.connection').forEach(e=>e.remove());
    clone.querySelectorAll('link[href]').forEach(e=>{const url=new URL(e.getAttribute('href')!,location.href);if(url.origin===location.origin)e.setAttribute('href',url.pathname);});
    const originals=document.querySelectorAll('select');clone.querySelectorAll('select').forEach((e,i)=>e.querySelectorAll('option').forEach(o=>{
      if(o.value===originals[i]!.value)o.setAttribute('selected','');else o.removeAttribute('selected');}));return '<!doctype html>'+clone.outerHTML;});
  await writeFile(join(root,name+'.html'),html);
}
test('P6 00 progress503-first still reads an authorized complete prefix on one polling chain',async({page})=>{
  const d=fixture(),order=await routes(page,d);let reads=0;
  await page.route(jobPath,r=>{reads++;order.push('progress-unavailable');return r.fulfill({status:503,json:{}});});
  await enter(page,d);const viewer=page.locator('.joint-prefix-viewer'),row=recorded.completed[1].page.records[1];
  await expect(viewer).toHaveAttribute('data-selected-at',row.time.at);
  await expect(viewer.locator('.coupled-canvas')).toHaveAttribute('data-scene-at',row.time.at);
  await expect.poll(()=>viewer.locator('.coupled-canvas').evaluate(e=>Number((e as HTMLElement).dataset.drawCalls))).toBeGreaterThan(0);
  expect(order).toEqual(['progress-unavailable','summary','events','samples']);expect(reads).toBe(1);
  await page.clock.fastForward(10_000);await expect.poll(()=>reads).toBe(2);
  await expect.poll(()=>order.length).toBe(8);expect(order.slice(4)).toEqual(['progress-unavailable','summary','events','samples']);
});
test('P6 01 progress503 cannot bypass a current prefix rights rejection',async({page})=>{
  const d=fixture();let progressReads=0,prefixReads=0;await routes(page,d);
  await page.route(jobPath,r=>{progressReads++;return r.fulfill({status:503,json:{}});});
  await page.route(prefixPath,r=>{prefixReads++;return r.fulfill({status:422,json:{}});});
  await enter(page,d);await expect(page.getByLabel('계산 진행 상태')).toContainText('조회 보류');
  await expect(page.locator('.joint-prefix')).toHaveCount(0);await page.clock.fastForward(60_000);
  expect(progressReads).toBe(1);expect(prefixReads).toBe(1);
});
test('P6 02 progress authorization denial never queries the prefix',async({page})=>{
  const d=fixture(),order=await routes(page,d);await page.route(jobPath,r=>r.fulfill({status:403,json:{}}));
  await enter(page,d);await expect(page.getByLabel('계산 진행 상태')).toContainText('조회 보류');
  await page.clock.fastForward(60_000);expect(order).toEqual([]);await expect(page.locator('.joint-prefix')).toHaveCount(0);
});
test('P5 00 original UTC values, fifty cohorts, chart and actual WebGL stay together',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));const order=await routes(page);await enter(page);
  const root=page.getByLabel('계산 중 확정 생장 결과'),viewer=root.locator('.joint-prefix-viewer'),row=recorded.completed[1].page.records[1];
  await expect(viewer).toHaveAttribute('data-selected-at',row.time.at);
  const canvas=root.locator('.coupled-canvas');await expect(canvas).toHaveAttribute('data-scene-at',row.time.at);
  await expect(root.locator('.joint-history')).toHaveAttribute('data-selected-at',row.time.at);
  await expect(root.locator('.coupled-readout [data-metric=leaf_area_index]')).toHaveAttribute('data-raw-value',String(row.value.derived.leaf_area_index.value));
  expect(await canvas.evaluate(e=>Number((e as HTMLElement).dataset.leafSurfaceArea))).toBeCloseTo(row.value.derived.leaf_area_index.value,8);
  const drawing=await canvas.evaluate(e=>JSON.parse((e as HTMLElement).dataset.cohortDrawing!));
  expect(drawing.carbon.map((v:any)=>v.value)).toEqual(row.value.cohort_state.fruit_carbohydrate.map((q:any)=>q.value));
  expect(drawing.number.map((v:any)=>v.value)).toEqual(row.value.cohort_state.fruit_number.map((q:any)=>q.value));
  expect(await canvas.evaluate(e=>Number((e as HTMLElement).dataset.drawCalls))).toBeGreaterThan(0);
  await expect(root.locator('.coupled-cohort-table tbody tr')).toHaveCount(50);
  await expect(root.locator('.cycle-events article')).toHaveCount(2);expect(order).toEqual(['progress','summary','events','samples']);
  await snapshot(page,'prefix-active');await page.getByRole('button',{name:'이전 확정 시점',exact:true}).click();
  const first=recorded.completed[1].page.records[0];await expect(canvas).toHaveAttribute('data-scene-at',first.time.at);
  await expect(root.locator('.joint-history')).toHaveAttribute('data-selected-at',first.time.at);expect(errors).toEqual([]);
});
test('P5 01 replaces a selector atomically and schedules the next poll after all pages',async({page})=>{
  const a=fixture(1,1,1),b=fixture(2,2,2);let phase=0,progressReads=0;let release:()=>void=()=>{};
  const wait=new Promise<void>(r=>{release=r;});await routes(page,a);
  await page.route(jobPath,r=>{progressReads++;return r.fulfill({json:a.progress});});
  await page.route(prefixPath,r=>r.fulfill({json:phase?b.summary:a.summary}));
  await page.route(prefixPath+'/*?*',async r=>{const kind=r.request().url().includes('/events?')?'events':'samples';
    const value=phase?b:a;if(phase&&kind==='samples')await wait;await r.fulfill({json:value.page(kind)}).catch(()=>{});});
  await enter(page,a);const root=page.getByLabel('계산 중 확정 생장 결과');await expect(root).toHaveAttribute('data-prefix-sequence','1');
  await page.clock.pauseAt(await page.evaluate(()=>Date.now()+1_000));
  phase=1;await page.clock.fastForward(10_000);await expect.poll(()=>progressReads).toBe(2);await page.clock.fastForward(20_000);
  await expect(root).toHaveAttribute('data-prefix-sequence','1');expect(progressReads).toBe(2);release();
  await expect(root).toHaveAttribute('data-prefix-sequence','2');await page.clock.fastForward(9_999);expect(progressReads).toBe(2);
  await page.clock.fastForward(1);await expect.poll(()=>progressReads).toBe(3);
});
test('P5 02 unchanged confirmed selector keeps the selected original UTC',async({page})=>{
  const order=await routes(page);await enter(page);await expect(page.locator('.joint-prefix-viewer')).toBeVisible();
  await page.getByRole('button',{name:'이전 확정 시점',exact:true}).click();const at=recorded.completed[1].page.records[0].time.at;
  await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();await expect.poll(()=>order.length).toBe(8);
  await expect(page.locator('.joint-prefix-viewer')).toHaveAttribute('data-selected-at',at);
});
test('P5 02b a new selector without a new sample preserves the selected UTC',async({page})=>{
  let phase=0;await routes(page);await page.route(prefixPath,r=>r.fulfill({json:fixture(phase?2:1).summary}));
  await page.route(prefixPath+'/*?*',r=>r.fulfill({json:fixture(phase?2:1).page(r.request().url().includes('/events?')?'events':'samples')}));
  await enter(page);await expect(page.locator('.joint-prefix-viewer')).toBeVisible();await page.getByRole('button',{name:'이전 확정 시점',exact:true}).click();
  phase=1;await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();await expect(page.locator('.joint-prefix')).toHaveAttribute('data-prefix-sequence','2');
  await expect(page.locator('.joint-prefix-viewer')).toHaveAttribute('data-selected-at',recorded.completed[1].page.records[0].time.at);
});
for(const state of ['none','ready'])test(`P5 03 ${state} has no invented sample or page query`,async({page})=>{
  const d=fixture(1,0,0),order=await routes(page,d);
  if(state==='none')await page.route(prefixPath,r=>r.fulfill({json:{...d.summary,prefix_status:'none',reference:null,summary:null}}));
  else Object.assign(d.summary.reference.checkpoint,{status:'ready',steps:0,computed_through_utc:null});
  await enter(page,d);await expect.poll(()=>order.filter(x=>x==='progress').length).toBe(1);
  await expect(page.getByText(state==='none'?'표시 가능한 확정 생장 시점을 기다립니다.':'아직 확정된 생장 시점이 없습니다',{exact:true})).toBeVisible();
  await expect(page.locator('.joint-prefix-viewer')).toHaveCount(0);await expect(page.locator('.coupled-canvas')).toHaveCount(0);
  expect(order.filter(x=>x==='events'||x==='samples')).toEqual([]);await snapshot(page,'prefix-empty-'+state);
});
test('P5 04 an event without a saved sample does not create a growth frame',async({page})=>{
  const d=fixture(1,0,1),order=await routes(page,d);await enter(page,d);
  await expect(page.locator('.joint-prefix .cycle-events article')).toHaveCount(1);await expect(page.locator('.joint-prefix-viewer')).toHaveCount(0);
  expect(order).toEqual(['progress','summary','events']);
});
for(const fault of [401,403,422,'malformed'] as const)test(`P5 05 rejection ${fault} clears original values and stops polling`,async({page})=>{
  let reject=false,count=0;await routes(page);await page.route(prefixPath,r=>{count++;
    return reject?r.fulfill(fault==='malformed'?{json:{...fixture().summary,G0_G4:'passed'}}:{status:fault,json:{}}):r.fulfill({json:fixture().summary});});
  await enter(page);await expect(page.locator('.joint-prefix-viewer')).toBeVisible();reject=true;
  await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();await expect(page.getByLabel('계산 진행 상태')).toContainText('조회 보류');
  await expect(page.locator('.joint-prefix')).toHaveCount(0);await page.clock.fastForward(60_000);expect(count).toBe(2);
  await expect(page.getByRole('button',{name:'서버 계산 취소',exact:true})).toBeEnabled();if(fault===422)await snapshot(page,'prefix-blocked');
});
test('P5 06 transient page 503 keeps the previous whole snapshot marked as historical',async({page})=>{
  let phase=0;await routes(page,fixture(1,1,1));await page.route(prefixPath,r=>r.fulfill({json:fixture(phase?2:1,phase?2:1,phase?2:1).summary}));
  await page.route(prefixPath+'/*?*',r=>r.fulfill(phase?{status:503,json:{}}:{json:fixture(1,1,1).page(r.request().url().includes('/events?')?'events':'samples')}));
  await enter(page);await expect(page.locator('.joint-prefix')).toHaveAttribute('data-prefix-sequence','1');phase=1;
  await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();await expect(page.getByLabel('계산 진행 상태')).toContainText('연결 끊김');
  await expect(page.locator('.joint-prefix')).toHaveAttribute('data-prefix-sequence','1');await expect(page.locator('.joint-prefix')).toContainText('마지막으로 확인한 확정 결과');
});
test('P5 07 selector conflict removes the prefix before reading terminal state',async({page})=>{
  let phase=0;const d=fixture();await routes(page,d);
  await page.route(jobPath,r=>r.fulfill({json:phase===2?d.final('completed'):d.progress}));
  await page.route(prefixPath+'/*?*',r=>r.fulfill(phase?{status:409,json:{}}:{json:d.page(r.request().url().includes('/events?')?'events':'samples')}));
  await enter(page);await expect(page.locator('.joint-prefix')).toBeVisible();phase=1;await page.getByRole('button',{name:'지금 다시 확인',exact:true}).click();
  await expect(page.locator('.joint-prefix')).toHaveCount(0);await expect(page.getByRole('alert')).toContainText('확정 판본');phase=2;
  await page.clock.fastForward(20_000);await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기'})).toBeVisible();
});
test('P5 08 cancel is independent of an in-flight prefix page and discards its late values',async({page})=>{
  const d=fixture();let waiting=false,canceled=false;let release:()=>void=()=>{};const wait=new Promise<void>(r=>{release=r;});
  await routes(page,d);await page.route(jobPath,r=>r.fulfill({json:canceled?{...d.progress,job:{...d.job,state:'canceled'},checkpoint_status:'none',checkpoint:null}:d.progress}));
  await page.route(prefixPath+'/*?*',async r=>{waiting=true;await wait;await r.fulfill({json:d.page('events')}).catch(()=>{});});
  await page.route(jobPath+'/cancel',r=>{canceled=true;return r.fulfill({json:{version:'joint-crop-climate-execution-cancel-v1',scope:d.summary.scope,
    G0_G4:'not_assessed',job:{...d.job,state:'canceled'},cancel_requested:false,cancel_accepted:true,observed_at:OBS}});});
  await enter(page);await expect.poll(()=>waiting).toBe(true);await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();
  await expect.poll(()=>canceled).toBe(true);release();await expect(page.getByRole('heading',{name:'취소됨',exact:true})).toBeVisible();
  await expect(page.locator('.joint-prefix')).toHaveCount(0);
});
test('P5 09 hiding discards the snapshot and resumes one current sequence',async({page})=>{
  const order=await routes(page);await enter(page);await expect(page.locator('.joint-prefix')).toBeVisible();
  await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,value:'hidden'});document.dispatchEvent(new Event('visibilitychange'));});
  await expect(page.locator('.joint-prefix')).toHaveCount(0);await page.clock.fastForward(60_000);expect(order.length).toBe(4);
  await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,value:'visible'});document.dispatchEvent(new Event('visibilitychange'));});
  await expect(page.locator('.joint-prefix')).toBeVisible();expect(order.length).toBe(8);
});
for(const change of ['selection','account'])test(`P5 10 late prefix response after ${change} cannot restore the scene`,async({page})=>{
  let waiting=false;let release:()=>void=()=>{};const wait=new Promise<void>(r=>{release=r;});await routes(page);
  await page.route(prefixPath,async r=>{waiting=true;await wait;await r.fulfill({json:fixture().summary}).catch(()=>{});});await enter(page);
  await expect.poll(()=>waiting).toBe(true);
  if(change==='selection'){
    await page.locator('.joint-execution>.crop-lookup summary').click();await page.getByLabel('계산 농장 판본',{exact:true}).fill('r2');
  }else{
    if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
    await page.getByLabel('접근 토큰').fill(TOKEN+'-changed');await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  }
  release();await expect(page.locator('.joint-prefix')).toHaveCount(0);await expect(page.getByLabel('계산 진행 상태')).toHaveCount(0);
});
for(const kind of ['completed','hold'] as const)test(`P5 11 ${kind} closes the prefix and opens the original stored result`,async({page})=>{
  const d=fixture(1,2,2,kind);let phase=0,progressReads=0;const order=await routes(page,d);
  await page.route(jobPath,r=>{progressReads++;return r.fulfill({json:phase?d.final(kind):d.progress});});
  await page.route('**/v1/crop-climate-joint-research-results/**',r=>{const q=new URL(r.request().url()).searchParams;
    return r.fulfill({json:recorded[kind][q.get('view')==='summary'?0:q.get('kind')==='events'?2:1]});});
  await enter(page,d);await expect(page.locator('.joint-prefix')).toBeVisible();phase=1;await page.clock.fastForward(10_000);
  await expect(page.locator('.joint-prefix')).toHaveCount(0);await page.getByRole('button',{name:'같은 저장 결과 3D 열기'}).click();
  await expect(page.locator('.joint-viewer')).toHaveAttribute('data-result-id',recorded[kind][0].result_id);
  await expect(page.locator('.joint-viewer')).toHaveAttribute('data-selected-at',recorded[kind][1].page.records[0].time.at);
  await page.clock.fastForward(60_000);expect(order).toEqual(['summary','events','samples']);expect(progressReads).toBe(2);
});
test('P5 12 mobile labels, keyboard and bounded tables have no page overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await routes(page);await enter(page);
  await expect(page.locator('.joint-prefix-viewer')).toBeVisible();const slider=page.getByLabel('확정 생장 시점 선택');await slider.focus();await slider.press('ArrowLeft');
  await expect(page.locator('.joint-prefix-viewer')).toHaveAttribute('data-selected-at',recorded.completed[1].page.records[0].time.at);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await snapshot(page,'prefix-mobile');
});
