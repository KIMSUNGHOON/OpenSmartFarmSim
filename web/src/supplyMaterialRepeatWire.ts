import {sha256} from './morphologyReplay';
import {compare,fraction} from './supplyMorphologyGraphValues';
import {utc} from './storedLeafReplayIO';

const MAX_DOCUMENT=2097152,MAX_PHYSICAL_BYTES=67108864,MAX_FILES=4096;
const GROUPS=['original','base','forcing','material','repeat','points','frames'] as const;
const CODE_PATHS=[
 'backend/app/content_access.py',
 'backend/app/crop_area_canopy_energy.py',
 'backend/app/crop_canopy_energy_transport.py',
 'backend/app/crop_canopy_exchange.py',
 'backend/app/crop_explicit_lai_carbon_cohorts.py',
 'backend/app/crop_explicit_lai_climate_rhs.py',
 'backend/app/crop_explicit_lai_photosynthesis.py',
 'backend/app/crop_fruit_allocation.py',
 'backend/app/crop_fruit_cohorts.py',
 'backend/app/crop_fruit_startup.py',
 'backend/app/crop_fruit_transport.py',
 'backend/app/crop_funded_event_state.py',
 'backend/app/crop_funded_event_time.py',
 'backend/app/crop_funded_shoot_clock.py',
 'backend/app/crop_growing_geometry_climate.py',
 'backend/app/crop_growth_rates.py',
 'backend/app/crop_internode_elongation.py',
 'backend/app/crop_internode_length.py',
 'backend/app/crop_internode_length_change.py',
 'backend/app/crop_leaf_area.py',
 'backend/app/crop_leaf_area_change.py',
 'backend/app/crop_leaf_carbon_partition.py',
 'backend/app/crop_leaf_carbon_stock_artifact_producer.py',
 'backend/app/crop_leaf_carbon_stock_artifact_reader.py',
 'backend/app/crop_leaf_carbon_stock_continuation.py',
 'backend/app/crop_leaf_carbon_stock_dynamics.py',
 'backend/app/crop_leaf_carbon_stock_rhs.py',
 'backend/app/crop_leaf_expansion.py',
 'backend/app/crop_leaf_funded_birth_continuation.py',
 'backend/app/crop_leaf_funded_birth_point.py',
 'backend/app/crop_leaf_partition_climate_rhs.py',
 'backend/app/crop_morphology_artifact_io.py',
 'backend/app/crop_morphology_artifact_reader.py',
 'backend/app/crop_morphology_thermal_clock.py',
 'backend/app/crop_organ_current_shoot_clock.py',
 'backend/app/crop_organ_fractional_candidate.py',
 'backend/app/crop_organ_fractional_clocks.py',
 'backend/app/crop_organ_fractional_context.py',
 'backend/app/crop_organ_fractional_continuation.py',
 'backend/app/crop_organ_fractional_point.py',
 'backend/app/crop_organ_funded_continuation.py',
 'backend/app/crop_organ_next_threshold.py',
 'backend/app/crop_organ_repeat.py',
 'backend/app/crop_organ_repeat_events.py',
 'backend/app/crop_organ_repeat_proofs.py',
 'backend/app/crop_organ_successor_candidate.py',
 'backend/app/crop_organ_successor_point.py',
 'backend/app/crop_phytomer_emergence.py',
 'backend/app/crop_plant_cohort_rates.py',
 'backend/app/crop_rational_internode_length.py',
 'backend/app/crop_rational_morphology_artifact_producer.py',
 'backend/app/crop_rational_morphology_artifact_reader.py',
 'backend/app/crop_rational_morphology_clock.py',
 'backend/app/crop_rational_new_internodes.py',
 'backend/app/crop_rational_shoot_inventory.py',
 'backend/app/crop_shoot_timeline.py',
 'backend/app/crop_stem_root_carbon_partition.py',
 'backend/app/crop_stem_root_carbon_stock_rhs.py',
 'backend/app/crop_stem_root_funded_internode_point.py',
 'backend/app/crop_stem_root_funded_leaf_point.py',
 'backend/app/crop_stem_root_initial_binding.py',
 'backend/app/crop_stem_root_partition_climate_rhs.py',
 'backend/app/crop_stem_root_stock_continuation.py',
 'backend/app/crop_stem_root_stock_dynamics.py',
 'backend/app/crop_supply_forcing_interval.py',
 'backend/app/crop_supply_forcing_owner.py',
 'backend/app/crop_supply_forcing_threshold.py',
 'backend/app/crop_supply_forcing_threshold_state.py',
 'backend/app/crop_supply_material_artifact_producer.py',
 'backend/app/crop_supply_material_artifact_reader.py',
 'backend/app/crop_supply_material_owner.py',
 'backend/app/crop_supply_material_point.py',
 'backend/app/crop_supply_material_proof.py',
 'backend/app/crop_supply_material_repeat_artifact_producer.py',
 'backend/app/crop_supply_material_repeat_artifact_reader.py',
 'backend/app/crop_supply_material_repeat_owner.py',
 'backend/app/crop_supply_material_repeat_point.py',
 'backend/app/crop_supply_material_repeat_proof.py',
 'backend/app/crop_supply_morphology_artifact_producer.py',
 'backend/app/crop_supply_morphology_artifact_projection.py',
 'backend/app/crop_supply_morphology_artifact_reader.py',
 'backend/app/crop_supply_morphology_birth_stage.py',
 'backend/app/crop_supply_morphology_books.py',
 'backend/app/crop_supply_morphology_candidate.py',
 'backend/app/crop_supply_morphology_candidate_books.py',
 'backend/app/crop_supply_morphology_context.py',
 'backend/app/crop_supply_morphology_context_proofs.py',
 'backend/app/crop_supply_morphology_newborn_books.py',
 'backend/app/crop_supply_morphology_newborn_candidate.py',
 'backend/app/crop_supply_morphology_newborn_candidate_books.py',
 'backend/app/crop_supply_morphology_newborn_point.py',
 'backend/app/crop_supply_morphology_newborn_point_books.py',
 'backend/app/crop_supply_morphology_newborn_point_core.py',
 'backend/app/crop_supply_morphology_newborn_resume.py',
 'backend/app/crop_supply_morphology_point.py',
 'backend/app/crop_supply_morphology_point_books.py',
 'backend/app/crop_supply_morphology_point_core.py',
 'backend/app/crop_supply_morphology_repeat_books.py',
 'backend/app/crop_supply_morphology_repeat_candidate.py',
 'backend/app/crop_supply_morphology_repeat_candidate_books.py',
 'backend/app/crop_supply_morphology_repeat_context.py',
 'backend/app/crop_supply_morphology_repeat_encoding.py',
 'backend/app/crop_supply_morphology_repeat_point.py',
 'backend/app/crop_supply_morphology_repeat_point_books.py',
 'backend/app/crop_supply_morphology_repeat_point_core.py',
 'backend/app/crop_supply_morphology_repeat_proofs.py',
 'backend/app/crop_supply_morphology_repeat_resume.py',
 'backend/app/crop_supply_morphology_resume.py',
 'backend/app/crop_supply_morphology_rhs.py',
 'backend/app/crop_supply_morphology_stage.py',
 'backend/app/crop_supply_morphology_successor_books.py',
 'backend/app/crop_supply_morphology_successor_context.py',
 'backend/app/crop_supply_morphology_successor_context_proofs.py',
 'backend/app/crop_supply_morphology_successor_resume.py',
 'backend/app/crop_supply_season.py',
 'backend/app/crop_supply_threshold_state_books.py',
 'backend/app/job_store.py',
 'backend/app/thermal_run_store.py',
 'research/export-leaf-funded-birth-replay.py',
 'research/export-material-replay.py',
] as const;
const FLAGS={scope:'software_research_only',G0_G4:'not_assessed',R2:'not_approved',
 time_kind:'synthetic_model_clock_not_observation',claim_scope:'stored_synthetic_repeat_material_window_only'} as const;
export type RepeatRef={sha256:string;bytes:number};
export type RepeatExact={numerator:string;denominator:string;unit:string};
export type RepeatAt={time_origin_utc:string;elapsed_seconds_exact:RepeatExact};
export type RepeatPhase='material_before'|'material_after'|'original_grid_endpoint'|'forcing_before'|'forcing_after'|'declared_end';
type Group=typeof GROUPS[number];
type Raw3={cursor:RepeatRef;current:RepeatRef;basis:RepeatRef};
type Selection={definition:RepeatRef;cursor:RepeatRef};
type Source={owner_version:'supply-material-repeat-owner-research-v1';definition:RepeatRef;anchor:Raw3;final:Raw3;
 original_root:RepeatRef;original_frame_index:number;base:Selection;forcing:Selection;material:Selection};
type PointEvidence={witness:RepeatRef;receipt:RepeatRef;calculation_sha256:string;candidate_calculation_sha256:string;
 before_frame:RepeatRef;after_frame:RepeatRef};
type TransitionFields={index:number;previous_cursor_sha256:string;cursor:RepeatRef;history_page:RepeatRef;
 before_current:RepeatRef;after_current:RepeatRef;before_basis:RepeatRef;after_basis:RepeatRef;frame_indices:number[]};
export type RepeatTransition=(TransitionFields&{kind:'interval'|'forcing_switch'})|
 (TransitionFields&{kind:'material_adoption';point:PointEvidence});
export type RepeatFrameDescriptor={index:number;transition_index:number;phase:RepeatPhase;at:RepeatAt;
 active_basis_sha256:string;frame:RepeatRef;state_scalars:number};
export type RepeatManifest={schema_version:'supply-material-repeat-artifact-v1'}&typeof FLAGS&{
 code_sha256:Record<string,string>;source:Source;blob_groups:Record<Group,RepeatRef[]>;
 transitions:RepeatTransition[];frames:RepeatFrameDescriptor[];effective_rights:{use:true;display:true;redistribute:boolean};
 window:{first_at:RepeatAt;last_at:RepeatAt;covers_whole_season:false;selection:'committed_repeat_material_and_confirmed_remainder'};
 terminal:{status:'completed'|'confirmed_prefix';hold:null;scope:'declared_synthetic_forcing_plan_only'};notice:RepeatRef;
};
export type RepeatManifestExpectation={rootSha256:string;codeSha256:Record<string,string>};

function check(value:unknown,message:string):asserts value {
 if(!value)throw Error('Stored repeat artifact: '+message);
}
type JsonNode={kind:'object';fields:Record<string,JsonNode>}|{kind:'array';items:JsonNode[]}|{kind:'string';value:string}|
 {kind:'number';lexeme:string}|{kind:'boolean';value:boolean}|{kind:'null'};
function unicodeOrder(a:string,b:string):number {
 const x=[...a],y=[...b];
 for(let i=0;i<Math.min(x.length,y.length);i++){
  const d=x[i]!.codePointAt(0)!-y[i]!.codePointAt(0)!;if(d)return d;
 }
 return x.length-y.length;
}
// Numeric tokens remain raw lexemes until the corresponding typed field validates them.
function parseCanonical(text:string):JsonNode {
 let offset=0;
 function string():string {
  const start=offset;check(text[offset++]==='"','JSON string required');
  while(offset<text.length){
   const char=text[offset++];
   if(char==='\\'){offset++;continue;}
   if(char==='"'){
    const raw=text.slice(start,offset);let value:unknown;
    try{value=JSON.parse(raw);}catch{throw Error('Stored repeat artifact: invalid JSON string');}
    check(typeof value==='string','JSON string required');
    for(let i=0;i<value.length;i++){
     const c=value.charCodeAt(i);
     if(c>=0xd800&&c<=0xdbff){const next=value.charCodeAt(++i);check(next>=0xdc00&&next<=0xdfff,'unpaired surrogate');}
     else check(c<0xdc00||c>0xdfff,'unpaired surrogate');
    }
    check(JSON.stringify(value)===raw,'canonical UTF-8 string required');return value;
   }
  }
  throw Error('Stored repeat artifact: incomplete JSON string');
 }
 function value(depth:number):JsonNode {
  check(depth<=64,'invalid JSON nesting');const char=text[offset];
  if(char==='"')return {kind:'string',value:string()};
  if(char==='{'||char==='['){
   offset++;const object=char==='{',end=object?'}':']';
   const fields=Object.create(null) as Record<string,JsonNode>,items:JsonNode[]=[];let previous:string|undefined;
   if(text[offset]===end){offset++;return object?{kind:'object',fields}:{kind:'array',items};}
   while(offset<text.length){
    if(object){
     const key=string();check(!Object.hasOwn(fields,key),'duplicate JSON key');
     check(previous===undefined||unicodeOrder(previous,key)<0,'canonical object key order required');previous=key;
     check(text[offset++]===':','JSON colon required');fields[key]=value(depth+1);
    }else items.push(value(depth+1));
    if(text[offset]===end){offset++;return object?{kind:'object',fields}:{kind:'array',items};}
    check(text[offset++]===',','JSON comma required');
   }
   throw Error('Stored repeat artifact: incomplete JSON container');
  }
  for(const literal of ['true','false','null'] as const){
   if(text.startsWith(literal,offset)){offset+=literal.length;return literal==='null'?{kind:'null'}:{kind:'boolean',value:literal==='true'};}
  }
  const number=/^-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?/.exec(text.slice(offset));
  check(number,'JSON value required');offset+=number[0].length;return {kind:'number',lexeme:number[0]};
 }
 const root=value(0);check(offset===text.length,'canonical complete JSON bytes required');return root;
}
function fields(node:JsonNode|undefined,keys:readonly string[]):Record<string,JsonNode> {
 check(node?.kind==='object','object required');
 check(Object.keys(node.fields).length===keys.length&&keys.every(key=>Object.hasOwn(node.fields,key)),'closed object required');
 return node.fields;
}
function string(node:JsonNode|undefined):string {check(node?.kind==='string','string required');return node.value;}
function literal<T extends string>(node:JsonNode|undefined,wanted:T):T {
 check(string(node)===wanted,'unsupported tag');return wanted;
}
function oneOf<const T extends readonly string[]>(node:JsonNode|undefined,choices:T):T[number] {
 const value=string(node);check(choices.includes(value),'unsupported enum');return value as T[number];
}
function bool(node:JsonNode|undefined):boolean {check(node?.kind==='boolean','boolean required');return node.value;}
function integer(node:JsonNode|undefined,min:number,max:number):number {
 check(node?.kind==='number'&&/^(?:0|[1-9]\d*)$/.test(node.lexeme),'strict nonnegative integer required');
 const value=Number(node.lexeme);check(Number.isSafeInteger(value)&&value>=min&&value<=max,'integer outside bound');return value;
}
function list(node:JsonNode|undefined,min:number,max:number):JsonNode[] {
 check(node?.kind==='array'&&node.items.length>=min&&node.items.length<=max,'array outside bound');return node.items;
}
function digest(value:string):string {check(/^[a-f0-9]{64}$/.test(value),'SHA256 required');return value;}
function ref(node:JsonNode|undefined,max=MAX_DOCUMENT):RepeatRef {
 const row=fields(node,['sha256','bytes']);return {sha256:digest(string(row.sha256)),bytes:integer(row.bytes,1,max)};
}
function raw3(node:JsonNode|undefined):Raw3 {
 const row=fields(node,['cursor','current','basis']);return {cursor:ref(row.cursor),current:ref(row.current),basis:ref(row.basis)};
}
function selection(node:JsonNode|undefined):Selection {
 const row=fields(node,['definition','cursor']);return {definition:ref(row.definition),cursor:ref(row.cursor)};
}
function exact(node:JsonNode|undefined,unit:string):RepeatExact {
 const row=fields(node,['numerator','denominator','unit']);
 const result={numerator:string(row.numerator),denominator:string(row.denominator),unit:literal(row.unit,unit)};
 fraction(result,unit);return result;
}
function at(node:JsonNode|undefined):RepeatAt {
 const row=fields(node,['time_origin_utc','elapsed_seconds_exact']);const origin=string(row.time_origin_utc);utc(origin);
 check(origin.slice(0,4)!=='0000','original UTC year range required');
 const elapsed=exact(row.elapsed_seconds_exact,'s');check(fraction(elapsed,'s').n>=0n,'negative elapsed time');
 return {time_origin_utc:origin,elapsed_seconds_exact:elapsed};
}
function equalRef(a:RepeatRef,b:RepeatRef):boolean{return a.sha256===b.sha256&&a.bytes===b.bytes;}
function timeOrder(a:RepeatAt,b:RepeatAt):number {
 check(a.time_origin_utc===b.time_origin_utc,'one original UTC origin required');
 return compare(fraction(a.elapsed_seconds_exact,'s'),fraction(b.elapsed_seconds_exact,'s'));
}
function codePins(expected:RepeatManifestExpectation):{root:string;code:Record<string,string>} {
 check(expected!==null&&typeof expected==='object'&&!Array.isArray(expected),'caller pins required');
 check(Object.keys(expected).length===2&&Object.hasOwn(expected,'rootSha256')&&Object.hasOwn(expected,'codeSha256'),'closed caller pins required');
 check(typeof expected.rootSha256==='string','caller root SHA required');const root=digest(expected.rootSha256),code=expected.codeSha256;
 check(code!==null&&typeof code==='object'&&!Array.isArray(code),'caller code map required');
 check(Object.keys(code).length===CODE_PATHS.length&&CODE_PATHS.every(key=>Object.hasOwn(code,key)),'fixed component map required');
 const copy:Record<string,string>={};for(const key of CODE_PATHS){check(typeof code[key]==='string','code digest required');copy[key]=digest(code[key]!);}
 return {root,code:copy};
}
function source(node:JsonNode|undefined):Source {
 const row=fields(node,['owner_version','definition','anchor','final','original_root','original_frame_index','base','forcing','material']);
 return {owner_version:literal(row.owner_version,'supply-material-repeat-owner-research-v1'),definition:ref(row.definition),anchor:raw3(row.anchor),final:raw3(row.final),
  original_root:ref(row.original_root),original_frame_index:integer(row.original_frame_index,0,511),base:selection(row.base),forcing:selection(row.forcing),material:selection(row.material)};
}
function descriptor(node:JsonNode):RepeatFrameDescriptor {
 const row=fields(node,['index','transition_index','phase','at','active_basis_sha256','frame','state_scalars']);
 return {index:integer(row.index,0,511),transition_index:integer(row.transition_index,0,255),
  phase:oneOf(row.phase,['material_before','material_after','original_grid_endpoint','forcing_before','forcing_after','declared_end']),at:at(row.at),
  active_basis_sha256:digest(string(row.active_basis_sha256)),frame:ref(row.frame),state_scalars:integer(row.state_scalars,1,32768)};
}
function transition(node:JsonNode):RepeatTransition {
 check(node.kind==='object','transition object required');
 const kind=oneOf(node.fields.kind,['interval','forcing_switch','material_adoption']);
 const row=fields(node,['index','kind','previous_cursor_sha256','cursor','history_page','before_current','after_current','before_basis','after_basis','frame_indices',...(kind==='material_adoption'?['point']:[])]);
 const common:TransitionFields={index:integer(row.index,0,255),previous_cursor_sha256:digest(string(row.previous_cursor_sha256)),cursor:ref(row.cursor),history_page:ref(row.history_page),
  before_current:ref(row.before_current),after_current:ref(row.after_current),before_basis:ref(row.before_basis),after_basis:ref(row.after_basis),
  frame_indices:list(row.frame_indices,kind==='material_adoption'?2:1,kind==='material_adoption'?2:1).map(item=>integer(item,0,511))};
 if(kind!=='material_adoption')return {...common,kind};
 const p=fields(row.point,['witness','receipt','calculation_sha256','candidate_calculation_sha256','before_frame','after_frame']);
 const point={witness:ref(p.witness),receipt:ref(p.receipt),calculation_sha256:digest(string(p.calculation_sha256)),
  candidate_calculation_sha256:digest(string(p.candidate_calculation_sha256)),before_frame:ref(p.before_frame),after_frame:ref(p.after_frame)};
 check(new Set([point.witness.sha256,point.receipt.sha256,point.calculation_sha256,point.candidate_calculation_sha256]).size===4,'distinct point identities required');
 return {...common,kind,point};
}
function validate(node:JsonNode,pins:{root:string;code:Record<string,string>},rawBytes:number):RepeatManifest {
 const row=fields(node,['schema_version',...Object.keys(FLAGS),'code_sha256','source','blob_groups','transitions','frames','effective_rights','window','terminal','notice']);
 literal(row.schema_version,'supply-material-repeat-artifact-v1');for(const [key,value]of Object.entries(FLAGS))literal(row[key],value);
 const codes=fields(row.code_sha256,CODE_PATHS),code:Record<string,string>={};
 for(const path of CODE_PATHS){code[path]=digest(string(codes[path]));check(code[path]===pins.code[path],'caller code pin differs');}
 const src=source(row.source),groupNodes=fields(row.blob_groups,GROUPS),physical=new Map<string,number>();
 const groups={} as Record<Group,RepeatRef[]>;
 for(const kind of GROUPS){
  const entries=list(groupNodes[kind],1,MAX_FILES).map(item=>ref(item,kind==='original'?16777216:MAX_DOCUMENT));
  let previous='';for(const entry of entries){
   check(entry.sha256>previous,'unique digest-sorted group required');previous=entry.sha256;
   check(entry.sha256!==pins.root,'manifest cannot reference itself');
   const known=physical.get(entry.sha256);check(known===undefined||known===entry.bytes,'one digest has unequal lengths');physical.set(entry.sha256,entry.bytes);
  }
  groups[kind]=entries;
 }
 check(physical.size+1<=MAX_FILES,'physical file bound exceeded');
 check([...physical.values()].reduce((sum,n)=>sum+n,rawBytes)<=MAX_PHYSICAL_BYTES,'physical byte bound exceeded');
 function member(kind:Group,value:RepeatRef){check(groups[kind].some(entry=>equalRef(entry,value)),'selected descriptor missing from '+kind);}
 member('repeat',src.definition);for(const value of [...Object.values(src.anchor),...Object.values(src.final)])member('repeat',value);
 member('original',src.original_root);const notice=ref(row.notice);member('original',notice);
 for(const kind of ['base','forcing','material'] as const){member(kind,src[kind].definition);member(kind,src[kind].cursor);}
 const transitions=list(row.transitions,1,256).map(transition),frames=list(row.frames,2,512).map(descriptor);
 check(frames.reduce((sum,frame)=>sum+frame.state_scalars,0)<=32768,'sampled scalar bound exceeded');
 const frameDigests=new Set<string>();for(const [index,frame]of frames.entries()){
  check(frame.index===index,'frame order differs');check(frame.phase!=='declared_end'||index===frames.length-1,'declared end must be final');member('frames',frame.frame);
  check(!frameDigests.has(frame.frame.sha256),'projected frame duplicated');frameDigests.add(frame.frame.sha256);
  if(index)check(timeOrder(frames[index-1]!.at,frame.at)<=0,'frame time order differs');
 }
 check(frameDigests.size===groups.frames.length,'projected frame group differs');
 let prior=src.anchor,frameIndex=0,adoptions=0;
 const cursors=new Set([src.anchor.cursor.sha256]),pages=new Set<string>(),receipts=new Set<string>();
 for(const [index,t]of transitions.entries()){
  check(t.index===index&&t.previous_cursor_sha256===prior.cursor.sha256&&equalRef(t.before_current,prior.current)&&equalRef(t.before_basis,prior.basis),'transition before-chain differs');
  check(!cursors.has(t.cursor.sha256)&&!pages.has(t.history_page.sha256),'acyclic transition order required');cursors.add(t.cursor.sha256);pages.add(t.history_page.sha256);
  for(const value of [t.cursor,t.history_page,t.before_current,t.after_current,t.before_basis,t.after_basis])member('repeat',value);
  for(const position of t.frame_indices){check(position===frameIndex++,'transition frame coverage differs');check(frames[position]?.transition_index===index,'frame transition differs');}
  const first=frames[t.frame_indices[0]!]!;check(first!==undefined,'transition frame missing');
  if(t.kind==='material_adoption'){
   const last=frames[t.frame_indices[1]!]!;check(last!==undefined,'material-after frame missing');adoptions++;
   check(first.phase==='material_before'&&last.phase==='material_after'&&timeOrder(first.at,last.at)===0,'same-time material pair required');
   check(first.active_basis_sha256===t.before_basis.sha256&&last.active_basis_sha256===t.after_basis.sha256,'material basis differs');
   member('repeat',t.point.witness);member('repeat',t.point.before_frame);member('repeat',t.point.after_frame);member('points',t.point.receipt);
   check(!receipts.has(t.point.receipt.sha256),'public point duplicated');receipts.add(t.point.receipt.sha256);
  }else{
   check(equalRef(t.before_basis,t.after_basis)&&first.active_basis_sha256===t.after_basis.sha256,'confirmed basis differs');
   if(t.kind==='interval')check(['original_grid_endpoint','forcing_before','declared_end'].includes(first.phase),'interval phase differs');
   else{
    check(first.phase==='forcing_after','forcing-after phase required');const before=frames[first.index-1];
    if(before){check(before.phase==='forcing_before','adjacent forcing pair required');
     check(timeOrder(before.at,first.at)===0&&before.active_basis_sha256===first.active_basis_sha256,'forcing At or basis differs');}
    // A source-only anchor emits no frame; its unreceived phase remains server-certified.
   }
  }
  prior={cursor:t.cursor,current:t.after_current,basis:t.after_basis};
 }
 check(adoptions>0&&receipts.size===groups.points.length,'complete committed material points required');
 check(frameIndex===frames.length&&equalRef(prior.cursor,src.final.cursor)&&equalRef(prior.current,src.final.current)&&equalRef(prior.basis,src.final.basis),'final source or frame coverage differs');
 const rights=fields(row.effective_rights,['use','display','redistribute']);check(bool(rights.use)&&bool(rights.display),'use and display rights required');const redistribute=bool(rights.redistribute);
 const w=fields(row.window,['first_at','last_at','covers_whole_season','selection']);check(bool(w.covers_whole_season)===false,'whole-season claim unsupported');
 const firstAt=at(w.first_at),lastAt=at(w.last_at);check(timeOrder(firstAt,frames[0]!.at)===0&&timeOrder(lastAt,frames.at(-1)!.at)===0,'window differs');
 const terminal=fields(row.terminal,['status','hold','scope']),status=oneOf(terminal.status,['completed','confirmed_prefix']);
 check(terminal.hold?.kind==='null','terminal hold must be null');
 check((status==='completed')===(frames.at(-1)!.phase==='declared_end'),'terminal completion differs');
 return {schema_version:'supply-material-repeat-artifact-v1',...FLAGS,code_sha256:code,source:src,blob_groups:groups,transitions,frames,
  effective_rights:{use:true,display:true,redistribute},window:{first_at:firstAt,last_at:lastAt,covers_whole_season:false,selection:literal(w.selection,'committed_repeat_material_and_confirmed_remainder')},
  terminal:{status,hold:null,scope:literal(terminal.scope,'declared_synthetic_forcing_plan_only')},notice};
}
export async function decodeRepeatManifest(raw:Uint8Array,expected:RepeatManifestExpectation):Promise<RepeatManifest> {
 check(raw instanceof Uint8Array&&raw.byteLength>0&&raw.byteLength<=MAX_DOCUMENT,'bounded manifest bytes required');
 const snapshot=new Uint8Array(raw),pins=codePins(expected);
 check(await sha256(snapshot)===pins.root,'caller root SHA differs');
 let text:string;try{text=new TextDecoder('utf-8',{fatal:true,ignoreBOM:true}).decode(snapshot);}catch{throw Error('Stored repeat artifact: valid UTF-8 required');}
 return validate(parseCanonical(text),pins,snapshot.byteLength);
}
