import { useEffect,useRef,useState } from 'react';
import { ApiError,type createApi,type SourceHistoryPage,type SourceResearch,
  type SourceActivityPage,type SourceActivityItem } from './api';
import type { FarmEconomicCandidate,FarmEconomicPage,FarmEconomicSelection,
  SourceFarmSelection } from './source-farm-api';
import './SourceFarmSelector.css';

const sourceDocumentIcon=new URL('./assets/cutout-15-b6376be1ea78.png',import.meta.url).href;

type Api=ReturnType<typeof createApi>;
type Work='history'|'activity'|'source'|'economics'|'selection';
const states:Record<SourceResearch['job']['state'],string>={queued:'대기 중',researching:'조사 중',
  collecting:'수집 중',reviewing:'검토 중',simulating:'계산 중',assessing:'평가 중',
  succeeded:'작업 완료',hold:'판단 보류',failed:'실행 실패',canceled:'취소됨'};

export default function SourceFarmSelector({api,locked,onSelection}:{api:Api|null;locked:boolean;
  onSelection:(selection:FarmEconomicSelection|null)=>void}) {
  const [history,setHistory]=useState<SourceHistoryPage|null>(null);
  const [research,setResearch]=useState<SourceResearch|null>(null);
  const [activity,setActivity]=useState<SourceActivityPage|null>(null);
  const [source,setSource]=useState<SourceFarmSelection|null>(null);
  const [economics,setEconomics]=useState<FarmEconomicPage|null>(null);
  const [selection,setSelection]=useState<FarmEconomicSelection|null>(null);
  const [step,setStep]=useState<'source'|'economics'|'form'>('source');
  const [busy,setBusy]=useState<Work|null>(null);
  const [error,setError]=useState<string|null>(null);
  const generation=useRef(0),notifier=useRef(onSelection);
  notifier.current=onSelection;
  useEffect(()=>{
    generation.current++;setHistory(null);setResearch(null);setActivity(null);
    setSource(null);setEconomics(null);setSelection(null);setStep('source');
    setBusy(null);setError(null);notifier.current(null);
    return ()=>{generation.current++;};
  },[api]);
  const disabled=!api||locked||!!busy;
  function clearSelection() {setSelection(null);notifier.current(null);}
  async function read(work:Work,load:()=>Promise<void>) {
    if(disabled)return;
    const epoch=generation.current;setBusy(work);setError(null);
    try {await load();}
    catch(value) {
      if(epoch!==generation.current)return;
      const code=value instanceof ApiError?value.code:'network_unresolved';
      setError(code==='access_denied'?'현재 계정에 이 자료를 읽을 권한이 없습니다.':
        code==='auth_required'?'연결을 다시 설정한 뒤 저장 기록에서 선택하세요.':
        code==='invalid_request'?'현재 원천·경제 판본의 근거를 확인하지 못해 선택을 보류했습니다.':
        code==='not_available'?'현재 계정에서 이 저장 기록을 찾을 수 없습니다.':
        code==='response_rejected'?'원천과 경제 판본의 응답 연결을 검증하지 못했습니다.':
        '조회가 완료되지 않았습니다. 같은 조회 버튼으로 다시 확인하세요.');
    } finally {if(epoch===generation.current)setBusy(null);}
  }
  async function loadHistory(more=false) {
    if(!api||disabled)return;
    const epoch=generation.current;
    await read('history',async()=>{
      const page=await api.sourceHistory(more?history?.next_cursor:undefined);
      if(epoch!==generation.current)return;
      setHistory(more&&history?{items:[...history.items,...page.items.filter(item=>
        !history.items.some(previous=>previous.job.job_id===item.job.job_id))],next_cursor:page.next_cursor}:page);
    });
  }
  async function chooseResearch(item:SourceResearch) {
    if(!api||disabled||item.job.state!=='succeeded'||item.current_authority!=='available')return;
    generation.current++;const epoch=generation.current;
    clearSelection();setResearch(item);setActivity(null);setSource(null);setEconomics(null);setStep('source');
    await read('activity',async()=>{
      const detail=await api.sourceHistoryDetail(item.job.job_id);
      if(epoch!==generation.current)return;
      if(detail.research.job.state!=='succeeded'||detail.research.current_authority!=='available')
        throw new ApiError('invalid_request');
      const page=await api.sourceActivity(item.job.job_id);
      if(epoch===generation.current){setResearch(detail.research);setActivity(page);}
    });
  }
  async function loadActivity() {
    if(!api||!research||disabled||!activity?.next_cursor)return;
    const epoch=generation.current;
    await read('activity',async()=>{
      const page=await api.sourceActivity(research.job.job_id,activity.next_cursor);
      if(epoch===generation.current)setActivity({...page,items:[...activity.items,...page.items.filter(item=>
        !activity.items.some(previous=>previous.job.job_id===item.job.job_id))]});
    });
  }
  async function chooseCollection(item:SourceActivityItem) {
    if(!api||!research||disabled||item.kind!=='collection'||item.job.state!=='succeeded')return;
    generation.current++;const epoch=generation.current;
    clearSelection();setSource(null);setEconomics(null);
    await read('source',async()=>{
      const current=await api.sourceFarmReferences(research.job.job_id,item.job.job_id);
      if(epoch!==generation.current)return;
      if(current.claim_mode!=='ex_post_replay')throw new ApiError('invalid_request');
      setSource(current);setStep('economics');
    });
  }
  async function loadEconomics(more=false) {
    if(!api||!source||disabled)return;
    const epoch=generation.current;
    clearSelection();
    await read('economics',async()=>{
      const page=await api.sourceEconomicCandidates(source,more?economics?.next_cursor??undefined:undefined);
      if(epoch!==generation.current)return;
      setEconomics(more&&economics?{...page,items:[...economics.items,...page.items.filter(item=>
        !economics.items.some(previous=>previous.economic.candidate_id===item.economic.candidate_id))]}:page);
    });
  }
  async function chooseEconomic(item:FarmEconomicCandidate) {
    if(!api||!source||disabled)return;
    const epoch=generation.current;clearSelection();
    await read('selection',async()=>{
      const current=await api.sourceEconomicCandidate(source,item);
      if(epoch!==generation.current)return;
      setSelection(current);setStep('form');notifier.current(current);
    });
  }
  function change(step:'source'|'economics') {
    if(disabled)return;
    clearSelection();setStep(step);setError(null);
  }
  return <section className="source-farm-selector" aria-label="저장 원천과 경제 판본 선택">
    <ol className="source-farm-progress" aria-label="자료 선택 순서">
      <li aria-current={step==='source'?'step':undefined}><span>01</span> 원천 선택</li>
      <li aria-current={step==='economics'?'step':undefined}><span>02</span> 경제 판본 확인</li>
      <li aria-current={step==='form'?'step':undefined}><span>03</span> 농장 조건 작성</li>
    </ol>
    {error&&<p className="notice error" role="alert">{error}</p>}
    {busy&&<p className="muted" role="status">{busy==='selection'?'선택한 경제 판본의 현재 권리 확인 중…':
      busy==='source'?'정확한 조사·수집의 현재 참조 확인 중…':'저장 기록 조회 중…'}</p>}
    {step==='source'&&<>
      <div className="source-farm-heading"><div><h4>저장된 조사와 수집 선택</h4>
        <p>현재 계정의 완료 기록을 선택하세요. 기록의 작업 완료는 자료 승인이나 계산 완료를 뜻하지 않습니다.</p></div>
        <button type="button" className="button secondary" disabled={disabled}
          onClick={()=>void loadHistory()}>저장 조사 조회</button></div>
      <div className="source-farm-columns"><section className="source-farm-card" aria-label="완료 조사 선택">
        <h4>완료 조사</h4>
        {!history?<p className="muted">저장 조사 조회 버튼으로 기록을 불러오세요.</p>:history.items.length?
          <ul className="source-farm-list">{history.items.map(item=><li key={item.job.job_id}>
            <button type="button" disabled={disabled||item.job.state!=='succeeded'||item.current_authority==='hold'}
              aria-pressed={research?.job.job_id===item.job.job_id} onClick={()=>void chooseResearch(item)}>
              <strong>좌표 {item.point.latitude}, {item.point.longitude}</strong>
              <span>{item.period_start_utc} ~ {item.period_end_utc}</span><code>{item.job.job_id}</code>
              <small>{states[item.job.state]} · {item.current_authority==='hold'?'현재 근거 보류':'선택 시 현재 참조 재확인'}</small>
            </button></li>)}</ul>:<p className="muted" role="status">현재 계정에 저장된 조사 기록이 없습니다.</p>}
        {history?.next_cursor&&<button type="button" className="button secondary" disabled={disabled}
          onClick={()=>void loadHistory(true)}>이전 조사 더 보기</button>}
      </section><section className="source-farm-card" aria-label="해당 조사의 완료 수집 선택">
        <h4>해당 조사의 수집·검토 기록</h4>
        {!research?<p className="muted">먼저 완료 조사를 선택하세요.</p>:!activity?
          <p className="muted">조사 기록을 다시 선택해 수집 이력을 확인하세요.</p>:activity.items.length?
          <ul className="source-farm-list">{activity.items.map(item=><li key={item.job.job_id}>
            {item.kind==='collection'?<button type="button" disabled={disabled||item.job.state!=='succeeded'}
              onClick={()=>void chooseCollection(item)}><strong>원본 수집 · {states[item.job.state]}</strong>
              <code>{item.job.job_id}</code><small>{item.job.created_at} · 현재 참조 확인</small></button>:
              <div className="source-farm-review"><strong>수집 검토 · {states[item.job.state]}</strong>
                <code>{item.job.job_id}</code><small>수집 {item.collection_job.job_id}</small></div>}
          </li>)}</ul>:<p className="muted" role="status">이 조사에 저장된 수집 기록이 없습니다.</p>}
        {activity?.next_cursor&&<button type="button" className="button secondary" disabled={disabled}
          onClick={()=>void loadActivity()}>이전 수집·검토 더 보기</button>}
      </section></div>
    </>}
    {source&&step!=='source'&&<div className={step==='form'?'source-farm-pinned-columns':'source-farm-context'}>
      <section className="source-farm-summary" aria-label="선택한 원천 참조">
        <div className="source-farm-heading"><h4><img src={sourceDocumentIcon} alt="" width={28} height={28}/>
          같은 원천에 묶인 참조</h4>
          <button type="button" className="button secondary" disabled={disabled}
            onClick={()=>change('source')}>원천 다시 선택</button></div>
        <dl><div><dt>좌표</dt><dd>{source.point.latitude}, {source.point.longitude}</dd></div>
          <div><dt>원본 기간 · UTC</dt><dd>{source.period_start_utc} ~ {source.period_end_utc}</dd></div>
          <div><dt>결정 시각 · UTC</dt><dd>{source.decision_at_utc} · {source.decision_time_kind==='hypothetical'?'가상 결정 시각':'실제 결정 시각'}</dd></div></dl>
        <details className="source-farm-reference-details"><summary>조사·수집 식별자 상세</summary>
          <dl><div><dt>조사</dt><dd><code>{source.research_job_id}</code></dd></div>
            <div><dt>수집</dt><dd><code>{source.collection_job_id}</code></dd></div></dl>
        </details>
        <p className="source-farm-hold">소프트웨어 시험용 · 사후 재현 · G0/G1 미수용 · 판단 보류</p>
      </section>
      {step==='economics'&&<section className="source-farm-card" aria-label="같은 원천의 경제 판본 선택">
        <div className="source-farm-heading"><div><h4>같은 문맥의 저장 경제 판본</h4>
          <p>목록은 과거 기록입니다. 선택한 판본의 현재 권리와 연결을 다시 확인합니다.</p></div>
          <button type="button" className="button secondary" disabled={disabled}
            onClick={()=>void loadEconomics()}>{economics?'경제 목록 새로고침':'경제 판본 조회'}</button></div>
        {!economics?<p className="muted">경제 판본 조회 버튼으로 연결된 기록을 확인하세요.</p>:economics.items.length?
          <ul className="source-farm-economic-list">{economics.items.map(item=><li key={item.economic.candidate_id}>
            <div><strong>{item.economic.scenario_id} / {item.economic.revision}</strong>
              <span>{item.period_start} ~ {item.period_end} · KST 평가 날짜</span>
              <small>기록 {item.recorded_at}</small><code>{item.economic.candidate_id}</code>
              <small>시장 자료 보류 · {item.market_context.hold_report_id}</small></div>
            <button type="button" className="button secondary" disabled={disabled}
              aria-label={item.economic.scenario_id+' '+item.economic.revision+' 현재 참조 확인'}
              onClick={()=>void chooseEconomic(item)}>현재 참조 확인</button>
          </li>)}</ul>:<p className="source-farm-hold" role="status">같은 원천 문맥에 연결된 저장 경제 판본이 없습니다.
            경제 입력 화면에서 사용자 가정과 판본을 준비한 뒤 다시 조회하세요. 임의 판본을 만들지 않습니다.</p>}
        {economics?.next_cursor&&<button type="button" className="button secondary" disabled={disabled}
          onClick={()=>void loadEconomics(true)}>이전 경제 판본 더 보기</button>}
      </section>}
      {step==='form'&&selection&&<section className="source-farm-selected" aria-label="작성에 연결된 경제 판본">
        <div className="source-farm-heading"><h4>{selection.economic.scenario_id} / {selection.economic.revision}</h4>
          <button type="button" className="button secondary" disabled={disabled}
            onClick={()=>change('economics')}>경제 판본 다시 선택</button></div>
        <p>평가 날짜 {selection.period_start} ~ {selection.period_end} · 등록 시 현재 권리 재검사</p>
        <p className="muted">아래 참조는 읽기 전용입니다. 시설 수치·작성 출처·권리 선언은 직접 확인하세요.</p>
      </section>}
    </div>}
  </section>;
}
