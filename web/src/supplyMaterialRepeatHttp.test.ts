import {expect,it,vi} from 'vitest';
import {createHash} from 'node:crypto';
import type {RepeatRead} from './supplyMaterialRepeatReplay';

// Own opaque byte fixtures: mock transport, not issued artifacts or TLS evidence.
const hash=(raw:Uint8Array)=>createHash('sha256').update(raw).digest('hex');
function stream(raw:Uint8Array,mutatePrevious=false):ReadableStream<Uint8Array>{
 const parts=[raw.slice(0,47),raw.slice(47,213),raw.slice(213)];
 let next=0,previous:Uint8Array|undefined;
 return new ReadableStream<Uint8Array>({pull(controller){
  if(mutatePrevious)previous?.fill(0);
  const part=parts[next++];
  if(part===undefined){controller.close();return;}
  previous=part;controller.enqueue(part);
 }},{highWaterMark:0});
}

it('reads fixed protected paths as exact copied bytes and releases streamed bodies (own mock transport)',async()=>{
 const utf8=new TextEncoder();
 const manifest=utf8.encode('{"own":"opaque HTTP transport manifest","counter":'+'1'+'0'.repeat(309)+',"float":1.0,"null":null}\n');
 const frame=utf8.encode('{"own":"opaque HTTP transport frame","counter":'+'1'+'0'.repeat(308)+'1'+',"float":1e-3,"signed":-0.0}\n');
 const expectedHashes=['4efae4ece041a3f54c8c0b7825fa62dee2beb883f9ed0ae859eb504e9dfdeb36',
  'dfc70f3fb82bc856b8212471250fa6d045e954c0e81a781816bdb0a55ab043b6'];
 for(const [index,raw] of [manifest,frame].entries()){
  expect(raw.byteLength).toBe(386);expect(hash(raw)).toBe(expectedHashes[index]);
  const fixture=stream(raw),reader=fixture.getReader(),parts:Uint8Array[]=[];
  try{for(;;){const part=await reader.read();if(part.done)break;parts.push(part.value);}}
  finally{await reader.cancel();reader.releaseLock();}
  const joined=new Uint8Array(parts.reduce((size,part)=>size+part.byteLength,0));let offset=0;
  for(const part of parts){joined.set(part,offset);offset+=part.byteLength;}
  expect(joined).toEqual(raw);expect(fixture.locked).toBe(false);
 }
 const cancel=vi.spyOn(ReadableStreamDefaultReader.prototype,'cancel');
 const release=vi.spyOn(ReadableStreamDefaultReader.prototype,'releaseLock');
 const caller=new AbortController();
 const added=vi.spyOn(caller.signal,'addEventListener');
 const removed=vi.spyOn(caller.signal,'removeEventListener');
 try{
  // Resolve the feature only after both own byte/hash and real-stream gates.
  const modulePath='./supplyMaterialRepeatHttp';
  const api:{createSupplyMaterialRepeatRead:(token:string,fetcher?:typeof fetch)=>RepeatRead}=
   await import(/* @vite-ignore */ modulePath);
  expect(typeof api.createSupplyMaterialRepeatRead).toBe('function');
  const replies:Response[]=[];
  const token='own-repeat-http-fixture-'+'t'.repeat(32);
  const fetcher=vi.fn<typeof fetch>().mockImplementation(async(input,init)=>{
   expect(init?.method).toBe('GET');expect(init?.credentials).toBe('omit');
   expect(init?.redirect).toBe('error');expect(init?.cache).toBe('no-store');
   expect(init?.body).toBeUndefined();
   expect(new Headers(init?.headers).get('authorization')).toBe('Bearer '+token);
   expect(init?.signal).toBeInstanceOf(AbortSignal);expect(init?.signal).not.toBe(caller.signal);
   expect(init?.signal?.aborted).toBe(false);expect(String(input)).not.toContain(token);
   expect(['/v1/research/material-repeat/manifest','/v1/research/material-repeat/frames/511']).toContain(input);
   const raw=input==='/v1/research/material-repeat/manifest'?manifest:frame;
   const response=new Response(stream(raw,true),{status:200,headers:{
    'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store'}});
   replies.push(response);return response;
  });
  const read=api.createSupplyMaterialRepeatRead(token,fetcher);
  const first=await read({kind:'manifest'},caller.signal);
  const second=await read({kind:'frame',index:511},caller.signal);
  expect(first).toBeInstanceOf(Uint8Array);expect(second).toBeInstanceOf(Uint8Array);
  expect(first).toEqual(manifest);expect(second).toEqual(frame);
  expect(hash(first)).toBe(expectedHashes[0]);expect(hash(second)).toBe(expectedHashes[1]);
  expect(first).not.toBe(manifest);expect(second).not.toBe(frame);
  first.fill(0);second.fill(0);
  expect(hash(manifest)).toBe(expectedHashes[0]);expect(hash(frame)).toBe(expectedHashes[1]);
  expect(fetcher.mock.calls.map(call=>call[0])).toEqual([
   '/v1/research/material-repeat/manifest','/v1/research/material-repeat/frames/511']);
  expect(replies).toHaveLength(2);
  for(const response of replies){expect(response.bodyUsed).toBe(true);expect(response.body?.locked).toBe(false);}
  expect(cancel).toHaveBeenCalledTimes(2);expect(release).toHaveBeenCalledTimes(2);
  expect(added).toHaveBeenCalledTimes(2);expect(removed).toHaveBeenCalledTimes(2);
  for(let index=0;index<2;index++){
   expect(added.mock.calls[index]?.[0]).toBe('abort');
   expect(removed.mock.calls[index]?.[0]).toBe('abort');
   expect(removed.mock.calls[index]?.[1]).toBe(added.mock.calls[index]?.[1]);
  }
  expect(caller.signal.aborted).toBe(false);
 }finally{vi.restoreAllMocks();}
});


// Own mock transport only: these rows do not exercise a backend or TLS connection.
import {ApiError as _httpApiError} from './api-validation';

async function _httpFactory(){
 const modulePath='./supplyMaterialRepeatHttp';
 const api:{createSupplyMaterialRepeatRead:(token:string,fetcher?:typeof fetch)=>RepeatRead}=
  await import(/* @vite-ignore */ modulePath);
 expect(typeof api.createSupplyMaterialRepeatRead).toBe('function');
 return api.createSupplyMaterialRepeatRead;
}

async function _httpRejected(operation:()=>unknown|PromiseLike<unknown>,code:string,status:number|null=null){
 let caught:unknown;
 try{await operation();}catch(value){caught=value;}
 expect(caught).toBeInstanceOf(_httpApiError);
 if(!(caught instanceof _httpApiError))throw new Error('expected a fixed transport rejection');
 expect({name:caught.name,code:caught.code,status:caught.status,message:caught.message})
  .toEqual({name:'ApiError',code,status,message:code});
 expect(caught.cause).toBeUndefined();
 return caught;
}

function _httpBody(parts:readonly Uint8Array[]){
 const state={pulls:0,cancels:0};let index=0;
 const body=new ReadableStream<Uint8Array>({
  pull(controller){
   state.pulls++;const part=parts[index++];
   if(part===undefined)controller.close();else controller.enqueue(part);
  },
  cancel(){state.cancels++;}
 },{highWaterMark:0});
 return {body,state};
}

function _httpResponse(body:ReadableStream<Uint8Array>|null,status=200,headers:HeadersInit={
 'Content-Type':'application/json','Cache-Control':'no-store'
}){return new Response(body,{status,headers});}

function _httpReply(raw:Uint8Array){return _httpResponse(_httpBody([raw.slice()]).body);}

it('rejects invalid transport inputs without fetching and snapshots the fixed path before await (own mock transport)',async()=>{
 const factory=await _httpFactory(),raw=Uint8Array.of(0x30);
 const minimum='t'.repeat(32),maximum='u'.repeat(128);
 let next=_httpReply(raw);
 const fetcher=vi.fn<typeof fetch>().mockImplementation(async()=>next);
 const signal=new AbortController().signal;
 const positive=async(token:string)=>{
  next=_httpReply(raw);const previous=fetcher.mock.calls.length;
  const actual=await factory(token,fetcher)({kind:'manifest'},signal);
  expect(actual).toEqual(raw);expect(actual).not.toBe(raw);
  expect(fetcher).toHaveBeenCalledTimes(previous+1);
  expect(new Headers(fetcher.mock.calls.at(-1)?.[1]?.headers).get('authorization')).toBe('Bearer '+token);
 };
 await positive(minimum);
 const invalidTokens:unknown[]=[null,'t'.repeat(31),'t'.repeat(129),'t'.repeat(31)+'!'];
 for(const token of invalidTokens){
  const previous=fetcher.mock.calls.length;
  await _httpRejected(()=>Reflect.apply(factory,undefined,[token,fetcher]),'auth_required');
  expect(fetcher).toHaveBeenCalledTimes(previous);
 }
 const read=factory(minimum,fetcher);
 const invalidSelections:unknown[]=[null,{kind:'other'},
  ...[true,'0',NaN,Infinity,-1,0.5,512].map(index=>({kind:'frame',index}))];
 for(const selection of invalidSelections){
  const previous=fetcher.mock.calls.length;
  await _httpRejected(()=>Reflect.apply(read,undefined,[selection,signal]),'response_rejected');
  expect(fetcher).toHaveBeenCalledTimes(previous);
 }
 const canceled=new AbortController();canceled.abort();
 const beforeCanceled=fetcher.mock.calls.length;
 await _httpRejected(()=>read({kind:'manifest'},canceled.signal),'request_canceled');
 expect(fetcher).toHaveBeenCalledTimes(beforeCanceled);
 let deliver:(response:Response)=>void=()=>{throw new Error('deferred fixture was not initialized');};
 const deferred=new Promise<Response>(resolve=>{deliver=resolve;});
 const delayed=vi.fn<typeof fetch>().mockImplementation(()=>deferred);
 const selection:{kind:'frame';index:number}={kind:'frame',index:511};
 const pending=factory(minimum,delayed)(selection,signal);
 expect(delayed).toHaveBeenCalledTimes(1);
 expect(delayed.mock.calls[0]?.[0]).toBe('/v1/research/material-repeat/frames/511');
 selection.index=0;deliver(_httpReply(raw));
 expect(await pending).toEqual(raw);
 expect(delayed.mock.calls[0]?.[0]).toBe('/v1/research/material-repeat/frames/511');
 await positive(maximum);
 expect(fetcher.mock.calls.map(call=>call[0])).toEqual([
  '/v1/research/material-repeat/manifest','/v1/research/material-repeat/manifest']);
});

it('rejects HTTP and media faults without reading error bodies or exposing foreign errors (own mock transport)',async()=>{
 const factory=await _httpFactory(),token='p'.repeat(32),raw=Uint8Array.of(0x30);
 const marker='own-sensitive-transport-error';
 let next:Response|Error=_httpReply(raw);
 const fetcher=vi.fn<typeof fetch>().mockImplementation(async()=>{
  if(next instanceof Error)throw next;return next;
 });
 const read=factory(token,fetcher),signal=new AbortController().signal;
 const recovery=async()=>{
  next=_httpReply(raw);const previous=fetcher.mock.calls.length;
  expect(await read({kind:'manifest'},signal)).toEqual(raw);
  expect(fetcher).toHaveBeenCalledTimes(previous+1);
 };
 const faults:{name:string;status:number;code:string;errorStatus:number|null;
  mime?:string;cache?:string|null;redirected?:boolean}[]=[
  {name:'unauthenticated',status:401,code:'auth_required',errorStatus:401},
  {name:'denied',status:403,code:'access_denied',errorStatus:403},
  {name:'unavailable',status:404,code:'not_available',errorStatus:404},
  {name:'conflict',status:409,code:'intent_conflict',errorStatus:409},
  {name:'HTTP oversized',status:413,code:'too_large',errorStatus:413},
  {name:'invalid request',status:422,code:'invalid_request',errorStatus:422},
  {name:'server hold',status:503,code:'server_unavailable',errorStatus:503},
  {name:'unexpected success',status:201,code:'response_rejected',errorStatus:201},
  {name:'wrong media',status:200,code:'response_rejected',errorStatus:null,mime:'text/plain'},
  {name:'missing no-store',status:200,code:'response_rejected',errorStatus:null,cache:null},
  {name:'followed redirect',status:200,code:'response_rejected',errorStatus:null,redirected:true}
 ];
 await recovery();
 for(const fault of faults){
  const fixture=_httpBody([new TextEncoder().encode(marker)]);
  const headers=new Headers({'Content-Type':fault.mime??'application/json'});
  if(fault.cache!==null)headers.set('Cache-Control',fault.cache??'no-store');
  const response=_httpResponse(fixture.body,fault.status,headers);
  if(fault.redirected)Object.defineProperty(response,'redirected',{value:true});
  next=response;const previous=fetcher.mock.calls.length;
  const error=await _httpRejected(()=>read({kind:'manifest'},signal),fault.code,fault.errorStatus);
  expect(String(error)).not.toContain(marker);
  expect(fetcher, fault.name).toHaveBeenCalledTimes(previous+1);
  expect(fixture.state).toEqual({pulls:0,cancels:1});
  expect(response.body?.locked).toBe(false);
  await recovery();
 }
 for(const external of [new Error(marker),new _httpApiError(marker,499)]){
  next=external;const previous=fetcher.mock.calls.length;
  const error=await _httpRejected(()=>read({kind:'manifest'},signal),'network_unresolved');
  expect(error).not.toBe(external);expect(String(error)).not.toContain(marker);
  expect(fetcher).toHaveBeenCalledTimes(previous+1);
  await recovery();
 }
});

it('uses actual streamed bytes for the inclusive2MiB bound and releases rejected bodies (own mock transport)',async()=>{
 const factory=await _httpFactory(),token='b'.repeat(32),one=Uint8Array.of(0x30),maximum=2097152;
 let next=_httpReply(one);
 const fetcher=vi.fn<typeof fetch>().mockImplementation(async()=>next);
 const read=factory(token,fetcher),signal=new AbortController().signal;
 const recovery=async()=>{
  next=_httpReply(one);const actual=await read({kind:'manifest'},signal);
  expect(actual).toEqual(one);expect(actual.byteLength).toBe(1);expect(actual).not.toBe(one);
 };
 await recovery();
 const full=new Uint8Array(maximum).fill(0x20);full[0]=0x30;
 const fullHash='d67b18148ff8ecc6e75a0697c29c84bfed6b137394252c3a384590ffcc5d8fbf';
 expect(hash(full)).toBe(fullHash);
 const accepted=_httpBody([full.subarray(0,12345),full.subarray(12345)]);
 next=_httpResponse(accepted.body);
 const actual=await read({kind:'frame',index:0},signal);
 expect(actual.byteLength).toBe(maximum);expect(hash(actual)).toBe(fullHash);expect(Object.is(actual,full)).toBe(false);
 expect(accepted.body.locked).toBe(false);
 actual[0]=0x31;expect(hash(full)).toBe(fullHash);
 const oversized=_httpBody([new Uint8Array(maximum).fill(0x20),Uint8Array.of(0x30),Uint8Array.of(0x31)]);
 next=_httpResponse(oversized.body);
 await _httpRejected(()=>read({kind:'manifest'},signal),'too_large');
 expect(oversized.state).toEqual({pulls:2,cancels:1});expect(oversized.body.locked).toBe(false);
 await recovery();
 const empty=_httpBody([]);next=_httpResponse(empty.body);
 await _httpRejected(()=>read({kind:'manifest'},signal),'response_rejected');
 expect(empty.state).toEqual({pulls:1,cancels:0});expect(empty.body.locked).toBe(false);
 await recovery();
 const absent=_httpResponse(null);expect(absent.body).toBeNull();next=absent;
 await _httpRejected(()=>read({kind:'manifest'},signal),'response_rejected');
 await recovery();
 const nonByteState={pulls:0,cancels:0};
 const nonByte=new ReadableStream<Uint8Array>({
  pull(controller){nonByteState.pulls++;Reflect.apply(controller.enqueue,controller,['own non-byte chunk']);},
  cancel(){nonByteState.cancels++;}
 },{highWaterMark:0});
 next=_httpResponse(nonByte);
 await _httpRejected(()=>read({kind:'manifest'},signal),'response_rejected');
 expect(nonByteState).toEqual({pulls:1,cancels:1});expect(nonByte.locked).toBe(false);
 await recovery();
});


// Controlled clocks below test software deadlines, not real HTTP/TLS elapsed time.
function _httpBGate<T>(){
 let complete:(value:T)=>void=()=>{throw new Error('deferred fixture was not initialized');};
 const promise=new Promise<T>(resolve=>{complete=resolve;});
 return {promise,resolve:(value:T)=>complete(value)};
}

function _httpBClock(){
 vi.useFakeTimers({toFake:['setTimeout','clearTimeout']});
 let now=0;vi.spyOn(performance,'now').mockImplementation(()=>now);
 return {
  now:()=>now,
  move:(value:number)=>{expect(value).toBeGreaterThanOrEqual(now);now=value;},
  tick:async(delta:number)=>{now+=delta;await vi.advanceTimersByTimeAsync(delta);},
  restore:()=>{vi.restoreAllMocks();vi.useRealTimers();}
 };
}

function _httpBCaller(){
 const controller=new AbortController();
 return {controller,added:vi.spyOn(controller.signal,'addEventListener'),
  removed:vi.spyOn(controller.signal,'removeEventListener')};
}

function _httpBReleased(caller:ReturnType<typeof _httpBCaller>){
 expect(caller.added).toHaveBeenCalledTimes(1);expect(caller.removed).toHaveBeenCalledTimes(1);
 expect(caller.added.mock.calls[0]?.[0]).toBe('abort');expect(caller.removed.mock.calls[0]?.[0]).toBe('abort');
 expect(caller.removed.mock.calls[0]?.[1]).toBe(caller.added.mock.calls[0]?.[1]);
 expect(vi.getTimerCount()).toBe(0);
}

function _httpBLateReply(){
 const canceled=_httpBGate<void>(),state={pulls:0,cancels:0};
 const body=new ReadableStream<Uint8Array>({
  pull(controller){state.pulls++;controller.enqueue(Uint8Array.of(0x30));},
  cancel(){state.cancels++;canceled.resolve(undefined);}
 },{highWaterMark:0});
 return {response:_httpResponse(body),body,state,canceled:canceled.promise};
}

function _httpBStalledBody(first?:Uint8Array){
 const ready=_httpBGate<void>(),finished=_httpBGate<void>(),state={pulls:0,cancels:0};
 const body=new ReadableStream<Uint8Array>({
  async pull(controller){
   state.pulls++;
   if(first!==undefined&&state.pulls===1){controller.enqueue(first);return;}
   ready.resolve(undefined);await finished.promise;
  },
  cancel(){state.cancels++;finished.resolve(undefined);}
 },{highWaterMark:0});
 return {body,state,ready:ready.promise};
}

async function _httpBRecovery(factory:Awaited<ReturnType<typeof _httpFactory>>){
 const caller=_httpBCaller(),raw=Uint8Array.of(0x30),response=_httpReply(raw);
 const fetcher=vi.fn<typeof fetch>().mockResolvedValue(response);
 const actual=await factory('r'.repeat(32),fetcher)({kind:'manifest'},caller.controller.signal);
 expect(actual).toEqual(raw);expect(Object.is(actual,raw)).toBe(false);
 expect(fetcher).toHaveBeenCalledTimes(1);expect(response.body?.locked).toBe(false);
 expect(caller.controller.signal.aborted).toBe(false);_httpBReleased(caller);
}

it('keeps caller cancellation authoritative during ignored fetch and native stream waits (own mock transport)',async()=>{
 const factory=await _httpFactory(),clock=_httpBClock(),token='c'.repeat(32);
 try{
  const caller=_httpBCaller(),gate=_httpBGate<Response>();let internal:AbortSignal|null|undefined;
  const fetcher=vi.fn<typeof fetch>().mockImplementation((_path,init)=>{internal=init?.signal;return gate.promise;});
  const pending=factory(token,fetcher)({kind:'manifest'},caller.controller.signal);
  const rejected=_httpRejected(()=>pending,'request_canceled');
  expect(internal?.aborted).toBe(false);caller.controller.abort();await rejected;
  expect(internal?.aborted).toBe(true);expect(fetcher).toHaveBeenCalledTimes(1);_httpBReleased(caller);
  const late=_httpBLateReply();gate.resolve(late.response);await late.canceled;
  expect(late.state).toEqual({pulls:0,cancels:1});expect(late.body.locked).toBe(false);
  await _httpBRecovery(factory);
  const streamingCaller=_httpBCaller(),streaming=_httpBStalledBody();let streamSignal:AbortSignal|null|undefined;
  const streamingFetch=vi.fn<typeof fetch>().mockImplementation(async(_path,init)=>{
   streamSignal=init?.signal;return _httpResponse(streaming.body);
  });
  const streamPending=factory(token,streamingFetch)({kind:'frame',index:0},streamingCaller.controller.signal);
  const streamRejected=_httpRejected(()=>streamPending,'request_canceled');
  await streaming.ready;expect(streaming.state.pulls).toBe(1);expect(streaming.body.locked).toBe(true);
  streamingCaller.controller.abort();await streamRejected;
  expect(streamSignal?.aborted).toBe(true);expect(streamingFetch).toHaveBeenCalledTimes(1);
  expect(streaming.state).toEqual({pulls:1,cancels:1});expect(streaming.body.locked).toBe(false);
  _httpBReleased(streamingCaller);await _httpBRecovery(factory);
 }finally{clock.restore();}
});

it('keeps one original30 budget across pending fetch and body progress (own mock transport)',async()=>{
 const factory=await _httpFactory(),clock=_httpBClock(),token='d'.repeat(32);
 try{
  const caller=_httpBCaller(),gate=_httpBGate<Response>();let internal:AbortSignal|null|undefined;
  const fetcher=vi.fn<typeof fetch>().mockImplementation((_path,init)=>{internal=init?.signal;return gate.promise;});
  const pending=factory(token,fetcher)({kind:'manifest'},caller.controller.signal);
  const rejected=_httpRejected(()=>pending,'network_unresolved');
  expect(vi.getTimerCount()).toBe(1);
  await clock.tick(29999);expect(internal?.aborted).toBe(false);
  await clock.tick(1);await rejected;
  expect(internal?.aborted).toBe(true);expect(caller.controller.signal.aborted).toBe(false);
  expect(fetcher).toHaveBeenCalledTimes(1);_httpBReleased(caller);
  const late=_httpBLateReply();gate.resolve(late.response);await late.canceled;
  expect(late.state).toEqual({pulls:0,cancels:1});expect(late.body.locked).toBe(false);
  await _httpBRecovery(factory);
  const bodyCaller=_httpBCaller(),bodyGate=_httpBGate<Response>(),body=_httpBStalledBody(Uint8Array.of(0x30));
  const started=clock.now();let bodySignal:AbortSignal|null|undefined;
  const bodyFetch=vi.fn<typeof fetch>().mockImplementation((_path,init)=>{bodySignal=init?.signal;return bodyGate.promise;});
  const bodyPending=factory(token,bodyFetch)({kind:'frame',index:0},bodyCaller.controller.signal);
  const bodyRejected=_httpRejected(()=>bodyPending,'network_unresolved');
  await clock.tick(20000);expect(bodySignal?.aborted).toBe(false);
  bodyGate.resolve(_httpResponse(body.body));await body.ready;
  expect(body.state.pulls).toBe(2);expect(body.body.locked).toBe(true);
  await clock.tick(9999);expect(bodySignal?.aborted).toBe(false);
  await clock.tick(1);await bodyRejected;
  expect(clock.now()-started).toBe(30000);expect(bodySignal?.aborted).toBe(true);
  expect(bodyFetch).toHaveBeenCalledTimes(1);expect(bodyCaller.controller.signal.aborted).toBe(false);
  expect(body.state).toEqual({pulls:2,cancels:1});expect(body.body.locked).toBe(false);
  _httpBReleased(bodyCaller);await _httpBRecovery(factory);
 }finally{clock.restore();}
});

it('denies late fetch, chunk and final release before a delayed timer callback runs (own mock transport)',async()=>{
 const factory=await _httpFactory(),clock=_httpBClock(),token='f'.repeat(32);
 try{
  const caller=_httpBCaller(),gate=_httpBGate<Response>();let internal:AbortSignal|null|undefined;
  const fetcher=vi.fn<typeof fetch>().mockImplementation((_path,init)=>{internal=init?.signal;return gate.promise;});
  const deadline=clock.now()+30000;
  const pending=factory(token,fetcher)({kind:'manifest'},caller.controller.signal);
  const rejected=_httpRejected(()=>pending,'network_unresolved');
  expect(vi.getTimerCount()).toBe(1);clock.move(deadline);
  const late=_httpBLateReply();gate.resolve(late.response);await rejected;await late.canceled;
  expect(internal?.aborted).toBe(true);expect(fetcher).toHaveBeenCalledTimes(1);
  expect(late.state).toEqual({pulls:0,cancels:1});expect(late.body.locked).toBe(false);
  _httpBReleased(caller);await _httpBRecovery(factory);
  const chunkCaller=_httpBCaller(),chunkDeadline=clock.now()+30000,state={pulls:0,cancels:0};
  const chunk=new ReadableStream<Uint8Array>({
   pull(controller){state.pulls++;clock.move(chunkDeadline);controller.enqueue(Uint8Array.of(0x30));},
   cancel(){state.cancels++;}
  },{highWaterMark:0});let chunkSignal:AbortSignal|null|undefined;
  const chunkFetch=vi.fn<typeof fetch>().mockImplementation(async(_path,init)=>{
   chunkSignal=init?.signal;return _httpResponse(chunk);
  });
  await _httpRejected(()=>factory(token,chunkFetch)({kind:'frame',index:0},chunkCaller.controller.signal),'network_unresolved');
  expect(chunkSignal?.aborted).toBe(true);expect(chunkFetch).toHaveBeenCalledTimes(1);
  expect(state).toEqual({pulls:1,cancels:1});expect(chunk.locked).toBe(false);
  _httpBReleased(chunkCaller);await _httpBRecovery(factory);
  const releaseCaller=_httpBCaller(),normal=_httpBody([Uint8Array.of(0x30)]),releaseDeadline=clock.now()+30000;
  const nativeRelease=ReadableStreamDefaultReader.prototype.releaseLock;let released=0;
  const release=vi.spyOn(ReadableStreamDefaultReader.prototype,'releaseLock').mockImplementation(function(this:ReadableStreamDefaultReader){
   nativeRelease.call(this);released++;clock.move(releaseDeadline);
  });let releaseSignal:AbortSignal|null|undefined;
  const releaseFetch=vi.fn<typeof fetch>().mockImplementation(async(_path,init)=>{
   releaseSignal=init?.signal;return _httpResponse(normal.body);
  });
  try{
   await _httpRejected(()=>factory(token,releaseFetch)({kind:'manifest'},releaseCaller.controller.signal),'network_unresolved');
   expect(released).toBe(1);expect(release).toHaveBeenCalledTimes(1);
   expect(releaseSignal?.aborted).toBe(true);expect(releaseFetch).toHaveBeenCalledTimes(1);
   expect(normal.state).toEqual({pulls:2,cancels:0});expect(normal.body.locked).toBe(false);
   _httpBReleased(releaseCaller);
  }finally{release.mockRestore();}
  await _httpBRecovery(factory);
 }finally{clock.restore();}
});


it('never returns success or masks a primary error after controlled native cleanup faults (own mock transport)',async()=>{
 const factory=await _httpFactory(),clock=_httpBClock(),token='e'.repeat(32),marker='own-cleanup-fault';
 try{
  await _httpBRecovery(factory);
  for(const mode of ['cancel_reject','release_throw','primary403_cancel_reject','primary_nonbyte_release_throw']){
   const caller=_httpBCaller(),state={pulls:0,cancels:0};
   const body=new ReadableStream<Uint8Array>({
    pull(controller){
     state.pulls++;
     if(mode==='primary_nonbyte_release_throw')Reflect.apply(controller.enqueue,controller,['own nonbyte fault']);
     else if(state.pulls===1)controller.enqueue(Uint8Array.of(0x30));else controller.close();
    },
    cancel(){state.cancels++;if(mode==='primary403_cancel_reject')throw new Error(marker);}
   },{highWaterMark:0});
   const nativeCancel=ReadableStreamDefaultReader.prototype.cancel,nativeRelease=ReadableStreamDefaultReader.prototype.releaseLock;
   let canceled=0,released=0;
   const cancel=vi.spyOn(ReadableStreamDefaultReader.prototype,'cancel').mockImplementation(function(this:ReadableStreamDefaultReader,reason?:unknown){
    const result=nativeCancel.call(this,reason);canceled++;
    return mode==='cancel_reject'?result.then(()=>{throw new Error(marker);}):result;
   });
   const release=vi.spyOn(ReadableStreamDefaultReader.prototype,'releaseLock').mockImplementation(function(this:ReadableStreamDefaultReader){
    nativeRelease.call(this);released++;
    if(mode==='release_throw'||mode==='primary_nonbyte_release_throw')throw new Error(marker);
   });
   try{
    const status=mode==='primary403_cancel_reject'?403:200;
    const fetcher=vi.fn<typeof fetch>().mockResolvedValue(_httpResponse(body,status));
    const code=mode==='primary403_cancel_reject'?'access_denied':mode==='primary_nonbyte_release_throw'?'response_rejected':'network_unresolved';
    const error=await _httpRejected(()=>factory(token,fetcher)({kind:'manifest'},caller.controller.signal),code,status===403?403:null);
    expect(String(error)).not.toContain(marker);expect(fetcher).toHaveBeenCalledTimes(1);
    expect(body.locked).toBe(false);_httpBReleased(caller);
    if(status===403){
     expect(state).toEqual({pulls:0,cancels:1});expect(canceled).toBe(0);expect(released).toBe(0);
     expect(cancel).not.toHaveBeenCalled();expect(release).not.toHaveBeenCalled();
    }else{
     expect(canceled).toBe(1);expect(released).toBe(1);
     expect(cancel).toHaveBeenCalledTimes(1);expect(release).toHaveBeenCalledTimes(1);
     expect(state).toEqual(mode==='primary_nonbyte_release_throw'?{pulls:1,cancels:1}:{pulls:2,cancels:0});
    }
   }finally{cancel.mockRestore();release.mockRestore();}
   await _httpBRecovery(factory);
  }
 }finally{clock.restore();}
});

it('expires a controlled cleanup stall at the original deadline and never turns late settlement into success (own mock transport)',async()=>{
 const factory=await _httpFactory(),clock=_httpBClock(),token='s'.repeat(32);
 const held=_httpBGate<void>(),entered=_httpBGate<void>(),completed=_httpBGate<void>();
 const nativeCancel=ReadableStreamDefaultReader.prototype.cancel,nativeRelease=ReadableStreamDefaultReader.prototype.releaseLock;
 let canceled=0,released=0,completedCleanup=false;
 const cancel=vi.spyOn(ReadableStreamDefaultReader.prototype,'cancel').mockImplementation(function(this:ReadableStreamDefaultReader,reason?:unknown){
  const native=nativeCancel.call(this,reason);canceled++;
  return native.then(async()=>{entered.resolve(undefined);await held.promise;completedCleanup=true;completed.resolve(undefined);});
 });
 const release=vi.spyOn(ReadableStreamDefaultReader.prototype,'releaseLock').mockImplementation(function(this:ReadableStreamDefaultReader){
  nativeRelease.call(this);released++;
 });
 try{
  const caller=_httpBCaller(),responseGate=_httpBGate<Response>();let internal:AbortSignal|null|undefined,settled=false;
  const body=_httpBody([Uint8Array.of(0x30)]),response=_httpResponse(body.body);
  const fetcher=vi.fn<typeof fetch>().mockImplementation((_path,init)=>{internal=init?.signal;return responseGate.promise;});
  const pending=factory(token,fetcher)({kind:'manifest'},caller.controller.signal);
  void pending.then(()=>{settled=true;},()=>{settled=true;});
  const rejected=_httpRejected(()=>pending,'network_unresolved');
  await clock.tick(19000);responseGate.resolve(response);await entered.promise;
  expect(canceled).toBe(1);expect(released).toBe(0);expect(body.body.locked).toBe(true);
  expect(clock.now()).toBe(19000);expect(completedCleanup).toBe(false);
  await clock.tick(10999);expect(clock.now()).toBe(29999);expect(settled).toBe(false);
  expect(internal?.aborted).toBe(false);expect(vi.getTimerCount()).toBe(1);
  await clock.tick(1);await rejected;
  expect(clock.now()).toBe(30000);expect(internal?.aborted).toBe(true);expect(settled).toBe(true);
  expect(canceled).toBe(1);expect(released).toBe(1);expect(completedCleanup).toBe(false);
  expect(body.state).toEqual({pulls:2,cancels:0});expect(body.body.locked).toBe(false);
  expect(fetcher).toHaveBeenCalledTimes(1);_httpBReleased(caller);
  held.resolve(undefined);await completed.promise;expect(completedCleanup).toBe(true);
  expect(settled).toBe(true);expect(vi.getTimerCount()).toBe(0);
  cancel.mockRestore();release.mockRestore();await _httpBRecovery(factory);
 }finally{held.resolve(undefined);cancel.mockRestore();release.mockRestore();clock.restore();}
});
