import { readFileSync } from 'node:fs';
import { decodeCycleCropResponse,type CycleCropSummaryResponse,type CycleCropPageResponse } from '../src/cycleCropReplay';
import type { StartupCropSample } from '../src/startupCropReplay';
import type { CoupledCropEvent } from '../src/coupledCropReplay';
type Dataset={summary:CycleCropSummaryResponse;samples:readonly StartupCropSample[];events:readonly CoupledCropEvent[];shape_only:boolean};
const raw=JSON.parse(readFileSync(new URL('./cycle-crop-recorded-responses.json',import.meta.url),'utf8'));
const decode=(v:Record<string,any>)=>decodeCycleCropResponse(v,{result_id:v.result_id,...v.farm});
export function cycleReference(kind:'long'|'empty-hold'|'empty-completed'|'past-hold'|'many'='long'):Dataset{
  const responses=raw[kind==='empty-hold'?'short':'long'].map(decode);
  let summary=structuredClone(responses.find((v:any)=>v.summary?.status===(kind==='empty-hold'?'hold':'completed'))) as CycleCropSummaryResponse;
  const pages=responses.filter((v:any)=>v.result_id===summary.result_id && v.page!==null) as CycleCropPageResponse[];
  let samples=pages.flatMap(v=>v.page.kind==='samples'?v.page.records:[]),events=pages.flatMap(v=>v.page.kind==='events'?v.page.records:[]);
  // These three shapes exercise presentation contracts; none runs the crop equations or has server custody.
  if(kind==='empty-completed'){samples=[];events=[];summary={...summary,reference:{...summary.reference,sample_count:0,event_count:0}};}
  if(kind==='past-hold'){
    samples=samples.slice(0,7);events=[];const confirmed=samples[6]!;
    summary={...summary,reference:{...summary.reference,status:'hold',steps:summary.reference.steps-1,sample_count:7,event_count:0},
      summary:{...summary.summary,status:'hold',hold:{reason_code:'NUMERIC_HOLD',phase:'rk4-k2',time_meaning:'solver_evaluation_time',
        at:confirmed.at.replace('Z','.500000Z'),last_confirmed:{...structuredClone(confirmed),at:confirmed.at.replace('Z','.250000Z'),phase:'step-end'}}}};
  }
  if(kind==='many'){
    const at=(i:number)=>new Date(Date.parse(summary.reference.start_utc)+i*1000).toISOString().replace('.000Z','Z');
    samples=Array.from({length:512},(_,i)=>({...structuredClone(samples[0]!),at:at(i)}));
    events=Array.from({length:128},(_,i)=>({...structuredClone(events[0]!),at:at(i)}));
    summary={...summary,reference:{...summary.reference,sample_count:512,event_count:128}};
  }
  decode(summary);return {summary,samples,events,shape_only:!['long','empty-hold'].includes(kind)};
}
export function cyclePage(data:Dataset,kind:'samples'|'events',offset:number,limit:number,shortCount?:number):CycleCropPageResponse{
  const rows=kind==='samples'?data.samples:data.events,count=Math.min(shortCount??limit,limit,rows.length-offset),next=offset+count;
  return decode({...data.summary,summary:null,page:{kind,offset,limit,total:rows.length,next_offset:next<rows.length?next:null,
    records:rows.slice(offset,next)}}) as CycleCropPageResponse;
}
