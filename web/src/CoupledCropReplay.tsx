import { lazy,Suspense,useEffect,useMemo,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import { coupledCohortScales } from './coupledCropGeometry';
import { COUPLED_CUMULATIVE,type CoupledCropLookup,type CoupledCropReplay,type CoupledCropSample,
  type CoupledCropEvent,type CoupledCropHold } from './coupledCropReplay';
import researchLeaf from './assets/crop-coupled-design/cutout-39-e57cccea5fd1.png';
import './CoupledCropReplay.css';
const Scene=lazy(()=>import('./CoupledCropScene'));
const Chart=lazy(()=>import('./CoupledCropChart'));
type Api=ReturnType<typeof createApi>;
const EMPTY:CoupledCropLookup={result_id:'',scenario_id:'',scenario_revision:'',registration_sha256:'',crop_id:''};
const LABELS:Record<keyof CoupledCropLookup,string>={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',
  scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const STATE_LABELS={buffer:'버퍼 탄소',leaf:'잎 탄소',stem_root:'줄기·뿌리 탄소',
  temperature_filtered_24h:'24시간 평활 온도',temperature_sum:'온도 합'};
const MESSAGES:Record<string,string>={auth_required:'접근 토큰을 설정해 주세요.',access_denied:'이 계정에는 연구 결과 조회 권한이 없습니다.',
  not_available:'열람 가능한 저장 연구 결과가 없습니다. 결과 ID와 현재 연결을 확인하세요.',
  invalid_request:'현재 권리 또는 농장 연결을 확인할 수 없어 연구 재생을 보류했습니다.',
  response_rejected:'응답의 ID·단위·페이지·연구 범위를 확인할 수 없어 표시를 보류했습니다.',
  request_canceled:'연구 결과 조회를 취소했습니다.',server_unavailable:'현재 서버에서 연구 결과를 조회할 수 없습니다.',
  network_unresolved:'조회 응답을 받지 못했습니다. 다시 조회해 주세요.'};
function Quantity({value}:{value:{value:number;unit:string}}){return <>{String(value.value)}<small>{value.unit}</small></>;}
function Cohorts({sample,diagnostic=false}:{sample:CoupledCropSample;diagnostic?:boolean}){
  return <div className="crop-table-scroll" role="region" tabIndex={0} aria-label={diagnostic?'마지막 확인 구획 진단':'저장 과실 구획 수치'}>
    <table className={diagnostic?'coupled-diagnostic-table':'coupled-cohort-table'}><caption>구획 1–50의 서버 원값 · {sample.at} UTC. N은 개수 상당량이며 실제 열매 개수가 아닙니다.</caption>
      <thead><tr><th scope="col">구획</th><th scope="col">과실 탄소 C<small>{sample.state.fruit_carbohydrate[0]!.unit}</small></th>
        <th scope="col">개수 상당량 N<small>{sample.state.fruit_number[0]!.unit}</small></th></tr></thead>
      <tbody>{sample.state.fruit_carbohydrate.map((q,i)=><tr key={i} data-cohort={i+1}>
        <th scope="row">{i+1}</th><td data-metric="carbon" data-raw-value={q.value}>{String(q.value)}</td>
        <td data-metric="number" data-raw-value={sample.state.fruit_number[i]!.value}>{String(sample.state.fruit_number[i]!.value)}</td></tr>)}</tbody></table>
  </div>;
}
function Hold({hold}:{hold:CoupledCropHold}){
  return <section className="panel crop-hold coupled-hold" aria-label="연결 작물 계산 보류 진단"><h2>계산이 보류되었습니다</h2>
    <strong>{hold.reason_code}</strong><p>수치 검사 시각 {hold.at} · {hold.phase}. solver 평가 시각이며 선택 가능한 완료 sample이 아닙니다.</p>
    {hold.last_confirmed?<details><summary>마지막 확인 진단 · {hold.last_confirmed.at}</summary>
      <p>확인 단계 {hold.last_confirmed.phase}. 별도 진단이며 시간축에 새 프레임으로 추가하지 않습니다.</p>
      <dl>{Object.entries(STATE_LABELS).map(([key,label])=><div key={key}><dt>{label}</dt>
        <dd><Quantity value={hold.last_confirmed!.state[key as keyof typeof STATE_LABELS]}/></dd></div>)}
        <div><dt>잎 면적 지수</dt><dd><Quantity value={hold.last_confirmed.lai}/></dd></div></dl>
      <Cohorts sample={hold.last_confirmed} diagnostic/></details>:<p>확인된 과거 sample과 마지막 확인 상태가 없습니다. 수치 장면을 표시하지 않습니다.</p>}
    <p className="crop-caption">확인된 과거 저장 시점만 탐색합니다. 실패한 trial·보류 이후 상태·미래 예측은 표시하지 않습니다.</p>
  </section>;
}
function Samples({data,index,select}:{data:CoupledCropReplay;index:number;select:(i:number)=>void}){
  const first=Math.floor(index/50)*50;
  return <section className="panel"><div className="crop-heading"><h2>저장 시계열</h2><span>{first+1}–{Math.min(first+50,data.samples.length)} / {data.samples.length}</span></div>
    <div className="crop-table-scroll" tabIndex={0} role="region" aria-label="연결 작물 저장 시계열 수치"><table className="crop-table coupled-time-table">
      <caption>같은 결과의 UTC·기관 상태·LAI·총 과실 탄소·수지. 시간 버튼은 저장된 정수 인덱스만 선택합니다.</caption>
      <thead><tr><th scope="col">저장 시각 (UTC)</th>{Object.values(STATE_LABELS).map(label=><th key={label} scope="col">{label}</th>)}
        {['LAI','총 과실 탄소','탄소 수지 잔차','탄소 허용 한도','개수 상당량 수지 잔차','개수 상당량 허용 한도'].map(label=><th key={label} scope="col">{label}</th>)}</tr></thead>
      <tbody>{data.samples.slice(first,first+50).map((row,offset)=><tr key={row.at} aria-selected={index===first+offset}>
        <th scope="row"><button className="crop-time-button" onClick={()=>select(first+offset)}>{row.at}</button></th>
        {(Object.keys(STATE_LABELS) as (keyof typeof STATE_LABELS)[]).map(key=><td key={key} data-metric={key} data-raw-value={row.state[key].value}><Quantity value={row.state[key]}/></td>)}
        {(['lai','fruit_carbohydrate_total','carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'] as const)
          .map(key=><td key={key} data-metric={key} data-raw-value={row[key].value}><Quantity value={row[key]}/></td>)}
      </tr>)}</tbody></table></div>
    {data.samples.length>50 && <div className="crop-page-controls"><button className="button secondary" disabled={first===0} onClick={()=>select(first-50)}>이전 50시점</button>
      <button className="button secondary" disabled={first+50>=data.samples.length} onClick={()=>select(first+50)}>다음 50시점</button></div>}
  </section>;
}

export default function CoupledCropReplayView({api,initialSelection,autoLoadInitialSelection=false}:{api:Api|null;
  initialSelection?:CoupledCropLookup;autoLoadInitialSelection?:boolean}){
  const initial=initialSelection?.result_id.startsWith('crop-result-v2:')?initialSelection:undefined;
  const [lookup,setLookup]=useState(initial??EMPTY),[loaded,setLoaded]=useState<{api:Api;data:CoupledCropReplay}|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState<ApiError|null>(null),[progress,setProgress]=useState<{pages:number;samples:number;total:number}|null>(null);
  const [index,setIndex]=useState(0),[playing,setPlaying]=useState(false),[reduced,setReduced]=useState(false);
  const [events,setEvents]=useState<readonly CoupledCropEvent[]>([]),[eventOffset,setEventOffset]=useState(0),[eventBusy,setEventBusy]=useState(false);
  const epoch=useRef(0),abort=useRef<AbortController|null>(null),data=loaded?.api===api?loaded.data:null;
  const sample=data?.samples[index],scales=useMemo(()=>coupledCohortScales(data?.samples??[]),[data]);
  function clear(){epoch.current++;abort.current?.abort();abort.current=null;setLoaded(null);setBusy(false);setProgress(null);
    setPlaying(false);setIndex(0);setEvents([]);setEventOffset(0);setEventBusy(false);setError(null);}
  async function read(client:Api,selection:CoupledCropLookup){
    clear();const current=epoch.current,controller=new AbortController();abort.current=controller;setBusy(true);
    try{const value=await client.coupledCropReplay(selection,{signal:controller.signal,
      onProgress:p=>{if(current===epoch.current)setProgress(p);}});
      if(current===epoch.current){setLoaded({api:client,data:value});setEvents(value.events);}}
    catch(cause){if(current===epoch.current)setError(cause instanceof ApiError?cause:new ApiError('network_unresolved'));}
    finally{if(current===epoch.current){setBusy(false);abort.current=null;}}
  }
  useEffect(()=>{clear();setLookup(initial??EMPTY);
    if(api && initial && autoLoadInitialSelection)void read(api,initial);
    return()=>{epoch.current++;abort.current?.abort();};
  },[api,initial,autoLoadInitialSelection]);
  useEffect(()=>{const query=matchMedia('(prefers-reduced-motion: reduce)');const change=()=>{setReduced(query.matches);if(query.matches)setPlaying(false);};
    change();query.addEventListener('change',change);return()=>query.removeEventListener('change',change);},[]);
  useEffect(()=>{const pause=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',pause);
    return()=>document.removeEventListener('visibilitychange',pause);},[]);
  useEffect(()=>{if(!playing || reduced || !data)return;
    if(index>=data.samples.length-1){setPlaying(false);return;}
    const timer=setTimeout(()=>setIndex(i=>Math.min(i+1,data.samples.length-1)),1000);return()=>clearTimeout(timer);
  },[playing,reduced,data,index]);
  function select(i:number){setPlaying(false);setIndex(i);}
  function submit(e:FormEvent){e.preventDefault();if(busy || eventBusy)return;
    if(!api){clear();setError(new ApiError('auth_required'));return;}void read(api,{...lookup});}
  async function readEvents(offset:number){
    if(!api || !data || eventBusy)return;const client=api,current=epoch.current,controller=new AbortController();abort.current=controller;
    setEvents([]);setEventBusy(true);setPlaying(false);
    try{const page=await client.coupledCropEvents(data,offset,controller.signal);
      if(current===epoch.current){setEvents(page.events);setEventOffset(offset);}}
    catch(cause){if(current===epoch.current){clear();setError(cause instanceof ApiError?cause:new ApiError('network_unresolved'));}}
    finally{if(current===epoch.current){setEventBusy(false);abort.current=null;}}
  }
  return <div className="crop-replay coupled-replay" aria-busy={busy || eventBusy}>
    <div className="crop-scope"><img src={researchLeaf} alt=""/><div><strong>합성 계산 · 품종 미검증</strong>
      <p>미게시 연구 결과 · <span>관문 미평가</span>. 실제 품종의 전체 작기·생과 생산량·예측·추천은 보류입니다.</p></div></div>
    {data?.hold && <Hold hold={data.hold}/>}
    <details className="panel crop-lookup" open={!data}><summary>저장 연구 결과 조회</summary>
      <p>v2 기관·50과실 구획의 고정 결과 ID와 등록 농장 판본을 입력하세요. 현재 권리와 저장 기록을 확인합니다.</p>
      <form onSubmit={submit}><div className="crop-lookup-fields">{(Object.keys(LABELS) as (keyof CoupledCropLookup)[]).map(key=><label key={key}>{LABELS[key]}
        <input value={lookup[key]} name={key} maxLength={key==='result_id'?79:key==='registration_sha256'?64:200} required autoComplete="off" spellCheck={false}
          onChange={e=>{clear();setLookup(old=>({...old,[key]:e.target.value}));}}/></label>)}</div>
        <button className="button primary" disabled={busy || eventBusy}>{busy?'연구 기록 확인 중…':'저장 연구 조회'}</button></form></details>
    {error && <p className="notice error" role="alert">{MESSAGES[error.code]??'현재 연구 기록을 확인할 수 없습니다.'}</p>}
    {busy && <div className="panel coupled-progress" role="status"><p>전체 저장 시점 확인 중 · {progress?`${progress.pages}페이지 · ${progress.samples}/${progress.total}시점`:'첫 페이지 대기'}</p>
      <p>모든 시점을 확인한 뒤 같은 척도로 표시합니다. 각 페이지 조회 제한은 30초입니다.</p>
      <button className="button secondary" onClick={()=>{clear();setError(new ApiError('request_canceled'));}}>연구 조회 취소</button></div>}
    {!data && !busy && !error && <section className="panel crop-empty"><h2>기관·50과실 구획의 저장 계산을 선택해 주세요</h2>
      <p>서버가 저장한 시점만 3D·그래프·표에 연결합니다. 열람할 저장 기록이 없다면 운영자의 결과 ID가 필요합니다.</p></section>}
    {data && sample && <div className="coupled-viewer" data-result-id={data.result_id} data-selected-at={sample.at}>
      <div className="crop-period"><strong>{data.study_id} / {data.revision}</strong><span>{data.start_utc} → {data.end_utc} · {data.samples.length} 저장 시점</span></div>
      <p className="coupled-result-id">결과 ID <code>{data.result_id}</code></p>
      <section className="panel crop-timeline coupled-timeline"><div className="crop-heading"><h2>저장 시점 · UTC</h2><strong>{sample.at}</strong><span>{index+1}/{data.samples.length}</span></div>
        <label>연결 연구 저장 시점 선택<input type="range" min={0} max={data.samples.length-1} step={1} value={index}
          aria-valuetext={sample.at+' UTC · '+(index+1)+'번째 저장 시점'} onChange={e=>select(Number(e.target.value))}/></label>
        <div className="crop-play-buttons"><button className="button secondary" aria-label="이전 연결 연구 저장 시점" disabled={index===0} onClick={()=>select(index-1)}>이전</button>
          <button className="button primary" aria-label={playing?'연결 연구 일시 정지':'연결 연구 자동 재생'} disabled={reduced || index>=data.samples.length-1}
            onClick={()=>setPlaying(p=>!p)}>{playing?'정지':'재생'}</button><button className="button secondary" aria-label="다음 연결 연구 저장 시점" disabled={index>=data.samples.length-1}
              onClick={()=>select(index+1)}>다음</button></div><p className="crop-caption">화면 1초마다 다음 저장 시점을 선택하며 보간하지 않습니다.{reduced && ' 동작 줄이기 설정으로 자동 재생이 꺼져 있습니다.'}</p>
      </section>
      <div className="coupled-top-grid"><section className="panel"><h2>잎 면적·50과실 구획의 3D 수치 모식도</h2>
        <Suspense fallback={<p role="status">3D 준비 중… 같은 원값은 표에서 확인하세요.</p>}><Scene sample={sample} scales={scales}/></Suspense></section>
        <section className="panel coupled-readout" data-selected-at={sample.at}><h2>선택 시점의 기관·온도 상태</h2><dl>
          {(Object.entries(STATE_LABELS) as [keyof typeof STATE_LABELS,string][]).map(([key,label])=><div key={key} className="crop-carbon-card"><dt>{label}</dt>
            <dd data-metric={key} data-raw-value={sample.state[key].value}><Quantity value={sample.state[key]}/></dd></div>)}
          {(['lai','fruit_carbohydrate_total'] as const).map(key=><div className="crop-carbon-card" key={key}><dt>{key==='lai'?'잎 면적 지수':'총 과실 탄소'} </dt>
            <dd data-metric={key} data-raw-value={sample[key].value}><Quantity value={sample[key]}/></dd></div>)}</dl>
          <p className="crop-caption">mg_CH2O는 탄수화물 환산 질량입니다. 생과 kg·실제 개수로 환산하지 않습니다.</p></section></div>
      <Suspense fallback={<p role="status">그래프 준비 중… 같은 원값은 표에서 확인하세요.</p>}><Chart samples={data.samples} sample={sample} scales={scales}/></Suspense>
      <section className="panel coupled-cohorts" data-selected-at={sample.at}><h2>과실 구획 1–50 · 정확한 저장 값</h2><Cohorts sample={sample}/></section>
      <Samples data={data} index={index} select={select}/>
      <details className="panel crop-cumulative"><summary>선택 시점의 누적량·두 수지</summary><p>{sample.at} UTC</p><dl>
        {COUPLED_CUMULATIVE.map(key=><div key={key}><dt>{key}</dt><dd data-cumulative={key} data-raw-value={sample.cumulative[key].value}><Quantity value={sample.cumulative[key]}/></dd></div>)}
        {(['carbon_residual','carbon_residual_budget','number_residual','number_residual_budget'] as const).map(key=><div key={key}><dt>{key}</dt>
          <dd><Quantity value={sample[key]}/></dd></div>)}</dl><p className="crop-caption">terminal·관리 제거는 모델의 유출입니다. 실제 숙기·생과 수확·판매 또는 구매 자원이 아닙니다.</p></details>
    </div>}
    {data && <details className="panel coupled-events"><summary>입력된 기관·구획 제거 · {data.total_events}건</summary>
      <p className="crop-caption">실제 적정 관리·생과 수확을 뜻하지 않는 수식 입력입니다. 사건 페이지는 필요할 때 따로 조회합니다.</p>
      {eventBusy?<p role="status">사건 페이지 확인 중…</p>:events.map((event,i)=><details className="crop-event" key={event.at+':'+i}><summary>{event.at} UTC</summary>
        <p>잎 제거 <Quantity value={event.removed.leaf}/> · 줄기·뿌리 제거 <Quantity value={event.removed.stem_root}/></p>
        <details><summary>제거 전·후와 50구획 원값</summary><pre>{JSON.stringify(event,null,2)}</pre></details></details>)}
      {data.total_events>8 && <div className="crop-page-controls"><button className="button secondary" disabled={eventBusy || eventOffset===0} onClick={()=>void readEvents(eventOffset-8)}>이전 8사건</button>
        <span>{eventOffset+1}–{Math.min(eventOffset+8,data.total_events)} / {data.total_events}</span>
        <button className="button secondary" disabled={eventBusy || eventOffset+8>=data.total_events} onClick={()=>void readEvents(eventOffset+8)}>다음 8사건</button>
        {eventBusy && <button className="button secondary" onClick={()=>{clear();setError(new ApiError('request_canceled'));}}>사건 조회 취소</button>}</div>}
    </details>}
    {data && <details className="panel crop-evidence"><summary>고정 입력·모델과 저장 증거</summary>
      <p>결과 ID <code>{data.result_id}</code> · 저장 {data.recorded_at}</p><p>농장 {data.farm.scenario_id} / {data.farm.scenario_revision} · 작물 {data.farm.crop_id} · 배치 {data.batch_id} · 구역 {data.zone_id}</p>
      <p>{data.status} · 완료 걸음 {data.steps}/{data.planned_steps}. 일반 토마토 참조 프로필이며 해당 등록 품종의 승인 계수가 아닙니다. 이 프로그램의 수렴 검증은 미평가입니다.</p>
      <pre>{JSON.stringify({farm:data.farm,farm_sha256:data.farm_sha256,source_binding_sha256:data.source_binding_sha256,manifest:data.manifest},null,2)}</pre>
    </details>}
  </div>;
}
