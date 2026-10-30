import {expect,it} from 'vitest';
import {fraction,binary64,add,sub,mul,compare,wireObject,document} from './supplyMorphologyGraphValues';

const q=(n:string,d='1',unit='s')=>({numerator:n,denominator:d,unit});
it.each([q('0'),q('-1','2'),q('1'+'0'.repeat(4095))])('retains a canonical signed exact quantity %j',v=>{
 const x=fraction(v,'s');expect(x.n.toString()).toBe(v.numerator);expect(x.d.toString()).toBe(v.denominator);
});
it.each([q('-0'),q('01'),q('1','0'),q('2','4'),q('1','-2'),q('1','1','m'),q('1'+'0'.repeat(4096)),q('-1'+'0'.repeat(4095))])('rejects a noncanonical or out of bound exact value %j',v=>{
 expect(()=>fraction(v,'s')).toThrow();
});
it.each([[0,0n,1n],[-0,0n,1n],[.1,3602879701896397n,36028797018963968n],[-.125,-1n,8n],
 [Number.MIN_VALUE,1n,1n<<1074n]])('reads the exact binary64 value %s',(value,n,d)=>{
 expect(binary64(Number(value))).toEqual({n,d});
});
it.each([NaN,Infinity,-Infinity])('rejects nonfinite binary64 %s',v=>expect(()=>binary64(v)).toThrow());
it('compares original fractional seconds without rounding or crop equations',()=>{
 const a=fraction(q('305181','1024'),'s'),b=binary64(8);
 expect(compare(a,b)).toBe(1);expect(add(a,sub(b,a))).toEqual(b);expect(mul(b,fraction(q('64'),'s'))).toEqual({n:512n,d:1n});
});
it('retains raw numeric tokens when constructing a protocol hash object',()=>{
 expect(wireObject({state:'[2.0,-0.0,1e-07]',index:'1'})).toBe('{"index":1,"state":[2.0,-0.0,1e-07]}');
 expect(document('{"original":2.0}').fields.original).toBe('2.0');
 expect(()=>document('{"x":1,"x":2}')).toThrow();
});
