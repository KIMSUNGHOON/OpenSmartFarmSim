import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {readCompleteCropReplay,loadCompleteCropReplay,CompleteCropRequest,type CompleteCropAnchor} from './completeCropReplay';
import {COMPLETE_CROP_FIXTURE as F} from './completeCropReplayFixture';
const file=(scenario:string,name:string)=>new Uint8Array(readFileSync(new URL(`../public/complete-crop-replay/${scenario}/${name}`,import.meta.url)));
it.each(Object.keys(F.scenarios))('reads the exact complete published trajectory in %s',async scenario=>{
 const anchor=F.scenarios[scenario as keyof typeof F.scenarios];let reads=0;
 const result=await readCompleteCropReplay(async name=>{reads++;return file(scenario,name);},anchor,new AbortController().signal);
 expect(result.frames).toHaveLength(anchor.frames);expect(reads).toBe(anchor.public_files);
 for(const frame of result.frames)expect(frame.raw).toEqual(JSON.parse(new TextDecoder().decode(file(scenario,`frame-${frame.index}.json`))).frame);
 expect(result.frames.at(-1)!.at.elapsed_seconds_exact).toEqual({numerator:'512',denominator:'1',unit:'s'});
});
it('rejects unknown wire bytes before accepting a decoded trajectory',async()=>{
 const anchor:FAnchor=F.scenarios['initial-0'];
 await expect(readCompleteCropReplay(async()=>new TextEncoder().encode('{}'),anchor,new AbortController().signal)).rejects.toThrow();
});
type FAnchor=CompleteCropAnchor;

import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';

const text=(raw:Uint8Array)=>new TextDecoder().decode(raw),bytes=(s:string)=>new TextEncoder().encode(s);
const base=JSON.parse(text(file('initial-0','index.json'))),root=JSON.parse(text(file('initial-0',base.root.path))),packet=JSON.parse(text(file('initial-0',base.packet.path)));
const pathByHash=new Map<string,string>(base.blobs.map((d:{sha256:string;path:string})=>[d.sha256,d.path]));
const dense=packet.frames.findIndex((f:{evidence:{checkpoint:unknown}})=>f.evidence.checkpoint===null);
const roles=[...new Set<string>(['index.json','root.json','NOTICE.txt',base.packet.path,
 pathByHash.get(root.contexts[0].sha256)!,pathByHash.get(root.geometry_receipts.at(-1)[0].sha256)!,
 pathByHash.get(packet.basis.source_selection.leaf_root_sha256)!,pathByHash.get(packet.basis.source_selection.stem_root_sha256)!,
 'frame-0.json',`frame-${dense}.json`,`frame-${dense+1}.json`,'frame-68.json'])];
it.each(roles)('rejects altered bytes in graph role %s',async target=>{
 await expect(readCompleteCropReplay(async name=>name===target?bytes('{}'):file('initial-0',name),F.scenarios['initial-0'],new AbortController().signal)).rejects.toThrow();
});
function alter(raw:string,path:string[],replacement:unknown):string{
 if(!path.length)return JSON.stringify(replacement);
 const key=path[0]!,remaining=path.slice(1);
 if(raw[0]==='['){const items=wireItems(raw);items[Number(key)]=alter(items[Number(key)]!,remaining,replacement);return '['+items.join(',')+']';}
 const fields=wireFields(raw);fields[key]=alter(fields[key]??'null',remaining,replacement);
 return '{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+fields[k]).join(',')+'}';
}
const mutations:Array<[string[],unknown]>=[
 [['extra'],1],[['schema_version'],'old'],[['G0_G4'],'approved'],[['R2'],'approved'],
 [['exporter_sha256'],'0'.repeat(64)],[['output_writer_sha256'],'0'.repeat(64)],
 [['blobs','0','path'],'../root.json'],[['blobs','0','bytes'],true],[['blobs','0','bytes'],2*1024**2+1],
 [['blobs','1'],base.blobs[0]],[['frames','0','index'],true],[['frames','0','phase'],'after_birth'],
 [['frames','0','checkpoint_sha256'],null],[['sample_scalars'],false],[['root','sha256'],'0'.repeat(64)],
 [['basis','source_rights','leaf','redistribute'],false],[['basis','initial_bindings','rights','redistribute'],false],
 [['basis','new_stem_carbon_allocation'],'verified'],[['basis','initial_leaf_history'],'verified'],
 [['basis','model_floor_area','unit'],'ha'],[['code_sha256','backend/app/crop_complete_artifact_reader.py'],'0'.repeat(64)]
];
it.each(mutations)('rejects independently rehashed invalid index semantics at %j',async(path,value)=>{
 const changed=alter(text(file('initial-0','index.json')),path,value),anchor={...F.scenarios['initial-0'],index_sha256:await wireHash(changed)};
 await expect(readCompleteCropReplay(async name=>name==='index.json'?bytes(changed):file('initial-0',name),anchor,new AbortController().signal)).rejects.toThrow();
});
it.each(['duplicate','depth','nonfinite','utf8','oversize'])('rejects invalid wire syntax/cap: %s',async kind=>{
 let raw:Uint8Array;
 if(kind==='duplicate'){const original=text(file('initial-0','index.json'));raw=bytes('{"scope":"software_research_only",'+original.slice(1));}
 else if(kind==='depth')raw=bytes('{"nested":'+'['.repeat(66)+'0'+']'.repeat(66)+'}');
 else if(kind==='nonfinite')raw=bytes('{"nested":1e999}');
 else if(kind==='utf8')raw=new Uint8Array([0xff,0xff]);
 else raw=new Uint8Array(2*1024**2+1);
 const {sha256}=await import('./morphologyReplay');const anchor={...F.scenarios['initial-0'],index_sha256:await sha256(new Uint8Array(raw))};
 await expect(readCompleteCropReplay(async()=>raw,anchor,new AbortController().signal)).rejects.toThrow();
});
afterEach(()=>vi.unstubAllGlobals());
function fetcher(){vi.stubGlobal('fetch',vi.fn(async(url:string,options:RequestInit)=>{
 const match=/^\.\/complete-crop-replay\/([^/]+)\/([^/]+)$/.exec(url);expect(match).not.toBeNull();
 expect(options).toMatchObject({cache:'no-store',redirect:'error',credentials:'omit'});return new Response(file(match![1]!,match![2]!));
}));}
it('aborts before/after a pending read and rejects an unknown scenario',async()=>{
 const c=new AbortController();c.abort();let calls=0;
 await expect(readCompleteCropReplay(async()=>{calls++;return file('initial-0','index.json');},F.scenarios['initial-0'],c.signal)).rejects.toThrow();expect(calls).toBe(0);
 let release!:(v:Uint8Array)=>void;const current=new AbortController(),pending=readCompleteCropReplay(()=>new Promise(resolve=>release=resolve),F.scenarios['initial-0'],current.signal);
 current.abort();release(file('initial-0','index.json'));await expect(pending).rejects.toThrow();
 await expect(loadCompleteCropReplay('unknown',new AbortController().signal)).rejects.toThrow();
});
it('discards the older response when a fetcher ignores cancellation',async()=>{
 let release!:(r:Response)=>void;let first=true;fetcher();const original=fetch;
 vi.stubGlobal('fetch',vi.fn(async(...args:Parameters<typeof fetch>)=>{
  if(first){first=false;return new Promise<Response>(resolve=>release=resolve);}return original(...args);
 }));
 const request=new CompleteCropRequest(),one=request.load('initial-0');const rejected=expect(one).rejects.toThrow();
 const two=await request.load('additional-0');expect(two.frames).toHaveLength(70);release(new Response(file('initial-0','index.json')));await rejected;
});
it('returns independent projections on a second load',async()=>{
 fetcher();const one=await loadCompleteCropReplay('initial-0',new AbortController().signal);const old=one.frames[0]!.leaves[0]!.area.value;
 one.frames[0]!.leaves[0]!.area.value=999;one.frames[0]!.snapshot.state=[];
 const two=await loadCompleteCropReplay('initial-0',new AbortController().signal);expect(two.frames[0]!.leaves[0]!.area.value).toBe(old);expect(two.frames[0]!.snapshot.state).not.toHaveLength(0);
});
