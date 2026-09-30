// Actual HTTPS/PG integration; all farm inputs and CLI authority are synthetic.
import { chromium,expect } from '@playwright/test';
import { createInterface } from 'node:readline';

const [origin,thermal,economic]=process.argv.slice(2);
const token='synthetic-assessment-browser-'+'a'.repeat(32);
const browser=await chromium.launch();
const context=await browser.newContext({ignoreHTTPSErrors:true});
const page=await context.newPage();
const errors=[];const replies=[];let posts=0;
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{if(['error','warning'].includes(message.type()))errors.push(message.type());});
page.on('response',response=>{if(response.url().includes('/v1/'))replies.push(response.status());});
page.on('request',request=>{if(request.url().endsWith('/v1/assessments'))posts++;});
try {
  await page.goto(origin);
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).press('Enter');
  await page.getByRole('button',{name:'06 계산 평가'}).press('Enter');
  await page.getByLabel('완료 열 계산 작업 ID').fill(thermal);
  await page.getByLabel('완료 경제 계산 작업 ID').fill(economic);
  const admitted=page.waitForResponse(response=>response.url().endsWith('/v1/assessments'));
  await page.getByRole('button',{name:'계산 평가 요청',exact:true}).press('Enter');
  const response=await admitted;expect(response.status()).toBe(202);
  const job=await response.json();expect(job.stage).toBe('assessment');expect(job.state).toBe('queued');
  await expect(page.getByText('대기 중',{exact:true})).toBeVisible();
  process.stdout.write(JSON.stringify({event:'queued',job_id:job.job_id})+'\n');
  const input=createInterface({input:process.stdin});
  const timeout=setTimeout(()=>input.close(),60_000);
  let ready=false;
  for await(const line of input){ready=line==='hold-ready';break;}
  clearTimeout(timeout);input.close();expect(ready).toBe(true);
  await page.getByRole('button',{name:'평가 상태 확인',exact:true}).press('Enter');
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toBeVisible({timeout:30_000});
  await expect(page.getByText('서버가 기록한 누락 근거 6건입니다.')).toBeVisible();
  await expect(page.getByText('같은 조건의 작물 대응 비교',{exact:true})).toBeVisible();
  await page.reload();
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'06 계산 평가'}).click();
  await page.getByLabel('저장 평가 작업 ID').fill(job.job_id);
  await page.getByRole('button',{name:'저장 평가 조회'}).press('Enter');
  await expect(page.getByRole('heading',{name:'판단 보류 근거'})).toBeVisible({timeout:30_000});
  expect(posts).toBe(1);expect(replies).toEqual([202,200,200,200,200]);expect(errors).toEqual([]);
  process.stdout.write(JSON.stringify({event:'verified',hold_count:6,post_count:posts,
    https_responses:replies.length,console_errors:errors.length})+'\n');
} finally {await context.close();await browser.close();}
