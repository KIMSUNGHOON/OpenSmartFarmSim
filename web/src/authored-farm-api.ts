import { closed,date,need,object,uuid } from './api-validation';
import type { JobStatus } from './api';

const IDENTIFIER=/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/;
const DIGEST=/^[0-9a-f]{64}$/;
const RUN=/^authored-thermal-run-v1:[0-9a-f]{64}$/;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number,
  timeoutMs?:number)=>Promise<unknown>;
type Identity={scenario_id:string;scenario_revision:string};
export type AuthoredFarmRequest={schema_version:'farm-authoring-request-v1';
  farm:Identity & Record<string,unknown>;rights:Identity & Record<string,unknown>};
export type AuthoredFarmSummary=Identity & {scenario_sha256:string;farm_sha256:string;
  numeric_input_sha256:string;rights_sha256:string;
  registration_status:'registered_unpublished_inputs';intent_job:JobStatus};
export type AuthoredFarmCursor={created_at:string;job_id:string};
export type AuthoredFarmPage={items:AuthoredFarmSummary[];next_cursor:AuthoredFarmCursor|null};
export type AuthoredFarmActivity=
  {kind:'review';job:JobStatus;review_job:null}|
  {kind:'simulation';job:JobStatus;review_job:JobStatus};
export type AuthoredFarmActivityPage=Identity & {registration_sha256:string;
  items:AuthoredFarmActivity[];next_cursor:AuthoredFarmCursor|null};
export type AuthoredRunRef={run_id:string;simulation_job_id:string;recorded_at:string;
  verification:'requires_current_read'};
export type AuthoredRunCursor={recorded_at:string;run_id:string};
export type AuthoredRunCatalog={items:AuthoredRunRef[];next_cursor:AuthoredRunCursor|null};
export type AuthoredReviewIntent=Identity & {registration_sha256:string;idempotency_key:string};
export type AuthoredRunIntent=AuthoredReviewIntent & {review_job_id:string};

function identifier(value:unknown):value is string {
  return typeof value==='string' && IDENTIFIER.test(value);
}
function digest(value:unknown):value is string {
  return typeof value==='string' && DIGEST.test(value);
}
function identity(value:Identity) {
  need(identifier(value.scenario_id) && identifier(value.scenario_revision));
}
function summary(value:unknown,expected:Identity|null,decodeJob:(value:unknown)=>JobStatus):AuthoredFarmSummary {
  need(object(value));
  closed(value,['scenario_id','scenario_revision','scenario_sha256','farm_sha256',
    'numeric_input_sha256','rights_sha256','registration_status','intent_job']);
  need(identifier(value.scenario_id) && identifier(value.scenario_revision)
    && (!expected || value.scenario_id===expected.scenario_id
      && value.scenario_revision===expected.scenario_revision)
    && digest(value.scenario_sha256) && digest(value.farm_sha256)
    && digest(value.numeric_input_sha256) && digest(value.rights_sha256)
    && value.registration_status==='registered_unpublished_inputs');
  const job=decodeJob(value.intent_job);
  need(job.stage==='collection');
  return {...value,intent_job:job} as AuthoredFarmSummary;
}

export function createAuthoredFarmApi(request:Request,decodeJob:(value:unknown)=>JobStatus) {
  return {
    async registerAuthoredFarm(value:AuthoredFarmRequest):Promise<AuthoredFarmSummary> {
      need(value.schema_version==='farm-authoring-request-v1' && object(value.farm)
        && object(value.rights));
      identity(value.farm);identity(value.rights);
      need(value.farm.scenario_id===value.rights.scenario_id
        && value.farm.scenario_revision===value.rights.scenario_revision);
      return summary(await request('/v1/farm-authored-inputs','POST',value,200),value.farm,decodeJob);
    },
    async authoredFarm(scenarioId:string,revision:string):Promise<AuthoredFarmSummary> {
      identity({scenario_id:scenarioId,scenario_revision:revision});
      return summary(await request('/v1/farm-authored-inputs?scenario_id='
        +encodeURIComponent(scenarioId)+'&scenario_revision='+encodeURIComponent(revision)),
        {scenario_id:scenarioId,scenario_revision:revision},decodeJob);
    },
    async authoredFarmCatalog(cursor?:AuthoredFarmCursor):Promise<AuthoredFarmPage> {
      if(cursor)need(date(cursor.created_at) && uuid(cursor.job_id));
      const query=cursor ? '?'+new URLSearchParams({
        before_created_at:cursor.created_at,before_job_id:cursor.job_id}) : '';
      const raw=await request('/v1/farm-authored-inputs/catalog'+query,'GET',undefined,200,65_536);
      need(object(raw));closed(raw,['items','next_cursor']);
      need(Array.isArray(raw.items) && raw.items.length<=20);
      const items=raw.items.map(value=>summary(value,null,decodeJob));
      need(new Set(items.map(item=>item.intent_job.job_id)).size===items.length);
      let next_cursor:AuthoredFarmCursor|null=null;
      if(raw.next_cursor!==null) {
        need(object(raw.next_cursor));closed(raw.next_cursor,['created_at','job_id']);
        need(date(raw.next_cursor.created_at) && uuid(raw.next_cursor.job_id)
          && items.length===20 && items[19]?.intent_job.created_at===raw.next_cursor.created_at
          && items[19]?.intent_job.job_id===raw.next_cursor.job_id);
        next_cursor={created_at:raw.next_cursor.created_at,job_id:raw.next_cursor.job_id};
      }
      return {items,next_cursor};
    },
    async authoredFarmActivity(scenarioId:string,revision:string,registrationSha256:string,
      cursor?:AuthoredFarmCursor):Promise<AuthoredFarmActivityPage> {
      identity({scenario_id:scenarioId,scenario_revision:revision});
      need(digest(registrationSha256));
      if(cursor)need(date(cursor.created_at) && uuid(cursor.job_id));
      const query=new URLSearchParams({scenario_id:scenarioId,scenario_revision:revision,
        registration_sha256:registrationSha256,
        ...(cursor ? {before_created_at:cursor.created_at,before_job_id:cursor.job_id} : {})});
      const raw=await request('/v1/farm-authored-inputs/activity?'+query,'GET',undefined,200,65_536);
      need(object(raw));closed(raw,['scenario_id','scenario_revision','registration_sha256',
        'items','next_cursor']);
      need(raw.scenario_id===scenarioId && raw.scenario_revision===revision
        && raw.registration_sha256===registrationSha256
        && Array.isArray(raw.items) && raw.items.length<=20);
      const items:AuthoredFarmActivity[]=raw.items.map(value=>{
        need(object(value));closed(value,['kind','job','review_job']);
        const job=decodeJob(value.job);
        if(value.kind==='review') {
          need(job.stage==='collection_review' && value.review_job===null);
          return {kind:'review',job,review_job:null};
        }
        need(value.kind==='simulation' && job.stage==='simulation');
        const review=decodeJob(value.review_job);
        need(review.stage==='collection_review' && review.job_id!==job.job_id);
        return {kind:'simulation',job,review_job:review};
      });
      need(new Set(items.map(item=>item.job.job_id)).size===items.length);
      let next_cursor:AuthoredFarmCursor|null=null;
      if(raw.next_cursor!==null) {
        need(object(raw.next_cursor));closed(raw.next_cursor,['created_at','job_id']);
        need(date(raw.next_cursor.created_at) && uuid(raw.next_cursor.job_id)
          && items.length===20 && items[19]?.job.created_at===raw.next_cursor.created_at
          && items[19]?.job.job_id===raw.next_cursor.job_id);
        next_cursor={created_at:raw.next_cursor.created_at,job_id:raw.next_cursor.job_id};
      }
      return {scenario_id:scenarioId,scenario_revision:revision,
        registration_sha256:registrationSha256,items,next_cursor};
    },
    async authoredRunCatalog(cursor?:AuthoredRunCursor):Promise<AuthoredRunCatalog> {
      if(cursor)need(date(cursor.recorded_at) && RUN.test(cursor.run_id));
      const query=cursor?'?'+new URLSearchParams({before_recorded_at:cursor.recorded_at,
        before_run_id:cursor.run_id}):'';
      const raw=await request('/v1/authored-runs/catalog'+query,'GET',undefined,200,65_536);
      need(object(raw));closed(raw,['items','next_cursor']);
      need(Array.isArray(raw.items) && raw.items.length<=20);
      const items:AuthoredRunRef[]=raw.items.map(value=>{
        need(object(value));closed(value,['run_id','simulation_job_id','recorded_at','verification']);
        need(typeof value.run_id==='string' && RUN.test(value.run_id)
          && uuid(value.simulation_job_id) && date(value.recorded_at)
          && value.verification==='requires_current_read');
        return value as AuthoredRunRef;
      });
      need(new Set(items.map(item=>item.run_id)).size===items.length);
      let next_cursor:AuthoredRunCursor|null=null;
      if(raw.next_cursor!==null) {
        need(object(raw.next_cursor));closed(raw.next_cursor,['recorded_at','run_id']);
        need(date(raw.next_cursor.recorded_at) && typeof raw.next_cursor.run_id==='string'
          && RUN.test(raw.next_cursor.run_id) && items.length===20
          && items[19]?.run_id===raw.next_cursor.run_id
          && items[19]?.recorded_at===raw.next_cursor.recorded_at);
        next_cursor={recorded_at:raw.next_cursor.recorded_at,run_id:raw.next_cursor.run_id};
      }
      return {items,next_cursor};
    },
    async submitAuthoredReview(value:AuthoredReviewIntent):Promise<JobStatus> {
      identity(value);
      need(digest(value.registration_sha256) && identifier(value.idempotency_key));
      const job=decodeJob(await request('/v1/farm-authored-reviews','POST',{
        schema_version:'farm-authored-review-request-v1',scenario_id:value.scenario_id,
        scenario_revision:value.scenario_revision,registration_sha256:value.registration_sha256,
        idempotency_key:value.idempotency_key},202,65_536,180_000));
      need(job.stage==='collection_review');
      return job;
    },
    async submitAuthoredRun(value:AuthoredRunIntent):Promise<JobStatus> {
      identity(value);
      need(digest(value.registration_sha256) && uuid(value.review_job_id)
        && identifier(value.idempotency_key));
      const job=decodeJob(await request('/v1/authored-runs','POST',{
        schema_version:'authored-thermal-simulation-request-v1',
        review_job_id:value.review_job_id,scenario_id:value.scenario_id,
        scenario_revision:value.scenario_revision,registration_sha256:value.registration_sha256,
        idempotency_key:value.idempotency_key},202,65_536,180_000));
      need(job.stage==='simulation');
      return job;
    },
  };
}
