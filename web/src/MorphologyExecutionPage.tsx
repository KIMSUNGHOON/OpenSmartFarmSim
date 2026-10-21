import { useEffect,useMemo,useRef,useState } from 'react';
import MorphologyReplayPage from './MorphologyReplayPage';
import { ApiError } from './api-validation';
import { createMorphologyExecutionClient,decodeMorphologyRequest,type MorphologyExecutionClient,type MorphologyJob,
  type MorphologyStatus,type MorphologyRequest } from './morphologyExecution';
import type { MorphologyReplay,MorphologyReplaySource } from './morphologyReplay';
import './MorphologyExecutionPage.css';

const TOKEN_KEY='ossf-morphology-token-v1',JOB_KEY='ossf-morphology-job-v1',PENDING_KEY='ossf-morphology-pending-v1';
const stateLabel={queued:'대기 중',simulating:'입력 확인 · 계산 중',succeeded:'저장 완료',hold:'계산 보류',failed:'계산 실패',canceled:'취소됨'};
function read(storage:'sessionStorage'|'localStorage',key:string){try{return window[storage].getItem(key)??'';}catch{return '';}}
function store(storage:'sessionStorage'|'localStorage',key:string,value:string|null){try{if(value===null)window[storage].removeItem(key);else window[storage].setItem(key,value);}catch{/* The server job remains authoritative when browser storage is unavailable. */}}
function initialClient(){try{const token=read('sessionStorage',TOKEN_KEY);return token?createMorphologyExecutionClient(token):null;}catch{return null;}}
function initialJob(){const value=read('localStorage',JOB_KEY);return /^[0-9a-f-]{36}$/.test(value)?value:'';}
function initialPending(){try{const raw=read('localStorage',PENDING_KEY);return raw?decodeMorphologyRequest(JSON.parse(raw)):null;}catch{return null;}}
function terminal(job:MorphologyJob|null){return !!job&&['succeeded','hold','failed','canceled'].includes(job.state);}
function message(error:unknown){return error instanceof ApiError&&error.status===401?'연결이 만료됐습니다. 다시 연결해 주세요.':
  error instanceof ApiError&&error.status===403?'현재 계정의 접근 권한을 확인할 수 없습니다.':
  error instanceof ApiError&&error.status===422?'현재 입력·권리 확인이 보류됐습니다. 저장 수치는 표시하지 않습니다.':
  error instanceof ApiError&&error.status===409?'같은 요청 판본에 다른 입력이 있습니다. 접수 내역을 확인해 주세요.':
  '현재 서버 응답을 확인할 수 없습니다. 같은 작업을 다시 확인해 주세요.';}

export default function MorphologyExecutionPage(){
  const [credential,setCredential]=useState(()=>read('sessionStorage',TOKEN_KEY)),[client,setClient]=useState<MorphologyExecutionClient|null>(initialClient);
  const [jobId,setJobId]=useState(initialJob),[job,setJob]=useState<MorphologyJob|null>(null),[status,setStatus]=useState<MorphologyStatus|null>(null);
  const [pending,setPending]=useState<MorphologyRequest|null>(initialPending),[preview,setPreview]=useState<{label:string;request:MorphologyRequest}|null>(null);
  const [data,setData]=useState<MorphologyReplay|null>(null),[error,setError]=useState(''),[inputError,setInputError]=useState('');
  const [busy,setBusy]=useState<'connect'|'submit'|'refresh'|'cancel'|null>(null),[tab,setTab]=useState<'overview'|'replay'|'evidence'>('overview');
  const generation=useRef(0),active=useRef<AbortController|null>(null),timer=useRef<number|null>(null),id=useRef(jobId),currentJob=useRef(job);
  const loadedResult=useRef<string|null>(null),pendingRequest=useRef(pending);id.current=jobId;currentJob.current=job;pendingRequest.current=pending;
  const source=useMemo<MorphologyReplaySource>(()=>({version:'v2',directory:'./morphology-rational-replay',
    artifact_sha256:data?.artifact_sha256??'0'.repeat(64),index_sha256:'0'.repeat(64),frames:data?.frames.length??0}),[data]);
  function stop(){generation.current++;active.current?.abort();if(timer.current!==null)window.clearTimeout(timer.current);timer.current=null;}
  function begin(kind:typeof busy){stop();const version=generation.current,controller=new AbortController();active.current=controller;setBusy(kind);
    return {signal:controller.signal,current:()=>generation.current===version&&!controller.signal.aborted};}
  function clearResult(){setData(null);loadedResult.current=null;}
  function rejected(cause:unknown){clearResult();setStatus(null);setBusy(null);setError(message(cause));if(cause instanceof ApiError&&cause.status===401){
    store('sessionStorage',TOKEN_KEY,null);setClient(null);setCredential('');setPreview(null);}}
  async function refresh(api:MorphologyExecutionClient,jobIdentifier:string){
    const work=begin('refresh');setError('');
    try{
      const value=await api.status(jobIdentifier,work.signal);if(!work.current())return;
      setJob(value.job);setStatus(value);currentJob.current=value.job;
      if(value.job.state==='succeeded'){
        if(loadedResult.current!==value.result!.result_sha256){
          const saved=await api.replay(jobIdentifier,work.signal);if(!work.current())return;
          setStatus(saved.status);setData(saved.replay);loadedResult.current=saved.status.result!.result_sha256;
          setTab(previous=>previous==='overview'?'replay':previous);
        }
      }else clearResult();
      if(!terminal(value.job))timer.current=window.setTimeout(()=>void refresh(api,jobIdentifier),3500);
    }catch(cause){if(!work.current())return;rejected(cause);
      if(!(cause instanceof ApiError)||cause.status===503){if(!terminal(currentJob.current))timer.current=window.setTimeout(()=>void refresh(api,jobIdentifier),5000);}
    }finally{if(work.current())setBusy(null);}
  }
  useEffect(()=>{
    if(!client)return;const api=client,work=begin('connect');setPreview(null);setInputError('');
    void (async()=>{
      try{const value=await api.preview(work.signal);if(work.current())setPreview(value);}
      catch(cause){if(work.current()){setInputError(message(cause));if(cause instanceof ApiError&&cause.status===401)rejected(cause);}}
      if(work.current()){setBusy(null);if(id.current&&!pendingRequest.current)void refresh(api,id.current);}
    })();
    const visible=()=>{if(document.hidden){stop();setBusy(null);}else if(id.current&&!pendingRequest.current)void refresh(api,id.current);};
    document.addEventListener('visibilitychange',visible);
    return()=>{stop();document.removeEventListener('visibilitychange',visible);};
  },[client]);
  async function submit(){
    if(!client||(!preview&&!pending))return;
    const request=pending??{...preview!.request,study_id:'morphology-'+crypto.randomUUID(),revision:'r1'};
    setPending(request);pendingRequest.current=request;store('localStorage',PENDING_KEY,JSON.stringify(request));const work=begin('submit');setError('');clearResult();setStatus(null);
    try{const value=await client.submit(request,work.signal);if(!work.current())return;
      setJobId(value.job_id);id.current=value.job_id;store('localStorage',JOB_KEY,value.job_id);setJob(value);currentJob.current=value;
      setStatus(null);setPending(null);pendingRequest.current=null;store('localStorage',PENDING_KEY,null);setBusy(null);void refresh(client,value.job_id);
    }catch(cause){if(work.current()){rejected(cause);setBusy(null);}}
  }
  async function cancel(){
    if(!client||!jobId)return;const work=begin('cancel');setError('');
    try{const value=await client.cancel(jobId,work.signal);if(!work.current())return;
      setJob(value.job);currentJob.current=value.job;clearResult();setStatus(null);setBusy(null);void refresh(client,jobId);
    }catch(cause){if(work.current()){rejected(cause);setBusy(null);}}
  }
  const locked=busy==='connect'||busy==='submit'||busy==='cancel',running=!!job&&!terminal(job);
  return <main className="morphology-execution" data-job-id={jobId||undefined} data-job-state={job?.state??'none'}>
    <header className="morph-execution-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR</span>
      <h1>작물 성장 실험실</h1><p>연결된 입력으로 계산하고, 같은 시점의 토마토 3D를 확인합니다.</p></div>
      <a href="http://localhost:5173/">기존 작업 공간 ↗</a></header>
    <p className="morph-execution-scope">자체 합성 입력 · 실제 품종·농장 검증 전 · 생산·수익·작물 추천 미제공</p>
    <details className="morph-execution-connection" open={!client}><summary>연결 {client?'설정됨':'필요'}</summary>
      <form onSubmit={event=>{event.preventDefault();try{const value=createMorphologyExecutionClient(credential);store('sessionStorage',TOKEN_KEY,credential);setError('');setClient(value);}catch{setError('접근 토큰의 형식을 확인해 주세요.');}}}>
        <label>접근 토큰<input type="password" value={credential} autoComplete="off" spellCheck={false} onChange={event=>setCredential(event.target.value)} disabled={locked}/></label>
        <button disabled={locked}>연결</button>{client&&<button type="button" disabled={locked} onClick={()=>{stop();setClient(null);setCredential('');store('sessionStorage',TOKEN_KEY,null);clearResult();setPreview(null);setStatus(null);setBusy(null);}}>연결 해제</button>}
      </form><p>토큰은 이 탭의 세션에만 보관합니다. 권한은 서버가 요청마다 확인합니다.</p></details>
    <nav className="morph-execution-tabs" aria-label="실험실 메뉴">{(['overview','replay','evidence'] as const).map((key,index)=><button key={key}
      aria-current={tab===key?'page':undefined} onClick={()=>setTab(key)}>{['계산 작업','3D 결과','근거와 범위'][index]}</button>)}</nav>
    {error&&<p className="morph-execution-error" role="alert">{error}</p>}
    <section className="morph-execution-work" hidden={tab!=='overview'} aria-label="계산 작업">
      <article className="morph-execution-input"><span className="morphology-eyebrow">CONNECTED RESEARCH INPUT</span><h2>{preview?.label??'연결된 연구 입력 확인'}</h2>
        <p>기온과 명시된 초기 기관을 사용해 출현 시각·절간 길이를 계산합니다. 화면의 재생은 완료된 저장 시점만 사용합니다.</p>
        {inputError&&<p role="status">{inputError}</p>}
        {preview&&<dl><div><dt>등록 입력</dt><dd>{preview.request.farm.scenario_id} / {preview.request.farm.scenario_revision}</dd></div>
          <div><dt>작물 참조</dt><dd>{preview.request.farm.crop_id} · 검증된 품종 계수 아님</dd></div></dl>}
        <button className="morph-execution-primary" disabled={!client||locked||running||(!preview&&!pending)} onClick={()=>void submit()}>
          {busy==='submit'?'접수 확인 중…':pending?'같은 접수 다시 확인':job?'같은 입력으로 새 계산':'계산 시작'}</button>
        {pending&&<p>응답이 유실돼도 같은 요청으로 접수를 확인합니다. 확인 전 새 요청을 만들지 않습니다.</p>}
      </article>
      <article className="morph-execution-status" aria-label="서버 계산 상태"><span className="morphology-eyebrow">SERVER EXECUTION</span>
        <div role="status"><h2>{busy==='submit'?'새 계산 접수 확인 중':pending?'새 접수 확인 필요':status?.cancel_requested?'취소 요청됨 · 확인 대기':job?stateLabel[job.state]:busy==='connect'?'연결 확인 중':'아직 접수한 계산이 없습니다'}</h2></div>
        <ol hidden={!!pending}>{['접수','계산','저장 완료'].map((label,index)=><li key={label} aria-current={index===1&&job?.state==='simulating'?'step':undefined}
          data-complete={!!job&&(index===0||job.state==='succeeded')}>
          <span>{index+1}</span>{label}</li>)}</ol>
        {jobId&&!pending&&<><p className="morph-execution-identifier">작업 ID <code>{jobId}</code></p><p>메뉴를 이동하거나 새로고침해도 이 작업을 다시 조회합니다.</p>
          {job&&<dl><div><dt>등록 시각</dt><dd>{job.created_at}</dd></div><div><dt>최근 상태 기록</dt><dd>{job.updated_at}</dd></div></dl>}
          <div className="morph-execution-actions"><button disabled={!client||locked} onClick={()=>client&&void refresh(client,jobId)}>현재 상태 다시 확인</button>
            <button disabled={!client||locked||terminal(job)} onClick={()=>void cancel()}>취소 요청</button></div></>}
        {busy==='refresh'&&<p role="status">서버의 현재 입력·권리와 작업 상태를 확인하고 있습니다.</p>}
        {job?.reason_code&&<p>서버 사유: {job.reason_code}</p>}
      </article></section>
    <section hidden={tab!=='replay'} aria-label="3D 결과">
      {data?<><div className="morph-execution-result-bar"><span>완료 작업의 원 저장 결과 · {data.frames.length}시점</span>
        <button disabled={!client||locked} onClick={()=>client&&void refresh(client,jobId)}>현재 권한 다시 확인</button></div>
        <MorphologyReplayPage providedReplay={data} source={source} embedded paused={tab!=='replay'}/></>:
        <div className="morph-execution-empty"><h2>{error?'저장 결과 표시 보류':'완료된 계산을 기다립니다'}</h2><p>원 결과를 확인한 뒤 3D·표·그래프를 같은 저장 시점에 연결합니다.</p>
          {jobId&&<button disabled={!client||locked} onClick={()=>client&&void refresh(client,jobId)}>작업 다시 확인</button>}</div>}
    </section>
    <section className="morph-execution-evidence" hidden={tab!=='evidence'} aria-label="근거와 범위"><h2>계산과 표현의 범위</h2>
      <p>줄기 길이와 기관 출현은 저장된 계산값입니다. 고정된 복엽 3개·표면·줄기 반경은 제작 가정이며 실제 잎 수나 품종 형태의 예측이 아닙니다.</p>
      <p>현재 입력은 자체 합성 자료입니다. 실제 품종의 초기 개체·계수와 독립 농장 측정을 확보한 뒤 검증해야 합니다. 과실·숙기·생산량, 자원·경제와 자율 작물 선정은 후속입니다.</p>
      {status&&<dl><div><dt>마지막 서버 확인</dt><dd>{status.observed_at}</dd></div><div><dt>현재 결과 ID</dt><dd>{status.result?.result_sha256??'없음'}</dd></div>
        <div><dt>실제 계산 시각</dt><dd>{status.result?.calculated_at??'완료 전'}</dd></div></dl>}
      <p>G0–G4는 미평가입니다. 서버 조회가 거부되면 수치를 제거하며, 이전 결과나 임의 애니메이션을 대신 표시하지 않습니다.</p>
    </section>
  </main>;
}
