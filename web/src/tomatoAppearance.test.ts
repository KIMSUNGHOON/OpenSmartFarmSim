import { describe,it,expect } from 'vitest';
import { Box3,Mesh,MeshStandardMaterial,Vector3 } from 'three';
import { createTomatoAppearance,tomatoFruitGeometry,tomatoLeafletGeometry,APPEARANCE_SCOPE } from './tomatoAppearance';

describe('authored tomato appearance (not a crop prediction)',()=>{
  it('has curved finite leaflet surfaces with texture coordinates and a toothed outline',()=>{
    const g=tomatoLeafletGeometry(),p=g.getAttribute('position');
    expect(g.getAttribute('uv').count).toBe(p.count);
    expect([...p.array].every(Number.isFinite)).toBe(true);
    expect([...g.getAttribute('normal').array].every(Number.isFinite)).toBe(true);
    g.computeBoundingBox();expect(g.boundingBox!.min.z).toBeLessThan(-.1);
    expect(g.index!.count).toBeGreaterThan(1000);g.dispose();
  });
  it('retains a three-dimensional fruit surface and finite normals at the stem depression',()=>{
    const g=tomatoFruitGeometry();g.computeBoundingBox();
    expect([...g.getAttribute('normal').array].every(Number.isFinite)).toBe(true);
    expect(g.boundingBox!.max.y).toBeLessThan(1);
    expect(g.boundingBox!.getSize(new Vector3()).z).toBeGreaterThan(1.9);g.dispose();
  });
  it('builds a finite plant with attached authored organs, explicit scope and releasable geometry',()=>{
    const material=new MeshStandardMaterial(),plant=createTomatoAppearance({leaf:material,stem:material,fruit:material,calyx:material,flower:material});
    expect(plant.root.userData.scope).toBe(APPEARANCE_SCOPE);expect(plant.leafletCount).toBeGreaterThan(60);
    expect(plant.fruitCount).toBeGreaterThan(0);
    for(let i=0;i<plant.fruitBounds.length;i++)for(let j=i+1;j<plant.fruitBounds.length;j++){
      const a=plant.fruitBounds[i]!,b=plant.fruitBounds[j]!;
      expect(a.center.distanceTo(b.center)).toBeGreaterThan(a.radius+b.radius);
    }
    const size=new Box3().setFromObject(plant.root).getSize(new Vector3());
    expect([size.x,size.y,size.z].every(x=>Number.isFinite(x)&&x>0)).toBe(true);
    const disposed=new Set<string>();plant.root.traverse(object=>{if(object instanceof Mesh)
      object.geometry.addEventListener('dispose',()=>disposed.add(object.geometry.uuid));});
    plant.dispose();expect(disposed.size).toBeGreaterThanOrEqual(5);material.dispose();
  });
});
