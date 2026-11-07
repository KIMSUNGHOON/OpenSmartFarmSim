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
