import {BufferGeometry,CatmullRomCurve3,CylinderGeometry,Group,InstancedMesh,Matrix4,Mesh,Quaternion,Triangle,TubeGeometry,Vector3,type Material} from 'three';
import {tomatoLeafletGeometry} from './tomatoAppearance';
import {need} from './storedLeafReplayIO';
import type {SupplyMaterialFrame} from './supplyMaterialReplay';
import {supplyMaterialPlantLayout,SUPPLY_MATERIAL_GEOMETRY_MAPPING,SUPPLY_MATERIAL_GEOMETRY_POSE} from './supplyMaterialPlantLayout';

function surface(mesh:InstancedMesh){
 const p=mesh.geometry.getAttribute('position'),indices=mesh.geometry.index;need(indices);
 const matrix=new Matrix4(),a=new Vector3(),b=new Vector3(),c=new Vector3(),triangle=new Triangle(a,b,c);let total=0;
 for(let k=0;k<mesh.count;k++){
  mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld);
  for(let j=0;j<indices.count;j+=3){
   a.fromBufferAttribute(p,indices.getX(j)).applyMatrix4(matrix);b.fromBufferAttribute(p,indices.getX(j+1)).applyMatrix4(matrix);
   c.fromBufferAttribute(p,indices.getX(j+2)).applyMatrix4(matrix);total+=triangle.getArea();
  }
 }return total;
}
export function createSupplyMaterialPlant(frame:SupplyMaterialFrame,materials:{stem:Material;leaf:Material}){
 const input=structuredClone(frame),placements=supplyMaterialPlantLayout(input),root=new Group(),forest=new Group(),unbound=new Group();root.add(forest,unbound);
 const owned:BufferGeometry[]=[],surfaces:InstancedMesh[]=[],segments:Mesh[]=[];let disposed=false;
 const own=<T extends BufferGeometry,>(g:T)=>{owned.push(g);return g;};
 const dispose=()=>{if(disposed)return;disposed=true;root.removeFromParent();surfaces.forEach(m=>m.dispose());owned.forEach(g=>g.dispose());};
 const live=()=>need(!disposed);
 try{
  const stemGeometry=own(new CylinderGeometry(.0013,.0016,1,14,1,true)),blade=own(tomatoLeafletGeometry());
  const curve=new CatmullRomCurve3([new Vector3(),new Vector3(.024,.013,0),new Vector3(.055,.005,0)]);
  const stalkGeometry=own(new TubeGeometry(curve,18,.00025,7,false)),matrices:Matrix4[]=[];
  for(let k=0;k<3;k++)for(const sign of [-1,1]){
   const t=.22+k*.25+(sign>0?.035:0),direction=new Vector3(.5,.12,sign*.8).normalize();
   matrices.push(new Matrix4().compose(curve.getPoint(t),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),direction),new Vector3(.017-k*.002,.025-k*.002,.025-k*.002)));
  }
  matrices.push(new Matrix4().compose(curve.getPoint(1),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),new Vector3(1,-.2,0).normalize()),new Vector3(.019,.032,.032)));
  for(const [i,n]of placements.nodes.entries()){
   const mesh=new Mesh(stemGeometry,materials.stem);mesh.position.set(n.base[0],n.base[1]+n.length_m/2,n.base[2]);mesh.scale.y=n.length_m;
   mesh.visible=n.length_m>0;mesh.castShadow=true;mesh.receiveShadow=true;
   mesh.userData={internode_id:n.id,parent_internode_id:n.parent_internode_id,stored_length_m:n.length_m,stored:structuredClone(input.internodes[i])};forest.add(mesh);segments.push(mesh);
  }
  for(const [i,l]of placements.leaves.entries()){
   const group=new Group();group.position.fromArray(l.position);group.rotation.y=l.yaw_rad;(l.parent_internode_id===null?unbound:forest).add(group);
   const stalk=new Mesh(stalkGeometry,materials.stem);stalk.castShadow=true;group.add(stalk);
   const mesh=new InstancedMesh(blade,materials.leaf,matrices.length);surfaces.push(mesh);matrices.forEach((m,i)=>mesh.setMatrixAt(i,m));
   mesh.castShadow=true;mesh.receiveShadow=true;mesh.userData={leaf_id:l.id,parent_internode_id:l.parent_internode_id,status:l.status,stored:structuredClone(input.leaves[i])};group.add(mesh);
   root.updateMatrixWorld(true);const measured=surface(mesh);need(Number.isFinite(measured)&&measured>0);
   const scale=l.area_m2===0?0:Math.sqrt(l.area_m2)/Math.sqrt(measured);need(Number.isFinite(scale));group.scale.setScalar(scale);group.visible=l.area_m2>0;
  }
  root.userData={mapping:SUPPLY_MATERIAL_GEOMETRY_MAPPING,pose:SUPPLY_MATERIAL_GEOMETRY_POSE,...structuredClone(placements.metadata)};
  const leafSurfaceAreas=()=>{
   live();root.updateMatrixWorld(true);return surfaces.map(mesh=>({leaf_id:mesh.userData.leaf_id as string,parent_internode_id:mesh.userData.parent_internode_id as string|null,area_m2:surface(mesh)}));
  };
  for(const [i,measured]of leafSurfaceAreas().entries()){
   const expected=placements.leaves[i]!.area_m2;need(Number.isFinite(measured.area_m2)&&(expected===0?measured.area_m2===0:Math.abs(measured.area_m2/expected-1)<5e-12));
  }
  return {root,forest,unbound,segments,leafSurfaceAreas,placements:()=>{live();return structuredClone(placements);},dispose};
 }catch(error){dispose();throw error;}
}
