import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {COMPLETE_CROP_FIXTURE as F} from '../src/completeCropReplayFixture';
const stored=(s:string,i:number)=>JSON.parse(readFileSync(new URL(`../public/complete-crop-replay/${s}/frame-${i}.json`,import.meta.url),'utf8')).frame;

async function selected(page:Page,scenario:keyof typeof F.scenarios,index:number){
 const f=stored(scenario,index),n=f.leaves.length,state=f.evidence.checkpoint?.last_confirmed.state??f.snapshot.state;
 const canvas=page.locator('canvas');await expect(canvas).toHaveAttribute('data-selected-index',String(index),{timeout:60000});
 const actual=await canvas.evaluate(c=>({d:{...c.dataset},areas:[...document.querySelectorAll('td[data-raw-area]')].map(n=>n.getAttribute('data-raw-area')),
  carbons:[...document.querySelectorAll('td[data-raw-carbon]')].map(n=>n.getAttribute('data-raw-carbon')),
  ages:[...document.querySelectorAll('td[data-raw-age]')].map(n=>n.getAttribute('data-raw-age')),
  lengths:[...document.querySelectorAll('td[data-raw-length]')].map(n=>n.getAttribute('data-raw-length')),
  parents:[...document.querySelectorAll('tr[data-leaf-id]')].map(n=>[n.getAttribute('data-leaf-id'),n.getAttribute('data-parent-id')]),
  scopes:[...document.querySelectorAll('[data-selected-at]')].map(n=>n.getAttribute('data-selected-at')),
  points:[...document.querySelectorAll(`circle[data-index="${c.dataset.selectedIndex}"]`)].map(n=>n.getAttribute('data-stored-value'))}));
 expect(JSON.parse(actual.d.sceneAt!)).toEqual(f.at);expect(actual.d.artifactSha256).toBe(F.scenarios[scenario].artifact_sha256);
 expect(actual.d.phase).toBe(f.phase);expect(actual.d.checkpointSha256).toBe(f.evidence.checkpoint_sha256??'');
 expect(Number(actual.d.drawCalls)).toBeGreaterThan(0);expect(Number(actual.d.triangles)).toBeGreaterThan(0);
 const surfaces=JSON.parse(actual.d.renderedLeafAreas!)as {leaf_id:string;attachment_internode_id:string;area_m2:number}[];
 expect(surfaces).toHaveLength(n);
 for(let j=0;j<n;j++){
  const l=f.leaves[j],mesh=surfaces.find(q=>q.leaf_id===l.leaf_id)!;
  expect(mesh.attachment_internode_id).toBe(l.attachment_internode_id);expect(Math.abs(mesh.area_m2/state[107+n+j]-1)).toBeLessThan(5e-12);
 }
 expect(actual.areas).toEqual(state.slice(107+n,107+2*n).map(String));expect(actual.carbons).toEqual(state.slice(107+2*n).map(String));
 expect(actual.ages).toEqual(state.slice(107,107+n).map(String));
 expect(actual.parents).toEqual(f.leaves.map((l:{leaf_id:string;attachment_internode_id:string})=>[l.leaf_id,l.attachment_internode_id]));
 expect(actual.lengths).toEqual(f.shoot.internodes.map((q:{length:{value:number}})=>String(q.length.value)));
 expect(JSON.parse(actual.d.renderedLengths!)).toEqual(f.shoot.internodes.map((q:{internode_id:string;length:{value:number}})=>({internode_id:q.internode_id,length_m:q.length.value})));
 expect(actual.scopes.length).toBe(4);actual.scopes.forEach(q=>expect(JSON.parse(q!)).toEqual(f.at));
 expect(actual.points).toEqual([String(f.tracked_leaf_area.value),String(f.shoot.tracked_axis_length.value)]);
 return actual;
}

for(const scenario of Object.keys(F.scenarios)as (keyof typeof F.scenarios)[]){
 test(`all stored times, original triangle surfaces/lengths/parents: ${scenario}`,async({page},info)=>{
  test.setTimeout(120000);const errors:string[]=[],warnings:string[]=[],methods:string[]=[],paths=new Set<string>();
  page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());if(m.type()==='warning')warnings.push(m.text());});
  page.on('request',r=>{methods.push(r.method());const p=new URL(r.url()).pathname;if(p.startsWith(`/complete-crop-replay/${scenario}/`))paths.add(p);});
  await page.goto(`/complete-crop-replay.html?scenario=${scenario}`);await selected(page,scenario,0);const first=await page.locator('canvas').screenshot();
  for(let i=1;i<F.scenarios[scenario].frames;i++){await page.getByRole('slider',{name:'저장 시점',exact:true}).press('ArrowRight');await selected(page,scenario,i);}
  expect((await page.locator('canvas').screenshot()).equals(first)).toBe(false);
  expect(paths.size).toBe(F.scenarios[scenario].public_files);expect(methods.every(m=>m==='GET')).toBe(true);expect(errors).toEqual([]);
  await info.attach('actual-console-warnings',{body:JSON.stringify(warnings),contentType:'application/json'});
  if(scenario==='additional-0')await page.screenshot({path:info.outputPath('complete-crop-desktop.png'),fullPage:true});
 });
}
test('menu/reload, playback, idle, mobile camera and latest scenario',async({page},info)=>{
 test.setTimeout(120000);await page.goto('/complete-crop-replay.html');await selected(page,'initial-0',0);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,'initial-0',68);await page.reload();await selected(page,'initial-0',68);
 await page.getByRole('link',{name:'제작 외형 보기 ↗',exact:true}).click();await expect(page).toHaveURL(/\/crop-appearance.html/);
 await page.goBack();await selected(page,'initial-0',68);
 await page.getByRole('button',{name:'저장 결과 재생',exact:true}).click();
 await expect.poll(async()=>Number(await page.locator('canvas').getAttribute('data-selected-index')),{timeout:15000}).toBeLessThan(68);
 await expect.poll(async()=>Number(await page.locator('canvas').getAttribute('data-selected-index')),{timeout:15000}).toBeGreaterThan(0);
 await page.getByRole('button',{name:'일시 정지',exact:true}).click();const index=Number(await page.locator('canvas').getAttribute('data-selected-index'));
 await selected(page,'initial-0',index);const count=await page.locator('canvas').getAttribute('data-frame');await page.waitForTimeout(1200);
 expect(await page.locator('canvas').getAttribute('data-frame')).toBe(count);
 const canvas=page.locator('canvas'),rect=await canvas.boundingBox();expect(rect).not.toBeNull();const before=await canvas.screenshot();
 await page.mouse.move(rect!.x+rect!.width*.5,rect!.y+rect!.height*.5);await page.mouse.down();await page.mouse.move(rect!.x+rect!.width*.65,rect!.y+rect!.height*.56,{steps:8});await page.mouse.up();
 expect((await canvas.screenshot()).equals(before)).toBe(false);await selected(page,'initial-0',index);
 await page.mouse.wheel(0,-240);await selected(page,'initial-0',index);expect(new URL(page.url()).searchParams.get('frame')).toBe(String(index));
 await page.setViewportSize({width:390,height:844});const previous=await canvas.getAttribute('data-frame');await page.getByRole('button',{name:'전체 보기',exact:true}).click();
 await expect.poll(()=>canvas.getAttribute('data-frame')).not.toBe(previous);await selected(page,'initial-0',index);
 const bounds=JSON.parse((await page.locator('canvas').getAttribute('data-leaf-clip-bounds'))!);expect(Math.max(...Object.values(bounds).map(v=>Math.abs(Number(v))))).toBeLessThan(1);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:info.outputPath('complete-crop-mobile.png'),fullPage:true});
 await page.getByRole('combobox',{name:'저장된 합성 사례'}).selectOption('initial-2');await page.getByRole('combobox',{name:'저장된 합성 사례'}).selectOption('additional-4');
 await selected(page,'additional-4',0);expect(new URL(page.url()).searchParams.get('scenario')).toBe('additional-4');
});
test('changed source holds all 3D/table/graph and reload restores exact saved state',async({page})=>{
 await page.goto('/complete-crop-replay.html');await selected(page,'initial-0',0);await page.getByRole('button',{name:'마지막',exact:true}).click();await selected(page,'initial-0',68);
 await page.route('**/complete-crop-replay/initial-0/index.json',route=>route.fulfill({contentType:'application/json',body:'{}'}));await page.reload();
 await expect(page.getByText(/저장 결과 표시 보류/)).toBeVisible();await expect(page.locator('canvas')).toHaveCount(0);await expect(page.locator('table')).toHaveCount(0);await expect(page.locator('svg')).toHaveCount(0);
 await page.unroute('**/complete-crop-replay/initial-0/index.json');await page.getByRole('button',{name:'원 결과 다시 확인',exact:true}).click();await selected(page,'initial-0',68);
});
test('WebGL unavailable keeps verified original table on mobile',async({page})=>{
 await page.addInitScript(()=>{const original=HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,name,...args){return name==='webgl2'?null:Reflect.apply(original,this,[name,...args]);} as typeof original;});
 await page.setViewportSize({width:390,height:844});await page.goto('/complete-crop-replay.html?scenario=additional-0');
 await expect(page.getByText(/3D 표시 보류: WebGL2/)).toBeVisible({timeout:60000});await expect(page.locator('td[data-raw-area]')).toHaveCount(3);
 await page.getByRole('button',{name:'마지막',exact:true}).click();await expect(page.locator('td[data-raw-area]')).toHaveCount(7);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});
