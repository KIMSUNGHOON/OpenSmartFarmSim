import {closed,need,object,id} from './storedLeafReplayIO';
import {equal,COHORT,CLIMATE} from './leafFundedBirthReplaySchema';
import {list,type Row} from './supplyMorphologyGraphValues';
import {MASS,numberQuantity} from './supplyMorphologyQuantityCore';

export function quantityLayout(value:unknown){
 const seed=object(value),program=closed(seed.program,['capacity_outflow','capacity_policy','input_id','leaf_stock_policy','leaves',
  'model_floor_area','normalization','origin','scenario','stem_root_compartments','stem_root_stock_policy','thermal_age_policy']);
 id(program.input_id);need(program.origin==='synthetic');
 const policies={capacity_policy:'declared_outflow_plus_area_capacity_derivative_v1',leaf_stock_policy:'leaf-stocks-uniform-maintenance-explicit-removal-v1',
  stem_root_stock_policy:'stem-root-stocks-uniform-maintenance-explicit-removal-v1',normalization:'zero_lower_asymptote_sigmoid_v1',thermal_age_policy:'dynamic_indoor_air_no_clip_v1'};
 for(const [key,p]of Object.entries(policies))need(program[key]===p);
 need(numberQuantity(program.model_floor_area,'m2_floor')>0);numberQuantity(program.capacity_outflow,'J/m2_floor/K/s',true);
 const organs=closed(seed.organs,['leaves','internodes','roots']);
 const leaves=list(program.leaves).map(v=>closed(v,['base_temperature','carbon_removal','curve','initial_area','initial_carbon','leaf_id','sink_weight','thermal_age']));
 const stems=list(program.stem_root_compartments).map(v=>closed(v,['carbon_removal','compartment_id','initial_carbon','kind','sink_weight']));
 const nodes=list(organs.internodes).map(object),leafMeta=list(organs.leaves).map(object);
 const n=leaves.length,m=stems.length,h=nodes.length,size=106+3*n+m;need(n>=1&&m>=1&&h>=1&&leafMeta.length===n);
 const identifiers=(rows:Row[],key:string)=>{const ids=rows.map(r=>{id(r[key]);return r[key] as string;});need(new Set(ids).size===ids.length);return ids;};
 const leafIDs=identifiers(leaves,'leaf_id'),stemIDs=identifiers(stems,'compartment_id'),nodeIDs=identifiers(nodes,'compartment_id');
 equal(identifiers(leafMeta,'leaf_id'),leafIDs);
 for(const node of nodeIDs)need(stemIDs.includes(node));
 for(const row of [...leafMeta,...nodes])need(row.parent_internode_id===null||nodeIDs.includes(String(row.parent_internode_id)));
 const plant={buffer:MASS,temperature_filtered_24h:'degC',temperature_sum:'degC_day'};
 const expected={appended_blocks:['thermal_age','length'],appended_units:{length:'m',thermal_age:'degC_day'},internode_ids:nodeIDs,original_prefix_length:size,
  original:{plant:Object.keys(plant),cohort_arrays:Object.keys(COHORT),climate:Object.keys(CLIMATE),leaf_ids:leafIDs,leaf_blocks:['thermal_age','area','carbon'],
   stem_root_compartments:stems.map(r=>({compartment_id:r.compartment_id,kind:r.kind})),stem_root_blocks:['carbon'],
   units:{plant,cohort_arrays:COHORT,climate:CLIMATE,leaf_blocks:{area:'m2',carbon:MASS,thermal_age:'degC_day'},stem_root_blocks:{carbon:MASS}}}};
 equal(seed.state_layout,expected);
 return {seed,program,organs,leaves,stems,nodes,leafMeta,n,m,h,size};
}
export type QuantityLayout=ReturnType<typeof quantityLayout>;
