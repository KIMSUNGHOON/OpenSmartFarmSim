import { it,expect,vi,afterEach } from 'vitest';
import { createHash } from 'node:crypto';
import { decodeLeafPopulationRequest,decodeLeafPopulationStatus,decodeLeafPopulationExecutionReplay,createLeafPopulationExecutionClient } from './leafPopulationExecution';
import { leafResponse,leafJobId,leafRequest,leafPreview,leafFlags,leafToken } from '../e2e/leaf-population-execution-fixture';

afterEach(()=>{vi.unstubAllGlobals();vi.useRealTimers();});
const clone=<T,>(value:T):T=>structuredClone(value);
const json=(value:unknown,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});

it('preserves all original12 frames/52 areas, exact clocks, parent and original server time',async()=>{
  const original=leafResponse(),loaded=await decodeLeafPopulationExecutionReplay(original,leafJobId);
  expect(loaded.replay.frames).toEqual(original.replay.frames);expect(loaded.replay.frames.flatMap(f=>f.leaves)).toHaveLength(52);
  expect(loaded.status.result?.parent_job_id).toBe(original.result.parent_job_id);
  expect(loaded.status.result?.calculated_at).toBe('2026-10-23T04:01:00.123456Z');
});
it.each(['job','scope','normalization','parent','signed_parent','root','count','order','time','unit','duplicate_leaf','attachment','birth','sum','private'])('rejects inconsistent %s without a substitute',async(change)=>{
  const value=leafResponse();
  if(change==='job')value.job.job_id=value.result.parent_job_id;
  else if(change==='scope')value.gates='G1';
  else if(change==='normalization')value.result.normalization='per_m2';
  else if(change==='parent')value.result.parent_numerical_root_sha256='0'.repeat(64);
  else if(change==='signed_parent')value.replay.manifest.parent_result_sha256='0'.repeat(64);
  else if(change==='root')value.replay.manifest.manifest.program_sha256='0'.repeat(64);
  else if(change==='count')value.replay.frames.pop();
  else if(change==='order')value.replay.frames.reverse();
  else if(change==='time')value.replay.frames[0].at=value.replay.frames[1].at;
  else if(change==='unit')value.replay.frames[0].leaves[0].area.unit='cm2';
  else if(change==='duplicate_leaf')value.replay.frames[0].leaves[1].leaf_id=value.replay.frames[0].leaves[0].leaf_id;
  else if(change==='attachment')value.replay.frames[0].leaves[0].attachment_internode_id='missing';
  else if(change==='birth')value.replay.frames[0].leaves[0].emerged_elapsed_seconds_exact.denominator='0';
  else if(change==='sum')value.replay.frames[0].tracked_leaf_area.value*=2;
  else Object.assign(value,{private_source:'not permitted'});
  await expect(decodeLeafPopulationExecutionReplay(value,leafJobId)).rejects.toThrow();
});
it('accepts a structurally consistent non-public root with denied redistribution',async()=>{
  const value=leafResponse(),root=value.replay.manifest.manifest;root.program_rights.redistribute=false;
  const canonical=(v:unknown):string=>v===null||typeof v!=='object'?JSON.stringify(v):Array.isArray(v)?'['+v.map(canonical).join(',')+']':
    '{'+Object.keys(v).sort().map(k=>JSON.stringify(k)+':'+canonical(Reflect.get(v,k))).join(',')+'}';
  const digest=createHash('sha256').update(canonical(root)).digest('hex');value.result.numerical_root_sha256=digest;
  value.replay.manifest.numerical_root_sha256=digest;for(const frame of value.replay.frames)frame.artifact_sha256=digest;
  expect((await decodeLeafPopulationExecutionReplay(value,leafJobId)).replay.artifact_sha256).toBe(digest);
});
it.each(['parent','rights','extra'])('rejects invalid request %s',change=>{
  const value=leafRequest();if(change==='parent')value.parent.job_id='../escape';
  else if(change==='rights')value.rights.input_source_sha256='0'.repeat(64);else Object.assign(value,{tenant_id:'other'});
  expect(()=>decodeLeafPopulationRequest(value)).toThrow();
});
it('pending/canceled statuses have no numerical result',()=>{
  const value=leafResponse();Object.assign(value,{result:null,replay:null});value.job.state='queued';
  expect(decodeLeafPopulationStatus(value,leafJobId).result).toBeNull();value.job.state='canceled';
  expect(decodeLeafPopulationStatus(value,leafJobId).job.state).toBe('canceled');
});
it('uses exact authenticated paths and explicit current read without static fallback',async()=>{
  const value=leafResponse(),calls:RequestInit[]=[];const urls:string[]=[];
  vi.stubGlobal('fetch',vi.fn(async(url:string,options:RequestInit)=>{urls.push(url);calls.push(options);
    return json(url==='/leaf-preview-input'?leafPreview():{...value,replay:null});}));
  const api=createLeafPopulationExecutionClient(leafToken),signal=new AbortController().signal;
  expect((await api.preview(signal)).request).toEqual(leafRequest());await api.status(leafJobId,signal);
  expect(urls).toEqual(['/leaf-preview-input',`/v1/jobs/${leafJobId}/crop-leaf-population-execution`]);
  expect(calls.every(v=>v.cache==='no-store'&&v.credentials==='omit'&&v.redirect==='error')).toBe(true);
  expect(calls[0]?.headers).toEqual({Authorization:'Bearer '+leafToken});
});
it('preserves the exact same pending request on repeat submission',async()=>{
  const row=leafResponse().job,bodies:string[]=[];vi.stubGlobal('fetch',vi.fn(async(_url:string,options:RequestInit)=>{bodies.push(String(options.body));return json(row,202);}));
  const api=createLeafPopulationExecutionClient(leafToken),body=decodeLeafPopulationRequest(leafRequest()),signal=new AbortController().signal;
  await api.submit(body,signal);await api.submit(clone(body),signal);expect(bodies).toHaveLength(2);expect(bodies[0]).toBe(bodies[1]);
});
it.each([401,403,409,422,503,504])('propagates HTTP%s once without automatic POST retry',async(status)=>{
  const fetch=vi.fn(async()=>json({error:{code:'unavailable'}},status));vi.stubGlobal('fetch',fetch);
  await expect(createLeafPopulationExecutionClient(leafToken).submit(decodeLeafPopulationRequest(leafRequest()),new AbortController().signal)).rejects.toMatchObject({status});
  expect(fetch).toHaveBeenCalledTimes(1);
});
it('reads cancellation under the matching leaf job and unassessed flags',async()=>{
  const row=leafResponse().job;vi.stubGlobal('fetch',vi.fn(async()=>json({schema_version:'leaf-population-execution-cancel-v1',...leafFlags,
    observed_at:'2026-10-23T04:02:00Z',job:{...row,state:'canceled'},cancel_requested:true,cancel_accepted:true})));
  expect((await createLeafPopulationExecutionClient(leafToken).cancel(leafJobId,new AbortController().signal)).job.state).toBe('canceled');
});
it('reads status for pending jobs and requests replay only after an unchanged completed summary',async()=>{
  const value=leafResponse(),pending={...value,job:{...value.job,state:'simulating'},result:null,replay:null};
  const fetch=vi.fn().mockResolvedValueOnce(json(pending)).mockResolvedValueOnce(json({...value,replay:null})).mockResolvedValueOnce(json(value));vi.stubGlobal('fetch',fetch);
  const api=createLeafPopulationExecutionClient(leafToken),signal=new AbortController().signal;
  expect((await api.observe(leafJobId,signal)).replay).toBeNull();
  expect((await api.observe(leafJobId,signal)).replay?.frames).toHaveLength(12);
  expect(fetch.mock.calls.map(call=>call[0])).toEqual([`/v1/jobs/${leafJobId}/crop-leaf-population-execution`,
    `/v1/jobs/${leafJobId}/crop-leaf-population-execution`,`/v1/jobs/${leafJobId}/crop-leaf-population-execution/replay`]);
});
it('rejects a different completed result between status and replay',async()=>{
  const value=leafResponse(),status={...value,result:{...value.result,result_sha256:'a'.repeat(64)},replay:null};
  vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(json(status)).mockResolvedValueOnce(json(value)));
  await expect(createLeafPopulationExecutionClient(leafToken).observe(leafJobId,new AbortController().signal)).rejects.toThrow();
});
it('bounds the response stream at2MiB and cancels further reads',async()=>{
  let cancelled=false;
  const stream=new ReadableStream({pull(c){c.enqueue(new Uint8Array(2*1024**2+1));},cancel(){cancelled=true;}});
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(stream,{headers:{'Content-Type':'application/json','Cache-Control':'no-store'}})));
  await expect(createLeafPopulationExecutionClient(leafToken).status(leafJobId,new AbortController().signal)).rejects.toThrow();expect(cancelled).toBe(true);
});
it.each(['media','cache','utf8'])('rejects invalid response transport %s',async(fault)=>{
  const headers={'Content-Type':fault==='media'?'text/html':'application/json','Cache-Control':fault==='cache'?'public':'no-store'};
  vi.stubGlobal('fetch',vi.fn(async()=>new Response(fault==='utf8'?new Uint8Array([255]):JSON.stringify({...leafResponse(),replay:null}),{headers})));
  await expect(createLeafPopulationExecutionClient(leafToken).status(leafJobId,new AbortController().signal)).rejects.toThrow();
});
it('propagates caller cancellation and never retries a request',async()=>{
  const fetch=vi.fn((_url:string,options:RequestInit)=>new Promise((_resolve,reject)=>options.signal?.addEventListener('abort',()=>reject(options.signal?.reason),{once:true})));
  vi.stubGlobal('fetch',fetch);const controller=new AbortController();const pending=createLeafPopulationExecutionClient(leafToken).status(leafJobId,controller.signal);
  controller.abort();await expect(pending).rejects.toBeDefined();expect(fetch).toHaveBeenCalledTimes(1);
});
