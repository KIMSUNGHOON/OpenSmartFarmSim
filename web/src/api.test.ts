import { expect, test, vi } from 'vitest';
import { createApi, ApiError, type LocationIntent } from './api';

const id = '11111111-1111-4111-8111-111111111111';
const token = 'synthetic-browser-test-token-only';
const job = { job_id:id, stage:'research', state:'queued', attempt_count:0, max_attempts:3,
  created_at:'2026-09-29T00:00:00Z', updated_at:'2026-09-29T00:00:00Z', reason_code:null };
const intent: LocationIntent = { latitude:37.5, longitude:127,
  period_start_utc:'2026-10-15T08:00:00Z', period_end_utc:'2026-10-15T10:00:00Z',
  goal_id:'owned-fixture-contract-check', idempotency_key:'one-intent' };
const reply = (value:unknown, status=200) => new Response(JSON.stringify(value),
  { status, headers:{'content-type':'application/json'} });

test('admission sends only fixed same-origin contract and preserves caller intent key', async () => {
  const value = { location_id:'location-v1-'+'a'.repeat(64), point:{latitude:37.5,longitude:127},
    spatial_support:'pending_research', research_job:job };
  const fetcher = vi.fn<typeof fetch>().mockImplementation(async()=>reply(value,202));
  const api = createApi(token, fetcher);
  expect(await api.location(intent)).toEqual(value);
  expect(fetcher).toHaveBeenCalledWith('/v1/locations', expect.objectContaining({
    method:'POST', redirect:'error', credentials:'omit', cache:'no-store', body:JSON.stringify(intent),
    headers:{'content-type':'application/json', authorization:'Bearer '+token} }));
  await api.location(intent);
  expect(fetcher.mock.calls[1]?.[1]?.body).toBe(fetcher.mock.calls[0]?.[1]?.body);
});

test('known job and bounded hold are decoded', async () => {
  const hold = {job_id:id,stage:'research',hold_id:id,status:'hold',recorded_at:job.updated_at,
    reason_code:'evidence_missing',missing_evidence:['signed_decision_context'],missing_evidence_count:1};
  const fetcher = vi.fn<typeof fetch>().mockResolvedValueOnce(reply(job)).mockResolvedValueOnce(reply(hold));
  const api = createApi(token,fetcher);
  expect(await api.job(id)).toEqual(job);
  expect(await api.hold(id)).toEqual(hold);
});

test('source collection and review use their fixed parent fields and reject foreign stages',async () => {
  const collection={...job,stage:'collection'};
  const review={...job,stage:'collection_review'};
  const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(reply(collection,202))
    .mockResolvedValueOnce(reply(review,202)).mockResolvedValueOnce(reply(job,202));
  const api=createApi(token,fetcher);
  const source={parent_job_id:id,idempotency_key:'source-intent-1'};
  expect(await api.ingestSource(source)).toEqual(collection);
  expect(await api.reviewSource(source)).toEqual(review);
  expect(JSON.parse(String(fetcher.mock.calls[0]?.[1]?.body))).toEqual({
    research_job_id:id,idempotency_key:source.idempotency_key});
  expect(JSON.parse(String(fetcher.mock.calls[1]?.[1]?.body))).toEqual({
    collection_job_id:id,idempotency_key:source.idempotency_key});
  await expect(api.ingestSource(source)).rejects.toMatchObject({code:'response_rejected'});
  await expect(api.reviewSource({...source,parent_job_id:'../foreign'}))
    .rejects.toMatchObject({code:'response_rejected'});
  expect(fetcher).toHaveBeenCalledTimes(3);
});

test('real server timestamps preserve their explicit timezone and microseconds',async () => {
  const value={...job,created_at:'2026-09-29T17:09:21.652617+09:00',updated_at:'2026-09-29T17:09:21.652617+09:00'};
  expect(await createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply(value))).job(id)).toEqual(value);
});

test.each([401,403,404,409,413,422,503])('HTTP %s produces a bounded message without raw details',async status => {
  const api = createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply({detail:'private backend value'},status)));
  const error = await api.job(id).catch(error=>error);
  expect(error).toBeInstanceOf(ApiError);
  expect(error.status).toBe(status);
  expect(String(error)).not.toContain('private');
});

test.each([
  {...job,stage:'unknown'}, {...job,state:'simulated'}, {...job,job_id:'../../outside'},
  {...job,attempt_count:-1}, {...job,max_attempts:4}, {...job,created_at:'not-a-date'},
  {...job,created_at:'2026-02-30T00:00:00Z'},
  {...job,private_source:'must not be rendered'}, {...job,reason_code:'<script>alert(1)</script>'},
])('malformed job is never exposed',async value => {
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply(value))).job(id))
    .rejects.toMatchObject({code:'response_rejected'});
});

test('unexpected successful HTTP status cannot claim admission',async () => {
  const value={location_id:'location-v1-'+'a'.repeat(64),point:{latitude:37.5,longitude:127},
    spatial_support:'pending_research',research_job:job};
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply(value,200))).location(intent))
    .rejects.toMatchObject({code:'response_rejected'});
});

test('response byte limit cancels an oversized UTF-8 stream before decoding',async () => {
  let canceled=false;
  const body=new ReadableStream<Uint8Array>({start(controller) {
    controller.enqueue(new TextEncoder().encode('가'.repeat(22_000)));
  },cancel(){canceled=true;}});
  const response=new Response(body,{headers:{'content-type':'application/json'}});
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(response)).job(id))
    .rejects.toMatchObject({code:'response_rejected'});
  expect(canceled).toBe(true);
});

test('foreign result, unknown evidence and mismatched count are rejected',async () => {
  const base = {job_id:id,stage:'research',hold_id:id,status:'hold',recorded_at:job.updated_at,
    reason_code:'evidence_missing',missing_evidence:['signed_decision_context'],missing_evidence_count:1};
  for (const change of [{job_id:'22222222-2222-4222-8222-222222222222'},
    {missing_evidence:['raw-private-id']}, {missing_evidence_count:0}]) {
    await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply({...base,...change}))).hold(id))
      .rejects.toMatchObject({code:'response_rejected'});
  }
});

test('invalid identity or path does not send a request; lost response stays unresolved',async () => {
  const fetcher=vi.fn<typeof fetch>().mockRejectedValue(new Error('private network details'));
  expect(()=>createApi('bad\r\nheader',fetcher)).toThrow(ApiError);
  await expect(createApi(token,fetcher).job('../outside')).rejects.toBeInstanceOf(ApiError);
  expect(fetcher).not.toHaveBeenCalled();
  await expect(createApi(token,fetcher).location(intent)).rejects.toMatchObject({code:'network_unresolved'});
});
