import {need} from './storedLeafReplayIO';
import {compare,fraction} from './supplyMorphologyGraphValues';
import {MASS,type ExactQuantity} from './supplyMorphologyQuantityCore';

function value(q:ExactQuantity){
 need(q.unit===MASS||q.unit==='fruits_equivalent/m2_floor');const v=fraction(q,q.unit);need(v.n>=0n);return v;
}
/** Six decimal places for display; exact source quantities remain unchanged. */
export function formatTerminalQuantity(q:ExactQuantity){
 const v=value(q),scale=1000000n,rounded=(2n*v.n*scale+v.d)/(2n*v.d);
 if(rounded===0n)return v.n===0n?'0':'<0.000001';
 const whole=rounded/scale,part=(rounded%scale).toString().padStart(6,'0').replace(/0+$/,'');
 return whole.toString()+(part?'.'+part:'');
}
export function terminalPlotRatio(q:ExactQuantity,maximum:ExactQuantity){
 need(q.unit===maximum.unit);const v=value(q),m=value(maximum);need(compare(v,m)<=0);
 return m.n===0n?0:Number(v.n*m.d*1000000n/(v.d*m.n))/1000000;
}
