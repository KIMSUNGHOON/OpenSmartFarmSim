// HTTP doubles for authored replay software checks; no product CLI or G1 proof.
import { thermalResponses } from './thermal-fixture';

export const authoredJobId='44444444-4444-4444-8444-444444444444';
export const authoredRunId='authored-thermal-run-v1:'+'e'.repeat(64);

export function authoredResponses() {
  const original=thermalResponses();
  const summary={run_id:authoredRunId,status:'accepted',synthetic:true,
    claim_scope:'synthetic_thermal_replay_only',temporal_provenance:'ex_post_replay',
    scenario_id:'farm-1',scenario_revision:'r1',registration_sha256:'a'.repeat(64),
    release_sha256:'b'.repeat(64),decision_at_utc:original.summary.decision_at_utc,
    review_at_utc:original.summary.review_at_utc,start_utc:original.summary.start_utc,
    end_utc:original.summary.end_utc,model_version:'thermal-v1',engine_version:'thermal-euler-v1',
    unit_registry_version:'thermal-si-nws-v1',trace_sha256:['c'.repeat(64),'d'.repeat(64)],
    point_count:120};
  return {summary,series:{run_id:authoredRunId,temporal_provenance:'ex_post_replay',
    points:original.series.points}};
}
