import { BufferGeometry,Float32BufferAttribute,Group,InstancedMesh,Matrix4,Mesh,
  Vector3,Quaternion,CatmullRomCurve3,TubeGeometry,SphereGeometry,Color,
  LineSegments,LineBasicMaterial,type Material } from 'three';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';

// Authored appearance only. These coordinates are not crop model parameters.
export const TOMATO_APPEARANCE_VERSION='authored-tomato-appearance-v1';
export const APPEARANCE_SCOPE='representative_geometry_not_growth_prediction';
const up=new Vector3(0,1,0);
const point=(x:number,y:number,z:number)=>new Vector3(x,y,z);

export function tomatoLeafletGeometry():BufferGeometry {
  const positions:number[]=[],uv:number[]=[],colors:number[]=[],indices:number[]=[];
  const rows=48,cols=12;
  for(let i=0;i<=rows;i++){
    const t=i/rows;
    const lobes=1+.24*Math.sin(t*7*Math.PI-.5)+.035*Math.sin(t*31*Math.PI);
    const width=Math.pow(Math.sin(t*Math.PI),.86)*.305*lobes;
    for(let j=0;j<=cols;j++){
      const s=j/cols*2-1;
      positions.push(width*s,t,-.16*t*t+.065*s*s*Math.sin(t*Math.PI)+.018*Math.sin(t*17+s*3)*s*s);
      uv.push((s+1)/2,t);
      const c=new Color().setRGB(.72+.14*t,.85+.1*t,.61+.14*t);
      colors.push(c.r,c.g,c.b);
      if(i<rows && j<cols){const a=i*(cols+1)+j,b=a+cols+1;indices.push(a,b,a+1,a+1,b,b+1);}
    }
  }
  const g=new BufferGeometry();g.setAttribute('position',new Float32BufferAttribute(positions,3));
  g.setAttribute('uv',new Float32BufferAttribute(uv,2));g.setAttribute('color',new Float32BufferAttribute(colors,3));
  g.setIndex(indices);g.computeVertexNormals();return g;
}

export function tomatoFruitGeometry():BufferGeometry {
  const g=new SphereGeometry(1,40,28),p=g.getAttribute('position'),c:number[]=[];
  for(let i=0;i<p.count;i++){
    const x=p.getX(i),y=p.getY(i),z=p.getZ(i),a=Math.atan2(z,x);
    const rib=1+.015*Math.cos(a*5)*Math.pow(Math.max(0,y),3);
    p.setXYZ(i,x*rib,y*.94-(y>.6?.045*Math.pow((y-.6)/.4,2):0),z*rib);
    const shade=1-.13*Math.pow(Math.max(0,y),4);c.push(shade,shade,shade);
  }
  g.setAttribute('color',new Float32BufferAttribute(c,3));g.computeVertexNormals();return g;
}

type Materials={leaf:Material;stem:Material;fruit:Material;calyx:Material;flower:Material};
export function createTomatoAppearance(materials:Materials){
  const root=new Group(),stemParts:BufferGeometry[]=[],leafMatrices:Matrix4[]=[],calyxMatrices:Matrix4[]=[],
    fruitMatrices:Matrix4[]=[],fruitColors:Color[]=[],flowerMatrices:Matrix4[]=[],hairs:number[]=[];
  const owned:BufferGeometry[]=[];
  const fruitBounds:{center:Vector3;radius:number}[]=[];
  function stem(points:Vector3[],radius:number,hairy=false){
    const curve=new CatmullRomCurve3(points),g=new TubeGeometry(curve,Math.max(8,points.length*7),radius,7,false);
    stemParts.push(g);
    if(hairy)for(let i=0;i<80;i++){
      const t=(i+.5)/80,p=curve.getPoint(t),tangent=curve.getTangent(t),angle=i*2.39996;
      const normal=point(Math.cos(angle),.13,Math.sin(angle)).projectOnPlane(tangent).normalize();
      const a=p.clone().addScaledVector(normal,radius),b=p.clone().addScaledVector(normal,radius+.0018);
      hairs.push(a.x,a.y,a.z,b.x,b.y,b.z);
    }
  }
  const main=(t:number)=>point(.025*Math.sin(t*8),t*1.72,.018*Math.sin(t*13));
  stem(Array.from({length:12},(_,i)=>main(i/11)),.007,true);
  function blade(at:Vector3,direction:Vector3,length:number,width:number,roll=0){
    const q=new Quaternion().setFromUnitVectors(up,direction.clone().normalize());
    q.multiply(new Quaternion().setFromAxisAngle(up,roll));
    leafMatrices.push(new Matrix4().compose(at,q,point(width,length,length)));
  }
  // Each compound leaf has its own curved rachis and attached leaflets.
  for(let n=0;n<11;n++){
    const height=.31+n*.122,angle=n*2.41+.9,origin=main(height/1.72);
    const outward=point(Math.cos(angle),0,Math.sin(angle)),side=point(-outward.z,0,outward.x);
    const reach=.33+.07*Math.sin(n*1.7),tip=origin.clone().addScaledVector(outward,reach).add(point(0,.04,0));
    const middle=origin.clone().addScaledVector(outward,reach*.46).add(point(0,.075,0));
    const curve=new CatmullRomCurve3([origin,middle,tip]);
    stem([origin,middle,tip],.0025,true);
    for(let k=0;k<3;k++)for(const sign of [-1,1]){
      const t=.26+k*.24+(sign===1?.035:0),start=curve.getPoint(t);
      const direction=outward.clone().multiplyScalar(.4).addScaledVector(side,sign*.9).add(point(0,-.06-k*.08,0));
      const joint=start.clone().addScaledVector(direction,.017);stem([start,joint],.0011);
      const size=(.13+k*.02)*(n>8?.8:1);
      blade(joint,direction,size,size*(.87+.12*Math.sin(n+k)),sign*(.2+.14*k));
      if(k===0)blade(start.clone().addScaledVector(outward,.025),direction.clone().addScaledVector(outward,-.4),.055,.05,sign*.5);
    }
    blade(tip,outward.clone().add(point(0,-.19,0)),.19*(n>8?.8:1),.16,n*.18);
  }
  // Three deliberately authored trusses; no mapping from carbon to fruit count.
  const trussViews:Vector3[]=[];
  for(let n=0;n<3;n++){
    const angle=-.8+n*.65,dir=point(Math.cos(angle),0,Math.sin(angle)),side=point(-dir.z,0,dir.x);
    const start=main((.5+n*.36)/1.72),base=start.clone().addScaledVector(dir,.13).add(point(0,-.025,0));
    const tip=base.clone().addScaledVector(dir,.15).add(point(0,-.3,0));
    const curve=new CatmullRomCurve3([start,base,tip]);
    stem([start,base,tip],.0028,true);
    for(let k=0;k<8;k++){
      const a=curve.getPoint(.28+k*.085),sign=k%2===0?-1:1;
      const radius=.029-(k*.0011)+.0012*Math.sin(k*3+n);
      const center=a.clone().addScaledVector(side,sign*(.045+.005*(k%3))).add(point(0,-.057,0));
      for(let attempt=0;fruitBounds.some(b=>b.center.distanceTo(center)<(b.radius+radius*1.1)*1.08);attempt++){
        if(attempt>=64)throw Error('appearance_fruit_overlap');
        center.addScaledVector(side,sign*.004).addScaledVector(dir,.001);
      }
      fruitBounds.push({center:center.clone(),radius:radius*1.1});
      const top=center.clone().add(point(0,radius*.91,0));
      stem([a,a.clone().lerp(top,.5).add(point(0,.009,0)),top],.00125,true);
      fruitMatrices.push(new Matrix4().compose(center,new Quaternion().setFromAxisAngle(up,k*.74),point(radius,radius*1.1,radius)));
      fruitColors.push(new Color(n===0?(k<5?'#c72c16':k<7?'#e78723':'#a1a83a'):
        n===1?(k<3?'#e86c22':k<5?'#c2ad3d':'#6c902d'):'#719538'));
      for(let j=0;j<5;j++){
        const a=j*Math.PI*2/5+k*.2,d=point(Math.cos(a),.33,Math.sin(a));
        const q=new Quaternion().setFromUnitVectors(up,d.normalize());
        calyxMatrices.push(new Matrix4().compose(top,q,point(radius*.4,radius*.86,radius*.46)));
      }
      if(n===0 && k===3)trussViews.push(center.clone());
    }
  }
  const flowerBase=main(.91),flowerCenter=flowerBase.clone().add(point(-.12,.03,.03));
  stem([flowerBase,flowerCenter],.0017);
  for(let i=0;i<5;i++){
    const a=i*Math.PI*2/5,d=point(Math.cos(a),Math.sin(a),.25),q=new Quaternion().setFromUnitVectors(up,d.normalize());
    flowerMatrices.push(new Matrix4().compose(flowerCenter,q,point(.012,.024,.009)));
  }
  function instances(geometry:BufferGeometry,material:Material,matrices:Matrix4[],colors?:Color[]){
    owned.push(geometry);const mesh=new InstancedMesh(geometry,material,matrices.length);
    matrices.forEach((matrix,i)=>{mesh.setMatrixAt(i,matrix);if(colors?.[i])mesh.setColorAt(i,colors[i]!);});
    mesh.castShadow=true;mesh.receiveShadow=true;root.add(mesh);return mesh;
  }
  const leaves=instances(tomatoLeafletGeometry(),materials.leaf,leafMatrices);
  const fruits=instances(tomatoFruitGeometry(),materials.fruit,fruitMatrices,fruitColors);
  instances(tomatoLeafletGeometry(),materials.calyx,calyxMatrices);
  instances(tomatoLeafletGeometry(),materials.flower,flowerMatrices);
  const merged=mergeGeometries(stemParts);stemParts.forEach(g=>g.dispose());
  if(!merged)throw Error('appearance_stem_merge');owned.push(merged);
  const stems=new Mesh(merged,materials.stem);stems.castShadow=true;stems.receiveShadow=true;root.add(stems);
  const hairGeometry=new BufferGeometry();hairGeometry.setAttribute('position',new Float32BufferAttribute(hairs,3));owned.push(hairGeometry);
  const hairMaterial=new LineBasicMaterial({color:'#c5d294',transparent:true,opacity:.28});
  root.add(new LineSegments(hairGeometry,hairMaterial));
  root.userData={version:TOMATO_APPEARANCE_VERSION,scope:APPEARANCE_SCOPE};
  return {root,leafletCount:leaves.count,fruitCount:fruits.count,fruitBounds,
    trussFocus:trussViews[0]!,leafFocus:point(.05,1.28,.02),
    dispose(){root.removeFromParent();owned.forEach(g=>g.dispose());hairMaterial.dispose();}};
}
