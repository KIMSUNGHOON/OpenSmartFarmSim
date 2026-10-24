import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadGrowingGeometryRemovalReplay,decodeGrowingGeometryRemovalFrame,type GrowingGeometryRemovalScenario} from './growingGeometryRemovalReplay';
import {growingGeometryOffset} from './growingGeometryReplay';
import {GROWING_GEOMETRY_REMOVAL_FIXTURE as FIXTURE} from './growingGeometryRemovalReplayFixture';
import {object} from './storedLeafReplayIO';

const scenarios=Object.keys(FIXTURE.scenarios) as GrowingGeometryRemovalScenario[];
const file=(name:string,scenario:GrowingGeometryRemovalScenario='case-0-remove-1')=>readFileSync(new URL(`../public/growing-geometry-removal-replay/${scenario}/${name}`,import.meta.url));
const value=(name:string,scenario:GrowingGeometryRemovalScenario='case-0-remove-1')=>JSON.parse(file(name,scenario).toString());
const meta=(scenario:GrowingGeometryRemovalScenario='case-0-remove-1')=>({artifact_sha256:FIXTURE.scenarios[scenario].artifact_sha256,
 root:value('root.json',scenario),context:value('source-context.json',scenario),program:value('source-program.json',scenario),seed:value('source-seed.json',scenario),postContext:value('source-post_context.json',scenario),postProgram:value('source-post_program.json',scenario),postSeed:value('source-post_seed.json',scenario),point:value('source-point_result.json',scenario),inputs:value('source-inputs.json',scenario),curveHashes:FIXTURE.scenarios[scenario].leaf_curve_sha256});
const decode=(i=17,scenario:GrowingGeometryRemovalScenario='case-0-remove-1')=>decodeGrowingGeometryRemovalFrame(value(`frame-${i}.json`,scenario),value(`checkpoint-${i}.json`,scenario),value('index.json',scenario).frames[i],meta(scenario));
function stub(change?:(name:string,raw:Uint8Array)=>Uint8Array){
 return vi.stubGlobal('fetch',vi.fn(async(url:string,options:RequestInit)=>{
  const match=/^\.\/growing-geometry-removal-replay\/([^/]+)\/([^/]+)$/.exec(url);expect(match).not.toBeNull();
  expect(options).toMatchObject({cache:'no-store',credentials:'omit',redirect:'error'});
  const name=match![2]!,raw=file(name,match![1] as GrowingGeometryRemovalScenario);
  return new Response(new Uint8Array(change?change(name,raw):raw),{status:200});
 }));
}
afterEach(()=>vi.unstubAllGlobals());

it.each(scenarios)('preserves all original states/leaves/ledgers/bytes for %s',async scenario=>{
 stub();const replay=await loadGrowingGeometryRemovalReplay(scenario,new AbortController().signal);
 expect(replay.scenario).toBe(scenario);expect(replay.artifact_sha256).toBe(FIXTURE.scenarios[scenario].artifact_sha256);
 expect(replay.frames).toHaveLength(18);expect(fetch).toHaveBeenCalledTimes(54);
 for(let i=0;i<18;i++){
  expect(replay.frames[i]).toEqual(value(`frame-${i}.json`,scenario));expect(decode(i,scenario)).toEqual(replay.frames[i]);
  const n=i<=7?3:scenario.endsWith('remove-1')?2:1;
  expect(replay.frames[i]!.sample.state).toHaveLength(108+2*n);expect(Object.keys(replay.frames[i]!.original_interval_transfers)).toHaveLength(21);
  expect(replay.frames[i]!.leaf_ids).toEqual(i<=7?['own-leaf-0','own-leaf-1','own-leaf-2']:n===2?['own-leaf-1','own-leaf-2']:['own-leaf-1']);
 }
});

it.each(['index.json','root.json','NOTICE.txt',...['inputs','request','program','context','seed','growth_profile','cohort_profile','transport_profile','exchange_profile','point_inputs','point_result','post_context','post_program','post_seed','post_snapshot'].map(k=>`source-${k}.json`),...Array.from({length:18},(_,i)=>`checkpoint-${i}.json`),...Array.from({length:18},(_,i)=>`frame-${i}.json`)])(
 'rejects changed original wire file %s',async name=>{
 stub((path,raw)=>path===name?new TextEncoder().encode('{}'):raw);
 await expect(loadGrowingGeometryRemovalReplay('case-0-remove-1',new AbortController().signal)).rejects.toThrow();
});

const mutations:Array<[string[],unknown]>=[
 [['extra'],1],[['G0_G4'],'approved'],[['leaves','0','area','unit'],'cm2'],[['leaves','0','area','value'],0],
 [['leaves','0','leaf_id'],'different'],[['leaves'],[]],[['leaves','0','thermal_age','value'],0],
 [['at','elapsed_seconds_exact','denominator'],'2'],[['elapsed_seconds'],1],[['source_rights','display'],false],
 [['sample','state'],[]],[['plant','buffer','unit'],'kg'],[['cohorts','fruit_number'],[]],
 [['climate','air_temperature','value'],0],[['original_interval_transfers','sensible','unit'],'W/m2_floor'],
 [['global_balance_budgets','vapor','value'],-1],[['display_policy','geometry_authority'],'SLA'],[['phase'],'before_removal'],[['global_step_index'],17],
 [['leaves','0','initial_area_receipt','leaf_id'],'own-leaf-0'],[['leaves','0','curve_sha256'],'0'.repeat(64)],
 [['removed_last_states'],[]],[['point_outflows','capacity','unit'],'J/K'],[['segment_integrated_transfers','vapor','value'],0],
 [['original_curve_invariant'],[]],[['active_original_curve_invariant'],[]],[['segment_balance_residuals'],null]
];
function setPath(document:unknown,path:string[],replacement:unknown){
 let current=document;for(const key of path.slice(0,-1))current=Array.isArray(current)?current[Number(key)]:object(current)[key];
 const key=path.at(-1)!;if(Array.isArray(current))current[Number(key)]=replacement;else object(current)[key]=replacement;
}
it.each(mutations)('rejects invalid frame projection at %j without trusting its outer hash',(path,replacement)=>{
 const f=value('frame-17.json');setPath(f,path,replacement);expect(()=>decodeGrowingGeometryRemovalFrame(f,value('checkpoint-17.json'),value('index.json').frames[17],meta())).toThrow();
});

it('preserves exact binary64 grid rather than the rounded elapsed product',()=>{
 expect(growingGeometryOffset(1/3,3)).toEqual({numerator:'18014398509481983',denominator:'18014398509481984',unit:'s'});
 expect(growingGeometryOffset(2,0)).toEqual({numerator:'0',denominator:'1',unit:'s'});
});
it('returns detached copies',()=>{
 const original=value('frame-17.json'),decoded=decodeGrowingGeometryRemovalFrame(original,value('checkpoint-17.json'),value('index.json').frames[17],meta());
 decoded.leaves[0]!.area.value=0;expect(original.leaves[0].area.value).toBeGreaterThan(0);
});
it('aborts before fetching and rejects non-OK or oversized input',async()=>{
 stub();const c=new AbortController();c.abort();await expect(loadGrowingGeometryRemovalReplay('case-0-remove-1',c.signal)).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:403})));
 await expect(loadGrowingGeometryRemovalReplay('case-0-remove-1',new AbortController().signal)).rejects.toThrow();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Uint8Array(2*1024**2+1))));
 await expect(loadGrowingGeometryRemovalReplay('case-0-remove-1',new AbortController().signal)).rejects.toThrow();
});

it.each(scenarios)('keeps two phases at the original event coordinate for %s',scenario=>{
 const before=decode(7,scenario),after=decode(8,scenario);expect(before.at).toEqual(after.at);
 expect(before.global_step_index).toBe(7);expect(after.global_step_index).toBe(7);
 expect(before.phase).toBe('before_removal');expect(after.phase).toBe('after_removal_before_next_step');
 expect(before.point_outflows).toBeNull();expect(before.segment_integrated_transfers).toBeNull();
 expect(before.checkpoint_sha256).not.toBe(after.checkpoint_sha256);expect(after.index).toBe(before.index+1);
});
it('aborts in the middle of a load and rejects an unknown scenario',async()=>{
 const c=new AbortController();stub();const original=fetch;let calls=0;vi.stubGlobal('fetch',vi.fn(async(...args:Parameters<typeof fetch>)=>{
 const response=await original(...args);if(++calls===4)c.abort();return response;}));
 await expect(loadGrowingGeometryRemovalReplay('case-0-remove-1',c.signal)).rejects.toThrow();expect(calls).toBe(4);
 await expect(loadGrowingGeometryRemovalReplay('unknown' as GrowingGeometryRemovalScenario,new AbortController().signal)).rejects.toThrow();
});
