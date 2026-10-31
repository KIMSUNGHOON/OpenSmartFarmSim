import {need} from './storedLeafReplayIO';
import {add,binary64,compare,mul,sub,type Fraction} from './supplyMorphologyGraphValues';

function bitsOf(value:number){const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,value,false);return view.getBigUint64(0,false);}
function floatOf(bits:bigint){const view=new DataView(new ArrayBuffer(8));view.setBigUint64(0,bits,false);return view.getFloat64(0,false);}
function neighbor(value:number,direction:1|-1):Fraction{
 if(value===0)return binary64(direction*Number.MIN_VALUE);
 const bits=bitsOf(value),offset=BigInt(value>0?direction:-direction),next=floatOf(bits+offset);
 if(Number.isFinite(next))return binary64(next);
 const opposite=floatOf(bits-offset);
 return add(binary64(value),sub(binary64(value),binary64(opposite)));
}

/** Validate one-round nearest-even storage; no crop rate or time step is evaluated. */
export function storedRounding(exact:Fraction,value:number){
 need(typeof value==='number'&&Number.isFinite(value));
 if(exact.n===0n){need(Object.is(value,0));return;}
 need(value!==0);
 const current=binary64(value),half={n:1n,d:2n};
 const lower=mul(add(neighbor(value,-1),current),half),upper=mul(add(current,neighbor(value,1)),half);
 const lo=compare(exact,lower),hi=compare(exact,upper),even=(bitsOf(value)&1n)===0n;
 need((lo>0||lo===0&&even)&&(hi<0||hi===0&&even));
}

export function storedCombine(before:readonly number[],rows:readonly (readonly number[])[],weights:readonly Fraction[],dt:Fraction,after:readonly number[]){
 need(rows.length===weights.length&&before.length===after.length&&before.length>0&&before.length<=32768);
 need(rows.every(r=>r.length===before.length));
 for(let i=0;i<before.length;i++){
  let rate:Fraction={n:0n,d:1n};
  for(let j=0;j<rows.length;j++)rate=add(rate,mul(weights[j]!,binary64(rows[j]![i])));
  const delta=mul(dt,rate);storedRounding(add(binary64(before[i]),delta),after[i]!);
  need(delta.n===0n||after[i]!==before[i]);
 }
}
