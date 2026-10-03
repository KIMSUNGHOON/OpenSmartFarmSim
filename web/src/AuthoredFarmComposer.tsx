import { useEffect,useId,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import type { AuthoredFarmRequest,AuthoredFarmSummary } from './authored-farm-api';
import { buildFarmAuthoringRequest,FarmDraftError,type FarmDraft,type Row } from './farm-authoring-input';
import SourceFarmSelector from './SourceFarmSelector';
import { farmReferenceFields,type FarmEconomicSelection } from './source-farm-api';

type Api=ReturnType<typeof createApi>;
type FieldSpec={key:string;label:string;help?:string};
const references:FieldSpec[]=[
  {key:'scenario_id',label:'새 농장 시나리오 ID'},
  {key:'scenario_revision',label:'새 농장 판본'},
  {key:'research_job_id',label:'완료된 조사 작업 UUID'},
  {key:'snapshot_id',label:'원본 열 스냅샷 ID'},
  {key:'decision_context_id',label:'서명된 결정 문맥 ID'},
  {key:'decision_at',label:'결정 시각 · UTC',help:'YYYY-MM-DDTHH:mm:ssZ · 소수점 여섯 자리까지 보존'},
  {key:'market_hold_report_id',label:'시장 자료 보류 보고서 ID'},
  {key:'period_start',label:'평가 시작일 · KST',help:'YYYY-MM-DD'},
  {key:'period_end',label:'평가 종료일 · KST',help:'YYYY-MM-DD'},
  {key:'economic_scenario_id',label:'경제 시나리오 ID'},
  {key:'economic_revision',label:'경제 판본'},
  {key:'economic_sha256',label:'경제 입력 SHA-256'},
  {key:'economic_candidate_id',label:'경제 후보 SHA-256'},
];
const facility:FieldSpec[]=[
  {key:'zone_id',label:'온실 구역 ID'},
  {key:'floor_area',label:'온실 바닥 면적 · m²'},
  {key:'cultivable_area',label:'재배 가능 면적 · m²'},
  {key:'indoor_volume',label:'실내 부피 · m³'},
  {key:'effective_heat_capacity',label:'유효 열용량 · J/K',help:'온실 내부의 온도 변화에 필요한 열량입니다. 근거 없이 추정하지 마세요.'},
  {key:'dry_air_mass',label:'건조 공기 질량 · kg_da'},
  {key:'envelope_conductance',label:'외피 열전달 계수 · W/K'},
  {key:'absorbed_solar_fraction',label:'흡수 일사 비율 · 0~1'},
  {key:'initial_temperature',label:'초기 온도 · K',help:'절대온도입니다. 섭씨 온도를 그대로 입력하면 안 됩니다.'},
  {key:'initial_humidity_ratio',label:'초기 절대습도 · kg_v/kg_da'},
  {key:'heater_capacity',label:'공급 가능한 난방열 · W_th',help:'연료·전기 구매량이 아닙니다.'},
  {key:'heater_setpoint',label:'난방 설정온도 · K'},
];
const forcingFields:FieldSpec[]=[
  {key:'start',label:'구간 시작 · UTC'},{key:'end',label:'구간 종료 · UTC'},
  {key:'ventilation',label:'환기 건조공기 유량 · kg_da/s'},
  {key:'canopy',label:'작물 증발 수증기 · kg_v/s'},
  {key:'ground',label:'지중 열류 · W (유입 + / 유출 −)'},
];
const cropFields:FieldSpec[]=[
  {key:'crop_id',label:'작물 의도 ID'},{key:'batch_id',label:'경제 원장의 배치 ID'},
  {key:'species',label:'작물명'},{key:'variety',label:'품종명'},
  {key:'area',label:'점유 면적 · m²'},
  {key:'occupancy_start',label:'재배 점유 시작 · UTC'},
  {key:'occupancy_end',label:'재배 점유 종료 · UTC'},
  {key:'release_at',label:'정리 완료 · UTC'},
  {key:'harvest_start',label:'수확 예상 시작 · UTC'},
  {key:'harvest_end',label:'수확 예상 종료 · UTC'},
  {key:'sales_start',label:'판매 예상 시작 · UTC'},
  {key:'sales_end',label:'판매 예상 종료 · UTC'},
  {key:'collection_start',label:'수금 예상 시작 · UTC'},
  {key:'collection_end',label:'수금 예상 종료 · UTC'},
  {key:'grades',label:'경제 원장의 등급 ID · 쉼표 구분'},
  {key:'channels',label:'판매 경로 ID · 쉼표 구분'},
];

function TextField({spec,value,onChange,disabled,readOnly=false}:{spec:FieldSpec;value:string;
  onChange:(value:string)=>void;disabled:boolean;readOnly?:boolean}) {
  return <label className="authored-field">{spec.label}
    <input name={spec.key} value={value} onChange={event=>onChange(event.target.value)}
      maxLength={spec.key==='grades'||spec.key==='channels'?2000:200}
      disabled={disabled} readOnly={readOnly} autoComplete="off" spellCheck={false}/>
    {spec.help && <small>{spec.help}</small>}
  </label>;
}
function SelectField({name,label,value,onChange,options,disabled}:{name:string;label:string;value:string;
  onChange:(value:string)=>void;options:[string,string][];disabled:boolean}) {
  return <label className="authored-field">{label}<select name={name} value={value}
    onChange={event=>onChange(event.target.value)} disabled={disabled}>
    <option value="">선택해 주세요</option>{options.map(([id,name])=><option key={id} value={id}>{name}</option>)}
  </select></label>;
}

export default function AuthoredFarmComposer({api,onRegistered,onPending}:{api:Api|null;
  onRegistered:(summary:AuthoredFarmSummary)=>void;onPending?:(pending:boolean)=>void}) {
  const sectionId=useId();
  const [draft,setDraft]=useState<FarmDraft>({fields:{},forcing:[{}],crops:[],rightsConfirmed:false});
  const [preview,setPreview]=useState<AuthoredFarmRequest|null>(null);
  const [uncertain,setUncertain]=useState(false);
  const [busy,setBusy]=useState(false);
  const [error,setError]=useState<string|null>(null);
  const [referenceMode,setReferenceMode]=useState<'saved'|'manual'>('saved');
  const [selected,setSelected]=useState(false);
  const alive=useRef(true);
  useEffect(()=>{alive.current=true;return ()=>{alive.current=false;};},[]);
  const locked=busy||uncertain;
  useEffect(()=>{onPending?.(locked);return()=>onPending?.(false);},[locked,onPending]);
  const ready=referenceMode==='manual'||selected;
  function selectReferences(selection:FarmEconomicSelection|null) {
    const fields=selection?farmReferenceFields(selection):
      Object.fromEntries(references.slice(2).map(spec=>[spec.key,'']));
    setDraft(current=>({...current,fields:{...current.fields,...fields},rightsConfirmed:false}));
    setSelected(!!selection);setPreview(null);setError(null);
  }
  function changeReferenceMode(mode:'saved'|'manual') {
    if(locked||mode===referenceMode)return;
    selectReferences(null);setReferenceMode(mode);
  }
  function edit(fields:Row) {
    if(locked)return;
    const changedReference=references.slice(2).some(spec=>Object.hasOwn(fields,spec.key));
    setDraft(current=>({...current,fields:{...current.fields,...fields},
      rightsConfirmed:changedReference?false:current.rightsConfirmed}));setPreview(null);setError(null);
  }
  function editRow(kind:'forcing'|'crops',index:number,key:string,value:string) {
    if(locked)return;
    setDraft(current=>({...current,[kind]:current[kind].map((row,i)=>i===index?{...row,[key]:value}:row)}));
    setPreview(null);setError(null);
  }
  function addRow(kind:'forcing'|'crops') {
    if(locked)return;
    setDraft(current=>({...current,[kind]:current[kind].length<32?[...current[kind],{}]:current[kind]}));
    setPreview(null);setError(null);
  }
  function removeRow(kind:'forcing'|'crops',index:number) {
    if(locked)return;
    setDraft(current=>({...current,[kind]:current[kind].filter((_,i)=>i!==index)}));
    setPreview(null);setError(null);
  }
  function review(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();if(locked||!ready)return;
    try {setPreview(buildFarmAuthoringRequest(draft));setError(null);}
    catch(value) {setPreview(null);setError(value instanceof FarmDraftError?value.message:
      '입력을 확인할 수 없습니다.');}
  }
  async function register() {
    if(!api||!preview||busy)return;
    setBusy(true);setError(null);
    try {const result=await api.registerAuthoredFarm(preview);
      if(alive.current)onRegistered(result);
    } catch(value) {
      if(!alive.current)return;
      const code=value instanceof ApiError?value.code:'network_unresolved';
      if(code==='network_unresolved'||code==='server_unavailable'||code==='response_rejected') {
        setUncertain(true);
        setError('응답이 불확실합니다. 같은 입력과 판본으로 저장 접수를 다시 확인하세요.');
      } else {
        setUncertain(false);
        setPreview(null);
        setError(code==='intent_conflict'?'같은 판본에 다른 입력이 저장되어 있습니다. 새 판본을 선택하세요.':
          code==='access_denied'?'입력 등록 권한이 없습니다.':
          code==='invalid_request'?'서버가 입력·현재 출처·권리를 확인하지 못했습니다. 항목과 원천 상태를 확인하세요.':
          '등록을 확인할 수 없습니다.');
      }
    } finally {if(alive.current)setBusy(false);}
  }
  const f=draft.fields;
  return <form className="authored-composer" onSubmit={review}>
    <div className="authored-composer-lead"><div><p className="step-number">새 입력 판본</p>
      <h3>농장 조건 직접 등록</h3><p>모든 수치는 사용자 가정입니다. 모르는 값은 임의로 채우지 마세요.
        저장 후 수정하려면 새 판본을 등록해야 합니다.</p></div>
      <span className="badge">입력 후보 · 검토 전</span></div>
    {error && <div className="notice error" role="alert">{error}</div>}
    <div className="authored-mode" aria-label="기준 참조 선택 방식">
      <button type="button" className="button secondary" disabled={locked}
        aria-pressed={referenceMode==='saved'} onClick={()=>changeReferenceMode('saved')}>저장 원천에서 선택</button>
      <button type="button" className="button secondary" disabled={locked}
        aria-pressed={referenceMode==='manual'} onClick={()=>changeReferenceMode('manual')}>참조 직접 입력</button>
    </div>
    {referenceMode==='saved'&&<SourceFarmSelector api={api} locked={locked} onSelection={selectReferences}/>}
    {ready&&<>
    <nav className="authored-composer-steps" aria-label="입력 구역">
      <a href={'#'+sectionId+'-references'}>01 기준 판본</a><a href={'#'+sectionId+'-facility'}>02 시설·제어</a>
      <a href={'#'+sectionId+'-cultivation'}>03 구간·재배</a><a href={'#'+sectionId+'-rights'}>04 목표·권리</a>
    </nav>
    <details className="authored-section" open><summary id={sectionId+'-references'}><span>01</span> 기준 판본과 공통 가정</summary>
      <p>{referenceMode==='saved'?'선택한 원천·경제 참조는 읽기 전용입니다. 새 농장 ID와 판본을 입력하세요.':
        '앞선 조사·시장 보류·경제 입력에서 실제로 발급받은 식별자를 입력합니다.'}
        {' '}서버가 등록 시 현재 권리와 판본을 다시 확인합니다.</p>
      <div className="authored-fields">{(selected?references.slice(0,2):references).map(spec=><TextField key={spec.key} spec={spec}
        value={f[spec.key]??''} onChange={value=>edit({[spec.key]:value})} disabled={locked}/>)}</div>
      {selected&&<details className="authored-reference-details"><summary>원천·경제 참조 상세 · 읽기 전용</summary>
        <div className="authored-fields source-farm-readonly">{references.slice(2).map(spec=><TextField key={spec.key} spec={spec}
          value={f[spec.key]??''} onChange={value=>edit({[spec.key]:value})} disabled={locked} readOnly/>)}</div>
      </details>}
      <div className="authored-subsection"><h4>작성한 수치의 공통 출처</h4><p>아래 출처 참조와 시각을
        모든 사용자 가정 수치에 붙입니다. 이것은 실측이나 독립 승인이 아닙니다.</p>
        <div className="authored-fields">{[
          {key:'source_ref',label:'사용자 가정 출처 참조'},
          {key:'record_revision',label:'가정 기록 판본'},
          {key:'available_at',label:'가정을 알 수 있던 시각 · UTC',help:'결정 시각보다 늦으면 등록할 수 없습니다. YYYY-MM-DDTHH:mm:ssZ'},
        ].map(spec=><TextField key={spec.key} spec={spec} value={f[spec.key]??''}
          onChange={value=>edit({[spec.key]:value})} disabled={locked}/>)}</div></div>
    </details>
    <details className="authored-section" open><summary id={sectionId+'-facility'}><span>02</span> 온실 시설과 열 제어</summary>
      <p>시설의 크기와 물리 값을 각각 입력합니다. 온실 면적에서 열용량이나 환기량을
        자동 추정하지 않습니다.</p>
      <div className="authored-fields"><SelectField name="tenure" label="시설 소유 상태" value={f.tenure??''}
        onChange={value=>edit({tenure:value})} disabled={locked} options={[
          ['owned','소유'],['leased','임차'],['unknown','미확인']]}/>
        <SelectField name="decision_basis" label="결정 유형" value={f.decision_basis??''}
          onChange={value=>edit({decision_basis:value})} disabled={locked} options={[
            ['new_facility','신규 시설'],['existing_facility_crop_change','기존 시설 작물 변경']]}/>
        {facility.map(spec=><TextField key={spec.key} spec={spec} value={f[spec.key]??''}
          onChange={value=>edit({[spec.key]:value})} disabled={locked}/>)}
        <SelectField name="heater_available" label="난방 사용 가능 여부" value={f.heater_available??''}
          onChange={value=>edit({heater_available:value})} disabled={locked} options={[
            ['yes','사용 가능'],['no','사용 불가']]}/></div>
      <p className="authored-caveat">난방열은 모델의 공급열입니다. 실제 구매 전력·연료량은
        이 입력만으로 계산하지 않습니다.</p>
    </details>
    <details className="authored-section" open><summary id={sectionId+'-cultivation'}><span>03</span> 원본 구간과 재배 의도</summary>
      <p>원본 날씨의 각 구간과 정확히 같은 UTC 시작·종료 시각을 한 줄씩 적습니다.
        현재 서버는 일치하지 않는 구간을 거부합니다.</p>
      <div className="authored-repeat">{draft.forcing.map((row,index)=><fieldset key={index}
        className="authored-repeat-row"><legend>원본 구간 {index+1}</legend>
        <div className="authored-fields">{forcingFields.map(spec=><TextField key={spec.key} spec={spec}
          value={row[spec.key]??''} onChange={value=>editRow('forcing',index,spec.key,value)}
          disabled={locked}/>)}</div>
        {draft.forcing.length>1&&<button type="button" className="button secondary"
          disabled={locked} onClick={()=>removeRow('forcing',index)}>이 구간 삭제</button>}</fieldset>)}</div>
      <button type="button" className="button secondary" disabled={locked||draft.forcing.length>=32}
        onClick={()=>addRow('forcing')}>원본 구간 추가</button>
      <div className="authored-subsection"><h4>작물 의도와 달력</h4><p>경제 원장에 신규 수확이나
        판매가 있으면 같은 배치·등급·판매 경로를 등록해야 합니다. 입력한 작물명은 생장이나
        수확 예측을 만들지 않습니다. 열 계산만 하는 경우에는 비워 둘 수 있습니다.</p>
        {draft.crops.map((row,index)=><fieldset key={index} className="authored-repeat-row">
          <legend>작물 의도 {index+1}</legend><div className="authored-fields">
            {cropFields.map(spec=><TextField key={spec.key} spec={spec} value={row[spec.key]??''}
              onChange={value=>editRow('crops',index,spec.key,value)} disabled={locked}/>)}</div>
          <button type="button" className="button secondary" disabled={locked}
            onClick={()=>removeRow('crops',index)}>이 작물 의도 삭제</button></fieldset>)}
        <button type="button" className="button secondary" disabled={locked||draft.crops.length>=32}
          onClick={()=>addRow('crops')}>작물 의도 추가</button></div>
    </details>
    <details className="authored-section" open><summary id={sectionId+'-rights'}><span>04</span> 목표와 사용 권리</summary>
      <div className="authored-fields"><SelectField name="objective" label="조건부 평가 목표" value={f.objective??''}
        onChange={value=>edit({objective:value})} disabled={locked} options={[
          ['conditional_operating_profit','조건부 운영이익'],
          ['conditional_operating_margin','조건부 운영 마진율'],
          ['minimum_cash','최소 현금 잔액']]}/>
        <SelectField name="capex_mode" label="설비 투자 한도 상태" value={f.capex_mode??''}
          onChange={value=>edit({capex_mode:value})} disabled={locked} options={[
          ['unknown','미확인 · null'],['known','금액 입력']]}/>
        {f.capex_mode==='known'&&<TextField spec={{key:'capex_ceiling',label:'설비 투자 한도 · KRW'}}
          value={f.capex_ceiling??''} onChange={value=>edit({capex_ceiling:value})} disabled={locked}/>}
        <SelectField name="cash_mode" label="최소 현금 상태" value={f.cash_mode??''}
          onChange={value=>edit({cash_mode:value})} disabled={locked} options={[
          ['unknown','미확인 · null'],['known','금액 입력']]}/>
        {f.cash_mode==='known'&&<TextField spec={{key:'minimum_cash',label:'최소 현금 · KRW'}}
          value={f.minimum_cash??''} onChange={value=>edit({minimum_cash:value})} disabled={locked}/>}
        <TextField spec={{key:'declaration_id',label:'권리 선언 ID'}}
          value={f.declaration_id??''} onChange={value=>edit({declaration_id:value})} disabled={locked}/>
        <TextField spec={{key:'rights_revision',label:'권리 선언 판본'}}
          value={f.rights_revision??''} onChange={value=>edit({rights_revision:value})} disabled={locked}/></div>
      <label className="rights-checkbox authored-rights"><input type="checkbox"
        checked={draft.rightsConfirmed} disabled={locked} onChange={event=>{
          setDraft(current=>({...current,rightsConfirmed:event.target.checked}));
          setPreview(null);setError(null);}}/>
        <span>위 수치·재배 의도를 제가 작성했고 평가 기간 동안 접근·저장·변환·계산 사용·
          화면 표시를 허용합니다. 재배포는 허용하지 않습니다. 이 선언은 외부 기상·시장 자료의
          권리 승인이나 수치의 정확성 인증이 아닙니다.</span></label>
    </details>
    <div className="authored-submit"><p>입력은 판본으로 변경 불가 저장됩니다.
      등록 직후에는 검토·해제·시뮬레이션이 완료되지 않습니다.</p>
      <button type="submit" className="button secondary" disabled={locked}>입력 내용 검토</button></div>
    {preview&&<section className="authored-preview" aria-label="제출 전 확인">
      <h4>제출 전 확인</h4><dl><div><dt>농장 판본</dt><dd>{preview.farm.scenario_id} / {preview.farm.scenario_revision}</dd></div>
        <div><dt>평가 기간</dt><dd>{String(preview.farm.period_start)} ~ {String(preview.farm.period_end)}</dd></div>
        <div><dt>원본 구간</dt><dd>{draft.forcing.length}개 · 작성한 구간과 원본 일치 여부는 서버 검증</dd></div>
        <div><dt>작물 의도</dt><dd>{draft.crops.length}개 · 생장·수확 예측 없음</dd></div>
        <div><dt>시장 자료</dt><dd>보류 · 자료 유래 전망 없음</dd></div>
        <div><dt>권리</dt><dd>사용자 가정만 선언 · 재배포 불가</dd></div></dl>
      <button type="button" className="button primary" disabled={!api||busy}
        onClick={register}>{busy?'등록 확인 중…':uncertain?'같은 입력으로 등록 재확인':'불변 입력 판본 등록'}</button>
      {uncertain&&<p className="muted">응답 유실 후에는 내용을 수정하지 않고 같은 판본·바이트로 재확인합니다.</p>}
    </section>}
    </>}
  </form>;
}
