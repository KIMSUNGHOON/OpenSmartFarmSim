import {expect,it} from 'vitest';
import {readSupplyTerminalSelection,serializeSupplyTerminalSelection,supplyTerminalSelectionURL,selectSupplyTerminalFrame} from './supplyTerminalSelection';
import {formatTerminalQuantity,terminalPlotRatio} from './supplyTerminalPresentation';
import {SUPPLY_MORPHOLOGY_FIXTURE as F} from './supplyMorphologyReplayFixture';
const MASS='mg_CH2O/m2_floor',NUMBER='fruits_equivalent/m2_floor';
const q=(n:string,d='1',unit=MASS)=>({numerator:n,denominator:d,unit});
it('starts with the same frame/window endpoint and preserves the own source-specific selection',()=>{
 expect(readSupplyTerminalSelection('',null)).toEqual({index:0,first:0,view:'connected',panel:'scene'});
 const state={index:9,first:3,view:'unbound' as const,panel:'data' as const},raw=serializeSupplyTerminalSelection(state);
 expect(readSupplyTerminalSelection('',raw)).toEqual(state);
 expect(JSON.parse(raw).artifact_sha256).toBe(F.anchor.artifact_sha256);
 const url=supplyTerminalSelectionURL('http://localhost:5182/supply-production-replay.html',state);
 expect(readSupplyTerminalSelection(url.search,null)).toEqual(state);
});
it('clamps the start when a current frame moves earlier and keeps menu/view selections',()=>{
 const state={index:9,first:3,view:'all' as const,panel:'data' as const};
 expect(selectSupplyTerminalFrame(state,2)).toEqual({...state,index:2,first:2});
 expect(selectSupplyTerminalFrame(state,37)).toEqual({...state,index:37});
 const raw=serializeSupplyTerminalSelection(state);
 expect(readSupplyTerminalSelection('?frame=2',raw)).toEqual({...state,index:2,first:2});
 expect(readSupplyTerminalSelection('?frame=9&from=7&panel=scene',raw)).toEqual({...state,first:7,panel:'scene'});
});
it.each(['-1','99','1.5','true','00','NaN','0&from=1'])('rejects malformed from=%s with a valid current frame',raw=>{
 expect(readSupplyTerminalSelection('?frame=9&from='+raw,null).first).toBe(0);
});
it('refuses invalid serialization and frame transitions without mutating the caller',()=>{
 const state={index:9,first:3,view:'connected' as const,panel:'scene' as const};
 for(const first of [-1,10,NaN,0.5])expect(()=>serializeSupplyTerminalSelection({...state,first})).toThrow();
 for(const index of [-1,38,NaN,0.5])expect(()=>selectSupplyTerminalFrame(state,index)).toThrow();
 expect(state).toEqual({index:9,first:3,view:'connected',panel:'scene'});
});
it('does not adopt a preference from another artifact or an oversized/malformed input',()=>{
 const state={index:9,first:3,view:'connected' as const,panel:'data' as const};
 const raw=serializeSupplyTerminalSelection(state),changed=JSON.parse(raw);changed.artifact_sha256='0'.repeat(64);
 expect(readSupplyTerminalSelection('',JSON.stringify(changed))).toEqual({index:0,first:0,view:'connected',panel:'scene'});
 for(const broken of ['null','[]','{', 'x'.repeat(1025)])expect(readSupplyTerminalSelection('',broken).first).toBe(0);
 expect(readSupplyTerminalSelection('?'+ 'x'.repeat(4096),raw)).toEqual(state);
});
it('rounds presentation only and distinguishes tiny nonzero quantities from zero',()=>{
 expect(formatTerminalQuantity(q('0'))).toBe('0');expect(formatTerminalQuantity(q('1','3'))).toBe('0.333333');
 expect(formatTerminalQuantity(q('2','3',NUMBER))).toBe('0.666667');
 expect(formatTerminalQuantity(q('1','10000000'))).toBe('<0.000001');
 expect(formatTerminalQuantity(q('1','2000000'))).toBe('0.000001');
 const original=q('123456789','100');expect(formatTerminalQuantity(original)).toBe('1234567.89');
 expect(original).toEqual(q('123456789','100'));
});
it('normalizes chart positions with integer ratios when direct Number division would overflow',()=>{
 const power=2n**2048n,n=power+1n;
 const value=q(String(n),String(power)),maximum=q(String(n),String(power/2n));
 expect(Number(value.numerator)/Number(value.denominator)).toBeNaN();
 expect(terminalPlotRatio(value,maximum)).toBe(0.5);
 expect(terminalPlotRatio(q('0'),q('0'))).toBe(0);
 expect(terminalPlotRatio(q('2'),q('2'))).toBe(1);
});
it('refuses invalid quantities and chart bounds',()=>{
 for(const bad of [q('-1'),q('1','0'),q('1','1','kg'),q('2','2')])expect(()=>formatTerminalQuantity(bad)).toThrow();
 for(const pair of [[q('1'),q('0')],[q('2'),q('1')],[q('1'),q('1','1',NUMBER)]])
  expect(()=>terminalPlotRatio(pair[0]!,pair[1]!)).toThrow();
});
