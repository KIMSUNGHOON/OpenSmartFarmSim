import {sha256} from './morphologyReplay';
import {growingGeometryOffset} from './growingGeometryReplay';
import {need,object,closed,digest,id,utc,integer,rights,readStoredLeafFile} from './storedLeafReplayIO';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {programInfo,IDENTITY,POINT as POINT_UNITS,POINT_BALANCE,type ProgramInfo,type Row} from './leafFundedBirthReplaySchema';
import {POLICY} from './leafFundedBirthReplayEvents';
import {COMPLETE_CROP_FIXTURE as F} from './completeCropReplayFixture';
import {FLAGS,DESCRIPTOR_FIELDS,flags,equal,list,quantity,block,contextLinks,checkedFrame,snapshot,frac,sameFraction,leq,type CompleteCropFrame} from './completeCropReplaySchema';
export type {CompleteCropFrame,CropLeaf,CropNode} from './completeCropReplaySchema';
export type CompleteCropScenario=keyof typeof F.scenarios;
export type CompleteCropAnchor={artifact_sha256:string;index_sha256:string;frames:number;public_files:number};
export type CompleteCropReplay={artifact_sha256:string;basis:Row;frames:CompleteCropFrame[]};
const CROP='funded-fractional-original-grid-continuation-research-v1',POINT='internode-logistic-length-point-research-v1';
const BINDING='funded-fractional-source-shoot-leaf-binding-research-v1',MODEL='funded-complete-source-prefix-fractional-geometry-research-v1';
const DESCRIPTOR=['path','sha256','bytes'];
function pins(value:unknown,keys:readonly string[]){const q=closed(value,[...keys]),expected:Record<string,string>=F.code_sha256;for(const key of keys)need(q[key]===expected[key]);}
function sourceDescriptor(value:unknown){const d=closed(value,['sha256','bytes']);digest(d.sha256);integer(d.bytes,1,2*1024**2);return d;}
function wireObject(fields:Record<string,string>){return '{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+fields[k]).join(',')+'}';}
export function isCompleteCropScenario(v:unknown):v is CompleteCropScenario{return typeof v==='string'&&Object.hasOwn(F.scenarios,v);}

/** The anchor is independently trusted; downloaded content cannot authorize itself. */
export async function readCompleteCropReplay(readFile:(name:string)=>Promise<Uint8Array>,anchor:CompleteCropAnchor,signal:AbortSignal):Promise<CompleteCropReplay>{
 anchor={...anchor};signal.throwIfAborted();closed(anchor,['artifact_sha256','index_sha256','frames','public_files']);digest(anchor.artifact_sha256);digest(anchor.index_sha256);integer(anchor.frames,1,512);integer(anchor.public_files,1,4609);
 let downloaded=0;
 const read=async(name:string)=>{signal.throwIfAborted();need(/^(?:index\.json|root\.json|NOTICE\.txt|blob-[0-9a-f]{64}\.json|frame-(?:0|[1-9]\d{0,2})\.json)$/.test(name));
  const value=await readFile(name);signal.throwIfAborted();need(value instanceof Uint8Array&&value.byteLength>0&&value.byteLength<=2*1024**2);downloaded+=value.byteLength;need(downloaded<=64*1024**2);return new Uint8Array(value);};
 const text=(raw:Uint8Array)=>new TextDecoder('utf-8',{fatal:true}).decode(raw);
 const document=(raw:string)=>{wireFields(raw);return object(JSON.parse(raw));};
 const indexRaw=text(await read('index.json'));need(await wireHash(indexRaw)===anchor.index_sha256);
 const index=closed(document(indexRaw),[...Object.keys(FLAGS),'artifact_sha256','code_sha256','exporter_sha256','output_writer_sha256','basis','root','packet','notice','blobs','frames','sample_scalars']);
 flags(index,'complete-crop-public-fixture-v1');need(index.artifact_sha256===anchor.artifact_sha256&&index.exporter_sha256===F.exporter_sha256&&index.output_writer_sha256===F.output_writer_sha256);pins(index.code_sha256,Object.keys(F.code_sha256));
 const descriptors=list(index.blobs);need(descriptors.length>=1&&descriptors.length<=4096&&descriptors.length+anchor.frames+1===anchor.public_files);
 const blobs=new Map<string,{raw:string;bytes:number;path:string}>(),paths=new Set<string>();
 for(const value of descriptors){
  const d=closed(value,DESCRIPTOR);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  const path=d.sha256===anchor.artifact_sha256?'root.json':d.sha256===F.notice_sha256?'NOTICE.txt':`blob-${d.sha256}.json`;
  need(d.path===path&&!paths.has(path)&&!blobs.has(d.sha256));paths.add(path);const bytes=await read(path);need(bytes.byteLength===d.bytes&&await sha256(bytes)===d.sha256);const raw=text(bytes);
  if(path!=='NOTICE.txt')document(raw);blobs.set(d.sha256,{raw,bytes:bytes.byteLength,path});
 }
 const get=(value:unknown,maximum=2*1024**2)=>{const d=sourceDescriptor(value),b=blobs.get(String(d.sha256));need(b&&b.bytes===d.bytes&&b.bytes<=maximum);return b.raw;};
 const doc=(hash:unknown)=>{digest(hash);const b=blobs.get(hash);need(b&&b.path!=='NOTICE.txt');return document(b.raw);};
 for(const key of ['root','packet','notice']){const d=closed(index[key],DESCRIPTOR),b=blobs.get(String(d.sha256));need(b&&b.path===d.path&&b.bytes===d.bytes);}
 need(object(index.root).sha256===anchor.artifact_sha256&&object(index.notice).sha256===F.notice_sha256);
 const root=closed(doc(anchor.artifact_sha256),[...Object.keys(FLAGS),'code_sha256','packet','contexts','source_blobs','geometry_receipts','frames']);flags(root);pins(root.code_sha256,Object.keys(F.code_sha256));
 equal(root.code_sha256,index.code_sha256);equal(root.packet,{sha256:object(index.packet).sha256,bytes:object(index.packet).bytes});
 const packetRaw=get(root.packet),packet=closed(document(packetRaw),['basis','status','segment_receipts','sample_scalars','frames','current_checkpoint_RHS_evaluations','past_ODE_or_clock_advances']);
 need(packet.status==='completed_software_fixture'&&packet.past_ODE_or_clock_advances===0);integer(packet.sample_scalars,1,32768);equal(packet.sample_scalars,index.sample_scalars);
 const b=closed(packet.basis,['model_version','scope','G0_G4','R2','code_sha256','source_selection','model_floor_area','stem_source_state_sha256','development_origin_utc','simulation_start_development_seconds_exact','initial_bindings','source_rights','equation_reference','new_stem_carbon_allocation','initial_leaf_history']);
 need(b.model_version===MODEL&&b.scope==='software_research_only'&&b.G0_G4==='not_assessed'&&b.R2==='not_approved');pins(b.code_sha256,F.code_sets.basis);equal(b,index.basis);
 need(await wireHash(wireFields(indexRaw).basis!)===await wireHash(wireFields(packetRaw).basis!));
 need(b.new_stem_carbon_allocation==='not_independently_allocated_in_aggregate_stem_pool'&&b.initial_leaf_history==='explicit_carry_over_ages_and_links_not_verified_past_emergence');need(quantity(b.model_floor_area,'m2_floor')>0);
 const selection=closed(b.source_selection,['leaf_root_sha256','stem_root_sha256','stem_start_index','bracket_index','time_tolerance_seconds_exact']);
 const leafRoot=doc(selection.leaf_root_sha256),stemRoot=doc(selection.stem_root_sha256);pins(leafRoot.code_sha256,F.code_sets.leaf);pins(stemRoot.code_sha256,F.code_sets.stem);
 need(leafRoot.scope==='software_research_only'&&leafRoot.G0_G4==='not_assessed'&&stemRoot.scope==='software_research_only'&&stemRoot.gates==='not_assessed'&&stemRoot.schema_version==='morphology-research-artifact-v2'&&leafRoot.schema_version==='funded-leaf-research-artifact-v1');
 rights(leafRoot.source_rights);rights(stemRoot.program_rights);equal(b.source_rights,{leaf:leafRoot.source_rights,stem:stemRoot.program_rights});equal(b.equation_reference,stemRoot.equation_reference);
 const initial=closed(b.initial_bindings,['schema_version','input_id','origin','context_sha256','leaf_root_sha256','stem_root_sha256','root_initial_state_sha256','model_floor_area','initial_attachments','rights','reviewer']);
 need(initial.schema_version==='funded-fractional-initial-links-v1'&&initial.origin==='synthetic');id(initial.input_id);id(initial.reviewer);rights(initial.rights);equal(initial.model_floor_area,b.model_floor_area);
 need(initial.leaf_root_sha256===selection.leaf_root_sha256&&initial.stem_root_sha256===selection.stem_root_sha256&&initial.root_initial_state_sha256===leafRoot.initial_state_sha256);
 const contexts=new Map<string,{q:Row;raw:string}>(),contextDescriptors=list(root.contexts);need(contextDescriptors.length>=1&&contextDescriptors.length<=511);
 for(const d of contextDescriptors){const raw=get(d),q=closed(document(raw),['version','code_sha256','source','original','program','anchors','branch_initial','base_lifetime_transfers','base_prior_budgets','records','seed']);
  need(q.version===CROP);pins(q.code_sha256,F.code_sets.context);await contextLinks(raw);const source=closed(q.source,['version','candidate','program','anchors','past_event_ids','code_sha256','profile_sha256']);need(source.version==='funded-fractional-structural-birth-point-research-v1');pins(source.code_sha256,F.code_sets.point);equal(source.profile_sha256,Object.fromEntries(Object.entries(IDENTITY.profile_sha256).map(([k,v])=>[k+'_profile',v])));
  const candidate=object(source.candidate);pins(candidate.source_code_sha256,F.code_sets.candidate);need(candidate.code_sha256===F.code_sha256['backend/app/crop_funded_event_state.py']);
  const hash=String(object(d).sha256);need(!contexts.has(hash));contexts.set(hash,{q,raw});}
 const contextKeys=[...contexts.keys()],first=contexts.get(contextKeys[0]!)!.q,candidate=object(object(first.source).candidate),original=object(first.original);
 need(initial.context_sha256===contextKeys[0]);equal(candidate.selection,selection);const left=object(object(candidate.source_root_certificate).source_bracket).left_frame_index;integer(left,0,511);
 const sources=object(leafRoot.sources);need(object(sources.license_notice).sha256===F.notice_sha256);
 for(const [name,hash]of Object.entries(IDENTITY.profile_sha256)){need(object(sources[name+'_profile']).sha256===hash);get(sources[name+'_profile']);}
 const sourceProgram=get(sources.program),sourceInputs=closed(document(get(sources.inputs)),['schema_version','input_id','origin','rights','time_origin_utc','step_seconds','step_count','program','births']);
 need(sourceInputs.schema_version==='funded-leaf-artifact-input-v1'&&sourceInputs.origin==='synthetic'&&sourceInputs.time_origin_utc===leafRoot.time_origin_utc);integer(sourceInputs.step_count,1,4096);need(typeof sourceInputs.step_seconds==='number'&&sourceInputs.step_seconds>0);
 rights(sourceInputs.rights);equal(sourceInputs.rights,leafRoot.source_rights);equal(sourceInputs.program,document(get(sources.request)));
 const programs=new Map<string,ProgramInfo>();
 const addProgram=async(raw:string)=>{const hash=await wireHash(raw);if(!programs.has(hash))programs.set(hash,await programInfo(raw));};
 await addProgram(sourceProgram);
 for(const e of list(leafRoot.events))await addProgram(wireFields(get(object(e).context_snapshot)).program!);
 for(const c of contexts.values())await addProgram(wireFields(c.raw).program!);
 const rootInfo=programs.get(await wireHash(sourceProgram))!;equal(rootInfo.program.model_floor_area,b.model_floor_area);
 const links=list(initial.initial_attachments,rootInfo.leaves.length),metadata=new Map<string,{parent:string;kind:string;event:string|null;birth:unknown}>();
 links.forEach((v,i)=>{const q=closed(v,['leaf_id','attachment_internode_id']);need(q.leaf_id===rootInfo.leaves[i]!.leaf_id);id(q.attachment_internode_id);metadata.set(String(q.leaf_id),{parent:q.attachment_internode_id,kind:'explicit_preexisting_initial_link',event:null,birth:null});});
 const addEvents=(events:unknown,birth:unknown,kind:string)=>{for(const v of list(events)){const e=closed(v,['event_id','attachment_internode_id','incoming_temperature','leaf']);id(e.event_id);id(e.attachment_internode_id);const leaf=object(e.leaf);id(leaf.leaf_id);need(!metadata.has(leaf.leaf_id));metadata.set(leaf.leaf_id,{parent:e.attachment_internode_id,kind,event:e.event_id,birth});}};
 for(const v of list(sourceInputs.births)){const p=closed(v,['step_index','point_inputs']);integer(p.step_index,0,4096);addEvents(object(p.point_inputs).events,growingGeometryOffset(Number(sourceInputs.step_seconds),p.step_index),'original_funded_point');}
 const recordsByContext=new Map<string,unknown[]>();let priorRecords:unknown[]=[];
 for(const [ci,key]of contextKeys.entries()){
  const c=contexts.get(key)!,rows=list(c.q.records,ci+1);if(ci){equal(rows.slice(0,-1),priorRecords);equal(c.q.source,first.source);equal(c.q.original,original);}const row=closed(rows.at(-1),['inputs','input_sha256','at','new_leaves','receipts','point_flows','balances','branch_air_integral_at_birth','lifetime_air_integral_at_birth','before_checkpoint_sha256','after_sample_sha256','after_program_sha256']),input=closed(row.inputs,['schema_version','input_id','origin','policy','context_sha256','at_elapsed_seconds_exact','model_floor_area','events',ci===0?'candidate_sha256':'checkpoint_sha256']);
  need(input.origin==='synthetic'&&input.policy===POLICY&&input.schema_version===(ci===0?'funded-fractional-birth-point-input-v1':'fractional-continuation-birth-input-v1'));id(input.input_id);digest(input.context_sha256);equal(input.model_floor_area,b.model_floor_area);
  const rowRaw=wireItems(wireFields(c.raw).records!).at(-1)!;need(await wireHash(wireFields(rowRaw).inputs!)===row.input_sha256);
  block(row.point_flows,POINT_UNITS);const budgets=closed(row.balances,Object.keys(POINT_BALANCE));for(const [k,u]of Object.entries(POINT_BALANCE)){const q=closed(budgets[k],['residual','budget']);need(quantity(q.budget,u)>=0&&Math.abs(quantity(q.residual,u))<=quantity(q.budget,u));}
  equal(row.at,input.at_elapsed_seconds_exact);const events=list(input.events),receipts=list(row.receipts,events.length);need(events.length>=1);
  for(const [j,v]of events.entries()){const e=object(v),r=object(receipts[j]);need(r.event_id===e.event_id&&r.attachment_internode_id===e.attachment_internode_id);const init=object(r.initialization);need(init.scope==='software_research_only'&&init.gates==='not_assessed');need(quantity(object(e.leaf).initial_carbon,'mg_CH2O/m2_floor')>0);}
  addEvents(events,row.at,'fractional_branch_point');recordsByContext.set(key,rows);priorRecords=rows;
 }
 const stemProgramRaw=String(blobs.get(String(stemRoot.program_sha256))?.raw);document(stemProgramRaw);integer(selection.stem_start_index,-1,list(stemRoot.samples).length-1);
 let stemStateRaw:string;
 if(selection.stem_start_index===-1)stemStateRaw=wireFields(stemProgramRaw).initial_state!;
 else{const d=object(list(stemRoot.samples)[selection.stem_start_index]);stemStateRaw=wireFields(String(blobs.get(String(d.result_sha256))?.raw)).state!;need(await wireHash(stemStateRaw)===d.state_sha256);}
 need(await wireHash(stemStateRaw)===b.stem_source_state_sha256);const stemState=document(stemStateRaw),timeline=object(stemState.timeline_state);utc(timeline.at);utc(timeline.started_at);
 need(timeline.at===leafRoot.time_origin_utc&&timeline.started_at===b.development_origin_utc);const offset=frac(b.simulation_start_development_seconds_exact);need(offset.n===BigInt((Date.parse(timeline.at)-Date.parse(timeline.started_at))/1000)*offset.d);
 const sourceNodes=list(stemState.internodes),sourceNodeRaw=wireItems(wireFields(stemStateRaw).internodes!);
 const tfields=wireFields(wireFields(stemStateRaw).timeline_state!),identityFields:Record<string,string>={birth_age_exact:tfields.next_threshold_exact!,sequence:tfields.next_sequence!};
 for(const k of ['development_origin_id','schedule_id','shoot_id','started_at'])identityFields[k]=tfields[k]!;
 const bornID='internode:'+await wireHash(wireObject(identityFields)),bornAt=frac(object(candidate.at).elapsed_seconds_exact);
 const firstContext=contexts.get(contextKeys[0]!)!,candidateRaw=wireFields(wireFields(firstContext.raw).source!).candidate!,candidateSHA=await wireHash(candidateRaw);
 need(candidate.model_version==='funded-air-dense-event-state-and-exact-time-refinement-research-v1'&&candidate.scope==='software_research_only'&&candidate.G0_G4==='not_assessed'&&candidate.integrator_checkpoint===null&&candidate.new_internodes==='not_created');
 const firstRecord=object(list(first.records)[0]),firstInput=object(firstRecord.inputs);
 need(firstInput.candidate_sha256===candidateSHA&&firstRecord.before_checkpoint_sha256===candidate.source_left_checkpoint_sha256);
 equal(firstRecord.at,object(candidate.at).elapsed_seconds_exact);equal(firstInput.model_floor_area,b.model_floor_area);
 const adds=(parent:unknown,birth:unknown)=>{const x=frac(parent),y=frac(birth);return x.n*offset.d*y.d<=(offset.n*y.d+y.n*offset.d)*x.d;};
 const birthRaw=wireFields(String(blobs.get(String(object(contextDescriptors[0]).sha256))?.raw)).source!;
 need(await wireHash(birthRaw)===object(object(list(first.records)[0]).inputs).context_sha256);
 const frameRaws=wireItems(wireFields(packetRaw).frames!),stored=list(packet.frames,anchor.frames),publicFrames=list(index.frames,anchor.frames),rootFrames=list(root.frames,anchor.frames),geometry=list(root.geometry_receipts,anchor.frames),receipts=list(packet.segment_receipts,contexts.size);
 const frames:CompleteCropFrame[]=[];let scalar=0,denseCount=0,fractionalCount=0,ci=-1;
 for(let i=0;i<anchor.frames;i++){
  signal.throwIfAborted();const f=object(stored[i]),e=object(f.evidence),info=programs.get(String(f.program_sha256));need(info);const d=closed(publicFrames[i],[...DESCRIPTOR_FIELDS,...DESCRIPTOR]);
  integer(d.index,0,511);need(d.index===i&&d.path===`frame-${i}.json`);for(const k of DESCRIPTOR_FIELDS)equal(d[k],object(rootFrames[i])[k]);
  const bytes=await read(`frame-${i}.json`);integer(d.bytes,1,2*1024**2);need(bytes.byteLength===d.bytes&&await sha256(bytes)===d.sha256);const dtoRaw=text(bytes),dto=closed(document(dtoRaw),['schema_version','artifact_sha256','index','frame']);
  need(dto.schema_version==='complete-crop-public-frame-v1'&&dto.artifact_sha256===anchor.artifact_sha256);integer(dto.index,0,511);need(dto.index===i);
  const fraw=wireFields(dtoRaw).frame!;need(await wireHash(fraw)===d.frame_sha256&&await wireHash(frameRaws[i]!)===d.frame_sha256);equal(dto.frame,f);
  const fields=wireFields(fraw),eRaw=wireFields(fields.evidence!),s=snapshot(f);let sampleRaw:string;
  if(e.checkpoint===null){need(e.kind==='checked_dense_candidate');closed(e,['kind','candidate_sha256','candidate','checkpoint_sha256','checkpoint']);need(i===left+1&&e.checkpoint_sha256===null&&f.phase==='before_birth');denseCount++;sampleRaw=fields.snapshot!;equal(e.candidate,candidate);need(await wireHash(eRaw.candidate!)===e.candidate_sha256);const initial=object(first.branch_initial);for(const k of ['state','derived','curve_residuals','curve_invariant_changes'])equal(s[k],initial[k]);
   equal(f.at,candidate.at);need(f.event_sequence===frames[i-1]!.event_sequence+1);
   need(await wireHash(wireObject({event_sequence:String(f.event_sequence),model_version:JSON.stringify(CROP),phase:'"before_birth"',previous:JSON.stringify(frames[i-1]!.raw.output_prefix_sha256),sample:wireFields(firstContext.raw).branch_initial!}))===f.output_prefix_sha256);
  }
  else{const cp=object(e.checkpoint),cpRaw=eRaw.checkpoint!;need(await wireHash(cpRaw)===e.checkpoint_sha256);sampleRaw=wireFields(cpRaw).last_confirmed!;
   if(e.kind==='original_funded_checkpoint'){closed(e,['kind','source_frame_index','checkpoint_sha256','checkpoint']);need(e.source_frame_index===i&&i<=left);const source=object(list(leafRoot.samples)[i]);need(source.checkpoint_sha256===e.checkpoint_sha256);need(blobs.get(String(e.checkpoint_sha256))?.raw===cpRaw&&new TextEncoder().encode(cpRaw).byteLength<=1024**2);equal(object(f.at).elapsed_seconds_exact,source.elapsed_seconds_exact);need(f.phase===source.phase&&f.event_sequence===source.event_sequence&&f.output_prefix_sha256===cp.output_prefix_sha256);}
   else{need(e.kind==='fractional_checkpoint');closed(e,['kind','context_sha256','checkpoint_sha256','checkpoint']);fractionalCount++;
    if(ci<0||e.context_sha256!==contextKeys[ci]){if(ci>=0)need(object(receipts[ci]).last_checkpoint_sha256===frames[i-1]!.checkpoint_sha256);ci++;need(e.context_sha256===contextKeys[ci]);const c=contexts.get(contextKeys[ci]!)!.q;need(cp.segment_steps===0&&f.phase==='after_birth');equal(cp.last_confirmed,object(c.seed).sample);const receipt=closed(receipts[ci],['context_sha256','first_checkpoint_sha256','initial_bindings_sha256','last_checkpoint_sha256']);need(receipt.first_checkpoint_sha256===e.checkpoint_sha256);
    const linksRaw=wireFields(wireFields(wireFields(packetRaw).basis!).initial_bindings!);linksRaw.context_sha256=JSON.stringify(contextKeys[ci]);need(await wireHash(wireObject(linksRaw))===receipt.initial_bindings_sha256);
    need(receipt.context_sha256===contextKeys[ci]&&f.event_sequence===frames[i-1]!.event_sequence+(ci===0?0:1));
     if(ci){const row=object(recordsByContext.get(contextKeys[ci]!)!.at(-1));need(row.before_checkpoint_sha256===object(frames[i-1]!.raw.evidence).checkpoint_sha256&&object(row.inputs).context_sha256===contextKeys[ci-1]);}}
    else need(cp.segment_steps===Number(object(object(frames[i-1]!.raw.evidence).checkpoint).segment_steps)+1&&f.phase==='grid_endpoint'&&f.event_sequence===frames[i-1]!.event_sequence);
    const active=contexts.get(contextKeys[ci]!)!.q,seed=object(active.seed),start=frac(object(object(seed.sample).at).elapsed_seconds_exact),dt=Number(original.grid_step_seconds),step=frac(growingGeometryOffset(dt,1));
    const firstGrid=Number(start.n*step.d/(start.d*step.n));integer(firstGrid,0,4096);need(cp.branch_steps===Number(seed.branch_step_count)+Number(cp.segment_steps));
    if(cp.segment_steps===0)equal(cp.at,object(seed.sample).at);else sameFraction(object(cp.at).elapsed_seconds_exact,growingGeometryOffset(dt,firstGrid+Number(cp.segment_steps)));
    need(cp.grid_step_index===firstGrid+Number(cp.segment_steps));
    equal(cp.at,f.at);need(cp.context_sha256===e.context_sha256&&cp.phase===f.phase&&cp.event_sequence===f.event_sequence&&cp.output_cursor===f.output_cursor);
    const previous=String(frames[i-1]!.raw.output_prefix_sha256);need(await wireHash(wireObject({event_sequence:String(cp.event_sequence),model_version:JSON.stringify(CROP),phase:JSON.stringify(cp.phase),previous:JSON.stringify(previous),sample:sampleRaw}))===f.output_prefix_sha256);
   }}
  need(await wireHash(wireFields(sampleRaw).state!)===d.state_sha256);for(const key of ['at','phase','event_sequence','output_cursor','output_prefix_sha256'])equal(f[key],d[key]);
  const view=checkedFrame(f,info,i);need(view.at.time_origin_utc===leafRoot.time_origin_utc);if(i)need(leq(frames[i-1]!.at.elapsed_seconds_exact,view.at.elapsed_seconds_exact));
  for(const leaf of view.leaves){const expected=metadata.get(leaf.leaf_id);need(expected);need(leaf.attachment_internode_id===expected.parent&&leaf.kind===expected.kind&&leaf.event_id===expected.event);equal(leaf.birth_at_elapsed_seconds_exact,expected.birth);}
  need(view.internodes.length===sourceNodes.length+(e.kind==='original_funded_checkpoint'?0:1));
  for(const [j,v]of sourceNodes.entries()){const old=object(v),state=object(old.length_state),node=view.internodes[j]!;need(node.internode_id===object(state.clock_state).internode_id&&node.sequence===old.sequence&&node.kind==='selected_original');equal(node.curve,state.curve);equal(node.initial_anchor,state.anchor);equal(node.development_birth_seconds_exact,object(state.clock_state).emerged_elapsed_seconds_exact);need(node.source_length_state_sha256===await wireHash(wireFields(sourceNodeRaw[j]!).length_state!));}
  if(e.kind!=='original_funded_checkpoint'){
   const node=view.internodes.at(-1)!,birth=object(object(f.shoot).birth),profile=object(stemState.emergence_profile),development=frac(node.development_birth_seconds_exact);
   need(node.internode_id===bornID&&node.sequence===timeline.next_sequence&&node.kind==='numerical_threshold_birth'&&node.source_length_state_sha256===null);equal(node.curve,profile.curve);
   need(development.n*offset.d*bornAt.d===(offset.n*bornAt.d+bornAt.n*offset.d)*development.d);
   need(birth.internode_id===bornID&&birth.candidate_sha256===candidateSHA&&birth.sequence===timeline.next_sequence);equal(birth.at_elapsed_seconds_exact,object(candidate.at).elapsed_seconds_exact);equal(birth.numerical_root_interval,object(candidate.source_root_certificate).numerical_root_interval);
   const anchor=closed(node.initial_anchor,['at_elapsed_seconds_exact','age_exact','requested_initial_length','canonical_initial_length']);sameFraction(anchor.age_exact,{numerator:'0',denominator:'1',unit:'degC_day'},'degC_day');equal(anchor.at_elapsed_seconds_exact,birth.at_elapsed_seconds_exact);equal(anchor.requested_initial_length,profile.initial_length);
  }else need(object(f.shoot).birth===null);
  for(const leaf of view.leaves){const parent=view.internodes.find(n=>n.internode_id===leaf.attachment_internode_id)!;need(adds(parent.development_birth_seconds_exact,leaf.birth_at_elapsed_seconds_exact??{numerator:'0',denominator:'1',unit:'s'}));}
  for(const [j,node]of view.internodes.entries()){
   const receipt=document(get(list(geometry[i],view.internodes.length)[j],64*1024));closed(receipt,['request','response']);const rr=wireFields(get(list(geometry[i])[j],64*1024)),req=closed(receipt.request,['input_id','origin','thermal_age_basis','age_exact','curve']),response=closed(receipt.response,['model_version','scope','claim_scope','gates','input_sha256','curve_sha256','age_exact','length']);
   need(req.origin==='synthetic'&&req.thermal_age_basis==='since_internode_emergence'&&response.model_version===POINT&&response.scope==='software_research_only'&&response.claim_scope==='synthetic_crop_math_only'&&response.gates==='not_assessed');equal(req.age_exact,node.age_exact);equal(req.curve,node.curve);equal(response.age_exact,node.age_exact);equal(response.length,node.length);
   need(await wireHash(wireObject({inputs:rr.request!,model_version:JSON.stringify(POINT)}))===node.point_input_sha256&&response.input_sha256===node.point_input_sha256);
   need(await wireHash(wireObject({curve:wireFields(rr.request!).curve!,rate_model_version:'"internode-logistic-thermal-rate-research-v1"'}))===node.curve_sha256&&response.curve_sha256===node.curve_sha256);
   const identity=node.kind==='selected_original'?{id:node.internode_id,model:e.kind==='original_funded_checkpoint'?MODEL:BINDING,source:b.stem_source_state_sha256}:{candidate:object(object(f.shoot).birth).candidate_sha256,id:node.internode_id,model:BINDING};
   need(req.input_id===await wireHash(JSON.stringify(identity)));
  }
  scalar+=list(s.state).length+2*view.leaves.length+8;need(scalar<=32768);frames.push(view);
 }
 need(object(receipts[ci]).last_checkpoint_sha256===frames.at(-1)!.checkpoint_sha256);
 need(denseCount===1&&ci+1===contexts.size&&fractionalCount===packet.current_checkpoint_RHS_evaluations&&scalar===packet.sample_scalars);
 sameFraction(frames[0]!.at.elapsed_seconds_exact,{numerator:'0',denominator:'1',unit:'s'});sameFraction(frames.at(-1)!.at.elapsed_seconds_exact,growingGeometryOffset(Number(original.grid_step_seconds),Number(original.grid_step_count)));
 for(const d of list(root.source_blobs))get(d);signal.throwIfAborted();return structuredClone({artifact_sha256:anchor.artifact_sha256,basis:b,frames});
}
export async function loadCompleteCropReplay(scenario:string,signal:AbortSignal){signal.throwIfAborted();need(isCompleteCropScenario(scenario));const replay=await readCompleteCropReplay(name=>readStoredLeafFile(`./complete-crop-replay/${scenario}/`,name,signal),F.scenarios[scenario],signal);return {...replay,scenario};}
export class CompleteCropRequest{
 private generation=0;private controller?:AbortController;
 cancel(){this.generation++;this.controller?.abort();this.controller=undefined;}
 async load(scenario:string){this.cancel();const generation=this.generation,c=new AbortController();this.controller=c;try{const result=await loadCompleteCropReplay(scenario,c.signal);c.signal.throwIfAborted();need(generation===this.generation);return result;}finally{if(generation===this.generation)this.controller=undefined;}}
}
