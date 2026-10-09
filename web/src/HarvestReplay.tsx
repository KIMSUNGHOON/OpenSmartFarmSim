import { useEffect,useMemo,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import { validHarvestLookup,type HarvestSummaryResponse,type HarvestPageResponse } from './harvestReplay';
import { type CalculationCycleCropSummaryResponse,type CalculationCycleCropPageResponse } from './calculationCycleCropReplay';
import { bindHarvestGrowthWindow } from './harvestGrowthBinding';
import './HarvestReplay.css';

type Props=Readonly<{api:ReturnType<typeof createApi>|null;parent:CalculationCycleCropSummaryResponse|null;
  samplePage:CalculationCycleCropPageResponse|null;selectedAt:string|null;
  selectSample:(globalIndex:number)=>void;invalidate:(error:ApiError)=>void;initialResultId?:string}>;
type Visible=Readonly<{api:Props['api'];parent:Props['parent'];id:string;selectionId:string|null;phase:'loading'|'ready'|'error';
  summary:HarvestSummaryResponse|null;page:HarvestPageResponse|null;error:ApiError|null}>;
const LIMIT=3;
const PURPOSE={harvest:'수확',thinning:'솎기',disposal:'폐기',sampling:'표본',unassigned:'미배정'};
const KIND={model_terminal_outflow:'모델 말단 유출',explicit_fruit_removal:'명시 제거'};
function Amount({q,original=false,unassigned=false}:{q:{value:number;unit:string};original?:boolean;unassigned?:boolean}){
  return <span data-original-fresh={original?'':undefined} data-unassigned-fresh={unassigned?'':undefined}
    data-raw-value={q.value} data-unit={q.unit}>{String(q.value)}<small>{q.unit}</small></span>;
}

export default function HarvestReplay(props:Props){
  const {api,parent,samplePage,selectedAt,selectSample,invalidate}=props,selectionId=props.initialResultId??null;
  const [id,setId]=useState(''),[visible,setVisible]=useState<Visible|null>(null);
  const [autoLoad,setAutoLoad]=useState<Readonly<{api:Props['api'];parent:Props['parent'];id:string}>|null>(null);
  const live=useRef({api,parent,id,selectionId,invalidate});live.current={api,parent,id,selectionId,invalidate};
  const generation=useRef(0),controller=useRef<AbortController|null>(null),pending=useRef<Promise<void>>(Promise.resolve());
  const state=visible?.api===api&&visible.parent===parent&&visible.id===id&&visible.selectionId===selectionId?visible:null;
  function cancel(){generation.current++;controller.current?.abort();controller.current=null;setVisible(null);setAutoLoad(null);}
  useEffect(()=>{cancel();setId(selectionId??'');
    if(api&&parent&&selectionId)setAutoLoad({api,parent,id:selectionId});
    return()=>{generation.current++;controller.current?.abort();};
  },[api,parent,selectionId]);
  useEffect(()=>{if(autoLoad?.api===api&&autoLoad?.parent===parent&&autoLoad?.id===id)load();},[autoLoad,api,parent,id]);
  const binding=useMemo(()=>{
    if(!parent||state?.phase!=='ready'||!state.summary||!state.page)return null;
    try{return bindHarvestGrowthWindow({crop_summary:parent,sample_page:samplePage,
      harvest_summary:state.summary,harvest_page:state.page});}catch{return null;}
  },[parent,samplePage,state]);
  useEffect(()=>{if(state?.phase==='ready'&&!binding){cancel();invalidate(new ApiError('response_rejected'));}},[state,binding,invalidate]);
  function load(offset=0,baseline:HarvestSummaryResponse|null=null){
    if(!api||!parent)return;
    const lookup={...parent.farm,result_id:id};cancel();
    if(!validHarvestLookup(lookup)){
      setVisible({api,parent,id,selectionId,phase:'error',summary:null,page:null,error:new ApiError('invalid_request')});return;
    }
    const client=api,crop=parent,version=++generation.current,owned=new AbortController();controller.current=owned;
    const current=()=>generation.current===version&&!owned.signal.aborted&&live.current.api===client
      &&live.current.parent===crop&&live.current.id===lookup.result_id&&live.current.selectionId===selectionId;
    const prior=pending.current;
    setVisible({api:client,parent:crop,id:lookup.result_id,selectionId,phase:'loading',summary:null,page:null,error:null});
    pending.current=prior.catch(()=>{}).then(async()=>{
      if(!current())return;
      try{
        const summary=baseline??await client.harvestSummary(lookup,owned.signal);if(!current())return;
        const page=await client.harvestPage(lookup,{offset,limit:LIMIT},{signal:owned.signal,summary});if(!current())return;
        bindHarvestGrowthWindow({crop_summary:crop,sample_page:null,harvest_summary:summary,harvest_page:page});
        setVisible({api:client,parent:crop,id:lookup.result_id,selectionId,phase:'ready',summary,page,error:null});
      }catch(error){
        if(current()){
          const failure=error instanceof ApiError?error:new ApiError('network_unresolved');
          setVisible({api:client,parent:crop,id:lookup.result_id,selectionId,phase:'error',summary:null,page:null,error:failure});
          live.current.invalidate(failure);
        }
      }finally{if(version===generation.current)controller.current=null;}
    });
  }
  function submit(event:FormEvent){event.preventDefault();load();}
  if(!api||!parent)return null;
  const busy=state?.phase==='loading',range=binding?.harvest_range;
  return <section id="crop-harvest" className="panel harvest-replay" aria-label="저장 제거·배정" aria-busy={busy}
    data-phase={state?.phase??'idle'} data-selected-at={selectedAt??''} data-result-id={state?.summary?.result_id??''}
    data-offset={range?.offset??''} data-count={range?.count??0} data-total={range?.total??''}>
    <header className="harvest-header"><div><h2>저장 제거·배정</h2><div className="harvest-badges">
      <span>합성 환산</span><span>관문 미평가</span>{parent.reference.status==='hold'&&<span>확인된 과거 · 계산 보류</span>}
    </div></div><p>현재 선택 UTC <strong>{selectedAt??'선택 없음'}</strong></p></header>
    <p className="crop-caption">명시 가정에 따른 연구용 배정입니다. 실제 품종의 생과 수확·숙기·판매량으로 검증되지 않았습니다.</p>
    <details className="harvest-lookup" open={!binding}><summary>저장 수확 결과 조회</summary>
      <form onSubmit={submit}><label>저장 수확 결과 ID<input value={id} maxLength={128} required spellCheck={false} autoComplete="off"
        onChange={e=>{cancel();setId(e.target.value);}}/></label><button className="button primary" disabled={busy}>저장 수확 조회</button></form>
    </details>
    {state?.error&&<p role="alert" className="notice error">저장 수확 결과 ID를 확인해 주세요.</p>}
    {busy&&<div role="status" className="harvest-loading"><p>현재 권리와 저장 수확 범위를 확인합니다…</p>
      <button className="button secondary" onClick={cancel}>수확 조회 취소</button></div>}
    {binding&&range&&<>
      <div className="harvest-range"><h3>현재 읽은 제거 행</h3><p><strong>{range.partial?'부분 범위':'전체 저장 범위'}</strong> ·
        현재 {range.count?`${range.offset+1}–${range.offset+range.count}`:'0'} / 전체 저장 {range.total}행</p></div>
      <div className="crop-table-scroll harvest-table-scroll" tabIndex={0} role="region" aria-label="저장 제거·배정 수치">
        <table className="harvest-table"><caption>현재 읽은 원 행만 표시합니다. 표를 가로로 스크롤하면 모든 열을 확인할 수 있습니다.
          수량의 바닥 면적 기준과 정확 분수는 원 기록을 유지합니다.</caption>
          <thead><tr><th scope="col">구간 / 사건 UTC</th><th scope="col">제거 유형</th><th scope="col">배정 목적</th>
            <th scope="col">원 생과 환산량</th><th scope="col">미배정</th><th scope="col">같은 UTC 저장 생장</th></tr></thead>
          <tbody>{binding.rows.map(({index,row,at,frame,frame_status,interval})=><tr key={row.row_id} data-harvest-index={index}
            data-end-at={at} data-frame-status={frame_status} aria-selected={at===selectedAt}>
            <th scope="row"><time>{row.mass.removal.start_at}</time>{row.mass.removal.start_at!==at&&<><br/>→ <time>{at}</time></>}</th>
            <td>{KIND[row.mass.removal.kind]}<details><summary>원 수량·정확 분수</summary><pre>{JSON.stringify({
              carbohydrate:row.mass.removal.carbohydrate,number:row.mass.removal.number,dry_matter:row.mass.dry_matter,
              fresh_matter:row.mass.fresh_matter,allocations:row.allocations,unassigned:row.unassigned},null,2)}</pre></details></td>
            <td><ul>{row.allocations.map(allocation=><li key={allocation.assignment_id}><strong>{PURPOSE[allocation.purpose]}</strong>
              <Amount q={allocation.quantities.fresh_matter}/></li>)}</ul>{!row.allocations.length&&'배정 없음'}</td>
            <td><Amount q={row.mass.fresh_matter} original/></td><td><Amount q={row.unassigned.quantities.fresh_matter} unassigned/></td>
            <td><button className="button secondary" disabled={!frame} onClick={()=>{if(frame)selectSample(frame.index);}}>생장 시점 보기</button>
              {!frame&&<p>현재 생장 범위에 대응 시점 없음</p>}{interval&&<small>구간 끝의 저장 상태. 제거 직전 상태를 뜻하지 않습니다.</small>}</td>
          </tr>)}</tbody></table></div>
      {!range.count&&<p>현재 범위의 저장 제거 행이 없습니다.</p>}
      <details className="harvest-whole"><summary>전체 저장 배정 합계</summary><div data-whole-summary data-row-count={binding.entire_stored_harvest_summary.row_count}>
        <p>현재 표와 별개인 전체 확정 과거 {binding.entire_stored_harvest_summary.row_count}행의 저장 합계입니다.</p>
        {(Object.keys(KIND) as (keyof typeof KIND)[]).map(kind=><div key={kind}><h3>{KIND[kind]}</h3><dl>
          {(Object.keys(PURPOSE) as (keyof typeof PURPOSE)[]).map(purpose=><div key={purpose}><dt>{PURPOSE[purpose]}</dt><dd>
            <Amount q={binding.entire_stored_harvest_summary.totals_by_kind_and_purpose[kind][purpose].quantities.fresh_matter}/>
          </dd></div>)}</dl></div>)}</div></details>
      <details className="harvest-comparisons"><summary>합성 관측 비교</summary>
        {binding.entire_stored_harvest_summary.observation_comparisons.map(comparison=><article key={comparison.observation.observation_id}
          data-comparison-status={comparison.status}><h3>{comparison.observation.start_at} → {comparison.observation.end_at} UTC</h3>
          <p>{comparison.status==='compared_synthetic_fixture'?'합성 fixture 대조 · 현장 검증 아님':'선택 범위 미완료 · 비교 보류'}</p><dl>
            <div><dt>가정 관측값</dt><dd><Amount q={comparison.observation.fresh_matter}/></dd></div>
            <div><dt>모델 배정값</dt><dd>{comparison.modeled_fresh_matter?<Amount q={comparison.modeled_fresh_matter}/>:'보류'}</dd></div>
            <div><dt>관측값 − 모델 배정값</dt><dd>{comparison.observed_minus_modeled?<Amount q={comparison.observed_minus_modeled}/>:'보류'}</dd></div>
          </dl></article>)}{!binding.entire_stored_harvest_summary.observation_comparisons.length&&<p>저장된 비교가 없습니다.</p>}
      </details>
      <nav className="harvest-controls" aria-label="수확 저장 범위"><button className="button secondary" disabled={range.offset===0}
        onClick={()=>load(Math.max(0,range.offset-LIMIT),state!.summary)}>이전 수확 범위</button>
        <button className="button secondary" onClick={()=>load()}>수확 권리 다시 조회</button>
        <button className="button primary" disabled={state!.page!.page.next_offset===null}
          onClick={()=>{const offset=state!.page!.page.next_offset;if(offset!==null)load(offset,state!.summary);}}>다음 수확 범위</button></nav>
      <p className="crop-caption">현재 범위의 정확히 같은 UTC만 기존 3D로 이동합니다. 이미 받은 화면의 권리를 계속 감시하는 기능은 아닙니다.</p>
      <details className="harvest-evidence"><summary>상세 정보 · 내부 ID / 원문 증거</summary><pre>{JSON.stringify({
        result_id:state!.summary!.result_id,farm:parent.farm,reference:state!.summary!.reference,
        allocation:state!.summary!.summary.allocation_parameters},null,2)}</pre></details>
    </>}
  </section>;
}
