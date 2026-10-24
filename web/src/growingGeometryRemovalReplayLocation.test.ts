import {expect,it} from 'vitest';
import {readGrowingRemovalReplayLocation,growingRemovalReplayURL} from './growingGeometryRemovalReplayLocation';
import {GROWING_GEOMETRY_REMOVAL_FIXTURE as F} from './growingGeometryRemovalReplayFixture';
it.each(Object.keys(F.scenarios))('restores a pinned scenario/frame: %s',name=>{
 const scenario=name as keyof typeof F.scenarios,url=growingRemovalReplayURL('http://localhost:5176/growing-geometry-removal-replay.html',scenario,16);
 expect(url).not.toBeNull();expect(readGrowingRemovalReplayLocation(new URL(url!).search)).toEqual({scenario,index:16});
});
it.each(['','?scenario=other','?scenario=case-1-remove-1&frame=1','?scenario=case-1-remove-1&scenario=case-0-remove-1',
 '?scenario=case-0-remove-1&artifact=bad&frame=16',`?artifact=${F.scenarios['case-0-remove-1'].artifact_sha256}&frame=18`,
 `?artifact=${F.scenarios['case-0-remove-1'].artifact_sha256}&frame=01`,`?artifact=${F.scenarios['case-0-remove-1'].artifact_sha256}&frame=1&frame=2`])('rejects unbound frame selections %s',search=>{
 expect(readGrowingRemovalReplayLocation(search).index).toBe(0);
});
it.each([-1,18,NaN,Infinity,1.5])('refuses invalid output frame %s',index=>expect(growingRemovalReplayURL('http://localhost:5176/growing-geometry-removal-replay.html','case-0-remove-1',index)).toBeNull());

it('restores each same-time phase by its distinct stored index',()=>{
 const before=growingRemovalReplayURL('http://localhost:5176/growing-geometry-removal-replay.html','case-0-remove-1',7);
 const after=growingRemovalReplayURL('http://localhost:5176/growing-geometry-removal-replay.html','case-0-remove-1',8);
 expect(before).not.toBe(after);expect(readGrowingRemovalReplayLocation(new URL(before!).search).index).toBe(7);
 expect(readGrowingRemovalReplayLocation(new URL(after!).search).index).toBe(8);
});
