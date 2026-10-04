import { useEffect,useRef,useState } from 'react';
import { init,use,type EChartsType } from 'echarts/core';
import { LineChart,BarChart } from 'echarts/charts';
import { GridComponent,TooltipComponent,MarkLineComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import { CARBON_UNIT,displayNumber } from './cropReplay';
import { FRUIT_NUMBER_UNIT,type CoupledCropSample } from './coupledCropReplay';
import type { CohortScales } from './coupledCropGeometry';
use([LineChart,BarChart,GridComponent,TooltipComponent,MarkLineComponent,SVGRenderer]);
const LABELS={lai:'잎 면적 지수',buffer:'버퍼 탄소',leaf:'잎 탄소',stem_root:'줄기·뿌리 탄소',
  fruit_carbohydrate_total:'총 과실 탄소',temperature_filtered_24h:'평활 온도',temperature_sum:'온도 합',
  fruit_carbohydrate:'구획별 과실 탄소',fruit_number:'구획별 개수 상당량'};
type Metric=keyof typeof LABELS;
function quantity(sample:CoupledCropSample,metric:Metric,cohort:number){
  if(metric==='lai' || metric==='fruit_carbohydrate_total')return sample[metric];
  if(metric==='fruit_number' || metric==='fruit_carbohydrate')return sample.state[metric][cohort]!;
  return sample.state[metric];
}
function Plot({option,raw}:{option:Record<string,unknown>;raw?:readonly number[]}){
  const target=useRef<HTMLDivElement>(null),chart=useRef<EChartsType|null>(null),[failed,setFailed]=useState(false);
  useEffect(()=>{
    const element=target.current;if(!element)return;
    let pending:number|null=null;
    try{chart.current=init(element,null,{renderer:'svg'});}catch{setFailed(true);return;}
    const observer=new ResizeObserver(()=>{if(pending!==null)return;
      pending=requestAnimationFrame(()=>{pending=null;chart.current?.resize();});});observer.observe(element);
    return()=>{observer.disconnect();if(pending!==null)cancelAnimationFrame(pending);chart.current?.dispose();chart.current=null;};
  },[]);
  useEffect(()=>{try{chart.current?.setOption(option,true);}catch{setFailed(true);}},[option]);
  return <><div className="coupled-plot" ref={target} data-values={raw?JSON.stringify(raw):undefined} aria-hidden="true"/>
    {failed && <p role="status">그래프를 사용할 수 없습니다. 같은 값은 표에서 확인하세요.</p>}</>;
}
export default function CoupledCropChart({samples,sample,scales}:{samples:readonly CoupledCropSample[];sample:CoupledCropSample;scales:CohortScales}){
  const [metric,setMetric]=useState<Metric>('lai'),[cohort,setCohort]=useState(0);
  const selected=quantity(sample,metric,cohort),values=samples.map(row=>quantity(row,metric,cohort).value);
  const common={animation:false,textStyle:{fontFamily:'Noto Sans KR Variable, sans-serif'},
    tooltip:{trigger:'axis',renderMode:'richText'},grid:{left:64,right:22,top:42,bottom:38}};
  return <>
    <section className="panel coupled-distribution" data-selected-at={sample.at}><h2>과실 구획 1–50 · 같은 저장 시점</h2>
      <div className="coupled-distribution-grid">{(['carbon','number'] as const).map(kind=>{
        const carbon=kind==='carbon',raw=sample.state[carbon?'fruit_carbohydrate':'fruit_number'].map(q=>q.value);
        const unit=carbon?CARBON_UNIT:FRUIT_NUMBER_UNIT,color=carbon?'#7d943b':'#547a96';
        return <div key={kind} data-distribution={kind}><h3>{carbon?'과실 탄소 C':'개수 상당량 N'}</h3>
          <Plot raw={raw} option={{...common,xAxis:{type:'category',data:Array.from({length:50},(_,i)=>String(i+1)),
            axisLabel:{interval:4}},yAxis:{type:'value',name:unit,min:0,...(scales[kind]>0?{max:scales[kind]}:{})},
            series:[{type:'bar',data:raw,itemStyle:{color},animation:false}]}}/>
          <p className="crop-caption">{unit} · 전체 저장 시점의 공통 최대 {displayNumber(scales[kind])}</p></div>;
      })}</div></section>
    <section className="panel coupled-history" data-selected-at={sample.at} data-selected-value={selected.value} data-selected-unit={selected.unit}>
      <div className="crop-heading"><h2>시간에 따른 저장 계산값</h2><label>연결 연구 그래프 항목<select value={metric}
        onChange={e=>setMetric(e.target.value as Metric)}>{Object.entries(LABELS).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
        {(metric==='fruit_number' || metric==='fruit_carbohydrate') && <label>그래프 과실 구획<select value={cohort} onChange={e=>setCohort(Number(e.target.value))}>
          {Array.from({length:50},(_,i)=><option key={i} value={i}>{i+1}</option>)}</select></label>}</div>
      <Plot raw={values} option={{...common,xAxis:{type:'category',boundaryGap:false,data:samples.map(row=>row.at),
        axisLabel:{formatter:(at:string)=>at.slice(11,19)}},yAxis:{type:'value',name:selected.unit,scale:true},
        series:[{type:'line',name:LABELS[metric],data:values,smooth:false,showSymbol:samples.length<=200,
          itemStyle:{color:'#367744'},markLine:{silent:true,symbol:['none','none'],
            label:{formatter:'선택 시점'},lineStyle:{color:'#aa8732',type:'dashed'},data:[{xAxis:sample.at}]}}]}}/>
      <p className="crop-caption">점선은 선택 UTC입니다. 선은 저장된 값의 연결이며 중간 상태를 계산하지 않습니다.</p>
    </section>
  </>;
}
