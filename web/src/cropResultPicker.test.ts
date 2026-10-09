import {readFileSync} from 'node:fs';
import {describe,it,expect,vi} from 'vitest';
import {ApiError} from './api-validation';
import type {AuthoredFarmSummary,AuthoredFarmCursor,AuthoredFarmPage} from './authored-farm-api';
import {decodeCropFarmSelection,type CropFarmRegistration} from './cropFarmSelection';
import {decodeCropCatalogPage,type CropCatalogQuery} from './cropResultCatalog';
import {createCropResultPicker,type CropResultPickerApi} from './cropResultPicker';

const catalog=JSON.parse(readFileSync(new URL('../e2e/crop-result-catalog-recorded-responses.json',import.meta.url),'utf8'));
const crops=JSON.parse(readFileSync(new URL('../e2e/crop-farm-selection-recorded-responses.json',import.meta.url),'utf8'));
const source=JSON.parse(catalog.bodies_raw_utf8.growth_max);
const records=[...source.items,...JSON.parse(catalog.bodies_raw_utf8.growth_tail).items];
const farm:AuthoredFarmSummary={scenario_id:source.farm.scenario_id,scenario_revision:source.farm.scenario_revision,
  scenario_sha256:source.farm.registration_sha256,farm_sha256:'a'.repeat(64),numeric_input_sha256:'b'.repeat(64),
  rights_sha256:'c'.repeat(64),registration_status:'registered_unpublished_inputs',intent_job:{
    job_id:'11111111-1111-4111-8111-111111111111',stage:'collection',state:'queued',attempt_count:0,max_attempts:3,
    created_at:'2026-10-01T00:00:00Z',updated_at:'2026-10-01T00:00:00Z',reason_code:null}};
function result(query:CropCatalogQuery){
  if(query.kind==='harvest_v1')return decodeCropCatalogPage(JSON.parse(catalog.bodies_raw_utf8.harvest),query);
  const index=query.before?records.findIndex(row=>row.result_id===query.before!.result_id)+1:0;
  const items=records.slice(index,index+10),last=items.at(-1);
  return decodeCropCatalogPage({...source,items,next_cursor:index+10<records.length?
    {recorded_at:last.recorded_at,result_id:last.result_id}:null},query);
}
function setup(){
  const api={
    authoredFarmCatalog:vi.fn(async(_cursor?:AuthoredFarmCursor):Promise<AuthoredFarmPage>=>({items:[structuredClone(farm)],next_cursor:null})),
    authoredFarm:vi.fn(async()=>structuredClone(farm)),
    cropFarmSelection:vi.fn(async(requested:CropFarmRegistration)=>decodeCropFarmSelection(JSON.parse(crops.bodies_raw_utf8.registered),requested)),
    cropResultCatalog:vi.fn(async(query:CropCatalogQuery)=>result(query)),
  } satisfies CropResultPickerApi;
  const changed=vi.fn(),picker=createCropResultPicker(api,changed);
  return {api,picker,changed};
}
async function registered(c=setup()){
  await c.picker.refreshFarms();await c.picker.chooseFarm(farm.intent_job.job_id);return c;
}
async function ready(c=setup()){
  await registered(c);await c.picker.chooseCrop(source.farm.crop_id);return c;
}
function gate(){
  let release!:()=>void,enter!:()=>void;
  const promise=new Promise<void>(resolve=>{release=resolve;}),entered=new Promise<void>(resolve=>{enter=resolve;});
  return {promise,release,enter,entered};
}

describe('stored crop result picker',()=>{
  it('starts without a request and rechecks a listed immutable registration before crop lookup',async()=>{
    const c=setup();expect(c.api.authoredFarmCatalog).not.toHaveBeenCalled();await registered(c);
    expect(c.api.authoredFarm).toHaveBeenCalledWith(farm.scenario_id,farm.scenario_revision);
    expect(c.picker.snapshot().farm).toEqual(farm);
    expect(c.picker.snapshot().crops?.items[0]?.origin).toBe('user');
    expect(c.api.cropResultCatalog).not.toHaveBeenCalled();
  });
  it('refuses a changed registration hash before reading crops',async()=>{
    const c=setup();c.api.authoredFarm.mockResolvedValue({...farm,scenario_sha256:'0'.repeat(64)});
    await registered(c);expect(c.picker.snapshot().phase).toBe('error');
    expect(c.api.cropFarmSelection).not.toHaveBeenCalled();expect(c.picker.snapshot().farms).toBeNull();
  });
  it('copies the exact verified growth ID and farm without reading or generating numerical output',async()=>{
    const c=await ready(),page=c.picker.snapshot().page!;c.picker.select(page.items[0]!.result_id);
    expect(c.picker.snapshot().selection).toEqual({kind:'calculation_cycle_v1',farm:source.farm,result_id:records[0].result_id});
    expect(c.api.cropResultCatalog).toHaveBeenCalledTimes(1);
  });
  it('copies the original harvest and verified parent IDs, including a stored hold',async()=>{
    const c=await ready();await c.picker.setKind('harvest_v1');const page=c.picker.snapshot().page!;
    expect(page.kind).toBe('harvest_v1');if(page.kind!=='harvest_v1')throw Error('wrong fixture');
    const item=page.items[0]!;c.picker.select(item.result_id);
    expect(c.picker.snapshot().selection).toEqual({kind:'harvest_v1',farm:page.farm,result_id:item.result_id,parent_result_id:item.parent_result_id});
    expect(item.row_count).toBe(JSON.parse(catalog.bodies_raw_utf8.harvest).items[0].row_count);
  });
  it('keeps an equivalent selected result stable and does not reload the same kind',async()=>{
    const c=await ready();c.picker.select(records[0].result_id);const selected=c.picker.snapshot().selection;
    c.picker.select(records[0].result_id);await c.picker.setKind('calculation_cycle_v1');
    expect(c.picker.snapshot().selection).toBe(selected);expect(c.api.cropResultCatalog).toHaveBeenCalledTimes(1);
  });
  it('refuses IDs outside the current visible farm/crop/result pages',async()=>{
    const c=await ready();
    expect(()=>c.picker.chooseFarm('foreign')).toThrow(ApiError);
    expect(()=>c.picker.chooseCrop('foreign')).toThrow(ApiError);
    expect(()=>c.picker.select('foreign')).toThrow(ApiError);expect(c.api.cropResultCatalog).toHaveBeenCalledTimes(1);
  });
  it('pages original metadata using exact cursors, clears replay, and reads previous pages again',async()=>{
    const c=await ready();c.picker.select(records[0].result_id);await c.picker.nextResults();
    expect(c.picker.snapshot().selection).toBeNull();expect(c.picker.snapshot().page?.items).toEqual(records.slice(10,20));
    await c.picker.nextResults();expect(c.picker.snapshot().result_page).toBe(2);
    expect(c.picker.snapshot().page?.items).toEqual(records.slice(20));
    expect(()=>c.picker.nextResults()).toThrow(ApiError);
    await c.picker.previousResults();expect(c.picker.snapshot().page?.items).toEqual(records.slice(10,20));
    await c.picker.previousResults();expect(c.picker.snapshot().page?.items).toEqual(records.slice(0,10));
    expect(()=>c.picker.previousResults()).toThrow(ApiError);
    expect(c.api.cropResultCatalog.mock.calls.every(([q])=>q.limit===10)).toBe(true);
  });
  it('keeps a single farm page and clears crop/result when changing farm pages',async()=>{
    const c=await ready(),items=Array.from({length:20},(_,i)=>({...farm,intent_job:{...farm.intent_job,
      job_id:'00000000-0000-4000-8000-'+String(i+1).padStart(12,'0')}}));
    const cursor={created_at:items[19]!.intent_job.created_at,job_id:items[19]!.intent_job.job_id};
    c.api.authoredFarmCatalog.mockResolvedValueOnce({items,next_cursor:cursor});await c.picker.refreshFarms();
    expect(c.picker.snapshot().farms?.items).toHaveLength(20);
    c.api.authoredFarmCatalog.mockResolvedValueOnce({items:[],next_cursor:null});await c.picker.nextFarms();
    expect(c.api.authoredFarmCatalog).toHaveBeenLastCalledWith(cursor);
    expect(c.picker.snapshot().farms?.items).toEqual([]);expect(c.picker.snapshot().crop).toBeNull();
    await c.picker.previousFarms();expect(c.api.authoredFarmCatalog).toHaveBeenLastCalledWith(undefined);
    expect(c.picker.snapshot().farm_page).toBe(0);
  });
  it('preserves empty current results without inventing a total or a selected result',async()=>{
    const c=await registered();c.api.cropResultCatalog.mockImplementationOnce(async q=>decodeCropCatalogPage({...source,items:[],next_cursor:null},q));
    await c.picker.chooseCrop(source.farm.crop_id);expect(c.picker.snapshot().page?.items).toEqual([]);
    expect(c.picker.snapshot().selection).toBeNull();expect(()=>c.picker.nextResults()).toThrow(ApiError);
  });
  it('allows opening a metadata hold while preserving its status for the existing query',async()=>{
    const c=await registered();c.api.cropResultCatalog.mockImplementationOnce(async q=>decodeCropCatalogPage({
      ...source,items:[{...records[0],calculation_status:'hold'}],next_cursor:null},q));
    await c.picker.chooseCrop(source.farm.crop_id);c.picker.select(records[0].result_id);
    expect(c.picker.snapshot().page?.items[0]?.calculation_status).toBe('hold');expect(c.picker.snapshot().selection).not.toBeNull();
  });
  it('clears all previous metadata and replay after a current rights error',async()=>{
    const c=await ready();c.picker.select(records[0].result_id);
    c.api.cropResultCatalog.mockRejectedValueOnce(new ApiError('access_denied',403));await c.picker.refreshResults();
    const s=c.picker.snapshot();expect(s.phase).toBe('error');expect(s.selection).toBeNull();expect(s.farm).toBeNull();
    expect(s.farms).toBeNull();expect(s.page).toBeNull();expect(s.error?.code).toBe('access_denied');
  });
  it('ignores a late noncancelable farm-list success after cancel',async()=>{
    const c=setup(),g=gate();c.api.authoredFarmCatalog.mockImplementationOnce(async()=>{g.enter();await g.promise;return {items:[farm],next_cursor:null};});
    const work=c.picker.refreshFarms();await g.entered;c.picker.cancel();g.release();await work;
    expect(c.picker.snapshot().phase).toBe('idle');expect(c.picker.snapshot().farms).toBeNull();
  });
  it('aborts and ignores a late result success without restoring the previous replay',async()=>{
    const c=await ready(),g=gate();c.picker.select(records[0].result_id);
    c.api.cropResultCatalog.mockImplementationOnce(async q=>{g.enter();await g.promise;return result(q);});
    const work=c.picker.refreshResults();await g.entered;expect(c.picker.snapshot().selection).toBeNull();
    c.picker.cancel();g.release();await work;expect(c.picker.snapshot().page).toBeNull();
    expect(c.picker.snapshot().phase).toBe('idle');
  });
  it('serializes a new kind after a late failed request and ignores the stale error',async()=>{
    const c=await ready(),g=gate();c.api.cropResultCatalog.mockImplementationOnce(async()=>{g.enter();await g.promise;throw new ApiError('access_denied');});
    const old=c.picker.refreshResults();await g.entered;const next=c.picker.setKind('harvest_v1');
    expect(c.api.cropResultCatalog).toHaveBeenCalledTimes(2);g.release();await Promise.all([old,next]);
    expect(c.picker.snapshot().page?.kind).toBe('harvest_v1');expect(c.picker.snapshot().error).toBeNull();
  });
  it('never publishes a pending result after disposal',async()=>{
    const c=await ready(),g=gate();c.api.cropResultCatalog.mockImplementationOnce(async q=>{g.enter();await g.promise;return result(q);});
    const work=c.picker.refreshResults();await g.entered;c.picker.dispose();const calls=c.changed.mock.calls.length;
    g.release();await work;expect(c.picker.snapshot().phase).toBe('disposed');expect(c.changed).toHaveBeenCalledTimes(calls);
  });
  it('keeps requests serial when a subscriber changes kind during the loading notification',async()=>{
    const c=setup(),g=gate();let active=0,peak=0,switched=false,nested=Promise.resolve();
    const picker=createCropResultPicker(c.api,s=>{
      if(s.work==='results'&&!switched){switched=true;nested=picker.setKind('harvest_v1');}
    });
    c.api.cropResultCatalog.mockImplementation(async q=>{
      active++;peak=Math.max(peak,active);
      if(q.kind==='harvest_v1'){g.enter();await g.promise;}
      active--;return result(q);
    });
    await picker.refreshFarms();await picker.chooseFarm(farm.intent_job.job_id);
    const first=picker.chooseCrop(source.farm.crop_id);await g.entered;const last=picker.setKind('calculation_cycle_v1');
    await new Promise(resolve=>setImmediate(resolve));g.release();await Promise.all([first,nested,last]);
    expect(peak).toBe(1);expect(picker.snapshot().page?.kind).toBe('calculation_cycle_v1');
  });
});
