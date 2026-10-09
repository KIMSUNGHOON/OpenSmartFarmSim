import { useEffect,useRef,useState } from 'react';
import { init,use,type EChartsType } from 'echarts/core';
import { LineChart } from 'echarts/charts';
import { GridComponent,TooltipComponent,MarkLineComponent } from 'echarts/components';
import { SVGRenderer } from 'echarts/renderers';
import type { ThermalPoint } from './thermal-api';
import { metrics,displayNumber,type Metric } from './replay-format';
use([LineChart,GridComponent,TooltipComponent,MarkLineComponent,SVGRenderer]);

export default function ReplayChart({points,point}:{points:ThermalPoint[];point:ThermalPoint}) {
  const target=useRef<HTMLDivElement>(null),chart=useRef<EChartsType|null>(null);
  const [metric,setMetric]=useState<Metric>(metrics[0]);
  const [failed,setFailed]=useState(false);
  useEffect(()=>{
    const element=target.current;if(!element)return;
    try {chart.current=init(element,null,{renderer:'svg'});}
    catch {setFailed(true);return;}
    let resizeFrame:number|null=null;
    const observer=new ResizeObserver(()=>{if(resizeFrame!==null)return;
      resizeFrame=requestAnimationFrame(()=>{resizeFrame=null;chart.current?.resize();});});observer.observe(element);
    return ()=>{observer.disconnect();if(resizeFrame!==null)cancelAnimationFrame(resizeFrame);
      chart.current?.dispose();chart.current=null;};
  },[]);
  useEffect(()=>{
    try {chart.current?.setOption({animation:false,textStyle:{fontFamily:'Noto Sans KR Variable, sans-serif'},
      grid:{left:68,right:28,top:34,bottom:64},
      tooltip:{trigger:'axis',renderMode:'richText',axisPointer:{type:'line'}},
      xAxis:{type:'category',name:'UTC',nameLocation:'middle',nameGap:45,boundaryGap:false,
        data:points.map(row=>row.at_utc),axisLabel:{formatter:(at:string)=>at.slice(11,16)}},
      yAxis:{type:'value',name:metric.unit,scale:true,axisLabel:{formatter:(value:number)=>String(Number(value.toPrecision(4)))}},
      series:[{type:'line',name:metric.label,data:points.map(row=>displayNumber(row,metric)),showSymbol:false,
        smooth:false,lineStyle:{color:'#327836',width:2},itemStyle:{color:'#327836'},
        markLine:{symbol:['none','none'],silent:true,lineStyle:{color:'#956021',type:'dashed',width:2},
          label:{show:true,formatter:'선택 시각',position:'insideEndTop'},data:[{xAxis:point.at_utc}]}}]},true);
    }catch {setFailed(true);}
  },[points,point,metric]);
  return <section className="panel replay-chart" data-selected-at={point.at_utc} data-selected-value={displayNumber(point,metric)}>
    <div className="picker-heading"><h2>저장된 시계열</h2><label>그래프 항목<select value={metric.key}
      onChange={event=>setMetric(metrics.find(item=>item.key===event.target.value) ?? metrics[0])}>
      {metrics.map(item=><option key={item.key} value={item.key}>{item.label} ({item.unit})</option>)}</select></label></div>
    <div ref={target} className="replay-plot" aria-hidden="true"/>
    {failed && <p role="status">그래프를 사용할 수 없습니다. 아래 표에서 같은 값을 확인하세요.</p>}
    <p className="muted">점선은 선택 시각입니다. 선은 저장된 시점들을 연결하며 중간 상태를 계산하지 않습니다.</p>
  </section>;
}
