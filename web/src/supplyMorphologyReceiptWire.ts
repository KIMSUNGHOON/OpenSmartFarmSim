import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {closed,digest,need,STORED_LEAF_MAX_BYTES} from './storedLeafReplayIO';

const encoder=new TextEncoder();
const size=(raw:string)=>encoder.encode(raw).byteLength;

function codepointOrder(a:string,b:string){
 const x=[...a],y=[...b];
 for(let i=0;i<Math.min(x.length,y.length);i++){
  const difference=x[i]!.codePointAt(0)!-y[i]!.codePointAt(0)!;
  if(difference)return difference;
 }
 return x.length-y.length;
}

/** Restores original wire bytes only; full crop replay semantics are checked later. */
export async function expandSupplyMorphologyReceipt(parentSeedRaw:string,packedRaw:string,modelPinsRaw:string):Promise<string>{
 for(const raw of [parentSeedRaw,packedRaw,modelPinsRaw]){
  need(typeof raw==='string'&&raw.length>0&&raw.length<=STORED_LEAF_MAX_BYTES&&size(raw)<=STORED_LEAF_MAX_BYTES);
 }
 const containers=new Map<string,Record<string,string>|string[]>();
 function fieldsOf(raw:string){
  const previous=containers.get(raw);
  if(previous!==undefined){need(!Array.isArray(previous));return previous;}
  const value=wireFields(raw);if(containers.size<4096)containers.set(raw,value);return value;
 }
 function itemsOf(raw:string){
  const previous=containers.get(raw);
  if(previous!==undefined){need(Array.isArray(previous));return previous;}
  const value=wireItems(raw);if(containers.size<4096)containers.set(raw,value);return value;
 }
 fieldsOf(parentSeedRaw);
 const pins=fieldsOf(modelPinsRaw);
 need(Object.keys(pins).length>=1&&Object.keys(pins).length<=102);
 for(const raw of Object.values(pins))digest(JSON.parse(raw));
 const fields=fieldsOf(packedRaw);
 const packed=closed(JSON.parse(packedRaw),['version','receipt_sha256','source_code_set_sha256','body']);
 need(packed.version==='supply-morphology-parent-referenced-receipt-v1');
 digest(packed.receipt_sha256);digest(packed.source_code_set_sha256);
 need(await wireHash(modelPinsRaw)===packed.source_code_set_sha256);
 let used=0;
 const consume=(count:number)=>{used+=count;need(used<=STORED_LEAF_MAX_BYTES);};

 function reference(sourceRaw:string,pathRaw:string):string{
  need(sourceRaw==='0'||sourceRaw==='1');
  const path=itemsOf(pathRaw);need(path.length<=64);
  let value=sourceRaw==='0'?parentSeedRaw:modelPinsRaw;
  for(const part of path){
   if(value[0]==='{'){
    const key:unknown=JSON.parse(part);need(typeof key==='string');
    const q=fieldsOf(value);need(Object.hasOwn(q,key));value=q[key]!;
   }else{
    need(value[0]==='['&&/^(?:0|[1-9]\d*)$/.test(part));
    const index=Number(part),items=itemsOf(value);
    need(Number.isSafeInteger(index)&&index<items.length);value=items[index]!;
   }
  }
  consume(size(value));return value;
 }

 function decode(raw:string,depth:number):string{
  need(depth<=64);
  if(raw[0]!=='['){
   const value:unknown=JSON.parse(raw);
   need(value===null||typeof value==='string'||typeof value==='boolean'||typeof value==='number'&&Number.isFinite(value));
   consume(size(raw));return raw;
  }
  const node=itemsOf(raw);need(node.length===2||node.length===3);
  if(node[0]==='2'){
   need(node.length===3);return reference(node[1]!,node[2]!);
  }
  need(node.length===2);
  if(node[0]==='0'){
   const values=fieldsOf(node[1]!),keys=Object.keys(values).sort(codepointOrder);
   consume(2+Math.max(0,keys.length-1)+keys.reduce((sum,key)=>sum+size(JSON.stringify(key))+1,0));
   return '{'+keys.map(key=>JSON.stringify(key)+':'+decode(values[key]!,depth+1)).join(',')+'}';
  }
  need(node[0]==='1');
  const values=itemsOf(node[1]!);consume(2+Math.max(0,values.length-1));
  return '['+values.map(value=>decode(value,depth+1)).join(',')+']';
 }

 const expanded=decode(fields.body!,0);
 need(size(expanded)===used&&await wireHash(expanded)===packed.receipt_sha256);
 return expanded;
}
