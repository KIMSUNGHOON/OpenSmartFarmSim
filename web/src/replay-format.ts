import type { ThermalPoint } from './thermal-api';

export const metrics=[
  {key:'temperature_k',label:'실내 온도',unit:'°C'},
  {key:'relative_humidity_fraction',label:'상대습도',unit:'%'},
  {key:'humidity_ratio_kg_v_per_kg_da',label:'습기비',unit:'kg_v/kg_da'},
  {key:'heat_demand_w_th',label:'모델 열수요',unit:'W_th'},
  {key:'heat_delivered_w_th',label:'모델 공급열',unit:'W_th'},
  {key:'delivered_heat_energy_kwh_th',label:'1분 구간 공급열',unit:'kWh_th'},
] as const;
export type Metric=typeof metrics[number];
export function displayNumber(point:ThermalPoint,metric:Metric):number {
  const value=point[metric.key];
  return metric.key==='temperature_k' ? value-273.15 : metric.key==='relative_humidity_fraction' ? value*100 : value;
}
export function displayValue(point:ThermalPoint,metric:Metric):string {
  return new Intl.NumberFormat('ko-KR',{maximumSignificantDigits:6}).format(displayNumber(point,metric));
}
export function temperatureColor(point:ThermalPoint,range:readonly [number,number]):string {
  const fraction=range[1]===range[0] ? 0.5 : Math.min(1,Math.max(0,(point.temperature_k-range[0])/(range[1]-range[0])));
  return `hsl(${210-180*fraction}, 48%, 68%)`;
}
export function kst(at:string):string {
  return new Intl.DateTimeFormat('ko-KR',{timeZone:'Asia/Seoul',dateStyle:'short',timeStyle:'medium'}).format(new Date(at))+' KST';
}
