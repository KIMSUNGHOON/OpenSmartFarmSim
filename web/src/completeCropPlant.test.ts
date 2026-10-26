import {describe,it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {Box3,InstancedMesh,Matrix4,MeshBasicMaterial,PerspectiveCamera,Vector3} from 'three';
import {readCompleteCropReplay} from './completeCropReplay';
import {COMPLETE_CROP_FIXTURE as F} from './completeCropReplayFixture';
import {createCompleteCropPlant,COMPLETE_CROP_MAPPING,COMPLETE_CROP_POSE} from './completeCropPlant';

const read=(scenario:string)=>readCompleteCropReplay(async name=>new Uint8Array(readFileSync(new URL(`../public/complete-crop-replay/${scenario}/${name}`,import.meta.url))),
 F.scenarios[scenario as keyof typeof F.scenarios],new AbortController().signal);

function independentArea(mesh:InstancedMesh){
 const positions=mesh.geometry.getAttribute('position'),indices=mesh.geometry.index!,matrix=new Matrix4();let total=0;
 for(let instance=0;instance<mesh.count;instance++){
  mesh.getMatrixAt(instance,matrix);matrix.premultiply(mesh.matrixWorld);
  for(let j=0;j<indices.count;j+=3){
   const a=new Vector3().fromBufferAttribute(positions,indices.getX(j)).applyMatrix4(matrix);
   const b=new Vector3().fromBufferAttribute(positions,indices.getX(j+1)).applyMatrix4(matrix).sub(a);
   const c=new Vector3().fromBufferAttribute(positions,indices.getX(j+2)).applyMatrix4(matrix).sub(a);
   total+=b.cross(c).length()/2;
  }
 }return total;
}

describe('actual stored complete crop on realistic owned leaf geometry',()=>{
 it.each(Object.keys(F.scenarios))('binds endpoints and every birth boundary for %s',async scenario=>{
  const replay=await read(scenario),material=new MeshBasicMaterial(),indices=new Set([0,replay.frames.length-1]);
  replay.frames.forEach((f,i)=>{if(i>0&&(f.leaves.length!==replay.frames[i-1]!.leaves.length||f.internodes.length!==replay.frames[i-1]!.internodes.length||f.checkpoint_sha256===null)){
   indices.add(i-1);indices.add(i);
  }});
  for(const i of indices){
   const frame=replay.frames[i]!,original=structuredClone(frame),plant=createCompleteCropPlant(frame,{stem:material,leaf:material});
   expect(plant.root.userData.mapping).toBe(COMPLETE_CROP_MAPPING);expect(plant.root.userData.pose).toBe(COMPLETE_CROP_POSE);
   expect(plant.root.userData.at).toEqual(frame.at);expect(plant.root.userData.phase).toBe(frame.phase);
   plant.root.updateMatrixWorld(true);let top=0;
   for(const [j,node]of frame.internodes.entries()){
    const segment=plant.segments[j]!,bounds=new Box3().setFromObject(segment);
    expect(segment.userData.internode_id).toBe(node.internode_id);expect(Math.abs(bounds.min.y-top)).toBeLessThan(1e-15);
    top+=node.length.value;expect(Math.abs(bounds.max.y-top)).toBeLessThan(1e-15);
   }
   const surfaces:InstancedMesh[]=[];plant.root.traverse(n=>{if(n instanceof InstancedMesh)surfaces.push(n);});
   expect(surfaces).toHaveLength(frame.leaves.length);
   for(const leaf of frame.leaves){
    const mesh=surfaces.find(n=>n.userData.leaf_id===leaf.leaf_id)!;
    expect(Math.abs(independentArea(mesh)/leaf.area.value-1)).toBeLessThan(5e-12);
    const attachment=plant.attachments().find(a=>a.leaf_id===leaf.leaf_id)!;
    const parentIndex=frame.internodes.findIndex(n=>n.internode_id===leaf.attachment_internode_id);
    expect(attachment.attachment_internode_id).toBe(leaf.attachment_internode_id);
    expect(attachment.height_m).toBe(frame.internodes.slice(0,parentIndex+1).reduce((s,n)=>s+n.length.value,0));
   }
   const camera=new PerspectiveCamera(36,1,.001,10);camera.position.set(.2,.15,.3);camera.lookAt(0,.03,0);camera.updateProjectionMatrix();
   expect(Object.values(plant.projectedLeafBounds(camera)).every(Number.isFinite)).toBe(true);
   expect(frame).toEqual(original);const oldAreas=plant.leafSurfaceAreas();frame.leaves[0]!.area.value=0;
   expect(plant.leafSurfaceAreas()).toEqual(oldAreas);frame.leaves[0]!.area.value=original.leaves[0]!.area.value;
   plant.dispose();plant.dispose();expect(()=>plant.leafSurfaceAreas()).toThrow();
  }material.dispose();
 },60000);
 it('rejects missing parents and invalid units, and preserves borrowed materials',async()=>{
  const frame=(await read('initial-0')).frames[0]!,material=new MeshBasicMaterial();let materialsDisposed=0;
  material.addEventListener('dispose',()=>materialsDisposed++);
  for(const change of [()=>{frame.leaves[0]!.attachment_internode_id='unknown';},()=>{frame.leaves[0]!.area.unit='cm2';},
   ()=>{frame.internodes[0]!.length.value=NaN;}]){
   const saved=structuredClone(frame);change();expect(()=>createCompleteCropPlant(frame,{stem:material,leaf:material})).toThrow();Object.assign(frame,saved);
  }
  const plant=createCompleteCropPlant(frame,{stem:material,leaf:material});let disposed=0;
  plant.root.traverse(n=>{if('geometry'in n)(n.geometry as import('three').BufferGeometry).addEventListener('dispose',()=>disposed++);});
  plant.dispose();expect(disposed).toBeGreaterThan(0);expect(materialsDisposed).toBe(0);material.dispose();
 });
});
