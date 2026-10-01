import { describe,expect,it,vi } from 'vitest';
import { createApi } from './api';
import { farmReferenceFields,type SourceFarmSelection,type FarmEconomicCandidate } from './source-farm-api';

const research='11111111-1111-4111-8111-111111111111';
const collection='22222222-2222-4222-8222-222222222222';
const digest='a'.repeat(64);
const path='/v1/source-history/'+research+'/collections/'+collection;
const token='synthetic-source-farm-client-token';
function fixtureSource():SourceFarmSelection {
  return {selection_version:'owned-source-farm-selection-v1',claim_scope:'software_fixture_only',
    assessment_status:'hold',g0_status:'not_accepted',g1_status:'not_accepted',requires_registration_recheck:true,
    research_job_id:research,research_attempt:1,research_decision_id:'33333333-3333-4333-8333-333333333333',
    research_input_sha256:digest,research_artifact_sha256:digest,collection_job_id:collection,
    collection_attempt:1,collection_input_sha256:digest,collection_record_sha256:digest,
    point:{latitude:35,longitude:127},period_start_utc:'2026-10-15T00:00:00.123456Z',
    period_end_utc:'2026-10-15T02:00:00.123456Z',goal_id:'historical-thermal-replay',
    provider_id:'project-fixture:manifest-v2',registry_sha256:digest,bundle_sha256:digest,
    snapshot_id:'thermal-snapshot-v1:'+digest,manifest_sha256:digest,weather_sha256:digest,
    thermal_sha256:digest,decision_context_id:'context-1',context_sha256:digest,
    decision_at_utc:'2026-09-28T00:00:00.123456Z',claim_mode:'ex_post_replay',decision_time_kind:'hypothetical'};
}
function fixtureCandidate():FarmEconomicCandidate {
  return {economic:{scenario_id:'economic-1',revision:'r1',sha256:digest,candidate_id:digest},
    market_context:{kind:'unavailable',hold_report_id:'market-hold-v1:'+digest},
    period_start:'2026-10-01',period_end:'2026-10-31',recorded_at:'2026-10-01T00:00:00.123456Z'};
}
function client(value:unknown,status=200) {
  const fetcher=vi.fn<typeof fetch>().mockResolvedValue(Response.json(value,{status}));
  return {api:createApi(token,fetcher),fetcher};
}
function page() {return {source:fixtureSource(),verification:'requires_current_selection',
  items:[fixtureCandidate()],next_cursor:null};}

describe('source and farm selection transport',()=>{
  it('reads the exact completed pair and carries only server reference fields into a draft',async()=>{
    const source=fixtureSource(),pin=fixtureCandidate();
    const selected={...pin,source,verification:'requires_registration_recheck' as const};
    const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(Response.json(source))
      .mockResolvedValueOnce(Response.json(page())).mockResolvedValueOnce(Response.json(selected));
    const api=createApi(token,fetcher);
    expect(await api.sourceFarmReferences(research,collection)).toEqual(source);
    const catalog=await api.sourceEconomicCandidates(source);
    expect(catalog.verification).toBe('requires_current_selection');
    const result=await api.sourceEconomicCandidate(source,catalog.items[0]!);
    expect(result).toEqual(selected);
    expect(farmReferenceFields(result)).toEqual({research_job_id:research,snapshot_id:source.snapshot_id,
      decision_context_id:'context-1',decision_at:source.decision_at_utc,
      market_hold_report_id:pin.market_context.hold_report_id,period_start:pin.period_start,
      period_end:pin.period_end,economic_scenario_id:'economic-1',economic_revision:'r1',
      economic_sha256:digest,economic_candidate_id:digest});
    expect(fetcher.mock.calls.map(([url])=>url)).toEqual([path+'/farm-input-references',
      path+'/economic-candidates?limit=20',path+'/economic-candidates/'+digest]);
    for(const [,init] of fetcher.mock.calls)expect(init).toMatchObject({method:'GET',
      credentials:'omit',redirect:'error',cache:'no-store',headers:{authorization:'Bearer '+token}});
    expect(result.source.assessment_status).toBe('hold');expect(result.source.g1_status).toBe('not_accepted');
  });
  it.each(['foreign','private','approved','point','hash','time','attempt','mode'])('rejects %s source response',async kind=>{
    const source=fixtureSource();
    if(kind==='foreign')source.collection_job_id=research;
    if(kind==='private')Object.assign(source,{raw_utf8:'restricted fixture raw'});
    if(kind==='approved')Object.assign(source,{g1_status:'accepted'});
    if(kind==='point')source.point.latitude=91;
    if(kind==='hash')source.context_sha256='not-a-digest';
    if(kind==='time')source.period_end_utc=source.period_start_utc;
    if(kind==='attempt')source.research_attempt=0;
    if(kind==='mode')Object.assign(source,{claim_mode:'forecast'});
    await expect(client(source).api.sourceFarmReferences(research,collection))
      .rejects.toMatchObject({code:'response_rejected'});
  });
  it('rejects unsafe parent IDs and unsupported ex ante authoring before a request',async()=>{
    const {api,fetcher}=client(page());
    await expect(api.sourceFarmReferences('../tenant',collection)).rejects.toMatchObject({code:'response_rejected'});
    await expect(api.sourceFarmReferences(research,research)).rejects.toMatchObject({code:'response_rejected'});
    const source=fixtureSource();source.claim_mode='ex_ante';
    expect((await client(source).api.sourceFarmReferences(research,collection)).claim_mode).toBe('ex_ante');
    await expect(api.sourceEconomicCandidates(source)).rejects.toMatchObject({code:'response_rejected'});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('preserves a microsecond tie cursor and accepts only older rows on recovery',async()=>{
    const source=fixtureSource();
    const items=Array.from({length:20},(_,i)=>({...fixtureCandidate(),economic:{...fixtureCandidate().economic,
      candidate_id:(40-i).toString(16).padStart(64,'0')}}));
    const last=items[19]!,cursor={recorded_at:last.recorded_at,candidate_id:last.economic.candidate_id};
    const older={...fixtureCandidate(),recorded_at:'2026-10-01T00:00:00.123455Z'};
    const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(Response.json({source,
      verification:'requires_current_selection',items,next_cursor:cursor})).mockResolvedValueOnce(Response.json({
        ...page(),items:[older]}));
    const api=createApi(token,fetcher);
    expect((await api.sourceEconomicCandidates(source)).next_cursor).toEqual(cursor);
    expect((await api.sourceEconomicCandidates(source,cursor)).items).toEqual([older]);
    expect(String(fetcher.mock.calls[1]![0])).toContain('before_recorded_at=2026-10-01T00%3A00%3A00.123456Z');
    expect(Date.parse(older.recorded_at)).toBe(Date.parse(cursor.recorded_at));
  });
  it.each(['source','microseconds','approval','duplicate','order','cursor','extra','calendar'])('rejects %s catalog mismatch',async kind=>{
    const value=page(),expected=fixtureSource();
    if(kind==='source')value.source.context_sha256='b'.repeat(64);
    if(kind==='microseconds')value.source.decision_at_utc='2026-09-28T00:00:00.123457Z';
    if(kind==='approval')value.verification='approved';
    if(kind==='duplicate')value.items.push(value.items[0]!);
    if(kind==='order')value.items.push({...fixtureCandidate(),recorded_at:'2026-10-01T00:00:00.123457Z'});
    if(kind==='cursor')Object.assign(value,{next_cursor:{recorded_at:value.items[0]!.recorded_at,candidate_id:digest}});
    if(kind==='extra')Object.assign(value,{recommended_crop:'invented'});
    if(kind==='calendar')value.items[0]!.period_start='2026-02-30';
    await expect(client(value).api.sourceEconomicCandidates(expected)).rejects.toMatchObject({code:'response_rejected'});
  });
  it.each(['candidate','revision','hash','hold','calendar','source','private','marker'])('rejects %s exact selection mismatch',async kind=>{
    const source=fixtureSource(),expected=fixtureCandidate();
    const value={...fixtureCandidate(),source,verification:'requires_registration_recheck'};
    if(kind==='candidate')value.economic.candidate_id='b'.repeat(64);
    if(kind==='revision')value.economic.revision='r2';
    if(kind==='hash')value.economic.sha256='b'.repeat(64);
    if(kind==='hold')value.market_context.hold_report_id='market-hold-v1:'+'b'.repeat(64);
    if(kind==='calendar')value.period_end='2026-11-01';
    if(kind==='source')value.source.weather_sha256='b'.repeat(64);
    if(kind==='private')Object.assign(value,{rights_manifest:'restricted fixture'});
    if(kind==='marker')value.verification='accepted';
    await expect(client(value).api.sourceEconomicCandidate(fixtureSource(),expected))
      .rejects.toMatchObject({code:'response_rejected'});
  });
  it('keeps an empty catalog empty and rejects malformed cursors before network access',async()=>{
    const value=page();value.items=[];
    expect((await client(value).api.sourceEconomicCandidates(fixtureSource())).items).toEqual([]);
    const {api,fetcher}=client(value);
    for(const cursor of [{recorded_at:'2026-10-01T00:00:00+09:00',candidate_id:digest},
      {recorded_at:'2026-10-01T00:00:00Z',candidate_id:'A'.repeat(64)},
      {recorded_at:'2026-10-01T00:00:00.1234567Z',candidate_id:digest}]) {
      await expect(api.sourceEconomicCandidates(fixtureSource(),cursor)).rejects.toMatchObject({code:'response_rejected'});
    }
    expect(fetcher).not.toHaveBeenCalled();
  });
  it.each([[403,'access_denied'],[422,'invalid_request'],[503,'server_unavailable']] as const)(
    'preserves %s current selection failure without producing a pin',async(status,code)=>{
      await expect(client({error:{code:'private',message:'private fixture detail'}},status).api
        .sourceEconomicCandidate(fixtureSource(),fixtureCandidate())).rejects.toMatchObject({code});
    });
});
