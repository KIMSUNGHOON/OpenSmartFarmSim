import { test,expect } from '@playwright/test';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

test('real geometry renders and camera controls change the WebGL view without crop requests',async({page})=>{
  const errors:string[]=[],api:string[]=[];
  page.on('pageerror',error=>errors.push(error.message));
  page.on('request',request=>{if(new URL(request.url()).pathname.startsWith('/v1/'))api.push(request.url());});
  await page.setViewportSize({width:1440,height:1000});
  await page.goto('/crop-appearance.html');
  const scene=page.locator('canvas');
  await expect(scene).toHaveAttribute('data-appearance-version','authored-tomato-appearance-v1',{timeout:60_000});
  await expect(page.getByText('외형 연구용 · 생장 계산 연결 전')).toBeVisible();
  const folder=resolve('../research/artifacts');mkdirSync(folder,{recursive:true});
  await page.screenshot({path:resolve(folder,'tomato-appearance-plant-20261021.png')});
  const original=await scene.screenshot();
  await page.getByRole('button',{name:'과실 송이',exact:true}).click();
  await expect(scene).toHaveAttribute('data-camera-view','truss');
  const truss=await scene.screenshot();expect(Buffer.compare(original,truss)).not.toBe(0);
  await page.screenshot({path:resolve(folder,'tomato-appearance-truss-20261021.png')});
  const frame=Number(await scene.getAttribute('data-frame'));
  await page.getByRole('button',{name:'오른쪽으로 회전'}).click();
  await expect.poll(async()=>Number(await scene.getAttribute('data-frame'))).toBeGreaterThan(frame);
  expect(Buffer.compare(truss,await scene.screenshot())).not.toBe(0);
  await page.getByRole('button',{name:'잎 가까이',exact:true}).click();
  await expect(scene).toHaveAttribute('data-camera-view','leaf');
  await page.screenshot({path:resolve(folder,'tomato-appearance-leaf-20261021.png')});
  await expect(page.getByRole('slider')).toHaveCount(0);
  expect(errors).toEqual([]);expect(api).toEqual([]);
});

test('narrow viewport retains camera controls and readable scope',async({page})=>{
  await page.setViewportSize({width:390,height:844});await page.goto('/crop-appearance.html');
  await expect(page.locator('canvas')).toHaveAttribute('data-appearance-version','authored-tomato-appearance-v1',{timeout:60_000});
  await expect(page.getByText('외형 연구용 · 생장 계산 연결 전')).toBeVisible();
  for(const name of ['전체 식물','과실 송이','잎 가까이'])await expect(page.getByRole('button',{name,exact:true})).toBeInViewport();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
  await page.screenshot({path:resolve('../research/artifacts/tomato-appearance-narrow-20261021.png'),fullPage:true});
});

test('unavailable WebGL leaves an explicit fallback',async({page})=>{
  await page.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext=function(this:HTMLCanvasElement,type:string,...args:unknown[]){
      return type==='webgl2'?null:Reflect.apply(get,this,[type,...args]);
    } as typeof get;
  });
  await page.goto('/crop-appearance.html');
  await expect(page.getByText('이 환경에서 3D를 표시할 수 없습니다.',{exact:false})).toBeVisible();
  await expect(page.getByRole('button',{name:'과실 송이',exact:true})).toBeDisabled();
});
