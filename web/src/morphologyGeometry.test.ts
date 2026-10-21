import { describe,it,expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { Box3,MeshStandardMaterial,Vector3 } from 'three';
import type { MorphologyFrame } from './morphologyReplay';
import { createMorphologyGeometry,MORPHOLOGY_MAPPING } from './morphologyGeometry';

describe('stored internode geometry',()=>{
  it('uses each original metre length and identity, with a fixed authored leaf count and releasable resources',()=>{
    const material=new MeshStandardMaterial();
    for(const index of [0,7,11]){
      const frame=JSON.parse(readFileSync(new URL(`../public/morphology-replay/frame-${index}.json`,import.meta.url),'utf8')) as MorphologyFrame;
      const plant=createMorphologyGeometry(frame,{stem:material,leaf:material});plant.root.updateMatrixWorld(true);
      expect(plant.root.userData.mapping).toBe(MORPHOLOGY_MAPPING);expect(plant.authoredLeafCount).toBe(3);
      expect(plant.segments).toHaveLength(frame.internodes.length);
      plant.segments.forEach((mesh,i)=>{
        const node=frame.internodes[i]!;expect(mesh.userData.internode_id).toBe(node.internode_id);
        expect(new Box3().setFromObject(mesh).getSize(new Vector3()).y).toBeCloseTo(node.length.value,14);
        expect([...mesh.geometry.getAttribute('position').array].every(Number.isFinite)).toBe(true);
      });
      const seen=new Set<string>(),disposed=new Set<string>();plant.root.traverse(o=>{
        if('geometry' in o){const geometry=o.geometry as import('three').BufferGeometry;
          if(!seen.has(geometry.uuid)){seen.add(geometry.uuid);geometry.addEventListener('dispose',()=>disposed.add(geometry.uuid));}}
      });plant.dispose();expect(disposed).toEqual(seen);
    }
    material.dispose();
  });
});
