import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { ApiError,createApi } from './api';
import { decodeCycleCropResponse,createCycleCropReplayApi,validCycleCropLookup,type CycleCropLookup } from './cycleCropReplay';

const bytes=readFileSync(new URL('../e2e/cycle-crop-recorded-responses.json',import.meta.url));
const fixture=JSON.parse(bytes.toString());
const lookup=(p:Record<string,any>):CycleCropLookup=>({result_id:p.result_id,...p.farm});
const first=fixture.long[0],selection=lookup(first);
const samplePage=()=>structuredClone(fixture.long.find((p:Record<string,any>)=>p.page?.kind==='samples'));
const eventPage=()=>structuredClone(fixture.long.find((p:Record<string,any>)=>p.page?.kind==='events'));
const emptyHeld=()=>structuredClone(fixture.short.find((p:Record<string,any>)=>p.summary?.status==='hold'));
const stamp=(seconds:number)=>new Date(Date.parse(first.reference.start_utc)+seconds*1000).toISOString().replace('.000Z','Z');
// Shape-only cases below reuse synthetic rows; they do not run the crop equations.
function shapedPage(summary:Record<string,any>,kind:'samples'|'events',offset=0,limit=64,one=false):Record<string,any>{
  const total=summary.reference[kind==='samples'?'sample_count':'event_count'];
  const original=(kind==='samples'?samplePage():eventPage()).page.records[0];
  const count=Math.min(one?1:limit,total-offset),next=offset+count;
  return {...structuredClone(summary),summary:null,page:{kind,offset,limit,total,next_offset:next<total?next:null,
    records:Array.from({length:count},(_,i)=>({...structuredClone(original),at:stamp(offset+i)}))}};
}

describe('cycle original public results',()=>{
  it('preserves all actual short/25h public JSON and original arrays unchanged',()=>{
    expect(createHash('sha256').update(bytes).digest('hex')).toBe('43fad7bf11f43a2fd92ed04323a024848b1e8d086add391e0a714016a3e3c990');
    expect(fixture.scope).toBe('own_synthetic_decoded_public_TLS_JSON_not_wire_bytes_live_history_or_real_farm_data');
    for(const raw of [...fixture.short,...fixture.long])expect(decodeCycleCropResponse(raw,lookup(raw))).toEqual(raw);
    expect(first.reference.steps).toBe(11400);expect(first.reference.sample_count).toBe(27);
    expect(first.reference.event_count).toBe(5);
    const p=samplePage();expect(p.page.records[0].state.fruit_number).toHaveLength(50);
    expect(Object.keys(p.page.records[0].cumulative)).toHaveLength(16);
    expect(Object.keys(p.page.records[0].startup_diagnostics)).toHaveLength(4);
    expect(eventPage().page.records[0].removed.fruit_carbohydrate).toHaveLength(50);
  });
  it.each(['old_id','lookup_unknown','scope','gates','schema','top_unknown','reference_unknown','reference_missing',
    'farm','area_zero','area_unit','area_exponent','hash','dependency','artifact_ref','period','whole_date','duration',
    'steps_bool','steps_fraction','steps_over','steps_mismatch','count_over','storage_over','summary_xor',
    'model','manifest_unknown','code','physical','profile','plan','input_root','calculation','solver','boundary',
    'python','page_unknown','page_kind','page_offset','page_limit','page_total','page_next','page_empty',
    'sample_nonfinite','sample_unknown','sample_unit','sample_count','cumulative','diagnostics','budget',
    'carbon_balance','number_balance','requested_balance','respiration_balance','sample_fractional',
    'sample_future','sample_duplicate','sample_reverse','event_unknown','event_count','event_unit'])
    ('rejects %s before rendering',fault=>{
      const isPage=fault.startsWith('page_') || fault.startsWith('sample_') || fault.startsWith('event_')
        || ['cumulative','diagnostics','budget','carbon_balance','number_balance','requested_balance','respiration_balance'].includes(fault);
      const p=fault.startsWith('event_')?eventPage():isPage?samplePage():structuredClone(first);
      const r=p.reference,m=p.summary?.manifest,s=p.page?.records[0],pick=lookup(p);
      if(fault==='old_id')(pick as any).result_id=pick.result_id.replace('cycle-result-v1','result-v3');
      if(fault==='lookup_unknown')(pick as any).tenant='other';
      if(fault==='scope')r.scope='production';if(fault==='gates')r.gates='G3a';
      if(fault==='schema')p.schema_version='crop-startup-replay-v1';if(fault==='top_unknown')p.fresh_kg=1;
      if(fault==='reference_unknown')r.fresh_kg=1;if(fault==='reference_missing')delete r.head_sha256;
      if(fault==='farm')p.farm.crop_id='other';if(fault==='area_zero')r.floor_area.value='0.0';
      if(fault==='area_unit')r.floor_area.unit='ha';if(fault==='area_exponent')r.floor_area.value='1e2';
      if(fault==='hash')r.head_sha256='A'.repeat(64);if(fault==='dependency')delete r.server_dependency_sha256.file_helper;
      if(fault==='artifact_ref')r.artifact_ref='crop-cycle-artifact-v1:'+'a'.repeat(64);
      if(fault==='period')r.end_utc=r.start_utc;if(fault==='whole_date')r.start_utc=r.start_utc.replace('Z','.000001Z');
      if(fault==='duration')r.end_utc='2028-01-01T00:00:00Z';if(fault==='steps_bool')r.steps=true;
      if(fault==='steps_fraction')r.steps=0.5;if(fault==='steps_over')r.steps=40000001;
      if(fault==='steps_mismatch')r.steps--;if(fault==='count_over')r.sample_count=131073;
      if(fault==='storage_over')r.storage_bytes=512*1024*1024+1;if(fault==='summary_xor')p.page=samplePage().page;
      if(fault==='model')m.rate_model_version='automatic_fruit_set';if(fault==='manifest_unknown')m.coefficients={};
      if(fault==='code')delete m.code_sha256.continuation;if(fault==='physical')delete m.physical_code_sha256.startup;
      if(fault==='profile')m.profile_sha256.growth_profile={sha256:'a'.repeat(64)};if(fault==='plan')m.planned_steps++;
      if(fault==='input_root')m.input_root_sha256='a'.repeat(64);if(fault==='calculation')m.calculation_sha256='a'.repeat(64);
      if(fault==='solver')m.solver.max_steps=10000;if(fault==='boundary')m.boundary_count=393217;
      if(fault==='python')m.python_version='node22';if(fault==='page_unknown')p.page.private_path='path';
      if(fault==='page_kind')p.page.kind='summary';if(fault==='page_offset')p.page.offset=-1;
      if(fault==='page_limit')p.page.limit=65;if(fault==='page_total')p.page.total++;
      if(fault==='page_next')p.page.next_offset++;if(fault==='page_empty')p.page.records=[];
      if(fault==='sample_nonfinite')s.state.leaf.value=Infinity;if(fault==='sample_unknown')s.fresh_kg=1;
      if(fault==='sample_unit')s.state.fruit_number[0].unit='fruit';if(fault==='sample_count')s.state.fruit_number.pop();
      if(fault==='cumulative')delete s.cumulative.deferred_fruit_carbohydrate;
      if(fault==='diagnostics')s.startup_diagnostics.requested_residual.unit='kg';
      if(fault==='budget')s.startup_diagnostics.requested_budget.value=-1;
      if(fault==='carbon_balance')s.carbon_residual.value=s.carbon_residual_budget.value+1;
      if(fault==='number_balance')s.number_residual.value=s.number_residual_budget.value+1;
      if(fault==='requested_balance')s.startup_diagnostics.requested_residual.value=s.startup_diagnostics.requested_budget.value+1;
      if(fault==='respiration_balance')s.startup_diagnostics.growth_respiration_residual.value=s.startup_diagnostics.growth_respiration_budget.value+1;
      if(fault==='sample_fractional')s.at=s.at.replace('Z','.000001Z');if(fault==='sample_future')s.at='2028-01-01T00:00:00Z';
      if(fault==='sample_duplicate')p.page.records[1].at=s.at;if(fault==='sample_reverse')p.page.records.reverse();
      if(fault==='event_unknown')s.fresh_kg=1;if(fault==='event_count')s.removed.fruit_carbohydrate.pop();
      if(fault==='event_unit')s.removed.leaf.unit='kg';
      expect(()=>decodeCycleCropResponse(p,pick)).toThrow(ApiError);
    });
  it('accepts selected outputs without endpoint samples and completed zero selected outputs',()=>{
    const p=structuredClone(first);p.reference.sample_count=0;
    expect(decodeCycleCropResponse(p,selection)).toEqual(p);
    const page=samplePage();page.page.records=page.page.records.slice(1);page.page.offset=1;
    expect(decodeCycleCropResponse(page,selection)).toEqual(page);
    expect(validCycleCropLookup(selection)).toBe(true);
  });
});

describe('cycle sequential bounded pages',()=>{
  it.each(['samples','events'] as const)('follows the actual byte-short %s pages once in order',async kind=>{
    const originals=fixture.long.filter((p:Record<string,any>)=>p.page?.kind===kind && p.page.records.length);
    const calls:URL[]=[],seen:unknown[]=[];let active=0,maxActive=0;
    const request=vi.fn(async(path:string)=>{
      active++;maxActive=Math.max(active,maxActive);const u=new URL(path,'https://localhost');calls.push(u);
      await Promise.resolve();active--;
      return structuredClone(u.searchParams.get('view')==='summary'?first:
        originals.find((p:Record<string,any>)=>p.page.offset===Number(u.searchParams.get('offset'))));
    });
    const api=createCycleCropReplayApi(request),summaries:unknown[]=[];
    const iterator=api.cycleCropPages(selection,kind,{limit:kind==='samples'?7:2,onSummary:s=>summaries.push(s)});
    let result;for(;;){const next=await iterator.next();if(next.done){result=next.value;break;}seen.push(next.value);}
    expect(seen).toEqual(originals);expect(summaries).toEqual([first]);expect(maxActive).toBe(1);
    expect(result).toEqual({kind,count:kind==='samples'?27:5,total:kind==='samples'?27:5,complete:true});
    expect(calls).toHaveLength(originals.length+1);expect(calls[0]!.searchParams.has('offset')).toBe(false);
    expect(calls[0]!.searchParams.has('limit')).toBe(false);
    for(const call of request.mock.calls)expect(call.slice(1,6)).toEqual(['GET',undefined,200,2*1024*1024,30_000]);
  });
  it('uses the current Bearer transport and canonical single-page queries',async ()=>{
    const token='own-synthetic-cycle-client-only',fetcher=vi.fn<typeof fetch>().mockResolvedValue(
      new Response(JSON.stringify(samplePage()),{headers:{'content-type':'application/json'}}));
    const p=samplePage();const result=await createApi(token,fetcher).cycleCropPage(selection,
      {kind:'samples',offset:p.page.offset,limit:p.page.limit},{summary:first});expect(result).toEqual(p);
    const [url,init]=fetcher.mock.calls[0]!,u=new URL(String(url),'https://localhost');
    expect(decodeURIComponent(u.pathname)).toBe('/v1/crop-cycle-research-results/'+selection.result_id);
    expect(Object.fromEntries(u.searchParams)).toEqual({...first.farm,view:'samples',offset:'0',limit:String(p.page.limit)});
    expect(init).toMatchObject({method:'GET',body:undefined,credentials:'omit',cache:'no-store',redirect:'error',
      headers:{authorization:'Bearer '+token}});
  });
  it('advances 513 byte-short pages without accumulating arrays or an old 16-request cap',async ()=>{
    const summary=structuredClone(first);summary.reference.sample_count=513;let calls=0;
    const request=async(path:string)=>{calls++;const u=new URL(path,'https://localhost');
      return u.searchParams.get('view')==='summary'?structuredClone(summary):
        shapedPage(summary,'samples',Number(u.searchParams.get('offset')),64,true);};
    const iterator=createCycleCropReplayApi(request).cycleCropPages(selection,'samples');let count=0;
    for(;;){const next=await iterator.next();if(next.done){expect(next.value).toEqual({kind:'samples',count:513,total:513,complete:true});break;}
      expect(next.value.page.records).toHaveLength(1);expect(next.value.page.offset).toBe(count++);}
    expect(count).toBe(513);expect(calls).toBe(514);
  });
  it.each(['samples','events'] as const)('ends a zero-output %s result using one empty page',async kind=>{
    const summary=structuredClone(first);summary.reference.sample_count=0;summary.reference.event_count=0;
    const request=vi.fn(async(path:string)=>new URL(path,'https://localhost').searchParams.get('view')==='summary'
      ?structuredClone(summary):shapedPage(summary,kind,0,kind==='samples'?64:8));
    const iterator=createCycleCropReplayApi(request).cycleCropPages(selection,kind);
    const firstPage=await iterator.next();expect(firstPage.done).toBe(false);
    if(!firstPage.done)expect(firstPage.value.page.records).toEqual([]);
    expect(await iterator.next()).toEqual({done:true,value:{kind,count:0,total:0,complete:true}});
    expect(request).toHaveBeenCalledTimes(2);
  });
  it('accepts the maximum count and terminal empty offset without claiming a maximum crop calculation',async ()=>{
    const summary=structuredClone(first);summary.reference.sample_count=131072;
    const request=vi.fn(async()=>shapedPage(summary,'samples',131072));
    const page=await createCycleCropReplayApi(request).cycleCropPage(selection,
      {kind:'samples',offset:131072,limit:64},{summary});expect(page.page.records).toEqual([]);
    expect(page.page.next_offset).toBeNull();expect(request).toHaveBeenCalledTimes(1);
  });
  it.each(['head_sha256','payload_sha256','header_sha256','context_sha256','input_root_sha256','farm_sha256',
    'source_binding_sha256','notice_sha256','storage_bytes','sample_count','recorded_at','study_id','revision','floor_area',
    'kind','offset','limit','future','duplicate'])('rejects %s drift on a later page without completing',async fault=>{
      const summary=structuredClone(first);summary.reference.sample_count=3;let calls=0;
      const request=async(path:string)=>{
        const u=new URL(path,'https://localhost');calls++;
        if(u.searchParams.get('view')==='summary')return structuredClone(summary);
        const p=shapedPage(summary,'samples',Number(u.searchParams.get('offset')),2,true);
        if(calls===3){
          if(fault.endsWith('_sha256'))p.reference[fault]='a'.repeat(64);
          if(fault==='storage_bytes')p.reference.storage_bytes++;if(fault==='sample_count'){p.reference.sample_count++;p.page.total++;}
          if(fault==='recorded_at')p.recorded_at='2026-10-06T00:00:00Z';if(fault==='study_id')p.study_id='other';
          if(fault==='revision')p.revision='other';if(fault==='floor_area')p.reference.floor_area.value='101';
          if(fault==='kind')p.page.kind='events';if(fault==='offset')p.page.offset=0;
          if(fault==='limit')p.page.limit=3;if(fault==='future')p.page.records[0].at='2028-01-01T00:00:00Z';
          if(fault==='duplicate')p.page.records[0].at=stamp(0);
        }return p;
      };
      const iterator=createCycleCropReplayApi(request).cycleCropPages(selection,'samples',{limit:2});
      expect((await iterator.next()).done).toBe(false);await expect(iterator.next()).rejects.toBeInstanceOf(ApiError);
      expect(calls).toBe(3);
    });
  it.each(['lookup','query','summary','aborted'] as const)('rejects %s change during the full response',async change=>{
    const selected={...selection},query={kind:'samples' as const,offset:0,limit:7},summary=structuredClone(first),controller=new AbortController();
    const request=vi.fn(async()=>{
      if(change==='lookup')selected.result_id='crop-cycle-result-v1:'+'a'.repeat(64);
      if(change==='query')query.offset=7;if(change==='summary')summary.reference.floor_area.value='101';
      if(change==='aborted')controller.abort();return samplePage();});
    await expect(createCycleCropReplayApi(request).cycleCropPage(selected,query,{summary,signal:controller.signal}))
      .rejects.toMatchObject({code:change==='aborted'?'request_canceled':'response_rejected'});
    expect(request).toHaveBeenCalledTimes(1);
  });
  it.each(['id','unknown_query','offset','fraction','event_limit','summary_query','options'] as const)
    ('rejects invalid %s before network',async fault=>{
      const selected={...selection},query:Record<string,any>={kind:'samples',offset:0,limit:64};
      if(fault==='id')selected.result_id='crop-result-v3:'+'a'.repeat(64);if(fault==='unknown_query')query.tenant='x';
      if(fault==='offset')query.offset=131073;if(fault==='fraction')query.offset=0.5;
      if(fault==='event_limit'){query.kind='events';query.limit=9;}if(fault==='summary_query')query.kind='summary';
      const request=vi.fn(async()=>samplePage()),api=createCycleCropReplayApi(request);
      await expect(api.cycleCropPage(selected,query as any,fault==='options'?{tenant:'x'} as any:{})).rejects.toBeInstanceOf(ApiError);
      expect(request).not.toHaveBeenCalled();
    });
  it('stops after rights refusal and passes no stale rows from that request',async ()=>{
    let calls=0;const request=async()=>{if(++calls===1)return structuredClone(first);throw new ApiError('forbidden',403);};
    const iterator=createCycleCropReplayApi(request).cycleCropPages(selection,'samples');
    await expect(iterator.next()).rejects.toMatchObject({code:'forbidden',status:403});expect(calls).toBe(2);
  });
  it('prevents overlapping HTTP requests and releases the owned request after failure',async ()=>{
    let release!:()=>void;const blocked=new Promise<void>(r=>{release=r;});
    const request=vi.fn(async()=>{await blocked;return structuredClone(first);}),api=createCycleCropReplayApi(request);
    const original=api.cycleCropSummary(selection);await expect(api.cycleCropSummary(selection)).rejects.toBeInstanceOf(ApiError);
    expect(request).toHaveBeenCalledTimes(1);release();await original;
    expect(await api.cycleCropSummary(selection)).toEqual(first);expect(request).toHaveBeenCalledTimes(2);
  });
  it('does not issue the next request until the consumer advances, nor complete after return()',async ()=>{
    const request=vi.fn(async(path:string)=>new URL(path,'https://localhost').searchParams.get('view')==='summary'?first:samplePage());
    const iterator=createCycleCropReplayApi(request).cycleCropPages(selection,'samples',{limit:7});
    expect((await iterator.next()).done).toBe(false);expect(request).toHaveBeenCalledTimes(2);
    await Promise.resolve();expect(request).toHaveBeenCalledTimes(2);
    expect((await iterator.return(undefined)).value).toBeUndefined();expect(request).toHaveBeenCalledTimes(2);
  });
});

describe('cycle holds and cancellation',()=>{
  function held(){
    const p=structuredClone(first),row=samplePage().page.records[0];p.reference.status='hold';p.reference.steps=0;
    p.reference.sample_count=1;p.summary.status='hold';
    p.summary.hold={reason_code:'NUMERIC_HOLD',at:stamp(1).replace('Z','.000001Z'),phase:'rk4-k2',
      time_meaning:'solver_evaluation_time',last_confirmed:{...row,phase:'boundary'}};return p;
  }
  it('keeps actual empty-hold diagnostics separate and fractional confirmed past without injecting a frame',async ()=>{
    const p=held();expect(decodeCycleCropResponse(p,selection)).toEqual(p);
    expect(p.summary.hold.at).toBe(stamp(1).replace('Z','.000001Z'));
    const empty=emptyHeld();expect(decodeCycleCropResponse(empty,lookup(empty))).toEqual(empty);
    expect(empty.summary.hold.last_confirmed).toBeNull();expect(empty.reference.sample_count).toBe(0);
    let count=0;const request=async(path:string)=>new URL(path,'https://localhost').searchParams.get('view')==='summary'?p:shapedPage(p,'samples');
    for await(const page of createCycleCropReplayApi(request).cycleCropPages(selection,'samples'))count+=page.page.records.length;
    expect(count).toBe(1);expect(p.summary.hold.last_confirmed.phase).toBe('boundary');
  });
  it.each(['missing','reason','phase','time','invalid_date','past','future','confirmed_future','confirmed_phase','confirmed_balance'])
    ('rejects invalid %s hold diagnostics',fault=>{
      const p=held(),h=p.summary.hold;
      if(fault==='missing')p.summary.hold=null;if(fault==='reason')h.reason_code='AUTO_HARVEST';
      if(fault==='phase')h.phase='completed';if(fault==='time')h.time_meaning='harvest';
      if(fault==='invalid_date')h.at='2026-02-30T00:00:00Z';if(fault==='past')h.at='2026-09-30T00:00:00Z';
      if(fault==='future')h.at='2028-01-01T00:00:00Z';if(fault==='confirmed_future')h.last_confirmed.at=stamp(2);
      if(fault==='confirmed_phase')h.last_confirmed.phase='rk4-k2';
      if(fault==='confirmed_balance')h.last_confirmed.number_residual.value=h.last_confirmed.number_residual_budget.value+1;
      expect(()=>decodeCycleCropResponse(p,selection)).toThrow(ApiError);
    });
  it.each(['samples','events'] as const)('validates hold time against %s using the same summary',async kind=>{
    const p=held();p.reference.event_count=1;const data=shapedPage(p,kind,0,kind==='samples'?64:8);
    data.page.records[0].at=stamp(2);
    const request=vi.fn(async()=>data);
    await expect(createCycleCropReplayApi(request).cycleCropPage(selection,
      {kind,offset:0,limit:kind==='samples'?64:8},{summary:p})).rejects.toBeInstanceOf(ApiError);
  });
  it('allows an event at the exact hold clock but rejects a sample at that clock',async ()=>{
    const p=held();p.summary.hold.at=stamp(1);p.reference.event_count=1;
    const event=shapedPage(p,'events',0,8);event.page.records[0].at=stamp(1);
    expect(await createCycleCropReplayApi(async()=>event).cycleCropPage(selection,{kind:'events',offset:0,limit:8},{summary:p})).toEqual(event);
    const sample=shapedPage(p,'samples');sample.page.records[0].at=stamp(1);
    await expect(createCycleCropReplayApi(async()=>sample).cycleCropPage(selection,{kind:'samples',offset:0,limit:64},{summary:p}))
      .rejects.toBeInstanceOf(ApiError);
  });
  it('does not request after cancellation or changed selection while a page is yielded',async ()=>{
    for(const change of ['cancel','selection','summary']){
      const selected={...selection},controller=new AbortController();let summary:Record<string,any>|null=null;
      const request=vi.fn(async(path:string)=>new URL(path,'https://localhost').searchParams.get('view')==='summary'?structuredClone(first):samplePage());
      const iterator=createCycleCropReplayApi(request).cycleCropPages(selected,'samples',
        {signal:controller.signal,limit:7,onSummary:s=>{summary=s;}});
      await iterator.next();
      if(change==='cancel')controller.abort();if(change==='selection')selected.crop_id='changed';
      if(change==='summary')summary!.reference.head_sha256='a'.repeat(64);
      await expect(iterator.next()).rejects.toMatchObject({code:change==='cancel'?'request_canceled':'response_rejected'});
      expect(request).toHaveBeenCalledTimes(2);
    }
  });
  it('rejects already canceled reads and callback selection changes without another request',async ()=>{
    const controller=new AbortController();controller.abort();const request=vi.fn(async()=>structuredClone(first));
    await expect(createCycleCropReplayApi(request).cycleCropSummary(selection,controller.signal)).rejects.toMatchObject({code:'request_canceled'});
    expect(request).not.toHaveBeenCalled();const selected={...selection};
    const iterator=createCycleCropReplayApi(request).cycleCropPages(selected,'samples',{onSummary:()=>{selected.crop_id='changed';}});
    await expect(iterator.next()).rejects.toBeInstanceOf(ApiError);expect(request).toHaveBeenCalledTimes(1);
  });
  it('releases a failed HTTP request and rejects wrong response views',async ()=>{
    const request=vi.fn().mockRejectedValueOnce(new ApiError('server_unavailable',503)).mockResolvedValueOnce(first);
    const api=createCycleCropReplayApi(request);
    await expect(api.cycleCropSummary(selection)).rejects.toMatchObject({code:'server_unavailable'});
    expect(await api.cycleCropSummary(selection)).toEqual(first);
    await expect(createCycleCropReplayApi(async()=>samplePage()).cycleCropSummary(selection)).rejects.toBeInstanceOf(ApiError);
    await expect(createCycleCropReplayApi(async()=>first).cycleCropPage(selection,{kind:'samples',offset:0,limit:64}))
      .rejects.toBeInstanceOf(ApiError);
  });
});
