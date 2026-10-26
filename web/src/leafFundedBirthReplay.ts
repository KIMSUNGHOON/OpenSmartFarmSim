import {sha256} from './morphologyReplay';
import {growingGeometryOffset} from './growingGeometryReplay';
import {need,object,closed,digest,id,utc,integer,rights,exact,readStoredLeafFile} from './storedLeafReplayIO';
import {wireFields,wireHash} from './fundedLeafReplayWire';
import {ANCHORS,PINS,ROOT,IDENTITY,NOTICE,EXPORTER,POINT,equal,list,block,flags,fluxUnits,balances,programInfo,sample,rootSeed,frame,grid,type FundedLeafFrame,type Row} from './leafFundedBirthReplaySchema';
import {EVENT_FIELDS,POLICY,adoptStoredEvent,type GraphState} from './leafFundedBirthReplayEvents';

export type {FundedLeafFrame} from './leafFundedBirthReplaySchema';
export type LeafFundedBirthScenario=keyof typeof ANCHORS;
export type FundedLeafAnchor={artifact_sha256:string;index_sha256:string;frames:number;events:number};
export type FundedLeafReplay={artifact_sha256:string;frames:FundedLeafFrame[]};
export type LeafFundedBirthReplay=FundedLeafReplay&{scenario:LeafFundedBirthScenario};
const SOURCE_ROLES=['inputs','request','program','seed','context','growth_profile','cohort_profile','transport_profile','exchange_profile','license_notice'];
const ROOT_FIELDS=[...Object.keys(ROOT),'input_id','source_rights','time_origin_utc','sources','code_sha256','context_sha256','initial_state_sha256','terminal_state_sha256','events','samples'];
const SAMPLE_FIELDS=['index','step_index','elapsed_seconds_exact','phase','event_sequence','context_sha256','checkpoint_sha256','checkpoint_bytes','sample_sha256','state_sha256','previous_checkpoint_sha256'];
const FRAME_FIELDS=['index','step_index','phase','event_sequence','at','context_sha256','checkpoint_sha256','sample_sha256','state_sha256','path','sha256','bytes'];
const ROOT_CP=['version','context_sha256','step_index','output_cursor','output_prefix_sha256','last_confirmed','integrated_transfers','balance_residuals','balance_budgets'];
const FUNDED_CP=[...ROOT_CP,'segment_step_index','event_sequence','phase','at_elapsed_seconds_exact','segment_integrated_transfers','point_history_sha256','point_totals','global_balance_residuals','global_balance_budgets','scope','G0_G4'];
export function isLeafFundedBirthScenario(v:unknown):v is LeafFundedBirthScenario{return typeof v==='string'&&Object.hasOwn(ANCHORS,v);}

/** The caller supplies a trusted immutable anchor; an arbitrary downloaded index is not an anchor. */
export async function readFundedLeafReplay(readFile:(name:string)=>Promise<Uint8Array>,anchor:FundedLeafAnchor,signal:AbortSignal):Promise<FundedLeafReplay>{
 signal.throwIfAborted();digest(anchor.artifact_sha256);digest(anchor.index_sha256);integer(anchor.frames,3,512);integer(anchor.events,1,511);
 const read=async(name:string)=>{signal.throwIfAborted();const value=await readFile(name);signal.throwIfAborted();need(value instanceof Uint8Array&&value.byteLength>0&&value.byteLength<=2*1024**2);return new Uint8Array(value);};
 const text=(raw:Uint8Array)=>new TextDecoder('utf-8',{fatal:true}).decode(raw);
 const document=(raw:Uint8Array)=>{const value=text(raw);wireFields(value);return object(JSON.parse(value));};
 const pinned=async(name:string,d:Row,max=2*1024**2)=>{
  digest(d.sha256);integer(d.bytes,1,max);const raw=await read(name);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);return raw;
 };
 const indexRaw=await read('index.json');need(await sha256(indexRaw)===anchor.index_sha256);
 const index=closed(document(indexRaw),[...Object.keys(ROOT),'artifact_sha256','input_id','source_rights','exporter_sha256','sources','events','checkpoints','frames']);
 flags(index,'funded-leaf-public-fixture-v1');need(index.artifact_sha256===anchor.artifact_sha256&&index.exporter_sha256===EXPORTER);rights(index.source_rights);
 const loaded:Record<string,Uint8Array<ArrayBuffer>>={};
 for(const source of list(index.sources,11)){
  const d=closed(source,['role','path','sha256','bytes']);need(typeof d.role==='string'&&['root',...SOURCE_ROLES].includes(d.role)&&!Object.hasOwn(loaded,d.role));
  const path=d.role==='root'?'root.json':d.role==='license_notice'?'NOTICE.txt':`source-${d.role}.json`;need(d.path===path);loaded[d.role]=await pinned(path,d);
 }
 need(await sha256(loaded.root!)===anchor.artifact_sha256);const root=closed(document(loaded.root!),ROOT_FIELDS);flags(root,ROOT.schema_version);equal(root.code_sha256,PINS);
 id(root.input_id);utc(root.time_origin_utc);rights(root.source_rights);equal(root.source_rights,index.source_rights);need(root.input_id===index.input_id);
 const sourceDescriptors=closed(root.sources,SOURCE_ROLES);
 for(const role of SOURCE_ROLES){const d=closed(sourceDescriptors[role],['sha256','bytes']);need(loaded[role]!.byteLength===d.bytes&&await sha256(loaded[role]!)===d.sha256);}
 need(object(sourceDescriptors.license_notice).sha256===NOTICE);for(const [k,h]of Object.entries(IDENTITY.profile_sha256))need(object(sourceDescriptors[k+'_profile']).sha256===h);
 const input=closed(document(loaded.inputs!),['schema_version','input_id','origin','program','births','rights','time_origin_utc','step_seconds','step_count']);
 need(input.schema_version==='funded-leaf-artifact-input-v1'&&input.origin==='synthetic'&&input.input_id===root.input_id&&input.time_origin_utc===root.time_origin_utc);equal(input.rights,root.source_rights);
 const rootInfo=await programInfo(text(loaded.program!)),rootContext=closed(document(loaded.context!),['identity','request_sha256','program_sha256','seed_sha256','numerical','state_layout','flux_units']);
 equal(rootContext.identity,IDENTITY);equal(rootContext.state_layout,rootInfo.layout);equal(rootContext.flux_units,fluxUnits(rootInfo.leaves.length));equal(input.program,document(loaded.request!));equal(input.program,rootInfo.program);
 need(root.context_sha256===object(sourceDescriptors.context).sha256);
 for(const k of ['request','program','seed'])need(rootContext[k+'_sha256']===object(sourceDescriptors[k]).sha256);
 need(['request','program','seed','context'].reduce((sum,k)=>sum+loaded[k]!.byteLength,0)<=2*1024**2);
 const {dt,count}=grid(rootContext.numerical,input,rootInfo.leaves.length),births=list(input.births,anchor.events);
 need(anchor.frames===count+1+births.length);const samples=list(root.samples,anchor.frames),events=list(root.events,anchor.events);
 const descriptors=list(index.frames,anchor.frames),checkpoints=list(index.checkpoints,anchor.frames);
 need(root.initial_state_sha256===object(samples[0]).state_sha256&&root.terminal_state_sha256===object(samples.at(-1)).state_sha256);
 const {seed,receipts}=rootSeed(document(loaded.seed!),rootInfo),rootY=list(seed.state),n0=rootInfo.leaves.length;
 need(root.initial_state_sha256===await wireHash(wireFields(text(loaded.seed!)).state!));
 let state:GraphState={info:rootInfo,context:rootContext,seed:{anchors:object(seed.evaluation).curve_residuals},history:[],receipts,bases:rootInfo.leaves.map((l,i)=>({leaf_id:l.leaf_id,step_index:0,thermal_age:rootY[107+i],carbon:rootY[107+2*n0+i],air_temperature_integral:0}))};
 const eventAt=new Map<number,{d:Row;item:Row}>();let lastBirthStep=0;
 for(let j=0;j<events.length;j++){
  const d=closed(events[j],EVENT_FIELDS),publicD=closed(list(index.events,anchor.events)[j],EVENT_FIELDS),item=closed(births[j],['step_index','point_inputs']);
  integer(item.step_index,lastBirthStep,count);lastBirthStep=item.step_index;need(d.event_sequence===j+1&&d.step_index===item.step_index&&d.after_frame_index===item.step_index+j+1);digest(d.context_sha256);
  const point=closed(item.point_inputs,['schema_version','input_id','origin','policy','context_sha256','checkpoint_sha256','at_elapsed_seconds_exact','model_floor_area','events']);
  need(point.schema_version==='leaf-funded-birth-point-input-v1'&&point.origin==='synthetic'&&point.policy===POLICY);id(point.input_id);digest(point.context_sha256);digest(point.checkpoint_sha256);
  exact(point.at_elapsed_seconds_exact,'s');equal(point.at_elapsed_seconds_exact,growingGeometryOffset(dt,item.step_index));equal(point.model_floor_area,rootInfo.program.model_floor_area);
  for(const k of EVENT_FIELDS.filter(k=>!['point','context_snapshot'].includes(k)))equal(publicD[k],d[k]);
  for(const [key,path]of [['point',`event-${j}.json`],['context_snapshot',`context-${j}.json`]]){
   const original=closed(d[key!],['sha256','bytes']),published=closed(publicD[key!],['sha256','bytes','path']);need(published.path===path);equal(original,{sha256:published.sha256,bytes:published.bytes});
  }
  eventAt.set(Number(d.after_frame_index),{d:publicD,item});
 }
 const frames:FundedLeafFrame[]=[],seen=new Set<string>();let previous:Row|undefined,previousSHA:string|null=null,previousStep=-1,sequence=0,prefix=await wireHash('[]'),firstCP:Row|undefined,scalar=0;
 for(let i=0;i<anchor.frames;i++){
  signal.throwIfAborted();const d=closed(samples[i],SAMPLE_FIELDS),cpD=closed(checkpoints[i],[...SAMPLE_FIELDS,'path','sha256','bytes']);
  for(const k of SAMPLE_FIELDS)equal(cpD[k],d[k]);integer(d.step_index,0,count);integer(d.event_sequence,0,anchor.events);
  need(d.index===i&&d.previous_checkpoint_sha256===previousSHA&&cpD.path===`checkpoint-${i}.json`&&cpD.sha256===d.checkpoint_sha256&&cpD.bytes===d.checkpoint_bytes);
  for(const k of ['checkpoint_sha256','context_sha256','sample_sha256','state_sha256'])digest(d[k]);exact(d.elapsed_seconds_exact,'s');equal(d.elapsed_seconds_exact,growingGeometryOffset(dt,d.step_index));
  const event=eventAt.get(i);
  if(event){
   need(previous!==undefined&&previousSHA!==null&&d.step_index===previousStep&&event.item.step_index===d.step_index&&event.d.event_sequence===sequence+1);
   const pointRaw=await pinned(`event-${sequence}.json`,object(event.d.point)),contextRaw=await pinned(`context-${sequence}.json`,object(event.d.context_snapshot));
   state=await adoptStoredEvent(text(pointRaw),text(contextRaw),event.d,event.item,sequence+1,previous,previousSHA,state,rootContext,String(root.context_sha256),seen);sequence++;firstCP=undefined;
  }else need(d.step_index===previousStep+1);
  need(d.event_sequence===sequence&&d.context_sha256===(sequence?object(events[sequence-1]).context_sha256:root.context_sha256));
  const raw=await pinned(`checkpoint-${i}.json`,cpD,1024**2),cp=closed(document(raw),sequence?FUNDED_CP:ROOT_CP),fields=wireFields(text(raw));
  need(cp.context_sha256===d.context_sha256&&cp.step_index===d.step_index&&cp.output_cursor===i+1);digest(cp.output_prefix_sha256);
  sample(cp.last_confirmed,state.info,d.step_index,dt);block(cp.integrated_transfers,fluxUnits(state.info.leaves.length));balances(cp,state.info.leaves.length);
  need(await wireHash(fields.last_confirmed!)===d.sample_sha256&&await wireHash(wireFields(fields.last_confirmed!).state!)===d.state_sha256);
  if(sequence){
   const local=d.step_index-Number(object(state.context.numerical).event_global_step_index);
   need(cp.version==='funded-individual-leaf-continuation-checkpoint-v1'&&cp.segment_step_index===local&&local>=0&&cp.event_sequence===sequence&&cp.phase===d.phase&&d.phase===(local===0?'after_birth':'funded_birth_interval'));
   need(cp.scope==='software_research_only'&&cp.G0_G4==='not_assessed'&&cp.point_history_sha256===state.context.history_sha256);equal(cp.at_elapsed_seconds_exact,d.elapsed_seconds_exact);
   block(cp.segment_integrated_transfers,fluxUnits(state.info.leaves.length));block(cp.point_totals,POINT);balances(cp,state.info.leaves.length,true);
   if(local===0){equal(cp.last_confirmed,state.seed.last_confirmed);equal(cp.integrated_transfers,state.seed.base_transfers);need(Object.values(object(cp.segment_integrated_transfers)).every(v=>object(v).value===0));}
   else{need(firstCP);equal(cp.point_totals,firstCP.point_totals);}
   prefix=await wireHash('{"event_sequence":'+sequence+',"phase":'+JSON.stringify(cp.phase)+',"previous":'+JSON.stringify(prefix)+',"sample":'+fields.last_confirmed+'}');
   firstCP??=cp;
  }else{
   need(cp.version==='individual-leaf-carbon-area-checkpoint-v1'&&d.phase==='root_interval'&&i===d.step_index);
   if(i===0){
    const first=object(cp.last_confirmed),e=object(seed.evaluation),rhs=object(e.stock_rhs);
    equal(first.state,seed.state);equal(first.derived,{...object(object(object(rhs.source_stage).source_joint).derived),leaf_carbohydrate:object(rhs.leaf_totals).carbon});equal(first.curve_residuals,e.curve_residuals);
    need(list(first.curve_invariant_changes).every(v=>object(v).value===0)&&Object.values(object(cp.integrated_transfers)).every(v=>object(v).value===0));
   }
   prefix=await wireHash('{"previous":'+JSON.stringify(prefix)+',"sample":'+fields.last_confirmed+'}');
  }
  need(prefix===cp.output_prefix_sha256);scalar+=115+5*state.info.leaves.length;need(scalar<=32768);
  const dtoD=closed(descriptors[i],FRAME_FIELDS);need(dtoD.path===`frame-${i}.json`);equal(dtoD.at,{time_origin_utc:root.time_origin_utc,elapsed_seconds_exact:d.elapsed_seconds_exact});
  for(const k of ['index','step_index','phase','event_sequence','context_sha256','checkpoint_sha256','sample_sha256','state_sha256'])equal(dtoD[k],d[k]);
  const dto=await pinned(`frame-${i}.json`,dtoD);frames.push(frame(document(dto),cp,d,root,anchor.artifact_sha256,state.info,state.receipts,state.bases));
  previous=cp;previousSHA=String(d.checkpoint_sha256);previousStep=d.step_index;
 }
 need(previousStep===count&&sequence===anchor.events);signal.throwIfAborted();return {artifact_sha256:anchor.artifact_sha256,frames};
}
export async function loadLeafFundedBirthReplay(scenario:string,signal:AbortSignal):Promise<LeafFundedBirthReplay>{
 signal.throwIfAborted();need(isLeafFundedBirthScenario(scenario));
 const result=await readFundedLeafReplay(name=>readStoredLeafFile(`./leaf-funded-birth-replay/${scenario}/`,name,signal),ANCHORS[scenario],signal);
 return {...result,scenario};
}
export class LeafFundedBirthRequest{
 private generation=0;private controller?:AbortController;
 cancel(){this.generation++;this.controller?.abort();this.controller=undefined;}
 async load(scenario:string){
  this.cancel();const generation=this.generation,controller=new AbortController();this.controller=controller;
  try{const result=await loadLeafFundedBirthReplay(scenario,controller.signal);controller.signal.throwIfAborted();need(generation===this.generation);return result;}
  finally{if(generation===this.generation)this.controller=undefined;}
 }
}
