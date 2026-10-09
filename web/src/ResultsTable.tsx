import type { ThermalPoint } from './thermal-api';
import { metrics,displayValue,kst } from './replay-format';

export default function ResultsTable({points,point,onSelect}:{points:ThermalPoint[];point:ThermalPoint;onSelect:(index:number)=>void}) {
  return <section className="panel replay-table-panel"><h2>시각별 저장 값</h2>
    <p>시각을 선택하면 장면·그래프·현재 시각 요약도 함께 이동합니다.</p>
    <div className="replay-table-scroll" tabIndex={0} role="region" aria-label="시각별 계산 표">
      <table className="replay-table"><caption>합성 계산 · 1분 간격 · 모든 값은 서버 기록에서 조회</caption>
        <thead><tr><th scope="col">시각 (UTC)</th>{metrics.map(metric=><th scope="col" key={metric.key}>{metric.label}<br/>{metric.unit}</th>)}</tr></thead>
        <tbody>{points.map((row,index)=><tr key={row.at_utc} aria-selected={row===point} data-at-utc={row.at_utc}>
          <th scope="row"><button className="table-time" aria-current={row===point ? 'true' : undefined}
            onClick={()=>onSelect(index)} title={kst(row.at_utc)}>{row.at_utc.replace('T',' ').replace('Z','')}<span className="sr-only"> 선택</span></button></th>
          {metrics.map(metric=><td key={metric.key} data-metric={metric.key} data-raw-value={row[metric.key]}>{displayValue(row,metric)}</td>)}
        </tr>)}</tbody>
      </table>
    </div><p className="muted">열수요·공급열은 모델의 열량입니다. 구매 전력·연료나 요금으로 환산하지 않습니다. 습기비는 마른 공기 1kg당 수증기 kg입니다.</p>
  </section>;
}
