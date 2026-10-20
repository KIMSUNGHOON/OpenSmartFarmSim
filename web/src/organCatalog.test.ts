import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {describe,it,expect,vi} from 'vitest';
import {ApiError,createApi} from './api';
import {decodeCropCatalogPage,type CropCatalogQuery} from './cropResultCatalog';

const fixture=JSON.parse(readFileSync(new URL('../e2e/organ-catalog-recorded-responses.json',import.meta.url),'utf8'));
const source=JSON.parse(fixture.bodies_raw_utf8.organ);
const query=():CropCatalogQuery=>({kind:'organ_v1',farm:structuredClone(source.farm)});
const token='owned-synthetic-organ-catalogue-test-only';
const response=(value:unknown,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json'}});

describe('recorded organ catalogue SDK',()=>{
  it('preserves all seven original HTTPS body hashes and both positive metadata replies',()=>{
    for(const item of fixture.actual_HTTPS_body_checks){
      const raw=fixture.bodies_raw_utf8[item.label];
      expect(Buffer.byteLength(raw)).toBe(item.bytes);
      expect(createHash('sha256').update(raw).digest('hex')).toBe(item.body_SHA256);
    }
    for(const label of ['organ','restored']){
      const value=JSON.parse(fixture.bodies_raw_utf8[label]);
      expect(decodeCropCatalogPage(value,query())).toEqual(value);
    }
    expect(fixture.actual_crop_Runs).toBe(0);
  });
  it('sends exactly one bounded GET using the original farm and explicit kind',async()=>{
    const fetcher=vi.fn<typeof fetch>(async()=>response(source));
    expect(await createApi(token,fetcher).cropResultCatalog(query())).toEqual(source);
    expect(fetcher).toHaveBeenCalledTimes(1);
    const [url,options]=fetcher.mock.calls[0]!;
    const target=new URL(String(url),'http://localhost');
    expect(target.pathname).toBe('/v1/crop-research-result-catalog');
    expect(Object.fromEntries(target.searchParams)).toEqual({kind:'organ_v1',...source.farm,limit:'10'});
    expect(options?.method).toBe('GET');expect(options?.cache).toBe('no-store');
    expect(options?.redirect).toBe('error');expect(options?.headers).toMatchObject({authorization:'Bearer '+token});
  });
  const faults:Record<string,(value:any)=>void>={
    kind:v=>v.kind='calculation_cycle_v1',ID:v=>v.items[0].result_id='crop-result-v2:'+'a'.repeat(64),
    farm:v=>v.farm.crop_id='other',extra:v=>v.items[0].yield_kg=3,
    claim:v=>v.items[0].claim_scope='crop_prediction',approval:v=>v.rights_or_gate_approval=0,
    selection:v=>v.selection_validation_required=1,samples:v=>v.items[0].sample_count=true,
    sampleLimit:v=>v.items[0].sample_count=131073,eventLimit:v=>v.items[0].event_count=131073,
    eventNegative:v=>v.items[0].event_count=-1,period:v=>v.items[0].period.end=v.items[0].period.start,
    time:v=>v.items[0].recorded_at='2026-10-20T00:00:00.000Z',
    cursor:v=>v.next_cursor={recorded_at:v.items[0].recorded_at,result_id:'crop-cycle-verified-result-v1:'+'a'.repeat(64)},
    parent:v=>v.items[0].parent_result_id='crop-result-v1:'+'b'.repeat(64),
  };
  it.each(Object.keys(faults))('rejects software malformed %s without exposing a result',fault=>{
    const value=structuredClone(source);faults[fault]!(value);
    expect(()=>decodeCropCatalogPage(value,query())).toThrow(ApiError);
  });
  it('preserves exact microsecond cursors and empty/hold metadata without approving growth',()=>{
    const first=source.items[0],a={...first,recorded_at:'2026-10-20T00:00:00.000010Z'},
      b={...first,result_id:'crop-result-v1:'+'0'.repeat(64),recorded_at:'2026-10-20T00:00:00.000009Z'};
    const request={...query(),limit:1,before:{recorded_at:a.recorded_at,result_id:a.result_id}};
    expect(decodeCropCatalogPage({...source,items:[b]},request).items[0]).toEqual(b);
    expect(()=>decodeCropCatalogPage({...source,items:[a]},request)).toThrow(ApiError);
    const hold={...first,calculation_status:'hold',sample_count:0,event_count:0};
    expect(decodeCropCatalogPage({...source,items:[hold]},query()).items[0]).toEqual(hold);
    expect(decodeCropCatalogPage({...source,items:[]},query()).items).toEqual([]);
  });
  it('does not transmit a different-kind cursor or a pre-cancelled query',async()=>{
    const fetcher=vi.fn<typeof fetch>(),api=createApi(token,fetcher);
    await expect(api.cropResultCatalog({...query(),before:{recorded_at:source.items[0].recorded_at,
      result_id:'crop-result-v2:'+'a'.repeat(64)}})).rejects.toMatchObject({code:'response_rejected'});
    const cancelled=new AbortController();cancelled.abort();
    await expect(api.cropResultCatalog(query(),cancelled.signal)).rejects.toMatchObject({code:'request_canceled'});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('refuses a late success after cancellation',async()=>{
    let release!:(value:Response)=>void;
    const fetcher=vi.fn<typeof fetch>(()=>new Promise(resolve=>{release=resolve;})),controller=new AbortController();
    const work=createApi(token,fetcher).cropResultCatalog(query(),controller.signal);
    controller.abort();release(response(source));
    await expect(work).rejects.toMatchObject({code:'request_canceled'});
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
