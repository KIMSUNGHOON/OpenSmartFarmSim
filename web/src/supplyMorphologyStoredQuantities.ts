import {wireFields,wireItems} from './fundedLeafReplayWire';
import {closed,need,object} from './storedLeafReplayIO';
import {equal} from './leafFundedBirthReplaySchema';
import {exactAt,fraction,list,type Row} from './supplyMorphologyGraphValues';
import {MASS,exactClock,geometryProof,ledgerProof,numberQuantity,type Quantity,type ExactQuantity} from './supplyMorphologyQuantityCore';
import {quantityLayout,type QuantityLayout} from './supplyMorphologyQuantityLayout';
import {accountUnits,checkpointQuantities,exactBlock} from './supplyMorphologyQuantityAccounts';
import {readSupplyMorphologySourceGraph,type SupplyGraphAnchor} from './supplyMorphologySourceGraph';

export type StoredSupplyOrgan={id:string;parent_internode_id:string|null;geometry:Quantity;carbon:Quantity;represented_age:Quantity;
 clock_exact:ExactQuantity;birth:Row;geometry_origin:Row;geometry_diagnostics:Row;metadata:Row};
type Evidence={snapshot:unknown;lifetime:unknown;geometry:unknown;global:unknown};
const DERIVED={air_capacity:'J/m2_floor/K',canopy_capacity:'J/m2_floor/K',air_vapor_pressure:'Pa',canopy_temperature:'degC',
 canopy_temperature_rate:'K/s',leaf_area_index:'m2_leaf/m2_floor',leaf_area_index_rate:'m2_leaf/m2_floor/s',leaf_carbohydrate:MASS,stem_root_carbohydrate:MASS};

export function floatStateWire(raw:string):number[]{
 return wireItems(raw).map(token=>{const v:unknown=JSON.parse(token);need(typeof v==='number'&&Number.isFinite(v)&&/[.eE]/.test(token));return v;});
}
export function storedFrameQuantities(layout:QuantityLayout,value:unknown,evidence:Evidence){
 const f=object(value),{seed,program,n,h,size,leafMeta,nodes,stems}=layout;
 equal(f.snapshot,evidence.snapshot);equal(f.state_layout,seed.state_layout);equal(f.model_floor_area,program.model_floor_area);
 const snapshot=closed(f.snapshot,['at','state','derived']);exactAt(snapshot.at);equal(f.at,snapshot.at);
 const state=list(snapshot.state,size+2*h).map(v=>{need(typeof v==='number'&&Number.isFinite(v));return v;});need(state.length===size+2*h);
 const derived=closed(snapshot.derived,Object.keys(DERIVED));
 for(const [key,unit]of Object.entries(DERIVED))numberQuantity(derived[key],unit);
 const {flow,ledger}=accountUnits(layout),lifetime=exactBlock(evidence.lifetime,flow),geometry=closed(evidence.geometry,
  [...Array.from({length:n},(_,i)=>`leaf_${i}`),...Array.from({length:h},(_,i)=>`internode_${i}`)]);
 ledgerProof(evidence.global,ledger);equal(f.global_ledgers,evidence.global);
 const origins=closed(seed.geometry_baselines,['leaves','internodes']);
 function rows(kind:'leaf'|'internode',metadata:Row[]):StoredSupplyOrgan[]{
  const key=kind==='leaf'?'leaves':'internodes',identifier=kind==='leaf'?'leaf_id':'compartment_id',unit=kind==='leaf'?'m2':'m';
  const supplied=list(f[key]),bases=list(origins[key]);need(supplied.length===metadata.length&&bases.length===metadata.length);
  return metadata.map((meta,i)=>{
   const row=closed(supplied[i],['id','parent_internode_id','geometry','carbon','represented_age','clock_exact','birth','geometry_origin','geometry_diagnostics','metadata']);
   const baseline=object(meta.baseline),origin=closed(bases[i],[identifier,'origin','origin_elapsed_seconds_exact','origin_geometry','origin_lifetime_inflow_exact']);
   need(baseline[identifier]===meta[identifier]&&origin[identifier]===meta[identifier]);
   numberQuantity(baseline.carbon,MASS,true);numberQuantity(origin.origin_geometry,unit,true);
   need(fraction(origin.origin_elapsed_seconds_exact,'s').n>=0n);fraction(origin.origin_lifetime_inflow_exact,MASS);
   const carbonOffset=kind==='leaf'?106+2*n+i:106+3*n+stems.findIndex(s=>s.compartment_id===meta[identifier]);
   const coordinate=(offset:number,u:string):Quantity=>{const v=state[offset]!;need(v>=0);return {value:v,unit:u};};
   const expected:StoredSupplyOrgan={id:meta[identifier] as string,parent_internode_id:meta.parent_internode_id as string|null,
    geometry:coordinate(kind==='leaf'?106+n+i:size+h+i,unit),carbon:coordinate(carbonOffset,MASS),
    represented_age:coordinate(kind==='leaf'?106+i:size+i,'degC_day'),
    clock_exact:exactClock(baseline,object(snapshot.at).elapsed_seconds_exact,lifetime.indoor_air_temperature_time),
    birth:baseline,geometry_origin:origin,geometry_diagnostics:geometryProof(geometry[`${kind}_${i}`],unit),metadata:meta};
   equal(row,expected);return expected;
  });
 }
 return {...f,snapshot:{...snapshot,state,derived},leaves:rows('leaf',leafMeta),internodes:rows('internode',nodes)};
}

export async function readSupplyMorphologyStoredQuantities(readFile:(name:string)=>Promise<Uint8Array>,anchor:SupplyGraphAnchor,signal:AbortSignal){
 const g=await readSupplyMorphologySourceGraph(readFile,anchor,signal);
 const contexts=new Map(g.contexts.map(c=>[c.sha256,c])),checkpoints=new Map(g.contexts.flatMap(c=>c.checkpoints.map(cp=>[cp.value.output_prefix_sha256,cp] as const)));
 const before=new Map(g.receipts.map((m,i)=>[g.contexts[i+1]!.descriptor.value.point_sha256,m]));
 const frames=[];
 for(const context of g.contexts){
  const layout=quantityLayout(context.seed.value);
  for(const cp of context.checkpoints){
   signal.throwIfAborted();checkpointQuantities(layout,cp.value,g.root.value.shoot_base_temperature);
   const branch=wireFields(cp.fields.branch_integrated_transfers!);
   for(const raw of Object.values(branch)){const token=wireFields(raw).value!;floatStateWire('['+token+']');}
  }
 }
 for(const dto of g.frames){
  signal.throwIfAborted();const f=object(dto.value.frame),context=contexts.get(String(f.context_sha256));need(context);
  const layout=quantityLayout(context.seed.value);let evidence:Evidence;
  if(f.checkpoint_sha256!==null){
   const cp=checkpoints.get(f.output_prefix_sha256);need(cp);evidence={snapshot:cp.value.last_confirmed,lifetime:cp.value.lifetime_transfers_exact,geometry:cp.value.geometry_diagnostics,global:cp.value.global_ledgers};
  }else{
   const material=before.get(f.receipt_sha256);
   need(material);const dense=object(material.before.value.dense_candidate);
   evidence={snapshot:{at:dense.at,state:dense.state,derived:dense.derived},lifetime:dense.pending_lifetime_transfers_exact,geometry:dense.geometry_diagnostics,global:dense.global_ledgers};
  }
  const snapshot=wireFields(wireFields(dto.fields.frame!).snapshot!);floatStateWire(snapshot.state!);
  frames.push(storedFrameQuantities(layout,f,evidence));
 }
 signal.throwIfAborted();return {...g,validation_scope:'stored_quantities_http_ui_pending' as const,frames};
}
