import { need,object,closed,date,uuid } from './api-validation';
import { point,type ThermalPoint } from './thermal-api';

export type AuthoredThermalSummary={run_id:string;status:'accepted';synthetic:true;
  claim_scope:'synthetic_thermal_replay_only';temporal_provenance:'ex_post_replay';
  scenario_id:string;scenario_revision:string;registration_sha256:string;release_sha256:string;
  decision_at_utc:string;review_at_utc:string;start_utc:string;end_utc:string;
  model_version:'thermal-v1';engine_version:'thermal-euler-v1';
  unit_registry_version:'thermal-si-nws-v1';trace_sha256:string[];point_count:120};
export type AuthoredThermalReplay={summary:AuthoredThermalSummary;
  series:{run_id:string;temporal_provenance:'ex_post_replay';points:ThermalPoint[]}};

const RUN=/^authored-thermal-run-v1:[0-9a-f]{64}$/;
const IDENTIFIER=/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/;
const DIGEST=/^[0-9a-f]{64}$/;
function utc(value:unknown):value is string {return date(value) && value.endsWith('Z');}
function digest(value:unknown):value is string {return typeof value==='string' && DIGEST.test(value);}
function summary(value:unknown):AuthoredThermalSummary {
  need(object(value));closed(value,['run_id','status','synthetic','claim_scope','temporal_provenance',
    'scenario_id','scenario_revision','registration_sha256','release_sha256','decision_at_utc',
    'review_at_utc','start_utc','end_utc','model_version','engine_version',
    'unit_registry_version','trace_sha256','point_count']);
  need(typeof value.run_id==='string' && RUN.test(value.run_id) && value.status==='accepted'
    && value.synthetic===true && value.claim_scope==='synthetic_thermal_replay_only'
    && value.temporal_provenance==='ex_post_replay'
    && typeof value.scenario_id==='string' && IDENTIFIER.test(value.scenario_id)
    && typeof value.scenario_revision==='string' && IDENTIFIER.test(value.scenario_revision)
    && digest(value.registration_sha256) && digest(value.release_sha256)
    && utc(value.decision_at_utc) && utc(value.review_at_utc)
    && utc(value.start_utc) && utc(value.end_utc)
    && Date.parse(value.end_utc)-Date.parse(value.start_utc)===7_200_000
    && value.model_version==='thermal-v1' && value.engine_version==='thermal-euler-v1'
    && value.unit_registry_version==='thermal-si-nws-v1'
    && Array.isArray(value.trace_sha256) && value.trace_sha256.length===2
    && value.trace_sha256.every(digest) && value.point_count===120);
  return value as AuthoredThermalSummary;
}

export function createAuthoredThermalApi(request:(path:string)=>Promise<unknown>) {
  async function authoredThermalSummary(jobId:string):Promise<AuthoredThermalSummary> {
    need(uuid(jobId));
    return summary(await request('/v1/jobs/'+jobId+'/authored-run'));
  }
  return {authoredThermalSummary,async authoredThermalReplay(jobId:string):Promise<AuthoredThermalReplay> {
    const discovered=await authoredThermalSummary(jobId);
    const base='/v1/authored-runs/'+encodeURIComponent(discovered.run_id);
    const [rawSummary,rawSeries]=await Promise.all([request(base),request(base+'/series')]);
    const pinned=summary(rawSummary);
    need(JSON.stringify(pinned)===JSON.stringify(discovered));
    need(object(rawSeries));closed(rawSeries,['run_id','temporal_provenance','points']);
    need(rawSeries.run_id===pinned.run_id && rawSeries.temporal_provenance==='ex_post_replay'
      && Array.isArray(rawSeries.points) && rawSeries.points.length===pinned.point_count);
    const points=rawSeries.points.map(point);
    need(points.every((row,index)=>Date.parse(row.at_utc)===Date.parse(pinned.start_utc)+(index+1)*60_000));
    return {summary:pinned,series:{run_id:pinned.run_id,temporal_provenance:'ex_post_replay',points}};
  }};
}
