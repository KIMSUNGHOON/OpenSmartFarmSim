import { LAI_UNIT,type CropReplay } from './cropReplay';

export const TOMATO_LEAF_MAPPING='stored-lai-relative-area-v1';
export type TomatoLeafBinding=Readonly<{mapping:typeof TOMATO_LEAF_MAPPING;result_id:string;at:string;
  lai:number;reference_lai:number;area_ratio:number;payload_sha256:string;
  scope:'synthetic_crop_math_only';gates:'not_assessed'}>;

export function tomatoLeafBinding(replay:CropReplay,index:number):TomatoLeafBinding|null {
  if(replay.status!=='completed'||!Number.isSafeInteger(index)||index<0||index>=replay.samples.length
    ||replay.claim_scope!=='synthetic_crop_math_only'||replay.gates!=='not_assessed'
    ||replay.normalization!=='per_m2_floor')return null;
  let reference=0;
  for(const point of replay.samples){
    if(point.lai.unit!==LAI_UNIT||!Number.isFinite(point.lai.value)||point.lai.value<0)return null;
    reference=Math.max(reference,point.lai.value);
  }
  const sample=replay.samples[index]!;
  return {mapping:TOMATO_LEAF_MAPPING,result_id:replay.result_id,at:sample.at,lai:sample.lai.value,
    reference_lai:reference,area_ratio:reference===0?0:sample.lai.value/reference,
    payload_sha256:replay.manifest.payload_sha256,scope:replay.claim_scope,gates:replay.gates};
}
