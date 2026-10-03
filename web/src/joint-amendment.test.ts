import {it,expect} from 'vitest';
import {amendJoint,numericSlots} from './joint-amendment';
import type {Baseline,JointRecord,NumericInput} from './economic-api';
const at='2026-09-28T00:00:00.000001Z';
const input:NumericInput={value:'55.0000000001',unit:'KRW',input_id:'생산/지급',revision:'new',origin:'user',evidence_level:'assumed',
  assumption_scope:'자가 작성 시험',source_ref:'test',available_at:at,scope_start:'2026-10-01',scope_end:'2026-10-31'};
const meta={revision:'r1',payload_sha256:'a'.repeat(64),recorded_at:at,admission_kind:'contract_valid_user_assumption'} as const;
const baseline:Baseline={...meta,kind:'economic_scenario',record_id:'base',decision_at:at,period_start:'2026-10-01',period_end:'2026-10-31',
  market_context:{kind:'unavailable',hold_report_id:'11111111-1111-4111-8111-111111111111'}};
const rights={use:'allowed',display:'allowed',redistribute:'allowed'} as const;
const {scope_start:_,scope_end:__,...number}=input;
const record:JointRecord={...meta,kind:'joint_shock',record_id:'shock',decision_at:at,baseline_sha256:meta.payload_sha256,
  input:{schema_version:'1',shock_id:'shock',revision:'r1',baseline_sha256:meta.payload_sha256,decision_at:at,
    effective_start:input.scope_start,effective_end:input.scope_end,available_at:'2026-09-28T00:00:00Z',origin:'user',evidence_level:'assumed',rights,
    drivers:['demand','supply','macro'].map((kind,index)=>({kind:kind as 'demand'|'supply'|'macro',record_id:kind,revision:'r1',
      origin:'user',evidence_level:'assumed',available_at:'2026-09-28T00:00:00Z',effective_start:input.scope_start,effective_end:input.scope_end,
      rights,hypothesis:'Self-authored test',source_ref:'test',causal_status:'unvalidated_user_hypothesis',changes:[{
        event_group:'variable_costs',event_id:'production',field:'payment',number:{...number,input_id:index===2 ? input.input_id : kind,revision:'r2',value:'60'},time:null,reference:null}]})),
    contract_caps:[],settlement_bindings:[{binding_id:'binding',revision:'r2',sha256:'b'.repeat(64)}]}};

it('pins only the explicitly selected numeric edit and its rights with precise Unicode hashing',async ()=>{
  const original=structuredClone(record);const slots=numericSlots(record,input);expect(slots).toHaveLength(1);
  const pinned=await amendJoint(record,baseline,input,slots[0]!.key,true);
  expect(record).toEqual(original);
  expect(pinned.rights.input.raw_sha256).toBe('8bc430cf3c4de64e4264e38332a3c960a20e9920e5393b3433e91fdb98bde60d');
  expect(pinned.rights.input.available_at).toBe(at);
  expect(pinned.rights.input.rights.redistribute).toBe('denied');
  expect(pinned.shock.input.available_at).toBe(at);
  expect(pinned.shock.input.drivers[2]!.available_at).toBe(at);
  expect(pinned.shock.input.drivers[2]!.changes[0]!.number).toEqual(number);
  expect(pinned.shock.input.drivers.slice(0,2)).toEqual(original.input.drivers.slice(0,2));
  expect(pinned.shock.input.settlement_bindings).toEqual(original.input.settlement_bindings);
  expect(pinned.shock.input.revision).not.toBe('r1');
  expect(pinned.shock.input.drivers[2]!.revision).not.toBe('r1');
  expect(pinned.shock.input.drivers[2]!.rights.redistribute).toBe('denied');
});
it.each([
  {available_at:'2026-09-28T00:00:00.000002Z'},
  {scope_start:'2026-10-02'}, {scope_end:'2026-10-30'}, {input_id:'different'}, {unit:'kg'}, {revision:'r2'},
])('rejects a mismatched or future numeric assumption %j',async change=>{
  await expect(amendJoint(record,baseline,{...input,...change} as NumericInput,'[2,0]',true)).rejects.toMatchObject({code:'amendment_mismatch'});
});
it('requires explicit slot and ownership/use/display declaration',async ()=>{
  await expect(amendJoint(record,baseline,input,'',true)).rejects.toMatchObject({code:'amendment_mismatch'});
  await expect(amendJoint(record,baseline,input,'[2,0]',false)).rejects.toMatchObject({code:'rights_required'});
});
