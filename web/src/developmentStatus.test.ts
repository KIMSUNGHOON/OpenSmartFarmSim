import {describe, expect, it} from 'vitest';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';
import {parseDevelopmentStatus} from './developmentStatus';
const published = readFileSync(new URL('../public/development-status.json',import.meta.url),'utf8');
const raw = JSON.stringify({
  schema_version: 'development-status-v2',
  reported_at: '2026-10-12T06:00:00.000000Z',
  estimate_reviewed_at: '2026-10-12T06:00:00.000000Z',
  estimate_reason: 'Unknown remaining work while user activation is pending.',
  remaining_focused_hours: null,
  new_model_deployed: false,
  real_farm_runs: 0,
  full_product_completion: null,
  stages: ['growth','storage','api','execution_3d','activation'].map((id, index) => ({
    id, state: index === 4 ? 'next' : 'completed', evidence: 'Synthetic parser contract fixture.',
  })),
});
const inline = readFileSync(new URL('../preview-progress.js', import.meta.url), 'utf8');
const legacyParse = (recordRaw: string) => runInNewContext(inline+'\nparse(recordRaw)', {
  document: {getElementById: () => null}, TextEncoder, recordRaw,
});
describe.each([['React', parseDevelopmentStatus], ['5173', legacyParse]] as const)('%s development record', (_, parse) => {
  it('preserves the current published record without assuming historical milestones', () => {
    expect(parse(published)).toEqual(JSON.parse(published));
  });
  it('shows accepted storage and pending user activation', () => {
    const record = parse(raw);
    expect(record.stages[1]?.state).toBe('completed');
    expect(record.stages[4]?.state).toBe('next');
    expect(record.new_model_deployed).toBe(false);
    expect(record.remaining_focused_hours).toBeNull();
    expect(record.schema_version).toBe('development-status-v2');
  });
  it('reads historical numeric v1 records without inventing unknown hours', () => {
    const record = JSON.parse(raw);
    record.schema_version='development-status-v1';
    delete record.estimate_reviewed_at; delete record.estimate_reason;
    expect(() => parse(JSON.stringify(record))).toThrow();
    record.remaining_focused_hours={min:2,max:4};
    expect(parse(JSON.stringify(record)).remaining_focused_hours).toEqual({min:2,max:4});
  });
  it('allows a reviewed positive range in v2', () => {
    const record = JSON.parse(raw);
    record.remaining_focused_hours={min:1,max:3};
    expect(parse(JSON.stringify(record)).remaining_focused_hours).toEqual({min:1,max:3});
  });
  it.each(['{"state":"running"}', '<html>SPA fallback</html>', raw+' '.repeat(16385)])('rejects an invalid public record', value => {
    expect(() => parse(value)).toThrow();
  });
  it.each(['duplicate-stage','unknown-field','bad-time','bad-estimate','missing-review','future-review','blank-reason'])('rejects misleading record: %s', kind => {
    const record = JSON.parse(raw);
    if(kind==='duplicate-stage') record.stages[2]=record.stages[1];
    if(kind==='unknown-field') record.token='forbidden';
    if(kind==='bad-time') record.reported_at='tomorrow';
    if(kind==='bad-estimate') record.remaining_focused_hours={min:0,max:-1};
    if(kind==='missing-review') delete record.estimate_reviewed_at;
    if(kind==='future-review') record.estimate_reviewed_at='2099-01-01T00:00:00.000000Z';
    if(kind==='blank-reason') record.estimate_reason=' ';
    expect(() => parse(JSON.stringify(record))).toThrow();
  });
});
