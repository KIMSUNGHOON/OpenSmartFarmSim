import {BufferGeometry,CatmullRomCurve3,CylinderGeometry,Float32BufferAttribute,Group,InstancedMesh,LineBasicMaterial,
 LineSegments,Matrix4,Mesh,Quaternion,SphereGeometry,Triangle,TubeGeometry,Vector3,type Camera,type Material} from 'three';
import {tomatoLeafletGeometry} from './tomatoAppearance';
import type {GrowingGeometryFrame} from './growingGeometryReplay';
import type {GrowingGeometryRemovalFrame} from './growingGeometryRemovalReplay';
import type {LeafCarbonStockFrame} from './leafCarbonStockReplay';

export const GROWING_SCAFFOLD={version:'authored-three-leaf-scaffold-v1',origin:'authored_visual_asset',
 stem_height_m:1.6,leaves:[{leaf_id:'own-leaf-0',height_m:.45,yaw_rad:.4},
  {leaf_id:'own-leaf-1',height_m:.95,yaw_rad:2.8},{leaf_id:'own-leaf-2',height_m:1.4,yaw_rad:5.2}]} as const;
export const GROWING_AREA_MAPPING='stored-leaf-m2-authored-compound-triangles-v1';
type VisualFrame=Pick<GrowingGeometryFrame,'leaves'|'leaf_ids'|'checkpoint_sha256'|'at'>;
type Materials={stem:Material;leaf:Material};
type Attachment=typeof GROWING_SCAFFOLD.leaves[number];

function surfaceArea(mesh:InstancedMesh){
 const positions=mesh.geometry.getAttribute('position'),indices=mesh.geometry.index;if(!indices)throw Error('leaf_triangles_missing');
 const matrix=new Matrix4(),a=new Vector3(),b=new Vector3(),c=new Vector3(),triangle=new Triangle(a,b,c);let area=0;
 for(let k=0;k<mesh.count;k++){
  mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld);
  for(let i=0;i<indices.count;i+=3){a.fromBufferAttribute(positions,indices.getX(i)).applyMatrix4(matrix);
   b.fromBufferAttribute(positions,indices.getX(i+1)).applyMatrix4(matrix);c.fromBufferAttribute(positions,indices.getX(i+2)).applyMatrix4(matrix);area+=triangle.getArea();}
 }return area;
}

export function createGrowingGeometryPlant(frame:GrowingGeometryFrame,materials:{stem:Material;leaf:Material}){
 return createPlant(frame,materials,GROWING_SCAFFOLD.leaves);
}

export function createLeafCarbonStockPlant(frame:LeafCarbonStockFrame,materials:Materials){
 const stocks=frame.leaves.map(leaf=>{
  if(leaf.carbon.unit!=='mg_CH2O/m2_floor'||!Number.isFinite(leaf.carbon.value)||leaf.carbon.value<0)throw Error('stored_leaf_carbon_binding_invalid');
  return {leaf_id:leaf.leaf_id,carbon:structuredClone(leaf.carbon)};
 });
 const plant=createPlant(frame,materials,GROWING_SCAFFOLD.leaves);let disposed=false;
 plant.root.userData.carbon_authority='stored_individual_leaf_carbon';
 return {...plant,leafCarbonStocks(){if(disposed)throw Error('disposed_leaf_geometry');return structuredClone(stocks);},
  dispose(){disposed=true;plant.dispose();}};
}

export function createGrowingGeometryRemovalPlant(frame:GrowingGeometryRemovalFrame,materials:Materials){
 const before=frame.phase==='before_removal';
 if(!before&&!['after_removal_before_next_step','post_removal_interval'].includes(frame.phase))throw Error('stored_removal_phase_invalid');
 if(before?frame.leaves.length!==3:frame.leaves.length<1||frame.leaves.length>2)throw Error('authored_scaffold_leaf_scope');
 const specifications=frame.leaves.map(leaf=>{
  const specification=GROWING_SCAFFOLD.leaves.find(spec=>spec.leaf_id===leaf.leaf_id);
  if(!specification)throw Error('authored_scaffold_leaf_scope');return specification;
 });
 const indices=specifications.map(spec=>GROWING_SCAFFOLD.leaves.indexOf(spec));
 if(indices.some((index,i)=>i>0&&index<=indices[i-1]!))throw Error('stored_leaf_order_invalid');
 return createPlant(frame,materials,specifications);
}

function createPlant(frame:VisualFrame,materials:Materials,specifications:readonly Attachment[]){
 if(frame.leaves.length!==specifications.length||frame.leaf_ids.length!==frame.leaves.length)throw Error('authored_scaffold_leaf_scope');
 frame.leaves.forEach((leaf,i)=>{
  if(leaf.leaf_id!==specifications[i]!.leaf_id||frame.leaf_ids[i]!==leaf.leaf_id||leaf.area.unit!=='m2'||
   !Number.isFinite(leaf.area.value)||leaf.area.value<=0)throw Error('stored_area_binding_invalid');
 });
 const bindings=frame.leaves.map(leaf=>({leaf_id:leaf.leaf_id,area:leaf.area.value}));
 const root=new Group(),owned:BufferGeometry[]=[],instances:InstancedMesh[]=[],surfaces:InstancedMesh[]=[];
 let hairMaterial:LineBasicMaterial|undefined,disposed=false;
 const own=<T extends BufferGeometry,>(geometry:T)=>{owned.push(geometry);return geometry;};
 const dispose=()=>{if(disposed)return;disposed=true;root.removeFromParent();instances.forEach(m=>m.dispose());owned.forEach(g=>g.dispose());hairMaterial?.dispose();};
 try{
  const stemGeometry=own(new CylinderGeometry(.008,.012,GROWING_SCAFFOLD.stem_height_m,16,1,true)),stem=new Mesh(stemGeometry,materials.stem);
  stem.position.y=GROWING_SCAFFOLD.stem_height_m/2;stem.castShadow=true;stem.receiveShadow=true;root.add(stem);
  const nodeGeometry=own(new SphereGeometry(.013,12,8)),leaflet=own(tomatoLeafletGeometry());
  GROWING_SCAFFOLD.leaves.forEach(specification=>{
   const node=new Mesh(nodeGeometry,materials.stem);node.position.y=specification.height_m;root.add(node);
  });
  specifications.forEach((specification,index)=>{
   const group=new Group();group.position.y=specification.height_m;group.rotation.y=specification.yaw_rad;root.add(group);
   const curve=new CatmullRomCurve3([new Vector3(),new Vector3(.024,.013,0),new Vector3(.055,.005,0)]);
   const rachis=own(new TubeGeometry(curve,18,.00025,7,false)),stalk=new Mesh(rachis,materials.stem);stalk.castShadow=true;group.add(stalk);
   const matrices:Matrix4[]=[];
   for(let k=0;k<3;k++)for(const sign of [-1,1]){
    const t=.22+k*.25+(sign>0?.035:0),direction=new Vector3(.5,.12,sign*.8).normalize();
    matrices.push(new Matrix4().compose(curve.getPoint(t),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),direction),
     new Vector3(.017-k*.002,.025-k*.002,.025-k*.002)));
   }
   matrices.push(new Matrix4().compose(curve.getPoint(1),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),new Vector3(1,-.2,0).normalize()),new Vector3(.019,.032,.032)));
   const leaves=new InstancedMesh(leaflet,materials.leaf,matrices.length);instances.push(leaves);surfaces.push(leaves);
   matrices.forEach((matrix,i)=>leaves.setMatrixAt(i,matrix));leaves.castShadow=true;leaves.receiveShadow=true;group.add(leaves);
   root.updateMatrixWorld(true);const area=surfaceArea(leaves),scale=Math.sqrt(bindings[index]!.area)/Math.sqrt(area);
   if(!Number.isFinite(scale)||scale<=0)throw Error('stored_leaf_surface_unavailable');group.scale.setScalar(scale);
  });
  const hairs:number[]=[];
  for(let i=0;i<180;i++){const angle=i*2.39996,y=(i+.5)/180*GROWING_SCAFFOLD.stem_height_m,r=.012-.004*y/GROWING_SCAFFOLD.stem_height_m;
   const x=Math.cos(angle),z=Math.sin(angle);hairs.push(x*r,y,z*r,x*(r+.004),y+.001,z*(r+.004));}
  const hairGeometry=own(new BufferGeometry());hairGeometry.setAttribute('position',new Float32BufferAttribute(hairs,3));
  hairMaterial=new LineBasicMaterial({color:'#cedba1',transparent:true,opacity:.4});root.add(new LineSegments(hairGeometry,hairMaterial));
  root.userData={mapping:GROWING_AREA_MAPPING,geometry_authority:'stored_leaf_area',scaffold_version:GROWING_SCAFFOLD.version,
   checkpoint_sha256:frame.checkpoint_sha256,at:structuredClone(frame.at)};
  const leafSurfaceAreas=()=>{if(disposed)throw Error('disposed_leaf_geometry');root.updateMatrixWorld(true);
   return surfaces.map((mesh,i)=>({leaf_id:bindings[i]!.leaf_id,area_m2:surfaceArea(mesh)}));};
  for(const [i,row]of leafSurfaceAreas().entries())if(!Number.isFinite(row.area_m2)||Math.abs(row.area_m2/bindings[i]!.area-1)>5e-12)throw Error('stored_leaf_area_mapping_mismatch');
  const projectedLeafBounds=(camera:Camera)=>{
   root.updateMatrixWorld(true);camera.updateMatrixWorld(true);
   const projection=new Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse),matrix=new Matrix4(),point=new Vector3();
   const bounds={minX:Infinity,maxX:-Infinity,minY:Infinity,maxY:-Infinity};
   for(const mesh of surfaces){const positions=mesh.geometry.getAttribute('position');
    for(let k=0;k<mesh.count;k++){mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld).premultiply(projection);
     for(let i=0;i<positions.count;i++){point.fromBufferAttribute(positions,i).applyMatrix4(matrix);
      bounds.minX=Math.min(bounds.minX,point.x);bounds.maxX=Math.max(bounds.maxX,point.x);bounds.minY=Math.min(bounds.minY,point.y);bounds.maxY=Math.max(bounds.maxY,point.y);}
    }
   }return bounds;
  };
  return {root,leafSurfaceAreas,projectedLeafBounds,attachments:()=>structuredClone(specifications),dispose};
 }catch(error){dispose();throw error;}
}
