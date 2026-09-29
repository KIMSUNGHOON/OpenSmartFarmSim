// Actual authenticated TLS API and PG; existing self-authored trial source fixtures.
import {chromium,expect} from '@playwright/test';
import {createInterface} from 'node:readline';
const browser=await chromium.launch(),context=await browser.newContext({ignoreHTTPSErrors:true}),page=await context.newPage();
const network=[],errors=[],started=Date.now(),losePlanReply=process.argv[3]==='lose-plan-reply';let planId,expectedLossMessages=0;
for(const event of ['request','response','requestfailed'])page.on(event,value=>{
  const path=new URL(value.url()).pathname;
  if(['/v1/economic-scenarios','/v1/break-even-plans','/v1/break-even-plans/receipt'].includes(path)
    || path.endsWith('/break-even-result'))network.push({path,event,status:event==='response' ? value.status() : undefined,elapsed_ms:Date.now()-started});
  if(event==='request' && path==='/v1/break-even-plans')planId=value.postDataJSON().request.plan_id;
});
page.on('pageerror',error=>errors.push(error.message));page.on('console',message=>{
  if(!['error','warning'].includes(message.type()))return;
  const location=message.location().url;
  if(location && new URL(location).pathname==='/v1/break-even-plans/receipt'
    && message.text()==='Failed to load resource: the server responded with a status of 404 (Not Found)')return;
  const networkError=message.text().match(/^Failed to load resource: (net::[A-Z_]+)$/)?.[1];
  if(losePlanReply && location && new URL(location).pathname==='/v1/break-even-plans' && networkError==='net::ERR_FAILED') {
    expectedLossMessages++;return;
  }
  errors.push({kind:message.type(),path:location ? new URL(location).pathname : '',networkError});
});
try {
  if(losePlanReply)await page.route('**/v1/break-even-plans',async route=>{
    const actual=await route.fetch();expect(actual.status()).toBe(202);await route.abort();
  });
  await page.goto(process.argv[2]);await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill('synthetic-break-even-browser-'+'b'.repeat(32));await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'03 경제 가정·계산'}).click();const area=page.getByRole('region',{name:'손익분기 계획과 결과',exact:true});
  const baseline=area.getByRole('region',{name:'손익분기 기준 원장',exact:true});await baseline.getByRole('button',{name:'목록 조회'}).click();
  await baseline.locator('li button').filter({has:page.getByText('scenario-1',{exact:true})}).click();
  await expect(area.getByLabel('손익분기 판매·수금')).toBeVisible({timeout:45000});await area.getByLabel('손익분기 판매·수금').selectOption(JSON.stringify(['sale-1','collection-1']));
  await area.getByLabel('손익분기 목표').selectOption('oi');await area.getByLabel('바꿀 변수').selectOption('KRW/kg');
  await area.getByLabel(/^최소 시험값/).fill('20');await area.getByLabel(/^최대 시험값/).fill('32');await area.getByLabel(/^시험값 증분/).fill('12');
  const trials=area.getByRole('region',{name:'손익분기 시험 공동 가정',exact:true});await trials.getByRole('button',{name:'목록 조회'}).click();
  for(const index of [0,1]) {
    await trials.locator('li button').filter({has:page.getByText('joint-trial-'+index,{exact:true})}).click();
    await expect(area.getByRole('button',{name:'이 공동 가정을 시험에 추가'})).toBeEnabled({timeout:45000});await area.getByRole('button',{name:'이 공동 가정을 시험에 추가'}).click();
  }
  await area.getByRole('button',{name:'선택한 시험으로 손익분기 요청'}).click();
  await expect.poll(async()=>await area.getByText('손익분기 작업: 대기 중',{exact:true}).isVisible() || await area.getByRole('alert').isVisible(),{timeout:150000}).toBe(true);
  let recovered=false;
  if(await area.getByRole('alert').isVisible()) {
    await expect.poll(async()=>{
      const response=page.waitForResponse(reply=>new URL(reply.url()).pathname==='/v1/break-even-plans/receipt');
      await area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'}).click();const reply=await response;
      expect([200,404]).toContain(reply.status());
      await expect(area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'})).toBeEnabled();
      recovered=await area.getByText('손익분기 작업: 대기 중',{exact:true}).isVisible();return recovered;
    },{timeout:120000,intervals:[1000,2000,5000]}).toBe(true);
  } else {
    const response=page.waitForResponse(reply=>new URL(reply.url()).pathname==='/v1/break-even-plans/receipt');
    await area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'}).click();
    const reply=await response;expect(reply.status()).toBe(200);
  }
  await expect(area.getByText('손익분기 작업: 대기 중',{exact:true})).toBeVisible({timeout:45000});
  const jobId=await area.locator('.break-even-job-reference code').textContent();expect(jobId).toMatch(/^[0-9a-f-]{36}$/);expect(planId).toBeTruthy();
  process.stdout.write(JSON.stringify({stage:'queued',job_id:jobId,plan_id:planId,network})+'\n');
  const input=createInterface({input:process.stdin}),timer=setTimeout(()=>input.close(),240000);let expected;
  for await(const line of input){expected=JSON.parse(line);break;}clearTimeout(timer);input.close();expect(expected).toBeTruthy();
  await area.getByRole('button',{name:'손익분기 상태·결과 확인'}).click();
  await expect(area.getByRole('heading',{name:'손익분기 결과 · 평가 상태: 판단 보류'})).toBeVisible({timeout:45000});
  await expect(area.locator('tbody tr')).toHaveCount(expected.trials.length);
  const money=value=>{if(value===null)return '미확인';const [whole,fraction]=value.split('.');return whole.replace(/\B(?=(\d{3})+(?!\d))/g,',')+(fraction===undefined ? '' : '.'+fraction)+' 원';};
  for(const [index,row] of expected.trials.entries()) {
    const actual=area.locator('tbody tr').nth(index);await expect(actual.locator('th')).toHaveText(row.value);
    await expect(actual.locator('td')).toHaveText([money(row.target_value_krw),money(row.minimum_cash_balance_krw),money(row.cash_shortage_krw)]);
  }
  await expect(area.getByRole('list',{name:'교차 구간'})).toContainText(expected.brackets[0].join(' ~ '));
  const repeat=page.waitForResponse(response=>new URL(response.url()).pathname==='/v1/break-even-plans/receipt');
  await area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'}).click();const repeated=await repeat;expect(repeated.status()).toBe(200);
  await expect(area.getByRole('button',{name:'같은 손익분기 계획 요청 다시 확인'})).toBeEnabled();
  await expect(area.locator('.break-even-job-reference code')).toHaveText(jobId);expect(errors).toEqual([]);
  expect(expectedLossMessages).toBe(losePlanReply ? 1 : 0);
  expect(network.filter(row=>row.event==='request' && row.path==='/v1/break-even-plans')).toHaveLength(1);
  expect(network.filter(row=>row.event==='request' && row.path==='/v1/economic-scenarios')).toHaveLength(2);
  process.stdout.write(JSON.stringify({stage:'verified',assessment:'hold',duplicate_job:false,network})+'\n');
} catch(error) {
  process.stderr.write(JSON.stringify({stage:'browser_failed',network,alerts:await page.getByRole('alert').allTextContents(),error:String(error).slice(0,350)})+'\n');process.exitCode=1;
} finally {await context.close();await browser.close();}
