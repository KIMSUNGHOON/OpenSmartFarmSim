import { describe,it,expect,vi } from 'vitest';
import { MeshBasicMaterial,Vector3 } from 'three';
import { coupledCohortScales,coupledCohortHeights,createCohortDiagrams } from './coupledCropGeometry';
import { FRUIT_NUMBER_UNIT,type CoupledCropState } from './coupledCropReplay';
import { CARBON_UNIT } from './cropReplay';

function state(c:(index:number)=>number,n:(index:number)=>number):CoupledCropState{
  const q=(value:number,unit:typeof CARBON_UNIT)=>({value,unit});
  return {buffer:q(0,CARBON_UNIT),leaf:q(0,CARBON_UNIT),stem_root:q(0,CARBON_UNIT),
    temperature_filtered_24h:{value:20,unit:'degC'},temperature_sum:{value:0,unit:'degC_day'},
    fruit_carbohydrate:Array.from({length:50},(_,i)=>q(c(i),CARBON_UNIT)),
    fruit_number:Array.from({length:50},(_,i)=>({value:n(i),unit:FRUIT_NUMBER_UNIT}))};
}

describe('separate cohort carbon and equivalent-number diagrams',()=>{
  it('uses separate fixed maxima over every saved state without mixing units',()=>{
    const a={state:state(i=>i+1,i=>(i+1)/100)},b={state:state(i=>100-i,i=>(50-i)/10)};
    const scales=coupledCohortScales([a,b]);expect(scales).toEqual({carbon:100,number:5});
    const heights=coupledCohortHeights(a.state,scales);
    expect(heights.carbon).toHaveLength(50);expect(heights.number).toHaveLength(50);
    for(let i=0;i<50;i++){
      expect(heights.carbon[i]!*scales.carbon).toBeCloseTo(a.state.fruit_carbohydrate[i]!.value,10);
      expect(heights.number[i]!*scales.number).toBeCloseTo(a.state.fruit_number[i]!.value,10);
    }
  });
  it('actual transformed mesh height and slot index preserve selected saved values',()=>{
    const carbonMaterial=new MeshBasicMaterial(),numberMaterial=new MeshBasicMaterial();
    const a=state(i=>i+1,i=>(50-i)/10),b=state(i=>i+51,i=>(i+1)/5),scales=coupledCohortScales([{state:a},{state:b}]);
    const diagram=createCohortDiagrams(carbonMaterial,numberMaterial);
    try{
      for(const selected of [a,b,a]){
        diagram.update(selected,scales);diagram.group.updateMatrixWorld(true);
        for(const [key,bars,quantities] of [['carbon',diagram.carbon,a.fruit_carbohydrate],
          ['number',diagram.number,a.fruit_number]] as const){
          const actual=key==='carbon'?selected.fruit_carbohydrate:selected.fruit_number;
          expect(bars).toHaveLength(quantities.length);
          for(const [i,bar] of bars.entries()){
            const bottom=new Vector3(0,-.5,0).applyMatrix4(bar.matrixWorld),top=new Vector3(0,.5,0).applyMatrix4(bar.matrixWorld);
            expect((top.y-bottom.y)*scales[key]).toBeCloseTo(actual[i]!.value,10);
            expect(bottom.y).toBeCloseTo(0,14);expect(bar.userData.cohortIndex).toBe(i+1);
            expect(bar.userData.value).toBe(actual[i]!.value);expect(bar.userData.unit).toBe(actual[i]!.unit);
          }
        }
      }
      expect(diagram.carbon[0]!.geometry).toBe(diagram.carbon[49]!.geometry);
      expect(diagram.carbon[0]!.geometry).toBe(diagram.number[49]!.geometry);
      expect(diagram.carbon[0]!.material).toBe(carbonMaterial);expect(diagram.number[0]!.material).toBe(numberMaterial);
    }finally{diagram.dispose();carbonMaterial.dispose();numberMaterial.dispose();}
  });
  it('all zero quantities have hidden zero-height meshes and no arbitrary minimum',()=>{
    const s=state(()=>0,()=>0),scales=coupledCohortScales([{state:s}]);
    expect(scales).toEqual({carbon:0,number:0});expect(coupledCohortHeights(s,scales)).toEqual({carbon:Array(50).fill(0),number:Array(50).fill(0)});
    const material=new MeshBasicMaterial(),diagram=createCohortDiagrams(material,material);
    try{diagram.update(s,scales);expect([...diagram.carbon,...diagram.number].every(b=>!b.visible && b.scale.y===0 && b.userData.value===0)).toBe(true);}
    finally{diagram.dispose();material.dispose();}
  });
  it('finite enormous values use a ratio without overflow or derived mass',()=>{
    const s=state(()=>Number.MAX_VALUE,()=>Number.MAX_VALUE),scales=coupledCohortScales([{state:s}]);
    expect(coupledCohortHeights(s,scales)).toEqual({carbon:Array(50).fill(1),number:Array(50).fill(1)});
  });
  it.each(['negative','infinite','nan','length','unit','max_zero','max_negative','max_small','max_infinite','underflow','gpu_underflow'])
    ('rejects %s for text/table fallback rather than fabricated height',fault=>{
      const s=structuredClone(state(()=>1,()=>1)) as any,scales={carbon:1,number:1};
      if(fault==='negative')s.fruit_carbohydrate[0].value=-1;
      if(fault==='infinite')s.fruit_number[0].value=Infinity;
      if(fault==='nan')s.fruit_number[0].value=NaN;
      if(fault==='length')s.fruit_number.pop();
      if(fault==='unit')s.fruit_carbohydrate[0].unit=FRUIT_NUMBER_UNIT;
      if(fault==='max_zero')scales.carbon=0;
      if(fault==='max_negative')scales.number=-1;
      if(fault==='max_small')scales.carbon=.5;
      if(fault==='max_infinite')scales.number=Infinity;
      if(fault==='underflow'){s.fruit_number[0].value=Number.MIN_VALUE;scales.number=Number.MAX_VALUE;}
      if(fault==='gpu_underflow'){s.fruit_carbohydrate[0].value=1e-50;}
      expect(()=>coupledCohortHeights(s,scales)).toThrow('crop_scene_unavailable');
    });
  it('failed update keeps the previously confirmed geometry untouched',()=>{
    const material=new MeshBasicMaterial(),diagram=createCohortDiagrams(material,material),s=state(()=>1,()=>2);
    try{
      diagram.update(s,{carbon:2,number:4});const before=[...diagram.carbon,...diagram.number].map(b=>b.scale.y);
      expect(()=>diagram.update(s,{carbon:2,number:0})).toThrow('crop_scene_unavailable');
      expect([...diagram.carbon,...diagram.number].map(b=>b.scale.y)).toEqual(before);
    }finally{diagram.dispose();material.dispose();}
  });
  it('disposes its shared geometry once and leaves caller materials to the owner',()=>{
    const material=new MeshBasicMaterial(),diagram=createCohortDiagrams(material,material);
    const geometryDispose=vi.spyOn(diagram.carbon[0]!.geometry,'dispose'),materialDispose=vi.spyOn(material,'dispose');
    diagram.dispose();diagram.dispose();expect(geometryDispose).toHaveBeenCalledTimes(1);expect(materialDispose).not.toHaveBeenCalled();
    expect(diagram.group.children).toHaveLength(0);expect(()=>diagram.update(state(()=>1,()=>1),{carbon:1,number:1})).toThrow('crop_scene_unavailable');
    material.dispose();
  });
});
