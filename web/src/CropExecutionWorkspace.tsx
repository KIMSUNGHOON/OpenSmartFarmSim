import { lazy,Suspense,useState } from 'react';
import type { createApi } from './api';
const Joint=lazy(()=>import('./JointCropClimateExecution'));
const Ventilation=lazy(()=>import('./GreenhouseVentilationExecution'));

export default function CropExecutionWorkspace({api,active=true}:{api:ReturnType<typeof createApi>|null;active?:boolean}){
  const [model,setModel]=useState<'joint'|'ventilation'>(()=>
    window.location.hash==='#ventilation-execution'?'ventilation':'joint');
  return <>
    <section className="panel crop-lookup" aria-label="계산 모델 선택">
      <label htmlFor="crop-execution-model">계산 모델</label>
      <select id="crop-execution-model" value={model} onChange={event=>setModel(event.target.value==='ventilation'?'ventilation':'joint')}>
        <option value="joint">작물·기후 공동 계산</option>
        <option value="ventilation">작물·기후·명시 환기 계산</option>
      </select>
      <p className="crop-caption">선택한 모델의 등록 입력과 작업 ID를 사용합니다. 모델을 바꾸면 화면 조회가 중지되며 서버 계산은 계속됩니다.</p>
    </section>
    <Suspense fallback={<p role="status">계산 연결 화면 준비 중…</p>}>
      {model==='joint'?<Joint api={api} active={active}/>:<Ventilation api={api} active={active}/>}
    </Suspense>
  </>;
}
