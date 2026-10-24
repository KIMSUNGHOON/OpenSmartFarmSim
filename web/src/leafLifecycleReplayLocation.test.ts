import {describe,it,expect} from 'vitest';
import {readLifecycleReplayLocation,lifecycleReplayURL} from './leafLifecycleReplayLocation';

describe('lifecycle scenario and stored frame restoration',()=>{
 it.each(['no-removal','with-removal'] as const)('roundtrips12frames in %s with its own artifact',scenario=>{
  for(let index=0;index<12;index++){
   const url=new URL(lifecycleReplayURL('http://localhost:5176/leaf-lifecycle-replay.html',scenario,index)!);
   expect(readLifecycleReplayLocation(url.search)).toEqual({scenario,index});
  }
 });
 it.each(['','?frame=11','?scenario=unknown&frame=11','?scenario=with-removal&scenario=no-removal&frame=11',
  '?scenario=no-removal&artifact=bad&frame=11'])('holds an unbound or ambiguous selection %s',search=>{
  expect(readLifecycleReplayLocation(search).index).toBe(0);
 });
 it.each(['12','-1','1.5','true','01','1&frame=2'])('rejects invalid stored frame %s',frame=>{
  const url=new URL(lifecycleReplayURL('http://localhost:5176/leaf-lifecycle-replay.html','no-removal',11)!);url.searchParams.delete('frame');
  expect(readLifecycleReplayLocation(url.search+'&frame='+frame)).toEqual({scenario:'no-removal',index:0});
 });
 it.each([-1,12,1.5,NaN,Infinity])('does not produce an invalid stored index %s',index=>{
  expect(lifecycleReplayURL('http://localhost:5176/leaf-lifecycle-replay.html','with-removal',index)).toBeNull();
 });
});
