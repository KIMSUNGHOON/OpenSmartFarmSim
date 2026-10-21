import { test,expect,type Page } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { morphologyFlags,morphologyFrame,morphologyJobId,morphologyPreview,morphologyResponse,morphologyToken } from './morphology-execution-fixture';

async function setup(page:Page){
  const state={phase:'queued',submissions:[] as string[],lost:false,failRead:false,cancels:0,requests:[] as string[]};
  page.on('pageerror',error=>console.log('Owned morphology browser error:',error.name,error.message));
  await page.addInitScript(token=>sessionStorage.setItem('ossf-morphology-token-v1',token),morphologyToken);
  await page.route('**/preview-input',route=>route.fulfill({json:morphologyPreview()}));
  await page.route('**/v1/**',async route=>{
    const request=route.request(),path=new URL(request.url()).pathname;state.requests.push(path);
    if(request.headers().authorization!=='Bearer '+morphologyToken)return route.fulfill({status:403,json:{error:{code:'forbidden'}}});
    if(path==='/v1/crop-morphology-executions'&&request.method()==='POST'){
      state.submissions.push(request.postData()!);
      if(state.lost){state.lost=false;return route.abort('failed');}
      return route.fulfill({status:202,json:morphologyResponse('queued').job});
    }
    if(path===`/v1/jobs/${morphologyJobId}/crop-morphology-execution/cancel`){state.phase='canceled';state.cancels++;
      return route.fulfill({json:{schema_version:'morphology-execution-cancel-v1',...morphologyFlags,observed_at:'2026-10-21T21:01:00Z',
        job:morphologyResponse('canceled').job,cancel_requested:false,cancel_accepted:true}});}
    if(state.failRead)return route.fulfill({status:422,json:{error:{code:'morphology_execution_hold'}}});
    if(path===`/v1/jobs/${morphologyJobId}/crop-morphology-execution`||path===`/v1/jobs/${morphologyJobId}/crop-morphology-execution/replay`)
      return route.fulfill({json:morphologyResponse(state.phase,path.endsWith('/replay'))});
    return route.fulfill({status:404,json:{error:{code:'not_found'}}});
  });
  await page.goto('/morphology-execution.html');await expect(page.getByRole('button',{name:'계산 시작',exact:true})).toBeEnabled();return state;
}
async function check(page:Page,index:number){
  const saved=morphologyFrame(index),canvas=page.locator('canvas');await expect(canvas).toHaveAttribute('data-selected-index',String(index));
  await expect(canvas).toHaveAttribute('data-scene-at',saved.at);await expect(canvas).toHaveAttribute('data-axis-length',String(saved.tracked_axis_length.value));
  expect(JSON.parse((await canvas.getAttribute('data-rendered-lengths'))!)).toEqual(saved.internodes.map((n:{length:{value:number}})=>n.length.value));
  expect(await page.locator('tbody td[data-raw-value]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-value'))))
    .toEqual(saved.internodes.map((n:{length:{value:number}})=>String(n.length.value)));
}

test('queued calculation, stored WebGL, menu/reload recovery, and current denial remove all values',async({page})=>{
  const state=await setup(page);await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.locator('.morphology-execution')).toHaveAttribute('data-job-state','queued');
  state.phase='simulating';await page.getByRole('button',{name:'현재 상태 다시 확인',exact:true}).click();
  await expect(page.locator('.morphology-execution')).toHaveAttribute('data-job-state','simulating');
  state.phase='succeeded';await page.getByRole('button',{name:'현재 상태 다시 확인',exact:true}).click();
  try{await check(page,0);}catch(error){console.log('Owned fixture requests:',JSON.stringify(state.requests));
    console.log('Owned fixture interface:',await page.locator('main').innerText());throw error;}
  mkdirSync(resolve('../research/artifacts'),{recursive:true});await page.screenshot({path:resolve('../research/artifacts/morphology-execution-first-20261022.png'),fullPage:true});
  await page.getByRole('button',{name:'마지막',exact:true}).click();await check(page,11);
  await page.getByRole('button',{name:'근거와 범위',exact:true}).click();await expect(page.getByRole('heading',{name:'계산과 표현의 범위'})).toBeVisible();
  await page.getByRole('button',{name:'계산 작업',exact:true}).click();await expect(page.getByText(morphologyJobId,{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'3D 결과',exact:true}).click();await check(page,11);
  await page.screenshot({path:resolve('../research/artifacts/morphology-execution-last-20261022.png'),fullPage:true});
  await page.reload();await check(page,0);expect(state.submissions).toHaveLength(1);
  state.failRead=true;await page.getByRole('button',{name:'현재 권한 다시 확인',exact:true}).click();
  await expect(page.getByRole('alert')).toContainText('보류');await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('table')).toHaveCount(0);
  expect(state.requests.every(path=>!path.includes('morphology-rational-replay/'))).toBe(true);
});

test('lost admission response survives reload and reuses the exact original request',async({page})=>{
  const state=await setup(page);state.lost=true;await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.getByRole('alert')).toBeVisible();await page.reload();
  await expect(page.getByRole('button',{name:'같은 접수 다시 확인',exact:true})).toBeEnabled();
  await page.getByRole('button',{name:'같은 접수 다시 확인',exact:true}).click();
  await expect(page.locator('.morphology-execution')).toHaveAttribute('data-job-id',morphologyJobId);
  expect(state.submissions).toHaveLength(2);expect(state.submissions[0]).toBe(state.submissions[1]);
});

test('actual server cancellation state is shown without geometry or a fake completion',async({page})=>{
  const state=await setup(page);state.phase='simulating';await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.getByRole('button',{name:'취소 요청',exact:true})).toBeEnabled();await page.getByRole('button',{name:'취소 요청',exact:true}).click();
  await expect(page.locator('.morphology-execution')).toHaveAttribute('data-job-state','canceled');
  expect(state.cancels).toBe(1);await expect(page.locator('canvas')).toHaveCount(0);
});

test('mobile WebGL fallback retains the original stored quantities and stays within the viewport',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,type:string,...args:unknown[]){
      return type==='webgl2'?null:Reflect.apply(get,this,[type,...args]);} as typeof get;});
  const state=await setup(page);state.phase='succeeded';await page.getByRole('button',{name:'계산 시작',exact:true}).click();
  await expect(page.getByText('3D 표시 보류:',{exact:false})).toBeVisible();await expect(page.locator('tbody tr')).toHaveCount(3);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:resolve('../research/artifacts/morphology-execution-mobile-20261022.png'),fullPage:true});
});
