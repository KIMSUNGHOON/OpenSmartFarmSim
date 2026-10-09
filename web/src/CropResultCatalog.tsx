import {useEffect,useMemo,useRef,useState} from 'react';
import type {createApi} from './api';
import {createCropResultPicker,emptyCropResultPicker,type CropResultPickerState} from './cropResultPicker';
import SelectedCropReplay from './SelectedCropReplay';
import './CropResultCatalog.css';

type Api=ReturnType<typeof createApi>;type Picker=ReturnType<typeof createCropResultPicker>;
const emptyImage=new URL('./assets/crop-result-empty.png',import.meta.url).href;
const errors:Record<string,string>={auth_required:'계정 연결을 다시 설정해주세요.',
  access_denied:'현재 계정의 열람 권한을 확인할 수 없어 이전 목록과 결과를 지웠습니다.',
  not_available:'현재 계정에서 이 등록 또는 저장 결과를 찾을 수 없습니다.',
  response_rejected:'등록 판본과 서버 응답의 연결을 확인할 수 없어 표시를 보류했습니다.'};
const utc=(value:string)=>value.replace('T',' ').replace(/Z$/,'');

export default function CropResultCatalog({api,onCreateFarm}:{api:Api|null;onCreateFarm?:()=>void}){
  const owner=useMemo(()=>({api}),[api]),current=useRef<Picker|null>(null);
  const [visible,setVisible]=useState<{owner:typeof owner;state:CropResultPickerState}|null>(null);
  const farmSelect=useRef<HTMLSelectElement|null>(null);
  useEffect(()=>{
    const picker=createCropResultPicker(owner.api,state=>setVisible({owner,state}));current.current=picker;
    setVisible({owner,state:picker.snapshot()});
    return()=>{picker.dispose();if(current.current===picker)current.current=null;};
  },[owner]);
  const initialized=visible?.owner===owner,state=initialized?visible.state:emptyCropResultPicker();
  const busy=state.phase==='loading',disabled=!api||!initialized||busy,page=state.page;
  function act(action:(picker:Picker)=>void|Promise<void>){
    const picker=current.current;
    if(!api||!initialized||!picker||picker.snapshot().phase==='loading')return;
    void action(picker);
  }
  return <div className="crop-result-catalog" aria-busy={busy} data-picker-phase={state.phase}>
    <p className="catalog-scope">저장 결과 조회 · 실시간 계산 미연동 <span>합성 시험 · 생산 예측 보류</span></p>
    <div className="catalog-toolbar">
      <button className="button secondary" disabled={disabled} onClick={()=>act(p=>p.refreshFarms())}>
        {state.farms?'농장 목록 새로고침':'농장 목록 조회'}</button>
      {busy&&<button className="button secondary" onClick={()=>current.current?.cancel()}>조회 취소</button>}
      {!api&&<p>내부 시험 연결에서 계정을 연결한 뒤 저장 결과를 조회하세요.</p>}
    </div>
    {busy&&<p role="status">{state.work==='farms'?'현재 계정의 농장 목록을 읽습니다…':
      state.work==='crops'?'선택한 농장 판본과 등록 작물을 확인합니다…':'선택한 작물의 저장 결과 목록을 읽습니다…'}</p>}
    {state.error&&<p role="alert" className="notice error">{errors[state.error.code]??'조회를 완료하지 못했습니다. 농장 목록부터 다시 확인해주세요.'}</p>}
    <div className="catalog-filters">
      <section className="catalog-filter"><h2>농장 선택</h2>
        <label className="catalog-label">등록된 농장 판본<select ref={farmSelect} disabled={disabled||!state.farms?.items.length}
          value={state.farm?.intent_job.job_id??''} onChange={e=>act(p=>p.chooseFarm(e.target.value))}>
          <option value="" disabled>농장 판본을 선택하세요</option>
          {state.farms?.items.map(farm=><option key={farm.intent_job.job_id} value={farm.intent_job.job_id}>
            {farm.scenario_id} · 수정본 {farm.scenario_revision}</option>)}</select></label>
        {state.farms&&<div className="catalog-pages" aria-label="농장 목록 페이지">
          <span>이번 페이지 {state.farms.items.length}개 · {state.farm_page+1}번째 페이지</span>
          <button className="button secondary" disabled={disabled||state.farm_page===0} onClick={()=>act(p=>p.previousFarms())}>농장 이전 페이지</button>
          <button className="button secondary" disabled={disabled||!state.farms.next_cursor} onClick={()=>act(p=>p.nextFarms())}>농장 다음 페이지</button>
        </div>}
        {state.farms?.items.length===0&&<p>이 페이지에 등록된 농장이 없습니다.
          {onCreateFarm&&<button className="button secondary" onClick={onCreateFarm}>작성 농장 화면 열기</button>}</p>}
      </section>
      <section className="catalog-filter"><h2>작물 선택</h2>
        <label className="catalog-label">등록된 작물과 재배 기간<select disabled={disabled||!state.crops?.items.length}
          value={state.crop?.crop_id??''} onChange={e=>act(p=>p.chooseCrop(e.target.value))}>
          <option value="" disabled>농장 확인 후 작물을 선택하세요</option>
          {state.crops?.items.map(crop=><option key={crop.crop_id} value={crop.crop_id}>
            {crop.species} · {crop.variety} · {crop.occupancy.start.slice(0,10)} → {crop.occupancy.end.slice(0,10)} · {crop.batch_id}</option>)}</select></label>
        {state.crops&&<p className="catalog-hint">사용자가 등록한 재배 의도입니다. 실제 품종 모델과 계수는 미검증입니다.</p>}
        {state.crops?.items.length===0&&<p>이 농장 판본에 등록된 작물이 없습니다.</p>}
      </section>
    </div>
    <fieldset className="catalog-kinds"><legend>저장 결과 종류</legend>
      <button disabled={disabled} aria-pressed={state.kind==='calculation_cycle_v1'} onClick={()=>act(p=>p.setKind('calculation_cycle_v1'))}>생장 계산</button>
      <button disabled={disabled} aria-pressed={state.kind==='harvest_v1'} onClick={()=>act(p=>p.setKind('harvest_v1'))}>수확 배정</button>
    </fieldset>
    <section className="catalog-results" aria-labelledby="crop-catalog-heading">
      <div className="catalog-list-heading"><h2 id="crop-catalog-heading">저장된 연구 결과 목록</h2>
        <button className="button secondary" disabled={disabled||!state.crop} onClick={()=>act(p=>p.refreshResults())}>결과 목록 새로고침</button></div>
      {!page&&!busy&&<p className="catalog-hint">농장 판본과 작물을 선택하면 현재 열람 가능한 저장 결과를 찾습니다.</p>}
      {page?.items.length===0&&<div className="catalog-empty" role="status">
        <img src={emptyImage} alt=""/><h3>저장된 연구 결과가 없습니다</h3>
        <p>선택한 농장·작물·결과 종류의 현재 페이지에 저장된 결과가 없습니다.</p>
        <div><button className="button" disabled={disabled} onClick={()=>act(p=>p.refreshResults())}>목록 새로고침</button>
          <button className="button secondary" onClick={()=>farmSelect.current?.focus()}>선택 조건 변경</button></div>
      </div>}
      {page&&page.items.length>0&&<div className="catalog-table-scroll" tabIndex={0} role="region" aria-label="저장 결과 표, 좁은 화면에서는 가로로 이동">
        <table><caption>{page.kind==='calculation_cycle_v1'?'생장 계산':'수확 배정'} · 현재 페이지 {page.items.length}건</caption>
          <thead><tr><th scope="col">저장 시각 (UTC)</th><th scope="col">기간 / 연결</th><th scope="col">계산 상태</th>
            <th scope="col">{page.kind==='calculation_cycle_v1'?'저장 시점 수':'배정 행 수'}</th><th scope="col">열기</th></tr></thead>
          <tbody>{page.kind==='calculation_cycle_v1'?page.items.map(item=><tr key={item.result_id} aria-selected={state.selection?.result_id===item.result_id}>
            <td><time dateTime={item.recorded_at}>{utc(item.recorded_at)}</time></td>
            <td>{utc(item.period.start)}<br/>→ {utc(item.period.end)}</td>
            <td><span className={'catalog-status '+item.calculation_status}>{item.calculation_status==='completed'?'계산 완료':'계산 보류'}</span></td>
            <td>{item.sample_count.toLocaleString('ko-KR')}</td><td><button className="button secondary" disabled={disabled}
              aria-label={utc(item.recorded_at)+' 생장 결과 열기'} onClick={()=>act(p=>p.select(item.result_id))}>결과 열기</button></td>
          </tr>):page.items.map(item=><tr key={item.result_id} aria-selected={state.selection?.result_id===item.result_id}>
            <td><time dateTime={item.recorded_at}>{utc(item.recorded_at)}</time></td><td>같은 저장 생장 부모</td>
            <td><span className={'catalog-status '+item.calculation_status}>{item.calculation_status==='completed'?'계산 완료':'계산 보류'}</span></td>
            <td>{item.row_count.toLocaleString('ko-KR')}</td><td><button className="button secondary" disabled={disabled}
              aria-label={utc(item.recorded_at)+' 수확 결과 열기'} onClick={()=>act(p=>p.select(item.result_id))}>결과 열기</button></td>
          </tr>)}</tbody></table></div>}
      {page&&<div className="catalog-pages" aria-label="결과 목록 페이지"><span>현재 페이지 {page.items.length}건 · {state.result_page+1}번째 페이지</span>
        <button className="button secondary" disabled={disabled||state.result_page===0} onClick={()=>act(p=>p.previousResults())}>결과 이전 페이지</button>
        <button className="button secondary" disabled={disabled||!page.next_cursor} onClick={()=>act(p=>p.nextResults())}>결과 다음 페이지</button></div>}
      <aside className="catalog-notice"><strong>선택한 저장 결과를 기존 3D 화면에서 엽니다</strong>
        <p>열 때 원 결과와 현재 권리를 다시 확인합니다. 계산 완료는 품종 검증이나 생산 예측 승인을 뜻하지 않습니다.</p></aside>
    </section>
    {state.selection&&<section className="catalog-replay" aria-label="선택한 저장 결과 재생"><SelectedCropReplay api={api} selection={state.selection}/></section>}
  </div>;
}
