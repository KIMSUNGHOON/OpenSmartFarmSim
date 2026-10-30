import {sha256} from './morphologyReplay';
import {closed,digest,integer,need,object} from './storedLeafReplayIO';
import {wireHash,wireFields} from './fundedLeafReplayWire';
import {equal} from './leafFundedBirthReplaySchema';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
import {readSupplyContext,readSupplyCheckpoint,type SupplyContext} from './supplyMorphologyContextGraph';
import {readSupplyMaterial,type MaterialLink} from './supplyMorphologyMaterialGraph';
import {installedPins,publicRights,researchFlags,sourceDescriptor,verifySupplySourceBinding} from './supplyMorphologySourceBinding';
import {binary64,compare,document,exactAt,list,mul,type WireDocument} from './supplyMorphologyGraphValues';
export type SupplyGraphAnchor={artifact_sha256:string;index_sha256:string;frames:number;public_files:number};
type Expected={context_sha256:string;checkpoint_sha256:string|null;receipt_sha256:string|null;at:unknown;phase:unknown;event_sequence:unknown;output_cursor:unknown;output_prefix_sha256:unknown;snapshotRaw:string};
const FLAGS=['schema_version','scope','G0_G4','R2','time_kind','claim_scope'];
const META=['index','context_sha256','checkpoint_sha256','receipt_sha256','at','phase','event_sequence','output_cursor','output_prefix_sha256'];
const DESCRIPTOR=[...META,'frame_sha256','state_sha256'],FILE=['path','sha256','bytes'];

/** Source provenance only. Quantities and a UI projection remain unapproved. */
export async function readSupplyMorphologySourceGraph(readFile:(name:string)=>Promise<Uint8Array>,anchor:SupplyGraphAnchor,signal:AbortSignal){
 anchor={...anchor};closed(anchor,['artifact_sha256','index_sha256','frames','public_files']);digest(anchor.artifact_sha256);digest(anchor.index_sha256);
 integer(anchor.frames,1,512);integer(anchor.public_files,1,4609);signal.throwIfAborted();let downloaded=0;
 const read=async(name:string)=>{
  signal.throwIfAborted();need(/^(?:index\.json|root\.json|NOTICE\.txt|blob-[0-9a-f]{64}\.json|frame-(?:0|[1-9]\d{0,2})\.json)$/.test(name));
  const value=await readFile(name);signal.throwIfAborted();need(value instanceof Uint8Array&&value.byteLength>0&&value.byteLength<=2*1024**2);
  downloaded+=value.byteLength;need(downloaded<=64*1024**2);return new Uint8Array(value);
 };
 const text=(raw:Uint8Array)=>new TextDecoder('utf-8',{fatal:true}).decode(raw);
 const indexBytes=await read('index.json');need(await sha256(indexBytes)===anchor.index_sha256);
 const index=document(text(indexBytes)),i=closed(index.value,[...FLAGS,'artifact_sha256','code_sha256','exporter_sha256','output_writer_sha256','source_rights','redistribution_authorized','terminal','root','notice','blobs','frames','sample_scalars']);
 researchFlags(i,'supply-morphology-public-fixture-v1');need(i.artifact_sha256===anchor.artifact_sha256&&i.exporter_sha256===F.exporter_sha256&&i.output_writer_sha256===F.output_writer_sha256);
 installedPins(i.code_sha256,Object.keys(F.code_sha256));publicRights(i.source_rights);need(i.redistribution_authorized===true);integer(i.sample_scalars,1,32768);
 const descriptors=list(i.blobs,4096),publicFrames=list(i.frames);need(descriptors.length>=1&&publicFrames.length===anchor.frames&&descriptors.length+anchor.frames+1===anchor.public_files);
 let declared=indexBytes.byteLength;const paths=new Set<string>(),hashes=new Set<string>();
 for(const value of [...descriptors,...publicFrames]){
  const d=object(value);digest(d.sha256);integer(d.bytes,1,2*1024**2);declared+=d.bytes;need(declared<=64*1024**2);
 }
 const blobs=new Map<string,{raw:string;bytes:number;path:string}>();
 for(const value of descriptors){
  const d=closed(value,FILE);digest(d.sha256);integer(d.bytes,1,2*1024**2);
  const path=d.sha256===anchor.artifact_sha256?'root.json':d.sha256===F.notice_sha256?'NOTICE.txt':`blob-${d.sha256}.json`;
  need(d.path===path&&!paths.has(path)&&!hashes.has(d.sha256));paths.add(path);hashes.add(d.sha256);
  const raw=await read(path);need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);const body=text(raw);
  if(path!=='NOTICE.txt')document(body);blobs.set(d.sha256,{raw:body,bytes:raw.byteLength,path});
 }
 const used=new Set<string>();
 const byHash=(hash:unknown)=>{digest(hash);const b=blobs.get(hash);need(b);used.add(hash);return b.raw;};
 const get=(value:unknown)=>{const d=sourceDescriptor(value),b=blobs.get(d.sha256);need(b&&b.bytes===d.bytes);return byHash(d.sha256);};
 for(const name of ['root','notice']){const d=closed(i[name],FILE),b=blobs.get(String(d.sha256));need(b&&b.path===d.path&&b.bytes===d.bytes);}
 need(object(i.root).sha256===anchor.artifact_sha256&&object(i.notice).sha256===F.notice_sha256);
 const root=document(byHash(anchor.artifact_sha256)),r=closed(root.value,[...F.schema_keys.root]);researchFlags(r,'supply-morphology-research-artifact-v1');
 installedPins(r.code_sha256,Object.keys(F.code_sha256));equal(r.source_rights,i.source_rights);equal(r.terminal,i.terminal);need(r.redistribution_authorized===true);
 await verifySupplySourceBinding(root,get,byHash);signal.throwIfAborted();
 const segments=list(r.segments),contexts:SupplyContext[]=[],receipts:MaterialLink[]=[],expected:Expected[]=[];need(segments.length>=1);
 let previous:SupplyContext|undefined,last:WireDocument|undefined;
 for(const value of segments){
  signal.throwIfAborted();const segment=closed(value,['context','checkpoints']),descriptor=sourceDescriptor(segment.context);
  const current=await readSupplyContext(get(segment.context),descriptor.sha256);
  need(current.descriptor.value.origin_context_sha256===sourceDescriptor(object(r.root_inputs).origin_context).sha256);
  if(previous){
   need(last);const m=await readSupplyMaterial(previous,current,last);receipts.push(m);signal.throwIfAborted();
   expected.push({context_sha256:previous.sha256,checkpoint_sha256:null,receipt_sha256:String(current.descriptor.value.point_sha256),
    at:m.receipt.value.at,phase:'fractional_before_compatible_material_point',event_sequence:last.value.event_sequence,
    output_cursor:Number(last.value.output_cursor)+1,output_prefix_sha256:current.seed.value.before_material_prefix_sha256,snapshotRaw:m.beforeSnapshotRaw});
  }else need(current.packed.length===0);
  const checkpoints=list(segment.checkpoints);need(checkpoints.length>=1);let prior:WireDocument|undefined;
  for(const value of checkpoints){
   const d=sourceDescriptor(value,512*1024),cp=await readSupplyCheckpoint(get(value),current,prior);current.checkpoints.push(cp);
   expected.push({context_sha256:current.sha256,checkpoint_sha256:d.sha256,receipt_sha256:null,at:cp.value.at,phase:cp.value.phase,
    event_sequence:cp.value.event_sequence,output_cursor:cp.value.output_cursor,output_prefix_sha256:cp.value.output_prefix_sha256,snapshotRaw:cp.fields.last_confirmed!});
   need(expected.length<=512);prior=cp;
  }
  contexts.push(current);previous=current;last=prior;
 }
 need(last&&previous&&expected.length===anchor.frames);
 const terminal=closed(r.terminal,['status','hold']);
 if(terminal.status==='completed'){
  const n=object(previous.seed.value.original_numerical);need(terminal.hold===null&&last.value.grid_index===n.step_count);
  need(compare(exactAt(last.value.at).elapsed,mul(binary64(n.step_seconds),{n:BigInt(Number(n.step_count)),d:1n}))===0);
 }else need(terminal.status==='hold'&&typeof terminal.hold==='string'&&terminal.hold.length<=1024
  &&terminal.hold.includes(':')&&terminal.hold.slice(0,terminal.hold.indexOf(':')).endsWith('_HOLD'));
 const rootFrames=list(r.frames),frames:WireDocument[]=[];need(rootFrames.length===anchor.frames);let scalars=0;
 for(const [index,source]of expected.entries()){
  const d=closed(publicFrames[index],[...DESCRIPTOR,...FILE]),original=closed(rootFrames[index],DESCRIPTOR);
  need(d.index===index&&d.path===`frame-${index}.json`);for(const key of DESCRIPTOR)equal(d[key],original[key]);
  for(const key of META)equal(d[key],key==='index'?index:source[key as keyof Expected]);
  digest(d.frame_sha256);digest(d.state_sha256);
  const raw=await read(String(d.path));need(raw.byteLength===d.bytes&&await sha256(raw)===d.sha256);
  const dto=document(text(raw)),q=closed(dto.value,['schema_version','artifact_sha256','index','frame']);
  need(q.schema_version==='supply-morphology-public-frame-v1'&&q.artifact_sha256===anchor.artifact_sha256&&q.index===index);
  const frame=document(dto.fields.frame!),f=closed(frame.value,[...FLAGS,...META,'snapshot','model_floor_area','state_layout','leaves','internodes','global_ledgers']);
  researchFlags(f,'supply-morphology-replay-frame-v1');for(const key of META)equal(f[key],d[key]);
  need(frame.fields.snapshot===source.snapshotRaw&&await wireHash(frame.raw)===d.frame_sha256);
  const snapshot=wireFields(source.snapshotRaw);need(await wireHash(snapshot.state!)===d.state_sha256);
  const state=list(object(f.snapshot).state,32768);need(state.length>=1);scalars+=state.length;need(scalars<=32768);
  if(index){const a=exactAt(expected[index-1]!.at),b=exactAt(source.at);need(a.origin===b.origin&&compare(a.elapsed,b.elapsed)<=0&&Number(source.output_cursor)===Number(expected[index-1]!.output_cursor)+1);}
  frames.push(dto);
 }
 signal.throwIfAborted();need(scalars===i.sample_scalars&&downloaded===declared&&used.size===blobs.size);
 return {validation_scope:'source_graph_only_quantities_pending' as const,artifact_sha256:anchor.artifact_sha256,index,root,blobs,contexts,receipts,frames,sample_scalars:scalars,downloaded_bytes:downloaded};
}
