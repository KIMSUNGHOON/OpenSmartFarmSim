import { describe,it,expect,vi,afterEach } from 'vitest';
import { readFileSync } from 'node:fs';
import { decodeMorphologyStatus,decodeMorphologyReplay,createMorphologyExecutionClient } from './morphologyExecution';

const fixture=(name:string)=>JSON.parse(readFileSync(new URL(`../public/morphology-rational-replay/${name}`,import.meta.url),'utf8'));
const jobId='11111111-1111-4111-8111-111111111111',hash=(n:string)=>n.repeat(64);
const flags={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'};
export function response(){
  const result={result_sha256:hash('2'),numerical_root_sha256:fixture('frame-0.json').artifact_sha256,
    calculated_at:'2026-10-21T21:00:00.000000Z',study_id:'study',revision:'r1',farm:{scenario_id:'farm',scenario_revision:'r1',registration_sha256:hash('3'),crop_id:'crop-1'},
    profile_applicability:'unvalidated_for_registered_crop',binding_sha256:hash('4'),program_sha256:fixture('root.json').program_sha256,
    source_sha256:hash('5'),input_evidence_sha256:hash('6')};
  return {schema_version:'morphology-execution-read-v1',...flags,observed_at:'2026-10-21T21:01:00.000000Z',cancel_requested:false,
    job:{job_id:jobId,stage:'simulation',state:'succeeded',attempt_count:1,max_attempts:3,created_at:'2026-10-21T21:00:00Z',updated_at:'2026-10-21T21:00:01Z',reason_code:null},
    result,manifest:null,frame:null,replay:{manifest:{schema_version:'morphology-signed-manifest-v1',...flags,...result,manifest:fixture('root.json')},
      frames:Array.from({length:12},(_,i)=>fixture(`frame-${i}.json`))}};
}
afterEach(()=>vi.unstubAllGlobals());
describe('authenticated immutable morphology SDK',()=>{
  it('preserves original UTC, exact births, quantities and server result identity',async()=>{
    const value=response(),loaded=await decodeMorphologyReplay(value,jobId);
    expect(loaded.replay.frames).toEqual(value.replay.frames);expect(loaded.status.result?.result_sha256).toBe(hash('2'));
    expect(loaded.replay.artifact_sha256).toBe(value.result.numerical_root_sha256);
  });
  it.each(['job','gate','root','time','order','count','birth','unit','private'])('rejects changed %s without fallback',async(change)=>{
    const value=response();
    if(change==='job')value.job.job_id='11111111-1111-4111-8111-111111111112';
    else if(change==='gate')value.gates='G1';
    else if(change==='root')value.replay.frames[0].artifact_sha256=hash('0');
    else if(change==='time')value.replay.frames[0].at='2026-10-01T03:00:00Z';
    else if(change==='order')value.replay.frames.reverse();
    else if(change==='count')value.replay.frames.pop();
    else if(change==='birth')value.replay.frames[0].internodes[0].emerged_elapsed_seconds_exact.denominator='0';
    else if(change==='unit')value.replay.frames[0].internodes[0].length.unit='cm';
    else Object.assign(value,{private_source:'not allowed'});
    await expect(decodeMorphologyReplay(value,jobId)).rejects.toThrow();
  });
  it('queued and canceled statuses have no result or synthetic fallback',()=>{
    const value=response();value.job.state='queued';Object.assign(value,{result:null,replay:null});
    expect(decodeMorphologyStatus(value,jobId).result).toBeNull();value.job.state='canceled';
    expect(decodeMorphologyStatus(value,jobId).job.state).toBe('canceled');
  });
  it('sends one authenticated current read with no ambient cookies or redirects',async()=>{
    const value=response();Object.assign(value,{replay:null});const fetch=vi.fn(async(_url:RequestInfo|URL,_options?:RequestInit)=>new Response(JSON.stringify(value),{status:200}));vi.stubGlobal('fetch',fetch);
    const api=createMorphologyExecutionClient('owned-token-'+ 'a'.repeat(32));await api.status(jobId,new AbortController().signal);
    expect(fetch).toHaveBeenCalledTimes(1);expect(fetch.mock.calls[0]?.[0]).toBe(`/v1/jobs/${jobId}/crop-morphology-execution`);
    expect(fetch.mock.calls[0]?.[1]).toMatchObject({cache:'no-store',redirect:'error',credentials:'omit',method:'GET'});
  });
});
