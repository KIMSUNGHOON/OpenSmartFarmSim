import type {SupplyStoredFrame} from './supplyMorphologyReplay';
export type SupplyHistoryPoint={index:number;area:number;length:number;phase:string};
export function SupplyHistory({points,index,select}:{points:SupplyHistoryPoint[];index:number;select:(index:number)=>void}){
 return <>{(['area','length']as const).map(field=>{
  const max=Math.max(...points.map(p=>p[field]),0),range=max||1;
  const x=(i:number)=>28+i/Math.max(1,points.length-1)*344,y=(v:number)=>120-v/range*88;
  return <section key={field} id={`viewport-1-winner-analytics-${field==='area'?'leaf':'stem'}`} className="supply-history">
   <h2>{field==='area'?'저장 잎 면적 합계':'저장 절간 길이 합계'} <small>{field==='area'?'m²':'m'}</small></h2>
   <svg viewBox="0 0 400 156" role="img" aria-label={field==='area'?'원 저장 순서의 잎 면적':'원 저장 순서의 절간 길이'} data-series={field}>
    <line x1="28" y1="120" x2="372" y2="120" stroke="#c5cebc"/><text x="5" y="124">0</text>
    <text x="28" y="17">{max.toPrecision(4)}</text><polyline fill="none" stroke="#769363" strokeWidth="2" points={points.map(p=>`${x(p.index)},${y(p[field])}`).join(' ')}/>
    {points.map(p=><circle key={p.index} role="button" tabIndex={0} aria-label={`저장 시점 ${p.index+1} 선택`} aria-pressed={p.index===index}
     data-index={p.index} data-stored-value={p[field]} data-phase={p.phase} cx={x(p.index)} cy={y(p[field])} r={p.index===index?5:2.4}
     fill={p.index===index?'#254e35':'#89a775'} onClick={()=>select(p.index)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();select(p.index);}}}>
     <title>{p.index+1} · {String(p[field])} {field==='area'?'m²':'m'} · {p.phase}</title></circle>)}
    <text x="28" y="146">첫 저장 시점</text><text x="300" y="146">마지막 시점</text>
   </svg>
   <p>원 저장 순서 · 점은 저장값, 시간 비례 축은 아닙니다.</p>
  </section>;
 })}</>;
}
export function SupplyOrganTable({frame,detailed=false}:{frame:SupplyStoredFrame;detailed?:boolean}){
 return <div className={detailed?'supply-tables supply-tables-detailed':'supply-tables'}>
  <div className="supply-table-scroll"><table><caption>같은 시점의 잎 · 면적은 단면 기준</caption>
   <thead><tr><th scope="col">잎 / 부모 절간</th><th scope="col">면적 m²</th>{detailed&&<><th scope="col">탄수화물</th><th scope="col">정확 열적 나이 °C·day</th><th scope="col">형상 부족분 · 원 정확값</th></>}</tr></thead>
   <tbody>{frame.leaves.map(l=><tr key={l.id} data-leaf-id={l.id} data-parent-id={l.parent_internode_id??''}>
    <th scope="row"><span className="supply-organ-id" title={l.id}>{l.id}</span><small title={l.parent_internode_id??'부착 정보 없음'}>{l.parent_internode_id??'부착 미지정 · 별도 표시'}</small></th>
    <td data-raw-area={l.geometry.value}>{String(l.geometry.value)}</td>{detailed&&<><td data-raw-carbon={l.carbon.value}>{String(l.carbon.value)}</td>
     <td data-clock-exact={JSON.stringify(l.clock_exact)}><code>{l.clock_exact.numerator}/{l.clock_exact.denominator}</code></td>
     <td data-deficit-exact={JSON.stringify(l.geometry_diagnostics.deficit_exact)}><code>{JSON.stringify(l.geometry_diagnostics.deficit_exact)}</code></td></>}</tr>)}</tbody>
  </table></div>
  {detailed&&<div className="supply-table-scroll"><table><caption>같은 시점의 절간 · 원 부모 관계와 길이</caption>
   <thead><tr><th scope="col">절간 / 부모 절간</th><th scope="col">길이 m</th><th scope="col">탄수화물</th><th scope="col">정확 열적 나이 °C·day</th><th scope="col">형상 부족분 · 원 정확값</th></tr></thead>
   <tbody>{frame.internodes.map(n=><tr key={n.id} data-internode-id={n.id} data-parent-id={n.parent_internode_id??''}>
    <th scope="row"><span className="supply-organ-id" title={n.id}>{n.id}</span><small>{n.parent_internode_id??'부모 미지정 · 독립 표시 원점'}</small></th>
    <td data-raw-length={n.geometry.value}>{String(n.geometry.value)}{n.geometry.value===0&&<small>길이 0 · 기관 존재 보존</small>}</td>
    <td data-raw-carbon={n.carbon.value}>{String(n.carbon.value)}</td><td data-clock-exact={JSON.stringify(n.clock_exact)}><code>{n.clock_exact.numerator}/{n.clock_exact.denominator}</code></td>
    <td data-deficit-exact={JSON.stringify(n.geometry_diagnostics.deficit_exact)}><code>{JSON.stringify(n.geometry_diagnostics.deficit_exact)}</code></td>
   </tr>)}</tbody></table></div>}
  {detailed&&<p className="supply-note">탄수화물 단위: mg CH₂O/m² 재배면적. 잎 방향·소엽 형태·굵기·직선 축과 미연결 기관의 위치는 제작 표시 규칙입니다.</p>}
 </div>;
}
