import {closed,digest,need,object} from './storedLeafReplayIO';
import {equal} from './leafFundedBirthReplaySchema';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {add,binary64,compare,counter,document,exactAt,fraction,list,mul,sub,without,type WireDocument,type Row,type Fraction} from './supplyMorphologyGraphValues';
import {SUPPLY_MATERIAL_FIXTURE as F} from './supplyMaterialFixture';
import {storedCombine} from './supplyMaterialValues';
import {floatStateWire,storedFrameQuantities} from './supplyMorphologyStoredQuantities';
import {quantityLayout} from './supplyMorphologyQuantityLayout';
import {accountUnits,checkpointQuantities,exactBlock} from './supplyMorphologyQuantityAccounts';
import {exactRecord} from './supplyMorphologyQuantityCore';
import {materialStoredSchema} from './supplyMaterialSchemas';

export type Group='original'|'base'|'forcing'|'material';
export type GetRecord=(sha:unknown,group:Group)=>WireDocument;
export type Link={sha:string;cursor:WireDocument;current:WireDocument;page?:WireDocument};
export type Chain={links:Link[];basis:WireDocument};
export const FLAGS={scope:'software_research_only',G0_G4:'not_assessed',R2:'not_approved',time_kind:'synthetic_model_clock_not_observation',claim_scope:'stored_synthetic_material_window_only'} as const;
const paths:Readonly<Record<string,string>>=F.code_sha256;
const modelCode=(group:Exclude<Group,'original'>)=>paths[`backend/app/${group==='base'?'crop_supply_season':group==='forcing'?'crop_supply_forcing_owner':'crop_supply_material_owner'}.py`];
export function materialFlags(value:Row,schema:string){need(value.schema_version===schema);for(const [k,v]of Object.entries(FLAGS))need(value[k]===v);}
export function numericFlags(value:Row){for(const k of ['scope','G0_G4','R2'])need(value[k]===FLAGS[k as keyof typeof FLAGS]);}
export function materialPins(value:unknown){const q=closed(value,Object.keys(paths));for(const [k,v]of Object.entries(paths))need(q[k]===v);}
export function publicMaterialRights(value:unknown){const q=closed(value,['use','display','redistribute']);need(Object.values(q).every(v=>v===true));return {use:true,display:true,redistribute:true};}
const numerical=(doc:WireDocument,group:Exclude<Group,'original'>)=>{
 const n=group==='base'?doc:document(doc.fields.numeric!);materialStoredSchema(n);numericFlags(n.value);
 counter(n,'branch_steps');counter(n,'event_sequence');counter(n,'grid_index');same(n.value.at,object(n.value.last_confirmed).at);return n;
};

export function archiveChain(get:GetRecord,group:Exclude<Group,'original'>,selector:unknown):Chain{
 const selected=closed(selector,['definition_sha256','cursor_sha256']);digest(selected.definition_sha256);digest(selected.cursor_sha256);
 const prefix={base:'supply-season',forcing:'supply-forcing-owner',material:'supply-material'}[group];
 let hash=selected.cursor_sha256,basisSHA:string|undefined;const seen=new Set<string>(),links:Link[]=[];
 while(true){
  need(!seen.has(hash)&&seen.size<256);seen.add(hash);
  const cursor=get(hash,group),c=closed(cursor.value,['schema_version','scope','G0_G4','R2','code_sha256','definition_sha256','basis_sha256','current_sha256','previous_cursor_sha256','history_page_sha256']);
  numericFlags(c);need(c.schema_version===prefix+'-cursor-v1'&&c.code_sha256===modelCode(group)&&c.definition_sha256===selected.definition_sha256);
  digest(c.basis_sha256);digest(c.current_sha256);basisSHA??=c.basis_sha256;need(c.basis_sha256===basisSHA);
  const current=get(c.current_sha256,group);numericFlags(current.value);need(current.value.schema_version===prefix+'-current-v1');
  if(group!=='base')need(current.value.definition_sha256===selected.definition_sha256&&current.value.code_sha256===modelCode(group));
  const page=c.history_page_sha256===null?undefined:get(c.history_page_sha256,group);
  if(c.previous_cursor_sha256!==null){
   digest(c.previous_cursor_sha256);need(page);const parent=get(c.previous_cursor_sha256,group);
   need(page.value.previous_cursor_sha256===c.previous_cursor_sha256&&page.value.before_current_sha256===parent.value.current_sha256&&page.value.after_current_sha256===c.current_sha256);
  }else if(group==='material')need(page?.value.kind==='material_adoption'&&page.value.after_current_sha256===c.current_sha256);
  else need(!page);
  links.push({sha:hash,cursor,current,page});
  if(c.previous_cursor_sha256===null)break;hash=c.previous_cursor_sha256;
 }
 need(basisSHA);return {links:links.reverse(),basis:get(basisSHA,group)};
}

function same(value:unknown,expected:unknown){equal(value,expected);}
function frac(value:unknown,unit:string){return fraction(value,unit);}
function eq(a:Fraction,b:Fraction){need(compare(a,b)===0);}
function currentTransfers(doc:WireDocument){return document(doc.fields.branch_integrated_transfers!);}
function floats(raw:string){return floatStateWire(raw);}

export function storedChainProof(chain:Chain,group:Exclude<Group,'original'>){
 const basis=group==='base'?chain.basis:document(chain.basis.fields[group==='forcing'?'arithmetic_basis':'numeric_basis']!);
 for(let i=1;i<chain.links.length;i++){
  const before=chain.links[i-1]!,after=chain.links[i]!,a=numerical(before.current,group),b=numerical(after.current,group),page=after.page!;
  need(after.cursor.value.previous_cursor_sha256===before.sha);
  if(page.value.kind==='forcing_switch'){
   need(group!=='base');for(const k of ['at','branch_steps','schedule','event_sequence','branch_integrated_transfers','lifetime_transfers_exact','point_totals_exact','branch_ledgers','global_ledgers','transfer_origins'])same(b.value[k],a.value[k]);
   need(wireFields(a.fields.last_confirmed!).state===wireFields(b.fields.last_confirmed!).state);continue;
  }
  need(page.value.kind===(group==='base'?'step':'interval'));
  const evidence=group==='base'?page.fields.interval!:group==='forcing'?wireFields(page.fields.evidence!).interval!:page.fields.evidence!;
  const trace=document(evidence),t=closed(trace.value,['left_elapsed_seconds_exact','right_elapsed_seconds_exact','step_seconds_exact','stages','endpoint','flux_order','shoot_clock_certificate']);
  const left=exactAt(a.value.at),right=exactAt(b.value.at),dt=sub(right.elapsed,left.elapsed);need(left.origin===right.origin&&dt.n>0n);
  eq(frac(t.left_elapsed_seconds_exact,'s'),left.elapsed);eq(frac(t.right_elapsed_seconds_exact,'s'),right.elapsed);eq(frac(t.step_seconds_exact,'s'),dt);
  const y=floats(wireFields(a.fields.last_confirmed!).state!),end=floats(wireFields(b.fields.last_confirmed!).state!);
  const rows=wireItems(trace.fields.stages!).map(document);need(rows.length===4);
  const order=list(t.flux_order,2048).map(v=>closed(v,['name','unit'])),names=order.map(v=>String(v.name));need(new Set(names).size===names.length);
  const av=closed(a.value.branch_integrated_transfers,names),bv=closed(b.value.branch_integrated_transfers,names);
  const rates:number[][]=[],flows:number[][]=[];
  for(let j=0;j<4;j++){
   const row=rows[j]!,v=closed(row.value,['stage','at_elapsed_seconds_exact','state','rates','flux']),offset=j===0?{n:0n,d:1n}:j===3?dt:mul(dt,{n:1n,d:2n});
   need(v.stage===['k1','k2','k3','k4'][j]);eq(frac(v.at_elapsed_seconds_exact,'s'),add(left.elapsed,offset));
   const state=floats(row.fields.state!);if(j===0)need(row.fields.state===wireFields(a.fields.last_confirmed!).state);else storedCombine(y,[rates[j-1]!],[{n:1n,d:1n}],offset,state);
   const r=floats(row.fields.rates!),flow=floats(row.fields.flux!);need(r.length===y.length&&flow.length===names.length);rates.push(r);flows.push(flow);
  }
  const weights=[{n:1n,d:6n},{n:1n,d:3n},{n:1n,d:3n},{n:1n,d:6n}];storedCombine(y,rates,weights,dt,end);
  const endpoint=document(trace.fields.endpoint!);need(endpoint.fields.state===wireFields(b.fields.last_confirmed!).state);need(floats(endpoint.fields.rates!).length===y.length&&floats(endpoint.fields.flux!).length===names.length);
  const ta=currentTransfers(a),tb=currentTransfers(b);
  const values=(doc:WireDocument)=>names.map((name,k)=>{const v=closed(doc.value[name],['value','unit']);need(v.unit===order[k]!.unit);return floats('['+wireFields(doc.fields[name]!).value!+']')[0]!;});
  const initial=values(ta),final=values(tb);storedCombine(initial,flows,weights,dt,final);
  const lifeA=closed(a.value.lifetime_transfers_exact,names),lifeB=closed(b.value.lifetime_transfers_exact,names);
  for(let j=0;j<names.length;j++){const name=names[j]!,unit=String(order[j]!.unit);eq(frac(lifeB[name],unit),add(frac(lifeA[name],unit),sub(binary64(final[j]),binary64(initial[j]))));need(object(av[name]).unit===unit&&object(bv[name]).unit===unit);}
  const air=names.indexOf('indoor_air_temperature_time');need(air>=0);
  const age=add(frac(object(a.value.schedule).age_exact,'degC_day'),mul(sub(sub(binary64(final[air]),binary64(initial[air])),mul(binary64(basis.value.shoot_base_temperature),dt)),{n:1n,d:86400n}));
  same(b.value.schedule,{...object(a.value.schedule),age_exact:exactRecord(age,'degC_day')});
  need(counter(b,'branch_steps')===counter(a,'branch_steps')+1);same(b.value.point_totals_exact,a.value.point_totals_exact);same(b.value.transfer_origins,a.value.transfer_origins);
 }
}

export async function materialSourceGraph(root:WireDocument,get:GetRecord,original:WireDocument,signal:AbortSignal){
 const r=root.value,source=closed(r.source,['original_root','source_frame_index','base','forcing','material']);
 const bd=get(object(source.base).definition_sha256,'base'),fd=get(object(source.forcing).definition_sha256,'forcing'),md=get(object(source.material).definition_sha256,'material');
 for(const [group,d]of [['base',bd],['forcing',fd],['material',md]] as const){numericFlags(d.value);need(d.value.code_sha256===modelCode(group));publicMaterialRights(d.value.rights??object(d.value.inputs).rights);}
 need(bd.value.schema_version==='supply-season-definition-v1'&&fd.value.schema_version==='supply-forcing-definition-v1'&&md.value.schema_version==='supply-material-definition-v1');
 const base=archiveChain(get,'base',source.base),forcing=archiveChain(get,'forcing',source.forcing),material=archiveChain(get,'material',source.material);
 const index=counter(document(root.fields.source!),'source_frame_index',0,511),originalFrames=list(original.value.frames);need(index<originalFrames.length);
 same(bd.value.source,{artifact_sha256:object(source.original_root).sha256,frame_index:index});same(fd.value.source,source.base);same(md.value.source,source.forcing);
 const oldContext=get(object(originalFrames[index]).context_sha256,'original');
 need(base.basis.fields.seed===wireFields(oldContext.fields.descriptor!).seed&&base.basis.value.source_checkpoint_sha256===object(originalFrames[index]).checkpoint_sha256);
 const baseLast=base.links.at(-1)!,forceLast=forcing.links.at(-1)!;
 same(forcing.basis.value.source,source.base);need(forcing.basis.value.source_current_sha256===await wireHash(baseLast.current.raw)&&forcing.basis.fields.arithmetic_basis===base.basis.raw);
 const point=get(md.value.point_sha256,'material'),pv=point.value,inputs=object(md.value.inputs),pending=get(md.value.pending_page_sha256,'forcing');
 need(md.value.proof_code_sha256===paths['backend/app/crop_supply_material_proof.py']&&pv.code_sha256===paths['backend/app/crop_supply_material_point.py']);
 need(pv.status==='point_ready'&&pv.calculation_sha256===md.value.expected_point_sha256&&pv.calculation_sha256===await wireHash(without(point.raw,'calculation_sha256')));
 need(point.fields.inputs===md.fields.inputs&&pv.input_sha256===await wireHash(point.fields.inputs!)&&pv.source_current_sha256===await wireHash(forceLast.current.raw));
 need(pv.cursor_sha256===object(source.forcing).cursor_sha256&&pv.definition_sha256===object(source.forcing).definition_sha256&&pv.pending_page_sha256===md.value.pending_page_sha256);
 need(pending.value.previous_cursor_sha256===object(source.forcing).cursor_sha256&&pending.value.definition_sha256===object(source.forcing).definition_sha256);
 need(object(pending.value.result).status==='awaiting_material'&&object(pending.value.result).current===null);
 publicMaterialRights(inputs.rights);publicMaterialRights(bd.value.rights);publicMaterialRights(fd.value.rights);
 const spans=list(fd.value.spans,128);need(spans.length>=1);for(const span of spans)publicMaterialRights(object(span).rights);
 publicMaterialRights(pv.effective_rights);publicMaterialRights(r.effective_rights);need(original.value.redistribution_authorized===true);
 const newBasis=document(material.basis.fields.numeric_basis!),seed=document(newBasis.fields.seed!),sv=seed.value;
 same(material.basis.value.source,source.forcing);need(material.basis.value.point_sha256===md.value.point_sha256&&material.basis.value.source_current_sha256===await wireHash(forceLast.current.raw));
 const mapping={program:'after_program',organs:'after_organs',costs:'after_costs',state_layout:'after_state_layout',birth_bases:'after_birth_baselines',geometry_baselines:'after_geometry_baselines',
  global_ledgers:'post_point_global_ledgers_preview',lifetime_transfers_exact:'post_point_lifetime_transfers_exact_preview',point_totals_exact:'post_point_point_totals_exact_preview'};
 for(const [key,value]of Object.entries(mapping))need(seed.fields[key]===point.fields[value]);
 const origins=closed(material.basis.value.origin_records,['physical','geometry']),sourceN=object(forceLast.current.value.numeric);
 for(const [kind,value]of Object.entries(origins)){const origin=get(object(sv.transfer_origins)[kind],'material');same(origin.value,value);need(origin.value.point_sha256===md.value.point_sha256&&origin.value.previous_origin_sha256===object(sourceN.transfer_origins)[kind]);}
 const event=object(pv.source_event),schedule=object(sv.schedule),dense=document(point.fields.before_dense!);
 const seq=counter(document(point.fields.source_event!),'sequence',1),sd=document(seed.fields.schedule!);
 need(schedule.consumed_event_id===event.source_event_id&&counter(sd,'consumed_sequence',1)===seq&&counter(sd,'next_sequence',1)===seq+1);
 same(schedule.age_exact,dense.value.shoot_age_exact);need(counter(seed,'event_sequence')===counter(document(forceLast.current.fields.numeric!),'event_sequence')+1);
 same(pv.at,dense.value.at);same(object(sv.initial_sample).at,pv.at);
 for(const [chain,kind]of [[base,'base'],[forcing,'forcing'],[material,'material']] as const){signal.throwIfAborted();storedChainProof(chain,kind);}
 return {base,forcing,material,bd,fd,md,point,seed,newBasis,dense};
}

export type MaterialSources=Awaited<ReturnType<typeof materialSourceGraph>>;
export function materialFrameValue(frame:WireDocument,index:number,g:MaterialSources,root:WireDocument){
 const f=frame.value;materialFlags(f,'supply-material-replay-frame-v1');need(counter(frame,'index',0,511)===index);
 const n=index===0?g.dense:document(g.material.links[index-1]!.current.fields.numeric!);
 const seed=index===0?document(document(g.forcing.basis.fields.arithmetic_basis!).fields.seed!):g.seed;
 const lifetime=n.value[index===0?'pending_lifetime_transfers_exact':'lifetime_transfers_exact'];
 const geometry=index===0?root.value.before_geometry_diagnostics:n.value.geometry_diagnostics;
 const accounts=n.value[index===0?'pending_global_ledgers':'global_ledgers'];
 const snapshotRaw=index===0?'{"at":'+n.fields.at+',"derived":'+n.fields.derived+',"state":'+n.fields.state+'}':n.fields.last_confirmed!;
 need(frame.fields.snapshot===snapshotRaw);floats(wireFields(snapshotRaw).state!);
 const layout=quantityLayout(seed.value),units=accountUnits(layout);exactBlock(lifetime,units.flow);
 if(index!==0){
  materialStoredSchema(n);numericFlags(n.value);need(n.value.schema_version==='supply-material-numeric-v1'&&n.value.code_sha256===modelCode('material'));
  checkpointQuantities(layout,n.value,g.newBasis.value.shoot_base_temperature);
  const link=g.material.links[index-1]!,cur=link.current.value;publicMaterialRights(cur.effective_rights);
  same(cur.effective_rights,root.value.effective_rights);same(cur.at,n.value.at);same(cur.at,object(n.value.last_confirmed).at);
  need(cur.phase===n.value.phase||cur.phase==='declared_end'&&n.value.phase==='original_grid_endpoint');
  counter(link.current,'integration_count');counter(link.current,'output_cursor',1);digest(cur.output_prefix_sha256);counter(n,'event_sequence');counter(n,'branch_steps');
  if(index===1)need(n.fields.last_confirmed===seed.fields.initial_sample);
  const at=exactAt(cur.at),spanIndex=counter(link.current,'span_index',0,127),spans=list(g.fd.value.spans,128);need(spanIndex<spans.length);
  const span=object(object(spans[spanIndex]).span),begin=frac(span.start,'s'),end=frac(span.end,'s'),stop=frac(g.fd.value.stop_at,'s'),grid=binary64(object(seed.value.original_numerical).step_seconds);
  const phase=cur.phase,gridIndex=counter(n,'grid_index',0);need(grid.n>0n);
  const modulo=sub(at.elapsed,mul(grid,{n:BigInt(gridIndex),d:1n}));need(modulo.n>=0n&&compare(modulo,grid)<0);
  eq(frac(n.value.grid_remainder_exact,'s'),modulo);eq(frac(n.value.next_grid_endpoint_exact,'s'),mul(grid,{n:BigInt(gridIndex+1),d:1n}));
  need(compare(at.elapsed,begin)>=0&&compare(at.elapsed,end)<=0&&(
   phase==='material_after'&&compare(at.elapsed,exactAt(object(seed.value.initial_sample).at).elapsed)===0||
   phase==='forcing_after'&&compare(at.elapsed,begin)===0||phase==='forcing_before'&&spanIndex<spans.length-1&&compare(at.elapsed,end)===0||
   phase==='declared_end'&&spanIndex===spans.length-1&&compare(at.elapsed,stop)===0||phase==='original_grid_endpoint'&&modulo.n===0n&&compare(at.elapsed,end)<0));
  same(f.at,cur.at);need(f.phase===phase&&f.source_sha256===link.cursor.value.current_sha256&&f.source_cursor_sha256===link.sha&&f.state_kind==='confirmed_material_current');
  need(f.event_sequence===n.value.event_sequence);same(f.schedule,n.value.schedule);same(f.point_totals_exact,n.value.point_totals_exact);same(f.transfer_origins,n.value.transfer_origins);
  const globals=closed(accounts,Object.keys(units.ledger)),branch=closed(n.value.branch_ledgers,Object.keys(units.ledger)),origin=closed(seed.value.global_ledgers,Object.keys(units.ledger));
  for(const [name,unit]of Object.entries(units.ledger)){const a=object(origin[name]),b=object(branch[name]),c=object(globals[name]);for(const field of ['residual_exact','budget_exact'])eq(frac(c[field],unit),add(frac(a[field],unit),frac(b[field],unit)));}
 }else{
  need(f.phase==='material_before'&&f.source_sha256===g.md.value.point_sha256&&f.source_cursor_sha256===null&&f.state_kind==='dense_before_from_adopted_point');
  need(f.event_sequence===n.value.event_sequence);same(f.schedule,{...object(g.point.value.source_schedule),age_exact:n.value.shoot_age_exact});same(f.point_totals_exact,n.value.point_totals_exact);same(f.transfer_origins,n.value.transfer_origins);
 }
 same(f.lifetime_transfers_exact,lifetime);
 return {...storedFrameQuantities(layout,f,{snapshot:JSON.parse(snapshotRaw),lifetime,geometry,global:accounts}),at:f.at,phase:f.phase};
}
