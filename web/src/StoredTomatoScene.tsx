import { useMemo } from 'react';
import type { CropReplay } from './cropReplay';
import { tomatoLeafBinding } from './tomatoLeafReplay';
import TomatoAppearanceScene from './TomatoAppearanceScene';
import './TomatoAppearance.css';

export default function StoredTomatoScene({data,index}:{data:CropReplay;index:number}){
  const binding=useMemo(()=>tomatoLeafBinding(data,index),[data,index]);
  if(!binding)return <p role="status">저장 시점과 잎 면적을 확인할 수 없어 토마토 3D 표시를 보류합니다.</p>;
  return <TomatoAppearanceScene leafBinding={binding} embedded/>;
}
