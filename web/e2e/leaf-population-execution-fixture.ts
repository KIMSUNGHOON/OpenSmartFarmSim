import { readFileSync } from 'node:fs';

const fixture=(name:string)=>JSON.parse(readFileSync(new URL(`../public/leaf-population-replay/${name}`,import.meta.url),'utf8'));
export const leafJobId='11111111-1111-4111-8111-111111111119';
export const leafToken='owned-leaf-browser-software-token-'+ 'a'.repeat(32);
export const leafFlags={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'};
const hash=(letter:string)=>letter.repeat(64);
export function leafRequest(){return {study_id:'owned-leaf-study',revision:'r1',
  farm:{scenario_id:'owned-farm',scenario_revision:'r1',registration_sha256:hash('3'),crop_id:'crop-1'},
  parent:{job_id:'22222222-2222-4222-8222-222222222222',result_sha256:hash('4'),numerical_root_sha256:fixture('root.json').stem_artifact_sha256},
  input:{schema_version:'leaf-population-input-source-v1',program_id:'owned-software-leaves',program_sha256:fixture('root.json').program_sha256,
    source_sha256:hash('5'),evidence_sha256:hash('6')},
  rights:{schema_version:'leaf-population-input-rights-v1',declaration_id:'owned-leaf-source',revision:'r1',
    input_source_sha256:hash('5'),available_at:'2026-10-22T00:00:00Z',redistribute:false,
    ownership_asserted:true,access:true,store:true,transform:true,use:true,display:true}};}
export function leafPreview(){return {schema_version:'owned-leaf-population-preview-input-v1',...leafFlags,
  label:'자체 합성 토마토 · 새 잎 12시점',request:leafRequest()};}
export function leafResponse(){
  const request=leafRequest(),result={result_sha256:hash('7'),numerical_root_sha256:fixture('frame-0.json').artifact_sha256,
    calculated_at:'2026-10-23T04:01:00.123456Z',parent_job_id:request.parent.job_id,parent_result_sha256:request.parent.result_sha256,
    parent_numerical_root_sha256:request.parent.numerical_root_sha256,parent_calculated_at:'2026-10-23T03:00:00Z',
    normalization:'per_tracked_shoot',study_id:request.study_id,revision:request.revision,farm:request.farm,
    profile_applicability:'unvalidated_for_registered_crop',binding_sha256:hash('8'),program_sha256:request.input.program_sha256,
    source_sha256:request.input.source_sha256,input_evidence_sha256:request.input.evidence_sha256};
  return {schema_version:'leaf-population-execution-read-v1',...leafFlags,observed_at:'2026-10-23T04:02:00Z',
    job:{job_id:leafJobId,stage:'simulation',state:'succeeded',attempt_count:1,max_attempts:3,
      created_at:'2026-10-23T04:00:00Z',updated_at:'2026-10-23T04:01:00.123456Z',reason_code:'leaf_population_completed'},
    cancel_requested:false,result,manifest:null,frame:null,replay:{
      manifest:{schema_version:'leaf-population-signed-manifest-v1',...leafFlags,...result,manifest:fixture('root.json')},
      frames:Array.from({length:12},(_,index)=>fixture(`frame-${index}.json`))}};
}
