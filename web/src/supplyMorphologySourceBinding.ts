import {closed,digest,need,object,rights,integer} from './storedLeafReplayIO';
import {wireHash,wireFields} from './fundedLeafReplayWire';
import {equal} from './leafFundedBirthReplaySchema';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {document,list,without,type WireDocument} from './supplyMorphologyGraphValues';

export function publicRights(value:unknown){const q=closed(value,['crop','stem','declaration']);Object.values(q).forEach(rights);}
export function installedPins(value:unknown,paths:readonly string[]){
 const q=closed(value,[...paths]),expected:Readonly<Record<string,string>>=F.code_sha256;
 for(const path of paths)need(q[path]===expected[path]);
}
export function researchFlags(value:Record<string,unknown>,schema:string){
 need(value.schema_version===schema&&value.scope==='software_research_only'&&value.G0_G4==='not_assessed'&&value.R2==='not_approved');
 need(value.time_kind==='synthetic_model_clock_not_observation'&&value.claim_scope==='stored_synthetic_supply_limited_morphology_only');
}
export function sourceDescriptor(value:unknown,maximum=2*1024**2){
 const d=closed(value,['sha256','bytes']);digest(d.sha256);integer(d.bytes,1,maximum);return {sha256:d.sha256,bytes:d.bytes};
}
export async function verifySupplySourceBinding(root:WireDocument,get:(descriptor:unknown)=>string,byHash:(hash:unknown)=>string){
 const r=root.value,inputs=closed(r.root_inputs,['request','program','seed','manifest','origin_context','license_notice',...Object.keys(F.profiles)]);
 for(const d of Object.values(inputs))get(d);
 for(const [name,expected]of Object.entries({...F.profiles,license_notice:F.notice_sha256}))need(sourceDescriptor(inputs[name]).sha256===expected);
 const archive=list(r.source_blobs,4096),hashes=new Set<string>();need(archive.length>=1);
 for(const d of archive){const descriptor=sourceDescriptor(d);need(!hashes.has(descriptor.sha256));hashes.add(descriptor.sha256);get(d);}
 const binding=document(get(r.initial_binding)),b=closed(binding.value,[...F.schema_keys.binding]);
 for(const [key,value]of Object.entries(F.source_claims.binding))equal(b[key],value);
 need(b.calculation_sha256===await wireHash(without(binding.raw,'calculation_sha256')));
 installedPins(b.source_code_sha256,F.code_sets.binding);
 need(b.code_sha256===F.code_sha256['backend/app/crop_stem_root_initial_binding.py']);
 publicRights(r.source_rights);equal(b.source_rights,r.source_rights);rights(object(b.declaration).rights);
 equal(object(b.declaration).rights,object(r.source_rights).declaration);
 const selection=closed(r.selection,['crop_root_sha256','stem_root_sha256','stem_start_index','binding_declaration']);
 equal(selection.binding_declaration,b.declaration);
 const crop=document(byHash(selection.crop_root_sha256)),stem=document(byHash(selection.stem_root_sha256));
 closed(crop.value,[...F.schema_keys.crop]);closed(stem.value,[...F.schema_keys.stem]);
 for(const [key,value]of Object.entries(F.source_claims.crop))equal(crop.value[key],value);
 for(const [key,value]of Object.entries(F.source_claims.stem))equal(stem.value[key],value);
 installedPins(crop.value.code_sha256,F.code_sets.crop);installedPins(stem.value.code_sha256,F.code_sets.stem);
 equal(crop.value.source_rights,object(r.source_rights).crop);equal(stem.value.program_rights,object(r.source_rights).stem);
 rights(crop.value.source_rights);rights(stem.value.program_rights);
 const cropSources=object(crop.value.sources);for(const d of Object.values(cropSources)){need(hashes.has(sourceDescriptor(d).sha256));get(d);}
 const cropSample=object(list(crop.value.samples)[0]),chosen=object(b.crop_selection);
 need(chosen.root_sha256===selection.crop_root_sha256&&chosen.state_sha256===crop.value.initial_state_sha256&&chosen.checkpoint_sha256===cropSample.checkpoint_sha256);
 need(chosen.program_sha256===sourceDescriptor(cropSources.program).sha256);
 const samples=list(stem.value.samples);integer(selection.stem_start_index,0,samples.length-1);
 const sample=object(samples[selection.stem_start_index]),result=document(byHash(sample.result_sha256));
 const stateSHA=await wireHash(wireFields(result.raw).state!),linked=object(b.stem_selection);
 need(linked.root_sha256===selection.stem_root_sha256&&linked.index===selection.stem_start_index&&linked.result_sha256===sample.result_sha256);
 need(stateSHA===linked.state_sha256&&stateSHA===sample.state_sha256);equal(linked.source_state,result.value.state);
 const base=object(object(object(result.value.state).timeline_state).base_temperature);
 need(base.unit==='degC'&&typeof base.value==='number'&&Number.isFinite(base.value)&&base.value===r.shoot_base_temperature);
 return binding;
}
