import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {InstancedMesh,Matrix4,MeshBasicMaterial,Vector3} from 'three';
import {createSupplyMorphologyPlant} from './supplyMorphologyPlant';
import type {SupplyStoredFrame} from './supplyMorphologyReplay';
import {object} from './storedLeafReplayIO';
const frame=(i:number):SupplyStoredFrame=>JSON.parse(readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/frame-${i}.json`,import.meta.url),'utf8')).frame;
function area(mesh:InstancedMesh){
 const p=mesh.geometry.getAttribute('position'),idx=mesh.geometry.index!,matrix=new Matrix4();let sum=0;
 for(let k=0;k<mesh.count;k++){
  mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld);
  for(let j=0;j<idx.count;j+=3){
   const a=new Vector3().fromBufferAttribute(p,idx.getX(j)).applyMatrix4(matrix);
   const b=new Vector3().fromBufferAttribute(p,idx.getX(j+1)).applyMatrix4(matrix).sub(a);
   const c=new Vector3().fromBufferAttribute(p,idx.getX(j+2)).applyMatrix4(matrix).sub(a);sum+=b.cross(c).length()/2;
  }
 }return sum;
}
it('matches every original area/length and declared forest without inventing unbound parents',()=>{
 const material=new MeshBasicMaterial();let leaves=0,nodes=0,zeros=0,unbound=0;
 for(let i=0;i<38;i++){
  const f=frame(i),saved=structuredClone(f),plant=createSupplyMorphologyPlant(f,{stem:material,leaf:material});plant.root.updateMatrixWorld(true);
  expect(plant.root.userData.at).toEqual(object(f).at);expect(plant.root.userData.phase).toBe(object(f).phase);
  const placements=plant.placements();expect(placements.nodes).toHaveLength(f.internodes.length);expect(placements.leaves).toHaveLength(f.leaves.length);
  for(const [j,n]of f.internodes.entries()){
   nodes++;const mesh=plant.segments[j]!,bottom=new Vector3(0,-.5,0).applyMatrix4(mesh.matrixWorld),top=new Vector3(0,.5,0).applyMatrix4(mesh.matrixWorld);
   expect(mesh.userData.internode_id).toBe(n.id);expect(mesh.userData.parent_internode_id).toBe(n.parent_internode_id);
   expect(Math.abs(top.distanceTo(bottom)-n.geometry.value)).toBeLessThan(1e-14);
   const p=placements.nodes.find(v=>v.id===n.id)!;expect(p.parent_internode_id).toBe(n.parent_internode_id);
   expect(bottom.distanceTo(new Vector3(...p.base))).toBeLessThan(1e-14);expect(top.distanceTo(new Vector3(...p.tip))).toBeLessThan(1e-14);
   if(n.parent_internode_id!==null)expect(p.base).toEqual(placements.nodes.find(v=>v.id===n.parent_internode_id)!.tip);
   else expect(p.base[1]).toBe(0);
   if(n.geometry.value===0){zeros++;expect(mesh.visible).toBe(false);expect(p.base).toEqual(p.tip);}
  }
  const surfaces:InstancedMesh[]=[];plant.root.traverse(n=>{if(n instanceof InstancedMesh)surfaces.push(n);});expect(surfaces).toHaveLength(f.leaves.length);
  for(const l of f.leaves){
   leaves++;const mesh=surfaces.find(m=>m.userData.leaf_id===l.id)!;expect(Math.abs(area(mesh)/l.geometry.value-1)).toBeLessThan(5e-12);
   const p=placements.leaves.find(v=>v.id===l.id)!;expect(p.parent_internode_id).toBe(l.parent_internode_id);
   if(l.parent_internode_id===null){unbound++;expect(p.status).toBe('unbound_display_only');expect(mesh.parent!.parent).toBe(plant.unbound);}
   else expect(p.position).toEqual(placements.nodes.find(v=>v.id===l.parent_internode_id)!.tip);
  }
  expect(f).toEqual(saved);const before=plant.leafSurfaceAreas();f.leaves[0]!.geometry.value=999;expect(plant.leafSurfaceAreas()).toEqual(before);
  placements.nodes[0]!.base[0]=999;expect(plant.placements().nodes[0]!.base[0]).not.toBe(999);
  plant.dispose();plant.dispose();expect(()=>plant.placements()).toThrow();expect(()=>plant.leafSurfaceAreas()).toThrow();
 }
 expect({leaves,nodes,zeros,unbound}).toEqual({leaves:358,nodes:356,zeros:4,unbound:114});material.dispose();
},30000);
it.each(['negative','nonfinite','unit','duplicate_node','duplicate_leaf','missing_parent','cycle','self','leaf_parent','time','gate'])('rejects invalid geometry %s',kind=>{
 const f=frame(0);
 if(kind==='negative')f.internodes[0]!.geometry.value=-1;
 if(kind==='nonfinite')f.leaves[0]!.geometry.value=Infinity;
 if(kind==='unit')f.internodes[0]!.geometry.unit='cm';
 if(kind==='duplicate_node')f.internodes[1]!.id=f.internodes[0]!.id;
 if(kind==='duplicate_leaf')f.leaves[1]!.id=f.leaves[0]!.id;
 if(kind==='missing_parent')f.internodes[0]!.parent_internode_id='missing';
 if(kind==='cycle'){f.internodes[0]!.parent_internode_id=f.internodes[1]!.id;f.internodes[1]!.parent_internode_id=f.internodes[0]!.id;}
 if(kind==='self')f.internodes[0]!.parent_internode_id=f.internodes[0]!.id;
 if(kind==='leaf_parent')f.leaves[0]!.parent_internode_id='missing';
 if(kind==='time')object(f).at={time_origin_utc:'invalid',elapsed_seconds_exact:{numerator:'0',denominator:'1',unit:'s'}};
 if(kind==='gate')object(f).G0_G4='approved';
 const material=new MeshBasicMaterial();expect(()=>createSupplyMorphologyPlant(f,{stem:material,leaf:material})).toThrow();material.dispose();
});
it('preserves exact zero leaf area and releases owned resources without disposing borrowed materials',()=>{
 const f=frame(0);f.leaves[0]!.geometry.value=0;const material=new MeshBasicMaterial();let borrowed=0,owned=0;
 material.addEventListener('dispose',()=>borrowed++);const plant=createSupplyMorphologyPlant(f,{stem:material,leaf:material});
 expect(plant.leafSurfaceAreas().find(v=>v.leaf_id===f.leaves[0]!.id)!.area_m2).toBe(0);
 plant.root.traverse(n=>{if('geometry'in n)(n.geometry as import('three').BufferGeometry).addEventListener('dispose',()=>owned++);});
 plant.dispose();expect(owned).toBeGreaterThan(0);expect(borrowed).toBe(0);material.dispose();
});
