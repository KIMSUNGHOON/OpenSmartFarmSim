import {closed,digest,need,object,STORED_LEAF_MAX_BYTES} from './storedLeafReplayIO';
import {equal} from './leafFundedBirthReplaySchema';
import {sha256} from './morphologyReplay';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {counter,document,exactAt,fraction,list,wireObject,type WireDocument} from './supplyMorphologyGraphValues';
import {exactRecord} from './supplyMorphologyQuantityCore';
import {floatStateWire} from './supplyMorphologyStoredQuantities';
import {publicMaterialRights} from './supplyMaterialGraphChecks';
import type {readSupplyMaterialFiles} from './supplyMaterialGraph';
import {MATERIAL_QUANTITY_FIXTURE as F} from './supplyMaterialQuantityFixture';
import {MATERIAL_COUNTER_UNITS as UNITS,quantityStock,materialQuantityWindow,type MaterialQuantityFrame,type QuantityAt} from './supplyMaterialQuantityValues';
export type MaterialQuantityAnchor={fixture_sha256:string;fixture_bytes:number;result_sha256:string;result_bytes:number};
type Graph=Awaited<ReturnType<typeof readSupplyMaterialFiles>>;
function at(value:unknown):QuantityAt{const t=exactAt(value);return {time_origin_utc:t.origin,elapsed_seconds_exact:exactRecord(t.elapsed,'s')};}
function hash(value:unknown){digest(value);return value;}

/** Remove formatting while retaining the original Python float lexemes. */
export function canonicalQuantityWire(raw:string):string{
 raw=raw.trim();if(raw[0]==='{'){const fields=wireFields(raw);return '{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+canonicalQuantityWire(fields[k]!)).join(',')+'}';}
 if(raw[0]==='[')return '['+wireItems(raw).map(canonicalQuantityWire).join(',')+']';return raw;
}
export async function validateMaterialQuantityWire(raw:Uint8Array,g:Graph,original:WireDocument[],signal:AbortSignal,anchor:MaterialQuantityAnchor=F){
 signal.throwIfAborted();need(raw instanceof Uint8Array&&raw.byteLength>0&&raw.byteLength<=STORED_LEAF_MAX_BYTES&&raw.byteLength===anchor.fixture_bytes);
 const snapshot=new Uint8Array(raw);need(await sha256(snapshot)===anchor.fixture_sha256);signal.throwIfAborted();
 const doc=document(new TextDecoder('utf-8',{fatal:true}).decode(snapshot)),p=closed(doc.value,['schema_version','scope','G0_G4','R2','provenance','effective_rights','notice','projection_code_sha256','result_sha256','canonical_result_bytes','result']);
 need(p.schema_version===F.schema_version&&p.scope==='software_research_only'&&p.G0_G4==='not_assessed'&&p.R2==='not_approved');
 counter(doc,'canonical_result_bytes',1,STORED_LEAF_MAX_BYTES);counter(document(doc.fields.notice!),'bytes',1,STORED_LEAF_MAX_BYTES);
 publicMaterialRights(p.effective_rights);equal(p.notice,F.notice);need(p.projection_code_sha256===F.projection_code_sha256&&p.result_sha256===anchor.result_sha256);
 const canonical=canonicalQuantityWire(doc.fields.result!);need(new TextEncoder().encode(canonical).byteLength===anchor.result_bytes&&p.canonical_result_bytes===anchor.result_bytes&&await wireHash(canonical)===anchor.result_sha256);
 const provenance=closed(p.provenance,['source_url','product_id','observed_at','published_at','available_at','retrieved_at','vintage','revision','units','qc','raw_sha256','reviewer','source_artifact_sha256']);
 need(provenance.source_url==='urn:opensmartfarmsim:own-public-material-quantity-fixture-v1'&&provenance.product_id==='own-public-material-quantities-v1'&&provenance.observed_at===null);
 need(provenance.qc==='software_contract_only_not_farm_measurements'&&provenance.reviewer==='native-gpt-6.1-sol-xhigh'&&provenance.vintage==='own'&&provenance.revision==='own-public-v1');
 need(provenance.available_at===provenance.published_at&&provenance.available_at===provenance.retrieved_at&&typeof provenance.available_at==='string'&&Number.isFinite(Date.parse(provenance.available_at)));
 need(provenance.raw_sha256===anchor.result_sha256&&provenance.source_artifact_sha256===g.artifact_sha256);
 equal(provenance.units,{stock_carbohydrate:'mg_CH2O/m2_floor',stock_number:'fruits_equivalent/m2_floor',...UNITS});
 const result=document(doc.fields.result!),r=closed(result.value,['schema_version','scope','claim_scope','time_kind','G0_G4','R2','projection_code_sha256','source','model_floor_area','counter_units','window','frames','intervals','totals_exact']);
 need(r.schema_version===F.result_schema_version&&r.scope==='software_research_only'&&r.claim_scope==='stored_synthetic_material_quantities_only'&&r.time_kind===g.root.value.time_kind&&r.G0_G4==='not_assessed'&&r.R2==='not_approved'&&r.projection_code_sha256===F.projection_code_sha256);
 const source=closed(r.source,['artifact_sha256','code_sha256','effective_rights','source','window','terminal']);need(source.artifact_sha256===g.artifact_sha256);
 const sourceWire=document(result.fields.source!);
 for(const key of ['code_sha256','effective_rights','source','window','terminal']){equal(source[key],g.root.value[key]);need(canonicalQuantityWire(sourceWire.fields[key]!)===g.root.fields[key]);}
 equal(r.model_floor_area,object(g.frames[0]).model_floor_area);need(canonicalQuantityWire(result.fields.model_floor_area!)===original[0]!.fields.model_floor_area);
 equal(r.counter_units,UNITS);publicMaterialRights(source.effective_rights);
 const rows=wireItems(result.fields.frames!),descriptors=list(g.root.value.frames);need(rows.length===g.frames.length&&original.length===rows.length);
 const frames:MaterialQuantityFrame[]=[],references:string[]=[],descriptorRaw=wireItems(g.root.fields.frames!);
 for(const [i,body]of rows.entries()){
  signal.throwIfAborted();const d=document(body),v=closed(d.value,['reference','at','phase','fruit_carbohydrate','fruit_number','carbohydrate_stock_exact','number_stock_exact','cumulative_exact']);
  const model=g.frames[i]!,m=object(model),rawModel=original[i]!;
  const stateRaw=wireFields(rawModel.fields.snapshot!).state!,ref=document(d.fields.reference!);
  const stateHash=await wireHash(stateRaw),expected=wireFields(descriptorRaw[i]!);expected.state_sha256=JSON.stringify(stateHash);expected.state_kind=JSON.stringify(m.state_kind);
  equal(ref.value,{...object(descriptors[i]),state_sha256:stateHash,state_kind:m.state_kind});
  need(canonicalQuantityWire(ref.raw)===wireObject(expected));references.push(wireObject(expected));
  need(counter(ref,'index',0,rows.length-1)===i);counter(ref,'bytes',1,STORED_LEAF_MAX_BYTES);counter(ref,'state_scalars',1,32768);counter(ref,'event_sequence');
  need(typeof ref.value.phase==='string'&&typeof ref.value.state_kind==='string');equal(v.at,m.at);equal(v.phase,m.phase);equal(ref.value.at,v.at);equal(ref.value.phase,v.phase);
  const vectors:{values:number[];unit:string}[]=[];
  for(const [name,start,unit]of [['fruit_carbohydrate',3,'mg_CH2O/m2_floor'],['fruit_number',53,'fruits_equivalent/m2_floor']]as const){
   const q=closed(v[name],['values','unit']);need(q.unit===unit);const values=floatStateWire(wireFields(d.fields[name]!).values!);
   need(values.length===50&&values.every((n,j)=>Object.is(n,model.snapshot.state[start+j])&&n>=0));vectors.push({values,unit});
  }
  const carbon=vectors[0]!,number=vectors[1]!;need(carbon.values.every((c,j)=>c===0||number.values[j]!>0));
  const c=quantityStock(carbon.values,carbon.unit),n=quantityStock(number.values,number.unit);equal(v.carbohydrate_stock_exact,c);equal(v.number_stock_exact,n);
  const supplied=closed(v.cumulative_exact,Object.keys(UNITS)),actual=object(m.lifetime_transfers_exact),cumulative:MaterialQuantityFrame['cumulative_exact']={};
  for(const [name,unit]of Object.entries(UNITS)){const q=fraction(supplied[name],unit);if(name==='terminal_carbon'||name==='terminal_number')need(q.n>=0n);equal(supplied[name],actual[name]);cumulative[name]=exactRecord(q,unit);}
  const rv=ref.value,phase=rv.phase,kind=rv.state_kind;need(typeof phase==='string'&&typeof kind==='string');
  frames.push({reference:{index:i,phase,at:at(rv.at),source_sha256:hash(rv.source_sha256),source_cursor_sha256:rv.source_cursor_sha256===null?null:hash(rv.source_cursor_sha256),
   event_sequence:counter(ref,'event_sequence'),frame_sha256:hash(rv.frame_sha256),bytes:counter(ref,'bytes',1,STORED_LEAF_MAX_BYTES),state_scalars:counter(ref,'state_scalars',1,32768),state_sha256:hash(rv.state_sha256),state_kind:kind},
   at:at(v.at),phase,fruit_carbohydrate:carbon,fruit_number:number,carbohydrate_stock_exact:c,number_stock_exact:n,cumulative_exact:cumulative});
 }
 const window=document(result.fields.window!);counter(window,'first_frame',0,frames.length-1);counter(window,'last_frame',0,frames.length-1);
 for(const [i,body]of wireItems(result.fields.intervals!).entries()){
  const row=document(body);need(canonicalQuantityWire(row.fields.from_frame!)===references[i]&&canonicalQuantityWire(row.fields.to_frame!)===references[i+1]);
 }
 const selected=materialQuantityWindow(frames);equal(r.window,selected.window);equal(r.intervals,selected.intervals);equal(r.totals_exact,selected.totals_exact);
 signal.throwIfAborted();return {frames,source:r.source,model_floor_area:r.model_floor_area,fixture:doc,result};
}
