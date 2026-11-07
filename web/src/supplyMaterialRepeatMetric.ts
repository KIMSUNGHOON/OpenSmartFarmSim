import {need} from './api-validation';
import type {RepeatSelection} from './supplyMaterialRepeatReplay';
import type {RepeatAt,RepeatBinding,RepeatExact,RepeatOrgan,RepeatPhase,RepeatQuantity,
 RepeatSourceObject,RepeatSourceValue} from './supplyMaterialRepeatWire';

export type MetricQuantity<U extends string>={value:number;unit:U};
export type MetricExact<U extends string>={numerator:string;denominator:string;unit:U};
export type MetricAt={time_origin_utc:string;elapsed_seconds_exact:MetricExact<'s'>};
export type MetricOrgan<U extends 'm2'|'m'>={id:string;parent_internode_id:string|null;
 geometry:MetricQuantity<U>;carbon:MetricQuantity<'mg_CH2O/m2_floor'>;
 clock_exact:MetricExact<'degC_day'>;geometry_diagnostics:{deficit_exact:MetricExact<U>}};
export type MetricFrame={index:number;phase:RepeatPhase;at:MetricAt;
 G0_G4:'not_assessed';R2:'not_approved';leaves:MetricOrgan<'m2'>[];internodes:MetricOrgan<'m'>[]};
export type RepeatMetricView={metric:MetricFrame;
 identity:{rootSha256:string;index:number;binding:RepeatBinding};
 dimensions:{n:number;m:number;h:number};evidence:RepeatSelection};

function quantity<U extends string>(value:RepeatQuantity,unit:U):MetricQuantity<U>{
 need(value.unit===unit&&typeof value.value==='number'&&Number.isFinite(value.value)&&value.value>=0);
 return {value:value.value,unit};
}
function exact<U extends string>(value:RepeatExact,unit:U):MetricExact<U>{
 need(value.unit===unit&&typeof value.numerator==='string'&&typeof value.denominator==='string');
 return {numerator:value.numerator,denominator:value.denominator,unit};
}
function at(value:RepeatAt):MetricAt{
 need(typeof value.time_origin_utc==='string');
 return {time_origin_utc:value.time_origin_utc,elapsed_seconds_exact:exact(value.elapsed_seconds_exact,'s')};
}
function sameAt(a:RepeatAt,b:RepeatAt):boolean{
 return a.time_origin_utc===b.time_origin_utc&&a.elapsed_seconds_exact.unit==='s'&&b.elapsed_seconds_exact.unit==='s'
  &&a.elapsed_seconds_exact.numerator===b.elapsed_seconds_exact.numerator
  &&a.elapsed_seconds_exact.denominator===b.elapsed_seconds_exact.denominator;
}
function organ<U extends 'm2'|'m'>(row:RepeatOrgan,unit:U):MetricOrgan<U>{
 need(typeof row.id==='string'&&(row.parent_internode_id===null||typeof row.parent_internode_id==='string'));
 return {id:row.id,parent_internode_id:row.parent_internode_id,geometry:quantity(row.geometry,unit),
  carbon:quantity(row.carbon,'mg_CH2O/m2_floor'),clock_exact:exact(row.clock_exact,'degC_day'),
  geometry_diagnostics:{deficit_exact:exact(row.geometry_diagnostics.deficit_exact,unit)}};
}
function object(value:RepeatSourceValue|undefined):RepeatSourceObject{
 need(value!==null&&typeof value==='object'&&!Array.isArray(value));return value;
}
function matchingIDs(value:RepeatSourceValue|undefined,expected:string[]):void{
 need(Array.isArray(value)&&value.length===expected.length&&value.every((id,i)=>id===expected[i]));
}
function dimensions(selection:RepeatSelection):{n:number;m:number;h:number}{
 const frame=selection.frame,layout=object(frame.state_layout),original=object(layout.original);
 const leaves=frame.leaves.map(row=>row.id),nodes=frame.internodes.map(row=>row.id);
 matchingIDs(original.leaf_ids,leaves);matchingIDs(layout.internode_ids,nodes);
 const compartments=original.stem_root_compartments;need(Array.isArray(compartments));
 const ids:string[]=[];let internode=0,roots=0;
 for(const value of compartments){
  const row=object(value);need(typeof row.compartment_id==='string');ids.push(row.compartment_id);
  if(row.kind==='internode'){need(row.compartment_id===nodes[internode]);internode++;}
  else{need(row.kind==='root_system');roots++;}
 }
 need(internode===nodes.length&&roots===1&&new Set(ids).size===ids.length);
 return {n:leaves.length,m:compartments.length,h:nodes.length};
}

export function repeatMetricView(selected:Readonly<RepeatSelection>):RepeatMetricView{
 need(selected!==null&&typeof selected==='object');
 const evidence:RepeatSelection=structuredClone(selected),frame=evidence.frame;
 need(typeof evidence.rootSha256==='string'&&/^[0-9a-f]{64}$/.test(evidence.rootSha256));
 need(Number.isSafeInteger(evidence.index)&&evidence.index>=0&&evidence.index<evidence.manifest.frames.length);
 const descriptor=evidence.manifest.frames[evidence.index];need(descriptor);
 need(frame.index===evidence.index&&descriptor.index===evidence.index&&frame.phase===descriptor.phase);
 need(sameAt(frame.at,descriptor.at)&&sameAt(frame.snapshot.at,frame.at));
 need(frame.binding.active_basis_sha256===descriptor.active_basis_sha256
  &&frame.binding.transition_index===descriptor.transition_index);
 need(frame.G0_G4==='not_assessed'&&frame.R2==='not_approved');
 const metric:MetricFrame={index:frame.index,phase:frame.phase,at:at(frame.at),G0_G4:'not_assessed',R2:'not_approved',
  leaves:frame.leaves.map(row=>organ(row,'m2')),internodes:frame.internodes.map(row=>organ(row,'m'))};
 return {metric,identity:{rootSha256:evidence.rootSha256,index:evidence.index,binding:structuredClone(frame.binding)},
  dimensions:dimensions(evidence),evidence};
}
