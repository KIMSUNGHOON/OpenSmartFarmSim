import { useEffect,useRef,useState } from 'react';
import { ApiError,type createApi,type JobStatus,type JobHold,type CalculationAssessmentIntent } from './api';
import { need } from './api-validation';
import type { AuthoredEconomicSelection,AuthoredEconomicIntent,FinancialHistory,FinancialActivity } from './authored-financial-api';
import type { AuthoredRunRef,AuthoredRunCatalog } from './authored-farm-api';
import type { EconomicResult,CashPage } from './economic-api';
import { money } from './economic-format';

type Api=ReturnType<typeof createApi>;
type Financial={economic:JobStatus|null;result:EconomicResult|null;cash:CashPage|null;assessment:JobStatus|null;hold:JobHold|null};
type Pending={kind:'economic';body:AuthoredEconomicIntent}|{kind:'assessment';body:CalculationAssessmentIntent};
const EMPTY:Financial={economic:null,result:null,cash:null,assessment:null,hold:null};
const states:Record<string,string>={queued:'대기 중',simulating:'계산 중',assessing:'평가 중',succeeded:'작업 완료',
  hold:'판단 보류',failed:'실행 실패',canceled:'취소됨'};
const evidence={market_source_g0:'시장 자료의 권리와 품질',eligible_crop_candidates:'재배 가능한 작물 후보',
  farm_scenario_binding:'시설·재배·경제 조건을 함께 고정한 농장 시나리오',local_measurements_g2:'독립 현장 측정',
  future_validation_g3a:'미사용 기간 미래 수확·경제 검증',paired_comparison_g3b:'같은 조건의 작물 대응 비교'};
const errors:Record<string,string>={auth_required:'접근 토큰을 다시 확인해 주세요.',
  access_denied:'현재 계정에 필요한 조회·접수 권한이 없습니다.',not_available:'현재 열람할 수 있는 저장 기록이 없습니다.',
  invalid_request:'현재 Run과 경제 입력의 연결을 서버에서 확인할 수 없습니다.',
  intent_conflict:'같은 요청 식별자에 다른 입력이 등록되어 있습니다.',
  response_rejected:'응답의 형식이나 연결을 검증할 수 없어 표시를 보류했습니다.',
  network_unresolved:'응답을 받지 못했습니다.',server_unavailable:'현재 서버 근거를 확인할 수 없습니다.'};
function time(value:string) {
  return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',dateStyle:'short',timeStyle:'medium'}).format(new Date(value))+' KST';
}

export default function AuthoredFinancialWorkspace({api,initialJobId,onOpenReplay,onPending,blocked}:{api:Api|null;
  initialJobId?:string;onOpenReplay:(id:string)=>void;onPending:(pending:boolean)=>void;blocked:boolean}) {
  const [catalog,setCatalog]=useState<AuthoredRunCatalog|null>(null);
  const [selected,setSelected]=useState<AuthoredEconomicSelection|null>(null);
  const [history,setHistory]=useState<FinancialHistory|null>(null);
  const [financial,setFinancial]=useState<Financial>(EMPTY);
  const [pending,setPending]=useState<Pending|null>(null);
  const [newRequestReady,setNewRequestReady]=useState(false);
  const [busy,setBusy]=useState(false);const [error,setError]=useState<ApiError|null>(null);
  const generation=useRef(0),inFlight=useRef(false);
  const disabled=!api || busy || blocked;

  useEffect(()=>{onPending(busy || !!pending);},[busy,pending,onPending]);
  useEffect(()=>{
    const epoch=++generation.current;inFlight.current=false;
    setCatalog(null);setSelected(null);setHistory(null);setFinancial(EMPTY);setPending(null);setNewRequestReady(false);setBusy(false);setError(null);
    if(api && initialJobId){
      inFlight.current=true;setBusy(true);onPending(true);
      void loadSelection(api,initialJobId,epoch).catch(value=>{
        if(epoch===generation.current){setSelected(null);setHistory(null);failure(value);}
      }).finally(()=>{if(epoch===generation.current){inFlight.current=false;setBusy(false);}});
    }
    return()=>{generation.current++;};
  },[api,initialJobId]);

  function failure(value:unknown) {setError(value instanceof ApiError?value:new ApiError('network_unresolved'));}
  async function act(work:(client:Api,epoch:number)=>Promise<void>,kind:'read'|'post'='read') {
    if(!api || blocked || inFlight.current || (pending && kind==='read'))return;
    const epoch=generation.current;inFlight.current=true;setBusy(true);onPending(true);setError(null);
    try {await work(api,epoch);}
    catch(value){
      if(epoch!==generation.current)return;
      const problem=value instanceof ApiError?value:new ApiError('network_unresolved');failure(problem);
      setFinancial(previous=>kind==='post'?{...EMPTY,economic:previous.economic}:EMPTY);
      if(kind==='read'){setSelected(null);setHistory(null);}
      else if(problem.status!==null && problem.status>=400 && problem.status<500){
        setPending(null);
        if(problem.status===401 || problem.status===403 || problem.status===404){setSelected(null);setHistory(null);}
      }
    } finally {if(epoch===generation.current){inFlight.current=false;setBusy(false);}}
  }
  async function loadSelection(client:Api,id:string,epoch:number,expectedRun?:string) {
    const value=await client.authoredEconomicSelection(id);
    need(!expectedRun || value.thermal_run.run_id===expectedRun);
    const page=await client.authoredFinancialHistory(value);
    if(epoch!==generation.current)return;
    setSelected(value);setHistory(page);setNewRequestReady(page.items.length===0);
  }
  async function currentSelection(client:Api,value:AuthoredEconomicSelection) {
    const current=await client.authoredEconomicSelection(value.calculation_input.thermal_job_id);
    need(JSON.stringify(current)===JSON.stringify(value));return current;
  }
  async function readMoney(client:Api,id:string,value:AuthoredEconomicSelection):Promise<Financial> {
    const economic=await client.authoredEconomicJob(id);
    const result=economic.state==='succeeded' ? await client.authoredEconomicResult(id,value) : null;
    return {...EMPTY,economic,result};
  }
  function loadCatalog(next=false) {
    void act(async(client,epoch)=>{
      const page=await client.authoredRunCatalog(next?catalog?.next_cursor??undefined:undefined);
      if(epoch===generation.current)setCatalog(previous=>next && previous?{...page,items:[...previous.items,...page.items]}:page);
    });
  }
  function selectRun(item:AuthoredRunRef) {
    if(disabled || pending || inFlight.current)return;
    setSelected(null);setHistory(null);setFinancial(EMPTY);setNewRequestReady(false);
    void act((client,epoch)=>loadSelection(client,item.simulation_job_id,epoch,item.run_id));
  }
  function loadHistory(next=false) {
    if(!selected || inFlight.current)return;
    setFinancial(EMPTY);setNewRequestReady(false);
    void act(async(client,epoch)=>{
      const current=await currentSelection(client,selected);
      const page=await client.authoredFinancialHistory(current,next?history?.next_cursor??undefined:undefined);
      if(epoch===generation.current){
        setHistory(previous=>next && previous?{...page,items:[...previous.items,...page.items]}:page);
        setNewRequestReady(!next && page.items.length===0);
      }
    });
  }
  function openActivity(item:FinancialActivity) {
    if(!selected || disabled || pending || inFlight.current)return;
    setFinancial(EMPTY);setNewRequestReady(false);
    void act(async(client,epoch)=>{
      const current=await currentSelection(client,selected);
      const moneyState=await readMoney(client,item.kind==='economic'?item.job.job_id:item.economic_job.job_id,current);
      if(item.kind==='economic'){
        if(epoch===generation.current)setFinancial(moneyState);return;
      }
      need(moneyState.economic?.state==='succeeded' && moneyState.result);
      const status=await client.assessmentJob(item.job.job_id);
      const report=status.state==='hold' ? await client.assessmentHold(status.job_id) : null;
      if(report)need(report.missing_evidence_count===6 && JSON.stringify(report.missing_evidence)===JSON.stringify(Object.keys(evidence)));
      if(epoch===generation.current)setFinancial({...moneyState,assessment:status,hold:report});
    });
  }
  function refreshMoney() {
    if(!selected || !financial.economic)return;
    openActivity({kind:'economic',job:financial.economic,economic_job:null});
  }
  function refreshAssessment() {
    if(!financial.economic || !financial.assessment)return;
    openActivity({kind:'assessment',job:financial.assessment,economic_job:financial.economic});
  }
  function submit(kind:Pending['kind']) {
    if(!selected || disabled || inFlight.current || (pending && pending.kind!==kind))return;
    if(!pending && kind==='economic' && !newRequestReady)return;
    if(!pending && kind==='assessment' && (!financial.result || financial.economic?.state!=='succeeded'))return;
    const intent=pending ?? (kind==='economic'
      ?{kind,body:{...selected.calculation_input,idempotency_key:'web-authored-money-v1:'+crypto.randomUUID()}}
      :{kind,body:{run_job_id:selected.calculation_input.thermal_job_id,economic_job_id:financial.economic!.job_id,
        idempotency_key:'web-authored-assessment-v1:'+crypto.randomUUID()}});
    setPending(intent);setError(null);
    if(kind==='economic')setFinancial(EMPTY);
    else setFinancial(previous=>({...previous,assessment:null,hold:null,cash:null}));
    void act(async(client,epoch)=>{
      const job=intent.kind==='economic'?await client.calculateAuthored(intent.body):await client.assessCalculations(intent.body);
      if(epoch!==generation.current)return;
      setPending(null);setHistory(null);setNewRequestReady(false);
      setFinancial(previous=>intent.kind==='economic'?{...EMPTY,economic:job}:{...previous,assessment:job});
    },'post');
  }
  function loadCash(next=false) {
    if(!selected || !financial.result || !financial.economic || inFlight.current)return;
    const parent=financial.economic,result=financial.result,after=next?financial.cash?.next_month_cursor??undefined:undefined;
    setFinancial(previous=>({...previous,cash:null}));
    void act(async(client,epoch)=>{
      await currentSelection(client,selected);
      const page=await client.economicCash(parent.job_id,result,after);
      if(epoch===generation.current)setFinancial(previous=>({...previous,cash:page}));
    });
  }

  return <div className="authored-financial-workflow" aria-label="작성 Run 경제와 평가">
    {error && <p className="notice error" role="alert">{errors[error.code] ?? '요청을 확인할 수 없습니다.'}
      {pending && ' 접수 여부가 미확인이므로 같은 요청을 다시 확인하세요.'}</p>}
    {busy && <p role="status">현재 서버 기록 확인 중…</p>}
    <div className="economic-layout">
      <section className="panel"><p className="step-number">01 / 저장 결과 선택</p><h2>저장된 작성 Run</h2>
        <p>완료된 저장 기록을 선택하면 현재 권리·해제와 해당 농장의 경제 입력을 다시 확인합니다.</p>
        <button className="button secondary" disabled={disabled || !!pending} onClick={()=>loadCatalog()}>저장 Run 목록 조회</button>
        {catalog && (catalog.items.length ? <ul className="authored-catalog-list">{catalog.items.map(item=><li key={item.run_id}>
          <button disabled={disabled || !!pending} onClick={()=>selectRun(item)}><span><strong>저장된 합성 열 Run</strong>
            <small>{time(item.recorded_at)}</small><code>{item.run_id}</code></span><span>경제·평가 선택</span></button></li>)}</ul>
          :<p className="muted">현재 계정에 저장된 작성 Run이 없습니다.</p>)}
        {catalog?.next_cursor && <button className="button secondary" disabled={disabled || !!pending} onClick={()=>loadCatalog(true)}>이전 Run 더 보기</button>}
      </section>
      <section className="panel"><p className="step-number">선택한 Run</p><h2>같은 농장 조건 유지</h2>
        {selected ? <><p className="badge">합성 열 재생 · 사용자 가정</p>
          <dl className="job-facts"><div><dt>농장 판본</dt><dd>{selected.thermal_run.scenario_id} / {selected.thermal_run.scenario_revision}</dd></div>
            <div><dt>재생 시작 (UTC)</dt><dd>{selected.thermal_run.start_utc}</dd></div>
            <div><dt>경제 입력 판본</dt><dd>{selected.calculation_input.scenario_id} / {selected.calculation_input.scenario_revision}</dd></div></dl>
          <p>경제 입력은 이 농장에 고정된 사용자 가정입니다. 접수와 결과 조회 시 서버가 근거를 다시 확인합니다.</p>
          <button className="button secondary" disabled={disabled || !!pending}
            onClick={()=>onOpenReplay(selected.calculation_input.thermal_job_id)}>같은 Run 3D 열기</button>
          <details><summary>연결 식별자</summary><code>{selected.thermal_run.run_id}</code><p>{selected.calculation_input.thermal_job_id}</p></details>
        </>:<p className="empty-result">저장 Run을 선택하세요. 미확인 입력과 금액은 계산 결과로 표시하지 않습니다.</p>}
      </section>
    </div>
    {selected && <>
      <div className="economic-layout">
        <section className="panel"><p className="step-number">02 / 조건부 경제</p><h2>서버 금액과 현금흐름</h2>
          <p>판매·비용 가정을 대입한 조건부 계산입니다. 미래 수익과 구매 에너지 비용을 예측한 결과가 아닙니다.</p>
          {!newRequestReady && !financial.economic && history?.items.length!==0 && <p className="notice">저장된 경제·평가 기록을 먼저 선택해 확인하세요. 새 계산은 확인 후 별도로 준비합니다.</p>}
          <div className="economic-actions"><button className="button" disabled={disabled || !!financial.economic || !pending && !newRequestReady || !!pending && pending.kind!=='economic'}
            onClick={()=>submit('economic')}>{pending?.kind==='economic'?'같은 경제 요청 다시 확인':'선택 Run 경제 계산 요청'}</button>
            <button className="button secondary" disabled={disabled || !!pending || !financial.economic} onClick={refreshMoney}>경제 상태·결과 확인</button></div>
          {financial.economic && <><p role="status">경제 작업: {states[financial.economic.state]}</p>
            <details><summary>경제 작업 ID</summary><code>{financial.economic.job_id}</code></details></>}
          {financial.result ? <><p className="badge">사용자 가정 · {financial.result.calculation_status==='hold'?'계산 보류':'조건부 산술'}</p>
            <div className="economic-totals">{([['매출','revenue_krw'],['관리용 영업이익','management_operating_income_krw'],['현금 부족','cash_shortage_krw']] as const)
              .map(([label,key])=><div key={key}><h3>{label}</h3><strong data-money-field={key}>{money(financial.result!.amounts[key])}</strong></div>)}</div>
            <details><summary>조건부 비용·현금 합계</summary><dl className="job-facts">{([['변동비','variable_cost_krw'],['고정비','fixed_cost_krw'],
              ['감가상각','depreciation_krw'],['영업 현금','operating_cash_krw'],['사업 현금','business_cash_krw'],['자기자본 현금','equity_cash_krw']] as const)
              .map(([label,key])=><div key={key}><dt>{label}</dt><dd data-money-field={key}>{money(financial.result!.amounts[key])}</dd></div>)}</dl></details>
          </>:<p className="empty-result">현재 완료 금액을 확인하지 않았습니다. 미확인은 0원이 아닙니다.</p>}
          <section className="cash-panel" aria-label="작성 Run 월별 현금흐름"><h3>월별 현금흐름</h3>
            <button className="button secondary" disabled={disabled || !!pending || !financial.result} onClick={()=>loadCash()}>작성 Run 월별 현금 조회</button>
            {financial.cash && (financial.cash.series_status==='unavailable'?<p role="status">월별 현금흐름: 미확인</p>:<>
              <div className="cash-table-scroll" tabIndex={0} role="region" aria-label="작성 Run 현금 표 가로 스크롤"><table className="cash-table">
                <caption>한국 월 기준 · 금액: 원(KRW) · 최저 잔액 시각: UTC</caption><thead><tr>{['월','기초 잔액','순현금','기말 잔액','최저 잔액','최저 시각','현금 부족'].map(label=><th key={label}>{label}</th>)}</tr></thead>
                <tbody>{financial.cash.monthly_cash!.map(row=><tr key={row.month}><th scope="row">{row.month}</th><td>{money(row.opening_balance_krw)}</td>
                  <td>{money(row.net_cash_krw)}</td><td>{money(row.closing_balance_krw)}</td><td>{money(row.minimum_balance_krw)}</td>
                  <td>{row.minimum_at_utc}</td><td>{money(row.cash_shortage_krw)}</td></tr>)}</tbody></table></div>
              {financial.cash.next_month_cursor && <button className="button secondary" disabled={disabled || !!pending} onClick={()=>loadCash(true)}>다음 현금 페이지</button>}
            </>)}
          </section>
          <button className="button secondary" disabled={disabled || !!pending || !financial.economic}
            onClick={()=>{setFinancial(EMPTY);setError(null);setNewRequestReady(true);}}>새 경제 요청 준비</button>
        </section>
        <section className="panel"><p className="step-number">03 / 평가 근거</p><h2>작물 선택 판단 보류</h2>
          <p>경제 계산 완료는 작물 추천 승인이 아닙니다. 독립 자료와 비교 검증이 부족해 작물 선택은 보류합니다.</p>
          <div className="economic-actions"><button className="button" disabled={disabled || !!financial.assessment ||
            !!pending && pending.kind!=='assessment' || !pending && (!financial.result || financial.economic?.state!=='succeeded')}
            onClick={()=>submit('assessment')}>{pending?.kind==='assessment'?'같은 작성 평가 다시 확인':'작성 Run 평가 요청'}</button>
            <button className="button secondary" disabled={disabled || !!pending || !financial.assessment} onClick={refreshAssessment}>작성 평가 상태 확인</button></div>
          {financial.assessment && <><p role="status">평가 작업: {states[financial.assessment.state]}</p>
            <details><summary>작성 평가 작업 ID</summary><code>{financial.assessment.job_id}</code></details></>}
          {financial.hold && <div className="hold-panel"><h3>작성 Run 판단 보류 근거</h3>
            <ul>{financial.hold.missing_evidence.map(code=><li key={code}>{evidence[code as keyof typeof evidence]}</li>)}</ul>
            <p>서버가 기록한 누락 근거 {financial.hold.missing_evidence_count}개입니다.</p></div>}
        </section>
      </div>
      <section className="panel"><p className="step-number">저장 작업 이력</p><h2>같은 Run의 경제·평가 기록</h2>
        <p>이력은 접수 기록입니다. 선택할 때 현재 상태·금액·보류 근거를 다시 읽습니다.</p>
        <button className="button secondary" disabled={disabled || !!pending} onClick={()=>loadHistory()}>경제·평가 기록 새로고침</button>
        {history && (history.items.length?<ul className="authored-catalog-list">{history.items.map(item=><li key={item.job.job_id}>
          <button disabled={disabled || !!pending} onClick={()=>openActivity(item)}><span><strong>{item.kind==='economic'?'경제 계산 기록':'작성 평가 기록'}</strong>
            <small>{time(item.job.created_at)} · {states[item.job.state]}</small><code>{item.job.job_id}</code></span><span>현재 기록 조회</span></button></li>)}</ul>
          :<p className="muted">이 Run에 저장된 경제·평가 작업이 없습니다.</p>)}
        {history?.next_cursor && <button className="button secondary" disabled={disabled || !!pending} onClick={()=>loadHistory(true)}>이전 경제·평가 더 보기</button>}
      </section>
    </>}
  </div>;
}
