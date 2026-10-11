import { describe,it,expect,vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { createApi,ApiError } from './api';
import { utcMicroseconds } from './coupledCropReplay';
import { createGreenhouseVentilationReplayApi,decodeGreenhouseVentilationResponse,validGreenhouseVentilationLookup,
  type GreenhouseVentilationLookup,type GreenhouseVentilationSummaryResponse } from './greenhouseVentilationReplay';

const bytes=readFileSync(new URL('../e2e/greenhouse-ventilation-recorded-responses.json',import.meta.url));
const fixture=JSON.parse(bytes.toString());
type Raw=Record<string,any>;
const original=fixture.completed[0],held=fixture.hold[0];
const lookup=(p:Raw):GreenhouseVentilationLookup=>({result_id:p.result_id,...Object.fromEntries(
  ['scenario_id','scenario_revision','registration_sha256','crop_id'].map(k=>[k,p.farm[k]]))}) as GreenhouseVentilationLookup;
const pick=lookup(original);
const summary=()=>structuredClone(original),samples=()=>structuredClone(fixture.completed[1]),events=()=>structuredClone(fixture.completed[2]);
const ready=(value:unknown)=>new Response(JSON.stringify(value),{status:200,headers:{'content-type':'application/json'}});
function shaped(kind:'samples'|'events',offset=0,limit=kind==='samples'?64:8){
  const p=kind==='samples'?samples():events();const all=p.page.records;
  p.page.records=all.slice(offset,offset+limit);p.page.offset=offset;p.page.limit=limit;
  p.page.next_offset=offset+p.page.records.length<p.page.total?offset+p.page.records.length:null;return p;
}
function provider(){return vi.fn(async(path:string)=>{
  const q=new URL(path,'https://localhost').searchParams,view=q.get('view');
  return view==='summary'?summary():shaped(view as 'samples'|'events',Number(q.get('offset')),Number(q.get('limit')));
});}
function deferred<T>(){let release!:(v:T)=>void;const promise=new Promise<T>(r=>{release=r;});return {promise,release};}

describe('joint original saved crop/climate responses',()=>{
  it('keeps the six original verified HTTPS responses and all quantity/time fields',()=>{
    expect(createHash('sha256').update(bytes).digest('hex')).toBe('fce186ea3214157f73f63d6d51fd37627704f29bf680110b664f74ab13a9b1b1');
    expect(fixture.scope).toBe('owned_synthetic_verified_HTTPS_original_wire_not_measured_data_or_gate_acceptance');
    for(const p of [...fixture.completed,...fixture.hold])expect(decodeGreenhouseVentilationResponse(p,lookup(p))).toEqual(p);
    expect(original.reference.artifact.steps).toBe(16);expect(original.reference.G0_G4).toBe('not_assessed');
    const s=samples().page.records[0];expect(Object.keys(s.value.plant_state)).toHaveLength(5);
    expect(Object.keys(s.value.climate_state)).toHaveLength(3);expect(s.value.cohort_state.fruit_carbohydrate).toHaveLength(50);
    expect(s.value.cohort_state.fruit_number).toHaveLength(50);expect(Object.keys(s.value.integrated_transfers)).toHaveLength(25);
    expect(s.time.at).toBe('2026-10-01T00:00:00.123456Z');
    expect(utcMicroseconds(original.reference.time_grid.end_utc)-utcMicroseconds(s.time.at)).toBe(32000000n);
    expect(held.summary.checkpoint_sha256).toBeNull();expect(held.summary.hold).not.toBeNull();
    expect(events().page.records[0].value.management).not.toHaveProperty('event');
  });
  it.each(['lookup-extra','old-id','schema','gates','claim','top-extra','farm','batch','reference-extra','hash','code-map','profile-map','model-version',
    'model-mantissa','artifact-ref','steps','sample-count','event-count','storage','commit','grid-unit','grid-us','grid-end','grid-decimal','grid-step-count',
    'last-time','last-index','input-time','summary-xor','summary-status','manifest-identity','manifest-policy','numerical-method','numerical-step','numerical-duration',
    'summary-checkpoint','summary-last','sample-unit','sample-negative','sample-NaN','sample-cohorts','sample-cohort-unit','sample-cohort-negative',
    'sample-extra','sample-phase','sample-elapsed','sample-time','sample-residual','sample-budget','sample-transfer','sample-event-count',
    'page-total','page-offset','page-limit','page-next','page-count','page-order','event-code','event-profile','event-policy','event-before-hash',
    'event-before-state','event-removal-unit','event-cohorts','event-budget','event-raw','event-time','hold-phase','hold-time','hold-checkpoint','hold-reason'])
    ('rejects %s before display',fault=>{
      const p:Raw=fault.startsWith('event-') && fault!=='event-count'?events():fault.startsWith('sample-')||fault.startsWith('page-')?samples():
        fault.startsWith('hold-')?structuredClone(held):summary();
      const r=p.reference,a=r.artifact,g=r.time_grid,s=p.page?.records[0],m=s?.value.management,select=lookup(p);
      if(fault==='lookup-extra')(select as any).unknown=true;if(fault==='old-id')(select as any).result_id='crop-cycle-verified-result-v1:'+'a'.repeat(64);
      if(fault==='schema')p.schema_version='crop-cycle-calculation-replay-v1';if(fault==='gates')r.G0_G4='G2';if(fault==='claim')r.claim_scope='crop_prediction';
      if(fault==='top-extra')p.fresh_kg=1;if(fault==='farm')p.farm.crop_id='other';if(fault==='batch')p.farm.batch_id='';
      if(fault==='reference-extra')r.coefficients={};if(fault==='hash')r.payload_sha256='A'.repeat(64);
      if(fault==='code-map')delete r.code.server_dependency_sha256.time;if(fault==='profile-map')r.model.profile_sha256.extra='a'.repeat(64);
      if(fault==='model-version')r.model.engine_version='other';if(fault==='model-mantissa')r.model.float_mant_dig=24;
      if(fault==='artifact-ref')a.ref='joint-ventilation-storage-research-v1:'+'a'.repeat(64);if(fault==='steps')a.steps++;
      if(fault==='sample-count')a.sample_count=513;if(fault==='event-count')a.event_count=129;if(fault==='storage')a.storage_bytes=512*1024*1024+1;
      if(fault==='commit')a.commit_count=4098;if(fault==='grid-unit')g.time_rule='seconds';if(fault==='grid-us')g.step_microseconds++;
      if(fault==='grid-end')g.end_utc=g.end_utc.replace('.123456Z','.123457Z');if(fault==='grid-decimal')g.step_seconds_decimal='NaN';
      if(fault==='grid-step-count')g.step_count--;if(fault==='last-time')r.last_confirmed.at=g.start_utc;if(fault==='last-index')r.last_confirmed.step_index--;
      if(fault==='input-time')r.input.start_utc=r.input.end_utc;if(fault==='summary-xor')p.page=samples().page;
      if(fault==='summary-status')p.summary.status='hold';if(fault==='manifest-identity')p.summary.manifest.identity.engine_code_sha256='a'.repeat(64);
      if(fault==='manifest-policy')p.summary.manifest.policy_sha256='invalid-digest';if(fault==='numerical-method')p.summary.manifest.numerical.method='animation';
      if(fault==='numerical-step')p.summary.manifest.numerical.step_seconds++;if(fault==='numerical-duration')p.summary.manifest.numerical.duration_seconds++;
      if(fault==='summary-checkpoint')p.summary.checkpoint_sha256=null;if(fault==='summary-last')p.summary.last_confirmed.time.at=g.start_utc;
      if(fault==='sample-unit')s.value.plant_state.leaf.unit='kg';if(fault==='sample-negative')s.value.plant_state.leaf.value=-1;
      if(fault==='sample-NaN')s.value.climate_state.air_temperature.value=NaN;if(fault==='sample-cohorts')s.value.cohort_state.fruit_number.pop();
      if(fault==='sample-cohort-unit')s.value.cohort_state.fruit_number[0].unit='kg';if(fault==='sample-cohort-negative')s.value.cohort_state.fruit_number[0].value=-1;
      if(fault==='sample-extra')s.value.fresh_kg=1;if(fault==='sample-phase')s.value.phase='interpolated';if(fault==='sample-elapsed')s.value.elapsed_seconds++;
      if(fault==='sample-time')s.time.at=s.time.at.replace('.123456Z','.123457Z');if(fault==='sample-residual')s.value.balance_residuals.carbohydrate.value=1e9;
      if(fault==='sample-budget')s.value.balance_budgets.carbohydrate.value=-1;if(fault==='sample-transfer')delete s.value.integrated_transfers.capacity_allocation;
      if(fault==='sample-event-count')s.value.event_count=129;if(fault==='page-total')p.page.total++;if(fault==='page-offset')p.page.offset=-1;
      if(fault==='page-limit')p.page.limit=65;if(fault==='page-next')p.page.next_offset=1;if(fault==='page-count')p.page.records.pop();
      if(fault==='page-order')p.page.records[1]=structuredClone(s);if(fault==='event-code')m.code_sha256='a'.repeat(64);
      if(fault==='event-profile')m.profile_sha256.growth='a'.repeat(64);if(fault==='event-policy')m.policy_sha256='a'.repeat(64);
      if(fault==='event-before-hash')m.before.calculation_sha256='a'.repeat(64);if(fault==='event-before-state')m.before.plant_state.leaf.value=-1;
      if(fault==='event-removal-unit')m.removed.leaf.unit='kg';if(fault==='event-cohorts')m.removed.fruit_carbohydrate.pop();
      if(fault==='event-budget')m.balance_budgets.temperature.value=-1;if(fault==='event-raw')m.event={};if(fault==='event-time')s.value.elapsed_seconds++;
      if(fault==='hold-phase')p.summary.hold.phase='interpolated';if(fault==='hold-time')p.summary.hold.time.at=g.start_utc;
      if(fault==='hold-checkpoint')p.summary.checkpoint_sha256='a'.repeat(64);if(fault==='hold-reason')p.summary.hold.reason_code='raw details';
      expect(()=>decodeGreenhouseVentilationResponse(p,select)).toThrow(ApiError);
    });
  it('binds a shape-only one-microsecond grid without JS millisecond rounding',()=>{
    const p=summary(),g=p.reference.time_grid;g.step_seconds_decimal='0.000001';g.step_microseconds=1;
    g.end_utc=p.reference.input.end_utc='2026-10-01T00:00:00.123472Z';p.reference.last_confirmed.at=g.end_utc;
    p.summary.last_confirmed.time.at=g.end_utc;p.summary.last_confirmed.value.elapsed_seconds=0.000001*16;
    Object.assign(p.summary.manifest.numerical,{step_seconds:0.000001,duration_seconds:0.000001*16});
    expect(decodeGreenhouseVentilationResponse(p,lookup(p))).toEqual(p);
    g.step_seconds_decimal='1e-06';expect(decodeGreenhouseVentilationResponse(p,lookup(p))).toEqual(p);
    g.end_utc=p.reference.input.end_utc='2026-10-01T00:00:00.123473Z';expect(()=>decodeGreenhouseVentilationResponse(p,lookup(p))).toThrow(ApiError);
  });
  it.each(['continuation','time'])('binds the exposed %s dependency to its model/time identity',field=>{
    const p=summary();p.reference.code.server_dependency_sha256[field]='a'.repeat(64);
    expect(()=>decodeGreenhouseVentilationResponse(p,lookup(p))).toThrow(ApiError);
  });
  it('requires own lookup fields before issuing a request',async()=>{
    const inherited=Object.assign(Object.create({crop_id:pick.crop_id}),pick);delete inherited.crop_id;inherited.extra=true;
    expect(validGreenhouseVentilationLookup(inherited)).toBe(false);
    const request=provider();await expect(createGreenhouseVentilationReplayApi(request).greenhouseVentilationSummary(inherited)).rejects.toBeInstanceOf(ApiError);
    expect(request).not.toHaveBeenCalled();
  });
});

describe('joint typed authenticated requests',()=>{
  it('adds the new reader to the existing no-store API and preserves requested identity',async()=>{
    const p=samples(),fetcher=vi.fn<typeof fetch>(async()=>ready(p));const api=createApi('owned-synthetic-token-'+'x'.repeat(32),fetcher);
    expect(await api.greenhouseVentilationPage(pick,{kind:'samples',offset:0,limit:64},{summary:original})).toEqual(p);
    const [path,init]=fetcher.mock.calls[0]!,url=new URL(String(path),'https://localhost');
    expect(decodeURIComponent(url.pathname)).toBe('/v1/crop-greenhouse-ventilation-research-results/'+pick.result_id);
    expect(Object.fromEntries(url.searchParams)).toEqual({...Object.fromEntries(FARM_PICK()),view:'samples',offset:'0',limit:'64'});
    expect(init).toMatchObject({method:'GET',cache:'no-store',credentials:'omit',redirect:'error'});
    expect((init?.headers as Record<string,string>).authorization).toContain('Bearer ');
    expect(api).toHaveProperty('calculationCycleCropSummary');
  });
  it.each([401,403,404,422,503])('preserves server refusal %s',async status=>{
    const api=createApi('owned-synthetic-token-'+'x'.repeat(32),async()=>new Response('{}',{status,headers:{'content-type':'application/json'}}));
    await expect(api.greenhouseVentilationSummary(pick)).rejects.toBeInstanceOf(ApiError);
  });
  it('rejects responses over 2MiB through the actual common transport',async()=>{
    const api=createApi('owned-synthetic-token-'+'x'.repeat(32),async()=>new Response(' '.repeat(2*1024*1024+1),{headers:{'content-type':'application/json'}}));
    await expect(api.greenhouseVentilationSummary(pick)).rejects.toMatchObject({code:'response_rejected'});
  });
  it.each(['lookup','query','summary','abort'] as const)('withholds a late reply after %s changes',async fault=>{
    const wait=deferred<unknown>(),request=vi.fn(()=>wait.promise),api=createGreenhouseVentilationReplayApi(request);
    const select={...pick},q={kind:'samples' as const,offset:0,limit:64},s=summary() as GreenhouseVentilationSummaryResponse,abort=new AbortController();
    const pending=api.greenhouseVentilationPage(select,q,{summary:s,signal:abort.signal});
    if(fault==='lookup')select.crop_id='other';if(fault==='query')q.offset=1;
    if(fault==='summary')(s as any).reference.payload_sha256='a'.repeat(64);if(fault==='abort')abort.abort();
    wait.release(samples());await expect(pending).rejects.toBeInstanceOf(ApiError);
    expect(request).toHaveBeenCalledTimes(1);
  });
  it('rejects concurrent calls and recovers after a failed request',async()=>{
    const wait=deferred<unknown>(),request=vi.fn(()=>wait.promise),api=createGreenhouseVentilationReplayApi(request);
    const pending=api.greenhouseVentilationSummary(pick);await expect(api.greenhouseVentilationSummary(pick)).rejects.toBeInstanceOf(ApiError);
    wait.release({});await expect(pending).rejects.toBeInstanceOf(ApiError);
    request.mockImplementation(async()=>summary());expect(await api.greenhouseVentilationSummary(pick)).toEqual(original);
  });
  it.each(['kind','offset','limit','extra','summary','summary-null','summary-false','aborted'])('rejects invalid %s before requests',async fault=>{
    const request=provider(),api=createGreenhouseVentilationReplayApi(request),q:any={kind:'samples',offset:0,limit:64};const options:any={};
    if(fault==='kind')q.kind='summary';if(fault==='offset')q.offset=513;if(fault==='limit')q.limit=65;if(fault==='extra')q.unknown=true;
    if(fault==='summary')options.summary=held;if(fault==='aborted'){const c=new AbortController();c.abort();options.signal=c.signal;}
    if(fault==='summary-null')options.summary=null;if(fault==='summary-false')options.summary=false;
    await expect(api.greenhouseVentilationPage(pick,q,options)).rejects.toBeInstanceOf(ApiError);expect(request).not.toHaveBeenCalled();
  });
  it.each(['batch_id','zone_id','recorded_at','payload_sha256','source_sha256','model','time_grid','status'])('rejects foreign page %s',async fault=>{
    const p=samples();if(fault==='batch_id'||fault==='zone_id')p.farm[fault]='foreign';
    if(fault==='recorded_at')p.recorded_at='2026-10-09T00:00:00.123456Z';if(fault==='payload_sha256')p.reference.payload_sha256='a'.repeat(64);
    if(fault==='source_sha256')p.reference.input.source_sha256='a'.repeat(64);if(fault==='model')p.reference.model.driver_code_sha256='a'.repeat(64);
    if(fault==='time_grid')p.reference.time_grid.time_code_sha256='a'.repeat(64);if(fault==='status')p.reference.artifact.status='hold';
    const api=createGreenhouseVentilationReplayApi(async()=>p);await expect(api.greenhouseVentilationPage(pick,{kind:'samples',offset:0,limit:64},{summary:original})).rejects.toBeInstanceOf(ApiError);
  });
});
function FARM_PICK(){return Object.entries(pick).filter(([k])=>k!=='result_id');}

describe('joint bounded iteration',()=>{
  it.each(['samples','events'] as const)('walks original %s with one-record pages and exact completion',async kind=>{
    const request=provider(),api=createGreenhouseVentilationReplayApi(request),iter=api.greenhouseVentilationPages(pick,kind,{limit:1});
    const rows=[];let result=await iter.next();while(!result.done){rows.push(...result.value.page.records);result=await iter.next();}
    expect(rows).toEqual(fixture.completed[kind==='samples'?1:2].page.records);
    expect(result.value).toEqual({kind,count:rows.length,total:rows.length,complete:true});expect(request).toHaveBeenCalledTimes(rows.length+1);
  });
  it.each(['samples','events'] as const)('supports a terminal empty %s page',async kind=>{
    const total=original.reference.artifact[kind==='samples'?'sample_count':'event_count'];const api=createGreenhouseVentilationReplayApi(provider());
    const p=await api.greenhouseVentilationPage(pick,{kind,offset:total,limit:1},{summary:original});expect(p.page.records).toEqual([]);expect(p.page.next_offset).toBeNull();
  });
  it('never reports completion when the consumer stops early',async()=>{
    const request=provider(),iter=createGreenhouseVentilationReplayApi(request).greenhouseVentilationPages(pick,'samples',{limit:1});
    expect((await iter.next()).done).toBe(false);expect(await iter.return(undefined)).toEqual({done:true,value:undefined});expect(request).toHaveBeenCalledTimes(2);
  });
  it('checks cancellation between yielded pages',async()=>{
    const request=provider(),abort=new AbortController(),iter=createGreenhouseVentilationReplayApi(request).greenhouseVentilationPages(pick,'samples',{limit:1,signal:abort.signal});
    await iter.next();abort.abort();await expect(iter.next()).rejects.toMatchObject({code:'request_canceled'});expect(request).toHaveBeenCalledTimes(2);
  });
  it('rejects a duplicate step across page boundaries',async()=>{
    const base=provider(),request=vi.fn(async(path:string)=>{const p=await base(path);if(p.page?.offset===1)p.page.records[0]=samples().page.records[0];return p;});
    const iter=createGreenhouseVentilationReplayApi(request).greenhouseVentilationPages(pick,'samples',{limit:1});await iter.next();await expect(iter.next()).rejects.toBeInstanceOf(ApiError);
  });
  it('rejects summary mutation by the summary callback before requesting pages',async()=>{
    const request=provider(),iter=createGreenhouseVentilationReplayApi(request).greenhouseVentilationPages(pick,'samples',{
      onSummary(s){(s as any).reference.payload_sha256='a'.repeat(64);}});
    await expect(iter.next()).rejects.toBeInstanceOf(ApiError);expect(request).toHaveBeenCalledTimes(1);
  });
  it('uses no mutable global result selection',()=>{
    expect(validGreenhouseVentilationLookup(pick)).toBe(true);expect(validGreenhouseVentilationLookup({...pick,tenant_id:'foreign'})).toBe(false);
  });
});


describe('current-stage ventilation original fields',()=>{
  it('retains the composed manifest policy separately from the underlying crop policy',()=>{
    for(const rows of [fixture.completed,fixture.hold]){
      const p=rows[0];expect(p.summary.manifest.policy_sha256).not.toBe(p.reference.model.policy_sha256);
      expect(decodeGreenhouseVentilationResponse(p,lookup(p))).toEqual(p);
    }
  });
  it.each(['diagnostic-missing','diagnostic-extra','input-hash','density-unit','density-NaN','forcing-unit','forcing-extra',
    'latent-unit','ledger-missing','ledger-unit','partition-missing','partition-residual','inner-stage','event-diagnostic-missing'])
    ('rejects %s without adapting it to the older version',fault=>{
      const p:Raw=fault==='inner-stage'?structuredClone(held):fault.startsWith('event-')?events():samples();
      const value=p.page?.records[0]?.value,d=value?.ventilation;
      if(fault==='diagnostic-missing')delete value.ventilation;
      if(fault==='diagnostic-extra')d.estimated_yield=1;
      if(fault==='input-hash')d.input_sha256='bad';
      if(fault==='density-unit')d.derived.indoor_vapor_density.unit='kg_water';
      if(fault==='density-NaN')d.derived.outdoor_vapor_density.value=NaN;
      if(fault==='forcing-unit')d.forcing_contribution.air_external_sensible_heat.unit='J/m2_floor';
      if(fault==='forcing-extra')d.forcing_contribution.fan_power={value:1,unit:'W'};
      if(fault==='latent-unit')d.latent_energy.unit='J/m2_floor';
      if(fault==='ledger-missing')delete value.integrated_transfers.ventilation_latent_energy;
      if(fault==='ledger-unit')value.integrated_transfers.ventilation_vapor.unit='kg_water/m3';
      if(fault==='partition-missing')delete value.balance_budgets.ventilation_sensible_partition;
      if(fault==='partition-residual')value.balance_residuals.ventilation_latent_partition.value=1e10;
      if(fault==='inner-stage')p.summary.hold.inner_failed_stage='interpolated';
      if(fault==='event-diagnostic-missing')delete value.ventilation_after;
      expect(()=>decodeGreenhouseVentilationResponse(p,lookup(p))).toThrow(ApiError);
    });
  it('keeps all three ventilation ledgers, ten residuals and event diagnostics in their original units',()=>{
    for(const rows of [fixture.completed,fixture.hold])for(const raw of rows){
      const value=decodeGreenhouseVentilationResponse(raw,lookup(raw));expect(value).toEqual(raw);
      if(value.page?.kind==='samples')for(const row of value.page.records){
        expect(Object.keys(row.value.integrated_transfers)).toHaveLength(25);
        expect(Object.keys(row.value.balance_residuals)).toHaveLength(10);
        expect(row.value.ventilation.latent_energy.unit).toBe('W/m2_floor');
      }
      if(value.page?.kind==='events')for(const row of value.page.records)expect(row.value.ventilation_after).toEqual(
        raw.page.records.find((r:Raw)=>r.time.step_index===row.time.step_index).value.ventilation_after);
    }
  });
});
