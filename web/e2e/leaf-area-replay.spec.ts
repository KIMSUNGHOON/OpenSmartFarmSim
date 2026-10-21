import { test,expect,type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';

const stored=(i:number)=>JSON.parse(readFileSync(new URL(`../public/leaf-area-replay/frame-${i}.json`,import.meta.url),'utf8'));
async function selected(page:Page,index:number){
  const f=stored(index),canvas=page.locator('canvas');
  await expect.poll(async()=>({at:await canvas.getAttribute('data-scene-at'),index:await canvas.getAttribute('data-selected-index'),
    calls:Number(await canvas.getAttribute('data-draw-calls'))>0}),{timeout:60000}).toEqual({at:f.at,index:String(index),calls:true});
  expect(await canvas.getAttribute('data-leaf-artifact-sha256')).toBe(f.artifact_sha256);
  expect(await canvas.getAttribute('data-leaf-result-sha256')).toBe(f.result_sha256);
  expect(JSON.parse((await canvas.getAttribute('data-rendered-lengths'))!)).toEqual(f.stem.internodes.map((n:{length:{value:number}})=>n.length.value));
  expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-areas'))!)).toEqual(f.leaves.map((q:{area:{value:number}})=>q.area.value));
  const measured=JSON.parse((await canvas.getAttribute('data-rendered-leaf-areas'))!);
  measured.forEach((q:{leaf_id:string;attachment_internode_id:string;area_m2:number},i:number)=>{
    expect(q.leaf_id).toBe(f.leaves[i].leaf_id);expect(q.attachment_internode_id).toBe(f.leaves[i].attachment_internode_id);
    expect(Math.abs(q.area_m2-f.leaves[i].area.value)/f.leaves[i].area.value).toBeLessThan(1e-9);});
  expect(await page.locator('td[data-raw-area]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-area')))).toEqual(f.leaves.map((q:{area:{value:number}})=>String(q.area.value)));
  for(const selector of ['.leaf-area-page','.morphology-summary','.morphology-history','.leaf-area-table'])expect(await page.locator(selector).getAttribute('data-selected-at')).toBe(f.at);
}

test('original leaf surfaces, UTC/table/graph, autoplay and idle with no calculation',async({page},info)=>{
  const errors:string[]=[],methods:string[]=[],requests:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
  page.on('request',r=>{methods.push(r.method());if(new URL(r.url()).pathname.startsWith('/leaf-area-replay/'))requests.push(new URL(r.url()).pathname);});
  await page.goto('/leaf-area-replay.html');await selected(page,0);const first=await page.locator('canvas').screenshot();
  await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,11);
  expect((await page.locator('canvas').screenshot()).equals(first)).toBe(false);
  await page.screenshot({path:info.outputPath('leaf-area-last.png'),fullPage:true});
  await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();
  await expect.poll(async()=>Number(await page.locator('canvas').getAttribute('data-selected-index')),{timeout:10000}).toBeGreaterThan(0);
  await page.getByRole('button',{name:'일시 정지',exact:true}).click();const index=Number(await page.locator('canvas').getAttribute('data-selected-index'));await selected(page,index);
  const frame=await page.locator('canvas').getAttribute('data-frame');await page.waitForTimeout(1200);expect(await page.locator('canvas').getAttribute('data-frame')).toBe(frame);
  await page.setViewportSize({width:390,height:844});await selected(page,index);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:info.outputPath('leaf-area-mobile.png'),fullPage:true});expect(errors).toEqual([]);expect(methods.every(m=>m==='GET')).toBe(true);expect(requests).toHaveLength(17);
});

test('WebGL unavailable retains the original stored table',async({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,name,...args){return name==='webgl2'?null:Reflect.apply(original,this,[name,...args]);} as typeof original;});
  await page.setViewportSize({width:390,height:844});await page.goto('/leaf-area-replay.html');
  await expect(page.getByText(/3D 표시 보류: WebGL2/)).toBeVisible();await expect(page.locator('td[data-raw-area]')).toHaveCount(3);
  await page.getByRole('button',{name:'마지막',exact:true}).click();expect(await page.locator('td[data-raw-area]').first().getAttribute('data-raw-area')).toBe(String(stored(11).leaves[0].area.value));
  await expect(page.locator('canvas')).not.toHaveAttribute('data-draw-calls');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
