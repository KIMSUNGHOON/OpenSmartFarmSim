import { useEffect,useRef,useState,type FormEvent } from 'react';
import { ApiError,type Evidence,type JobHold,type JobStatus,type createApi } from './api';
import type { AuthoredFarmActivity,AuthoredFarmCursor,AuthoredFarmSummary } from './authored-farm-api';
import AuthoredFarmComposer from './AuthoredFarmComposer';
import './AuthoredFarmWorkspace.css';

type Api=ReturnType<typeof createApi>;
type Work='lookup'|'review'|'review-status'|'run'|'run-status';
const LAST_FARM_KEY='ossf.authored.last-farm.v1';
const IDENTIFIER=/^[A-Za-z0-9][A-Za-z0-9_.:/-]{0,199}$/;
const DIGEST=/^[0-9a-f]{64}$/;
type SavedFarm={scenario_id:string;scenario_revision:string;scenario_sha256:string};
function lastFarm():SavedFarm|null {
  try {
    const raw=sessionStorage.getItem(LAST_FARM_KEY);
    if(!raw || raw.length>600)return null;
    const value:unknown=JSON.parse(raw);
    if(!value || typeof value!=='object' || Array.isArray(value))return null;
    const fields=value as Record<string,unknown>;
    if(Object.keys(fields).length!==3 || typeof fields.scenario_id!=='string'
      || !IDENTIFIER.test(fields.scenario_id) || typeof fields.scenario_revision!=='string'
      || !IDENTIFIER.test(fields.scenario_revision) || typeof fields.scenario_sha256!=='string'
      || !DIGEST.test(fields.scenario_sha256))return null;
    return fields as SavedFarm;
  } catch {return null;}
}
function rememberFarm(value:AuthoredFarmSummary) {
  try {sessionStorage.setItem(LAST_FARM_KEY,JSON.stringify({scenario_id:value.scenario_id,
    scenario_revision:value.scenario_revision,scenario_sha256:value.scenario_sha256}));}
  catch { /* Storage may be disabled; server lookup still works. */ }
}
function forgetFarm() {
  try {sessionStorage.removeItem(LAST_FARM_KEY);} catch { /* Storage may be disabled. */ }
}
const stateName:Record<JobStatus['state'],string>={queued:'대기 중',researching:'조사 중',
  collecting:'수집 중',reviewing:'검토 중',simulating:'계산 중',assessing:'평가 중',
  succeeded:'완료',hold:'보류',failed:'실패',canceled:'취소'};
const errors:Record<string,string>={auth_required:'먼저 내부 시험 연결을 설정해 주세요.',
  access_denied:'이 판본이나 작업에 필요한 권한이 없습니다.',
  not_available:'등록된 판본 또는 작업을 찾을 수 없습니다.',
  invalid_request:'현재 입력·권리·해제 근거를 서버가 확인하지 못했습니다.',
  intent_conflict:'같은 요청 식별자에 다른 입력이 등록되어 있습니다.',
  server_unavailable:'서버가 접수 여부를 확인하지 못했습니다. 같은 버튼으로 재확인해 주세요.',
  network_unresolved:'응답을 받지 못했습니다. 같은 버튼으로 저장된 접수를 다시 확인해 주세요.',
  response_rejected:'서버 응답의 판본 또는 작업 연결을 확인할 수 없습니다.'};
const evidenceName:Record<Evidence,string>={
  research_source_evidence:'자료 출처와 이용 근거',
  signed_decision_context:'결정 시각의 서명 근거',
  real_source_g0:'권리와 품질을 확인한 원천 자료',
  market_source_g0:'권리와 품질을 확인한 시장 자료',
  eligible_crop_candidates:'재배 가능한 작물 후보',
  farm_scenario_binding:'시설·재배·경제 조건을 묶은 입력',
  local_measurements_g2:'독립적인 현장 측정',
  future_validation_g3a:'미사용 기간의 수확·경제 검증',
  paired_comparison_g3b:'같은 조건의 작물 대응 비교',
  other_evidence:'추가 확인이 필요한 증거',
};

function JobCard({title,job,onRefresh,busy}:{title:string;job:JobStatus|null;
  onRefresh:()=>void;busy:boolean}) {
  return <section className="authored-job">
    <div className="authored-job-title"><h3>{title}</h3><span className="authored-state">{job ? stateName[job.state] : '아직 접수 전'}</span></div>
    {job ? <><p className="authored-job-id">작업 ID <code>{job.job_id}</code></p>
      <p className="authored-job-meta">서버 갱신 {job.updated_at}</p>
      {job.reason_code && <details className="authored-job-meta"><summary>기술 기록</summary>
        <code>{job.reason_code}</code></details>}
      <button type="button" className="button secondary" disabled={busy} onClick={onRefresh}>상태 다시 확인</button></>
      : <p className="muted">등록된 판본을 확인한 뒤 작업을 접수할 수 있습니다.</p>}
  </section>;
}

export default function AuthoredFarmWorkspace({api,onOpenReplay}:{api:Api|null;
  onOpenReplay:(jobId:string)=>void}) {
  const [scenarioId,setScenarioId]=useState('');
  const [revision,setRevision]=useState('');
  const [farm,setFarm]=useState<AuthoredFarmSummary|null>(null);
  const [catalog,setCatalog]=useState<AuthoredFarmSummary[]|null>(null);
  const [catalogCursor,setCatalogCursor]=useState<AuthoredFarmCursor|null>(null);
  const [catalogBusy,setCatalogBusy]=useState(false);
  const [catalogError,setCatalogError]=useState<string|null>(null);
  const [activity,setActivity]=useState<AuthoredFarmActivity[]|null>(null);
  const [activityCursor,setActivityCursor]=useState<AuthoredFarmCursor|null>(null);
  const [activityBusy,setActivityBusy]=useState(false);
  const [activityError,setActivityError]=useState<string|null>(null);
  const [creating,setCreating]=useState(false);
  const [review,setReview]=useState<JobStatus|null>(null);
  const [run,setRun]=useState<JobStatus|null>(null);
  const [reviewHold,setReviewHold]=useState<JobHold|null>(null);
  const [busy,setBusy]=useState<Work|null>(null);
  const [error,setError]=useState<string|null>(null);
  const generation=useRef(0);
  const activityRequest=useRef(0);
  const reviewKey=useRef<string|null>(null);
  const runKey=useRef<string|null>(null);

  useEffect(()=>{
    const epoch=++generation.current;
    activityRequest.current++;
    setScenarioId('');setRevision('');setFarm(null);setCreating(false);setReview(null);setRun(null);
    setCatalog(null);setCatalogCursor(null);setCatalogBusy(false);setCatalogError(null);
    setActivity(null);setActivityCursor(null);setActivityBusy(false);setActivityError(null);
    setReviewHold(null);setBusy(null);setError(null);reviewKey.current=null;
    runKey.current=null;
    const saved=lastFarm();
    if(!api || !saved)return;
    setBusy('lookup');
    void api.authoredFarm(saved.scenario_id,saved.scenario_revision).then(result=>{
      if(epoch!==generation.current)return;
      if(result.scenario_sha256!==saved.scenario_sha256)
        throw new ApiError('response_rejected');
      setScenarioId(result.scenario_id);setRevision(result.scenario_revision);setFarm(result);
    }).catch(value=>{
      if(epoch!==generation.current)return;
      if(value instanceof ApiError && ['not_available','access_denied','invalid_request',
        'response_rejected'].includes(value.code))forgetFarm();
      else {setScenarioId(saved.scenario_id);setRevision(saved.scenario_revision);}
      const code=value instanceof ApiError ? value.code : 'network_unresolved';
      setError(errors[code] ?? '저장된 판본을 다시 확인할 수 없습니다.');
    }).finally(()=>{if(epoch===generation.current)setBusy(null);});
  },[api]);

  function reset() {
    forgetFarm();
    generation.current++;activityRequest.current++;
    setFarm(null);setCreating(false);setReview(null);setRun(null);setReviewHold(null);
    setScenarioId('');setRevision('');setBusy(null);setError(null);setCatalogBusy(false);
    setActivity(null);setActivityCursor(null);setActivityBusy(false);setActivityError(null);
    reviewKey.current=null;runKey.current=null;
  }
  function failure(value:unknown) {
    const code=value instanceof ApiError ? value.code : 'network_unresolved';
    setError(errors[code] ?? '요청을 확인할 수 없습니다.');
  }
  function acceptFarm(result:AuthoredFarmSummary,keepActivity=false) {
    rememberFarm(result);
    setScenarioId(result.scenario_id);setRevision(result.scenario_revision);setFarm(result);
    setReview(null);setRun(null);setReviewHold(null);
    if(!keepActivity){
      activityRequest.current++;setActivity(null);setActivityCursor(null);
      setActivityBusy(false);setActivityError(null);
    }
    reviewKey.current=null;runKey.current=null;
  }
  async function loadCatalog(next=false) {
    if(catalogBusy || !api)return;
    const epoch=generation.current;
    const cursor=next ? catalogCursor ?? undefined : undefined;
    setCatalogBusy(true);setCatalogError(null);
    try {
      const page=await api.authoredFarmCatalog(cursor);
      if(epoch!==generation.current)return;
      setCatalog(previous=>next && previous ? [...previous,...page.items] : page.items);
      setCatalogCursor(page.next_cursor);
    } catch(value) {
      if(epoch!==generation.current)return;
      const code=value instanceof ApiError ? value.code : 'network_unresolved';
      setCatalogError(errors[code] ?? '등록 판본 목록을 확인할 수 없습니다.');
    } finally {if(epoch===generation.current)setCatalogBusy(false);}
  }
  async function selectCatalog(item:AuthoredFarmSummary) {
    if(busy || catalogBusy || !api)return;
    const epoch=generation.current;
    setBusy('lookup');setError(null);
    try {
      const result=await api.authoredFarm(item.scenario_id,item.scenario_revision);
      if(epoch!==generation.current)return;
      if(result.scenario_sha256!==item.scenario_sha256)throw new ApiError('response_rejected');
      acceptFarm(result);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function loadActivity(next=false) {
    if(busy || activityBusy || !api || !farm)return;
    const epoch=generation.current;
    const request=++activityRequest.current;
    const cursor=next ? activityCursor ?? undefined : undefined;
    setActivityBusy(true);setActivityError(null);
    try {
      const page=await api.authoredFarmActivity(farm.scenario_id,farm.scenario_revision,
        farm.scenario_sha256,cursor);
      if(epoch!==generation.current || request!==activityRequest.current)return;
      setActivity(previous=>next && previous ? [...previous,...page.items] : page.items);
      setActivityCursor(page.next_cursor);
    } catch(value) {
      if(epoch!==generation.current || request!==activityRequest.current)return;
      const code=value instanceof ApiError ? value.code : 'network_unresolved';
      setActivityError(errors[code] ?? '저장된 작업 이력을 확인할 수 없습니다.');
    } finally {if(epoch===generation.current && request===activityRequest.current)setActivityBusy(false);}
  }
  async function selectActivity(item:AuthoredFarmActivity) {
    if(busy || activityBusy || !api || !farm)return;
    const epoch=generation.current;
    setBusy('lookup');setError(null);
    try {
      const current=await api.authoredFarm(farm.scenario_id,farm.scenario_revision);
      if(current.scenario_sha256!==farm.scenario_sha256)throw new ApiError('response_rejected');
      const status=await api.job(item.job.job_id);
      if(status.stage!==(item.kind==='review'?'collection_review':'simulation'))
        throw new ApiError('response_rejected');
      const linked=item.kind==='simulation' ? await api.job(item.review_job.job_id) : null;
      if(linked && linked.stage!=='collection_review')throw new ApiError('response_rejected');
      if(epoch!==generation.current)return;
      acceptFarm(current,true);
      setReview(linked ?? status);setRun(item.kind==='simulation' ? status : null);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function lookup(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();if (busy || !api) {if(!api)setError('먼저 내부 시험 연결을 설정해 주세요.');return;}
    const epoch=generation.current;
    setBusy('lookup');setError(null);
    try {
      const result=await api.authoredFarm(scenarioId.trim(),revision.trim());
      if(epoch!==generation.current)return;
      acceptFarm(result);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  function registered(result:AuthoredFarmSummary) {
    generation.current++;
    acceptFarm(result);setCreating(false);setError(null);setBusy(null);setCatalogBusy(false);
  }
  async function submitReview() {
    if(busy || !api || !farm)return;
    const epoch=generation.current;
    reviewKey.current ??= 'review-'+crypto.randomUUID();
    setBusy('review');setError(null);
    try {
      const value=await api.submitAuthoredReview({scenario_id:farm.scenario_id,
        scenario_revision:farm.scenario_revision,registration_sha256:farm.scenario_sha256,
        idempotency_key:reviewKey.current});
      if(epoch===generation.current){setReview(value);setReviewHold(null);}
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function refreshReview() {
    if(busy || !api || !review)return;
    const epoch=generation.current;
    setBusy('review-status');setError(null);
    try {
      const value=await api.job(review.job_id);
      if(value.stage!=='collection_review')throw new ApiError('response_rejected');
      const hold=value.state==='hold' ? await api.hold(value.job_id) : null;
      if(epoch===generation.current){setReview(value);setReviewHold(hold);}
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function submitRun() {
    if(busy || !api || !farm || !review || review.state!=='succeeded')return;
    const epoch=generation.current;
    runKey.current ??= 'run-'+crypto.randomUUID();
    setBusy('run');setError(null);
    try {
      const value=await api.submitAuthoredRun({scenario_id:farm.scenario_id,
        scenario_revision:farm.scenario_revision,registration_sha256:farm.scenario_sha256,
        review_job_id:review.job_id,idempotency_key:runKey.current});
      if(epoch===generation.current)setRun(value);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function refreshRun() {
    if(busy || !api || !run)return;
    const epoch=generation.current;
    setBusy('run-status');setError(null);
    try {
      const value=await api.job(run.job_id);
      if(value.stage!=='simulation')throw new ApiError('response_rejected');
      if(epoch===generation.current)setRun(value);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }

  return <section className="authored-workflow" aria-labelledby="authored-workflow-heading">
    <div className="authored-intro"><div><p className="step-number">작성 농장 / 내부 작업</p>
      <h2 id="authored-workflow-heading">등록 판본에서 3D 열 재생까지</h2>
      <p>서버에 이미 등록된 농장 판본을 확인하고 검토·계산 작업을 접수합니다. 각 단계의 완료 여부는 서버 기록으로 확인합니다.</p></div>
      <span className="badge">합성 열 재생 범위</span></div>
    <ol className="authored-progress" aria-label="작업 단계">
      <li className={farm?'done':creating?'active':''}>1. 입력 등록·확인</li>
      <li className={review?.state==='succeeded'?'done':review?'active':''}>2. 입력 검토</li>
      <li className={run?.state==='succeeded'?'done':run?'active':''}>3. 계산 작업</li>
      <li className={run?.state==='succeeded'?'active':''}>4. 3D 열기</li>
    </ol>
    {error && <div className="notice error" role="alert">{error}</div>}
    <div className="authored-columns"><div className="authored-main">
      <section className="panel"><p className="step-number">01 / 등록 판본</p><h3>{creating?'새 농장 입력 등록':'서버에 저장된 농장 찾기'}</h3>
        {!farm&&<div className="authored-mode"><button type="button" className="button secondary"
          disabled={!!busy || catalogBusy} aria-pressed={!creating} onClick={()=>setCreating(false)}>저장된 판본 찾기</button>
          <button type="button" className="button secondary" disabled={!!busy || catalogBusy} aria-pressed={creating}
            onClick={()=>setCreating(true)}>새 입력 판본 작성</button></div>}
        {creating&&!farm?<AuthoredFarmComposer api={api} onRegistered={registered}/>:<>
        <p className="muted">등록 때 받은 시나리오 ID와 판본을 입력하세요. 조회와 등록은 현재 서버의 권리·입력 연결을 다시 검사합니다.</p>
        <form onSubmit={lookup} className="authored-lookup"><label>시나리오 ID
          <input required maxLength={200} value={scenarioId} readOnly={!!farm || !!busy}
            onChange={event=>setScenarioId(event.target.value)} autoComplete="off"/></label>
          <label>판본<input required maxLength={200} value={revision} readOnly={!!farm || !!busy}
            onChange={event=>setRevision(event.target.value)} autoComplete="off"/></label>
          <button className="button primary" disabled={!api || !!busy || !!farm}>등록 기록 확인</button>
          {farm && <button type="button" className="button secondary" disabled={!!busy}
            onClick={reset}>다른 판본</button>}</form>
        {farm && <dl className="authored-facts"><div><dt>등록 상태</dt><dd>입력 등록됨 · 계산 전</dd></div>
          <div><dt>등록 해시</dt><dd><code>{farm.scenario_sha256}</code></dd></div>
          <div><dt>입력 작업</dt><dd><code>{farm.intent_job.job_id}</code></dd></div></dl>}
        {farm && <section className="authored-catalog" aria-label="저장된 작업 이력">
          <div className="authored-catalog-heading"><div><h4>저장된 작업 이력</h4>
            <p className="muted">검토·계산 작업의 과거 기록입니다. 선택할 때 현재 판본과 작업 상태를 다시 확인합니다.</p></div>
            <button type="button" className="button secondary" disabled={!api || !!busy || activityBusy}
              onClick={()=>void loadActivity()}>{activityBusy?'이력 확인 중…':activity?'이력 새로고침':'작업 이력 보기'}</button></div>
          {activityError && <p role="alert" className="notice error">{activityError}</p>}
          {activity && (activity.length ? <><ul className="authored-catalog-list">
            {activity.map(item=><li key={item.job.job_id}><button type="button"
              disabled={!api || !!busy || activityBusy} onClick={()=>void selectActivity(item)}>
              <span><strong>{item.kind==='review'?'입력 검토':'열 계산'}</strong> · <code>{item.job.job_id}</code></span>
              <small>{stateName[item.job.state]} · {item.job.created_at}</small>
            </button></li>)}</ul>
            {activityCursor && <button type="button" className="button secondary"
              disabled={!api || !!busy || activityBusy} onClick={()=>void loadActivity(true)}>이전 작업 더 보기</button>}
          </> : <p className="muted">이 판본의 검토·계산 작업 기록이 없습니다.</p>)}
        </section>}
        {!farm && !creating && <div className="authored-catalog">
          <div className="authored-catalog-heading"><div><h4>저장된 판본</h4>
            <p className="muted">현재 계정의 등록 기록입니다. 선택할 때 이용 권리와 입력을 다시 확인합니다.</p></div>
            <button type="button" className="button secondary" disabled={!api || !!busy || catalogBusy}
              onClick={()=>void loadCatalog()}>{catalogBusy?'목록 확인 중…':catalog?'목록 새로고침':'목록 보기'}</button></div>
          {catalogError && <p role="alert" className="notice error">{catalogError}</p>}
          {catalog && (catalog.length ? <><ul className="authored-catalog-list">
            {catalog.map(item=><li key={item.intent_job.job_id}>
              <button type="button" disabled={!api || !!busy || catalogBusy}
                onClick={()=>void selectCatalog(item)}>
                <span><strong>{item.scenario_id}</strong> · {item.scenario_revision}</span>
                <small>등록 {item.intent_job.created_at}</small>
              </button></li>)}</ul>
            {catalogCursor && <button type="button" className="button secondary"
              disabled={!api || !!busy || catalogBusy} onClick={()=>void loadCatalog(true)}>이전 판본 더 보기</button>}
          </> : <p className="muted">현재 계정에 등록된 농장 판본이 없습니다.</p>)}
        </div>}
        </>}
      </section>
      <section className="panel"><p className="step-number">02 / 작성 입력 검토</p>
        <h3>검토 작업 접수</h3><p className="muted">접수는 AI 판단 또는 독립 서명 해제가 아닙니다. 실제 작업자가 실행한 뒤 별도 검토 근거가 필요합니다.</p>
        <button className="button primary" type="button" disabled={!farm || !!busy || !!review}
          onClick={submitReview}>{busy==='review' ? '검토 접수 확인 중…' : '입력 검토 요청'}</button>
        <JobCard title="입력 검토 작업" job={review} onRefresh={refreshReview} busy={!!busy}/>
        {reviewHold && <div className="authored-hold" role="status"><strong>검토 보류</strong>
          <p>서버가 확인한 누락 근거 {reviewHold.missing_evidence_count}건입니다.</p>
          <ul>{reviewHold.missing_evidence.map(item=><li key={item}>{evidenceName[item]}</li>)}</ul></div>}
      </section>
      <section className="panel"><p className="step-number">03 / 작성 열 계산</p>
        <h3>해제 후 계산 작업 접수</h3><p className="muted">검토 작업이 완료되어도 독립 서명 해제가 저장되어야 접수됩니다. 해제 또는 현재 권리가 없으면 서버가 보류합니다.</p>
        <button className="button primary" type="button" disabled={review?.state!=='succeeded' || !!busy || !!run}
          onClick={submitRun}>{busy==='run' ? '계산 접수 확인 중…' : '열 계산 요청'}</button>
        <JobCard title="열 계산 작업" job={run} onRefresh={refreshRun} busy={!!busy}/>
      </section>
    </div><aside className="authored-side" aria-label="결과 범위와 보류">
      <section className="panel authored-result"><p className="step-number">04 / 결과</p><h3>3D 열 재생</h3>
        <p>완료된 저장 Run의 온도·습도·모델 열수요를 120개 시점에서 확인합니다.</p>
        <button className="button primary" type="button" disabled={run?.state!=='succeeded'}
          onClick={()=>{if(run)onOpenReplay(run.job_id);}}>3D 재생 열기</button>
        {run?.state!=='succeeded' && <p className="muted">계산 작업 완료 후 열 수 있습니다.</p>}</section>
      <section className="panel authored-limits"><h3>현재 확인 범위</h3>
        <ul><li>입력 등록과 작업 상태는 서버에서 확인합니다.</li>
          <li>검토 완료와 독립 해제는 서로 다른 단계입니다.</li>
          <li>합성 화면은 생장·수확·미래 마진·작물 순위를 예측하지 않습니다.</li></ul>
      </section>
    </aside></div>
  </section>;
}
