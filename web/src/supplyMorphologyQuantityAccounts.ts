import {closed,need,object} from './storedLeafReplayIO';
import {equal,fluxUnits} from './leafFundedBirthReplaySchema';
import {add,binary64,compare,exactAt,fraction,mul,sub,type Row} from './supplyMorphologyGraphValues';
import {MASS,exactRecord,ledgerProof,numberQuantity} from './supplyMorphologyQuantityCore';
import type {QuantityLayout} from './supplyMorphologyQuantityLayout';

export function accountUnits({n,m,h}:QuantityLayout){
 const flow=fluxUnits(n),ledger:Record<string,string>={carbohydrate:MASS,number:'fruits_equivalent/m2_floor',canopy_sensible:'J/m2_floor',
  air_sensible:'J/m2_floor',vapor:'kg_water/m2_floor',area_capacity:'J/m2_floor/K',reduced_energy:'J/m2_floor',stem_root_carbon:MASS};
 for(let i=0;i<m;i++){
  for(const k of ['inflow','maintenance','removal'])flow[`stem_root_${i}_${k}`]=MASS;
  ledger[`stem_root_carbon_${i}`]=MASS;
 }
 for(const [kind,count,unit]of [['leaf',n,'m2'],['internode',h,'m']] as const){
  for(let i=0;i<count;i++){
   for(const k of ['potential','realized'])flow[`${kind}_${i}_${k}`]=unit;
   for(const k of ['extension','unmapped'])flow[`${kind}_${i}_${k}`]=MASS;
   for(const k of ['construction','partition'])ledger[`${kind}_${i}_${k}`]=MASS;
   ledger[`${kind}_${i}_geometry`]=unit;
   ledger[kind==='leaf'?`leaf_age_${i}`:`internode_${i}_age`]='degC_day';
   if(kind==='leaf')ledger[`leaf_carbon_${i}`]=MASS;
  }
 }
 return {flow,ledger};
}
export function exactBlock(value:unknown,units:Readonly<Record<string,string>>){
 const q=closed(value,Object.keys(units));for(const [name,unit]of Object.entries(units))fraction(q[name],unit);return q;
}
const POINT={buffer_debit:MASS,capacity_in:'J/m2_floor/K',growth_respiration:MASS,leaf_structural_carbon:MASS,
 sensible_in:'J/m2_floor',stem_structural_carbon:MASS,structural_carbon:MASS};
export function checkpointQuantities(layout:QuantityLayout,value:unknown,shootBase:unknown){
 const {seed}=layout,cp=object(value),{flow,ledger}=accountUnits(layout);
 const seedLifetime=exactBlock(seed.lifetime_transfers_exact,flow),lifetime=exactBlock(cp.lifetime_transfers_exact,flow);
 const branch=closed(cp.branch_integrated_transfers,Object.keys(flow));
 for(const [name,unit]of Object.entries(flow)){
  const b=binary64(numberQuantity(branch[name],unit));
  need(compare(fraction(lifetime[name],unit),add(fraction(seedLifetime[name],unit),b))===0);
 }
 exactBlock(seed.point_totals_exact,POINT);exactBlock(cp.point_totals_exact,POINT);
 equal(cp.point_totals_exact,seed.point_totals_exact);equal(cp.transfer_origins,seed.transfer_origins);
 ledgerProof(seed.global_ledgers,ledger);ledgerProof(cp.branch_ledgers,ledger);ledgerProof(cp.global_ledgers,ledger);
 const start=exactAt(object(seed.initial_sample).at),end=exactAt(cp.at),duration=sub(end.elapsed,start.elapsed);
 need(start.origin===end.origin&&duration.n>=0n);
 const schedule=object(seed.schedule),air=binary64(numberQuantity(branch.indoor_air_temperature_time,'degC_s'));
 const age=add(fraction(schedule.age_exact,'degC_day'),mul(sub(air,mul(binary64(shootBase),duration)),{n:1n,d:86400n}));
 equal(cp.schedule,{...schedule,age_exact:exactRecord(age,'degC_day')});
 need(compare(age,fraction(schedule.next_threshold_exact,'degC_day'))<0);
 return {lifetime,global:cp.global_ledgers as Row,geometry:object(cp.geometry_diagnostics)};
}
