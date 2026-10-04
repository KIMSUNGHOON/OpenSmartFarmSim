import { lazy,Suspense,useEffect,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import { STORES,CUMULATIVE,STORE_LABELS,STORE_COLORS,CARBON_UNIT,LAI_UNIT,displayNumber,
  type CropLookup,type CropReplay,type CropHold,type CropSample } from './cropReplay';
import { maximumCarbon } from './cropGeometry';
import researchLeaf from './assets/crop-research-leaf.png';
import researchHold from './assets/crop-design/research-hold.png';
import './CropReplay.css';
const CropScene=lazy(()=>import('./CropScene'));
const CropChart=lazy(()=>import('./CropChart'));
type Api=ReturnType<typeof createApi>;
const EMPTY:CropLookup={result_id:'',scenario_id:'',scenario_revision:'',registration_sha256:'',crop_id:''};
const LABELS:Record<keyof CropLookup,string>={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',
  scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const MESSAGES:Record<string,string>={auth_required:'접근 토큰을 설정해 주세요.',access_denied:'이 계정에는 연구 결과 조회 권한이 없습니다.',
  not_available:'열람 가능한 저장 연구 결과가 없습니다. 결과 ID와 현재 연결을 확인하세요.',
  invalid_request:'현재 권리 또는 농장 연결을 확인할 수 없어 연구 재생을 보류했습니다.',
  response_rejected:'응답의 ID·단위·연구 범위를 확인할 수 없어 표시를 보류했습니다.',
  server_unavailable:'현재 서버에서 연구 결과를 조회할 수 없습니다.',network_unresolved:'조회 응답을 받지 못했습니다. 다시 조회해 주세요.'};

function HoldDiagnostic({hold}:{hold:CropHold}){
  return <section className="panel crop-hold" aria-label="작물 계산 보류 진단">
    <div className="crop-heading"><h2><img className="crop-hold-icon" src={researchHold} alt=""/>계산이 보류되었습니다</h2><span className="badge">정상 성장 재생 없음</span></div>
    <div className="crop-hold-reason"><strong>{hold.reason_code}</strong>
      <p>수치 검사 시각 {hold.attempted_at} · {hold.phase}. 이 시각은 solver 평가 시각이며 새로운 완료 sample이 아닙니다.</p></div>
    <div className="crop-diagnostic-grid"><div><h3>실패 진단</h3><dl>
      {([...STORES,'temperature_filtered_24h','temperature_sum'] as const).map(key=>{
        const q=hold.failed_state[key];return <div key={key}><dt>{key==='temperature_filtered_24h'?'평활 온도':
          key==='temperature_sum'?'온도 합':STORE_LABELS[key]}</dt><dd>{q.value===null?'수치 없음':displayNumber(q.value)}<small>{q.unit}</small></dd></div>;})}
    </dl></div><div><h3>마지막 확인 상태</h3>{hold.last_confirmed?<>
      <p>{hold.last_confirmed.at} · UTC</p><dl>{STORES.map(key=><div key={key}><dt>{STORE_LABELS[key]}</dt>
        <dd>{displayNumber(hold.last_confirmed!.state[key].value)}<small>{CARBON_UNIT}</small></dd></div>)}</dl>
      <p>LAI {displayNumber(hold.last_confirmed.lai.value)} {LAI_UNIT}</p></>:<p>마지막 확인 sample이 없습니다.</p>}</div></div>
    <p className="crop-caption">진단값은 실패 원인 확인용입니다. 전체 작기·생과 생산량·현장 예측이 아닙니다.</p>
  </section>;
}

function SavedTable({samples,index,onSelect}:{samples:readonly CropSample[];index:number;onSelect:(index:number)=>void}){
  const first=Math.floor(index/50)*50;
  return <section className="panel crop-data" id="viewport-1-winner-data"><div className="crop-heading">
    <h2>저장된 시계열 데이터</h2><span>{first+1}–{Math.min(first+50,samples.length)} / {samples.length} 시점</span></div>
    <div className="crop-table-scroll" tabIndex={0} role="region" aria-label="저장 성장 수치 표">
      <table className="crop-table"><caption>같은 저장 계산의 UTC·기관 탄소량·잎 면적과 수지. 각 시간 버튼으로 해당 저장 시점을 선택합니다.</caption>
        <thead><tr><th scope="col">저장 시각 (UTC)</th>{STORES.map(key=><th key={key} scope="col">{STORE_LABELS[key]}<small>{CARBON_UNIT}</small></th>)}
          <th scope="col">LAI<small>{LAI_UNIT}</small></th><th scope="col">탄소 수지 잔차<small>{CARBON_UNIT}</small></th>
          <th scope="col">잔차 허용 한도<small>{CARBON_UNIT}</small></th><th scope="col">평활 온도<small>degC</small></th><th scope="col">온도 합<small>degC_day</small></th></tr></thead>
        <tbody>{samples.slice(first,first+50).map((row,offset)=><tr key={row.at} aria-selected={index===first+offset}>
          <th scope="row"><button className="crop-time-button" onClick={()=>onSelect(first+offset)}>{row.at}</button></th>
          {STORES.map(key=><td key={key} data-metric={key} data-raw-value={row.state[key].value}>{displayNumber(row.state[key].value)}</td>)}
          <td data-metric="lai" data-raw-value={row.lai.value}>{displayNumber(row.lai.value)}</td>
          <td>{displayNumber(row.carbon_residual.value)}</td><td>{displayNumber(row.carbon_residual_budget.value)}</td>
          <td>{displayNumber(row.state.temperature_filtered_24h.value)}</td><td>{displayNumber(row.state.temperature_sum.value)}</td>
        </tr>)}</tbody></table></div>
    {samples.length>50 && <div className="crop-page-controls"><button className="button secondary" disabled={first===0}
      onClick={()=>onSelect(first-50)}>이전 50시점</button><button className="button secondary" disabled={first+50>=samples.length}
      onClick={()=>onSelect(first+50)}>다음 50시점</button></div>}
  </section>;
}

function CropEvents({data}:{data:CropReplay}){
  const [page,setPage]=useState(0);
  return <details className="panel crop-events"><summary>입력된 탄소 제거 · {data.events.length}건</summary>
    <p className="crop-caption">수식 입력의 제거 사건입니다. 실제 적정 관리·숙기·생과 수확을 뜻하지 않습니다.</p>
    {data.events.slice(page*50,(page+1)*50).map((event,index)=><div className="crop-event" key={event.at+':'+index}>
      <strong>{event.at} · UTC</strong><p>{(['leaf','stem_root','fruit'] as const).map(key=>
        STORE_LABELS[key]+' '+displayNumber(event.removals[key].value)+' '+CARBON_UNIT).join(' / ')}</p></div>)}
    {data.events.length>50 && <div className="crop-page-controls"><button className="button secondary" disabled={page===0}
      onClick={()=>setPage(n=>n-1)}>이전 50사건</button><span>{page+1} / {Math.ceil(data.events.length/50)}</span>
      <button className="button secondary" disabled={(page+1)*50>=data.events.length} onClick={()=>setPage(n=>n+1)}>다음 50사건</button></div>}
  </details>;
}

export default function CropReplayView({api,initialSelection,autoLoadInitialSelection=false}:{api:Api|null;
  initialSelection?:CropLookup;autoLoadInitialSelection?:boolean}){
  const [lookup,setLookup]=useState<CropLookup>(initialSelection??EMPTY),[loaded,setLoaded]=useState<{api:Api;data:CropReplay}|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState<ApiError|null>(null),[index,setIndex]=useState(0);
  const [playing,setPlaying]=useState(false),[reduced,setReduced]=useState(false),epoch=useRef(0);
  const data=loaded?.api===api?loaded.data:null,sample=data?.status==='completed'?data.samples[index]:undefined;
  const maximum=data?maximumCarbon(data.samples):0;
  async function read(client:Api,selection:CropLookup){
    const current=++epoch.current;setLoaded(null);setBusy(true);setError(null);setPlaying(false);setIndex(0);
    try{const value=await client.cropReplay(selection);if(current===epoch.current)setLoaded({api:client,data:value});}
    catch(cause){if(current===epoch.current)setError(cause instanceof ApiError?cause:new ApiError('network_unresolved'));}
    finally{if(current===epoch.current)setBusy(false);}
  }
  useEffect(()=>{
    epoch.current++;setLoaded(null);setError(null);setBusy(false);setPlaying(false);setIndex(0);setLookup(initialSelection??EMPTY);
    if(api && initialSelection && autoLoadInitialSelection)void read(api,initialSelection);
    return()=>{epoch.current++;};
  },[api,initialSelection,autoLoadInitialSelection]);
  useEffect(()=>{const query=matchMedia('(prefers-reduced-motion: reduce)');
    const change=()=>{setReduced(query.matches);if(query.matches)setPlaying(false);};change();
    query.addEventListener('change',change);return()=>query.removeEventListener('change',change);},[]);
  useEffect(()=>{const pause=()=>{if(document.hidden)setPlaying(false);};
    document.addEventListener('visibilitychange',pause);return()=>document.removeEventListener('visibilitychange',pause);},[]);
  useEffect(()=>{
    if(!playing || reduced || !data || data.status!=='completed')return;
    if(index>=data.samples.length-1){setPlaying(false);return;}
    const timer=setInterval(()=>setIndex(value=>Math.min(value+1,data.samples.length-1)),1000);
    return()=>clearInterval(timer);
  },[playing,reduced,data,index]);
  function select(value:number){setPlaying(false);setIndex(value);}
  function edit(key:keyof CropLookup,value:string){
    epoch.current++;setLookup(previous=>({...previous,[key]:value}));setLoaded(null);setBusy(false);setError(null);setPlaying(false);setIndex(0);
  }
  function submit(event:FormEvent){event.preventDefault();if(busy)return;
    if(!api){setError(new ApiError('auth_required'));return;}void read(api,{...lookup});}
  return <div className="crop-replay" aria-busy={busy}>
    <div className="crop-scope" id="viewport-1-winner-notice"><img src={researchLeaf} alt=""/>
      <div><strong>합성 계산 · 품종 미검증</strong><p>미게시 연구 결과 · <span>관문 미평가</span>. 실제 품종의 전체 작기·생과 생산량·예측·추천은 보류입니다.</p></div></div>
    {data?.status==='hold' && data.hold && <HoldDiagnostic hold={data.hold}/>}
    <details className="panel crop-lookup" id="viewport-1-winner-results" open={!data || data.status==='hold'}>
      <summary>저장 연구 결과 조회</summary><p>연구 결과와 등록 농장 판본의 식별자를 입력하세요. 서버가 현재 권리와 저장 기록을 확인합니다.</p>
      <form onSubmit={submit}><div className="crop-lookup-fields">{(Object.keys(LABELS) as (keyof CropLookup)[]).map(key=><label key={key}>
        {LABELS[key]}<input name={key} value={lookup[key]} maxLength={key==='result_id'?79:key==='registration_sha256'?64:200}
          autoComplete="off" spellCheck={false} required onChange={event=>edit(key,event.target.value)}/></label>)}</div>
        <button className="button primary" disabled={busy}>{busy?'연구 기록 확인 중…':'저장 연구 조회'}</button></form>
    </details>
    {error && <p className="notice error" role="alert">{MESSAGES[error.code]??'현재 연구 기록을 확인할 수 없습니다.'}</p>}
    {!data && !busy && !error && <section className="panel crop-empty"><h2>저장된 계산을 선택해 주세요</h2>
      <p>잎 면적과 기관 탄소량을 같은 UTC 시점의 3D 모식도·그래프·표에서 확인합니다.</p>
      <p className="crop-caption">등록된 결과가 없다면 운영자 조회 ID가 필요합니다. 로컬 합성 데모는 실제 저장 내역과 별도입니다.</p></section>}
    {busy && <p role="status">현재 권리 아래 저장된 연구 결과를 조회합니다…</p>}
    {data && sample && <div className="crop-viewer" data-result-id={data.result_id} data-selected-at={sample.at}>
      <div className="crop-period"><strong>{data.study_id} / {data.revision}</strong>
        <span>{data.start_utc} → {data.end_utc} · {data.samples.length} 저장 시점</span></div>
      <div className="crop-top-grid">
        <section className="panel crop-scene-panel" id="viewport-1-winner-canopy"><h2>잎 면적 기반 성장 모식도</h2>
          <Suspense fallback={<p role="status">3D를 준비합니다. 같은 수치는 옆 요약과 아래 표에서 확인하세요.</p>}>
            <CropScene sample={sample} maximum={maximum}/></Suspense></section>
        <section className="panel crop-readout" id="viewport-1-winner-carbon" data-selected-at={sample.at} aria-label="선택 성장 시점 계산값">
          <h2>기관별 탄소량</h2><dl>{STORES.map(key=><div className="crop-carbon-card" key={key}>
            <dt><span className="crop-dot" style={{background:STORE_COLORS[key]}}/>{STORE_LABELS[key]}</dt>
            <dd data-metric={key} data-raw-value={sample.state[key].value}>{displayNumber(sample.state[key].value)}<small>{CARBON_UNIT}</small></dd></div>)}</dl>
          <div className="crop-lai"><strong>잎 면적 지수 (LAI)</strong><span data-metric="lai" data-raw-value={sample.lai.value}>
            {displayNumber(sample.lai.value)}<small>{LAI_UNIT}</small></span></div>
          <p className="crop-caption">mg_CH2O는 탄수화물 환산 질량입니다. 생과 중량으로 환산하는 근거는 아직 검증되지 않았습니다.</p></section>
        <section className="panel crop-timeline" id="viewport-1-winner-timeline"><h2>저장 성장 시점</h2>
          <p className="crop-selected-time" aria-live={playing?'off':'polite'}><strong>{sample.at}</strong><span>{index+1} / {data.samples.length} · UTC</span></p>
          <label>저장 성장 시점 선택<input type="range" min={0} max={data.samples.length-1} step={1} value={index}
            aria-valuetext={sample.at+' UTC · '+(index+1)+'번째 저장 시점'} onChange={e=>select(Number(e.target.value))}/></label>
          <div className="crop-play-buttons"><button className="button secondary" aria-label="이전 저장 성장 시점" disabled={index===0} onClick={()=>select(index-1)}>이전</button>
            <button className="button primary" aria-label={playing?'성장 일시 정지':'성장 자동 재생'} disabled={reduced || index===data.samples.length-1}
              onClick={()=>setPlaying(value=>!value)}>{playing?'정지':'재생'}</button>
            <button className="button secondary" aria-label="다음 저장 성장 시점" disabled={index===data.samples.length-1} onClick={()=>select(index+1)}>다음</button></div>
          {data.samples.length<=12 && <ol className="crop-sample-list">{data.samples.map((row,i)=><li key={row.at}>
            <button aria-current={index===i?'step':undefined} onClick={()=>select(i)}><span>{i+1}</span>{row.at.slice(11,19)} UTC</button></li>)}</ol>}
          <p className="crop-caption">재생은 화면 1초마다 다음 저장 시점으로 이동합니다. 중간 상태를 만들지 않습니다.
            {reduced && ' 동작 줄이기 설정으로 자동 재생은 꺼져 있습니다.'}</p></section>
      </div>
      <Suspense fallback={<p role="status">그래프 준비 중… 같은 계산값은 표에서 확인하세요.</p>}><CropChart samples={data.samples} sample={sample}/></Suspense>
      <SavedTable samples={data.samples} index={index} onSelect={select}/>
      <details className="panel crop-cumulative"><summary>선택 시점의 누적 탄소 유량·수지</summary>
        <p>{sample.at} · UTC</p><dl>{CUMULATIVE.map(key=><div key={key}><dt>{key}</dt><dd>{displayNumber(sample.cumulative[key].value)}<small>{CARBON_UNIT}</small></dd></div>)}</dl>
        <p>수지 잔차 {displayNumber(sample.carbon_residual.value)} / 허용 한도 {displayNumber(sample.carbon_residual_budget.value)} {CARBON_UNIT}</p></details>
      <CropEvents key={data.result_id} data={data}/>
    </div>}
    {data && <details className="panel crop-evidence"><summary>고정 입력·모델과 저장 증거</summary>
      <p>연구 {data.study_id} / {data.revision} · 저장 {data.recorded_at}</p><p>결과 ID <code>{data.result_id}</code></p>
      <p>농장 {data.farm.scenario_id} / {data.farm.scenario_revision} · 작물 {data.farm.crop_id} · 배치 {data.batch_id} · 구역 {data.zone_id}</p>
      <p>모델 {data.manifest.rate_model_version} · 적분 {data.manifest.integrator_version} · 완료 걸음 {data.steps}/{data.planned_steps}</p>
      <p>참조 프로필 {data.manifest.profile_id} · {data.manifest.domain_policy}</p>
      <p>이 프로그램의 수렴 검증은 미평가입니다. 일반 토마토 참조 프로필이며 해당 등록 품종의 승인 계수가 아닙니다.</p>
      <dl>{Object.entries({registration_sha256:data.farm.registration_sha256,farm_sha256:data.farm_sha256,
        source_binding_sha256:data.source_binding_sha256,...Object.fromEntries(Object.entries(data.manifest).filter(([key])=>key.endsWith('sha256') && key!=='code_sha256')),
        integrator_code_sha256:data.manifest.code_sha256.integrator,rates_code_sha256:data.manifest.code_sha256.rates})
        .map(([key,value])=><div key={key}><dt>{key}</dt><dd><code>{String(value)}</code></dd></div>)}</dl>
    </details>}
  </div>;
}
