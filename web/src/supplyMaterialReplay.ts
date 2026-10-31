import {integer,need,readStoredLeafFile} from './storedLeafReplayIO';
import {readSupplyMaterialFiles} from './supplyMaterialGraph';
import {SUPPLY_MATERIAL_FIXTURE as F} from './supplyMaterialFixture';

export type SupplyMaterialFrame=Awaited<ReturnType<typeof readSupplyMaterialFiles>>['frames'][number];
export type SupplyMaterialReplay=Awaited<ReturnType<typeof loadSupplyMaterialReplay>>;
export async function loadSupplyMaterialReplay(signal:AbortSignal){
 signal.throwIfAborted();const anchor={...F.anchor};
 const q=await readSupplyMaterialFiles(name=>readStoredLeafFile('./supply-material-replay/own-public-v1/',name,signal),anchor,signal);
 signal.throwIfAborted();const frames=structuredClone(q.frames),root=q.root.value;
 const summary=structuredClone({schema_version:'supply-material-http-replay-v1' as const,validation_scope:'stored_http_replay_only' as const,
  artifact_sha256:q.artifact_sha256,index_sha256:anchor.index_sha256,frames:frames.length,sample_scalars:q.sample_scalars,
  downloaded_bytes:q.downloaded_bytes,scope:root.scope,claim_scope:root.claim_scope,time_kind:root.time_kind,
  effective_rights:{use:true,display:true,redistribute:true},window:root.window,code_sha256:root.code_sha256,terminal:root.terminal,G0_G4:root.G0_G4,R2:root.R2});
 return {summary:()=>structuredClone(summary),frame:(index:number):SupplyMaterialFrame=>{integer(index,0,frames.length-1);return structuredClone(frames[index]!);}};
}
export class SupplyMaterialRequest{
 private generation=0;private controller?:AbortController;
 cancel(){this.generation++;this.controller?.abort();this.controller=undefined;}
 async load(){
  this.cancel();const generation=this.generation,controller=new AbortController();this.controller=controller;
  try{const replay=await loadSupplyMaterialReplay(controller.signal);controller.signal.throwIfAborted();need(generation===this.generation);return replay;}
  finally{if(generation===this.generation)this.controller=undefined;}
 }
}
