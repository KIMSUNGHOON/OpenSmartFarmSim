import {closed,need,object,rights,integer,id} from './storedLeafReplayIO';
import {wireHash,wireItems,wireFields} from './fundedLeafReplayWire';
import {expandSupplyMorphologyReceipt} from './supplyMorphologyReceiptWire';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {equal} from './leafFundedBirthReplaySchema';
import {AUTHORITY,MODEL_PINS_RAW,modelPins,type SupplyContext} from './supplyMorphologyContextGraph';
import {add,compare,document,exactAt,fraction,list,sub,wireObject,without,type WireDocument} from './supplyMorphologyGraphValues';
export type MaterialLink={receipt:WireDocument;before:WireDocument;beforeSnapshotRaw:string;afterSnapshotRaw:string};

export async function readSupplyMaterial(old:SupplyContext,next:SupplyContext,previous:WireDocument):Promise<MaterialLink>{
 need(next.doc.fields.root_checkpoint===old.doc.fields.root_checkpoint&&next.descriptor.value.origin_context_sha256===old.descriptor.value.origin_context_sha256);
 need(next.packed.length===old.packed.length+1&&next.packed.slice(0,-1).every((raw,i)=>raw===old.packed[i]));
 equal((next.descriptor.value.receipt_sha256 as unknown[]).slice(0,-1),old.descriptor.value.receipt_sha256);
 const raw=await expandSupplyMorphologyReceipt(old.seed.raw,next.packed.at(-1)!,MODEL_PINS_RAW),receipt=document(raw);
 const p=closed(receipt.value,[...F.schema_keys.point]),before=document(receipt.fields.before_candidate!),b=closed(before.value,[...F.schema_keys.candidate]);
 for(const [doc,version]of [[receipt,'supply-morphology-repeat-compact-material-receipt-v1'],[before,'supply-morphology-repeat-compact-candidate-receipt-v1']]as const){
  const q=doc.value;need(q.model_version===version&&q.scope==='software_research_only'&&q.G0_G4==='not_assessed');modelPins(q.source_code_sha256);
  need(q.calculation_sha256===await wireHash(without(doc.raw,'calculation_sha256')));
 }
 const pointSHA=await wireHash(raw),cpSHA=await wireHash(previous.raw);
 need(pointSHA===next.descriptor.value.point_sha256&&p.context_sha256===old.sha256&&b.context_sha256===old.sha256);
 need(p.checkpoint_sha256===cpSHA&&b.checkpoint_sha256===cpSHA&&before.fields.source_prefix===previous.raw);
 need(p.integrator_checkpoint===null&&b.integrator_checkpoint===null&&b.schedule_consumed===false&&b.new_organs_created===false);
 const inputs=closed(p.inputs,[...F.schema_keys.point_inputs]);rights(inputs.rights);
 const event=closed(p.source_event,['entity','internode_event_id','internode_id','leaf_event_id','leaf_id','sequence','source_event_id','threshold_exact']);
 integer(event.sequence,0,Number.MAX_SAFE_INTEGER);id(event.source_event_id);id(event.internode_id);id(event.internode_event_id);
 need(p.input_sha256===await wireHash(receipt.fields.inputs!)&&inputs.context_sha256===old.sha256&&inputs.checkpoint_sha256===cpSHA);
 need(inputs.candidate_sha256===p.before_candidate_sha256&&p.before_candidate_sha256===b.proposal_sha256);
 const previousSchedule=object(previous.value.schedule);
 need(inputs.source_event_id===event.source_event_id&&inputs.source_threshold_sequence===event.sequence&&event.sequence===previousSchedule.next_sequence);
 equal(inputs.source_threshold_exact,event.threshold_exact);equal(event.threshold_exact,previousSchedule.next_threshold_exact);
 const after=next.seed.value,oldSeed=old.seed.value;
 for(const [target,source]of Object.entries({program:'after_program',organs:'after_organs',costs:'after_costs',state_layout:'after_state_layout',
  birth_bases:'after_birth_baselines',geometry_baselines:'after_geometry_baselines',global_ledgers:'post_point_global_ledgers_preview',
  lifetime_transfers_exact:'post_point_lifetime_transfers_exact_preview',point_totals_exact:'post_point_point_totals_exact_preview'})){
  need(next.seed.fields[target]===receipt.fields[source]);
 }
 const dense=document(before.fields.dense_candidate!);
 const beforeSnapshotRaw=wireObject(Object.fromEntries(['at','state','derived'].map(k=>[k,dense.fields[k]!])));
 const afterSnapshotRaw=wireObject({at:receipt.fields.at!,state:receipt.fields.after_state!,derived:receipt.fields.after_derived!});
 need(next.seed.fields.initial_sample===afterSnapshotRaw&&receipt.fields.at===before.fields.at&&receipt.fields.at===dense.fields.at);
 const at=exactAt(p.at),priorAt=exactAt(previous.value.at);need(at.origin===priorAt.origin&&compare(at.elapsed,priorAt.elapsed)>0);
 need(wireFields(receipt.fields.after_stage!).derived===receipt.fields.after_derived);
 need(after.event_sequence===Number(previous.value.event_sequence)+1&&after.output_cursor===Number(previous.value.output_cursor)+2);
 need(next.seed.fields.original_numerical===old.seed.fields.original_numerical&&next.seed.fields.transfer_origins===old.seed.fields.transfer_origins);
 for(const kind of ['leaves','internodes']){
  const prior=wireItems(wireFields(old.seed.fields.geometry_baselines!)[kind]!),current=wireItems(wireFields(next.seed.fields.geometry_baselines!)[kind]!);
  need(current.slice(0,prior.length).every((raw,i)=>raw===prior[i])&&current.length>=prior.length);
 }
 const oldOrgans=object(oldSeed.organs),newOrgans=object(after.organs);
 need(list(newOrgans.internodes).length===list(oldOrgans.internodes).length+1);
 need(list(newOrgans.leaves).length===list(oldOrgans.leaves).length+(inputs.leaf===null?0:1));
 async function prefix(previousSHA:unknown,snapshotRaw:string,sequence:unknown,phase:string){return wireHash(wireObject({
  previous_output_prefix_sha256:JSON.stringify(previousSHA),sample_sha256:JSON.stringify(await wireHash(snapshotRaw)),
  event_sequence:String(sequence),phase:JSON.stringify(phase),material_point_sha256:JSON.stringify(pointSHA),version:JSON.stringify(AUTHORITY)}));}
 const beforeSHA=await prefix(previous.value.output_prefix_sha256,beforeSnapshotRaw,previous.value.event_sequence,'fractional_before_compatible_material_point');
 const afterSHA=await prefix(beforeSHA,afterSnapshotRaw,after.event_sequence,'fractional_after_compatible_material_point');
 need(after.source_output_prefix_sha256===previous.value.output_prefix_sha256&&after.before_material_prefix_sha256===beforeSHA&&after.output_prefix_sha256===afterSHA);
 const schedule=closed(after.schedule,[...F.schema_keys.schedule]),oldSchedule=object(oldSeed.schedule);
 const spacing=sub(fraction(oldSchedule.next_threshold_exact,'degC_day'),fraction(oldSchedule.consumed_threshold_exact,'degC_day'));
 const threshold=fraction(event.threshold_exact,'degC_day'),age=fraction(schedule.age_exact,'degC_day');need(spacing.n>0n);
 need(schedule.consumed_event_id===event.source_event_id&&schedule.consumed_sequence===event.sequence&&schedule.next_sequence===Number(event.sequence)+1);
 equal(schedule.consumed_threshold_exact,event.threshold_exact);equal(schedule.age_exact,dense.value.shoot_age_exact);
 need(compare(fraction(schedule.next_threshold_exact,'degC_day'),add(threshold,spacing))===0&&compare(age,threshold)>=0&&compare(age,add(threshold,spacing))<0);
 need(schedule.policy==='repeated_material_event_once_no_threshold_snap');
 need(oldSchedule.policy===(old.packed.length===0?'compatible_successor_source_event_once_no_threshold_snap':'repeated_material_event_once_no_threshold_snap'));
 for(const k of ['source_schedule_id','age_basis'])equal(schedule[k],oldSchedule[k]);
 need(p.redistribution_authorized===true&&after.redistribution_authorized===true&&oldSeed.redistribution_authorized===true);
 return {receipt,before,beforeSnapshotRaw,afterSnapshotRaw};
}
