import {integer,need,readStoredLeafFile,STORED_LEAF_MAX_BYTES} from './storedLeafReplayIO';
import {document,type WireDocument} from './supplyMorphologyGraphValues';
import {readSupplyMaterialFiles} from './supplyMaterialGraph';
import {SUPPLY_MATERIAL_FIXTURE as MODEL} from './supplyMaterialFixture';
import {MATERIAL_QUANTITY_FIXTURE as F} from './supplyMaterialQuantityFixture';
import {validateMaterialQuantityWire} from './supplyMaterialQuantityWire';
import {materialQuantityWindow} from './supplyMaterialQuantityValues';
export type MaterialQuantityScope='model'|'quantities';
export type MaterialQuantityReplay=Awaited<ReturnType<typeof readMaterialQuantityReplay>>;
export async function readMaterialQuantityReplay(readFile:(scope:MaterialQuantityScope,name:string)=>Promise<Uint8Array>,signal:AbortSignal){
 const saved=new Map<string,Uint8Array>();signal.throwIfAborted();
 const g=await readSupplyMaterialFiles(async name=>{
  const b=await readFile('model',name);signal.throwIfAborted();
  if(/^frame-[0-9]+\.json$/.test(name)&&b instanceof Uint8Array&&b.byteLength<=STORED_LEAF_MAX_BYTES)saved.set(name,new Uint8Array(b));return b;
 },{...MODEL.anchor},signal);
 const original:WireDocument[]=g.frames.map((_,i)=>{const b=saved.get(`frame-${i}.json`);need(b);const dto=document(new TextDecoder('utf-8',{fatal:true}).decode(b));return document(dto.fields.frame!);});
 signal.throwIfAborted();const raw=await readFile('quantities','quantities.json');signal.throwIfAborted();
 const q=await validateMaterialQuantityWire(raw,g,original,signal),morphology=structuredClone(g.frames),frames=structuredClone(q.frames);
 const source=structuredClone(q.source),summary=structuredClone({schema_version:'supply-material-quantity-http-replay-v1' as const,
  validation_scope:'stored_material_quantities_and_geometry_only' as const,artifact_sha256:g.artifact_sha256,fixture_sha256:F.fixture_sha256,result_sha256:F.result_sha256,
  projection_code_sha256:F.projection_code_sha256,frames:frames.length,sample_scalars:g.sample_scalars,downloaded_bytes:g.downloaded_bytes+raw.byteLength,
  source,model_floor_area:q.model_floor_area,scope:'software_research_only' as const,claim_scope:'stored_synthetic_material_quantities_only' as const,
  time_kind:g.root.value.time_kind,G0_G4:g.root.value.G0_G4,R2:g.root.value.R2,terminal:g.root.value.terminal});
 signal.throwIfAborted();
 return {summary:()=>structuredClone(summary),frame:(index:number)=>{integer(index,0,frames.length-1);return structuredClone({morphology:morphology[index]!,quantities:frames[index]!});},
  window:(first=0,last=frames.length-1)=>{
   const selected=materialQuantityWindow(frames,first,last),result={schema_version:'supply-material-quantity-browser-window-v1' as const,
    backend_reference:{schema_version:F.result_schema_version,code_sha256:F.projection_code_sha256},scope:summary.scope,claim_scope:summary.claim_scope,G0_G4:summary.G0_G4,R2:summary.R2,source,model_floor_area:q.model_floor_area,...selected};
   need(new TextEncoder().encode(JSON.stringify(result)).byteLength<=STORED_LEAF_MAX_BYTES);return structuredClone(result);
  }};
}
export function loadMaterialQuantityReplay(signal:AbortSignal){
 return readMaterialQuantityReplay((scope,name)=>readStoredLeafFile(scope==='model'?'./supply-material-replay/own-public-v1/':'./supply-material-quantities/own-public-v1/',name,signal),signal);
}
export class MaterialQuantityRequest{
 private generation=0;private controller?:AbortController;
 cancel(){this.generation++;this.controller?.abort();this.controller=undefined;}
 async load(){
  this.cancel();const generation=this.generation,controller=new AbortController();this.controller=controller;
  try{const replay=await loadMaterialQuantityReplay(controller.signal);controller.signal.throwIfAborted();need(generation===this.generation);return replay;}
  finally{if(generation===this.generation)this.controller=undefined;}
 }
}
