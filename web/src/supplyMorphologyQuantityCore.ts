import {closed,need,object} from './storedLeafReplayIO';
import {add,binary64,compare,fraction,mul,sub,type Fraction} from './supplyMorphologyGraphValues';
export type Quantity={value:number;unit:string};
export type ExactQuantity={numerator:string;denominator:string;unit:string};
export const MASS='mg_CH2O/m2_floor';
export const exactRecord=(x:Fraction,unit:string):ExactQuantity=>({numerator:x.n.toString(),denominator:x.d.toString(),unit});

export function numberQuantity(value:unknown,unit:string,nonnegative=false):number{
 const q=closed(value,['value','unit']);need(q.unit===unit&&typeof q.value==='number'&&Number.isFinite(q.value));
 if(nonnegative)need(q.value>=0);return q.value;
}
export function exactClock(origin:unknown,at:unknown,air:unknown):ExactQuantity{
 const b=object(origin),base=binary64(numberQuantity(b.base_temperature,'degC'));
 const duration=sub(fraction(at,'s'),fraction(b.at_elapsed_seconds_exact,'s'));need(duration.n>=0n);
 const integral=sub(fraction(air,'degC_s'),fraction(b.air_temperature_integral_exact,'degC_s'));
 const age=add(fraction(b.thermal_age_exact,'degC_day'),mul(sub(integral,mul(base,duration)),{n:1n,d:86400n}));
 need(age.n>=0n);return exactRecord(age,'degC_day');
}
export function geometryProof(value:unknown,unit:string){
 const q=closed(value,['potential_exact','realized_exact','deficit_exact','lifetime_potential_exact','lifetime_realized_exact',
  'lifetime_deficit_exact','canonical_gap_exact','canonical_potential_difference_exact']);
 for(const v of Object.values(q))fraction(v,unit);
 for(const prefix of ['','lifetime_']){
  const p=fraction(q[prefix+'potential_exact'],unit),r=fraction(q[prefix+'realized_exact'],unit),d=fraction(q[prefix+'deficit_exact'],unit);
  need(r.n>=0n&&compare(p,r)>=0&&compare(sub(p,r),d)===0);
 }
 return q;
}
export function ledgerProof(value:unknown,units:Readonly<Record<string,string>>){
 const q=closed(value,Object.keys(units));
 for(const [name,unit]of Object.entries(units)){
  const row=closed(q[name],['residual_exact','budget_exact']),r=fraction(row.residual_exact,unit),b=fraction(row.budget_exact,unit);
  need(b.n>=0n&&compare({n:r.n<0n?-r.n:r.n,d:r.d},b)<=0);
 }
 return q;
}
