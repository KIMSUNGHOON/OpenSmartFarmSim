import { describe,it,expect,vi } from 'vitest';
import { createApi,ApiError } from './api';
import { decodeCoupledCropPage,assembleCoupledCropReplay,createCoupledCropReplayApi,
  utcMicroseconds,type CoupledCropLookup } from './coupledCropReplay';

const carbon='mg_CH2O/m2_floor',number='fruits_equivalent/m2_floor';
const hash='a'.repeat(64),start='2026-10-01T00:00:00Z',end='2026-10-01T00:05:00Z';
const selection:CoupledCropLookup={result_id:'crop-result-v2:'+hash,scenario_id:'farm-1',
  scenario_revision:'r1',registration_sha256:hash,crop_id:'crop-1'};
const q=(value=0,unit=carbon)=>({value,unit});
// Shapes and boundary values only; not a model execution or agricultural observation.
function state(){return {buffer:q(),leaf:q(),stem_root:q(),temperature_filtered_24h:q(20,'degC'),
  temperature_sum:q(0,'degC_day'),fruit_number:Array.from({length:50},()=>q(0,number)),
  fruit_carbohydrate:Array.from({length:50},()=>q())};}
function sample(at:string){return {at,state:state(),lai:q(0,'m2_leaf/m2_floor'),fruit_carbohydrate_total:q(),
  cumulative:Object.fromEntries(['photosynthesis','growth_respiration','maintenance_leaf','maintenance_stem_root',
    'maintenance_fruit','removal_leaf','removal_stem_root','terminal_carbohydrate','terminal_number',
    'entry_number','event_carbohydrate','event_number'].map(k=>[k,q(0,k.endsWith('number')?number:carbon)])),
  carbon_residual:q(),carbon_residual_budget:q(),number_residual:q(0,number),number_residual_budget:q(0,number)};}
function raw():Record<string,any>{return {result_id:selection.result_id,recorded_at:'2026-10-05T00:00:00.123456Z',
  study_id:'software-shape-only',revision:'r1',farm:Object.fromEntries(Object.entries(selection).filter(([k])=>k!=='result_id')),
  batch_id:'batch-1',zone_id:'zone-1',farm_sha256:hash,source_binding_sha256:hash,
  storage_status:'stored_unpublished_research',claim_scope:'synthetic_crop_math_only',scope:'software_research_only',
  gates:'not_assessed',normalization:'per_m2_floor',profile_applicability:'unvalidated_for_registered_crop',
  temporal_provenance:'synthetic_research_program',start_utc:start,end_utc:end,status:'completed',steps:30,planned_steps:30,
  manifest:{integrator_version:'crop-plant-cohort-rk4-research-v1',
    rate_model_version:'vanthoor-greenlight-explicit-entry-plant-rates-research-v1',
    profiles:Object.fromEntries(['growth_profile','cohort_profile','transport_profile'].map(k=>[k,{profile_id:k,sha256:hash}])),
    policy_sha256:hash,code_sha256:Object.fromEntries(['integrator','coupled','plant','cohorts','allocation','transport'].map(k=>[k,hash])),
    artifact_code_sha256:hash,storage_code_sha256:hash,binding_code_sha256:hash,input_sha256:hash,raw_program_sha256:hash,
    result_sha256:hash,artifact_sha256:hash,payload_sha256:hash,notice_sha256:hash,
    solver:{method:'rk4-fixed-v1',max_step_seconds:10,max_steps:10000,roundoff_rule:'64-ulp-per-operation-v1'},
    time_rule:'UTC_POSIX_whole_seconds_v1',python_version:'3.12.3',convergence:'not_evaluated_for_this_program',
    temperature_sum_method:'analytic_piecewise_constant_fraction_v1',
    research_assumptions:['leaf_stem_fixed_RGR_from_reference_profile_not_measured']},
  samples:[sample(start),sample(end)],events:[],sample_page:{offset:0,limit:64,total:2,next_offset:null},
  event_page:{offset:0,limit:8,total:0,next_offset:null},hold:null};}
const reply=(value:unknown,status=200)=>new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});
function capacity(){
  const data=raw();data.end_utc='2026-10-01T00:08:31Z';
  data.samples=Array.from({length:512},(_,i)=>sample(new Date(Date.parse(start)+i*1000).toISOString().replace('.000Z','Z')));
  data.events=Array.from({length:128},(_,i)=>({at:data.samples[i].at,before:state(),after:state(),
    removed:{leaf:q(),stem_root:q(),fruit_number:Array.from({length:50},()=>q(0,number)),
      fruit_carbohydrate:Array.from({length:50},()=>q())}}));return data;
}
function page(data:Record<string,any>,offset=0,eventOffset=0){
  const p=structuredClone(data);p.samples=data.samples.slice(offset,offset+64);p.events=data.events.slice(eventOffset,eventOffset+8);
  p.sample_page={offset,limit:64,total:data.samples.length,next_offset:offset+64<data.samples.length?offset+64:null};
  p.event_page={offset:eventOffset,limit:8,total:data.events.length,next_offset:eventOffset+8<data.events.length?eventOffset+8:null};return p;
}
function held(at='2026-10-01T00:00:00.000001Z',empty=false){
  const d=raw();d.status='hold';d.steps=0;d.samples=empty?[]:[sample(start)];d.sample_page.total=d.samples.length;
  d.hold={reason_code:'DEPLETED_STATE_HOLD',at,phase:'rk4-k2',time_meaning:'solver_evaluation_time',
    last_confirmed:empty?null:{...sample(start),phase:'boundary'}};return d;
}

describe('closed coupled saved quantities and UTC boundaries',()=>{
  it('preserves exact quantities and synthetic scope without derived harvest',()=>{
    const d=raw();d.samples[1].state.fruit_number[49]=q(.125,number);
    d.samples[1].state.fruit_carbohydrate[49]=q(57.75);
    expect(decodeCoupledCropPage(d,selection)).toEqual(d);
    expect(assembleCoupledCropReplay([decodeCoupledCropPage(d,selection)]).samples).toEqual(d.samples);
  });
  it.each(['result','farm','unknown','50number','50carbon','negative','infinite','unit','number_unit','temperature',
    'cum_unit','residual','model','profile','assumptions','python','solver','gate','scope','calendar','timezone',
    'fractional_sample','reorder','duplicate','page_count','page_offset','page_limit','page_next','page_total','steps',
    'event_fields','event_before','event_removed','event_time','hold_mixed','hold_reason','hold_future','last_future'])
    ('rejects %s before display',fault=>{
      const d=fault.startsWith('hold') || fault.startsWith('last')?held():raw();const s=d.samples[0];
      if(fault==='result')d.result_id='crop-result-v1:'+hash;
      if(fault==='farm')d.farm.crop_id='foreign';
      if(fault==='unknown')s.fresh_kg=100;
      if(fault==='50number')s.state.fruit_number.pop();
      if(fault==='50carbon')s.state.fruit_carbohydrate.push(q());
      if(fault==='negative')s.state.fruit_number[0].value=-1;
      if(fault==='infinite')s.state.buffer.value=Infinity;
      if(fault==='unit')s.state.leaf.unit='kg';
      if(fault==='number_unit')s.state.fruit_number[0].unit='fruit';
      if(fault==='temperature')s.state.temperature_filtered_24h.value=-1;
      if(fault==='cum_unit')s.cumulative.terminal_number.unit=carbon;
      if(fault==='residual')s.number_residual.unit=carbon;
      if(fault==='model')d.manifest.rate_model_version='foreign';
      if(fault==='profile')d.manifest.profiles.growth_profile.sha256='A'.repeat(64);
      if(fault==='assumptions')d.manifest.research_assumptions=[];
      if(fault==='python')d.manifest.python_version=' 3.12.3';
      if(fault==='solver')d.manifest.solver.max_steps=10001;
      if(fault==='gate')d.gates='G1';
      if(fault==='scope')d.claim_scope='forecast';
      if(fault==='calendar')s.at='2026-02-30T00:00:00Z';
      if(fault==='timezone')s.at='2026-10-01T09:00:00+09:00';
      if(fault==='fractional_sample')s.at='2026-10-01T00:00:00.1Z';
      if(fault==='reorder')d.samples.reverse();
      if(fault==='duplicate')d.samples[1].at=start;
      if(fault==='page_count')d.sample_page.total=3;
      if(fault==='page_offset')d.sample_page.offset=3;
      if(fault==='page_limit')d.sample_page.limit=65;
      if(fault==='page_next')d.sample_page.next_offset=1;
      if(fault==='page_total')d.sample_page.total=513;
      if(fault==='steps')d.steps=31;
      if(fault.startsWith('event')){
        const e={at:start,before:state(),after:state(),removed:{leaf:q(),stem_root:q(),
          fruit_number:Array.from({length:50},()=>q(0,number)),fruit_carbohydrate:Array.from({length:50},()=>q())}};
        d.events=[e];d.event_page.total=1;
        if(fault==='event_fields')(e as any).input_id='hidden';
        if(fault==='event_before')e.before.fruit_number=[];
        if(fault==='event_removed')e.removed.fruit_carbohydrate[0]!.unit=number;
        if(fault==='event_time')e.at='2026-10-01T00:05:01Z';
      }
      if(fault==='hold_mixed')d.hold=null;
      if(fault==='hold_reason')d.hold.reason_code='invented';
      if(fault==='hold_future')d.hold.at=start;
      if(fault==='last_future')d.hold.last_confirmed.at='2026-10-01T00:00:00.000002Z';
      expect(()=>decodeCoupledCropPage(d,selection)).toThrow(ApiError);
    });
  it('keeps sub-millisecond hold ordering and separate last-confirmed diagnostics',()=>{
    expect(utcMicroseconds('2026-10-01T00:00:00.000001Z')-utcMicroseconds(start)).toBe(1n);
    expect(Date.parse('2026-10-01T00:00:00.000001Z')).toBe(Date.parse(start));
    const value=assembleCoupledCropReplay([decodeCoupledCropPage(held(),selection)]);
    expect(value.samples).toHaveLength(1);expect(value.hold?.last_confirmed?.phase).toBe('boundary');
    const empty=assembleCoupledCropReplay([decodeCoupledCropPage(held(start,true),selection)]);
    expect(empty.samples).toEqual([]);expect(empty.hold?.last_confirmed).toBeNull();
  });
  it.each(['start','end'])('rejects a truncated completed %s after page assembly',key=>{
    const d=raw();d.samples[key==='start'?0:1].at='2026-10-01T00:01:00Z';
    if(key==='end')d.samples[1].at='2026-10-01T00:04:00Z';
    expect(()=>assembleCoupledCropReplay([decodeCoupledCropPage(d,selection)])).toThrow(ApiError);
  });
  it('accepts signed residuals without recomputing crop or conservation values',()=>{
    const d=raw();d.samples[0].carbon_residual.value=-1e-12;d.samples[0].number_residual.value=-1e-13;
    expect(decodeCoupledCropPage(d,selection).samples[0]!.number_residual.value).toBe(-1e-13);
  });
});

describe('complete sequential sample pages and separately paged events',()=>{
  it('keeps all 512 samples and fetches events once; keeps all 128 events on demand',async ()=>{
    const d=capacity(),calls:URL[]=[],progress:{pages:number;samples:number;total:number}[]=[];
    let active=0,maxActive=0;
    const request=vi.fn(async(path:string)=>{active++;maxActive=Math.max(maxActive,active);
      const u=new URL(path,'https://localhost');calls.push(u);await Promise.resolve();active--;
      return page(d,Number(u.searchParams.get('sample_offset')),Number(u.searchParams.get('event_offset')));});
    const api=createCoupledCropReplayApi(request),value=await api.coupledCropReplay(selection,{onProgress:p=>progress.push(p)});
    expect(value.samples).toEqual(d.samples);expect(value.events).toEqual(d.events.slice(0,8));
    expect(value.total_events).toBe(128);expect(value.total_samples).toBe(512);expect(maxActive).toBe(1);
    expect(calls).toHaveLength(8);expect(progress.at(-1)).toEqual({pages:8,samples:512,total:512});
    expect(calls.slice(1).every(u=>u.searchParams.get('event_offset')==='128')).toBe(true);
    const events=[...value.events];
    for(let offset=8;offset<128;offset+=8){const p=await api.coupledCropEvents(value,offset);events.push(...p.events);}
    expect(events).toEqual(d.events);expect(calls.slice(8).every(u=>u.searchParams.get('sample_offset')==='512')).toBe(true);
  });
  it.each(['missing','duplicate','order','hash','recorded','hold','total','first_offset','events'])
    ('rejects %s pages without a completed result',async fault=>{
      const d=capacity();let calls=0;
      const request=async(path:string)=>{const u=new URL(path,'https://localhost');
        const offset=Number(u.searchParams.get('sample_offset')),eventOffset=Number(u.searchParams.get('event_offset'));
        const p=page(d,offset,eventOffset);calls++;
        if(calls===1 && fault==='first_offset')return page(d,64,0);
        if(calls!==2)return p;
        if(fault==='missing')p.samples.pop();
        if(fault==='duplicate')p.samples[0].at=d.samples[63].at;
        if(fault==='order')return page(d,128,128);
        if(fault==='hash')p.manifest.payload_sha256='b'.repeat(64);
        if(fault==='recorded')p.recorded_at='2026-10-05T00:00:01Z';
        if(fault==='hold')return page({...d,...held()},0,0);
        if(fault==='total'){p.sample_page.total=511;}
        if(fault==='events')return page(d,offset,0);
        return p;};
      await expect(createCoupledCropReplayApi(request).coupledCropReplay(selection)).rejects.toBeInstanceOf(ApiError);
      expect(calls).toBeLessThanOrEqual(2);
    });
  it('rejects stale or foreign separate event pages',async ()=>{
    const d=capacity(),first=decodeCoupledCropPage(page(d),selection);
    const value=assembleCoupledCropReplay(Array.from({length:8},(_,i)=>decodeCoupledCropPage(page(d,i*64,i?128:0),selection)));
    const wrong=page(d,512,8);wrong.manifest.result_sha256='b'.repeat(64);
    await expect(createCoupledCropReplayApi(async()=>wrong).coupledCropEvents(value,8)).rejects.toBeInstanceOf(ApiError);
    expect(first.events).toHaveLength(8);
  });
  it.each(['result_id','scenario_id','scenario_revision','registration_sha256','crop_id'] as const)
    ('rejects invalid %s lookup before network',async key=>{
      const request=vi.fn(async()=>raw());
      await expect(createCoupledCropReplayApi(request).coupledCropReplay({...selection,[key]:'<invalid>'})).rejects.toBeInstanceOf(ApiError);
      expect(request).not.toHaveBeenCalled();
    });
  it('identity compares JSON field values rather than insertion order',async ()=>{
    const d=capacity();
    const request=async(path:string)=>{const u=new URL(path,'https://localhost');const p=page(d,
      Number(u.searchParams.get('sample_offset')),Number(u.searchParams.get('event_offset')));
      p.manifest=Object.fromEntries(Object.entries(p.manifest).reverse());return p;};
    expect((await createCoupledCropReplayApi(request).coupledCropReplay(selection)).samples).toEqual(d.samples);
  });
});

describe('existing authenticated bounded transport with cancellation',()=>{
  const token='synthetic-coupled-browser-token-only';
  it('uses only exact same-origin read queries, bounded body and memory Bearer',async ()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply(raw()));
    const value=await createApi(token,fetcher).coupledCropReplay(selection);
    expect(value.samples).toEqual(raw().samples);const [url,init]=fetcher.mock.calls[0]!;
    const u=new URL(String(url),'https://localhost');
    expect(decodeURIComponent(u.pathname)).toBe('/v1/crop-coupled-research-results/'+selection.result_id);
    expect(Object.fromEntries(u.searchParams)).toEqual({...raw().farm,sample_offset:'0',sample_limit:'64',event_offset:'0',event_limit:'8'});
    expect(init).toMatchObject({method:'GET',credentials:'omit',cache:'no-store',redirect:'error',headers:{authorization:'Bearer '+token}});
    expect(init?.body).toBeUndefined();
  });
  it.each([401,403,404,422,503])('HTTP %s stops all pages and hides private details',async status=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply({private:'secret'},status));
    const error=await createApi(token,fetcher).coupledCropReplay(selection).catch(e=>e);
    expect(error).toBeInstanceOf(ApiError);expect(error.status).toBe(status);expect(String(error)).not.toContain('secret');
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('rejects 2 MiB plus one bytes and cancels the response stream',async ()=>{
    let canceled=false;const body=new ReadableStream<Uint8Array>({start(c){c.enqueue(new Uint8Array(2*1024*1024+1));},cancel(){canceled=true;}});
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(new Response(body,{headers:{'content-type':'application/json'}}));
    await expect(createApi(token,fetcher).coupledCropReplay(selection)).rejects.toMatchObject({code:'response_rejected'});
    expect(canceled).toBe(true);
  });
  it('pre-canceled lookup starts no fetch',async ()=>{
    const abort=new AbortController();abort.abort();const fetcher=vi.fn<typeof fetch>();
    await expect(createApi(token,fetcher).coupledCropReplay(selection,{signal:abort.signal})).rejects.toMatchObject({code:'request_canceled'});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('cancellation reaches an active fetch and ignores a late successful reply',async ()=>{
    const abort=new AbortController();let resolve!:(value:Response)=>void,activeSignal:AbortSignal|null|undefined;
    const fetcher=vi.fn<typeof fetch>().mockImplementation((_url,init)=>{activeSignal=init?.signal;return new Promise(r=>resolve=r);});
    const pending=createApi(token,fetcher).coupledCropReplay(selection,{signal:abort.signal});
    let bodyCanceled=false;const lateBody=new ReadableStream<Uint8Array>({start(c){c.enqueue(new TextEncoder().encode(JSON.stringify(raw())));},
      cancel(){bodyCanceled=true;}});
    await Promise.resolve();abort.abort();expect(activeSignal?.aborted).toBe(true);
    resolve(new Response(lateBody,{headers:{'content-type':'application/json'}}));
    await expect(pending).rejects.toMatchObject({code:'request_canceled'});
    expect(bodyCanceled).toBe(true);
  });
  it('a progress callback cancellation never requests the next page',async ()=>{
    const abort=new AbortController(),d=capacity();const fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply(page(d)));
    await expect(createApi(token,fetcher).coupledCropReplay(selection,{signal:abort.signal,onProgress:()=>abort.abort()}))
      .rejects.toMatchObject({code:'request_canceled'});expect(fetcher).toHaveBeenCalledTimes(1);
  });
  it('invalid UTF-8 cannot become a completed replay',async ()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(new Response(new Uint8Array([0xc0,0xaf]),
      {headers:{'content-type':'application/json'}}));
    await expect(createApi(token,fetcher).coupledCropReplay(selection)).rejects.toMatchObject({code:'response_rejected'});
  });
  it('rights denied after a first page exposes no completed result or later requests',async ()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(reply(page(capacity())))
      .mockResolvedValueOnce(reply({private:'hidden'},422));
    await expect(createApi(token,fetcher).coupledCropReplay(selection)).rejects.toMatchObject({code:'invalid_request',status:422});
    expect(fetcher).toHaveBeenCalledTimes(2);
  });
  it('keeps the existing 30 second per-request timeout and removes external listeners',async ()=>{
    vi.useFakeTimers();const abort=new AbortController(),add=vi.spyOn(abort.signal,'addEventListener'),remove=vi.spyOn(abort.signal,'removeEventListener');
    const fetcher=vi.fn<typeof fetch>().mockImplementation((_url,init)=>new Promise((_r,reject)=>
      init?.signal?.addEventListener('abort',()=>reject(new DOMException('Aborted','AbortError')),{once:true})));
    try{
      const pending=createApi(token,fetcher).coupledCropReplay(selection,{signal:abort.signal}).catch(e=>e);
      await vi.advanceTimersByTimeAsync(30_000);expect(await pending).toMatchObject({code:'network_unresolved'});
      expect(fetcher).toHaveBeenCalledTimes(1);expect(add).toHaveBeenCalledTimes(1);expect(remove).toHaveBeenCalledTimes(1);
      expect(vi.getTimerCount()).toBe(0);
    }finally{vi.useRealTimers();}
  });
});
