import {useEffect,useState} from 'react';
import CompleteCropScene from './CompleteCropScene';
import {loadCompleteCropReplay,isCompleteCropScenario,type CompleteCropReplay,type CompleteCropScenario} from './completeCropReplay';
import {COMPLETE_CROP_FIXTURE as F} from './completeCropReplayFixture';
import {readCompleteCropLocation,completeCropURL} from './completeCropReplayLocation';
import {COMPLETE_CROP_POSE} from './completeCropPlant';
import './MorphologyReplayPage.css';
import './LeafAreaReplayPage.css';
import './CompleteCropReplayPage.css';

function caseName(s:CompleteCropScenario){return `${s.startsWith('initial')?'초기 출현':'추가 출현'} · 합성 사례 ${Number(s.split('-')[1])+1}`;}
export default function CompleteCropReplayPage(){
 const [selection,setSelection]=useState(()=>readCompleteCropLocation(window.location.search));
 const [loaded,setLoaded]=useState<{scenario:CompleteCropScenario;value:CompleteCropReplay}|null>(null);
 const [error,setError]=useState(false),[playing,setPlaying]=useState(false),[retry,setRetry]=useState(0),[waiting,setWaiting]=useState(0);
 const data=loaded?.scenario===selection.scenario?loaded.value:null,frame=data?.frames[selection.index];
 useEffect(()=>{
  const controller=new AbortController();let active=true;setLoaded(null);setError(false);setPlaying(false);setWaiting(0);
  const timer=window.setInterval(()=>setWaiting(n=>n+1),1000);
  loadCompleteCropReplay(selection.scenario,controller.signal).then(value=>{if(active){setLoaded({scenario:selection.scenario,value});clearInterval(timer);}},()=>{
   if(active){setError(true);clearInterval(timer);}
  });
  return()=>{active=false;controller.abort();clearInterval(timer);};
 },[selection.scenario,retry]);
 useEffect(()=>{const pop=()=>{setPlaying(false);setSelection(readCompleteCropLocation(window.location.search));};window.addEventListener('popstate',pop);return()=>window.removeEventListener('popstate',pop);},[]);
 useEffect(()=>{if(data){const url=completeCropURL(window.location.href,selection.scenario,selection.index);if(url)window.history.replaceState(null,'',url);}},[data,selection]);
 useEffect(()=>{if(playing&&data&&selection.index===data.frames.length-1)setPlaying(false);},[playing,data,selection.index]);
 useEffect(()=>{
  if(!playing||!data)return;if(document.hidden){setPlaying(false);return;}
  const timer=window.setInterval(()=>setSelection(v=>({...v,index:Math.min(v.index+1,data.frames.length-1)})),900);
  const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
  return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',hidden);};
 },[playing,data]);
 const select=(index:number)=>{setPlaying(false);setSelection(v=>({...v,index}));};
 const at=frame?JSON.stringify(frame.at):'',maximumArea=data?Math.max(...data.frames.map(f=>f.tracked_leaf_area.value)):1;
 const maximumLength=data?Math.max(...data.frames.map(f=>f.tracked_axis_length.value)):1;
 const plot=(field:'tracked_leaf_area'|'tracked_axis_length',maximum:number)=>data?.frames.map((f,i)=>`${25+i/Math.max(1,data.frames.length-1)*590},${125-f[field].value/maximum*105}`).join(' ');
 return <main className="morphology-page leaf-area-page complete-crop-page" data-selected-at={at||undefined} data-selected-index={frame?.index}
  data-artifact-sha256={data?.artifact_sha256} data-scenario={selection.scenario}>
  <header className="morphology-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR / STORED CROP REPLAY</span>
   <h1>저장된 잎과 줄기의 변화</h1><p>원 계산의 잎 출현·면적·절간 길이를 같은 시점의 3D와 표로 확인합니다.</p></div>
   <nav aria-label="연구 화면"><a href="./crop-appearance.html">제작 외형 보기 ↗</a></nav></header>
  <p className="morphology-scope">자체 합성 512초 계산 · 저장 결과 재생 · 실제 품종·한 작기·농장 검증 전 · 수확·수익·작물 추천 미제공</p>
  <div className="complete-crop-choice"><label>저장된 합성 사례 <select value={selection.scenario} onChange={e=>{
   const scenario=e.target.value;if(!isCompleteCropScenario(scenario))return;setPlaying(false);setSelection({scenario,index:0});
  }}>{Object.keys(F.scenarios).filter(isCompleteCropScenario).map(s=><option key={s} value={s}>{caseName(s)}</option>)}</select></label>
   <p>검사 자료의 줄기·잎 비율은 실제 식물과 다릅니다. 잎·줄기의 원 크기를 유지하며 중간 생장을 만들지 않습니다.</p></div>
  {!data||!frame?<section className="complete-crop-loading" role="status" aria-live="polite"><p>{error?
   '저장 결과 표시 보류: 원 파일·권리·무결성을 확인할 수 없습니다.':`원 파일·권리·무결성 검사 중 · 경과 ${waiting}초`}</p>
   <p>검증이 끝나면 같은 저장 상태의 3D·표·재생을 표시합니다.</p>{error&&<button onClick={()=>setRetry(n=>n+1)}>원 결과 다시 확인</button>}</section>:<>
   <div className="morphology-layout"><CompleteCropScene frame={frame} artifact={data.artifact_sha256}/>
    <aside className="morphology-summary" aria-label="선택한 저장 시점" data-selected-at={at}>
     <span className="morphology-eyebrow">SELECTED STORED STATE</span><h2>저장 시점 {frame.index+1} / {data.frames.length}</h2>
     <dl><div><dt>추적 잎 면적 합계</dt><dd data-raw-total-area={frame.tracked_leaf_area.value}>{frame.tracked_leaf_area.value.toFixed(6)} <small>m²</small></dd></div>
      <div><dt>추적 축 길이 합계</dt><dd data-raw-total-length={frame.tracked_axis_length.value}>{frame.tracked_axis_length.value.toFixed(6)} <small>m</small></dd></div>
      <div><dt>저장된 기관</dt><dd>{frame.leaves.length}<small> 잎 · </small>{frame.internodes.length}<small> 절간</small></dd></div></dl>
     <p>잎의 단면 삼각형 면적·절간 길이·부모 ID는 저장값입니다. 소엽 형태·잎의 방향·굵기·직선 축·조명은 제작 외형이며 과실은 표시하지 않습니다. 추적 축 길이는 실제 식물 키와 다릅니다.</p>
     <p>모델 원점 {frame.at.time_origin_utc}<br/>정확 경과 <span data-exact-elapsed>{frame.at.elapsed_seconds_exact.numerator}/{frame.at.elapsed_seconds_exact.denominator}</span>초<br/>
      원 단계 <span data-selected-phase>{frame.phase}</span> · {frame.checkpoint_sha256?'원 체크포인트':'CP 없는 원 후보'}</p>
     <details><summary>원 파일과 저장 지문</summary><p className="morphology-hash">결과 {data.artifact_sha256}<br/>체크포인트 {frame.checkpoint_sha256??'없음: 원 후보 상태'}<br/>제작 외형 {COMPLETE_CROP_POSE}</p>
      <a href={`./complete-crop-replay/${selection.scenario}/root.json`}>저장 지문</a> · <a href={`./complete-crop-replay/${selection.scenario}/frame-${frame.index}.json`}>현재 원 상태</a> ·
      <a href={`./complete-crop-replay/${selection.scenario}/NOTICE.txt`}>자료 권리</a></details>
    </aside></div>
   <section className="morphology-timeline" aria-label="저장 시점 재생"><div className="morphology-controls">
    <button onClick={()=>{if(!playing&&selection.index===data.frames.length-1)select(0);setPlaying(!playing);}}>{playing?'일시 정지':'저장 결과 재생'}</button>
    <button disabled={selection.index===0} onClick={()=>select(0)}>처음</button><button disabled={selection.index===0} onClick={()=>select(selection.index-1)}>이전</button>
    <button disabled={selection.index===data.frames.length-1} onClick={()=>select(selection.index+1)}>다음</button><button disabled={selection.index===data.frames.length-1} onClick={()=>select(data.frames.length-1)}>마지막</button>
    <span role="status">{playing?'원 저장 시점 재생 중':'일시 정지'} · {selection.index+1}/{data.frames.length} · 새 계산 없음</span></div>
    <label>저장 시점<input type="range" min="0" max={data.frames.length-1} step="1" value={selection.index} onChange={e=>select(Number(e.target.value))}/></label>
    <div className="morphology-range"><span>첫 저장 시점</span><span>원 저장 순서 · 실제 시간 간격은 다릅니다</span><span>마지막 저장 시점</span></div></section>
   <div className="morphology-evidence"><section className="morphology-history" aria-label="저장 면적과 길이 이력" data-selected-at={at}>
    {(['tracked_leaf_area','tracked_axis_length']as const).map(field=>{const max=field==='tracked_leaf_area'?maximumArea:maximumLength;return <div key={field}>
     <h2>{field==='tracked_leaf_area'?'추적 잎 면적':'추적 축 길이'} <small>{field==='tracked_leaf_area'?'m²':'m'}</small></h2>
     <svg viewBox="0 0 640 160" role="img" aria-label={field==='tracked_leaf_area'?'원 저장 순서의 잎 면적':'원 저장 순서의 축 길이'}>
      <line x1="25" y1="125" x2="615" y2="125" stroke="#c4ccb9"/><polyline fill="none" stroke="#729361" strokeWidth="2" points={plot(field,max)}/>
      {data.frames.map((f,i)=><circle key={i} data-index={i} data-stored-value={f[field].value} data-phase={f.phase} cx={25+i/Math.max(1,data.frames.length-1)*590} cy={125-f[field].value/max*105}
       r={i===selection.index?6:2} fill={i===selection.index?'#224d33':'#93a884'}><title>원 시점 {i+1} · {String(f[field].value)} {f[field].unit} · {f.phase}</title></circle>)}
      <text x="25" y="150">첫 저장 시점</text><text x="530" y="150">마지막 저장 시점</text></svg></div>;})}
    <p className="leaf-area-note">원 저장값과 0부터 시작하는 세로축입니다. 가로축은 등간격 저장 순서이며 시간 비례 축이 아닙니다. 새 중간 상태를 계산하지 않습니다.</p>
   </section><section className="morphology-table" aria-label="현재 기관 원 값" data-selected-at={at}>
    <h2>같은 시점의 잎</h2><div className="morphology-table-scroll"><table><caption>원 단위의 저장값 · 탄수화물은 재배면적 기준</caption>
     <thead><tr><th scope="col">잎 ID / 부모 절간 ID</th><th scope="col">면적 (m²)</th><th scope="col">탄수화물 (mg CH₂O/m²)</th><th scope="col">열적 나이 (°C·day)</th></tr></thead>
     <tbody>{frame.leaves.map(l=><tr key={l.leaf_id} data-leaf-id={l.leaf_id} data-parent-id={l.attachment_internode_id}>
      <th scope="row">{l.leaf_id}<br/><small>{l.attachment_internode_id}</small></th><td data-raw-area={l.area.value}>{String(l.area.value)}</td>
      <td data-raw-carbon={l.carbohydrate.value}>{String(l.carbohydrate.value)}</td><td data-raw-age={l.thermal_age.value}>{String(l.thermal_age.value)}</td></tr>)}</tbody></table></div>
    <h2>같은 시점의 절간</h2><div className="morphology-table-scroll"><table><caption>원 축 순서 · 저장 길이</caption><thead><tr><th scope="col">절간 ID</th><th scope="col">길이 (m)</th></tr></thead>
     <tbody>{frame.internodes.map(n=><tr key={n.internode_id} data-internode-id={n.internode_id}><th scope="row">{n.internode_id}</th><td data-raw-length={n.length.value}>{String(n.length.value)}</td></tr>)}</tbody></table></div>
   </section></div>
   <footer className="morphology-footer">소프트웨어 계약 확인용 자체 합성 계산입니다. 실제 품종의 형태·생산량·자원 구매·사업성·자율 작물 선정에는 독립 자료와 관문 검증이 필요합니다. G0–G4 미평가 · R2 미승인.</footer>
  </>}
 </main>;
}
