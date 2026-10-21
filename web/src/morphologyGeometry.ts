import { BufferGeometry,CatmullRomCurve3,CylinderGeometry,Float32BufferAttribute,Group,InstancedMesh,
  LineBasicMaterial,LineSegments,Matrix4,Mesh,Quaternion,SphereGeometry,TubeGeometry,Vector3,type Material } from 'three';
import { tomatoLeafletGeometry } from './tomatoAppearance';
import type { MorphologyFrame } from './morphologyReplay';

export const MORPHOLOGY_MAPPING='stored-internode-metres-straight-axis-v1';
const leafAnchors=['synthetic-initial-0','synthetic-initial-1','synthetic-initial-2'];

export function createMorphologyGeometry(frame:MorphologyFrame,materials:{stem:Material;leaf:Material}){
  const root=new Group(),owned:BufferGeometry[]=[],instances:InstancedMesh[]=[],leafGroups:Group[]=[];
  const stemGeometry=new CylinderGeometry(.0013,.0016,1,14,1,true),nodeGeometry=new SphereGeometry(.00165,12,8);
  const leaflet=tomatoLeafletGeometry();owned.push(stemGeometry,nodeGeometry,leaflet);
  const hairs:number[]=[],segments:Mesh[]=[];let y=0;
  for(const n of frame.internodes){
    const length=n.length.value,mesh=new Mesh(stemGeometry,materials.stem);
    mesh.scale.y=length;mesh.position.y=y+length/2;mesh.castShadow=true;mesh.receiveShadow=true;
    mesh.userData={internode_id:n.internode_id,sequence:n.sequence,stored_length_m:length};root.add(mesh);segments.push(mesh);
    for(let j=0;j<48;j++){
      const angle=j*2.39996+n.sequence,t=(j+.5)/48;
      const x=Math.cos(angle),z=Math.sin(angle),at=y+t*length;
      hairs.push(x*.0015,at,z*.0015,x*.0024,at+.00015,z*.0024);
    }
    y+=length;
    const node=new Mesh(nodeGeometry,materials.stem);node.position.y=y;node.castShadow=true;root.add(node);
    const anchor=leafAnchors.indexOf(n.internode_id);
    if(anchor<0)continue;
    // Fixed authored leaves: no leaf count, area or organ classification is inferred.
    const group=new Group();group.position.y=y;group.rotation.y=anchor*2.4+.6;root.add(group);leafGroups.push(group);
    const curve=new CatmullRomCurve3([new Vector3(),new Vector3(.024,.013,0),new Vector3(.055,.005,0)]);
    const rachis=new TubeGeometry(curve,18,.00055,7,false);owned.push(rachis);
    const stalk=new Mesh(rachis,materials.stem);stalk.castShadow=true;group.add(stalk);
    const matrices:Matrix4[]=[];
    for(let k=0;k<3;k++)for(const sign of [-1,1]){
      const t=.22+k*.25+(sign>0?.035:0),at=curve.getPoint(t),direction=new Vector3(.5,.12,sign*.8).normalize();
      matrices.push(new Matrix4().compose(at,new Quaternion().setFromUnitVectors(new Vector3(0,1,0),direction),
        new Vector3(.017-k*.002,.025-k*.002,.025-k*.002)));
    }
    matrices.push(new Matrix4().compose(curve.getPoint(1),new Quaternion().setFromUnitVectors(new Vector3(0,1,0),
      new Vector3(1,-.2,0).normalize()),new Vector3(.019,.032,.032)));
    const leaves=new InstancedMesh(leaflet,materials.leaf,matrices.length);instances.push(leaves);
    matrices.forEach((m,i)=>leaves.setMatrixAt(i,m));leaves.castShadow=true;leaves.receiveShadow=true;group.add(leaves);
  }
  const hairGeometry=new BufferGeometry();hairGeometry.setAttribute('position',new Float32BufferAttribute(hairs,3));owned.push(hairGeometry);
  const hairMaterial=new LineBasicMaterial({color:'#cfdaa5',transparent:true,opacity:.4});
  root.add(new LineSegments(hairGeometry,hairMaterial));
  root.userData={mapping:MORPHOLOGY_MAPPING,at:frame.at,result_sha256:frame.result_sha256};
  return {root,segments,authoredLeafCount:leafGroups.length,
    dispose(){root.removeFromParent();instances.forEach(m=>m.dispose());owned.forEach(g=>g.dispose());hairMaterial.dispose();}};
}
