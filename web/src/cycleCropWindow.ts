import { ApiError,need,object,closed } from './api-validation';
import { validCycleCropLookup,type CycleCropLookup,type CycleCropSummaryResponse,type CycleCropPageResponse,
  type CycleCropDataPage,type createCycleCropReplayApi } from './cycleCropReplay';
import { type StartupCropSample } from './startupCropReplay';

type Kind='samples'|'events';
type Api=Pick<ReturnType<typeof createCycleCropReplayApi>,'cycleCropSummary'|'cycleCropPage'>;
type Selection=Readonly<{result_id:string;farm:CycleCropSummaryResponse['farm'];
  reference:CycleCropSummaryResponse['reference'];index:number;sample:StartupCropSample}>;
export type CycleCropRange=Readonly<{kind:Kind;offset:number;count:number;total:number;last_index:number|null;
  next_offset:number|null;first_utc:string|null;last_utc:string|null;partial:boolean}>;
export type CycleCropWindowState=Readonly<{phase:'idle'|'loading'|'ready'|'error'|'disposed';
  summary:CycleCropSummaryResponse|null;sample_page:CycleCropPageResponse|null;event_page:CycleCropPageResponse|null;
  range:CycleCropRange|null;selected:Selection|null;can_previous:boolean;can_next:boolean;error:ApiError|null}>;
type Context={api:Api;lookup:CycleCropLookup;offsets:Record<Kind,number[]>;cursor:Record<Kind,number>};
function empty(phase:CycleCropWindowState['phase'],error:ApiError|null=null):CycleCropWindowState{
  return {phase,summary:null,sample_page:null,event_page:null,range:null,selected:null,can_previous:false,can_next:false,error};
}
export function cycleCropRange(page:CycleCropDataPage):CycleCropRange{
  const count=page.records.length;
  return {kind:page.kind,offset:page.offset,count,total:page.total,last_index:count?page.offset+count-1:null,
    next_offset:page.next_offset,first_utc:page.records[0]?.at??null,last_utc:page.records.at(-1)?.at??null,
    partial:page.offset!==0 || count!==page.total};
}
function selection(summary:CycleCropSummaryResponse,page:CycleCropPageResponse,index:number):Selection|null{
  if(page.page.kind!=='samples')return null;const sample=page.page.records[index];
  return sample?{result_id:summary.result_id,farm:summary.farm,reference:summary.reference,index:page.page.offset+index,sample}:null;
}
export function createCycleCropWindow(changed:(state:CycleCropWindowState)=>void,
    limits:Readonly<{sample_limit:number;event_limit:number}>={sample_limit:64,event_limit:8}){
  need(object(limits));closed(limits,['sample_limit','event_limit']);
  need(typeof changed==='function' && Number.isSafeInteger(limits.sample_limit) && limits.sample_limit>=1 && limits.sample_limit<=64
    && Number.isSafeInteger(limits.event_limit) && limits.event_limit>=1 && limits.event_limit<=8);
  const sampleLimit=limits.sample_limit,eventLimit=limits.event_limit;
  let state=empty('idle'),context:Context|null=null,generation=0,disposed=false;
  let controller:AbortController|null=null,pending:Promise<void>=Promise.resolve();
  const current=(version:number,signal:AbortSignal)=>!disposed && version===generation && !signal.aborted;
  function publish(next:CycleCropWindowState){state=next;changed(state);}
  function load(ctx:Context,kind:Kind,offset:number,baseline:CycleCropSummaryResponse|null,commit:()=>void){
    const version=++generation;controller?.abort();const owned=new AbortController();controller=owned;
    const prior=pending;state=empty('loading');
    const task=prior.catch(()=>{}).then(async()=>{
      if(!current(version,owned.signal))return;
      try{
        const summary=baseline??await ctx.api.cycleCropSummary(ctx.lookup,owned.signal);
        if(!current(version,owned.signal))return;
        const page=await ctx.api.cycleCropPage(ctx.lookup,{kind,offset,limit:kind==='samples'?sampleLimit:eventLimit},
          {signal:owned.signal,summary});
        if(!current(version,owned.signal))return;
        commit();publish({phase:'ready',summary,sample_page:kind==='samples'?page:null,event_page:kind==='events'?page:null,
          range:cycleCropRange(page.page),selected:selection(summary,page,0),can_previous:ctx.cursor[kind]>0,
          can_next:page.page.next_offset!==null,error:null});
      }catch(error){
        if(current(version,owned.signal))publish(empty('error',error instanceof ApiError?error:new ApiError('network_error')));
      }finally{if(version===generation)controller=null;}
    });
    pending=task;changed(state);return task;
  }
  function active(kind:Kind){
    need(!disposed && state.phase==='ready' && context && state.summary);
    const page=kind==='samples'?state.sample_page:state.event_page;need(page?.page.kind===kind);
    return {ctx:context,summary:state.summary,page};
  }
  function show(kind:Kind){
    need(!disposed && state.phase==='ready' && context && state.summary);
    const ctx=context;return load(ctx,kind,ctx.offsets[kind][ctx.cursor[kind]]!,state.summary,()=>{});
  }
  return {
    snapshot:()=>state,
    open(api:Api,lookup:CycleCropLookup){
      need(!disposed && validCycleCropLookup(lookup));
      const ctx:Context={api,lookup:{...lookup},offsets:{samples:[0],events:[0]},cursor:{samples:0,events:0}};
      context=ctx;return load(ctx,'samples',0,null,()=>{});
    },
    showSamples:()=>show('samples'),showEvents:()=>show('events'),
    next(kind:Kind){
      const {ctx,summary,page}=active(kind),offset=page.page.next_offset;need(offset!==null);
      return load(ctx,kind,offset,summary,()=>{
        ctx.offsets[kind]=ctx.offsets[kind].slice(0,ctx.cursor[kind]+1);ctx.offsets[kind].push(offset);ctx.cursor[kind]++;
      });
    },
    previous(kind:Kind){
      const {ctx,summary}=active(kind);need(ctx.cursor[kind]>0);
      const index=ctx.cursor[kind]-1;return load(ctx,kind,ctx.offsets[kind][index]!,summary,()=>{ctx.cursor[kind]=index;});
    },
    select(index:number){
      const {summary,page}=active('samples');need(Number.isSafeInteger(index) && index>=0 && index<page.page.records.length);
      publish({...state,selected:selection(summary,page,index)});
    },
    cancel(){const settling=pending;generation++;controller?.abort();controller=null;context=null;
      if(!disposed)publish(empty('idle'));return settling.then(()=>{});
    },
    dispose(){generation++;disposed=true;controller?.abort();controller=null;context=null;state=empty('disposed');return pending.then(()=>{});},
  };
}
