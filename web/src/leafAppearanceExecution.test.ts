import {it,expect,vi,afterEach} from 'vitest';
import {createHash} from 'node:crypto';
import {decodeLeafAppearanceRequest,decodeLeafAppearanceStatus,decodeLeafAppearanceExecutionReplay,createLeafAppearanceExecutionClient} from './leafAppearanceExecution';
import {appearanceResponse,appearanceManifestResponse,appearanceFrameResponse,appearanceJobId,appearanceRequest,appearancePreview,appearanceFlags,appearanceToken} from '../e2e/leaf-appearance-execution-fixture';
import {leafResponse} from '../e2e/leaf-population-execution-fixture';

const clone=<T,>(value:T):T=>structuredClone(value);
const json=(value:unknown,status=200)=>new Response(JSON.stringify(value),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
const signal=()=>new AbortController().signal;
afterEach(()=>vi.unstubAllGlobals());

it('preserves original12 frames/47 areas and source/parent/exact clocks/server first time',async()=>{
 const value=appearanceResponse(),out=await decodeLeafAppearanceExecutionReplay(value,appearanceJobId);
 expect(out.replay.frames).toEqual(value.replay.frames);expect(out.replay.frames.flatMap(f=>f.leaves)).toHaveLength(47);
 expect(out.status.result?.parent_job_id).toBe(value.result.parent_job_id);
 expect(out.status.result?.calculated_at).toBe('2026-10-23T19:01:00.123456Z');
 expect('policy' in out.replay).toBe(false);
});
it.each(['family','job','gate','normalization','parent','signed_parent','root','count','order','time','unit','duplicate','attachment','birth','sum','policy','profile','source','population','preparation','display','code','private'])('rejects inconsistent %s',async(fault)=>{
 const v=appearanceResponse(),f=v.replay.frames[0];
 if(fault==='family'){const other=leafResponse();other.job.job_id=appearanceJobId;await expect(decodeLeafAppearanceExecutionReplay(other,appearanceJobId)).rejects.toThrow();return;}
 if(fault==='job')v.job.job_id=v.result.parent_job_id;
 else if(fault==='gate')v.gates='G1';
 else if(fault==='normalization')v.result.normalization='per_m2';
 else if(fault==='parent')v.result.parent_numerical_root_sha256='0'.repeat(64);
 else if(fault==='signed_parent')v.replay.manifest.parent_result_sha256='0'.repeat(64);
 else if(fault==='root')v.replay.manifest.manifest.source_program_sha256='0'.repeat(64);
 else if(fault==='count')v.replay.frames.pop();
 else if(fault==='order')v.replay.frames.reverse();
 else if(fault==='time')f.at=v.replay.frames[1].at;
 else if(fault==='unit')f.leaves[0].area.unit='cm2';
 else if(fault==='duplicate')f.leaves[1].leaf_id=f.leaves[0].leaf_id;
 else if(fault==='attachment')f.leaves[0].attachment_internode_id='missing';
 else if(fault==='birth')f.leaves[0].emerged_elapsed_seconds_exact.denominator='0';
 else if(fault==='sum')f.tracked_leaf_area.value*=2;
 else if(fault==='policy')v.replay.frames[1].policy_sha256='0'.repeat(64);
 else if(fault==='profile')v.replay.frames[1].leaf_profile_sha256='0'.repeat(64);
 else if(fault==='source')f.source_program_sha256='0'.repeat(64);
 else if(fault==='population')f.population_artifact_sha256='0'.repeat(64);
 else if(fault==='preparation')f.preparation_sha256='0'.repeat(64);
 else if(fault==='display')f.display_policy.leaf_count='arbitrary';
 else if(fault==='code')v.replay.manifest.manifest.code_sha256={};
 else Object.assign(v,{private_source:'not permitted'});
 await expect(decodeLeafAppearanceExecutionReplay(v,appearanceJobId)).rejects.toThrow();
});
it('accepts another structurally bound root and non-redistributable input without fixed fixture root',async()=>{
 const v=appearanceResponse(),root=v.replay.manifest.manifest;root.program_rights.redistribute=false;
 const canonical=(x:unknown):string=>x===null||typeof x!=='object'?JSON.stringify(x):Array.isArray(x)?'['+x.map(canonical).join(',')+']':
 '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(Reflect.get(x,k))).join(',')+'}';
 const digest=createHash('sha256').update(canonical(root)).digest('hex');v.result.numerical_root_sha256=digest;
 v.replay.manifest.numerical_root_sha256=digest;for(const f of v.replay.frames)f.artifact_sha256=digest;
 expect((await decodeLeafAppearanceExecutionReplay(v,appearanceJobId)).replay.artifact_sha256).toBe(digest);
});
it.each(['parent','rights','family','extra'])('rejects invalid request %s',fault=>{
 const v=appearanceRequest();if(fault==='parent')v.parent.job_id='../escape';else if(fault==='rights')v.rights.input_source_sha256='0'.repeat(64);
 else if(fault==='family')v.input.schema_version='leaf-population-input-source-v1';else Object.assign(v,{tenant_id:'other'});
 expect(()=>decodeLeafAppearanceRequest(v)).toThrow();
});
it('keeps pending/canceled result and all numerical views null',()=>{
 const v={...appearanceResponse(),result:null,replay:null,job:{...appearanceResponse().job,state:'simulating'}};
 expect(decodeLeafAppearanceStatus(v,appearanceJobId).result).toBeNull();v.job.state='canceled';
 expect(decodeLeafAppearanceStatus(v,appearanceJobId).job.state).toBe('canceled');
 expect(()=>decodeLeafAppearanceStatus({...v,replay:{}},appearanceJobId)).toThrow();
});
it('uses exact current authenticated paths and bounded no-store transport',async()=>{
 const urls:string[]=[],calls:RequestInit[]=[];vi.stubGlobal('fetch',vi.fn(async(url:string,opts:RequestInit)=>{urls.push(url);calls.push(opts);return json(url==='/leaf-appearance-preview-input'?appearancePreview():{...appearanceResponse(),replay:null});}));
 const api=createLeafAppearanceExecutionClient(appearanceToken);expect((await api.preview(signal())).request).toEqual(appearanceRequest());await api.status(appearanceJobId,signal());
 expect(urls).toEqual(['/leaf-appearance-preview-input',`/v1/jobs/${appearanceJobId}/crop-leaf-appearance-execution`]);
 expect(calls.every(v=>v.cache==='no-store'&&v.credentials==='omit'&&v.redirect==='error')).toBe(true);expect(calls[0]?.headers).toEqual({Authorization:'Bearer '+appearanceToken});
});
it('preserves same pending body and never adds an automatic POST',async()=>{
 const bodies:string[]=[];const fetch=vi.fn(async(_url:string,opts:RequestInit)=>{bodies.push(String(opts.body));return json(appearanceResponse().job,202);});vi.stubGlobal('fetch',fetch);
 const api=createLeafAppearanceExecutionClient(appearanceToken),body=decodeLeafAppearanceRequest(appearanceRequest());await api.submit(body,signal());await api.submit(clone(body),signal());
 expect(bodies[0]).toBe(bodies[1]);expect(body).toEqual(appearanceRequest());expect(fetch).toHaveBeenCalledTimes(2);
});
it.each([401,403,409,422,429,503,504])('propagates HTTP%s once with unchanged pending body',async(status)=>{
 const fetch=vi.fn(async()=>json({error:{code:'unavailable'}},status));vi.stubGlobal('fetch',fetch);const body=decodeLeafAppearanceRequest(appearanceRequest());
 await expect(createLeafAppearanceExecutionClient(appearanceToken).submit(body,signal())).rejects.toMatchObject({status});expect(body).toEqual(appearanceRequest());expect(fetch).toHaveBeenCalledTimes(1);
});
it('returns null while simulating and binds completed status to subsequent replay',async()=>{
 const v=appearanceResponse(),pending={...v,result:null,replay:null,job:{...v.job,state:'simulating'}};
 const fetch=vi.fn().mockResolvedValueOnce(json(pending)).mockResolvedValueOnce(json({...v,replay:null})).mockResolvedValueOnce(json(v));vi.stubGlobal('fetch',fetch);
 const api=createLeafAppearanceExecutionClient(appearanceToken);expect((await api.observe(appearanceJobId,signal())).replay).toBeNull();expect((await api.observe(appearanceJobId,signal())).replay?.frames).toHaveLength(12);
 expect(fetch.mock.calls).toHaveLength(3);
});
it('rejects a changed completed summary between status and replay',async()=>{
 const v=appearanceResponse();vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(json({...v,replay:null,result:{...v.result,result_sha256:'a'.repeat(64)}})).mockResolvedValueOnce(json(v)));
 await expect(createLeafAppearanceExecutionClient(appearanceToken).observe(appearanceJobId,signal())).rejects.toThrow();
});
it('reads original manifest and a frame under its unchanged summary',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce(json(appearanceManifestResponse())).mockResolvedValueOnce(json(appearanceManifestResponse())).mockResolvedValueOnce(json(appearanceFrameResponse(3)));vi.stubGlobal('fetch',fetch);
 const api=createLeafAppearanceExecutionClient(appearanceToken);expect((await api.manifest(appearanceJobId,signal())).root.sample_count).toBe(12);
 const out=await api.frame(appearanceJobId,3,signal());expect(out.frame).toEqual(appearanceResponse().replay.frames[3]);expect(out.frame_sha256).toBe(appearanceFrameResponse(3).frame.frame_sha256);
 expect(fetch.mock.calls.map(q=>q[0])).toEqual([`/v1/jobs/${appearanceJobId}/crop-leaf-appearance-execution/manifest`,`/v1/jobs/${appearanceJobId}/crop-leaf-appearance-execution/manifest`,`/v1/jobs/${appearanceJobId}/crop-leaf-appearance-execution/frames/3`]);
});
it.each(['summary','index','digest','extra'])('rejects invalid signed frame %s',async(fault)=>{
 const f=appearanceFrameResponse();if(fault==='summary')f.result.parent_result_sha256='a'.repeat(64);else if(fault==='index')f.frame.frame.index=1;
 else if(fault==='digest')f.frame.frame_sha256='invalid';else Object.assign(f.frame,{private_key:'forbidden'});
 vi.stubGlobal('fetch',vi.fn().mockResolvedValueOnce(json(appearanceManifestResponse())).mockResolvedValueOnce(json(f)));
 await expect(createLeafAppearanceExecutionClient(appearanceToken).frame(appearanceJobId,0,signal())).rejects.toThrow();
});
it.each(['canceled','simulating'])('reads current cancel envelope for matching job in %s',async(state)=>{
 vi.stubGlobal('fetch',vi.fn(async()=>json({schema_version:'leaf-appearance-execution-cancel-v1',...appearanceFlags,observed_at:'2026-10-23T19:02:00Z',job:{...appearanceResponse().job,state},cancel_requested:true,cancel_accepted:true})));
 expect((await createLeafAppearanceExecutionClient(appearanceToken).cancel(appearanceJobId,signal())).job.state).toBe(state);
});
it('accepts actual immediate queued cancellation with no pending cancellation flag',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>json({schema_version:'leaf-appearance-execution-cancel-v1',...appearanceFlags,observed_at:'2026-10-23T22:58:00Z',job:{...appearanceResponse().job,state:'canceled',attempt_count:0},cancel_requested:false,cancel_accepted:true})));
 const value=await createLeafAppearanceExecutionClient(appearanceToken).cancel(appearanceJobId,signal());
 expect(value).toMatchObject({job:{state:'canceled',attempt_count:0},cancel_requested:false,cancel_accepted:true});
});
it('rejects accepted cancellation with neither terminal cancellation nor a pending request',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>json({schema_version:'leaf-appearance-execution-cancel-v1',...appearanceFlags,observed_at:'2026-10-23T22:58:00Z',job:{...appearanceResponse().job,state:'queued',attempt_count:0},cancel_requested:false,cancel_accepted:true})));
 await expect(createLeafAppearanceExecutionClient(appearanceToken).cancel(appearanceJobId,signal())).rejects.toThrow();
});
it('bounds response stream at2MiB and cancels more reads',async()=>{
 let canceled=false;const stream=new ReadableStream({pull(c){c.enqueue(new Uint8Array(2*1024**2+1));},cancel(){canceled=true;}});vi.stubGlobal('fetch',vi.fn(async()=>new Response(stream,{headers:{'Content-Type':'application/json','Cache-Control':'no-store'}})));
 await expect(createLeafAppearanceExecutionClient(appearanceToken).status(appearanceJobId,signal())).rejects.toThrow();expect(canceled).toBe(true);
});
it.each(['media','cache','utf8','view','success_status'])('rejects invalid transport/view %s',async(fault)=>{
 const v={...appearanceResponse(),replay:fault==='view'?{}:null};vi.stubGlobal('fetch',vi.fn(async()=>new Response(fault==='utf8'?new Uint8Array([255]):JSON.stringify(v),{status:fault==='success_status'?201:200,headers:{'Content-Type':fault==='media'?'text/html':'application/json','Cache-Control':fault==='cache'?'public':'no-store'}})));
 await expect(createLeafAppearanceExecutionClient(appearanceToken).status(appearanceJobId,signal())).rejects.toThrow();
});
it('propagates in-flight and pre-start abort without a retry',async()=>{
 const fetch=vi.fn((_url:string,opts:RequestInit)=>new Promise((_resolve,reject)=>opts.signal?.addEventListener('abort',()=>reject(opts.signal?.reason),{once:true})));vi.stubGlobal('fetch',fetch);
 const api=createLeafAppearanceExecutionClient(appearanceToken),c=new AbortController(),pending=api.status(appearanceJobId,c.signal);c.abort();await expect(pending).rejects.toBeDefined();
 await expect(api.status(appearanceJobId,c.signal)).rejects.toBeDefined();expect(fetch).toHaveBeenCalledTimes(1);
});
it.each(['leaf_id','curve','birth','stem_id','late_leaf'])('rejects cross-frame organ drift %s',async(fault)=>{
 const v=appearanceResponse(),f=v.replay.frames[1];
 if(fault==='leaf_id')f.leaves[0].leaf_id='different-live-leaf';
 else if(fault==='curve')f.leaves[0].curve_sha256='a'.repeat(64);
 else if(fault==='birth')f.leaves[0].emerged_elapsed_seconds_exact={numerator:'1',denominator:'1',unit:'s'};
 else if(fault==='stem_id')v.replay.frames[8].stem.internodes[4].internode_id='drifted-generative-internode';
 else{const omitted=v.replay.frames[3];omitted.leaves.pop();omitted.tracked_leaf_count=omitted.leaves.length;
  omitted.tracked_leaf_area.value=omitted.leaves.reduce((sum:number,q:{area:{value:number}})=>sum+q.area.value,0);}
 await expect(decodeLeafAppearanceExecutionReplay(v,appearanceJobId)).rejects.toThrow();
});
it.each([422,503])('does not return an earlier replay after a new current HTTP%s refusal',async(status)=>{
 const v=appearanceResponse(),fetch=vi.fn().mockResolvedValueOnce(json({...v,replay:null})).mockResolvedValueOnce(json(v)).mockResolvedValueOnce(json({error:{code:'unavailable'}},status));vi.stubGlobal('fetch',fetch);
 const api=createLeafAppearanceExecutionClient(appearanceToken);expect((await api.observe(appearanceJobId,signal())).replay?.frames).toHaveLength(12);
 await expect(api.observe(appearanceJobId,signal())).rejects.toMatchObject({status});expect(fetch).toHaveBeenCalledTimes(3);
});
it.each([-1,.5,64])('rejects invalid frame index%s before network',async(index)=>{
 const fetch=vi.fn();vi.stubGlobal('fetch',fetch);await expect(createLeafAppearanceExecutionClient(appearanceToken).frame(appearanceJobId,index,signal())).rejects.toThrow();expect(fetch).not.toHaveBeenCalled();
});
it('requires submit202 and rejects path injection before network',async()=>{
 const fetch=vi.fn(async()=>json(appearanceResponse().job,200));vi.stubGlobal('fetch',fetch);const api=createLeafAppearanceExecutionClient(appearanceToken);
 await expect(api.submit(decodeLeafAppearanceRequest(appearanceRequest()),signal())).rejects.toThrow();
 await expect(api.status('../escape',signal())).rejects.toThrow();expect(fetch).toHaveBeenCalledTimes(1);
});
