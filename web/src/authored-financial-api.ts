import { need,object,closed,date,uuid,member } from './api-validation';
import { decodeAuthoredThermalSummary,type AuthoredThermalSummary } from './authored-thermal-api';
import { decodeEconomicResult,hash } from './economic-api';
import type { JobStatus } from './api';

export type AuthoredEconomicInput={input_version:'economic-calculation-input-v3';scenario_id:string;
  scenario_revision:string;scenario_sha256:string;candidate_id:string;
  formula_version:'economic-ledger-v9-sales-settlement';authored_scenario_id:string;
  authored_scenario_revision:string;registration_sha256:string;thermal_job_id:string};
export type AuthoredEconomicIntent=AuthoredEconomicInput & {idempotency_key:string};
export type AuthoredEconomicSelection={schema_version:'authored-economic-selection-v1';
  thermal_run:AuthoredThermalSummary;calculation_input:AuthoredEconomicInput;
  verification:'requires_admission_recheck'};
export type FinancialCursor={created_at:string;job_id:string};
export type FinancialActivity={kind:'economic';job:JobStatus;economic_job:null}|
  {kind:'assessment';job:JobStatus;economic_job:JobStatus};
export type FinancialHistory={schema_version:'authored-financial-history-v1';thermal_job_id:string;run_id:string;
  items:FinancialActivity[];next_cursor:FinancialCursor|null;verification:'requires_current_read'};
type Request=(path:string,method?:string,body?:unknown,expected?:number)=>Promise<unknown>;
const INPUT=['input_version','scenario_id','scenario_revision','scenario_sha256','candidate_id','formula_version',
  'authored_scenario_id','authored_scenario_revision','registration_sha256','thermal_job_id'] as const;
const SIMULATION=['queued','simulating','succeeded','hold','failed','canceled'] as const;
const ASSESSMENT=['queued','assessing','hold','failed','canceled'] as const;
function identifier(value:unknown):value is string {
  return typeof value==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value);
}
function input(value:unknown):AuthoredEconomicInput {
  need(object(value));closed(value,INPUT);
  need(value.input_version==='economic-calculation-input-v3' && value.formula_version==='economic-ledger-v9-sales-settlement'
    && identifier(value.scenario_id) && identifier(value.scenario_revision) && hash(value.scenario_sha256)
    && hash(value.candidate_id) && identifier(value.authored_scenario_id) && identifier(value.authored_scenario_revision)
    && hash(value.registration_sha256) && uuid(value.thermal_job_id));
  return value as AuthoredEconomicInput;
}
function selection(value:unknown,id:string):AuthoredEconomicSelection {
  need(object(value));closed(value,['schema_version','thermal_run','calculation_input','verification']);
  need(value.schema_version==='authored-economic-selection-v1' && value.verification==='requires_admission_recheck');
  const thermal=decodeAuthoredThermalSummary(value.thermal_run),economic=input(value.calculation_input);
  need(economic.thermal_job_id===id && economic.authored_scenario_id===thermal.scenario_id
    && economic.authored_scenario_revision===thermal.scenario_revision && economic.registration_sha256===thermal.registration_sha256);
  return {...value,thermal_run:thermal,calculation_input:economic} as AuthoredEconomicSelection;
}
function cursor(value:unknown):FinancialCursor {
  need(object(value));closed(value,['created_at','job_id']);need(date(value.created_at) && uuid(value.job_id));
  return {created_at:value.created_at,job_id:value.job_id};
}
function compareInstant(a:string,b:string) {
  const milliseconds=Date.parse(a)-Date.parse(b);
  if(milliseconds)return milliseconds;
  const tail=(value:string)=>(value.match(/\.(\d{1,6})/)?.[1] ?? '').padEnd(6,'0').slice(3);
  return tail(a)<tail(b) ? -1 : tail(a)>tail(b) ? 1 : 0;
}
function before(a:FinancialCursor,b:FinancialCursor) {
  const order=compareInstant(a.created_at,b.created_at);
  return order<0 || order===0 && a.job_id<b.job_id;
}
export function createAuthoredFinancialApi(request:Request,job:(value:unknown)=>JobStatus) {
  return {
    async authoredEconomicSelection(id:string):Promise<AuthoredEconomicSelection> {
      need(uuid(id));return selection(await request('/v1/jobs/'+id+'/authored-economic-input'),id);
    },
    async authoredFinancialHistory(selected:AuthoredEconomicSelection,after?:FinancialCursor):Promise<FinancialHistory> {
      const id=selected.calculation_input.thermal_job_id;selection(selected,id);
      if(after)cursor(after);
      const query=new URLSearchParams({limit:'20'});
      if(after){query.set('before_created_at',after.created_at);query.set('before_job_id',after.job_id);}
      const raw=await request('/v1/jobs/'+id+'/authored-financial-history?'+query);need(object(raw));
      closed(raw,['schema_version','thermal_job_id','run_id','items','next_cursor','verification']);
      need(raw.schema_version==='authored-financial-history-v1' && raw.thermal_job_id===id
        && raw.run_id===selected.thermal_run.run_id && raw.verification==='requires_current_read'
        && Array.isArray(raw.items) && raw.items.length<=20);
      const seen=new Set<string>();let previous=after;
      const items=raw.items.map(value=>{
        need(object(value));closed(value,['kind','job','economic_job']);
        const status=job(value.job);need(!seen.has(status.job_id));seen.add(status.job_id);
        if(previous)need(before(status,previous));previous=status;
        if(value.kind==='economic'){
          need(status.stage==='simulation' && member(status.state,SIMULATION) && value.economic_job===null);
          return {kind:'economic' as const,job:status,economic_job:null};
        }
        need(value.kind==='assessment' && status.stage==='assessment' && member(status.state,ASSESSMENT));
        const parent=job(value.economic_job);need(parent.stage==='simulation' && member(parent.state,SIMULATION)
          && parent.job_id!==status.job_id && parent.job_id!==id);
        return {kind:'assessment' as const,job:status,economic_job:parent};
      });
      const next=raw.next_cursor===null ? null : cursor(raw.next_cursor);
      if(next)need(items.length===20 && next.job_id===previous!.job_id && next.created_at===previous!.created_at);
      return {schema_version:'authored-financial-history-v1',thermal_job_id:id,run_id:raw.run_id,
        items,next_cursor:next,verification:'requires_current_read'};
    },
    async calculateAuthored(intent:AuthoredEconomicIntent):Promise<JobStatus> {
      need(object(intent));closed(intent,[...INPUT,'idempotency_key']);
      input(Object.fromEntries(INPUT.map(key=>[key,intent[key]])));need(identifier(intent.idempotency_key));
      const result=job(await request('/v1/economic-results','POST',intent));
      need(result.stage==='simulation' && member(result.state,SIMULATION));return result;
    },
    async authoredEconomicJob(id:string):Promise<JobStatus> {
      need(uuid(id));const result=job(await request('/v1/jobs/'+id));
      need(result.job_id===id && result.stage==='simulation' && member(result.state,SIMULATION));return result;
    },
    async authoredEconomicResult(id:string,selected:AuthoredEconomicSelection) {
      need(uuid(id));selection(selected,selected.calculation_input.thermal_job_id);
      const result=decodeEconomicResult(await request('/v1/jobs/'+id+'/economic-result'));
      need(result.scenario_id===selected.calculation_input.scenario_id
        && result.scenario_revision===selected.calculation_input.scenario_revision
        && compareInstant(result.decision_at_utc,selected.thermal_run.decision_at_utc)===0);
      return result;
    },
  };
}
