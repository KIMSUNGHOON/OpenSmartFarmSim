import {afterEach,describe,it,expect,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {decodeLeafLifecycleFrame,loadLeafLifecycleReplay,activeLifecycleLeafBinding,type LeafLifecycleScenario} from './leafLifecycleReplay';
import {LEAF_LIFECYCLE_FIXTURE as FIXTURE} from './leafLifecycleReplayFixture';

const scenarios=['no-removal','with-removal'] as const;
const file=(name:string,scenario:LeafLifecycleScenario='with-removal')=>readFileSync(new URL(`../public/leaf-lifecycle-replay/${scenario}/${name}`,import.meta.url));
const value=(name:string,scenario:LeafLifecycleScenario='with-removal')=>JSON.parse(file(name,scenario).toString());
const names=['index.json','root.json','input.json','management.json','preparation.json','initial-state.json','stem-root.json','stem-input.json',
 ...Array.from({length:12},(_,i)=>`frame-${i}.json`)];
const decode=(i=11,scenario:LeafLifecycleScenario='with-removal')=>decodeLeafLifecycleFrame(value(`frame-${i}.json`,scenario),value('index.json',scenario).frames[i],value('root.json',scenario),scenario);
afterEach(()=>vi.unstubAllGlobals());

describe('immutable lifecycle SDK and active renderer binding',()=>{
 it.each(scenarios)('retains original12frames47tracked states and active-only copied geometry for %s',scenario=>{
  let states=0;
  for(let i=0;i<12;i++){
   const original=value(`frame-${i}.json`,scenario),frame=decode(i,scenario),before=structuredClone(frame),binding=activeLifecycleLeafBinding(frame);
   expect(frame).toEqual(original);expect(frame.at).toBe(frame.stem.at);states+=frame.tracked_leaf_count;
   expect(binding).toEqual({artifact_sha256:frame.artifact_sha256,result_sha256:frame.result_sha256,at:frame.at,
    leaves:frame.active_leaves.map(q=>({leaf_id:q.leaf_id,attachment_internode_id:q.attachment_internode_id,area:q.area}))});
   expect(binding.leaves).toHaveLength(frame.active_leaf_count);
   expect(binding.leaves.every(q=>!frame.removed_leaves.some(r=>r.leaf_id===q.leaf_id)&&!frame.pending_leaves.some(r=>r.leaf_id===q.leaf_id))).toBe(true);
   expect(frame).toEqual(before);expect(binding.leaves[0]).not.toBe(frame.active_leaves[0]);expect(binding.leaves[0]!.area).not.toBe(frame.active_leaves[0]!.area);
  }
  expect(states).toBe(47);expect(decode(11,scenario).artifact_sha256).toBe(FIXTURE.scenarios[scenario].artifact_sha256);
 });

 it('keeps removed last clocks/areas separate and pending without current state',()=>{
  const early=decode(0),later=decode(11);
  expect(early.active_leaf_count).toBe(2);expect(early.removed_leaf_count).toBe(1);expect(early.pending_leaf_count).toBe(2);
  expect(later.active_leaf_count).toBe(3);expect(later.removed_leaf_count).toBe(2);expect(later.pending_leaf_count).toBe(0);
  expect(later.removed_leaves[0]!.area).toEqual(early.removed_leaves[0]!.area);
  expect(later.removed_leaves[1]!.last_at_elapsed_seconds_exact).toEqual({numerator:'432000',denominator:'17',unit:'s'});
  expect(later.removed_leaves[1]!.age_exact).toEqual({numerator:'0',denominator:'1',unit:'degC_day'});
  expect(Object.keys(early.pending_leaves[0]!).sort()).toEqual(['attachment_internode_id','emerged_elapsed_seconds_exact','leaf_id']);
 });

 it('pure adapter preserves an empty current list without fallback geometry or input changes',()=>{
  const original=decode(),empty={...original,active_leaves:[],active_leaf_count:0,active_leaf_area:{value:0,unit:'m2' as const}};
  const before=structuredClone(empty);expect(activeLifecycleLeafBinding(empty).leaves).toEqual([]);expect(empty).toEqual(before);
 });

 it.each(['unit','negative','infinite','ID','attachment','curve','birth','age','extra-leaf','missing-active','active-count','removed-count',
  'pending-count','tracked-count','declared-count','birth-count','emerged-count','active-sum','removed-sum','tracked-sum','sum-unit','last-time',
  'last-age-unit','removal-id','removal-time','pending-current','pending-ID','pending-time','future-active','at','exact-now','origin',
  'scope','extra','root','source','management','preparation','display','stem','descriptor','state-chain','code','rights'])('rejects %s drift',kind=>{
  const i=kind.startsWith('pending')||kind==='future-active'?0:11,raw=value(`frame-${i}.json`),index=value('index.json'),root=value('root.json'),d=index.frames[i];
  if(kind==='unit')raw.active_leaves[0].area.unit='cm2';
  if(kind==='negative')raw.active_leaves[0].area.value=-1;
  if(kind==='infinite')raw.active_leaves[0].area.value=Infinity;
  if(kind==='ID')raw.active_leaves[0].leaf_id='unknown';
  if(kind==='attachment')raw.active_leaves[0].attachment_internode_id='unknown';
  if(kind==='curve')raw.active_leaves[0].curve_sha256='0'.repeat(64);
  if(kind==='birth')raw.active_leaves[0].emerged_elapsed_seconds_exact={numerator:'1',denominator:'1',unit:'s'};
  if(kind==='age')raw.active_leaves[0].age_exact={numerator:'2',denominator:'2',unit:'degC_day'};
  if(kind==='extra-leaf')raw.active_leaves[0].yield_kg=100;
  if(kind==='missing-active')raw.active_leaves.pop();
  const counts:Record<string,string>={'active-count':'active_leaf_count','removed-count':'removed_leaf_count','pending-count':'pending_leaf_count','tracked-count':'tracked_leaf_count',
   'declared-count':'declared_leaf_count','birth-count':'scheduled_birth_count','emerged-count':'emerged_new_leaf_count'};
  if(counts[kind])raw[counts[kind]!]+=1;
  const sums:Record<string,string>={'active-sum':'active_leaf_area','removed-sum':'removed_leaf_area','tracked-sum':'last_tracked_leaf_area'};
  if(sums[kind])raw[sums[kind]!].value+=1;
  if(kind==='sum-unit')raw.active_leaf_area.unit='ha';
  if(kind==='last-time')raw.removed_leaves[0].last_at_elapsed_seconds_exact=raw.at_elapsed_seconds_exact;
  if(kind==='last-age-unit')raw.removed_leaves[0].age_exact.unit='day';
  if(kind==='removal-id')raw.removed_leaves[0].removal_declaration.event_id='unknown';
  if(kind==='removal-time')raw.removed_leaves[1].removal_declaration.at_elapsed_seconds_exact={numerator:'0',denominator:'1',unit:'s'};
  if(kind==='pending-current')raw.pending_leaves[0].area={value:1,unit:'m2'};
  if(kind==='pending-ID')raw.pending_leaves[0].leaf_id='unknown';
  if(kind==='pending-time')raw.pending_leaves[0].emerged_elapsed_seconds_exact={numerator:'0',denominator:'1',unit:'s'};
  if(kind==='future-active')raw.active_leaves.push(value('frame-11.json').active_leaves.at(-1));
  if(kind==='at')raw.at='2026-10-03T00:00:00Z';
  if(kind==='exact-now')raw.at_elapsed_seconds_exact={numerator:'0',denominator:'1',unit:'s'};
  if(kind==='origin')raw.time_origin_utc='2026-10-02T00:00:00Z';
  if(kind==='scope')raw.gates='passed';
  if(kind==='extra')raw.harvest_kg=100;
  if(kind==='root')raw.artifact_sha256='0'.repeat(64);
  if(kind==='source')raw.appearance_program_sha256='0'.repeat(64);
  if(kind==='management')raw.management_program_sha256='0'.repeat(64);
  if(kind==='preparation')raw.preparation_sha256='0'.repeat(64);
  if(kind==='display')raw.display_policy.leaf_count='predicted';
  if(kind==='stem')raw.stem.at='2026-10-03T00:00:00Z';
  if(kind==='descriptor')d.input_sha256='0'.repeat(64);
  if(kind==='state-chain')root.samples[1].input_state_sha256='0'.repeat(64);
  if(kind==='code')root.code_sha256[Object.keys(root.code_sha256)[0]!]='0'.repeat(64);
  if(kind==='rights')root.source_rights.management.redistribute=false;
  expect(()=>decodeLeafLifecycleFrame(raw,d,root,'with-removal')).toThrow();
 });

 it.each(scenarios)('loads exactly20 original files for %s without a write request',async scenario=>{
  const requests:string[]=[];
  vi.stubGlobal('fetch',async(input:RequestInfo|URL,options?:RequestInit)=>{
   const url=String(input);requests.push(url);expect(url.startsWith(`./leaf-lifecycle-replay/${scenario}/`)).toBe(true);
   expect(options).toEqual(expect.objectContaining({cache:'no-store',redirect:'error',credentials:'omit',signal:expect.any(AbortSignal)}));
   expect(options?.method??'GET').toBe('GET');return new Response(new Uint8Array(file(url.split('/').at(-1)!,scenario)));
  });
  const replay=await loadLeafLifecycleReplay(scenario,new AbortController().signal);
  expect(replay.frames).toEqual(Array.from({length:12},(_,i)=>value(`frame-${i}.json`,scenario)));
  expect(replay.scenario).toBe(scenario);expect(requests).toHaveLength(20);expect(requests.map(url=>url.split('/').at(-1)).sort()).toEqual([...names].sort());
 });

 it.each(names)('rejects changed bytes in %s without replacement results',async name=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const current=String(input).split('/').at(-1)!;
   return new Response(new Uint8Array(current===name?Buffer.concat([file(current),Buffer.from(' ')]):file(current)));});
  await expect(loadLeafLifecycleReplay('with-removal',new AbortController().signal)).rejects.toThrow();
 });

 it('rejects mixing the no-removal management file into the removal replay',async()=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const name=String(input).split('/').at(-1)!;
   return new Response(new Uint8Array(file(name,name==='management.json'?'no-removal':'with-removal')));});
  await expect(loadLeafLifecycleReplay('with-removal',new AbortController().signal)).rejects.toThrow();
 });

 it('rejects a missing source without a fallback',async()=>{
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{const name=String(input).split('/').at(-1)!;
   return name==='initial-state.json'?new Response(null,{status:404}):new Response(new Uint8Array(file(name)));});
  await expect(loadLeafLifecycleReplay('with-removal',new AbortController().signal)).rejects.toThrow();
 });

 it.each([0,8,20])('rejects abort at request%d without returning partial frames',async point=>{
  const controller=new AbortController();let calls=0;if(point===0)controller.abort();
  vi.stubGlobal('fetch',async(input:RequestInfo|URL)=>{calls++;if(calls===point)controller.abort();return new Response(new Uint8Array(file(String(input).split('/').at(-1)!)));});
  await expect(loadLeafLifecycleReplay('with-removal',controller.signal)).rejects.toThrow();expect(calls).toBe(point);
 });

 it('cancels a stream above2MiB',async()=>{
  const cancel=vi.fn();vi.stubGlobal('fetch',async()=>new Response(new ReadableStream({start(c){c.enqueue(new Uint8Array(2*1024**2+1));},cancel})));
  await expect(loadLeafLifecycleReplay('with-removal',new AbortController().signal)).rejects.toThrow();expect(cancel).toHaveBeenCalledOnce();
 });
});
