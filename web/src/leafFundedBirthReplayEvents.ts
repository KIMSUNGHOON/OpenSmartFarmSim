import {need,object,closed,digest,id} from './storedLeafReplayIO';
import {wireFields,wireHash} from './fundedLeafReplayWire';
import {PINS,IDENTITY,quantity,block,POINT,POINT_BALANCE,equal,list,sample,programInfo,finite,fluxUnits,type Row,type ProgramInfo} from './leafFundedBirthReplaySchema';

export const EVENT_FIELDS=['event_sequence','step_index','after_frame_index','point','context_snapshot','context_sha256'];
export const POLICY='explicit-new-structural-carbon-from-buffer-v1';
const POINT_FIELDS=['model_version','policy','code_sha256','clock_code_sha256','input_sha256','context_sha256','checkpoint_sha256','parent_manifest','inputs','before_checkpoint','after_program','after_sample','after_rates','after_state_layout','birth_receipts','point_flows','balances','checkpoint_validation_stage_evaluations','after_stage_evaluations','elapsed_steps_advanced','checkpoint','scope','claim_scope','G0_G4','calculation_sha256'];
export type GraphState={info:ProgramInfo;context:Row;seed:Row;history:unknown[];receipts:Row[];bases:Row[]};
export async function adoptStoredEvent(pointRaw:string,archiveRaw:string,descriptor:Row,item:Row,sequence:number,
 before:Row,beforeSHA:string,previous:GraphState,rootContext:Row,rootSHA:string,seen:Set<string>):Promise<GraphState>{
 const point=closed(JSON.parse(pointRaw),POINT_FIELDS),archive=closed(JSON.parse(archiveRaw),['program','seed','history','manifest']);
 const fields=wireFields(pointRaw),parts=wireFields(archiveRaw),input=object(item.point_inputs);
 const calculation='{'+Object.entries(fields).filter(([k])=>k!=='calculation_sha256').map(([k,v])=>JSON.stringify(k)+':'+v).join(',')+'}';
 need(point.model_version==='leaf-funded-structural-birth-point-research-v1'&&point.policy===POLICY&&point.code_sha256===PINS['backend/app/crop_leaf_funded_birth_point.py']&&point.clock_code_sha256===PINS['backend/app/crop_rational_morphology_clock.py']);
 need(point.input_sha256===await wireHash(fields.inputs!)&&point.calculation_sha256===await wireHash(calculation));equal(point.inputs,input);
 need(point.scope==='software_research_only'&&point.G0_G4==='not_assessed'&&point.claim_scope==='synthetic_declared_new_structural_allocation_point_only'&&point.checkpoint===null&&point.elapsed_steps_advanced===0&&point.checkpoint_validation_stage_evaluations===1&&point.after_stage_evaluations===1);
 need(point.checkpoint_sha256===beforeSHA&&input.checkpoint_sha256===beforeSHA&&await wireHash(fields.before_checkpoint!)===beforeSHA);
 need(point.context_sha256===before.context_sha256&&input.context_sha256===before.context_sha256);equal(point.before_checkpoint,before);equal(point.parent_manifest,previous.context);
 const m=closed(archive.manifest,['version','identity','root_context_sha256','parent_context_sha256','parent_checkpoint_sha256','program_sha256','seed_sha256','history_sha256','numerical','state_layout']);
 const seed=closed(archive.seed,['last_confirmed','before_checkpoint','anchors','birth_bases','base_transfers']);
 need(m.version==='funded-individual-leaf-context-v1'&&await wireHash(parts.manifest!)===descriptor.context_sha256&&m.root_context_sha256===rootSHA&&m.parent_context_sha256===point.context_sha256&&m.parent_checkpoint_sha256===beforeSHA);
 equal(m.identity,{version:'leaf-funded-birth-continuation-research-v1',code_sha256:PINS['backend/app/crop_leaf_funded_birth_continuation.py'],point_code_sha256:PINS['backend/app/crop_leaf_funded_birth_point.py'],clock_code_sha256:PINS['backend/app/crop_rational_morphology_clock.py'],root_identity:IDENTITY});
 for(const k of ['program','seed','history'])need(m[k+'_sha256']===await wireHash(parts[k]!));
 const info=await programInfo(parts.program!),n0=previous.info.leaves.length,n=info.leaves.length;
 const events=list(input.events);need(events.length>=1&&n===n0+events.length);
 const leaves=events.map(v=>{
  const event=closed(v,['event_id','attachment_internode_id','incoming_temperature','leaf']);id(event.event_id);id(event.attachment_internode_id);quantity(event.incoming_temperature,'degC');
  need(!seen.has(event.event_id));seen.add(event.event_id);const leaf=object(event.leaf);need(quantity(leaf.thermal_age,'degC_day')===0&&quantity(leaf.initial_carbon,'mg_CH2O/m2_floor')>0);return leaf;
 });
 equal(info.program,{...previous.info.program,leaves:[...previous.info.leaves,...leaves]});equal(point.after_program,info.program);equal(point.after_state_layout,info.layout);equal(m.state_layout,info.layout);
 equal(m.numerical,{...object(rootContext.numerical),event_global_step_index:item.step_index});
 const dt=object(rootContext.numerical).step_seconds;finite(dt);const step=item.step_index;finite(step);
 sample(point.after_sample,info,step,dt);equal(seed.last_confirmed,point.after_sample);equal(seed.before_checkpoint,before);
 const old=list(object(before.last_confirmed).state),next=list(object(point.after_sample).state);
 equal(next.slice(1,104),old.slice(1,104));equal(next.slice(105,107),old.slice(105,107));
 equal(next.slice(107,107+n0),old.slice(107,107+n0));equal(next.slice(107+n0,107+n),leaves.map(()=>0));
 equal(next.slice(107+n,107+n+n0),old.slice(107+n0,107+2*n0));equal(next.slice(107+2*n,107+2*n+n0),old.slice(107+2*n0));
 equal(next.slice(107+2*n+n0),leaves.map(l=>quantity(l.initial_carbon,'mg_CH2O/m2_floor')));list(point.after_rates,next.length).forEach(finite);
 block(point.point_flows,POINT);const b=closed(point.balances,Object.keys(POINT_BALANCE));
 for(const [k,u]of Object.entries(POINT_BALANCE)){const row=closed(b[k],['residual','budget']);need(quantity(row.budget,u)>=0&&Math.abs(quantity(row.residual,u))<=quantity(row.budget,u));}
 const history=list(archive.history,sequence);equal(history.slice(0,-1),previous.history);
 const integral=quantity(object(before.integrated_transfers).indoor_air_temperature_time,'degC_s');
 equal(history.at(-1),{inputs:input,calculation_sha256:point.calculation_sha256,after_sample_sha256:await wireHash(fields.after_sample!),new_leaves:leaves,point_flows:point.point_flows,balances:point.balances,air_temperature_integral:integral});
 equal(seed.anchors,[...list(previous.seed.anchors),...leaves.map(()=>({value:0,unit:'m2'}))]);
 const bases=[...previous.bases,...leaves.map(l=>({leaf_id:l.leaf_id,step_index:step,thermal_age:0,carbon:quantity(l.initial_carbon,'mg_CH2O/m2_floor'),air_temperature_integral:integral}))];equal(seed.birth_bases,bases);
 equal(seed.base_transfers,Object.fromEntries(Object.entries(fluxUnits(n)).map(([k,u])=>[k,object(before.integrated_transfers)[k]??{value:0,unit:u}])));
 const receipts=list(point.birth_receipts,leaves.length).map((v,i)=>{
  const row=closed(v,['event_id','attachment_internode_id','initialization','capacity_in','sensible_in']),event=object(events[i]),leaf=leaves[i]!;
  need(row.event_id===event.event_id&&row.attachment_internode_id===event.attachment_internode_id);quantity(row.capacity_in,'J/m2_floor/K');quantity(row.sensible_in,'J/m2_floor');
  const initial=closed(row.initialization,['model_version','scope','claim_scope','gates','input_sha256','state']);digest(initial.input_sha256);
  need(initial.model_version==='leaf-logistic-canonical-area-state-research-v1'&&initial.scope==='software_research_only'&&initial.claim_scope==='synthetic_crop_math_only'&&initial.gates==='not_assessed');
  const state=closed(initial.state,['model_version','origin','thermal_age_basis','normalization','leaf_id','curve','curve_sha256','age_exact','area','anchor']);
  const anchor=closed(state.anchor,['leaf_id','age_exact','curve_sha256','requested_area','canonical_area']);
  need(state.model_version===initial.model_version&&state.origin==='synthetic'&&state.thermal_age_basis==='since_leaf_emergence'&&state.normalization==='zero_lower_asymptote_sigmoid_v1'&&state.leaf_id===leaf.leaf_id&&anchor.leaf_id===leaf.leaf_id&&state.curve_sha256===info.areaCurveHashes[n0+i]&&anchor.curve_sha256===state.curve_sha256);
  equal(state.curve,leaf.curve);equal(state.age_exact,{numerator:'0',denominator:'1',unit:'degC_day'});equal(anchor.age_exact,state.age_exact);equal(anchor.requested_area,leaf.initial_area);equal(state.area,anchor.canonical_area);
  need(quantity(state.area,'m2')===next[107+n+n0+i]);return {kind:'funded_birth',value:row};
 });
 return {info,context:m,seed,history,receipts:[...previous.receipts,...receipts],bases};
}
