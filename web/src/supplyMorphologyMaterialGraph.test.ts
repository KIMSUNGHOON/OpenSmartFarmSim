import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {readSupplyMaterial} from './supplyMorphologyMaterialGraph';
import {readSupplyContext} from './supplyMorphologyContextGraph';
import {document,wireObject} from './supplyMorphologyGraphValues';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
const text=(name:string)=>readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url),'utf8');
const index=JSON.parse(text('index.json')),root=JSON.parse(text('root.json'));
const paths=new Map<string,string>(index.blobs.map((d:{sha256:string;path:string})=>[d.sha256,d.path]));
const file=(sha:string)=>text(paths.get(sha)!);
it('links all five authentic material receipts to the original preceding Context and CP',async()=>{
 for(let i=1;i<root.segments.length;i++){
  const a=root.segments[i-1],b=root.segments[i];
  const old=await readSupplyContext(file(a.context.sha256),a.context.sha256),next=await readSupplyContext(file(b.context.sha256),b.context.sha256);
  const cp=document(file(a.checkpoints.at(-1).sha256)),m=await readSupplyMaterial(old,next,cp);
  expect(await wireHash(m.receipt.raw)).toBe(next.descriptor.value.point_sha256);
  expect(m.before.value.source_prefix).toEqual(cp.value);
  expect(m.afterSnapshotRaw).toBe(next.seed.fields.initial_sample);
 }
});
function alter(raw:string,path:string[],replacement:unknown):string{
 if(!path.length)return JSON.stringify(replacement);
 const key=path[0]!,tail=path.slice(1);
 if(raw[0]==='['){const items=wireItems(raw);items[Number(key)]=alter(items[Number(key)]!,tail,replacement);return '['+items.join(',')+']';}
 const fields=wireFields(raw);fields[key]=alter(fields[key]??'null',tail,replacement);return wireObject(fields);
}
it.each([
 [['program','input_id'],'different-program'],[['costs','extra'],1],
 [['source_output_prefix_sha256'],'0'.repeat(64)],[['before_material_prefix_sha256'],'0'.repeat(64)],
 [['output_prefix_sha256'],'0'.repeat(64)],[['schedule','next_sequence'],999],
 [['initial_sample','derived','canopy_temperature','value'],99],
 [['geometry_baselines','leaves','0','origin_geometry','value'],1]
] as Array<[string[],unknown]>)('rejects independently rehashed after-material metadata %j',async(path,value)=>{
 const a=root.segments[0],b=root.segments[1],old=await readSupplyContext(file(a.context.sha256),a.context.sha256);
 const changed=alter(file(b.context.sha256),['descriptor','seed',...path],value),next=await readSupplyContext(changed,await wireHash(changed));
 await expect(readSupplyMaterial(old,next,document(file(a.checkpoints.at(-1).sha256)))).rejects.toThrow();
});
it('rejects a genuine but stale source checkpoint',async()=>{
 const a=root.segments[0],b=root.segments[1],old=await readSupplyContext(file(a.context.sha256),a.context.sha256),next=await readSupplyContext(file(b.context.sha256),b.context.sha256);
 await expect(readSupplyMaterial(old,next,document(file(a.checkpoints[0].sha256)))).rejects.toThrow();
});
