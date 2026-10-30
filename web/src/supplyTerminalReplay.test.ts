import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {object} from './storedLeafReplayIO';
import {list} from './supplyMorphologyGraphValues';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {readSupplyTerminalReplay,loadSupplyTerminalReplay,SupplyTerminalRequest} from './supplyTerminalReplay';

const file=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url)));
const original=(index:number)=>object(JSON.parse(new TextDecoder().decode(file(`frame-${index}.json`)))).frame;
const gold=object(JSON.parse(readFileSync(new URL('../../research/fixtures/supply-terminal-window-own-20261031.json',import.meta.url),'utf8')));
const reference=object(gold.result),windows=list(gold.windows),names:string[]=[];
const replay=await readSupplyTerminalReplay(async name=>{names.push(name);return file(name);},F.anchor,new AbortController().signal);
afterEach(()=>vi.unstubAllGlobals());

function equalReference(actual:unknown,expected:unknown){
 const r=object(expected),{schema_version,code_sha256,...body}=r;
 expect(actual).toEqual({...body,schema_version:'supply-terminal-browser-window-v1',
  backend_reference:{schema_version,code_sha256}});
}
it('reuses exactly101original files and binds all38 morphology and terminal quantity frames',()=>{
 expect(names).toHaveLength(101);expect(new Set(names).size).toBe(101);
 equalReference(replay.window(),reference);
 for(let i=0;i<38;i++){
  expect(replay.frame(i).morphology).toEqual(original(i));
  expect(replay.frame(i).quantities).toEqual(list(reference.frames)[i]);
 }
 expect(replay.summary()).toMatchObject({frames:38,sample_scalars:6208,
  artifact_sha256:F.anchor.artifact_sha256,index_sha256:F.anchor.index_sha256,
  claim_scope:'synthetic_terminal_quantities_only',G0_G4:'not_assessed',R2:'not_approved',
  terminal:{status:'completed',hold:null}});
});
it.each(windows.map((w,i)=>({w,i})))('matches backend first/last/single/partial window $i',({w})=>{
 const select=object(object(w).window);
 equalReference(Reflect.apply(replay.window,undefined,[select.first_frame,select.last_frame]),w);
});
it('rejects malformed original indices and never returns a partial selection',()=>{
 for(const args of [[true],[-1],[38],[null],['0'],[0,false],[0,38],[0,1.1],[8,7]])
  expect(()=>Reflect.apply(replay.window,undefined,args)).toThrow();
 for(const value of [true,-1,38,0.5,NaN,Infinity,'0',null])
  expect(()=>Reflect.apply(replay.frame,undefined,[value])).toThrow();
});
it('returns defensive copies of morphology, quantities, source and totals',()=>{
 const window=replay.window(),frame=replay.frame(0),summary=replay.summary();
 window.frames[0]!.fruit_carbohydrate.values[0]=999;
 window.totals.terminal_number_exact.numerator='999';
 frame.quantities.terminal_number_exact.numerator='999';
 frame.morphology.snapshot.state[0]=999;
 object(summary.source_rights).crop=false;
 equalReference(replay.window(),reference);
 expect(replay.frame(0).morphology).toEqual(original(0));
 expect(object(replay.summary().source_rights).crop).not.toBe(false);
});
it('does not cache a prior successful source validation across new reads',async()=>{
 let reads=0;
 await expect(readSupplyTerminalReplay(async name=>{reads++;const bytes=file(name);bytes[0]=0;return bytes;},F.anchor,new AbortController().signal)).rejects.toThrow();
 expect(reads).toBe(1);
 equalReference(replay.window(),reference);
});
it('rejects abort before the first file and at the last original file without a partial replay',async()=>{
 const first=new AbortController();first.abort();let count=0;
 await expect(readSupplyTerminalReplay(async name=>{count++;return file(name);},F.anchor,first.signal)).rejects.toThrow();expect(count).toBe(0);
 const last=new AbortController();
 await expect(readSupplyTerminalReplay(async name=>{if(name==='frame-37.json')last.abort();return file(name);},F.anchor,last.signal)).rejects.toThrow();
});
function originalFetch(){return vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
 expect(String(input)).toMatch(/^\.\/supply-morphology-replay\/own-public-v1\/(?:index\.json|root\.json|NOTICE\.txt|blob-[a-f0-9]{64}\.json|frame-\d+\.json)$/);
 expect(options).toMatchObject({cache:'no-store',redirect:'error',credentials:'omit'});
 return new Response(file(String(input).split('/').at(-1)!));
});}
it('loads a single original HTTP bundle with the bounded existing transport',async()=>{
 const fetch=originalFetch();vi.stubGlobal('fetch',fetch);
 const loaded=await loadSupplyTerminalReplay(new AbortController().signal);
 expect(fetch).toHaveBeenCalledTimes(101);equalReference(loaded.window(),reference);
},15000);
it('rejects older responses after the latest load succeeds even when transport ignores abort',async()=>{
 const fetch=originalFetch();let release!:(r:Response)=>void,first:AbortSignal|undefined;
 vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL,options?:RequestInit)=>{
  if(!first){first=options!.signal as AbortSignal;return new Promise<Response>(resolve=>release=resolve);}
  return fetch(input,options);
 }));
 const request=new SupplyTerminalRequest(),older=request.load().then(()=>false,()=>true),latest=await request.load();
 expect(first!.aborted).toBe(true);equalReference(latest.window(),reference);
 release(new Response(file('index.json')));expect(await older).toBe(true);
},15000);
it('cancel invalidates an ignored pending abort and a fresh retry can succeed',async()=>{
 let release!:(r:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(resolve=>release=resolve)));
 const request=new SupplyTerminalRequest(),pending=request.load().then(()=>false,()=>true);
 request.cancel();release(new Response(file('index.json')));expect(await pending).toBe(true);
 vi.stubGlobal('fetch',originalFetch());equalReference((await request.load()).window(),reference);
},15000);
