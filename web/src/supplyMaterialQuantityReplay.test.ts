import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadMaterialQuantityReplay,MaterialQuantityRequest} from './supplyMaterialQuantityReplay';
import {object} from './storedLeafReplayIO';
const read=(kind:'model'|'quantities',name:string)=>new Uint8Array(readFileSync(new URL(`../public/${kind==='model'?'supply-material-replay':'supply-material-quantities'}/own-public-v1/${name}`,import.meta.url)));
const expected=JSON.parse(new TextDecoder().decode(read('quantities','quantities.json'))).result;
const signal=()=>new AbortController().signal;
function transport(){return vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
 const name=String(input);expect(options).toMatchObject({cache:'no-store',credentials:'omit',redirect:'error'});expect(options!.signal).toBeInstanceOf(AbortSignal);
 if(name==='./supply-material-quantities/own-public-v1/quantities.json')return new Response(read('quantities','quantities.json'));
 expect(name).toMatch(/^\.\/supply-material-replay\/own-public-v1\/(?:index\.json|root\.json|NOTICE\.txt|blob-[a-f0-9]{64}\.json|frame-\d+\.json)$/);
 return new Response(read('model',name.split('/').at(-1)!));
});}
afterEach(()=>vi.unstubAllGlobals());
it('reads107 original files and binds every quantity/geometry to the actual4 model states',async()=>{
 const fetch=transport();vi.stubGlobal('fetch',fetch);const data=await loadMaterialQuantityReplay(signal());
 expect(fetch).toHaveBeenCalledTimes(107);expect(data.summary().frames).toBe(4);expect(data.summary().G0_G4).toBe('not_assessed');
 for(let i=0;i<4;i++){
  expect(data.frame(i).morphology).toEqual(JSON.parse(new TextDecoder().decode(read('model',`frame-${i}.json`))).frame);
  expect(data.frame(i).quantities).toEqual(expected.frames[i]);
 }
 for(const [first,last]of [[0,3],[0,1],[1,3],[2,2]] as const){
  const w=data.window(first,last);expect(w.window.first_frame).toBe(first);expect(w.window.last_frame).toBe(last);
  expect(w.frames).toEqual(expected.frames.slice(first,last+1));expect(w.intervals).toEqual(expected.intervals.slice(first,last));
 }
 expect(data.window().totals_exact).toEqual(expected.totals_exact);
},20000);
it('isolates copies and refuses invalid range/frame selectors',async()=>{
 vi.stubGlobal('fetch',transport());const d=await loadMaterialQuantityReplay(signal()),f=d.frame(1),w=d.window();
 f.morphology.leaves[0]!.geometry.value=999;f.quantities.fruit_number.values[0]=999;w.totals_exact.external_vapor!.numerator='999';
 expect(d.frame(1).morphology).toEqual(JSON.parse(new TextDecoder().decode(read('model','frame-1.json'))).frame);
 const summary=d.summary();object(object(summary.source).effective_rights).display=false;
 expect(object(object(d.summary().source).effective_rights).display).toBe(true);
 expect(d.frame(1).quantities).toEqual(expected.frames[1]);expect(d.window().totals_exact).toEqual(expected.totals_exact);
 for(const index of [-1,4,0.5,NaN,Infinity,true,'0'])expect(()=>d.frame(index as number)).toThrow();
 for(const [a,b]of [[-1,3],[0,4],[2,1],[true,3],[0,1.5]])expect(()=>d.window(a as number,b as number)).toThrow();
},20000);
it('refuses cancelled responses even if fetch ignores its signal',async()=>{
 let release!:(r:Response)=>void;vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(r=>release=r)));
 const r=new MaterialQuantityRequest(),old=r.load().then(()=>false,()=>true);r.cancel();release(new Response(read('model','index.json')));expect(await old).toBe(true);
});
it('keeps only the latest complete model-plus-quantity response',async()=>{
 const normal=transport();let release!:(r:Response)=>void,seen!:()=>void;
 const waiting=new Promise<void>(r=>seen=r);let held=false;
 vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL,options?:RequestInit)=>{
  if(String(input).includes('supply-material-quantities/')&&!held){held=true;seen();return new Promise<Response>(r=>release=r);}return normal(input,options);
 }));
 const r=new MaterialQuantityRequest(),old=r.load().then(()=>false,()=>true);await waiting;
 const current=await r.load();release(new Response(read('quantities','quantities.json')));
 expect(await old).toBe(true);expect(current.window().totals_exact).toEqual(expected.totals_exact);
},20000);
it.each([404,503])('refuses quantity HTTP%s after the original model is validated',async status=>{
 const normal=transport(),fetch=vi.fn((input:RequestInfo|URL,options?:RequestInit)=>String(input).includes('supply-material-quantities/')?Promise.resolve(new Response('unavailable',{status})):normal(input,options));
 vi.stubGlobal('fetch',fetch);await expect(loadMaterialQuantityReplay(signal())).rejects.toThrow();expect(fetch).toHaveBeenCalledTimes(107);
},20000);
it('cancels an oversized quantity stream and releases the reader',async()=>{
 const normal=transport(),cancel=vi.fn(),stream=new ReadableStream<Uint8Array>({start(c){c.enqueue(new Uint8Array(2*1024**2));c.enqueue(new Uint8Array(1));},cancel});
 vi.stubGlobal('fetch',vi.fn((input:RequestInfo|URL,options?:RequestInit)=>String(input).includes('supply-material-quantities/')?Promise.resolve(new Response(stream)):normal(input,options)));
 await expect(loadMaterialQuantityReplay(signal())).rejects.toThrow();expect(cancel).toHaveBeenCalledOnce();expect(stream.locked).toBe(false);
},20000);
