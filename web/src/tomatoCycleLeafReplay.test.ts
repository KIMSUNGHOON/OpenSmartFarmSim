import { describe,it,expect } from 'vitest';
import { cycleReference } from '../e2e/cycle-crop-fixture';
import { cycleTomatoLeafBinding,type TomatoLeafAnchor } from './tomatoLeafReplay';

describe('paged cycle leaf display with a fixed stored endpoint reference',()=>{
  const data=cycleReference(),last=data.samples.at(-1)!;
  const anchor:TomatoLeafAnchor={result_id:data.summary.result_id,payload_sha256:data.summary.reference.payload_sha256,
    sample_index:data.summary.reference.sample_count-1,at:last.at,lai:last.lai.value};
  it('uses the same stored endpoint on different pages without fetching or interpolating a whole crop',()=>{
    for(const i of [0,1,data.samples.length-1]){
      const sample=data.samples[i]!,binding=cycleTomatoLeafBinding(data.summary,sample,i,anchor)!;
      expect(binding).toMatchObject({at:sample.at,lai:sample.lai.value,result_id:data.summary.result_id,
        reference_lai:last.lai.value,reference_at:last.at,reference_kind:'last_stored_sample'});
      expect(binding.area_ratio).toBe(sample.lai.value/last.lai.value);
    }
  });
  it('rejects a reference from another result, payload or nonterminal index',()=>{
    for(const wrong of [{...anchor,result_id:'wrong'},{...anchor,payload_sha256:'0'.repeat(64)},
      {...anchor,sample_index:0}])expect(cycleTomatoLeafBinding(data.summary,data.samples[0]!,0,wrong)).toBeNull();
  });
  it('withholds a zero, nonfinite or insufficient display reference without clipping the stored value',()=>{
    for(const lai of [0,NaN,Infinity,anchor.lai/100])
      expect(cycleTomatoLeafBinding(data.summary,data.samples[0]!,0,{...anchor,lai})).toBeNull();
  });
  it('rejects a mismatched terminal UTC or terminal quantity',()=>{
    expect(cycleTomatoLeafBinding(data.summary,last,anchor.sample_index,{...anchor,at:data.samples[0]!.at})).toBeNull();
    expect(cycleTomatoLeafBinding(data.summary,last,anchor.sample_index,{...anchor,lai:anchor.lai*2})).toBeNull();
  });
});
