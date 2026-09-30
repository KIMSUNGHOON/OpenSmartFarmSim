import { lazy,Suspense,useEffect,useMemo,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import type { ThermalReplay } from './thermal-api';
import type { AuthoredThermalReplay } from './authored-thermal-api';
import ResultsTable from './ResultsTable';
import { metrics,displayValue,temperatureColor,kst } from './replay-format';
import './Replay.css';

const ZoneScene=lazy(()=>import('./ZoneScene'));
const ReplayChart=lazy(()=>import('./ReplayChart'));

type Api=ReturnType<typeof createApi>;
type ReplayKind='fixed'|'authored';
type Loaded={api:Api;kind:'fixed';data:ThermalReplay}|{api:Api;kind:'authored';data:AuthoredThermalReplay};
const messages:Record<string,string>={auth_required:'먼저 내부 시험 연결을 설정해 주세요.',
  access_denied:'이 계정에는 해당 Run을 읽을 권한이 없습니다.',not_available:'완료된 열 작업을 확인할 수 없습니다.',
  response_rejected:'서버 기록의 연결·범위·시각을 확인할 수 없어 표시를 보류했습니다.',
  network_unresolved:'응답을 받지 못했습니다. 조회를 다시 시도해 주세요.',server_unavailable:'서버가 Run을 확인하지 못했습니다.'};

export default function Replay({api,initialSelection}:{api:Api|null;
  initialSelection?:{kind:ReplayKind;jobId:string}}) {
  const [jobId,setJobId]=useState(initialSelection?.jobId ?? ''),[busy,setBusy]=useState(false),[error,setError]=useState<ApiError|null>(null);
  const [kind,setKind]=useState<ReplayKind>(initialSelection?.kind ?? 'fixed');
  const [loaded,setLoaded]=useState<Loaded|null>(null),[index,setIndex]=useState(0);
  const [playing,setPlaying]=useState(false),[reduced,setReduced]=useState(()=>matchMedia('(prefers-reduced-motion: reduce)').matches);
  const epoch=useRef(0);
  const data=loaded?.api===api ? loaded.data : null;
  const point=data?.series.points[index];
  const range=useMemo<readonly [number,number]>(()=>data ? [Math.min(...data.series.points.map(row=>row.temperature_k)),
    Math.max(...data.series.points.map(row=>row.temperature_k))] : [0,0],[data]);
  const maximumHeat=useMemo(()=>data ? Math.max(...data.series.points.map(row=>row.heat_delivered_w_th)) : 0,[data]);
  useEffect(()=>{epoch.current++;setLoaded(null);setBusy(false);setError(null);setIndex(0);setPlaying(false);
    setJobId(initialSelection?.jobId ?? '');setKind(initialSelection?.kind ?? 'fixed');
    return ()=>{epoch.current++;};},[api]);
  useEffect(()=>{const query=matchMedia('(prefers-reduced-motion: reduce)');
    const update=()=>{setReduced(query.matches);if(query.matches)setPlaying(false);};
    query.addEventListener('change',update);return ()=>query.removeEventListener('change',update);},[]);
  useEffect(()=>{if(!playing || !data || reduced)return;
    const timer=setInterval(()=>setIndex(current=>Math.min(current+1,data.series.points.length-1)),1000);
    return ()=>clearInterval(timer);},[playing,data,reduced]);
  useEffect(()=>{if(data && index===data.series.points.length-1)setPlaying(false);},[data,index]);
  useEffect(()=>{const pause=()=>{if(document.hidden)setPlaying(false);};
    document.addEventListener('visibilitychange',pause);return ()=>document.removeEventListener('visibilitychange',pause);},[]);
  function select(value:number) {setPlaying(false);setIndex(value);}
  function chooseKind(value:ReplayKind) {
    epoch.current++;setKind(value);setLoaded(null);setBusy(false);setError(null);
    setPlaying(false);setIndex(0);setJobId('');
  }
  async function load(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();if(busy)return;
    if(!api){setError(new ApiError('auth_required'));return;}
    const client=api,request=++epoch.current,selectedKind=kind;
    setBusy(true);setLoaded(null);setError(null);setPlaying(false);setIndex(0);
    try {
      if(selectedKind==='authored') {
        const value=await client.authoredThermalReplay(jobId.trim());
        if(request===epoch.current)setLoaded({api:client,kind:selectedKind,data:value});
      } else {
        const value=await client.thermalReplay(jobId.trim());
        if(request===epoch.current)setLoaded({api:client,kind:selectedKind,data:value});
      }
    }
    catch(cause){if(request===epoch.current)setError(cause instanceof ApiError ? cause : new ApiError('network_unresolved'));}
    finally {if(request===epoch.current)setBusy(false);}
  }
  return <div className="replay-workspace">
    <section className="panel replay-admission"><h2>저장된 열 계산 열기</h2>
      <fieldset className="replay-kind"><legend>재생할 계산 종류</legend>
        <label className={kind==='fixed' ? 'selected' : ''}><input type="radio" name="thermal-replay-kind"
          value="fixed" checked={kind==='fixed'} onChange={()=>chooseKind('fixed')}/>고정 합성 열 재생</label>
        <label className={kind==='authored' ? 'selected' : ''}><input type="radio" name="thermal-replay-kind"
          value="authored" checked={kind==='authored'} onChange={()=>chooseKind('authored')}/>작성한 농장 열 재생</label>
      </fieldset>
      <details open={!data}><summary>완료된 열 작업 선택</summary>
      <p>완료된 열 계산 작업의 ID를 입력하세요. 서버에서 기록·출처·현재 열람 권한을 확인합니다.</p>
      <form onSubmit={load}><label>완료된 열 작업 ID<input value={jobId} disabled={busy} autoComplete="off" spellCheck={false}
        pattern="[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}" required
        onChange={event=>{epoch.current++;setJobId(event.target.value);setLoaded(null);setError(null);setPlaying(false);}}/></label>
        <button className="button primary" disabled={busy}>{busy ? '기록 확인 중…' : '저장된 Run 조회'}</button></form></details>
      {error && <p className="notice error" role="alert">{messages[error.code] ?? '실행 기록을 확인할 수 없습니다.'}</p>}
    </section>
    {!data || !point ? <section className="panel replay-empty"><h2>계산 기록을 선택해 주세요</h2>
      <p>조회한 합성 계산의 한 시각을 온실 개념도·그래프·표에서 함께 확인합니다.</p>
      <p className="muted">식물 생장·수확 예측과 실제 농장 관측을 재생하는 화면은 아닙니다.</p></section> :
      <div className="replay-viewer" data-run-id={data.summary.run_id} data-selected-at={point.at_utc}
        data-replay-kind={loaded?.kind}>
        <div className="notice"><strong>{loaded?.kind==='authored' ?
          '작성한 농장 입력 · 합성 열 재생' : '직접 작성한 합성 자료 · 저장된 계산 재생'}</strong>
          <p>가상 시각의 사후 재현입니다. 현장 정확도·작물 선택·생장·수확은 아직 검증되지 않았습니다.</p></div>
        <div className="replay-top-grid">
          <section className="panel replay-scene-panel" id="viewport-1-c-scene"><h2>3D 온실 상태</h2>
            <Suspense fallback={<p role="status">3D 장면을 준비합니다. 수치는 요약과 표에서 확인할 수 있습니다.</p>}><ZoneScene point={point} range={range} maximumHeat={maximumHeat}/></Suspense>
            <div className="scene-legend"><span className="legend-color" style={{background:temperatureColor({...point,temperature_k:range[0]},range)}}/>
              <span>{(range[0]-273.15).toFixed(2)}°C</span><span>이 Run의 온도 색 범위</span>
              <span>{(range[1]-273.15).toFixed(2)}°C</span><span className="legend-color" style={{background:temperatureColor({...point,temperature_k:range[1]},range)}}/></div>
            <p className="muted">색은 저장 값의 상대 범위입니다. 작물의 안전·최적 온도 기준이 아닙니다. 공급열 막대는 이 Run의 최대 공급열 {maximumHeat.toPrecision(6)} W_th를 기준으로 표시합니다.</p>
          </section>
          <section className="panel replay-summary" id="viewport-1-c-summary" aria-label="현재 시각 요약" data-selected-at={point.at_utc}>
            <h2>현재 시각 요약</h2><p className="selected-time" aria-live={playing ? 'off' : 'polite'}><strong>{kst(point.at_utc)}</strong><span>{point.at_utc} · UTC</span></p>
            <dl>{metrics.map(metric=><div key={metric.key}><dt>{metric.label}</dt><dd data-metric={metric.key} data-raw-value={point[metric.key]}>{displayValue(point,metric)} <small>{metric.unit}</small></dd></div>)}</dl>
            <p className="muted">환기·제어 명령은 이 시계열에 제공되지 않습니다.</p>
          </section>
        </div>
        <section className="panel replay-controls"><h2>저장 시각 선택</h2>
          <label>저장 시각 선택<input type="range" min={0} max={data.series.points.length-1} step={1} value={index}
            aria-valuetext={point.at_utc+' UTC · '+kst(point.at_utc)} onChange={event=>select(Number(event.target.value))}/></label>
          <div className="replay-control-buttons"><button className="button secondary" disabled={index===0} onClick={()=>select(index-1)}>이전 1분</button>
            <button className="button primary" disabled={reduced || index===data.series.points.length-1} onClick={()=>setPlaying(value=>!value)}>{playing ? '일시 정지' : '자동 재생'}</button>
            <button className="button secondary" disabled={index===data.series.points.length-1} onClick={()=>select(index+1)}>다음 1분</button>
            <button className="button secondary" onClick={()=>select(0)}>처음 시각</button><span>{index+1} / {data.series.points.length} 저장 시점</span></div>
          <p className="muted">자동 재생은 화면 1초마다 저장 시각을 1분 이동합니다. 중간 상태를 만들지 않습니다.{reduced && ' 동작 줄이기 설정에 따라 자동 재생은 꺼져 있습니다.'}</p>
        </section>
        <Suspense fallback={<p role="status">그래프를 준비합니다. 같은 값은 아래 표에서 확인할 수 있습니다.</p>}><ReplayChart points={data.series.points} point={point}/></Suspense>
        <ResultsTable points={data.series.points} point={point} onSelect={select}/>
        <section className="panel replay-evidence"><h2>계산과 출처 기록</h2>
          <p>열 모델 {data.summary.model_version} · 적분 {data.summary.engine_version} · 단위 {data.summary.unit_registry_version}</p>
          <p>공급열 kWh_th는 각 1분 구간의 계산값입니다. 실제 구매 전력·연료·비용을 뜻하지 않습니다.</p>
          {loaded?.kind==='authored' ? <><p>현재 농장 등록·권리·해제 기록을 서버가 재확인한 내부 재생입니다. 독립 G1 수용이나 현장 정확도를 뜻하지 않습니다.</p>
            <details><summary>작성 입력과 해시</summary>
              <p>농장 판본: {loaded.data.summary.scenario_id} / {loaded.data.summary.scenario_revision}</p>
              <p>등록 입력: <code>{loaded.data.summary.registration_sha256}</code><br/>
                해제 기록: <code>{loaded.data.summary.release_sha256}</code></p>
              <p>열 궤적 1: <code>{loaded.data.summary.trace_sha256[0]}</code><br/>
                열 궤적 2: <code>{loaded.data.summary.trace_sha256[1]}</code></p>
              <p>Run: <code>{loaded.data.summary.run_id}</code></p>
            </details></> : loaded?.kind==='fixed' ? <><details><summary>합성 출처와 법칙 표시 조건</summary>
            {loaded.data.manifest.used_sources.map(source=><div className="replay-source" key={source.fixture_id}><strong>{source.product_id}</strong>
              <p>{source.source_locator}<br/>합성 자체 검사·자체 검토 · 표시권: 허용</p>
              <p>알 수 있게 된 가상 시각: {source.available_at_utc}<br/>조회 기록 시각: {source.retrieved_at_utc}</p>
              <p>판본 {source.vintage_id} / {source.revision_id}<br/>원본 해시: <code>{source.raw_sha256}</code></p></div>)}
            <div className="replay-source"><strong>포화 수증기압 법칙 출처</strong><p>{loaded.data.manifest.law_reference.product_id}</p>
              <p>{loaded.data.manifest.law_reference.source_url}</p><p>발행 시각과 해당 판본의 가용 시각은 미확인입니다.</p>
              <p>{loaded.data.manifest.law_reference.display_conditions}</p></div>
            <p>스냅샷 생성 당시 미해결 항목:</p><ul>{loaded.data.manifest.source_unresolved_at_creation.map((item,i)=><li key={i}>{item}</li>)}</ul>
            <p>이 열 계산에서 제외한 입력: {loaded.data.manifest.excluded_fixture_ids.join(', ')}</p>
          </details><details><summary>실행 식별자와 고정 해시</summary>
            <p>Run: <code>{loaded.data.summary.run_id}</code><br/>스냅샷: <code>{loaded.data.manifest.snapshot_id}</code></p>
            <p>Manifest: <code>{loaded.data.manifest.manifest_sha256}</code><br/>코드: <code>{loaded.data.manifest.code_sha256}</code><br/>환경: <code>{loaded.data.manifest.environment_sha256}</code></p>
          </details></> : null}
        </section>
      </div>}
  </div>;
}
