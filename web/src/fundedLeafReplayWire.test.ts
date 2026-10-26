import {expect,it} from 'vitest';
import {wireFields,wireItems,wireHash} from './fundedLeafReplayWire';

it('preserves binary64 spellings and nested JSON strings in original wire slices',async()=>{
 const raw='{"array":[2.0,-0.0,1e-07,{"text":"a,}\\\"b"}],"null":null}';
 const fields=wireFields(raw),items=wireItems(fields.array!);
 expect(items.slice(0,3)).toEqual(['2.0','-0.0','1e-07']);
 expect(JSON.parse(items[3]!)).toEqual({text:'a,}\"b'});
 expect(fields.null).toBe('null');
 expect(await wireHash('2.0')).not.toBe(await wireHash('2'));
});
it.each(['{"a":1,"a":2}','[1]','{"a":NaN}','{"a":1}junk','{"a":1,}','{"a":1,"\\u0061":2}'])('rejects ambiguous or malformed object %s',raw=>{
 expect(()=>wireFields(raw)).toThrow();
});
it('requires bounded containers and rejects duplicate nested keys',()=>{
 expect(()=>wireItems('{}')).toThrow();expect(()=>wireFields('{"nested":{"x":1,"x":2}}')).toThrow();
 expect(()=>wireFields('{"x":'+ '['.repeat(65)+'0'+']'.repeat(65)+'}')).toThrow();
});
