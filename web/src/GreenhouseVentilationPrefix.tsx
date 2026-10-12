import { lazy,Suspense,useMemo,useState } from 'react';
import type { createApi } from './api';
import type { VentilationExecutionLookup } from './greenhouseVentilationExecution';
import type { VentilationPrefixSummaryResponse } from './greenhouseVentilationPrefix';
import type { GreenhouseVentilationSample,GreenhouseVentilationEvent,JointQuantity } from './greenhouseVentilationReplay';
import { jointSceneSample,jointSceneScales } from './jointCropClimateGeometry';
import './CoupledCropReplay.css';
import './CycleCropReplay.css';
const Scene=lazy(()=>import('./CoupledCropScene'));
const Chart=lazy(()=>import('./JointCropClimateChart'));
type Api=ReturnType<typeof createApi>;
export type VentilationPrefixSnapshot=Readonly<{summary:VentilationPrefixSummaryResponse;samples:readonly GreenhouseVentilationSample[];
  events:readonly GreenhouseVentilationEvent[];sampleStart:number;eventStart:number}>;
export async function readVentilationPrefixSnapshot(api:Api,lookup:VentilationExecutionLookup,signal:AbortSignal){
  const summary=await api.greenhouseVentilationPrefix(lookup,signal);
  if(summary.prefix_status!=='accepted')return {observedAt:summary.observed_at,snapshot:null};
  const counts=summary.summary.counts,selector=summary.reference.selector;
  const sampleStart=Math.max(0,counts.samples-64),eventStart=Math.max(0,counts.events-8);
  const options={signal,summary};
  const events=counts.events?(await api.greenhouseVentilationPrefixPage(lookup,selector,
    {kind:'events',start:eventStart,limit:8},options)).page.records as readonly GreenhouseVentilationEvent[]:[];
  const samples=counts.samples?(await api.greenhouseVentilationPrefixPage(lookup,selector,
    {kind:'samples',start:sampleStart,limit:64},options)).page.records as readonly GreenhouseVentilationSample[]:[];
  return {observedAt:summary.observed_at,snapshot:{summary,samples,events,sampleStart,eventStart} satisfies VentilationPrefixSnapshot};
}
const LABELS:Record<string,string>={leaf_area_index:'잎 면적 지수 (LAI)',canopy_temperature:'수관 온도',air_temperature:'공기 온도',
  air_vapor_mass:'공기 수증기 질량',buffer:'버퍼 탄소',leaf:'잎 탄소',stem_root:'줄기·뿌리 탄소',
  temperature_filtered_24h:'24시간 평활 온도',temperature_sum:'온도 합',indoor_vapor_density:'실내 수증기 밀도',outdoor_vapor_density:'실외 수증기 밀도',
  air_external_sensible_heat:'공기 현열 경계량',air_external_vapor:'공기 수증기 경계량',latent_energy:'환기 잠열 흐름',
  ventilation_sensible_heat:'환기 누적 현열',ventilation_vapor:'환기 누적 수증기',ventilation_latent_energy:'환기 누적 잠열'};
function Quantities({values,label}:{values:Readonly<Record<string,JointQuantity>>;label:string}){
  return <dl aria-label={label}>{Object.entries(values).map(([key,q])=><div key={key}><dt>{LABELS[key]??key}</dt>
    <dd data-metric={key} data-raw-value={q.value}>{String(q.value)}<small>{q.unit}</small></dd></div>)}</dl>;
}
export default function GreenhouseVentilationPrefix({snapshot,observedAt,stale}:{snapshot:VentilationPrefixSnapshot;observedAt:string;stale:boolean}){
  const {summary,samples,events,sampleStart,eventStart}=snapshot;
  const [index,setIndex]=useState(()=>Math.max(0,samples.length-1)),sample=samples[index];
  const scales=useMemo(()=>jointSceneScales(samples),[samples]),ref=summary.reference;
  return <section className="joint-prefix" aria-label="계산 중 확정 생장 결과" data-prefix-sequence={ref.selector.publication_sequence}
    data-prefix-selector={JSON.stringify(ref.selector)} data-prefix-reference={JSON.stringify(ref)}>
    <section className="panel cycle-range"><div className="crop-heading"><h2>계산 중 확정된 생장</h2><span className="badge">합성 계산 · 부분 결과</span></div>
      <p role="status">{stale?'새 응답 확인 중 · 아래는 마지막으로 확인한 확정 결과입니다.':'확정된 원 저장값을 표시합니다.'}</p>
      <dl className="prefix-times"><div><dt>부분 결과 확인 (UTC)</dt><dd>{observedAt}</dd></div>
        <div><dt>판본 최초 수용 (UTC)</dt><dd>{ref.checkpoint.checkpoint_recorded_at}</dd></div>
        <div><dt>계산된 시각 (UTC)</dt><dd>{ref.checkpoint.computed_through_utc??'아직 계산 전'}</dd></div>
        <div><dt>마지막 저장 시점 (UTC)</dt><dd>{summary.summary.last_sample_utc??'아직 저장 시점 없음'}</dd></div></dl>
      <p>확정 {summary.summary.counts.samples}시점 / {summary.summary.counts.events}사건 · 현재 최근 {samples.length}시점 / {events.length}사건</p>
      <p className="crop-caption">새 저장 시점을 받으면 가장 최근 시점을 선택합니다. 최대64시점·8사건의 원값을 읽으며 미확정 중간 상태를 만들지 않습니다.</p>
    </section>
    {sample?<div className="coupled-viewer joint-prefix-viewer" data-selected-at={sample.time.at} data-selected-index={sampleStart+index}>
      <div className="coupled-top-grid"><section className="panel"><h2>확정 LAI·과실 구획·온도 3D</h2>
        <Suspense fallback={<p role="status">3D 준비 중… 같은 원값은 표에서 확인하세요.</p>}>
          <Scene sample={jointSceneSample(sample)} scales={scales} rangeLabel="현재 읽은 확정 부분 결과"/></Suspense></section>
        <section className="panel coupled-readout" data-selected-at={sample.time.at}><h2>같은 UTC의 확정 계산값</h2>
          <p className="crop-selected-time">{sample.time.at} · UTC</p>
          <Quantities values={{...sample.value.plant_state,...sample.value.climate_state,...sample.value.derived}} label="확정 작물·기후 원값"/>
          <p className="crop-caption">수치 모식도입니다. 실제 품종 외형·현장 관측·생산량·수확량·미래 마진은 검증 전입니다.</p></section></div>
      <section className="panel ventilation-readout" data-selected-at={sample.time.at} data-ventilation={JSON.stringify(sample.value.ventilation)}>
        <h2>같은 UTC의 명시 환기 원값</h2><p>{sample.time.at} · UTC</p>
        <Quantities values={{...sample.value.ventilation.derived,...sample.value.ventilation.forcing_contribution,
          latent_energy:sample.value.ventilation.latent_energy}} label="확정 명시 환기 원값"/>
        <p className="crop-caption">등록된 환기량의 열·수증기 교환 수치입니다. 구매 에너지·설비 용량·농장 생산 예측은 검증 전입니다.</p>
        <details><summary>확정 환기 입력 식별자</summary><p>{sample.value.ventilation.input_sha256}</p></details></section>
      <section className="panel crop-timeline"><h2>확정 저장 시점 선택</h2><p aria-live="polite">{sample.time.at} · 원 시점 {sampleStart+index+1} / {summary.summary.counts.samples}</p>
        <label>확정 생장 시점 선택<input type="range" min={0} max={samples.length-1} step={1} value={index}
          aria-valuetext={sample.time.at+' UTC'} onChange={event=>setIndex(Number(event.target.value))}/></label>
        <div className="crop-play-buttons"><button className="button secondary" disabled={index===0} onClick={()=>setIndex(index-1)}>이전 확정 시점</button>
          <button className="button secondary" disabled={index===samples.length-1} onClick={()=>setIndex(samples.length-1)}>최신 확정 시점</button></div></section>
      <Suspense fallback={<p role="status">확정 원값 그래프 준비 중…</p>}><Chart samples={samples} sample={sample} scales={scales}/></Suspense>
      <section className="panel coupled-cohorts" data-selected-at={sample.time.at}><h2>확정 시점의 50과실 구획</h2>
        <div className="crop-table-scroll" tabIndex={0} role="region" aria-label="확정 과실 구획 원값"><table className="coupled-cohort-table">
          <caption>{sample.time.at} UTC · C는 탄수화물 환산 질량, N은 개수 상당량입니다.</caption>
          <thead><tr><th scope="col">구획</th><th scope="col">C ({sample.value.cohort_state.fruit_carbohydrate[0]!.unit})</th>
            <th scope="col">N ({sample.value.cohort_state.fruit_number[0]!.unit})</th></tr></thead>
          <tbody>{sample.value.cohort_state.fruit_carbohydrate.map((q,i)=><tr key={i}><th scope="row">{i+1}</th>
            <td data-metric="carbon" data-raw-value={q.value}>{String(q.value)}</td>
            <td data-metric="number" data-raw-value={sample.value.cohort_state.fruit_number[i]!.value}>{String(sample.value.cohort_state.fruit_number[i]!.value)}</td></tr>)}</tbody>
        </table></div></section>
      <section className="panel joint-samples"><h2>현재 확정 범위의 원 저장 시점</h2><div className="crop-table-scroll" tabIndex={0} role="region" aria-label="확정 생장 시점 표">
        <table className="crop-table"><caption>원 UTC·LAI·수관/공기 온도</caption><thead><tr><th scope="col">UTC</th><th scope="col">LAI</th><th scope="col">수관 °C</th><th scope="col">공기 °C</th></tr></thead>
          <tbody>{samples.map((row,i)=><tr key={row.time.step_index} aria-selected={i===index}><th scope="row">
            <button className="crop-time-button" onClick={()=>setIndex(i)}>{row.time.at}</button></th>
            {[row.value.derived.leaf_area_index,row.value.derived.canopy_temperature,row.value.climate_state.air_temperature].map((q,j)=><td key={j} data-raw-value={q.value}>{String(q.value)}</td>)}</tr>)}</tbody>
        </table></div></section>
      <details className="panel joint-ledgers" data-selected-at={sample.time.at}><summary>선택 확정 시점의 장부와 수지</summary><p>{sample.time.at} · UTC</p>
        <Quantities values={sample.value.integrated_transfers} label="확정 누적25장부"/><Quantities values={sample.value.event_totals} label="확정 사건 누적"/>
        <Quantities values={sample.value.balance_residuals} label="확정 수지 잔차"/><Quantities values={sample.value.balance_budgets} label="확정 잔차 허용 한도"/></details>
    </div>:<section className="panel prefix-empty"><h2>아직 확정된 생장 시점이 없습니다</h2><p>원 저장 시점이 생길 때까지 3D 프레임을 만들지 않습니다.</p></section>}
    <section className="panel cycle-events"><h2>같은 확정 판본의 관리 사건</h2><p>명시적 제거 입력이며 실제 적정 관리나 생과 수확을 뜻하지 않습니다.</p>
      {!events.length&&<p>확정된 관리 사건이 없습니다.</p>}{events.map((event,i)=><article key={event.time.step_index} data-event-index={eventStart+i}>
        <h3>{event.time.at} · UTC</h3><Quantities values={event.value.management.removed_totals} label="확정 사건 제거 합계"/>
        <details><summary>사건 직후 명시 환기 원값</summary><pre>{JSON.stringify(event.value.ventilation_after,null,2)}</pre></details>
        <details><summary>관리 사건 원값</summary><pre>{JSON.stringify(event.value.management,null,2)}</pre></details></article>)}</section>
    <details className="panel crop-evidence"><summary>현재 확정 판본과 입력 증거</summary><p>연구 {ref.study_id} / {ref.revision} · G0–G4 미평가</p>
      <pre>{JSON.stringify(ref,null,2)}</pre></details>
  </section>;
}
