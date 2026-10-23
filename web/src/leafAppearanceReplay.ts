import {decodeMorphologyFrame,RATIONAL_MORPHOLOGY_SOURCE,sha256} from './morphologyReplay';
import type {LeafPopulationFrame} from './leafPopulationReplay';
import {MODELS as POPULATION_MODELS,DISPLAY as POPULATION_DISPLAY} from './leafPopulationReplay';
import {LEAF_APPEARANCE_FIXTURE as FIXTURE} from './leafAppearanceReplayFixture';
import {STORED_LEAF_MAX_BYTES as MAX,need,object,closed,digest,id,utc,integer,flags,exact,area,constants,rights,readStoredLeafFile,parse} from './storedLeafReplayIO';

export const APPEARANCE_DISPLAY=FIXTURE.display_policy;
export type LeafAppearanceFrame=Omit<LeafPopulationFrame,'schema_version'>&{
 schema_version:'leaf-appearance-replay-frame-v1';population_artifact_sha256:string;source_program_sha256:string;
 preparation_sha256:string;policy_sha256:string;leaf_profile_sha256:string;display_policy:typeof APPEARANCE_DISPLAY};
export type LeafAppearanceReplay={artifact_sha256:string;frames:LeafAppearanceFrame[];policy:typeof FIXTURE.policy};
const REFERENCES=['source_program_sha256','preparation_sha256','generated_program_sha256','population_artifact_sha256',
 'stem_artifact_sha256','stem_program_sha256','time_origin_utc','initial_state_sha256','terminal_state_sha256'] as const;
const same=(a:unknown,b:unknown)=>JSON.stringify(a)===JSON.stringify(b);
const PREPARATION_MODELS=Object.fromEntries(Object.entries(FIXTURE.model_versions).filter(([name])=>!['appearance_producer','population_producer'].includes(name)));

function codes(value:unknown,names:readonly string[]){
 const values=closed(value,[...names]),expected=object(FIXTURE.code_sha256);
 for(const [name,d]of Object.entries(values)){digest(d);need(d===expected[name]);}
}

function manifest(value:unknown){
 const m=closed(value,['schema_version','status','scope','claim_scope','gates','time_kind','parameter_scope','model_versions','display_policy',
  'source_program_sha256','source_program_bytes','preparation_sha256','preparation_bytes','generated_program_sha256','generated_program_bytes',
  'population_artifact_sha256','stem_artifact_sha256','stem_program_sha256','program_rights','code_sha256','time_origin_utc',
  'initial_at_elapsed_seconds_exact','initial_state_sha256','terminal_state_sha256','sample_count']);
 flags(m);need(m.schema_version==='leaf-appearance-research-artifact-v1'&&m.status==='completed_software_fixture'&&
  m.time_kind==='synthetic_model_clock_not_observation'&&m.parameter_scope==='synthetic_software_fixture_only');
 constants(m.model_versions,FIXTURE.model_versions);constants(m.display_policy,APPEARANCE_DISPLAY);rights(m.program_rights);
 codes(m.code_sha256,Object.keys(FIXTURE.code_sha256));for(const key of REFERENCES)need(m[key]===FIXTURE[key]);utc(m.time_origin_utc);
 for(const key of ['source_program_bytes','preparation_bytes','generated_program_bytes'])integer(m[key],1,MAX);
 const at=exact(m.initial_at_elapsed_seconds_exact,'s'),original=exact(FIXTURE.initial_at_elapsed_seconds_exact,'s');
 need(at.n===original.n&&at.d===original.d);integer(m.sample_count,1,64);need(m.sample_count===FIXTURE.frames);
 need(m.stem_artifact_sha256===RATIONAL_MORPHOLOGY_SOURCE.artifact_sha256);return m;
}

function populationManifest(value:unknown,m:Record<string,unknown>){
 const p=closed(value,['schema_version','status','scope','claim_scope','gates','time_kind','parameter_scope','model_versions','display_policy',
  'program_sha256','program_bytes','program_rights','stem_artifact_sha256','stem_program_sha256','code_sha256','time_origin_utc',
  'initial_at_elapsed_seconds_exact','initial_state_sha256','terminal_state_sha256','samples']);flags(p);
 need(p.schema_version==='leaf-population-research-artifact-v1'&&p.status==='completed_software_fixture'&&
  p.time_kind==='synthetic_model_clock_not_observation'&&p.parameter_scope==='synthetic_software_fixture_only');
 constants(p.model_versions,POPULATION_MODELS);constants(p.display_policy,POPULATION_DISPLAY);rights(p.program_rights);
 codes(p.code_sha256,FIXTURE.population_source_paths);integer(p.program_bytes,1,MAX);
 need(p.program_sha256===m.generated_program_sha256&&p.program_bytes===m.generated_program_bytes&&same(p.program_rights,m.program_rights));
 for(const key of ['stem_artifact_sha256','stem_program_sha256','time_origin_utc','initial_state_sha256','terminal_state_sha256'])need(p[key]===m[key]);
 need(same(p.initial_at_elapsed_seconds_exact,m.initial_at_elapsed_seconds_exact));
 need(Array.isArray(p.samples)&&p.samples.length===FIXTURE.frames);let previous=p.initial_state_sha256,last=Date.parse(FIXTURE.time_origin_utc);
 for(let i=0;i<p.samples.length;i++){
  const d=closed(p.samples[i],['index','at','result_sha256','result_bytes','binding_sha256','binding_bytes','input_state_sha256','state_sha256','input_sha256','stem_result_sha256']);
  need(d.index===i&&d.input_state_sha256===previous);utc(d.at);need(Date.parse(d.at)>last);last=Date.parse(d.at);previous=d.state_sha256;
  for(const key of ['result_bytes','binding_bytes'])integer(d[key],1,MAX);
  for(const key of ['result_sha256','binding_sha256','input_state_sha256','state_sha256','input_sha256','stem_result_sha256'])digest(d[key]);
 }
 need(previous===p.terminal_state_sha256);return p;
}

export function decodeLeafAppearanceFrame(value:unknown,descriptor:unknown,root:unknown,populationRoot:unknown):LeafAppearanceFrame{
 const m=manifest(root),population=populationManifest(populationRoot,m);
 const d=closed(descriptor,['index','at','path','sha256','bytes','result_sha256','binding_sha256','stem_result_sha256']);
 integer(d.index,0,FIXTURE.frames-1);utc(d.at);integer(d.bytes,1,MAX);need(d.path===`frame-${d.index}.json`);
 for(const key of ['sha256','result_sha256','binding_sha256','stem_result_sha256'])digest(d[key]);
 digest(d.sha256);digest(d.stem_result_sha256);
 const sample=object((population.samples as unknown[])[d.index]);
 for(const key of ['index','at','result_sha256','binding_sha256','stem_result_sha256'])need(d[key]===sample[key]);
 const f=closed(value,['schema_version','scope','claim_scope','gates','artifact_sha256','result_sha256','binding_sha256','input_sha256',
  'index','at','time_origin_utc','tracked_leaf_count','tracked_leaf_area','leaves','stem','population_artifact_sha256',
  'source_program_sha256','preparation_sha256','policy_sha256','leaf_profile_sha256','display_policy']);flags(f);
 need(f.schema_version==='leaf-appearance-replay-frame-v1'&&f.artifact_sha256===FIXTURE.artifact_sha256&&
  f.index===d.index&&f.at===d.at&&f.result_sha256===d.result_sha256&&f.binding_sha256===d.binding_sha256&&
  f.input_sha256===sample.input_sha256&&f.time_origin_utc===m.time_origin_utc);
 for(const key of ['population_artifact_sha256','source_program_sha256','preparation_sha256','policy_sha256','leaf_profile_sha256']as const)need(f[key]===FIXTURE[key]);
 constants(f.display_policy,APPEARANCE_DISPLAY);area(f.tracked_leaf_area);integer(f.tracked_leaf_count,1,512);
 const stem=decodeMorphologyFrame(f.stem,{index:d.index,at:d.at,path:d.path,sha256:d.sha256,bytes:d.bytes,result_sha256:d.stem_result_sha256},RATIONAL_MORPHOLOGY_SOURCE);
 need(stem.schema_version==='morphology-replay-frame-v2'&&stem.at===f.at&&stem.time_origin_utc===f.time_origin_utc);
 const elapsed=BigInt((Date.parse(d.at)-Date.parse(stem.time_origin_utc))/1000);
 const declarations=FIXTURE.declared_leaves.filter(q=>{const b=exact(q.emerged_elapsed_seconds_exact,'s');return b.n<=elapsed*b.d;});
 need(Array.isArray(f.leaves)&&f.leaves.length===declarations.length&&f.tracked_leaf_count===declarations.length);
 for(let i=0;i<f.leaves.length;i++){
  const q=closed(f.leaves[i],['leaf_id','attachment_internode_id','curve_sha256','emerged_elapsed_seconds_exact','age_exact','area']),declared=declarations[i]!;
  need(q.leaf_id===declared.leaf_id&&q.attachment_internode_id===declared.attachment_internode_id&&q.curve_sha256===declared.curve_sha256);
  const b=exact(q.emerged_elapsed_seconds_exact,'s'),original=exact(declared.emerged_elapsed_seconds_exact,'s');
  need(b.n===original.n&&b.d===original.d&&b.n<=elapsed*b.d);exact(q.age_exact,'degC_day');area(q.area);
  const parent=stem.internodes.find(n=>n.internode_id===q.attachment_internode_id);need(parent);
  const birth=exact(parent.emerged_elapsed_seconds_exact,'s');need(birth.n*b.d<=b.n*birth.d);
 }
 return {...f,stem} as LeafAppearanceFrame;
}

function evidence(source:unknown,preparation:unknown,generated:unknown,m:Record<string,unknown>,stem:unknown){
 const s=closed(source,['schema_version','origin','program_id','rights','stem','initialization','policy','leaf_profile','display_policy']);
 need(s.schema_version==='leaf-appearance-software-program-v1'&&s.origin==='synthetic');id(s.program_id);rights(s.rights);
 need(same(s.rights,m.program_rights));constants(s.policy,FIXTURE.policy);constants(s.display_policy,APPEARANCE_DISPLAY);
 const parent=closed(s.stem,['artifact_sha256','program_sha256']);need(parent.artifact_sha256===m.stem_artifact_sha256&&parent.program_sha256===m.stem_program_sha256);
 const initial=closed(s.initialization,['input_id','initial_inventory']);id(initial.input_id);const inventory=object(initial.initial_inventory);
 need(Array.isArray(inventory.leaves)&&inventory.leaves.length===FIXTURE.initial_leaves);object(s.leaf_profile);
 const g=closed(generated,['schema_version','origin','program_id','rights','stem','initialization','births','display_policy']);
 need(g.schema_version==='leaf-population-software-program-v1'&&g.origin==='synthetic'&&g.program_id===s.program_id);
 rights(g.rights);need(same(g.rights,s.rights)&&same(g.stem,s.stem)&&same(g.initialization,s.initialization));constants(g.display_policy,POPULATION_DISPLAY);
 need(Array.isArray(g.births)&&g.births.length===FIXTURE.declared_leaves.length-FIXTURE.initial_leaves);
 const declared=[...inventory.leaves.map(raw=>{const item=closed(raw,['attachment_internode_id','initialization']),clock=object(object(item.initialization).clock_state);
  return {leaf_id:clock.leaf_id,attachment_internode_id:item.attachment_internode_id,emerged_elapsed_seconds_exact:clock.emerged_elapsed_seconds_exact};}),
  ...g.births.map(raw=>{const event=closed(raw,['leaf_id','attachment_internode_id','emerged_elapsed_seconds_exact','base_temperature','curve','normalization','initial_area']);
   return {leaf_id:event.leaf_id,attachment_internode_id:event.attachment_internode_id,emerged_elapsed_seconds_exact:event.emerged_elapsed_seconds_exact};})];
 for(let i=0;i<declared.length;i++){const q=declared[i]!,original=FIXTURE.declared_leaves[i]!;
  need(q.leaf_id===original.leaf_id&&q.attachment_internode_id===original.attachment_internode_id&&same(q.emerged_elapsed_seconds_exact,original.emerged_elapsed_seconds_exact));}
 const p=closed(preparation,['model_version','scope','claim_scope','gates','model_versions','input_sha256','source_program_sha256','source_program_bytes',
  'generated_program_sha256','generated_program','initial_state_sha256','initial_bindings_sha256','initial_bindings','derivation_sha256','derivation','display_policy','code_sha256']);
 flags(p);need(p.model_version===FIXTURE.model_versions.preparation);constants(p.model_versions,PREPARATION_MODELS);
 codes(p.code_sha256,Object.keys(FIXTURE.code_sha256).filter(name=>name!=='backend/app/crop_leaf_appearance_artifact_producer.py'));
 need(p.source_program_sha256===m.source_program_sha256&&p.source_program_bytes===m.source_program_bytes&&
  p.generated_program_sha256===m.generated_program_sha256&&p.initial_state_sha256===m.initial_state_sha256&&same(p.generated_program,g));
 constants(p.display_policy,APPEARANCE_DISPLAY);for(const key of ['input_sha256','initial_bindings_sha256','derivation_sha256'])digest(p[key]);
 const d=object(p.derivation);flags(d);need(d.model_version===FIXTURE.model_versions.birth_inputs&&same(d.policy,s.policy)&&
  d.policy_sha256===FIXTURE.policy_sha256&&d.leaf_profile_sha256===FIXTURE.leaf_profile_sha256&&d.stem_artifact_sha256===m.stem_artifact_sha256&&d.stem_program_sha256===m.stem_program_sha256);
 const originalStem=object(stem);rights(originalStem.program_rights);flags(originalStem);
 need(originalStem.schema_version==='morphology-research-artifact-v2'&&originalStem.program_sha256===m.stem_program_sha256);
}

export async function loadLeafAppearanceReplay(signal:AbortSignal):Promise<LeafAppearanceReplay>{
 const read=(name:string)=>{signal.throwIfAborted();return readStoredLeafFile('./leaf-appearance-replay/',name,signal);};
 const checked=async(name:string,expected:unknown,bytes?:unknown)=>{
  digest(expected);const raw=await read(name);need(await sha256(raw)===expected);
  if(bytes!==undefined){integer(bytes,1,MAX);need(raw.length===bytes);}return raw;
 };
 const raw=await checked('index.json',FIXTURE.index_sha256);
 const index=closed(parse(raw),['schema_version','scope','claim_scope','gates','model_versions','display_policy','artifact_sha256',
  'source_program_sha256','preparation_sha256','generated_program_sha256','population_artifact_sha256','stem_artifact_sha256','stem_program_sha256','rights','stem_rights','frames']);
 flags(index);need(index.schema_version==='leaf-appearance-public-fixture-v1'&&index.artifact_sha256===FIXTURE.artifact_sha256);
 constants(index.model_versions,FIXTURE.model_versions);constants(index.display_policy,APPEARANCE_DISPLAY);rights(index.rights);rights(index.stem_rights);
 const root=manifest(parse(await checked('root.json',FIXTURE.artifact_sha256)));
 for(const key of REFERENCES.slice(0,6))need(index[key]===root[key]);need(same(index.rights,root.program_rights));
 const input=parse(await checked('input.json',root.source_program_sha256,root.source_program_bytes));
 const preparation=parse(await checked('preparation.json',root.preparation_sha256,root.preparation_bytes));
 const generated=parse(await checked('generated-input.json',root.generated_program_sha256,root.generated_program_bytes));
 const population=parse(await checked('population-root.json',root.population_artifact_sha256));populationManifest(population,root);
 const stem=parse(await checked('stem-root.json',root.stem_artifact_sha256));
 const stemInput=object(parse(await checked('stem-input.json',root.stem_program_sha256)));
 need(same(index.stem_rights,object(stem).program_rights)&&same(index.stem_rights,stemInput.rights));evidence(input,preparation,generated,root,stem);
 need(Array.isArray(index.frames)&&index.frames.length===FIXTURE.frames);const frames:LeafAppearanceFrame[]=[];
 for(let i=0;i<index.frames.length;i++){
  const d=object(index.frames[i]);need(d.index===i&&d.path===`frame-${i}.json`);
  const frame=await checked(`frame-${i}.json`,d.sha256,d.bytes);frames.push(decodeLeafAppearanceFrame(parse(frame),d,root,population));
 }
 signal.throwIfAborted();return {artifact_sha256:FIXTURE.artifact_sha256,frames,policy:FIXTURE.policy};
}
