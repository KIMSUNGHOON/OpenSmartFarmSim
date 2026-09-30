import { useEffect,useRef,useState,type FormEvent } from 'react';
import { ApiError,type CalculationAssessmentIntent,type Evidence,type JobHold,type createApi } from './api';
import { uuid } from './api-validation';

type Api=ReturnType<typeof createApi>;
type Job=Awaited<ReturnType<Api['assessmentJob']>>;
const states:Record<Job['state'],string>={queued:'대기 중',assessing:'평가 중',
  hold:'판단 보류',failed:'실행 실패',canceled:'취소됨'};
const evidenceNames:Record<Evidence,string>={research_source_evidence:'자료 출처와 이용 근거',
  signed_decision_context:'서명된 결정 시각 근거',real_source_g0:'실제 원천의 권리와 품질',
  market_source_g0:'시장 자료의 권리와 품질',eligible_crop_candidates:'재배 가능한 작물 후보',
  farm_scenario_binding:'시설·재배·경제 조건을 함께 고정한 농장 시나리오',
  local_measurements_g2:'독립 현장 측정',future_validation_g3a:'미사용 기간 미래 수확·경제 검증',
  paired_comparison_g3b:'같은 조건의 작물 대응 비교',other_evidence:'추가 확인이 필요한 증거'};
const errors:Record<string,string>={invalid_input:'완료 작업의 식별자를 확인해 주세요.',
  auth_required:'접근 토큰을 설정하거나 다시 확인해 주세요.',access_denied:'이 계정에 필요한 평가·조회 권한이 없습니다.',
  invalid_request:'같은 조건의 완료 열·경제 작업인지 확인해 주세요. 현재 지원되지 않는 입력도 접수할 수 없습니다.',
  not_available:'열람할 수 있는 평가 작업 또는 보류 보고서가 없습니다.',
  intent_conflict:'같은 요청 식별자에 다른 입력이 등록되어 있습니다.',
  response_rejected:'서버 응답을 검증할 수 없어 표시를 보류했습니다.',
  too_large:'요청이 허용 크기를 넘었습니다.',
  server_unavailable:'서버가 요청을 확인하지 못했습니다. 접수 요청은 같은 내용으로 다시 확인하세요.',
  network_unresolved:'응답을 받지 못했습니다. 접수 요청은 같은 내용으로 다시 확인하세요.'};

export default function AssessmentWorkspace({api,onPending,blocked}:{api:Api|null;
  onPending:(pending:boolean)=>void;blocked:boolean}) {
  const [runId,setRunId]=useState('');const [economicId,setEconomicId]=useState('');
  const [savedId,setSavedId]=useState('');
  const [intent,setIntent]=useState<CalculationAssessmentIntent|null>(null);
  const [assessmentId,setAssessmentId]=useState<string|null>(null);
  const [job,setJob]=useState<Job|null>(null);const [hold,setHold]=useState<JobHold|null>(null);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<ApiError|null>(null);
  const [checked,setChecked]=useState<string|null>(null);
  const generation=useRef(0);const inFlight=useRef(false);
  const refused=!!error?.status && error.status>=400 && error.status<500;
  const unresolved=!!intent && !assessmentId && !refused;
  const disabled=!api || busy || blocked;

  useEffect(()=>{
    generation.current++;inFlight.current=false;
    setRunId('');setEconomicId('');setSavedId('');setIntent(null);
    setAssessmentId(null);setJob(null);setHold(null);setBusy(false);setError(null);setChecked(null);
    return()=>{generation.current++;};
  },[api]);
  useEffect(()=>{onPending(busy || unresolved);},[busy,unresolved,onPending]);

  async function load(id:string) {
    if(!api)return;
    const epoch=generation.current;
    const status=await api.assessmentJob(id);
    if(epoch!==generation.current)return;
    setAssessmentId(status.job_id);setJob(status);setChecked(new Date().toISOString());setHold(null);
    if(status.state==='hold'){
      const report=await api.assessmentHold(id);
      if(epoch===generation.current)setHold(report);
    }
  }
  async function request(kind:'submit'|'refresh'|'restore',event?:FormEvent) {
    event?.preventDefault();
    if(!api || blocked || inFlight.current || (kind!=='submit' && unresolved))return;
    if(kind==='submit' && assessmentId)return;
    const epoch=generation.current;
    inFlight.current=true;setBusy(true);onPending(true);setError(null);
    try {
      if(kind==='submit'){
        if(!intent && (!uuid(runId) || !uuid(economicId)))throw new ApiError('invalid_input');
        const body=intent??{run_job_id:runId,economic_job_id:economicId,
          idempotency_key:'web-assessment-v1:'+crypto.randomUUID()};
        setIntent(body);
        const result=await api.assessCalculations(body);
        if(epoch!==generation.current)return;
        setAssessmentId(result.job_id);setJob(result);setHold(null);setChecked(new Date().toISOString());
        if(result.state==='hold')await load(result.job_id);
      } else if(kind==='restore'){
        if(!uuid(savedId))throw new ApiError('invalid_input');
        setAssessmentId(null);setJob(null);setHold(null);setChecked(null);setIntent(null);
        await load(savedId);
      } else if(assessmentId){
        setJob(null);setHold(null);setChecked(null);
        await load(assessmentId);
      }
    } catch(value) {
      if(epoch===generation.current)setError(value instanceof ApiError?value:new ApiError('network_unresolved'));
    } finally {
      if(epoch===generation.current){inFlight.current=false;setBusy(false);}
    }
  }
  function reset() {
    if(disabled || unresolved)return;
    setIntent(null);setAssessmentId(null);setJob(null);setHold(null);setError(null);setChecked(null);setSavedId('');
  }

  return <div className="economic-layout" aria-label="계산 평가">
    <section className="panel" aria-labelledby="assessment-input-heading">
      <p className="step-number">06 / 계산 평가</p><h2 id="assessment-input-heading">완료 계산 연결</h2>
      <p>같은 조건으로 완료된 열·경제 계산을 서버에서 다시 확인하고, 작물 판단에 필요한 근거를 조회합니다.</p>
      <p className="muted">운영자가 제공한 완료 작업 식별자를 입력하세요. 작성 농장의 별도 Run 평가는 아직 지원하지 않습니다.</p>
      <form className="assumption-form" onSubmit={event=>void request('submit',event)}>
        <label>완료 열 계산 작업 ID<input value={runId} onChange={event=>setRunId(event.target.value)}
          autoComplete="off" spellCheck={false} required readOnly={!!intent} disabled={disabled} /></label>
        <label>완료 경제 계산 작업 ID<input value={economicId} onChange={event=>setEconomicId(event.target.value)}
          autoComplete="off" spellCheck={false} required readOnly={!!intent} disabled={disabled} /></label>
        <div className="economic-actions"><button className="button" disabled={disabled || !!assessmentId}>
          {intent?'같은 평가 요청 다시 확인':'계산 평가 요청'}</button>
          <button type="button" className="button secondary" onClick={reset} disabled={disabled || unresolved}>새 평가 입력</button></div>
      </form>
      {intent && <details className="job-reference"><summary>접수 요청 기록</summary>
        <p>응답이 불확실하면 같은 요청을 다시 확인하세요. 새로고침하면 이 임시 기록은 사라지므로 식별자를 보관해 주세요.</p>
        <code>열 작업: {intent.run_job_id}</code><code>경제 작업: {intent.economic_job_id}</code>
        <code>요청 키: {intent.idempotency_key}</code>
      </details>}
      <form className="assumption-form" onSubmit={event=>void request('restore',event)}>
        <h3>저장된 평가 다시 열기</h3><label>저장 평가 작업 ID<input value={savedId}
          onChange={event=>setSavedId(event.target.value)} autoComplete="off" spellCheck={false}
          required disabled={disabled || unresolved} /></label>
        <button className="button secondary" disabled={disabled || unresolved}>저장 평가 조회</button>
      </form>
    </section>
    <section className="panel evidence-panel" aria-labelledby="assessment-state-heading">
      <h2 id="assessment-state-heading">평가 상태와 필요한 근거</h2>
      {busy && <p role="status">서버 기록 확인 중…</p>}
      {error && <p className="notice error" role="alert">{errors[error.code]??'요청을 확인할 수 없습니다.'}</p>}
      {job ? <>
        <p className="job-status" role="status">{states[job.state]}</p>
        <p>접수와 계산 완료는 작물 추천의 승인이 아닙니다. 현재 합성 평가의 최종 판단은 보류됩니다.</p>
        <dl className="job-facts"><div><dt>평가 작업 ID</dt><dd>{job.job_id}</dd></div>
          <div><dt>실행 시도</dt><dd>{job.attempt_count} / {job.max_attempts}</dd></div>
          <div><dt>확인 시각 (UTC)</dt><dd>{checked}</dd></div></dl>
        {hold && <div className="notice"><h3>판단 보류 근거</h3>
          <ul>{hold.missing_evidence.map((code,index)=><li key={code+index}>{evidenceNames[code]}</li>)}</ul>
          <p>서버가 기록한 누락 근거 {hold.missing_evidence_count}건입니다.</p></div>}
        {job.state==='hold' && !hold && <p className="muted">보류 보고서는 아직 확인되지 않았습니다. 상태를 다시 확인해 주세요.</p>}
      </> : <p>{assessmentId?'현재 평가 상태는 확인되지 않았습니다. 같은 저장 작업을 다시 조회해 주세요.':
        '평가를 접수하거나 저장된 평가 작업을 조회해 주세요.'}</p>}
      {assessmentId && <>
        {!job && <code>저장된 평가 작업 ID: {assessmentId}</code>}
        <button className="button secondary" disabled={disabled} onClick={()=>void request('refresh')}>평가 상태 확인</button>
      </>}
    </section>
  </div>;
}
