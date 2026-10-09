import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {describe,it,expect,vi} from 'vitest';
import {ApiError,createApi} from './api';
import {decodeCropFarmSelection,type CropFarmRegistration} from './cropFarmSelection';

const fixture=JSON.parse(readFileSync(new URL('../e2e/crop-farm-selection-recorded-responses.json',import.meta.url),'utf8'));
const token='owned-synthetic-farm-crop-selection-token';
const body=()=>JSON.parse(fixture.bodies_raw_utf8.registered);
const selection=():CropFarmRegistration=>({...fixture.actual_HTTPS_body_checks[0].query});
function response(value:unknown,status=200){return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});}

describe('current registered crop selection SDK',()=>{
  it('reads both unchanged actual HTTPS bodies and preserves their source hashes and metadata',async()=>{
    for(const check of fixture.actual_HTTPS_body_checks){
      const raw=fixture.bodies_raw_utf8[check.label];
      expect(createHash('sha256').update(raw).digest('hex')).toBe(check.body_sha256);
      expect(Buffer.byteLength(raw)).toBe(check.bytes);
      const fetcher=vi.fn<typeof fetch>().mockResolvedValue(new Response(raw,{headers:{'content-type':'application/json'}}));
      expect(await createApi(token,fetcher).cropFarmSelection(check.query)).toEqual(JSON.parse(raw));
      expect(fetcher).toHaveBeenCalledTimes(1);
    }
    expect(body().items).toHaveLength(1);expect(fixture.actual_crop_Runs).toBe(0);
  });
  const faults:Record<string,(v:any)=>void>={
    extra:v=>v.result_count=1,version:v=>v.version='production',scope:v=>v.scope='validated_crop_profile',
    missing:v=>delete v.items,items:v=>v.items={},farmExtra:v=>v.farm.crop_id='crop',
    farmID:v=>v.farm.scenario_id='different',farmRevision:v=>v.farm.scenario_revision='different',
    farmHash:v=>v.farm.registration_sha256='A'.repeat(64),farmMissing:v=>delete v.farm.scenario_revision,
    selectionFalse:v=>v.selection_validation_required=false,selectionNumber:v=>v.selection_validation_required=1,
    approvalTrue:v=>v.rights_or_gate_approval=true,approvalNumber:v=>v.rights_or_gate_approval=0,
    cropMissing:v=>delete v.items[0].variety,cropExtra:v=>v.items[0].yield_kg=100,
    cropID:v=>v.items[0].crop_id='../crop',batchID:v=>v.items[0].batch_id='',
    speciesType:v=>v.items[0].species=3,varietyType:v=>v.items[0].variety=null,
    speciesEmpty:v=>v.items[0].species='',varietyLong:v=>v.items[0].variety='🍅'.repeat(201),
    speciesLeftSpace:v=>v.items[0].species=' 토마토',varietyRightSpace:v=>v.items[0].variety='품종\u3000',
    pythonSpaceLeft:v=>v.items[0].species='\u0085토마토',pythonSpaceRight:v=>v.items[0].species='토마토\u0085',
    control:v=>v.items[0].species='토\u001f마토',newline:v=>v.items[0].variety='품\n종',
    loneSurrogate:v=>v.items[0].variety='\ud800',profile:v=>v.items[0].profile_status='validated',
    origin:v=>v.items[0].origin='source',evidence:v=>v.items[0].evidence_level='measured',
    occupancyMissing:v=>delete v.items[0].occupancy.end,occupancyExtra:v=>v.items[0].occupancy.unit='UTC',
    date:v=>v.items[0].occupancy.start='2026-02-30T00:00:00.000000Z',
    offset:v=>v.items[0].occupancy.start='2026-01-01T00:00:00.000000+00:00',
    precision:v=>v.items[0].occupancy.start='2026-01-01T00:00:00.000Z',
    zeroPeriod:v=>v.items[0].occupancy.end=v.items[0].occupancy.start,
    reversedPeriod:v=>v.items[0].occupancy={start:'2026-01-01T00:00:00.000010Z',end:'2026-01-01T00:00:00.000009Z'},
    duplicate:v=>v.items.push(structuredClone(v.items[0])),
    reversedIDs:v=>{const row=v.items[0];v.items=[{...row,crop_id:'crop-z'},{...row,crop_id:'crop-a'}];},
    tooMany:v=>v.items=Array.from({length:33},(_,i)=>({...v.items[0],crop_id:'crop-'+String(i).padStart(2,'0')})),
  };
  it.each(Object.keys(faults))('rejects malformed or unsupported %s',fault=>{
    const value=body();faults[fault]!(value);
    expect(()=>decodeCropFarmSelection(value,selection())).toThrow(ApiError);
  });
  it('accepts empty and thirty-two registered crops without claiming stored results or approval',()=>{
    const value=body();expect(decodeCropFarmSelection({...value,items:[]},selection()).items).toEqual([]);
    value.items=Array.from({length:32},(_,i)=>({...value.items[0],crop_id:'crop-'+String(i).padStart(2,'0')}));
    const decoded=decodeCropFarmSelection(value,selection());expect(decoded.items).toHaveLength(32);
    expect(decoded.scope).toBe('registered_user_inputs_only');expect(decoded.rights_or_gate_approval).toBe(false);
    expect(decoded.selection_validation_required).toBe(true);
  });
  it('preserves Korean and astral names at the two-hundred-code-point boundary and submillisecond UTC',()=>{
    const value=body();value.items[0].species='방울 토마토';value.items[0].variety='🍅'.repeat(200);
    value.items[0].occupancy={start:'2026-01-01T00:00:00.000009Z',end:'2026-01-01T00:00:00.000010Z'};
    expect(value.items[0].variety.length).toBe(400);
    expect(Date.parse(value.items[0].occupancy.start)).toBe(Date.parse(value.items[0].occupancy.end));
    expect(decodeCropFarmSelection(value,selection())).toEqual(value);
    value.items[0].species='\ufeff토마토';expect(decodeCropFarmSelection(value,selection())).toEqual(value);
  });
  it('detaches farm, crop and occupancy references and never caches returned values',()=>{
    const value=body(),expected=structuredClone(value),decoded=decodeCropFarmSelection(value,selection());
    value.farm.scenario_id='changed';value.items[0].species='changed';value.items[0].occupancy.start='changed';
    expect(decoded).toEqual(expected);Object.assign(decoded.items[0]!.occupancy,{start:'changed'});
    expect(decodeCropFarmSelection(body(),selection())).toEqual(expected);
  });
  const badQueries:Record<string,(v:any)=>void>={
    extra:v=>v.crop_id='crop',tenant:v=>v.tenant_id='other',token:v=>v.token=token,
    missing:v=>delete v.scenario_revision,name:v=>v.scenario_id='../farm',empty:v=>v.scenario_revision='',
    hash:v=>v.registration_sha256='A'.repeat(64),hashType:v=>v.registration_sha256=0,
  };
  it.each(Object.keys(badQueries))('does not transmit invalid farm query %s',async fault=>{
    const value=selection();badQueries[fault]!(value);const fetcher=vi.fn<typeof fetch>();
    await expect(createApi(token,fetcher).cropFarmSelection(value)).rejects.toMatchObject({code:'response_rejected'});
    expect(fetcher).not.toHaveBeenCalled();
  });
  it('uses one exact same-origin GET with the current bearer and no hidden query or body',async()=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(response(body()));
    await createApi(token,fetcher).cropFarmSelection(selection());expect(fetcher).toHaveBeenCalledTimes(1);
    const [path,init]=fetcher.mock.calls[0]!,url=new URL(String(path),'https://owned.test');
    expect(url.pathname).toBe('/v1/crop-research-result-catalog/farm-crops');
    expect(Object.fromEntries(url.searchParams)).toEqual(selection());
    expect(init).toMatchObject({method:'GET',cache:'no-store',redirect:'error',credentials:'omit',headers:{authorization:'Bearer '+token}});
    expect(init?.body).toBeUndefined();
  });
  it('rejects a farm changed while its response is pending',async()=>{
    let complete!:(response:Response)=>void;
    const fetcher=vi.fn<typeof fetch>().mockImplementation(()=>new Promise(resolve=>{complete=resolve;}));
    const farm={...selection()},pending=createApi(token,fetcher).cropFarmSelection(farm);
    farm.scenario_revision='different';complete(response(body()));
    await expect(pending).rejects.toMatchObject({code:'response_rejected'});
  });
  it('does not send an already-canceled request and refuses late success after cancellation',async()=>{
    const stopped=new AbortController();stopped.abort();const unused=vi.fn<typeof fetch>();
    await expect(createApi(token,unused).cropFarmSelection(selection(),stopped.signal)).rejects.toMatchObject({code:'request_canceled'});
    expect(unused).not.toHaveBeenCalled();
    let complete!:(response:Response)=>void;
    const fetcher=vi.fn<typeof fetch>().mockImplementation(()=>new Promise(resolve=>{complete=resolve;}));
    const controller=new AbortController(),pending=createApi(token,fetcher).cropFarmSelection(selection(),controller.signal);
    controller.abort();expect(fetcher.mock.calls[0]![1]?.signal?.aborted).toBe(true);complete(response(body()));
    await expect(pending).rejects.toMatchObject({code:'request_canceled'});
  });
  it('keeps the shared 64KiB and thirty-second limits',async()=>{
    const tooLarge=new Response(' '.repeat(65536)+fixture.bodies_raw_utf8.registered,{headers:{'content-type':'application/json'}});
    await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(tooLarge)).cropFarmSelection(selection())).rejects.toMatchObject({code:'response_rejected'});
    vi.useFakeTimers();
    try{
      const fetcher=vi.fn<typeof fetch>().mockImplementation((_url,init)=>new Promise((_resolve,reject)=>{
        init?.signal?.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')),{once:true});
      }));
      const pending=createApi(token,fetcher).cropFarmSelection(selection()),rejected=expect(pending).rejects.toMatchObject({code:'network_unresolved'});
      await vi.advanceTimersByTimeAsync(29999);expect(fetcher.mock.calls[0]![1]?.signal?.aborted).toBe(false);
      await vi.advanceTimersByTimeAsync(1);await rejected;
    }finally{vi.useRealTimers();}
  });
  it.each([[401,'auth_required'],[403,'access_denied'],[422,'invalid_request'],[503,'server_unavailable']] as const)('preserves HTTP %s refusal without retry',async(status,code)=>{
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(response({untrusted:'details'},status));
    await expect(createApi(token,fetcher).cropFarmSelection(selection())).rejects.toMatchObject({code,status});
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
