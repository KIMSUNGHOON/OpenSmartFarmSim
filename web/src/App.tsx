import { lazy,Suspense,useRef,useState,type FormEvent } from 'react';
import { createApi, ApiError, type Evidence, type JobHold, type JobStatus, type LocationAccepted,
  type LocationIntent, type State } from './api';
import EconomicWorkspace from './EconomicWorkspace';
const Replay=lazy(()=>import('./Replay'));

const statusNames:Record<State,string>={queued:'대기 중',researching:'자료 조사 중',collecting:'원본 수집 중',
  reviewing:'자료 검토 중',simulating:'계산 중',assessing:'평가 중',succeeded:'작업 완료',hold:'판단 보류',
  failed:'실행 실패',canceled:'취소됨'};
const evidenceNames:Record<Evidence,string>={research_source_evidence:'조사할 자료의 출처와 이용 근거',
  signed_decision_context:'결정 시각을 확인할 서명 근거',real_source_g0:'권리와 품질을 확인한 실제 원천',
  market_source_g0:'권리와 품질을 확인한 시장 자료',eligible_crop_candidates:'이번 조건에서 재배 가능한 작물 후보',
  farm_scenario_binding:'시설·재배·경제 조건을 함께 고정한 시나리오',local_measurements_g2:'독립적인 현장 측정',
  future_validation_g3a:'미사용 기간의 미래 수확·경제 검증',paired_comparison_g3b:'같은 조건의 작물 대응 비교',
  other_evidence:'추가 확인이 필요한 증거'};
const errorNames:Record<string,string>={auth_required:'접근 토큰을 확인해 주세요.',
  access_denied:'이 계정에 필요한 조회 또는 접수 권한이 없습니다.',not_available:'열람할 수 있는 작업 또는 보류 보고서가 없습니다.',
  invalid_request:'서버에 등록된 좌표·기간인지 확인해 주세요.',intent_conflict:'같은 요청 식별자에 다른 입력이 등록되어 있습니다.',
  too_large:'요청이 허용 크기를 넘었습니다.',response_rejected:'서버 응답을 확인할 수 없어 표시를 보류했습니다.',
  server_unavailable:'서버가 접수 여부를 확인하지 못했습니다. 같은 요청을 다시 확인해 주세요.',
  network_unresolved:'응답을 받지 못했습니다. 중복 접수를 피하려면 같은 요청을 다시 확인해 주세요.',
  invalid_input:'좌표와 가상 적용 시작 시각을 확인해 주세요.'};
function timestamp(value:string) {
  return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',dateStyle:'short',timeStyle:'medium'}).format(new Date(value))+' KST';
}
function makeIntent(latitude:string,longitude:string,start:string):LocationIntent {
  const lat=Number(latitude),lon=Number(longitude);
  const instant=new Date(start+':00Z');
  if (!latitude.trim() || !longitude.trim() || !Number.isFinite(lat) || !Number.isFinite(lon)
    || Math.abs(lat)>90 || Math.abs(lon)>180 || !/^\d{4}-\d\d-\d\dT\d\d:\d\d$/.test(start)
    || !Number.isFinite(instant.getTime()) || instant.toISOString().slice(0,16)!==start) throw new ApiError('invalid_input');
  return {latitude:lat,longitude:lon,period_start_utc:instant.toISOString(),
    period_end_utc:new Date(instant.getTime()+7_200_000).toISOString(),goal_id:'historical-thermal-replay',
    idempotency_key:'web-location-v1:'+crypto.randomUUID()};
}

export default function App() {
  const [api,setApi]=useState<ReturnType<typeof createApi>|null>(null);
  const [token,setToken]=useState(''); const [latitude,setLatitude]=useState('');
  const [longitude,setLongitude]=useState(''); const [startDate,setStartDate]=useState('');
  const [startTime,setStartTime]=useState('');
  const [view,setView]=useState<'input'|'work'|'economic'|'replay'>('input'); const [busy,setBusy]=useState(false);
  const [financialLock,setFinancialLock]=useState(false);
  const [intent,setIntent]=useState<LocationIntent|null>(null); const pinned=useRef<LocationIntent|null>(null);
  const jobId=useRef<string|null>(null); const inFlight=useRef(false); const generation=useRef(0);
  const [accepted,setAccepted]=useState<LocationAccepted|null>(null);
  const [job,setJob]=useState<JobStatus|null>(null); const [hold,setHold]=useState<JobHold|null>(null);
  const [error,setError]=useState<ApiError|null>(null);
  const [checked,setChecked]=useState<string|null>(null);
  function reset() {
    generation.current++; pinned.current=null; jobId.current=null;
    setIntent(null);setAccepted(null);setJob(null);setHold(null);setError(null);setChecked(null);setView('input');
  }
  function connect(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();
    try { const client=createApi(token);generation.current++;setApi(client);setToken('');
      setAccepted(null);setJob(null);setHold(null);setError(null);setChecked(null); }
    catch(error) { setError(error instanceof ApiError ? error : new ApiError('auth_required')); }
  }
  async function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (inFlight.current) return;
    if (!api) {setError(new ApiError('auth_required'));return;}
    const epoch=generation.current;inFlight.current=true;setBusy(true);setError(null);
    try {
      const body=pinned.current ?? makeIntent(latitude,longitude,startDate+'T'+startTime);
      pinned.current=body;setIntent(body);
      const result=await api.location(body);
      if (epoch!==generation.current) return;
      jobId.current=result.research_job.job_id;setAccepted(result);setJob(result.research_job);
      setHold(null);setChecked(new Date().toISOString());setView('work');
    } catch(error) { if (epoch===generation.current) setError(error instanceof ApiError ? error : new ApiError('network_unresolved')); }
    finally {inFlight.current=false;if (epoch===generation.current) setBusy(false);}
  }
  async function refresh() {
    if (!api || !jobId.current || inFlight.current) return;
    const epoch=generation.current;inFlight.current=true;setBusy(true);setError(null);
    try {
      const result=await api.job(jobId.current);
      if (epoch!==generation.current) return;
      setJob(result);setHold(null);setChecked(new Date().toISOString());
      if (result.state==='hold') {
        const report=await api.hold(result.job_id);
        if (report.stage!==result.stage) throw new ApiError('response_rejected');
        if (epoch===generation.current) setHold(report);
      }
    } catch(error) {if (epoch===generation.current) setError(error instanceof ApiError ? error : new ApiError('network_unresolved'));}
    finally {inFlight.current=false;if (epoch===generation.current) setBusy(false);}
  }
  const canReset=!intent || !!job || !!error?.status && error.status<500;
  return <div className="app-shell">
    <a className="skip-link" href="#main">본문으로 이동</a>
    <aside className="sidebar" id="viewport-1-a-nav">
      <p className="brand">Open<br/>SmartFarmSim</p>
      <span className="sidebar-label">온실 시뮬레이션</span>
      <nav aria-label="주요 화면">
        <button aria-current={view==='input' ? 'page' : undefined} onClick={()=>setView('input')}>01 <span>입력 설정</span></button>
        <button aria-current={view==='work' ? 'page' : undefined} onClick={()=>setView('work')}>02 <span>작업과 근거</span></button>
        <button aria-current={view==='economic' ? 'page' : undefined} onClick={()=>setView('economic')}>03 <span>경제 가정·계산</span></button>
        <button aria-current={view==='replay' ? 'page' : undefined} onClick={()=>setView('replay')}>04 <span>3D 열 재생</span></button>
      </nav><p className="sidebar-note">직접 작성한 합성 자료<br/>내부 계약 시험</p>
    </aside>
    <main id="main" tabIndex={-1}>
      <header className="page-header"><div><p className="eyebrow">OPEN SMART FARM SIMULATOR</p>
        <h1>{view==='input' ? '시뮬레이션 입력 설정' : view==='work' ? '작업 진행과 근거' : view==='replay' ? '두 시간 온실 재생' : '경제 가정과 조건부 계산'}</h1>
        <p>{view==='economic' ? '저장된 가정을 검토하고, 판본을 고정해 조건부 원장 계산을 확인하세요.' :
          view==='replay' ? '저장된 합성 계산의 같은 시각을 3D·그래프·표에서 확인하세요.' : '좌표와 기간을 지정하고, 자료 조사 상태와 판단에 필요한 근거를 확인하세요.'}</p></div>
        <div className="scope-summary" aria-label="입력 요약"><span className="badge">합성 자료 시험</span>
          <strong>{view==='economic' ? '저장 원장 · 사용자 가정' : '온실 한 구역 · 두 시간'}</strong><span>실제 관측·미래 예측·작물 추천이 아닙니다.</span></div>
      </header>
      <details className="connection"><summary>내부 시험 연결</summary>
        <p>운영자가 발급한 접근 토큰을 입력하세요. 토큰은 저장하지 않으며, 페이지를 새로 열면 다시 연결해야 합니다.</p>
        <form onSubmit={connect}><label>접근 토큰<input type="password" value={token} onChange={e=>setToken(e.target.value)}
          autoComplete="off" spellCheck={false} required disabled={busy || financialLock}/></label>
          <button className="button" disabled={busy || financialLock}>연결 설정</button>
          {api && <button type="button" className="button secondary" disabled={busy || financialLock} onClick={()=>{reset();setApi(null);setToken('');setLatitude('');setLongitude('');setStartDate('');setStartTime('');}}>연결 해제</button>}
        </form><p className="connection-state">{api ? '연결 정보 설정됨 · 권한은 서버가 요청마다 확인합니다.' : '접근 토큰을 설정해 주세요.'}</p>
      </details>
      {error && <div className="notice error" role="alert">{errorNames[error.code] ?? '요청을 확인할 수 없습니다.'}</div>}
      <div hidden={view!=='economic'}><EconomicWorkspace api={api} onPending={setFinancialLock} blocked={busy}/></div>
      {view==='replay' && <Suspense fallback={<p role="status">재생 화면 준비 중…</p>}><Replay api={api}/></Suspense>}
      {view==='economic' || view==='replay' ? null : view==='input' ? <form onSubmit={submit} className="input-form">
        <section className="panel input-panel" id="viewport-1-a-coordinates"><div><p className="step-number">01 / 지역</p><h2>위도·경도 설정</h2>
          <p>한국 내 좌표를 입력하세요. 서버에 등록된 시범 범위만 접수됩니다.</p>
          <div className="field-row"><label>위도 (°N)<input type="number" min="-90" max="90" step="any" required value={latitude}
            readOnly={!!intent} onChange={e=>setLatitude(e.target.value)}/></label>
            <label>경도 (°E)<input type="number" min="-180" max="180" step="any" required value={longitude}
              readOnly={!!intent} onChange={e=>setLongitude(e.target.value)}/></label></div></div>
          <div className="coordinate-readout"><span>입력 좌표</span><strong>{latitude || '—'}° N<br/>{longitude || '—'}° E</strong>
            <p>농장 위치·주변 환경의 정밀도를 보장하는 좌표가 아닙니다.</p></div>
        </section>
        <section className="panel input-panel" id="viewport-1-a-period"><div><p className="step-number">02 / 기간</p><h2>가상 적용 시각</h2>
          <p>합성 자료에 붙인 시각입니다. 실제 관측 시각으로 해석하지 마세요.</p>
          <div className="field-row"><label>시작 날짜 (UTC)<input type="date" required value={startDate} readOnly={!!intent}
            onChange={e=>setStartDate(e.target.value)}/></label>
            <label>시작 시각 (UTC)<input type="time" step="60" required value={startTime} readOnly={!!intent}
              onChange={e=>setStartTime(e.target.value)}/></label></div></div>
          <div className="scope-detail"><strong>시작부터 정확히 두 시간</strong><p>UTC는 세계 표준 시각이며 한국 시각(KST)은 UTC보다 9시간 빠릅니다.</p>
            <button type="button" className="button secondary" disabled={busy || !!intent} onClick={()=>{setLatitude('37.5');setLongitude('127');setStartDate('2026-10-15');setStartTime('08:00');}}>합성 예시 채우기</button></div>
        </section>
        <section className="panel input-panel" id="viewport-1-a-zone"><div><p className="step-number">03 / 계산 범위</p><h2>개념적 온실 한 구역</h2>
          <p>한 구역의 온도·습도·설비 반응이 계산 대상입니다. 승인된 입력과 모델이 있어야 계산을 진행할 수 있습니다.</p></div>
          <div className="scope-detail"><span className="badge">검토 전</span><p>현재 화면에서는 자료 조사 접수와 작업·보류 근거를 확인합니다.</p></div></section>
        <div className="form-actions"><p>합성 시험만으로 현장 정확도나 작물의 우열을 판단하지 않습니다.</p>
          <button type="button" className="button secondary" disabled={busy || financialLock || !canReset} onClick={reset}>새 입력</button>
          <button className="button primary" disabled={busy || financialLock}>{busy ? '접수 확인 중…' : pinned.current ? '같은 요청 다시 확인' : '자료 조사 요청'}</button></div>
      </form> : <div className="work-layout" id="viewport-1-b-progress">
        <section className="panel work-panel"><p className="step-number">현재 작업</p><h2>서버 작업 기록</h2>
          {job ? <><div className="job-status" role="status"><span className="status-dot"/><strong>{statusNames[job.state]}</strong></div>
            <dl className="job-facts"><div><dt>현재 단계</dt><dd>{({research:'자료 조사',collection:'원본 수집',collection_review:'수집 자료 검토',simulation:'수치 계산',assessment:'평가'})[job.stage]}</dd></div>
              <div><dt>시도 횟수</dt><dd>{job.attempt_count} / 최대 {job.max_attempts}</dd></div>
              <div><dt>작업 등록</dt><dd>{timestamp(job.created_at)}<small>서버 시각: {job.created_at}</small></dd></div>
              <div><dt>서버 기록 갱신</dt><dd>{timestamp(job.updated_at)}<small>서버 시각: {job.updated_at}</small></dd></div></dl>
            <p className="muted">작업 완료는 현장 정확도나 추천 승인과 별개입니다.</p>
          </> : <p>표시할 작업을 서버에서 아직 확인하지 않았습니다.</p>}
          <button className="button primary" onClick={refresh} disabled={busy || !api || !jobId.current}>{busy ? '확인 중…' : '현재 상태 확인'}</button>
          {checked && <p className="muted">마지막 화면 확인: {timestamp(checked)}</p>}
          {job && <details className="job-reference"><summary>작업 식별자</summary><code>{job.job_id}</code></details>}
        </section>
        <section className="panel evidence-panel" id="viewport-1-b-summary"><p className="step-number">근거 확인</p>
          <h2>{job?.state==='hold' ? '판단 보류' : '검증된 보류 근거'}</h2>
          {hold ? <><p>서버가 확인한 누락 근거 {hold.missing_evidence_count}건입니다.</p>
            <ul>{hold.missing_evidence.map(item=><li key={item}>{evidenceNames[item]}</li>)}</ul>
            <p className="muted">기록 시각: {timestamp(hold.recorded_at)}</p></>
            : <p>{job?.state==='hold' ? '서버가 작업을 보류했습니다. 열람 가능한 검증 보고서를 확인해 주세요.' : '검증된 보고서를 받으면 필요한 근거를 표시합니다.'}</p>}
          {accepted && <div className="notice"><strong>지역 검토 전</strong><p>{accepted.point.latitude}° N · {accepted.point.longitude}° E</p></div>}
          <p className="muted">현재 상태나 합성 자료만으로 미래 수확·이익·작물 순위를 확정하지 않습니다.</p>
        </section>
      </div>}
      <footer>OpenSmartFarmSim · 직접 작성한 합성 자료를 위한 내부 시험 화면</footer>
    </main>
  </div>;
}
