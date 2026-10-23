import { useEffect,useRef,useState } from 'react';
import MorphologyScene from './MorphologyScene';
import { loadLeafAreaReplay,type LeafAreaReplay } from './leafAreaReplay';
import { loadLeafPopulationReplay,type LeafPopulationReplay } from './leafPopulationReplay';
import './MorphologyReplayPage.css';
import './LeafAreaReplayPage.css';

export default function LeafAreaReplayPage({population=false,providedReplay,paused=false,embedded=false,initialIndex=0,onIndexChange}:{population?:boolean;
  providedReplay?:LeafAreaReplay|LeafPopulationReplay;paused?:boolean;embedded?:boolean;initialIndex?:number;onIndexChange?:(index:number)=>void}={}){
  const startingIndex=useRef(initialIndex);
  const [loaded,setLoaded]=useState<{population:boolean;data:LeafAreaReplay|LeafPopulationReplay}|null>(null),[error,setError]=useState(false),[index,setIndex]=useState(()=>providedReplay?Math.max(0,Math.min(initialIndex,providedReplay.frames.length-1)):0),[playing,setPlaying]=useState(false);
  const data=providedReplay??(loaded?.population===population?loaded.data:null);
  const title=population?'저장된 출현 잎과 줄기':'저장된 잎 면적과 줄기',directory=population?'./leaf-population-replay':'./leaf-area-replay';
  useEffect(()=>{const controller=new AbortController();let active=true;setError(false);setIndex(0);setPlaying(false);
    if(providedReplay){setIndex(Math.max(0,Math.min(startingIndex.current,providedReplay.frames.length-1)));return()=>{active=false;controller.abort();};}
    const load=population?loadLeafPopulationReplay:loadLeafAreaReplay;
    load(controller.signal).then(value=>{if(active)setLoaded({population,data:value});},()=>{if(active)setError(true);});
    return()=>{active=false;controller.abort();};},[population,providedReplay]);
  useEffect(()=>{if(paused)setPlaying(false);},[paused]);
  useEffect(()=>{if(data)onIndexChange?.(index);},[data,index,onIndexChange]);
  useEffect(()=>{if(!playing||!data||paused)return;
    const timer=window.setInterval(()=>setIndex(value=>{if(value+1>=data.frames.length){setPlaying(false);return value;}return value+1;}),900);
    const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
    return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',hidden);};},[playing,data,paused]);
  const select=(value:number)=>{setPlaying(false);setIndex(value);};
  if(!data)return <main className="morphology-page leaf-area-page"><h1>{title}</h1><p role="status">{error?
    '저장 결과 표시 보류: 원 파일·권리·무결성을 확인할 수 없습니다. 대체 결과는 표시하지 않습니다.':'저장된 계산 결과를 확인하고 있습니다.'}</p></main>;
  const frame=data.frames[index]!,maximum=Math.max(...data.frames.map(f=>f.stem.tracked_axis_length.value));
  const maximumArea=Math.max(...data.frames.map(f=>f.tracked_leaf_area.value));
  const x=(i:number)=>25+i/Math.max(1,data.frames.length-1)*590,y=(v:number)=>125-v/maximumArea*105;
  const Container=embedded?'div':'main';
  return <Container className="morphology-page leaf-area-page" data-selected-at={frame.at} data-selected-index={index} data-artifact-sha256={data.artifact_sha256} data-source={population?'population':'initial'}>
    {!embedded&&<header className="morphology-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR / STORED LEAF AREA</span>
      <h1>{title}</h1><p>{population?'명시 출현 → 잎별 기온 적산 → 면적 계산 → 같은 시점의 3D':'기온 → 잎별 나이 → 면적 계산 → 같은 시점의 3D'}</p></div>
      <a href="./morphology-execution.html">계산 작업으로 ↗</a></header>}
    {!embedded&&<p className="morphology-scope">별도 자체 합성 입력 · 저장 결과 재생 · 실제 품종·농장 검증 전 · 생산·수익·작물 추천 미제공</p>}
    <div className="morphology-layout"><MorphologyScene frame={frame.stem} maximum={maximum} leafBinding={frame}/>
      <aside className="morphology-summary" data-selected-at={frame.at} aria-label="선택한 저장 시점">
        <span className="morphology-eyebrow">SELECTED MODEL TIME</span><h2><time dateTime={frame.at}>{frame.at.replace('T',' ').replace('Z',' UTC')}</time></h2>
        <dl><div><dt>추적 잎 면적 합계</dt><dd data-total-area={frame.tracked_leaf_area.value}>{frame.tracked_leaf_area.value.toFixed(6)} <small>m²</small></dd></div>
          <div><dt>{population?'그 시점의 선언 잎':'선언한 잎'}</dt><dd>{frame.tracked_leaf_count} <small>개</small></dd></div><div><dt>저장 시점</dt><dd>{index+1} <small>/ {data.frames.length}</small></dd></div></dl>
        <p>각 잎의 면적은 원 저장 계산값입니다. 제작한 단면 소엽 삼각형 면적에 대응합니다. 새 계산이나 중간값을 생성하지 않습니다.</p>
        <p>{population?'잎 수는 초기 목록과 입력에 명시한 출현 사건입니다.':'잎 수는 초기 입력의 선언입니다.'} 길이·폭·각도·소엽 수·잎자루/표면은 제작 가정이며 실제 품종 형태의 예측이 아닙니다.</p>
        <p>원 줄기 길이 합계 <strong>{frame.stem.tracked_axis_length.value.toFixed(6)} m</strong> · 실제 식물 키와 다릅니다.</p>
        <details><summary>원 입력과 저장 지문</summary><p className="morphology-hash">leaf artifact {data.artifact_sha256}<br/>leaf result {frame.result_sha256}<br/>stem artifact {frame.stem.artifact_sha256}</p>
          <p>합성 정규화·초기 면적과 모델/코드를 명시했습니다. 실제 Axiany 계수·초기 관측과 독립 농장 검증은 미확보입니다.</p>
          {!providedReplay&&<><a href={`${directory}/input.json`}>원 잎 입력</a> · <a href={`${directory}/root.json`}>모델·코드/상태 지문</a> ·
          <a href={`${directory}/stem-input.json`}>원 줄기 입력</a></>}</details>
      </aside></div>
    <section className="morphology-timeline" aria-label="저장 시점 재생"><div className="morphology-controls">
      <button onClick={()=>{if(!playing&&index===data.frames.length-1)setIndex(0);setPlaying(!playing);}}>{playing?'일시 정지':'저장 결과 재생'}</button>
      <button disabled={index===0} onClick={()=>select(0)}>처음</button><button disabled={index===0} onClick={()=>select(index-1)}>이전</button>
      <button disabled={index===data.frames.length-1} onClick={()=>select(index+1)}>다음</button><button disabled={index===data.frames.length-1} onClick={()=>select(data.frames.length-1)}>마지막</button>
      <span role="status">{playing?'원 저장 시점을 재생 중':'일시 정지'} · 새 계산 없음</span></div>
      <label>저장 시점<input type="range" min={0} max={data.frames.length-1} step={1} value={index} onChange={e=>select(Number(e.target.value))}/></label>
      <div className="morphology-range"><span>{data.frames[0]!.at}</span><span>합성 모델 시각 · 원 저장 시점</span><span>{data.frames.at(-1)!.at}</span></div></section>
    <div className="morphology-evidence"><section className="morphology-history" data-selected-at={frame.at} aria-label="저장 잎 면적 이력"><h2>추적 잎 면적 <small>m²</small></h2>
      <svg viewBox="0 0 640 160" role="img" aria-label={`${data.frames.length}개 원 저장 시점의 추적 잎 면적 합계`}>
        <line x1="25" y1="125" x2="615" y2="125" stroke="#c4ccb9"/>
        <polyline fill="none" stroke="#729361" strokeWidth="2" points={data.frames.map((f,i)=>`${x(i)},${y(f.tracked_leaf_area.value)}`).join(' ')}/>
        {data.frames.map((f,i)=><circle key={f.at} cx={x(i)} cy={y(f.tracked_leaf_area.value)} r={i===index?6:3} fill={i===index?'#224d33':'#93a884'}/>)}
        <text x="25" y="150">첫 저장 시점</text><text x="540" y="150">마지막 시점</text></svg>
      <p className="leaf-area-note">{population?'초기 잎과 입력에 명시한 새 잎만 추적합니다. 자동 출현 예측·적엽·노화·과실/숙기·수확은 포함하지 않습니다.':'초기부터 선언한 잎만 추적합니다. 새 잎 출현·적엽·노화·과실/숙기·수확은 이 결과에 포함하지 않습니다.'}</p></section>
      <section className="morphology-table leaf-area-table" data-selected-at={frame.at}><h2>같은 시점의 원 잎 면적</h2>
        <div className="morphology-table-scroll"><table><caption>{frame.at} · m² 단위 원 저장값</caption><thead><tr>
          <th scope="col">잎 ID</th><th scope="col">면적 (m²)</th><th scope="col">정확 열적 나이 (°C·day)</th></tr></thead>
          <tbody>{frame.leaves.map(leaf=><tr key={leaf.leaf_id} data-leaf-id={leaf.leaf_id} data-attachment-id={leaf.attachment_internode_id}>
            <th scope="row">{leaf.leaf_id}</th><td data-raw-area={leaf.area.value}>{String(leaf.area.value)}</td>
            <td data-age-exact={`${leaf.age_exact.numerator}/${leaf.age_exact.denominator}`}>{leaf.age_exact.numerator}/{leaf.age_exact.denominator}</td></tr>)}</tbody></table></div>
        <p className="leaf-area-note">시간 원점 {frame.time_origin_utc}. 원점 이후 정확 출현 초와 줄기 부착 ID는 원 파일에 보관합니다.</p>
      </section></div>
    {!embedded&&<footer className="morphology-footer">명시 합성 계산과 제작 외형의 연결입니다. 실제 측정 면적 정의/품종 형태·한 작기/탄소·자원·경제·자율 작물 선정과 독립 검증은 후속입니다. G0–G4는 미평가입니다.</footer>}
  </Container>;
}
