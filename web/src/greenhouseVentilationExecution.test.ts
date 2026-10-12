import { afterEach,describe,it,expect,vi } from 'vitest';
import { createApi,ApiError,type JobStatus } from './api';
import { createGreenhouseVentilationExecutionApi,ventilationExecutionResultLookup,validVentilationExecutionRequest,
  type VentilationExecutionRequest,type VentilationExecutionLookup } from './greenhouseVentilationExecution';

const TOKEN='owned-synthetic-execution-token-'+'x'.repeat(32),ID='11111111-1111-4111-8111-111111111111';
const AT='2026-10-10T05:00:00.123456Z',OBS='2026-10-10T05:00:00.123457Z';
const FARM={scenario_id:'farm',scenario_revision:'r1',registration_sha256:'a'.repeat(64),crop_id:'crop'};
const LOOKUP:VentilationExecutionLookup={job_id:ID,farm:FARM};
const INPUT:VentilationExecutionRequest={study_id:'study',revision:'r1',farm:FARM,
  input:{schema_version:'joint-ventilation-input-source-v1',program_id:'program',source_sha256:'b'.repeat(64),
    context_sha256:'c'.repeat(64),time_binding_sha256:'d'.repeat(64),evidence_sha256:'e'.repeat(64)},
  rights:{schema_version:'joint-ventilation-input-rights-v1',declaration_id:'owned',revision:'r1',
    input_source_sha256:'b'.repeat(64),available_at:AT,redistribute:false,ownership_asserted:true,
    access:true,store:true,transform:true,use:true,display:true}};
const job=(state='queued',attempt=0)=>({job_id:ID,stage:'simulation',state,attempt_count:attempt,max_attempts:3,
  created_at:AT,updated_at:AT,reason_code:null});
const queued=()=>({version:'joint-ventilation-execution-query-v1',scope:'synthetic_joint_ventilation_math_only',
  G0_G4:'not_assessed',job:job(),cancel_requested:false,observed_at:OBS,checkpoint_status:'none',checkpoint:null,result:null});
const active=()=>({...queued(),job:job('simulating',1),checkpoint_status:'current',checkpoint:{head_sha256:'1'.repeat(64),
  proof_sha256:'2'.repeat(64),artifact_sha256:null,status:'yielded',steps:7,planned_steps:16,counts:{samples:3,events:1},
  computed_through_utc:'2026-10-01T00:00:14.123456Z',checkpoint_recorded_at:AT,publication_sequence:2}});
const terminal=(status='completed')=>({...active(),job:{...job(status==='completed'?'succeeded':'hold',1),
  reason_code:status==='hold'?'ventilation_numerical_hold':null},checkpoint:{...active().checkpoint,status,steps:16,artifact_sha256:'3'.repeat(64)},
  result:{result_id:'joint-ventilation-result-v1:'+'4'.repeat(64),farm:{...FARM,batch_id:'batch',zone_id:'zone'},status}});
const cancellation=(state='simulating')=>({version:'joint-ventilation-execution-cancel-v1',scope:'synthetic_joint_ventilation_math_only',
  G0_G4:'not_assessed',job:job(state,state==='queued'?0:1),cancel_requested:state==='simulating',cancel_accepted:true,observed_at:OBS});
type Raw=Record<string,any>;
function response(value:unknown,status=200){return new Response(JSON.stringify(value),{status,headers:{'content-type':'application/json'}});}
function client(value:unknown,status=200){const fetcher=vi.fn<typeof fetch>(async()=>response(value,status));return {api:createApi(TOKEN,fetcher),fetcher};}
function deferred<T>(){let release!:(value:T)=>void;const promise=new Promise<T>(r=>release=r);return {promise,release};}
afterEach(()=>vi.useRealTimers());

describe('ventilation execution limits and protocol',()=>{
  it.each(['steps','planned_steps','samples','events'])('rejects an out-of-contract %s',async field=>{
    const value=active();
    if(field==='steps')value.checkpoint.steps=4097;
    if(field==='planned_steps')value.checkpoint.planned_steps=4097;
    if(field==='samples')value.checkpoint.counts.samples=513;
    if(field==='events')value.checkpoint.counts.events=129;
    await expect(client(value).api.greenhouseVentilationExecution(LOOKUP)).rejects.toBeInstanceOf(ApiError);
  });
  it('rejects the other execution and input family',async()=>{
    const value=queued();value.version='joint-crop-climate-execution-query-v1';
    await expect(client(value).api.greenhouseVentilationExecution(LOOKUP)).rejects.toBeInstanceOf(ApiError);
    const request=structuredClone(INPUT) as Raw;request.input.schema_version='joint-crop-climate-input-source-v1';
    expect(validVentilationExecutionRequest(request)).toBe(false);
  });
});

describe('ventilation execution typed client',()=>{
  it.each([queued(),active(),terminal(),terminal('hold'),{...queued(),checkpoint_status:'unavailable'},
    {...terminal(),checkpoint_status:'unavailable',checkpoint:null,result:null},
    {...active(),job:job('queued',1)}, {...active(),job:job('canceled',1)},
    {...active(),checkpoint:{...active().checkpoint,status:'ready',steps:0,computed_through_utc:null}},
    {...active(),job:{...job('simulating',1),created_at:AT.replace('T05:','T14:').replace('Z','+09:00'),
      updated_at:AT.replace('T05:','T14:').replace('Z','+09:00')}}])
    ('keeps legal original values and UTC %#',async value=>{
      const {api}=client(value);expect(await api.greenhouseVentilationExecution(LOOKUP)).toEqual(value);
    });
  it.each(['completed','hold'])('selects the same saved %s result without estimating growth',async status=>{
    const {api}=client(terminal(status)),value=await api.greenhouseVentilationExecution(LOOKUP);
    expect(ventilationExecutionResultLookup(value)).toEqual({result_id:terminal(status).result.result_id,...FARM});
    expect(value.checkpoint?.computed_through_utc).toBe('2026-10-01T00:00:14.123456Z');
    expect(value.observed_at).toBe(OBS);
  });
  it('has no saved result for an unstarted or unavailable checkpoint',async()=>{
    expect(ventilationExecutionResultLookup(await client(queued()).api.greenhouseVentilationExecution(LOOKUP))).toBeNull();
  });
  it.each(['version','scope','gate','extra','job-id','stage','state','attempt','max-attempt','job-extra',
    'job-created','job-updated','job-offset','observed','observed-offset','observed-before','cancel-flag',
    'checkpoint-status','checkpoint-null','none-with-checkpoint','counts-extra','count-negative','count-unsafe','count-string',
    'checkpoint-extra','head','proof','artifact','steps','planned','steps-over','sequence-zero','sequence-over',
    'computed','computed-offset','ready-steps','ready-time','yielded-null','recorded-before','recorded-after',
    'result-extra','result-id','result-farm','result-batch','result-zone','result-status','result-job','result-checkpoint',
    'completed-steps','terminal-missing-result','terminal-none'])('rejects mixed or invalid %s',async fault=>{
      const p:Raw=fault.startsWith('result') || fault.startsWith('terminal') || fault==='completed-steps'?terminal():active();
      const c=p.checkpoint,j=p.job;
      if(fault==='version')p.version='old';if(fault==='scope')p.scope='production';if(fault==='gate')p.G0_G4='G2';if(fault==='extra')p.secret='private';
      if(fault==='job-id')j.job_id='22222222-2222-4222-8222-222222222222';if(fault==='stage')j.stage='research';
      if(fault==='state')j.state='researching';if(fault==='attempt')j.attempt_count=0;if(fault==='max-attempt')j.max_attempts=0;
      if(fault==='job-extra')j.lease_token='private';if(fault==='job-created')j.created_at='2026-02-30T00:00:00Z';
      if(fault==='job-updated')j.updated_at='2026-10-10T05:00:00.123455Z';if(fault==='job-offset')j.created_at=AT.replace('Z','+99:00');
      if(fault==='observed')p.observed_at='now';if(fault==='observed-offset')p.observed_at=OBS.replace('Z','+00:00');
      if(fault==='observed-before')p.observed_at='2026-10-10T05:00:00.123455Z';if(fault==='cancel-flag')p.cancel_requested=1;
      if(fault==='checkpoint-status')p.checkpoint_status='pending';if(fault==='checkpoint-null')p.checkpoint=null;
      if(fault==='none-with-checkpoint')p.checkpoint_status='none';if(fault==='counts-extra')c.counts.private=0;
      if(fault==='count-negative')c.counts.samples=-1;if(fault==='count-unsafe')c.counts.samples=2**53;if(fault==='count-string')c.counts.samples='3';
      if(fault==='checkpoint-extra')c.context={};if(fault==='head')c.head_sha256='x';if(fault==='proof')c.proof_sha256='A'.repeat(64);
      if(fault==='artifact')c.artifact_sha256='1'.repeat(64);if(fault==='steps')c.steps=1.5;if(fault==='planned')c.planned_steps=0;
      if(fault==='steps-over')c.steps=17;if(fault==='sequence-zero')c.publication_sequence=0;if(fault==='sequence-over')c.publication_sequence=4100;
      if(fault==='computed')c.computed_through_utc='2026-02-30T00:00:00Z';if(fault==='computed-offset')c.computed_through_utc=AT.replace('Z','+00:00');
      if(fault==='ready-steps'){c.status='ready';c.computed_through_utc=null;}if(fault==='ready-time'){c.status='ready';c.steps=0;}
      if(fault==='yielded-null')c.computed_through_utc=null;if(fault==='recorded-before')c.checkpoint_recorded_at='2026-10-10T05:00:00.123455Z';
      if(fault==='recorded-after')c.checkpoint_recorded_at='2026-10-10T05:00:00.123458Z';
      if(fault==='result-extra')p.result.private={};if(fault==='result-id')p.result.result_id='crop-result-v1:'+'4'.repeat(64);
      if(fault==='result-farm')p.result.farm.scenario_id='foreign';if(fault==='result-batch')p.result.farm.batch_id='';
      if(fault==='result-zone')p.result.farm.zone_id=null;if(fault==='result-status')p.result.status='yielded';
      if(fault==='result-job')j.state='simulating';if(fault==='result-checkpoint')c.status='hold';if(fault==='completed-steps')c.steps=15;
      if(fault==='terminal-missing-result')p.result=null;if(fault==='terminal-none'){p.result=null;p.checkpoint=null;p.checkpoint_status='none';}
      await expect(client(p).api.greenhouseVentilationExecution(LOOKUP)).rejects.toMatchObject({code:'response_rejected'});
    });
  it.each(['extra','missing','name','farm','farm-extra','input-version','input-extra','digest','rights-version','rights-extra',
    'rights-source','rights-date','redistribute',...['ownership_asserted','access','store','transform','use','display']])
    ('rejects invalid admission %s before fetch',async fault=>{
      const p:Raw=structuredClone(INPUT);if(fault==='extra')p.extra=true;if(fault==='missing')delete p.revision;
      if(fault==='name')p.study_id='한글';if(fault==='farm')p.farm.registration_sha256='short';if(fault==='farm-extra')p.farm.batch_id='batch';
      if(fault==='input-version')p.input.schema_version='old';if(fault==='input-extra')p.input.url='https://example.test';
      if(fault==='digest')p.input.context_sha256='A'.repeat(64);if(fault==='rights-version')p.rights.schema_version='old';
      if(fault==='rights-extra')p.rights.extra=true;if(fault==='rights-source')p.rights.input_source_sha256='c'.repeat(64);
      if(fault==='rights-date')p.rights.available_at='2026-02-30T00:00:00Z';if(fault==='redistribute')p.rights.redistribute=true;
      if(['ownership_asserted','access','store','transform','use','display'].includes(fault))p.rights[fault]=false;
      expect(validVentilationExecutionRequest(p)).toBe(false);const {api,fetcher}=client(job(),202);
      await expect(api.submitGreenhouseVentilationExecution(p as VentilationExecutionRequest)).rejects.toBeInstanceOf(ApiError);expect(fetcher).not.toHaveBeenCalled();
    });
  it('uses existing authenticated transport, admission202, read200 and cancellation200',async()=>{
    for(const operation of ['submit','read','cancel'] as const){
      const {api,fetcher}=client(operation==='submit'?job():operation==='read'?active():cancellation(),operation==='submit'?202:200);
      if(operation==='submit')await api.submitGreenhouseVentilationExecution(INPUT);else if(operation==='read')await api.greenhouseVentilationExecution(LOOKUP);
      else await api.cancelGreenhouseVentilationExecution(ID);
      const [path,init]=fetcher.mock.calls[0]!;
      expect(path).toBe(operation==='submit'?'/v1/crop-greenhouse-ventilation-executions':'/v1/jobs/'+ID+'/crop-greenhouse-ventilation-execution'+(operation==='cancel'?'/cancel':''));
      expect(init).toMatchObject({method:operation==='read'?'GET':'POST',credentials:'omit',redirect:'error',cache:'no-store'});
      expect(new Headers(init?.headers).get('authorization')).toBe('Bearer '+TOKEN);
      expect(init?.body).toBe(operation==='submit'?JSON.stringify(INPUT):undefined);
    }
  });
  it.each(['queued','simulating','succeeded','hold','failed','canceled'])('accepts idempotent admission returning %s',async state=>{
    expect((await client(job(state,state==='queued'?0:1),202).api.submitGreenhouseVentilationExecution(INPUT)).state).toBe(state);
  });
  it.each([cancellation(),{...cancellation('canceled'),cancel_requested:false},
    {...cancellation('succeeded'),cancel_accepted:false,cancel_requested:false}])('preserves cancellation acceptance and actual state %#',async value=>{
      expect(await client(value).api.cancelGreenhouseVentilationExecution(ID)).toEqual(value);
    });
  it.each(['extra','version','scope','gate','job','accepted','requested','time'])('rejects cancellation %s',async fault=>{
    const p:Raw=cancellation();if(fault==='extra')p.extra=true;if(fault==='version')p.version='old';if(fault==='scope')p.scope='production';
    if(fault==='gate')p.G0_G4='G2';if(fault==='job')p.job.job_id='22222222-2222-4222-8222-222222222222';
    if(fault==='accepted')p.cancel_accepted='true';if(fault==='requested')p.cancel_requested=0;if(fault==='time')p.observed_at=AT.replace('Z','+01:00');
    await expect(client(p).api.cancelGreenhouseVentilationExecution(ID)).rejects.toBeInstanceOf(ApiError);
  });
  it.each([[401,'auth_required'],[403,'access_denied'],[404,'not_available'],[409,'intent_conflict'],[413,'too_large'],
    [422,'invalid_request'],[503,'server_unavailable']] as const)('preserves HTTP %d as %s',async(status,code)=>{
    await expect(client({},status).api.greenhouseVentilationExecution(LOOKUP)).rejects.toMatchObject({code,status});
  });
  it('rejects noncanonical IDs and missing/extra farm selections without I/O',async()=>{
    const {api,fetcher}=client(queued());
    for(const select of [{...LOOKUP,job_id:'../private'},{...LOOKUP,extra:true},{job_id:ID,farm:{...FARM,extra:true}}]){
      await expect(api.greenhouseVentilationExecution(select)).rejects.toBeInstanceOf(ApiError);
    }
    await expect(api.cancelGreenhouseVentilationExecution('INVALID')).rejects.toBeInstanceOf(ApiError);expect(fetcher).not.toHaveBeenCalled();
  });
  it('rejects oversize bytes, malformed UTF8/JSON and wrong response status/type',async()=>{
    for(const make of [()=>new Response(' '.repeat(16385),{headers:{'content-type':'application/json'}}),
      ()=>new Response(new Uint8Array([255]),{headers:{'content-type':'application/json'}}),
      ()=>new Response('{',{headers:{'content-type':'application/json'}}),()=>response(queued(),202),()=>new Response('{}')]){
      const fetcher=vi.fn<typeof fetch>(async()=>make());await expect(createApi(TOKEN,fetcher).greenhouseVentilationExecution(LOOKUP)).rejects.toBeInstanceOf(ApiError);
    }
  });
  it('propagates already aborted and late aborts, releases transport and permits another request',async()=>{
    const abort=new AbortController();abort.abort();const {api,fetcher}=client(queued());
    await expect(api.greenhouseVentilationExecution(LOOKUP,abort.signal)).rejects.toMatchObject({code:'request_canceled'});expect(fetcher).not.toHaveBeenCalled();
    const pending=deferred<Response>(),late=new AbortController(),lateFetcher=vi.fn<typeof fetch>(()=>pending.promise),sdk=createApi(TOKEN,lateFetcher);
    const read=sdk.greenhouseVentilationExecution(LOOKUP,late.signal);late.abort();pending.release(response(queued()));
    await expect(read).rejects.toMatchObject({code:'request_canceled'});expect(lateFetcher.mock.calls[0]![1]?.signal?.aborted).toBe(true);
    lateFetcher.mockImplementation(async()=>response(queued()));expect(await sdk.greenhouseVentilationExecution(LOOKUP)).toEqual(queued());
  });
  it('keeps caller mutations out of the admitted body and rejects changed selections after await',async()=>{
    const done=deferred<unknown>(),bodies:unknown[]=[];
    const request=vi.fn(async(_path:string,_method?:string,body?:unknown)=>{bodies.push(body);return done.promise;});
    const sdk=createGreenhouseVentilationExecutionApi(request,value=>value as JobStatus),input={...INPUT,farm:{...FARM}};
    const pending=sdk.submitGreenhouseVentilationExecution(input);input.farm.scenario_id='changed';done.release(job());
    await expect(pending).rejects.toBeInstanceOf(ApiError);expect(bodies[0]).toEqual(INPUT);
    const reply=deferred<Response>(),select={job_id:ID,farm:{...FARM}},api=createApi(TOKEN,vi.fn<typeof fetch>(()=>reply.promise));
    const read=api.greenhouseVentilationExecution(select);select.farm.crop_id='changed';reply.release(response(active()));await expect(read).rejects.toBeInstanceOf(ApiError);
  });
  it('times out through the existing abort transport and removes the timer',async()=>{
    vi.useFakeTimers();const fetcher=vi.fn<typeof fetch>(async(_path,init)=>new Promise((_resolve,reject)=>{
      init?.signal?.addEventListener('abort',()=>reject(new DOMException('aborted','AbortError')),{once:true});}));
    const pending=createApi(TOKEN,fetcher).greenhouseVentilationExecution(LOOKUP);
    const rejected=expect(pending).rejects.toMatchObject({code:'network_unresolved'});
    await vi.advanceTimersByTimeAsync(30_000);await rejected;expect(vi.getTimerCount()).toBe(0);
  });
});
