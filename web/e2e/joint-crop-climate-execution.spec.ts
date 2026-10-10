import { test,expect,type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { join } from 'node:path';
declare global { interface Window { executionReads:{start:number;end:number}[] } }
const recorded=JSON.parse(readFileSync(new URL('./joint-crop-climate-recorded-responses.json',import.meta.url),'utf8'));
const ID='11111111-1111-4111-8111-111111111111',AT='2026-10-10T05:00:00.123456Z',OBS='2026-10-10T05:00:00.123457Z';
const TOKEN='owned-joint-execution-screen-test';
const path='**/v1/jobs/'+ID+'/crop-climate-joint-execution';
function data(kind:'completed'|'hold'='completed'){
  const rows=recorded[kind],s=rows[0],a=s.reference.artifact;
  const {scenario_id,scenario_revision,registration_sha256,crop_id}=s.farm;
  const farm={scenario_id,scenario_revision,registration_sha256,crop_id};
  const request={study_id:'owned-execution-ui',revision:'r1',farm,
    input:{schema_version:'joint-crop-climate-input-source-v1',program_id:'program',source_sha256:'b'.repeat(64),
      context_sha256:'c'.repeat(64),time_binding_sha256:'d'.repeat(64),evidence_sha256:'e'.repeat(64)},
    rights:{schema_version:'joint-crop-climate-input-rights-v1',declaration_id:'owned',revision:'r1',input_source_sha256:'b'.repeat(64),
      available_at:AT,redistribute:false,ownership_asserted:true,access:true,store:true,transform:true,use:true,display:true}};
  const job=(state='queued')=>({job_id:ID,stage:'simulation',state,attempt_count:state==='queued'?0:1,max_attempts:3,
    created_at:AT,updated_at:AT,reason_code:state==='hold'?'joint_numerical_hold':null});
  const queued={version:'joint-crop-climate-execution-query-v1',scope:'synthetic_joint_crop_climate_math_only',G0_G4:'not_assessed',
    job:job(),cancel_requested:false,observed_at:OBS,checkpoint_status:'none',checkpoint:null,result:null};
  const active={...queued,job:job('simulating'),checkpoint_status:'current',checkpoint:{head_sha256:'1'.repeat(64),
    proof_sha256:'2'.repeat(64),artifact_sha256:null,status:'yielded',steps:7,planned_steps:16,counts:{samples:3,events:1},
    computed_through_utc:'2026-10-01T00:00:14.123456Z',checkpoint_recorded_at:AT,publication_sequence:2}};
  const final={...active,job:job(kind==='completed'?'succeeded':'hold'),checkpoint:{...active.checkpoint,status:kind,
    steps:a.steps,planned_steps:a.planned_steps,artifact_sha256:a.sha256},result:{result_id:s.result_id,farm:s.farm,status:kind}};
  const cancel=(state='simulating',accepted=true)=>({version:'joint-crop-climate-execution-cancel-v1',scope:queued.scope,G0_G4:'not_assessed',
    job:job(state),cancel_requested:state==='simulating',cancel_accepted:accepted,observed_at:OBS});
  return {rows,farm,request,job,queued,active,final,cancel};
}
test.setTimeout(30_000);
test.afterEach(async({page})=>{const cdp=await page.context().newCDPSession(page);
  try{await cdp.send('HeapProfiler.collectGarbage');}finally{await cdp.detach();}});
async function enter(page:Page){
  // This older response set represents the execution server with prefix routes disabled.
  await page.route('**/v1/jobs/*/crop-climate-joint-execution/prefix',r=>r.fulfill({status:404,json:{}}));
  await page.clock.install();await page.addInitScript(()=>{
    const w=window;w.executionReads=[];const original=window.fetch;
    window.fetch=async(...args)=>{const path=String(args[0]),start=Date.now(),response=await original(...args);
      if(/\/crop-climate-joint-execution$/.test(path))w.executionReads.push({start,end:Date.now()});return response;};
  });await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(TOKEN);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption('joint-execution');
  await expect(page.getByRole('heading',{name:'작물·기후 계산 상태',exact:true})).toBeVisible();
}
async function upload(page:Page,value:unknown=data().request){
  await page.getByLabel('검토된 계산 접수 파일').setInputFiles({name:'owned-request.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
  await expect(page.getByRole('button',{name:'계산 접수',exact:true})).toBeEnabled();
}
async function attach(page:Page,d=data()){
  const detail=page.locator('.joint-execution>.crop-lookup');if(await detail.getAttribute('open')===null)await detail.locator('summary').click();
  const labels={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
  for(const [key,value] of Object.entries({job_id:ID,...d.farm}))await page.getByLabel(labels[key as keyof typeof labels],{exact:true}).fill(value);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();
}
async function saved(page:Page,d=data()){
  const calls:string[]=[];await page.route('**/v1/crop-climate-joint-research-results/**',async route=>{
    const q=new URL(route.request().url()).searchParams;calls.push(route.request().url());
    expect(q.get('scenario_id')).toBe(d.farm.scenario_id);expect(q.get('registration_sha256')).toBe(d.farm.registration_sha256);
    await route.fulfill({json:d.rows[q.get('view')==='summary'?0:q.get('kind')==='events'?2:1]});
  });return calls;
}
async function snapshot(page:Page,name:string){
  const root=process.env.OSSF_JOINT_VIEW_EVIDENCE;if(!root)return;
  await page.screenshot({path:join(root,name+'.png'),fullPage:true});
  const html=await page.evaluate(()=>{const clone=document.documentElement.cloneNode(true) as HTMLElement;
    clone.querySelectorAll('script,.connection').forEach(e=>e.remove());
    clone.querySelectorAll('link[href]').forEach(e=>{const url=new URL(e.getAttribute('href')!,location.href);if(url.origin===location.origin)e.setAttribute('href',url.pathname);});
    const originals=document.querySelectorAll('select');clone.querySelectorAll('select').forEach((e,i)=>e.querySelectorAll('option').forEach(o=>{
      if(o.value===originals[i]!.value)o.setAttribute('selected','');else o.removeAttribute('selected');}));
    return '<!doctype html>'+clone.outerHTML;});await writeFile(join(root,name+'.html'),html);
}
test('E8 00 submits once, polls original checkpoint, opens same completed UTC 3D',async({page})=>{
  const d=data(),errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));let phase=0,gets=0,posts=0;
  await page.route('**/v1/crop-climate-joint-executions',async r=>{posts++;expect(r.request().postDataJSON()).toEqual(d.request);
    expect(r.request().headers().authorization).toBe('Bearer '+TOKEN);await r.fulfill({status:202,json:d.job()});});
  await page.route(path,async r=>{gets++;await r.fulfill({json:phase===0?d.active:d.final});});const calls=await saved(page,d);
  await enter(page);await upload(page);await page.getByRole('button',{name:'계산 접수',exact:true}).click();
  await expect(page.getByLabel('서버 수용 체크포인트')).toContainText('7 / 16');
  await expect(page.getByLabel('계산 진행 상태')).toContainText(AT);await expect(page.getByLabel('계산 진행 상태')).toContainText(OBS);
  expect(gets).toBe(1);await snapshot(page,'execution-active');phase=1;await page.clock.fastForward(10_000);
  await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기'})).toBeVisible();expect(gets).toBe(2);expect(posts).toBe(1);
  const reads=await page.evaluate(()=>(window).executionReads);
  expect(reads[1]!.start-reads[0]!.end).toBeGreaterThanOrEqual(10_000);
  await page.getByRole('button',{name:'같은 저장 결과 3D 열기'}).click();
  const viewer=page.locator('.joint-viewer');await expect(viewer).toHaveAttribute('data-result-id',d.final.result.result_id);
  await expect(viewer).toHaveAttribute('data-selected-at',d.rows[1].page.records[0].time.at);await expect(page.locator('.coupled-canvas')).toBeVisible();
  await page.clock.fastForward(60_000);expect(gets).toBe(2);expect(calls.length).toBe(2);expect(errors).toEqual([]);
});
test('E8 01 numerical hold opens original failure result',async({page})=>{
  const d=data('hold');await page.route(path,r=>r.fulfill({json:d.final}));await saved(page,d);await enter(page);await attach(page,d);
  await expect(page.getByRole('heading',{name:'보류',exact:true})).toBeVisible();await snapshot(page,'execution-hold');
  await page.getByRole('button',{name:'같은 저장 결과 3D 열기'}).click();await expect(page.locator('.joint-replay')).toContainText('joint_');
  await expect(page.locator('.joint-replay')).toContainText('hold');
});
test('E8 02 pending GET never overlaps and explicit cancel remains independent',async({page})=>{
  const d=data();let gets=0,cancels=0;let release:()=>void=()=>{},acknowledge:()=>void=()=>{};
  const wait=new Promise<void>(resolve=>{release=resolve;}),ack=new Promise<void>(resolve=>{acknowledge=resolve;});
  await page.route(path,async r=>{gets++;if(gets===1){await wait;await r.fulfill({json:d.active}).catch(()=>{});}else {await ack;await r.fulfill({json:{...d.queued,job:d.job('canceled')}});}});
  await page.route(path+'/cancel',async r=>{cancels++;await r.fulfill({json:d.cancel()});});await enter(page);await attach(page);
  await expect.poll(()=>gets).toBe(1);await page.clock.fastForward(20_000);expect(gets).toBe(1);
  await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();await expect.poll(()=>cancels).toBe(1);
  await expect(page.getByLabel('계산 진행 상태')).toContainText('작업자의 취소 확인');release();acknowledge();
  await expect(page.getByRole('heading',{name:'취소됨',exact:true})).toBeVisible();await expect(page.getByLabel('서버 수용 체크포인트')).toHaveCount(0);
  await expect(page.getByLabel('계산 진행 상태')).not.toContainText('작업자의 취소 확인');
});
test('E8 03 disconnect backoff and manual reconnect preserve job identity',async({page})=>{
  const d=data();let count=0;await page.route(path,r=>{count++;return count===1?r.fulfill({status:503,json:{}}):r.fulfill({json:d.active});});
  await enter(page);await attach(page);await expect(page.getByLabel('계산 진행 상태')).toContainText('연결 끊김');
  await page.clock.fastForward(20_000);
  await expect(page.getByLabel('서버 수용 체크포인트')).toContainText('7 / 16');expect(count).toBe(2);
  const reads=await page.evaluate(()=>(window).executionReads);
  expect(reads[1]!.start-reads[0]!.end).toBeGreaterThanOrEqual(20_000);
  await page.getByRole('button',{name:'조회 연결 해제'}).click();await expect(page.getByLabel('계산 진행 상태')).toHaveCount(0);
  await page.getByRole('button',{name:'기존 계산 조회',exact:true}).click();await expect(page.getByLabel('계산 진행 상태')).toContainText(ID);expect(count).toBe(3);
});
for(const status of [401,403,404,422])test(`E8 04 denial ${status} clears numbers and stops polling, keeps cancel`,async({page})=>{
  const d=data();let count=0;await page.route(path,r=>{count++;return count===1?r.fulfill({json:d.active}):r.fulfill({status,json:{}});});
  await page.route(path+'/cancel',r=>r.fulfill({json:d.cancel('canceled')}));await enter(page);await attach(page);
  await expect(page.getByLabel('서버 수용 체크포인트')).toBeVisible();await page.getByRole('button',{name:'지금 다시 확인'}).click();
  await expect(page.getByLabel('계산 진행 상태')).toContainText('조회 보류');await expect(page.getByLabel('서버 수용 체크포인트')).toHaveCount(0);
  await page.clock.fastForward(60_000);expect(count).toBe(2);await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();
  await expect(page.getByLabel('계산 진행 상태')).toContainText('취소 요청 수락');
});
test('E8 05 selection and account changes discard late responses',async({page})=>{
  const d=data();let count=0;let release:()=>void=()=>{},releaseAccount:()=>void=()=>{};const wait=new Promise<void>(r=>{release=r;});
  const accountWait=new Promise<void>(r=>{releaseAccount=r;});
  await page.route(path,async r=>{count++;await (count===1?wait:accountWait);await r.fulfill({json:d.final}).catch(()=>{});});await enter(page);await attach(page);
  await expect.poll(()=>count).toBe(1);const details=page.locator('.joint-execution>.crop-lookup');await details.locator('summary').click();
  await page.getByLabel('계산 농장 판본',{exact:true}).fill('r2');release();await expect(page.getByLabel('계산 진행 상태')).toHaveCount(0);
  await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기'})).toHaveCount(0);
  await attach(page);await expect.poll(()=>count).toBe(2);
  if(!await page.getByLabel('접근 토큰').isVisible())await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(TOKEN+'-changed');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();releaseAccount();
  await expect(page.getByLabel('계산 진행 상태')).toHaveCount(0);
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();await page.getByLabel('저장 결과 판본').selectOption('joint-execution');
  await expect(page.getByLabel('계산 농장 판본',{exact:true})).toHaveValue('');
});
test('E8 06 hidden view stops polling and resumes one current read',async({page})=>{
  const d=data();let count=0;await page.route(path,r=>{count++;return r.fulfill({json:d.active});});await enter(page);await attach(page);
  await expect(page.getByLabel('서버 수용 체크포인트')).toBeVisible();await page.evaluate(()=>{
    Object.defineProperty(document,'visibilityState',{configurable:true,value:'hidden'});document.dispatchEvent(new Event('visibilitychange'));});
  await expect(page.getByLabel('계산 진행 상태')).toContainText('화면 숨김');await page.clock.fastForward(60_000);expect(count).toBe(1);
  await page.evaluate(()=>{Object.defineProperty(document,'visibilityState',{configurable:true,value:'visible'});document.dispatchEvent(new Event('visibilitychange'));});
  await expect.poll(()=>count).toBe(2);
});
test('E8 07 rejects malformed file, retries same request after unknown submission',async({page})=>{
  const d=data();let posts=0;await page.route('**/v1/crop-climate-joint-executions',async r=>{
    posts++;expect(r.request().postDataJSON()).toEqual(d.request);await r.fulfill({status:posts===1?503:202,json:posts===1?{}:d.job()});});
  await page.route(path,r=>r.fulfill({json:d.queued}));await enter(page);
  await page.getByLabel('검토된 계산 접수 파일').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from('{"farm":"bad"}')});
  await expect(page.getByRole('alert')).toContainText('형식');expect(posts).toBe(0);
  await page.getByLabel('검토된 계산 접수 파일').setInputFiles({name:'too-large.json',mimeType:'application/json',buffer:Buffer.alloc(65_537,65)});
  await expect(page.getByRole('alert')).toContainText('허용 크기');expect(posts).toBe(0);await upload(page);
  await page.getByRole('button',{name:'계산 접수',exact:true}).click();await expect(page.getByRole('alert')).toContainText('서버');
  await page.getByRole('button',{name:'계산 접수',exact:true}).click();await expect(page.getByLabel('계산 진행 상태')).toContainText(ID);expect(posts).toBe(2);
});
test('E8 08 mobile keyboard labels and no horizontal overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});const d=data();await page.route(path,r=>r.fulfill({json:d.active}));await enter(page);await attach(page);
  await expect(page.getByLabel('서버 수용 체크포인트')).toBeVisible();await page.getByRole('button',{name:'지금 다시 확인'}).focus();
  await expect(page.getByRole('button',{name:'지금 다시 확인'})).toBeFocused();await page.keyboard.press('Tab');
  await expect(page.getByRole('button',{name:'서버 계산 취소',exact:true})).toBeFocused();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await snapshot(page,'execution-mobile');
});
test('E8 09 mismatched terminal response cannot open result',async({page})=>{
  const d=data();await page.route(path,r=>r.fulfill({json:{...d.final,result:{...d.final.result,farm:{...d.final.result.farm,crop_id:'wrong'}}}}));
  await enter(page);await attach(page);await expect(page.getByRole('alert')).toContainText('형식');
  await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기'})).toHaveCount(0);await snapshot(page,'execution-blocked');
});
test('E8 10 empty selected result creates no invented 3D frame',async({page})=>{
  const d=data(),reference={...d.rows[0].reference,artifact:{...d.rows[0].reference.artifact,sample_count:0}};
  d.rows=[{...d.rows[0],reference},{...d.rows[1],reference,page:{...d.rows[1].page,total:0,records:[],next_offset:null}}];
  await page.route(path,r=>r.fulfill({json:{...d.final,checkpoint:{...d.final.checkpoint,counts:{samples:0,events:0}}}}));
  await saved(page,d);await enter(page);await attach(page);await page.getByRole('button',{name:'같은 저장 결과 3D 열기'}).click();
  await expect(page.getByRole('heading',{name:'선택 가능한 저장 시점이 없습니다',exact:true})).toBeVisible();
  await expect(page.locator('.joint-viewer,.coupled-canvas,.crop-timeline')).toHaveCount(0);
});
test('E8 11 terminal cancel refusal preserves completed status',async({page})=>{
  const d=data();let completed=false;
  await page.route(path,r=>r.fulfill({json:completed?d.final:d.queued}));
  await page.route(path+'/cancel',async r=>{completed=true;await r.fulfill({json:d.cancel('succeeded',false)});});
  await enter(page);await attach(page);await expect(page.getByRole('heading',{name:'대기 중',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'서버 계산 취소',exact:true}).click();
  await expect(page.getByLabel('계산 진행 상태')).toContainText('취소 요청으로 상태가 바뀌지 않음');
  await expect(page.getByRole('heading',{name:'계산 완료',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'취소됨',exact:true})).toHaveCount(0);
  await expect(page.getByRole('button',{name:'같은 저장 결과 3D 열기'})).toBeVisible();
});
