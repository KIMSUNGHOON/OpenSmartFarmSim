import {test,expect,type Page} from '@playwright/test';
import {appearanceFlags,appearanceJobId,appearancePreview,appearanceResponse,appearanceToken} from './leaf-appearance-execution-fixture';

async function setup(page:Page){
  const state={phase:'queued',submissions:[] as string[],lost:false,denied:0,transientReads:0,cancels:0,delay:0,requests:[] as string[]};
  await page.addInitScript(token=>{if(sessionStorage.getItem('ossf-leaf-appearance-token-v1')===null)sessionStorage.setItem('ossf-leaf-appearance-token-v1',token);},appearanceToken);
  await page.route('**/leaf-appearance-preview-input',route=>route.fulfill({json:appearancePreview(),headers:{'Cache-Control':'no-store'}}));
  await page.route('**/v1/**',async route=>{
    const request=route.request(),path=new URL(request.url()).pathname;state.requests.push(path);
    if(request.headers().authorization!=='Bearer '+appearanceToken)return route.fulfill({status:403});
    if(path==='/v1/crop-leaf-appearance-executions'){
      state.submissions.push(request.postData()!);if(state.lost){state.lost=false;return route.fulfill({status:504});}
      return route.fulfill({status:202,json:{...appearanceResponse().job,state:'queued',attempt_count:0,reason_code:null},headers:{'Cache-Control':'no-store'}});
    }
    if(path.endsWith('/cancel')){state.phase='canceled';state.cancels++;
      return route.fulfill({json:{schema_version:'leaf-appearance-execution-cancel-v1',...appearanceFlags,
        observed_at:'2026-10-23T19:02:00Z',job:{...appearanceResponse().job,state:'canceled'},cancel_requested:true,cancel_accepted:true},headers:{'Cache-Control':'no-store'}});}
    if(state.denied)return route.fulfill({status:state.denied});
    if(state.transientReads>0){state.transientReads--;return route.fulfill({status:503});}
    if(new RegExp(`^/v1/jobs/(?:${appearanceJobId}|33333333-3333-4333-8333-333333333333)/crop-leaf-appearance-execution(?:/replay)?$`).test(path)){
      if(path.endsWith('/replay')&&state.phase!=='succeeded')return route.fulfill({status:422});
      const response=appearanceResponse();if(state.phase!=='succeeded')Object.assign(response,{job:{...response.job,state:state.phase},result:null,replay:null});
      if(!path.endsWith('/replay'))Object.assign(response,{replay:null});
      response.job.job_id=path.split('/')[3]!;
      if(state.delay)await new Promise(resolve=>setTimeout(resolve,state.delay));
      return route.fulfill({json:response,headers:{'Cache-Control':'no-store'}}).catch(()=>{});
    }
    return route.fulfill({status:404});
  });
  await page.route('**/leaf-appearance-replay/**',route=>route.abort());
  await page.goto('/leaf-appearance-execution.html');await expect(page.getByRole('button',{name:'계산 시작',exact:true})).toBeEnabled();return state;
}
async function check(page:Page,index:number){
  const frame=appearanceResponse().replay.frames[index],canvas=page.locator('canvas');
  await expect(canvas).toHaveAttribute('data-selected-index',String(index),{timeout:60_000});
  await expect(canvas).toHaveAttribute('data-scene-at',frame.at);
  const areas=frame.leaves.map((leaf:{area:{value:number}})=>leaf.area.value);
  expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-areas'))!)).toEqual(areas);
  const rendered=JSON.parse((await canvas.getAttribute('data-rendered-leaf-areas'))!) as {leaf_id:string;area_m2:number}[];
  expect(rendered).toHaveLength(areas.length);rendered.forEach((leaf,i)=>{expect(leaf.leaf_id).toBe(frame.leaves[i].leaf_id);expect(Math.abs(leaf.area_m2-areas[i])/areas[i]).toBeLessThan(1e-12);});
  expect(await page.locator('td[data-raw-area]').evaluateAll(nodes=>nodes.map(node=>node.getAttribute('data-raw-area')))).toEqual(areas.map(String));
  await expect(page.locator('.morphology-history')).toHaveAttribute('data-selected-at',frame.at);
}

test('same job: real phases, all 12 stored frames, menu/reload retention, and denial removes numbers',async({page})=>{
  const state=await setup(page);await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.locator('.leaf-execution')).toHaveAttribute('data-job-state','queued');
  state.phase='simulating';await expect(page.getByRole('button',{name:'현재 상태 다시 확인',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'현재 상태 다시 확인',exact:true}).click();await expect(page.locator('.leaf-execution')).toHaveAttribute('data-job-state','simulating');
  state.phase='succeeded';await expect(page.getByRole('button',{name:'현재 상태 다시 확인',exact:true})).toBeEnabled();await page.getByRole('button',{name:'현재 상태 다시 확인',exact:true}).click();
  for(let index=0;index<12;index++){if(index)await page.getByRole('button',{name:'다음',exact:true}).click();await check(page,index);}
  await page.getByRole('button',{name:'근거와 범위',exact:true}).click();await expect(page.getByRole('heading',{name:'계산과 표현의 범위'})).toBeVisible();
  await page.getByRole('button',{name:'계산 작업',exact:true}).click();await expect(page.getByText(appearanceJobId,{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'3D 결과',exact:true}).click();await check(page,11);
  expect(new URL(page.url()).searchParams.get('frame')).toBe('11');await page.reload();await check(page,11);expect(state.submissions).toHaveLength(1);
  await page.screenshot({path:test.info().outputPath('appearance-execution-completed.png'),fullPage:true});
  state.denied=422;await page.getByRole('button',{name:'현재 권한 다시 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('보류');await expect(page.locator('canvas,table,.morphology-history')).toHaveCount(0);
  expect(state.requests.every(path=>path.includes('crop-leaf-appearance-execution'))).toBe(true);
});
test('504 submission survives reload and explicit retry uses exactly the same body',async({page})=>{
  const state=await setup(page);state.lost=true;await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('보류');await page.reload();
  await expect(page.getByRole('button',{name:'같은 접수 다시 확인',exact:true})).toBeEnabled();expect(state.submissions).toHaveLength(1);
  await expect(page.locator('canvas')).toHaveCount(0);await page.getByRole('button',{name:'같은 접수 다시 확인',exact:true}).click();
  await expect(page.locator('.leaf-execution')).toHaveAttribute('data-job-id',appearanceJobId);
  expect(state.submissions).toHaveLength(2);expect(state.submissions[0]).toBe(state.submissions[1]);
});
test('unconfirmed new job takes priority over previous completed job after reload',async({page})=>{
  const state=await setup(page);state.phase='succeeded';await page.getByRole('button',{name:'계산 시작',exact:true}).click();await check(page,0);
  await page.getByRole('button',{name:'계산 작업',exact:true}).click();
  state.lost=true;await expect(page.getByRole('button',{name:'같은 입력으로 새 계산',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'같은 입력으로 새 계산',exact:true}).click();await expect(page.getByRole('alert')).toBeVisible();
  await page.reload();await expect(page.getByRole('heading',{name:'새 접수 확인 필요',exact:true})).toBeVisible();
  await expect(page.locator('canvas,table')).toHaveCount(0);expect(state.submissions).toHaveLength(2);
});
test('cancel interrupts an in-flight state read and shows only server cancellation state',async({page})=>{
  const state=await setup(page);state.delay=2000;await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.getByRole('button',{name:'취소 요청',exact:true})).toBeEnabled();await page.getByRole('button',{name:'취소 요청',exact:true}).click();
  await expect(page.locator('.leaf-execution')).toHaveAttribute('data-job-state','canceled');
  expect(state.cancels).toBe(1);await expect(page.getByRole('heading',{name:'계산 취소됨',exact:true})).toBeVisible();await expect(page.locator('canvas,table')).toHaveCount(0);
});
test('mobile fallback preserves stored leaf values and fits viewport',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,type:string,...args:unknown[]){return type==='webgl2'?null:Reflect.apply(get,this,[type,...args]);} as typeof get;});
  const state=await setup(page);state.phase='succeeded';await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.getByText('3D 표시 보류:',{exact:false})).toBeVisible();await expect(page.locator('tbody tr')).toHaveCount(3);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
test('disconnect clears results and reload does not reuse the previous workspace token',async({page})=>{
  await page.addInitScript(token=>sessionStorage.setItem('ossf-morphology-token-v1',token),appearanceToken);
  const state=await setup(page);state.phase='succeeded';await page.getByRole('button',{name:'계산 시작',exact:true}).click();await check(page,0);
  await page.getByText('연결 설정됨',{exact:true}).click();await page.getByRole('button',{name:'연결 해제',exact:true}).click();
  await expect(page.locator('canvas,table')).toHaveCount(0);await page.reload();
  await expect(page.getByText('연결 필요',{exact:true})).toBeVisible();await expect(page.locator('canvas,table')).toHaveCount(0);
});
test('a new admission updates a bookmarked job URL so reload keeps the newly selected job',async({page})=>{
  const state=await setup(page);state.phase='succeeded';
  await page.goto('/leaf-appearance-execution.html?job_id=33333333-3333-4333-8333-333333333333');await check(page,0);
  await page.getByRole('button',{name:'계산 작업',exact:true}).click();await page.getByRole('button',{name:'계산 입력 확인',exact:true}).click();
  await expect(page.getByRole('button',{name:'같은 입력으로 새 계산',exact:true})).toBeEnabled();await page.getByRole('button',{name:'같은 입력으로 새 계산',exact:true}).click();await check(page,0);
  expect(new URL(page.url()).searchParams.get('job_id')).toBe(appearanceJobId);await page.reload();await check(page,0);
  await expect(page.locator('.leaf-execution')).toHaveAttribute('data-job-id',appearanceJobId);expect(state.submissions).toHaveLength(1);
});
test('deadline failure stays visible without automatic retries and explicit recovery restores the same job',async({page})=>{
  const state=await setup(page);state.phase='succeeded';await page.getByRole('button',{name:'계산 시작',exact:true}).click();await check(page,0);
  state.denied=504;await page.getByRole('button',{name:'현재 권한 다시 확인',exact:true}).click();await expect(page.getByRole('alert')).toContainText('보류');
  const requests=state.requests.length;await page.waitForTimeout(5500);expect(state.requests).toHaveLength(requests);
  await expect(page.locator('canvas,table')).toHaveCount(0);state.denied=0;await page.getByRole('button',{name:'작업 다시 확인',exact:true}).click();await check(page,0);
  expect(state.submissions).toHaveLength(1);
});
test('a temporarily changing server state recovers with a bounded GET retry and never repeats admission',async({page})=>{
  const state=await setup(page);state.phase='succeeded';state.transientReads=1;
  await page.getByRole('button',{name:'계산 시작',exact:true}).click();await expect(page.getByRole('alert')).toContainText('보류');await check(page,0);
  expect(state.submissions).toHaveLength(1);expect(state.requests.filter(v=>v.endsWith('/replay'))).toHaveLength(1);
});
test('persistent 503 stops after three GET attempts and keeps the hold visible',async({page})=>{
  const state=await setup(page);state.denied=503;await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect.poll(()=>state.requests.filter(v=>v.endsWith('/crop-leaf-appearance-execution')).length,{timeout:20000}).toBe(3);
  const count=state.requests.length;await page.waitForTimeout(5500);expect(state.requests).toHaveLength(count);
  await expect(page.getByRole('alert')).toContainText('보류');await expect(page.locator('canvas,table')).toHaveCount(0);expect(state.submissions).toHaveLength(1);
});

test('plain entry restores the same local job and frame into its URL without a new POST',async({page})=>{
 const state=await setup(page);state.phase='succeeded';await page.getByRole('button',{name:'계산 시작',exact:true}).click();await check(page,0);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await check(page,11);
 await page.goto('/leaf-appearance-execution.html');await check(page,11);
 expect(new URL(page.url()).searchParams.get('job_id')).toBe(appearanceJobId);expect(new URL(page.url()).searchParams.get('frame')).toBe('11');expect(state.submissions).toHaveLength(1);
 await page.getByText('원 입력과 저장 지문',{exact:true}).click();await expect(page.getByText('합성 출현 정책: 첫 생식 순번',{exact:false})).toHaveCount(0);
});
