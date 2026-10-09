import {useMemo} from 'react';
import type {createApi} from './api';
import {closed,need,object} from './api-validation';
import type {CropFarm} from './cropReplay';
import {validCalculationCycleCropLookup} from './calculationCycleCropReplay';
import {validHarvestLookup} from './harvestReplay';
import CycleCropReplay from './CycleCropReplay';

export type StoredCropSelection=Readonly<{kind:'calculation_cycle_v1';farm:Readonly<CropFarm>;result_id:string}>
  |Readonly<{kind:'harvest_v1';farm:Readonly<CropFarm>;result_id:string;parent_result_id:string}>;
function resolve(value:StoredCropSelection|null){
  if(value===null)return null;
  need(object(value));closed(value,value.kind==='harvest_v1'?['kind','farm','result_id','parent_result_id']:['kind','farm','result_id']);
  need(value.kind==='calculation_cycle_v1'||value.kind==='harvest_v1');
  need(object(value.farm));closed(value.farm,['scenario_id','scenario_revision','registration_sha256','crop_id']);
  const farm={scenario_id:value.farm.scenario_id,scenario_revision:value.farm.scenario_revision,
    registration_sha256:value.farm.registration_sha256,crop_id:value.farm.crop_id};
  const lookup={...farm,result_id:value.kind==='harvest_v1'?value.parent_result_id:value.result_id};
  need(validCalculationCycleCropLookup(lookup));
  const harvestId=value.kind==='harvest_v1'?value.result_id:undefined;
  if(harvestId!==undefined)need(validHarvestLookup({...farm,result_id:harvestId}));
  return {lookup,harvestId,key:JSON.stringify([value.kind,lookup,harvestId??null])};
}
export default function SelectedCropReplay({api,selection}:{api:ReturnType<typeof createApi>|null;selection:StoredCropSelection|null}){
  let resolved:ReturnType<typeof resolve>|undefined;try{resolved=resolve(selection);}catch{resolved=undefined;}
  const identity=resolved===null?'none':resolved===undefined?'invalid':resolved.key;
  const selected=useMemo(()=>resolved,[identity]);
  if(!api||selected===null)return null;
  if(selected===undefined)return <p role="alert" className="notice error">선택한 저장 결과의 농장·판본 연결을 확인할 수 없습니다.</p>;
  return <CycleCropReplay key={selected.key} api={api} sourceKind="calculation" initialSelection={selected.lookup}
    autoLoadInitialSelection initialHarvestResultId={selected.harvestId}/>;
}
