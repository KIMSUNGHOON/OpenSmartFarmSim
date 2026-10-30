import {wireFields} from './fundedLeafReplayWire';
import {closed,need,object,utc,integer} from './storedLeafReplayIO';

export type Row=Record<string,unknown>;
export type WireDocument={raw:string;value:Row;fields:Record<string,string>};
export type Fraction={n:bigint;d:bigint};

function normalize(n:bigint,d:bigint):Fraction{
 need(d>0n);let a=n<0n?-n:n,b=d;
 while(b){const r=a%b;a=b;b=r;}
 return {n:n/a,d:d/a};
}
export function fraction(value:unknown,unit:string):Fraction{
 const q=closed(value,['numerator','denominator','unit']);need(q.unit===unit);
 need(typeof q.numerator==='string'&&q.numerator.length<=4096&&/^-?(?:0|[1-9]\d{0,4095})$/.test(q.numerator));
 need(typeof q.denominator==='string'&&/^[1-9]\d{0,4095}$/.test(q.denominator));
 const v=normalize(BigInt(q.numerator),BigInt(q.denominator));
 need(v.n.toString()===q.numerator&&v.d.toString()===q.denominator);return v;
}
export function binary64(value:unknown):Fraction{
 need(typeof value==='number'&&Number.isFinite(value));
 const view=new DataView(new ArrayBuffer(8));view.setFloat64(0,value,false);
 const bits=view.getBigUint64(0,false),exponent=Number((bits>>52n)&2047n);
 let mantissa=bits&((1n<<52n)-1n);if(exponent)mantissa+=1n<<52n;
 if(bits>>63n)mantissa=-mantissa;
 const power=exponent?exponent-1075:-1074;
 return power<0?normalize(mantissa,1n<<BigInt(-power)):normalize(mantissa<<BigInt(power),1n);
}
export const add=(a:Fraction,b:Fraction)=>normalize(a.n*b.d+b.n*a.d,a.d*b.d);
export const sub=(a:Fraction,b:Fraction)=>normalize(a.n*b.d-b.n*a.d,a.d*b.d);
export const mul=(a:Fraction,b:Fraction)=>normalize(a.n*b.n,a.d*b.d);
export function compare(a:Fraction,b:Fraction){const d=a.n*b.d-b.n*a.d;return d<0n?-1:d>0n?1:0;}
export function exactAt(value:unknown){
 const at=closed(value,['time_origin_utc','elapsed_seconds_exact']);utc(at.time_origin_utc);
 const elapsed=fraction(at.elapsed_seconds_exact,'s');need(elapsed.n>=0n);return {origin:at.time_origin_utc,elapsed};
}
export function list(value:unknown,maximum=512):unknown[]{need(Array.isArray(value)&&value.length<=maximum);return value;}
export function document(raw:string):WireDocument{
 const fields=wireFields(raw);return {raw,fields,value:object(JSON.parse(raw))};
}
export function wireObject(fields:Record<string,string>){
 return '{'+Object.keys(fields).sort().map(key=>JSON.stringify(key)+':'+fields[key]).join(',')+'}';
}
export function without(raw:string,key:string){const fields=wireFields(raw);need(Object.hasOwn(fields,key));delete fields[key];return wireObject(fields);}
export function counter(doc:WireDocument,key:string,minimum=0,maximum=Number.MAX_SAFE_INTEGER){
 const value=doc.value[key];integer(value,minimum,maximum);need(/^(?:0|[1-9]\d*)$/.test(doc.fields[key]!));return value;
}
