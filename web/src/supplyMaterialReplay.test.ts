import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadSupplyMaterialReplay,SupplyMaterialRequest} from './supplyMaterialReplay';
const bytes=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-material-replay/own-public-v1/${name}`,import.meta.url)));
const original=(i:number)=>JSON.parse(new TextDecoder().decode(bytes(`frame-${i}.json`))).frame;
const signal=()=>new AbortController().signal;
afterEach(()=>vi.unstubAllGlobals());
function transport(){return vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
 expect(String(input)).toMatch(/^\.\/supply-material-replay\/own-public-v1\/(?:index\.json|root\.json|NOTICE\.txt|blob-[a-f0-9]{64}\.json|frame-\d+\.json)$/);
 expect(options).toMatchObject({cache:'no-store',redirect:'error',credentials:'omit'});
 expect(options!.signal).toBeInstanceOf(AbortSignal);
 return new Response(bytes(String(input).split('/').at(-1)!));
});}
it('loads the original106files and exact before/after/remainder in the new namespace',async()=>{
 const fetch=transport();vi.stubGlobal('fetch',fetch);const replay=await loadSupplyMaterialReplay(signal());
 expect(fetch).toHaveBeenCalledTimes(106);expect(replay.summary().frames).toBe(4);expect(replay.summary().sample_scalars).toBe(722);
 expect(replay.summary().G0_G4).toBe('not_assessed');expect(replay.summary().R2).toBe('not_approved');
 for(let i=0;i<4;i++)expect(replay.frame(i)).toEqual(original(i));
 expect(replay.frame(0).leaves).toHaveLength(11);expect(replay.frame(1).leaves).toHaveLength(12);
},20000);
it('isolates copies and rejects invalid frame selectors',async()=>{
 vi.stubGlobal('fetch',transport());const replay=await loadSupplyMaterialReplay(signal());
 const copy=replay.frame(1);copy.leaves[0]!.geometry.value=999;copy.snapshot.state[0]=999;
 expect(replay.frame(1)).toEqual(original(1));expect(replay.frame(0)).toEqual(original(0));
 const summary=replay.summary();summary.effective_rights.display=false;
 expect(replay.summary().effective_rights.display).toBe(true);
 for(const index of [-1,4,0.5,NaN,Infinity,true,'0'])expect(()=>replay.frame(index as number)).toThrow();
},20000);
it('cancels a pending request even when fetch ignores its signal',async()=>{
 let release!:(v:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(resolve=>release=resolve)));
 const request=new SupplyMaterialRequest(),result=request.load().then(()=>false,()=>true);request.cancel();
 release(new Response(bytes('index.json')));expect(await result).toBe(true);
});
it('keeps only the latest request when an old fetch resolves after the new dataset',async()=>{
 let release!:(v:Response)=>void,calls=0;const normal=transport();
 vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL,options?:RequestInit)=>++calls===1?new Promise<Response>(r=>release=r):normal(input,options)));
 const request=new SupplyMaterialRequest(),old=request.load().then(()=>false,()=>true),latest=await request.load();
 release(new Response(bytes('index.json')));expect(await old).toBe(true);expect(latest.frame(1)).toEqual(original(1));
},20000);
it.each([503,404])('rejects HTTP%s without an implicit retry',async status=>{
 const fetch=vi.fn(async()=>new Response('unavailable',{status}));vi.stubGlobal('fetch',fetch);
 await expect(loadSupplyMaterialReplay(signal())).rejects.toThrow();expect(fetch).toHaveBeenCalledTimes(1);
});
it('cancels an oversized streamed response despite a small content-length',async()=>{
 const cancel=vi.fn(),stream=new ReadableStream<Uint8Array>({start(c){c.enqueue(new Uint8Array(2*1024**2));c.enqueue(new Uint8Array(1));},cancel});
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(stream,{headers:{'content-length':'1'}})));
 await expect(loadSupplyMaterialReplay(signal())).rejects.toThrow();expect(cancel).toHaveBeenCalledOnce();expect(stream.locked).toBe(false);
});
it('propagates a stream error and releases its lock',async()=>{
 const stream=new ReadableStream<Uint8Array>({start(c){c.error(Error('fixture stream failure'));}});
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(stream)));
 await expect(loadSupplyMaterialReplay(signal())).rejects.toThrow();expect(stream.locked).toBe(false);
});
