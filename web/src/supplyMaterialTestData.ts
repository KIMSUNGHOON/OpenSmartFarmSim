import {readFileSync} from 'node:fs';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {SUPPLY_MATERIAL_FIXTURE as F} from './supplyMaterialFixture';

export const file=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-material-replay/own-public-v1/${name}`,import.meta.url)));
export const text=(name:string)=>new TextDecoder().decode(file(name));
export const bytes=(raw:string)=>new TextEncoder().encode(raw);
export function alter(raw:string,path:string[],value:unknown):string{
 if(!path.length)return JSON.stringify(value);
 const key=path[0]!,tail=path.slice(1);
 if(raw[0]==='['){const items=wireItems(raw);items[Number(key)]=alter(items[Number(key)]!,tail,value);return '['+items.join(',')+']';}
 const fields=wireFields(raw);fields[key]=alter(fields[key]??'null',tail,value);
 return '{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+fields[k]).join(',')+'}';
}
export async function repack(rootRaw=text('root.json'),changedFrame?:{index:number;raw:string}){
 if(changedFrame){
  const j=String(changedFrame.index);
  rootRaw=alter(rootRaw,['frames',j,'frame_sha256'],await wireHash(changedFrame.raw));
  rootRaw=alter(rootRaw,['frames',j,'bytes'],bytes(changedFrame.raw).byteLength);
 }
 const rootSHA=await wireHash(rootRaw),index=JSON.parse(text('index.json')),files=new Map<string,Uint8Array>([['root.json',bytes(rootRaw)]]);
 index.artifact_sha256=rootSHA;index.root={path:'root.json',sha256:rootSHA,bytes:bytes(rootRaw).byteLength};
 index.blobs[index.blobs.findIndex((d:{path:string})=>d.path==='root.json')]=index.root;
 const root=JSON.parse(rootRaw);for(const key of ['window','terminal','effective_rights','code_sha256'])index[key]=root[key];
 for(let j=0;j<4;j++){
  let raw=text(`frame-${j}.json`);
  if(changedFrame?.index===j){const fields=wireFields(raw);fields.frame=changedFrame.raw;raw='{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+fields[k]).join(',')+'}';}
  raw=alter(raw,['artifact_sha256'],rootSHA);files.set(`frame-${j}.json`,bytes(raw));
  Object.assign(index.frames[j],root.frames[j],{path:`frame-${j}.json`,sha256:await wireHash(raw),bytes:bytes(raw).byteLength});
 }
 const raw=JSON.stringify(index);files.set('index.json',bytes(raw));
 return {anchor:{...F.anchor,artifact_sha256:rootSHA,index_sha256:await wireHash(raw)},read:async(name:string)=>files.get(name)??file(name)};
}
