import { useState } from 'react';
import { Plot } from './CoupledCropChart';
import type { JointCropClimateSample,JointQuantity } from './jointCropClimateReplay';
import type { CohortScales } from './coupledCropGeometry';

const LABELS:Record<string,string>={leaf_area_index:'잎 면적 지수 (LAI)',canopy_temperature:'수관 온도',air_temperature:'공기 온도',
  air_vapor_mass:'공기 수증기 질량',buffer:'버퍼 탄소',leaf:'잎 탄소',stem_root:'줄기·뿌리 탄소',
  temperature_filtered_24h:'24시간 평활 온도',temperature_sum:'온도 합'};
function metrics(row:JointCropClimateSample):Record<string,JointQuantity>{
  return {...row.value.plant_state,...row.value.climate_state,...row.value.derived,...row.value.integrated_transfers};
}
export default function JointCropClimateChart({samples,sample,scales}:{samples:readonly JointCropClimateSample[];sample:JointCropClimateSample;scales:CohortScales}){
  const [metric,setMetric]=useState('leaf_area_index'),[cohort,setCohort]=useState(0);
  const selected=metrics(sample),quantity=(row:JointCropClimateSample)=>metric==='fruit_carbohydrate'||metric==='fruit_number'
    ?row.value.cohort_state[metric][cohort]!:metrics(row)[metric]!;
  const q=quantity(sample),values=samples.map(row=>quantity(row).value),at=sample.time.at;
  const common={animation:false,textStyle:{fontFamily:'Noto Sans KR Variable, sans-serif'},
    tooltip:{trigger:'axis',renderMode:'richText'},grid:{left:75,right:22,top:42,bottom:38}};
  return <>
    <section className="panel coupled-distribution joint-distribution" data-selected-at={at}><h2>과실 구획 1–50 · 같은 저장 시점</h2>
      <div className="coupled-distribution-grid">{(['fruit_carbohydrate','fruit_number'] as const).map((kind,i)=>{
        const rows=sample.value.cohort_state[kind],raw=rows.map(q=>q.value),unit=rows[0]!.unit,maximum=i?scales.number:scales.carbon;
        return <div key={kind} data-distribution={kind}><h3>{i?'개수 상당량 N':'과실 탄소 C'}</h3>
          <Plot raw={raw} option={{...common,xAxis:{type:'category',data:Array.from({length:50},(_,i)=>String(i+1)),axisLabel:{interval:4}},
            yAxis:{type:'value',name:unit,min:0,...(maximum>0?{max:maximum}:{})},
            series:[{type:'bar',data:raw,itemStyle:{color:i?'#547a96':'#7d943b'}}]}}/>
          <p className="crop-caption">{unit} · 현재 범위의 공통 최대 {String(maximum)}</p></div>;
      })}</div></section>
    <section className="panel coupled-history joint-history" data-selected-at={at} data-selected-value={q.value} data-selected-unit={q.unit}>
      <div className="crop-heading"><h2>시간에 따른 저장 계산값</h2><label>작물·기후 그래프 항목<select aria-label="작물·기후 그래프 항목" value={metric}
        onChange={e=>setMetric(e.target.value)}>{[...Object.keys(selected),'fruit_carbohydrate','fruit_number'].map(key=>
          <option key={key} value={key}>{LABELS[key]??(key==='fruit_carbohydrate'?'구획별 과실 탄소':key==='fruit_number'?'구획별 개수 상당량':key)}</option>)}</select></label>
        {(metric==='fruit_carbohydrate'||metric==='fruit_number')&&<label>그래프 과실 구획<select aria-label="그래프 과실 구획" value={cohort} onChange={e=>setCohort(Number(e.target.value))}>
          {Array.from({length:50},(_,i)=><option key={i} value={i}>{i+1}</option>)}</select></label>}</div>
      <Plot raw={values} option={{...common,xAxis:{type:'category',boundaryGap:false,data:samples.map(row=>row.time.at),axisLabel:{formatter:(at:string)=>at.slice(11)}},
        yAxis:{type:'value',name:q.unit,scale:true},series:[{type:'line',data:values,smooth:false,showSymbol:true,
          itemStyle:{color:'#367744'},markLine:{silent:true,symbol:['none','none'],label:{formatter:'선택 시점'},
            lineStyle:{color:'#aa8732',type:'dashed'},data:[{xAxis:at}]}}]}}/>
      <p className="crop-caption">점선은 선택 UTC입니다. 선은 현재 범위의 원 저장값을 연결하며 중간 상태를 계산하지 않습니다.</p>
    </section>
  </>;
}
