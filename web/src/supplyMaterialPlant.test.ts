import {expect,it} from 'vitest';
import {MeshStandardMaterial,InstancedMesh,Mesh,Matrix4,Vector3,Triangle} from 'three';
import {createSupplyMaterialPlant} from './supplyMaterialPlant';
import {supplyMaterialPlantLayout} from './supplyMaterialPlantLayout';
import type {SupplyMaterialFrame} from './supplyMaterialReplay';
import {text} from './supplyMaterialTestData';
const frame=(index:number):SupplyMaterialFrame=>JSON.parse(text(`frame-${index}.json`)).frame;
it.each([0,1,2,3])('keeps actual phase/time/IDs and independently measures frame%i geometry',index=>{
 const f=frame(index),before=structuredClone(f),material=new MeshStandardMaterial(),plant=createSupplyMaterialPlant(f,{stem:material,leaf:material});
 try{
  expect(plant.placements().metadata.at).toEqual(f.at);expect(plant.placements().metadata.phase).toBe(f.phase);
  expect(plant.segments.map(m=>({id:m.userData.internode_id,length:m.scale.y,visible:m.visible}))).toEqual(f.internodes.map(n=>({id:n.id,length:n.geometry.value,visible:n.geometry.value>0})));
  plant.root.updateMatrixWorld(true);const measured=new Map<string,number>();
  for(const [j,n]of f.internodes.entries()){
   const mesh=plant.segments[j]!,bottom=new Vector3(0,-.5,0).applyMatrix4(mesh.matrixWorld),top=new Vector3(0,.5,0).applyMatrix4(mesh.matrixWorld);
   expect(Math.abs(top.distanceTo(bottom)-n.geometry.value)).toBeLessThan(1e-14);
   const placed=plant.placements().nodes.find(v=>v.id===n.id)!;expect(bottom.distanceTo(new Vector3(...placed.base))).toBeLessThan(1e-14);
   expect(top.distanceTo(new Vector3(...placed.tip))).toBeLessThan(1e-14);
   if(n.parent_internode_id!==null)expect(placed.base).toEqual(plant.placements().nodes.find(v=>v.id===n.parent_internode_id)!.tip);
  }
  plant.root.traverse(node=>{
   if(!(node instanceof InstancedMesh))return;
   const p=node.geometry.getAttribute('position'),indices=node.geometry.index!,m=new Matrix4(),a=new Vector3(),b=new Vector3(),c=new Vector3();let area=0;
   for(let k=0;k<node.count;k++){
    node.getMatrixAt(k,m);m.premultiply(node.matrixWorld);
    for(let j=0;j<indices.count;j+=3){a.fromBufferAttribute(p,indices.getX(j)).applyMatrix4(m);b.fromBufferAttribute(p,indices.getX(j+1)).applyMatrix4(m);c.fromBufferAttribute(p,indices.getX(j+2)).applyMatrix4(m);area+=new Triangle(a,b,c).getArea();}
   }measured.set(node.userData.leaf_id,area);
  });
  for(const l of f.leaves){const a=measured.get(l.id)!;expect(Number.isFinite(a)).toBe(true);if(l.geometry.value===0)expect(a).toBe(0);else expect(Math.abs(a/l.geometry.value-1)).toBeLessThan(5e-12);}
  expect(f).toEqual(before);expect(plant.root.children.every(g=>g instanceof Mesh||g.type==='Group')).toBe(true);
 }finally{plant.dispose();plant.dispose();material.dispose();}
 expect(()=>plant.placements()).toThrow();
});
it('keeps the actually funded initial area of the new leaf and the same ID after resuming',()=>{
 const before=frame(0),after=frame(1),next=frame(2),old=new Set(before.leaves.map(l=>l.id)),born=after.leaves.filter(l=>!old.has(l.id));
 expect(born).toHaveLength(1);expect(born[0]!.geometry.value).toBeGreaterThan(0);expect(next.leaves.find(l=>l.id===born[0]!.id)!.geometry.value).toBeGreaterThan(0);
 expect(supplyMaterialPlantLayout(after).leaves.find(l=>l.id===born[0]!.id)!.area_m2).toBe(born[0]!.geometry.value);
});
it('preserves zero area without inflating an organ in a renderer-only unit fixture',()=>{
 const f=frame(1);f.leaves[0]!.geometry.value=0;const m=new MeshStandardMaterial(),p=createSupplyMaterialPlant(f,{stem:m,leaf:m});
 try{expect(p.leafSurfaceAreas().find(l=>l.leaf_id===f.leaves[0]!.id)!.area_m2).toBe(0);}finally{p.dispose();m.dispose();}
});
it.each(['fractional_before_compatible_material_point','future_prediction','invented'])('rejects an unrelated phase %s',phase=>{
 const f={...frame(0),phase};expect(()=>supplyMaterialPlantLayout(f)).toThrow();
});
