import { expect,test,vi } from 'vitest';
import { createApi,type CalculationAssessmentIntent } from './api';

const id='11111111-1111-4111-8111-111111111111';
const economic='22222222-2222-4222-8222-222222222222';
const token='synthetic-assessment-test-token';
const job={job_id:id,stage:'assessment',state:'queued',attempt_count:0,max_attempts:3,
  created_at:'2026-10-01T00:00:00Z',updated_at:'2026-10-01T00:00:00Z',reason_code:null};
const intent:CalculationAssessmentIntent={run_job_id:id,economic_job_id:economic,
  idempotency_key:'web-assessment-v1:one-intent'};
const reply=(value:unknown,status=200)=>new Response(JSON.stringify(value),{
  status,headers:{'content-type':'application/json'}});

test('assessment submits only parent IDs and stable key with strict 202 admission',async()=>{
  const fetcher=vi.fn<typeof fetch>().mockImplementation(async()=>reply(job,202));
  const api=createApi(token,fetcher);
  const extended={...intent,tenant_id:'never-forward',approved:true};
  expect(await api.assessCalculations(extended)).toEqual(job);
  await api.assessCalculations(intent);
  expect(fetcher).toHaveBeenCalledWith('/v1/assessments',expect.objectContaining({
    method:'POST',body:JSON.stringify(intent),cache:'no-store',credentials:'omit',redirect:'error',
    headers:{'content-type':'application/json',authorization:'Bearer '+token}}));
  expect(fetcher.mock.calls[0]?.[1]?.body).toBe(fetcher.mock.calls[1]?.[1]?.body);
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply(job))).assessCalculations(intent))
    .rejects.toMatchObject({code:'response_rejected'});
});

test.each([{run_job_id:'../foreign'},{economic_job_id:'BAD-UUID'},
  {idempotency_key:''},{idempotency_key:'a'.repeat(201)},{idempotency_key:'bad key'},
  {idempotency_key:'unaccepted&key'}])('invalid assessment intent does not make a request',async change=>{
  const fetcher=vi.fn<typeof fetch>();
  await expect(createApi(token,fetcher).assessCalculations({...intent,...change}))
    .rejects.toMatchObject({code:'response_rejected'});
  expect(fetcher).not.toHaveBeenCalled();
});

test.each([{stage:'research'},{state:'succeeded'},{state:'simulating'},
  {selected_crop:'invented'},{job_id:'../unsafe'}])('held assessment cannot decode a positive or foreign result',async change=>{
  const fetcher=vi.fn<typeof fetch>().mockResolvedValue(reply({...job,...change},202));
  await expect(createApi(token,fetcher).assessCalculations(intent))
    .rejects.toMatchObject({code:'response_rejected'});
});

test('assessment lookup and report require the same assessment job and public stage',async()=>{
  const hold={job_id:id,stage:'assessment',hold_id:economic,status:'hold',
    recorded_at:job.updated_at,reason_code:'evidence_missing',missing_evidence:['market_source_g0'],
    missing_evidence_count:1};
  const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(reply({...job,state:'hold'}))
    .mockResolvedValueOnce(reply(hold)).mockResolvedValueOnce(reply({...job,job_id:economic}))
    .mockResolvedValueOnce(reply({...hold,stage:'research'}));
  const api=createApi(token,fetcher);
  expect(await api.assessmentJob(id)).toEqual({...job,state:'hold'});
  expect(await api.assessmentHold(id)).toEqual(hold);
  expect(fetcher.mock.calls[0]?.[0]).toBe('/v1/jobs/'+id);
  expect(fetcher.mock.calls[1]?.[0]).toBe('/v1/jobs/'+id+'/hold-report');
  await expect(api.assessmentJob(id)).rejects.toMatchObject({code:'response_rejected'});
  await expect(api.assessmentHold(id)).rejects.toMatchObject({code:'response_rejected'});
});

test('lost assessment reply stays unknown and HTTP refusal contains no private details',async()=>{
  const fetcher=vi.fn<typeof fetch>().mockRejectedValueOnce(new Error('private connection'))
    .mockResolvedValueOnce(reply({private:'never render'},422));
  const api=createApi(token,fetcher);
  await expect(api.assessCalculations(intent)).rejects.toMatchObject({code:'network_unresolved',status:null});
  const error=await api.assessCalculations(intent).catch(error=>error);
  expect(error).toMatchObject({code:'invalid_request',status:422});
  expect(String(error)).not.toContain('private');
});
