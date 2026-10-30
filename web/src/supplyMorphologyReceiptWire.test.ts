import {expect,it} from 'vitest';
import {readFileSync} from 'node:fs';
import {expandSupplyMorphologyReceipt} from './supplyMorphologyReceiptWire';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';

const text=(name:string)=>readFileSync(new URL(`../public/supply-morphology-replay/own-public-v1/${name}`,import.meta.url),'utf8');
const oracle=JSON.parse(readFileSync(new URL('../../research/fixtures/supply-morphology-receipt-wire-20261030.json',import.meta.url),'utf8')) as {
 rows:Array<{context_path:string;parent_context_path:string;receipt_sha256:string;expanded_bytes:number;calculation_sha256:string;
 candidate_calculation_sha256:string;source_checkpoint_sha256:string;before_state_sha256:string;after_state_sha256:string;after_program_sha256:string}>;
};
const originalPins=wireFields(wireFields(text('root.json')).code_sha256!);
for(const name of ['reader','projection','producer'])delete originalPins[`backend/app/crop_supply_morphology_artifact_${name}.py`];
const pins='{'+Object.keys(originalPins).sort().map(k=>JSON.stringify(k)+':'+originalPins[k]).join(',')+'}';
const without=(raw:string,key:string)=>{const q=wireFields(raw);delete q[key];return '{'+Object.keys(q).sort().map(k=>JSON.stringify(k)+':'+q[k]).join(',')+'}';};

it.each(oracle.rows)('restores the actual Python receipt bytes in $context_path',async row=>{
 const parent=wireFields(wireFields(text(row.parent_context_path)).descriptor!).seed!;
 const packed=wireItems(wireFields(text(row.context_path)).receipts!).at(-1)!;
 const raw=await expandSupplyMorphologyReceipt(parent,packed,pins),f=wireFields(raw);
 expect(new TextEncoder().encode(raw)).toHaveLength(row.expanded_bytes);
 expect(await wireHash(raw)).toBe(row.receipt_sha256);
 expect(await wireHash(without(raw,'calculation_sha256'))).toBe(row.calculation_sha256);
 expect(await wireHash(without(f.before_candidate!,'calculation_sha256'))).toBe(row.candidate_calculation_sha256);
 expect(JSON.parse(f.checkpoint_sha256!)).toBe(row.source_checkpoint_sha256);
 expect(await wireHash(wireFields(wireFields(f.before_candidate!).dense_candidate!).state!)).toBe(row.before_state_sha256);
 expect(await wireHash(f.after_state!)).toBe(row.after_state_sha256);
 expect(await wireHash(f.after_program!)).toBe(row.after_program_sha256);
});

const ownPins='{"model.py":"'+'1'.repeat(64)+'"}';
async function pack(body:string,expected:string){return '{"body":'+body+',"receipt_sha256":'+JSON.stringify(await wireHash(expected))+
 ',"source_code_set_sha256":'+JSON.stringify(await wireHash(ownPins))+',"version":"supply-morphology-parent-referenced-receipt-v1"}';}

it('keeps original Python float, signed zero and exponent tokens through a reference',async()=>{
 const expected='{"exponent":1e-07,"float":2.0,"negativeZero":-0.0}';
 const result=await expandSupplyMorphologyReceipt('{"nested":'+expected+'}',await pack('[2,0,["nested"]]',expected),ownPins);
 expect(result).toBe(expected);expect(JSON.stringify(JSON.parse(result))).not.toBe(result);
});
it('restores objects, arrays and scalar tokens in Python codepoint key order',async()=>{
 const body='[0,{"2":[1,[1.0,true,null]],"10":"value","\uE000":-0.0,"\u{10000}":2.0}]';
 const expected='{"10":"value","2":[1.0,true,null],"\uE000":-0.0,"\u{10000}":2.0}';
 expect(await expandSupplyMorphologyReceipt('{}',await pack(body,expected),ownPins)).toBe(expected);
});
it('resolves own array and code-set references without inherited properties',async()=>{
 const body='[0,{"array":[2,0,["rows",0]],"pin":[2,1,["model.py"]]}]';
 const expected='{"array":3.0,"pin":"'+'1'.repeat(64)+'"}';
 expect(await expandSupplyMorphologyReceipt('{"rows":[3.0]}',await pack(body,expected),ownPins)).toBe(expected);
});

const invalid=[
 '[2,true,[]]','[2,2,[]]','[2,"0",[]]','[2,0.0,[]]','[2.0,0,[]]',
 '[2,0,["missing"]]','[2,0,["__proto__"]]','[2,0,["rows",-1]]','[2,0,["rows",true]]',
 '[2,0,["rows",0.0]]','[2,0,["rows",2]]','[2,0,["rows",0,"value"]]',
 '[2,0,"rows"]','[2,0,[],1]','[1,{}]','[0,[]]','[3,[]]','[1,[],0]','[1.0,[]]',
 '{}','[0,{"same":1,"same":2}]','[1,[1e999]]','[0,{"nested":{}}]',
 '[2,0,['+Array(65).fill('"rows"').join(',')+']]'
];
it.each(invalid)('rejects malformed/reference wire %s',async body=>{
 await expect(expandSupplyMorphologyReceipt('{"rows":[3.0]}',await pack(body,'{}'),ownPins)).rejects.toThrow();
});
it.each(['receipt','code','version','extra','duplicate','depth','parent','pins'])('rejects changed closed source proof: %s',async kind=>{
 let packed=await pack('[0,{}]','{}'),parent='{}',code=ownPins;
 if(kind==='receipt')packed=packed.replace(await wireHash('{}'),'0'.repeat(64));
 if(kind==='code')packed=packed.replace(await wireHash(ownPins),'0'.repeat(64));
 if(kind==='version')packed=packed.replace('parent-referenced-receipt-v1','parent-referenced-receipt-v2');
 if(kind==='extra')packed='{"extra":1,'+packed.slice(1);
 if(kind==='duplicate')packed='{"body":[0,{}],'+packed.slice(1);
 if(kind==='depth')packed=await pack('[1,['.repeat(66)+'0'+']]'.repeat(66),'{}');
 if(kind==='parent')parent='{"duplicate":1,"duplicate":2}';
 if(kind==='pins')code='[]';
 await expect(expandSupplyMorphologyReceipt(parent,packed,code)).rejects.toThrow();
});
it.each(['input','utf8','expanded'])('enforces bounded byte use before returning: %s',async kind=>{
 let parent='{}',body='[0,{}]';
 if(kind==='input')parent=' '.repeat(2*1024**2+1);
 if(kind==='utf8')parent='{"value":"'+'한'.repeat(800000)+'"}';
 if(kind==='expanded'){parent='{"value":"'+'a'.repeat(1024**2)+'"}';body='[1,[[2,0,["value"]],[2,0,["value"]]]]';}
 await expect(expandSupplyMorphologyReceipt(parent,await pack(body,'{}'),ownPins)).rejects.toThrow();
});
