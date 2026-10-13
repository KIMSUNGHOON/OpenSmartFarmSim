import {readFileSync,writeFileSync,existsSync,mkdirSync,rmSync,openSync,closeSync,renameSync} from 'node:fs';
import {spawn} from 'node:child_process';
import {createHash} from 'node:crypto';
import {setTimeout as delay} from 'node:timers/promises';

const config=JSON.parse(readFileSync(process.argv[2],'utf8'));
const request=JSON.parse(readFileSync(config.request_file,'utf8'));
const assert=(value,message)=>{if(!value)throw Error(message);};
const save=(name,value)=>writeFileSync(config.directory+'/'+name,JSON.stringify(value,null,2),{mode:0o600,flag:'wx'});
const profile=config.directory+'/chromium-profile';mkdirSync(profile,{mode:0o700});
const log=openSync(config.directory+'/chromium.private.log','wx',0o600);
const child=spawn(config.chromium,['--headless','--no-sandbox','--disable-dev-shm-usage',
  '--disable-background-networking','--disable-extensions','--disable-component-update','--disable-sync',
  '--disable-gpu-rasterization','--disable-gpu-compositing',
  '--disable-features=Translate,OptimizationHints,MediaRouter','--enable-unsafe-swiftshader',
  '--single-process','--no-zygote','--num-raster-threads=1','--use-gl=angle','--use-angle=swiftshader-webgl',
  '--js-flags=--jitless --max-old-space-size=24 --max-semi-space-size=1 --expose-gc',
  '--user-data-dir='+profile,'--remote-debugging-address=127.0.0.1','--remote-debugging-port=0','about:blank'],
  {stdio:['ignore',log,log]});
let socket,session,sequence=0,phase='starting',jobId=null,captureInstalled=false;
const pending=new Map(),methods=new Map(),responses=[],networkResponses=[],errors=[],warnings=[],frames=[];
const started=Date.now();
function memory(next){if(next)phase=next;const target=config.directory+'/node-memory.private.json';
  writeFileSync(target+'.tmp',JSON.stringify({stage:phase,memory:process.memoryUsage()}),{mode:0o600});renameSync(target+'.tmp',target);}
const timer=setInterval(()=>{memory();globalThis.gc?.();},250);timer.unref();memory();
async function until(action,message,seconds=45){const end=Date.now()+seconds*1000;
  while(true){if(captureInstalled)await flushHTTP();const value=await action();if(value)return value;assert(child.exitCode===null,'Chromium exited');
    assert(Date.now()<end,message);await delay(200);}}
function send(method,params={},attached=true){const id=++sequence;
  return new Promise((resolve,reject)=>{pending.set(id,{resolve,reject});
    socket.send(JSON.stringify({id,method,params,...(attached?{sessionId:session}:{})}));});}
async function evaluate(expression){const value=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true});
  assert(!value.exceptionDetails,'browser evaluation failed');return value.result.value;}
async function flushHTTP(){
  const value=await evaluate(`(()=>{const source=globalThis.__ownedHTTPCloneEvidence;
    if(!source)return {pending:0,count:0,bytes:0,errors:[],entries:[]};
    const entries=source.entries.flatMap((entry,index)=>!entry.flushed&&(typeof entry.body==='string'||entry.aborted)?[{...entry,index}]:[]);
    for(const entry of source.entries)if(typeof entry.body==='string'||entry.aborted){delete entry.body;entry.flushed=true;}
    return {pending:source.pending,count:source.entries.length,bytes:source.bytes,errors:source.errors,entries};})()`);
  assert(!value.errors.length,'actual fetch response clone failed');
  for(const entry of value.entries){
    const {body,index,...record}=entry;delete record.flushed;
    if(typeof body==='string'){
      const raw=Buffer.from(body),name='wire-'+index+'.private.json';
      writeFileSync(config.directory+'/'+name,raw,{mode:0o400,flag:'wx'});
      record.wire_file=name;record.body_sha256=createHash('sha256').update(raw).digest('hex');
    }else assert(record.aborted&&record.method==='GET','unexpected missing fetch body');
    responses[index]=record;
  }
  return value;
}
function element(kind,text){return `(()=>{const text=${JSON.stringify(text)},kind=${JSON.stringify(kind)};
  if(kind==='label'){const label=[...document.querySelectorAll('label')].find(e=>e.textContent.trim()===text);
    return label?.control||[...document.querySelectorAll('[aria-label]')].find(e=>e.getAttribute('aria-label')===text);}
  const selector=kind==='button'?'button':kind==='heading'?'h1,h2,h3,h4,[role=heading]':kind==='status'?'[role=status]':kind==='alert'?'[role=alert]':'summary';
  return [...document.querySelectorAll(selector)].find(e=>e.textContent.trim()===text);})()`;}
async function has(kind,text){return evaluate(`Boolean(${element(kind,text)})`);}
async function click(kind,text){const point=await until(()=>evaluate(`(()=>{const e=${element(kind,text)};
  if(!e||e.disabled)return null;e.scrollIntoView({block:'center'});const r=e.getBoundingClientRect();
  return r.width&&r.height?{x:r.x+r.width/2,y:r.y+r.height/2}:null;})()`),'control unavailable: '+text);
  await send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});
  await send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});}
async function fill(label,value){await click('label',label);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'a',code:'KeyA',modifiers:2,windowsVirtualKeyCode:65});
  await send('Input.insertText',{text:value});}
const inputValue=label=>evaluate(`(${element('label',label)})?.value`);
function frameDOM(prefix){const root=document.querySelector(prefix?'.joint-prefix-viewer':'.ventilation-viewer');if(!root)return null;
  const canvas=root.querySelector('.coupled-canvas'),at=root.dataset.selectedAt,chart=root.querySelector('.joint-history');
  if(!canvas||canvas.dataset.sceneAt!==at||Number(canvas.dataset.drawCalls)<=0||chart?.dataset.selectedAt!==at)return null;
  const quantities=selector=>Object.fromEntries([...root.querySelectorAll(selector+' [data-metric]')].map(q=>
    [q.dataset.metric,{value:Number(q.dataset.rawValue),unit:q.querySelector('small').textContent.trim()}]));
  return {at,scene_at:canvas.dataset.sceneAt,chart_at:chart.dataset.selectedAt,
    reference:JSON.parse(prefix?root.closest('.joint-prefix').dataset.prefixReference:root.dataset.reference),
    draw_calls:Number(canvas.dataset.drawCalls),leaf_surface_area:Number(canvas.dataset.leafSurfaceArea),
    drawing:JSON.parse(canvas.dataset.cohortDrawing),cohorts:[...root.querySelectorAll('.coupled-cohort-table tbody tr')]
      .map(row=>[...row.querySelectorAll('td')].map(q=>Number(q.dataset.rawValue))),
    quantities:quantities(prefix?'dl[aria-label="확정 작물·기후 원값"]':'dl[aria-label="작물·기후 원값"]'),
    ventilation:JSON.parse(root.querySelector('[data-ventilation]').dataset.ventilation),
    ledgers:quantities(prefix?'dl[aria-label="확정 누적25장부"]':'dl[aria-label="누적25장부"]'),
    residuals:quantities(prefix?'dl[aria-label="확정 수지 잔차"]':'dl[aria-label="수지 잔차"]')};}
const capture=(prefix=true)=>evaluate(`(${frameDOM.toString()})(${prefix})`);
async function screenshot(name){await send('HeapProfiler.collectGarbage');
  await evaluate(`document.querySelector('.coupled-top-grid')?.scrollIntoView({block:'start'})`);
  const value=await send('Page.captureScreenshot',{format:'png'});
  writeFileSync(config.directory+'/'+name+'.private.png',Buffer.from(value.data,'base64'),{mode:0o600,flag:'wx'});}
async function rights(name){writeFileSync(config.directory+'/'+name,'',{mode:0o600,flag:'wx'});
  await until(()=>existsSync(config.directory+'/'+name+'-ack'),'current rights acknowledgement missing',10);}
async function reconnect(){await click('button','조회 연결 해제');
  const labels={job_id:'계산 작업 ID',scenario_id:'계산 농장 시나리오 ID',scenario_revision:'계산 농장 판본',
    registration_sha256:'계산 농장 등록 SHA-256',crop_id:'계산 작물 ID'};
  for(const [key,value] of Object.entries({job_id:jobId,...request.farm}))await fill(labels[key],value);
  await click('button','기존 계산 조회');}
async function event(value){const p=value.params;
  if(value.method==='Network.requestWillBeSent')methods.set(p.requestId,p.request.method);
  if(value.method==='Network.responseReceived'){
    const url=new URL(p.response.url);if(!url.pathname.startsWith('/v1/'))return;
    assert(url.origin===config.origin,'unexpected API response origin');
    networkResponses.push({path:url.pathname,query:url.search,status:p.response.status,method:methods.get(p.requestId),requestId:p.requestId});
  }
  if(value.method==='Network.loadingFailed'){
    const reply=networkResponses.find(r=>r.requestId===p.requestId);
    if(reply){reply.failed=true;reply.canceled=Boolean(p.canceled);}
  }
  if(value.method==='Runtime.exceptionThrown')errors.push(p.exceptionDetails.text);
  if(value.method==='Runtime.consoleAPICalled'&&['warning','error'].includes(p.type))warnings.push(p.type);
}
try{
  await until(()=>existsSync(profile+'/DevToolsActivePort'),'Chromium debugging endpoint missing',15);
  const [port,path]=readFileSync(profile+'/DevToolsActivePort','utf8').trim().split('\n');
  socket=new WebSocket('ws://127.0.0.1:'+port+path);
  await new Promise((resolve,reject)=>{socket.addEventListener('open',resolve,{once:true});socket.addEventListener('error',reject,{once:true});});
  socket.addEventListener('close',()=>{for(const entry of pending.values())entry.reject(Error('CDP closed'));pending.clear();});
  socket.addEventListener('message',e=>{const value=JSON.parse(e.data);
    if(value.id){const entry=pending.get(value.id);pending.delete(value.id);
      if(value.error)entry?.reject(Error('CDP command rejected'));else entry?.resolve(value.result);}
    else event(value).catch(()=>errors.push('protocol_event_failed'));});
  const target=await send('Target.createTarget',{url:'about:blank'},false);
  session=(await send('Target.attachToTarget',{targetId:target.targetId,flatten:true},false)).sessionId;
  for(const domain of ['Page','Runtime'])await send(domain+'.enable');
  await send('Network.enable',{maxTotalBufferSize:1,maxResourceBufferSize:1});
  await send('Page.addScriptToEvaluateOnNewDocument',{source:`(()=>{
    const original=globalThis.fetch,evidence={pending:0,bytes:0,entries:[],errors:[]};
    Object.defineProperty(globalThis,'__ownedHTTPCloneEvidence',{value:evidence});
    globalThis.fetch=async function(...args){const response=await Reflect.apply(original,this,args),url=new URL(response.url);
      if(!url.pathname.startsWith('/v1/'))return response;
      const input=args[0],entry={path:url.pathname,query:url.search,status:response.status,
        method:args[1]?.method||(input instanceof Request?input.method:'GET')};
      evidence.entries.push(entry);evidence.pending++;
      response.clone().text().then(body=>{const size=new TextEncoder().encode(body).length;evidence.bytes+=size;
        if(size>2*1024**2||evidence.bytes>4*1024**2||evidence.entries.length>64)throw Error('HTTP capture limit');entry.body=body;
      }).catch(error=>{if(error.name==='AbortError'&&entry.method==='GET'){entry.aborted=true;entry.abort_reason='AbortError';}
        else evidence.errors.push('unexpected_fetch_clone_failure');}).finally(()=>evidence.pending--);
      return response;};})()`});
  captureInstalled=true;
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:600,deviceScaleFactor:1,mobile:false});
  await send('Emulation.setTimezoneOverride',{timezoneId:'Asia/Seoul'});
  memory('page');await send('Page.navigate',{url:config.origin+'/#ventilation-execution'});
  await until(()=>has('label','접근 토큰'),'product connection form missing');
  if(!await evaluate(`document.querySelector('.connection')?.open`))await click('summary','내부 시험 연결');
  await fill('접근 토큰',config.token);await click('button','연결 설정');
  assert(await inputValue('계산 모델')==='ventilation','wrong product model');
  const file=await until(async()=>{const doc=await send('DOM.getDocument');
    const found=await send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'input[type=file]'});
    return found.nodeId?found:null;},'product request file input missing');
  await send('DOM.setFileInputFiles',{nodeId:file.nodeId,files:[config.request_file]});
  await click('button','계산 접수');
  await until(async()=>{const value=await inputValue('계산 작업 ID');
    if(/^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$/.test(value)){jobId=value;return true;}return false;},'admitted job not displayed');
  memory('running');let terminal=false,canceled=false,selectionVerified=false;
  const end=Date.now()+420000;
  while(Date.now()<end){
    await flushHTTP();
    const frame=await capture();
    if(frame&&!frames.some(old=>old.at===frame.at&&old.reference.selector.publication_sequence===frame.reference.selector.publication_sequence)){
      frame.observed_at=new Date().toISOString();frame.selection='automatic_latest';frames.push(frame);
      save('observed-frame-'+frames.length+'.private.json',frame);
      if(frames.length===1){
        if(config.mode==='cancel'){
          await click('button','서버 계산 취소');
          await until(()=>evaluate(`Boolean([...document.querySelectorAll('[role=status]')].find(e=>/^취소 요청 수락 · 취소 응답 당시:/.test(e.textContent.trim())))`),'cancellation not accepted');
          await until(()=>has('heading','취소됨'),'cancellation not settled',90);
          assert(await evaluate(`document.querySelectorAll('.coupled-canvas').length`)===0,'canceled scene remains');
          canceled=true;break;
        }
        await screenshot('running');
        if(Number(await evaluate(`(${element('label','확정 생장 시점 선택')})?.max`))>0){
          await click('label','확정 생장 시점 선택');await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Home',code:'Home',windowsVirtualKeyCode:36});
          await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Home',code:'Home',windowsVirtualKeyCode:36});
          const first=await until(()=>capture(),'manual saved frame missing',10);first.selection='manual_saved_point';frames.push(first);
          save('observed-frame-'+frames.length+'.private.json',first);selectionVerified=true;await click('button','최신 확정 시점');
        }
      }
    }
    if(await has('button','같은 저장 결과 3D 열기')){terminal=true;break;}
    await delay(300);
  }
  assert(frames.length>0,'no running confirmed WebGL frame');assert(!errors.length,'product JavaScript error');
  const result={mode:config.mode,job_id:jobId,running_frames:frames,selection_verified:selectionVerified,
    cancel_accepted:canceled,scene_cleared:canceled,pageerrors:errors,responses,warnings,test_pause:false};
  if(config.mode!=='cancel'){
    assert(terminal,'terminal result missing');memory('terminal');await click('button','같은 저장 결과 3D 열기');
    result.terminal_frame=await until(()=>capture(false),'terminal WebGL missing');
    result.result_id=await evaluate(`document.querySelector('.ventilation-viewer').dataset.resultId`);
    await send('Emulation.setDeviceMetricsOverride',{width:800,height:600,deviceScaleFactor:1,mobile:false});await screenshot('terminal');
    await reconnect();await until(()=>has('button','같은 저장 결과 3D 열기'),'same job reconnect missing');
    await click('button','같은 저장 결과 3D 열기');await until(()=>capture(false),'reconnected WebGL missing');
    assert(await evaluate(`document.querySelector('.ventilation-viewer').dataset.resultId`)===result.result_id,'reconnect result changed');result.reconnected=true;
    memory('rights');await rights('rights-revoke');await click('button','현재 권리 다시 조회');
    await until(()=>evaluate(`document.querySelectorAll('[role=alert]').length`),'current rights alert missing');
    assert(networkResponses.some(r=>r.status===422&&r.path.startsWith('/v1/crop-greenhouse-ventilation-research-results/')),'actual rights denial missing');
    assert(await evaluate(`document.querySelectorAll('.coupled-canvas').length`)===0,'revoked scene remains');result.rights_cleared=true;await screenshot('rights-blocked');
    await rights('rights-restore');await click('button','저장 연구 조회');
    result.restored_frame=await until(()=>capture(false),'restored WebGL missing');
    assert(await evaluate(`document.querySelector('.ventilation-viewer').dataset.resultId`)===result.result_id,'restored result changed');result.rights_restored=true;
    memory('mobile');await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:false});
    assert(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'),'mobile overflow');await screenshot('mobile');
  }else assert(canceled,'cancel did not settle');
  const captured=await until(async()=>{const value=await flushHTTP();return value.pending===0?value:null;},'HTTP body capture incomplete',15);
  assert(responses.length===captured.count&&responses.every(r=>r.wire_file||r.aborted),'fetch body capture incomplete');
  assert(!errors.length,'browser evidence failed');
  result.network_responses=networkResponses.map(({requestId,...record})=>record);
  result.response_capture={mechanism:'actual fetch Response.clone; CDP transport',requests_added:0,bytes:captured.bytes,
    product_aborted_GETs:responses.filter(r=>r.aborted).length};
  result.wall_seconds=(Date.now()-started)/1000;save('browser-result.private.json',result);
  console.log(JSON.stringify({mode:config.mode,running_frames:frames.length,pageerrors:0,wall_seconds:result.wall_seconds}));
}catch(error){save('browser-failure.private.json',{message:error.message,job_id:jobId,running_frames:frames,pageerrors:errors,responses,
    network_responses:networkResponses.map(({requestId,...record})=>record)});
  if(session)try{await screenshot('failure');}catch{}throw error;
}finally{
  memory('closing');clearInterval(timer);
  if(socket?.readyState===WebSocket.OPEN)try{await send('Browser.close',{},false);}catch{}
  const end=Date.now()+15000;while(child.exitCode===null&&Date.now()<end)await delay(100);
  socket?.close();closeSync(log);
  assert(child.exitCode!==null,'Chromium did not close');rmSync(profile,{recursive:true,force:true});
}
