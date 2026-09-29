// HTTP response doubles for software tests; no accepted farm or model evidence.
export const thermalJobId='22222222-2222-4222-8222-222222222222';
export const thermalRunId='synthetic-thermal-v1:'+'a'.repeat(64);
export function thermalResponses() {
  const summary={run_id:thermalRunId,status:'accepted',synthetic:true,temporal_provenance:'ex_post_replay',
    decision_at_utc:'2026-10-15T08:00:00Z',review_at_utc:'2026-10-16T11:00:00Z',
    start_utc:'2026-10-15T08:00:00Z',end_utc:'2026-10-15T10:00:00Z',model_version:'thermal-v1',
    parameter_set_version:'synthetic-thermal-parameters-v1',engine_version:'thermal-euler-v1',
    unit_registry_version:'thermal-si-nws-v1',manifest_sha256:'b'.repeat(64),
    trace_sha256:['c'.repeat(64),'d'.repeat(64)],point_count:120};
  const points=Array.from({length:120},(_,i)=>({
    at_utc:new Date(Date.parse(summary.start_utc)+(i+1)*60_000).toISOString().replace('.000Z','Z'),
    temperature_k:293.15+i/10,humidity_ratio_kg_v_per_kg_da:0.007+i/100_000,
    relative_humidity_fraction:0.5+i/500,heat_demand_w_th:300+i,
    heat_delivered_w_th:240+i,delivered_heat_energy_kwh_th:(240+i)/60_000}));
  const source=(id:string)=>({fixture_id:id,product_id:id,source_locator:'fixture://'+id,
    raw_sha256:'e'.repeat(64),vintage_id:'software-double-v1',revision_id:'1',
    available_at_utc:'2026-10-15T10:00:00Z',retrieved_at_utc:'2026-10-16T10:00:00Z',
    observed_start_utc:null,observed_end_utc:null,qc_status:'self_checked_synthetic',
    review_status:'self_reviewed_synthetic',display_right:'allowed',synthetic:true});
  const manifest={run_id:thermalRunId,synthetic:true,temporal_provenance:'ex_post_replay',
    snapshot_id:'thermal-snapshot-v1:'+'f'.repeat(64),manifest_sha256:summary.manifest_sha256,
    code_sha256:'1'.repeat(64),environment_sha256:'2'.repeat(64),release_sha256:'3'.repeat(64),
    trace_sha256:summary.trace_sha256,source_unresolved_at_creation:['NO_LOCAL_MEASUREMENTS'],
    used_sources:[source('synthetic-weather-v1'),source('synthetic-thermal-parameters-v1')],
    excluded_fixture_ids:['synthetic-economics-v1'],law_reference:{product_id:'nws-vapor-pressure-law',
      source_url:'https://www.weather.gov/media/epz/wxcalc/vaporPressure.pdf',raw_pdf_sha256:'4'.repeat(64),
      published_at_utc:null,available_at_utc:null,retrieved_at_utc:'2026-09-27T00:00:00Z',
      publication_time_status:'unknown',version_status:'unknown',rights_status:'software_response_double',
      display_right:'allowed_with_conditions',display_conditions:'Software test double; not reviewed source evidence.'}};
  return {summary,series:{run_id:thermalRunId,temporal_provenance:'ex_post_replay',points},manifest};
}
