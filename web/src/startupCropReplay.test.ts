import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createApi,ApiError } from './api';
import { decodeStartupCropPage,assembleStartupCropReplay,createStartupCropReplayApi,
  type StartupCropLookup } from './startupCropReplay';

// Decoded public JSON from an own synthetic, cleaned-up TLS/SCRAM test; not wire bytes or live history.
const fixture=readFileSync(new URL('../e2e/startup-crop-recorded-page.json',import.meta.url));
const recorded=JSON.parse(fixture.toString());
const selection:StartupCropLookup={result_id:recorded.result_id,...recorded.farm};
const carbon='mg_CH2O/m2_floor',number='fruits_equivalent/m2_floor';
const stamp=(seconds:number)=>new Date(Date.parse(recorded.start_utc)+seconds*1000).toISOString().replace('.000Z','Z');
// The following helpers change page shapes and times only. They do not execute a crop model.
function raw():Record<string,any>{
  const p=structuredClone(recorded);p.samples=p.samples.slice(0,2);p.events=[];
  p.end_utc=p.samples[1].at;p.steps=1;p.planned_steps=1;
  p.sample_page={offset:0,limit:64,total:2,next_offset:null};p.event_page={offset:0,limit:8,total:0,next_offset:null};return p;
}
function capacity(){
  const p=raw();p.end_utc=stamp(511);p.steps=511;p.planned_steps=511;
  p.samples=Array.from({length:512},(_,i)=>({...structuredClone(p.samples[0]),at:stamp(i)}));
  p.events=Array.from({length:128},(_,i)=>({...structuredClone(recorded.events[0]),at:stamp(i)}));return p;
}
function page(p:Record<string,any>,sampleOffset=0,eventOffset=0):Record<string,any>{
  return {...p,samples:p.samples.slice(sampleOffset,sampleOffset+64),events:p.events.slice(eventOffset,eventOffset+8),
    sample_page:{offset:sampleOffset,limit:64,total:p.samples.length,next_offset:sampleOffset+64<p.samples.length?sampleOffset+64:null},
    event_page:{offset:eventOffset,limit:8,total:p.events.length,next_offset:eventOffset+8<p.events.length?eventOffset+8:null}};
}
function held(empty=false){
  const p=raw();p.status='hold';p.steps=0;p.samples=empty?[]:[p.samples[0]];p.sample_page.total=p.samples.length;
  p.hold={reason_code:'DEPLETED_STATE_HOLD',at:p.start_utc.replace('Z',empty?'Z':'.000001Z'),phase:'rk4-k2',
    time_meaning:'solver_evaluation_time',last_confirmed:empty?null:{...structuredClone(p.samples[0]),phase:'boundary'}};return p;
}
const reply=(p:unknown,status=200)=>new Response(JSON.stringify(p),{status,headers:{'content-type':'application/json'}});

describe('startup saved response and exact model boundary',()=>{
  it('keeps the recorded TLS projection, all 50 arrays, 16 cumulatives and 4 diagnostics unchanged',()=>{
    expect(createHash('sha256').update(fixture).digest('hex')).toBe('a72b82432eb73163af9767c5445a41c3058d37fee5c369f6c36345b2db4edac7');
    const p=decodeStartupCropPage(recorded,selection);expect(p).toEqual(recorded);
    expect(p.samples).toHaveLength(64);expect(p.events).toHaveLength(8);
    expect(p.samples[63]?.state.fruit_number).toEqual(recorded.samples[63].state.fruit_number);
    expect(Object.keys(p.samples[63]!.cumulative)).toHaveLength(16);
    expect(Object.keys(p.samples[63]!.startup_diagnostics)).toHaveLength(4);
    expect(p.manifest.startup_assumptions).toContain('approximately_8_52_percent_small_cohort_error_observed_in_synthetic_test');
  });
  it.each(['old_id','schema','model','program','policy','dependency','missing_code','assumptions','transition','balance_rule',
    'area_zero','area_exponent','area_unit','unknown','fruit_count','fruit_unit','cumulative','diagnostics','signed_budget',
    'nonfinite','phase','date','reorder','duplicate','hold_missing','future_sample','future_confirmed'])('rejects %s before use',fault=>{
      const p=fault.startsWith('hold') || fault.startsWith('future')?held():raw(),s=p.samples[0],m=p.manifest;
      if(fault==='old_id')p.result_id=p.result_id.replace('v3','v2');
      if(fault==='schema')p.schema_version='crop-coupled-replay-v1';
      if(fault==='model')m.rate_model_version='vanthoor-greenlight-explicit-entry-plant-rates-research-v1';
      if(fault==='program')delete m.program_version;
      if(fault==='policy')m.allocation_policy_sha256='A'.repeat(64);
      if(fault==='dependency')delete m.artifact_dependency_sha256.canonical_json;
      if(fault==='missing_code')delete m.code_sha256.startup;
      if(fault==='assumptions')m.startup_assumptions[0]=m.startup_assumptions[1];
      if(fault==='transition')m.startup_transition='automatic_set';
      if(fault==='balance_rule')m.startup_balance_rule='absolute_floor';
      if(fault==='area_zero')p.floor_area.value='0.0';
      if(fault==='area_exponent')p.floor_area.value='1e2';
      if(fault==='area_unit')p.floor_area.unit='ha';
      if(fault==='unknown')p.fresh_kg=100;
      if(fault==='fruit_count')s.state.fruit_carbohydrate.pop();
      if(fault==='fruit_unit')s.state.fruit_number[0].unit='fruit';
      if(fault==='cumulative')delete s.cumulative.deferred_fruit_carbohydrate;
      if(fault==='diagnostics')s.startup_diagnostics.requested_residual.unit=number;
      if(fault==='signed_budget')s.startup_diagnostics.requested_budget.value=-1;
      if(fault==='nonfinite')s.state.buffer.value=Infinity;
      if(fault==='phase')s.phase='boundary';
      if(fault==='date')s.at='2026-02-30T00:00:00Z';
      if(fault==='reorder')p.samples.reverse();
      if(fault==='duplicate')p.samples[1].at=s.at;
      if(fault==='hold_missing')p.hold=null;
      if(fault==='future_sample')p.samples[0].at=p.end_utc;
      if(fault==='future_confirmed')p.hold.last_confirmed.at=p.end_utc;
      expect(()=>decodeStartupCropPage(p,selection)).toThrow(ApiError);
    });
  it('assembles a complete result and preserves fractional hold diagnostics without another sample',()=>{
    const complete=assembleStartupCropReplay([decodeStartupCropPage(raw(),selection)]);
    expect(complete.samples).toEqual(raw().samples);expect(complete.events).toEqual([]);
    const past=assembleStartupCropReplay([decodeStartupCropPage(held(),selection)]);
    expect(past.samples).toHaveLength(1);expect(past.hold?.at).toBe(stamp(0).replace('Z','.000001Z'));
    expect(past.hold?.last_confirmed?.phase).toBe('boundary');
    expect(assembleStartupCropReplay([decodeStartupCropPage(held(true),selection)]).samples).toEqual([]);
  });
  it('retains signed diagnostics and decimal area text without crop arithmetic or money conversion',()=>{
    const p=raw();p.floor_area.value='0.000000000000000000000000000000000001';
    p.samples[0].startup_diagnostics.requested_residual.value=-1e-13;
    const value=decodeStartupCropPage(p,selection);expect(value.floor_area.value).toBe(p.floor_area.value);
    expect(value.samples[0]?.startup_diagnostics.requested_residual).toEqual({value:-1e-13,unit:carbon});
  });
  it.each(['start','end'])('rejects a missing completed %s after assembly',where=>{
    const p=raw();p[where+'_utc']=stamp(where==='start'?-1:2);
    expect(()=>assembleStartupCropReplay([decodeStartupCropPage(p,selection)])).toThrow(ApiError);
  });
});

describe('startup complete sequential samples and events',()=>{
  it('loads all 512 samples and 128 events once in 16 bounded sequential requests',async ()=>{
    const p=capacity(),calls:URL[]=[];let active=0,maxActive=0;
    const request=vi.fn(async(path:string)=>{
      active++;maxActive=Math.max(active,maxActive);const u=new URL(path,'https://localhost');calls.push(u);
      await Promise.resolve();active--;return page(p,Number(u.searchParams.get('sample_offset')),Number(u.searchParams.get('event_offset')));
    });
    const value=await createStartupCropReplayApi(request).startupCropReplay(selection);
    expect(value.samples).toEqual(p.samples);expect(value.events).toEqual(p.events);
    expect(value.total_samples).toBe(512);expect(value.total_events).toBe(128);
    expect(calls).toHaveLength(16);expect(maxActive).toBe(1);
    expect(calls[8]?.searchParams.get('sample_offset')).toBe('512');
    for(const call of request.mock.calls){expect(call.slice(1,6)).toEqual(['GET',undefined,200,2*1024*1024,30_000]);}
  });
  it('uses the authenticated transport for the new same-origin read without a request body',async ()=>{
    const token='synthetic-startup-client-token-only',fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply(raw()));
    const value=await createApi(token,fetcher).startupCropReplay(selection);expect(value.samples).toEqual(raw().samples);
    const [path,init]=fetcher.mock.calls[0]!,u=new URL(String(path),'https://localhost');
    expect(decodeURIComponent(u.pathname)).toBe('/v1/crop-startup-research-results/'+selection.result_id);
    expect(Object.fromEntries(u.searchParams)).toEqual({...recorded.farm,sample_offset:'0',sample_limit:'64',event_offset:'0',event_limit:'8'});
    expect(init).toMatchObject({method:'GET',body:undefined,credentials:'omit',cache:'no-store',redirect:'error',
      headers:{authorization:'Bearer '+token}});
  });
  it.each(['sample_offset','event_offset','sample_total','event_total','sample_order','event_order','result_hash',
    'allocation_hash','startup_code','area','recorded','status','missing_sample','missing_event'])
    ('rejects %s drift without a partial replay',async fault=>{
      const data=capacity();let requests=0;
      const request=async(path:string)=>{
        const u=new URL(path,'https://localhost'),p=structuredClone(page(data,
          Number(u.searchParams.get('sample_offset')),Number(u.searchParams.get('event_offset'))));
        if(++requests===2){
          if(fault==='sample_offset')p.sample_page.offset=0;
          if(fault==='event_offset')p.event_page.offset=0;
          if(fault==='sample_total')p.sample_page.total=511;
          if(fault==='event_total')p.event_page.total=127;
          if(fault==='sample_order')for(let i=0;i<p.samples.length;i++)p.samples[i].at=stamp(i);
          if(fault==='event_order')for(let i=0;i<p.events.length;i++)p.events[i].at=stamp(i);
          if(fault==='result_hash')p.manifest.result_sha256='b'.repeat(64);
          if(fault==='allocation_hash')p.manifest.allocation_policy_sha256='b'.repeat(64);
          if(fault==='startup_code')p.manifest.code_sha256.startup='b'.repeat(64);
          if(fault==='area')p.floor_area.value='101.0';
          if(fault==='recorded')p.recorded_at='2026-10-05T00:00:00Z';
          if(fault==='status')p.status='hold';
          if(fault==='missing_sample')p.samples.pop();
          if(fault==='missing_event')p.events.pop();
        }
        return p;
      };
      await expect(createStartupCropReplayApi(request).startupCropReplay(selection)).rejects.toBeInstanceOf(ApiError);
      expect(requests).toBe(2);
    });
  it('compares field values independent of JSON key order',async ()=>{
    const data=capacity();const request=async(path:string)=>{
      const u=new URL(path,'https://localhost'),p=page(data,Number(u.searchParams.get('sample_offset')),Number(u.searchParams.get('event_offset')));
      p.manifest=Object.fromEntries(Object.entries(p.manifest).reverse());return p;
    };
    expect((await createStartupCropReplayApi(request).startupCropReplay(selection)).events).toEqual(data.events);
  });
  it.each(['result_id','scenario_id','scenario_revision','registration_sha256','crop_id'] as const)
    ('rejects invalid %s before the network',async key=>{
      const request=vi.fn(async()=>raw());
      await expect(createStartupCropReplayApi(request).startupCropReplay({...selection,[key]:'<invalid>'})).rejects.toBeInstanceOf(ApiError);
      expect(request).not.toHaveBeenCalled();
    });
  it.each([{sample_offset:-1},{sample_offset:513},{sample_limit:65},{event_offset:129},{event_limit:9},{event_limit:0},
    {sample_offset:NaN},{sample_offset:.5}])('rejects invalid pagination %j before the network',async change=>{
      const request=vi.fn(async()=>raw());
      await expect(createStartupCropReplayApi(request).startupCropPage(selection,
        {sample_offset:0,sample_limit:64,event_offset:0,event_limit:8,...change})).rejects.toBeInstanceOf(ApiError);
      expect(request).not.toHaveBeenCalled();
    });
  it('returns only the confirmed past or an empty result for holds',async ()=>{
    for(const empty of [false,true]){
      const p=held(empty),value=await createStartupCropReplayApi(async()=>p).startupCropReplay(selection);
      expect(value.samples).toEqual(p.samples);expect(value.hold?.last_confirmed).toEqual(p.hold.last_confirmed);
      expect(value.total_samples).toBe(empty?0:1);
    }
  });
  it('rejects a caller changing farm identity during progress before another request',async ()=>{
    const lookup={...selection},request=vi.fn(async()=>page(capacity()));
    await expect(createStartupCropReplayApi(request).startupCropReplay(lookup,
      {onProgress:()=>{lookup.crop_id='another-crop';}})).rejects.toBeInstanceOf(ApiError);
    expect(request).toHaveBeenCalledTimes(1);
  });
});

describe('startup cancellation, authorization and bounded transport',()=>{
  const token='synthetic-startup-client-token-only';
  it.each([401,403,404,422,503])('HTTP %s stops collection without returning private details',async status=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply({private:'hidden'},status));
    const error=await createApi(token,fetcher).startupCropReplay(selection).catch(e=>e);
    expect(error).toBeInstanceOf(ApiError);expect(error.status).toBe(status);expect(String(error)).not.toContain('hidden');
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('rights denied between sample pages returns no partial data',async ()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(reply(page(capacity())))
      .mockResolvedValueOnce(reply({private:'hidden'},422));
    await expect(createApi(token,fetcher).startupCropReplay(selection)).rejects.toMatchObject({code:'invalid_request',status:422});
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
  it('rights denied during remaining event pages returns no completed samples',async ()=>{
    const p=capacity(),fetcher=vi.fn<typeof fetch>();
    for(let i=0;i<8;i++)fetcher.mockResolvedValueOnce(reply(page(p,i*64,i*8)));
    fetcher.mockResolvedValueOnce(reply({},403));
    await expect(createApi(token,fetcher).startupCropReplay(selection)).rejects.toMatchObject({code:'access_denied',status:403});
    expect(fetcher).toHaveBeenCalledTimes(9);
  });
  it('pre-canceled lookup starts no network request',async ()=>{
    const abort=new AbortController();abort.abort();const fetcher=vi.fn<typeof fetch>();
    await expect(createApi(token,fetcher).startupCropReplay(selection,{signal:abort.signal})).rejects.toMatchObject({code:'request_canceled'});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('canceling progress prevents later requests and clears per-request listeners',async ()=>{
    const abort=new AbortController(),remove=vi.spyOn(abort.signal,'removeEventListener');
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply(page(capacity())));
    await expect(createApi(token,fetcher).startupCropReplay(selection,{signal:abort.signal,onProgress:()=>abort.abort()}))
      .rejects.toMatchObject({code:'request_canceled'});
    expect(fetcher).toHaveBeenCalledTimes(1);expect(remove).toHaveBeenCalledTimes(1);
  });
  it('an account or result change can abort an active request and reject its late success',async ()=>{
    const abort=new AbortController();let resolve!:(v:Response)=>void,signal:AbortSignal|null|undefined;
    const fetcher=vi.fn<typeof fetch>().mockImplementation((_url,init)=>{signal=init?.signal;return new Promise(r=>{resolve=r;});});
    const pending=createApi(token,fetcher).startupCropReplay(selection,{signal:abort.signal});
    await Promise.resolve();abort.abort();expect(signal?.aborted).toBe(true);
    let closedBody=false;const body=new ReadableStream<Uint8Array>({start(c){c.enqueue(new TextEncoder().encode(JSON.stringify(raw())));},
      cancel(){closedBody=true;}});
    resolve(new Response(body,{headers:{'content-type':'application/json'}}));
    await expect(pending).rejects.toMatchObject({code:'request_canceled'});expect(closedBody).toBe(true);
  });
  it('rejects a 2 MiB plus one body and cancels the stream',async ()=>{
    let closedBody=false;const body=new ReadableStream<Uint8Array>({start(c){c.enqueue(new Uint8Array(2*1024*1024+1));},
      cancel(){closedBody=true;}});
    await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(new Response(body,{headers:{'content-type':'application/json'}})))
      .startupCropReplay(selection)).rejects.toMatchObject({code:'response_rejected'});expect(closedBody).toBe(true);
  });
  it('invalid UTF-8 cannot become a decoded crop result',async ()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(new Response(new Uint8Array([0xc0,0xaf]),{headers:{'content-type':'application/json'}}));
    await expect(createApi(token,fetcher).startupCropReplay(selection)).rejects.toMatchObject({code:'response_rejected'});
  });
  it('retains the 30 second timeout and removes timers and external listeners',async ()=>{
    vi.useFakeTimers();const abort=new AbortController(),remove=vi.spyOn(abort.signal,'removeEventListener');
    const fetcher=vi.fn<typeof fetch>().mockImplementation((_url,init)=>new Promise((_resolve,reject)=>
      init?.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true})));
    try{
      const pending=createApi(token,fetcher).startupCropReplay(selection,{signal:abort.signal}).catch(e=>e);
      await vi.advanceTimersByTimeAsync(30_000);expect(await pending).toMatchObject({code:'network_unresolved'});
      expect(fetcher).toHaveBeenCalledTimes(1);expect(remove).toHaveBeenCalledTimes(1);expect(vi.getTimerCount()).toBe(0);
    }finally{vi.useRealTimers();}
  });
});
