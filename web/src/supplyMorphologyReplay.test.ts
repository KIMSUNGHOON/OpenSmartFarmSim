import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadSupplyMorphologyReplay,SupplyMorphologyRequest} from './supplyMorphologyReplay';
const bytes=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url)));
const original=(i:number)=>JSON.parse(new TextDecoder().decode(bytes(`frame-${i}.json`))).frame;
const signal=()=>new AbortController().signal;
afterEach(()=>vi.unstubAllGlobals());
function originalFetch(){return vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
 expect(String(input)).toMatch(/^\.\/supply-morphology-replay\/own-public-v1\/(?:index\.json|root\.json|NOTICE\.txt|blob-[a-f0-9]{64}\.json|frame-\d+\.json)$/);
 expect(options).toMatchObject({cache:'no-store',redirect:'error',credentials:'omit'});expect(options!.signal).toBeInstanceOf(AbortSignal);
 return new Response(bytes(String(input).split('/').at(-1)!));
});}
it('reads original101files and exposes isolated original frame/summary copies',async()=>{
 const fetch=originalFetch();vi.stubGlobal('fetch',fetch);const replay=await loadSupplyMorphologyReplay(signal());
 expect(fetch).toHaveBeenCalledTimes(101);expect(replay.summary().frames).toBe(38);expect(replay.summary().sample_scalars).toBe(6208);
 for(let i=0;i<38;i++)expect(replay.frame(i)).toEqual(original(i));
 const first=replay.frame(0);first.leaves[0]!.geometry.value=999;first.snapshot.state[0]=999;
 expect(replay.frame(0)).toEqual(original(0));expect(replay.frame(1)).toEqual(original(1));
 const summary=replay.summary();(summary.source_rights as any).crop.redistribute=false;
 expect((replay.summary().source_rights as any).crop.redistribute).toBe(true);
 expect(replay.summary().G0_G4).toBe('not_assessed');expect(replay.summary().R2).toBe('not_approved');
 for(const index of [-1,38,0.5,NaN,Infinity,true,'0'])expect(()=>replay.frame(index as number)).toThrow();
},15000);
it.each(['status','empty','wrong_bytes','oversize','stream_error'])('rejects invalid HTTP stream %s',async kind=>{
 let cancelled=0;
 vi.stubGlobal('fetch',vi.fn(async()=>{
  if(kind==='status')return new Response('failure',{status:503});
  if(kind==='empty')return new Response(null,{status:204});
  if(kind==='wrong_bytes')return new Response('{}');
  return new Response(new ReadableStream<Uint8Array>({
   start(c){if(kind==='stream_error')c.error(Error('stream failed'));else{c.enqueue(new Uint8Array(2*1024**2));c.enqueue(new Uint8Array(1));}},
   cancel(){cancelled++;}
  }));
 }));
 await expect(loadSupplyMorphologyReplay(signal())).rejects.toThrow();
 if(kind==='oversize')expect(cancelled).toBe(1);
});
it('refuses cancellation before the first request',async()=>{
 const fetch=originalFetch();vi.stubGlobal('fetch',fetch);const c=new AbortController();c.abort();
 await expect(loadSupplyMorphologyReplay(c.signal)).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
});
it('rejects an older delayed response after the latest original replay completes',async()=>{
 const real=originalFetch();let release!:(value:Response)=>void,firstSignal:AbortSignal|undefined;
 vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL,options?:RequestInit)=>{
  if(!firstSignal){firstSignal=options!.signal as AbortSignal;return new Promise<Response>(resolve=>release=resolve);}
  return real(input,options);
 }));
 const request=new SupplyMorphologyRequest(),old=request.load().then(()=>false,()=>true),latest=await request.load();
 expect(firstSignal!.aborted).toBe(true);expect(latest.frame(37)).toEqual(original(37));
 release(new Response(bytes('index.json')));expect(await old).toBe(true);
},15000);
it('cancel invalidates a pending response even if the transport ignores the signal',async()=>{
 let release!:(value:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(resolve=>release=resolve)));
 const request=new SupplyMorphologyRequest(),pending=request.load().then(()=>false,()=>true);
 request.cancel();release(new Response(bytes('index.json')));expect(await pending).toBe(true);
});
