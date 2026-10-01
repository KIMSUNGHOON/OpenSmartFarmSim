import type { Page } from '@playwright/test';
import type { SourceResearch,SourceActivityPage } from '../src/api';
import type { SourceFarmSelection,FarmEconomicCandidate,FarmEconomicSelection } from '../src/source-farm-api';

export const sourceToken='synthetic-source-farm-browser-token';
const hash='a'.repeat(64),stamp='2026-10-01T00:00:00.123456Z';
export const source:SourceFarmSelection={selection_version:'owned-source-farm-selection-v1',
  claim_scope:'software_fixture_only',assessment_status:'hold',g0_status:'not_accepted',g1_status:'not_accepted',
  requires_registration_recheck:true,research_job_id:'11111111-1111-4111-8111-111111111111',research_attempt:1,
  research_decision_id:'33333333-3333-4333-8333-333333333333',research_input_sha256:hash,
  research_artifact_sha256:hash,collection_job_id:'22222222-2222-4222-8222-222222222222',collection_attempt:1,
  collection_input_sha256:hash,collection_record_sha256:hash,point:{latitude:35,longitude:127},
  period_start_utc:'2026-10-15T00:00:00Z',period_end_utc:'2026-10-15T02:00:00Z',
  goal_id:'historical-thermal-replay',provider_id:'project-fixture:manifest-v2',registry_sha256:hash,bundle_sha256:hash,
  snapshot_id:'thermal-snapshot-v1:'+hash,manifest_sha256:hash,weather_sha256:hash,thermal_sha256:hash,
  decision_context_id:'context-1',context_sha256:hash,decision_at_utc:'2026-09-28T00:00:00.123456Z',
  claim_mode:'ex_post_replay',decision_time_kind:'hypothetical'};
const job={state:'succeeded' as const,attempt_count:1,max_attempts:3,created_at:stamp,updated_at:stamp,reason_code:null};
export const research:SourceResearch={job:{...job,job_id:source.research_job_id,stage:'research'},point:source.point,
  period_start_utc:source.period_start_utc,period_end_utc:source.period_end_utc,goal_id:source.goal_id,current_authority:'available'};
export const collection={...job,job_id:source.collection_job_id,stage:'collection' as const};
export const activity:SourceActivityPage={research_job_id:source.research_job_id,
  items:[{kind:'review',job:{...job,job_id:'44444444-4444-4444-8444-444444444444',stage:'collection_review',state:'hold'},
    collection_job:collection},{kind:'collection',job:collection,collection_job:null}],next_cursor:null};
export const candidate:FarmEconomicCandidate={economic:{scenario_id:'economic-1',revision:'r1',sha256:hash,candidate_id:hash},
  market_context:{kind:'unavailable',hold_report_id:'market-hold-v1:'+hash},period_start:'2026-10-01',
  period_end:'2026-10-31',recorded_at:stamp};
export const selected:FarmEconomicSelection={...candidate,source,verification:'requires_registration_recheck'};
export const sourcePath='/v1/source-history/'+source.research_job_id+'/collections/'+source.collection_job_id;
export const explicitFields:Record<string,string>={scenario_id:'farm-browser',scenario_revision:'r1',
  source_ref:'self-authored-browser',record_revision:'r1',available_at:'2026-09-28T00:00:00Z',zone_id:'zone-1',
  floor_area:'100',cultivable_area:'80',indoor_volume:'400',effective_heat_capacity:'1000000',dry_air_mass:'400',
  envelope_conductance:'200',absorbed_solar_fraction:'0.5',initial_temperature:'293',initial_humidity_ratio:'0.008',
  heater_capacity:'500',heater_setpoint:'293',declaration_id:'rights-farm-browser',rights_revision:'r1'};

export async function routeSourceFixture(page:Page) {
  await page.route('**/v1/**',async route=>{
    const path=new URL(route.request().url()).pathname;
    const json=path==='/v1/source-history'?{items:[research],next_cursor:null}:
      path==='/v1/source-history/'+source.research_job_id?{research,collection,review:activity.items[0]!.job}:
      path==='/v1/source-history/'+source.research_job_id+'/activity'?activity:
      path===sourcePath+'/farm-input-references'?source:
      path===sourcePath+'/economic-candidates'?{verification:'requires_current_selection',source,items:[candidate],next_cursor:null}:
      path===sourcePath+'/economic-candidates/'+candidate.economic.candidate_id?selected:null;
    return route.fulfill(json?{status:200,json}:{status:404,json:{code:'not_available'}});
  });
}
export async function openComposer(page:Page,token=sourceToken) {
  await page.goto('/');await page.getByText('내부 시험 연결',{exact:true}).click();
  await page.getByLabel('접근 토큰').fill(token);await page.getByRole('button',{name:'연결 설정',exact:true}).click();
  await page.getByRole('button',{name:'04 작성 농장 실행',exact:true}).click();
  await page.getByRole('button',{name:'새 입력 판본 작성',exact:true}).click();
}
export async function chooseSource(page:Page) {
  await page.getByRole('button',{name:'저장 조사 조회',exact:true}).click();
  await page.getByRole('button',{name:/좌표 35, 127/}).click();
  await page.getByRole('button',{name:/원본 수집 · 작업 완료/}).click();
}
export async function chooseEconomics(page:Page) {
  await page.getByRole('button',{name:'경제 판본 조회',exact:true}).click();
  await page.getByRole('button',{name:'economic-1 r1 현재 참조 확인',exact:true}).click();
}
export async function fillExplicitFarm(page:Page) {
  for(const [key,value] of Object.entries(explicitFields))await page.locator(`.authored-composer input[name="${key}"]`).fill(value);
  for(const [key,value] of Object.entries({tenure:'unknown',decision_basis:'existing_facility_crop_change',
    heater_available:'yes',objective:'conditional_operating_margin',capex_mode:'unknown',cash_mode:'unknown'}))
    await page.locator(`.authored-composer select[name="${key}"]`).selectOption(value);
  const forcing=page.locator('.authored-repeat-row').first();
  for(const [key,value] of Object.entries({start:source.period_start_utc,end:source.period_end_utc,
    ventilation:'0.02',canopy:'0.0001',ground:'-20'}))await forcing.locator(`input[name="${key}"]`).fill(value);
}
