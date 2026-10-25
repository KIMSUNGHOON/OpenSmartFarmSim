import {afterEach,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadLeafCarbonStockReplay,decodeLeafCarbonStockFrame,isLeafCarbonStockScenario,type LeafCarbonStockScenario} from './leafCarbonStockReplay';
import {growingGeometryOffset} from './growingGeometryReplay';
import {LEAF_CARBON_STOCK_FIXTURE as FIXTURE} from './leafCarbonStockReplayFixture';
import {object,parse,digest,id} from './storedLeafReplayIO';

function array(v:unknown):unknown[]{if(!Array.isArray(v))throw Error('array required');return v;}
const scenarios=Object.keys(FIXTURE.scenarios).filter(isLeafCarbonStockScenario);
const file=(name:string,scenario:LeafCarbonStockScenario='warm-day-individual-stock')=>readFileSync(new URL(`../public/leaf-carbon-stock-replay/${scenario}/${name}`,import.meta.url));
const value=(name:string,scenario:LeafCarbonStockScenario='warm-day-individual-stock')=>parse(new Uint8Array(file(name,scenario)));
const meta=(scenario:LeafCarbonStockScenario='warm-day-individual-stock')=>({artifact_sha256:FIXTURE.scenarios[scenario].artifact_sha256,
 root:value('root.json',scenario),context:value('source-context.json',scenario),program:value('source-program.json',scenario),seed:value('source-seed.json',scenario),inputs:value('source-inputs.json',scenario),request:value('source-request.json',scenario),curveHashes:FIXTURE.scenarios[scenario].leaf_curve_sha256});
const decode=(i=16,scenario:LeafCarbonStockScenario='warm-day-individual-stock')=>decodeLeafCarbonStockFrame(value(`frame-${i}.json`,scenario),value(`checkpoint-${i}.json`,scenario),array(object(value('index.json',scenario)).frames)[i],meta(scenario));
function stub(change?:(name:string,raw:Uint8Array)=>Uint8Array){
 return vi.stubGlobal('fetch',vi.fn(async(url:string,options:RequestInit)=>{
  const match=/^\.\/leaf-carbon-stock-replay\/([^/]+)\/([^/]+)$/.exec(url);expect(match).not.toBeNull();
  expect(options).toMatchObject({cache:'no-store',credentials:'omit',redirect:'error'});
  if(!match||!isLeafCarbonStockScenario(match[1])||!match[2])throw Error('unexpected fixture path');
  const name=match[2],raw=file(name,match[1]);
  return new Response(new Uint8Array(change?change(name,raw):raw),{status:200});
 }));
}
afterEach(()=>vi.unstubAllGlobals());

it.each(scenarios)('preserves all original states/leaves/ledgers/bytes for %s',async scenario=>{
 stub();const replay=await loadLeafCarbonStockReplay(scenario,new AbortController().signal);
 expect(replay.scenario).toBe(scenario);expect(replay.artifact_sha256).toBe(FIXTURE.scenarios[scenario].artifact_sha256);
 expect(replay.frames).toHaveLength(17);expect(fetch).toHaveBeenCalledTimes(46);
 for(let i=0;i<17;i++){
  expect(replay.frames[i]).toEqual(value(`frame-${i}.json`,scenario));expect(decode(i,scenario)).toEqual(replay.frames[i]);
  expect(replay.frames[i]!.sample.state).toHaveLength(116);expect(Object.keys(replay.frames[i]!.integrated_transfers)).toHaveLength(30);
 }
});

it.each(['index.json','root.json','NOTICE.txt',...['inputs','request','program','context','seed','growth_profile','cohort_profile','transport_profile','exchange_profile'].map(k=>`source-${k}.json`),...Array.from({length:17},(_,i)=>`checkpoint-${i}.json`),...Array.from({length:17},(_,i)=>`frame-${i}.json`)])(
 'rejects changed original wire file %s',async name=>{
 stub((path,raw)=>path===name?new TextEncoder().encode('{}'):raw);
 await expect(loadLeafCarbonStockReplay('warm-day-individual-stock',new AbortController().signal)).rejects.toThrow();
});

const mutations:Array<[string[],unknown]>=[
 [['extra'],1],[['G0_G4'],'approved'],[['leaves','0','area','unit'],'cm2'],[['leaves','0','area','value'],0],
 [['leaves','0','leaf_id'],'different'],[['leaves'],[]],[['leaves','0','thermal_age','value'],0],
 [['at','elapsed_seconds_exact','denominator'],'2'],[['elapsed_seconds'],1],[['source_rights','display'],false],
 [['sample','state'],[]],[['plant','buffer','unit'],'kg'],[['cohorts','fruit_number'],[]],
 [['climate','air_temperature','value'],0],[['integrated_transfers','sensible','unit'],'W/m2_floor'],
 [['leaves','0','carbon','value'],-1],[['leaves','0','carbon','unit'],'mg_CH2O'],
 [['leaves','0','curve_sha256'],'0'.repeat(64)],[['leaves','0','initial_area_receipt','leaf_id'],'other'],
 [['integrated_transfers','leaf_0_inflow','unit'],'mg_CH2O'],[['balance_residuals','leaf_carbon_0','value'],1e20],
 [['balance_budgets','vapor','value'],-1],[['display_policy','geometry_authority'],'SLA']
];
function setPath(document:unknown,path:string[],replacement:unknown){
 let current=document;for(const key of path.slice(0,-1))current=Array.isArray(current)?current[Number(key)]:object(current)[key];
 const key=path.at(-1)!;if(Array.isArray(current))current[Number(key)]=replacement;else object(current)[key]=replacement;
}
it.each(mutations)('rejects invalid frame projection at %j without trusting its outer hash',(path,replacement)=>{
 const f=value('frame-16.json');setPath(f,path,replacement);expect(()=>decodeLeafCarbonStockFrame(f,value('checkpoint-16.json'),array(object(value('index.json')).frames)[16],meta())).toThrow();
});

it('preserves exact binary64 grid rather than the rounded elapsed product',()=>{
 expect(growingGeometryOffset(1/3,3)).toEqual({numerator:'18014398509481983',denominator:'18014398509481984',unit:'s'});
 expect(growingGeometryOffset(2,0)).toEqual({numerator:'0',denominator:'1',unit:'s'});
});
it('returns detached copies',()=>{
 const original=value('frame-16.json'),snapshot=structuredClone(original),decoded=decodeLeafCarbonStockFrame(original,value('checkpoint-16.json'),array(object(value('index.json')).frames)[16],meta());
 decoded.leaves[0]!.area.value=0;decoded.leaves[0]!.carbon.value=-1;expect(original).toEqual(snapshot);
});
it('aborts before fetching and rejects non-OK or oversized input',async()=>{
 stub();const c=new AbortController();c.abort();await expect(loadLeafCarbonStockReplay('warm-day-individual-stock',c.signal)).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:403})));
 await expect(loadLeafCarbonStockReplay('warm-day-individual-stock',new AbortController().signal)).rejects.toThrow();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Uint8Array(2*1024**2+1))));
 await expect(loadLeafCarbonStockReplay('warm-day-individual-stock',new AbortController().signal)).rejects.toThrow();
});


const sourceMutations:Array<[string[],unknown]>=[
 [['inputs','schema_version'],'other'],[['inputs','rights','redistribute'],false],
 [['context','identity','engine_version'],'other'],[['context','identity','profile_sha256','growth'],'0'.repeat(64)],
 [['context','state_layout','leaf_blocks'],['thermal_age','area']],[['context','flux_units','leaf_0_inflow'],'kg'],
 [['context','numerical','step_seconds'],0],[['context','numerical','duration_seconds'],999],
 [['context','numerical','sample_scalar_budget'],999999],[['context','extra'],1],
 [['program','scenario','plant_state','leaf'],{value:50000,unit:'mg_CH2O/m2_floor'}],
 [['program','scenario','removals','leaf'],{value:0,unit:'mg_CH2O/m2_floor/s'}],
 [['seed','initial_area_receipts','0','leaf_id'],'other'],[['seed','state'],[]],
 [['seed','evaluation','stock_rhs','leaf_totals','carbon','unit'],'kg'],
 [['root','sources','license_notice','sha256'],'0'.repeat(64)],
 [['root','code_sha256','backend/app/crop_leaf_carbon_stock_rhs.py'],'0'.repeat(64)]
];
it.each(sourceMutations)('rejects changed source context at %j',(path,replacement)=>{
 const m=structuredClone(meta());setPath(m,path,replacement);
 expect(()=>decodeLeafCarbonStockFrame(value('frame-16.json'),value('checkpoint-16.json'),array(object(value('index.json')).frames)[16],m)).toThrow();
});

it('aborts mid load and rejects unknown scenarios',async()=>{
 const c=new AbortController();stub();const original=fetch;let calls=0;
 vi.stubGlobal('fetch',vi.fn(async(...args:Parameters<typeof fetch>)=>{const response=await original(...args);if(++calls===4)c.abort();return response;}));
 await expect(loadLeafCarbonStockReplay('warm-day-individual-stock',c.signal)).rejects.toThrow();expect(calls).toBe(4);
 await expect(loadLeafCarbonStockReplay('unknown',new AbortController().signal)).rejects.toThrow();
});

function boundary(name:string){
 const read=(file:string)=>parse(new Uint8Array(readFileSync(new URL(`../test-fixtures/leaf-carbon-stock-replay/${name}/${file}`,import.meta.url))));
 const index=read('index.json'),last=array(object(index).frames).length-1,frame=read(`frame-${last}.json`);
 const pairs:[string,string][]=array(object(frame).leaves).map(v=>{const q=object(v);id(q.leaf_id);digest(q.curve_sha256);return[q.leaf_id,q.curve_sha256];});
 return {frame,checkpoint:read(`checkpoint-${last}.json`),descriptor:array(object(index).frames)[last],meta:{
  artifact_sha256:String(object(index).artifact_sha256),root:read('root.json'),program:read('source-program.json'),
  seed:read('source-seed.json'),context:read('source-context.json'),inputs:read('source-inputs.json'),request:read('source-request.json'),curveHashes:Object.fromEntries(pairs)}};
}
it.each([1,512])('decodes actual backend stored boundary of %i leaves',n=>{
 const b=boundary(`stock-boundary-${n}`),f=decodeLeafCarbonStockFrame(b.frame,b.checkpoint,b.descriptor,b.meta);
 expect(f.sample.state).toHaveLength(107+3*n);expect(f.leaves).toHaveLength(n);expect(Object.keys(f.integrated_transfers)).toHaveLength(21+3*n);
 for(let i=0;i<n;i++)expect(f.leaves[i]!.carbon).toEqual({value:f.sample.state[107+2*n+i],unit:'mg_CH2O/m2_floor'});
});
it('decodes original fractional stored frame without rounding its exact coordinate',()=>{
 const b=boundary('stock-boundary-fractional'),f=decodeLeafCarbonStockFrame(b.frame,b.checkpoint,b.descriptor,b.meta);
 expect(f.at.elapsed_seconds_exact).toEqual(growingGeometryOffset(1/3,3));expect(f.elapsed_seconds).toBe(1);
});
