import {describe,expect,it} from 'vitest';
import {MeshBasicMaterial} from 'three';
import {readFileSync} from 'node:fs';
import {createLeafCarbonStockPlant,GROWING_SCAFFOLD} from './growingGeometryPlant';
import type {LeafCarbonStockFrame} from './leafCarbonStockReplay';
import {LEAF_CARBON_STOCK_FIXTURE as FIXTURE} from './leafCarbonStockReplayFixture';

function frame(scenario:string,index:number):LeafCarbonStockFrame{
 return JSON.parse(readFileSync(new URL(`../public/leaf-carbon-stock-replay/${scenario}/frame-${index}.json`,import.meta.url),'utf8'));
}
describe('stored area on separate authored geometry',()=>{
 it.each(Object.keys(FIXTURE.scenarios))('maps all17frames/51areas without changing source for %s',scenario=>{
  const material=new MeshBasicMaterial();
  for(let i=0;i<17;i++){
   const source=frame(scenario,i),before=structuredClone(source),plant=createLeafCarbonStockPlant(source,{stem:material,leaf:material});
   expect(plant.root.userData.scaffold_version).toBe(GROWING_SCAFFOLD.version);
   expect(plant.root.userData.geometry_authority).toBe('stored_leaf_area');
   const measured=plant.leafSurfaceAreas();expect(measured.map(x=>x.leaf_id)).toEqual(source.leaf_ids);
   measured.forEach((x,j)=>expect(Math.abs(x.area_m2/source.leaves[j]!.area.value-1)).toBeLessThanOrEqual(5e-12));
   expect(plant.leafCarbonStocks()).toEqual(source.leaves.map(leaf=>({leaf_id:leaf.leaf_id,carbon:leaf.carbon})));expect(plant.attachments()).toEqual(GROWING_SCAFFOLD.leaves);expect(source).toEqual(before);plant.dispose();plant.dispose();
  }material.dispose();
 });
 it.each(['zero','negative','nonfinite','unit','missing','duplicate','foreign'])('rejects invalid bindings: %s',kind=>{
  const source=frame('warm-day-individual-stock',0),material=new MeshBasicMaterial();
  if(kind==='zero')source.leaves[0]!.area.value=0;
  if(kind==='negative')source.leaves[0]!.area.value=-1;
  if(kind==='nonfinite')source.leaves[0]!.area.value=Infinity;
  if(kind==='unit')source.leaves[0]!.area.unit='cm2';
  if(kind==='missing')source.leaves.pop();
  if(kind==='duplicate')source.leaves[1]!.leaf_id=source.leaves[0]!.leaf_id;
  if(kind==='foreign')source.leaves[0]!.leaf_id='unknown';
  expect(()=>createLeafCarbonStockPlant(source,{stem:material,leaf:material})).toThrow();material.dispose();
 });
 it('disposes its geometry but preserves borrowed materials',()=>{
  const material=new MeshBasicMaterial(),plant=createLeafCarbonStockPlant(frame('warm-day-individual-stock',0),{stem:material,leaf:material});let disposed=0,materials=0;
  plant.root.traverse(node=>{if('geometry'in node)(node.geometry as import('three').BufferGeometry).addEventListener('dispose',()=>disposed++);});
  material.addEventListener('dispose',()=>materials++);plant.dispose();expect(disposed).toBeGreaterThan(0);expect(materials).toBe(0);material.dispose();
 });
 it('keeps captured IDs and areas when the caller later changes its copy',()=>{
  const source=frame('warm-day-individual-stock',0),material=new MeshBasicMaterial(),plant=createLeafCarbonStockPlant(source,{stem:material,leaf:material}),old=plant.leafSurfaceAreas();
  source.leaves[0]!.leaf_id='changed';source.leaves[0]!.area.value=0;expect(plant.leafSurfaceAreas()).toEqual(old);plant.dispose();material.dispose();
 });
});


it('carbon changes do not change the authored pose or actual area triangles',()=>{
 const first=frame('warm-day-individual-stock',0),second=structuredClone(first),material=new MeshBasicMaterial();
 second.leaves.forEach((l,i)=>l.carbon.value=1e5*(i+1));
 const a=createLeafCarbonStockPlant(first,{stem:material,leaf:material}),b=createLeafCarbonStockPlant(second,{stem:material,leaf:material});
 expect(a.leafSurfaceAreas()).toEqual(b.leafSurfaceAreas());expect(a.attachments()).toEqual(b.attachments());
 expect(a.leafCarbonStocks()).not.toEqual(b.leafCarbonStocks());a.dispose();b.dispose();material.dispose();
});
it.each(['negative','nonfinite','unit'])('rejects invalid captured carbon: %s',kind=>{
 const source=frame('warm-day-individual-stock',0),material=new MeshBasicMaterial();
 if(kind==='negative')source.leaves[0]!.carbon.value=-1;
 if(kind==='nonfinite')source.leaves[0]!.carbon.value=Infinity;
 if(kind==='unit')source.leaves[0]!.carbon.unit='mg_CH2O';
 expect(()=>createLeafCarbonStockPlant(source,{stem:material,leaf:material})).toThrow();material.dispose();
});
it('captures independent carbon copies and closes them when disposed',()=>{
 const source=frame('warm-day-individual-stock',0),material=new MeshBasicMaterial(),p=createLeafCarbonStockPlant(source,{stem:material,leaf:material}),captured=p.leafCarbonStocks();
 source.leaves[0]!.carbon.value=-1;const copy=p.leafCarbonStocks();copy[0]!.carbon.value=0;
 expect(p.leafCarbonStocks()).toEqual(captured);p.dispose();p.dispose();expect(()=>p.leafCarbonStocks()).toThrow();material.dispose();
});
