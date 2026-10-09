import { lazy,Suspense,useEffect,useMemo,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import { validCycleCropLookup,type CycleCropLookup } from './cycleCropReplay';
import { validCalculationCycleCropLookup } from './calculationCycleCropReplay';
import { createCycleCropWindow,type CycleCropWindowState } from './cycleCropWindow';
import { startupCohortScales } from './coupledCropGeometry';
import { STARTUP_CUMULATIVE,type StartupCropSample,type StartupCropHold } from './startupCropReplay';
import type { CoupledCropState } from './coupledCropReplay';
import researchLeaf from './assets/crop-coupled-design/cutout-39-e57cccea5fd1.png';
import './CropReplay.css';
import './CoupledCropReplay.css';
import './CycleCropReplay.css';
import HarvestReplay from './HarvestReplay';
const Scene=lazy(()=>import('./CoupledCropScene'));
const Chart=lazy(()=>import('./CoupledCropChart'));
type Api=ReturnType<typeof createApi>;
const EMPTY:CycleCropLookup={result_id:'',scenario_id:'',scenario_revision:'',registration_sha256:'',crop_id:''};
const LABELS:Record<keyof CycleCropLookup,string>={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',
  scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const STATE_LABELS={buffer:'버퍼 탄소',leaf:'잎 탄소',stem_root:'줄기·뿌리 탄소',
  temperature_filtered_24h:'24시간 평활 온도',temperature_sum:'온도 합'};
const SAMPLE_LABELS={lai:'잎 면적 지수 (LAI)',fruit_carbohydrate_total:'총 과실 탄소',
  carbon_residual:'탄소 수지 잔차',carbon_residual_budget:'탄소 허용 한도',
  number_residual:'개수 상당량 수지 잔차',number_residual_budget:'개수 상당량 허용 한도'};
const DIAGNOSTIC_LABELS={requested_residual:'요청·실현·유보 수지 잔차',requested_budget:'요청 수지 허용 한도',
  growth_respiration_residual:'생장 호흡 수지 잔차',growth_respiration_budget:'생장 호흡 허용 한도'};
const MESSAGES:Record<string,string>={auth_required:'접근 토큰을 설정해 주세요.',access_denied:'이 계정에는 연구 결과 조회 권한이 없습니다.',
  not_available:'열람 가능한 저장 연구 결과가 없습니다. 결과 ID와 현재 연결을 확인하세요.',
  invalid_request:'현재 권리 또는 농장 연결을 확인할 수 없어 표시를 보류했습니다.',
  response_rejected:'응답의 ID·단위·페이지·연구 범위를 확인할 수 없어 표시를 보류했습니다.',
  request_canceled:'연구 결과 조회를 취소했습니다.',server_unavailable:'현재 서버에서 연구 결과를 조회할 수 없습니다.',
  network_unresolved:'조회 응답을 받지 못했습니다. 다시 조회해 주세요.'};
const NO_SAMPLES:readonly StartupCropSample[]=[];
function Quantity({q}:{q:{value:number;unit:string}}){return <>{String(q.value)}<small>{q.unit}</small></>;}
function Cohorts({state,at,diagnostic=false}:{state:Pick<CoupledCropState,'fruit_carbohydrate'|'fruit_number'>;at:string;diagnostic?:boolean}){
  return <div className="crop-table-scroll" tabIndex={0} role="region" aria-label={diagnostic?'구획 진단':'저장 과실 구획 수치'}>
    <table className={diagnostic?'coupled-diagnostic-table':'coupled-cohort-table'}><caption>구획 1–50 · {at} UTC. N은 개수 상당량입니다.</caption>
      <thead><tr><th scope="col">구획</th><th scope="col">과실 탄소 C<small>{state.fruit_carbohydrate[0]!.unit}</small></th>
        <th scope="col">개수 상당량 N<small>{state.fruit_number[0]!.unit}</small></th></tr></thead>
      <tbody>{state.fruit_carbohydrate.map((q,i)=><tr key={i} data-cohort={i+1}><th scope="row">{i+1}</th>
        <td data-metric="carbon" data-raw-value={q.value}>{String(q.value)}</td>
        <td data-metric="number" data-raw-value={state.fruit_number[i]!.value}>{String(state.fruit_number[i]!.value)}</td></tr>)}</tbody>
    </table></div>;
}
function StateValues({state}:{state:CoupledCropState}){
  return <dl>{(Object.keys(STATE_LABELS) as (keyof typeof STATE_LABELS)[]).map(key=><div key={key}><dt>{STATE_LABELS[key]}</dt>
    <dd data-event-state={key} data-raw-value={state[key].value}><Quantity q={state[key]}/></dd></div>)}</dl>;
}
function Accumulation({sample,diagnostic=false}:{sample:StartupCropSample;diagnostic?:boolean}){
  return <div data-selected-at={sample.at}><p>{sample.at} · UTC</p><dl>{STARTUP_CUMULATIVE.map(key=><div key={key}>
    <dt>{key}</dt><dd data-cumulative={diagnostic?undefined:key} data-confirmed-cumulative={diagnostic?key:undefined}
      data-raw-value={sample.cumulative[key].value}><Quantity q={sample.cumulative[key]}/></dd></div>)}</dl>
    <h3>요청·실현·유보와 생장 호흡 수지</h3><dl>{(Object.keys(DIAGNOSTIC_LABELS) as (keyof typeof DIAGNOSTIC_LABELS)[]).map(key=><div key={key}>
      <dt>{DIAGNOSTIC_LABELS[key]}</dt><dd data-startup-diagnostic={diagnostic?undefined:key} data-confirmed-startup-diagnostic={diagnostic?key:undefined}
        data-raw-value={sample.startup_diagnostics[key].value}><Quantity q={sample.startup_diagnostics[key]}/></dd></div>)}</dl></div>;
}
function Hold({hold}:{hold:StartupCropHold}){
  const confirmed=hold.last_confirmed;
  return <section className="panel crop-hold coupled-hold" aria-label="연결 작물 계산 보류 진단"><h2>계산이 보류되었습니다</h2>
    <strong>{hold.reason_code}</strong><p>수치 검사 시각 {hold.at} · {hold.phase}. 새로운 완료 시점이 아닙니다.</p>
    {confirmed?<details><summary>마지막 확인 진단 · {confirmed.at}</summary><p>확인 단계 {confirmed.phase}. 시간축에 추가하지 않습니다.</p>
      <dl>{(Object.keys(STATE_LABELS) as (keyof typeof STATE_LABELS)[]).map(key=><div key={key}><dt>{STATE_LABELS[key]}</dt>
        <dd><Quantity q={confirmed.state[key]}/></dd></div>)}<div><dt>잎 면적 지수</dt><dd><Quantity q={confirmed.lai}/></dd></div></dl>
      <Cohorts state={confirmed.state} at={confirmed.at} diagnostic/><Accumulation sample={confirmed} diagnostic/>
    </details>:<p>마지막 확인 진단 상태가 없습니다. 확인된 저장 시점이 있다면 아래 범위에서 탐색할 수 있습니다.</p>}
    <p className="crop-caption">확인된 과거 저장 시점만 탐색합니다. 실패한 trial·보류 이후 상태·미래 예측은 표시하지 않습니다.</p>
  </section>;
}
function SampleTable({samples,index,select}:{samples:readonly StartupCropSample[];index:number;select:(index:number)=>void}){
  return <section className="panel"><h2>현재 범위의 저장 시계열</h2><div className="crop-table-scroll" tabIndex={0} role="region" aria-label="연결 작물 저장 시계열 수치">
    <table className="crop-table coupled-time-table"><caption>현재 읽은 원 시점만 표시합니다. 같은 UTC의 기관·LAI·수지를 선택하세요.</caption>
      <thead><tr><th scope="col">저장 시각 (UTC)</th>{Object.values(STATE_LABELS).map(label=><th key={label} scope="col">{label}</th>)}
        {Object.values(SAMPLE_LABELS).map(label=><th key={label} scope="col">{label}</th>)}</tr></thead>
      <tbody>{samples.map((row,i)=><tr key={row.at} aria-selected={i===index}><th scope="row"><button className="crop-time-button" onClick={()=>select(i)}>{row.at}</button></th>
        {(Object.keys(STATE_LABELS) as (keyof typeof STATE_LABELS)[]).map(key=><td key={key} data-metric={key} data-raw-value={row.state[key].value}><Quantity q={row.state[key]}/></td>)}
        {(Object.keys(SAMPLE_LABELS) as (keyof typeof SAMPLE_LABELS)[]).map(key=><td key={key} data-metric={key} data-raw-value={row[key].value}><Quantity q={row[key]}/></td>)}
      </tr>)}</tbody></table></div></section>;
}
export default function CycleCropReplayView({api,initialSelection,autoLoadInitialSelection=false,sourceKind='original',initialHarvestResultId}:{api:Api|null;
  initialSelection?:CycleCropLookup;autoLoadInitialSelection?:boolean;sourceKind?:'original'|'calculation';initialHarvestResultId?:string}){
  const initial=initialSelection?.result_id.startsWith(sourceKind==='calculation'?'crop-cycle-verified-result-v1:':'crop-cycle-result-v1:')?initialSelection:undefined;
  const [lookup,setLookup]=useState(initial??EMPTY),[localError,setLocalError]=useState<ApiError|null>(null);
  const [playing,setPlaying]=useState(false),[reduced,setReduced]=useState(false),owner=useRef({api,sourceKind});
  const viewerTarget=useRef<HTMLDivElement|null>(null),sampleNumber=useRef<HTMLInputElement|null>(null);
  const [visible,setVisible]=useState<{api:Api|null;sourceKind:'original'|'calculation';state:CycleCropWindowState}|null>(null);
  const [window]=useState(()=>createCycleCropWindow(state=>setVisible({...owner.current,state}),{sample_limit:7,event_limit:2}));
  const state=visible?.api===api && visible.sourceKind===sourceKind?visible.state:null,summary=state?.summary,range=state?.range;
  const samples=state?.sample_page?.page.kind==='samples'?state.sample_page.page.records:NO_SAMPLES;
  const events=state?.event_page?.page.kind==='events'?state.event_page.page.records:null;
  const sample=state?.selected?.sample,index=state?.selected && range?state.selected.index-range.offset:0;
  const scales=useMemo(()=>startupCohortScales(samples),[samples]);
  const busy=state?.phase==='loading',error=localError??state?.error;
  const rangeLabel=range?`현재 읽은 범위 ${range.count?`${range.offset+1}–${range.offset+range.count}`:'0'} / ${range.total} · ${range.first_utc??'시점 없음'} → ${range.last_utc??'시점 없음'} UTC`:'';
  function clear(){setPlaying(false);setLocalError(null);void window.cancel();}
  function read(client:Api,selection:CycleCropLookup){
    setPlaying(false);setLocalError(null);owner.current={api:client,sourceKind};
    if(!(sourceKind==='calculation'?validCalculationCycleCropLookup(selection):validCycleCropLookup(selection))){
      void window.cancel();setLocalError(new ApiError('invalid_request'));return;}
    if(sourceKind==='calculation')void window.openCalculation(client,selection);else void window.open(client,selection);
  }
  useEffect(()=>{owner.current={api,sourceKind};clear();setLookup(initial??EMPTY);
    if(api && initial && autoLoadInitialSelection)read(api,initial);
    return()=>{void window.cancel();};
  },[api,initial,autoLoadInitialSelection,sourceKind,window]);
  useEffect(()=>()=>{void window.dispose();},[window]);
  useEffect(()=>{const query=matchMedia('(prefers-reduced-motion: reduce)');
    const change=()=>{setReduced(query.matches);if(query.matches)setPlaying(false);};change();
    query.addEventListener('change',change);return()=>query.removeEventListener('change',change);},[]);
  useEffect(()=>{const pause=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',pause);
    return()=>document.removeEventListener('visibilitychange',pause);},[]);
  useEffect(()=>{if(!playing || reduced || !sample || !state)return;
    if(index>=samples.length-1){setPlaying(false);return;}
    const timer=setTimeout(()=>{if(window.snapshot()===state)window.select(index+1);},1000);
    return()=>clearTimeout(timer);
  },[playing,reduced,sample,state,index,samples,window]);
  function select(i:number){setPlaying(false);window.select(i);}
  function move(direction:'previous'|'next'){if(!range || state?.phase!=='ready')return;setPlaying(false);void window[direction](range.kind);}
  function submit(e:FormEvent){e.preventDefault();if(busy)return;
    if(!api){clear();setLocalError(new ApiError('auth_required'));return;}read(api,{...lookup});}
  return <div className="crop-replay coupled-replay startup-replay cycle-replay" aria-busy={busy} data-window-phase={state?.phase??'idle'}
    data-source-kind={sourceKind} data-retained-samples={samples.length} data-retained-events={events?.length??0}>
    <div className="crop-scope"><img src={researchLeaf} alt=""/><div><strong>합성 계산 · 품종 미검증</strong>
      <p>미게시 연구 결과 · <span>관문 미평가</span>. 실제 품종의 생과 생산량·예측·추천은 보류입니다.</p></div></div>
    <details className="panel startup-assumptions" aria-label="명시 진입 연구의 적용 범위"><summary>명시적 진입 · 초기 전환 미검증 · 합성 오차 약 8.52%</summary>
      <p>진입 개수와 질량은 명시적 입력입니다. 자동 착과·검증된 빈 과실 sink 모델이 아닙니다.</p>
      <p>초기 전환의 수렴은 미평가입니다. 작은 과실 구획 합성 시험의 약 8.52% 오차는 실제 품종 정확도를 보증하지 않습니다.</p></details>
    {summary?.summary.hold && <Hold hold={summary.summary.hold}/>}
    <details className="panel crop-lookup" open={!summary}><summary>저장 연구 결과 조회</summary>
      <p>긴 계산의 결과 ID와 등록 농장 판본을 입력하세요. 서버가 매 조회의 현재 권리와 저장 기록을 확인합니다.</p>
      <form onSubmit={submit}><div className="crop-lookup-fields">{(Object.keys(LABELS) as (keyof CycleCropLookup)[]).map(key=><label key={key}>{LABELS[key]}
        <input name={key} value={lookup[key]} maxLength={key==='result_id'?(sourceKind==='calculation'?94:85):key==='registration_sha256'?64:200} required autoComplete="off" spellCheck={false}
          onChange={e=>{clear();setLookup(old=>({...old,[key]:e.target.value}));}}/></label>)}</div>
        <button className="button primary" disabled={busy}>{busy?'연구 기록 확인 중…':'저장 연구 조회'}</button></form></details>
    {error && <p className="notice error" role="alert">{MESSAGES[error.code]??'현재 연구 기록을 확인할 수 없습니다.'}</p>}
    {busy && <section className="panel coupled-progress" role="status"><p>현재 범위를 조회합니다…</p>
      <button className="button secondary" onClick={()=>{clear();setLocalError(new ApiError('request_canceled'));}}>연구 조회 취소</button></section>}
    {!summary && !busy && !error && <section className="panel crop-empty"><h2>저장된 긴 계산을 선택해 주세요</h2>
      <p>현재 읽은 시점의 표·그래프·3D를 함께 확인합니다. 조회 ID는 저장 결과에서 가져옵니다.</p></section>}
    {summary && range && <>
      <section className="panel cycle-range" aria-label="현재 저장 범위" data-result-id={summary.result_id} data-kind={range.kind}
        data-offset={range.offset} data-count={range.count} data-total={range.total} data-next-offset={range.next_offset??''}>
        <div className="cycle-range-header"><h2>현재 저장 범위 · {range.kind==='samples'?'시점':'관리 사건'}</h2>
          <strong>{summary.reference.status==='completed'?'계산 완료':'계산 보류'} · {range.partial?'부분 범위':'전체 저장 범위'}</strong></div>
        <p>전체 저장 {summary.reference.sample_count}시점 / {summary.reference.event_count}사건 · 완료 걸음 {summary.reference.steps}/{summary.reference.planned_steps}</p>
        <p className="cycle-range-utc">{rangeLabel}</p><p className="crop-caption cycle-range-note">전체 저장 수와 현재 읽은 범위는 다릅니다.
          축은 현재 시점 범위에서 고정하며 범위를 바꾸면 달라질 수 있습니다. 이미 읽은 화면의 권리를 계속 확인하는 기능은 아닙니다.</p>
        <div className="cycle-range-controls"><button className="button secondary" disabled={!state?.can_previous} onClick={()=>move('previous')}>이전 저장 범위</button>
          <button className="button secondary" disabled={!state?.can_next} onClick={()=>move('next')}>다음 저장 범위</button>
          <button className="button secondary" disabled={range.kind==='samples'} onClick={()=>{setPlaying(false);void window.showSamples();}}>저장 시점 보기</button>
          <button className="button secondary" disabled={range.kind==='events'} onClick={()=>{setPlaying(false);void window.showEvents();}}>관리 사건 보기</button>
          <button className="button secondary" onClick={()=>{if(api)read(api,{...lookup});}}>현재 권리 다시 조회</button>
          {sourceKind==='calculation'&&<a className="button secondary" href="#crop-harvest">저장 수확 배정 보기</a>}</div>
        {summary.reference.sample_count>0 && <form className="cycle-range-controls" onSubmit={event=>{
          event.preventDefault();if(!sampleNumber.current)return;
          setPlaying(false);void window.seekSample(sampleNumber.current.valueAsNumber-1);
        }}><label>원 저장 시점 번호<input ref={sampleNumber} type="number" min={1} max={summary.reference.sample_count}
          step={1} required defaultValue={1} disabled={busy}/></label>
          <button className="button secondary" disabled={busy}>저장 시점으로 이동</button>
          <button type="button" className="button secondary" disabled={busy} onClick={()=>{
            setPlaying(false);void window.seekSample(summary.reference.sample_count-1);
          }}>마지막 저장 시점</button></form>}
        <p className="crop-caption">번호는 원본 저장 순서입니다. 이동한 시점부터 작은 범위만 읽으며 저장 시점 사이의 값을 보간하지 않습니다.</p>
      </section>
      {sample && <div className="coupled-viewer" ref={viewerTarget} tabIndex={-1} aria-label="선택된 저장 생장 시점"
        data-result-id={summary.result_id} data-selected-at={sample.at} data-selected-index={state!.selected!.index}
        data-farm={JSON.stringify(summary.farm)} data-reference={JSON.stringify(summary.reference)}>
        <div className="coupled-top-grid"><section className="panel"><h2>LAI·과실 구획 수치 모식도</h2>
          <Suspense fallback={<p role="status">3D 준비 중… 같은 값은 표에서 확인하세요.</p>}><Scene sample={sample} scales={scales} rangeLabel={rangeLabel}/></Suspense></section>
          <section className="panel coupled-readout" data-selected-at={sample.at}><h2>같은 UTC의 계산값</h2><dl>
            {(Object.keys(STATE_LABELS) as (keyof typeof STATE_LABELS)[]).map(key=><div key={key}><dt>{STATE_LABELS[key]}</dt>
              <dd data-metric={key} data-raw-value={sample.state[key].value}><Quantity q={sample.state[key]}/></dd></div>)}
            {(['lai','fruit_carbohydrate_total'] as const).map(key=><div key={key}><dt>{SAMPLE_LABELS[key]}</dt>
              <dd data-metric={key} data-raw-value={sample[key].value}><Quantity q={sample[key]}/></dd></div>)}</dl>
            <p className="crop-caption">mg_CH2O는 탄수화물 환산 질량입니다. 생과 kg·실제 개수·숙기·수확량은 아직 검증되지 않았습니다.</p></section></div>
        <section className="panel crop-timeline"><h2>현재 범위의 저장 성장 시점</h2><p className="crop-selected-time" aria-live={playing?'off':'polite'}>
          <strong>{sample.at}</strong><span>원 시점 {state!.selected!.index+1} / {summary.reference.sample_count} · UTC</span></p>
          <label>저장 성장 시점 선택<input type="range" min={0} max={samples.length-1} step={1} value={index}
            aria-valuetext={`${sample.at} UTC · 원 시점 ${state!.selected!.index+1}`} onChange={e=>select(Number(e.target.value))}/></label>
          <div className="crop-play-buttons"><button className="button secondary" aria-label="이전 저장 성장 시점" disabled={index===0} onClick={()=>select(index-1)}>이전</button>
            <button className="button primary" aria-label={playing?'성장 일시 정지':'성장 자동 재생'} disabled={reduced || index===samples.length-1} onClick={()=>setPlaying(value=>!value)}>{playing?'정지':'재생'}</button>
            <button className="button secondary" aria-label="다음 저장 성장 시점" disabled={index===samples.length-1} onClick={()=>select(index+1)}>다음</button></div>
          <p className="crop-caption">화면 1초마다 현재 범위의 다음 원 시점을 선택합니다. 끝에서 멈추며 새 범위를 자동 조회하거나 중간 상태를 만들지 않습니다.
            {reduced && ' 동작 줄이기 설정으로 자동 재생은 꺼져 있습니다.'}</p></section>
        <Suspense fallback={<p role="status">그래프 준비 중… 같은 값은 표에서 확인하세요.</p>}><Chart samples={samples} sample={sample} scales={scales} rangeLabel={rangeLabel}/></Suspense>
        <section className="panel coupled-cohorts" data-selected-at={sample.at}><h2>선택 시점의 50과실 구획 원값</h2><Cohorts state={sample.state} at={sample.at}/></section>
        <SampleTable samples={samples} index={index} select={select}/>
        <details className="panel crop-cumulative"><summary>선택 시점의 누적 유량·수지</summary><Accumulation sample={sample}/>
          <dl>{(['carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'] as const).map(key=><div key={key}>
            <dt>{SAMPLE_LABELS[key]}</dt><dd data-balance={key} data-raw-value={sample[key].value}><Quantity q={sample[key]}/></dd></div>)}</dl></details>
      </div>}
      {!sample && range.kind==='samples' && <section className="panel cycle-no-samples"><h2>선택 가능한 저장 시점이 없습니다</h2>
        <p>{summary.reference.status==='completed'?'계산은 완료되었으나 선택 출력은 0개입니다.':'확인된 과거 출력은 0개입니다.'} 시작·끝·실패 시각의 프레임을 만들지 않습니다.</p></section>}
      {events && <section className="panel cycle-events"><h2>현재 범위의 관리 사건</h2><p>명시적 입력의 제거입니다. 실제 적정 관리·숙기·생과 수확이 아닙니다.</p>
        {!events.length && <p>현재 범위에 저장된 관리 사건이 없습니다.</p>}{events.map((event,i)=><article key={event.at+':'+i} data-event-index={range.offset+i}>
          <h3>{event.at} · UTC</h3><dl>{(['leaf','stem_root'] as const).map(key=><div key={key}><dt>제거 {STATE_LABELS[key]}</dt>
            <dd data-event-metric={key} data-raw-value={event.removed[key].value}><Quantity q={event.removed[key]}/></dd></div>)}</dl>
          <details><summary>제거 C/N 원값</summary><Cohorts state={event.removed} at={event.at} diagnostic/></details>
          <details><summary>사건 직전 원값</summary><StateValues state={event.before}/><Cohorts state={event.before} at={event.at} diagnostic/></details>
          <details><summary>사건 직후 원값</summary><StateValues state={event.after}/><Cohorts state={event.after} at={event.at} diagnostic/></details>
        </article>)}</section>}
      <details className="panel crop-evidence cycle-evidence"><summary>고정 입력·모델과 저장 증거</summary>
        <p>연구 {summary.study_id} / {summary.revision} · 저장 {summary.recorded_at}</p><p>결과 ID <code>{summary.result_id}</code></p>
        <p>농장 {summary.farm.scenario_id} / {summary.farm.scenario_revision} · 작물 {summary.farm.crop_id}</p>
        <p>계산 구간 {summary.reference.start_utc} → {summary.reference.end_utc} UTC · 바닥 {summary.reference.floor_area.value}{summary.reference.floor_area.unit}</p>
        <p>모델 {summary.summary.manifest.rate_model_version} · solver {summary.summary.manifest.solver.method}. 일반 토마토 참조 프로필이며 등록 품종의 승인 계수가 아닙니다.</p>
        <details><summary>고정 참조·모델 판본</summary><pre>{JSON.stringify({farm:summary.farm,reference:summary.reference,manifest:summary.summary.manifest},null,2)}</pre></details>
      </details>
    </>}
    <HarvestReplay api={sourceKind==='calculation'?api:null}
      initialResultId={sourceKind==='calculation'?initialHarvestResultId:undefined}
      parent={summary?.schema_version==='crop-cycle-calculation-replay-v1'?summary:null}
      samplePage={state?.sample_page?.schema_version==='crop-cycle-calculation-replay-v1'&&state.sample_page.page.kind==='samples'?state.sample_page:null}
      selectedAt={sample?.at??null} selectSample={globalIndex=>{select(globalIndex-(state?.sample_page?.page.offset??0));
        viewerTarget.current?.focus({preventScroll:true});viewerTarget.current?.scrollIntoView({block:'start'});}}
      invalidate={error=>{clear();setLocalError(error);}}/>
  </div>;
}
