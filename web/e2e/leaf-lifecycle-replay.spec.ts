import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
type Scenario='no-removal'|'with-removal';
const stored=(index:number,scenario:Scenario='with-removal')=>JSON.parse(readFileSync(new URL(`../public/leaf-lifecycle-replay/${scenario}/frame-${index}.json`,import.meta.url),'utf8'));
async function selected(page:Page,index:number,scenario:Scenario='with-removal'){
 const f=stored(index,scenario),canvas=page.locator('canvas');
 await expect(page.locator('main')).toHaveAttribute('data-scenario',scenario);
 await expect.poll(async()=>({at:await canvas.getAttribute('data-scene-at'),index:await canvas.getAttribute('data-selected-index'),
  root:await canvas.getAttribute('data-leaf-artifact-sha256'),calls:Number(await canvas.getAttribute('data-draw-calls'))>0}),{timeout:60000})
  .toEqual({at:f.at,index:String(index),root:f.artifact_sha256,calls:true});
 expect(await canvas.getAttribute('data-leaf-result-sha256')).toBe(f.result_sha256);
 expect(await canvas.getAttribute('data-authored-leaf-count')).toBe(String(f.active_leaf_count));
 const surfaces=JSON.parse((await canvas.getAttribute('data-rendered-leaf-areas'))!);expect(surfaces).toHaveLength(f.active_leaves.length);
 surfaces.forEach((q:{leaf_id:string;attachment_internode_id:string;area_m2:number},i:number)=>{
  expect(q.leaf_id).toBe(f.active_leaves[i].leaf_id);expect(q.attachment_internode_id).toBe(f.active_leaves[i].attachment_internode_id);
  expect(Math.abs(q.area_m2-f.active_leaves[i].area.value)/f.active_leaves[i].area.value).toBeLessThan(1e-9);
 });
 expect(await page.locator('td[data-raw-area]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-area')))).toEqual(f.active_leaves.map((q:{area:{value:number}})=>String(q.area.value)));
 expect(await page.locator('td[data-last-area]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-last-area')))).toEqual(f.removed_leaves.map((q:{area:{value:number}})=>String(q.area.value)));
 expect(await page.locator('td[data-last-at]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-last-at')))).toEqual(f.removed_leaves.map((q:{last_at_elapsed_seconds_exact:{numerator:string;denominator:string}})=>`${q.last_at_elapsed_seconds_exact.numerator}/${q.last_at_elapsed_seconds_exact.denominator}`));
 expect(await page.locator('.lifecycle-pending tr[data-leaf-id]').count()).toBe(f.pending_leaf_count);
 expect(await page.locator('[data-active-area]').getAttribute('data-active-area')).toBe(String(f.active_leaf_area.value));
 for(const selector of ['main','.morphology-summary','.morphology-history','.lifecycle-active','.lifecycle-removed','.lifecycle-pending'])
  expect(await page.locator(selector).getAttribute('data-selected-at')).toBe(f.at);
}

test('two actual saved scenarios retain24UTC frames and73active surfaces, compare/reload/menu/mobile/idle',async({page},info)=>{
 const errors:string[]=[],warnings:string[]=[],methods:string[]=[],requests:string[]=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text());});
 page.on('request',r=>{methods.push(r.method());if(new URL(r.url()).pathname.startsWith('/leaf-lifecycle-replay/'))requests.push(new URL(r.url()).pathname);});
 await page.goto('/leaf-lifecycle-replay.html');await selected(page,0);await expect(page.getByRole('heading',{name:'잎 생장과 관리',exact:true})).toBeVisible();
 const first=await page.locator('canvas').screenshot();
 for(let i=1;i<12;i++){await page.getByRole('button',{name:'다음',exact:true}).click();await selected(page,i);}
 expect((await page.locator('canvas').screenshot()).equals(first)).toBe(false);
 await page.screenshot({path:info.outputPath('lifecycle-removed-last.png'),fullPage:true});
 await page.getByLabel('관리 시나리오').selectOption('no-removal');await selected(page,11,'no-removal');
 await page.getByRole('button',{name:'처음',exact:true}).click();await selected(page,0,'no-removal');
 for(let i=1;i<12;i++){await page.getByRole('button',{name:'다음',exact:true}).click();await selected(page,i,'no-removal');}
 expect(requests).toHaveLength(40);
 expect(await page.locator('.morphology-history circle').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-area'))))
  .toEqual(Array.from({length:12},(_,i)=>String(stored(i,'no-removal').active_leaf_area.value)));
 expect(new URL(page.url()).searchParams.get('scenario')).toBe('no-removal');expect(new URL(page.url()).searchParams.get('frame')).toBe('11');
 await page.reload();await selected(page,11,'no-removal');
 await page.getByRole('link',{name:'제거 전 출현 예제 ↗',exact:true}).click();await expect(page).toHaveURL(/leaf-appearance-replay\.html/);
 await page.goBack();await selected(page,11,'no-removal');
 const slider=page.getByRole('slider',{name:'저장 시점'});await slider.focus();await slider.press('Home');await selected(page,0,'no-removal');await slider.press('ArrowRight');await selected(page,1,'no-removal');
 await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();await expect.poll(async()=>Number(await page.locator('canvas').getAttribute('data-selected-index')),{timeout:10000}).toBeGreaterThan(1);
 await page.getByRole('button',{name:'일시 정지',exact:true}).click();await page.waitForTimeout(300);
 const index=Number(await page.locator('canvas').getAttribute('data-selected-index'));await selected(page,index,'no-removal');
 const draws=await page.locator('canvas').getAttribute('data-frame');await page.waitForTimeout(1200);expect(await page.locator('canvas').getAttribute('data-frame')).toBe(draws);
 await page.setViewportSize({width:390,height:844});await selected(page,index,'no-removal');expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath('lifecycle-mobile.png'),fullPage:true});
 await info.attach('console-warnings.json',{body:JSON.stringify(warnings),contentType:'application/json'});
 expect(errors).toEqual([]);expect(methods.every(m=>m==='GET')).toBe(true);
});

test('invalid rights/hash removes all results; restoration reload retains same scenario/frame',async({page})=>{
 await page.goto('/leaf-lifecycle-replay.html');await selected(page,0);await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,11);
 await page.route('**/leaf-lifecycle-replay/with-removal/management.json',async route=>{
  const p=JSON.parse(readFileSync(new URL('../public/leaf-lifecycle-replay/with-removal/management.json',import.meta.url),'utf8'));p.rights.display=false;
  await route.fulfill({contentType:'application/json',body:JSON.stringify(p)});
 });
 await page.reload();await expect(page.getByText(/저장 결과 표시 보류/)).toBeVisible();await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('table')).toHaveCount(0);
 await page.unroute('**/leaf-lifecycle-replay/with-removal/management.json');await page.reload();await selected(page,11);
});

test('WebGL unavailable retains original active/removed/pending tables and timeline',async({page})=>{
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,name,...args){return name==='webgl2'?null:Reflect.apply(original,this,[name,...args]);} as typeof original;});
 await page.setViewportSize({width:390,height:844});await page.goto('/leaf-lifecycle-replay.html');
 await expect(page.getByText(/3D 표시 보류: WebGL2/)).toBeVisible();await expect(page.locator('td[data-raw-area]')).toHaveCount(2);await expect(page.locator('td[data-last-area]')).toHaveCount(1);
 await expect(page.locator('.lifecycle-pending tr[data-leaf-id]')).toHaveCount(2);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await expect(page.locator('td[data-raw-area]')).toHaveCount(3);await expect(page.locator('td[data-last-area]')).toHaveCount(2);
 expect(await page.locator('td[data-raw-area]').last().getAttribute('data-raw-area')).toBe(String(stored(11).active_leaves.at(-1).area.value));
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('explicit empty geometry renders original stems without fixed fallback leaves',async({page})=>{
 await page.goto('/e2e/leaf-lifecycle-empty-harness.html');
 await expect(page.getByText(/새 작물 계산 결과가 아닙니다/)).toBeVisible();
 const canvas=page.locator('canvas');await expect.poll(async()=>Number(await canvas.getAttribute('data-draw-calls')),{timeout:60000}).toBeGreaterThan(0);
 expect(await canvas.getAttribute('data-authored-leaf-count')).toBe('0');expect(await canvas.getAttribute('data-rendered-leaf-areas')).toBe('[]');
 expect(JSON.parse((await canvas.getAttribute('data-rendered-lengths'))!)).toEqual(stored(11).stem.internodes.map((q:{length:{value:number}})=>q.length.value));
});
