import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { ApiError,need,object } from './api-validation';
import { createCalculationCycleCropReplayApi,decodeCalculationCycleCropResponse,validCalculationCycleCropLookup,
  type CalculationCycleCropResponse } from './calculationCycleCropReplay';
import { createCycleCropReplayApi,decodeCycleCropResponse,validCycleCropLookup,type CycleCropResponse } from './cycleCropReplay';
import { createCycleCropWindow } from './cycleCropWindow';

type Case='long'|'short'|'past'|'empty'|'fractional'|'zero';
const fixture:Record<Case,unknown[]>=JSON.parse(readFileSync(new URL('../e2e/calculation-cycle-crop-prefix-recorded-responses.json',import.meta.url),'utf8'));
function lookup(raw:unknown){
  need(object(raw) && object(raw.farm));const pick={...raw.farm,result_id:raw.result_id};
  need(validCalculationCycleCropLookup(pick));return pick;
}
function responses(name:Case){const rows=fixture[name].map(raw=>decodeCalculationCycleCropResponse(raw,lookup(raw)));
  const summary=rows[0];need(summary?.summary!==null && summary!==undefined);
  return {summary,rows:rows.filter(r=>r.result_id===summary.result_id)};
}
const originalFixture:{long:unknown[]}=JSON.parse(readFileSync(new URL('../e2e/cycle-crop-recorded-responses.json',import.meta.url),'utf8'));
const originalRows=originalFixture.long.map(raw=>{
  need(object(raw) && object(raw.farm));const pick={...raw.farm,result_id:raw.result_id};need(validCycleCropLookup(pick));
  return decodeCycleCropResponse(raw,pick);
});
function recorded<T extends CalculationCycleCropResponse|CycleCropResponse>(rows:readonly T[],options:{
  delay?:(url:URL)=>Promise<void>;change?:(value:T,url:URL)=>unknown}={}){
  const summary=rows[0];need(summary && summary.summary!==null);
  const calls:URL[]=[],request=vi.fn(async(path:string)=>{
    const u=new URL(path,'https://localhost');calls.push(u);await options.delay?.(u);
    const kind=u.searchParams.get('view'),offset=Number(u.searchParams.get('offset'));
    const raw=kind==='summary'?summary:rows.find(r=>r.page?.kind===kind && r.page.offset===offset);need(raw);
    // Echoing a different request limit is a metadata-only shape test; raw numerical rows are unchanged.
    const value=structuredClone(raw.page?{...raw,page:{...raw.page,limit:Number(u.searchParams.get('limit'))}}:raw);
    return options.change?options.change(value,u):value;
  });return {request,calls};
}
function calculation(name:Case='long',options:Parameters<typeof recorded<CalculationCycleCropResponse>>[1]={}){
  const data=responses(name),r=recorded(data.rows,options);
  return {...r,...data,api:createCalculationCycleCropReplayApi(r.request),lookup:lookup(data.summary)};
}
function original(options:Parameters<typeof recorded<CycleCropResponse>>[1]={}){
  const r=recorded(originalRows,options),summary=originalRows[0];need(summary && summary.summary!==null);
  return {...r,summary,api:createCycleCropReplayApi(r.request),lookup:{result_id:summary.result_id,...summary.farm}};
}

describe('verified calculation current window',()=>{
  it('preserves full verified provenance and original selected UTC',async()=>{
    const r=calculation(),notify=vi.fn(),window=createCycleCropWindow(notify,{sample_limit:7,event_limit:2});
    await window.openCalculation(r.api,r.lookup);const state=window.snapshot();
    expect(state.phase).toBe('ready');expect(state.summary).toEqual(r.summary);
    expect(state.summary?.schema_version).toBe('crop-cycle-calculation-replay-v1');
    expect(state.sample_page).toEqual(r.rows[1]);expect(state.selected?.reference).toEqual(r.summary.reference);
    expect(state.selected?.result_id).toBe(r.lookup.result_id);expect(state.selected?.sample).toEqual(r.rows[1]?.page?.records[0]);
    expect(state.range).toMatchObject({offset:0,count:7,total:27,last_index:6,next_offset:7,partial:true});
    window.select(6);expect(window.snapshot().selected).toMatchObject({index:6,sample:r.rows[1]?.page?.records[6]});
    expect(r.request).toHaveBeenCalledTimes(2);expect(notify).toHaveBeenCalledTimes(3);
  });
  it.each(['long','short','past','empty','fractional','zero'] as const)('keeps the actual %s result and hold diagnostics separate',async name=>{
    const r=calculation(name),window=createCycleCropWindow(()=>{},{sample_limit:7,event_limit:2});
    await window.openCalculation(r.api,r.lookup);const state=window.snapshot();
    expect(state.phase).toBe('ready');expect(state.summary).toEqual(r.summary);
    const samples=r.rows.find(row=>row.page?.kind==='samples' && row.page.offset===0);
    expect(state.sample_page).toEqual(samples);expect(state.range?.total).toBe(r.summary.reference.sample_count);
    if(state.selected){
      expect(state.selected.sample).toEqual(samples?.page?.records[0]);expect(state.selected.index).toBe(0);
      if(r.summary.summary.hold)expect(Date.parse(state.selected.sample.at)).toBeLessThan(Date.parse(r.summary.summary.hold.at));
    }else expect(state.range?.count).toBe(0);
    await window.showEvents();expect(window.snapshot().selected).toBeNull();expect(window.snapshot().sample_page).toBeNull();
    expect(window.snapshot().event_page).toEqual(r.rows.find(row=>row.page?.kind==='events' && row.page.offset===0));
    expect(window.snapshot().summary).toEqual(r.summary);
  });
  it('follows byte-short offsets and retains only the current original sample or event page',async()=>{
    const r=calculation(),window=createCycleCropWindow(()=>{});await window.openCalculation(r.api,r.lookup);
    expect(r.calls[1]?.searchParams.get('limit')).toBe('64');expect(window.snapshot().range?.next_offset).toBe(7);
    await window.next('samples');expect(window.snapshot().range?.offset).toBe(7);expect(window.snapshot().selected?.index).toBe(7);
    window.select(6);expect(window.snapshot().selected?.index).toBe(13);
    expect(window.snapshot().selected?.sample).toEqual(r.rows.find(row=>row.page?.kind==='samples' && row.page.offset===7)?.page?.records[6]);
    await window.next('samples');await window.previous('samples');expect(window.snapshot().range?.offset).toBe(7);
    await window.showEvents();expect(window.snapshot().range).toMatchObject({offset:0,count:2,total:5,next_offset:2});
    expect(r.calls.at(-1)?.searchParams.get('limit')).toBe('8');expect(window.snapshot().sample_page).toBeNull();
    await window.next('events');await window.next('events');expect(window.snapshot().range).toMatchObject({offset:4,count:1,last_index:4,next_offset:null});
    await window.previous('events');expect(window.snapshot().range?.offset).toBe(2);
    await window.showSamples();expect(window.snapshot().range?.offset).toBe(7);expect(window.snapshot().event_page).toBeNull();
    await window.next('samples');await window.next('samples');expect(window.snapshot().range).toMatchObject({offset:21,count:6,total:27,last_index:26,next_offset:null});
    expect(window.snapshot().can_next).toBe(false);const calls=r.calls.length;
    expect(()=>window.next('samples')).toThrow(ApiError);expect(()=>window.select(6)).toThrow(ApiError);
    expect(()=>window.select(-1)).toThrow(ApiError);expect(()=>window.select(0.5)).toThrow(ApiError);
    expect(()=>window.previous('events')).toThrow(ApiError);expect(r.calls).toHaveLength(calls);
    expect(r.calls.slice(2).map(u=>u.searchParams.get('offset'))).toEqual(['7','14','7','0','2','4','2','7','14','21']);
  });
  it('seeks an original sample directly from events, preserving identity and bounded history',async()=>{
    const r=calculation(),window=createCycleCropWindow(()=>{},{sample_limit:7,event_limit:2});
    await window.openCalculation(r.api,r.lookup);await window.showEvents();
    await window.seekSample(21);const result=window.snapshot();
    expect(result.range).toMatchObject({kind:'samples',offset:21,count:6,total:27,next_offset:null});
    expect(result.summary).toEqual(r.summary);expect(result.selected?.index).toBe(21);
    expect(result.selected?.sample).toEqual(r.rows.find(row=>row.page?.kind==='samples'&&row.page.offset===21)?.page?.records[0]);
    expect(result.event_page).toBeNull();expect(r.calls.at(-1)?.searchParams.get('limit')).toBe('7');
    await window.previous('samples');expect(window.snapshot().selected?.index).toBe(0);
    await window.seekSample(7);await window.seekSample(7);await window.previous('samples');
    expect(window.snapshot().selected?.index).toBe(0);
    const calls=r.calls.length;
    for(const index of [-1,27,0.5,NaN,Infinity])expect(()=>window.seekSample(index)).toThrow(ApiError);
    expect(r.calls).toHaveLength(calls);expect(window.snapshot().summary).toEqual(r.summary);
  });
  it('clears selected quantities on a seek rights refusal and suppresses a canceled late seek',async()=>{
    let fail=false,block=false,release!:()=>void,entered!:()=>void;
    const waiting=new Promise<void>(resolve=>{release=resolve;}),started=new Promise<void>(resolve=>{entered=resolve;});
    const r=calculation('long',{delay:async u=>{if(block&&u.searchParams.get('offset')==='21'){entered();await waiting;}},
      change:value=>{if(fail)throw new ApiError('forbidden',403);return value;}});
    const window=createCycleCropWindow(()=>{});await window.openCalculation(r.api,r.lookup);fail=true;
    const denied=window.seekSample(21);expect(window.snapshot().selected).toBeNull();await denied;
    expect(window.snapshot()).toMatchObject({phase:'error',summary:null,sample_page:null,event_page:null,selected:null});
    expect(window.snapshot().error?.code).toBe('forbidden');
    fail=false;await window.openCalculation(r.api,r.lookup);block=true;
    const seeking=window.seekSample(21);await started;const settling=window.cancel();
    expect(window.snapshot()).toMatchObject({phase:'idle',summary:null,selected:null});
    release();await Promise.all([seeking,settling]);expect(window.snapshot().phase).toBe('idle');
    expect(window.snapshot().selected).toBeNull();expect(()=>window.seekSample(0)).toThrow(ApiError);
  });
  it.each(['validation','recorded','rights','server'] as const)('clears old quantities and provenance on %s refusal',async fault=>{
    let fail=false;const r=calculation('long',{change:value=>{
      if(!fail)return value;
      if(fault==='rights')throw new ApiError('forbidden',403);
      if(fault==='server')throw new ApiError('server_unavailable',503);
      if(fault==='recorded')return {...value,recorded_at:'2026-10-08T00:00:00Z'};
      return {...value,reference:{...value.reference,input_validation:{...value.reference.input_validation,evidence_sha256:'a'.repeat(64)}}};
    }}),window=createCycleCropWindow(()=>{});await window.openCalculation(r.api,r.lookup);
    fail=true;const moving=window.next('samples');
    expect(window.snapshot()).toMatchObject({phase:'loading',summary:null,sample_page:null,event_page:null,selected:null});await moving;
    expect(window.snapshot()).toMatchObject({phase:'error',summary:null,sample_page:null,event_page:null,range:null,selected:null,can_next:false,can_previous:false});
    expect(window.snapshot().error?.code).toBe(fault==='rights'?'forbidden':fault==='server'?'server_unavailable':'response_rejected');
    expect(()=>window.select(0)).toThrow(ApiError);expect(()=>window.showSamples()).toThrow(ApiError);
    fail=false;await window.openCalculation(r.api,r.lookup);expect(window.snapshot().range?.offset).toBe(0);
  });
  it('rejects source-specific IDs and invalid bounds before any request; owns a lookup copy',async()=>{
    const r=calculation(),old=original(),window=createCycleCropWindow(()=>{}),pick={...r.lookup};
    expect(()=>window.openCalculation(r.api,old.lookup)).toThrow(ApiError);
    expect(()=>window.open(old.api,r.lookup)).toThrow(ApiError);
    expect(()=>createCycleCropWindow(()=>{},{sample_limit:65,event_limit:8})).toThrow(ApiError);
    expect(()=>createCycleCropWindow(()=>{},{sample_limit:64,event_limit:9})).toThrow(ApiError);
    expect(r.request).not.toHaveBeenCalled();expect(old.request).not.toHaveBeenCalled();
    const opening=window.openCalculation(r.api,pick);pick.result_id='changed';await opening;
    expect(window.snapshot().selected?.result_id).toBe(r.lookup.result_id);
  });
});

describe('verified calculation source ownership and settlement',()=>{
  it.each(['original-to-calculation','calculation-to-original','calculation-to-calculation'] as const)
    ('waits for an aborted response to settle on %s',async direction=>{
      let release!:()=>void,entered!:()=>void;
      const blocked=new Promise<void>(resolve=>{release=resolve;}),started=new Promise<void>(resolve=>{entered=resolve;});
      let active=0,peak=0;
      const waiting=async()=>{active++;peak=Math.max(peak,active);entered();await blocked;active--;};
      const immediate=async()=>{active++;peak=Math.max(peak,active);await Promise.resolve();active--;};
      const first=calculation('long',{delay:waiting}),firstOld=original({delay:waiting});
      const second=calculation('long',{delay:immediate,change:value=>({...value,result_id:'crop-cycle-verified-result-v1:'+'a'.repeat(64)})});
      const secondOld=original({delay:immediate}),window=createCycleCropWindow(()=>{});
      const running=direction==='original-to-calculation'?window.open(firstOld.api,firstOld.lookup):window.openCalculation(first.api,first.lookup);
      await started;const current=direction==='calculation-to-original'?window.open(secondOld.api,secondOld.lookup):
        window.openCalculation(second.api,{...second.lookup,result_id:'crop-cycle-verified-result-v1:'+'a'.repeat(64)});
      expect(window.snapshot()).toMatchObject({phase:'loading',summary:null,selected:null,sample_page:null,event_page:null});
      await Promise.resolve();await Promise.resolve();expect(second.request).not.toHaveBeenCalled();expect(secondOld.request).not.toHaveBeenCalled();
      release();await Promise.all([running,current]);expect(peak).toBe(1);
      expect(first.request.mock.calls.length+firstOld.request.mock.calls.length).toBe(1);
      const result=window.snapshot();expect(result.phase).toBe('ready');
      if(direction==='calculation-to-original'){
        expect(result.summary).toEqual(secondOld.summary);expect(secondOld.request).toHaveBeenCalledTimes(2);expect(second.request).not.toHaveBeenCalled();
      }else{
        expect(result.summary).toEqual({...second.summary,result_id:'crop-cycle-verified-result-v1:'+'a'.repeat(64)});
        expect(second.request).toHaveBeenCalledTimes(2);expect(secondOld.request).not.toHaveBeenCalled();
      }
    });
  it('starts only the latest queued source and supports a reentrant account change',async()=>{
    const one=calculation(),two=original(),three=calculation('past');let latest:Promise<void>|undefined,switched=false;
    const window=createCycleCropWindow(state=>{
      if(state.phase==='loading' && !switched){switched=true;latest=window.open(two.api,two.lookup);}
    });
    const first=window.openCalculation(one.api,one.lookup),last=window.openCalculation(three.api,three.lookup);
    await Promise.all([first,latest,last]);expect(one.request).not.toHaveBeenCalled();expect(two.request).not.toHaveBeenCalled();
    expect(three.request).toHaveBeenCalledTimes(2);expect(window.snapshot().summary).toEqual(three.summary);
  });
  it.each(['cancel','dispose'] as const)('clears during a sample page on %s and waits without late publication',async action=>{
    let release!:()=>void,entered!:()=>void;
    const blocked=new Promise<void>(resolve=>{release=resolve;}),started=new Promise<void>(resolve=>{entered=resolve;});
    const r=calculation('long',{delay:u=>{if(u.searchParams.get('offset')==='7'){entered();return blocked;}return Promise.resolve();}});
    const notify=vi.fn(),window=createCycleCropWindow(notify);await window.openCalculation(r.api,r.lookup);
    const moving=window.next('samples');await started;const settling=window[action]();let ended=false;void settling.then(()=>{ended=true;});
    expect(window.snapshot()).toMatchObject({phase:action==='cancel'?'idle':'disposed',summary:null,range:null,selected:null,sample_page:null,event_page:null});
    const notifications=notify.mock.calls.length;await Promise.resolve();expect(ended).toBe(false);
    release();await Promise.all([moving,settling]);expect(ended).toBe(true);expect(notify).toHaveBeenCalledTimes(notifications);expect(r.request).toHaveBeenCalledTimes(3);
    if(action==='dispose'){
      expect(()=>window.openCalculation(r.api,r.lookup)).toThrow(ApiError);expect(()=>window.open(original().api,original().lookup)).toThrow(ApiError);
      expect(()=>window.showSamples()).toThrow(ApiError);expect(()=>window.select(0)).toThrow(ApiError);expect(r.request).toHaveBeenCalledTimes(3);
    }else{
      await window.openCalculation(r.api,r.lookup);expect(window.snapshot().phase).toBe('ready');expect(window.snapshot().selected?.index).toBe(0);
    }
  });
});
