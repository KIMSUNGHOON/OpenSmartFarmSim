import {id,integer,need,object} from './storedLeafReplayIO';
import {exactAt} from './supplyMorphologyGraphValues';
import {exactRecord} from './supplyMorphologyQuantityCore';
import type {SupplyStoredFrame} from './supplyMorphologyReplay';
export type Position=[number,number,number];
export type SupplyNodePlacement={id:string;parent_internode_id:string|null;base:Position;tip:Position;length_m:number};
export type SupplyLeafPlacement={id:string;parent_internode_id:string|null;position:Position;area_m2:number;
 status:'declared_parent'|'unbound_display_only';yaw_rad:number};
export const SUPPLY_GEOMETRY_MAPPING='stored-supply-area-length-parent-forest-v1';
export const SUPPLY_GEOMETRY_POSE='authored-independent-roots-and-unbound-leaf-display-v1';

export function supplyPlantLayout(frame:SupplyStoredFrame){
 const f=object(frame),time=exactAt(f.at);need(typeof time.origin==='string');integer(f.index,0,511);
 need(typeof f.phase==='string'&&['fractional_before_compatible_material_point','fractional_after_compatible_material_point','original_grid_endpoint'].includes(f.phase));
 need(f.G0_G4==='not_assessed'&&f.R2==='not_approved');
 const metadata={at:{time_origin_utc:time.origin,elapsed_seconds_exact:exactRecord(time.elapsed,'s')},phase:f.phase,index:f.index,G0_G4:f.G0_G4,R2:f.R2};
 need(Array.isArray(frame.internodes)&&frame.internodes.length>=1&&frame.internodes.length<=512&&Array.isArray(frame.leaves)&&frame.leaves.length<=512);
 const nodes=frame.internodes.map(n=>({id:n.id,parent:n.parent_internode_id,length:n.geometry.value}));
 const leaves=frame.leaves.map(l=>({id:l.id,parent:l.parent_internode_id,area:l.geometry.value}));
 const nodeIDs=new Set(nodes.map(n=>n.id));need(nodeIDs.size===nodes.length&&new Set(leaves.map(l=>l.id)).size===leaves.length);
 for(const [rows,kind,unit]of [[frame.internodes,'node','m'],[frame.leaves,'leaf','m2']]as const){
  for(const row of rows){id(row.id);need(row.geometry.unit===unit&&typeof row.geometry.value==='number'&&Number.isFinite(row.geometry.value)&&row.geometry.value>=0);
   need(row.parent_internode_id===null||typeof row.parent_internode_id==='string'&&nodeIDs.has(row.parent_internode_id));
   if(kind==='node')need(row.parent_internode_id!==row.id);
  }
 }
 const source=new Map(nodes.map(n=>[n.id,n])),done=new Map<string,SupplyNodePlacement>(),visiting=new Set<string>();
 const roots=nodes.filter(n=>n.parent===null),unbound=leaves.filter(l=>l.parent===null);
 const resolve=(key:string):SupplyNodePlacement=>{
  const ready=done.get(key);if(ready)return ready;need(!visiting.has(key));visiting.add(key);const node=source.get(key);need(node);
  const base:Position=node.parent===null?[roots.findIndex(n=>n.id===key)*.25,0,0]:[...resolve(node.parent).tip];
  const result={id:key,parent_internode_id:node.parent,base,tip:[base[0],base[1]+node.length,base[2]]as Position,length_m:node.length};
  need(result.tip.every(Number.isFinite));visiting.delete(key);done.set(key,result);return result;
 };
 const placements=nodes.map(n=>resolve(n.id));
 const leafPlacements:SupplyLeafPlacement[]=leaves.map(l=>{
  let hash=2166136261;for(const ch of l.id)hash=Math.imul(hash^ch.charCodeAt(0),16777619)>>>0;
  return {id:l.id,parent_internode_id:l.parent,area_m2:l.area,
   position:l.parent===null?[.75+unbound.findIndex(x=>x.id===l.id)*1.2,.35,0]:[...resolve(l.parent).tip],
   status:l.parent===null?'unbound_display_only':'declared_parent',yaw_rad:hash/2**32*Math.PI*2};
 });
 return {nodes:placements,leaves:leafPlacements,metadata};
}
