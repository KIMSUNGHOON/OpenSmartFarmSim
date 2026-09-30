import { expect,test,vi } from 'vitest';
import { createApi } from './api';
import type { AuthoredFarmRequest } from './authored-farm-api';

const token='synthetic-authored-farm-client-token';
const uuid='11111111-1111-4111-8111-111111111111';
const job=(stage:string)=>({
  job_id:uuid,stage,state:'queued',attempt_count:0,max_attempts:3,
  created_at:'2026-09-30T00:00:00Z',updated_at:'2026-09-30T00:00:00Z',reason_code:null,
});
const identity={scenario_id:'farm-1',scenario_revision:'r1'};
const digest='a'.repeat(64);
const saved={...identity,scenario_sha256:digest,farm_sha256:digest,
  numeric_input_sha256:digest,rights_sha256:digest,
  registration_status:'registered_unpublished_inputs',intent_job:job('collection')};
const farm:AuthoredFarmRequest={schema_version:'farm-authoring-request-v1',
  farm:{...identity,schema_version:'farm-inputs-v1',facility:{zone_id:'zone-1'}},
  rights:{...identity,schema_version:'farm-assumption-rights-v1',ownership_asserted:true}};
const reply=(value:unknown,status=200)=>new Response(JSON.stringify(value),
  {status,headers:{'content-type':'application/json'}});

test('owned registration and exact lookup preserve identity and server proof',async()=>{
  const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(reply(saved))
    .mockResolvedValueOnce(reply(saved));
  const api=createApi(token,fetcher);
  expect(await api.registerAuthoredFarm(farm)).toEqual(saved);
  expect(await api.authoredFarm('farm-1','r1')).toEqual(saved);
  expect(fetcher.mock.calls.map(([path])=>path)).toEqual([
    '/v1/farm-authored-inputs',
    '/v1/farm-authored-inputs?scenario_id=farm-1&scenario_revision=r1',
  ]);
  expect(fetcher.mock.calls[0]?.[1]).toEqual(expect.objectContaining({
    method:'POST',body:JSON.stringify(farm),credentials:'omit',redirect:'error',cache:'no-store',
  }));
});

test('owned farm catalog pages contain only bounded server metadata',async()=>{
  const entries=Array.from({length:20},(_,index)=>({...saved,
    scenario_revision:'r'+(index+1),intent_job:{...saved.intent_job,
      job_id:'00000000-0000-4000-8000-'+String(index+1).padStart(12,'0')}}));
  const cursor={created_at:entries[19]!.intent_job.created_at,job_id:entries[19]!.intent_job.job_id};
  const fetcher=vi.fn<typeof fetch>()
    .mockResolvedValueOnce(reply({items:[saved],next_cursor:null}))
    .mockResolvedValueOnce(reply({items:entries,next_cursor:cursor}));
  const api=createApi(token,fetcher);
  expect((await api.authoredFarmCatalog()).items).toEqual([saved]);
  expect((await api.authoredFarmCatalog(cursor)).next_cursor).toEqual(cursor);
  expect(fetcher.mock.calls.map(([path])=>path)).toEqual([
    '/v1/farm-authored-inputs/catalog',
    '/v1/farm-authored-inputs/catalog?before_created_at=2026-09-30T00%3A00%3A00Z&before_job_id='
      +cursor.job_id,
  ]);
  await expect(api.authoredFarmCatalog({created_at:'bad',job_id:uuid}))
    .rejects.toMatchObject({code:'response_rejected'});
  expect(fetcher).toHaveBeenCalledTimes(2);
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply({
    items:[{...saved,private_input:'restricted'}],next_cursor:null}))).authoredFarmCatalog())
    .rejects.toMatchObject({code:'response_rejected'});
});

test('review and simulation admit only the pinned revision and preserve retry keys',async()=>{
  const fetcher=vi.fn<typeof fetch>().mockResolvedValueOnce(reply(job('collection_review'),202))
    .mockResolvedValueOnce(reply(job('simulation'),202));
  const api=createApi(token,fetcher);
  const review={...identity,registration_sha256:digest,idempotency_key:'review-r1'};
  const run={...review,review_job_id:uuid,idempotency_key:'run-r1'};
  expect((await api.submitAuthoredReview(review)).stage).toBe('collection_review');
  expect((await api.submitAuthoredRun(run)).stage).toBe('simulation');
  expect(JSON.parse(String(fetcher.mock.calls[0]?.[1]?.body))).toEqual({
    schema_version:'farm-authored-review-request-v1',...review,
  });
  expect(JSON.parse(String(fetcher.mock.calls[1]?.[1]?.body))).toEqual({
    schema_version:'authored-thermal-simulation-request-v1',...run,
  });
});

test('foreign registration, unexpected job stage and unsafe paths are rejected',async()=>{
  const foreign={...saved,scenario_revision:'r2'};
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply(foreign)))
    .authoredFarm('farm-1','r1')).rejects.toMatchObject({code:'response_rejected'});
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply({
    ...saved,private_input:'do not display'}))).registerAuthoredFarm(farm))
    .rejects.toMatchObject({code:'response_rejected'});
  await expect(createApi(token,vi.fn<typeof fetch>().mockResolvedValue(reply(job('research'),202)))
    .submitAuthoredReview({...identity,registration_sha256:digest,idempotency_key:'review-r1'}))
    .rejects.toMatchObject({code:'response_rejected'});
  const fetcher=vi.fn<typeof fetch>();
  await expect(createApi(token,fetcher).authoredFarm('../other','r1'))
    .rejects.toMatchObject({code:'response_rejected'});
  expect(fetcher).not.toHaveBeenCalled();
});
