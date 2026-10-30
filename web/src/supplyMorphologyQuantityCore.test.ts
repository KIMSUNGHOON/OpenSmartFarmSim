import {expect,it} from 'vitest';
import {exactClock,geometryProof,ledgerProof,numberQuantity} from './supplyMorphologyQuantityCore';
const q=(n:string,d='1',unit='s')=>({numerator:n,denominator:d,unit});
const baseline={at_elapsed_seconds_exact:q('0'),air_temperature_integral_exact:q('0','1','degC_s'),thermal_age_exact:q('10','1','degC_day'),base_temperature:{value:5,unit:'degC'}};
it('composes original exact age without converting it to a rounded day',()=>{
 expect(exactClock(baseline,q('1'),q('20','1','degC_s'))).toEqual(q('57601','5760','degC_day'));
});
it('retains an exact binary64 fractional base and negative air integral without clipping',()=>{
 const b={...baseline,base_temperature:{value:.125,unit:'degC'}};
 expect(exactClock(b,q('1'),q('-1','1','degC_s'))).toEqual(q('767999','76800','degC_day'));
});
it.each(['before_birth','negative_age','wrong_base_unit','wrong_air_unit'])('rejects invalid clock input %s',kind=>{
 const b=structuredClone(baseline);let at=q('1'),air=q('20','1','degC_s');
 if(kind==='before_birth')b.at_elapsed_seconds_exact=q('2');
 if(kind==='negative_age'){b.thermal_age_exact=q('0','1','degC_day');air=q('-1000000','1','degC_s');}
 if(kind==='wrong_base_unit')b.base_temperature.unit='K';
 if(kind==='wrong_air_unit')air=q('20','1','s');
 expect(()=>exactClock(b,at,air)).toThrow();
});
const geometry=()=>Object.fromEntries(['potential_exact','realized_exact','deficit_exact','lifetime_potential_exact','lifetime_realized_exact','lifetime_deficit_exact','canonical_gap_exact','canonical_potential_difference_exact'].map(k=>[k,q(k.includes('potential')?'3':k.includes('realized')?'2':k.includes('deficit')?'1':'-1','1','m2')]));
it('keeps exact realized/deficit identities and signed canonical gaps',()=>expect(()=>geometryProof(geometry(),'m2')).not.toThrow());
it.each(['deficit_exact','lifetime_deficit_exact','realized_exact','canonical_gap_exact'])('rejects wrong geometry quantity %s',field=>{
 const g=geometry();g[field]=field==='canonical_gap_exact'?q('1','1','m'):q('5','1','m2');expect(()=>geometryProof(g,'m2')).toThrow();
});
it('checks exact recorded budgets without requiring a zero residual',()=>{
 expect(()=>ledgerProof({carbon:{residual_exact:q('-1','10','mg'),budget_exact:q('1','10','mg')}},{carbon:'mg'})).not.toThrow();
 expect(()=>ledgerProof({carbon:{residual_exact:q('1','5','mg'),budget_exact:q('1','10','mg')}},{carbon:'mg'})).toThrow();
});
it.each([NaN,Infinity,-1,true,'1'])('rejects a nonnegative coordinate %j',v=>expect(()=>numberQuantity({value:v,unit:'m'},'m',true)).toThrow());
