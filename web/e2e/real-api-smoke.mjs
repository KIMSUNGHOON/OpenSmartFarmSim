// Explicit synthetic HTTPS integration, run by backend/tests/web_shell_smoke.py.
import { chromium, expect } from '@playwright/test';
import { createInterface } from 'node:readline';

const token='synthetic-runtime-bearer-'+'r'.repeat(32);
const browser=await chromium.launch();
const context=await browser.newContext({ignoreHTTPSErrors:true});
const page=await context.newPage();
const errors=[];
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{if (['error','warning'].includes(message.type())) errors.push(message.type());});
try {
  await page.goto(process.argv[2]);
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).press('Enter');
  await page.getByRole('button',{name:'합성 예시 채우기'}).press('Enter');
  const received=page.waitForResponse(response=>response.url().endsWith('/v1/locations'));
  await page.getByRole('button',{name:'자료 조사 요청'}).press('Enter');
  const response=await received;
  expect(response.status()).toBe(202);
  await expect(page.getByText('대기 중',{exact:true})).toBeVisible();
  await expect(page.getByLabel('접근 토큰')).toHaveValue('');
  await page.getByText('작업 식별자',{exact:true}).click();
  const jobId=await page.locator('.job-reference code').innerText();
  process.stdout.write(JSON.stringify({stage:'queued',job_id:jobId})+'\n');
  const input=createInterface({input:process.stdin});
  const timeout=setTimeout(()=>{input.close();},30_000);
  let ready=false;
  for await (const line of input) {ready=line==='hold-ready'; break;}
  clearTimeout(timeout);input.close();
  expect(ready).toBe(true);
  await page.getByRole('button',{name:'현재 상태 확인'}).press('Enter');
  await expect(page.getByRole('heading',{name:'판단 보류',exact:true})).toBeVisible();
  await expect(page.getByText('결정 시각을 확인할 서명 근거')).toBeVisible();
  await expect(page.getByText('서버가 확인한 누락 근거 2건입니다.')).toBeVisible();
  await page.getByRole('button',{name:'01 입력 설정'}).click();
  const replay=page.waitForResponse(value=>value.url().endsWith('/v1/locations'));
  await page.getByRole('button',{name:'같은 요청 다시 확인'}).press('Enter');
  const replayResponse=await replay;
  expect(replayResponse.status()).toBe(202);
  await expect(page.locator('.job-reference code')).toHaveText(jobId);
  await page.getByRole('button',{name:'현재 상태 확인'}).click();
  await expect(page.getByText('결정 시각을 확인할 서명 근거')).toBeVisible();
  expect(errors).toEqual([]);
  process.stdout.write(JSON.stringify({stage:'verified',hold_count:2,duplicate_job:false})+'\n');
} finally {await context.close();await browser.close();}
