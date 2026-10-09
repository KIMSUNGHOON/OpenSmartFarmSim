import { closed,need,object } from './api-validation';
import { decodeCalculationCycleCropResponse,matchCalculationCycleCropPage,
  type CalculationCycleCropSummaryResponse,type CalculationCycleCropPageResponse } from './calculationCycleCropReplay';
import { decodeHarvestReplayResponse,matchHarvestReplayPage,
  type HarvestSummaryResponse,type HarvestPageResponse,type HarvestRow } from './harvestReplay';
import { type StartupCropSample } from './startupCropReplay';
import { utcMicroseconds } from './coupledCropReplay';

export type HarvestGrowthInput=Readonly<{crop_summary:CalculationCycleCropSummaryResponse;
  sample_page:CalculationCycleCropPageResponse|null;harvest_summary:HarvestSummaryResponse;harvest_page:HarvestPageResponse}>;
export type HarvestGrowthFrame=Readonly<{index:number;at:string;sample:StartupCropSample}>;
export type HarvestGrowthRow=Readonly<{index:number;row:HarvestRow;at:string;
  frame_status:'same_utc_stored_sample'|'outside_loaded_samples';frame:HarvestGrowthFrame|null;
  interval:Readonly<{start:HarvestGrowthFrame|null;end:HarvestGrowthFrame|null}>|null}>;
type Range=Readonly<{offset:number;count:number;total:number;partial:boolean}>;

export function matchHarvestGrowthSummary(crop:CalculationCycleCropSummaryResponse,harvest:HarvestSummaryResponse){
  need(object(crop)&&object(harvest));
  const cropLookup={...crop.farm,result_id:crop.result_id},harvestLookup={...harvest.farm,result_id:harvest.result_id};
  need(decodeCalculationCycleCropResponse(crop,cropLookup).summary!==null);
  need(decodeHarvestReplayResponse(harvest,harvestLookup).summary!==null);
  const source=harvest.reference.source,ref=crop.reference;
  for(const key of ['scenario_id','scenario_revision','registration_sha256','crop_id'] as const)
    need(crop.farm[key]===harvest.farm[key]);
  need(harvest.reference.parent_result_id===crop.result_id&&source.result_id===crop.result_id
    &&source.payload_sha256===ref.payload_sha256&&source.input_root_sha256===ref.input_root_sha256
    &&source.artifact_sha256===ref.artifact_sha256&&source.math_manifest_sha256===ref.context_sha256
    &&source.source_status===ref.status);
}

export function bindHarvestGrowthWindow(input:HarvestGrowthInput){
  need(object(input));closed(input,['crop_summary','sample_page','harvest_summary','harvest_page']);
  const {crop_summary:crop,sample_page:samplePage,harvest_summary:harvest,harvest_page:harvestPage}=input;
  matchHarvestGrowthSummary(crop,harvest);
  const cropLookup={...crop.farm,result_id:crop.result_id},harvestLookup={...harvest.farm,result_id:harvest.result_id};
  need(decodeHarvestReplayResponse(harvestPage,harvestLookup).page!==null);
  matchHarvestReplayPage(harvest,harvestPage);
  const source=harvest.reference.source,ref=crop.reference;
  const frames:HarvestGrowthFrame[]=[];
  let sampleRange:Range|null=null;
  if(samplePage!==null){
    need(decodeCalculationCycleCropResponse(samplePage,cropLookup).page!==null);
    matchCalculationCycleCropPage(crop,samplePage);need(samplePage.page.kind==='samples');
    const page=samplePage.page;
    for(const [i,sample] of page.records.entries())frames.push({index:page.offset+i,at:sample.at,sample});
    sampleRange=range(page.offset,frames.length,page.total);
  }
  const byTime=new Map(frames.map(frame=>[frame.at,frame]));
  const byIndex=new Map(frames.map(frame=>[frame.index,frame]));
  const first=frames[0],last=frames.at(-1);
  function endpoint(index:number,at:string):HarvestGrowthFrame|null{
    need(index<ref.sample_count);
    const frame=byIndex.get(index)??null;
    if(frame)need(frame.at===at);
    if(first&&last){
      if(at<first.at)need(index<first.index);
      else if(at>last.at)need(index>last.index);
      else need(frame!==null);
    }
    return frame;
  }
  const confirmedEnd=crop.summary.hold===null?ref.end_utc:crop.summary.hold.last_confirmed?.at??null;
  const startAt=utcMicroseconds(ref.start_utc),confirmedAt=confirmedEnd===null?null:utcMicroseconds(confirmedEnd);
  const rows:HarvestGrowthRow[]=harvestPage.page.records.map((row,i)=>{
    const removal=row.mass.removal;
    need(confirmedAt!==null&&utcMicroseconds(removal.start_at)>=startAt&&utcMicroseconds(removal.end_at)<=confirmedAt);
    let interval:HarvestGrowthRow['interval']=null,frame:HarvestGrowthFrame|null;
    if(removal.kind==='model_terminal_outflow'){
      const [start,end]=removal.position.samples;
      interval={start:endpoint(start,removal.start_at),end:endpoint(end,removal.end_at)};frame=interval.end;
    }else{
      need(removal.position.event<ref.event_count);frame=byTime.get(removal.end_at)??null;
    }
    return {index:harvestPage.page.offset+i,row,at:removal.end_at,interval,frame,
      frame_status:frame?'same_utc_stored_sample':'outside_loaded_samples'};
  });
  return {crop_result_id:crop.result_id,harvest_result_id:harvest.result_id,farm:crop.farm,
    source_status:source.source_status,scope:'software_research_only' as const,gates:'not_assessed' as const,
    rights_or_gate_approval:false as const,sample_range:sampleRange,
    harvest_range:range(harvestPage.page.offset,rows.length,harvestPage.page.total),rows,
    entire_stored_harvest_summary:harvest.summary};
}
function range(offset:number,count:number,total:number):Range{
  return {offset,count,total,partial:offset!==0||count!==total};
}
