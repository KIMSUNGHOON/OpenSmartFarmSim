import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {readSupplyMaterialFiles} from './supplyMaterialGraph';
import {SUPPLY_MATERIAL_FIXTURE as MODEL} from './supplyMaterialFixture';
import {MATERIAL_QUANTITY_FIXTURE as F} from './supplyMaterialQuantityFixture';
import {canonicalQuantityWire,validateMaterialQuantityWire} from './supplyMaterialQuantityWire';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';
import {document} from './supplyMorphologyGraphValues';
import {sha256} from './morphologyReplay';
const enc=(s:string)=>new TextEncoder().encode(s),signal=()=>new AbortController().signal;
const model=(name:string)=>new Uint8Array(readFileSync(new URL(`../public/supply-material-replay/own-public-v1/${name}`,import.meta.url)));
const fixture=new TextDecoder().decode(readFileSync(new URL('../public/supply-material-quantities/own-public-v1/quantities.json',import.meta.url)));
const graph=await readSupplyMaterialFiles(async name=>model(name),MODEL.anchor,signal());
const frames=Array.from({length:4},(_,i)=>document(document(new TextDecoder().decode(model(`frame-${i}.json`))).fields.frame!));
function put(raw:string,path:string[],token:string):string{
 if(!path.length)return token;const key=path[0]!,tail=path.slice(1);
 if(raw[0]==='['){const a=wireItems(raw);a[Number(key)]=put(a[Number(key)]!,tail,token);return '['+a.join(',')+']';}
 const f=wireFields(raw);f[key]=put(f[key]??'null',tail,token);return '{'+Object.keys(f).sort().map(k=>JSON.stringify(k)+':'+f[k]).join(',')+'}';
}
async function rehash(raw:string){
 const result=canonicalQuantityWire(wireFields(raw).result!),hash=await wireHash(result),size=enc(result).byteLength;
 raw=put(raw,['result_sha256'],JSON.stringify(hash));raw=put(raw,['canonical_result_bytes'],String(size));raw=put(raw,['provenance','raw_sha256'],JSON.stringify(hash));
 return {raw:enc(raw),anchor:{fixture_sha256:await wireHash(raw),fixture_bytes:enc(raw).byteLength,result_sha256:hash,result_bytes:size}};
}
it('canonicalizes original floats without Number reserialization',async()=>{
 const d=document(fixture),raw=canonicalQuantityWire(d.fields.result!);expect(enc(raw).byteLength).toBe(F.result_bytes);expect(await wireHash(raw)).toBe(F.result_sha256);
 expect(canonicalQuantityWire('{ "b": [1.0, -0.0, 1e-06], "a": true }')).toBe('{"a":true,"b":[1.0,-0.0,1e-06]}');
});
it.each([
 [['extra'],true],[['G0_G4'],'approved'],[['R2'],'approved'],[['effective_rights','display'],false],
 [['notice','sha256'],'0'.repeat(64)],[['provenance','observed_at'],'2026-10-01T07:00:00Z'],
 [['result','projection_code_sha256'],'0'.repeat(64)],[['result','source','artifact_sha256'],'0'.repeat(64)],
 [['result','source','code_sha256','backend/app/crop_supply_material_owner.py'],'0'.repeat(64)],
 [['result','source','effective_rights','redistribute'],false],[['result','window','first_frame'],true],
 [['result','frames','0','reference','state_sha256'],'0'.repeat(64)],
 [['result','frames','0','reference','source_cursor_sha256'],'0'.repeat(64)],
 [['result','frames','0','phase'],'material_after'],[['result','frames','1','reference','event_sequence'],true],
 [['result','frames','0','fruit_carbohydrate','values','0'],99.25],
 [['result','frames','0','fruit_number','unit'],'fruits'],
 [['result','frames','0','carbohydrate_stock_exact','numerator'],'999'],
 [['result','frames','0','cumulative_exact','external_vapor','unit'],'kg'],
 [['result','frames','0','cumulative_exact','external_vapor','numerator'],'1'],
 [['result','intervals','0','kind'],'stored_model_interval'],
 [['result','totals_exact','external_vapor','numerator'],'1']
 ]as Array<[string[],unknown]>)('rejects semantically invalid data even after every quantity hash is rebuilt: %j',async(path,value)=>{
 const q=await rehash(put(fixture,path,JSON.stringify(value)));await expect(validateMaterialQuantityWire(q.raw,graph,frames,signal(),q.anchor)).rejects.toThrow();
});
it.each([
 [['result','window','first_frame']],[['result','frames','0','reference','index']],
 [['result','intervals','0','from_frame','index']]
 ])('rejects an integer-looking float token at %j',async path=>{
 const q=await rehash(put(fixture,path,'0.0'));expect(await validateMaterialQuantityWire(q.raw,graph,frames,signal(),q.anchor).then(()=>false,()=>true)).toBe(true);
});
it('does not accept a float token for the declared canonical byte count',async()=>{
 const q=await rehash(fixture);q.raw=enc(put(new TextDecoder().decode(q.raw),['canonical_result_bytes'],String(q.anchor.result_bytes)+'.0'));
 q.anchor.fixture_sha256=await wireHash(new TextDecoder().decode(q.raw));q.anchor.fixture_bytes=q.raw.byteLength;
 expect(await validateMaterialQuantityWire(q.raw,graph,frames,signal(),q.anchor).then(()=>false,()=>true)).toBe(true);
});
it('checks cancellation before consuming the fixture or returning validated data',async()=>{
 const c=new AbortController();c.abort();await expect(validateMaterialQuantityWire(enc(fixture),graph,frames,c.signal)).rejects.toThrow();
});
it.each(['oversize','utf8','duplicate','depth','nonfinite'])('refuses malformed quantity input %s',async kind=>{
 const raw=kind==='oversize'?new Uint8Array(2*1024**2+1):kind==='utf8'?new Uint8Array([255]):
  kind==='duplicate'?enc('{"scope":"software_research_only",'+fixture.slice(1)):
  kind==='depth'?enc('{"x":'+'['.repeat(66)+'0'+']'.repeat(66)+'}'):enc('{"x":1e999}');
 const anchor={fixture_bytes:raw.byteLength,fixture_sha256:await sha256(raw),result_bytes:F.result_bytes,result_sha256:F.result_sha256};
 await expect(validateMaterialQuantityWire(raw,graph,frames,signal(),anchor)).rejects.toThrow();
});
