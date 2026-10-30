import type {SupplyTerminalFrame,SupplyTerminalReplay} from './supplyTerminalReplay';
import {formatTerminalQuantity,terminalPlotRatio} from './supplyTerminalPresentation';
import {compare,fraction} from './supplyMorphologyGraphValues';
import type {ExactQuantity} from './supplyMorphologyQuantityCore';
import './SupplyTerminalPanel.css';
const fields=['carbohydrate_stock_exact','number_stock_exact'] as const;
const labels=['과실 탄수화물 저장량','과실 수 상당 저장량'],units=['mg CH₂O / m² 재배면적','과실 수 상당량 / m² 재배면적'];
type Window=ReturnType<SupplyTerminalReplay['window']>;
export default function SupplyTerminalPanel({frame,history,window,select,first}:{frame:SupplyTerminalFrame;history:SupplyTerminalFrame[];
 window:Window;select:(index:number)=>void;first:(index:number)=>void}){
 const index=frame.reference.index;
 function plot(field:typeof fields[number],i:number){
  let maximum=history[0]![field];for(const q of history)if(compare(fraction(q[field],maximum.unit),fraction(maximum,maximum.unit))>0)maximum=q[field];
  const x=(n:number)=>30+n/Math.max(1,history.length-1)*330,y=(q:ExactQuantity)=>124-terminalPlotRatio(q,maximum)*91;
  return <section id={i===0?'viewport-2-a-storage':'viewport-2-a-fruit'} key={field} className="terminal-chart">
   <h3>{labels[i]} <small>{units[i]}</small></h3>
   <p className="terminal-stock" data-terminal-field={field} data-exact={JSON.stringify(frame[field])}>{formatTerminalQuantity(frame[field])}</p>
   <svg viewBox="0 0 390 164" role="img" aria-label={labels[i]+' 저장 순서 그래프'} data-terminal-series={field}>
    <line x1="30" y1="124" x2="360" y2="124" stroke="#c5cebc"/><text x="8" y="128">0</text><text x="30" y="20">{formatTerminalQuantity(maximum)}</text>
    <polyline fill="none" stroke="#638545" strokeWidth="2" points={history.map(q=>`${x(q.reference.index)},${y(q[field])}`).join(' ')}/>
    {history.map(q=><circle key={q.reference.index} role="button" tabIndex={0} aria-label={`${labels[i]} 저장 시점 ${q.reference.index+1} 선택`}
     aria-pressed={q.reference.index===index} data-index={q.reference.index} data-exact={JSON.stringify(q[field])} data-phase={q.phase}
     cx={x(q.reference.index)} cy={y(q[field])} r={q.reference.index===index?5:2.4} fill={q.reference.index===index?'#254e35':'#89a775'}
     onClick={()=>select(q.reference.index)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();select(q.reference.index);}}}>
     <title>{q.reference.index+1} · {formatTerminalQuantity(q[field])} · {units[i]}</title></circle>)}
    <text x="30" y="153">첫 저장 시점</text><text x="280" y="153">마지막 시점</text>
   </svg><p className="supply-note">점은 원 저장값입니다. 가로축은 저장 순서이며 시간 비례 축은 아닙니다.</p>
  </section>;
 }
 return <section className="terminal-panel" aria-label="같은 시점의 모형 과실 수량" data-terminal-index={index}
  data-terminal-at={JSON.stringify(frame.at)} data-terminal-phase={frame.phase}>
  <header><p className="supply-eyebrow">같은 저장 상태 · 과실 구획 원장</p><h2>모형 과실 저장량과 구간 유출</h2>
   <p className="supply-note">3D와 같은 시점의 탄수화물·과실 수 상당량입니다. N은 질소가 아닙니다. 개별 실제 과실·생과kg·수확량으로 환산하지 않았습니다.</p></header>
  <div className="terminal-charts">{fields.map(plot)}</div>
  <section id="viewport-3-b-analysis" className="terminal-window" aria-label="선택 구간의 모형 유출">
   <div><h3>집계 구간 · 양끝 포함</h3><label>집계 시작 시점 <select aria-label="집계 시작 시점" value={window.window.first_frame} onChange={e=>first(Number(e.target.value))}>
    {Array.from({length:index+1},(_,i)=><option key={i} value={i}>{i+1} / {history.length}</option>)}</select></label>
    <p className="supply-note">끝: 현재3D 선택 시점 {index+1} · {window.intervals.length}개 인접 구간<br/>같은 시각의 출현 전·후를 보존하며, 한 시점만 선택하면 유출 합은0입니다.</p></div>
   <dl>{(['terminal_carbohydrate_exact','terminal_number_exact']as const).map((key,i)=><div key={key}>
    <dt>{i===0?'구간 탄수화물 유출 합':'구간 과실 수 상당 유출 합'}</dt><dd data-window-terminal={key} data-exact={JSON.stringify(window.totals[key])}>{formatTerminalQuantity(window.totals[key])}</dd><small>{units[i]}</small></div>)}</dl>
  </section>
  <section id="viewport-3-b-sources" className="terminal-cohorts"><h3>현재 시점의 과실 발달50구획</h3>
   <div className="supply-table-scroll"><table><caption>각 구획의 원 좌표 · 구획 번호는 개별 실제 과실 ID가 아닙니다.</caption>
    <thead><tr><th scope="col">발달 구획</th><th scope="col">탄수화물 · mg CH₂O/m²</th><th scope="col">과실 수 상당량/m²</th></tr></thead>
    <tbody>{frame.fruit_carbohydrate.values.map((c,i)=><tr key={i} data-cohort-index={i}><th scope="row">{i}</th>
     <td data-raw-cohort-carbon={String(c)}>{String(c)}</td><td data-raw-cohort-number={String(frame.fruit_number.values[i])}>{String(frame.fruit_number.values[i])}</td></tr>)}</tbody>
   </table></div><p className="supply-note">합계의 소수 표시는 반올림입니다. 원 좌표·정확 분수·시점 지문은 보존합니다. 현재 합성 QA이며 G0–G4 미평가·R2 미승인입니다.</p>
  </section>
  <details className="supply-evidence terminal-exact"><summary>과실 수량·집계 구간의 정확 원본 증거</summary>
   <pre data-terminal-evidence>{JSON.stringify({reference:frame.reference,state_sha256:frame.state_sha256,at:frame.at,phase:frame.phase,
    carbohydrate_stock_exact:frame.carbohydrate_stock_exact,number_stock_exact:frame.number_stock_exact,
    terminal_carbohydrate_exact:frame.terminal_carbohydrate_exact,terminal_number_exact:frame.terminal_number_exact,
    window:window.window,totals:window.totals,intervals:window.intervals},null,2)}</pre>
  </details>
 </section>;
}
