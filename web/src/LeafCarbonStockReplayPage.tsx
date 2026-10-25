import {useEffect,useState} from 'react';
import GrowingGeometryScene from './GrowingGeometryScene';
import {loadLeafCarbonStockReplay,isLeafCarbonStockScenario,type LeafCarbonStockReplay,type LeafCarbonStockScenario} from './leafCarbonStockReplay';
import {readLeafCarbonStockLocation,leafCarbonStockURL} from './leafCarbonStockReplayLocation';
import {GROWING_SCAFFOLD} from './growingGeometryPlant';
import './MorphologyReplayPage.css';
import './LeafAreaReplayPage.css';
import './LeafLifecycleReplayPage.css';

const NAMES:Record<LeafCarbonStockScenario,string>={'warm-day-individual-stock':'따뜻한 낮','reverse-individual-stock':'역방향 열·증기 교환','cool-dark-individual-stock':'서늘한 암기',
 'warm-reference30-individual-stock':'따뜻한 낮 · 기준 온도30°C','warm-reference22-individual-stock':'따뜻한 낮 · 기준 온도22°C','empty-entry-individual-stock':'초기 빈 과실 구획'};
export default function LeafCarbonStockReplayPage(){
 const [selection,setSelection]=useState(()=>readLeafCarbonStockLocation(window.location.search));
 const [loaded,setLoaded]=useState<LeafCarbonStockReplay|null>(null),[error,setError]=useState(false),[playing,setPlaying]=useState(false),[retry,setRetry]=useState(0);
 const data=loaded?.scenario===selection.scenario?loaded:null,frame=data?.frames[selection.index];
 useEffect(()=>{const controller=new AbortController();let active=true;setLoaded(null);setError(false);setPlaying(false);
  loadLeafCarbonStockReplay(selection.scenario,controller.signal).then(value=>{if(active)setLoaded(value);},()=>{if(active)setError(true);});
  return()=>{active=false;controller.abort();};
 },[selection.scenario,retry]);
 useEffect(()=>{const pop=()=>{setPlaying(false);setSelection(readLeafCarbonStockLocation(window.location.search));};window.addEventListener('popstate',pop);return()=>window.removeEventListener('popstate',pop);},[]);
 useEffect(()=>{if(data){const url=leafCarbonStockURL(window.location.href,selection.scenario,selection.index);if(url)window.history.replaceState(null,'',url);}},[data,selection]);
 useEffect(()=>{if(playing&&data&&selection.index===data.frames.length-1)setPlaying(false);},[playing,data,selection.index]);
 useEffect(()=>{if(!playing||!data)return;const timer=window.setInterval(()=>setSelection(value=>({...value,index:Math.min(value.index+1,data.frames.length-1)})),900);
  const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
  return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',hidden);};
 },[playing,data]);
 const select=(index:number)=>{setPlaying(false);setSelection(value=>({...value,index}));};
 const at=frame?`${frame.at.time_origin_utc} + ${frame.at.elapsed_seconds_exact.numerator}/${frame.at.elapsed_seconds_exact.denominator} s`:'';
 const maximumLAI=data?Math.max(...data.frames.map(f=>f.sample.derived.leaf_area_index!.value)):1;
 const y=(lai:number)=>125-lai/maximumLAI*105;
 const maximumCarbon=data?Math.max(...data.frames.flatMap(f=>f.leaves.map(l=>l.carbon.value))):1;
 const carbonY=(value:number)=>125-(maximumCarbon>0?value/maximumCarbon:0)*105;
 const colors=['#315c3c','#718a3e','#958357'];
 return <main className="morphology-page leaf-area-page lifecycle-page" data-selected-at={at||undefined} data-selected-index={frame?.index}
  data-artifact-sha256={data?.artifact_sha256} data-scenario={selection.scenario}>
  <header className="morphology-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR / STORED LEAF CARBON / AREA</span>
   <h1>저장된 잎의 탄소와 면적</h1><p>같은 계산 시점의 탄소량·면적·기후를 실제 잎 표면·표·그래프로 확인합니다.</p></div>
   <nav aria-label="연구 화면"><a href="./growing-geometry-replay.html">기존 면적·기후 예제 ↗</a><br/><a href="./crop-appearance.html">작물 외형 보기 ↗</a></nav></header>
  <p className="morphology-scope">자체 합성32초 계산 · 저장 결과 재생 · 실제 품종·농장 검증 전</p>
  <div className="lifecycle-choice"><label>합성 계산 사례 <select value={selection.scenario} onChange={event=>{
   const scenario=event.target.value;if(!isLeafCarbonStockScenario(scenario))return;setPlaying(false);setSelection({scenario,index:0});
  }}>{Object.entries(NAMES).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
   <p>짧은 검증 구간이라 잎의 외형 변화가 작습니다. 원 저장값의 변화량을 확대하지 않습니다.</p></div>
  {!data||!frame?<section role="status"><p>{error?'저장 결과 표시 보류: 원 파일·권리·무결성을 확인할 수 없습니다.':'저장된 계산 결과를 확인하고 있습니다.'}</p>
   {error&&<button onClick={()=>setRetry(n=>n+1)}>원 결과 다시 확인</button>}</section>:<>
   <div className="morphology-layout"><GrowingGeometryScene frame={frame}/>
    <aside className="morphology-summary" aria-label="선택한 저장 시점" data-selected-at={at}>
     <span className="morphology-eyebrow">SELECTED MODEL TIME</span><h2>모델 경과 {String(frame.elapsed_seconds)}초</h2>
     <dl><div><dt>저장 LAI</dt><dd data-raw-lai={frame.sample.derived.leaf_area_index!.value}>{frame.sample.derived.leaf_area_index!.value.toFixed(6)} <small>m²/m²</small></dd></div>
      <div><dt>실내 기온</dt><dd data-raw-air-temperature={frame.climate.air_temperature!.value}>{frame.climate.air_temperature!.value.toFixed(6)} <small>°C</small></dd></div>
      <div><dt>수관 온도</dt><dd data-raw-canopy-temperature={frame.sample.derived.canopy_temperature!.value}>{frame.sample.derived.canopy_temperature!.value.toFixed(6)} <small>°C</small></dd></div>
      <div><dt>잎 탄수화물 합계</dt><dd data-raw-leaf-carbon-total={frame.sample.derived.leaf_carbohydrate!.value}>{frame.sample.derived.leaf_carbohydrate!.value.toFixed(3)} <small>mg CH₂O/m²</small></dd></div></dl>
     <p>잎의 단면 표면적은 원 계산값입니다. 줄기·부착 위치·소엽 형태와 방향은 제작 외형이며, 보기 위한 조명은 고정했습니다.</p>
     <p>저장 잎 {frame.leaves.length}개 · 탄소량의 기준은 재배면적입니다.<br/>원점 {frame.at.time_origin_utc}<br/>정확 경과 {frame.at.elapsed_seconds_exact.numerator}/{frame.at.elapsed_seconds_exact.denominator}초</p>
     <details><summary>계산 근거와 저장 내역</summary><p className="morphology-hash">결과 {data.artifact_sha256}<br/>시점 {frame.checkpoint_sha256}</p>
      <p>제작 외형 {GROWING_SCAFFOLD.version}. 줄기{GROWING_SCAFFOLD.stem_height_m}m는 제작한 크기이며 예측된 키가 아닙니다.</p>
      <a href={`./leaf-carbon-stock-replay/${selection.scenario}/source-inputs.json`}>원 입력</a> · <a href={`./leaf-carbon-stock-replay/${selection.scenario}/root.json`}>저장 지문</a> ·
      <a href={`./leaf-carbon-stock-replay/${selection.scenario}/checkpoint-${frame.index}.json`}>현재 원 상태</a></details>
    </aside></div>
   <section className="morphology-timeline" aria-label="저장 시점 재생"><div className="morphology-controls">
    <button onClick={()=>{if(!playing&&selection.index===data.frames.length-1)select(0);setPlaying(!playing);}}>{playing?'일시 정지':'저장 결과 재생'}</button>
    <button disabled={selection.index===0} onClick={()=>select(0)}>처음</button><button disabled={selection.index===0} onClick={()=>select(selection.index-1)}>이전</button>
    <button disabled={selection.index===data.frames.length-1} onClick={()=>select(selection.index+1)}>다음</button><button disabled={selection.index===data.frames.length-1} onClick={()=>select(data.frames.length-1)}>마지막</button>
    <span role="status">{playing?'원 저장 시점을 재생 중':'일시 정지'} · {selection.index+1}/{data.frames.length} · 새 계산 없음</span></div>
    <label>저장 시점<input type="range" min="0" max={data.frames.length-1} step="1" value={selection.index} onChange={event=>select(Number(event.target.value))}/></label>
    <div className="morphology-range"><span>경과0초</span><span>합성 모델 시각 · 원 저장 시점</span><span>경과{String(data.frames.at(-1)!.elapsed_seconds)}초</span></div></section>
   <div className="morphology-evidence"><section className="morphology-history" aria-label="저장 LAI 이력"><h2>저장 LAI <small>m²/m²</small></h2>
    <svg viewBox="0 0 640 160" role="img" aria-label={`${data.frames.length}개 원 저장 시점의 LAI`}><line x1="25" y1="125" x2="615" y2="125" stroke="#c4ccb9"/>
     <polyline fill="none" stroke="#729361" strokeWidth="2" points={data.frames.map((f,i)=>`${25+i/(data.frames.length-1)*590},${y(f.sample.derived.leaf_area_index!.value)}`).join(' ')}/>
     {data.frames.map((f,i)=><circle key={i} data-index={i} data-lai={f.sample.derived.leaf_area_index!.value} cx={25+i/(data.frames.length-1)*590} cy={y(f.sample.derived.leaf_area_index!.value)}
      r={i===selection.index?6:3} fill={i===selection.index?'#224d33':'#93a884'}><title>경과{f.elapsed_seconds}초 · {String(f.sample.derived.leaf_area_index!.value)} m²/m²</title></circle>)}
     <text x="25" y="150">경과0초</text><text x="540" y="150">경과{String(data.frames.at(-1)!.elapsed_seconds)}초</text></svg>
    <p className="leaf-area-note">원 저장값과0부터 시작하는 축입니다. 새로운 중간 생장을 만들지 않습니다.</p>
    <h3>저장된 잎 탄소량 <small>mg CH₂O/m²</small></h3>
    <svg className="leaf-carbon-history" viewBox="0 0 640 160" role="img" aria-label="원 저장 시점의 잎별 탄소량">
     <line x1="25" y1="125" x2="615" y2="125" stroke="#c4ccb9"/>
     {frame.leaves.map((leaf,j)=><g key={leaf.leaf_id}><polyline fill="none" stroke={colors[j]} strokeWidth="2"
      points={data.frames.map((f,i)=>`${25+i/(data.frames.length-1)*590},${carbonY(f.leaves[j]!.carbon.value)}`).join(' ')}/>
      {data.frames.map((f,i)=><circle key={i} data-index={i} data-leaf-id={leaf.leaf_id} data-carbon={f.leaves[j]!.carbon.value}
       cx={25+i/(data.frames.length-1)*590} cy={carbonY(f.leaves[j]!.carbon.value)} r={i===selection.index?5:2} fill={colors[j]}>
       <title>{leaf.leaf_id} · 경과{f.elapsed_seconds}초 · {String(f.leaves[j]!.carbon.value)} mg CH₂O/m²</title></circle>)}</g>)}
     <text x="25" y="150">경과0초</text><text x="540" y="150">경과{String(data.frames.at(-1)!.elapsed_seconds)}초</text>
    </svg><p className="leaf-area-note">{frame.leaf_ids.join(' · ')} · 각 시점의 원 탄소량입니다. 면적이나 외형을 탄소량으로 환산하지 않습니다.</p></section>
    <section className="morphology-table" aria-label="현재 잎 원 값" data-selected-at={at}><h2>현재 잎</h2><div className="morphology-table-scroll"><table>
     <caption>모델 경과{frame.elapsed_seconds}초 · 원 저장값</caption><thead><tr><th scope="col">잎 ID</th><th scope="col">면적 (m²)</th><th scope="col">모델 탄소량 (mg CH₂O/m²)</th><th scope="col">열적 나이 (°C·day)</th></tr></thead>
     <tbody>{frame.leaves.map(leaf=><tr key={leaf.leaf_id} data-leaf-id={leaf.leaf_id}><th scope="row">{leaf.leaf_id}</th><td data-raw-area={leaf.area.value}>{String(leaf.area.value)}</td>
      <td data-raw-carbon={leaf.carbon.value}>{String(leaf.carbon.value)}</td><td data-raw-age={leaf.thermal_age.value}>{String(leaf.thermal_age.value)}</td></tr>)}</tbody></table></div>
     <details><summary>선택한 시점의 누적량과 수지</summary>
      <div className="morphology-table-scroll"><table aria-label="원 누적량"><thead><tr><th scope="col">저장 항목</th><th scope="col">누적량</th><th scope="col">단위</th></tr></thead>
       <tbody>{Object.entries(frame.integrated_transfers).map(([key,q])=><tr key={key} data-transfer-key={key}><th scope="row">{key}</th>
        <td data-raw-transfer={q.value}>{String(q.value)}</td><td>{q.unit}</td></tr>)}</tbody></table></div>
      <div className="morphology-table-scroll"><table aria-label="원 수지 잔차"><thead><tr><th scope="col">저장 수지</th><th scope="col">잔차</th><th scope="col">허용량</th></tr></thead>
       <tbody>{Object.entries(frame.balance_residuals).map(([key,q])=><tr key={key} data-balance-key={key}><th scope="row">{key}</th>
        <td data-raw-balance={q.value}>{String(q.value)}</td><td data-raw-budget={frame.balance_budgets[key]!.value}>{String(frame.balance_budgets[key]!.value)} {q.unit}</td></tr>)}</tbody></table></div>
     </details></section></div>
   <footer className="morphology-footer">자체 합성 계산을 재생한 연구 화면입니다. 실제 품종의 한 작기·수확·자원/사업성·최적 작물 추천에는 독립 농장 검증이 필요합니다.</footer>
  </>}
 </main>;
}
