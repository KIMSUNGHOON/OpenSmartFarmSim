import { ApiError, need, object, member, date, uuid, closed } from './api-validation';
export { ApiError } from './api-validation';
import { createEconomicApi } from './economic-api';
import { createBreakEvenApi } from './break-even-api';
import { createThermalApi } from './thermal-api';
import { createAuthoredThermalApi } from './authored-thermal-api';
import { createAuthoredFarmApi } from './authored-farm-api';
import { createAuthoredFinancialApi } from './authored-financial-api';
import { createSourceFarmApi } from './source-farm-api';
import { createCropReplayApi } from './cropReplay';
import { createCoupledCropReplayApi } from './coupledCropReplay';
import { createStartupCropReplayApi } from './startupCropReplay';
import { createCycleCropReplayApi } from './cycleCropReplay';
export const STAGES = ['research','collection','collection_review','simulation','assessment'] as const;
export const STATES = ['queued','researching','collecting','reviewing','simulating','assessing',
  'succeeded','hold','failed','canceled'] as const;
export const EVIDENCE = ['research_source_evidence','signed_decision_context','real_source_g0',
  'market_source_g0','eligible_crop_candidates','farm_scenario_binding','local_measurements_g2',
  'future_validation_g3a','paired_comparison_g3b','other_evidence'] as const;
export type Stage = typeof STAGES[number];
export type State = typeof STATES[number];
export type Evidence = typeof EVIDENCE[number];
export type JobStatus = { job_id:string; stage:Stage; state:State; attempt_count:number; max_attempts:number;
  created_at:string; updated_at:string; reason_code:string|null };
export type LocationIntent = { latitude:number; longitude:number; period_start_utc:string;
  period_end_utc:string; goal_id:string; idempotency_key:string };
export type LocationAccepted = { location_id:string; point:{latitude:number;longitude:number};
  spatial_support:'pending_research'; research_job:JobStatus };
export type JobHold = { job_id:string; stage:'research'|'collection_review'|'assessment'; hold_id:string;
  status:'hold'; recorded_at:string; reason_code:'evidence_missing'|'decision_held';
  missing_evidence:Evidence[]; missing_evidence_count:number };
export type SourceIntent={parent_job_id:string;idempotency_key:string};
export type CalculationAssessmentIntent={run_job_id:string;economic_job_id:string;idempotency_key:string};
const ASSESSMENT_STATES=['queued','assessing','hold','failed','canceled'] as const;
export type SourceResearch={job:JobStatus;point:{latitude:number;longitude:number};
  period_start_utc:string;period_end_utc:string;goal_id:string;current_authority:'available'|'hold'};
export type SourceHistoryDetail={research:SourceResearch;collection:JobStatus|null;review:JobStatus|null};
export type SourceHistoryPage={items:SourceResearch[];next_cursor:{created_at:string;job_id:string}|null};
export type SourceActivityItem={kind:'collection';job:JobStatus;collection_job:null}|
  {kind:'review';job:JobStatus;collection_job:JobStatus};
export type SourceActivityPage={research_job_id:string;items:SourceActivityItem[];
  next_cursor:SourceHistoryPage['next_cursor']};

const CODE = /^[a-z][a-z0-9_]{0,79}$/;
function integer(value:unknown):value is number { return typeof value === 'number' && Number.isSafeInteger(value); }
function decodeJob(value:unknown):JobStatus {
  need(object(value));
  closed(value,['job_id','stage','state','attempt_count','max_attempts','created_at','updated_at','reason_code']);
  need(uuid(value.job_id) && member(value.stage,STAGES) && member(value.state,STATES));
  need(integer(value.attempt_count) && value.attempt_count >= 0 && integer(value.max_attempts)
    && value.max_attempts >= 1 && value.max_attempts <= 3 && value.attempt_count <= value.max_attempts);
  need(date(value.created_at) && date(value.updated_at));
  need(value.reason_code === null || typeof value.reason_code === 'string' && CODE.test(value.reason_code));
  return {job_id:value.job_id,stage:value.stage,state:value.state,attempt_count:value.attempt_count,
    max_attempts:value.max_attempts,created_at:value.created_at,updated_at:value.updated_at,reason_code:value.reason_code};
}
function decodeAssessmentJob(value:unknown,id?:string) {
  const result=decodeJob(value);
  need(result.stage==='assessment' && member(result.state,ASSESSMENT_STATES) &&
    (!id || result.job_id===id));
  return {...result,stage:result.stage,state:result.state};
}
function decodeLocation(value:unknown, intent:LocationIntent):LocationAccepted {
  need(object(value)); closed(value,['location_id','point','spatial_support','research_job']);
  need(typeof value.location_id === 'string' && /^location-v1-[0-9a-f]{64}$/.test(value.location_id));
  need(value.spatial_support === 'pending_research' && object(value.point));
  closed(value.point,['latitude','longitude']);
  need(value.point.latitude === intent.latitude && value.point.longitude === intent.longitude);
  const research_job=decodeJob(value.research_job); need(research_job.stage === 'research');
  return {location_id:value.location_id,point:{latitude:intent.latitude,longitude:intent.longitude},
    spatial_support:value.spatial_support,research_job};
}
function decodeHold(value:unknown, jobId:string):JobHold {
  need(object(value));
  closed(value,['job_id','stage','hold_id','status','recorded_at','reason_code','missing_evidence','missing_evidence_count']);
  need(value.job_id === jobId && member(value.stage,['research','collection_review','assessment'] as const)
    && uuid(value.hold_id) && value.status === 'hold' && date(value.recorded_at));
  need(member(value.reason_code,['evidence_missing','decision_held'] as const));
  need(Array.isArray(value.missing_evidence) && value.missing_evidence.every(entry=>member(entry,EVIDENCE)));
  need(integer(value.missing_evidence_count) && value.missing_evidence_count >= value.missing_evidence.length
    && value.missing_evidence_count <= 50 && value.missing_evidence.length <= 50);
  return {job_id:jobId,stage:value.stage,hold_id:value.hold_id,status:value.status,recorded_at:value.recorded_at,
    reason_code:value.reason_code,missing_evidence:value.missing_evidence,missing_evidence_count:value.missing_evidence_count};
}

function decodeSourceResearch(value:unknown):SourceResearch {
  need(object(value));closed(value,['job','point','period_start_utc','period_end_utc','goal_id','current_authority']);
  const job=decodeJob(value.job);need(job.stage==='research');
  need(object(value.point));closed(value.point,['latitude','longitude']);
  need(typeof value.point.latitude==='number' && Number.isFinite(value.point.latitude) &&
    Math.abs(value.point.latitude)<=90 && typeof value.point.longitude==='number' &&
    Number.isFinite(value.point.longitude) && Math.abs(value.point.longitude)<=180);
  need(date(value.period_start_utc) && date(value.period_end_utc) &&
    typeof value.goal_id==='string' && value.goal_id.length>0 && value.goal_id.length<=200 &&
    member(value.current_authority,['available','hold'] as const));
  return {job,point:{latitude:value.point.latitude,longitude:value.point.longitude},
    period_start_utc:value.period_start_utc,period_end_utc:value.period_end_utc,
    goal_id:value.goal_id,current_authority:value.current_authority};
}
function decodeSourceHistoryPage(value:unknown):SourceHistoryPage {
  need(object(value));closed(value,['items','next_cursor']);
  need(Array.isArray(value.items) && value.items.length<=50);
  const items=value.items.map(decodeSourceResearch);
  let next_cursor:SourceHistoryPage['next_cursor']=null;
  if(value.next_cursor!==null){
    need(object(value.next_cursor));closed(value.next_cursor,['created_at','job_id']);
    need(date(value.next_cursor.created_at) && uuid(value.next_cursor.job_id));
    next_cursor={created_at:value.next_cursor.created_at,job_id:value.next_cursor.job_id};
  }
  return {items,next_cursor};
}
function decodeSourceHistoryDetail(value:unknown,id:string):SourceHistoryDetail {
  need(object(value));closed(value,['research','collection','review']);
  const research=decodeSourceResearch(value.research);need(research.job.job_id===id);
  const collection=value.collection===null?null:decodeJob(value.collection);
  const review=value.review===null?null:decodeJob(value.review);
  need((!collection || collection.stage==='collection') && (!review || review.stage==='collection_review')
    && (!review || !!collection));
  return {research,collection,review};
}
function decodeSourceActivity(value:unknown,id:string):SourceActivityPage {
  need(object(value));closed(value,['research_job_id','items','next_cursor']);
  need(value.research_job_id===id && Array.isArray(value.items) && value.items.length<=20);
  const items:SourceActivityItem[]=value.items.map(entry=>{
    need(object(entry));closed(entry,['kind','job','collection_job']);
    const job=decodeJob(entry.job);
    if(entry.kind==='collection'){
      need(job.stage==='collection' && entry.collection_job===null);
      return {kind:'collection',job,collection_job:null};
    }
    need(entry.kind==='review' && job.stage==='collection_review');
    const parent=decodeJob(entry.collection_job);need(parent.stage==='collection');
    return {kind:'review',job,collection_job:parent};
  });
  need(new Set(items.map(item=>item.job.job_id)).size===items.length);
  let next_cursor:SourceActivityPage['next_cursor']=null;
  if(value.next_cursor!==null){
    need(object(value.next_cursor));closed(value.next_cursor,['created_at','job_id']);
    need(date(value.next_cursor.created_at) && uuid(value.next_cursor.job_id) &&
      items.length===20 && items[19]?.job.created_at===value.next_cursor.created_at &&
      items[19]?.job.job_id===value.next_cursor.job_id);
    next_cursor={created_at:value.next_cursor.created_at,job_id:value.next_cursor.job_id};
  }
  return {research_job_id:id,items,next_cursor};
}

export function createApi(token:string, fetcher:typeof fetch = fetch) {
  if (!/^[\x21-\x7e]{20,512}$/.test(token)) throw new ApiError('auth_required');
  async function request(path:string, method='GET', body?:unknown, expected=method==='POST' ? 202 : 200,
    maxBytes=65_536, timeoutMs=30_000, externalSignal?:AbortSignal):Promise<unknown> {
    const abort = new AbortController(); const timer = setTimeout(()=>abort.abort(),timeoutMs);
    const cancel=()=>abort.abort();
    externalSignal?.addEventListener('abort',cancel,{once:true});
    try {
      if(externalSignal?.aborted)throw new ApiError('request_canceled');
      const response=await fetcher(path,{method,body:body ? JSON.stringify(body) : undefined,
        headers:body ? {'content-type':'application/json',authorization:'Bearer '+token} : {authorization:'Bearer '+token},
        credentials:'omit',redirect:'error',cache:'no-store',signal:abort.signal});
      if(externalSignal?.aborted){
        await response.body?.cancel().catch(()=>{});
        throw new ApiError('request_canceled');
      }
      if (!response.ok) {
        const codes:Record<number,string> = {401:'auth_required',403:'access_denied',404:'not_available',
          409:'intent_conflict',413:'too_large',422:'invalid_request'};
        throw new ApiError(codes[response.status] ?? 'server_unavailable',response.status);
      }
      need(response.status === expected);
      need(response.headers.get('content-type')?.split(';')[0]?.trim() === 'application/json');
      const reader=response.body?.getReader(); need(reader);
      const chunks:Uint8Array[]=[]; let length=0;
      try {
        for (;;) {
          const {value,done}=await reader.read(); if (done) break;
          length+=value.byteLength; need(length <= maxBytes); chunks.push(value);
        }
      } finally { await reader.cancel().catch(()=>{}); reader.releaseLock(); }
      const bytes=new Uint8Array(length); let offset=0;
      for (const chunk of chunks) { bytes.set(chunk,offset); offset+=chunk.byteLength; }
      if(externalSignal?.aborted)throw new ApiError('request_canceled');
      try { return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); }
      catch { throw new ApiError('response_rejected'); }
    } catch(error) {
      if(externalSignal?.aborted)throw new ApiError('request_canceled');
      if (error instanceof ApiError) throw error;
      throw new ApiError('network_unresolved');
    } finally { clearTimeout(timer);externalSignal?.removeEventListener('abort',cancel); }
  }
  return {
    ...createCropReplayApi(request),
    ...createCoupledCropReplayApi(request),
    ...createStartupCropReplayApi(request),
    ...createCycleCropReplayApi(request),
    ...createThermalApi(request),
    ...createAuthoredThermalApi(request),
    ...createAuthoredFarmApi(request,decodeJob),
    ...createAuthoredFinancialApi(request,decodeJob),
    ...createSourceFarmApi(request),
    ...createEconomicApi(request, decodeJob),
    ...createBreakEvenApi(request, decodeJob),
    async location(intent:LocationIntent) { return decodeLocation(await request('/v1/locations','POST',intent),intent); },
    async sourceHistory(cursor?:SourceHistoryPage['next_cursor']) {
      const query=cursor?'?'+new URLSearchParams({before_created_at:cursor.created_at,
        before_job_id:cursor.job_id}).toString():'';
      return decodeSourceHistoryPage(await request('/v1/source-history'+query));
    },
    async sourceHistoryDetail(id:string) {
      need(uuid(id));return decodeSourceHistoryDetail(await request('/v1/source-history/'+id),id);
    },
    async sourceActivity(id:string,cursor?:SourceActivityPage['next_cursor']) {
      need(uuid(id));
      if(cursor)need(date(cursor.created_at) && uuid(cursor.job_id));
      const query=cursor?'?'+new URLSearchParams({before_created_at:cursor.created_at,
        before_job_id:cursor.job_id}).toString():'';
      return decodeSourceActivity(await request('/v1/source-history/'+id+'/activity'+query),id);
    },
    async ingestSource(intent:SourceIntent) {
      need(uuid(intent.parent_job_id) && /^[\x21-\x7e]{1,200}$/.test(intent.idempotency_key));
      const result=decodeJob(await request('/v1/ingestions','POST',{
        research_job_id:intent.parent_job_id,idempotency_key:intent.idempotency_key}));
      need(result.stage==='collection');return result;
    },
    async reviewSource(intent:SourceIntent) {
      need(uuid(intent.parent_job_id) && /^[\x21-\x7e]{1,200}$/.test(intent.idempotency_key));
      const result=decodeJob(await request('/v1/collection-reviews','POST',{
        collection_job_id:intent.parent_job_id,idempotency_key:intent.idempotency_key}));
      need(result.stage==='collection_review');return result;
    },
    async assessCalculations(intent:CalculationAssessmentIntent) {
      need(uuid(intent.run_job_id) && uuid(intent.economic_job_id) &&
        /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(intent.idempotency_key));
      return decodeAssessmentJob(await request('/v1/assessments','POST',{
        run_job_id:intent.run_job_id,economic_job_id:intent.economic_job_id,
        idempotency_key:intent.idempotency_key}));
    },
    async assessmentJob(id:string) {
      need(uuid(id));return decodeAssessmentJob(await request('/v1/jobs/'+id),id);
    },
    async assessmentHold(id:string) {
      need(uuid(id));const result=decodeHold(await request('/v1/jobs/'+id+'/hold-report'),id);
      need(result.stage==='assessment');return {...result,stage:result.stage};
    },
    async job(id:string) {
      need(uuid(id)); const result=decodeJob(await request('/v1/jobs/'+id)); need(result.job_id === id); return result;
    },
    async hold(id:string) { need(uuid(id)); return decodeHold(await request('/v1/jobs/'+id+'/hold-report'),id); },
  };
}
