import {expect,it} from 'vitest';
import {readSupplySelection,serializeSupplySelection,supplySelectionURL} from './supplyMorphologySelection';
const chosen={index:24,view:'unbound' as const,panel:'data' as const};
it('retains the same original frame and view through menus and fresh-page loading',()=>{
 const saved=serializeSupplySelection(chosen);expect(readSupplySelection('',saved)).toEqual(chosen);
 const url=supplySelectionURL('http://localhost:5181/supply-morphology-replay.html?keep=yes#source',chosen);
 expect(readSupplySelection(url.search,null)).toEqual(chosen);expect(url.searchParams.get('keep')).toBe('yes');expect(url.hash).toBe('#source');
 const next={...chosen,panel:'scene' as const};expect(readSupplySelection('',serializeSupplySelection(next))).toEqual(next);
});
it.each(['?frame=-1','?frame=38','?frame=true','?frame=0.5','?frame=Infinity','?frame=01','?frame=999999'])('rejects invalid original-frame selection %s',search=>expect(readSupplySelection(search,serializeSupplySelection(chosen)).index).toBe(0));
it('prefers valid explicit URL selections and isolates obsolete artifact preferences',()=>{
 const saved=serializeSupplySelection(chosen);
 expect(readSupplySelection('?frame=37&view=all&panel=scene',saved)).toEqual({index:37,view:'all',panel:'scene'});
 expect(readSupplySelection('',saved.replace('"version":1','"version":2'))).toEqual({index:0,view:'connected',panel:'scene'});
 const q=JSON.parse(saved);q.artifact_sha256='0'.repeat(64);expect(readSupplySelection('',JSON.stringify(q)).index).toBe(0);
});
it.each(['bad','null','[]','{"index":24}','x'.repeat(1025)])('does not adopt malformed browser preferences',raw=>expect(readSupplySelection('',raw).index).toBe(0));
it('rejects unsupported view/panel values and invalid writes',()=>{
 expect(readSupplySelection('?view=unknown&panel=unknown',serializeSupplySelection(chosen))).toEqual({...chosen,view:'connected',panel:'scene'});
 expect(()=>serializeSupplySelection({...chosen,index:38})).toThrow();
});
it('writes only its own artifact identity and explicit selection fields',()=>{
 const extra={...chosen,artifact_sha256:'bad',version:2,unrelated:'discard'};
 const raw=serializeSupplySelection(extra),saved=JSON.parse(raw);
 expect(saved.version).toBe(1);expect(saved.artifact_sha256).not.toBe('bad');expect(saved.unrelated).toBeUndefined();
 expect(readSupplySelection('',raw)).toEqual(chosen);
});
