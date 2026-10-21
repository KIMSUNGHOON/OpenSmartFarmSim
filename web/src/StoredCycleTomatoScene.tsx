import { useMemo } from 'react';
import type { CycleCropSummaryResponse } from './cycleCropReplay';
import type { CalculationCycleCropSummaryResponse } from './calculationCycleCropReplay';
import type { StartupCropSample } from './startupCropReplay';
import { cycleTomatoLeafBinding,type TomatoLeafAnchor } from './tomatoLeafReplay';
import TomatoAppearanceScene from './TomatoAppearanceScene';
import './TomatoAppearance.css';

export default function StoredCycleTomatoScene({summary,sample,index,anchor}:{
  summary:CycleCropSummaryResponse|CalculationCycleCropSummaryResponse;sample:StartupCropSample;index:number;anchor:TomatoLeafAnchor|null}){
  const binding=useMemo(()=>anchor?cycleTomatoLeafBinding(summary,sample,index,anchor):null,[summary,sample,index,anchor]);
  if(!anchor)return <p role="status">마지막 저장 시점의 잎 면적을 확인하고 있습니다.</p>;
  if(!binding)return <p role="status">이 시점은 확인된 외형 표시 기준에 연결할 수 없어 3D를 보류합니다. 원 계산값은 표에서 확인하세요.</p>;
  return <TomatoAppearanceScene leafBinding={binding} embedded/>;
}
