import { readFileSync } from 'node:fs';

const fixture=(name:string)=>JSON.parse(readFileSync(new URL(`../public/leaf-appearance-replay/${name}`,import.meta.url),'utf8'));
export const appearanceJobId='11111111-1111-4111-8111-111111111120';
export const appearanceToken='owned-leaf-browser-software-token-'+ 'a'.repeat(32);
export const appearanceFlags={scope:'software_research_only',claim_scope:'synthetic_crop_math_only',gates:'not_assessed'};
const hash=(letter:string)=>letter.repeat(64);
export function appearanceRequest(){return {study_id:'owned-leaf-study',revision:'r1',
  farm:{scenario_id:'owned-farm',scenario_revision:'r1',registration_sha256:hash('3'),crop_id:'crop-1'},
  parent:{job_id:'22222222-2222-4222-8222-222222222222',result_sha256:hash('4'),numerical_root_sha256:fixture('root.json').stem_artifact_sha256},
  input:{schema_version:'leaf-appearance-input-source-v1',program_id:'owned-software-leaves',program_sha256:fixture('root.json').source_program_sha256,
    source_sha256:hash('5'),evidence_sha256:hash('6')},
  rights:{schema_version:'leaf-appearance-input-rights-v1',declaration_id:'owned-leaf-source',revision:'r1',
    input_source_sha256:hash('5'),available_at:'2026-10-23T16:00:00Z',redistribute:false,
    ownership_asserted:true,access:true,store:true,transform:true,use:true,display:true}};}
export function appearancePreview(){return {schema_version:'owned-leaf-appearance-preview-input-v1',...appearanceFlags,
  label:'자체 합성 토마토 · 새 잎 12시점',request:appearanceRequest()};}
export function appearanceResponse(){
  const request=appearanceRequest(),result={result_sha256:hash('7'),numerical_root_sha256:fixture('frame-0.json').artifact_sha256,
    calculated_at:'2026-10-23T19:01:00.123456Z',parent_job_id:request.parent.job_id,parent_result_sha256:request.parent.result_sha256,
    parent_numerical_root_sha256:request.parent.numerical_root_sha256,parent_calculated_at:'2026-10-23T18:00:00Z',
    normalization:'per_tracked_shoot',study_id:request.study_id,revision:request.revision,farm:request.farm,
    profile_applicability:'unvalidated_for_registered_crop',binding_sha256:hash('8'),program_sha256:request.input.program_sha256,
    source_sha256:request.input.source_sha256,input_evidence_sha256:request.input.evidence_sha256};
  return {schema_version:'leaf-appearance-execution-read-v1',...appearanceFlags,observed_at:'2026-10-23T19:02:00Z',
    job:{job_id:appearanceJobId,stage:'simulation',state:'succeeded',attempt_count:1,max_attempts:3,
      created_at:'2026-10-23T19:00:00Z',updated_at:'2026-10-23T19:01:00.123456Z',reason_code:'leaf_appearance_completed'},
    cancel_requested:false,result,manifest:null,frame:null,replay:{
      manifest:{schema_version:'leaf-appearance-signed-manifest-v1',...appearanceFlags,...result,manifest:fixture('root.json')},
      frames:Array.from({length:12},(_,index)=>fixture(`frame-${index}.json`))}};
}

export function appearanceManifestResponse(){const value=appearanceResponse();return {...value,manifest:value.replay.manifest,replay:null};}
export function appearanceFrameResponse(index=0){const value=appearanceResponse();return {...value,replay:null,frame:{
 schema_version:'leaf-appearance-signed-frame-v1',...appearanceFlags,...value.result,frame:value.replay.frames[index],
 frame_sha256:fixture('index.json').frames[index].sha256}};}
