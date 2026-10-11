const panel = document.getElementById('preview-development-status');
const labels = {
  growth: '작물·환기 생장 계산', storage: '결과 저장·현재 권한 조회', api: '사용자 조회 API 연결',
  execution_3d: '자동 작업자·같은 시각의 3D 연결', activation: '실제 브라우저 검증·사용자 화면 적용',
};
const states = {completed: '검증 완료', next: '다음 작업', pending: '대기'};
const stamp = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$/;
const exact = (value, keys) => value !== null && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join(',') === [...keys].sort().join(',');
function parse(raw) {
  const v = JSON.parse(raw);
  if (!exact(v, ['schema_version','reported_at','stages','remaining_focused_hours',
    'new_model_deployed','real_farm_runs','full_product_completion']) || v.schema_version !== 'development-status-v1' ||
    typeof v.reported_at !== 'string' || !stamp.test(v.reported_at) || !Number.isFinite(Date.parse(v.reported_at)) ||
    Date.parse(v.reported_at) > Date.now()+60000 || typeof v.new_model_deployed !== 'boolean' ||
    !Number.isSafeInteger(v.real_farm_runs) || v.real_farm_runs < 0 || v.full_product_completion !== null) throw Error('invalid record');
  const hours = v.remaining_focused_hours;
  if (!exact(hours, ['min','max']) || !Number.isSafeInteger(hours.min) || !Number.isSafeInteger(hours.max) ||
    hours.min < 0 || hours.min > hours.max || hours.max > 100 || !Array.isArray(v.stages) || v.stages.length !== 5) throw Error('invalid range');
  v.stages.forEach((s, i) => {
    if (!exact(s, ['id','state','evidence']) || s.id !== Object.keys(labels)[i] || !Object.hasOwn(states, s.state) ||
      typeof s.evidence !== 'string' || !s.evidence.length || s.evidence.length > 240) throw Error('invalid stage');
  });
  return v;
}
if (panel) {
  const node = name => panel.querySelector(`[data-progress-${name}]`);
  const localTime = value => new Date(value).toLocaleString('ko-KR');
  let latest = null, latestRaw = null, stopped = false, request = null, timer;
  async function read() {
    request = new AbortController();
    const timeout = setTimeout(() => request.abort(), 5000);
    try {
      const response = await fetch('/development-status.json', {cache:'no-store', credentials:'omit', redirect:'error', signal:request.signal});
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json') ||
        Number(response.headers.get('content-length') ?? 0) > 16384 || !response.body) throw Error('record unavailable');
      const reader = response.body.getReader(), chunks = [];
      let length = 0;
      for (;;) {
        const {done, value} = await reader.read();
        if (done) break;
        length += value.byteLength;
        if (length > 16384) {await reader.cancel(); throw Error('record too large');}
        chunks.push(value);
      }
      const bytes = new Uint8Array(length);
      let offset = 0;
      for (const chunk of chunks) {bytes.set(chunk, offset); offset += chunk.byteLength;}
      const raw = new TextDecoder('utf-8', {fatal:true}).decode(bytes), record = parse(raw);
      if (latest && (record.reported_at < latest.reported_at ||
        (record.reported_at === latest.reported_at && raw !== latestRaw))) throw Error('record moved backwards');
      if (stopped) return;
      if (raw !== latestRaw) {
        node('time').textContent = `개발 기록 갱신: ${localTime(record.reported_at)}`;
        node('stages').replaceChildren(...record.stages.map(s => {
          const li = document.createElement('li'), strong = document.createElement('strong');
          strong.textContent = `${states[s.state]} · ${labels[s.id]}`;
          li.append(strong, document.createTextNode(` — ${s.evidence}`));
          return li;
        }));
        node('estimate').textContent = `새 환기 모델의 짧은 합성 계산 화면 연결: 약 ${record.remaining_focused_hours.min}–${record.remaining_focused_hours.max}집중작업시간 추정. 전체 제품 완료 시각을 뜻하지 않습니다.`;
        node('scope').textContent = `새 환기 모델: ${record.new_model_deployed ? '사용자 화면 적용됨' : '현재 사용자 화면에 미배포'}. 실제 농장 Run: ${record.real_farm_runs}건. 전체 제품 완료일: 미정.`;
        latest = record; latestRaw = raw;
        node('record').hidden = false;
      }
      node('message').textContent = Date.now()-Date.parse(latest.reported_at) > 1800000
        ? '30분 이상 새 개발 기록이 없습니다. 마지막 검증 기록을 표시합니다.'
        : '단계별 개발 기록입니다. 아래에서 완료한 검증과 남은 작업을 확인하세요.';
      node('checked').textContent = `기록을 15초마다 확인합니다. 마지막 조회: ${localTime(Date.now())}.`;
    } catch {
      if (!stopped) node('message').textContent = latest
        ? '새 기록을 확인하지 못했습니다. 마지막 검증 기록을 표시합니다. 15초 뒤 다시 확인합니다.'
        : '개발 기록을 불러오지 못했습니다. 15초 뒤 다시 확인합니다. 아래 링크에서도 현황을 확인할 수 있습니다.';
    } finally {
      clearTimeout(timeout);
      if (!stopped) timer = setTimeout(read, 15000);
    }
  }
  window.addEventListener('pagehide', () => {stopped = true; clearTimeout(timer); request?.abort();}, {once:true});
  void read();
}
