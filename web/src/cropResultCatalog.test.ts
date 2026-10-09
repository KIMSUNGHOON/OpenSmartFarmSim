import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {describe,it,expect,vi} from 'vitest';
import {ApiError,createApi} from './api';
import {decodeCropCatalogPage,type CropCatalogQuery} from './cropResultCatalog';

const fixture=JSON.parse(readFileSync(new URL('../e2e/crop-result-catalog-recorded-responses.json',import.meta.url),'utf8'));
const body=(label='growth_default')=>JSON.parse(fixture.bodies_raw_utf8[label]);
const token='owned-synthetic-catalogue-browser-token';
function selection(label='growth_default'):CropCatalogQuery{
  const v=fixture.actual_HTTPS_body_checks.find((v:any)=>v.label===label).query;
  return {kind:v.kind,farm:{scenario_id:v.scenario_id,scenario_revision:v.scenario_revision,
    registration_sha256:v.registration_sha256,crop_id:v.crop_id},
    ...(Object.hasOwn(v,'limit')?{limit:v.limit}:{}),
    before:v.before_result_id?{recorded_at:v.before_recorded_at,result_id:v.before_result_id}:null};
}
function response(value:unknown,status=200){return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});}
function altered(label:string,change:(value:any)=>void){const value=body(label);change(value);return value;}

describe('stored crop research catalogue SDK',()=>{
  it('preserves all seven actual HTTPS body hashes, lengths and metadata',()=>{
    for(const check of fixture.actual_HTTPS_body_checks){
      const raw=fixture.bodies_raw_utf8[check.label];
      expect(createHash('sha256').update(raw).digest('hex')).toBe(check.body_sha256);
      expect(Buffer.byteLength(raw)).toBe(check.bytes);
      expect(decodeCropCatalogPage(JSON.parse(raw),selection(check.label))).toEqual(JSON.parse(raw));
    }
    expect(body('growth_max').items).toHaveLength(20);
    expect(body('growth_tail').items).toHaveLength(1);
    expect(body('harvest').items[0].row_count).toBe(5);
    expect(fixture.actual_crop_Runs).toBe(0);
  });

  const common:Record<string,(v:any)=>void>={
    extra:v=>v.extra=1,version:v=>v.version='production',scope:v=>v.scope='live_simulation',
    kind:v=>v.kind=v.kind==='harvest_v1'?'calculation_cycle_v1':'harvest_v1',
    farmExtra:v=>v.farm.tenant_id='foreign',farm:v=>v.farm.crop_id='foreign',
    hash:v=>v.farm.registration_sha256='A'.repeat(64),missing:v=>delete v.farm.scenario_revision,
    approval:v=>v.rights_or_gate_approval=true,falseNumber:v=>v.rights_or_gate_approval=0,
    selection:v=>v.selection_validation_required=false,trueNumber:v=>v.selection_validation_required=1,
    items:v=>v.items={},rowExtra:v=>v.items[0].yield_kg=20,
    status:v=>v.items[0].calculation_status='succeeded',claim:v=>v.items[0].claim_scope='crop_prediction',
    ID:v=>v.items[0].result_id='unknown:'+'a'.repeat(64),
    time:v=>v.items[0].recorded_at='2026-02-30T00:00:00.000000Z',
    offset:v=>v.items[0].recorded_at='2026-10-09T00:00:00.000000+00:00',
    precision:v=>v.items[0].recorded_at='2026-10-09T00:00:00.001Z',
    duplicate:v=>{v.items[1]=v.items[0];},
    cursorExtra:v=>v.next_cursor={recorded_at:v.items.at(-1).recorded_at,result_id:v.items.at(-1).result_id,approval:true},
    cursorID:v=>v.next_cursor={recorded_at:v.items.at(-1).recorded_at,result_id:'unknown'},
    cursorBeforeLast:v=>v.next_cursor={recorded_at:v.items[0].recorded_at,result_id:v.items[0].result_id},
  };
  for(const label of ['growth_default','harvest']){
    it.each(Object.keys(common))(`${label} rejects malformed %s`,fault=>{
      expect(()=>decodeCropCatalogPage(altered(label,common[fault]!),selection(label))).toThrow(ApiError);
    });
  }
  const growthFaults:Record<string,(v:any)=>void>={
    sampleNegative:v=>v.items[0].sample_count=-1,sampleBool:v=>v.items[0].sample_count=true,
    sampleFraction:v=>v.items[0].sample_count=.5,sampleLimit:v=>v.items[0].sample_count=131073,
    eventInfinity:v=>v.items[0].event_count=Infinity,eventLimit:v=>v.items[0].event_count=131073,
    study:v=>v.items[0].study_id='../unknown',revision:v=>v.items[0].revision='',
    periodExtra:v=>v.items[0].period.unit='UTC',periodInvalid:v=>v.items[0].period.start='2026-02-30T00:00:00Z',
    periodOffset:v=>v.items[0].period.start='2026-01-01T00:00:00+00:00',
    periodEmpty:v=>v.items[0].period.start=v.items[0].period.end,
    periodReversed:v=>v.items[0].period={start:'2026-01-01T00:00:00.12Z',end:'2026-01-01T00:00:00.119999Z'},
    periodEquivalent:v=>v.items[0].period={start:'2026-01-01T00:00:00.1Z',end:'2026-01-01T00:00:00.100000Z'},
    reversed:v=>v.items.reverse(),tooMany:v=>v.items.push(...body('growth_max').items),
  };
  it.each(Object.keys(growthFaults))('growth rejects %s',fault=>{
    expect(()=>decodeCropCatalogPage(altered('growth_default',growthFaults[fault]!),selection())).toThrow(ApiError);
  });
  it.each(['parent','rowNegative','rowBool','rowFraction','rowLimit'])('harvest rejects %s',fault=>{
    const value=body('harvest'),row=value.items[0];
    if(fault==='parent')row.parent_result_id=row.result_id;
    else row.row_count={rowNegative:-1,rowBool:false,rowFraction:.1,rowLimit:262145}[fault as 'rowNegative'];
    expect(()=>decodeCropCatalogPage(value,selection('harvest'))).toThrow(ApiError);
  });

  it('preserves microseconds when ordering timestamps and enforcing the cursor',()=>{
    const value=body('growth_tail'),row=value.items[0];
    value.items=[{...row,result_id:'crop-cycle-verified-result-v1:'+'0'.repeat(64),recorded_at:'2026-01-01T00:00:00.000010Z'},
      {...row,result_id:'crop-cycle-verified-result-v1:'+'f'.repeat(64),recorded_at:'2026-01-01T00:00:00.000009Z'}];
    const request={...selection(),limit:2};
    expect(Date.parse(value.items[0].recorded_at)).toBe(Date.parse(value.items[1].recorded_at));
    expect(decodeCropCatalogPage(value,request).items).toHaveLength(2);
    expect(()=>decodeCropCatalogPage({...value,items:[...value.items].reverse()},request)).toThrow(ApiError);
    const before={recorded_at:value.items[0].recorded_at,result_id:value.items[0].result_id};
    expect(decodeCropCatalogPage({...value,items:[value.items[1]]},{...request,before}).items).toHaveLength(1);
    expect(()=>decodeCropCatalogPage(value,{...request,before})).toThrow(ApiError);
  });
  it('preserves positive submillisecond periods and allows empty/hold metadata only',()=>{
    const request={...selection(),limit:1};
    const value=body('growth_tail');value.items[0].period={start:'2026-01-01T00:00:00Z',end:'2026-01-01T00:00:00.000001Z'};
    value.items[0].calculation_status='hold';value.items[0].sample_count=0;value.items[0].event_count=0;
    expect(decodeCropCatalogPage(value,request)).toEqual(value);
    expect(decodeCropCatalogPage({...value,items:[]},request).items).toEqual([]);
    expect(()=>decodeCropCatalogPage({...value,items:[],next_cursor:{result_id:value.items[0].result_id,
      recorded_at:value.items[0].recorded_at}},request)).toThrow(ApiError);
    const harvest=body('harvest');harvest.items[0].calculation_status='hold';harvest.items[0].row_count=0;
    expect(decodeCropCatalogPage(harvest,selection('harvest'))).toEqual(harvest);
  });
  it('rejects a short page with a cursor, excess request count and wrong-kind cursor',()=>{
    const v=body('growth_tail');v.next_cursor={recorded_at:v.items[0].recorded_at,result_id:v.items[0].result_id};
    expect(()=>decodeCropCatalogPage(v,{...selection(),limit:2})).toThrow(ApiError);
    expect(()=>decodeCropCatalogPage(body('growth_max'),selection())).toThrow(ApiError);
    expect(()=>decodeCropCatalogPage(body('harvest'),{...selection('harvest'),before:v.next_cursor})).toThrow(ApiError);
  });
  it.each(['growth_tail','harvest'])('%s rejects one result repeated at different timestamps',label=>{
    const value=body(label),row=value.items[0];
    value.items=[{...row,recorded_at:'2026-01-01T00:00:00.000010Z'},
      {...row,recorded_at:'2026-01-01T00:00:00.000009Z'}];
    expect(()=>decodeCropCatalogPage(value,{...selection(label),limit:2,before:null})).toThrow(ApiError);
  });
  const queryFaults:Record<string,(v:any)=>void>={
    kind:v=>v.kind='legacy',missing:v=>delete v.farm,extra:v=>v.token='hidden',farmExtra:v=>v.farm.tenant_id='foreign',
    farmHash:v=>v.farm.registration_sha256='A'.repeat(64),crop:v=>v.farm.crop_id='../crop',
    zero:v=>v.limit=0,bool:v=>v.limit=true,fraction:v=>v.limit=1.2,limit:v=>v.limit=21,
    undefined:v=>v.limit=undefined,beforeExtra:v=>v.before={...body('growth_default').next_cursor,offset:0},
    beforeMissing:v=>v.before={recorded_at:'2026-01-01T00:00:00.000000Z'},
    beforeUTC:v=>v.before={...body('growth_default').next_cursor,recorded_at:'2026-01-01T00:00:00.000Z'},
  };
  it.each(Object.keys(queryFaults))('does not send invalid %s',async fault=>{
    const request=structuredClone(selection());queryFaults[fault]!(request);
    const fetcher=vi.fn<typeof fetch>();await expect(createApi(token,fetcher).cropResultCatalog(request)).rejects.toMatchObject({code:'response_rejected'});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('uses one fixed same-origin request and exactly transmits the server cursor',async()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(response(body('growth_max'))).mockResolvedValueOnce(response(body('growth_tail')));
    const api=createApi(token,fetcher),first=await api.cropResultCatalog(selection('growth_max'));
    expect(fetcher).toHaveBeenCalledTimes(1);
    const next=await api.cropResultCatalog({...selection('growth_max'),before:first.next_cursor});
    expect(next).toEqual(body('growth_tail'));expect(fetcher).toHaveBeenCalledTimes(2);
    const [path,init]=fetcher.mock.calls[1]!;const url=new URL(String(path),'https://owned.test');
    expect(url.pathname).toBe('/v1/crop-research-result-catalog');
    expect(url.searchParams.get('before_recorded_at')).toBe(first.next_cursor!.recorded_at);
    expect(url.searchParams.get('before_result_id')).toBe(first.next_cursor!.result_id);
    expect(url.searchParams.get('limit')).toBe('20');
    expect(init).toMatchObject({method:'GET',credentials:'omit',redirect:'error',cache:'no-store',headers:{authorization:'Bearer '+token}});
    expect(init?.body).toBeUndefined();expect(url.searchParams.has('token')).toBe(false);
  });
  it('defaults to ten and detaches returned nested objects from the transport payload',async()=>{
    const raw=body(),fetcher=vi.fn<typeof fetch>().mockResolvedValue(response(raw));
    const {kind,farm}=selection();const value=await createApi(token,fetcher).cropResultCatalog({kind,farm});
    expect(new URL(String(fetcher.mock.calls[0]![0]),'https://owned.test').searchParams.get('limit')).toBe('10');
    const original=body();const decoded=decodeCropCatalogPage(raw,selection());
    Object.assign(raw.farm,{crop_id:'changed'});Object.assign(raw.items[0].period,{start:'changed'});
    expect(decoded).toEqual(original);expect(value).toEqual(original);
    Object.assign(decoded.next_cursor!,{result_id:'changed'});expect(original.next_cursor.result_id).not.toBe('changed');
  });
  it('rejects a changed request while its response is pending',async()=>{
    let complete!:(value:Response)=>void;const fetcher=vi.fn<typeof fetch>().mockImplementation(()=>new Promise(resolve=>{complete=resolve;}));
    const request=structuredClone(selection()),pending=createApi(token,fetcher).cropResultCatalog(request);
    Object.assign(request.farm,{crop_id:'different'});complete(response(body()));
    await expect(pending).rejects.toMatchObject({code:'response_rejected'});
  });
  it('cancels before send and rejects a late response after cancellation',async()=>{
    const stopped=new AbortController();stopped.abort();const unused=vi.fn<typeof fetch>();
    await expect(createApi(token,unused).cropResultCatalog(selection(),stopped.signal)).rejects.toMatchObject({code:'request_canceled'});
    expect(unused).not.toHaveBeenCalled();
    let complete!:(value:Response)=>void;const fetcher=vi.fn<typeof fetch>().mockImplementation(()=>new Promise(resolve=>{complete=resolve;}));
    const controller=new AbortController(),pending=createApi(token,fetcher).cropResultCatalog(selection(),controller.signal);
    controller.abort();expect(fetcher.mock.calls[0]![1]?.signal?.aborted).toBe(true);complete(response(body()));
    await expect(pending).rejects.toMatchObject({code:'request_canceled'});
  });
  it('enforces 64KiB and the existing thirty second timeout',async()=>{
    const tooLarge=new Response(' '.repeat(65536)+fixture.bodies_raw_utf8.growth_default,{headers:{'content-type':'application/json'}});
    await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(tooLarge)).cropResultCatalog(selection())).rejects.toMatchObject({code:'response_rejected'});
    vi.useFakeTimers();
    try{
      const fetcher=vi.fn<typeof fetch>().mockImplementation((_url,init)=>new Promise((_resolve,reject)=>{
        init?.signal?.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')),{once:true});
      }));
      const pending=createApi(token,fetcher).cropResultCatalog(selection()),rejected=expect(pending).rejects.toMatchObject({code:'network_unresolved'});
      await vi.advanceTimersByTimeAsync(29999);expect(fetcher.mock.calls[0]![1]?.signal?.aborted).toBe(false);
      await vi.advanceTimersByTimeAsync(1);await rejected;
    }finally{vi.useRealTimers();}
  });
  it.each([[401,'auth_required'],[403,'access_denied'],[422,'invalid_request'],[503,'server_unavailable']] as const)('keeps HTTP %s as a refusal',async(status,code)=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(response({private:'untrusted'},status));
    await expect(createApi(token,fetcher).cropResultCatalog(selection())).rejects.toMatchObject({code,status});
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
