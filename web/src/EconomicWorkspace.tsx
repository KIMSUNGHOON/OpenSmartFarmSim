import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ApiError, type createApi, type JobStatus } from './api';
import { decimal, type SourceKind, type SourceMeta, type SourcePage, type NumericRecord, type NumericIntent,
  type SourceSaved, type Baseline, type Shock, type Candidate, type ScenarioIntent, type CalculationIntent,
  type EconomicResult } from './economic-api';

type Client=ReturnType<typeof createApi>;
const names:Record<SourceKind,string>={economic_input:'숫자 가정',economic_scenario:'기준 원장',joint_shock:'수급·거시 공동 가정'};
const errors:Record<string,string>={auth_required:'접근 토큰을 확인해 주세요.',access_denied:'이 계정에 필요한 경제 입력·계산 권한이 없습니다.',
  not_available:'아직 열람할 수 있는 입력 또는 완료 결과가 없습니다.',invalid_request:'판본·권리·결정 시각과 원장 연결을 확인해 주세요.',
  intent_conflict:'같은 요청에 다른 입력이 이미 등록되어 있습니다.',response_rejected:'서버 응답을 확인할 수 없어 표시를 보류했습니다.',
  too_large:'입력이 서버의 크기 한도를 넘었습니다.',server_unavailable:'접수 여부를 확인하지 못했습니다. 같은 요청을 다시 확인해 주세요.',
  network_unresolved:'응답을 받지 못했습니다. 같은 요청을 다시 확인해 주세요.',invalid_assumption:'가정값과 알게 된 UTC 날짜·시각을 확인해 주세요.',
  assumption_mismatch:'공동 가정이 선택한 기준 원장·결정 시각과 맞지 않습니다.'};
function money(value:string|null) {
  if(value===null) return '미확인';
  const [whole,fraction]=value.split('.');
  return (whole ?? '').replace(/\B(?=(\d{3})+(?!\d))/g,',')+(fraction===undefined ? '' : '.'+fraction)+' 원';
}
export default function EconomicWorkspace({api,onPending,blocked}:{api:Client|null;onPending:(value:boolean)=>void;blocked:boolean}) {
  const [pages,setPages]=useState<Partial<Record<SourceKind,SourcePage>>>({});
  const [numeric,setNumeric]=useState<NumericRecord|null>(null); const [value,setValue]=useState('');
  const [knownDate,setKnownDate]=useState('');const [knownTime,setKnownTime]=useState('');
  const [saved,setSaved]=useState<SourceSaved|null>(null);
  const [baseline,setBaseline]=useState<Baseline|null>(null);const [shock,setShock]=useState<Shock|null>(null);
  const [candidate,setCandidate]=useState<Candidate|null>(null);const [job,setJob]=useState<JobStatus|null>(null);
  const [result,setResult]=useState<EconomicResult|null>(null);const [busy,setBusy]=useState(false);
  const [error,setError]=useState<ApiError|null>(null);const [unresolved,setUnresolved]=useState(false);
  const sourceIntent=useRef<NumericIntent|null>(null);
  const flow=useRef<{scenario:ScenarioIntent;candidate:Candidate|null;calculation:CalculationIntent|null}|null>(null);
  const pending=useRef(false);const inFlight=useRef(false);const epoch=useRef(0);
  useEffect(()=>{
    epoch.current++;sourceIntent.current=null;flow.current=null;pending.current=false;onPending(false);
    setPages({});setNumeric(null);setSaved(null);setBaseline(null);setShock(null);setCandidate(null);setJob(null);
    setResult(null);setValue('');setKnownDate('');setKnownTime('');setError(null);setUnresolved(false);
  },[api,onPending]);
  async function perform(action:(client:Client,current:()=>boolean)=>Promise<void>) {
    if(!api || inFlight.current || blocked) {if(!api)setError(new ApiError('auth_required'));return;}
    const version=epoch.current;inFlight.current=true;setBusy(true);onPending(true);setError(null);
    const current=()=>version===epoch.current;
    try {await action(api,current);}
    catch(error) {
      if(current()) {
        const failure=error instanceof ApiError ? error : new ApiError('network_unresolved');setError(failure);
        if(failure.status!==null && failure.status<500) pending.current=false;
        setUnresolved(pending.current);
      }
    } finally {inFlight.current=false;if(current()){setBusy(false);onPending(pending.current);}}
  }
  function page(kind:SourceKind,next=false) {
    void perform(async (client,current)=>{
      const cursor=next ? pages[kind]?.next_cursor : null;
      const response=await client.sources(kind,cursor ?? undefined);
      if(current())setPages(old=>({...old,[kind]:response}));
    });
  }
  function choose(kind:SourceKind,ref:SourceMeta) {
    void perform(async (client,current)=>{
      if(kind==='economic_input') {
        const response=await client.numeric(ref);if(!current())return;
        setNumeric(response);setValue(response.input.value);setKnownDate('');setKnownTime('');setSaved(null);sourceIntent.current=null;
      } else if(kind==='economic_scenario') {
        const response=await client.baseline(ref);if(current())setBaseline(response);
      } else {const response=await client.shock(ref);if(current())setShock(response);}
    });
  }
  function save(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();if(!numeric)return;
    void perform(async (client,current)=>{
      if(!sourceIntent.current) {
        const at=new Date(knownDate+'T'+knownTime+':00Z');
        if(!decimal(value) || !/^\d{4}-\d\d-\d\d$/.test(knownDate) || !/^\d\d:\d\d$/.test(knownTime)
          || !Number.isFinite(at.getTime()) || at.toISOString().slice(0,16)!==knownDate+'T'+knownTime) throw new ApiError('invalid_assumption');
        const revision='web-'+crypto.randomUUID();
        sourceIntent.current={kind:'economic_input',input:{...numeric.input,value,revision,
          available_at:knownDate+'T'+knownTime+':00Z',source_ref:'user-entry-'+revision},idempotency_key:'web-economic-input-v1:'+crypto.randomUUID()};
      }
      pending.current=true;setUnresolved(true);
      const response=await client.saveNumeric(sourceIntent.current);
      if(current()) {setSaved(response);pending.current=false;setUnresolved(false);}
    });
  }
  function calculate() {
    if(!baseline || !shock)return;
    void perform(async (client,current)=>{
      if(!flow.current) {
        if(baseline.payload_sha256!==shock.baseline_sha256 || baseline.decision_at!==shock.decision_at)
          throw new ApiError('assumption_mismatch');
        flow.current={candidate:null,calculation:null,scenario:{request:{schema_version:'1',
          baseline:{scenario_id:baseline.record_id,revision:baseline.revision,sha256:baseline.payload_sha256},
          shock:{shock_id:shock.record_id,revision:shock.revision,sha256:shock.payload_sha256},decision_at:baseline.decision_at,
          market_context:baseline.market_context},idempotency_key:'web-economic-scenario-v1:'+crypto.randomUUID()}};
      }
      pending.current=true;setUnresolved(true);
      const pinned=flow.current;
      if(!pinned.candidate) {
        const registered=await client.scenario(pinned.scenario);if(!current())return;
        pinned.candidate=registered;setCandidate(registered);
      }
      if(!pinned.calculation) pinned.calculation={input_version:'economic-calculation-input-v1',
        scenario_id:pinned.candidate.scenario_id,scenario_revision:pinned.candidate.scenario_revision,
        scenario_sha256:pinned.candidate.scenario_sha256,candidate_id:pinned.candidate.candidate_id,
        formula_version:'economic-ledger-v9-sales-settlement',idempotency_key:'web-economic-calculation-v1:'+crypto.randomUUID()};
      const response=await client.calculate(pinned.calculation);
      if(current()){setJob(response);setResult(null);pending.current=false;setUnresolved(false);}
    });
  }
  function refresh() {
    if(!job || !candidate || !flow.current)return;
    const context=flow.current.scenario.request;
    void perform(async (client,current)=>{
      const status=await client.job(job.job_id);if(!current())return;setJob(status);setResult(null);
      if(status.stage!=='simulation')throw new ApiError('response_rejected');
      if(status.state==='succeeded') {
        const response=await client.economicResult(status.job_id,candidate,context);
        if(current())setResult(response);
      }
    });
  }
  const disabled=busy || blocked;const selectionLocked=disabled || unresolved || flow.current!==null;
  function picker(kind:SourceKind) {
    const data=pages[kind];return <section className="source-picker" aria-label={names[kind]}>
      <div className="picker-heading"><h3>{names[kind]}</h3><button type="button" className="button secondary" disabled={selectionLocked}
        onClick={()=>page(kind)}>목록 조회</button></div>
      {data ? data.items.length ? <ul>{data.items.map(item=><li key={JSON.stringify([item.record_id,item.revision])}>
        <button type="button" disabled={selectionLocked} onClick={()=>choose(kind,item)}><strong>{item.record_id}</strong>
          <span>판본 {item.revision}</span><small>사용자 가정 · {item.recorded_at}</small></button></li>)}</ul>
        : <p>등록된 {names[kind]}이 없습니다. 원장·입력과 적용 근거를 먼저 등록해야 합니다.</p>
        : <p>이 계정의 저장 목록을 아직 조회하지 않았습니다.</p>}
      {data?.next_cursor && <button type="button" className="button secondary" disabled={selectionLocked} onClick={()=>page(kind,true)}>다음 판본 목록</button>}
    </section>;
  }
  return <div className="economic-workspace">
    {error && <div role="alert" className="notice error">{errors[error.code] ?? '요청을 확인할 수 없습니다.'}</div>}
    <div className="notice"><strong>사용자 가정의 조건부 계산</strong><p>수확·가격·판매량의 예측과 작물 순위는 독립 근거가 필요한 기능입니다.
      여기서는 저장된 가정과 서버 계산을 확인합니다.</p></div>
    <div className="economic-layout">
      <section className="panel" id="viewport-1-d-assumptions"><p className="step-number">01 / 사용자 가정</p><h2>가정 입력과 판본</h2>
        {picker('economic_input')}
        {numeric && <form onSubmit={save} className="assumption-form">
          <p><strong>{numeric.record_id}</strong><br/>적용 기간: {numeric.input.scope_start} ~ {numeric.input.scope_end}</p>
          <details><summary>원본 가정의 입력 근거</summary><dl className="job-facts">
            <div><dt>가정 범위</dt><dd>{numeric.input.assumption_scope}</dd></div>
            <div><dt>입력 근거</dt><dd>{numeric.input.source_ref}</dd></div>
            <div><dt>알게 된 시각 (UTC)</dt><dd>{numeric.input.available_at}</dd></div>
          </dl></details>
          <label>새 가정값 ({numeric.input.unit})<input type="text" inputMode="decimal" maxLength={64} required
            value={value} readOnly={!!sourceIntent.current} onChange={event=>setValue(event.target.value)}/></label>
          <p className="muted">0은 명시적인 가정입니다. 모르는 값은 숫자로 채우지 마세요. 쉼표 없이 입력하세요.</p>
          <div className="field-row"><label>가정을 알게 된 날짜 (UTC)<input type="date" value={knownDate} required
            readOnly={!!sourceIntent.current} onChange={event=>setKnownDate(event.target.value)}/></label>
            <label>가정을 알게 된 시각 (UTC)<input type="time" value={knownTime} required step="60"
              readOnly={!!sourceIntent.current} onChange={event=>setKnownTime(event.target.value)}/></label></div>
          <p className="muted">결정 시점 뒤에 알게 된 정보는 과거 판단의 입력으로 쓸 수 없습니다.</p>
          <button className="button primary" disabled={disabled || !!flow.current || !!saved}>
            {sourceIntent.current ? '같은 가정 요청 다시 확인' : '새 가정 판본 등록'}</button>
          {saved && <div className="notice" role="status"><strong>새 가정 판본 접수됨</strong><p>{saved.revision}</p>
            <p>등록한 숫자는 선택 원장에 아직 반영되지 않았습니다. 이 판본을 참조하는 원장을 별도로 등록·검토해야 계산에 사용할 수 있습니다.</p></div>}
          {sourceIntent.current && !unresolved && <button type="button" className="button secondary" disabled={disabled}
            onClick={()=>{sourceIntent.current=null;setSaved(null);setError(null);}}>새 수정 시작</button>}
        </form>}
        <div className="scenario-pickers">{picker('economic_scenario')}{picker('joint_shock')}</div>
        {baseline && <p className="selected-source">선택 원장: <strong>{baseline.record_id} / {baseline.revision}</strong><br/>
          원장 기간: {baseline.period_start} ~ {baseline.period_end}<br/>결정 시각: {baseline.decision_at}</p>}
        {shock && <p className="selected-source">선택 공동 가정: <strong>{shock.record_id} / {shock.revision}</strong></p>}
        <p className="muted">위에 선택한 원장·공동 가정의 고정 판본으로 계산합니다. 새 숫자는 원장·권리 연결을 확인한 뒤 사용할 수 있습니다.</p>
        <div className="economic-actions"><button className="button primary" disabled={disabled || !baseline || !shock || unresolved && !flow.current}
          onClick={calculate}>{flow.current ? '같은 계산 요청 다시 확인' : '선택한 가정으로 계산 요청'}</button>
          {flow.current && !unresolved && <button className="button secondary" disabled={disabled} onClick={()=>{
            flow.current=null;setCandidate(null);setJob(null);setResult(null);setError(null);}}>새 계산 선택</button>}</div>
      </section>
      <div className="economic-results" id="viewport-1-d-results"><section className="panel"><p className="step-number">02 / 조건부 결과</p><h2>서버 원장 계산</h2>
        <p>서버가 완료된 작업의 입력·영수증·원장을 대사한 결과를 표시합니다.</p>
        {job && <p role="status">계산 작업: {({queued:'대기 중',simulating:'계산 중',succeeded:'작업 완료',hold:'계산 보류',failed:'실행 실패',canceled:'취소됨'} as Record<string,string>)[job.state] ?? '상태 확인 필요'}</p>}
        <button className="button secondary" disabled={disabled || unresolved || !job} onClick={refresh}>계산 상태·결과 확인</button>
        {job && <details className="economic-job-reference"><summary>계산 작업 식별자</summary><code>{job.job_id}</code></details>}
        {result ? <><p className="badge">사용자 가정 · {result.calculation_status==='hold' ? '계산 보류' : '조건부 산술'}</p>
          <div className="economic-totals">{([['매출','revenue_krw'],['관리용 영업이익','management_operating_income_krw'],['현금 부족','cash_shortage_krw']] as const).map(([label,key])=>
            <div key={key}><h3>{label}</h3><strong>{money(result.amounts[key])}</strong><small>선택 원장·공동 가정 기준</small></div>)}</div>
          <details><summary>비용·현금 세부 합계</summary><dl className="job-facts">
            {([['변동비','variable_cost_krw'],['고정비','fixed_cost_krw'],['감가상각','depreciation_krw'],['영업 현금','operating_cash_krw'],
              ['사업 현금','business_cash_krw'],['자기자본 현금','equity_cash_krw'],['최저 현금잔액','minimum_cash_balance_krw']] as const).map(([label,key])=>
              <div key={key}><dt>{label}</dt><dd>{money(result.amounts[key])}</dd></div>)}</dl></details>
          <p className="muted">산식: {result.formula_version}<br/>결과 원장: {result.scenario_id} / {result.scenario_revision}</p>
        </> : <p className="empty-result">완료된 서버 결과를 아직 확인하지 않았습니다. 미확인 금액은 0원으로 표시하지 않습니다.</p>}
      </section><section className="panel" id="viewport-1-d-evaluation"><p className="step-number">03 / 평가 근거</p>
        <h2>{result ? '경제 결과의 평가 상태: 판단 보류' : '경제 결과의 평가 상태'}</h2>
        <p>{result ? '서버 결과의 시장 문맥은 자료 이용 불가이며 평가 상태는 보류입니다.' : '서버 경제 결과를 받으면 시장 문맥과 평가 상태를 확인합니다.'}</p>
        {result && <p>추가 확인이 필요한 계산 근거: {result.hold_reason_codes.length}개</p>}
        <p className="muted">작물 선택과 미래 사업성 판단에는 독립적인 현장 측정, 미래 검증, 같은 조건의 후보 비교가 필요합니다.</p>
      </section></div>
    </div>
  </div>;
}
