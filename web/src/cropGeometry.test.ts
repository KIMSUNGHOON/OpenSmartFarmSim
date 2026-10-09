import { describe,it,expect } from 'vitest';
import { MeshBasicMaterial,Vector3 } from 'three';
import { createCanopy,maximumCarbon,carbonHeights } from './cropGeometry';
import { decodeCropReplay,STORES } from './cropReplay';
import { cropReferenceResponse,cropReferenceSelection } from '../e2e/crop-fixture';

describe('schematic geometry represents saved quantities',()=>{
  it.each([0,0.000001,0.1161888,1,3,10,1e6])('measures actual triangle surface at LAI %s',lai=>{
    const material=new MeshBasicMaterial();const canopy=createCanopy(material);
    try{
      canopy.update(lai);canopy.group.updateMatrixWorld(true);
      let total=0;
      for(const mesh of canopy.patches){
        if(!mesh.visible)continue;
        const positions=mesh.geometry.getAttribute('position'),indices=mesh.geometry.index!;
        for(let i=0;i<indices.count;i+=3){
          const a=new Vector3().fromBufferAttribute(positions,indices.getX(i)).applyMatrix4(mesh.matrixWorld);
          const b=new Vector3().fromBufferAttribute(positions,indices.getX(i+1)).applyMatrix4(mesh.matrixWorld);
          const c=new Vector3().fromBufferAttribute(positions,indices.getX(i+2)).applyMatrix4(mesh.matrixWorld);
          total+=b.sub(a).cross(c.sub(a)).length()/2;
        }
      }
      expect(Math.abs(total-lai)).toBeLessThanOrEqual(Math.max(1e-8,lai*1e-6));
      expect(canopy.area()).toBeCloseTo(total,8);
      expect(canopy.patches.every(p=>p.visible===Boolean(lai))).toBe(true);
    }finally{canopy.dispose();material.dispose();}
  });
  it('uses each actual saved frame, including the input removal, without fabricated growth',()=>{
    const replay=decodeCropReplay(cropReferenceResponse(),cropReferenceSelection);
    const material=new MeshBasicMaterial(),canopy=createCanopy(material),maximum=maximumCarbon(replay.samples);
    try{
      expect(maximum).toBe(20000);
      for(const sample of replay.samples){
        canopy.update(sample.lai.value);
        expect(Math.abs(canopy.area()-sample.lai.value)).toBeLessThan(1e-8);
        const heights=carbonHeights(sample,maximum);
        for(const store of STORES)expect(heights[store]*maximum).toBeCloseTo(sample.state[store].value,8);
      }
      expect(replay.samples[3]!.lai.value).toBeLessThan(replay.samples[2]!.lai.value);
    }finally{canopy.dispose();material.dispose();}
  });
  it.each([-1,NaN,Infinity,1e6+1])('keeps unsafe geometric inputs out of the GPU: %s',value=>{
    const material=new MeshBasicMaterial(),canopy=createCanopy(material);
    try{expect(()=>canopy.update(value)).toThrow('crop_scene_unavailable');}
    finally{canopy.dispose();material.dispose();}
  });
  it('zero carbon has zero bar height and uses no artificial minimum',()=>{
    const sample=structuredClone(decodeCropReplay(cropReferenceResponse(),cropReferenceSelection).samples[0]!);
    for(const store of STORES)(sample.state[store] as {value:number}).value=0;
    expect(maximumCarbon([sample])).toBe(0);
    expect(carbonHeights(sample,0)).toEqual({leaf:0,stem_root:0,fruit:0,buffer:0});
  });
});
