import { test,expect,type Page } from '@playwright/test';
import { cropReferenceResponse,cropReferenceSelection } from './crop-fixture';
import { decodeCropReplay,STORES } from '../src/cropReplay';

const token='synthetic-crop-browser-token-only';
const replay=decodeCropReplay(cropReferenceResponse(),cropReferenceSelection);
const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',
  registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
async function connect(page:Page,bearer=token){
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(bearer);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
}
async function selection(page:Page){
  for(const key of Object.keys(labels) as (keyof typeof labels)[])await page.getByLabel(labels[key],{exact:true}).fill(cropReferenceSelection[key]);
}
async function load(page:Page){await selection(page);await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.crop-viewer')).toBeVisible();}
async function mock(page:Page,data:unknown=cropReferenceResponse()){
  await page.route('**/v1/crop-research-results/**',async route=>{
    expect(route.request().method()).toBe('GET');expect(route.request().headers().authorization).toBe('Bearer '+token);
    expect(Object.fromEntries(new URL(route.request().url()).searchParams)).toEqual(replay.farm);
    await route.fulfill({json:data});
  });
}
async function sameSample(page:Page,index:number,scene=true){
  const point=replay.samples[index]!;
  for(const selector of ['.crop-viewer','.crop-readout','.crop-chart',...(scene?['.crop-scene']:[])])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',point.at);
  for(const key of ['lai',...STORES] as const){
    const value=key==='lai'?point.lai.value:point.state[key].value;
    await expect(page.locator('.crop-readout [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(value));
    await expect(page.locator('.crop-table tr[aria-selected=true] [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(value));
  }
  if(scene){
    const canvas=page.locator('.crop-canvas');await expect(canvas).toHaveAttribute('data-scene-at',point.at);
    await expect.poll(async()=>Math.abs(Number(await canvas.getAttribute('data-leaf-surface-area'))-point.lai.value))
      .toBeLessThanOrEqual(Math.max(1e-8,point.lai.value*1e-6));
    for(const store of STORES)await expect(canvas).toHaveAttribute('data-carbon-'+store.replace('_','-'),String(point.state[store].value));
    expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  }
}

test('six saved frames map to actual WebGL surface, table and graph with discrete keyboard controls',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await mock(page);await connect(page);await load(page);
  await expect(page.getByText('합성 계산 · 품종 미검증',{exact:true})).toBeVisible();
  await expect(page.getByText('관문 미평가',{exact:true})).toBeVisible();
  await expect(page.locator('.crop-viewer')).toHaveAttribute('data-result-id',replay.result_id);
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});
  await slider.focus();
  for(let i=0;i<replay.samples.length;i++){
    if(i)await slider.press('ArrowRight');await sameSample(page,i);
    for(const metric of ['lai',...STORES] as const){
      await page.getByLabel('성장 그래프 항목').selectOption(metric);
      const value=metric==='lai'?replay.samples[i]!.lai.value:replay.samples[i]!.state[metric].value;
      await expect(page.locator('.crop-chart')).toHaveAttribute('data-selected-value',String(value));
      await expect(page.locator('.crop-plot svg')).toBeVisible();
    }
  }
  await expect(page.getByRole('button',{name:'성장 자동 재생',exact:true})).toBeDisabled();
  await slider.focus();await slider.press('Home');await sameSample(page,0);
  await page.getByRole('button',{name:'성장 오른쪽에서 보기',exact:true}).click();await sameSample(page,0);
  await page.getByRole('button',{name:'성장 자동 재생',exact:true}).click();
  await expect(slider).not.toHaveValue('0');await page.getByRole('button',{name:'성장 일시 정지',exact:true}).click();
  const paused=await slider.inputValue();await page.waitForTimeout(1100);await expect(slider).toHaveValue(paused);
  await page.locator('.crop-table tbody button').last().click();await sameSample(page,5);
  await expect(page.locator('.crop-events')).toContainText('입력된 탄소 제거');
  expect(errors).toEqual([]);
});

test('actual WebGL context loss and restoration preserve the current stored sample',async({page})=>{
  await mock(page);await connect(page);await load(page);await sameSample(page,0);
  const canvas=page.locator('.crop-canvas');
  const extension=await canvas.evaluateHandle(element=>{
    const value=(element as HTMLCanvasElement).getContext('webgl2')?.getExtension('WEBGL_lose_context');
    if(!value)throw new Error('context loss extension required');return value;});
  await extension.evaluate(value=>value.loseContext());
  await expect(page.getByText('성장 3D를 사용할 수 없습니다.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'다음 저장 성장 시점',exact:true}).click();await sameSample(page,1,false);
  expect(await canvas.getAttribute('data-scene-at')).toBeNull();
  await extension.evaluate(value=>value.restoreContext());await extension.dispose();
  await sameSample(page,1);await expect(page.getByText('성장 3D 준비됨',{exact:true})).toBeVisible();
});

test('WebGL absence and reduced motion retain keyboard/table at narrow and enlarged widths',async({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype,'getContext',{value:function(this:HTMLCanvasElement,...args:Parameters<typeof original>){
      return args[0]==='webgl2'?null:original.apply(this,args);}});});
  await page.emulateMedia({reducedMotion:'reduce'});await mock(page);await connect(page);await load(page);
  await expect(page.getByText('성장 3D를 사용할 수 없습니다.',{exact:true})).toBeVisible();
  await expect(page.getByRole('button',{name:'성장 자동 재생',exact:true})).toBeDisabled();
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});await slider.focus();await slider.press('End');
  await sameSample(page,5,false);
  for(const fontSize of ['16px','32px'])for(const width of [320,768,1440]){
    await page.setViewportSize({width,height:900});await page.evaluate(size=>{document.documentElement.style.fontSize=size;},fontSize);
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await expect(slider).toBeVisible();await sameSample(page,5,false);
  }
});

test('current read denial clears the previous values and scene',async({page})=>{
  let allowed=true;
  await page.route('**/v1/crop-research-results/**',route=>route.fulfill(allowed?{json:cropReferenceResponse()}:
    {status:403,json:{error:{code:'forbidden',message:'not available'}}}));
  await connect(page);await load(page);await sameSample(page,0);allowed=false;
  await page.getByText('저장 연구 결과 조회',{exact:true}).click();
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.crop-viewer')).toHaveCount(0);await expect(page.locator('.crop-canvas')).toHaveCount(0);
  await expect(page.locator('.crop-replay [role=alert]')).toContainText('조회 권한');
});

test('hold diagnostics keep signed/unknown failed values outside the growth scene',async({page})=>{
  const data=cropReferenceResponse() as Record<string,any>,last=data.samples[0],failed=structuredClone(last.state);
  failed.buffer.value=-0.125;failed.fruit.value=null;
  Object.assign(data,{status:'hold',steps:0,samples:[],events:[],hold:{reason_code:'DEPLETED_STATE_HOLD',
    attempted_at:data.start_utc,phase:'rk4-k1',time_meaning:'solver_evaluation_time',last_confirmed:last,failed_state:failed}});
  await mock(page,data);await connect(page);await selection(page);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.crop-hold')).toContainText('DEPLETED_STATE_HOLD');
  await expect(page.locator('.crop-hold')).toContainText('-0.125');
  await expect(page.locator('.crop-hold')).toContainText('수치 없음');
  await expect(page.locator('.crop-canvas,.crop-chart,.crop-table')).toHaveCount(0);
});

test('editing the lookup discards a pending response',async({page})=>{
  let resolve:(()=>void)|undefined;
  await page.route('**/v1/crop-research-results/**',async route=>{
    await new Promise<void>(r=>{resolve=r;});await route.fulfill({json:cropReferenceResponse()});});
  await connect(page);await selection(page);await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect.poll(()=>Boolean(resolve)).toBe(true);
  await page.getByLabel('작물 ID',{exact:true}).fill('other-crop');
  const late=page.waitForResponse('**/v1/crop-research-results/**');resolve!();await (await late).finished();
  await page.waitForTimeout(100);
  await expect(page.locator('.crop-replay')).not.toHaveAttribute('aria-busy','true');
  await expect(page.locator('.crop-viewer,.crop-canvas')).toHaveCount(0);
});

test('connection change and reconnect never reuse previous results',async({page})=>{
  await mock(page);await connect(page);await load(page);await sameSample(page,0);
  await page.getByLabel('접근 토큰').fill('different-crop-browser-token-only');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await expect(page.locator('.crop-viewer,.crop-canvas')).toHaveCount(0);
  await expect(page.getByLabel('저장 연구 결과 ID',{exact:true})).toHaveValue('');
  await connect(page);await load(page);await sameSample(page,0);
  await page.getByRole('button',{name:'01 입력 설정',exact:true}).click();
  await expect(page.locator('.crop-canvas')).toHaveCount(0);
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await expect(page.locator('.crop-viewer')).toHaveCount(0);
});

test('invalid response units withhold all calculated display',async({page})=>{
  const data=cropReferenceResponse() as Record<string,any>;data.samples[2].state.fruit.unit='kg';
  await mock(page,data);await connect(page);await selection(page);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.locator('.crop-replay [role=alert]')).toContainText('응답');
  await expect(page.locator('.crop-viewer,.crop-canvas')).toHaveCount(0);
});

test('a pending response cannot restore another connection’s results',async({page})=>{
  let resolve:(()=>void)|undefined;
  await page.route('**/v1/crop-research-results/**',async route=>{
    await new Promise<void>(r=>{resolve=r;});await route.fulfill({json:cropReferenceResponse()});});
  await connect(page);await selection(page);await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect.poll(()=>Boolean(resolve)).toBe(true);
  await page.getByLabel('접근 토큰').fill('different-crop-browser-token-only');
  await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await expect(page.getByLabel('저장 연구 결과 ID',{exact:true})).toHaveValue('');
  const late=page.waitForResponse('**/v1/crop-research-results/**');resolve!();await (await late).finished();
  await page.waitForTimeout(100);await expect(page.locator('.crop-viewer,.crop-canvas')).toHaveCount(0);
});

test('long software fixture paginates 50 rows while retaining selected sample identity',async({page})=>{
  const data=cropReferenceResponse() as Record<string,any>,initial=data.samples[0];
  data.samples=Array.from({length:101},(_,index)=>({...structuredClone(initial),
    at:new Date(Date.parse(data.start_utc)+index*1000).toISOString().replace('.000Z','Z')}));
  data.end_utc=data.samples[100].at;data.events=[];
  await mock(page,data);await connect(page);await load(page);
  await expect(page.locator('.crop-table tbody tr')).toHaveCount(50);
  await page.getByRole('button',{name:'다음 50시점',exact:true}).click();
  await expect(page.locator('.crop-table tbody tr')).toHaveCount(50);
  await expect(page.locator('.crop-viewer')).toHaveAttribute('data-selected-at',data.samples[50].at);
  await page.getByRole('slider',{name:'저장 성장 시점 선택'}).focus();
  await page.getByRole('slider',{name:'저장 성장 시점 선택'}).press('End');
  await expect(page.locator('.crop-table tbody tr')).toHaveCount(1);
  await expect(page.locator('.crop-viewer')).toHaveAttribute('data-selected-at',data.end_utc);
  await expect(page.locator('.crop-canvas')).toHaveAttribute('data-scene-at',data.end_utc);
  await expect(page.locator('.crop-chart')).toHaveAttribute('data-selected-at',data.end_utc);
  await expect(page.getByRole('button',{name:'다음 50시점',exact:true})).toBeDisabled();
});
