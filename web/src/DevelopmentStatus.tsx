import {useEffect, useState} from 'react';
import {developmentStages, parseDevelopmentStatus, type DevelopmentStatus as Status} from './developmentStatus';

const stateNames = {completed:'검증 완료', next:'다음 작업', pending:'대기'};
export default function DevelopmentStatus() {
  const [record, setRecord] = useState<Status|null>(null);
  const [checked, setChecked] = useState<string|null>(null);
  const [unavailable, setUnavailable] = useState(false);
  useEffect(() => {
    let stopped = false;
    let timer: ReturnType<typeof setTimeout>;
    let request: AbortController|null = null;
    async function read() {
      request = new AbortController();
      const timeout = setTimeout(() => request?.abort(), 5000);
      try {
        const response = await fetch('/development-status.json', {cache:'no-store', credentials:'omit', signal:request.signal});
        if (!response.ok || Number(response.headers.get('content-length') ?? 0) > 16384) throw Error('status unavailable');
        const next = parseDevelopmentStatus(await response.text());
        if (Date.parse(next.reported_at) > Date.now()+60000) throw Error('future status');
        if (!stopped) {setRecord(next); setChecked(new Date().toISOString()); setUnavailable(false);}
      } catch {
        if (!stopped) setUnavailable(true);
      } finally {
        clearTimeout(timeout);
        if (!stopped) timer = setTimeout(() => {void read();}, 15000);
      }
    }
    void read();
    return () => {stopped=true; clearTimeout(timer); request?.abort();};
  }, []);
  return <>
    {!record && <p role="status">{unavailable?'개발 진행 기록을 불러오지 못했습니다. 15초 뒤 다시 확인합니다.':'최신 개발 진행 기록을 확인하고 있습니다.'}</p>}
    {record && <>
      <p>개발 기록 갱신: <time dateTime={record.reported_at}>{new Date(record.reported_at).toLocaleString('ko-KR')}</time></p>
      <ol>{record.stages.map(stage => <li key={stage.id}><strong>{stateNames[stage.state]} · {developmentStages[stage.id]}</strong> — {stage.evidence}</li>)}</ol>
      <p>새 환기 모델 화면 연결까지: 집중 작업 약 <strong>{record.remaining_focused_hours.min}–{record.remaining_focused_hours.max}시간</strong> 예상. 연속 작업 기준의 추정이며 완료 시각을 보장하지 않습니다.</p>
      <p>새 환기 모델: {record.new_model_deployed?'사용자 화면 적용됨':'현재 사용자 화면에 미배포'}. 실제 농장 Run: {record.real_farm_runs}건. 전체 제품 완료일: 미정.</p>
      {Date.now()-Date.parse(record.reported_at)>1800000 && <p>30분 이상 새 개발 기록이 없습니다. 위 내용은 마지막 검증 기록입니다.</p>}
      {unavailable && <p role="status">새 기록을 확인하지 못했습니다. 마지막 확인 기록을 표시합니다.</p>}
      <p className="crop-caption">기록을 15초마다 확인합니다. 마지막 조회: {checked?new Date(checked).toLocaleTimeString('ko-KR'):'미확인'}. 단계별 검증 뒤 갱신되는 개발 기록이며, 선택한 계산의 진행률은 아래에서 확인합니다.</p>
    </>}
    <p>현재 계산 화면은 기존 합성 입력의 작물·기후 계산과 확정 저장값의 3D를 제공합니다. 전체 제품은 자원 사용·생산량·경제 통합과 독립 농장 검증이 남아 있습니다.</p>
  </>;
}
