import { useEffect,useState } from 'react';
import MorphologyScene from './MorphologyScene';
import { loadMorphologyReplay,type MorphologyReplay } from './morphologyReplay';
import './MorphologyReplayPage.css';

export default function MorphologyReplayPage(){
  const [data,setData]=useState<MorphologyReplay|null>(null),[error,setError]=useState(false),[index,setIndex]=useState(0),[playing,setPlaying]=useState(false);
  useEffect(()=>{const controller=new AbortController();let active=true;
    loadMorphologyReplay(controller.signal).then(value=>{if(active)setData(value);},()=>{if(active)setError(true);});
    return()=>{active=false;controller.abort();};},[]);
  useEffect(()=>{
    if(!playing||!data)return;
    const timer=window.setInterval(()=>setIndex(value=>{if(value+1>=data.frames.length){setPlaying(false);return value;}return value+1;}),900);
    const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
    return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',hidden);};
  },[playing,data]);
  const select=(value:number)=>{setPlaying(false);setIndex(value);};
  if(!data)return <main className="morphology-page"><h1>저장된 줄기 생장</h1><p role="status">{error?
    '저장 결과 조회 보류: 원 파일·권리·무결성을 확인할 수 없습니다. 새 계산이나 대체 결과는 표시하지 않습니다.':'12개 저장 시점을 확인하고 있습니다.'}</p></main>;
  const frame=data.frames[index]!,maximum=Math.max(...data.frames.map(f=>f.tracked_axis_length.value));
  const x=(i:number)=>25+i/(data.frames.length-1)*590,y=(v:number)=>125-v/maximum*105;
  return <main className="morphology-page" data-selected-at={frame.at} data-selected-index={index}>
    <header className="morphology-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR / MORPHOLOGY STUDY</span>
      <h1>저장된 줄기 생장</h1><p>기온 → 기관 출현 → 절간 길이 → 같은 시점의 3D</p></div>
      <a href="./crop-appearance.html">성숙 토마토 외형 참고 ↗</a></header>
    <p className="morphology-scope">자체 합성 소프트웨어 검증 · 실제 품종·농장 검증 전 · 저장 결과 재생</p>
    <div className="morphology-layout"><MorphologyScene frame={frame} maximum={maximum}/>
      <aside className="morphology-summary" aria-label="선택한 저장 시점" data-selected-at={frame.at}>
        <span className="morphology-eyebrow">SELECTED MODEL TIME</span><h2><time dateTime={frame.at}>{frame.at.replace('T',' ').replace('Z',' UTC')}</time></h2>
        <dl><div><dt>추적 축 길이 합계</dt><dd data-raw-value={frame.tracked_axis_length.value}>{frame.tracked_axis_length.value.toFixed(6)} <small>m</small></dd></div>
          <div><dt>추적 절간</dt><dd>{frame.internodes.length} <small>개</small></dd></div><div><dt>저장 시점</dt><dd>{index+1} <small>/ {data.frames.length}</small></dd></div></dl>
        <p>줄기 길이와 마디 위치는 원 저장값을 사용합니다. 실제 식물의 키를 뜻하지 않습니다.</p>
        <p>고정된 복엽 3개·표면·줄기 반경은 제작 가정입니다. 잎 수·잎 면적·화방·과실·숙기·수확을 예측하지 않습니다.</p>
        <details><summary>입력과 계산 근거</summary><p className="morphology-hash">artifact {data.artifact_sha256}<br/>result {frame.result_sha256}</p>
          <p>Smoleňová et al. (2025), Eq.4 · 논문 CC BY 4.0. 계수는 자체 합성 fixture이며 품종 계수를 채택하지 않았습니다.</p>
          <a href="./morphology-replay/input.json">원 합성 입력</a> · <a href="./morphology-replay/root.json">모델·코드/상태 지문</a></details>
      </aside></div>
    <section className="morphology-timeline" aria-label="저장 시점 재생">
      <div className="morphology-controls"><button onClick={()=>{if(!playing&&index===data.frames.length-1)setIndex(0);setPlaying(!playing);}}>{playing?'일시 정지':'저장 결과 재생'}</button>
        <button disabled={index===0} onClick={()=>select(0)}>처음</button><button disabled={index===0} onClick={()=>select(index-1)}>이전</button>
        <button disabled={index===data.frames.length-1} onClick={()=>select(index+1)}>다음</button><button disabled={index===data.frames.length-1} onClick={()=>select(data.frames.length-1)}>마지막</button>
        <span role="status">{playing?'저장 시점을 순서대로 재생 중':'일시 정지'} · 새 계산 없음</span></div>
      <label>저장 시점 <input type="range" min={0} max={data.frames.length-1} step={1} value={index} onChange={event=>select(Number(event.target.value))}/></label>
      <div className="morphology-range"><span>{data.frames[0]!.at}</span><span>합성 모델 시각 · 2시간 간격</span><span>{data.frames.at(-1)!.at}</span></div>
    </section>
    <div className="morphology-evidence"><section className="morphology-history" data-selected-at={frame.at} aria-label="저장 축 길이 이력"><h2>추적 축 길이 <small>m</small></h2>
      <svg viewBox="0 0 640 160" role="img" aria-label="12개 원 저장 시점의 축 길이. 선택 시점은 진한 점으로 표시합니다.">
        <line x1="25" y1="125" x2="615" y2="125" stroke="#c4ccb9"/><polyline fill="none" stroke="#729361" strokeWidth="2" points={data.frames.map((f,i)=>`${x(i)},${y(f.tracked_axis_length.value)}`).join(' ')}/>
        {data.frames.map((f,i)=><circle key={f.at} cx={x(i)} cy={y(f.tracked_axis_length.value)} r={i===index?6:3} fill={i===index?'#224d33':'#93a884'}/>)}
        <text x="25" y="150">첫 저장 시점</text><text x="540" y="150">마지막 시점</text>
      </svg></section>
      <section className="morphology-table" data-selected-at={frame.at}><h2>같은 시점의 원 절간 길이</h2><div className="morphology-table-scroll"><table><caption>{frame.at} · 값은 미터 단위 원 저장값입니다.</caption>
        <thead><tr><th scope="col">순번</th><th scope="col">절간 길이 (m)</th><th scope="col">출현 UTC</th></tr></thead>
        <tbody>{frame.internodes.map(n=><tr key={n.internode_id} data-internode-id={n.internode_id}><th scope="row">{n.sequence}</th><td data-raw-value={n.length.value}>{String(n.length.value)}</td><td>{n.emerged_at}</td></tr>)}</tbody>
      </table></div></section></div>
    <footer className="morphology-footer">연구용 형태 연결입니다. 지역 선택·자율 작물 선정·생산량/자원·경제 통합과 독립 검증은 후속입니다. G0–G4는 미평가입니다.</footer>
  </main>;
}
