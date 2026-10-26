import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {COMPLETE_CROP_FIXTURE as FIXTURE} from './completeCropReplayFixture';
import {checkedFrame,contextLinks} from './completeCropReplaySchema';
import {programInfo,list,type ProgramInfo} from './leafFundedBirthReplaySchema';
import {object} from './storedLeafReplayIO';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
const read=(scenario:string,name:string)=>readFileSync(new URL(`../public/complete-crop-replay/${scenario}/${name}`,import.meta.url),'utf8');

async function prepared(scenario:string){
 const index=JSON.parse(read(scenario,'index.json')),root=JSON.parse(read(scenario,index.root.path));
 const blobs=new Map<string,string>(index.blobs.map((d:{sha256:string;path:string})=>[d.sha256,read(scenario,d.path)]));
 const packet=JSON.parse(blobs.get(index.packet.sha256)!),programs=new Map<string,ProgramInfo>();
 for(const raw of blobs.values()){
  if(!raw.startsWith('{'))continue;const value=object(JSON.parse(raw));
  if(value.origin==='synthetic'&&Array.isArray(value.leaves)&&value.scenario)programs.set(await wireHash(raw),await programInfo(raw));
  if(value.program&&object(value.program).leaves){const p=wireFields(raw).program!;programs.set(await wireHash(p),await programInfo(p));}
 }
 return {packet,root,programs};
}
it.each(Object.keys(FIXTURE.scenarios))('preserves stored vectors and organ inventory in %s',async scenario=>{
 const {packet,programs}=await prepared(scenario);let scalar=0;
 for(const [index,value]of list(packet.frames).entries()){
  const raw=object(value),info=programs.get(String(raw.program_sha256));expect(info).toBeDefined();const result=checkedFrame(raw,info!,index),n=result.leaves.length;
  expect(result.raw).toEqual(raw);const y=list(result.snapshot.state);scalar+=y.length+2*n+8;
  result.leaves.forEach((leaf,j)=>expect([leaf.thermal_age.value,leaf.area.value,leaf.carbohydrate.value]).toEqual([y[107+j],y[107+n+j],y[107+2*n+j]]));
 }
 expect(scalar).toBe(packet.sample_scalars);
});
it('rejects invalid state, units, parents and counters independently of outer hashes',async()=>{
 const {packet,programs}=await prepared('initial-0'),raw=object(packet.frames.at(-1)),info=programs.get(String(raw.program_sha256))!;
 const bad=[(f:Record<string,unknown>)=>f.output_cursor=true,
  (f:Record<string,unknown>)=>object(object(f.evidence).checkpoint).event_sequence=true,
  (f:Record<string,unknown>)=>object(list(f.leaves)[0]).attachment_internode_id='missing',
  (f:Record<string,unknown>)=>object(f.tracked_leaf_area).unit='cm2',
  (f:Record<string,unknown>)=>object(object(object(f.evidence).checkpoint).last_confirmed).state=[],
  (f:Record<string,unknown>)=>object(object(object(f.evidence).checkpoint).global_balance_budgets).vapor={value:-1,unit:'kg_water/m2_floor'}];
 for(const change of bad){const f=structuredClone(raw);change(f);expect(()=>checkedFrame(f,info,packet.frames.length-1)).toThrow();}
});

it('ties the exact context seed/program/input bytes to their recorded identities',async()=>{
 const index=JSON.parse(read('initial-0','index.json')),root=JSON.parse(read('initial-0',index.root.path));
 const path=index.blobs.find((d:{sha256:string})=>d.sha256===root.contexts[0].sha256).path,raw=read('initial-0',path);
 await expect(contextLinks(raw)).resolves.toBeUndefined();
 for(const key of ['after_sample_sha256','after_program_sha256','input_sha256']){
  const fields=wireFields(raw),records=wireItems(fields.records!),row=wireFields(records.at(-1)!);row[key]=JSON.stringify('0'.repeat(64));
  records[records.length-1]='{'+Object.keys(row).sort().map(k=>JSON.stringify(k)+':'+row[k]).join(',')+'}';fields.records='['+records.join(',')+']';
  const changed='{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+fields[k]).join(',')+'}';await expect(contextLinks(changed)).rejects.toThrow();
 }
});
