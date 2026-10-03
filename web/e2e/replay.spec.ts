import { test,expect,type Page } from '@playwright/test';
import { thermalJobId,thermalResponses } from './thermal-fixture';

const token='synthetic-browser-replay-token-only';
async function routes(page:Page,data=thermalResponses()) {
  await page.route('**/v1/**',async route=>{
    expect(route.request().method()).toBe('GET');
    expect(route.request().headers().authorization).toBe('Bearer '+token);
    const path=new URL(route.request().url()).pathname;
    await route.fulfill({json:path.endsWith('/series') ? data.series : path.endsWith('/manifest') ? data.manifest : data.summary});
  });
}
async function connect(page:Page) {
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'05 3D 열 재생'}).click();
}
async function load(page:Page) {
  await page.getByLabel('완료된 열 작업 ID').fill(thermalJobId);
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.locator('.replay-viewer')).toBeVisible();
}
async function samePoint(page:Page,index:number) {
  const point=thermalResponses().series.points[index]!;
  await expect(page.locator('.replay-viewer')).toHaveAttribute('data-selected-at',point.at_utc);
  await expect(page.locator('.replay-summary')).toHaveAttribute('data-selected-at',point.at_utc);
  await expect(page.locator('.replay-chart')).toHaveAttribute('data-selected-at',point.at_utc);
  await expect(page.locator('.zone-scene')).toHaveAttribute('data-selected-at',point.at_utc);
  for(const key of ['temperature_k','relative_humidity_fraction','humidity_ratio_kg_v_per_kg_da',
    'heat_demand_w_th','heat_delivered_w_th','delivered_heat_energy_kwh_th'] as const) {
    await expect(page.locator('.replay-summary [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(point[key]));
    await expect(page.locator('.replay-table tr[aria-selected=true] [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(point[key]));
  }
  return point;
}

test('actual WebGL scene, keyboard time, graph/table identity and context-loss fallback',async ({page})=>{
  const errors:string[]=[];page.on('pageerror',error=>errors.push(error.message));
  await routes(page);await connect(page);await load(page);
  await expect(page.getByText('3D 준비됨',{exact:true})).toBeVisible();
  const canvas=page.locator('.zone-canvas');
  await samePoint(page,0);
  await expect(canvas).toHaveAttribute('data-scene-at-utc',thermalResponses().series.points[0]!.at_utc);
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  for(const width of [768,320,1440]){
    await page.setViewportSize({width,height:900});
    await expect.poll(()=>page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
    await expect(canvas).toHaveAttribute('data-scene-at-utc',thermalResponses().series.points[0]!.at_utc);
  }
  const firstFrame=await canvas.screenshot();
  const slider=page.getByRole('slider',{name:'저장 시각 선택'});
  await slider.focus();await slider.press('End');const last=await samePoint(page,119);
  await expect(canvas).toHaveAttribute('data-temperature-k',String(last.temperature_k));
  await expect(canvas).toHaveAttribute('data-heat-delivered-w-th',String(last.heat_delivered_w_th));
  expect(firstFrame.equals(await canvas.screenshot())).toBe(false);
  const metric=page.getByLabel('그래프 항목');
  for(const key of ['temperature_k','relative_humidity_fraction','humidity_ratio_kg_v_per_kg_da',
    'heat_demand_w_th','heat_delivered_w_th','delivered_heat_energy_kwh_th'] as const){
    await metric.selectOption(key);
    const value=key==='temperature_k' ? last[key]-273.15 : key==='relative_humidity_fraction' ? last[key]*100 : last[key];
    await expect(page.locator('.replay-chart')).toHaveAttribute('data-selected-value',String(value));
    await expect(page.locator('.replay-plot svg')).toBeVisible();
  }
  await expect(page.getByRole('button',{name:'자동 재생',exact:true})).toBeDisabled();
  await slider.press('Home');await slider.press('ArrowRight');await samePoint(page,1);
  await page.getByRole('button',{name:'오른쪽에서 보기'}).click();await samePoint(page,1);
  await page.getByRole('button',{name:'자동 재생',exact:true}).click();
  await expect(page.locator('.replay-viewer')).not.toHaveAttribute('data-selected-at',thermalResponses().series.points[1]!.at_utc);
  await page.getByRole('button',{name:'일시 정지',exact:true}).click();
  const paused=await slider.inputValue();await page.waitForTimeout(1100);expect(await slider.inputValue()).toBe(paused);
  const extension=await canvas.evaluateHandle(element=>{const gl=(element as HTMLCanvasElement).getContext('webgl2');
    const value=gl?.getExtension('WEBGL_lose_context');if(!value)throw new Error('context loss extension required');return value;});
  await extension.evaluate(value=>value.loseContext());
  await expect(page.getByText('이 환경에서 3D를 사용할 수 없습니다.',{exact:true})).toBeVisible();
  await page.getByRole('button',{name:'다음 1분'}).click();await samePoint(page,Number(paused)+1);
  expect(await canvas.getAttribute('data-scene-at-utc')).toBeNull();
  await extension.evaluate(value=>value.restoreContext());await extension.dispose();
  await expect(page.getByText('3D 준비됨',{exact:true})).toBeVisible();
  await expect(canvas).toHaveAttribute('data-scene-at-utc',thermalResponses().series.points[Number(paused)+1]!.at_utc);
  expect(errors).toEqual([]);
});

test('WebGL absence, reduced motion and responsive doubled text retain every value/control',async ({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
    Object.defineProperty(HTMLCanvasElement.prototype,'getContext',{value:function(this:HTMLCanvasElement,...args:Parameters<typeof original>){
      if(String(args[0]).startsWith('webgl'))return null;
      return Reflect.apply(original,this,args);
    }});});
  await page.emulateMedia({reducedMotion:'reduce'});await routes(page);
  for(const width of [320,768,1440]) {
    await page.setViewportSize({width,height:900});await connect(page);await load(page);
    await expect(page.getByText('이 환경에서 3D를 사용할 수 없습니다.',{exact:true})).toBeVisible();
    await expect(page.getByRole('button',{name:'자동 재생',exact:true})).toBeDisabled();
    for(const doubled of [false,true]) {
      if(doubled)await page.addStyleTag({content:':root{font-size:32px}'});
      expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
      expect(await page.evaluate(()=>document.documentElement.scrollHeight<=document.body.getBoundingClientRect().height+1)).toBe(true);
      await page.getByRole('slider',{name:'저장 시각 선택'}).focus();
      await page.getByRole('slider',{name:'저장 시각 선택'}).press('End');await samePoint(page,119);
      await page.getByRole('button',{name:'처음 시각'}).click();await samePoint(page,0);
    }
  }
});

test('new selection and connection changes discard previous and delayed results',async ({page})=>{
  await routes(page);await connect(page);await load(page);
  await page.getByText('완료된 열 작업 선택',{exact:true}).click();
  await page.getByLabel('완료된 열 작업 ID').fill('33333333-3333-4333-8333-333333333333');
  await expect(page.locator('.replay-viewer')).toHaveCount(0);
  await page.unroute('**/v1/**');
  let release:()=>void=()=>{};
  const wait=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/v1/**',async route=>{await wait;await route.fulfill({json:thermalResponses().summary});});
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await page.getByRole('button',{name:'연결 해제'}).click();release();
  await expect(page.locator('.replay-viewer')).toHaveCount(0);
  await page.getByRole('button',{name:'05 3D 열 재생'}).click();
  await expect(page.locator('.replay-viewer')).toHaveCount(0);
});

test('mismatched server manifest yields an explicit hold and no scene',async ({page})=>{
  const data=thermalResponses();data.manifest.trace_sha256=['0'.repeat(64),'1'.repeat(64)];
  await routes(page,data);await connect(page);
  await page.getByLabel('완료된 열 작업 ID').fill(thermalJobId);await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.getByRole('alert')).toContainText('표시를 보류');
  await expect(page.locator('.replay-viewer')).toHaveCount(0);
});
