import { describe,it,expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { decodeJointCropClimateResponse,validJointCropClimateLookup,type JointCropClimateSample } from './jointCropClimateReplay';
import { need,object } from './api-validation';
import { jointSceneSample,jointSceneScales } from './jointCropClimateGeometry';
import { coupledCohortHeights,temperaturePosition } from './coupledCropGeometry';
const fixture=JSON.parse(readFileSync(new URL('../e2e/joint-crop-climate-recorded-responses.json',import.meta.url),'utf8'));
function samples():JointCropClimateSample[]{
  const raw:unknown=fixture.completed[1];need(object(raw)&&object(raw.farm));
  const {scenario_id,scenario_revision,registration_sha256,crop_id}=raw.farm;
  const lookup={result_id:raw.result_id,scenario_id,scenario_revision,registration_sha256,crop_id};need(validJointCropClimateLookup(lookup));
  const p=decodeJointCropClimateResponse(raw,lookup);need(p.page?.kind==='samples');return [...p.page.records];
}
describe('joint original quantities in the shared numerical scene',()=>{
  it('passes original microsecond UTC and original LAI/cohort/temperature objects without legacy state fields',()=>{
    for(const row of samples()){
      const point=jointSceneSample(row);expect(point.at).toBe(row.time.at);expect(point.lai).toBe(row.value.derived.leaf_area_index);
      expect(point.state).toBe(row.value.cohort_state);expect(Object.keys(point.state)).toEqual(['fruit_carbohydrate','fruit_number']);
      expect(point.temperatures!.canopy).toBe(row.value.derived.canopy_temperature);expect(point.temperatures!.air).toBe(row.value.climate_state.air_temperature);
    }
  });
  it('represents every original cohort on one page scale with finite separate C/N heights',()=>{
    const rows=samples(),before=JSON.stringify(rows),scales=jointSceneScales(rows);
    for(const row of rows){const heights=coupledCohortHeights(row.value.cohort_state,scales);
      for(const kind of ['carbon','number'] as const){expect(heights[kind]).toHaveLength(50);expect(heights[kind].every(v=>Number.isFinite(v)&&v>=0&&v<=1)).toBe(true);}}
    expect(JSON.stringify(rows)).toBe(before);
    expect(scales.temperatures!.minimum).toBe(Math.min(...rows.flatMap(row=>[row.value.derived.canopy_temperature.value,row.value.climate_state.air_temperature.value])));
    expect(scales.temperatures!.maximum).toBe(Math.max(...rows.flatMap(row=>[row.value.derived.canopy_temperature.value,row.value.climate_state.air_temperature.value])));
  });
  it('does not invent a temperature axis or state for an empty output page',()=>{
    expect(jointSceneScales([])).toEqual({carbon:0,number:0,logarithmic:{carbon:null,number:null}});
  });
  it.each([{minimum:-20,maximum:40},{minimum:-1e308,maximum:1e308},{minimum:23,maximum:24}])('keeps endpoints and midpoint on the declared visual temperature axis %j',range=>{
    expect(temperaturePosition(range.minimum,range)).toBe(0);expect(temperaturePosition(range.maximum,range)).toBe(1);
    expect(temperaturePosition(range.minimum/2+range.maximum/2,range)).toBeCloseTo(.5,12);
  });
  it('places a constant temperature at the labelled midpoint, including zero and negative values',()=>{
    for(const value of [0,-12,26])expect(temperaturePosition(value,{minimum:value,maximum:value})).toBe(.5);
  });
  it.each([NaN,Infinity,-Infinity,41,-21])('refuses invalid/outside-axis marker %s without clipping a physical value',value=>{
    expect(()=>temperaturePosition(value,{minimum:-20,maximum:40})).toThrow('crop_scene_unavailable');
  });
});
