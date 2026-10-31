import {need} from './storedLeafReplayIO';
import {fraction} from './supplyMorphologyGraphValues';
import type {ExactQuantity} from './supplyMorphologyQuantityCore';
import {MATERIAL_COUNTER_UNITS} from './supplyMaterialQuantityValues';
/** Eight-place display only; retain the original exact quantity in the UI data. */
export function formatMaterialQuantity(q:ExactQuantity){
 need(Object.values(MATERIAL_COUNTER_UNITS).some(unit=>unit===q.unit));const v=fraction(q,q.unit),negative=v.n<0n,n=negative?-v.n:v.n;
 const scale=100000000n,rounded=(2n*n*scale+v.d)/(2n*v.d);
 if(rounded===0n)return n===0n?'0':negative?'−(<0.00000001)':'<0.00000001';
 const whole=rounded/scale,part=(rounded%scale).toString().padStart(8,'0').replace(/0+$/,'');
 return (negative?'−':'')+whole.toString()+(part?'.'+part:'');
}
