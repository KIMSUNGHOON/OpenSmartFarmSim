import { describe,it,expect } from 'vitest';
import { createApi,ApiError } from './api';
import { thermalJobId,thermalRunId,thermalResponses } from '../e2e/thermal-fixture';

function mock(data=thermalResponses()) {
  const calls:{path:string;init:RequestInit|undefined}[]=[];
  const fetcher:typeof fetch=async (url,init)=>{
    const path=String(url);calls.push({path,init});
    const body=path.endsWith('/series') ? data.series : path.endsWith('/manifest') ? data.manifest : data.summary;
    return new Response(JSON.stringify(body),{headers:{'content-type':'application/json'}});
  };
  return {api:createApi('synthetic-thermal-api-token-only',fetcher),calls};
}
describe('closed stored thermal replay',()=>{
  it('joins job completion and all three views with explicit read-only authorization',async ()=>{
    const {api,calls}=mock();const result=await api.thermalReplay(thermalJobId);
    expect(result.summary.run_id).toBe(thermalRunId);expect(result.series.points).toHaveLength(120);
    expect(result.series.points[119]?.at_utc).toBe(result.summary.end_utc);
    expect(calls.map(call=>call.path)).toEqual(['/v1/jobs/'+thermalJobId+'/run',
      '/v1/runs/'+encodeURIComponent(thermalRunId),'/v1/runs/'+encodeURIComponent(thermalRunId)+'/series',
      '/v1/runs/'+encodeURIComponent(thermalRunId)+'/manifest']);
    for (const {init} of calls) {
      expect(init?.method).toBe('GET');expect(init?.cache).toBe('no-store');
      expect(init?.redirect).toBe('error');expect(init?.credentials).toBe('omit');
    }
  });
  it.each(['run','trace','scope','units','count','time','nonfinite','rights','extra'])('rejects %s disagreement without a partial replay',async kind=>{
    const data=thermalResponses();
    if(kind==='run')data.series.run_id='synthetic-thermal-v1:'+'0'.repeat(64);
    if(kind==='trace')data.manifest.trace_sha256=['0'.repeat(64),'d'.repeat(64)];
    if(kind==='scope')data.summary.temporal_provenance='ex_ante';
    if(kind==='units')data.summary.unit_registry_version='thermal-other-units';
    if(kind==='count')data.series.points.pop();
    if(kind==='time')data.series.points[1]!.at_utc=data.series.points[0]!.at_utc;
    if(kind==='nonfinite')data.series.points[1]!.heat_delivered_w_th=Infinity;
    if(kind==='rights')data.manifest.used_sources[0]!.display_right='denied';
    if(kind==='extra')Object.assign(data.series.points[0]!,{crop_growth_cm:12});
    await expect(mock(data).api.thermalReplay(thermalJobId)).rejects.toBeInstanceOf(ApiError);
  });
});
