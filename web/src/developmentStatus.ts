export const developmentStages = {
  growth: '작물·환기 생장 계산',
  storage: '결과 저장·현재 권한 조회',
  api: '사용자 조회 API 연결',
  execution_3d: '자동 작업자·같은 시각의 3D 연결',
  activation: '실제 브라우저 검증·사용자 화면 적용',
} as const;
type StatusFields = {
  reported_at: string;
  stages: {id: keyof typeof developmentStages; state: 'completed'|'next'|'pending'; evidence: string}[];
  new_model_deployed: boolean;
  real_farm_runs: number;
  full_product_completion: null;
};
type Hours = {min: number; max: number};
export type DevelopmentStatus = StatusFields & (
  {schema_version: 'development-status-v1'; remaining_focused_hours: Hours} |
  {schema_version: 'development-status-v2'; remaining_focused_hours: Hours|null;
    estimate_reviewed_at: string; estimate_reason: string}
);
function object(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw Error('invalid development status');
  return value as Record<string, unknown>;
}
function keys(value: Record<string, unknown>, expected: string[]) {
  if (Object.keys(value).sort().join(',') !== expected.sort().join(',')) throw Error('invalid development fields');
}
export function parseDevelopmentStatus(raw: string): DevelopmentStatus {
  if (new TextEncoder().encode(raw).length > 16384) throw Error('development status too large');
  const value = object(JSON.parse(raw));
  const v2 = value.schema_version === 'development-status-v2';
  keys(value, ['schema_version','reported_at','stages','remaining_focused_hours','new_model_deployed','real_farm_runs','full_product_completion',
    ...(v2 ? ['estimate_reviewed_at','estimate_reason'] : [])]);
  if ((!v2 && value.schema_version !== 'development-status-v1') || typeof value.reported_at !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$/.test(value.reported_at) ||
      !Number.isFinite(Date.parse(value.reported_at)) || typeof value.new_model_deployed !== 'boolean' ||
      !Number.isSafeInteger(value.real_farm_runs) || (value.real_farm_runs as number) < 0 ||
      value.full_product_completion !== null) throw Error('invalid development status');
  if (!v2 || value.remaining_focused_hours !== null) {
    const hours = object(value.remaining_focused_hours);
    keys(hours, ['min','max']);
    if (!Number.isSafeInteger(hours.min) || !Number.isSafeInteger(hours.max) ||
        (hours.min as number) < 0 || (hours.max as number) < (hours.min as number) ||
        (hours.max as number) > 100) throw Error('invalid development estimate');
  }
  if (v2 && (typeof value.estimate_reviewed_at !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$/.test(value.estimate_reviewed_at) ||
      !Number.isFinite(Date.parse(value.estimate_reviewed_at)) ||
      Date.parse(value.estimate_reviewed_at) > Date.parse(value.reported_at) ||
      typeof value.estimate_reason !== 'string' || !value.estimate_reason.trim() || value.estimate_reason.length > 240)) {
    throw Error('invalid estimate review');
  }
  if (!Array.isArray(value.stages) || value.stages.length !== Object.keys(developmentStages).length) throw Error('invalid development stages');
  const expected = Object.keys(developmentStages);
  value.stages.forEach((item, index) => {
    const stage = object(item); keys(stage, ['id','state','evidence']);
    if (stage.id !== expected[index] || !['completed','next','pending'].includes(stage.state as string) ||
        typeof stage.evidence !== 'string' || stage.evidence.length < 1 || stage.evidence.length > 240) throw Error('invalid development stage');
  });
  return value as DevelopmentStatus;
}
