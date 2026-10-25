import {object} from '../src/storedLeafReplayIO';
import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {LEAF_CARBON_STOCK_FIXTURE as FIXTURE} from '../src/leafCarbonStockReplayFixture';
type Scenario=keyof typeof FIXTURE.scenarios;
const scenarios=Object.keys(FIXTURE.scenarios) as Scenario[];
const stored=(scenario:Scenario,index:number)=>JSON.parse(readFileSync(new URL(`../public/leaf-carbon-stock-replay/${scenario}/frame-${index}.json`,import.meta.url),'utf8'));
async function selected(page:Page,scenario:Scenario,index:number){
 const f=stored(scenario,index),canvas=page.locator('canvas');
 await expect.poll(async()=>{const raw=await canvas.getAttribute('data-leaf-clip-bounds');return {index:await canvas.getAttribute('data-selected-index'),checkpoint:await canvas.getAttribute('data-checkpoint-sha256'),
  calls:Number(await canvas.getAttribute('data-draw-calls'))>0,inside:raw!==null&&Math.max(...Object.values(JSON.parse(raw)).map(v=>Math.abs(Number(v))))<=.98};
 },{timeout:15000}).toEqual({index:String(index),checkpoint:f.checkpoint_sha256,calls:true,inside:true});
 expect(JSON.parse((await canvas.getAttribute('data-scene-at'))!)).toEqual(f.at);
 expect(await canvas.getAttribute('data-artifact-sha256')).toBe(f.artifact_sha256);
 expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-ids'))!)).toEqual(f.leaf_ids);
 expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-areas'))!)).toEqual(f.leaves.map((x:{area:{value:number}})=>x.area.value));
 expect(JSON.parse((await canvas.getAttribute('data-stored-leaf-carbons'))!)).toEqual(f.leaves.map((l:{leaf_id:string;carbon:unknown})=>({leaf_id:l.leaf_id,carbon:l.carbon})));
 const surfaces=JSON.parse((await canvas.getAttribute('data-rendered-leaf-areas'))!);
 expect(surfaces).toHaveLength(3);surfaces.forEach((row:{leaf_id:string;area_m2:number},i:number)=>{
  expect(row.leaf_id).toBe(f.leaf_ids[i]);expect(Math.abs(row.area_m2/f.leaves[i].area.value-1)).toBeLessThanOrEqual(5e-12);
 });
 expect(await canvas.getAttribute('data-scaffold-origin')).toBe('authored_visual_asset');
 expect(await canvas.getAttribute('data-scaffold-version')).toBe('authored-three-leaf-scaffold-v1');
 const clip=JSON.parse((await canvas.getAttribute('data-leaf-clip-bounds'))!);
 expect(Math.max(Math.abs(clip.minX),Math.abs(clip.maxX),Math.abs(clip.minY),Math.abs(clip.maxY))).toBeLessThanOrEqual(.98);
 expect(await page.locator('td[data-raw-area]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-area')))).toEqual(f.leaves.map((x:{area:{value:number}})=>String(x.area.value)));
 expect(await page.locator('td[data-raw-carbon]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-carbon')))).toEqual(f.leaves.map((x:{carbon:{value:number}})=>String(x.carbon.value)));
 expect(await page.locator('[data-raw-leaf-carbon-total]').getAttribute('data-raw-leaf-carbon-total')).toBe(String(f.sample.derived.leaf_carbohydrate.value));
 expect(await page.locator('[data-transfer-key]').evaluateAll(nodes=>nodes.map(n=>[n.getAttribute('data-transfer-key'),n.querySelector('[data-raw-transfer]')?.getAttribute('data-raw-transfer')]))).toEqual(Object.entries(f.integrated_transfers).map(([k,v])=>[k,String(object(v).value)]));
 expect(await page.locator('[data-balance-key]').evaluateAll(nodes=>nodes.map(n=>[n.getAttribute('data-balance-key'),n.querySelector('[data-raw-balance]')?.getAttribute('data-raw-balance'),n.querySelector('[data-raw-budget]')?.getAttribute('data-raw-budget')]))).toEqual(Object.entries(f.balance_residuals).map(([k,v])=>[k,String(object(v).value),String(f.balance_budgets[k].value)]));
 expect(await page.locator('td[data-raw-age]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-raw-age')))).toEqual(f.leaves.map((x:{thermal_age:{value:number}})=>String(x.thermal_age.value)));
 expect(await page.locator('[data-raw-lai]').getAttribute('data-raw-lai')).toBe(String(f.sample.derived.leaf_area_index.value));
 expect(await page.locator('[data-raw-air-temperature]').getAttribute('data-raw-air-temperature')).toBe(String(f.climate.air_temperature.value));
 expect(await page.locator('[data-raw-canopy-temperature]').getAttribute('data-raw-canopy-temperature')).toBe(String(f.sample.derived.canopy_temperature.value));
 expect(await page.locator('main').getAttribute('data-selected-index')).toBe(String(index));
 expect(await page.locator('main').getAttribute('data-scenario')).toBe(scenario);
}

for(const scenario of scenarios)test(`${scenario}: all17 stored frames and51 actual surfaces`,async({page},info)=>{
 const errors:string[]=[],warnings:string[]=[],methods:string[]=[],files:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text());});
 page.on('request',request=>{methods.push(request.method());if(new URL(request.url()).pathname.startsWith('/leaf-carbon-stock-replay/'))files.push(new URL(request.url()).pathname);});
 await page.goto(`/leaf-carbon-stock-replay.html?scenario=${scenario}`);await selected(page,scenario,0);
 await expect(page.getByRole('heading',{name:'저장된 잎의 탄소와 면적',exact:true})).toBeVisible();
 for(let i=1;i<17;i++){await page.getByRole('button',{name:'다음',exact:true}).click();await selected(page,scenario,i);}
 expect(files).toHaveLength(46);expect(methods.every(method=>method==='GET')).toBe(true);expect(errors).toEqual([]);
 expect(await page.locator('.morphology-history circle[data-lai]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('data-lai'))))
  .toEqual(Array.from({length:17},(_,i)=>String(stored(scenario,i).sample.derived.leaf_area_index.value)));
 expect(await page.locator('.leaf-carbon-history circle').evaluateAll(nodes=>nodes.map(n=>[n.getAttribute('data-leaf-id'),n.getAttribute('data-index'),n.getAttribute('data-carbon')]))).toEqual(stored(scenario,0).leaf_ids.flatMap((id:string,j:number)=>Array.from({length:17},(_,i)=>[id,String(i),String(stored(scenario,i).leaves[j].carbon.value)])));
 await info.attach('warnings.json',{body:JSON.stringify(warnings),contentType:'application/json'});
 if(scenario==='warm-day-individual-stock')await page.screenshot({path:info.outputPath('leaf-carbon-stock-desktop.png'),fullPage:true});
});

test('same selected source after scenario/menu/reload and keyboard navigation',async({page})=>{
 await page.goto('/leaf-carbon-stock-replay.html');await selected(page,'warm-day-individual-stock',0);
 await page.getByLabel('합성 계산 사례').selectOption('reverse-individual-stock');await selected(page,'reverse-individual-stock',0);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,'reverse-individual-stock',16);
 expect(new URL(page.url()).searchParams.get('artifact')).toBe(FIXTURE.scenarios['reverse-individual-stock'].artifact_sha256);
 await page.reload();await selected(page,'reverse-individual-stock',16);
 await page.getByRole('link',{name:'기존 면적·기후 예제 ↗',exact:true}).click();await expect(page).toHaveURL(/growing-geometry-replay\.html/);
 await page.goBack();await selected(page,'reverse-individual-stock',16);
 const slider=page.getByRole('slider',{name:'저장 시점'});await slider.focus();await slider.press('Home');await selected(page,'reverse-individual-stock',0);
 await slider.press('ArrowRight');await selected(page,'reverse-individual-stock',1);
});

test('replays stored points, stops idle draws and fits a mobile viewport',async({page},info)=>{
 await page.goto('/leaf-carbon-stock-replay.html');await selected(page,'warm-day-individual-stock',0);
 await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();
 await expect.poll(async()=>Number(await page.locator('main').getAttribute('data-selected-index'))).toBeGreaterThan(0);
 await page.getByRole('button',{name:'일시 정지',exact:true}).click();
 const index=Number(await page.locator('main').getAttribute('data-selected-index'));await selected(page,'warm-day-individual-stock',index);
 await page.evaluate(async()=>{await document.fonts.ready;await new Promise<void>(r=>requestAnimationFrame(()=>requestAnimationFrame(()=>r())));});
 const before=await page.locator('canvas').getAttribute('data-frame');await page.waitForTimeout(500);expect(await page.locator('canvas').getAttribute('data-frame')).toBe(before);
 await page.setViewportSize({width:390,height:844});await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,'warm-day-individual-stock',16);
 await page.evaluate(()=>document.fonts.ready);expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath('leaf-carbon-stock-mobile.png'),fullPage:true});
});

test('invalid source fails closed and can be retried',async({page})=>{
 await page.route('**/leaf-carbon-stock-replay/warm-day-individual-stock/frame-16.json',route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));
 await page.goto('/leaf-carbon-stock-replay.html');await expect(page.getByText('저장 결과 표시 보류:',{exact:false})).toBeVisible();
 await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('td[data-raw-area]')).toHaveCount(0);
 await page.unroute('**/leaf-carbon-stock-replay/warm-day-individual-stock/frame-16.json');await page.getByRole('button',{name:'원 결과 다시 확인'}).click();await selected(page,'warm-day-individual-stock',0);
});

test('late old selection cannot replace the current scenario',async({page})=>{
 let release=()=>{},started=()=>{};const gate=new Promise<void>(r=>release=r),observed=new Promise<void>(r=>started=r);
 await page.route('**/leaf-carbon-stock-replay/warm-day-individual-stock/index.json',async route=>{started();await gate;try{await route.continue();}catch{/* cancelled old request */}});
 await page.goto('/leaf-carbon-stock-replay.html',{waitUntil:'domcontentloaded'});await observed;
 await page.getByLabel('합성 계산 사례').selectOption('cool-dark-individual-stock');release();await selected(page,'cool-dark-individual-stock',0);
 await page.waitForTimeout(200);await selected(page,'cool-dark-individual-stock',0);
});

test('context loss clears the rendered scene and keeps original values',async({page})=>{
 await page.goto('/leaf-carbon-stock-replay.html');await selected(page,'warm-day-individual-stock',0);
 await page.locator('canvas').evaluate(canvas=>(canvas as HTMLCanvasElement).getContext('webgl2')!.getExtension('WEBGL_lose_context')!.loseContext());
 await expect(page.getByText('3D 표시 보류: WebGL2를 사용할 수 없습니다.',{exact:false})).toBeVisible();
 expect(await page.locator('canvas').getAttribute('data-checkpoint-sha256')).toBeNull();
 await page.getByRole('button',{name:'다음',exact:true}).click();await expect(page.locator('main')).toHaveAttribute('data-selected-index','1');
 expect(await page.locator('td[data-raw-area]').first().getAttribute('data-raw-area')).toBe(String(stored('warm-day-individual-stock',1).leaves[0].area.value));
});

test.describe('WebGL2 unavailable',()=>{
 test('keeps the same original table and navigation',async({page})=>{
  await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
   HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,name,...args){return name==='webgl2'?null:Reflect.apply(original,this,[name,...args]);} as typeof original;});
  await page.goto('/leaf-carbon-stock-replay.html');await expect(page.getByText('3D 표시 보류: WebGL2를 사용할 수 없습니다.',{exact:false})).toBeVisible();
  await page.getByRole('button',{name:'마지막',exact:true}).click();await expect(page.locator('main')).toHaveAttribute('data-selected-index','16');
  expect(await page.locator('td[data-raw-area]').first().getAttribute('data-raw-area')).toBe(String(stored('warm-day-individual-stock',16).leaves[0].area.value));
 });
});
