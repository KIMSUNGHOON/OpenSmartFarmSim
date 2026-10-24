import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {GROWING_GEOMETRY_REMOVAL_FIXTURE as FIXTURE} from '../src/growingGeometryRemovalReplayFixture';
type Scenario=keyof typeof FIXTURE.scenarios;
const scenarios=Object.keys(FIXTURE.scenarios) as Scenario[];
const stored=(scenario:Scenario,index:number)=>JSON.parse(readFileSync(new URL(`../public/growing-geometry-removal-replay/${scenario}/frame-${index}.json`,import.meta.url),'utf8'));
async function selected(page:Page,scenario:Scenario,index:number){
 const f=stored(scenario,index),canvas=page.locator('canvas');
 await expect.poll(async()=>{const raw=await canvas.getAttribute('data-leaf-clip-bounds');return {index:await canvas.getAttribute('data-selected-index'),checkpoint:await canvas.getAttribute('data-checkpoint-sha256'),
  calls:Number(await canvas.getAttribute('data-draw-calls'))>0,inside:raw!==null&&Math.max(...Object.values(JSON.parse(raw)).map(v=>Math.abs(Number(v))))<=.98};
 },{timeout:15000}).toEqual({index:String(index),checkpoint:f.checkpoint_sha256,calls:true,inside:true});
 expect(JSON.parse((await canvas.getAttribute('data-scene-at'))!)).toEqual(f.at);
 expect(await canvas.getAttribute('data-artifact-sha256')).toBe(f.artifact_sha256);
 expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-ids'))!)).toEqual(f.leaf_ids);
 expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-areas'))!)).toEqual(f.leaves.map((x:{area:{value:number}})=>x.area.value));
 const surfaces=JSON.parse((await canvas.getAttribute('data-rendered-leaf-areas'))!);
 expect(surfaces).toHaveLength(f.leaves.length);surfaces.forEach((row:{leaf_id:string;area_m2:number},i:number)=>{
  expect(row.leaf_id).toBe(f.leaf_ids[i]);expect(Math.abs(row.area_m2/f.leaves[i].area.value-1)).toBeLessThanOrEqual(5e-12);
 });
 expect(await canvas.getAttribute('data-phase')).toBe(f.phase);
 expect(await canvas.getAttribute('data-global-step-index')).toBe(String(f.global_step_index));
 expect(await page.locator('main').getAttribute('data-selected-phase')).toBe(f.phase);
 expect(await page.locator('.morphology-summary').getAttribute('data-selected-phase')).toBe(f.phase);
 expect(await page.locator('.morphology-table').getAttribute('data-selected-phase')).toBe(f.phase);
 expect(JSON.parse((await canvas.getAttribute('data-scaffold-attachments'))!)).toEqual([
  {leaf_id:'own-leaf-0',height_m:.45,yaw_rad:.4},{leaf_id:'own-leaf-1',height_m:.95,yaw_rad:2.8},{leaf_id:'own-leaf-2',height_m:1.4,yaw_rad:5.2}
 ].filter(x=>f.leaf_ids.includes(x.leaf_id)));
 expect(await canvas.getAttribute('data-scaffold-origin')).toBe('authored_visual_asset');
 expect(await canvas.getAttribute('data-scaffold-version')).toBe('authored-three-leaf-scaffold-v1');
 const clip=JSON.parse((await canvas.getAttribute('data-leaf-clip-bounds'))!);
 expect(Math.max(Math.abs(clip.minX),Math.abs(clip.maxX),Math.abs(clip.minY),Math.abs(clip.maxY))).toBeLessThanOrEqual(.98);
 expect(await page.locator('td[data-raw-area]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-area')))).toEqual(f.leaves.map((x:{area:{value:number}})=>String(x.area.value)));
 expect(await page.locator('td[data-raw-age]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-age')))).toEqual(f.leaves.map((x:{thermal_age:{value:number}})=>String(x.thermal_age.value)));
 expect(await page.locator('[data-raw-lai]').getAttribute('data-raw-lai')).toBe(String(f.sample.derived.leaf_area_index.value));
 expect(await page.locator('[data-raw-air-temperature]').getAttribute('data-raw-air-temperature')).toBe(String(f.climate.air_temperature.value));
 expect(await page.locator('[data-raw-canopy-temperature]').getAttribute('data-raw-canopy-temperature')).toBe(String(f.sample.derived.canopy_temperature.value));
 expect(await page.locator('main').getAttribute('data-selected-index')).toBe(String(index));
 expect(await page.locator('main').getAttribute('data-scenario')).toBe(scenario);
}

for(const scenario of scenarios)test(`${scenario}: all18 stored frames and original-ID surfaces`,async({page},info)=>{
 const errors:string[]=[],warnings:string[]=[],methods:string[]=[],files:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text());});
 page.on('request',request=>{methods.push(request.method());if(new URL(request.url()).pathname.startsWith('/growing-geometry-removal-replay/'))files.push(new URL(request.url()).pathname);});
 await page.goto(`/growing-geometry-removal-replay.html?scenario=${scenario}`);await selected(page,scenario,0);
 await expect(page.getByRole('heading',{name:'잎 제거와 이후 생장',exact:true})).toBeVisible();
 for(let i=1;i<18;i++){await page.getByRole('button',{name:'다음',exact:true}).click();await selected(page,scenario,i);}
 expect(files).toHaveLength(54);expect(methods.every(method=>method==='GET')).toBe(true);expect(errors).toEqual([]);
 expect(await page.locator('.morphology-history circle').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-lai'))))
  .toEqual(Array.from({length:18},(_,i)=>String(stored(scenario,i).sample.derived.leaf_area_index.value)));
 await info.attach('warnings.json',{body:JSON.stringify(warnings),contentType:'application/json'});
 if(scenario==='case-0-remove-1')await page.screenshot({path:info.outputPath('growing-geometry-desktop.png'),fullPage:true});
});

test('same selected source after scenario/menu/reload and keyboard navigation',async({page})=>{
 await page.goto('/growing-geometry-removal-replay.html');await selected(page,'case-0-remove-1',0);
 await page.getByLabel('합성 계산 사례').selectOption('case-1-remove-1');await selected(page,'case-1-remove-1',0);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,'case-1-remove-1',17);
 expect(new URL(page.url()).searchParams.get('artifact')).toBe(FIXTURE.scenarios['case-1-remove-1'].artifact_sha256);
 await page.reload();await selected(page,'case-1-remove-1',17);
 await page.getByRole('link',{name:'연속 생장 예제 ↗',exact:true}).click();await expect(page).toHaveURL(/growing-geometry-replay\.html/);
 await page.goBack();await selected(page,'case-1-remove-1',17);
 const slider=page.getByRole('slider',{name:'저장 시점'});await slider.focus();await slider.press('Home');await selected(page,'case-1-remove-1',0);
 await slider.press('ArrowRight');await selected(page,'case-1-remove-1',1);
});

test('replays stored points, stops idle draws and fits a mobile viewport',async({page},info)=>{
 await page.goto('/growing-geometry-removal-replay.html');await selected(page,'case-0-remove-1',0);
 await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();
 await expect.poll(async()=>Number(await page.locator('main').getAttribute('data-selected-index'))).toBeGreaterThan(0);
 await page.getByRole('button',{name:'일시 정지',exact:true}).click();
 const index=Number(await page.locator('main').getAttribute('data-selected-index'));await selected(page,'case-0-remove-1',index);
 await page.evaluate(async()=>{await document.fonts.ready;await new Promise<void>(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r())));});
 const before=await page.locator('canvas').getAttribute('data-frame');await page.waitForTimeout(500);expect(await page.locator('canvas').getAttribute('data-frame')).toBe(before);
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,'case-0-remove-1',17);
 await page.evaluate(()=>document.fonts.ready);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath('growing-geometry-mobile.png'),fullPage:true});
});

test('invalid source fails closed and can be retried',async({page})=>{
 await page.route('**/growing-geometry-removal-replay/case-0-remove-1/frame-17.json',route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await page.goto('/growing-geometry-removal-replay.html');await expect(page.getByText('저장 결과 표시 보류:',{exact:false})).toBeVisible();
 await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('td[data-raw-area]')).toHaveCount(0);
 await page.unroute('**/growing-geometry-removal-replay/case-0-remove-1/frame-17.json');await page.getByRole('button',{name:'원 결과 다시 확인'}).click();await selected(page,'case-0-remove-1',0);
});

test('late old selection cannot replace the current scenario',async({page})=>{
 let release=()=>{},started=()=>{};const gate=new Promise<void>(r=>release=r),observed=new Promise<void>(r=>started=r);
 await page.route('**/growing-geometry-removal-replay/case-0-remove-1/index.json',async route=>{started();await gate;try{await route.continue();}catch{/* cancelled old request */}});
 await page.goto('/growing-geometry-removal-replay.html',{waitUntil:'domcontentloaded'});await observed;
 await page.getByLabel('합성 계산 사례').selectOption('case-2-remove-1');release();await selected(page,'case-2-remove-1',0);
 await page.waitForTimeout(200);await selected(page,'case-2-remove-1',0);
});

test('context loss clears the rendered scene and keeps original values',async({page})=>{
 await page.goto('/growing-geometry-removal-replay.html');await selected(page,'case-0-remove-1',0);
 await page.locator('canvas').evaluate(canvas=>(canvas as HTMLCanvasElement).getContext('webgl2')!.getExtension('WEBGL_lose_context')!.loseContext());
 await expect(page.getByText('3D 표시 보류: WebGL2를 사용할 수 없습니다.',{exact:false})).toBeVisible();
 expect(await page.locator('canvas').getAttribute('data-checkpoint-sha256')).toBeNull();
 await page.getByRole('button',{name:'다음',exact:true}).click();await expect(page.locator('main')).toHaveAttribute('data-selected-index','1');
 expect(await page.locator('td[data-raw-area]').first().getAttribute('data-raw-area')).toBe(String(stored('case-0-remove-1',1).leaves[0].area.value));
});

test.describe('WebGL2 unavailable',()=>{
 test('keeps the same original table and navigation',async({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
   HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,name,...args){return name==='webgl2'?null:Reflect.apply(original,this,[name,...args]);} as typeof original;});
  await page.goto('/growing-geometry-removal-replay.html');await expect(page.getByText('3D 표시 보류: WebGL2를 사용할 수 없습니다.',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'마지막',exact:true}).click();await expect(page.locator('main')).toHaveAttribute('data-selected-index','17');
  expect(await page.locator('td[data-raw-area]').first().getAttribute('data-raw-area')).toBe(String(stored('case-0-remove-1',17).leaves[0].area.value));
 });
});

test('same-time point controls preserve phase, coordinates and retained attachment through reload',async({page})=>{
 await page.goto('/growing-geometry-removal-replay.html?scenario=case-0-remove-2');await selected(page,'case-0-remove-2',0);
 await page.getByRole('button',{name:'제거 직전',exact:true}).click();await selected(page,'case-0-remove-2',7);
 const before=await page.locator('main').getAttribute('data-selected-at');
 await page.getByRole('button',{name:'제거 직후',exact:true}).click();await selected(page,'case-0-remove-2',8);
 expect(await page.locator('main').getAttribute('data-selected-at')).toBe(before);
 const points=await page.locator('.morphology-history circle').evaluateAll(nodes=>nodes.slice(7,9).map(n=>({x:n.getAttribute('cx'),y:n.getAttribute('cy'),phase:n.getAttribute('data-phase')})));
 expect(points[0]!.x).toBe(points[1]!.x);expect(points[0]!.y).not.toBe(points[1]!.y);
 expect(points.map(p=>p.phase)).toEqual(['before_removal','after_removal_before_next_step']);
 await page.reload();await selected(page,'case-0-remove-2',8);
 await page.setViewportSize({width:390,height:844});
 for(const index of [0,7,8,17]){
  await page.getByRole('slider',{name:'저장 시점'}).fill(String(index));await selected(page,'case-0-remove-2',index);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 }
});
