import {describe, expect, it} from 'vitest';
import {readFileSync} from 'node:fs';
import {parseDevelopmentStatus} from './developmentStatus';
const raw = readFileSync(new URL('../public/development-status.json',import.meta.url),'utf8');
describe('published development record', () => {
  it('shows accepted storage and pending user activation', () => {
    const record = parseDevelopmentStatus(raw);
    expect(record.stages[1]?.state).toBe('completed');
    expect(record.stages[2]?.state).toBe('next');
    expect(record.new_model_deployed).toBe(false);
  });
  it.each(['{"state":"running"}', '<html>SPA fallback</html>', raw+' '.repeat(16385)])('rejects an invalid public record', value => {
    expect(() => parseDevelopmentStatus(value)).toThrow();
  });
  it.each(['duplicate-stage','unknown-field','bad-time','bad-estimate'])('rejects misleading record: %s', kind => {
    const record = JSON.parse(raw);
    if(kind==='duplicate-stage') record.stages[2]=record.stages[1];
    if(kind==='unknown-field') record.token='forbidden';
    if(kind==='bad-time') record.reported_at='tomorrow';
    if(kind==='bad-estimate') record.remaining_focused_hours.max=-1;
    expect(() => parseDevelopmentStatus(JSON.stringify(record))).toThrow();
  });
});
