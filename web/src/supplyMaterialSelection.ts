import {SUPPLY_MATERIAL_FIXTURE as F} from './supplyMaterialFixture';
export type SupplyView='connected'|'unbound'|'all';
export type SupplyPanel='scene'|'data';
export type SupplyMaterialSelection={index:number;view:SupplyView;panel:SupplyPanel};
export const SUPPLY_MATERIAL_SELECTION_KEY=`osfs:supply-material:${F.anchor.artifact_sha256}:selection:v1`;
const initial:SupplyMaterialSelection={index:0,view:'connected',panel:'scene'};
const validIndex=(v:unknown):v is number=>typeof v==='number'&&Number.isSafeInteger(v)&&v>=0&&v<F.anchor.frames;
const validView=(v:unknown):v is SupplyView=>v==='connected'||v==='unbound'||v==='all';
const validPanel=(v:unknown):v is SupplyPanel=>v==='scene'||v==='data';
function storedSelection(raw:string|null):SupplyMaterialSelection{
 if(!raw||raw.length>1024)return {...initial};
 try{
  const q=JSON.parse(raw) as Record<string,unknown>;
  if(q?.version===1&&q.artifact_sha256===F.anchor.artifact_sha256&&validIndex(q.index)&&validView(q.view)&&validPanel(q.panel))return {index:q.index,view:q.view,panel:q.panel};
 }catch{}
 return {...initial};
}
export function readSupplyMaterialSelection(search:string,stored:string|null):SupplyMaterialSelection{
 const saved=storedSelection(stored),query=new URLSearchParams(search.length<=4096?search:'');
 const raw=query.get('frame'),index=raw!==null&&/^(?:0|[1-9]\d?)$/.test(raw)?Number(raw):undefined,view=query.get('view'),panel=query.get('panel');
 return {index:query.has('frame')?validIndex(index)?index:0:saved.index,
  view:query.has('view')?validView(view)?view:'connected':saved.view,
  panel:query.has('panel')?validPanel(panel)?panel:'scene':saved.panel};
}
export function serializeSupplyMaterialSelection(value:SupplyMaterialSelection){
 if(!validIndex(value.index)||!validView(value.view)||!validPanel(value.panel))throw Error('invalid_supply_selection');
 return JSON.stringify({version:1,artifact_sha256:F.anchor.artifact_sha256,index:value.index,view:value.view,panel:value.panel});
}
export function supplyMaterialSelectionURL(base:string,value:SupplyMaterialSelection){
 serializeSupplyMaterialSelection(value);const url=new URL(base);url.searchParams.set('frame',String(value.index));url.searchParams.set('view',value.view);url.searchParams.set('panel',value.panel);return url;
}
