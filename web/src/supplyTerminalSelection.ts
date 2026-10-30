import {integer} from './storedLeafReplayIO';
import {readSupplySelection,serializeSupplySelection,supplySelectionURL,type SupplySelection} from './supplyMorphologySelection';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';

export type SupplyTerminalSelection=SupplySelection&{first:number};
export const SUPPLY_TERMINAL_SELECTION_KEY=`osfs:supply-terminal:${F.anchor.artifact_sha256}:selection:v1`;
function validFirst(value:unknown):value is number{
 return typeof value==='number'&&Number.isSafeInteger(value)&&value>=0&&value<F.anchor.frames;
}
function savedFirst(raw:string|null){
 if(!raw||raw.length>1024)return 0;
 try{
  const value:unknown=JSON.parse(raw);
  if(value&&typeof value==='object'&&!Array.isArray(value)&&'version'in value&&value.version===1
   &&'artifact_sha256'in value&&value.artifact_sha256===F.anchor.artifact_sha256
   &&'first'in value&&validFirst(value.first))return value.first;
 }catch{}
 return 0;
}
export function readSupplyTerminalSelection(search:string,stored:string|null):SupplyTerminalSelection{
 const base=readSupplySelection(search,stored),query=new URLSearchParams(search.length<=4096?search:'');
 const values=query.getAll('from'),raw=values[0];let first=savedFirst(stored);
 if(query.has('from'))first=values.length===1&&raw!==undefined&&/^(?:0|[1-9]\d?)$/.test(raw)&&validFirst(Number(raw))?Number(raw):0;
 return {...base,first:Math.min(first,base.index)};
}
export function serializeSupplyTerminalSelection(value:SupplyTerminalSelection){
 serializeSupplySelection(value);integer(value.first,0,value.index);
 return JSON.stringify({version:1,artifact_sha256:F.anchor.artifact_sha256,index:value.index,view:value.view,panel:value.panel,first:value.first});
}
export function selectSupplyTerminalFrame(value:SupplyTerminalSelection,index:number):SupplyTerminalSelection{
 serializeSupplyTerminalSelection(value);integer(index,0,F.anchor.frames-1);
 return {...value,index,first:Math.min(value.first,index)};
}
export function supplyTerminalSelectionURL(base:string,value:SupplyTerminalSelection){
 serializeSupplyTerminalSelection(value);const url=supplySelectionURL(base,value);url.searchParams.set('from',String(value.first));return url;
}
