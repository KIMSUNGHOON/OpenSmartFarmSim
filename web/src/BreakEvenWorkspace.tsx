import {useEffect,useRef,useState,type FormEvent} from 'react';
import {ApiError,type createApi,type JobStatus} from './api';
import {member} from './api-validation';
import {decimal,type Baseline,type SourceMeta,type SourcePage,type JointRecord,type Candidate,type ScenarioIntent} from './economic-api';
import {TARGETS,VARIABLES,type SaleTerms,type BreakEvenRequest,type BreakEvenSubmission,type BreakEvenResult} from './break-even-api';
import {money} from './economic-format';

type Client=ReturnType<typeof createApi>;
type Flow={request:BreakEvenRequest;registrations:{intent:ScenarioIntent;candidate:Candidate|null}[];
  submission:BreakEvenSubmission|null;planAttempted:boolean};
const targets={oi:'관리용 영업이익',operating_cash:'영업 현금',cumulative_equity_cash:'투자·금융 포함 자기자본 누적 순현금'};
const states:Record<string,string>={queued:'대기 중',simulating:'계산 중',succeeded:'작업 완료',hold:'계산 보류',failed:'실행 실패',canceled:'취소됨'};
const explanations={zero_on_grid:'나열한 시험값에서 목표가 0인 점을 확인했습니다.',
  no_zero_on_grid:'나열한 시험값에서는 목표가 0인 점이 없습니다. 값 사이의 연속 해가 없다는 뜻은 아닙니다.',
  bracket_only:'인접한 시험값 사이에서 목표의 부호가 바뀝니다. 이 구간은 정확한 손익분기점이 아닙니다.',
  nonmonotone_on_grid:'시험값에 따라 목표가 한 방향으로 움직이지 않습니다. 하나의 보편적인 기준값으로 요약할 수 없습니다.',
  hold:'이 목표를 계산할 근거가 부족합니다. 시험 금액을 만들지 않습니다.'};
const errors:Record<string,string>={auth_required:'접근 토큰을 확인해 주세요.',access_denied:'손익분기 입력·계산·조회 권한을 확인해 주세요.',
  invalid_request:'시험 순서·범위·날짜·권리·고정 가정과 정산 연결을 확인해 주세요.',invalid_grid:'목표·단위·판매·수금을 선택하고 음수가 아닌 범위와 0보다 큰 증분을 입력하세요.',
  assumption_mismatch:'이 공동 가정은 선택한 원장·결정 시각과 맞지 않습니다.',not_available:'선택한 기록 또는 완료 결과를 조회할 수 없습니다.',
  response_rejected:'서버 응답이 고정한 계획과 맞지 않아 표시를 보류했습니다.',intent_conflict:'같은 계획 식별자에 다른 입력이 등록되어 있습니다.',
  receipt_pending:'저장된 계획 접수를 아직 확인하지 못했습니다. 원래 요청을 유지하고 접수 기록을 다시 확인하세요.',
  server_unavailable:'접수 여부를 확인하지 못했습니다. 같은 계획 요청을 다시 확인하세요.',network_unresolved:'응답을 받지 못했습니다. 같은 계획 요청을 다시 확인하세요.',too_large:'요청 또는 응답이 허용 크기를 넘었습니다.'};
const timeNames:Record<string,string>={dispatch_at:'출하',delivery_at:'인도',inspection_at:'검수',recognized_at:'판매 인정',collection_at:'수금'};
export default function BreakEvenWorkspace({api,blocked,onPending}:{api:Client|null;blocked:boolean;onPending:(value:boolean)=>void}) {
  const [baselinePage,setBaselinePage]=useState<SourcePage|null>(null),[shockPage,setShockPage]=useState<SourcePage|null>(null);
  const [baseline,setBaseline]=useState<Baseline|null>(null),[sales,setSales]=useState<SaleTerms[]>([]),[saleKey,setSaleKey]=useState('');
  const [preview,setPreview]=useState<JointRecord|null>(null),[trials,setTrials]=useState<JointRecord[]>([]);
  const [target,setTarget]=useState(''),[variable,setVariable]=useState(''),[minimum,setMinimum]=useState(''),[maximum,setMaximum]=useState(''),[step,setStep]=useState('');
  const [busy,setBusy]=useState(false),[error,setError]=useState<ApiError|null>(null),[unresolved,setUnresolved]=useState(false);
  const [phase,setPhase]=useState(''),[job,setJob]=useState<JobStatus|null>(null),[result,setResult]=useState<BreakEvenResult|null>(null);
  const flow=useRef<Flow|null>(null),pending=useRef(false),inFlight=useRef(false),epoch=useRef(0);
  useEffect(()=>{
    epoch.current++;flow.current=null;pending.current=false;onPending(false);setBaselinePage(null);setShockPage(null);setBaseline(null);setSales([]);setSaleKey('');
    setPreview(null);setTrials([]);setTarget('');setVariable('');setMinimum('');setMaximum('');setStep('');setError(null);setUnresolved(false);setJob(null);setResult(null);setPhase('');
  },[api,onPending]);
  async function perform(action:(client:Client,current:()=>boolean)=>Promise<void>) {
    if(!api || blocked || inFlight.current){if(!api)setError(new ApiError('auth_required'));return;}
    const generation=epoch.current;inFlight.current=true;setBusy(true);setError(null);onPending(true);const current=()=>generation===epoch.current;
    try {await action(api,current);}
    catch(error) {if(current()){
      const failure=error instanceof ApiError ? error : new ApiError('network_unresolved');setError(failure);
      setPhase('요청 응답을 확인하지 못했습니다. 보류 사유를 확인하세요.');
      if(failure.status!==null && failure.status<500)pending.current=false;setUnresolved(pending.current);
    }} finally {inFlight.current=false;if(current()){setBusy(false);onPending(pending.current);}}
  }
  function catalog(kind:'economic_scenario'|'joint_shock',next=false) {
    void perform(async(client,current)=>{
      const page=kind==='economic_scenario' ? baselinePage : shockPage;
      const response=await client.sources(kind,next ? page?.next_cursor ?? undefined : undefined);
      if(current())(kind==='economic_scenario' ? setBaselinePage : setShockPage)(response);
    });
  }
  function choose(kind:'economic_scenario'|'joint_shock',ref:SourceMeta) {
    void perform(async(client,current)=>{
      if(kind==='economic_scenario') {
        const chosen=await client.baseline({record_id:ref.record_id,revision:ref.revision});
        if(chosen.payload_sha256!==ref.payload_sha256)throw new ApiError('response_rejected');
        const rows=await client.breakEvenSales(chosen);if(!current())return;
        setBaseline(chosen);setSales(rows);setSaleKey('');setPreview(null);setTrials([]);
      } else {
        const chosen=await client.joint({record_id:ref.record_id,revision:ref.revision});
        if(chosen.payload_sha256!==ref.payload_sha256)throw new ApiError('response_rejected');
        if(!baseline || chosen.baseline_sha256!==baseline.payload_sha256 || chosen.decision_at!==baseline.decision_at)throw new ApiError('assumption_mismatch');
        if(current())setPreview(chosen);
      }
    });
  }
  function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();void perform(async(client,current)=>{
      if(!flow.current) {
        const sale=sales.find(row=>JSON.stringify([row.sale_id,row.collection_id])===saleKey);
        if(!baseline || !sale || !member(target,TARGETS) || !member(variable,VARIABLES) || trials.length<2
          || ![minimum,maximum,step].every(value=>decimal(value)) || /^0(?:\.0+)?$/.test(step))throw new ApiError('invalid_grid');
        const request:BreakEvenRequest={schema_version:'1',plan_id:'web-break-even-v1:'+crypto.randomUUID(),
          baseline:{scenario_id:baseline.record_id,revision:baseline.revision,sha256:baseline.payload_sha256},
          decision_at:baseline.decision_at,market_context:baseline.market_context,period_start:baseline.period_start,period_end:baseline.period_end,
          ...sale,target,variable,minimum,maximum,step};
        flow.current={request,submission:null,planAttempted:false,registrations:trials.map(trial=>({candidate:null,intent:{request:{schema_version:'1',
          baseline:request.baseline,decision_at:request.decision_at,market_context:request.market_context,
          shock:{shock_id:trial.record_id,revision:trial.revision,sha256:trial.payload_sha256}},idempotency_key:'web-break-even-scenario-v1:'+crypto.randomUUID()}}))};
      }
      const pinned=flow.current;pending.current=true;setUnresolved(true);setResult(null);
      for(const [index,registration] of pinned.registrations.entries()) {
        if(registration.candidate)continue;setPhase(`시험 ${index+1}/${pinned.registrations.length} 시나리오 접수 확인`);
        const candidate=await client.scenario(registration.intent);if(!current())return;registration.candidate=candidate;
      }
      if(!pinned.submission)pinned.submission={request:pinned.request,trials:pinned.registrations.map(row=>({scenario_id:row.candidate!.scenario_id,
        revision:row.candidate!.scenario_revision,scenario_sha256:row.candidate!.scenario_sha256}))};
      setPhase('손익분기 계획 접수 확인');
      let accepted;
      if(pinned.planAttempted) {
        try {accepted=await client.breakEvenReceipt(pinned.submission);}
        catch(error) {if(error instanceof ApiError && error.status===409)throw error;throw new ApiError('receipt_pending');}
      } else {
        pinned.planAttempted=true;
        try {accepted=await client.breakEvenPlan(pinned.submission);}
        catch(error) {if(error instanceof ApiError && error.status!==null && error.status<500)pinned.planAttempted=false;throw error;}
      }
      if(!current())return;
      setJob(accepted.intent_job);setPhase('계획 의도 저장됨 · 결과는 아직 확인하지 않았습니다.');pending.current=false;setUnresolved(false);
    });
  }
  function refresh() {
    if(!job || !flow.current?.submission)return;const pinned=flow.current;
    void perform(async(client,current)=>{
      setResult(null);setPhase('손익분기 작업 상태·결과 조회 중');const status=await client.job(job.job_id);if(!current())return;
      if(status.stage!=='simulation')throw new ApiError('response_rejected');setJob(status);
      if(status.state==='succeeded'){const response=await client.breakEvenResult(status.job_id,pinned.submission!);if(current()){setResult(response);setPhase('완료된 서버 손익분기 결과를 확인했습니다.');}}
      else setPhase('작업 상태 조회됨 · 완료 결과는 아직 확인하지 않았습니다.');
    });
  }
  const disabled=busy || blocked,locked=disabled || flow.current!==null;
  function picker(kind:'economic_scenario'|'joint_shock',title:string,page:SourcePage|null) {
    return <section className="source-picker" aria-label={title}><div className="picker-heading"><h3>{title}</h3>
      <button type="button" className="button secondary" disabled={locked || kind==='joint_shock' && !baseline} onClick={()=>catalog(kind)}>목록 조회</button></div>
      {page ? page.items.length ? <ul>{page.items.map(ref=><li key={JSON.stringify([ref.record_id,ref.revision])}>
        <button type="button" disabled={locked} onClick={()=>choose(kind,ref)}><strong>{ref.record_id}</strong><span>판본 {ref.revision}</span></button></li>)}</ul>
        : <p>등록된 판본이 없습니다.</p> : <p>저장된 사용자 가정의 판본을 직접 조회하고 선택하세요.</p>}
      {page?.next_cursor && <button type="button" className="button secondary" disabled={locked} onClick={()=>catalog(kind,true)}>다음 판본 목록</button>}
    </section>;
  }
  return <section className="panel break-even-workspace" aria-label="손익분기 계획과 결과"><p className="step-number">04 / 조건부 손익분기</p>
    <h2>손익분기 계획과 시험 시나리오</h2><p>같은 판매·수금·고정 가정에서 수량 또는 단가를 바꾼 저장 판본을 비교합니다. 미래 이익이나 작물 순위가 아닙니다.</p>
    {error && <p role="alert" className="notice error">{errors[error.code] ?? '요청을 확인할 수 없습니다.'}</p>}
    <div className="break-even-inputs"><div>{picker('economic_scenario','손익분기 기준 원장',baselinePage)}
      {baseline && <><p>선택 원장: <strong>{baseline.record_id} / {baseline.revision}</strong><br/>평가 기간: {baseline.period_start} ~ {baseline.period_end}<br/>결정 시각 (UTC): {baseline.decision_at}</p>
        <label>손익분기 판매·수금<select value={saleKey} disabled={locked} onChange={event=>setSaleKey(event.target.value)}>
          <option value="">판매와 수금을 선택하세요</option>{sales.map(row=><option key={JSON.stringify([row.sale_id,row.collection_id])} value={JSON.stringify([row.sale_id,row.collection_id])}>
            {row.sale_id} / {row.grade} / {row.channel} / 수금 {row.collection_id}</option>)}</select></label>
        {sales.length===0 && <p className="notice">선택할 판매·수금 기록이 없습니다. 실제 원장 기록을 먼저 등록해야 합니다.</p>}
        {sales.filter(row=>JSON.stringify([row.sale_id,row.collection_id])===saleKey).map(row=><details key={saleKey}><summary>고정한 판매·수금 날짜와 범위</summary>
          <p>배치 {row.batch_id} · 등급 {row.grade} · 채널 {row.channel}</p><dl className="job-facts">
            {Object.entries(timeNames).map(([key,label])=><div key={key}><dt>{label} (UTC)</dt><dd>{row[key as keyof SaleTerms]}</dd></div>)}</dl></details>)}</>}
      <form onSubmit={submit} className="assumption-form"><label>손익분기 목표<select value={target} disabled={locked} required onChange={event=>setTarget(event.target.value)}>
        <option value="">목표를 선택하세요</option>{TARGETS.map(value=><option key={value} value={value}>{targets[value]}</option>)}</select></label>
        <p className="muted">영업이익은 발생 기준, 영업 현금은 운영 수금·지급 기준입니다. 자기자본 누적 순현금은 투자·대출·상환을 포함하며 기초 잔액과 구별합니다.</p>
        <label>바꿀 변수<select value={variable} disabled={locked} required onChange={event=>setVariable(event.target.value)}>
          <option value="">수량 또는 단가를 선택하세요</option><option value="kg">판매 수량 (kg)</option><option value="KRW/kg">판매 단가 (원/kg)</option></select></label>
        <div className="field-row">{([['최소 시험값',minimum,setMinimum],['최대 시험값',maximum,setMaximum],['시험값 증분',step,setStep]] as const).map(([label,value,set])=>
          <label key={label}>{label} ({variable || '단위 선택 필요'})<input type="text" inputMode="decimal" maxLength={64} required value={value} readOnly={locked} onChange={event=>set(event.target.value)}/></label>)}</div>
        <p className="muted">쉼표 없이 입력하세요. 0은 명시적 시험값입니다. 서버가 범위·증분과 2~256개 시험 판본의 일치를 검사합니다.</p>
        <button className="button primary" disabled={disabled || !flow.current && (!baseline || !saleKey || trials.length<2 || !target || !variable)}>
          {flow.current ? '같은 손익분기 계획 요청 다시 확인' : '선택한 시험으로 손익분기 요청'}</button>
      </form>
      {flow.current && !unresolved && <button type="button" className="button secondary" disabled={disabled} onClick={()=>{
        flow.current=null;setJob(null);setResult(null);setPhase('');setError(null);}}>새 손익분기 계획 작성</button>}
    </div><div>{picker('joint_shock','손익분기 시험 공동 가정',shockPage)}
      {preview && <div className="amendment-preview"><h3>검토할 공동 가정: {preview.record_id} / {preview.revision}</h3>
        <details><summary>저장된 변경 숫자와 가설</summary>{preview.input.drivers.map(driver=><div key={JSON.stringify([driver.kind,driver.record_id,driver.revision])}>
          <p>{driver.hypothesis}</p><ul>{driver.changes.filter(edit=>edit.number!==null).map((edit,index)=><li key={index}>
            {edit.event_group} / {edit.event_id} / {edit.field}: {edit.number!.value} {edit.number!.unit}</li>)}</ul></div>)}</details>
        <button type="button" className="button secondary" disabled={locked || trials.length>=256 || trials.some(row=>row.record_id===preview.record_id && row.revision===preview.revision)}
          onClick={()=>setTrials(rows=>[...rows,preview])}>이 공동 가정을 시험에 추가</button></div>}
      <h3>시험 순서 · {trials.length}개</h3><p>최소값부터 증분 순서로 저장 판본을 추가하세요. 자동으로 숫자·수금·정산 증거를 만들지 않습니다.</p>
      <ol className="break-even-trials">{trials.map((trial,index)=><li key={JSON.stringify([trial.record_id,trial.revision])}>
        <strong>{trial.record_id} / {trial.revision}</strong><div className="economic-actions">
          <button type="button" className="button secondary" disabled={locked || index===0} aria-label={`시험 ${index+1} 위로`} onClick={()=>setTrials(rows=>{
            const next=[...rows];[next[index-1],next[index]]=[next[index]!,next[index-1]!];return next;})}>위로</button>
          <button type="button" className="button secondary" disabled={locked || index===trials.length-1} aria-label={`시험 ${index+1} 아래로`} onClick={()=>setTrials(rows=>{
            const next=[...rows];[next[index],next[index+1]]=[next[index+1]!,next[index]!];return next;})}>아래로</button>
          <button type="button" className="button secondary" disabled={locked} aria-label={`시험 ${index+1} 제거`} onClick={()=>setTrials(rows=>rows.filter((_,i)=>i!==index))}>제거</button>
        </div></li>)}</ol>
    </div></div>
    {phase && <p role="status" className="notice">{phase}</p>}
    {job && <><p role="status">손익분기 작업: {states[job.state] ?? '상태 확인 필요'}</p>
      <button className="button secondary" disabled={disabled || unresolved} onClick={refresh}>손익분기 상태·결과 확인</button>
      <details className="break-even-job-reference"><summary>손익분기 작업 식별자</summary><code>{job.job_id}</code></details></>}
    {result ? <section aria-label="손익분기 서버 결과"><h3>손익분기 결과 · 평가 상태: 판단 보류</h3><p className="notice">{explanations[result.status]}</p>
      <p>사용자 가정의 조건부 시험 · 목표: {targets[result.target]} · 변수: {result.variable_unit}</p>
      {result.zero_values.length>0 && <p>나열한 시험의 0인 값: {result.zero_values.join(', ')} {result.variable_unit}</p>}
      {result.brackets.length>0 && <ul aria-label="교차 구간">{result.brackets.map((pair,index)=><li key={index}>{pair[0]} ~ {pair[1]} {result.variable_unit} · 정확한 해 아님</li>)}</ul>}
      {result.trials.length>0 && <div className="cash-table-scroll" role="region" tabIndex={0} aria-label="손익분기 시험 표 가로 스크롤"><table className="cash-table">
        <caption>서버 시험 결과 · 목표·잔액·부족액 단위: 원(KRW)</caption><thead><tr>{['시험값 ('+result.variable_unit+')','목표 금액','최저 현금 잔액','현금 부족'].map(label=><th scope="col" key={label}>{label}</th>)}</tr></thead>
        <tbody>{result.trials.map(row=><tr key={row.value}><th scope="row">{row.value}</th><td>{money(row.target_value_krw)}</td><td>{money(row.minimum_cash_balance_krw)}</td><td>{money(row.cash_shortage_krw)}</td></tr>)}</tbody>
      </table></div>}
      <p>추가 확인이 필요한 근거: {result.hold_reason_codes.length}개. 미래 검증·작물 비교·운영 증거는 별도로 필요합니다.</p>
    </section> : <p className="empty-result">완료된 손익분기 결과를 아직 확인하지 않았습니다. 금액과 기준값을 만들지 않습니다.</p>}
  </section>;
}
