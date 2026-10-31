import {integer,need} from './storedLeafReplayIO';
import {equal} from './leafFundedBirthReplaySchema';
import {add,binary64,fraction,sub,type Fraction} from './supplyMorphologyGraphValues';
import {exactRecord,type ExactQuantity} from './supplyMorphologyQuantityCore';
export const MATERIAL_COUNTER_UNITS={terminal_carbon:'mg_CH2O/m2_floor',terminal_number:'fruits_equivalent/m2_floor',
 sensible:'J/m2_floor',latent:'J/m2_floor',incoming_heat:'J/m2_floor',outgoing_heat:'J/m2_floor',
 canopy_external:'J/m2_floor',air_external:'J/m2_floor',vapor:'kg_water/m2_floor',external_vapor:'kg_water/m2_floor'} as const;
export type QuantityAt={time_origin_utc:string;elapsed_seconds_exact:ExactQuantity};
export type MaterialQuantityReference={index:number;phase:string;at:QuantityAt;source_sha256:string;source_cursor_sha256:string|null;
 event_sequence:number;frame_sha256:string;bytes:number;state_scalars:number;state_sha256:string;state_kind:string};
export type MaterialQuantityFrame={reference:MaterialQuantityReference;at:QuantityAt;phase:string;
 fruit_carbohydrate:{values:number[];unit:string};fruit_number:{values:number[];unit:string};
 carbohydrate_stock_exact:ExactQuantity;number_stock_exact:ExactQuantity;cumulative_exact:Record<string,ExactQuantity>};
export function quantityStock(values:number[],unit:string){
 return exactRecord(values.reduce((v,n)=>add(v,binary64(n)),{n:0n,d:1n}),unit);
}
export function materialQuantityInterval(left:MaterialQuantityFrame,right:MaterialQuantityFrame){
 need(left.at.time_origin_utc===right.at.time_origin_utc&&right.reference.index===left.reference.index+1);
 const dt=sub(fraction(right.at.elapsed_seconds_exact,'s'),fraction(left.at.elapsed_seconds_exact,'s'));need(dt.n>=0n);
 const flows:Record<string,ExactQuantity>={};
 for(const [name,unit]of Object.entries(MATERIAL_COUNTER_UNITS)){
  const d=sub(fraction(right.cumulative_exact[name],unit),fraction(left.cumulative_exact[name],unit));
  if(name==='terminal_carbon'||name==='terminal_number')need(d.n>=0n);if(dt.n===0n)need(d.n===0n);
  flows[name]=exactRecord(d,unit);
 }
 if(dt.n===0n){
  need(left.phase==='material_before'&&right.phase==='material_after'&&right.reference.event_sequence===left.reference.event_sequence+1);
  equal(left.fruit_carbohydrate,right.fruit_carbohydrate);equal(left.fruit_number,right.fruit_number);
 }
 return {from_frame:left.reference,to_frame:right.reference,start_at:left.at,end_at:right.at,elapsed_seconds_exact:exactRecord(dt,'s'),
  kind:dt.n===0n?'zero_duration_material_boundary':'stored_model_interval',flows_exact:flows};
}
export function materialQuantityWindow(frames:MaterialQuantityFrame[],first=0,last=frames.length-1){
 integer(first,0,frames.length-1);integer(last,first,frames.length-1);const selected=frames.slice(first,last+1),a=selected[0]!,b=selected.at(-1)!;
 const intervals=selected.slice(1).map((f,i)=>materialQuantityInterval(selected[i]!,f)),totals:Record<string,ExactQuantity>={};
 for(const [name,unit]of Object.entries(MATERIAL_COUNTER_UNITS)){
  const delta=sub(fraction(b.cumulative_exact[name],unit),fraction(a.cumulative_exact[name],unit));
  const sum:Fraction=intervals.reduce((v,r)=>add(v,fraction(r.flows_exact[name],unit)),{n:0n,d:1n});need(sub(sum,delta).n===0n);
  totals[name]=exactRecord(delta,unit);
 }
 return {window:{first_frame:first,last_frame:last,start_at:a.at,end_at:b.at},frames:selected,intervals,totals_exact:totals};
}
