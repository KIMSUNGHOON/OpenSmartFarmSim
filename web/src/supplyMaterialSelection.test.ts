import {expect,it} from 'vitest';
import {SUPPLY_MATERIAL_SELECTION_KEY,readSupplyMaterialSelection,serializeSupplyMaterialSelection,supplyMaterialSelectionURL} from './supplyMaterialSelection';
import {SUPPLY_SELECTION_KEY,serializeSupplySelection} from './supplyMorphologySelection';
it('keeps this root and its four frame selections separate from the old dataset',()=>{
 expect(SUPPLY_MATERIAL_SELECTION_KEY).not.toBe(SUPPLY_SELECTION_KEY);
 for(let index=0;index<4;index++){
  const s={index,view:'all' as const,panel:'data' as const},saved=serializeSupplyMaterialSelection(s);
  expect(readSupplyMaterialSelection('',saved)).toEqual(s);
  expect(readSupplyMaterialSelection(supplyMaterialSelectionURL('http://localhost/supply-material-replay.html',s).search,null)).toEqual(s);
 }
 const old=serializeSupplySelection({index:3,view:'all',panel:'data'});
 expect(readSupplyMaterialSelection('',old)).toEqual({index:0,view:'connected',panel:'scene'});
});
it.each(['4','37','-1','1.5','true','1e0'])('rejects a frame selector outside the material namespace: %s',value=>{
 expect(readSupplyMaterialSelection('?frame='+value,null).index).toBe(0);
});
it('lets explicit URL selection override saved selection and rejects invalid serialization',()=>{
 const saved=serializeSupplyMaterialSelection({index:3,view:'unbound',panel:'data'});
 expect(readSupplyMaterialSelection('?frame=1&view=all&panel=scene',saved)).toEqual({index:1,view:'all',panel:'scene'});
 expect(()=>serializeSupplyMaterialSelection({index:4,view:'all',panel:'data'})).toThrow();
});
