import { describe,it,expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { createApi,ApiError } from './api';
import { cropReferenceResponse,cropReferenceSelection } from '../demo/crop-reference';
import { decodeCropReplay,type CropLookup } from './cropReplay';

function raw():Record<string,any>{return cropReferenceResponse() as Record<string,any>;}
function mock(data:unknown=cropReferenceResponse()) {
  const calls:{path:string;init:RequestInit|undefined}[]=[];
  const fetcher:typeof fetch=async (url,init)=>{calls.push({path:String(url),init});
    return new Response(JSON.stringify(data),{headers:{'content-type':'application/json'}});};
  return {api:createApi('synthetic-crop-browser-token-only',fetcher),calls};
}
describe('saved crop research browser contract',()=>{
  it('retains the exact recorded public TLS values and all evidence scope',async ()=>{
    const artifact=JSON.parse(readFileSync(new URL('../../research/artifacts/api-crop-replay-reference-20261004.json',import.meta.url),'utf8'));
    expect(cropReferenceResponse()).toEqual(artifact.runtime_evidence.responses[3].value);
    const {api,calls}=mock();const value=await api.cropReplay(cropReferenceSelection);
    expect(value).toEqual(cropReferenceResponse());expect(value.samples).toHaveLength(6);
    expect(value.events).toHaveLength(2);expect(value.status).toBe('completed');
    expect(value.manifest.convergence).toBe('not_evaluated_for_this_program');
    expect(calls).toHaveLength(1);
    const url=new URL(calls[0]!.path,'http://127.0.0.1');
    expect(decodeURIComponent(url.pathname)).toBe('/v1/crop-research-results/'+value.result_id);
    expect(Object.fromEntries(url.searchParams)).toEqual(value.farm);
    expect(calls[0]!.init).toMatchObject({method:'GET',cache:'no-store',credentials:'omit',redirect:'error',
      headers:{authorization:'Bearer synthetic-crop-browser-token-only'}});
  });
  it.each(['result_id','scenario_id','scenario_revision','registration_sha256','crop_id'] as const)
    ('rejects foreign %s',key=>{
      const selection:CropLookup={...cropReferenceSelection,[key]:key.endsWith('sha256')?'0'.repeat(64):
        key==='result_id'?'crop-result-v1:'+'0'.repeat(64):'foreign'};
      expect(()=>decodeCropReplay(raw(),selection)).toThrow(ApiError);
    });
  it.each(['unit','negative','infinity','unknown','profile','scope','gate','reordered','duplicate',
    'start','end','date','timezone','fraction','manifest','solver','sample_bound','event_bound',
    'event_time','steps','hold_mix','hold_missing','cumulative','residual_unit','names'])
    ('rejects %s before any display',kind=>{
      const d=raw(),s=d.samples[1];
      if(kind==='unit')s.lai.unit='m2';
      if(kind==='negative')s.state.fruit.value=-1;
      if(kind==='infinity')s.state.buffer.value=Infinity;
      if(kind==='unknown')s.harvest_kg=10;
      if(kind==='profile')d.profile_applicability='validated';
      if(kind==='scope')d.claim_scope='crop_forecast';
      if(kind==='gate')d.gates='G1';
      if(kind==='reordered')d.samples.reverse();
      if(kind==='duplicate')s.at=d.samples[0].at;
      if(kind==='start')d.start_utc='2026-09-30T23:59:59Z';
      if(kind==='end')d.end_utc='2026-10-01T00:06:00Z';
      if(kind==='date')s.at='2026-02-30T00:01:00Z';
      if(kind==='timezone')s.at='2026-10-01T09:01:00+09:00';
      if(kind==='fraction')s.at='2026-10-01T00:01:00.5Z';
      if(kind==='manifest')d.manifest.code_sha256.secret='private';
      if(kind==='solver')d.manifest.solver.max_steps=1_000_001;
      if(kind==='sample_bound')d.samples=Array(20_001).fill(s);
      if(kind==='event_bound')d.events=Array(20_001).fill(d.events[0]);
      if(kind==='event_time')d.events[0].at='2026-10-01T00:06:00Z';
      if(kind==='steps')d.steps=d.planned_steps+1;
      if(kind==='hold_mix')d.status='hold';
      if(kind==='hold_missing')d.hold={};
      if(kind==='cumulative')s.cumulative.removal_fruit.value=-1;
      if(kind==='residual_unit')s.carbon_residual.unit='kg';
      if(kind==='names')d.manifest.profile_id='not a profile';
      expect(()=>decodeCropReplay(d,cropReferenceSelection)).toThrow(ApiError);
    });
  it('preserves signed hold diagnostics without normal samples or fabricated growth',()=>{
    const d=raw(),last=d.samples[0],failed=structuredClone(last.state);
    failed.buffer.value=-0.125;failed.fruit.value=null;
    Object.assign(d,{status:'hold',steps:0,samples:[],events:[],hold:{reason_code:'DEPLETED_STATE_HOLD',
      attempted_at:'2026-10-01T00:00:00.000001Z',phase:'rk4-k2',time_meaning:'solver_evaluation_time',
      last_confirmed:last,failed_state:failed}});
    const value=decodeCropReplay(d,cropReferenceSelection);
    expect(value.samples).toEqual([]);expect(value.hold?.failed_state.buffer.value).toBe(-0.125);
    expect(value.hold?.failed_state.fruit.value).toBeNull();
    d.hold.reason_code='invented';expect(()=>decodeCropReplay(d,cropReferenceSelection)).toThrow(ApiError);
  });
  it.each(['result_id','scenario_id','registration_sha256','crop_id'] as const)
    ('rejects invalid lookup %s without a network call',async key=>{
      const {api,calls}=mock();await expect(api.cropReplay({...cropReferenceSelection,[key]:'<invalid>'}))
        .rejects.toBeInstanceOf(ApiError);expect(calls).toEqual([]);
    });
});
