import { Suspense, lazy } from 'react';
import { createRoot } from 'react-dom/client';
import { createApi } from '../src/api';
import { authoredJobId } from '../e2e/authored-thermal-fixture';
import '@fontsource-variable/noto-sans-kr';
import '../src/App.css';

const Replay=lazy(()=>import('../src/Replay'));
const api=createApi('synthetic-demo-token-only');
const root=document.getElementById('root');
if (!root) throw new Error('Demo root unavailable');
createRoot(root).render(<div className="app-shell">
  <aside className="sidebar"><p className="brand">Open<br/>SmartFarmSim</p>
    <span className="sidebar-label">로컬 합성 3D 데모</span>
    <p className="sidebar-note">자료는 화면 시험용 응답입니다.</p></aside>
  <main>
    <header className="page-header"><div><p className="eyebrow">OPEN SMART FARM SIMULATOR · LOCAL DEMO</p>
      <h1>두 시간 온실 재생</h1><p>아래 <strong>저장된 Run 조회</strong>를 누르면 3D 장면과 120개 저장 시각을 볼 수 있습니다.</p></div>
      <div className="scope-summary"><span className="badge">합성 응답 데모</span>
        <strong>온실 한 구역 · 두 시간</strong><span>실제 관측·농장 계산·작물 추천이 아닙니다.</span></div></header>
    <div className="notice"><strong>브라우저 소프트웨어 데모</strong>
      <p>표시 값은 직접 작성한 고정 시험 응답입니다. 실제 자료 수집, Codex CLI 검토, 독립 해제나 생산 서비스가 실행되지 않습니다.</p></div>
    <Suspense fallback={<p role="status">재생 화면 준비 중…</p>}>
      <Replay api={api} initialSelection={{kind:'authored',jobId:authoredJobId}}/>
    </Suspense>
  </main>
</div>);
