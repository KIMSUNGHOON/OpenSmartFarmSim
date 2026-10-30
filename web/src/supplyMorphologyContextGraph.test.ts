import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {readSupplyContext,readSupplyCheckpoint} from './supplyMorphologyContextGraph';
import {document,wireObject,counter} from './supplyMorphologyGraphValues';
import {wireFields} from './fundedLeafReplayWire';
const text=(name:string)=>readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url),'utf8');
const index=JSON.parse(text('index.json')),root=JSON.parse(text('root.json'));
const paths=new Map<string,string>(index.blobs.map((d:{sha256:string;path:string})=>[d.sha256,d.path]));
const file=(sha:string)=>text(paths.get(sha)!);
it('checks all six genuine Contexts and 33 original checkpoints including fractional starts',async()=>{
 let count=0;
 for(const s of root.segments){
  const c=await readSupplyContext(file(s.context.sha256),s.context.sha256);let previous;
  for(const d of s.checkpoints){const cp=await readSupplyCheckpoint(file(d.sha256),c,previous);previous=cp;count++;}
 }
 expect(count).toBe(33);
});
const change=(raw:string,key:string,v:unknown)=>wireObject({...wireFields(raw),[key]:JSON.stringify(v)});
it.each([
 ['version','old'],['scope','approved'],['G0_G4','approved'],['branch_steps',true],['grid_index',999],['event_sequence',0],
 ['output_cursor',1],['phase','before_birth'],['seed_checkpoint_sha256','0'.repeat(64)],['point_sha256','0'.repeat(64)],
 ['origin_context_sha256','0'.repeat(64)],['context_sha256','0'.repeat(64)],['output_prefix_sha256','0'.repeat(64)],
 ['output_prefix_link',{}],['redistribution_authorized',false],['extra',0]
] as Array<[string,unknown]>)('rejects a rehashed invalid checkpoint property %s',async(key,v)=>{
 const s=root.segments[0],c=await readSupplyContext(file(s.context.sha256),s.context.sha256);
 await expect(readSupplyCheckpoint(change(file(s.checkpoints[0].sha256),key,v),c,undefined)).rejects.toThrow();
});
it('rejects omitted or repeated consecutive checkpoints',async()=>{
 const s=root.segments[0],c=await readSupplyContext(file(s.context.sha256),s.context.sha256),first=await readSupplyCheckpoint(file(s.checkpoints[0].sha256),c,undefined);
 await expect(readSupplyCheckpoint(file(s.checkpoints[2].sha256),c,first)).rejects.toThrow();
 await expect(readSupplyCheckpoint(first.raw,c,first)).rejects.toThrow();
});
it.each(['1.0','true','-0','9007199254740992'])('keeps typed lexical protocol counters: %s',raw=>{
 expect(()=>counter(document('{"count":'+raw+'}'),'count')).toThrow();
});
