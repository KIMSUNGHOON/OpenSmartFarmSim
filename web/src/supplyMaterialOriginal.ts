import {need,object,closed} from './storedLeafReplayIO';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {document,list,type WireDocument} from './supplyMorphologyGraphValues';
import {installedPins,researchFlags,sourceDescriptor,verifySupplySourceBinding} from './supplyMorphologySourceBinding';
import {readSupplyContext,readSupplyCheckpoint,type SupplyContext} from './supplyMorphologyContextGraph';
import {readSupplyMaterial} from './supplyMorphologyMaterialGraph';
import {quantityLayout} from './supplyMorphologyQuantityLayout';
import {checkpointQuantities} from './supplyMorphologyQuantityAccounts';

// Validate the embedded original archive with its own contracts and horizon.
export async function materialOriginal(root:WireDocument,byHash:(hash:unknown)=>WireDocument,getRaw:(descriptor:unknown)=>string,signal:AbortSignal){
 const r=closed(root.value,[...F.schema_keys.root]);researchFlags(r,'supply-morphology-research-artifact-v1');
 installedPins(r.code_sha256,Object.keys(F.code_sha256));need(r.redistribution_authorized===true);
 await verifySupplySourceBinding(root,getRaw,hash=>byHash(hash).raw);
 let previous:SupplyContext|undefined,last:WireDocument|undefined,count=0;
 const segments=list(r.segments);need(segments.length>=1);
 for(const value of segments){
  signal.throwIfAborted();const segment=closed(value,['context','checkpoints']),d=sourceDescriptor(segment.context);
  const current=await readSupplyContext(getRaw(segment.context),d.sha256);
  need(current.descriptor.value.origin_context_sha256===sourceDescriptor(object(r.root_inputs).origin_context).sha256);
  if(previous){need(last);await readSupplyMaterial(previous,current,last);count++;}else need(current.packed.length===0);
  let prior:WireDocument|undefined;const cps=list(segment.checkpoints);need(cps.length>=1);
  const layout=quantityLayout(current.seed.value);
  for(const cp of cps){
   signal.throwIfAborted();const result=await readSupplyCheckpoint(getRaw(cp),current,prior);
   checkpointQuantities(layout,result.value,r.shoot_base_temperature);prior=result;count++;
  }
  previous=current;last=prior;
 }
 need(count===list(r.frames).length&&last&&previous);
 // Every root input and source descriptor has been checked by the source binding.
 return document(root.raw);
}
