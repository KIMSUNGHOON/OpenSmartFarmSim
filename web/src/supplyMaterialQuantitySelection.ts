import {integer} from './storedLeafReplayIO';
import {readSupplyMaterialSelection,serializeSupplyMaterialSelection,supplyMaterialSelectionURL,type SupplyMaterialSelection} from './supplyMaterialSelection';
import {SUPPLY_MATERIAL_FIXTURE as MODEL} from './supplyMaterialFixture';
import {MATERIAL_QUANTITY_FIXTURE as F} from './supplyMaterialQuantityFixture';
export type MaterialQuantitySelection=SupplyMaterialSelection&{first:number};
export const MATERIAL_QUANTITY_SELECTION_KEY=`osfs:supply-material-quantities:${MODEL.anchor.artifact_sha256}:${F.result_sha256}:selection:v1`;
function saved(raw:string|null){
 if(!raw||raw.length>1024)return null;
 try{const q=JSON.parse(raw);if(q&&typeof q==='object'&&!Array.isArray(q)&&q.result_sha256===F.result_sha256)return raw;}catch{}
 return null;
}
function first(value:unknown):value is number{return typeof value==='number'&&Number.isSafeInteger(value)&&value>=0&&value<MODEL.anchor.frames;}
export function readMaterialQuantitySelection(search:string,stored:string|null):MaterialQuantitySelection{
 const valid=saved(stored),base=readSupplyMaterialSelection(search,valid),query=new URLSearchParams(search.length<=4096?search:''),values=query.getAll('from'),raw=values[0];let start=0;
 if(valid){const q=JSON.parse(valid);if(first(q.first))start=q.first;}
 if(query.has('from'))start=values.length===1&&raw!==undefined&&/^(?:0|[1-9]\d?)$/.test(raw)&&first(Number(raw))?Number(raw):0;
 return {...base,first:Math.min(start,base.index)};
}
export function serializeMaterialQuantitySelection(value:MaterialQuantitySelection){
 serializeSupplyMaterialSelection(value);integer(value.first,0,value.index);
 return JSON.stringify({version:1,artifact_sha256:MODEL.anchor.artifact_sha256,result_sha256:F.result_sha256,index:value.index,view:value.view,panel:value.panel,first:value.first});
}
export function selectMaterialQuantityFrame(value:MaterialQuantitySelection,index:number):MaterialQuantitySelection{
 serializeMaterialQuantitySelection(value);integer(index,0,MODEL.anchor.frames-1);return {...value,index,first:Math.min(value.first,index)};
}
export function materialQuantitySelectionURL(base:string,value:MaterialQuantitySelection){
 serializeMaterialQuantitySelection(value);const url=supplyMaterialSelectionURL(base,value);url.searchParams.set('from',String(value.first));return url;
}
