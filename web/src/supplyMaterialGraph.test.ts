import {expect,it} from 'vitest';
import {readSupplyMaterialFiles} from './supplyMaterialGraph';
import {SUPPLY_MATERIAL_FIXTURE as F} from './supplyMaterialFixture';
import {wireFields,wireHash} from './fundedLeafReplayWire';
import {sha256} from './morphologyReplay';
import {file,text,bytes,alter,repack} from './supplyMaterialTestData';
const signal=()=>new AbortController().signal;
it.each([
 [['extra'],1],[['G0_G4'],'approved'],[['R2'],'approved'],[['schema_version'],'old'],
 [['effective_rights','display'],false],[['effective_rights','redistribute'],false],
 [['code_sha256','backend/app/crop_supply_material_owner.py'],'0'.repeat(64)],
 [['exporter_sha256'],'0'.repeat(64)],[['output_writer_sha256'],'0'.repeat(64)],
 [['blobs','0','path'],'../root.json'],[['blobs','0','bytes'],true],[['blobs','0','bytes'],2*1024**2+1],
 [['sample_scalars'],32769],[['frames','0','index'],true],[['notice','sha256'],'0'.repeat(64)]
 ]as Array<[string[],unknown]>)('rejects rehashed invalid index %j',async(path,value)=>{
 const raw=alter(text('index.json'),path,value),anchor={...F.anchor,index_sha256:await wireHash(raw)};
 await expect(readSupplyMaterialFiles(async name=>name==='index.json'?bytes(raw):file(name),anchor,signal())).rejects.toThrow();
});
it.each(['index.json','root.json','NOTICE.txt','frame-0.json','frame-3.json'])('rejects changed original bytes in %s',async target=>{
 await expect(readSupplyMaterialFiles(async name=>name===target?bytes('{}'):file(name),F.anchor,signal())).rejects.toThrow();
});
it.each(['duplicate','utf8','depth','nonfinite','oversize'])('rejects invalid wire %s',async kind=>{
 const raw=kind==='duplicate'?bytes('{"scope":"software_research_only",'+text('index.json').slice(1)):
  kind==='utf8'?new Uint8Array([255]):kind==='depth'?bytes('{"x":'+'['.repeat(66)+'0'+']'.repeat(66)+'}'):
  kind==='nonfinite'?bytes('{"x":1e999}'):new Uint8Array(2*1024**2+1);
 await expect(readSupplyMaterialFiles(async()=>raw,{...F.anchor,index_sha256:await sha256(raw)},signal())).rejects.toThrow();
});
it.each([
 [['extra'],1],[['G0_G4'],'approved'],[['effective_rights','display'],false],
 [['window','covers_whole_season'],true],[['window','source_event_id'],'invented'],
 [['source','source_frame_index'],-1],[['blob_groups','material'],[]],[['terminal','status'],'future_prediction']
 ]as Array<[string[],unknown]>)('rejects rehashed root %j',async(path,value)=>{
 const q=await repack(alter(text('root.json'),path,value));await expect(readSupplyMaterialFiles(q.read,q.anchor,signal())).rejects.toThrow();
},20000);
it.each([
 [['leaves','0','geometry','value'],12.5],[['leaves','0','clock_exact','unit'],'s'],
 [['snapshot','derived','air_capacity','unit'],'W'],[['phase'],'material_after'],
 [['event_sequence'],true],[['internodes','0','id'],'invented']
 ]as Array<[string[],unknown]>)('rejects rehashed frame %j after valid graph hashes',async(path,value)=>{
 const changed=alter(wireFields(text('frame-0.json')).frame!,path,value),q=await repack(undefined,{index:0,raw:changed});
 await expect(readSupplyMaterialFiles(q.read,q.anchor,signal())).rejects.toThrow();
},20000);
it('keeps the unmodified repacked dataset valid with all independent hashes',async()=>{
 const q=await repack(),r=await readSupplyMaterialFiles(q.read,q.anchor,signal());
 expect(r.frames).toHaveLength(4);expect(r.sample_scalars).toBe(722);
 for(let j=0;j<4;j++)expect(r.frames[j]).toEqual(JSON.parse(text(`frame-${j}.json`)).frame);
},20000);
it('rejects aggregate overflow before reading a source',async()=>{
 const i=JSON.parse(text('index.json'));i.blobs.forEach((d:{bytes:number})=>d.bytes=2*1024**2);
 const raw=JSON.stringify(i);let reads=0;
 await expect(readSupplyMaterialFiles(async name=>{reads++;return name==='index.json'?bytes(raw):file(name);},{...F.anchor,index_sha256:await wireHash(raw)},signal())).rejects.toThrow();expect(reads).toBe(1);
});
it('rejects cancellation before and after an awaited read',async()=>{
 const a=new AbortController();a.abort();let reads=0;
 await expect(readSupplyMaterialFiles(async name=>{reads++;return file(name);},F.anchor,a.signal)).rejects.toThrow();expect(reads).toBe(0);
 const b=new AbortController();let release!:(v:Uint8Array)=>void;
 const pending=readSupplyMaterialFiles(()=>new Promise(resolve=>release=resolve),F.anchor,b.signal);b.abort();release(file('index.json'));await expect(pending).rejects.toThrow();
});
