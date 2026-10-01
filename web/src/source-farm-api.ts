import { closed,date,member,need,object,uuid } from './api-validation';

export type SourceFarmSelection={selection_version:'owned-source-farm-selection-v1';
  claim_scope:'software_fixture_only';assessment_status:'hold';g0_status:'not_accepted';
  g1_status:'not_accepted';requires_registration_recheck:true;
  research_job_id:string;research_attempt:number;research_decision_id:string;
  research_input_sha256:string;research_artifact_sha256:string;collection_job_id:string;
  collection_attempt:number;collection_input_sha256:string;collection_record_sha256:string;
  point:{latitude:number;longitude:number};period_start_utc:string;period_end_utc:string;
  goal_id:'historical-thermal-replay';provider_id:'project-fixture:manifest-v2';
  registry_sha256:string;bundle_sha256:string;snapshot_id:string;manifest_sha256:string;
  weather_sha256:string;thermal_sha256:string;decision_context_id:string;context_sha256:string;
  decision_at_utc:string;claim_mode:'ex_ante'|'ex_post_replay';decision_time_kind:'actual'|'hypothetical'};
export type FarmEconomicCandidate={economic:{scenario_id:string;revision:string;sha256:string;candidate_id:string};
  market_context:{kind:'unavailable';hold_report_id:string};period_start:string;period_end:string;recorded_at:string};
export type FarmEconomicCursor={recorded_at:string;candidate_id:string};
export type FarmEconomicPage={verification:'requires_current_selection';source:SourceFarmSelection;
  items:FarmEconomicCandidate[];next_cursor:FarmEconomicCursor|null};
export type FarmEconomicSelection=FarmEconomicCandidate & {verification:'requires_registration_recheck';
  source:SourceFarmSelection};
type Request=(path:string,method?:string,body?:unknown,expected?:number,maxBytes?:number)=>Promise<unknown>;

const SOURCE=['selection_version','claim_scope','assessment_status','g0_status','g1_status',
  'requires_registration_recheck','research_job_id','research_attempt','research_decision_id',
  'research_input_sha256','research_artifact_sha256','collection_job_id','collection_attempt',
  'collection_input_sha256','collection_record_sha256','point','period_start_utc','period_end_utc',
  'goal_id','provider_id','registry_sha256','bundle_sha256','snapshot_id','manifest_sha256',
  'weather_sha256','thermal_sha256','decision_context_id','context_sha256','decision_at_utc',
  'claim_mode','decision_time_kind'] as const;
const HASHES=['research_input_sha256','research_artifact_sha256','collection_input_sha256',
  'collection_record_sha256','registry_sha256','bundle_sha256','manifest_sha256','weather_sha256',
  'thermal_sha256','context_sha256'] as const;
const CANDIDATE=['economic','market_context','period_start','period_end','recorded_at'] as const;
function digest(value:unknown):value is string {return typeof value==='string' && /^[0-9a-f]{64}$/.test(value);}
function identifier(value:unknown):value is string {
  return typeof value==='string' && /^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/.test(value);
}
function utc(value:unknown):value is string {return date(value) && /(?:Z|\+00:00)$/.test(value);}
function day(value:unknown):value is string {
  return typeof value==='string' && /^\d{4}-\d\d-\d\d$/.test(value) && date(value+'T00:00:00Z');
}
function instant(value:string) {
  return value.slice(0,19)+'.'+(value.match(/\.(\d{1,6})/)?.[1]??'').padEnd(6,'0');
}
function base(researchId:string,collectionId:string) {
  need(uuid(researchId) && uuid(collectionId) && researchId!==collectionId);
  return '/v1/source-history/'+researchId+'/collections/'+collectionId;
}
function source(value:unknown,researchId:string,collectionId:string):SourceFarmSelection {
  need(object(value));closed(value,SOURCE);
  need(value.selection_version==='owned-source-farm-selection-v1' && value.claim_scope==='software_fixture_only'
    && value.assessment_status==='hold' && value.g0_status==='not_accepted' && value.g1_status==='not_accepted'
    && value.requires_registration_recheck===true && value.research_job_id===researchId
    && value.collection_job_id===collectionId && uuid(value.research_decision_id));
  need(typeof value.research_attempt==='number' && Number.isSafeInteger(value.research_attempt)
    && value.research_attempt>=1 && typeof value.collection_attempt==='number'
    && Number.isSafeInteger(value.collection_attempt) && value.collection_attempt>=1);
  need(HASHES.every(key=>digest(value[key])) && object(value.point));
  closed(value.point,['latitude','longitude']);
  need(typeof value.point.latitude==='number' && Number.isFinite(value.point.latitude)
    && Math.abs(value.point.latitude)<=90 && typeof value.point.longitude==='number'
    && Number.isFinite(value.point.longitude) && Math.abs(value.point.longitude)<=180);
  need(utc(value.period_start_utc) && value.period_start_utc.endsWith('Z')
    && utc(value.period_end_utc) && value.period_end_utc.endsWith('Z')
    && utc(value.decision_at_utc) && value.decision_at_utc.endsWith('Z')
    && instant(value.period_start_utc)<instant(value.period_end_utc)
    && value.goal_id==='historical-thermal-replay' && value.provider_id==='project-fixture:manifest-v2'
    && typeof value.snapshot_id==='string' && /^thermal-snapshot-v1:[0-9a-f]{64}$/.test(value.snapshot_id)
    && identifier(value.decision_context_id) && member(value.claim_mode,['ex_ante','ex_post_replay'] as const)
    && member(value.decision_time_kind,['actual','hypothetical'] as const));
  return value as SourceFarmSelection;
}
function sameSource(a:SourceFarmSelection,b:SourceFarmSelection) {
  need(SOURCE.every(key=>key==='point' ? a.point.latitude===b.point.latitude && a.point.longitude===b.point.longitude
    : a[key]===b[key]));
}
function candidate(value:unknown):FarmEconomicCandidate {
  need(object(value));closed(value,CANDIDATE);
  need(object(value.economic));closed(value.economic,['scenario_id','revision','sha256','candidate_id']);
  need(identifier(value.economic.scenario_id) && identifier(value.economic.revision)
    && digest(value.economic.sha256) && digest(value.economic.candidate_id));
  need(object(value.market_context));closed(value.market_context,['kind','hold_report_id']);
  need(value.market_context.kind==='unavailable' && identifier(value.market_context.hold_report_id)
    && day(value.period_start) && day(value.period_end) && value.period_start<=value.period_end
    && utc(value.recorded_at));
  return value as FarmEconomicCandidate;
}
function cursor(value:unknown):FarmEconomicCursor {
  need(object(value));closed(value,['recorded_at','candidate_id']);
  need(utc(value.recorded_at) && digest(value.candidate_id));return value as FarmEconomicCursor;
}
function before(a:FarmEconomicCursor,b:FarmEconomicCursor) {
  const aa=instant(a.recorded_at),bb=instant(b.recorded_at);
  return aa<bb || aa===bb && a.candidate_id<b.candidate_id;
}
function currentSource(selected:SourceFarmSelection) {
  base(selected.research_job_id,selected.collection_job_id);
  source(selected,selected.research_job_id,selected.collection_job_id);need(selected.claim_mode==='ex_post_replay');
}
export function farmReferenceFields(selected:FarmEconomicSelection):Record<string,string> {
  closed(selected,[...CANDIDATE,'verification','source']);
  currentSource(selected.source);
  need(selected.verification==='requires_registration_recheck');
  const pin=candidate(Object.fromEntries(CANDIDATE.map(key=>[key,selected[key]])));
  return {research_job_id:selected.source.research_job_id,snapshot_id:selected.source.snapshot_id,
    decision_context_id:selected.source.decision_context_id,decision_at:selected.source.decision_at_utc,
    market_hold_report_id:pin.market_context.hold_report_id,period_start:pin.period_start,period_end:pin.period_end,
    economic_scenario_id:pin.economic.scenario_id,economic_revision:pin.economic.revision,
    economic_sha256:pin.economic.sha256,economic_candidate_id:pin.economic.candidate_id};
}
export function createSourceFarmApi(request:Request) {
  return {
    async sourceFarmReferences(researchId:string,collectionId:string):Promise<SourceFarmSelection> {
      const raw=await request(base(researchId,collectionId)+'/farm-input-references');
      return source(raw,researchId,collectionId);
    },
    async sourceEconomicCandidates(selected:SourceFarmSelection,after?:FarmEconomicCursor):Promise<FarmEconomicPage> {
      currentSource(selected);if(after)cursor(after);
      const query=new URLSearchParams({limit:'20'});
      if(after){query.set('before_recorded_at',after.recorded_at);query.set('before_candidate_id',after.candidate_id);}
      const raw=await request(base(selected.research_job_id,selected.collection_job_id)+'/economic-candidates?'+query);
      need(object(raw));closed(raw,['verification','source','items','next_cursor']);
      need(raw.verification==='requires_current_selection' && Array.isArray(raw.items) && raw.items.length<=20);
      const linked=source(raw.source,selected.research_job_id,selected.collection_job_id);sameSource(linked,selected);
      const seen=new Set<string>();let previous=after;
      const items=raw.items.map(value=>{
        const item=candidate(value),next={recorded_at:item.recorded_at,candidate_id:item.economic.candidate_id};
        need(!seen.has(next.candidate_id));seen.add(next.candidate_id);
        if(previous)need(before(next,previous));previous=next;return item;
      });
      const next=raw.next_cursor===null?null:cursor(raw.next_cursor);
      if(next)need(items.length===20 && previous?.candidate_id===next.candidate_id
        && previous.recorded_at===next.recorded_at);
      return {verification:'requires_current_selection',source:linked,items,next_cursor:next};
    },
    async sourceEconomicCandidate(selected:SourceFarmSelection,expected:FarmEconomicCandidate):Promise<FarmEconomicSelection> {
      currentSource(selected);candidate(expected);
      const raw=await request(base(selected.research_job_id,selected.collection_job_id)
        +'/economic-candidates/'+expected.economic.candidate_id);
      need(object(raw));closed(raw,[...CANDIDATE,'verification','source']);
      need(raw.verification==='requires_registration_recheck');
      const linked=source(raw.source,selected.research_job_id,selected.collection_job_id);sameSource(linked,selected);
      const pin=candidate(Object.fromEntries(CANDIDATE.map(key=>[key,raw[key]])));
      need(Object.keys(pin.economic).every(key=>pin.economic[key as keyof typeof pin.economic]
        ===expected.economic[key as keyof typeof expected.economic])
        && pin.market_context.hold_report_id===expected.market_context.hold_report_id
        && pin.period_start===expected.period_start && pin.period_end===expected.period_end
        && pin.recorded_at===expected.recorded_at);
      return {...pin,verification:'requires_registration_recheck',source:linked};
    },
  };
}
