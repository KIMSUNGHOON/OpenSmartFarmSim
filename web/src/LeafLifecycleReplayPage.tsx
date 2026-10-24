import {useEffect,useState} from 'react';
import MorphologyScene from './MorphologyScene';
import {loadLeafLifecycleReplay,activeLifecycleLeafBinding,type LeafLifecycleReplay} from './leafLifecycleReplay';
import {readLifecycleReplayLocation,lifecycleReplayURL} from './leafLifecycleReplayLocation';
import './MorphologyReplayPage.css';
import './LeafAreaReplayPage.css';
import './LeafLifecycleReplayPage.css';

export default function LeafLifecycleReplayPage(){
 const [selection,setSelection]=useState(()=>readLifecycleReplayLocation(window.location.search));
 const [loaded,setLoaded]=useState<LeafLifecycleReplay|null>(null),[error,setError]=useState(false),[playing,setPlaying]=useState(false);
 const data=loaded?.scenario===selection.scenario?loaded:null;
 useEffect(()=>{
  const controller=new AbortController();let active=true;setLoaded(null);setError(false);setPlaying(false);
  loadLeafLifecycleReplay(selection.scenario,controller.signal).then(value=>{if(active)setLoaded(value);},()=>{if(active)setError(true);});
  return()=>{active=false;controller.abort();};
 },[selection.scenario]);
 useEffect(()=>{if(data){const url=lifecycleReplayURL(window.location.href,selection.scenario,selection.index);if(url)window.history.replaceState(null,'',url);}},[data,selection]);
 useEffect(()=>{
  if(!playing||!data)return;
  const timer=window.setInterval(()=>setSelection(value=>{
   if(value.index+1>=data.frames.length){setPlaying(false);return value;}return {...value,index:value.index+1};
  }),900);
  const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
  return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',hidden);};
 },[playing,data]);
 const select=(index:number)=>{setPlaying(false);setSelection(value=>({...value,index}));};
 const frame=data?.frames[selection.index];
 const maximumArea=data?Math.max(...data.frames.map(f=>f.active_leaf_area.value)):0;
 const areaY=(value:number)=>125-(maximumArea>0?value/maximumArea:0)*105;
 return <main className="morphology-page leaf-area-page lifecycle-page" data-selected-at={frame?.at} data-selected-index={frame?.index}
  data-artifact-sha256={data?.artifact_sha256} data-scenario={selection.scenario}>
  <header className="morphology-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR / STORED LEAF LIFECYCLE</span>
   <h1>잎 생장과 관리</h1><p>현재 잎을 보고, 제거된 잎의 마지막 기록과 앞으로 생길 잎을 구분합니다.</p></div>
   <nav aria-label="연구 화면"><a href="./leaf-appearance-replay.html">제거 전 출현 예제 ↗</a><br/><a href="./morphology-execution.html">이전 계산 화면 ↗</a></nav></header>
  <p className="morphology-scope">자체 합성 입력 · 저장 결과 재생 · 실제 품종·농장 검증 전 · 생산·수익·작물 추천 미제공</p>
  <div className="lifecycle-choice"><label>관리 시나리오 <select value={selection.scenario} onChange={event=>{
   setPlaying(false);const scenario=event.target.value==='no-removal'?'no-removal':'with-removal';setSelection(value=>({...value,scenario}));
  }}><option value="with-removal">명시 잎 제거</option><option value="no-removal">제거 없음</option></select></label>
   <p>같은 저장 시점에서 두 시나리오를 비교할 수 있습니다.</p></div>
  {!data||!frame?<p role="status">{error?'저장 결과 표시 보류: 원 파일·권리·무결성을 확인할 수 없습니다.':'저장된 계산 결과를 확인하고 있습니다.'}</p>:<>
   <div className="morphology-layout"><MorphologyScene frame={frame.stem} maximum={Math.max(...data.frames.map(f=>f.stem.tracked_axis_length.value))} leafBinding={activeLifecycleLeafBinding(frame)}/>
    <aside className="morphology-summary" data-selected-at={frame.at} aria-label="선택한 저장 시점">
     <span className="morphology-eyebrow">SELECTED MODEL TIME</span><h2><time dateTime={frame.at}>{frame.at.replace('T',' ').replace('Z',' UTC')}</time></h2>
     <dl><div><dt>현재 잎 면적</dt><dd data-active-area={frame.active_leaf_area.value}>{frame.active_leaf_area.value.toFixed(6)} <small>m²</small></dd></div>
      <div><dt>현재 잎</dt><dd data-active-count={frame.active_leaf_count}>{frame.active_leaf_count} <small>개</small></dd></div>
      <div><dt>제거된 잎</dt><dd data-removed-count={frame.removed_leaf_count}>{frame.removed_leaf_count} <small>개</small></dd></div>
      <div><dt>출현 예정 잎</dt><dd data-pending-count={frame.pending_leaf_count}>{frame.pending_leaf_count} <small>개</small></dd></div></dl>
     <p>3D에는 현재 잎만 표시합니다. 각 잎의 원 면적을 제작한 단면 소엽 표면에 대응합니다.</p>
     <p>제거된 잎은 아래에 제거 당시의 마지막 값만 남깁니다. 출현 예정 잎은 현재 형상과 면적에 포함하지 않습니다.</p>
     <p>길이·폭·각도·소엽 수와 표면은 제작 가정입니다. 실제 품종 형태의 예측이 아닙니다.</p>
     <details><summary>원 입력과 저장 지문</summary><p className="morphology-hash">결과 {data.artifact_sha256}<br/>시점 {frame.result_sha256}<br/>줄기 {frame.stem.artifact_sha256}</p>
      <p>원점 {frame.time_origin_utc}. 아래 분수 초는 이 원점 이후의 정확한 모델 시각입니다.</p>
      <a href={`./leaf-lifecycle-replay/${selection.scenario}/input.json`}>원 출현 입력</a> · <a href={`./leaf-lifecycle-replay/${selection.scenario}/management.json`}>원 관리 입력</a> ·
      <a href={`./leaf-lifecycle-replay/${selection.scenario}/root.json`}>저장 지문</a></details>
    </aside></div>
   <section className="morphology-timeline" aria-label="저장 시점 재생"><div className="morphology-controls">
    <button onClick={()=>{if(!playing&&selection.index===data.frames.length-1)setSelection(value=>({...value,index:0}));setPlaying(!playing);}}>{playing?'일시 정지':'저장 결과 재생'}</button>
    <button disabled={selection.index===0} onClick={()=>select(0)}>처음</button><button disabled={selection.index===0} onClick={()=>select(selection.index-1)}>이전</button>
    <button disabled={selection.index===data.frames.length-1} onClick={()=>select(selection.index+1)}>다음</button><button disabled={selection.index===data.frames.length-1} onClick={()=>select(data.frames.length-1)}>마지막</button>
    <span role="status">{playing?'원 저장 시점을 재생 중':'일시 정지'} · {selection.index+1}/{data.frames.length} · 새 계산 없음</span></div>
    <label>저장 시점<input type="range" min="0" max={data.frames.length-1} step="1" value={selection.index} onChange={event=>select(Number(event.target.value))}/></label>
    <div className="morphology-range"><span>{data.frames[0]!.at}</span><span>합성 모델 시각 · 원 저장 시점</span><span>{data.frames.at(-1)!.at}</span></div></section>
   <div className="morphology-evidence"><section className="morphology-history" data-selected-at={frame.at} aria-label="현재 잎 면적 이력"><h2>현재 잎 면적 <small>m²</small></h2>
    <svg viewBox="0 0 640 160" role="img" aria-label={`${data.frames.length}개 원 저장 시점의 현재 잎 면적`}>
     <line x1="25" y1="125" x2="615" y2="125" stroke="#c4ccb9"/>
     <polyline fill="none" stroke="#729361" strokeWidth="2" points={data.frames.map((f,i)=>`${25+i/Math.max(1,data.frames.length-1)*590},${areaY(f.active_leaf_area.value)}`).join(' ')}/>
     {data.frames.map((f,i)=><circle key={f.at} data-at={f.at} data-area={f.active_leaf_area.value} cx={25+i/Math.max(1,data.frames.length-1)*590}
      cy={areaY(f.active_leaf_area.value)} r={i===selection.index?6:3} fill={i===selection.index?'#224d33':'#93a884'}>
      <title>{f.at} · {f.active_leaf_area.value} m²</title></circle>)}
     <text x="25" y="150">첫 저장 시점</text><text x="540" y="150">마지막 시점</text></svg>
    <p className="leaf-area-note">현재 잎만 합산한 원 저장값입니다. 제거된 잎의 마지막 면적을 현재 면적에 더하지 않습니다.</p></section>
    <section className="morphology-table lifecycle-active" data-selected-at={frame.at}><h2>현재 잎</h2>
     <div className="morphology-table-scroll"><table><caption>{frame.at} · m² 단위 원 저장값</caption><thead><tr><th scope="col">잎 ID</th><th scope="col">면적 (m²)</th><th scope="col">정확 열적 나이 (°C·day)</th></tr></thead>
      <tbody>{frame.active_leaves.map(leaf=><tr key={leaf.leaf_id} data-leaf-id={leaf.leaf_id}><th scope="row">{leaf.leaf_id}</th>
       <td data-raw-area={leaf.area.value}>{String(leaf.area.value)}</td><td data-age-exact={`${leaf.age_exact.numerator}/${leaf.age_exact.denominator}`}>{leaf.age_exact.numerator}/{leaf.age_exact.denominator}</td></tr>)}
       {frame.active_leaves.length===0&&<tr><td colSpan={3}>현재 표시할 잎이 없습니다.</td></tr>}</tbody></table></div></section></div>
   <section className="morphology-table lifecycle-removed" data-selected-at={frame.at}><h2>제거된 잎의 마지막 기록</h2>
    <p className="leaf-area-note">아래 면적과 나이는 제거 당시의 값입니다. 이후 시점의3D나 현재 면적에는 포함하지 않습니다.</p>
    {frame.removed_leaves.length===0?<p className="leaf-area-note">제거 이력이 없습니다.</p>:<div className="morphology-table-scroll"><table><caption>원점 {frame.time_origin_utc} · 제거 시점의 저장값</caption><thead><tr>
     <th scope="col">잎 ID</th><th scope="col">마지막 면적 (m²)</th><th scope="col">마지막 열적 나이 (°C·day)</th><th scope="col">제거 시각 (원점 이후 초)</th></tr></thead>
     <tbody>{frame.removed_leaves.map(leaf=><tr key={leaf.leaf_id} data-leaf-id={leaf.leaf_id}><th scope="row">{leaf.leaf_id}</th>
      <td data-last-area={leaf.area.value}>{String(leaf.area.value)}</td><td>{leaf.age_exact.numerator}/{leaf.age_exact.denominator}</td>
      <td data-last-at={`${leaf.last_at_elapsed_seconds_exact.numerator}/${leaf.last_at_elapsed_seconds_exact.denominator}`}>{leaf.last_at_elapsed_seconds_exact.numerator}/{leaf.last_at_elapsed_seconds_exact.denominator}</td></tr>)}</tbody></table></div>}</section>
   <section className="morphology-table lifecycle-pending" data-selected-at={frame.at}><h2>출현 예정 잎</h2>
    {frame.pending_leaves.length===0?<p className="leaf-area-note">출현 예정 잎이 없습니다.</p>:<div className="morphology-table-scroll"><table><caption>원점 {frame.time_origin_utc} · 현재 형상·면적 없음</caption><thead><tr>
     <th scope="col">예정 잎 ID</th><th scope="col">부착 마디 ID</th><th scope="col">출현 시각 (원점 이후 초)</th></tr></thead>
     <tbody>{frame.pending_leaves.map(leaf=><tr key={leaf.leaf_id} data-leaf-id={leaf.leaf_id}><th scope="row">{leaf.leaf_id}</th><td>{leaf.attachment_internode_id}</td>
      <td>{leaf.emerged_elapsed_seconds_exact.numerator}/{leaf.emerged_elapsed_seconds_exact.denominator}</td></tr>)}</tbody></table></div>}</section>
   <footer className="morphology-footer">명시 합성 계산과 제작 외형의 연결입니다. 실제 품종·한 작기·과실/수확·자원·경제·자율 작물 선정과 독립 농장 검증은 후속이며 G0–G4는 미평가입니다.</footer>
  </>}
 </main>;
}
