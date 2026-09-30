import { ApiError, need, object, member, date, uuid, closed } from './api-validation';
export { ApiError } from './api-validation';
import { createEconomicApi } from './economic-api';
import { createBreakEvenApi } from './break-even-api';
import { createThermalApi } from './thermal-api';
import { createAuthoredThermalApi } from './authored-thermal-api';
import { createAuthoredFarmApi } from './authored-farm-api';
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

export function createApi(token:string, fetcher:typeof fetch = fetch) {
  if (!/^[\x21-\x7e]{20,512}$/.test(token)) throw new ApiError('auth_required');
  async function request(path:string, method='GET', body?:unknown, expected=method==='POST' ? 202 : 200,
    maxBytes=65_536, timeoutMs=30_000):Promise<unknown> {
    const abort = new AbortController(); const timer = setTimeout(()=>abort.abort(),timeoutMs);
    try {
      const response=await fetcher(path,{method,body:body ? JSON.stringify(body) : undefined,
        headers:body ? {'content-type':'application/json',authorization:'Bearer '+token} : {authorization:'Bearer '+token},
        credentials:'omit',redirect:'error',cache:'no-store',signal:abort.signal});
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
      try { return JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes)); }
      catch { throw new ApiError('response_rejected'); }
    } catch(error) {
      if (error instanceof ApiError) throw error;
      throw new ApiError('network_unresolved');
    } finally { clearTimeout(timer); }
  }
  return {
    ...createThermalApi(request),
    ...createAuthoredThermalApi(request),
    ...createAuthoredFarmApi(request,decodeJob),
    ...createEconomicApi(request, decodeJob),
    ...createBreakEvenApi(request, decodeJob),
    async location(intent:LocationIntent) { return decodeLocation(await request('/v1/locations','POST',intent),intent); },
    async job(id:string) {
      need(uuid(id)); const result=decodeJob(await request('/v1/jobs/'+id)); need(result.job_id === id); return result;
    },
    async hold(id:string) { need(uuid(id)); return decodeHold(await request('/v1/jobs/'+id+'/hold-report'),id); },
  };
}
