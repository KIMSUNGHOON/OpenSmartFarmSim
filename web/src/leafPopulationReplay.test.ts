import {afterEach,describe,it,expect,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {decodeLeafPopulationFrame,loadLeafPopulationReplay} from './leafPopulationReplay';
const file=(name:string)=>readFileSync(new URL('../public/leaf-population-replay/'+name,import.meta.url));
const value=(name:string)=>JSON.parse(file(name).toString());
afterEach(()=>vi.unstubAllGlobals());
describe('stored explicitly declared leaf population',()=>{
 it('retains original twelve UTCs, three-to-six declarations and square metres',()=>{
  const root=value('root.json'),index=value('index.json'),counts=[];
  for(let i=0;i<12;i++){
   const raw=value(`frame-${i}.json`),frame=decodeLeafPopulationFrame(raw,index.frames[i],root);
   expect(frame.leaves).toEqual(raw.leaves);expect(frame.stem).toEqual(raw.stem);expect(frame.at).toBe(raw.stem.at);
   expect(frame.binding_sha256).toBe(index.frames[i].binding_sha256);counts.push(frame.tracked_leaf_count);
  }
  expect(counts).toEqual([3,3,3,4,4,4,4,5,5,5,6,6]);
 });
 it.each(['unit','ID','attachment','age','birth','curve','negative','at','scope','binding','count','missing','future'])('rejects %s mixing',kind=>{
  const index=value('index.json'),root=value('root.json'),i=kind==='future'?0:11,raw=value(`frame-${i}.json`);
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
  expect(()=>decodeLeafPopulationFrame(raw,index.frames[i],root)).toThrow();
 });
 it('loads exactly seventeen checked files using only the stored fixture',async()=>{
  const fetcher=vi.fn(async(input:RequestInfo|URL)=>new Response(new Uint8Array(file(String(input).split('/').at(-1)!))));
  vi.stubGlobal('fetch',fetcher);const data=await loadLeafPopulationReplay(new AbortController().signal);
  expect(data.frames).toHaveLength(12);expect(fetcher).toHaveBeenCalledTimes(17);
  expect(fetcher.mock.calls.every(([url])=>String(url).startsWith('./leaf-population-replay/'))).toBe(true);
 });
 it('rejects changed bytes without replacement frames',async()=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const name=String(input).split('/').at(-1)!;
   return new Response(new Uint8Array(name==='frame-7.json'?Buffer.concat([file(name),Buffer.from(' ')]):file(name)));});
  await expect(loadLeafPopulationReplay(new AbortController().signal)).rejects.toThrow();
 });
});
