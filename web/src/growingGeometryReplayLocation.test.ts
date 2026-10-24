import {expect,it} from 'vitest';
import {readGrowingReplayLocation,growingReplayURL} from './growingGeometryReplayLocation';
import {GROWING_GEOMETRY_FIXTURE as F} from './growingGeometryReplayFixture';
it.each(Object.keys(F.scenarios))('restores a pinned scenario/frame: %s',name=>{
 const scenario=name as keyof typeof F.scenarios,url=growingReplayURL('http://localhost:5176/growing-geometry-replay.html',scenario,16);
 expect(url).not.toBeNull();expect(readGrowingReplayLocation(new URL(url!).search)).toEqual({scenario,index:16});
});
it.each(['','?scenario=other','?scenario=reverse&frame=1','?scenario=reverse&scenario=warm-day',
 '?scenario=warm-day&artifact=bad&frame=16',`?artifact=${F.scenarios['warm-day'].artifact_sha256}&frame=17`,
 `?artifact=${F.scenarios['warm-day'].artifact_sha256}&frame=01`,`?artifact=${F.scenarios['warm-day'].artifact_sha256}&frame=1&frame=2`])('rejects unbound frame selections %s',search=>{
 expect(readGrowingReplayLocation(search).index).toBe(0);
});
it.each([-1,17,NaN,Infinity,1.5])('refuses invalid output frame %s',index=>expect(growingReplayURL('http://localhost:5176/growing-geometry-replay.html','warm-day',index)).toBeNull());
