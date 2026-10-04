import { useEffect,useRef,useState } from 'react';
import { init,use,type EChartsType } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent,TooltipComponent,MarkLineComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import { METRICS,metricValue,metricUnit,metricLabel,STORE_COLORS,type CropMetric,type CropSample } from './cropReplay';
use([LineChart,GridComponent,TooltipComponent,MarkLineComponent,SVGRenderer]);

export default function CropChart({samples,sample}:{samples:readonly CropSample[];sample:CropSample}){
  const target=useRef<HTMLDivElement>(null),chart=useRef<EChartsType|null>(null);
  const [metric,setMetric]=useState<CropMetric>('lai'),[failed,setFailed]=useState(false);
  useEffect(()=>{
    const element=target.current;if(!element)return;
    try{chart.current=init(element,null,{renderer:'svg'});}catch{setFailed(true);return;}
    let pending:number|null=null;
    const observer=new ResizeObserver(()=>{if(pending!==null)return;
      pending=requestAnimationFrame(()=>{pending=null;chart.current?.resize();});});observer.observe(element);
    return()=>{observer.disconnect();if(pending!==null)cancelAnimationFrame(pending);chart.current?.dispose();chart.current=null;};
  },[]);
  useEffect(()=>{
    const color=metric==='lai'?'#367744':STORE_COLORS[metric];
    try{chart.current?.setOption({animation:false,textStyle:{fontFamily:'Noto Sans KR Variable, sans-serif'},
      grid:{left:76,right:30,top:42,bottom:58},tooltip:{trigger:'axis',renderMode:'richText',axisPointer:{type:'line'}},
      xAxis:{type:'category',name:'UTC',nameLocation:'middle',nameGap:40,boundaryGap:false,
        data:samples.map(row=>row.at),axisLabel:{formatter:(at:string)=>at.slice(11,19)}},
      yAxis:{type:'value',name:metricUnit(metric),scale:true,axisLabel:{formatter:(n:number)=>String(Number(n.toPrecision(4)))}},
      series:[{type:'line',name:metricLabel(metric),data:samples.map(row=>metricValue(row,metric)),
        showSymbol:samples.length<=200,symbolSize:6,smooth:false,lineStyle:{color,width:2},itemStyle:{color},
        markLine:{symbol:['none','none'],silent:true,lineStyle:{color:'#aa8732',type:'dashed',width:2},
          label:{show:true,formatter:'선택 시점',position:'insideEndTop'},data:[{xAxis:sample.at}]}}]},true);
    }catch{setFailed(true);}
  },[samples,sample,metric]);
  return <section className="panel crop-chart" id="viewport-1-winner-history" data-selected-at={sample.at}
    data-selected-value={metricValue(sample,metric)}>
    <div className="crop-heading"><h2>시간에 따른 계산값</h2><label>성장 그래프 항목<select value={metric}
      onChange={e=>setMetric(e.target.value as CropMetric)}>{METRICS.map(key=><option key={key} value={key}>
        {metricLabel(key)} ({metricUnit(key)})</option>)}</select></label></div>
    <div ref={target} className="crop-plot" aria-hidden="true"/>
    {failed && <p role="status">그래프를 사용할 수 없습니다. 같은 값은 아래 표에서 확인하세요.</p>}
    <p className="crop-caption">점선은 선택 시점입니다. 선은 저장된 값의 연결이며 중간 시점의 계산이 아닙니다.</p>
  </section>;
}
