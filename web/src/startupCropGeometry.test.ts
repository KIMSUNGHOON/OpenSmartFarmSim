import { describe,it,expect } from 'vitest';
import { MeshBasicMaterial } from 'three';
import { startupCohortScales,coupledCohortHeights,createCohortDiagrams } from './coupledCropGeometry';
import { startupReference } from '../e2e/startup-crop-fixture';
import { decodeStartupCropPage } from './startupCropReplay';

function saved(kind:Parameters<typeof startupReference>[0]='empty-entry'){
  const data=startupReference(kind);return decodeStartupCropPage(data,{result_id:data.result_id,...data.farm});
}
function uniform(value:number){
  const row=saved().samples[0]!;return {...row,state:{...row.state,
    fruit_carbohydrate:row.state.fruit_carbohydrate.map(q=>({...q,value})),
    fruit_number:row.state.fruit_number.map(q=>({...q,value}))}};
}

describe('startup logarithmic display without changing saved quantities',()=>{
  it('keeps actual empty-entry tiny cohorts positive and Float32 representable',()=>{
    const data=saved(),scales=startupCohortScales(data.samples);
    for(const row of data.samples){
      const heights=coupledCohortHeights(row.state,scales);
      for(const [kind,key] of [['carbon','fruit_carbohydrate'],['number','fruit_number']] as const)
        for(const [i,q] of row.state[key].entries()){
          const bound=scales.logarithmic[kind],h=heights[kind][i]!;
          expect(h).toBe(q.value===0?0:(Math.log10(q.value)-bound!.lower)/(bound!.upper-bound!.lower));
          expect(h>=0 && h<=1).toBe(true);expect(q.value===0 || Math.fround(h)>0).toBe(true);
        }
    }
  });
  it('stores the original C/N in the actual mesh and hides removed zeros before reentry',()=>{
    const data=saved('full-removal-reentry'),scales=startupCohortScales(data.samples);
    const material=new MeshBasicMaterial(),diagram=createCohortDiagrams(material,material);
    try{for(const row of data.samples){
      diagram.update(row.state,scales);
      for(const [kind,key] of [['carbon','fruit_carbohydrate'],['number','fruit_number']] as const)
        for(const [i,q] of row.state[key].entries()){
          const mesh=diagram[kind][i]!;expect(mesh.userData.value).toBe(q.value);expect(mesh.userData.unit).toBe(q.unit);
          expect(mesh.visible).toBe(q.value>0);expect(mesh.position.y).toBe(mesh.scale.y/2);
          if(q.value>0)expect(Math.fround(mesh.scale.y)).toBeGreaterThan(0);
        }
    }}finally{diagram.dispose();material.dispose();}
  });
  it.each([0,Number.MIN_VALUE,1,Number.MAX_VALUE])('handles constant value %s without seed or overflow',value=>{
    const row=uniform(value);
    const scales=startupCohortScales([row]),heights=coupledCohortHeights(row.state,scales);
    for(const kind of ['carbon','number'] as const){
      if(value===0){expect(scales.logarithmic[kind]).toBeNull();expect(heights[kind]).toEqual(Array(50).fill(0));}
      else expect(heights[kind].every(h=>h>0 && h<=1 && Math.fround(h)>0)).toBe(true);
    }
  });
  it('keeps separate bounds fixed across all saved frames and validates out of range values',()=>{
    const a=uniform(0),b=uniform(0);
    a.state.fruit_carbohydrate[0]!.value=Number.MIN_VALUE;b.state.fruit_carbohydrate[0]!.value=Number.MAX_VALUE;
    a.state.fruit_number[0]!.value=1e-200;b.state.fruit_number[0]!.value=1;
    const scales=startupCohortScales([a,b]);expect(scales.logarithmic.carbon).toEqual({lower:-325,upper:309});
    expect(scales.logarithmic.number).toEqual({lower:-201,upper:0});
    for(const row of [a,b])expect(()=>coupledCohortHeights(row.state,scales)).not.toThrow();
    const bad={...scales,logarithmic:{...scales.logarithmic,number:{lower:0,upper:0}}};
    expect(()=>coupledCohortHeights(a.state,bad)).toThrow('crop_scene_unavailable');
  });
});
