import { describe,it,expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { MeshStandardMaterial } from 'three';
import { createMorphologyGeometry,STORED_LEAF_AREA_MAPPING } from './morphologyGeometry';

const frame=(i:number)=>JSON.parse(readFileSync(new URL(`../public/leaf-area-replay/frame-${i}.json`,import.meta.url),'utf8'));
describe('stored square metres on authored leaf surfaces',()=>{
  it.each([0,11])('uses original per-leaf area, ID and stem attachment at frame %i',index=>{
    const f=frame(index),material=new MeshStandardMaterial(),plant=createMorphologyGeometry(f.stem,{stem:material,leaf:material},f.leaves);
    expect(STORED_LEAF_AREA_MAPPING).toBe('stored-leaf-m2-authored-blade-triangles-v1');
    const measured=plant.leafSurfaceAreas();expect(measured).toHaveLength(3);
    measured.forEach((leaf,i)=>{expect(leaf.leaf_id).toBe(f.leaves[i].leaf_id);
      expect(leaf.attachment_internode_id).toBe(f.leaves[i].attachment_internode_id);
      expect(Math.abs(leaf.area_m2-f.leaves[i].area.value)/f.leaves[i].area.value).toBeLessThan(1e-9);});
    expect(plant.segments.map(s=>s.scale.y)).toEqual(f.stem.internodes.map((n:{length:{value:number}})=>n.length.value));
    const seen=new Set<string>(),disposed=new Set<string>();plant.root.traverse(o=>{if('geometry' in o){
      const g=o.geometry as import('three').BufferGeometry;if(!seen.has(g.uuid)){seen.add(g.uuid);g.addEventListener('dispose',()=>disposed.add(g.uuid));}}});
    plant.dispose();expect(disposed).toEqual(seen);material.dispose();
  });
  it.each(['unknown','duplicate','unit','negative','infinite'])('holds %s leaf bindings',kind=>{
    const f=frame(0),material=new MeshStandardMaterial();
    if(kind==='unknown')f.leaves[0].attachment_internode_id='missing';
    if(kind==='duplicate')f.leaves[1].leaf_id=f.leaves[0].leaf_id;
    if(kind==='unit')f.leaves[0].area.unit='cm2';
    if(kind==='negative')f.leaves[0].area.value=-1;
    if(kind==='infinite')f.leaves[0].area.value=Infinity;
    expect(()=>createMorphologyGeometry(f.stem,{stem:material,leaf:material},f.leaves)).toThrow();material.dispose();
  });
});
