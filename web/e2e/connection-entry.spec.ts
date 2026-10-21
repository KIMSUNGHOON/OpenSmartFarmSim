import {test,expect,type Page} from '@playwright/test';
import {revealConnection,revealConnectedControls} from './connection-fixture';

test('connection entry preserves the open form and reopens a closed form',async({page})=>{
  await page.goto('/');
  const token=page.getByLabel('접근 토큰');
  await expect(token).toBeVisible();
  await token.fill('owned-connection-entry-draft-only');
  await revealConnection(page);
  await expect(token).toHaveValue('owned-connection-entry-draft-only');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await expect(token).toBeHidden();
  await revealConnection(page);
  await expect(token).toBeVisible();
  await expect(token).toHaveValue('owned-connection-entry-draft-only');
});

test('connection controls remain available for locks and account changes after connecting',async({page})=>{
  await page.goto('/');
  await revealConnection(page);
  const token=page.getByLabel('접근 토큰');
  await token.fill('owned-connection-entry-draft-only');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await expect(token).toBeHidden();
  await revealConnectedControls(page);
  await expect(page.getByRole('button',{name:'연결 해제',exact:true})).toBeEnabled();
  await token.fill('owned-replacement-account-draft-only');
  await expect(token).toHaveValue('owned-replacement-account-draft-only');
});

const executionJobId='11111111-1111-4111-8111-111111111111';
const executionAt='2026-10-10T05:00:00.123456Z';
const executionFarm={scenario_id:'owned-navigation-farm',scenario_revision:'r1',registration_sha256:'a'.repeat(64),crop_id:'crop'};
function executionRequest(ventilation:boolean){
  const source=ventilation?'joint-ventilation':'joint-crop-climate';
  return {study_id:'owned-navigation',revision:'r1',farm:executionFarm,
    input:{schema_version:source+'-input-source-v1',program_id:'program',source_sha256:'b'.repeat(64),
      context_sha256:'c'.repeat(64),time_binding_sha256:'d'.repeat(64),evidence_sha256:'e'.repeat(64)},
    rights:{schema_version:source+'-input-rights-v1',declaration_id:'owned',revision:'r1',input_source_sha256:'b'.repeat(64),
      available_at:executionAt,redistribute:false,ownership_asserted:true,access:true,store:true,transform:true,use:true,display:true}};
}
async function executionNavigation(page:Page,ventilation:boolean,pendingSubmission=false){
  const base=ventilation?'crop-greenhouse-ventilation':'crop-climate-joint';
  const source=ventilation?'joint-ventilation':'joint-crop-climate';
  const job={job_id:executionJobId,stage:'simulation',state:'queued',attempt_count:0,max_attempts:3,
    created_at:executionAt,updated_at:executionAt,reason_code:null};
  const counts={posts:0,reads:0};let release=()=>{};
  const pending=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/v1/'+base+'-executions',async route=>{
    counts.posts++;expect(route.request().postDataJSON()).toEqual(executionRequest(ventilation));
    if(pendingSubmission)await pending;
    await route.fulfill({status:202,json:job}).catch(()=>{});
  });
  await page.route('**/v1/jobs/'+executionJobId+'/'+base+'-execution/prefix',route=>route.fulfill({status:404,json:{}}));
  await page.route('**/v1/jobs/'+executionJobId+'/'+base+'-execution',async route=>{
    counts.reads++;
    await route.fulfill({json:{version:source+'-execution-query-v1',scope:'synthetic_'+(ventilation?'joint_ventilation':'joint_crop_climate')+'_math_only',
      G0_G4:'not_assessed',job:{...job,state:'simulating',attempt_count:1},cancel_requested:false,observed_at:executionAt,
      checkpoint_status:'current',checkpoint:{head_sha256:'1'.repeat(64),proof_sha256:'2'.repeat(64),artifact_sha256:null,
        status:'yielded',steps:6+counts.reads,planned_steps:16,counts:{samples:3,events:1},computed_through_utc:executionAt,
        checkpoint_recorded_at:executionAt,publication_sequence:counts.reads},result:null}});
  });
  await page.clock.install();await page.goto('/#'+(ventilation?'ventilation-execution':'crop-execution'));
  await page.getByLabel('접근 토큰').fill('owned-navigation-screen-test');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByLabel('검토된 계산 접수 파일').setInputFiles({name:'owned-navigation.json',mimeType:'application/json',
    buffer:Buffer.from(JSON.stringify(executionRequest(ventilation)))});
  await page.getByRole('button',{name:'계산 접수',exact:true}).click();
  return {counts,release};
}
for(const ventilation of [false,true]){
  const model=ventilation?'ventilation':'joint';
  test(`${model} execution survives menu navigation and resumes current reads without resubmitting`,async({page})=>{
    const {counts}=await executionNavigation(page,ventilation);
    await expect(page.getByLabel('서버 수용 체크포인트')).toContainText('7 / 16');
    await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();
    await page.clock.fastForward(60_000);expect(counts).toEqual({posts:1,reads:1});
    await page.getByRole('button',{name:'09 계산 진행 상태',exact:true}).click();
    await expect(page.getByLabel('서버 수용 체크포인트')).toContainText('8 / 16');
    await expect(page.getByLabel('계산 작업 ID',{exact:true})).toHaveValue(executionJobId);
    await expect(page.getByLabel('계산 모델',{exact:true})).toHaveValue(ventilation?'ventilation':'joint');
    expect(await page.getByLabel('검토된 계산 접수 파일').evaluate((input:HTMLInputElement)=>input.files?.[0]?.name)).toBe('owned-navigation.json');
    expect(counts).toEqual({posts:1,reads:2});
  });
  test(`${model} execution accepts a pending submission while another menu is open`,async({page})=>{
    const {counts,release}=await executionNavigation(page,ventilation,true);
    await expect.poll(()=>counts.posts).toBe(1);
    await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();release();
    await expect(page.getByLabel('계산 작업 ID',{exact:true})).toHaveValue(executionJobId);
    expect(counts.reads).toBe(0);
    await page.getByRole('button',{name:'09 계산 진행 상태',exact:true}).click();
    await expect(page.getByLabel('계산 진행 상태')).toContainText(executionJobId);
    expect(counts).toEqual({posts:1,reads:1});
  });
  test(`${model} execution clears the retained selection when the account changes while hidden`,async({page})=>{
    const {counts}=await executionNavigation(page,ventilation);
    await expect(page.getByLabel('서버 수용 체크포인트')).toBeVisible();
    await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();
    await revealConnection(page);await page.getByLabel('접근 토큰').fill('owned-replacement-account-screen-test');
    await page.getByRole('button',{name:'연결 설정',exact:true}).click();
    await page.getByRole('button',{name:'09 계산 진행 상태',exact:true}).click();
    await expect(page.getByLabel('계산 작업 ID',{exact:true})).toHaveValue('');
    await expect(page.getByLabel('검토된 계산 접수 파일')).toHaveValue('');
    await expect(page.getByRole('button',{name:'계산 접수',exact:true})).toBeDisabled();
    await page.clock.fastForward(60_000);expect(counts).toEqual({posts:1,reads:1});
  });
}
