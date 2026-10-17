import { lazy,Suspense,useEffect,useMemo,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import { validGreenhouseSolarLookup,type GreenhouseSolarLookup,type GreenhouseSolarSummaryResponse,
  type GreenhouseSolarPageResponse,type GreenhouseSolarPageQuery,type GreenhouseSolarState,type GreenhouseSolarBoundary,type SolarQuantity } from './greenhouseSolarReplay';
import { jointSceneSample,jointSceneScales } from './jointCropClimateGeometry';
import researchLeaf from './assets/crop-coupled-design/cutout-39-e57cccea5fd1.png';
import './CropReplay.css';
import './CoupledCropReplay.css';
import './CycleCropReplay.css';
const Scene=lazy(()=>import('./CoupledCropScene'));
const Chart=lazy(()=>import('./JointCropClimateChart'));
type Api=ReturnType<typeof createApi>;
type Loaded={api:Api;lookup:GreenhouseSolarLookup;summary:GreenhouseSolarSummaryResponse;page:GreenhouseSolarPageResponse};
const EMPTY:GreenhouseSolarLookup={result_id:'',scenario_id:'',scenario_revision:'',registration_sha256:'',crop_id:''};
const LABELS:Record<keyof GreenhouseSolarLookup,string>={result_id:'저장 연구 결과 ID',scenario_id:'농장 시나리오 ID',
  scenario_revision:'농장 판본',registration_sha256:'등록 SHA-256',crop_id:'작물 ID'};
const METRICS:Record<string,string>={leaf_area_index:'잎 면적 지수 (LAI)',canopy_temperature:'수관 온도',air_temperature:'공기 온도',
  air_vapor_mass:'공기 수증기 질량',buffer:'버퍼 탄소',leaf:'잎 탄소',stem_root:'줄기·뿌리 탄소',
  temperature_filtered_24h:'24시간 평활 온도',temperature_sum:'온도 합',
  indoor_vapor_density:'실내 수증기 밀도',outdoor_vapor_density:'실외 수증기 밀도',
  air_external_sensible_heat:'공기 현열 경계량',air_external_vapor:'공기 수증기 경계량',latent_energy:'환기 잠열 흐름',
  ventilation_sensible_heat:'환기 누적 현열',ventilation_vapor:'환기 누적 수증기',ventilation_latent_energy:'환기 누적 잠열',
  canopy_non_solar_heat:'수관 비일사 열 경계',canopy_absorbed_par:'수관 흡수 PAR',canopy_absorbed_nir:'수관 흡수 NIR',
  canopy_external_heat:'수관 외부 열 경계',par_above_canopy:'작물 입력 PAR',outdoor_PAR:'실외 PAR',
  above_canopy_PAR:'수관 위 PAR',outdoor_nir:'실외 NIR',available_virtual_nir:'가상 가용 NIR',
  floor_absorbed_nir:'바닥 흡수 NIR',upward_virtual_nir:'가상 상향 NIR',construction_unallocated_nir:'구조체 미배정 NIR'};
const MESSAGES:Record<string,string>={auth_required:'접근 토큰을 설정해 주세요.',access_denied:'현재 계정에 조회 권한이 없습니다.',
  not_available:'열람 가능한 저장 결과가 없습니다.',invalid_request:'현재 권리 또는 농장 연결을 확인할 수 없어 표시를 보류했습니다.',
  response_rejected:'응답의 ID·판본·단위·시간·값을 확인할 수 없어 표시를 보류했습니다.',request_canceled:'연구 결과 조회를 취소했습니다.',
  server_unavailable:'현재 서버에서 연구 결과를 조회할 수 없습니다.',network_unresolved:'조회 응답을 받지 못했습니다. 다시 조회해 주세요.'};
function Quantities({values,label}:{values:Readonly<Record<string,SolarQuantity>>;label:string}){
  return <dl aria-label={label}>{Object.entries(values).map(([key,q])=><div key={key}><dt>{METRICS[key]??key}</dt>
    <dd data-metric={key} data-raw-value={q.value}>{String(q.value)}<small>{q.unit}</small></dd></div>)}</dl>;
}
function Cohorts({state,at}:{state:GreenhouseSolarState['cohort_state'];at:string}){
  return <div className="crop-table-scroll" tabIndex={0} role="region" aria-label="저장 과실 구획 수치"><table className="coupled-cohort-table">
    <caption>구획1–50 · {at} UTC. C는 탄수화물 환산 질량, N은 개수 상당량입니다.</caption>
    <thead><tr><th scope="col">구획</th><th scope="col">C<small>{state.fruit_carbohydrate[0]!.unit}</small></th>
      <th scope="col">N<small>{state.fruit_number[0]!.unit}</small></th></tr></thead>
    <tbody>{state.fruit_carbohydrate.map((q,i)=><tr key={i}><th scope="row">{i+1}</th>
      <td data-metric="carbon" data-raw-value={q.value}>{String(q.value)}</td>
      <td data-metric="number" data-raw-value={state.fruit_number[i]!.value}>{String(state.fruit_number[i]!.value)}</td></tr>)}</tbody>
  </table></div>;
}
function SolarDiagnostic({state,at}:{state:GreenhouseSolarBoundary;at:string}){
  return <section className="panel coupled-readout solar-diagnostic" data-selected-at={at}
    data-solar-heat={JSON.stringify(state.solar_heat_composition)} data-solar-par={JSON.stringify(state.solar_par)}
    data-solar-nir={JSON.stringify(state.solar_nir)}><h2>같은 UTC의 PAR·NIR 경계값</h2>
    <Quantities values={state.solar_heat_composition} label="일사 열 경계 원값"/>
    <Quantities values={state.solar_par.crop_forcing} label="작물 입력 PAR 원값"/>
    <p className="crop-caption">현재 원 모델에 저장된 일사 경계의 연구 표현입니다. 단위와 원 수치를 유지하며 시설 실측·생산/구매 에너지 검증은 남아 있습니다.</p>
    <details><summary>PAR 분배·단위·입력 SHA-256</summary><pre>{JSON.stringify(state.solar_par,null,2)}</pre></details>
    <details><summary>NIR 분배·광학·수지·입력 SHA-256</summary><pre>{JSON.stringify(state.solar_nir,null,2)}</pre></details>
  </section>;
}
export default function GreenhouseSolarReplay({api,initialSelection,autoLoadInitialSelection=false}:{api:Api|null;
  initialSelection?:GreenhouseSolarLookup;autoLoadInitialSelection?:boolean}){
  const [lookup,setLookup]=useState<GreenhouseSolarLookup>(initialSelection??EMPTY),[loaded,setLoaded]=useState<Loaded|null>(null);
  const [busy,setBusy]=useState(false),[error,setError]=useState<ApiError|null>(null),[index,setIndex]=useState(0);
  const [playing,setPlaying]=useState(false),[reduced,setReduced]=useState(false);
  const epoch=useRef(0),abort=useRef<AbortController|null>(null),pending=useRef<Promise<void>|null>(null);
  const current=loaded?.api===api?loaded:null,summary=current?.summary,page=current?.page.page;
  const samples=page?.kind==='samples'?page.records:[],sample=samples[index];
  const scales=useMemo(()=>jointSceneScales(samples),[page]);
  function clear(){epoch.current++;abort.current?.abort();setLoaded(null);setBusy(false);setError(null);setPlaying(false);setIndex(0);}
  function read(client:Api,selection:GreenhouseSolarLookup,kind:GreenhouseSolarPageQuery['kind']='samples',offset=0,known?:GreenhouseSolarSummaryResponse){
    const previous=pending.current,id=++epoch.current;abort.current?.abort();const controller=new AbortController();abort.current=controller;
    setLoaded(null);setBusy(true);setError(null);setPlaying(false);setIndex(0);
    const active=()=>id===epoch.current&&!controller.signal.aborted;
    const task=(async()=>{
      try{
        await previous;if(!active())return;
        if(!validGreenhouseSolarLookup(selection))throw new ApiError('response_rejected');
        const value=known??await client.greenhouseSolarSummary(selection,controller.signal);if(!active())return;
        const data=await client.greenhouseSolarPage(selection,{kind,offset,limit:kind==='samples'?64:8},{summary:value,signal:controller.signal});
        if(active())setLoaded({api:client,lookup:selection,summary:value,page:data});
      }catch(cause){if(active())setError(cause instanceof ApiError?cause:new ApiError('network_unresolved'));}
      finally{if(active())setBusy(false);}
    })();pending.current=task;
  }
  useEffect(()=>{clear();setLookup(initialSelection??EMPTY);
    if(api&&initialSelection&&autoLoadInitialSelection)read(api,{...initialSelection});
    return()=>{epoch.current++;abort.current?.abort();};
  },[api,initialSelection,autoLoadInitialSelection]);
  useEffect(()=>{const media=matchMedia('(prefers-reduced-motion: reduce)');const change=()=>{setReduced(media.matches);if(media.matches)setPlaying(false);};
    change();media.addEventListener('change',change);return()=>media.removeEventListener('change',change);},[]);
  useEffect(()=>{const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
    return()=>document.removeEventListener('visibilitychange',hidden);},[]);
  useEffect(()=>{if(!playing||reduced||!sample)return;if(index>=samples.length-1){setPlaying(false);return;}
    const timer=setTimeout(()=>setIndex(i=>i+1),1000);return()=>clearTimeout(timer);
  },[playing,reduced,sample,index,samples.length]);
  function select(value:number){setPlaying(false);setIndex(value);}
  function move(kind:GreenhouseSolarPageQuery['kind'],offset:number){if(current)read(current.api,current.lookup,kind,offset,current.summary);}
  function submit(event:FormEvent){event.preventDefault();if(busy)return;
    if(!api){clear();setError(new ApiError('auth_required'));return;}read(api,{...lookup});}
  return <div className="crop-replay coupled-replay cycle-replay joint-replay solar-replay" aria-busy={busy}>
    <div className="crop-scope"><img src={researchLeaf} alt=""/><div><strong>작물·기후·일사·명시 환기 계산 · 합성 연구</strong>
      <p>관문 미평가 · 등록 품종 미검증. 완료 저장 결과 재생입니다. 계산 중 확정 결과는 계산 상태 화면에서 조회합니다.</p></div></div>
    <details className="panel crop-lookup" open={!summary}><summary>저장 연구 결과 조회</summary>
      <p>일사(PAR/NIR) 결과와 농장 판본의 식별자를 입력하세요. 서버가 현재 권리와 저장 기록을 확인합니다.</p>
      <form onSubmit={submit}><div className="crop-lookup-fields">{(Object.keys(LABELS) as (keyof GreenhouseSolarLookup)[]).map(key=><label key={key}>{LABELS[key]}
        <input name={key} value={lookup[key]} maxLength={key==='result_id'?120:key==='registration_sha256'?64:200} required autoComplete="off" spellCheck={false}
          onChange={e=>{clear();setLookup(old=>({...old,[key]:e.target.value}));}}/></label>)}</div>
        <button className="button primary" disabled={busy}>{busy?'연구 기록 확인 중…':'저장 연구 조회'}</button></form></details>
    {error&&<p className="notice error" role="alert">{MESSAGES[error.code]??'현재 연구 기록을 확인할 수 없습니다.'}</p>}
    {busy&&<section className="panel coupled-progress" role="status"><p>현재 저장 범위를 조회합니다…</p>
      <button className="button secondary" onClick={()=>{clear();setError(new ApiError('request_canceled'));}}>연구 조회 취소</button></section>}
    {!summary&&!busy&&!error&&<section className="panel crop-empty"><h2>저장된 일사·환기 계산을 선택해 주세요</h2>
      <p>같은 UTC의 작물·기후 원값을 표·그래프·수치3D에서 확인합니다.</p></section>}
    {summary&&page&&<>
      {summary.summary.hold&&<section className="panel crop-hold" aria-label="일사 계산 보류 진단"><h2>계산이 보류되었습니다</h2>
        <strong>{summary.summary.hold.reason_code}</strong><p>실패 경계 {summary.summary.hold.time.at} · {summary.summary.hold.phase} / 내부 단계 {summary.summary.hold.inner_failed_stage??'해당 없음'}.
          실패 시점의 새 프레임을 만들지 않습니다. 아래는 실패 이전에 저장된 확정 출력입니다.</p>
        <details><summary>마지막 확정 상태 · {summary.summary.last_confirmed.time.at}</summary><pre>{JSON.stringify(summary.summary.last_confirmed,null,2)}</pre></details></section>}
      <section className="panel cycle-range" data-kind={page.kind} data-offset={page.offset} data-count={page.records.length} data-total={page.total}>
        <div className="cycle-range-header"><h2>현재 저장 범위 · {page.kind==='samples'?'시점':'관리 사건'}</h2>
          <strong>{summary.summary.status==='completed'?'계산 완료':'계산 보류'} · {page.records.length===page.total?'전체 저장 범위':'부분 범위'}</strong></div>
        <p>전체 저장 {summary.reference.artifact.sample_count}시점 / {summary.reference.artifact.event_count}사건 · 완료 걸음
          {summary.reference.artifact.steps}/{summary.reference.artifact.planned_steps}</p>
        <p>현재 {page.records.length?page.offset+1:0}–{page.offset+page.records.length} / {page.total}. 표시 축은 현재 읽은 범위에서 고정합니다.</p>
        <div className="cycle-range-controls"><button className="button secondary" disabled={page.offset===0} onClick={()=>move(page.kind,Math.max(0,page.offset-page.limit))}>이전 저장 범위</button>
          <button className="button secondary" disabled={page.next_offset===null} onClick={()=>move(page.kind,page.next_offset!)}>다음 저장 범위</button>
          <button className="button secondary" disabled={page.kind==='samples'} onClick={()=>move('samples',0)}>저장 시점 보기</button>
          <button className="button secondary" disabled={page.kind==='events'} onClick={()=>move('events',0)}>관리 사건 보기</button>
          <button className="button secondary" onClick={()=>read(current!.api,current!.lookup)}>현재 권리 다시 조회</button></div>
        <p className="crop-caption">이미 읽은 화면의 권리를 계속 확인하는 기능은 아닙니다. 새 조회에서 실패하면 이전 값을 지웁니다.</p>
      </section>
      {sample&&<div className="coupled-viewer joint-viewer solar-viewer" data-selected-at={sample.time.at} data-selected-index={page.offset+index}
        data-result-id={summary.result_id} data-farm={JSON.stringify(summary.farm)} data-reference={JSON.stringify(summary.reference)}>
        <div className="coupled-top-grid"><section className="panel"><h2>LAI·과실 구획·온도 수치 모식도</h2>
          <Suspense fallback={<p role="status">3D 준비 중… 같은 값은 표에서 확인하세요.</p>}>
            <Scene sample={jointSceneSample(sample)} scales={scales} rangeLabel="현재 읽은 저장 시점 범위"/></Suspense></section>
          <section className="panel coupled-readout" data-selected-at={sample.time.at}><h2>같은 UTC의 작물·기후 계산값</h2>
            <Quantities values={{...sample.value.plant_state,...sample.value.climate_state,...sample.value.derived}} label="작물·기후 원값"/>
            <p className="crop-caption">온도는 공동 계산의 상태값입니다. 실제 계측 온도·생과 kg·숙기·수확량·마진 예측은 미검증입니다.</p></section></div>
        <section className="panel coupled-readout ventilation-diagnostic" data-selected-at={sample.time.at}
          data-ventilation={JSON.stringify(sample.value.ventilation)}><h2>같은 UTC의 명시 환기 경계값</h2>
          <Quantities values={{...sample.value.ventilation.derived,...sample.value.ventilation.forcing_contribution,
            latent_energy:sample.value.ventilation.latent_energy}} label="명시 환기 원값"/>
          <p className="crop-caption">명시 환기량으로 계산한 실내·실외 교환입니다. 시설의 실제 환기량·구매 에너지·비용 예측은 아닙니다.</p>
          <details><summary>환기 입력 SHA-256</summary><code>{sample.value.ventilation.input_sha256}</code></details></section>
        <SolarDiagnostic state={sample.value} at={sample.time.at}/>
        <section className="panel crop-timeline"><h2>현재 범위의 저장 시점</h2><p className="crop-selected-time" aria-live={playing?'off':'polite'}>
          <strong>{sample.time.at}</strong><span>원 시점 {page.offset+index+1} / {summary.reference.artifact.sample_count} · UTC</span></p>
          <label>저장 성장 시점 선택<input type="range" min={0} max={samples.length-1} step={1} value={index}
            aria-valuetext={sample.time.at+' UTC'} onChange={e=>select(Number(e.target.value))}/></label>
          <div className="crop-play-buttons"><button className="button secondary" aria-label="이전 저장 성장 시점" disabled={index===0} onClick={()=>select(index-1)}>이전</button>
            <button className="button primary" aria-label={playing?'성장 일시 정지':'성장 자동 재생'} disabled={reduced||index===samples.length-1}
              onClick={()=>setPlaying(v=>!v)}>{playing?'정지':'재생'}</button>
            <button className="button secondary" aria-label="다음 저장 성장 시점" disabled={index===samples.length-1} onClick={()=>select(index+1)}>다음</button></div>
          <p className="crop-caption">화면1초마다 다음 저장 시점으로 이동하며 현재 범위 끝에서 멈춥니다. 중간 상태를 만들지 않습니다.
            {reduced&&' 동작 줄이기 설정으로 자동 재생은 꺼져 있습니다.'}</p></section>
        <Suspense fallback={<p role="status">그래프 준비 중… 원값은 표에서 확인하세요.</p>}><Chart samples={samples} sample={sample} scales={scales}/></Suspense>
        <section className="panel coupled-cohorts" data-selected-at={sample.time.at}><h2>선택 시점의 50과실 구획 원값</h2>
          <Cohorts state={sample.value.cohort_state} at={sample.time.at}/></section>
        <section className="panel crop-data joint-samples"><h2>현재 범위의 원 저장 시점</h2><div className="crop-table-scroll" tabIndex={0} role="region" aria-label="작물·기후 시점 표">
          <table className="crop-table"><caption>원 UTC·LAI·수관/공기 온도. 시간 버튼으로 같은 저장 시점을 선택합니다.</caption>
            <thead><tr><th scope="col">UTC</th><th scope="col">LAI</th><th scope="col">수관 °C</th><th scope="col">공기 °C</th></tr></thead>
            <tbody>{samples.map((row,i)=><tr key={row.time.step_index} aria-selected={i===index}>
              <th scope="row"><button className="crop-time-button" onClick={()=>select(i)}>{row.time.at}</button></th>
              {[row.value.derived.leaf_area_index,row.value.derived.canopy_temperature,row.value.climate_state.air_temperature].map((q,j)=><td key={j} data-raw-value={q.value}>{String(q.value)}</td>)}</tr>)}</tbody>
          </table></div></section>
        <details className="panel crop-cumulative joint-ledgers" data-selected-at={sample.time.at}><summary>선택 시점의 누적 유량·사건 합계·수지</summary>
          <p>{sample.time.at} · UTC · 41연속/6사건 장부·15수지</p><Quantities values={sample.value.integrated_transfers} label="누적41장부"/>
          <Quantities values={sample.value.event_totals} label="관리 사건 누적"/>
          <Quantities values={sample.value.balance_residuals} label="수지 잔차"/><Quantities values={sample.value.balance_budgets} label="잔차 허용 한도"/></details>
      </div>}
      {page.kind==='samples'&&!samples.length&&<section className="panel cycle-no-samples"><h2>선택 가능한 저장 시점이 없습니다</h2>
        <p>시작·끝·실패 시각의 프레임을 만들지 않습니다. 마지막 확정 진단과 저장 출력을 구분합니다.</p></section>}
      {page.kind==='events'&&<section className="panel cycle-events"><h2>현재 범위의 관리 사건</h2>
        <p>명시적 제거 입력이며 실제 적정 관리·생과 수확이 아닙니다.</p>{!page.records.length&&<p>현재 범위에 저장된 관리 사건이 없습니다.</p>}
        {page.records.map((event,i)=><article key={event.time.step_index} data-event-index={page.offset+i}>
          <h3>{event.time.at} · UTC</h3><Quantities values={event.value.management.removed_totals} label="사건 제거 합계"/>
          <details><summary>사건 직전·직후 일사·환기 진단</summary><pre>{JSON.stringify({before:event.value.solar_before,after:event.value.solar_after},null,2)}</pre></details>
          <details><summary>제거·직전/직후 상태와 수지 원값</summary><pre>{JSON.stringify(event.value.management,null,2)}</pre></details></article>)}</section>}
      <details className="panel crop-evidence cycle-evidence joint-evidence"><summary>고정 입력·모델과 저장 증거</summary>
        <p>연구 {summary.study_id} / {summary.revision} · 저장 {summary.recorded_at}</p><p>결과 ID <code>{summary.result_id}</code></p>
        <p>계산 구간 {summary.reference.time_grid.start_utc} → {summary.reference.time_grid.end_utc} UTC</p>
        <p>32초 참조 검사는 전체 작기 정확도·실제 품종 검증을 뜻하지 않습니다. 현재 입력의 명시적 경계만 재생합니다.</p>
        <details><summary>고정 참조·모델 판본</summary><pre>{JSON.stringify({farm:summary.farm,reference:summary.reference,manifest:summary.summary.manifest},null,2)}</pre></details></details>
    </>}
  </div>;
}
