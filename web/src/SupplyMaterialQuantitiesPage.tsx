import {useEffect,useMemo,useState} from 'react';
import SupplyMaterialScene from './SupplyMaterialScene';
import {SupplyHistory,SupplyOrganTable,type SupplyHistoryPoint} from './SupplyReplayData';
import {MaterialQuantityRequest,type MaterialQuantityReplay} from './supplyMaterialQuantityReplay';
import {supplyMaterialPlantLayout} from './supplyMaterialPlantLayout';
import {readMaterialQuantitySelection,serializeMaterialQuantitySelection,materialQuantitySelectionURL,MATERIAL_QUANTITY_SELECTION_KEY,selectMaterialQuantityFrame,type MaterialQuantitySelection} from './supplyMaterialQuantitySelection';
import type {SupplyView} from './supplyMaterialSelection';
import SupplyMaterialQuantityPanel from './SupplyMaterialQuantityPanel';
import {object} from './storedLeafReplayIO';
import seedlingIcon from './supplyDesignIcons/seedling.svg';
import pauseIcon from './supplyDesignIcons/pause.svg';
import './SupplyMorphologyReplayPage.css';
import './SupplyMaterialQuantitiesPage.css';
const phaseNames:Record<string,string>={material_before:'새 기관 채택 직전',material_after:'새 기관 채택 직후',original_grid_endpoint:'재개된 확정 격자',declared_end:'선언 구간 종료'};
function saved(){try{return localStorage.getItem(MATERIAL_QUANTITY_SELECTION_KEY);}catch{return null;}}
export default function SupplyMaterialQuantitiesPage(){
 const [selection,setSelection]=useState(()=>readMaterialQuantitySelection(location.search,saved())),[data,setData]=useState<MaterialQuantityReplay|null>(null);
 const [error,setError]=useState(false),[retry,setRetry]=useState(0),[waiting,setWaiting]=useState(0),[playing,setPlaying]=useState(false);
 useEffect(()=>{
  const request=new MaterialQuantityRequest();let active=true;setData(null);setError(false);setWaiting(0);setPlaying(false);
  const timer=window.setInterval(()=>setWaiting(v=>v+1),1000);
  request.load().then(value=>{if(active){setData(value);clearInterval(timer);}},()=>{if(active){setError(true);clearInterval(timer);}});
  return()=>{active=false;request.cancel();clearInterval(timer);};
 },[retry]);
 useEffect(()=>{try{localStorage.setItem(MATERIAL_QUANTITY_SELECTION_KEY,serializeMaterialQuantitySelection(selection));}catch{}
  history.replaceState(null,'',materialQuantitySelectionURL(location.href,selection));
 },[selection]);
 useEffect(()=>{const pop=()=>{setPlaying(false);setSelection(readMaterialQuantitySelection(location.search,saved()));};addEventListener('popstate',pop);return()=>removeEventListener('popstate',pop);},[]);
 useEffect(()=>{
  if(!playing||!data)return;if(document.hidden){setPlaying(false);return;}
  const timer=window.setInterval(()=>setSelection(s=>({...s,index:Math.min(s.index+1,data.summary().frames-1)})),900);
  const hidden=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hidden);
  return()=>{clearInterval(timer);document.removeEventListener('visibilitychange',hidden);};
 },[playing,data]);
 useEffect(()=>{if(playing&&data&&selection.index===data.summary().frames-1)setPlaying(false);},[playing,data,selection.index]);
 const bound=useMemo(()=>data?.frame(selection.index),[data,selection.index]),frame=bound?.morphology,layout=useMemo(()=>frame?supplyMaterialPlantLayout(frame):null,[frame]);
 const points=useMemo<SupplyHistoryPoint[]>(()=>data?Array.from({length:data.summary().frames},(_,index)=>{const f=data.frame(index).morphology;return {index,phase:supplyMaterialPlantLayout(f).metadata.phase,
  area:f.leaves.reduce((a,l)=>a+l.geometry.value,0),length:f.internodes.reduce((a,n)=>a+n.geometry.value,0)};}):[],[data]);
 const quantityHistory=useMemo(()=>data?Array.from({length:data.summary().frames},(_,i)=>data.frame(i).quantities):[],[data]);
 const selectedWindow=useMemo(()=>data?.window(selection.first,selection.index),[data,selection.first,selection.index]);
 const summary=data?.summary(),terminal=summary?object(summary.terminal):null,at=layout?JSON.stringify(layout.metadata.at):'';
 const total=points[selection.index],count=summary?.frames??4;
 const select=(index:number)=>{setPlaying(false);setSelection(s=>selectMaterialQuantityFrame(s,index));};
 const change=(value:Partial<MaterialQuantitySelection>)=>{setPlaying(false);setSelection(s=>({...s,...value}));};
 const reload=()=>{setPlaying(false);setData(null);setError(false);setRetry(v=>v+1);};
 const play=()=>{if(!data)return;if(selection.index===count-1)select(0);setPlaying(v=>!v);};
 const controls=<div id="viewport-1-winner-playback" className="supply-playback">
  <div className="supply-transport"><button aria-label="이전 저장 시점" disabled={!data||selection.index===0} onClick={()=>select(selection.index-1)}>◀</button>
   <button aria-label={playing?'재생 일시 정지':'저장 결과 재생'} className="supply-primary" disabled={!data} onClick={play}>{playing?<img className="supply-icon supply-icon-light" src={pauseIcon} alt=""/>:'▶'}</button>
   <button aria-label="다음 저장 시점" disabled={!data||selection.index===count-1} onClick={()=>select(selection.index+1)}>▶|</button><span>{selection.index+1} / {count}</span></div>
  <label className="supply-slider"><span className="supply-sr">저장 시점</span><input aria-label="저장 시점" type="range" min="0" max={count-1} step="1" value={selection.index} disabled={!data} onChange={e=>select(Number(e.target.value))}/></label>
  <div className="supply-views" aria-label="3D 기관 보기">{([['connected','연결된 기관'],['unbound','미연결 초기 잎'],['all','모든 기관']]as [SupplyView,string][]).map(([view,label])=>
   <button key={view} aria-pressed={selection.view===view} onClick={()=>change({view})}>{label}</button>)}</div>
 </div>;
 return <main className="generated-screen supply-page" id="supply-material-quantities-app" data-selected-index={frame?selection.index:undefined} data-selected-at={at||undefined}
  data-artifact-sha256={summary?.artifact_sha256} onKeyDown={e=>{
   if(!data||e.target instanceof HTMLInputElement||e.target instanceof HTMLButtonElement||e.target instanceof HTMLSelectElement)return;
   if(e.key==='ArrowLeft'){e.preventDefault();select(Math.max(0,selection.index-1));}else if(e.key==='ArrowRight'){e.preventDefault();select(Math.min(count-1,selection.index+1));}
   else if(e.key===' '){e.preventDefault();play();}
  }}>
  <div className="ly-anchor-canvas"><div id="page-flow"><section id="viewport-1-winner">
   <header id="viewport-1-winner-header" className="supply-header"><div><p className="supply-eyebrow">OPENSMARTFARMSIM / 연구 재생 공간</p>
    <h1>새 잎·과실·자원 저장 3D</h1><p>같은 저장 시점의3D와 모형 과실·열·수분 전달량을 함께 확인합니다.</p></div>
    <div className="supply-header-right"><span id="viewport-1-winner-header-dataset" className="supply-badge"><img className="supply-icon" src={seedlingIcon} alt=""/> 자체 합성 QA · 4개 저장 시점</span>
     <nav aria-label="재생 메뉴"><button aria-current={selection.panel==='scene'?'page':undefined} onClick={()=>change({panel:'scene'})}>3D 재생</button><button aria-current={selection.panel==='data'?'page':undefined} onClick={()=>change({panel:'data'})}>원본 데이터</button></nav></div>
   </header>
   {!data&&<section className="supply-loading" role="status"><h2>{error?'저장 자료 확인 보류':'원본 저장 결과를 확인하고 있습니다'}</h2>
    <p>{error?'자료·권리·원본 지문을 확인할 수 없습니다. 이전 화면은 제거했습니다.':`파일·시각·기관·장부를 검증 중입니다. 대기 ${waiting}초`}</p>
    {error&&<button className="supply-primary" onClick={reload}>다시 확인</button>}</section>}
   {data&&frame&&layout&&summary&&<>
    {selection.panel==='scene'?<div id="viewport-1-winner-viewer" className="supply-viewer">
     <SupplyMaterialScene frame={frame} artifact={summary.artifact_sha256} mode={selection.view}/>
     <span className="supply-live">저장 상태 3D</span>
     <aside id="viewport-1-winner-viewer-inspector" className="supply-inspector" aria-label="선택한 저장 시점">
      <p>선택한 저장 시점 {selection.index+1}</p><strong>{phaseNames[layout.metadata.phase]}</strong>
      <p className="supply-time">원점 UTC {layout.metadata.at.time_origin_utc}<br/>정확 경과는 아래 증거에서 확인합니다.</p>
      <dl><div><dt>저장 잎 면적 합계</dt><dd data-raw-total-area={total?.area}>{total?.area.toFixed(6)} m²</dd></div>
       <div><dt>절간 길이 합계</dt><dd data-raw-total-length={total?.length}>{total?.length.toFixed(6)} m</dd></div>
       <div><dt>원 기관</dt><dd>{frame.leaves.length} 잎 · {frame.internodes.length} 절간</dd></div>
       <div><dt>부착 미지정 잎</dt><dd>{frame.leaves.filter(l=>l.parent_internode_id===null).length}개 · 별도 표시</dd></div>
       <div><dt>면적 0 잎</dt><dd>{frame.leaves.filter(l=>l.geometry.value===0).length}개 · 기관 존재 보존</dd></div>
       <div><dt>길이 0 절간</dt><dd>{frame.internodes.filter(n=>n.geometry.value===0).length}개</dd></div></dl>
      <p className="supply-note">새 잎의 초기 치수도 원 저장값입니다. 면적 0인 기관은 늘려 그리지 않습니다. 길이 합계는 실제 키가 아닙니다.</p>
     </aside>
    </div>:<section className="supply-detail" aria-label="현재 원본 데이터"><h2>같은 시점의 원본 기관</h2><SupplyOrganTable frame={frame} detailed/></section>}
    {controls}
    <p className="supply-play-status" role="status">{playing?'원 저장 순서로 재생 중':'일시 정지'} · 중간 상태 계산 없음 · 실제 시간 간격과 재생 간격은 다릅니다.</p>
    {bound&&selectedWindow&&<SupplyMaterialQuantityPanel frame={bound.quantities} history={quantityHistory} window={selectedWindow} select={select}
     first={first=>{if(Number.isSafeInteger(first)&&first>=0&&first<=selection.index){setPlaying(false);setSelection(s=>({...s,first}));}}}/>}
    <div id="viewport-1-winner-analytics" className="supply-analytics" data-selected-at={at}>
     <section id="viewport-1-winner-analytics-sources" className="supply-source-card"><h2>동일 시점의 원본 데이터</h2><SupplyOrganTable frame={frame}/></section>
     <SupplyHistory points={points} index={selection.index} select={select}/>
    </div>
    <details id="viewport-1-winner-logs" className="supply-evidence"><summary>원 시각·증거와 계산 보류 내역</summary>
     <p>원점 UTC <code>{layout.metadata.at.time_origin_utc}</code> · 정확 경과 <code data-exact-elapsed>{layout.metadata.at.elapsed_seconds_exact.numerator}/{layout.metadata.at.elapsed_seconds_exact.denominator}</code>초</p>
     <p>채택 전후는 같은 정확 시각의 별개 상태입니다. 원 단계 <code data-selected-phase>{layout.metadata.phase}</code> · G0–G4 미평가 · R2 미승인</p>
     <p>저장 계산 상태: {terminal?.status==='hold'?'보류 · 아래 원 사유까지의 확정 결과를 재생합니다.':'선언한 합성 저장 창 · 전체 작기는 미완료'} <code>{typeof terminal?.hold==='string'?terminal.hold:''}</code></p>
     <p className="supply-hash">원 결과 {summary.artifact_sha256}</p><a href="./supply-material-replay/own-public-v1/root.json">원 저장 지문</a> · <a href="./supply-material-quantities/own-public-v1/quantities.json">수량·자원 원본</a> · <a href={`./supply-material-replay/own-public-v1/frame-${selection.index}.json`}>선택한 원 상태</a> · <a href="./supply-material-replay/own-public-v1/NOTICE.txt">자료 권리</a>
     <details className="supply-ledgers"><summary>같은 시점의 수지 장부 · 원 정확값과 단위</summary><pre data-global-ledgers>{JSON.stringify(object(frame).global_ledgers,null,2)}</pre></details>
     <button onClick={reload}>원 자료 다시 확인</button>
    </details>
   </>}
   <footer className="supply-footer"><p>A·D 회전 / W·S 확대·축소 / R 카메라 초기화 · ← → 시점 이동 / Space 재생</p>
    <p>소프트웨어 검증용 합성 계산입니다. 실제 품종·한 작기·생산/수익·작물 추천 검증 전입니다. 잎 형태·방향·굵기·조명은 제작 외형입니다.</p>
    <a href="./licenses/three-MIT.txt">Three.js MIT</a> · <a href="./licenses/noto-sans-kr-OFL.txt">글꼴 OFL</a></footer>
  </section></div></div>
 </main>;
}
