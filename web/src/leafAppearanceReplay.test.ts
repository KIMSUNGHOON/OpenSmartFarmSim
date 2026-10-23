import {afterEach,describe,it,expect,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {decodeLeafAppearanceFrame,loadLeafAppearanceReplay} from './leafAppearanceReplay';
import {LEAF_APPEARANCE_FIXTURE as FIXTURE} from './leafAppearanceReplayFixture';

const file=(name:string)=>readFileSync(new URL('../public/leaf-appearance-replay/'+name,import.meta.url));
const value=(name:string)=>JSON.parse(file(name).toString());
const names=['index.json','root.json','input.json','preparation.json','generated-input.json','population-root.json','stem-root.json','stem-input.json',
 ...Array.from({length:12},(_,i)=>`frame-${i}.json`)];
afterEach(()=>vi.unstubAllGlobals());

describe('stored policy-derived appearance SDK',()=>{
 it('retains every original field in12 DTOs,47areas,exact births and the new provenance',()=>{
  const index=value('index.json'),root=value('root.json'),population=value('population-root.json');const counts=[];
  for(let i=0;i<12;i++){
   const raw=value(`frame-${i}.json`),frame=decodeLeafAppearanceFrame(raw,index.frames[i],root,population);
   expect(frame).toEqual(raw);expect(frame.at).toBe(raw.stem.at);counts.push(frame.tracked_leaf_count);
   expect(frame.artifact_sha256).toBe(FIXTURE.artifact_sha256);expect(frame.population_artifact_sha256).toBe(FIXTURE.population_artifact_sha256);
  }
  expect(counts).toEqual([3,3,3,4,4,4,4,4,4,4,5,5]);expect(counts.reduce((a,b)=>a+b,0)).toBe(47);
  const last=decodeLeafAppearanceFrame(value('frame-11.json'),index.frames[11],root,population);
  expect(last.leaves[3]!.emerged_elapsed_seconds_exact).toEqual({numerator:'432000',denominator:'17',unit:'s'});
  expect(last.leaves[4]!.emerged_elapsed_seconds_exact).toEqual({numerator:'1296000',denominator:'17',unit:'s'});
 });

 it.each(['unit','ID','attachment','age','birth','curve','negative','at','scope','binding','count','missing','future',
  'outer-root','inner-root','source','preparation','policy','profile','display','extra','bool-index','descriptor','state-chain','code','rights'])('rejects %s mixing',kind=>{
  const index=value('index.json'),root=value('root.json'),population=value('population-root.json'),i=kind==='future'?0:11;
  const raw=value(`frame-${i}.json`),descriptor=index.frames[i];
  if(kind==='unit')raw.leaves[0].area.unit='cm2';
  if(kind==='ID')raw.leaves[0].leaf_id='unknown';
  if(kind==='attachment')raw.leaves[0].attachment_internode_id='unknown';
  if(kind==='age')raw.leaves[0].age_exact={numerator:'2',denominator:'2',unit:'degC_day'};
  if(kind==='birth')raw.leaves.at(-1).emerged_elapsed_seconds_exact={numerator:'0',denominator:'1',unit:'s'};
  if(kind==='curve')raw.leaves[0].curve_sha256='0'.repeat(64);
  if(kind==='negative')raw.leaves[0].area.value=-1;
  if(kind==='at')raw.at='2026-10-03T00:00:00Z';
  if(kind==='scope')raw.gates='passed';
  if(kind==='binding')raw.binding_sha256='0'.repeat(64);
  if(kind==='count')raw.tracked_leaf_count+=1;
  if(kind==='missing'){raw.leaves.pop();raw.tracked_leaf_count-=1;}
  if(kind==='future'){raw.leaves.push(value('frame-11.json').leaves.at(-1));raw.tracked_leaf_count+=1;}
  if(kind==='outer-root')raw.artifact_sha256='0'.repeat(64);
  if(kind==='inner-root')raw.population_artifact_sha256='0'.repeat(64);
  if(kind==='source')raw.source_program_sha256='0'.repeat(64);
  if(kind==='preparation')raw.preparation_sha256='0'.repeat(64);
  if(kind==='policy')raw.policy_sha256='0'.repeat(64);
  if(kind==='profile')raw.leaf_profile_sha256='0'.repeat(64);
  if(kind==='display')raw.display_policy.leaf_count='predicted';
  if(kind==='extra')raw.yield_kg=100;
  if(kind==='bool-index')raw.index=true;
  if(kind==='descriptor')descriptor.stem_result_sha256='0'.repeat(64);
  if(kind==='state-chain')population.samples[1].input_state_sha256='0'.repeat(64);
  if(kind==='code')root.code_sha256[Object.keys(root.code_sha256)[0]!]='0'.repeat(64);
  if(kind==='rights')root.program_rights.display=1;
  expect(()=>decodeLeafAppearanceFrame(raw,descriptor,root,population)).toThrow();
 });

 it('loads exactly20 checked files and returns original12 frames and source policy',async()=>{
  const fetcher=vi.fn(async(input:RequestInfo|URL,options?:RequestInit)=>{
   expect(options).toEqual(expect.objectContaining({cache:'no-store',redirect:'error',credentials:'omit',signal:expect.any(AbortSignal)}));
   expect(options?.method??'GET').toBe('GET');return new Response(new Uint8Array(file(String(input).split('/').at(-1)!)));
  });
  vi.stubGlobal('fetch',fetcher);const data=await loadLeafAppearanceReplay(new AbortController().signal);
  expect(data.artifact_sha256).toBe(FIXTURE.artifact_sha256);expect(data.policy).toEqual(FIXTURE.policy);
  expect(data.frames).toEqual(Array.from({length:12},(_,i)=>value(`frame-${i}.json`)));
  expect(fetcher).toHaveBeenCalledTimes(20);
  expect(fetcher.mock.calls.map(([url])=>String(url).split('/').at(-1)).sort()).toEqual([...names].sort());
  expect(fetcher.mock.calls.every(([url])=>String(url).startsWith('./leaf-appearance-replay/'))).toBe(true);
 });

 it.each(names)('rejects changed bytes in %s without replacement frames',async name=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const current=String(input).split('/').at(-1)!;
   return new Response(new Uint8Array(current===name?Buffer.concat([file(current),Buffer.from(' ')]):file(current)));});
  await expect(loadLeafAppearanceReplay(new AbortController().signal)).rejects.toThrow();
 });

 it('rejects a changed positive area even when its format remains valid',async()=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const name=String(input).split('/').at(-1)!;
   const raw=value(name);if(name==='frame-8.json')raw.leaves[0].area.value*=1.1;
   return new Response(new Uint8Array(name==='frame-8.json'?Buffer.from(JSON.stringify(raw)):file(name)));});
  await expect(loadLeafAppearanceReplay(new AbortController().signal)).rejects.toThrow();
 });

 it('rejects missing files without a fallback',async()=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const name=String(input).split('/').at(-1)!;
   return name==='preparation.json'?new Response(null,{status:404}):new Response(new Uint8Array(file(name)));});
  await expect(loadLeafAppearanceReplay(new AbortController().signal)).rejects.toThrow();
 });

 it('rejects an already aborted request without GETs',async()=>{
  const controller=new AbortController();controller.abort();const fetcher=vi.fn();vi.stubGlobal('fetch',fetcher);
  await expect(loadLeafAppearanceReplay(controller.signal)).rejects.toThrow();expect(fetcher).not.toHaveBeenCalled();
 });

 it('rejects an abort after the final response instead of returning frames',async()=>{
  const controller=new AbortController();let calls=0;
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{calls++;if(calls===20)controller.abort();
   return new Response(new Uint8Array(file(String(input).split('/').at(-1)!)));});
  await expect(loadLeafAppearanceReplay(controller.signal)).rejects.toThrow();expect(calls).toBe(20);
 });

 it('cancels an oversized stream at2MiB',async()=>{
  const cancel=vi.fn();vi.stubGlobal('fetch',async()=>new Response(new ReadableStream({
   start(controller){controller.enqueue(new Uint8Array(2*1024**2+1));},cancel,
  })));
  await expect(loadLeafAppearanceReplay(new AbortController().signal)).rejects.toThrow();expect(cancel).toHaveBeenCalledOnce();
 });
});
