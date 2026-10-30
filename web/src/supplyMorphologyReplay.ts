import {integer,need,readStoredLeafFile} from './storedLeafReplayIO';
import {readSupplyMorphologyStoredQuantities} from './supplyMorphologyStoredQuantities';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';

export type SupplyStoredFrame=Awaited<ReturnType<typeof readSupplyMorphologyStoredQuantities>>['frames'][number];
export type SupplyMorphologyReplay=Awaited<ReturnType<typeof loadSupplyMorphologyReplay>>;

export async function loadSupplyMorphologyReplay(signal:AbortSignal){
 signal.throwIfAborted();
 const anchor={...F.anchor};
 const q=await readSupplyMorphologyStoredQuantities(name=>readStoredLeafFile('./supply-morphology-replay/own-public-v1/',name,signal),anchor,signal);
 signal.throwIfAborted();
 const frames=structuredClone(q.frames),root=q.root.value;
 const summary=structuredClone({schema_version:'supply-morphology-http-replay-v1' as const,validation_scope:'stored_http_replay_only' as const,
  artifact_sha256:q.artifact_sha256,index_sha256:anchor.index_sha256,frames:frames.length,sample_scalars:q.sample_scalars,
  downloaded_bytes:q.downloaded_bytes,scope:root.scope,claim_scope:root.claim_scope,time_kind:root.time_kind,
  source_rights:root.source_rights,code_sha256:root.code_sha256,terminal:root.terminal,G0_G4:root.G0_G4,R2:root.R2});
 return {summary:()=>structuredClone(summary),frame:(index:number):SupplyStoredFrame=>{
  integer(index,0,frames.length-1);return structuredClone(frames[index]!);
 }};
}
export class SupplyMorphologyRequest{
 private generation=0;private controller?:AbortController;
 cancel(){this.generation++;this.controller?.abort();this.controller=undefined;}
 async load(){
  this.cancel();const generation=this.generation,controller=new AbortController();this.controller=controller;
  try{
   const replay=await loadSupplyMorphologyReplay(controller.signal);controller.signal.throwIfAborted();need(generation===this.generation);return replay;
  }finally{if(generation===this.generation)this.controller=undefined;}
 }
}
