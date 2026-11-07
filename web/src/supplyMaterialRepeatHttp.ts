import {ApiError} from './api-validation';
import type {RepeatRead} from './supplyMaterialRepeatReplay';

const MAX_BYTES=2097152,SECONDS_MS=30000;

export function createSupplyMaterialRepeatRead(token:string,fetcher:typeof fetch=fetch):RepeatRead{
 if(typeof token!=='string'||!/^[A-Za-z0-9_-]{32,128}$/.test(token))throw new ApiError('auth_required');
 if(typeof fetcher!=='function')throw new ApiError('response_rejected');
 return async(selection,caller)=>{
  const deadline=performance.now()+SECONDS_MS;
  if(caller.aborted)throw new ApiError('request_canceled');
  let path:string;
  try{
   const kind=selection.kind;
   if(kind==='manifest')path='/v1/research/material-repeat/manifest';
   else if(kind==='frame'){
    const index=selection.index;
    if(!Number.isSafeInteger(index)||index<0||index>511)throw new Error();
    path='/v1/research/material-repeat/frames/'+String(index);
   }else throw new Error();
  }catch{throw new ApiError('response_rejected');}
  const controller=new AbortController(),ownedErrors=new Set<ApiError>();
  const error=(code:string,status:number|null=null)=>{
   const value=new ApiError(code,status);ownedErrors.add(value);return value;
  };
  let rejectStop:(reason:ApiError)=>void=()=>{};
  const stopped=new Promise<never>((_resolve,reject)=>{rejectStop=reject;});
  void stopped.catch(()=>{});
  const stop=()=>{
   controller.abort();rejectStop(error(caller.aborted?'request_canceled':'network_unresolved'));
  };
  const fence=()=>{
   if(caller.aborted)throw error('request_canceled');
   if(controller.signal.aborted||performance.now()>=deadline){stop();throw error('network_unresolved');}
  };
  const wait=async<T>(operation:PromiseLike<T>):Promise<T>=>{
   const value=await Promise.race([operation,stopped]);fence();return value;
  };
  const cancel=()=>stop();
  caller.addEventListener('abort',cancel,{once:true});
  const timer=setTimeout(stop,Math.max(0,deadline-performance.now()));
  let response:Response|undefined,reader:ReadableStreamDefaultReader<Uint8Array>|undefined;
  let raw:Uint8Array|undefined,failure:unknown,failed=false,finished=false;
  const discardLate=(value:Response)=>{
   try{void value.body?.cancel().catch(()=>{});}catch{}
  };
  try{
   fence();
   const pending=Promise.resolve(fetcher(path,{method:'GET',headers:{Authorization:'Bearer '+token},
    credentials:'omit',redirect:'error',cache:'no-store',signal:controller.signal})).then(value=>{
     response=value;if(finished)discardLate(value);return value;
    });
   response=await wait(pending);
   if(!response||!Number.isSafeInteger(response.status)||response.status<0||response.status>599)
    throw error('response_rejected');
   if(response.status!==200){
    const codes:Record<number,string>={401:'auth_required',403:'access_denied',404:'not_available',
     409:'intent_conflict',413:'too_large',422:'invalid_request'};
    throw error(codes[response.status]??(response.status>=200&&response.status<300?'response_rejected':'server_unavailable'),response.status);
   }
   if(response.redirected||response.headers.get('content-type')?.split(';')[0]?.trim().toLowerCase()!=='application/json'
    ||!response.headers.get('cache-control')?.split(',').some(value=>value.trim().toLowerCase()==='no-store')
    ||!response.body||response.bodyUsed||response.body.locked)
    throw error('response_rejected');
   const storage=new Uint8Array(MAX_BYTES);let size=0;
   reader=response.body.getReader();
   for(;;){
    const part=await wait(reader.read());
    if(part.done)break;
    if(!(part.value instanceof Uint8Array))throw error('response_rejected');
    if(part.value.byteLength>MAX_BYTES-size)throw error('too_large');
    storage.set(part.value,size);size+=part.value.byteLength;
   }
   if(size===0)throw error('response_rejected');
   raw=storage.slice(0,size);fence();
  }catch(value){failed=true;failure=value;}
  finally{
   finished=true;
   try{
    if(reader)await wait(reader.cancel());
    else if(response?.body)await wait(response.body.cancel());
   }catch(value){if(!failed){failed=true;failure=value;}}
   finally{
    try{reader?.releaseLock();}catch(value){if(!failed){failed=true;failure=value;}}
    clearTimeout(timer);caller.removeEventListener('abort',cancel);
   }
  }
  if(caller.aborted)throw error('request_canceled');
  if(failed)throw failure instanceof ApiError&&ownedErrors.has(failure)?failure:error('network_unresolved');
  fence();
  if(raw===undefined)throw error('response_rejected');
  return raw;
 };
}
