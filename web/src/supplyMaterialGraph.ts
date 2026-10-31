import {sha256} from './morphologyReplay';
import {closed,digest,integer,need,object} from './storedLeafReplayIO';
import {equal} from './leafFundedBirthReplaySchema';
import {wireHash} from './fundedLeafReplayWire';
import {compare,counter,document,exactAt,list,type WireDocument} from './supplyMorphologyGraphValues';
import {sourceDescriptor} from './supplyMorphologySourceBinding';
import {SUPPLY_MORPHOLOGY_FIXTURE as ORIGINAL} from './supplyMorphologyReplayFixture';
import {SUPPLY_MATERIAL_FIXTURE as F} from './supplyMaterialFixture';
import {FLAGS,materialFlags,materialPins,publicMaterialRights,materialSourceGraph,materialFrameValue,type Group,type GetRecord} from './supplyMaterialGraphChecks';
import {materialOriginal} from './supplyMaterialOriginal';
import {materialStoredSchema} from './supplyMaterialSchemas';

export type SupplyMaterialAnchor={artifact_sha256:string;index_sha256:string;frames:number;public_files:number};
const FILE=['path','sha256','bytes'];
const META=['index','phase','at','source_sha256','source_cursor_sha256','event_sequence','frame_sha256','state_scalars'];

/** A pinned local public fixture reader, not an authority for arbitrary farm data. */
export async function readSupplyMaterialFiles(readFile:(name:string)=>Promise<Uint8Array>,anchor:SupplyMaterialAnchor,signal:AbortSignal){
 anchor={...anchor};closed(anchor,['artifact_sha256','index_sha256','frames','public_files']);digest(anchor.artifact_sha256);digest(anchor.index_sha256);
 integer(anchor.frames,1,512);integer(anchor.public_files,1,4609);let downloaded=0;signal.throwIfAborted();
 const read=async(name:string)=>{
  signal.throwIfAborted();need(/^(?:index\.json|root\.json|NOTICE\.txt|blob-[0-9a-f]{64}\.json|frame-(?:0|[1-9]\d{0,2})\.json)$/.test(name));
  const result=await readFile(name);signal.throwIfAborted();need(result instanceof Uint8Array&&result.byteLength>0&&result.byteLength<=2*1024**2);
  downloaded+=result.byteLength;need(downloaded<=64*1024**2);return new Uint8Array(result);
 };
 const text=(raw:Uint8Array)=>new TextDecoder('utf-8',{fatal:true}).decode(raw);
 const indexBytes=await read('index.json');need(await sha256(indexBytes)===anchor.index_sha256);signal.throwIfAborted();
 const index=document(text(indexBytes)),i=closed(index.value,['schema_version',...Object.keys(FLAGS),'artifact_sha256','code_sha256','exporter_sha256','output_writer_sha256','effective_rights','window','terminal','root','notice','blobs','frames','sample_scalars']);
 materialFlags(i,'supply-material-public-fixture-v1');materialPins(i.code_sha256);publicMaterialRights(i.effective_rights);
 need(i.artifact_sha256===anchor.artifact_sha256&&i.exporter_sha256===F.exporter_sha256&&i.output_writer_sha256===F.output_writer_sha256);
 const descriptors=list(i.blobs,4096),frameDescriptors=list(i.frames);need(frameDescriptors.length===anchor.frames&&descriptors.length+anchor.frames+1===anchor.public_files);
 integer(i.sample_scalars,1,32768);let declared=indexBytes.byteLength;
 for(const value of [...descriptors,...frameDescriptors]){const d=object(value);digest(d.sha256);integer(d.bytes,1,2*1024**2);declared+=d.bytes;need(declared<=64*1024**2);}
 const blobs=new Map<string,{raw:string;bytes:number;path:string}>(),docs=new Map<string,WireDocument>();
 for(const value of descriptors){
  const d=closed(value,FILE);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  const path=d.sha256===anchor.artifact_sha256?'root.json':d.sha256===F.notice_sha256?'NOTICE.txt':`blob-${d.sha256}.json`;
  need(d.path===path&&!blobs.has(d.sha256));const raw=await read(path);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);
  const body=text(raw);if(path!=='NOTICE.txt')docs.set(d.sha256,document(body));blobs.set(d.sha256,{raw:body,bytes:raw.byteLength,path});
 }
 for(const key of ['root','notice']){const d=closed(i[key],FILE),b=blobs.get(String(d.sha256));need(b&&d.path===b.path&&d.bytes===b.bytes);}
 need(object(i.root).sha256===anchor.artifact_sha256&&object(i.notice).sha256===F.notice_sha256);
 const root=docs.get(anchor.artifact_sha256);need(root);const r=closed(root.value,['schema_version',...Object.keys(FLAGS),'code_sha256','source','blob_groups','before_geometry_diagnostics','effective_rights','window','terminal','frames','notice']);
 materialFlags(r,'supply-material-research-artifact-v1');materialPins(r.code_sha256);publicMaterialRights(r.effective_rights);
 for(const key of ['effective_rights','window','terminal'])equal(r[key],i[key]);
 const groups=closed(r.blob_groups,['original','base','forcing','material']),members=new Map<Group,Set<string>>(),used=new Map<Group,Set<string>>();
 const all=new Set<string>([anchor.artifact_sha256]);
 for(const group of ['original','base','forcing','material'] as const){
  const set=new Set<string>();for(const value of list(groups[group],1024)){
   const d=sourceDescriptor(value),b=blobs.get(d.sha256);need(b&&b.bytes===d.bytes&&!set.has(d.sha256)&&d.sha256!==anchor.artifact_sha256);set.add(d.sha256);all.add(d.sha256);
  }need(set.size>0);members.set(group,set);used.set(group,new Set());
 }need(all.size===blobs.size);
 const raw=(hash:unknown,group:Group)=>{digest(hash);need(members.get(group)!.has(hash));used.get(group)!.add(hash);return blobs.get(hash)!.raw;};
 const get:GetRecord=(hash,group)=>{raw(hash,group);const doc=docs.get(String(hash));need(doc);if(group!=='original')materialStoredSchema(doc);return doc;};
 const getOriginal=(value:unknown)=>{const d=sourceDescriptor(value);need(blobs.get(d.sha256)?.bytes===d.bytes);return raw(d.sha256,'original');};
 const source=object(r.source),od=sourceDescriptor(source.original_root);need(od.sha256===ORIGINAL.anchor.artifact_sha256);
 const original=get(od.sha256,'original');need(blobs.get(od.sha256)?.bytes===od.bytes);
 await materialOriginal(original,hash=>get(hash,'original'),getOriginal,signal);signal.throwIfAborted();
 const sources=await materialSourceGraph(root,get,original,signal);signal.throwIfAborted();
 const notice=sourceDescriptor(r.notice);need(notice.sha256===F.notice_sha256&&notice.bytes===blobs.get(notice.sha256)?.bytes);raw(notice.sha256,'original');
 for(const group of ['original','base','forcing','material'] as const)need(used.get(group)!.size===members.get(group)!.size);
 const rootFrames=list(r.frames);need(rootFrames.length===anchor.frames&&sources.material.links.length+1===anchor.frames);
 const frames=[];let scalars=0;
 for(const [j,value]of frameDescriptors.entries()){
  signal.throwIfAborted();const d=closed(value,[...META,...FILE]),rd=closed(rootFrames[j],[...META,'bytes']);
  need(d.path===`frame-${j}.json`);for(const key of META)equal(d[key],rd[key]);
  const bytes=await read(String(d.path));need(bytes.byteLength===d.bytes&&await sha256(bytes)===d.sha256);
  const dto=document(text(bytes)),q=closed(dto.value,['schema_version','artifact_sha256','index','frame']);
  need(q.schema_version==='supply-material-public-frame-v1'&&q.artifact_sha256===anchor.artifact_sha256&&counter(dto,'index',0,511)===j);
  const frame=document(dto.fields.frame!);closed(frame.value,['schema_version',...Object.keys(FLAGS),'snapshot','model_floor_area','state_layout','leaves','internodes','global_ledgers',...META.filter(k=>!['frame_sha256','state_scalars'].includes(k)),'schedule','point_totals_exact','lifetime_transfers_exact','transfer_origins','state_kind']);
  need(new TextEncoder().encode(frame.raw).byteLength===rd.bytes&&await wireHash(frame.raw)===d.frame_sha256);
  for(const key of META.filter(k=>!['frame_sha256','state_scalars'].includes(k)))equal(frame.value[key],d[key]);
  const result=materialFrameValue(frame,j,sources,root);need(result.snapshot.state.length===d.state_scalars);scalars+=result.snapshot.state.length;need(scalars<=32768);
  if(j){const a=exactAt(frames[j-1]!.at),b=exactAt(result.at);need(a.origin===b.origin&&compare(a.elapsed,b.elapsed)<=0);}
  frames.push(result);
 }
 const window=closed(r.window,['source_event_id','first_at','last_at','covers_whole_season','selection']);
 need(window.covers_whole_season===false&&window.selection==='one_adopted_material_and_confirmed_remainder'&&window.source_event_id===object(sources.point.value.source_event).source_event_id);
 equal(window.first_at,frames[0]!.at);equal(window.last_at,frames.at(-1)!.at);equal(frames[0]!.at,frames[1]!.at);
 const terminal=closed(r.terminal,['status','scope','hold']);need(terminal.hold===null&&terminal.scope==='declared_synthetic_forcing_plan_only');
 need(terminal.status===(frames.at(-1)!.phase==='declared_end'?'completed':'confirmed_prefix'));
 signal.throwIfAborted();need(scalars===i.sample_scalars&&downloaded===declared);
 return {artifact_sha256:anchor.artifact_sha256,index,root,frames,sample_scalars:scalars,downloaded_bytes:downloaded};
}
