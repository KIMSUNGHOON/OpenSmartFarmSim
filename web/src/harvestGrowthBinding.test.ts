import { readFileSync } from 'node:fs';
import { describe,it,expect } from 'vitest';
import { ApiError } from './api-validation';
import { decodeCalculationCycleCropResponse } from './calculationCycleCropReplay';
import { decodeHarvestReplayResponse } from './harvestReplay';
import { bindHarvestGrowthWindow,type HarvestGrowthInput } from './harvestGrowthBinding';

const crops=JSON.parse(readFileSync(new URL('../e2e/calculation-cycle-crop-prefix-recorded-responses.json',import.meta.url),'utf8'));
const harvests=JSON.parse(readFileSync(new URL('../e2e/harvest-recorded-responses.json',import.meta.url),'utf8'));
const lookup=(p:any)=>({...p.farm,result_id:p.result_id});
// Metadata and times are deliberately rebound for software shape tests, not an observed joint run.
function input():HarvestGrowthInput{
  const harvest=JSON.parse(harvests.bodies_raw_utf8.summary),harvestPage=JSON.parse(harvests.bodies_raw_utf8.records);
  const crop=structuredClone(crops.long[0]),ref=crop.reference,source=harvest.reference.source;
  crop.result_id=source.result_id;crop.farm=structuredClone(harvest.farm);
  Object.assign(ref,{payload_sha256:source.payload_sha256,input_root_sha256:source.input_root_sha256,
    artifact_sha256:source.artifact_sha256,artifact_ref:'crop-cycle-verified-artifact-v1:'+source.artifact_sha256,
    context_sha256:source.math_manifest_sha256,start_utc:'2026-10-01T00:00:00Z',end_utc:'2026-10-01T00:02:00Z',
    sample_count:3,event_count:4,steps:120,planned_steps:120});
  ref.input_validation.context_sha256=source.math_manifest_sha256;
  crop.summary.manifest.input_root_sha256=source.input_root_sha256;crop.summary.manifest.planned_steps=120;
  const original=crops.long.find((p:any)=>p.page?.kind==='samples').page.records;
  const samplePage={...structuredClone(crop),summary:null,page:{kind:'samples',offset:0,limit:3,total:3,next_offset:null,
    records:original.slice(0,3).map((sample:any,i:number)=>({...structuredClone(sample),at:`2026-10-01T00:0${i}:00Z`}))}};
  const c=decodeCalculationCycleCropResponse(crop,lookup(crop)),p=decodeCalculationCycleCropResponse(samplePage,lookup(crop));
  const h=decodeHarvestReplayResponse(harvest,lookup(harvest)),hp=decodeHarvestReplayResponse(harvestPage,lookup(harvest));
  if(c.summary===null||p.page===null||h.summary===null||hp.page===null)throw new Error('expected summaries and pages');
  return {crop_summary:c,sample_page:p,harvest_summary:h,harvest_page:hp};
}
function cropField(v:any,key:string,value:unknown){v.crop_summary.reference[key]=value;v.sample_page.reference[key]=value;}
function setStatus(v:any){
  function visit(x:any){if(x&&typeof x==='object')for(const [key,value] of Object.entries(x)){
    if(key==='source_status')x[key]='hold';else visit(value);}}
  visit(v);cropField(v,'status','hold');cropField(v,'steps',119);cropField(v,'end_utc','2026-10-01T00:03:00Z');
  v.crop_summary.summary.status='hold';v.crop_summary.summary.hold={reason_code:'NUMERIC_HOLD',phase:'step-end',
    at:'2026-10-01T00:03:00Z',time_meaning:'solver_evaluation_time',last_confirmed:{...structuredClone(v.sample_page.page.records[2]),phase:'step-end'}};
}
function individuallyValid(v:HarvestGrowthInput){
  decodeCalculationCycleCropResponse(v.crop_summary,lookup(v.crop_summary));
  if(v.sample_page)decodeCalculationCycleCropResponse(v.sample_page,lookup(v.crop_summary));
  decodeHarvestReplayResponse(v.harvest_summary,lookup(v.harvest_summary));
  decodeHarvestReplayResponse(v.harvest_page,lookup(v.harvest_summary));
}

describe('bounded stored harvest/growth binding',()=>{
  it('keeps source quantities and exact same-UTC stored frames without changing either input',()=>{
    const v=input(),before=structuredClone(v),bound=bindHarvestGrowthWindow(v);
    expect(v).toEqual(before);expect(bound.crop_result_id).toBe(v.crop_summary.result_id);
    expect(bound.harvest_result_id).toBe(v.harvest_summary.result_id);expect(bound.farm).toEqual(v.crop_summary.farm);
    expect(bound.rows.map(r=>r.frame?.index??null)).toEqual([0,1,1,null,2,2]);
    expect(bound.rows[1]?.interval?.start?.index).toBe(0);expect(bound.rows[1]?.interval?.end?.index).toBe(1);
    expect(bound.rows[4]?.interval?.start?.index).toBe(1);expect(bound.rows[4]?.interval?.end?.index).toBe(2);
    for(const [i,b] of bound.rows.entries()){
      expect(b.row).toBe(v.harvest_page.page.records[i]);
      if(b.frame){expect(b.frame.at).toBe(b.at);expect(b.frame.sample).toBe(v.sample_page!.page.records[b.frame.index]);}
    }
    expect(bound.entire_stored_harvest_summary).toBe(v.harvest_summary.summary);
    expect(bound).toMatchObject({scope:'software_research_only',gates:'not_assessed',rights_or_gate_approval:false});
    expect(bound.harvest_range).toEqual({offset:0,count:6,total:6,partial:false});
  });
  it('does not interpolate the unsampled event or assert it is absent from the whole result',()=>{
    const bound=bindHarvestGrowthWindow(input()),event=bound.rows[3]!;
    expect(event.at).toBe('2026-10-01T00:01:30Z');expect(event.frame).toBeNull();expect(event.interval).toBeNull();
    expect(event.frame_status).toBe('outside_loaded_samples');
  });
  it('separates the current partial page from whole stored totals and comparisons',()=>{
    const v=input(),split=decodeHarvestReplayResponse(JSON.parse(harvests.bodies_raw_utf8['split-0']),lookup(v.harvest_summary));
    if(split.page===null)throw new Error('expected split page');
    const bound=bindHarvestGrowthWindow({...v,harvest_page:split});
    expect(bound.rows).toHaveLength(3);expect(bound.harvest_range).toEqual({offset:0,count:3,total:6,partial:true});
    expect(bound.entire_stored_harvest_summary).toEqual(v.harvest_summary.summary);
    expect(bound.entire_stored_harvest_summary.observation_comparisons[0]?.status).toBe('compared_synthetic_fixture');
  });
  it('uses global sample indices in a partial growth window and keeps unavailable endpoints null',()=>{
    const v:any=input();v.sample_page.page={kind:'samples',offset:1,limit:1,total:3,next_offset:2,records:[v.sample_page.page.records[1]]};
    const bound=bindHarvestGrowthWindow(v);
    expect(bound.sample_range).toEqual({offset:1,count:1,total:3,partial:true});
    expect(bound.rows.map(r=>r.frame?.index??null)).toEqual([null,1,1,null,null,null]);
    expect(bound.rows[1]?.interval?.start).toBeNull();expect(bound.rows[4]?.interval?.start?.index).toBe(1);
  });
  it('has no frames when no growth page has been read',()=>{
    const bound=bindHarvestGrowthWindow({...input(),sample_page:null});
    expect(bound.sample_range).toBeNull();expect(bound.rows.every(r=>r.frame===null&&r.frame_status==='outside_loaded_samples')).toBe(true);
  });
  it('accepts empty end pages without collecting or reconstructing records',()=>{
    const v:any=input();v.sample_page.page={kind:'samples',offset:3,limit:3,total:3,next_offset:null,records:[]};
    v.harvest_page=JSON.parse(harvests.bodies_raw_utf8['empty-end']);
    const bound=bindHarvestGrowthWindow(v);expect(bound.rows).toEqual([]);
    expect(bound.sample_range).toEqual({offset:3,count:0,total:3,partial:true});
    expect(bound.harvest_range).toEqual({offset:6,count:0,total:6,partial:true});
  });
  it('preserves a held confirmed past and never upgrades it',()=>{
    const v=input();setStatus(v);individuallyValid(v);const bound=bindHarvestGrowthWindow(v);
    expect(bound.source_status).toBe('hold');expect(bound.rights_or_gate_approval).toBe(false);expect(bound.rows).toHaveLength(6);
  });
  it('compares a fractional confirmed solver time without dropping a whole-second stored endpoint',()=>{
    const v:any=input();setStatus(v);v.crop_summary.summary.hold.last_confirmed.at='2026-10-01T00:02:00.500000Z';
    individuallyValid(v);expect(bindHarvestGrowthWindow(v).rows[4]?.frame?.at).toBe('2026-10-01T00:02:00Z');
  });
  const joins:Record<string,(v:any)=>void>={
    parent:v=>{v.crop_summary.result_id='crop-cycle-verified-result-v1:'+'1'.repeat(64);v.sample_page.result_id=v.crop_summary.result_id;},
    scenario:v=>{v.crop_summary.farm.scenario_id='other';v.sample_page.farm.scenario_id='other';},
    revision:v=>{v.crop_summary.farm.scenario_revision='other';v.sample_page.farm.scenario_revision='other';},
    registration:v=>{v.crop_summary.farm.registration_sha256='1'.repeat(64);v.sample_page.farm.registration_sha256='1'.repeat(64);},
    crop:v=>{v.crop_summary.farm.crop_id='other';v.sample_page.farm.crop_id='other';},
    payload:v=>cropField(v,'payload_sha256','1'.repeat(64)),
    inputRoot:v=>{cropField(v,'input_root_sha256','1'.repeat(64));v.crop_summary.summary.manifest.input_root_sha256='1'.repeat(64);},
    artifact:v=>{cropField(v,'artifact_sha256','1'.repeat(64));cropField(v,'artifact_ref','crop-cycle-verified-artifact-v1:'+'1'.repeat(64));},
    manifest:v=>{cropField(v,'context_sha256','1'.repeat(64));v.crop_summary.reference.input_validation.context_sha256='1'.repeat(64);v.sample_page.reference.input_validation.context_sha256='1'.repeat(64);},
    status:v=>{setStatus(v);function visit(x:any){if(x&&typeof x==='object')for(const [k,val] of Object.entries(x)){if(k==='source_status')x[k]='completed';else visit(val);}}visit(v.harvest_summary);visit(v.harvest_page);},
  };
  it.each(Object.keys(joins))('rejects independently valid but unrelated %s',key=>{
    const v=input();joins[key]!(v);individuallyValid(v);expect(()=>bindHarvestGrowthWindow(v)).toThrow(ApiError);
  });
  const faults:Record<string,(v:any)=>void>={
    summaryPageIdentity:v=>{v.sample_page.recorded_at='2026-10-02T00:00:00Z';},
    harvestPageIdentity:v=>{v.harvest_page.recorded_at='2026-10-02T00:00:00Z';},
    harvestRule:v=>{v.harvest_page.page.records[0].allocations[0].assignment_id='not-declared';},
    terminalTime:v=>{v.sample_page.page.records[1].at='2026-10-01T00:00:59Z';},
    terminalIndex:v=>{v.harvest_page.page.records[1].mass.removal.position.samples=[1,2];},
    terminalOutsideCount:v=>{cropField(v,'sample_count',2);v.sample_page.page.total=2;v.sample_page.page.records.pop();},
    eventOutsideCount:v=>cropField(v,'event_count',3),
    eventBeforeCycle:v=>{cropField(v,'start_utc','2026-10-01T00:00:01Z');v.sample_page=null;},
    beyondConfirmed:v=>{setStatus(v);v.crop_summary.summary.hold.last_confirmed={...structuredClone(v.sample_page.page.records[1]),phase:'step-end'};},
    noConfirmedPast:v=>{setStatus(v);v.crop_summary.summary.hold.last_confirmed=null;},
    eventPage:v=>{const event=structuredClone(crops.long.find((p:any)=>p.page?.kind==='events').page.records[0]);
      event.at=v.crop_summary.reference.start_utc;v.sample_page={...structuredClone(v.crop_summary),summary:null,
        page:{kind:'events',offset:0,limit:1,total:4,next_offset:1,records:[event]}};},
    inputExtra:v=>{v.nearest_frame=true;},
    rowClaim:v=>{v.harvest_page.page.records[0].rights_or_gate_approval=true;},
    sampleQuantity:v=>{v.sample_page.page.records[0].lai.value=Infinity;},
  };
  it.each(Object.keys(faults))('refuses %s before producing a frame or table',key=>{
    const v=input();faults[key]!(v);
    if(key==='eventBeforeCycle'||key==='eventPage')individuallyValid(v);
    expect(()=>bindHarvestGrowthWindow(v)).toThrow(ApiError);
  });
  it('rejects a conflicting time inside a loaded index range even without an exact matching timestamp',()=>{
    const v:any=input();v.sample_page.page={kind:'samples',offset:0,limit:1,total:3,next_offset:1,records:[v.sample_page.page.records[1]]};
    individuallyValid(v);expect(()=>bindHarvestGrowthWindow(v)).toThrow(ApiError);
  });
  it('revalidates caller mutations on every binding without retaining an earlier result',()=>{
    const v:any=input();expect(bindHarvestGrowthWindow(v).rows).toHaveLength(6);
    v.harvest_page.page.records[0].mass.removal.source.payload_sha256='1'.repeat(64);
    expect(()=>bindHarvestGrowthWindow(v)).toThrow(ApiError);
  });
});
