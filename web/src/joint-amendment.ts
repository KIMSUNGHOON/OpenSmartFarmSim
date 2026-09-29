import {ApiError} from './api-validation';
import type {Baseline,EconomicNumber,JointRecord,NumericInput,RightsIntent,JointIntent} from './economic-api';

function utcOrder(value:string) {
  const text=value.replace(/\+00:00$/,'Z');
  return text.slice(0,19)+'.'+(text.split('.')[1]?.slice(0,-1) ?? '').padEnd(6,'0');
}
function later(a:string,b:string) {return utcOrder(a)>=utcOrder(b) ? a : b;}
function covers(start:string,end:string,baseline:Baseline) {return start<=baseline.period_start && end>=baseline.period_end;}
export function numericSlots(record:JointRecord,input:NumericInput) {
  return record.input.drivers.flatMap((driver,d)=>driver.changes.flatMap((edit,e)=>
    edit.number?.input_id===input.input_id && edit.number.unit===input.unit && edit.number.revision!==input.revision
      ? [{key:JSON.stringify([d,e]),driver,edit}] : []));
}
export async function amendJoint(record:JointRecord,baseline:Baseline,input:NumericInput,slot:string,ownedRights:boolean):Promise<{rights:RightsIntent;shock:JointIntent}> {
  if(!ownedRights)throw new ApiError('rights_required');
  const selected=numericSlots(record,input).find(item=>item.key===slot);
  if(!selected || record.baseline_sha256!==baseline.payload_sha256 || record.decision_at!==baseline.decision_at
    || utcOrder(input.available_at)>utcOrder(baseline.decision_at) || !covers(input.scope_start,input.scope_end,baseline)
    || !covers(record.input.effective_start,record.input.effective_end,baseline)
    || !covers(selected.driver.effective_start,selected.driver.effective_end,baseline)
    || utcOrder(record.input.available_at)>utcOrder(baseline.decision_at)
    || utcOrder(selected.driver.available_at)>utcOrder(baseline.decision_at)
    || record.input.drivers.length!==3 || new Set(record.input.drivers.map(driver=>driver.kind)).size!==3
    || record.input.drivers.some(driver=>driver.changes.length===0))throw new ApiError('amendment_mismatch');
  const number:EconomicNumber={value:input.value,unit:input.unit,input_id:input.input_id,revision:input.revision,
    origin:input.origin,evidence_level:input.evidence_level,assumption_scope:input.assumption_scope,
    source_ref:input.source_ref,available_at:input.available_at};
  const canonical=JSON.stringify(Object.fromEntries(Object.keys(number).sort().map(key=>[key,number[key as keyof EconomicNumber]])));
  const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(canonical));
  const raw_sha256=Array.from(new Uint8Array(digest),byte=>byte.toString(16).padStart(2,'0')).join('');
  const rights={use:'allowed',display:'allowed',redistribute:'denied'} as const;
  const shock=structuredClone(record.input);shock.revision='web-'+crypto.randomUUID();shock.rights=rights;
  shock.available_at=later(shock.available_at,input.available_at);
  const [d,e]=JSON.parse(selected.key) as [number,number];
  const driver=shock.drivers[d]!;driver.revision='web-'+crypto.randomUUID();driver.rights=rights;
  driver.available_at=later(driver.available_at,input.available_at);driver.changes[e]!.number=number;
  return {rights:{kind:'input_rights',input:{input_id:input.input_id,revision:input.revision,raw_sha256,
    origin:'user',evidence_level:'assumed',rights,available_at:input.available_at,
    effective_start:input.scope_start,effective_end:input.scope_end,immutable:true},idempotency_key:'web-input-rights-v1:'+crypto.randomUUID()},
    shock:{kind:'joint_shock',input:shock,idempotency_key:'web-joint-amendment-v1:'+crypto.randomUUID()}};
}
