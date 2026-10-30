import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {readSupplyMorphologySourceGraph} from './supplyMorphologySourceGraph';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';

const file=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url)));
const text=(name:string)=>new TextDecoder().decode(file(name));
const bytes=(value:string)=>new TextEncoder().encode(value);
it('links every original file and frame without approving a crop UI projection',async()=>{
 const names:string[]=[];
 const g=await readSupplyMorphologySourceGraph(async name=>{names.push(name);return file(name);},F.anchor,new AbortController().signal);
 expect(g.validation_scope).toBe('source_graph_only_quantities_pending');expect(g.contexts).toHaveLength(6);
 expect(g.contexts.flatMap(c=>c.checkpoints)).toHaveLength(33);expect(g.receipts).toHaveLength(5);expect(g.frames).toHaveLength(38);
 expect(names).toHaveLength(101);expect(new Set(names).size).toBe(101);
 for(const [i,frame]of g.frames.entries())expect(frame.raw).toBe(text(`frame-${i}.json`));
});
function alter(raw:string,path:string[],value:unknown):string{
 if(!path.length)return JSON.stringify(value);
 const key=path[0]!,tail=path.slice(1);
 if(raw[0]==='['){const v=wireItems(raw);v[Number(key)]=alter(v[Number(key)]!,tail,value);return '['+v.join(',')+']';}
 const v=wireFields(raw);v[key]=alter(v[key]??'null',tail,value);return '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+v[k]).join(',')+'}';
}
it.each([
 [['extra'],1],[['G0_G4'],'approved'],[['R2'],'approved'],[['schema_version'],'old'],
 [['source_rights','crop','redistribute'],false],[['source_rights','declaration','display'],false],
 [['code_sha256','backend/app/crop_supply_morphology_artifact_reader.py'],'0'.repeat(64)],
 [['exporter_sha256'],'0'.repeat(64)],[['output_writer_sha256'],'0'.repeat(64)],
 [['blobs','0','path'],'../root.json'],[['blobs','0','bytes'],true],[['blobs','0','bytes'],2*1024**2+1],
 [['sample_scalars'],32769],[['frames','0','index'],true],[['notice','sha256'],'0'.repeat(64)]
] as Array<[string[],unknown]>)('rejects independently rehashed invalid index %j',async(path,value)=>{
 const raw=alter(text('index.json'),path,value),anchor={...F.anchor,index_sha256:await wireHash(raw)};
 await expect(readSupplyMorphologySourceGraph(async name=>name==='index.json'?bytes(raw):file(name),anchor,new AbortController().signal)).rejects.toThrow();
});
it.each(['index.json','root.json','NOTICE.txt','frame-0.json','frame-37.json'])('rejects altered original graph bytes in %s',async target=>{
 await expect(readSupplyMorphologySourceGraph(async name=>name===target?bytes('{}'):file(name),F.anchor,new AbortController().signal)).rejects.toThrow();
});
it('rejects an aborted read before and after waiting for original bytes',async()=>{
 const a=new AbortController();a.abort();let calls=0;
 await expect(readSupplyMorphologySourceGraph(async()=>{calls++;return file('index.json');},F.anchor,a.signal)).rejects.toThrow();expect(calls).toBe(0);
 const b=new AbortController();let release!:(raw:Uint8Array)=>void;
 const pending=readSupplyMorphologySourceGraph(()=>new Promise(resolve=>release=resolve),F.anchor,b.signal);
 b.abort();release(file('index.json'));await expect(pending).rejects.toThrow();
});

it.each([
 [['extra'],1],[['G0_G4'],'approved'],[['R2'],'approved'],[['redistribution_authorized'],false],
 [['selection','stem_start_index'],-1],[['source_rights','stem','redistribute'],false],
 [['root_inputs','growth_profile','sha256'],'0'.repeat(64)],[['segments'],[]],
 [['segments','0','checkpoints'],[]],[['terminal','status'],'unknown']
] as Array<[string[],unknown]>)('rejects independently rehashed invalid root %j',async(path,value)=>{
 const root=alter(text('root.json'),path,value),hash=await wireHash(root),index=JSON.parse(text('index.json'));
 index.artifact_sha256=hash;index.root={path:'root.json',sha256:hash,bytes:bytes(root).byteLength};
 const original=index.blobs.findIndex((d:{path:string})=>d.path==='root.json');index.blobs[original]=index.root;
 const indexRaw=JSON.stringify(index),anchor={...F.anchor,artifact_sha256:hash,index_sha256:await wireHash(indexRaw)};
 await expect(readSupplyMorphologySourceGraph(async name=>name==='index.json'?bytes(indexRaw):name==='root.json'?bytes(root):file(name),anchor,new AbortController().signal)).rejects.toThrow();
});
it('rejects a byte-valid but unreachable extra source file',async()=>{
 const index=JSON.parse(text('index.json')),raw='{}',hash=await wireHash(raw),path=`blob-${hash}.json`;
 expect(index.blobs.some((d:{sha256:string})=>d.sha256===hash)).toBe(false);
 index.blobs.push({path,sha256:hash,bytes:2});const indexRaw=JSON.stringify(index);
 const anchor={...F.anchor,index_sha256:await wireHash(indexRaw),public_files:F.anchor.public_files+1};
 await expect(readSupplyMorphologySourceGraph(async name=>name==='index.json'?bytes(indexRaw):name===path?bytes(raw):file(name),anchor,new AbortController().signal)).rejects.toThrow();
});
it.each(['duplicate','utf8','depth','nonfinite','oversize'])('rejects invalid input wire %s',async kind=>{
 let raw:Uint8Array;
 if(kind==='duplicate')raw=bytes('{"scope":"software_research_only",'+text('index.json').slice(1));
 else if(kind==='utf8')raw=new Uint8Array([255]);
 else if(kind==='depth')raw=bytes('{"x":'+'['.repeat(66)+'0'+']'.repeat(66)+'}');
 else if(kind==='nonfinite')raw=bytes('{"x":1e999}');
 else raw=new Uint8Array(2*1024**2+1);
 const {sha256}=await import('./morphologyReplay');const anchor={...F.anchor,index_sha256:await sha256(new Uint8Array(raw))};
 await expect(readSupplyMorphologySourceGraph(async()=>raw,anchor,new AbortController().signal)).rejects.toThrow();
});
it('rejects declared aggregate overflow before downloading any source or frame',async()=>{
 const index=JSON.parse(text('index.json'));index.frames.forEach((d:{bytes:number})=>{d.bytes=2*1024**2;});
 const raw=JSON.stringify(index),anchor={...F.anchor,index_sha256:await wireHash(raw)};let reads=0;
 await expect(readSupplyMorphologySourceGraph(async name=>{reads++;return name==='index.json'?bytes(raw):file(name);},anchor,new AbortController().signal)).rejects.toThrow();
 expect(reads).toBe(1);
});
it('keeps a valid native held result without restricting its original hold prefix',async()=>{
 const terminal={status:'hold',hold:'clock2_HOLD: preserved source reason'};
 const root=alter(text('root.json'),['terminal'],terminal),rootHash=await wireHash(root),index=JSON.parse(text('index.json'));
 index.artifact_sha256=rootHash;index.terminal=terminal;
 index.root={path:'root.json',sha256:rootHash,bytes:bytes(root).byteLength};
 index.blobs[index.blobs.findIndex((d:{path:string})=>d.path==='root.json')]=index.root;
 const changed=new Map<string,Uint8Array>([['root.json',bytes(root)]]);
 for(const [i,d]of index.frames.entries()){
  const raw=alter(text(`frame-${i}.json`),['artifact_sha256'],rootHash);
  d.sha256=await wireHash(raw);d.bytes=bytes(raw).byteLength;changed.set(`frame-${i}.json`,bytes(raw));
 }
 const raw=JSON.stringify(index);changed.set('index.json',bytes(raw));
 const anchor={...F.anchor,artifact_sha256:rootHash,index_sha256:await wireHash(raw)};
 const g=await readSupplyMorphologySourceGraph(async name=>changed.get(name)??file(name),anchor,new AbortController().signal);
 expect(g.root.value.terminal).toEqual(terminal);expect(g.validation_scope).toBe('source_graph_only_quantities_pending');
});
