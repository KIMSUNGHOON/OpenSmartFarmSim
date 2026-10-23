import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
const stored=(i:number)=>JSON.parse(readFileSync(new URL(`../public/leaf-appearance-replay/frame-${i}.json`,import.meta.url),'utf8'));
async function selected(page:Page,index:number){
 const f=stored(index),canvas=page.locator('canvas');
 await expect.poll(async()=>({at:await canvas.getAttribute('data-scene-at'),index:await canvas.getAttribute('data-selected-index'),
  calls:Number(await canvas.getAttribute('data-draw-calls'))>0}),{timeout:60000}).toEqual({at:f.at,index:String(index),calls:true});
 expect(await canvas.getAttribute('data-leaf-artifact-sha256')).toBe(f.artifact_sha256);
 expect(await canvas.getAttribute('data-leaf-result-sha256')).toBe(f.result_sha256);
 expect(await canvas.getAttribute('data-authored-leaf-count')).toBe(String(f.tracked_leaf_count));
 expect(JSON.parse((await canvas.getAttribute('data-rendered-lengths'))!)).toEqual(f.stem.internodes.map((q:{length:{value:number}})=>q.length.value));
 const measured=JSON.parse((await canvas.getAttribute('data-rendered-leaf-areas'))!);expect(measured).toHaveLength(f.leaves.length);
 measured.forEach((q:{leaf_id:string;attachment_internode_id:string;area_m2:number},i:number)=>{
  expect(q.leaf_id).toBe(f.leaves[i].leaf_id);expect(q.attachment_internode_id).toBe(f.leaves[i].attachment_internode_id);
  expect(Math.abs(q.area_m2-f.leaves[i].area.value)/f.leaves[i].area.value).toBeLessThan(1e-9);
 });
 expect(await page.locator('td[data-raw-area]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-area')))).toEqual(f.leaves.map((q:{area:{value:number}})=>String(q.area.value)));
 for(const selector of ['.leaf-area-page','.morphology-summary','.morphology-history','.leaf-area-table'])expect(await page.locator(selector).getAttribute('data-selected-at')).toBe(f.at);
}

test('policy-derived3to5leaves preserve12stored frames/47areas, navigation/reload and idle/mobile',async({page},info)=>{
 const errors:string[]=[],methods:string[]=[],requests:string[]=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
 page.on('request',r=>{methods.push(r.method());if(new URL(r.url()).pathname.startsWith('/leaf-appearance-replay/'))requests.push(new URL(r.url()).pathname);});
 await page.goto('/leaf-appearance-replay.html');await selected(page,0);await expect(page.getByRole('heading',{name:'정책 기반 잎 출현과 줄기',exact:true})).toBeVisible();
 const first=await page.locator('canvas').screenshot();
 for(let index=1;index<12;index++){await page.getByRole('button',{name:'다음',exact:true}).click();await selected(page,index);}
 expect((await page.locator('canvas').screenshot()).equals(first)).toBe(false);expect(requests).toHaveLength(20);
 await page.screenshot({path:info.outputPath('leaf-appearance-last.png'),fullPage:true});
 expect(new URL(page.url()).searchParams.get('frame')).toBe('11');await page.reload();await selected(page,11);
 await page.getByRole('link',{name:'명시 출현 예제 ↗',exact:true}).click();await expect(page).toHaveURL(/leaf-population-replay\.html/);
 await page.goBack();await selected(page,11);
 await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();await selected(page,0);
 await expect.poll(async()=>Number(await page.locator('canvas').getAttribute('data-selected-index')),{timeout:10000}).toBeGreaterThan(0);
 await page.getByRole('button',{name:'일시 정지',exact:true}).click();const index=Number(await page.locator('canvas').getAttribute('data-selected-index'));await selected(page,index);
 const frame=await page.locator('canvas').getAttribute('data-frame');await page.waitForTimeout(1200);expect(await page.locator('canvas').getAttribute('data-frame')).toBe(frame);
 await page.setViewportSize({width:390,height:844});await selected(page,index);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath('leaf-appearance-mobile.png'),fullPage:true});expect(errors).toEqual([]);expect(methods.every(m=>m==='GET')).toBe(true);
});

test('rights/hash hold removes scene/table, restoration reload keeps the same saved frame',async({page})=>{
 await page.goto('/leaf-appearance-replay.html');await selected(page,0);await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,11);
 await page.route('**/leaf-appearance-replay/input.json',async route=>{
  const p=JSON.parse(readFileSync(new URL('../public/leaf-appearance-replay/input.json',import.meta.url),'utf8'));p.rights.display=false;
  await route.fulfill({contentType:'application/json',body:JSON.stringify(p)});
 });
 await page.reload();await expect(page.getByText(/저장 결과 표시 보류/)).toBeVisible();await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('table')).toHaveCount(0);
 await page.unroute('**/leaf-appearance-replay/input.json');await page.reload();await selected(page,11);
});

test('WebGL unavailable retains only original five stored leaves in table',async({page})=>{
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,name,...args){return name==='webgl2'?null:Reflect.apply(original,this,[name,...args]);} as typeof original;});
 await page.setViewportSize({width:390,height:844});await page.goto('/leaf-appearance-replay.html');
 await expect(page.getByText(/3D 표시 보류: WebGL2/)).toBeVisible();await expect(page.locator('td[data-raw-area]')).toHaveCount(3);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await expect(page.locator('td[data-raw-area]')).toHaveCount(5);
 expect(await page.locator('td[data-raw-area]').last().getAttribute('data-raw-area')).toBe(String(stored(11).leaves.at(-1).area.value));
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
