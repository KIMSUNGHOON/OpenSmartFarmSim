import {afterEach,beforeAll,expect,it,vi} from 'vitest';
import {readFileSync} from 'node:fs';
import {loadLeafFundedBirthReplay,isLeafFundedBirthScenario,readFundedLeafReplay,LeafFundedBirthRequest,type FundedLeafAnchor} from './leafFundedBirthReplay';
import {LEAF_FUNDED_BIRTH_FIXTURE as FIXTURE} from './leafFundedBirthReplayFixture';
import {programInfo,frame,sample,balances,list,type ProgramInfo,type Row} from './leafFundedBirthReplaySchema';
import {object} from './storedLeafReplayIO';
import {wireFields,wireHash} from './fundedLeafReplayWire';
import {growingGeometryOffset} from './growingGeometryReplay';

const scenarios=Object.keys(FIXTURE.scenarios).filter(isLeafFundedBirthScenario);
const file=(scenario:string,name:string)=>new Uint8Array(readFileSync(new URL(`../public/leaf-funded-birth-replay/${scenario}/${name}`,import.meta.url)));
function stub(change?:(name:string,raw:Uint8Array)=>Uint8Array){
 vi.stubGlobal('fetch',vi.fn(async(url:string,options:RequestInit)=>{
  const match=/^\.\/leaf-funded-birth-replay\/([^/]+)\/([^/]+)$/.exec(url);expect(match).not.toBeNull();
  expect(options).toMatchObject({cache:'no-store',credentials:'omit',redirect:'error'});
  const raw=file(match![1]!,match![2]!);return new Response(new Uint8Array(change?change(match![2]!,raw):raw));
 }));
}
afterEach(()=>vi.unstubAllGlobals());
it.each(scenarios)('preserves every original frame, variable leaf state, phase and ledger in %s',async scenario=>{
 stub();const replay=await loadLeafFundedBirthReplay(scenario,new AbortController().signal);
 expect(replay.artifact_sha256).toBe(FIXTURE.scenarios[scenario].artifact_sha256);
 expect(replay.frames).toHaveLength(19);expect(fetch).toHaveBeenCalledTimes(54);
 for(let i=0;i<19;i++)expect(replay.frames[i]).toEqual(JSON.parse(new TextDecoder().decode(file(scenario,`frame-${i}.json`))));
 expect(replay.frames[0]!.leaves).toHaveLength(3);expect(replay.frames[5]!.leaves).toHaveLength(4);expect(replay.frames[14]!.leaves).toHaveLength(5);
 expect(replay.frames[4]!.at).toEqual(replay.frames[5]!.at);expect(replay.frames[4]!.phase).toBe('root_interval');expect(replay.frames[5]!.phase).toBe('after_birth');
});
it('rejects unknown scenarios and aborted requests before reading',async()=>{
 stub();const c=new AbortController();c.abort();await expect(loadLeafFundedBirthReplay(scenarios[0]!,c.signal)).rejects.toThrow();
 await expect(loadLeafFundedBirthReplay('unknown',new AbortController().signal)).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
});

const original=(name:string)=>JSON.parse(new TextDecoder().decode(file(scenarios[0]!,name))) as unknown;
const index=object(original('index.json'));
const descriptors=list(index.sources).concat(list(index.events).flatMap(v=>[object(v).point,object(v).context_snapshot]),list(index.checkpoints),list(index.frames));
const wireFiles=['index.json',...descriptors.map(v=>String(object(v).path))];
it.each(wireFiles)('rejects tampered original wire bytes in %s',async name=>{
 stub((path,raw)=>path===name?new TextEncoder().encode('{}'):raw);
 await expect(loadLeafFundedBirthReplay(scenarios[0]!,new AbortController().signal)).rejects.toThrow();
});
function change(document:unknown,path:string[],replacement:unknown){
 let current=document;for(const k of path.slice(0,-1))current=Array.isArray(current)?current[Number(k)]:object(current)[k];
 const k=path.at(-1)!;if(Array.isArray(current))current[Number(k)]=replacement;else object(current)[k]=replacement;
}
let info:ProgramInfo;const stored=object(original('frame-18.json')),cp=object(original('checkpoint-18.json')),root=object(original('root.json'));
const leaves=stored.leaves as Row[],receipts=leaves.map(l=>object(l.creation_receipt)),bases=leaves.map(l=>object(l.creation_basis));
beforeAll(async()=>{info=await programInfo(wireFields(new TextDecoder().decode(file(scenarios[0]!,'context-1.json'))).program!);});
const frameMutations:Array<[string[],unknown]>=[
 [['extra'],1],[['G0_G4'],'approved'],[['phase'],'root_interval'],[['event_sequence'],1],[['step_index'],0],
 [['at','elapsed_seconds_exact','unit'],'day'],[['at','elapsed_seconds_exact','numerator'],'1'],[['source_rights','display'],false],
 [['state_layout','leaf_blocks'],['area']],[['leaf_ids'],[]],[['leaves','0','leaf_id'],'missing'],
 [['leaves','0','area','unit'],'cm2'],[['leaves','0','area','value'],0],[['leaves','0','carbon','value'],-1],
 [['leaves','0','curve_sha256'],'0'.repeat(64)],[['leaves','3','creation_basis','air_temperature_integral'],0],
 [['leaves','3','attachment','status'],'bound'],[['leaves','3','attachment','internode_id'],'other'],
 [['leaves','3','creation_receipt','kind'],'initial'],[['leaves','3','creation_receipt','value','event_id'],'other'],
 [['sample','state'],[]],[['plant','leaf'],{value:1,unit:'mg_CH2O/m2_floor'}],[['cohorts','fruit_number'],[]],
 [['climate','air_temperature','value'],0],[['point_totals','buffer_debit','unit'],'kg'],
 [['segment_integrated_transfers','sensible','value'],1e20],[['global_balance_budgets','vapor','value'],-1],
 [['display_policy','stem_pose_attachment'],'biological_emergence_prediction']
];
it.each(frameMutations)('rejects invalid projection independently of the outer hash at %j',(path,replacement)=>{
 const value=structuredClone(stored);change(value,path,replacement);
 expect(()=>frame(value,cp,object((root.samples as unknown[])[18]),root,FIXTURE.scenarios[scenarios[0]!].artifact_sha256,info,receipts,bases)).toThrow();
});
const sampleMutations:Array<[string[],unknown]>=[
 [['state'],[]],[['state','0'],-1],[['state','107'],-1],[['state','117'],-1],
 [['derived','leaf_carbohydrate','unit'],'kg'],[['curve_residuals','0','unit'],'cm2'],[['elapsed_seconds'],0]
];
it.each(sampleMutations)('rejects invalid original state or units at %j',(path,value)=>{
 const q=structuredClone(cp.last_confirmed);change(q,path,value);expect(()=>sample(q,info,16,2)).toThrow();
});
it.each(['balance_residuals','global_balance_residuals'])('enforces local and lifetime QC in %s',key=>{
 const q=structuredClone(cp);change(q,[key,'carbohydrate','value'],1e20);expect(()=>balances(q,5,key.startsWith('global'))).toThrow();
});
const indexMutations:Array<[string[],unknown]>=[
 [['schema_version'],'old'],[['G0_G4'],'approved'],[['source_rights','redistribute'],false],[['exporter_sha256'],'0'.repeat(64)],
 [['sources','0','path'],'../root.json'],[['frames'],[]],[['events','0','after_frame_index'],6],
 [['checkpoints','5','previous_checkpoint_sha256'],'0'.repeat(64)],[['frames','5','phase'],'root_interval']
];
it.each(indexMutations)('rejects a rehashed index with invalid semantics at %j',async(path,value)=>{
 const q=structuredClone(index);change(q,path,value);const text=JSON.stringify(q);
 const anchor={...FIXTURE.scenarios[scenarios[0]!],index_sha256:await wireHash(text)};
 await expect(readFundedLeafReplay(async name=>name==='index.json'?new TextEncoder().encode(text):file(scenarios[0]!,name),anchor,new AbortController().signal)).rejects.toThrow();
});
it.each(['minimum','maximum','fractional','same-time'])('reads actual backend-generated %s boundary packets',async name=>{
 const read=(path:string)=>new Uint8Array(readFileSync(new URL(`../test-fixtures/leaf-funded-birth-replay/${name}/${path}`,import.meta.url)));
 const anchors=JSON.parse(readFileSync(new URL('../test-fixtures/leaf-funded-birth-replay/anchors.json',import.meta.url),'utf8')) as {scenarios:Record<string,FundedLeafAnchor>};
 const replay=await readFundedLeafReplay(async path=>read(path),anchors.scenarios[name]!,new AbortController().signal);
 expect(replay.frames).toHaveLength(anchors.scenarios[name]!.frames);
 for(let i=0;i<replay.frames.length;i++)expect(replay.frames[i]).toEqual(JSON.parse(new TextDecoder().decode(read(`frame-${i}.json`))));
 if(name==='minimum')expect(replay.frames.map(f=>f.leaves.length)).toEqual([1,2,2]);
 if(name==='maximum')expect(replay.frames.map(f=>f.leaves.length)).toEqual([3,512,512]);
 if(name==='fractional'){expect(replay.frames.at(-1)!.at.elapsed_seconds_exact).toEqual(growingGeometryOffset(1/3,3));expect(replay.frames.at(-1)!.sample.elapsed_seconds).toBe(1);}
 if(name==='same-time'){expect(replay.frames[1]!.at).toEqual(replay.frames[2]!.at);expect(replay.frames[2]!.at).toEqual(replay.frames[3]!.at);expect(replay.frames.slice(1,4).map(f=>f.event_sequence)).toEqual([0,1,2]);}
},30000);
it('never returns the previous request after a newer selection, even when fetch ignores abort',async()=>{
 stub();const normal=fetch;let release:(value:Response)=>void=()=>{};let first=true;
 vi.stubGlobal('fetch',vi.fn((...args:Parameters<typeof fetch>)=>{if(first){first=false;return new Promise<Response>(r=>{release=r;});}return normal(...args);}));
 const session=new LeafFundedBirthRequest(),stale=session.load(scenarios[0]!);void stale.catch(()=>{});
 const current=await session.load(scenarios[1]!);release(new Response(file(scenarios[0]!,'index.json')));
 await expect(stale).rejects.toThrow();expect(current.scenario).toBe(scenarios[1]);
});
it('supports cancellation mid-read and detached results without a shared mutable cache',async()=>{
 const session=new LeafFundedBirthRequest();stub();const a=await session.load(scenarios[0]!);a.frames[0]!.leaves[0]!.area.value=0;
 const b=await session.load(scenarios[0]!);expect(b.frames[0]!.leaves[0]!.area.value).toBeGreaterThan(0);
 const normal=fetch;let calls=0;vi.stubGlobal('fetch',vi.fn(async(...args:Parameters<typeof fetch>)=>{const response=await normal(...args);if(++calls===4)session.cancel();return response;}));
 await expect(session.load(scenarios[0]!)).rejects.toThrow();expect(calls).toBe(4);
});
it('rejects non-OK HTTP, invalid UTF8 and oversized streaming input',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('{}',{status:403})));
 await expect(loadLeafFundedBirthReplay(scenarios[0]!,new AbortController().signal)).rejects.toThrow();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Uint8Array([255,255]))));
 await expect(loadLeafFundedBirthReplay(scenarios[0]!,new AbortController().signal)).rejects.toThrow();
 let cancelled=false;vi.stubGlobal('fetch',vi.fn(async()=>new Response(new ReadableStream({start(c){c.enqueue(new Uint8Array(2*1024**2+1));},cancel(){cancelled=true;}}))));
 await expect(loadLeafFundedBirthReplay(scenarios[0]!,new AbortController().signal)).rejects.toThrow();expect(cancelled).toBe(true);
});
