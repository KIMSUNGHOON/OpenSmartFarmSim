import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
export const morphologyJobId='11111111-1111-4111-8111-111111111111';
export const morphologyToken='owned-morphology-browser-token-'+ 'a'.repeat(32);
const hash=(n:string)=>n.repeat(64);
export const morphologyFlags={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'};
export const morphologyFrame=(index:number)=>JSON.parse(readFileSync(resolve(`public/morphology-rational-replay/frame-${index}.json`),'utf8'));
const root=()=>JSON.parse(readFileSync(resolve('public/morphology-rational-replay/root.json'),'utf8'));
export function morphologyPreview(){return {schema_version:'owned-morphology-preview-input-v1',...morphologyFlags,
  label:'자체 합성 토마토 · 하루 12시점',request:{study_id:'study',revision:'r1',farm:{scenario_id:'farm',scenario_revision:'r1',registration_sha256:hash('3'),crop_id:'crop-1'},
    input:{schema_version:'morphology-input-source-v1',program_id:'program',program_sha256:root().program_sha256,source_sha256:hash('5'),evidence_sha256:hash('6')},
    rights:{schema_version:'morphology-input-rights-v1',declaration_id:'owned',revision:'r1',input_source_sha256:hash('5'),
      available_at:'2026-10-21T18:49:47.384461Z',redistribute:false,...Object.fromEntries(['ownership_asserted','access','store','transform','use','display'].map(k=>[k,true]))}}};}
export function morphologyResponse(state='succeeded',replay=false){
  const result={result_sha256:hash('2'),numerical_root_sha256:morphologyFrame(0).artifact_sha256,
    calculated_at:'2026-10-21T21:00:00.000000Z',study_id:'study',revision:'r1',farm:morphologyPreview().request.farm,
    profile_applicability:'unvalidated_for_registered_crop',binding_sha256:hash('4'),program_sha256:root().program_sha256,
    source_sha256:hash('5'),input_evidence_sha256:hash('6')};
  return {schema_version:'morphology-execution-read-v1',...morphologyFlags,observed_at:'2026-10-21T21:01:00.000000Z',cancel_requested:false,
    job:{job_id:morphologyJobId,stage:'simulation',state,attempt_count:state==='queued'?0:1,max_attempts:3,created_at:'2026-10-21T21:00:00Z',
      updated_at:'2026-10-21T21:00:01Z',reason_code:state==='canceled'?'canceled_by_request':null},
    result:state==='succeeded'?result:null,manifest:null,frame:null,replay:replay?{
      manifest:{schema_version:'morphology-signed-manifest-v1',...morphologyFlags,...result,manifest:root()},
      frames:Array.from({length:12},(_,i)=>morphologyFrame(i))}:null};
}
