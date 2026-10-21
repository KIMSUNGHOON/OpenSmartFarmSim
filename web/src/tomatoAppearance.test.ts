import { describe,it,expect } from 'vitest';
import { Box3,Mesh,InstancedMesh,Matrix4,MeshStandardMaterial,Triangle,Vector3 } from 'three';
import { createTomatoAppearance,tomatoFruitGeometry,tomatoLeafletGeometry,APPEARANCE_SCOPE } from './tomatoAppearance';

describe('authored tomato appearance (not a crop prediction)',()=>{
  it('scales actual leaflet triangles by stored area ratio while keeping the authored leaf bases fixed',()=>{
    const leaf=new MeshStandardMaterial(),other=new MeshStandardMaterial();
    const plant=createTomatoAppearance({leaf,stem:other,fruit:other,calyx:other,flower:other});
    const leaves=plant.root.children.find(x=>x instanceof InstancedMesh&&x.material===leaf) as InstancedMesh;
    function area(){
      if(!leaves.visible)return 0;
      const p=leaves.geometry.getAttribute('position'),idx=leaves.geometry.index!,matrix=new Matrix4();
      const a=new Vector3(),b=new Vector3(),c=new Vector3(),t=new Triangle(a,b,c);let total=0;
      for(let k=0;k<leaves.count;k++){
        leaves.getMatrixAt(k,matrix);
        for(let i=0;i<idx.count;i+=3){a.fromBufferAttribute(p,idx.getX(i)).applyMatrix4(matrix);
          b.fromBufferAttribute(p,idx.getX(i+1)).applyMatrix4(matrix);c.fromBufferAttribute(p,idx.getX(i+2)).applyMatrix4(matrix);total+=t.getArea();}
      }
      return total;
    }
    const initial=area(),before=new Matrix4();leaves.getMatrixAt(3,before);
    plant.setLeafAreaRatio(.25);
    expect(area()/initial).toBeCloseTo(.25,6);
    const after=new Matrix4();leaves.getMatrixAt(3,after);
    expect(after.elements.slice(12,15)).toEqual(before.elements.slice(12,15));
    for(const object of plant.root.children)if(object instanceof InstancedMesh&&object.material===other)expect(object.visible).toBe(false);
    plant.setLeafAreaRatio(0);expect(area()).toBe(0);
    plant.setLeafAreaRatio(1);expect(area()/initial).toBeCloseTo(1,6);
    for(const ratio of [-1,1.1,Infinity,NaN])expect(()=>plant.setLeafAreaRatio(ratio)).toThrow();
    plant.setLeafAreaRatio(null);expect(area()/initial).toBeCloseTo(1,6);
    for(const object of plant.root.children)if(object instanceof InstancedMesh&&object.material===other)expect(object.visible).toBe(true);
    plant.dispose();leaf.dispose();other.dispose();
  });
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
