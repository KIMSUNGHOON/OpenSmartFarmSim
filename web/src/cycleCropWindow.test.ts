import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createCycleCropReplayApi,type CycleCropLookup } from './cycleCropReplay';
import { createCycleCropWindow } from './cycleCropWindow';
import { ApiError } from './api-validation';

const fixture=JSON.parse(readFileSync(new URL('../e2e/cycle-crop-recorded-responses.json',import.meta.url),'utf8'));
const summary=fixture.long[0],lookup:CycleCropLookup={result_id:summary.result_id,...summary.farm};
function recordedApi(options:{delay?:()=>Promise<void>;change?:(p:Record<string,any>)=>void}={}){
  const calls:URL[]=[],request=vi.fn(async(path:string)=>{
    const u=new URL(path,'https://localhost');calls.push(u);await options.delay?.();
    const kind=u.searchParams.get('view'),offset=Number(u.searchParams.get('offset'));
    const p=structuredClone(kind==='summary'?summary:fixture.long.find((p:Record<string,any>)=>p.page?.kind===kind && p.page.offset===offset));
    if(p?.page)p.page.limit=kind==='samples'?64:8;
    options.change?.(p);return p;
  });return {api:createCycleCropReplayApi(request),request,calls};
}

describe('cycle current original window',()=>{
  it('preserves the original selected UTC and partial range, with no generated endpoints',async ()=>{
    const recorded=recordedApi(),updates:unknown[]=[],window=createCycleCropWindow(s=>updates.push(s));
    expect(window.snapshot().phase).toBe('idle');await window.open(recorded.api,lookup);
    const state=window.snapshot();expect(state.phase).toBe('ready');expect(state.summary).toEqual(summary);
    expect(state.sample_page?.page.records).toEqual(fixture.long[1].page.records);
    expect(state.range).toMatchObject({kind:'samples',offset:0,count:7,total:27,next_offset:7,partial:true,
      first_utc:fixture.long[1].page.records[0].at,last_utc:fixture.long[1].page.records[6].at,last_index:6});
    expect(state.selected?.sample).toEqual(fixture.long[1].page.records[0]);expect(state.selected?.index).toBe(0);
    window.select(6);expect(window.snapshot().selected?.sample.at).toBe(fixture.long[1].page.records[6].at);
    expect(window.snapshot().selected?.result_id).toBe(summary.result_id);
    expect(recorded.request).toHaveBeenCalledTimes(2);expect(updates).toHaveLength(3);
  });
  it('uses byte-short next and actually visited previous offsets without old arrays',async ()=>{
    const recorded=recordedApi(),window=createCycleCropWindow(()=>{});await window.open(recorded.api,lookup);
    await window.next('samples');expect(window.snapshot().range?.offset).toBe(7);
    expect(window.snapshot().sample_page?.page.records).toEqual(fixture.long[2].page.records);
    await window.next('samples');expect(window.snapshot().range?.offset).toBe(14);
    await window.previous('samples');expect(window.snapshot().range?.offset).toBe(7);
    expect(window.snapshot().selected?.index).toBe(7);expect(window.snapshot().can_previous).toBe(true);
    await window.previous('samples');expect(window.snapshot().can_previous).toBe(false);
    expect(recorded.calls.slice(2).map(u=>u.searchParams.get('offset'))).toEqual(['7','14','7','0']);
    expect(window.snapshot().event_page).toBeNull();
  });
  it('clears selection on every request and separates event windows from sample frames',async ()=>{
    const recorded=recordedApi(),window=createCycleCropWindow(()=>{});await window.open(recorded.api,lookup);
    const eventLoad=window.showEvents();expect(window.snapshot()).toMatchObject({phase:'loading',sample_page:null,event_page:null,selected:null});
    await eventLoad;expect(window.snapshot().range).toMatchObject({kind:'events',offset:0,count:2,total:5,partial:true});
    expect(window.snapshot().selected).toBeNull();expect(window.snapshot().sample_page).toBeNull();
    await window.next('events');expect(window.snapshot().range?.offset).toBe(2);await window.previous('events');
    expect(window.snapshot().range?.offset).toBe(0);await window.showSamples();
    expect(window.snapshot().selected?.sample).toEqual(fixture.long[1].page.records[0]);
    expect(window.snapshot().event_page).toBeNull();
  });
  it('keeps final-window count and visited prior offsets without declaring all pages present',async ()=>{
    const recorded=recordedApi(),window=createCycleCropWindow(()=>{});await window.open(recorded.api,lookup);
    await window.next('samples');await window.next('samples');await window.next('samples');
    expect(window.snapshot().range).toMatchObject({offset:21,count:6,total:27,last_index:26,next_offset:null,partial:true});
    expect(window.snapshot().can_next).toBe(false);expect(window.snapshot().can_previous).toBe(true);
    expect(()=>window.next('samples')).toThrow(ApiError);expect(()=>window.select(6)).toThrow(ApiError);
    expect(()=>window.select(-1)).toThrow(ApiError);expect(()=>window.select(0.5)).toThrow(ApiError);
    expect(()=>window.previous('events')).toThrow(ApiError);expect(recorded.request).toHaveBeenCalledTimes(5);
  });
  it.each(['head','recorded','hold_time','forbidden','server'])('clears all old numeric data on %s refusal',async failure=>{
    let calls=0;const recorded=recordedApi({change:p=>{
      if(++calls===3){
        if(failure==='head')p.reference.head_sha256='a'.repeat(64);
        if(failure==='recorded')p.recorded_at='2026-10-07T00:00:00Z';
        if(failure==='hold_time')p.page.records[0].at='2028-01-01T00:00:00Z';
        if(failure==='forbidden')throw new ApiError('forbidden',403);
        if(failure==='server')throw new ApiError('server_unavailable',503);
      }
    }}),window=createCycleCropWindow(()=>{});await window.open(recorded.api,lookup);await window.next('samples');
    expect(window.snapshot()).toMatchObject({phase:'error',summary:null,sample_page:null,event_page:null,range:null,selected:null});
    expect(window.snapshot().error?.code).toBe(failure==='forbidden'?'forbidden':failure==='server'?'server_unavailable':'response_rejected');
    expect(()=>window.select(0)).toThrow(ApiError);expect(()=>window.showSamples()).toThrow(ApiError);
    await window.open(recorded.api,lookup);expect(window.snapshot().range?.offset).toBe(0);
  });
  it('shows a completed empty output without a fabricated endpoint or selection',async ()=>{
    const p=structuredClone(summary);p.reference.sample_count=0;p.reference.event_count=0;
    const request=async(path:string)=>new URL(path,'https://localhost').searchParams.get('view')==='summary'?p:
      {...structuredClone(p),summary:null,page:{kind:'samples',offset:0,limit:64,total:0,next_offset:null,records:[]}};
    const window=createCycleCropWindow(()=>{});await window.open(createCycleCropReplayApi(request),lookup);
    expect(window.snapshot()).toMatchObject({phase:'ready',selected:null,can_next:false,can_previous:false,
      range:{count:0,total:0,first_utc:null,last_utc:null,last_index:null,partial:false}});
    expect(window.snapshot().summary?.reference.status).toBe('completed');
  });
  it('keeps actual empty hold diagnostics separate from an empty sample window',async ()=>{
    const hold=fixture.short.find((p:Record<string,any>)=>p.summary?.status==='hold');
    const request=async(path:string)=>{
      if(new URL(path,'https://localhost').searchParams.get('view')==='summary')return structuredClone(hold);
      const p=structuredClone(fixture.short.find((p:Record<string,any>)=>p.result_id===hold.result_id && p.page?.kind==='samples'));
      p.page.limit=64;return p;
    };
    const window=createCycleCropWindow(()=>{});await window.open(createCycleCropReplayApi(request),{result_id:hold.result_id,...hold.farm});
    expect(window.snapshot().summary?.summary.hold).toEqual(hold.summary.hold);
    expect(window.snapshot().sample_page?.page.records).toEqual([]);expect(window.snapshot().selected).toBeNull();
  });
  it('retains only the current raw page across many shape-only range moves',async ()=>{
    const recorded=recordedApi(),window=createCycleCropWindow(()=>{});await window.open(recorded.api,lookup);
    for(let i=0;i<40;i++){
      await window.next('samples');expect(window.snapshot().sample_page?.page.records.length).toBeLessThanOrEqual(64);
      expect(window.snapshot().event_page).toBeNull();await window.previous('samples');
    }
    expect(window.snapshot().range?.offset).toBe(0);expect(window.snapshot().sample_page?.page.records).toHaveLength(7);
  });
});

describe('cycle serialized selection and settlement',()=>{
  it('waits for an aborted full response to settle before a new account/ID starts HTTP',async ()=>{
    let release!:()=>void;const blocked=new Promise<void>(resolve=>{release=resolve;});
    let started!:()=>void;const entered=new Promise<void>(resolve=>{started=resolve;});
    let active=0,maxActive=0;const firstApi=createCycleCropReplayApi(async()=>{
      active++;maxActive=Math.max(active,maxActive);started();await blocked;active--;return structuredClone(summary);
    });
    const selected={...lookup,result_id:'crop-cycle-result-v1:'+'a'.repeat(64)};
    const second=recordedApi({change:p=>{p.result_id=selected.result_id;},delay:async()=>{
      active++;maxActive=Math.max(active,maxActive);await Promise.resolve();active--;
    }});
    const window=createCycleCropWindow(()=>{}),old=window.open(firstApi,lookup);
    await entered;expect(active).toBe(1);
    const newer=window.open(second.api,selected);expect(window.snapshot().selected).toBeNull();
    await Promise.resolve();await Promise.resolve();expect(second.request).not.toHaveBeenCalled();
    release();await Promise.all([old,newer]);expect(maxActive).toBe(1);
    expect(window.snapshot().selected?.result_id).toBe(selected.result_id);expect(second.request).toHaveBeenCalledTimes(2);
  });
  it('does not start a superseded queued selection, and accepts only the latest version',async ()=>{
    const first=recordedApi(),second=recordedApi(),window=createCycleCropWindow(()=>{});
    const old=window.open(first.api,lookup),newer=window.open(second.api,lookup);await Promise.all([old,newer]);
    expect(first.request).not.toHaveBeenCalled();expect(second.request).toHaveBeenCalledTimes(2);
    expect(window.snapshot().phase).toBe('ready');
  });
  it.each(['cancel','dispose'] as const)('clears synchronously on %s and rejects a late response',async action=>{
    let release!:()=>void;const blocked=new Promise<void>(resolve=>{release=resolve;});
    let started!:()=>void;const entered=new Promise<void>(resolve=>{started=resolve;});
    const recorded=recordedApi({delay:()=>{started();return blocked;}}),notify=vi.fn(),window=createCycleCropWindow(notify);
    const running=window.open(recorded.api,lookup);await entered;const settling=window[action]();
    expect(window.snapshot()).toMatchObject({phase:action==='cancel'?'idle':'disposed',selected:null,summary:null,sample_page:null});
    const updates=notify.mock.calls.length;let ended=false;settling.then(()=>{ended=true;});
    await Promise.resolve();expect(ended).toBe(false);release();await Promise.all([running,settling]);
    expect(ended).toBe(true);expect(notify).toHaveBeenCalledTimes(updates);expect(recorded.request).toHaveBeenCalledTimes(1);
    if(action==='dispose')expect(()=>window.open(recorded.api,lookup)).toThrow(ApiError);
  });
  it('does not publish an aborted page or keep its former selection',async ()=>{
    let calls=0,release!:()=>void;const blocked=new Promise<void>(resolve=>{release=resolve;});
    let started!:()=>void;const entered=new Promise<void>(resolve=>{started=resolve;});
    const recorded=recordedApi({delay:()=>{if(++calls===3){started();return blocked;}return Promise.resolve();}}),window=createCycleCropWindow(()=>{});
    await window.open(recorded.api,lookup);const moving=window.next('samples');await entered;
    const cancel=window.cancel();expect(window.snapshot().selected).toBeNull();release();await Promise.all([moving,cancel]);
    expect(window.snapshot().phase).toBe('idle');expect(recorded.request).toHaveBeenCalledTimes(3);
  });
  it('serializes a reentrant selection callback without overwriting the pending owner',async ()=>{
    const one=recordedApi(),two=recordedApi();let latest:Promise<void>|null=null,switched=false;
    const window=createCycleCropWindow(s=>{if(s.phase==='loading' && !switched){switched=true;latest=window.open(two.api,lookup);}});
    const old=window.open(one.api,lookup);await old;await latest;
    expect(one.request).not.toHaveBeenCalled();expect(two.request).toHaveBeenCalledTimes(2);expect(window.snapshot().phase).toBe('ready');
  });
  it('rejects invalid IDs/limits before any HTTP and preserves the selection after caller lookup mutation',async ()=>{
    const recorded=recordedApi(),window=createCycleCropWindow(()=>{}),selected={...lookup};
    expect(()=>window.open(recorded.api,{...lookup,result_id:'old'})).toThrow(ApiError);
    expect(()=>createCycleCropWindow(()=>{},{sample_limit:65,event_limit:8})).toThrow(ApiError);
    expect(()=>createCycleCropWindow(()=>{},{sample_limit:64,event_limit:9})).toThrow(ApiError);
    expect(recorded.request).not.toHaveBeenCalled();const opening=window.open(recorded.api,selected);
    selected.result_id='changed';await opening;expect(window.snapshot().selected?.result_id).toBe(lookup.result_id);
  });
});
