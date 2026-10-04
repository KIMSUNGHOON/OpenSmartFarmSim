import { Suspense, lazy,useState } from 'react';
import { createRoot } from 'react-dom/client';
import { createApi } from '../src/api';
import { authoredJobId } from '../e2e/authored-thermal-fixture';
import '@fontsource-variable/noto-sans-kr';
import '../src/App.css';
import { cropReferenceSelection,cropHoldReferenceSelection } from '../e2e/crop-fixture';

const Replay=lazy(()=>import('../src/Replay'));
const CropReplay=lazy(()=>import('../src/CropReplay'));
const api=createApi('synthetic-demo-token-only');
const root=document.getElementById('root');
if (!root) throw new Error('Demo root unavailable');
function Demo(){
  const [growth,setGrowth]=useState(new URL(location.href).searchParams.get('view')==='growth');
  const held=new URL(location.href).searchParams.get('state')==='hold';
  const selectedCrop=held?cropHoldReferenceSelection:cropReferenceSelection;
  return <div className={'app-shell'+(growth?' crop-shell':'')}>
  <aside className="sidebar"><p className="brand">Open<br/>SmartFarmSim</p>
    <span className="sidebar-label">로컬 합성 3D 데모</span>
    <nav aria-label="데모 종류"><button aria-current={!growth?'page':undefined} onClick={()=>setGrowth(false)}>05 <span>3D 열 재생</span></button>
      <button aria-current={growth?'page':undefined} onClick={()=>setGrowth(true)}>08 <span>성장 연구 3D</span></button></nav>
    <p className="sidebar-note">자료는 화면 시험용 응답입니다.</p></aside>
  <main>
    <header className="page-header"><div><p className="eyebrow">OPEN SMART FARM SIMULATOR · LOCAL DEMO</p>
      <h1>{growth?'계산 기반 성장 연구 재생':'두 시간 온실 재생'}</h1><p>합성 3D 장면을 자동으로 불러옵니다. 실제 저장 내역이 없어도 시연을 볼 수 있습니다.</p></div>
      <div className="scope-summary"><span className="badge">합성 응답 데모</span>
        <strong>{growth?(held?'수치 보류 · 정상 성장 재생 없음':'6개 저장 시점 · 5분 합성 계산'):'온실 한 구역 · 두 시간'}</strong><span>실제 관측·농장 예측·작물 추천이 아닙니다.</span></div></header>
    <div className="notice"><strong>브라우저 소프트웨어 데모</strong>
      <p>{growth?'실제 SCRAM 저장·HTTPS 수용 시험에서 기록한 공개 합성 계산 응답을 재생합니다. 시험 DB는 정리되었으며 이 페이지에서 새 계산을 실행하거나 사용자 저장 내역을 조회하지 않습니다.':'표시 값은 직접 작성한 고정 시험 응답입니다.'}
        {' '}실제 자료 수집, Codex CLI 검토, 독립 해제나 생산 서비스가 실행되지 않습니다.</p></div>
    <Suspense fallback={<p role="status">재생 화면 준비 중…</p>}>
      {growth?<CropReplay api={api} initialSelection={selectedCrop} autoLoadInitialSelection/>:
        <Replay api={api} initialSelection={{kind:'authored',jobId:authoredJobId}} autoLoadInitialSelection/>}
    </Suspense>
  </main>
</div>;}
createRoot(root).render(<Demo/>);
