import { useEffect,useRef,useState } from 'react';
import { ApiError,type Evidence,type JobHold,type JobStatus,type createApi } from './api';
import './SourceWorkflow.css';

type Api=ReturnType<typeof createApi>;
type Work='collection'|'collection-status'|'review'|'review-status';
const labels:Record<JobStatus['state'],string>={queued:'대기 중',researching:'조사 중',
  collecting:'수집 중',reviewing:'검토 중',simulating:'계산 중',assessing:'평가 중',
  succeeded:'작업 완료',hold:'판단 보류',failed:'실행 실패',canceled:'취소됨'};
const evidence:Record<Evidence,string>={research_source_evidence:'자료 출처와 이용 근거',
  signed_decision_context:'서명된 결정 시각 근거',real_source_g0:'실제 원천의 권리와 품질',
  market_source_g0:'시장 자료의 권리와 품질',eligible_crop_candidates:'재배 가능한 작물 후보',
  farm_scenario_binding:'시설·재배·경제 조건을 묶은 농장 판본',
  local_measurements_g2:'독립 현장 측정',future_validation_g3a:'미사용 기간 미래 검증',
  paired_comparison_g3b:'같은 조건의 작물 대응 비교',other_evidence:'추가 확인이 필요한 증거'};

export default function SourceWorkflow({api,researchJob}:{api:Api|null;researchJob:JobStatus|null}) {
  const [collection,setCollection]=useState<JobStatus|null>(null);
  const [review,setReview]=useState<JobStatus|null>(null);
  const [hold,setHold]=useState<JobHold|null>(null);
  const [busy,setBusy]=useState<Work|null>(null);
  const [error,setError]=useState<string|null>(null);
  const collectionKey=useRef<string|null>(null);
  const reviewKey=useRef<string|null>(null);
  const generation=useRef(0);
  const researchId=researchJob?.job_id;

  useEffect(()=>{
    generation.current++;
    collectionKey.current=null;reviewKey.current=null;
    setCollection(null);setReview(null);setHold(null);setBusy(null);setError(null);
  },[api,researchId]);

  function failure(value:unknown) {
    const code=value instanceof ApiError?value.code:'network_unresolved';
    setError(code==='access_denied'?'이 단계의 서버 권한이 없습니다.':
      code==='invalid_request'?'현재 원본·결정 문맥을 확인할 수 없어 다음 단계를 보류했습니다.':
      code==='intent_conflict'?'같은 요청 식별자에 다른 입력이 저장돼 있습니다.':
      code==='response_rejected'?'서버 작업 응답을 검증하지 못했습니다.':
      '접수 또는 상태를 확인하지 못했습니다. 같은 버튼으로 기존 요청을 다시 확인하세요.');
  }
  async function submitCollection() {
    if(!api || researchJob?.state!=='succeeded' || busy || collection)return;
    const epoch=generation.current;
    collectionKey.current ??= 'web-owned-ingestion-'+crypto.randomUUID();
    setBusy('collection');setError(null);
    try {
      const value=await api.ingestSource({parent_job_id:researchJob.job_id,
        idempotency_key:collectionKey.current});
      if(epoch===generation.current)setCollection(value);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function refreshCollection() {
    if(!api || !collection || busy)return;
    const epoch=generation.current;
    setBusy('collection-status');setError(null);
    try {
      const value=await api.job(collection.job_id);
      if(value.stage!=='collection')throw new ApiError('response_rejected');
      if(epoch===generation.current)setCollection(value);
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function submitReview() {
    if(!api || collection?.state!=='succeeded' || busy || review)return;
    const epoch=generation.current;
    reviewKey.current ??= 'web-owned-review-'+crypto.randomUUID();
    setBusy('review');setError(null);
    try {
      const value=await api.reviewSource({parent_job_id:collection.job_id,
        idempotency_key:reviewKey.current});
      if(epoch===generation.current){setReview(value);setHold(null);}
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }
  async function refreshReview() {
    if(!api || !review || busy)return;
    const epoch=generation.current;
    setBusy('review-status');setError(null);
    try {
      const value=await api.job(review.job_id);
      if(value.stage!=='collection_review')throw new ApiError('response_rejected');
      const report=value.state==='hold'?await api.hold(value.job_id):null;
      if(report && report.stage!=='collection_review')throw new ApiError('response_rejected');
      if(epoch===generation.current){setReview(value);setHold(report);}
    } catch(value) {if(epoch===generation.current)failure(value);}
    finally {if(epoch===generation.current)setBusy(null);}
  }

  if(!researchJob)return null;
  return <section className="panel source-workflow" aria-labelledby="source-workflow-title">
    <div className="source-workflow-head"><div><p className="step-number">지역 조사 다음 단계</p>
      <h2 id="source-workflow-title">원본 수집과 입력 검토</h2>
      <p>완료된 조사에서 서버가 확인한 제공자만 수집하고, 저장된 원본을 별도 검토 작업에 묶습니다.</p>
    </div><span className="badge">내부 합성 자료 경로</span></div>
    {error && <p className="notice error" role="alert">{error}</p>}
    <ol className="source-workflow-steps">
      <li><div><span className="step-number">01 / 자료 조사</span><strong>{labels[researchJob.state]}</strong>
        <small>작업 {researchJob.job_id}</small></div>
        {researchJob.state!=='succeeded' && <p>서버 조사 작업이 완료돼야 수집을 요청할 수 있습니다.</p>}</li>
      <li><div><span className="step-number">02 / 원본 수집</span>
        <strong>{collection?labels[collection.state]:'접수 전'}</strong>
        {collection && <small>작업 {collection.job_id}</small>}</div>
        {collection?<button type="button" className="button secondary"
          disabled={!api || !!busy} onClick={()=>void refreshCollection()}>
          {busy==='collection-status'?'확인 중…':'수집 상태 확인'}</button>
          :<button type="button" className="button secondary"
            disabled={!api || !!busy || researchJob.state!=='succeeded'}
            onClick={()=>void submitCollection()}>{busy==='collection'?'접수 확인 중…':
              collectionKey.current?'같은 수집 요청 다시 확인':'원본 수집 요청'}</button>}</li>
      <li><div><span className="step-number">03 / 수집 입력 검토</span>
        <strong>{review?labels[review.state]:'접수 전'}</strong>
        {review && <small>작업 {review.job_id}</small>}</div>
        {review?<button type="button" className="button secondary"
          disabled={!api || !!busy} onClick={()=>void refreshReview()}>
          {busy==='review-status'?'확인 중…':'검토 상태 확인'}</button>
          :<button type="button" className="button secondary"
            disabled={!api || !!busy || collection?.state!=='succeeded'}
            onClick={()=>void submitReview()}>{busy==='review'?'접수 확인 중…':
              reviewKey.current?'같은 검토 요청 다시 확인':'수집 입력 검토 요청'}</button>}</li>
    </ol>
    {hold && <div className="source-workflow-hold" role="status"><strong>검토 보류 근거</strong>
      <ul>{hold.missing_evidence.map(item=><li key={item}>{evidence[item]}</li>)}</ul></div>}
    <p className="muted">수집·검토 작업 완료는 실제 자료 G0 승인이나 시뮬레이션 Run 게시를 뜻하지 않습니다.</p>
  </section>;
}
