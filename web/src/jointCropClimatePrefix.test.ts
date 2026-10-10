import { describe,it,expect,vi,afterEach } from 'vitest';
import { readFileSync } from 'node:fs';
import { createApi,ApiError } from './api';
import { createJointCropClimatePrefixApi,matchJointPrefixPage,
  type JointPrefixSummaryResponse } from './jointCropClimatePrefix';

// Owned recorded values supply codec fixtures; their new prefix envelopes are not server evidence.
const fixture=JSON.parse(readFileSync(new URL('../e2e/joint-crop-climate-recorded-responses.json',import.meta.url),'utf8'));
const stored=fixture.completed[0],rows=fixture.completed[1].page,events=fixture.completed[2].page;
const ID='11111111-1111-4111-8111-111111111111',TOKEN='owned-prefix-unit-token-'+'x'.repeat(32);
const AT='2026-10-10T11:38:00.123456Z',OBS='2026-10-10T11:38:00.123457Z';
const {scenario_id,scenario_revision,registration_sha256,crop_id}=stored.farm;
const LOOKUP={job_id:ID,farm:{scenario_id,scenario_revision,registration_sha256,crop_id}};
const PIN={publication_sequence:1,head_sha256:stored.reference.artifact.head_sha256,proof_sha256:stored.reference.artifact.proof_sha256};
type Raw=Record<string,any>;
function accepted(kind='summary',start=0,limit=kind==='events'?8:64):Raw{
  const a=stored.reference.artifact,source=kind==='events'?events:rows;
  return {schema_version:'joint-crop-climate-prefix-replay-v1',scope:'synthetic_joint_crop_climate_math_only',
    claim_scope:'synthetic_joint_crop_climate_confirmed_prefix_only',G0_G4:'not_assessed',
    job:{job_id:ID,stage:'simulation',state:'simulating',attempt_count:1,max_attempts:3,created_at:AT,updated_at:AT,reason_code:null},
    cancel_requested:false,observed_at:OBS,prefix_status:'accepted',reference:{selector:{...PIN},
      checkpoint:{...PIN,artifact_sha256:a.sha256,status:'completed',steps:a.steps,planned_steps:a.planned_steps,
        counts:{samples:a.sample_count,events:a.event_count},computed_through_utc:stored.reference.last_confirmed.at,checkpoint_recorded_at:AT},
      checkpoint_attempt:1,study_id:stored.study_id,revision:stored.revision,farm:structuredClone(stored.farm),
      input:structuredClone(stored.reference.input),manifest:structuredClone(stored.summary.manifest),time_grid:structuredClone(stored.reference.time_grid)},
    summary:kind==='summary'?{counts:{samples:a.sample_count,events:a.event_count},
      last_sample_utc:rows.records.at(-1).time.at,last_event_utc:events.records.at(-1).time.at}:null,
    page:kind==='summary'?null:{kind,start,limit,total:source.total,next_offset:start+limit<source.total?start+limit:null,
      records:structuredClone(source.records.slice(start,start+limit))}};
}
function absent(status='none'):Raw{
  const p=accepted();p.prefix_status=status;p.reference=p.summary=p.page=null;
  p.job.state=status==='none'?'queued':'canceled';p.job.attempt_count=0;return p;
}
function client(value:unknown,fetcher?:typeof fetch){
  const fetch=fetcher??vi.fn(async()=>new Response(JSON.stringify(value),{status:200,headers:{'Content-Type':'application/json'}}));
  return {api:createApi(TOKEN,fetch),fetch};
}
afterEach(()=>vi.useRealTimers());

describe('owned prefix codec and authenticated transport',()=>{
  it('keeps original samples/events/numeric values and UTC without a terminal reference',async()=>{
    const summary=await client(accepted()).api.jointCropClimatePrefix(LOOKUP);
    expect(summary).toEqual(accepted());expect(summary.reference).not.toHaveProperty('artifact');
    for(const kind of ['samples','events'] as const){
      const p=accepted(kind),value=await client(p).api.jointCropClimatePrefixPage(LOOKUP,PIN,{kind,start:0,limit:kind==='samples'?64:8});
      expect(value).toEqual(p);expect(value.page.records).toEqual(kind==='samples'?rows.records:events.records);
    }
  });
  it.each(['none','closed'])('returns %s with no invented values',async status=>{
    expect(await client(absent(status)).api.jointCropClimatePrefix(LOOKUP)).toEqual(absent(status));
  });
  it('keeps ready without a sample timestamp and accepts original offset job times',async()=>{
    const p=accepted();Object.assign(p.reference.checkpoint,{artifact_sha256:null,status:'ready',steps:0,computed_through_utc:null,counts:{samples:0,events:0}});
    p.summary={counts:{samples:0,events:0},last_sample_utc:null,last_event_utc:null};
    p.job.created_at=p.job.updated_at='2026-10-10T20:38:00.123456+09:00';
    expect(await client(p).api.jointCropClimatePrefix(LOOKUP)).toEqual(p);
  });
  it('passes fixed limits, auth and signal; only sends the original selector and start',async()=>{
    const request=vi.fn(async()=>accepted('samples'));const signal=new AbortController().signal;
    const api=createJointCropClimatePrefixApi(request,v=>v as any);
    await api.jointCropClimatePrefixPage(LOOKUP,PIN,{kind:'samples',start:0,limit:64},{signal});
    expect(request).toHaveBeenCalledWith('/v1/jobs/'+ID+'/crop-climate-joint-execution/prefix/samples?'+new URLSearchParams({...PIN,
      publication_sequence:'1',start:'0',limit:'64'}),'GET',undefined,200,2*1024*1024,30000,signal);
    const c=client(accepted());await c.api.jointCropClimatePrefix(LOOKUP);
    expect(c.fetch).toHaveBeenCalledWith('/v1/jobs/'+ID+'/crop-climate-joint-execution/prefix',expect.objectContaining({headers:expect.objectContaining({authorization:'Bearer '+TOKEN})}));
  });
  it.each(['extra','version','scope','claim','gate','wrong-job','wrong-stage','wrong-state','job-before','job-attempt','observed','observed-before','cancel',
    'accepted-closed','both-payloads','neither-payload','reference-extra','sequence','head','proof','selector-mismatch','attempt',
    'farm','farm-extra','batch','zone','input-extra','input-hash','input-start','grid-step','grid-duration','manifest-extra','manifest-count',
    'manifest-code','manifest-policy','computed','count-over','ready-count','recorded-before','recorded-after','summary-count','summary-time','summary-null',
    'sample-unit','sample-length','sample-nan','sample-utc','sample-step','sample-order','page-start','page-total','page-next','page-records','event-code','event-extra'])
    ('rejects malformed or mixed prefix %s',async fault=>{
      const event=fault.startsWith('event-'),page=fault.startsWith('sample-')||fault.startsWith('page-')||event;
      const p=accepted(page?(event?'events':'samples'):'summary'),r=p.reference,c=r.checkpoint;
      if(fault==='extra')p.private={};if(fault==='version')p.schema_version='old';if(fault==='scope')p.scope='production';
      if(fault==='claim')p.claim_scope='prediction';if(fault==='gate')p.G0_G4='passed';if(fault==='wrong-job')p.job.job_id='22222222-2222-4222-8222-222222222222';
      if(fault==='wrong-stage')p.job.stage='research';if(fault==='wrong-state')p.job.state='assessing';if(fault==='observed')p.observed_at=AT.replace('Z','+00:00');
      if(fault==='job-before')p.job.updated_at='2026-10-10T11:38:00.123455Z';if(fault==='job-attempt')p.job.attempt_count=0;
      if(fault==='observed-before')p.observed_at='2026-10-10T11:38:00.123455Z';if(fault==='cancel')p.cancel_requested=1;
      if(fault==='accepted-closed')p.cancel_requested=true;if(fault==='both-payloads')p.page=accepted('samples').page;if(fault==='neither-payload')p.summary=null;
      if(fault==='reference-extra')r.root={};if(fault==='sequence')r.selector.publication_sequence=4100;if(fault==='head')r.selector.head_sha256='A'.repeat(64);
      if(fault==='proof')r.selector.proof_sha256='x';if(fault==='selector-mismatch')c.publication_sequence=2;if(fault==='attempt')r.checkpoint_attempt=2;
      if(fault==='farm')r.farm.crop_id='foreign';if(fault==='farm-extra')r.farm.private=0;if(fault==='batch')r.farm.batch_id='';if(fault==='zone')r.farm.zone_id=null;
      if(fault==='input-extra')r.input.url='https://example.test';if(fault==='input-hash')r.input.context_sha256='bad';if(fault==='input-start')r.input.start_utc=AT;
      if(fault==='grid-step')r.time_grid.step_microseconds++;if(fault==='grid-duration')r.time_grid.end_utc=AT;
      if(fault==='manifest-extra')r.manifest.private=1;if(fault==='manifest-count')r.manifest.numerical.step_count++;
      if(fault==='manifest-code')r.manifest.identity.component_code_sha256.private='a'.repeat(64);if(fault==='manifest-policy')r.manifest.policy_sha256='f'.repeat(64);
      if(fault==='computed')c.computed_through_utc=r.time_grid.start_utc;if(fault==='count-over')c.counts.samples=513;
      if(fault==='ready-count'){c.status='ready';c.steps=0;c.artifact_sha256=null;c.computed_through_utc=null;}
      if(fault==='recorded-before')c.checkpoint_recorded_at='2026-10-10T11:38:00.123455Z';if(fault==='recorded-after')c.checkpoint_recorded_at='2026-10-10T11:38:00.123458Z';
      if(fault==='summary-count')p.summary.counts.samples++;if(fault==='summary-time')p.summary.last_sample_utc=AT;if(fault==='summary-null')p.summary.last_event_utc=null;
      if(fault==='sample-unit')p.page.records[0].value.plant_state.leaf.unit='kg';if(fault==='sample-length')p.page.records[0].value.cohort_state.fruit_number.pop();
      if(fault==='sample-nan')p.page.records[0].value.plant_state.leaf.value=NaN;if(fault==='sample-utc')p.page.records[0].time.at=AT;
      if(fault==='sample-step')p.page.records[0].value.step_index=1;if(fault==='sample-order')p.page.records.reverse();
      if(fault==='page-start')p.page.start=-1;if(fault==='page-total')p.page.total++;if(fault==='page-next')p.page.next_offset=0;if(fault==='page-records')p.page.records.pop();
      if(fault==='event-code')p.page.records[0].value.management.code_sha256='f'.repeat(64);if(fault==='event-extra')p.page.records[0].value.management.source={};
      const api=client(p).api;
      await expect(page?api.jointCropClimatePrefixPage(LOOKUP,PIN,{kind:event?'events':'samples',start:0,limit:event?8:64}):api.jointCropClimatePrefix(LOOKUP))
        .rejects.toMatchObject({code:'response_rejected'});
    });
  it.each(['none-with-reference','closed-active','none-terminal','closed-with-page'])('rejects invalid absence %s',async fault=>{
    const p=absent(fault.startsWith('none')?'none':'closed');
    if(fault==='none-with-reference')p.reference=accepted().reference;if(fault==='closed-active')p.job.state='simulating';
    if(fault==='none-terminal')p.job.state='failed';if(fault==='closed-with-page')p.page=accepted('samples').page;
    await expect(client(p).api.jointCropClimatePrefix(LOOKUP)).rejects.toMatchObject({code:'response_rejected'});
  });
  it.each([401,403,404,409,422,503])('preserves transport error %i',async status=>{
    const fetch=vi.fn(async()=>new Response('{}',{status}));await expect(client(null,fetch).api.jointCropClimatePrefix(LOOKUP)).rejects.toMatchObject({status});
  });
  it('matches only the same immutable reference and the summary last timestamp',async()=>{
    const summary=await client(accepted()).api.jointCropClimatePrefix(LOOKUP) as JointPrefixSummaryResponse;
    const page=await client(accepted('samples')).api.jointCropClimatePrefixPage(LOOKUP,PIN,{kind:'samples',start:0,limit:64},{summary});
    expect(()=>matchJointPrefixPage(summary,page)).not.toThrow();
    const bad={...page,reference:{...page.reference,manifest:{...page.reference.manifest,program_sha256:'f'.repeat(64)}}};expect(()=>matchJointPrefixPage(summary,bad)).toThrow(ApiError);
    const old={...page,observed_at:AT};expect(()=>matchJointPrefixPage(summary,old)).toThrow(ApiError);
  });
  it('allows empty end pages and rejects wrong selector/shape before or after fetch',async()=>{
    const total=rows.total;const page=await client(accepted('samples',total,1)).api.jointCropClimatePrefixPage(LOOKUP,PIN,{kind:'samples',start:total,limit:1});
    expect(page.page.records).toEqual([]);expect(page.page.next_offset).toBeNull();
    const c=client(accepted('samples'));
    for(const query of [{kind:'samples',start:-1,limit:1},{kind:'samples',start:0,limit:65},{kind:'events',start:0,limit:9},{kind:'samples',start:0.5,limit:1}])
      await expect(c.api.jointCropClimatePrefixPage(LOOKUP,PIN,query as any)).rejects.toThrow(ApiError);
    expect(c.fetch).not.toHaveBeenCalled();
    await expect(c.api.jointCropClimatePrefixPage(LOOKUP,{...PIN,publication_sequence:2},{kind:'samples',start:0,limit:64})).rejects.toThrow(ApiError);
  });
  it.each(['lookup','selector','query','summary'])('rejects a late %s mutation',async mode=>{
    const lookup=structuredClone(LOOKUP),pin={...PIN},query={kind:'samples' as const,start:0,limit:64};
    const summary=accepted();let release!:(v:Response)=>void;
    const fetch=vi.fn(()=>new Promise<Response>(resolve=>release=resolve));const pending=client(null,fetch).api.jointCropClimatePrefixPage(lookup,pin,query,{summary:summary as JointPrefixSummaryResponse});
    if(mode==='lookup')lookup.farm.crop_id='foreign';if(mode==='selector')pin.publication_sequence=2;if(mode==='query')query.limit=1;
    if(mode==='summary')summary.reference.manifest.program_sha256='f'.repeat(64);
    release(new Response(JSON.stringify(accepted('samples')),{headers:{'Content-Type':'application/json'}}));await expect(pending).rejects.toMatchObject({code:'response_rejected'});
  });
  it('handles early/late abort, timeout and whole UTF8 response cap',async()=>{
    const abort=new AbortController();abort.abort();const c=client(accepted());
    await expect(c.api.jointCropClimatePrefix(LOOKUP,abort.signal)).rejects.toMatchObject({code:'request_canceled'});expect(c.fetch).not.toHaveBeenCalled();
    const late=new AbortController();const fetch=vi.fn(async()=>{late.abort();return new Response(JSON.stringify(accepted()),{headers:{'Content-Type':'application/json'}});});
    await expect(client(null,fetch).api.jointCropClimatePrefix(LOOKUP,late.signal)).rejects.toMatchObject({code:'request_canceled'});
    await expect(client(null,vi.fn(async()=>new Response('한'.repeat(700000),{headers:{'Content-Type':'application/json'}}))).api.jointCropClimatePrefix(LOOKUP)).rejects.toMatchObject({code:'response_rejected'});
    vi.useFakeTimers();const never=vi.fn((_p:RequestInfo|URL,_i?:RequestInit)=>new Promise<Response>((_r,reject)=>_i?.signal?.addEventListener('abort',()=>reject(new Error('timeout')))));
    const pending=client(null,never).api.jointCropClimatePrefix(LOOKUP);const rejected=expect(pending).rejects.toMatchObject({code:'network_unresolved'});
    await vi.advanceTimersByTimeAsync(30001);await rejected;
  });
});
