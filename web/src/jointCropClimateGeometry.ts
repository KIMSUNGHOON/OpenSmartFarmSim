import { startupCohortScales,type CohortSceneSample,type CohortScales } from './coupledCropGeometry';
import type { JointCropClimateSample } from './jointCropClimateReplay';

export function jointSceneSample(sample:JointCropClimateSample):CohortSceneSample{
  return {at:sample.time.at,state:sample.value.cohort_state,lai:sample.value.derived.leaf_area_index,
    temperatures:{canopy:sample.value.derived.canopy_temperature,air:sample.value.climate_state.air_temperature}};
}
export function jointSceneScales(samples:readonly JointCropClimateSample[]):CohortScales{
  const points=samples.map(jointSceneSample),values=points.flatMap(point=>[point.temperatures!.canopy.value,point.temperatures!.air.value]);
  return {...startupCohortScales(points),...(values.length?{temperatures:{minimum:Math.min(...values),maximum:Math.max(...values)}}:{})};
}
