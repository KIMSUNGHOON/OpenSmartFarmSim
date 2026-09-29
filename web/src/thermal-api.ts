import { need,object,closed,date,uuid } from './api-validation';

export type ThermalPoint={at_utc:string;temperature_k:number;humidity_ratio_kg_v_per_kg_da:number;
  relative_humidity_fraction:number;heat_demand_w_th:number;heat_delivered_w_th:number;delivered_heat_energy_kwh_th:number};
export type ThermalSummary={run_id:string;status:'accepted';synthetic:true;temporal_provenance:'ex_post_replay';
  decision_at_utc:string;review_at_utc:string;start_utc:string;end_utc:string;model_version:'thermal-v1';
  parameter_set_version:'synthetic-thermal-parameters-v1';engine_version:'thermal-euler-v1';
  unit_registry_version:'thermal-si-nws-v1';manifest_sha256:string;trace_sha256:string[];point_count:number};
export type ThermalSource={fixture_id:string;product_id:string;source_locator:string;raw_sha256:string;
  vintage_id:string;revision_id:string;available_at_utc:string;retrieved_at_utc:string;
  observed_start_utc:string|null;observed_end_utc:string|null;qc_status:'self_checked_synthetic';
  review_status:'self_reviewed_synthetic';display_right:'allowed';synthetic:true};
export type ThermalLaw={product_id:string;source_url:string;raw_pdf_sha256:string;published_at_utc:null;
  available_at_utc:null;retrieved_at_utc:string;publication_time_status:string;version_status:string;
  rights_status:string;display_right:'allowed_with_conditions';display_conditions:string};
export type ThermalManifest={run_id:string;synthetic:true;temporal_provenance:'ex_post_replay';snapshot_id:string;
  manifest_sha256:string;code_sha256:string;environment_sha256:string;release_sha256:string;trace_sha256:string[];
  source_unresolved_at_creation:string[];used_sources:ThermalSource[];excluded_fixture_ids:string[];law_reference:ThermalLaw};
export type ThermalReplay={summary:ThermalSummary;series:{run_id:string;temporal_provenance:'ex_post_replay';points:ThermalPoint[]};manifest:ThermalManifest};

const RUN=/^synthetic-thermal-v1:[0-9a-f]{64}$/;
function text(value:unknown):value is string {return typeof value==='string' && value.length>0 && value.length<=4096;}
function digest(value:unknown):value is string {return typeof value==='string' && /^[0-9a-f]{64}$/.test(value);}
function utc(value:unknown):value is string {return date(value) && value.endsWith('Z');}
function number(value:unknown):value is number {return typeof value==='number' && Number.isFinite(value) && value>=0;}
function traces(value:unknown):value is string[] {return Array.isArray(value) && value.length===2 && value.every(digest);}
function strings(value:unknown):value is string[] {return Array.isArray(value) && value.length<=50 && value.every(text);}
function summary(value:unknown):ThermalSummary {
  need(object(value));closed(value,['run_id','status','synthetic','temporal_provenance','decision_at_utc','review_at_utc',
    'start_utc','end_utc','model_version','parameter_set_version','engine_version','unit_registry_version',
    'manifest_sha256','trace_sha256','point_count']);
  need(text(value.run_id) && RUN.test(value.run_id) && value.status==='accepted' && value.synthetic===true
    && value.temporal_provenance==='ex_post_replay' && utc(value.decision_at_utc) && utc(value.review_at_utc)
    && utc(value.start_utc) && utc(value.end_utc) && Date.parse(value.end_utc)-Date.parse(value.start_utc)===7_200_000
    && value.model_version==='thermal-v1' && value.parameter_set_version==='synthetic-thermal-parameters-v1'
    && value.engine_version==='thermal-euler-v1' && value.unit_registry_version==='thermal-si-nws-v1'
    && digest(value.manifest_sha256) && traces(value.trace_sha256) && value.point_count===120);
  return {run_id:value.run_id,status:value.status,synthetic:true,temporal_provenance:value.temporal_provenance,
    decision_at_utc:value.decision_at_utc,review_at_utc:value.review_at_utc,start_utc:value.start_utc,end_utc:value.end_utc,
    model_version:value.model_version,parameter_set_version:value.parameter_set_version,engine_version:value.engine_version,
    unit_registry_version:value.unit_registry_version,manifest_sha256:value.manifest_sha256,
    trace_sha256:value.trace_sha256,point_count:value.point_count};
}
function point(value:unknown):ThermalPoint {
  need(object(value));closed(value,['at_utc','temperature_k','humidity_ratio_kg_v_per_kg_da','relative_humidity_fraction',
    'heat_demand_w_th','heat_delivered_w_th','delivered_heat_energy_kwh_th']);
  need(utc(value.at_utc) && number(value.temperature_k) && number(value.humidity_ratio_kg_v_per_kg_da)
    && number(value.relative_humidity_fraction) && value.relative_humidity_fraction<=1 && number(value.heat_demand_w_th)
    && number(value.heat_delivered_w_th) && number(value.delivered_heat_energy_kwh_th));
  return {at_utc:value.at_utc,temperature_k:value.temperature_k,humidity_ratio_kg_v_per_kg_da:value.humidity_ratio_kg_v_per_kg_da,
    relative_humidity_fraction:value.relative_humidity_fraction,heat_demand_w_th:value.heat_demand_w_th,
    heat_delivered_w_th:value.heat_delivered_w_th,delivered_heat_energy_kwh_th:value.delivered_heat_energy_kwh_th};
}
function source(value:unknown):ThermalSource {
  need(object(value));closed(value,['fixture_id','product_id','source_locator','raw_sha256','vintage_id','revision_id',
    'available_at_utc','retrieved_at_utc','observed_start_utc','observed_end_utc','qc_status','review_status','display_right','synthetic']);
  need(text(value.fixture_id) && text(value.product_id) && text(value.source_locator) && digest(value.raw_sha256)
    && text(value.vintage_id) && text(value.revision_id) && utc(value.available_at_utc) && utc(value.retrieved_at_utc)
    && (value.observed_start_utc===null || utc(value.observed_start_utc))
    && (value.observed_end_utc===null || utc(value.observed_end_utc)) && value.qc_status==='self_checked_synthetic'
    && value.review_status==='self_reviewed_synthetic' && value.display_right==='allowed' && value.synthetic===true);
  return {fixture_id:value.fixture_id,product_id:value.product_id,source_locator:value.source_locator,
    raw_sha256:value.raw_sha256,vintage_id:value.vintage_id,revision_id:value.revision_id,available_at_utc:value.available_at_utc,
    retrieved_at_utc:value.retrieved_at_utc,observed_start_utc:value.observed_start_utc,observed_end_utc:value.observed_end_utc,
    qc_status:value.qc_status,review_status:value.review_status,display_right:value.display_right,synthetic:true};
}
function law(value:unknown):ThermalLaw {
  need(object(value));closed(value,['product_id','source_url','raw_pdf_sha256','published_at_utc','available_at_utc',
    'retrieved_at_utc','publication_time_status','version_status','rights_status','display_right','display_conditions']);
  need(text(value.product_id) && text(value.source_url) && value.source_url.startsWith('https://')
    && digest(value.raw_pdf_sha256) && value.published_at_utc===null && value.available_at_utc===null && utc(value.retrieved_at_utc)
    && text(value.publication_time_status) && text(value.version_status) && text(value.rights_status)
    && value.display_right==='allowed_with_conditions' && text(value.display_conditions));
  return {product_id:value.product_id,source_url:value.source_url,raw_pdf_sha256:value.raw_pdf_sha256,
    published_at_utc:null,available_at_utc:null,retrieved_at_utc:value.retrieved_at_utc,publication_time_status:value.publication_time_status,
    version_status:value.version_status,rights_status:value.rights_status,display_right:value.display_right,display_conditions:value.display_conditions};
}
function manifest(value:unknown,pinned:ThermalSummary):ThermalManifest {
  need(object(value));closed(value,['run_id','synthetic','temporal_provenance','snapshot_id','manifest_sha256','code_sha256',
    'environment_sha256','release_sha256','trace_sha256','source_unresolved_at_creation','used_sources','excluded_fixture_ids','law_reference']);
  need(value.run_id===pinned.run_id && value.synthetic===true && value.temporal_provenance==='ex_post_replay'
    && text(value.snapshot_id) && /^thermal-snapshot-v1:[0-9a-f]{64}$/.test(value.snapshot_id)
    && value.manifest_sha256===pinned.manifest_sha256 && digest(value.code_sha256) && digest(value.environment_sha256)
    && digest(value.release_sha256) && traces(value.trace_sha256)
    && value.trace_sha256.every((hash,index)=>hash===pinned.trace_sha256[index]) && strings(value.source_unresolved_at_creation)
    && strings(value.excluded_fixture_ids) && Array.isArray(value.used_sources) && value.used_sources.length===2);
  const used_sources=value.used_sources.map(source);
  need(new Set(used_sources.map(item=>item.fixture_id)).size===2 && used_sources.every(item=>
    ['synthetic-weather-v1','synthetic-thermal-parameters-v1'].includes(item.fixture_id)));
  return {run_id:pinned.run_id,synthetic:true,temporal_provenance:value.temporal_provenance,snapshot_id:value.snapshot_id,
    manifest_sha256:pinned.manifest_sha256,code_sha256:value.code_sha256,environment_sha256:value.environment_sha256,
    release_sha256:value.release_sha256,trace_sha256:value.trace_sha256,source_unresolved_at_creation:value.source_unresolved_at_creation,
    used_sources,excluded_fixture_ids:value.excluded_fixture_ids,law_reference:law(value.law_reference)};
}

export function createThermalApi(request:(path:string)=>Promise<unknown>) {
  return {async thermalReplay(jobId:string):Promise<ThermalReplay> {
    need(uuid(jobId));const discovered=summary(await request('/v1/jobs/'+jobId+'/run'));
    const base='/v1/runs/'+encodeURIComponent(discovered.run_id);
    const [rawSummary,rawSeries,rawManifest]=await Promise.all([request(base),request(base+'/series'),request(base+'/manifest')]);
    const pinned=summary(rawSummary);need(JSON.stringify(pinned)===JSON.stringify(discovered));
    need(object(rawSeries));closed(rawSeries,['run_id','temporal_provenance','points']);
    need(rawSeries.run_id===pinned.run_id && rawSeries.temporal_provenance==='ex_post_replay'
      && Array.isArray(rawSeries.points) && rawSeries.points.length===pinned.point_count);
    const points=rawSeries.points.map(point);
    need(points.every((row,index)=>Date.parse(row.at_utc)===Date.parse(pinned.start_utc)+(index+1)*60_000));
    return {summary:pinned,series:{run_id:pinned.run_id,temporal_provenance:'ex_post_replay',points},manifest:manifest(rawManifest,pinned)};
  }};
}
