import { test,expect } from '@playwright/test';
import { cropReferenceResponse,cropReferenceSelection } from './crop-fixture';
import { decodeCropReplay } from '../src/cropReplay';
import { revealConnection } from './connection-fixture';
import { mkdirSync } from 'node:fs';
import { resolve } from 'node:path';

test('stored LAI drives tomato leaflet area at the same UTC as the table and chart, and revocation clears it',async({page})=>{
  const data=decodeCropReplay(cropReferenceResponse(),cropReferenceSelection),errors:string[]=[];
  let revoked=false,gets=0,posts=0;
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST')posts++;});
  await page.route('**/v1/crop-research-results/**',async route=>{
    expect(route.request().method()).toBe('GET');expect(route.request().headers().authorization).toBe('Bearer synthetic-tomato-leaf-only');gets++;
    await route.fulfill(revoked?{status:422,json:{error:{code:'crop_research_hold',message:'Research replay unavailable'}}}:{json:cropReferenceResponse()});
  });
  await page.setViewportSize({width:1440,height:1100});await page.goto('/');await revealConnection(page);
  await page.getByLabel('접근 토큰').fill('synthetic-tomato-leaf-only');await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
  for(const key of Object.keys(labels) as (keyof typeof labels)[])await page.getByLabel(labels[key],{exact:true}).fill(cropReferenceSelection[key]);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await page.getByRole('button',{name:'토마토 잎 면적 3D',exact:true}).click();
  const canvas=page.locator('.tomato-appearance canvas'),reference=Math.max(...data.samples.map(s=>s.lai.value));
  const slider=page.getByRole('slider',{name:'저장 성장 시점 선택'});
  for(const i of [0,2,5]){
    await slider.fill(String(i));const sample=data.samples[i]!;
    await expect(canvas).toHaveAttribute('data-scene-at',sample.at,{timeout:45_000});
    await expect(canvas).toHaveAttribute('data-result-id',data.result_id);
    await expect(canvas).toHaveAttribute('data-payload-sha256',data.manifest.payload_sha256);
    await expect(canvas).toHaveAttribute('data-raw-lai',String(sample.lai.value));
    await expect(canvas).toHaveAttribute('data-reference-lai',String(reference));
    await expect(canvas).toHaveAttribute('data-reproductive-geometry','withheld');
    await expect.poll(async()=>Math.abs(Number(await canvas.getAttribute('data-leaf-area-ratio'))-sample.lai.value/reference)).toBeLessThan(1e-6);
    for(const selector of ['.crop-readout','.crop-chart','.tomato-appearance'])await expect(page.locator(selector)).toHaveAttribute('data-selected-at',sample.at);
    await expect(page.locator('.crop-table tr[aria-selected=true] [data-metric="lai"]')).toHaveAttribute('data-raw-value',String(sample.lai.value));
  }
  await expect(page.getByRole('button',{name:'과실 송이',exact:true})).toBeDisabled();
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  await page.getByRole('button',{name:'잎 가까이',exact:true}).click();await expect(canvas).toHaveAttribute('data-camera-view','leaf');
  const directory=resolve('../research/artifacts');mkdirSync(directory,{recursive:true});
  await page.locator('.crop-scene-panel').screenshot({path:resolve(directory,'tomato-leaf-stored-20261021.png')});
  revoked=true;
  const lookup=page.locator('.crop-lookup');await lookup.locator('summary').click();
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await expect(page.getByRole('alert')).toBeVisible();await expect(page.locator('.tomato-appearance canvas')).toHaveCount(0);
  expect(gets).toBe(2);expect(posts).toBe(0);expect(errors).toEqual([]);
});
