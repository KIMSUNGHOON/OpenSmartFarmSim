import { test,expect,type Page } from '@playwright/test';
import { authoredJobId,authoredRunId,authoredResponses } from './authored-thermal-fixture';

const token='synthetic-authored-browser-token-only';

async function connect(page:Page) {
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'05 3D 열 재생'}).click();
}

async function load(page:Page) {
  await page.getByRole('radio',{name:'작성한 농장 열 재생'}).check();
  await page.getByLabel('완료된 열 작업 ID').fill(authoredJobId);
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
}

test('authored job selects one server Run for actual 3D, graph, summary and table',async ({page})=>{
  const errors:string[]=[];
  const paths:string[]=[];
  const data=authoredResponses();
  page.on('pageerror',error=>errors.push(error.message));
  await page.route('**/v1/**',async route=>{
    const request=route.request();
    expect(request.method()).toBe('GET');
    expect(request.headers().authorization).toBe('Bearer '+token);
    const path=new URL(request.url()).pathname;
    paths.push(path);
    expect(path).toMatch(/^\/v1\/(jobs\/|authored-runs\/)/);
    await route.fulfill({json:path.endsWith('/series') ? data.series : data.summary});
  });
  await connect(page);
  await load(page);
  const viewer=page.locator('.replay-viewer');
  await expect(viewer).toHaveAttribute('data-run-id',authoredRunId);
  await expect(viewer).toHaveAttribute('data-replay-kind','authored');
  await expect(page.getByText('작성한 농장 입력 · 합성 열 재생',{exact:true})).toBeVisible();
  await expect(page.getByText(/독립 G1 수용이나 현장 정확도를 뜻하지 않습니다/)).toBeVisible();
  await expect(page.getByText('3D 준비됨',{exact:true})).toBeVisible();
  expect(paths).toEqual(['/v1/jobs/'+authoredJobId+'/authored-run',
    '/v1/authored-runs/'+encodeURIComponent(authoredRunId),
    '/v1/authored-runs/'+encodeURIComponent(authoredRunId)+'/series']);
  const canvas=page.locator('.zone-canvas');
  expect(Number(await canvas.getAttribute('data-draw-calls'))).toBeGreaterThan(0);
  const firstImage=await canvas.screenshot();
  const slider=page.getByRole('slider',{name:'저장 시각 선택'});
  await slider.focus();
  await slider.press('End');
  const selected=data.series.points[119]!;
  for(const selector of ['.replay-viewer','.replay-summary','.replay-chart','.zone-scene']) {
    await expect(page.locator(selector)).toHaveAttribute('data-selected-at',selected.at_utc);
  }
  await expect(canvas).toHaveAttribute('data-scene-at-utc',selected.at_utc);
  for(const key of ['temperature_k','relative_humidity_fraction','humidity_ratio_kg_v_per_kg_da',
    'heat_demand_w_th','heat_delivered_w_th','delivered_heat_energy_kwh_th'] as const) {
    await expect(page.locator('.replay-summary [data-metric="'+key+'"]').first()).toHaveAttribute('data-raw-value',String(selected[key]));
    await expect(page.locator('.replay-table tr[aria-selected=true] [data-metric="'+key+'"]')).toHaveAttribute('data-raw-value',String(selected[key]));
  }
  expect(firstImage.equals(await canvas.screenshot())).toBe(false);
  await page.getByText('작성 입력과 해시',{exact:true}).click();
  await expect(page.getByText(data.summary.registration_sha256,{exact:true})).toBeVisible();
  await expect(page.getByText('합성 출처와 법칙 표시 조건',{exact:true})).toHaveCount(0);
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('.replay-admission').scrollIntoViewIfNeeded();
  await page.screenshot({path:'../research/artifacts/authored-thermal-replay-desktop.png'});
  expect(errors).toEqual([]);
});

test('invalid authored response holds before any 3D scene, and kind changes clear old values',async ({page})=>{
  const data=authoredResponses();
  await page.route('**/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    await route.fulfill({json:path.endsWith('/series') ? data.series : data.summary});
  });
  await connect(page);
  await load(page);
  await expect(page.locator('.replay-viewer')).toBeVisible();
  await page.getByText('완료된 열 작업 선택',{exact:true}).click();
  await page.getByRole('radio',{name:'고정 합성 열 재생'}).check();
  await expect(page.locator('.replay-viewer')).toHaveCount(0);
  await expect(page.getByLabel('완료된 열 작업 ID')).toHaveValue('');
  data.summary.claim_scope='crop_forecast';
  await page.getByRole('radio',{name:'작성한 농장 열 재생'}).check();
  await page.getByLabel('완료된 열 작업 ID').fill(authoredJobId);
  await page.getByRole('button',{name:'저장된 Run 조회'}).click();
  await expect(page.getByRole('alert')).toContainText('표시를 보류');
  await expect(page.locator('.replay-viewer')).toHaveCount(0);
});
