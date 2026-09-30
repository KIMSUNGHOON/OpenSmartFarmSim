import { describe,it,expect } from 'vitest';
import { createApi,ApiError } from './api';
import { authoredJobId,authoredRunId,authoredResponses } from '../e2e/authored-thermal-fixture';

function mock(data=authoredResponses()) {
  const calls:{path:string;init:RequestInit|undefined}[]=[];
  const fetcher:typeof fetch=async (url,init)=>{
    const path=String(url);calls.push({path,init});
    return new Response(JSON.stringify(path.endsWith('/series') ? data.series : data.summary),
      {headers:{'content-type':'application/json'}});
  };
  return {api:createApi('synthetic-authored-thermal-token',fetcher),calls};
}

describe('authored thermal replay read',()=>{
  it('binds completed job, Run and all points with read-only requests',async ()=>{
    const {api,calls}=mock();const value=await api.authoredThermalReplay(authoredJobId);
    expect(value.summary.run_id).toBe(authoredRunId);
    expect(value.summary.claim_scope).toBe('synthetic_thermal_replay_only');
    expect(value.series.points).toHaveLength(120);
    expect(calls.map(call=>call.path)).toEqual(['/v1/jobs/'+authoredJobId+'/authored-run',
      '/v1/authored-runs/'+encodeURIComponent(authoredRunId),
      '/v1/authored-runs/'+encodeURIComponent(authoredRunId)+'/series']);
    for(const {init} of calls){expect(init?.method).toBe('GET');expect(init?.cache).toBe('no-store');
      expect(init?.redirect).toBe('error');expect(init?.credentials).toBe('omit');}
  });
  it.each(['run','scope','trace','time','count','extra','numeric'])('holds %s mismatch before display',async kind=>{
    const data=authoredResponses();
    if(kind==='run')data.series.run_id='authored-thermal-run-v1:'+'0'.repeat(64);
    if(kind==='scope')data.summary.claim_scope='crop_forecast';
    if(kind==='trace')data.summary.trace_sha256=['not-a-digest','d'.repeat(64)];
    if(kind==='time')data.series.points[1]!.at_utc=data.series.points[0]!.at_utc;
    if(kind==='count')data.series.points.pop();
    if(kind==='extra')Object.assign(data.series.points[0]!,{crop_growth_cm:12});
    if(kind==='numeric')data.series.points[0]!.heat_delivered_w_th=-1;
    await expect(mock(data).api.authoredThermalReplay(authoredJobId)).rejects.toBeInstanceOf(ApiError);
  });
});
