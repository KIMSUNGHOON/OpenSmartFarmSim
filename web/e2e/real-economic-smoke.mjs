// Explicit self-authored synthetic inputs over actual TLS and PostgreSQL.
import {chromium,expect} from '@playwright/test';
import {createInterface} from 'node:readline';
const browser=await chromium.launch();
const context=await browser.newContext({ignoreHTTPSErrors:true});
const page=await context.newPage();const errors=[];
const network=[];const started=Date.now();
page.on('request',request=>{
  const path=new URL(request.url()).pathname;
  if(['/v1/economic-scenarios','/v1/economic-results'].includes(path)) network.push({path,status:'requested',elapsed_ms:Date.now()-started});
});
page.on('response',response=>{
  const path=new URL(response.url()).pathname;
  if(['/v1/economic-scenarios','/v1/economic-results'].includes(path)) network.push({path,status:response.status(),elapsed_ms:Date.now()-started});
});
page.on('requestfailed',request=>{
  const path=new URL(request.url()).pathname;
  if(['/v1/economic-scenarios','/v1/economic-results'].includes(path)) network.push({path,status:'request_failed',elapsed_ms:Date.now()-started});
});
page.on('pageerror',error=>errors.push(error.message));
page.on('console',message=>{if(['error','warning'].includes(message.type()))errors.push(message.type());});
try {
  await page.goto(process.argv[2]);
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill('synthetic-economic-browser-'+'e'.repeat(32));
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'03 경제 가정·계산'}).click();
  const numbers=page.getByRole('region',{name:'숫자 가정',exact:true});
  await numbers.getByRole('button',{name:'목록 조회'}).click();
  await numbers.locator('li button').first().click();
  await page.getByLabel(/^새 가정값/).fill('9007199254740993.0000000001');
  await page.getByLabel('가정을 알게 된 날짜 (UTC)').fill('2026-09-29');
  await page.getByLabel('가정을 알게 된 시각 (UTC)').fill('08:00');
  const registration=page.waitForResponse(response=>response.url().endsWith('/v1/market-user-sources') && response.request().method()==='POST');
  await page.getByRole('button',{name:'새 가정 판본 등록'}).click();
  const registered=await registration;
  expect(registered.status()).toBe(200);
  const savedInput=registered.request().postDataJSON().input;
  expect(savedInput.available_at).toBe('2026-09-29T08:00:00Z');
  expect(savedInput.value).toBe('9007199254740993.0000000001');
  await expect(page.getByText('새 가정 판본 접수됨',{exact:true})).toBeVisible();
  for(const name of ['기준 원장','수급·거시 공동 가정']) {
    const picker=page.getByRole('region',{name,exact:true});
    await picker.getByRole('button',{name:'목록 조회'}).click();
    await picker.locator('li button').first().click();
  }
  await page.getByRole('button',{name:'선택한 가정으로 계산 요청'}).click();
  await expect.poll(async()=>await page.getByText('계산 작업: 대기 중',{exact:true}).isVisible() || await page.getByRole('alert').isVisible(),{timeout:120000}).toBe(true);
  expect(await page.getByRole('alert').allTextContents()).toEqual([]);
  await page.getByText('계산 작업 식별자',{exact:true}).click();
  const jobId=await page.locator('.economic-job-reference code').innerText();
  process.stdout.write(JSON.stringify({stage:'queued',job_id:jobId,source_id:savedInput.input_id,source_revision:savedInput.revision,network})+'\n');
  const input=createInterface({input:process.stdin});const timer=setTimeout(()=>input.close(),180000);
  let expected;
  for await(const line of input){expected=JSON.parse(line);break;}
  clearTimeout(timer);input.close();expect(expected).toBeTruthy();
  await page.getByRole('button',{name:'계산 상태·결과 확인'}).click();
  await expect(page.getByRole('heading',{name:'경제 결과의 평가 상태: 판단 보류',exact:true})).toBeVisible({timeout:45000});
  const labels={revenue_krw:'매출',management_operating_income_krw:'관리용 영업이익',cash_shortage_krw:'현금 부족'};
  for(const [key,label] of Object.entries(labels)) {
    const value=expected.amounts[key];const [whole,fraction]=(value ?? '').split('.');
    const text=value===null ? '미확인' : whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')+(fraction===undefined ? '' : '.'+fraction)+' 원';
    await expect(page.locator('.economic-totals>div').filter({has:page.getByRole('heading',{name:label,exact:true})}).locator('strong')).toHaveText(text);
  }
  const repeat=page.waitForResponse(response=>response.url().endsWith('/v1/economic-results') && response.request().method()==='POST');
  await page.getByRole('button',{name:'같은 계산 요청 다시 확인'}).click();
  expect((await repeat).status()).toBe(202);
  await expect(page.getByRole('button',{name:'같은 계산 요청 다시 확인'})).toBeEnabled();
  await expect(page.locator('.economic-job-reference code')).toHaveText(jobId);
  expect(errors).toEqual([]);
  process.stdout.write(JSON.stringify({stage:'verified',assessment:'hold',duplicate_job:false})+'\n');
} catch(error) {
  process.stderr.write(JSON.stringify({stage:'browser_failed',network,alert:await page.getByRole('alert').allTextContents(),error:String(error).slice(0,350)})+'\n');
  process.exitCode=1;
} finally {await context.close();await browser.close();}
