import {test,expect,type Page} from '@playwright/test';
import {mkdir} from 'node:fs/promises';
import {SOURCE_FIELDS} from '../src/source-fields';
const id='11111111-1111-4111-8111-111111111111';
const time='2026-09-28T00:00:00Z';const value='55.0000000001';
const rights={use:'allowed',display:'allowed',redistribute:'denied'};
const number={value:'40',unit:'KRW',input_id:'production-paid',revision:'r1',origin:'user',evidence_level:'assumed',
  assumption_scope:'self-authored synthetic test',source_ref:'test',available_at:time,scope_start:'2026-10-01',scope_end:'2026-10-31'};
const {scope_start:_,scope_end:__,...inline}=number;
const scope={origin:'user',evidence_level:'assumed',available_at:time,effective_start:number.scope_start,effective_end:number.scope_end,rights};
const shock={schema_version:'1',shock_id:'joint-1',revision:'r1',baseline_sha256:'a'.repeat(64),decision_at:time,...scope,
  drivers:['demand','supply','macro'].map((kind,index)=>({kind,record_id:kind,revision:'r1',...scope,
    hypothesis:'Self-authored test hypothesis',source_ref:'test',causal_status:'unvalidated_user_hypothesis',changes:[{
      event_group:index===0 ? 'sales' : index===1 ? 'harvests' : 'variable_costs',event_id:index===2 ? 'production' : 'row',
      field:index===2 ? 'payment' : 'quantity',number:{...inline,input_id:index===2 ? number.input_id : kind,
        revision:'r2',value:index===2 ? '60' : '10',unit:index===2 ? 'KRW' : 'kg'},time:null,reference:null}]})),
  contract_caps:[],settlement_bindings:[{binding_id:'existing-binding',revision:'r2',sha256:'b'.repeat(64)}]};
const baseline={...Object.fromEntries(SOURCE_FIELDS.economic_scenario.map(key=>[key,null])),scenario_id:'base',scenario_revision:'r1',decision_at:time,
  period_start:'2026-10-01',period_end:'2026-10-31',market_context:{kind:'unavailable',hold_report_id:id}};
const job={job_id:id,stage:'collection',state:'queued',attempt_count:0,max_attempts:3,created_at:time,updated_at:time,reason_code:null};
function meta(kind:string,record_id:string,revision='r1') {return {kind,record_id,revision,payload_sha256:'a'.repeat(64),recorded_at:time,admission_kind:'contract_valid_user_assumption'};}
async function choose(page:Page,name:string) {
  const picker=page.getByRole('region',{name,exact:true});
  await expect(picker.getByRole('button',{name:'목록 조회'})).toBeEnabled();await picker.getByRole('button',{name:'목록 조회'}).click();
  await expect(picker.locator('li button')).toBeEnabled();await picker.locator('li button').click();
  if(name==='숫자 가정')await expect(page.getByLabel(/^새 가정값/)).toBeVisible();
  else await expect(page.locator('.selected-source').filter({hasText:name==='기준 원장' ? '선택 원장:' : '선택 공동 가정:'})).toBeVisible();
}
for(const loss of ['rights','shock','read','none','future'] as const) {
test(`new assumption applies through explicit rights and immutable joint revision: ${loss}`,async ({page})=>{
  let savedNumber=number;let savedShock=shock;let failedRead=false;
  const writes:Record<string,string[]>={economic_input:[],input_rights:[],joint_shock:[]};
  const scenarios:Record<string,unknown>[]=[];
  await page.route('**/v1/market-user-sources?*',route=>{
    const kind=new URL(route.request().url()).searchParams.get('kind')!;
    return route.fulfill({json:{kind,items:[meta(kind,kind==='economic_input' ? number.input_id : kind==='economic_scenario' ? 'base' : 'joint-1')],next_cursor:null}});
  });
  await page.route('**/v1/market-user-sources/record?*',route=>{
    const query=new URL(route.request().url()).searchParams;const kind=query.get('kind')!;const revision=query.get('revision')!;
    if(loss==='read' && kind==='joint_shock' && revision!=='r1' && !failedRead){failedRead=true;return route.abort();}
    const input=kind==='economic_input' ? revision==='r1' ? number : savedNumber : kind==='economic_scenario' ? baseline : revision==='r1' ? shock : savedShock;
    return route.fulfill({json:{...meta(kind,kind==='economic_input' ? number.input_id : kind==='economic_scenario' ? 'base' : 'joint-1',revision),input}});
  });
  await page.route('**/v1/market-user-sources',route=>{
    const body=route.request().postDataJSON();writes[body.kind]!.push(route.request().postData()!);
    if(body.kind==='economic_input')savedNumber=body.input;
    if(body.kind==='joint_shock')savedShock=body.input;
    if((loss==='rights' && body.kind==='input_rights' || loss==='shock' && body.kind==='joint_shock') && writes[body.kind]!.length===1)return route.abort();
    return route.fulfill({json:{...meta(body.kind,body.input.input_id ?? body.input.shock_id,body.input.revision),intent_job:job}});
  });
  await page.route('**/v1/economic-scenarios',route=>{
    scenarios.push(route.request().postDataJSON());return route.fulfill({json:{candidate_id:'c'.repeat(64),scenario_id:'derived',scenario_revision:'r2',
      scenario_sha256:'d'.repeat(64),registration_status:'pinned_user_assumption',recorded_at:time,intent_job:job}});
  });
  await page.route('**/v1/economic-results',route=>route.fulfill({status:202,json:{...job,stage:'simulation'}}));
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill('synthetic-joint-amendment-token');await page.getByRole('button',{name:'연결 설정'}).press('Enter');
  await page.getByRole('button',{name:'03 경제 가정·계산'}).press('Enter');
  await choose(page,'숫자 가정');await page.getByLabel(/^새 가정값/).fill(value);
  await page.getByLabel('가정을 알게 된 날짜 (UTC)').fill(loss==='future' ? '2026-09-29' : '2026-09-27');
  await page.getByLabel('가정을 알게 된 시각 (UTC)').fill('08:00');await page.getByRole('button',{name:'새 가정 판본 등록'}).press('Enter');
  await expect(page.getByText('새 가정 판본 접수됨',{exact:true})).toBeVisible();
  await choose(page,'기준 원장');await choose(page,'수급·거시 공동 가정');
  await page.getByRole('button',{name:'새 숫자의 적용 위치 확인'}).press('Enter');
  const select=page.getByLabel('적용할 숫자 위치');await expect(select).toBeVisible();await expect(select).toHaveValue('');
  const apply=page.getByRole('button',{name:'권리·공동 가정 판본 등록·선택'});await expect(apply).toBeDisabled();
  await select.selectOption('[2,0]');await expect(apply).toBeDisabled();
  await expect(page.locator('.amendment-preview')).toContainText('새 값: '+value+' KRW');
  const consent=page.getByRole('checkbox');await consent.check();await apply.press('Enter');
  if(loss==='future') {
    await expect(page.getByRole('alert')).toContainText('결정 시각');expect(writes.input_rights).toHaveLength(0);expect(writes.joint_shock).toHaveLength(0);return;
  }
  if(loss!=='none') {
    await expect(page.getByRole('alert')).toContainText('같은 요청');
    await expect(select).toBeDisabled();await expect(consent).toBeDisabled();
    await expect(page.getByRole('button',{name:'선택한 가정으로 계산 요청'})).toBeDisabled();
    await expect(page.getByRole('button',{name:'연결 해제'}))[loss==='read' ? 'toBeEnabled' : 'toBeDisabled']();
    await page.getByRole('button',{name:'02 작업과 근거'}).click();await page.getByRole('button',{name:'03 경제 가정·계산'}).click();
    await page.getByRole('button',{name:'같은 적용 요청 다시 확인'}).press('Enter');
  }
  await expect(page.getByText('새 숫자를 참조하는 공동 가정 판본이 선택되었습니다.',{exact:false})).toBeVisible();
  expect(writes.input_rights).toHaveLength(loss==='rights' ? 2 : 1);expect(writes.joint_shock).toHaveLength(loss==='shock' ? 2 : 1);
  for(const bodies of Object.values(writes))if(bodies.length===2)expect(bodies[1]).toBe(bodies[0]);
  const registeredRights=JSON.parse(writes.input_rights![0]!).input;
  expect(registeredRights.available_at).toBe('2026-09-27T08:00:00Z');expect(registeredRights.rights.redistribute).toBe('denied');
  const registered=JSON.parse(writes.joint_shock![0]!).input;
  expect(registered.drivers[2].changes[0].number.value).toBe(value);expect(registered.drivers[2].changes[0].number.revision).toBe(savedNumber.revision);
  expect(registered.settlement_bindings).toEqual(shock.settlement_bindings);expect(registered.drivers.slice(0,2)).toEqual(shock.drivers.slice(0,2));
  expect(scenarios).toHaveLength(0);await expect(page.locator('.economic-totals')).toHaveCount(0);
  if(loss==='none')for(const width of [320,768,1440]) {
    await page.setViewportSize({width,height:900});await page.evaluate(()=>document.fonts.ready);
    for(const size of ['16px','32px']) {
      await page.addStyleTag({content:':root{font-size:'+size+'}'});
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      const capture=process.env.OSSF_UI_CAPTURE_DIR;if(capture){await mkdir(capture,{recursive:true});await page.evaluate(()=>scrollTo(0,0));
        await page.screenshot({path:`${capture}/joint-amendment-${width}-${size}.png`,fullPage:true});}
    }
  }
  await page.getByRole('button',{name:'선택한 가정으로 계산 요청'}).press('Enter');
  await expect(page.getByText('계산 작업: 대기 중',{exact:true})).toBeVisible();
  expect(scenarios).toHaveLength(1);expect(scenarios[0]).toMatchObject({request:{shock:{shock_id:'joint-1',revision:savedShock.revision,sha256:'a'.repeat(64)}}});
});
}
