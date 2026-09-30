import { test,expect } from '@playwright/test';
import { writeFile } from 'node:fs/promises';

const digest='a'.repeat(64);
const stamp='2026-09-30T00:00:00Z';
const registration={scenario_id:'farm-browser',scenario_revision:'r1',scenario_sha256:digest,
  farm_sha256:'b'.repeat(64),numeric_input_sha256:'c'.repeat(64),
  rights_sha256:'d'.repeat(64),registration_status:'registered_unpublished_inputs',
  intent_job:{job_id:'22222222-2222-4222-8222-222222222222',stage:'collection',state:'queued',
    attempt_count:0,max_attempts:3,created_at:stamp,updated_at:stamp,reason_code:null}};

test('new authored farm is reviewed, retried byte-identically, and server confirmed',async({page},testInfo)=>{
  const calls:string[]=[];
  await page.route('**/v1/farm-authored-inputs',async route=>{
    expect(route.request().method()).toBe('POST');
    expect(route.request().headers().authorization).toBe('Bearer synthetic-authored-form-token');
    calls.push(route.request().postData() ?? '');
    if(calls.length===1)return route.abort('failed');
    return route.fulfill({status:200,json:registration});
  });
  await page.goto('/');
  await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill('synthetic-authored-form-token');
  await page.getByRole('button',{name:'연결 설정'}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행'}).click();
  await page.getByRole('button',{name:'새 입력 판본 작성'}).click();
  await page.setViewportSize({width:1440,height:900});
  await page.screenshot({path:testInfo.outputPath('authored-form-desktop.png')});
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('heading',{name:'농장 조건 직접 등록'}).scrollIntoViewIfNeeded();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
  await page.screenshot({path:testInfo.outputPath('authored-form-phone.png')});
  await page.setViewportSize({width:1440,height:900});
  const fields:Record<string,string>={
    scenario_id:'farm-browser',scenario_revision:'r1',
    research_job_id:'00000000-0000-4000-8000-000000000001',
    snapshot_id:'thermal-snapshot-v1:'+digest,decision_context_id:'context-1',
    decision_at:'2026-09-28T00:00:00Z',market_hold_report_id:'hold-1',
    period_start:'2026-10-01',period_end:'2026-11-30',
    economic_scenario_id:'economic-1',economic_revision:'r1',
    economic_sha256:digest,economic_candidate_id:digest,
    source_ref:'self-authored-browser',record_revision:'r1',
    available_at:'2026-09-28T00:00:00Z',zone_id:'zone-1',
    floor_area:'100',cultivable_area:'80',indoor_volume:'400',
    effective_heat_capacity:'1000000',dry_air_mass:'400',envelope_conductance:'200',
    absorbed_solar_fraction:'0.5',initial_temperature:'293',
    initial_humidity_ratio:'0.008',heater_capacity:'500',heater_setpoint:'293',
    declaration_id:'rights-farm-browser',rights_revision:'r1',
  };
  for(const [key,value] of Object.entries(fields))
    await page.locator(`.authored-composer input[name="${key}"]`).fill(value);
  await page.locator('.authored-composer select[name="tenure"]').selectOption('unknown');
  await page.locator('.authored-composer select[name="decision_basis"]')
    .selectOption('existing_facility_crop_change');
  await page.locator('.authored-composer select[name="heater_available"]').selectOption('yes');
  await page.locator('.authored-composer select[name="objective"]')
    .selectOption('conditional_operating_margin');
  await page.locator('.authored-composer select[name="capex_mode"]').selectOption('unknown');
  await page.locator('.authored-composer select[name="cash_mode"]').selectOption('unknown');
  const forcing=page.locator('.authored-repeat-row').first();
  for(const [key,value] of Object.entries({start:'2026-10-01T00:00:00Z',
    end:'2026-10-01T00:01:00Z',ventilation:'0.02',canopy:'0.0001',ground:'-20'}))
    await forcing.locator(`input[name="${key}"]`).fill(value);
  await page.locator('.authored-rights input').check();
  await page.getByRole('button',{name:'입력 내용 검토'}).click();
  await expect(page.getByRole('region',{name:'제출 전 확인'})).toContainText('farm-browser');
  await page.getByRole('button',{name:'불변 입력 판본 등록'}).click();
  await expect(page.getByRole('alert')).toContainText('같은 입력과 판본');
  await expect(page.locator('.authored-composer input[name="floor_area"]')).toBeDisabled();
  await page.getByRole('button',{name:'같은 입력으로 등록 재확인'}).click();
  await expect(page.getByText('입력 등록됨 · 계산 전')).toBeVisible();
  expect(calls).toHaveLength(2);
  expect(calls[0]).toBe(calls[1]);
  const submittedRaw=calls[1]!;
  await writeFile(testInfo.outputPath('authored-request.json'),submittedRaw);
  const submitted=JSON.parse(submittedRaw) as {farm:{facility:{floor_area:{value:string}},
    constraints:{capex_ceiling:null;minimum_cash:null},crops:unknown[]},
    rights:{redistribute:boolean}};
  expect(submitted.farm.facility.floor_area.value).toBe('100');
  expect(submitted.farm.constraints).toEqual({capex_ceiling:null,minimum_cash:null});
  expect(submitted.farm.crops).toEqual([]);
  expect(submitted.rights.redistribute).toBe(false);
  const saved=await page.evaluate(()=>sessionStorage.getItem('ossf.authored.last-farm.v1'));
  expect(saved).toContain('farm-browser');
  expect(saved).not.toContain('1000000');
});
