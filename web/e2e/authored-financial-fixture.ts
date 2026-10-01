// Synthetic HTTP contract doubles; amounts are not agricultural forecasts.
import type { AuthoredEconomicSelection } from '../src/authored-financial-api';
import type { AuthoredThermalSummary } from '../src/authored-thermal-api';
import type { EconomicResult } from '../src/economic-api';
import { authoredJobId,authoredRunId,authoredResponses } from './authored-thermal-fixture';

export const economicId='22222222-2222-4222-8222-222222222222';
export const assessmentId='33333333-3333-4333-8333-333333333333';
export const financialTime='2026-10-01T00:00:00.123456Z';
export function financialResponses() {
  const selected:AuthoredEconomicSelection={schema_version:'authored-economic-selection-v1',
    thermal_run:authoredResponses().summary as AuthoredThermalSummary,
    calculation_input:{input_version:'economic-calculation-input-v3',scenario_id:'economic-1',scenario_revision:'r1',
      scenario_sha256:'f'.repeat(64),candidate_id:'1'.repeat(64),formula_version:'economic-ledger-v9-sales-settlement',
      authored_scenario_id:'farm-1',authored_scenario_revision:'r1',registration_sha256:'a'.repeat(64),thermal_job_id:authoredJobId},
    verification:'requires_admission_recheck'};
  const economic={job_id:economicId,stage:'simulation',state:'succeeded',attempt_count:1,max_attempts:3,
    created_at:financialTime,updated_at:financialTime,reason_code:null};
  const assessment={...economic,job_id:assessmentId,stage:'assessment',state:'hold',reason_code:'validated_hold'};
  const history={schema_version:'authored-financial-history-v1',thermal_job_id:authoredJobId,run_id:authoredRunId,
    items:[{kind:'assessment',job:assessment,economic_job:{...economic}},{kind:'economic',job:economic,economic_job:null}],
    next_cursor:null,verification:'requires_current_read'};
  const result:EconomicResult={economic_result_id:'2'.repeat(64),market_scenario_result_id:'3'.repeat(64),
    scenario_id:'economic-1',scenario_revision:'r1',decision_at_utc:selected.thermal_run.decision_at_utc,
    formula_version:'economic-ledger-v9-sales-settlement',market_context_kind:'unavailable',market_hold_report_id:authoredJobId,
    calculation_status:'conditional_user_assumption',assessment_status:'hold',sales_totals_status:'inventory_reconciled',
    input_origin:'user',evidence_level:'assumed',quantities:{harvest_kg:'20',packout_kg:'10',recognized_kg:'9',net_sold_kg:'8'},
    amounts:{gross_sales_krw:'9007199254740993.0000000001',revenue_krw:'9007199254740993.0000000001',
      variable_cost_krw:'1',fixed_cost_krw:'2',depreciation_krw:null,management_operating_income_krw:null,
      operating_cash_krw:'-3',business_cash_krw:'-4',equity_cash_krw:'-5',minimum_cash_balance_krw:'-7',cash_shortage_krw:'7'},
    hold_reason_codes:['MISSING_DEPRECIATION']};
  const report={job_id:assessmentId,stage:'assessment',hold_id:authoredJobId,status:'hold',recorded_at:financialTime,
    reason_code:'evidence_missing',missing_evidence:['market_source_g0','eligible_crop_candidates',
      'farm_scenario_binding','local_measurements_g2','future_validation_g3a','paired_comparison_g3b'],missing_evidence_count:6};
  const cashIdentity={economic_result_id:result.economic_result_id,market_scenario_result_id:result.market_scenario_result_id,
    scenario_id:result.scenario_id,scenario_revision:result.scenario_revision,decision_at_utc:result.decision_at_utc,
    formula_version:result.formula_version,market_context_kind:result.market_context_kind,market_hold_report_id:result.market_hold_report_id,
    calculation_status:result.calculation_status,assessment_status:result.assessment_status,input_origin:result.input_origin,
    evidence_level:result.evidence_level,hold_reason_codes:result.hold_reason_codes};
  const monthly=Array.from({length:13},(_,index)=>{
    const month=index<12 ? '2026-'+String(index+1).padStart(2,'0') : '2027-01';
    return {month,opening_balance_krw:'-7',net_cash_krw:'0',closing_balance_krw:'-7',minimum_balance_krw:'-7',
      minimum_at_utc:month+'-01T00:00:00Z',cash_shortage_krw:'7'};
  });
  const cash={...cashIdentity,schema_version:'economic-cash-page-v1',calendar_timezone:'Asia/Seoul',series_status:'available',
    total_months:13,limit:12,after_month:null,next_month_cursor:'2026-12',monthly_cash:monthly.slice(0,12)};
  const lastCash={...cash,after_month:'2026-12',next_month_cursor:null,monthly_cash:monthly.slice(12)};
  const catalog={items:[{run_id:authoredRunId,simulation_job_id:authoredJobId,recorded_at:financialTime,
    verification:'requires_current_read'}],next_cursor:null};
  return {selected,economic,assessment,history,result,report,cash,lastCash,catalog};
}
