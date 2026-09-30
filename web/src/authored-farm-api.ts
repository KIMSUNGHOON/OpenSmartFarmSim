import { closed,need,object,uuid } from './api-validation';
import type { JobStatus } from './api';

const IDENTIFIER=/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/;
const DIGEST=/^[0-9a-f]{64}$/;
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number)=>Promise<unknown>;
type Identity={scenario_id:string;scenario_revision:string};
export type AuthoredFarmRequest={schema_version:'farm-authoring-request-v1';
  farm:Identity & Record<string,unknown>;rights:Identity & Record<string,unknown>};
export type AuthoredFarmSummary=Identity & {scenario_sha256:string;farm_sha256:string;
  numeric_input_sha256:string;rights_sha256:string;
  registration_status:'registered_unpublished_inputs';intent_job:JobStatus};
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
function summary(value:unknown,expected:Identity,decodeJob:(value:unknown)=>JobStatus):AuthoredFarmSummary {
  need(object(value));
  closed(value,['scenario_id','scenario_revision','scenario_sha256','farm_sha256',
    'numeric_input_sha256','rights_sha256','registration_status','intent_job']);
  need(value.scenario_id===expected.scenario_id && value.scenario_revision===expected.scenario_revision
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
    async submitAuthoredReview(value:AuthoredReviewIntent):Promise<JobStatus> {
      identity(value);
      need(digest(value.registration_sha256) && identifier(value.idempotency_key));
      const job=decodeJob(await request('/v1/farm-authored-reviews','POST',{
        schema_version:'farm-authored-review-request-v1',scenario_id:value.scenario_id,
        scenario_revision:value.scenario_revision,registration_sha256:value.registration_sha256,
        idempotency_key:value.idempotency_key}));
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
        idempotency_key:value.idempotency_key}));
      need(job.stage==='simulation');
      return job;
    },
  };
}
