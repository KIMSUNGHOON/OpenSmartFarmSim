import {BufferGeometry,CatmullRomCurve3,CylinderGeometry,Group,InstancedMesh,Matrix4,Mesh,Quaternion,
 Triangle,TubeGeometry,Vector3,type Camera,type Material} from 'three';
import {tomatoLeafletGeometry} from './tomatoAppearance';
import type {CompleteCropFrame} from './completeCropReplay';

export const COMPLETE_CROP_MAPPING='stored-complete-crop-length-area-parent-v1';
export const COMPLETE_CROP_POSE='authored-straight-axis-compound-leaf-pose-v1';

function surfaceArea(mesh:InstancedMesh){
 const positions=mesh.geometry.getAttribute('position'),indices=mesh.geometry.index;
 if(!indices)throw Error('complete_crop_surface_missing');
 const matrix=new Matrix4(),a=new Vector3(),b=new Vector3(),c=new Vector3(),triangle=new Triangle(a,b,c);let total=0;
 for(let k=0;k<mesh.count;k++){
  mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld);
  for(let j=0;j<indices.count;j+=3){a.fromBufferAttribute(positions,indices.getX(j)).applyMatrix4(matrix);
   b.fromBufferAttribute(positions,indices.getX(j+1)).applyMatrix4(matrix);c.fromBufferAttribute(positions,indices.getX(j+2)).applyMatrix4(matrix);total+=triangle.getArea();}
 }return total;
}

/** Render only decoded stored quantities. Shape, azimuth, thickness and lighting remain authored assets. */
export function createCompleteCropPlant(frame:CompleteCropFrame,materials:{stem:Material;leaf:Material}){
 const nodes=frame.internodes.map(n=>({id:n.internode_id,sequence:n.sequence,length:n.length.value}));
 const leaves=frame.leaves.map(l=>({id:l.leaf_id,parent:l.attachment_internode_id,area:l.area.value}));
 if(nodes.length<1||nodes.length>512||leaves.length>512||new Set(nodes.map(n=>n.id)).size!==nodes.length||
  new Set(leaves.map(l=>l.id)).size!==leaves.length||nodes.some((n,i)=>!Number.isFinite(n.length)||n.length<=0||
   frame.internodes[i]!.length.unit!=='m'||!Number.isSafeInteger(n.sequence)||i>0&&n.sequence<=nodes[i-1]!.sequence)||
  leaves.some((l,i)=>!nodes.some(n=>n.id===l.parent)||!Number.isFinite(l.area)||l.area<=0||frame.leaves[i]!.area.unit!=='m2'))throw Error('complete_crop_geometry_binding_invalid');
 const root=new Group(),owned:BufferGeometry[]=[],instances:InstancedMesh[]=[],segments:Mesh[]=[],surfaces:InstancedMesh[]=[];
 const attachments:{leaf_id:string;attachment_internode_id:string;height_m:number;yaw_rad:number}[]=[];let disposed=false;
 const own=<T extends BufferGeometry,>(g:T)=>{owned.push(g);return g;};
 const dispose=()=>{if(disposed)return;disposed=true;root.removeFromParent();instances.forEach(m=>m.dispose());owned.forEach(g=>g.dispose());};
 const live=()=>{if(disposed)throw Error('complete_crop_geometry_disposed');};
 try{
  const stemGeometry=own(new CylinderGeometry(.0013,.0016,1,14,1,true)),bladeGeometry=own(tomatoLeafletGeometry());let y=0;
  for(const n of nodes){
   const stem=new Mesh(stemGeometry,materials.stem);stem.scale.y=n.length;stem.position.y=y+n.length/2;
   stem.castShadow=true;stem.receiveShadow=true;stem.userData={internode_id:n.id,stored_length_m:n.length};segments.push(stem);root.add(stem);y+=n.length;
   for(const l of leaves.filter(q=>q.parent===n.id)){
    // A stable per-ID pose separates several declared QA leaves on the same parent without implying phyllotaxy.
    let hash=2166136261;for(const ch of l.id)hash=Math.imul(hash^ch.charCodeAt(0),16777619)>>>0;
    const yaw=hash/2**32*Math.PI*2,group=new Group();group.position.y=y;group.rotation.y=yaw;root.add(group);
    attachments.push({leaf_id:l.id,attachment_internode_id:n.id,height_m:y,yaw_rad:yaw});
    const curve=new CatmullRomCurve3([new Vector3(),new Vector3(.024,.013,0),new Vector3(.055,.005,0)]);
    const stalk=new Mesh(own(new TubeGeometry(curve,18,.00025,7,false)),materials.stem);stalk.castShadow=true;group.add(stalk);
    const matrices:Matrix4[]=[];
    for(let k=0;k<3;k++)for(const sign of [-1,1]){
     const t=.22+k*.25+(sign>0?.035:0),direction=new Vector3(.5,.12,sign*.8).normalize();
     matrices.push(new Matrix4().compose(curve.getPoint(t),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),direction),
      new Vector3(.017-k*.002,.025-k*.002,.025-k*.002)));
    }
    matrices.push(new Matrix4().compose(curve.getPoint(1),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),new Vector3(1,-.2,0).normalize()),new Vector3(.019,.032,.032)));
    const blades=new InstancedMesh(bladeGeometry,materials.leaf,matrices.length);instances.push(blades);surfaces.push(blades);
    matrices.forEach((m,i)=>blades.setMatrixAt(i,m));blades.castShadow=true;blades.receiveShadow=true;group.add(blades);
    root.updateMatrixWorld(true);const area=surfaceArea(blades),scale=Math.sqrt(l.area)/Math.sqrt(area);
    if(!Number.isFinite(scale)||scale<=0)throw Error('complete_crop_surface_unavailable');group.scale.setScalar(scale);
    blades.userData.leaf_id=l.id;
   }
  }
  root.userData={mapping:COMPLETE_CROP_MAPPING,pose:COMPLETE_CROP_POSE,at:structuredClone(frame.at),phase:frame.phase,index:frame.index};
  const leafSurfaceAreas=()=>{live();root.updateMatrixWorld(true);return surfaces.map(m=>{
   const l=leaves.find(q=>q.id===m.userData.leaf_id)!;return {leaf_id:l.id,attachment_internode_id:l.parent,area_m2:surfaceArea(m)};
  });};
  for(const q of leafSurfaceAreas()){const l=leaves.find(l=>l.id===q.leaf_id)!;
   if(!Number.isFinite(q.area_m2)||Math.abs(q.area_m2/l.area-1)>5e-12)throw Error('complete_crop_surface_mismatch');}
  const projectedLeafBounds=(camera:Camera)=>{
   live();root.updateMatrixWorld(true);camera.updateMatrixWorld(true);
   const projection=new Matrix4().multiplyMatrices(camera.projectionMatrix,camera.matrixWorldInverse),matrix=new Matrix4(),point=new Vector3();
   const bounds={minX:Infinity,maxX:-Infinity,minY:Infinity,maxY:-Infinity};
   for(const mesh of surfaces)for(let k=0;k<mesh.count;k++){
    mesh.getMatrixAt(k,matrix);matrix.premultiply(mesh.matrixWorld).premultiply(projection);const positions=mesh.geometry.getAttribute('position');
    for(let i=0;i<positions.count;i++){point.fromBufferAttribute(positions,i).applyMatrix4(matrix);bounds.minX=Math.min(bounds.minX,point.x);
     bounds.maxX=Math.max(bounds.maxX,point.x);bounds.minY=Math.min(bounds.minY,point.y);bounds.maxY=Math.max(bounds.maxY,point.y);}
   }return bounds;
  };
  return {root,segments,leafSurfaceAreas,projectedLeafBounds,attachments:()=>{live();return structuredClone(attachments);},dispose};
 }catch(error){dispose();throw error;}
}
