import { test,expect } from '@playwright/test';
import { mkdirSync,readFileSync } from 'node:fs';
import { resolve } from 'node:path';

const fixture=(index:number)=>JSON.parse(readFileSync(resolve(`public/morphology-replay/frame-${index}.json`),'utf8'));
test('stored UTC, exact internode lengths, table and graph move together in actual WebGL',async({page})=>{
  const errors:string[]=[],methods:string[]=[];
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error'||m.type()==='warning')errors.push(m.text());});
  page.on('request',r=>methods.push(r.method()));await page.setViewportSize({width:1440,height:1100});
  await page.goto('/morphology-replay.html');const canvas=page.locator('canvas');
  await expect(canvas).toHaveAttribute('data-mapping','stored-internode-metres-straight-axis-v1',{timeout:60_000});
  async function check(index:number){
    const saved=fixture(index);await expect(canvas).toHaveAttribute('data-scene-at',saved.at);
    for(const selector of ['.morphology-page','.morphology-summary','.morphology-history','.morphology-table'])
      await expect(page.locator(selector)).toHaveAttribute('data-selected-at',saved.at);
    expect(JSON.parse((await canvas.getAttribute('data-rendered-lengths'))!)).toEqual(saved.internodes.map((n:{length:{value:number}})=>n.length.value));
    await expect(canvas).toHaveAttribute('data-internode-count',String(saved.internodes.length));
    await expect(canvas).toHaveAttribute('data-axis-length',String(saved.tracked_axis_length.value));
    await expect(canvas).toHaveAttribute('data-authored-leaf-count','3');
    expect(await page.locator('tbody td[data-raw-value]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-value'))))
      .toEqual(saved.internodes.map((n:{length:{value:number}})=>String(n.length.value)));
  }
  await check(0);const first=await canvas.screenshot();mkdirSync(resolve('../research/artifacts'),{recursive:true});
  await page.screenshot({path:resolve('../research/artifacts/morphology-replay-first-20261022.png'),fullPage:true});
  await page.getByRole('button',{name:'마지막',exact:true}).click();await check(11);
  expect(Buffer.compare(first,await canvas.screenshot())).not.toBe(0);
  await page.screenshot({path:resolve('../research/artifacts/morphology-replay-last-20261022.png'),fullPage:true});
  const rendered=Number(await canvas.getAttribute('data-frame'));await page.waitForTimeout(1500);
  expect(Number(await canvas.getAttribute('data-frame'))).toBe(rendered);
  await page.getByRole('button',{name:'처음',exact:true}).click();await check(0);
  await page.getByRole('slider',{name:'저장 시점'}).focus();await page.keyboard.press('ArrowRight');await check(1);
  await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();
  await expect.poll(async()=>Number(await canvas.getAttribute('data-selected-index'))).toBeGreaterThan(1);
  await page.getByRole('button',{name:'일시 정지',exact:true}).click();
  const index=Number(await canvas.getAttribute('data-selected-index'));await check(index);
  await page.waitForTimeout(1100);expect(Number(await canvas.getAttribute('data-selected-index'))).toBe(index);
  expect(errors).toEqual([]);expect(methods.every(m=>m==='GET')).toBe(true);
});

test('narrow screen has usable playback and no document overflow',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/morphology-replay.html');
  await expect(page.locator('canvas')).toHaveAttribute('data-authored-leaf-count','3',{timeout:60_000});
  await page.getByRole('button',{name:'다음',exact:true}).scrollIntoViewIfNeeded();await page.getByRole('button',{name:'다음',exact:true}).click();
  await expect(page.locator('canvas')).toHaveAttribute('data-selected-index','1');
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:resolve('../research/artifacts/morphology-replay-mobile-20261022.png'),fullPage:true});
});

test('changed result bytes leave an explicit hold and no geometry or fallback results',async({page})=>{
  await page.route('**/morphology-replay/frame-2.json',route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));
  await page.goto('/morphology-replay.html');await expect(page.getByRole('status')).toContainText('저장 결과 조회 보류');
  await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('table')).toHaveCount(0);
});

test('unavailable WebGL keeps the original numerical result accessible',async({page})=>{
  await page.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,type:string,...args:unknown[]){
      return type==='webgl2'?null:Reflect.apply(get,this,[type,...args]);
    } as typeof get;
  });await page.goto('/morphology-replay.html');
  await expect(page.getByText('3D 표시 보류:',{exact:false})).toBeVisible();
  await expect(page.locator('tbody tr')).toHaveCount(3);await expect(page.getByRole('button',{name:'전체 보기',exact:true})).toBeDisabled();
});
