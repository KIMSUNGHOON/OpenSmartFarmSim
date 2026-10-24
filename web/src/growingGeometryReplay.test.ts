import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadGrowingGeometryReplay,decodeGrowingGeometryFrame,growingGeometryOffset,type GrowingGeometryScenario} from './growingGeometryReplay';
import {GROWING_GEOMETRY_FIXTURE as FIXTURE} from './growingGeometryReplayFixture';
import {object} from './storedLeafReplayIO';

const scenarios=Object.keys(FIXTURE.scenarios) as GrowingGeometryScenario[];
const file=(name:string,scenario:GrowingGeometryScenario='warm-day')=>readFileSync(new URL(`../public/growing-geometry-replay/${scenario}/${name}`,import.meta.url));
const value=(name:string,scenario:GrowingGeometryScenario='warm-day')=>JSON.parse(file(name,scenario).toString());
const meta=(scenario:GrowingGeometryScenario='warm-day')=>({artifact_sha256:FIXTURE.scenarios[scenario].artifact_sha256,
 root:value('root.json',scenario),context:value('source-context.json',scenario),program:value('source-program.json',scenario),seed:value('source-seed.json',scenario)});
const decode=(i=16,scenario:GrowingGeometryScenario='warm-day')=>decodeGrowingGeometryFrame(value(`frame-${i}.json`,scenario),value(`checkpoint-${i}.json`,scenario),value('index.json',scenario).frames[i],meta(scenario));
function stub(change?:(name:string,raw:Uint8Array)=>Uint8Array){
 return vi.stubGlobal('fetch',vi.fn(async(url:string,options:RequestInit)=>{
  const match=/^\.\/growing-geometry-replay\/([^/]+)\/([^/]+)$/.exec(url);expect(match).not.toBeNull();
  expect(options).toMatchObject({cache:'no-store',credentials:'omit',redirect:'error'});
  const name=match![2]!,raw=file(name,match![1] as GrowingGeometryScenario);
  return new Response(new Uint8Array(change?change(name,raw):raw),{status:200});
 }));
}
afterEach(()=>vi.unstubAllGlobals());

it.each(scenarios)('preserves all original states/leaves/ledgers/bytes for %s',async scenario=>{
 stub();const replay=await loadGrowingGeometryReplay(scenario,new AbortController().signal);
 expect(replay.scenario).toBe(scenario);expect(replay.artifact_sha256).toBe(FIXTURE.scenarios[scenario].artifact_sha256);
 expect(replay.frames).toHaveLength(17);expect(fetch).toHaveBeenCalledTimes(46);
 for(let i=0;i<17;i++){
  expect(replay.frames[i]).toEqual(value(`frame-${i}.json`,scenario));expect(decode(i,scenario)).toEqual(replay.frames[i]);
  expect(replay.frames[i]!.sample.state).toHaveLength(114);expect(Object.keys(replay.frames[i]!.integrated_transfers)).toHaveLength(21);
 }
});

it.each(['index.json','root.json','source-inputs.json','source-program.json','source-context.json','source-seed.json',
 'source-growth_profile.json','source-cohort_profile.json','source-transport_profile.json','source-exchange_profile.json','NOTICE.txt','checkpoint-0.json','checkpoint-16.json','frame-0.json','frame-16.json'])(
 'rejects changed original wire file %s',async name=>{
 stub((path,raw)=>path===name?new TextEncoder().encode('{}'):raw);
 await expect(loadGrowingGeometryReplay('warm-day',new AbortController().signal)).rejects.toThrow();
});

const mutations:Array<[string[],unknown]>=[
 [['extra'],1],[['G0_G4'],'approved'],[['leaves','0','area','unit'],'cm2'],[['leaves','0','area','value'],0],
 [['leaves','0','leaf_id'],'different'],[['leaves'],[]],[['leaves','0','thermal_age','value'],0],
 [['at','elapsed_seconds_exact','denominator'],'2'],[['elapsed_seconds'],1],[['source_rights','display'],false],
 [['sample','state'],[]],[['plant','buffer','unit'],'kg'],[['cohorts','fruit_number'],[]],
 [['climate','air_temperature','value'],0],[['integrated_transfers','sensible','unit'],'W/m2_floor'],
 [['balance_budgets','vapor','value'],-1],[['display_policy','geometry_authority'],'SLA']
];
function setPath(document:unknown,path:string[],replacement:unknown){
 let current=document;for(const key of path.slice(0,-1))current=Array.isArray(current)?current[Number(key)]:object(current)[key];
 const key=path.at(-1)!;if(Array.isArray(current))current[Number(key)]=replacement;else object(current)[key]=replacement;
}
it.each(mutations)('rejects invalid frame projection at %j without trusting its outer hash',(path,replacement)=>{
 const f=value('frame-16.json');setPath(f,path,replacement);expect(()=>decodeGrowingGeometryFrame(f,value('checkpoint-16.json'),value('index.json').frames[16],meta())).toThrow();
});

it('preserves exact binary64 grid rather than the rounded elapsed product',()=>{
 expect(growingGeometryOffset(1/3,3)).toEqual({numerator:'18014398509481983',denominator:'18014398509481984',unit:'s'});
 expect(growingGeometryOffset(2,0)).toEqual({numerator:'0',denominator:'1',unit:'s'});
});
it('returns detached copies',()=>{
 const original=value('frame-16.json'),decoded=decodeGrowingGeometryFrame(original,value('checkpoint-16.json'),value('index.json').frames[16],meta());
 decoded.leaves[0]!.area.value=0;expect(original.leaves[0].area.value).toBeGreaterThan(0);
});
it('aborts before fetching and rejects non-OK or oversized input',async()=>{
 stub();const c=new AbortController();c.abort();await expect(loadGrowingGeometryReplay('warm-day',c.signal)).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:403})));
 await expect(loadGrowingGeometryReplay('warm-day',new AbortController().signal)).rejects.toThrow();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Uint8Array(2*1024**2+1))));
 await expect(loadGrowingGeometryReplay('warm-day',new AbortController().signal)).rejects.toThrow();
});
