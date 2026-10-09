import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { describe,it,expect,vi } from 'vitest';
import { ApiError,createApi } from './api';
import { decodeHarvestReplayResponse,createHarvestReplayApi } from './harvestReplay';

const fixture=JSON.parse(readFileSync(new URL('../e2e/harvest-recorded-responses.json',import.meta.url),'utf8'));
const body=(name='records')=>JSON.parse(fixture.bodies_raw_utf8[name]);
const selection={result_id:body().result_id,...body().farm};

describe('registered harvest replay SDK',()=>{
  it('preserves the accepted actual HTTPS bodies and original nested quantities',()=>{
    for(const check of fixture.actual_HTTPS_body_checks){
      const raw=fixture.bodies_raw_utf8[check.label];
      expect(createHash('sha256').update(raw).digest('hex')).toBe(check.body_sha256);
      expect(Buffer.byteLength(raw)).toBe(check.bytes);
      const value=JSON.parse(raw);
      expect(decodeHarvestReplayResponse(value,selection)).toBe(value);
    }
    expect(body().page.records).toHaveLength(6);
    expect(body('summary').summary.observation_comparisons[0].status).toBe('compared_synthetic_fixture');
    expect(body().reference.gates).toBe('not_assessed');
    expect(body().reference.rights_or_gate_approval).toBe(false);
  });
  const faults:Record<string,(v:any)=>void>={
    unknown:v=>v.extra=1,oldSchema:v=>v.schema_version='crop-cycle-replay-v1',farm:v=>v.farm.crop_id='other',
    recordedTime:v=>v.recorded_at='2026-02-30T00:00:00Z',scope:v=>v.reference.scope='production',
    approval:v=>v.reference.rights_or_gate_approval=true,gates:v=>v.reference.gates='G1',
    parent:v=>v.reference.parent_result_id='crop-cycle-verified-result-v1:'+'0'.repeat(64),
    sourceExtra:v=>v.reference.source.private_key='no',hash:v=>v.reference.payload_sha256='A'.repeat(64),
    dependency:v=>v.reference.query_dependency_sha256.registry='0'.repeat(64),bothViews:v=>v.summary=body('summary').summary,
    fractionalOffset:v=>v.page.offset=.5,limit:v=>v.page.limit=65,total:v=>v.page.total++,next:v=>v.page.next_offset=3,
    short:v=>v.page.records.pop(),reversed:v=>v.page.records.reverse(),duplicate:v=>v.page.records[1]=v.page.records[0],
    nestedExtra:v=>v.page.records[0].mass.parameters.population.fresh_kg=1,
    origin:v=>v.page.records[0].mass.parameters.origin='measured',
    rowApproval:v=>v.page.records[0].rights_or_gate_approval=1,codeMix:v=>v.page.records[0].mass.code_sha256='0'.repeat(64),
    rowSource:v=>v.page.records[0].mass.removal.source.input_root_sha256='0'.repeat(64),
    parameter:v=>v.page.records[0].mass.parameter_sha256='0'.repeat(64),
    parameterRevision:v=>v.page.records[0].mass.parameters.revision='other',
    segment:v=>v.page.records[0].mass.parameters.segment.segment_id='other',
    coverage:v=>v.page.records[0].mass.parameters.segment.start_at='2026-10-01T00:01:00Z',
    dmc:v=>v.page.records[0].mass.parameters.segment.dmc.value=1.01,
    infinite:v=>v.page.records[0].mass.fresh_matter.value=Infinity,
    negative:v=>v.page.records[0].mass.dry_matter.value=-1,
    unit:v=>v.page.records[0].mass.fresh_matter.unit='kg',
    perEquivalent:v=>v.page.records[0].mass.fresh_mass_per_equivalent.value=null,
    cohorts:v=>v.page.records[0].mass.removal.cohorts.fruit_number.pop(),
    cohortSum:v=>v.page.records[0].mass.removal.cohorts.fruit_carbohydrate[0].value++,
    eventPosition:v=>v.page.records[0].mass.removal.position.event=.2,
    terminalPosition:v=>v.page.records[1].mass.removal.position.samples[1]=7,
    eventTime:v=>v.page.records[0].mass.removal.end_at='2026-10-01T00:00:01Z',
    fractionalUTC:v=>v.page.records[0].mass.removal.start_at='2026-10-01T00:00:00.1Z',
    fraction:v=>v.page.records[0].allocations[0].fraction.value='1.000000000000000001',
    fractionZero:v=>v.page.records[0].allocations[0].fraction.value='0.0',
    fractionSum:v=>v.page.records[0].allocations.pop(),
    unassigned:v=>v.page.records[0].unassigned.fraction.value=1,
    allocationName:v=>v.page.records[0].allocations[1].assignment_id=v.page.records[0].allocations[0].assignment_id,
    exactValue:v=>v.page.records[0].allocations[0].quantities.carbohydrate.value=.41,
    exactPortion:v=>{v.page.records[0].allocations[0].quantities.carbohydrate.value=.5;v.page.records[0].allocations[0].quantities.carbohydrate.exact={numerator:'1',denominator:'2'};},
    exactLeading:v=>v.page.records[0].allocations[0].quantities.carbohydrate.exact.numerator='02',
    exactDenominator:v=>v.page.records[0].allocations[0].quantities.carbohydrate.exact.denominator='0',
    exactReduced:v=>v.page.records[0].allocations[0].quantities.carbohydrate.exact={numerator:'4',denominator:'10'},
    exactHuge:v=>v.page.records[0].allocations[0].quantities.carbohydrate.exact.numerator='1'.repeat(2049),
  };
  it.each(Object.keys(faults))('rejects malformed or mixed %s',fault=>{
    const value=body();faults[fault]!(value);expect(()=>decodeHarvestReplayResponse(value,selection)).toThrow(ApiError);
  });
  const summaryFaults:Record<string,(v:any)=>void>={
    count:v=>v.summary.row_count++,chain:v=>v.summary.row_chain_sha256='0'.repeat(64),
    source:v=>v.summary.source.artifact_sha256='0'.repeat(64),allocation:v=>v.summary.allocation_sha256='0'.repeat(64),
    policy:v=>v.summary.allocation_parameters.policy='automatic_harvest',
    totalUnit:v=>v.summary.totals_by_kind_and_purpose.model_terminal_outflow.harvest.quantities.number.unit='fruit',
    totalZero:v=>v.summary.totals_by_kind_and_purpose.model_terminal_outflow.harvest.rows=0,
    totalOverRows:v=>v.summary.totals_by_kind_and_purpose.explicit_fruit_removal.unassigned.rows=7,
    duplicateRule:v=>v.summary.allocation_parameters.rules.push(v.summary.allocation_parameters.rules[0]),
    overlappingRule:v=>v.summary.allocation_parameters.rules[0].fraction.value='1',
    missingAssignment:v=>v.summary.allocation_parameters.observations[0].assignment_ids=['missing'],
    comparison:v=>v.summary.observation_comparisons[0].observed_minus_modeled.exact.numerator='1',
    comparisonMissing:v=>v.summary.observation_comparisons=[],
    incomplete:v=>v.summary.observation_comparisons[0].status='incomplete_selected_window',
    observationMix:v=>v.summary.observation_comparisons[0].observation.evidence_id='other',
  };
  it.each(Object.keys(summaryFaults))('rejects malformed summary %s',fault=>{
    const value=body('summary');summaryFaults[fault]!(value);expect(()=>decodeHarvestReplayResponse(value,selection)).toThrow(ApiError);
  });
  const roundingVectors:[string,string,number][]=[['1','10',.1],['0','1',0],
    [(2n**53n+1n).toString(),(2n**53n).toString(),1],
    [(2n**53n+3n).toString(),(2n**53n).toString(),1+2**-51],
    ['1',(2n**1074n).toString(),Number.MIN_VALUE],['3',(2n**1075n).toString(),2*Number.MIN_VALUE],
    [((2n**53n-1n)*2n**971n).toString(),'1',Number.MAX_VALUE],
    ['1'+'0'.repeat(400)+'1','1'+'0'.repeat(400),10]];
  it.each(roundingVectors)('accepts canonical exact Float64 rounding %s/%s',(numerator,denominator,value)=>{
    const v=body('summary');v.summary.totals_by_kind_and_purpose.model_terminal_outflow.harvest.quantities.fresh_matter={value,unit:'kg_FW/m2_floor',exact:{numerator,denominator}};
    expect(decodeHarvestReplayResponse(v,selection)).toBe(v);
  });
  it.each([['1',(2n**1075n).toString(),0],['1','10',.1+Number.EPSILON],
    [((2n**54n-1n)*2n**970n).toString(),'1',Number.MAX_VALUE]])('rejects underflow or wrong rounding %s/%s',(numerator,denominator,value)=>{
    const v=body('summary');v.summary.totals_by_kind_and_purpose.model_terminal_outflow.harvest.quantities.fresh_matter={value,unit:'kg_FW/m2_floor',exact:{numerator,denominator}};
    expect(()=>decodeHarvestReplayResponse(v,selection)).toThrow(ApiError);
  });
  it('preserves a valid negative observed-minus-modeled and an incomplete comparison',()=>{
    const v=body('summary'),comparison=v.summary.observation_comparisons[0];
    v.summary.allocation_parameters.observations[0].fresh_matter.value=0;
    comparison.observation.fresh_matter.value=0;
    comparison.observed_minus_modeled=structuredClone(comparison.modeled_fresh_matter);
    comparison.observed_minus_modeled.value=-comparison.observed_minus_modeled.value;
    comparison.observed_minus_modeled.exact.numerator='-'+comparison.observed_minus_modeled.exact.numerator;
    expect(decodeHarvestReplayResponse(v,selection)).toBe(v);
    comparison.status='incomplete_selected_window';comparison.modeled_fresh_matter=null;comparison.observed_minus_modeled=null;
    expect(decodeHarvestReplayResponse(v,selection)).toBe(v);
  });
  it('preserves hold source metadata without upgrading claims',()=>{
    const v=body('summary');v.reference.source.source_status='hold';v.summary.source.source_status='hold';
    v.summary.allocation_parameters.source.source_status='hold';expect(decodeHarvestReplayResponse(v,selection)).toBe(v);
  });
  const response=(name:string)=>new Response(fixture.bodies_raw_utf8[name],{headers:{'content-type':'application/json'}});
  it('connects the shared Bearer transport and reads split pages sequentially with no prefetch',async()=>{
    const pending=['summary','split-0','split-3'];let active=0,peak=0;
    const fetcher=vi.fn(async(path,init)=>{active++;peak=Math.max(peak,active);expect(init.headers.authorization).toBe('Bearer '+'t'.repeat(20));
      expect(init.cache).toBe('no-store');expect(init.credentials).toBe('omit');expect(init.redirect).toBe('error');
      const url=new URL(String(path),'https://localhost');expect(decodeURIComponent(url.pathname)).toBe('/v1/crop-harvest-research-results/'+selection.result_id);
      for(const k of ['scenario_id','scenario_revision','registration_sha256','crop_id'])expect(url.searchParams.get(k)).toBe(selection[k]);
      active--;return response(pending.shift()!);});
    const api=createApi('t'.repeat(20),fetcher),onSummary=vi.fn(),iter=api.harvestPages(selection,{limit:3,onSummary});
    expect(fetcher).not.toHaveBeenCalled();const first=await iter.next();expect(first.done).toBe(false);expect(fetcher).toHaveBeenCalledTimes(2);
    expect(onSummary).toHaveBeenCalledOnce();const second=await iter.next();expect(second.done).toBe(false);
    if(first.done||second.done)throw new Error('expected two data pages');
    expect(first.value.page.records.concat(second.value.page.records)).toEqual(body().page.records);
    expect(await iter.next()).toEqual({done:true,value:{kind:'records',count:6,total:6,complete:true}});
    expect(await iter.next()).toEqual({done:true,value:undefined});expect(fetcher).toHaveBeenCalledTimes(3);expect(peak).toBe(1);
  });
  it('uses the current timeout/byte limits and rejects concurrent reads until settlement',async()=>{
    let resolve!:(value:unknown)=>void;const request=vi.fn(()=>new Promise(r=>resolve=r));const api=createHarvestReplayApi(request);
    const first=api.harvestSummary(selection);await expect(api.harvestSummary(selection)).rejects.toThrow(ApiError);
    expect(request).toHaveBeenCalledTimes(1);expect(request.mock.calls[0]?.slice(1,6)).toEqual(['GET',undefined,200,2*1024*1024,30_000]);
    resolve(body('summary'));await first;const next=api.harvestSummary(selection);resolve(body('summary'));await next;
  });
  it('validates requested offset/limit and same summary provenance',async()=>{
    const request=vi.fn(async()=>body('split-0')),api=createHarvestReplayApi(request);
    await expect(api.harvestPage(selection,{offset:0,limit:3},{summary:body('summary')})).resolves.toEqual(body('split-0'));
    await expect(api.harvestPage(selection,{offset:3,limit:3})).rejects.toThrow(ApiError);
    const foreign=body('summary');foreign.reference.payload_sha256='0'.repeat(64);
    await expect(api.harvestPage(selection,{offset:0,limit:3},{summary:foreign})).rejects.toThrow(ApiError);
  });
  it.each(['lookup','query','summary'])('rejects %s mutation while a request is pending',async kind=>{
    let resolve!:(value:unknown)=>void;const api=createHarvestReplayApi(()=>new Promise(r=>resolve=r));
    const lookup={...selection},query={offset:0,limit:3},summary=body('summary');
    const pending=api.harvestPage(lookup,query,{summary});
    if(kind==='lookup')lookup.crop_id='changed';if(kind==='query')query.limit=4;if(kind==='summary')summary.reference.payload_sha256='0'.repeat(64);
    resolve(body('split-0'));await expect(pending).rejects.toThrow(ApiError);
  });
  it('honors cancellation before dispatch and after a late successful response',async()=>{
    const abort=new AbortController(),request=vi.fn(async()=>body('summary')),api=createHarvestReplayApi(request);abort.abort();
    await expect(api.harvestSummary(selection,abort.signal)).rejects.toMatchObject({code:'request_canceled'});expect(request).not.toHaveBeenCalled();
    const later=new AbortController(),late=createHarvestReplayApi(async()=>{later.abort();return body('summary');});
    await expect(late.harvestSummary(selection,later.signal)).rejects.toMatchObject({code:'request_canceled'});
  });
  it('releases a failed request and rejects mutated summaries from the callback',async()=>{
    const request=vi.fn().mockRejectedValueOnce(new ApiError('network_unresolved')).mockResolvedValue(body('summary'));
    const api=createHarvestReplayApi(request);await expect(api.harvestSummary(selection)).rejects.toMatchObject({code:'network_unresolved'});
    await expect(api.harvestSummary(selection)).resolves.toEqual(body('summary'));
    const iter=api.harvestPages(selection,{onSummary:s=>Object.assign(s.reference,{payload_sha256:'0'.repeat(64)})});
    await expect(iter.next()).rejects.toThrow(ApiError);expect(request).toHaveBeenCalledTimes(3);
  });
  it.each([401,403,404,422,503])('settles %s rights/availability errors without reporting completion',async status=>{
    const fetcher=vi.fn(async()=>new Response('',{status})),iter=createApi('t'.repeat(20),fetcher).harvestPages(selection);
    await expect(iter.next()).rejects.toMatchObject({status});expect(await iter.next()).toEqual({done:true,value:undefined});expect(fetcher).toHaveBeenCalledOnce();
  });
  it('stops after consumer return or cancellation without fetching another page',async()=>{
    const request=vi.fn(async()=>request.mock.calls.length===1?body('summary'):body('split-0'));
    const api=createHarvestReplayApi(request),iter=api.harvestPages(selection,{limit:3});await iter.next();await iter.return(undefined);await iter.next();expect(request).toHaveBeenCalledTimes(2);
    const abort=new AbortController(),other=api.harvestPages(selection,{limit:3,signal:abort.signal});
    request.mockImplementationOnce(async()=>body('summary'));request.mockImplementationOnce(async()=>body('split-0'));
    await other.next();abort.abort();await expect(other.next()).rejects.toMatchObject({code:'request_canceled'});expect(request).toHaveBeenCalledTimes(4);
  });
  it('refuses a page with reversed time across an otherwise valid page boundary',async()=>{
    const second=body('split-3');second.page.records[0]=body('records').page.records[0];
    const queue=[body('summary'),body('split-0'),second],request=vi.fn(async()=>queue.shift());
    const iter=createHarvestReplayApi(request).harvestPages(selection,{limit:3});await iter.next();await expect(iter.next()).rejects.toThrow(ApiError);
    expect(await iter.next()).toEqual({done:true,value:undefined});expect(request).toHaveBeenCalledTimes(3);
  });
  it('rejects consistent per-page mass revision changes across pages',async()=>{
    const second=body('split-3');for(const row of second.page.records)row.mass.parameters.revision='other';
    const queue=[body('summary'),body('split-0'),second],iter=createHarvestReplayApi(async()=>queue.shift()).harvestPages(selection,{limit:3});
    await iter.next();await expect(iter.next()).rejects.toThrow(ApiError);
  });
  it('keeps the validated boundary independent of consumer page object mutation',async()=>{
    const queue=[body('summary'),body('split-0'),body('split-3')],iter=createHarvestReplayApi(async()=>queue.shift()).harvestPages(selection,{limit:3});
    const first=await iter.next();if(first.done)throw new Error('expected data');
    Object.assign(first.value.page.records[2]!.mass.removal,{end_at:'2099-01-01T00:00:00Z'});
    expect((await iter.next()).done).toBe(false);
    expect(await iter.next()).toEqual({done:true,value:{kind:'records',count:6,total:6,complete:true}});
  });
  it('preserves empty final pages and completed zero-row format fixtures',async()=>{
    const api=createHarvestReplayApi(async()=>body('empty-end'));await expect(api.harvestPage(selection,{offset:6,limit:3},{summary:body('summary')})).resolves.toEqual(body('empty-end'));
    const summary=body('summary'),page=body('empty-end');summary.reference.row_count=0;summary.summary.row_count=0;page.reference.row_count=0;page.page.offset=0;page.page.total=0;
    for(const by of Object.values(summary.summary.totals_by_kind_and_purpose) as any[]){
      for(const total of Object.values(by) as any[]){total.rows=0;for(const q of Object.values(total.quantities) as any[]){q.value=0;q.exact={numerator:'0',denominator:'1'};}}}
    for(const comparison of summary.summary.observation_comparisons){comparison.status='incomplete_selected_window';comparison.modeled_fresh_matter=null;comparison.observed_minus_modeled=null;}
    const values=[summary,page],iter=createHarvestReplayApi(async()=>values.shift()).harvestPages(selection,{limit:3});
    expect((await iter.next()).done).toBe(false);expect(await iter.next()).toEqual({done:true,value:{kind:'records',count:0,total:0,complete:true}});
  });
});
