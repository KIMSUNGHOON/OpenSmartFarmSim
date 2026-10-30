import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {readSupplyMorphologySourceGraph} from './supplyMorphologySourceGraph';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {quantityLayout} from './supplyMorphologyQuantityLayout';
import {storedFrameQuantities,floatStateWire,readSupplyMorphologyStoredQuantities} from './supplyMorphologyStoredQuantities';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
const file=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url)));
const graph=()=>readSupplyMorphologySourceGraph(async name=>file(name),F.anchor,new AbortController().signal);
const source=await graph();
const seed=source.contexts[0]!.seed.value,cp=source.contexts[0]!.checkpoints[0]!.value,frame=source.frames[0]!.value.frame;
const evidence={snapshot:cp.last_confirmed,lifetime:cp.lifetime_transfers_exact,geometry:cp.geometry_diagnostics,global:cp.global_ledgers};
it('validates all38 original frames/6208 coordinates and preserves every projected value',async()=>{
 const names:string[]=[];
 const q=await readSupplyMorphologyStoredQuantities(async name=>{names.push(name);return file(name);},F.anchor,new AbortController().signal);
 expect(q.validation_scope).toBe('stored_quantities_http_ui_pending');expect(q.frames).toHaveLength(38);expect(q.sample_scalars).toBe(6208);
 expect(names).toHaveLength(101);expect(new Set(names).size).toBe(101);
 for(const [i,f]of q.frames.entries())expect(f).toEqual(source.frames[i]!.value.frame);
 expect(q.root.value.G0_G4).toBe('not_assessed');expect(q.root.value.R2).toBe('not_approved');
 expect(q.root.value.terminal).toEqual(source.root.value.terminal);
});
it.each(['geometry','carbon','age','clock','birth','origin','metadata','parent','id','layout','floor','derived','vector','negative','account','extra'])('rejects wrong named frame quantity %s independently of hashes',kind=>{
 const f=structuredClone(frame) as any;
 if(kind==='geometry')f.leaves[0].geometry.value+=1;
 if(kind==='carbon')f.internodes[0].carbon.value+=1;
 if(kind==='age')f.leaves[0].represented_age.value+=1;
 if(kind==='clock')f.leaves[0].clock_exact={numerator:'0',denominator:'1',unit:'degC_day'};
 if(kind==='birth')f.leaves[0].birth.carbon.value+=1;
 if(kind==='origin')f.leaves[0].geometry_origin.origin_geometry.value+=1;
 if(kind==='metadata')f.internodes[0].metadata.lineage_kind='invented';
 if(kind==='parent')f.leaves[0].parent_internode_id='invented';
 if(kind==='id')f.leaves[0].id='invented';
 if(kind==='layout')f.state_layout.original_prefix_length++;
 if(kind==='floor')f.model_floor_area.unit='ha';
 if(kind==='derived')f.snapshot.derived.air_capacity.unit='W';
 if(kind==='vector')f.snapshot.state.pop();
 if(kind==='negative')f.leaves[0].geometry.value=-1;
 if(kind==='account')f.global_ledgers.carbohydrate.budget_exact.numerator='-1';
 if(kind==='extra')f.leaves[0].extra=true;
 expect(()=>storedFrameQuantities(quantityLayout(seed),f,evidence)).toThrow();
});
it('rejects source geometry or clock evidence even when the projected row copies the change',()=>{
 const e=structuredClone(evidence) as any,f=structuredClone(frame) as any;
 e.geometry.leaf_0.deficit_exact={numerator:'1',denominator:'1',unit:'m2'};
 f.leaves[0].geometry_diagnostics=e.geometry.leaf_0;
 expect(()=>storedFrameQuantities(quantityLayout(seed),f,e)).toThrow();
 const e2=structuredClone(evidence) as any;
 e2.lifetime.indoor_air_temperature_time={numerator:'-10000000000',denominator:'1',unit:'degC_s'};
 expect(()=>storedFrameQuantities(quantityLayout(seed),frame,e2)).toThrow();
});
it.each(['[1]','[true]','[1e999]','[null]'])('rejects a non-original binary64 vector %s',raw=>expect(()=>floatStateWire(raw)).toThrow());
it('retains Python float tokens including integer-valued doubles and signed zero',()=>expect(floatStateWire('[1.0,-0.0,1e-2]')).toEqual([1,-0,0.01]));
it('honors cancellation before reading any bytes',async()=>{
 const c=new AbortController();c.abort();let calls=0;
 await expect(readSupplyMorphologyStoredQuantities(async name=>{calls++;return file(name);},F.anchor,c.signal)).rejects.toThrow();expect(calls).toBe(0);
});
it('rejects a forged projected area after all surrounding DTO/root/index hashes are recomputed',async()=>{
 const decode=(name:string)=>new TextDecoder().decode(file(name));
 const put=(raw:string,key:string,token:string)=>{
  const fields=wireFields(raw);fields[key]=token;
  return '{'+Object.keys(fields).sort().map(k=>JSON.stringify(k)+':'+fields[k]).join(',')+'}';
 };
 const first=wireFields(decode('frame-0.json')),body=wireFields(first.frame!),leaves=wireItems(body.leaves!);
 const leaf=wireFields(leaves[0]!);leaves[0]=put(leaves[0]!,'geometry',put(leaf.geometry!,'value','12.5'));
 const changed=put(first.frame!,'leaves','['+leaves.join(',')+']'),frameHash=await wireHash(changed);
 const rootFields=wireFields(decode('root.json')),descriptors=wireItems(rootFields.frames!);
 descriptors[0]=put(descriptors[0]!,'frame_sha256',JSON.stringify(frameHash));
 const rootRaw=put(decode('root.json'),'frames','['+descriptors.join(',')+']'),rootHash=await wireHash(rootRaw);
 const index=JSON.parse(decode('index.json')),files=new Map<string,Uint8Array>();
 const bytes=(raw:string)=>new TextEncoder().encode(raw);
 for(let i=0;i<38;i++){
  let dto=decode(`frame-${i}.json`);if(i===0)dto=put(dto,'frame',changed);
  dto=put(dto,'artifact_sha256',JSON.stringify(rootHash));const data=bytes(dto);files.set(`frame-${i}.json`,data);
  Object.assign(index.frames[i],{sha256:await wireHash(dto),bytes:data.byteLength});
  if(i===0)index.frames[i].frame_sha256=frameHash;
 }
 index.artifact_sha256=rootHash;index.root={path:'root.json',sha256:rootHash,bytes:bytes(rootRaw).byteLength};
 const old=index.blobs.findIndex((d:{path:string})=>d.path==='root.json');index.blobs[old]=index.root;
 const indexRaw=JSON.stringify(index),anchor={...F.anchor,artifact_sha256:rootHash,index_sha256:await wireHash(indexRaw)};
 files.set('root.json',bytes(rootRaw));files.set('index.json',bytes(indexRaw));
 const read=async(name:string)=>files.get(name)??file(name);
 expect((await readSupplyMorphologySourceGraph(read,anchor,new AbortController().signal)).validation_scope).toBe('source_graph_only_quantities_pending');
 await expect(readSupplyMorphologyStoredQuantities(read,anchor,new AbortController().signal)).rejects.toThrow();
},15000);
