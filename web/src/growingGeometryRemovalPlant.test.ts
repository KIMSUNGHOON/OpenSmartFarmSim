import {describe,expect,it} from 'vitest';
import {MeshBasicMaterial} from 'three';
import {readFileSync} from 'node:fs';
import {createGrowingGeometryRemovalPlant,GROWING_SCAFFOLD} from './growingGeometryPlant';
import type {GrowingGeometryRemovalFrame} from './growingGeometryRemovalReplay';
import {GROWING_GEOMETRY_REMOVAL_FIXTURE as FIXTURE} from './growingGeometryRemovalReplayFixture';

function frame(scenario:string,index:number):GrowingGeometryRemovalFrame{
 return JSON.parse(readFileSync(new URL(`../public/growing-geometry-removal-replay/${scenario}/frame-${index}.json`,import.meta.url),'utf8'));
}
describe('stored area on separate authored geometry',()=>{
 it.each(Object.keys(FIXTURE.scenarios))('maps all18frames/actual retained areas without changing source for %s',scenario=>{
  const material=new MeshBasicMaterial();
  for(let i=0;i<18;i++){
   const source=frame(scenario,i),before=structuredClone(source),plant=createGrowingGeometryRemovalPlant(source,{stem:material,leaf:material});
   expect(plant.root.userData.scaffold_version).toBe(GROWING_SCAFFOLD.version);
   expect(plant.root.userData.geometry_authority).toBe('stored_leaf_area');
   const measured=plant.leafSurfaceAreas();expect(measured.map(x=>x.leaf_id)).toEqual(source.leaf_ids);
   measured.forEach((x,j)=>expect(Math.abs(x.area_m2/source.leaves[j]!.area.value-1)).toBeLessThanOrEqual(5e-12));
   expect(plant.attachments()).toEqual(GROWING_SCAFFOLD.leaves.filter(leaf=>source.leaf_ids.includes(leaf.leaf_id)));expect(source).toEqual(before);plant.dispose();plant.dispose();
  }material.dispose();
 });
 it.each(['zero','negative','nonfinite','unit','missing','duplicate','foreign'])('rejects invalid bindings: %s',kind=>{
  const source=frame('case-0-remove-1',0),material=new MeshBasicMaterial();
  if(kind==='zero')source.leaves[0]!.area.value=0;
  if(kind==='negative')source.leaves[0]!.area.value=-1;
  if(kind==='nonfinite')source.leaves[0]!.area.value=Infinity;
  if(kind==='unit')source.leaves[0]!.area.unit='cm2';
  if(kind==='missing')source.leaves.pop();
  if(kind==='duplicate')source.leaves[1]!.leaf_id=source.leaves[0]!.leaf_id;
  if(kind==='foreign')source.leaves[0]!.leaf_id='unknown';
  expect(()=>createGrowingGeometryRemovalPlant(source,{stem:material,leaf:material})).toThrow();material.dispose();
 });
 it('disposes its geometry but preserves borrowed materials',()=>{
  const material=new MeshBasicMaterial(),plant=createGrowingGeometryRemovalPlant(frame('case-0-remove-1',0),{stem:material,leaf:material});let disposed=0,materials=0;
  plant.root.traverse(node=>{if('geometry'in node)(node.geometry as import('three').BufferGeometry).addEventListener('dispose',()=>disposed++);});
  material.addEventListener('dispose',()=>materials++);plant.dispose();expect(disposed).toBeGreaterThan(0);expect(materials).toBe(0);material.dispose();
 });
 it('keeps captured IDs and areas when the caller later changes its copy',()=>{
  const source=frame('case-0-remove-1',0),material=new MeshBasicMaterial(),plant=createGrowingGeometryRemovalPlant(source,{stem:material,leaf:material}),old=plant.leafSurfaceAreas();
  source.leaves[0]!.leaf_id='changed';source.leaves[0]!.area.value=0;expect(plant.leafSurfaceAreas()).toEqual(old);plant.dispose();material.dispose();
 });
});

it.each(Object.keys(FIXTURE.scenarios))('retains original attachment IDs and positions across the point for %s',scenario=>{
 const material=new MeshBasicMaterial(),before=createGrowingGeometryRemovalPlant(frame(scenario,7),{stem:material,leaf:material}),after=createGrowingGeometryRemovalPlant(frame(scenario,8),{stem:material,leaf:material});
 expect(frame(scenario,7).at).toEqual(frame(scenario,8).at);
 expect(after.attachments()).toEqual(before.attachments().filter(leaf=>frame(scenario,8).leaf_ids.includes(leaf.leaf_id)));
 expect(after.attachments()[0]).toEqual(GROWING_SCAFFOLD.leaves[1]);
 before.dispose();after.dispose();material.dispose();
});
it.each(['unknown-phase','empty','reordered','after-with-three'])('rejects a wrong original subset: %s',kind=>{
 const source=frame('case-0-remove-1',8),material=new MeshBasicMaterial();
 if(kind==='unknown-phase')Reflect.set(source,'phase','unknown');
 if(kind==='empty'){source.leaves=[];source.leaf_ids=[];}
 if(kind==='reordered'){source.leaves.reverse();source.leaf_ids.reverse();}
 if(kind==='after-with-three'){const initial=frame('case-0-remove-1',0);source.leaves=initial.leaves;source.leaf_ids=initial.leaf_ids;}
 expect(()=>createGrowingGeometryRemovalPlant(source,{stem:material,leaf:material})).toThrow();material.dispose();
});
