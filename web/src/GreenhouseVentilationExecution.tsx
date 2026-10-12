import { lazy,Suspense,useEffect,useRef,useState,type FormEvent } from 'react';
import { ApiError,type createApi } from './api';
import { ventilationExecutionResultLookup,validVentilationExecutionRequest,type VentilationExecutionRequest,type VentilationExecutionLookup,
  type VentilationExecutionJob,type VentilationExecutionRead,type VentilationExecutionCancellation } from './greenhouseVentilationExecution';
import type { GreenhouseVentilationLookup } from './greenhouseVentilationReplay';
import Prefix,{readVentilationPrefixSnapshot,type VentilationPrefixSnapshot} from './GreenhouseVentilationPrefix';
import './CropReplay.css';
import './JointCropClimateExecution.css';
const Replay=lazy(()=>import('./GreenhouseVentilationReplay'));
type Api=ReturnType<typeof createApi>;
type Session={api:Api;lookup:VentilationExecutionLookup};
type Connection='idle'|'checking'|'waiting'|'retrying'|'blocked'|'terminal';
const EMPTY={job_id:'',scenario_id:'',scenario_revision:'',registration_sha256:'',crop_id:''};
const LABELS={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',
  registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
const STATES={queued:'대기 중',simulating:'계산 중',succeeded:'계산 완료',hold:'보류',failed:'실행 실패',canceled:'취소됨'};
const ERRORS:Record<string,string>={auth_required:'접근 토큰을 설정해 주세요.',access_denied:'현재 조회 권한이 없습니다.',
  not_available:'열람 가능한 계산 작업이 없습니다.',invalid_request:'현재 자료 권리 또는 농장 연결을 확인할 수 없습니다.',
  response_rejected:'입력 또는 응답의 형식을 확인할 수 없습니다.',request_canceled:'HTTP 조회를 중단했습니다.',
  intent_conflict:'같은 연구 ID·판본에 다른 입력이 등록돼 있습니다.',too_large:'접수 파일이 허용 크기를 넘습니다.',
  network_unresolved:'응답을 받지 못했습니다.',server_unavailable:'서버에 연결할 수 없습니다.'};
const BLOCKED=new Set(['auth_required','access_denied','not_available','invalid_request','response_rejected']);
function errorOf(cause:unknown){return cause instanceof ApiError?cause:new ApiError('network_unresolved');}
function terminal(value:VentilationExecutionRead){
  return !['queued','simulating'].includes(value.job.state)
    && !(value.checkpoint_status==='unavailable' && (value.job.state==='succeeded'||value.job.state==='hold'));
}
function terminalState(value:VentilationExecutionRead|null){return value!==null&&(!['queued','simulating'].includes(value.job.state)||value.cancel_requested);}
export default function GreenhouseVentilationExecution({api}:{api:Api|null}){
  const [fields,setFields]=useState(EMPTY),[request,setRequest]=useState<VentilationExecutionRequest|null>(null);
  const [session,setSession]=useState<Session|null>(null),[job,setJob]=useState<VentilationExecutionJob|null>(null);
  const [progress,setProgress]=useState<VentilationExecutionRead|null>(null),[cancellation,setCancellation]=useState<VentilationExecutionCancellation|null>(null);
  const [error,setError]=useState<ApiError|null>(null),[commandError,setCommandError]=useState<ApiError|null>(null);
  const [connection,setConnection]=useState<Connection>('idle'),[lastObserved,setLastObserved]=useState<string|null>(null);
  const [submitBusy,setSubmitBusy]=useState(false),[cancelBusy,setCancelBusy]=useState(false),[restart,setRestart]=useState(0);
  const [visible,setVisible]=useState(()=>document.visibilityState!=='hidden');
  const [opened,setOpened]=useState<GreenhouseVentilationLookup|null>(null);
  const [prefix,setPrefix]=useState<VentilationPrefixSnapshot|null>(null),[prefixObserved,setPrefixObserved]=useState<string|null>(null);
  const [prefixUnavailable,setPrefixUnavailable]=useState(false);
  const prefixDisabled=useRef(false);
  const epoch=useRef(0),submitAbort=useRef<AbortController|null>(null),cancelAbort=useRef<AbortController|null>(null);
  const pollAbort=useRef<AbortController|null>(null),pending=useRef<Promise<void>|null>(null);
  const current=session?.api===api?session:null;
  function reset(){
    epoch.current++;submitAbort.current?.abort();cancelAbort.current?.abort();pollAbort.current?.abort();
    setSession(null);setJob(null);setProgress(null);setCancellation(null);setOpened(null);setError(null);setCommandError(null);
    setLastObserved(null);setConnection('idle');setSubmitBusy(false);setCancelBusy(false);
    setPrefix(null);setPrefixObserved(null);setPrefixUnavailable(false);prefixDisabled.current=false;
  }
  useEffect(()=>{reset();setRequest(null);setFields(EMPTY);return()=>{epoch.current++;
    submitAbort.current?.abort();cancelAbort.current?.abort();pollAbort.current?.abort();};},[api]);
  useEffect(()=>{const change=()=>{setVisible(document.visibilityState!=='hidden');setOpened(null);setPrefix(null);setPrefixObserved(null);};
    document.addEventListener('visibilitychange',change);return()=>document.removeEventListener('visibilitychange',change);},[]);
  useEffect(()=>{
    if(!current||!visible||cancelBusy)return;
    let active=true,timer:ReturnType<typeof setTimeout>|undefined,delay=10_000;
    let allowsPrefix=!cancellation?.cancel_requested && (!job||['queued','simulating'].includes(job.state));
    const controller=new AbortController();pollAbort.current=controller;
    const valid=()=>active&&!controller.signal.aborted;
    async function refreshPrefix(){
      try{
        const next=await readVentilationPrefixSnapshot(current!.api,current!.lookup,controller.signal);if(!valid())return false;
        const snapshot=next.snapshot;
        if(snapshot){
          setJob(snapshot.summary.job);
          allowsPrefix=!snapshot.summary.cancel_requested && ['queued','simulating'].includes(snapshot.summary.job.state);
        }
        setPrefix(old=>!allowsPrefix?null:old&&snapshot&&JSON.stringify(old.summary.reference)===JSON.stringify(snapshot.summary.reference)?old:snapshot);
        setPrefixObserved(allowsPrefix?next.observedAt:null);setPrefixUnavailable(false);
        return true;
      }catch(cause){
        if(!valid())return false;const failure=errorOf(cause);
        if(failure.code!=='not_available')throw failure;
        setPrefix(null);setPrefixObserved(null);setPrefixUnavailable(true);prefixDisabled.current=true;
        return false;
      }
    }
    async function poll(){
      await pending.current;if(!valid())return;setConnection('checking');
      const task=(async()=>{
        let progressReadFailed=true;
        try{
          const value=await current!.api.greenhouseVentilationExecution(current!.lookup,controller.signal);if(!valid())return;
          progressReadFailed=false;
          setProgress(value);setJob(value.job);setLastObserved(value.observed_at);setError(null);delay=10_000;
          allowsPrefix=!value.cancel_requested && ['queued','simulating'].includes(value.job.state);
          if(!allowsPrefix){
            setPrefix(null);setPrefixObserved(null);
          }
          if(terminal(value)){setConnection('terminal');return;}
          if(allowsPrefix&&!prefixDisabled.current){await refreshPrefix();if(!valid())return;}
          setConnection('waiting');
        }catch(cause){
          if(!valid())return;let failure=errorOf(cause),prefixRead=false;
          if(progressReadFailed&&failure.code==='server_unavailable'&&allowsPrefix&&!prefixDisabled.current){
            try{prefixRead=await refreshPrefix();}catch(prefixCause){failure=errorOf(prefixCause);}
            if(!valid())return;
          }
          setError(failure);setProgress(null);setOpened(null);
          if(BLOCKED.has(failure.code)){setPrefix(null);setPrefixObserved(null);setLastObserved(null);setConnection('blocked');return;}
          if(failure.code==='intent_conflict'){setPrefix(null);setPrefixObserved(null);}
          delay=prefixRead?10_000:Math.min(delay*2,60_000);setConnection('retrying');
        }
        if(valid())timer=setTimeout(()=>{void poll();},delay);
      })();pending.current=task;await task;
    }
    void poll();return()=>{active=false;controller.abort();clearTimeout(timer);};
  },[current,visible,cancelBusy,restart]);
  async function chooseFile(file:File|undefined){
    reset();setRequest(null);if(!file)return;const id=epoch.current;
    try{
      if(file.size>64*1024)throw new ApiError('too_large');
      const value:unknown=JSON.parse(await file.text());if(id!==epoch.current)return;
      if(!validVentilationExecutionRequest(value))throw new ApiError('response_rejected');setRequest(value);
    }catch(cause){if(id===epoch.current)setCommandError(cause instanceof ApiError?cause:new ApiError('response_rejected'));}
  }
  async function submit(event:FormEvent){
    event.preventDefault();if(!api||!request||submitBusy)return;reset();const id=epoch.current;
    const controller=new AbortController();submitAbort.current=controller;setSubmitBusy(true);
    try{
      const accepted=await api.submitGreenhouseVentilationExecution(request,controller.signal);if(id!==epoch.current)return;
      setFields({job_id:accepted.job_id,...request.farm});setJob(accepted);setSession({api,lookup:{job_id:accepted.job_id,farm:{...request.farm}}});
    }catch(cause){if(id===epoch.current)setCommandError(errorOf(cause));}
    finally{if(id===epoch.current)setSubmitBusy(false);}
  }
  function reconnect(event:FormEvent){
    event.preventDefault();if(!api)return;reset();const {job_id,...farm}=fields;
    setSession({api,lookup:{job_id,farm}});
  }
  async function cancel(){
    if(!current||cancelBusy)return;const id=epoch.current,controller=new AbortController();cancelAbort.current=controller;
    pollAbort.current?.abort();setCancelBusy(true);setProgress(null);setOpened(null);setCommandError(null);
    setPrefix(null);setPrefixObserved(null);
    try{
      const value=await current.api.cancelGreenhouseVentilationExecution(current.lookup.job_id,controller.signal);if(id!==epoch.current)return;
      setCancellation(value);setJob(value.job);setLastObserved(value.observed_at);
    }catch(cause){if(id===epoch.current)setCommandError(errorOf(cause));}
    finally{if(id===epoch.current)setCancelBusy(false);}
  }
  const state=current?progress?.job??cancellation?.job??job:null;
  const checkpoint=current?progress?.checkpoint:null;
  const result=current&&progress?ventilationExecutionResultLookup(progress):null;
  return <div className="crop-replay joint-execution">
    <section className="panel"><div className="crop-heading"><div><p className="step-number">공동 계산 / 실행 연결</p>
      <h1>작물·기후·명시 환기 계산 상태</h1></div><span className="badge">합성 연구 · 현장 검증 전</span></div>
      <p>계산 중에는 확정된 저장 시점의 생장 수치를 표·그래프·3D로 확인합니다. 완료·수치 보류 뒤 같은 최종 저장 결과를 엽니다.</p>
      <p className="crop-caption">진행 걸음은 수치 계산의 작업량입니다. 작물 생장률·남은 시간·생산 예측이 아닙니다. 미확정 중간 상태를 만들지 않습니다.</p>
    </section>
    {!current&&<section className="panel" aria-label="계산 연결 안내" role="status">
      <h2>{api?'계산 작업 선택 전':'서버 연결 전'}</h2>
      <p>{api?'조회할 작업이 아직 선택되지 않았습니다. 아래에서 접수 파일을 선택해 계산을 접수하거나 기존 계산 작업을 조회하세요.':
        '상단의 내부 시험 연결에서 접근 토큰을 설정하세요. 연결 전에는 작업의 진행 여부를 조회하지 않습니다.'}</p>
      <p>작업을 연결하면 서버 상태·확정 계산 걸음·마지막 확인 시각이 표시됩니다. 개발용 별도 DB의 작업은 이 화면에 자동 표시되지 않습니다.</p>
    </section>}
    <section className="panel"><h2>등록 입력으로 계산 시작</h2><form onSubmit={submit}>
      <label>검토된 계산 접수 파일<input type="file" accept="application/json,.json" disabled={submitBusy||cancelBusy}
        onChange={event=>void chooseFile(event.target.files?.[0])}/></label>
      <p className="crop-caption">서버에 등록된 입력의 접수 JSON을 선택하세요. 원자료·인증 정보는 넣지 않습니다. 자료 권리는 서버에서 다시 확인합니다.</p>
      {request&&<p>선택한 연구: {request.study_id} / {request.revision} · 작물 {request.farm.crop_id}</p>}
      <button className="button primary" disabled={!api||!request||submitBusy||cancelBusy}>{submitBusy?'접수 확인 중…':'계산 접수'}</button>
      <p className="crop-caption">응답이 끊겼다면 같은 파일로 접수를 다시 확인할 수 있습니다. HTTP 중단만으로 미접수나 서버 취소가 확인되지는 않습니다.</p>
    </form></section>
    <details className="panel crop-lookup" open={!current}><summary>기존 계산에 다시 연결</summary><form onSubmit={reconnect}>
      <div className="crop-lookup-fields">{Object.entries(LABELS).map(([key,label])=><label key={key}>{label}<input required
        value={fields[key as keyof typeof fields]} maxLength={key==='registration_sha256'?64:200}
        pattern={key==='job_id'?'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}':key==='registration_sha256'?'[0-9a-f]{64}':'[A-Za-z0-9][A-Za-z0-9_.:\\/\\-]{0,199}'}
        onChange={event=>{reset();setFields({...fields,[key]:event.target.value});}}/></label>)}</div>
      <button className="button secondary" disabled={!api||submitBusy||cancelBusy}>기존 계산 조회</button>
    </form></details>
    {commandError&&<p className="panel" role="alert">{ERRORS[commandError.code]??'명령의 결과를 확인할 수 없습니다.'} 서버 작업 상태를 다시 확인하세요.</p>}
    {current&&<section className="panel execution-progress" aria-label="계산 진행 상태">
      <div className="crop-heading"><h2>{state?STATES[state.state]:'작업 확인 중'}</h2>
        <span role="status">{!visible?'화면 숨김 · 자동 조회 중지':cancelBusy?'서버 취소 요청 중':
          ({idle:'조회 전',checking:'서버 확인 중',waiting:'자동 조회 연결',retrying:'연결 끊김 · 자동 재시도',blocked:'조회 보류 · 자동 조회 중지',terminal:'최종 상태 확인'}[connection])}</span></div>
      <dl><div><dt>계산 작업 ID</dt><dd>{current.lookup.job_id}</dd></div>
        <div><dt>마지막 서버 확인 (UTC)</dt><dd>{lastObserved??'아직 확인하지 못함'}</dd></div>
        <div><dt>작업 갱신 시각</dt><dd>{state?.updated_at??'—'}</dd></div>
        <div><dt>작업 시도</dt><dd>{state?`${state.attempt_count} / ${state.max_attempts}`:'—'}</dd></div>
      </dl>
      {error&&<p role="alert">{error.code==='intent_conflict'?'조회할 확정 판본이 바뀌었습니다.':ERRORS[error.code]??'진행 정보를 확인할 수 없습니다.'}
        {prefix?' 아래는 마지막으로 확인한 확정 결과입니다.':' 이전 수치를 지웠습니다.'}</p>}
      {checkpoint?<dl aria-label="서버 수용 체크포인트"><div><dt>확정 계산 걸음</dt><dd>{checkpoint.steps} / {checkpoint.planned_steps}</dd></div>
        <div><dt>계산된 시각 (UTC)</dt><dd>{checkpoint.computed_through_utc??'초기 상태 · 아직 계산 전'}</dd></div>
        <div><dt>체크포인트 최초 수용 (UTC)</dt><dd>{checkpoint.checkpoint_recorded_at}</dd></div>
        <div><dt>확정 저장 행</dt><dd>{checkpoint.counts.samples} 시점 / {checkpoint.counts.events} 사건</dd></div></dl>:
        <p>{progress?.checkpoint_status==='unavailable'?'체크포인트 변경 중입니다. 확인 가능한 새 게시를 기다립니다.':'현재 표시할 확정 체크포인트가 없습니다.'}</p>}
      {(!visible||connection==='checking'||connection==='retrying'||connection==='blocked')&&
        <p className="crop-caption">표시한 작업 상태·시각은 마지막 확인 기록이며 현재 상태를 보장하지 않습니다.</p>}
      {(progress?progress.cancel_requested:cancellation?.cancel_requested)&&state?.state==='simulating'&&
        <p>서버가 취소 요청을 수락했습니다. 작업자의 취소 확인을 기다립니다.</p>}
      {cancellation&&<p role="status">{cancellation.cancel_accepted?'취소 요청 수락':'취소 요청으로 상태가 바뀌지 않음'} · 취소 응답 당시: {STATES[cancellation.job.state]}</p>}
      {state?.reason_code&&<p>서버 사유: {state.reason_code}</p>}
      <div className="crop-page-controls"><button className="button secondary" disabled={cancelBusy||!visible}
        onClick={()=>{setOpened(null);prefixDisabled.current=false;setPrefixUnavailable(false);setRestart(value=>value+1);}}>지금 다시 확인</button>
        <button className="button secondary" disabled={cancelBusy||state?.state==='canceled'} onClick={()=>void cancel()}>서버 계산 취소</button>
        <button className="button secondary" onClick={reset}>조회 연결 해제</button>
        {result&&<button className="button primary" onClick={()=>setOpened(result)}>같은 저장 결과 3D 열기</button>}</div>
      <p className="crop-caption">정상 응답 뒤 10초를 기다려 다시 조회합니다. 통신 오류는 최대 60초까지 간격을 늘립니다. 숨긴 화면에서는 조회를 멈춥니다.</p>
    </section>}
    {current&&visible&&!cancelBusy&&!opened&&<>
      {prefix&&prefixObserved?<Prefix key={prefix.summary.summary.last_sample_utc??'empty'} snapshot={prefix} observedAt={prefixObserved}
        stale={connection==='checking'||connection==='retrying'}/>:
        !terminalState(progress)&&<p className="panel" role="status">{prefixUnavailable?'현재 서버에서 확정 부분 결과를 열 수 없습니다. 계산 상태는 계속 확인합니다.':'표시 가능한 확정 생장 시점을 기다립니다.'}</p>}
    </>}
    {current&&opened&&<Suspense fallback={<p role="status">같은 저장 결과 준비 중…</p>}>
      <Replay api={current.api} initialSelection={opened} autoLoadInitialSelection/></Suspense>}
  </div>;
}
