import {describe,it,expect} from 'vitest';
import {readAppearanceReplayIndex,appearanceReplayURL} from './leafAppearanceReplayLocation';
import {LEAF_APPEARANCE_FIXTURE as F} from './leafAppearanceReplayFixture';

describe('appearance replay source and selected index in the URL',()=>{
 it.each([0,5,11])('restores frame%s only for the same immutable source',index=>{
  const url=appearanceReplayURL('http://localhost:5176/leaf-appearance-replay.html',index)!;
  expect(readAppearanceReplayIndex(new URL(url).search)).toBe(index);
  expect(new URL(url).searchParams.get('artifact')).toBe(F.artifact_sha256);
 });
 it.each(['','?frame=11',`?artifact=${'0'.repeat(64)}&frame=11`,`?artifact=${F.artifact_sha256}&frame=11&frame=1`,
  `?artifact=${F.artifact_sha256}&artifact=${F.artifact_sha256}&frame=11`,
  ...['-1','12','01','1.0','true','+1','99999999999999999999999999',''].map(frame=>`?artifact=${F.artifact_sha256}&frame=${frame}`)])('starts at0 for invalid cursor %s',query=>{
  expect(readAppearanceReplayIndex(query)).toBe(0);
 });
 it.each([-1,12,1.5,NaN,Infinity])('does not write an invalid index %s',index=>{
  expect(appearanceReplayURL('http://localhost:5176/leaf-appearance-replay.html',index)).toBeNull();
 });
});
