import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {need,object,closed,integer,id,exact,utc} from './storedLeafReplayIO';
import {equal,list,finite,quantity,block,balances,fluxUnits,POINT,type ProgramInfo,type Row,type Quantity} from './leafFundedBirthReplaySchema';
export {equal,list,finite,quantity,block};
export type Exact={numerator:string;denominator:string;unit:'s'|'degC_day'};
export type At={time_origin_utc:string;elapsed_seconds_exact:Exact};
export type CropLeaf={leaf_id:string;attachment_internode_id:string;kind:string;event_id:string|null;
 birth_at_elapsed_seconds_exact:Exact|null;curve_sha256:string;thermal_age:Quantity;area:Quantity;carbohydrate:Quantity};
export type CropNode={internode_id:string;sequence:number;kind:string;development_birth_seconds_exact:Exact;
 age_exact:Exact;curve:Row;curve_sha256:string;length:Quantity;point_input_sha256:string;source_length_state_sha256:string|null;initial_anchor:Row};
export type CompleteCropFrame={index:number;at:At;phase:string;event_sequence:number;output_cursor:number;checkpoint_sha256:string|null;
 raw:Row;snapshot:Row;leaves:CropLeaf[];internodes:CropNode[];tracked_leaf_area:Quantity;tracked_axis_length:Quantity;
 lifetime_integrated_transfers:Row;ledgers:Row};
export const FLAGS={schema_version:'complete-crop-research-artifact-v1',scope:'software_research_only',G0_G4:'not_assessed',
 R2:'not_approved',status:'completed_software_fixture',time_kind:'synthetic_model_clock_not_observation',claim_scope:'stored_synthetic_complete_crop_geometry_only'};
export const FRAME_FIELDS=['at','phase','event_sequence','output_cursor','output_prefix_sha256','program_sha256','shoot','leaves','tracked_leaf_area','evidence','quantities_storage'];
export const DESCRIPTOR_FIELDS=['index','at','phase','event_sequence','output_cursor','output_prefix_sha256','frame_sha256','state_sha256','checkpoint_sha256'];
export const CP_FIELDS=['version','context_sha256','at','grid_step_index','segment_steps','branch_steps','event_sequence','phase','last_confirmed',
 'output_cursor','output_prefix_sha256','segment_integrated_transfers','branch_integrated_transfers','lifetime_integrated_transfers',
 'branch_point_transfers','lifetime_point_transfers','branch_balance_residuals','branch_balance_budgets','global_balance_residuals','global_balance_budgets','scope','G0_G4'];
export const DERIVED={canopy_temperature:'degC',leaf_area_index:'m2_leaf/m2_floor',leaf_area_index_rate:'m2_leaf/m2_floor/s',
 canopy_capacity:'J/m2_floor/K',air_capacity:'J/m2_floor/K',air_vapor_pressure:'Pa',canopy_temperature_rate:'K/s',leaf_carbohydrate:'mg_CH2O/m2_floor'};
export function flags(value:Row,schema=FLAGS.schema_version){for(const [k,v]of Object.entries(FLAGS))need(value[k]===(k==='schema_version'?schema:v));}
export function at(value:unknown){const q=closed(value,['time_origin_utc','elapsed_seconds_exact']);utc(q.time_origin_utc);exact(q.elapsed_seconds_exact,'s');return q as At;}
export function frac(value:unknown,unit:'s'|'degC_day'='s'){return exact(value,unit);}
export function sameFraction(a:unknown,b:unknown,unit:'s'|'degC_day'='s'){const x=frac(a,unit),y=frac(b,unit);need(x.n*y.d===y.n*x.d);}
export function leq(a:unknown,b:unknown,unit:'s'|'degC_day'='s'){const x=frac(a,unit),y=frac(b,unit);return x.n*y.d<=y.n*x.d;}
export function sumClose(values:number[],target:number){
 values.forEach(finite);finite(target);const sum=values.reduce((a,b)=>a+b,0),error=(values.length+1)*Number.EPSILON;
 need(Number.isFinite(sum)&&Math.abs(sum-target)<=Math.max(Math.abs(sum),Math.abs(target))*error/(1-error));
}
export function snapshot(frame:Row){const e=object(frame.evidence);return object(e.checkpoint===null?frame.snapshot:object(e.checkpoint).last_confirmed);}
export function quantities(frame:Row){
 const e=object(frame.evidence),s=snapshot(frame),cp=e.checkpoint===null?null:object(e.checkpoint);
 if(cp===null)return {s,flows:object(frame.lifetime_integrated_transfers),ledgers:object(frame.ledgers)};
 if(e.kind==='fractional_checkpoint')return {s,flows:object(cp.lifetime_integrated_transfers),ledgers:{balance_residuals:cp.global_balance_residuals,balance_budgets:cp.global_balance_budgets}};
 return {s,flows:object(cp.integrated_transfers),ledgers:{balance_residuals:cp.global_balance_residuals??cp.balance_residuals,balance_budgets:cp.global_balance_budgets??cp.balance_budgets}};
}
export function checkedFrame(value:unknown,info:ProgramInfo,index:number):CompleteCropFrame{
 const f=object(value),e=object(f.evidence),dense=e.kind==='checked_dense_candidate';
 closed(f,[...FRAME_FIELDS,...(dense?['snapshot','lifetime_integrated_transfers','lifetime_point_transfers','ledgers']:[])]);
 const time=at(f.at);integer(f.output_cursor,1,512);need(f.output_cursor===index+1);integer(f.event_sequence,0,511);
 need(['root_interval','funded_birth_interval','before_birth','after_birth','grid_endpoint'].includes(String(f.phase)));
 need(f.quantities_storage===(dense?'source_prefix_plus_dense_partial':'checkpoint'));
 const {s,flows,ledgers}=quantities(f),n=info.leaves.length,y=list(s.state,107+3*n);y.forEach(finite);
 need([...y.slice(0,2),...y.slice(3,104),y[106],...y.slice(107+2*n)].every(v=>typeof v==='number'&&v>=0));
 block(s.derived,DERIVED);for(const k of ['curve_residuals','curve_invariant_changes'])list(s[k],n).forEach(v=>quantity(v,'m2'));
 block(flows,fluxUnits(n));balances(ledgers,n);
 if(e.kind==='fractional_checkpoint'){
  const cp=closed(e.checkpoint,CP_FIELDS);need(cp.version==='fractional-individual-leaf-checkpoint-v1'&&cp.scope==='software_research_only'&&cp.G0_G4==='not_assessed');
  for(const k of ['grid_step_index','segment_steps','branch_steps','event_sequence','output_cursor'])integer(cp[k],0,Number.MAX_SAFE_INTEGER);
  for(const k of ['segment_integrated_transfers','branch_integrated_transfers','lifetime_integrated_transfers'])block(cp[k],fluxUnits(n));
  for(const k of ['branch_point_transfers','lifetime_point_transfers'])block(cp[k],POINT);
  balances({balance_residuals:cp.branch_balance_residuals,balance_budgets:cp.branch_balance_budgets},n);
  closed(s,['schema_version','at','state','derived','curve_residuals','curve_invariant_changes']);need(s.schema_version==='fractional-individual-leaf-state-v1');equal(s.at,time);
 }else if(dense){closed(s,['state','derived','curve_residuals','curve_invariant_changes']);block(f.lifetime_point_transfers,POINT);}
 else{closed(s,['step_index','elapsed_seconds','state','derived','curve_residuals','curve_invariant_changes']);integer(s.step_index,0,4096);finite(s.elapsed_seconds);}
 const shoot=closed(f.shoot,['internodes','shoot_age_exact','birth','next_threshold_exact','tracked_axis_length']);exact(shoot.shoot_age_exact,'degC_day');const threshold=exact(shoot.next_threshold_exact,'degC_day');need(threshold.n>0n);
 const nodes=list(shoot.internodes).map(v=>{
  const q=closed(v,['internode_id','sequence','kind','development_birth_seconds_exact','age_exact','curve','curve_sha256','length','point_input_sha256','source_length_state_sha256','initial_anchor']);
  id(q.internode_id);integer(q.sequence,0,Number.MAX_SAFE_INTEGER);exact(q.development_birth_seconds_exact,'s');exact(q.age_exact,'degC_day');
  need(['selected_original','numerical_threshold_birth'].includes(String(q.kind)));const curve=closed(q.curve,['profile_id','origin','values']);id(curve.profile_id);need(curve.origin==='synthetic');
  const c=block(curve.values,{maximum_length:'m',steepness:'1/degC_day',inflection_age:'degC_day'});need(quantity(c.maximum_length,'m')>0&&quantity(c.steepness,'1/degC_day')>0&&quantity(c.inflection_age,'degC_day')>=0);
  const length=quantity(q.length,'m');need(length>0&&length<=quantity(c.maximum_length,'m'));return q as CropNode;
 });
 need(nodes.length>=1&&nodes.length<=512&&new Set(nodes.map(q=>q.internode_id)).size===nodes.length);
 const parents=new Set(nodes.map(q=>q.internode_id));const rows=list(f.leaves,n);const leaves=rows.map((value,j)=>{
  const q=closed(value,['leaf_id','attachment_internode_id','kind','event_id','birth_at_elapsed_seconds_exact','curve_sha256']);
  need(q.leaf_id===info.leaves[j]!.leaf_id&&q.curve_sha256===info.curveHashes[j]);id(q.attachment_internode_id);need(parents.has(q.attachment_internode_id));
  if(q.event_id!==null)id(q.event_id);if(q.birth_at_elapsed_seconds_exact!==null){exact(q.birth_at_elapsed_seconds_exact,'s');need(leq(q.birth_at_elapsed_seconds_exact,time.elapsed_seconds_exact));}
  const age=y[107+j]as number,area=y[107+n+j]as number,carbon=y[107+2*n+j]as number;
  need(age>=quantity(info.leaves[j]!.thermal_age,'degC_day')&&area>0&&area<=quantity(object(object(info.leaves[j]!.curve).values).maximum_area,'m2'));
  return {...q,thermal_age:{value:age,unit:'degC_day'},area:{value:area,unit:'m2'},carbohydrate:{value:carbon,unit:'mg_CH2O/m2_floor'}}as CropLeaf;
 });
 sumClose(leaves.map(l=>l.area.value),quantity(f.tracked_leaf_area,'m2'));sumClose(nodes.map(q=>q.length.value),quantity(shoot.tracked_axis_length,'m'));
 return {index,at:time,phase:String(f.phase),event_sequence:f.event_sequence,output_cursor:f.output_cursor,checkpoint_sha256:e.checkpoint_sha256 as string|null,
  raw:f,snapshot:s,leaves,internodes:nodes,tracked_leaf_area:f.tracked_leaf_area as Quantity,tracked_axis_length:shoot.tracked_axis_length as Quantity,lifetime_integrated_transfers:flows,ledgers};
}

export async function contextLinks(raw:string){
 const fields=wireFields(raw),value=object(JSON.parse(raw)),seed=closed(value.seed,['sample','branch_base_transfers','branch_step_count','output_cursor','output_prefix_sha256']);
 integer(seed.branch_step_count,0,4096);integer(seed.output_cursor,1,512);
 const record=object(list(value.records).at(-1)),recordRaw=wireItems(fields.records!).at(-1)!;
 need(await wireHash(wireFields(fields.seed!).sample!)===record.after_sample_sha256&&await wireHash(fields.program!)===record.after_program_sha256);
 need(await wireHash(wireFields(recordRaw).inputs!)===record.input_sha256);
}
