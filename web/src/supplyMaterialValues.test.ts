import {expect,it} from 'vitest';
import {storedRounding,storedCombine} from './supplyMaterialValues';
import {add,binary64,mul} from './supplyMorphologyGraphValues';

it.each([0,1,-1,0.1,-0.1,Number.MIN_VALUE,-Number.MIN_VALUE,Number.MAX_VALUE,-Number.MAX_VALUE])('accepts exact finite stored number %s',value=>{
 expect(()=>storedRounding(binary64(value),value)).not.toThrow();
});
it('checks exact nearest-even ties on both sides of one',()=>{
 const one=binary64(1),half={n:1n,d:2n},next=binary64(1+Number.EPSILON),tie=mul(add(one,next),half);
 expect(()=>storedRounding(tie,1)).not.toThrow();expect(()=>storedRounding(tie,1+Number.EPSILON)).toThrow();
 const next2=binary64(1+2*Number.EPSILON),tie2=mul(add(next,next2),half);
 expect(()=>storedRounding(tie2,1+Number.EPSILON)).toThrow();expect(()=>storedRounding(tie2,1+2*Number.EPSILON)).not.toThrow();
});
it.each([NaN,Infinity,-Infinity])('rejects nonfinite actual value %s',value=>{
 expect(()=>storedRounding(binary64(1),value)).toThrow();
});
it('does not convert large rationals through overflowing Number division',()=>{
 expect(()=>storedRounding({n:1n<<2000n,d:1n<<2000n},1)).not.toThrow();
 expect(()=>storedRounding({n:3n<<2000n,d:1n<<2000n},1)).toThrow();
});
it('rejects loss of a nonzero value/change and a signed zero substitution',()=>{
 expect(()=>storedRounding({n:1n,d:1n<<2000n},0)).toThrow();
 expect(()=>storedRounding({n:0n,d:1n},-0)).toThrow();
 expect(()=>storedCombine([1],[[Number.MIN_VALUE]],[{n:1n,d:1n}],{n:1n,d:1n},[1])).toThrow();
});
it('verifies the full stored weighted sum and refuses changed endpoints',()=>{
 const rates=[[1,2],[3,4],[5,6],[7,8]],weights=[{n:1n,d:6n},{n:1n,d:3n},{n:1n,d:3n},{n:1n,d:6n}];
 expect(()=>storedCombine([0,1],rates,weights,{n:1n,d:2n},[2,3.5])).not.toThrow();
 expect(()=>storedCombine([0,1],rates,weights,{n:1n,d:2n},[3,3.5])).toThrow();
});
