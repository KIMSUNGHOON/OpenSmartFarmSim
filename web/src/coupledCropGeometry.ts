import { BoxGeometry,Group,Mesh,type Material } from 'three';
import { CARBON_UNIT } from './cropReplay';
import { FRUIT_NUMBER_UNIT,type CoupledCropState,type CoupledCropSample } from './coupledCropReplay';

export type CohortScales=Readonly<{carbon:number;number:number}>;
type Heights=Readonly<{carbon:readonly number[];number:readonly number[]}>;
function need(value:unknown):asserts value {if(!value)throw new Error('crop_scene_unavailable');}
function quantities(state:CoupledCropState){
  for(const [values,unit] of [[state.fruit_carbohydrate,CARBON_UNIT],[state.fruit_number,FRUIT_NUMBER_UNIT]] as const){
    need(Array.isArray(values) && values.length===50);
    for(const q of values)need(q && q.unit===unit && Number.isFinite(q.value) && q.value>=0);
  }
}
export function coupledCohortScales(samples:readonly Pick<CoupledCropSample,'state'>[]):CohortScales{
  let carbon=0,number=0;
  for(const sample of samples){
    quantities(sample.state);
    for(const q of sample.state.fruit_carbohydrate)carbon=Math.max(carbon,q.value);
    for(const q of sample.state.fruit_number)number=Math.max(number,q.value);
  }
  return {carbon,number};
}
export function coupledCohortHeights(state:CoupledCropState,scales:CohortScales):Heights{
  quantities(state);
  function heights(values:readonly {value:number}[],maximum:number){
    need(Number.isFinite(maximum) && maximum>=0);
    return values.map(({value})=>{
      need(value<=maximum);
      const height=maximum?value/maximum:0;
      // GPU transform precision is a representation bound, not a crop threshold.
      need(Number.isFinite(height) && height>=0 && height<=1 && (value===0 || height>0 && Math.fround(height)>0));
      return height;
    });
  }
  return {carbon:heights(state.fruit_carbohydrate,scales.carbon),number:heights(state.fruit_number,scales.number)};
}
export function createCohortDiagrams(carbonMaterial:Material,numberMaterial:Material){
  const group=new Group(),carbonGroup=new Group(),numberGroup=new Group(),geometry=new BoxGeometry(.07,1,.07);
  numberGroup.position.x=1.4;group.add(carbonGroup,numberGroup);
  function bars(parent:Group,material:Material,unit:string){
    return Array.from({length:50},(_,i)=>{
      const mesh=new Mesh(geometry,material);
      mesh.position.set((i%10-4.5)*.1,0,(Math.floor(i/10)-2)*.14);
      mesh.scale.y=0;mesh.visible=false;mesh.userData={cohortIndex:i+1,unit,value:0};parent.add(mesh);return mesh;
    });
  }
  const carbon=bars(carbonGroup,carbonMaterial,CARBON_UNIT),number=bars(numberGroup,numberMaterial,FRUIT_NUMBER_UNIT);
  let disposed=false;
  return {group,carbon,number,
    update(state:CoupledCropState,scales:CohortScales){
      need(!disposed);const heights=coupledCohortHeights(state,scales);
      for(const [meshes,values,ratios] of [[carbon,state.fruit_carbohydrate,heights.carbon],
        [number,state.fruit_number,heights.number]] as const){
        for(const [i,mesh] of meshes.entries()){
          const height=ratios[i]!;mesh.scale.y=height;mesh.position.y=height/2;
          mesh.visible=height>0;mesh.userData.value=values[i]!.value;
        }
      }
      group.updateMatrixWorld(true);
    },
    dispose(){
      if(disposed)return;disposed=true;group.removeFromParent();carbonGroup.clear();numberGroup.clear();group.clear();geometry.dispose();
    }
  };
}
