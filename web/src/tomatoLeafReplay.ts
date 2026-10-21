import { LAI_UNIT,type CropReplay } from './cropReplay';
import type { CycleCropSummaryResponse } from './cycleCropReplay';
import type { CalculationCycleCropSummaryResponse } from './calculationCycleCropReplay';
import type { StartupCropSample } from './startupCropReplay';

export const TOMATO_LEAF_MAPPING='stored-lai-relative-area-v1';
export type TomatoLeafBinding=Readonly<{mapping:typeof TOMATO_LEAF_MAPPING;result_id:string;at:string;
  lai:number;reference_lai:number;area_ratio:number;payload_sha256:string;
  reference_kind:'whole_result_maximum'|'last_stored_sample';reference_at:string|null;
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
    payload_sha256:replay.manifest.payload_sha256,scope:replay.claim_scope,gates:replay.gates,
    reference_kind:'whole_result_maximum',reference_at:null};
}

export type TomatoLeafAnchor=Readonly<{result_id:string;payload_sha256:string;sample_index:number;at:string;lai:number}>;
export function cycleTomatoLeafBinding(summary:CycleCropSummaryResponse|CalculationCycleCropSummaryResponse,
  sample:StartupCropSample,index:number,anchor:TomatoLeafAnchor):TomatoLeafBinding|null {
  const ref=summary.reference;
  if(ref.claim_scope!=='synthetic_crop_math_only'||ref.gates!=='not_assessed'||ref.normalization!=='per_m2_floor'
    ||anchor.result_id!==summary.result_id||anchor.payload_sha256!==ref.payload_sha256
    ||anchor.sample_index!==ref.sample_count-1||!Number.isSafeInteger(index)||index<0||index>=ref.sample_count
    ||!Number.isFinite(anchor.lai)||anchor.lai<=0||sample.lai.unit!==LAI_UNIT
    ||!Number.isFinite(sample.lai.value)||sample.lai.value<0||sample.lai.value>anchor.lai
    ||index===anchor.sample_index&&(sample.at!==anchor.at||sample.lai.value!==anchor.lai))return null;
  return {mapping:TOMATO_LEAF_MAPPING,result_id:summary.result_id,at:sample.at,lai:sample.lai.value,
    reference_lai:anchor.lai,area_ratio:sample.lai.value/anchor.lai,payload_sha256:ref.payload_sha256,
    scope:ref.claim_scope,gates:ref.gates,reference_kind:'last_stored_sample',reference_at:anchor.at};
}
