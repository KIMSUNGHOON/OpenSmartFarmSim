import {expect,it} from 'vitest';
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';

// Own constructed browser wire, not a server-issued artifact or numerical evidence.
// The old own-public root supplies only its fixed code-path inventory, not a DTO cast.
const oldPublicRoot = new URL('../public/supply-material-replay/own-public-v1/root.json',import.meta.url);
const extraCodePaths = [
 'backend/app/crop_supply_material_repeat_owner.py',
 'backend/app/crop_supply_material_repeat_point.py',
 'backend/app/crop_supply_material_repeat_proof.py',
 'backend/app/crop_supply_material_repeat_artifact_producer.py',
 'backend/app/crop_supply_material_repeat_artifact_reader.py',
];
const utf8 = new TextEncoder();
const hash = (raw:Uint8Array) => createHash('sha256').update(raw).digest('hex');
const labelHash = (text:string) => hash(utf8.encode(text));
const reference = (name:string) => {
 const raw=utf8.encode('own synthetic browser marker:'+name);
 return {sha256:hash(raw),bytes:raw.byteLength};
};
function canonical(value:unknown):string {
 if(value===null||typeof value!=='object'){const text=JSON.stringify(value);if(text===undefined)throw Error('Unsupported own fixture value');return text;}
 if(Array.isArray(value))return '['+value.map(canonical).join(',')+']';
 const row=value as Record<string,unknown>;
 return '{'+Object.keys(row).sort().map(key=>JSON.stringify(key)+':'+canonical(row[key])).join(',')+'}';
}
function ownManifest() {
 const legacy=JSON.parse(readFileSync(oldPublicRoot,'utf8')) as {code_sha256:Record<string,string>};
 const paths=[...new Set([...Object.keys(legacy.code_sha256),...extraCodePaths])].sort();
 const code=Object.fromEntries(paths.map(path=>[path,labelHash('own synthetic browser code:'+path)]));
 const at={time_origin_utc:'2026-10-01T07:00:00Z',elapsed_seconds_exact:{numerator:'60',denominator:'1',unit:'s'}};
 const anchor={cursor:reference('anchor-cursor'),current:reference('anchor-current'),basis:reference('anchor-basis')};
 const final={cursor:reference('final-cursor'),current:reference('final-current'),basis:reference('final-basis')};
 const definition=reference('repeat-definition'),original=reference('original-root'),notice=reference('NOTICE');
 const page=reference('history-page'),witness=reference('physical-witness'),receipt=reference('full-public-receipt');
 const before=reference('material-before-source-frame'),after=reference('material-after-source-frame');
 const projectedBefore=reference('projected-before'),projectedAfter=reference('projected-after');
 const selections=Object.fromEntries(['base','forcing','material'].map(kind=>[kind,{
  definition:reference(kind+'-definition'),cursor:reference(kind+'-cursor'),
 }]));
 const ordered=(rows:{sha256:string;bytes:number}[])=>rows.sort((a,b)=>a.sha256<b.sha256?-1:a.sha256>b.sha256?1:0);
 const root={
  schema_version:'supply-material-repeat-artifact-v1',scope:'software_research_only',G0_G4:'not_assessed',R2:'not_approved',
  time_kind:'synthetic_model_clock_not_observation',claim_scope:'stored_synthetic_repeat_material_window_only',
  code_sha256:code,
  source:{owner_version:'supply-material-repeat-owner-research-v1',definition,anchor,final,original_root:original,original_frame_index:0,...selections},
  blob_groups:{original:ordered([original,notice]),
   ...Object.fromEntries(Object.entries(selections).map(([kind,value])=>[kind,ordered(Object.values(value))])),
   repeat:ordered([definition,...Object.values(anchor),...Object.values(final),page,witness,before,after]),
   points:[receipt],frames:ordered([projectedBefore,projectedAfter]),
  },
  transitions:[{index:0,kind:'material_adoption',previous_cursor_sha256:anchor.cursor.sha256,cursor:final.cursor,
   history_page:page,before_current:anchor.current,after_current:final.current,before_basis:anchor.basis,after_basis:final.basis,
   frame_indices:[0,1],point:{witness,receipt,calculation_sha256:labelHash('own synthetic inner calculation'),
    candidate_calculation_sha256:labelHash('own synthetic candidate calculation'),before_frame:before,after_frame:after},
  }],
  frames:[{index:0,transition_index:0,phase:'material_before',at,active_basis_sha256:anchor.basis.sha256,frame:projectedBefore,state_scalars:112},
   {index:1,transition_index:0,phase:'material_after',at,active_basis_sha256:final.basis.sha256,frame:projectedAfter,state_scalars:115}],
  effective_rights:{use:true,display:true,redistribute:false},
  window:{first_at:at,last_at:at,covers_whole_season:false,selection:'committed_repeat_material_and_confirmed_remainder'},
  terminal:{status:'confirmed_prefix',hold:null,scope:'declared_synthetic_forcing_plan_only'},notice,
 };
 const raw=utf8.encode(canonical(root));
 return {root,raw,expected:{rootSha256:hash(raw),codeSha256:structuredClone(code)}};
}
type ManifestView={
 schema_version:string;effective_rights:{use:boolean;display:boolean;redistribute:boolean};
 frames:{index:number;phase:string;at:unknown;active_basis_sha256:string;state_scalars:number}[];
};
type WireAPI={decodeRepeatManifest(raw:Uint8Array,expected:{rootSha256:string;codeSha256:Record<string,string>}):Promise<ManifestView>};

it('decodes only the caller-pinned repeat manifest and preserves its same-time material pair',async()=>{
 const own=ownManifest();
 expect(Object.keys(own.root.code_sha256)).toHaveLength(120);
 expect(own.expected.rootSha256).toBe('8c9e94ecff41d88ca51a6a414e546101d92a49f30f304557893474807997160e');
 expect(own.raw.byteLength).toBe(20502);
 expect(own.root.frames.map(frame=>frame.index)).toEqual([0,1]);
 expect(own.root.frames[0]!.at).toEqual(own.root.frames[1]!.at);
 // Computed import is deferred until these real raw-fixture/hash gates have run.
 const modulePath='./supplyMaterialRepeatWire';
 const wire:WireAPI=await import(/* @vite-ignore */ modulePath);
 const decoded=await wire.decodeRepeatManifest(own.raw,own.expected);
 expect(decoded).toEqual(own.root);
 expect(decoded.schema_version).toBe('supply-material-repeat-artifact-v1');
 expect(decoded.effective_rights).toEqual({use:true,display:true,redistribute:false});
 expect(decoded.frames.map(frame=>[frame.index,frame.phase,frame.state_scalars])).toEqual([
  [0,'material_before',112],[1,'material_after',115],
 ]);
 expect(decoded.frames[0]!.at).toEqual(decoded.frames[1]!.at);
 expect(decoded.frames[0]!.active_basis_sha256).not.toBe(decoded.frames[1]!.active_basis_sha256);
 await expect(wire.decodeRepeatManifest(own.raw,{...own.expected,rootSha256:'0'.repeat(64)})).rejects.toThrow();
});

type OwnManifestRoot=ReturnType<typeof ownManifest>['root'];

async function acceptedManifestForAdverse(){
 const own=ownManifest();
 expect(Object.keys(own.root.code_sha256)).toHaveLength(120);
 expect(own.raw.byteLength).toBe(20502);
 expect(hash(own.raw)).toBe('8c9e94ecff41d88ca51a6a414e546101d92a49f30f304557893474807997160e');
 const modulePath='./supplyMaterialRepeatWire';
 const wire:WireAPI=await import(/* @vite-ignore */ modulePath);
 expect(await wire.decodeRepeatManifest(own.raw,own.expected)).toEqual(own.root);
 return {own,wire};
}

const structuredManifestFaults:{name:string;change:(root:OwnManifestRoot)=>unknown}[]=[
 {name:'an unknown root field',change:root=>({...root,unregistered_manifest_field:true})},
 {name:'an unsupported schema version',change:root=>({...root,schema_version:'supply-material-repeat-artifact-v0'})},
 {name:'a denied use grant',change:root=>({...root,effective_rights:{...root.effective_rights,use:false}})},
 {name:'a code digest different from the caller pin',change:root=>{
  const path=Object.keys(root.code_sha256)[0]!;
  expect(root.code_sha256[path]).not.toBe('0'.repeat(64));
  return {...root,code_sha256:{...root.code_sha256,[path]:'0'.repeat(64)}};
 }},
 {name:'a reversed material pair descriptor order',change:root=>({...root,
  transitions:root.transitions.map((transition,index)=>index===0?{...transition,frame_indices:[1,0]}:transition),
 })},
 {name:'a conflicting byte length for the same final-current digest',change:root=>({...root,
  source:{...root.source,final:{...root.source.final,current:{...root.source.final.current,
   bytes:root.source.final.current.bytes+1,
  }}},
 })},
 {name:'a sampled-scalar total above the parent limit',change:root=>({...root,
  frames:root.frames.map((frame,index)=>index===0?{...frame,state_scalars:32768}:frame),
 })},
 {name:'year zero in every otherwise matching At',change:root=>{
  const at={...root.frames[0]!.at,time_origin_utc:'0000-10-01T07:00:00Z'};
  return {...root,frames:root.frames.map(frame=>({...frame,at})),
   window:{...root.window,first_at:at,last_at:at}};
 }},
];

it.each(structuredManifestFaults)('rejects $name even when the changed raw root is caller-pinned',async({change})=>{
 const {own,wire}=await acceptedManifestForAdverse();
 const changed=utf8.encode(canonical(change(own.root)));
 expect(changed.byteLength).toBeLessThanOrEqual(2097152);
 expect(hash(changed)).not.toBe(own.expected.rootSha256);
 const expected={rootSha256:hash(changed),codeSha256:structuredClone(own.expected.codeSha256)};
 await expect(wire.decodeRepeatManifest(changed,expected)).rejects.toThrow();
 expect(hash(own.raw)).toBe(own.expected.rootSha256);
 expect(own.expected.codeSha256).toEqual(own.root.code_sha256);
 expect(await wire.decodeRepeatManifest(own.raw,own.expected)).toEqual(own.root);
});

const malformedManifestRaws:{name:string;change:(raw:Uint8Array)=>Uint8Array}[]=[
 {name:'a duplicated root key with the same valid value',change:raw=>{
  const text=new TextDecoder('utf-8',{fatal:true}).decode(raw);
  const token='"schema_version":"supply-material-repeat-artifact-v1"';
  expect(text.indexOf(token)).toBeGreaterThanOrEqual(0);
  expect(text.indexOf(token)).toBe(text.lastIndexOf(token));
  return utf8.encode(text.replace(token,token+','+token));
 }},
 {name:'malformed UTF-8 bytes',change:raw=>{
  const changed=raw.slice();
  changed[0]=0xff;
  return changed;
 }},
];

it.each(malformedManifestRaws)('rejects $name after a successful manifest baseline',async({change})=>{
 const {own,wire}=await acceptedManifestForAdverse();
 const changed=change(own.raw);
 expect(changed.byteLength).toBeLessThanOrEqual(2097152);
 expect(hash(changed)).not.toBe(own.expected.rootSha256);
 const expected={rootSha256:hash(changed),codeSha256:structuredClone(own.expected.codeSha256)};
 await expect(wire.decodeRepeatManifest(changed,expected)).rejects.toThrow();
 expect(hash(own.raw)).toBe(own.expected.rootSha256);
 expect(own.expected.codeSha256).toEqual(own.root.code_sha256);
 expect(await wire.decodeRepeatManifest(own.raw,own.expected)).toEqual(own.root);
});


import {wireFields as repeatOldFields,wireItems as repeatOldItems} from './fundedLeafReplayWire';
import {wireObject as repeatRawObject} from './supplyMorphologyGraphValues';
import {exactClock as repeatExpectedClock} from './supplyMorphologyQuantityCore';

type RepeatFrameView={
 schema_version:string;index:number;phase:string;
 binding:{active_basis_sha256:string;checkpoint_cursor_sha256:string|null;source:Record<string,{sha256:string;bytes:number}>};
 snapshot:{at:unknown;state:number[];derived:unknown};
 leaves:{geometry:{value:number;unit:string};clock_exact:unknown;geometry_diagnostics:Record<string,unknown>}[];
 internodes:{geometry:{value:number;unit:string};clock_exact:unknown;geometry_diagnostics:Record<string,unknown>}[];
 accounts:{event_sequence:bigint};
};
type RepeatFrameWireAPI=WireAPI&{
 decodeRepeatFrame(raw:Uint8Array,issuedManifest:object,index:number):Promise<RepeatFrameView>;
};
const repeatHugeSequence='1'+'0'.repeat(309);
const repeatOldFramePins=[
 '2aa751390cf09638b214886d378ec0b9115d8ea53657e287aa1c54db53f5b999',
 'd0f6cc6e76367a67175a44481fddf7e0a2357024ceb50538f1eaf7d54407ee26',
];
function ownRepeatFramePair(){
 const own=ownManifest();
 const originRecords={physical:reference('own physical origin record'),geometry:reference('own geometry origin record')};
 own.root.blob_groups.repeat.push(...Object.values(originRecords));
 own.root.blob_groups.repeat.sort((a,b)=>a.sha256<b.sha256?-1:1);
 const rows=([0,1]as const).map(index=>{
  const file=readFileSync(new URL(`../public/supply-material-replay/own-public-v1/frame-${index}.json`,import.meta.url));
  expect(hash(file)).toBe(repeatOldFramePins[index]);
  const legacy=repeatOldFields(repeatOldFields(file.toString('utf8')).frame!);
  const transition=own.root.transitions[0]!,point=transition.point;
  const binding={kind:index===0?'dense_material_before':'adopted_material_after',transition_index:0,
   history_page_sha256:transition.history_page.sha256,transition_cursor_sha256:transition.cursor.sha256,
   active_basis_sha256:index===0?transition.before_basis.sha256:transition.after_basis.sha256,
   context_cursor_sha256:transition.previous_cursor_sha256,checkpoint_cursor_sha256:index===0?null:transition.cursor.sha256,
   source:{...(index===0?{}:{current:transition.after_current}),receipt:point.receipt,witness:point.witness,
    material_frame:index===0?point.before_frame:point.after_frame},
  };
  const organs=(kind:'leaves'|'internodes')=>'['+repeatOldItems(legacy[kind]!).map((raw,i)=>{
   const row=repeatOldFields(raw),diagnostics=repeatOldFields(row.geometry_diagnostics!);
   diagnostics.kind=JSON.stringify(index===0?'dense_stored_transfers':'stored_confirmed');
   diagnostics.canonical_status=JSON.stringify(index===0?'not_stored_at_dense_boundary':'stored');
   if(index===0){diagnostics.canonical_gap_exact='null';diagnostics.canonical_potential_difference_exact='null';}
   return repeatRawObject({...row,source_index:String(i),geometry_diagnostics:repeatRawObject(diagnostics)});
  }).join(',')+']';
  const accountFields=Object.fromEntries(['schedule','global_ledgers','point_totals_exact','lifetime_transfers_exact','transfer_origins']
   .map(key=>[key,legacy[key]!]));
  // Unit fixture only: these old public frames expose the same validated ledger-row shape.
  // Their fixed global map is used as the new own local-map specimen, not source authority.
  accountFields.local_ledgers=legacy.global_ledgers!;
  // Both new own rows use these two selected synthetic origin-record descriptors.
  accountFields.transfer_origins=canonical(Object.fromEntries(Object.entries(originRecords).map(([kind,record])=>[kind,record.sha256])));
  accountFields.event_sequence=index===0?repeatHugeSequence:(10n**309n+1n).toString();
  const snapshot=repeatOldFields(legacy.snapshot!),state=repeatOldItems(snapshot.state!);state[0]='-7.25';
  snapshot.state='['+state.join(',')+']';
  const fields:Record<string,string>={};
  for(const key of ['G0_G4','R2','at','index','model_floor_area','phase','scope','state_layout','time_kind'])fields[key]=legacy[key]!;
  Object.assign(fields,{schema_version:JSON.stringify('supply-material-repeat-replay-frame-v1'),
   claim_scope:JSON.stringify('stored_synthetic_repeat_material_window_only'),binding:canonical(binding),
   snapshot:repeatRawObject(snapshot),leaves:organs('leaves'),internodes:organs('internodes'),accounts:repeatRawObject(accountFields)});
  const raw=utf8.encode(repeatRawObject(fields));
  const expected:Record<string,unknown>={};
  for(const [key,value]of Object.entries(fields))if(key!=='accounts')expected[key]=JSON.parse(value);
  expected.accounts=Object.fromEntries(Object.entries(accountFields).map(([key,value])=>[
   key,key==='event_sequence'?BigInt(value):JSON.parse(value),
  ]));
  return {raw,expected,index,at:JSON.parse(legacy.at!)as OwnManifestRoot['frames'][number]['at'],stateCount:state.length};
 });
 own.root.frames=own.root.frames.map((descriptor,index)=>({...descriptor,at:rows[index]!.at,state_scalars:rows[index]!.stateCount,
  frame:{sha256:hash(rows[index]!.raw),bytes:rows[index]!.raw.byteLength},
 }));
 own.root.blob_groups.frames=own.root.frames.map(descriptor=>({...descriptor.frame})).sort((a,b)=>a.sha256<b.sha256?-1:1);
 own.root.window={...own.root.window,first_at:rows[0]!.at,last_at:rows[1]!.at};
 const raw=utf8.encode(canonical(own.root));
 return {rows,root:own.root,raw,expected:{rootSha256:hash(raw),codeSha256:structuredClone(own.expected.codeSha256)}};
}

it('decodes own per-basis material frames only under issued manifest evidence and preserves huge integers and copies',async()=>{
 const pair=ownRepeatFramePair();
 expect(pair.rows.map(row=>row.stateCount)).toEqual([176,182]);
 expect(pair.rows.map(row=>[hash(row.raw),row.raw.byteLength])).toEqual([["99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1",168588],["49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73",180344]]);
 const modulePath='./supplyMaterialRepeatWire';
 const wire:RepeatFrameWireAPI=await import(/* @vite-ignore */ modulePath);
 const issued=await wire.decodeRepeatManifest(pair.raw,pair.expected);
 expect(issued).toEqual(pair.root);
 const selectedOrigins=new Set(pair.root.blob_groups.repeat.map(record=>record.sha256));
 for(const row of pair.rows){
  const origins=(row.expected.accounts as {transfer_origins:Record<string,string>}).transfer_origins;
  expect(Object.keys(origins).sort()).toEqual(['geometry','physical']);
  for(const origin of Object.values(origins)){expect(origin).toMatch(/^[a-f0-9]{64}$/);expect(selectedOrigins.has(origin)).toBe(true);}
 }
 for(const row of pair.rows){
  const expected=row.expected as {leaves:Record<string,unknown>[];internodes:Record<string,unknown>[];
   at:{elapsed_seconds_exact:unknown};accounts:{lifetime_transfers_exact:Record<string,unknown>}};
  expect(expected.leaves).toHaveLength(row.index===0?11:12);expect(expected.internodes).toHaveLength(row.index===0?12:13);
  for(const organ of [...expected.leaves,...expected.internodes]){
   expect(organ.clock_exact).toEqual(repeatExpectedClock(organ.birth,expected.at.elapsed_seconds_exact,
    expected.accounts.lifetime_transfers_exact.indoor_air_temperature_time));
  }
 }
 expect(typeof wire.decodeRepeatFrame).toBe('function');
 const beforeInput=pair.rows[0]!.raw.slice();
 const pendingBefore=wire.decodeRepeatFrame(beforeInput,issued,0);beforeInput.fill(0);
 const before=await pendingBefore,after=await wire.decodeRepeatFrame(pair.rows[1]!.raw,issued,1);
 expect(before).toEqual(pair.rows[0]!.expected);expect(after).toEqual(pair.rows[1]!.expected);
 expect(before.accounts.event_sequence).toBe(10n**309n);expect(after.accounts.event_sequence).toBe(10n**309n+1n);
 expect(before.snapshot.state[0]).toBe(-7.25);expect(after.snapshot.state[0]).toBe(-7.25);
 expect(before.binding.checkpoint_cursor_sha256).toBeNull();expect(after.binding.checkpoint_cursor_sha256).not.toBeNull();
 expect(before.leaves[0]!.geometry_diagnostics.canonical_gap_exact).toBeNull();
 expect(after.leaves[0]!.geometry_diagnostics.canonical_gap_exact).not.toBeNull();
 await expect(wire.decodeRepeatFrame(pair.rows[0]!.raw,structuredClone(issued),0)).rejects.toThrow();
 // Exposed RootDTO mutations cannot replace the privately pinned descriptor/basis.
 Object.assign(issued.frames[0]!,{active_basis_sha256:'0'.repeat(64),frame:{sha256:hash(pair.rows[1]!.raw),bytes:pair.rows[1]!.raw.byteLength}});
 await expect(wire.decodeRepeatFrame(pair.rows[1]!.raw,issued,0)).rejects.toThrow();
 beforeInput.fill(0);before.snapshot.state[0]=999;before.leaves[0]!.geometry.value=999;
 before.binding.source.receipt!.bytes=1;
 expect(await wire.decodeRepeatFrame(pair.rows[0]!.raw,issued,0)).toEqual(pair.rows[0]!.expected);
});

type RepeatAdversePath=readonly (string|number)[];
type RepeatOwnPair=ReturnType<typeof ownRepeatFramePair>;

// Locate only token spans in the already positive own fixture; numbers stay opaque.
function repeatAdverseTokenEnd(text:string,start:number):number {
 const first=text[start];
 if(first==='"'){
  for(let i=start+1;i<text.length;i++){
   if(text[i]==='\\'){i++;continue;}
   if(text[i]==='"')return i+1;
  }
  throw Error('Unclosed own fixture string');
 }
 if(first==='{'||first==='['){
  let depth=0;
  for(let i=start;i<text.length;i++){
   const ch=text[i];
   if(ch==='"'){i=repeatAdverseTokenEnd(text,i)-1;continue;}
   if(ch==='{'||ch==='[')depth++;
   if(ch==='}'||ch===']'){depth--;if(depth===0)return i+1;}
  }
  throw Error('Unclosed own fixture container');
 }
 let end=start;
 while(end<text.length&&text[end]!==','&&text[end]!=='}'&&text[end]!==']')end++;
 if(end===start)throw Error('Empty own fixture token');
 return end;
}
function repeatAdverseRange(text:string,path:RepeatAdversePath):[number,number] {
 let start=0,end=repeatAdverseTokenEnd(text,0);
 expect(end).toBe(text.length);
 for(const part of path){
  let cursor=start+1,found=false;
  if(typeof part==='string'){
   expect(text[start]).toBe('{');
   while(cursor<end-1){
    expect(text[cursor]).toBe('"');
    const keyEnd=repeatAdverseTokenEnd(text,cursor);
    const key:unknown=JSON.parse(text.slice(cursor,keyEnd));
    expect(typeof key).toBe('string');expect(text[keyEnd]).toBe(':');
    const valueStart=keyEnd+1,valueEnd=repeatAdverseTokenEnd(text,valueStart);
    if(key===part){start=valueStart;end=valueEnd;found=true;break;}
    cursor=valueEnd+1;
   }
  }else{
   expect(text[start]).toBe('[');expect(Number.isSafeInteger(part)&&part>=0).toBe(true);
   let index=0;
   while(cursor<end-1){
    const valueEnd=repeatAdverseTokenEnd(text,cursor);
    if(index===part){start=cursor;end=valueEnd;found=true;break;}
    index++;cursor=valueEnd+1;
   }
  }
  expect(found).toBe(true);
 }
 return [start,end];
}
function repeatAdverseRead(raw:Uint8Array,path:RepeatAdversePath):string {
 const text=new TextDecoder('utf-8',{fatal:true}).decode(raw),[start,end]=repeatAdverseRange(text,path);
 return text.slice(start,end);
}
function repeatAdverseEdit(raw:Uint8Array,path:RepeatAdversePath,change:(token:string)=>string):Uint8Array {
 const text=new TextDecoder('utf-8',{fatal:true}).decode(raw),[start,end]=repeatAdverseRange(text,path);
 return utf8.encode(text.slice(0,start)+change(text.slice(start,end))+text.slice(end));
}
function repeatAdverseExactPlusOne(raw:string):string {
 const read=(key:string)=>{
  const [start,end]=repeatAdverseRange(raw,[key]);
  const value:unknown=JSON.parse(raw.slice(start,end));
  if(typeof value!=='string')throw Error('Own Exact field must be a string');
  return value;
 };
 const numerator=read('numerator'),denominator=read('denominator'),unit=read('unit');
 expect(canonical({numerator,denominator,unit})).toBe(raw);
 expect(BigInt(denominator)>0n&&BigInt(numerator)>=0n).toBe(true);
 return canonical({numerator:(BigInt(numerator)+BigInt(denominator)).toString(),denominator,unit});
}
type RepeatFrameFault={name:string;index:0|1;paths:readonly RepeatAdversePath[];reason:string;
 change:(raw:Uint8Array,pair:RepeatOwnPair)=>Uint8Array};
const repeatFrameFaults:RepeatFrameFault[]=[
 {name:'an embedded selected-index mismatch',index:0,paths:[['index']],reason:'selected frame descriptor differs',
  change:raw=>repeatAdverseEdit(raw,['index'],token=>{expect(token).toBe('0');return '1';})},
 {name:'an after-basis digest on the dense before side',index:0,paths:[['binding','active_basis_sha256']],reason:'selected frame binding differs',
  change:(raw,pair)=>repeatAdverseEdit(raw,['binding','active_basis_sha256'],token=>{
   const before=pair.root.transitions[0]!.before_basis.sha256,after=pair.root.transitions[0]!.after_basis.sha256;
   expect(before).not.toBe(after);expect(token).toBe(JSON.stringify(before));return JSON.stringify(after);
  })},
 {name:'a leaf area labelled in metres',index:0,paths:[['leaves',0,'geometry','unit']],reason:'unsupported tag',
  change:raw=>repeatAdverseEdit(raw,['leaves',0,'geometry','unit'],token=>{expect(token).toBe('"m2"');return '"m"';})},
 {name:'internode carbon read from row position instead of compartment ID',index:0,
  paths:[['internodes',0,'carbon','value']],reason:'organ metric does not match active state coordinate',
  change:raw=>{
   expect(repeatAdverseRead(raw,['state_layout','original','stem_root_compartments',0,'kind'])).toBe('"root_system"');
   expect(repeatAdverseRead(raw,['state_layout','original','stem_root_compartments',1,'compartment_id']))
    .toBe(repeatAdverseRead(raw,['internodes',0,'id']));
   const wrong=repeatAdverseRead(raw,['snapshot','state',139]),right=repeatAdverseRead(raw,['snapshot','state',140]);
   expect(wrong).not.toBe(right);expect(/[.eE]/.test(wrong)&&/[.eE]/.test(right)).toBe(true);
   return repeatAdverseEdit(raw,['internodes',0,'carbon','value'],token=>{expect(token).toBe(right);return wrong;});
  }},
 {name:'a source_index different from its row position',index:0,paths:[['leaves',0,'source_index']],reason:'organ identity/order/parent differs',
  change:raw=>repeatAdverseEdit(raw,['leaves',0,'source_index'],token=>{expect(token).toBe('0');return '1';})},
 {name:'a current exact clock different from its received birth inputs',index:0,paths:[['leaves',0,'clock_exact']],reason:'birth-relative exact clock differs',
  change:raw=>repeatAdverseEdit(raw,['leaves',0,'clock_exact'],repeatAdverseExactPlusOne)},
 {name:'a stored canonical value at the dense null boundary',index:0,paths:[['leaves',0,'geometry_diagnostics','canonical_gap_exact']],
  reason:'dense canonical diagnostics are not stored',change:raw=>repeatAdverseEdit(raw,['leaves',0,'geometry_diagnostics','canonical_gap_exact'],token=>{
   expect(token).toBe('null');return canonical({numerator:'0',denominator:'1',unit:'m2'});
  })},
 {name:'a null canonical observation on a confirmed frame',index:1,paths:[['leaves',0,'geometry_diagnostics','canonical_gap_exact']],
  reason:'object required',change:raw=>repeatAdverseEdit(raw,['leaves',0,'geometry_diagnostics','canonical_gap_exact'],token=>{
   expect(token).not.toBe('null');return 'null';
  })},
 {name:'a decimal token in the exact integer counter slot',index:0,paths:[['accounts','event_sequence']],reason:'canonical nonnegative integer required',
  change:raw=>repeatAdverseEdit(raw,['accounts','event_sequence'],token=>{expect(token).toBe(repeatHugeSequence);return '9007199254740993.0';})},
 {name:'a valid origin digest outside the selected descriptor closure',index:0,paths:[['accounts','transfer_origins','physical']],
  reason:'selected origin descriptor missing',change:(raw,pair)=>{
   const origin=labelHash('own Frame negative unselected origin');
   const selected=new Set(Object.values(pair.root.blob_groups).flatMap(records=>records.map(record=>record.sha256)));
   expect(origin).toMatch(/^[a-f0-9]{64}$/);expect(selected.has(origin)).toBe(false);
   return repeatAdverseEdit(raw,['accounts','transfer_origins','physical'],()=>JSON.stringify(origin));
  }},
 {name:'a coherent lifetime diagnostic different from the received transfer',index:0,
  paths:[['leaves',0,'geometry_diagnostics','lifetime_potential_exact'],['leaves',0,'geometry_diagnostics','lifetime_deficit_exact']],
  reason:'available lifetime transfer differs',change:raw=>{
   const first=repeatAdverseEdit(raw,['leaves',0,'geometry_diagnostics','lifetime_potential_exact'],repeatAdverseExactPlusOne);
   return repeatAdverseEdit(first,['leaves',0,'geometry_diagnostics','lifetime_deficit_exact'],repeatAdverseExactPlusOne);
  }},
 {name:'an integer-spelled Quantity with the same positive floor value',index:0,paths:[['model_floor_area','value']],reason:'binary64 number required',
  change:raw=>repeatAdverseEdit(raw,['model_floor_area','value'],token=>{expect(token).toBe('1.0');return '1';})},
 {name:'an overflowing binary64 Quantity token',index:0,paths:[['model_floor_area','value']],reason:'finite binary64 required',
  change:raw=>repeatAdverseEdit(raw,['model_floor_area','value'],token=>{expect(token).toBe('1.0');return '1e309';})},
];
function repeatAdverseRepin(pair:RepeatOwnPair,index:0|1,raw:Uint8Array){
 const root=structuredClone(pair.root),previous=root.frames[index]!.frame;
 const frame={sha256:hash(raw),bytes:raw.byteLength};
 expect(frame.sha256).not.toBe(previous.sha256);
 root.frames[index]={...root.frames[index]!,frame};
 root.blob_groups.frames=root.blob_groups.frames.map(record=>record.sha256===previous.sha256?frame:record)
  .sort((a,b)=>a.sha256<b.sha256?-1:a.sha256>b.sha256?1:0);
 const manifestRaw=utf8.encode(canonical(root));
 return {root,raw:manifestRaw,expected:{rootSha256:hash(manifestRaw),codeSha256:structuredClone(pair.expected.codeSha256)}};
}

it.each(repeatFrameFaults)('rejects $name after fresh raw and manifest repinning',async fault=>{
 const pair=ownRepeatFramePair(),originalHashes=pair.rows.map(row=>hash(row.raw));
 expect(originalHashes).toEqual(['99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',
  '49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73']);
 expect(pair.rows.map(row=>row.raw.byteLength)).toEqual([168588,180344]);
 const modulePath='./supplyMaterialRepeatWire';
 const wire:RepeatFrameWireAPI=await import(/* @vite-ignore */ modulePath);
 const originalIssued=await wire.decodeRepeatManifest(pair.raw,pair.expected);
 expect(originalIssued).toEqual(pair.root);
 for(const row of pair.rows){
  expect(repeatAdverseEdit(row.raw,['index'],token=>token)).toEqual(row.raw);
  expect(await wire.decodeRepeatFrame(row.raw,originalIssued,row.index)).toEqual(row.expected);
 }
 const selected=pair.rows[fault.index]!;
 for(const path of fault.paths)expect(repeatAdverseEdit(selected.raw,path,token=>token)).toEqual(selected.raw);
 const changed=fault.change(selected.raw,pair);
 expect(changed.byteLength).toBeLessThanOrEqual(2097152);
 const counter=fault.index===0?repeatHugeSequence:(10n**309n+1n).toString();
 expect(repeatAdverseRead(changed,['accounts','event_sequence']))
  .toBe(fault.reason==='canonical nonnegative integer required'?'9007199254740993.0':counter);
 const repinned=repeatAdverseRepin(pair,fault.index,changed);
 const freshIssued=await wire.decodeRepeatManifest(repinned.raw,repinned.expected);
 expect(freshIssued).toEqual(repinned.root);
 await expect(wire.decodeRepeatFrame(changed,freshIssued,fault.index))
  .rejects.toThrow('Stored repeat artifact: '+fault.reason);
 const sibling=pair.rows[fault.index===0?1:0]!;
 expect(await wire.decodeRepeatFrame(sibling.raw,freshIssued,sibling.index)).toEqual(sibling.expected);
 expect(await wire.decodeRepeatFrame(selected.raw,originalIssued,selected.index)).toEqual(selected.expected);
 expect(pair.rows.map(row=>hash(row.raw))).toEqual(originalHashes);
 expect(hash(pair.raw)).toBe(pair.expected.rootSha256);
 expect(pair.expected.codeSha256).toEqual(pair.root.code_sha256);
});


type RepeatRequestRead=(selection:{kind:'manifest'}|{kind:'frame';index:number},signal:AbortSignal)=>Promise<Uint8Array>;
type RepeatRequestSelectionView={rootSha256:string;index:number;manifest:OwnManifestRoot;
 frame:RepeatFrameView&{at:OwnManifestRoot['frames'][number]['at']}};
type RepeatRequestView={select(index:number):Promise<RepeatRequestSelectionView>;
 current():RepeatRequestSelectionView|null;cancel():void};
type RepeatRequestAPI={SupplyMaterialRepeatRequest:new(read:RepeatRequestRead,
 expected:{rootSha256:string;codeSha256:Record<string,string>})=>RepeatRequestView};

it('keeps only the latest same-time repeat selection and clears rejected or cancelled state without sharing copies',async()=>{
 const pair=ownRepeatFramePair();
 expect(pair.rows.map(row=>[hash(row.raw),row.raw.byteLength])).toEqual([
  ['99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',168588],
  ['49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73',180344],
 ]);
 expect(pair.rows.map(row=>row.stateCount)).toEqual([176,182]);
 expect(hash(pair.raw)).toBe(pair.expected.rootSha256);
 expect(pair.root.frames[0]!.at).toEqual(pair.root.frames[1]!.at);
 expect(pair.root.frames[0]!.active_basis_sha256).not.toBe(pair.root.frames[1]!.active_basis_sha256);
 const wirePath='./supplyMaterialRepeatWire';
 const wire:RepeatFrameWireAPI=await import(/* @vite-ignore */ wirePath);
 const issued=await wire.decodeRepeatManifest(pair.raw,pair.expected);
 expect(issued).toEqual(pair.root);
 for(const row of pair.rows)expect(await wire.decodeRepeatFrame(row.raw,issued,row.index)).toEqual(row.expected);
 expect((pair.rows[0]!.expected.accounts as {event_sequence:bigint}).event_sequence).toBe(10n**309n);
 expect((pair.rows[1]!.expected.accounts as {event_sequence:bigint}).event_sequence).toBe(10n**309n+1n);
 // The missing Replay module/API is reached only after both complete Wire positives.
 const replayPath='./supplyMaterialRepeatReplay';
 const replay:RepeatRequestAPI=await import(/* @vite-ignore */ replayPath);
 expect(typeof replay.SupplyMaterialRepeatRequest).toBe('function');
 const calls:{selection:{kind:'manifest'}|{kind:'frame';index:number};signal:AbortSignal}[]=[];
 let holdFrame=false,corruptFrame=false,heldSignal:AbortSignal|undefined;
 let releaseOld:((raw:Uint8Array)=>void)|undefined,markHeld!:()=>void;
 const held=new Promise<void>(resolve=>{markHeld=resolve;});
 const read:RepeatRequestRead=async(selection,signal)=>{
  expect(signal).toBeInstanceOf(AbortSignal);expect(signal.aborted).toBe(false);
  calls.push({selection:structuredClone(selection),signal});
  if(selection.kind==='manifest'){
   expect(selection).toEqual({kind:'manifest'});return pair.raw.slice();
  }
  expect(selection).toEqual({kind:'frame',index:selection.index});
  expect(selection.index===0||selection.index===1).toBe(true);
  if(holdFrame&&selection.index===0){
   holdFrame=false;heldSignal=signal;
   return new Promise<Uint8Array>(resolve=>{releaseOld=resolve;markHeld();});
  }
  const raw=pair.rows[selection.index]!.raw.slice();
  if(corruptFrame&&selection.index===0){corruptFrame=false;raw[0]=0xff;}
  return raw;
 };
 const callerPins=structuredClone(pair.expected),request=new replay.SupplyMaterialRepeatRequest(read,callerPins);
 callerPins.rootSha256='0'.repeat(64);
 callerPins.codeSha256[Object.keys(callerPins.codeSha256)[0]!]='f'.repeat(64);
 const expected=(index:0|1)=>({rootSha256:pair.expected.rootSha256,index,manifest:pair.root,frame:pair.rows[index]!.expected});
 expect(request.current()).toBeNull();
 try{
  const first=request.select(0);expect(request.current()).toBeNull();
  const before=await first;expect(before).toEqual(expected(0));expect(request.current()).toEqual(expected(0));
  expect(before.frame.accounts.event_sequence).toBe(10n**309n);
  holdFrame=true;
  const old=request.select(0).then(value=>({kind:'fulfilled' as const,value}),error=>({kind:'rejected' as const,error}));
  expect(request.current()).toBeNull();await held;
  expect(heldSignal).toBeInstanceOf(AbortSignal);expect(heldSignal!.aborted).toBe(false);
  const pendingLatest=request.select(1);expect(request.current()).toBeNull();
  expect(heldSignal!.aborted).toBe(true);
  const latest=await pendingLatest;expect(latest).toEqual(expected(1));expect(request.current()).toEqual(expected(1));
  expect(latest.frame.at).toEqual(before.frame.at);
  expect(latest.frame.binding.active_basis_sha256).not.toBe(before.frame.binding.active_basis_sha256);
  expect(latest.frame.accounts.event_sequence).toBe(10n**309n+1n);
  const view=request.current();expect(view).not.toBeNull();if(view===null)throw Error('Latest selection required');
  expect(view).not.toBe(latest);expect(view.frame).not.toBe(latest.frame);expect(view.manifest).not.toBe(latest.manifest);
  latest.frame.snapshot.state[0]=999;latest.frame.leaves[0]!.geometry.value=999;
  latest.frame.accounts.event_sequence=0n;latest.manifest.frames[1]!.active_basis_sha256='0'.repeat(64);
  view.frame.snapshot.state[0]=777;view.frame.binding.source.receipt!.bytes=1;
  view.frame.accounts.event_sequence=1n;view.manifest.effective_rights.display=false;
  expect(request.current()).toEqual(expected(1));
  expect(releaseOld).toBeTypeOf('function');releaseOld!(pair.rows[0]!.raw.slice());
  expect((await old).kind).toBe('rejected');expect(request.current()).toEqual(expected(1));
  corruptFrame=true;
  const failed=request.select(0);expect(request.current()).toBeNull();
  await expect(failed).rejects.toThrow('Stored repeat artifact: selected frame SHA differs');
  expect(corruptFrame).toBe(false);expect(request.current()).toBeNull();
  const recovered=await request.select(1);expect(recovered).toEqual(expected(1));expect(request.current()).toEqual(expected(1));
  expect(calls.map(call=>call.selection)).toEqual([
   {kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'},{kind:'frame',index:0},
   {kind:'manifest'},{kind:'frame',index:1},{kind:'manifest'},{kind:'frame',index:0},
   {kind:'manifest'},{kind:'frame',index:1},
  ]);
  expect(new Set(calls.filter(call=>call.selection.kind==='manifest').map(call=>call.signal)).size).toBe(5);
  for(let i=0;i<calls.length;i+=2)expect(calls[i]!.signal).toBe(calls[i+1]!.signal);
  expect(calls[8]!.signal.aborted).toBe(false);request.cancel();
  expect(request.current()).toBeNull();
  expect(recovered).toEqual(expected(1));
  expect(pair.rows.map(row=>hash(row.raw))).toEqual([
   '99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',
   '49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73',
  ]);
  expect(hash(pair.raw)).toBe(pair.expected.rootSha256);expect(pair.expected.codeSha256).toEqual(pair.root.code_sha256);
 }finally{request.cancel();releaseOld?.(pair.rows[0]!.raw.slice());}
});


type RepeatRequestCall={selection:Parameters<RepeatRequestRead>[0];signal:AbortSignal};
async function repeatRequestAdversePair(){
 const pair=ownRepeatFramePair();
 expect(pair.rows.map(row=>[hash(row.raw),row.raw.byteLength])).toEqual([
  ['99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',168588],
  ['49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73',180344],
 ]);
 expect(pair.root.frames[0]!.at).toEqual(pair.root.frames[1]!.at);
 expect(pair.root.frames[0]!.active_basis_sha256).not.toBe(pair.root.frames[1]!.active_basis_sha256);
 const wirePath='./supplyMaterialRepeatWire';
 const wire:RepeatFrameWireAPI=await import(/* @vite-ignore */ wirePath);
 const issued=await wire.decodeRepeatManifest(pair.raw,pair.expected);expect(issued).toEqual(pair.root);
 for(const row of pair.rows)expect(await wire.decodeRepeatFrame(row.raw,issued,row.index)).toEqual(row.expected);
 const replayPath='./supplyMaterialRepeatReplay';
 const replay:RepeatRequestAPI=await import(/* @vite-ignore */ replayPath);
 expect(typeof replay.SupplyMaterialRepeatRequest).toBe('function');
 return {pair,Request:replay.SupplyMaterialRepeatRequest,
  expected:(index:0|1)=>({rootSha256:pair.expected.rootSha256,index,manifest:pair.root,frame:pair.rows[index]!.expected})};
}

it.each(['manifest','frame'] as const)('rejects an explicitly cancelled pending %s read even when transport ignores abort, then retries fresh',async stage=>{
 const {pair,Request,expected}=await repeatRequestAdversePair(),calls:RepeatRequestCall[]=[];
 let hold=false,heldSignal:AbortSignal|undefined,release:((raw:Uint8Array)=>void)|undefined,markHeld!:()=>void;
 const held=new Promise<void>(resolve=>{markHeld=resolve;});
 const read:RepeatRequestRead=async(selection,signal)=>{
  expect(signal).toBeInstanceOf(AbortSignal);expect(signal.aborted).toBe(false);
  calls.push({selection:structuredClone(selection),signal});
  if(selection.kind==='manifest')expect(selection).toEqual({kind:'manifest'});
  else{expect(selection).toEqual({kind:'frame',index:selection.index});expect(selection.index===0||selection.index===1).toBe(true);}
  const raw=selection.kind==='manifest'?pair.raw.slice():pair.rows[selection.index]!.raw.slice();
  if(hold&&selection.kind===stage){
   hold=false;heldSignal=signal;
   return new Promise<Uint8Array>(resolve=>{release=resolve;markHeld();});
  }
  return raw;
 };
 const request=new Request(read,pair.expected);
 const releaseBytes=()=>stage==='manifest'?pair.raw.slice():pair.rows[1]!.raw.slice();
 try{
  expect(await request.select(0)).toEqual(expected(0));expect(request.current()).toEqual(expected(0));
  hold=true;
  const pending=request.select(1).then(value=>({kind:'fulfilled' as const,value}),error=>({kind:'rejected' as const,error}));
  expect(request.current()).toBeNull();await held;
  expect(heldSignal).toBeInstanceOf(AbortSignal);expect(heldSignal!.aborted).toBe(false);
  expect(calls[2]!.selection).toEqual({kind:'manifest'});expect(calls[2]!.signal).toBe(heldSignal);
  if(stage==='frame'){expect(calls[3]!.selection).toEqual({kind:'frame',index:1});expect(calls[3]!.signal).toBe(heldSignal);}
  request.cancel();expect(heldSignal!.aborted).toBe(true);expect(request.current()).toBeNull();
  expect(release).toBeTypeOf('function');release!(releaseBytes());
  expect((await pending).kind).toBe('rejected');expect(request.current()).toBeNull();
  expect(calls).toHaveLength(stage==='manifest'?3:4);
  const recovered=await request.select(1);expect(recovered).toEqual(expected(1));expect(request.current()).toEqual(expected(1));
  expect(recovered.frame.accounts.event_sequence).toBe(10n**309n+1n);
  expect(calls.map(call=>call.selection)).toEqual(stage==='manifest'?[
   {kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'},{kind:'manifest'},{kind:'frame',index:1},
  ]:[
   {kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'},{kind:'frame',index:1},{kind:'manifest'},{kind:'frame',index:1},
  ]);
  expect(calls[0]!.signal).toBe(calls[1]!.signal);
  expect(calls.at(-2)!.signal).toBe(calls.at(-1)!.signal);
  expect(new Set(calls.filter(call=>call.selection.kind==='manifest').map(call=>call.signal)).size).toBe(3);
  expect(hash(pair.raw)).toBe(pair.expected.rootSha256);expect(pair.expected.codeSha256).toEqual(pair.root.code_sha256);
  expect(pair.rows.map(row=>hash(row.raw))).toEqual([
   '99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',
   '49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73',
  ]);
 }finally{request.cancel();release?.(releaseBytes());}
});

it('rejects invalid indices before transport and an admitted unavailable index before a Frame read, then recovers',async()=>{
 const {pair,Request,expected}=await repeatRequestAdversePair(),calls:RepeatRequestCall[]=[];
 const read:RepeatRequestRead=async(selection,signal)=>{
  expect(signal).toBeInstanceOf(AbortSignal);expect(signal.aborted).toBe(false);
  calls.push({selection:structuredClone(selection),signal});
  if(selection.kind==='manifest'){expect(selection).toEqual({kind:'manifest'});return pair.raw.slice();}
  expect(selection).toEqual({kind:'frame',index:selection.index});expect(selection.index===0||selection.index===1).toBe(true);
  return pair.rows[selection.index]!.raw.slice();
 };
 const request=new Request(read,pair.expected);
 try{
  expect(await request.select(0)).toEqual(expected(0));expect(request.current()).toEqual(expected(0));
  for(const index of [-1,512,0.5,NaN,true,'0']){
   const pending:Promise<unknown>=Reflect.apply(request.select,request,[index]);
   expect(request.current()).toBeNull();await expect(pending).rejects.toThrow();expect(calls).toHaveLength(2);
  }
  const unavailable=request.select(2);expect(request.current()).toBeNull();
  await expect(unavailable).rejects.toThrow();expect(request.current()).toBeNull();
  expect(calls.map(call=>call.selection)).toEqual([{kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'}]);
  expect(await request.select(1)).toEqual(expected(1));expect(request.current()).toEqual(expected(1));
  expect(calls.map(call=>call.selection)).toEqual([
   {kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'},{kind:'manifest'},{kind:'frame',index:1},
  ]);
  expect(calls[0]!.signal).toBe(calls[1]!.signal);expect(calls[3]!.signal).toBe(calls[4]!.signal);
  expect(new Set(calls.filter(call=>call.selection.kind==='manifest').map(call=>call.signal)).size).toBe(3);
  expect(hash(pair.raw)).toBe(pair.expected.rootSha256);expect(pair.expected.codeSha256).toEqual(pair.root.code_sha256);
  expect(pair.rows.map(row=>hash(row.raw))).toEqual([
   '99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',
   '49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73',
  ]);
 }finally{request.cancel();}
});

it('clears a latest corrupt-manifest failure before any Frame read and validates a fresh retry',async()=>{
 const {pair,Request,expected}=await repeatRequestAdversePair(),calls:RepeatRequestCall[]=[];
 let corrupt=false,changedHash:string|undefined;
 const read:RepeatRequestRead=async(selection,signal)=>{
  expect(signal).toBeInstanceOf(AbortSignal);expect(signal.aborted).toBe(false);
  calls.push({selection:structuredClone(selection),signal});
  if(selection.kind==='manifest'){
   expect(selection).toEqual({kind:'manifest'});const raw=pair.raw.slice();
   if(corrupt){corrupt=false;raw[0]=0xff;changedHash=hash(raw);expect(raw.byteLength).toBe(pair.raw.byteLength);expect(changedHash).not.toBe(pair.expected.rootSha256);}
   return raw;
  }
  expect(selection).toEqual({kind:'frame',index:selection.index});expect(selection.index===0||selection.index===1).toBe(true);
  return pair.rows[selection.index]!.raw.slice();
 };
 const request=new Request(read,pair.expected);
 try{
  expect(await request.select(0)).toEqual(expected(0));expect(request.current()).toEqual(expected(0));
  corrupt=true;const pending=request.select(1);expect(request.current()).toBeNull();
  await expect(pending).rejects.toThrow();expect(request.current()).toBeNull();
  expect(corrupt).toBe(false);expect(changedHash).toMatch(/^[a-f0-9]{64}$/);expect(changedHash).not.toBe(pair.expected.rootSha256);
  expect(calls.map(call=>call.selection)).toEqual([{kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'}]);
  expect(await request.select(1)).toEqual(expected(1));expect(request.current()).toEqual(expected(1));
  expect(calls.map(call=>call.selection)).toEqual([
   {kind:'manifest'},{kind:'frame',index:0},{kind:'manifest'},{kind:'manifest'},{kind:'frame',index:1},
  ]);
  expect(calls[0]!.signal).toBe(calls[1]!.signal);expect(calls[3]!.signal).toBe(calls[4]!.signal);
  expect(new Set(calls.filter(call=>call.selection.kind==='manifest').map(call=>call.signal)).size).toBe(3);
  expect(hash(pair.raw)).toBe(pair.expected.rootSha256);expect(pair.expected.codeSha256).toEqual(pair.root.code_sha256);
  expect(pair.rows.map(row=>hash(row.raw))).toEqual([
   '99456f234912c2b5230f806d0e59f5e39b3ccba2031797a877935e5f8aaf64b1',
   '49e491d9c36cf9872c4129112c20e28c04a15b929995f0b80f8c8b1508819c73',
  ]);
 }finally{request.cancel();}
});
