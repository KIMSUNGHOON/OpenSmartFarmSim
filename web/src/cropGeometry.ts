import { CircleGeometry,Group,Mesh,Triangle,Vector3,type Material } from 'three';
import { STORES,type CropSample,type Store } from './cropReplay';

function surfaceArea(mesh:Mesh<CircleGeometry>){
  const positions=mesh.geometry.getAttribute('position'),indices=mesh.geometry.index;
  if(!indices)throw new Error('crop_scene_unavailable');
  const a=new Vector3(),b=new Vector3(),c=new Vector3(),triangle=new Triangle(a,b,c);
  let total=0;
  for(let i=0;i<indices.count;i+=3){
    a.fromBufferAttribute(positions,indices.getX(i)).applyMatrix4(mesh.matrixWorld);
    b.fromBufferAttribute(positions,indices.getX(i+1)).applyMatrix4(mesh.matrixWorld);
    c.fromBufferAttribute(positions,indices.getX(i+2)).applyMatrix4(mesh.matrixWorld);
    total+=triangle.getArea();
  }
  return total;
}

export function createCanopy(material:Material){
  const group=new Group(),geometry=new CircleGeometry(1,64);
  const patches:Mesh<CircleGeometry>[]=[];
  for(let i=0;i<8;i++){
    const patch=new Mesh(geometry,material);
    patch.position.set((i%4-1.5)*0.22,0.23+Math.floor(i/4)*0.19,(Math.floor(i/4)-0.5)*0.38);
    patch.rotation.set(-Math.PI/2+(i%2?0.12:-0.12),0,(i%4-1.5)*0.16);
    group.add(patch);patches.push(patch);
  }
  const reference=new Mesh(geometry,material);reference.updateMatrixWorld(true);
  const unitArea=surfaceArea(reference);
  return {group,patches,
    update(lai:number){
      // This is a GPU representation bound, not a crop applicability threshold.
      if(!Number.isFinite(lai) || lai<0 || lai>1e6)throw new Error('crop_scene_unavailable');
      const scale=Math.sqrt(lai/(patches.length*unitArea)),aspect=Math.sqrt(1.8);
      for(const patch of patches){patch.visible=lai>0;patch.scale.set(scale*aspect,scale/aspect,1);}
      group.updateMatrixWorld(true);
    },
    area(){group.updateMatrixWorld(true);return patches.reduce((sum,patch)=>sum+(patch.visible?surfaceArea(patch):0),0);},
    dispose(){geometry.dispose();}
  };
}

export function maximumCarbon(samples:readonly CropSample[]){
  let maximum=0;
  for(const sample of samples)for(const store of STORES)maximum=Math.max(maximum,sample.state[store].value);
  return maximum;
}
export function carbonHeights(sample:CropSample,maximum:number):Record<Store,number>{
  return {leaf:maximum?sample.state.leaf.value/maximum:0,
    stem_root:maximum?sample.state.stem_root.value/maximum:0,
    fruit:maximum?sample.state.fruit.value/maximum:0,buffer:maximum?sample.state.buffer.value/maximum:0};
}
