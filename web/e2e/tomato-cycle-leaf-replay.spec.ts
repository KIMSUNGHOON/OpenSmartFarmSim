import { test,expect } from '@playwright/test';
import { readFileSync,mkdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { cycleReference } from './cycle-crop-fixture';
import { decodeCalculationCycleCropResponse } from '../src/calculationCycleCropReplay';
import { revealConnection } from './connection-fixture';

const original=cycleReference();
const raw=JSON.parse(readFileSync(new URL('./calculation-cycle-crop-prefix-recorded-responses.json',import.meta.url),'utf8'));
const calculated=(raw.long as Record<string,any>[]).map(row=>decodeCalculationCycleCropResponse(row,{result_id:row.result_id,...row.farm}));
const calculationSummary=calculated.find(row=>row.summary!==null)!;
const calculation={summary:calculationSummary,samples:calculated.flatMap(row=>row.page?.kind==='samples'?row.page.records:[]),
  events:calculated.flatMap(row=>row.page?.kind==='events'?row.page.records:[])};

for(const kind of ['original','calculation'] as const)test(`${kind} cycle reuses a stored endpoint across pages and clears tomato rendering after a denied lookup`,async({page})=>{
  const data=kind==='original'?original:calculation,last=data.samples.at(-1)!;
  const path=kind==='original'?'crop-cycle-research-results':'crop-cycle-calculation-research-results';
  const token='synthetic-windowed-tomato-only',errors:string[]=[],calls:{kind:string;offset:number;limit:number}[]=[];
  let denied=false,posts=0;
  page.on('pageerror',error=>errors.push(error.message));page.on('request',request=>{if(request.method()==='POST')posts++;});
  await page.route('**/v1/'+path+'/**',async route=>{
    expect(route.request().headers().authorization).toBe('Bearer '+token);expect(route.request().method()).toBe('GET');
    if(denied){await route.fulfill({status:422,json:{error:{code:'crop_cycle_research_hold',message:'Research unavailable'}}});return;}
    const q=new URL(route.request().url()).searchParams,view=q.get('view')!,offset=Number(q.get('offset')),limit=Number(q.get('limit'));
    calls.push({kind:view,offset,limit});
    if(view==='summary'){await route.fulfill({json:data.summary});return;}
    const rows=view==='samples'?data.samples:data.events,records=rows.slice(offset,offset+limit),next=offset+records.length;
    await route.fulfill({json:{...data.summary,summary:null,page:{kind:view,offset,limit,total:rows.length,
      next_offset:next<rows.length?next:null,records}}});
  });
  await page.setViewportSize({width:1440,height:1100});await page.goto('/');await revealConnection(page);
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'08 성장 연구 3D',exact:true}).click();
  await page.getByLabel('저장 결과 판본').selectOption(kind==='original'?'cycle':'calculation-cycle');
  const labels={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
  const lookup={...data.summary.farm,result_id:data.summary.result_id};
  for(const key of Object.keys(labels) as (keyof typeof labels)[])await page.getByLabel(labels[key],{exact:true}).fill(lookup[key]);
  await page.getByRole('button',{name:'저장 연구 조회',exact:true}).click();
  await page.getByRole('button',{name:'토마토 잎 면적 3D',exact:true}).click();
  const canvas=page.locator('.tomato-appearance canvas');
  await expect(canvas).toHaveAttribute('data-scene-at',last.at,{timeout:45_000});
  await expect(canvas).toHaveAttribute('data-reference-lai',String(last.lai.value));
  await expect(canvas).toHaveAttribute('data-payload-sha256',data.summary.reference.payload_sha256);
  await expect(canvas).toHaveAttribute('data-reproductive-geometry','withheld');
  await expect(page.locator('.coupled-viewer')).toHaveAttribute('data-selected-index',String(data.summary.reference.sample_count-1));
  await page.getByLabel('원 저장 시점 번호').fill('1');
  await page.getByRole('button',{name:'저장 시점으로 이동',exact:true}).click();
  const first=data.samples[0]!;
  await expect(canvas).toHaveAttribute('data-scene-at',first.at,{timeout:45_000});
  await expect(canvas).toHaveAttribute('data-reference-lai',String(last.lai.value));
  await expect(canvas).toHaveAttribute('data-raw-lai',String(first.lai.value));
  await expect.poll(async()=>Math.abs(Number(await canvas.getAttribute('data-leaf-area-ratio'))-first.lai.value/last.lai.value)).toBeLessThan(1e-6);
  for(const selector of ['.coupled-viewer','.coupled-readout','.coupled-history','.tomato-appearance'])
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',first.at);
  await expect(page.getByRole('button',{name:'과실 송이',exact:true})).toBeDisabled();
  expect(calls.filter(call=>call.kind==='summary')).toHaveLength(1);
  expect(calls.filter(call=>call.kind==='samples').map(call=>call.offset)).toEqual([0,data.summary.reference.sample_count-1,0]);
  expect(calls.filter(call=>call.kind==='samples').every(call=>call.limit===7)).toBe(true);
  mkdirSync(resolve('../research/artifacts'),{recursive:true});
  await page.locator('.tomato-appearance').screenshot({path:resolve(`../research/artifacts/tomato-cycle-${kind}-20261021.png`)});
  denied=true;await page.getByRole('button',{name:'마지막 저장 시점',exact:true}).click();
  await expect(page.getByRole('alert')).toBeVisible();await expect(canvas).toHaveCount(0);
  expect(errors).toEqual([]);expect(posts).toBe(0);
});
