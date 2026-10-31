import {expect,it} from 'vitest';
import {formatMaterialQuantity} from './supplyMaterialQuantityPresentation';
const q=(n:string,d='1',unit='kg_water/m2_floor')=>({numerator:n,denominator:d,unit});
it.each([
 ['0','1','0'],['1','8','0.125'],['-1','8','−0.125'],['1','200000000','0.00000001'],['-1','200000000','−0.00000001'],
 ['1','1'+'0'.repeat(400),'<0.00000001'],['-1','1'+'0'.repeat(400),'−(<0.00000001)']
 ])('preserves the exact sign and bounded rounding of %s/%s',(n,d,text)=>expect(formatMaterialQuantity(q(n!,d!))).toBe(text));
it('also formats original carbohydrate and model counts without turning them into money',()=>{
 expect(formatMaterialQuantity(q('13','2','mg_CH2O/m2_floor'))).toBe('6.5');
 expect(formatMaterialQuantity(q('13','2','fruits_equivalent/m2_floor'))).toBe('6.5');
 expect(()=>formatMaterialQuantity(q('1','1','KRW'))).toThrow();
 expect(()=>formatMaterialQuantity(q('1','0'))).toThrow();
});
