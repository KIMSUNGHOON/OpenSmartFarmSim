import {useCallback,useEffect,useRef,useState} from 'react';
import {ApiError,uuid} from './api-validation';
import LeafAreaReplayPage from './LeafAreaReplayPage';
import {createLeafAppearanceExecutionClient,decodeLeafAppearanceRequest,type LeafAppearanceExecutionClient,
  type LeafAppearanceJob,type LeafAppearanceStatus} from './leafAppearanceExecution';
import type {LeafAppearanceExecutionReplay} from './leafAppearanceExecution';
import './MorphologyExecutionPage.css';
import './LeafPopulationExecutionPage.css';

const TOKEN='ossf-leaf-appearance-token-v1',JOB='ossf-leaf-appearance-job-v1',PENDING='ossf-leaf-appearance-pending-v1',FRAME='ossf-leaf-appearance-frame-v1';
function read(storage:'localStorage'|'sessionStorage',key:string){try{return window[storage].getItem(key);}catch{return null;}}
function save(storage:'localStorage'|'sessionStorage',key:string,value:string|null){try{if(value===null)window[storage].removeItem(key);else window[storage].setItem(key,value);}catch{/* The server remains authoritative when browser storage is unavailable. */}}
function credential(){return read('sessionStorage',TOKEN)??read('sessionStorage','ossf-leaf-token-v1')??read('sessionStorage','ossf-morphology-token-v1')??'';}
function storedJob(){const query=new URLSearchParams(location.search).get('job_id'),value=query??read('localStorage',JOB);return uuid(value)?value:'';}
function rememberJob(value:string){save('localStorage',JOB,value);const url=new URL(location.href);url.searchParams.set('job_id',value);url.searchParams.delete('frame');history.replaceState(null,'',url);}
function storedPending(){try{const value=read('localStorage',PENDING);return value?decodeLeafAppearanceRequest(JSON.parse(value)):null;}catch{return null;}}
function terminal(job:LeafAppearanceJob|null){return !!job&&['succeeded','hold','failed','canceled'].includes(job.state);}
function errorMessage(cause:unknown){
  if(cause instanceof ApiError){
    if(cause.status===401)return '연결이 만료됐습니다. 접근 토큰을 다시 확인해 주세요.';
    if(cause.status===403||cause.status===422)return '현재 입력·권리 확인이 거부돼 표시를 보류합니다. 저장 수치는 제거했습니다.';
    if(cause.status===503||cause.status===504)return '서버 응답을 확인하지 못해 표시를 보류합니다. 접수 응답이 없으면 같은 요청으로 다시 확인해 주세요.';
    if(cause.status===404)return '이 서버에서 작업을 찾지 못했습니다. 작업 ID와 연결을 확인해 주세요.';
  }
  return '응답·연결 또는 무결성을 확인하지 못해 표시를 보류합니다. 원 결과를 다시 확인해 주세요.';
}
const labels:Record<LeafAppearanceJob['state'],string>={queued:'접수됨 · 계산 대기',simulating:'서버에서 계산 중',succeeded:'계산 완료 · 결과 저장됨',hold:'계산 보류',failed:'계산 실패',canceled:'계산 취소됨'};

export default function LeafAppearanceExecutionPage(){
  const [secret,setSecret]=useState(''),[client,setClient]=useState<LeafAppearanceExecutionClient|null>(()=>{try{return createLeafAppearanceExecutionClient(credential());}catch{return null;}});
  const [jobId,setJobId]=useState(storedJob),[pending,setPending]=useState(storedPending),[job,setJob]=useState<LeafAppearanceJob|null>(null);
  const [preview,setPreview]=useState<Awaited<ReturnType<LeafAppearanceExecutionClient['preview']>>|null>(null);
  const [status,setStatus]=useState<LeafAppearanceStatus|null>(null),[data,setData]=useState<LeafAppearanceExecutionReplay|null>(null);
  const [tab,setTab]=useState<'overview'|'replay'|'evidence'>(()=>storedJob()&&!storedPending()?'replay':'overview');
  const [busy,setBusy]=useState<'input'|'submit'|'refresh'|'cancel'|null>(null),[elapsed,setElapsed]=useState(0),[error,setError]=useState(''),[lookup,setLookup]=useState('');
  const [cancelRequested,setCancelRequested]=useState(false);
  const id=useRef(jobId),unconfirmed=useRef(pending),sequence=useRef(0),abort=useRef<AbortController|null>(null),timer=useRef<number|undefined>(undefined);
  const stop=()=>{sequence.current++;abort.current?.abort();clearTimeout(timer.current);};
  function begin(kind:NonNullable<typeof busy>){stop();const generation=sequence.current,controller=new AbortController();abort.current=controller;setBusy(kind);setElapsed(0);
    return {signal:controller.signal,current:()=>sequence.current===generation&&!controller.signal.aborted};}
  function reject(cause:unknown){setData(null);setStatus(null);setError(errorMessage(cause));
    if(cause instanceof ApiError&&cause.status===401){save('sessionStorage',TOKEN,'');setSecret('');setClient(null);}}
  async function refresh(api:LeafAppearanceExecutionClient,value:string,retries=0){
    if(unconfirmed.current||document.hidden)return;const work=begin('refresh');setData(null);setStatus(null);if(!retries)setError('');
    try{const result=await api.observe(value,work.signal);if(!work.current())return;
      setJob(result.status.job);setStatus(result.status);setCancelRequested(result.status.cancel_requested);setData(result.replay);setBusy(null);setError('');
      if(result.replay)setTab('replay');else if(!terminal(result.status.job))timer.current=window.setTimeout(()=>void refresh(api,value),3500);
    }catch(cause){if(!work.current())return;reject(cause);setBusy(null);
      if(cause instanceof ApiError&&cause.status===503&&retries<2)timer.current=window.setTimeout(()=>void refresh(api,value,retries+1),5000);}
  }
  async function loadInput(api:LeafAppearanceExecutionClient){const work=begin('input');setError('');
    try{const value=await api.preview(work.signal);if(work.current()){setPreview(value);setBusy(null);
      if(job&&!terminal(job)&&id.current&&!unconfirmed.current)timer.current=window.setTimeout(()=>void refresh(api,id.current),3500);}}
    catch(cause){if(work.current()){reject(cause);setBusy(null);}}}
  useEffect(()=>{const url=new URL(location.href);if(jobId&&!url.searchParams.has('job_id')){url.searchParams.set('job_id',jobId);history.replaceState(null,'',url);}},[jobId]);
  useEffect(()=>{
    if(!client)return;const api=client;
    if(id.current&&!unconfirmed.current)void refresh(api,id.current);else if(!unconfirmed.current)void loadInput(api);
    const visible=()=>{if(document.hidden){stop();setBusy(null);setData(null);setStatus(null);}else if(id.current&&!unconfirmed.current)void refresh(api,id.current);};
    document.addEventListener('visibilitychange',visible);return()=>{stop();document.removeEventListener('visibilitychange',visible);};
  },[client]);
  useEffect(()=>{if(!busy)return;const interval=window.setInterval(()=>setElapsed(value=>value+1),1000);return()=>clearInterval(interval);},[busy]);
  async function submit(){
    if(!client||(!pending&&!preview))return;
    const request=pending??{...preview!.request,study_id:'appearance-'+crypto.randomUUID(),revision:'r1'};
    save('localStorage',PENDING,JSON.stringify(request));setPending(request);unconfirmed.current=request;
    const work=begin('submit');setData(null);setStatus(null);setJob(null);setCancelRequested(false);setError('');setTab('overview');
    try{const value=await client.submit(request,work.signal);if(!work.current())return;
      id.current=value.job_id;setJobId(value.job_id);rememberJob(value.job_id);setJob(value);
      save('localStorage',PENDING,null);unconfirmed.current=null;setPending(null);setBusy(null);void refresh(client,value.job_id);
    }catch(cause){if(work.current()){reject(cause);setBusy(null);}}
  }
  async function cancel(){
    if(!client||!id.current||unconfirmed.current)return;const work=begin('cancel');setData(null);setStatus(null);setError('');
    try{const value=await client.cancel(id.current,work.signal);if(!work.current())return;
      setJob(value.job);setCancelRequested(value.cancel_requested);setBusy(null);
      if(!terminal(value.job))timer.current=window.setTimeout(()=>void refresh(client,id.current),3500);
    }catch(cause){if(work.current()){reject(cause);setBusy(null);}}
  }
  const rememberFrame=useCallback((index:number)=>{save('localStorage',FRAME,JSON.stringify({job_id:id.current,index}));
    const url=new URL(location.href);if(url.searchParams.get('job_id')===id.current){url.searchParams.set('frame',String(index));history.replaceState(null,'',url);}},[]);
  function initialFrame(){try{const query=new URLSearchParams(location.search).get('frame');
    if(query!==null&&/^(0|[1-9][0-9]?)$/.test(query)&&Number(query)<64)return Number(query);
    const value=JSON.parse(read('localStorage',FRAME)??'null');return value?.job_id===jobId&&Number.isInteger(value.index)&&value.index>=0&&value.index<64?value.index:0;}catch{return 0;}}
  function openJob(){if(!client||!uuid(lookup)||pending)return;stop();id.current=lookup;setJobId(lookup);rememberJob(lookup);setJob(null);setTab('replay');void refresh(client,lookup);}
  const locked=busy==='submit'||busy==='cancel',running=!!job&&!terminal(job),refreshing=busy==='refresh';
  return <main className="morphology-execution leaf-execution leaf-appearance-execution" data-execution-kind="leaf-appearance" data-job-id={jobId||undefined} data-job-state={pending?'unconfirmed':job?.state??'none'}>
    <header className="morph-execution-header"><div><span className="morphology-eyebrow">OPEN SMART FARM SIMULATOR</span><h1>정책 기반 잎 성장 실험실</h1>
      <p>실제 계산 작업에서 저장한 잎과 줄기를 같은 시점의 3D로 확인합니다.</p></div><a href="./morphology-execution.html">이전 줄기 작업 공간 ↗</a></header>
    <p className="morph-execution-scope">자체 합성 연구 입력 · 실제 품종·농장 검증 전 · 생산·수익·작물 추천 미제공</p>
    <details className="morph-execution-connection" open={!client}><summary>연결 {client?'설정됨':'필요'}</summary>
      <form onSubmit={event=>{event.preventDefault();try{const api=createLeafAppearanceExecutionClient(secret);save('sessionStorage',TOKEN,secret);setClient(api);setSecret('');setError('');}catch{setError('접근 토큰의 형식을 확인해 주세요.');}}}>
        <label>접근 토큰<input type="password" value={secret} autoComplete="off" spellCheck={false} onChange={e=>setSecret(e.target.value)} disabled={locked}/></label><button disabled={locked}>연결</button>
        {client&&<button type="button" disabled={locked} onClick={()=>{stop();save('sessionStorage',TOKEN,'');setSecret('');setClient(null);setData(null);setStatus(null);setPreview(null);setBusy(null);}}>연결 해제</button>}
      </form><p>접근 토큰은 이 탭의 세션에 보관합니다. 권한은 서버가 요청마다 확인합니다.</p></details>
    <nav className="morph-execution-tabs" aria-label="실험실 메뉴">{(['overview','replay','evidence'] as const).map((key,i)=><button key={key} aria-current={tab===key?'page':undefined} onClick={()=>setTab(key)}>{['계산 작업','3D 결과','근거와 범위'][i]}</button>)}</nav>
    {error&&<p role="alert" className="morph-execution-error">{error}</p>}
    {busy&&<p role="status" className="leaf-execution-wait">{busy==='submit'?'접수 응답':busy==='cancel'?'취소 응답':busy==='input'?'입력 검토':'현재 작업·권리'} 확인 중 · 응답 대기 {elapsed}초 <span>서버 응답에 따라 갱신합니다.</span></p>}
    <section className="morph-execution-work" hidden={tab!=='overview'} aria-label="계산 작업">
      <article className="morph-execution-input"><span className="morphology-eyebrow">CONNECTED RESEARCH INPUT</span><h2>{preview?.label??'연결된 잎 계산 입력'}</h2>
        <p>완료된 줄기 결과와 초기 잎·명시 출현 정책을 연결합니다. 기온에 따른 잎 면적을 계산해 불변 결과로 저장합니다.</p>
        {preview&&<dl><div><dt>등록 입력</dt><dd>{preview.request.farm.scenario_id} / {preview.request.farm.scenario_revision}</dd></div>
          <div><dt>작물 참조</dt><dd>{preview.request.farm.crop_id} · 품종 계수 미검증</dd></div><div><dt>연결된 완료 줄기 작업</dt><dd>{preview.request.parent.job_id}</dd></div></dl>}
        {!preview&&!pending&&<button disabled={!client||!!busy} onClick={()=>client&&void loadInput(client)}>계산 입력 확인</button>}
        <button className="morph-execution-primary" disabled={!client||!!busy||running||(!preview&&!pending)} onClick={()=>void submit()}>{busy==='submit'?'접수 확인 중…':pending?'같은 접수 다시 확인':job?'같은 입력으로 새 계산':'계산 시작'}</button>
        {pending&&<p>접수가 아직 확인되지 않았습니다. 새로고침 후에도 같은 요청을 유지하며 새 요청을 자동 생성하지 않습니다.</p>}
      </article>
      <article className="morph-execution-status" aria-label="서버 계산 상태"><span className="morphology-eyebrow">SERVER EXECUTION</span>
        <div role="status"><h2>{pending?(busy==='submit'?'새 계산 접수 확인 중':'새 접수 확인 필요'):cancelRequested&&!terminal(job)?'취소 요청됨 · 확인 대기':job?labels[job.state]:refreshing?'저장 작업 확인 중':'아직 접수한 계산이 없습니다'}</h2></div>
        <ol hidden={!!pending}>{['접수','계산','저장 완료'].map((label,i)=><li key={label} aria-current={i===1&&job?.state==='simulating'?'step':undefined} data-complete={!!job&&(i===0||job.state==='succeeded')}><span>{i+1}</span>{label}</li>)}</ol>
        {jobId&&!pending&&<><p className="morph-execution-identifier">작업 ID <code>{jobId}</code></p><p>메뉴 이동·새로고침 시 같은 작업을 다시 조회합니다.</p>
          {job&&<dl><div><dt>최근 서버 상태 기록</dt><dd>{job.updated_at}</dd></div><div><dt>서버 사유</dt><dd>{job.reason_code??'없음'}</dd></div></dl>}
          <div className="morph-execution-actions"><button disabled={!client||!!busy} onClick={()=>client&&void refresh(client,jobId)}>현재 상태 다시 확인</button>
            <button disabled={!client||locked||terminal(job)} onClick={()=>void cancel()}>취소 요청</button></div></>}
      </article>
      <form className="leaf-execution-lookup" onSubmit={e=>{e.preventDefault();openJob();}}><label>저장 작업 ID<input value={lookup} spellCheck={false} onChange={e=>setLookup(e.target.value.trim())} placeholder="완료 또는 진행 중인 작업 ID"/></label>
        <button disabled={!client||!!busy||!!pending||!uuid(lookup)}>저장 작업 열기</button></form>
    </section>
    <section hidden={tab!=='replay'} aria-label="3D 결과">{data?<><div className="morph-execution-result-bar"><span>같은 작업의 원 저장 결과 · {data.frames.length}시점</span><button disabled={!client||!!busy} onClick={()=>client&&void refresh(client,jobId)}>현재 권한 다시 확인</button></div>
      <LeafAreaReplayPage key={jobId} providedReplay={data} source="appearance" embedded paused={tab!=='replay'} initialIndex={initialFrame()} onIndexChange={rememberFrame}/></>:
      <div className="morph-execution-empty"><h2>{error?'저장 결과 표시 보류':refreshing?'원 저장 결과를 확인하고 있습니다':'완료된 계산을 기다립니다'}</h2><p>현재 작업·입력·권리를 확인한 원 결과만 3D·표·그래프에 표시합니다.</p>
        {jobId&&!pending&&<button disabled={!client||!!busy} onClick={()=>client&&void refresh(client,jobId)}>작업 다시 확인</button>}</div>}</section>
    <section className="morph-execution-evidence" hidden={tab!=='evidence'} aria-label="근거와 범위"><h2>계산과 표현의 범위</h2>
      <p>잎별 면적과 줄기 길이는 이 작업의 저장 계산값입니다. 잎 수는 초기 목록과 명시한 영양·생식 위치 정책을 따라 계산합니다. 실제 품종의 출현 예측은 검증 전입니다.</p>
      <p>잎 면적은 제작한 단면 소엽 삼각형 면적에 대응합니다. 잎 모양·잎맥·각도·소엽 수·줄기 반경은 제작 가정이며 실제 품종 형태는 검증 전입니다.</p>
      <p>실제 품종·독립 농장 자료는 미확보입니다. 과실·숙기·생산량, 자원·경제와 자율 작물 선정은 후속이며 G0–G4는 미평가입니다.</p>
      {status&&<dl><div><dt>마지막 서버 확인</dt><dd>{status.observed_at}</dd></div><div><dt>실제 계산 시각</dt><dd>{status.result?.calculated_at??'완료 전'}</dd></div>
        <div><dt>결과 지문</dt><dd>{status.result?.result_sha256??'없음'}</dd></div><div><dt>완료 줄기 작업</dt><dd>{status.result?.parent_job_id??'완료 전'}</dd></div></dl>}
      <p>권리·연결·무결성을 확인하지 못하면 3D와 저장 수치를 제거합니다. 재생은 원 저장 시점만 이동합니다.</p>
    </section>
  </main>;
}
