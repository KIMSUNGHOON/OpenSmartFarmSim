import {describe,it,expect} from 'vitest';
import {readFileSync} from 'node:fs';
import {MeshStandardMaterial} from 'three';
import {createMorphologyGeometry} from './morphologyGeometry';

const frame=(i:number,scenario='with-removal')=>JSON.parse(readFileSync(new URL(`../public/leaf-lifecycle-replay/${scenario}/frame-${i}.json`,import.meta.url),'utf8'));
describe('lifecycle current-only geometry',()=>{
 it.each(['no-removal','with-removal'])('preserves12frame active areas and removes last/pending geometry for %s',scenario=>{
  const material=new MeshStandardMaterial();let states=0;
  for(let i=0;i<12;i++){
   const f=frame(i,scenario),plant=createMorphologyGeometry(f.stem,{stem:material,leaf:material},f.active_leaves);
   expect(plant.authoredLeafCount).toBe(f.active_leaf_count);const areas=plant.leafSurfaceAreas();states+=f.tracked_leaf_count;
   expect(areas).toHaveLength(f.active_leaf_count);
   areas.forEach((q,j)=>{expect(q.leaf_id).toBe(f.active_leaves[j].leaf_id);expect(q.attachment_internode_id).toBe(f.active_leaves[j].attachment_internode_id);
    expect(Math.abs(q.area_m2-f.active_leaves[j].area.value)/f.active_leaves[j].area.value).toBeLessThan(1e-9);});
   plant.dispose();
  }
  expect(states).toBe(47);material.dispose();
 });
 it('an explicit empty inventory has no leaf surfaces and retains original stems',()=>{
  const f=frame(11),material=new MeshStandardMaterial(),plant=createMorphologyGeometry(f.stem,{stem:material,leaf:material},[]);
  expect(plant.authoredLeafCount).toBe(0);expect(plant.leafSurfaceAreas()).toEqual([]);
  expect(plant.segments.map(s=>s.scale.y)).toEqual(f.stem.internodes.map((q:{length:{value:number}})=>q.length.value));
  plant.dispose();material.dispose();
 });
 it('retained leaves keep the same authored orientation after a different leaf is removed',()=>{
  const f=frame(11,'no-removal'),material=new MeshStandardMaterial();
  const all=createMorphologyGeometry(f.stem,{stem:material,leaf:material},f.active_leaves);
  const reduced=createMorphologyGeometry(f.stem,{stem:material,leaf:material},f.active_leaves.slice(1));
  const rotations=(plant:typeof all)=>plant.root.children.filter(q=>q.type==='Group').map(q=>q.rotation.y);
  expect(rotations(reduced)).toEqual(rotations(all).slice(1));all.dispose();reduced.dispose();material.dispose();
 });
});
