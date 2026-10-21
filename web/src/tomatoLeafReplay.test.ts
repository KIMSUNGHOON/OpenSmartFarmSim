import { describe,it,expect } from 'vitest';
import { decodeCropReplay } from './cropReplay';
import { cropReferenceResponse,cropReferenceSelection } from '../e2e/crop-fixture';
import { tomatoLeafBinding,TOMATO_LEAF_MAPPING } from './tomatoLeafReplay';

describe('saved tomato leaf area display mapping',()=>{
  const data=()=>decodeCropReplay(cropReferenceResponse(),cropReferenceSelection);
  it('keeps the exact stored identity, UTC, LAI and result payload version',()=>{
    const replay=data(),binding=tomatoLeafBinding(replay,2)!;
    expect(binding).toMatchObject({mapping:TOMATO_LEAF_MAPPING,result_id:replay.result_id,at:replay.samples[2]!.at,
      lai:replay.samples[2]!.lai.value,payload_sha256:replay.manifest.payload_sha256,
      scope:'synthetic_crop_math_only',gates:'not_assessed'});
  });
  it('uses one unchanged reference across the whole stored result without amplifying small changes',()=>{
    const replay=data(),reference=Math.max(...replay.samples.map(s=>s.lai.value));
    for(let i=0;i<replay.samples.length;i++){
      const b=tomatoLeafBinding(replay,i)!;
      expect(b.reference_lai).toBe(reference);expect(b.area_ratio).toBe(replay.samples[i]!.lai.value/reference);
    }
    expect(tomatoLeafBinding(replay,0)!.area_ratio).toBeGreaterThan(.95);
  });
  it('handles zero leaf area without inferring plant emergence, height or reproductive state',()=>{
    const replay=data(),zero={...replay,samples:replay.samples.map(s=>({...s,lai:{...s.lai,value:0}}))};
    const b=tomatoLeafBinding(zero,0)!;expect(b.area_ratio).toBe(0);expect(b.reference_lai).toBe(0);
    for(const key of ['height','fruit_count','fruit_color','ripeness','yield'])expect(b).not.toHaveProperty(key);
  });
  it('rejects non-saved indices, failed result and nonfinite or negative leaf area',()=>{
    const replay=data();for(const i of [-1,.5,replay.samples.length,NaN])expect(tomatoLeafBinding(replay,i)).toBeNull();
    expect(tomatoLeafBinding({...replay,status:'hold'},0)).toBeNull();
    for(const value of [-1,NaN,Infinity]){
      const samples=replay.samples.map((s,i)=>i===0?{...s,lai:{...s.lai,value}}:s);
      expect(tomatoLeafBinding({...replay,samples},1)).toBeNull();
    }
  });
});
