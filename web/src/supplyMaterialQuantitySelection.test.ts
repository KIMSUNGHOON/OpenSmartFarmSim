import {expect,it} from 'vitest';
import {MATERIAL_QUANTITY_SELECTION_KEY,readMaterialQuantitySelection,serializeMaterialQuantitySelection,selectMaterialQuantityFrame,materialQuantitySelectionURL} from './supplyMaterialQuantitySelection';
import {SUPPLY_MATERIAL_SELECTION_KEY} from './supplyMaterialSelection';
it('keeps root/result-specific selection and all valid inclusive windows across menus/reload',()=>{
 expect(MATERIAL_QUANTITY_SELECTION_KEY).not.toBe(SUPPLY_MATERIAL_SELECTION_KEY);
 for(let index=0;index<4;index++)for(let first=0;first<=index;first++){
  const s={index,first,panel:'data' as const,view:'all' as const},raw=serializeMaterialQuantitySelection(s);
  expect(readMaterialQuantitySelection('',raw)).toEqual(s);
  expect(readMaterialQuantitySelection(materialQuantitySelectionURL('http://localhost/supply-material-quantities-replay.html',s).search,null)).toEqual(s);
 }
});
it('clamps the start to the selected frame and rejects wrong datasets/invalid serialization',()=>{
 const s={index:3,first:2,panel:'scene' as const,view:'all' as const};
 expect(selectMaterialQuantityFrame(s,0)).toEqual({...s,index:0,first:0});
 const old=JSON.parse(serializeMaterialQuantitySelection(s));old.result_sha256='0'.repeat(64);
 expect(readMaterialQuantitySelection('',JSON.stringify(old))).toEqual({index:0,first:0,panel:'scene',view:'connected'});
 expect(()=>serializeMaterialQuantitySelection({...s,index:1})).toThrow();
 expect(()=>selectMaterialQuantityFrame(s,4)).toThrow();
});
it.each(['4','-1','1.5','true','1e0','1&from=2'])('refuses invalid start query %s',raw=>{
 expect(readMaterialQuantitySelection('?frame=3&from='+raw,null).first).toBe(0);
});
